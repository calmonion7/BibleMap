"""절 본문 검색 공용 헬퍼 — 통합 검색(`/search`)과 단어 절 목록(`/words/{book_id}/verses`)이 함께 쓴다(task#267).

정본 절 사전(`overlays.bible_verses()`, 키 `BBCCCVVV`)을 substring 스캔한다. 역색인이 아니라
31,103절 전수 스캔이므로 질의 단위 `lru_cache`로 반복 질의를 흡수한다(CONCERNS "전수 스캔" 항목과 같은 성질).
"""

import functools

from . import overlays


@functools.lru_cache(maxsize=256)
def search_verses(term: str, book_id: str = "all", match_en: bool = False) -> tuple:
    """`term`을 포함하는 절을 정경 순서로 반환 — `(total, (항목, ...))`.

    항목은 `{verseId, bookId, chapter, verse, ref, textKo, textEn}`. `match_en`이 참이면
    `textEn`도 대소문자 무시로 매칭한다. 결과 상한은 호출부가 슬라이스한다(총계는 `total`이 보존).
    """
    term = term.strip()
    if not term:
        return 0, ()

    books = overlays.books_ko()
    book_ids = list(books)  # 정경 순서 1~66 = 절 키 BBCCCVVV의 BB
    prefix = None
    if book_id != "all":
        if book_id not in books:
            return 0, ()
        prefix = f"{book_ids.index(book_id) + 1:02d}"

    term_en = term.lower() if match_en else None
    items = []
    for key in sorted(overlays.bible_verses()):
        if prefix and not key.startswith(prefix):
            continue
        v = overlays.bible_verses()[key]
        ko = v.get("textKo") or ""
        en = v.get("textEn") or ""
        if term not in ko and not (term_en and term_en in en.lower()):
            continue
        bb = int(key[:2])
        chapter, verse = int(key[2:5]), int(key[5:8])
        meta = books.get(book_ids[bb - 1]) or {}
        abbr = (meta.get("alias") or [meta.get("ko", "")])[0]
        items.append({
            "verseId": key,
            "bookId": book_ids[bb - 1],
            "chapter": chapter,
            "verse": verse,
            "ref": f"{abbr} {chapter}:{verse}",
            "textKo": ko,
            "textEn": en,
        })
    return len(items), tuple(items)
