#!/usr/bin/env python3
"""장면 명세(`scenes/*.json`) 기계 검사 (task 332 S1). GPU 0.

  check_scenes.py [<scene-id> ...]      # 인자 없으면 scenes/ 전부. 하나라도 낙제면 종료코드 1.

검사 항목(3/7 DoD 2): 필수 필드 · 인용 절이 verses.json에 존재 · figures[].prop 1개 · figures[].cast가 cast/<id>.json에 존재 ·
구역 상자 [0,1] 안(x0<x1, y0<y1) · stages/figures/crowds/judge가 가리키는 구역이 regions에 있음 · judge.figures ⊆ figures.cast.
task 363: 한 장 프롬프트(`derive_scene.whole_prompt`)가 Z-Image 인코더 상한 512토큰(채팅 틀 포함) 안 — 넘는 뒤쪽은 잘려 무처치다.
  토크나이저(HF 캐시, 오프라인)가 필요하므로 venv314로 실행한다. 못 불러오면 실패로 보고한다.
task 375: 구절 시각 요소(`verse_elements`)가 있는 장면은 요소마다 인용·칸·파생 프롬프트 문구를 짝짓고, 「못 그림」류 제외 사유는 실패.
  대상 14장면(params.VERSE_ELEMENT_SCENES)에 목록이 없으면 「미작성」 경고, 끝에 「구절 요소: N/14 장면」(notes/VERSE-ELEMENTS.md).
task 387: 장면 구절 상황 칸(`situation`)이 있는 명세는 text가 비지 않고 same_time 키가 quotes 키와 같아야 한다(없는 명세는 그대로).
"""
import glob
import json
import os
import re
import sys

import params

SCENES = os.path.join(params.CANON_DIR, "scenes")
CAST = os.path.join(params.CANON_DIR, "cast")
VERSES = os.path.join(params.REPO_ROOT, "data", "bible", "verses.json")
BOOK = {"삼상": 9, "삼하": 10, "왕상": 11, "왕하": 12, "대상": 13, "대하": 14, "시": 19}
REQUIRED = ("id", "title", "verses", "moment", "background", "figures", "regions", "stages", "judge")
KINDS = {"full", "region", "ridge", "plate", "refine", "prop"}
WHOLE_MAX = 512   # diffusers ZImagePipeline.encode_prompt max_sequence_length(truncation=True) — task 362 실측
# 넘어도 되는 장면 → 이유. 512 안에 들어오면 검사가 「예외 지울 것」으로 실패한다(낡은 예외 방지).
WHOLE_OVER_OK = {}


def verse_ids(book, ref):
    """'17:4-7' / '17:7 · 17:41' / '10:17–24' → verseID 목록. 장 하나에 절 범위."""
    out = []
    for part in re.split(r"[·,]", ref):
        m = re.match(r"\s*(\d+):(\d+)(?:\s*[-–~]\s*(\d+))?", part)
        if not m:
            continue
        ch, a, b = int(m.group(1)), int(m.group(2)), int(m.group(3) or m.group(2))
        out += [f"{book:02d}{ch:03d}{v:03d}" for v in range(a, b + 1)]
    return out


