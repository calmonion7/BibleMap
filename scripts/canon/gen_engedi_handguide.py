#!/usr/bin/env python3
"""엔게디 손 국소 수정 r4 — 문구만으로는 「칼날이 천을 가름」이 안 그려져(r3), 손 부위에 동작 뼈대를 직접 그려 넣고 낮은 강도로 다시 그린다.
  VENV=~/.local/biblemap-imggen/.venv314/bin/python
  $VENV gen_engedi_handfix.py enc    # (r3 P1 임베딩을 그대로 씀 — 먼저 한 번)
  $VENV gen_engedi_handguide.py      # 뼈대 그림 guide-B11.png + 강도 × 시드
출발 = r2 s11(손이 이미 갈림). 뼈대: 긴 칼날을 천 색으로 지우고 손가락 길이 칼날 → 칼끝에서 오른손이 쥔 자락을 가로지르는 밝은 틈(베인 선)·벌어진 귀퉁이.
좌표는 1216×640 원본 기준, 눈으로 잡음(notes/ENGEDI-HANDFIX.md r4)."""
import os

from PIL import Image, ImageDraw, ImageFilter

import gen_engedi_handfix as H

R = "r4b"   # r4 = P1·강도 0.45/0.55(뼈대 무시, 긴 칼로 덮음) → r4b = 칼 없는 P3·강도 0.3/0.38
START = "r2/B11-st0.75-i2.png"
BOX = (380, 460, 520, 545)
STRENGTHS = (0.3, 0.38)
CLOTH, BLADE, EDGE, GAP = (42, 33, 27), (196, 190, 176), (70, 62, 55), (150, 120, 86)


def guide(im):
    g = im.copy()
    d = ImageDraw.Draw(g)
    d.polygon([(440, 498), (497, 512), (497, 528), (440, 516)], fill=CLOTH)          # 긴 칼날 지움
    d.polygon([(441, 503), (462, 509), (464, 512), (441, 509)], fill=BLADE, outline=EDGE)   # 손가락 길이 칼날
    d.polygon([(462, 496), (500, 490), (512, 532), (470, 538)], fill=CLOTH)          # 오른손이 들어 올린 자락
    d.line([(463, 510), (476, 520), (490, 534)], fill=GAP, width=3)                  # 칼끝에서 이어지는 베인 틈
    d.polygon([(476, 520), (490, 534), (498, 538), (484, 522)], fill=GAP)            # 벌어진 귀퉁이 사이로 보이는 땅
    return Image.blend(im, g.filter(ImageFilter.GaussianBlur(0.8)), 0.9)


if __name__ == "__main__":
    import torch
    torch.set_grad_enabled(False)
    os.makedirs(os.path.join(H.OUT, R), exist_ok=True)
    g = guide(Image.open(os.path.join(H.OUT, START)).convert("RGB"))
    g.save(os.path.join(H.OUT, R, "guide-B11.png"))
    crop, mask, (l, t, side) = H.crop_mask(g, BOX)
    pipe = H.load_pipe()
    e = [x.to("mps", torch.bfloat16) for x in torch.load(H.EMB.format("P3"))]
    for st in STRENGTHS:
        for i in H.SEEDS:
            out = os.path.join(H.OUT, R, f"B11-st{st}-i{i}.png")
            if os.path.exists(out):
                continue
            new = pipe(prompt_embeds=e, image=crop, mask_image=mask, strength=st, height=768, width=768, num_inference_steps=9,
                       guidance_scale=0.0, generator=torch.Generator("mps").manual_seed(i)).images[0]
            layer, mm = Image.new("RGB", g.size), Image.new("L", g.size, 0)
            layer.paste(new.resize((side, side), Image.LANCZOS), (l, t))
            mm.paste(mask.resize((side, side), Image.LANCZOS), (l, t))
            Image.composite(layer, g, mm).save(out)
            print("[EngediHandguide] 저장", os.path.basename(out), flush=True)
