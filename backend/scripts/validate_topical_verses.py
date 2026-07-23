"""주제별 큐레이션 성구 정본(data/topical_verses/topics.json)을 기계 검증한다 (task#250 S1).

검증 항목:
  a) 주제 수 10~14건
  b) 주제당 verseIds 최소 3개
  c) verseId 전수 실존 — 정본 절 사전(data/bible/verses.json) 대조
  d) id 유일

위반이 있으면 목록을 출력하고 종료 코드 1.
"""
import json
import os
import sys

_DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")


def main():
    verses = json.load(open(os.path.join(_DATA, "bible", "verses.json"), encoding="utf-8"))
    topics = json.load(open(os.path.join(_DATA, "topical_verses", "topics.json"), encoding="utf-8"))["topics"]

    violations = []
    seen_ids = set()
    for t in topics:
        tag = t.get("id")
        verse_ids = t.get("verseIds", [])
        if len(verse_ids) < 3:
            violations.append(f"{tag}: verseIds {len(verse_ids)}개 — 최소 3개 미달")
        for vid in verse_ids:
            if vid not in verses:
                violations.append(f"{tag}: verseId 미실존 {vid}")
        if tag in seen_ids:
            violations.append(f"{tag}: id 중복")
        seen_ids.add(tag)

    if not (10 <= len(topics) <= 14):
        violations.append(f"주제 수 {len(topics)}건 — 10~14 범위 밖")

    print(f"검사: {len(topics)}건 주제, verseId {sum(len(t.get('verseIds', [])) for t in topics)}개")
    if violations:
        print(f"FAIL — 위반 {len(violations)}건")
        for v in violations[:40]:
            print(" -", v)
        sys.exit(1)
    print("PASS — 탈락 0")


if __name__ == "__main__":
    main()