def check(spec, verses):
    errs = []
    for k in REQUIRED:
        if k not in spec:
            errs.append(f"필수 필드 없음: {k}")
    if errs:
        return errs
    # 절 존재 — range의 책 약칭으로 quotes 키를 푼다
    m = re.match(r"(삼상|삼하|왕상|왕하|대상|대하|시)\s*(\d+):", spec["verses"].get("range", ""))
    if not m:
        errs.append(f"verses.range 형식: {spec['verses'].get('range')!r} (예: 삼상 17:1-49)")
    else:
        book = BOOK[m.group(1)]
        for ref, text in spec["verses"].get("quotes", {}).items():
            ids = verse_ids(book, ref)
            if not ids:
                errs.append(f"quotes 키 형식: {ref!r}")
            for vid in ids:
                if vid not in verses:
                    errs.append(f"절 없음: {ref} ({vid})")
            if not text.strip():
                errs.append(f"인용 비어 있음: {ref}")
    # 장면 구절 상황 칸(task 387) — 있는 명세만: 같은 때 이유가 인용 절마다 하나씩
    if "situation" in spec:
        sit = spec["situation"]
        if not str(sit.get("text", "")).strip():
            errs.append("situation.text 비어 있음")
        if set(sit.get("same_time") or {}) != set(spec["verses"].get("quotes", {})):
            errs.append(f"situation.same_time 키 ≠ quotes 키: {sorted(sit.get('same_time') or {})}")
    regs = spec["regions"]
    if "full" not in regs:
        errs.append("regions.full 없음")
    for name, box in regs.items():
        ok = isinstance(box, list) and len(box) == 4 and all(isinstance(v, (int, float)) and 0 <= v <= 1 for v in box) \
            and box[0] < box[2] and box[1] < box[3]
        if not ok:
            errs.append(f"구역 상자 이상: {name}={box}")
    casts = set()
    for f in spec["figures"]:
        for k in ("cast", "role", "pose", "prop", "facing", "region", "verse"):
            if k not in f:
                errs.append(f"figures[{f.get('cast')}] 필드 없음: {k}")
        if not isinstance(f.get("prop"), str) or not f["prop"].strip() or "·" in f["prop"] or " and " in f["prop"]:
            errs.append(f"figures[{f.get('cast')}] 지물은 하나의 문자열: {f.get('prop')!r}")
        if f.get("cast") and not os.path.exists(os.path.join(CAST, f"{f['cast']}.json")):
            errs.append(f"cast 정본 없음: cast/{f['cast']}.json")
        if f.get("region") not in regs:
            errs.append(f"figures[{f.get('cast')}] 구역 없음: {f.get('region')}")
        if f.get("facing") not in ("left", "right"):
            errs.append(f"figures[{f.get('cast')}] facing은 left|right: {f.get('facing')!r}")
        casts.add(f.get("cast"))
    for c in spec.get("crowds", []):
        if c.get("region") not in regs:
            errs.append(f"crowds 구역 없음: {c.get('region')}")
    ids = set()
    by_id = {st.get('id'): st for st in spec['stages']}
    for s in spec["stages"]:
        for k in ("id", "kind", "region", "verse", "prompt", "neg"):
            if k not in s:
                errs.append(f"stages[{s.get('id')}] 필드 없음: {k}")
        if s.get("kind") not in KINDS:
            errs.append(f"stages[{s.get('id')}] kind 이상: {s.get('kind')}")
        if s.get("region") not in regs:
            errs.append(f"stages[{s.get('id')}] 구역 없음: {s.get('region')}")
        if s.get("id") in ids:
            errs.append(f"stages id 중복: {s.get('id')}")
        ids.add(s.get("id"))
        # {costume:<id>}도 같은 규칙 — 옛 id(`{costume:david}`)가 나뉜 id(david-boy) 장면에 남는 것을 막음(task 390)
        for ph, cid in re.findall(r"\{(castc?|costume):([a-z0-9-]+)\}", s.get("prompt", "")):
            if not os.path.exists(os.path.join(CAST, f"{cid}.json")):
                errs.append(f"stages[{s.get('id')}] {{{ph}:{cid}}} 정본 없음")
            if cid not in casts:
                errs.append(f"stages[{s.get('id')}] {{{ph}:{cid}}}가 figures에 없음")
        if "from" in s and s["from"] not in ids:
            errs.append(f"stages[{s.get('id')}] from이 앞 단계가 아님: {s['from']}")
    # groups — 장면 안 경로에서 **한 번에 그릴** 인물 단계 묶음(task 337). 없으면 검사 없음.
    # 판 경로는 이 키를 읽지 않으므로 봉인된 장면은 영향이 없다.
    seen = set()
    for g in spec.get("groups", []):
        for k in ("stages", "prompt", "neg"):
            if k not in g:
                errs.append(f"groups 필드 없음: {k}")
        gs = g.get("stages") or []
        if len(gs) < 2:
            errs.append(f"groups.stages는 둘 이상이어야 한다(한 번에 그릴 이유가 없다): {gs}")
        for i in gs:
            if i not in ids:
                errs.append(f"groups.stages에 없는 단계: {i}")
            elif by_id[i].get("kind") != "plate":
                errs.append(f"groups.stages는 인물(plate) 단계만: {i}={by_id[i].get('kind')}")
            if i in seen:
                errs.append(f"groups.stages 단계 중복: {i}")
            seen.add(i)
        for cid in re.findall(r"\{castc?:([a-z0-9-]+)\}", g.get("prompt", "")):
            if cid not in casts:
                errs.append(f"groups[{gs[:1]}] {{castc:{cid}}}가 figures에 없음")
    j = spec["judge"]
    for k in ("figures", "gap_bands", "crest_x"):
        if k not in j:
            errs.append(f"judge 필드 없음: {k}")
    for c in j.get("figures", []):
        if c not in casts:
            errs.append(f"judge.figures에 figures 밖 인물: {c}")
        if c not in regs:
            errs.append(f"judge.figures 인물의 구역 없음: {c}")
    if "crest_x" in j and not (isinstance(j["crest_x"], dict) and "left" in j["crest_x"] and "right" in j["crest_x"]):
        errs.append("judge.crest_x는 {left:[x0,x1], right:[x0,x1]}")
    return errs


