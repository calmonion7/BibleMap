"""장 개요 정본(data/chapter_summaries/books.json)을 기계 검증한다 (task#206 S2).

검증 항목:
  a) 커버리지 — 66권 전수, 권별 장 수가 정본 절 사전(BBCCC 도출)과 정확히 일치, 장 번호 1..N 연속
  b) 요약 — 한글 한 줄, 1~60자
  c) 대표절 — keyVerseId(BBCCCVVV)가 정본 절 사전에 실존하고, 그 권·그 장 소속

위반이 있으면 목록을 출력하고 종료 코드 1.
"""
import json
import os
import sys

_DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")


def main():
    verses = json.load(open(os.path.join(_DATA, "bible", "verses.json"), encoding="utf-8"))
    books_ko = json.load(open(os.path.join(_DATA, "names_ko", "books.json"), encoding="utf-8"))
    summaries = json.load(open(os.path.join(_DATA, "chapter_summaries", "books.json"), encoding="utf-8"))

    # 정본에서 권별 장 수 도출 (BB → max CCC)
    chapter_count = {}
    for k in verses:
        bb, ccc = int(k[:2]), int(k[2:5])
        chapter_count[bb] = max(chapter_count.get(bb, 0), ccc)
    bb_of = {tid: i for i, tid in enumerate(books_ko, 1)}

    violations = []
    total = 0

    missing_books = [tid for tid in books_ko if tid not in summaries]
    if missing_books:
        violations.append(f"[커버리지] 누락 권 {len(missing_books)}: {[books_ko[t]['ko'] for t in missing_books]}")
    for tid in summaries:
        if tid not in bb_of:
            violations.append(f"[커버리지] 미지의 bookId: {tid}")

    for tid, entries in summaries.items():
        if tid not in bb_of:
            continue
        bb = bb_of[tid]
        ko = books_ko[tid]["ko"]
        expected = chapter_count[bb]
        chapters = [e.get("chapter") for e in entries]
        if chapters != list(range(1, expected + 1)):
            violations.append(f"[커버리지] {ko}: 장 수/순서 불일치 (기대 1..{expected}, 실제 {len(chapters)}개)")
        for e in entries:
            total += 1
            c, s, vid = e.get("chapter"), e.get("summary"), e.get("keyVerseId")
            if not s or not isinstance(s, str) or not (1 <= len(s) <= 60):
                violations.append(f"[요약] {ko} {c}장: 길이 위반 ({len(s or '')}자)")
            if not vid or vid not in verses:
                violations.append(f"[대표절] {ko} {c}장: keyVerseId 미실존 ({vid})")
            elif vid[:5] != f"{bb:02d}{c:03d}":
                violations.append(f"[대표절] {ko} {c}장: 장 범위 밖 ({vid})")

    print(f"검사: {len(summaries)}권 {total}장")
    if violations:
        print(f"FAIL — 위반 {len(violations)}건")
        for v in violations[:40]:
            print(" -", v)
        sys.exit(1)
    print("PASS — 탈락 0")


if __name__ == "__main__":
    main()
