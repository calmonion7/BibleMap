from fastapi import APIRouter, Query
from ..db import get_driver
from ..verse_search import search_verses

router = APIRouter()

SEARCH_LIMIT = 20
# 절 본문 검색은 31k절 전수 스캔이라 1자 질의는 사실상 전체 매칭이 된다 — 2자 미만은 절 검색을 건너뛴다.
MIN_VERSE_QUERY = 2

@router.get("/search")
def search(q: str = Query("")):
    """통합 검색(task#267) — 노드 이름 + 절 본문을 한 응답으로 반환한다.

    절 항목은 화면 이동에 필요한 `verseId`·`bookId`·`chapter`를 실어, 결과 클릭으로 리더의
    해당 장을 열고 그 절을 강조할 수 있게 한다.
    """
    q = q.strip()
    if not q:
        return {"nodes": [], "verses": []}
    driver = get_driver()
    with driver.session() as session:
        result = session.run(
            f"""
            MATCH (n)
            WHERE (n.nameKo CONTAINS $q OR toLower(n.name) CONTAINS toLower($q))
            AND n.theographic_id IS NOT NULL
            AND (n.status IS NULL OR n.status <> 'wip')
            WITH n, labels(n) AS labels,
              CASE
                WHEN n.nameKo = $q OR toLower(n.name) = toLower($q) THEN 0
                WHEN n.nameKo STARTS WITH $q OR toLower(n.name) STARTS WITH toLower($q) THEN 1
                ELSE 2
              END AS rank
            RETURN n, labels
            ORDER BY rank, n.nameKo
            LIMIT {SEARCH_LIMIT}
            """,
            q=q
        )
        items = []
        for record in result:
            props = dict(record["n"])
            labels = record["labels"]
            name = props.get("name") or props.get("title", "")
            items.append({
                "id": props.get("theographic_id", ""),
                "label": labels[0] if labels else "Unknown",
                "name": name,
                "nameKo": props.get("nameKo") or name,
            })

    verses = []
    if len(q) >= MIN_VERSE_QUERY:
        _, matched = search_verses(q, match_en=True)
        verses = list(matched[:SEARCH_LIMIT])
    return {"nodes": items, "verses": verses}
