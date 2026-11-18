"""task 645 — 뿔을 직접 칠해 얹은 뒤 같은 생성기(Z-Image img2img)로 그림 전체를 가볍게 다시 그림.
뿔만 따로 생성하면 생성기가 또 넓은 입으로 붓는 꼴을 그리므로, 꼴은 손으로 정하고 화풍은 생성기가 입힌다.
쓰기: python3 horn_compose.py compose  → src.png
      venv314 python horn_compose.py redraw  → out-<strength>.png"""
import json, os, sys
from PIL import Image, ImageDraw, ImageFilter

CANON = "/Users/calmonion/Project/BibleMap/scripts/canon"
OUT = os.path.join(CANON, "samples", "bethlehem-horn-i2i")
BASE = os.path.join(CANON, "samples", "bethlehem-step23-t9", "composition-A-s202.png")
SEED, STRENGTHS = 202, (0.2, 0.28, 0.35)   # 0.35 이상은 생성기가 뿔을 넓은 입 쪽으로 다시 뒤집음(task 645)


def bez(p0, c, p1, n=24):
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * c[0] + t * t * p1[0],
             (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * c[1] + t * t * p1[1]) for t in (i / n for i in range(n + 1))]


def compose():
    import cv2
    import numpy as np
    os.makedirs(OUT, exist_ok=True)
    im = Image.open(BASE).convert("RGB")
    mask = Image.new("L", im.size, 0)
    md = ImageDraw.Draw(mask)
    md.polygon([(436, 318), (434, 300), (468, 254), (484, 246), (500, 248), (514, 258), (514, 300), (500, 306), (470, 300), (450, 330)], fill=255)   # 옛 뿔(손 위쪽)·넓은 입·기름 줄기
    a = cv2.inpaint(np.array(im)[:, :, ::-1], np.array(mask), 7, cv2.INPAINT_TELEA)   # 둘레 화소로 메움(평평한 색 덮개는 뒤 형 머리 위에 갈색 덩어리)
    im = Image.fromarray(a[:, :, ::-1])
    d = ImageDraw.Draw(im)
    pts = bez((443, 318), (477, 260), (502, 286))     # 밑동(두 손 위) → 위로 휘어 → 뾰족한 끝(소년 머리 위, 아래를 향함) · 길이 약 60화소(사전 0.15 × 사람 키)
    n = len(pts) - 1
    for i, (x, y) in enumerate(pts):                  # 바깥 선(짙은 뼈빛) 먼저
        r = 9 * (1 - i / n) + 1.2
        d.ellipse([x - r - 1.2, y - r - 1.2, x + r + 1.2, y + r + 1.2], fill=(150, 125, 85))
    for i, (x, y) in enumerate(pts):                  # 몸통(옅은 뼈빛)
        r = 9 * (1 - i / n) + 1.2
        d.ellipse([x - r, y - r, x + r, y + r], fill=(232, 218, 182))
    d.ellipse([500, 284, 505, 289], fill=(90, 70, 45))                     # 열린 뾰족한 끝
    d.line([(503, 289), (505, 300)], fill=(214, 168, 40), width=3)          # 끝에서 소년 머리로 떨어지는 금빛 기름
    im.save(os.path.join(OUT, "src.png"))
    print("[HornCompose]", os.path.join(OUT, "src.png"))


def redraw():
    sys.path.insert(0, os.path.join(CANON, "batch"))
    sys.path.insert(0, CANON)
    os.chdir(CANON)
    import rule_ab as R
    import run_scene
    R.use(639)
    pa, _ = R.prompts(R.FX["cases"][0])
    jobs = [{"prompt": pa, "seed": SEED, "w": 1216, "h": 640, "src": os.path.join(OUT, "src.png"), "strength": s,
             "out": os.path.join(OUT, f"out-{s}.png")} for s in STRENGTHS]
    tmp = os.path.expanduser("~/.local/biblemap-imggen/bethlehem-horn-i2i")
    os.makedirs(tmp, exist_ok=True)
    print("[HornCompose] i2i", run_scene.gen_zimage(jobs, tmp, "i2i"))


if __name__ == "__main__":
    {"compose": compose, "redraw": redraw}[sys.argv[1]]()
