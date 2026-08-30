"""part 3 최종 장면 — 생성 전용 콘티 위에 배경 → 다윗 → 골리앗을 순차 인페인팅한다.

`gen_combined.py`가 세운 기제(**종횡비를 지키는 수동 크롭 + 마스크 화소만 되돌리기**)를 그대로
쓰되, **입력 세 가지가 전부 바뀌었다.** 그래서 그 파일을 고치지 않고 새로 둔다 — 그 파일의
docstring은 「잘라붙이기 ↔ 인페인팅」 비교 실측의 기록이고, 입력을 갈아끼우면 그 기록이 거짓이 된다.

| 무엇 | `gen_combined.py` (part 1 이전) | 이 파일 (part 3) | 근거 |
|---|---|---|---|
| ControlNet 조건 | 앱 장면 스케치(`cond-scene-ctrl.png`) | **생성 전용 콘티**(`conti/goliath_scene.png`) | ADR `260826-082626` |
| 인페인팅 마스크 | 앱 스케치 잉크를 41px 팽창 | **콘티 잉크 볼록껍질**(`conti/mask_*.png`) | task#318 S4 — 겹침 0px · 잉크 포함률 1.0 |
| 인물 레퍼런스 | 동결 두상 + 화풍 시트 2장 | **전신 표본 1장뿐**(`samples/*.png`) | part 2 — 두 장을 물리면 시트(0.7)가 동결(0.3)을 덮어 축 B가 +.1942 → +.0256로 무너졌다 |

## 왜 배경과 인물을 다른 실행으로 나누는가

두 단계가 서로 다른 파이프라인 클래스를 쓴다(`…ControlNetPipeline` ↔ `…ControlNetInpaintPipeline`).
한 프로세스에서 둘을 같이 들면 SDXL 가중치가 두 벌 올라간다 — 회고가 「스왑 압박 구간에서 1장씩
직렬로 돌린 것이 3배 열화를 막았다」고 실측한 그 여유(767M~897M)를 그대로 날린다. 그래서
`bg`가 시드 전부의 배경을 한 번의 로드로 찍고, `figures`가 시드 전부의 인물을 한 번의 로드로 찍는다.
**모델 로드는 전체에서 2회다** — 시드마다 2회가 아니다.

## 단계마다 무엇을 담당하는가 — S1 실측으로 확정된 분담

배경 단계에서 (시트 IP 강도 × CN) 격자를 다시 쓸어 나온 결론이 `PROMPTING.md` 11이다:
**화풍의 유일한 공급원은 이미지 앵커이고, 그 앵커는 CN이 낮아져 화풍이 통할 때 구도를 자기
레이아웃(설정화 시트)으로 대체한다.** 화풍이 풀리는 CN 지점과 구도가 끊기는 CN 지점이 같은 칸이라
한 단계에서 둘 다 얻는 값이 없다. 그래서:

  · **배경 단계** = 구도 + 배경 어휘 (앵커 없음 `--ips 0.0` · `--cns 0.6`). 축 A를 요구하지 않는다.
  · **인물 단계** = 화풍 + 정체성. 마스크가 화면의 33%이고 [[전신 표본]]의 ink가 .0986·.6377이라
    최종본의 어두운 화소가 여기서 나온다.
  · **축 A는 최종 장면에서만 판정한다** — 배경에서 재는 것은 범주 오용이다(REFERENCE.md
    「축 A 지표의 적용 범위는 장면류」). 임계는 만지지 않았다. 바뀐 것은 자를 대는 자리다.

손잡이 하나를 판정하려면 최소 3시드다(PROMPTING.md 5: 시드 11 고정으로 11회를 비교해 낸 결론이
시드를 바꾸자 뒤집혔다). S1에서도 CN 0.4·시트 1.0이 시드 11에서 통과(.1573)하고 42에서 실패
(.0858)했다.

Usage:
  .../python gen_final.py bg      --ips 0.0 --cns 0.6 --seeds 11,42,7
  .../python gen_final.py figures --cn 0.6 --bg-ip 0.0 [--fig-cn 0.3] [--ip 0.3] [--seeds 11,42,7]
"""
import argparse
import json
import os
import sys
import time

