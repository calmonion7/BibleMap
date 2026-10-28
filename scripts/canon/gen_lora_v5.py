#!/usr/bin/env python3
"""LoRA 학습 묶음을 장면 화풍으로 v5(task 448, notes/LORA-V5.md 고정 절) — 다윗 청년 묶음 다시 칠하기 → 머리 둘레 화풍 관문 → 학습 → 기브아 C/T/L.
  $VENV gen_lora_v5.py calib                 # S1 머리 둘레 Gram 측정자 맞춰 보기(GPU 0)
  $VENV gen_lora_v5.py probe                 # S2 묶음 01을 세기 0.65·0.8·0.9로 → 머리 둘레 점수(0.5 = v4 묶음)
  python3 gen_lora_v5.py eye <세기> '<한 줄>'  # S2 Claude 눈 한 줄 기록 → 다 차면 세기 고름
  $VENV gen_lora_v5.py sheet                 # S3 고른 세기로 25장 + 관문(미달이면 한 단계 위로 한 번)
  python3 gen_lora_v5.py train               # S4 mflux-train(겹침 금지)
  $VENV gen_lora_v5.py scene | heads | judge # S5 C/T/L 24장 → 다윗 머리 둘레 → 기계 판정
그림은 레포 밖 ~/.local/biblemap-imggen/lora-v5/, 수치는 samples/lora-v5/metrics.json. 생성 프로세스는 한 번에 하나."""
import glob, json, os, statistics, subprocess, sys, zipfile

from PIL import Image

import gen_lora_v4 as V4
import params

HERE = V4.HERE
OUT = os.path.join(V4.ROOT, "lora-v5")
SHEET = os.path.join(OUT, "sheet", params.LORA_V5_WHO)
SAMP = os.path.join(HERE, "samples", "lora-v5")
METRICS = os.path.join(SAMP, "metrics.json")
RAW = os.path.join(V4.OUT, "raw", params.LORA_V5_WHO)
V4_JOBS = os.path.join(V4.OUT, "restyle-jobs.json")
NAME = "david-youth-v5"
LORA = os.path.join(V4.ROOT, "lora", f"{NAME}.safetensors")
# 맞춰 보기 라벨(고정 절): 맞음 = C 다윗 머리 9 · 틀림 = 445 L 8 + 447 L·K5·K3·R 4
POS = [f"{V4.OUT}/scene/C-s{s}.png" for s in params.LORA_V4_SCENE_SEEDS] + [f"{V4.ROOT}/lora-style/scene/C-s11.png"]
NEG = [f"{V4.OUT}/scene/L-s{s}.png" for s in params.LORA_V4_SCENE_SEEDS] + \
      [f"{V4.ROOT}/lora-style/scene/{a}-s11.png" for a in ("L", "K5", "K3", "R")]


def load():
    return json.load(open(METRICS, encoding="utf-8")) if os.path.exists(METRICS) else {}


def save(m):
    os.makedirs(SAMP, exist_ok=True)
    with open(METRICS, "w", encoding="utf-8") as fh:
        json.dump(m, fh, ensure_ascii=False, indent=1)


def tag(p):
    """그림 경로 → 짧은 이름(445-C-s11 · 447-K5-s11 · probe-0.8 …)."""
    d = os.path.basename(os.path.dirname(os.path.dirname(p)))
    return {"face-lora-v4": "445", "lora-style": "447"}.get(d, d) + "-" + os.path.basename(p)[:-4]


# ── 머리 둘레(모든 그림 같은 길) ─────────────────────────────────────────────

def head_box(im, left=False):
    """OWLv2 점수 0.05 이상 후보 중 가장 큰 상자(447 heads와 같음). left = 기브아 다윗(왼쪽 절반)만."""
    import face_ab_heads as fh
    f = [b for b, s in fh._faces(im) if s >= 0.05 and (not left or (b[0] + b[2]) / 2 < im.width / 2)]
    return max(f, key=lambda b: (b[2] - b[0]) * (b[3] - b[1])) if f else None


def head_crop(src, out, target=None):
    """→ 머리 상자(원래 화소) 또는 None. target(긴 변 화소)이 있으면 묶음 그림 — 머리 긴 변이 target이 되게 먼저 줄이고 잘라 3배."""
    import gen_face_detail as G
    im = Image.open(src).convert("RGB")
    b = head_box(im, left=target is None)
    if b is None:
        return None
    if target:
        k = target / max(b[2] - b[0], b[3] - b[1])
        im = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
        b2 = [v * k for v in b]
    else:
        b2 = b
    c = im.crop(tuple(G.region(b2, *im.size)))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    c.resize((c.width * 3, c.height * 3), Image.LANCZOS).save(out)
    return [round(v) for v in b]


