"""팔 판정자 후보 훑기 — 대조군에 대고 고른다 (task#321 S3, GPU 0).

**대조군은 이 파일보다 먼저 못박혔다**(`notes/ARM.md`, 앞선 커밋). 여기서 하는 일은 후보를
그 대조군에 대고 재는 것뿐이고, 값을 보고 대조군이나 임계를 고치지 않는다(ADR `260825-013557`).

## 왜 「부위별 축 C」 하나로 안 끝나는가 — 결함을 눈으로 확인하고 후보를 설계했다

2026-08-30, 팔 구간(x326-487, y230-393)을 세 장에서 잘라 육안 확인했다:

  * **콘티(양성)** — 어깨에서 손까지 올라가는 팔이 **두 획**으로 그려져 있다(바깥 stroke 7 ·
    안쪽 stroke 4). 사지의 윤곽선 두 줄이다.
  * **음성 A (s11 분리)** — 팔 자리가 통째로 **배경**이다. 창백한 쐐기 모양만 있고 사지가 없다.
  * **음성 B (s7 관통)** — **물매 끈 얇은 직선**이 팔 회랑을 그대로 지나간다. 역시 사지가 없다.
    끈은 한 줄이므로 콘티의 두 획 중 **한 획만** 덮을 수 있다.

### 1차 훑기가 전멸했고, 그 전멸이 방향을 알려줬다 (2026-08-30)

첫 다섯 후보(`part_corr` · `part_corr_excl` · `stroke_min_cov2/3` · `collar_cleanliness`)는
**전부 「콘티 선 자리에 엣지가 있는가」 한 종류**였고 전부 음성 B에 뚫렸다. 실측이 이유를 말한다:

  part_corr — 음성 B **+0.489** > 양성(콘티) **+0.226**

**음성 B가 정답보다 높다.** 끈이 콘티 선 위에 정확히 놓이면 이 계열은 원리적으로 못 가른다 —
임계를 어디에 두든 양성보다 높은 음성은 못 떨어뜨린다. 그리고 「콘티 팔은 두 획이니 얇은 한 줄은
한 획만 덮는다」는 전제도 실측으로 틀렸다: 두 획(7px·4px)의 간격이 5.8px이라 렌더에서 **하나로
붙는다**(연결성분 1개). 콘티는 팔을 윤곽이 아니라 **굵은 선 하나**로 그린다.

그래서 방향을 바꾼다. 크롭이 보여준 진짜 차이는 「선 위에 무엇이 있는가」가 아니라
**사지에는 두께가 있고 끈에는 없다**이다 — `limb_width`가 그것을 잰다. 나머지 다섯은 기각
근거로 남긴다(계획 S3: 실측 사항이지 인용으로 기각할 것이 아니다).

Usage: /Users/calmonion/.local/biblemap-imggen/.venv314/bin/python arm_sweep.py [--json OUT]
"""
import json
import os
import sys
from collections import deque

import numpy as np
from PIL import Image, ImageFilter

import judge_axes as ja
import judge_s1 as js1
import params

PART = "david-arm"
WHO = "david"
DEFAULT_JSON = os.path.join(params.NOTES, "arm-sweep.json")

# 다른 부위 — 배타 띠 후보가 이 띠들을 뺀다. 콘티 DOM의 부위 id에서 온다(손으로 지은 목록이 아니다).
OTHER_PARTS = ("david-head", "david-torso", "david-arm-off", "david-leg", "david-prop")


def _label(mask):
    """4-이웃 연결성분. scipy가 없어 직접 쓴다 — 팔 잉크는 737화소라 BFS로 충분하다."""
    lab = np.zeros(mask.shape, dtype=np.int32)
    cur = 0
    for sy, sx in zip(*np.nonzero(mask)):
        if lab[sy, sx]:
            continue
        cur += 1
        q = deque([(sy, sx)])
        lab[sy, sx] = cur
        while q:
            y, x = q.popleft()
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ny, nx = y + dy, x + dx
                if 0 <= ny < mask.shape[0] and 0 <= nx < mask.shape[1] \
                        and mask[ny, nx] and not lab[ny, nx]:
                    lab[ny, nx] = cur
                    q.append((ny, nx))
    return lab, cur


def _dilate(m, r):
    im = Image.fromarray((m > 0).astype(np.uint8) * 255)
    return np.asarray(im.filter(ImageFilter.MaxFilter(2 * r + 1))) > 127


