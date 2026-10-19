#!/usr/bin/env python3
"""task#368 — 밤샘 5장면 × 8시드: 장면마다 바탕 8장(Z-Image, derive_scene.plate_whole_prompt) → 정본 참조 편집(2511 + Lightning, 장면 id 인자).

  VENV=~/.local/biblemap-imggen/.venv314/bin/python
  $VENV batch/run_night.py one      # S1 시험: 첫 장면 첫 시드 1장(바탕 + 편집) — 본 실행이 건너뜀
  nohup caffeinate -i $VENV batch/run_night.py all > batch/night.log 2>&1 &   # S2 본 실행(이미 있으면 건너뜀) → 끝에 검증 페이지
  $VENV batch/run_night.py page     # 검증 페이지만 다시(make_night_page)

편집 실행·되붙임·조작 확인은 gen_ref_edit_lightning·gen_ref_edit_2511 그대로(360·361 재현값 무변경), 몸·머리 상자만 장면 명세에서 일반화.
생성 프로세스는 한 번에 하나(시작 전 pgrep). 산출은 레포 밖 ~/.local/biblemap-imggen/night-pilot/<장면>/{base,edit}/,
목록은 samples/night-pilot/metrics.json(params.NIGHT_*, notes/NIGHT-PILOT.md 고정 절)."""
import json, os, subprocess, sys, time

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import params
import derive_scene as D
import face_ab_heads
import gen_ref_edit as G
import gen_ref_edit_2511 as R
import gen_ref_edit_lightning as L
import run_scene

OUT = os.path.join(G.ROOT, "night-pilot")
METRICS = os.path.join(HERE, "samples", "night-pilot", "metrics.json")
FACE_MIN = 0.015   # 얼굴 상자 최소 폭(화면 폭 비율) — 먼 무리의 작은 얼굴을 인물 머리로 잡지 않게
Q = params.REF_EDIT_LIGHTNING_QUANTS[0]   # 360·361과 같은 q8 --low-ram
LIVE = {}


def base_path(sid, s):
    return os.path.join(OUT, sid, "base", f"s{s}.png")


def edit_path(sid, s, who, last):
    return os.path.join(OUT, sid, "edit", f"s{s}.png" if last else f"s{s}-{who}.png")


def busy():
    r = subprocess.run(["pgrep", "-fl", "mflux|run_scene.py --worker|gen_video_pilot|mlx_video"], capture_output=True, text=True)
    return r.stdout.strip()


def sides(spec):
    """정본 인물 → 얼굴이 놓이는 가로 구간(화면 폭 비율). 이웃 인물 구역 가운데 사이를 가른다
    (make_cast_v2_pilot_page.SIDE의 일반화) — 혼자면 그 구역 ± 0.15."""
    figs = sorted(spec["figures"], key=lambda f: sum(spec["regions"][f["region"]][0::2]))
    if len(figs) == 1:
        r = spec["regions"][figs[0]["region"]]
        return {figs[0]["cast"]: (max(0, r[0] - 0.15), min(1, r[2] + 0.15))}
    cx = [sum(spec["regions"][f["region"]][0::2]) / 2 for f in figs]
    cut = [0] + [(a + b) / 2 for a, b in zip(cx, cx[1:])] + [1]
    return {f["cast"]: (cut[i], cut[i + 1]) for i, f in enumerate(figs)}


def heads(spec, im):
    """→ {인물: (머리 상자, 출처)} — face_ab_heads.heads와 같은 넓힘, 못 찾으면 명세 구역 위쪽 가운데."""
    faces = [(b, s) for b, s in face_ab_heads._faces(im) if b[2] - b[0] >= FACE_MIN * im.width]
    out = {}
    for who, (lo, hi) in sides(spec).items():
        c = [(s, b) for b, s in faces if lo * im.width <= (b[0] + b[2]) / 2 <= hi * im.width]
        if c:
            x0, y0, x1, y1 = max(c)[1]
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2 - face_ab_heads.LIFT * (y1 - y0)
            w, h = (x1 - x0) * face_ab_heads.GROW, (y1 - y0) * face_ab_heads.GROW
            out[who] = ((max(0, cx - w / 2), max(0, cy - h / 2), min(im.width, cx + w / 2), min(im.height, cy + h / 2)), "owl")
        else:
            r = spec["regions"][next(f["region"] for f in spec["figures"] if f["cast"] == who)]
            x, y = (r[0] + r[2]) / 2 * im.width, r[1] * im.height
            out[who] = ((x - 20, y, x + 20, y + 40), "region")
    return out


