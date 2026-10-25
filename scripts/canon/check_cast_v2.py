#!/usr/bin/env python3
"""인물 정의 cast-vocab-2 기계 검사 (task 352). GPU 0.

  check_cast_v2.py      # cast/*.json 전부. 하나라도 낙제면 종료코드 1.

검사 항목(352 DoD 1): (a) `_format`이 cast-vocab-2 · card/face 층 필드 전부 · class 허용값
(a2) ageBand·beardVolume·silhouette의 text가 정도 낱말만으로 끝나지 않음 (b) 외모 필드 전부 `_why`
(c) `_why`의 구절 표기가 verses.json 절로 풀림 (c2) 구절 바로 뒤 「인용」이 그 절 원문에 글자 그대로 있음(「…」 생략 허용) (d) 역표 정차지마다 함께 나오는 인물 쌍이 카드 층 2필드 이상 다름
(e) 모든 인물이 `cast/APPEARANCE-VERSES.md` 표에 줄을 가짐. 필드 표 정본은 `cast/CAST.md` 「cast-vocab-2 필드 표」.
task 353에서 더함: (f) `_why`가 근거 단계 `[직접]`·`[추론]`·`[저작](이유 4자 이상)`로 시작 · `role` 필드와 근거
(g) 얼굴·카드 층에 성품 낱말 없음(삼상 16:7 — 표정은 장면 `expression` 몫) (h) 생애 단계 쌍을 뺀 **모든** 쌍이 카드 층 2필드 이상 다름
(i) 파생 문구(장면 `cast_describe`·정본 `gen_face_canon.look`)에 `bare head` 없음 — Z-Image가 민머리로 그린다(346·353 두 번 밟음, notes/PROMPTING.md 14).
task 429에서 더함: (j) ageBand 나이 글의 숫자가 class 범위 안(규칙 spec.cast-age-band).
"""
import glob
import itertools
import json
import os
import re
import sys

import params

CAST = os.path.join(params.CANON_DIR, "cast")
VERSES = os.path.join(params.REPO_ROOT, "data", "bible", "verses.json")
BOOK = {"창": 1, "출": 2, "레": 3, "민": 4, "신": 5, "수": 6, "삿": 7, "룻": 8, "삼상": 9, "삼하": 10,
        "왕상": 11, "왕하": 12, "대상": 13, "대하": 14, "느": 16, "시": 19, "잠": 20, "전": 21, "아": 22,
        "마": 40, "막": 41, "눅": 42, "행": 44}
CARD = {
    "heightRel": {"child", "short", "average", "tall", "towering"},
    "ageBand": {"child", "youth", "young", "prime", "middle", "elder"},
    "beardVolume": {"none", "stubble", "trimmed", "full", "long"},
    "silhouette": {"slight", "lean", "average", "broad", "heavy", "giant"},
    "headOutline": {"bare", "headwrap", "turban", "veil", "shawl", "diadem", "helmet"},
    "costumeColor": {"red", "brown", "white", "blue", "green", "purple", "black", "gold", "undyed"},
}
FACE = ("faceShape", "eyes", "nose", "mouth", "skin", "brows", "marks")
V1 = ("age", "hair", "beard", "headwear", "build", "costume")
SHAPED = ("ageBand", "beardVolume", "silhouette")
DEGREE = {"short", "tall", "long", "big", "small", "large", "little", "old", "young", "thick", "thin", "very",
          "quite", "average", "normal", "medium", "some", "slightly", "rather", "fairly"}
STOP = {"a", "an", "the", "of", "with", "and", "to", "in", "at", "on", "his", "her", "its", "by", "for", "over",
        "under", "from", "is"}
TIERS = ("[직접]", "[추론]", "[저작]")
# 성품·인상 낱말 — 고정 정의에 두지 않는다(CAST.md 「근거 단계」). task 353 DoD 4 목록과 같다.
TRAIT = re.compile(r"\b(cold|cruel|hard|harsh|wicked|evil|sly|cunning|menacing|sinister|kind|gentle|wise|noble|arrogant|proud"
                   r"|haughty|shifty|pleading|trembling|tense|anxious|fierce|stern|serene|innocent|calm|steady|composed)\b")
# 같은 사람의 생애 단계 — 일부러 닮게 하므로 (h)에서 뺀다.
STAGES = {frozenset(p) for fam in [("david-boy", "david-youth", "david", "david-prime", "david-elder", "david-old"),
                                   ("saul", "saul-old"), ("solomon", "solomon-prime", "solomon-old")]
          for p in itertools.combinations(fam, 2)}
