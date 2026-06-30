"""큐레이션된 13인 인물 목록 엔드포인트.

person_events/*.json 파일에서 eventCount 와 theographic_id(첫 번째 participants)를
정적으로 읽어 반환한다. Neo4j 조회 없이 파일만으로 충분히 결정적이므로 단순성 우선."""
import functools
import json

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ..overlays import _resolve

router = APIRouter()

# slug → era 고정 매핑
_ERA: dict[str, str] = {
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
    "isaiah": "선지자",
    "john_the_baptist": "신약",
    "jesus": "신약",
    "mary": "신약",
    "paul": "신약",
    "peter": "신약",
    "john_the_apostle": "신약",
}

# slug → 한글 이름
_NAME_KO: dict[str, str] = {
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
    "isaiah": "이사야",
    "john_the_baptist": "세례 요한",
    "jesus": "예수",
    "mary": "마리아",
    "paul": "바울",
    "peter": "베드로",
    "john_the_apostle": "사도 요한",
}

# era 표시 순서
_ERA_ORDER = ["족장", "출애굽·정복", "사사", "왕국", "선지자", "신약"]


@functools.lru_cache(maxsize=1)
def _build_list() -> list[dict]:
    result = []
    for slug in sorted(_ERA.keys()):
        path = _resolve(f"person_events/{slug}.json")
        if path is None:
            continue
        with open(path, encoding="utf-8") as f:
            events = json.load(f)

        # theographic_id: 파일 내 모든 이벤트의 첫 번째 participant가 동일인임을 검증 완료
        person_id = events[0]["participants"][0]
        result.append(
            {
                "id": person_id,
                "slug": slug,
                "nameKo": _NAME_KO[slug],
                "era": _ERA[slug],
                "eventCount": len(events),
            }
        )

    result.sort(key=lambda p: (_ERA_ORDER.index(p["era"]), p["slug"]))
    return result


@router.get("/persons/curated")
def get_curated_persons():
    """활동범위가 그려지는 큐레이션된 13인 목록.
    각 항목: { id, slug, nameKo, era, eventCount }"""
    return JSONResponse(
        content=_build_list(),
        headers={"Cache-Control": "max-age=3600"},
    )
