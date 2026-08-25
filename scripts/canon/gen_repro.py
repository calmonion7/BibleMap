"""task#317 S4 — 최선 후보를 다른 시드 2개로 재현한다(GPU 2장).

**후보 선정 근거.** CN 0.3 x IP 0.5가 세 축에 가장 가깝다(시드 11 실측):
  축 A ink 0.0363 (임계 0.0250 통과) · p05 0.596 (임계 0.560 **근소 미달**)
  축 B 다윗 +0.1332 (임계 +0.1367 근소 미달) · 골리앗 +0.0505 (미달)
  축 C 농축 1.825 (임계 1.691 통과)
세 축 동시 성립은 **아직 없다**. 그래도 재현을 찍는 이유는, 이 개선이 시드에 얹힌 우연인지
조합의 성질인지가 다음 관문의 원가를 가르기 때문이다 — 시드 하나로는 못 가른다.

시드는 `params.SCENE_SEEDS`의 나머지 둘(42, 7)을 쓴다. 시드를 새로 고르지 않는다 — 앞선 실측이
같은 시드 집합 위에 있어야 축 B의 짝짓기(같은 시드 a-none 기준선)가 성립한다.

Usage: /Users/calmonion/.local/biblemap-imggen/.venv314/bin/python gen_repro.py
"""
import json
import os
import sys
import time

import torch
from diffusers import ControlNetModel, StableDiffusionXLControlNetPipeline
from diffusers.image_processor import IPAdapterMaskProcessor
from PIL import Image

import params

sys.path.insert(0, params.CANON_DIR)
import derive_prompts  # noqa: E402

OUT = os.path.join(params.OUT_ROOT, "repro")
MASKS = os.path.join(params.OUT_ROOT, "masks")
COND_SCENE = os.path.join(params.OUT_ROOT, "cond-scene-ctrl.png")
KNEE_CN = 0.3   # S3'의 곡선에서 파생한 무릎.
KNEE_IP = 0.5   # 같은 실측에서 세 축에 가장 가까웠던 값.
SEEDS = [s for s in params.SCENE_SEEDS if s != params.SEED_FIXED]   # 42, 7


def main():
    os.makedirs(OUT, exist_ok=True)
    derive_prompts.main()
    P = json.load(open(params.PROMPTS_JSON, encoding="utf-8"))
    PROMPT, NEG = P["bg_on"]["prompt"], P["negative"]

    cond = Image.open(COND_SCENE).convert("RGB").resize(params.SCENE_SIZE)
    refs = [[Image.open(os.path.join(params.FROZEN, f"{n}.png")).convert("RGB")]
            for n in ("david", "goliath")]
    masks_im = [Image.open(os.path.join(MASKS, f"{n}.png")).convert("L").resize(params.SCENE_SIZE)
                for n in ("david", "goliath")]

    t = time.time()
    cn = ControlNetModel.from_pretrained(params.CN_MODEL, torch_dtype=torch.float16)
    pipe = StableDiffusionXLControlNetPipeline.from_pretrained(
        params.SDXL_BASE, controlnet=cn, torch_dtype=torch.float16, variant="fp16",
        use_safetensors=True).to("mps")
    pipe.set_progress_bar_config(disable=True)
    pipe.load_ip_adapter(params.IP_ADAPTER_REPO, subfolder=params.IP_ADAPTER_SUBFOLDER,
                         weight_name=[params.IP_ADAPTER_WEIGHT] * 2)
    masks = IPAdapterMaskProcessor().preprocess(
        masks_im, height=params.SCENE_SIZE[1], width=params.SCENE_SIZE[0])
    print(f"로드 {time.time() - t:.0f}s", flush=True)

    pipe.set_ip_adapter_scale([KNEE_IP] * 2)
    for seed in SEEDS:
        out = os.path.join(OUT, f"cn{KNEE_CN}-ip{KNEE_IP}-s{seed}.png")
        if os.path.exists(out):
            print(f"  [스킵] {os.path.basename(out)}")
            continue
        ts = time.time()
        pipe(prompt=PROMPT, negative_prompt=NEG, image=cond,
             width=params.SCENE_SIZE[0], height=params.SCENE_SIZE[1],
             controlnet_conditioning_scale=KNEE_CN,
             num_inference_steps=params.STEPS, guidance_scale=params.GUIDANCE,
             ip_adapter_image=refs, cross_attention_kwargs={"ip_adapter_masks": masks},
             generator=torch.Generator("mps").manual_seed(seed)
             ).images[0].save(out)
        print(f"  [s{seed}] {time.time() - ts:.0f}s -> {os.path.basename(out)}", flush=True)
    print(f"완료: {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
