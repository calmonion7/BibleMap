#!/usr/bin/env python3
"""Z-Image-Turbo 얼굴 정본 후보 생성(task#346 → 353). 정면과 3/4 측면을 시드마다 1장씩.

  VENV=~/.local/biblemap-imggen/.venv314/bin/python
  $VENV gen_face_canon.py [--who saul david samuel] [--out ~/.local/biblemap-imggen/face-canon-v2]

후보는 레포 밖(--out/<인물>/s<시드>-<front|34>.png)에 둔다. 문구는 **cast/<id>.json의 카드 층·얼굴 층에서만** 파생한다
(task 353 — 이 파일에 인물별 낱말을 두던 `LOOK` 상수는 카드 값과 어긋나서 지웠다: 사울 「fifties」 ↔ 카드 40대).
Z-Image 생성 프로세스는 batch/run_scene.py의 enc/gen 분리 워커를 그대로 쓴다. 머신에서 생성은 한 번에 하나.
"""
import argparse, json, os, sys

import params
import derive_scene as ds

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "batch"))

STYLE = "warm cream paper, soft pencil and colored-pencil storybook illustration, gentle hand-drawn lines"
VIEWS = {"front": "facing forward", "34": "three-quarter view, head turned slightly to the left"}


def look(cid):
    """카드 층·얼굴 층 → 머리 초상 서술(정본 생성·얼굴 시트·정본 판정 루브릭이 같이 쓴다)."""
    c = ds.load_cast(cid)
    card, face = c["card"], c["face"]
    look = [ds._who(c), card["ageBand"]["text"]]
    if card["beardVolume"]["class"] != "none":
        look.append(card["beardVolume"]["text"])
    look.append(ds.head_text(card))
    look += [face[k] for k in ("faceShape", "eyes", "nose", "mouth", "brows", "skin")]
    if face["marks"] != "none":
        look.append(face["marks"])
    return ", ".join(look + [f"wearing {card['costumeColor']['text']}"])


def prompt(cid, view="front"):
    return f"{STYLE}, close-up head portrait, {VIEWS[view]}, plain cream background. {look(cid)}, head and shoulders only."


if __name__ == "__main__":
    import run_scene
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.expanduser("~/.local/biblemap-imggen/face-canon-v2"))
    ap.add_argument("--who", nargs="+", default=["saul", "david", "samuel"])
    a = ap.parse_args()
    w, h = params.FACE_CANON_SIZE
    for cid in a.who:
        d = os.path.join(a.out, cid)
        os.makedirs(d, exist_ok=True)
        jobs = [{"prompt": prompt(cid, v), "seed": s, "w": w, "h": h, "out": os.path.join(d, f"s{s}-{v}.png")}
                for s in params.FACE_CANON_SEEDS for v in VIEWS if not os.path.exists(os.path.join(d, f"s{s}-{v}.png"))]
        print(f"[{cid}] {prompt(cid)}\n  후보 {len(jobs)}장 생성", flush=True)
        if jobs:
            run_scene.gen_zimage(jobs, d)