# ageBand class 나이 범위(CAST.md 사다리 — youth 10대 · young 20대 · prime 30대 · middle 40~50대 · elder 60대~, task 429)
AGE_RANGE = {"child": (0, 9), "youth": (10, 19), "young": (20, 29), "prime": (30, 39), "middle": (40, 59), "elder": (60, 120)}
AGE_TEXT = re.compile(r"\b(?:about|around) (\d+)\b|\b(early |mid-|late )?(\d)0s\b")
REF = re.compile(r"(" + "|".join(sorted(BOOK, key=len, reverse=True)) + r")\s*(\d+):(\d+)(?:\s*[-–~]\s*(\d+))?")
QUOTE = re.compile(REF.pattern + r"\s*(?:\([^)]*\)\s*)?「([^」]+)」")


def stop_cast():
    """CAST.md 역표 → {stop-id: [cast id]}. 「samuel(영으로 등장)」은 괄호를 떼고 셈."""
    out = {}
    with open(os.path.join(CAST, "CAST.md"), encoding="utf-8") as fh:
        for line in fh:
            m = re.match(r"\|\s*(authored-[\w-]+)\s*\|([^|]*)\|", line)
            if m:
                out[m.group(1)] = [re.sub(r"\(.*?\)", "", x).strip() for x in m.group(2).split(",") if x.strip()]
    return out


def card_age(text):
    """나이 글 → (낮은, 높은) 나이. 「about 14」「around 60」 → 한 점 · 「in his 40s」 → 40~49 · early/mid-/late → 40~43·43~46·46~49.
    숫자를 못 읽으면 None."""
    m = AGE_TEXT.search(text or "")
    if not m:
        return None
    if m.group(1):
        return int(m.group(1)), int(m.group(1))
    d = int(m.group(3)) * 10
    lo, hi = {"early ": (0, 3), "mid-": (3, 6), "late ": (6, 9)}.get(m.group(2), (0, 9))
    return d + lo, d + hi


def age_band_errors(band):
    """규칙 spec.cast-age-band(task 429) — 나이 글의 나이가 class 범위 안인지. → [] 통과 · [오류] 걸림 · None 못 잼(숫자 없음).
    david-prime 「in his 40s」가 class prime(30대)으로 남아 판 경로 문구와 카드가 갈렸다(task 426 scripture-reviewer)."""
    age = card_age((band or {}).get("text", ""))
    if age is None:
        return None
    lo, hi = AGE_RANGE.get((band or {}).get("class"), (None, None))
    if lo is None or not (lo <= age[0] and age[1] <= hi):
        return [f"ageBand 나이 {age[0]}~{age[1]}세가 class {band.get('class')!r} 범위 {lo}~{hi} 밖: {band.get('text')!r}"]
    return []


def check(c, verses):
    errs = []
    if "cast-vocab-2" not in c.get("_format", ""):
        errs.append(f"(a) _format: {c.get('_format', '')[:30]!r}")
    card, face, why = c.get("card", {}), c.get("face", {}), c.get("_why", {})
    for k, allowed in CARD.items():
        v = card.get(k)
        cls = v if k == "heightRel" else (v or {}).get("class")
        if cls not in allowed:
            errs.append(f"(a) card.{k} class {cls!r} ∉ {sorted(allowed)}")
        if k != "heightRel" and not (v or {}).get("text"):
            errs.append(f"(a) card.{k}.text 비어 있음")
    for k in FACE:
        if not face.get(k):
            errs.append(f"(a) face.{k} 비어 있음")
    for k in SHAPED:
        v = card.get(k) or {}
        text = v.get("text", "")
        if k == "beardVolume" and v.get("class") == "none" and text == "없음":
            continue
        words = [w for w in re.findall(r"[a-z']+", text.lower()) if w not in DEGREE and w not in STOP]
        if len(words) < 2:
            errs.append(f"(a2) card.{k}.text 정도 낱말뿐: {text!r}")
    age = age_band_errors(card.get("ageBand"))
    errs += ["(j) 나이 글에 숫자 없음(「about N」·「in his Ns」)"] if age is None else [f"(j) {e}" for e in age]
    if not c.get("role"):
        errs.append("(f) role 비어 있음")
    keys = list(V1) + [f"card.{k}" for k in CARD] + [f"face.{k}" for k in FACE] + ["role"]
    for k in keys:
        w = why.get(k, "")
        if not w:
            errs.append(f"(b) _why[{k}] 없음")
        elif not w.startswith(TIERS):
            errs.append(f"(f) _why[{k}] 근거 단계 표시 없음: {w[:40]!r}")
        elif w.startswith("[저작]"):
            m = re.match(r"\[저작\]\(([^)]*)\)", w)
            r = (m.group(1) if m else "").replace(" ", "")
            if len(r) < 4 or r in ("본문밖", "저작자정함", "본문밖·저작자정함"):
                errs.append(f"(f) _why[{k}] [저작] 이유 없음: {w[:40]!r}")
        elif not REF.search(w):
            errs.append(f"(b) _why[{k}] [직접]·[추론]인데 구절 없음: {w[:40]!r}")
    for k, v in list(face.items()) + [(k, v.get("text", "")) for k, v in card.items() if isinstance(v, dict)]:
        m = TRAIT.search(v.lower())
        if m:
            errs.append(f"(g) {k} 성품 낱말 「{m.group(1)}」: {v!r}")
    for k, w in why.items():
        for m in REF.finditer(w):
            ch, a, b = int(m.group(2)), int(m.group(3)), int(m.group(4) or m.group(3))
            miss = [v for v in range(a, b + 1) if f"{BOOK[m.group(1)]:02d}{ch:03d}{v:03d}" not in verses]
            if miss:
                errs.append(f"(c) _why[{k}] {m.group(0)} — 없는 절 {miss}")
        for m in QUOTE.finditer(w):  # 352 회고: 기억으로 쓴 인용이 원문과 갈림(도엑 21:7)
            ch, a, b = int(m.group(2)), int(m.group(3)), int(m.group(4) or m.group(3))
            src = re.sub(r"\s+", "", "".join(verses.get(f"{BOOK[m.group(1)]:02d}{ch:03d}{v:03d}", {}).get("textKo", "")
                                              for v in range(a, b + 1)))
            for frag in re.split(r"…|\.\.\.", m.group(5)):
                if re.sub(r"\s+", "", frag) not in src:
                    errs.append(f"(c2) _why[{k}] {m.group(1)} {ch}:{a} 인용이 원문에 없음: 「{frag.strip()[:30]}」")
    return errs


