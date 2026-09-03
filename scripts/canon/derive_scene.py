#!/usr/bin/env python3
"""장면 명세(`scenes/<id>.json`) → 단계별 영문 프롬프트 파생기 (2026-09-04, task 330).

**한국어 명세가 정본, 영문 프롬프트는 파생물이다**(PROMPTING 1·7 — 손으로 프롬프트를 쓰지 않는다).
생성기(`gen_scripture_scene.py`)와 판정자(`judge_scene.py`)는 둘 다 여기서 명세를 읽는다 —
구역 상자·단계 순서·인물 목록이 **한 파일**에만 있어야 자와 그림이 어긋나지 않는다.

파생 규칙(현행 삼상17 코드와 문자열 동일이 회귀 가드다):
  prompt = f"{ST} {stage.prompt}"           — ST는 derive_prompts.STYLE에서 파생한 공용 화풍 머리
  neg    = NEG + ", " + ", ".join(stage.neg) — NEG는 공용 부정어(액자족 포함)
  자리표시자: `{costume:<cast>}` → derive_prompts.SAMPLE_COSTUME[cast]의 `in ` 뒤 (인물 정본 읽기 인터페이스 —
              내용은 2/7이 채운다) · `{head_neg}` → derive_prompts.HEAD_NEG_EXTRA

사용:
  derive_scene.py <scene-id>            # 단계별 prompt/neg를 찍는다
  derive_scene.py <scene-id> --check    # 토큰 수를 재고 77 초과가 하나라도 있으면 종료코드 1 (GPU 0)
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import params  # noqa: E402
import derive_prompts as dp  # noqa: E402

SCENES_DIR = os.path.join(params.CANON_DIR, "scenes")

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
    return out.replace("{head_neg}", dp.HEAD_NEG_EXTRA)


def stages(spec):
    """→ [{id, kind, region, verse, prompt, neg, skip}] — prompt/neg는 완성 문자열."""
    return [{**s, "prompt": f"{ST} {_fill(s['prompt'])}",
             "neg": NEG + ", " + ", ".join(_fill(n) for n in s["neg"]),
             "skip": s.get("skip")} for s in spec["stages"]]


def regions(spec):
    return {k: tuple(v) for k, v in spec["regions"].items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scene")
    ap.add_argument("--check", action="store_true", help="토큰 수만 재고 끝낸다(GPU 0)")
    a = ap.parse_args()
    spec = load(a.scene)
    tok = None
    if a.check:
        from transformers import CLIPTokenizer
        tok = CLIPTokenizer.from_pretrained(params.SDXL_BASE, subfolder="tokenizer")
    over = []
    for s in stages(spec):
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