def boxes(spec, path):
    """→ {인물: {head, body, src}} — 몸 상자는 gen_ref_edit.body_box와 같은 규칙(머리 중심을 담고 다른 인물 머리는 안 담는
    「a person」 상자 중 최고 점수, 위로 머리 높이 하나 더), 못 찾으면 머리 기준 대체 상자."""
    im = Image.open(path).convert("RGB")
    hd = heads(spec, im)
    persons = G._persons(im)
    inside = lambda b, h: b[0] <= (h[0] + h[2]) / 2 <= b[2] and b[1] - 0.5 * (h[3] - h[1]) <= (h[1] + h[3]) / 2 <= b[3]
    out = {}
    for who, (hb, hsrc) in hd.items():
        others = [h for o, (h, _) in hd.items() if o != who]
        c = [(s, b) for b, s in persons if inside(b, hb) and not any(inside(b, o) for o in others) and (b[2] - b[0]) < 0.5 * im.width]
        if c:
            b = max(c)[1]
            body, bsrc = [b[0], max(0, min(b[1], hb[1]) - (hb[3] - hb[1])), b[2], b[3]], "owl"
        else:
            cx, hw, hh = (hb[0] + hb[2]) / 2, hb[2] - hb[0], hb[3] - hb[1]
            body, bsrc = [cx - 1.25 * hw, hb[1], cx + 1.25 * hw, min(im.height, hb[1] + 6 * hh)], "fallback"
        out[who] = {"head": [round(v) for v in hb], "head_src": hsrc, "body": [round(v) for v in body], "body_src": bsrc}
    return out


def side(bx, who, width):
    x = {k: sum(v["head"][0::2]) / 2 for k, v in bx.items()}
    o = [v for k, v in x.items() if k != who]
    return "left" if x[who] < (sum(o) / len(o) if o else width / 2) else "right"


def look(spec, who):
    """정체성(정본 그림 쪽, 차림 절 없음) + 차림 — 장면 명세 costume이 있으면 그것, 없으면 바탕 문구가 쓴 인물 카드 차림(고정 절)."""
    f = next(f for f in spec["figures"] if f.get("cast") == who)
    cost = f["costume"]["en"] if f.get("costume") else D._cast_in_scene(f)["costume"]
    return params.REF_EDIT_LIGHTNING_LOOK_IDENTITY[who] + ", " + (cost if cost.startswith("in ") else "wearing " + cost)


def edit_one(sid, spec, who, s, bx, src, out):
    b = bx[who]["body"]
    pw, ph = (b[2] - b[0]) * params.REF_EDIT_MASK_PAD, (b[3] - b[1]) * params.REF_EDIT_MASK_PAD
    mb = [round(max(0, b[0] - pw)), round(max(0, b[1] - ph)), round(min(G.W, b[2] + pw)), round(min(G.H, b[3] + ph))]
    mask = os.path.join(OUT, sid, "mask", f"s{s}-{who}.png")
    os.makedirs(os.path.dirname(mask), exist_ok=True)
    m = Image.new("L", (G.W, G.H), 0)
    ImageDraw.Draw(m).rectangle(mb, fill=255)
    m.save(mask)
    sd = side(bx, who, G.W)
    prompt = params.REF_EDIT_LIGHTNING_PROMPT.format(side=sd, look=look(spec, who))
    raw = os.path.join(OUT, sid, "raw", f"s{s}-{who}.png")
    e = {**L.run_edit(Q, src, who, s, prompt, raw), "scene": sid, "src": src, "side": sd, "mask_box": mb, "prompt": prompt}
    if e["status"] == "ok":
        e["resized"] = R.paste(raw, src, mask, out)
        e["out"] = out
        e["targeted"], e["diff_in"], e["diff_out"] = L.targeted(raw, src, mb)
        print(f"  [Night] {sid} {who} s{s} targeted {e['targeted']} side {sd}", flush=True)
    return e


def load_m():
    return json.load(open(METRICS)) if os.path.exists(METRICS) else {"scenes": {}, "runs": [], "restarts": 0}


