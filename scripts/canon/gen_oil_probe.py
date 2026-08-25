"""task#317 후속 탐색 — 「고대비를 요구하는 화풍 블록」이 ControlNet을 견디는가(GPU 4장).

**왜 이 시험인가.** task#317이 확정한 것은 ControlNet이 대비를 눌러 화풍을 죽인다는 것이었다
(CN 0.8 → ink .0051, CN 0 → .0983, 34배). 그런데 실행 뒤 사용자가 제시한 프롬프트를 보고
현행 화풍 블록을 다시 읽으니 **그 블록 자체가 저대비를 요구하고 있다**:

    현행:  light shading(옅은 음영) · muted palette(절제된 색) · gentle hand-drawn lines
    제시안: dramatic lighting · rich textured brushwork · warm directional light · high detail

즉 대비를 죽이는 힘이 둘이었을 수 있다 — ControlNet **과** 프롬프트. 앞의 것만 실측했다.
프롬프트가 반대로 밀면 ControlNet 아래에서도 잉크가 남는지는 **한 번도 안 봤다.**

**토큰 사실.** 제시안 원문은 **379토큰**이라 CLIP 77에서 80%가 조용히 잘린다 — 다윗·골리앗·
군대·붓질 묘사가 전부 사라지고 앞 두 문장(배경 설정)만 도달한다. `raster-pilot/FINDINGS.md`
결함 1이 정확히 이것이고(151토큰이 잘려 화풍 블록 소실), 그래서 (raw)를 대조군으로 함께 찍는다 —
「길게 쓰면 좋다」가 이 파이프라인에서 어떻게 배신하는지를 그림으로 남긴다.

네 장 (시드 11 고정 · 레퍼런스·마스크·STEPS·GUIDANCE 전부 현행 그대로):
  (raw)     제시안 원문 그대로  + CN 0.8  — 잘림이 실제로 무엇을 만드는가
  (fitA)    압축·원문 구도 유지 + CN 0.8  — 「골리앗이 쓰러진다」가 콘티(둘 다 서 있음)와 싸운다
  (fitB)    압축·콘티에 정렬    + CN 0.8  — **본 시험**: 고대비 화풍이 CN을 견디는가
  (fitB-cn0) 같은 프롬프트      + CN 0    — 천장(이 프롬프트가 낼 수 있는 최대)

네거티브는 제시안의 권장을 따르되(`blurry, low quality, deformed`) **글자 금지는 남긴다** —
조건 입력에 글자가 없어도 새어 나오는 것이 raster-pilot 결함 2다.

Usage: /Users/calmonion/.local/biblemap-imggen/.venv314/bin/python gen_oil_probe.py
"""
import os
import sys
import time

import torch
from diffusers import ControlNetModel, StableDiffusionXLControlNetPipeline
from diffusers.image_processor import IPAdapterMaskProcessor
from PIL import Image

import params

OUT = os.path.join(params.OUT_ROOT, "oil")
MASKS = os.path.join(params.OUT_ROOT, "masks")
COND_SCENE = os.path.join(params.OUT_ROOT, "cond-scene-ctrl.png")

