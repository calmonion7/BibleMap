"""task#315 S2 교정 — (B) 판정을 **단일 주어 초상**에서 다시 가른다.

왜 다시 하는가. 1차 S2(gen_sweep_scale_age.py)는 (B)「얼굴 정본 1장 + 나이는 프롬프트가 얹는다」를
**장면**에서 시험했다. 그 시험대는 (B) 성립을 보여줄 수 없는 구조였다 — 실측 두 가지:

  (1) 나이가 대상에 결속되지 않는다. 실제로 쓴 문장은
      "... an old man of sixty-two shepherd swings a sling on the left, a huge armored giant
       stands on the right." 다. CLIP은 주어 결속을 못 하므로 "old"가 전역에 걸리고, 산출 6장을
      직접 보면 **나이 변화가 오른쪽 골리앗에게 실렸다**(age=62 세 장 모두 거인이 백발·노년).
      negative의 "child, youth"도 두 인물 모두를 늙히는 쪽으로 작동한다.
  (2) SCENE_CN=0.8이 실루엣을 고정한다. 왼쪽 다윗은 어느 scale에서도 아이 체형을 벗지 못한다 —
      나이는 표면(머리색·주름)에만 실릴 수 있다.

⇒ 1차의 "(B) 불성립"은 **(B)가 틀렸다는 증거가 아니라 시험대가 못 쟀다는 증거**다. 이 값은 74명
확대의 동결 원가를 74장과 150~220장 사이에서 가르므로(3배), 교란된 시험으로 확정하지 않는다.

이 스크립트가 가르는 방식 — 축을 섞지 않는다(task#308 선례, 계획이 명시한 규율):
  · 주어를 하나로: **초상**이다. 화면에 인물이 하나뿐이라 나이가 붙을 곳이 하나다.
  · 조건 입력을 두상으로: cond-david-ctrl.png. 몸이 없으니 실루엣이 체형을 고정하지 않는다.
  · 강도를 조건의 종류에 맞춘다: PERSON_CN(=0.3, gen_candidates.py에서 **파생**).
    ADR 260824-191250 — 파생은 승계하지 않는다. 두상에 SCENE_CN을 쓰면 빈 타원이 된다(SWEEP.md).
  · 변수는 둘뿐: ip_adapter_scale {0.3,0.5,0.7} × 나이 {15, 62}. 시드·화풍·스텝은 전부 고정.

프롬프트는 derive_prompts.portrait_prompt()의 조립 규칙을 그대로 쓴다(손으로 쓰지 않는다) —
나이 어휘만 갈아 끼운다. 나이 숫자는 data/person_events/david.json의 sortKey에서 파생한다.
"""
import hashlib
import json
import os
import sys
import time

import torch
from diffusers import ControlNetModel, StableDiffusionXLControlNetPipeline
from PIL import Image

import params

sys.path.insert(0, params.CANON_DIR)
from derive_prompts import (  # noqa: E402
    STYLE, NEG, AXIS_EN, age_at, num_to_words, read_axes, read_brief,
)

OUT = os.path.join(params.OUT_ROOT, "sweep2p")
COND_DAVID = os.path.join(params.OUT_ROOT, "cond-david-ctrl.png")
FROZEN_DAVID = os.path.join(params.FROZEN, "david.png")
# 두상 강도는 예전에 gen_candidates.py를 정규식으로 긁어 파생했지만, 이제 그 파일도 정본을
# 읽으므로 경유가 한 겹 늘 뿐이다 — params.PERSON_CN을 직접 읽는다.


# 나이 두 값 — 데이터에서 파생(리터럴 금지). 15 = 골리앗 사건, 62 = 마지막 이벤트.
YOUNG = age_at("authored-david-goliath-gath")
OLD = age_at("authored-david-returns-jerusalem")
AGES = [
    (YOUNG, AXIS_EN["age"]["소년/청년"][0], AXIS_EN["age"]["소년/청년"][1]),
    (OLD, f"old man of {num_to_words(OLD)}", AXIS_EN["age"]["성인"][1]),
]


