"""data/authored_persons/mothers.json의 어머니-자식 저작 간선을 Neo4j에 멱등 적재한다 (ADR-0027).

성경에 어머니가 명시된 경우만 담는 보강 간선(삼하 3:2-5의 다윗 아들들, 열왕기 모후 정형구 등).
어머니·자식 모두 기존 Person 노드여야 하며(MATCH — 노드 신규 생성 없음), PARENT_OF/CHILD_OF를
load_theographic.py와 동일 규약(양방향)으로 MERGE한다.

재적재 규칙: 그래프 초기화 후 load_theographic.py 재실행 시 이 스크립트도 재실행해야 복원된다
(load_authored_genealogy.py와 동일).
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
PATH = os.path.normpath(
    os.path.join(SCRIPT_DIR, "..", "..", "data", "authored_persons", "mothers.json")
)


def main():
    with open(PATH, encoding="utf-8") as f:
        pairs = json.load(f)["pairs"]

    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    with driver.session() as session:
        result = session.run(
            """
            UNWIND $pairs AS pair
            MATCH (m:Person {theographic_id: pair.motherId})
            MATCH (c:Person {theographic_id: pair.childId})
            MERGE (m)-[:PARENT_OF]->(c)
            MERGE (c)-[:CHILD_OF]->(m)
            RETURN count(*) AS n
            """,
            pairs=[{"motherId": p["motherId"], "childId": p["childId"]} for p in pairs],
        ).single()
        print(f"mother edges merged: {result['n']}/{len(pairs)}")
        if result["n"] != len(pairs):
            raise SystemExit(f"경고: {len(pairs) - result['n']}쌍이 노드 미존재로 적재되지 않음")

    driver.close()
    print("Done.")


if __name__ == "__main__":
    main()
