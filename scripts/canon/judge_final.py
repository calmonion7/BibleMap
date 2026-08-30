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

**축 E 5축 재확인**(2026-08-28 신설) — 인물별 머리 밴드에 정본 5축의 대립쌍을 걸어 마진의 **부호**를
본다. 5축이 프롬프트 파생(입력)에만 쓰이고 출력 검증에는 안 쓰이던 비대칭을 메운다(뿔·투구가
사라진 것을 축 A~D 중 아무것도 잡지 못했다). `sex`는 정본 자신이 통과하지 못해 게이트에서 뺀다.

**축 G 팔이 사지인가**(2026-08-30 배선, task#322 S4) — 콘티 팔 중심선의 법선 위에서 「중심이
매끄럽고 양쪽에 경계가 있으며 그 간격이 w_min 이상인」 표본의 비율. part 1(task#321)이 후보
7개를 대조군에 걸어 고른 자다: 부위별 상관은 음성 B(관통) +0.489 > 양성(콘티) +0.226이라
임계를 어디 두든 못 갈랐고, 이 자만 승인본 s11(분리)·s7(관통)을 둘 다 떨어뜨렸다.
축 A~F가 여섯 축을 다 통과시킨 그림들이 팔에서 깨져 있었다는 것이 이 축의 존재 이유다.

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


def axis_b(emb, cn, seed, threshold, bg_ip, fig_cn, sip, ref_band=None, head_cn=None):
    """전이 점수 = Δ(자기 표본) − Δ(남의 표본). 기준선은 그 인물을 그리기 직전 캔버스.

    **정의역 = 머리 밴드** (task#322 R4 — 2026-08-30 사람 승인 갈림길 ②). 전신 크롭은 정체성
    전이와 **자세 복제를 한 값에 섞으므로**, 축 B를 세게 통과할수록 자세가 콘티에서 멀어진다
    (ZIMAGE §9-27의 구조적 상충). `judge_s1.axis_b`가 임계를 **밴드 정의역에서 파생**하도록
    바뀌었으므로 장면 쪽도 같은 정의역이어야 한다 — 임계만 밴드에서 오고 측정은 전신이면
    정의역 불일치다.

    **양쪽 밴드가 왜 서로 다른 함수인가**: 분율(`HEAD_BAND`)은 **세로 전신 표본 전용**이다
    (judge_s1.py의 `HEAD_BAND` 주석). 장면에 그 분율을 쓰면 다윗은 물매를 머리 위로 치켜들고
    있어 밴드에 **머리가 한 화소도 안 든다**(§9-10 실측 — 2026-08-30 R4에서 재확인: 창
    (169,60,676,640)의 상단 0.30은 하늘과 물매뿐이었다). 그래서 장면은 콘티 저작 머리 원에서
    파생하는 `judge_s1._band_scene`을 쓴다 — 손으로 고른 상자가 아니라 저작자가 id로 명시한
    도형에서 나온다. 둘이 **같은 부위**라는 근거는 코드베이스 자신에 있다: `judge_s1.axis_e`의
    양성 대조군이 `_band_fullbody(표본)`을 `conti_head_box` 상자에 그대로 붙여 넣고 8/8로
    통과한다(judge_s1.py 「장면합성 표본머리」).
    """
    samples = {n: emb.embed(judge_s1._band_fullbody(os.path.join(gf.SAMPLES, f"{n}.png")))
               for n in gf.PEOPLE}
    t = gf.tag(cn, bg_ip, fig_cn, sip, ref_band, head_cn)
    david_out = os.path.join(OUT, f"1-david-{t}-s{seed}.png")
    stage = {
        "david": (gf.bg_path(cn, seed, bg_ip), david_out),
        "goliath": (david_out, os.path.join(OUT, f"2-goliath-{t}-s{seed}.png")),
    }
    rows = {}
    for who in gf.PEOPLE:
        base_p, cur_p = stage[who]
        other = "goliath" if who == "david" else "david"
        def _band(p):
            im = Image.open(p).convert("RGB").resize(params.SCENE_SIZE)
            return judge_s1._band_scene(im, who)
        e_base = emb.embed(_band(base_p))
        e_cur = emb.embed(_band(cur_p))
        d_self = jm.cos(e_cur, samples[who]) - jm.cos(e_base, samples[who])
        d_cross = jm.cos(e_cur, samples[other]) - jm.cos(e_base, samples[other])
        score = d_self - d_cross
        rows[who] = {"score": score, "d_self": d_self, "d_cross": d_cross,
                     "margin": score - threshold, "pass": bool(score > threshold),
                     "base": os.path.basename(base_p), "cur": os.path.basename(cur_p)}
    return {"threshold": threshold, "by_person": rows,
            "domain": "머리 밴드 — 표본은 _band_fullbody(상단 0.30), 장면은 _band_scene(콘티 머리 원)",
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


def axis_e(path, spec):
    """인물별 머리 밴드에 정본 5축 대립쌍을 걸어 마진의 부호를 본다. judge_s1의 산식을 그대로 쓴다."""
    axes = spec["canon_axes"]
    gated = spec["gated_axes"]
    tv = judge_s1.axis_e_text_vectors()
    emb = jm.Embedder()
    im = Image.open(path).convert("RGB").resize(params.SCENE_SIZE)
    rows = {}
    for who in gf.PEOPLE:
        band = judge_s1._band_scene(im, who)   # 밴드 = 콘티 저작 머리 원(분율 손잡이 폐지, §9-10)
        m = judge_s1.axis_e_margins(band, who, axes[who], tv, emb)
        rows[who] = {"margins": m, "failed_axes": [a for a in gated if m[a] <= 0],
                     "pass": all(m[a] > 0 for a in gated)}
    return {"gated_axes": gated,
            "head_boxes": {w: list(judge_s1.conti_head_box(w)) for w in gf.PEOPLE},
            "by_person": rows, "pass": all(r["pass"] for r in rows.values())}


def axis_f(path, spec):
    """갑주 착용 여부 — 게이트 인물의 몸통 밴드에 의상 대립쌍을 걸어 부호를 본다.
    ⚠ 종류(비늘 vs 판금)는 재지 않는다 — `spec["does_not_measure"]` 참조."""
    gated = spec["gated_people"]
    tv = judge_s1.costume_text_vectors()
    emb = jm.Embedder()
    im = Image.open(path).convert("RGB").resize(params.SCENE_SIZE)
    rows = {}
    for who in gated:
        band = im.crop(tuple(spec["torso_boxes"][who]))
        mg = judge_s1.costume_margin(band, who, tv, emb)
        rows[who] = {"margin": mg, "pass": bool(mg > 0)}
    return {"gated_people": gated, "by_person": rows,
            "pass": all(r["pass"] for r in rows.values())}


def axis_g(path, spec):
    """축 G 팔이 사지인가 — part 1(task#321)이 후보 7개를 대조군에 걸어 고른 자다.

    **judge_s1의 기하·로더·엣지 산식을 그대로 재사용한다.** 임계만 물려받고 정의역이 갈리면
    「옳은 결론을 틀린 이유로」가 된다 — 회고 `260830-093209`이 축 E에서 실측한 결함이고,
    회고 `260830-125935`이 「양성 대조군의 정의역이 판정 대상의 정의역과 같은지 먼저 본다」로
    승급한 습관이다. part 1의 사다리·음성 4종·양성이 전부 `_axis_c_load` + `_edge_bool_f`로
    재어졌으므로 여기서도 그 둘을 쓴다.

    이 파일은 임계를 만들지 않는다 — `s1-baseline.json`의 `axis_g.threshold`를 읽는다
    (축 A~F와 같은 규약, ADR `260823-221839`).
    """
    g = judge_s1.arm_geometry()
    samples = judge_s1.arm_centerline(g["ink"])
    v = judge_s1.arm_limb_score(g, samples)(
        judge_s1._edge_bool_f(judge_s1._axis_c_load(path)))
    thr = spec["threshold"]
    return {"score": v, "threshold": thr, "margin": v - thr,
            "domain_px": int(g["ink"].sum()), "pass": bool(v > thr)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cn", required=True)
    ap.add_argument("--bg-ip", required=True)
    ap.add_argument("--fig-cn", required=True, help="인물 크롭 안의 ControlNet 강도")
    ap.add_argument("--sip", required=True, help="인물 단계 전신 표본 IP 강도")
    ap.add_argument("--seeds", default=",".join(str(s) for s in params.SCENE_SEEDS))
    ap.add_argument("--ref-band", type=float, default=None,
                    help="생성 때 쓴 `gen_final.py --ref-band` 값 — 산출물 이름이 그것을 담으므로 "
                         "같은 값을 줘야 그 그림을 찾는다")
    ap.add_argument("--head-cn", type=float, default=None,
                    help="생성 때 쓴 `gen_final.py --head-cn` 값 — 켰으면 산출물 이름이 그것도 "
                         "담으므로 같은 값을 줘야 그 그림을 찾는다(생략하면 머리 단계 없는 이름)")
    ap.add_argument("--json", default=os.path.join(params.NOTES, "final-verdict.json"))
    a = ap.parse_args()
    cn = float(a.cn)
    bg_ip = float(a.bg_ip)
    fig_cn = float(a.fig_cn)
    sip = float(a.sip)
    ref_band = a.ref_band
    head_cn = a.head_cn
    seeds = [int(s) for s in a.seeds.split(",")]

    s1 = _load_s1()
    if s1["axis_b"]["threshold"] is None:
        sys.exit("축 B 임계가 비어 있다 — part 2가 파생하지 않았다")
    emb = jm.Embedder()

    verdict = {"cn": cn, "bg_ip": bg_ip, "fig_cn": fig_cn, "sample_ip": sip,
               "thresholds_from": "notes/s1-baseline.json", "seeds": {}}
    for seed in seeds:
        final = os.path.join(OUT, f"3-final-{gf.tag(cn, bg_ip, fig_cn, sip, ref_band, head_cn)}-s{seed}.png")
        if not os.path.exists(final):
            print(f"[s{seed}] 최종이 없다: {os.path.basename(final)} — 건너뛴다")
            continue
        r = {
            "final": os.path.basename(final),
            "axis_a": axis_a(final, s1["axis_a"]["thresholds"]),
            "axis_b": axis_b(emb, cn, seed, s1["axis_b"]["threshold"], bg_ip, fig_cn, sip, ref_band, head_cn),
            "axis_c": axis_c(final, s1["axis_c"]["thresholds_by_key"]),
            "axis_d": axis_d(final, s1["axis_d"]),
            "axis_e": axis_e(final, s1["axis_e"]),
            "axis_f": axis_f(final, s1["axis_f"]),
            "axis_g": axis_g(final, s1["axis_g"]),
        }
        # 축 C가 `machine_gate_ready: false`면 그 축은 게이트가 아니다 — 판정은 내되 종합에서
        # 빼고, 어느 축이 종합에 들어갔는지를 기록한다(끼워 맞추지 않는다).
        gate = {"axis_a": True, "axis_b": s1["axis_b"]["machine_gate_ready"],
                "axis_c": s1["axis_c"]["machine_gate_ready"],
                "axis_d": s1["axis_d"]["machine_gate_ready"],
                "axis_e": s1["axis_e"]["machine_gate_ready"],
                "axis_f": s1["axis_f"]["machine_gate_ready"],
                "axis_g": s1["axis_g"]["machine_gate_ready"]}
        r["gated_axes"] = [k for k, v in gate.items() if v]
        r["all_gated_pass"] = all(r[k]["pass"] for k in r["gated_axes"])
        r["all_axes_pass"] = all(r[f"axis_{x}"]["pass"] for x in "abcdefg")
        verdict["seeds"][str(seed)] = r

        A, B, C, D, E, F, G = (r["axis_a"], r["axis_b"], r["axis_c"], r["axis_d"],
                               r["axis_e"], r["axis_f"], r["axis_g"])
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
        for who, v in E["by_person"].items():
            print(f"  축 E  {who:8s} " + " ".join(f"{a}={v['margins'][a]:+.4f}" for a in E["gated_axes"])
                  + f"  {'✅' if v['pass'] else '❌ ' + ','.join(v['failed_axes'])}")
        for who, v in F["by_person"].items():
            print(f"  축 F  {who:8s} 갑주착용 {v['margin']:+.4f}  {'✅' if v['pass'] else '❌'}"
                  f"   (⚠ 종류는 재지 않는다)")
        print(f"  축 G  다윗 팔  사지비율 {G['score']:+.4f} (임계 {G['threshold']:+.4f}, "
              f"여유 {G['margin']:+.4f}, 정의역 {G['domain_px']}화소)  {'✅' if G['pass'] else '❌'}")
        print(f"  → 게이트 축 {r['gated_axes']} 전부 통과 = {r['all_gated_pass']}  ·  "
              f"전 축 통과 = {r['all_axes_pass']}")

    n_gated = sum(v["all_gated_pass"] for v in verdict["seeds"].values())
    n_all = sum(v["all_axes_pass"] for v in verdict["seeds"].values())
    verdict["n_seeds"] = len(verdict["seeds"])
    verdict["n_all_gated_pass"] = n_gated
    verdict["n_all_axes_pass"] = n_all
    verdict["reproduced"] = bool(n_gated >= 2)   # 계획 S4 완료기준: 3시드 중 2개 이상
    with open(a.json, "w", encoding="utf-8") as f:
        json.dump(verdict, f, ensure_ascii=False, indent=1)
    print(f"\n{'=' * 78}\n게이트 축 전부 통과 {n_gated}/{verdict['n_seeds']} 시드  ·  "
          f"전 축 통과 {n_all}/{verdict['n_seeds']} 시드  ·  "
          f"재현(2/3 이상) = {verdict['reproduced']}")
    print(f"기록: {a.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
