"""task#314 S4 2단계 — 프롬프트를 5축(AXES)에서 파생한다(손으로 쓰지 않는다).

`cast/david.jsx`·`cast/goliath.jsx`의 `export const AXES = {...}`를 정적으로 읽어(정규식 —
render_scene.py의 stroke_scale()이 lib.jsx에서 W를 읽는 것과 같은 기법) 한글 축값을 영문 어휘로
매핑하는 표 하나(AXIS_EN)로 문장을 조립한다. 화풍 블록은 task#308 `run_grid.py`의 PROMPT 앞부분을
그대로 승계(#305/#308과 비교 가능해야 한다는 계획 요구).

배경 어휘(§bg_vocab)는 축이 아니라 NEEDS.md §4 / BACKGROUND.md §6가 이미 좌표로 확정한 목록의
직역이다 — 그대로 파생이지 새로 짓지 않는다.

CLIP 77토큰 하드 게이트는 이 스크립트가 아니라 GPU 스크립트(gen_candidates.py)가 진다 — 그 스크립트가
실제로 로드하는 파이프라인의 tokenizer로 재는 것이 유일하게 정확하다(run_grid.py 선례와 동일 위치).
"""
import json
import os
import re
import sys

import params

ROOT = params.REPO_ROOT

# task#308 run_grid.py 화풍 블록 그대로 승계(비교 가능성 요구).
STYLE = ("warm cream paper, soft pencil and colored-pencil storybook illustration, "
         "gentle hand-drawn lines, light shading, simple, clean background, muted palette.")

NEG = ("text, letters, words, watermark, photorealistic, 3d render, high saturation, "
       "cluttered background, dark, heavy shadows, frame, border, stick figure, crude drawing")

# task#315 S2 정정 — 나이를 data/person_events/*.json의 sortKey에서 파생한다(손으로 쓰지 않는다).
# num_to_words: 나이는 형용사가 아니라 숫자로 못박는다("young boy"가 화풍(storybook)과 합쳐져
# 유아·인형이 된 선례, 2026-08-24 사용자 UAT). age_at: 출생(=최소 sortKey) 대비 해당 이벤트의 나이.
def num_to_words(n):
    ones = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
            "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen",
            "eighteen", "nineteen"]
    tens = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]
    if n < 20:
        return ones[n]
    t, o = divmod(n, 10)
    return tens[t] + (f"-{ones[o]}" if o else "")


def age_at(event_id, person="david"):
    path = os.path.join(ROOT, "data/person_events", f"{person}.json")
    with open(path, encoding="utf-8") as f:
        events = json.load(f)
    birth = min(events, key=lambda e: e["sortKey"])
    assert "birth" in birth["id"], f"최소 sortKey 이벤트가 출생이 아니다: {birth['id']}"
    by_id = {e["id"]: e["sortKey"] for e in events}
    return by_id[event_id] - birth["sortKey"]


# "boy of about twelve"는 데이터(출생 -1040 → 골리앗 사건 -1025 = 15세)와 어긋났다(task#315 계획 정정).
_DAVID_GOLIATH_AGE = age_at("authored-david-goliath-gath")

# 5축 한글 -> (긍정 어휘, 그 값이 negative_prompt에 더하는 어휘).
# S1 NEEDS.md §3 표에 등재된 값만 다룬다 — 새 값이 나오면 KeyError로 드러난다.
#
# **부정형을 긍정 프롬프트에 쓰지 않는다.** CLIP은 부정을 못 다룬다 — 1차판의
# "no hair visible, no beard, clean-shaven"은 골리앗에게 수염을 없앤 게 아니라 **얼굴 자체를
# 비웠다**(사용자 UAT 2026-08-24 실패의 직접 원인). 「없음」 축값은 긍정에서 빼고 negative로 옮긴다.
AXIS_EN = {
    "hair": {"곱슬머리": ("curly hair", ""), "없음": ("", "visible hair, long hair")},
    "beard": {"없음": ("", "beard, moustache, stubble")},
    # 「투구」에 **뿔**을 넣은 것은 2026-08-26 사용자 판단이다. 삼상 17:5는 「놋투구」만 말하고 뿔은
    # 없으므로 이것은 본문 파생이 아니라 **연출 결정**이다. ⚠ **인물 정본 2층과 어긋난다** —
    # `cast/goliath.jsx`의 선화는 strokes=4(머리 윤곽 1 + 투구 돔 1 + 볼가림 2)로 뿔이 없고
    # `frozen/goliath.png`도 뿔 없는 볼가림 투구다. 두 층을 맞추는 것은 저작 층 변경이라 별건이다.
    "headwear": {"없음": ("bare head", ""), "투구": ("horned bronze helmet with cheek guards", "")},
    "age": {"소년/청년": (f"boy of {num_to_words(_DAVID_GOLIATH_AGE)}",
                       "baby, toddler, infant, chibi, doll"),
            "성인": ("grown man of about forty", "child, youth")},
    # 성별은 나이 어휘(boy/man)가 이미 나르므로 긍정 토큰을 쓰지 않고 negative로만 잠근다
    # — 77토큰이 빠듯하다(화풍 블록만 35토큰).
    "sex": {"남": ("", "woman, girl, female")},
}

# 5축 **재확인**(판정용) 대립쌍 — 축값마다 (정본 문구, 반대 문구).
# 생성용 `AXIS_EN`과 같은 자리에서 파생한다: 판정 문구도 손으로 쓰지 않는다는 같은 규율이고,
# 축값이 늘면 여기서도 KeyError로 드러난다. 판정은 **마진의 부호**다 —
# cos(그림, 정본문구) − cos(그림, 반대문구) > 0 이면 그 축이 정본과 맞는다.
#
# ⚠ `sex`는 대립쌍이 있어도 **기계 판정에서 뺀다** — 정본 자신이 통과하지 못한다
# (`frozen/david.png`가 -0.0135). 소년 얼굴이 CLIP에서 man/woman 사이에 놓이기 때문이고,
# 이는 `AXIS_EN`의 성별 주석(「나이 어휘가 이미 나르므로 긍정 토큰을 안 쓴다」)과 같은 현상이다.
AXIS_PROBE_EN = {
    "hair": {"곱슬머리": ("a person with curly hair", "a person with no visible hair"),
             "없음": ("a person with no visible hair", "a person with curly hair")},
    "beard": {"없음": ("a clean-shaven face with no beard", "a face with a full beard")},
    "headwear": {"투구": ("wearing a bronze helmet on the head", "a bare head with no helmet"),
                 "없음": ("a bare head with no helmet", "wearing a bronze helmet on the head")},
    "age": {"소년/청년": ("a young boy", "a grown adult man"),
            "성인": ("a grown adult man", "a young boy")},
    "sex": {"남": ("a man", "a woman")},
}
# 기계 게이트에 쓰는 축 — `sex` 제외(위 주석).
AXIS_PROBE_GATED = ("hair", "beard", "headwear", "age")

