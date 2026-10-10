"""neo4j 드라이버 바꿔치기 — 같은 앱·스크립트 코드를 Apache AGE(또는 neo4j와 AGE 동시)에서 돌린다.

`install(...)`이 `neo4j.GraphDatabase.driver`를 갈아끼운다. 반환 드라이버의 `session.run`은
  - neo4j 쪽이 있으면 실제 neo4j에서 실행하고(결과는 정규화해 기록),
  - AGE 쪽이 있으면 같은 Cypher를 `ag_catalog.cypher(...)`로 감싸 실행한다.
`primary`가 호출자에게 돌려줄 쪽이다. primary='age'면 AGE 오류는 기록 후 그대로 던진다.
호출마다 호출 지점(backend/ 안의 파일:줄)·구문·정규화 결과·오류·지연을 `log`로 넘긴다.
판정은 여기서 하지 않는다 — run_check.py의 compare()/classify()가 기록을 읽어 한다.
"""
import inspect
import json
import os
import re
import time

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
BACKEND = os.path.join(REPO, "backend") + os.sep

AGE_CONNINFO = "host=127.0.0.1 port=15432 user=agecheck password=agecheck-pass dbname=agecheck"


# ---------------------------------------------------------------- agtype → 파이썬

class AgeNode(dict):
    """neo4j.graph.Node 흉내 — dict(n)·n["p"]·n.get·n.labels·n.element_id."""
    def __init__(self, v):
        super().__init__(v.get("properties") or {})
        self.labels = frozenset([v["label"]])
        self.element_id = str(v["id"])
        self.id = v["id"]


class AgeRel(dict):
    def __init__(self, v):
        super().__init__(v.get("properties") or {})
        self.type = v["label"]
        self.element_id = str(v["id"])
        self.start_id, self.end_id = v["start_id"], v["end_id"]


class AgePath(list):
    @property
    def nodes(self):
        return [x for x in self if isinstance(x, AgeNode)]

    @property
    def relationships(self):
        return [x for x in self if isinstance(x, AgeRel)]


def _hook(d):
    t = d.get("__agt__")
    if t == "vertex":
        return AgeNode(d["v"])
    if t == "edge":
        return AgeRel(d["v"])
    if t == "path":
        return AgePath(d["v"])
    return d


def parse_agtype(text):
    """agtype 텍스트(JSON + `::vertex`/`::edge`/`::path`/`::numeric` 꼬리표) → 파이썬 값.
    꼬리표 앞의 값을 {"__agt__": 종류, "v": 값}으로 감싼 JSON으로 바꾼 뒤 한 번에 읽는다."""
    if text is None:
        return None
    out, starts, last_start = [], [], 0
    i, n, in_str = 0, len(text), False
    while i < n:
        ch = text[i]
        if in_str:
            out.append(ch)
            if ch == "\\":
                out.append(text[i + 1])
                i += 1
            elif ch == '"':
                in_str = False
        elif ch == '"':
            in_str = True
            last_start = len(out)
            out.append(ch)
        elif ch in "{[":
            starts.append(len(out))
            out.append(ch)
        elif ch in "}]":
            out.append(ch)
            last_start = starts.pop()
        elif ch == ":" and text.startswith("::", i):
            m = re.match(r"::([a-z_]+)", text[i:])
            kind = m.group(1)
            i += len(m.group(0))
            if kind in ("vertex", "edge", "path"):
                val = "".join(out[last_start:])
                del out[last_start:]
                out.append('{"__agt__": "%s", "v": %s}' % (kind, val))
            continue  # numeric 등은 꼬리표만 버린다
        else:
            out.append(ch)
        i += 1
    return json.loads("".join(out), object_hook=_hook)


# ---------------------------------------------------------------- 정규화(비교용)