def portrait(age_phrase, age_neg):
    """portrait_prompt()의 조립 순서(나이 → BRIEF → 머리카락 → 머리쓰개)를 그대로 쓰고
    나이 어휘만 갈아 끼운다. 다윗의 나머지 축(곱슬머리·맨머리·수염없음·남)은 정본에서 읽는다."""
    axes = read_axes("david")
    en = {k: AXIS_EN[k][v] for k, v in axes.items()}
    parts = [age_phrase, read_brief("david"), en["hair"][0], en["headwear"][0]]
    body = ", ".join(p for p in parts if p)
    art = "an" if body[0].lower() in "aeiou" else "a"
    prompt = f"{STYLE} close-up head portrait of {art} {body}, facing forward."
    negs = [NEG, age_neg] + [v[1] for k, v in en.items() if k != "age" and v[1]]
    return prompt, ", ".join(p for p in negs if p)


def main():
    os.makedirs(OUT, exist_ok=True)
    for p in (COND_DAVID, FROZEN_DAVID):
        if not os.path.exists(p):
            sys.exit(f"입력이 없다: {p}")
    cn_scale = params.PERSON_CN

    t = time.time()
    cn = ControlNetModel.from_pretrained(params.CN_MODEL, torch_dtype=torch.float16)
    pipe = StableDiffusionXLControlNetPipeline.from_pretrained(
        params.SDXL_BASE, controlnet=cn, torch_dtype=torch.float16, variant="fp16",
        use_safetensors=True).to("mps")
    pipe.set_progress_bar_config(disable=True)
    pipe.load_ip_adapter(params.IP_ADAPTER_REPO, subfolder=params.IP_ADAPTER_SUBFOLDER,
                         weight_name=params.IP_ADAPTER_WEIGHT)
    print(f"로드 {time.time() - t:.0f}s  PERSON_CN={cn_scale}(정본)", flush=True)

    # CLIP 77토큰 하드 게이트 — 파이프라인의 실제 tokenizer로 잰다(조용히 잘리면 뒤가 사라진다).
    built = [(age, *portrait(ph, ng)) for age, ph, ng in AGES]
    for _, pr, ng in built:
        for s in (pr, ng):
            n = len(pipe.tokenizer(s).input_ids)
            print(f"  토큰 {n}/{pipe.tokenizer.model_max_length}  {s[:64]}...")
            if n > pipe.tokenizer.model_max_length:
                sys.exit(f"CLIP 한도 초과({n}) — 중단한다: {s}")

    cond = Image.open(COND_DAVID).convert("RGB").resize(params.PERSON_SIZE)
    ref = Image.open(FROZEN_DAVID).convert("RGB")
    meta, t0, n = [], time.time(), 0
    total = len(params.IP_SCALES) * len(built)
    for ip in params.IP_SCALES:
        pipe.set_ip_adapter_scale(ip)
        for age, prompt, neg in built:
            out = os.path.join(OUT, f"david-ip{ip}-age{age}-s{params.SEED_FIXED}.png")
            n += 1
            if os.path.exists(out):
                continue
            ts = time.time()
            img = pipe(prompt=prompt, negative_prompt=neg, image=cond,
                       ip_adapter_image=ref,
                       width=params.PERSON_SIZE[0], height=params.PERSON_SIZE[1],
                       controlnet_conditioning_scale=cn_scale, num_inference_steps=params.STEPS,
                       guidance_scale=params.GUIDANCE,
                       generator=torch.Generator("mps").manual_seed(params.SEED_FIXED)).images[0]
            img.save(out)
            print(f"  [{n}/{total}] {os.path.basename(out)}  {time.time() - ts:.0f}s", flush=True)
            meta.append({"ip_adapter_scale": ip, "age": age, "path": out, "prompt": prompt,
                         "negative": neg, "seconds": round(time.time() - ts, 1)})

    shas = {}
    for f in sorted(os.listdir(OUT)):
        if f.endswith(".png"):
            p = os.path.join(OUT, f)
            shas[f] = hashlib.sha256(open(p, "rb").read()).hexdigest()
    assert len(set(shas.values())) == len(shas), f"sha256 중복: {shas}"
    print(f"\n{len(shas)}장  sha256 전수 상이 ✓  총 {time.time() - t0:.0f}s")
    with open(os.path.join(params.NOTES, "sweep2p-meta.json"), "w", encoding="utf-8") as f:
        json.dump({"person_cn": cn_scale, "seed": params.SEED_FIXED,
                   "size": params.PERSON_SIZE, "ages": [YOUNG, OLD],
                   "ip_scales": params.IP_SCALES, "sha256": shas, "runs": meta}, f,
                  ensure_ascii=False, indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
