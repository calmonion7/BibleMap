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
            WHERE (n.nameKo CONTAINS $q OR n.name CONTAINS $q)
            AND n.theographic_id IS NOT NULL
            RETURN n, labels(n) AS labels
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
