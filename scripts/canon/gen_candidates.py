"""task#314 S4 3단계 — 후보 생성(GPU). run_grid.py(task#308)와 같은 스택·설정을 승계한다:
스크리블 ControlNet + SDXL base(params.CN_MODEL·params.SDXL_BASE), params.STEPS 스텝,
params.GUIDANCE, IP-Adapter 없음(2층 후보를 만드는 단계 — 아직 물릴 레퍼런스가 없다).
강도(cn scale)는 조건 입력의 선 밀도에 따라 가른다 — params.py의 PERSON_CN/SCENE_CN 주석 참조.

대상 4개, 총 10장:
  david   × 4시드 (조건: 다윗 정본 두상)
  goliath × 4시드 (조건: 골리앗 정본 두상)
  bg-on   × 1시드 (조건: GoliathScene 전신, 배경 어휘 있음)
  bg-off  × 1시드 (조건: GoliathScene 전신, 배경 어휘 없음 — bg-on과 같은 시드·같은 구조 조건)

CLIP 77토큰 초과는 경고만 남기고 뒤를 조용히 버린다 — 하드 실패로 막는다(task#304/#308 선례).
"""
import itertools
import json
import os
import sys
import time

import torch
from diffusers import ControlNetModel, StableDiffusionXLControlNetPipeline
from PIL import Image

import params

OUT = os.path.join(params.OUT_ROOT, "gen")

with open(params.PROMPTS_JSON, encoding="utf-8") as f:
    P = json.load(f)
NEG = P["negative"]

# (대상, 조건 입력 파일, 프롬프트, negative, 강도, 생성 크기, 시드 목록)
# negative는 대상별이다 — 「없음」 축값(수염 없음·머리카락 없음)이 긍정 프롬프트가 아니라
# 여기로 간다(derive_prompts.py 참조: CLIP은 부정을 못 다룬다).
TARGETS = [
    ("david", "cond-david-ctrl.png", P["david"]["prompt"], P["david"]["negative"],
     params.PERSON_CN, params.PERSON_SIZE, params.PERSON_SEEDS),
    ("goliath", "cond-goliath-ctrl.png", P["goliath"]["prompt"], P["goliath"]["negative"],
     params.PERSON_CN, params.PERSON_SIZE, params.PERSON_SEEDS),
    ("bg-on", "cond-scene-ctrl.png", P["bg_on"]["prompt"], NEG,
     params.SCENE_CN, params.SCENE_SIZE, [params.BG_SEED]),
    ("bg-off", "cond-scene-ctrl.png", P["bg_off"]["prompt"], NEG,
     params.SCENE_CN, params.SCENE_SIZE, [params.BG_SEED]),
]


def main():
    os.makedirs(OUT, exist_ok=True)
    for _, f, *_ in TARGETS:
        if not os.path.exists(os.path.join(params.OUT_ROOT, f)):
            sys.exit(f"조건 입력이 없다: {f} — prep_cond.py를 먼저 돌려라")

    t = time.time()
    cn = ControlNetModel.from_pretrained(params.CN_MODEL, torch_dtype=torch.float16)
    pipe = StableDiffusionXLControlNetPipeline.from_pretrained(
        params.SDXL_BASE, controlnet=cn, torch_dtype=torch.float16, variant="fp16",
        use_safetensors=True).to("mps")
    pipe.set_progress_bar_config(disable=True)
    print(f"로드 {time.time() - t:.0f}s", flush=True)

    # CLIP 77토큰 하드 게이트(run_grid.py 선례) — 실제로 쓰는 파이프라인 tokenizer로 잰다.
    seen = {NEG}
    for _, _, prompt, neg, *_ in TARGETS:
        seen.add(prompt)
        seen.add(neg)
    for pr in seen:
        n = len(pipe.tokenizer(pr).input_ids)
        print(f"  토큰 {n}/{pipe.tokenizer.model_max_length}  {pr[:50]}...")
        if n > pipe.tokenizer.model_max_length:
            sys.exit(f"프롬프트가 CLIP 한도를 넘었다({n}) — 조용히 잘리므로 중단한다: {pr}")

    ctrl_cache = {}
    t0, n, total = time.time(), 0, sum(len(seeds) for *_, seeds in TARGETS)
    for name, cond_file, prompt, neg, cn_scale, size, seeds in TARGETS:
        if cond_file not in ctrl_cache:
            ctrl_cache[cond_file] = Image.open(os.path.join(params.OUT_ROOT, cond_file)).convert("RGB")
        cond = ctrl_cache[cond_file]
        for seed in seeds:
            out = os.path.join(OUT, f"{name}-s{seed}.png")
            if os.path.exists(out):
                n += 1
                continue
            ts = time.time()
            img = pipe(prompt=prompt, negative_prompt=neg, image=cond.resize(size),
                       width=size[0], height=size[1],
                       controlnet_conditioning_scale=cn_scale, num_inference_steps=params.STEPS,
                       guidance_scale=params.GUIDANCE,
                       generator=torch.Generator("mps").manual_seed(seed)).images[0]
            img.save(out)
            n += 1
            print(f"  [{n}/{total}] {os.path.basename(out)}  {time.time() - ts:.0f}s", flush=True)
    print(f"\n{n}장 완료  총 {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
