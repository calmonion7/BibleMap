#!/usr/bin/env python3
"""장면 명세(`scenes/<id>.json`) → 단계별 영문 프롬프트 파생기 (2026-09-04, task 330).

**한국어 명세가 정본, 영문 프롬프트는 파생물이다**(PROMPTING 1·7 — 손으로 프롬프트를 쓰지 않는다).
생성기(`gen_scripture_scene.py`)와 판정자(`judge_scene.py`)는 둘 다 여기서 명세를 읽는다 —
구역 상자·단계 순서·인물 목록이 **한 파일**에만 있어야 자와 그림이 어긋나지 않는다.

파생 규칙(현행 삼상17 코드와 문자열 동일이 회귀 가드다):
  prompt = f"{ST} {stage.prompt}"           — ST는 derive_prompts.STYLE에서 파생한 공용 화풍 머리
  neg    = NEG + ", " + ", ".join(stage.neg) — NEG는 공용 부정어(액자족 포함)
  자리표시자: `{costume:<cast>}` → derive_prompts.SAMPLE_COSTUME[cast]의 `in ` 뒤 (삼상17 호환) ·
              `{cast:<id>}` → cast/<id>.json 어휘 정본 전체 문구(cast_describe — 2/7 판 시트와 같은 문구) · `{head_neg}` → HEAD_NEG_EXTRA

사용:
  derive_scene.py <scene-id>            # 단계별 prompt/neg를 찍는다
  derive_scene.py <scene-id> --check    # 토큰 수를 재고 77 초과가 하나라도 있으면 종료코드 1 (GPU 0)
  derive_scene.py <scene-id> --figures whole [--check]   # 장면 한 장 프롬프트 하나(task 345) — --check는 필드·gaze·문구 포함 검사
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import params  # noqa: E402
import derive_prompts as dp  # noqa: E402

SCENES_DIR = os.path.join(params.CANON_DIR, "scenes")
CAST_DIR = os.path.join(params.CANON_DIR, "cast")


def load_cast(cid):
    with open(os.path.join(CAST_DIR, f"{cid}.json"), encoding="utf-8") as fh:
        return json.load(fh)


CAST_RE = re.compile(r"\{castc?:([a-z0-9-]+)\}")


NOUN = {("male", False): "man", ("male", True): "boy", ("female", False): "woman", ("female", True): "girl"}
HEIGHT = {"short": "short of stature", "tall": "tall of stature", "towering": "towering in height"}


def _who(c):
    """시대·민족 + 성별 명사 + 신분(task 353). 성별을 `age` 낱말에 묻지 않고 `sex`에서 고정한다
    — 골리앗 「warrior」·병기 든 자 「young soldier」에는 남성 명사가 없었다."""
    young = c.get("card", {}).get("ageBand", {}).get("class") in ("child", "youth")
    who = f"{c['era']} {NOUN[(c['sex'], young)]}"
    if c.get("role"):
        who += f", {'an' if c['role'][0] in 'aeiou' else 'a'} {c['role']}"
    return who


def head_text(card):
    """카드 층 머리 윤곽 → 프롬프트 문구. class `bare`는 「머리쓰개 없음」이라는 뜻인데, 문구의 `bare head`를
    Z-Image가 **민머리**로 그린다(353 실측: 사울 정본 16/16 대머리, 346도 같은 함정) — 그 낱말을 빼고 머리털을 덮게 한다."""
    t = card["headOutline"]["text"]
    if card["headOutline"]["class"] == "bare":
        t = re.sub(r"^bare head,\s*", "", t) + ", hair covering the whole head, no headwear"
    return t


def cast_describe(c):
    """어휘 정본 → 인물 서술 한 구절(task 331 → 353). 시대·민족 낱말이 맨 앞(PROMPTING 2·14). `none` 필드는 뺀다.
    장면 판 프롬프트의 `{cast:<id>}`와 판 시트(`gen_cast_plate.py`)가 **같은 문구**를 쓴다 — ADR 260904-055320 1항.
    task 353: 맨 앞은 「era + 성별 명사 + role + 카드 층 ageBand」, 이어서 카드 층 text(수염·체형·머리 윤곽).
    v1의 정도 낱말(`age`·`beard`·`build`·`headwear`)은 카드 층과 겹치므로 빼고 카드 쪽을 남긴다.
    `build: none`(장면 `cast_override`)이면 키 낱말도 뺀다 — 엔게디 사울 웅크림(r4 실측)."""
    card = c.get("card")
    if not card:  # eco: cast-vocab-1 파일 호환 — 지금은 29명 전부 v2
        parts = [f"{_who(c)}, {c['age']}"]
        parts += [c[k] for k in ("hair", "beard", "headwear", "build") if c.get(k) and c[k] != "none"]
        return ", ".join(parts + [c["costume"]])
    parts = [_who(c), card["ageBand"]["text"]]
    if c.get("build") != "none" and card.get("heightRel") in HEIGHT:
        parts.append(HEIGHT[card["heightRel"]])
    if card["beardVolume"]["class"] != "none":
        parts.append(card["beardVolume"]["text"])
    parts += [card["silhouette"]["text"], head_text(card)]
    if c.get("hair") and c["hair"] != "none" and card["headOutline"]["class"] != "bare":  # bare면 윤곽 text가 머리털을 말함
        parts.append(c["hair"])
    if c.get("costume"):  # 한 장 모드는 장면 차림을 따로 잇는다(task 363) — 빈 차림은 넣지 않는다
        parts.append(c["costume"])
    return ", ".join(parts)


def cast_describe_compact(c):
    """어휘 정본 → **짧은** 인물 서술(task 337, 장면 안 경로의 그룹 단계 전용).

    얼굴 앵커가 얼굴을 지므로 머리·수염·머리쓰개·체격 낱말을 뺀다. 한 프롬프트에 두 사람을
    온전한 서술로 넣으면 77토큰을 넘기 때문이다 — 실측: 사무엘 22낱말 → 14낱말, 사울 24 → 13.
    ⚠ 앵커가 없는 인물에게 쓰면 정체를 지탱할 것이 사라진다. 그룹 단계에서만 쓴다.
    task 353: 성별 명사를 넣는다(`_who`)."""
    return f"{_who(c)}, {c['age']}, {c['costume']}"

# 장면 공용 화풍 머리·부정어 — 장면마다 바뀌지 않는다(실측으로 정한 값, 명세 밖 공통 상수).
ST = dp._drop(dp.STYLE, "simple", "clean background", "light shading", "muted palette")
NEG = dp._drop(dp.NEG, "dark", "heavy shadows") + (
    # 2026-08-31 실측: NEG에 이미 `frame, border`가 있는데도 **액자·매트가 그려졌다**.
    # 종이 화풍(「미색 종이」)이 「종이에 붙인 그림」으로 읽힌 것으로 보고 액자류를 늘린다.
    ", framed, picture frame, matte, passepartout, vignette, paper edge, torn paper")


def load(scene_id):
    with open(os.path.join(SCENES_DIR, f"{scene_id}.json"), encoding="utf-8") as fh:
        return json.load(fh)


def _fill(text):
    out = text
    for cast in dp.SAMPLE_COSTUME:
        out = out.replace(f"{{costume:{cast}}}", dp.SAMPLE_COSTUME[cast][3:])   # `in ` 뒤
    for cid in set(re.findall(r"\{cast:([a-z0-9-]+)\}", out)):                 # 인물 정본 전체 문구(task 331 이후)
        out = out.replace(f"{{cast:{cid}}}", cast_describe(load_cast(cid)))
    for cid in set(re.findall(r"\{castc:([a-z0-9-]+)\}", out)):                # 짧은 문구(task 337 그룹 단계)
        out = out.replace(f"{{castc:{cid}}}", cast_describe_compact(load_cast(cid)))
    return out.replace("{head_neg}", dp.HEAD_NEG_EXTRA)


def _build(s, kind, regions, prompt_raw, neg_raw):
    return {**s, "kind": kind, "regions": list(regions),
            "prompt": f"{ST} {_fill(prompt_raw)}",
            "neg": NEG + ", " + ", ".join(_fill(n) for n in neg_raw),
            "skip": s.get("skip"),
            "casts": list(dict.fromkeys(CAST_RE.findall(prompt_raw)))}


def stage_plan(spec, figures="plate"):
    """→ [(원본 단계 dict, kind, regions)] — **프롬프트를 채우지 않는 구조만**의 단계 목록.

    판정자(`judge_scene.configure`)가 생성기와 **같은 목록**을 보게 하려고 뺐다. 그룹이 한 단계로
    합쳐지면 산출물 파일도 하나뿐인데, 판정자가 옛 목록을 보면 없는 단계를 찾고 그룹 상자를
    반쪽만 잰다 — 이 파일 머리말의 「자와 그림이 어긋나면 안 된다」가 그 뜻이다."""
    if figures != "inscene":
        return [(s, s["kind"], [s["region"]]) for s in spec["stages"]]
    by_id = {s["id"]: s for s in spec["stages"]}
    lead, absorbed = {}, {}
    for g in spec.get("groups", []):
        ids = g["stages"]
        lead[ids[0]] = g
        for i in ids[1:]:
            absorbed[i] = ids[0]
    out = []
    for s in spec["stages"]:
        if s["id"] in absorbed:
            continue
        if s["id"] in lead:
            out.append((s, "scene", [by_id[i]["region"] for i in lead[s["id"]]["stages"]]))
        else:
            out.append((s, "scene" if s["kind"] == "plate" else s["kind"], [s["region"]]))
    return out


def stages(spec, figures="plate"):
    """→ [{id, kind, region, regions, verse, prompt, neg, skip, casts}] — prompt/neg는 완성 문자열.

    `figures="inscene"`(task 337)이면 판 단계를 **장면 안 인페인팅**(kind `scene`)으로 바꾸고,
    명세의 `groups`에 묶인 단계들은 **한 단계로 합친다** — 두 인물이 한 마스크 안에서 함께
    그려져야 서로 닿을 수 있다(각자 다른 상자에 따로 그리면 기하학적으로 불가능하다).
    기본값 `"plate"`는 문자열까지 종전과 같다 — 봉인된 삼상17의 회귀 가드다."""
    grp = {g["stages"][0]: g for g in spec.get("groups", [])} if figures == "inscene" else {}
    return [_build(s, kind, regs,
                   grp[s["id"]]["prompt"] if s["id"] in grp else s["prompt"],
                   grp[s["id"]]["neg"] if s["id"] in grp else s["neg"])
            for s, kind, regs in stage_plan(spec, figures)]


WHOLE_NEG = NEG + ", crown, modern clothes, duplicated figures, extra people, cropped, cut off"
# 「royal robe」는 일부러 뺐다 — cast/saul.json neg에 있어 344가 엔게디 사울(겉옷 자락이 베인 겉옷, 삼상 24:4·11)을 지웠다.
VIEWER = "viewer"  # gaze 예약값: 인물이 아니라 관람자(백성) 쪽
DOWN = "down"  # gaze 예약값: 아래를 보며 모름(엔게디 사울 24:4)
AHEAD = "ahead"  # gaze 예약값: 화면 오른쪽 어귀를 똑바로 바라봄(엔게디 사울, r4)
# 화면 기준 방향(r4, 실측 0/12 → 4/4): 인물별 선택 필드 screen_facing → (인물 절 문구, 전원 같을 때 장면 문장 동사구)
SCREEN_FACING = {
    "right": ("facing toward the right edge of the picture", "face toward the right edge of the picture"),
    "left": ("facing toward the left edge of the picture", "face toward the left edge of the picture"),
    "viewer": ("facing the viewer", "face the viewer"),
    "away": ("turned away from the viewer, back to the viewer", "are turned away from the viewer"),
}
PHRASE_KEYS = ("expression", "gesture", "costume")
OUT_OF_TEXT = "본문 밖 · 저작자 정함"


def _side(fig, spec):
    r = spec["regions"][fig["region"]]
    cx = (r[0] + r[2]) / 2
    return "on the left" if cx < 0.4 else "on the right" if cx > 0.6 else "in the center"


def _cast_in_scene(f):
    """cast 정본 + 이 장면 한정 덮어쓰기(`cast_override`, 근거 `cast_override_why` 필수).
    정본 낱말이 장면 자세와 부딪힐 때 쓴다 — 엔게디 24:3-4 사울의 'tall king·a head taller'가 웅크림을 세웠다(r4 실측)."""
    return {**load_cast(f["cast"]), **f.get("cast_override", {})}


def whole_prompt(spec):
    """장면 한 장 프롬프트 하나(task 345). 화풍 머리 + 배경 + 인물마다(위치·cast 정본·표정·몸짓·복식·시선) + 관계.
    필드의 en 문구를 **그대로** 잇는다 — 손으로 쓴 영문은 없다(PROMPTING 7)."""
    figs = sorted(spec["figures"], key=lambda f: spec["regions"][f["region"]][0])
    by_cast = {f["cast"]: f for f in figs}
    parts = [spec["whole_background"]["en"] + "."]
    # 전원 같은 방향의 장면 문장(「Both figures face …」)은 두지 않는다 — 인물마다 방향 구절이 지고(task 363 r2: 빼면 사울이 돌아섬)
    for f in figs:
        if isinstance(f["gaze"], dict):  # 문구 객체 {ko,en,verse} — en을 그대로 시선 구절로(task 365, PROMPTING 7)
            looks = f["gaze"]["en"]
        elif f["gaze"] == VIEWER:  # eco: 백성=관람자 쪽 시선은 cast 대상이 아니라 예약어 하나로
            looks = "looking straight out toward the crowd and the viewer"
        elif f["gaze"] == AHEAD:
            looks = "looking straight ahead toward the right edge of the picture"
        elif f["gaze"] == DOWN:
            looks = "eyes lowered, looking at the ground, unaware"
        else:
            tgt = by_cast[f["gaze"]]
            looks = f"looking toward the {_cast_in_scene(tgt)['age']} {_side(tgt, spec)}"
        # 차림은 장면 명세가 덮어쓴다(용어집 「카드 층 / 얼굴 층」) — 정본 costume은 빼고 장면 costume을 몸짓 뒤에 한 번(task 363)
        c, cost = {**_cast_in_scene(f), "costume": ""}, [f["costume"]["en"]]
        if "beardless" in cost[0]:  # costume이 cast의 수염·복식을 덮어쓴다 — 모순·중복 방지, v2 카드 층 수염도 끈다(task 363)
            c, cost = {**c, "beard": "none", "costume": cost[0]}, []
            if c.get("card"):
                c["card"] = {**c["card"], "beardVolume": {"class": "none", "text": ""}}
            if c["costume"].startswith("a Philistine"):  # cast의 era·age('unarmed … servant')가 투구 문구와 충돌 — 함께 대체
                c = {**c, "era": "a Philistine", "age": ""}
        facing = [SCREEN_FACING[f["screen_facing"]][0]] if f.get("screen_facing") else []
        parts.append(", ".join([f"{_side(f, spec).capitalize()}: {cast_describe(c)}", f["expression"]["en"],
                                f["gesture"]["en"], *cost, looks, *facing]) + ".")
    parts.append(spec["relation"]["en"] + ".")
    if spec.get("screen_light"):  # 선택: 화면 기준 빛 방향 {ko,en,verse}
        parts.append(spec["screen_light"]["en"] + ".")
    return f"{ST} " + " ".join(parts)


def route_prompt(spec):
    """task 375·376 경로 규칙: 한 장 모드 칸(whole_background)이 있으면 whole_prompt, 없으면 plate_whole_prompt."""
    return (whole_prompt if "whole_background" in spec else plate_whole_prompt)(spec)


def plate_whole_prompt(spec):
    """한 장 모드 칸이 없는 판 단계 명세 → 한 장 프롬프트(task 368, 사용자 결정 — 명세 수정 없음).
    판 단계 문구를 **그대로** 잇는다: 화풍 머리 + 배경(full) + 구역·무리 단계 + 인물마다 「위치: 판 문구」 + `groups` 묶음 문구.
    판 단계의 「no people」은 인물을 따로 얹던 경로의 말이라 뗀다."""
    bare = lambda t: re.sub(r",?\s*no people\.?\s*$", "", _fill(t).strip()).rstrip(". ") + "."
    st = spec["stages"]
    parts = [bare(s["prompt"]) for s in st if s["kind"] == "full"]
    parts += [bare(s["prompt"]) for s in st if s["kind"] not in ("full", "plate")]
    for f in sorted(spec["figures"], key=lambda f: spec["regions"][f["region"]][0]):
        s = next(x for x in st if x["kind"] == "plate" and x["region"] == f["region"])
        parts.append(f"{_side(f, spec).capitalize()}: {bare(s['prompt'])}")
    parts += [bare(g["prompt"]) for g in spec.get("groups", [])]
    return f"{ST} " + " ".join(parts)


def check_whole(spec):
    """→ 위반 문자열 목록(빈 목록이면 통과). 토큰 한도 대신 필드 존재·gaze 실존·파생 프롬프트 포함을 본다."""
    bad = []

    def field(obj, name, where):
        v = obj.get(name)
        ok = isinstance(v, dict) and all(isinstance(v.get(k), str) and v[k].strip() for k in ("ko", "en", "verse"))
        if not ok:
            bad.append(f"{where}.{name}: ko/en/verse 가 비어 있거나 없다")
        return v if ok else None

    for name in ("meaning", "relation", "whole_background"):
        field(spec, name, "장면")
    if "screen_light" in spec:
        field(spec, "screen_light", "장면")
    casts = {f["cast"] for f in spec["figures"]}
    for f in spec["figures"]:
        if f.get("screen_facing", "right") not in SCREEN_FACING:
            bad.append(f"{f['cast']}.screen_facing: {f['screen_facing']!r} 는 {sorted(SCREEN_FACING)} 중 하나여야 한다")
        for k in PHRASE_KEYS:
            field(f, k, f["cast"])
        if "cast_override" in f:
            unknown = set(f["cast_override"]) - set(load_cast(f["cast"]))
            if unknown or not str(f.get("cast_override_why", "")).strip():
                bad.append(f"{f['cast']}.cast_override: cast에 없는 키 {sorted(unknown)} 또는 cast_override_why 없음")
        g = f.get("gaze")
        if isinstance(g, dict):  # 문구 객체 — ko/en/verse 모두 있어야 한다(task 365)
            field(f, "gaze", f["cast"])
        elif g not in (VIEWER, DOWN, AHEAD) and (g not in casts or g == f["cast"]):
            bad.append(f"{f['cast']}.gaze: 대상 인물 {g!r}이 이 장면에 없다")
    if bad:
        return bad
    prompt = whole_prompt(spec)
    need = [("relation", spec["relation"]["en"]), ("whole_background", spec["whole_background"]["en"])]
    need += [(f"{f['cast']}.{k}", f[k]["en"]) for f in spec["figures"] for k in PHRASE_KEYS]
    if spec.get("screen_light"):
        need.append(("screen_light", spec["screen_light"]["en"]))
    bad += [f"{n}: 파생 프롬프트에 문구가 없다" for n, s in need if s not in prompt]
    return bad


def regions(spec):
    return {k: tuple(v) for k, v in spec["regions"].items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scene")
    ap.add_argument("--check", action="store_true", help="토큰 수만 재고 끝낸다(GPU 0)")
    ap.add_argument("--figures", choices=("plate", "inscene", "whole"), default="plate")
    a = ap.parse_args()
    spec = load(a.scene)
    if a.figures == "whole":
        if a.check:
            bad = check_whole(spec)
            for b in bad:
                print(f"[Derive] {a.scene} {b}", file=sys.stderr)
            print(f"{a.scene} whole {'통과' if not bad else f'위반 {len(bad)}건'}")
            return 1 if bad else 0
        print(f"[whole {a.scene}]\n  + {whole_prompt(spec)}\n  - {WHOLE_NEG}")
        return 0
    tok = None
    if a.check:
        from transformers import CLIPTokenizer
        tok = CLIPTokenizer.from_pretrained(params.SDXL_BASE, subfolder="tokenizer")
    over = []
    for s in stages(spec, a.figures):
        tag = f"{s['id']} {s['region']} {s['verse']}" + (" (skip)" if s["skip"] else "")
        print(f"[{tag}]\n  + {s['prompt']}\n  - {s['neg']}")
        if tok is not None:
            lim = tok.model_max_length
            n_p, n_n = len(tok(s["prompt"]).input_ids), len(tok(s["neg"]).input_ids)
            # 부정어는 판 단계에서 `_fit_neg`가 예산 안에 싸므로 긍정만 가드다(넘치면 조용히 잘린다).
            flag = "" if n_p <= lim else " ← 넘친다"
            print(f"  토큰 긍정 {n_p}/{lim}{flag} · 부정 {n_n}/{lim}")
            if n_p > lim and not s["skip"]:
                over.append(s["id"])
    if over:
        sys.exit(f"프롬프트가 한도를 넘었다: {', '.join(over)} — 조용히 잘리므로 생성하지 않는다")
    return 0


if __name__ == "__main__":
    sys.exit(main())
