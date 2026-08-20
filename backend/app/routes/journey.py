"""GET /person/{id}/journey — 큐레이션 인물의 시간순 여정 정차지.

응답 stops 필드:
  seq: 좌표가 있는 정차지에만 1부터 부여(없으면 null)
  연속 동일 좌표 사건도 각각 stop으로 포함(0길이 세그먼트 방지는 프론트 담당).
큐레이션 35인이 아니면 빈 stops 반환(404 아님).
"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from ..db import get_driver
from ..curated import CURATED, id_to_slug, person_events

router = APIRouter()


def _fetch_place_coords(place_ids: list[str]) -> dict[str, dict]:
    """Neo4j에서 Place 노드의 longitude/latitude를 배치 조회.
    반환: {theographic_id: {"lng": float, "lat": float, "nameKo": str|None}}
    """
    if not place_ids:
        return {}
    driver = get_driver()
    with driver.session() as session:
        result = session.run(
            """
            UNWIND $ids AS tid
            MATCH (p:Place {theographic_id: tid})
            RETURN p.theographic_id AS id,
                   p.longitude               AS lng,
                   p.latitude                AS lat,
                   coalesce(p.nameKo, p.name, p.title) AS nameKo
            """,
            ids=place_ids,
        )
        coords: dict[str, dict] = {}
        for r in result:
            lng = r["lng"]
            lat = r["lat"]
            coords[r["id"]] = {
                "lng": float(lng) if lng is not None else None,
                "lat": float(lat) if lat is not None else None,
                "nameKo": r["nameKo"],
            }
    return coords


@router.get("/person/{person_id}/journey")
def get_person_journey(person_id: str):
    """인물의 시간순 여정 정차지 목록.

    큐레이션 35인이 아니면 stops=[] 빈 응답 반환.
    stops 각 항목:
      seq, eventId, title, nameKo, sortKey, placeId, placeNameKo, lng, lat
    """
    slug = id_to_slug().get(person_id)

    if slug is None:
        return JSONResponse(
            content={"personId": person_id, "nameKo": None, "stops": []},
            headers={"Cache-Control": "max-age=300"},
        )

    events = person_events(slug)

    # 좌표가 필요한 place_id 수집 (occursAt[0] 기준)
    place_ids = list({
        e["occursAt"][0]
        for e in events
        if e.get("occursAt")
    })
    coords = _fetch_place_coords(place_ids)

    stops = []
    seq_counter = 0
    for event in events:
        place_id = event["occursAt"][0] if event.get("occursAt") else None
        place_info = coords.get(place_id) if place_id else None

        has_coords = (
            place_info is not None
            and place_info["lng"] is not None
            and place_info["lat"] is not None
        )

        if has_coords:
            seq_counter += 1
            seq = seq_counter
        else:
            seq = None

        stops.append({
            "seq": seq,
            "eventId": event["id"],
            "title": event["title"],
            "nameKo": event["nameKo"],
            "sortKey": event["sortKey"],
            "placeId": place_id,
            "placeNameKo": place_info["nameKo"] if place_info else None,
            "lng": place_info["lng"] if place_info else None,
            "lat": place_info["lat"] if place_info else None,
        })

    return JSONResponse(
        content={
            "personId": person_id,
            "nameKo": CURATED[slug]["nameKo"],
            "stops": stops,
        },
        headers={"Cache-Control": "max-age=300"},
    )
