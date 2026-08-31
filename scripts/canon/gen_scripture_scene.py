#!/usr/bin/env python3
"""본문 기반 단계 인페인팅 장면 생성기 (2026-08-31, 사용자 재설계 지시).

**콘티를 쓰지 않는다.** 사용자 지시: 「콘티 사용하지말자 / 장면에 사용할 설명을 성경 내용을
충실히 만든 다음 / 토큰한계를 고려하여 프롬프트를 만들고 프롬프팅 순서를 정하고 인페인팅
방법으로 그림제작 / 1. 프롬프팅 → 그림1번 / 2. 1번그림, 프롬프팅 → 그림2번 / …」

**왜 이 구조인가 — 실측이 강제한다.**
  · 단일 프롬프트는 77토큰이라 장면 서술을 못 담는다. 골리앗 전신이 74/77이어서 방향을 두
    단어(`facing left`)밖에 못 실었고, 상세 후보는 79/77로 기각된 기록이 있다(§9-39).
    **단계마다 77이 새로 생기므로** 여덟 단계로 나누면 예산이 74 → 합계 444가 된다.
  · 콘티(ControlNet)는 「있고 없음」은 나르지만 「모양·방향」은 못 나른다(§9-32). 대신 정면 원
    머리가 시선을 못박는 대가를 치렀다. 텍스트 단계화는 그 대가 없이 서술을 싣는다.
  · 콘티를 빼면 판정 축 C·D·G가 파생원을 잃는다(§9-33의 소거 실험). 그 대체는 이 파일의
    `REGIONS`다 — 콘티도 사람이 저작한 것이었으므로 저작 층이 바뀐 것이고, 축 B·E·F가 쓰던
    인물창·머리밴드·몸통밴드는 여기서 다시 파생할 수 있다.

장면 명세는 `notes/SCENE-1SAM17.md`가 진다 — **요소마다 출처 절이 달려 있다.** 이 파일은
그 명세의 구역과 순서를 코드로 옮긴 것이고, 새 서술을 발명하지 않는다.

Usage:
  .../python gen_scripture_scene.py --seeds 11,42,7 [--stages S1,S2,...] [--label v1]
"""
import argparse
import os
import sys
import time

import torch
from diffusers import StableDiffusionXLInpaintPipeline
from PIL import Image, ImageFilter

import params

sys.path.insert(0, params.CANON_DIR)
import derive_prompts as dp  # noqa: E402

OUT = os.path.join(params.OUT_ROOT, "scripture-scene")
W, H = params.SCENE_SIZE
STRENGTH = 0.99          # 구역 안을 사실상 새로 그린다(기존 파이프라인과 같은 값)
FEATHER = 0.06           # 마스크 깃털 = 구역 짧은 변의 분율. 고정 px는 큰 구역에서 상자 변을
                         # 드러낸다(머리 단계 실측: 고정 6px에서 네모 이음매가 보였다).

# --- 구역 명세 — 캔버스 분율. **좌표가 있는 곳은 여기 한 곳뿐이다.** -----------------
# 크기 대비의 근거: 골리앗 세로 0.90 · 다윗 0.48 = 1.87배 ↔ 17:4 「여섯 규빗 한 뼘」(약 2.9m)
# 대 소년(약 1.6m). 좌우 배치는 17:2-3(양쪽 산)과 17:41·48(서로 마주 나아감)에서 온다.
REGIONS = {
    "full":         (0.00, 0.00, 1.00, 1.00),
    "crest_left":   (0.02, 0.30, 0.40, 0.40),   # 이스라엘 쪽 산등성이 (17:2-3) — 1차에서 구역이
                                                # 커서 「멀리 작은 인물」이 안 잡혔다. 능선 선에 얇게 붙인다.
    "crest_right":  (0.60, 0.26, 0.98, 0.36),   # 블레셋 쪽 산등성이
    "goliath":      (0.58, 0.05, 0.90, 0.95),   # 거인 (17:4 신장)
    "shieldman":    (0.46, 0.46, 0.60, 0.95),   # 방패 든 자 — 골리앗 **앞** (17:7·41)
    "david":        (0.13, 0.44, 0.34, 0.92),   # 소년
    "david_props":  (0.10, 0.22, 0.46, 0.82),   # 막대기 + 머리 위로 휘두르는 물매 (17:40)
    "david_head":   (0.185, 0.44, 0.29, 0.575),
    "goliath_head": (0.635, 0.05, 0.795, 0.30),
}

