"""BibleMap Cypher × Apache AGE(postgres 16) 호환성 점검 — task#340.

  python3 scripts/age_compat/run_check.py             전체 점검 → REPORT.md (판정과 무관하게 완주하면 exit 0)
  python3 scripts/age_compat/run_check.py --selftest  비교기가 차이를 실제로 잡는지
  python3 scripts/age_compat/run_check.py --coverage  보고서 행 ↔ 정적 호출 지점 대조 + 빈 칸 검사

흐름: 일회용 스택(docker-compose.yml) 기동 → 기준 neo4j에 적재 체인 실행 → 기준 그래프를 AGE `biblemap`에
복사 → 같은 체인을 AGE `biblemap_loaders`에 재생 → 앱을 neo4j·AGE 동시(dual)로 돌려 호출 지점별 대조 →
엔드포인트 JSON·지연 대조 → REPORT.md → `down -v`. prod(biblemap) 스택은 건드리지도 읽지도 않는다.
필요: docker, python3 + neo4j·fastapi·httpx·psycopg[binary] (requirements.txt).
"""
import argparse
import collections
import datetime
import json
import os
import re
import runpy
import shutil
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
import age_adapter as A  # noqa: E402

COMPOSE = ["docker", "compose", "-p", "biblemap-agecheck", "-f", os.path.join(HERE, "docker-compose.yml")]
NEO_URI, NEO_AUTH = "bolt://127.0.0.1:17687", ("neo4j", "agecheck-pass")
REPORT = os.path.join(HERE, "REPORT.md")

# 적재 체인 — 기준 neo4j와 AGE 재생이 이 순서 하나를 쓴다. 근거: README(원본 → 주입), CONTEXT
# (저작 Person이 load_person_events보다 먼저), load_books는 GitHub 원본 구절로 교집합을 내니 원본 바로 뒤 —
# 그래야 load_person_events·load_verse_events의 CONTAINS_BOOK MERGE가 Book을 찾는다.
LOAD_CHAIN = [
    "load_theographic", "load_books", "load_authored_persons", "load_authored_events", "load_authored_genealogy",
    "load_authored_mothers", "load_person_events", "load_verse_events", "apply_event_dedupe", "enrich_place_coords", "inject_ko_names", "inject_date_corrections",
    "inject_book_context", "inject_person_context", "inject_person_traits", "inject_place_context",
    "generate_book_events", "validate_event_chronology",
]

# DB를 부르는 엔드포인트 전부(+ 라벨 분기를 다 밟도록 노드 종류별 대표 id). DB 안 쓰는 엔드포인트도 싸니 함께 부른다.
IDS = {
    "jesus": "recgkFqZovgbr3pAi", "david": "rec1ZMFtfbEvoGC73", "place": "recL1WV82pXaRBQ59",  # 예루살렘
    "event": "recmXmhZt51doQu7o", "authored": "authored-david-goliath-gath",  # Holy Week(자식 PART_OF 보유)
    "group": "rechHR2dYztVvgNWa", "book": "rec4GS8yWh2R4mpdB",  # 사무엘상
}
ENDPOINTS = [
    "/books-overview", "/book/{book}/chapters", "/book/{book}/quotations", "/book/{book}/chapter/1",
    "/events", "/covenants", "/messianic-prophecies", "/topical-verses", "/parables-miracles",
    "/event/{event}/verses", "/event/{authored}/verses", "/node/{authored}", "/person/{jesus}/journey", "/person/{david}/journey",
    "/person/{jesus}/family", "/person/{david}/family", "/person/{jesus}/event-ids",
    "/node/{jesus}/places", "/node/{event}/places", "/node/{group}/places", "/node/{book}/places",
    "/node/{place}/places", "/node/{jesus}/neighbors/grouped", "/node/{jesus}", "/node/{book}",
    "/node/{place}", "/node/{event}", "/node/{group}", "/person/{jesus}/reliance", "/reliance/ranking",
    "/persons/curated", "/keypeople-cards", "/person/{jesus}/connections", "/person/{david}/relations",
    "/place/{place}/curated-persons", "/place/{place}", "/search?q=다윗", "/search?q=Jerusalem",
    "/tours", "/tour/david-united-kingdom", "/stats", "/verse/09017049/persons", "/timeline/canon", "/words/{book}",
    "/words/{book}/verses?w=하나님",
]


# ================================================================ 재작성안
# 오류(또는 결과 차이)를 낸 구문에 붙는 재작성안. kind: mechanical(구문 국소 치환 — 코드모드로 가능) |
# manual(쿼리를 다시 짜거나 일부를 앱/SQL로 옮겨야 함). 실행형(transform/apply)은 AGE 실패 시 그 재작성으로
# 대신 돌려 흐름을 잇고, 결과를 neo4j와 대조해 재작성안이 실제로 맞는지 보고서에 적는다.
# 이 목록은 실측(AGE 1.6.0)으로 막힌 구문마다 만든 것이다 — 새 구문이 막히면 여기에 추가한다.

_CLAUSE_KW = r"\b(OPTIONAL\s+MATCH|MATCH|WITH|RETURN|UNWIND|WHERE|ORDER\s+BY|SKIP|LIMIT|CREATE|MERGE|SET|DELETE|DETACH|CALL|UNION)\b"
_AGG = re.compile(r"\b(count|sum|avg|min|max|collect)\s*\(", re.I)


def _agg_order_clause(q):
    """집계 별칭을 같은 절에서 ORDER BY 하는 WITH/RETURN 절 → (시작, 끝, 키워드, 항목) | None."""
    masked = A._mask(q)
    kws = list(re.finditer(_CLAUSE_KW, masked, re.I))
    for cur, nxt in zip(kws, kws[1:]):
        kw = cur.group(1).upper()
        if kw in ("WITH", "RETURN") and nxt.group(1).upper().startswith("ORDER") \
                and _AGG.search(q[cur.end():nxt.start()]):
            return cur.start(), nxt.start(), kw, q[cur.end():nxt.start()].strip()
    return None


def _split_agg_order(q):
    s, e, kw, items = _agg_order_clause(q)
    names = []
    for item in A._top_level_split(items):
        m = re.search(r"\s+AS\s+(`?\w+`?)\s*$", item.strip(), re.I)
        names.append(m.group(1) if m else item.strip())
    return f"{q[:s]}WITH {items} {kw} {', '.join(names)} {q[e:]}"


