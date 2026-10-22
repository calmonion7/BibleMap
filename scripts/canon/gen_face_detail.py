#!/usr/bin/env python3
"""얼굴 보정(task 393) — 기브아 C·V2·V3 24장의 머리를 고해상도로 다시 그려 얼굴 판정 화면에 쓴다(사람 메모 「화질이 안좋음」).
  $VENV gen_face_detail.py trial   # 3머리 × FACE_DETAIL_TRIAL 세기 → face-detail/trial/ (세기 고르기)
  $VENV gen_face_detail.py all     # 48머리 + 비교 기준 머리 2 → face-detail/<갈래>-s<시드>-<인물>.png
  $VENV gen_face_detail.py v3paste # task 395: C 장면 머리 16 × V3 보정 → face-detail-v3/heads, C 원본에 되붙여 → paste 8
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
V3_OUT = os.path.join(ROOT, "face-detail-v3")   # task 395
V3_LOG = os.path.join(HERE, "samples", "face-detail-v3", "log.json")
GIBEAH_393 = "12a25b1^"   # 393 C 그림을 그린 옛 기브아 명세(394 재저작 앞 — 다윗 cast가 성인 david)
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


def prompt(sid, cast, ver, who, figures=None):
    import derive_scene as ds
    f = next(f for f in figures or ds.load(sid)["figures"] if f["cast"] == cast)
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


def plan_v3():
    """task 395: C 장면(LoRA 없음) 머리 16개를 그 인물 V3 어댑터로 보정(notes/FACE-DETAIL-V3.md 고정 절)."""
    for d in ("src", "heads", "paste"):
        os.makedirs(os.path.join(V3_OUT, d), exist_ok=True)
    heads = json.load(open(HEADS))
    figs = json.loads(subprocess.check_output(["git", "show", f"{GIBEAH_393}:scripts/canon/scenes/{GIBEAH}.json"], cwd=HERE))["figures"]
    jobs = []
    for s in params.LORA_V3_SCENE_SEEDS:
        scene = os.path.join(SCENE_OUT, f"C-s{s}.png")
        im = Image.open(scene).convert("RGB")
        for who, box in sorted(heads[f"C-s{s}"].items()):
            key, r = f"C-s{s}-{who}", region(box, *im.size)
            src = os.path.join(V3_OUT, "src", f"{key}.png")
            im.crop(r).resize((params.FACE_DETAIL_SIZE,) * 2, Image.LANCZOS).save(src)
            jobs.append({"key": key, "src": src, "region": r, "box": box, "scene": scene, "prompt": prompt(GIBEAH, who, "v3", who, figs),
                         "ver": "v3", "who": who, "seed": s, "strength": params.FACE_DETAIL_STRENGTH,
                         "out": os.path.join(V3_OUT, "heads", f"{key}.png")})
    return jobs


def paste_v3(jobs):
    """보정 정사각을 원래 크기로 줄여 머리 타원(가장자리 흐림)만 C 원본 위에 합성. 색 맞춤 없이 타원 안 평균 색 차만 잰다."""
    from PIL import ImageDraw, ImageFilter, ImageStat
    out = []
    for scene in dict.fromkeys(j["scene"] for j in jobs):
        im, diff, js = Image.open(scene).convert("RGB"), {}, [j for j in jobs if j["scene"] == scene]
        for j in js:
            r, b = j["region"], j["box"]
            layer = im.copy()
            layer.paste(Image.open(j["out"]).convert("RGB").resize((r[2] - r[0],) * 2, Image.LANCZOS), tuple(r[:2]))
            cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
            hw, hh = (b[2] - b[0]) * params.FACE_DETAIL_V3_PASTE_GROW / 2, (b[3] - b[1]) * params.FACE_DETAIL_V3_PASTE_GROW / 2
            hard = Image.new("L", im.size, 0)
            ImageDraw.Draw(hard).ellipse([cx - hw, cy - hh, cx + hw, cy + hh], fill=255)
            diff[j["who"]] = [round(a - c, 1) for a, c in zip(ImageStat.Stat(layer, hard).mean, ImageStat.Stat(im, hard).mean)]
            soft = hard.filter(ImageFilter.GaussianBlur(max(b[2] - b[0], b[3] - b[1]) * params.FACE_DETAIL_V3_PASTE_FEATHER))
            im = Image.composite(layer, im, soft)
        p = os.path.join(V3_OUT, "paste", os.path.basename(scene))
        im.save(p)
        out.append({"kind": "paste", "seed": js[0]["seed"], "out": p, "color_diff": diff})
    return out


def run_v3():
    jobs = plan_v3()
    path = os.path.join(V3_OUT, "jobs.json")
    json.dump(jobs, open(path, "w"), ensure_ascii=False, indent=1)
    print(f"[FaceDetail] v3paste {len(jobs)}머리", flush=True)
    if not all(os.path.exists(j["out"]) for j in jobs):
        for m in ("enc", "gen"):
            subprocess.run([sys.executable, os.path.abspath(__file__), "worker-" + m, path], check=True)
    done = {x["out"]: x for x in json.load(open(path + ".log.json"))}
    log = [{"kind": "head", "cast": j["who"], "seed": j["seed"], "out": j["out"], "secs": done[j["out"]]["secs"],
            "active": done[j["out"]]["active"]} for j in jobs] + paste_v3(jobs)
    os.makedirs(os.path.dirname(V3_LOG), exist_ok=True)
    json.dump(log, open(V3_LOG, "w"), ensure_ascii=False, indent=1)
    print(f"[FaceDetail] 되붙임 {sum(x['kind'] == 'paste' for x in log)}장 → {V3_LOG}", flush=True)


def worker(mode, JOBS=JOBS):
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
    worker(a[7:], *sys.argv[2:]) if a.startswith("worker-") else run_v3() if a == "v3paste" else run(a == "trial")