# --- 축 F: 갑주 **착용 여부** (2026-08-29 라운드 13) ------------------------------------
# **이 축이 재지 않는 것을 먼저 적는다: 갑주의 종류(비늘 vs 판금)를 재지 않는다.**
# 같은 몸통 상자·같은 기제로 두 대립쌍을 실측했다(ZIMAGE §9-15):
#   있음/없음  표본(갑주) +0.1028 · 인물없음 −0.0678        → 크게 갈린다
#   비늘/판금  표본 +0.0651 · **구 반사실 표본 +0.0957**     → 반사실이 더 높다. 못 가른다
# CLIP 대립쌍은 **존재/부재**에는 강하고 **한 종류 안의 세부**에는 무력하다는 것이 이 실측의 뜻이고,
# 사람이 지적한 「판금 기사」는 후자다 — 그래서 그 결함은 이 축으로 잡히지 않는다(사람에게 넘겼다).
#
# 정본값은 본문에서 온다: 골리앗 삼상 17:5 「놋투구를 그 머리에 쓰고 어린갑을 입었으니」 →
# 「갑옷」. 다윗 삼상 17:38-39 사울의 갑옷을 입었다가 **벗었다** → 「없음」.
COSTUME_CANON = {"goliath": "갑옷", "david": "없음"}
COSTUME_PROBE_EN = {
    "갑옷": ("wearing bronze armor on the chest", "a bare chest with no armor"),
    "없음": ("a bare chest with no armor", "wearing bronze armor on the chest"),
}
# **부재값은 게이트에 넣지 않는다** — 빈 배경이 「갑옷 없음」을 자동으로 만족해 음성 대조군이
# 무너진다(실측: 인물없음[david] +0.0872로 통과). 축 E가 `sex`를 뺀 것과 같은 이유다.
COSTUME_GATED = tuple(n for n, v in COSTUME_CANON.items() if v != "없음")

# NEEDS.md §4 배경 좌표 목록의 직역(BACKGROUND.md §6가 "그대로 파생" 대상으로 못박은 것과 동일 어휘) —
# CLIP 77토큰에 맞춰 항목은 그대로 두고 표현만 압축했다(축약이 아니라 표현 압축, 항목 손실 없음).
BG_VOCAB = ("dry streambed, five smooth stones, near hills, far ridges, "
            "hillside bushes, birds, dry grass")

# NEEDS.md §2 실측(둘 다 서 있는 자세, 물매를 돌리는 중) — --at 9000 조건 입력과 같은 순간을 말한다.
SCENE_PERSON = "a small shepherd boy swings a sling on the left, a huge armored giant stands on the right."


def read_axes(name):
    src = os.path.join(ROOT, "frontend/src/sketches/cast", f"{name}.jsx")
    with open(src, encoding="utf-8") as f:
        text = f.read()
    m = re.search(r"export const AXES\s*=\s*\{([^}]*)\}", text)
    if not m:
        sys.exit(f"{src}에서 AXES를 찾지 못했다")
    axes = dict(re.findall(r"(\w+):\s*'([^']*)'", m.group(1)))
    if set(axes) != set(AXIS_EN):
        sys.exit(f"{name}: AXES 키 불일치 — {set(axes)} vs {set(AXIS_EN)}")
    return axes


def read_brief(name):
    """정본 파일이 선언한 한 줄 인물 개요(BRIEF). 5축은 **구별**을 위한 것이라 「거인」·「위협」처럼
    그 인물을 그리는 데 필요한 성질을 담는 축이 없다 — 그것이 골리앗이 빈 타원으로 나온 나머지 절반의
    원인이다(사용자 UAT 2026-08-24). BRIEF는 장면 소스 주석에서 파생해 정본 파일에 선언한다
    (GoliathScene 주석 「얼굴 — 위협(눈썹을 아래로 모은다)」·「거인」). 선언이 없으면 빈 문자열."""
    src = os.path.join(ROOT, "frontend/src/sketches/cast", f"{name}.jsx")
    with open(src, encoding="utf-8") as f:
        m = re.search(r"export const BRIEF\s*=\s*'([^']*)'", f.read())
    return m.group(1) if m else ""


def portrait_prompt(name):
    axes = read_axes(name)
    try:
        en = {k: AXIS_EN[k][v] for k, v in axes.items()}
    except KeyError as e:
        sys.exit(f"{name}: 매핑 표에 없는 축값 {e} — AXIS_EN을 갱신하라(NEEDS.md §3과 대조)")
    # 긍정은 있는 것만. 순서는 나이(주어) → 개요 → 머리카락 → 머리쓰개 (앞일수록 CLIP에 세게 걸린다).
    parts = [en["age"][0], read_brief(name), en["hair"][0], en["headwear"][0]]
    body = ", ".join(p for p in parts if p)
    art = "an" if body[0].lower() in "aeiou" else "a"
    prompt = f"{STYLE} close-up head portrait of {art} {body}, facing forward."
    neg = ", ".join([_drop(NEG, "dark", "heavy shadows")] + [v[1] for v in en.values() if v[1]])
    return prompt, neg, axes


