"""data/person_context/people.json을 읽어 Neo4j Person 노드에 role/intro/verses 속성을 SET한다."""
import json
import os

from neo4j import GraphDatabase

NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD")
if not NEO4J_PASSWORD:
    raise RuntimeError("NEO4J_PASSWORD 환경변수가 설정되지 않았습니다")

SCRIPT_DIR = os.path.dirname(__file__)
CONTEXT_PATH = os.path.normpath(
    os.path.join(SCRIPT_DIR, "..", "..", "data", "person_context", "people.json")
)


def main():
    if not os.path.exists(CONTEXT_PATH):
        raise FileNotFoundError(f"{CONTEXT_PATH} not found")

    with open(CONTEXT_PATH, encoding="utf-8") as f:
        person_context = json.load(f)

    rows = []
    for tid, person in person_context.items():
        # verses는 JSON 문자열로 직렬화해 Neo4j 속성에 저장
        rows.append({
            "theographic_id": tid,
            "role": person.get("role"),
            "intro": person.get("intro"),
            "verses_json": json.dumps(person.get("verses", []), ensure_ascii=False),
        })

    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    with driver.session() as session:
        session.run(
            """
            UNWIND $rows AS row
            MATCH (p:Person {theographic_id: row.theographic_id})
            SET p.role = row.role, p.intro = row.intro, p.verses = row.verses_json
            """,
            rows=rows,
        )
        updated = session.run(
            "MATCH (p:Person) WHERE p.role IS NOT NULL RETURN count(p) AS c"
        ).single()["c"]
        print(f"Updated {updated} Person nodes with role/intro/verses")

    driver.close()
    print("Done.")


if __name__ == "__main__":
    main()
