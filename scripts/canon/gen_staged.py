"""단계 생성 — 배경 → 다윗 → 골리앗을 따로 그려 합친다(GPU 3장).

**두 가지를 동시에 시험한다.**

① **토큰 예산.** 한 장에 두 인물을 다 실으면 86토큰이라 77을 넘고, 맞추려면 골리앗의 투구 같은
   특징을 버려야 한다(`gen_prompt_axis.py`가 실제로 버렸다). 단계로 나누면 **각 단계가 77토큰을
   통째로 쓴다** — 다윗 단계는 다윗만 말하면 되고, 그 문장은 초상 경로가 이미 파생해 둔 것이다.

② **인물 크기.** task#317의 벽은 「다윗 얼굴이 98px(동결 정본 1024px의 1/17)이라 치비로만
   그려지고, 치비를 막으면 사라진다」였다. 계획의 S5 분기는 여기서 **콘티 클로즈업 축 개방
   → 296장면 저작 규약 변경**(큰 결정)으로 갔다. 그런데 인물 영역만 **떼어 크게 그린 뒤 줄여
   붙이면** 콘티를 그대로 두고 해상도를 얻는다 — 다윗 bbox 251x327을 768x1024로 그리면
   얼굴이 약 400px, **4배**다.

## 단계

    1) 배경   전체 캔버스 1216x640, 인물 어휘 없는 프롬프트, CN=콘티 전체
    2) 다윗   1)의 다윗 bbox를 잘라 768x1024로 확대 → 그 영역의 콘티 크롭을 CN으로,
              다윗 전용 프롬프트(77토큰 전부) + 다윗 동결본만 IP로 → 원래 크기로 줄여 붙인다
    3) 골리앗 같은 방식(bbox 398x453 → 896x1024)

각 단계는 **앞 단계의 그림 위에** 그린다(사용자 제안 그대로). 붙일 때는 마스크 가장자리를
부드럽게 해 이음새를 줄인다 — 다만 이음새·화풍 드리프트는 이 시험의 관심사가 아니다.
**관심사는 하나: 크게 그리면 [[정본 전이]]가 붙는가.**

판정은 두 곳에서 한다 — 붙이기 **전 크롭**에서(해상도 효과 자체) 그리고 합친 **전체 장면**에서
(줄여 붙인 뒤에도 남는가). 앞의 것이 오르고 뒤의 것이 안 오르면 원인은 축소다.

Usage: /Users/calmonion/.local/biblemap-imggen/.venv314/bin/python gen_staged.py
"""
import json
import os
import sys
import time

import numpy as np
import torch
from diffusers import ControlNetModel, StableDiffusionXLControlNetPipeline
from PIL import Image, ImageFilter

import params

sys.path.insert(0, params.CANON_DIR)
import derive_prompts  # noqa: E402
import judge_metrics as jm  # noqa: E402

OUT = os.path.join(params.OUT_ROOT, "staged")
MASKS = os.path.join(params.OUT_ROOT, "masks")
COND_SCENE = os.path.join(params.OUT_ROOT, "cond-scene-ctrl.png")
FEATHER = 12   # 붙일 때 마스크 가장자리를 흐리는 반경(px). 이음새 완화용이지 판정 대상이 아니다.


def bbox_of(name):
    m = np.array(Image.open(os.path.join(MASKS, f"{name}.png")).convert("L")
                 .resize(params.SCENE_SIZE))
    ys, xs = np.where(m > 0)
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def gen_size(box, target=1024):
    """bbox의 종횡비를 지키면서 긴 변을 target으로. SDXL이 다루는 8의 배수로 맞춘다."""
    w, h = box[2] - box[0], box[3] - box[1]
    s = target / max(w, h)
    return (max(8, int(round(w * s / 8)) * 8), max(8, int(round(h * s / 8)) * 8))


