"""part 3 최종 판정 — 최종 장면 1장에 축 A·B·C·D를 **동시에** 건다(GPU 0, CLIP 임베더만 쓴다).

임계는 **전부 `notes/s1-baseline.json`에서 읽는다**. 이 파일은 임계를 만들지 않는다 —
part 1(축 A·C·D)·part 2(축 B)가 못박은 값을 그대로 쓴다(ADR `260823-221839` · 계획 S3
「미달 축이 있으면 어느 손잡이가 남았는지 적고 멈춘다 — 임계를 만지지 않는다, 결론 선취다」).

## 축마다 무엇을 재는가 — 그리고 짝이 무엇인가

**축 A 화풍** — `judge_style.style_metrics`의 ink·val_p05를 정답지 구간에 건다. 장면 전체가 대상이다
(단독 인물·초상은 이 축의 적용 범주가 **아니다** — `reference/REFERENCE.md`, part 2가 범주 오용을
실측으로 확인했다).

**축 B [[정본 전이]]** — 짝은 **같은 시드의 「그 인물을 그리기 직전 캔버스」**다. 순차 인페인팅이
그 짝을 공짜로 만든다:

  | 인물 | 기준선(base) | 현행(cur) |
  |---|---|---|
  | 다윗 | `bg-cn{cn}-s{seed}.png`(인물 없음) | `1-david-…png` |
  | 골리앗 | `1-david-…png`(다윗만 있음) | `2-goliath-…png` |

  같은 시드·같은 캔버스·같은 콘티이므로 PROMPTING.md 구멍 3(짝은 CN·프롬프트가 같을 때만 성립)을
  지킨다. 크롭은 인페인팅에 쓴 그 창(`gen_final.window`)이고, 비교 대상은 [[전신 표본]]이다 —
  `s1-baseline.json`의 `axis_b.formula`가 「비교 대상만 frozen head → 전신 표본」이라고 못박은 그대로.

  ⚠ **자가 진단 한 줄**: part 2가 파생한 임계는 「표본 파이프라인 전체 프레임」 척도에서 나왔고,
  이 파일은 「장면 안 인물 창」 척도에서 잰다. 척도가 다르면 임계를 그대로 쓰는 것 자체가 범주
  오용일 수 있다(축 A에서 실제로 그 오용이 있었다). 그래서 점수와 함께 **기준선 대비 여유**를
  같이 찍어 사람이 그 판단을 할 수 있게 남긴다 — 임계를 고치지 않는다.

**축 C 구도** — 마스크 안에서 콘티 잉크 ↔ 산출물 엣지의 픽셀별 피어슨 상관(2026-08-28 교체,
옛 산식은 에지 에너지 농축비였다). `s1-baseline.json`의 `thresholds_by_key`를 쓰고,
**combined 하나로 판정하지 않는다** — 인물별(david·goliath) 값을 같이 낸다(#317 구멍 2: 인물이
통째로 빠져도 combined는 통과할 수 있다).

**축 D 동작** — `axis_d.chosen`이 고른 지표(`mask_ink_edge_correlation`): 다윗 마스크 안에서
콘티 잉크와 산출물 엣지의 픽셀별 상관.

Usage: .../python judge_final.py --cn 0.8 [--seeds 11,42,7] [--json OUT]
"""
import argparse
import json
import os
import sys

import numpy as np
from PIL import Image

import gen_final as gf
import judge_metrics as jm
import judge_s1
import judge_style as js
import params

OUT = gf.OUT
S1_PATH = os.path.join(params.NOTES, "s1-baseline.json")


def _load_s1():
    with open(S1_PATH, encoding="utf-8") as f:
        return json.load(f)


def axis_a(path, thr):
    m = js.style_metrics(path)
    ok = m["ink"] >= thr["ink_min"] and m["val_p05"] <= thr["val_p05_max"]
    over = m["ink"] > thr["ink_max"]
    return {"ink": m["ink"], "val_p05": m["val_p05"], "pass": bool(ok),
            "ink_over_max_warn": bool(over)}


