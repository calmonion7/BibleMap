"""프롬프트 연습대 — 한 줄 넣고 토큰·그림·세 축 수치를 한 번에 받는다.

**왜 이 도구인가.** 이 파이프라인에서 프롬프트를 손보는 일은 세 군데서 조용히 배신한다:
CLIP 77토큰을 넘으면 **에러 없이 잘리고**(뒤에 있는 화풍 블록이 통째로 사라진다),
잘 나온 것 같아도 잉크가 목표 구간 밖일 수 있고, 화풍을 얻는 대신 구도를 잃을 수 있다.
그래서 셋을 한 화면에 같이 낸다.

## 쓰는 법

    VENV=/Users/calmonion/.local/biblemap-imggen/.venv314/bin/python   # 전부 이 파이썬으로 돈다

    # ① 공짜 연습 — GPU도 모델 로드도 없이 토큰만 본다(1초). 문구 다듬을 땐 이것만 반복한다.
    $VENV try_prompt.py --check "프롬프트 문장"

    # ② 실제로 한 장 뽑는다 (약 2~3분)
    $VENV try_prompt.py "프롬프트 문장"

    # ③ 손잡이를 돌려본다
    $VENV try_prompt.py "..." --cn 0.3        # ControlNet(구도 강제) 0~1, 기본 params.SCENE_CN
    $VENV try_prompt.py "..." --ip 0.7        # IP-Adapter(얼굴 참고) 0~1, 기본 params.IP_SCALE
    $VENV try_prompt.py "..." --seed 42       # 다른 시드. 한 장으로 판단하지 말라는 뜻이기도 하다
    $VENV try_prompt.py "..." --no-ref        # 얼굴 참고사진을 아예 안 태운다(대조군)
    $VENV try_prompt.py "..." --neg "..."     # 부정 프롬프트 교체. 생략하면 현행 정본을 쓴다
    $VENV try_prompt.py "..." --label 실험이름  # 파일명에 붙는다. 생략하면 프롬프트 해시

산출은 `.forge/reports/canon-pilot/try/`에 쌓인다(git 미추적).

## 읽는 법

세 축의 임계는 **이 도구가 정하지 않는다** — `notes/s0-baseline.json`에 못박힌 값을 읽는다
(task#317 S0가 정답지에서 파생한 것). 자를 바꾸고 싶으면 그 슬라이스를 다시 돌려야 하고,
결과가 마음에 안 든다고 여기서 임계를 만지는 것은 결론 선취다(ADR `260825-013557`).

**축 A(화풍)는 상한이 없다** — 통과했다고 목표 화풍이라는 뜻이 아니다. 반드시 함께 찍히는
**정답지 구간(.102~.221)** 과 비교해서 읽어라. 유화 프롬프트는 .72로 통과하지만 7배 초과다.
"""
import argparse
import hashlib
import json
import os
import sys
import time

import params

OUT = os.path.join(params.OUT_ROOT, "try")
MASKS = os.path.join(params.OUT_ROOT, "masks")
COND_SCENE = os.path.join(params.OUT_ROOT, "cond-scene-ctrl.png")
BASELINE = os.path.join(params.NOTES, "s0-baseline.json")


def default_negative():
    with open(params.PROMPTS_JSON, encoding="utf-8") as f:
        return json.load(f)["negative"]


def token_report(prompt, tokenizer, label="긍정"):
    """넘치면 **무엇이 잘리는지** 보여준다 — 수만 보여주면 무엇을 줄일지 알 수 없다."""
    ids = tokenizer(prompt).input_ids
    lim = tokenizer.model_max_length
    ok = len(ids) <= lim
    print(f"  {label} {len(ids):3d}/{lim} 토큰  {'OK' if ok else '← 넘친다'}")
    if not ok:
        kept = tokenizer.decode(ids[1:lim - 1], skip_special_tokens=True)
        cut = tokenizer.decode(ids[lim - 1:], skip_special_tokens=True)
        print(f"    도달: …{kept[-90:]}")
        print(f"    잘림: {cut[:160]}…  ({len(ids) - lim}토큰, {(len(ids) - lim) / len(ids) * 100:.0f}%)")
    return ok


