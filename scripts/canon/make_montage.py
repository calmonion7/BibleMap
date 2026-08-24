"""task#314 S4 4단계 — 후보 10장을 대조표 3장으로 묶는다: 다윗 4칸 · 골리앗 4칸 · 배경 어휘 대조 2칸
(plan.md 원안의 "3장"은 인물2x4+배경1x4였으나, S3가 배경 정본을 두지 않기로 정해 배경 축이
"어휘 유/무 대조 2칸"으로 바뀌었다 — BACKGROUND.md §6). 칸마다 (대상·시드)를 각인하고, 시트 크기를
상수에서 재계산해 기계로 검산한다(storyboard-density/make_montage.py와 같은 패턴).
"""
import glob
import os
import re
import sys

from PIL import Image, ImageDraw, ImageFont

import params

GEN = os.path.join(params.OUT_ROOT, "gen")

LABEL_H, GAP, TITLE_H = 20, 6, 26
PERSON_CELL = (320, 320)   # 1024x1024 후보 — 표시용 축소
BG_CELL = (480, 252)       # 1216x640 후보(x0.395) — 장면 비율 유지


def font(sz):
    # 한글 제목이 두부(□)로 깨지지 않게 한글 글리프가 있는 폰트를 먼저 본다(task#314 검산).
    for p in ("/System/Library/Fonts/AppleSDGothicNeo.ttc",
              "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
              "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
              "/System/Library/Fonts/Supplemental/Arial.ttf"):
        if os.path.exists(p):
            return ImageFont.truetype(p, sz)
    return ImageFont.load_default()


def seeds_for(target):
    paths = sorted(glob.glob(os.path.join(GEN, f"{target}-s*.png")))
    out = []
    for p in paths:
        m = re.search(rf"{re.escape(target)}-s(\d+)\.png$", p)
        if m:
            out.append((int(m.group(1)), p))
    return sorted(out)


def person_sheet(target, cell_w, cell_h, cols=2):
    items = seeds_for(target)
    if not items:
        sys.exit(f"{target}: 생성물이 없다 — gen_candidates.py를 먼저 돌려라")
    rows = (len(items) + cols - 1) // cols
    sheet_w = cols * cell_w + (cols - 1) * GAP
    sheet_h = TITLE_H + rows * (LABEL_H + cell_h) + (rows - 1) * GAP
    sheet = Image.new("RGB", (sheet_w, sheet_h), (255, 255, 255))
    dr = ImageDraw.Draw(sheet)
    dr.text((4, 5), f"{target}  후보 {len(items)}장(시드별)", fill=(0, 0, 0), font=font(15))
    for i, (seed, path) in enumerate(items):
        r, c = divmod(i, cols)
        x, y = c * (cell_w + GAP), TITLE_H + r * (LABEL_H + cell_h + GAP)
        dr.text((x + 3, y + 3), f"{target} · seed {seed}", fill=(0, 0, 0), font=font(13))
        im = Image.open(path).convert("RGB").resize((cell_w, cell_h), Image.LANCZOS)
        sheet.paste(im, (x, y + LABEL_H))
    out = os.path.join(params.OUT_ROOT, f"montage-{target}.png")
    sheet.save(out)
    expect = (sheet_w, sheet_h)
    assert sheet.size == expect, f"{target}: {sheet.size} != {expect}"
    print(f"{os.path.basename(out)}  {sheet.size}  칸 {len(items)}(규격 {expect})")
    return out, sheet.size


def bg_sheet(cell_w, cell_h):
    cells = []
    for target in ("bg-on", "bg-off"):
        items = seeds_for(target)
        if not items:
            sys.exit(f"{target}: 생성물이 없다 — gen_candidates.py를 먼저 돌려라")
        cells.append((target, *items[0]))  # 시드 1개(대조는 시드를 고정해야 변수가 갈리지 않는다)
    cols = len(cells)
    sheet_w = cols * cell_w + (cols - 1) * GAP
    sheet_h = TITLE_H + LABEL_H + cell_h
    sheet = Image.new("RGB", (sheet_w, sheet_h), (255, 255, 255))
    dr = ImageDraw.Draw(sheet)
    dr.text((4, 5), "배경 어휘 대조 — 같은 구조 조건·같은 시드, 어휘 있음/없음만 바꿈",
             fill=(0, 0, 0), font=font(15))
    for c, (label, seed, path) in enumerate(cells):
        x, y = c * (cell_w + GAP), TITLE_H
        dr.text((x + 3, y + 3), f"{label} · seed {seed}", fill=(0, 0, 0), font=font(13))
        im = Image.open(path).convert("RGB").resize((cell_w, cell_h), Image.LANCZOS)
        sheet.paste(im, (x, y + LABEL_H))
    out = os.path.join(params.OUT_ROOT, "montage-bgtest.png")
    sheet.save(out)
    expect = (sheet_w, sheet_h)
    assert sheet.size == expect, f"bgtest: {sheet.size} != {expect}"
    print(f"{os.path.basename(out)}  {sheet.size}  칸 {cols}(규격 {expect})")
    return out, sheet.size


def main():
    made = [
        person_sheet("david", *PERSON_CELL),
        person_sheet("goliath", *PERSON_CELL),
        bg_sheet(*BG_CELL),
    ]
    print(f"{len(made)}장 생성")
    return made


if __name__ == "__main__":
    main()
