#!/usr/bin/env python3
"""task#378 — 두 겹 판정 1/3: 명세 판정자(그림 전에 장면 명세를 성경 앞뒤 문맥에 비춤) + 두 판정자의 채점.

  python3 batch/judge_spec.py mutants                      # 변이 사본 5개 → samples/spec-judge/mutants/
  python3 batch/judge_spec.py run --key blind [--only <장면,…>] [--limit 1] [--workers 3]
  python3 batch/judge_spec.py run --key mutants --mutants  # 변이 사본에
  python3 batch/judge_spec.py score            # 원 답 → metrics 요약 + notes/SPEC-JUDGE.md 결과 절(판정 두 줄)
  python3 batch/judge_spec.py score --check    # 다시 계산해 metrics·notes와 대조(손 집계 방지) — 다르면 exit 1

규칙·정답·변이·이상한 점 라벨은 notes/SPEC-JUDGE.md 고정 절의 ```json fixed 블록(fixed()가 읽는다 — 손으로 옮기지 않음).
이상한 점 판정자의 답은 judge_items.py(머리말 o1, 문항 oddity)가 samples/judge-items/metrics.json에 쓴다 — 여기서는 채점만."""
import argparse, copy, fcntl, json, os, re, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import judge_items as J

HERE = J.HERE
sys.path.insert(0, HERE)
import check_scenes as CS
import derive_scene as D
import params

NOTE_MD = os.path.join(HERE, "notes", "SPEC-JUDGE.md")
OUT = os.path.join(HERE, "samples", "spec-judge")
METRICS = os.path.join(OUT, "metrics.json")
MUTANTS = os.path.join(OUT, "mutants")
BOOK_NAME = {"삼상": "사무엘상", "삼하": "사무엘하", "왕상": "열왕기상", "왕하": "열왕기하", "대상": "역대상", "대하": "역대하"}
KINDS = ("빠짐", "축약", "어긋남", "순간")
SKIP_KEYS = ("stages", "regions", "_regions_why", "judge", "_format", "negatives")
BEGIN, END = "<!-- spec-judge:begin -->", "<!-- spec-judge:end -->"

HEADER = """너는 성경 장면 명세를 검토하는 성경 고증가다. 아래 「장면 명세」는 그림 생성기와 그림 판정자가 함께 읽는 글이다. 이 명세가 「성경 본문」(고정한 순간의 절이 든 장 전체, 개역한글)을 빠짐없이·세밀하게·어긋남 없이 옮겼는지 본다.
지적 종류:
- 빠짐: 고정한 순간(moment)에 본문이 말하는 시각 요소(인물·무리·행동·지물·장소·때·상태)가 명세에 없다. 앞뒤 절이 그 순간에 함께 있다고 말하는 사람·물건·도움·세부도 포함한다.
- 축약: 명세에 있으나 본문보다 줄거나 흐려졌다(예: 본문 「침을 수염에 흘리매」 → 명세 「침을 흘린다」).
- 어긋남: 명세 칸끼리, 또는 한국어 칸과 영문 파생 문구가 서로 다르다(예: 자세 칸은 「칼을 빼지 않는다」인데 지물 칸은 뽑은 칼).
- 순간: 본문에 비추어, 고정한 순간보다 더 그 장면다운 순간이 있다(참고용).
규칙:
- 빠짐·축약·순간은 근거 절(verse, 예 "17:22")과 그 절 본문에서 **글자 그대로 옮긴** 짧은 인용(quote)을 적는다. 본문에 없는 말을 인용하지 마라.
- 어긋남은 quote 대신 field에 서로 어긋난 칸 두 개를 목록으로 적는다(예 ["moment.why", "figures[0].pose"]).
- 「본문 밖 · 저작자 정함」으로 적힌 칸은 본문이 그와 다르게 말할 때만 지적한다. verse_elements에서 out으로 적은(순간 밖) 요소는 지적하지 않는다.
- 그림 생성 모델이 그리기 어렵다는 이유로 무엇을 빼라고 하지 마라.
- 제안: 명세에 무엇을 어떻게 더하거나 고칠지 한두 문장.
- 지적할 것이 없으면 빈 목록.
출력은 JSON 하나만: {"findings": [{"kind": "빠짐|축약|어긋남|순간", "verse": "장:절", "quote": "본문 인용", "field": "칸 이름 또는 [칸, 칸]", "제안": "..."}]}"""


