"""task 679 — 사람 678 「더 밝아야 될것 같음」: klein 편집은 color_match로 다시 그린 부분 색을 주변에 맞춰 금빛이 눌림 → 기름 줄기 화소만 골라 밝은 금빛 쪽으로 끌어올림.
  python3 batch/oil_brighten.py <그림> <x0,y0,x1,y1> <세기 0~1> <출력>"""
import sys
import numpy as np
from PIL import Image, ImageFilter
src, box, k, out = sys.argv[1], [int(v) for v in sys.argv[2].split(",")], float(sys.argv[3]), sys.argv[4]
im = Image.open(src).convert("RGB"); a = np.asarray(im).astype(float)
x0, y0, x1, y1 = box
c = a[y0:y1, x0:x1]
r, g, b = c[:, :, 0], c[:, :, 1], c[:, :, 2]
m = ((r - b > 55) & (g - b > 25) & (r > 110)).astype(float)                       # 금빛(뿔 갈색은 g-b가 작고 r가 낮음)
m = np.asarray(Image.fromarray((m * 255).astype("uint8")).filter(ImageFilter.GaussianBlur(0.7))).astype(float) / 255 * k
gold = np.array([255, 214, 52.0])
lum = c.mean(2, keepdims=True) / 255
tgt = gold * (0.75 + 0.35 * lum)                                                  # 원래 밝기 결은 남김(윤기)
c2 = c * (1 - m[..., None]) + np.clip(tgt, 0, 255) * m[..., None]
a[y0:y1, x0:x1] = c2
Image.fromarray(a.clip(0, 255).astype("uint8")).save(out); print("[OilBrighten]", out, int((m > 0.3 * k).sum()), "화소")