# --- 장면 프롬프트의 정체성 어휘 (task#317 S2) ---------------------------------
# 장면은 지금까지 "a small shepherd boy"/"a huge armored giant" 한 마디였다(SCENE_PERSON).
# 초상은 5축·BRIEF·나이에서 파생하는데 장면은 손으로 쓴 문구였고, 실제 산출에서 다윗은 5~7세
# 유아 얼굴로 나온다. 여기서는 **초상과 같은 출처**에서 조립한다 — 다만 2인 장면이라 CLIP 77토큰이
# 빠듯하므로, 완성된 문장이 아니라 **우선순위대로 정렬한 조각**을 넘기고 예산에 맞추는 일은
# 실제 tokenizer를 쥔 GPU 스크립트가 한다(이 파일이 토큰을 재지 않는다는 머리 주석의 규약 그대로).
SCENE_SLOT_ORDER = ("age", "brief", "hair", "headwear")   # portrait_prompt의 선언 순서 그대로


def scene_person_slots(name):
    """장면용 인물 서술 조각 — 앞일수록 CLIP에 세게 걸리므로 자를 때는 뒤에서 자른다."""
    axes = read_axes(name)
    en = {k: AXIS_EN[k][v] for k, v in axes.items()}
    src = {"age": en["age"][0], "brief": read_brief(name),
           "hair": en["hair"][0], "headwear": en["headwear"][0]}
    return [(k, src[k]) for k in SCENE_SLOT_ORDER if src[k]]


# 장면이 서술하는 동작·자리. NEEDS.md §2 실측(--at 9000의 콘티와 같은 순간)에서 온 것이라
# SCENE_PERSON과 같은 출처이고, 바뀌는 것은 인물 서술뿐이다.
SCENE_FRAME = ("a {david} swings a sling on the left, "
               "a {goliath} stands on the right.")

# 장면 네거티브에 더할 어휘. **축값의 부정어가 아니라 화풍 블록의 실패 양태**다 —
# "young boy"가 storybook과 합쳐져 유아·인형이 된 선례(2026-08-24 사용자 UAT)라서 초상 축에
# 달려 있었을 뿐, 두 인물 중 누구도 이것에 해당하지 않는다. 그래서 2인 장면에 그대로 실을 수 있다.
# 나머지 축 부정어는 실을 수 없다 — 두 인물의 축값이 갈리기 때문이다: 골리앗의 "child, youth"는
# 다윗(열다섯 소년)을 지우고, 골리앗의 "visible hair, long hair"는 다윗의 곱슬을 지운다.
SCENE_NEG_EXTRA = AXIS_EN["age"]["소년/청년"][1]


# --- 전신 프롬프트 (task#317 후속, 순차 인페인팅용) ----------------------------
# 인물 **영역 전체**를 인페인팅할 때 초상 프롬프트를 쓰면 안 된다 — 그것은
# "close-up head portrait of …, facing forward"라서, 전신 실루엣 안에 얼굴 클로즈업을 그리려다
# 가면 같은 형체가 나온다(2026-08-25 실측: 골리앗 유사도 0.5345 → 0.4570으로 되레 떨어졌다).
# 그래서 같은 조각(5축·BRIEF·나이)에서 **전신·동작** 문장을 따로 파생한다.
#
# 동작의 출처는 SCENE_PERSON과 같다 — NEEDS.md §2 실측(--at 9000 콘티가 그리는 그 순간).
# 2026-08-29: 골리앗의 동작에서 **의상을 뺐다**("standing in heavy armor" → "standing").
# 동작 자리가 의상을 담고 있었고, 그 "heavy armor"는 (a) 아래에서 더하는 의상 서술과 중복이며
# (b) 일반적 낱말이라 모델의 **판금** 사전지식 쪽으로 민다. 의상은 의상 자리(SAMPLE_COSTUME)에서 온다.
# 2026-08-30 (task#322 S2): **방향을 지시한다** — 보완 ③(두 인물이 서로를 보는 것).
# ③은 「표본이 정면을 실어 왔다」가 아니라 **아무도 방향을 지시하지 않아 표본만 말하고 있는 것**이다:
# 콘티 머리는 <circle>이라 회전 정보가 0이고, 어깨 호는 좌우대칭 정면이며, 여기에도 방향 어휘가
# 없었다. 가장 싼 손잡이인 프롬프트부터 연다(계획 S2 · 사용자 선택).
# 다윗이 화면 왼쪽(마스크 bbox x 233~611) · 골리앗이 오른쪽(660~1085)이므로 다윗은 오른쪽을,
# 골리앗은 왼쪽을 본다. **화면 기준**이다 — "his right"는 인물 기준이라 거울상이 된다.
# 낱말은 토큰 실측으로 골랐다(try_prompt.py --check, GPU 0):
#   A "facing right/left"        다윗 65 · 골리앗 74/77
#   B "head turned to the …"     다윗 68 · 골리앗 77/77  ← 여유 0. 규칙 1은 초과분이 조용히 잘린다
#   C "looking right/left"       다윗 65 · 골리앗 74/77  ← 채택
#   D "eyes on the giant to …"   다윗 70 · 골리앗 79/77  ← 초과, 기각
# A와 C는 값이 같은데 C를 고른 이유가 둘이다: ③이 묻는 것은 **시선**이고, "facing"은 몸통 회전을
# 지시해 CN 0.8이 콘티의 **좌우대칭 정면 어깨**에 묶어 둔 것과 정면으로 다툰다(PROMPTING.md 4의
# 「같은 자원을 놓고 싸운다」가 여기 적용되는지가 이 슬라이스의 관찰 대상이다 — 생성에서 확인한다).
# 2026-08-30 (사용자 「몸 전체 구도변경」) — **C에서 A로 바꾼다.** 위에서 C를 고른 이유가
# 「③이 묻는 것은 시선이고, "facing"은 **몸통 회전**을 지시해 CN이 묶어 둔 좌우대칭 정면 어깨와
# 다툰다」였는데, 사용자가 요구한 것이 바로 그 **몸통 회전**이다. 토큰은 A와 C가 같다(65·74/77).
# 그리고 실측이 「모델은 오히려 돌려는 경향」임을 보인다 — 표본은 정면을 유지하려고 부정어에
# **`profile view`를 명시로 넣어야 했다**(아래 SAMPLE_NEG_EXTRA 주석 ③). 장면 부정어에는 그
# 억제가 없으므로(NEG 확인), 막고 있던 것은 억제가 아니라 **지시가 시선까지만이었던 것**이다.
SCENE_ACTION = {"david": "swinging a sling, facing right",
                "goliath": "standing, facing left"}


