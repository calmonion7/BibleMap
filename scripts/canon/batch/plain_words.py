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
~/.local/biblemap-imggen/plain-words/<회차>/<장면>/s<시드>.png, 목록·답·사다리는 samples/plain-words/metrics.json."""
import copy, hashlib, json, os, re, subprocess, sys, threading, time
from concurrent.futures import ThreadPoolExecutor

from PIL import Image

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "batch"))
import derive_scene as D
import judge_items as J
import make_night_page as P

NOTES = os.path.join(HERE, "notes", "PLAIN-WORDS.md")
WORDS = os.path.join(HERE, "..", "..", "data", "scripture_words", "words.json")
SAMPLES = os.path.join(HERE, "samples", "plain-words")
SPECS = os.path.join(SAMPLES, "specs")
METRICS = os.path.join(SAMPLES, "metrics.json")
OUT = os.path.expanduser("~/.local/biblemap-imggen/plain-words")
SET = "plain-words"
KINDS = {"J1": ("v2", 1.0), "J1-prop": ("p2", 2.5), "O1": ("o1", 1.0), "W": ("v2", 1.0), "W-prop": ("p2", 2.5)}
LOCK = threading.Lock()
_TOK = []


def fixed():
    t = open(NOTES, encoding="utf-8").read()
    return json.loads(re.search(r"```json fixed\n(.*?)\n```", t, re.S).group(1))


FX = fixed()
LEX = {e["id"]: e for e in json.load(open(WORDS, encoding="utf-8"))["words"]}


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
    spec = copy.deepcopy(D.load(sid))
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
    return {u["id"]: "L2" if u["role"] == "core" else "L1" for u in units(sid)}


def spec_path(rnd, sid):
    return os.path.join(SPECS, rnd, f"{sid}.json")


def img_path(rnd, sid, s):
    return os.path.join(OUT, rnd, sid, f"s{s}.png")


# --- 그림 ----------------------------------------------------------------------
def busy():
    r = subprocess.run(["pgrep", "-fl", "mflux|run_scene.py --worker|gen_video_pilot|mlx_video"], capture_output=True, text=True)
    return r.stdout.strip()


def generate(m, rnd, specs, seeds=None, base=None, raised=None):
    """specs = {장면: 사본 명세} → 사본 저장 · 바탕 생성(없는 것만) · 상자 → metrics rounds[rnd]."""
    import run_scene
    import run_night as RN
    seeds = seeds or FX["seeds"]
    R = m["rounds"].setdefault(rnd, {"scenes": {}})
    for sid, spec in specs.items():
        os.makedirs(os.path.dirname(spec_path(rnd, sid)), exist_ok=True)
        json.dump(spec, open(spec_path(rnd, sid), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        p = D.route_prompt(spec)
        sc = R["scenes"].setdefault(sid, {"seeds": [], "sec": 0.0})
        sc.update(prompt=p, tokens=tokens(p), **({"levels": base[sid][0], "base": base[sid][1], "raised": raised[sid]} if base else {}))
        todo = [{"prompt": p, "seed": s, "w": 1216, "h": 640, "out": img_path(rnd, sid, s)} for s in seeds if not os.path.exists(img_path(rnd, sid, s))]
        print(f"[PlainWords] {rnd} {sid} {sc['tokens']}토큰 · {len(seeds)}장 중 {len(todo)}장 생성", flush=True)
        if todo:
            if busy():
                sys.exit(f"[PlainWords] 다른 생성 프로세스가 돈다 — 겹치지 않게 멈춤:\n{busy()}")
            os.makedirs(os.path.dirname(img_path(rnd, sid, seeds[0])), exist_ok=True)
            sc["sec"] = round(sc["sec"] + sum(run_scene.gen_zimage(todo, os.path.dirname(img_path(rnd, sid, seeds[0])))), 1)
        have = {x["seed"] for x in sc["seeds"]}
        canon = D.load(sid)
        for s in seeds:
            if s not in have:
                sc["seeds"].append({"seed": s, "base": img_path(rnd, sid, s), "boxes": RN.boxes(canon, img_path(rnd, sid, s))})
        save_m(m)


# --- 판정 ----------------------------------------------------------------------
def _seeds(m, rnd, sid):
    return m["rounds"][rnd]["scenes"][sid]["seeds"]


def j1_qs(m, rnd, sid):
    """A와 같은 J1 문항(정본 명세 → make_night_page.questions, A 과제와 같은 wide) — 크롭만 이 그림들 상자로."""
    seeds = _seeds(m, rnd, sid)
    task = FX["scenes"][sid]["a"]["task"]
    qs = P.questions(D.load(sid), {"seeds": seeds}, task in P.FACING370)
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


def items(m, rnd, kind, sids=None):
    out = []
    for sid in sids or m["rounds"][rnd]["scenes"]:
        spec = D.load(sid)
        qs = {"J1": lambda: j1_qs(m, rnd, sid), "J1-prop": lambda: [q for q in j1_qs(m, rnd, sid) if J.cls(q["id"]) == "prop"],
              "O1": lambda: j1_qs(m, rnd, sid), "W": lambda: word_qs(m, rnd, sid, False), "W-prop": lambda: word_qs(m, rnd, sid, True)}[kind]()
        if not qs:
            continue
        for x in _seeds(m, rnd, sid):
            it = {"key": f"{rnd}:{sid}:{x['seed']}", "task": rnd, "scene": sid, "title": spec["title"], "range": spec["verses"]["range"],
                  "seed": x["seed"], "src": x["base"], "qs": qs, "qids": ["oddity"] if kind == "O1" else [q["id"] for q in qs]}
            if kind == "O1":
                it["spec"] = J.oddity_spec(sid)
            out.append(it)
    return out


def judge(m, rnd, kinds=tuple(KINDS), sids=None, workers=8):
    """claude -p 판정(J1·J1-prop·O1·특징 문항) — 이미 답한 그림은 건너뛴다. 답마다 바로 저장."""
    todo = []
    for kind in kinds:
        done = m["answers"].setdefault(rnd, {}).setdefault(kind, {})
        todo += [(kind, it) for it in items(m, rnd, kind, sids) if it["key"] not in done or not done[it["key"]].get("answers")]
    print(f"[PlainWords] {rnd} 판정 {len(todo)}건 {sorted({k for k, _ in todo})}", flush=True)
    t = time.time()

    def one(job):
        kind, it = job
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
            m["answers"][rnd][kind][it["key"]] = {"tries": tries, "raw": None if got else str(o.get("result"))[:400], **(got or {"answers": None})}
            save_m(m)
        if not got:
            print(f"[PlainWords] {kind} {it['key']} 답 없음", flush=True)

    with ThreadPoolExecutor(workers) as ex:
        list(ex.map(one, todo))
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


# --- A ------------------------------------------------------------------------
def predict_a(m):
    jm = J.load()
    R = m["rounds"].setdefault("A", {"scenes": {}})
    for sid, c in FX["scenes"].items():
        src = json.load(open(os.path.join(HERE, "samples", c["a"]["dir"], "metrics.json")))["scenes"][sid]
        R["scenes"][sid] = {"src": c["a"], "prompt": src["prompt"], "tokens": tokens(src["prompt"]),
                            "seeds": [{"seed": x["seed"], "base": x["base"], "boxes": x["boxes"]} for x in src["seeds"]]}
        assert src["prompt"] == D.route_prompt(D.load(sid)), f"{sid}: A 프롬프트가 지금 정본 명세와 다름"
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
    return 8 - unit_hits(m, "A", sid, uid)


def ladder(m):
    if not m["answers"].get("A", {}).get("W-prop"):
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
                if canon_verse(spec) != canon_verse(D.load(sid)):
                    bad.append(f"b2 {sid} 근거 verse 칸이 바뀜")
                if set(re.findall(r"[a-z]+", p.lower())) & set(FX["forbidden"]):
                    bad.append(f"b2 {sid} 금지어")
                continue
            if spec != render(sid, lv):
                bad.append(f"{rnd} {sid} 사본이 render(단계)와 다름")
            if rnd != "r1":
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
            spec = D.load(sid)
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


def main(argv):
    cmd = argv[0]
    m = load_m()
    if cmd == "predict-a":
        predict_a(m)
    elif cmd == "one":   # 시험 1장 — 경로 확인 + 고친 낱말이 보이는가(이 장의 특징 문항)
        sid = next(iter(FX["scenes"]))
        lv = start_levels(sid)
        generate(m, "r1", {sid: render(sid, lv)}, seeds=FX["seeds"][:1], base={sid: (lv, "A")}, raised={sid: list(lv)})
        judge(m, "r1", ("W", "W-prop"), sids=[sid])
        s = FX["seeds"][0]
        print(f"[PlainWords] 시험 {sid} s{s} 특징 {feats(m, 'r1', sid, s)}", flush=True)
    elif cmd == "ladder":
        ladder(m)
    elif cmd == "b2":
        b2(m)
    elif cmd == "cand":
        cand(m, argv[1] if len(argv) > 1 else None)
    elif cmd == "check":
        sys.exit(0 if check(m) else 1)
    elif cmd == "report":
        for rnd in m["rounds"]:
            report(m, rnd)
    else:
        sys.exit(f"알 수 없는 명령 {cmd}")


if __name__ == "__main__":
    main(sys.argv[1:])
