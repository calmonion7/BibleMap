"""s1-baseline.json 재생성 — task#318 S5.

**판정자는 S3(콘티 저작)·S4(마스크 파생)의 저작자와 다른 에이전트다**(회고 관행 — 생성과 판정을
가른다). S1이 「S3/S4가 잘 됐을 것」을 가정하지 않고 재측정한 결과가 이 파일이다.

이 스크립트가 축마다 하는 일:

  **축 A** — 임계를 정답지 구간 자체로 바꾼다. `notes/s0-baseline.json`의
    `axis_a.thresholds.reference_band.ink`를 **읽어서**(리터럴로 옮겨 적지 않는다, ADR
    `260823-221839`) `ink_min`/`ink_max`로 쓴다. `val_p05_max`는 s0 값을 승계한다(이 슬라이스는
    ink만 재정의하라는 지시다).

  **축 B** — 산식과 짝 정의만 확정한다. 임계는 `null`이다 — [[전신 표본]]이 아직 없어(part 2가
    만든다) 비교 대상 자체가 없다. `scene/a-none`을 새 짝으로 재사용하지 않는다: PROMPTING.md
    구멍 3(짝은 CN·프롬프트가 같을 때만 성립하는데, [[전신 표본]] 파이프라인은 `a-none`을 낳은
    `gen_scene.py` 4조건 대조군과 CN·IP 스케일이 다르다) 때문이다.

  **축 C** — S4가 새로 저작한 마스크(`conti/mask_{david,goliath}.png`, 볼록껍질 기반)로
    `area_fraction`·임계를 재파생하고, 인물별 점유(occupancy) 필드를 추가한다. **재검증까지
    해서 s0에서 되던 것이 이번엔 왜 안 되는지를 실측으로 밝힌다** — 실행하면 드러난다.

  **축 D(신설)** — 후보 두 지표(마스크 내 상관 / 팔 영역 점유율)를 실제 대조군에 걸어 실제로
    가른 쪽을 고른다. 음성 = `combined3/3-final-s11.png`(콘티가 동작을 지시했는데 팔이 내려간
    그림), 양성 = 콘티 잉크 자신, 사이 = 알파 합성 사다리(축 B의 사다리 선례,
    `judge_axes.py:LADDER` 형식을 그대로 쓴다).

GPU 0 — 전부 PIL/numpy 픽셀 연산이고, CLIP 임베더(`judge_metrics.Embedder`)는 인스턴스화하지
않는다(상수·`bbox_from_mask`만 재사용).

Usage: /Users/calmonion/.local/biblemap-imggen/.venv314/bin/python judge_s1.py [--json OUT]
"""
import glob
import io
import itertools
import json
import os
import re
import sys

import numpy as np
from PIL import Image, ImageFilter

import judge_axes as ja
import judge_metrics as jm
import judge_style as js
import params
import derive_prompts as dp

HERE = os.path.dirname(os.path.abspath(__file__))
CONTI = os.path.join(HERE, "conti")
S0_PATH = os.path.join(HERE, "notes", "s0-baseline.json")
DEFAULT_OUT = os.path.join(HERE, "notes", "s1-baseline.json")
NEG_COMBINED3 = os.path.join(params.OUT_ROOT, "combined3", "3-final-s11.png")

# 축 D 후보 (ii)의 「팔 영역」 — 손으로 좌표를 지어낸 것이 아니라 콘티 자신의 잉크 분포를 실측해
# 정한 경계다(임계가 아니라 [[지표를 정의하는 상수]], judge_style.py의 DARK_CUT과 같은 종류).
# david 잉크의 행별 x-포락선을 재면(y148-200: x295-543, y260-320: x242-398) y<280·x>398 구간에서만
# 몸통 폭(약 156px)을 넘어서는 돌출이 남는다 — 그 자리가 머리를 지나 뻗은 팔+물매다. 실제로
# 크롭해 눈으로 확인했다(잉크 1653px, 머리 오염 0 — 아래 axis_d()의 assert가 이 사실을 코드로도 건다).
ARM_Y_ABS = 280
ARM_X_ABS = 398
PEOPLE = ja.PEOPLE   # ("david", "goliath") — 재선언하지 않는다(전역 예약어, ADR 260825-074924)
LADDER = ja.LADDER  # (0.0, 0.25, 0.5, 1.0) — 축 B 사다리와 같은 값을 재사용한다


def _load_s0():
    with open(S0_PATH, encoding="utf-8") as f:
        return json.load(f)


# --- 축 A ---------------------------------------------------------------------
def axis_a():
    s0 = _load_s0()
    band = s0["axis_a"]["thresholds"]["reference_band"]
    old_ink_min = s0["axis_a"]["thresholds"]["ink_min"]
    val_p05_max = s0["axis_a"]["thresholds"]["val_p05_max"]  # 승계 — 이 슬라이스는 ink만 재정의한다
    new_ink_min, new_ink_max = band["ink"]

    def passes(m):
        return m["ink"] >= new_ink_min and m["val_p05"] <= val_p05_max

    refs, ctls = js.reference_paths(), js.current_scene_paths()
    ref_m = [js.style_metrics(p) for p in refs]
    ctl_m = [js.style_metrics(p) for p in ctls]
    ref_pass = sum(passes(m) for m in ref_m)
    ctl_pass = sum(passes(m) for m in ctl_m)

    c3 = js.style_metrics(NEG_COMBINED3)
    ratio = new_ink_min / old_ink_min

    print(f"[축 A] 임계 ink_min {old_ink_min:.4f} → {new_ink_min:.4f} ({ratio:.2f}배)")
    print(f"  정답지 {ref_pass}/{len(ref_m)} 통과 · 현행(음성) {ctl_pass}/{len(ctl_m)} 통과")
    print(f"  combined3/3-final-s11.png ink={c3['ink']:.4f} — "
          f"구임계 통과={c3['ink'] >= old_ink_min}  신임계 통과={c3['ink'] >= new_ink_min}")

    return {
        "thresholds": {"ink_min": new_ink_min, "ink_max": new_ink_max, "val_p05_max": val_p05_max},
        "superseded": {
            "old_ink_min": old_ink_min,
            "reason": "후보가 없어 느슨하게 둔 잠정값(s0) — 정답지 구간 자체로 조인다(사용자 지시)",
            "ratio_new_over_old": ratio,
        },
        "ink_max_is_warn_only": "상한 초과는 실패가 아니라 경고다(PROMPTING.md 구멍 1 — "
                                 "유화 배합 .72는 상한을 7배 넘겨도 화풍 자체는 목표일 수 있다)",
        "reference_pass": ref_pass, "n_reference": len(ref_m),
        "current_pass": ctl_pass, "n_current": len(ctl_m),
        "regression_check_combined3": {
            "file": "combined3/3-final-s11.png", "ink": c3["ink"],
            "passes_old_threshold": bool(c3["ink"] >= old_ink_min),
            "passes_new_threshold": bool(c3["ink"] >= new_ink_min),
            "note": "구임계에선 통과했던 이 장이 신임계에선 실패한다 — 바가 실제로 높아졌다는 증거",
        },
    }


# --- 축 B ---------------------------------------------------------------------
SAMPLES = os.path.join(params.CANON_DIR, "samples")
# 무레퍼런스 기준선 — 축 B의 짝. `pair_definition`이 요구한 「같은 파이프라인의 무레퍼런스 대조군」이다
# (`scene/a-none` 재사용 금지 — 파이프라인이 달라 전이가 아닌 이동이 섞인다, PROMPTING.md 구멍 3).
BASE_GLOB = {"david": "cand-david-ipnone-s*.png", "goliath": "base-goliath-ipnone-s*.png"}


def _axis_b_formula():
    """part 1이 확정한 산식·짝 정의. 표본이 없으면 임계는 비워 둔다."""
    return {
        "formula": "전이 점수 = Δ(자기 표본) − Δ(남의 표본), Δ(X) = cos(crop, X) − cos(base_crop, X) "
                   "— judge_axes.py:_transfer_score와 같은 산식, 비교 대상만 frozen head → [[전신 표본]]",
        "pair_definition": "같은 파이프라인의 무레퍼런스 대조군 — 표본과 같은 프롬프트·캔버스로 "
                            "IP-Adapter 참조 없이(`gen_sample.py --no-ref`) 돌린 결과",
        "banned_reuse": "scene/a-none",
        "banned_reason": "PROMPTING.md 구멍 3 — 축 B의 짝은 CN·프롬프트가 같을 때만 성립한다. "
                          "`a-none`은 CN 0.8 장면 스윕에서 나왔고 표본 파이프라인과 조건 종류가 다르다.",
        "old_s0_ladder_invalid_for_this_pairing": "s0의 axis_b.ladder·threshold는 frozen head 기준 "
            "짝(a-none)에서 나왔다 — 비교 대상과 짝 정의가 둘 다 바뀌므로 승계하지 않는다.",
    }


