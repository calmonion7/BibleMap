"""data/verse_events/events.json을 읽어 신규 Event 노드 + CONTAINS_BOOK 관계를 Neo4j에 멱등 적재한다.

사용법:
  NEO4J_PASSWORD=... python3 load_verse_events.py
"""
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
    os.path.join(SCRIPT_DIR, "..", "..", "data", "verse_events", "events.json")
)


def main():
    if not os.path.exists(EVENTS_PATH):
        raise FileNotFoundError(f"{EVENTS_PATH} not found — generate_verse_events.py를 먼저 실행하세요")

    with open(EVENTS_PATH, encoding="utf-8") as f:
        data = json.load(f)
    events = data["events"]
    print(f"{len(events)}개 사건 로드")

    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    event_count = 0
    rel_count = 0

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
                    e.yearLabel = $yearLabel
                """,
                id=ev["id"],
                title=ev.get("title", ""),
                nameKo=ev.get("nameKo"),
                startDate=str(ev.get("startDate", "")),
                sortKey=int(ev.get("sortKey", 0)),
                yearLabel=ev.get("yearLabel"),
            )
            event_count += 1

            # CONTAINS_BOOK: 생성 시 기록한 source book_id 사용
            book_id = ev.get("book_id")
            if book_id:
                result = session.run(
                    """
                    MATCH (b:Book {theographic_id: $book_id})
                    MATCH (e:Event {theographic_id: $ev_id})
                    MERGE (b)-[r:CONTAINS_BOOK]->(e)
                    RETURN count(r) AS c
                    """,
                    book_id=book_id,
                    ev_id=ev["id"],
                )
                rel_count += result.single()["c"]

        # 검증
        new_count = session.run(
            "MATCH (e:Event) WHERE e.theographic_id STARTS WITH 'verse-event-' "
            "RETURN count(e) AS c"
        ).single()["c"]

    driver.close()
    print(f"MERGE 완료: Event {event_count}개 처리, CONTAINS_BOOK {rel_count}개 생성")
    print(f"Neo4j verse-event 노드 총 수: {new_count}")
    print("Done.")


if __name__ == "__main__":
    main()
