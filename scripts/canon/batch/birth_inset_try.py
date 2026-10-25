#!/usr/bin/env python3
"""task 417 — 곁 장면(뭉게구름) 합성 시험: 큰 장면(삼하 12:25 나단)과 곁 장면(12:24 밧세바가 아들을 안음)을 고정 시드 한 장씩 따로 그려
명세 inset.region 자리에 크림 종이 뭉게구름 가장자리로 합성한다(사람 결정 2026-10-25, fu-416b1c7e2a90).

  VENV=~/.local/biblemap-imggen/.venv314/bin/python
  $VENV batch/birth_inset_try.py gen        # 두 장면 route_prompt · 깊이 가이드(CN 1.0 · 4스텝) · 시드 SEED 한 장씩
  python3 batch/birth_inset_try.py comp     # 합성 → samples/birth-inset/comp-s<시드>.png

곁 장면 가이드는 좌우를 뒤집어 씀 — make_guide sit 꼴은 왼쪽을 보는데 곁 장면 밧세바는 큰 장면 쪽(오른쪽)을 봄(시험 한정)."""
import json, os, subprocess, sys

from PIL import Image, ImageDraw, ImageFilter, ImageOps

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "batch"))
import derive_scene as D

MAIN = "authored-solomon-jerusalem-birth"
SEED = int(sys.argv[sys.argv.index("--seed") + 1]) if "--seed" in sys.argv else 42
W, H = 1216, 640
CN = {"scale": 1.0, "cn_steps": 4}   # 단일 깊이 가이드 — 기브아 a6~f6e3과 같은 값
OUT = os.path.expanduser("~/.local/biblemap-imggen/birth-inset")
SAMPLES = os.path.join(HERE, "samples", "birth-inset")
PAPER = (243, 234, 214)   # 화풍 머리 「warm cream paper」 바탕 빛


def img(sid):
    return os.path.join(OUT, f"{sid}-s{SEED}.png")


def gen():
    import recheck
    import run_scene
    spec = D.load(MAIN)
    sub = spec["inset"]["spec"]
    busy = subprocess.run(["pgrep", "-fl", "mflux|run_scene.py --worker|gen_video_pilot|mlx_video"], capture_output=True, text=True).stdout.strip()
    if busy:
        sys.exit(f"[BirthInset] 다른 생성 프로세스가 돈다 — 겹치지 않게 멈춤:\n{busy}")
    os.makedirs(OUT, exist_ok=True)
    jobs = []
    for sid in (MAIN, sub):
        recheck.require_pass(sid)   # generate.spec-gate
        guide = os.path.join(SAMPLES, f"guide-{sid}.png")
        w = W
        if sid == sub:   # 곁 장면은 구름 틀 비율로 그림 — 넓은 화면에 앉은 한 사람이면 빈자리에 다른 사람을 그려 넣음(s42 곁에 선 여인, 문구를 바꿔도 남음)
            w = inset_w(spec)
            g = ImageOps.mirror(Image.open(guide).convert("RGB"))
            x0 = (W - w) // 2   # 인물 구역이 가운데(0.38~0.62)라 가운데로 자름
            g = g.crop((x0, 0, x0 + w, H))
            guide = os.path.join(OUT, f"_guide-{sid}-flip-{w}.png")
            g.save(guide)
        cn = {"control": guide, **CN}
        if D.load(sid)["guide"].get("split"):   # 시도 3: 뼈대 인물은 스텝별 가이드(앞 2스텝 뼈대 → 뒤 2스텝 깊이, 기브아 m17e와 같은 값)
            cn = {"control": os.path.join(SAMPLES, f"guide-{sid}-1.png"), "control2": os.path.join(SAMPLES, f"guide-{sid}-2.png"),
                  "scale": CN["scale"], "cn_steps": 2, "cn_steps2": 2}
        if not os.path.exists(img(sid)):
            jobs.append({"prompt": D.route_prompt(D.load(sid)), "seed": SEED, "w": w, "h": H, "out": img(sid), **cn})
    print(f"[BirthInset] {len(jobs)}장 생성", flush=True)
    if jobs:
        print(f"[BirthInset] 생성 끝 {run_scene.gen_zimage(jobs, OUT, 'gencn')}", flush=True)


def inset_w(spec):
    """곁 장면 생성 너비 — 구름 틀(inset.region) 가로세로 비 × 높이 H, 16의 배수."""
    x0, y0, x1, y1 = spec["inset"]["region"]
    return round((x1 - x0) * W / ((y1 - y0) * H) * H / 16) * 16


def cloud_mask(w, h, inset=0):
    """뭉게구름 꼴 — 안쪽 타원 + 가장자리를 따라 겹친 원(둥근 혹). inset만큼 안으로 줄임."""
    import math
    m = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(m)
    cx, cy, rx, ry = w / 2, h / 2, w / 2 - inset, h / 2 - inset
    bump = min(rx, ry) * 0.22
    d.ellipse([cx - (rx - bump), cy - (ry - bump), cx + (rx - bump), cy + (ry - bump)], fill=255)
    n = 18
    for i in range(n):
        a = 2 * math.pi * i / n
        x, y = cx + (rx - bump) * math.cos(a), cy + (ry - bump) * math.sin(a)
        r = bump * (1.0 if i % 2 else 0.8)
        d.ellipse([x - r, y - r, x + r, y + r], fill=255)
    return m


def comp():
    spec = D.load(MAIN)
    sub = spec["inset"]["spec"]
    base = Image.open(img(MAIN)).convert("RGB")
    x0, y0, x1, y1 = spec["inset"]["region"]
    bx, by, bw, bh = round(x0 * W), round(y0 * H), round((x1 - x0) * W), round((y1 - y0) * H)
    ins = Image.open(img(sub)).convert("RGB").resize((bw, bh), Image.LANCZOS)   # 곁 장면은 이미 틀 비율로 그림
    pad = 14                                   # 종이 테두리 두께(px)
    outer = cloud_mask(bw, bh)                 # 종이 구름(바깥)
    inner = cloud_mask(bw, bh, inset=pad).filter(ImageFilter.GaussianBlur(4))   # 그림이 비치는 안쪽 — 가장자리 번짐
    paper = Image.new("RGB", (bw, bh), PAPER)
    cloud = Image.composite(ins, paper, inner)
    out = base.copy()
    out.paste(cloud, (bx, by), outer.filter(ImageFilter.GaussianBlur(1.5)))
    # 연필 테두리 — 바깥 구름 윤곽을 옅은 회갈색으로
    edge = outer.filter(ImageFilter.FIND_EDGES).filter(ImageFilter.GaussianBlur(0.8)).point(lambda v: min(255, v * 2))
    line = Image.new("RGB", (bw, bh), (120, 105, 90))
    out.paste(line, (bx, by), edge.point(lambda v: int(v * 0.55)))
    os.makedirs(SAMPLES, exist_ok=True)
    dst = os.path.join(SAMPLES, f"comp-s{SEED}.png")
    out.save(dst)
    print(f"[BirthInset] 합성 {dst}")


if __name__ == "__main__":
    {"gen": gen, "comp": comp}[sys.argv[1]]()