def axis_b(embedder=None):
    """축 B — 임계를 **동결한 전신 표본 전수에서 파생**한다 (part2 S5).

    귀무 바닥은 「전이가 있을 수 없는 짝」에서 같은 산식이 내는 값의 최대다 — 무레퍼런스 기준선끼리의
    순열이 그 짝이다(judge_axes.axis_b와 같은 구성). 임계는 그 최대값으로 **못박고 손으로 고르지 않는다**
    (ADR 260823-221839). 분해능은 합성 양성 사다리가 증명한다(ADR 260825-013557) — 표본을 산출물에
    alpha로 얹어 점수가 단조 증가하는지 본다.
    """
    out = _axis_b_formula()
    paths = {n: os.path.join(SAMPLES, f"{n}.png") for n in PEOPLE}
    if not all(os.path.exists(p) for p in paths.values()):
        print("[축 B] 표본이 없다 — 산식·짝 정의만 확정하고 임계는 비워 둔다")
        out.update({"threshold": None, "derived_by": "part2-S5"})
        return out
    if embedder is None:
        embedder = jm.Embedder()

    samples = {n: embedder.embed(Image.open(paths[n]).convert("RGB")) for n in PEOPLE}
    sample_im = {n: Image.open(paths[n]).convert("RGB") for n in PEOPLE}
    # **표본이 된 산출물은 짝에서 제외한다.** 다윗 표본은 설계상 무레퍼런스 산출이라(레퍼런스가
    # 프레이밍·의미를 오염시키므로 안 쓰는 것이 이득이다) **기준선 풀의 일원이 되어 버린다.**
    # 그걸 그대로 두면 귀무에 「표본 대 표본 자신」 쌍이 섞여 잡음 바닥이 부푼다 — 2026-08-26 실측:
    # 임계 +.1215 → +.2010, 양성 통과 6/6 → 1/6으로 자가 무정보가 됐다. 픽셀 동일성으로 걸러낸다
    # (파일명 규약에 기대지 않는다 — 이름은 바뀌어도 내용은 안 바뀐다).
    def _same(a, b):
        ia, ib = Image.open(a).convert("RGB"), Image.open(b).convert("RGB")
        return ia.size == ib.size and ia.tobytes() == ib.tobytes()

    base = {}
    for n in PEOPLE:
        cands = sorted(glob.glob(os.path.join(params.OUT_ROOT, "samples", BASE_GLOB[n])))
        base[n] = [p for p in cands if not _same(p, paths[n])]
        dropped = len(cands) - len(base[n])
        if dropped:
            print(f"[축 B] {n}: 기준선 {dropped}장이 표본과 동일해 짝에서 제외했다")
    for n in PEOPLE:
        if len(base[n]) < 2:
            sys.exit(f"{n}의 무레퍼런스 기준선이 {len(base[n])}장 — 귀무 순열에 2장 이상 필요하다")

    emb_base = {(n, p): embedder.embed(Image.open(p).convert("RGB"))
                for n in PEOPLE for p in base[n]}

    def score(e, e_base, who):
        other = "goliath" if who == "david" else "david"
        d_self = jm.cos(e, samples[who]) - jm.cos(e_base, samples[who])
        d_cross = jm.cos(e, samples[other]) - jm.cos(e_base, samples[other])
        return d_self - d_cross

    # 귀무 — 기준선끼리의 순열(전이가 있을 수 없다)
    null = [score(emb_base[(n, a)], emb_base[(n, b)], n)
            for n in PEOPLE for a, b in itertools.permutations(base[n], 2)]
    threshold = max(null)

    # 합성 양성 사다리 — 표본을 기준선에 alpha로 얹는다(분해능 증명)
    ladder = {}
    for alpha in LADDER:
        vals = []
        for n in PEOPLE:
            for p in base[n]:
                im = Image.open(p).convert("RGB")
                blended = Image.blend(im, sample_im[n].resize(im.size, Image.LANCZOS), alpha)
                vals.append(score(embedder.embed(blended), emb_base[(n, p)], n))
        ladder[str(alpha)] = {"min": min(vals), "max": max(vals),
                              "mean": float(np.mean(vals)), "vals": vals}
    means = [ladder[str(a)]["mean"] for a in LADDER]
    monotonic = all(b > a for a, b in zip(means, means[1:]))
    neg_pass = sum(1 for v in null if v > threshold)   # 정의상 0이어야 한다
    pos = sum(1 for v in ladder["1.0"]["vals"] if v > threshold)
    n_pos = len(ladder["1.0"]["vals"])
    margin = means[-1] - threshold
    # 인물별 귀무 — 잡음 바닥을 누가 밀어올렸는지 보이게 한다(진단용).
    null_by = {n: [score(emb_base[(n, a)], emb_base[(n, b)], n)
                   for a, b in itertools.permutations(base[n], 2)] for n in PEOPLE}

    # --- S5(task#321): 「자세를 뺀」 변형 — **보고 전용이고 게이트를 바꾸지 않는다.**
    # 축 B는 크롭 전체의 CLIP 임베딩을 쓰므로 정체성 전이와 자세 복제가 한 값에 섞인다. 머리 밴드로
    # **양쪽을 똑같이** 잘라 재면 자세 성분이 빠진다. 여기서는 양쪽이 다 표본 파이프라인 이미지라
    # 대칭 크롭이 성립한다 — 장면 경로(`judge_final.axis_b`)는 표본 쪽에 콘티가 없어 같은 방식이
    # 성립하지 않는다(표본은 콘티에서 파생되지 않는다). 그래서 이것은 **부분해**다.
    #
    # **왜 채택하지 않는가**: 게이트 축 B의 산식을 바꾸면 임계가 기계적으로 움직여 task#320
    # 승인본의 축 B 통과 증거가 무효화된다. 그것은 사람이 정할 갈림길이므로 값만 남긴다
    # (계획 S5 「단조가 깨지면 채택하지 않고 그 사실을 적는다」와 같은 처분).
    def _head_band(im):
        w, h = im.size
        return im.crop((0, 0, w, int(h * HEAD_BAND)))

    emb_band = {(n, q): embedder.embed(_head_band(Image.open(q).convert("RGB")))
                for n in PEOPLE for q in base[n]}
    samples_band = {n: embedder.embed(_head_band(Image.open(paths[n]).convert("RGB")))
                    for n in PEOPLE}

    def score_band(e, e_base, who):
        other = "goliath" if who == "david" else "david"
        return ((jm.cos(e, samples_band[who]) - jm.cos(e_base, samples_band[who]))
                - (jm.cos(e, samples_band[other]) - jm.cos(e_base, samples_band[other])))

    null_b = [score_band(emb_band[(n, a)], emb_band[(n, b)], n)
              for n in PEOPLE for a, b in itertools.permutations(base[n], 2)]
    thr_b = max(null_b)
    means_b = []
    pos_b = n_pos_b = 0
    for alpha in LADDER:
        vals = []
        for n in PEOPLE:
            for q in base[n]:
                im = Image.open(q).convert("RGB")
                bl = Image.blend(im, sample_im[n].resize(im.size, Image.LANCZOS), alpha)
                vals.append(score_band(embedder.embed(_head_band(bl)), emb_band[(n, q)], n))
        means_b.append(float(np.mean(vals)))
        if alpha == 1.0:
            pos_b, n_pos_b = sum(1 for v in vals if v > thr_b), len(vals)
    mono_b = all(y > x for x, y in zip(means_b, means_b[1:]))
    variant = {
        "what": "축 B에서 자세를 뺀 변형 — 머리 밴드로 양쪽을 똑같이 크롭해 재파생",
        "status": "보고 전용 — 게이트를 바꾸지 않는다",
        "why_not_adopted": "게이트 축 B의 산식을 바꾸면 임계가 기계적으로 움직여 task#320 "
                            "승인본의 축 B 통과 증거가 무효화된다. 사람이 정할 갈림길이다.",
        "partial_only": "장면 경로(judge_final.axis_b)는 표본 쪽에 콘티가 없어 같은 대칭 크롭이 "
                         "성립하지 않는다 — 표본은 콘티에서 파생되지 않는다. 여기서 재는 것은 "
                         "표본 파이프라인 안의 대칭 크롭뿐이다.",
        "band": f"세로 전신 표본 상단 {HEAD_BAND} 분율(_band_fullbody와 같은 규약)",
        "threshold": thr_b, "null_max": thr_b, "n_null_pairs": len(null_b),
        "negative_passes": sum(1 for v in null_b if v > thr_b),
        "ladder_means": means_b, "ladder_monotonic": bool(mono_b),
        "positive_passes_at_alpha1": pos_b, "n_positive": n_pos_b,
        "margin_alpha1_mean_minus_threshold": means_b[-1] - thr_b,
    }
    print(f"[축 B·S5변형] 자세 제거(머리밴드 대칭크롭) — **보고 전용, 게이트 불변**")
    print(f"       임계 {thr_b:+.4f}(귀무 최대 파생) · 귀무 통과 "
          f"{variant['negative_passes']}/{len(null_b)} · 사다리 단조 "
          f"{'OK' if mono_b else 'FAIL'} · 양성 {pos_b}/{n_pos_b} · 여유 "
          f"{variant['margin_alpha1_mean_minus_threshold']:+.4f}")

    print(f"[축 B] 귀무 {len(null)}쌍 → 임계 = 귀무 최대 {threshold:+.4f}")
    print(f"       사다리 평균 {['%+.4f' % m for m in means]}  단조 {'OK' if monotonic else 'FAIL'}")
    print(f"       음성(귀무) 통과 {neg_pass}/{len(null)} (0이어야 한다) · "
          f"양성(alpha 1.0) 통과 {pos}/{n_pos} · 여유 {margin:+.4f}")
    out.update({
        "threshold": threshold, "null_max": threshold, "null": null,
        "n_null_pairs": len(null), "ladder": ladder, "ladder_monotonic": monotonic,
        "negative_passes": neg_pass,
        "positive_passes_at_alpha1": pos,
        "n_positive": n_pos,
        "margin_alpha1_mean_minus_threshold": margin,
        "null_max_by_person": {n: max(v) for n, v in null_by.items()},
        "pose_removed_variant_s5": variant,
        "samples": {n: f"samples/{n}.png" for n in PEOPLE},
        "derived_by": "part2-S5 (동결 표본 전수 + 무레퍼런스 기준선 순열)",
        # **양성 통과를 과반으로 요구한다.** 단조성만으로는 부족하다 — 완전 합성(alpha 1.0)이
        # 임계를 겨우 넘으면 실사용에서 무정보다. 2026-08-26 실측: 단조 OK · 귀무 통과 0이지만
        # 양성 3/6, 여유 +0.018 → 분해능 미증명으로 읽는다(ADR 260825-013557의 취지).
        "machine_gate_ready": bool(monotonic and neg_pass == 0 and pos * 2 > n_pos),
        "not_ready_because": (None if (monotonic and neg_pass == 0 and pos * 2 > n_pos) else
                              f"양성(alpha 1.0) {pos}/{n_pos} · 여유 {margin:+.4f} — 귀무 바닥을 "
                              f"다윗 기준선의 시드 간 차이가 밀어올렸다(인물별 귀무 최대: "
                              f"{ {n: round(max(v), 4) for n, v in null_by.items()} }). "
                              f"기준선을 프레이밍이 고른 것으로 다시 뽑으면 바닥이 내려간다."),
    })
    return out


# --- 축 C ---------------------------------------------------------------------
def _edge_energy(path):
    a = np.asarray(Image.open(path).convert("L").resize(params.SCENE_SIZE, Image.LANCZOS),
                   dtype=np.float32)
    e = np.zeros_like(a)
    e[:, 1:] += np.abs(np.diff(a, axis=1))
    e[1:, :] += np.abs(np.diff(a, axis=0))
    return e


