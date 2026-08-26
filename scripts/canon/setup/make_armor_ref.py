"""사용자 제공 비늘갑옷 참고 이미지에서 **의상 앵커 전용** 레퍼런스를 파생한다 (2026-08-26).

**왜 필요한가.** 원본(`ref-scale-armor.png`, 사용자 제공 — 출처는 SETUP.md)은 비늘갑옷 앵커로는
성공했지만(7회째에 처음 비늘이 나왔다) 두 결함을 함께 실어 왔다:
  ① **창·방패·망토** — 특히 방패는 골리앗의 지물이 아니다(삼상 17:7 「방패 든 자는 앞서 행하더라」).
     지물 제거용 부정어는 이 파이프라인에서 반복적으로 무력했다(표본 5회·시트 4회·앵커 2회 전부 실패,
     PROMPTING.md 8) — 그래서 **부정어가 아니라 레퍼런스 쪽을 손댄다.**
  ② **유화 배경** — 골리앗 표본 ink .4356 ↔ 다윗 표본 .0440으로 화풍이 약 10배 어긋났다.
     배경(하늘·풍경·진영)을 목표 화풍의 미색 종이로 바꿔 그 기여를 없앤다.

**프레이밍은 유지한다 — 자르지 않는다.** IP-Adapter 상류가 `resize(shortest_edge=224)+center_crop(224)`
이므로 레퍼런스의 프레이밍이 산출물로 전이된다(task#319 발견 1). 좁게 자르면 전신이 흉상으로 바뀐
실측이 있다(시도 1). 그래서 캔버스 크기와 인물의 위치·크기를 그대로 두고 **인물 기둥 밖만** 덮는다.

좌표는 격자 오버레이로 눈으로 읽었다(원본 1408x768): 인물 기둥 x 545~880 · 검 x 250~560 ·
창 x 875~1030. 배경색은 다윗 정답지 시트의 종이 여백에서 표본 추출한다(임의 색을 쓰지 않는다).

Usage: VENV .../python make_armor_ref.py   → ref-scale-armor-clean.png
"""
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "ref-scale-armor.png")
DST = os.path.join(HERE, "ref-scale-armor-clean.png")
SHEET = os.path.join(os.path.dirname(HERE), "reference", "sheet-s200.png")
FIGURE_COLUMN = (545, 880)   # 눈으로 읽은 인물 기둥 x 범위(검과 창을 둘 다 벗어난다)


def main():
    if not os.path.exists(SRC):
        sys.exit(f"원본이 없다: {SRC}")
    src = Image.open(SRC).convert("RGB")
    w, h = src.size

    # 배경색 — 목표 화풍의 종이색을 정답지에서 파생한다(리터럴 색을 쓰지 않는다).
    sheet = np.asarray(Image.open(SHEET).convert("RGB"))
    paper = tuple(int(v) for v in np.median(sheet[:40, :40].reshape(-1, 3), axis=0))

    out = Image.new("RGB", (w, h), paper)
    x0, x1 = FIGURE_COLUMN
    out.paste(src.crop((x0, 0, x1, h)), (x0, 0))
    out.save(DST)

    col = (x1 - x0) / w
    print(f"종이색(정답지 파생) = {paper}")
    print(f"인물 기둥 x {x0}~{x1} ({col:.1%} 폭)만 남기고 나머지를 종이색으로 덮었다")
    print(f"캔버스 {w}x{h} 유지 — 프레이밍 전이를 지키기 위해 자르지 않았다")
    print(f"-> {DST}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
