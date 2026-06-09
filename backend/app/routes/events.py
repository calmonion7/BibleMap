from fastapi import APIRouter
from fastapi.responses import JSONResponse
from ..db import get_driver

router = APIRouter()

@router.get("/events")
def get_events():
    driver = get_driver()
    with driver.session() as session:
        result = session.run(
            "MATCH (e:Event) WHERE e.startDate IS NOT NULL "
            "RETURN e ORDER BY e.sortKey ASC"
        )
        events = []
        for record in result:
            e = record["e"]
            props = dict(e)
            events.append({
                "id": props.get("theographic_id", ""),
                "title": props.get("title", ""),
                "nameKo": props.get("nameKo"),
                "startDate": props.get("startDate", ""),
                "sortKey": float(props.get("sortKey", 0)),
            })
        return JSONResponse(content=events, headers={"Cache-Control": "no-store"})