# --- 머리 단계 (task#322, 2026-08-31 · 사용자 「토큰이 부족하니 인페인팅을 적극 활용하고
# 단계적으로 그림을 완성」) -------------------------------------------------------
# **왜 단계를 나누는가 — 실측이 강제한다.** 팔①은 **높은** 인물 CN이라야 서고(콘티가 사지
# 구조를 공급한다, §9-28), 머리③은 **낮은** CN이라야 돈다(콘티 머리가 대칭 <circle>이라
# CN을 세게 걸면 정면까지 강제된다 — fig_cn 0.8·0.5는 정면, **0.3에서만 회전**, 그런데 0.3에서는
# 축 C 셋·D·G가 통째로 무너진다, §9-32). 둘이 **같은 손잡이에 반대로 묶여** 있어 파라미터로는
# 못 푼다. 단계를 나누면 각자 CN을 갖는다.
# **덤 — 토큰.** 전신 프롬프트는 골리앗이 이미 74/77이라 방향을 두 단어(`facing left`)밖에 못
# 실었다. 후보 D `"eyes on the giant to …"`는 **79/77로 초과돼 기각**된 기록이 위에 있다.
# 머리 단계는 의상·자세·배경 조각이 빠지므로 **남는 예산을 방향 서술에 통째로 쓴다.**
# **부정어도 대칭으로 건다.** 표본은 정면을 지키려고 `SAMPLE_NEG_EXTRA`에 `profile view`를
# 넣어야 했다(아래 주석 ③ — "facing forward"만으로는 3/4 회전을 못 막았다). 그 반대를 여기 건다.
HEAD_DIRECTION = {"david": ("right", "the giant"), "goliath": ("left", "the shepherd boy")}
HEAD_NEG_EXTRA = "facing forward, frontal face, looking at viewer, symmetrical face"
# 부재 축을 **긍정으로** 말하는 문구(머리 단계 전용 — head_prompt 안의 근거 주석 참조).
# 순서가 곧 우선순위다: 실측에서 수염이 세 시드 전부 실패했고 머리카락은 한 시드만 실패했다.
HEAD_ABSENCE = {"beard": "clean-shaven", "hair": "no hair showing"}


def head_prompt(name):
    """머리 밴드 전용. 정체성 축은 portrait_prompt와 **같은 출처**에서 뽑아 두 층이 갈리지 않게
    하고, 남는 예산 전부를 방향에 쓴다. 토큰은 이 파일이 재지 않는다(머리 주석의 규약) —
    `gen_final._tok`이 한도 초과를 하드 실패로 잡는다."""
    axes = read_axes(name)
    en = {k: AXIS_EN[k][v] for k, v in axes.items()}
    parts = [en["age"][0], read_brief(name), en["hair"][0], en["headwear"][0]]
    body = ", ".join(p for p in parts if p)
    art = "an" if body[0].lower() in "aeiou" else "a"
    side, target = HEAD_DIRECTION[name]
    # 화풍 조각은 figure_prompt와 **같은 이유·같은 방식**으로 덜어낸다: 머리 마스크 안만 그리므로
    # 배경 어휘가 무의미하고, "light shading"·"muted palette"는 대비를 도로 깎는다(라운드 20).
    # 실측으로 강제된 절감이기도 하다 — 덜기 전 골리앗이 **82/77로 초과**했다(2026-08-31).
    head_style = _drop(STYLE, "simple", "clean background", "light shading", "muted palette")
    # **부재 축의 긍정 서술 — 머리 단계 전용** (2026-08-31 R3).
    # `hair=없음`·`beard=없음`은 AXIS_EN에서 **긍정이 비어 있고 부정어로만** 표현된다. 전신
    # 단계에서는 IP 레퍼런스(수염 없는 투구 머리)가 그 부재를 **이미지로** 지고 있어 문제가
    # 없었다. 그런데 머리 단계에서 회전을 얻으려면 그 레퍼런스를 떼야 하고(IP 0.15는 안 돌고
    # 0.0이라야 돈다), 그러면 부재를 주장하는 것이 부정어뿐이라 **약하다**(PROMPTING.md 3의
    # 배수표 — 부정어는 3×, 매체 교체는 140×). 실측: IP 0.0에서 축 E 수염이 세 시드 전부
    # 실패했다(−0.034 / −0.014 / −0.005). 그래서 **이 단계에서만** 부재를 긍정으로 말한다.
    # AXIS_EN(정본 표)은 건드리지 않는다 — 전신·표본·초상 프롬프트가 지금 통과 중이고, 표를
    # 바꾸면 그 층까지 함께 움직인다.
    absent = [HEAD_ABSENCE[k] for k in ("beard", "hair") if not en.get(k, ("",))[0]
              and k in axes and k in HEAD_ABSENCE]
    if absent:
        body = ", ".join([body] + absent)
    # **방향 서술을 줄이고 그 토큰을 정체성에 넘긴다** (2026-08-31 R4). 초판은 방향을 네 구절로
    # 중복 서술했는데(`strict … / head fully turned … / eyes on … / nose and chin point …`)
    # 실측상 **방향은 이미 이기고 있고 지는 쪽은 정체성**이다: R3에서 골리앗이 세 시드 모두
    # 옆얼굴로 돌았고, 떨어진 것은 축 E의 수염·머리카락이었다. 중복 두 구절을 덜어 그 자리에
    # 부재 서술 둘을 다 싣는다 — 같은 예산 안에서 이기는 쪽을 줄이고 지는 쪽을 늘리는 것이다.
    prompt = (f"{head_style} head of {art} {body}, "
              f"strict side profile facing {side}, eyes on {target}.")
    neg = ", ".join([_drop(NEG, "dark", "heavy shadows"), HEAD_NEG_EXTRA]
                    + [v[1] for v in en.values() if v[1]])
    return prompt, neg


