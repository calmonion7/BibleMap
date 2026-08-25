"""task#317 S1 — 축 1: `control_guidance_end` 스윕(GPU).

**가설**: ControlNet 경로가 화풍을 죽인다(정답지 ink 0.10~0.22 ↔ 현행 0.000~0.008, 16.7배).
강도 축은 기존 데이터가 이미 기각했다 — CN 0.5에서 이미 창백하다(계획 실측 ①). 미시험이고
1패스라 가장 싼 축이 **CN을 거는 구간**이다: 뒤쪽 스텝에서 CN을 놓으면 구도는 이미 잡혀 있고
화풍은 모델이 마무리한다.

**축을 섞지 않는다**(회고 `260825-013953` 교훈 2 — 목록에 없는 축이 결과를 지배했다).
`gen_scene.py`의 (c) 조건을 그대로 승계하고 `control_guidance_end` 하나만 움직인다:
시드 11 · 레퍼런스 2장(다윗·골리앗 동결본) · 인물별 마스크 · params.SCENE_CN · STEPS · GUIDANCE ·
IP_SCALE · 같은 프롬프트(`derive_prompts.py` 재생성) 전부 고정.

**스모크 1장**을 가장 공격적인 값(최소 cge)으로 먼저 찍는다 — 파이프가 인자를 실제로 받는지,
구도가 완전히 무너지지는 않는지를 4장 원가 전에 확인한다(회고 `260825-013953`: 이전에 12장 약
40분을 살렸다).

**cge=1.0은 현행 재생성**이다. `scene/c-mask-s11.png`와 sha256이 같으면 재현이 닫힌 것이고,
다르면 그 자체가 미결 3축(모델 리비전·MPS 결정성)의 실측이다 — 어느 쪽이든 기록한다.

Usage: /Users/calmonion/.local/biblemap-imggen/.venv314/bin/python gen_cge_sweep.py
"""
import hashlib
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

OUT = os.path.join(params.OUT_ROOT, "cge")
MASKS = os.path.join(params.OUT_ROOT, "masks")
COND_SCENE = os.path.join(params.OUT_ROOT, "cond-scene-ctrl.png")
CURRENT_REF = os.path.join(params.OUT_ROOT, "scene", "c-mask-s11.png")


def main():
    os.makedirs(OUT, exist_ok=True)
    need = [COND_SCENE, os.path.join(params.FROZEN, "david.png"),
            os.path.join(params.FROZEN, "goliath.png"),
            os.path.join(MASKS, "david.png"), os.path.join(MASKS, "goliath.png")]
    for p in need:
        if not os.path.exists(p):
            sys.exit(f"필요한 입력이 없다: {p}")

    derive_prompts.main()
    with open(params.PROMPTS_JSON, encoding="utf-8") as f:
        P = json.load(f)
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
    print(f"로드 {time.time() - t:.0f}s  프롬프트 토큰 "
          f"{len(pipe.tokenizer(PROMPT).input_ids)}/{pipe.tokenizer.model_max_length}", flush=True)

    def gen(cge, with_ref=True):
        label = f"cge{cge}" if with_ref else f"cge{cge}-noref"
        out = os.path.join(OUT, f"{label}-s{params.SEED_FIXED}.png")
        if os.path.exists(out):
            print(f"  [스킵, 존재함] {os.path.basename(out)}")
            return out
        ts = time.time()
        kwargs = dict(prompt=PROMPT, negative_prompt=NEG, image=cond,
                      width=params.SCENE_SIZE[0], height=params.SCENE_SIZE[1],
                      controlnet_conditioning_scale=params.SCENE_CN,
                      control_guidance_end=cge,
                      num_inference_steps=params.STEPS, guidance_scale=params.GUIDANCE,
                      generator=torch.Generator("mps").manual_seed(params.SEED_FIXED))
        if with_ref:
            kwargs["ip_adapter_image"] = refs
            kwargs["cross_attention_kwargs"] = {"ip_adapter_masks": masks}
        pipe(**kwargs).images[0].save(out)
        print(f"  [{label}] {time.time() - ts:.0f}s -> {os.path.basename(out)}", flush=True)
        return out

    # --- 스모크: 가장 공격적인 값 1장 ---
    smoke_cge = min(params.CONTROL_ENDS)
    print(f"\n== 스모크 cge={smoke_cge} (파이프가 인자를 받는지 · 구도가 남는지) ==", flush=True)
    sp = gen(smoke_cge)
    assert Image.open(sp).size == params.SCENE_SIZE, "스모크 출력 크기가 다르다"
    print(f"  스모크 통과 — {sp}")

    print("\n== 나머지 cge ==", flush=True)
    made = [sp] + [gen(c) for c in params.CONTROL_ENDS if c != smoke_cge]

    # 재현 확인 — cge=1.0은 현행 조건의 재생성이다.
    base = os.path.join(OUT, f"cge1.0-s{params.SEED_FIXED}.png")
    if os.path.exists(base) and os.path.exists(CURRENT_REF):
        d = [hashlib.sha256(open(p, "rb").read()).hexdigest() for p in (base, CURRENT_REF)]
        print(f"\n재현: cge=1.0 재생성 vs 현행 c-mask-s11 — sha256 "
              f"{'일치(재현 닫힘)' if d[0] == d[1] else '불일치(재현 미결 — 미결 3축의 실측)'}")

    print(f"\n{len(made)}장 완료: {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
