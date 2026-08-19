"""통사 연표 엔드포인트(task#271) — 시대 밴드 + 전 성경 사건 + 큐레이션 인물 활동 구간을 한 응답으로.

세 재료 모두 **기존 출처를 재사용**한다(신규 데이터 저작 0):
  - 시대 밴드 : `stats.ERA_BANDS` (백엔드 정본 — 새 복제를 만들지 않는다)
  - 사건      : `events._compute_events()` (`/events`와 같은 목록)
  - 인물 구간 : `person_events/<slug>.json`의 `sortKey` min/max (persons.py가 min을 이미 앵커로 씀)
"""
import functools
import json

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ..overlays import _resolve, curated_person_id
from .events import _compute_events
from .persons import _ERA, _ERA_ORDER, _NAME_KO
from .stats import ERA_BANDS, _era_of

router = APIRouter()


def _person_spans() -> list[dict]:
    """큐레이션 인물의 활동 구간 — (slug, nameKo, era, startYear, endYear).

    persons.py `_build_list`와 **같은 정렬 규칙**(시대 순 → 최초 등장 → slug)을 써서
    `/persons/curated` 순서와 모순되지 않게 한다.
    """
    spans = []
    for slug in sorted(_ERA.keys()):
        path = _resolve(f"person_events/{slug}.json")
        if path is None:
            continue
        with open(path, encoding="utf-8") as f:
            events = json.load(f)
        keys = [e["sortKey"] for e in events if e.get("sortKey") is not None]
        if not keys:
            continue
        person_id = curated_person_id(events)
        if person_id is None:
            continue
        spans.append({
            "id": person_id,
            "slug": slug,
            "nameKo": _NAME_KO[slug],
            "era": _ERA[slug],
            "startYear": min(keys),
            "endYear": max(keys),
            "eventCount": len(events),
        })
    spans.sort(key=lambda p: (_ERA_ORDER.index(p["era"]), p["startYear"], p["slug"]))
    return spans


@functools.lru_cache(maxsize=1)
def _canon_payload() -> dict:
    bands = []
    for i, (name, frm) in enumerate(ERA_BANDS):
        to = ERA_BANDS[i + 1][1] if i + 1 < len(ERA_BANDS) else None
        bands.append({
            "name": name,
            # 원시사는 -inf — JSON에 그대로 실을 수 없어 null로 보내고 프론트가 축 왼쪽 끝으로 처리한다.
            "from": None if frm == float("-inf") else frm,
            "to": to,
        })

    events = [
        {
            "id": e["id"],
            "nameKo": e["nameKo"] or e["title"],
            "year": e["sortKey"],
            "yearLabel": e["yearLabel"],
            "era": _era_of(e["sortKey"]),
            "bookNameKo": (e["books"][0]["nameKo"] if e["books"] else None),
        }
        for e in _compute_events()
    ]
    return {"bands": bands, "events": events, "persons": _person_spans()}


@router.get("/timeline/canon")
def get_canon_timeline():
    """통사 연표 — 시대 밴드·사건 요약·인물 활동 구간을 한 번에. 1회 계산 후 캐시."""
    return JSONResponse(content=_canon_payload(), headers={"Cache-Control": "max-age=300"})
