#!/usr/bin/env python3
"""정본 전이 v4(task 445, notes/FACE-LORA-V4.md 고정 절) — 장면 화풍으로 다시 칠한 학습 묶음 → 사울·다윗 청년 LoRA → 기브아 창 C/L → 사람 판정 화면.
  python3 gen_lora_v4.py cal | cal-report           # S2 화풍 판정자 맞춰 보기(GPU 0, claude -p Sonnet 3회 다수결)
  python3 gen_lora_v4.py views | body | raw        # S3 klein 각도 정본·전신(새 정본) → 다시 칠하기 전 묶음
  $VENV gen_lora_v4.py restyle [--retry <id>...]   # S3 Z-Image img2img로 장면 화풍에 다시 칠함 → lora-sheet-v4 + 학습 설정
  python3 gen_lora_v4.py sheet-judge               # S3 묶음 화풍 관문
  python3 gen_lora_v4.py train                     # S4 mflux-train 차례로(동시 금지)
  $VENV gen_lora_v4.py scene [--retry]             # S5 C/L 16장(--retry = L만 세기 0.7) · 토큰 기록
  $VENV gen_lora_v4.py heads                       # S5 OWLv2 머리 상자
  python3 gen_lora_v4.py scene-judge               # S5 장면 화풍 관문
  $VENV gen_lora_v4.py detail                      # S6 판정 화면용 얼굴 보정(완성 그림엔 안 붙임)
  python3 gen_lora_v4.py page | record '<답>'      # S6
그림은 레포 밖 ~/.local/biblemap-imggen/{face-lora-v4,lora-sheet-v4}, 목록·판정은 samples/face-lora-v4/. 생성 프로세스는 한 번에 하나."""
import glob, json, os, re, subprocess, sys, threading, zipfile
from concurrent.futures import ThreadPoolExecutor

from PIL import Image, ImageOps

import params

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "batch"))
import derive_scene as ds  # noqa: E402

ROOT = os.path.expanduser("~/.local/biblemap-imggen")
OUT = os.path.join(ROOT, "face-lora-v4")
SHEET = os.path.join(ROOT, "lora-sheet-v4")
TRAIN = os.path.join(ROOT, "train")
MFLUX = os.path.join(ROOT, ".venv-mflux", "bin")
NOTE = os.path.join(HERE, "notes", "FACE-LORA-V4.md")
SAMP = os.path.join(HERE, "samples", "face-lora-v4")
METRICS = os.path.join(SAMP, "metrics.json")
HEADS = os.path.join(SAMP, "heads.json")
EXCLUDE = os.path.join(SAMP, "exclude.json")
PAGE = os.path.join(ROOT, "pages", "face-lora-v4.html")
SID = "authored-saul-gibeah-spear"
WHO = params.LORA_V4_WHO
TRIG = params.LORA_V4_TRIGGER
NAME = {"saul": "사울", "david-youth": "다윗"}
V3_NAME = {"saul": "saul", "david-youth": "david"}   # V3 학습 설정 파일 이름
LOCK = threading.Lock()
FX = json.loads(re.search(r"```json fixed\n(.*?)\n```", open(NOTE, encoding="utf-8").read(), re.S).group(1))


def load():
    return json.load(open(METRICS, encoding="utf-8")) if os.path.exists(METRICS) else {}


def save(m):
    os.makedirs(SAMP, exist_ok=True)
    with open(METRICS, "w", encoding="utf-8") as fh:
        json.dump(m, fh, ensure_ascii=False, indent=1)


def canon(who):
    return os.path.join(HERE, "frozen", f"{who}.png"), os.path.join(ROOT, "face-canon-v3", who, f"s{params.LORA_V4_CANON_SEED[who]}-34.png")


def describe(who):
    """기브아 명세가 그 인물을 부르는 cast 서술 — 다시 칠하기·얼굴 보정 문구가 장면 문구와 같은 말을 쓰게."""
    f = next(f for f in ds.load(SID)["figures"] if f["cast"] == who)
    return ds.cast_describe(ds._cast_in_scene(f))


# ── 셈(순수 함수 — test_lora_v4) ─────────────────────────────────────────────

def majority(v):
    return "틀림" if v.count("틀림") * 2 > len(v) else "맞음"


