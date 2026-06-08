from fastapi import APIRouter, HTTPException
from ..db import get_driver

router = APIRouter()

@router.get("/node/{node_id}")
def get_node(node_id: str):
    driver = get_driver()
    with driver.session() as session:
        # 노드 조회
        result = session.run(
            "MATCH (n {theographic_id: $id}) RETURN n, labels(n) AS labels",
            id=node_id
        )
        record = result.single()
        if not record:
            raise HTTPException(status_code=404, detail="Node not found")

        node = record["n"]
        labels = record["labels"]
        props = dict(node)

        node_id_val = props.get("theographic_id", node_id)
        name = props.get("name") or props.get("title", "")
        name_ko = props.get("nameKo")

        # 이웃 조회
        neighbors_result = session.run(
            "MATCH (n {theographic_id: $id})-[r]-(m) RETURN m, type(r) AS rel, labels(m) AS mlabels LIMIT 50",
            id=node_id
        )

        neighbors = []
        for nr in neighbors_result:
            m = nr["m"]
            m_props = dict(m)
            m_name_ko = m_props.get("nameKo")
            m_name = m_props.get("name") or m_props.get("title", "")
            neighbors.append({
                "id": m_props.get("theographic_id", ""),
                "label": nr["mlabels"][0] if nr["mlabels"] else "Unknown",
                "name": m_name,
                "nameKo": m_name_ko if m_name_ko else m_name,
                "nameKoMissing": m_name_ko is None,
                "relation": nr["rel"],
            })

        # properties: name/nameKo/theographic_id/aliasesKo 제외
        exclude = {"name", "nameKo", "theographic_id", "aliasesKo"}
        clean_props = {k: v for k, v in props.items() if k not in exclude}

        return {
            "id": node_id_val,
            "label": labels[0] if labels else "Unknown",
            "name": name,
            "nameKo": name_ko if name_ko else name,
            "nameKoMissing": name_ko is None,
            "properties": clean_props,
            "neighbors": neighbors,
        }
