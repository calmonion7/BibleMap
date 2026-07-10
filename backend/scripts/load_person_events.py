"""data/person_events/*.json을 읽어 인물 여정 저작 이벤트를 Neo4j에 멱등 적재한다.

각 이벤트는 authored=true로 마킹한 Event 노드이며, OCCURS_AT→Place, HAS_PARTICIPANT→Person으로 연결된다.
books 필드가 있으면 Book-[:CONTAINS_BOOK]->Event 관계도 생성한다(ADR-0005 보완)."""
import glob as glob_module
import json
import os

from neo4j import GraphDatabase

NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD")
if not NEO4J_PASSWORD:
    raise RuntimeError("NEO4J_PASSWORD 환경변수가 설정되지 않았습니다")

SCRIPT_DIR = os.path.dirname(__file__)
PERSON_EVENTS_DIR = os.path.normpath(
    os.path.join(SCRIPT_DIR, "..", "..", "data", "person_events")
)

FILES = [
    os.path.basename(p)
    for p in sorted(glob_module.glob(os.path.join(PERSON_EVENTS_DIR, "*.json")))
]


def load_events(session, events):
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

        # books[0]=발생(primary), 이후=회고 인용 (ADR-0012)
        for idx, book_ref in enumerate(ev.get("books", [])):
            session.run(
                """
                MATCH (b:Book {theographic_id: $book_id})
                MATCH (e:Event {theographic_id: $ev_id})
                MERGE (b)-[r:CONTAINS_BOOK]->(e)
                SET r.primary = $primary
                """,
                book_id=book_ref["bookId"],
                ev_id=ev["id"],
                primary=(idx == 0),
            )


def main():
    all_events = []
    for fname in FILES:
        path = os.path.join(PERSON_EVENTS_DIR, fname)
        with open(path, encoding="utf-8") as f:
            events = json.load(f)
        all_events.extend(events)
        print(f"  {fname}: {len(events)}개 이벤트 로드")

    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    with driver.session() as session:
        load_events(session, all_events)

        # 검증
        total_authored = session.run(
            "MATCH (e:Event) WHERE e.authored = true RETURN count(e) AS c"
        ).single()["c"]
        new_ids = [ev["id"] for ev in all_events]
        new_count = session.run(
            "MATCH (e:Event) WHERE e.theographic_id IN $ids RETURN count(e) AS c",
            ids=new_ids,
        ).single()["c"]
        occurs = session.run(
            "MATCH (e:Event)-[:OCCURS_AT]->(:Place) WHERE e.theographic_id IN $ids "
            "RETURN count(e) AS c",
            ids=new_ids,
        ).single()["c"]
        participants = session.run(
            "MATCH (e:Event)-[:HAS_PARTICIPANT]->(:Person) WHERE e.theographic_id IN $ids "
            "RETURN count(e) AS c",
            ids=new_ids,
        ).single()["c"]
        contains_books = session.run(
            "MATCH (:Book)-[:CONTAINS_BOOK]->(e:Event) WHERE e.theographic_id IN $ids "
            "RETURN count(e) AS c",
            ids=new_ids,
        ).single()["c"]

    driver.close()

    print(f"\n완료:")
    print(f"  전체 authored Event: {total_authored}개")
    print(f"  인물 여정 이벤트: {new_count}개")
    print(f"  OCCURS_AT 관계: {occurs}개")
    print(f"  HAS_PARTICIPANT 관계: {participants}개")
    print(f"  CONTAINS_BOOK 관계: {contains_books}개")


if __name__ == "__main__":
    main()
