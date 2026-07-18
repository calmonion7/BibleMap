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
    # 장 개요 오버레이 합성(task#206) — 없으면 None(리더 헤더가 조용히 생략)
    summary = next(
        (e.get("summary") for e in overlays.chapter_summaries().get(book_id, []) if e.get("chapter") == n),
        None,
    )
    return {
        "bookId": book_id,
        "nameKo": meta.get("nameKo") or overlays.books_ko().get(book_id, {}).get("ko"),
        "chapterCount": meta.get("chapterCount"),
        "chapter": n,
        "summary": summary,
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


@router.get("/book/{book_id}/chapters")
def get_book_chapters(book_id: str):
    """본문 리더 장 목차(task#206) — 장별 개요·대표절 목록 + 장 묶음(task#212). 오버레이 없으면 빈 목록으로 폴백."""
    bb = _book_bb().get(book_id)
    if not bb:
        raise HTTPException(status_code=404, detail="unknown book")
    meta = _book_meta().get(book_id, {})
    return JSONResponse(
        {
            "bookId": book_id,
            "nameKo": meta.get("nameKo") or overlays.books_ko().get(book_id, {}).get("ko"),
            "chapterCount": meta.get("chapterCount"),
            "chapters": overlays.chapter_summaries().get(book_id, []),
            "sections": overlays.chapter_sections().get(book_id, []),
        },
        headers={"Cache-Control": "public, max-age=3600"},
    )


@functools.lru_cache(maxsize=66)
def _quotations_payload(book_id: str) -> "dict | None":
    """인용 관계 페이로드(task#210) — 구약 권은 '이 책을 인용한 신약'(quotedBy), 신약 권은
    '이 책이 인용한 구약'(quotes). 본문은 정본 절 사전에서 합성(ADR-0015), 권별 집계 동봉."""
    bb = _book_bb().get(book_id)
    if not bb:
        return None
    is_ot = bb <= 39
    prefix = f"{bb:02d}"
    verses_all = overlays.bible_verses()
    books_ko = overlays.books_ko()
    tids = list(books_ko)

    def side(ids, label):
        return {
            "rangeLabel": label,
            "verses": [
                {"verseId": k, "textKo": verses_all.get(k, {}).get("textKo"), "textEn": verses_all.get(k, {}).get("textEn")}
                for k in ids
            ],
        }

    pairs = []
    for q in overlays.quotations():
        mine = q["otVerseIds"] if is_ot else q["ntVerseIds"]
        if not mine[0].startswith(prefix):
            continue
        other_ids = q["ntVerseIds"] if is_ot else q["otVerseIds"]
        other_tid = tids[int(other_ids[0][:2]) - 1]
        pairs.append({
            "counterpartBookId": other_tid,
            "counterpartNameKo": books_ko[other_tid]["ko"],
            "nt": side(q["ntVerseIds"], q["ntRangeLabel"]),
            "ot": side(q["otVerseIds"], q["otRangeLabel"]),
            **({"note": q["note"]} if q.get("note") else {}),
        })

    counts: dict = {}
    for p in pairs:
        counts[p["counterpartBookId"]] = counts.get(p["counterpartBookId"], 0) + 1
    books = [
        {"bookId": tid, "nameKo": books_ko[tid]["ko"], "count": counts[tid]}
        for tid in tids if tid in counts  # 정경 순
    ]
    return {"bookId": book_id, "direction": "quotedBy" if is_ot else "quotes", "books": books, "pairs": pairs}


@router.get("/book/{book_id}/quotations")
def get_book_quotations(book_id: str):
    """책 기준 인용 관계(task#210) — 미지 책 404, 인용 0건 권은 빈 배열."""
    payload = _quotations_payload(book_id)
    if payload is None:
        raise HTTPException(status_code=404, detail="unknown book")
    return JSONResponse(payload, headers={"Cache-Control": "public, max-age=3600"})


@router.get("/book/{book_id}/chapter/{n}")
def get_book_chapter(book_id: str, n: int):
    """본문 리더(task#205) — 책의 n장 절 목록(한/영). 미지의 책은 404, 범위 밖 장은 빈 목록."""
    payload = _chapter_payload(book_id, n)
    if payload is None:
        raise HTTPException(status_code=404, detail="unknown book")
    return JSONResponse(payload, headers={"Cache-Control": "public, max-age=3600"})
