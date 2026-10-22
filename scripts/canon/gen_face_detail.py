#!/usr/bin/env python3
"""얼굴 보정(task 393) — 기브아 C·V2·V3 24장의 머리를 고해상도로 다시 그려 얼굴 판정 화면에 쓴다(사람 메모 「화질이 안좋음」).
  $VENV gen_face_detail.py trial   # 3머리 × FACE_DETAIL_TRIAL 세기 → face-detail/trial/ (세기 고르기)
  $VENV gen_face_detail.py all     # 48머리 + 비교 기준 머리 2 → face-detail/<갈래>-s<시드>-<인물>.png
머리 둘레 정사각(머리 상자 긴 변 × FACE_DETAIL_MARGIN, 그림 안으로 밀어 넣음)을 FACE_DETAIL_SIZE로 키워 img2img.
문구 = 공용 화풍 머리 + 「head and shoulders close-up of」 + 장면 명세의 cast 서술(LoRA 갈래는 트리거 낱말 앞에).
LoRA는 그 머리 인물의 어댑터 하나만(C·기준 머리는 LoRA 없음). 생성 프로세스는 한 번에 하나, 인코딩/생성은 따로(notes/ZIMAGE.md)."""
import json, os, subprocess, sys, time

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import params  # noqa: E402

ROOT = os.path.expanduser("~/.local/biblemap-imggen")
OUT = os.path.join(ROOT, "face-detail")
SCENE_OUT = os.path.join(ROOT, "lora-v3-scene")
HEADS = os.path.join(HERE, "samples", "face-lora-v3", "heads.json")
JOBS = os.path.join(OUT, "jobs.json")
ARMS = {"C": None, "V2": "v2", "V3": "v3"}
GIBEAH = "authored-saul-gibeah-spear"
# 비교 기준 머리(make_face_judge_v2.OTHER와 같은 그림)
REFS = {"saul": ("whole-fix", "authored-saul-gilgal-amalek", 11, "saul", "base/s11.png"),
        "david": ("whole-wide", "authored-david-gibeah-harp", 11, "david-boy", "edit/s11.png")}


def region(box, W, H):
    """머리 상자 [x0,y0,x1,y1] → 둘레 정사각(그림 안)."""
    s = min(round(max(box[2] - box[0], box[3] - box[1]) * params.FACE_DETAIL_MARGIN), W, H)
    cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
    x0 = min(max(0, round(cx - s / 2)), W - s)
    y0 = min(max(0, round(cy - s / 2)), H - s)
    return [x0, y0, x0 + s, y0 + s]


def prompt(sid, cast, ver, who):
    import derive_scene as ds
    f = next(f for f in ds.load(sid)["figures"] if f["cast"] == cast)
    d = ds.cast_describe(ds._cast_in_scene(f))
    trig = f"{params.LORA_SHEET_TRIGGER[who]}, " if ver else ""
    return f"{ds.ST} head and shoulders close-up of {trig}{d}."


def plan(trial=False):
    os.makedirs(os.path.join(OUT, "src"), exist_ok=True)
    heads = json.load(open(HEADS))
    jobs = []

    def add(key, img, box, sid, cast, ver, who, seed, strengths, out_dir):
        im = Image.open(img).convert("RGB")
        r = region(box, *im.size)
        src = os.path.join(OUT, "src", f"{key}.png")
        im.crop(r).resize((params.FACE_DETAIL_SIZE,) * 2, Image.LANCZOS).save(src)
        for st in strengths:
            jobs.append({"key": key, "src": src, "region": r, "prompt": prompt(sid, cast, ver, who), "ver": ver, "who": who,
                         "seed": seed, "strength": st, "out": os.path.join(out_dir, f"{key}{'-' + str(st) if trial else ''}.png")})

    if trial:
        d = os.path.join(OUT, "trial")
        os.makedirs(d, exist_ok=True)
        for arm, s, who in (("C", 42, "saul"), ("V3", 42, "saul"), ("V3", 23, "david")):
            add(f"{arm}-s{s}-{who}", os.path.join(SCENE_OUT, f"{arm}-s{s}.png"), heads[f"{arm}-s{s}"][who], GIBEAH, who, ARMS[arm], who, s,
                params.FACE_DETAIL_TRIAL, d)
        return jobs
    for arm, ver in ARMS.items():
        for s in params.LORA_V3_SCENE_SEEDS:
            for who, box in heads[f"{arm}-s{s}"].items():
                add(f"{arm}-s{s}-{who}", os.path.join(SCENE_OUT, f"{arm}-s{s}.png"), box, GIBEAH, who, ver, who, s,
                    (params.FACE_DETAIL_STRENGTH,), OUT)
    for who, (d, sid, seed, cast, rel) in REFS.items():
        m = json.load(open(os.path.join(HERE, "samples", d, "metrics.json")))
        box = next(x["boxes"][cast]["head"] for x in m["scenes"][sid]["seeds"] if str(x["seed"]) == str(seed))
        add(f"ref-{who}", os.path.join(ROOT, d, sid, rel), box, sid, cast, None, who, seed, (params.FACE_DETAIL_STRENGTH,), OUT)
    return [j for j in jobs if not os.path.exists(j["out"])]