def fixed(path=NOTE_MD):
    """고정 절의 ```json fixed 블록 → dict."""
    with open(path, encoding="utf-8") as fh:
        t = fh.read()
    m = re.search(r"```json fixed\n(.*?)\n```", t, re.S)
    return json.loads(m.group(1))


def book_of(spec):
    return re.match(r"(삼상|삼하|왕상|왕하|대상|대하|시)\s*\d+:", spec["verses"]["range"]).group(1)


def refs(text):
    """'17:22' · '삼하 17:26-29' · '21:13 후반' · '2:14·2:15' → ['17:22', …] (장:절 문자열 목록)."""
    out = []
    for part in re.split(r"[·,]|\s및\s", str(text or "")):
        m = re.search(r"(\d+):(\d+)(?:\s*[-–~]\s*(?:(\d+):)?(\d+))?", part)
        if not m:
            continue
        ch, a = int(m.group(1)), int(m.group(2))
        ch2, b = int(m.group(3) or ch), int(m.group(4) or a)
        if ch2 != ch:   # 장을 넘는 범위 — 시작 절만(창 계산은 chapters()가 따로 한다)
            out.append(f"{ch}:{a}")
            continue
        out += [f"{ch}:{v}" for v in range(a, b + 1)]
    return out


def chapters(spec):
    """순간 절이 든 장 전체 — verses.range와 moment.verse에 나온 장의 최소~최대."""
    chs = [int(x) for x in re.findall(r"(\d+):\d+", spec["verses"]["range"] + " " + spec["moment"]["verse"])]
    return list(range(min(chs), max(chs) + 1))


def window(spec, verses):
    """→ [(장:절, textKo)] — chapters()의 모든 절(verses.json 순서)."""
    b = CS.BOOK[book_of(spec)]
    out = []
    for ch in chapters(spec):
        v = 1
        while (k := f"{b:02d}{ch:03d}{v:03d}") in verses:
            out.append((f"{ch}:{v}", verses[k]["textKo"].strip()))
            v += 1
    return out


def spec_input(spec):
    return {k: v for k, v in spec.items() if k not in SKIP_KEYS}


def prompt(spec, verses, en=None):
    en = en if en is not None else D.route_prompt(spec)
    lines = [HEADER, "", "## 장면 명세 (JSON)", json.dumps(spec_input(spec), ensure_ascii=False, indent=1), "",
             "## 영문 파생 문구 (그림 생성기가 실제로 읽는 글)", en, "",
             f"## 성경 본문 — {BOOK_NAME.get(book_of(spec), book_of(spec))} {', '.join(f'{c}장' for c in chapters(spec))} (개역한글)"]
    lines += [f"{r} {t}" for r, t in window(spec, verses)]
    return "\n".join(lines)


def parse(txt):
    """claude 결과 글 → 지적 목록(형식이 깨지면 None)."""
    m = re.search(r"\{.*\}", txt or "", re.S)
    try:
        d = json.loads(m.group(0)) if m else None
    except json.JSONDecodeError:
        return None
    f = (d or {}).get("findings")
    if not isinstance(f, list) or not all(isinstance(x, dict) for x in f):
        return None
    return f


def field_names(f):
    v = f.get("field")
    if isinstance(v, list):
        return [str(x) for x in v if str(x).strip()]
    return [x.strip() for x in re.split(r"↔|<->|,|/|·| vs | 와 |\s&\s", str(v or "")) if x.strip()]


def squash(s):
    return re.sub(r"\s+", "", s or "")


def validate(f, win):
    """지적 하나 → (ok?, 사유). win = {장:절: textKo}.
    빠짐·축약·순간 = 인용이 그 절(범위면 이어 붙인 절) 본문의 부분 문자열(띄어쓰기 무시), 절이 창 밖이면 지어냄.
    어긋남 = field에 칸 둘 이상."""
    k = f.get("kind")
    if k not in KINDS:
        return False, "종류"
    if k == "어긋남":
        return (True, "") if len(field_names(f)) >= 2 else (False, "칸 둘 미만")
    rs = refs(f.get("verse"))
    if not rs or any(r not in win for r in rs):
        return False, "창 밖 절"
    q = squash(f.get("quote"))
    if not q or q not in squash("".join(win[r] for r in rs)):
        return False, "지어낸 인용"
    return True, ""


