"""비늘 질감 앵커를 **목표 화풍 맥락 안에서** 파생한다 (2026-08-28, 라운드 8 ㉯).

**왜 새로 만드는가.** 현행 앵커 `ref-scale-texture.png`(660x870)는 몸통을 **크롭**한 것이고
ink **.8793** — 정답지 구간(.1024~.2213)의 4배다. 그 앵커로 뽑은 `samples/goliath.png`는
ink **.6377**로, 다윗 표본(.0986)과 화풍이 6.5배 어긋난다(SAMPLES.md 「남은 미달」 1).
`ZIMAGE.md` §9-10이 사람 판정과 맞물려 확정한 것: 그 표본이 part 3의 반사실 화풍의 뿌리다.

같은 원본에서 파생한 `ref-scale-armor-clean.png`는 ink **.1583으로 구간 안**이다 — 차이는
**종이 맥락을 지녔다는 것 하나**다(`make_armor_ref.py`가 캔버스를 유지하고 인물 기둥 밖만 종이색으로
덮었다). 그런데 그 앵커는 인물 기둥 안에 **화살통·망토·창**을 남겨 지물을 실어 왔다. 그래서
질감 크롭으로 옮겨 갔고, 그 순간 종이 맥락이 사라져 화풍이 깨졌다.

**이 스크립트가 하는 것: 내용은 비늘만, 맥락은 종이.** 지물을 전부 벗어나는 몸통 비늘 상자만
종이색 **정사각** 캔버스에 얹는다. 정사각인 이유는 `gen_sample.py --ref`가 레터박스를 하지 않고
그대로 넘기는데, 상류 `CLIPImageProcessor`가 `resize(shortest_edge=224)+center_crop(224)`를
강제하기 때문이다(task#319 발견 1) — 정사각이면 인코더가 앵커 전체를 본다.

**좌표는 격자 오버레이로 눈으로 읽었다**(원본 1408x768, `make_armor_ref.py`와 같은 방법):
투구+뿔 y10~110 · 화살통 x800~880 · 창 x940~1020 · 대검 x360~540 · 맨팔 x<600·x>780 ·
전장 바닥 y>490. 몸통 비늘(가슴 비늘 + 비늘 치마)은 **x605~775 · y195~485**로, 그 전부를 벗어난다.

**점유율은 임계가 아니라 쓸기다.** 인코더 시야에서 비늘이 차지하는 비율이 「질감 전이 세기」와
「화풍 끌림」을 동시에 정하는 유일한 손잡이여서, 값을 손으로 못박지 않고 3단으로 뽑아 **산출물의
ink가 정답지 구간에 드는지 + 비늘이 실제로 나오는지**로 고른다(ADR `260825-013557`의 태도).

Usage: VENV/python make_scale_anchor.py   → ref-scale-onpaper-f{35,55,75}.png
"""
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
CANON = os.path.dirname(HERE)
sys.path.insert(0, CANON)
import params  # noqa: E402

SRC = os.path.join(HERE, "ref-scale-armor.png")
SHEET = os.path.join(params.REFERENCE, "sheet-s200.png")
TORSO_BOX = (635, 195, 770, 485)   # 눈으로 읽은 몸통 비늘 상자 — 지물·맨팔·투구·바닥을 전부 벗어난다.
                                   # x를 605→635, 775→770으로 조였다: 왼쪽 28열에 파란 **망토**가 10~17%(팔과 몸통
                                   # 사이로 보인다), 오른쪽 25열에 **맨팔** 살색이 5~15% 있었다. 망토는 SAMPLES.md가
                                   # 기록한 재발 결함이라 앵커에서 그 시각 단서를 지운다(부정어는 무력했다 — 규칙 9).
FRACTIONS = (0.35, 0.55, 0.75)     # 인코더 시야 세로 점유율 — 쓸기(위 docstring)
SIDE = params.PERSON_SIZE[0]       # 정사각 변 — 프로젝트 상수를 승계한다(새 숫자를 만들지 않는다)


def paper_color():
    """종이색을 **정답지에서 파생한다** — 임의 색을 쓰지 않는다(`make_armor_ref.py`와 같은 규약)."""
    sheet = np.asarray(Image.open(SHEET).convert("RGB"))
    return tuple(int(v) for v in np.median(sheet[:40, :40].reshape(-1, 3), axis=0))


def main():
    if not os.path.exists(SRC):
        sys.exit(f"원본이 없다: {SRC}")
    src = Image.open(SRC).convert("RGB")
    patch = src.crop(TORSO_BOX)
    paper = paper_color()
    print(f"종이색(정답지 파생) = {paper}  ·  비늘 상자 {TORSO_BOX} = {patch.size}  ·  캔버스 {SIDE}x{SIDE}")

    for f in FRACTIONS:
        h = int(SIDE * f)
        w = max(1, round(patch.width * h / patch.height))
        out = Image.new("RGB", (SIDE, SIDE), paper)
        out.paste(patch.resize((w, h), Image.LANCZOS), ((SIDE - w) // 2, (SIDE - h) // 2))
        dst = os.path.join(HERE, f"ref-scale-onpaper-f{int(f * 100)}.png")
        out.save(dst)
        area = (w * h) / (SIDE * SIDE)
        print(f"  f={f:.2f}  패치 {w}x{h}  시야 면적 {area:.1%}  -> {os.path.basename(dst)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