def _path(spec, path):
    """'figures[1].gesture' · 'stages[S3].prompt' → 값(없으면 KeyError). 대괄호 숫자 = 목록 자리, 그 밖 = id가 같은 항목."""
    v = spec
    for name, idx in re.findall(r"([A-Za-z_]+)(?:\[([^\]]+)\])?", path):
        v = v[name]
        if idx:
            v = v[int(idx)] if idx.isdigit() else next(x for x in v if x.get("id") == idx)
    return v


def _strings(v):
    return [v] if isinstance(v, str) else [s for x in (v.values() if isinstance(v, dict) else v if isinstance(v, list) else []) for s in _strings(x)]


def verse_element_errors(spec, prompt, verses=None):
    """구절 시각 요소 검사(task 375) → 오류 목록. prompt = 그 장면의 파생 프롬프트(whole_prompt 또는 plate_whole_prompt).
    verses(verses.json)를 주면 quote가 실제 본문(textKo, 띄어쓰기 무시)에도 있는지 본다."""
    errs, quotes = [], spec["verses"].get("quotes", {})
    m = re.match(r"(삼상|삼하|왕상|왕하|대상|대하|시)\s*\d+:", spec["verses"].get("range", ""))
    squash = lambda s: re.sub(r"\s+", "", s)
    for i, e in enumerate(spec.get("verse_elements") or []):
        at = f"verse_elements[{i}] {e.get('ko', '')!r}"
        if e.get("quote", "") == "" or e["quote"] not in quotes.get(e.get("verse"), ""):
            errs.append(f"{at}: quote가 verses.quotes[{e.get('verse')!r}] 안에 없음")
        elif verses is not None and m:
            text = "".join(verses.get(v, {}).get("textKo", "") for v in verse_ids(BOOK[m.group(1)], e["verse"]))
            if squash(e["quote"]) not in squash(text):
                errs.append(f"{at}: quote가 본문({e['verse']} 개역한글)에 없음")
        if e.get("kind") not in params.VERSE_ELEMENT_KINDS:
            errs.append(f"{at}: kind는 {'·'.join(params.VERSE_ELEMENT_KINDS)} 중 하나: {e.get('kind')!r}")
        carried, out = "field" in e or "en" in e, "out" in e
        if carried == out:
            errs.append(f"{at}: 실음(field+en)과 제외(out) 중 하나만")
            continue
        if out:
            bad = [w for w in params.VERSE_ELEMENT_BANNED if w in e["out"]]
            if not e["out"].strip() or bad:
                errs.append(f"{at}: 제외는 순간 밖만 — 사유 금지 낱말 {bad}")
            continue
        try:
            val = _path(spec, e.get("field", ""))
        except (KeyError, IndexError, StopIteration, TypeError, ValueError):
            errs.append(f"{at}: field 경로 없음: {e.get('field')!r}")
            continue
        en = (e.get("en") or "").strip()
        if not en or not any(en.lower() in s.lower() for s in _strings(val)):
            errs.append(f"{at}: en이 {e['field']} 칸 안에 없음: {en!r}")
        elif en.lower() not in prompt.lower():
            errs.append(f"{at}: en이 파생 프롬프트에 없음: {en!r}")
    return errs


