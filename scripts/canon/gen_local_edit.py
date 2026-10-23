#!/usr/bin/env python3
"""task#371 — 국소 편집: 고른 바탕의 한 부위만 klein 지시 편집으로 고친다(엔게디 칼 조리법 일반화 — gen_engedi_knife.py는 그대로).
작은 크롭 → 1024 klein 편집(지시 하나) → 원본 크롭 색에 맞춤(color_match) → 타원 마스크 안쪽만 되붙임.

  python3 gen_local_edit.py trial            # S1 시험: 놉 제사장 s7 · N1 · 시드 1 한 장
  python3 gen_local_edit.py stage1           # 놉 제사장 12장 + 가드 몸 12장(이미 있으면 건너뜀) → 판정 페이지 1
  python3 gen_local_edit.py stage2 L,T,SIDE,x0,y0,x1,y1   # 가드 1단계 고른 장의 얼굴 크롭·마스크 → 3장 → 판정 페이지 2
  python3 gen_local_edit.py page 1|2         # 판정 페이지만 다시
  python3 gen_local_edit.py record <판정.txt> # 페이지 「판정 문장」 → metrics + 고른 장면 명세 approved.final(path: local-edit)

task#386 — 383에서 사람이 고른 plain-words r2 두 장(베들레헴 s42 기름 · 가드 s5 침)에 같은 조리법. 고정 절 = notes/LOCAL-EDIT.md 「task 386」(```json fixed386),
산출 ~/.local/biblemap-imggen/local-edit/386/<장면>/, 목록 samples/local-edit/metrics-386.json(371과 섞지 않음).
  python3 gen_local_edit.py trial386 · run386 · check386        # 시험 1장 · 12장 · 마스크 밖 차 0·지시 글 대조
  $VENV gen_local_edit.py judge386 · cand386                    # 기계 거름(특징·J1, claude -p) · 후보 화면 2화면
  python3 gen_local_edit.py record386 <판정.txt> · verdict386

산출 ~/.local/biblemap-imggen/local-edit/<장면>/, 목록 samples/local-edit/metrics.json. 고정 절 notes/LOCAL-EDIT.md."""
import hashlib, json, os, re, shutil, subprocess, sys, time

from PIL import Image, ImageChops, ImageDraw, ImageFilter

import params
from gen_engedi_knife import color_match
from gen_face_ab_klein import MFLUX

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.expanduser("~/.local/biblemap-imggen/whole-wide")
OUT = os.path.expanduser("~/.local/biblemap-imggen/local-edit")
METRICS = os.path.join(HERE, "samples", "local-edit", "metrics.json")
EDIT = 1024
NOB, GATH = "authored-david-nob-priests", "authored-david-gath-achish"
# (장면, 바탕 시드) → 크롭 (L, T, 변) · 마스크 상자(원본 좌표, 눈으로 잡음 — 고정 절 표)
BOX = {(NOB, 7): ((440, 250, 380), (445, 355, 810, 500)),
       (NOB, 202): ((430, 260, 380), (435, 390, 810, 535)),
       (GATH, 5): ((20, 120, 400), (70, 140, 400, 505)),
       (GATH, 7): ((20, 120, 400), (70, 140, 400, 505))}
GUIDE = (88, 120, 118, 520)          # 팔 G: 다윗 왼쪽 어깨 옆 갈색 세로 띠(원본 좌표, 크롭 안)
GUIDE_RGB = (112, 76, 44)
KEEP_SWORD = ("Keep everything else exactly the same: both men's hands holding it, their sleeves, the background, the lighting and "
              "the same soft pencil and colored-pencil illustration style.")
KEEP_BODY = ("Keep his face, his red tunic and belt, the stone wall, the lighting and the same soft pencil and colored-pencil "
             "illustration style.")