def gram(paths):
    import style_metric as SM
    F = SM.feats(paths)
    return {p: {k: F[p][k] for k in params.LORA_V5_LAYERS} for p in paths}


def dist(a, b):
    return float(1 - (a @ b))


def score(g, refs, layer):
    """C 머리 기준 묶음과의 평균 거리."""
    return statistics.fmean(dist(g[layer], r[layer]) for r in refs)


def auc(pos, neg):
    return sum((p < n) + 0.5 * (p == n) for p in pos for n in neg) / (len(pos) * len(neg))


# ── S1 ────────────────────────────────────────────────────────────────────

def calib():
    crops, boxes = {}, {}
    for p in POS + NEG:
        o = os.path.join(OUT, "calib", tag(p) + ".png")
        b = head_crop(p, o)
        if b:
            crops[p], boxes[tag(p)] = o, b
    G = gram(list(crops.values()))
    pos = [G[crops[p]] for p in POS if p in crops]
    neg = [G[crops[p]] for p in NEG if p in crops]
    res = {"n_pos": len(pos), "n_neg": len(neg), "auc": {}, "thr": {}, "scores": {}}
    for L in params.LORA_V5_LAYERS:
        ps = [score(g, [r for r in pos if r is not g], L) for g in pos]
        ns = [score(g, pos, L) for g in neg]
        res["auc"][L], res["thr"][L] = round(auc(ps, ns), 3), round(max(ps), 5)
        res["scores"][L] = {tag(p): round(s, 5) for p, s in zip([p for p in POS if p in crops] + [p for p in NEG if p in crops], ps + ns)}
    res["gate_layers"] = [L for L in params.LORA_V5_LAYERS if res["auc"][L] >= params.LORA_V5_AUC_MIN]
    res["decision"] = "관문으로 씀" if res["gate_layers"] else "관문 아님"
    res["median_head"] = statistics.median(max(b[2] - b[0], b[3] - b[1]) for t, b in boxes.items() if "-C-" in t)
    res["boxes"] = boxes
    m = load()
    m["calib"] = res
    save(m)
    for L in params.LORA_V5_LAYERS:
        s = res["scores"][L]
        print(f"{L} AUC {res['auc'][L]} · 문턱 {res['thr'][L]} | " + " ".join(f"{k} {v:.4f}" for k, v in s.items()))
    print(f"측정자: {res['decision']} (관문 층 {res['gate_layers']}) · C 다윗 머리 긴 변 중앙값 {res['median_head']}")


def ref_grams():
    m = load()["calib"]
    paths = [os.path.join(OUT, "calib", tag(p) + ".png") for p in POS if tag(p) in m["boxes"]]
    G = gram(paths)
    return [G[p] for p in paths], m


def judge_sheet(srcs, key):
    """묶음 그림들 → [{n, box, 점수…, in}] (머리 못 잡으면 box None·in None)."""
    refs, c = ref_grams()
    rows, crops = [], {}
    for n, src in srcs:
        o = os.path.join(OUT, f"{key}-heads", f"{n}.png")
        b = head_crop(src, o, target=c["median_head"])
        rows.append({"n": n, "box": b})
        if b:
            crops[n] = o
    G = gram(list(crops.values()))
    for r in rows:
        if r["box"]:
            g = G[crops[r["n"]]]
            for L in params.LORA_V5_LAYERS:
                r[L] = round(score(g, refs, L), 5)
            r["in"] = all(r[L] <= c["thr"][L] for L in c["gate_layers"]) if c["gate_layers"] else None
    return rows


def v4_prompt(n):
    return next(j["prompt"] for j in json.load(open(V4_JOBS)) if j["src"] == os.path.join(RAW, f"{n}.png"))


def restyle_jobs(ns, s, d):
    jobs = []
    for n in ns:
        src = os.path.join(RAW, f"{n}.png")
        w, h = Image.open(src).size
        jobs.append({"src": src, "w": w, "h": h, "strength": s, "seed": int(n), "out": os.path.join(d, f"{n}.png"), "prompt": v4_prompt(n)})
    return jobs


# ── S2 ────────────────────────────────────────────────────────────────────