def place_on_figure_errors(spec):
    """행동의 자리(task 399, 규칙 spec.action-place-on-figure) → 오류 목록, 요소 목록이 없으면 None(잴 수 없음).
    `자리` 요소(예: 18:11 「다윗을 벽에 박으리라」 — 다윗이 벽 앞에 있어야 함)는 배경이 아니라 인물 칸(figures[i].*)이 날라야 한다."""
    els = spec.get("verse_elements")
    if not els:
        return None
    return [f"verse_elements[{i}] {e.get('ko', '')!r}: 자리는 인물 칸(figures[i].*)에 — 지금 {e.get('field')!r}"
            for i, e in enumerate(els) if e.get("kind") == "자리" and "out" not in e and not str(e.get("field", "")).startswith("figures[")]


WORDS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "scripture_words", "words.json")


def lexicon_look_errors(spec, prompt):
    """지물 모양은 낱말 사전에서(task 400, 규칙 spec.lexicon-link) → 오류 목록, 요소 목록이 없으면 None.
    실은 지물 요소의 quote에 사전 표제어·꼴이 있으면 파생 프롬프트에 그 항목의 look L1|L2|L3 en 하나가 실려야 한다
    (397·400 a1: 「a small wooden lyre」만으로 16장 중 15장이 류트 — 단계는 장면 증거로 고르고, 사전 문구를 쓰는 것은 규칙)."""
    els = spec.get("verse_elements")
    if not els:
        return None
    with open(WORDS, encoding="utf-8") as fh:
        words = [w for w in json.load(fh)["words"] if w.get("drawable", True)]
    squash, low, errs = lambda t: re.sub(r"\s+", "", t), prompt.lower(), []
    for i, e in enumerate(els):
        if e.get("kind") != "지물" or "out" in e:
            continue
        for w in words:
            if any(squash(f) in squash(e["quote"]) for f in [w["word"], *w["forms"]]) and \
                    not any(w["look"][k]["en"].lower().rstrip(".") in low for k in ("L1", "L2", "L3")):
                errs.append(f"verse_elements[{i}] {e['quote']!r}: 사전 {w['id']} look 문구가 파생 프롬프트에 없음")
    return errs


PROP_TAIL = ("of", "in", "on", "with", "at", "for", "from", "to", "under", "over", "across", "held", "slung", "hanging")
PROP_PART = ("corner", "fold", "edge", "hem", "end", "tip")   # 「robe corner」 — 부분 낱말이면 앞 명사(옷)가 핵심


def prop_in_prompt_errors(spec, prompt):
    """지물이 파생 프롬프트에 실렸나(task 396) → 오류 목록. prompt = route_prompt.
    한 장 모드 파생은 prop 칸을 잇지 않아 지물은 다른 칸 문구에 있어야 그려진다(394 회고).
    핵심 낱말 = 영문 명사구의 머리 명사(전치사·분사 앞 마지막 낱말, 복수 s 허용). 영문이 없으면 실패."""
    errs, low = [], prompt.lower()
    for f in spec["figures"]:
        p = f.get("prop")
        if not p or p == "none":
            continue
        en = p.get("en", "") if isinstance(p, dict) else p
        words = re.findall(r"[a-z]+", en.lower())
        if not words:
            errs.append(f"{f['cast']} prop {en!r}: 영문 없음")
            continue
        cut = next((i for i, w in enumerate(words) if i and w in PROP_TAIL), len(words))
        head = words[cut - 2] if cut >= 2 and words[cut - 1] in PROP_PART else words[cut - 1]
        if not re.search(rf"\b{head}(e?s)?\b", low):
            errs.append(f"{f['cast']} prop {en!r}: 「{head}」가 프롬프트에 없음")
    return errs


