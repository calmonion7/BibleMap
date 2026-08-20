"""큐레이션 인물 색인의 정본 — slug↔id 해석기, 시대 순서, person_events 캐시 로더.

overlays.py와 같은 층(라우트를 import하지 않는다 — 순환 import 차단).
소비처: persons·journey·places·timeline·tours·stats·reliance·family (task#278)."""
import functools
import json
import logging

from .overlays import _resolve, curated_person_id

logger = logging.getLogger(__name__)

# slug → {nameKo, era} 고정 매핑 (큐레이션 35)
CURATED: dict[str, dict] = {
    "adam": {"nameKo": "아담", "era": "원시사"},
    "noah": {"nameKo": "노아", "era": "원시사"},
    "cain": {"nameKo": "가인", "era": "원시사"},
    "abel": {"nameKo": "아벨", "era": "원시사"},
    "seth": {"nameKo": "셋", "era": "원시사"},
    "enoch": {"nameKo": "에녹", "era": "원시사"},
    "abraham": {"nameKo": "아브라함", "era": "족장"},
    "isaac": {"nameKo": "이삭", "era": "족장"},
    "jacob": {"nameKo": "야곱", "era": "족장"},
    "joseph": {"nameKo": "요셉", "era": "족장"},
    "job": {"nameKo": "욥", "era": "족장"},
    "moses": {"nameKo": "모세", "era": "출애굽·정복"},
    "joshua": {"nameKo": "여호수아", "era": "출애굽·정복"},
    "gideon": {"nameKo": "기드온", "era": "사사"},
    "deborah": {"nameKo": "드보라", "era": "사사"},
    "jephthah": {"nameKo": "입다", "era": "사사"},
    "samson": {"nameKo": "삼손", "era": "사사"},
    "ruth": {"nameKo": "룻", "era": "사사"},
    "saul": {"nameKo": "사울", "era": "왕국"},
    "samuel": {"nameKo": "사무엘", "era": "왕국"},
    "david": {"nameKo": "다윗", "era": "왕국"},
    "solomon": {"nameKo": "솔로몬", "era": "왕국"},
    "elijah": {"nameKo": "엘리야", "era": "선지자"},
    "elisha": {"nameKo": "엘리사", "era": "선지자"},
    "jonah": {"nameKo": "요나", "era": "선지자"},
    "isaiah": {"nameKo": "이사야", "era": "선지자"},
    "daniel": {"nameKo": "다니엘", "era": "포로"},
    "esther": {"nameKo": "에스더", "era": "포로"},
    "nehemiah": {"nameKo": "느헤미야", "era": "포로"},
    "john_the_baptist": {"nameKo": "세례 요한", "era": "신약"},
    "jesus": {"nameKo": "예수", "era": "신약"},
    "mary": {"nameKo": "마리아", "era": "신약"},
    "paul": {"nameKo": "바울", "era": "신약"},
    "peter": {"nameKo": "베드로", "era": "신약"},
    "john_the_apostle": {"nameKo": "사도 요한", "era": "신약"},
}

# era 표시 순서
ERA_ORDER = ["원시사", "족장", "출애굽·정복", "사사", "왕국", "선지자", "포로", "신약"]


@functools.lru_cache(maxsize=64)
def person_events(slug: str) -> list[dict]:
    """person_events/<slug>.json을 sortKey 순으로 정렬해 반환. 없으면 빈 리스트."""
    path = _resolve(f"person_events/{slug}.json")
    if path is None:
        return []
    with open(path, encoding="utf-8") as f:
        events = json.load(f)
    return sorted(events, key=lambda e: e["sortKey"])


@functools.lru_cache(maxsize=1)
def curated_index() -> list[dict]:
    """큐레이션 35인 목록. 각 항목: {id, slug, nameKo, era, eventCount}.
    시대 그룹(ERA_ORDER) 내에서 여정 최초 등장 시점(min sortKey) 순, 동시각은 slug tie-break."""
    result = []
    for slug in sorted(CURATED.keys()):
        events = person_events(slug)
        if not events:
            continue

        person_id = curated_person_id(events)
        if person_id is None:
            logger.warning("[Curated] curated: %s — events[0].participants 비어 있음, 건너뜀", slug)
            continue
        result.append(
            {
                "id": person_id,
                "slug": slug,
                "nameKo": CURATED[slug]["nameKo"],
                "era": CURATED[slug]["era"],
                "eventCount": len(events),
                # 정렬 전용: 여정 최초 등장 시점(최소 sortKey). 응답 전 제거.
                "_anchor": min(e["sortKey"] for e in events),
            }
        )

    result.sort(key=lambda p: (ERA_ORDER.index(p["era"]), p["_anchor"], p["slug"]))
    for p in result:
        del p["_anchor"]
    return result


@functools.lru_cache(maxsize=1)
def id_to_slug() -> dict[str, str]:
    """theographic_id → slug (큐레이션 35)."""
    return {p["id"]: p["slug"] for p in curated_index()}


@functools.lru_cache(maxsize=1)
def slug_to_id() -> dict[str, str]:
    """slug → theographic_id (큐레이션 35)."""
    return {p["slug"]: p["id"] for p in curated_index()}


@functools.lru_cache(maxsize=1)
def seal_id_to_slug() -> dict[str, str]:
    """인장 조회용 id → slug. 큐레이션 35인(우선) + 비큐레이션 인장 보유 인물
    (person_slugs/seal_slugs.json, ADR-0025) = 50."""
    out = dict(id_to_slug())
    path = _resolve("person_slugs/seal_slugs.json")
    if path is not None:
        with open(path, encoding="utf-8") as f:
            seals = json.load(f)
        for slug, pid in seals.items():
            if slug != "note":
                out.setdefault(pid, slug)
    return out
