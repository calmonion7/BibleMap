"""task 656·658 — 정본 s5에 잘린 끝·입구 마개를 칠하고 같은 생성기로 약하게 다시 그림(사람 655 「뾰족한 끝이 잘려 있어야 … 입구에는 마개」)."""
import os, sys
CANON = "/Users/calmonion/Project/BibleMap/scripts/canon"
sys.path.insert(0, CANON); sys.path.insert(0, os.path.join(CANON, "batch"))
from PIL import Image, ImageDraw
D = os.path.join(CANON, "samples", "prop-oil-horn-lying")

def compose():
    import math
    im = Image.open(os.path.join(D, "sheet-s5.png")).convert("RGB")
    d = ImageDraw.Draw(im)
    paper = im.getpixel((1050, 150))
    def ell(cx, cy, rx, ry, deg, n=64):
        a = math.radians(deg)
        return [(cx + rx * math.cos(t) * math.cos(a) - ry * math.sin(t) * math.sin(a),
                 cy + rx * math.cos(t) * math.sin(a) + ry * math.sin(t) * math.cos(a)) for t in (2 * math.pi * i / n for i in range(n))]
    def hull(pts):
        pts = sorted(set(pts)); cr = lambda o, a, b: (a[0]-o[0])*(b[1]-o[1]) - (a[1]-o[1])*(b[0]-o[0])
        lo, up = [], []
        for q in pts:
            while len(lo) >= 2 and cr(lo[-2], lo[-1], q) <= 0: lo.pop()
            lo.append(q)
        for q in reversed(pts):
            while len(up) >= 2 and cr(up[-2], up[-1], q) <= 0: up.pop()
            up.append(q)
        return lo[:-1] + up[:-1]
    # 끝: 뿔 축(약 -31°)에 수직으로 x 935에서 자름 — 단면은 뿔 굵기 그대로·뿔 색, 가운데 작은 구멍(사람 657 「구멍이 자연스럽지 않음」 — 옅은 원판이 와셔처럼 보였음)
    cx, cy, ux, uy = 935, 250, math.cos(math.radians(-31)), math.sin(math.radians(-31))
    px = im.load()
    for x in range(915, 1000):
        for y in range(195, 315):
            if (x - cx) * ux + (y - cy) * uy > 0: px[x, y] = paper
    d.polygon(ell(cx, cy, 18, 6, 59), fill=(104, 70, 40), outline=(40, 27, 16))
    d.polygon(ell(cx + 1, cy - 1, 12, 3.5, 59), fill=(124, 86, 50))                       # 단면 결(가운데 조금 밝게)
    d.polygon(ell(cx, cy, 4, 2.5, 59), fill=(22, 13, 6))                                 # 작은 주둥이 구멍
    # 입구: 위로 조금 튀어나온 나무 원통 마개(사람 657 「마개는 진흙인가?」 → 사람 「나무 마개」)
    mx, my, rx, ry, deg, ox, oy = 356, 234, 67, 27, -11, -4, -20
    d.polygon(ell(mx, my, 72, 31, deg), fill=(38, 24, 12))                                # 마개와 입구 테 사이 그림자
    base, top = ell(mx, my, rx, ry, deg), ell(mx + ox, my + oy, rx, ry, deg)
    d.polygon(hull([(round(x), round(y)) for x, y in base + top]), fill=(146, 100, 58), outline=(70, 45, 24))
    for i in range(10, 31, 3):                                                           # 옆면 나뭇결(앞쪽 = 아래 반만 보임)
        (x0, y0), (x1, y1) = base[i], top[i]
        d.line([(x0, y0), (x1 + 1, y1)], fill=(112, 74, 40), width=2)
    for i in range(0, 9):                                                                # 오른쪽 옆면 그늘
        d.line([base[i], top[i]], fill=(118, 80, 44), width=3)
    d.polygon(top, fill=(188, 142, 92), outline=(92, 60, 32))                            # 윗면(나무 끝면)
    for k in (0.75, 0.5, 0.25):                                                          # 나이테
        d.polygon(ell(mx + ox + 4, my + oy, rx * k, ry * k, deg), outline=(150, 106, 64))
    im.save(os.path.join(D, "fix-src.png"))


def redraw():
    import run_scene, prop_sheet as P
    os.chdir(CANON)
    prompt = (f"{P.STYLE} A single object drawn alone on plain warm cream paper, with nothing else: {P.look('oil-horn')}, "
              "lying on its side, its wide opening at the upper left closed by a short round wooden plug with visible wood grain that sticks out slightly, the body sagging into a gentle curve "
              "and rising to the right, its narrow tip cut off square with a tiny drilled hole in the dark horn. No hands, no people, no background, no text.")
    jobs = [{"prompt": prompt, "seed": 5, "w": 1216, "h": 640, "src": os.path.join(D, "fix-src.png"), "strength": s,
             "out": os.path.join(D, f"fix-{s}.png")} for s in (0.2, 0.25)]
    tmp = os.path.expanduser("~/.local/biblemap-imggen/prop-oil-horn-lying"); os.makedirs(tmp, exist_ok=True)
    print("[HornSheetFix]", run_scene.gen_zimage(jobs, tmp, "i2i"))

{"compose": compose, "redraw": redraw}[sys.argv[1]]()
