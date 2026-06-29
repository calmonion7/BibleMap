"""data/authored_persons/people.json을 읽어 저작 인물을 Neo4j Person 노드로 멱등 적재한다.

각 인물은 MERGE (p:Person {theographic_id})로 만들고 authored=true 마킹한다 (ADR-0008).
Theographic 그래프에 없는 큐레이션 주인공(사사시대 인물 등)에만 쓴다 — authored 사건의
주변 참여자(네로·에스더 등 카드 없는 인물)는 대상이 아니다(ADR-0005의 경계).

적재 순서 제약: 이 스크립트가 load_person_events.py보다 먼저 실행돼야 인물 여정 사건의
HAS_PARTICIPANT MATCH가 성립한다."""
import json
import os

from neo4j import GraphDatabase

NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD")
if not NEO4J_PASSWORD:
    raise RuntimeError("NEO4J_PASSWORD 환경변수가 설정되지 않았습니다")

SCRIPT_DIR = os.path.dirname(__file__)
PEOPLE_PATH = os.path.normpath(
    os.path.join(SCRIPT_DIR, "..", "..", "data", "authored_persons", "people.json")
)


def main():
    if not os.path.exists(PEOPLE_PATH):
        raise FileNotFoundError(f"{PEOPLE_PATH} not found")

    with open(PEOPLE_PATH, encoding="utf-8") as f:
        people = json.load(f)

    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    with driver.session() as session:
        for person in people:
            session.run(
                """
                MERGE (p:Person {theographic_id: $id})
                SET p.authored = true,
                    p.name     = $name,
                    p.nameKo   = $nameKo
                """,
                id=person["id"],
                name=person.get("name", ""),
                nameKo=person.get("nameKo"),
            )

        # 검증
        authored_count = session.run(
            "MATCH (p:Person) WHERE p.authored = true RETURN count(p) AS c"
        ).single()["c"]
        print(f"authored Person nodes: {authored_count}")

    driver.close()
    print("Done.")


if __name__ == "__main__":
    main()
