"""task 656 — 정본 s5에 잘린 끝·입구 마개를 칠하고 같은 생성기로 약하게 다시 그림(사람 655 「뾰족한 끝이 잘려 있어야 … 입구에는 마개」)."""
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
    d.rectangle([908, 196, 1010, 300], fill=paper)                        # 끝 바깥을 종이색으로(둘레 화소 메움은 그림자 얼룩 — 656)
    def ell(cx, cy, rx, ry, deg, n=48):
        a = math.radians(deg)
        return [(cx + rx * math.cos(t) * math.cos(a) - ry * math.sin(t) * math.sin(a),
                 cy + rx * math.cos(t) * math.sin(a) + ry * math.sin(t) * math.cos(a)) for t in (2 * math.pi * i / n for i in range(n))]
    d.polygon(ell(908, 252, 13, 25, -20), fill=(205, 170, 120), outline=(60, 38, 20))   # 잘린 면(보는 쪽으로 조금 돌림)
    d.polygon(ell(909, 252, 6, 12, -20), fill=(25, 15, 8))                                # 크고 짙은 주둥이 구멍(사람 656 「구멍 뚫는데 잘보이게」)
    d.polygon(ell(352, 234, 80, 34, -11), fill=(122, 80, 44), outline=(64, 40, 22))      # 입구 안쪽 타원을 꽉 채운 마개(사람 656 「마개는 입구에 맞게」)
    d.polygon(ell(345, 228, 52, 18, -11), fill=(150, 104, 60))                           # 마개 윗면 결
    im.save(os.path.join(D, "fix-src.png"))


def redraw():
    import run_scene, prop_sheet as P
    os.chdir(CANON)
    prompt = (f"{P.STYLE} A single object drawn alone on plain warm cream paper, with nothing else: {P.look('oil-horn')}, "
              "lying on its side, its wide opening at the upper left closed by a fitted round wooden stopper, the body sagging into a gentle curve "
              "and rising to the right, its tip cut off flat with a small hole. No hands, no people, no background, no text.")
    jobs = [{"prompt": prompt, "seed": 5, "w": 1216, "h": 640, "src": os.path.join(D, "fix-src.png"), "strength": s,
             "out": os.path.join(D, f"fix-{s}.png")} for s in (0.2, 0.25)]
    tmp = os.path.expanduser("~/.local/biblemap-imggen/prop-oil-horn-lying"); os.makedirs(tmp, exist_ok=True)
    print("[HornSheetFix]", run_scene.gen_zimage(jobs, tmp, "i2i"))

{"compose": compose, "redraw": redraw}[sys.argv[1]]()
