from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ..db import get_driver

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
