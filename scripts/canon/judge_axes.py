"""축 B [[정본 전이]] · 축 C 구도 — 자를 세우고 착수 시점에 거짓임을 실측한다(task#317 S0).

축 A는 `judge_style.py`가 진다. 이 파일은 나머지 두 축과 **세 축 종합표**를 낸다.

## 축 B — 왜 「짝지어」 재는가

task#315의 축 B는 인물 bbox를 CLIP으로 임베딩해 동결본과의 유사도를 절대값으로 봤고, 레퍼런스를
안 태운 조건(`a-none`)이 3/3 통과해 **무정보가 됐다**. 이 파일이 그 자리에서 바꾼 것은 도구가 아니라
**측정의 짝**이다:

  1. **크롭을 얼굴로 좁힌다.** 인물 bbox(다윗 251x327)는 얼굴(~98x116)을 1/7 면적으로 묻는다.
     머리 마스크는 인물 정본 컴포넌트의 delay 슬롯에서 파생한다(check_mask_ranges.derive_head_ranges).
  2. **같은 시드의 `a-none`을 기준선으로 빼서 짝지어 잰다.** 절대 유사도는 시드 분산(0.52~0.57)이
     조건 차이(+0.05~+0.15)를 덮는다. 같은 시드끼리 빼면 그 분산이 상쇄된다 — 실제로 짝짓기 전에는
     대조군과 현행의 여유가 +0.005(잡음)였고, 짝지은 뒤 18/18이 같은 부호로 갈렸다.
  3. **정체성 특정분만 남긴다.** 전이 점수 = Δ(자기 동결본) − Δ(남의 동결본). 레퍼런스를 태우면
     그림 전체가 조금씩 움직이는데, 그 공통 이동은 「그 아이인가」의 증거가 아니다.

**임계는 귀무 바닥에서 파생한다.** `a-none` 3장을 서로에 대해 같은 산식으로 재면(전이가 있을 수
없는 짝) 그 최대값이 이 자의 잡음 바닥이다. 임계 = 그 바닥. 리터럴이 없다.

**분해능은 합성 양성 대조군이 증명한다**(ADR `260825-013641` — 도구를 의심하기 전에 배제한다).
동결본을 머리 영역에 alpha로 얹은 장면을 만들어 alpha 사다리(0 → 0.25 → 0.5 → 1.0)에서 점수가
단조 증가하는지 본다. 증가하면 **이 크기·이 맥락에서 잴 수 있다**는 뜻이고, 그때 현행이 낮은 것은
자의 실패가 아니라 실측이다.

## 축 C — 구도

지시 영역(콘티 마스크) 안의 **에지 에너지 농축비** = (마스크 안 에지 비율) / (마스크 면적 비율).
인물이 지시된 자리에 있으면 1을 넘는다. 화풍과 무관하게 성립하는 것이 이 지표를 고른 이유다 —
현행 장면은 어두운 화소가 거의 없어(축 A가 재는 바로 그 결함) 잉크 기반 지표는 축 C에서 퇴화한다.

**음성 대조군은 정답지 자신이다.** 정답지 10장은 전부 ControlNet 없이 뽑혀 콘티를 따르지 않는다 —
한 집합이 축 A의 양성이면서 축 C의 음성인 것이 이 파일럿이 푸는 긴장이다(REFERENCE.md).

Usage: /Users/calmonion/.local/biblemap-imggen/.venv314/bin/python judge_axes.py [--json OUT]
"""
import glob
import itertools
import json
import os
import sys

import numpy as np
from PIL import Image

import judge_metrics as jm
import judge_style
import params

MASKS = os.path.join(params.OUT_ROOT, "masks")
SCENE = os.path.join(params.OUT_ROOT, "scene")
BASELINE_COND = "a-none"   # 레퍼런스를 아예 안 태운 조건 — 축 B의 짝 기준선이자 음성 대조군
PEOPLE = ("david", "goliath")
LADDER = (0.0, 0.25, 0.5, 1.0)  # 합성 양성 대조군의 alpha 사다리 — 분해능 증명용