import numpy as np
import torch
from diffusers import (ControlNetModel, StableDiffusionXLControlNetInpaintPipeline,
                       StableDiffusionXLControlNetPipeline)
from PIL import Image, ImageFilter

import params

sys.path.insert(0, params.CANON_DIR)
import derive_prompts  # noqa: E402
import judge_style as js  # noqa: E402

OUT = os.path.join(params.OUT_ROOT, "final3")
CONTI = os.path.join(params.CANON_DIR, "conti")
SAMPLES = os.path.join(params.CANON_DIR, "samples")
STYLE_SHEET = os.path.join(params.REFERENCE, "sheet-s200.png")
PEOPLE = ("david", "goliath")

PAD = 64          # 마스크 둘레 여백(px) — gen_combined.py가 정한 값을 승계한다(맥락용).
TARGET = 1024     # 확대한 창의 긴 변 — 같은 승계.
STRENGTH = 0.99   # 마스크 안을 사실상 새로 그린다(낮추면 앞 단계의 창백함을 물고 간다).
MASK_BLUR = 6     # 볼록껍질은 경계가 칼같아 되돌릴 때 선이 보인다. 살짝만 흐린다.


def scene_cond():
    """생성 전용 콘티 → 스크리블 ControlNet 조건 입력(흰 선 / 검은 바탕).

    산식은 `prep_cond.py`와 **같다** — 코너 중앙값을 배경으로 보고 |a-bg| > params.THRESHOLD를
    잉크로 본다. 같은 임계·같은 극성이어야 잉크 정의가 파이프라인 전체에서 갈리지 않는다
    (`make_conti_masks._ink_mask`도 같은 식이다). prep_cond.py를 고치지 않는 이유는 그 파일의
    JOBS가 앱 스케치 3건을 가리키는 기록이라서다.
    """
    src = os.path.join(CONTI, "goliath_scene.png")
    a = np.array(Image.open(src).convert("L").resize(params.SCENE_SIZE, Image.LANCZOS)).astype(int)
    bg = int(np.median(a[0:8, 0:8]))
    ctrl = np.where(np.abs(a - bg) > params.THRESHOLD, 255, 0).astype(np.uint8)
    out = os.path.join(OUT, "cond-conti-ctrl.png")
    Image.fromarray(np.stack([ctrl] * 3, -1)).save(out)
    print(f"조건 입력: {os.path.basename(out)}  bg={bg}  잉크율 {ctrl.mean() / 255 * 100:.2f}%")
    return Image.open(out).convert("RGB")


def figure_mask(name):
    """콘티 잉크의 볼록껍질(task#318 S4 산출)을 그대로 인페인팅 마스크로 쓴다.

    `gen_sequential.figure_mask`처럼 41px 팽창하지 않는다 — 껍질은 이미 solid한 실루엣이고
    잉크 포함률이 1.0이다(팽창은 배경을 더 먹을 뿐이다). 경계만 살짝 흐려 되돌릴 때 선이
    안 보이게 한다.
    """
    m = Image.open(os.path.join(CONTI, f"mask_{name}.png")).convert("L").resize(params.SCENE_SIZE)
    return m.filter(ImageFilter.GaussianBlur(MASK_BLUR))


def window(mask, pad):
    """마스크를 감싸는 창(여백 포함, 캔버스 안으로 클램프) — gen_combined.window와 같은 산식."""
    ys, xs = np.where(np.array(mask) > 127)
    W, H = params.SCENE_SIZE
    return (max(0, int(xs.min()) - pad), max(0, int(ys.min()) - pad),
            min(W, int(xs.max()) + 1 + pad), min(H, int(ys.max()) + 1 + pad))


def gen_size(box, target=TARGET):
    """창의 종횡비를 지키면서 긴 변을 target으로. 8의 배수로 맞춘다."""
    w, h = box[2] - box[0], box[3] - box[1]
    s = target / max(w, h)
    return max(8, round(w * s / 8) * 8), max(8, round(h * s / 8) * 8)


