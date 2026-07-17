import functools

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from ..db import get_driver
from .. import overlays

router = APIRouter()


@router.get("/books-overview")
def get_books_overview():
    """개요 뷰 전용 책 목록. startYear 조건 없이 전체 반환."""
    driver = get_driver()
    with driver.session() as session:
        result = session.run("MATCH (b:Book) RETURN b ORDER BY b.bookOrder ASC")
        books = []
        for record in result:
            props = dict(record["b"])
            books.append({
                "id": props.get("theographic_id", ""),
                "nameKo": props.get("nameKo"),
                "testament": props.get("testament"),
                "bookOrder": props.get("bookOrder"),
                "genre": props.get("genre"),
                "themes": props.get("themes"),
                "keyVerse": props.get("keyVerse"),
                "keyVerseTextKo": props.get("keyVerseTextKo"),
                "authorKo": props.get("authorKo"),
                "writtenDate": props.get("writtenDate"),
            })
        return JSONResponse(content=books, headers={"Cache-Control": "no-store"})


@functools.lru_cache(maxsize=1)
def _book_bb() -> dict:
    """theographic_id → 정경 순번 BB(1-based). reliance._alias_to_bb와 같은 books_ko() 순서 도출."""
    return {tid: i for i, tid in enumerate(overlays.books_ko(), 1)}


@functools.lru_cache(maxsize=1)
def _book_meta() -> dict:
    """theographic_id → {nameKo, chapterCount} — Book 노드 1회 로드 캐시(리더 헤더·장 경계용)."""
    driver = get_driver()
    with driver.session() as session:
        result = session.run(
            "MATCH (b:Book) RETURN b.theographic_id AS id, b.nameKo AS nameKo, b.chapterCount AS chapterCount"
        )
        return {r["id"]: {"nameKo": r["nameKo"], "chapterCount": r["chapterCount"]} for r in result}


@functools.lru_cache(maxsize=2048)
def _chapter_payload(book_id: str, n: int) -> "dict | None":
    """장 본문 페이로드 — 정본 절 사전(BBCCCVVV)에서 그 장의 절을 절 번호순으로 추출. 장 단위 캐시."""
    bb = _book_bb().get(book_id)
    if not bb:
        return None
    prefix = f"{bb:02d}{n:03d}"
    verses_all = overlays.bible_verses()
    keys = sorted(k for k in verses_all if k.startswith(prefix))
    meta = _book_meta().get(book_id, {})
    return {
        "bookId": book_id,
        "nameKo": meta.get("nameKo") or overlays.books_ko().get(book_id, {}).get("ko"),
        "chapterCount": meta.get("chapterCount"),
        "chapter": n,
        "verses": [
            {
                "verseId": k,
                "v": int(k[5:]),
                "textKo": verses_all[k].get("textKo"),
                "textEn": verses_all[k].get("textEn"),
            }
            for k in keys
        ],
    }


@router.get("/book/{book_id}/chapter/{n}")
def get_book_chapter(book_id: str, n: int):
    """본문 리더(task#205) — 책의 n장 절 목록(한/영). 미지의 책은 404, 범위 밖 장은 빈 목록."""
    payload = _chapter_payload(book_id, n)
    if payload is None:
        raise HTTPException(status_code=404, detail="unknown book")
    return JSONResponse(payload, headers={"Cache-Control": "public, max-age=3600"})
