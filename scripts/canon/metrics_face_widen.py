#!/usr/bin/env python3
"""task#348 S3 — 넓히기 머리 6개(골리앗 다윗 ×2, 길갈 사울 ×2·사무엘 ×2)의 참고 측정. 자는 347 metrics_face_style 그대로.
  VENV=~/.local/biblemap-imggen/.venv314/bin/python; $VENV metrics_face_widen.py   # → samples/face-widen/metrics.json
B-e 원본과 R1을 함께 재고, 347과 같은 기준으로 「참고 통과」를 매긴다. 머리 판정은 사람이 한다 — 이 값은 정답이 아니다."""
import json, os, tempfile

from PIL import Image

import params
from face_ab_heads import heads
from metrics_face_style import FROZEN_DIR, OTHERS, style

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "samples", "face-widen")


def main():
    import check_face_scale as cfs
    import check_face_judge as cfj
    import judge_metrics as jm
    emb = jm.Embedder()
    canon = {w: Image.open(os.path.join(FROZEN_DIR, f"{w}.png")).convert("RGB") for w in ("saul", "david", "samuel")}
    cbox = {w: cfs.detect_head(os.path.join(FROZEN_DIR, f"{w}.png")) for w in canon}
    old = {k: Image.open(os.path.join(FROZEN_DIR, f"{k}.png")).convert("RGB") for k in OTHERS if k not in canon}
    tmp = tempfile.mkdtemp()
    res = {}
    for scene, (_, ws) in params.FACE_WIDEN_SCENES.items():
        ref = Image.open(os.path.join(OUT, f"approved-{scene}.png")).convert("RGB")
        for seed in params.FACE_WIDEN_SEEDS:
            for kind in ("B-e", f"R1-g{params.FACE_WIDEN_R1_GROW}"):
                name = f"{kind}-{scene}-s{seed}"
                path = os.path.join(OUT, name + ".png")
                im = Image.open(path).convert("RGB")
                hb = heads(scene, os.path.join(OUT, f"B-e-{scene}-s{seed}.png"))   # R1은 B-e 머리 상자 자리에 붙였다
                hs = {}
                for who in ws:
                    if who not in hb:
                        hs[who] = {"missing": True}
                        continue
                    box = hb[who]
                    d, regs = style(im, ref, box)
                    others = list(old.values()) + [canon[o] for o in canon if o != who]
                    score, px = cfs.face_score(canon[who], im, box, emb, cbox[who], others)
                    crop = os.path.join(tmp, f"{name}-{who}.png")
                    cfs.head_crop(im, box)[0].save(crop)
                    v = cfj.same_person(os.path.join(FROZEN_DIR, f"{who}.png"), crop)
                    hs[who] = {"box": [round(b) for b in box], "face_px": round(px), "face_score": round(score, 3),
                               "same": v.get("same"), "reason": v.get("reason"), "style_dist": d, "style": regs}
                    print(name, who, d, round(score, 3), v.get("same"), flush=True)
                res[name] = {"scene": scene, "seed": seed, "heads": hs}
    for name, r in res.items():   # 참고 통과 = 347 기준 그대로(같은 장면·시드·인물의 B-e 원본 대비)
        if not name.startswith("R1"):
            continue
        base = res[f"B-e-{r['scene']}-s{r['seed']}"]["heads"]
        for who, h in r["heads"].items():
            b = base.get(who)
            h["ref_pass"] = bool(b and "missing" not in h and "missing" not in b
                                 and h["style_dist"] <= b["style_dist"] * params.FACE_STYLE_DIST_MAX_RATIO
                                 and h["face_score"] >= b["face_score"] * params.FACE_STYLE_FACE_MIN_RATIO
                                 and h["same"] is True)
    json.dump(res, open(os.path.join(OUT, "metrics.json"), "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