def bg_path(cn, seed, ip=1.0):
    """배경 산출 경로. **시트 강도(ip)도 파일명에 넣는다** — 2026-08-26 실측으로 이 축이 열렸다:
    CN 0.4 · 시트 1.0은 축 A를 통과했으나(ink .1573) 시트의 **설정화 레이아웃이 통째로 전이**됐다
    (같은 소년 3명 + 소품 삽화). 마스크는 화면의 33%뿐이라 그 나머지가 최종본에 남는다.
    강도를 손잡이로 쓰려면 파일명이 그것을 구분해야 한다."""
    return os.path.join(OUT, f"bg-ip{ip}-cn{cn}-s{seed}.png")


def _judge():
    """판정 모듈은 **지역에서** 부른다 — 밴드 상자만 쓰는데 CLIP 등 무거운 의존을 생성 경로에
    상시로 끌지 않기 위해서다."""
    import judge_s1
    return judge_s1


def _stage_spec(val):
    """단계 CN 스펙. `"0.3"` → 두 인물 다 0.3 · `"david=0.0"` → 다윗만(골리앗은 그 단계를 건너뛴다)
    · `"david=0.0,goliath=0.5"` → 인물별. None이면 그 단계를 아예 끈다.

    **왜 인물별이 필요한가**(2026-08-31 실측): 머리 단계는 다윗을 돌렸지만 골리앗은 못 돌리고
    축 C(−0.0012)·축 E 수염(−0.0055)만 깎았다 — 그에겐 순손실이라 끌 수 있어야 한다."""
    if val is None:
        return None
    if "=" not in val:
        return {n: float(val) for n in PEOPLE}
    out = {}
    for part in val.split(","):
        k, _, v = part.partition("=")
        if k not in PEOPLE:
            sys.exit(f"모르는 인물: {k!r} — {PEOPLE} 중 하나여야 한다")
        out[k] = float(v)
    return out


def _spec_tag(spec):
    """스펙을 파일명 성분으로. 인물 첫 글자 + 값 — 순서는 PEOPLE 고정이라 결정적이다."""
    return "" if not spec else "".join(f"{n[0]}{spec[n]}" for n in PEOPLE if n in spec)


def tag(cn, bg_ip, fig_cn, ip, ref_band=None, head_cn=None, torso_cn=None, head_ip=None):
    """인물 단계 산출물의 손잡이 태그. **네 손잡이를 전부 파일명에 싣는다** — 두 개(배경 CN·IP)만
    싣던 초판에서는 인물 크롭 CN을 바꾼 재시도가 앞 결과를 조용히 덮어썼다.

    `ref_band`(task#322 R3)도 같은 이유로 싣는다 — 네 손잡이가 같아도 **IP 레퍼런스가 다르면 다른
    그림**인데, 이름이 같으면 아래 `[스킵]` 분기가 낡은 단계 PNG를 재사용한다(2026-08-30 실측:
    콘티 판본이 이름에 없어 뿔을 넣고 돌린 재시도가 어제 그림을 그대로 다시 합성했다)."""
    rb = "" if ref_band is None else f"-rb{ref_band}"
    # `head_cn`(task#322 2026-08-31)도 같은 이유로 싣는다 — 머리 단계를 켜면 **다른 그림**이다.
    # 기본은 None이라 끄면 태그가 종전 그대로다(역호환).
    hc = "" if not head_cn else f"-h{_spec_tag(head_cn)}"
    tc = "" if not torso_cn else f"-t{_spec_tag(torso_cn)}"
    hi = "" if not head_ip else f"-hi{_spec_tag(head_ip)}"
    return f"ip{bg_ip}-cn{cn}-fcn{fig_cn}-sip{ip}{rb}{hc}{tc}{hi}"


BAND_FEATHER = 0.12   # 밴드 마스크 깃털 = 상자 짧은 변의 이 분율(하한 MASK_BLUR).
# **왜 분율인가**: MASK_BLUR(6)만으로는 골리앗 머리 둘레에 **상자 변이 네모로 드러났다**
# (2026-08-31 실측). 마스크가 「밴드 상자 ∩ 인물 마스크」라 상자 변이 그대로 남기 때문이다.
# 상자는 인물마다 크기가 다르므로(다윗 머리 100px · 골리앗 174px) 고정값이 아니라 분율로 판다.


