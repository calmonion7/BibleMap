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

import numpy as np
import torch
from diffusers import StableDiffusionXLInpaintPipeline
from PIL import Image, ImageFilter

import params

sys.path.insert(0, params.CANON_DIR)
import derive_prompts as dp  # noqa: E402

OUT = os.path.join(params.OUT_ROOT, "scripture-scene")
W, H = params.SCENE_SIZE
STRENGTH = 0.99          # 새 내용을 만드는 단계 — 구역 안을 사실상 새로 그린다
REFINE_STRENGTH = 0.55   # **이미 있는 것을 다듬는 단계**(얼굴). 1에 가까우면 모델이 그 자리에
                         # 새 그림을 그려 얼굴이 둘이 된다(2026-08-31 v4 실측: 다윗 얼굴이 별도의
                         # 큰 초상으로 생겼다). 낮은 strength가 「고치기」의 도구다.
FEATHER = 0.06           # 마스크 깃털 = 구역 짧은 변의 분율. 고정 px는 큰 구역에서 상자 변을
                         # 드러낸다(머리 단계 실측: 고정 6px에서 네모 이음매가 보였다).

# --- 구역 명세 — 캔버스 분율. **좌표가 있는 곳은 여기 한 곳뿐이다.** -----------------
# 크기 대비의 근거: 골리앗 세로 0.90 · 다윗 0.48 = 1.87배 ↔ 17:4 「여섯 규빗 한 뼘」(약 2.9m)
# 대 소년(약 1.6m). 좌우 배치는 17:2-3(양쪽 산)과 17:41·48(서로 마주 나아감)에서 온다.
REGIONS = {
    "full":         (0.00, 0.00, 1.00, 1.00),
    "crest_left":   (0.02, 0.24, 0.44, 0.47),   # 이스라엘 쪽 산등성이 (17:2-3) — 1차에서 구역이
                                                # 커서 「멀리 작은 인물」이 안 잡혔다. 능선 선에 얇게 붙인다.
    "crest_right":  (0.56, 0.18, 0.99, 0.43),   # 블레셋 쪽 산등성이
    # 종횡비를 사람 비율로 좁힌다 — 0.68은 텐트/원뿔의 prior에 가깝고, v7에서 실제로 텐트가 나왔다.
    "goliath":      (0.625, 0.05, 0.855, 0.95),  # 거인 (17:4 신장) · 비율 0.51
    "shieldman":    (0.44, 0.52, 0.585, 0.94),  # 방패 든 자 — 골리앗 **앞**(=더 가까이·아래) (17:7·41)
    "david":        (0.15, 0.52, 0.305, 0.92),  # 소년 — 세로 0.40. 골리앗 0.90 대비 2.25배로
                                                # 잡아 실측이 1.8 근처로 떨어지게 한다(v8은 1.4였다)
    # ⚠ 1차 실측: 이 구역이 0.10~0.46 × 0.22~0.82이라 **다윗 상반신을 덮어 S5의 소년을 지우고**
    # 노인을 그렸고, 그 탓에 크기 대비까지 무너졌다. **다윗 몸에 겹치지 않는 얇은 띠**로 줄인다 —
    # 머리 위로 휘두르는 물매 호만 담는다. 막대기는 S5 프롬프트로 옮겼다(겹침 위험 제거).
    "sling_arc":    (0.15, 0.26, 0.42, 0.44),
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
     NEG + ", people, figures, soldiers, flat plain, open field"),   # ⚠ v10에서 `grid·stripes·ruled paper`를
     # 부정어에 넣었더니 **화면 전체에 격자가 나타났다**(부정어 누출). 도로 뺀다 — 부정어는
     # 낱말을 지우는 도구가 아니라 확률을 미는 도구여서, 없던 개념을 불러오는 쪽으로도 작동한다.
    ("S2a", "crest_left", 17.2, f"{ST} hundreds of tiny distant soldiers packed shoulder to "
                                f"shoulder in long ranks on the hillside, a dense forest of small "
                                f"upright spears, tiny far away crowd.",
     NEG + ", empty hill, bare ridge, single figure, close-up"),
    ("S2b", "crest_right", 17.3, f"{ST} hundreds of tiny distant soldiers packed shoulder to "
                                 f"shoulder in long ranks on the hillside, a dense forest of small "
                                 f"upright spears, tiny far away crowd.",
     NEG + ", empty hill, bare ridge, single figure, close-up"),
    # ⓑ **갑주를 프롬프트로 찾는다**(2026-08-31 사용자 지시). 기록의 실패는 「중립적 갑옷 낱말이
    # 모델의 기사 사전지식에 4회 연속 졌다 — 판금·면갑·망토·대검으로 수렴」이고, **통한 방향은
    # `barbaric` 레지스터**였다(PROMPTING.md 8 · SAMPLE_COSTUME 주석). 1차 실행에서 내가 정본
    # 문구를 쓰지 않고 줄여 쓴 것도 실패 요인이다. 그래서 셋을 함께 건다:
    #   ① 의상은 **정본 문구 그대로**(dp.SAMPLE_COSTUME — 표본·전신과 같은 출처)
    #   ② 야만인 레지스터로 기사 사전지식을 밀어낸다
    #   ③ **수렴 대상 네 가지를 부정어로 직접 막는다**(판금·면갑·망토·대검)
    # ⚠ v7 정정 — **부정어를 과하게 걸어 역효과가 났다.** plate·knight·cape·cloak·sword·
    # breastplate를 한꺼번에 막으니 모델이 「갑옷 입은 사람」을 그릴 손잡이를 다 잃고 **반투명
    # 텐트**를 그렸다(비늘 무늬가 사람이 아니라 원뿔 꼭대기에 붙었다). 기록의 교훈은 「중립 갑옷
    # 낱말이 기사 prior에 졌고 통한 것은 barbaric 레지스터」였지 갑옷 낱말을 지우라는 것이 아니다.
    # 그래서 ① **사람 낱말을 맨 앞에** 두어 형태 prior를 사람으로 잡고 ② 부정어는 뿔·판금·기사
    # 셋만 남긴다.
    ("S3", "goliath", 17.5, f"{ST} full body of a huge bronze age Philistine warrior man, "
                            # `nine feet tall`을 뺐다 — 크기는 **구역 상자가 정한다**(실측
                            # 골리앗:다윗 1.9배). 문구로 중복해 말할 토큰이 없다(78/77 초과했다).
                            f"plain bronze helmet, "
                            f"{dp.SAMPLE_COSTUME['goliath'][3:]}, bronze greaves, holding one "
                            f"thick heavy spear, seen from the side, body and face turned left.",
     # `barbaric`은 기사 prior를 밀어냈지만 **맨가슴**을 불러 어린갑과 상충했다(v8 실측).
     # 청동기·블레셋이라는 **시대·민족 레지스터**로 바꾼다 — 중세 판금을 배제하면서 옷은 안 벗긴다.
     NEG + ", horns, horned helmet, plate armour, knight, medieval, tent, cone, robe, "
            "bare chest, shirtless, naked torso"),
    ("S4", "shieldman", 17.7, f"{ST} full body of a Philistine shield bearer walking on the "
                              f"ground ahead of the giant, holding a large round bronze shield, "
                              f"plain tunic, facing left.",
     NEG + ", oval, circle, medallion, vignette, inset, floating"),
    ("S5", "david", 17.40, f"{ST} a small ruddy shepherd boy of fifteen, no armour, plain "
                           f"linen tunic with a cloth belt, a shepherd's bag at his side, "
                           f"whirling a small leather sling on short cords in his raised hand, "
                           f"running forward, facing right.",
     NEG + ", armour, helmet, sword, beard, old man, grey hair, robe, tall adult"),
    ("S9", "sling_arc", 17.40, # ⚠ 「above the boy's head」라고 쓰자 모델이 **머리를 그렸다**(v4·v6 실측: 왼쪽 위에 큰 얼굴).
     # 이 단계는 지물만 그려야 하므로 인물 낱말을 한 개도 넣지 않는다.
     # v9에서 S5 프롬프트에 합쳤더니 **손이 빈 채로** 나왔다 — 지물은 자기 단계가 있어야 한다.
     # 구역은 다윗 실루엣 상단에서 파생해 **손 근처**에 둔다(허공에 따로 그리면 해먹으로 읽혔다).
     f"{ST} a small leather sling held up in a boy's hand, two short "
                                 f"taut cords and a small pouch holding one round stone, "
                                 f"close to the hand.",
     NEG + ", staff, pole, club, flag, banner, rope, head, face, person, boy, figure"),
    ("S7", "david_head", 17.42, f"{ST} head of a ruddy boy of fifteen, clean-shaven, curly hair, "
                                f"bare head, strict side profile facing right, eyes on the giant.",
     NEG + ", " + dp.HEAD_NEG_EXTRA),
    ("S8_DROPPED", "goliath_head", 17.5, f"{ST} head of a grown man of about forty, clean-shaven, no hair "
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


SKIP = {"S8_DROPPED"}
# S6: v8까지 물매를 허공에 따로 그렸더니 **해먹·그물**로 읽혔다.
                               # 손에 쥔 것으로 S5에 합친다 — 떠 있는 지물이 오독의 원인이었다.
# S8(골리앗 얼굴)도 폐기했다 — v9 실측: 다듬기 단계가 머리를 다시 그리며 **놋투구를 지워
# 대머리로** 만들었다. 그리고 S3만으로 이미 왼쪽을 보므로 이 단계는 순손실이다.
REFINE_STAGES = {"S7"}   # 다듬는 단계 — REFINE_STRENGTH를 쓴다
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


def _change_mask(new_im, old_im):
    """**앞 단계 대비 바뀐 화소** = 이 단계가 실제로 그린 것. 사각 상자 대신 이것으로 되붙인다.

    **왜 필요한가**(2026-08-31 v4·v5 실측):
    ① v4 — 구역 마스크가 사각형이라 창 안의 **배경까지** 새로 칠해 붙었고, 단계마다 그 사각형이
       드러나 그림이 **콜라주**가 됐다(콘티 파이프라인은 마스크가 인물 볼록껍질이라 이 문제가 없었다).
    ② v5 — 그래서 「종이색이 아닌 화소」를 실루엣으로 썼더니 **옅게 그려진 골리앗이 통째로
       버려졌다.** 절대 밝기 기준은 옅은 인물을 못 잡는다.
    그래서 기준을 **변화량**으로 바꾼다. 이 단계가 그린 곳은 앞 단계와 다르고, 손대지 않은
    배경은 (같은 프롬프트 맥락에서 다시 그려도) 거의 같다 — 밝기와 무관하게 자기 보정된다.
    임계는 `params.THRESHOLD`를 그대로 쓴다(파이프라인 전체가 쓰는 잉크 판정 임계)."""
    a = np.asarray(new_im.convert("L")).astype(int)
    b = np.asarray(old_im.convert("L")).astype(int)
    return Image.fromarray(((np.abs(a - b) > params.THRESHOLD) * 255).astype(np.uint8), "L")


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
    # **갑주에만 이미지 앵커를 붙인다**(2026-08-31). 어린갑은 v3~v9까지 **일곱 번 어휘로 실패**했고
    # (barbaric → 맨가슴 · 청동기 레지스터 → 줄무늬 튜닉 · 정본 문구도 무효), `PROMPTING.md` 8이
    # 이미 「어휘 6종 0/6 · 이미지 앵커만 통했다」로 적어 둔 자리다. 같은 실패를 여덟 번째로
    # 반복하지 않는다. 레퍼런스는 **동결 표본의 몸통 밴드** — 콘티가 아니라 표본이므로 「콘티를
    # 쓰지 말자」는 지시와 어긋나지 않고, 그 밴드에 실제 비늘갑이 있다.
    pipe.load_ip_adapter(params.IP_ADAPTER_REPO, subfolder=params.IP_ADAPTER_SUBFOLDER,
                         weight_name=params.IP_ADAPTER_WEIGHT)
    pipe.set_ip_adapter_scale(0.0)          # 기본 꺼짐 — 갑주 단계에서만 켠다
    _g = Image.open(os.path.join(params.CANON_DIR, "samples", "goliath.png")).convert("RGB")
    ARMOUR_REF = _g.crop((0, int(_g.height * 0.28), _g.width, int(_g.height * 0.62)))
    print(f"로드 {time.time() - t:.0f}s  ·  ControlNet 없음 · IP 레퍼런스 없음 — "
          f"서술은 전부 텍스트가 진다", flush=True)

    for seed in seeds:
        # S1은 빈 종이색 캔버스를 전체 인페인팅한다 — text2img와 같고 파이프라인이 하나면 된다.
        canvas = Image.new("RGB", (W, H), (247, 240, 226))
        drawn = {}   # 단계별 실제로 그려진 실루엣 bbox — 머리 상자를 여기서 파생한다
        for name, region, verse, prompt, neg in STAGES:
            if name in SKIP or (pick is not None and name not in pick):
                continue
            # **머리 상자는 저작하지 않고 실루엣에서 파생한다.** v8까지 골리앗 머리 상자가
            # y 0.05~0.30에 고정돼 있었는데 구역을 좁히며 그의 머리가 내려가, S8이 **빈 하늘을
            # 칠하고 있었다**(그래서 얼굴 단계가 「거의 안 먹는다」로 보였다).
            src = {"S7": "S5", "S9": "S5"}.get(name)
            if src and src in drawn:
                x0, y0, x1, y1 = drawn[src]
                if name == "S9":
                    # 물매는 **든 손 크기**여야 한다. v10·v11에서 마스크가 다윗 몸통만 해서
                    # 「거대한 팔」이 나왔다 — 창을 고쳐도 **마스크가 크면 큰 것을 그린다.**
                    fw, fh = x1 - x0, y1 - y0
                    b = (x0 + int(fw * 0.62), max(0, y0 - int(fh * 0.06)),
                         min(W, x0 + int(fw * 1.06)), y0 + int(fh * 0.20))
                else:
                    hh = int(round((y1 - y0) * 0.30))      # 인물 상단 30% = 머리·어깨
                    b = (x0, y0, x1, y0 + hh)
                m = Image.new("L", (W, H), 0)
                m.paste(255, b)
                m = m.filter(ImageFilter.GaussianBlur(
                    max(4, int(round(FEATHER * min(b[2] - b[0], b[3] - b[1]))))))
            else:
                b = box_px(region)
                m = region_mask(region)
            n, lim = _tok(pipe, prompt, f"{name} {region}")
            # **구역만 잘라 1024로 키워 생성하고 되붙인다.** 전체 캔버스를 strength 0.99로
            # 넘기면 이미지 전체가 재노이즈되어 구역 내용이 **주변과 무관하게** 나오고, 단계마다
            # 쓰레기가 누적된다(2026-08-31 1차 실행에서 그렇게 무너졌다). 기존에 작동하던
            # `gen_final.run_figures`가 쓰는 패턴이 이것이다 — 창 크롭 → 확대 → 인페인팅 → 되붙임.
            # **창(맥락)과 마스크(칠할 곳)를 분리한다.** v10 실측: 작은 파생 구역(158×175)을
            # 1024로 확대하니 모델이 **클로즈업**을 그려 「거대한 손」·「인형 얼굴」이 나왔다.
            # 옛 콘티 파이프라인은 창 = 인물창 + 여백, 마스크 = 인물 실루엣으로 분리돼 있었다.
            win = _window(drawn[src]) if (src and src in drawn) else _window(b)
            gw, gh = _gen_size(win)
            ts = time.time()
            refine = name in REFINE_STAGES
            use_ip = name == "S3"
            # 앵커 강도 — v10의 0.55는 비늘을 살렸지만 **표본의 정면성까지** 실어 왔다.
            # 낮춰서 재질만 남기는 지점을 찾는다(레퍼런스가 자세를 나른다는 PROMPTING.md 9).
            pipe.set_ip_adapter_scale(0.25 if use_ip else 0.0)
            res = pipe(prompt=prompt, negative_prompt=neg,
                       image=canvas.crop(win).resize((gw, gh), Image.LANCZOS),
                       mask_image=m.crop(win).resize((gw, gh), Image.LANCZOS),
                       width=gw, height=gh,
                       strength=REFINE_STRENGTH if refine else STRENGTH,
                       num_inference_steps=params.STEPS,
                       guidance_scale=params.GUIDANCE,
                       ip_adapter_image=ARMOUR_REF if use_ip else Image.new("RGB", (8, 8)),
                       generator=torch.Generator("mps").manual_seed(seed)).images[0]
            ww, wh = win[2] - win[0], win[3] - win[1]
            back = res.resize((ww, wh), Image.LANCZOS)
            if name == "S1":
                # 지형은 화면 전체다. **마스크를 쓰지 않고 통째로 갈아끼운다** — 부분 마스크로
                # 전체를 칠하면 캔버스 경계에서 가로 줄무늬 글리치가 남는다(v3~v8 실측).
                canvas = back
                print(f"  [{name} {region} 17:1] {time.time() - ts:.0f}s  {n}/{lim}토큰  전체 교체",
                      flush=True)
                continue
            else:
                # **실루엣으로 되붙인다** — 사각 상자를 붙이면 그 변이 드러나 콜라주가 된다.
                sil = _change_mask(back, canvas.crop(win))
                # **형태학적 닫기(팽창 → 침식)로 내부 구멍을 메운다.** v6 실측: 옅게 그려진
                # 골리앗의 **내부**에서 변화량이 임계 아래라 구멍이 뚫려 그가 반투명해졌다.
                # 반지름은 구역 짧은 변에서 판다(고정값은 큰 구역에서 부족하다).
                r = max(3, int(round(0.035 * min(ww, wh))))
                k = 2 * r + 1
                sil = sil.filter(ImageFilter.MaxFilter(k)).filter(ImageFilter.MinFilter(k))
                sil = sil.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(4))
                paste_m = Image.composite(sil, Image.new("L", sil.size, 0), m.crop(win))
            canvas.paste(back, (win[0], win[1]), paste_m)
            bb = paste_m.point(lambda v: 255 if v > 40 else 0).getbbox()
            if bb:
                drawn[name] = (win[0] + bb[0], win[1] + bb[1], win[0] + bb[2], win[1] + bb[3])
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
