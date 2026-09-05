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

**장면 명세를 읽는다**(task 330). 구역 상자·인물 목록·단계 순서는 `scenes/<id>.json`에서 오고
축 이름은 명세의 판정 인물(`judge.figures`)에서 파생한다(`ink_<cast>`·`h_<cast>`). 임계·산식은
장면과 무관한 공통 상수로 여기 남는다.

사용:
    python3 judge_scene.py v35 --scene <id>     # 한 판 — JSON + 종료코드(0=다섯 축 통과)
    python3 judge_scene.py v17 v25 v33 v35      # 여러 판 — 한 줄씩 비교 (scenes/에 명세가 하나면 --scene 생략 가능)
"""

import argparse
import json
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import params  # noqa: E402
import derive_scene as ds  # noqa: E402  — 단계 목록을 **생성기와 같은 곳**에서 읽는다

W, H = params.SCENE_SIZE
DARK_CUT = 0.55      # judge_style와 같은 값 — 화풍(잉크) 축은 산식을 바꾸지 않는다
SKY_MARGIN = 0.05    # 하늘 중앙값에서 이만큼 어두우면 「사물」
SEAM_STEP = 0.02     # 이음매로 셀 한 픽셀 밝기 단차

# 구역 상자 — **생성자와 같은 명세에서 읽는다**(configure). 예전엔 좌표를 여기 복제했고 실제로
# 어긋나 있었다(shieldman y0 .52 vs 생성자 .41 — task 330에서 발견). 생성자를 import하면
# torch·diffusers가 딸려 와 GPU 없이 못 돌므로, 명세 JSON을 공유 지점으로 삼는다.
REGIONS = {}
GAP_BANDS = []        # 인물이 없는 세로 띠 — 골짜기 바닥을 여기서 잰다 (명세 judge.gap_bands)
CREST_L_X = CREST_R_X = None   # 좌·우 능선 높이를 재는 x 구간 (명세 judge.crest_x)
STAGE_ORDER = []      # [(단계, 구역|None)] — C3 붙임 이음매가 훑는 순서 (명세 stages, skip 제외)
FIGURES = []
AXES = []   # 이 장면에서 판정할 축(명세에서 파생 — configure)          # C4·C5가 재는 인물 cast (명세 judge.figures)


def configure(spec, figures="plate"):
    """장면 명세에서 판정 기하를 채운다 — 생성자(`gen_scripture_scene`)도 같은 명세로 이 함수를 부른다.

    `figures`는 생성기에 준 값과 **같아야 한다**(task 337). 장면 안 경로에서는 그룹이 한 단계로
    합쳐져 산출물 파일도 하나뿐인데, 옛 목록을 보면 없는 단계를 찾고 그룹 상자를 반쪽만 잰다."""
    REGIONS.clear()
    REGIONS.update({k: tuple(v) for k, v in spec["regions"].items()})
    j = spec["judge"]
    GAP_BANDS[:] = [tuple(b) for b in j["gap_bands"]]
    global CREST_L_X, CREST_R_X
    CREST_L_X, CREST_R_X = tuple(j["crest_x"]["left"]), tuple(j["crest_x"]["right"])
    STAGE_ORDER[:] = [(st["id"], None if kind == "full" else tuple(regs))
                      for st, kind, regs in ds.stage_plan(spec, figures) if not st.get("skip")]
    FIGURES[:] = list(j["figures"])
    # **적용 축을 명세에서 파생한다**(task 333). C1(골짜기)·C2(군대 능선)·C5(크기 대비)는 삼상17 기하가
    # 있어야 뜻이 있는 축이다 — 능선 구역이 없는 장면에서 재면 KeyError이거나 무의미한 수치가 나온다.
    # 임계·산식은 **건드리지 않는다**(회귀 가드). 삼상17 명세는 셋을 다 만족하므로 다섯 축 그대로다.
    AXES[:] = j.get("axes") or (
        ["C3", "C4"]
        + (["C1", "C2"] if {"crest_left", "crest_right"} <= set(spec["regions"]) else [])
        # C5의 임계(1.60)는 「여섯 규빗 거인 대 소년」 대비에서 온 값이다 — 성인 둘이 나란한 장면에
        # 걸면 반드시 낙제한다. 그래서 **명세가 그만한 대비를 의도했을 때만** 이 축을 켠다(임계는 불변).
        + (["C5"] if len(FIGURES) >= 2 and _spec_scale(spec) >= THRESHOLDS["c5_scale_min"] else []))


def _spec_scale(spec):
    """명세의 판정 인물 상자 높이 비 — C5를 켤지 정하는 파생값(재는 것은 그림에서 잰다)."""
    hs = [spec["regions"][k][3] - spec["regions"][k][1] for k in spec["judge"]["figures"]
          if k in spec["regions"]]
    return max(hs) / max(min(hs), 1e-6) if len(hs) >= 2 else 0.0


def load_scene(scene_id=None):
    """`--scene`이 없고 scenes/에 명세가 하나면 그것을 쓴다 — 둘 이상이면 골라야 한다."""
    d = os.path.join(params.CANON_DIR, "scenes")
    if scene_id is None:
        ids = sorted(f[:-5] for f in os.listdir(d) if f.endswith(".json"))
        if len(ids) != 1:
            sys.exit(f"--scene을 지정하라 — scenes/에 명세가 {len(ids)}개다: {', '.join(ids)}")
        scene_id = ids[0]
    with open(os.path.join(d, f"{scene_id}.json"), encoding="utf-8") as fh:
        return json.load(fh)


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


RIDGE_UP, RIDGE_DOWN = 0.09, 0.05   # 「능선 위」로 볼 하늘선 위아래 여유(생성 띠보다 넉넉하게)


def c2_army(lum, key, terrain_top, before=None):
    """C2 — 능선 띠 안에서 **군대 단계가 실제로 그린 것**이 「작은 것이 여럿」인가. 17:2-3.

    ⚠ **세 번 고쳐서 여기 왔다(2026-09-01). 앞의 셋이 왜 못 쓰는지 남긴다.**
    ① 손으로 적은 가로 상자 전체의 「하늘 아닌 것」 — v17이 병사 둘을 **빈 하늘**에 그려도 통과했다.
    ② +`on_ridge`(하늘선 근처 비율) — 뜬 병사는 걸렀지만 세로 런이 **병사가 아니라 언덕**을 쟀다
       (상자의 30%가 지형). 띠를 얇게 해도 0.127로 되레 늘었다.
    ③ 능선 띠 안의 잉크·엣지 — 마른 언덕의 **등고선**이 군중과 구별되지 않았다(v17 우측 엣지밀도
       0.395 ↔ 진짜 군중 0.472, 못 가른다).
    ④ **군대 단계 직전(S1c)과 직후(S2b)의 차이**를 잰다. 그 둘이 곧 S2a·S2b가 그린 것이고
       지형은 정의상 빠진다. 파이프라인이 단계마다 저장하므로 새 자료가 필요 없다.
    `before`가 없으면(단계 산출물이 없는 옛 판) 능선 띠의 잉크로 물러난다 — 비교는 못 한다."""
    x0, _, x1, _ = box(key)
    yy = np.arange(H)[:, None]
    band = (yy >= (terrain_top - RIDGE_UP * H)) & (yy <= (terrain_top + RIDGE_DOWN * H))
    band &= (terrain_top < H - 1)[None, :]
    if before is not None:
        drew = (np.abs(lum - before) > 0.04) & band     # 이 단계가 손댄 화소
    else:
        drew = (lum < DARK_CUT) & band
    sub = drew[:, x0:x1]
    bb = band[:, x0:x1]
    rows = bb.any(axis=1)
    xings = float(np.abs(np.diff(sub.astype(np.int8), axis=1)).sum(axis=1)[rows].mean() / 2) \
        if rows.any() else 0.0
    return {"cov": float(sub.sum() / max(1, bb.sum())), "xings": xings,
            "runlen95": _runs95(sub) / H}


def c3_lines(lum, terrain_top=None):
    """C3의 절반 — **하늘을 가로지르는** 얇은 가로선 행수(종횡비 아티팩트).

    **하늘로 한정해야 한다**(2026-09-01 실측): 지면의 지층선·능선도 화면 폭 절반을 넘게 이어지는
    얇은 가로선이라, 한정하지 않으면 **정상 묘사를 결함으로 센다**(t323b에서 남은 6행 중 넷이
    지층선이었다). 하늘에 가로지르는 자 같은 선은 어느 화풍에서도 결함이다."""
    d = 3
    body = lum[d:-d]
    thin = (body < lum[: -2 * d] - 0.03) & (body < lum[2 * d:] - 0.03)
    if terrain_top is None:
        terrain_top = skyline(lum)
    yy = np.arange(d, H - d)[:, None]
    sky = yy < terrain_top[None, :]          # 그 열에서 지형보다 위인가
    line_rows = int(((thin & sky).mean(axis=1) > 0.40).sum())

    return {"line_rows": line_rows}


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


# --- C3 재정의(2026-09-01, task 325) — 「붙임이 상자 선에서 끝났는가」 -----------------
# 앞선 세 판(절대 단차 · 상자 변 열의 행 비율 · 그 상대값)은 모두 **화면을 세로로 지나는 것**을
# 셌다. 그래서 창자루·바위 등고선 같은 **정상 묘사**가 걸렸고(v35의 최대값 0.823이 골리앗의
# 창자루였다), 지형이 상세해지면 보통 열의 99백분위가 임계를 넘어 판정 자체가 불가능해졌다.
#
# 이음매의 기전은 「세로선이 있다」가 아니라 **「이 단계가 칠한 자리가 상자 선에서 잘리고,
# 그 선을 넘는 밝기 단차가 남았다」** 이다. 둘이 **동시에** 성립해야 한다. 단계마다 직전/직후
# 그림이 저장돼 있으므로 「이 단계가 칠한 자리」를 정확히 알 수 있다(C2를 정직하게 만든 수법).
# 이 정의에서는 창자루가 자동으로 빠진다 — 붙임 **안쪽**에 있지 상자 선에 걸치지 않는다.
# STAGE_ORDER는 명세에서 온다(configure) — 예전 값: S1 · S1b/hill_left · S1c/hill_right · S2a/crest_left ·
# S2b/crest_right · S3/goliath · S4/shieldman · S5/david.
PASTE_CUT = 0.04    # 이 단계가 칠했다고 볼 밝기 변화
EDGE_IN = 3         # 상자 선 안쪽/바깥쪽을 보는 거리(px)
# 최소 표본 가드 — 임계(「한 변의 **대부분**에서 끊긴다」)와 같은 단위여야 한다. 절대치 `n<20`은
# 변 길이의 2~3%를 판정에 넣어 인물 겨드랑이의 배경 몇 픽셀로 v38·v39의 S3/goliath가 .658로
# 걸렸다. 실측 교정 구간(2026-09-02): 배경 비율 16.5%(v38 goliath.bottom, 이음매 아님) ↔ 26.2%
# (v17 crest_right.bottom, 진짜 이음매) — 0.20은 그 사이다(ADR 260902-231339).
SEAM_MIN_FRAC = 0.20  # 표본이 변 길이의 1/5 미만이면 그 변은 판정하지 않는다


def _edge_seam(cur, prev, b):
    """상자 b의 네 변에서 「붙임이 그 선에서 끝나며 단차를 남긴」 위치의 비율(최댓값).

    안/밖은 **상자 중심 기준**이다(화면 절반 기준으로 잡았다가 좌우가 뒤집혔다 — 2026-09-01)."""
    drew = np.abs(cur - prev) > PASTE_CUT
    x0, y0, x1, y1 = b
    worst, at = 0.0, None
    sides = (("left",   x0,     +1, True),  ("right",  x1 - 1, -1, True),
             ("top",    y0,     +1, False), ("bottom", y1 - 1, -1, False))
    for side, line, inward, vert in sides:
        lim = W if vert else H
        if not (EDGE_IN < line < lim - EDGE_IN - 1):
            continue
        i, o = line + inward * EDGE_IN, line - inward * EDGE_IN
        if vert:
            ins, out = drew[y0:y1, i], drew[y0:y1, o]
            step = np.abs(cur[y0:y1, line + 1] - cur[y0:y1, line - 1]) > SEAM_STEP
            bg = (cur[y0:y1, i] > DARK_CUT) & (cur[y0:y1, o] > DARK_CUT)
        else:
            ins, out = drew[i, x0:x1], drew[o, x0:x1]
            step = np.abs(cur[line + 1, x0:x1] - cur[line - 1, x0:x1]) > SEAM_STEP
            bg = (cur[i, x0:x1] > DARK_CUT) & (cur[o, x0:x1] > DARK_CUT)
        # **양쪽이 다 배경일 때만 센다.** 인물이 상자 바닥에 발을 딛으면 붙임이 그 선에서 끝나고
        # 단차도 있지만 그것은 **발**이지 이음매가 아니다(2026-09-01 실측: 이 조건 없이는 판 합성도
        # 0.61로 걸렸다). 이음매는 **배경 안에** 생기는 사각형 자국이다.
        n = int((ins & bg).sum())
        L = (y1 - y0) if vert else (x1 - x0)
        if n < SEAM_MIN_FRAC * L:   # 이 변에 붙임이 배경으로 거의 안 닿았으면 판정 대상이 아니다
            continue
        f = float((ins & ~out & step & bg).sum() / n)
        if f > worst:
            worst, at = f, side
    return worst, at


def c3_paste_seam(root, label, seed):
    """붙임 이음매 — 단계마다 직전/직후를 비교해 상자 선에서 잘린 붙임을 찾는다."""
    prev, worst, at = None, 0.0, None
    for name, regions in STAGE_ORDER:
        f = os.path.join(root, f"{label}-{name}-s{seed}.png")
        if not os.path.exists(f):
            continue
        cur = load(f)
        if prev is not None and regions is not None:
            # 그룹 단계는 상자가 여럿이다 — **합집합 상자**의 변에서 잰다. 한 인물 상자만 보면
            # 실제로 칠한 자리가 잘린 선을 놓친다.
            bs = [box(r) for r in regions]
            b = (min(x[0] for x in bs), min(x[1] for x in bs),
                 max(x[2] for x in bs), max(x[3] for x in bs))
            v, side = _edge_seam(cur, prev, b)
            if v > worst:
                worst, at = v, f"{name}/{'+'.join(regions)}.{side}"
        prev = cur
    return {"paste_seam": worst, "paste_seam_at": at}


def c4_style(lum):
    """C4 — 인물별 잉크(judge_style.style_metrics의 ink와 같은 산식)와 둘의 비.
    **실루엣 bbox에서 잰다** — 노트 §10의 「다윗 0.2225 · 골리앗 0.2537」과 같은 기준."""
    out = {}
    for key in FIGURES:
        b = _sil_bbox(lum, key)
        out[f"ink_{key}"] = 0.0 if b is None else \
            float((lum[b[1]:b[3], b[0]:b[2]] < DARK_CUT).mean())
    inks = sorted(out.values())
    out["ink_ratio"] = inks[-1] / max(inks[0], 1e-6)
    return out


def c5_figures(lum):
    """C5 — 두 인물의 잉크 bbox 높이와 그 비(크기 대비 17:4)."""
    ink = lum < DARK_CUT     # **잉크 bbox** — obj_mask(하늘 아닌 것)로 재면 상자를 채운
                             # 배경·잔상까지 잡혀 어느 판이나 상자 비(2.2)만 나온다(실측).
    hs = {}
    for key in FIGURES:
        x0, y0, x1, y1 = box(key)
        rows = np.flatnonzero(ink[y0:y1, x0:x1].any(axis=1))
        hs[key] = float(rows[-1] - rows[0]) / H if rows.size else 0.0
    # 크기 대비 = 가장 큰 인물 / 가장 작은 인물 (삼상17에서는 골리앗/다윗)
    return {**{f"h_{k}": v for k, v in hs.items()},
            "scale_ratio": max(hs.values()) / max(min(hs.values()), 1e-6)}


def measure(root, label, seed=11):
    """한 판의 다섯 축. 단계 산출물을 **판정자가 스스로 찾는다** — C2(군대 단계 직전/직후 차이)와
    C3(붙임이 상자 선에서 끝났는가)이 둘 다 단계 그림을 필요로 하므로, 경로를 손으로 넘기지 않는다."""
    def path(stage):
        return os.path.join(root, f"{label}-{stage}-s{seed}.png")
    lum = load(path("final"))
    terr = load(path("S1c")) if os.path.exists(path("S1c")) else lum
    top = skyline(terr)
    arm = load(path("S2b")) if os.path.exists(path("S2b")) else None
    m = {
        "label": label, "seed": seed,
        "c3_seam": {**c3_lines(lum, top), **c3_paste_seam(root, label, seed)},
        "c4_style": c4_style(lum),
    }
    if "C1" in AXES:
        m["c1_valley"] = c1_valley(terr)
    if "C2" in AXES:
        m["c2_army_left"] = c2_army(arm if arm is not None else lum, "crest_left", top,
                                    terr if arm is not None else None)
        m["c2_army_right"] = c2_army(arm if arm is not None else lum, "crest_right", top,
                                     terr if arm is not None else None)
    if "C5" in AXES:
        m["c5_figures"] = c5_figures(lum)
    return m


THRESHOLDS = {
    # 실측 교정(2026-09-01, v12·v15·v16·v17·v18 다섯 판). 「통과한 예」가 없는 축(C1·C2·C3)은
    # 본문·명세에서 온 목표치이고, 「지금 통과 중인 예」가 있는 축(C4·C5)은 v17 실측에서 왔다.
    "c1_drop_min": 0.14,        # 골짜기 깊이 ≥ 높이의 14%  (실측 v17 +0.028 · v16 −0.152)
    # C2는 산식을 네 번 고쳤으므로(c2_army 주석) 임계도 **새 산식의 실측**에서 다시 왔다.
    # ⚠ 양성 표본이 t324c 한 판뿐이다 — 통과한 예가 하나라는 것을 알고 쓴다.
    "c2_cov_min": 0.20,         # 군대 단계가 능선 띠를 채웠나 (t324c .389/.405 ↔ v17 .036/.069 ↔ v25 .000)
    "c2_xings_min": 2.5,        # 한 덩어리 막대가 아니라 여럿 (t324c 7.19/5.41 ↔ v17 0.29/1.31)
    "c2_runlen95_max": 0.06,    # 세로 런 95p ≤ 높이의 6%(38px) — 「큰 병사」 배제 (t324c .045 ↔ v17 .058)
    "c3_line_rows_max": 1,      # 하늘 가로선 행 ≤ 1 (v17 6행 ↔ 종횡비를 고친 뒤 0행)
    # 직사각 잔상이면 붙임이 **한 변의 대부분**에서 끊긴다 — 임계를 「대부분」에서 잡는다.
    # 실측 분리(비율 가드 SEAM_MIN_FRAC): 상자 인페인팅 .645~.844 ↔ 판 합성 .198~.222 (3배).
    # 구 가드(n<20) 값은 상자 .774~.950 ↔ 판 .250 이었다 — task 325에서 재정의, 328에서 가드 교정.
    "c3_paste_seam_max": 0.40,
    "c4_ink_min": 0.055,        # 인물이 지워지지 않을 것 (v17 다윗 0.0727 · v15 0.0434 = 실패)
    "c4_ratio_max": 2.40,       # 두 인물 잉크 비 (v17 2.14 · v15 3.34 = 실패)
    "c5_scale_min": 1.60,       # 크기 대비 17:4 (v17 2.02 · v18 1.88)
}


def verdict(m, t=THRESHOLDS):
    c = {}
    if "C1" in AXES:
        c["C1"] = m["c1_valley"]["drop"] >= t["c1_drop_min"]
    if "C2" in AXES:
        c["C2"] = all(
            a["cov"] >= t["c2_cov_min"] and a["xings"] >= t["c2_xings_min"]
            and a["runlen95"] <= t["c2_runlen95_max"]
            for a in (m["c2_army_left"], m["c2_army_right"]))
    c["C3"] = (m["c3_seam"]["line_rows"] <= t["c3_line_rows_max"]
               and m["c3_seam"]["paste_seam"] <= t["c3_paste_seam_max"])
    s = m["c4_style"]
    c["C4"] = (min(v for k, v in s.items() if k.startswith("ink_") and k != "ink_ratio") >= t["c4_ink_min"]
               and s["ink_ratio"] <= t["c4_ratio_max"])
    if "C5" in AXES:
        c["C5"] = m["c5_figures"]["scale_ratio"] >= t["c5_scale_min"]
    return c


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("labels", nargs="+", help="판 라벨 하나 이상 (예: v35). 여럿이면 표로 비교한다")
    ap.add_argument("--seed", type=int, default=11)
    ap.add_argument("--json", default=None, help="라벨이 하나일 때 판정을 파일로 남긴다")
    ap.add_argument("--scene", default=None, help="장면 명세 id (scenes/<id>.json) — 명세가 하나면 생략 가능")
    a = ap.parse_args()
    configure(load_scene(a.scene))
    root = os.path.join(params.OUT_ROOT, "scripture-scene")

    if len(a.labels) == 1:
        m = measure(root, a.labels[0], a.seed)
        m["verdict"] = verdict(m)
        print(json.dumps(m, ensure_ascii=False, indent=2))
        if a.json:
            with open(a.json, "w") as fh:
                json.dump(m, fh, ensure_ascii=False, indent=2)
        return 0 if all(m["verdict"].values()) else 1

    print(f"{'라벨':>6} {'C1골짜기':>8} {'C2좌':>6} {'C2우':>6} {'가로선':>6} {'붙임이음매':>10} "
          f"{'잉크비':>6} {'크기비':>6}  통과")
    ok = True
    for lab in a.labels:
        if not os.path.exists(os.path.join(root, f"{lab}-final-s{a.seed}.png")):
            print(f"{lab:>6}  (없음)")
            continue
        m = measure(root, lab, a.seed)
        v = verdict(m)
        ok = ok and all(v.values())
        num = lambda x, w, p: f"{x:{w}.{p}f}" if x is not None else " " * (w - 1) + "-"   # noqa: E731
        print(f"{lab:>6} {num(m.get('c1_valley', {}).get('drop'), 8, 3)} "
              f"{num(m.get('c2_army_left', {}).get('cov'), 6, 3)} "
              f"{num(m.get('c2_army_right', {}).get('cov'), 6, 3)} {m['c3_seam']['line_rows']:6d} "
              f"{m['c3_seam']['paste_seam']:10.3f} {m['c4_style']['ink_ratio']:6.2f} "
              f"{num(m.get('c5_figures', {}).get('scale_ratio'), 6, 2)}  "
              f"{' '.join(k for k, y in v.items() if y)}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
