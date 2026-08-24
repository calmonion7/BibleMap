"""조건 입력을 얇은 선으로 다시 찍은 뒤 적정 강도를 다시 잡는 확인 4장(다윗·골리앗 × cn 0.3/0.5).

sweep_cause.py는 **두꺼운 띠** 조건에서 강도를 갈랐다(0.8 빈 타원 / 0.3 완성 초상). cond_shoot_heads.py의
THIN_SW로 조건 입력이 얇아지면 선이 덜 강압적이라 최적점이 위로 움직일 수 있다 — 본 생성 8장(약 18분)을
찍기 전에 4장으로 확인한다. 프롬프트는 개정판(prompts.json, BRIEF 반영) 하나만 쓴다(축을 다시 섞지 않는다).
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

OUT = os.path.join(params.OUT_ROOT, "probe")
# CN_SCALES는 이 실험이 **가르려는 축**이라 정본이 아니다 — params.py의 고정값과 다른 성질이다.
CN_SCALES = [0.5, 0.3]

with open(params.PROMPTS_JSON, encoding="utf-8") as f:
    P = json.load(f)
SUBJECTS = ["david", "goliath"]


def main():
    os.makedirs(OUT, exist_ok=True)
    t = time.time()
    cn = ControlNetModel.from_pretrained(params.CN_MODEL, torch_dtype=torch.float16)
    pipe = StableDiffusionXLControlNetPipeline.from_pretrained(
        params.SDXL_BASE, controlnet=cn, torch_dtype=torch.float16, variant="fp16",
        use_safetensors=True).to("mps")
    pipe.set_progress_bar_config(disable=True)
    print(f"로드 {time.time() - t:.0f}s", flush=True)

    lim = pipe.tokenizer.model_max_length
    for s in SUBJECTS:
        for f in ("prompt", "negative"):
            n = len(pipe.tokenizer(P[s][f]).input_ids)
            print(f"  토큰 {s}.{f}: {n}/{lim}", flush=True)
            if n > lim:
                sys.exit(f"{s}.{f}가 CLIP 한도를 넘었다({n}) — 조용히 잘리므로 중단한다")

    t0, n, total = time.time(), 0, len(SUBJECTS) * len(CN_SCALES)
    for s, cs in itertools.product(SUBJECTS, CN_SCALES):
        out = os.path.join(OUT, f"{s}-cn{cs}-s{params.SEED_FIXED}.png")
        if os.path.exists(out):
            n += 1
            continue
        ctrl = Image.open(os.path.join(params.OUT_ROOT, f"cond-{s}-ctrl.png")).convert("RGB")
        ts = time.time()
        img = pipe(prompt=P[s]["prompt"], negative_prompt=P[s]["negative"], image=ctrl,
                   controlnet_conditioning_scale=cs, num_inference_steps=params.STEPS,
                   guidance_scale=params.GUIDANCE,
                   width=params.PERSON_SIZE[0], height=params.PERSON_SIZE[1],
                   generator=torch.Generator("mps").manual_seed(params.SEED_FIXED)).images[0]
        img.save(out)
        n += 1
        print(f"  [{n}/{total}] {os.path.basename(out)}  {time.time() - ts:.0f}s", flush=True)
    print(f"\n{n}장 완료  총 {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
