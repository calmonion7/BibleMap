#!/usr/bin/env python3
"""task#349 S1/S2 — klein 얼굴 적중률(참조 1명 대 2명, 머리당 시드 8)과 화질 표본 R1. 설정은 params.FACE_HITRATE_*(실행 전 고정).
  python3 gen_face_hitrate.py klein     # S1 klein 48장(GPU, 한 번에 하나 — mflux CLI를 한 장씩 부른다, 이미 있는 파일은 건너뜀)
  VENV=~/.local/biblemap-imggen/.venv314/bin/python; $VENV gen_face_hitrate.py r1   # S2 화질 표본 R1 4장(CPU)
출력: samples/face-hitrate/K2-<장면>-s<시드>.png · K1-<장면>-<인물>-s<시드>.png · R1-<장면>-s<시드>.png. 346·348 산출은 건드리지 않는다."""
import os, subprocess, sys

from PIL import Image

import params
from gen_face_ab_klein import MFLUX, FROZEN_DIR

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "samples", "face-hitrate")
# 장면 속 누구인가 — 길갈은 gen_face_widen, 엔게디는 gen_face_ab_klein의 묘사 그대로
DESC = {"gilgal": {"saul": "the tall bearded king on the right", "samuel": "the old white-haired prophet on the left"},
        "engedi": {"david": "the young kneeling man on the left", "saul": "the crouching king on the right"}}
KEEP = ("Image 1 is a finished pencil storybook illustration. Keep image 1 exactly as it is — same composition, bodies, poses, "
        "clothes, background, lighting and soft pencil art style — and redraw only ")


def cap(s):
    return s[0].upper() + s[1:]


def k2(scene, seed):
    return os.path.join(OUT, f"K2-{scene}-s{seed}.png")


def k1(scene, who, seed):
    return os.path.join(OUT, f"K1-{scene}-{who}-s{seed}.png")


def jobs():
    for scene, whos in params.FACE_HITRATE_SCENES.items():
        same = " ".join(f"{cap(DESC[scene][w])} has exactly the face, hair and beard of the man in image {2 + i}." for i, w in enumerate(whos))
        for seed in params.FACE_HITRATE_SEEDS:
            yield k2(scene, seed), [os.path.join(FROZEN_DIR, f"{w}.png") for w in whos], scene, KEEP + "the faces. " + same, seed
            for w in whos:
                prompt = (KEEP + f"the face of {DESC[scene][w]}; leave every other face unchanged. "
                          f"{cap(DESC[scene][w])} has exactly the face, hair and beard of the man in image 2.")
                yield k1(scene, w, seed), [os.path.join(FROZEN_DIR, f"{w}.png")], scene, prompt, seed


def klein():
    for out, refs, scene, prompt, seed in jobs():
        if os.path.exists(out):
            continue
        cmd = [MFLUX, "--model", "flux2-klein-4b", "-q", "8", "--image-paths", os.path.join(OUT, f"approved-{scene}.png"), *refs,
               "--prompt", prompt, "--seed", str(seed), "--steps", "4", "--width", "1216", "--height", "640", "--output", out]
        print("[klein]", os.path.basename(out), flush=True)
        subprocess.run(cmd, check=False)


def r1():
    from face_ab_heads import heads
    from gen_face_style import paste_heads
    for scene, whos in params.FACE_HITRATE_SCENES.items():
        base = Image.open(os.path.join(OUT, f"approved-{scene}.png")).convert("RGB")
        for seed in params.FACE_HITRATE_R1_SEEDS:
            src = k2(scene, seed)
            im = paste_heads(base, Image.open(src).convert("RGB"), heads(scene, src), whos, params.FACE_WIDEN_R1_GROW, f"{scene} {seed}")
            out = os.path.join(OUT, f"R1-{scene}-s{seed}.png")
            im.save(out)
            print("저장", out, flush=True)


if __name__ == "__main__":
    {"klein": klein, "r1": r1}[sys.argv[1]]()
