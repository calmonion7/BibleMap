from fastapi import APIRouter, HTTPException
from ..db import get_driver

router = APIRouter()

MAX_NEIGHBORS_PER_TYPE = 30
NODE_NEIGHBOR_LIMIT = 50

@router.get("/node/{node_id}/places")
def get_node_places(node_id: str):
    driver = get_driver()
    with driver.session() as session:
        result = session.run(
            "MATCH (n {theographic_id: $id}) RETURN labels(n) AS labels",
            id=node_id
        )
        record = result.single()
        if not record:
            raise HTTPException(status_code=404, detail="Node not found")
        labels = record["labels"]
        label = labels[0] if labels else "Unknown"

        if label == "Person":
            places_result = session.run(
                """
                MATCH (e:Event)-[:HAS_PARTICIPANT]->(n {theographic_id: $id})
                MATCH (e)-[:OCCURS_AT]->(p:Place)
                WHERE p.latitude IS NOT NULL AND p.longitude IS NOT NULL
                RETURN p, false AS isPrimary
                """,
                id=node_id
            )
        elif label == "Event":
            places_result = session.run(
                """
                MATCH (n {theographic_id: $id})-[:OCCURS_AT]->(p:Place)
                WHERE p.latitude IS NOT NULL AND p.longitude IS NOT NULL
                RETURN p, true AS isPrimary
                """,
                id=node_id
            )
        elif label == "PeopleGroup":
            places_result = session.run(
                """
                MATCH (n:PeopleGroup {theographic_id: $id})<-[:MEMBER_OF]-(person:Person)
                MATCH (e:Event)-[:HAS_PARTICIPANT]->(person)
                MATCH (e)-[:OCCURS_AT]->(p:Place)
                WHERE p.latitude IS NOT NULL AND p.longitude IS NOT NULL
                RETURN p, false AS isPrimary
                """,
                id=node_id
            )
        elif label == "Book":
            places_result = session.run(
                """
                MATCH (n:Book {theographic_id: $id})-[:CONTAINS_BOOK]->(e:Event)
                MATCH (e)-[:OCCURS_AT]->(p:Place)
                WHERE p.latitude IS NOT NULL AND p.longitude IS NOT NULL
                RETURN p, false AS isPrimary
                """,
                id=node_id
            )
        else:
            places_result = session.run(
                """
                MATCH (p:Place {theographic_id: $id})
                WHERE p.latitude IS NOT NULL AND p.longitude IS NOT NULL
                RETURN p, true AS isPrimary
                """,
                id=node_id
            )

        places = []
        seen = set()
        for record in places_result:
            p = record["p"]
            props = dict(p)
            tid = props.get("theographic_id", "")
            if tid in seen:
                continue
            seen.add(tid)
            name = props.get("name", "")
            name_ko = props.get("nameKo")
            try:
                lat = float(props.get("latitude", 0))
                lng = float(props.get("longitude", 0))
            except (TypeError, ValueError):
                continue
            places.append({
                "id": tid,
                "name": name,
                "nameKo": name_ko if name_ko else name,
                "lat": lat,
                "lng": lng,
                "isPrimary": record["isPrimary"],
            })
        return {"label": label, "places": places}


@router.get("/node/{node_id}/neighbors/grouped")
def get_node_neighbors_grouped(node_id: str):
    driver = get_driver()
    with driver.session() as session:
        result = session.run(
            "MATCH (n {theographic_id: $id})-[r]-(m) RETURN m, type(r) AS rel, labels(m) AS mlabels",
            id=node_id
        )

        grouped = {"Person": [], "Event": [], "PeopleGroup": [], "Place": []}
        counts = {k: 0 for k in grouped}

        for nr in result:
            m_props = dict(nr["m"])
            mlabels = nr["mlabels"]
            label = mlabels[0] if mlabels else None
            if label not in grouped:
                continue
            if counts[label] >= MAX_NEIGHBORS_PER_TYPE:
                continue
            m_name = m_props.get("name") or m_props.get("title", "")
            m_name_ko = m_props.get("nameKo")
            grouped[label].append({
                "id": m_props.get("theographic_id", ""),
                "name": m_name,
                "nameKo": m_name_ko if m_name_ko is not None else m_name,
                "nameKoMissing": m_name_ko is None,
                "relation": nr["rel"],
            })
            counts[label] += 1

        return grouped


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
            f"MATCH (n {{theographic_id: $id}})-[r]-(m) RETURN m, type(r) AS rel, labels(m) AS mlabels LIMIT {NODE_NEIGHBOR_LIMIT}",
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

        # 전체 이웃 수(LIMIT 전) — 잘림 신호용. neighbors는 NODE_NEIGHBOR_LIMIT으로 잘릴 수 있다.
        total_result = session.run(
            "MATCH (n {theographic_id: $id})-[r]-(m) RETURN count(m) AS total",
            id=node_id
        )
        neighbor_total = total_result.single()["total"]

        # properties: name/nameKo/theographic_id/aliasesKo 제외
        exclude = {"name", "nameKo", "theographic_id", "aliasesKo"}
        clean_props = {k: v for k, v in props.items() if k not in exclude}

        label_val = labels[0] if labels else "Unknown"

        # Book 전용 추가 필드
        top_persons = []
        top_events = []
        if label_val == "Book":
            persons_result = session.run(
                """
                MATCH (b:Book {theographic_id: $id})-[:CONTAINS_BOOK]->(e:Event)
                MATCH (e)-[:HAS_PARTICIPANT]->(p:Person)
                WHERE p.theographic_id IS NOT NULL
                WITH p, count(e) AS cnt
                ORDER BY cnt DESC LIMIT 10
                RETURN p.theographic_id AS id, p.name AS name, p.nameKo AS nameKo
                """,
                id=node_id,
            )
            for r in persons_result:
                top_persons.append({
                    "id": r["id"],
                    "name": r["name"],
                    "nameKo": r["nameKo"] or r["name"],
                })

            events_result = session.run(
                """
                MATCH (b:Book {theographic_id: $id})-[:CONTAINS_BOOK]->(e:Event)
                WHERE e.theographic_id IS NOT NULL
                RETURN e.theographic_id AS id, e.title AS name, e.nameKo AS nameKo,
                       e.startDate AS startDate
                ORDER BY e.startDate LIMIT 10
                """,
                id=node_id,
            )
            for r in events_result:
                top_events.append({
                    "id": r["id"],
                    "name": r["name"],
                    "nameKo": r["nameKo"] or r["name"],
                    "startDate": r["startDate"],
                })

        # Person traits JSON 파싱
        if label_val == "Person" and "traits" in clean_props:
            import json as _json
            try:
                clean_props["traits"] = _json.loads(clean_props["traits"])
            except Exception:
                clean_props["traits"] = []

        response = {
            "id": node_id_val,
            "label": label_val,
            "name": name,
            "nameKo": name_ko if name_ko else name,
            "nameKoMissing": name_ko is None,
            "properties": clean_props,
            "neighbors": neighbors,
            "neighborTotal": neighbor_total,
        }
        if label_val == "Book":
            response["topPersons"] = top_persons
            response["topEvents"] = top_events
        return response
