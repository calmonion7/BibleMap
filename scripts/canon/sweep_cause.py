"""task#314 수정 — 사용자 UAT 실패("둘다 이상함")의 지배적 원인을 가르는 싼 실험.

두 후보 원인이 있고 섞으면 못 가른다(task#308이 밀도·강도를 섞어 실패한 선례):
  축 A 프롬프트 — 현행은 부정형("no hair visible, no beard, clean-shaven")뿐이고 얼굴을 묘사하는
                  말이 하나도 없다. CLIP은 부정을 못 다루므로 모델에 그릴 근거가 0이다.
  축 B ControlNet 강도 — 0.8은 "이 그림은 이 선이 전부"에 가깝다. 골리앗 조건은 stroke 4개뿐이라
                  내부를 채울 여지가 없다(빈 타원의 유력 원인).

골리앗 1대상 × 2프롬프트 × 3강도 × 1시드 = 6장(약 10분)으로 먼저 가른 뒤 본 생성에 규모를 준다.
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

OUT = os.path.join(params.OUT_ROOT, "sweep")
# CN_SCALES는 이 실험이 **가르려는 축**이라 정본이 아니다(축 B 그 자체).
CN_SCALES = [0.8, 0.5, 0.3]

with open(params.PROMPTS_JSON, encoding="utf-8") as f:
    P = json.load(f)

STYLE = P["style"]
# v1 = 현행(대조군). v2 = 있는 것을 묘사하고 없는 것은 negative로 옮긴 판.
PROMPTS = {
    "v1": P["goliath"]["prompt"],
    # 화풍 블록이 35토큰을 먹어 인물 묘사에 42토큰뿐 — 축을 섞지 않으려 화풍은 v1과 동일하게 두고
    # 인물 묘사만 77 안에 들어가게 줄였다(prompt_2 분리는 별개 축이라 여기서 열지 않는다).
    "v2": (f"{STYLE} close-up head portrait of a fierce giant warrior, "
           "heavy scowling brow, deep-set glaring eyes, hard jaw, "
           "bronze helmet with cheek guards, facing forward."),
}
NEGS = {
    "v1": P["negative"],
    "v2": P["negative"] + ", beard, moustache, long hair, blank face, featureless, empty oval, child, cute, doll",
}


def main():
    os.makedirs(OUT, exist_ok=True)
    ctrl_path = os.path.join(params.OUT_ROOT, "cond-goliath-ctrl.png")
    if not os.path.exists(ctrl_path):
        sys.exit(f"조건 입력이 없다: {ctrl_path}")

    t = time.time()
    cn = ControlNetModel.from_pretrained(params.CN_MODEL, torch_dtype=torch.float16)
    pipe = StableDiffusionXLControlNetPipeline.from_pretrained(
        params.SDXL_BASE, controlnet=cn, torch_dtype=torch.float16, variant="fp16",
        use_safetensors=True).to("mps")
    pipe.set_progress_bar_config(disable=True)
    print(f"로드 {time.time() - t:.0f}s", flush=True)

    lim = pipe.tokenizer.model_max_length
    for k in PROMPTS:
        for name, txt in (("prompt", PROMPTS[k]), ("negative", NEGS[k])):
            n = len(pipe.tokenizer(txt).input_ids)
            print(f"  토큰 {k}.{name}: {n}/{lim}")
            if n > lim:
                sys.exit(f"{k}.{name}이 CLIP 한도를 넘었다({n}) — 조용히 잘리므로 중단한다")

    ctrl = Image.open(ctrl_path).convert("RGB")
    t0, n = time.time(), 0
    total = len(PROMPTS) * len(CN_SCALES)
    for pk, cs in itertools.product(PROMPTS, CN_SCALES):
        out = os.path.join(OUT, f"goliath-{pk}-cn{cs}-s{params.SEED_FIXED}.png")
        if os.path.exists(out):
            n += 1
            continue
        ts = time.time()
        img = pipe(prompt=PROMPTS[pk], negative_prompt=NEGS[pk], image=ctrl,
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
