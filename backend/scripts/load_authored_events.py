"""data/authored_events/events.json을 읽어 저작 사건을 Neo4j Event 노드로 멱등 적재한다.

각 사건은 MERGE (e:Event {theographic_id})로 만들고 authored=true 마킹한다.
occursAt의 Place·participants의 Person은 '노드가 실제로 존재할 때만' 관계를 건다(MERGE).
CONTAINS_BOOK은 만들지 않는다(ADR-0005: 서신서는 사건을 '기록'하지 않음)."""
import json
import os

from neo4j import GraphDatabase

NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD")
if not NEO4J_PASSWORD:
    raise RuntimeError("NEO4J_PASSWORD 환경변수가 설정되지 않았습니다")

SCRIPT_DIR = os.path.dirname(__file__)
EVENTS_PATH = os.path.normpath(
    os.path.join(SCRIPT_DIR, "..", "..", "data", "authored_events", "events.json")
)


def main():
    if not os.path.exists(EVENTS_PATH):
        raise FileNotFoundError(f"{EVENTS_PATH} not found")

    with open(EVENTS_PATH, encoding="utf-8") as f:
        events = json.load(f)

    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    with driver.session() as session:
        for ev in events:
            session.run(
                """
                MERGE (e:Event {theographic_id: $id})
                SET e.authored  = true,
                    e.title     = $title,
                    e.nameKo    = $nameKo,
                    e.startDate = $startDate,
                    e.sortKey   = $sortKey,
                    e.yearLabel = $yearLabel,
                    e.context   = $context
                """,
                id=ev["id"],
                title=ev.get("title", ""),
                nameKo=ev.get("nameKo"),
                startDate=ev.get("startDate", ""),
                sortKey=ev.get("sortKey", 0),
                yearLabel=ev.get("yearLabel"),
                context=ev.get("context"),
            )

            for place_id in ev.get("occursAt", []):
                session.run(
                    """
                    MATCH (e:Event {theographic_id: $id})
                    MATCH (p:Place {theographic_id: $place_id})
                    MERGE (e)-[:OCCURS_AT]->(p)
                    """,
                    id=ev["id"],
                    place_id=place_id,
                )

            for person_id in ev.get("participants", []):
                session.run(
                    """
                    MATCH (e:Event {theographic_id: $id})
                    MATCH (p:Person {theographic_id: $person_id})
                    MERGE (e)-[:HAS_PARTICIPANT]->(p)
                    """,
                    id=ev["id"],
                    person_id=person_id,
                )

        # 검증
        authored_count = session.run(
            "MATCH (e:Event) WHERE e.authored = true RETURN count(e) AS c"
        ).single()["c"]
        occurs_count = session.run(
            "MATCH (e:Event)-[r:OCCURS_AT]->(:Place) WHERE e.authored = true "
            "RETURN count(r) AS c"
        ).single()["c"]
        participant_count = session.run(
            "MATCH (e:Event)-[r:HAS_PARTICIPANT]->(:Person) WHERE e.authored = true "
            "RETURN count(r) AS c"
        ).single()["c"]
        print(f"authored Event nodes: {authored_count}")
        print(f"OCCURS_AT relationships (authored): {occurs_count}")
        print(f"HAS_PARTICIPANT relationships (authored): {participant_count}")

    driver.close()
    print("Done.")


if __name__ == "__main__":
    main()
