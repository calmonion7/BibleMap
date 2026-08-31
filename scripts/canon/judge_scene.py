"""본문 기반 장면(콘티 없음)의 기계 판정자 — `gen_scripture_scene.py` 산출물 전용.

**왜 새로 만드는가.** 기존 판정자(`judge_s1.py`·`judge_final.py`)의 축 C·D·G는 **콘티 잉크와의
상관**으로 정의돼 있어, 콘티를 버린 이 구조에서는 잴 대상 자체가 없다(2026-09-01 사용자 지시로
콘티 폐기, `notes/SCENE-1SAM17.md` §0). 화풍 축(A)만 `judge_style.style_metrics`로 살아남는다.

**무엇을 재는가 — 다섯.** `notes/SCENE-1SAM17.md` §5 체크리스트 열 항목 중 **기계로 잴 수 있는
것만** 고른다. 「어린갑을 입었는가」·「놋투구인가」 같은 항목은 여기서 재지 않는다(사람이 본다).

  C1 골짜기   17:3 — 좌우 능선이 가운데 골짜기 바닥보다 높은가 (하늘선 프로파일)
  C2 군대     17:2-3 — 좌우 능선 띠에 **작은 것이 많이** 있는가 (행별 교차수 · 세로 런 길이)
  C3 이음매   가로 자·직사각 잔상이 없는가 (전폭 얇은 가로선 행수 · 구역 상자 세로 변 대비)
  C4 화풍     인물별 잉크가 정답지 구간 안이고 둘의 비가 작은가 (judge_style와 같은 산식)
  C5 인물     두 인물이 남아 있고 크기 대비가 유지되는가 (잉크 bbox 높이)

**하늘 임계는 적응식이다.** 종이색(247,240,226)이 밝기 0.94쯤이고 마른 언덕은 0.75~0.85라
`judge_style`의 DARK_CUT=0.55로는 지형이 안 잡힌다. 위 5% 행의 중앙값을 하늘로 보고 거기서
`SKY_MARGIN`만큼 어두우면 「지형/사물」로 센다.

사용:
    python3 judge_scene.py <final.png> [--terrain <S1c.png>] [--json out.json]
    python3 judge_scene.py --calibrate v15 v16 v17 v18
"""

import argparse
import json
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import params  # noqa: E402

W, H = params.SCENE_SIZE
DARK_CUT = 0.55      # judge_style와 같은 값 — 화풍(잉크) 축은 산식을 바꾸지 않는다
SKY_MARGIN = 0.05    # 하늘 중앙값에서 이만큼 어두우면 「사물」

# 구역 상자 — gen_scripture_scene.REGIONS와 **같은 값이어야 한다**. 판정자가 생성자를 import하면
# torch·diffusers가 딸려 와 GPU 없이 못 돌므로, 좌표만 여기 복제하고 --check로 대조한다.
REGIONS = {
    "hill_left":   (0.00, 0.30, 0.38, 0.74),
    "hill_right":  (0.62, 0.26, 1.00, 0.72),
    "crest_left":  (0.02, 0.24, 0.44, 0.47),
    "crest_right": (0.56, 0.18, 0.99, 0.43),
    "goliath":     (0.625, 0.05, 0.855, 0.95),
    "shieldman":   (0.44, 0.52, 0.585, 0.94),
    "david":       (0.15, 0.52, 0.305, 0.92),
}
# 인물이 없는 세로 띠 — 골짜기 바닥을 여기서 잰다(다윗 0.305 끝 · 방패든자 0.44 시작 · 골리앗 0.625 시작)
GAP_BANDS = [(0.385, 0.435), (0.590, 0.620)]
CREST_L_X = (0.02, 0.30)   # 좌 능선 높이를 재는 x 구간
CREST_R_X = (0.70, 0.98)


def load(path):
    im = Image.open(path).convert("RGB")
    if im.size != (W, H):
        im = im.resize((W, H), Image.LANCZOS)
    return np.asarray(im.convert("L"), dtype=np.float32) / 255.0


def box(name):
    x0, y0, x1, y1 = REGIONS[name]
    return int(x0 * W), int(y0 * H), int(x1 * W), int(y1 * H)


def obj_mask(lum):
    """「하늘이 아닌 것」 — 적응 임계."""
    sky = float(np.median(lum[: int(0.05 * H)]))
    return lum < (sky - SKY_MARGIN), sky


THICK = 12   # 하늘선으로 인정할 최소 세로 두께(px)


