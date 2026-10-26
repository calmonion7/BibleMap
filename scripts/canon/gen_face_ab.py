#!/usr/bin/env python3
"""task#346 S5 — A 갈래(LoRA 얼굴 인페인트) 비교 생성. 인물 1인 1LoRA를 차례로 얹어 머리 영역만 다시 그린다.
  VENV=~/.local/biblemap-imggen/.venv314/bin/python
  $VENV gen_face_ab.py plan                 # 머리 상자(OWLv2, CPU)를 읽어 작업표 jobs.json을 만든다
  $VENV gen_face_ab.py enc|gen              # 한 번에 하나씩(Z-Image는 인코딩/생성을 프로세스로 쪼갠다 — ZIMAGE.md)
출력: samples/face-ab/A-<e|f>-<gilgal|engedi>-s<시드>.png. (e)=345 승인 그림 출발, (f)=같은 345 장면 프롬프트의 다른 시드 후보 출발.
GPU 생성 프로세스는 머신에서 한 번에 하나."""
import json, os, sys
from PIL import Image, ImageDraw, ImageFilter

import params

HERE = os.path.dirname(os.path.abspath(__file__))
PILOT = os.path.abspath(os.path.join(HERE, "..", "..", ".forge", "reports", "scene-whole-pilot"))
RUN = os.path.expanduser("~/.local/biblemap-imggen/face-ab/run")
JOBS = os.path.join(RUN, "a-jobs.json")
OUT = os.path.join(HERE, "samples", "face-ab")
LORA = os.path.expanduser("~/.local/biblemap-imggen/lora/{who}-v1.safetensors")
SCENE = {"gilgal": "authored-saul-gilgal-coronation", "engedi": "authored-david-en-gedi-saul"}
WHO = {"gilgal": ["saul"], "engedi": ["david", "saul"]}      # LoRA가 있는 인물만
ANGLE = {"gilgal": "facing forward", "engedi": "in right profile"}   # 명세 시선(길갈 사울은 정면, 엔게디 둘은 오른쪽 옆얼굴)
STYLE = "warm cream paper, soft pencil and colored-pencil storybook illustration, gentle hand-drawn lines"
BASE = "Tongyi-MAI/Z-Image-Turbo"
GGUF = "leejet/Z-Image-Turbo-GGUF"


def prompt(who, scene):
    return f"{who}face, close-up head portrait, {ANGLE[scene]}, {STYLE}"


def plan():
    from face_ab_heads import heads
    jobs = []
    for scene, sid in SCENE.items():
        approved = os.path.join(PILOT, sid, "final.png")
        for seed in params.FACE_AB_SEEDS:
            for start, base in (("e", approved), ("f", os.path.join(PILOT, sid, "cand", f"whole-1216x640-s{seed}.png"))):
                hb = heads(scene, base)
                steps = [{"who": w, "box": hb[w], "prompt": prompt(w, scene)} for w in WHO[scene] if w in hb]
                jobs.append({"base": base, "seed": seed, "steps": steps, "out": os.path.join(OUT, f"A-{start}-{scene}-s{seed}.png")})
    os.makedirs(RUN, exist_ok=True)
    json.dump(jobs, open(JOBS, "w"), indent=1)
    for j in jobs:
        print(os.path.basename(j["out"]), [(s["who"], [round(v) for v in s["box"]]) for s in j["steps"]])