def main():
    os.makedirs(OUT, exist_ok=True)
    derive_prompts.main()
    P = json.load(open(params.PROMPTS_JSON, encoding="utf-8"))
    NEG = P["negative"]
    # 배경 단계는 인물 어휘를 안 쓴다 — 인물은 뒤 단계가 그린다. 화풍 + 배경만.
    BG_PROMPT = f"{derive_prompts.STYLE} {derive_prompts.BG_VOCAB}"
    # 인물 단계는 **초상 경로가 이미 파생한 문장을 그대로 쓴다.** 한 인물만 말하므로 77에 들어가고,
    # 두 인물을 합칠 때 버려야 했던 조각(골리앗의 투구)이 여기서는 살아남는다.
    PERSON_PROMPT = {n: P[n]["prompt"] for n in ("david", "goliath")}
    PERSON_NEG = {n: P[n]["negative"] for n in ("david", "goliath")}

    cond_full = Image.open(COND_SCENE).convert("RGB").resize(params.SCENE_SIZE)
    boxes = {n: bbox_of(n) for n in ("david", "goliath")}

    t = time.time()
    cn = ControlNetModel.from_pretrained(params.CN_MODEL, torch_dtype=torch.float16)
    pipe = StableDiffusionXLControlNetPipeline.from_pretrained(
        params.SDXL_BASE, controlnet=cn, torch_dtype=torch.float16, variant="fp16",
        use_safetensors=True).to("mps")
    pipe.set_progress_bar_config(disable=True)
    lim = pipe.tokenizer.model_max_length
    print(f"로드 {time.time() - t:.0f}s")
    print(f"  배경 프롬프트 {len(pipe.tokenizer(BG_PROMPT).input_ids)}/{lim}토큰")
    for n in ("david", "goliath"):
        print(f"  {n} 프롬프트 {len(pipe.tokenizer(PERSON_PROMPT[n]).input_ids)}/{lim}토큰"
              f"  (2인 합본은 86토큰이라 조각을 버려야 했다)")

    # --- 1) 배경 -------------------------------------------------------------
    bg_path = os.path.join(OUT, f"1-bg-s{params.SEED_FIXED}.png")
    if os.path.exists(bg_path):
        print(f"  [스킵] {os.path.basename(bg_path)}")
        canvas = Image.open(bg_path).convert("RGB")
    else:
        ts = time.time()
        canvas = pipe(prompt=BG_PROMPT, negative_prompt=NEG, image=cond_full,
                      width=params.SCENE_SIZE[0], height=params.SCENE_SIZE[1],
                      controlnet_conditioning_scale=params.SCENE_CN,
                      num_inference_steps=params.STEPS, guidance_scale=params.GUIDANCE,
                      generator=torch.Generator("mps").manual_seed(params.SEED_FIXED)).images[0]
        canvas.save(bg_path)
        print(f"  [1 배경] {time.time() - ts:.0f}s -> {os.path.basename(bg_path)}", flush=True)

    # --- 2·3) 인물 — 영역만 확대해 그리고 줄여 붙인다 -------------------------
    pipe.load_ip_adapter(params.IP_ADAPTER_REPO, subfolder=params.IP_ADAPTER_SUBFOLDER,
                         weight_name=params.IP_ADAPTER_WEIGHT)   # 인물 단계는 레퍼런스 1장뿐
    for step, name in ((2, "david"), (3, "goliath")):
        box = boxes[name]
        gw, gh = gen_size(box)
        crop_path = os.path.join(OUT, f"{step}-{name}-crop-s{params.SEED_FIXED}.png")
        if os.path.exists(crop_path):
            print(f"  [스킵] {os.path.basename(crop_path)}")
            crop = Image.open(crop_path).convert("RGB")
        else:
            # 조건 입력도 같은 영역만 잘라 확대한다 — 콘티를 바꾸지 않고 **보는 배율만** 키운다.
            cond_crop = cond_full.crop(box).resize((gw, gh), Image.LANCZOS)
            ref = Image.open(os.path.join(params.FROZEN, f"{name}.png")).convert("RGB")
            pipe.set_ip_adapter_scale(params.IP_SCALE)
            ts = time.time()
            crop = pipe(prompt=PERSON_PROMPT[name], negative_prompt=PERSON_NEG[name],
                        image=cond_crop, width=gw, height=gh,
                        controlnet_conditioning_scale=params.SCENE_CN,
                        num_inference_steps=params.STEPS, guidance_scale=params.GUIDANCE,
                        ip_adapter_image=ref,
                        generator=torch.Generator("mps").manual_seed(params.SEED_FIXED)).images[0]
            crop.save(crop_path)
            print(f"  [{step} {name}] {time.time() - ts:.0f}s  {box[2]-box[0]}x{box[3]-box[1]}"
                  f" → {gw}x{gh} (배율 {gw/(box[2]-box[0]):.1f}x) -> {os.path.basename(crop_path)}",
                  flush=True)
        # 줄여서 붙인다. 가장자리를 흐린 마스크로 합성해 이음새를 줄인다.
        bw, bh = box[2] - box[0], box[3] - box[1]
        patch = crop.resize((bw, bh), Image.LANCZOS)
        soft = Image.new("L", (bw, bh), 0)
        soft.paste(255, (FEATHER, FEATHER, bw - FEATHER, bh - FEATHER))
        soft = soft.filter(ImageFilter.GaussianBlur(FEATHER / 2))
        canvas.paste(patch, (box[0], box[1]), soft)

    final = os.path.join(OUT, f"4-final-s{params.SEED_FIXED}.png")
    canvas.save(final)
    print(f"\n합성 완료 -> {final}")

    # --- 판정: 크롭 자체 vs 합친 장면 ----------------------------------------
    emb = jm.Embedder()
    frozen = {n: emb.embed(Image.open(os.path.join(params.FROZEN, f"{n}.png")))
              for n in ("david", "goliath")}
    head = {n: jm.bbox_from_mask(os.path.join(MASKS, f"{n}_head.png")) for n in frozen}
    print("\n동결 정본과의 유사도 (절대값 — 짝짓기 없이 원자료로 본다)")
    print(f"  {'':10s} {'크게 그린 크롭':>14s} {'줄여 붙인 뒤':>14s} {'현행 장면':>12s}")
    cur = Image.open(os.path.join(params.OUT_ROOT, "scene",
                                  f"c-mask-s{params.SEED_FIXED}.png")).convert("RGB").resize(params.SCENE_SIZE)
    fin = Image.open(final).convert("RGB")
    for name in ("david", "goliath"):
        box = boxes[name]
        crop = Image.open(os.path.join(OUT, f"{2 if name == 'david' else 3}-{name}-crop-s{params.SEED_FIXED}.png"))
        # 크롭 안에서의 머리 위치 = 전체 머리 bbox를 인물 bbox 기준으로 옮겨 배율을 곱한 것
        hx0, hy0, hx1, hy1 = head[name]
        sx, sy = crop.width / (box[2] - box[0]), crop.height / (box[3] - box[1])
        hb = (int((hx0 - box[0]) * sx), int((hy0 - box[1]) * sy),
              int((hx1 - box[0]) * sx), int((hy1 - box[1]) * sy))
        v_crop = jm.cos(emb.embed(crop.crop(hb)), frozen[name])
        v_fin = jm.cos(emb.embed(fin.crop(head[name])), frozen[name])
        v_cur = jm.cos(emb.embed(cur.crop(head[name])), frozen[name])
        print(f"  {name:10s} {v_crop:14.4f} {v_fin:14.4f} {v_cur:12.4f}"
              f"   (머리 {hb[2]-hb[0]}px ← 현행 {hx1-hx0}px)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