def judge(path):
    """세 축을 건다. 임계는 S0가 못박은 것을 읽기만 한다."""
    import judge_axes as ja
    import judge_metrics as jm
    import judge_style as js
    from PIL import Image

    base = json.load(open(BASELINE, encoding="utf-8"))
    a_thr, b_thr, c_thr = (base["axis_a"]["thresholds"], base["axis_b"]["threshold"],
                           base["axis_c"]["threshold"])
    band = a_thr["reference_band"]["ink"]

    m = js.style_metrics(path)
    person, frac = ja._person_area()
    e = ja._edge_energy(path)
    c = float((e[person].sum() / e.sum()) / frac)

    seed = int(os.path.basename(path).rsplit("-s", 1)[1].split(".")[0])
    bp = os.path.join(params.OUT_ROOT, "scene", f"{ja.BASELINE_COND}-s{seed}.png")
    box = ja.head_boxes()
    b = None
    if os.path.exists(bp):
        emb = jm.Embedder()
        frozen = {n: emb.embed(Image.open(os.path.join(params.FROZEN, f"{n}.png")))
                  for n in ja.PEOPLE}
        im, bim = ja.scene_image(path), ja.scene_image(bp)
        b = {who: ja._transfer_score(emb.embed(im.crop(box[who])),
                                     emb.embed(bim.crop(box[who])), frozen, who)[0]
             for who in ja.PEOPLE}

    print("\n판정 (임계는 notes/s0-baseline.json — 이 도구가 정하지 않는다)")
    over = m["ink"] > band[1]
    print(f"  A 화풍   잉크 {m['ink']:.4f}  "
          f"{'✅' if js.passes(m, a_thr) else '❌'} (임계 ≥{a_thr['ink_min']:.4f})"
          f"   정답지 구간 {band[0]:.3f}~{band[1]:.3f}"
          f"{'  ⚠ 구간을 초과한다 — 통과했어도 목표 화풍이 아니다' if over else ''}")
    print(f"           명암 p05 {m['val_p05']:.3f} (임계 ≤{a_thr['val_p05_max']:.3f})"
          f" · 채도 p95 {m['sat_p95']:.3f}(판정 미사용)")
    if b:
        print(f"  B 전이   다윗 {b['david']:+.4f} · 골리앗 {b['goliath']:+.4f}  "
              f"{'✅' if all(v > b_thr for v in b.values()) else '❌'} (임계 >{b_thr:+.4f})")
        print(f"           ※ 같은 시드 `a-none`과 짝지어 잰다. CN·프롬프트를 크게 바꾸면 짝이"
              f" 어긋나 이 수는 전이 아닌 이동을 섞는다")
    else:
        print(f"  B 전이   짝 기준선({os.path.basename(bp)})이 없어 못 잰다 — 시드 11/42/7만 가능")
    print(f"  C 구도   농축비 {c:.3f}  {'✅' if c > c_thr else '❌'} (임계 >{c_thr:.3f})")
    print(f"           ※ 인물이 통째로 빠져도 통과할 수 있고, 배경 디테일이 늘면 희석된다")


def main():
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("prompt")
    ap.add_argument("--neg", default=None)
    ap.add_argument("--cn", type=float, default=params.SCENE_CN)
    ap.add_argument("--ip", type=float, default=params.IP_SCALE)
    ap.add_argument("--seed", type=int, default=params.SEED_FIXED)
    ap.add_argument("--no-ref", action="store_true")
    ap.add_argument("--label", default=None)
    ap.add_argument("--check", action="store_true", help="토큰만 확인하고 끝낸다(GPU 0)")
    a = ap.parse_args()
    neg = a.neg if a.neg is not None else default_negative()

    if a.check:
        from transformers import CLIPTokenizer
        tok = CLIPTokenizer.from_pretrained(params.SDXL_BASE, subfolder="tokenizer")
        print("토큰 확인만 (생성 안 함)")
        ok = token_report(a.prompt, tok) & token_report(neg, tok, "부정")
        return 0 if ok else 1

    import torch
    from diffusers import ControlNetModel, StableDiffusionXLControlNetPipeline
    from diffusers.image_processor import IPAdapterMaskProcessor
    from PIL import Image

    os.makedirs(OUT, exist_ok=True)
    label = a.label or hashlib.sha256(a.prompt.encode()).hexdigest()[:8]
    out = os.path.join(OUT, f"{label}-cn{a.cn}-ip{a.ip}-s{a.seed}.png")

    cond = Image.open(COND_SCENE).convert("RGB").resize(params.SCENE_SIZE)
    refs = [[Image.open(os.path.join(params.FROZEN, f"{n}.png")).convert("RGB")]
            for n in ("david", "goliath")]
    masks_im = [Image.open(os.path.join(MASKS, f"{n}.png")).convert("L").resize(params.SCENE_SIZE)
                for n in ("david", "goliath")]

    t = time.time()
    cn = ControlNetModel.from_pretrained(params.CN_MODEL, torch_dtype=torch.float16)
    pipe = StableDiffusionXLControlNetPipeline.from_pretrained(
        params.SDXL_BASE, controlnet=cn, torch_dtype=torch.float16, variant="fp16",
        use_safetensors=True).to("mps")
    pipe.set_progress_bar_config(disable=True)
    print(f"로드 {time.time() - t:.0f}s")
    if not (token_report(a.prompt, pipe.tokenizer) & token_report(neg, pipe.tokenizer, "부정")):
        sys.exit("한도를 넘었다 — 조용히 잘리므로 생성하지 않는다. --check로 다듬은 뒤 다시 오라.")

    kw = dict(prompt=a.prompt, negative_prompt=neg, image=cond,
              width=params.SCENE_SIZE[0], height=params.SCENE_SIZE[1],
              controlnet_conditioning_scale=a.cn, num_inference_steps=params.STEPS,
              guidance_scale=params.GUIDANCE,
              generator=torch.Generator("mps").manual_seed(a.seed))
    if not a.no_ref:
        pipe.load_ip_adapter(params.IP_ADAPTER_REPO, subfolder=params.IP_ADAPTER_SUBFOLDER,
                             weight_name=[params.IP_ADAPTER_WEIGHT] * 2)
        pipe.set_ip_adapter_scale([a.ip] * 2)
        kw["ip_adapter_image"] = refs
        kw["cross_attention_kwargs"] = {"ip_adapter_masks": IPAdapterMaskProcessor().preprocess(
            masks_im, height=params.SCENE_SIZE[1], width=params.SCENE_SIZE[0])}

    ts = time.time()
    pipe(**kw).images[0].save(out)
    print(f"\n생성 {time.time() - ts:.0f}s  CN={a.cn} IP={'없음' if a.no_ref else a.ip} 시드={a.seed}")
    print(f"→ {out}")
    judge(out)
    print(f"\n같은 조합을 다른 시드로 한 번 더 보라 — 한 장은 시드 운일 수 있다(task#317 S4가 그랬다):"
          f"\n  … --seed 42 --label {label}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
