"""task#315 S4 — 장면 생성, 대조군을 함께 낸다(GPU). 네 조건 x 3시드 = 12장.

같은 콘티 조건 입력(cond-scene-ctrl.png, --at 9000) · params.SCENE_CN=0.8 · params.STEPS=30 · params.GUIDANCE=6.5 ·
1216x640 · ip_adapter_scale=0.3(S2가 정함) · 시드 {11,42,7}(PERSON_SEEDS 관례) 전부 고정 —
축을 섞지 않는다.

네 조건:
  (a) a-none   — IP-Adapter 미로드(scale 0이 아니라 아예 안 태운다). task#308 기준선·화풍 기준선.
  (b) b-nomask — 다윗+골리앗 레퍼런스 2장, 마스크 없이 전체에 건다. 오염 대조군(일부러 틀리게).
  (c) c-mask   — 다윗+골리앗 레퍼런스 2장, 인물별 영역 마스크로 배선.
  (d) d-mask-bg— (c) + 배경 레퍼런스(masks/background.png 여집합으로 gen/bg-on-s11.png에서 파생) +
                 배경 마스크. 3레퍼런스+3마스크.

스모크: (c) 조건 시드 11을 다른 (c)·(d) 생성보다 먼저 찍어 리스트 중첩·마스크 텐서 배선을 실측
확인한다(계획 지시) — 실패하면 여기서 멈춘다.

프롬프트: derive_prompts.py를 다시 돌려 prompts.json을 신선하게 재생성한 뒤 bg_on을 쓴다(근거는
SCENE.md). 네 조건 전부 같은 프롬프트 — 변수를 IP-Adapter 축 하나로 가둔다.
"""
import hashlib
import os
import sys
import time

import numpy as np
import torch
from diffusers import ControlNetModel, StableDiffusionXLControlNetPipeline
from diffusers.image_processor import IPAdapterMaskProcessor
from PIL import Image

import params

sys.path.insert(0, params.CANON_DIR)
import derive_prompts  # noqa: E402

# 동결본·마스크는 추적 입력(scripts/canon/), 나머지 생성물은 미추적 산출물(OUT_ROOT).
OUT = os.path.join(params.OUT_ROOT, "scene")
FROZEN_DAVID = os.path.join(params.FROZEN, "david.png")
FROZEN_GOLIATH = os.path.join(params.FROZEN, "goliath.png")
MASK_DAVID = os.path.join(params.OUT_ROOT, "masks", "david.png")
MASK_GOLIATH = os.path.join(params.OUT_ROOT, "masks", "goliath.png")
MASK_BG = os.path.join(params.OUT_ROOT, "masks", "background.png")
COND_SCENE = os.path.join(params.OUT_ROOT, "cond-scene-ctrl.png")
BG_SOURCE = os.path.join(params.OUT_ROOT, "gen", "bg-on-s11.png")
BG_REF_OUT = os.path.join(params.OUT_ROOT, "bg-ref.png")


def make_bg_reference():
    """배경 레퍼런스 = 인물 마스크 여집합 크롭(BACKGROUND.md §5 재정의). 배경 마스크는 두 인물
    구멍이 뚫린 형태라 bbox 크롭이 무의미하다(구멍이 화면 가장자리까지 닿지 않아 bbox=캔버스
    전체가 된다) — 그래서 "크롭"을 bbox가 아니라 마스크 합성(인물 구멍을 배경 자신의 평균색으로
    메움)으로 구현한다. 파라미터 없음(eco) — 채울 색을 손으로 고르지 않고 배경 영역 자체의 평균
    RGB에서 파생한다."""
    bg_on = Image.open(BG_SOURCE).convert("RGB").resize(params.SCENE_SIZE)
    mask = Image.open(MASK_BG).convert("L").resize(params.SCENE_SIZE)
    arr = np.array(bg_on)
    m = np.array(mask) > 0
    fill_color = tuple(int(round(v)) for v in arr[m].mean(axis=0))
    blank = Image.new("RGB", params.SCENE_SIZE, fill_color)
    bg_ref = Image.composite(bg_on, blank, mask)
    bg_ref.save(BG_REF_OUT)
    print(f"배경 레퍼런스 생성: {BG_REF_OUT}  fill_color={fill_color}  출처={BG_SOURCE}")
    return bg_ref


