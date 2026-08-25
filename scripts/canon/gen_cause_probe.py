"""task#317 S1 확장 — 화풍을 죽이는 것이 무엇인지 극한값으로 가른다(GPU 2장).

**왜 필요한가.** S1의 `cge` 스윕은 화풍을 움직이지 못했다(ink 0.0046~0.0066, 단조성 없음).
그런데 계획의 가설은 「ControlNet 경로가 화풍을 죽인다」였다. cge를 0.3까지 내려 스텝의 70%를
CN 없이 돌려도 안 움직였다면, **가설 자체를 극한에서 확인해야 한다** — 아니면 「CN 탓」이라는
판정문만 남고 근거는 반증된 채로 다음 슬라이스에 실린다(ADR `260825-013641`).

**무엇을 이미 아는가**(GPU 0, 원자료를 읽어 확인):
  - 정답지를 만든 `~/.local/biblemap-imggen/prompts/scene-2-goliath.txt`의 **화풍 블록은 현행과
    글자 그대로 같고**, 인물 문구도 거의 같다("at far left"/"on the left" 차이뿐).
    ⇒ **프롬프트는 범인이 아니다.**
  - 정답지 생성기(`scenes.py`)와 현행의 차이는 셋뿐이다: ① ControlNet 유무 ② IP-Adapter
    레퍼런스가 **화풍을 가진 시트**(ink 0.20)인가 **창백한 동결 두상**(ink 0.006)인가, 그리고
    그 강도(0.7 vs 0.3) ③ 시드.

그래서 두 장을 찍는다 — 둘 다 ControlNet 강도 0(아예 끈다):
  (i)  refs ON  — CN만 끈다. 화풍이 살아나면 **CN이 원인**이고 처방은 2패스(S3)다.
  (ii) refs OFF — CN도 레퍼런스도 없다. 정답지 생성 조건에 가장 가깝다. 여기서도 창백하면
       원인은 CN이 아니라 **파이프라인/스케줄러 층**이고, 계획의 S5 분기표가 통째로 바뀐다.

구도는 CN을 끄면 무너진다(축 C가 떨어지는 것이 정상) — 이 두 장은 **원인 규명용이지 후보가 아니다**.

Usage: /Users/calmonion/.local/biblemap-imggen/.venv314/bin/python gen_cause_probe.py
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

OUT = os.path.join(params.OUT_ROOT, "cause")
MASKS = os.path.join(params.OUT_ROOT, "masks")
COND_SCENE = os.path.join(params.OUT_ROOT, "cond-scene-ctrl.png")


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

    for label, with_ref in (("cn0-ref", True), ("cn0-noref", False)):
        out = os.path.join(OUT, f"{label}-s{params.SEED_FIXED}.png")
        if os.path.exists(out):
            print(f"  [스킵] {os.path.basename(out)}")
            continue
        t = time.time()
        kw = dict(prompt=PROMPT, negative_prompt=NEG, image=cond,
                  width=params.SCENE_SIZE[0], height=params.SCENE_SIZE[1],
                  controlnet_conditioning_scale=0.0,   # ControlNet을 끈다 — 원인 규명용 극한값
                  num_inference_steps=params.STEPS, guidance_scale=params.GUIDANCE,
                  generator=torch.Generator("mps").manual_seed(params.SEED_FIXED))
        if with_ref:
            kw["ip_adapter_image"] = refs
            kw["cross_attention_kwargs"] = {"ip_adapter_masks": masks}
        else:
            # 어댑터를 로드한 채 이미지를 안 주면 UNet이 `image_embeds` 없다고 죽는다
            # (scale 0으로는 안 된다 — 아예 내려야 한다). gen_scene.py의 (a) 조건과 같은 형태.
            pipe.unload_ip_adapter()
        pipe(**kw).images[0].save(out)
        print(f"  [{label}] {time.time() - t:.0f}s -> {os.path.basename(out)}", flush=True)
    print(f"완료: {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
