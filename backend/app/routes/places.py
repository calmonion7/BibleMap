"""장소를 지나는 큐레이션 인물 엔드포인트.

person_events/<slug>.json 의 occursAt 배열을 검사해 place_id 를 포함하는
인물을 필터링한다. Neo4j 조회 없이 파일만으로 결정적.
era/이름 매핑은 curated.py를 단일 출처로 import한다(드리프트 방지)."""
import functools
import logging

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from .. import overlays
from ..curated import CURATED, ERA_ORDER, person_events
from ..overlays import curated_person_id

logger = logging.getLogger(__name__)

router = APIRouter()


@functools.lru_cache(maxsize=256)
def _place_to_persons(place_id: str) -> list[dict]:
    """place_id 를 포함하는 큐레이션 인물 목록(era순 정렬). 결과 캐시."""
    result = []
    for slug in CURATED:
        events = person_events(slug)
        if not events:
            continue

        # 이 인물의 어느 사건이든 occursAt[0](정차 장소)이 place_id 면 포함.
        # journey.py/tours.py가 occursAt[0]만 정차지로 쓰므로 판정 기준 일치(2차 장소 제외).
        visited = any((evt.get("occursAt") or [None])[0] == place_id for evt in events)
        if not visited:
            continue

        person_id = curated_person_id(events)
        if person_id is None:
            logger.warning("[Places] curated-persons: %s — events[0].participants 비어 있음, 건너뜀", slug)
            continue
        result.append(
            {
                "id": person_id,
                "slug": slug,
                "nameKo": CURATED[slug]["nameKo"],
                "era": CURATED[slug]["era"],
                # 정렬 전용: 여정 최초 등장 시점(최소 sortKey). 응답 전 제거.
                "_anchor": min(e["sortKey"] for e in events),
            }
        )

    # curated.curated_index와 동일 규칙: 시대 내 최초 등장 시간순, 동시각 slug tie-break
    result.sort(key=lambda p: (ERA_ORDER.index(p["era"]), p["_anchor"], p["slug"]))
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


@functools.lru_cache(maxsize=256)
def _place_events(place_id: str) -> list[dict]:
    """이 장소에서 일어난 사건 목록(연대순) — 인물 귀속 포함.

    판정 기준은 `occursAt[0]`(정차 장소)로 `_place_to_persons`·journey·tours와 **일치**시킨다.
    기준이 갈리면 같은 장소인데 화면마다 숫자가 달라진다(계획의 핵심 제약).
    """
    events = []
    for slug in CURATED:
        for evt in person_events(slug):
            if (evt.get("occursAt") or [None])[0] != place_id:
                continue
            events.append({
                "id": evt.get("id"),
                "nameKo": evt.get("nameKo") or evt.get("title"),
                "yearLabel": evt.get("yearLabel"),
                "sortKey": evt.get("sortKey"),
                "context": evt.get("context"),
                "personSlug": slug,
                "personNameKo": CURATED[slug]["nameKo"],
            })
    # 같은 사건이 여러 인물 파일에 있을 수 있다 — id 기준 1회만(먼저 만난 인물로 귀속).
    seen, unique = set(), []
    for e in sorted(events, key=lambda e: (e["sortKey"] if e["sortKey"] is not None else 0, e["id"] or "")):
        if e["id"] in seen:
            continue
        seen.add(e["id"])
        unique.append(e)
    return unique


@router.get("/place/{place_id}")
def get_place(place_id: str):
    """장소 페이지(task#270) — 배경·핵심 구절 + 좌표 + 거쳐 간 큐레이션 인물 + 그곳의 사건.

    컨텍스트가 없는 좌표 전용 장소도 200으로 응답한다(빈 폴백) — 지도 마커 어디서 들어와도
    화면이 열려야 하기 때문. 넷 다 비면 그때 404.
    """
    ctx = overlays.place_context().get(place_id) or {}
    coords = overlays.place_coords().get(place_id) or {}
    persons = _place_to_persons(place_id)
    events = _place_events(place_id)

    if not ctx and not coords and not persons and not events:
        raise HTTPException(status_code=404, detail="unknown place")

    return JSONResponse(
        content={
            "placeId": place_id,
            "nameKo": coords.get("nameKo") or ctx.get("nameKo") or place_id,
            "name": coords.get("name"),
            "lat": coords.get("lat"),
            "lng": coords.get("lng"),
            "background": ctx.get("background"),
            "keyVerse": ctx.get("keyVerse"),
            "keyVerseTextKo": ctx.get("keyVerseTextKo"),
            "keyVerseTextEn": ctx.get("keyVerseTextEn"),
            "persons": persons,
            "events": events,
        },
        headers={"Cache-Control": "max-age=300"},
    )
