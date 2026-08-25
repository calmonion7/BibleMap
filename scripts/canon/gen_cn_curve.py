"""task#317 S3' — ControlNet 강도 곡선: 축 A와 축 C의 트레이드오프를 수로 적는다(GPU 3장).

**왜 이 축을 다시 여는가.** 계획은 강도 축을 「기존 데이터가 기각한다」고 적었다(CN 0.5에서 이미
창백 — `scrib-cn0.5-ip0.5`의 ink 0.0097). 그러나 그 실측은 **다른 스크립트·다른 프롬프트·다른
ControlNet**(raster-pilot의 canny/scribble 시험)에서 나왔다. 현행 파이프라인에서 이 태스크가
실측한 것은 두 점뿐이다:

    CN 0.8 → ink 0.0051 (현행)        CN 0.0 → ink 0.0725 (레퍼런스 켬) / 0.0983 (끔)

**34배가 이 두 점 사이에 있다.** 그 사이가 절벽인지 비탈인지 모르는 채로 「강도로는 안 된다」를
승계하면, 반증 가능한 값을 안 보고 다음 관문의 원가를 지불하게 된다(ADR `260825-074925`).
그리고 `control_guidance_end`(뒤쪽 스텝을 놓는다)와 2패스(낮은 denoise)가 **둘 다 실패했으므로**
남은 손잡이는 강도뿐이다.

축 C(구도)가 함께 떨어질 것이다 — 그것이 이 슬라이스가 재려는 **트레이드오프**다. 축 C의 임계는
S0가 못박아 뒀으므로 어디서 구도가 깨지는지 수로 나온다.

나머지 축은 전부 고정한다: 시드 11 · 레퍼런스 2장 · 마스크 · 프롬프트 · STEPS · GUIDANCE ·
IP_SCALE · cge 1.0(S1이 기각했으므로 현행값으로 되돌린다).

Usage: /Users/calmonion/.local/biblemap-imggen/.venv314/bin/python gen_cn_curve.py
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

OUT = os.path.join(params.OUT_ROOT, "cncurve")
MASKS = os.path.join(params.OUT_ROOT, "masks")
COND_SCENE = os.path.join(params.OUT_ROOT, "cond-scene-ctrl.png")
# 이미 두 끝점(0.0 · 0.8)이 있으므로 사이만 채운다.
SCALES = [0.2, 0.4, 0.6]


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
    pipe.set_ip_adapter_scale([params.IP_SCALE] * 2)
    masks = IPAdapterMaskProcessor().preprocess(
        masks_im, height=params.SCENE_SIZE[1], width=params.SCENE_SIZE[0])
    print(f"로드 {time.time() - t:.0f}s", flush=True)

    for sc in SCALES:
        out = os.path.join(OUT, f"cn{sc}-s{params.SEED_FIXED}.png")
        if os.path.exists(out):
            print(f"  [스킵] {os.path.basename(out)}")
            continue
        ts = time.time()
        pipe(prompt=PROMPT, negative_prompt=NEG, image=cond,
             width=params.SCENE_SIZE[0], height=params.SCENE_SIZE[1],
             controlnet_conditioning_scale=sc,
             num_inference_steps=params.STEPS, guidance_scale=params.GUIDANCE,
             ip_adapter_image=refs, cross_attention_kwargs={"ip_adapter_masks": masks},
             generator=torch.Generator("mps").manual_seed(params.SEED_FIXED)
             ).images[0].save(out)
        print(f"  [cn={sc}] {time.time() - ts:.0f}s -> {os.path.basename(out)}", flush=True)
    print(f"완료: {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
