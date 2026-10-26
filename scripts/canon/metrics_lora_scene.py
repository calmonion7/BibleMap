#!/usr/bin/env python3
"""task 357 S3 — LoRA 장면 72장 + 353 음성 대조 9쌍의 목록·생성 시간·대상 머리 상자 → samples/lora-scene/metrics.json.
  VENV=~/.local/biblemap-imggen/.venv314/bin/python; $VENV metrics_lora_scene.py
머리는 OWLv2(face_ab_heads, CPU) — 353 페이지와 같은 좌우 구간·같은 대체(명세 구역 위). 생성과 겹치지 않게 생성이 끝난 뒤 돈다."""
import json, os

from PIL import Image

import params
from make_cast_v2_pilot_page import head
import gen_lora_scene as G

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "samples", "lora-scene", "metrics.json")
PILOT = os.path.expanduser("~/.local/biblemap-imggen/cast-v2-pilot/scene")
REFS = {"gilgal": os.path.join(HERE, "samples", "face-widen", "approved-gilgal.png"),
        "engedi": os.path.join(HERE, "samples", "face-ab", "approved-engedi.png"),
        "ramah": os.path.join(PILOT, "authored-david-ramah-samuel", "s11.png")}


def main():
    old = json.load(open(OUT)) if os.path.exists(OUT) else {}
    log = {e["out"]: e for e in json.load(open(G.JOBS + ".log.json"))} if os.path.exists(G.JOBS + ".log.json") else {}
    scenes, path, heads, fallback = [], {"L1": {}, "L2": {}}, {}, 0

    def boxes(key, p, whos):
        nonlocal fallback
        im = Image.open(p)
        out = {}
        for w in whos:
            b, how = head(key, w, p)
            fallback += how == "region"
            out[w] = [b[0] / im.width, b[1] / im.height, b[2] / im.width, b[3] / im.height]
        heads[p] = out
        return out

    for key, (sid, whos) in params.LORA_SCENE_SCENES.items():
        for cond in ("L1", "L2"):
            for who in (whos if cond == "L1" else ["both"]):
                for s in params.LORA_SCENE_SEEDS:
                    p = os.path.join(G.OUT, cond, key, f"{who}-s{s}.png")
                    assert os.path.exists(p), p
                    path[cond].setdefault(key, {}).setdefault(who, {})[str(s)] = p
                    scenes.append({"cond": cond, "scene": key, "loras": whos if who == "both" else [who], "seed": s, "path": p,
                                   "secs": log.get(p, {}).get("secs"), "active": log.get(p, {}).get("active"),
                                   "heads": boxes(key, p, whos)})
    controls = []
    for who, (a, b) in params.LORA_SCENE_PAIRS.items():
        for s in params.LORA_SCENE_CONTROL_SEEDS:
            pa, pb = (os.path.join(PILOT, params.LORA_SCENE_SCENES[k][0], f"s{s}.png") for k in (a, b))
            boxes(a, pa, params.LORA_SCENE_SCENES[a][1]); boxes(b, pb, params.LORA_SCENE_SCENES[b][1])
            controls.append({"who": who, "seed": s, "a": pa, "b": pb})
    m = {**old, "scenes": scenes, "controls": controls, "scene_path": path, "heads": heads, "refs": REFS,
         "head_fallback": fallback, "l1": old.get("l1", {}), "l2": old.get("l2", {}), "verdict": old.get("verdict")}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(m, open(OUT, "w"), ensure_ascii=False, indent=1)
    print(f"[LoraScene] metrics scenes {len(scenes)} controls {len(controls)} 머리 대체 {fallback}", flush=True)


if __name__ == "__main__":
    main()
