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
import judge_scene as J  # noqa: E402  — 판정자와 **같은 하늘선 산식**을 쓴다(자와 그림이 어긋나면 안 된다)

OUT = os.path.join(params.OUT_ROOT, "scripture-scene")
W, H = params.SCENE_SIZE
# **단계별 strength** — 이음매와 「그린 것의 세기」가 상반된다(2026-09-01 실측, notes §12 판별표).
# 이미 그려진 지형 위에 **큰 상자**를 얹는 단계는 0.99면 상자 안 배경까지 새로 칠해 변화 마스크가
# 상자 전체가 되고, 그 테두리가 직사각 잔상으로 붙는다(언덕오른쪽 .989 · 거인 .542).
# 낮추면 아래를 보고 이어 그린다. 다만 **작은 상자까지 낮추면 인물이 지워진다**(다윗 잉크 .093→.035).
STRENGTH_BY_STAGE = {
    "S1":  0.99,   # 빈 종이색 캔버스에서 시작 — 통째로 새로 그린다
    "S1b": 0.95,   # 언덕은 **지형을 바꿔야** 하므로 이어붙임보다 세기가 우선(이음매 여유 .148~.204)
    "S1c": 0.95,
    "S2a": 0.85,   # 능선 위 군중 — 이어 그려야 배경이 안 갈라진다
    "S2b": 0.85,
    "S3":  0.85,   # 거인 상자가 가장 커서 이음매가 가장 잘 난다
    "S4":  0.99,   # 작은 상자 — 0.85까지 낮추면 **사라진다**(다윗 잉크 .093→.035, v21).
    "S5":  0.99,   # ⚠ 0.93으로 낮춰 봤다(v30): 이음매는 .342 → .403으로 **악화**했고 화풍만
                   # 좋아졌다(비 1.27 → 1.12). 이 둘의 이음매는 strength로 안 잡힌다.
}
DEFAULT_STRENGTH = 0.99
REFINE_STRENGTH = 0.72   # v12까지 0.55로는 고개를 못 돌렸다(다윗이 숙인 채였다).
                         # **이미 있는 것을 다듬는 단계**(얼굴). 1에 가까우면 모델이 그 자리에
                         # 새 그림을 그려 얼굴이 둘이 된다(2026-08-31 v4 실측: 다윗 얼굴이 별도의
                         # 큰 초상으로 생겼다). 낮은 strength가 「고치기」의 도구다.
FEATHER = 0.06           # 마스크 깃털 = 구역 짧은 변의 분율. 고정 px는 큰 구역에서 상자 변을
                         # 드러낸다(머리 단계 실측: 고정 6px에서 네모 이음매가 보였다).

