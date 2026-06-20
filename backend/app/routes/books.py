from fastapi import APIRouter
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


@router.get("/books")
def get_books():
    """타임라인 배치용 책 목록. startYear 있으면 그대로(yearApprox=false),
    없으면 추정연도 오버레이(yearApprox=true). 연도를 못 얻는 책은 제외."""
    approx = overlays.approx_years()
    book_events = overlays.book_events_raw()
    driver = get_driver()
    with driver.session() as session:
        result = session.run("MATCH (b:Book) RETURN b ORDER BY b.bookOrder ASC")
        books = []
        for record in result:
            props = dict(record["b"])
            tid = props.get("theographic_id", "")
            start_year = props.get("startYear")
            year_approx = False
            basis = None
            if start_year is None:
                a = approx.get(tid)
                if a is not None:
                    start_year = a.get("placementYear")
                    basis = a.get("basis")
                    year_approx = True
            if start_year is None:
                continue  # 정확·추정 연도 모두 없는 책은 시대순 배치 불가 → 제외
            books.append({
                "id": tid,
                "name": props.get("name", ""),
                "nameKo": props.get("nameKo"),
                "testament": props.get("testament"),
                "bookOrder": props.get("bookOrder"),
                "startYear": int(start_year),
                "endYear": props.get("endYear"),
                "yearApprox": year_approx,
                "yearBasis": basis,
                "genre": props.get("genre"),
                "themes": props.get("themes"),
                "keyVerse": props.get("keyVerse"),
                "keyVerseTextKo": props.get("keyVerseTextKo"),
                "events": book_events.get(tid, []),
            })
        return JSONResponse(content=books, headers={"Cache-Control": "no-store"})