KEEP_FACE = "Keep his face shape, hair, beard, the lighting and the same soft pencil and colored-pencil illustration style."
PROMPTS = {
    "N1": ("Replace the sword with a long bundle wrapped completely in plain white linen cloth and tied with cords; only the sword's "
           "handle sticks out of one end of the bundle. No bare metal blade is visible. " + KEEP_SWORD),
    "N2": ("Hide the whole sword blade inside a long roll of folded white cloth bound with string, so the sword becomes a "
           "cloth-wrapped parcel with only its hilt showing at one end. " + KEEP_SWORD),
    "I": ("The young man leans his shoulder against a tall old wooden gate post beside him, his head tilted to one side and both "
          "arms hanging limp. " + KEEP_BODY),
    "G": ("Redraw the brown vertical bar as an old weathered wooden gate post, and the young man leans his shoulder against it, "
          "his head tilted to one side and both arms hanging limp. " + KEEP_BODY),
    "F": ("Saliva drips from his slack open mouth down into his beard, and his eyes stare unfocused and vacant. " + KEEP_FACE),
}
ARMS = {NOB: ("N1", "N2"), GATH: ("I", "G")}
STAGES = {NOB: 1, GATH: 2}           # 장면마다 판정 단계 수(가드는 몸 → 얼굴)



# task 403 d3e — 무인 규칙 edit.small-prop-orient: 작은 허공 지물(창)의 방향·모양은 생성 뒤 국소 편집으로.
# 크롭·마스크를 사람 눈 대신 명세 구역에서 뽑는다(구역 ± 가로 PROP_PAD_X · 세로 PROP_PAD_Y — 생성은 구역보다 길게 그리기도 함, d3 창 x 110~515 vs 구역 128~413).
PROP_PAD_X, PROP_PAD_Y, PROP_PAD_FRONT = 0.1, 0.04, 0.015   # front: 벽 구역(0~0.09) 밖 — 구역 왼끝 0.105
KEEP_PROP = ("Add nothing new: no person, no hand, no other object — the plain wall behind the spear stays empty. "
             "Keep the lighting and the same soft pencil and colored-pencil illustration style.")   # d3e2: 「Keep … the people」이 빈 벽 크롭에 창 쥔 사람을 불러옴


def prop_box(region, w, h, end="back"):
    """명세 구역(0~1)의 한 끝 → (크롭 (L, T, 변), 마스크 상자) 원본 화소. 가이드 꼴 spear는 촉이 늘 왼쪽 끝(make_guide.spear) —
    end back = 가운데~오른끝 + PROP_PAD_X, front = 왼끝 - PROP_PAD_X ~ 가운데. 세로는 ± PROP_PAD_Y.
    d3e: 창 전체 크롭 + 지시 둘(왼쪽 촉·오른쪽 물미)은 klein이 양끝에 촉을 그림 → 끝마다 작은 크롭·지시 하나로 차례로.
    생성은 구역보다 길게 그리기도 함(d3 창 x 110~515 vs 구역 128~413)."""
    x0, y0, x1, y1 = region
    mid = (x0 + x1) / 2
    bx0, bx1 = (mid, x1 + PROP_PAD_X) if end == "back" else (x0 - PROP_PAD_FRONT, mid)   # d4e: 앞끝 여유 0.1은 벽 안까지 → 벽에 날개 장식
    box = (max(0, round(bx0 * w)), max(0, round((y0 - PROP_PAD_Y) * h)), min(w, round(bx1 * w)), min(h, round((y1 + PROP_PAD_Y) * h)))
    side = min(min(w, h), max(box[2] - box[0], box[3] - box[1]) + 40)
    cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
    L = int(min(max(0, cx - side / 2), w - side))
    T = int(min(max(0, cy - side / 2), h - side))
    return (L, T, side), box


def prop_prompt(look_en, end="back"):
    """편집 지시 하나. back = 뒤끝 촉 지우기(d3e) · front = 앞끝을 사전 촉 모양으로(d3e3 앞 촉이 작은 화살촉·뒤에 나무 혹).
    look_en(사전 L2)에서 끝 모양 낱말을 빌린다."""
    if end == "back":
        cap = "a small iron cap" if "small iron cap" in look_en else "a plain wooden end"
        return (f"Remove the large metal spearhead from the right end of the wooden spear shaft, so the right end is only {cap}, "
                f"much thinner than a spearhead. {KEEP_PROP}")
    m = re.search(r"one (large [a-z-]+ iron point)", look_en)
    head = m.group(1) if m else "large iron point"
    return (f"Enlarge the iron spearhead at the left end of the wooden spear shaft into one {head}, a broad blade much wider than the shaft. "
            f"Do not add any crossguard, wings or second blade. {KEEP_PROP}")   # d4e: 「nothing sticking out beyond it」 → 벽에 날개·코등이 장식