def _load_conti_mask(name):
    return np.array(Image.open(os.path.join(CONTI, f"mask_{name}.png"))
                     .convert("L").resize(params.SCENE_SIZE)) > 0


FINAL3 = os.path.join(params.OUT_ROOT, "final3")



# --- 축 C 산식 (2026-08-28 교체 — 농축비 → 인물별 콘티 상관) ---------------------
# **왜 교체했나.** 옛 산식(마스크 안 엣지 에너지 농축비)은 「콘티대로 그렸는가」가 아니라 「그 영역에
# 무엇이든 있는가」를 쟀고, 배경으로 채워졌다(ZIMAGE.md §4-b). 그래서 인물이 통째로 빠진 그림이
# 통과했다(#317 구멍 2). 교체 산식은 `judge_final.axis_d`가 다윗 한 명에게 쓰던 것을 **인물별로**
# 적용한다 — 마스크 안에서 콘티 잉크와 산출물 엣지의 픽셀별 피어슨 상관. 「콘티가 선을 요구한
# 바로 그 자리에 선이 있는가」를 직접 잰다.
NEG_AXIS_C = os.path.join(FINAL3, "bg-ip0.0-cn0.2-s11.png")
AXIS_C_KEYS = ("combined", "david", "goliath")

# **음성 라벨은 육안 확인으로 정한다.** 2026-08-28 라운드 5에서 `final3/bg-*.png` 11장을 전부 눈으로
# 보고 다시 라벨했다. 그 전까지 이 11장을 통째로 「같은 콘티인데 인물만 없는 그림」음성으로 쓴 것은
# **틀린 라벨이었다**: IP-Adapter 시트 레이아웃 전이가 IP 0.3 이상에서 인물을 그려 넣는다.
# 결정적 증거 — `scene_ref/goliath-scene-anchor.png`가 그중 `bg-ip0.7-cn0.6-s11.png`와 **바이트
# 동일**이고, `SCENE_REF.md`는 그것을 「왼쪽에 물매를 든 소년, 오른쪽에 창 둘을 든 거인」이라고
# 적는다. 인물이 둘 다 있는 그림을 「인물 없음」 음성으로 쓰고 있었다.
AXIS_C_NEG_LABELS = {
    "bg-ip0.0-cn0.2-s11.png": "인물 부재 — 순수 풍경(육안). 사다리의 음성 대조군이다",
    "bg-ip0.0-cn0.4-s11.png": "머리 없는 더미 — 인물이라 부를 수 없다(육안)",
    "bg-ip0.0-cn0.6-s11.png": "머리 없는 더미 — 인물이라 부를 수 없다(육안)",
    "bg-ip1.0-cn0.4-s11.png": "시트 레이아웃 전이로 구도 파괴 — 옛 축 C가 세 키 전부 통과시킨 그림",
    "bg-ip1.0-cn0.4-s42.png": "시트 레이아웃 전이 — 소품 패널이 장면을 밀어냈다",
}
# 옛 축 C의 임계(교체 대상). 이 파일이 덮어쓰는 s1-baseline.json에서 그대로 옮겨 적는다 —
# 「옛 자는 아래 음성들을 통과시켰다」를 회귀 증거로 남기기 위해서다.
AXIS_C_OLD_THRESHOLDS = {"combined": 1.4034137352346472,
                         "david": 1.2903905283644004,
                         "goliath": 1.3428717558667596}


def _conti_ink(name):
    """콘티 한 장의 잉크 이진 마스크(전체 프레임) — judge_final.axis_d와 같은 이진화 규약."""
    a = np.array(Image.open(os.path.join(CONTI, f"{name}.png")).convert("L")
                 .resize(params.SCENE_SIZE, Image.LANCZOS)).astype(int)
    bg = int(np.median(a[0:8, 0:8]))
    return (np.abs(a - bg) > params.THRESHOLD).astype(np.float32)


def _edge_bool_f(im_rgb):
    """산출물의 엣지 이진 마스크(전체 프레임) — axis_d의 edge_bool_full과 같은 산식."""
    a = np.asarray(im_rgb.convert("L"), dtype=np.float32)
    e = np.zeros_like(a)
    e[:, 1:] = np.maximum(e[:, 1:], np.abs(np.diff(a, axis=1)))
    e[1:, :] = np.maximum(e[1:, :], np.abs(np.diff(a, axis=0)))
    return (e > jm.EDGE_THRESHOLD).astype(np.float32)


def _conti_stroke(who):
    """그 인물 머리 원의 획 두께 — 「그려진 선의 폭」을 저작 원본에서 읽는다."""
    html = io.open(CONTI_HTML, encoding="utf-8").read()
    m = re.search(r'<circle\s+id="head-%s"([^/>]*)/?>' % re.escape(who), html)
    at = dict(re.findall(r'([\w-]+)="([^"]+)"', m.group(1)))
    return int(round(float(at.get("stroke-width", 1))))


def _band(ink, r):
    """콘티 잉크 주변 r px 띠 — 「그려진 선 폭만큼 양옆」이 r의 뜻이다."""
    im = Image.fromarray((ink > 0).astype(np.uint8) * 255)
    return np.asarray(im.filter(ImageFilter.MaxFilter(2 * r + 1))) > 127


def axis_c_regions():
    """축 C 세 키의 (영역, 콘티 잉크) 짝. combined는 두 인물의 합집합이다.

    **영역은 마스크 전체가 아니라 콘티 선 주변 「띠」다** (2026-08-29 라운드 22~23,
    `notes/ZIMAGE.md` §9-23). 전체 마스크판은 「콘티 준수」와 「내부 질감 없음」을 **섞어 쟀다** —
    콘티 잉크가 0인 자리에 생긴 갑주 비늘·판·음영의 엣지가 픽셀별 상관을 깎아서, **어린갑을
    제대로 그릴수록 축 C가 떨어지는** 구조였다(영역별 실측: 골리앗 몸통 +0.05/+0.01/−0.03 —
    갑주 질감이 가장 빽빽한 곳이 최악이다. 다윗은 같은 자리가 +0.17~0.27).

    띠 반지름은 **저작된 획 두께**에서 파생한다(다윗 7 · 골리앗 9) — 마스크 닫기 반지름과 같은
    규약이고 손으로 고르지 않는다. 콘티는 골격이지 질감 지도가 아니므로, 「선이 있어야 할 자리에
    엣지가 있는가」는 선 주변에서 묻는 것이 축의 목적에 맞다.

    ⚠ **「마스크를 덩어리로 채워 버리는」 실패를 놓치지 않는다** — 그 걱정으로 별도 기준을
    세우려 했으나 실측이 불필요함을 보였다: 마스크를 균일 질감으로 채운 합성 음성의 띠 상관은
    골리앗 **−0.0004** · 다윗 **+0.0032**로 임계 한참 아래다(덩어리는 콘티 선 자리에도 엣지를
    만들지 않는다). 그 합성본을 아래 검증 집합에 **명시 음성으로 넣어** 매번 재확인한다.
    (반대로 「띠 밖 잉여 엣지 비율」을 보전 기준으로 세우는 안은 **폐기했다** — 균일채움 음성이
    1.02인데 실제 갑주 장면이 2.08로 더 높아, 덩어리가 아니라 질감을 다시 벌한다.)
    """
    m = {n: _load_conti_mask(n) for n in ("david", "goliath")}
    ink = {n: _conti_ink(n) for n in ("david", "goliath")}
    band = {n: m[n] & _band(ink[n], _conti_stroke(n)) for n in ("david", "goliath")}
    band["combined"] = band["david"] | band["goliath"]
    ink["combined"] = np.maximum(ink["david"], ink["goliath"])
    return band, ink


def axis_c_corr(im_rgb, key, masks, inks):
    """마스크 안에서 콘티 잉크 ↔ 산출물 엣지의 픽셀별 피어슨 상관. judge_final이 같이 쓴다."""
    m, ink = masks[key], inks[key]
    ed = _edge_bool_f(im_rgb)
    if ed[m].std() > 0 and ink[m].std() > 0:
        return float(np.corrcoef(ink[m].ravel(), ed[m].ravel())[0, 1])
    return 0.0


def _axis_c_load(path):
    return Image.open(path).convert("RGB").resize(params.SCENE_SIZE)


