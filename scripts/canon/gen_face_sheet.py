#!/usr/bin/env python3
"""task#346 S3 — A 갈래: 인물별 Z-Image 다각도 시트 후보 40장(클로즈업 14·상반신 14·몸 전체 12).

  VENV=~/.local/biblemap-imggen/.venv314/bin/python
  $VENV gen_face_sheet.py --who saul [--out ~/.local/biblemap-imggen/face-ab]

후보는 <out>/cand-<인물>/NN.png + NN.txt(캡션). 프롬프트는 정본 생성(gen_face_canon)의 화풍·어휘에서 출발해
구도와 각도만 바꾼다. 생성은 한 번에 하나(batch/run_scene 워커).
"""
import argparse, json, os, sys

import params
import gen_face_canon as g

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "batch"))
import run_scene

ANGLES = ["facing forward", "turned three-quarters to the left", "turned three-quarters to the right",
          "in left profile", "in right profile", "head tilted slightly up", "head tilted slightly down",
          "facing forward, gentle smile", "three-quarter view, solemn expression", "looking over the shoulder"]
# (구도 키, 문구, 장수)
SHOTS = [("close", "close-up head portrait", 14), ("half", "waist-up portrait", 14), ("full", "full-body standing figure", 12)]


def plan(cid):
    out, i = [], 0
    for key, phrase, n in SHOTS:
        for k in range(n):
            out.append((i, key, phrase, ANGLES[(k + (3 if key == "full" else 0)) % len(ANGLES)]))
            i += 1
    return out


def prompt(cid, phrase, angle):
    c = json.load(open(os.path.join(HERE, "cast", f"{cid}.json"), encoding="utf-8"))
    return (f"{g.STYLE}, {phrase}, {angle}, plain cream background. "
            f"{c['era']} {g.LOOK[cid]}, {c['hair']}, {c['beard']}, hair covering the whole head down to the forehead, no hat, dark wool tunic.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--who", required=True, choices=["saul", "david"])
    ap.add_argument("--out", default=os.path.expanduser("~/.local/biblemap-imggen/face-ab"))
    a = ap.parse_args()
    d = os.path.join(a.out, f"cand-{a.who}")
    os.makedirs(d, exist_ok=True)
    jobs = []
    for i, key, phrase, angle in plan(a.who):
        f = os.path.join(d, f"{i:02d}")
        w, h = params.FACE_SHEET_SIZES[key]
        open(f + ".txt", "w", encoding="utf-8").write(f"{a.who}face, {phrase}, {angle}, {g.STYLE}")
        if not os.path.exists(f + ".png"):
            jobs.append({"prompt": prompt(a.who, phrase, angle), "seed": params.FACE_SHEET_SEED0 + i, "w": w, "h": h, "out": f + ".png"})
    print(f"[{a.who}] 후보 {len(jobs)}장 생성", flush=True)
    if jobs:
        print("초:", run_scene.gen_zimage(jobs, d))
