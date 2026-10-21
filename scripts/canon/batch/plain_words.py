#!/usr/bin/env python3
"""task#382 — 성경 낱말 사전 2/3: 사전으로 다시 쓴 명세(r1) → 남은 실패만 단계 올리기(r2·r3·따로 시험) → 쉬운 말(b2) → A와 기계 비교 → 사람 후보 화면.

  VENV=~/.local/biblemap-imggen/.venv314/bin/python
  $VENV batch/plain_words.py predict-a        # A 32장(376·379 그림) — J1·J1-prop·O1 답은 그대로 옮기고 특징 문항만 묻는다(GPU 0)
  $VENV batch/plain_words.py one              # 시험 1장(r1 첫 장면 첫 시드) + 그 낱말 특징 문항
  nohup caffeinate -i $VENV batch/plain_words.py ladder > batch/plain-words.log 2>&1 &   # r1 → r2·r3·따로 시험(무인, 이미 있으면 건너뜀)
  $VENV batch/plain_words.py b2               # specs/b2/(손으로 쓴 쉬운 말 사본) 검사 → 생성 → 예측
  $VENV batch/plain_words.py cand             # 최종 고르기 → 후보 화면 4장(블라인드 좌우)
  $VENV batch/plain_words.py check            # 회차 사본 검사(C3) → ok
  (run_night.py <cmd> --set plain-words 도 같다.)

규칙·단위·자리는 notes/PLAIN-WORDS.md 고정 절(```json fixed). 사본은 samples/plain-words/specs/<회차>/<장면>.json, 그림은 레포 밖
~/.local/biblemap-imggen/plain-words/<회차>/<장면>/s<시드>.png, 목록·답·사다리는 samples/plain-words/metrics.json.

task#385 — `--set jordan-moment`: 같은 사다리를 요단 귀환 새 순간(19:18 전체)에 — 고정 절 notes/JORDAN-MOMENT.md,
그림 ~/.local/biblemap-imggen/jordan-moment/, metrics samples/jordan-moment/metrics.json. A(기존 그림) 없음 → J1 문항은 정본 명세에서 바로,
후보 화면은 최종 회차 기계 1위·2위 블라인드 1화면(+ 접힌 8장). `--set` 없으면 382 묶음(plain-words) 그대로.
  $VENV batch/plain_words.py one --set jordan-moment   ·   ladder · cand · check · record <판정.txt> · verdict · lexicon

task#387 — `--set jordan-scene`: 장면 구절로 다시 쓴 요단 정본 그대로 r1 한 회차(사다리 없음) + 장면 요소 문항(E) → 문구 1위의 「다윗 바로 앞」이
틀리면 국소 편집 12장 → 후보 화면 1화면. 고정 절 notes/JORDAN-SCENE.md.
  $VENV batch/plain_words.py one|scene|check|edit|cand|record <판정.txt>|verdict|report --set jordan-scene

task#388 — `--set jordan-guide`: 지리·새 구도로 고친 요단 정본 + 구도 가이드(깊이, batch/make_guide.py) · CN 2602 lite.
시험 1장 → 격자(강도 × CN 스텝 × 시드) → 고른 설정 8시드 → 후보 1화면. 고정 절 notes/JORDAN-GUIDE.md.
  $VENV batch/plain_words.py one|grid|scene|check|cand|record <판정.txt>|verdict|approve|report --set jordan-guide"""
import copy, hashlib, json, os, re, subprocess, sys, threading, time
from concurrent.futures import ThreadPoolExecutor

from PIL import Image

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "batch"))
import derive_scene as D
import judge_items as J
import make_night_page as P

# 묶음 → 고정 절·과제 번호·정본 명세 읽는 자리. canon_rev: 382 묶음은 그 회차를 만든 정본(385가 요단 정본을 고치기 전 커밋)으로 읽어
# 사본 검사(render 대조)가 옛 회차 그대로 통과한다.
SETS = {"plain-words": {"notes": "PLAIN-WORDS.md", "task": 382, "canon_rev": "03b0b07"},
        "jordan-moment": {"notes": "JORDAN-MOMENT.md", "task": 385, "canon_rev": "1ce6720"},   # 387이 요단 정본을 장면 구절로 고치기 전
        "jordan-scene": {"notes": "JORDAN-SCENE.md", "task": 387, "canon_rev": "15fc2de"},   # 388이 요단 정본에 지리·새 구도를 넣기 전
        "jordan-guide": {"notes": "JORDAN-GUIDE.md", "task": 388, "canon_rev": "a680048"}}   # restyle r3가 요단 정본에 다윗 왕·시므이 방향을 넣기 전
SET = sys.argv[sys.argv.index("--set") + 1] if "--set" in sys.argv else "plain-words"
TASK = SETS[SET]["task"]
NOTES = os.path.join(HERE, "notes", SETS[SET]["notes"])
WORDS = os.path.join(HERE, "..", "..", "data", "scripture_words", "words.json")
SAMPLES = os.path.join(HERE, "samples", SET)
SPECS = os.path.join(SAMPLES, "specs")
METRICS = os.path.join(SAMPLES, "metrics.json")
OUT = os.path.expanduser(f"~/.local/biblemap-imggen/{SET}")
_CANON = {}


def canon(sid):
    """정본 명세 — canon_rev가 있으면 그 커밋의 파일(git show), 없으면 지금 파일."""
    rev = SETS[SET]["canon_rev"]
    if not rev:
        return D.load(sid)
    if sid not in _CANON:
        _CANON[sid] = json.loads(subprocess.run(["git", "show", f"{rev}:scripts/canon/scenes/{sid}.json"], cwd=HERE,
                                                capture_output=True, text=True, check=True).stdout)
    return copy.deepcopy(_CANON[sid])
KINDS = {"J1": ("v2", 1.0), "J1-prop": ("p2", 2.5), "O1": ("o1", 1.0), "W": ("v2", 1.0), "W-prop": ("p2", 2.5),
         "E": ("v2", 1.0), "S": ("v2", 1.0)}   # E = 387 장면 요소 문항 · S = 388 화풍·가이드 복제 문항(전체 그림)
LOCK = threading.Lock()
_TOK = []


def fixed():
    t = open(NOTES, encoding="utf-8").read()
    return json.loads(re.search(r"```json fixed\n(.*?)\n```", t, re.S).group(1))


FX = fixed()
# 382 묶음은 사전도 그 회차 때 것(canon_rev)으로 — 384가 진설병 L3를 고친 뒤에도 옛 사본 대조가 그대로 통과한다
LEX = {e["id"]: e for e in (json.loads(subprocess.run(["git", "show", f"{SETS[SET]['canon_rev']}:data/scripture_words/words.json"], cwd=HERE,
                                                      capture_output=True, text=True, check=True).stdout)
                             if SETS[SET]["canon_rev"] else json.load(open(WORDS, encoding="utf-8")))["words"]}


def load_m():
    return json.load(open(METRICS)) if os.path.exists(METRICS) else {"rounds": {}, "answers": {}, "ladder": {}}


def save_m(m):
    os.makedirs(SAMPLES, exist_ok=True)
    tmp = METRICS + ".tmp"
    json.dump(m, open(tmp, "w"), ensure_ascii=False, indent=1)
    os.replace(tmp, METRICS)


def tokens(p):
    if not _TOK:
        import check_scenes as CS
        _TOK.append(CS.zimage_tokens())
    return _TOK[0](p)


# --- 회차 사본 -----------------------------------------------------------------
def _walk(spec, path):
    """「stages[1].prompt」 → (부모, 키)."""
    keys = [int(k) if k.isdigit() else k for k in re.findall(r"[^.\[\]]+", path)]
    obj = spec
    for k in keys[:-1]:
        obj = obj[k]
    return obj, keys[-1]


def insert_form(en):
    """사전 look.en → 명사구 자리 삽입꼴(고정 절): 첫 글자 소문자 · 끝 마침표 뗌 · 문장 사이 「. 」→「, 」. 낱말은 그대로."""
    s = en.strip().rstrip(".")
    return (s[0].lower() + s[1:]).replace(". ", ", ")


def phrase(uid, level):
    return insert_form(LEX[uid]["look"][level]["en"])


def units(sid):
    return FX["scenes"][sid]["units"]


def render(sid, levels):
    """정본 명세 → 단위마다 자리를 그 단계 삽입꼴로, 그릴 수 없는 낱말은 이름 문구를 뺀 사본(결정적)."""
    spec = copy.deepcopy(canon(sid))
    for u in units(sid):
        o, k = _walk(spec, u["slot"]["path"])
        assert o[k].count(u["slot"]["old"]) == 1, (sid, u["id"], o[k])
        o[k] = o[k].replace(u["slot"]["old"], phrase(u["id"], levels[u["id"]]))
    for s in FX["scenes"][sid].get("signs", []):
        o, k = _walk(spec, s["remove"]["path"])
        assert o[k].count(s["remove"]["old"]) == 1, (sid, s["id"])
        o[k] = o[k].replace(s["remove"]["old"], "")
    return spec


def start_levels(sid):
    """핵심 L2 · 배경 L1 — 단위에 start가 있으면 그 단계(385: 그림 증거가 있는 단계에서 시작)."""
    return {u["id"]: u.get("start") or ("L2" if u["role"] == "core" else "L1") for u in units(sid)}


def spec_path(rnd, sid):
    return os.path.join(SPECS, rnd, f"{sid}.json")


def img_path(rnd, sid, s):
    return os.path.join(OUT, rnd, sid, f"s{s}.png")


# --- 그림 ----------------------------------------------------------------------
def busy():
    r = subprocess.run(["pgrep", "-fl", "mflux|run_scene.py --worker|gen_video_pilot|mlx_video"], capture_output=True, text=True)
    return r.stdout.strip()


