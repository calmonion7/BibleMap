"""순차 인페인팅 + 종횡비를 지키는 수동 크롭 — 세 결함을 한 번에 고친다(GPU 2장).

앞선 두 시험이 각각 절반씩 맞았다:

  `gen_staged.py`  잘라 그리고 **붙였다** → 해상도 3.1배는 얻었으나 bbox 사각형 자국이 남았다
  `gen_sequential.py` 캔버스 하나에 **인페인팅** → 이음새는 사라졌으나 인물이 뭉개졌다

뭉개진 원인 둘은 방법이 아니라 인자였다:
  ① **초상 프롬프트를 전신 영역에 썼다** — "close-up head portrait …, facing forward"를 전신
     실루엣에 걸어 가면 같은 형체가 나왔다. → `derive_prompts.figure_prompt()`로 전신 문장을
     따로 파생했다(같은 5축·BRIEF·나이에서, 동작만 더한다).
  ② **`padding_mask_crop`이 종횡비를 뭉갠다** — 넘긴 width/height를 무시하고 캔버스 크기를
     강제한 뒤 `resize_mode="fill"`로 세로 크롭을 가로로 채운다(파이프라인 소스 1539~1542행).
     → 쓰지 않는다. 마스크 둘레를 **직접** 잘라 종횡비를 지킨 크기로 그린다.

## 이 스크립트가 하는 일

    마스크 bbox + 여백 → 그 창을 종횡비 유지한 채 1024급으로 확대
    → 그 창 안에서 인페인팅(그림·마스크·콘티를 같은 창으로 자른다)
    → 원래 크기로 줄여 **마스크 화소만** 되돌린다

경계가 **안 바뀐 배경 화소**에 떨어지므로 이음새가 생길 자리가 없다 —
`padding_mask_crop`이 하려던 일을 종횡비를 지키며 하는 것이다.

Usage: /Users/calmonion/.local/biblemap-imggen/.venv314/bin/python gen_combined.py
"""
import json
import os
import sys
import time

import numpy as np
import torch
from diffusers import ControlNetModel, StableDiffusionXLControlNetInpaintPipeline
from PIL import Image

import params

sys.path.insert(0, params.CANON_DIR)
import derive_prompts  # noqa: E402
import gen_sequential as seq  # noqa: E402  — figure_mask(잉크 부풀리기)를 재사용한다
import judge_metrics as jm  # noqa: E402

OUT = os.path.join(params.OUT_ROOT, "combined3")
MASKS = os.path.join(params.OUT_ROOT, "masks")
COND_SCENE = os.path.join(params.OUT_ROOT, "cond-scene-ctrl.png")
# 배경(1단계) 산출. argv로 갈아끼울 수 있다 — 화풍 레퍼런스를 태운 배경을 쓰기 위해서다.
BG_SOURCE = os.path.join(params.OUT_ROOT, "styleref", "sheet1.0-cn0.8-s11.png")
STYLE_SHEET = os.path.join(params.REFERENCE, "sheet-s200.png")
# 인물 단계에 함께 물리는 화풍 레퍼런스 강도. argv[2]로 갈아끼운다.
# **0이 기본이다** — 0.7로 물렸더니 화풍은 올랐으나(ink .0191 → .0361) 동결 얼굴(IP_SCALE 0.3)보다
# 세서 얼굴을 덮었다(골리앗 축 B +0.1942 → +0.0256). 배경의 화풍은 인페인팅이 맥락으로 이미
# 나르므로 인물 단계에서 시트를 또 물릴 이유가 없다.
STYLE_IP = 0.0
PAD = 64          # 마스크 둘레 여백(px) — 모델에게 맥락을 준다
TARGET = 1024     # 확대한 창의 긴 변
STRENGTH = 0.99


def window(mask, pad):
    """마스크를 감싸는 창(여백 포함, 캔버스 안으로 클램프)."""
    a = np.array(mask) > 127
    ys, xs = np.where(a)
    W, H = params.SCENE_SIZE
    return (max(0, int(xs.min()) - pad), max(0, int(ys.min()) - pad),
            min(W, int(xs.max()) + 1 + pad), min(H, int(ys.max()) + 1 + pad))


def gen_size(box, target=TARGET):
    """창의 종횡비를 지키면서 긴 변을 target으로. 8의 배수로 맞춘다."""
    w, h = box[2] - box[0], box[3] - box[1]
    s = target / max(w, h)
    return max(8, round(w * s / 8) * 8), max(8, round(h * s / 8) * 8)