def crop_mask(im, box):
    """머리 상자 중심 정사각 크롭(경계 밖은 가장자리 색 복제 대신 흰 종이색) + 타원 마스크 → (크롭 768, 마스크 768, 크롭 좌상단·한 변)."""
    x0, y0, x1, y1 = box
    side = int(round(max(x1 - x0, y1 - y0) * params.FACE_AB_CROP_SCALE))
    l, t = int(round((x0 + x1) / 2 - side / 2)), int(round((y0 + y1) / 2 - side / 2))
    canvas = Image.new("RGB", (side, side), (245, 235, 215))
    canvas.paste(im, (-l, -t))
    k = 768 / side
    m = Image.new("L", (768, 768), 0)
    cx, cy = ((x0 + x1) / 2 - l) * k, ((y0 + y1) / 2 - t) * k
    rw, rh = (x1 - x0) * k / 2 * params.FACE_AB_MASK_GROW, (y1 - y0) * k / 2 * params.FACE_AB_MASK_GROW
    ImageDraw.Draw(m).ellipse([cx - rw, cy - rh, cx + rw, cy + rh], fill=255)
    m = m.filter(ImageFilter.GaussianBlur(768 * params.FACE_AB_MASK_FEATHER * 0.25))
    return canvas.resize((768, 768), Image.LANCZOS), m, (l, t, side)


def worker(mode):
    import torch
    torch.set_grad_enabled(False)
    from diffusers import ZImagePipeline
    jobs = json.load(open(JOBS))
    flat = [s for j in jobs for s in j["steps"]]
    emb_path = JOBS + ".emb.pt"
    if mode == "enc":
        pipe = ZImagePipeline.from_pretrained(BASE, transformer=None, torch_dtype=torch.bfloat16).to("mps")
        torch.save([[t.cpu() for t in pipe.encode_prompt(s["prompt"], device="mps", do_classifier_free_guidance=False)[0]] for s in flat], emb_path)
        return
    from diffusers import GGUFQuantizationConfig, ZImageInpaintPipeline, ZImageTransformer2DModel
    from diffusers.models.model_loading_utils import load_gguf_checkpoint
    from huggingface_hub import hf_hub_download
    sd = load_gguf_checkpoint(hf_hub_download(GGUF, "z_image_turbo-Q8_0.gguf"))
    for k in ("cap_pad_token", "x_pad_token"):    # ZIMAGE.md: GGUF 로드 우회 2줄
        sd[k] = sd[k].reshape(1, -1)
    tr = ZImageTransformer2DModel.from_single_file(sd, quantization_config=GGUFQuantizationConfig(compute_dtype=torch.bfloat16),
                                                   config=BASE, subfolder="transformer", torch_dtype=torch.bfloat16)
    pipe = ZImageInpaintPipeline.from_pretrained(BASE, transformer=tr, text_encoder=None, tokenizer=None, torch_dtype=torch.bfloat16).to("mps")
    pipe.set_progress_bar_config(disable=True)
    embs = iter(torch.load(emb_path))
    loaded = None
    for j in jobs:
        im = Image.open(j["base"]).convert("RGB")
        for s in j["steps"]:
            e = [x.to("mps", torch.bfloat16) for x in next(embs)]
            if loaded != s["who"]:
                if loaded:
                    pipe.unload_lora_weights()
                pipe.load_lora_weights(LORA.format(who=s["who"]))
                loaded = s["who"]
            crop, mask, (l, t, side) = crop_mask(im, s["box"])
            new = pipe(prompt_embeds=e, image=crop, mask_image=mask, strength=params.FACE_AB_INPAINT_STRENGTH, height=768, width=768,
                       num_inference_steps=9, guidance_scale=0.0, generator=torch.Generator("mps").manual_seed(j["seed"])).images[0]
            new = new.resize((side, side), Image.LANCZOS)
            m = mask.resize((side, side), Image.LANCZOS)
            layer = Image.new("RGB", im.size)
            layer.paste(new, (l, t))
            mm = Image.new("L", im.size, 0)
            mm.paste(m, (l, t))
            im = Image.composite(layer, im, mm)    # 마스크 안쪽만 새 얼굴 — 크롭 밖·마스크 밖은 원본 그대로
        im.save(j["out"])
        print("저장", j["out"], flush=True)


if __name__ == "__main__":
    {"plan": plan}.get(sys.argv[1], lambda: worker(sys.argv[1]))()
