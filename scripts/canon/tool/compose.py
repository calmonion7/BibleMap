#!/usr/bin/env python3
"""단계 문구를 AI가 짓는다 — 사람은 한국어로 시키기만 한다 (2026-09-05, task 339 후속).

**한국어 명세가 정본, 영문 프롬프트는 파생물이다**(PROMPTING 7 — 손으로 프롬프트를 쓰지 않는다).
그 파생을 사람이 영어로 타이핑하던 자리를 AI가 대신한다. 사람은 「사무엘이 기름 뿔을 들게」처럼
한국어로 말하고, 이 모듈이 장면 명세의 한국어 근거와 실측 규칙을 함께 실어 `claude -p`에 넘긴다.

호스트 python3로 돈다(표준 라이브러리 + `claude` CLI). 토큰 재기는 venv 쪽 `count_tokens.py`가 한다.

  SCENE_TOOL_FAKE_AI=1 이면 AI를 부르지 않고 정해진 답을 준다 — 스모크 전용.
"""
import json
import os
import subprocess

CLAUDE = os.environ.get("SCENE_TOOL_CLAUDE", "claude")
FAKE_AI = os.environ.get("SCENE_TOOL_FAKE_AI") == "1"

RULES = """당신은 성경 장면 삽화 파이프라인의 **단계 문구 저작자**다. 아래 실측 규칙을 지킨다.

1. **77토큰이 하드 한계다.** 넘으면 에러 없이 뒤가 잘린다. 화풍 머리 22토큰이 앞에 자동으로 붙으므로
   당신이 쓰는 문구는 **자리표시자를 확장한 뒤 48토큰 이내**(합계 70)를 목표로 한다.
   한계에 붙이지 마라 — 사람이 낱말 하나를 더하면 곧바로 넘어 뒤가 잘린다. 짧을수록 좋다.
2. **문장을 쓰지 않는다.** 쉼표로 끊은 명사구·분사구의 나열이다.
   예: `a wide dry open field, sparse dry grass, hazy low hills far behind, no people.`
3. **인물의 생김새를 직접 쓰지 않는다.** 반드시 `{cast:<id>}` 자리표시자를 쓴다 — 인물 어휘 정본이
   자동으로 확장된다. 시대·민족·나이·머리·수염·복식은 이미 그 안에 있으니 되풀이하지 않는다.
   자리표시자 뒤에는 **자세·손·시선·향하는 쪽**만 붙인다.
4. **형용사보다 대상의 색·매체 낱말이 그림을 움직인다.** 「beautiful」 같은 말은 버린다.
5. **부정어는 짧게.** 그리지 말아야 할 것의 이름만 나열한다. 이미 공용 부정어가 따로 붙는다.
6. 배경 단계는 사람을 그리지 않는다 — 필요하면 `no people`을 넣는다.
7. 가능하면 아래 「이미 쓰는 조각」의 표현을 **그대로 재사용**한다. 그래야 화면에 한글 뜻이 붙는다.

**출력은 JSON 하나뿐이다.** 설명도 코드펜스도 붙이지 않는다.

{"prompt": "<영문 단계 문구, 마침표로 끝냄>",
 "neg": ["<영문 부정어>", ...],
 "why": "<무엇을 왜 이렇게 했는지 한국어 한 줄>",
 "gloss": {"<영문 조각 또는 부정어>": "<한글 뜻>", ...}}

**`gloss`는 빠뜨리지 마라.** 당신이 쓴 문구를 쉼표로 끊은 **모든 조각**과 **모든 부정어**를 열쇠로 넣고,
한글 뜻을 값으로 준다(`{cast:...}` 자리표시자는 뺀다). 화면이 영문 옆에 이 한글을 붙여 주므로,
빠진 것은 사람에게 물음표로 보인다. 뜻은 **명사구는 명사구로, 분사구는 분사구로** 옮긴다 —
「a wide dry open field」는 「넓고 마른 열린 들」, 「facing right」는 「오른쪽을 향함」처럼."""


