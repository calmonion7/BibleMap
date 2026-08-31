"""전신 표본 생성기 (task#319 part2 S2) — 정체성 없는 단독 인물 1장.

`derive_prompts.sample_prompt()`(중립 정면 단독 전신)를 화풍 시트의 **얼굴 크롭 1컷**을
IP-Adapter 레퍼런스로 물려 생성한다. ControlNet은 쓰지 않는다 — 콘티가 없는 단독 표본이라
구도를 강제할 대상이 없다.

**레퍼런스가 시트 전체가 아니라 얼굴 크롭인 이유** — `.forge/reports/raster-pilot/FINDINGS.md`
실험①의 실측: 시트 전체(다포즈 캐릭터 시트)를 IP-Adapter에 물리면 배치까지 전이돼 산출물에
인물이 여럿 생긴다("소년 3명, 거인 없음"). 260×260 얼굴 크롭으로 바꾸자 그 오염이 완전히
사라졌다(CONTEXT.md [[전신 표본]] 참조). `reference/scene-*-refN.png`도 이 슬라이스에서 육안
확인한 결과 REFERENCE.md의 "단독 장면" 서술과 달리 실제로는 인물 1명의 3개 포즈/각도가 한
캔버스에 든 패널 구성이라(정면·측면 등) `sheet-s20*.png`와 같은 다포즈 위험을 그대로 진다 —
그래서 두 후보 모두 대신, 이미 실측으로 검증된 얼굴 크롭 경로를 쓴다.

**시도 2(part2 S2 재시도) 진단 — 크롭이 아니라 그 크롭의 구도가 전이됐다.** 시도 1(위 문단의
FACE_CROP_BOX)은 인물수 오염(3명)은 막았지만 새 오염을 냈다: ink=.1694로 축 A는 통과했는데,
산출물이 "full body … standing alone, facing forward" 지시를 누르고 **목~가슴만 나온 3/4 측면
흉상**이 됐다. FACE_CROP_BOX 자체가 이미 "얼굴 근접 클로즈업" 구도라 IP-Adapter가 정체성뿐 아니라
그 구도까지 같이 실은 것으로 진단됨(판정자 노트, 2026-08-26). 손잡이를 IP 강도가 아니라
**레퍼런스 선택**으로 바꾼다 — 같은 시트의 좌상단 정면 전신 패널(손을 허리에 얹고 선 단독 포즈)을
대신 문다. 레퍼런스의 구도 자체가 이미 "전신·정면·단독"이므로 구도가 함께 전이돼도 목표와 부딪히지
않는다. IP 강도는 그대로 1.0으로 둔다 — 변수를 한 번에 둘 바꾸면 무엇이 고쳤는지 갈릴 수 없다.

**시도 3(part2 S2 마지막 재시도) 진단 — 크롭이 아니라 그 상류의 CLIPImageProcessor가 정사각으로
자른다.** 시도 2는 레퍼런스를 전신 패널로 바꿨지만 여전히 실패했다: ink=.1092로 축 A는 통과했는데
머리가 프레임 밖으로 잘렸다(가슴~허벅지만 보임). `transformers.CLIPImageProcessor()` 기본값을 직접
인스턴스화해 확인한 결과 `do_resize(shortest_edge=224)` + `do_center_crop(224×224, 정사각)`이다.
IDENTITY_CROP_BOX가 낸 360×1004 세로 직사각형을 정사각화 없이 그대로 넘기면, 리사이즈 후
center-crop이 원본 좌표 기준 y≈321~681(가슴~허벅지 밴드)만 남긴다 — 이번 산출물의 프레이밍과
정확히 일치한다. 그래서 IP-Adapter에 넘기기 전에 **정사각으로 레터박스**한다(`ImageOps.pad`,
여백은 크롭 자체의 종이색으로 채운다) — CLIPImageProcessor의 center-crop이 머리~발 전체를
224×224 안에 담게 하기 위함이다. IP 강도(1.0)·레퍼런스 선택(좌상단 전신 패널)은 그대로 둔다 —
이번 실패는 강도나 레퍼런스 문제가 아니라 전처리 단계에서 이미 정보가 잘리는 문제였다.

Usage: /Users/calmonion/.local/biblemap-imggen/.venv314/bin/python gen_sample.py david [--seed 11] [--ip 1.0]
"""
import argparse
import os
import sys
import time

import torch
from diffusers import AutoPipelineForText2Image
from PIL import Image, ImageOps

import params

sys.path.insert(0, params.CANON_DIR)
import derive_prompts  # noqa: E402

