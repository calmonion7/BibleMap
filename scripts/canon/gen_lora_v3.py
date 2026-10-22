#!/usr/bin/env python3
"""인물 LoRA v3(2026-10-22, notes/FACE-LORA-V3.md) — 각도 정본으로 다각도·원경 시트 → 학습 → 기브아 창 C·V2·V3 비교.
  python3 gen_lora_v3.py body         # 시트 전신(klein 4B, 참조 = 정면 정본 + 3/4 각도 정본) 인물 × 자세 4 × 시드 2
  python3 gen_lora_v3.py sheet        # 초상 13 + 전신 8 + 원경 4 → ~/.local/biblemap-imggen/lora-sheet-v3/<id>/NN.png+txt, 학습 설정 train/<id>-v3.json
  python3 gen_lora_v3.py train        # mflux-train 차례로(동시 금지) → lora/<id>-v3.safetensors
  ~/.local/biblemap-imggen/.venv314/bin/python gen_lora_v3.py scene   # 기브아 C·V2·V3 × 8시드(gen_lora_scene 경로 재사용)"""
import glob, json, os, shutil, subprocess, sys, zipfile

from PIL import Image, ImageOps

import params

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.expanduser("~/.local/biblemap-imggen")
VIEWS = os.path.join(ROOT, "face-angles", "views")
BODY = os.path.join(ROOT, "lora-v3-body")
SHEET = os.path.join(ROOT, "lora-sheet-v3")
TRAIN = os.path.join(ROOT, "train")
SCENE_OUT = os.path.join(ROOT, "lora-v3-scene")
MFLUX = os.path.join(ROOT, ".venv-mflux", "bin")
SCENE = "authored-saul-gibeah-spear"


def body():
    from gen_face_angles import klein
    for who in params.LORA_V3_WHO:
        refs = [os.path.join(HERE, "frozen", f"{who}.png"), os.path.join(VIEWS, f"pick-{who}.png")]
        for pose, (text, (w, h)) in params.LORA_V3_BODY.items():
            prompt = ("Images 1 and 2 show the same man from the front and in three-quarter view. Draw the very same man — exactly the same face, "
                      f"hair, beard, age and build — {text}. Plain clothes of an ancient Israelite, soft colored-pencil storybook style, natural adult proportions.")
            for seed in params.LORA_V3_BODY_SEEDS:
                klein(refs, prompt, seed, os.path.join(BODY, f"{who}-{pose}-s{seed}.png"), w, h)


def far(src, frac):
    """전신을 1216×640 빈 바탕(가장자리 평균색)에 화면 높이 frac 크기로 놓음 — 원경 작은 인물."""
    im = Image.open(src).convert("RGB")
    a = im.resize((1, 1), Image.LANCZOS).getpixel((0, 0))
    edge = im.crop((0, 0, im.width, 8)).resize((1, 1), Image.LANCZOS).getpixel((0, 0))
    k = 640 * frac / im.height
    small = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
    c = Image.new("RGB", (1216, 640), edge if edge else a)
    c.paste(small, (round(1216 * 0.55), 640 - small.height - 40))
    return c