# --- 단계 — 순서는 **먼 것 → 가까운 것, 큰 것 → 작은 것**이다. 뒤 단계가 앞을 덮으므로
# 원근과 가림이 저절로 맞는다(방패 든 자가 골리앗 앞에 서는 것이 17:7·41이다).
ST = dp._drop(dp.STYLE, "simple", "clean background", "light shading", "muted palette")
NEG = dp._drop(dp.NEG, "dark", "heavy shadows") + (
    # 2026-08-31 실측: NEG에 이미 `frame, border`가 있는데도 **액자·매트가 그려졌다**.
    # 종이 화풍(「미색 종이」)이 「종이에 붙인 그림」으로 읽힌 것으로 보고 액자류를 늘린다.
    ", framed, picture frame, matte, passepartout, vignette, paper edge, torn paper")

STAGES = [
    # 17:3 「블레셋 사람은 이편 산에 섰고 이스라엘은 저편 산에 섰고 사이에는 골짜기가 있었더라」
    # — 1차 실측에서 열린 평야가 나왔다. **두 산과 그 사이 골짜기**를 문장 앞으로 당겨 세게 민다.
    ("S1", "full", 17.1, f"{ST} two facing hillsides with a deep dry valley between them, "
                         f"a hill on the left and a hill on the right, sunbaked stony ground, "
                         f"a dry brook with smooth stones, sparse dry grass, no people.",
     NEG + ", people, figures, soldiers, flat plain, open field"),
    ("S2a", "crest_left", 17.2, f"{ST} a long dense row of tiny distant soldiers lined up "
                                f"shoulder to shoulder along the hill crest, a forest of small "
                                f"spears, seen from very far away.", NEG + ", empty hill, bare ridge"),
    ("S2b", "crest_right", 17.3, f"{ST} a long dense row of tiny distant soldiers lined up "
                                 f"shoulder to shoulder along the hill crest, a forest of small "
                                 f"spears, seen from very far away.", NEG + ", empty hill, bare ridge"),
    ("S3", "goliath", 17.5, f"{ST} a towering giant warrior nine feet tall, plain bronze helmet, "
                            f"coat of overlapping bronze scales, bronze greaves on his shins, "
                            f"a short javelin between his shoulders, a huge thick spear like a "
                            f"weaver's beam, facing left.", NEG + ", horns, horned helmet"),
    ("S4", "shieldman", 17.7, f"{ST} a Philistine shield bearer walking ahead of the giant, "
                              f"holding a large round bronze shield, plain tunic, facing left.", NEG),
    ("S5", "david", 17.40, f"{ST} a ruddy shepherd boy of fifteen, no armour, plain linen tunic "
                           f"with a cloth belt, a shepherd's bag at his side, running forward and "
                           f"swinging a sling overhead, facing right.", NEG + ", armour, helmet, sword"),
    ("S6", "david_props", 17.41, f"{ST} a plain wooden shepherd's staff in his left hand, a leather "
                                 f"sling with two long cords whirling above his head, one smooth "
                                 f"stone in the sling pouch.", NEG),
    ("S7", "david_head", 17.42, f"{ST} head of a ruddy boy of fifteen, clean-shaven, curly hair, "
                                f"bare head, strict side profile facing right, eyes on the giant.",
     NEG + ", " + dp.HEAD_NEG_EXTRA),
    ("S8", "goliath_head", 17.5, f"{ST} head of a grown man of about forty, clean-shaven, no hair "
                                 f"showing, plain bronze helmet with cheek guards, strict side "
                                 f"profile facing left, eyes on the boy.",
     NEG + ", " + dp.HEAD_NEG_EXTRA + ", horns"),
]


def box_px(name):
    x0, y0, x1, y1 = REGIONS[name]
    return (int(x0 * W), int(y0 * H), int(x1 * W), int(y1 * H))


def region_mask(name):
    """구역 마스크 — 상자 + 깃털. 깃털은 구역 짧은 변에서 판다(고정 px는 큰 구역에서 변이 드러난다)."""
    b = box_px(name)
    m = Image.new("L", (W, H), 0)
    m.paste(255, b)
    f = max(4, int(round(FEATHER * min(b[2] - b[0], b[3] - b[1]))))
    return m.filter(ImageFilter.GaussianBlur(f))