def skyline(lum):
    """열마다 위에서 처음 **두꺼운** 사물이 나오는 행. 없으면 H.

    **두께 조건이 없으면 못 쓴다**(2026-09-01 실측): 화면을 가로지르는 자 같은 가로선(C3의
    결함) 때문에 전 열의 하늘선이 그 선의 y로 붙어 버려, v17의 좌·우·가운데가 전부 97~102로
    나왔다. 언덕은 두껍고 가로선은 1~3px이므로 **세로로 THICK행 이어질 때만** 지형으로 센다."""
    m, _ = obj_mask(lum)
    thick = m[: H - THICK + 1].copy()
    for k in range(1, THICK):
        thick &= m[k: H - THICK + 1 + k]
    first = np.argmax(thick, axis=0).astype(float)
    first[~thick.any(axis=0)] = H
    # 25px 이동 중앙값 — 홑점 잡티를 지운다
    k = 25
    pad = np.pad(first, k // 2, mode="edge")
    return np.median(np.lib.stride_tricks.sliding_window_view(pad, k), axis=-1)


def c1_valley(lum):
    """C1 — 좌우 능선이 골짜기 바닥보다 얼마나 높은가(캔버스 높이 분율)."""
    top = skyline(lum)
    xs = lambda a, b: slice(int(a * W), int(b * W))  # noqa: E731
    crest_l = float(np.percentile(top[xs(*CREST_L_X)], 10))
    crest_r = float(np.percentile(top[xs(*CREST_R_X)], 10))
    gap = np.concatenate([top[xs(a, b)] for a, b in GAP_BANDS])
    floor = float(np.median(gap))
    return {
        "crest_left_y": crest_l, "crest_right_y": crest_r, "floor_y": floor,
        "drop": min(floor - crest_l, floor - crest_r) / H,
    }


def _runs95(col_mask):
    """세로 런 길이의 95백분위 — 「큰 것 하나」와 「작은 것 여럿」을 가른다."""
    lens = []
    for c in range(col_mask.shape[1]):
        col = col_mask[:, c]
        if not col.any():
            continue
        d = np.diff(np.concatenate(([0], col.view(np.int8), [0])))
        lens.extend((np.flatnonzero(d < 0) - np.flatnonzero(d > 0)).tolist())
    return float(np.percentile(lens, 95)) if lens else 0.0


RIDGE_BAND = 0.08   # 「능선 위」로 인정할 하늘선 위아래 여유(캔버스 높이 분율)


def c2_army(lum, key, terrain_top=None):
    """C2 — 능선 띠 안의 「작은 것이 많음」. 교차수는 많고 세로 런은 짧아야 한다.

    **`on_ridge`가 없으면 못 쓴다**: v17은 병사 둘을 **빈 하늘 한가운데**에 그렸는데(17:2-3은
    「이편 산에 섰고 저편 산에 섰고」다) 띠 안에만 들어오면 교차수·런 길이만으로는 통과한다.
    지형 하늘선에서 ±RIDGE_BAND 안에 있는 잉크의 비율을 함께 본다."""
    x0, y0, x1, y1 = box(key)
    m, _ = obj_mask(lum)
    sub = m[y0:y1, x0:x1]
    rows = sub.any(axis=1)
    xings = float(np.abs(np.diff(sub.astype(np.int8), axis=1)).sum(axis=1)[rows].mean() / 2) \
        if rows.any() else 0.0
    on_ridge = 0.0
    if terrain_top is not None and sub.any():
        yy = np.arange(y0, y1)[:, None]
        ridge = terrain_top[x0:x1][None, :]
        near = np.abs(yy - ridge) <= RIDGE_BAND * H
        on_ridge = float((sub & near).sum() / sub.sum())
    return {"cov": float(sub.mean()), "xings": xings,
            "runlen95": _runs95(sub) / H, "on_ridge": on_ridge}


def c3_seam(lum):
    """C3 — ① 전폭 얇은 가로선 행수 ② 구역 상자 세로 변의 밝기 단차 배율."""
    d = 3
    body = lum[d:-d]
    thin = (body < lum[: -2 * d] - 0.03) & (body < lum[2 * d:] - 0.03)
    line_rows = int((thin.mean(axis=1) > 0.5).sum())

    grad = np.abs(np.diff(lum, axis=1))            # (H, W-1)
    worst, worst_at = 0.0, None
    for key in ("goliath", "david", "shieldman", "crest_left", "crest_right",
                "hill_left", "hill_right"):
        bx0, by0, bx1, by1 = box(key)
        for xe in (bx0, bx1 - 1):
            if not (32 < xe < W - 33):
                continue
            # **인물 선이 없는 행만** 본다. 상자가 인물에 딱 붙어 있어 그의 윤곽선이 변 근처를
            # 지나면 정상적인 선도 단차로 잡힌다 — 그러면 닫을 수 없는 조건이 된다. 배경 행에서
            # 재면 「배경에 사각 잔상이 있는가」만 남는다.
            bg = lum[by0:by1, max(0, xe - 20):xe + 21].min(axis=1) > DARK_CUT
            if bg.sum() < 20:
                continue
            g = grad[by0:by1, :][bg]
            colmean = g.mean(axis=0)
            # 상자 변 **±20px 중 가장 센 열**을 본다 — 되붙임 마스크에 깃털(FEATHER)이 걸려
            # 실제 단차가 변에서 몇 px 안쪽에 생긴다(v16의 눈에 띄는 사각 잔상이 변 정각에서는
            # 1.68로 안 잡혔다, 2026-09-01 실측).
            # **절대량으로 잰다.** 이웃 대비 배율을 쓰면 배경 행의 기준선이 0에 가까워 배율이
            # 폭발한다(같은 v16이 1.68 → 38.6). 눈에 보이는 단차는 밝기 단위로 말할 수 있다.
            here = float(colmean[max(0, xe - 20):xe + 21].max())
            if here > worst:
                worst, worst_at = here, f"{key}@x={xe}"
    return {"line_rows": line_rows, "vseam": worst, "vseam_at": worst_at}


def _sil_bbox(lum, key):
    """구역 상자 안에서 **실제로 그려진 것**의 bbox — 상자에는 배경이 많아 그대로 재면
    인물이 아니라 여백을 재게 된다(노트 §10의 실측이 실루엣 기준이라 값이 두 배 달랐다)."""
    x0, y0, x1, y1 = box(key)
    m, _ = obj_mask(lum)
    sub = m[y0:y1, x0:x1]
    rows, cols = np.flatnonzero(sub.any(axis=1)), np.flatnonzero(sub.any(axis=0))
    if not rows.size or not cols.size:
        return None
    return (x0 + int(cols[0]), y0 + int(rows[0]), x0 + int(cols[-1]) + 1, y0 + int(rows[-1]) + 1)


def c4_style(lum):
    """C4 — 인물별 잉크(judge_style.style_metrics의 ink와 같은 산식)와 둘의 비.
    **실루엣 bbox에서 잰다** — 노트 §10의 「다윗 0.2225 · 골리앗 0.2537」과 같은 기준."""
    out = {}
    for key in ("david", "goliath"):
        b = _sil_bbox(lum, key)
        out[f"ink_{key}"] = 0.0 if b is None else \
            float((lum[b[1]:b[3], b[0]:b[2]] < DARK_CUT).mean())
    lo, hi = sorted((out["ink_david"], out["ink_goliath"]))
    out["ink_ratio"] = hi / max(lo, 1e-6)
    return out


def c5_figures(lum):
    """C5 — 두 인물의 잉크 bbox 높이와 그 비(크기 대비 17:4)."""
    ink = lum < DARK_CUT     # **잉크 bbox** — obj_mask(하늘 아닌 것)로 재면 상자를 채운
                             # 배경·잔상까지 잡혀 어느 판이나 상자 비(2.2)만 나온다(실측).
    hs = {}
    for key in ("david", "goliath"):
        x0, y0, x1, y1 = box(key)
        rows = np.flatnonzero(ink[y0:y1, x0:x1].any(axis=1))
        hs[key] = float(rows[-1] - rows[0]) / H if rows.size else 0.0
    return {"h_david": hs["david"], "h_goliath": hs["goliath"],
            "scale_ratio": hs["goliath"] / max(hs["david"], 1e-6)}


def measure(final_path, terrain_path=None):
    lum = load(final_path)
    terr = load(terrain_path) if terrain_path else lum
    top = skyline(terr)
    return {
        "final": os.path.basename(final_path),
        "terrain": os.path.basename(terrain_path) if terrain_path else None,
        "c1_valley": c1_valley(terr),
        "c2_army_left": c2_army(lum, "crest_left", top),
        "c2_army_right": c2_army(lum, "crest_right", top),
        "c3_seam": c3_seam(lum),
        "c4_style": c4_style(lum),
        "c5_figures": c5_figures(lum),
    }


THRESHOLDS = {
    # 실측 교정(2026-09-01, v12·v15·v16·v17·v18 다섯 판). 「통과한 예」가 없는 축(C1·C2·C3)은
    # 본문·명세에서 온 목표치이고, 「지금 통과 중인 예」가 있는 축(C4·C5)은 v17 실측에서 왔다.
    "c1_drop_min": 0.14,        # 골짜기 깊이 ≥ 높이의 14%  (실측 v17 +0.028 · v16 −0.152)
    "c2_cov_min": 0.04,         # 능선 띠가 비어 있지 않을 것 (v18 우측 = 없음)
    "c2_xings_min": 15.0,       # 행당 교차 ≥ 15 = 폭 511px에 34px마다 하나 (v17 좌 1.95 · 우 7.29)
    "c2_on_ridge_min": 0.50,    # 잉크의 절반 이상이 하늘선 ±8% 안 = 「산에 섰다」(17:2-3)
    "c2_runlen95_max": 0.06,    # 세로 런 95p ≤ 높이의 6%(38px) — 「큰 병사」 배제 (v17 우 0.092)
    "c3_line_rows_max": 1,      # 전폭 얇은 가로선 행 ≤ 1  (다섯 판 모두 8~10)
    "c3_vseam_max": 0.010,      # 상자 변 배경 단차(밝기) — 보통 열은 0.002/90p 0.0045, 변은 0.069~0.101
    "c4_ink_min": 0.055,        # 인물이 지워지지 않을 것 (v17 다윗 0.0727 · v15 0.0434 = 실패)
    "c4_ratio_max": 2.40,       # 두 인물 잉크 비 (v17 2.14 · v15 3.34 = 실패)
    "c5_scale_min": 1.60,       # 크기 대비 17:4 (v17 2.02 · v18 1.88)
}


def verdict(m, t=THRESHOLDS):
    c = {}
    c["C1"] = m["c1_valley"]["drop"] >= t["c1_drop_min"]
    c["C2"] = all(
        a["cov"] >= t["c2_cov_min"] and a["xings"] >= t["c2_xings_min"]
        and a["runlen95"] <= t["c2_runlen95_max"] and a["on_ridge"] >= t["c2_on_ridge_min"]
        for a in (m["c2_army_left"], m["c2_army_right"]))
    c["C3"] = (m["c3_seam"]["line_rows"] <= t["c3_line_rows_max"]
               and m["c3_seam"]["vseam"] <= t["c3_vseam_max"])
    s = m["c4_style"]
    c["C4"] = (min(s["ink_david"], s["ink_goliath"]) >= t["c4_ink_min"]
               and s["ink_ratio"] <= t["c4_ratio_max"])
    c["C5"] = m["c5_figures"]["scale_ratio"] >= t["c5_scale_min"]
    return c


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("final", nargs="?")
    ap.add_argument("--terrain", default=None, help="지형만 있는 단계 산출물(S1c) — 없으면 final로 잰다")
    ap.add_argument("--json", default=None)
    ap.add_argument("--calibrate", nargs="+", default=None, help="라벨들(v15 v16 ...)을 한 줄씩 비교")
    a = ap.parse_args()

    root = os.path.join(params.OUT_ROOT, "scripture-scene") \
        if hasattr(params, "OUT_ROOT") else None

    if a.calibrate:
        print(f"{'라벨':>6} {'C1 drop':>8} {'L xings':>8} {'L ridge':>8} {'R xings':>8} {'R ridge':>8} "
              f"{'가로선':>6} {'세로단차':>9} {'ink D':>7} {'ink G':>7} {'비':>5} {'크기비':>6}")
        for lab in a.calibrate:
            f = os.path.join(root, f"{lab}-final-s11.png")
            if not os.path.exists(f):
                print(f"{lab:>6}  (없음)")
                continue
            t = os.path.join(root, f"{lab}-S1c-s11.png")
            m = measure(f, t if os.path.exists(t) else None)
            v = verdict(m)
            print(f"{lab:>6} {m['c1_valley']['drop']:8.3f} "
                  f"{m['c2_army_left']['xings']:8.2f} {m['c2_army_left']['on_ridge']:8.2f} "
                  f"{m['c2_army_right']['xings']:8.2f} {m['c2_army_right']['on_ridge']:8.2f} "
                  f"{m['c3_seam']['line_rows']:6d} {m['c3_seam']['vseam']:9.4f} "
                  f"{m['c4_style']['ink_david']:7.4f} {m['c4_style']['ink_goliath']:7.4f} "
                  f"{m['c4_style']['ink_ratio']:5.2f} {m['c5_figures']['scale_ratio']:6.2f}  "
                  + " ".join(k for k, ok in v.items() if ok))
        return 0

    if not a.final:
        sys.exit("판정할 이미지를 달라 (또는 --calibrate)")
    m = measure(a.final, a.terrain)
    v = verdict(m)
    m["verdict"] = v
    print(json.dumps(m, ensure_ascii=False, indent=2))
    if a.json:
        with open(a.json, "w") as fh:
            json.dump(m, fh, ensure_ascii=False, indent=2)
    return 0 if all(v.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