# --- 구역 명세 — 캔버스 분율. **좌표가 있는 곳은 여기 한 곳뿐이다.** -----------------
# 크기 대비의 근거: 골리앗 세로 0.90 · 다윗 0.48 = 1.87배 ↔ 17:4 「여섯 규빗 한 뼘」(약 2.9m)
# 대 소년(약 1.6m). 좌우 배치는 17:2-3(양쪽 산)과 17:41·48(서로 마주 나아감)에서 온다.
REGIONS = {
    "full":         (0.00, 0.00, 1.00, 1.00),
    # 지형을 **상자로** 지시한다(규칙 다섯째). 프롬프트로 두 번 밀어 두 번 실패했다(격자·드레이프).
    # S1이 골짜기 바닥만 그리고, 좌우 산을 이 두 구역이 올린다 — 가운데가 낮게 남아 골짜기가 된다.
    "hill_left":    (0.00, 0.12, 0.40, 0.78),
    "hill_right":   (0.60, 0.10, 1.00, 0.76),
    "crest_left":   (0.02, 0.24, 0.44, 0.47),   # 이스라엘 쪽 산등성이 (17:2-3) — 1차에서 구역이
                                                # 커서 「멀리 작은 인물」이 안 잡혔다. 능선 선에 얇게 붙인다.
    "crest_right":  (0.56, 0.18, 0.99, 0.43),   # 블레셋 쪽 산등성이
    # 종횡비를 사람 비율로 좁힌다 — 0.68은 텐트/원뿔의 prior에 가깝고, v7에서 실제로 텐트가 나왔다.
    "goliath":      (0.625, 0.05, 0.855, 0.95),  # 거인 (17:4 신장) · 비율 0.51
    # 세로 0.42 → 0.53(2026-09-03, task 329): 성인 종자다 — 골리앗 2.9m : 성인 1.7m ≈ 1.7배 → 0.90/1.7.
    # x는 그대로다 — 판 방식에서 `_place`는 상자의 **높이와 가로 중심**만 쓰고 폭은 배율에 안 쓴다.
    "shieldman":    (0.44, 0.41, 0.585, 0.94),  # 방패 든 자 — 골리앗 **앞**(=더 가까이·아래) (17:7·41)
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
    ("S1", "full", 17.1, # ⚠ v13 정정 — 「far left / far right / middle / bottom」처럼 **위치를 말로 지시하자
    # 화면 전체가 격자·패널 도해**가 됐다. 모델은 위치 서술어를 레이아웃 지시로 읽는다.
    # 배치는 **구역 상자가 지고** 프롬프트는 사물만 말한다. v12 문구로 되돌린다.
    # ⚠ 두 번 시도해 두 번 실패했다: 위치 서술어(left/right/middle)는 **격자·패널 도해**를 부르고
    # (v13), 「V자 협곡·양쪽 급사면」은 **드레이프 천 같은 형태**를 냈다(v15). 배치·지형 형태를
    # 말로 밀는 것은 이 모델에서 잘 안 먹는다 — v12 문구로 되돌리고 골짜기는 미해결로 둔다.
    f"{ST} a low flat dry valley floor of pale stony ground, a dry "
                         f"brook bed with smooth round stones, sparse dry grass, empty pale sky, "
                         f"no hills, no people.",
     NEG + ", people, figures, soldiers, flat plain, open field"),   # ⚠ v10에서 `grid·stripes·ruled paper`를
     # 부정어에 넣었더니 **화면 전체에 격자가 나타났다**(부정어 누출). 도로 뺀다 — 부정어는
     # 낱말을 지우는 도구가 아니라 확률을 미는 도구여서, 없던 개념을 불러오는 쪽으로도 작동한다.
    ("S1b", "hill_left", 17.3, f"{ST} a tall steep dry rocky hillside rising up, sunbaked "
                               f"brown slope, layered rock, sparse dry grass, no people.",
     NEG + ", people, figures, flat ground, valley, pagoda, temple, tower, roof, building"),
    ("S1c", "hill_right", 17.3, f"{ST} a tall steep dry rocky hillside rising up, sunbaked "
                                f"brown slope, layered rock, sparse dry grass, no people.",
     NEG + ", people, figures, flat ground, valley, pagoda, temple, tower, roof, building"),
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
    # ⚠ 지물을 **문장 앞으로**(2026-09-01 task 325). d1~d5에서 얻은 규칙 — 모델은 손에 지물을
    # **하나만** 쥐고, 문장 앞에 둔 것이 이긴다. g1에서 자루는 한 자루로 돌아왔으나 손에서 떨어져
    # 따로 섰고 손에는 타원 주걱이 남았다. 자루를 명시해 손에 묶는다.
    # ⚠ 2026-09-03(task 329) — 앵커를 뗀 뒤 어휘만으로 간다. v39의 결함 「원뿔 모자·목각 톤·둘로
    # 보임」에 맞춰 **볼가리개 놋투구**(`with cheek guards`)·**수염 난 위압적 얼굴**·비늘갑(가산)을
    # 명시하고, 정본 의상 문구 대신 짧은 `overlapping bronze scale armour`로 토큰을 확보했다.
    # 후보 실측표는 노트 §21.
    # ⚠ v40 실측: gA s42는 육안 통과였으나 `ink_goliath 0.059`(정답지 0.102~0.221)로 C4 낙제 — 앵커를
    # 떼자 연필 스케치 톤으로 옅어졌다(판 잉크 0.014 vs 다윗 0.172). gB「bold dark ink outlines and
    # rich colored-pencil fill」은 **효과 0**(0.010~0.034) — 화풍 형용사는 톤을 못 바꾼다. C4는 어두운
    # 화소 비율이라 청동·베이지 낱말만으로 채운 인물은 무엇을 해도 밝다 → **대상의 색 낱말**로 어두운
    # 화소를 만든다(검은 수염·어두운 청동). 공용 ST는 건드리지 않는다(다윗 s42·방패병 s11 확정).
    ("S3", "goliath", 17.5, f"{ST} a towering black-bearded Philistine warrior gripping "
                            # `nine feet tall`을 뺐다 — 크기는 **구역 상자가 정한다**(실측
                            # 골리앗:다윗 1.9배). 문구로 중복해 말할 토큰이 없다(78/77 초과했다).
                            # ⚠ 방향구를 문장 앞으로 당기는 것은 **시도했다가 되돌렸다**(g4).
                            # `strict side view ... facing left`를 앞에 두자 얼굴이 통째로
                            # 사라지고(투구 아래 검은 덩어리) 창이 도끼가 됐다. 방향은 끝에 둔다.
                            f"one thick heavy spear with a long wooden shaft, "
                            f"dark bronze helmet with cheek guards, "
                            f"torso covered in dark overlapping bronze scale armour, bronze greaves, "
                            f"seen from the side, body and face turned left.",
     # `barbaric`은 기사 prior를 밀어냈지만 **맨가슴**을 불러 어린갑과 상충했다(v8 실측).
     # 청동기·블레셋이라는 **시대·민족 레지스터**로 바꾼다 — 중세 판금을 배제하면서 옷은 안 벗긴다.
     # ⚠ 판에서 창이 **두 자루의 나란한 장대**로 읽혔다(v31~v33) — 자루를 겹선으로 그린 탓이다.
     # ⚠ 동의어 중복을 뺐다(2026-09-01) — 테두리족을 필수부로 올리느라 자리가 필요했고, 개념은
     # 하나도 안 버렸다: `horned helmet`⊂`horns` · `naked torso`⊂`bare chest, shirtless`.
     # `pair of poles`도 뺐다 — v36에서 **장대 개념 자체가 밀려나** 창이 짧은 손잡이 타원 주걱이
     # 됐다(과교정). 두 자루를 막되 자루는 남겨야 한다.
     NEG + ", horns, plate armour, knight, medieval, tent, cone, robe, "
            "bare chest, shirtless, two spears, double spear"),
    # ⚠ 2026-09-03(task 329) — 사용자 결정: 방패 든 자는 **무장 없는 종자**, 성인 크기(상자 세로 0.53).
    # 「양손으로 큰 방패를 앞에 세워 들고 걷는다」로 자세를 박고, 갑주·창·검·망토·투구를 부정어로.
    ("S4", "shieldman", 17.7, f"{ST} full body of an unarmed Philistine servant walking, "
                              f"carrying a large round bronze shield upright in front of him with both hands, "
                              f"plain knee-length tunic, sandals, facing left.",
     NEG + ", armour, spear, sword, cape, helmet, oval, circle, medallion, vignette, inset, floating"),
    ("S5", "david", 17.40, # ⚠ **`swinging a sling`은 쓰지 말 것** — v15에서 모델이 **그네(swing)** 로 읽어 아이가
     # 그네를 타고 있었다. `whirling`은 손을 비게 만들었다(v9·v14). 동작 낱말을 버리고
     # **쥐고 있는 물건**으로 말한다 — 손에 무엇이 있는지가 그려져야 할 것의 전부다.
     # 지물을 **문장 앞으로** 당긴다 — 판에서 주머니만 나오고 물매·막대기가 빠졌다(v31~v33).
     # 막대기는 **요구에서 뺐다** — §5가 고정한 순간은 17:48-49(빨리 달리며 손을 주머니에 넣어)이고,
     # 그 순간 다윗의 두 손은 **물매와 주머니**가 가져간다. 17:40의 막대기는 「나아갈 때」의 지물이다.
     # 근거: ADR 260902-170558(고정한 순간이 지물 요구를 판다) · 모델은 한 손에 지물을 하나만 쥔다
     # (task 325 실측: 다섯 문구 × 네 시드에서 막대기를 넣으면 물매가 죽거나 그 반대였다).
     # ⚠ 2026-09-03(task 329) — v39 판의 결함 중 **시대 불일치**(셔츠·반바지·구두·핸드백)를 여기서
     # 고친다: 시대·민족 낱말을 **맨 앞**에(`ancient Israelite`), 복식은 정본 `SAMPLE_COSTUME`에서,
     # bag → **pouch**(bag은 핸드백으로 읽혔다), 부정어에 현대 복식. **투척 자세는 요구에서 뺐다** —
     # 문구 3종(mid-throw/arm flung/cords flying 류) × 시드 4 = 12장 0 통과(끈이 손에서 시작 0·주머니 0·
     # 날개·바구니·종이 테두리), 순간은 17:48-49 전반 「달리며 물매를 쥔」으로 되돌렸다
     # (ADR 260903-154254가 062732를 대체). 실측표는 노트 §21.
     # dR(되돌림 1차) 4장: s42는 끈이 주먹에서 시작하는 통과 후보였으나 **주머니 0/4**(16장 누적 0) —
     # 문장 끝 `a leather pouch at his side`는 힘이 없다(PROMPTING 2). 주머니를 물매 바로 뒤로.
     # dR2(`pouch hanging at his hip`) 4장: 주머니 1/4·물매 손 0/4 — 둘이 한 그림에 함께 나온 적이
     # 20장 중 0. 모델은 인물에 지물 하나만 붙인다(task 325 규칙 재현). 셋째 문구는 둘을 **다른 신체
     # 부위**에 묶는다(주먹 ↔ 가슴 멜빵). 시드 7은 부정어를 살려도 종이 테두리(dR·dR2 연속) — 시드 prior.
     # dR3(주먹 ↔ 가슴 멜빵) 4장: 손에 물매 0. 「손의 물매」와 「주머니」는 24장 중 한 그림에 함께 나온
     # 적이 없다 → 사용자 결정(2026-09-03): **주머니를 요구에서 빼고** dR 문구·시드 42를 채택한다
     # (주머니는 17:40의 지물, §5의 순간에는 손이 물매를 쥔다). 문구는 dR 그대로 — 시드 재현을 위해
     # 낱말 하나도 바꾸지 않는다(`pouch at his side`가 남아 있어도 그림엔 안 나온다).
     f"{ST} an ancient Israelite shepherd boy running mid-stride, "
                           f"gripping a short leather sling, "
                           f"{dp.SAMPLE_COSTUME['david'][3:]}, "
                           f"a leather pouch at his side, facing right.",
     # 부정어는 필수부(단계 낱말)가 공용 뒤쪽을 밀어낸다(`_fit_neg`) — 12장 실측에서 `framed,
     # picture frame`이 잘려 시드 7이 종이 테두리를 그렸다. 중복(`sneakers`⊂shoes·`backpack`·
     # `grey hair`⊂old man)을 빼 공용 액자족이 예산 안에 들게 한다.
     NEG + ", armour, helmet, sword, beard, old man, robe, tall adult, "
           "shirt, shorts, trousers, shoes, handbag"),
    ("S9", "sling_arc", 17.40, # ⚠ 「above the boy's head」라고 쓰자 모델이 **머리를 그렸다**(v4·v6 실측: 왼쪽 위에 큰 얼굴).
     # 이 단계는 지물만 그려야 하므로 인물 낱말을 한 개도 넣지 않는다.
     # v9에서 S5 프롬프트에 합쳤더니 **손이 빈 채로** 나왔다 — 지물은 자기 단계가 있어야 한다.
     # 구역은 다윗 실루엣 상단에서 파생해 **손 근처**에 둔다(허공에 따로 그리면 해먹으로 읽혔다).
     f"{ST} two very thin taut leather cords stretched in the air, "
                                 f"a tiny pouch with one small round stone at their far end, "
                                 f"thin lines only, nothing thick.",
     NEG + ", staff, pole, club, flag, banner, rope, head, face, person, boy, figure"),
    ("S7", "david_head", 17.42, f"{ST} head of a ruddy boy of fifteen, clean-shaven, curly hair, "
                                f"bare head, strict side profile facing right, chin up, "
                                f"looking straight at the giant on the right.",
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


# S9(물매)도 폐기했다 — v10~v13 **네 판 연속 실패**: 거대한 손 → 거대한 팔 → 원뿔 → 손톱 손.
# 작은 상자에 「지물 하나」를 그리라 하면 모델이 그 상자를 채우는 크기로 그린다. 물매는 S5의
# 인물 프롬프트가 지게 두고, 별도 단계를 만들지 않는다.
SKIP = {"S8_DROPPED", "S9", "S7"}
# **S7(다윗 얼굴 다듬기)도 폐기했다**(2026-09-01). 상자 인페인팅 시절에는 다윗이 고개를 숙인 채라
# 이 단계가 고개를 들게 했다. 판 합성에서는 **판이 이미 얼굴과 방향을 준다** — 그 위에 다시
# 그리면 되레 망친다(v32 실측: 얼굴이 지워지고 뒤통수가 됐다. v31에서는 살아남았으니 동전던지기다).
# S6: v8까지 물매를 허공에 따로 그렸더니 **해먹·그물**로 읽혔다.
                               # 손에 쥔 것으로 S5에 합친다 — 떠 있는 지물이 오독의 원인이었다.
# S8(골리앗 얼굴)도 폐기했다 — v9 실측: 다듬기 단계가 머리를 다시 그리며 **놋투구를 지워
# 대머리로** 만들었다. 그리고 S3만으로 이미 왼쪽을 보므로 이 단계는 순손실이다.
REFINE_STAGES = {"S7"}
RIDGE_STAGES = {"S2a", "S2b"}   # 마스크를 상자가 아니라 지형 하늘선에서 판다(ridge_mask)
PLATE_STAGES = {"S3", "S4", "S5"}
# **인물은 장면 안에서 그리지 않고 「판」으로 따로 그려 오려 붙인다**(2026-09-01 사용자 제안, 실측 확인).
# 상자 인페인팅의 두 결함이 여기서 함께 사라진다:
#   ① 자세가 지형에 끌려간다 — 가파른 비탈 위 상자를 채우려 골리앗이 웅크리거나 누웠다(v26·v29·v30).
#   ② 상자 변이 잔상으로 남는다 — 모델이 상자 안 배경까지 새로 지으니 붙임 마스크가 사각형이 된다.
# 민 종이 위에서는 모델이 지형과 싸우지 않고, 붙임 마스크가 **인물 실루엣**이라 변이 없다.
# 캔버스는 params.SAMPLE_SIZE(832x1216) — 「가로 캔버스로 단독 전신을 뽑으면 모델이 장면을
# 구성해 버린다」는 2026-08-26 실측이 그 주석에 이미 있다.
PAPER = (247, 240, 226)   # 종이색 — 캔버스 바탕이자 판의 배경(오려내기 기준)
PLATE_BG = " plain empty paper background."
PLATE_NEG = ", landscape, hills, sky, ground, scenery, shadow"
PLATE_STRENGTH = 0.99   # 판은 빈 종이에서 시작하므로 통째로 새로 그린다
PLATE_CUT = 20   # 종이색과의 차이가 이보다 크면 인물. ⚠ 10에서는 **판 전체가 잡힌다**(옅은 배경
                 # 얼룩). 반대로 너무 높이면 v5의 「옅게 그려진 골리앗을 통째로 버림」이 재현된다.
# **창을 전체 캔버스로 주는 단계.** 규칙 ③(창 ≠ 마스크)의 또 다른 적용 — 능선 띠를 1024로 확대해
# 생성하면 「멀리 작은 병사」를 그리라 해도 **큰 병사**가 나온다(v9~v17). 창을 화면 전체로 주면
# 모델이 장면 배율을 보고 그 안에서 작게 그린다. 마스크는 여전히 능선 띠다.
# ⚠ v18 실측 — 전체 창을 주자 S2가 **아무것도 안 그렸다**(구역 창에서는 큰 병사가 나왔다).
# 「멀리 작은 군중」은 이 두 손잡이 사이에 답이 없다. **미해결로 남긴다** — 비워 두면 구역 창이다.
CONTEXT_FULL = set()   # 다듬는 단계 — REFINE_STRENGTH를 쓴다
PAD = 0.10        # 구역 둘레 맥락 여백(구역 짧은 변의 분율) — 모델이 이어붙일 주변을 봐야 한다.
                  # ⚠ 0.40으로 올려 봤다(2026-09-01): 이음매가 0.989 → 0.375로 줄었지만 **판당
                  # 6분 → 11분**이 됐고, 아래 가중치 붙임이 같은 결함을 원가 없이 없앤다.
TARGET = 1024     # 생성 해상도(긴 변) — gen_final.TARGET과 같은 값·같은 이유
# **S1 전용 생성 크기 — 캔버스보다 덜 납작하게 그려서 가운데 띠만 잘라 쓴다.**
# 2026-09-01 실측(같은 프롬프트·같은 시드 11, 크기만 바꿈): 1024×536(1.91:1)에서 하늘을
# 가로지르는 자 같은 선이 **5행**, 1024×768(1.33:1)과 1024×1024에서 **0행**. 즉 이 선은
# 프롬프트가 아니라 **극단적 종횡비의 생성 아티팩트**다(낱말·부정어로 다섯 판을 쓴 자리다).
# 캔버스가 1216×640 = 1.9:1이므로 S1만은 덜 납작하게 그리고 캔버스 종횡비로 **잘라** 맞춘다
# — 늘려 맞추면 지형이 눌린다.
S1_GEN = (1024, 768)
# 잘라낼 띠의 위치 — 0.0이면 **위쪽**, 0.5면 가운데, 1.0이면 아래쪽. 가운데를 자르면 4:3 원본이
# 그린 **하늘과 능선을 통째로 버린다**(2026-09-01 실측: 능선이 화면 위끝에 붙어 골짜기 깊이가
# +0.069에 머물고 군대를 세울 능선이 화면 밖으로 나갔다). 위쪽을 잘라 쓰면 하늘·능선이 남고
# 버리는 것은 가까운 자갈밭인데, 그 자리는 어차피 인물이 덮는다.
# ⚠ 1024x1024(1:1)는 **원형 액자**를 그린다 — 4:3이 이 모델의 자리다.
S1_CROP_BIAS = 0.0


ASPECT_MAX = 1.5   # 창의 긴 변 / 짧은 변 상한 — 넘으면 **가로 줄무늬 아티팩트**가 나온다
                   # (2026-09-01 실측: 1.91:1에서 하늘 가로선 5행, 1.33:1에서 0행. notes §12 규칙 여섯째)


PAD_BY_STAGE = {}
# ⚠ **인물 단계만 0.35로 넓혀 봤다가 되돌렸다**(2026-09-01 v28): 이음매는 자리만 옮겼고
# (골리앗·방패든자 → 다윗 .525) 그림이 무너졌다 — **다윗이 둘로 늘고**, 골리앗이 비탈에 눕고,
# 왼쪽 바위가 탑이 됐다. 창이 커지면 모델이 **마스크를 어디 채울지 잃는다**(v18의 「전체 창에서
# 아무것도 안 그렸다」와 같은 결). 창은 상자에 붙여 두고 이음매는 붙임 램프로 잡는다.


def _window(b, name=None):
    """구역 + 맥락 여백, 캔버스 안으로 클램프. gen_final.window와 같은 구실.

    **납작한 창은 짧은 쪽을 늘려 완화한다.** 능선 띠처럼 가늘고 긴 구역을 그대로 창으로 쓰면
    종횡비가 3:1을 넘어 모델이 자 같은 가로선을 그린다. 마스크는 그대로 두고 창만 넓히는 것이라
    규칙 ③(창 ≠ 마스크)의 또 다른 적용이다."""
    pad = int(round(PAD_BY_STAGE.get(name, PAD) * min(b[2] - b[0], b[3] - b[1])))
    x0, y0 = max(0, b[0] - pad), max(0, b[1] - pad)
    x1, y1 = min(W, b[2] + pad), min(H, b[3] + pad)
    for _ in range(8):
        w, h = x1 - x0, y1 - y0
        if w > h * ASPECT_MAX:
            need = int(round(w / ASPECT_MAX)) - h
            y0, y1 = max(0, y0 - need // 2), min(H, y1 + (need - need // 2))
            if y0 == 0 and y1 == H:
                break
        elif h > w * ASPECT_MAX:
            need = int(round(h / ASPECT_MAX)) - w
            x0, x1 = max(0, x0 - need // 2), min(W, x1 + (need - need // 2))
            if x0 == 0 and x1 == W:
                break
        else:
            break
    return (x0, y0, x1, y1)


RIDGE_UP, RIDGE_DOWN = 0.07, 0.05   # 능선 띠 = 하늘선 위 7% ~ 아래 5%
# ⚠ **0.035/0.02로 얇게 해 봤다가 되돌렸다**(2026-09-01). 「띠 두께가 병사 키를 정한다」고 봤는데,
# 그렇게 본 근거였던 세로 런이 사실은 **병사가 아니라 언덕**을 재고 있었다(판정자 버그, judge_scene
# c2_army 주석 ②). 자를 고쳐 다시 재니 얇은 띠는 군중 밀도를 **0.39 → 0.065로 떨어뜨렸다** —
# 모델이 채울 자리가 없으면 안 그린다(v18의 「마스크가 묻히면 아무것도 안 그린다」와 같은 결).


def ridge_mask(canvas, region):
    """**능선을 따라가는 띠** — 「이편 산에 섰고 저편 산에 섰고」(17:3)를 상자가 아니라 지형에서
    파생한다. 손으로 적은 가로 상자는 지형이 바뀔 때마다 어긋나 병사가 **빈 하늘에** 그려졌다
    (v17 실측: 능선 위 비율 좌 0.28 · 우 0.20)."""
    lum = np.asarray(canvas.convert("L"), dtype=np.float32) / 255.0
    top = J.skyline(lum)
    x0, _, x1, _ = box_px(region)
    yy = np.arange(H)[:, None]
    band = (yy >= (top - RIDGE_UP * H)) & (yy <= (top + RIDGE_DOWN * H))
    band &= (top < H - 1)[None, :]     # 지형이 없는 열(하늘선 = H)은 뺀다 — 안 그러면 화면 바닥에 띠가 생긴다
    m = np.zeros((H, W), np.uint8)
    m[:, x0:x1] = (band[:, x0:x1] * 255).astype(np.uint8)
    return Image.fromarray(m, "L").filter(ImageFilter.GaussianBlur(max(4, int(0.02 * H))))


def _gen_size(win):
    w, h = win[2] - win[0], win[3] - win[1]
    sc = TARGET / max(w, h)
    return max(8, round(w * sc / 8) * 8), max(8, round(h * sc / 8) * 8)


def _change_mask(new_im, old_im):
    """**앞 단계 대비 바뀐 화소** = 이 단계가 실제로 그린 것. 사각 상자 대신 이것으로 되붙인다.

    **왜 필요한가**(2026-08-31 v4·v5 실측):
    ① v4 — 구역 마스크가 사각형이라 창 안의 **배경까지** 새로 칠해 붙었고, 단계마다 그 사각형이
       드러나 그림이 **콜라주**가 됐다.
    ② v5 — 그래서 「종이색이 아닌 화소」를 실루엣으로 썼더니 **옅게 그려진 골리앗이 통째로
       버려졌다.** 절대 밝기 기준은 옅은 인물을 못 잡는다.
    그래서 기준을 **변화량**으로 바꾼다 — 밝기와 무관하게 자기 보정된다.

    ⚠ **경계에 램프를 둔다**(2026-09-01 v29). 이진 컷은 「많이 바뀐 곳」의 테두리를 **한 픽셀
    단차**로 만들고 그것이 그대로 이음매가 된다(지형이 상세해지자 골리앗 .365 · 방패든자 .352).
    임계 **이상은 그대로 꽉 차게**(=옛 동작 보존, 인물이 옅어지지 않는다) 두고, 임계의 45%부터
    임계까지만 0→255로 올린다. 앞서 램프를 임계의 50%~200%로 걸었다가 **인물까지 부분 알파로
    붙어 다윗 잉크가 반토막**났던 것이 v24다 — 램프는 임계 **아래에만** 있어야 한다."""
    a = np.asarray(new_im.convert("L")).astype(np.float32)
    b = np.asarray(old_im.convert("L")).astype(np.float32)
    d = np.abs(a - b)
    lo = params.THRESHOLD * 0.45
    ramp = np.clip((d - lo) / (params.THRESHOLD - lo), 0.0, 1.0)
    return Image.fromarray((ramp * 255).astype(np.uint8), "L")


# ⚠ **부정어에는 토큰 가드가 없었다**(2026-09-01 task 325 실측). 긍정만 재고 부정은 그대로
# 넘겼다 — S3의 판 부정어가 **105/77**이라 뒤 28토큰이 조용히 잘렸고, 잘린 것이 하필
# **창 부정어 셋(two spears·double spear·pair of poles)과 PLATE_NEG 전부**였다.
# 그래서 「부정어로 안 잡혔다」(a591905 커밋 메시지)는 틀린 판정이다 — 부정어가 모델에
# **도달한 적이 없다**. 잘림이 불가피하면 무엇을 버릴지는 **명시적으로** 고른다:
#   ① PLATE_NEG — 배경을 그리면 오려낼 수가 없다(판 경로의 존재 이유)
#   ② 단계 고유 부정어 — 그 판의 결함을 막으려고 적은 말
#   ③ 공용 NEG — 앞에서부터 들어가는 만큼만
def _fit_neg(tok, stage_neg, lim):
    """판 부정어를 한도 안에 **명시적으로** 싼다 → (부정어, 버린 것). 조용히 자르지 않는다."""
    specific_raw = stage_neg[len(NEG):] if stage_neg.startswith(NEG) else stage_neg
    split = lambda t: [x.strip() for x in t.split(",") if x.strip()]
    # 화풍 바닥(`stick figure, crude drawing`)도 필수부에 넣는다 — 다섯 축의 C4가 재는 값이라
    # 공용 뒤쪽으로 밀리면 회귀 가드를 이 수선이 스스로 깨뜨린다.
    # ⚠ **테두리족도 필수부다**(2026-09-01 v36·d1 실측). 처음엔 「판은 어차피 오려내니 액자류는
    # 저가」로 보고 공용 뒤쪽에 뒀는데 **두 군데서 값을 치렀다**: ① v36에서 골리앗 판이 제 발밑에
    # 회색 그림자 타원을 그렸고 그것이 알파 컷에 들어가 판 하단이 직선으로 붙었다(C3 이음매
    # 0.250 → 0.540 실패) ② 판별 실행 d1의 시드 7에서 **테두리가 그려진 흰 종이**가 판을 통째로
    # 채웠다. 판을 오려 붙이는 구조에서는 판이 제 테두리를 그리는 순간 그것이 곧 이음매다.
    head = (split(PLATE_NEG) + ["stick figure", "crude drawing"]
            # `framed, picture frame`도 필수부(2026-09-03 task 329: 다윗 판 문구 4종 모두 시드 7이
            # 종이 테두리 — 단계 부정어가 늘자 이 둘이 공용 뒤쪽에서 잘렸다).
            + ["frame", "border", "framed", "picture frame", "vignette", "paper edge", "torn paper"]
            + split(specific_raw))
    head = list(dict.fromkeys(head))              # 단계 부정어와 겹칠 수 있다(S4의 vignette)
    if len(tok(", ".join(head)).input_ids) > lim:
        sys.exit(f"판 부정어의 필수부가 한도를 넘었다"
                 f"({len(tok(', '.join(head)).input_ids)}/{lim}) — 단계 부정어를 줄여라")
    generic = [t for t in split(NEG) if t not in head]   # 필수부와 겹치면 보고가 거짓말을 한다
    kept = list(head)
    for i, t in enumerate(generic):
        if len(tok(", ".join(kept + [t])).input_ids) > lim:
            return ", ".join(kept), generic[i:]
        kept.append(t)
    return ", ".join(kept), []


def _plate(pipe, name, prompt, neg, seed, label):
    """인물 한 명을 **민 종이 위에 단독으로** 그려 오려낸다 → (그림, 알파, 토큰수).

    배경 지시는 프롬프트 뒤에 붙이므로 **토큰 한도를 넘으면 조용히 잘려** 배경이 그려진다.
    넘으면 자세 문구를 줄여서 배경 지시를 살린다 — 배경이 그려지면 오려낼 수가 없다."""
    pw, ph = params.SAMPLE_SIZE
    p = prompt.rstrip() + PLATE_BG
    lim = pipe.tokenizer.model_max_length
    # ⚠ 문장부호에 기대지 말 것 — S3은 「…turned left.」로 **마침표**로 끝나서 앞선 규칙이
    # 아무것도 못 줄였고 가드가 79/77로 멈췄다(2026-09-01 v31 1차). 구절 자체를 갈아끼운다.
    for long, brief in (("seen from the side, body and face turned left", "side view facing left"),
                        ("strict side profile facing left", "side view facing left"),
                        ("strict side profile facing right", "side view facing right"),
                        ("running mid-stride", "running")):
        if len(pipe.tokenizer(p).input_ids) <= lim:
            break
        p = p.replace(long, brief, 1)
    n = len(pipe.tokenizer(p).input_ids)
    if n > lim:
        sys.exit(f"{name} 판 프롬프트가 한도를 넘었다({n}/{lim}) — 배경 지시가 잘린다")
    ng, dropped = _fit_neg(pipe.tokenizer, neg, lim)
    if dropped:
        print(f"    [{name}] 부정어 {len(dropped)}개를 예산에서 뺐다(공용 뒤쪽): "
              f"{', '.join(dropped)}", flush=True)
    res = pipe(prompt=p, negative_prompt=ng,
               image=Image.new("RGB", (pw, ph), PAPER),
               mask_image=Image.new("L", (pw, ph), 255),
               width=pw, height=ph, strength=PLATE_STRENGTH,
               num_inference_steps=params.STEPS, guidance_scale=params.GUIDANCE,
               generator=torch.Generator("mps").manual_seed(seed)).images[0]
    d = np.abs(np.asarray(res.convert("RGB")).astype(int) - np.array(PAPER)).max(axis=2)
    al = Image.fromarray(((d > PLATE_CUT) * 255).astype(np.uint8), "L")
    al = al.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(5))   # 내부 구멍 메우기
    bb = al.getbbox()
    if bb is None:
        sys.exit(f"{name} 판에서 인물을 못 오렸다 — PLATE_CUT을 의심하라")
    # **크롭 전 원본 판을 남긴다.** 프롬프트·시드가 고정이면 판은 결정적이라, 이 한 장이 있으면
    # 오려내기·배율 규칙 훑기를 **GPU 없이** 반복할 수 있다(알파는 PAPER/PLATE_CUT에서 재파생).
    res.save(os.path.join(OUT, f"{label}-plate-{name}-s{seed}.png"))   # 라벨을 붙여 문구 판별 비교가 되게
    return res.crop(bb), al.crop(bb).filter(ImageFilter.GaussianBlur(1.5)), n, lim


BODY_COV = 0.20   # 이 비율(행/열 최대 피복 대비) 이상이 **본체**다. 물매 끈·고리처럼 피복 2~5%인
                  # 얇은 지물을 배율·중심의 기준에서 뺀다 — 2026-09-02 실측: 다윗 판의 위쪽 314행
                  # (알파 bbox 848행의 **37%**)이 피복 1.8~4.7%짜리 끈이었다.


def _body_box(alpha):
    """판에서 **본체**(얇은 지물을 뺀 몸)의 상자. 배율과 가로 중심의 기준이다."""
    a = np.asarray(alpha) > 127
    cov = a.sum(axis=1)
    rows = np.flatnonzero(cov >= BODY_COV * cov.max())
    y0, y1 = int(rows[0]), int(rows[-1]) + 1
    ccov = a[y0:y1].sum(axis=0)
    cols = np.flatnonzero(ccov >= BODY_COV * ccov.max())
    return int(cols[0]), y0, int(cols[-1]) + 1, y1


def _place(canvas, fig, alpha, b):
    """오려낸 인물을 상자에 맞춰 얹는다 — **본체를 상자 높이에 맞추고 본체의 발이 상자 바닥에** 오게.

    ⚠ 기준을 판 전체 bbox에서 **본체**로 옮겼다(2026-09-02). 판 전체로 재면 얇은 지물이 두 번
    손해를 끼친다: ① 끈이 bbox를 세로로 늘린 만큼 소년이 **축소되고**(다윗 기여 잉크 0.048 →
    0.118) ② 끈이 bbox 중심을 끌어당겨 몸이 상자에서 **밀려난다**(같은 배율에서 0.083 → 0.118).
    붙일 범위는 여전히 알파 전체다 — 물매는 그림에 그대로 남는다.

    본체 아래의 그림자·지면은 이제 상자 선 **아래로 넘어간다**(골리앗 13px · 다윗 18px). 상자는
    「인물이 어디에 얼마나 크게 서는가」를 말하는 것이지 판이 그린 그림자까지 그 안에 욱여넣으라는
    뜻이 아니다."""
    bx0, by0, bx1, by1 = b
    cx0, cy0, cx1, cy1 = _body_box(alpha)
    sc = (by1 - by0) / (cy1 - cy0)
    nw, nh = max(8, int(fig.width * sc)), max(8, int(fig.height * sc))
    px = int(round((bx0 + bx1) / 2 - (cx0 + cx1) / 2 * sc))
    py = int(round(by1 - cy1 * sc))
    canvas.paste(fig.resize((nw, nh), Image.LANCZOS), (px, py),
                 alpha.resize((nw, nh), Image.LANCZOS))
    return canvas, (max(0, px), max(0, py), min(W, px + nw), min(H, py + nh))


CONTACT_STRENGTH = 0.55   # 접지 다듬기 — 있는 것을 고치는 쪽이라 낮다(얼굴 다듬기 0.72보다도).
                          # 높이면 모델이 그 자리에 새 그림을 그려 인물이 둘이 된다(v4 실측).
CONTACT_UP, CONTACT_DOWN, CONTACT_SIDE = 0.10, 0.06, 0.15   # 인물 높이·폭 대비 접지 띠


def _contact(pipe, canvas, bb, seed):
    """오려 붙인 인물의 **발 주변 띠만** 다듬어 땅에 닿게 하고 그림자를 넣는다.

    판 합성의 유일한 구조적 손해가 접지다 — 오려낸 인물은 배경과 **닿은 적이 없어서**
    발이 뜨고 그림자가 없다(스티커로 읽힌다). 장면 안 인페인팅은 이걸 공짜로 얻었다.
    인물 전체를 다시 그리면 판으로 얻은 자세를 잃으므로, 띠를 얇게 잡고 낮은 strength로 건다."""
    px0, py0, px1, py1 = bb
    fw, fh = px1 - px0, py1 - py0
    b = (max(0, int(px0 - CONTACT_SIDE * fw)), max(0, int(py1 - CONTACT_UP * fh)),
         min(W, int(px1 + CONTACT_SIDE * fw)), min(H, int(py1 + CONTACT_DOWN * fh)))
    m = Image.new("L", (W, H), 0)
    m.paste(255, b)
    m = m.filter(ImageFilter.GaussianBlur(max(4, int(0.25 * (b[3] - b[1])))))
    win = _window(b)
    gw, gh = _gen_size(win)
    prompt = (f"{ST} dry stony ground at the foot of a slope, feet planted on the ground, "
              f"a soft grey contact shadow on the ground under them.")
    neg = NEG + ", floating, gap, outline, cut-out, new person, second figure, face, portrait"
    res = pipe(prompt=prompt, negative_prompt=neg,
               image=canvas.crop(win).resize((gw, gh), Image.LANCZOS),
               mask_image=m.crop(win).resize((gw, gh), Image.LANCZOS),
               width=gw, height=gh, strength=CONTACT_STRENGTH,
               num_inference_steps=params.STEPS, guidance_scale=params.GUIDANCE,
               generator=torch.Generator("mps").manual_seed(seed)).images[0]
    ww, wh = win[2] - win[0], win[3] - win[1]
    canvas.paste(res.resize((ww, wh), Image.LANCZOS), (win[0], win[1]), m.crop(win))
    return canvas, b


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
    ap.add_argument("--plate-seeds", default="", help="판 단계별 시드, 예 S3=42,S4=11,S5=7 (기본은 장면 시드)")
    a = ap.parse_args()
    seeds = [int(s) for s in a.seeds.split(",")]
    plate_seeds = {k: int(v) for k, v in (kv.split("=") for kv in a.plate_seeds.split(",") if kv)}
    pick = None if a.stages is None else set(a.stages.split(","))
    os.makedirs(OUT, exist_ok=True)

    t = time.time()
    pipe = StableDiffusionXLInpaintPipeline.from_pretrained(
        params.SDXL_BASE, torch_dtype=torch.float16, variant="fp16",
        use_safetensors=True).to("mps")
    pipe.set_progress_bar_config(disable=True)
    # **IP 앵커를 뗐다**(2026-09-03, task 329 · ADR `260903-062733`). 골리앗 갑주에만 동결 표본의
    # 몸통 밴드를 IP-Adapter 0.25로 붙여 왔는데(어휘 6종 0/6 이력), 판 방식에서 그 앵커가 표본의
    # **단색 목각 톤과 정면성**을 함께 실어 와 골리앗이 다른 삽화가의 그림으로 읽혔다. 세 판이 한
    # 화풍이어야 하므로 앵커 없이 어휘만으로 간다 — 갑옷이 새면 최소 패치 레퍼런스가 별건이다.
    print(f"로드 {time.time() - t:.0f}s  ·  ControlNet 없음 · IP 레퍼런스 없음 — "
          f"서술은 전부 텍스트가 진다", flush=True)

    for seed in seeds:
        # S1은 빈 종이색 캔버스를 전체 인페인팅한다 — text2img와 같고 파이프라인이 하나면 된다.
        canvas = Image.new("RGB", (W, H), PAPER)
        drawn = {}   # 단계별 실제로 그려진 실루엣 bbox — 머리 상자를 여기서 파생한다
        for name, region, verse, prompt, neg in STAGES:
            if name in SKIP or (pick is not None and name not in pick):
                continue
            # **머리 상자는 저작하지 않고 실루엣에서 파생한다.** v8까지 골리앗 머리 상자가
            # y 0.05~0.30에 고정돼 있었는데 구역을 좁히며 그의 머리가 내려가, S8이 **빈 하늘을
            # 칠하고 있었다**(그래서 얼굴 단계가 「거의 안 먹는다」로 보였다).
            if name in PLATE_STAGES:
                # **판으로 그려 오려 붙인다** — 장면 안에서 그리지 않는다(PLATE_STAGES 주석).
                ts = time.time()
                ps = plate_seeds.get(name, seed)   # 판별 시드 — 없으면 장면 시드
                fig, al, n, lim = _plate(pipe, name, prompt, neg, ps, a.label)
                canvas, bb = _place(canvas, fig, al, box_px(region))
                canvas, cb = _contact(pipe, canvas, bb, seed)
                drawn[name] = bb
                out = os.path.join(OUT, f"{a.label}-{name}-s{seed}.png")
                canvas.save(out)
                print(f"  [{name} {region} 17:{str(verse).split('.')[1]}] {time.time() - ts:.0f}s  "
                      f"{n}/{lim}토큰  판 s{ps} {fig.width}x{fig.height} → 얹음 {bb} · 접지 {cb} -> "
                      f"{os.path.basename(out)}", flush=True)
                continue

            src = {"S7": "S5", "S9": "S5"}.get(name)
            if src and src in drawn:
                x0, y0, x1, y1 = drawn[src]
                if name == "S9":
                    # 물매는 **든 손 크기**여야 한다. v10·v11에서 마스크가 다윗 몸통만 해서
                    # 「거대한 팔」이 나왔다 — 창을 고쳐도 **마스크가 크면 큰 것을 그린다.**
                    # v10~v12: 상자에 「물건」을 그리라 하면 그 상자 크기의 물건이 나온다(나팔·원뿔).
                    # 팔을 따라가는 **얇고 긴 띠**로 바꾸고, 문구도 「끈 두 가닥」으로만 말한다.
                    fw, fh = x1 - x0, y1 - y0
                    b = (x0 + int(fw * 0.55), max(0, y0 - int(fh * 0.16)),
                         min(W, x0 + int(fw * 1.30)), y0 + int(fh * 0.06))
                else:
                    hh = int(round((y1 - y0) * 0.30))      # 인물 상단 30% = 머리·어깨
                    b = (x0, y0, x1, y0 + hh)
                m = Image.new("L", (W, H), 0)
                m.paste(255, b)
                m = m.filter(ImageFilter.GaussianBlur(
                    max(4, int(round(FEATHER * min(b[2] - b[0], b[3] - b[1]))))))
            elif name in RIDGE_STAGES:
                m = ridge_mask(canvas, region)
                b = m.point(lambda v: 255 if v > 40 else 0).getbbox() or box_px(region)
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
            if name in CONTEXT_FULL:
                win = (0, 0, W, H)
            elif src and src in drawn:
                win = _window(drawn[src], name)
            else:
                win = _window(b, name)
            gw, gh = S1_GEN if name == "S1" else _gen_size(win)
            ts = time.time()
            refine = name in REFINE_STAGES
            res = pipe(prompt=prompt, negative_prompt=neg,
                       image=canvas.crop(win).resize((gw, gh), Image.LANCZOS),
                       mask_image=m.crop(win).resize((gw, gh), Image.LANCZOS),
                       width=gw, height=gh,
                       strength=(REFINE_STRENGTH if refine else
                                 STRENGTH_BY_STAGE.get(name, DEFAULT_STRENGTH)),
                       num_inference_steps=params.STEPS,
                       guidance_scale=params.GUIDANCE,
                       generator=torch.Generator("mps").manual_seed(seed)).images[0]
            ww, wh = win[2] - win[0], win[3] - win[1]
            if name == "S1":
                # 지형은 화면 전체다. **마스크를 쓰지 않고 통째로 갈아끼운다** — 부분 마스크로
                # 전체를 칠하면 캔버스 경계에서 가로 줄무늬 글리치가 남는다(v3~v8 실측).
                # 캔버스 종횡비의 **가운데 띠**만 잘라 쓴다(S1_GEN 주석 참조).
                ch = int(round(gw * H / W))
                oy = int(round((gh - ch) * S1_CROP_BIAS))
                canvas = res.crop((0, oy, gw, oy + ch)).resize((W, H), Image.LANCZOS)
                print(f"  [{name} {region} 17:1] {time.time() - ts:.0f}s  {n}/{lim}토큰  "
                      f"{gw}x{gh} → 가운데 {ch}행 잘라 전체 교체",
                      flush=True)
                continue
            else:
                back = res.resize((ww, wh), Image.LANCZOS)
                # **실루엣으로 되붙인다** — 사각 상자를 붙이면 그 변이 드러나 콜라주가 된다.
                sil = _change_mask(back, canvas.crop(win))
                # **형태학적 닫기(팽창 → 침식)로 내부 구멍을 메운다.** v6 실측: 옅게 그려진
                # 골리앗의 **내부**에서 변화량이 임계 아래라 구멍이 뚫려 그가 반투명해졌다.
                # 반지름은 구역 짧은 변에서 판다(고정값은 큰 구역에서 부족하다).
                # ⚠ **상한 8을 걸어 봤다가 되돌렸다**(2026-09-01 v27): 이음매는 안 줄고
                # (0.365 → 0.402, 자리만 옮겼다) 골리앗이 **반투명해졌다**(잉크 .109 → .049).
                # v6이 경고한 「옅은 인물 내부에 구멍」이 그대로 재현됐다 — 반지름은 구역 크기를
                # 따라가야 한다.
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