def matches(f, cond):
    """맞춤 조건(고정 절) — kind ∈ kinds · (절 겹침 또는 fields 두 칸 모두) · words가 quote+제안에."""
    if f.get("kind") not in cond["kinds"]:
        return False
    hit = bool(set(refs(f.get("verse"))) & set(cond["verses"]))
    if not hit and cond.get("fields"):
        names = " ".join(field_names(f))
        hit = all(x in names for x in cond["fields"])
    if not hit:
        return False
    return bool(re.search(cond["words"], f"{f.get('quote') or ''} {f.get('제안') or ''}"))


# 변이 사본 — 고정 절 mutants(m1~m5)의 요소를 명세 전체에서 지운다. (경로, 바꿀 글, 새 글) · 지울 verse_elements의 quote.
MUTANT_EDITS = {
    "m1": {"drop": ["나팔을 불고"], "edit": [
        ("moment.why", "즐거이 부르며 나팔을 불고 여호와의", "즐거이 부르며 여호와의"),
        ("crowds[0].what", "즐거이 노래하며 나팔을 불고 따른다", "즐거이 노래하며 따른다"),
        ("stages[1].prompt", " and blowing trumpets", "")]},
    "m2": {"drop": ["다윗에게 기름을 부어", "기름을 부어"], "edit": [
        ("moment.why", "다윗에게 기름을 부어 유다 족속의 왕을 삼는 순간", "다윗을 유다 족속의 왕으로 맞는 순간"),
        ("verse_elements[4].out", "기름 부음 뒤에", "왕을 삼은 뒤에"),
        ("figures[0].pose", " 머리에 기름 부음을 받으며", ""),
        ("stages[3].prompt", ", men of Judah pouring oil over his head", "")]},
    "m3": {"drop": ["내 종 다윗에게 말하기를"], "edit": [
        ("title", "나단 — 다윗에게 언약을 전하다", "나단과 다윗"),
        ("moment.why", "나단이 한 팔을 들어 다윗에게 언약의 말씀을 전하는 순간을 고정한다", "나단이 다윗 앞에 서 있는 순간을 고정한다"),
        ("figures[0].pose", "서서 한 팔을 들어 말한다", "지팡이를 쥐고 서 있다"),
        ("stages[1].prompt", ", one arm raised as if speaking", "")]},
    "m4": {"drop": ["시글락을 그에게 주었으므로"], "edit": [
        ("moment.why", "아기스가 손을 들어 성읍을 다윗에게 내어 주고, 다윗이", "아기스와 다윗이 함께 서 있고, 다윗이"),
        ("verse_elements[0].en", "standing, one arm raised gesturing toward the town", "standing"),
        ("verse_elements[4].out", "내어 주는 순간", "성읍 앞에 선 순간"),
        ("figures[0].role", "가드 왕 아기스 — 성읍을 내어 줌", "가드 왕 아기스"),
        ("figures[0].pose", "손을 들어 성읍을 가리키며 서 있다", "겉옷 자락을 쥐고 서 있다"),
        ("stages[2].prompt", ", one arm raised gesturing toward the town", "")]},
    "m5": {"drop": ["사울이 자기에게 행한 일을 다 고하였고"], "edit": [
        ("moment.why", "사무엘 앞에 나아가 사울이 자기에게 행한 일을 다 고하는 순간", "사무엘 앞에 나아간 순간"),
        ("meaning.ko", "사무엘 앞에 서서 사울이 자기에게 행한 일을 다 고하고, 늙은 선지자 사무엘이 그 말을 듣는다", "사무엘 앞에 서고, 늙은 선지자 사무엘이 그를 맞는다"),
        ("meaning.en", " and tells him everything Saul has done to him, while Samuel listens", ""),
        ("meaning.verse", " 사울이 자기에게 행한 일을 다 고하였고", ""),
        ("relation.ko", "한 손을 펴고 고하고, 사무엘은 오른쪽에서 다윗을 마주 보며 듣는다", "서고, 사무엘은 오른쪽에서 다윗을 마주 본다"),
        ("relation.en", "speaks earnestly toward Samuel with one open hand, and Samuel on the right faces him and listens", "stands toward Samuel, and Samuel on the right faces him"),
        ("relation.verse", "(고함·들음)", ""),
        ("figures[0].role", "다윗 — 도피하여 고하는 자", "다윗 — 도피한 자"),
        ("figures[0].pose", "사무엘 앞에 서서 한 손을 펴 고한다", "사무엘 앞에 선다"),
        ("figures[0].gesture.ko", "사무엘 앞에 서서 한 손을 펴 들고 사울이 한 일을 다 고한다", "사무엘 앞에 서 있다"),
        ("figures[0].gesture.en", "standing before Samuel, one open hand raised as he tells him everything that happened", "standing before Samuel"),
        ("figures[0].gesture.verse", " … 다 고하였고", ""),
        ("figures[1].role", "사무엘 — 듣는 선지자", "사무엘 — 선지자"),
        ("figures[1].pose", "서서 겉옷자락을 쥔 채 다윗의 말을 듣는다", "서서 겉옷자락을 쥔다"),
        ("figures[1].expression.verse", "(사무엘에게 고함 — 듣는 자)", ""),
        ("stages[1].prompt", ", telling everything", "")]},
}