def torso_prompt(name):
    """몸통 밴드 전용 (task#322 2026-08-31, 4단계). 의상 문구는 **`SAMPLE_COSTUME`에서 온다** —
    표본·전신·여기가 같은 정본 문구를 써야 층이 갈리지 않는다(figure_prompt와 같은 규약).

    **왜 이 단계가 필요한가**: 소거 실험(§9-33)에서 `fig_cn 0.0`의 골리앗이 판금 어깨받이·비늘·
    망토를 갖춰 훨씬 좋았다. `run_figures` docstring의 예언 그대로 **CN 0.8은 구조를 주고 내부
    질감을 앗아간다**(「이 그림은 이 선이 전부」가 되어 안을 비운다). 몸통만 낮은 CN으로 다시
    그리면 구조는 2단계가 지킨 채 질감만 되찾는다. 축 F(갑주 착용) 여유가 늘 얇았던 자리다."""
    axes = read_axes(name)
    en = {k: AXIS_EN[k][v] for k, v in axes.items()}
    torso_style = _drop(STYLE, "simple", "clean background", "light shading", "muted palette")
    art = "an" if read_brief(name)[0].lower() in "aeiou" else "a"
    prompt = (f"{torso_style} torso and shoulders of {art} {read_brief(name)} "
              f"{SAMPLE_COSTUME[name]}, close view of the fabric and metal, "
              f"crisp material detail.")
    neg = ", ".join([_drop(NEG, "dark", "heavy shadows"), "blank, featureless, flat, empty surface"]
                    + [v[1] for v in en.values() if v[1]])
    return prompt, neg


def figure_prompt(name):
    """전신 한 명. 순서는 portrait_prompt와 같다(나이 → 개요 → 머리카락 → 머리쓰개) —
    앞일수록 CLIP에 세게 걸리므로 정체성 조각을 앞에 두고 동작을 뒤에 붙인다."""
    axes = read_axes(name)
    en = {k: AXIS_EN[k][v] for k, v in axes.items()}
    parts = [en["age"][0], read_brief(name), en["hair"][0], en["headwear"][0]]
    body = ", ".join(p for p in parts if p)
    art = "an" if body[0].lower() in "aeiou" else "a"
    # 2026-08-29 **장면의 인물 단계에 의상이 없었다.** 그래서 장면은 갑주를 말로 지시받은 적이
    # 없고 유일한 신호가 IP 레퍼런스였는데, 그것은 갑주 **구조**를 전이하지 못한다 — 표본을
    # 어린갑으로 바꿔도 장면의 골리앗이 그대로였던 실측이 그 증거다(ZIMAGE §9-18).
    # 의상은 `SAMPLE_COSTUME`에서 온다 — 표본과 장면이 **같은 정본 문구**를 쓰게 해 두 층이 갈리지
    # 않게 한다. 배경 조각은 뺀다(토큰 확보 · 억제는 NEG가 진다).
    # --- 인물 단계 전용 화풍/부정 (2026-08-29 라운드 20) ---------------------
    # **인물 단계가 양쪽에서 창백함을 요구하고 있었다.** STYLE이 "light shading, muted palette"로
    # 저대비를 **명시 요구**하고, NEG가 "dark, heavy shadows"로 어두움을 **금지**한다 — 규칙 4가
    # 말한 「같은 대비 자원을 놓고 싸운다」의 텍스트 내부판이다. 그 대가가 실측돼 있다(§9-20):
    # 우리 최종본은 정답지와 **같은 밀도로 그리는데**(밀도 .41~.54 ↔ 정답지 .26~.71) **그린 영역
    # 안이 옅다**(.174~.303 ↔ .275~.638). 한쪽만 풀면 다른 쪽이 계속 당기므로 **둘 다** 푼다 —
    # SAMPLE_STYLE이 표본용으로 이미 쓰는 방식이다. 성공 기준: **그린 영역 안 ink ≥ .275**.
    # ⚠ 배경 단계와 표본 단계는 건드리지 않는다 — 손잡이를 하나만 돌린다.
    # (`_drop`이 이 함수보다 아래에 정의돼 있어 호출 시점에 부른다.)
    figure_style = _drop(STYLE, "simple", "clean background", "light shading", "muted palette")
    prompt = (f"{figure_style} full body of {art} {body} "
              f"{SAMPLE_COSTUME[name]}, {SCENE_ACTION[name]}, on dry ground.")
    # 부정에서도 어두움 금지를 뺀다 — 긍정만 풀면 이쪽이 계속 창백함을 당긴다.
    neg = ", ".join([_drop(NEG, "dark", "heavy shadows")]
                    + [v[1] for v in en.values() if v[1]])
    return prompt, neg


# --- 전신 표본 (task#319 part2 S1) --------------------------------------------
# 표본은 축 A(화풍) 정답지 구간(.102~.221)에 들어야 하는데, S0 실측(s0-baseline.json)은
# 현행 STYLE로 12/12 전부 실패했다(잉크 .0051, 정답지의 1/20~1/43). 계획이 지정한 손잡이는
# 정답지 시트를 IP 레퍼런스로 물리는 것(생성 시 배선 — 이 슬라이스는 GPU 0이라 여기서 하지 않는다).
#
# 그런데 STYLE 자신이 "light shading, muted palette"로 저대비를 **명시 요구**하고, NEG가
# "dark, heavy shadows"로 고대비를 막는다 — PROMPTING.md 4(ControlNet과 프롬프트가 같은 대비
# 자원을 놓고 싸운다)와 같은 충돌이 IP 레퍼런스와 텍스트 사이에도 날 것으로 본다: 레퍼런스가 밀어
# 넣으려는 대비를 텍스트가 도로 깎는다. 그래서 표본용 블록에서 그 두 조각만 뺀다.
#
# **매체 낱말(soft pencil and colored-pencil storybook illustration)은 그대로 둔다** — 유화로
# 매체를 바꾸면 .72로 정답지 구간을 7배 초과했다(PROMPTING.md 3, 표본에서도 같은 초과가 예상된다).
# 그리고 이 형용사 제거만으로 정답지 구간에 닿을 것이라 기대하지도 않는다 — 형용사는 매체의
# 2~3배 힘밖에 없다(PROMPTING.md 3 배수표: 대비 형용사 반전 2×, +부정어 3× vs 매체 교체 140×).
# 이 손질의 목적은 "형용사로 화풍을 세게 만드는 것"이 아니라, **IP 레퍼런스가 낼 대비를 텍스트가
# 반대 방향으로 깎지 않게 하는 것**이다 — 실제로 임계를 넘기는 일은 여전히 레퍼런스의 몫이다.
def _drop(style, *phrases):
    """STYLE·NEG에서 지정한 조각만 뺀다 — 새 문장을 쓰지 않고 정본 상수에서 파생한다.
    NEG는 마침표 없이 끝난다(그대로 concat해 negative_prompt를 잇는 원본 관례) — 뺀 뒤에도
    원본이 가졌던 끝맺음(마침표 유무)을 그대로 보존해, portrait_prompt·figure_prompt와 같은
    ", ".join([NEG, ...]) 이음 방식을 SAMPLE_NEG에도 그대로 쓸 수 있게 한다."""
    tail = "." if style.endswith(".") else ""
    kept = [p for p in style.rstrip(".").split(", ") if p not in phrases]
    return ", ".join(kept) + tail


