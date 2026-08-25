"""task#317 S3 — 2패스: CN으로 구도를 잡고, CN 없이 화풍을 되살린다(GPU).

**S1이 근거를 확정했다.** ControlNet을 끄면 잉크가 0.0051 → 0.0725로 **14배** 뛴다(cause/cn0-ref).
그런데 `control_guidance_end`로 뒤쪽 스텝의 CN을 놓아도 화풍은 안 돌아온다(0.0046~0.0066) —
**창백함은 앞쪽 스텝에서 결정되고, CN을 놓은 뒤에 남은 스텝으로는 복구되지 않는다.**
그리고 CN을 처음부터 끄면 구도가 통째로 무너진다(다윗이 화면에서 사라졌다).

⇒ 두 축은 한 패스 안에서 동시에 만족되지 않는다. 갈라서 준다: **패스 1이 구도**(CN 켜짐, 현행
그대로), **패스 2가 화풍**(CN 없는 img2img, denoise만큼만 다시 그린다). denoise가 트레이드오프
손잡이다 — 낮으면 구도를 지키고 화풍이 덜 오고, 높으면 그 반대다. 계획의 후보 {0.4, 0.5}에
가장 낮은 값 하나를 더해 손잡이의 기울기를 본다.

레퍼런스는 패스 2에서도 태운다 — 얼굴을 다시 그리는 단계이므로 여기서 빠지면 [[정본 전이]]가
패스 1의 잔상만 남는다. 마스크도 같이 간다(패스 1과 같은 배선).

Usage: /Users/calmonion/.local/biblemap-imggen/.venv314/bin/python gen_2pass.py
"""
import json
import os
import sys
import time

import torch
from diffusers import StableDiffusionXLImg2ImgPipeline
from diffusers.image_processor import IPAdapterMaskProcessor
from PIL import Image

import params

sys.path.insert(0, params.CANON_DIR)
import derive_prompts  # noqa: E402

OUT = os.path.join(params.OUT_ROOT, "twopass")
MASKS = os.path.join(params.OUT_ROOT, "masks")
# 패스 1 = 현행 조건 그대로. cge 스윕의 1.0이 `scene/c-mask-s11.png`와 sha256 동일함을 S1이
# 확인했으므로 어느 쪽을 써도 같다 — 추적 관계가 분명한 쪽(현행 산출)을 base로 둔다.
BASE = os.path.join(params.OUT_ROOT, "scene", "c-mask-s11.png")
DENOISE = [0.3, 0.4, 0.5]


def main():
    os.makedirs(OUT, exist_ok=True)
    if not os.path.exists(BASE):
        sys.exit(f"패스 1 산출이 없다: {BASE}")
    derive_prompts.main()
    P = json.load(open(params.PROMPTS_JSON, encoding="utf-8"))
    PROMPT, NEG = P["bg_on"]["prompt"], P["negative"]

    base_im = Image.open(BASE).convert("RGB").resize(params.SCENE_SIZE)
    refs = [[Image.open(os.path.join(params.FROZEN, f"{n}.png")).convert("RGB")]
            for n in ("david", "goliath")]
    masks_im = [Image.open(os.path.join(MASKS, f"{n}.png")).convert("L").resize(params.SCENE_SIZE)
                for n in ("david", "goliath")]

    t = time.time()
    pipe = StableDiffusionXLImg2ImgPipeline.from_pretrained(
        params.SDXL_BASE, torch_dtype=torch.float16, variant="fp16",
        use_safetensors=True).to("mps")
    pipe.set_progress_bar_config(disable=True)
    pipe.load_ip_adapter(params.IP_ADAPTER_REPO, subfolder=params.IP_ADAPTER_SUBFOLDER,
                         weight_name=[params.IP_ADAPTER_WEIGHT] * 2)
    pipe.set_ip_adapter_scale([params.IP_SCALE] * 2)
    masks = IPAdapterMaskProcessor().preprocess(
        masks_im, height=params.SCENE_SIZE[1], width=params.SCENE_SIZE[0])
    print(f"로드 {time.time() - t:.0f}s  패스1 = {os.path.basename(BASE)}", flush=True)

    for dn in DENOISE:
        out = os.path.join(OUT, f"p2-dn{dn}-s{params.SEED_FIXED}.png")
        if os.path.exists(out):
            print(f"  [스킵] {os.path.basename(out)}")
            continue
        ts = time.time()
        pipe(prompt=PROMPT, negative_prompt=NEG, image=base_im, strength=dn,
             num_inference_steps=params.STEPS, guidance_scale=params.GUIDANCE,
             ip_adapter_image=refs, cross_attention_kwargs={"ip_adapter_masks": masks},
             generator=torch.Generator("mps").manual_seed(params.SEED_FIXED)
             ).images[0].save(out)
        print(f"  [dn={dn}] {time.time() - ts:.0f}s -> {os.path.basename(out)}", flush=True)
    print(f"완료: {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