def busy():
    r = subprocess.run(["pgrep", "-fl", "mflux|run_scene.py --worker|gen_video_pilot|mlx_video"], capture_output=True, text=True)
    return r.stdout.strip()


def load_m():
    if os.path.exists(METRICS):
        return json.load(open(METRICS))
    return {"scenes": {sid: {"bases": {str(s): os.path.join(SRC, sid, "base", f"s{s}.png") for s in seeds}, "candidates": []}
                       for sid, seeds in params.LOCAL_EDIT_BASES.items()}, "sec": 0}


def save_m(m):
    os.makedirs(os.path.dirname(METRICS), exist_ok=True)
    json.dump(m, open(METRICS, "w"), ensure_ascii=False, indent=1)


def mask(crop, box):
    """크롭 크기 타원 마스크 — 상자 둘레 +20, 크롭 가장자리 안쪽 12px로 자르고 흐림 8(되붙임 경계가 크롭 모서리에 걸리지 않게)."""
    L, T, side = crop
    x0, y0, x1, y1 = box
    m = Image.new("L", (side, side), 0)
    e = [max(12, x0 - L - 20), max(12, y0 - T - 20), min(side - 12, x1 - L + 20), min(side - 12, y1 - T + 20)]
    ImageDraw.Draw(m).ellipse(e, fill=255)
    return m.filter(ImageFilter.GaussianBlur(8))


