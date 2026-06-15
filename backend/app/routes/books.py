import json
import os

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ..db import get_driver

router = APIRouter()

# 시대 연도(startYear)가 없는 책의 추정연도 오버레이. data 볼륨 마운트(/app/data)에서 런타임 로드.
_DATA_DIR = os.environ.get("DATA_DIR", "/app/data")
_APPROX_PATH = os.path.join(_DATA_DIR, "book_years_approx", "books.json")


def _load_approx():
    try:
        with open(_APPROX_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


@router.get("/books")
def get_books():
    """타임라인 배치용 책 목록. startYear 있으면 그대로(yearApprox=false),
    없으면 추정연도 오버레이(yearApprox=true). 연도를 못 얻는 책은 제외."""
    approx = _load_approx()
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
            })
        return JSONResponse(content=books, headers={"Cache-Control": "no-store"})
