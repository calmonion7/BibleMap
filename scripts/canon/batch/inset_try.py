#!/usr/bin/env python3
"""곁 장면(뭉게구름) 합성 도구(task 417 솔로몬 출생 시험 → task 421 일반화): 큰 장면과 그 `inset.spec` 곁 장면을 시드마다 따로 그려
명세 inset.region 자리에 크림 종이 뭉게구름 가장자리로 합성한다(규칙 spec.inset · generate.inset-frame-aspect).

  VENV=~/.local/biblemap-imggen/.venv314/bin/python
  $VENV batch/inset_try.py gen  --main <큰 장면 id> --dir <이름> --seeds 42,7   # 두 장면 route_prompt · 가이드 · 시드마다 한 장씩
  python3 batch/inset_try.py comp --main <큰 장면 id> --dir <이름> --seeds 42,7  # 합성 → samples/<이름>/comp-s<시드>.png
  (--main 기본 솔로몬 출생 · --dir 기본 = 큰 장면 id에서 authored- 뺀 것 · --seeds 기본 42 · 가이드는 samples/<이름>/guide-<장면 id>[-1|-2].png)"""
import json, os, subprocess, sys

from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "batch"))
import derive_scene as D
import paper_margin

def _arg(name, default):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


MAIN = _arg("--main", "authored-solomon-jerusalem-birth")
NAME = _arg("--dir", MAIN.removeprefix("authored-"))
SEEDS = [int(x) for x in _arg("--seeds", _arg("--seed", "42")).split(",")]
W, H = 1216, 640
CN = {"scale": 1.0, "cn_steps": 4}   # 단일 깊이 가이드 — 기브아 a6~f6e3과 같은 값
OUT = os.path.expanduser(f"~/.local/biblemap-imggen/{NAME}")
SAMPLES = os.path.join(HERE, "samples", NAME)
PAPER = (243, 234, 214)   # 화풍 머리 「warm cream paper」 바탕 빛


def img(sid, seed):
    return os.path.join(OUT, f"{sid}-s{seed}.png")


def gen():
    import recheck
    import run_scene
    spec = D.load(MAIN)
    sub = spec["inset"]["spec"]
    busy = subprocess.run(["pgrep", "-fl", "mflux|run_scene.py --worker|gen_video_pilot|mlx_video"], capture_output=True, text=True).stdout.strip()
    if busy:
        sys.exit(f"[Inset] 다른 생성 프로세스가 돈다 — 겹치지 않게 멈춤:\n{busy}")
    os.makedirs(OUT, exist_ok=True)
    jobs = []
    for sid in (MAIN, sub):
        recheck.require_pass(sid)   # generate.spec-gate
        guide = os.path.join(SAMPLES, f"guide-{sid}.png")
        w = W
        if sid == sub:   # 곁 장면은 구름 틀 비율로 그림 — 넓은 화면에 앉은 한 사람이면 빈자리에 다른 사람을 그려 넣음(s42 곁에 선 여인, 문구를 바꿔도 남음)
            w = inset_w(spec)
            g = Image.open(guide).convert("RGB")   # make_guide sit 꼴이 screen_facing을 따름(task 417 — 전엔 여기서 좌우를 뒤집음)
            rs = [r for k, r in D.load(sid)["regions"].items() if k != "full"]
            cx = sum((r[0] + r[2]) / 2 for r in rs) / len(rs) * W   # 인물 구역 가운데를 중심으로 자름(출생 곁 장면은 0.5 — 전과 같음)
            x0 = min(max(0, round(cx - w / 2)), W - w)
            g = g.crop((x0, 0, x0 + w, H))
            guide = os.path.join(OUT, f"_guide-{sid}-flip-{w}.png")
            g.save(guide)
        cn = {"control": guide, **CN}
        if D.load(sid)["guide"].get("split"):   # 시도 3: 뼈대 인물은 스텝별 가이드(앞 2스텝 뼈대 → 뒤 2스텝 깊이, 기브아 m17e와 같은 값)
            cn = {"control": os.path.join(SAMPLES, f"guide-{sid}-1.png"), "control2": os.path.join(SAMPLES, f"guide-{sid}-2.png"),
                  "scale": CN["scale"], "cn_steps": 2, "cn_steps2": 2}
        jobs += [{"prompt": D.route_prompt(D.load(sid)), "seed": seed, "w": w, "h": H, "out": img(sid, seed), **cn}
                 for seed in SEEDS if not os.path.exists(img(sid, seed))]
    print(f"[Inset] {len(jobs)}장 생성", flush=True)
    if jobs:
        print(f"[Inset] 생성 끝 {run_scene.gen_zimage(jobs, OUT, 'gencn')}", flush=True)


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
    for seed in SEEDS:
        comp_one(seed)


def comp_one(seed):
    spec = D.load(MAIN)
    sub = spec["inset"]["spec"]
    base = paper_margin.trim(Image.open(img(MAIN, seed)).convert("RGB"))   # 규칙 generate.trim-paper-margin — 생성 때 안 잘린 옛 그림도(task 422)
    x0, y0, x1, y1 = spec["inset"]["region"]
    bx, by, bw, bh = round(x0 * W), round(y0 * H), round((x1 - x0) * W), round((y1 - y0) * H)
    ins = paper_margin.trim(Image.open(img(sub, seed)).convert("RGB")).resize((bw, bh), Image.LANCZOS)   # 곁 장면은 이미 틀 비율로 그림
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
    dst = os.path.join(SAMPLES, f"comp-s{seed}.png")
    out.save(dst)
    print(f"[Inset] 합성 {dst}")


if __name__ == "__main__":
    {"gen": gen, "comp": comp}[sys.argv[1]]()