def cal_conclude(a, b):
    """a = [(다수결, 사람 답)] 24 · b = [다수결] 16 → (결론, 셈)."""
    agree, wrong = sum(x == y for x, y in a), sum(x == "틀림" for x in b)
    ok = agree >= FX["cal_a_min"] and wrong >= FX["cal_b_wrong_min"]
    return ("관문으로 씀" if ok else "관문 아님"), {"a_agree": agree, "a_n": len(a), "b_wrong": wrong, "b_n": len(b)}


def sheet_gate(maj):
    """한 인물 묶음 다수결 목록 → (통과, 맞음 수)."""
    n = sum(x == "맞음" for x in maj)
    return n >= FX["sheet_pass_ratio"] * len(maj), n


def scene_gate(rows):
    """rows = {갈래: [(전체 다수결, [머리 다수결…]) × 시드]} → {갈래: (전체 맞음, 두 머리 맞음, 통과)}. 머리를 못 찾은 장은 머리 불통과(보수)."""
    out = {}
    for arm, rs in rows.items():
        whole = sum(w == "맞음" for w, _ in rs)
        heads = sum(len(h) == len(WHO) and all(x == "맞음" for x in h) for _, h in rs)
        out[arm] = (whole, heads, whole >= FX["scene_pass_min"] and heads >= FX["scene_pass_min"])
    return out


def tally(ans, l_arm="L"):
    """사람 답 → (판정, 셈). ans = {문항 id: yes|no|unsure}."""
    style = all(ans.get(f"S:{w}") == "yes" for w in WHO)
    face = {arm: {w: sum(1 for k, v in ans.items() if k.startswith(f"A:{arm}:") and k.endswith(f":{w}") and v == "yes") for w in WHO}
            for arm in (l_arm, "C")}
    met = [w for w in WHO if face[l_arm][w] >= FX["adopt_face_min"]]
    v = "채택" if style and len(met) == len(WHO) else "조건부" if style and met else "미채택"
    lenient = all(face["C"][w] >= FX["lenient_control_min"] for w in WHO)
    return v, {"style": {w: ans.get(f"S:{w}") for w in WHO}, "face": face, "lenient": lenient}


# ── 화풍 판정자(style_judge의 s.style · 머리말 v2 · 3회) ─────────────────────

def zoom_crop(src, box, out):
    """머리 둘레(머리 상자 긴 변 × FACE_DETAIL_MARGIN 정사각)를 원래 화소에서 잘라 crop_zoom배."""
    import gen_face_detail as G
    if not os.path.exists(out) or os.path.getmtime(out) < os.path.getmtime(src):
        im = Image.open(src).convert("RGB")
        c = im.crop(tuple(G.region(box, *im.size)))
        z = FX["crop_zoom"]
        os.makedirs(os.path.dirname(out), exist_ok=True)
        c.resize((c.width * z, c.height * z), Image.LANCZOS).save(out)
    return out


def judge(items, workers=8):
    """items = [(열쇠, 묶음, 그림 경로)] — 회차마다 metrics['judge']에 바로 적음, 답한 회차는 건너뜀."""
    import judge_items as J
    import style_judge as SJ
    qs = [dict(q) for q in SJ.QS if q["id"] == "s.style"]
    spec, m = ds.load(SID), load()
    m.setdefault("judge", {})

    def ask(key, grp, src, rep):
        it = {"key": key, "task": re.sub(r"[^\w.-]", "-", key), "scene": "v4", "title": spec["title"], "range": spec["verses"]["range"],
              "seed": 0, "src": src, "qs": qs, "qids": ["s.style"]}
        d, files = J.prepare(it, "face-lora-v4")
        got, tries = None, []
        for _ in range(2):   # JSON이 깨지면 한 번만 다시(style_judge와 같음)
            o = J.call(J.prompt(it, files, J.HEADERS["v2"]), d, "sonnet")
            tries.append(J.use(o) | {"error": bool(o.get("is_error"))})
            got = None if o.get("is_error") else J.parse(o.get("result"), it["qids"])
            if got:
                break
        with LOCK:
            m["judge"].setdefault(key, {"group": grp, "src": src, "reps": {}})["reps"][str(rep)] = {"tries": tries, **(got or {"answers": None})}
            save(m)
        if not got:
            print(f"[LoraV4] {key} 회차 {rep} 답 없음", flush=True)

    todo = [(k, g, s, r) for k, g, s in items for r in range(1, FX["reps"] + 1)
            if not ((m["judge"].get(k) or {}).get("reps", {}).get(str(r)) or {}).get("answers")]
    print(f"[LoraV4] 판정 {len(todo)}건", flush=True)
    with ThreadPoolExecutor(workers) as ex:
        list(ex.map(lambda j: ask(*j), todo))
    return load()


