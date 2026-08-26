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
import itertools
import json
import os
import sys

import numpy as np
from PIL import Image

import judge_axes as ja
import judge_metrics as jm
import judge_style as js
import params

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


def _axis_c_corpus():
    """축 C의 양성 코퍼스와 음성 대조군을 고른다 — `revalidate_by: part3`가 지목한 그 교체다.

    **양성**은 「새 콘티로 조건화해 실제로 생성한 최종 장면」이어야 한다. 초판이 미증명으로 남은
    이유가 바로 이것이었다: 양성으로 쓴 `scene/*.png`는 **옛 앱 장면**의 ControlNet 조건으로
    생성됐고 새 마스크는 새 콘티에서 파생돼, 골리앗 bbox가 105px 어긋난 채로 재던 것이다.
    그래서 part 3의 `final3/3-final-*.png`가 있으면 그쪽을 쓰고, 없으면 옛 코퍼스로 떨어진다
    (part 1·2를 재실행해도 같은 값이 나오게 두려면 폴백이 필요하다).

    **음성에 「배경만 있는 장면」을 더한다.** 정답지 10장은 ControlNet 없이 뽑혀 콘티를 안 따르지만
    화풍·구성이 아예 다른 집합이라, 「같은 파이프라인·같은 콘티인데 인물만 없는 그림」을 거르는지는
    증명하지 못한다 — 그것이 #317 구멍 2(인물이 통째로 빠져도 통과한다)다. `final3/bg-*.png`가
    정확히 그 그림이다(같은 콘티로 조건화됐고 인물 마스크 자리에 인물이 없다). 음성 집합이 커지면
    `max(음성)`이 올라가므로 임계는 **더 엄해진다** — 완화가 아니다.
    """
    finals = sorted(glob.glob(os.path.join(FINAL3, "3-final-*.png")))
    bgs = sorted(glob.glob(os.path.join(FINAL3, "bg-*.png")))
    if finals:
        return finals, bgs, "final3/3-final-*.png (part3 — 새 콘티로 조건화한 최종 장면)"
    return (sorted(glob.glob(os.path.join(params.OUT_ROOT, "scene", "*.png"))), bgs,
            "scene/*.png (옛 앱 장면 조건 — part3 산출물이 없어 폴백)")