def geometry():
    """판정 기하 — 전부 콘티에서 파생한다(ADR `260830-084555`). 손으로 적은 좌표가 없다."""
    r = js1._conti_stroke(WHO)
    mask = js1._load_conti_mask(WHO)
    ink = js1._conti_ink(PART) > 0
    band = mask & js1._band(ink.astype(np.float32), r)
    other = np.zeros_like(band)
    for p in OTHER_PARTS:
        other |= mask & js1._band(js1._conti_ink(p), r)
    lab, n = _label(ink)
    return {"r": r, "mask": mask, "ink": ink, "band": band,
            "band_excl": band & ~other,
            "collar": (mask & js1._band(ink.astype(np.float32), 3 * r)) & ~band,
            "strokes": [lab == i for i in range(1, n + 1)]}


# --- 후보들 — 전부 「높을수록 좋다」로 맞춘다(임계가 음성·양성의 산술 중점이므로 방향이 같아야 한다)
def _corr(ink, ed, region):
    if region.sum() == 0 or ed[region].std() == 0 or ink[region].std() == 0:
        return 0.0
    return float(np.corrcoef(ink[region].ravel().astype(np.float32),
                             ed[region].ravel().astype(np.float32))[0, 1])


def _centerline(ink, n=25):
    """콘티 팔 잉크의 중심선 표본과 법선 — 전부 잉크에서 파생한다(손으로 적은 좌표가 없다).

    주축(PCA)을 따라 n곳을 잡고, 각 곳에서 주축 좌표가 가까운 잉크 화소의 무게중심을 중심점으로,
    부축을 법선으로 쓴다. 팔이 45도로 기울어 있어 행/열 평균은 왜곡되지만 주축은 그렇지 않다."""
    ys, xs = np.nonzero(ink)
    pts = np.stack([xs, ys], 1).astype(np.float64)
    c = pts.mean(0)
    u = np.linalg.svd(pts - c, full_matrices=False)[2]
    major, minor = u[0], u[1]
    proj = (pts - c) @ major
    out = []
    for s in np.linspace(proj.min(), proj.max(), n):
        sel = np.abs(proj - s) < 2.0
        if sel.sum() < 3:
            continue
        out.append((pts[sel].mean(0), minor))
    return out


def _limb(g, require_clean_center, w_min):
    """중심선 표본마다 법선 위에서 **경계 한 쌍**을 찾아 사지인지 센다.

    `require_clean_center` — 중심 화소 자체가 엣지면 그 표본을 사지로 세지 않는다. 이것이
    관통(음성 B)을 잡는 조건이다: 끈은 **중심선 위에 얹히고**, 사지는 중심이 매끄러운 내부다.
    실측 프로파일(2026-08-30, 표본 25개):

        콘티(양성)  엣지 t = -3, +4        중심 매끄러움 · 경계 한 쌍   → 사지
        s7(관통)    엣지 t = -1, 0, 1, 2, 3  **중심이 엣지**             → 사지 아님
        s11(분리)   엣지 없음                                            → 사지 아님

    `w_min` — 경계 사이 폭의 하한. **임계가 아니라 [[지표를 정의하는 상수]]**다
    (`judge_style.DARK_CUT`·`judge_s1.ARM_Y_ABS`와 같은 종류). 통과 임계는 여전히 사다리
    양끝의 산술 중점에서 파생하며 손대지 않는다.

    `reach` = 4 × 저작 획 두께. 이것도 콘티에서 파생한다."""
    samples = _centerline(g["ink"])
    reach = 4 * g["r"]
    h, w = g["ink"].shape

    def f(ed):
        ok = 0
        for c, nvec in samples:
            def at(t):
                x, y = int(round(c[0] + t * nvec[0])), int(round(c[1] + t * nvec[1]))
                return bool(ed[y, x]) if (0 <= x < w and 0 <= y < h) else False
            if require_clean_center and at(0):
                continue
            a = next((t for t in range(1, reach + 1) if at(t)), None)
            b = next((t for t in range(1, reach + 1) if at(-t)), None)
            if a is not None and b is not None and a + b >= w_min:
                ok += 1
        return float(ok / len(samples)) if samples else 0.0
    return f


