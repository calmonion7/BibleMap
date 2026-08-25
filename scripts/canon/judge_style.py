"""[[화풍 도달]] 판정 — 축 A (task#317 S0-2).

**정답지는 지어내지 않는다.** 양성 기준은 사용자가 목표로 지정한 `params.REFERENCE`의 10장이고
(reference/REFERENCE.md), 음성 대조군은 현행 ControlNet 경로 산출물이다. 이 스크립트가 하는 일은
그 두 집합에 지표를 걸어 **분리도를 재고, 분리되면 그 사이에서 임계를 파생하는 것**이다 —
임계를 리터럴로 적지 않는다(ADR `260823-221839`).

**지표를 고른 근거**(CONTEXT.md [[화풍 도달]], ADR `260825-013557` 2026-08-25 개정 따름 정리 1 —
지표는 고르기 전에 정답지와 현행 양쪽에 걸어 분리도를 잰다):

  육안 소견은 「창백하다」이고 거기서 자연스럽게 나오는 지표는 **채도**인데, 채도 평균은 정답지와
  현행의 구간이 겹쳐 아무것도 갈라내지 못한다(정답지 0.201~0.259 ↔ 현행 0.105~0.217). 실제로
  갈라내는 것은 **어두운 화소 비율**(`휘도 < DARK_CUT`)로 17~75배 벌어진다. 결함의 정체는 채도가 아니라
  **잉크·대비의 부재**다. 그래서 채도(`sat_p95`)는 계속 **재되 판정에 쓰지 않는다** — 분리하지
  못한다는 사실 자체가 이 파일럿의 실측이라 지우지 않고 남긴다.

**적용 범위는 장면류다**(같은 개정 따름 정리 3). 동결 정본(얼굴 클로즈업)은 이 지표에서 0.006으로
실패해야 할 현행 장면과 같은 값을 낸다 — 초상은 원래 어두운 화소가 적다. 초상 판정에 쓰지 않는다.

Usage:
  python3 judge_style.py                 # 정답지 vs 현행 12장 — 분리도 판정 + 임계 파생
  python3 judge_style.py --json out.json # 같은 판정을 json으로도 남긴다
"""
import glob
import json
import math
import os
import sys

import numpy as np
from PIL import Image

import params

# --- 지표를 정의하는 상수 (임계가 아니다) -------------------------------------
# 「어두운 화소」의 경계. CONTEXT.md [[화풍 도달]]이 정답지/현행 양쪽에 걸어 17~75배 분리를
# 실측한 그 정의를 그대로 승계한다 — 여기서 바꾸면 그 실측과 못 잇는다. `judge_metrics.py`의
# EDGE_THRESHOLD와 같은 종류(지표를 정의하는 상수는 [[생성 파라미터]]가 아니므로 params가 아니라
# 판정 모듈이 갖는다).
DARK_CUT = 0.55
# **정정(task#317 S0 실측)**: CONTEXT.md와 계획이 이 지표를 「`v<0.55` 비율」로 적었으나, 그
# 실측표를 재현하는 것은 HSV의 V가 아니라 **그레이스케일 휘도**다 — sheet-s200이 휘도로 0.2019
# (문서의 시트 구간 0.172~0.233 안), HSV V로는 0.0980(구간 밖)이다. 표기가 잘못됐던 것이지 수가
# 잘못됐던 것이 아니므로, **문서의 수와 이어지는 쪽(휘도)을 채택하고 이름을 고친다.** V로 바꾸면
# 분리는 여전하지만 앞선 실측과의 비교 가능성이 끊긴다.

APPLIES_TO = "장면류(1216x640 및 시트류). 초상 층에는 쓰지 않는다."


def style_metrics(path):
    """한 장의 화풍 지표. HSV의 V·S만 쓴다 — 새 의존성 없이 PIL로 끝난다."""
    im = Image.open(path).convert("RGB")
    lum = np.asarray(im.convert("L"), dtype=np.float32) / 255.0
    sat = np.asarray(im.convert("HSV"), dtype=np.float32)[..., 1] / 255.0
    return {
        "ink": float((lum < DARK_CUT).mean()),   # 어두운 화소 비율 — 판정에 쓰는 축
        "val_p05": float(np.percentile(lum, 5)),  # 가장 어두운 5% — 잉크의 깊이
        "sat_p95": float(np.percentile(sat, 95)),  # 참고용. 갈라내지 못한다는 것이 실측이다
    }


def reference_paths():
    """정답지 = 추적 위치의 전부. 「어느 것을 쓸까」를 손으로 고르지 않는다 — 고르는 순간
    유리한 쪽만 남길 여지가 생긴다. 무엇이 왜 거기 있는지는 REFERENCE.md가 진다."""
    return sorted(glob.glob(os.path.join(params.REFERENCE, "*.png")))


def current_scene_paths():
    """음성 대조군 = 현행 ControlNet 경로 산출물(task#315 S4의 12장)."""
    return sorted(glob.glob(os.path.join(params.OUT_ROOT, "scene", "*.png")))


def _log_mid(a, b):
    """두 값의 **로그 중점**. 정답지와 현행이 곱셈적으로(17~75배) 벌어져 있으므로 산술 중점은
    한쪽에 붙는다. 로그 중점은 비율 척도에서 두 집합에 같은 여유(최대 마진)를 주는 분할점이고,
    자유 파라미터가 없어 임계에 사람의 손이 들어가지 않는다."""
    return math.sqrt(a * b)