def _walk(o, p=""):
    if isinstance(o, dict):
        for k, v in o.items():
            yield from _walk(v, f"{p}.{k}" if p else k)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from _walk(v, f"{p}[{i}]")
    elif isinstance(o, str):
        yield p, o


def _get_set(o, path, value=None):
    keys = re.findall(r"[^.\[\]]+|\[\d+\]", path)
    for k in keys[:-1]:
        o = o[int(k[1:-1])] if k.startswith("[") else o[k]
    last = keys[-1]
    idx = int(last[1:-1]) if last.startswith("[") else last
    if value is not None:
        o[idx] = value
    return o[idx]


def mutate(spec, mid):
    """명세 → 변이 사본(원본은 그대로). 편집 대상 글이 없으면 AssertionError(조용히 무변이 방지)."""
    e = MUTANT_EDITS[mid]
    s = copy.deepcopy(spec)
    for path, old, new in e["edit"]:   # 편집 경로는 drop 전 색인 기준
        cur = _get_set(s, path)
        assert old in cur, f"{mid} {path}: {old!r} 없음"
        _get_set(s, path, cur.replace(old, new))
    s["verse_elements"] = [x for x in s.get("verse_elements", []) if x.get("quote") not in e["drop"]]
    return s


def leaks(s, forbid):
    """변이 사본에 남은 금지 낱말 — verses.quotes(성경 본문 그 자체)·stages[].neg는 뺀다."""
    return [(p, w) for p, t in _walk(s) if not p.startswith("verses.quotes") and not re.match(r"stages\[\d+\]\.neg", p)
            for w in forbid if w in t]


def scene(sid):
    with open(os.path.join(params.CANON_DIR, "scenes", f"{sid}.json"), encoding="utf-8") as fh:
        return json.load(fh)


