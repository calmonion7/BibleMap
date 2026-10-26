#!/usr/bin/env python3
"""task#346 S5 — samples/face-ab/*.png 각 장의 사울·다윗 머리를 찾아 S2 자(마진 점수)와 VLM 「같은 사람」 판정을 참고 수치로 낸다.
  VENV=~/.local/biblemap-imggen/.venv314/bin/python; PATH=<진짜 claude 앞세움>:$PATH $VENV metrics_face_ab.py
출력: samples/face-ab/metrics.json. 참고용 — 출발 방식·갈래 판정은 사람 몫(점수는 크기 우대를 뺀 CLIP 마진이라 절대 기준이 아니다)."""
import glob, json, os, tempfile

from PIL import Image

import check_face_scale as cfs
import check_face_judge as cfj
from face_ab_heads import heads

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "samples", "face-ab")
FROZEN_DIR = os.path.join(HERE, "frozen")
OTHERS = ["jonathan", "samuel", "abner", "joab", "nathan", "absalom"]   # S2와 같은 마진 기준 — 옛 정본 6명(retired-sdxl 아님)
WHO = {"gilgal": ["saul"], "engedi": ["david", "saul"]}


def main():
    import judge_metrics as jm
    emb = jm.Embedder()
    canon = {w: Image.open(os.path.join(FROZEN_DIR, f"{w}.png")).convert("RGB") for w in ("saul", "david")}
    cbox = {w: cfs.detect_head(os.path.join(FROZEN_DIR, f"{w}.png")) for w in canon}
    old = [Image.open(os.path.join(FROZEN_DIR, f"{k}.png")).convert("RGB") for k in OTHERS]
    tmp = tempfile.mkdtemp()
    res = {}
    for path in sorted(glob.glob(os.path.join(OUT, "*.png"))):
        name = os.path.basename(path)[:-4]
        scene = "gilgal" if "gilgal" in name else "engedi"
        im = Image.open(path).convert("RGB")
        res[name] = {}
        for who, box in heads(scene, path).items():
            if who not in WHO[scene]:
                continue
            others = old + [canon[o] for o in canon if o != who]
            score, px = cfs.face_score(canon[who], im, box, emb, cbox[who], others)
            crop = os.path.join(tmp, f"{name}-{who}.png")
            cfs.head_crop(im, box)[0].save(crop)
            v = cfj.same_person(os.path.join(FROZEN_DIR, f"{who}.png"), crop)
            res[name][who] = {"box": [round(b) for b in box], "face_px": round(px), "score": round(score, 3),
                              "same": v.get("same"), "reason": v.get("reason")}
            print(name, who, res[name][who]["score"], res[name][who]["same"], flush=True)
    json.dump(res, open(os.path.join(OUT, "metrics.json"), "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
