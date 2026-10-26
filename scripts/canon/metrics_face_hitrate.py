#!/usr/bin/env python3
"""task#349 S2 — 머리 64개(4머리×K1·K2×시드 8) + 화질 표본 R1 머리 8개의 머리 상자와 화질 자(라플라시안 분산 비).
  VENV=~/.local/biblemap-imggen/.venv314/bin/python; $VENV metrics_face_hitrate.py   # → samples/face-hitrate/metrics.json
화질 자 = 머리 상자 안 회색조 4-이웃 라플라시안 분산 「대상 ÷ 승인본 같은 인물 머리」, > FACE_HITRATE_LAP_RATIO_MAX면 거칠다고 예측.
얼굴 자는 재지 않는다 — 얼굴은 사람이 판정한다(348 회고). 머리를 못 찾으면 box·lap·lap_ratio가 None이다."""
import json, os

import numpy as np
from PIL import Image

import params
from face_ab_heads import heads
from gen_face_hitrate import OUT, k1, k2


def lap_var(im, box):
    x0, y0, x1, y1 = (round(v) for v in box)
    g = np.asarray(im.convert("L").crop((x0, y0, x1, y1)), np.float64)
    lap = g[1:-1, :-2] + g[1:-1, 2:] + g[:-2, 1:-1] + g[2:, 1:-1] - 4 * g[1:-1, 1:-1]
    return float(lap.var())


NONE = {"box": None, "lap": None, "lap_ratio": None, "pred_rough": None}


def head(path, scene, who, ref, box=None):
    box = box or heads(scene, path).get(who)
    if box is None:
        return dict(NONE)
    lap = lap_var(Image.open(path), box)
    r = lap / ref
    return {"box": [round(b) for b in box], "lap": round(lap, 1), "lap_ratio": round(r, 3),
            "pred_rough": r > params.FACE_HITRATE_LAP_RATIO_MAX}


def main():
    res = {"approved": {}, "klein": [], "r1": []}
    ref = {}
    for scene, whos in params.FACE_HITRATE_SCENES.items():
        ap = os.path.join(OUT, f"approved-{scene}.png")
        hb = heads(scene, ap)
        for who in whos:
            ref[scene, who] = lap_var(Image.open(ap), hb[who])
            res["approved"][f"{scene}-{who}"] = {"box": [round(b) for b in hb[who]], "lap": round(ref[scene, who], 1)}
            print("승인본", scene, who, res["approved"][f"{scene}-{who}"], flush=True)
    for scene, whos in params.FACE_HITRATE_SCENES.items():
        for seed in params.FACE_HITRATE_SEEDS:
            for who in whos:
                for cond, path in (("K1", k1(scene, who, seed)), ("K2", k2(scene, seed))):
                    h = head(path, scene, who, ref[scene, who])
                    res["klein"].append({"scene": scene, "who": who, "cond": cond, "seed": seed, "file": os.path.basename(path), **h})
                    print(cond, scene, who, seed, h["lap_ratio"], flush=True)
        for seed in params.FACE_HITRATE_R1_SEEDS:
            hb = heads(scene, k2(scene, seed))   # R1은 K2 머리 상자 자리에 붙였다
            for who in whos:
                path = os.path.join(OUT, f"R1-{scene}-s{seed}.png")
                h = head(path, scene, who, ref[scene, who], hb[who]) if who in hb else dict(NONE)
                res["r1"].append({"scene": scene, "who": who, "seed": seed, "file": os.path.basename(path), **h})
                print("R1", scene, who, seed, h["lap_ratio"], flush=True)
    json.dump(res, open(os.path.join(OUT, "metrics.json"), "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