def edit(src, crop, box, arm, seed, out, guide=False, prompt=None):
    """바탕 src의 crop 부위를 klein으로 고쳐 out에 되붙인다 → 기록(dict). 이미 있으면 다시 그리지 않는다. prompt 없으면 PROMPTS[arm]."""
    L, T, side = crop
    base = Image.open(src).convert("RGB")
    stem = out[:-4]
    inp = stem + "-in.png"
    c = base.crop((L, T, L + side, T + side))
    if guide:   # True = 371 가드 기둥 띠 · (상자, 색) = 386 기름 줄기 띠
        (gx0, gy0, gx1, gy1), rgb = (GUIDE, GUIDE_RGB) if guide is True else guide
        ImageDraw.Draw(c).rectangle([gx0 - L, gy0 - T, gx1 - L, gy1 - T], fill=tuple(rgb))
    c.resize((EDIT, EDIT), Image.LANCZOS).save(inp)
    raw, sec = stem + "-raw.png", 0.0
    if not os.path.exists(raw):
        t = time.time()
        subprocess.run([MFLUX, "--model", "flux2-klein-4b", "-q", "8", "--image-paths", inp, "--prompt", prompt or PROMPTS[arm], "--seed", str(seed),
                        "--steps", "4", "--width", str(EDIT), "--height", str(EDIT), "--output", raw], check=False,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        sec = round(time.time() - t, 1)
    if not os.path.exists(raw):
        return {"status": "fail", "sec": sec}
    layer, mm = Image.new("RGB", base.size), Image.new("L", base.size, 0)
    e = Image.open(raw).convert("RGB").resize((side, side), Image.LANCZOS)
    layer.paste(color_match(e, base.crop((L, T, L + side, T + side))), (L, T))
    mm.paste(mask(crop, box), (L, T))
    Image.composite(layer, base, mm).save(out)
    return {"status": "ok", "sec": sec}


def add(m, sid, stage, arm, base_seed, seed, src, crop, box):
    sc = m["scenes"][sid]
    cid = f"{arm}-b{base_seed}-k{seed}"
    if any(c["id"] == cid for c in sc["candidates"]):
        return
    out = os.path.join(OUT, sid, cid + ".png")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    r = edit(src, crop, box, arm, seed, out, guide=arm == "G")
    m["sec"] = round(m["sec"] + r["sec"], 1)
    if r["status"] != "ok":
        print(f"[LocalEdit] {sid} {cid} 실패", flush=True)
        return
    sc["candidates"].append({"id": cid, "stage": stage, "arm": arm, "base": base_seed, "seed": seed, "src": src, "image": out,
                             "crop": list(crop), "box": list(box), "sec": r["sec"]})
    save_m(m)
    print(f"[LocalEdit] {sid} {cid} {r['sec']}s", flush=True)


def stage1(m, only=None):
    for sid, seeds in params.LOCAL_EDIT_BASES.items():
        for b in seeds:
            crop, box = BOX[(sid, b)]
            for arm in ARMS[sid]:
                for k in params.LOCAL_EDIT_SEEDS:
                    if only and (sid, b, arm, k) != only:
                        continue
                    add(m, sid, 1, arm, b, k, m["scenes"][sid]["bases"][str(b)], crop, box)


def stage2(m, spec):
    """가드 1단계 고른 장 위에 얼굴 편집(F) × 시드 3. spec = 'L,T,SIDE,x0,y0,x1,y1'(원본 좌표)."""
    sc = m["scenes"][GATH]
    p = sc.get("pick1") or {}
    if not p.get("id"):
        sys.exit("[LocalEdit] 가드 1단계 고른 장이 없다(「없음」) — 2단계 건너뜀")
    v = [int(x) for x in spec.split(",")]
    first = next(c for c in sc["candidates"] if c["id"] == p["id"])
    sc["face"] = {"crop": v[:3], "box": v[3:]}
    for k in params.LOCAL_EDIT_SEEDS:
        add(m, GATH, 2, "F", first["base"], k, first["image"], tuple(v[:3]), tuple(v[3:]))


def record(m, path):
    """판정 문장(「판정 task 371 단계 N」 + JSON 한 줄) → metrics. 장면의 마지막 단계이거나 「없음」이면 최종 pick + 명세 승인."""
    import approve
    v = json.loads(open(path, encoding="utf-8").read().split("\n", 1)[1])
    st = v["stage"]
    m.setdefault("human_minutes", {})[str(st)] = v.get("human_minutes")
    for sid, a in v["scenes"].items():
        sc = m["scenes"][sid]
        sc[f"items{st}"], sc[f"pick{st}"], sc[f"minutes{st}"] = a["items"], a["pick"], a.get("minutes")
        if st < STAGES[sid] and a["pick"]["id"]:
            continue
        sc["items"], sc["pick"] = a["items"], a["pick"]
        if a["pick"]["id"]:
            by = {c["id"]: c for c in sc["candidates"]}
            c = by[a["pick"]["id"]]
            steps, x = [], c
            while x:   # 편집 차례: 고른 장 → 그것을 얹은 앞 단계 장
                steps.insert(0, {k: x[k] for k in ("id", "arm", "seed", "crop", "box")} | {"prompt": PROMPTS[x["arm"]]})
                x = next((y for y in sc["candidates"] if y["image"] == x["src"]), None)
            spec = approve.load_spec(sid)
            approve.save_spec(approve.local_edit(spec, c["base"], c["image"], steps, "user"))
    save_m(m)


def page(stage):
    import make_local_edit_page
    make_local_edit_page.main(METRICS, stage)


# --- task#386 -------------------------------------------------------------------
NOTES = os.path.join(HERE, "notes", "LOCAL-EDIT.md")
M386 = os.path.join(HERE, "samples", "local-edit", "metrics-386.json")
OUT386 = os.path.join(OUT, "386")
sys.path.insert(0, os.path.join(HERE, "batch"))   # judge_items · plain_words · make_night_page
KINDS386 = {"J1": ("v2", 1.0), "J1-prop": ("p2", 2.5), "W": ("p2", 2.5)}   # 특징 문항은 J1-prop 머리말·편집 크롭 2.5배(고정 절)


def fx386():
    t = open(NOTES, encoding="utf-8").read()
    return json.loads(re.search(r"```json fixed386\n(.*?)\n```", t, re.S).group(1))


def load386():
    if os.path.exists(M386):
        return json.load(open(M386))
    F = fx386()
    return {"scenes": {sid: {"base": c["base"], "src": os.path.expanduser(F["src"].format(scene=sid, seed=c["base"])), "candidates": []}
                       for sid, c in F["scenes"].items()}, "answers": {}, "sec": 0}


def save386(m):
    os.makedirs(os.path.dirname(M386), exist_ok=True)
    tmp = M386 + ".tmp"
    json.dump(m, open(tmp, "w"), ensure_ascii=False, indent=1)
    os.replace(tmp, M386)


def run386(only=None):
    F, m = fx386(), load386()
    for sid, c in F["scenes"].items():
        sc = m["scenes"][sid]
        for arm, prompt in c["arms"].items():
            for k in F["seeds"]:
                cid = f"{arm}-k{k}"
                if (only and (sid, arm, k) != only) or any(x["id"] == cid for x in sc["candidates"]):
                    continue
                out = os.path.join(OUT386, sid, cid + ".png")
                os.makedirs(os.path.dirname(out), exist_ok=True)
                g = c.get("guide", {}).get(arm)
                r = edit(sc["src"], tuple(c["crop"]), tuple(c["box"]), arm, k, out, guide=(g["rect"], g["rgb"]) if g else False, prompt=prompt)
                m["sec"] = round(m["sec"] + r["sec"], 1)
                if r["status"] != "ok":
                    print(f"[LocalEdit386] {sid} {cid} 실패", flush=True)
                    continue
                sc["candidates"].append({"id": cid, "arm": arm, "seed": k, "image": out, "crop": c["crop"], "box": c["box"],
                                         "prompt": prompt, "sec": r["sec"]})
                save386(m)
                print(f"[LocalEdit386] {sid} {cid} {r['sec']}s", flush=True)


def check386():
    """C2 — 장면마다 6장 · 마스크 밖 픽셀이 원본과 같음(차 0) · 기록한 지시 글이 고정 절과 글자까지 같음."""
    F, m, bad = fx386(), load386(), []
    for sid, c in F["scenes"].items():
        sc = m["scenes"][sid]
        n = len(c["arms"]) * len(F["seeds"])
        if len(sc["candidates"]) != n:
            bad.append(f"{sid} 편집 {len(sc['candidates'])} ≠ {n}")
        base = Image.open(sc["src"]).convert("RGB")
        L, T, side = c["crop"]
        mm = Image.new("L", base.size, 0)
        mm.paste(mask(tuple(c["crop"]), tuple(c["box"])), (L, T))
        outside = mm.point(lambda v: 255 if v == 0 else 0)
        for x in sc["candidates"]:
            diff = ImageChops.difference(Image.open(x["image"]).convert("RGB"), base).convert("L").point(lambda v: 255 if v else 0)
            if ImageChops.multiply(diff, outside).getbbox():
                bad.append(f"{sid} {x['id']} 마스크 밖이 원본과 다름")
            if x["prompt"] != c["arms"][x["arm"]]:
                bad.append(f"{sid} {x['id']} 지시 글이 고정 절과 다름")
    print("ok" if not bad else "불통:\n" + "\n".join(bad))
    return not bad


def _items386(m, kind):
    """원본 + 편집 → 판정 항목. J1 = 382 r2에서 이 그림에 물은 문항 그대로(크롭은 바탕 시드 상자), W = 사전 특징 문항(편집 크롭)."""
    import plain_words as PW   # --set 없음 = 382 묶음(r2 문항·상자)
    import judge_items as J
    F, m382 = fx386(), PW.load_m()
    lex = {e["id"]: e for e in json.load(open(PW.WORDS, encoding="utf-8"))["words"]}
    out = []
    for sid, c in F["scenes"].items():
        sc, b = m["scenes"][sid], str(F["scenes"][sid]["base"])
        j1 = PW.j1_qs(m382, "r2", sid)
        L, T, side = c["crop"]
        W, H = Image.open(sc["src"]).size
        L, T, side = L / W, T / H, side   # judge_items 크롭은 그림 크기 비율(x, y, w, h)
        side_w, side_h = side / W, side / H
        qs = {"J1": j1, "J1-prop": [q for q in j1 if J.cls(q["id"]) == "prop"],
              "W": [{"id": f"w.{c['word']}.{j}", "q": lex[c["word"]]["word"], "what": f["q"], "who": "edit", "kind": "crop", "ar": 1,
                     "crop": {b: [L, T, side_w, side_h]}} for j, f in enumerate(lex[c["word"]]["criteria"]["features"])] +
                   [{"id": f"w.{c['word']}.x{j}", "q": lex[c["word"]]["word"], "what": f["q"], "who": "edit", "kind": "crop", "ar": 1,
                     "crop": {b: [L, T, side_w, side_h]}} for j, f in enumerate(c.get("extra_features", []))]}[kind]   # 사용자 지시 문항
        if not qs:
            continue
        spec = PW.canon(sid)
        for cid, img in [("orig", sc["src"])] + [(x["id"], x["image"]) for x in sc["candidates"]]:
            out.append({"key": f"{sid}:{cid}", "task": f"386-{cid}", "scene": sid, "title": spec["title"], "range": spec["verses"]["range"],
                        "seed": int(b), "src": img, "qs": qs, "qids": [q["id"] for q in qs]})
    return out


def judge386(workers=8):
    import judge_items as J
    from concurrent.futures import ThreadPoolExecutor
    import threading
    m, lock = load386(), threading.Lock()
    todo = [(k, it) for k in KINDS386 for it in _items386(m, k) if not (m["answers"].get(k, {}).get(it["key"]) or {}).get("answers")]
    print(f"[LocalEdit386] 판정 {len(todo)}건", flush=True)

    def one(job):
        kind, it = job
        header, zoom = KINDS386[kind]
        d, files = J.prepare(it, "local-edit-386", zoom)
        text, got, tries = J.prompt(it, files, J.HEADERS[header]), None, []
        for _ in range(2):
            o = J.call(text, d, "sonnet")
            tries.append(J.use(o) | {"error": bool(o.get("is_error"))})
            got = None if o.get("is_error") else J.parse(o.get("result"), it["qids"])
            if got:
                break
        with lock:
            m["answers"].setdefault(kind, {})[it["key"]] = {"tries": tries, **(got or {"answers": None})}
            save386(m)

    with ThreadPoolExecutor(workers) as ex:
        list(ex.map(one, todo))
    miss = sum(1 for k in KINDS386 for v in m["answers"].get(k, {}).values() if not v.get("answers"))
    for sid in m["scenes"]:
        r = rank386(m, sid)
        m["scenes"][sid]["top"] = {"id": r[0], "all_feats": feats_ok386(m, sid, r[0])}
        print(f"[LocalEdit386] {sid} 원본 특징 {sum(v == '맞음' for v in feats386(m, sid, 'orig').values())} · " +
              " · ".join(f"{c} 특징 {sum(v == '맞음' for v in feats386(m, sid, c).values())}/틀림 {wrong386(m, sid, c)}" for c in r) +
              f" → 1위 {r[0]}", flush=True)
    save386(m)
    print(f"[LocalEdit386] 판정 끝 · 답 없음 {miss}", flush=True)


def _a386(m, kind, sid, cid):
    return (m["answers"].get(kind, {}).get(f"{sid}:{cid}") or {}).get("answers") or {}


def feats386(m, sid, cid):
    return _a386(m, "W", sid, cid)


def feats_ok386(m, sid, cid):
    f = feats386(m, sid, cid)
    return bool(f) and all(v == "맞음" for v in f.values())


def wrong386(m, sid, cid):
    import judge_items as J
    a, p = _a386(m, "J1", sid, cid), _a386(m, "J1-prop", sid, cid)
    return sum(1 for q, v in a.items() if (p.get(q) if J.cls(q) == "prop" and q in p else v) == "틀림")


def rank386(m, sid):
    """편집만 — 특징 다 맞음 먼저 · (아니면 특징 맞힘 많은 순) · J1 틀림 적은 순 · 갈래 순서 · 시드 순서(고정 절 1위 규칙)."""
    F = fx386()
    arms, seeds = list(F["scenes"][sid]["arms"]), F["seeds"]
    right = lambda c: sum(v == "맞음" for v in feats386(m, sid, c).values())
    cs = m["scenes"][sid]["candidates"]
    return [x["id"] for x in sorted(cs, key=lambda x: (not feats_ok386(m, sid, x["id"]), 0 if feats_ok386(m, sid, x["id"]) else -right(x["id"]),
                                                        wrong386(m, sid, x["id"]), arms.index(x["arm"]), seeds.index(x["seed"])))]


def cand386(out=None):
    """장면마다 1화면: 원본 대 1위 편집 블라인드 좌우(장면 id 해시) · 카드마다 편집 부위 크롭 · 접힌 칸에 편집 6장."""
    import make_cand_page as C
    import make_night_page as P
    import plain_words as PW
    import judge_items as J
    F, m = fx386(), load386()
    page_t = (PW.PAGE.replace("<title>낱말 사전 그림 비교 382</title>", "<title>국소 편집 비교 386</title>")
              .replace("const TASK = 382;", "const TASK = 386;").replace('"plain-words-page-"', '"local-edit-page-"')
              .replace("<h2>굵은 절에 더 맞게 그린 쪽은?</h2>", "<h2>굵은 절의 모습이 보이고 이음 자국이 없는 쪽은?</h2>")
              .replace("<h1>${esc(s.title)} · ${esc(s.range)}</h1>", '<h1>${esc(s.title)} · ${esc(s.range)}</h1>${s.note ? `<p class="hint">${esc(s.note)}</p>` : ""}')
              .replace('((a.answer === "left") === (s.left_is === "A") ? "A" : "final")', '(a.answer === "left" ? s.left_is : s.right_is)')
              .replace('</div><span class="tag">${tag}</span><span class="zoom">크게</span></button>',
                       '</div><img src="${IMGS[key + "#c"]}" alt="편집 부위" style="width:100%;display:block"><span class="tag">${tag}</span><span class="zoom">크게</span></button>')
              .replace('<img src="${IMGS[k]}" alt="">`;', '<img src="${IMGS[k]}" alt="">${IMGS[k + "#c"] ? `<img src="${IMGS[k + "#c"]}" alt="">` : ""}`;')
              .replace('<div class="pair">${pic(s.left, "왼쪽")}${pic(s.right, "오른쪽")}</div>',
                       '<div class="pair">${pic(s.left, "왼쪽")}${pic(s.right, "오른쪽")}</div>${all6(s)}')
              .replace("function next() {", """function all6(s) {
  return `<details class="more"><summary>편집 ${s.all.length}장 전부(기계 불통과 포함 · 누르면 크게)</summary><div class="grid8">${s.all.map(([k, t]) =>
    `<button type="button" class="card" data-k="${k}"><img src="${IMGS[k + "#c"]}" alt="" style="width:100%;display:block"><span class="tag">${esc(t)}</span></button>`).join("")}</div></details>`;
}
function next() {""")
              .replace(".answer3 {", ".grid8 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 6px; margin: 8px 0; }\n.more summary { cursor: pointer; padding: 6px 0; }\n.answer3 {"))
    assert page_t.count("${all6(s)}") == 1 and "s.right_is" in page_t and page_t.count('IMGS[key + "#c"]') == 1
    for w, q in C.SIZES:
        scenes, data = [], {}
        for sid, c in F["scenes"].items():
            sc = m["scenes"][sid]
            top = sc["top"]["id"]
            imgs = {"orig": sc["src"], **{x["id"]: x["image"] for x in sc["candidates"]}}
            L, T, side = c["crop"]
            for cid, path in imgs.items():
                im = Image.open(path).convert("RGB")
                data[f"{sid}:{cid}"] = P.uri(im, w, q)
                data[f"{sid}:{cid}#c"] = P.uri(im.crop((L, T, L + side, T + side)), 480, q)
            orig_left = int(hashlib.sha1(sid.encode()).hexdigest(), 16) % 2 == 0
            left, right = (f"{sid}:orig", f"{sid}:{top}") if orig_left else (f"{sid}:{top}", f"{sid}:orig")
            spec = PW.canon(sid)
            scenes.append({"id": sid, "title": spec["title"], "range": spec["verses"]["range"], "ab": True, "reject": False,
                           "left": left, "right": right, "left_is": "orig" if orig_left else "edit", "right_is": "edit" if orig_left else "orig",
                           "top": top, "note": "" if sc["top"]["all_feats"] else "기계 1위도 특징 문항을 다 맞지는 못했습니다(맞힘이 가장 많은 장).",
                           "all": [[f"{sid}:{x['id']}", f"{x['arm']} · 시드 {x['seed']}"] for x in sc["candidates"]], "verses": C.scripture(sid)})
        page = (page_t.replace("/*STYLE*/", C.STYLE + C.VERSE_STYLE).replace("/*SCENES*/[]", json.dumps(scenes, ensure_ascii=False))
                .replace("/*IMGS*/{}", json.dumps(data)))
        if len(page) <= P.LIMIT:
            break
    out = out or os.path.join(J.PAGES, "local-edit-386-cand.html")
    open(out, "w", encoding="utf-8").write(page)
    m["cand"] = {s["id"]: {k: s[k] for k in ("left", "right", "left_is", "right_is", "top")} for s in scenes}
    save386(m)
    print(f"[LocalEdit386] 후보 화면 {out} {len(page) / 1e6:.2f}MB · {w}px q{q} · 화면 {len(scenes)}", flush=True)


def record386(path):
    """「판정 task 386」 + JSON 한 줄 → metrics human · 편집 쪽을 고른 장면은 명세 approved.final(path: local-edit) + 승인 그림 레포 사본."""
    import approve
    F, m = fx386(), load386()
    v = json.loads(open(path, encoding="utf-8").read().split("\n", 1)[1])
    assert v["task"] == 386 and v["kind"] == "ab", v.get("task")
    m["human"] = {k: v.get(k) for k in ("human_minutes", "active_minutes", "screens")} | {"scenes": {}}
    for sid, a in v["scenes"].items():
        assert (a["left"], a["right"]) == (m["cand"][sid]["left"], m["cand"][sid]["right"]), sid
        m["human"]["scenes"][sid] = {k: a.get(k) for k in ("answer", "chose", "memo", "minutes", "active_minutes")}
        if a["chose"] != "edit":
            continue
        sc, top = m["scenes"][sid], m["cand"][sid]["top"]
        x = next(c for c in sc["candidates"] if c["id"] == top)
        keep = os.path.join(HERE, "samples", "local-edit", f"approved-{sid}.png")
        shutil.copyfile(x["image"], keep)
        steps = [{"id": x["id"], "arm": x["arm"], "seed": x["seed"], "crop": x["crop"], "box": x["box"], "prompt": x["prompt"],
                  "base_src": f"plain-words r2 s{sc['base']}"}]
        approve.save_spec(approve.local_edit(approve.load_spec(sid), sc["base"], os.path.relpath(keep, HERE), steps, "user"))
    save386(m)
    print("[LocalEdit386] 사람 답 " + " · ".join(f"{s.split('-', 2)[2]} {a['chose']}" for s, a in m["human"]["scenes"].items()), flush=True)


def verdict386():
    n = sum(a["chose"] == "edit" for a in load386()["human"]["scenes"].values())
    line = {2: "판정: 둘 다 고침", 1: "판정: 하나 고침", 0: "판정: 못 고침"}[n]
    print(line)
    return line


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd in ("trial386", "run386") and busy():
        sys.exit(f"[LocalEdit386] 다른 생성 프로세스가 돈다 — 겹치지 않게 멈춤:\n{busy()}")
    if cmd in ("trial386", "run386", "check386", "judge386", "cand386", "record386", "verdict386"):
        F = fx386()
        {"trial386": lambda: run386(("authored-samuel-bethlehem-david-anointing", "O1", F["seeds"][0])), "run386": run386,
         "check386": lambda: sys.exit(0 if check386() else 1), "judge386": judge386, "cand386": lambda: cand386(sys.argv[2] if len(sys.argv) > 2 else None),
         "record386": lambda: record386(sys.argv[2]), "verdict386": verdict386}[cmd]()
        sys.exit(0)
    if cmd in ("trial", "stage1", "stage2") and busy():
        sys.exit(f"[LocalEdit] 다른 생성 프로세스가 돈다 — 겹치지 않게 멈춤:\n{busy()}")
    m = load_m()
    if cmd == "trial":
        stage1(m, (NOB, 7, "N1", 1))
    elif cmd == "stage1":
        stage1(m)
        page(1)
    elif cmd == "stage2":
        stage2(m, sys.argv[2])
        page(2)
    elif cmd == "page":
        page(int(sys.argv[2]))
    elif cmd == "record":
        record(m, sys.argv[2])