def zimage_tokens():
    """→ 프롬프트 → 채팅 틀 포함 토큰 수. ZImagePipeline.encode_prompt와 같은 틀(enable_thinking=True)."""
    from huggingface_hub import snapshot_download
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(os.path.join(snapshot_download("Tongyi-MAI/Z-Image-Turbo", local_files_only=True), "tokenizer"))
    return lambda p: len(tok(tok.apply_chat_template([{"role": "user", "content": p}], tokenize=False,
                                                     add_generation_prompt=True, enable_thinking=True)).input_ids)


def whole_prompt_overflow(ids=None):
    """→ {장면: 오류} — 한 장 모드 장면(whole_background 있음)의 토큰 상한 검사. 토크나이저를 못 불러오면 예외."""
    import derive_scene as ds
    n = zimage_tokens()
    ids = ids or sorted(os.path.basename(f)[:-5] for f in glob.glob(os.path.join(SCENES, "*.json")))
    bad = {}
    for sid in ids:
        spec = ds.load(sid)
        if "whole_background" not in spec:
            continue
        k = n(ds.whole_prompt(spec))
        if k > WHOLE_MAX and sid not in WHOLE_OVER_OK:
            bad[sid] = f"한 장 프롬프트 {k}토큰 > {WHOLE_MAX} — 뒤쪽이 잘려 무처치"
        elif k <= WHOLE_MAX and sid in WHOLE_OVER_OK:
            bad[sid] = f"한 장 프롬프트 {k}토큰 ≤ {WHOLE_MAX} — WHOLE_OVER_OK 예외 지울 것"
    return bad


def element_check(sid, n, verses=None):
    """→ (오류 목록, 목록 있음) — 구절 시각 요소 + 판 경로 장면도 파생 프롬프트 512토큰 안(task 375)."""
    import derive_scene as ds
    spec = ds.load(sid)
    if "verse_elements" not in spec:
        return [], False
    prompt = ds.whole_prompt(spec) if "whole_background" in spec else ds.plate_whole_prompt(spec)
    errs = verse_element_errors(spec, prompt, verses)
    if "whole_background" not in spec and n(prompt) > WHOLE_MAX:
        errs.append(f"판 경로 한 장 프롬프트 {n(prompt)}토큰 > {WHOLE_MAX} — 뒤쪽이 잘려 구절 요소가 빠진다")
    return errs, True


def main():
    with open(VERSES, encoding="utf-8") as fh:
        verses = json.load(fh)
    ids = sys.argv[1:] or sorted(os.path.basename(f)[:-5] for f in glob.glob(os.path.join(SCENES, "*.json")))
    try:
        over = whole_prompt_overflow(ids)
        n = zimage_tokens()
    except Exception as e:  # 토크나이저 없음(시스템 python3·캐시 없음) — 검사를 건너뛰지 않고 실패로
        print(f"✗ 토큰 검사 불가 — venv314로 실행할 것: {type(e).__name__}: {e}")
        return 1
    bad, done, missing = 0, 0, []
    for sid in ids:
        with open(os.path.join(SCENES, f"{sid}.json"), encoding="utf-8") as fh:
            spec = json.load(fh)
        el_errs, has = element_check(sid, n, verses)
        errs = check(spec, verses) + ([over[sid]] if sid in over else []) + el_errs
        print(f"{'✅' if not errs else '✗'} {sid}" + ("" if not errs else "\n    - " + "\n    - ".join(errs)))
        bad += bool(errs)
        if sid in params.VERSE_ELEMENT_SCENES:
            done += has and not errs
            if not has:
                missing.append(sid)
    print(f"{len(ids) - bad}/{len(ids)} 통과")
    targets = [s for s in params.VERSE_ELEMENT_SCENES if s in ids]
    if missing:
        print(f"⚠ 구절 요소 미작성: {', '.join(missing)}")
    print(f"구절 요소: {done}/{len(targets)} 장면")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
