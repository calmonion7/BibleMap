"""큐레이션된 13인 인물 목록 엔드포인트.

person_events/*.json 파일에서 eventCount 와 theographic_id(첫 번째 participants)를
정적으로 읽어 반환한다. Neo4j 조회 없이 파일만으로 충분히 결정적이므로 단순성 우선."""
import functools
import json
import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ..db import get_driver
from ..overlays import _resolve

router = APIRouter()

# slug → era 고정 매핑
_ERA: dict[str, str] = {
    "adam": "원시사",
    "noah": "원시사",
    "cain": "원시사",
    "abel": "원시사",
    "seth": "원시사",
    "enoch": "원시사",
    "abraham": "족장",
    "isaac": "족장",
    "jacob": "족장",
    "joseph": "족장",
    "moses": "출애굽·정복",
    "joshua": "출애굽·정복",
    "gideon": "사사",
    "deborah": "사사",
    "jephthah": "사사",
    "samson": "사사",
    "ruth": "사사",
    "saul": "왕국",
    "samuel": "왕국",
    "david": "왕국",
    "solomon": "왕국",
    "elijah": "선지자",
    "elisha": "선지자",
    "jonah": "선지자",
    "isaiah": "선지자",
    "daniel": "포로",
    "esther": "포로",
    "nehemiah": "포로",
    "john_the_baptist": "신약",
    "jesus": "신약",
    "mary": "신약",
    "paul": "신약",
    "peter": "신약",
    "john_the_apostle": "신약",
}

# slug → 한글 이름
_NAME_KO: dict[str, str] = {
    "adam": "아담",
    "noah": "노아",
    "cain": "가인",
    "abel": "아벨",
    "seth": "셋",
    "enoch": "에녹",
    "abraham": "아브라함",
    "isaac": "이삭",
    "jacob": "야곱",
    "joseph": "요셉",
    "moses": "모세",
    "joshua": "여호수아",
    "gideon": "기드온",
    "deborah": "드보라",
    "jephthah": "입다",
    "samson": "삼손",
    "ruth": "룻",
    "saul": "사울",
    "samuel": "사무엘",
    "david": "다윗",
    "solomon": "솔로몬",
    "elijah": "엘리야",
    "elisha": "엘리사",
    "jonah": "요나",
    "isaiah": "이사야",
    "daniel": "다니엘",
    "esther": "에스더",
    "nehemiah": "느헤미야",
    "john_the_baptist": "세례 요한",
    "jesus": "예수",
    "mary": "마리아",
    "paul": "바울",
    "peter": "베드로",
    "john_the_apostle": "사도 요한",
}

# era 표시 순서
_ERA_ORDER = ["원시사", "족장", "출애굽·정복", "사사", "왕국", "선지자", "포로", "신약"]


@functools.lru_cache(maxsize=1)
def _build_list() -> list[dict]:
    result = []
    for slug in sorted(_ERA.keys()):
        path = _resolve(f"person_events/{slug}.json")
        if path is None:
            continue
        with open(path, encoding="utf-8") as f:
            events = json.load(f)

        if not events or not events[0].get("participants"):
            logging.warning("persons/curated: %s — events[0].participants 비어 있음, 건너뜀", slug)
            continue
        # theographic_id: 파일 내 모든 이벤트의 첫 번째 participant가 동일인임을 검증 완료
        person_id = events[0]["participants"][0]
        result.append(
            {
                "id": person_id,
                "slug": slug,
                "nameKo": _NAME_KO[slug],
                "era": _ERA[slug],
                "eventCount": len(events),
                # 정렬 전용: 여정 최초 등장 시점(최소 sortKey). 응답 전 제거.
                "_anchor": min(e["sortKey"] for e in events),
            }
        )

    # 시대 그룹 내에서 최초 등장 시점(anchor) 시간순, 동시각은 slug tie-break
    result.sort(key=lambda p: (_ERA_ORDER.index(p["era"]), p["_anchor"], p["slug"]))
    for p in result:
        del p["_anchor"]
    return result


@router.get("/persons/curated")
def get_curated_persons():
    """활동범위가 그려지는 큐레이션된 13인 목록.
    각 항목: { id, slug, nameKo, era, eventCount }"""
    return JSONResponse(
        content=_build_list(),
        headers={"Cache-Control": "max-age=300"},
    )


@functools.lru_cache(maxsize=None)
def _build_connections(node_id: str) -> dict:
    """큐레이션 인물의 연결 두 축(CONTEXT '인물 연결'). 큐레이션 인물로 한정.
    - coParticipants: 같은 Event에 HAS_PARTICIPANT로 함께 등장(2-hop), 큐레이션 교집합·self·God 제외, 공유 사건 수 desc.
    - contemporaries: 같은 era 큐레이션 인물, self·coParticipants 제외(_build_list 정렬 순 유지)."""
    curated = _build_list()
    by_id = {p["id"]: p for p in curated}
    me = by_id.get(node_id)
    if me is None:
        return {"coParticipants": [], "contemporaries": []}

    driver = get_driver()
    with driver.session() as session:
        result = session.run(
            """
            MATCH (e:Event)-[:HAS_PARTICIPANT]->(:Person {theographic_id: $id})
            MATCH (e)-[:HAS_PARTICIPANT]->(p2:Person)
            WHERE p2.theographic_id <> $id AND p2.name <> 'God'
            RETURN p2.theographic_id AS id, count(DISTINCT e) AS shared
            ORDER BY shared DESC
            """,
            id=node_id,
        )
        co_raw = [(r["id"], r["shared"]) for r in result]

    co_participants = []
    co_ids = set()
    for pid, shared in co_raw:
        p = by_id.get(pid)
        if p is None:
            continue
        co_participants.append({"id": pid, "nameKo": p["nameKo"], "shared": shared})
        co_ids.add(pid)

    contemporaries = [
        {"id": p["id"], "nameKo": p["nameKo"]}
        for p in curated
        if p["era"] == me["era"] and p["id"] != node_id and p["id"] not in co_ids
    ]
    return {"coParticipants": co_participants, "contemporaries": contemporaries}


@router.get("/person/{node_id}/connections")
def get_person_connections(node_id: str):
    """큐레이션 인물 상세 시트의 '함께 등장한 인물'·'동시대 인물' 섹션 데이터.
    큐레이션이 아닌 id는 두 배열 모두 빈 채로 반환."""
    return JSONResponse(
        content=_build_connections(node_id),
        headers={"Cache-Control": "max-age=300"},
    )
