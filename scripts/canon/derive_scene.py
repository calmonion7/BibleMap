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


def cast_describe(c):
    """어휘 정본 → 인물 서술 한 구절(task 331). 시대·민족 낱말이 맨 앞(PROMPTING 2·14). `none` 필드는 뺀다.
    장면 판 프롬프트의 `{cast:<id>}`와 판 시트(`gen_cast_plate.py`)가 **같은 문구**를 쓴다 — ADR 260904-055320 1항."""
    parts = [f"{c['era']} {c['age']}"]
    parts += [c[k] for k in ("hair", "beard", "headwear", "build") if c.get(k) and c[k] != "none"]
    parts.append(c["costume"])
    return ", ".join(parts)


def cast_describe_compact(c):
    """어휘 정본 → **짧은** 인물 서술(task 337, 장면 안 경로의 그룹 단계 전용).

    얼굴 앵커가 얼굴을 지므로 머리·수염·머리쓰개·체격 낱말을 뺀다. 한 프롬프트에 두 사람을
    온전한 서술로 넣으면 77토큰을 넘기 때문이다 — 실측: 사무엘 22낱말 → 14낱말, 사울 24 → 13.
    ⚠ 앵커가 없는 인물에게 쓰면 정체를 지탱할 것이 사라진다. 그룹 단계에서만 쓴다."""
    return f"{c['era']} {c['age']}, {c['costume']}"

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


def regions(spec):
    return {k: tuple(v) for k, v in spec["regions"].items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scene")
    ap.add_argument("--check", action="store_true", help="토큰 수만 재고 끝낸다(GPU 0)")
    ap.add_argument("--figures", choices=("plate", "inscene"), default="plate")
    a = ap.parse_args()
    spec = load(a.scene)
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