def norm(v):
    """neo4j/AGE 값 → 엔진 중립 JSON 값. 노드·관계는 라벨/유형 + 속성, 내부 id는 버린다."""
    t = type(v).__name__
    if isinstance(v, AgeNode) or t == "Node":
        return {"__node__": sorted(v.labels), "props": norm(dict(v))}
    if isinstance(v, AgeRel) or t == "Relationship":
        return {"__rel__": v.type, "props": norm(dict(v))}
    if isinstance(v, AgePath):
        return {"__path__": [norm(x) for x in v]}
    if t == "Path":
        seq = [v.nodes[0]]
        for r, nd in zip(v.relationships, v.nodes[1:]):
            seq += [r, nd]
        return {"__path__": [norm(x) for x in seq]}
    if isinstance(v, dict):
        return {k: norm(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [norm(x) for x in v]
    if isinstance(v, float):
        return round(v, 9)
    return v


def norm_records(records):
    return [{k: norm(r[k]) for k in r.keys()} for r in records]


# ---------------------------------------------------------------- Cypher → SQL

def _top_level_split(s, sep=","):
    parts, depth, cur, q = [], 0, [], None
    for ch in s:
        if q:
            cur.append(ch)
            if ch == q:
                q = None
            continue
        if ch in "'\"`":
            q = ch
        elif ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        if ch == sep and depth == 0:
            parts.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    parts.append("".join(cur))
    return parts


def _mask(q):
    """문자열 리터럴·괄호 안을 공백으로 지운 사본(길이 동일) — 최상위 키워드 찾기용."""
    out, depth, quote = [], 0, None
    for ch in q:
        if quote:
            out.append(" ")
            if ch == quote:
                quote = None
            continue
        if ch in "'\"`":
            quote = ch
            out.append(" ")
            continue
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
            out.append(" ")
            continue
        out.append(ch if depth == 0 else " ")
    return "".join(out)


def return_columns(q):
    """마지막 최상위 RETURN 절의 열 이름 목록. RETURN이 없으면 [] (쓰기 전용)."""
    masked = _mask(q)
    ms = list(re.finditer(r"\bRETURN\b", masked, re.I))
    if not ms:
        return []
    start = ms[-1].end()
    tail_masked = masked[start:]
    end = re.search(r"\b(ORDER\s+BY|SKIP|LIMIT|UNION)\b", tail_masked, re.I)
    body = q[start:start + end.start()] if end else q[start:]
    body = re.sub(r"^\s*DISTINCT\b", "", body, flags=re.I)
    cols = []
    for item in _top_level_split(body):
        item = item.strip()
        m = re.search(r"\s+AS\s+`?(\w+)`?\s*$", item, re.I)
        cols.append(m.group(1) if m else item)
    return cols


def _jsonable(v):
    if isinstance(v, (list, tuple, set, frozenset)):
        return [_jsonable(x) for x in v]
    if isinstance(v, dict):
        return {k: _jsonable(x) for k, x in v.items()}
    return v


class AgeBackend:
    def __init__(self, graph, conninfo=AGE_CONNINFO):
        self.graph, self.conninfo = graph, conninfo
        self.connect()
        if not self.conn.execute("SELECT 1 FROM ag_graph WHERE name = %s", (graph,)).fetchone():
            self.conn.execute("SELECT create_graph(%s)", (graph,))

    def connect(self):
        """(재)연결. 앞 쿼리가 AGE 서버 프로세스를 죽였으면(메모리 초과 등) 복구될 때까지 기다린다 —
        크래시 한 번이 뒤의 모든 호출을 '연결 끊김'으로 오염시키지 않게."""
        import psycopg
        for _ in range(60):
            try:
                self.conn = psycopg.connect(self.conninfo, autocommit=True)
                break
            except psycopg.OperationalError:
                time.sleep(1)
        self.conn.execute("LOAD 'age'")
        self.conn.execute('SET search_path = ag_catalog, "$user", public')

    def sql(self, sql, args=None):
        if self.conn.closed:
            self.connect()
        cur = self.conn.execute(sql, args)
        return cur.fetchall() if cur.description else []

    def cypher(self, q, params):
        cols = return_columns(q)
        spec = ", ".join(f"c{i} agtype" for i in range(max(len(cols), 1)))
        body = q.replace("%", "%%")
        sql = f"SELECT * FROM cypher('{self.graph}', $cy$ {body} $cy$, %s) AS ({spec})"
        rows = self.sql(sql, (json.dumps(_jsonable(params), ensure_ascii=False),))
        return cols, [AgeRecord(cols, [parse_agtype(x) for x in row]) for row in rows] if cols else []

    def ensure_vlabel(self, label):
        if not self.sql("SELECT 1 FROM ag_label l JOIN ag_graph g ON l.graph = g.graphid "
                        "WHERE g.name = %s AND l.name = %s", (self.graph, label)):
            self.sql("SELECT create_vlabel(%s, %s)", (self.graph, label))


# ---------------------------------------------------------------- 결과 흉내

class AgeRecord:
    def __init__(self, keys, values):
        self._keys, self._values = list(keys), list(values)

    def __getitem__(self, k):
        return self._values[k] if isinstance(k, int) else self._values[self._keys.index(k)]

    def get(self, k, default=None):
        return self[k] if k in self._keys else default

    def keys(self):
        return list(self._keys)

    def values(self):
        return list(self._values)

    def items(self):
        return list(zip(self._keys, self._values))

    def data(self):
        def plain(v):
            if isinstance(v, AgeNode):
                return dict(v)
            if isinstance(v, AgeRel):
                return ({}, v.type, {})
            if isinstance(v, list):
                return [plain(x) for x in v]
            if isinstance(v, dict):
                return {k: plain(x) for k, x in v.items()}
            return v
        return {k: plain(v) for k, v in self.items()}


class _Counters:
    """AGE에는 쓰기 카운터가 없다. 읽히면 그 호출에 표시하고 0을 준다."""
    def __init__(self, entry):
        self._entry = entry

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        self._entry["counters_read"] = True
        return 0


class _Summary:
    def __init__(self, counters):
        self.counters = counters


class FakeResult:
    def __init__(self, records, summary):
        self._records, self._summary = list(records), summary

    def __iter__(self):
        return iter(self._records)

    def single(self, strict=False):
        return self._records[0] if self._records else None

    def data(self, *keys):
        return [r.data() for r in self._records]

    def values(self):
        return [r.values() for r in self._records]

    def value(self, key=0, default=None):
        return [r[key] for r in self._records]

    def keys(self):
        return self._records[0].keys() if self._records else []

    def consume(self):
        return self._summary


# ---------------------------------------------------------------- 호출 지점 귀속

def caller_site():
    """backend/ 안의 가장 안쪽 프레임 → 'backend/…/x.py:줄'."""
    for fr in inspect.stack(context=0)[2:]:
        f = os.path.abspath(fr.filename)
        if f.startswith(BACKEND):
            return f"{os.path.relpath(f, REPO)}:{fr.lineno}"
    return "?"


# ---------------------------------------------------------------- 드라이버·세션

class Session:
    def __init__(self, drv):
        self.d = drv
        self.neo = drv.neo.session() if drv.neo else None

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()

    def close(self):
        if self.neo:
            self.neo.close()

    def run(self, query, parameters=None, **kw):
        params = {**(parameters or {}), **kw}
        entry = {"site": caller_site(), "query": query, "ctx": self.d.ctx}
        neo_recs = neo_res = age_recs = None
        if self.d.neo:
            t = time.perf_counter()
            neo_res = self.neo.run(query, params)
            neo_recs = list(neo_res)
            entry["neo_ms"] = (time.perf_counter() - t) * 1000
            entry["neo_rows"] = norm_records(neo_recs)
        if self.d.age:
            t = time.perf_counter()
            try:
                _, age_recs = self.d.age_run(query, params, entry)
                entry["age_rows"] = norm_records(age_recs)
            except Exception as e:  # noqa: BLE001 — 기록이 목적, primary=age면 아래에서 다시 던진다
                entry["age_error"] = _err(e)
                self.d.log(entry)
                if self.d.primary == "age":
                    raise
                age_recs = None
            entry["age_ms"] = (time.perf_counter() - t) * 1000
            if neo_recs is not None and age_recs is not None and "rewrite" not in entry and self.d.compare \
                    and self.d.compare(entry["neo_rows"], entry["age_rows"]) == "diff":
                # 오류 없이 결과만 다른 구문 — 맞는 재작성이 있으면 돌려 neo4j와 다시 대조(재작성안 검증)
                rws = self.d.matching(query)
                if rws:
                    try:
                        _, rr = rewrite_exec(self.d.age, query, params, rws)
                        entry["rewrite_check"] = self.d.compare(entry["neo_rows"], norm_records(rr))
                    except Exception as e:  # noqa: BLE001
                        entry["rewrite_check"] = "error: " + _err(e)
        if "age_error" not in entry:
            self.d.log(entry)
        if self.d.primary == "neo":
            return FakeResult(neo_recs, neo_res.consume())
        return FakeResult(age_recs, _Summary(_Counters(entry)))


class Driver:
    def __init__(self, neo=None, age=None, primary="neo", log=None, rewrites=None, ctx=None, compare=None):
        self.neo, self.age, self.primary, self.compare = neo, age, primary, compare
        self.log = log or (lambda e: None)
        self.rewrites = rewrites or []
        self.ctx = ctx

    def session(self, **kw):
        return Session(self)

    def close(self):
        if self.neo:
            self.neo.close()

    def verify_connectivity(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()

    def matching(self, q):
        return [rw for rw in self.rewrites
                if (rw["match"](q) if callable(rw["match"]) else re.search(rw["match"], q, re.S))]

    def age_run(self, q, params, entry):
        """AGE 실행. 실패하면 맞는 재작성(들)로 대신 돌린다(기록에 남김) — 재작성안이 실제로 도는지의 증거."""
        try:
            return self.age.cypher(q, params)
        except Exception as e:
            rws = self.matching(q)
            if not rws:
                raise
            first = _err(e)
            out = rewrite_exec(self.age, q, params, rws)
            entry["rewrite"], entry["age_error_original"] = [rw["id"] for rw in rws], first
            return out


def rewrite_exec(age, q, params, rws):
    """apply가 있는 재작성은 그것 하나로 실행, 아니면 transform들을 차례로 적용한 Cypher를 실행."""
    for rw in rws:
        if rw.get("apply"):
            return rw["apply"](age, q, params)
    for rw in rws:
        q = rw["transform"](q)
    return age.cypher(q, params)


def _err(e):
    return f"{type(e).__name__}: {str(e).strip().splitlines()[0]}"


def install(neo_uri=None, neo_auth=None, age_graph=None, primary="neo", log=None, rewrites=None, ctx=None,
            compare=None):
    """neo4j.GraphDatabase.driver를 바꿔치기한다. 이후 앱·스크립트가 만드는 드라이버는 전부 이것."""
    import neo4j
    real = neo4j.GraphDatabase.driver

    def fake(uri=None, auth=None, **kw):
        neo = real(neo_uri, auth=neo_auth) if neo_uri else None
        age = AgeBackend(age_graph) if age_graph else None
        return Driver(neo, age, primary, log, rewrites, ctx, compare)

    neo4j.GraphDatabase.driver = staticmethod(fake)
    return real