def check_tokens(pipe, prompt, neg):
    for label, pr in (("prompt", prompt), ("negative", neg)):
        n = len(pipe.tokenizer(pr).input_ids)
        print(f"  토큰[{label}] {n}/{pipe.tokenizer.model_max_length}  {pr[:60]}...")
        if n > pipe.tokenizer.model_max_length:
            sys.exit(f"프롬프트가 CLIP 한도를 넘었다({n}) — 조용히 잘리므로 중단한다: {pr}")


def main():
    os.makedirs(OUT, exist_ok=True)
    for p in (FROZEN_DAVID, FROZEN_GOLIATH, MASK_DAVID, MASK_GOLIATH, MASK_BG, COND_SCENE, BG_SOURCE):
        if not os.path.exists(p):
            sys.exit(f"필요한 입력이 없다: {p}")

    # 프롬프트는 손으로 쓰지 않는다 — derive_prompts.py를 다시 돌려 prompts.json을 신선하게 만든다.
    derive_prompts.main()
    import json
    with open(params.PROMPTS_JSON, encoding="utf-8") as f:
        P = json.load(f)
    # bg_on 채택 — 근거는 SCENE.md: (d)가 배경 레퍼런스 이미지를 태우므로 텍스트도 배경 어휘를
    # 실어 이미지·텍스트 조건이 같은 것을 말하게 한다(NEEDS.md §2 선례) + 네 조건 전부 같은
    # 프롬프트를 써서 변수를 IP-Adapter 축 하나로 가둔다(섞으면 못 가른다, SWEEP.md 교훈).
    PROMPT = P["bg_on"]["prompt"]
    NEG = P["negative"]

    bg_ref = make_bg_reference()
    cond = Image.open(COND_SCENE).convert("RGB").resize(params.SCENE_SIZE)
    ref_david = Image.open(FROZEN_DAVID).convert("RGB")
    ref_goliath = Image.open(FROZEN_GOLIATH).convert("RGB")
    mask_david_im = Image.open(MASK_DAVID).convert("L").resize(params.SCENE_SIZE)
    mask_goliath_im = Image.open(MASK_GOLIATH).convert("L").resize(params.SCENE_SIZE)
    mask_bg_im = Image.open(MASK_BG).convert("L").resize(params.SCENE_SIZE)

    t = time.time()
    cn = ControlNetModel.from_pretrained(params.CN_MODEL, torch_dtype=torch.float16)
    pipe = StableDiffusionXLControlNetPipeline.from_pretrained(
        params.SDXL_BASE, controlnet=cn, torch_dtype=torch.float16, variant="fp16",
        use_safetensors=True).to("mps")
    pipe.set_progress_bar_config(disable=True)
    print(f"로드 {time.time() - t:.0f}s", flush=True)
    check_tokens(pipe, PROMPT, NEG)

    proc = IPAdapterMaskProcessor()
    outputs = []  # (label, path)
    t0 = time.time()

    def gen_one(label, seed, ip_image=None, cross_kwargs=None):
        out = os.path.join(OUT, f"{label}-s{seed}.png")
        outputs.append((label, out))
        if os.path.exists(out):
            print(f"  [스킵, 존재함] {os.path.basename(out)}")
            return
        ts = time.time()
        kwargs = dict(prompt=PROMPT, negative_prompt=NEG, image=cond,
                      width=params.SCENE_SIZE[0], height=params.SCENE_SIZE[1],
                      controlnet_conditioning_scale=params.SCENE_CN, num_inference_steps=params.STEPS,
                      guidance_scale=params.GUIDANCE,
                      generator=torch.Generator("mps").manual_seed(seed))
        if ip_image is not None:
            kwargs["ip_adapter_image"] = ip_image
        if cross_kwargs is not None:
            kwargs["cross_attention_kwargs"] = cross_kwargs
        img = pipe(**kwargs).images[0]
        img.save(out)
        dt = time.time() - ts
        print(f"  [{label} s{seed}] {dt:.0f}s -> {os.path.basename(out)}", flush=True)

    # --- (a) IP-Adapter 미로드 — task#308/화풍 기준선 ---
    print("\n== (a) a-none — IP-Adapter 미로드 ==", flush=True)
    for seed in params.SCENE_SEEDS:
        gen_one("a-none", seed)

    # --- 어댑터 2개(다윗·골리앗) 로드: (b)·(c)가 공유 ---
    print("\n== IP-Adapter 로드(N=2: david, goliath) ==", flush=True)
    pipe.load_ip_adapter(params.IP_ADAPTER_REPO, subfolder=params.IP_ADAPTER_SUBFOLDER,
                         weight_name=[params.IP_ADAPTER_WEIGHT] * 2)
    pipe.set_ip_adapter_scale([params.IP_SCALE, params.IP_SCALE])
    ip_image_2 = [[ref_david], [ref_goliath]]

    # --- 스모크: (c) 시드 11을 (b)·(c) 나머지보다 먼저 찍어 배선을 확인한다 ---
    print("\n== 스모크: c-mask s11 (마스크 배선 실측 확인) ==", flush=True)
    masks_2 = proc.preprocess([mask_david_im, mask_goliath_im], height=params.SCENE_SIZE[1], width=params.SCENE_SIZE[0])
    print(f"  IPAdapterMaskProcessor.preprocess 출력 shape={tuple(masks_2.shape)} dtype={masks_2.dtype}")
    # 실측 정정(스모크 1차 시도, ValueError로 확인): cross_attention_kwargs={"ip_adapter_masks":[masks]}
    # 처럼 리스트로 한 번 더 감싸면 len==1로 읽혀 "Length of ip_adapter_masks array (1) must match
    # length of self.scale array (2)"로 실패한다. diffusers attention_processor.py:4310-4312가
    # 텐서를 직접 받으면 list(tensor.unsqueeze(1))로 알아서 N개로 쪼갠다 — 감싸지 않고 텐서 그대로 넘긴다.
    gen_one("c-mask", 11, ip_image=ip_image_2, cross_kwargs={"ip_adapter_masks": masks_2})
    smoke_path = os.path.join(OUT, "c-mask-s11.png")
    smoke_im = Image.open(smoke_path)
    assert smoke_im.size == params.SCENE_SIZE, f"스모크 출력 크기가 다르다: {smoke_im.size}"
    print(f"  스모크 통과 — {smoke_path} 크기={smoke_im.size}")

    # --- (b) 마스크 없이 2레퍼런스 전체 적용 — 오염 대조군 ---
    print("\n== (b) b-nomask — 마스크 없음 ==", flush=True)
    for seed in params.SCENE_SEEDS:
        gen_one("b-nomask", seed, ip_image=ip_image_2)

    # --- (c) 나머지 시드 ---
    print("\n== (c) c-mask — 나머지 시드 ==", flush=True)
    for seed in params.SCENE_SEEDS:
        if seed == 11:
            continue
        gen_one("c-mask", seed, ip_image=ip_image_2, cross_kwargs={"ip_adapter_masks": masks_2})

    # --- 어댑터 3개(다윗·골리앗·배경)로 재로드: (d) ---
    print("\n== IP-Adapter 재로드(N=3: david, goliath, background) ==", flush=True)
    pipe.unload_ip_adapter()
    pipe.load_ip_adapter(params.IP_ADAPTER_REPO, subfolder=params.IP_ADAPTER_SUBFOLDER,
                         weight_name=[params.IP_ADAPTER_WEIGHT] * 3)
    pipe.set_ip_adapter_scale([params.IP_SCALE, params.IP_SCALE, params.IP_SCALE])
    ip_image_3 = [[ref_david], [ref_goliath], [bg_ref]]
    masks_3 = proc.preprocess([mask_david_im, mask_goliath_im, mask_bg_im],
                               height=params.SCENE_SIZE[1], width=params.SCENE_SIZE[0])
    print(f"  masks_3 shape={tuple(masks_3.shape)}")
    print("\n== (d) d-mask-bg ==", flush=True)
    for seed in params.SCENE_SEEDS:
        gen_one("d-mask-bg", seed, ip_image=ip_image_3, cross_kwargs={"ip_adapter_masks": masks_3})

    print(f"\n{len(outputs)}장 완료  총 {time.time() - t0:.0f}s")

    # 완료기준 — sha256 전수 상이를 스크립트가 단정한다.
    digests = [hashlib.sha256(open(p, "rb").read()).hexdigest() for _, p in outputs]
    assert len(set(digests)) == len(digests), "sha256 중복이 있다"
    assert len(outputs) == 12, f"12장이 아니다: {len(outputs)}"
    for (label, p), d in zip(outputs, digests):
        print(f"sha256 {d[:16]}...  {os.path.basename(p)}")
    print("SANITY 통과 — 12장, sha256 전수 상이")
    return 0


if __name__ == "__main__":
    sys.exit(main())