def build_mutants():
    os.makedirs(MUTANTS, exist_ok=True)
    for m in fixed()["mutants"]:
        s = mutate(scene(m["scene"]), m["id"])
        bad = leaks(s, m["forbid"])
        assert not bad, f"{m['id']} 금지 낱말 남음: {bad[:3]}"
        json.dump(s, open(os.path.join(MUTANTS, f"{m['id']}-{m['scene']}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print(f"[JudgeSpec] 변이 {m['id']} {m['scene']} — {m['what']}", flush=True)


def call(text, model):
    d = tempfile.mkdtemp(prefix="judge-spec-")
    cmd = ["claude", "-p", "--model", model, "--output-format", "json", "--no-session-persistence",
           "--strict-mcp-config", "--disable-slash-commands", "--allowedTools", ""]
    r = subprocess.run(cmd, input=text, capture_output=True, text=True, cwd=d, timeout=900)
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return {"is_error": True, "result": (r.stdout + r.stderr)[-500:]}


def load():
    return json.load(open(METRICS, encoding="utf-8")) if os.path.exists(METRICS) else {}


def update(fn):
    """여러 run·score가 동시에 돌아도 서로의 답을 지우지 않게 — 파일 잠금 아래 디스크의 최신 metrics를 다시 읽어 fn(m)만 합쳐 쓴다
    (task 378: 도는 중 score가 읽어 둔 옛 사본을 통째로 저장해 답이 지워질 뻔함 — judge_items.update와 같은 꼴)."""
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "metrics.lock"), "w") as lk:
        fcntl.flock(lk, fcntl.LOCK_EX)
        m = load()
        fn(m)
        save(m)
        return m


def save(m):
    os.makedirs(OUT, exist_ok=True)
    tmp = f"{METRICS}.{os.getpid()}.tmp"
    json.dump(m, open(tmp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    os.replace(tmp, METRICS)


def judged(findings, win):
    """원 지적 → [{…, ok, why}] (버린 지적도 남김 — 채점이 다시 센다)."""
    return [{**f, "ok": ok, "why": why} for f in findings for ok, why in [validate(f, win)]]


def run(a):
    with open(CS.VERSES, encoding="utf-8") as fh:
        verses = json.load(fh)
    if a.mutants:
        todo = [(f"{m['id']}:{m['scene']}", json.load(open(os.path.join(MUTANTS, f"{m['id']}-{m['scene']}.json"), encoding="utf-8")))
                for m in fixed()["mutants"]]
    else:
        ids = a.only.split(",") if a.only else (list(params.VERSE_ELEMENT_SCENES) if a.key == "blind" else
                                               sorted(os.path.basename(p)[:-5] for p in os.listdir(os.path.join(params.CANON_DIR, "scenes"))
                                                      if p.endswith(".json") and p[:-5] not in params.VERSE_ELEMENT_SCENES) if a.key == "rest" else [])
        assert ids, "--only 또는 --key blind/rest"
        todo = [(sid, scene(sid)) for sid in ids]
    m = load()
    r = m.setdefault("runs", {}).setdefault(a.key, {"model": a.model, "answers": {}})
    assert r["model"] == a.model, f"{a.key}는 {r['model']}로 이미 시작함"
    todo = [(k, s) for k, s in todo if k not in r["answers"]][: a.limit or None]
    print(f"[JudgeSpec] {a.key} {a.model} — 남은 장면 {len(todo)}", flush=True)

    def one(ks):
        k, s = ks
        win = dict(window(s, verses))
        tries, got = [], None
        for _ in range(2):   # JSON이 깨지면 한 번만 다시
            o = call(prompt(s, verses), a.model)
            tries.append(J.use(o) | {"error": bool(o.get("is_error"))})
            got = None if o.get("is_error") else parse(o.get("result"))
            if got is not None:
                break
        rec = {"tries": tries, "findings": judged(got, win) if got is not None else None,
               "raw": None if got is not None else str(o.get("result"))[:400]}
        update(lambda mm: mm.setdefault("runs", {}).setdefault(a.key, {"model": a.model, "answers": {}})["answers"].__setitem__(k, rec))
        fs = rec["findings"]
        res = "답 없음" if fs is None else f"지적 {len(fs)} · 버림 {sum(1 for f in fs if not f['ok'])}"
        print(f"[JudgeSpec] {k} {res} · {sum(t['seconds'] for t in tries):.0f}초", flush=True)

    with ThreadPoolExecutor(a.workers) as ex:
        list(ex.map(one, todo))


# ---- 채점 -------------------------------------------------------------

def kept(rec):
    return [f for f in (rec or {}).get("findings") or [] if f["ok"]]


def spec_summary(m, fx):
    runs = m.get("runs", {})
    blind, mut = runs.get("blind", {}).get("answers", {}), runs.get("mutants", {}).get("answers", {})
    truth = {t["id"]: any(matches(f, t) for f in kept(blind.get(t["scene"]))) for t in fx["truth"]}
    measure = {t["id"]: any(matches(f, t) for f in kept(blind.get(t["scene"]))) for t in fx["measure"]}
    mutants = {x["id"]: any(matches(f, x) for f in kept(mut.get(f"{x['id']}:{x['scene']}"))) for x in fx["mutants"]}
    # 대조: 원본(변이 전) 장면 답에서도 같은 조건이 맞았나 — 맞았다면 그 변이 잡기는 분해능의 증거가 약하다(측정만)
    orig = {x["id"]: any(matches(f, x) for f in kept(blind.get(x["scene"]))) for x in fx["mutants"]}
    allf = [f for k in ("blind", "mutants") for rec in runs.get(k, {}).get("answers", {}).values() for f in (rec.get("findings") or [])]
    fab = sum(1 for f in allf if not f["ok"])
    missing = [s for s in params.VERSE_ELEMENT_SCENES if s not in blind] + [f"{x['id']}:{x['scene']}" for x in fx["mutants"] if f"{x['id']}:{x['scene']}" not in mut]
    failed = [k for kk in ("blind", "mutants") for k, rec in runs.get(kk, {}).get("answers", {}).items() if rec.get("findings") is None]
    rl = fx["rules"]["spec"]
    t_ok, m_ok = sum(truth.values()), sum(mutants.values())
    rate = fab / len(allf) if allf else 0.0
    verdict = None if missing else ("채택" if t_ok >= rl["truth_min"] and m_ok >= rl["mutant_min"] and rate <= rl["fabricated_max"] else "미채택")
    by_kind = {k: sum(1 for f in allf if f.get("kind") == k) for k in KINDS}
    return {"truth": truth, "measure": measure, "mutants": mutants, "mutant_orig_hit": orig, "truth_hit": t_ok, "mutant_hit": m_ok,
            "findings": len(allf), "fabricated": fab, "fabricated_rate": round(rate, 4), "by_kind": by_kind,
            "failed": failed, "missing": missing, "verdict": verdict}


def oddity_answers(jm):
    """이상한 점 답(「틀림」 = 있음) — 라벨 묶음 run(oddity/O1)이 우선, 없으면 t<과제>/O1."""
    out = {}
    for s in ("t376", "oddity"):
        for k, rec in jm.get(s, {}).get("O1", {}).get("answers", {}).items():
            if (rec or {}).get("answers"):
                out[k] = rec["answers"]["oddity"]
            else:
                out.setdefault(k, None)
    return out


def j1_guard(jm, key):
    import judge_learn as L
    task = int(key.split(":")[0])
    try:
        return L.j1_answer(jm, task, key, "guard")[0]
    except KeyError:
        return None


def oddity_summary(jm, fx):
    od, ans = fx["oddity"], oddity_answers(jm)
    missing = [k for k in od["pos"] + od["neg"] if k not in ans]
    pos_hit = [k for k in od["pos"] if ans.get(k) == "틀림"]       # 답 없음(None)은 라벨 반대 = 못 잡음
    neg_ok = [k for k in od["neg"] if ans.get(k) == "맞음"]         # 답 없음은 라벨 반대 = 통과 못 함
    must = {s: sum(1 for k in pos_hit if k.split(":")[1] == s) for s in od["must"]}
    jg_pos = sum(1 for k in od["pos"] if j1_guard(jm, k) == "틀림")
    jg_neg = sum(1 for k in od["neg"] if j1_guard(jm, k) == "맞음")
    rl = fx["rules"]["oddity"]
    c, p = len(pos_hit) / len(od["pos"]), len(neg_ok) / len(od["neg"])
    verdict = None if missing else ("채택" if c >= rl["catch_min"] and p >= rl["pass_min"] and all(must.values()) else "미채택")
    return {"catch": f"{len(pos_hit)}/{len(od['pos'])}", "pass": f"{len(neg_ok)}/{len(od['neg'])}", "catch_rate": round(c, 4), "pass_rate": round(p, 4),
            "must": must, "missed": [k for k in od["pos"] if k not in pos_hit], "false": [k for k in od["neg"] if k not in neg_ok],
            "j1_guard": {"catch": f"{jg_pos}/{len(od['pos'])}", "pass": f"{jg_neg}/{len(od['neg'])}"},
            "missing": missing, "verdict": verdict}


def table(sm, om, fx):
    t = {x["id"]: x for x in fx["truth"] + fx["measure"] + fx["mutants"]}
    L = ["### 명세 판정자 (14장면 블라인드 + 변이 5, Opus)", ""]
    if sm["verdict"]:
        L.append(f"판정(명세 판정자): {sm['verdict']} — 정답 잡기 {sm['truth_hit']}/5 · 변이 잡기 {sm['mutant_hit']}/5 · 지어낸 인용 {sm['fabricated']}/{sm['findings']} ({sm['fabricated_rate'] * 100:.1f}%)")
    else:
        L.append(f"명세 판정자 대기 — 아직 안 돌린 것 {len(sm['missing'])}")
    L += ["", "| 항목 | 내용 | 잡음 |", "|---|---|---|"]
    L += [f"| {k} | {t[k]['what']} | {'예' if v else '아니오'} |" for k, v in sm["truth"].items()]
    L += [f"| {k} (측정만) | {t[k]['what']} | {'예' if v else '아니오'} |" for k, v in sm["measure"].items()]
    L += [f"| {k} (변이) | {t[k]['what']} | {'예' if v else '아니오'}{' · 원본에서도 맞음' if sm['mutant_orig_hit'][k] else ''} |" for k, v in sm["mutants"].items()]
    L += ["", "지적 종류별: " + " · ".join(f"{k} {n}" for k, n in sm["by_kind"].items()) + f" · 답 없음 {len(sm['failed'])}", "",
          "### 이상한 점 판정자 (라벨 있음 12 · 없음 33, Sonnet)", ""]
    if om["verdict"]:
        L.append(f"판정(이상한 점): {om['verdict']} — 있음 잡기 {om['catch']} ({om['catch_rate'] * 100:.1f}%) · 없음 통과 {om['pass']} ({om['pass_rate'] * 100:.1f}%) · "
                 + " · ".join(f"{s.split('-')[-1]} {n}시드" for s, n in om["must"].items()))
    else:
        L.append(f"이상한 점 판정자 대기 — 답 없는 라벨 칸 {len(om['missing'])}")
    L += ["", f"비교값 — 같은 칸의 J1 가드: 있음 잡기 {om['j1_guard']['catch']} · 없음 통과 {om['j1_guard']['pass']}",
          f"놓친 있음: {', '.join(om['missed']) or '없음'}", f"잘못 잡은 없음: {', '.join(om['false']) or '없음'}"]
    return "\n".join(L)


def score(a):
    fx, m, jm = fixed(), load(), J.load()
    sm, om = spec_summary(m, fx), oddity_summary(jm, fx)
    block = table(sm, om, fx)
    notes = open(NOTE_MD, encoding="utf-8").read()
    if a.check:
        bad = []
        if m.get("summary") != {"spec": sm, "oddity": om}:
            bad.append("metrics 요약")
        cur = notes[notes.index(BEGIN) + len(BEGIN): notes.index(END)].strip() if BEGIN in notes else ""
        if cur != block:
            bad.append("notes 결과 절")
        print(f"[JudgeSpec] score --check {'불일치: ' + ', '.join(bad) if bad else '일치'}", flush=True)
        sys.exit(1 if bad else 0)
    update(lambda mm: mm.__setitem__("summary", {"spec": sm, "oddity": om}))   # 그 사이 run이 쓴 답을 지우지 않게 요약만 합쳐 씀
    body = f"{BEGIN}\n{block}\n{END}"
    notes = re.sub(re.escape(BEGIN) + r".*?" + re.escape(END), lambda _: body, notes, flags=re.S) if BEGIN in notes else notes.rstrip() + "\n\n## 결과\n\n" + body + "\n"
    open(NOTE_MD, "w", encoding="utf-8").write(notes)
    print(block, flush=True)


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("mutants")
    r = sub.add_parser("run")
    r.add_argument("--key", required=True, help="blind · rest · mutants · after1 …")
    r.add_argument("--only", default="")
    r.add_argument("--mutants", action="store_true")
    r.add_argument("--model", default="opus")
    r.add_argument("--limit", type=int, default=0)
    r.add_argument("--workers", type=int, default=3)
    s = sub.add_parser("score")
    s.add_argument("--check", action="store_true")
    a = p.parse_args()
    {"mutants": lambda a: build_mutants(), "run": run, "score": score}[a.cmd](a)


if __name__ == "__main__":
    main()