def vote(m, key):
    v = [(r.get("answers") or {}).get("s.style") for _, r in sorted(((m.get("judge") or {}).get(key) or {}).get("reps", {}).items())]
    return majority([x for x in v if x]), "".join(x[0] if x else "-" for x in v)


# ── S2 판정자 맞춰 보기 ─────────────────────────────────────────────────────

def cal_items():
    v3 = os.path.join(ROOT, "lora-v3-scene")
    a = [(f"cal:A:{arm}:s{s}", "A", os.path.join(v3, f"{arm}-s{s}.png")) for arm in ("C", "V2", "V3") for s in params.LORA_V3_SCENE_SEEDS]
    boxes = json.load(open(os.path.join(HERE, "samples", "face-lora-v3", "heads.json")))
    b = [(f"cal:B:s{s}:{w}", "B", zoom_crop(os.path.join(ROOT, "face-detail-v3", "paste", f"C-s{s}.png"), boxes[f"C-s{s}"][w],
                                            os.path.join(OUT, "judge-src", f"cal-B-s{s}-{w}.png")))
         for s in params.LORA_V3_SCENE_SEEDS for w in ("saul", "david")]
    mm = [(f"cal:M:{w}:{os.path.basename(p)[:-4]}", "M", p) for w in ("saul", "david")
          for p in sorted(glob.glob(os.path.join(ROOT, "lora-sheet-v3", w, "*.png")))]
    return a, b, mm


def cal_report():
    a, b, mm = cal_items()
    m = load()
    av = [(vote(m, k)[0], "맞음" if ":C:" in k else "틀림") for k, _, _ in a]
    bv = [vote(m, k)[0] for k, _, _ in b]
    for k, _, _ in a + b:
        print(k, *vote(m, k))
    c, why = cal_conclude(av, bv)
    meas = {w: sum(vote(m, k)[0] == "맞음" for k, _, _ in mm if f":{w}:" in k) for w in ("saul", "david")}
    meas_n = {w: sum(1 for k, _, _ in mm if f":{w}:" in k) for w in ("saul", "david")}
    m["cal"] = {"conclusion": c, **why, "v3_sheet_ok": meas, "v3_sheet_n": meas_n}
    save(m)
    print(f"[측정] V3 묶음 다수결 맞음: " + " · ".join(f"{w} {meas[w]}/{meas_n[w]}" for w in meas))
    print(f"판정자: {c} {why}")
    return c


def gate_on():
    return (load().get("cal") or {}).get("conclusion") == "관문으로 씀"


# ── S3 묶음 ─────────────────────────────────────────────────────────────────

# 성인 틀(「man … beard」)을 수염 없는 청년 정본에 걸면 klein이 수염 난 성인을 그림(2026-10-27 각도 6장 모두) — 인물마다 정체성 낱말
LOOK = {"saul": ("man", "hair, beard, age"),
        "david-youth": ("young man", "curly hair, beardless smooth youthful face (about 18, no beard, no stubble), age")}


def views():
    from gen_face_angles import VIEW_TEXT, klein
    for who in WHO:
        man, keep = LOOK[who]
        for view in ("three-quarter", "profile"):
            prompt = (f"Image 1 is a portrait of a {man} in a soft colored-pencil storybook style. Draw the very same {man} — exactly the same face, "
                      f"eyes, nose, {keep} and skin — " + VIEW_TEXT[view].format(side=params.LORA_V4_SIDE[who]) +
                      ". Head and shoulders, same clothes, same plain cream paper background, same colored-pencil art style.")
            for seed in params.FACE_ANGLE_VIEW_SEEDS:
                klein([canon(who)[0]], prompt, seed, os.path.join(OUT, "views", f"{who}-{view}-s{seed}.png"), 768, 768)


def body():
    from gen_face_angles import klein
    for who in WHO:
        man, keep = LOOK[who]
        for pose, (text, (w, h)) in params.LORA_V3_BODY.items():
            prompt = (f"Images 1 and 2 show the same {man} from the front and in three-quarter view. Draw the very same {man} — exactly the same face, "
                      f"{keep} and build — {text}. Plain clothes of an ancient Israelite, soft colored-pencil storybook style, natural adult proportions.")
            for seed in params.LORA_V3_BODY_SEEDS:
                klein(list(canon(who)), prompt, seed, os.path.join(OUT, "body", f"{who}-{pose}-s{seed}.png"), w, h)