RAW = (
    "A sweeping, epic oil painting in a dramatic, romantic realism style depicting the "
    "legendary battle between David and Goliath, set in a rugged, arid valley in ancient Judea "
    "at late afternoon. The scene captures the critical moment of the confrontation on a rocky, "
    "dusty battlefield with rolling hills and an ancient fortified city (Gath) in the background "
    "under a dramatic, cloudy sky with warm sunset light breaking through. On the left, David, a "
    "young shepherd boy with flowing brown hair, dressed in a simple tunic and leather sling "
    "pouch, is dynamically engaged in the act of releasing a stone from his slingshot, his body "
    "twisted forward, gaze intensely fixed on Goliath. Goliath, a colossal giant clad in heavy "
    "bronze armor (scale mail, greaves, helmet with crest, large shield, and spear), towers over "
    "David, reeling backward with a pained, shocked expression, struck in the forehead by the "
    "stone, dropping his massive sword and shield. The giant is falling backward, his enormous "
    "armored form dominating the right side of the composition on the uneven, rocky ground. The "
    "background is filled with the opposing armies: thousands of Philistine soldiers in armor "
    "stand shocked and chaotic on the ridge behind Goliath, while the smaller, awestruck "
    "Israelite army watches from the opposite hill. The ground is dusty and strewn with rocks. "
    "David stands firmly on a small mound. The painting has rich, textured brushwork, capturing "
    "the movement, tension, dust, and dramatic lighting. The composition is dynamic with diagonal "
    "lines. The giant wears detailed armor; David holds his sling high. The background hills, the "
    "distant city walls, and the multitude of soldiers are visible but secondary to the central "
    "figures. The light is warm and directional, illuminating the figures against the epic, "
    "rugged landscape. The painting has a classical feel with high detail, capturing the texture "
    "of armor, cloth, and stone."
)
# 압축 — 앞이 무거울수록 CLIP에 세게 걸리므로 화풍을 맨 앞에 두고(FINDINGS 결함 1의 처방 그대로),
# 원문의 어휘를 그대로 살린다. 버린 것은 군대·도시·먼지 같은 **부차 요소**이지 화풍이 아니다.
FIT_A = ("An epic oil painting in dramatic romantic realism: a young shepherd boy releases a "
         "stone from his sling on the left, a colossal giant in heavy bronze armor reels backward "
         "on the right, on a rocky dusty battlefield under a cloudy sky, warm directional sunset "
         "light, rich textured brushwork.")
# 콘티(--at 9000)는 **둘 다 서 있고 다윗이 물매를 돌리는 중**이다. 원문의 「쓰러지는 골리앗」은
# 그 순간이 아니라서 ControlNet과 텍스트가 서로 다른 그림을 요구하게 된다 — 그래서 정렬본을 둔다.
FIT_B = ("An epic oil painting in dramatic romantic realism: a young shepherd boy swings a sling "
         "on the left, a colossal giant in heavy bronze armor stands on the right, on a rocky "
         "dusty battlefield under a cloudy sky, warm directional sunset light, rich textured "
         "brushwork, high detail.")
NEG = "blurry, low quality, deformed, text, letters, words, watermark, frame, border"


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
    for lbl, pr in (("raw", RAW), ("fitA", FIT_A), ("fitB", FIT_B)):
        print(f"  {lbl:5s} {len(pipe.tokenizer(pr).input_ids):3d}/{lim} 토큰"
              f"{'  ← 잘린다(의도된 대조군)' if len(pipe.tokenizer(pr).input_ids) > lim else ''}")

    jobs = [("raw", RAW, params.SCENE_CN), ("fitA", FIT_A, params.SCENE_CN),
            ("fitB", FIT_B, params.SCENE_CN), ("fitB-cn0", FIT_B, 0.0)]
    for label, pr, cns in jobs:
        out = os.path.join(OUT, f"{label}-s{params.SEED_FIXED}.png")
        if os.path.exists(out):
            print(f"  [스킵] {os.path.basename(out)}")
            continue
        ts = time.time()
        pipe(prompt=pr, negative_prompt=NEG, image=cond,
             width=params.SCENE_SIZE[0], height=params.SCENE_SIZE[1],
             controlnet_conditioning_scale=cns,
             num_inference_steps=params.STEPS, guidance_scale=params.GUIDANCE,
             ip_adapter_image=refs, cross_attention_kwargs={"ip_adapter_masks": masks},
             generator=torch.Generator("mps").manual_seed(params.SEED_FIXED)
             ).images[0].save(out)
        print(f"  [{label} cn={cns}] {time.time() - ts:.0f}s -> {os.path.basename(out)}", flush=True)
    print(f"완료: {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
