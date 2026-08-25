"""task#317 후속 — 화풍은 유지하고 **대비 어휘만 뒤집는다**(GPU 2장).

`gen_oil_probe.py`가 뜻밖의 것을 보여줬다: 유화 프롬프트는 CN 0.8에서도 잉크 .7215, CN 0에서
.7189로 **거의 같다.** 즉 ControlNet의 대비 억제는 절대적이지 않다 — 프롬프트가 세게 반대로 밀면
뚫린다. 앞선 34배 낙차는 「CN이 대비를 죽인다」와 「프롬프트도 저대비를 요구한다」가 **같은 방향으로
겹친** 결과였다.

그런데 유화는 정답지 구간(.102~.221)을 3~7배 **초과**한다 — 목표 화풍이 아니라 다른 화풍이다.
그래서 목표 화풍(연필 동화책)을 **그대로 두고 대비를 요구하는 낱말만** 바꾼다:

    현행: gentle hand-drawn lines · light shading · muted palette
    개정: confident dark graphite linework · strong tonal contrast · deep shadows

인물·배경 문구는 현행 그대로다 — **이 묶음에서 움직이는 축은 화풍 낱말 하나뿐이다.**
두 번째 장은 거기에 치비 방지 부정어를 더한다(task#317 S2가 축 A를 올린 그 어휘).

Usage: /Users/calmonion/.local/biblemap-imggen/.venv314/bin/python gen_contrast_flip.py
"""
import os
import sys
import time

import torch
from diffusers import ControlNetModel, StableDiffusionXLControlNetPipeline
from diffusers.image_processor import IPAdapterMaskProcessor
from PIL import Image

import params

OUT = os.path.join(params.OUT_ROOT, "flip")
MASKS = os.path.join(params.OUT_ROOT, "masks")
COND_SCENE = os.path.join(params.OUT_ROOT, "cond-scene-ctrl.png")

sys.path.insert(0, params.CANON_DIR)
import derive_prompts  # noqa: E402

# 현행 화풍 블록에서 **대비를 낮추라고 말하는 낱말만** 교체한다. 나머지(미색 종이·연필·색연필·
# 동화책 삽화·단순한 배경)는 글자 그대로 유지 — 목표 화풍을 바꾸는 것이 아니라 그 안에서
# 대비 요구의 부호만 뒤집는 것이다.
# 34토큰 — 현행 화풍 블록(33토큰)과 거의 같은 무게라 인물·배경 문구를 그대로 두고도 77에 들어간다
# (첫 시도는 39토큰이라 전체 81이 됐고 토큰 하드 게이트가 정확히 막았다).
STYLE_FLIP = ("warm cream paper, soft pencil and colored-pencil storybook illustration, "
              "dark graphite linework, strong tonal contrast, deep shadows, "
              "simple, clean background.")
FLIP = f"{STYLE_FLIP} {derive_prompts.SCENE_PERSON} {derive_prompts.BG_VOCAB}"
NEG_BASE = derive_prompts.NEG
NEG_CHIBI = f"{NEG_BASE}, {derive_prompts.AXIS_EN['age']['소년/청년'][1]}"



def main():
    os.makedirs(OUT, exist_ok=True)
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
    lim = pipe.tokenizer.model_max_length
    print(f"로드 {time.time() - t:.0f}s")
    print(f"  flip {len(pipe.tokenizer(FLIP).input_ids):3d}/{lim} 토큰")
    for pr, lbl in ((FLIP, "긍정"), (NEG_CHIBI, "부정+치비금지")):
        n = len(pipe.tokenizer(pr).input_ids)
        if n > lim:
            sys.exit(f"{lbl}이 한도를 넘었다({n}) — 조용히 잘리므로 중단한다")

    jobs = [("flip", FLIP, NEG_BASE), ("flip-chibi", FLIP, NEG_CHIBI)]
    for label, pr, ng in jobs:
        out = os.path.join(OUT, f"{label}-s{params.SEED_FIXED}.png")
        if os.path.exists(out):
            print(f"  [스킵] {os.path.basename(out)}")
            continue
        ts = time.time()
        pipe(prompt=pr, negative_prompt=ng, image=cond,
             width=params.SCENE_SIZE[0], height=params.SCENE_SIZE[1],
             controlnet_conditioning_scale=params.SCENE_CN,
             num_inference_steps=params.STEPS, guidance_scale=params.GUIDANCE,
             ip_adapter_image=refs, cross_attention_kwargs={"ip_adapter_masks": masks},
             generator=torch.Generator("mps").manual_seed(params.SEED_FIXED)
             ).images[0].save(out)
        print(f"  [{label}] {time.time() - ts:.0f}s -> {os.path.basename(out)}", flush=True)
    print(f"완료: {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