def sheet():
    trig = params.LORA_SHEET_TRIGGER
    for who in params.LORA_V3_WHO:
        d = os.path.join(SHEET, who)
        shutil.rmtree(d, ignore_errors=True)
        os.makedirs(d)
        items = [(Image.open(os.path.join(HERE, "frozen", f"{who}.png")), "close-up head portrait, facing forward, plain cream background")]
        for view, text in (("three-quarter", "three-quarter view"), ("profile", "side profile view")):
            for p in sorted(glob.glob(os.path.join(VIEWS, f"{who}-{view}-s*.png"))):
                im = Image.open(p)
                items.append((im, f"close-up head portrait, {text}, plain cream background"))
                items.append((ImageOps.mirror(im), f"close-up head portrait, {text}, plain cream background"))
        for pose, (text, _) in params.LORA_V3_BODY.items():
            for seed in params.LORA_V3_BODY_SEEDS:
                items.append((Image.open(os.path.join(BODY, f"{who}-{pose}-s{seed}.png")), text))
        for pose, frac in params.LORA_V3_FAR.items():
            for seed in params.LORA_V3_BODY_SEEDS:
                items.append((far(os.path.join(BODY, f"{who}-{pose}-s{seed}.png"), frac),
                              "small distant full-body figure in a wide empty scene, " + params.LORA_V3_BODY[pose][0].split(", ", 1)[1]))
        for i, (im, cap) in enumerate(items, 1):
            im.convert("RGB").save(os.path.join(d, f"{i:02d}.png"))
            open(os.path.join(d, f"{i:02d}.txt"), "w").write(f"{trig[who]}, a man, {cap}")
        cfg = json.load(open(os.path.join(TRAIN, f"{who}-v2.json")))
        cfg["data"] = d
        cfg["checkpoint"]["output_path"] = os.path.join(TRAIN, f"{who}-v3")
        cfg["training_loop"]["num_epochs"] = -(-params.LORA_V3_STEPS // len(items))
        json.dump(cfg, open(os.path.join(TRAIN, f"{who}-v3.json"), "w"), indent=1)
        print(f"[LoraV3] {who} 시트 {len(items)}장 · {cfg['training_loop']['num_epochs']}에폭", flush=True)


def train():
    for who in params.LORA_V3_WHO:
        out = os.path.join(ROOT, "lora", f"{who}-v3.safetensors")
        if os.path.exists(out):
            continue
        cfg = os.path.join(TRAIN, f"{who}-v3.json")
        with open(os.path.join(TRAIN, f"{who}-v3.log"), "w") as log:
            subprocess.run(["/usr/bin/time", "-l", os.path.join(MFLUX, "mflux-train"), "--config", cfg], stdout=log, stderr=subprocess.STDOUT, check=True)
        z = os.path.join(TRAIN, f"{who}-v3", "checkpoints", f"{params.LORA_V3_STEPS:07d}_checkpoint.zip")
        with zipfile.ZipFile(z) as zf, open(out, "wb") as f:   # v2와 같음: 300스텝 어댑터만 꺼냄
            f.write(zf.read(f"{params.LORA_V3_STEPS:07d}_adapter.safetensors"))
        print(f"[LoraV3] {who} 학습 끝 → {out}", flush=True)


ARMS = {"C": None, "V2": "v2", "V3": "v3"}
JOBS = os.path.join(SCENE_OUT, "_jobs.json")


def scene_prompt(loras):
    """경로 문구(route_prompt — 기브아는 판 경로라 plate_whole_prompt, 368 바탕과 같은 문구)에서 LoRA 인물의 cast 서술 앞에만 트리거 낱말."""
    import derive_scene as ds
    spec = ds.load(SCENE)
    p = ds.route_prompt(spec)
    for f in spec["figures"]:
        if f["cast"] in loras:
            d = ds.cast_describe(ds._cast_in_scene(f))
            assert p.count(d) == 1, (f["cast"], p.count(d))
            p = p.replace(d, f"{params.LORA_SHEET_TRIGGER[f['cast']]}, {d}")
    return p


def scene_plan():
    whos = list(params.LORA_V3_WHO)
    js = [{"arm": arm, "ver": ver, "seed": s, "prompt": scene_prompt(whos if ver else []),
           "out": os.path.join(SCENE_OUT, f"{arm}-s{s}.png")} for arm, ver in ARMS.items() for s in params.LORA_V3_SCENE_SEEDS]
    js = [j for j in js if not os.path.exists(j["out"])]
    os.makedirs(SCENE_OUT, exist_ok=True)
    json.dump(js, open(JOBS, "w"), ensure_ascii=False, indent=1)
    print(f"[LoraV3] 장면 작업 {len(js)}장", flush=True)
    return js


def scene_worker(mode):
    """gen_lora_scene.worker와 같은 경로 — 어댑터 이름에 판(v2/v3)을 붙이고, C(LoRA 없음)를 먼저 그린다."""
    import time
    import torch
    torch.set_grad_enabled(False)
    from diffusers import ZImagePipeline
    sys.path.insert(0, os.path.join(HERE, "batch"))
    import run_scene as rs
    jobs = json.load(open(JOBS))
    emb = JOBS + ".emb.pt"
    if mode == "enc":
        pipe = ZImagePipeline.from_pretrained(rs.ZI_BASE, transformer=None, torch_dtype=torch.bfloat16).to("mps")
        torch.save([[x.cpu() for x in pipe.encode_prompt(j["prompt"], device="mps", do_classifier_free_guidance=False)[0]]
                    for j in jobs], emb)
        return
    from diffusers import GGUFQuantizationConfig, ZImageTransformer2DModel
    from diffusers.models.model_loading_utils import load_gguf_checkpoint
    from huggingface_hub import hf_hub_download
    sd = load_gguf_checkpoint(hf_hub_download(rs.ZI_GGUF, "z_image_turbo-Q8_0.gguf"))
    for k in ("cap_pad_token", "x_pad_token"):     # ZIMAGE.md: GGUF 로드 우회 2줄
        sd[k] = sd[k].reshape(1, -1)
    tr = ZImageTransformer2DModel.from_single_file(sd, quantization_config=GGUFQuantizationConfig(compute_dtype=torch.bfloat16),
                                                   config=rs.ZI_BASE, subfolder="transformer", torch_dtype=torch.bfloat16)
    pipe = ZImagePipeline.from_pretrained(rs.ZI_BASE, transformer=tr, text_encoder=None, tokenizer=None,
                                          torch_dtype=torch.bfloat16).to("mps")
    pipe.set_progress_bar_config(disable=True)
    loaded, log = set(), []
    for j, e in zip(jobs, torch.load(emb)):
        names = [f"{w}-{j['ver']}" for w in params.LORA_V3_WHO] if j["ver"] else []
        for n in names:
            if n not in loaded:
                pipe.load_lora_weights(os.path.join(ROOT, "lora", f"{n}.safetensors"), adapter_name=n)
                loaded.add(n)
        if names:
            pipe.set_adapters(names, adapter_weights=[params.LORA_SCENE_SCALE] * len(names))
        elif loaded:
            pipe.disable_lora()
        t = time.time()
        pipe(prompt_embeds=[x.to("mps", torch.bfloat16) for x in e], width=1216, height=640, num_inference_steps=9,
             guidance_scale=0.0, generator=torch.Generator("mps").manual_seed(j["seed"])).images[0].save(j["out"])
        log.append({"out": j["out"], "secs": round(time.time() - t, 1), "active": pipe.get_active_adapters() if loaded else []})
        print(f"  [LoraV3] {j['arm']} s{j['seed']} {log[-1]['secs']}s {log[-1]['active']}", flush=True)
        json.dump(log, open(JOBS + ".log.json", "w"), ensure_ascii=False)


def scene():
    if scene_plan():
        for m in ("enc", "gen"):
            subprocess.run([sys.executable, os.path.abspath(__file__), "scene-" + m], check=True)


if __name__ == "__main__":
    a = sys.argv[1]
    scene_worker(a[6:]) if a.startswith("scene-") else {"body": body, "sheet": sheet, "train": train, "scene": scene}[a]()