def _band_pass(pipe, canvas, cond, masks, refs, P, key, box, who, cn_val, seed, label,
               ip_val=None, ip_base=None):
    """밴드 하나를 다시 그린다 — 머리 단계·몸통 단계가 **같은 코드**를 쓴다.

    마스크 = 밴드 상자 ∩ 인물 마스크. 상자는 콘티 저작 원본에서 파생한 것을 받는다
    (`judge_s1.conti_head_box` / `conti_torso_box` — ADR `260830-084555`). 배경까지 다시 그리지
    않도록 인물 마스크로 자르고, 상자 변이 드러나지 않도록 깃털을 준다."""
    m = Image.new("L", params.SCENE_SIZE, 0)
    m.paste(masks[who].crop(box), (box[0], box[1]))
    feather = max(MASK_BLUR, int(round(BAND_FEATHER * min(box[2] - box[0], box[3] - box[1]))))
    m = m.filter(ImageFilter.GaussianBlur(feather))
    win = window(m, PAD)
    gw, gh = gen_size(win)
    pr, ng = P[key][who]["prompt"], P[key][who]["negative"]
    n, lim = _tok(pipe, pr, f"{who} {label}")
    # 단계 전용 IP 강도. **왜 필요한가**(2026-08-31): 머리 단계의 레퍼런스는 표본 상단 밴드,
    # 곧 `sample_prompt`가 `"facing forward"`로 명시 저작한 **정면 얼굴 이미지**다. 다윗은 그것을
    # 이기고 돌았지만 골리앗의 회전대칭 투구는 훨씬 강한 앵커라 못 이겼다. 이 단계만 낮춘다 —
    # 전신 단계의 정체성 전이(축 B)는 건드리지 않는다. 끝나면 반드시 되돌린다.
    if ip_val is not None:
        pipe.set_ip_adapter_scale(ip_val)
    ts = time.time()
    res = pipe(prompt=pr, negative_prompt=ng,
               image=canvas.crop(win).resize((gw, gh), Image.LANCZOS),
               mask_image=m.crop(win).resize((gw, gh), Image.LANCZOS),
               control_image=cond.crop(win).resize((gw, gh), Image.LANCZOS),
               width=gw, height=gh, controlnet_conditioning_scale=cn_val, strength=STRENGTH,
               num_inference_steps=params.STEPS, guidance_scale=params.GUIDANCE,
               ip_adapter_image=refs[who],
               generator=torch.Generator("mps").manual_seed(seed)).images[0]
    w, h = win[2] - win[0], win[3] - win[1]
    if ip_val is not None:
        pipe.set_ip_adapter_scale(ip_base)
    canvas.paste(res.resize((w, h), Image.LANCZOS), (win[0], win[1]), m.crop(win))
    print(f"  [{label} {who} s{seed}] {time.time() - ts:.0f}s  프롬프트 {n}/{lim}토큰  "
          f"상자 {box} 깃털 {feather} → 창 {w}x{h} → {gw}x{gh}  CN {cn_val}"
          f"{'' if ip_val is None else f'  IP {ip_val}'}", flush=True)
    return canvas


def _tok(pipe, prompt, label):
    n = len(pipe.tokenizer(prompt).input_ids)
    lim = pipe.tokenizer.model_max_length
    # 무음 절단은 뒤에서 일어난다 — part 2에서 두 번(83/77·80/77) 성별 부정어가 조용히 잘렸다.
    if n > lim:
        sys.exit(f"{label} 프롬프트가 한도를 넘었다({n}/{lim}) — 뒤쪽 조각이 조용히 잘린다")
    return n, lim


