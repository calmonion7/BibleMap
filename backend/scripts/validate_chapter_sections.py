"""장 묶음 정본(data/chapter_sections/books.json)을 기계 검증한다 (task#212 S2).

검증 항목(권별 불변식):
  a) 커버리지 — 다장권(장≥2) 61권 전수 존재, 미지 bookId 없음
  b) 분할 — 각 권 묶음이 연속·전수·비중첩: 첫 start=1, 끝 end=chapterCount(정본 절 사전 도출),
     각 start=직전 end+1, start≤end, 범위 in [1,chapterCount]
  c) 제목 — 비어있지 않은 한 줄, 1~24자

단장권(장=1) 5권은 묶음을 두지 않는다(부재 정상; 존재 시에도 1..1 분할이면 통과).
위반이 있으면 목록을 출력하고 종료 코드 1.
"""
import json
import os
import sys

_DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")


def main():
    verses = json.load(open(os.path.join(_DATA, "bible", "verses.json"), encoding="utf-8"))
    books_ko = json.load(open(os.path.join(_DATA, "names_ko", "books.json"), encoding="utf-8"))
    sections = json.load(open(os.path.join(_DATA, "chapter_sections", "books.json"), encoding="utf-8"))

    # 정본에서 권별 장 수 도출 (BB → max CCC)
    chapter_count = {}
    for k in verses:
        bb, ccc = int(k[:2]), int(k[2:5])
        chapter_count[bb] = max(chapter_count.get(bb, 0), ccc)
    bb_of = {tid: i for i, tid in enumerate(books_ko, 1)}

    violations = []
    multi = [tid for tid in books_ko if chapter_count[bb_of[tid]] >= 2]
    missing = [tid for tid in multi if tid not in sections]
    if missing:
        violations.append(f"[커버리지] 다장권 누락 {len(missing)}: {[books_ko[t]['ko'] for t in missing]}")
    for tid in sections:
        if tid not in bb_of:
            violations.append(f"[커버리지] 미지의 bookId: {tid}")

    total_sections = 0
    for tid, secs in sections.items():
        if tid not in bb_of:
            continue
        ko = books_ko[tid]["ko"]
        n = chapter_count[bb_of[tid]]
        if not secs:
            violations.append(f"[분할] {ko}: 묶음이 비어있음")
            continue
        prev_end = 0
        for i, s in enumerate(secs):
            total_sections += 1
            t, a, b = s.get("title"), s.get("startChapter"), s.get("endChapter")
            if not t or not isinstance(t, str) or not (1 <= len(t) <= 24):
                violations.append(f"[제목] {ko} {a}-{b}장: 길이 위반 ({len(t or '')}자)")
            if not isinstance(a, int) or not isinstance(b, int):
                violations.append(f"[분할] {ko}: 비정수 범위 {a}-{b}")
                continue
            if a > b:
                violations.append(f"[분할] {ko}: 역전 범위 {a}-{b}")
            if a < 1 or b > n:
                violations.append(f"[분할] {ko}: 범위 이탈 {a}-{b} (전 {n}장)")
            if i == 0:
                if a != 1:
                    violations.append(f"[분할] {ko}: 첫 묶음 시작 {a}≠1")
            elif a != prev_end + 1:
                violations.append(f"[분할] {ko}: {i}번째 경계 불연속 {prev_end}→{a}")
            prev_end = b
        if prev_end != n:
            violations.append(f"[분할] {ko}: 끝 묶음 종료 {prev_end}≠{n}")

    print(f"검사: {len(sections)}권 {total_sections}묶음 (다장권 {len(multi)})")
    if violations:
        print(f"FAIL — 위반 {len(violations)}건")
        for v in violations[:40]:
            print(" -", v)
        sys.exit(1)
    print("PASS — 탈락 0")


if __name__ == "__main__":
    main()
