"""GET /tours — 테마 투어 목록
GET /tour/{tour_id} — 테마 투어 상세 (stops 포함)

투어 정의: data/tours/{id}.json  {id, title, subtitle, era, description, stops:[eventId,...]}
ADR-0011: tours는 event-reference 오버레이 — Neo4j 노드 추가·주입 없음.
"""
import functools
import glob
import json
import os

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ..overlays import _resolve
from .journey import _fetch_place_coords
from .persons import _ERA

router = APIRouter()


def _tours_dir() -> str | None:
    """data/tours 디렉터리 경로 반환 (overlays._resolve 방식과 동일한 우선순위)."""
    for base in (os.environ.get("DATA_DIR", "/app/data"),
                 os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
                     os.path.dirname(__file__)))), "data")):
        d = os.path.join(base, "tours")
        if os.path.isdir(d):
            return d
    return None


@functools.lru_cache(maxsize=1)
def _list_tours() -> list[dict]:
    """data/tours/*.json 을 스캔해 {id, title, subtitle, era, stopCount} 목록 반환."""
    d = _tours_dir()
    if d is None:
        return []
    results = []
    for path in sorted(glob.glob(os.path.join(d, "*.json"))):
        try:
            with open(path, encoding="utf-8") as f:
                t = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue
        results.append({
            "id": t.get("id", os.path.splitext(os.path.basename(path))[0]),
            "title": t.get("title"),
            "subtitle": t.get("subtitle"),
            "era": t.get("era"),
            "stopCount": len(t.get("stops", [])),
        })
    return results


@functools.lru_cache(maxsize=1)
def _build_event_index() -> dict[str, dict]:
    """eventId → event-body 인덱스. _ERA 내 모든 slug의 person_events/*.json 로드."""
    index: dict[str, dict] = {}
    for slug in _ERA:
        path = _resolve(f"person_events/{slug}.json")
        if path is None:
            continue
        try:
            with open(path, encoding="utf-8") as f:
                events = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue
        for e in events:
            index[e["id"]] = e
    return index


@router.get("/tours")
def list_tours():
    return JSONResponse(
        content=_list_tours(),
        headers={"Cache-Control": "max-age=300"},
    )


@router.get("/tour/{tour_id}")
def get_tour(tour_id: str):
    path = _resolve(f"tours/{tour_id}.json")
    if path is None:
        # eco: soft-empty pattern — journey.py 와 동일, 404 아님
        return JSONResponse(
            content={"id": tour_id, "title": None, "stops": []},
            headers={"Cache-Control": "max-age=300"},
        )

    with open(path, encoding="utf-8") as f:
        tour = json.load(f)

    event_index = _build_event_index()
    stop_ids: list[str] = tour.get("stops", [])

    # 알 수 없는 id 제거 후 sortKey 순 정렬
    events = sorted(
        (event_index[eid] for eid in stop_ids if eid in event_index),
        key=lambda e: e["sortKey"],
    )

    # 좌표 조회
    place_ids = list({
        e["occursAt"][0]
        for e in events
        if e.get("occursAt")
    })
    coords = _fetch_place_coords(place_ids)

    # journey.py 와 동일한 stops 구조
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
            "id": tour["id"],
            "title": tour.get("title"),
            "subtitle": tour.get("subtitle"),
            "era": tour.get("era"),
            "description": tour.get("description"),
            "stops": stops,
        },
        headers={"Cache-Control": "max-age=300"},
    )