def worker(mode):
    import torch
    torch.set_grad_enabled(False)
    sys.path.insert(0, os.path.join(HERE, "batch"))
    import run_scene as rs
    jobs = json.load(open(JOBS))
    emb = JOBS + ".emb.pt"
    if mode == "enc":
        from diffusers import ZImagePipeline
        pipe = ZImagePipeline.from_pretrained(rs.ZI_BASE, transformer=None, torch_dtype=torch.bfloat16).to("mps")
        torch.save([[x.cpu() for x in pipe.encode_prompt(j["prompt"], device="mps", do_classifier_free_guidance=False)[0]]
                    for j in jobs], emb)
        return
    from diffusers import GGUFQuantizationConfig, ZImageImg2ImgPipeline, ZImageTransformer2DModel
    from diffusers.models.model_loading_utils import load_gguf_checkpoint
    from huggingface_hub import hf_hub_download
    sd = load_gguf_checkpoint(hf_hub_download(rs.ZI_GGUF, "z_image_turbo-Q8_0.gguf"))
    for k in ("cap_pad_token", "x_pad_token"):     # ZIMAGE.md: GGUF 로드 우회 2줄
        sd[k] = sd[k].reshape(1, -1)
    tr = ZImageTransformer2DModel.from_single_file(sd, quantization_config=GGUFQuantizationConfig(compute_dtype=torch.bfloat16),
                                                   config=rs.ZI_BASE, subfolder="transformer", torch_dtype=torch.bfloat16)
    pipe = ZImageImg2ImgPipeline.from_pretrained(rs.ZI_BASE, transformer=tr, text_encoder=None, tokenizer=None,
                                                 torch_dtype=torch.bfloat16).to("mps")
    pipe.set_progress_bar_config(disable=True)
    loaded, log = set(), []
    for j, e in zip(jobs, torch.load(emb)):
        name = f"{j['who']}-{j['ver']}" if j["ver"] else None
        if name and name not in loaded:
            pipe.load_lora_weights(os.path.join(ROOT, "lora", f"{name}.safetensors"), adapter_name=name)
            loaded.add(name)
        if name:
            pipe.set_adapters([name], adapter_weights=[params.LORA_SCENE_SCALE])
        elif loaded:
            pipe.disable_lora()
        t = time.time()
        n = params.FACE_DETAIL_SIZE
        pipe(prompt_embeds=[x.to("mps", torch.bfloat16) for x in e], image=Image.open(j["src"]).convert("RGB"), strength=j["strength"],
             width=n, height=n, num_inference_steps=9, guidance_scale=0.0,
             generator=torch.Generator("mps").manual_seed(j["seed"])).images[0].save(j["out"])
        log.append({"out": j["out"], "secs": round(time.time() - t, 1), "active": pipe.get_active_adapters() if loaded else []})
        print(f"  [FaceDetail] {j['key']} {j['strength']} {log[-1]['secs']}s {log[-1]['active']}", flush=True)
        json.dump(log, open(JOBS + ".log.json", "w"), ensure_ascii=False)


def run(trial):
    jobs = sorted(plan(trial), key=lambda j: j["ver"] is not None)   # LoRA 없는 작업 먼저 — 한 번 불러온 어댑터는 disable_lora 뒤에도 활성 이름이 남는다
    json.dump(jobs, open(JOBS, "w"), ensure_ascii=False, indent=1)
    print(f"[FaceDetail] {len(jobs)}장", flush=True)
    if jobs:
        for m in ("enc", "gen"):
            subprocess.run([sys.executable, os.path.abspath(__file__), "worker-" + m], check=True)


if __name__ == "__main__":
    a = sys.argv[1]
    worker(a[7:]) if a.startswith("worker-") else run(a == "trial")
