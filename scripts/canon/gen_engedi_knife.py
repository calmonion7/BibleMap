#!/usr/bin/env python3
"""엔게디 C s23(사용자 채택, 2026-10-18) 칼만 고치기 — 사용자: 「칼이 정확히 표현안되」.
s23의 칼은 손보다 긴 검은 단검이 들린 자락 앞을 가로지를 뿐 천에 들어가지 않는다. klein 지시 편집으로 칼 부위만 고친다
(손·칼 부위 크롭 → 1024 편집 → 칼 둘레 타원 마스크 안쪽만 되붙임 — gen_engedi_handklein.py 틀).
  python3 gen_engedi_knife.py      # 문구 K1·K2 × 시드(이미 있으면 건너뜀)
되붙이기 전에 편집 크롭의 색을 원본 크롭의 채널별 평균·표준편차에 맞춘다(klein 편집이 천을 푸르게 띄움, 2026-10-18 실측)."""
import os, subprocess

from PIL import Image, ImageDraw, ImageFilter

from gen_face_ab_klein import MFLUX

SRC = os.path.expanduser("~/.local/biblemap-imggen/engedi-aftercut/C/s23.png")
OUT = os.path.expanduser("~/.local/biblemap-imggen/engedi-knife")
L, T, SIDE, EDIT = 380, 320, 280, 1024
KNIFE_BOX = (440, 440, 570, 500)    # 칼·칼 쥔 손·들린 자락 가운데(원본 좌표, 눈으로 잡음)
SEEDS = (1, 2, 3)
KEEP = ("Keep everything else exactly the same: the hand lifting the cloth, both arms, the cloth folds, the lighting and the same "
        "soft pencil and colored-pencil illustration style.")
PROMPTS = {
    "K1": ("Replace the long dark knife with a very small plain ancient knife with a short wooden handle and a short pale metal blade "
           "only as long as a finger. The blade is pushed into the lifted fold of the dark cloak: the tip is hidden inside the cloth and "
           "a short fresh slit is visible in the cloth along the blade. " + KEEP),
    "K2": ("The man's lower hand holds a tiny knife, its short pale blade only as long as a finger, and he is slicing the lifted edge "
           "of the dark wool cloak: the blade edge is in the cloth and the cloth is visibly cut open along the blade. Remove the long "
           "dark knife. " + KEEP),
}


def color_match(edit, ref):
    """채널별 평균·표준편차를 원본에 맞춤 — 편집이 남긴 색 어긋남(푸른 기)만 지운다."""
    import numpy as np
    e, r = np.asarray(edit, dtype=np.float32), np.asarray(ref, dtype=np.float32)
    e = (e - e.mean((0, 1))) / (e.std((0, 1)) + 1e-6) * r.std((0, 1)) + r.mean((0, 1))
    return Image.fromarray(e.clip(0, 255).astype("uint8"))


def mask():
    m = Image.new("L", (SIDE, SIDE), 0)
    x0, y0, x1, y1 = (v - o for v, o in zip(KNIFE_BOX, (L, T, L, T)))
    ImageDraw.Draw(m).ellipse([x0 - 20, y0 - 20, x1 + 20, y1 + 20], fill=255)
    return m.filter(ImageFilter.GaussianBlur(8))


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    base = Image.open(SRC).convert("RGB")
    src = os.path.join(OUT, "crop.png")
    base.crop((L, T, L + SIDE, T + SIDE)).resize((EDIT, EDIT), Image.LANCZOS).save(src)
    m = mask()
    for k, prompt in PROMPTS.items():
        for s in SEEDS:
            raw, out = os.path.join(OUT, f"{k}-s{s}-edit.png"), os.path.join(OUT, f"{k}-s{s}.png")
            if not os.path.exists(raw):
                subprocess.run([MFLUX, "--model", "flux2-klein-4b", "-q", "8", "--image-paths", src, "--prompt", prompt, "--seed", str(s),
                                "--steps", "4", "--width", str(EDIT), "--height", str(EDIT), "--output", raw], check=False,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if os.path.exists(raw) and not os.path.exists(out):
                layer, mm = Image.new("RGB", base.size), Image.new("L", base.size, 0)
                edit = Image.open(raw).convert("RGB").resize((SIDE, SIDE), Image.LANCZOS)
                layer.paste(color_match(edit, base.crop((L, T, L + SIDE, T + SIDE))), (L, T))
                mm.paste(m, (L, T))
                Image.composite(layer, base, mm).save(out)
                print("[EngediKnife] 저장", os.path.basename(out), flush=True)