def generate(m, rnd, specs, seeds=None, base=None, raised=None, cn=None):
    """specs = {장면: 사본 명세} → 사본 저장 · 바탕 생성(없는 것만) · 상자 → metrics rounds[rnd].
    cn = {scale, cn_steps}이면 구도 가이드(GUIDE)를 CN lite로 건다(388)."""
    import run_scene
    import run_night as RN
    seeds = seeds or FX["seeds"]
    R = m["rounds"].setdefault(rnd, {"scenes": {}})
    for sid, spec in specs.items():
        os.makedirs(os.path.dirname(spec_path(rnd, sid)), exist_ok=True)
        json.dump(spec, open(spec_path(rnd, sid), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        p = D.route_prompt(spec)
        sc = R["scenes"].setdefault(sid, {"seeds": [], "sec": 0.0})
        sc.update(prompt=p, tokens=tokens(p), **({"levels": base[sid][0], "base": base[sid][1], "raised": raised[sid]} if base else {}),
                  **({"cn": cn} if cn else {}))
        todo = [{"prompt": p, "seed": s, "w": 1216, "h": 640, "out": img_path(rnd, sid, s), **({"control": GUIDE, **cn} if cn else {})}
                for s in seeds if not os.path.exists(img_path(rnd, sid, s))]
        print(f"[PlainWords] {rnd} {sid} {sc['tokens']}토큰 · {len(seeds)}장 중 {len(todo)}장 생성", flush=True)
        if todo:
            if busy():
                sys.exit(f"[PlainWords] 다른 생성 프로세스가 돈다 — 겹치지 않게 멈춤:\n{busy()}")
            os.makedirs(os.path.dirname(img_path(rnd, sid, seeds[0])), exist_ok=True)
            d = os.path.dirname(img_path(rnd, sid, seeds[0]))
            sc["sec"] = round(sc["sec"] + sum(run_scene.gen_zimage(todo, d, "gencn" if cn else "gen")), 1)
            if cn:
                sc["peak_gib"] = max(sc.get("peak_gib", 0), json.load(open(os.path.join(d, "_zjobs.json.peak.json"))))
        have = {x["seed"] for x in sc["seeds"]}
        cn = canon(sid)
        for s in seeds:
            if s not in have:
                sc["seeds"].append({"seed": s, "base": img_path(rnd, sid, s), "boxes": RN.boxes(cn, img_path(rnd, sid, s))})
        save_m(m)


# --- 판정 ----------------------------------------------------------------------
def _seeds(m, rnd, sid):
    return m["rounds"][rnd]["scenes"][sid]["seeds"]


def j1_qs(m, rnd, sid):
    """A와 같은 J1 문항(정본 명세 → make_night_page.questions, A 과제와 같은 wide) — 크롭만 이 그림들 상자로."""
    seeds = _seeds(m, rnd, sid)
    a = FX["scenes"][sid].get("a")
    if not a:   # A 없는 묶음(385) — 정본 명세 문항 그대로
        return [q for q in P.questions(canon(sid), {"seeds": seeds}, FX["scenes"][sid].get("wide", False)) if not q["id"].endswith(".identity")]
    task = a["task"]
    qs = P.questions(canon(sid), {"seeds": seeds}, task in P.FACING370)
    # 문항 글은 A 페이지 그대로 — A 뒤에 정본 명세의 한국어 칸이 바뀐 장면(가드 자세 설명)도 A와 같은 말로 묻는다
    page = {q["id"]: q for s in J.page_scenes(J.TASKS[task][1]) if s["id"] == sid for q in s["qs"]}
    return [{**q, **{k: page[q["id"]][k] for k in ("q", "what", "verse") if k in page[q["id"]]}} for q in qs if not q["id"].endswith(".identity")]


def word_qs(m, rnd, sid, prop):
    """사전 특징 문항(skip 뺌) — prop=True면 지물 단위만(J1-prop 머리말), 아니면 동작·장면 사물."""
    seeds = _seeds(m, rnd, sid)
    W, H = Image.open(seeds[0]["base"]).size
    qs = []
    for u in units(sid):
        if (u["judge"] == "prop") != prop:
            continue
        crop = {"who": u["who"], "kind": "crop", "ar": 0.75,
                "crop": {str(x["seed"]): P.fit(x["boxes"][u["who"]]["body"], 0.75, W, H, 0.15) for x in seeds}} if u.get("who") else {}
        for j, f in enumerate(LEX[u["id"]]["criteria"]["features"]):
            if str(j) not in u.get("skip", {}):
                qs.append({"id": f"w.{u['id']}.{j}", "q": LEX[u["id"]]["word"], "what": f["q"], **crop})
    return qs


def elem_qs(sid, extra=False):
    """387 장면 요소 문항(고정 절 elements, 편집본이면 edit_extra까지) — 전체 그림."""
    c = FX["scenes"][sid]
    return [dict(e) for e in c.get("elements", []) + (c.get("edit_extra", []) if extra else [])]


def items(m, rnd, kind, sids=None):
    out = []
    for sid in sids or m["rounds"][rnd]["scenes"]:
        spec = canon(sid)
        qs = {"J1": lambda: j1_qs(m, rnd, sid), "J1-prop": lambda: [q for q in j1_qs(m, rnd, sid) if J.cls(q["id"]) == "prop"],
              "O1": lambda: j1_qs(m, rnd, sid), "W": lambda: word_qs(m, rnd, sid, False), "W-prop": lambda: word_qs(m, rnd, sid, True),
              "E": lambda: elem_qs(sid), "S": lambda: [dict(q) for q in FX["scenes"][sid].get("style", [])]}[kind]()
        if not qs:
            continue
        for x in _seeds(m, rnd, sid):
            it = {"key": f"{rnd}:{sid}:{x['seed']}", "task": rnd, "scene": sid, "title": spec["title"], "range": spec["verses"]["range"],
                  "seed": x["seed"], "src": x["base"], "qs": qs, "qids": ["oddity"] if kind == "O1" else [q["id"] for q in qs]}
            if kind == "O1":
                it["spec"] = J.oddity_spec(sid)
            out.append(it)
    return out


def ask(m, rnd, kind, it):
    """claude -p 한 건 → m["answers"][rnd][kind][key] (바로 저장)."""
    header, zoom = KINDS[kind]
    d, files = J.prepare(it, SET, zoom)
    text = J.oddity_prompt(it, files, J.HEADERS[header]) if kind == "O1" else J.prompt(it, files, J.HEADERS[header])
    tries, got = [], None
    for _ in range(2):   # JSON이 깨지면 한 번만 다시(judge_items.run과 같음)
        o = J.call(text, d, "sonnet")
        tries.append(J.use(o) | {"error": bool(o.get("is_error"))})
        got = None if o.get("is_error") else J.parse(o.get("result"), it["qids"])
        if got:
            break
    with LOCK:
        m["answers"].setdefault(rnd, {}).setdefault(kind, {})[it["key"]] = {"tries": tries, "raw": None if got else str(o.get("result"))[:400], **(got or {"answers": None})}
        save_m(m)
    if not got:
        print(f"[PlainWords] {kind} {it['key']} 답 없음", flush=True)


def judge(m, rnd, kinds=tuple(KINDS), sids=None, workers=8):
    """claude -p 판정(J1·J1-prop·O1·특징 문항) — 이미 답한 그림은 건너뛴다. 답마다 바로 저장."""
    todo = []
    for kind in kinds:
        done = m["answers"].setdefault(rnd, {}).setdefault(kind, {})
        todo += [(kind, it) for it in items(m, rnd, kind, sids) if it["key"] not in done or not done[it["key"]].get("answers")]
    print(f"[PlainWords] {rnd} 판정 {len(todo)}건 {sorted({k for k, _ in todo})}", flush=True)
    t = time.time()

    with ThreadPoolExecutor(workers) as ex:
        list(ex.map(lambda job: ask(m, rnd, *job), todo))
    miss = [(k, it["key"]) for k, it in todo if not m["answers"][rnd][k][it["key"]].get("answers")]
    print(f"[PlainWords] {rnd} 판정 끝 {time.time() - t:.0f}초 · 답 없음 {len(miss)}", flush=True)
    return miss


# --- 점수 ----------------------------------------------------------------------
def _a(m, rnd, kind, sid, s):
    return (m["answers"].get(rnd, {}).get(kind, {}).get(f"{rnd}:{sid}:{s}") or {}).get("answers") or {}


def j1(m, rnd, sid, s):
    """J1 답 — 지물 칸은 J1-prop 답(판정자 J1 = v2 전 문항 + p2 지물만)."""
    a, p = _a(m, rnd, "J1", sid, s), _a(m, rnd, "J1-prop", sid, s)
    return {q: (p.get(q) if J.cls(q) == "prop" and q in p else v) for q, v in a.items()}


def other_wrong(m, rnd, sid, s):
    return sum(1 for q, v in j1(m, rnd, sid, s).items() if v == "틀림" and q not in FX["scenes"][sid]["word_qids"])


def all_wrong(m, rnd, sid, s):
    return sum(1 for v in j1(m, rnd, sid, s).values() if v == "틀림")


def feats(m, rnd, sid, s):
    return {**_a(m, rnd, "W", sid, s), **_a(m, rnd, "W-prop", sid, s)}


def unit_ok(m, rnd, sid, s, uid):
    f = feats(m, rnd, sid, s)
    ids = [q for q in f if q.startswith(f"w.{uid}.")]
    return bool(ids) and all(f[q] == "맞음" for q in ids)


def seeds_of(m, rnd, sid):
    return [x["seed"] for x in _seeds(m, rnd, sid)]


def unit_hits(m, rnd, sid, uid):
    return sum(unit_ok(m, rnd, sid, s, uid) for s in seeds_of(m, rnd, sid))


def scene_hits(m, rnd, sid):
    return sum(all(unit_ok(m, rnd, sid, s, u["id"]) for u in units(sid)) for s in seeds_of(m, rnd, sid))


def other_sum(m, rnd, sid):
    return sum(other_wrong(m, rnd, sid, s) for s in seeds_of(m, rnd, sid))


def top(m, rnd, sid):
    """1위(고정 절): 특징 문항을 다 맞은 시드 중 J1 틀림 칸이 가장 적은 것 — 없으면 맞은 특징 문항이 가장 많은 시드 중에서."""
    order = FX["seeds"]
    ss = seeds_of(m, rnd, sid)
    right = {s: sum(v == "맞음" for v in feats(m, rnd, sid, s).values()) for s in ss}
    pool = [s for s in ss if all(unit_ok(m, rnd, sid, s, u["id"]) for u in units(sid))] or [s for s in ss if right[s] == max(right.values())]
    return min(pool, key=lambda s: (all_wrong(m, rnd, sid, s), order.index(s)))


def ranked(m, rnd, sid):
    """385 — 1위·2위(1위 규칙을 남은 시드에 한 번 더): 단위 다 맞음 먼저 · 맞은 특징 문항 많은 순 · J1 틀림 적은 순 · 시드 순서."""
    order = FX["seeds"]
    ok = lambda s: all(unit_ok(m, rnd, sid, s, u["id"]) for u in units(sid))
    right = lambda s: sum(v == "맞음" for v in feats(m, rnd, sid, s).values())
    out = sorted(seeds_of(m, rnd, sid), key=lambda s: (not ok(s), 0 if ok(s) else -right(s), all_wrong(m, rnd, sid, s), order.index(s)))
    assert out[0] == top(m, rnd, sid)
    return out


# --- A ------------------------------------------------------------------------
def predict_a(m):
    jm = J.load()
    R = m["rounds"].setdefault("A", {"scenes": {}})
    for sid, c in FX["scenes"].items():
        src = json.load(open(os.path.join(HERE, "samples", c["a"]["dir"], "metrics.json")))["scenes"][sid]
        R["scenes"][sid] = {"src": c["a"], "prompt": src["prompt"], "tokens": tokens(src["prompt"]),
                            "seeds": [{"seed": x["seed"], "base": x["base"], "boxes": x["boxes"]} for x in src["seeds"]]}
        assert src["prompt"] == D.route_prompt(canon(sid)), f"{sid}: A 프롬프트가 지금 정본 명세와 다름"
        # 같은 문항인지 — A 사람 페이지(J1이 읽은 문항)와 대조
        page = next(s for s in J.page_scenes(J.TASKS[c["a"]["task"]][1]) if s["id"] == sid)
        mine = [(q["id"], q["what"], q.get("crop")) for q in j1_qs(m, "A", sid)]
        theirs = [(q["id"], q["what"], q.get("crop")) for q in page["qs"] if not q["id"].endswith(".identity") and q.get("grp") != "plate"]
        assert mine == theirs, f"{sid}: J1 문항이 A 페이지와 다름"
        for kind in ("J1", "J1-prop", "O1"):   # 376·379 답을 그대로(같은 판정자·같은 문항)
            got = jm[f"t{c['a']['task']}"][kind]["answers"]
            dst = m["answers"].setdefault("A", {}).setdefault(kind, {})
            for x in src["seeds"]:
                k = f"{c['a']['task']}:{sid}:{x['seed']}"
                if k in got:
                    dst[f"A:{sid}:{x['seed']}"] = {**got[k], "from": k}
    save_m(m)
    miss = judge(m, "A", ("W", "W-prop"))
    report(m, "A")
    return miss


def report(m, rnd):
    for sid in m["rounds"][rnd]["scenes"]:
        u = " · ".join(f"{x['id']} {unit_hits(m, rnd, sid, x['id'])}/8" for x in units(sid))
        print(f"[PlainWords] {rnd} {sid}: 장면 낱말 {scene_hits(m, rnd, sid)}/8 · {u} · 다른 칸 틀림 {other_sum(m, rnd, sid)}", flush=True)


# --- 사다리 --------------------------------------------------------------------
def a_wrong(m, sid, uid):
    return 8 - unit_hits(m, "A", sid, uid) if "A" in m["rounds"] else 0   # A 없는 묶음은 같은 등급 안에서 단위 순서대로


def ladder(m):
    if any(c.get("a") for c in FX["scenes"].values()) and not m["answers"].get("A", {}).get("W-prop"):
        predict_a(m)
    L = m["ladder"]
    if "r1" not in L.get("_done", []):
        lv = {sid: start_levels(sid) for sid in FX["scenes"]}
        generate(m, "r1", {sid: render(sid, lv[sid]) for sid in FX["scenes"]},
                 base={sid: (lv[sid], "A") for sid in FX["scenes"]}, raised={sid: list(lv[sid]) for sid in FX["scenes"]})
        judge(m, "r1")
        for sid in FX["scenes"]:
            st = L.setdefault(sid, {"levels": lv[sid], "end": "r1", "rounds": ["r1"], "units": {}})
            for u in units(sid):
                st["units"][u["id"]] = {"level": lv[sid][u["id"]], "stop": None, "status": None, "with": [], "hist": []}
            settle(m, "r1", sid, list(lv[sid]))
        L.setdefault("_done", []).append("r1")
        save_m(m)
        report(m, "r1")
    for rnd in ("r2", "r3"):
        if rnd in L["_done"]:
            continue
        plan = {}
        for sid in FX["scenes"]:
            r = raise_plan(m, sid, rnd)
            if r:
                plan[sid] = r
        save_m(m)
        if plan:
            generate(m, rnd, {sid: render(sid, lv) for sid, (lv, _) in plan.items()},
                     base={sid: (lv, L[sid]["end"]) for sid, (lv, _) in plan.items()}, raised={sid: up for sid, (_, up) in plan.items()})
            judge(m, rnd)
            for sid, (lv, up) in plan.items():
                accept(m, rnd, sid, lv, up)
            report(m, rnd)
        L["_done"].append(rnd)
        save_m(m)
    for sid, st in L.items():   # 회차가 끝났는데 남은 실패 → L3면 문구 한계(r3 뒤에는 회차가 없다)
        if sid.startswith("_"):
            continue
        for uid, u in st["units"].items():
            if not u["stop"]:
                u["stop"] = "문구 한계" if u["level"] == "L3" else "회차 끝"
    save_m(m)


def settle(m, rnd, sid, changed):
    """맞은 단위 → 맞음 확정(그 회차에 바뀐 단위가 그것 하나) / 조건부(여럿, with = 함께 바뀐 단위)."""
    st = m["ladder"][sid]
    for uid in changed:
        u = st["units"][uid]
        hit = unit_hits(m, rnd, sid, uid)
        u["hist"].append({"round": rnd, "level": st["levels"][uid], "hits": hit})
        if hit >= FX["threshold"] and not u["stop"]:
            u.update(stop="맞음", status="확정" if len(changed) == 1 else "조건부", **{"with": [x for x in changed if x != uid]})


def raise_plan(m, sid, rnd):
    """→ (새 단계, 올린 단위) 또는 None. 문턱 미만 단위만, 핵심 먼저 · 같은 등급은 A 틀린 장 수 많은 순, 512 넘으면 상한."""
    st = m["ladder"][sid]
    lv = dict(st["levels"])
    role = {u["id"]: u["role"] for u in units(sid)}
    fail = [uid for uid, u in st["units"].items() if not u["stop"]]
    up = []
    for uid in sorted(fail, key=lambda x: (role[x] != "core", -a_wrong(m, sid, x))):
        cur = st["units"][uid]["level"]
        if cur == "L3":
            st["units"][uid]["stop"] = "문구 한계"
            continue
        nxt = FX["levels"][FX["levels"].index(cur) + 1]
        trial = {**lv, uid: nxt}
        if tokens(D.route_prompt(render(sid, trial))) > FX["token_max"]:
            st["units"][uid]["stop"] = "상한"
            continue
        lv, up = trial, up + [uid]
    return (lv, up) if up else None


def accept(m, rnd, sid, lv, up):
    st = m["ladder"][sid]
    prev = st["end"]
    if other_sum(m, rnd, sid) > other_sum(m, prev, sid) + FX["revert_plus"]:   # 되돌림(PROMPTING 10)
        m["rounds"][rnd]["scenes"][sid]["reverted"] = True
        for uid in up:
            st["units"][uid].update(stop="밀어냄(다른 칸)")
            st["units"][uid]["hist"].append({"round": rnd, "level": lv[uid], "hits": unit_hits(m, rnd, sid, uid), "reverted": True})
        return
    st.update(levels=lv, end=rnd)
    st["rounds"].append(rnd)
    for uid in up:
        st["units"][uid]["level"] = lv[uid]
    settle(m, rnd, sid, up)
    if len(up) > 1:   # 함께 올려 틀린 단위 → 따로 시험(같은 단계, 나머지는 직전 회차 단계)
        for uid in [x for x in up if not st["units"][x]["stop"]]:
            iso = f"iso-{rnd}-{uid}"
            base = dict(m["rounds"][prev]["scenes"][sid].get("levels") or start_levels(sid))
            ilv = {**base, uid: lv[uid]}
            generate(m, iso, {sid: render(sid, ilv)}, base={sid: (ilv, prev)}, raised={sid: [uid]})
            judge(m, iso)
            hit = unit_hits(m, iso, sid, uid)
            st["units"][uid]["hist"].append({"round": iso, "level": lv[uid], "hits": hit})
            if hit >= FX["threshold"]:
                st["units"][uid]["stop"] = "밀어냄(낱말끼리)"
    save_m(m)


# --- 검사(C3) ------------------------------------------------------------------
def check(m):
    bad = []
    canon_verse = lambda spec: json.dumps([(p, v) for p, v in _paths(spec) if p.endswith("verse") or ".verse" in p], ensure_ascii=False)
    names = ["feigning madness", "feign"]
    for rnd, R in m["rounds"].items():
        if rnd == "A":
            continue
        for sid, sc in R["scenes"].items():
            spec = json.load(open(spec_path(rnd, sid), encoding="utf-8"))
            p = D.route_prompt(spec)
            n = tokens(p)
            if n > FX["token_max"]:
                bad.append(f"{rnd} {sid} {n}토큰 > {FX['token_max']}")
            lv = m["ladder"][sid]["levels"] if rnd == "b2" else sc["levels"]
            for u in units(sid):
                if phrase(u["id"], lv[u["id"]]) not in p:
                    bad.append(f"{rnd} {sid} {u['id']} {lv[u['id']]} 삽입꼴 없음")
            if FX["scenes"][sid].get("signs") and any(x in p.lower() for x in names):
                bad.append(f"{rnd} {sid} 그릴 수 없는 낱말 이름 문구가 남음")
            if rnd == "b2":
                if canon_verse(spec) != canon_verse(canon(sid)):
                    bad.append(f"b2 {sid} 근거 verse 칸이 바뀜")
                if set(re.findall(r"[a-z]+", p.lower())) & set(FX["forbidden"]):
                    bad.append(f"b2 {sid} 금지어")
                continue
            if spec != render(sid, lv) and {**spec, "approved": None} != {**render(sid, lv), "approved": None}:   # 387: 채택 뒤 정본에 승인 기록이 붙어도
                bad.append(f"{rnd} {sid} 사본이 render(단계)와 다름")
            if rnd != "r1" and TASK != 388:   # 388은 회차마다 정본 그대로(시험·격자·본 실행) — 직전 회차 대비가 없다
                base = m["rounds"][sc["base"]]["scenes"][sid]["levels"]
                diff = sorted(u for u in lv if lv[u] != base[u])
                if diff != sorted(sc["raised"]):
                    bad.append(f"{rnd} {sid} 직전({sc['base']}) 대비 바뀐 단위 {diff} ≠ 올린 단위 {sc['raised']}")
    for sid, st in m["ladder"].items():
        if sid.startswith("_"):
            continue
        for uid, u in st["units"].items():
            if not u["stop"]:
                bad.append(f"ladder {sid} {uid} 멈춘 사유 없음")
    if TASK == 387:
        bad += check387(m)
    if TASK == 388:
        bad += check388(m)
    print("ok" if not bad else "불통:\n" + "\n".join(bad))
    return not bad


def _paths(v, p=""):
    if isinstance(v, dict):
        for k, x in v.items():
            yield from _paths(x, f"{p}.{k}")
    elif isinstance(v, list):
        for i, x in enumerate(v):
            yield from _paths(x, f"{p}[{i}]")
    else:
        yield p, v


# --- 최종 · 후보 화면 ----------------------------------------------------------
def final(m, sid):
    """사다리 끝 대 b2 — 장면 낱말 맞힘 많은 쪽, 같으면 b2."""
    end = m["ladder"][sid]["end"]
    if "b2" in m["rounds"] and sid in m["rounds"]["b2"]["scenes"] and scene_hits(m, "b2", sid) >= scene_hits(m, end, sid):
        return "b2"
    return end


def left_is_a(sid):
    return int(hashlib.sha1(sid.encode()).hexdigest(), 16) % 2 == 0


def cand(m, out=None):
    import make_cand_page as C
    for w, q in C.SIZES:
        scenes, data = [], {}
        for sid in FX["scenes"]:
            fr = final(m, sid)
            a, f = ("A", top(m, "A", sid)), (fr, top(m, fr, sid))
            sides = (a, f) if left_is_a(sid) else (f, a)
            for r, s in sides:
                data[f"{r}:{sid}:{s}"] = P.uri(Image.open(next(x["base"] for x in _seeds(m, r, sid) if x["seed"] == s)), w, q)
            spec = canon(sid)
            scenes.append({"id": sid, "title": spec["title"], "range": spec["verses"]["range"], "ab": True, "reject": False,
                           "left": f"{sides[0][0]}:{sid}:{sides[0][1]}", "right": f"{sides[1][0]}:{sid}:{sides[1][1]}",
                           "left_is": "A" if sides[0][0] == "A" else "final", "final_round": fr, "verses": C.scripture(sid)})
        page = (PAGE.replace("/*STYLE*/", C.STYLE + C.VERSE_STYLE).replace("/*SCENES*/[]", json.dumps(scenes, ensure_ascii=False))
                .replace("/*IMGS*/{}", json.dumps(data)))
        if len(page) <= P.LIMIT:
            break
    out = out or os.path.join(J.PAGES, "plain-words-cand.html")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w", encoding="utf-8").write(page)
    m["cand"] = {sid: {"final_round": s["final_round"], "left": s["left"], "right": s["right"], "left_is": s["left_is"]} for sid, s in zip(FX["scenes"], scenes)}
    save_m(m)
    print(f"[PlainWords] 후보 화면 {out} {len(page) / 1e6:.2f}MB · {w}px q{q} · 화면 {len(scenes)}", flush=True)
    return out


PAGE = r"""<title>낱말 사전 그림 비교 382</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+KR:wght@400;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
/*STYLE*/
.big { border: 1px solid var(--line); border-radius: 6px; overflow: hidden; position: relative; }
.pair { display: grid; gap: 8px; }
@media (min-width: 900px) { .pair { grid-template-columns: 1fr 1fr; } }
.pair .card { border-width: 2px; }
.pair .card.on { border-color: var(--pick); background: var(--pick-bg); }
.answer3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; }
</style>
<main id="app"></main>
<footer><div class="row"><button class="b" id="prev" type="button">이전</button><span class="bar" id="clock"></span><button class="b main" id="next" type="button" hidden>다음</button></div></footer>
<div class="ov" id="ov" hidden></div>
<script>
const SCENES = /*SCENES*/[];
const IMGS = /*IMGS*/{};
const TASK = 382;
const KEY = "plain-words-page-" + TASK;
let st = { i: 0, t0: null, done: null, sc: {}, act: 0, last: null };
const IDLE = 120000;   // 입력 없이 2분 넘은 간격은 쉼 — 「쉼 뺀 시간」에서 뺀다(task 379와 같음)
try { const s = JSON.parse(localStorage.getItem(KEY) || "null"); if (s && s.sc) st = s; } catch (e) { console.warn("[PlainWordsPage] 저장본 읽기 실패", e); }
const save = () => { try { localStorage.setItem(KEY, JSON.stringify(st)); } catch (e) { console.warn("[PlainWordsPage] 저장 실패", e); } };
const SCREENS = SCENES.map((s, k) => ({ s, k })).concat([{ t: "end" }]);
const $ = (h) => { const d = document.createElement("div"); d.innerHTML = h; return d; };
const esc = (t) => String(t).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const S = (s) => (st.sc[s.id] = st.sc[s.id] || { answer: null, memo: "", start: null, end: null, act: 0 });
function tick() { document.getElementById("clock").textContent = `${((st.act || 0) / 60000).toFixed(1)}분`; }
function act() {
  const now = Date.now();
  if (st.last != null && !st.done && now - st.last <= IDLE) {
    const d = now - st.last, sc = SCREENS[st.i];
    st.act = (st.act || 0) + d;
    if (sc && sc.s) { const a = S(sc.s); a.act = (a.act || 0) + d; }
  }
  st.last = now;
}
["pointerdown", "keydown"].forEach((e) => document.addEventListener(e, act, true));
document.addEventListener("scroll", act, { capture: true, passive: true });
function bible(s) {
  return `<details class="verse" open><summary>성경 원문 · ${esc(s.range)} (개역한글) — 굵은 절이 이 그림의 순간</summary>
    <ol>${s.verses.map(([r, x, now]) => `<li${now ? ' class="now"' : ""}><span class="ref">${esc(r)}</span>${esc(x)}</li>`).join("")}</ol></details>`;
}
function pic(key, tag) { return `<button type="button" class="card big" data-k="${key}"><div class="frame" style="aspect-ratio:1216/640"><img src="${IMGS[key]}" alt="${tag}" style="width:100%;left:0;top:0"></div><span class="tag">${tag}</span><span class="zoom">크게</span></button>`; }
function next() { st.i = Math.min(SCREENS.length - 1, st.i + 1); save(); render(); }
function render() {
  if (!st.t0) st.t0 = Date.now();
  const sc = SCREENS[st.i], app = document.getElementById("app");
  document.getElementById("prev").disabled = st.i === 0;
  app.innerHTML = "";
  if (sc.t === "end") return renderEnd(app);
  const s = sc.s, a = S(s);
  if (!a.start) a.start = Date.now();
  app.append($(`<div class="bar"><span>장면 ${sc.k + 1}/${SCENES.length}</span><span>두 그림 비교</span></div>
    <h1>${esc(s.title)} · ${esc(s.range)}</h1>${bible(s)}
    <h2>굵은 절에 더 맞게 그린 쪽은?</h2>
    <p class="hint">위가 왼쪽, 아래가 오른쪽입니다(넓은 화면에서는 나란히). 누르면 크게 봅니다.</p>
    <div class="pair">${pic(s.left, "왼쪽")}${pic(s.right, "오른쪽")}</div>
    <textarea id="memo" rows="3" placeholder="메모(선택) — 왜 그쪽인지, 둘 다 아니면 무엇이 틀렸는지">${esc(a.memo)}</textarea>
    <div class="answer3"><button class="b main" id="pickL" type="button">왼쪽</button><button class="b main" id="pickR" type="button">오른쪽</button><button class="b no" id="pickN" type="button">둘 다 아님</button></div>`));
  app.querySelectorAll("[data-k]").forEach((b) => b.onclick = () => zoom(b.dataset.k));
  const memo = document.getElementById("memo");
  memo.oninput = (e) => { a.memo = e.target.value; grow(memo); save(); };
  grow(memo);
  const done = (ans) => { a.answer = ans; a.end = Date.now(); next(); };
  document.getElementById("pickL").onclick = () => done("left");
  document.getElementById("pickR").onclick = () => done("right");
  document.getElementById("pickN").onclick = () => done("none");
  save(); window.scrollTo(0, 0);
}
function verdict() {
  const now = st.done || Date.now(), out = { task: TASK, kind: "ab", human_minutes: +((now - st.t0) / 60000).toFixed(2), active_minutes: +((st.act || 0) / 60000).toFixed(2), idle_ms: IDLE, screens: SCREENS.length - 1, scenes: {} };
  SCENES.forEach((s) => {
    const a = S(s), chose = a.answer === "none" || !a.answer ? a.answer : ((a.answer === "left") === (s.left_is === "A") ? "A" : "final");
    out.scenes[s.id] = { answer: a.answer, chose, left: s.left, right: s.right, memo: a.memo,
      minutes: a.start && a.end ? +((a.end - a.start) / 60000).toFixed(2) : null, active_minutes: +((a.act || 0) / 60000).toFixed(2) };
  });
  return out;
}
function renderEnd(app) {
  const missing = SCENES.filter((s) => !S(s).answer).map((s) => s.title);
  app.append($(`<div class="bar"><span>끝</span><span>장면 ${SCENES.length - missing.length}/${SCENES.length} 답함</span></div>
    <h2>판정 문장을 복사해 대화에 붙여 주세요</h2>
    ${missing.length ? `<p class="hint">아직 답하지 않은 장면: ${esc(missing.join(", "))} — 「이전」으로 돌아가 답하세요.</p>` : ""}
    <div class="row"><button class="b main" id="copy" type="button">판정 문장 복사</button><span class="hint" id="okc"></span></div>
    <textarea id="out" readonly></textarea>`));
  const ta = document.getElementById("out");
  ta.value = `판정 task ${TASK}\n` + JSON.stringify(verdict());
  document.getElementById("copy").onclick = () => {
    if (!st.done) st.done = Date.now();
    save(); tick();
    ta.value = `판정 task ${TASK}\n` + JSON.stringify(verdict());
    navigator.clipboard.writeText(ta.value).then(() => { document.getElementById("okc").textContent = "복사됨"; })
      .catch(() => { ta.focus(); ta.select(); document.getElementById("okc").textContent = "자동 복사가 막혀 글을 선택해 두었습니다. 직접 복사하세요."; });
  };
}
function zoom(k) {
  const ov = document.getElementById("ov");
  ov.innerHTML = `<div class="row" style="justify-content:space-between"><b>크게 보기</b><button class="b main" id="close" type="button">닫기</button></div><img src="${IMGS[k]}" alt="">`;
  document.getElementById("close").onclick = () => { ov.hidden = true; };
  ov.hidden = false;
}
function grow(el) { el.style.height = "auto"; el.style.height = el.scrollHeight + 2 + "px"; }
function keepVisible(el) { setTimeout(() => el.scrollIntoView({ block: "center", behavior: "smooth" }), 250); }
document.addEventListener("focusin", (e) => { if (e.target.id === "memo") { document.body.classList.add("typing"); keepVisible(e.target); } });
document.addEventListener("focusout", (e) => { if (e.target.id === "memo") document.body.classList.remove("typing"); });
if (window.visualViewport) visualViewport.addEventListener("resize", () => { const el = document.activeElement; if (el && el.id === "memo") keepVisible(el); });
const renderBase = render;
render = function () {
  renderBase();
  document.querySelectorAll(".verse ol").forEach((ol) => { const li = ol.querySelector("li.now"); if (li) ol.scrollTop = li.offsetTop - ol.offsetTop; });
};
document.getElementById("prev").onclick = () => { st.i = Math.max(0, st.i - 1); save(); render(); };
document.getElementById("next").onclick = next;
if (st.i >= SCREENS.length) st.i = 0;
render(); setInterval(tick, 5000); tick();
</script>
"""


PAGE_M = (PAGE.replace("<title>낱말 사전 그림 비교 382</title>", "<title>요단 순간 그림 비교 385</title>")
          .replace("const TASK = 382;", "const TASK = 385;")
          .replace("<h2>굵은 절에 더 맞게 그린 쪽은?</h2>", "<h2>굵은 절에 맞게 그린 쪽은?</h2>")
          .replace('((a.answer === "left") === (s.left_is === "A") ? "A" : "final")', '(a.answer === "left" ? s.left_is : s.right_is)')
          .replace('<div class="pair">${pic(s.left, "왼쪽")}${pic(s.right, "오른쪽")}</div>',
                   '<div class="pair">${pic(s.left, "왼쪽")}${pic(s.right, "오른쪽")}</div>${all8(s)}')
          .replace("function next() {", """function all8(s) {
  return `<details class="more"><summary>최종 회차 ${s.all.length}장 전부(기계 불통과 포함 · 누르면 크게)</summary><div class="grid8">${s.all.map((k) =>
    `<button type="button" class="card" data-k="${k}"><img src="${IMGS[k]}" alt="" style="width:100%;display:block"><span class="tag">s${k.split(":")[2]}</span></button>`).join("")}</div></details>`;
}
function next() {""")
          .replace(".answer3 {", ".grid8 { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; margin: 8px 0; }\n.more summary { cursor: pointer; padding: 6px 0; }\n.answer3 {"))
assert PAGE_M.count("${all8(s)}") == 1 and "const TASK = 385;" in PAGE_M and "s.right_is" in PAGE_M


def cand_moment(m, out=None):
    """385 — 장면마다 1화면: 최종(사다리 끝) 회차 기계 1위·2위를 블라인드 좌우(장면 id 해시로 고정) + 접힌 칸에 그 회차 8장 전부."""
    import make_cand_page as C
    for w, q in C.SIZES:
        scenes, data = [], {}
        for sid in FX["scenes"]:
            fr = m["ladder"][sid]["end"]
            r = ranked(m, fr, sid)
            one, two = f"{fr}:{sid}:{r[0]}", f"{fr}:{sid}:{r[1]}"
            left, right = (one, two) if left_is_a(sid) else (two, one)
            for s in FX["seeds"]:
                data[f"{fr}:{sid}:{s}"] = P.uri(Image.open(img_path(fr, sid, s)), w, q)
            spec = canon(sid)
            scenes.append({"id": sid, "title": spec["title"], "range": spec["verses"]["range"], "ab": True, "reject": False,
                           "left": left, "right": right, "left_is": "1위" if left == one else "2위", "right_is": "1위" if right == one else "2위",
                           "final_round": fr, "all": [f"{fr}:{sid}:{s}" for s in FX["seeds"]], "verses": C.scripture(sid)})
        page = (PAGE_M.replace("/*STYLE*/", C.STYLE + C.VERSE_STYLE).replace("/*SCENES*/[]", json.dumps(scenes, ensure_ascii=False))
                .replace("/*IMGS*/{}", json.dumps(data)))
        if len(page) <= P.LIMIT:
            break
    out = out or os.path.join(J.PAGES, f"{SET}-cand.html")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w", encoding="utf-8").write(page)
    m["cand"] = {s["id"]: {k: s[k] for k in ("final_round", "left", "right", "left_is", "right_is")} for s in scenes}
    save_m(m)
    print(f"[PlainWords] 후보 화면 {out} {len(page) / 1e6:.2f}MB · {w}px q{q} · 화면 {len(scenes)}", flush=True)
    return out


def verdict_moment(m):
    """385 고정 절 — 사람이 후보 하나를 고르면 순간 채택, 「둘 다 아님」이면 보류."""
    picked = {sid: a["chose"] for sid, a in m["human"]["scenes"].items()}
    line = "판정: 순간 채택" if any(c in ("1위", "2위") for c in picked.values()) else "판정: 보류"
    print(" · ".join(f"{sid.split('-', 2)[2]} {c}" for sid, c in picked.items()))
    print(line)
    return line


def b2(m):
    """specs/b2/의 손으로 쓴 사본을 검사(삽입꼴·verse·금지어·512)한 뒤 생성·예측."""
    specs = {sid: json.load(open(spec_path("b2", sid), encoding="utf-8")) for sid in FX["scenes"]}
    R = m["rounds"].setdefault("b2", {"scenes": {}})
    for sid in specs:
        R["scenes"].setdefault(sid, {"seeds": [], "sec": 0.0})["levels"] = m["ladder"][sid]["levels"]
        R["scenes"][sid]["base"] = m["ladder"][sid]["end"]
    if not check(m):
        sys.exit("[PlainWords] b2 사본 검사 불통 — 생성하지 않음")
    generate(m, "b2", specs)
    judge(m, "b2")
    report(m, "b2")


def record(m, path):
    """task 383·385 — 후보 화면 「판정 문장」(첫 줄 `판정 task <과제>` + JSON 한 줄) → metrics human."""
    v = json.loads(open(path, encoding="utf-8").read().split("\n", 1)[1])
    assert v["task"] == TASK and v["kind"] == "ab", v.get("task")
    # 387 회고: 사람 답 파일은 루프 검사 꼴 *<과제>*verdict*(과제 번호가 verdict 앞) — 386·387 두 번 어긋남
    assert TASK < 387 or re.search(rf"{TASK}.*verdict", os.path.basename(path)), f"사람 답 파일 이름은 *{TASK}*verdict* 꼴: {path}"
    for sid, a in v["scenes"].items():   # 좌우 출처가 화면을 만든 그대로인지 — 다른 화면의 답이 섞이지 않게
        assert (a["left"], a["right"]) == (m["cand"][sid]["left"], m["cand"][sid]["right"]), sid
    m["human"] = {"human_minutes": v["human_minutes"], "active_minutes": v["active_minutes"], "screens": v["screens"],
                  "scenes": {sid: {k: a[k] for k in ("answer", "chose", "memo", "minutes", "active_minutes")} for sid, a in v["scenes"].items()}}
    save_m(m)
    print(f"[PlainWords] 사람 답 기록 — 화면 {v['screens']} · 쉼 뺀 {v['active_minutes']}분 · " +
          " · ".join(f"{sid.split('-', 2)[2]} {a['chose']}" for sid, a in v["scenes"].items()), flush=True)


def verdict(m):
    """고정 절 「판정:」 규칙 셋 → 판정 한 줄(줄마다 셈을 함께)."""
    sids = list(FX["scenes"])
    gain = {sid: scene_hits(m, final(m, sid), sid) - scene_hits(m, "A", sid) for sid in sids}
    r1 = sum(g >= 3 for g in gain.values())
    a_sum, f_sum = sum(other_sum(m, "A", s) for s in sids), sum(other_sum(m, final(m, s), s) for s in sids)
    r3 = sum(m["human"]["scenes"][s]["chose"] == "final" for s in sids)
    rules = [(1, r1 >= 2, f"낱말 맞힘 +3 이상 장면 {r1} ≥ 2 ({' · '.join(f'{s.split(chr(45), 2)[2]} {g:+d}' for s, g in gain.items())})"),
             (2, f_sum <= a_sum + FX["revert_plus"], f"다른 칸 틀림 합 최종 {f_sum} ≤ A {a_sum} + {FX['revert_plus']}"),
             (3, r3 >= 3, f"사람이 최종을 고른 화면 {r3} ≥ 3")]
    for n, ok, why in rules:
        print(f"규칙 {n} {'지킴' if ok else '어김'} — {why}")
    bad = [n for n, ok, _ in rules if not ok]
    line = "판정: 낱말 사전 채택" if not bad else f"판정: 보류 (어긴 규칙 {', '.join(map(str, bad))})"
    print(line)
    return line


def lexicon(m):
    """사다리가 맞힌 단위 → 사전 verified_level(그림 증거만 — 문구 한계·상한·밀어냄은 적지 않음)."""
    d = json.load(open(WORDS, encoding="utf-8"))
    hit = {uid: u for sid, st in m["ladder"].items() if not sid.startswith("_") for uid, u in st["units"].items() if u["stop"] == "맞음"}
    mine = {u["id"] for sid in FX["scenes"] for u in units(sid)}
    for e in d["words"]:
        if e["id"] not in mine:   # 385: 이 묶음 단위만 고친다 — 다른 묶음이 적은 그림 증거는 그대로
            continue
        e.pop("verified_level", None)
        if e["id"] in hit:
            u = hit[e["id"]]
            e["verified_level"] = {"level": u["level"], "status": u["status"], "with": u["with"]}
    json.dump(d, open(WORDS, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    open(WORDS, "a").write("\n")
    print(f"[PlainWords] 사전 verified_level {len(hit)}항목: " + " · ".join(f"{k} {u['level']} {u['status']}" for k, u in hit.items()), flush=True)


# --- task#387 장면 구절(요단) — 사다리 없이 r1 한 회차 · 장면 요소 문항 · 편집 갈래 ------------------------
K387 = ("J1", "J1-prop", "O1", "E", "W")      # r1 그림마다 물을 종류(고정 절)
KE387 = ("J1", "J1-prop", "E", "W")            # 편집본마다(이상한 점은 기록용이라 뺌)


def wrong387(m, rnd, sid, s, key=None):
    """틀림 칸(고정 절) = J1(지물 칸은 J1-prop) + E + W의 「틀림」 수 — 「다윗 바로 앞」은 뺀다. key = 편집본 답 키."""
    if key:
        a = lambda k: (m["answers"].get(rnd, {}).get(k, {}).get(key) or {}).get("answers") or {}
        j, p = a("J1"), a("J1-prop")
        ans = {**{q: (p.get(q) if J.cls(q) == "prop" and q in p else v) for q, v in j.items()}, **a("E"), **a("W")}
    else:
        ans = {**j1(m, rnd, sid, s), **_a(m, rnd, "E", sid, s), **feats(m, rnd, sid, s)}
    return sum(1 for q, v in ans.items() if v == "틀림" and q != FX["scenes"][sid]["before_qid"])


def ranked387(m, sid):
    order = FX["seeds"]
    return sorted(seeds_of(m, "r1", sid), key=lambda s: (wrong387(m, "r1", sid, s), order.index(s)))


def scene387(m):
    """r1 = 고친 정본 그대로 8장 → 기계 판정(J1·J1-prop·O1·E·W) → 문구 1위·2위."""
    lv = {sid: start_levels(sid) for sid in FX["scenes"]}
    generate(m, "r1", {sid: render(sid, lv[sid]) for sid in FX["scenes"]},
             base={sid: (lv[sid], "canon") for sid in FX["scenes"]}, raised={sid: [] for sid in FX["scenes"]})
    miss = judge(m, "r1", K387)
    for sid in FX["scenes"]:
        st = m["ladder"].setdefault(sid, {"levels": lv[sid], "end": "r1", "rounds": ["r1"], "units": {}})
        for u in units(sid):
            st["units"][u["id"]] = {"level": lv[sid][u["id"]], "stop": "사다리 없음(387 — r1 한 회차)", "status": None, "with": [], "hist": []}
        r = ranked387(m, sid)
        m.setdefault("phrase", {})[sid] = {"ranked": r, "top": r[0], "second": r[1]}
    save_m(m)
    report387(m)
    return miss


def report387(m):
    for sid in FX["scenes"]:
        ss = seeds_of(m, "r1", sid)
        hit = lambda q, kind="E": sum(_a(m, "r1", kind, sid, s).get(q) == "맞음" for s in ss)
        jq = {q for s in ss for q in j1(m, "r1", sid, s)}
        print(f"[JordanScene] {sid} r1 {len(ss)}장 · " + " · ".join(f"{e['id']} {hit(e['id'])}/{len(ss)}" for e in elem_qs(sid)), flush=True)
        print("[JordanScene] J1 맞음 " + " · ".join(f"{q} {sum(j1(m, 'r1', sid, s).get(q) == '맞음' for s in ss)}" for q in sorted(jq)), flush=True)
        print(f"[JordanScene] 낱말 " + " · ".join(f"{u['id']} {unit_hits(m, 'r1', sid, u['id'])}/{len(ss)}" for u in units(sid)) +
              " · 틀림 칸 " + " · ".join(f"s{s} {wrong387(m, 'r1', sid, s)}" for s in ss), flush=True)
        if sid in m.get("phrase", {}):
            print(f"[JordanScene] 문구 1위 s{m['phrase'][sid]['top']} · 2위 s{m['phrase'][sid]['second']}", flush=True)


def edit_boxes():
    """고정 절 추가분(```json edit-boxes) — 바탕 시드마다 크롭(L, T, 변)·마스크 상자(원본 좌표). 편집 전에 커밋."""
    t = open(NOTES, encoding="utf-8").read()
    g = re.search(r"```json edit-boxes\n(.*?)\n```", t, re.S)
    return json.loads(g.group(1)) if g else None


def edit_img(sid, cid):
    return os.path.join(OUT, "edit", sid, f"{cid}.png")


def edit387(m):
    """문구 1위의 「다윗 바로 앞」이 틀림이면 문구 1위·2위 바탕 × 지시 둘 × klein 시드 셋 = 12장 → 기계 거름 → 편집 1위."""
    import gen_local_edit as LE
    for sid, c in FX["scenes"].items():
        ph = m["phrase"][sid]
        top = ph["top"]
        if _a(m, "r1", "E", sid, top).get(c["before_qid"]) == "맞음":
            m["edit"] = {"status": "건너뜀", "reason": f"문구 1위 s{top}의 「다윗 바로 앞」이 이미 맞음"}
            save_m(m)
            print(f"[JordanScene] 편집 건너뜀 — {m['edit']['reason']}", flush=True)
            continue
        bx = edit_boxes()
        if not bx:
            sys.exit("[JordanScene] 편집 상자 없음 — 고정 절 추가분(```json edit-boxes)을 먼저 쓰고 커밋")
        bases = [ph["top"], ph["second"]]
        E = m.setdefault("edit", {"status": "편집", "bases": bases, "candidates": [], "sec": 0.0})
        assert E["bases"] == bases and set(map(int, bx["bases"])) == set(bases), (E["bases"], bx)
        for b in bases:
            crop, box = tuple(bx["bases"][str(b)]["crop"]), tuple(bx["bases"][str(b)]["box"])
            for arm, prompt in FX["edit"]["arms"].items():
                for k in FX["edit"]["klein_seeds"]:
                    cid = f"{arm}-b{b}-k{k}"
                    if any(x["id"] == cid for x in E["candidates"]):
                        continue
                    if busy():
                        sys.exit(f"[JordanScene] 다른 생성 프로세스가 돈다 — 겹치지 않게 멈춤:\n{busy()}")
                    out = edit_img(sid, cid)
                    os.makedirs(os.path.dirname(out), exist_ok=True)
                    r = LE.edit(img_path("r1", sid, b), crop, box, arm, k, out, prompt=prompt)
                    E["sec"] = round(E["sec"] + r["sec"], 1)
                    if r["status"] != "ok":
                        print(f"[JordanScene] 편집 {cid} 실패", flush=True)
                        continue
                    E["candidates"].append({"id": cid, "arm": arm, "base": b, "seed": k, "image": out, "crop": list(crop), "box": list(box),
                                            "prompt": prompt, "sec": r["sec"]})
                    save_m(m)
                    print(f"[JordanScene] 편집 {cid} {r['sec']}s", flush=True)
        judge_edit(m, sid)


def edit_items(m, sid, kind):
    """편집본 → 판정 항목: 바탕 시드의 r1 문항·크롭 그대로(E는 「한 사람뿐」 추가)."""
    base = {it["seed"]: it for it in items(m, "r1", "E" if kind == "E" else kind, [sid])}
    out = []
    for x in m["edit"]["candidates"]:
        it = dict(base[x["base"]])
        qs = elem_qs(sid, extra=True) if kind == "E" else it["qs"]
        out.append({**it, "key": f"edit:{sid}:{x['id']}", "task": f"edit-{x['id']}", "src": x["image"], "qs": qs, "qids": [q["id"] for q in qs]})
    return out


def judge_edit(m, sid, workers=8):
    done = lambda k, key: (m["answers"].get("edit", {}).get(k, {}).get(key) or {}).get("answers")
    todo = [(k, it) for k in KE387 for it in edit_items(m, sid, k) if not done(k, it["key"])]
    print(f"[JordanScene] 편집본 판정 {len(todo)}건", flush=True)
    with ThreadPoolExecutor(workers) as ex:
        list(ex.map(lambda job: ask(m, "edit", *job), todo))
    c = FX["scenes"][sid]
    E = m["edit"]
    ea = lambda x: (m["answers"]["edit"].get("E", {}).get(f"edit:{sid}:{x['id']}") or {}).get("answers") or {}
    arms, ks = list(FX["edit"]["arms"]), FX["edit"]["klein_seeds"]
    for x in E["candidates"]:
        x["required_ok"] = all(ea(x).get(q) == "맞음" for q in c["edit_required"])
        x["wrong"] = wrong387(m, "edit", sid, x["base"], key=f"edit:{sid}:{x['id']}")
    ok = sorted((x for x in E["candidates"] if x["required_ok"]),
                key=lambda x: (x["wrong"], E["bases"].index(x["base"]), arms.index(x["arm"]), ks.index(x["seed"])))
    E["top"] = ok[0]["id"] if ok else None
    E["top_reason"] = (f"{len(ok)}장이 「다윗 바로 앞」·「엎드려 빎」·「한 사람뿐」을 모두 맞음 — 그중 틀림 칸 최소" if ok
                       else "「다윗 바로 앞」·「엎드려 빎」·「한 사람뿐」을 모두 맞은 편집본 없음")
    save_m(m)
    for x in E["candidates"]:
        a = ea(x)
        print(f"[JordanScene] {x['id']} " + " ".join(f"{q.split('.')[-1]}={a.get(q, '-')}" for q in c["edit_required"]) + f" · 틀림 {x['wrong']}", flush=True)
    print(f"[JordanScene] 편집 1위 {E['top']} — {E['top_reason']}", flush=True)


PAGE_S = (PAGE_M.replace("<title>요단 순간 그림 비교 385</title>", "<title>요단 장면 그림 비교 387</title>")
          .replace("const TASK = 385;", "const TASK = 387;")
          .replace("<h2>굵은 절에 맞게 그린 쪽은?</h2>", "<h2>장면 구절에 맞게 그린 쪽은?</h2>")
          .replace("— 굵은 절이 이 그림의 순간</summary>", "— 장면 구절 전부, 굵은 절이 이 그림의 순간</summary>")
          .replace("<summary>최종 회차 ${s.all.length}장 전부(기계 불통과 포함 · 누르면 크게)</summary>",
                   "<summary>문구 8장·편집본 전부 ${s.all.length}장(기계 불통과 포함 · 누르면 크게)</summary>")
          .replace("${s.all.map((k) =>", "${s.all.map(([k, t]) =>")
          .replace('<span class="tag">s${k.split(":")[2]}</span>', '<span class="tag">${esc(t)}</span>'))
assert "const TASK = 387;" in PAGE_S and "장면 구절에 맞게" in PAGE_S and "([k, t]) =>" in PAGE_S and "${esc(t)}</span></button>`).join" in PAGE_S


def cand387(m, out=None):
    """1화면: 문구 1위 / 편집 1위(없거나 건너뜀이면 문구 2위) 블라인드 좌우 + 접힌 칸에 r1 8장·편집 12장."""
    import make_cand_page as C
    for w, q in C.SIZES:
        scenes, data = [], {}
        for sid in FX["scenes"]:
            ph, E = m["phrase"][sid], m.get("edit", {})
            one = f"r1:{sid}:{ph['top']}"
            two, two_is = (f"edit:{sid}:{E['top']}", "편집 1위") if E.get("top") else (f"r1:{sid}:{ph['second']}", "문구 2위")
            for s in FX["seeds"]:
                data[f"r1:{sid}:{s}"] = P.uri(Image.open(img_path("r1", sid, s)), w, q)
            for x in E.get("candidates", []):
                data[f"edit:{sid}:{x['id']}"] = P.uri(Image.open(x["image"]), w, q)
            left, right = (one, two) if left_is_a(sid) else (two, one)
            spec = canon(sid)
            scenes.append({"id": sid, "title": spec["title"], "range": spec["verses"]["range"], "ab": True, "reject": False,
                           "left": left, "right": right, "left_is": "문구 1위" if left == one else two_is, "right_is": "문구 1위" if right == one else two_is,
                           "all": [[f"r1:{sid}:{s}", f"문구 s{s}"] for s in FX["seeds"]] +
                                  [[f"edit:{sid}:{x['id']}", f"편집 {x['arm']} 바탕 s{x['base']} k{x['seed']}"] for x in E.get("candidates", [])],
                           "verses": C.scripture(sid)})
        page = (PAGE_S.replace("/*STYLE*/", C.STYLE + C.VERSE_STYLE).replace("/*SCENES*/[]", json.dumps(scenes, ensure_ascii=False))
                .replace("/*IMGS*/{}", json.dumps(data)))
        if len(page) <= P.LIMIT:
            break
    out = out or os.path.join(J.PAGES, f"{SET}-cand.html")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w", encoding="utf-8").write(page)
    m["cand"] = {s["id"]: {k: s[k] for k in ("left", "right", "left_is", "right_is")} for s in scenes}
    save_m(m)
    print(f"[JordanScene] 후보 화면 {out} {len(page) / 1e6:.2f}MB · {w}px q{q} · 화면 {len(scenes)}", flush=True)
    return out


def verdict387(m):
    """고정 절 — 사람이 후보 하나를 고르면 장면 채택, 「둘 다 아님」이면 보류."""
    picked = {sid: a["chose"] for sid, a in m["human"]["scenes"].items()}
    line = "판정: 장면 채택" if any(c not in (None, "none") for c in picked.values()) else "판정: 보류"
    print(" · ".join(f"{sid.split('-', 2)[2]} {c}" for sid, c in picked.items()))
    print(line)
    return line


def approve387(m):
    """채택이면 고른 그림을 정본 approved.final로 — 문구 그림은 night-pick(바탕), 편집본은 local-edit(386과 같은 꼴) + 레포 사본."""
    import shutil
    import approve
    for sid, a in m["human"]["scenes"].items():
        if a["chose"] in (None, "none"):
            continue
        key = m["cand"][sid]["left" if a["answer"] == "left" else "right"]
        keep = os.path.join(SAMPLES, f"approved-{sid}.png")
        rel = os.path.relpath(keep, HERE)
        spec = approve.load_spec(sid)
        if key.startswith("edit:"):
            x = next(c for c in m["edit"]["candidates"] if c["id"] == key.split(":", 2)[2])
            shutil.copyfile(x["image"], keep)
            steps = [{k: x[k] for k in ("id", "arm", "seed", "crop", "box", "prompt")} | {"base_src": f"jordan-scene r1 s{x['base']}"}]
            spec = approve.local_edit(spec, x["base"], rel, steps, "user")
        else:
            s = int(key.split(":")[2])
            shutil.copyfile(img_path("r1", sid, s), keep)
            spec = approve.night_pick(spec, s, "base", rel, "user")
        approve.save_spec(spec)
        print(f"[JordanScene] 승인 {sid} ← {key} ({a['chose']}) · 사본 {rel}", flush=True)


def check387(m):
    """r1 8장 · 그림마다 다섯 종류 답(빈 답 0, 문항 빠짐 0) · 편집이 있으면 12장 답과 1위/사유."""
    bad = []
    for sid in FX["scenes"]:
        ss = seeds_of(m, "r1", sid) if "r1" in m["rounds"] else []
        if sorted(ss) != sorted(FX["seeds"]):
            bad.append(f"r1 {sid} 시드 {ss}")
        for kind in K387:
            for it in items(m, "r1", kind, [sid]) if ss else []:
                a = (m["answers"].get("r1", {}).get(kind, {}).get(it["key"]) or {}).get("answers")
                if not a or set(it["qids"]) - set(a):
                    bad.append(f"r1 {kind} {it['key']} 답 빠짐")
        if sid not in m.get("phrase", {}):
            bad.append(f"{sid} 문구 1위 없음")
        E = m.get("edit")
        if E and E["status"] == "편집":
            n = len(E["bases"]) * len(FX["edit"]["arms"]) * len(FX["edit"]["klein_seeds"])
            if len(E["candidates"]) != n:
                bad.append(f"편집 {len(E['candidates'])} ≠ {n}")
            for kind in KE387:
                for it in edit_items(m, sid, kind):
                    a = (m["answers"].get("edit", {}).get(kind, {}).get(it["key"]) or {}).get("answers")
                    if not a or set(it["qids"]) - set(a):
                        bad.append(f"edit {kind} {it['key']} 답 빠짐")
            if "top" not in E or not E.get("top_reason"):
                bad.append("편집 1위·사유 없음")
        elif E and not E.get("reason"):
            bad.append("편집 건너뜀 사유 없음")
    return bad

# --- task#388 구도 가이드(요단) — CN lite + 깊이 가이드: 시험 1장 → 격자 → 고른 설정 8시드 → 후보 1화면 ----------------
GUIDE = os.path.join(SAMPLES, "guide.png")
K388 = ("J1", "J1-prop", "O1", "E", "W", "S")   # 본 실행 그림마다
KG388 = ("J1", "J1-prop", "E", "W", "S")         # 격자 그림마다(이상한 점은 기록용이라 뺌)
REF387 = os.path.expanduser("~/.local/biblemap-imggen/jordan-scene/r1/authored-david-returns-jerusalem/s101.png")   # 387 문구 1위(참고)


def grid_rnd(scale, k):
    return f"g-{scale}-{k}"


def one388(m):
    """시험 1장 — 경로·장당 시간·피크 메모리 + 화풍·장면 요소 문항."""
    c, sid = FX["one"], next(iter(FX["scenes"]))
    lv = start_levels(sid)
    generate(m, "one", {sid: render(sid, lv)}, seeds=[c["seed"]], base={sid: (lv, "canon")}, raised={sid: []},
             cn={"scale": c["scale"], "cn_steps": c["cn_steps"]})
    judge(m, "one", ("S", "E"), sids=[sid])
    sc = m["rounds"]["one"]["scenes"][sid]
    print(f"[JordanGuide] 시험 s{c['seed']} {sc['sec']}s · 피크 {sc.get('peak_gib')}GiB · 화풍 {_a(m, 'one', 'S', sid, c['seed'])} · "
          f"장면 요소 {_a(m, 'one', 'E', sid, c['seed'])}", flush=True)


def wrong388(m, rnd, sid, s):
    """틀림 칸(고정 절) = J1(지물 칸은 J1-prop) + E + W + S의 「틀림」 수 — 「다윗 바로 앞」도 넣는다(목표가 배치)."""
    ans = {**j1(m, rnd, sid, s), **_a(m, rnd, "E", sid, s), **feats(m, rnd, sid, s), **_a(m, rnd, "S", sid, s)}
    return sum(1 for v in ans.values() if v == "틀림")


def grid388(m):
    """격자 = 강도 × CN 스텝 × 시드 → 기계 판정 → 통과 설정(화풍·복제 두 문항을 두 시드 모두 맞음) 중 배치 문항 맞힘 최대."""
    G, sid = FX["grid"], next(iter(FX["scenes"]))
    lv = start_levels(sid)
    cfgs = [(sc, k) for sc in G["scales"] for k in G["cn_steps"]]
    for sc, k in cfgs:
        generate(m, grid_rnd(sc, k), {sid: render(sid, lv)}, seeds=G["seeds"], base={sid: (lv, "canon")}, raised={sid: []},
                 cn={"scale": sc, "cn_steps": k})
    miss = sum(len(judge(m, grid_rnd(sc, k), KG388)) for sc, k in cfgs)
    place = FX["scenes"][sid]["placement"]
    m["grid"] = [{"scale": sc, "cn_steps": k, "seed": s, "image": img_path(grid_rnd(sc, k), sid, s),
                  "sec": m["rounds"][grid_rnd(sc, k)]["scenes"][sid]["sec"], "peak_gib": m["rounds"][grid_rnd(sc, k)]["scenes"][sid].get("peak_gib"),
                  **{kind: _a(m, grid_rnd(sc, k), kind, sid, s) for kind in ("S", "E", "W")}, "J1": j1(m, grid_rnd(sc, k), sid, s),
                  "wrong": wrong388(m, grid_rnd(sc, k), sid, s)} for sc, k in cfgs for s in G["seeds"]]
    rows = lambda sc, k: [g for g in m["grid"] if (g["scale"], g["cn_steps"]) == (sc, k)]
    ok = [(sc, k) for sc, k in cfgs if all(v == "맞음" for g in rows(sc, k) for v in g["S"].values()) and all(g["S"] for g in rows(sc, k))]
    hits = {c: sum(g["E"].get(q) == "맞음" for g in rows(*c) for q in place) for c in cfgs}
    if ok:
        sc, k = min(ok, key=lambda c: (-hits[c], c[0], c[1]))
        m["grid_pick"] = {"scale": sc, "cn_steps": k, "placement_hits": hits[(sc, k)], "passed": [list(c) for c in ok],
                          "why": f"통과 {len(ok)}설정 중 배치 문항 맞힘 최대({hits[(sc, k)]}/{len(place) * len(G['seeds'])}) — 같으면 낮은 강도 → 적은 스텝"}
    else:
        m["grid_pick"] = {"none": "화풍·가이드 복제 두 문항을 두 시드 모두 맞힌 설정 없음"}
    save_m(m)
    report388(m)
    return miss


def scene388(m):
    """고른 설정 × 8시드 → 기계 판정(J1·J1-prop·O1·E·W·S) → 1위·2위(틀림 칸 최소, 같으면 시드 순서)."""
    pk = m.get("grid_pick") or {}
    if "none" in pk or not pk:
        sys.exit(f"[JordanGuide] 격자 통과 설정 없음 — 본 실행 안 함: {pk}")
    lv = {sid: start_levels(sid) for sid in FX["scenes"]}
    generate(m, "r1", {sid: render(sid, lv[sid]) for sid in FX["scenes"]}, base={sid: (lv[sid], "canon") for sid in FX["scenes"]},
             raised={sid: [] for sid in FX["scenes"]}, cn={"scale": pk["scale"], "cn_steps": pk["cn_steps"]})
    miss = judge(m, "r1", K388)
    for sid in FX["scenes"]:
        st = m["ladder"].setdefault(sid, {"levels": lv[sid], "end": "r1", "rounds": ["r1"], "units": {}})
        for u in units(sid):
            st["units"][u["id"]] = {"level": lv[sid][u["id"]], "stop": "사다리 없음(388 — 구도 가이드 한 회차)", "status": None, "with": [], "hist": []}
        r = sorted(seeds_of(m, "r1", sid), key=lambda s: (wrong388(m, "r1", sid, s), FX["seeds"].index(s)))
        m.setdefault("phrase", {})[sid] = {"ranked": r, "top": r[0], "second": r[1]}
    save_m(m)
    report388(m)
    return miss


def report388(m):
    for sid, c in FX["scenes"].items():
        qs = [e["id"] for e in c["elements"]] + [q["id"] for q in c["style"]]
        for g in m.get("grid", []):
            print(f"[JordanGuide] 격자 {g['scale']}·{g['cn_steps']}스텝 s{g['seed']} 틀림 {g['wrong']} · " +
                  " ".join(f"{q.split('.', 1)[1]}={({**g['E'], **g['S']}).get(q, '-')}" for q in qs), flush=True)
        if m.get("grid_pick"):
            print(f"[JordanGuide] 격자 고름 {m['grid_pick']}", flush=True)
        if "r1" in m["rounds"]:
            ss = seeds_of(m, "r1", sid)
            print("[JordanGuide] 본 실행 " + " · ".join(f"{q} {sum(({**_a(m, 'r1', 'E', sid, s), **_a(m, 'r1', 'S', sid, s)}).get(q) == '맞음' for s in ss)}/{len(ss)}" for q in qs), flush=True)
            jq = sorted({q for s in ss for q in j1(m, "r1", sid, s)})
            print("[JordanGuide] J1 맞음 " + " · ".join(f"{q} {sum(j1(m, 'r1', sid, s).get(q) == '맞음' for s in ss)}" for q in jq), flush=True)
            print("[JordanGuide] 낱말 " + " · ".join(f"{u['id']} {unit_hits(m, 'r1', sid, u['id'])}/{len(ss)}" for u in units(sid)) +
                  " · 틀림 칸 " + " · ".join(f"s{s} {wrong388(m, 'r1', sid, s)}" for s in ss), flush=True)
            if sid in m.get("phrase", {}):
                print(f"[JordanGuide] 1위 s{m['phrase'][sid]['top']} · 2위 s{m['phrase'][sid]['second']}", flush=True)


PAGE_G = (PAGE_S.replace("<title>요단 장면 그림 비교 387</title>", "<title>요단 구도 그림 비교 388</title>")
          .replace("const TASK = 387;", "const TASK = 388;")
          .replace("<summary>문구 8장·편집본 전부 ${s.all.length}장(기계 불통과 포함 · 누르면 크게)</summary>",
                   "<summary>가이드·본 실행·격자·387 참고 ${s.all.length}장(기계 불통과 포함 · 누르면 크게)</summary>"))
assert "const TASK = 388;" in PAGE_G and "387 참고" in PAGE_G


def cand388(m, out=None):
    """1화면: 1위 / 2위 블라인드 좌우 + 접힌 칸에 가이드 그림·본 실행 8장·격자 전부·387 문구 1위 s101(참고)."""
    import make_cand_page as C
    for w, q in C.SIZES:
        scenes, data = [], {}
        for sid in FX["scenes"]:
            ph = m["phrase"][sid]
            one, two = f"r1:{sid}:{ph['top']}", f"r1:{sid}:{ph['second']}"
            data["guide"] = P.uri(Image.open(GUIDE), w, q)
            data["ref387"] = P.uri(Image.open(REF387), w, q)
            for s in FX["seeds"]:
                data[f"r1:{sid}:{s}"] = P.uri(Image.open(img_path("r1", sid, s)), w, q)
            for g in m["grid"]:
                data[f"{grid_rnd(g['scale'], g['cn_steps'])}:{sid}:{g['seed']}"] = P.uri(Image.open(g["image"]), w, q)
            left, right = (one, two) if left_is_a(sid) else (two, one)
            spec = canon(sid)
            scenes.append({"id": sid, "title": spec["title"], "range": spec["verses"]["range"], "ab": True, "reject": False,
                           "left": left, "right": right, "left_is": "1위" if left == one else "2위", "right_is": "1위" if right == one else "2위",
                           "all": [["guide", "구도 가이드(깊이)"]] + [[f"r1:{sid}:{s}", f"본 실행 s{s}"] for s in FX["seeds"]] +
                                  [[f"{grid_rnd(g['scale'], g['cn_steps'])}:{sid}:{g['seed']}", f"격자 {g['scale']}·{g['cn_steps']}스텝 s{g['seed']}"] for g in m["grid"]] +
                                  [["ref387", "387 문구 1위 s101(참고)"]],
                           "verses": C.scripture(sid)})
        page = (PAGE_G.replace("/*STYLE*/", C.STYLE + C.VERSE_STYLE).replace("/*SCENES*/[]", json.dumps(scenes, ensure_ascii=False))
                .replace("/*IMGS*/{}", json.dumps(data)))
        if len(page) <= P.LIMIT:
            break
    out = out or os.path.join(J.PAGES, f"{SET}-cand.html")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w", encoding="utf-8").write(page)
    m["cand"] = {s["id"]: {k: s[k] for k in ("left", "right", "left_is", "right_is")} for s in scenes}
    save_m(m)
    print(f"[JordanGuide] 후보 화면 {out} {len(page) / 1e6:.2f}MB · {w}px q{q} · 화면 {len(scenes)}", flush=True)
    return out


def verdict388(m):
    """고정 절 — 격자 통과 없음이면 보류, 사람이 후보 하나를 고르면 장면 채택, 「둘 다 아님」이면 보류."""
    if "none" in (m.get("grid_pick") or {}):
        line = "판정: 보류"
        print(f"격자 통과 없음 — {m['grid_pick']['none']}")
    else:
        picked = {sid: a["chose"] for sid, a in m["human"]["scenes"].items()}
        line = "판정: 장면 채택" if any(c not in (None, "none") for c in picked.values()) else "판정: 보류"
        print(" · ".join(f"{sid.split('-', 2)[2]} {c}" for sid, c in picked.items()))
    print(line)
    return line


def approve388(m):
    """채택이면 고른 본 실행 그림을 정본 approved.final로(night-pick 바탕 꼴 + 가이드·설정) + 레포 사본."""
    import shutil
    import approve
    for sid, a in m["human"]["scenes"].items():
        if a["chose"] in (None, "none"):
            continue
        s = int(m["cand"][sid]["left" if a["answer"] == "left" else "right"].split(":")[2])
        keep = os.path.join(SAMPLES, f"approved-{sid}.png")
        rel = os.path.relpath(keep, HERE)
        shutil.copyfile(img_path("r1", sid, s), keep)
        spec = approve.night_pick(approve.load_spec(sid), s, "base", rel, "user")
        spec["approved"]["final"].update(guide=os.path.relpath(GUIDE, HERE), cn="2602 lite", **m["grid_pick"] and
                                         {k: m["grid_pick"][k] for k in ("scale", "cn_steps")})
        approve.save_spec(spec)
        print(f"[JordanGuide] 승인 {sid} ← s{s} ({a['chose']}) · 사본 {rel}", flush=True)


def check388(m):
    """격자 12장(장마다 S·E·J1 답 빈 답 0) · grid_pick · 설정이 있으면 본 실행 8장 · 종류마다 답 · 1위/2위."""
    bad, G = [], FX["grid"]
    n = len(G["scales"]) * len(G["cn_steps"]) * len(G["seeds"])
    if len(m.get("grid", [])) != n:
        bad.append(f"격자 {len(m.get('grid', []))} ≠ {n}")
    for g in m.get("grid", []):
        for kind in ("S", "E", "J1"):
            if not g.get(kind) or any(v not in ("맞음", "틀림") for v in g[kind].values()):
                bad.append(f"격자 {g['scale']}·{g['cn_steps']} s{g['seed']} {kind} 답 빠짐")
    pk = m.get("grid_pick")
    if not pk:
        bad.append("grid_pick 없음")
    elif "none" not in pk:
        for sid in FX["scenes"]:
            ss = seeds_of(m, "r1", sid) if "r1" in m["rounds"] else []
            if sorted(ss) != sorted(FX["seeds"]):
                bad.append(f"r1 {sid} 시드 {ss}")
            for kind in K388:
                for it in items(m, "r1", kind, [sid]) if ss else []:
                    a = (m["answers"].get("r1", {}).get(kind, {}).get(it["key"]) or {}).get("answers")
                    if not a or set(it["qids"]) - set(a):
                        bad.append(f"r1 {kind} {it['key']} 답 빠짐")
            if sid not in m.get("phrase", {}):
                bad.append(f"{sid} 1위 없음")
    return bad



def main(argv):
    if "--set" in argv:
        i = argv.index("--set")
        argv = argv[:i] + argv[i + 2:]
    cmd = argv[0]
    m = load_m()
    if cmd == "predict-a":
        predict_a(m)
    elif cmd == "one" and TASK == 388:
        one388(m)
    elif cmd == "grid":
        sys.exit(1 if grid388(m) else 0)
    elif cmd == "one":   # 시험 1장 — 경로 확인 + 고친 낱말이 보이는가(이 장의 특징 문항)
        sid = next(iter(FX["scenes"]))
        lv = start_levels(sid)
        generate(m, "r1", {sid: render(sid, lv)}, seeds=FX["seeds"][:1], base={sid: (lv, "A")}, raised={sid: list(lv)})
        judge(m, "r1", ("W", "W-prop", "E"), sids=[sid])
        s = FX["seeds"][0]
        print(f"[PlainWords] 시험 {sid} s{s} 특징 {feats(m, 'r1', sid, s)} · 장면 요소 {_a(m, 'r1', 'E', sid, s)}", flush=True)
    elif cmd == "ladder":
        ladder(m)
    elif cmd == "scene":   # 387·388 — 사다리 없이 r1 한 회차
        sys.exit(1 if {387: scene387, 388: scene388}[TASK](m) else 0)
    elif cmd == "edit":
        edit387(m)
    elif cmd == "approve":
        {387: approve387, 388: approve388}[TASK](m)
    elif cmd == "b2":
        b2(m)
    elif cmd == "cand":
        {385: cand_moment, 387: cand387, 388: cand388}.get(TASK, cand)(m, argv[1] if len(argv) > 1 else None)
    elif cmd == "check":
        sys.exit(0 if check(m) else 1)
    elif cmd == "record":
        record(m, argv[1])
    elif cmd == "verdict":
        {385: verdict_moment, 387: verdict387, 388: verdict388}.get(TASK, verdict)(m)
    elif cmd == "lexicon":
        lexicon(m)
    elif cmd == "report":
        if TASK in (387, 388):
            return {387: report387, 388: report388}[TASK](m)
        for rnd in m["rounds"]:
            report(m, rnd)
    else:
        sys.exit(f"알 수 없는 명령 {cmd}")


if __name__ == "__main__":
    main(sys.argv[1:])
