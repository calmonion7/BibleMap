"""task#317 S2 — 장면 프롬프트의 정체성 어휘를 연다(GPU 4장).

**무엇을 가르려는가.** 장면의 다윗은 5~7세 유아 얼굴로 나온다. 후보 원인이 둘인데 지금까지
**둘 다 시험된 적이 없다**:

  (p) 긍정 어휘 — 장면은 "a small shepherd boy" 한 마디다. 초상은 5축·BRIEF·나이에서 파생한
      "boy of fifteen, lean-faced shepherd with calm steady eyes, curly hair, bare head"인데,
      그 어휘가 장면 경로에는 한 번도 안 실렸다. 그리고 "small"이 치비를 부른다.
  (n) 부정 어휘 — `AXIS_EN["age"]["소년/청년"]`이 이미 `"baby, toddler, infant, chibi, doll"`을
      **파생하고 있는데 장면 프롬프트는 그것을 못 받는다**(초상 전용 경로에만 붙는다).
      긍정 토큰을 0개 쓰면서 정확히 그 실패 양태를 막는 어휘가 놀고 있었다.

**두 축을 섞지 않는다**(회고 `260825-013953` 교훈 2). 네 장을 찍는다:

    (n)  옛 긍정 + 새 부정        — 부정 어휘만의 몫
    (p)  새 긍정 + 옛 부정        — 긍정 어휘만의 몫
    (pn) 새 긍정 + 새 부정        — 합
    (a)  새 긍정 + 새 부정 + **레퍼런스 없음** — 계획이 지목한 핵심 대조군.
         프롬프트만으로 되는 것인지, 레퍼런스가 실제로 기여하는지를 가른다(있음 − 없음).

기준선 (b)「옛 긍정 + 옛 부정 + 레퍼런스 있음」은 이미 있다 — `knee/cn0.3-ip0.5-s11.png`.
나머지는 전부 거기에 맞춘다: CN 0.3(S3'의 무릎) · IP 0.5 · 시드 11 · 마스크 · STEPS · GUIDANCE.

**토큰 예산.** 2인 장면에 초상 수준 어휘를 다 실으면 86토큰으로 CLIP 77을 넘는다(조용히 잘려
뒤쪽 화풍 블록이 소실되는 것이 raster-pilot 결함 1이다). 그래서 조각을 **선언된 우선순위**
(나이 → 개요 → 머리카락 → 머리쓰개, `portrait_prompt`가 이미 정한 순서)의 **뒤에서부터** 떨어뜨려
예산에 맞춘다 — 무엇을 버릴지 손으로 고르지 않는다. 무엇이 떨어졌는지는 찍어 둔다.

Usage: /Users/calmonion/.local/biblemap-imggen/.venv314/bin/python gen_prompt_axis.py
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

OUT = os.path.join(params.OUT_ROOT, "prompt")
MASKS = os.path.join(params.OUT_ROOT, "masks")
COND_SCENE = os.path.join(params.OUT_ROOT, "cond-scene-ctrl.png")
KNEE_CN, KNEE_IP = 0.3, 0.5   # S3'가 곡선에서 파생한 조합 — 여기서 고르는 값이 아니다.


def fit_identity_prompt(spec, tokenizer):
    """조각을 선언된 우선순위대로 채우고, 예산을 넘으면 **뒤에서부터** 떨어뜨린다."""
    slots = {n: list(spec["slots"][n]) for n in ("david", "goliath")}
    dropped = []
    while True:
        body = spec["frame"].format(
            **{n: ", ".join(t for _, t in slots[n]) for n in slots})
        prompt = f"{spec['style']} {body}"
        n = len(tokenizer(prompt).input_ids)
        if n <= tokenizer.model_max_length:
            return prompt, n, dropped
        # 가장 낮은 우선순위(각 인물의 마지막 조각) 중 뒤쪽을 하나 버린다.
        cand = [(len(slots[p]), p) for p in slots if len(slots[p]) > 1]
        if not cand:
            sys.exit(f"조각을 다 버려도 {n}토큰이라 예산에 못 맞춘다")
        _, person = max(cand)
        dropped.append(f"{person}.{slots[person].pop()[0]}")


def main():
    os.makedirs(OUT, exist_ok=True)
    derive_prompts.main()
    P = json.load(open(params.PROMPTS_JSON, encoding="utf-8"))
    spec = P["scene_identity"]
    old_prompt, old_neg = P["bg_on"]["prompt"], P["negative"]
    new_neg = f"{old_neg}, {spec['negative_extra']}"

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
    pipe.set_ip_adapter_scale([KNEE_IP] * 2)
    masks = IPAdapterMaskProcessor().preprocess(
        masks_im, height=params.SCENE_SIZE[1], width=params.SCENE_SIZE[0])

    new_prompt, ntok, dropped = fit_identity_prompt(spec, pipe.tokenizer)
    print(f"로드 {time.time() - t:.0f}s")
    print(f"새 긍정({ntok}/{pipe.tokenizer.model_max_length}토큰, 버린 조각 {dropped or '없음'}):\n  {new_prompt}")
    print(f"새 부정({len(pipe.tokenizer(new_neg).input_ids)}토큰): +{spec['negative_extra']}", flush=True)
    for pr, label in ((old_prompt, "옛"), (new_prompt, "새")):
        n = len(pipe.tokenizer(pr).input_ids)
        if n > pipe.tokenizer.model_max_length:
            sys.exit(f"{label} 긍정이 한도를 넘었다({n}) — 조용히 잘리므로 중단한다")

    jobs = [("n", old_prompt, new_neg, True),
            ("p", new_prompt, old_neg, True),
            ("pn", new_prompt, new_neg, True),
            ("a-noref", new_prompt, new_neg, False)]
    for label, pr, ng, with_ref in jobs:
        out = os.path.join(OUT, f"{label}-s{params.SEED_FIXED}.png")
        if os.path.exists(out):
            print(f"  [스킵] {os.path.basename(out)}")
            continue
        ts = time.time()
        kw = dict(prompt=pr, negative_prompt=ng, image=cond,
                  width=params.SCENE_SIZE[0], height=params.SCENE_SIZE[1],
                  controlnet_conditioning_scale=KNEE_CN,
                  num_inference_steps=params.STEPS, guidance_scale=params.GUIDANCE,
                  generator=torch.Generator("mps").manual_seed(params.SEED_FIXED))
        if with_ref:
            kw["ip_adapter_image"] = refs
            kw["cross_attention_kwargs"] = {"ip_adapter_masks": masks}
        else:
            pipe.unload_ip_adapter()   # scale 0으로는 안 된다 — 아예 내려야 한다
        pipe(**kw).images[0].save(out)
        print(f"  [{label}] {time.time() - ts:.0f}s -> {os.path.basename(out)}", flush=True)
    print(f"완료: {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