OUT = os.path.join(params.OUT_ROOT, "samples")
STYLE_SHEET = os.path.join(params.REFERENCE, "sheet-s200.png")
# sheet-s200.png 좌상단 정면 전신 패널(육안 확인 좌표) — 손을 허리에 얹고 선 단독 포즈, 다른
# 패널을 걸치지 않는다. 시도 1의 FACE_CROP_BOX(얼굴만, 770,30~1010,330 — 근접 클로즈업 구도)는
# 그 구도 자체가 전이돼 전신 프롬프트를 눌렀다고 진단됨(위 모듈 docstring 참조) — 목표 구도(전신·
# 정면·단독)와 이미 같은 패널로 바꿔 구도 신호와 텍스트 지시를 맞춘다.
IDENTITY_CROP_BOX = (10, 10, 370, 1014)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("name", choices=["david", "goliath"])
    ap.add_argument("--seed", type=int, default=params.SEED_FIXED)
    ap.add_argument("--ip", type=float, default=1.0)
    # 2026-08-26 실측으로 기본이 뒤집혔다 — 아래 --no-ref 주석 참조.
    ap.add_argument("--no-ref", dest="no_ref", action="store_true",
                    help="IP 레퍼런스를 아예 물리지 않는다(다윗의 권장 경로)")
    # 2026-08-26: 사용자가 **비늘갑옷 참고 이미지**를 제공했다. 골리앗의 어린갑(삼상 17:5)은
    # 어휘로 6종 0/6이었고(PROMPTING.md 8), 남은 손잡이가 이미지 앵커였다. 이 경로는 레퍼런스를
    # **자르지 않고 그대로** 넘긴다 — 224 center-crop이 이미 전신을 잡는 것을 실측으로 확인했다
    # (원본 1408x768 → 중앙 정사각이 전신·갑옷·투구·정강이받이를 전부 담는다).
    ap.add_argument("--ref", default=None,
                    help="IP 레퍼런스 경로를 직접 준다(자르지 않고 그대로 넘긴다)")
    ap.add_argument("--label", default=None)
    ap.add_argument("--portrait", action="store_true",
                    help="전신이 아니라 **두상 초상**으로 뽑는다 — 머리 단계 레퍼런스용. 몸·의상 "
                         "조각이 빠져 방향·부재 서술에 토큰을 통째로 쓸 수 있다")
    ap.add_argument("--profile", action="store_true",
                    help="옆얼굴 판본으로 뽑는다 — 머리 단계 전용 레퍼런스(sample_prompt 주석 참조). "
                         "정면 판본이 회전을 막던 자리를 대신한다")
    a = ap.parse_args()

    derive_prompts.main()
    if a.portrait:
        prompt, neg, _ = derive_prompts.portrait_prompt(a.name, profile=a.profile)
    else:
        prompt, neg = derive_prompts.sample_prompt(a.name, profile=a.profile)

    os.makedirs(OUT, exist_ok=True)
    label = a.label or f"{a.name}{'-portrait' if a.portrait else ''}{'-profile' if a.profile else ''}"
    tag = 'none' if (a.no_ref and not a.ref) else a.ip
    out = os.path.join(OUT, f"{label}-ip{tag}-s{a.seed}.png")

    # **레퍼런스를 물리지 않는 것이 표본의 권장 경로다(2026-08-26 실측).** 시도 1~3이 한
    # 메커니즘으로 수렴했다: IP-Adapter 상류의 CLIPImageProcessor가 resize(shortest_edge=224)
    # +center_crop(224)을 강제하므로 **레퍼런스의 프레이밍이 산출물 프레이밍으로 전이**되고,
    # 인물이 그 정사각을 못 채우면 화풍 신호가 희석된다(얼굴크롭→흉상 ink .1694 / 몸크롭→머리
    # 잘림 ink .1092 / 정사각 레터박스→전신이나 ink .0820으로 하한 미달). 사람은 1:2라
    # 「정사각(전신 프레이밍)」과 「채움(잉크 유지)」이 구조적으로 상충한다.
    # 그런데 **레퍼런스를 아예 빼고 텍스트만으로 뽑으면 ink .1849로 정답지 구간에 든다** —
    # 화풍은 레퍼런스를 요구하지 않는다. 그래서 표본은 --no-ref로 뽑고, 프레이밍은 세로 캔버스
    # (params.SAMPLE_SIZE)와 프롬프트 어휘로만 잡는다. 시트 경로는 대조군용으로 남겨 둔다.
    identity_ref = None
    if a.ref:
        if not os.path.exists(a.ref):
            sys.exit(f"레퍼런스가 없다: {a.ref}")
        identity_ref = Image.open(a.ref).convert("RGB")
    elif not a.no_ref:
        crop = Image.open(STYLE_SHEET).convert("RGB").crop(IDENTITY_CROP_BOX)
    # 시도3 수정: IP-Adapter 상류의 CLIPImageProcessor가 정사각 center-crop(224x224)을 강제한다
    # (위 모듈 docstring 「시도 3 진단」). 360x1004 직사각을 그대로 넘기면 가슴~허벅지 밴드만
    # 남는다 — 정사각으로 레터박스해 머리~발이 center-crop 안에 들어오게 한다. 여백은 크롭
    # 자신의 모서리(종이 여백, 인물이 없는 자리)에서 표본 추출한 색으로 채운다.
        identity_ref = ImageOps.pad(crop, (max(crop.size),) * 2, color=crop.getpixel((0, 0)))

    t = time.time()
    pipe = AutoPipelineForText2Image.from_pretrained(
        params.SDXL_BASE, torch_dtype=torch.float16, variant="fp16",
        use_safetensors=True).to("mps")
    pipe.set_progress_bar_config(disable=True)
    if identity_ref is not None:
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
    kw = {} if identity_ref is None else {"ip_adapter_image": identity_ref}
    pipe(prompt=prompt, negative_prompt=neg, width=params.SAMPLE_SIZE[0],
         height=params.SAMPLE_SIZE[1], num_inference_steps=params.STEPS,
         guidance_scale=params.GUIDANCE, **kw,
         generator=torch.Generator("mps").manual_seed(a.seed)).images[0].save(out)
    print(f"생성 {time.time() - ts:.0f}s  캔버스={params.SAMPLE_SIZE} "
          f"IP={'없음' if identity_ref is None else a.ip} 시드={a.seed}\n-> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