def card_classes(c):
    card = c.get("card", {})
    return {k: card.get(k) if k == "heightRel" else (card.get(k) or {}).get("class") for k in CARD}


def main():
    with open(VERSES, encoding="utf-8") as fh:
        verses = json.load(fh)
    cast = {}
    for f in sorted(glob.glob(os.path.join(CAST, "*.json"))):
        with open(f, encoding="utf-8") as fh:
            c = json.load(fh)
        cast[c["id"]] = c
    bad = 0
    for cid, c in cast.items():
        errs = check(c, verses)
        print(f"{'✅' if not errs else '✗'} {cid}" + ("" if not errs else "\n    - " + "\n    - ".join(errs)))
        bad += bool(errs)
    pair_errs = []
    for stop, ids in stop_cast().items():
        for x, y in itertools.combinations(ids, 2):
            if x not in cast or y not in cast:
                pair_errs.append(f"{stop}: 역표 인물 {x if x not in cast else y} 파일 없음")
                continue
            a, b = card_classes(cast[x]), card_classes(cast[y])
            diff = [k for k in CARD if a[k] != b[k]]
            if len(diff) < 2:
                pair_errs.append(f"{stop}: {x}·{y} 카드 층 차이 {len(diff)}개 {diff}")
    print(("✅" if not pair_errs else "✗") + " (d) 함께 나오는 쌍 카드 층 2필드 이상 다름"
          + "".join(f"\n    - {e}" for e in pair_errs))
    all_errs = []
    for x, y in itertools.combinations(sorted(cast), 2):
        if frozenset((x, y)) in STAGES:
            continue
        a, b = card_classes(cast[x]), card_classes(cast[y])
        if sum(a[k] != b[k] for k in CARD) < 2:
            all_errs.append(f"{x}·{y} 카드 층 차이 {sum(a[k] != b[k] for k in CARD)}개")
    print(("✅" if not all_errs else "✗") + " (h) 모든 쌍(생애 단계 쌍 제외) 카드 층 2필드 이상 다름"
          + "".join(f"\n    - {e}" for e in all_errs))
    import derive_scene as ds
    import gen_face_canon as gfc
    bald = [cid for cid, c in cast.items() if "bare head" in (ds.cast_describe(c) + gfc.look(cid)).lower()]
    print(("✅" if not bald else "✗") + " (i) 파생 문구에 `bare head` 없음(대머리 함정)" + (f" — {bald}" if bald else ""))
    av = os.path.join(CAST, "APPEARANCE-VERSES.md")
    rows = set()
    if os.path.exists(av):
        with open(av, encoding="utf-8") as fh:
            rows = {m.group(1) for m in (re.match(r"\|\s*([\w-]+)\s*\|", ln) for ln in fh) if m}
    missing = sorted(set(cast) - rows)
    print(("✅" if not missing else "✗") + f" (e) APPEARANCE-VERSES.md 인물 줄" + (f" — 빠짐 {missing}" if missing else ""))
    print(f"{len(cast) - bad}/{len(cast)} 인물 통과")
    return 1 if bad or pair_errs or all_errs or bald or missing else 0


if __name__ == "__main__":
    sys.exit(main())