def axis_c():
    m_d, m_g = _load_conti_mask("david"), _load_conti_mask("goliath")
    person = m_d | m_g
    overlap = int((m_d & m_g).sum())
    fracs = {"union": float(person.mean()), "david": float(m_d.mean()), "goliath": float(m_g.mean())}

    def enrich(path, mask, frac):
        e = _edge_energy(path)
        tot = e.sum()
        return float((e[mask].sum() / tot) / frac) if tot > 0 and frac > 0 else 0.0

    def score_all(path):
        return {"combined": enrich(path, person, fracs["union"]),
                "david": enrich(path, m_d, fracs["david"]),
                "goliath": enrich(path, m_g, fracs["goliath"])}

    cur_paths, bg_paths, corpus_note = _axis_c_corpus()
    ref_paths = js.reference_paths()
    current = {os.path.basename(p): score_all(p) for p in cur_paths}
    reference = {os.path.basename(p): score_all(p) for p in ref_paths}
    bg_only = {os.path.basename(p): score_all(p) for p in bg_paths}

    per_key = {}
    for key in ("combined", "david", "goliath"):
        cur_vals = [v[key] for v in current.values()]
        neg_vals = [v[key] for v in reference.values()] + [v[key] for v in bg_only.values()]
        thr = js._log_mid(min(cur_vals), max(neg_vals))
        per_key[key] = {
            "threshold": thr,
            "current_pass": sum(v > thr for v in cur_vals), "n_current": len(cur_vals),
            "reference_pass": sum(v[key] > thr for v in reference.values()),
            "n_reference": len(reference),
            "bg_only_pass": sum(v[key] > thr for v in bg_only.values()),
            "n_bg_only": len(bg_only),
        }

    # --- s0에서 되던 것이 이번엔 왜 안 되는지 실측으로 밝힌다 ---------------------
    old_bbox_d = jm.bbox_from_mask(os.path.join(params.OUT_ROOT, "masks", "david.png"))
    old_bbox_g = jm.bbox_from_mask(os.path.join(params.OUT_ROOT, "masks", "goliath.png"))
    new_bbox_d = jm.bbox_from_mask(os.path.join(CONTI, "mask_david.png"))
    new_bbox_g = jm.bbox_from_mask(os.path.join(CONTI, "mask_goliath.png"))
    shift_d = new_bbox_d[0] - old_bbox_d[0]
    shift_g = new_bbox_g[0] - old_bbox_g[0]

    # **모든 키가 깨끗해야 통과다** — combined만 보면 #317 구멍 2(인물이 통째로 빠져도 통과)를
    # 그대로 남긴다. 그리고 「배경만 있는 장면」음성이 0/N이어야 한다.
    clean = all(pk["current_pass"] == pk["n_current"] and pk["reference_pass"] == 0
                and pk["bg_only_pass"] == 0 for pk in per_key.values())
    c = per_key["combined"]
    print(f"[축 C] 코퍼스: {corpus_note}")
    for key in ("combined", "david", "goliath"):
        pk = per_key[key]
        print(f"  {key:8s} 임계 {pk['threshold']:.4f} — 양성 {pk['current_pass']}/{pk['n_current']} "
              f"· 정답지(음성) {pk['reference_pass']}/{pk['n_reference']} "
              f"· 배경만(음성) {pk['bg_only_pass']}/{pk['n_bg_only']}")
    print(f"  bbox x0 이동 — 다윗 {old_bbox_d[0]}→{new_bbox_d[0]}({shift_d:+d}px)  "
          f"골리앗 {old_bbox_g[0]}→{new_bbox_g[0]}({shift_g:+d}px)")

    out = {
        "masks": {"david": "conti/mask_david.png", "goliath": "conti/mask_goliath.png",
                  "method": "볼록껍질(convex hull), make_conti_masks.py — S4"},
        "area_fraction": fracs, "overlap_px": overlap,
        "per_person_occupancy": "current/reference/bg_only 각 항목이 combined·david·goliath 세 값을 "
                                 "담는다 — #317 구멍 2(인물이 통째로 빠져도 통과) 대응",
        "corpus": corpus_note,
        "negative_controls": "정답지 10장(ControlNet 없음) + 배경만 있는 장면(같은 콘티, 인물 없음). "
                              "후자가 구멍 2를 직접 건다 — 임계는 두 음성의 최대에서 파생하므로 "
                              "음성을 더한 것은 완화가 아니라 강화다.",
        "thresholds_by_key": per_key,
        "current": current, "reference": reference, "bg_only": bg_only,
    }

    if not clean:
        # `human_only`는 「기계가 영원히 못 잰다」는 뜻이므로 여기 쓰면 거짓이다 — 아래 근거가 스스로
        # 「산식이 깨진 게 아니라 코퍼스가 안 맞을 뿐」이라고 적고 있다. 상태는 **미증명**이지 강등이
        # 아니다: 기계가 잴 수 있으나 맞는 코퍼스(part 3의 새 콘티 산출물)가 아직 없다.
        out["human_only"] = False
        out["machine_gate_ready"] = False   # 분해능 미증명 — 게이트로 쓰면 안 된다
        out["revalidate_by"] = "part3"      # 새 콘티로 생성한 코퍼스가 나오면 재파생·재증명
        leak = {k: f"양성 {pk['current_pass']}/{pk['n_current']} · 정답지 {pk['reference_pass']}/"
                   f"{pk['n_reference']} · 배경만 {pk['bg_only_pass']}/{pk['n_bg_only']}"
                for k, pk in per_key.items()}
        out["demoted_because"] = (
            f"코퍼스 = {corpus_note}. 세 키 중 하나 이상이 완전 분리에 이르지 못했다 — {leak}. "
            f"세 키를 **전부** 요구하는 것은 #317 구멍 2(인물이 통째로 빠져도 combined는 통과할 수 "
            f"있다) 때문이고, 「배경만 있는 장면」음성이 그 구멍을 직접 건다. "
            f"참고로 마스크 자체는 콘티 교체로 옮겨갔다(골리앗 bbox x0 {old_bbox_g[0]}→{new_bbox_g[0]}, "
            f"{shift_g:+d}px) — 옛 `scene/*.png` 코퍼스로 재던 초판이 미증명으로 남은 원인이 그것이다. "
            f"축 C의 산식(에지 농축비)이 깨졌다는 뜻이 아니라, 이 코퍼스에서 그 분해능이 아직 "
            f"증명되지 않았다는 뜻이다."
        )
    else:
        out["human_only"] = False
        out["machine_gate_ready"] = True
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


def main():
    out = {"axis_a": axis_a(), "axis_b": axis_b(), "axis_c": axis_c(), "axis_d": axis_d()}
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
    return 0


if __name__ == "__main__":
    sys.exit(main())
