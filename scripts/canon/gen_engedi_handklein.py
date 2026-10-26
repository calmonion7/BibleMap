#!/usr/bin/env python3
"""엔게디 손 국소 수정 r5 — Z-Image 인페인트(r1~r4b)는 「칼날이 천을 가름」을 못 그려(칼을 말하면 큰 칼, 빼면 칼이 사라짐),
지시형 편집 FLUX.2-klein-4B(mflux)로 손 부위만 고친다. 손 부위 320 정사각 크롭 → 1024로 편집 → 손 둘레 타원 마스크 안쪽만 되붙임.
  python3 gen_engedi_handklein.py     # 출발 그림 × 시드(이미 있으면 건너뜀). mflux CLI를 한 장씩 부른다(별도 프로세스 — 메모리 반환)."""
import os, subprocess

from PIL import Image, ImageDraw, ImageFilter

import gen_engedi_handfix as H
from gen_face_ab_klein import MFLUX

R = "r5"
# 출발 그림(OUT 기준) → 손 부위 크롭 좌상단(320 정사각, 1216×640 안)
START = {"B11": ("r2/B11-st0.75-i2.png", (280, 320)), "B202": ("r2/B202-st0.85-i2.png", (310, 320))}
SIDE, EDIT = 320, 1024
SEEDS = (1, 2, 3)
PROMPT = ("Edit only the two hands of the kneeling man on the left and the cloth between them. His one hand lifts the corner of the "
          "dark brown wool cloak off the ground. His other hand holds a very small plain ancient knife with a wooden handle and no "
          "guard, the blade only as long as a finger, and the blade is slicing straight through the lifted cloth so that a clean "
          "fresh cut is clearly visible and the corner is coming off. Keep everything else exactly the same: same arms, legs, "
          "lighting and the same soft pencil and colored-pencil illustration style.")


def mask(box_hand):
    """크롭 안 손·칼 상자 둘레 타원(번짐) — 마스크 밖은 원본 그대로."""
    m = Image.new("L", (SIDE, SIDE), 0)
    x0, y0, x1, y1 = box_hand
    ImageDraw.Draw(m).ellipse([x0 - 25, y0 - 25, x1 + 25, y1 + 25], fill=255)
    return m.filter(ImageFilter.GaussianBlur(10))


if __name__ == "__main__":
    os.makedirs(os.path.join(H.OUT, R), exist_ok=True)
    for name, (start, (l, t)) in START.items():
        base = Image.open(os.path.join(H.OUT, start)).convert("RGB")
        src = os.path.join(H.OUT, R, f"{name}-crop.png")
        base.crop((l, t, l + SIDE, t + SIDE)).resize((EDIT, EDIT), Image.LANCZOS).save(src)
        bx = H.BOX[int(name[1:])]
        m = mask((bx[0] - l, bx[1] - t, bx[2] - l, bx[3] - t))
        for s in SEEDS:
            raw, out = os.path.join(H.OUT, R, f"{name}-s{s}-edit.png"), os.path.join(H.OUT, R, f"{name}-s{s}.png")
            if not os.path.exists(raw):
                subprocess.run([MFLUX, "--model", "flux2-klein-4b", "-q", "8", "--image-paths", src, "--prompt", PROMPT, "--seed", str(s),
                                "--steps", "4", "--width", str(EDIT), "--height", str(EDIT), "--output", raw], check=False,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if os.path.exists(raw) and not os.path.exists(out):
                layer, mm = Image.new("RGB", base.size), Image.new("L", base.size, 0)
                layer.paste(Image.open(raw).convert("RGB").resize((SIDE, SIDE), Image.LANCZOS), (l, t))
                mm.paste(m, (l, t))
                Image.composite(layer, base, mm).save(out)
                print("[EngediHandklein] 저장", os.path.basename(out), flush=True)
