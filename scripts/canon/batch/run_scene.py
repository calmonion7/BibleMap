#!/usr/bin/env python3
"""무인 배치 실행기 — 장면 id → 층(배경판 1 + 인물 판 N) 생성 → AI 판정 → 최고 선택 → 인물 오리기.

  VENV=~/.local/biblemap-imggen/.venv314/bin/python
  $VENV run_scene.py <장면id> [--engine zimage|sdxl] [--n 4] [--out <산출 루트>] [--smoke]

프롬프트는 장면 명세에서 derive_scene으로 파생한다(손으로 쓰지 않음). 산출(<out>/<장면>/):
  layers/bg.png · layers/fig-<인물키>.png(알파) · cand/<층>-s<시드>.png · judge.json
산출물 단위로 건너뛴다 — 이미 있는 층·후보·판정은 다시 하지 않고 이어 돈다.
후보 N → judge_vlm 판정 → 통과 중 평균점수 최고 선택 → 전부 탈락이면 시드를 바꿔 최대 2회 재생성
(그래도 없으면 최고점 후보를 pass:false로 표시해 쓴다). 생성 프로세스는 머신에서 한 번에 하나 — 시작 전 pgrep 확인.
Z-Image는 메모리 때문에 인코딩/생성을 별도 프로세스로 쪼갠다(notes/ZIMAGE.md) — 같은 파일의 `--worker`.
"""
import argparse, json, os, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor

import paper_margin

HERE = os.path.dirname(os.path.abspath(__file__))
CANON = os.path.dirname(HERE)
ROOT = os.path.abspath(os.path.join(CANON, "..", ".."))
OUT_DEFAULT = os.path.join(ROOT, ".forge", "reports", "scene-batch-pilot")
VISION_PY = os.path.expanduser("~/.local/biblemap-manimgx/.venv/bin/python")   # pyobjc(Vision)가 있는 venv
SEEDS = [11, 42, 7, 23]
RETRIES = 2
PLATE_TAIL = ", full body from head to feet, single figure, plain white background."
PLATE_NEG = ("landscape, hills, sky, ground, scenery, shadow, frame, border, framed, picture frame, vignette, "
             "paper edge, multiple people, cropped, cut off")
SDXL_BG, SDXL_FIG = (1216, 640), (832, 1216)   # params.SCENE_SIZE / SAMPLE_SIZE
ZI_BG = (1216, 640)   # r1: 2432x1280은 후보 ~2/3에서 가로줄무늬·패치 질감 붕괴(시드 42·7·11 대조, CANVAS.md) — 1216x640은 같은 시드에서 깨끗
ZI_GGUF = "leejet/Z-Image-Turbo-GGUF"
ZI_BASE = "Tongyi-MAI/Z-Image-Turbo"
ZI_CN = "alibaba-pai/Z-Image-Turbo-Fun-Controlnet-Union-2.1"
ZI_CN_LITE = "Z-Image-Turbo-Fun-Controlnet-Union-2.1-lite-2602-8steps.safetensors"


