"""메시아 예언↔성취 정본(data/messianic_prophecies/prophecies.json)을 기계 검증한다 (task#246 S1).

검증 항목:
  a) verseID 전수 실존 — 정본 절 사전(data/bible/verses.json) 대조
  b) rangeLabel 자기일치 — 라벨을 파싱한 결과가 verseIds 배열과 정확히 일치
  c) 각 쌍에 ot·nt 최소 1개, theme 존재
  d) id 유일
  e) 쌍 수 20~30 (목표 ~25)

위반이 있으면 목록을 출력하고 종료 코드 1.
"""
import json
import os
import re
import sys

_DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")
_REF = re.compile(r"^([가-힣]+)\s*(\d+):(\d+)(?:-(\d+))?$")


def main():
    verses = json.load(open(os.path.join(_DATA, "bible", "verses.json"), encoding="utf-8"))
    books = json.load(open(os.path.join(_DATA, "names_ko", "books.json"), encoding="utf-8"))
    data = json.load(open(os.path.join(_DATA, "messianic_prophecies", "prophecies.json"), encoding="utf-8"))
    entries = data.get("prophecies", [])

    alias_bb = {}
    for i, (tid, v) in enumerate(books.items(), 1):
        for a in v.get("alias", []):
            alias_bb[a] = i
        alias_bb[v["ko"]] = i

    def label_ids(label):
        m = _REF.match(label or "")
        if not m:
            return None
        bb = alias_bb.get(m.group(1))
        if not bb:
            return None
        ch, v1 = int(m.group(2)), int(m.group(3))
        v2 = int(m.group(4)) if m.group(4) else v1
        return [f"{bb:02d}{ch:03d}{v:03d}" for v in range(v1, v2 + 1)]

    violations = []
    seen_ids = set()
    for i, e in enumerate(entries):
        ot, nt = e.get("otVerseIds", []), e.get("ntVerseIds", [])
        tag = f"[{i}] {e.get('id')}: {e.get('otRangeLabel')} → {e.get('ntRangeLabel')}"
        for vid in ot + nt:
            if vid not in verses:
                violations.append(f"{tag}: verseID 미실존 {vid}")
        if not ot:
            violations.append(f"{tag}: otVerseIds 비어있음")
        if not nt:
            violations.append(f"{tag}: ntVerseIds 비어있음")
        if not e.get("theme"):
            violations.append(f"{tag}: theme 없음")
        if label_ids(e.get("otRangeLabel")) != ot:
            violations.append(f"{tag}: otRangeLabel 불일치")
        if label_ids(e.get("ntRangeLabel")) != nt:
            violations.append(f"{tag}: ntRangeLabel 불일치")
        eid = e.get("id")
        if eid in seen_ids:
            violations.append(f"{tag}: id 중복")
        seen_ids.add(eid)

    if not (20 <= len(entries) <= 30):
        violations.append(f"쌍 수 {len(entries)}건 — 20~30 범위 밖")

    print(f"검사: {len(entries)}쌍")
    if violations:
        print(f"FAIL — 위반 {len(violations)}건")
        for v in violations[:40]:
            print(" -", v)
        sys.exit(1)
    print("PASS — 탈락 0")


if __name__ == "__main__":
    main()
