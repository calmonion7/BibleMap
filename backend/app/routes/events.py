import functools
import json
import os

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from ..db import get_driver

router = APIRouter()

# 사건별 근거 구절 오버레이(권별 그룹·rangeLabel).
# DATA_DIR(기본 /app/data, docker 볼륨 마운트) 우선, 없으면 레포 상대경로(data/) 폴백.
_REPO_DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
    "data",
)
_EVENT_VERSES_CANDIDATES = [
    os.path.join(os.environ.get("DATA_DIR", "/app/data"), "event_verses", "events.json"),
    os.path.join(_REPO_DATA_DIR, "event_verses", "events.json"),
]
_BOOK_EVENTS_CANDIDATES = [
    os.path.join(os.environ.get("DATA_DIR", "/app/data"), "book_events", "books.json"),
    os.path.join(_REPO_DATA_DIR, "book_events", "books.json"),
]


@functools.lru_cache(maxsize=1)
def _load_event_verses():
    """사건별 구절 오버레이 JSON을 1회만 로드(캐시). DATA_DIR → 레포 상대경로 순으로
    탐색하고, 어느 후보에서도 못 읽으면 빈 dict 폴백."""
    for path in _EVENT_VERSES_CANDIDATES:
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            continue
    return {}


@functools.lru_cache(maxsize=1)
def _load_approx_book_index():
    """book_events.json({bookId:[eventId]}) → 역방향 {eventId:[bookId]} + Neo4j Book 메타.
    반환: (event_to_books: dict, book_meta: dict).
    event_to_books: {eventId: [{id, nameKo, name, bookOrder}]}
    book_meta는 중간 조회용으로만 사용."""
    book_events = {}
    for path in _BOOK_EVENTS_CANDIDATES:
        try:
            with open(path, encoding="utf-8") as f:
                book_events = json.load(f)
            break
        except (FileNotFoundError, json.JSONDecodeError):
            continue
    if not book_events:
        return {}

    # Neo4j에서 책 메타 일괄 조회
    book_ids = list(book_events.keys())
    driver = get_driver()
    with driver.session() as session:
        rows = session.run(
            "MATCH (b:Book) WHERE b.theographic_id IN $ids "
            "RETURN b.theographic_id AS id, b.nameKo AS nameKo, "
            "b.name AS name, b.bookOrder AS bookOrder",
            ids=book_ids,
        ).data()
    book_meta = {r["id"]: r for r in rows}

    # 역방향 맵 구성
    event_to_books: dict = {}
    for book_id, event_ids in book_events.items():
        meta = book_meta.get(book_id)
        if meta is None:
            continue
        book_entry = {
            "id": meta["id"],
            "nameKo": meta["nameKo"],
            "name": meta["name"],
            "bookOrder": meta["bookOrder"],
        }
        for eid in event_ids:
            event_to_books.setdefault(eid, []).append(book_entry)

    # 각 이벤트의 책 목록 bookOrder 정렬
    for eid in event_to_books:
        event_to_books[eid].sort(key=lambda b: b["bookOrder"])

    return event_to_books


@functools.lru_cache(maxsize=1)
def _compute_events():
    """Neo4j 쿼리 + approx_index 머지. 앱 재시작 전까지 결과를 메모리에 보관."""
    approx_index = _load_approx_book_index()
    driver = get_driver()
    with driver.session() as session:
        result = session.run(
            "MATCH (e:Event) WHERE e.startDate IS NOT NULL "
            "OPTIONAL MATCH (b:Book)-[:CONTAINS_BOOK]->(e) "
            "WITH e, b ORDER BY b.bookOrder ASC "
            "WITH e, collect(CASE WHEN b IS NULL THEN NULL ELSE "
            "  {id: b.theographic_id, nameKo: b.nameKo, name: b.name, bookOrder: b.bookOrder} "
            "END) AS books "
            "RETURN e, books ORDER BY e.sortKey ASC"
        )
        events = []
        for record in result:
            props = dict(record["e"])
            event_id = props.get("theographic_id", "")
            contains_books = [b for b in record["books"] if b is not None]
            approx_books = approx_index.get(event_id, [])
            contains_ids = {b["id"] for b in contains_books}
            extra = [b for b in approx_books if b["id"] not in contains_ids]
            events.append({
                "id": event_id,
                "title": props.get("title", ""),
                "nameKo": props.get("nameKo"),
                "startDate": props.get("startDate", ""),
                "sortKey": float(props.get("sortKey", 0)),
                "authored": props.get("authored", False),
                "yearLabel": props.get("yearLabel"),
                "books": contains_books + extra,
            })
        return events


@router.get("/events")
def get_events():
    """타임라인 사건 목록. 각 사건에 그 사건을 기록한 성경권(CONTAINS_BOOK)을
    정경순(bookOrder ASC) books 배열로 함께 반환 — 사건의 근거 칩 표시용.
    추정책(집필 배경 연결)은 CONTAINS_BOOK 항목 뒤에 추가된다.
    사건 없는 권은 여기 등장하지 않는다(권→사건 방향이라 OPTIONAL은 사건 기준)."""
    return JSONResponse(content=_compute_events(), headers={"Cache-Control": "max-age=300"})


@router.get("/event/{event_id}/verses")
def get_event_verses(event_id: str):
    """사건의 근거 구절을 권별로 그룹·정경순으로 반환(드릴다운용). 책 키 bookId는
    /events books의 id(theographic_id)와 일치 — 프론트가 id로 join. 없으면 빈 books."""
    overlay = _load_event_verses()
    entry = overlay.get(event_id, {"books": []})
    return JSONResponse(content=entry, headers={"Cache-Control": "max-age=300"})
