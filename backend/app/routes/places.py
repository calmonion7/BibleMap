"""장소를 지나는 큐레이션 13인 엔드포인트.

person_events/<slug>.json 의 occursAt 배열을 검사해 place_id 를 포함하는
인물을 필터링한다. Neo4j 조회 없이 파일만으로 결정적."""
import functools
import json

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from ..overlays import _resolve

router = APIRouter()

# persons.py 와 동일한 상수 — 단방향 참조를 피하기 위해 여기서 재선언
_ERA: dict[str, str] = {
    "abraham": "족장",
    "isaac": "족장",
    "jacob": "족장",
    "joseph": "족장",
    "moses": "출애굽·정복",
    "joshua": "출애굽·정복",
    "samuel": "왕국",
    "david": "왕국",
    "solomon": "왕국",
    "isaiah": "선지자",
    "john_the_baptist": "신약",
    "jesus": "신약",
    "mary": "신약",
}

_NAME_KO: dict[str, str] = {
    "abraham": "아브라함",
    "isaac": "이삭",
    "jacob": "야곱",
    "joseph": "요셉",
    "moses": "모세",
    "joshua": "여호수아",
    "samuel": "사무엘",
    "david": "다윗",
    "solomon": "솔로몬",
    "isaiah": "이사야",
    "john_the_baptist": "세례 요한",
    "jesus": "예수",
    "mary": "마리아",
}

_ERA_ORDER = ["족장", "출애굽·정복", "왕국", "선지자", "신약"]


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

        person_id = events[0]["participants"][0]
        result.append(
            {
                "id": person_id,
                "slug": slug,
                "nameKo": _NAME_KO[slug],
                "era": _ERA[slug],
            }
        )

    result.sort(key=lambda p: (_ERA_ORDER.index(p["era"]), p["slug"]))
    return result


@router.get("/place/{place_id}/curated-persons")
def get_place_curated_persons(
    place_id: str,
    exclude: str = Query(default=None, description="제외할 인물 theographic_id"),
):
    """특정 장소를 여정에 포함하는 큐레이션 13인 목록.

    응답: { placeId, persons: [ {id, slug, nameKo, era}, ... ] }
    exclude 쿼리로 현재 탐험 인물을 결과에서 제외할 수 있음."""
    persons = _place_to_persons(place_id)
    if exclude:
        persons = [p for p in persons if p["id"] != exclude]

    return JSONResponse(
        content={"placeId": place_id, "persons": persons},
        headers={"Cache-Control": "max-age=300"},
    )