# --- Z-Image 워커 (별도 프로세스) ------------------------------------------------
def worker(mode, jobs_path):
    import torch
    torch.set_grad_enabled(False)   # 인코딩에 그래프가 쌓여 MPS 천장(42GiB)을 넘은 적이 있다(task#346)
    from diffusers import ZImagePipeline
    jobs = json.load(open(jobs_path))
    emb_path = jobs_path + ".emb.pt"
    if mode == "enc":
        pipe = ZImagePipeline.from_pretrained(ZI_BASE, transformer=None, torch_dtype=torch.bfloat16).to("mps")
        embs = [pipe.encode_prompt(j["prompt"], device="mps", do_classifier_free_guidance=False)[0] for j in jobs]
        torch.save([[t.cpu() for t in e] for e in embs], emb_path)
        return
    from diffusers import GGUFQuantizationConfig, ZImageTransformer2DModel
    from diffusers.models.model_loading_utils import load_gguf_checkpoint
    from huggingface_hub import hf_hub_download
    sd = load_gguf_checkpoint(hf_hub_download(ZI_GGUF, "z_image_turbo-Q8_0.gguf"))
    for k in ("cap_pad_token", "x_pad_token"):     # ZIMAGE.md: GGUF 로드 우회 2줄
        sd[k] = sd[k].reshape(1, -1)
    tr = ZImageTransformer2DModel.from_single_file(
        sd, quantization_config=GGUFQuantizationConfig(compute_dtype=torch.bfloat16),
        config=ZI_BASE, subfolder="transformer", torch_dtype=torch.bfloat16)
    if mode in ("gencn", "i2icn"):   # task#388 — CN 2602 lite + 구도 가이드, 앞 cn_steps 스텝만 CN(그 뒤는 CN 출력 없음)
        from diffusers import ZImageControlNetModel, ZImageControlNetPipeline
        from safetensors.torch import load_file
        cn = ZImageControlNetModel(control_layers_places=[0, 10, 20], control_refiner_layers_places=[0, 1], control_in_dim=33,
                                   add_control_noise_refiner="control_noise_refiner")   # VideoX-Fun lite yaml(ZIMAGE §2 정정)
        miss, extra = cn.load_state_dict(load_file(hf_hub_download(ZI_CN, ZI_CN_LITE)), strict=False)
        assert not miss and not extra, (miss, extra)
        cn = ZImageControlNetModel.from_transformer(cn.to(torch.bfloat16), tr)
        pipe = ZImageControlNetPipeline.from_pretrained(ZI_BASE, transformer=tr, controlnet=cn, text_encoder=None, tokenizer=None,
                                                        torch_dtype=torch.bfloat16).to("mps")
        fwd, calls, cur = pipe.controlnet.forward, [0], [0]

        alt, cur2 = [None], [0]   # task 404 h1 — 둘째 가이드(control2): 앞 cur 스텝 뒤 cur2 스텝은 그 latent로 바꿔 넣는다(스텝별 가이드)

        def first_k(*a, **k):   # 파이프라인에 control_guidance_end가 없다 — 앞 cur 스텝 뒤엔 None(트랜스포머가 CN 없이 돈다)
            calls[0] += 1
            if calls[0] <= cur[0]:
                return fwd(*a, **k)
            if alt[0] is not None and calls[0] <= cur[0] + cur2[0]:
                a = list(a)
                a[3] = alt[0].repeat(a[3].shape[0] // alt[0].shape[0], 1, 1, 1, 1)
                return fwd(*a, **k)
            return None
        pipe.controlnet.forward = first_k
        import diffusers.pipelines.z_image.pipeline_z_image_controlnet as zcn

        def encode_control(img, w, h, gen):   # 파이프라인 4절(control_image 준비)과 같은 길 — 둘째 가이드를 미리 latent로
            ci = pipe.prepare_image(image=img, width=w, height=h, batch_size=1, num_images_per_prompt=1, device="mps", dtype=pipe.vae.dtype)
            ci = zcn.retrieve_latents(pipe.vae.encode(ci), generator=gen, sample_mode="argmax")
            ci = ((ci - pipe.vae.config.shift_factor) * pipe.vae.config.scaling_factor).unsqueeze(2)
            n = pipe.transformer.in_channels
            if n != pipe.controlnet.config.control_in_dim:
                ci = torch.cat([ci, torch.zeros(ci.shape[0], pipe.controlnet.config.control_in_dim - n, *ci.shape[2:]).to(ci.device, ci.dtype)], dim=1)
            return ci
        if mode == "i2icn":   # restyle-try r2 — 두 번째 단계 img2img에도 약한 CN: CN 파이프라인에 잘린 일정 + 잡음 섞은 시작 latent
            import diffusers.pipelines.z_image.pipeline_z_image_controlnet as zc
            from diffusers import ZImageImg2ImgPipeline
            i2i = ZImageImg2ImgPipeline(scheduler=pipe.scheduler, vae=pipe.vae, text_encoder=None, tokenizer=None, transformer=tr)
            orig, strength = zc.retrieve_timesteps, [None]

            def cut(scheduler, n, device, sigmas=None, **kw):   # ZImageImg2ImgPipeline.get_timesteps와 같은 자름
                ts, n = orig(scheduler, n, device, sigmas=sigmas, **kw)
                t0 = int(max(n - min(n * strength[0], n), 0))
                scheduler.set_begin_index(t0)
                return ts[t0:], n - t0
            zc.retrieve_timesteps = cut

            def start_latents(src, j, gen):
                h, w = 2 * (j["h"] // 16), 2 * (j["w"] // 16)
                mu = zc.calculate_shift((h // 2) * (w // 2), *(pipe.scheduler.config.get(k, d) for k, d in
                                        (("base_image_seq_len", 256), ("max_image_seq_len", 4096), ("base_shift", 0.5), ("max_shift", 1.15))))
                ts, _ = cut(pipe.scheduler, 9, "mps", sigmas=zc.get_default_z_image_sigmas(9), mu=mu)
                im = i2i.image_processor.preprocess(src, height=j["h"], width=j["w"])
                return i2i.prepare_latents(im, ts[:1], 1, tr.config.in_channels, j["h"], j["w"], torch.bfloat16, "mps", gen)
    elif mode == "i2i":   # restyle-try — CN 그림(src)을 CN 없이 strength만큼 다시 그림(두 단계)
        from diffusers import ZImageImg2ImgPipeline
        pipe = ZImageImg2ImgPipeline.from_pretrained(ZI_BASE, transformer=tr, text_encoder=None, tokenizer=None,
                                                     torch_dtype=torch.bfloat16).to("mps")
    else:
        pipe = ZImagePipeline.from_pretrained(ZI_BASE, transformer=tr, text_encoder=None, tokenizer=None,
                                              torch_dtype=torch.bfloat16).to("mps")
    pipe.set_progress_bar_config(disable=True)
    embs = torch.load(emb_path)
    secs, peak = [], 0.0
    for j, e in zip(jobs, embs):
        t = time.time()
        kw = {}
        gen = torch.Generator("mps").manual_seed(j["seed"])
        if mode in ("gencn", "i2icn"):
            from PIL import Image
            calls[0], cur[0] = 0, j["cn_steps"]
            alt[0], cur2[0] = None, 0
            if j.get("control2"):
                alt[0], cur2[0] = encode_control(Image.open(j["control2"]).convert("RGB"), j["w"], j["h"], gen), j["cn_steps2"]
            kw = {"control_image": Image.open(j["control"]).convert("RGB"), "controlnet_conditioning_scale": j["scale"]}
            if mode == "i2icn":
                strength[0] = j["strength"]
                kw["latents"] = start_latents(Image.open(j["src"]).convert("RGB"), j, gen)
        elif mode == "i2i":
            from PIL import Image
            kw = {"image": Image.open(j["src"]).convert("RGB"), "strength": j["strength"]}
        img = pipe(prompt_embeds=[x.to("mps", torch.bfloat16) for x in e], width=j["w"], height=j["h"],
                   num_inference_steps=9, guidance_scale=0.0,
                   generator=gen, **kw).images[0]
        paper_margin.trim(img).save(j["out"])   # 규칙 generate.trim-paper-margin — 둘레 미색 종이 띠를 잘라 원래 크기로(task 422)
        secs.append(round(time.time() - t, 1))
        peak = max(peak, torch.mps.driver_allocated_memory() / 2 ** 30)
        print(f"  [zimage] {os.path.basename(j['out'])} {secs[-1]}s", flush=True)
    json.dump(secs, open(jobs_path + ".secs.json", "w"))
    json.dump(round(peak, 2), open(jobs_path + ".peak.json", "w"))


_SDXL = {}


def gen_sdxl(jobs):
    import torch
    from diffusers import StableDiffusionXLPipeline
    sys.path.insert(0, CANON)
    import long_prompt as lp
    import params
    if "p" not in _SDXL:
        _SDXL["p"] = StableDiffusionXLPipeline.from_pretrained(
            params.SDXL_BASE, torch_dtype=torch.float16, variant="fp16", use_safetensors=True).to("mps")
        _SDXL["p"].set_progress_bar_config(disable=True)
    pipe, secs = _SDXL["p"], []
    for j in jobs:
        t = time.time()
        kw = lp.encode(pipe, j["prompt"], j["neg"], device="mps")
        pipe(**kw, width=j["w"], height=j["h"], num_inference_steps=params.STEPS, guidance_scale=params.GUIDANCE,
             generator=torch.Generator("mps").manual_seed(j["seed"])).images[0].save(j["out"])
        secs.append(round(time.time() - t, 1))
        print(f"  [sdxl] {os.path.basename(j['out'])} {secs[-1]}s", flush=True)
    return secs


def gen_zimage(jobs, tmp, gen="gen"):
    """gen="gencn"이면 job마다 control(가이드 png)·scale·cn_steps가 있어야 한다(task#388)."""
    jp = os.path.join(tmp, "_zjobs.json")
    json.dump(jobs, open(jp, "w"))
    for mode in ("enc", gen):   # 인코더와 트랜스포머를 같은 프로세스에 올리면 천장(~17GiB)을 넘는다
        subprocess.run([sys.executable, os.path.abspath(__file__), "--worker", mode, jp], check=True)
    return json.load(open(jp + ".secs.json"))


def generate(engine, jobs, tmp):
    return gen_sdxl(jobs) if engine == "sdxl" else gen_zimage(jobs, tmp)


# --- 프롬프트 파생 ----------------------------------------------------------------
def layer_specs(scene, engine="zimage"):
    """→ [(층 키, 판정 layer, 산출 파일명, 프롬프트, 부정어, 크기)] — bg 먼저, 인물은 명세 순서."""
    sys.path.insert(0, CANON)
    import derive_scene as ds
    st = ds.stages(ds.load(scene))
    bg = next(s for s in st if s["kind"] == "full")
    out = [("bg", "bg", "bg.png", bg["prompt"], bg["neg"], ZI_BG if engine == "zimage" else SDXL_BG)]
    for f in ds.load(scene)["figures"]:
        s = next(x for x in st if x["kind"] == "plate" and x["region"] == f["region"])
        out.append((f["cast"], f"figure:{f['cast']}", f"fig-{f['cast']}.png",
                    s["prompt"].rstrip(". ") + PLATE_TAIL, s["neg"] + ", " + PLATE_NEG, SDXL_FIG))
    return out


def mean(sc):
    return sum(sc.values()) / len(sc) if sc else 0.0


# --- 층 하나 ----------------------------------------------------------------------
def do_layer(scene, spec, a, root, jd):
    key, jlayer, _, prompt, neg, (w, h) = spec
    sys.path.insert(0, HERE)
    import judge_vlm
    rec = jd["layers"].setdefault(key, {"attempts": [], "regen": 0, "gen_sec": 0.0, "engine": a.engine})
    cand = os.path.join(root, "cand")
    for att in range(RETRIES + 1):
        seeds = [s + att * 1000 for s in SEEDS[:a.n]]
        todo = [s for s in seeds if not os.path.exists(os.path.join(cand, f"{key}-s{s}.png"))]
        if todo:
            jobs = [{"prompt": prompt, "neg": neg, "seed": s, "w": w, "h": h,
                     "out": os.path.join(cand, f"{key}-s{s}.png")} for s in todo]
            rec["gen_sec"] = round(rec["gen_sec"] + sum(generate(a.engine, jobs, cand)), 1)
        cs = [c for c in rec["attempts"] if c["attempt"] == att]
        new = [s for s in seeds if s not in {c["seed"] for c in cs}]
        if new:
            with ThreadPoolExecutor(4) as ex:
                res = list(ex.map(lambda s: judge_vlm.judge(os.path.join(cand, f"{key}-s{s}.png"), scene, jlayer), new))
            for s, r in zip(new, res):
                c = {"attempt": att, "seed": s, "file": f"cand/{key}-s{s}.png", **r}
                rec["attempts"].append(c)
                cs.append(c)
            json.dump(jd, open(os.path.join(root, "judge.json"), "w"), ensure_ascii=False, indent=1)
        ok = [c for c in cs if c["pass"]]
        if ok or att == RETRIES:
            best = max(ok or cs, key=lambda c: mean(c["scores"]))
            rec["selected"], rec["regen"], rec["pass"] = best["file"], att, bool(ok)
            return best
        print(f"  [{key}] 전부 탈락 → 시드 바꿔 재생성 {att + 1}/{RETRIES}", flush=True)


def finish(root, key, fname, best):
    os.makedirs(os.path.join(root, "layers"), exist_ok=True)
    src, dst = os.path.join(root, best["file"]), os.path.join(root, "layers", fname)
    if key == "bg":
        subprocess.run(["cp", src, dst], check=True)
        return None
    r = subprocess.run([VISION_PY, os.path.join(HERE, "fg_mask.py"), src, dst], capture_output=True, text=True, check=True)
    return float(r.stdout.strip().splitlines()[-1])


# --- 한 장 모드 (task 345) ---------------------------------------------------------
def whole_main(a):
    """장면 한 장 후보 N → judge v2(layer full) → 통과 중 최고 → final.png + judge.json. 층 분리 없음."""
    sys.path.insert(0, CANON)
    sys.path.insert(0, HERE)
    import derive_scene as ds
    import judge_vlm
    spec = ds.load(a.scene)
    prompt, neg = ds.whole_prompt(spec), ds.WHOLE_NEG
    w, h = map(int, a.size.split("x"))
    root = os.path.join(a.out, a.scene)
    cand = os.path.join(root, "cand")
    os.makedirs(cand, exist_ok=True)
    jp = os.path.join(root, "judge.json")
    jd = json.load(open(jp)) if os.path.exists(jp) else {"scene": a.scene, "mode": "whole", "attempts": [], "gen_sec": 0.0, "wall_sec": 0.0}
    jd["size"] = [w, h]
    t0 = time.time()
    for att in range(RETRIES + 1):
        seeds = [s + att * 1000 for s in SEEDS[:a.n]]
        fn = lambda s: os.path.join(cand, f"whole-{w}x{h}-s{s}.png")
        todo = [s for s in seeds if not os.path.exists(fn(s))]
        if todo:
            jobs = [{"prompt": prompt, "neg": neg, "seed": s, "w": w, "h": h, "out": fn(s)} for s in todo]
            jd["gen_sec"] = round(jd["gen_sec"] + sum(gen_zimage(jobs, cand)), 1)
        cs = [c for c in jd["attempts"] if c["attempt"] == att]
        new = [s for s in seeds if s not in {c["seed"] for c in cs}]
        if new:
            with ThreadPoolExecutor(4) as ex:
                res = list(ex.map(lambda s: judge_vlm.judge(fn(s), a.scene, "full"), new))
            for s, r in zip(new, res):
                c = {"attempt": att, "seed": s, "file": os.path.relpath(fn(s), root), **r}
                jd["attempts"].append(c)
                cs.append(c)
            json.dump(jd, open(jp, "w"), ensure_ascii=False, indent=1)
        ok = [c for c in cs if c["pass"]]
        if ok or att == RETRIES:
            best = max(ok or cs, key=lambda c: mean(c["scores"]))
            jd["selected"], jd["regen"], jd["pass"] = best["file"], att, bool(ok)
            subprocess.run(["cp", os.path.join(root, best["file"]), os.path.join(root, "final.png")], check=True)
            break
        print(f"  전부 탈락 → 시드 바꿔 재생성 {att + 1}/{RETRIES}", flush=True)
    jd["wall_sec"] = round(jd["wall_sec"] + time.time() - t0, 1)
    json.dump(jd, open(jp, "w"), ensure_ascii=False, indent=1)
    print(f"완료 pass={jd['pass']} 선택={jd['selected']} 재생성={jd['regen']} 벽시계={jd['wall_sec']}s -> {root}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scene", nargs="?")
    ap.add_argument("--engine", choices=("sdxl", "zimage"), default="zimage")
    ap.add_argument("--n", type=int, default=4)
    ap.add_argument("--out", default=OUT_DEFAULT)
    ap.add_argument("--mode", choices=("layers", "whole"), default="layers")
    ap.add_argument("--size", default="1216x640", help="whole 모드 캔버스 WxH")
    ap.add_argument("--smoke", action="store_true", help="배경판 후보 1장만 만들고(판정 없이) 끝낸다")
    ap.add_argument("--worker", nargs=2, metavar=("MODE", "JOBS"))
    a = ap.parse_args()
    if a.worker:
        return worker(*a.worker)
    if not a.scene:
        ap.error("장면 id 필요")
    busy = [l for l in subprocess.run(["pgrep", "-fl", "python"], capture_output=True, text=True).stdout.splitlines()
            if any(k in l for k in ("gen_", "run_scene", "try_prompt")) and l.split()[0] != str(os.getpid())]
    if busy:
        sys.exit("다른 생성 프로세스가 돌고 있다 — 중첩하면 20배 느려진다:\n" + "\n".join(busy))
    if a.mode == "whole":
        if a.smoke:  # 캔버스 시험: 한 장만, 판정 없이
            sys.path.insert(0, CANON)
            import derive_scene as ds
            w, h = map(int, a.size.split("x"))
            o = os.path.join(a.out, a.scene)
            os.makedirs(o, exist_ok=True)
            sec = gen_zimage([{"prompt": ds.whole_prompt(ds.load(a.scene)), "seed": SEEDS[0], "w": w, "h": h,
                               "out": os.path.join(o, f"canvas-test-{w}x{h}.png")}], o)
            print(f"캔버스 시험 {w}x{h} {sec[0]}s -> {o}")
            return
        return whole_main(a)
    specs = layer_specs(a.scene, a.engine)
    if a.smoke:
        _, _, _, prompt, neg, (w, h) = specs[0]
        os.makedirs(a.out, exist_ok=True)
        s = generate(a.engine, [{"prompt": prompt, "neg": neg, "seed": SEEDS[0], "w": w, "h": h,
                                 "out": os.path.join(a.out, f"bg-s{SEEDS[0]}.png")}], a.out)
        print(f"스모크 {a.engine} 배경판 1장 {s[0]}s -> {a.out}")
        return
    root = os.path.join(a.out, a.scene)
    os.makedirs(os.path.join(root, "cand"), exist_ok=True)
    jp = os.path.join(root, "judge.json")
    jd = json.load(open(jp)) if os.path.exists(jp) else {"scene": a.scene, "layers": {}}
    jd["engine"] = a.engine
    for spec in specs:
        key, _, fname = spec[:3]
        if os.path.exists(os.path.join(root, "layers", fname)):
            print(f"[{key}] 이미 있음 — 건너뜀")
            continue
        print(f"[{key}] 생성·판정", flush=True)
        t0 = time.time()
        best = do_layer(a.scene, spec, a, root, jd)
        tr = finish(root, key, fname, best)
        if tr is not None:
            jd["layers"][key]["transparent"] = round(tr, 3)
        jd["wall_sec"] = round(jd.get("wall_sec", 0) + time.time() - t0, 1)
        json.dump(jd, open(jp, "w"), ensure_ascii=False, indent=1)
    print(f"완료 -> {root}")


if __name__ == "__main__":
    main()
