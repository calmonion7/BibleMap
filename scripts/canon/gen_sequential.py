"""순차 인페인팅 — 화면은 하나, 그 위에 배경 → 다윗 → 골리앗을 차례로 그려 넣는다(GPU 3장).

`gen_staged.py`가 한 것은 **잘라 그리고 붙이기**였고, 그래서 bbox 사각형 자국이 남았다.
이 스크립트는 자르지 않는다 — **캔버스는 계속 하나**이고 각 단계는 앞 단계의 그림을 통째로
받아 **지정한 영역만 다시 그린다**(인페인팅). 모델이 주변을 보면서 그 안을 채우므로 이음새가
원리적으로 생기지 않는다.

## 두 가지를 같이 얻는다

**① 이음새 없음** — 붙이는 것이 아니라 모델이 채운다.
**② 해상도** — `padding_mask_crop`이 마스크 둘레를 여유 있게 잘라 **생성 해상도로 키워 그린 뒤
   마스크 부분만 되돌린다.** 다윗을 251px가 아니라 1024급으로 그리면서도, 되돌아오는 것은
   마스크 안쪽뿐이라 바깥은 한 픽셀도 안 변한다. `gen_staged.py`가 손으로 하던 일을
   파이프라인이 정확히 해 준다.

**③ 토큰** — 단계마다 77을 통째로 쓴다. 2인 합본(86토큰)에서 버려야 했던 조각이 살아남는다.

## 마스크를 사각형으로 쓰지 않는다

`masks/*.png`는 bbox(꽉 찬 사각형)라 그대로 쓰면 인물 주변 배경까지 다시 그려져 네모가 비친다.
그래서 **콘티 잉크를 부풀린 마스크**를 여기서 파생한다(`masks/_raw_*.png`는 `make_masks.py`가
delay 범위로 찍어 둔 인물 선 원본이다). 부풀리는 반경만큼 모델에게 여유를 주되, 배경은 남는다.

## 대조

다윗을 두 번 그린다 — `padding_mask_crop` **없이**(사용자 흐름 그대로, 캔버스 해상도에서 그린다)와
**있이**. 둘의 차이가 곧 「크게 그리는 것」의 몫이다. 골리앗은 좋은 쪽 위에만 얹는다.

Usage: /Users/calmonion/.local/biblemap-imggen/.venv314/bin/python gen_sequential.py
"""
import json
import os
import sys
import time

import numpy as np
import torch
from diffusers import ControlNetModel, StableDiffusionXLControlNetInpaintPipeline
from PIL import Image, ImageFilter

import params

sys.path.insert(0, params.CANON_DIR)
import derive_prompts  # noqa: E402
import judge_metrics as jm  # noqa: E402

OUT = os.path.join(params.OUT_ROOT, "seq")
MASKS = os.path.join(params.OUT_ROOT, "masks")
COND_SCENE = os.path.join(params.OUT_ROOT, "cond-scene-ctrl.png")
BG_SOURCE = os.path.join(params.OUT_ROOT, "staged", "1-bg-s11.png")  # 1단계 산출을 재사용
DILATE = 41      # 잉크를 부풀리는 커널(홀수 px). 인물보다 넉넉하되 배경을 다 먹지 않는 크기.
PAD = 48         # padding_mask_crop — 마스크 둘레로 이만큼 더 잘라 맥락을 준다.
STRENGTH = 0.99  # 마스크 안을 사실상 새로 그린다(낮추면 앞 단계의 창백함을 물고 간다)


def figure_mask(name):
    """콘티 잉크를 부풀려 인물 모양 마스크를 만든다 — bbox 사각형을 쓰면 네모가 비친다."""
    raw = os.path.join(MASKS, f"_raw_{name}.png")
    if not os.path.exists(raw):
        sys.exit(f"인물 선 원본이 없다: {raw} — make_masks.py를 먼저 돌려라")
    im = Image.open(raw).convert("L").resize(params.SCENE_SIZE, Image.LANCZOS)
    a = np.array(im).astype(int)
    bg = int(np.median(a[0:8, 0:8]))
    ink = (np.abs(a - bg) > params.THRESHOLD).astype(np.uint8) * 255
    m = Image.fromarray(ink, mode="L").filter(ImageFilter.MaxFilter(DILATE))
    return m.filter(ImageFilter.GaussianBlur(DILATE / 8))


