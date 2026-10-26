#!/usr/bin/env python3
"""task#348 S2/S3 — 조건부 R1을 새 장면(골리앗 다윗)·새 인물(길갈 사무엘)로 넓힌다. 설정은 params.FACE_WIDEN_*(실행 전 고정).
  python3 gen_face_widen.py klein       # S2 klein (e) 4장(GPU, 한 번에 하나 — mflux CLI를 한 장씩 부른다)
  VENV=~/.local/biblemap-imggen/.venv314/bin/python; $VENV gen_face_widen.py r1   # S3 R1 되붙이기 4장(CPU)
출력: samples/face-widen/B-e-<장면>-s<시드>.png · R1-g<배율>-<장면>-s<시드>.png. 346 face-ab 산출은 건드리지 않는다."""
import os, subprocess, sys

from PIL import Image

import params
from gen_face_ab_klein import MFLUX, FROZEN_DIR

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "samples", "face-widen")
# 참조 정본(이미지 번호 순) → 장면 속 누구인가
DESC = {"goliath": {"david": "the curly-haired youth with the sling on the left"},
        "gilgal": {"saul": "the tall bearded king on the right", "samuel": "the old white-haired prophet on the left"}}


def be(scene, seed):
    return os.path.join(OUT, f"B-e-{scene}-s{seed}.png")


def klein():
    for scene, (_, whos) in params.FACE_WIDEN_SCENES.items():
        refs = [os.path.join(FROZEN_DIR, f"{w}.png") for w in whos]
        who = " ".join(f"{DESC[scene][w][0].upper() + DESC[scene][w][1:]} has exactly the face, hair and beard of the man in image {2 + i}."
                       for i, w in enumerate(whos))
        prompt = ("Image 1 is a finished pencil storybook illustration. Keep image 1 exactly as it is — same composition, bodies, poses, "
                  "clothes, background, lighting and soft pencil art style — and redraw only the faces. " + who)
        for seed in params.FACE_WIDEN_SEEDS:
            out = be(scene, seed)
            if os.path.exists(out):
                continue
            cmd = [MFLUX, "--model", "flux2-klein-4b", "-q", "8", "--image-paths", os.path.join(OUT, f"approved-{scene}.png"), *refs,
                   "--prompt", prompt, "--seed", str(seed), "--steps", "4", "--width", "1216", "--height", "640", "--output", out]
            print("[klein]", os.path.basename(out), flush=True)
            subprocess.run(cmd, check=False)


def r1():
    from face_ab_heads import heads
    from gen_face_style import paste_heads
    g = params.FACE_WIDEN_R1_GROW
    for scene, (_, whos) in params.FACE_WIDEN_SCENES.items():
        base = Image.open(os.path.join(OUT, f"approved-{scene}.png")).convert("RGB")
        for seed in params.FACE_WIDEN_SEEDS:
            im = paste_heads(base, Image.open(be(scene, seed)).convert("RGB"), heads(scene, be(scene, seed)), whos, g, f"{scene} {seed}")
            out = os.path.join(OUT, f"R1-g{g}-{scene}-s{seed}.png")
            im.save(out)
            print("저장", out, flush=True)


if __name__ == "__main__":
    {"klein": klein, "r1": r1}[sys.argv[1]]()