def probe():
    d = os.path.join(OUT, "probe")
    jobs = [j | {"out": os.path.join(d, f"01-{s}.png")} for s in params.LORA_V5_PROBE for j in restyle_jobs(["01"], s, d)]
    V4.run_jobs(jobs, os.path.join(OUT, "probe-jobs.json"))
    srcs = [("0.5", os.path.join(V4.SHEET, params.LORA_V5_WHO, "01.png"))] + [(str(s), os.path.join(d, f"01-{s}.png")) for s in params.LORA_V5_PROBE]
    old = {r["strength"]: r.get("eye", "") for r in load().get("probe", [])}
    rows = [r | {"strength": float(r.pop("n")), "src": src, "eye": old.get(float(n), "")} for r, (n, src) in zip(judge_sheet(srcs, "probe"), srcs)]
    m = load()
    m["probe"] = rows
    save(m)
    for r in rows:
        print(r["strength"], {L: r.get(L) for L in params.LORA_V5_LAYERS}, "문턱 안" if r.get("in") else "문턱 밖" if r.get("in") is False else "—", r["src"])


def same_person(eye):
    return eye.startswith("같은 사람")


def pick(rows, gated):
    """문턱 안(관문 아님이면 Claude 눈의 화풍 「같은 화풍」) 그리고 Claude 눈 「같은 사람」인 가장 낮은 세기 → 세기 또는 None."""
    ok = [r["strength"] for r in rows if same_person(r["eye"]) and (r.get("in") if gated else "같은 화풍" in r["eye"])]
    return min(ok) if ok else None


def eye(strength, line):
    m = load()
    r = next(r for r in m["probe"] if r["strength"] == float(strength))
    r["eye"] = line
    if all(r["eye"] for r in m["probe"]):
        m["probe_pick"] = pick(m["probe"], bool(m["calib"]["gate_layers"]))
        print("고른 세기:", m["probe_pick"])
    save(m)


# ── S3 ────────────────────────────────────────────────────────────────────

def sheet():
    m = load()
    steps = sorted({0.5, *params.LORA_V5_PROBE})
    s = m["probe_pick"]
    tries = []
    for s in (s, *[x for x in steps if x > s][:1]):
        ns = [r["n"] for r in json.load(open(os.path.join(RAW, "items.json")))]
        for f in glob.glob(os.path.join(SHEET, "*.png")):
            os.remove(f)
        V4.run_jobs(restyle_jobs(ns, s, SHEET), os.path.join(OUT, f"sheet-jobs-{s}.json"), force=True)
        rows = judge_sheet([(n, os.path.join(SHEET, f"{n}.png")) for n in ns], f"sheet-{s}")
        cnt = [r for r in rows if r["box"]]
        n_in = sum(bool(r["in"]) for r in cnt)
        ok = n_in >= params.LORA_V5_SHEET_PASS * len(cnt)
        tries.append({"strength": s, "n_in": n_in, "n_counted": len(cnt), "n_skip": len(rows) - len(cnt), "pass": ok, "rows": rows})
        print(f"묶음 세기 {s}: 문턱 안 {n_in}/{len(cnt)} (뺀 장 {len(rows) - len(cnt)}) {'통과' if ok else '미달'}", flush=True)
        if ok:
            break
    for r in json.load(open(os.path.join(RAW, "items.json"))):
        open(os.path.join(SHEET, f"{r['n']}.txt"), "w").write(f"{params.LORA_V5_TRIGGER}, a man, {r['cap']}")
    m = load()
    m["sheet_gate"] = {"strength": s, "pass": tries[-1]["pass"], "tries": tries}
    save(m)


# ── S4 ────────────────────────────────────────────────────────────────────

