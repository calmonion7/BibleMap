"""큐레이션된 13인 인물 목록 엔드포인트.

person_events/*.json 파일에서 eventCount 와 theographic_id(첫 번째 participants)를
정적으로 읽어 반환한다. Neo4j 조회 없이 파일만으로 충분히 결정적이므로 단순성 우선."""
import functools
import json
import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ..db import get_driver
from ..overlays import _resolve, curated_person_id

logger = logging.getLogger(__name__)

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
    "job": "족장",
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
    "job": "욥",
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

        person_id = curated_person_id(events)
        if person_id is None:
            logger.warning("[Persons] curated: %s — events[0].participants 비어 있음, 건너뜀", slug)
            continue
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


@functools.lru_cache(maxsize=1)
def _load_keypeople_verses() -> dict:
    """data/keypeople_verses/people.json (무id 이름 키 카드) 로드. 없으면 빈 맵. ADR-0017."""
    path = _resolve("keypeople_verses/people.json")
    if path is None:
        logger.warning("[Persons] keypeople_verses/people.json 없음 — 빈 맵 반환")
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@functools.lru_cache(maxsize=1)
def _load_person_context() -> dict:
    """data/person_context/people.json (by-id 인물 카드, 본문 프리베이크) 로드. 없으면 빈 맵."""
    path = _resolve("person_context/people.json")
    if path is None:
        logger.warning("[Persons] person_context/people.json 없음 — 빈 맵 반환")
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@functools.lru_cache(maxsize=1)
def _load_keypeople_identity() -> dict:
    """data/keypeople/identity.json ((책,이름)→{kind, id?}) 로드. 없으면 빈 맵. ADR-0018."""
    path = _resolve("keypeople/identity.json")
    if path is None:
        logger.warning("[Persons] keypeople/identity.json 없음 — 빈 맵 반환")
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@router.get("/keypeople-cards")
def get_keypeople_cards():
    """책별 keyPeople 문자열 → 완성 카드(identity 조인). ADR-0018.
    { book_tid: { name: {kind, journeyId, role, intro, verses} } }
    person=person_context(by-id)+큐레이션 여정, noid=keypeople_verses(by-name), deity/미저작=평문(생략)."""
    identity = _load_keypeople_identity()
    pc = _load_person_context()
    kv = _load_keypeople_verses()
    curated_ids = {p["id"] for p in _build_list()}
    out: dict = {}
    for book, mp in identity.items():
        cards = {}
        for name, e in mp.items():
            kind = e.get("kind")
            if kind == "person":
                pid = e.get("id")
                card = pc.get(pid)
                is_curated = pid in curated_ids
                if not card and not is_curated:
                    continue  # 카드도 여정도 없음 → 평문
                cards[name] = {
                    "kind": "person",
                    "journeyId": pid if is_curated else None,
                    "role": (card or {}).get("role"),
                    "intro": (card or {}).get("intro"),
                    "verses": (card or {}).get("verses", []),
                }
            elif kind == "noid":
                card = kv.get(name)
                if not card:
                    continue  # 예: 가이아(지시대상 없음) → 평문
                cards[name] = {
                    "kind": "noid",
                    "journeyId": None,
                    "role": card.get("role"),
                    "intro": card.get("intro"),
                    "verses": card.get("verses", []),
                }
            # kind == 'deity' → 평문(생략)
        if cards:
            out[book] = cards
    return JSONResponse(content=out, headers={"Cache-Control": "max-age=300"})


@functools.lru_cache(maxsize=256)
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


@functools.lru_cache(maxsize=1)
def _load_relations() -> list[dict]:
    """인물 관계 pair 카탈로그(CONTEXT '인물 관계'). 런타임 오버레이 파일.
    각 phase에는 valence·label·verse·approxYear + 빌드타임 프리베이크된 verseTextKo/En이 담긴다."""
    path = _resolve("person_relations/relations.json")
    if path is None:
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f).get("relations", [])


@functools.lru_cache(maxsize=256)
def _build_relations(node_id: str) -> dict:
    """subject(node_id)가 낀 관계 pair만 필터해 상대 endpoint와 시간순 phases를 반환.
    상대에 slug가 있고 34인이면 withId를 해결(여정 점프 가능), 아니면 null. phases는 그대로 통과.
    note는 상대 endpoint의 role(각 endpoint 관점 역할, 예: 아벨 상세에서 아담=아버지)을 우선하고, 없으면 pair note로 폴백."""
    curated = _build_list()
    id_to_slug = {p["id"]: p["slug"] for p in curated}
    slug_to_id = {p["slug"]: p["id"] for p in curated}
    me_slug = id_to_slug.get(node_id)
    if me_slug is None:
        return {"relations": []}

    relations = []
    for pair in _load_relations():
        endpoints = pair.get("endpoints", [])
        if me_slug not in [ep.get("slug") for ep in endpoints]:
            continue
        other = next((ep for ep in endpoints if ep.get("slug") != me_slug), None)
        if other is None:
            continue
        relations.append(
            {
                "type": pair.get("type"),
                "note": other.get("role") or pair.get("note"),
                "withNameKo": other.get("nameKo"),
                "withId": slug_to_id.get(other["slug"]) if other.get("slug") else None,
                "withSlug": other.get("slug"),  # 인장 선화 렌더용(큐레이션 상대만 존재)
                "phases": pair.get("phases", []),
            }
        )
    return {"relations": relations}


@router.get("/person/{node_id}/relations")
def get_person_relations(node_id: str):
    """인물 관계 뷰 데이터(valence·시간순 국면·근거 구절 본문).
    관계 카탈로그에 없는 인물은 빈 배열 반환."""
    return JSONResponse(
        content=_build_relations(node_id),
        headers={"Cache-Control": "max-age=300"},
    )