def raw():
    """V3 구성(초상 13 · 전신 8 · 원경 4) → face-lora-v4/raw/<id>/NN.png + items.json. 눈 거르기로 뺀 장(exclude.json)은 빼고 적음."""
    from gen_lora_v3 import far
    ex = json.load(open(EXCLUDE)) if os.path.exists(EXCLUDE) else {}
    for who in WHO:
        skip = set((ex.get(who) or {}))
        items = [(Image.open(canon(who)[0]), "close-up head portrait, facing forward, plain cream background", "frozen")]
        for view, text in (("three-quarter", "three-quarter view"), ("profile", "side profile view")):
            for seed in params.FACE_ANGLE_VIEW_SEEDS:
                rel = f"views/{who}-{view}-s{seed}.png"
                if rel in skip:
                    continue
                im = Image.open(os.path.join(OUT, rel))
                cap = f"close-up head portrait, {text}, plain cream background"
                items += [(im, cap, rel), (ImageOps.mirror(im), cap, rel + "#mirror")]
        for pose, (text, _) in params.LORA_V3_BODY.items():
            for seed in params.LORA_V3_BODY_SEEDS:
                rel = f"body/{who}-{pose}-s{seed}.png"
                if rel not in skip:
                    items.append((Image.open(os.path.join(OUT, rel)), text, rel))
        for pose, frac in params.LORA_V3_FAR.items():
            for seed in params.LORA_V3_BODY_SEEDS:
                rel = f"body/{who}-{pose}-s{seed}.png"
                if rel not in skip:
                    items.append((far(os.path.join(OUT, rel), frac),
                                  "small distant full-body figure in a wide empty scene, " + params.LORA_V3_BODY[pose][0].split(", ", 1)[1], rel + "#far"))
        d = os.path.join(OUT, "raw", who)
        os.makedirs(d, exist_ok=True)
        for f in glob.glob(os.path.join(d, "*.png")):
            os.remove(f)
        rows = []
        for i, (im, cap, rel) in enumerate(items, 1):
            im.convert("RGB").save(os.path.join(d, f"{i:02d}.png"))
            rows.append({"n": f"{i:02d}", "cap": cap, "from": rel})
        json.dump(rows, open(os.path.join(d, "items.json"), "w"), ensure_ascii=False, indent=1)
        print(f"[LoraV4] {who} 묶음 {len(rows)}장(뺀 장 {len(skip)})", flush=True)


