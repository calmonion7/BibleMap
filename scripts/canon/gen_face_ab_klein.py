#!/usr/bin/env python3
"""task#346 S5 — B 갈래(FLUX.2 klein 4B 참조 편집/생성) 비교 생성. mflux CLI를 한 장씩 부른다(별도 프로세스 — 메모리 반환).
  python3 gen_face_ab_klein.py            # 8장 전부(이미 있는 파일은 건너뜀)
(e)=345 승인 그림 + 새 얼굴 정본을 참조로 「얼굴만 바꿔라」, (f)=정본만 참조로 345 장면 프롬프트를 새로 생성.
출력: samples/face-ab/B-<e|f>-<gilgal|engedi>-s<시드>.png. GPU 생성 프로세스는 머신에서 한 번에 하나."""
import os, subprocess, sys

import params
from derive_scene import load, whole_prompt

HERE = os.path.dirname(os.path.abspath(__file__))
PILOT = os.path.abspath(os.path.join(HERE, "..", "..", ".forge", "reports", "scene-whole-pilot"))
OUT = os.path.join(HERE, "samples", "face-ab")
FROZEN_DIR = os.path.join(HERE, "frozen")
MFLUX = os.path.expanduser("~/.local/biblemap-imggen/.venv-mflux/bin/mflux-generate-flux2-edit")
SCENE = {"gilgal": "authored-saul-gilgal-coronation", "engedi": "authored-david-en-gedi-saul"}
# 참조 정본(이미지 번호 순) → 장면 속 누구인가. 길갈의 사무엘은 새 정본이 없어 참조하지 않는다.
REFS = {"gilgal": [("saul", "the tall bearded king on the right")],
        "engedi": [("david", "the young kneeling man on the left"), ("saul", "the crouching king on the right")]}


def who_line(scene, first):
    return " ".join(f"{d[0].upper() + d[1:]} has exactly the face, hair and beard of the man in image {first + i}."
                    for i, (_, d) in enumerate(REFS[scene]))


def job(scene, start, seed):
    refs = [os.path.join(FROZEN_DIR, f"{w}.png") for w, _ in REFS[scene]]
    if start == "e":
        base = os.path.join(PILOT, SCENE[scene], "final.png")
        prompt = ("Image 1 is a finished pencil storybook illustration. Keep image 1 exactly as it is — same composition, bodies, poses, "
                  "clothes, background, lighting and soft pencil art style — and redraw only the faces. " + who_line(scene, 2))
        return [base] + refs, prompt
    prompt = whole_prompt(load(SCENE[scene])) + " " + who_line(scene, 1)
    return refs, prompt


def main():
    for scene in SCENE:
        for start in "ef":
            for seed in params.FACE_AB_SEEDS:
                out = os.path.join(OUT, f"B-{start}-{scene}-s{seed}.png")
                if os.path.exists(out):
                    continue
                imgs, prompt = job(scene, start, seed)
                cmd = [MFLUX, "--model", "flux2-klein-4b", "-q", "8", "--image-paths", *imgs, "--prompt", prompt,
                       "--seed", str(seed), "--steps", "4", "--width", "1216", "--height", "640", "--output", out]
                print("[klein]", os.path.basename(out), flush=True)
                subprocess.run(cmd, check=False)


if __name__ == "__main__":
    main()