def axis_b(emb, cn, seed, threshold, bg_ip, fig_cn, sip):
    """전이 점수 = Δ(자기 표본) − Δ(남의 표본). 기준선은 그 인물을 그리기 직전 캔버스."""
    samples = {n: emb.embed(Image.open(os.path.join(gf.SAMPLES, f"{n}.png")).convert("RGB"))
               for n in gf.PEOPLE}
    masks = {n: gf.figure_mask(n) for n in gf.PEOPLE}
    boxes = {n: gf.window(masks[n], gf.PAD) for n in gf.PEOPLE}
    t = gf.tag(cn, bg_ip, fig_cn, sip)
    david_out = os.path.join(OUT, f"1-david-{t}-s{seed}.png")
    stage = {
        "david": (gf.bg_path(cn, seed, bg_ip), david_out),
        "goliath": (david_out, os.path.join(OUT, f"2-goliath-{t}-s{seed}.png")),
    }
    rows = {}
    for who in gf.PEOPLE:
        base_p, cur_p = stage[who]
        other = "goliath" if who == "david" else "david"
        box = boxes[who]
        e_base = emb.embed(Image.open(base_p).convert("RGB").resize(params.SCENE_SIZE).crop(box))
        e_cur = emb.embed(Image.open(cur_p).convert("RGB").resize(params.SCENE_SIZE).crop(box))
        d_self = jm.cos(e_cur, samples[who]) - jm.cos(e_base, samples[who])
        d_cross = jm.cos(e_cur, samples[other]) - jm.cos(e_base, samples[other])
        score = d_self - d_cross
        rows[who] = {"score": score, "d_self": d_self, "d_cross": d_cross,
                     "margin": score - threshold, "pass": bool(score > threshold),
                     "base": os.path.basename(base_p), "cur": os.path.basename(cur_p)}
    return {"threshold": threshold, "by_person": rows,
            "pass": all(r["pass"] for r in rows.values())}


def axis_c(path, thresholds_by_key):
    """마스크 안 콘티잉크↔산출엣지 상관 — combined + 인물별. judge_s1의 산식을 그대로 재사용한다."""
    masks, inks = judge_s1.axis_c_regions()
    im = Image.open(path).convert("RGB").resize(params.SCENE_SIZE)
    out = {}
    for key in judge_s1.AXIS_C_KEYS:
        v = judge_s1.axis_c_corr(im, key, masks, inks)
        thr = thresholds_by_key[key]["threshold"]
        out[key] = {"corr": v, "threshold": thr, "margin": v - thr, "pass": bool(v > thr)}
    return {"by_key": out, "pass": all(v["pass"] for v in out.values())}