def save_m(m):
    if LIVE:   # 본 실행 중이면 진행 시각을 남긴다 — 중단돼도 wall_seconds를 셀 수 있게
        m["runs"][-1]["last"] = time.time()
        m["wall_seconds"] = round(sum(r.get("end", r.get("last", r["start"])) - r["start"] for r in m["runs"]), 1)
    os.makedirs(os.path.dirname(METRICS), exist_ok=True)
    json.dump(m, open(METRICS, "w"), ensure_ascii=False, indent=1)


def night_scene(m, sid, seeds):
    spec = D.load(sid)
    whos = params.NIGHT_SCENES[sid]
    sc = m["scenes"].setdefault(sid, {"who": whos, "seeds": [], "sec": {"base": 0.0, "edit": 0.0}})
    sc["prompt"] = D.plate_whole_prompt(spec)
    todo = [{"prompt": sc["prompt"], "seed": s, "w": G.W, "h": G.H, "out": base_path(sid, s)}
            for s in seeds if not os.path.exists(base_path(sid, s))]
    print(f"[Night] {sid} 바탕 {len(seeds)}장 중 {len(todo)}장 생성", flush=True)
    if todo:
        os.makedirs(os.path.join(OUT, sid, "base"), exist_ok=True)
        sc["sec"]["base"] = round(sc["sec"]["base"] + sum(run_scene.gen_zimage(todo, os.path.join(OUT, sid, "base"))), 1)
        save_m(m)
    by = {x["seed"]: x for x in sc["seeds"]}
    for s in seeds:
        if s not in by:
            by[s] = {"seed": s, "base": base_path(sid, s), "edits": {}}
            sc["seeds"].append(by[s])
        x = by[s]
        if "boxes" not in x:
            x["boxes"] = boxes(spec, x["base"])
            save_m(m)
        src = x["base"]
        for i, who in enumerate(whos):
            out = edit_path(sid, s, who, i == len(whos) - 1)
            if x["edits"].get(who) == out and os.path.exists(out):
                src = out
                continue
            e = edit_one(sid, spec, who, s, x["boxes"], src, out)
            sc["sec"]["edit"] = round(sc["sec"]["edit"] + e["sec"], 1)
            x.setdefault("log", []).append({k: v for k, v in e.items() if k not in ("prompt", "error")} | ({"error": e["error"][-400:]} if "error" in e else {}))
            x.setdefault("prompts", {})[who] = e["prompt"]
            if e["status"] != "ok":
                save_m(m)
                break   # 이 시드의 다음 인물은 건너뛴다 — 다음 시드로(다시 띄우면 채움)
            x["edits"][who] = out
            src = out
            save_m(m)
    order = {s: i for i, s in enumerate(params.NIGHT_SEEDS)}
    sc["seeds"].sort(key=lambda x: order.get(x["seed"], 99))
    save_m(m)


def page():
    sys.path.insert(0, HERE)
    import make_night_page
    make_night_page.main()


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd in ("one", "all") and busy():
        sys.exit(f"[Night] 다른 생성 프로세스가 돈다 — 겹치지 않게 멈춤:\n{busy()}")
    m = load_m()
    if cmd == "one":
        sid = next(iter(params.NIGHT_SCENES))
        t = time.time()
        night_scene(m, sid, params.NIGHT_SEEDS[:1])
        m["trial"] = {"scene": sid, "seed": params.NIGHT_SEEDS[0], "sec": round(time.time() - t, 1)}
        save_m(m)
    elif cmd == "all":
        m["runs"].append({"start": time.time()})
        m["restarts"] = len(m["runs"]) - 1   # 본 실행을 다시 띄운 횟수(시험 one은 안 셈)
        m["unattended"] = m["restarts"] == 0
        LIVE["on"] = True
        save_m(m)
        for sid in params.NIGHT_SCENES:
            night_scene(m, sid, params.NIGHT_SEEDS)
        m["runs"][-1]["end"] = time.time()
        save_m(m)
        miss = [(sid, x["seed"]) for sid, sc in m["scenes"].items() for x in sc["seeds"] if len(x["edits"]) != len(sc["who"])]
        print(f"[Night] 끝 — wall {m['wall_seconds']}s · 편집 빠짐 {miss or '없음'}", flush=True)
        try:
            page()
        except Exception as ex:   # 페이지는 따로 다시 만들 수 있다 — 생성 결과는 이미 저장됨
            print(f"[Night] 검증 페이지 실패(배치 결과는 저장됨): {ex!r}", flush=True)
    elif cmd == "page":
        page()
