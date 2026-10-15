#!/usr/bin/env python3
"""task#347 S2/S3 — B-e(klein 얼굴) 얼굴은 지키고 화풍을 345 승인본 쪽으로 되돌리는 두 방식.
  VENV=~/.local/biblemap-imggen/.venv314/bin/python
  $VENV gen_face_style.py r1            # R1 머리 되붙이기(CPU): 승인본 위에 B-e 머리 타원을 LAB 맞춤 후 붙인다 — 8장
  $VENV gen_face_style.py enc|gen       # R2 저강도 img2img(GPU, 한 번에 하나): B-e 전체 → Z-Image-Turbo Q8 — 8장
설정은 params.FACE_STYLE_SETTINGS. 출력: samples/face-style/R1-g<배율>-<장면>-s<시드>.png · R2-s<강도>-<장면>-s<시드>.png."""
import json, os, sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import params

HERE = os.path.dirname(os.path.abspath(__file__))
AB = os.path.join(HERE, "samples", "face-ab")
OUT = os.path.join(HERE, "samples", "face-style")
RUN = os.path.expanduser("~/.local/biblemap-imggen/face-style/run")
JOBS = os.path.join(RUN, "r2-jobs.json")
SCENE = {"gilgal": "authored-saul-gilgal-coronation", "engedi": "authored-david-en-gedi-saul"}
WHO = {"gilgal": ["saul"], "engedi": ["david", "saul"]}
BASE = "Tongyi-MAI/Z-Image-Turbo"
GGUF = "leejet/Z-Image-Turbo-GGUF"


def src(scene, seed):
    return os.path.join(AB, f"B-e-{scene}-s{seed}.png")


# --- sRGB ↔ CIELAB(D65) — 새 의존성 없이 ---------------------------------------
_M = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])
_W = np.array([0.95047, 1.0, 1.08883])


def to_lab(rgb):
    c = rgb / 255.0
    c = np.where(c > 0.04045, ((c + 0.055) / 1.055) ** 2.4, c / 12.92)
    t = (c @ _M.T) / _W
    f = np.where(t > 0.008856, np.cbrt(t), 7.787 * t + 16 / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)


def from_lab(lab):
    fy = (lab[..., 0] + 16) / 116
    f = np.stack([fy + lab[..., 1] / 500, fy, fy - lab[..., 2] / 200], -1)
    t = np.where(f > 0.206893, f ** 3, (f - 16 / 116) / 7.787) * _W
    c = t @ np.linalg.inv(_M).T
    c = np.where(c > 0.0031308, 1.055 * np.clip(c, 0, None) ** (1 / 2.4) - 0.055, 12.92 * c)
    return np.clip(c * 255, 0, 255).astype(np.uint8)


def r1():
    from face_ab_heads import heads
    approved = {s: Image.open(os.path.join(AB, f"approved-{s}.png")).convert("RGB") for s in SCENE}
    os.makedirs(OUT, exist_ok=True)
    for scene in SCENE:
        for seed in params.FACE_AB_SEEDS:
            be = Image.open(src(scene, seed)).convert("RGB")
            hb = heads(scene, src(scene, seed))
            for grow in params.FACE_STYLE_SETTINGS["R1"]:
                im = approved[scene].copy()
                for who in WHO[scene]:
                    if who not in hb:
                        print("머리 못 찾음", scene, seed, who, flush=True)
                        continue
                    x0, y0, x1, y1 = hb[who]
                    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
                    rw, rh = (x1 - x0) / 2 * grow, (y1 - y0) / 2 * grow
                    m = Image.new("L", im.size, 0)
                    ImageDraw.Draw(m).ellipse([cx - rw, cy - rh, cx + rw, cy + rh], fill=255)
                    hard = np.asarray(m) > 127                    # LAB 통계는 타원 안쪽 화소로 잰다
                    m = m.filter(ImageFilter.GaussianBlur(2 * rw * params.FACE_STYLE_R1_FEATHER * 0.25))
                    a, b = to_lab(np.asarray(im, np.float64)), to_lab(np.asarray(be, np.float64))
                    mu_a, sd_a = a[hard].mean(0), a[hard].std(0) + 1e-6
                    mu_b, sd_b = b[hard].mean(0), b[hard].std(0) + 1e-6
                    head = Image.fromarray(from_lab((b - mu_b) / sd_b * sd_a + mu_a))
                    im = Image.composite(head, im, m)
                out = os.path.join(OUT, f"R1-g{grow}-{scene}-s{seed}.png")
                im.save(out)
                print("저장", out, flush=True)


def plan():
    from derive_scene import load, whole_prompt
    jobs = [{"scene": sc, "seed": seed, "strength": st, "src": src(sc, seed), "prompt": whole_prompt(load(sid)),
             "out": os.path.join(OUT, f"R2-s{st}-{sc}-s{seed}.png")}
            for sc, sid in SCENE.items() for seed in params.FACE_AB_SEEDS for st in params.FACE_STYLE_SETTINGS["R2"]]
    os.makedirs(RUN, exist_ok=True)
    os.makedirs(OUT, exist_ok=True)
    json.dump(jobs, open(JOBS, "w"), ensure_ascii=False, indent=1)


def worker(mode):
    import torch
    torch.set_grad_enabled(False)
    from diffusers import ZImagePipeline
    if mode == "enc":
        plan()
        jobs = json.load(open(JOBS))
        pipe = ZImagePipeline.from_pretrained(BASE, transformer=None, torch_dtype=torch.bfloat16).to("mps")
        torch.save([[t.cpu() for t in pipe.encode_prompt(j["prompt"], device="mps", do_classifier_free_guidance=False)[0]]
                    for j in jobs], JOBS + ".emb.pt")
        return
    jobs = json.load(open(JOBS))
    from diffusers import GGUFQuantizationConfig, ZImageImg2ImgPipeline, ZImageTransformer2DModel
    from diffusers.models.model_loading_utils import load_gguf_checkpoint
    from huggingface_hub import hf_hub_download
    sd = load_gguf_checkpoint(hf_hub_download(GGUF, "z_image_turbo-Q8_0.gguf"))
    for k in ("cap_pad_token", "x_pad_token"):    # ZIMAGE.md: GGUF 로드 우회 2줄
        sd[k] = sd[k].reshape(1, -1)
    tr = ZImageTransformer2DModel.from_single_file(sd, quantization_config=GGUFQuantizationConfig(compute_dtype=torch.bfloat16),
                                                   config=BASE, subfolder="transformer", torch_dtype=torch.bfloat16)
    pipe = ZImageImg2ImgPipeline.from_pretrained(BASE, transformer=tr, text_encoder=None, tokenizer=None, torch_dtype=torch.bfloat16).to("mps")
    pipe.set_progress_bar_config(disable=True)
    for j, e in zip(jobs, torch.load(JOBS + ".emb.pt")):
        im = Image.open(j["src"]).convert("RGB")
        pipe(prompt_embeds=[x.to("mps", torch.bfloat16) for x in e], image=im, strength=j["strength"],
             width=im.width, height=im.height, num_inference_steps=9, guidance_scale=0.0,
             generator=torch.Generator("mps").manual_seed(j["seed"])).images[0].save(j["out"])
        print("저장", j["out"], flush=True)


if __name__ == "__main__":
    r1() if sys.argv[1] == "r1" else worker(sys.argv[1])
