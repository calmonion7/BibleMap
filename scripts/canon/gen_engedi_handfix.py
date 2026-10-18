#!/usr/bin/env python3
"""엔게디 손 국소 수정 시험 — 마주 봄이 없는 B 그림(365, 손·칼만 눌림)에서 다윗 두 손·칼 부위만 Z-Image 인페인트로 다시 그린다.
  VENV=~/.local/biblemap-imggen/.venv314/bin/python
  $VENV gen_engedi_handfix.py enc    # 프롬프트 인코딩(Z-Image는 인코딩/생성을 프로세스로 쪼갠다 — ZIMAGE.md)
  $VENV gen_engedi_handfix.py gen    # B 시드 × 강도 × 인페인트 시드
회차 r1 = 첫 시험(gen_face_ab.crop_mask, 크롭이 아래로 넘치면 크림색 채움 → 손에 흰 얼룩) · r2 = 크롭을 그림 안으로 당김 + 굴빛 문구 + 작은 칼.
r3 = r2 고른 그림(s11·s202)에서 출발, 「칼이 옷을 자르는 모습」 문구 둘(P1 자르는 중 · P2 막 자른 조각) + 턱 없는 옛 칼(사용자: 「칼이 옷을 자르는 장면이 정확히 표현안됨」).
틀은 gen_face_ab.py(크롭 → 타원 마스크 → 인페인트 → 마스크 안쪽만 되붙임). 마스크 밖(얼굴·시선·사울)은 원본 그대로.
산출 ~/.local/biblemap-imggen/engedi-handfix/<회차>/B<시드>-st<강도>-i<인페인트 시드>.png. GPU 생성 프로세스는 머신에서 한 번에 하나."""
import os, sys

from PIL import Image, ImageDraw, ImageFilter

import params

import gen_face_ab as F

SRC = os.path.expanduser("~/.local/biblemap-imggen/engedi-gaze/B/s{seed}.png")
OUT = os.path.expanduser("~/.local/biblemap-imggen/engedi-handfix")
# 다윗 두 손·칼 상자(1216×640 원본 좌표, 눈으로 잡음) — 판정에서 손·칼만 눌린 B 시드
BOX = {7: (380, 440, 520, 540), 11: (360, 440, 500, 530), 101: (360, 480, 500, 580), 202: (400, 440, 540, 530)}
R = "r3"
START = {11: "r2/B11-st0.75-i2.png", 202: "r2/B202-st0.85-i2.png"}   # r3 출발 그림(OUT 기준)
STRENGTHS = (0.65, 0.8)
SEEDS = (1, 2)
LOOK = "tanned skin in warm low light, dark sepia tones, soft pencil and colored-pencil illustration with hand-drawn hatching"
KNIFE = "a small simple ancient knife with a plain wooden handle and no guard, its short blade no longer than a finger"
PROMPTS = {
    "P1": ("close-up of the two hands of a kneeling young man at ground level in a dim cave: one hand lifting the corner of the hem of "
           f"a dark brown wool cloak, the other hand holding {KNIFE}, the blade pushed through the lifted hem and slicing it, the cloth "
           f"parting along a straight fresh cut line, the corner half cut off, {LOOK}"),
    "P2": ("close-up of the two hands of a kneeling young man at ground level in a dim cave: one hand holding up a small cut-off corner "
           f"piece of dark brown wool cloth, the other hand holding {KNIFE}, the cloak hem on the ground below has a missing corner "
           f"with a fresh straight cut edge, {LOOK}"),
    # r4b(gen_engedi_handguide) — 칼 낱말을 빼야 큰 칼을 새로 그리지 않는다(r4: 강도 0.45에도 긴 칼로 덮음)
    "P3": ("close-up of the two hands of a kneeling young man at ground level in a dim cave, one hand lifting the edge of a dark "
           f"brown wool cloak that has a thin straight fresh slit cut into it, its corner coming apart, {LOOK}"),
}
EMB = os.path.join(OUT, f"emb-{R}-{{}}.pt")