def main():
    os.makedirs(OUT, exist_ok=True)
    derive_prompts.main()
    P = json.load(open(params.PROMPTS_JSON, encoding="utf-8"))
    cond = Image.open(COND_SCENE).convert("RGB").resize(params.SCENE_SIZE)
    if not os.path.exists(BG_SOURCE):
        sys.exit(f"배경(1단계)이 없다: {BG_SOURCE} — gen_staged.py가 만든 것을 쓴다")
    bg = Image.open(BG_SOURCE).convert("RGB").resize(params.SCENE_SIZE)

    masks = {n: figure_mask(n) for n in ("david", "goliath")}
    for n, m in masks.items():
        cover = (np.array(m) > 127).mean()
        m.save(os.path.join(OUT, f"mask-{n}.png"))
        print(f"  마스크 {n:8s} 화면의 {cover * 100:.1f}% (bbox였다면 "
              f"{(np.array(Image.open(os.path.join(MASKS, f'{n}.png')).convert('L').resize(params.SCENE_SIZE)) > 0).mean() * 100:.1f}%)")

    t = time.time()
    cn = ControlNetModel.from_pretrained(params.CN_MODEL, torch_dtype=torch.float16)
    pipe = StableDiffusionXLControlNetInpaintPipeline.from_pretrained(
        params.SDXL_BASE, controlnet=cn, torch_dtype=torch.float16, variant="fp16",
        use_safetensors=True).to("mps")
    pipe.set_progress_bar_config(disable=True)
    pipe.load_ip_adapter(params.IP_ADAPTER_REPO, subfolder=params.IP_ADAPTER_SUBFOLDER,
                         weight_name=params.IP_ADAPTER_WEIGHT)
    pipe.set_ip_adapter_scale(params.IP_SCALE)
    lim = pipe.tokenizer.model_max_length
    print(f"로드 {time.time() - t:.0f}s")

    def paint(canvas, name, pad, label):
        out = os.path.join(OUT, f"{label}-s{params.SEED_FIXED}.png")
        if os.path.exists(out):
            print(f"  [스킵] {os.path.basename(out)}")
            return Image.open(out).convert("RGB")
        pr, ng = P[name]["prompt"], P[name]["negative"]
        n = len(pipe.tokenizer(pr).input_ids)
        if n > lim:
            sys.exit(f"{name} 프롬프트가 한도를 넘었다({n})")
        ref = Image.open(os.path.join(params.FROZEN, f"{name}.png")).convert("RGB")
        kw = dict(prompt=pr, negative_prompt=ng, image=canvas, mask_image=masks[name],
                  control_image=cond, width=params.SCENE_SIZE[0], height=params.SCENE_SIZE[1],
                  controlnet_conditioning_scale=params.SCENE_CN, strength=STRENGTH,
                  num_inference_steps=params.STEPS, guidance_scale=params.GUIDANCE,
                  ip_adapter_image=ref,
                  generator=torch.Generator("mps").manual_seed(params.SEED_FIXED))
        if pad is not None:
            kw["padding_mask_crop"] = pad
        ts = time.time()
        img = pipe(**kw).images[0]
        img.save(out)
        print(f"  [{label}] {time.time() - ts:.0f}s  프롬프트 {n}/{lim}토큰  "
              f"padding_mask_crop={pad} -> {os.path.basename(out)}", flush=True)
        return img

    print("\n2단계 — 배경 위에 다윗을 그려 넣는다 (두 방식 비교)")
    d_plain = paint(bg, "david", None, "2-david-plain")     # 캔버스 해상도 그대로
    d_crop = paint(bg, "david", PAD, "2-david-hires")       # 마스크 둘레를 키워 그린다

    print("\n3단계 — 다윗까지 그려진 그림 위에 골리앗을 그려 넣는다")
    final = paint(d_crop, "goliath", PAD, "3-final")

    # --- 판정: 얼굴이 동결 정본에 붙었는가 (원자료 절대값) --------------------
    emb = jm.Embedder()
    frozen = {n: emb.embed(Image.open(os.path.join(params.FROZEN, f"{n}.png")))
              for n in ("david", "goliath")}
    head = {n: jm.bbox_from_mask(os.path.join(MASKS, f"{n}_head.png")) for n in frozen}
    cur = Image.open(os.path.join(params.OUT_ROOT, "scene",
                                  f"c-mask-s{params.SEED_FIXED}.png")).convert("RGB").resize(params.SCENE_SIZE)
    staged = os.path.join(params.OUT_ROOT, "staged", f"4-final-s{params.SEED_FIXED}.png")
    print("\n동결 정본과의 유사도 (머리 크롭, 절대값)")
    print(f"  {'':9s} {'현행 한번에':>11s} {'잘라붙이기':>11s} {'순차(캔버스)':>13s} {'순차(고해상)':>13s} {'최종':>8s}")
    for name in ("david", "goliath"):
        row = {"현행": cur, "붙이기": Image.open(staged).convert("RGB"),
               "평면": d_plain, "고해상": d_crop, "최종": final}
        vals = {k: jm.cos(emb.embed(v.crop(head[name])), frozen[name]) for k, v in row.items()}
        print(f"  {name:9s} {vals['현행']:11.4f} {vals['붙이기']:11.4f} "
              f"{vals['평면']:13.4f} {vals['고해상']:13.4f} {vals['최종']:8.4f}")
    print(f"\n최종: {os.path.join(OUT, f'3-final-s{params.SEED_FIXED}.png')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
