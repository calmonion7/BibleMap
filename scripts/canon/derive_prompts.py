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
    "headwear": {"없음": ("bare head", ""), "투구": ("bronze helmet with cheek guards", "")},
    "age": {"소년/청년": (f"boy of {num_to_words(_DAVID_GOLIATH_AGE)}",
                       "baby, toddler, infant, chibi, doll"),
            "성인": ("grown man of about forty", "child, youth")},
    # 성별은 나이 어휘(boy/man)가 이미 나르므로 긍정 토큰을 쓰지 않고 negative로만 잠근다
    # — 77토큰이 빠듯하다(화풍 블록만 35토큰).
    "sex": {"남": ("", "woman, girl, female")},
}

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
    neg = ", ".join([NEG] + [v[1] for v in en.values() if v[1]])
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
SCENE_ACTION = {"david": "swinging a sling", "goliath": "standing in heavy armor"}


def figure_prompt(name):
    """전신 한 명. 순서는 portrait_prompt와 같다(나이 → 개요 → 머리카락 → 머리쓰개) —
    앞일수록 CLIP에 세게 걸리므로 정체성 조각을 앞에 두고 동작을 뒤에 붙인다."""
    axes = read_axes(name)
    en = {k: AXIS_EN[k][v] for k, v in axes.items()}
    parts = [en["age"][0], read_brief(name), en["hair"][0], en["headwear"][0]]
    body = ", ".join(p for p in parts if p)
    art = "an" if body[0].lower() in "aeiou" else "a"
    prompt = f"{STYLE} full body of {art} {body}, {SCENE_ACTION[name]}, on dry ground."
    neg = ", ".join([NEG] + [v[1] for v in en.values() if v[1]])
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
