#!/usr/bin/env python3
"""task 353 S2 — 넓힌 정의(cast-vocab-2)만으로 사울·다윗·사무엘 정본 후보와 장면 3곳을 한 번에 그린다.

  VENV=~/.local/biblemap-imggen/.venv314/bin/python
  $VENV gen_cast_v2_pilot.py [--out ~/.local/biblemap-imggen/cast-v2-pilot]

정본: 인물 3 × 시드 params.FACE_CANON_SEEDS(8) × 정면·3/4(gen_face_canon.prompt) → <out>/face/<id>/s<시드>-<view>.png
장면: 3곳 × 시드 params.SCENE_SEEDS(3), derive_scene.whole_prompt(얼굴 참조·IP 없음) → <out>/scene/<장면>/s<시드>.png
산출은 레포 밖. 같은 프롬프트·시드면 다시 그려지므로 커밋은 대표만(349 회고). Z-Image 워커 한 번(enc→gen)에 전부 — 생성은 한 번에 하나.
"""
import argparse, json, os, sys

import params
import derive_scene as ds
import gen_face_canon as g

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "batch"))
WHO = ("saul", "david", "samuel")
SCENES = ("authored-saul-gilgal-coronation", "authored-david-en-gedi-saul", "authored-david-ramah-samuel")
SCENE_SIZE = (1216, 640)   # 345 한 장 모드 캔버스(run_scene.ZI_BG)


def jobs(out):
    js = []
    w, h = params.FACE_CANON_SIZE
    for cid in WHO:
        for s in params.FACE_CANON_SEEDS:
            for v in g.VIEWS:
                js.append({"prompt": g.prompt(cid, v), "seed": s, "w": w, "h": h, "out": os.path.join(out, "face", cid, f"s{s}-{v}.png")})
    for sc in SCENES:
        for s in params.SCENE_SEEDS:
            js.append({"prompt": ds.whole_prompt(ds.load(sc)), "seed": s, "w": SCENE_SIZE[0], "h": SCENE_SIZE[1],
                       "out": os.path.join(out, "scene", sc, f"s{s}.png")})
    return js


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.expanduser("~/.local/biblemap-imggen/cast-v2-pilot"))
    a = ap.parse_args()
    js = jobs(a.out)
    for j in js:
        os.makedirs(os.path.dirname(j["out"]), exist_ok=True)
    json.dump({j["out"]: {"prompt": j["prompt"], "seed": j["seed"]} for j in js},
              open(os.path.join(a.out, "prompts.json"), "w"), ensure_ascii=False, indent=1)
    todo = [j for j in js if not os.path.exists(j["out"])]
    print(f"[Pilot] {len(js)}장 중 {len(todo)}장 생성", flush=True)
    if todo:
        import run_scene
        secs = run_scene.gen_zimage(todo, a.out)
        print(f"[Pilot] 완료 {len(secs)}장 합 {sum(secs):.0f}s", flush=True)
