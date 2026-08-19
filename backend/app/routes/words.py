from fastapi import APIRouter, HTTPException, Query

from .. import overlays
from ..verse_search import search_verses

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
    total, items = search_verses(w, book_id)
    verses = [{"ref": it["ref"], "textKo": it["textKo"], "textEn": it["textEn"]} for it in items[:VERSE_LIMIT]]
    return {"word": w, "total": total, "verses": verses}
