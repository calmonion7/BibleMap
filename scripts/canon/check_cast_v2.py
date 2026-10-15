#!/usr/bin/env python3
"""인물 정의 cast-vocab-2 기계 검사 (task 352). GPU 0.

  check_cast_v2.py      # cast/*.json 전부. 하나라도 낙제면 종료코드 1.

검사 항목(352 DoD 1): (a) `_format`이 cast-vocab-2 · card/face 층 필드 전부 · class 허용값
(a2) ageBand·beardVolume·silhouette의 text가 정도 낱말만으로 끝나지 않음 (b) 외모 필드 전부 `_why`
(c) `_why`의 구절 표기가 verses.json 절로 풀림 (d) 역표 정차지마다 함께 나오는 인물 쌍이 카드 층 2필드 이상 다름
(e) 모든 인물이 `cast/APPEARANCE-VERSES.md` 표에 줄을 가짐. 필드 표 정본은 `cast/CAST.md` 「cast-vocab-2 필드 표」.
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
    "costumeColor": {"red", "brown", "white", "blue", "purple", "black", "gold", "undyed"},
}
FACE = ("faceShape", "eyes", "nose", "mouth", "skin", "brows", "marks")
V1 = ("age", "hair", "beard", "headwear", "build", "costume")
SHAPED = ("ageBand", "beardVolume", "silhouette")
DEGREE = {"short", "tall", "long", "big", "small", "large", "little", "old", "young", "thick", "thin", "very",
          "quite", "average", "normal", "medium", "some", "slightly", "rather", "fairly"}
STOP = {"a", "an", "the", "of", "with", "and", "to", "in", "at", "on", "his", "her", "its", "by", "for", "over",
        "under", "from", "is"}
REF = re.compile(r"(" + "|".join(sorted(BOOK, key=len, reverse=True)) + r")\s*(\d+):(\d+)(?:\s*[-–~]\s*(\d+))?")


def stop_cast():
    """CAST.md 역표 → {stop-id: [cast id]}. 「samuel(영으로 등장)」은 괄호를 떼고 셈."""
    out = {}
    with open(os.path.join(CAST, "CAST.md"), encoding="utf-8") as fh:
        for line in fh:
            m = re.match(r"\|\s*(authored-[\w-]+)\s*\|([^|]*)\|", line)
            if m:
                out[m.group(1)] = [re.sub(r"\(.*?\)", "", x).strip() for x in m.group(2).split(",") if x.strip()]
    return out


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
    keys = list(V1) + [f"card.{k}" for k in CARD] + [f"face.{k}" for k in FACE]
    for k in keys:
        w = why.get(k, "")
        if not w:
            errs.append(f"(b) _why[{k}] 없음")
        elif "본문 밖" not in w and not REF.search(w):
            errs.append(f"(b) _why[{k}] 구절도 「본문 밖」도 없음: {w[:40]!r}")
    for k, w in why.items():
        for m in REF.finditer(w):
            ch, a, b = int(m.group(2)), int(m.group(3)), int(m.group(4) or m.group(3))
            miss = [v for v in range(a, b + 1) if f"{BOOK[m.group(1)]:02d}{ch:03d}{v:03d}" not in verses]
            if miss:
                errs.append(f"(c) _why[{k}] {m.group(0)} — 없는 절 {miss}")
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
    av = os.path.join(CAST, "APPEARANCE-VERSES.md")
    rows = set()
    if os.path.exists(av):
        with open(av, encoding="utf-8") as fh:
            rows = {m.group(1) for m in (re.match(r"\|\s*([\w-]+)\s*\|", ln) for ln in fh) if m}
    missing = sorted(set(cast) - rows)
    print(("✅" if not missing else "✗") + f" (e) APPEARANCE-VERSES.md 인물 줄" + (f" — 빠짐 {missing}" if missing else ""))
    print(f"{len(cast) - bad}/{len(cast)} 인물 통과")
    return 1 if bad or pair_errs or missing else 0


if __name__ == "__main__":
    sys.exit(main())
