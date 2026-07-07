"""장소를 지나는 큐레이션 인물 엔드포인트.

person_events/<slug>.json 의 occursAt 배열을 검사해 place_id 를 포함하는
인물을 필터링한다. Neo4j 조회 없이 파일만으로 결정적.
era/이름 매핑은 persons.py를 단일 출처로 import한다(드리프트 방지)."""
import functools
import json
import logging

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from ..overlays import _resolve
from .persons import _ERA, _NAME_KO, _ERA_ORDER

router = APIRouter()


@functools.lru_cache(maxsize=None)
def _place_to_persons(place_id: str) -> list[dict]:
    """place_id 를 포함하는 큐레이션 인물 목록(era순 정렬). 결과 캐시."""
    result = []
    for slug in _ERA:
        path = _resolve(f"person_events/{slug}.json")
        if path is None:
            continue
        with open(path, encoding="utf-8") as f:
            events = json.load(f)

        # 이 인물의 어느 사건이든 occursAt 에 place_id 가 있으면 포함
        visited = any(place_id in evt.get("occursAt", []) for evt in events)
        if not visited:
            continue

        if not events or not events[0].get("participants"):
            logging.warning("place/curated-persons: %s — events[0].participants 비어 있음, 건너뜀", slug)
            continue
        person_id = events[0]["participants"][0]
        result.append(
            {
                "id": person_id,
                "slug": slug,
                "nameKo": _NAME_KO[slug],
                "era": _ERA[slug],
                # 정렬 전용: 여정 최초 등장 시점(최소 sortKey). 응답 전 제거.
                "_anchor": min(e["sortKey"] for e in events),
            }
        )

    # persons.py _build_list와 동일 규칙: 시대 내 최초 등장 시간순, 동시각 slug tie-break
    result.sort(key=lambda p: (_ERA_ORDER.index(p["era"]), p["_anchor"], p["slug"]))
    for p in result:
        del p["_anchor"]
    return result


@router.get("/place/{place_id}/curated-persons")
def get_place_curated_persons(
    place_id: str,
    exclude: str = Query(default=None, description="제외할 인물 theographic_id"),
):
    """특정 장소를 여정에 포함하는 큐레이션 인물 목록.

    응답: { placeId, persons: [ {id, slug, nameKo, era}, ... ] }
    exclude 쿼리로 현재 탐험 인물을 결과에서 제외할 수 있음."""
    persons = _place_to_persons(place_id)
    if exclude:
        persons = [p for p in persons if p["id"] != exclude]

    return JSONResponse(
        content={"placeId": place_id, "persons": persons},
        headers={"Cache-Control": "max-age=300"},
    )