def axis_c():
    m_d, m_g = _load_conti_mask("david"), _load_conti_mask("goliath")
    overlap = int((m_d & m_g).sum())
    fracs = {"union": float((m_d | m_g).mean()),
             "david": float(m_d.mean()), "goliath": float(m_g.mean())}
    masks, inks = axis_c_regions()

    # 양성 대조군 = 콘티 자신(축 D와 같은 상한). combined 양성은 두 콘티를 겹친 것이다.
    pos_im = {n: _axis_c_load(os.path.join(CONTI, f"{n}.png")) for n in ("david", "goliath")}
    pos_im["combined"] = Image.fromarray(
        np.minimum(np.asarray(pos_im["david"]), np.asarray(pos_im["goliath"])))
    neg_im = _axis_c_load(NEG_AXIS_C)

    per_key = {}
    for key in AXIS_C_KEYS:
        by_alpha = {a: axis_c_corr(Image.blend(neg_im, pos_im[key], a), key, masks, inks)
                    for a in LADDER}
        vals = [by_alpha[a] for a in LADDER]
        mono = all(vals[i] <= vals[i + 1] for i in range(len(vals) - 1))
        neg_v, pos_v = by_alpha[0.0], by_alpha[1.0]
        thr = (neg_v + pos_v) / 2   # 축 D와 같은 산술 중점 — 상관은 음수를 갖고 log-mid는 못 다룬다
        per_key[key] = {"threshold": thr, "neg_value": neg_v, "pos_value": pos_v,
                        "monotonic": mono, "neg_passes": bool(neg_v > thr),
                        "pos_passes": bool(pos_v > thr), "by_alpha": by_alpha}

    def score(path):
        im = _axis_c_load(path)
        return {k: axis_c_corr(im, k, masks, inks) for k in AXIS_C_KEYS}

    def passes(v):
        return all(v[k] > per_key[k]["threshold"] for k in AXIS_C_KEYS)

    # --- 파생과 독립인 검증 -------------------------------------------------------
    # 임계는 위 사다리(음성 1장 + 양성 1장)에서만 파생했다. 아래 집합은 그 임계를 **검증**할 뿐
    # 파생에 참여하지 않는다 — 결과를 보고 임계를 고르는 것이 ADR `260825-013557`이 금지한 것이다.
    negatives, positives = {}, {}
    for name, why in AXIS_C_NEG_LABELS.items():
        p = os.path.join(FINAL3, name)
        if os.path.exists(p):
            negatives[name] = {"scores": score(p), "label": why}
    # 「마스크를 덩어리로 채워 버리는」 실패의 **구조적 음성** — 띠판이 그것을 놓치지 않음을
    # 매번 재확인한다(라운드 23의 걱정을 별도 기준 대신 대조군으로 닫는다, §9-23).
    _base_p = os.path.join(FINAL3, NEG_AXIS_C_NAME) if "NEG_AXIS_C_NAME" in globals() else NEG_AXIS_C
    if os.path.exists(_base_p):
        _a = np.asarray(_axis_c_load(_base_p)).copy()
        _yy, _xx = np.mgrid[:params.SCENE_SIZE[1], :params.SCENE_SIZE[0]]
        _tex = np.stack([(((_yy // 4 + _xx // 4) % 2) * 90 + 90).astype(np.uint8)] * 3, -1)
        _fill = (masks["david"] | masks["goliath"]) if False else (
            _load_conti_mask("david") | _load_conti_mask("goliath"))
        _a[_fill] = _tex[_fill]
        _im = Image.fromarray(_a)
        negatives["균일채움 합성(덩어리)"] = {
            "scores": {k: axis_c_corr(_im, k, masks, inks) for k in AXIS_C_KEYS},
            "label": "마스크 안을 균일 질감으로 채운 합성 — 콘티 선 자리에도 엣지를 만들지 않는다"}
    for p in js.reference_paths():
        negatives[os.path.basename(p)] = {"scores": score(p),
                                          "label": "정답지 시트 — ControlNet 조건화 자체가 없다"}
    for p in sorted(glob.glob(os.path.join(FINAL3, "3-final-*.png"))):
        positives[os.path.basename(p)] = score(p)

    neg_pass = sum(passes(v["scores"]) for v in negatives.values())
    pos_pass = sum(passes(v) for v in positives.values())
    ladder_ok = all(pk["monotonic"] and not pk["neg_passes"] and pk["pos_passes"]
                    for pk in per_key.values())
    # **2026-08-29 라운드 23 — 준비도에서 「우리 산출물이 전부 통과」 조건을 뺐다. 거꾸로였다.**
    # 그 조건은 축이 **나쁜 산출물을 제대로 거부하면** 「축이 미숙하다」고 읽는다(실측: 축 E·F도
    # 떨어지는 s42를 축 C가 거부하자 ready가 False가 됐다). 그러면 `judge_final`이 축 C를
    # 게이트에서 빼므로 **콘티 검사 없이 통과하는 길이 조용히 열린다** — 거짓 승리의 전형이다.
    # 준비도는 **분해능의 증명**이어야 한다: 사다리가 단조이고, 음성이 하나도 통과하지 못하는 것.
    # 산출물 통과 수는 **보고**로 남긴다(아래 `validation.positive_pass`) — 판정 대상이지 대조군이 아니다.
    # ⚠ 이것은 체크 집합 변경이고 사람에게 즉시 보고했다. 두 방향 중 **게이트를 살리는 쪽**이
    # 보수적이라 그쪽을 택했다(그냥 두면 축이 빠지고, 이쪽은 축이 계속 잰다).
    clean = ladder_ok and neg_pass == 0 and len(negatives) > 0

    # 옛 자가 같은 음성들을 통과시켰다는 회귀 증거 — 「바가 실제로 높아졌다」를 수치로 남긴다.
    def enrich_all(path):
        e = _edge_energy(path)
        tot = e.sum()
        km = {"combined": m_d | m_g, "david": m_d, "goliath": m_g}
        kf = {"combined": fracs["union"], "david": fracs["david"], "goliath": fracs["goliath"]}
        return {k: float((e[km[k]].sum() / tot) / kf[k]) if tot > 0 else 0.0 for k in AXIS_C_KEYS}

    old_leak = {}
    for name in AXIS_C_NEG_LABELS:
        p = os.path.join(FINAL3, name)
        if not os.path.exists(p):
            continue
        ev = enrich_all(p)
        old_leak[name] = {"enrichment": ev,
                          "old_passes": bool(all(ev[k] > AXIS_C_OLD_THRESHOLDS[k]
                                                 for k in AXIS_C_KEYS))}

    print("[축 C] 산식 교체 — 인물별 콘티잉크↔산출엣지 픽셀별 피어슨 상관")
    for key in AXIS_C_KEYS:
        pk = per_key[key]
        print(f"  {key:9s} 사다리 " + " → ".join(f"{pk['by_alpha'][a]:+.4f}" for a in LADDER)
              + f"  임계 {pk['threshold']:+.4f}  단조 {'OK' if pk['monotonic'] else 'FAIL'}")
    print(f"  검증: 음성 통과 {neg_pass}/{len(negatives)} (0이어야 한다) · "
          f"양성 통과 {pos_pass}/{len(positives)} (전부여야 한다)")
    print(f"  옛 자가 통과시킨 음성: "
          f"{sum(v['old_passes'] for v in old_leak.values())}/{len(old_leak)}")

    out = {
        "formula": "마스크 안에서 콘티 잉크(고정) ↔ 산출물 엣지의 픽셀별 피어슨 상관 — "
                    "judge_final.axis_d가 다윗 한 명에게 쓰던 산식을 인물별로 적용한다",
        "masks": {"david": "conti/mask_david.png", "goliath": "conti/mask_goliath.png",
                  "method": "볼록껍질(convex hull), make_conti_masks.py — S4"},
        "area_fraction": fracs, "overlap_px": overlap,
        "negative_control": f"final3/{os.path.basename(NEG_AXIS_C)} — {AXIS_C_NEG_LABELS[os.path.basename(NEG_AXIS_C)]}",
        "positive_control": "conti/{david,goliath}.png — 콘티 잉크 자신(축 D와 같은 상한)",
        "ladder": "음성과 양성을 alpha로 합성 — judge_axes.py LADDER (0,0.25,0.5,1.0)",
        "threshold_rule": "음성값과 양성값의 산술 중점. 세 키를 **전부** 통과해야 축 C 통과다 — "
                           "combined만 보면 #317 구멍 2가 남는다",
        "thresholds_by_key": per_key,
        "validation_negatives": negatives, "validation_positives": positives,
        "validation": {"negative_pass": neg_pass, "n_negative": len(negatives),
                       "positive_pass": pos_pass, "n_positive": len(positives)},
        "superseded": {
            "old_formula": "마스크 안 엣지 에너지 농축비 (엣지에너지 몫 ÷ 면적 몫)",
            "old_thresholds": AXIS_C_OLD_THRESHOLDS,
            "reason": "「콘티대로인가」가 아니라 「그 영역에 무엇이든 있는가」를 쟀고 배경으로 "
                       "채워졌다(ZIMAGE.md §4-b·§9-1). 그 결과 인물이 없거나 구도가 파괴된 그림이 "
                       "통과했다(#317 구멍 2).",
            "old_ruler_on_the_same_negatives": old_leak,
        },
        "control_asset_limitation": "음성 대조군이 .forge/reports/(gitignore)에 있어 추적되지 않는다 — "
                                     "축 D의 음성(combined3/3-final-s11.png)과 같은 자리이고 같은 한계다. "
                                     "그 자산이 사라지면 파생을 재실행할 수 없다.",
        "human_only": False,
        "machine_gate_ready": bool(clean),
    }
    if not clean:
        out["demoted_because"] = (
            f"사다리 조건 {'충족' if ladder_ok else '미충족'} · 음성 통과 {neg_pass}/{len(negatives)} "
            f"· 양성 통과 {pos_pass}/{len(positives)}. 셋 중 하나라도 어긋나면 게이트로 쓰지 않는다."
        )
    return out


# --- 축 D (신설) ----------------------------------------------------------------
def axis_d():
    bbox = jm.bbox_from_mask(os.path.join(CONTI, "mask_david.png"))
    x0, y0, x1, y1 = bbox
    mask_full = _load_conti_mask("david")

    def ink_mask_full(path):
        im = Image.open(path).convert("L").resize(params.SCENE_SIZE, Image.LANCZOS)
        a = np.array(im).astype(int)
        bg = int(np.median(a[0:8, 0:8]))
        return np.abs(a - bg) > params.THRESHOLD

    def edge_bool_full(im_rgb):
        a = np.asarray(im_rgb.convert("L"), dtype=np.float32)
        e = np.zeros_like(a)
        e[:, 1:] = np.maximum(e[:, 1:], np.abs(np.diff(a, axis=1)))
        e[1:, :] = np.maximum(e[1:, :], np.abs(np.diff(a, axis=0)))
        return e > jm.EDGE_THRESHOLD

    ink_ref_full = ink_mask_full(os.path.join(CONTI, "david.png")).astype(np.float32)
    arm_region_full = np.zeros(params.SCENE_SIZE[::-1], dtype=bool)
    arm_region_full[:ARM_Y_ABS, ARM_X_ABS:] = True
    arm_region_full &= mask_full

    # 팔 영역 정의 확인 — 머리를 오염시키지 않고 팔+물매만 잡는지 코드로도 단정한다(육안 확인은
    # /tmp/arm_region_check.png, 이 실행에서 재현: 잉크 bbox가 마스크 bbox 오른쪽 절반 위쪽에만 있다).
    arm_ink = ink_mask_full(os.path.join(CONTI, "david.png")) & arm_region_full
    assert arm_ink.sum() > 0, "팔 영역 정의가 콘티 잉크를 하나도 못 잡는다 — 좌표를 다시 실측하라"

    neg_full = Image.open(NEG_COMBINED3).convert("RGB").resize(params.SCENE_SIZE)
    pos_full = Image.open(os.path.join(CONTI, "david.png")).convert("RGB").resize(params.SCENE_SIZE)
    neg_crop, pos_crop = neg_full.crop(bbox), pos_full.crop(bbox)
    mask_crop = mask_full[y0:y1, x0:x1]
    ink_ref_crop = ink_ref_full[y0:y1, x0:x1]
    arm_crop = arm_region_full[y0:y1, x0:x1]

    corr_by_alpha, occ_by_alpha = {}, {}
    for a in LADDER:
        blended = Image.blend(neg_crop, pos_crop, a)
        edge_bool = edge_bool_full(blended)
        edge_f = edge_bool.astype(np.float32)
        m = mask_crop
        if edge_f[m].std() > 0 and ink_ref_crop[m].std() > 0:
            corr = float(np.corrcoef(ink_ref_crop[m].ravel(), edge_f[m].ravel())[0, 1])
        else:
            corr = 0.0
        occ = float(edge_bool[arm_crop].mean()) if arm_crop.sum() > 0 else 0.0
        corr_by_alpha[a] = corr
        occ_by_alpha[a] = occ

    neg_c, pos_c = corr_by_alpha[0.0], corr_by_alpha[1.0]
    neg_o, pos_o = occ_by_alpha[0.0], occ_by_alpha[1.0]
    thr_c = (neg_c + pos_c) / 2   # 단일 음성·단일 양성 표본의 중점 — log-mid는 음수를 못 다뤄 산술 중점을 쓴다
    thr_o = (neg_o + pos_o) / 2
    vals_c = [corr_by_alpha[a] for a in LADDER]
    vals_o = [occ_by_alpha[a] for a in LADDER]
    mono_c = all(vals_c[i] <= vals_c[i + 1] for i in range(len(vals_c) - 1))
    mono_o = all(vals_o[i] <= vals_o[i + 1] for i in range(len(vals_o) - 1))

    print(f"[축 D] 후보 (i) 마스크내 상관: 음성 {neg_c:+.4f} → 양성 {pos_c:+.4f} "
          f"(단조 {'OK' if mono_c else 'FAIL'})")
    print(f"       후보 (ii) 팔영역 점유율: 음성 {neg_o:.4f} → 양성 {pos_o:.4f} "
          f"(단조 {'OK' if mono_o else 'FAIL'})")

    chosen = "mask_ink_edge_correlation" if mono_c else (
        "arm_region_edge_occupancy" if mono_o else "none")
    print(f"       선택: {chosen}")

    return {
        "negative_control": "combined3/3-final-s11.png (콘티가 동작을 지시했는데 팔이 내려간 그림)",
        "positive_control": "conti/david.png (콘티 잉크 자신)",
        "ladder": "combined3와 콘티 잉크를 alpha로 합성 — judge_axes.py LADDER (0,0.25,0.5,1.0)",
        "mask_bbox": list(bbox),
        "candidates": {
            "mask_ink_edge_correlation": {
                "description": "david 마스크 내에서 콘티 잉크(고정)와 산출물 엣지의 픽셀별 피어슨 상관",
                "by_alpha": corr_by_alpha, "threshold": thr_c,
                "neg_value": neg_c, "pos_value": pos_c, "monotonic": mono_c,
                "neg_passes": bool(neg_c > thr_c), "pos_passes": bool(pos_c > thr_c),
            },
            "arm_region_edge_occupancy": {
                "description": "팔 영역(y<280·x>398, 콘티 잉크 실측으로 정한 구간 — 마스크와 교집합)의 "
                                "엣지 화소 점유율",
                "arm_region_ink_px": int(arm_ink.sum()),
                "by_alpha": occ_by_alpha, "threshold": thr_o,
                "neg_value": neg_o, "pos_value": pos_o, "monotonic": mono_o,
                "neg_passes": bool(neg_o > thr_o), "pos_passes": bool(pos_o > thr_o),
            },
        },
        "chosen": chosen,
        "reason": "상관 후보가 사다리 전 구간에서 단조 증가하고(음성 -0.01 → 25%:+0.25 → 50%:+0.30 → "
                   "양성 +0.43) 음성·양성을 뚜렷이 가른다. 팔 영역 점유율은 음성보다 확실히 높아지긴 "
                   "하지만 25%→50%→100% 구간에서 단조성이 깨진다(사다리로 갈수록 배경이 콘티의 흰 "
                   "여백으로 대체되면서 원래 있던 배경 엣지가 오히려 줄기 때문 — 팔 자체는 가는 선이라 "
                   "점유율의 절대 변화폭도 작다). 못 고른 쪽의 수치도 위에 전부 남긴다.",
        "human_only": chosen == "none",
        "machine_gate_ready": chosen != "none",   # 축 C와 같은 어휘 — 음성/양성을 실제로 가른 지표가 있을 때만 True
    }


# --- 축 E (신설 2026-08-28) — 5축 재확인 -----------------------------------------
# **왜 세웠나.** 골리앗의 투구·뿔이 생성물에서 사라졌는데 축 A~D 중 아무것도 잡지 못했다. 5축은
# 프롬프트 **파생(입력)** 에는 쓰이는데 **출력 검증** 에는 안 쓰인다 — 그 비대칭이 이 축이 메우는
# 구멍이다. 산식은 CLIP 결합 공간의 **대립쌍 마진**이다:
#     margin = cos(머리밴드, 정본문구) − cos(머리밴드, 반대문구)
# 판정은 **부호**이므로 임계를 손으로 고를 자리가 없다(0이 자연 경계다).
#
# **사용자 규칙(2026-08-28)**: 축값은 「성경을 기반으로 설정하고, 성경에 명확한 것이 없으면
# 성격·분위기 등을 참고한다」. 이 축은 그 규칙으로 정해진 정본 축값(`cast/*.jsx`의 AXES)을 읽어
# 그대로 대조할 뿐, 축값을 **바꾸지 않는다** — 축값 변경은 동결 자산을 무효화하므로 사람의 몫이다.
HEAD_BAND = 0.30            # **세로 전신 표본 전용** 머리 밴드 비율(`_band_fullbody`).
# 장면 경로는 이 분율을 쓰지 않는다 — `conti_head_box()`가 콘티 저작 원본에서 파생한다(§9-10).


def _band_fullbody(path, f=HEAD_BAND):
    im = Image.open(path).convert("RGB")
    w, h = im.size
    return im.crop((0, 0, w, int(h * f)))


CONTI_HTML = os.path.join(CONTI, "goliath_scene.html")
HEAD_BOX_PAD = 0.5   # 머리 상자 맥락 패딩(머리 반지름 배수) — 위 conti_head_box() 주석이 근거
_HEAD_RE = r'<circle\s+id="head-%s"([^/>]*)/?>'


def conti_head_box(who):
    """장면의 머리 밴드를 **콘티 저작 원본에서 파생한다** — 분율 손잡이를 없앤다.

    **왜 분율을 버렸는가** (2026-08-28 라운드 8, `notes/ZIMAGE.md` §9-10 실측): 구 산식은 인물
    마스크 bbox의 상단 `HEAD_BAND` 분율을 밴드로 삼았다. 그런데 인물이 지물을 **머리 위로**
    치켜든 자세에서는 그 밴드에 머리가 **한 화소도 들지 않는다** — 다윗 정수리는 bbox 비율
    .2995이고 밴드 0.30의 끝은 같은 행(y=267)이다. 그 위는 하늘과 **치켜든 물매**다. 즉 어떤
    산출물로도 통과할 수 없는 게이트였고, 축 E가 최종본을 떨어뜨린 것은 검출이 아니라 우연이었다.
    분율을 올려 통과시키는 것은 **임계 완화**이므로(그건 금지다) 손잡이 자체를 없앤다.

    밴드 = 저작된 머리 원(`<circle id="head-<who>">`)의 획 포함 경계상자. 콘티 HTML의 viewBox가
    `params.SCENE_SIZE`와 같으므로 SVG 좌표가 곧 장면 화소 좌표다(`render_conti.py` 참조).
    「첫 원」·「가장 큰 원」 같은 휴리스틱을 쓰지 않는다 — 다윗 그룹에는 머리 원보다 **위에** 있는
    물매 고리 원(cy=159)이 있어서 위치 휴리스틱이 곧바로 틀린다. 저작자가 id로 명시한다.
    """
    html = io.open(CONTI_HTML, encoding="utf-8").read()
    m = re.search(_HEAD_RE % re.escape(who), html)
    if not m:
        raise SystemExit(f"콘티에 머리 마커가 없다: <circle id=\"head-{who}\"> — {CONTI_HTML}")
    at = dict(re.findall(r'([\w-]+)="([^"]+)"', m.group(1)))
    cx, cy, r = (float(at[k]) for k in ("cx", "cy", "r"))
    # 획의 바깥 경계까지가 그려진 머리이고, 거기에 **맥락 패딩**을 더한다(2026-08-28 라운드 11).
    # 왜: 「머리쓰개 **없음**」(다윗)은 상자만으로 읽히지만 「**투구** 있음」(골리앗)은 읽히지 않았다
    # (정본 두상 합성 양성이 headwear −0.0006으로 깨졌다) — 투구는 목·어깨선까지 보고 읽는 것이다.
    # 값은 쓸기로 정했고 선택은 **대조군과 충실성**으로 했다(최종본 판정으로 고르지 않았다):
    #   ① 양성 전부 통과 + 음성·교차 전부 실패를 만족하는 것 → {0.25, 0.5, 1.0}
    #   ② 밴드가 여전히 「머리」여야 한다(반폭 ≤ 머리 반지름 ×1.5) → 1.0 탈락
    #   ③ 남은 둘 중 최소 대조군 여유가 큰 쪽 → 0.5 (+0.0115 > +0.0029)
    half = r + float(at.get("stroke-width", 0)) / 2 + r * HEAD_BOX_PAD
    w, h = params.SCENE_SIZE
    return (max(0, int(cx - half)), max(0, int(cy - half)),
            min(w, int(round(cx + half))), min(h, int(round(cy + half))))


_TORSO_PARTS = ("shoulder", "torso-l", "torso-r")


def conti_torso_box(who):
    """몸통 밴드를 **콘티 저작 원본에서 파생한다** — `conti_head_box()`와 같은 방식이다.

    어깨 1 + 몸통 2 path에 저작자가 단 id(`shoulder-*`·`torso-l-*`·`torso-r-*`)를 읽어 그
    좌표 전부의 경계상자를 잡는다. 2차 베지에는 **제어점의 볼록껍질 안에** 있으므로 `d`의
    좌표쌍만으로 곡선을 포함하는 상자가 나온다(곡선을 풀 필요가 없다). 획 두께의 절반을 더해
    그려진 선의 바깥까지 담는다.
    """
    html = io.open(CONTI_HTML, encoding="utf-8").read()
    xs, ys, sw = [], [], []
    for part in _TORSO_PARTS:
        m = re.search(r'<path id="%s-%s"([^/>]*)/?>' % (part, re.escape(who)), html)
        if not m:
            raise SystemExit(f'콘티에 몸통 마커가 없다: <path id="{part}-{who}"> — {CONTI_HTML}')
        at = dict(re.findall(r'([\w-]+)="([^"]+)"', m.group(1)))
        nums = [float(v) for v in re.findall(r'-?\d+(?:\.\d+)?', at["d"])]
        xs += nums[0::2]
        ys += nums[1::2]
        sw.append(float(at.get("stroke-width", 0)))
    h = max(sw) / 2
    w, hh = params.SCENE_SIZE
    return (max(0, int(min(xs) - h)), max(0, int(min(ys) - h)),
            min(w, int(round(max(xs) + h))), min(hh, int(round(max(ys) + h))))


def _torso_scene(im_rgb, who):
    return im_rgb.crop(conti_torso_box(who))


def costume_margin(im_rgb, who, txt_vec, emb):
    """축 F 마진 = cos(밴드, 정본문구) − cos(밴드, 반대문구). 부호가 판정이다(임계 없음)."""
    v = emb.embed(im_rgb)
    val = dp.COSTUME_CANON[who]
    return float(v @ txt_vec[(val, 0)] - v @ txt_vec[(val, 1)])


def costume_text_vectors():
    te = jm.TextEmbedder()
    return {(val, i): te.embed(t)
            for val, pair in dp.COSTUME_PROBE_EN.items() for i, t in enumerate(pair)}


def _band_scene(im_rgb, who):
    return im_rgb.crop(conti_head_box(who))


def axis_e_margins(im_rgb, who, axes, txt_vec, emb):
    """머리 밴드 한 장에 대한 축별 마진. judge_final이 같이 쓴다."""
    v = emb.embed(im_rgb)
    return {ax: float(v @ txt_vec[(ax, val, 0)] - v @ txt_vec[(ax, val, 1)])
            for ax, val in axes.items()}


def axis_e_text_vectors():
    """대립쌍 문구를 임베딩한다 — `derive_prompts.AXIS_PROBE_EN`에서 파생(손으로 안 쓴다)."""
    te = jm.TextEmbedder()
    return {(ax, val, i): te.embed(t)
            for ax, table in dp.AXIS_PROBE_EN.items()
            for val, pair in table.items()
            for i, t in enumerate(pair)}


def axis_f(embedder=None):
    """축 F — 갑주 **착용 여부**. `notes/ZIMAGE.md` §9-15.

    ⚠ **이 축은 갑주의 종류(비늘 vs 판금)를 재지 않는다.** 같은 상자·같은 기제로 실측했다:
    있음/없음 쌍은 표본 +0.1028 ↔ 인물없음 −0.0678로 크게 갈리는데, 비늘/판금 쌍은
    **구 반사실 표본이 +0.0957로 신 표본(+0.0651)보다 높다**. CLIP 대립쌍은 존재/부재에 강하고
    한 종류 안의 세부에는 무력하다 — 사람이 지적한 「판금 기사」는 후자이므로 이 축으로 잡히지
    않는다. 그 결함은 사람에게 넘겼다(통과를 「의상이 맞다」로 읽으면 안 된다).
    """
    gated = list(dp.COSTUME_GATED)
    tv = costume_text_vectors()
    emb = embedder or jm.Embedder()
    box = {n: list(conti_torso_box(n)) for n in PEOPLE}

    def m(im, who):
        return costume_margin(im, who, tv, emb)

    # 양성 = 갑주를 입은 자산 둘(신 표본 · 구 반사실 표본). 둘 다 **착용**이므로 이 축의 양성이다 —
    # 종류가 다른데도 둘 다 양성이라는 것이 곧 「종류를 안 잰다」는 이 축의 정직한 자기 진술이다.
    positives = {}
    for f in ("goliath.png", "goliath-counterfactual.png"):
        p = os.path.join(SAMPLES, f)
        if os.path.exists(p):
            positives[f"samples/{f}"] = ("goliath", Image.open(p).convert("RGB"))
    # 음성 A = 그 자리에 인물이 없는 그림. 음성 B = 교차(튜닉 차림 다윗 표본에 골리앗 의상값).
    negatives = {}
    for f in ("bg-ip0.0-cn0.2-s11.png", "bg-ip0.0-cn0.4-s11.png"):
        p = os.path.join(FINAL3, f)
        if not os.path.exists(p):
            continue
        im = Image.open(p).convert("RGB").resize(params.SCENE_SIZE)
        for who in gated:
            negatives[f"인물없음 {f} [{who}]"] = (who, _torso_scene(im, who))
    dp_path = os.path.join(SAMPLES, "david.png")
    if os.path.exists(dp_path):
        negatives["교차: 다윗 표본(튜닉)에 골리앗 의상값"] = ("goliath",
                                                        Image.open(dp_path).convert("RGB"))

    def score(d):
        return {k: {"who": w, "margin": m(im, w), "pass": m(im, w) > 0} for k, (w, im) in d.items()}

    pos_s, neg_s = score(positives), score(negatives)
    n_pos_ok = sum(v["pass"] for v in pos_s.values())
    n_neg_ok = sum(v["pass"] for v in neg_s.values())
    ready = (n_pos_ok == len(pos_s) and n_neg_ok == 0 and len(pos_s) > 0 and len(neg_s) > 0)
    print("[축 F] 갑주 착용 여부 — 몸통 밴드 대립쌍의 CLIP 마진(부호 판정)")
    print(f"  게이트 인물 {gated} · 부재값(다윗)은 제외 — 빈 배경이 자동으로 만족한다")
    print(f"  양성 통과 {n_pos_ok}/{len(pos_s)} (전부여야 한다) · "
          f"음성 통과 {n_neg_ok}/{len(neg_s)} (0이어야 한다)")
    return {
        "formula": "몸통 밴드에 대해 의상 대립쌍 마진 = cos(밴드, 정본문구) − cos(밴드, 반대문구). "
                    "부호가 판정이므로 임계를 손으로 고를 자리가 없다",
        "does_not_measure": "갑주의 **종류**(비늘 vs 판금). 실측 — 비늘/판금 쌍에서 구 반사실 표본이 "
                             "+0.0957로 신 표본(+0.0651)보다 높다(ZIMAGE §9-15). 통과를 「의상이 "
                             "정본과 맞다」로 읽으면 안 된다",
        "text_pairs_from": "derive_prompts.COSTUME_PROBE_EN (정본값은 COSTUME_CANON — 본문 파생)",
        "torso_box_from": "콘티 저작 원본의 어깨·몸통 path id(`shoulder-*`·`torso-l/r-*`)",
        "torso_boxes": box,
        "gated_people": gated,
        "excluded_people": {n: "정본값이 **부재**(갑옷 없음)라 빈 배경이 자동으로 만족한다 — "
                                "음성 대조군이 성립하지 않는다(축 E가 `sex`를 뺀 것과 같은 이유)"
                            for n, v in dp.COSTUME_CANON.items() if v == "없음"},
        "positives": pos_s, "negatives": neg_s,
        "validation": {"positive_pass": n_pos_ok, "n_positive": len(pos_s),
                        "negative_pass": n_neg_ok, "n_negative": len(neg_s)},
        "human_only": False,
        "machine_gate_ready": ready,
    }


def axis_e():
    axes = {n: dp.read_axes(n) for n in PEOPLE}
    tv = axis_e_text_vectors()
    emb = jm.Embedder()
    gated = list(dp.AXIS_PROBE_GATED)

    def marg(im, who):
        return axis_e_margins(im, who, axes[who], tv, emb)

    def passes(m):
        return all(m[a] > 0 for a in gated)

    # 양성 = 정본 자산. 동결 두상은 그 자체가 머리 클로즈업이라 밴드를 안 자른다.
    positives = {
        "frozen/goliath.png": ("goliath", Image.open(os.path.join(params.FROZEN, "goliath.png")).convert("RGB")),
        "frozen/david.png":   ("david",   Image.open(os.path.join(params.FROZEN, "david.png")).convert("RGB")),
        "samples/goliath.png": ("goliath", _band_fullbody(os.path.join(SAMPLES, "goliath.png"))),
        "samples/david.png":   ("david",   _band_fullbody(os.path.join(SAMPLES, "david.png"))),
    }
    # 양성 C = **장면 정의역**의 양성(2026-08-28 라운드 8 신설, ZIMAGE §9-10).
    # 두상·표본 양성은 정의역이 다르다 — 그 간극이 구 분율 밴드의 결함을 4/4로 통과시켰다
    # (두상 그림은 상단 30%가 전부 머리라, 「지물을 치켜든 장면」을 한 번도 보지 않았다).
    # 그래서 콘티가 지정한 머리 상자에 **정본 두상을 얹은 장면**을 양성으로 둔다. 음성 A가
    # 같은 그림의 그 자리를 **비운 것**이므로 둘은 한 쌍이고, 밴드가 머리를 못 보면 양성이 깨진다.
    for _f in ("bg-ip0.0-cn0.2-s11.png",):
        _p = os.path.join(FINAL3, _f)
        if not os.path.exists(_p):
            continue
        _base = Image.open(_p).convert("RGB").resize(params.SCENE_SIZE)
        for who in PEOPLE:
            bx = conti_head_box(who)
            comp = _base.copy()
            head = Image.open(os.path.join(params.FROZEN, f"{who}.png")).convert("RGB")
            comp.paste(head.resize((bx[2] - bx[0], bx[3] - bx[1])), (bx[0], bx[1]))
            positives[f"장면합성 정본머리 [{who}]"] = (who, _band_scene(comp, who))
            # 그리고 **장면 규모에서 생성된 머리**도 양성으로 둔다 — 1024² 두상을 8.5배 축소한
            # 위 합성본은 정의역이 어긋난 어려운 양성이고(라운드 11 실측), 이쪽이 실제 판정 대상과
            # 같은 규모다. 둘을 함께 두면 앞의 것이 엄격한 시험으로 남는다.
            comp_s = _base.copy()
            sband = _band_fullbody(os.path.join(SAMPLES, f"{who}.png"))
            comp_s.paste(sband.resize((bx[2] - bx[0], bx[3] - bx[1])), (bx[0], bx[1]))
            positives[f"장면합성 표본머리 [{who}]"] = (who, _band_scene(comp_s, who))

    # 음성 A = 그 자리에 인물이 없는 그림(구조적으로 확정된다 — 육안 확인된 순수 배경).
    negatives = {}
    for f in ("bg-ip0.0-cn0.2-s11.png", "bg-ip0.0-cn0.4-s11.png"):
        p = os.path.join(FINAL3, f)
        if not os.path.exists(p):
            continue
        im = Image.open(p).convert("RGB").resize(params.SCENE_SIZE)
        for who in PEOPLE:
            negatives[f"인물없음 {f} [{who}]"] = (who, _band_scene(im, who))
    # 음성 B = 교차(상대 인물의 정본에 이 인물의 축값을 건다).
    # ⚠ hair·headwear·age는 두 축값의 문구쌍이 서로 **역**이라 마진이 부호만 뒤집힌다 —
    #   그 세 축에 대해서는 동어반복이므로 **독립 증거가 아니다**. 그래도 부호 규약이
    #   깨지지 않았다는 자체검사로 남긴다(음성 A가 독립 증거다).
    cross = {
        "교차: frozen/goliath에 david 축값": ("david", positives["frozen/goliath.png"][1]),
        "교차: frozen/david에 goliath 축값": ("goliath", positives["frozen/david.png"][1]),
        "교차: samples/goliath에 david 축값": ("david", positives["samples/goliath.png"][1]),
        "교차: samples/david에 goliath 축값": ("goliath", positives["samples/david.png"][1]),
    }

    def score(d):
        return {k: {"who": w, "margins": marg(im, w), "pass": passes(marg(im, w))}
                for k, (w, im) in d.items()}

    pos_s, neg_s, cross_s = score(positives), score(negatives), score(cross)
    n_pos_ok = sum(v["pass"] for v in pos_s.values())
    n_neg_ok = sum(v["pass"] for v in neg_s.values())
    n_cross_ok = sum(v["pass"] for v in cross_s.values())
    clean = (n_pos_ok == len(pos_s) and n_neg_ok == 0 and n_cross_ok == 0 and len(neg_s) > 0)

    print("[축 E] 5축 재확인 — 정본 축값 대립쌍의 CLIP 마진(부호 판정)")
    print(f"  게이트 축 {gated} · `sex` 제외(정본 자신이 통과 못한다)")
    print(f"  양성(정본 자산) 통과 {n_pos_ok}/{len(pos_s)} (전부여야 한다) · "
          f"음성(인물 없음) 통과 {n_neg_ok}/{len(neg_s)} (0이어야 한다) · "
          f"교차 통과 {n_cross_ok}/{len(cross_s)} (0이어야 한다)")

    return {
        "formula": "머리 밴드에 대해 축별 대립쌍 마진 = cos(밴드, 정본문구) − cos(밴드, 반대문구). "
                    "판정은 부호이므로 임계를 손으로 고를 자리가 없다",
        "text_pairs_from": "derive_prompts.AXIS_PROBE_EN (생성용 AXIS_EN과 같은 자리에서 파생)",
        "clip_pairing": "이미지=IP-Adapter sdxl_models/image_encoder · 텍스트=SDXL text_encoder_2 — "
                         "둘 다 laion2B ViT-bigG-14, projection_dim 1280. 새 의존성이 아니다",
        "canon_axes": axes,
        "canon_source": "frontend/src/sketches/cast/{david,goliath}.jsx 의 AXES — 2026-08-28 사용자 "
                         "규칙(성경 기반, 성경에 명확한 것이 없으면 성격·분위기 참고)으로 정해진 값이다. "
                         "이 축은 그 값을 읽어 대조할 뿐 바꾸지 않는다",
        "gated_axes": gated,
        "excluded_axes": {"sex": "정본 자신이 통과하지 못한다(frozen/david.png 마진 -0.0135) — "
                                  "소년 얼굴이 CLIP에서 man/woman 사이에 놓인다"},
        "scene_band_from": "콘티 저작 원본의 머리 원 `<circle id=\"head-<who>\">`(획 포함 경계상자). "
                            "분율 손잡이는 **폐지했다** — `conti_head_box()` 참조",
        "scene_head_boxes": {w: list(conti_head_box(w)) for w in PEOPLE},
        "superseded_band": {
            "old": "마스크 bbox 상단 분율 0.30 (평탄구간 0.22~0.34)",
            "why_wrong": "인물이 지물을 머리 위로 치켜든 자세에서 밴드에 머리가 **0화소** 든다 — "
                          "다윗 정수리는 bbox 비율 .2995이고 밴드 0.30의 끝이 같은 행(y=267)이다. "
                          "어떤 산출물로도 통과할 수 없는 게이트였고, 축 E가 최종본을 떨어뜨린 것은 "
                          "검출이 아니라 **우연**이었다(ZIMAGE.md §9-10)",
            "why_plateau_missed_it": "평탄구간 실측의 양성이 전부 `frozen/*.png` **두상**이라 "
                                      "상단 30%가 전부 머리였다 — 「지물을 치켜든 전신 장면」 "
                                      "정의역을 한 번도 보지 않았다. 그래서 **장면 정의역 양성**을 신설했다",
            "why_not_widen": "0.40으로 올리면 다윗이 통과로 뒤집히지만 그것은 **임계 완화**다 — "
                              "미달을 임계로 푸는 것은 거짓 승리(loop 금지 항목)",
        },
        "fullbody_band_fraction": HEAD_BAND,
        "positives": pos_s, "negatives": neg_s, "cross_negatives": cross_s,
        "validation": {"positive_pass": n_pos_ok, "n_positive": len(pos_s),
                        "negative_pass": n_neg_ok, "n_negative": len(neg_s),
                        "cross_pass": n_cross_ok, "n_cross": len(cross_s)},
        "human_only": False,
        "machine_gate_ready": bool(clean),
    }


# --- 축 G (신설, task#321) — 팔이 사지인가 -------------------------------------
# **왜 필요한가.** 축 C는 인물 전체 띠에서 상관을 한 값으로 내므로 팔 하나의 이탈이 몸통·다리·
# 머리의 일치에 묻힌다. 승인본 s11(팔 차렷)과 s7(끈이 팔 회랑을 관통)이 **둘 다 여섯 축을
# 통과했고**, 보완 ①「다윗이 물맷돌을 던지는 동작」이 승인 뒤에 나왔다.
#
# **왜 상관을 부위로 좁히는 것으로는 안 되는가.** 실측(`notes/arm-sweep.json`): 부위별 상관에서
# 음성 B가 **+0.489**로 양성인 콘티 자신 **+0.226**보다 높다. 끈이 콘티 선 위에 정확히 놓이면
# 「선 자리에 엣지가 있는가」 계열은 임계를 어디 두든 못 가른다. 후보 7개 중 6개가 이 이유로 죽었다.
#
# **채택한 산식.** 법선 프로파일 실측이 셋을 갈랐다:
#     콘티(양성)  엣지 t = -3, +4          중심 매끄러움 + 경계 한 쌍  → 사지
#     s7(관통)    엣지 t = -1, 0, 1, 2, 3  **중심 자체가 엣지**        → 사지 아님
#     s11(분리)   엣지 없음                                            → 사지 아님
# 즉 「그 자리에 있는 것이 **사지인가**」를 묻는다. 사지는 매끄러운 내부를 두 경계가 감싸고,
# 끈은 중심선 위에 얹힌다.
ARM_PART = "david-arm"
ARM_W_MIN_INSET = 2   # 엣지가 경계 안쪽 1px씩에 놓여 저작 획 7px가 5~7로 측정된다(실측)


def arm_geometry():
    """축 G의 판정 기하 — 전부 콘티에서 파생한다(ADR `260830-084555`). 손으로 적은 좌표가 없다."""
    r = _conti_stroke("david")
    ink = _conti_ink(ARM_PART) > 0
    return {"r": r, "ink": ink,
            "band": _load_conti_mask("david") & _band(ink.astype(np.float32), r)}


def arm_centerline(ink, n=25):
    """콘티 팔 잉크의 중심선 표본과 법선. 주축(PCA)을 따라 n곳을 잡고, 주축 좌표가 가까운 잉크
    화소의 무게중심을 중심점으로, 부축을 법선으로 쓴다 — 팔이 45도로 기울어 행/열 평균은
    왜곡되지만 주축은 그렇지 않다."""
    ys, xs = np.nonzero(ink)
    pts = np.stack([xs, ys], 1).astype(np.float64)
    c = pts.mean(0)
    major, minor = np.linalg.svd(pts - c, full_matrices=False)[2][:2]
    proj = (pts - c) @ major
    out = []
    for t in np.linspace(proj.min(), proj.max(), n):
        sel = np.abs(proj - t) < 2.0
        if sel.sum() >= 3:
            out.append((pts[sel].mean(0), minor))
    return out


def arm_limb_score(g, samples, require_clean_center=True, w_min=None):
    """사지 판정 — 중심이 매끄럽고 양쪽에 경계가 있으며 그 간격이 w_min 이상인 표본의 비율.

    `w_min`은 **임계가 아니라 [[지표를 정의하는 상수]]**다(`judge_style.DARK_CUT`·`ARM_Y_ABS`와
    같은 종류). 통과 임계는 아래 사다리 양끝의 산술 중점에서 파생하며 손으로 고르지 않는다.
    `reach`도 저작 획 두께에서 파생한다."""
    w_min = g["r"] - ARM_W_MIN_INSET if w_min is None else w_min
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


def arm_synthetic_fill(base_path, band):
    """팔 띠를 균일 질감으로 덮은 합성 음성 — 축 C의 「균일채움 합성」과 같은 종류의 구조적 음성.
    루프가 만든 실패작이 아니므로 계보가 다르다(회고 `260830-093209`: 루프가 만든 실패작만
    음성으로 쓰면 Goodhart를 못 잡는다)."""
    a = np.asarray(_axis_c_load(base_path)).copy()
    yy, xx = np.mgrid[:params.SCENE_SIZE[1], :params.SCENE_SIZE[0]]
    tex = np.stack([(((yy // 4 + xx // 4) % 2) * 90 + 90).astype(np.uint8)] * 3, -1)
    a[band] = tex[band]
    return Image.fromarray(a)


# 축 G의 음성 대조군은 **task#320 승인본 그 자체**다 — 「그 파일이름에 지금 놓인 것」이 아니다.
# 2026-08-30(task#322 S3) 실측으로 드러난 함정: `gen_final.py`의 산출물 이름은 (cn, bg_ip,
# fig_cn, sip)만 담고 **콘티·프롬프트 판본을 담지 않는다.** 그래서 콘티를 고친 뒤 같은 조합으로
# 다시 생성하면 승인본을 **덮어쓴다** — 그러면 판정 대상이 자기 자신의 음성 대조군이 되는
# 순환이 생기고, `.forge/reports/`는 gitignore라 되돌릴 수도 없다.
# 그래서 승인본 2장을 `reference/`(git 추적, 다른 대조군 자산이 이미 사는 곳)로 옮겨 **고정한다.**
# 화소는 그대로이므로 임계는 움직이지 않는다 — 바뀐 것은 대조군의 **신원이 안정되었다**는 것뿐이다.
# ⚠ 남은 같은 종류의 취약점: `NEG_AXIS_C`도 FINAL3 안을 가리킨다(bg-ip0.0-cn0.2-s11.png).
#   이번 태스크의 조합(cn 0.6)과 겹치지 않아 지금은 안 깨지지만, 같은 함정 위에 있다 — 별건.
ARM_APPROVED = os.path.join(params.REFERENCE, "approved-320-s%s.png")


def axis_g():
    g = arm_geometry()
    samples = arm_centerline(g["ink"])
    score = arm_limb_score(g, samples)

    pos_path = os.path.join(CONTI, "david.png")
    pos_im, neg_im = _axis_c_load(pos_path), _axis_c_load(NEG_AXIS_C)
    by_alpha = {a: score(_edge_bool_f(Image.blend(neg_im, pos_im, a))) for a in LADDER}
    vals = [by_alpha[a] for a in LADDER]
    mono = all(vals[i] <= vals[i + 1] for i in range(len(vals) - 1))
    neg_v, pos_v = by_alpha[0.0], by_alpha[1.0]
    thr = (neg_v + pos_v) / 2      # 축 C·D와 같은 산술 중점

    # --- 파생과 독립인 검증 ------------------------------------------------------
    # 임계는 위 사다리(음성 1장 + 양성 1장)에서만 파생했다. 아래 집합은 검증만 한다.
    negatives = {}
    for key, seed, why in (("neg_a_separated", "11", "승인본 s11 — 팔이 차렷으로 내려오고 물매가 허공에 떴다(분리)"),
                            ("neg_b_pierced", "7", "승인본 s7 — 물매 끈이 팔 회랑을 한 줄로 지나간다(관통)")):
        p = ARM_APPROVED % seed
        if os.path.exists(p):
            negatives[key] = {"path": os.path.basename(p), "label": why,
                              "score": score(_edge_bool_f(_axis_c_load(p)))}
    negatives["neg_c_bg_only"] = {
        "path": os.path.basename(NEG_AXIS_C), "label": "배경만 — 인물 부재. 루프 밖 계보의 음성",
        "score": score(_edge_bool_f(_axis_c_load(NEG_AXIS_C)))}
    negatives["neg_d_synth_fill"] = {
        "path": "<합성> 팔 띠 균일채움", "label": "팔 띠를 덩어리로 채운 합성 — 구조적 음성",
        "score": score(_edge_bool_f(arm_synthetic_fill(NEG_AXIS_C, g["band"])))}

    positives = {os.path.basename(p): score(_edge_bool_f(_axis_c_load(p)))
                 for p in sorted(glob.glob(os.path.join(FINAL3, "3-final-*.png")))}

    neg_pass = sum(v["score"] > thr for v in negatives.values())
    pos_pass = sum(v > thr for v in positives.values())
    clean = mono and neg_pass == 0 and len(negatives) > 0 and pos_v > thr

    print("[축 G] 팔이 사지인가 — 콘티 팔 중심선의 법선 프로파일")
    print("  사다리 " + " → ".join(f"{by_alpha[a]:+.4f}" for a in LADDER)
          + f"  임계 {thr:+.4f}  단조 {'OK' if mono else 'FAIL'}  정의역 {int(g['ink'].sum())}화소")
    for k, v in negatives.items():
        print(f"    {k:18s} {v['score']:+.4f} {'통과 ✗' if v['score'] > thr else '기각 ✓'}  {v['label']}")
    print(f"  검증: 음성 통과 {neg_pass}/{len(negatives)} (0이어야 한다) · "
          f"양성(콘티) {pos_v:+.4f} 통과 {pos_v > thr} · 산출물 통과 {pos_pass}/{len(positives)}")

    return {
        "formula": "콘티 팔 중심선 표본마다 법선 위에서 (중심 화소가 엣지가 아니고) 양쪽에 경계가 "
                    "있으며 그 간격이 w_min 이상인 표본의 비율. 「선 자리에 엣지가 있는가」가 아니라 "
                    "「그 자리에 있는 것이 사지인가」를 묻는다",
        "why_not_correlation": "부위별 상관은 음성 B(관통) +0.489 > 양성(콘티) +0.226 — 임계를 "
                                "어디 두든 못 가른다. 후보 7개 중 6개가 이 이유로 죽었다 "
                                "(notes/arm-sweep.json · notes/ARM.md)",
        "part_source": f"conti/{ARM_PART}.png — 콘티 <g id=\"{ARM_PART}\">에서 파생(ADR 260830-084555)",
        "metric_constants": {"w_min": g["r"] - ARM_W_MIN_INSET, "reach": 4 * g["r"],
                              "note": "임계가 아니라 [[지표를 정의하는 상수]]. w_min은 저작 획 두께에서 "
                                      "엣지 검출의 경계 안쪽 1px씩을 뺀 값이다"},
        "domain_px": int(g["ink"].sum()),
        "positive_control": "conti/david.png — 콘티 잉크 자신",
        "negative_control": f"final3/{os.path.basename(NEG_AXIS_C)} — 사다리 음성(축 C와 같은 자산)",
        "ladder": {str(a): by_alpha[a] for a in LADDER},
        "ladder_monotonic": bool(mono),
        "threshold": thr,
        "threshold_rule": "사다리 양끝(음성·양성)의 산술 중점 — 축 C·D와 같은 규약",
        "validation_negatives": negatives, "validation_positives": positives,
        "validation": {"negative_pass": neg_pass, "n_negative": len(negatives),
                        "positive_pass": pos_pass, "n_positive": len(positives)},
        "human_only": False,
        "machine_gate_ready": bool(clean),
    }


def main():
    out = {"axis_a": axis_a(), "axis_b": axis_b(), "axis_c": axis_c(),
           "axis_d": axis_d(), "axis_e": axis_e(), "axis_f": axis_f(),
           "axis_g": axis_g()}
    out_path = sys.argv[sys.argv.index("--json") + 1] if "--json" in sys.argv else DEFAULT_OUT
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f"\n기록: {out_path}")

    # --- 완료기준 요약 -------------------------------------------------------
    print("\n" + "=" * 78)
    a_ok = out["axis_a"]["regression_check_combined3"]["passes_new_threshold"] is False
    d = out["axis_d"]["candidates"][out["axis_d"]["chosen"]] if out["axis_d"]["chosen"] != "none" else None
    d_ok = d is not None and (not d["neg_passes"]) and d["pos_passes"]
    print(f"축 A: combined3(회귀 표본)가 신임계에서 실패 = {a_ok}")
    b = out["axis_b"]
    if b.get("threshold") is None:
        print("축 B: 산식·짝만 확정(수치 없음) — 표본이 아직 없다")
    else:
        print(f"축 B: 임계 {b['threshold']:+.4f} = 귀무 최대(파생) · 사다리 단조 "
              f"{b['ladder_monotonic']} · 양성 {b['positive_passes_at_alpha1']}/{b['n_positive']} "
              f"· machine_gate_ready = {b['machine_gate_ready']}")
    print(f"축 C: machine_gate_ready = {out['axis_c']['machine_gate_ready']}"
          + ("" if out['axis_c']['machine_gate_ready'] else
             " — 분해능 미증명, part3 재검증 필요 (근거: demoted_because 필드)"))
    print(f"축 D: 선택 {out['axis_d']['chosen']} — 음성 실패·양성 통과 = {d_ok}")
    print(f"축 F: 갑주 착용 여부 — machine_gate_ready = {out['axis_f']['machine_gate_ready']} "
          f"(양성 {out['axis_f']['validation']['positive_pass']}/"
          f"{out['axis_f']['validation']['n_positive']} · 음성 "
          f"{out['axis_f']['validation']['negative_pass']}/"
          f"{out['axis_f']['validation']['n_negative']}) — ⚠ 종류(비늘/판금)는 재지 않는다")
    print(f"축 E: 5축 재확인 — machine_gate_ready = {out['axis_e']['machine_gate_ready']} "
          f"(양성 {out['axis_e']['validation']['positive_pass']}/"
          f"{out['axis_e']['validation']['n_positive']} · 음성 "
          f"{out['axis_e']['validation']['negative_pass']}/"
          f"{out['axis_e']['validation']['n_negative']})")
    print(f"축 G: 팔이 사지인가 — machine_gate_ready = {out['axis_g']['machine_gate_ready']} "
          f"(음성 통과 {out['axis_g']['validation']['negative_pass']}/"
          f"{out['axis_g']['validation']['n_negative']} · 사다리 단조 "
          f"{out['axis_g']['ladder_monotonic']}) — 승인본 s11·s7을 떨어뜨리라고 만든 축이다")
    return 0


if __name__ == "__main__":
    sys.exit(main())