def _rebind_unwind(q):
    m = re.search(r"UNWIND\s+\w+\s+AS\s+(\w+)\s+(?:OPTIONAL\s+)?MATCH\s+\((\1)\b", q)
    v = m.group(1)
    q = f"{q[:m.start(2)]}{v}_u{q[m.end(2):]}"
    tail = q[m.end():]
    nxt = re.search(r"\b(RETURN|WITH)\b", tail)
    seg, rest = tail[:nxt.start()], tail[nxt.start():]
    if re.search(r"\bWHERE\b", seg):
        seg = re.sub(r"\bWHERE\b", f"WHERE id({v}_u) = id({v}) AND (", seg, count=1).rstrip() + ")\n"
    else:
        seg = seg.rstrip() + f" WHERE id({v}_u) = id({v})\n"
    return q[:m.end()] + seg + rest


def _list_predicate(q):
    m = re.search(r"WHERE\s+all\(\s*(\w+)\s+IN\s+(.+?)\s+WHERE\s+(.+?)\)\s*(?=RETURN|WITH)", q, re.S)
    v, lst, cond = m.groups()
    match_clause = q[:m.start()]
    # 경로 변수 + 뒤에서 쓰이는 노드 변수만 넘긴다. 시작 노드(j)까지 묶어 집계하면 AGE가 메모리를 6GB 넘게 쓰다
    # 강제 종료된다(실측) — 묶음 키를 최소로.
    path_vars = re.findall(r"MATCH\s+(\w+)\s*=", match_clause)
    used = [x for x in re.findall(r"\((\w+)[:\s{)]", match_clause) if re.search(rf"\b{x}\b", q[m.end():])]
    carry = list(dict.fromkeys(path_vars + used))
    c = ", ".join(carry)
    return (f"{q[:m.start()]}WITH {c} UNWIND {lst} AS {v} "
            f"WITH {c}, sum(CASE WHEN {cond} THEN 0 ELSE 1 END) AS _bad WHERE _bad = 0\n{q[m.end():]}")


def _apply_index(age, q, params):
    label, prop = re.search(r"FOR\s*\(\s*\w+\s*:\s*(\w+)\s*\)\s*ON\s*\(\s*\w+\.(\w+)\s*\)", q).groups()
    age.ensure_vlabel(label)
    g = age.graph
    age.sql(f'CREATE INDEX IF NOT EXISTS "{label}_{prop}_btree" ON "{g}"."{label}" USING btree '
            f"(agtype_access_operator(VARIADIC ARRAY[properties, '\"{prop}\"'::agtype]))")
    age.sql(f'CREATE INDEX IF NOT EXISTS "{label}_props_gin" ON "{g}"."{label}" USING gin (properties)')
    return [], []


def _apply_collect_zip(age, q, params):
    """collect({a: a, b: b, …})[0..N] AS rows → 키마다 병렬 collect 후 앱에서 zip."""
    m = re.search(r"collect\(\{(.+?)\}\)\[0\.\.(\d+)\]\s+AS\s+(\w+)", q, re.S)
    keys = [kv.split(":")[0].strip() for kv in A._top_level_split(m.group(1))]
    n, alias = int(m.group(2)), m.group(3)
    par = ", ".join(f"collect({k}) AS _c_{k}" for k in keys)
    q2 = q[:m.start()] + par + q[m.end():]
    q2 = re.sub(rf"\bRETURN\s+{alias}\b", "RETURN " + ", ".join(f"_c_{k}[0..{n}] AS _c_{k}" for k in keys), q2)
    cols, recs = age.cypher(q2, params)
    out = []
    for r in recs:
        rows = [dict(zip(keys, vals)) for vals in zip(*(r[f"_c_{k}"] for k in keys))]
        rest = [c for c in cols if not c.startswith("_c_")]
        out.append(A.AgeRecord([alias] + rest, [rows] + [r[c] for c in rest]))
    return [alias] + rest, out


def _apply_split_call(age, q, params):
    """apply_event_dedupe의 CALL (r, k) { … } 다섯 개 + DETACH DELETE → 독립 문장 여섯."""
    h = "MATCH (r:Event {theographic_id: $rid}), (k:Event {theographic_id: $kid}) "
    for body in (
        "MATCH (r)-[:PART_OF]->(p) WHERE p <> k MERGE (k)-[:PART_OF]->(p)",
        "MATCH (r)-[:OCCURS_AT]->(pl) MERGE (k)-[:OCCURS_AT]->(pl)",
        "MATCH (r)-[:HAS_PARTICIPANT]->(per) MERGE (k)-[:HAS_PARTICIPANT]->(per)",
        "MATCH (c:Event)-[:PART_OF]->(r) WHERE c <> k MERGE (c)-[:PART_OF]->(k)",
        "MATCH (b:Book)-[rel:CONTAINS_BOOK]->(r) WHERE NOT EXISTS((b)-[:CONTAINS_BOOK]->(k)) "
        "CREATE (b)-[:CONTAINS_BOOK {primary: false}]->(k)",
    ):
        age.cypher(h + body, params)
    return age.cypher("MATCH (r:Event {theographic_id: $rid}) DETACH DELETE r", params)


def _apply_sql_order(age, q, params):
    """ORDER BY rank, n.nameKo → 정렬을 cypher() 밖 SQL로: 문자열은 COLLATE "C"(코드포인트, neo4j와 같은 순)."""
    m = re.search(r"RETURN\s+(.+?)\s+ORDER\s+BY\s+(.+?)\s+LIMIT\s+(\d+)\s*$", q, re.S)
    ret, order, limit = m.group(1), [x.strip() for x in m.group(2).split(",")], m.group(3)
    cols = [c.strip() for c in ret.split(",")]
    q2 = q[:m.start()] + "RETURN " + ", ".join(cols + [f"{o} AS _o{i}" for i, o in enumerate(order)])
    n = len(cols) + len(order)
    spec = ", ".join(f"c{i} agtype" for i in range(n))
    sort = ", ".join(f'c{len(cols) + i}::text COLLATE "C"' if "." in o else f"c{len(cols) + i}"
                     for i, o in enumerate(order))
    sql = (f"SELECT {', '.join(f'c{i}' for i in range(len(cols)))} FROM cypher('{age.graph}', $cy$ "
           f"{q2.replace('%', '%%')} $cy$, %s) AS ({spec}) ORDER BY {sort} LIMIT {limit}")
    rows = age.sql(sql, (json.dumps(params, ensure_ascii=False),))
    return cols, [A.AgeRecord(cols, [A.parse_agtype(x) for x in row]) for row in rows]