def briefing(spec, stage, ask, casts, frags):
    """명세의 한국어 근거 + 규칙 + 사람의 지시 → `claude -p`에 넘길 한 덩이."""
    reg = stage["region"]
    figs = [f for f in spec.get("figures", []) if f.get("region") == reg]
    crowds = [c for c in spec.get("crowds", []) if c.get("region") == reg]
    out = [RULES, "", "## 이 장면 (한국어 명세가 정본이다)",
           f"제목: {spec.get('title')}",
           f"본문: {spec['verses'].get('range')}"]
    for k, v in (spec["verses"].get("quotes") or {}).items():
        out.append(f"  {k} {v}")
    out.append(f"고정한 순간: {(spec.get('moment') or {}).get('why', '')}")
    if spec.get("background"):
        out.append("배경: " + " · ".join(b["what"] for b in spec["background"]))
    if spec.get("crowds"):
        out.append("무리: " + " · ".join(c["what"] for c in spec["crowds"]))
    if spec.get("figures"):
        out.append("인물: " + " · ".join(
            f"{f['cast']}={f.get('role', '')}({f.get('pose', '')}, {f.get('facing', '')})"
            for f in spec["figures"]))

    out += ["", "## 지금 고치는 단계",
            f"id {stage['id']} · 종류 {stage['kind']} · 구역 {reg} {spec['regions'][reg]}"]
    kind_hint = {"full": "배경 전체를 칠한다 — 사람을 그리지 않는다.",
                 "region": "구역 하나에 지물·구조물을 그린다.",
                 "ridge": "능선 띠에 멀리 있는 작은 것들을 그린다.",
                 "plate": "인물 한 사람을 민 종이에 그려 오려 붙인다 — 배경을 그리지 않는다."}
    if stage["kind"] in kind_hint:
        out.append(kind_hint[stage["kind"]])
    if figs:
        out.append("이 구역의 인물: " + " · ".join(
            f"{f['cast']} — {f.get('role', '')} / 자세 {f.get('pose', '')} / 지물 {f.get('prop', '')}"
            f" / {f.get('facing', '')}" for f in figs))
    if crowds:
        out.append("이 구역의 무리: " + " · ".join(c["what"] for c in crowds))
    out += [f"지금 문구: {stage.get('prompt', '')}",
            f"지금 부정어: {', '.join(stage.get('neg') or [])}"]

    if casts:
        out += ["", "## 쓸 수 있는 인물 자리표시자 (확장되는 영문까지)"]
        out += [f"  {{cast:{cid}}} → {txt}" for cid, txt in casts.items()]

    out += ["", "## 이미 쓰는 조각 (되도록 재사용)", ", ".join(sorted(frags))]
    out += ["", "## 사람의 지시 (한국어)", ask.strip() or "(지시 없음 — 위 명세대로 지금 문구를 다듬어라)"]
    return "\n".join(out)


def _parse(text):
    """모델이 앞뒤에 무엇을 붙이든 **마지막 JSON 객체**를 집어낸다."""
    start = text.rfind("{")
    while start != -1:
        try:
            obj = json.loads(text[start:text.rindex("}") + 1])
            if isinstance(obj, dict) and "prompt" in obj:
                return obj
        except (ValueError, json.JSONDecodeError):
            pass
        start = text.rfind("{", 0, start)
    raise RuntimeError(f"AI 응답에서 JSON을 못 찾았다: {text[-400:]}")


def compose(spec, stage, ask, casts, frags, timeout=180):
    if FAKE_AI:
        return {"prompt": f"a test field, {ask.strip()[:20] or 'no people'}, no people.",
                "neg": ["people", "modern"], "why": "가짜 AI — 스모크 전용",
                "gloss": {"a test field": "시험용 들", "modern": "현대풍"}}
    text = briefing(spec, stage, ask, casts, frags)
    r = subprocess.run([CLAUDE, "-p", text], capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0:
        raise RuntimeError(f"claude 호출이 실패했다({r.returncode}): {(r.stderr or r.stdout)[-400:]}")
    out = _parse(r.stdout)
    out["neg"] = [str(n) for n in (out.get("neg") or [])]
    out["prompt"] = str(out["prompt"]).strip()
    out["gloss"] = {str(k): str(v) for k, v in (out.get("gloss") or {}).items()}
    return out


TRANSLATE = """아래는 성경 장면 삽화 프롬프트에 쓰인 영문 조각들이다. 각각의 **한글 뜻**을 준다.

- 명사구는 명사구로, 분사구는 분사구로 옮긴다. 문장으로 풀지 않는다.
  「a wide dry open field」→「넓고 마른 열린 들」 · 「facing right」→「오른쪽을 향함」
  「gripping one sword」→「칼 하나를 쥔」 · 「no people」→「사람 없음」
- 그림을 그리라는 지시가 아니라 **낱말의 뜻**만 옮긴다.

출력은 JSON 하나뿐이다. 설명도 코드펜스도 붙이지 않는다.
{"<영문 조각>": "<한글 뜻>", ...}

## 옮길 조각
"""


def translate(terms, timeout=180):
    """용어집에 없는 조각들의 한글 뜻만 받아 온다 — 사람이 손으로 고쳐 넣은 표현을 위한 길."""
    terms = [t for t in terms if t.strip()]
    if not terms:
        return {}
    if FAKE_AI:
        return {t: f"[가짜]{t}" for t in terms}
    r = subprocess.run([CLAUDE, "-p", TRANSLATE + "\n".join(f"- {t}" for t in terms)],
                       capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0:
        raise RuntimeError(f"claude 호출이 실패했다({r.returncode}): {(r.stderr or r.stdout)[-400:]}")
    start = r.stdout.rfind("{")
    if start == -1:
        raise RuntimeError(f"응답에서 JSON을 못 찾았다: {r.stdout[-300:]}")
    got = json.loads(r.stdout[start:r.stdout.rindex("}") + 1])
    return {str(k): str(v) for k, v in got.items()}
