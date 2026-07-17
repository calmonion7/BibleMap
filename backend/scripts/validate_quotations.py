"""인용 관계 정본(data/quotations/quotations.json)을 기계 검증한다 (task#209 S2).

검증 항목:
  a) verseID 전수 실존 — 정본 절 사전(data/bible/verses.json) 대조
  b) 측 위반 — NT측 verseID는 신약 권(BB≥40), OT측은 구약 권(BB≤39)
  c) rangeLabel 자기일치 — 라벨을 파싱한 결과가 verseIds 배열과 정확히 일치
  d) 중복 쌍 0 — (ntVerseIds, otVerseIds) 조합 유일

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
    data = json.load(open(os.path.join(_DATA, "quotations", "quotations.json"), encoding="utf-8"))
    entries = data.get("quotations", [])

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
    seen = set()
    for i, e in enumerate(entries):
        nt, ot = e.get("ntVerseIds", []), e.get("otVerseIds", [])
        tag = f"[{i}] {e.get('ntRangeLabel')} ← {e.get('otRangeLabel')}"
        for vid in nt + ot:
            if vid not in verses:
                violations.append(f"{tag}: verseID 미실존 {vid}")
        if nt and int(nt[0][:2]) < 40:
            violations.append(f"{tag}: NT측이 구약 권")
        if ot and int(ot[0][:2]) > 39:
            violations.append(f"{tag}: OT측이 신약 권")
        if label_ids(e.get("ntRangeLabel")) != nt:
            violations.append(f"{tag}: ntRangeLabel 불일치")
        if label_ids(e.get("otRangeLabel")) != ot:
            violations.append(f"{tag}: otRangeLabel 불일치")
        key = (tuple(nt), tuple(ot))
        if key in seen:
            violations.append(f"{tag}: 중복 쌍")
        seen.add(key)

    print(f"검사: {len(entries)}쌍")
    if violations:
        print(f"FAIL — 위반 {len(violations)}건")
        for v in violations[:40]:
            print(" -", v)
        sys.exit(1)
    print("PASS — 탈락 0")


if __name__ == "__main__":
    main()
