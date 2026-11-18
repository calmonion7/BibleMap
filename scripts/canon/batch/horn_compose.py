"""task 645 — 뿔을 직접 칠해 얹은 뒤 같은 생성기(Z-Image img2img)로 그림 전체를 가볍게 다시 그림.
뿔만 따로 생성하거나 문구·가이드로 방향을 주면 생성기가 넓은 입으로 붓는 꼴로 되돌림(베들레헴 639·641·644 · 기혼 640·642) —
꼴은 손으로 정하고 화풍은 생성기가 입힌다. 세기 0.35 이상은 생성기가 뿔을 넓은 입 쪽으로 다시 뒤집음(task 645).
task 646 — 장면별 설정 · 짧고 굵은 원뿔꼴(사람 645 「기름뿔 모양 이상함」 — 길고 가는 뿔은 상아·낫처럼 보임).
쓰기: venv314 python horn_compose.py <scene> compose  → samples/<out>/src.png
      venv314 python horn_compose.py <scene> redraw   → samples/<out>/out-<strength>.png"""
import os, sys
from PIL import Image, ImageDraw

CANON = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCENES = {
    # base: 출발 그림 · fixed: 장면 문구를 읽을 고정 절 · seed · erase: 지울 옛 뿔·잔·기름 다각형들 · horn: (밑동, 굽음, 끝) · r: 밑동 반지름 · oil: 끝에서 머리까지
    "bethlehem": {"base": "samples/bethlehem-step23-t9/composition-A-s202.png", "out": "bethlehem-horn-i2i", "fixed": 639, "seed": 202,
                  "erase": [[(436, 318), (434, 300), (468, 254), (484, 246), (500, 248), (514, 258), (514, 300), (500, 306), (470, 300), (450, 330)]],
                  "horn": ((443, 318), (477, 260), (502, 286)), "r": 9, "oil": ((503, 289), (505, 300)), "strengths": (0.2, 0.28, 0.35)},
    "gihon": {"base": "samples/gihon-step23-t15/composition-A-s101.png", "out": "gihon-horn-i2i", "fixed": 642, "seed": 101,
              "erase": [[(516, 352), (522, 330), (540, 304), (558, 296), (586, 298), (594, 322), (582, 372), (570, 374), (540, 350)],
                        [(530, 368), (558, 366), (558, 404), (532, 406)]],   # 옛 뿔·기름 줄기 · 왼손의 잔(붓는 그릇이 둘)
              "horn": ((523, 374), (552, 326), (579, 361)), "r": 12, "oil": ((580, 364), (583, 377)), "oil_w": 5, "strengths": (0.2,)},   # task 646 b: 밑동을 두 손 사이(손이 비면 잔을 다시 쥐여 줌) · 기름 굵게(가는 줄은 흰 줄·검은 선으로 읽힘)
}


def bez(p0, c, p1, n=24):
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * c[0] + t * t * p1[0],
             (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * c[1] + t * t * p1[1]) for t in (i / n for i in range(n + 1))]


def compose(cfg):
    import cv2
    import numpy as np
    out = os.path.join(CANON, "samples", cfg["out"])
    os.makedirs(out, exist_ok=True)
    im = Image.open(os.path.join(CANON, cfg["base"])).convert("RGB")
    mask = Image.new("L", im.size, 0)
    md = ImageDraw.Draw(mask)
    for poly in cfg["erase"]:
        md.polygon(poly, fill=255)
    a = cv2.inpaint(np.array(im)[:, :, ::-1], np.array(mask), 7, cv2.INPAINT_TELEA)   # 둘레 화소로 메움(평평한 색 덮개는 뒤 사람 위에 덩어리)
    im = Image.fromarray(a[:, :, ::-1])
    d = ImageDraw.Draw(im)
    pts = bez(*cfg["horn"])   # 밑동(손 안) → 조금 휘어 → 뾰족한 끝(머리 위, 아래를 향함)
    n, r0 = len(pts) - 1, cfg["r"]
    for i, (x, y) in enumerate(pts):                  # 바깥 선(짙은 뼈빛) 먼저
        r = r0 * (1 - i / n) ** 0.8 + 1.2             # 밑동이 넓은 원뿔꼴(0.8제곱 — 끝 가까이에서 빨리 가늘어짐)
        d.ellipse([x - r - 1.2, y - r - 1.2, x + r + 1.2, y + r + 1.2], fill=(150, 125, 85))
    for i, (x, y) in enumerate(pts):                  # 몸통(옅은 뼈빛)
        r = r0 * (1 - i / n) ** 0.8 + 1.2
        d.ellipse([x - r, y - r, x + r, y + r], fill=(232, 218, 182))
    (tx, ty), (ox, oy) = cfg["oil"]
    d.ellipse([tx - 2.5, ty - 4.5, tx + 2.5, ty + 0.5], fill=(90, 70, 45))   # 열린 뾰족한 끝
    d.line([(tx, ty), (ox, oy)], fill=(214, 168, 40), width=cfg.get("oil_w", 3))   # 끝에서 머리로 떨어지는 금빛 기름
    im.save(os.path.join(out, "src.png"))
    print("[HornCompose]", os.path.join(out, "src.png"))


def redraw(cfg):
    sys.path.insert(0, os.path.join(CANON, "batch"))
    sys.path.insert(0, CANON)
    os.chdir(CANON)
    import rule_ab as R
    import run_scene
    R.use(cfg["fixed"])
    pa, _ = R.prompts(R.FX["cases"][0])
    out = os.path.join(CANON, "samples", cfg["out"])
    jobs = [{"prompt": pa, "seed": cfg["seed"], "w": 1216, "h": 640, "src": os.path.join(out, "src.png"), "strength": s,
             "out": os.path.join(out, f"out-{s}.png")} for s in cfg["strengths"]]
    tmp = os.path.expanduser(f"~/.local/biblemap-imggen/{cfg['out']}")
    os.makedirs(tmp, exist_ok=True)
    print("[HornCompose] i2i", run_scene.gen_zimage(jobs, tmp, "i2i"))


if __name__ == "__main__":
    {"compose": compose, "redraw": redraw}[sys.argv[2]](SCENES[sys.argv[1]])
