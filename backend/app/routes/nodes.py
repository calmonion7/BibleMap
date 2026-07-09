import logging

from fastapi import APIRouter, HTTPException
from ..db import get_driver

logger = logging.getLogger(__name__)

router = APIRouter()

MAX_NEIGHBORS_PER_TYPE = 30
NODE_NEIGHBOR_LIMIT = 50

@router.get("/person/{node_id}/event-ids")
def get_person_event_ids(node_id: str):
    driver = get_driver()
    with driver.session() as session:
        result = session.run(
            "MATCH (e:Event)-[:HAS_PARTICIPANT]->(n:Person {theographic_id: $id}) RETURN e.theographic_id AS id",
            id=node_id
        )
        return {"eventIds": [r["id"] for r in result]}


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

        # 이웃 조회 + 총수 — 단일 쿼리로 2 → 1 왕복
        neighbors_result = session.run(
            f"MATCH (n {{theographic_id: $id}})-[r]-(m) "
            f"WITH count(m) AS total, collect({{m: m, rel: type(r), mlabels: labels(m)}})[0..{NODE_NEIGHBOR_LIMIT}] AS rows "
            f"RETURN rows, total",
            id=node_id
        )
        nr_record = neighbors_result.single()
        rows = nr_record["rows"]
        neighbor_total = nr_record["total"]

        neighbors = []
        for row in rows:
            m = row["m"]
            m_props = dict(m)
            m_name_ko = m_props.get("nameKo")
            m_name = m_props.get("name") or m_props.get("title", "")
            neighbors.append({
                "id": m_props.get("theographic_id", ""),
                "label": row["mlabels"][0] if row["mlabels"] else "Unknown",
                "name": m_name,
                "nameKo": m_name_ko if m_name_ko else m_name,
                "nameKoMissing": m_name_ko is None,
                "relation": row["rel"],
            })

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
                WHERE p.theographic_id IS NOT NULL AND p.name <> 'God'
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
            # startDate는 "-4003"/"-1451-01"/"30" 형식 혼재 문자열 — 사전순 정렬 시
            # BC 연도가 역전되므로(예: -1451 < -4003) 연도를 파싱해 오름차순 상위 10개만.
            def _year(s):
                if not s:
                    return None
                neg = s.startswith("-")
                body = s[1:] if neg else s
                try:
                    y = int(body.split("-")[0])
                except ValueError:
                    return None
                return -y if neg else y
            top_events.sort(key=lambda ev: (_year(ev["startDate"]) is None, _year(ev["startDate"]) or 0))
            top_events = top_events[:10]

        # Person traits JSON 파싱
        if label_val == "Person" and "traits" in clean_props:
            import json as _json
            try:
                clean_props["traits"] = _json.loads(clean_props["traits"])
            except Exception as e:
                logger.warning("[Nodes] Person traits 파싱 실패 — 빈 목록 폴백 (%s): %s", node_id, e)
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