# --- 공통 ---------------------------------------------------------------------
def head_boxes():
    return {n: jm.bbox_from_mask(os.path.join(MASKS, f"{n}_head.png")) for n in PEOPLE}


def scene_image(path):
    return Image.open(path).convert("RGB").resize(params.SCENE_SIZE)


def seed_of(path):
    """`c-mask-s42.png` → 42. 파일명 관례가 곧 짝짓기 키다."""
    return int(os.path.basename(path).rsplit("-s", 1)[1].split(".")[0])


def cond_of(path):
    return os.path.basename(path).rsplit("-s", 1)[0]


# --- 축 B ---------------------------------------------------------------------
def _transfer_score(emb_head, base_head, frozen, who):
    """전이 점수 = Δ(자기) − Δ(남). 기준선(base_head)은 같은 시드의 `a-none` 머리."""
    other = "goliath" if who == "david" else "david"
    d_self = jm.cos(emb_head, frozen[who]) - jm.cos(base_head, frozen[who])
    d_cross = jm.cos(emb_head, frozen[other]) - jm.cos(base_head, frozen[other])
    return d_self - d_cross, d_self, d_cross


def axis_b(embedder):
    box = head_boxes()
    frozen = {n: embedder.embed(Image.open(os.path.join(params.FROZEN, f"{n}.png")))
              for n in PEOPLE}
    paths = sorted(glob.glob(os.path.join(SCENE, "*.png")))
    base = {seed_of(p): p for p in paths if cond_of(p) == BASELINE_COND}
    if not base:
        sys.exit(f"축 B 기준선 조건 `{BASELINE_COND}`이 없다 — 짝지을 대상이 없다")

    emb = {}   # (path, who) -> 임베딩
    for p in paths:
        im = scene_image(p)
        for who in PEOPLE:
            emb[(p, who)] = embedder.embed(im.crop(box[who]))

    # 귀무 바닥 — 전이가 있을 수 없는 짝(a-none 끼리)에서 같은 산식이 내는 값의 최대.
    null = []
    for who in PEOPLE:
        for a, b in itertools.permutations(base.values(), 2):
            null.append(_transfer_score(emb[(a, who)], emb[(b, who)], frozen, who)[0])
    threshold = max(null)

    # 합성 양성 대조군 — 동결본을 머리 자리에 alpha로 얹는다. 자의 분해능을 증명한다.
    frozen_im = {n: Image.open(os.path.join(params.FROZEN, f"{n}.png")).convert("RGB")
                 for n in PEOPLE}
    ladder = {}
    for alpha in LADDER:
        vals = []
        for who in PEOPLE:
            for seed, bp in base.items():
                im = scene_image(bp)
                x0, y0, x1, y1 = box[who]
                head = frozen_im[who].resize((x1 - x0, y1 - y0), Image.LANCZOS)
                blended = Image.blend(im.crop(box[who]), head, alpha)
                vals.append(_transfer_score(embedder.embed(blended), emb[(bp, who)],
                                            frozen, who)[0])
        ladder[alpha] = {"min": min(vals), "max": max(vals),
                         "mean": float(np.mean(vals)), "vals": vals}

    rows = []
    for p in paths:
        if cond_of(p) == BASELINE_COND:
            continue
        bp = base[seed_of(p)]
        for who in PEOPLE:
            sc, ds, dc = _transfer_score(emb[(p, who)], emb[(bp, who)], frozen, who)
            rows.append({"file": os.path.basename(p), "who": who, "score": sc,
                         "d_self": ds, "d_cross": dc, "pass": sc > threshold})
    return {"threshold": threshold, "null_max": threshold, "null": null,
            "ladder": ladder, "rows": rows}


# --- 축 C ---------------------------------------------------------------------
def _edge_energy(path):
    a = np.asarray(Image.open(path).convert("L").resize(params.SCENE_SIZE, Image.LANCZOS),
                   dtype=np.float32)
    e = np.zeros_like(a)
    e[:, 1:] += np.abs(np.diff(a, axis=1))
    e[1:, :] += np.abs(np.diff(a, axis=0))
    return e