# 2026-08-29: `"simple", "clean background"`도 뺀다 — 서술적 갑주 문구가 77토큰을 넘겨
# **뒤가 조용히 잘리기** 때문이고, 배경 억제는 이미 부정 프롬프트가 진다
# (`SAMPLE_NEG`의 "cluttered background" · `SAMPLE_NEG_EXTRA`의 "landscape, scenery").
SAMPLE_STYLE = _drop(STYLE, "light shading", "muted palette", "simple", "clean background")
SAMPLE_NEG = _drop(NEG, "dark", "heavy shadows")

# 표본 전용 추가 부정어 — 2026-08-26 실측이 낳은 것이다. 표본은 **레퍼런스 이미지가 아니라
# 정체성·화풍의 운반체**이므로 배경 장면과 잘림이 들어오면 part 3에서 그것까지 전이된다.
# ① 풍경류: 텍스트만 생성이 "simple, clean background" 지시를 무시하고 언덕·풀밭 장면을 냈다.
# ② 잘림류: 정강이에서 프레임이 끊겼다(전신 표본의 정의를 깨뜨린다).
# ③ 측면류: "facing forward"만으로는 3/4 회전을 못 막았다.
# 낱말 수는 77토큰 예산에 맞춰 깎았다 — 첫 시도가 83/77로 넘쳐 뒤쪽의 "woman, girl, female"이
# 조용히 잘렸다(PROMPTING.md 1). 잘린 것이 성별 축이어서 5축 판정이 무음으로 약해진다.
# 그래서 동의 중복(hills·grass·field ⊂ landscape·scenery, "cut off" ⊂ cropped)을 덜어냈다.
SAMPLE_NEG_EXTRA = "landscape, scenery, cropped, close-up, profile view"

# 표본 의상 — **발명하지 않고 프로젝트가 이미 문서화한 어휘를 출처로 쓴다**:
# frontend/src/sketches/lib.jsx의 선화 규약이 「다윗의 **튜닉**」(:115) ·
# 「겉옷/**튜닉**의 외곽선, **허리 매듭**」(:146)을 인물 의상으로 못박아 두었다.
# 왜 필요한가: 레퍼런스 이미지를 빼자(위 --no-ref 근거) 시대 의상 신호도 함께 사라져
# 멜빵·단추셔츠·구두(19세기 서양)가 나왔다(2026-08-26 smoke-r2 실측). 5축·BRIEF에는 의상
# 필드가 없으므로 BG_VOCAB과 같은 「문서화된 어휘 상수」 패턴으로 둔다.
# **인물별로 갈린다.** 2026-08-26 실측: 공통 "linen tunic"을 골리앗에게도 걸자 「튜닉 + 전사」가
# 충돌해 모델이 **중세 유럽 판금 갑주**(면갑 투구·어깨판·망토)를 지어냈다 — 삼상 17:5의 놋투구·
# 어린갑과 다른 시대다. 근거는 notes/PROCESS.md §3-b가 이미 표로 정리한 구절이다:
#   다윗  — 삼상 17:40 목자(막대기·물매·주머니). 갑주는 17:39에서 **벗었다**("익숙치 못하니").
#   골리앗 — 삼상 17:5 「머리에는 놋투구를 썼고 몸에는 어린갑(비늘갑옷)을 입었으니」
#            17:6 「그 다리에는 놋경갑을 쳤고」
# 투구는 AXES.headwear에서 이미 나오므로(read_axes → AXIS_EN) 여기서 되풀이하지 않는다.
SAMPLE_COSTUME = {
    "david": "in a plain linen tunic with a cloth belt",
    # 2026-08-26 사용자 판단: **야만인 스타일**. 그리고 중립적 갑옷 낱말("bronze scale armor")이
    # 모델의 「기사」 사전지식에 4회 연속 졌다(판금·면갑·망토·대검으로 수렴). barbarian은 그
    # 사전지식을 정면으로 밀어내는 낱말이라 접근 자체가 다르다(PROMPTING.md 3 — 낱말의 세기).
    # 갑옷을 벗기는 방향이 아니다: 삼상 17:5의 어린갑은 놋 5000세겔(약 57kg) 중무장이다.
    # 「거칠고 투박한 청동 비늘갑옷」 = 야만인 전사이면서 본문과 어긋나지 않는 읽기다.
    # 2026-08-26 3차: "bronze scale armor"가 계속 **천 튜닉**으로 그려졌다(IP 0.45·0.3 둘 다).
    # 「비늘」이 재질이 아니라 장식으로 읽힌 것으로 보고 **겹침(overlapping)**을 명시해 재질을 지시한다.
    # "and leather straps"를 뺀 자리로 토큰을 확보했다 — 그 낱말은 가죽 팔싸개만 냈고 비늘엔 무관했다.
    # 문구를 줄였다 — 사용자가 준 비늘갑옷 레퍼런스가 **이미지 앵커**로 재질을 나르므로 어휘로
    # 밀 필요가 없어졌고(어휘만으로는 5종 0/5였다), 그 토큰을 headwear의 「뿔」에 넘겼다.
    # **이 문구가 실측 최선이다(`setup/goliath-horned-*`).** 비늘 재질은 어휘로 도달하지 못했다 —
    # 6종 0/6(scale armor / overlapping scale mail / fish-scale over leather jerkin /
    # 맨 앞 배치 / wearing 결속 / 「scale」을 버리고 "rows of overlapping round bronze plates").
    # 마지막 것은 **갑옷을 아예 없앴다** — "armor"라는 낱말이 최소한 옷의 존재는 지키고 있었다.
    # 남은 손잡이는 **이미지 앵커**다(사용자 제공 비늘갑옷 참고 이미지 → `gen_setup_sheet.py --ref`).
    # 2026-08-29 **사용자 지적으로 뒤집힌 자리**: 지금까지의 실패는 전부 **용어 교체**였다
    # (PROMPTING.md 8의 6종 · 라운드 14의 3종 — "scale armor"·"scale mail"·"fish-scale" 등).
    # 모델이 그 낱말을 모른다면 낱말을 바꾸는 것은 무효다. **무엇으로 이루어졌고 어떤 모양인지**
    # 풀어 쓰자 비늘이 실제로 나왔다(ZIMAGE §9-16 실측: 용어 0/3 ↔ 서술 2/3).
    # ⚠ 직유는 **주어에 결속**해야 한다 — "like roof tiles"·"like a pinecone"을 뒤에 달았더니
    #   기와와 솔방울이 **배경 풍경으로** 그려졌다(직유 대상이 장면으로 샌다).
    "goliath": "in a coat of small overlapping bronze plates in rows, like fish scales",

}