def axis_d(path, spec):
    """다윗 마스크 안에서 콘티 잉크 ↔ 산출물 엣지의 픽셀별 피어슨 상관."""
    bbox = spec["mask_bbox"]
    x0, y0, x1, y1 = bbox
    mask = judge_s1._load_conti_mask("david")[y0:y1, x0:x1]
    conti = os.path.join(gf.CONTI, "david.png")
    a = np.array(Image.open(conti).convert("L").resize(params.SCENE_SIZE, Image.LANCZOS)).astype(int)
    bg = int(np.median(a[0:8, 0:8]))
    ink = (np.abs(a - bg) > params.THRESHOLD).astype(np.float32)[y0:y1, x0:x1]

    im = Image.open(path).convert("RGB").resize(params.SCENE_SIZE).crop(tuple(bbox))
    g = np.asarray(im.convert("L"), dtype=np.float32)
    ed = np.zeros_like(g)
    ed[:, 1:] = np.maximum(ed[:, 1:], np.abs(np.diff(g, axis=1)))
    ed[1:, :] = np.maximum(ed[1:, :], np.abs(np.diff(g, axis=0)))
    edge = (ed > jm.EDGE_THRESHOLD).astype(np.float32)

    if edge[mask].std() > 0 and ink[mask].std() > 0:
        corr = float(np.corrcoef(ink[mask].ravel(), edge[mask].ravel())[0, 1])
    else:
        corr = 0.0
    thr = spec["candidates"][spec["chosen"]]["threshold"]
    return {"metric": spec["chosen"], "corr": corr, "threshold": thr,
            "margin": corr - thr, "pass": bool(corr > thr)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cn", required=True)
    ap.add_argument("--bg-ip", required=True)
    ap.add_argument("--fig-cn", required=True, help="인물 크롭 안의 ControlNet 강도")
    ap.add_argument("--sip", required=True, help="인물 단계 전신 표본 IP 강도")
    ap.add_argument("--seeds", default=",".join(str(s) for s in params.SCENE_SEEDS))
    ap.add_argument("--json", default=os.path.join(params.NOTES, "final-verdict.json"))
    a = ap.parse_args()
    cn = float(a.cn)
    bg_ip = float(a.bg_ip)
    fig_cn = float(a.fig_cn)
    sip = float(a.sip)
    seeds = [int(s) for s in a.seeds.split(",")]

    s1 = _load_s1()
    if s1["axis_b"]["threshold"] is None:
        sys.exit("축 B 임계가 비어 있다 — part 2가 파생하지 않았다")
    emb = jm.Embedder()

    verdict = {"cn": cn, "bg_ip": bg_ip, "fig_cn": fig_cn, "sample_ip": sip,
               "thresholds_from": "notes/s1-baseline.json", "seeds": {}}
    for seed in seeds:
        final = os.path.join(OUT, f"3-final-{gf.tag(cn, bg_ip, fig_cn, sip)}-s{seed}.png")
        if not os.path.exists(final):
            print(f"[s{seed}] 최종이 없다: {os.path.basename(final)} — 건너뛴다")
            continue
        r = {
            "final": os.path.basename(final),
            "axis_a": axis_a(final, s1["axis_a"]["thresholds"]),
            "axis_b": axis_b(emb, cn, seed, s1["axis_b"]["threshold"], bg_ip, fig_cn, sip),
            "axis_c": axis_c(final, s1["axis_c"]["thresholds_by_key"]),
            "axis_d": axis_d(final, s1["axis_d"]),
        }
        # 축 C가 `machine_gate_ready: false`면 그 축은 게이트가 아니다 — 판정은 내되 종합에서
        # 빼고, 어느 축이 종합에 들어갔는지를 기록한다(끼워 맞추지 않는다).
        gate = {"axis_a": True, "axis_b": s1["axis_b"]["machine_gate_ready"],
                "axis_c": s1["axis_c"]["machine_gate_ready"],
                "axis_d": s1["axis_d"]["machine_gate_ready"]}
        r["gated_axes"] = [k for k, v in gate.items() if v]
        r["all_gated_pass"] = all(r[k]["pass"] for k in r["gated_axes"])
        r["all_four_pass"] = all(r[f"axis_{x}"]["pass"] for x in "abcd")
        verdict["seeds"][str(seed)] = r

        A, B, C, D = r["axis_a"], r["axis_b"], r["axis_c"], r["axis_d"]
        print(f"\n[시드 {seed}] {r['final']}")
        print(f"  축 A  ink={A['ink']:.4f} p05={A['val_p05']:.3f}  "
              f"{'✅' if A['pass'] else '❌'}{' ⚠상한초과' if A['ink_over_max_warn'] else ''}")
        for who, v in B["by_person"].items():
            print(f"  축 B  {who:8s} {v['score']:+.4f} (임계 {B['threshold']:+.4f}, "
                  f"여유 {v['margin']:+.4f})  {'✅' if v['pass'] else '❌'}")
        for key, v in C["by_key"].items():
            print(f"  축 C  {key:8s} {v['corr']:+.4f} (임계 {v['threshold']:+.4f}, "
                  f"여유 {v['margin']:+.4f})  {'✅' if v['pass'] else '❌'}")
        print(f"  축 D  상관 {D['corr']:+.4f} (임계 {D['threshold']:+.4f}, "
              f"여유 {D['margin']:+.4f})  {'✅' if D['pass'] else '❌'}")
        print(f"  → 게이트 축 {r['gated_axes']} 전부 통과 = {r['all_gated_pass']}  ·  "
              f"4축 전부 통과 = {r['all_four_pass']}")

    n_gated = sum(v["all_gated_pass"] for v in verdict["seeds"].values())
    n_four = sum(v["all_four_pass"] for v in verdict["seeds"].values())
    verdict["n_seeds"] = len(verdict["seeds"])
    verdict["n_all_gated_pass"] = n_gated
    verdict["n_all_four_pass"] = n_four
    verdict["reproduced"] = bool(n_gated >= 2)   # 계획 S4 완료기준: 3시드 중 2개 이상
    with open(a.json, "w", encoding="utf-8") as f:
        json.dump(verdict, f, ensure_ascii=False, indent=1)
    print(f"\n{'=' * 78}\n게이트 축 전부 통과 {n_gated}/{verdict['n_seeds']} 시드  ·  "
          f"4축 전부 통과 {n_four}/{verdict['n_seeds']} 시드  ·  "
          f"재현(2/3 이상) = {verdict['reproduced']}")
    print(f"기록: {a.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
