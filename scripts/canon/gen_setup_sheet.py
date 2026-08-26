"""[[설정화]] 시트 생성기 — 인물 하나의 4패널 캐릭터 설정 시트 (task#319 후속, 2026-08-26).

**왜 필요한가.** `reference/sheet-s200~203.png` 네 장은 **전부 다윗**이다. 골리앗에는 화풍·의상의
이미지 근거가 없어서, 텍스트만으로 전신 표본을 뽑으면 모델의 「판타지 기사」 사전지식이 이긴다 —
부정어를 5회 서로 다르게 강화(중립 갑옷 낱말 → 인물별 분리 → barbaric 레지스터)해도 판금·망토·무기가
남았다. `.forge/reports/raster-pilot/FINDINGS.md`가 이미 「**(인물 × 생애단계) 단위 시트 필요 확정**」
이라고 적어 둔 그 후속이고, 2026-08-26 사용자가 이 경로를 골랐다.

**레퍼런스로 다윗 시트 *전체*를 물린다 — 여기서는 그것이 결함이 아니라 이점이다.**
IP-Adapter 상류의 `CLIPImageProcessor`가 `resize(shortest_edge=224)+center_crop(224)`를 강제하므로
**레퍼런스의 프레이밍이 산출물 프레이밍으로 전이된다**(task#319 발견 1). 장면을 생성할 때 이 전이는
오염이어서 FINDINGS.md가 「레퍼런스는 시트가 아니라 시트에서 잘라낸 **얼굴 1컷**이다」로 규칙을 세웠다.
**이 스크립트는 반대 경우다** — 만들려는 것이 시트이므로 「4패널 설정화 레이아웃」의 전이가 곧 목표
프레이밍이다. 정체성은 텍스트(`BRIEF`·`AXES`)가 나르고 레퍼런스는 화풍·레이아웃만 나르게 해야 하므로,
IP 강도는 정체성 전이용 값(FINDINGS.md의 0.7)보다 **낮은 쪽**을 기본으로 두고 축을 열어 둔다.

**산출 위치가 `reference/`가 아닌 이유(중요).** `judge_style.reference_paths()`는
`glob(REFERENCE/*.png)`으로 **정답지 전부**를 읽어 축 A 임계를 파생한다. 새 시트를 그 디렉터리에 넣으면
**축 A 구간이 자동으로 바뀐다** — 임계 변경을 부작용으로 일으키는 것이고, 그것은 사람이 명시로 정할
결정이다(ADR `260823-221839`·`260825-013557`). 그래서 `scripts/canon/setup/`에 둔다. 이 자리도
`scripts/` 아래이므로 `validate_canon_pipeline` 축2가 추적을 기계적으로 강제한다.

Usage:
    VENV=/Users/calmonion/.local/biblemap-imggen/.venv314/bin/python
    $VENV gen_setup_sheet.py goliath --ip 0.45
    $VENV gen_setup_sheet.py goliath --ip 0.7 --label ip07     # 강도 축
"""
import argparse
import os
import sys
import time

import torch
from diffusers import AutoPipelineForText2Image
from PIL import Image

import params

sys.path.insert(0, params.CANON_DIR)
import derive_prompts  # noqa: E402

OUT = os.path.join(params.CANON_DIR, "setup")
STYLE_SHEET = os.path.join(params.REFERENCE, "sheet-s200.png")
SHEET_SIZE = (1024, 1024)   # 다윗 시트 4장과 같은 캔버스 — 비교 가능성 때문에 승계한다.


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("name", choices=["david", "goliath"])
    ap.add_argument("--seed", type=int, default=params.SEED_FIXED)
    # 정체성이 아니라 화풍·레이아웃만 원하므로 FINDINGS.md의 정체성용 0.7보다 낮게 시작한다.
    ap.add_argument("--ip", type=float, default=0.45)
    ap.add_argument("--label", default=None)
    # 레퍼런스를 갈아 끼우는 축 — 2026-08-26에 사용자가 **비늘갑옷 참고 이미지**를 제시했다.
    # 다윗 시트는 화풍·레이아웃은 나르지만 의상이 천이라 비늘을 못 낸다(SETUP.md 표, 5종 0/5).
    # 화풍은 프롬프트만으로도 정답지 구간에 드는 것이 실측이므로(ink .1849, task#319 발견 2),
    # 레퍼런스를 **의상 앵커**로 쓰고 화풍은 텍스트에 맡기는 조합이 가능하다.
    ap.add_argument("--ref", default=STYLE_SHEET,
                    help="IP 레퍼런스 경로(기본: 다윗 화풍 시트). 의상 앵커로 갈아 끼울 수 있다")
    a = ap.parse_args()

    derive_prompts.main()
    prompt, neg = derive_prompts.setup_sheet_prompt(a.name)

    os.makedirs(OUT, exist_ok=True)
    tag = os.path.splitext(os.path.basename(a.ref))[0]
    out = os.path.join(OUT, f"{a.label or a.name}-ref{tag}-ip{a.ip}-s{a.seed}.png")

    # 시트 **전체**를 그대로 물린다(크롭하지 않는다) — 레이아웃 전이가 목표다(위 docstring).
    if not os.path.exists(a.ref):
        sys.exit(f"레퍼런스가 없다: {a.ref}")
    ref = Image.open(a.ref).convert("RGB")

    t = time.time()
    pipe = AutoPipelineForText2Image.from_pretrained(
        params.SDXL_BASE, torch_dtype=torch.float16, variant="fp16",
        use_safetensors=True).to("mps")
    pipe.set_progress_bar_config(disable=True)
    pipe.load_ip_adapter(params.IP_ADAPTER_REPO, subfolder=params.IP_ADAPTER_SUBFOLDER,
                         weight_name=params.IP_ADAPTER_WEIGHT)
    pipe.set_ip_adapter_scale(a.ip)
    n_pos = len(pipe.tokenizer(prompt).input_ids)
    n_neg = len(pipe.tokenizer(neg).input_ids)
    print(f"로드 {time.time() - t:.0f}s  프롬프트 {n_pos}/{pipe.tokenizer.model_max_length}토큰"
          f"  부정 {n_neg}/{pipe.tokenizer.model_max_length}토큰", flush=True)
    if n_pos > pipe.tokenizer.model_max_length or n_neg > pipe.tokenizer.model_max_length:
        sys.exit("한도를 넘었다 — 조용히 잘리므로 생성하지 않는다.")

    ts = time.time()
    pipe(prompt=prompt, negative_prompt=neg, width=SHEET_SIZE[0], height=SHEET_SIZE[1],
         num_inference_steps=params.STEPS, guidance_scale=params.GUIDANCE,
         ip_adapter_image=ref,
         generator=torch.Generator("mps").manual_seed(a.seed)).images[0].save(out)
    print(f"생성 {time.time() - ts:.0f}s  캔버스={SHEET_SIZE} IP={a.ip} 시드={a.seed}\n-> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