# 부정어도 인물별로 갈린다 — 표본은 **중립**이어야 하므로 각 인물이 실제로 끌어들이는 것을 막는다.
# 다윗: 개가 함께 그려졌다(2026-08-26 smoke-r2). 골리앗: 동작 어휘가 없는데도 **대검**을 들었고
# 망토·판금이 붙었다(smoke-r3) — 지물은 장면 단계 소관이므로(계획 Non-goal) 표본에서 뺀다.
SAMPLE_NEG_BY_NAME = {
    "david": "dog, animal",
    # 77토큰 예산에 맞춰 깎았다 — "sword, weapon, cape, plate armor"는 80/77로 넘쳐 뒤쪽의
    # 성별 부정어가 조용히 잘렸다(PROMPTING.md 1). "sword" ⊂ "weapon", "plate armor" → "plate".
    # 판금·기사 사전지식을 이름으로 직접 막는다. 예산 때문에 "sword"⊂"weapon"으로 줄인 채 유지.
    # **`plate, knight`를 빼지 말 것 — 2026-08-26 실측으로 확인했다.** 비늘갑옷 앵커가 있으니
    # 사전지식 방어가 필요 없다고 보고 그 두 낱말을 지물 차단(`shield, spear`)으로 바꿨더니
    # **갑옷이 즉시 판금으로 돌아갔다**(IP 0.18에서는 중세 면갑 투구까지). 앵커는 판금 사전지식을
    # 이기지 못하고, 두 방어가 **함께** 있어야 비늘이 선다.
    # 그리고 `shield, spear`를 넣어도 **창·방패는 그대로 나왔다** — 지물 제거용 부정어는 이
    # 파이프라인에서 반복적으로 무력하다(표본 5회 · 시트 4회 · 여기 2회). 앵커 이미지가 창·방패를
    # 들고 있어 프레이밍과 함께 전이되는 것으로 읽는다(발견 1).
    "goliath": "plate, knight, weapon",
}


def sample_prompt(name):
    """전신 표본 — 중립 정면 단독 전신, 동작 어휘 없음(part2 계획 Non-goal, SCENE_ACTION을
    쓰지 않는다). 정체성 조각(나이·개요·머리카락·머리쓰개)은 figure_prompt와 같은 출처
    (AXIS_EN·read_brief·read_axes)에서 같은 순서로 파생한다. "facing forward"는 새 문구가
    아니라 portrait_prompt가 이미 쓰는 조각을 재사용한 것이고, "standing alone"이 동작 대신
    중립·단독을 명시한다(다포즈 시트를 레퍼런스로 물렸을 때 인물이 3명으로 늘어난 오염 실측이
    있어 "alone"으로 단독을 프롬프트 단에서도 밀어 둔다 — S2가 눈으로 재현 여부를 확인한다)."""
    axes = read_axes(name)
    en = {k: AXIS_EN[k][v] for k, v in axes.items()}
    parts = [en["age"][0], read_brief(name), en["hair"][0], en["headwear"][0]]
    body = ", ".join(p for p in parts if p)
    art = "an" if body[0].lower() in "aeiou" else "a"
    # 프레이밍을 프롬프트에서 강하게 밀어야 한다 — 2026-08-26 실측: 레퍼런스를 아예 빼고
    # 텍스트만으로 뽑으면 축 A는 정답지 구간에 들지만(ink .1849) 산출물이 ①정강이에서 잘린
    # 3/4 측면이고 ②"simple, clean background"를 지시했는데도 언덕·풀밭 장면이 나왔다.
    # 원인은 캔버스가 가로(1216x640)였던 것과 프레이밍 어휘가 약했던 것 둘이다 —
    # 캔버스는 params.SAMPLE_SIZE(세로)로 옮겼고, 여기서는 "head to toe"로 잘림을,
    # "front view"로 3/4 회전을 막는다. 배경은 부정어 쪽에서 죽인다(아래 SAMPLE_NEG_EXTRA).
    prompt = (f"{SAMPLE_STYLE} full body of {art} {body} {SAMPLE_COSTUME[name]}, "
              f"standing alone, facing forward, head to toe.")   # "front view"는 "facing forward"와 중복이라 뺐다(2026-08-29, 토큰 확보)
    neg = ", ".join([SAMPLE_NEG, SAMPLE_NEG_EXTRA, SAMPLE_NEG_BY_NAME[name]]
                    + [v[1] for v in en.values() if v[1]])
    return prompt, neg


