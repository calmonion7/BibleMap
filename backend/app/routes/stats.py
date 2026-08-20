"""GET /stats — 그래프 집계 통계 대시보드(task#248 S1).

성경 개요에서 진입하는 가벼운 통계 뷰용 엔드포인트. 저작 데이터 신설 없이 그래프에서
산출 가능한 집계만 제공한다. 전체 응답은 사용자 입력 없는 전역 집계라 lru_cache(maxsize=1)로
1회 계산 후 재사용(데이터 변경 시 API 재시작 필요 — 다른 집계 라우트와 동일 관행)."""
import functools
import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ..db import get_driver
from ..curated import CURATED, id_to_slug, person_events, slug_to_id
from .journey import _fetch_place_coords

logger = logging.getLogger(__name__)

router = APIRouter()

TOP_PERSONS_LIMIT = 10

# 시대 경계(연도, BC=음수) — frontend/src/TimelineView.jsx의 ERA_BANDS와 동일해야 한다.
# 공유 설정이 없어 수동 복제: 프론트 경계 변경 시 이 목록도 함께 갱신할 것.
ERA_BANDS = [
    ("원시사", float("-inf")),
    ("족장", -2166),
    ("출애굽·정복", -1876),
    ("사사", -1375),
    ("왕국", -1050),
    ("선지자", -930),
    ("포로", -586),
    ("신약", -5),
]


def _era_of(year: float) -> str:
    era = ERA_BANDS[0][0]
    for name, frm in ERA_BANDS:
        if year >= frm:
            era = name
    return era


def _fetch_totals(session) -> dict:
    record = session.run(
        """
        MATCH (p:Person) WITH count(p) AS persons
        MATCH (e:Event) WITH persons, count(e) AS events
        MATCH (pl:Place) WITH persons, events, count(pl) AS places
        MATCH (b:Book) WITH persons, events, places, count(b) AS books
        RETURN persons, events, places, books
        """
    ).single()
    return {
        "persons": record["persons"],
        "events": record["events"],
        "places": record["places"],
        "books": record["books"],
    }


def _fetch_top_persons(session) -> list[dict]:
    """참여 사건 수(HAS_PARTICIPANT) 기준 상위 인물. God은 거의 모든 사건에 걸쳐
    순위를 무의미하게 만들어 기존 관행(nodes.py topPersons·persons.py connections)대로 제외."""
    slug_by_id = id_to_slug()
    result = session.run(
        f"""
        MATCH (e:Event)-[:HAS_PARTICIPANT]->(p:Person)
        WHERE p.theographic_id IS NOT NULL AND p.name <> 'God'
        WITH p, count(DISTINCT e) AS cnt
        ORDER BY cnt DESC LIMIT {TOP_PERSONS_LIMIT}
        RETURN p.theographic_id AS id, p.name AS name, p.nameKo AS nameKo, cnt AS count
        """
    )
    return [
        {
            "id": r["id"],
            "nameKo": r["nameKo"] or r["name"],
            "count": r["count"],
            "slug": slug_by_id.get(r["id"]),
        }
        for r in result
    ]


def _fetch_era_distribution(session) -> list[dict]:
    result = session.run("MATCH (e:Event) WHERE e.sortKey IS NOT NULL RETURN e.sortKey AS sortKey")
    counts = {name: 0 for name, _ in ERA_BANDS}
    for r in result:
        counts[_era_of(r["sortKey"])] += 1
    return [{"era": name, "count": counts[name]} for name, _ in ERA_BANDS]


def _fetch_books(session) -> list[dict]:
    return session.run(
        """
        MATCH (b:Book)
        RETURN b.theographic_id AS bookId, b.nameKo AS nameKo, b.testament AS testament,
               b.bookOrder AS bookOrder, b.chapterCount AS chapterCount
        ORDER BY b.bookOrder ASC
        """
    ).data()


def _compute_longest_journeys() -> list[dict]:
    """큐레이션 35인의 정차지 수(journey.py와 동일한 occursAt[0] 좌표 보유 기준) 내림차순.

    CURATED 정의 순서로 순회한다(slug_to_id()·id_to_slug()는 curated_index()의 시대/등장시점
    정렬 순서를 따라 이 함수의 stopCount 동률 안정정렬 타이브레이크가 바뀌므로 쓰지 않음)."""
    slug_id_map = slug_to_id()
    results = []
    for slug in CURATED:
        person_id = slug_id_map.get(slug)
        if person_id is None:
            continue
        events = person_events(slug)
        place_ids = list({e["occursAt"][0] for e in events if e.get("occursAt")})
        coords = _fetch_place_coords(place_ids)
        stop_count = sum(
            1 for e in events
            if e.get("occursAt")
            and coords.get(e["occursAt"][0], {}).get("lng") is not None
            and coords.get(e["occursAt"][0], {}).get("lat") is not None
        )
        results.append({"id": person_id, "nameKo": CURATED[slug]["nameKo"], "stopCount": stop_count})
    results.sort(key=lambda r: -r["stopCount"])
    return results


@functools.lru_cache(maxsize=1)
def _compute_stats() -> dict:
    driver = get_driver()
    with driver.session() as session:
        totals = _fetch_totals(session)
        top_persons = _fetch_top_persons(session)
        era_distribution = _fetch_era_distribution(session)
        books = _fetch_books(session)
    return {
        "totals": totals,
        "topPersons": top_persons,
        "longestJourneys": _compute_longest_journeys(),
        "eraDistribution": era_distribution,
        "books": books,
    }


@router.get("/stats")
def get_stats():
    """헤드라인 총계 + 최다 등장 인물 + 최장 여정 + 시대별 사건 분포 + 책별 장 수."""
    return JSONResponse(content=_compute_stats(), headers={"Cache-Control": "max-age=300"})
