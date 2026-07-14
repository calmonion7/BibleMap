from fastapi import APIRouter, HTTPException, Query

from .. import overlays

router = APIRouter()

VERSE_LIMIT = 200


@router.get("/words/{book_id}")
def get_words(book_id: str):
    """책(theographic_id) 또는 "all"의 단어 분포 — [{word, count, polarity}]."""
    entry = overlays.word_distribution().get(book_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="unknown book")
    return {"bookId": book_id, "nameKo": entry.get("nameKo"), "words": entry["words"]}


@router.get("/words/{book_id}/verses")
def get_word_verses(book_id: str, w: str = Query("")):
    """해당 책(또는 전체)에서 textKo에 w를 포함하는 구절 목록. substring 매칭이라 활용형 포함."""
    w = w.strip()
    if not w:
        return {"word": w, "total": 0, "verses": []}
    if book_id not in overlays.word_distribution():
        raise HTTPException(status_code=404, detail="unknown book")
    books = overlays.books_ko()
    book_ids = list(books.keys())  # 정경 순서 1~66 = 절 키 BBCCCVVV의 BB
    prefix = f"{book_ids.index(book_id) + 1:02d}" if book_id != "all" else None

    matches = []
    for key, v in overlays.bible_verses().items():
        if prefix and not key.startswith(prefix):
            continue
        text = v.get("textKo") or ""
        if w in text:
            matches.append((key, text, v.get("textEn") or ""))

    verses = []
    for key, ko, en in matches[:VERSE_LIMIT]:
        meta = books.get(book_ids[int(key[:2]) - 1]) or {}
        abbr = (meta.get("alias") or [meta.get("ko", "")])[0]
        verses.append({"ref": f"{abbr} {int(key[2:5])}:{int(key[5:8])}", "textKo": ko, "textEn": en})
    return {"word": w, "total": len(matches), "verses": verses}
