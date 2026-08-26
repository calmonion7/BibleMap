"""[[전신 표본]] 동결 — 후보에서 고른 1장을 인물에 조밀하게 잘라 `samples/`에 동결한다 (task#319 S4).

`freeze_faces.py`(얼굴 동결, 정본 2층 구 정의)의 자리 관례를 따르되, 자르는 방식이 다르다.

**왜 자르는가 — 세 가지가 동시에 해결된다(전부 2026-08-26 실측 근거).**
 1. **지물 제거.** 골리앗 후보는 창·방패를 좌우 **바깥**에 들고 나온다. 지물 제거용 부정어는 이
    파이프라인에서 반복적으로 무력했다(표본 5회·시트 4회·앵커 2회 전부 실패 — PROMPTING.md 8).
    인물 기둥으로 자르면 그 지물이 프레임 밖으로 나간다. 특히 **방패는 골리앗의 지물이 아니다**
    (삼상 17:7 「방패 든 자는 앞서 행하더라」 — notes/PROCESS.md §3-b Q0-b).
 2. **인코더가 인물을 채운다.** IP-Adapter 상류가 `resize(shortest_edge=224)+center_crop(224)`이라
    인물이 정사각을 못 채우면 신호가 희석된다(task#319 발견 1: 정사각 레터박스에서 ink .0820으로
    하한 미달). 조밀 크롭이 그 희석을 없앤다.
 3. **축 A가 구간 쪽으로 올라간다.** 다윗 실측: 원본 전역 ink .0440 → 인물 조밀 크롭 .1504
    (정답지 구간 .1024~.2213 안). 단독 인물은 `reference/REFERENCE.md`상 축 A **적용 범주 밖**이므로
    이것은 게이트가 아니라 **참고 수치**다 — 임계를 만지려는 것이 아니다.

**bbox는 손으로 찍지 않는다.** 행·열별 「어두운 화소(lum < judge_style.DARK_CUT)」 개수 프로파일에서
파생한다 — 배경 비네팅에 강하다(단순 배경색 차이 마스크는 비네팅을 인물로 잡아 bbox가 화면 전체가
됐다, 2026-08-26 실측).

Usage: VENV .../python freeze_samples.py david <src.png> [--pad 12]
"""
import argparse
import os
import sys

import numpy as np
from PIL import Image

import params

sys.path.insert(0, params.CANON_DIR)
import judge_style  # noqa: E402

OUT = os.path.join(params.CANON_DIR, "samples")


def figure_bbox(im, frac=0.04):
    """행·열 프로파일 기반 자동 bbox — **골리앗류에는 쓸 수 없다.** 근거를 남긴다:
    좌우 바깥의 지물(창·방패)도 어두운 화소여서 min/max가 함께 품고(실측 x 47~786), 지물이 손에
    이어져 있어 「배경 틈에서 멈추는」 확장도 통하지 않으며, 배경 비네팅이 최댓값 열로 잡히면
    다윗에서 86px로 붕괴했다(실측). 그래서 **박스는 `--box`로 명시**하고 근거는 samples/SAMPLES.md가
    진다 — `make_masks.py`의 `BBOX_RATIONALE` 선례와 같은 처리다(단순한 선택 + 문서화된 근거).
    이 함수는 배경이 깨끗하고 지물이 없는 경우(다윗류)의 보조 수단으로만 남긴다.
    """
    lum = np.asarray(im.convert("L"), dtype=np.float32) / 255.0
    dark = lum < judge_style.DARK_CUT
    h, w = dark.shape
    rows = np.where(dark.sum(axis=1) > max(3, frac * w))[0]
    cols = np.where(dark.sum(axis=0) > max(3, frac * h))[0]
    if not len(rows) or not len(cols):
        sys.exit("어두운 화소로 인물을 못 찾았다")
    return int(cols.min()), int(rows.min()), int(cols.max()), int(rows.max())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("name", choices=["david", "goliath"])
    ap.add_argument("src")
    ap.add_argument("--pad", type=int, default=12, help="자동 bbox일 때의 여백(px)")
    ap.add_argument("--box", default=None,
                    help="x0,y0,x1,y1 — 명시 박스(지물이 좌우에 있는 경우. 근거는 SAMPLES.md)")
    a = ap.parse_args()

    if not os.path.exists(a.src):
        sys.exit(f"원본이 없다: {a.src}")
    im = Image.open(a.src).convert("RGB")
    w, h = im.size
    if a.box:
        x0, y0, x1, y1 = (int(v) for v in a.box.split(","))
        box = (max(0, x0), max(0, y0), min(w, x1), min(h, y1))
    else:
        x0, y0, x1, y1 = figure_bbox(im)
        box = (max(0, x0 - a.pad), max(0, y0 - a.pad),
               min(w, x1 + a.pad), min(h, y1 + a.pad))
    cut = im.crop(box)

    os.makedirs(OUT, exist_ok=True)
    dst = os.path.join(OUT, f"{a.name}.png")
    cut.save(dst)

    before = judge_style.style_metrics(a.src)["ink"]
    after = judge_style.style_metrics(dst)["ink"]
    print(f"{a.name}: {os.path.basename(a.src)} {im.size} → bbox {box} → {cut.size}")
    print(f"  전역 ink {before:.4f} → 조밀 크롭 {after:.4f} (참고 수치 — 단독 인물은 축 A 범주 밖)")
    print(f"-> {dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
