"""task 656·658·659 — 정본 s5에 잘린 끝·입구 마개를 칠하고 같은 생성기로 약하게 다시 그림(사람 655 「뾰족한 끝이 잘려 있어야 … 입구에는 마개」)."""
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
    # 끝: 뿔 축(약 -31°)에 수직으로 x 935에서 자름 — 단면은 뿔 굵기 그대로·뿔 색, 가운데 작은 구멍(사람 657 「구멍이 자연스럽지 않음」 — 옅은 원판이 와셔처럼 보였음)
    cx, cy, ux, uy = 935, 250, math.cos(math.radians(-31)), math.sin(math.radians(-31))
    px = im.load()
    for x in range(915, 1000):
        for y in range(195, 315):
            if (x - cx) * ux + (y - cy) * uy > 0: px[x, y] = paper
    d.polygon(ell(cx, cy, 18, 6, 59), fill=(104, 70, 40), outline=(40, 27, 16))
    d.polygon(ell(cx + 1, cy - 1, 12, 3.5, 59), fill=(124, 86, 50))                       # 단면 결(가운데 조금 밝게)
    d.polygon(ell(cx, cy, 4, 2.5, 59), fill=(22, 13, 6))                                 # 작은 주둥이 구멍
    # 입구: 테와 같은 높이로 끼운 납작한 나무판 + 송진 이음매(사람 658 「그 시대 마개는?」 → 사람 고증: 넓은 밑동은 나무판 등으로 영구히 막고 밀랍·송진으로 봉함)
    mx, my, rx, ry, deg = 352, 234, 78, 33, -11
    d.polygon(ell(mx, my, rx + 1.5, ry + 1, deg), fill=(40, 26, 14))                         # 송진 이음매(짙은 선)
    disc = ell(mx, my, rx - 1, ry - 1, deg)
    d.polygon(disc, fill=(168, 122, 74))
    ca, sa = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    from PIL import Image as _I
    mask = _I.new("L", im.size, 0); ImageDraw.Draw(mask).polygon(disc, fill=255)
    grain = im.copy(); g = ImageDraw.Draw(grain)
    for k, c, w in ((-26, 150, 1), (-19, 138, 2), (-9, 146, 1), (-4, 132, 2), (7, 144, 1), (13, 136, 2), (24, 148, 1)):  # 곧은 나뭇결(간격·짙기 불규칙)
        pts = [(mx + t * ca - (k + 2 * math.sin(t / 23)) * sa, my + t * sa + (k + 2 * math.sin(t / 23)) * ca) for t in range(-rx, rx + 1, 4)]
        g.line(pts, fill=(c, c - 42, c - 82), width=w)
    im.paste(grain, (0, 0), mask)
    im.save(os.path.join(D, "fix-src.png"))


def redraw():
    import run_scene, prop_sheet as P
    os.chdir(CANON)
    prompt = (f"{P.STYLE} A single object drawn alone on plain warm cream paper, with nothing else: {P.look('oil-horn')}, "
              "lying on its side, its wide opening at the upper left sealed flush with a flat fitted wooden disc set level with the rim, straight wood grain and a thin dark resin seam around it, the body sagging into a gentle curve "
              "and rising to the right, its narrow tip cut off square with a tiny drilled hole in the dark horn. No hands, no people, no background, no text.")
    jobs = [{"prompt": prompt, "seed": 5, "w": 1216, "h": 640, "src": os.path.join(D, "fix-src.png"), "strength": s,
             "out": os.path.join(D, f"fix-{s}.png")} for s in (0.2, 0.25)]
    tmp = os.path.expanduser("~/.local/biblemap-imggen/prop-oil-horn-lying"); os.makedirs(tmp, exist_ok=True)
    print("[HornSheetFix]", run_scene.gen_zimage(jobs, tmp, "i2i"))

{"compose": compose, "redraw": redraw}[sys.argv[1]]()