def train():
    if os.path.exists(LORA):
        return
    cfg = json.load(open(os.path.join(V4.TRAIN, "david-youth-v4.json")))
    n = len(glob.glob(os.path.join(SHEET, "*.png")))
    cfg["data"] = SHEET
    cfg["checkpoint"]["output_path"] = os.path.join(V4.TRAIN, NAME)
    cfg["training_loop"]["num_epochs"] = -(-params.LORA_V5_STEPS // n)
    path = os.path.join(V4.TRAIN, f"{NAME}.json")
    json.dump(cfg, open(path, "w"), indent=1)
    with open(os.path.join(V4.TRAIN, f"{NAME}.log"), "w") as log:
        subprocess.run(["/usr/bin/time", "-l", os.path.join(V4.MFLUX, "mflux-train"), "--config", path], stdout=log, stderr=subprocess.STDOUT, check=True)
    z = os.path.join(V4.TRAIN, NAME, "checkpoints", f"{params.LORA_V5_STEPS:07d}_checkpoint.zip")
    with zipfile.ZipFile(z) as zf, open(LORA, "wb") as f:   # v4와 같음: 300스텝 어댑터만 꺼냄
        f.write(zf.read(f"{params.LORA_V5_STEPS:07d}_adapter.safetensors"))
    print(f"[LoraV5] 학습 끝 → {LORA}", flush=True)


# ── S5 ────────────────────────────────────────────────────────────────────

def scene_prompt(trig):
    """route_prompt(지금 명세)에서 다윗 cast 서술 앞에만 트리거 낱말(gen_lora_v4.scene_prompt와 같은 자리 찾기)."""
    spec = V4.ds.load(V4.SID)
    p = V4.ds.route_prompt(spec)
    if trig:
        f = next(f for f in spec["figures"] if f["cast"] == params.LORA_V5_WHO)
        d = V4.ds.cast_describe(V4.ds._cast_in_scene(f)).rsplit(", in ", 1)[0]
        assert p.count(d) == 1, p.count(d)
        p = p.replace(d, f"{params.LORA_V5_TRIGGER}, {d}")
    return p


def scene():
    import check_scenes
    n = check_scenes.zimage_tokens()
    rows = []
    for arm in ("C", "T", "L"):
        p = scene_prompt(arm != "C")
        for s in params.LORA_V5_SCENE_SEEDS:
            rows.append({"arm": arm, "seed": s, "tokens": n(p), "prompt": p, "w": 1216, "h": 640, "scale": params.LORA_V5_SCALE,
                         "loras": [NAME] if arm == "L" else [], "out": os.path.join(OUT, "scene", f"{arm}-s{s}.png")})
    m = load()
    m["scene"] = [{k: r[k] for k in ("arm", "seed", "tokens", "out")} for r in rows]
    save(m)
    over = [r for r in rows if r["tokens"] > 512]
    if over:
        sys.exit(f"[LoraV5] 토큰 > 512 — 생성 안 함(벽): {sorted({r['tokens'] for r in over})}")
    log = {x["out"]: x for x in V4.run_jobs(rows, os.path.join(OUT, "scene-jobs.json"))}
    m = load()
    for r in m["scene"]:
        r |= {k: log[r["out"]][k] for k in ("secs", "active") if r["out"] in log}
    save(m)
    print(f"[LoraV5] 장면 {len(rows)}장 · 토큰 {sorted({r['tokens'] for r in rows})}", flush=True)


def heads():
    m = load()
    m["heads"] = {}
    for r in m["scene"]:
        k = f"{r['arm']}-s{r['seed']}"
        m["heads"][k] = head_crop(r["out"], os.path.join(OUT, "heads", f"{k}.png"))
        print(k, m["heads"][k], flush=True)
    save(m)


def same_style(d_lc, d_tc):
    """채택 규칙(고정 절) — d_lc·d_tc = {층: [시드 8개 거리 또는 None]} → (층별 통과 시드 수, 기계 「같은 화풍」)."""
    cnt = {}
    for L in d_lc:
        floor = max(x for x in d_tc[L] if x is not None)
        cnt[L] = sum(x is not None and x <= floor for x in d_lc[L])
    return cnt, all(c >= params.LORA_V5_SAME_MIN for c in cnt.values())


def judge():
    m = load()
    ks = [k for k, b in m["heads"].items() if b]
    G = gram([os.path.join(OUT, "heads", f"{k}.png") for k in ks])
    g = {k: G[os.path.join(OUT, "heads", f"{k}.png")] for k in ks}
    d = {a: {L: [] for L in params.LORA_V5_LAYERS} for a in ("L", "T")}
    for s in params.LORA_V5_SCENE_SEEDS:
        for a in ("L", "T"):
            for L in params.LORA_V5_LAYERS:
                x, c = g.get(f"{a}-s{s}"), g.get(f"C-s{s}")
                d[a][L].append(round(dist(x[L], c[L]), 5) if x and c else None)
    cnt, ok = same_style(d["L"], d["T"])
    m["judge"] = {"seeds": params.LORA_V5_SCENE_SEEDS, "d_LC": d["L"], "d_TC": d["T"], "count": cnt, "same": ok,
                  "gated": bool(m["calib"]["gate_layers"])}
    save(m)
    for L in params.LORA_V5_LAYERS:
        print(f"{L} d(L,C) {d['L'][L]} | d(T,C) {d['T'][L]} | ≤ T 바닥 {cnt[L]}/8")
    print("기계:", "같은 화풍" if ok else "다른 화풍")


if __name__ == "__main__":
    a = sys.argv[1]
    if a == "eye":
        eye(sys.argv[2], sys.argv[3])
    else:
        {"calib": calib, "probe": probe, "sheet": sheet, "train": train, "scene": scene, "heads": heads, "judge": judge}[a]()