def candidates(g):
    """이름 → (설명, 점수함수(edge_bool) → float, 정의역 마스크)."""
    ink = g["ink"]

    def cov(d):
        def f(ed):
            near = _dilate(ed > 0, d)
            return float(min((s & near).sum() / s.sum() for s in g["strokes"]))
        return f

    return {
        "part_corr": (
            "부위 띠 안 콘티잉크↔엣지 피어슨 상관 — 축 C를 팔에만 적용한 것",
            lambda ed: _corr(ink, ed, g["band"]), g["band"]),
        "part_corr_excl": (
            "배타 띠(다른 부위 띠를 뺀 것) 안 같은 상관",
            lambda ed: _corr(ink, ed, g["band_excl"]), g["band_excl"]),
        "stroke_min_cov2": (
            "콘티 팔 잉크를 엣지가 2px 안에서 덮은 비율(연결성분별 최솟값). **설계 전제가 실측으로 "
            "틀렸다** — 두 획이 5.8px 간격이라 렌더에서 붙어 성분이 1개이므로, 이것은 사실상 "
            "팔 전체 덮힘률이고 얇은 한 줄도 1.000을 낸다",
            cov(2), ink),
        "stroke_min_cov3": (
            "같은 것, 허용 반경 3px",
            cov(3), ink),
        "limb_width": (
            "두께 판정 1차안 — 법선 위 첫 엣지 쌍의 간격이 저작 획 두께(7) 이상인 표본의 비율. "
            "음성 4종을 다 떨어뜨렸으나 **사다리가 깨졌다**: 콘티는 획 두 개(7px·4px)가 겹쳐 "
            "내부에도 엣지가 있어서 자기 자신에게서 폭이 짧게 나온다(양성 0.56 < 알파0.5의 0.64)",
            _limb(g, False, g["r"]), ink),
        "limb_profile": (
            "두께 판정 2차안 — **중심 화소가 엣지가 아니고**(끈은 중심선 위에 얹힌다) 양쪽에 "
            "경계가 있으며 그 간격이 w_min=r−2 이상인 표본의 비율. 「선 위에 엣지가 있는가」가 "
            "아니라 「그 자리에 있는 것이 사지인가」를 묻는다",
            _limb(g, True, g["r"] - 2), ink),
        "collar_cleanliness": (
            "팔 띠 **바깥** 고리(3×획두께)의 엣지 밀도를 뒤집은 값 — 팔 자리를 벗어나 뻗은 "
            "선을 벌한다. 전역판은 §9-23이 폐기했으나(질감을 벌한다) 다윗은 갑주가 없다",
            lambda ed: -float(ed[g["collar"]].mean()), g["collar"]),
    }


