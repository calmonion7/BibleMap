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

@router.get("/events")
def get_events():
    """타임라인 사건 목록. 각 사건에 그 사건을 기록한 성경권(CONTAINS_BOOK)을
    정경순(bookOrder ASC) books 배열로 함께 반환 — 사건의 근거 칩 표시용.
    사건 없는 권은 여기 등장하지 않는다(권→사건 방향이라 OPTIONAL은 사건 기준)."""
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
            events.append({
                "id": props.get("theographic_id", ""),
                "title": props.get("title", ""),
                "nameKo": props.get("nameKo"),
                "startDate": props.get("startDate", ""),
                "sortKey": float(props.get("sortKey", 0)),
                "books": record["books"],
            })
        return JSONResponse(content=events, headers={"Cache-Control": "no-store"})


@router.get("/event/{event_id}/verses")
def get_event_verses(event_id: str):
    """사건의 근거 구절을 권별로 그룹·정경순으로 반환(드릴다운용). 책 키 bookId는
    /events books의 id(theographic_id)와 일치 — 프론트가 id로 join. 없으면 빈 books."""
    overlay = _load_event_verses()
    entry = overlay.get(event_id, {"books": []})
    return JSONResponse(content=entry, headers={"Cache-Control": "no-store"})