# --- 배경 단계 ---------------------------------------------------------------
def run_bg(cns, seeds, ips):
    derive_prompts.main()
    P = json.load(open(params.PROMPTS_JSON, encoding="utf-8"))
    prompt = f"{derive_prompts.STYLE} {derive_prompts.BG_VOCAB}"
    neg = P["negative"]
    cond = scene_cond()
    sheet = Image.open(STYLE_SHEET).convert("RGB")

    t = time.time()
    cn_model = ControlNetModel.from_pretrained(params.CN_MODEL, torch_dtype=torch.float16)
    pipe = StableDiffusionXLControlNetPipeline.from_pretrained(
        params.SDXL_BASE, controlnet=cn_model, torch_dtype=torch.float16, variant="fp16",
        use_safetensors=True).to("mps")
    pipe.set_progress_bar_config(disable=True)
    pipe.load_ip_adapter(params.IP_ADAPTER_REPO, subfolder=params.IP_ADAPTER_SUBFOLDER,
                         weight_name=params.IP_ADAPTER_WEIGHT)
    n, lim = _tok(pipe, prompt, "배경")
    load_s = time.time() - t
    print(f"로드 {load_s:.0f}s  ·  프롬프트 {n}/{lim}토큰", flush=True)

    times = []
    for ip in ips:
        # 강도 0은 레퍼런스를 **아예 걸지 않는다** — part 2 실측 「화풍은 이미지 레퍼런스를
        # 요구하지 않는다」(텍스트만 CN 0에서 ink .1849)를 이 격자 안에서 대조군으로 두는 칸이다.
        pipe.set_ip_adapter_scale(ip)
        for cn in cns:
            for seed in seeds:
                out = bg_path(cn, seed, ip)
                if os.path.exists(out):
                    print(f"  [스킵] {os.path.basename(out)}")
                    continue
                ts = time.time()
                kw = dict(prompt=prompt, negative_prompt=neg, image=cond,
                          width=params.SCENE_SIZE[0], height=params.SCENE_SIZE[1],
                          controlnet_conditioning_scale=cn,
                          num_inference_steps=params.STEPS, guidance_scale=params.GUIDANCE,
                          generator=torch.Generator("mps").manual_seed(seed))
                if ip > 0:
                    kw["ip_adapter_image"] = sheet
                else:
                    kw["ip_adapter_image"] = Image.new("RGB", sheet.size, (255, 255, 255))
                pipe(**kw).images[0].save(out)
                dt = time.time() - ts
                times.append(dt)
                print(f"  [IP {ip} · CN {cn} · s{seed}] {dt:.0f}s -> {os.path.basename(out)}",
                      flush=True)

    # --- 축 A 곡선 — 손잡이를 시드 전수로 판정한다(PROMPTING.md 5) -----------------
    thr = json.load(open(os.path.join(params.NOTES, "s1-baseline.json"),
                         encoding="utf-8"))["axis_a"]["thresholds"]
    lo, hi = thr["ink_min"], thr["ink_max"]
    print(f"\n축 A — 정답지 구간 ink {lo:.4f}~{hi:.4f} (상한 초과는 경고, s1-baseline "
          f"ink_max_is_warn_only)")
    for ip in ips:
        for cn in cns:
            vals, marks = [], []
            for seed in seeds:
                p = bg_path(cn, seed, ip)
                if not os.path.exists(p):
                    continue
                v = js.style_metrics(p)["ink"]
                vals.append(v)
                marks.append(f"s{seed}={v:.4f}"
                             f"{'✅' if lo <= v <= hi else ('⚠상한' if v > hi else '❌')}")
            if vals:
                n_in = sum(lo <= v <= hi for v in vals)
                print(f"  IP {ip} · CN {cn}: 구간 안 {n_in}/{len(vals)}  "
                      f"중앙값 {np.median(vals):.4f}  " + "  ".join(marks))
    if times:
        print(f"\n배경 실측: 장당 {min(times):.0f}~{max(times):.0f}s (로드 {load_s:.0f}s 별도, "
              f"{len(times)}장)")
    return 0