def restyle(retry=()):
    m = load()
    st = m.setdefault("sheet_strength", {})
    jobs = []
    for who in WHO:
        s = params.LORA_V4_RESTYLE_RETRY if who in retry else params.LORA_V4_RESTYLE
        if st.get(who) == s and who not in retry:
            continue
        d = os.path.join(SHEET, who)
        os.makedirs(d, exist_ok=True)
        for r in json.load(open(os.path.join(OUT, "raw", who, "items.json"))):
            src = os.path.join(OUT, "raw", who, f"{r['n']}.png")
            w, h = Image.open(src).size
            jobs.append({"src": src, "w": w, "h": h, "strength": s, "seed": int(r["n"]), "out": os.path.join(d, f"{r['n']}.png"),
                         "prompt": f"{ds.ST} {r['cap']}, {describe(who)}."})
            open(os.path.join(d, f"{r['n']}.txt"), "w").write(f"{TRIG[who]}, a man, {r['cap']}")
        st[who] = s
    if not jobs:
        return
    run_jobs(jobs, os.path.join(OUT, "restyle-jobs.json"), force=True)
    for who in WHO:
        n = len(glob.glob(os.path.join(SHEET, who, "*.png")))
        cfg = json.load(open(os.path.join(TRAIN, f"{V3_NAME[who]}-v3.json")))
        cfg["data"] = os.path.join(SHEET, who)
        cfg["checkpoint"]["output_path"] = os.path.join(TRAIN, f"{who}-v4")
        cfg["training_loop"]["num_epochs"] = -(-params.LORA_V4_STEPS // n)
        json.dump(cfg, open(os.path.join(TRAIN, f"{who}-v4.json"), "w"), indent=1)
        print(f"[LoraV4] {who} 묶음 {n}장 · 세기 {st[who]} · {cfg['training_loop']['num_epochs']}에폭", flush=True)
    m = load() | {"sheet_strength": st}
    save(m)


def sheet_items(who, m=None):
    s = (m or load())["sheet_strength"][who]
    return [(f"sheet:{who}:{s}:{os.path.basename(p)[:-4]}", f"sheet-{who}", p) for p in sorted(glob.glob(os.path.join(SHEET, who, "*.png")))]


def sheet_judge():
    m = judge([x for w in WHO for x in sheet_items(w)])
    res = {}
    for who in WHO:
        its = sheet_items(who, m)
        maj = [vote(m, k)[0] for k, _, _ in its]
        ok, n = sheet_gate(maj)
        res[who] = {"strength": m["sheet_strength"][who], "ok": n, "n": len(maj), "pass": ok}
        for k, _, _ in its:
            print(k, *vote(m, k))
    m.setdefault("sheet_gate", []).append(res)
    save(m)
    print("묶음 화풍: " + " · ".join(f"{w} {r['ok']}/{r['n']} (세기 {r['strength']}) {'통과' if r['pass'] else '미달'}" for w, r in res.items()))
    return res


# ── S4 학습 ─────────────────────────────────────────────────────────────────

def train():
    for who in WHO:
        out = os.path.join(ROOT, "lora", f"{who}-v4.safetensors")
        if os.path.exists(out):
            continue
        cfg = os.path.join(TRAIN, f"{who}-v4.json")
        with open(os.path.join(TRAIN, f"{who}-v4.log"), "w") as log:
            subprocess.run(["/usr/bin/time", "-l", os.path.join(MFLUX, "mflux-train"), "--config", cfg], stdout=log, stderr=subprocess.STDOUT, check=True)
        z = os.path.join(TRAIN, f"{who}-v4", "checkpoints", f"{params.LORA_V4_STEPS:07d}_checkpoint.zip")
        with zipfile.ZipFile(z) as zf, open(out, "wb") as f:   # V3와 같음: 300스텝 어댑터만 꺼냄
            f.write(zf.read(f"{params.LORA_V4_STEPS:07d}_adapter.safetensors"))
        print(f"[LoraV4] {who} 학습 끝 → {out}", flush=True)


# ── S5 장면 ─────────────────────────────────────────────────────────────────

def scene_prompt(loras):
    """route_prompt(지금 명세 — 기브아는 판 경로)에서 LoRA 인물 cast 서술 앞에만 트리거 낱말."""
    spec = ds.load(SID)
    p = ds.route_prompt(spec)
    for f in spec["figures"]:
        if f["cast"] in loras:
            d = ds.cast_describe(ds._cast_in_scene(f)).rsplit(", in ", 1)[0]   # 장면 문구는 옷 서술을 표정·자세 뒤로 보냄 — 옷 앞까지로 자리 찾기
            assert p.count(d) == 1, (f["cast"], p.count(d))
            p = p.replace(d, f"{TRIG[f['cast']]}, {d}")
    return p


def scene(retry=False):
    import check_scenes
    n = check_scenes.zimage_tokens()
    arms = ({"L07": params.LORA_V4_SCALE_RETRY} if retry else {"C": None, "L": params.LORA_V4_SCALE})
    rows = []
    for arm, scale in arms.items():
        p = scene_prompt(WHO if scale else ())
        for s in params.LORA_V4_SCENE_SEEDS:
            rows.append({"arm": arm, "seed": s, "scale": scale, "tokens": n(p), "prompt": p, "w": 1216, "h": 640,
                         "loras": [f"{w}-v4" for w in WHO] if scale else [], "out": os.path.join(OUT, "scene", f"{arm}-s{s}.png")})
    m = load()
    key = "scene_retry" if retry else "scene"
    m[key] = [{k: r[k] for k in ("arm", "seed", "scale", "tokens", "out")} for r in rows]
    save(m)
    over = [r for r in rows if r["tokens"] > 512]
    if over:
        sys.exit(f"[LoraV4] 토큰 > 512 — 생성 안 함(벽): {sorted({r['tokens'] for r in over})}")
    log = {x["out"]: x for x in run_jobs([r | {"scale": r["scale"] or 1.0} for r in rows], os.path.join(OUT, f"{key}-jobs.json"))}
    m = load()
    for r in m[key]:
        r |= {k: log[r["out"]][k] for k in ("secs", "active") if r["out"] in log}
    save(m)
    print(f"[LoraV4] {key} {len(rows)}장 · 토큰 {sorted({r['tokens'] for r in rows})}", flush=True)


def heads():
    import face_ab_heads as fh
    fh.SIDE["gibeah"] = {"david-youth": (0, 0.5), "saul": (0.5, 1)}   # 기브아 창: 다윗 왼쪽(수금)·사울 오른쪽(창)
    out = json.load(open(HEADS)) if os.path.exists(HEADS) else {}
    for p in sorted(glob.glob(os.path.join(OUT, "scene", "*.png"))):
        k = os.path.basename(p)[:-4]
        if k not in out:
            out[k] = {w: [round(v) for v in b] for w, b in fh.heads("gibeah", p).items()}
            print(k, out[k], flush=True)
    os.makedirs(SAMP, exist_ok=True)
    json.dump(out, open(HEADS, "w"), indent=1)


def scene_items(arm):
    boxes = json.load(open(HEADS))
    its = []
    for s in params.LORA_V4_SCENE_SEEDS:
        src = os.path.join(OUT, "scene", f"{arm}-s{s}.png")
        its.append((f"scene:{arm}:s{s}:whole", arm, src))
        its += [(f"scene:{arm}:s{s}:{w}", arm, zoom_crop(src, b, os.path.join(OUT, "judge-src", f"{arm}-s{s}-{w}.png")))
                for w, b in boxes[f"{arm}-s{s}"].items()]
    return its


def scene_judge():
    arms = [a for a in ("C", "L", "L07") if os.path.exists(os.path.join(OUT, "scene", f"{a}-s{params.LORA_V4_SCENE_SEEDS[0]}.png"))]
    m = judge([x for a in arms for x in scene_items(a)])
    rows = {}
    for a in arms:
        rows[a] = []
        for s in params.LORA_V4_SCENE_SEEDS:
            hv = [vote(m, f"scene:{a}:s{s}:{w}")[0] for w in WHO if f"scene:{a}:s{s}:{w}" in m["judge"]]
            rows[a].append((vote(m, f"scene:{a}:s{s}:whole")[0], hv))
            print(a, s, "전체", *vote(m, f"scene:{a}:s{s}:whole"), "머리", hv)
    g = scene_gate(rows)
    m["scene_gate"] = {a: {"whole": w, "heads": h, "pass": p} for a, (w, h, p) in g.items()}
    save(m)
    print("장면 화풍: " + " · ".join(f"{a} 전체 {w}/8 · 두 머리 {h}/8 {'통과' if p else '미달'}" for a, (w, h, p) in g.items()))
    return g


# ── Z-Image 작업(인코딩/생성 프로세스 따로 — notes/ZIMAGE.md) ──────────────────

def run_jobs(jobs, path, force=False):
    """LoRA 없는 작업 먼저(한 번 불러온 어댑터는 disable_lora 뒤에도 이름이 남는다) → venv 워커 enc·gen → 로그 목록."""
    jobs = sorted([j for j in jobs if force or not os.path.exists(j["out"])], key=lambda j: bool(j.get("loras")))
    if jobs:
        for j in jobs:
            os.makedirs(os.path.dirname(j["out"]), exist_ok=True)
        json.dump(jobs, open(path, "w"), ensure_ascii=False, indent=1)
        print(f"[LoraV4] 생성 {len(jobs)}장", flush=True)
        for mode in ("enc", "gen"):
            subprocess.run([sys.executable, os.path.abspath(__file__), "worker-" + mode, path], check=True)
    return json.load(open(path + ".log.json")) if os.path.exists(path + ".log.json") else []


def worker(mode, path):
    import time
    import torch
    torch.set_grad_enabled(False)
    import run_scene as rs
    jobs = json.load(open(path))
    emb = path + ".emb.pt"
    if mode == "enc":
        from diffusers import ZImagePipeline
        pipe = ZImagePipeline.from_pretrained(rs.ZI_BASE, transformer=None, torch_dtype=torch.bfloat16).to("mps")
        torch.save([[x.cpu() for x in pipe.encode_prompt(j["prompt"], device="mps", do_classifier_free_guidance=False)[0]]
                    for j in jobs], emb)
        return
    from diffusers import GGUFQuantizationConfig, ZImageImg2ImgPipeline, ZImagePipeline, ZImageTransformer2DModel
    from diffusers.models.model_loading_utils import load_gguf_checkpoint
    from huggingface_hub import hf_hub_download
    sd = load_gguf_checkpoint(hf_hub_download(rs.ZI_GGUF, "z_image_turbo-Q8_0.gguf"))
    for k in ("cap_pad_token", "x_pad_token"):     # ZIMAGE.md: GGUF 로드 우회 2줄
        sd[k] = sd[k].reshape(1, -1)
    tr = ZImageTransformer2DModel.from_single_file(sd, quantization_config=GGUFQuantizationConfig(compute_dtype=torch.bfloat16),
                                                   config=rs.ZI_BASE, subfolder="transformer", torch_dtype=torch.bfloat16)
    cls = ZImageImg2ImgPipeline if "src" in jobs[0] else ZImagePipeline
    pipe = cls.from_pretrained(rs.ZI_BASE, transformer=tr, text_encoder=None, tokenizer=None, torch_dtype=torch.bfloat16).to("mps")
    pipe.set_progress_bar_config(disable=True)
    loaded, log = set(), []
    for j, e in zip(jobs, torch.load(emb)):
        for n in j.get("loras", []):
            if n not in loaded:
                pipe.load_lora_weights(os.path.join(ROOT, "lora", f"{n}.safetensors"), adapter_name=n)
                loaded.add(n)
        if j.get("loras"):
            pipe.set_adapters(j["loras"], adapter_weights=[j["scale"]] * len(j["loras"]))
        elif loaded:
            pipe.disable_lora()
        kw = {"prompt_embeds": [x.to("mps", torch.bfloat16) for x in e], "width": j["w"], "height": j["h"], "num_inference_steps": 9,
              "guidance_scale": 0.0, "generator": torch.Generator("mps").manual_seed(j["seed"])}
        if "src" in j:
            kw |= {"image": Image.open(j["src"]).convert("RGB"), "strength": j["strength"]}
        t = time.time()
        pipe(**kw).images[0].save(j["out"])
        log.append({"out": j["out"], "secs": round(time.time() - t, 1), "active": pipe.get_active_adapters() if loaded else []})
        print(f"  [LoraV4] {os.path.relpath(j['out'], ROOT)} {log[-1]['secs']}s {log[-1]['active']}", flush=True)
        json.dump(log, open(path + ".log.json", "w"), ensure_ascii=False)


# ── S6 사람 판정 화면 ───────────────────────────────────────────────────────

def l_arm():
    g = load().get("scene_gate") or {}
    return "L07" if "L07" in g else "L"


def detail():
    """판정 화면용 얼굴 보정(393 v2 규칙) — 머리 둘레 정사각을 FACE_DETAIL_SIZE로 img2img FACE_DETAIL_STRENGTH. L은 그 인물 v4 어댑터 하나(그 갈래 세기), C는 없음."""
    import gen_face_detail as G
    boxes, la = json.load(open(HEADS)), l_arm()
    scale = params.LORA_V4_SCALE_RETRY if la == "L07" else params.LORA_V4_SCALE
    jobs, n = [], params.FACE_DETAIL_SIZE
    for arm in ("C", la):
        for s in params.LORA_V4_SCENE_SEEDS:
            im = Image.open(os.path.join(OUT, "scene", f"{arm}-s{s}.png")).convert("RGB")
            for w, b in boxes[f"{arm}-s{s}"].items():
                src = os.path.join(OUT, "detail", "src", f"{arm}-s{s}-{w}.png")
                os.makedirs(os.path.dirname(src), exist_ok=True)
                im.crop(tuple(G.region(b, *im.size))).resize((n, n), Image.LANCZOS).save(src)
                trig = f"{TRIG[w]}, " if arm != "C" else ""
                jobs.append({"src": src, "w": n, "h": n, "strength": params.FACE_DETAIL_STRENGTH, "seed": s,
                             "prompt": f"{ds.ST} head and shoulders close-up of {trig}{describe(w)}.", "loras": [f"{w}-v4"] if arm != "C" else [],
                             "scale": scale, "out": os.path.join(OUT, "detail", f"{arm}-s{s}-{w}.png")})
    log = run_jobs(jobs, os.path.join(OUT, "detail-jobs.json"))
    m = load()
    m["detail"] = log
    save(m)


def page():
    import random
    import make_face_judge_v2 as V
    boxes, la = json.load(open(HEADS)), l_arm()
    det = os.path.join(OUT, "detail")
    pick = next(s for s in params.LORA_V4_SCENE_SEEDS if all(len(boxes[f"{a}-s{s}"]) == len(WHO) for a in ("C", la)))
    st = []
    for w in WHO:
        c, lz = (Image.open(zoom_crop(os.path.join(OUT, "scene", f"{a}-s{pick}.png"), boxes[f"{a}-s{pick}"][w],   # 판정자가 관문 아니면 scene_judge가 안 만듦
                                      os.path.join(OUT, "judge-src", f"{a}-s{pick}-{w}.png"))) for a in ("C", la))
        st.append({"id": f"S:{w}", "tag": "화풍", "wide": True, "q": f"{NAME[w]} 머리 둘레 — 아래 그림이 위(기준)와 같은 화풍인가요?",
                   "hint": "같은 장면·같은 시드를 원래 화소의 3배로 키웠습니다. 연필 선·색연필 결·종이 질감이 같은지만 봅니다(같은 사람인지는 묻지 않습니다). "
                           "「다름」이면 나머지 문항은 안 풀어도 됩니다.", "yes": "같은 화풍", "no": "다름",
                   "refs": [V.uri(c, 900)], "caps": ["기준 — 인물 학습 없이 그린 그림"], "img": V.uri(lz, 900)})
    a = []
    for arm in ("C", la):
        for s in params.LORA_V4_SCENE_SEEDS:
            im = Image.open(os.path.join(OUT, "scene", f"{arm}-s{s}.png"))
            for w, b in boxes[f"{arm}-s{s}"].items():
                h = V.up(V.detail_crop(f"{arm}-s{s}-{w}", im, b, det)[0])
                (front, _), (three, _) = (V.matched_to(Image.open(x), V.hf(h)) for x in canon(w))
                a.append({"id": f"A:{arm}:{s}:{w}", "tag": "정본과 같은 사람인가", "q": f"가운데 머리가 {NAME[w]} 정본과 같은 사람인가요?",
                          "hint": "정본 두 장을 이 머리와 같은 선명도로 맞췄습니다. 얼굴·머리·수염·나이대만 봅니다(옷은 빼고).",
                          "refs": [V.uri(front), V.uri(three)], "caps": ["정본 정면(화질 맞춤)", "정본 3/4 측면(화질 맞춤)"], "img": V.uri(h),
                          "hf": [round(V.hf(h), 2), round(V.hf(front), 2), round(V.hf(three), 2)]})
    random.Random(1445).shuffle(a)
    qs = st + a
    html = (V.page(qs, V.scripture()).replace("<title>얼굴 판정 v2</title>", "<title>정본 전이 v4 판정</title>")
            .replace("판정 face-judge-v2", "판정 face-lora-v4"))
    os.makedirs(os.path.dirname(PAGE), exist_ok=True)
    open(PAGE, "w", encoding="utf-8").write(html)
    m = load()
    m["page"] = {"path": PAGE, "n": len(qs), "style_seed": pick, "l_arm": la, "mb": round(os.path.getsize(PAGE) / 1e6, 2)}
    save(m)
    print(PAGE, len(qs), "문항", m["page"]["mb"], "MB")


def record(text):
    body = text.split("판정 face-lora-v4", 1)[-1]
    ans = json.loads(re.search(r"\{.*?\}", body, re.S).group(0))
    open(os.path.join(SAMP, "verdict.txt"), "w", encoding="utf-8").write(text.strip() + "\n")
    v, why = tally(ans, load().get("page", {}).get("l_arm", "L"))
    print(f"판정: {v} {json.dumps(why, ensure_ascii=False)}")


if __name__ == "__main__":
    a = sys.argv[1]
    if a.startswith("worker-"):
        worker(a[7:], sys.argv[2])
    elif a == "cal":
        judge([x for g in cal_items() for x in g])
        cal_report()
    elif a == "restyle":
        restyle(sys.argv[sys.argv.index("--retry") + 1:] if "--retry" in sys.argv else ())
    elif a == "scene":
        scene("--retry" in sys.argv)
    elif a == "record":
        record(sys.argv[2])
    else:
        {"cal-report": cal_report, "views": views, "body": body, "raw": raw, "sheet-judge": sheet_judge, "train": train, "heads": heads,
         "scene-judge": scene_judge, "detail": detail, "page": page}[a]()
