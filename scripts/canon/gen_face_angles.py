#!/usr/bin/env python3
"""얼굴 각도 정본 시험(2026-10-22, task 350 회고 (가)·(나)). 설정은 params.FACE_ANGLE_*(실행 전 고정, notes/FACE-ANGLES.md).
  python3 gen_face_angles.py views     # (가) 정면 정본 → 3/4·옆얼굴, 인물 × 각도 × 시드 3 (klein 4B, 한 장씩)
  python3 gen_face_angles.py redraw    # (나) 기브아 바탕 8시드 × A(정면 참조)·B(3/4 참조) 얼굴만 다시 그림
출력(레포 밖): ~/.local/biblemap-imggen/face-angles/{views,redraw}/ — 이미 있는 파일은 건너뜀. 고른 각도 정본은 views/pick-<인물>.png."""
import os, subprocess, sys

import params
from gen_face_ab_klein import MFLUX, FROZEN_DIR
from gen_face_hitrate import KEEP

OUT = os.path.expanduser("~/.local/biblemap-imggen/face-angles")
BASE = os.path.expanduser(f"~/.local/biblemap-imggen/{params.FACE_ANGLE_SCENE_SET}/{params.FACE_ANGLE_SCENE}/base")
# 장면 속 누구인가 — 기브아 창 명세(사울 서서 창, 다윗 앉아 수금)
DESC = {"saul": "the tall bearded king standing on the right with the spear",
        "david": "the young man kneeling on the left playing the harp"}
VIEW_TEXT = {"three-quarter": "in three-quarter view, his head turned so that he looks toward the {side} side of the picture",
             "profile": "in full side profile, looking toward the {side} side of the picture"}


def view_path(who, view, seed):
    return os.path.join(OUT, "views", f"{who}-{view}-s{seed}.png")


def pick_path(who):
    return os.path.join(OUT, "views", f"pick-{who}.png")


def klein(images, prompt, seed, out, w, h):
    if os.path.exists(out):
        return
    os.makedirs(os.path.dirname(out), exist_ok=True)
    cmd = [MFLUX, "--model", "flux2-klein-4b", "-q", "8", "--image-paths", *images, "--prompt", prompt, "--seed", str(seed),
           "--steps", "4", "--width", str(w), "--height", str(h), "--output", out]
    print("[klein]", os.path.relpath(out, OUT), flush=True)
    subprocess.run(cmd, check=False)


def views():
    for who, side in params.FACE_ANGLE_PEOPLE.items():
        for view in params.FACE_ANGLE_VIEWS:
            prompt = ("Image 1 is a portrait of a man in a soft colored-pencil storybook style. Draw the very same man — exactly the same face, "
                      "eyes, nose, hair, beard, age and skin — " + VIEW_TEXT[view].format(side=side) +
                      ". Head and shoulders, same clothes, same plain cream paper background, same colored-pencil art style.")
            for seed in params.FACE_ANGLE_VIEW_SEEDS:
                klein([os.path.join(FROZEN_DIR, f"{who}.png")], prompt, seed, view_path(who, view, seed), 768, 768)


def redraw():
    whos = list(params.FACE_ANGLE_PEOPLE)
    same = " ".join(f"{DESC[w][0].upper() + DESC[w][1:]} has exactly the face, hair and beard of the man in image {2 + i}." for i, w in enumerate(whos))
    prompt = KEEP + "the faces. " + same
    refs = {"A": [os.path.join(FROZEN_DIR, f"{w}.png") for w in whos], "B": [pick_path(w) for w in whos]}
    missing = [p for p in refs["B"] if not os.path.exists(p)]
    if missing:
        sys.exit(f"[FaceAngles] 각도 정본을 먼저 고른다: {missing}")
    for seed in params.FACE_ANGLE_REDRAW_SEEDS:
        for arm, r in refs.items():
            klein([os.path.join(BASE, f"s{seed}.png"), *r], prompt, seed, os.path.join(OUT, "redraw", f"{arm}-s{seed}.png"), 1216, 640)


if __name__ == "__main__":
    {"views": views, "redraw": redraw}[sys.argv[1]]()