PAD = 0.10        # 구역 둘레 맥락 여백(구역 짧은 변의 분율) — 모델이 이어붙일 주변을 봐야 한다
TARGET = 1024     # 생성 해상도(긴 변) — gen_final.TARGET과 같은 값·같은 이유


def _window(b):
    """구역 + 맥락 여백, 캔버스 안으로 클램프. gen_final.window와 같은 구실."""
    pad = int(round(PAD * min(b[2] - b[0], b[3] - b[1])))
    return (max(0, b[0] - pad), max(0, b[1] - pad),
            min(W, b[2] + pad), min(H, b[3] + pad))


def _gen_size(win):
    w, h = win[2] - win[0], win[3] - win[1]
    sc = TARGET / max(w, h)
    return max(8, round(w * sc / 8) * 8), max(8, round(h * sc / 8) * 8)


def _tok(pipe, prompt, label):
    n = len(pipe.tokenizer(prompt).input_ids)
    lim = pipe.tokenizer.model_max_length
    if n > lim:
        sys.exit(f"{label} 프롬프트가 한도를 넘었다({n}/{lim}) — 뒤가 조용히 잘린다")
    return n, lim


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", default=",".join(str(s) for s in params.SCENE_SEEDS))
    ap.add_argument("--stages", default=None, help="쉼표로 단계 이름 일부만(기본 전부)")
    ap.add_argument("--label", default="v1")
    a = ap.parse_args()
    seeds = [int(s) for s in a.seeds.split(",")]
    pick = None if a.stages is None else set(a.stages.split(","))
    os.makedirs(OUT, exist_ok=True)

    t = time.time()
    pipe = StableDiffusionXLInpaintPipeline.from_pretrained(
        params.SDXL_BASE, torch_dtype=torch.float16, variant="fp16",
        use_safetensors=True).to("mps")
    pipe.set_progress_bar_config(disable=True)
    print(f"로드 {time.time() - t:.0f}s  ·  ControlNet 없음 · IP 레퍼런스 없음 — "
          f"서술은 전부 텍스트가 진다", flush=True)

    for seed in seeds:
        # S1은 빈 종이색 캔버스를 전체 인페인팅한다 — text2img와 같고 파이프라인이 하나면 된다.
        canvas = Image.new("RGB", (W, H), (247, 240, 226))
        for name, region, verse, prompt, neg in STAGES:
            if pick is not None and name not in pick:
                continue
            b = box_px(region)
            m = region_mask(region)
            n, lim = _tok(pipe, prompt, f"{name} {region}")
            # **구역만 잘라 1024로 키워 생성하고 되붙인다.** 전체 캔버스를 strength 0.99로
            # 넘기면 이미지 전체가 재노이즈되어 구역 내용이 **주변과 무관하게** 나오고, 단계마다
            # 쓰레기가 누적된다(2026-08-31 1차 실행에서 그렇게 무너졌다). 기존에 작동하던
            # `gen_final.run_figures`가 쓰는 패턴이 이것이다 — 창 크롭 → 확대 → 인페인팅 → 되붙임.
            win = _window(b)
            gw, gh = _gen_size(win)
            ts = time.time()
            res = pipe(prompt=prompt, negative_prompt=neg,
                       image=canvas.crop(win).resize((gw, gh), Image.LANCZOS),
                       mask_image=m.crop(win).resize((gw, gh), Image.LANCZOS),
                       width=gw, height=gh,
                       strength=STRENGTH, num_inference_steps=params.STEPS,
                       guidance_scale=params.GUIDANCE,
                       generator=torch.Generator("mps").manual_seed(seed)).images[0]
            ww, wh = win[2] - win[0], win[3] - win[1]
            canvas.paste(res.resize((ww, wh), Image.LANCZOS), (win[0], win[1]), m.crop(win))
            out = os.path.join(OUT, f"{a.label}-{name}-s{seed}.png")
            canvas.save(out)
            print(f"  [{name} {region} 17:{str(verse).split('.')[1]}] {time.time() - ts:.0f}s  "
                  f"{n}/{lim}토큰  상자 {b} -> {os.path.basename(out)}", flush=True)
        final = os.path.join(OUT, f"{a.label}-final-s{seed}.png")
        canvas.save(final)
        print(f"  최종: {os.path.basename(final)}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
