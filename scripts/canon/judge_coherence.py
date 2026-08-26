"""영역 간 화풍 정합 — **한 그림 안에서** 배경·다윗·골리앗의 화풍 지표가 같은가(GPU 0).

**이 도구는 게이트가 아니다. 수치를 보고만 한다.** 축을 게이트에 추가하는 것은 체크 집합의
변경이고 그건 사람의 결정이다(`PROCESS.md` §7 관문 0). 여기서는 그 결정에 필요한 수치를 낸다.

## 왜 필요한가 — 축 A가 못 잡는 것

`PROMPTING.md` 구멍 4: 축 A는 **그림 전체의** 어두운 화소 비율을 잰다. 그래서 서로 다른 화풍이
영역별로 섞여 있어도 **가중평균이 구간에 들면 통과한다.** 2026-08-27 실측이 그 경로를 정확히 보여줬다:

    배경 ink .0001 · 다윗 영역 .0602 · 골리앗 영역 .4617  → 영역 간 **6330배**
    그런데 전체 ink는 .1110으로 정답지 구간(.1024~.2213) **안**이다 → 축 A 통과

그림은 「창백한 연필 소년 + 반사실적 판금 기사 + 거의 흰 배경」인데 자는 「화풍 도달」이라고 답한다.

## 무엇을 재는가

`judge_style.style_metrics`와 **같은 잉크 정의**(`DARK_CUT` 미만 화소 비율)를 영역별로 낸다 —
새 지표를 만들지 않는다. 영역은 콘티 마스크(`conti/mask_*.png`)와 그 여집합(배경)이다.

  · 영역별 ink
  · **최대/최소 비** — 1에 가까울수록 한 화풍이다
  · 각 인물 영역 ↔ 그 인물의 [[전신 표본]] ink 대조 — 표본의 화풍이 얼마나 실렸는지 보인다

**임계를 두지 않는다.** 어느 비율부터 「불일치」인지는 정답지에서 파생해야 하는데, 그 정답지
(한 그림 안의 화풍 일관성 기준)가 아직 없다. 지어내면 그게 결론 선취다(ADR `260823-221839`).

Usage: .../python judge_coherence.py <최종본.png> [...]
"""
import os
import sys

import numpy as np
from PIL import Image

import judge_s1
import judge_style as js
import params

SAMPLES = os.path.join(params.CANON_DIR, "samples")
PEOPLE = judge_s1.PEOPLE


def region_ink(path):
    """영역별 잉크 비율. 잉크 정의는 judge_style와 같다(DARK_CUT 미만 화소 비율)."""
    g = np.asarray(Image.open(path).convert("RGB").resize(params.SCENE_SIZE).convert("L"),
                   dtype=np.float32) / 255.0
    masks = {n: judge_s1._load_conti_mask(n) for n in PEOPLE}
    regions = {"background": ~(masks["david"] | masks["goliath"])}
    regions.update(masks)
    return {k: float((g[m] < js.DARK_CUT).mean()) for k, m in regions.items()}


def main():
    paths = [a for a in sys.argv[1:] if not a.startswith("-")]
    if not paths:
        sys.exit(__doc__.strip().splitlines()[-1])
    sample_ink = {n: js.style_metrics(os.path.join(SAMPLES, f"{n}.png"))["ink"]
                  for n in PEOPLE if os.path.exists(os.path.join(SAMPLES, f"{n}.png"))}
    for p in paths:
        r = region_ink(p)
        whole = js.style_metrics(p)["ink"]
        lo, hi = min(r.values()), max(r.values())
        print(f"\n{os.path.basename(p)}  (전체 ink {whole:.4f})")
        for k, v in r.items():
            extra = ""
            if k in sample_ink:
                extra = f"   ↔ {k} 표본 ink {sample_ink[k]:.4f}"
            print(f"  {k:12s} ink={v:.4f}{extra}")
        # **인물 대 인물이 의미 있는 수다.** 배경은 이 화풍에서 원래 거의 흰색이라(미색 종이)
        # 배경을 포함한 최대/최소 비는 항상 수천 배로 부풀고 그림끼리 구별을 못 한다.
        # 2026-08-27 실측: 장면 앵커 1.7배(두 인물 다 연필풍) ↔ 최종본 7.7~12.9배(한쪽만 반사실적).
        pv = [r[n] for n in PEOPLE if n in r]
        if len(pv) == 2:
            print(f"  **인물 간 비 = {max(pv) / max(min(pv), 1e-6):.1f}배** "
                  f"← 이것이 의미 있는 수다 (배경 포함 최대/최소 {hi / max(lo, 1e-6):.0f}배는 "
                  f"배경이 원래 거의 흰색이라 부푼 값이다)")
        print("  임계는 두지 않는다 — 파생할 정답지(한 그림 안의 화풍 일관성 기준)가 아직 없다")
    return 0


if __name__ == "__main__":
    sys.exit(main())