def setup_sheet_prompt(name):
    """[[설정화]] 시트 — 인물 하나의 4패널 캐릭터 설정 시트(정답지 계열 자산, task#319 후속).

    **왜 필요한가.** `reference/sheet-s200~203.png` 네 장은 **전부 다윗**이라 골리앗에는 화풍·의상의
    이미지 근거가 없다. 그래서 텍스트만으로 뽑으면 모델의 「판타지 기사」 사전지식이 이긴다 —
    2026-08-26에 부정어를 5회 서로 다르게 강화해도 판금·망토·무기가 남았다. `raster-pilot/FINDINGS.md`가
    이미 「**(인물 × 생애단계) 단위 시트 필요 확정**」이라고 적어 둔 그 후속이다.

    **레퍼런스로 다윗 시트를 물린다 — 그리고 그것이 여기서는 결함이 아니라 이점이다.**
    IP-Adapter 상류의 CLIPImageProcessor가 224 center-crop을 하므로 **레퍼런스의 프레이밍이 전이된다**
    (task#319 발견 1). 장면을 생성할 때는 이 전이가 오염이어서 FINDINGS.md가
    「레퍼런스는 시트가 아니라 시트에서 잘라낸 **얼굴 1컷**이다」로 규칙을 세웠다. **여기는 반대 경우다** —
    우리가 만들려는 것이 시트이므로 「4패널 설정화 레이아웃」의 전이가 곧 목표 프레이밍이다.
    정체성은 텍스트(BRIEF·AXES)가 나르고, 레퍼런스는 화풍과 레이아웃만 나르게 한다 —
    그래서 IP 강도를 정체성 전이용 값(FINDINGS.md의 0.7)보다 **낮게** 잡는 축을 열어 둔다.
    """
    axes = read_axes(name)
    en = {k: AXIS_EN[k][v] for k, v in axes.items()}
    parts = [en["age"][0], read_brief(name), en["hair"][0], en["headwear"][0]]
    body = ", ".join(p for p in parts if p)
    art = "an" if body[0].lower() in "aeiou" else "a"
    # **이 구조가 실측 최선이다(`setup/goliath-ip03-sheet-ip0.3-s11.png`, IP 0.3).**
    # 2026-08-26에 두 변형을 시험해 **둘 다 더 나빴다**(근거는 setup/SETUP.md 표):
    #  ① 의상을 맨 앞으로(PROMPTING.md 2 「앞이 무겁다」) → 변화 없음. 위치는 원인이 아니었다.
    #  ② 의상을 주어에 `wearing …`으로 결속 + 레이아웃 어휘 제거(사용자 지적 "비늘갑옷을 걸친
    #     골리앗") → **투구가 머리에서 벗겨져 별도 패널로 밀려나고, 머리카락이 드러나 5축이 깨졌고,
    #     엘프 귀가 생겼다.** 결속이 의상 슬롯을 키우면서 `headwear` 축을 밀어낸 것으로 읽는다.
    # 레이아웃 어휘는 레퍼런스가 이미 4/4로 나르지만(발견 1), 빼면 위 ②의 부작용과 얽혀 나빠졌으므로
    # 남긴다 — 토큰을 아끼는 것보다 5축을 지키는 것이 우선이다.
    prompt = (f"{SAMPLE_STYLE} {SAMPLE_COSTUME[name]}. character design sheet of {art} {body}, "
              f"full body front view and side view, head study.")
    neg = ", ".join([SAMPLE_NEG, SAMPLE_NEG_BY_NAME[name]]
                    + [v[1] for v in en.values() if v[1]])
    return prompt, neg


def main():
    david_prompt, david_neg, david_axes = portrait_prompt("david")
    goliath_prompt, goliath_neg, goliath_axes = portrait_prompt("goliath")
    prompts = {
        "style": STYLE,
        "negative": NEG,
        "david": {"axes": david_axes, "prompt": david_prompt, "negative": david_neg},
        "goliath": {"axes": goliath_axes, "prompt": goliath_prompt, "negative": goliath_neg},
        "bg_on": {"prompt": f"{STYLE} {SCENE_PERSON} {BG_VOCAB}"},
        # 전신 — 인물 영역 인페인팅용(초상과 목적이 다르다, figure_prompt 주석 참조)
        "figure": {n: dict(zip(("prompt", "negative"), figure_prompt(n)))
                   for n in ("david", "goliath")},
        # 머리 단계 — 인물 단계 위에 머리 밴드만 다시 그린다(head_prompt 주석 참조)
        "head": {n: dict(zip(("prompt", "negative"), head_prompt(n)))
                 for n in ("david", "goliath")},
        # 몸통 단계 — 갑주·의상 질감(torso_prompt 주석 참조)
        "torso": {n: dict(zip(("prompt", "negative"), torso_prompt(n)))
                  for n in ("david", "goliath")},
        # 전신 표본(part2 S1) — 단독 중립 전신. **IP 레퍼런스를 물리지 않는다**(2026-08-26 실측:
        # 레퍼런스는 프레이밍까지 전이시키고, 화풍은 텍스트만으로도 정답지 구간에 든다)
        "sample": {n: dict(zip(("prompt", "negative"), sample_prompt(n)))
                   for n in ("david", "goliath")},
        # [[설정화]] 시트 — 정답지 계열 자산(setup_sheet_prompt 주석 참조)
        "setup_sheet": {n: dict(zip(("prompt", "negative"), setup_sheet_prompt(n)))
                        for n in ("david", "goliath")},
        # task#317 S2 — 조립은 GPU 스크립트가(토큰 예산 때문에). 여기서는 재료만 낸다.
        "scene_identity": {
            "style": STYLE, "frame": SCENE_FRAME,
            "slots": {n: scene_person_slots(n) for n in ("david", "goliath")},
            "negative_extra": SCENE_NEG_EXTRA,
        },
        "bg_off": {"prompt": f"{STYLE} {SCENE_PERSON}"},
    }
    out = params.PROMPTS_JSON
    with open(out, "w", encoding="utf-8") as f:
        json.dump(prompts, f, ensure_ascii=False, indent=2)
    for k, v in prompts.items():
        if isinstance(v, dict) and "prompt" in v:
            print(f"[{k}] {v['prompt']}")
    print(f"기록: {out}")


if __name__ == "__main__":
    main()