def _person_area():
    W, H = params.SCENE_SIZE
    m = np.zeros((H, W), dtype=bool)
    for n in PEOPLE:
        m |= np.array(Image.open(os.path.join(MASKS, f"{n}.png")).convert("L").resize((W, H))) > 0
    return m, float(m.mean())


def axis_c():
    person, frac = _person_area()

    def enrich(path):
        e = _edge_energy(path)
        tot = e.sum()
        return float((e[person].sum() / tot) / frac) if tot > 0 else 0.0

    cur = {os.path.basename(p): enrich(p) for p in sorted(glob.glob(os.path.join(SCENE, "*.png")))}
    ref = {os.path.basename(p): enrich(p) for p in judge_style.reference_paths()}
    thr = judge_style._log_mid(min(cur.values()), max(ref.values()))
    return {"area_fraction": frac, "threshold": thr, "current": cur, "reference": ref}


def _equiv_alpha(score, ladder):
    """현행 점수가 합성 사다리의 어디쯤인가 — 「전이가 몇 % 얹힌 것과 같은가」를 한 수로 읽는다."""
    xs = sorted(ladder)
    ys = [ladder[a]["mean"] for a in xs]
    if score <= ys[0]:
        return xs[0]
    for i in range(1, len(xs)):
        if score <= ys[i]:
            t = (score - ys[i - 1]) / (ys[i] - ys[i - 1]) if ys[i] != ys[i - 1] else 0.0
            return xs[i - 1] + t * (xs[i] - xs[i - 1])
    return xs[-1]