def _synthetic_fill(base_path, g):
    """팔 띠를 균일 질감으로 덮은 합성 음성 — 축 C의 「균일채움 합성」과 같은 종류의 구조적 음성.
    루프가 만든 실패작이 아니므로 Goodhart 검사용으로 계보가 다르다(회고 `260830-093209`)."""
    a = np.asarray(js1._axis_c_load(base_path)).copy()
    yy, xx = np.mgrid[:params.SCENE_SIZE[1], :params.SCENE_SIZE[0]]
    tex = np.stack([(((yy // 4 + xx // 4) % 2) * 90 + 90).astype(np.uint8)] * 3, -1)
    fill = g["band"]
    a[fill] = tex[fill]
    return Image.fromarray(a)


def main():
    g = geometry()
    cands = candidates(g)
    f3 = js1.FINAL3
    approved = "3-final-ip0.0-cn0.6-fcn0.8-sip0.9-s%s.png"

    pos_path = os.path.join(js1.CONTI, f"{WHO}.png")
    neg_ladder_path = js1.NEG_AXIS_C          # 배경만 — 축 C의 사다리 음성과 같은 자산
    controls = {
        "neg_a_separated": (os.path.join(f3, approved % "11"),
                            "승인본 s11 — 팔이 차렷으로 내려오고 물매가 허공에 떴다(분리)"),
        "neg_b_pierced": (os.path.join(f3, approved % "7"),
                          "승인본 s7 — 물매 끈이 팔 회랑을 한 줄로 지나간다(관통)"),
        "neg_c_bg_only": (neg_ladder_path, "배경만 — 인물 부재. 루프 밖 계보의 음성"),
        "pos_conti": (pos_path, "콘티 잉크 자신 — 양성 상한"),
    }
    for _, (p, _why) in controls.items():
        if not os.path.exists(p):
            raise SystemExit(f"대조군 자산이 없다: {p}")

    ed_of = {k: js1._edge_bool_f(js1._axis_c_load(p)) for k, (p, _w) in controls.items()}
    ed_of["neg_d_synth_fill"] = js1._edge_bool_f(_synthetic_fill(neg_ladder_path, g))
    controls["neg_d_synth_fill"] = (f"<합성> {os.path.basename(neg_ladder_path)} + 팔 띠 균일채움",
                                    "팔 띠를 덩어리로 채운 합성 — 콘티 선 자리에 엣지를 안 만든다")

    pos_im, neg_im = js1._axis_c_load(pos_path), js1._axis_c_load(neg_ladder_path)
    ladder_ed = {a: js1._edge_bool_f(Image.blend(neg_im, pos_im, a)) for a in ja.LADDER}

    out = {}
    for name, (why, fn, domain) in cands.items():
        by_alpha = {a: fn(ladder_ed[a]) for a in ja.LADDER}
        vals = [by_alpha[a] for a in ja.LADDER]
        mono = all(vals[i] <= vals[i + 1] for i in range(len(vals) - 1))
        neg_v, pos_v = by_alpha[0.0], by_alpha[1.0]
        thr = (neg_v + pos_v) / 2      # 축 C·D와 같은 산술 중점 — 손으로 고르지 않는다
        scores = {k: fn(ed) for k, ed in ed_of.items()}
        passes = {k: bool(v > thr) for k, v in scores.items()}
        out[name] = {
            "description": why,
            "domain_px": int(domain.sum()),      # 정의역 규칙(ARM.md) — 0이면 채택 불가
            "ladder": {str(a): by_alpha[a] for a in ja.LADDER},
            "ladder_monotonic": bool(mono),
            "threshold": thr,
            "scores": scores, "passes": passes,
            "verdict": {
                "neg_a_rejected": not passes["neg_a_separated"],
                "neg_b_rejected": not passes["neg_b_pierced"],
                "neg_c_rejected": not passes["neg_c_bg_only"],
                "neg_d_rejected": not passes["neg_d_synth_fill"],
                "pos_passed": passes["pos_conti"],
                "ladder_monotonic": bool(mono),
            },
        }
        v = out[name]["verdict"]
        out[name]["adopted"] = bool(all(v.values()) and out[name]["domain_px"] > 0)

    result = {
        "part": PART,
        "controls": {k: {"path": p, "label": w} for k, (p, w) in controls.items()},
        "threshold_rule": "음성(배경만)과 양성(콘티)의 사다리 양끝 산술 중점 — 축 C·D와 같은 규약",
        "ladder": "judge_axes.LADDER — 음성·양성을 alpha 합성. 파일명으로 기각하는 가짜 판정자는 "
                  "합성 중간 이미지에서 단조를 낼 수 없다(하드코딩 방지)",
        "adoption_rule": "음성 4종 전부 기각 + 양성 통과 + 사다리 단조 + 정의역 화소 > 0",
        "candidates": out,
        "adopted": [k for k, v in out.items() if v["adopted"]],
    }

    path = sys.argv[sys.argv.index("--json") + 1] if "--json" in sys.argv else DEFAULT_JSON
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)

    print(f"팔 부위 {PART} · 획 {len(g['strokes'])}개 · 띠 {int(g['band'].sum())}화소")
    print("=" * 100)
    hdr = f"{'후보':22s} {'정의역':>7s} {'음성A':>8s} {'음성B':>8s} {'음성C':>8s} {'음성D':>8s} {'양성':>8s} {'단조':>5s} {'채택':>5s}"
    print(hdr)
    for name, d in out.items():
        v, s = d["verdict"], d["scores"]
        def m(key, ok):
            return f"{s[key]:+.3f}{'✓' if ok else '✗'}"
        print(f"{name:22s} {d['domain_px']:7d} "
              f"{m('neg_a_separated', v['neg_a_rejected']):>9s} "
              f"{m('neg_b_pierced', v['neg_b_rejected']):>9s} "
              f"{m('neg_c_bg_only', v['neg_c_rejected']):>9s} "
              f"{m('neg_d_synth_fill', v['neg_d_rejected']):>9s} "
              f"{m('pos_conti', v['pos_passed']):>9s} "
              f"{'OK' if v['ladder_monotonic'] else 'FAIL':>5s} "
              f"{'채택' if d['adopted'] else '기각':>5s}   임계 {d['threshold']:+.4f}")
    print("=" * 100)
    print(f"기록: {path}")
    print(f"채택 가능 후보: {result['adopted'] or '없음 — 전멸'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