# --- 인물 단계 ---------------------------------------------------------------
def run_figures(cn, seeds, ip, bg_ip, fig_cn, ref_band=None, head_cn=None, torso_cn=None,
                head_ip=None):
    """인물 단계. `fig_cn`은 **인물 크롭 안의** ControlNet 강도다 — 배경의 `cn`과 다른 축이다.

    기본값을 `params.SCENE_CN`(0.8)에 두지 않고 호출자가 정하게 한 이유: `gen_combined.py`는
    인물 크롭을 「장면의 일부」로 보아 0.8을 걸었으나, **크롭 안의 조건 입력은 선 몇 개뿐인 얇은
    조건**이다. params.py가 그 경우를 이미 적어 두었다 — 「두상 조건은 stroke 4~8개뿐이라 0.8이면
    '이 그림은 이 선이 전부'가 되어 모델이 얼굴 안을 비운다 … 장면 조건은 189선이라 0.8을 그대로
    둔다」. 2026-08-26 실측이 그 예언 그대로였다: `fig_cn=0.8`로 그린 다윗은 배경의 창백한 원뿔
    실루엣에 얼굴만 생기고 전신 표본의 화풍이 전혀 실리지 않았다(PROMPTING.md 11의 문턱과 같은
    현상 — CN ≥ 0.4에서 대비가 0으로 눌린다). 얇은 조건용 정본 값은 `params.PERSON_CN`(0.3)이다.
    """
    derive_prompts.main()
    P = json.load(open(params.PROMPTS_JSON, encoding="utf-8"))
    cond = scene_cond()
    masks = {n: figure_mask(n) for n in PEOPLE}
    refs = {n: Image.open(os.path.join(SAMPLES, f"{n}.png")).convert("RGB") for n in PEOPLE}
    if ref_band is not None:
        # task#322 R3 — `PROMPTING.md` 9: 레퍼런스가 나르는 것은 화풍만이 아니라 **의미**이고,
        # 그 목록에 **자세**가 명시돼 있다(「무장한 영웅 figure(자세·갑주·망토·스탠스)가 CLIP
        # 임베딩으로 개념 자체를 실어 온다」). 같은 규칙이 그에 맞선 **프롬프트 축은 전부 무효**로
        # 실측했다(부정어·긍정전환·CFG 상향 3/3 실패). 따름 정리가 지시하는 처방이 이것이다 —
        # 「레퍼런스는 원하는 속성만 담은 최소 패치로 준다 · 재질은 이미지로, **구도는 콘티로**」.
        # 분율 규약은 `judge_s1._band_fullbody`(HEAD_BAND=0.30)와 같은 것을 쓴다. 규칙 9가 경계한
        # 「크롭 편법」(자산당 손 박스 판독이라 74명으로 확장 안 됨)이 아니다 — 분율은 규칙이라
        # 모든 표본에 같은 식으로 적용된다.
        refs = {n: im.crop((0, 0, im.width, int(im.height * ref_band))) for n, im in refs.items()}
    for name in PEOPLE:
        box = window(masks[name], PAD)
        print(f"  마스크 {name:8s} 화면의 {(np.array(masks[name]) > 127).mean() * 100:.1f}%  "
              f"창 {box}")

    t = time.time()
    cn_model = ControlNetModel.from_pretrained(params.CN_MODEL, torch_dtype=torch.float16)
    pipe = StableDiffusionXLControlNetInpaintPipeline.from_pretrained(
        params.SDXL_BASE, controlnet=cn_model, torch_dtype=torch.float16, variant="fp16",
        use_safetensors=True).to("mps")
    pipe.set_progress_bar_config(disable=True)
    # 레퍼런스는 **1장뿐**이다 — 전신 표본. 화풍 시트를 겹쳐 물리지 않는다(part 2 실측).
    pipe.load_ip_adapter(params.IP_ADAPTER_REPO, subfolder=params.IP_ADAPTER_SUBFOLDER,
                         weight_name=params.IP_ADAPTER_WEIGHT)
    pipe.set_ip_adapter_scale(ip)
    load_s = time.time() - t
    print(f"로드 {load_s:.0f}s  ·  전신 표본 IP {ip}  ·  인물 크롭 CN {fig_cn}  ·  "
          f"배경 IP {bg_ip} · CN {cn}  ·  레퍼런스 "
          f"{'전신 전체' if ref_band is None else f'상단 {ref_band} 밴드'}", flush=True)

    times = []
    for seed in seeds:
        src = bg_path(cn, seed, bg_ip)
        if not os.path.exists(src):
            sys.exit(f"배경이 없다: {src} — 먼저 `gen_final.py bg`를 돌려라")
        canvas = Image.open(src).convert("RGB")
        for step, name in enumerate(PEOPLE, start=1):
            out = os.path.join(OUT, f"{step}-{name}-{tag(cn, bg_ip, fig_cn, ip, ref_band, head_cn, torso_cn, head_ip)}-s{seed}.png")
            if os.path.exists(out):
                print(f"  [스킵] {os.path.basename(out)}")
                canvas = Image.open(out).convert("RGB")
                continue
            m = masks[name]
            box = window(m, PAD)
            bw, bh = box[2] - box[0], box[3] - box[1]
            gw, gh = gen_size(box)
            pr, ng = P["figure"][name]["prompt"], P["figure"][name]["negative"]
            n, lim = _tok(pipe, pr, f"{name} 전신")

            # 그림·마스크·콘티를 **같은 창**으로 자르고 같은 배율로 키운다 — 셋이 어긋나면 안 된다.
            sub_img = canvas.crop(box).resize((gw, gh), Image.LANCZOS)
            sub_msk = m.crop(box).resize((gw, gh), Image.LANCZOS)
            sub_cnd = cond.crop(box).resize((gw, gh), Image.LANCZOS)

            ts = time.time()
            res = pipe(prompt=pr, negative_prompt=ng, image=sub_img, mask_image=sub_msk,
                       control_image=sub_cnd, width=gw, height=gh,
                       controlnet_conditioning_scale=fig_cn, strength=STRENGTH,
                       num_inference_steps=params.STEPS, guidance_scale=params.GUIDANCE,
                       ip_adapter_image=refs[name],
                       generator=torch.Generator("mps").manual_seed(seed)).images[0]
            # 줄여서 **마스크 화소만** 되돌린다 — 경계가 안 바뀐 배경에 떨어져 이음새가 없다.
            canvas.paste(res.resize((bw, bh), Image.LANCZOS), (box[0], box[1]), m.crop(box))
            canvas.save(out)
            dt = time.time() - ts
            times.append(dt)
            print(f"  [{step} {name} s{seed}] {dt:.0f}s  프롬프트 {n}/{lim}토큰  "
                  f"창 {bw}x{bh} → {gw}x{gh} ({gw / bw:.1f}x) -> {os.path.basename(out)}",
                  flush=True)
        # --- 3·4단계: 밴드 인페인팅 (task#322, 2026-08-31 · 사용자 「인페인팅 순서 정해서」) ---
        # 순서는 **굵은 구조 → 세부**이고, 뒤 단계의 마스크가 앞 단계 안에 포개진다:
        #   1 배경(run_bg) → 2 전신(위 루프, fig_cn) → 3 얼굴(head_cn) → 4 몸통(torso_cn)
        # **왜 나누나.** 팔①은 높은 CN이라야 서고 머리③은 낮은 CN이라야 돈다(§9-32) — 하나의
        # `fig_cn`으로는 둘을 동시에 만족 못 한다. 그리고 CN 0.8은 구조를 주고 **내부 질감을
        # 앗아가므로**(§9-33) 몸통도 따로 낮게 다시 그려야 갑주가 산다. 단계마다 CN이 따로이고,
        # 단계마다 **77토큰이 새로 생긴다** — 전신 프롬프트가 74/77이라 방향을 두 단어밖에 못
        # 싣던 제약이 여기서 풀린다.
        for key, spec, boxfn, label, ipspec in (
                ("head", head_cn, lambda w: _judge().conti_head_box(w), "머리", head_ip),
                ("torso", torso_cn, lambda w: _judge().conti_torso_box(w), "몸통", None)):
            if not spec:
                continue
            for who in PEOPLE:
                if who not in spec:
                    continue
                canvas = _band_pass(pipe, canvas, cond, masks, refs, P, key, boxfn(who),
                                    who, spec[who], seed, label,
                                    None if not ipspec else ipspec.get(who), ip)
                canvas.save(os.path.join(
                    OUT, f"{key[0]}-{who}-{tag(cn, bg_ip, fig_cn, ip, ref_band, head_cn, torso_cn, head_ip)}"
                         f"-s{seed}.png"))
        final = os.path.join(OUT, f"3-final-{tag(cn, bg_ip, fig_cn, ip, ref_band, head_cn, torso_cn, head_ip)}-s{seed}.png")
        canvas.save(final)
        print(f"  최종: {os.path.basename(final)}")
    if times:
        print(f"\n인물 실측: 장당 {min(times):.0f}~{max(times):.0f}s (로드 {load_s:.0f}s 별도, "
              f"{len(times)}장)")
    return 0


