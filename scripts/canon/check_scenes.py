#!/usr/bin/env python3
"""장면 명세(`scenes/*.json`) 기계 검사 (task 332 S1). GPU 0.

  check_scenes.py [<scene-id> ...]      # 인자 없으면 scenes/ 전부. 하나라도 낙제면 종료코드 1.

검사 항목(3/7 DoD 2): 필수 필드 · 인용 절이 verses.json에 존재 · figures[].prop 1개 · figures[].cast가 cast/<id>.json에 존재 ·
구역 상자 [0,1] 안(x0<x1, y0<y1) · stages/figures/crowds/judge가 가리키는 구역이 regions에 있음 · judge.figures ⊆ figures.cast.
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
        for cid in re.findall(r"\{castc?:([a-z0-9-]+)\}", s.get("prompt", "")):
            if not os.path.exists(os.path.join(CAST, f"{cid}.json")):
                errs.append(f"stages[{s.get('id')}] {{cast:{cid}}} 정본 없음")
            if cid not in casts:
                errs.append(f"stages[{s.get('id')}] {{cast:{cid}}}가 figures에 없음")
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


def main():
    with open(VERSES, encoding="utf-8") as fh:
        verses = json.load(fh)
    ids = sys.argv[1:] or sorted(os.path.basename(f)[:-5] for f in glob.glob(os.path.join(SCENES, "*.json")))
    bad = 0
    for sid in ids:
        with open(os.path.join(SCENES, f"{sid}.json"), encoding="utf-8") as fh:
            spec = json.load(fh)
        errs = check(spec, verses)
        print(f"{'✅' if not errs else '✗'} {sid}" + ("" if not errs else "\n    - " + "\n    - ".join(errs)))
        bad += bool(errs)
    print(f"{len(ids) - bad}/{len(ids)} 통과")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