def derive_thresholds(ref, ctl):
    """임계를 **파생한다**. 정답지 하한과 현행 상한 사이(반대 방향 지표는 그 반대)의 로그 중점.

    분리되지 않으면 임계를 만들지 않고 실패한다 — 갈라내지 못하는 자로 다음 슬라이스에 들어가지
    않는다(ADR `260825-013557`: 대조군이 통과하면 무정보다)."""
    ref_ink_lo, ctl_ink_hi = min(m["ink"] for m in ref), max(m["ink"] for m in ctl)
    ref_p05_hi, ctl_p05_lo = max(m["val_p05"] for m in ref), min(m["val_p05"] for m in ctl)
    ref_sat_lo, ctl_sat_hi = min(m["sat_p95"] for m in ref), max(m["sat_p95"] for m in ctl)
    return {
        "ink_min": _log_mid(ref_ink_lo, ctl_ink_hi),
        "val_p05_max": _log_mid(ref_p05_hi, ctl_p05_lo),
        "separation": {
            "ink_ratio": ref_ink_lo / ctl_ink_hi if ctl_ink_hi else float("inf"),
            "val_p05_ratio": ctl_p05_lo / ref_p05_hi if ref_p05_hi else float("inf"),
            "sat_p95_ratio": ref_sat_lo / ctl_sat_hi if ctl_sat_hi else float("inf"),
        },
        "reference_band": {  # 「통과」와 별개로 정답지가 실제로 어디 있는지 — 조일 때 쓴다
            "ink": [min(m["ink"] for m in ref), max(m["ink"] for m in ref)],
            "val_p05": [min(m["val_p05"] for m in ref), max(m["val_p05"] for m in ref)],
        },
    }


def passes(m, thr):
    return m["ink"] >= thr["ink_min"] and m["val_p05"] <= thr["val_p05_max"]


def _row(path, m, thr=None):
    mark = "" if thr is None else ("  ✅" if passes(m, thr) else "  ❌")
    return (f"  {os.path.basename(path):38s} ink={m['ink']:.4f}  "
            f"p05={m['val_p05']:.3f}  sat_p95={m['sat_p95']:.3f}{mark}")


def main():
    refs, ctls = reference_paths(), current_scene_paths()
    if not refs:
        sys.exit(f"정답지가 없다: {params.REFERENCE}")
    if not ctls:
        sys.exit(f"음성 대조군(현행 장면)이 없다: {params.OUT_ROOT}/scene")

    ref_m = [style_metrics(p) for p in refs]
    ctl_m = [style_metrics(p) for p in ctls]
    thr = derive_thresholds(ref_m, ctl_m)

    print(f"축 A [[화풍 도달]] — 지표 정의: 휘도 < {DARK_CUT} 비율 · 휘도의 5백분위")
    print(f"적용 범위: {APPLIES_TO}\n")
    print(f"정답지 {len(refs)}장 (양성 기준)")
    for p, m in zip(refs, ref_m):
        print(_row(p, m))
    print(f"\n현행 ControlNet 경로 {len(ctls)}장 (음성 대조군)")
    for p, m in zip(ctls, ctl_m):
        print(_row(p, m))

    sep = thr["separation"]
    print(f"\n분리도 — ink {sep['ink_ratio']:.1f}배 · p05 {sep['val_p05_ratio']:.2f}배 "
          f"· sat_p95 {sep['sat_p95_ratio']:.2f}배(판정 미사용)")
    print(f"파생 임계 — ink >= {thr['ink_min']:.4f} · val_p05 <= {thr['val_p05_max']:.3f}")
    print(f"정답지 실제 구간 — ink {thr['reference_band']['ink'][0]:.4f}~{thr['reference_band']['ink'][1]:.4f} "
          f"· p05 {thr['reference_band']['val_p05'][0]:.3f}~{thr['reference_band']['val_p05'][1]:.3f}")

    # --- 완료기준: (정답지 통과 · 현행 실패)를 스크립트가 단정한다 ---
    ref_pass = sum(passes(m, thr) for m in ref_m)
    ctl_pass = sum(passes(m, thr) for m in ctl_m)
    print(f"\n정답지 통과 {ref_pass}/{len(ref_m)} · 현행 통과 {ctl_pass}/{len(ctl_m)}")
    ok = ref_pass == len(ref_m) and ctl_pass == 0
    if "--json" in sys.argv:
        out = sys.argv[sys.argv.index("--json") + 1]
        with open(out, "w", encoding="utf-8") as f:
            json.dump({"dark_cut": DARK_CUT, "applies_to": APPLIES_TO, "thresholds": thr,
                       "reference": {os.path.basename(p): m for p, m in zip(refs, ref_m)},
                       "current": {os.path.basename(p): m for p, m in zip(ctls, ctl_m)}},
                      f, ensure_ascii=False, indent=1)
        print(f"json 기록: {out}")
    if not ok:
        sys.exit("축 A 분리 실패 — 이 자는 정답지와 현행을 갈라내지 못한다. 지표를 교체하라.")
    print("축 A PASS — 정답지 전수 통과 · 현행 전수 실패. 이 자는 분해능이 있다.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