REWRITES = [
    {"id": "index-ddl", "kind": "mechanical", "match": r"CREATE\s+INDEX\b.*\bFOR\s*\(", "apply": _apply_index,
     "proposal": "Cypher 인덱스 DDL 대신 SQL: `create_vlabel(g,'L')` 후 `CREATE INDEX … ON g.\"L\" USING btree "
                 "(agtype_access_operator(VARIADIC ARRAY[properties, '\"p\"'::agtype]))` + 속성맵 MATCH용 `USING gin (properties)`"},
    {"id": "agg-orderby", "kind": "mechanical", "match": lambda q: _agg_order_clause(q) is not None,
     "transform": _split_agg_order,
     "proposal": "집계 별칭을 같은 절에서 ORDER BY 하지 말고 절을 하나 나눈다: `WITH p, count(e) AS cnt WITH p, cnt ORDER BY cnt`"},
    {"id": "keyword-alias", "kind": "mechanical", "match": r"\bAS\s+count\b",
     "transform": lambda q: re.sub(r"\bAS\s+count\b", "AS `count`", q),
     "proposal": "AGE 문법에서 `count`는 예약어 — 별칭을 백틱으로: ``cnt AS `count` ``"},
    {"id": "unwind-rebind", "kind": "mechanical", "match": r"UNWIND\s+\w+\s+AS\s+(\w+)\s+(?:OPTIONAL\s+)?MATCH\s+\(\1\b",
     "transform": _rebind_unwind,
     "proposal": "UNWIND로 받은 변수를 MATCH 패턴에 다시 쓰면 DuplicateAlias — 새 변수로 받고 `WHERE id(a_u) = id(a)`로 잇는다"},
    {"id": "list-predicate", "kind": "manual", "match": r"WHERE\s+all\(\s*\w+\s+IN\b", "transform": _list_predicate,
     "proposal": "리스트 술어 `all(n IN nodes(p)[1..] WHERE c)` 미지원(리스트 컴프리헨션 안 속성 접근도 실패) → "
                 "`WITH p, a UNWIND nodes(p)[1..] AS n WITH p, a, sum(CASE WHEN c THEN 0 ELSE 1 END) AS bad WHERE bad = 0` "
                 "— 묶음 키에 시작 노드까지 넣으면 AGE가 메모리 6GB↑로 강제 종료(실측), 맞는 형태도 예수 기준 ~20초"},
    {"id": "collect-map", "kind": "manual", "match": r"collect\(\{.+?\}\)\[0\.\.\d+\]", "apply": _apply_collect_zip,
     "proposal": "노드+리스트를 담은 맵을 ~80개 넘게 collect하면 AGE 내부 오류(`unknown type of agtype container`) → "
                 "키마다 병렬 `collect(m), collect(rel), collect(mlabels)` 후 앱에서 zip"},
    {"id": "call-subquery", "kind": "manual", "match": r"\bCALL\s*\([^)]*\)\s*\{", "apply": _apply_split_call,
     "proposal": "`CALL (r, k) { … }` 서브쿼리 미지원 → 서브쿼리마다 `MATCH (r …), (k …) MATCH … MERGE …` 독립 문장으로 쪼개 "
                 "차례 실행 후 `DETACH DELETE`(한 트랜잭션으로 묶을 것). `NOT (b)-[…]->(k)` 패턴 술어는 `NOT EXISTS((b)-[…]->(k))`"},
    {"id": "string-order", "kind": "manual", "match": r"ORDER\s+BY\s+\w+\s*,\s*\w+\.\w+\s+LIMIT", "apply": _apply_sql_order,
     "proposal": "AGE는 agtype 문자열을 neo4j(코드포인트 사전순)와 다르게 정렬한다 → 문자열 정렬을 cypher() 밖 SQL로: "
                 "`… AS (…, k agtype) ORDER BY k::text COLLATE \"C\" LIMIT n`"},
    {"id": "counters", "kind": "mechanical", "match": r"$^",
     "proposal": "AGE엔 쓰기 카운터(summary.counters)가 없다 → 쓰기 끝에 `RETURN count(p)`를 붙여 그 값을 센다"},
]
COUNTERS_RW = REWRITES[-1]
_RW = {rw["id"]: rw for rw in REWRITES}


def find_rewrite(q):
    for rw in REWRITES:
        if rw["match"](q) if callable(rw["match"]) else re.search(rw["match"], q, re.S):
            return rw
    return None


# ================================================================ 비교·분류

def _deep_sort(v):
    if isinstance(v, list):
        return sorted((_deep_sort(x) for x in v), key=lambda x: json.dumps(x, sort_keys=True, ensure_ascii=False))
    if isinstance(v, dict):
        return {k: _deep_sort(x) for k, x in v.items()}
    return v


def compare(a, b):
    """'same' | 'order'(순서만 다름 — 리스트를 깊이 정렬하면 같다) | 'diff'."""
    if a == b:
        return "same"
    return "order" if _deep_sort(a) == _deep_sort(b) else "diff"


def diff_summary(a, b):
    if isinstance(a, list) and isinstance(b, list) and len(a) != len(b):
        return f"행 수 neo4j {len(a)} vs AGE {len(b)}"
    sa, sb = _deep_sort(a), _deep_sort(b)
    if isinstance(sa, list) and isinstance(sb, list):
        for x, y in zip(sa, sb):
            if x != y:
                return f"첫 차이 neo4j {_short(x)} vs AGE {_short(y)}"
    return f"neo4j {_short(a)} vs AGE {_short(b)}"


def _short(v, n=160):
    s = json.dumps(v, ensure_ascii=False, sort_keys=True)
    return s if len(s) <= n else s[:n] + "…"


CLASSES = ["그대로 통과", "순서만 다름", "기계적 치환", "막힘"]


