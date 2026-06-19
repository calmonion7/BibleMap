import functools
import json
import os

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ..db import get_driver

router = APIRouter()

# 시대 연도(startYear)가 없는 책의 추정연도 오버레이.
# DATA_DIR(기본 /app/data, docker 볼륨 마운트) 우선, 없으면 레포 상대경로(data/) 폴백 →
# docker/비-docker 모두에서 파일을 찾는다.
_REPO_DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
    "data",
)
_APPROX_CANDIDATES = [
    os.path.join(os.environ.get("DATA_DIR", "/app/data"), "book_years_approx", "books.json"),
    os.path.join(_REPO_DATA_DIR, "book_years_approx", "books.json"),
]
# 추정연도 책 → 연결 사건 오버레이({bookId: [eventId,...]}). CONTAINS_BOOK(구절 교집합=
# 사건의 근거)와 별개의 "집필 배경/저자/직접 다루는" 연결 — Neo4j에 넣지 않고 런타임 오버레이.
_BOOK_EVENTS_CANDIDATES = [
    os.path.join(os.environ.get("DATA_DIR", "/app/data"), "book_events", "books.json"),
    os.path.join(_REPO_DATA_DIR, "book_events", "books.json"),
]


@functools.lru_cache(maxsize=1)
def _load_approx():
    """추정연도 오버레이 JSON을 1회만 로드(캐시). DATA_DIR → 레포 상대경로 순으로
    탐색하고, 어느 후보에서도 못 읽으면 기존처럼 빈 dict 폴백."""
    for path in _APPROX_CANDIDATES:
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            continue
    return {}


@functools.lru_cache(maxsize=1)
def _load_book_events():
    """책→연결사건 오버레이 JSON을 1회만 로드(캐시). 탐색·폴백은 _load_approx와 동일."""
    for path in _BOOK_EVENTS_CANDIDATES:
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            continue
    return {}


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
            })
        return JSONResponse(content=books, headers={"Cache-Control": "no-store"})


@router.get("/books")
def get_books():
    """타임라인 배치용 책 목록. startYear 있으면 그대로(yearApprox=false),
    없으면 추정연도 오버레이(yearApprox=true). 연도를 못 얻는 책은 제외."""
    approx = _load_approx()
    book_events = _load_book_events()
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
