from fastapi import APIRouter, Query
from ..db import get_driver

router = APIRouter()

SEARCH_LIMIT = 20

@router.get("/search")
def search(q: str = Query("")):
    if not q.strip():
        return []
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
        return items
