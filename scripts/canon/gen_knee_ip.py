"""task#317 S3'' — 무릎(CN 0.3)에서 IP-Adapter 강도를 연다: 축 B의 유일한 남은 손잡이(GPU 3장).

**어디까지 왔나.** CN 강도 곡선이 트레이드오프를 수로 확정했다(같은 시드·나머지 전부 고정):

    CN   0.0     0.2     0.4     0.6     0.8(현행)
    ink  0.0725  0.0512  0.0181  0.0095  0.0051    ← 축 A 임계 0.0250
    농축  1.453   1.563   1.823   2.097   2.151     ← 축 C 임계 1.691

축 A는 CN <= 0.2에서, 축 C는 CN >= 0.4에서 통과한다 — **한 값으로 둘 다 만족하는 지점이 없다.**
그 사이 0.3이 무릎이고, 두 임계가 교차하는 자리라 실측하지 않으면 「없다」를 단정할 수 없다.

**그리고 축 B는 어디서도 통과하지 않았다**(최대 +0.095, 임계 +0.1367). 전이량은 동결본 11~23%
혼합 수준에 머문다. 남은 손잡이는 `IP_SCALE`뿐이다 — 현행 0.3은 초상 층에서 정한 값이고
(gen_sweep_scale_age.py), 정답지를 만든 raster-pilot은 0.7을 썼다. 장면 층에서는 한 번도
쓸어보지 않았다.

그래서 CN을 무릎에 고정하고 IP만 움직인다 — **이 묶음 안에서 움직이는 축은 하나다.**
IP를 올리면 축 A가 함께 내려갈 수 있다(동결본 자체가 창백하다, ink 0.006) — 그 대가도 함께 나온다.

Usage: /Users/calmonion/.local/biblemap-imggen/.venv314/bin/python gen_knee_ip.py
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

OUT = os.path.join(params.OUT_ROOT, "knee")
MASKS = os.path.join(params.OUT_ROOT, "masks")
COND_SCENE = os.path.join(params.OUT_ROOT, "cond-scene-ctrl.png")
KNEE_CN = 0.3   # 두 임계가 교차하는 자리 — 곡선에서 파생한 값이지 고른 값이 아니다.
# IP 후보 범위는 `params.IP_SCALES`를 **그대로 읽는다** — 지역 별칭을 두면 정본 키를 재선언한
# 것이 되어 게이트가 막는다(실제로 막혔다: 정본 키는 이 디렉터리의 전역 예약어다, ADR 260825-074924).


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

    for ip in params.IP_SCALES:
        out = os.path.join(OUT, f"cn{KNEE_CN}-ip{ip}-s{params.SEED_FIXED}.png")
        if os.path.exists(out):
            print(f"  [스킵] {os.path.basename(out)}")
            continue
        pipe.set_ip_adapter_scale([ip] * 2)
        ts = time.time()
        pipe(prompt=PROMPT, negative_prompt=NEG, image=cond,
             width=params.SCENE_SIZE[0], height=params.SCENE_SIZE[1],
             controlnet_conditioning_scale=KNEE_CN,
             num_inference_steps=params.STEPS, guidance_scale=params.GUIDANCE,
             ip_adapter_image=refs, cross_attention_kwargs={"ip_adapter_masks": masks},
             generator=torch.Generator("mps").manual_seed(params.SEED_FIXED)
             ).images[0].save(out)
        print(f"  [cn={KNEE_CN} ip={ip}] {time.time() - ts:.0f}s -> {os.path.basename(out)}", flush=True)
    print(f"완료: {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