def crop_mask(im, box):
    """gen_face_ab.crop_mask와 같은 크롭·타원 마스크, 단 크롭을 그림 안으로 당긴다(종이색 채움 없음)."""
    x0, y0, x1, y1 = box
    side = int(round(max(x1 - x0, y1 - y0) * params.FACE_AB_CROP_SCALE))
    l = min(max(int(round((x0 + x1) / 2 - side / 2)), 0), im.width - side)
    t = min(max(int(round((y0 + y1) / 2 - side / 2)), 0), im.height - side)
    k = 768 / side
    m = Image.new("L", (768, 768), 0)
    cx, cy = ((x0 + x1) / 2 - l) * k, ((y0 + y1) / 2 - t) * k
    rw, rh = (x1 - x0) * k / 2 * params.FACE_AB_MASK_GROW, (y1 - y0) * k / 2 * params.FACE_AB_MASK_GROW
    ImageDraw.Draw(m).ellipse([cx - rw, cy - rh, cx + rw, cy + rh], fill=255)
    m = m.filter(ImageFilter.GaussianBlur(768 * params.FACE_AB_MASK_FEATHER * 0.25))
    return im.crop((l, t, l + side, t + side)).resize((768, 768), Image.LANCZOS), m, (l, t, side)


def load_pipe():
    import torch
    from diffusers import GGUFQuantizationConfig, ZImageInpaintPipeline, ZImageTransformer2DModel
    from diffusers.models.model_loading_utils import load_gguf_checkpoint
    from huggingface_hub import hf_hub_download
    sd = load_gguf_checkpoint(hf_hub_download(F.GGUF, "z_image_turbo-Q8_0.gguf"))
    for k in ("cap_pad_token", "x_pad_token"):    # ZIMAGE.md: GGUF 로드 우회 2줄
        sd[k] = sd[k].reshape(1, -1)
    tr = ZImageTransformer2DModel.from_single_file(sd, quantization_config=GGUFQuantizationConfig(compute_dtype=torch.bfloat16),
                                                   config=F.BASE, subfolder="transformer", torch_dtype=torch.bfloat16)
    pipe = ZImageInpaintPipeline.from_pretrained(F.BASE, transformer=tr, text_encoder=None, tokenizer=None, torch_dtype=torch.bfloat16).to("mps")
    pipe.set_progress_bar_config(disable=True)
    return pipe


def worker(mode):
    import torch
    torch.set_grad_enabled(False)
    os.makedirs(os.path.join(OUT, R), exist_ok=True)
    if mode == "enc":
        from diffusers import ZImagePipeline
        pipe = ZImagePipeline.from_pretrained(F.BASE, transformer=None, torch_dtype=torch.bfloat16).to("mps")
        for k, p in PROMPTS.items():
            torch.save([t.cpu() for t in pipe.encode_prompt(p, device="mps", do_classifier_free_guidance=False)[0]], EMB.format(k))
        return
    pipe = load_pipe()
    embs = {k: [x.to("mps", torch.bfloat16) for x in torch.load(EMB.format(k))] for k in PROMPTS}
    for seed, start in START.items():
        base = Image.open(os.path.join(OUT, start)).convert("RGB")
        crop, mask, (l, t, side) = crop_mask(base, BOX[seed])
        for k, e in embs.items():
            for st in STRENGTHS:
                for i in SEEDS:
                    out = os.path.join(OUT, R, f"B{seed}-{k}-st{st}-i{i}.png")
                    if os.path.exists(out):
                        continue
                    new = pipe(prompt_embeds=e, image=crop, mask_image=mask, strength=st, height=768, width=768, num_inference_steps=9,
                               guidance_scale=0.0, generator=torch.Generator("mps").manual_seed(i)).images[0]
                    layer, mm = Image.new("RGB", base.size), Image.new("L", base.size, 0)
                    layer.paste(new.resize((side, side), Image.LANCZOS), (l, t))
                    mm.paste(mask.resize((side, side), Image.LANCZOS), (l, t))
                    Image.composite(layer, base, mm).save(out)    # 마스크 안쪽만 새 손 — 밖은 원본 그대로
                    print("[EngediHandfix] 저장", os.path.basename(out), flush=True)

if __name__ == "__main__":
    worker(sys.argv[1])
