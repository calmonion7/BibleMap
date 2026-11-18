"""task 656 — 정본 s5에 잘린 끝·입구 마개를 칠하고 같은 생성기로 약하게 다시 그림(사람 655 「뾰족한 끝이 잘려 있어야 … 입구에는 마개」)."""
import os, sys
CANON = "/Users/calmonion/Project/BibleMap/scripts/canon"
sys.path.insert(0, CANON); sys.path.insert(0, os.path.join(CANON, "batch"))
from PIL import Image, ImageDraw
D = os.path.join(CANON, "samples", "prop-oil-horn-lying")

def compose():
    import cv2, numpy as np
    im = Image.open(os.path.join(D, "sheet-s5.png")).convert("RGB")
    mask = Image.new("L", im.size, 0); ImageDraw.Draw(mask).rectangle([917, 205, 1000, 300], fill=255)   # 끝 바깥을 종이로
    im = Image.fromarray(cv2.inpaint(np.array(im)[:, :, ::-1], np.array(mask), 9, cv2.INPAINT_TELEA)[:, :, ::-1])
    d = ImageDraw.Draw(im)
    d.ellipse([907, 236, 925, 274], fill=(196, 160, 110), outline=(70, 45, 25), width=2)   # 잘린 면
    d.ellipse([912, 250, 920, 260], fill=(40, 25, 15))                                    # 주둥이 구멍
    d.ellipse([292, 207, 412, 262], fill=(128, 84, 46), outline=(70, 45, 25), width=3)    # 입구에 꼭 맞는 나무 마개
    d.ellipse([310, 214, 380, 240], fill=(156, 108, 62))                                  # 마개 윗면 밝은 결
    im.save(os.path.join(D, "fix-src.png"))

def redraw():
    import run_scene, prop_sheet as P
    os.chdir(CANON)
    prompt = (f"{P.STYLE} A single object drawn alone on plain warm cream paper, with nothing else: {P.look('oil-horn')}, "
              "lying on its side, its wide opening at the upper left closed by a fitted round wooden stopper, the body sagging into a gentle curve "
              "and rising to the right, its tip cut off flat with a small hole. No hands, no people, no background, no text.")
    jobs = [{"prompt": prompt, "seed": 5, "w": 1216, "h": 640, "src": os.path.join(D, "fix-src.png"), "strength": s,
             "out": os.path.join(D, f"fix-{s}.png")} for s in (0.25, 0.35)]
    tmp = os.path.expanduser("~/.local/biblemap-imggen/prop-oil-horn-lying"); os.makedirs(tmp, exist_ok=True)
    print("[HornSheetFix]", run_scene.gen_zimage(jobs, tmp, "i2i"))

{"compose": compose, "redraw": redraw}[sys.argv[1]]()
