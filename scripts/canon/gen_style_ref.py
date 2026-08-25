"""화풍 고정 레퍼런스 — 화풍을 말이 아니라 **그림으로** 준다(GPU 3장).

**남은 축이 이것 하나다.** 결합 방식(`gen_combined.py`)이 이음새·구도·정본 전이를 세웠고
화풍만 미달이다(잉크 0.0191, 정답지 구간 0.102~0.221).

**그리고 이 카드는 한 번도 안 쓰였다.** `raster-pilot/FINDINGS.md` 55행이
*「화풍 드리프트(ControlNet 경로가 수채로 감) 대응 — 스타일 LoRA 또는 **화풍 고정 레퍼런스**」*
를 미시험 후보로 적어 둔 뒤 파일럿 3건이 그 위에 쌓였다.

**왜 될 법한가.** 두 가지 실측이 같은 곳을 가리킨다:
  · 정답지는 **화풍을 가진 시트**(`reference/sheet-s200.png`, 잉크 0.202)를 IP-Adapter로 0.4~0.7에
    물려 만들어졌다(`~/.local/biblemap-imggen/scenes.py`). 현행은 **창백한 동결 두상**(잉크 0.006)을
    0.3에 문다 — 레퍼런스 자체가 화풍을 안 나른다.
  · 유화 프롬프트 실측에서 **CN의 대비 억제는 절대적이지 않았다**(CN 0.8 .7215 ↔ CN 0 .7189).
    충분히 센 신호는 뚫는다. 이미지 조건은 토큰을 0개 쓰면서 그 신호를 준다.

**배경 단계에서 시험하는 이유**: 인물은 각자 자기 단계에서 자기 동결본을 레퍼런스로 쓰므로
화풍 시트를 겹쳐 물릴 자리가 없다. 배경 단계는 레퍼런스가 비어 있어 그대로 들어간다.
그리고 배경이 화면의 대부분이라 여기서 잉크가 오르면 전체가 오른다.

시트 하나만 쓴다 — 정답지 4장 중 어느 것을 고를지는 이 시험의 축이 아니다(고르면 축이 섞인다).
`IP_SCALES`(정본이 이미 선언한 0.3·0.5·0.7)를 그대로 쓸어 **강도-화풍 곡선**을 낸다.

Usage: /Users/calmonion/.local/biblemap-imggen/.venv314/bin/python gen_style_ref.py
"""
import json
import os
import sys
import time

import torch
from diffusers import ControlNetModel, StableDiffusionXLControlNetPipeline
from PIL import Image

import params

sys.path.insert(0, params.CANON_DIR)
import derive_prompts  # noqa: E402
import judge_style as js  # noqa: E402

OUT = os.path.join(params.OUT_ROOT, "styleref")
COND_SCENE = os.path.join(params.OUT_ROOT, "cond-scene-ctrl.png")
STYLE_SHEET = os.path.join(params.REFERENCE, "sheet-s200.png")
BASELINE = os.path.join(params.OUT_ROOT, "staged", "1-bg-s11.png")  # 레퍼런스 없는 같은 배경


def main():
    os.makedirs(OUT, exist_ok=True)
    if not os.path.exists(STYLE_SHEET):
        sys.exit(f"화풍 시트가 없다: {STYLE_SHEET}")
    derive_prompts.main()
    P = json.load(open(params.PROMPTS_JSON, encoding="utf-8"))
    # 배경 단계 프롬프트 — `gen_staged.py`와 **같은 문장**을 쓴다. 움직이는 축은 레퍼런스 하나다.
    PROMPT = f"{derive_prompts.STYLE} {derive_prompts.BG_VOCAB}"
    NEG = P["negative"]

    cond = Image.open(COND_SCENE).convert("RGB").resize(params.SCENE_SIZE)
    sheet = Image.open(STYLE_SHEET).convert("RGB")

    t = time.time()
    cn = ControlNetModel.from_pretrained(params.CN_MODEL, torch_dtype=torch.float16)
    pipe = StableDiffusionXLControlNetPipeline.from_pretrained(
        params.SDXL_BASE, controlnet=cn, torch_dtype=torch.float16, variant="fp16",
        use_safetensors=True).to("mps")
    pipe.set_progress_bar_config(disable=True)
    pipe.load_ip_adapter(params.IP_ADAPTER_REPO, subfolder=params.IP_ADAPTER_SUBFOLDER,
                         weight_name=params.IP_ADAPTER_WEIGHT)
    print(f"로드 {time.time() - t:.0f}s  프롬프트 "
          f"{len(pipe.tokenizer(PROMPT).input_ids)}/{pipe.tokenizer.model_max_length}토큰", flush=True)

    # (레퍼런스 강도, ControlNet 강도) 격자.
    # **배경 단계는 ControlNet을 강하게 걸 이유가 없다** — 단계 파이프라인에서 인물은 각자
    # 자기 단계에서 자기 콘티 크롭으로 그려지므로, 배경의 CN은 인물 실루엣을 눌러 놓을 뿐
    # 구도를 책임지지 않는다. 그리고 CN이 대비를 죽이는 것이 축 A의 지배 원인이었다
    # (CN 0.8 → ink .0051, CN 0.2 → .0512). 두 손잡이를 같이 푼다.
    GRID = [(sc, cnv) for cnv in (params.SCENE_CN, 0.4, 0.2) for sc in (0.7, 1.0)]
    made = []
    for sc, cnv in GRID:
        out = os.path.join(OUT, f"sheet{sc}-cn{cnv}-s{params.SEED_FIXED}.png")
        made.append((f"시트 {sc} · CN {cnv}", out))
        if os.path.exists(out):
            print(f"  [스킵] {os.path.basename(out)}")
            continue
        pipe.set_ip_adapter_scale(sc)
        ts = time.time()
        pipe(prompt=PROMPT, negative_prompt=NEG, image=cond,
             width=params.SCENE_SIZE[0], height=params.SCENE_SIZE[1],
             controlnet_conditioning_scale=cnv,
             num_inference_steps=params.STEPS, guidance_scale=params.GUIDANCE,
             ip_adapter_image=sheet,
             generator=torch.Generator("mps").manual_seed(params.SEED_FIXED)
             ).images[0].save(out)
        print(f"  [시트 {sc} CN {cnv}] {time.time() - ts:.0f}s -> {os.path.basename(out)}", flush=True)

    # --- 강도-화풍 곡선 -----------------------------------------------------
    base = json.load(open(os.path.join(params.NOTES, "s0-baseline.json"), encoding="utf-8"))
    thr = base["axis_a"]["thresholds"]
    band = thr["reference_band"]["ink"]
    rows = [("없음 · CN 0.8", BASELINE)] + made
    print(f"\n축 A 곡선 — 임계 ink≥{thr['ink_min']:.4f} · 정답지 구간 {band[0]:.3f}~{band[1]:.3f}"
          f" · 화풍 시트 자신 {js.style_metrics(STYLE_SHEET)['ink']:.4f}")
    for label, p in rows:
        if not os.path.exists(p):
            continue
        m = js.style_metrics(p)
        mark = "✅" if js.passes(m, thr) else "❌"
        inband = " ← 정답지 구간 안" if band[0] <= m["ink"] <= band[1] else ""
        print(f"  {label:18s} ink={m['ink']:.4f}  p05={m['val_p05']:.3f}  {mark}{inband}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
