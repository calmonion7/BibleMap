"""task 718 — 성전 봉헌: 고른 바탕에 klein 편집을 차례로(놋단 넣기 · 단상을 꾸밈 없는 청동으로) 하고, 편집 상자 안의 앞 인물은 원본 화소로 되살린다.

생성기는 청동 물건 둘(놋 단상·놋단)을 하나로 합친다(711~717) — 놋단은 고른 장에 따로 넣는다(skill 함정).
klein은 글로 준 너비를 따르지 않는다 — 넓이는 칠한 네모(paint)로 준다(718 r3 k9~k12).
지시문에 사람을 넣으면(「behind the kneeling man」) 사람이 하나 더 생긴다(718 r3 k1~k4).

쓰는 법: python3 batch/temple_altar_edit.py <설정.json> <출력 폴더> [klein 시드 …]
설정 = {"base": 바탕 경로, "steps": [{"name", "crop": [L, T, 한 변], "box": [x0, y0, x1, y1], "paint": [[x0, y0, x1, y1], [r, g, b]] | null,
        "prompt", "keep": [[x0, y0, x1, y1], …], "keep_seeds": [[x, y], …], "keep_blue_rows": [y0, y1] | null}]}
단계마다 앞 단계 결과를 바탕으로 쓴다(같은 klein 시드). keep = 원본에서 되살릴 앞 인물 범위(밝은 벽·하늘·돌바닥이 아닌 화소 중 keep_seeds에 이어진 덩어리).
"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageFilter

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import gen_local_edit as gle  # noqa: E402


def keep_mask(base, st):
    """원본에서 앞 인물 화소 → L 마스크. 밝고 옅은 화소(밝기 > 178 · 붉은기 r-b < 75)는 뺌."""
    from scipy import ndimage
    a = np.asarray(base).astype(int)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    fg = ~(((r + g + b) / 3 > 178) & (r - b < 75))
    if st.get("keep_blue_rows"):   # 뒷담 갓돌처럼 인물 몸통이 지나는 가로 줄은 청색 옷만(718 s101)
        y0, y1 = st["keep_blue_rows"]
        fg[y0:y1] &= (b > r)[y0:y1]
    m = np.zeros(fg.shape, bool)
    for x0, y0, x1, y1 in st["keep"]:
        m[y0:y1, x0:x1] = fg[y0:y1, x0:x1]
    lab, _ = ndimage.label(m)
    m = np.isin(lab, [lab[y, x] for x, y in st["keep_seeds"] if lab[y, x]])
    img = Image.fromarray((m * 255).astype("uint8"))
    return img.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(1))


def main():
    cfg, out_dir = json.load(open(sys.argv[1], encoding="utf-8")), sys.argv[2]
    seeds = [int(s) for s in sys.argv[3:]] or [1, 2, 3, 4]
    os.makedirs(out_dir, exist_ok=True)
    orig = Image.open(cfg["base"]).convert("RGB")
    for k in seeds:
        src = cfg["base"]
        for st in cfg["steps"]:
            raw = os.path.join(out_dir, f"{st['name']}-klein-s{k}.png")
            paint = tuple(map(tuple, st["paint"])) if st.get("paint") else False
            if st.get("polys"):   # 원근대로 칠한 다각형(앞면·물러나는 옆면 — 7191 사람 「원근감」) — 칠한 사본을 klein 바탕으로
                from PIL import ImageDraw
                pimg = Image.open(src).convert("RGB")
                for pts, rgb in st["polys"]:
                    ImageDraw.Draw(pimg).polygon([tuple(p) for p in pts], fill=tuple(rgb))
                src = os.path.join(out_dir, f"{st['name']}-paint-s{k}.png")
                pimg.save(src)
            r = gle.edit(src, tuple(st["crop"]), tuple(st["box"]), None, k, raw, prompt=st["prompt"], mask_shape="rect", guide=paint)
            if r["status"] != "ok":
                print(f"[TempleAltar] {st['name']} s{k} 실패", flush=True)
                break
            out = os.path.join(out_dir, f"{st['name']}-s{k}.png")
            img = Image.open(raw).convert("RGB")
            if st.get("keep"):
                km = keep_mask(orig, st)
                km.save(os.path.join(out_dir, f"{st['name']}-keep.png"))
                img = Image.composite(orig, img, km)
            img.save(out)
            src = out
            print(f"[TempleAltar] {st['name']} s{k} {r['sec']}s", flush=True)


if __name__ == "__main__":
    main()
