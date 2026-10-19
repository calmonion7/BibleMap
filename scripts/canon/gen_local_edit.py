#!/usr/bin/env python3
"""task#371 — 국소 편집: 고른 바탕의 한 부위만 klein 지시 편집으로 고친다(엔게디 칼 조리법 일반화 — gen_engedi_knife.py는 그대로).
작은 크롭 → 1024 klein 편집(지시 하나) → 원본 크롭 색에 맞춤(color_match) → 타원 마스크 안쪽만 되붙임.

  python3 gen_local_edit.py trial            # S1 시험: 놉 제사장 s7 · N1 · 시드 1 한 장
  python3 gen_local_edit.py stage1           # 놉 제사장 12장 + 가드 몸 12장(이미 있으면 건너뜀) → 판정 페이지 1
  python3 gen_local_edit.py stage2 L,T,SIDE,x0,y0,x1,y1   # 가드 1단계 고른 장의 얼굴 크롭·마스크 → 3장 → 판정 페이지 2
  python3 gen_local_edit.py page 1|2         # 판정 페이지만 다시
  python3 gen_local_edit.py record <판정.txt> # 페이지 「판정 문장」 → metrics + 고른 장면 명세 approved.final(path: local-edit)

산출 ~/.local/biblemap-imggen/local-edit/<장면>/, 목록 samples/local-edit/metrics.json. 고정 절 notes/LOCAL-EDIT.md."""
import json, os, subprocess, sys, time

from PIL import Image, ImageDraw, ImageFilter

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


def edit(src, crop, box, arm, seed, out, guide=False):
    """바탕 src의 crop 부위를 klein으로 고쳐 out에 되붙인다 → 기록(dict). 이미 있으면 다시 그리지 않는다."""
    L, T, side = crop
    base = Image.open(src).convert("RGB")
    stem = out[:-4]
    inp = stem + "-in.png"
    c = base.crop((L, T, L + side, T + side))
    if guide:
        ImageDraw.Draw(c).rectangle([GUIDE[0] - L, GUIDE[1] - T, GUIDE[2] - L, GUIDE[3] - T], fill=GUIDE_RGB)
    c.resize((EDIT, EDIT), Image.LANCZOS).save(inp)
    raw, sec = stem + "-raw.png", 0.0
    if not os.path.exists(raw):
        t = time.time()
        subprocess.run([MFLUX, "--model", "flux2-klein-4b", "-q", "8", "--image-paths", inp, "--prompt", PROMPTS[arm], "--seed", str(seed),
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


if __name__ == "__main__":
    cmd = sys.argv[1]
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
