#!/usr/bin/env python3
"""task#357 S2/S3 — 인물 LoRA(v2)를 장면 전체 생성에 건다. L1 = 그 인물 LoRA 하나, L2 = 장면의 두 인물 LoRA 동시.

  VENV=~/.local/biblemap-imggen/.venv314/bin/python
  $VENV gen_lora_scene.py plan [--test]      # 작업표(L1 48 + L2 24, --test는 L1·L2 1장씩)를 쓴다
  $VENV gen_lora_scene.py enc|gen            # Z-Image 인코딩/생성을 프로세스로 쪼갠다(run_scene과 같음). 생성은 한 번에 하나
  $VENV gen_lora_scene.py all [--test]       # plan → enc → gen

문구는 353과 같은 `derive_scene.whole_prompt(spec)`에서 LoRA를 건 인물의 `cast_describe` 앞에 트리거 낱말만 붙인다.
경로는 batch/run_scene의 diffusers GGUF Q8 + `load_lora_weights(adapter_name=인물)`, 세기 params.LORA_SCENE_SCALE.
산출은 레포 밖 ~/.local/biblemap-imggen/lora-scene/<L1|L2>/<장면>/<인물|both>-s<시드>.png."""
import json, os, subprocess, sys, time

import params
import derive_scene as ds

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.expanduser("~/.local/biblemap-imggen/lora-scene")
JOBS = os.path.join(OUT, "_jobs.json")
LORA = os.path.expanduser("~/.local/biblemap-imggen/lora/{}-v2.safetensors")
W, H = 1216, 640   # 345 한 장 모드(run_scene.ZI_BG)


def prompt(sid, loras):
    """whole_prompt에서 LoRA 인물의 cast 서술 앞에만 트리거 낱말을 붙인다 — 353 문구와의 차이는 이것 하나."""
    spec = ds.load(sid)
    p = ds.whole_prompt(spec)
    for f in spec["figures"]:
        if f["cast"] in loras:
            d = ds.cast_describe(ds._cast_in_scene(f))
            assert p.count(d) == 1, (sid, f["cast"], p.count(d))
            p = p.replace(d, f"{params.LORA_SHEET_TRIGGER[f['cast']]}, {d}")
    return p


def plan(test=False):
    js = []
    for key, (sid, whos) in params.LORA_SCENE_SCENES.items():
        seeds = params.LORA_SCENE_SEEDS[:1] if test else params.LORA_SCENE_SEEDS
        for who in whos[:1] if test else whos:
            js += [{"cond": "L1", "scene": key, "loras": [who], "seed": s, "prompt": prompt(sid, [who]),
                    "out": os.path.join(OUT, "L1", key, f"{who}-s{s}.png")} for s in seeds]
        js += [{"cond": "L2", "scene": key, "loras": whos, "seed": s, "prompt": prompt(sid, whos),
                "out": os.path.join(OUT, "L2", key, f"both-s{s}.png")} for s in seeds]
        if test:
            break
    js = [j for j in js if not os.path.exists(j["out"])]
    js.sort(key=lambda j: (j["loras"], j["scene"], j["seed"]))   # 어댑터 갈아 끼우기를 줄인다
    for j in js:
        os.makedirs(os.path.dirname(j["out"]), exist_ok=True)
    os.makedirs(OUT, exist_ok=True)
    json.dump(js, open(JOBS, "w"), ensure_ascii=False, indent=1)
    print(f"[LoraScene] 작업 {len(js)}장", flush=True)
    return js


def worker(mode):
    import torch
    torch.set_grad_enabled(False)
    from diffusers import ZImagePipeline
    sys.path.insert(0, os.path.join(HERE, "batch"))
    import run_scene as rs
    jobs = json.load(open(JOBS))
    emb = JOBS + ".emb.pt"
    if mode == "enc":
        pipe = ZImagePipeline.from_pretrained(rs.ZI_BASE, transformer=None, torch_dtype=torch.bfloat16).to("mps")
        torch.save([[t.cpu() for t in pipe.encode_prompt(j["prompt"], device="mps", do_classifier_free_guidance=False)[0]]
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
    loaded, active, log = set(), None, []
    for j, e in zip(jobs, torch.load(emb)):
        for who in j["loras"]:
            if who not in loaded:
                pipe.load_lora_weights(LORA.format(who), adapter_name=who)
                loaded.add(who)
        if active != j["loras"]:
            pipe.set_adapters(j["loras"], adapter_weights=[params.LORA_SCENE_SCALE] * len(j["loras"]))
            active = j["loras"]
        t = time.time()
        pipe(prompt_embeds=[x.to("mps", torch.bfloat16) for x in e], width=W, height=H, num_inference_steps=9,
             guidance_scale=0.0, generator=torch.Generator("mps").manual_seed(j["seed"])).images[0].save(j["out"])
        log.append({"out": j["out"], "secs": round(time.time() - t, 1), "active": pipe.get_active_adapters()})
        print(f"  [LoraScene] {j['cond']} {j['scene']} {'+'.join(j['loras'])} s{j['seed']} {log[-1]['secs']}s {log[-1]['active']}", flush=True)
        json.dump(log, open(JOBS + ".log.json", "w"), ensure_ascii=False)


if __name__ == "__main__":
    cmd, test = sys.argv[1], "--test" in sys.argv
    if cmd == "plan":
        plan(test)
    elif cmd == "all":
        if plan(test):
            for m in ("enc", "gen"):
                subprocess.run([sys.executable, os.path.abspath(__file__), m], check=True)
    else:
        worker(cmd)