def main():
    os.makedirs(OUT, exist_ok=True)
    derive_prompts.main()
    P = json.load(open(params.PROMPTS_JSON, encoding="utf-8"))
    cond = Image.open(COND_SCENE).convert("RGB").resize(params.SCENE_SIZE)
    bg_src = sys.argv[1] if len(sys.argv) > 1 else BG_SOURCE
    style_ip = float(sys.argv[2]) if len(sys.argv) > 2 else STYLE_IP
    canvas = Image.open(bg_src).convert("RGB").resize(params.SCENE_SIZE)
    print(f"배경(1단계): {os.path.basename(bg_src)}  ·  인물 단계 화풍 시트 강도 {style_ip}")
    masks = {n: seq.figure_mask(n) for n in ("david", "goliath")}

    t = time.time()
    cn = ControlNetModel.from_pretrained(params.CN_MODEL, torch_dtype=torch.float16)
    pipe = StableDiffusionXLControlNetInpaintPipeline.from_pretrained(
        params.SDXL_BASE, controlnet=cn, torch_dtype=torch.float16, variant="fp16",
        use_safetensors=True).to("mps")
    pipe.set_progress_bar_config(disable=True)
    # 레퍼런스 2장 — 동결 얼굴(정체성) + 화풍 시트(화풍). 마스크 없이 둘 다 크롭 전체에 건다:
    # 인물 단계의 크롭은 그 인물이 화면의 대부분이라 영역을 나눌 이유가 없고, 화풍은 원래
    # 전면에 걸려야 한다. 시트를 안 물리면 인물 자리만 배경보다 창백해진다(동결본 잉크 0.006).
    pipe.load_ip_adapter(params.IP_ADAPTER_REPO, subfolder=params.IP_ADAPTER_SUBFOLDER,
                         weight_name=[params.IP_ADAPTER_WEIGHT] * 2)
    pipe.set_ip_adapter_scale([params.IP_SCALE, style_ip])
    sheet = Image.open(STYLE_SHEET).convert("RGB")
    lim = pipe.tokenizer.model_max_length
    print(f"로드 {time.time() - t:.0f}s")

    for step, name in ((1, "david"), (2, "goliath")):
        out = os.path.join(OUT, f"{step}-{name}-s{params.SEED_FIXED}.png")
        if os.path.exists(out):
            print(f"  [스킵] {os.path.basename(out)}")
            canvas = Image.open(out).convert("RGB")
            continue
        m = masks[name]
        box = window(m, PAD)
        bw, bh = box[2] - box[0], box[3] - box[1]
        gw, gh = gen_size(box)
        pr, ng = P["figure"][name]["prompt"], P["figure"][name]["negative"]
        n = len(pipe.tokenizer(pr).input_ids)
        if n > lim:
            sys.exit(f"{name} 전신 프롬프트가 한도를 넘었다({n})")
        ref = [[Image.open(os.path.join(params.FROZEN, f"{name}.png")).convert("RGB")], [sheet]]

        # 그림·마스크·콘티를 **같은 창**으로 자르고 같은 배율로 키운다 — 셋이 어긋나면 안 된다.
        sub_img = canvas.crop(box).resize((gw, gh), Image.LANCZOS)
        sub_msk = m.crop(box).resize((gw, gh), Image.LANCZOS)
        sub_cnd = cond.crop(box).resize((gw, gh), Image.LANCZOS)

        ts = time.time()
        res = pipe(prompt=pr, negative_prompt=ng, image=sub_img, mask_image=sub_msk,
                   control_image=sub_cnd, width=gw, height=gh,
                   controlnet_conditioning_scale=params.SCENE_CN, strength=STRENGTH,
                   num_inference_steps=params.STEPS, guidance_scale=params.GUIDANCE,
                   ip_adapter_image=ref,
                   generator=torch.Generator("mps").manual_seed(params.SEED_FIXED)).images[0]

        # 줄여서 **마스크 화소만** 되돌린다 — 경계가 안 바뀐 배경에 떨어져 이음새가 없다.
        canvas.paste(res.resize((bw, bh), Image.LANCZOS), (box[0], box[1]),
                     m.crop(box))
        canvas.save(out)
        print(f"  [{step} {name}] {time.time() - ts:.0f}s  프롬프트 {n}/{lim}토큰  "
              f"창 {bw}x{bh} → {gw}x{gh} (배율 {gw / bw:.1f}x) -> {os.path.basename(out)}", flush=True)

    final = os.path.join(OUT, f"3-final-s{params.SEED_FIXED}.png")
    canvas.save(final)

    # --- 판정 ---------------------------------------------------------------
    emb = jm.Embedder()
    frozen = {n: emb.embed(Image.open(os.path.join(params.FROZEN, f"{n}.png")))
              for n in ("david", "goliath")}
    head = {n: jm.bbox_from_mask(os.path.join(MASKS, f"{n}_head.png")) for n in frozen}
    others = {
        "현행 한번에": os.path.join(params.OUT_ROOT, "scene", f"c-mask-s{params.SEED_FIXED}.png"),
        "잘라붙이기": os.path.join(params.OUT_ROOT, "staged", f"4-final-s{params.SEED_FIXED}.png"),
        "순차(초상문장)": os.path.join(params.OUT_ROOT, "seq", f"3-final-s{params.SEED_FIXED}.png"),
    }
    print("\n동결 정본과의 유사도 (머리 크롭, 절대값)")
    hdr = "  {:9s}".format("") + "".join(f"{k:>15s}" for k in others) + f"{'이번(결합)':>13s}"
    print(hdr)
    for name in ("david", "goliath"):
        vals = []
        for p in others.values():
            im = Image.open(p).convert("RGB").resize(params.SCENE_SIZE)
            vals.append(jm.cos(emb.embed(im.crop(head[name])), frozen[name]))
        v_new = jm.cos(emb.embed(Image.open(final).convert("RGB").crop(head[name])), frozen[name])
        print(f"  {name:9s}" + "".join(f"{v:15.4f}" for v in vals) + f"{v_new:13.4f}")
    print(f"\n최종: {final}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
