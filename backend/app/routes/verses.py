import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ..db import get_driver
from .. import overlays

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/verse/{verse_id}/persons")
def get_verse_persons(verse_id: str):
    """그 절(verseID = BBCCCVVV)에 등장/언급되는 인물 목록.

    구절↔인물 색인(overlays.verse_persons())에서 인물 rec id를 얻고, 우리 Neo4j에
    적재된 Person만 이름을 해석한다. 우리가 적재하지 않은 rec id는 id만 반환(무음 드롭 안 함).
    존재하지 않는 절은 빈 목록 폴백."""
    rec_ids = overlays.verse_persons().get(verse_id, [])
    if not rec_ids:
        return JSONResponse({"verseId": verse_id, "persons": []})

    driver = get_driver()
    resolved = {}
    with driver.session() as session:
        result = session.run(
            """
            MATCH (p:Person) WHERE p.theographic_id IN $ids
            RETURN p.theographic_id AS id, p.nameKo AS nameKo,
                   coalesce(p.displayTitle, p.name) AS name, p.slug AS slug
            """,
            ids=rec_ids,
        )
        for r in result:
            resolved[r["id"]] = {
                "id": r["id"],
                "nameKo": r["nameKo"],
                "name": r["name"],
                "slug": r["slug"],
            }

    persons = [resolved.get(rid, {"id": rid, "nameKo": None, "name": None, "slug": None}) for rid in rec_ids]
    return JSONResponse(
        {"verseId": verse_id, "persons": persons},
        headers={"Cache-Control": "max-age=300"},
    )