def classify(entry, base_rows):
    """한 호출 → (분류, 오류·차이, 재작성안). base_rows = 같은 호출의 neo4j 결과(없으면 None)."""
    q = entry["query"]
    if "age_error" in entry:
        rw = find_rewrite(q)
        return "막힘", entry["age_error"], rw["proposal"] if rw else ""
    if entry.get("rewrite"):
        rws = [_RW[i] for i in entry["rewrite"]]
        proposal = " / ".join(rw["proposal"] for rw in rws)
        c = compare(base_rows, entry.get("age_rows")) if base_rows is not None else None
        check = {None: "", "same": " (재작성 실행: neo4j와 일치)", "order": " (재작성 실행: 순서만 다르고 일치)"}.get(
            c, " (재작성 실행: 불일치 — " + (diff_summary(base_rows, entry.get("age_rows")) if c else "") + ")")
        if all(rw["kind"] == "mechanical" for rw in rws) and c != "diff":
            return "기계적 치환", entry["age_error_original"], proposal + check
        return "막힘", entry["age_error_original"], proposal + check
    if entry.get("counters_read"):
        return "기계적 치환", "result.consume().counters 를 읽음 — AGE는 0만 준다", COUNTERS_RW["proposal"]
    if base_rows is None:
        return "그대로 통과", "", ""
    c = compare(base_rows, entry.get("age_rows"))
    if c == "same":
        return "그대로 통과", "", ""
    if c == "order":
        return "순서만 다름", "ORDER BY 없는 결과(또는 collect)의 순서 차이", ""
    rw = find_rewrite(q)
    check = {"same": " (재작성 실행: neo4j와 일치)", "order": " (재작성 실행: 순서만 다르고 일치)"}.get(
        entry.get("rewrite_check"), f" (재작성 실행: {entry['rewrite_check']})" if entry.get("rewrite_check") else "")
    return "막힘", "결과 불일치: " + diff_summary(base_rows, entry.get("age_rows")), (rw["proposal"] + check) if rw else ""


def selftest():
    rows = [{"id": "a", "n": 1}, {"id": "b", "n": 2}]
    cases = [
        ("값 하나 다름", {"query": "MATCH (n) RETURN n.id AS id, n.n AS n", "age_rows": [{"id": "a", "n": 1}, {"id": "b", "n": 3}]}, "막힘"),
        ("순서만 다름", {"query": "MATCH (n) RETURN n.id AS id, n.n AS n", "age_rows": list(reversed(rows))}, "순서만 다름"),
        ("한쪽 오류", {"query": "MATCH (n) RETURN n.id AS id, n.n AS n", "age_error": "SyntaxError: x"}, "막힘"),
    ]
    ok = True
    for name, entry, want in cases:
        got = classify(entry, rows)[0]
        print(f"  {'✓' if got == want else '✗'} {name}: {got} (기대 {want})")
        ok &= got == want
    same = classify({"query": "RETURN 1", "age_rows": rows}, rows)[0]
    print(f"  {'✓' if same == '그대로 통과' else '✗'} 같은 결과: {same}")
    ok &= same == "그대로 통과"
    return 0 if ok else 1


# ================================================================ 정적 호출 지점·커버리지

def static_sites():
    sites = []
    for sub in ("backend/app", "backend/scripts"):
        for root, _, files in os.walk(os.path.join(REPO, sub)):
            for f in sorted(files):
                if not f.endswith(".py"):
                    continue
                path = os.path.join(root, f)
                with open(path, encoding="utf-8") as fh:
                    for i, line in enumerate(fh, 1):
                        if re.search(r"\.run\(", line) and "subprocess.run" not in line:
                            sites.append(f"{os.path.relpath(path, REPO)}:{i}")
    return sorted(sites)


def coverage():
    sites = static_sites()
    rows = {}
    blanks = 0
    with open(REPORT, encoding="utf-8") as f:
        section = None
        for line in f:
            if line.startswith("## "):
                section = line.strip()
            if not line.startswith("| backend/"):
                continue
            cells = [c.strip() for c in re.split(r"(?<!\\)\|", line.strip())[1:-1]]
            if "호출 지점 표" in (section or ""):
                rows[cells[0]] = cells
            # 막힘·기계적 치환 행: 파일:줄 · 구문 · 오류(차이) · 재작성안 네 칸
            if "막힌 구문" in (section or "") or "기계적 치환" in (section or ""):
                blanks += sum(1 for c in cells[:4] if not c)
            elif "호출 지점 표" in (section or "") and cells[1] in ("막힘", "기계적 치환"):
                blanks += sum(1 for i in (0, 3, 4, 5) if not cells[i])
    missing = [s for s in sites if s not in rows]
    extra = [s for s in rows if s not in sites]
    print(f"호출 지점 {len(sites)} · 보고서 행 {len(rows)} · 누락 {len(missing)}")
    print(f"막힘·기계적 치환 행 빈 칸 {blanks}")
    for s in missing:
        print("  누락:", s)
    for s in extra:
        print("  정적 목록에 없는 행:", s)
    return 0 if not missing and not extra and blanks == 0 else 1


# ================================================================ 탐침: 실제 실행에서 한 번도 안 불린 지점

def _literal_call(site):
    """'파일:줄'의 `.run(` 호출 → (쿼리 리터럴, 키워드 인자 이름들) | None (f-string·변수면 None)."""
    import ast
    path, line = site.rsplit(":", 1)
    with open(os.path.join(REPO, path), encoding="utf-8") as f:
        tree = ast.parse(f.read())
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and getattr(node.func, "attr", None) == "run" and node.lineno == int(line) \
                and node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
            return node.args[0].value, [k.arg for k in node.keywords if k.arg]
    return None


def probe(sites):
    """데이터에 해당 항목이 없어 실제 체인·API에서 안 불린 지점 — 소스의 쿼리 리터럴을 꺼내 가짜 인자로
    neo4j·AGE 양쪽에서 실행하고 둘 다 롤백한다(그래프 무변경). 실제 코드 경로가 아니므로 출처를 '탐침'으로 적는다."""
    from neo4j import GraphDatabase
    out = []
    with GraphDatabase.driver(NEO_URI, auth=NEO_AUTH) as d:
        for site in sites:
            lit = _literal_call(site)
            if not lit:
                continue
            q, keys = lit
            params = {k: "agecheck-probe" for k in keys}
            entry = {"site": site, "query": q, "ctx": "탐침"}
            with d.session() as s:
                tx = s.begin_transaction()
                entry["neo_rows"] = A.norm_records(list(tx.run(q, params)))
                tx.rollback()
            age = A.AgeBackend("biblemap")
            age.conn.autocommit = False
            try:
                _, recs = age.cypher(q, params)
                entry["age_rows"] = A.norm_records(recs)
            except Exception as e:  # noqa: BLE001 — 기록
                entry["age_error"] = A._err(e)
            age.conn.rollback()
            age.conn.close()
            out.append(entry)
    return out


