"""task#315 S2 — ip_adapter_scale x 나이 스윕(GPU). 다윗 동결본(frozen/david.png) 하나를
IP-Adapter 레퍼런스로 물려 `ip_adapter_scale {0.3, 0.5, 0.7}` x 나이 {골리앗 사건 나이, 마지막 이벤트
나이} = 6장을 낸다. 나머지는 전부 고정 — 축을 섞지 않는다(task#308 선례):
콘티 조건 입력 cond-scene-ctrl.png(--at 9000, SCENE_CN=0.8) · 시드 11(다윗 동결본과 동일 시드,
gen_candidates.py의 bg-on/bg-off와도 동일) · 화풍 블록(derive_prompts.STYLE). 마스크·골리앗
레퍼런스는 쓰지 않는다(이 단계의 비목표 — 마스크는 S4의 축).

나이 어휘는 derive_prompts.age_at()으로 data/person_events/david.json에서 파생한다(리터럴 15/62를
손으로 박지 않는다). 젊은 쪽은 derive_prompts.AXIS_EN의 "소년/청년"(이미 이 정정으로 "boy of
fifteen")을 그대로 쓴다. 나이 축의 negative도 AXIS_EN에서 재사용(baby/toddler류 · child/youth류).

스택은 gen_candidates.py를 그대로 승계(ControlNet scribble + SDXL base, STEPS=30, GUIDANCE=6.5,
mps/float16/fp16, CLIP 77토큰 하드 게이트, 기존 파일 건너뛰는 재개 로직).
"""
import hashlib
import os
import sys
import time

import torch
from diffusers import ControlNetModel, StableDiffusionXLControlNetPipeline
from PIL import Image

import params

sys.path.insert(0, params.CANON_DIR)
from derive_prompts import STYLE, NEG, AXIS_EN, age_at, num_to_words  # noqa: E402

OUT = os.path.join(params.OUT_ROOT, "sweep2")
FROZEN_DAVID = os.path.join(params.FROZEN, "david.png")
COND_SCENE = os.path.join(params.OUT_ROOT, "cond-scene-ctrl.png")

# 나이 두 값 — 데이터에서 파생(리터럴로 쓰지 않는다). 골리앗 사건 나이는 AXIS_EN["age"]["소년/청년"]가
# 이미 이 값으로 정정돼 있으므로(derive_prompts.py 참조) 긍정 어휘를 그대로 재사용한다.
YOUNG_AGE = age_at("authored-david-goliath-gath")
OLD_AGE = age_at("authored-david-returns-jerusalem")  # 마지막 이벤트 = 최대 sortKey
AGES = [
    (YOUNG_AGE, AXIS_EN["age"]["소년/청년"][0], AXIS_EN["age"]["소년/청년"][1]),
    (OLD_AGE, f"old man of {num_to_words(OLD_AGE)}", AXIS_EN["age"]["성인"][1]),
]

# 콘티가 그리는 순간(--at 9000, 삼상 17장 대결) 그대로 두 인물을 배치하되, 다윗의 나이만 바꾼다.
# 나머지 문구는 derive_prompts.SCENE_PERSON("a small shepherd boy swings...")의 뒷부분을 그대로 쓴다
# — 이 파일이 그 상수를 정의하지 않는 이유는 나이가 변수라서다.
SCENE_TAIL = "shepherd swings a sling on the left, a huge armored giant stands on the right."


def build_prompt(age_phrase):
    # 배경 어휘(BG_VOCAB)는 뺀다 — ADR 260824-191252(배경은 정본이 아니라 프롬프트 어휘)라 이 스윕이
    # 고정해야 할 축이 아니고, "old man of sixty-two" 조합에서 CLIP 77토큰을 실측 초과시켰다(79토큰,
    # 하드 게이트가 실제로 잡았다).
    art = "an" if age_phrase[0].lower() in "aeiou" else "a"
    return f"{STYLE} {art} {age_phrase} {SCENE_TAIL}"


def main():
    os.makedirs(OUT, exist_ok=True)
    for p in (FROZEN_DAVID, COND_SCENE):
        if not os.path.exists(p):
            sys.exit(f"필요한 입력이 없다: {p}")

    t = time.time()
    cn = ControlNetModel.from_pretrained(params.CN_MODEL, torch_dtype=torch.float16)
    pipe = StableDiffusionXLControlNetPipeline.from_pretrained(
        params.SDXL_BASE, controlnet=cn, torch_dtype=torch.float16, variant="fp16",
        use_safetensors=True).to("mps")
    pipe.set_progress_bar_config(disable=True)
    pipe.load_ip_adapter(params.IP_ADAPTER_REPO, subfolder=params.IP_ADAPTER_SUBFOLDER,
                         weight_name=params.IP_ADAPTER_WEIGHT)
    print(f"로드 {time.time() - t:.0f}s", flush=True)

    # CLIP 77토큰 하드 게이트 — 실제로 쓰는 파이프라인 tokenizer로 잰다(gen_candidates.py 선례).
    negs = {NEG}
    prompts = []
    for age, phrase, age_neg in AGES:
        prompt = build_prompt(phrase)
        prompts.append((age, prompt))
        negs.add(f"{NEG}, {age_neg}" if age_neg else NEG)
    for pr in list(negs) + [p for _, p in prompts]:
        n = len(pipe.tokenizer(pr).input_ids)
        print(f"  토큰 {n}/{pipe.tokenizer.model_max_length}  {pr[:60]}...")
        if n > pipe.tokenizer.model_max_length:
            sys.exit(f"프롬프트가 CLIP 한도를 넘었다({n}) — 조용히 잘리므로 중단한다: {pr}")

    cond = Image.open(COND_SCENE).convert("RGB").resize(params.SCENE_SIZE)
    ref = Image.open(FROZEN_DAVID).convert("RGB")

    outputs = []
    t0, n, total = time.time(), 0, len(params.IP_SCALES) * len(AGES)
    for scale in params.IP_SCALES:
        pipe.set_ip_adapter_scale(scale)
        for age, phrase, age_neg in AGES:
            prompt = build_prompt(phrase)
            neg = f"{NEG}, {age_neg}" if age_neg else NEG
            out = os.path.join(OUT, f"david-ip{scale}-age{age}-s{params.SEED_FIXED}.png")
            outputs.append(out)
            if os.path.exists(out):
                n += 1
                continue
            ts = time.time()
            img = pipe(prompt=prompt, negative_prompt=neg, image=cond, ip_adapter_image=ref,
                       width=params.SCENE_SIZE[0], height=params.SCENE_SIZE[1],
                       controlnet_conditioning_scale=params.SCENE_CN,
                       num_inference_steps=params.STEPS, guidance_scale=params.GUIDANCE,
                       generator=torch.Generator("mps").manual_seed(params.SEED_FIXED)).images[0]
            img.save(out)
            n += 1
            print(f"  [{n}/{total}] {os.path.basename(out)}  {time.time() - ts:.0f}s", flush=True)
    print(f"\n{n}장 완료  총 {time.time() - t0:.0f}s")

    # 완료기준 2 — sha256 전수 상이를 스크립트가 단정한다.
    digests = [hashlib.sha256(open(p, "rb").read()).hexdigest() for p in outputs]
    assert len(set(digests)) == len(digests), f"sha256 중복 있음: {outputs}"
    for p, d in zip(outputs, digests):
        print(f"sha256 {d[:16]}...  {os.path.basename(p)}")
    print("SANITY 통과 — 6장 sha256 전수 상이")
    return 0


if __name__ == "__main__":
    sys.exit(main())