def main():
    os.makedirs(OUT, exist_ok=True)
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=("bg", "figures"))
    ap.add_argument("--cns", default="0.8,0.4,0.2", help="배경 단계 ControlNet 강도 목록")
    ap.add_argument("--ips", default="1.0", help="배경 단계 화풍 시트 IP 강도 목록(0 = 레퍼런스 없음)")
    ap.add_argument("--cn", default=None, help="인물 단계가 물려받을 배경의 CN")
    ap.add_argument("--bg-ip", default=None, help="인물 단계가 물려받을 배경의 시트 IP 강도")
    ap.add_argument("--seeds", default=",".join(str(s) for s in params.SCENE_SEEDS))
    ap.add_argument("--ip", type=float, default=None, help="인물 단계 전신 표본 IP 강도")
    ap.add_argument("--ref-band", type=float, default=None,
                    help="인물 IP 레퍼런스를 전신 표본 **상단 이 분율**로 좁힌다(예: 0.30 — "
                         "judge_s1._band_fullbody와 같은 규약). 생략하면 종전대로 전신 전체를 쓴다")
    ap.add_argument("--fig-cn", default=None,
                    help="인물 크롭 안의 ControlNet 강도. 기본은 얇은 조건용 정본값 "
                         "params.PERSON_CN — 장면용 SCENE_CN(0.8)은 크롭 안에서 대비를 0으로 "
                         "누른다(2026-08-26 실측, run_figures docstring 참조)")
    ap.add_argument("--head-cn", default=None,
                    help="머리 단계를 켠다 — 인물 단계 위에 **머리 밴드만** 이 CN으로 다시 그린다. "
                         "생략하면 머리 단계를 돌리지 않는다(태그도 종전 그대로, 역호환). "
                         "팔은 높은 fig_cn이, 머리 회전은 낮은 CN이 필요해 둘을 분리한 것이다(§9-32). "
                         "`0.0`은 두 인물 다, `david=0.0`은 다윗만, `david=0.0,goliath=0.5`는 인물별")
    ap.add_argument("--head-ip", default=None,
                    help="머리 단계 전용 표본 IP 강도(형식은 --head-cn과 같다). 생략하면 전신과 "
                         "같은 --ip를 쓴다. 머리 단계 레퍼런스는 표본 상단 밴드 = **정면 얼굴**이라 "
                         "회전을 막는다 — 그 앵커만 이 단계에서 낮춘다")
    ap.add_argument("--torso-cn", default=None,
                    help="몸통 단계를 켠다 — 몸통 밴드만 이 CN으로 다시 그려 갑주·의상 질감을 "
                         "되찾는다(CN 0.8이 내부를 비운다, §9-33). 형식은 --head-cn과 같다")
    a = ap.parse_args()
    seeds = [int(s) for s in a.seeds.split(",")]
    if a.stage == "bg":
        return run_bg([float(c) for c in a.cns.split(",")], seeds,
                      [float(v) for v in a.ips.split(",")])
    if a.cn is None or a.bg_ip is None:
        sys.exit("`figures`는 --cn 과 --bg-ip 로 어느 배경을 물려받을지 지정해야 한다")
    return run_figures(float(a.cn), seeds, params.IP_SCALE if a.ip is None else a.ip,
                       float(a.bg_ip),
                       params.PERSON_CN if a.fig_cn is None else float(a.fig_cn),
                       a.ref_band, _stage_spec(a.head_cn), _stage_spec(a.torso_cn),
                       _stage_spec(a.head_ip))


if __name__ == "__main__":
    sys.exit(main())