# ================================================================ 하위 프로세스: 스크립트 1개 실행

def _jsonl_logger(path, ctx):
    ordinals = collections.Counter()

    def log(entry):
        ordinals[entry["site"]] += 1
        entry["ordinal"] = ordinals[entry["site"]]
        entry["ctx"] = ctx
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
    return log


def _set_env():
    os.environ.update(NEO4J_URI=NEO_URI, NEO4J_USER=NEO_AUTH[0], NEO4J_PASSWORD=NEO_AUTH[1])


def sub_script(name, backend, graph, log_path, data_dir):
    _set_env()
    scripts = os.path.join(REPO, "backend", "scripts")
    sys.path.insert(0, scripts)
    log = _jsonl_logger(log_path, name)
    if backend == "neo":
        A.install(neo_uri=NEO_URI, neo_auth=NEO_AUTH, primary="neo", log=log)
    else:
        A.install(age_graph=graph, primary="age", log=log, rewrites=REWRITES)
    path = os.path.join(scripts, name + ".py")
    sys.argv = [path]
    if name == "apply_event_dedupe":  # data/ 를 고쳐 쓰는 스크립트 — 임시 사본에서 돌린다
        import importlib
        mod = importlib.import_module(name)
        mod.DATA_DIR, mod.LEDGER_PATH = data_dir, os.path.join(data_dir, "event_dedupe", "dedupe.json")
        mod.main()
    elif name == "generate_book_events":  # DB 부분(load_events)만 — LLM 호출·파일 쓰기는 점검 대상이 아니다
        import importlib
        importlib.import_module(name).load_events()
    else:
        try:
            runpy.run_path(path, run_name="__main__")
        except SystemExit as e:  # 검증 스크립트의 위반 exit 1 은 결과일 뿐
            print(f"[age_compat] exit {e.code}")


# ================================================================ 하위 프로세스: API

def sub_api(mode, log_path, out_path):
    _set_env()
    sys.path.insert(0, REPO)
    log = _jsonl_logger(log_path, "api") if log_path else None
    if mode == "dual":
        A.install(neo_uri=NEO_URI, neo_auth=NEO_AUTH, age_graph="biblemap", primary="neo", log=log, rewrites=REWRITES,
                  compare=compare)
    elif mode == "neo":
        A.install(neo_uri=NEO_URI, neo_auth=NEO_AUTH, primary="neo", log=log)
    else:
        A.install(age_graph="biblemap", primary="age", log=log, rewrites=REWRITES)
    import logging
    logging.disable(logging.CRITICAL)
    from fastapi.testclient import TestClient
    from backend.app.main import app
    out = {}
    with TestClient(app, raise_server_exceptions=False) as c:
        for ep in ENDPOINTS:
            path = ep.format(**IDS)
            t = time.perf_counter()
            r = c.get(path)
            ms = (time.perf_counter() - t) * 1000
            try:
                body = r.json()
            except ValueError:
                body = r.text
            out[ep] = {"status": r.status_code, "ms": ms, "body": body}
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False)


# ================================================================ 오케스트레이션

def sh(cmd, **kw):
    return subprocess.run(cmd, check=True, text=True, capture_output=True, **kw).stdout


def wait_ready():
    from neo4j import GraphDatabase
    import psycopg
    for _ in range(90):
        try:
            with GraphDatabase.driver(NEO_URI, auth=NEO_AUTH) as d:
                d.verify_connectivity()
            psycopg.connect(A.AGE_CONNINFO).close()
            age = A.AgeBackend("probe")
            age.conn.close()
            return
        except Exception:  # noqa: BLE001 — 기동 대기
            time.sleep(2)
    raise RuntimeError("스택 기동 대기 시간 초과")


def run_sub(args, timeout=3600):
    t = time.perf_counter()
    p = subprocess.run([sys.executable, __file__, *args], text=True, capture_output=True, timeout=timeout)
    return p, time.perf_counter() - t


def export_neo():
    from neo4j import GraphDatabase
    with GraphDatabase.driver(NEO_URI, auth=NEO_AUTH) as d, d.session() as s:
        nodes = [(r["id"], r["labels"], r["props"]) for r in
                 s.run("MATCH (n) RETURN elementId(n) AS id, labels(n) AS labels, properties(n) AS props")]
        rels = [(r["a"], r["b"], r["t"], r["props"]) for r in
                s.run("MATCH (a)-[r]->(b) RETURN elementId(a) AS a, elementId(b) AS b, type(r) AS t, properties(r) AS props")]
    return nodes, rels


def export_age(graph):
    age = A.AgeBackend(graph)
    _, nrecs = age.cypher("MATCH (n) RETURN id(n) AS id, n", {})
    _, rrecs = age.cypher("MATCH (a)-[r]->(b) RETURN id(a) AS a, id(b) AS b, r", {})
    nodes = [(str(r["id"]), sorted(r["n"].labels), dict(r["n"])) for r in nrecs]
    rels = [(str(r["a"]), str(r["b"]), r["r"].type, dict(r["r"])) for r in rrecs]
    age.conn.close()
    return nodes, rels


def copy_to_age(nodes, rels, graph="biblemap"):
    """기준 neo4j 그래프를 AGE로 노드·관계 그대로 복사(라벨 테이블에 SQL INSERT)."""
    age = A.AgeBackend(graph)
    multi = [n for n in nodes if len(n[1]) != 1]
    idmap = {}
    by_label = collections.defaultdict(list)
    for nid, labels, props in nodes:
        by_label[labels[0] if labels else "_unlabeled"].append((nid, props))
    for label, items in by_label.items():
        age.ensure_vlabel(label)
        with age.conn.cursor() as cur:
            cur.executemany(f'INSERT INTO "{graph}"."{label}" (properties) VALUES (%s::agtype) RETURNING id',
                            [(json.dumps(p, ensure_ascii=False),) for _, p in items], returning=True)
            for (nid, _), gid in zip(items, _results(cur)):
                idmap[nid] = gid
    by_type = collections.defaultdict(list)
    for a, b, t, props in rels:
        by_type[t].append((idmap[a], idmap[b], json.dumps(props, ensure_ascii=False)))
    for t, items in by_type.items():
        if not age.sql("SELECT 1 FROM ag_label l JOIN ag_graph g ON l.graph = g.graphid WHERE g.name=%s AND l.name=%s",
                       (graph, t)):
            age.sql("SELECT create_elabel(%s, %s)", (graph, t))
        with age.conn.cursor() as cur:
            cur.executemany(f'INSERT INTO "{graph}"."{t}" (start_id, end_id, properties) '
                            f"VALUES (%s::graphid, %s::graphid, %s::agtype)", items)
    age.conn.close()
    return multi