# --- 종합 ---------------------------------------------------------------------
def main():
    print("=" * 78)
    print("task#317 S0 — 세 축의 자를 세우고 착수 시점에 거짓임을 실측한다")
    print("=" * 78)

    # 축 A
    a_json = {}
    ref_m = [judge_style.style_metrics(p) for p in judge_style.reference_paths()]
    cur_m = [judge_style.style_metrics(p) for p in judge_style.current_scene_paths()]
    a_thr = judge_style.derive_thresholds(ref_m, cur_m)
    a_ref_pass = sum(judge_style.passes(m, a_thr) for m in ref_m)
    a_cur_pass = sum(judge_style.passes(m, a_thr) for m in cur_m)
    print(f"\n[축 A 화풍 도달]  임계 ink>={a_thr['ink_min']:.4f} · p05<={a_thr['val_p05_max']:.3f} (정답지에서 파생)")
    print(f"  정답지 {a_ref_pass}/{len(ref_m)} 통과 · 현행 {a_cur_pass}/{len(cur_m)} 통과"
          f"  — 분리 {a_thr['separation']['ink_ratio']:.1f}배")
    a_json = {"thresholds": a_thr, "reference_pass": a_ref_pass, "current_pass": a_cur_pass,
              "n_reference": len(ref_m), "n_current": len(cur_m)}

    # 축 C (GPU/모델 불필요 — 먼저 낸다)
    c = axis_c()
    c_cur_pass = sum(v > c["threshold"] for v in c["current"].values())
    c_ref_pass = sum(v > c["threshold"] for v in c["reference"].values())
    print(f"\n[축 C 구도]  임계 농축비 > {c['threshold']:.3f} (현행 하한과 정답지 상한의 로그 중점)")
    print(f"  현행 {c_cur_pass}/{len(c['current'])} 통과 · 정답지(음성 대조군) {c_ref_pass}/{len(c['reference'])} 통과")
    print(f"  현행 {min(c['current'].values()):.3f}~{max(c['current'].values()):.3f}"
          f"  정답지 {min(c['reference'].values()):.3f}~{max(c['reference'].values()):.3f}")
    print("  ⇒ 축 C는 착수 시점에 **이미 참이다**. 이 축의 역할은 회귀 방지다"
          " — 축 A를 올리는 처방이 구도를 깨는지 본다.")

    # 축 B
    print(f"\n[축 B 정본 전이]  CLIP 이미지 인코더 로드 중…", flush=True)
    b = axis_b(jm.Embedder())
    print(f"  귀무 바닥(a-none 끼리, 전이 불가능한 짝) 최대 = {b['threshold']:+.4f} → 이것이 임계")
    print("  합성 양성 사다리(동결본을 머리 자리에 alpha로 얹음) — 단조 증가가 곧 분해능의 증거")
    for alpha, L in b["ladder"].items():
        print(f"    alpha={alpha:<5} 점수 {L['min']:+.4f}~{L['max']:+.4f}  평균 {L['mean']:+.4f}")
    # 판정 단위는 **조건 x 인물**(3시드)이다 — 낱장 판정은 시드 잡음에 흔들린다.
    by_cond = {}
    for r in b["rows"]:
        by_cond.setdefault((r["file"].rsplit("-s", 1)[0], r["who"]), []).append(r["score"])
    print("  현행 조건별 전이 점수(3시드) — 통과 = 3시드 전부 임계 초과")
    b_cond_pass = 0
    for (cond, who), vals in sorted(by_cond.items()):
        ok = min(vals) > b["threshold"]
        b_cond_pass += ok
        print(f"    {cond:12s} {who:8s} {min(vals):+.4f}~{max(vals):+.4f}"
              f"  평균 {np.mean(vals):+.4f}  ≈alpha {_equiv_alpha(np.mean(vals), b['ladder']):.2f}"
              f"  {'✅' if ok else '❌'}")
    b["condition_pass"] = b_cond_pass
    b["n_conditions"] = len(by_cond)
    print(f"  현행 {b_cond_pass}/{len(by_cond)} 조건 통과 (낱장으로는 {sum(r['pass'] for r in b['rows'])}/{len(b['rows'])})")

    # 분해능 증명 두 가지: 사다리가 평균에서 단조 증가하고, alpha=1.0이 조건 규칙으로 통과한다.
    means = [b["ladder"][a]["mean"] for a in LADDER]
    ladder_monotone = all(means[i] <= means[i + 1] for i in range(len(means) - 1))
    full_pass = b["ladder"][1.0]["min"] > b["threshold"]
    print(f"  사다리 평균 단조 {'OK' if ladder_monotone else 'FAIL'}"
          f" · 합성 alpha=1.0 전수 통과 {'OK' if full_pass else 'FAIL'}"
          f" — 자가 이 크기에서 전이를 {'잴 수 있다' if ladder_monotone and full_pass else '못 잰다'}")

    if "--json" in sys.argv:
        out = sys.argv[sys.argv.index("--json") + 1]
        json.dump({"axis_a": a_json, "axis_b": b, "axis_c": c}, open(out, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1, default=float)
        print(f"\njson 기록: {out}")

    # --- S0 완료기준 --------------------------------------------------------
    print("\n" + "=" * 78)
    fails = []
    if not (a_ref_pass == len(ref_m) and a_cur_pass == 0):
        fails.append(f"축 A: 정답지 {a_ref_pass}/{len(ref_m)} · 현행 {a_cur_pass}/{len(cur_m)}")
    if not (ladder_monotone and full_pass):
        fails.append("축 B: 합성 양성 대조군이 분해능을 증명하지 못했다 — 지표를 교체하라")
    if not (c_cur_pass == len(c["current"]) and c_ref_pass == 0):
        fails.append(f"축 C: 현행 {c_cur_pass}/{len(c['current'])} · 음성 {c_ref_pass}/{len(c['reference'])}")
    if fails:
        print("S0 완료기준 미충족:")
        for f in fails:
            print(f"  ❌ {f}")
        return 1
    print("S0 PASS — 세 축 전부 분해능이 증명됐다.")
    print(f"  축 A: 착수 시점 **거짓**(현행 0/{len(cur_m)}) — 이 파일럿이 올려야 할 축")
    print(f"  축 B: 자는 잴 수 있고(사다리 단조 + 합성 전수 통과), 현행 {b_cond_pass}/{b['n_conditions']} 조건 통과"
          f" — 임계 아래이면 착수 시점 **거짓**이다")
    print(f"  축 C: 착수 시점 **참**(현행 {c_cur_pass}/{len(c['current'])}) — 회귀 방지 기준")
    return 0


if __name__ == "__main__":
    sys.exit(main())
