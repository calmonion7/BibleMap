from fastapi import APIRouter
from fastapi.responses import JSONResponse
from ..db import get_driver

router = APIRouter()

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