def _results(cur):
    while True:
        yield cur.fetchone()[0]
        if not cur.nextset():
            break


def graph_tally(nodes, rels):
    """라벨별·관계 유형별 개수 + 내용 지문(theographic_id 기준) — 기준 vs 재생 대조용."""
    key_of = {nid: (labels[0] if labels else "", props.get("theographic_id")) for nid, labels, props in nodes}
    node_fp = collections.Counter(
        json.dumps([labels, A.norm(props)], sort_keys=True, ensure_ascii=False) for _, labels, props in nodes)
    rel_fp = collections.Counter(
        json.dumps([t, key_of[a], key_of[b], A.norm(p)], sort_keys=True, ensure_ascii=False) for a, b, t, p in rels)
    return {
        "labels": collections.Counter(labels[0] if labels else "" for _, labels, _ in nodes),
        "types": collections.Counter(t for _, _, t, _ in rels),
        "node_fp": node_fp, "rel_fp": rel_fp,
    }


def read_jsonl(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return [json.loads(x) for x in f]


def main():
    work = tempfile.mkdtemp(prefix="biblemap-agecheck-")
    data_neo, data_age = os.path.join(work, "data-neo"), os.path.join(work, "data-age")
    for d in (data_neo, data_age):
        shutil.copytree(os.path.join(REPO, "data"), d)
    started = datetime.datetime.now()
    meta = {"scripts": {}, "phases": {}}
    try:
        print("[1/6] 일회용 스택 기동 (biblemap-agecheck)…", flush=True)
        sh(COMPOSE + ["down", "-v", "--remove-orphans"])  # 이전 실행 잔여물이 있으면 깨끗이 — 그래프가 겹치지 않게
        sh(COMPOSE + ["up", "-d"])
        wait_ready()
        from neo4j import GraphDatabase
        with GraphDatabase.driver(NEO_URI, auth=NEO_AUTH) as d, d.session() as s:
            meta["neo_version"] = s.run("CALL dbms.components() YIELD versions RETURN versions[0] AS v").single()["v"]
        age = A.AgeBackend("probe")
        meta["age_version"] = age.sql("SELECT extversion FROM pg_extension WHERE extname='age'")[0][0]
        meta["pg_version"] = age.sql("SHOW server_version")[0][0]
        age.conn.close()

        base_log, replay_log = os.path.join(work, "base.jsonl"), os.path.join(work, "replay.jsonl")
        print("[2/6] 기준 neo4j 적재 체인…", flush=True)
        for name in LOAD_CHAIN:
            p, sec = run_sub(["_script", name, "--backend", "neo", "--log", base_log, "--data", data_neo])
            meta["scripts"].setdefault(name, {})["neo"] = {"rc": p.returncode, "sec": sec, "out": p.stdout[-4000:],
                                                          "err": p.stderr[-4000:]}
            print(f"      {name}: rc={p.returncode} {sec:.1f}s", flush=True)

        print("[3/6] 기준 그래프 → AGE `biblemap` 복사…", flush=True)
        t = time.perf_counter()
        base_nodes, base_rels = export_neo()
        meta["multi_label"] = len(copy_to_age(base_nodes, base_rels))
        meta["phases"]["copy"] = time.perf_counter() - t

        print("[4/6] 적재 체인 AGE `biblemap_loaders` 재생…", flush=True)
        for name in LOAD_CHAIN:
            p, sec = run_sub(["_script", name, "--backend", "age", "--graph", "biblemap_loaders", "--log", replay_log,
                              "--data", data_age])
            meta["scripts"][name]["age"] = {"rc": p.returncode, "sec": sec, "out": p.stdout[-4000:],
                                            "err": p.stderr[-4000:]}
            print(f"      {name}: rc={p.returncode} {sec:.1f}s", flush=True)
        replay_nodes, replay_rels = export_age("biblemap_loaders")
        tallies = (graph_tally(base_nodes, base_rels), graph_tally(replay_nodes, replay_rels))

        print("[5/6] API 대조 (dual · neo4j 단독 · AGE 단독)…", flush=True)
        api_log = os.path.join(work, "api.jsonl")
        outs = {}
        for mode in ("dual", "neo", "age"):
            out = os.path.join(work, f"api-{mode}.json")
            p, sec = run_sub(["_api", mode, "--log", api_log if mode == "dual" else "", "--out", out])
            meta["phases"][f"api-{mode}"] = sec
            if p.returncode != 0:
                raise RuntimeError(f"API {mode} 실패:\n{p.stderr[-3000:]}")
            with open(out, encoding="utf-8") as f:
                outs[mode] = json.load(f)
            print(f"      {mode}: {sec:.1f}s", flush=True)

        executed = {e["site"] for e in read_jsonl(replay_log) + read_jsonl(api_log)}
        probes = probe([s for s in static_sites() if s not in executed])

        print("[6/6] 보고서 작성…", flush=True)
        data_drift = sh(["git", "-C", REPO, "status", "--porcelain", "--", "data"]).strip()
        write_report(meta, read_jsonl(base_log), read_jsonl(replay_log), read_jsonl(api_log) + probes, tallies, outs,
                     started, data_drift)
        print(f"      → {os.path.relpath(REPORT, os.getcwd())}")
    finally:
        if os.environ.get("AGECHECK_KEEP"):  # 디버깅용: 스택과 작업 파일을 남긴다(끝나면 손으로 down -v)
            print(f"[정리 생략] AGECHECK_KEEP — 작업 파일 {work}", flush=True)
        else:
            print("[정리] down -v …", flush=True)
            subprocess.run(COMPOSE + ["down", "-v", "--remove-orphans"], capture_output=True)
            shutil.rmtree(work, ignore_errors=True)
    return 0


# ================================================================ 보고서

def _cell(s, n=None):
    s = re.sub(r"\s+", " ", str(s or "")).strip().replace("|", "\\|")
    return s if n is None or len(s) <= n else s[:n] + "…"


def write_report(meta, base, replay, api, tallies, outs, started, data_drift):
    sites = static_sites()
    per_site = collections.defaultdict(list)  # site → [(분류, 오류, 재작성안, query, 출처)]
    counts = collections.Counter()

    # 스크립트 재생: (스크립트, 지점, 순번)으로 기준과 맞춘다
    base_idx = {(e["ctx"], e["site"], e["ordinal"]): e for e in base}
    for e in replay:
        b = base_idx.get((e["ctx"], e["site"], e["ordinal"]))
        cls = classify(e, b["neo_rows"] if b else None)
        per_site[e["site"]].append((*cls, e["query"], f"재생:{e['ctx']}"))
        counts[e["site"]] += 1
    for e in api:  # dual: 같은 호출을 양쪽에서 — 기준은 그 호출의 neo4j 결과. 탐침도 같은 모양
        cls = classify(e, e.get("neo_rows"))
        per_site[e["site"]].append((*cls, e["query"], "탐침" if e["ctx"] == "탐침" else "API"))
        counts[e["site"]] += 1

    rank = {c: i for i, c in enumerate(CLASSES)}
    site_rows, blocked, mech = [], [], []
    for s in sites:
        hits = per_site.get(s)
        if not hits:
            site_rows.append((s, "미실행", 0, "", "", ""))
            continue
        worst = max(hits, key=lambda h: rank[h[0]])
        n = f"{counts[s]} (탐침)" if all(h[4] == "탐침" for h in hits) else counts[s]
        site_rows.append((s, worst[0], n, worst[3], worst[1], worst[2]))
        seen = set()
        for h in hits:  # 같은 지점의 같은 재작성(라벨만 다른 인덱스 DDL 등)은 한 행으로
            key = (h[0], h[2][:60] or h[1][:80])
            if h[0] in ("막힘", "기계적 치환") and key not in seen:
                seen.add(key)
                (blocked if h[0] == "막힘" else mech).append((s, h[3], h[1], h[2], h[4]))
    tally = collections.Counter(r[1] for r in site_rows)
    if tally["막힘"]:
        verdict = "막힘"
    elif tally["미실행"]:
        verdict = "미판정"
    else:
        verdict = "통과"

    base_t, rep_t = tallies
    L = []
    L.append("# BibleMap Cypher × Apache AGE 호환성 점검 (task#340)")
    L.append("")
    L.append(f"판정: {verdict}")
    L.append("")
    L.append(f"- 실행: {started:%Y-%m-%d %H:%M} · 기준 neo4j {meta['neo_version']} · AGE {meta['age_version']} / "
             f"PostgreSQL {meta['pg_version']} · 재실행 `python3 scripts/age_compat/run_check.py`")
    L.append(f"- 호출 지점 {len(sites)}: " + " · ".join(f"{c} {tally[c]}" for c in CLASSES + ["미실행"]))
    slow = [(ep, outs["age"][ep]["ms"], outs["neo"][ep]["ms"]) for ep in ENDPOINTS
            if outs["age"][ep]["ms"] >= 10 * max(outs["neo"][ep]["ms"], 1)]
    if slow:
        worst = max(slow, key=lambda x: x[1])
        L.append(f"- 지연(판정 무관): AGE가 10배 이상 느린 엔드포인트 {len(slow)}/{len(ENDPOINTS)} — 최악 `{worst[0]}` "
                 f"{worst[1] / 1000:.1f}s (neo4j {worst[2]:.0f}ms)")
    L.append("- 판정 규칙: 막힘 0 · 미실행 0 → 통과 / 막힘 ≥1 → 막힘 / 막힘 0인데 미실행 ≥1 → 미판정")
    L.append("")
    L.append("## 막힌 구문 목록")
    L.append("")
    L.append("| 파일:줄 | 구문 | AGE 오류(또는 차이) | 재작성안 | 어디서 |")
    L.append("|---|---|---|---|---|")
    for s, q, err, rw, src in blocked:
        L.append(f"| {s} | `{_cell(q, 220)}` | {_cell(err, 260)} | {_cell(rw)} | {src} |")
    if not blocked:
        L.append("| (없음) | | | | |")
    L.append("")
    L.append("## 기계적 치환")
    L.append("")
    L.append("| 파일:줄 | 구문 | AGE 오류(또는 차이) | 재작성안 | 어디서 |")
    L.append("|---|---|---|---|---|")
    for s, q, err, rw, src in mech:
        L.append(f"| {s} | `{_cell(q, 220)}` | {_cell(err, 260)} | {_cell(rw)} | {src} |")
    L.append("")
    L.append("## 호출 지점 표")
    L.append("")
    L.append("분류는 그 지점의 실행 중 가장 나쁜 것. 실행 수 = AGE 재생 + API(dual) 호출 수.")
    L.append("")
    L.append("| 파일:줄 | 분류 | 실행 수 | 구문 | AGE 오류(또는 차이) | 재작성안 |")
    L.append("|---|---|---|---|---|---|")
    for s, cls, n, q, err, rw in site_rows:
        L.append(f"| {s} | {cls} | {n} | `{_cell(q, 140)}` | {_cell(err, 200)} | {_cell(rw)} |")
    L.append("")
    L.append("## 적재 스크립트 재생")
    L.append("")
    L.append("| 스크립트 | neo4j rc · 초 | AGE rc · 초 | 출력 일치 | AGE 오류 꼬리 |")
    L.append("|---|---|---|---|---|")
    for name in LOAD_CHAIN:
        sc = meta["scripts"].get(name, {})
        n, a = sc.get("neo", {}), sc.get("age", {})
        same = _out_same(n.get("out"), a.get("out"))
        if same == "아니오" and any(e.get("counters_read") for e in replay if e["ctx"] == name):
            same += " (쓰기 카운터 0 — 갱신 수 출력이 다름)"
        tail = (a.get("err") or "").strip().splitlines()[-1:] if a.get("rc") else []
        L.append(f"| {name} | {n.get('rc')} · {n.get('sec', 0):.1f} | {a.get('rc')} · {a.get('sec', 0):.1f} | {same} | "
                 f"{_cell(tail[0] if tail else '', 200)} |")
    L.append("")
    L.append("## 개수 대조 (기준 neo4j ↔ AGE 재생 그래프 `biblemap_loaders`)")
    L.append("")
    L.append("| 종류 | 이름 | neo4j | AGE | 차 |")
    L.append("|---|---|---|---|---|")
    for kind, key in (("노드", "labels"), ("관계", "types")):
        for name in sorted(set(base_t[key]) | set(rep_t[key])):
            a, b = base_t[key][name], rep_t[key][name]
            L.append(f"| {kind} | {name} | {a} | {b} | {b - a:+d} |")
    nd = sum(((base_t["node_fp"] - rep_t["node_fp"]) + (rep_t["node_fp"] - base_t["node_fp"])).values())
    rd = sum(((base_t["rel_fp"] - rep_t["rel_fp"]) + (rep_t["rel_fp"] - base_t["rel_fp"])).values())
    L.append("")
    L.append(f"내용 지문(라벨+전체 속성 / 유형+양끝 theographic_id+속성) 대칭차: 노드 {nd} · 관계 {rd}. "
             f"다중 라벨 노드(AGE는 라벨 1개): {meta.get('multi_label', 0)}.")
    for title, fp in (("노드", "node_fp"), ("관계", "rel_fp")):
        only_b = list((base_t[fp] - rep_t[fp]).elements())[:3]
        only_r = list((rep_t[fp] - base_t[fp]).elements())[:3]
        for x in only_b:
            L.append(f"- {title} neo4j에만: `{_cell(x, 240)}`")
        for x in only_r:
            L.append(f"- {title} AGE에만: `{_cell(x, 240)}`")
    L.append("")
    L.append("## 엔드포인트 대조 · 지연")
    L.append("")
    L.append("앱을 neo4j 단독·AGE 단독으로 각각 띄워 같은 요청의 JSON을 비교. 지연은 기록만(판정 무관), AGE가 10배 이상 느리면 `느림`.")
    L.append("")
    L.append("| 엔드포인트 | 상태 neo4j/AGE | JSON | neo4j ms | AGE ms | 비고 |")
    L.append("|---|---|---|---|---|---|")
    for ep in ENDPOINTS:
        n, a = outs["neo"][ep], outs["age"][ep]
        c = compare(n["body"], a["body"]) if n["status"] == a["status"] else "diff"
        label = {"same": "같음", "order": "순서만 다름", "diff": "다름"}[c]
        slow = "느림" if a["ms"] >= 10 * max(n["ms"], 1) else ""
        note = diff_summary(n["body"], a["body"]) if c == "diff" else ""
        if c == "diff" and ep.startswith("/node/") and _shape(n["body"]) == _shape(a["body"]):
            # 노드 이웃은 앱이 ORDER BY 없는 결과를 상한(50·유형별 30)에서 자른다 — 어느 엔진이든 고르는 원소가 비결정.
            # 총수·길이·나머지 필드가 같으면 그 절단 차이일 뿐이다.
            label, note = "다름(상한 절단)", "ORDER BY 없는 이웃을 상한에서 자름 — 총수·길이·나머지 필드 같음, 고른 원소만 다름"
        L.append(f"| `{ep}` | {n['status']}/{a['status']} | {label} | {n['ms']:.0f} | {a['ms']:.0f} | "
                 f"{_cell(' '.join(x for x in (slow, note) if x), 200)} |")
    L.append("")
    L.append("## 점검 범위와 한계")
    L.append("")
    L.append("- 앱·스크립트 코드는 고치지 않았다. `neo4j.GraphDatabase.driver`를 바꿔치기한 어댑터(`age_adapter.py`)가 "
             "같은 코드를 AGE에서 돌린다 — 이전 시 실제 드라이버(psycopg + `cypher()` 감싸기)도 같은 일을 해야 한다.")
    L.append("- 탐침: 데이터에 해당 항목이 없어 실제 체인·API에서 한 번도 안 불린 지점은 소스의 쿼리 리터럴을 꺼내 가짜 인자"
             "(`'agecheck-probe'`)로 양쪽에서 실행 후 롤백했다 — 구문 호환성 증거이지 실제 데이터 경로 증거는 아니다. "
             "호출 지점 표에서는 실행 수 뒤에 `(탐침)`으로 표시한다.")
    L.append("- `apply_event_dedupe`는 `data/` 임시 사본에서, `generate_book_events`는 DB 부분(`load_events`)만 돌렸다(LLM 호출 제외).")
    L.append(f"- 점검 후 레포 `data/` 변경: {'없음' if not data_drift else _cell(data_drift)}.")
    L.append("- 결과 비교는 노드/관계를 (라벨·유형 + 속성)으로 정규화해 엔진 내부 id 차이를 무시한다. "
             "`순서만 다름` = 리스트를 깊이 정렬하면 같음(ORDER BY 없는 결과·collect 순서).")
    with open(REPORT, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")


def _shape(v):
    """리스트를 길이로 바꾼 구조 — 상한 절단(어느 원소를 골랐는지만 다름) 판별용."""
    if isinstance(v, list):
        return len(v)
    if isinstance(v, dict):
        return {k: _shape(x) if k != "neighbors" else len(x) for k, x in v.items()}
    return v


def _out_same(a, b):
    """스크립트 표준출력 비교 → '예' | '순서만 다름'(같은 토큰을 다른 순서로) | '아니오'."""
    a, b = (a or "").strip(), (b or "").strip()
    if a == b:
        return "예"
    tok = lambda s: sorted(re.findall(r"[^\s,\[\]'\"]+", s))  # noqa: E731
    return "순서만 다름" if tok(a) == tok(b) else "아니오"


# ================================================================ 진입

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--coverage", action="store_true")
    ap.add_argument("sub", nargs="*")
    ap.add_argument("--backend")
    ap.add_argument("--graph")
    ap.add_argument("--log")
    ap.add_argument("--data")
    ap.add_argument("--out")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    if a.coverage:
        sys.exit(coverage())
    if a.sub and a.sub[0] == "_script":
        sub_script(a.sub[1], a.backend, a.graph, a.log, a.data)
    elif a.sub and a.sub[0] == "_api":
        sub_api(a.sub[1], a.log, a.out)
    else:
        sys.exit(main())
