"""data/authored_persons/genealogy.json의 족보 사슬을 Neo4j에 멱등 적재한다 (ADR-0019).

혈통 단절 저작 보충 메커니즘. chain은 조상→후손 순서 단일 사슬이며:
  - authored=true 노드만 MERGE로 신규 생성(authored 마킹, ADR-0008).
  - 연속 쌍 (chain[i], chain[i+1]) = (부모, 자식)에 PARENT_OF/CHILD_OF 간선을
    load_theographic.py와 동일 규약(양방향)으로 MERGE. 기존↔저작·기존↔기존 모두 처리.
적재 후 사슬 끝(후손)에서 CHILD_OF*로 사슬 머리(조상)에 도달 가능한지 자체 검증한다.

재적재 규칙: load_theographic.py를 재실행하면 theographic 간선이 재적재되지만 이 저작
간선은 건드리지 않는다. 그래도 그래프 초기화 후엔 이 스크립트를 재실행해야 사슬이 복원된다.
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
    os.path.join(SCRIPT_DIR, "..", "..", "data", "authored_persons", "genealogy.json")
)


def main():
    with open(PATH, encoding="utf-8") as f:
        chain = json.load(f)["chain"]

    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    with driver.session() as session:
        # 1) 저작 노드 생성
        authored = [c for c in chain if c.get("authored")]
        for c in authored:
            session.run(
                """
                MERGE (p:Person {theographic_id: $id})
                SET p.authored = true, p.name = $name, p.nameKo = $nameKo
                """,
                id=c["id"], name=c.get("name", ""), nameKo=c.get("nameKo"),
            )
        print(f"authored genealogy nodes merged: {len(authored)}")

        # 2) 연속 쌍 간선 (부모 → 자식)
        pairs = [{"parentId": chain[i]["id"], "childId": chain[i + 1]["id"]}
                 for i in range(len(chain) - 1)]
        session.run(
            """
            UNWIND $pairs AS pair
            MATCH (parent:Person {theographic_id: pair.parentId})
            MATCH (child:Person  {theographic_id: pair.childId})
            MERGE (parent)-[:PARENT_OF]->(child)
            MERGE (child)-[:CHILD_OF]->(parent)
            """,
            pairs=pairs,
        )
        print(f"genealogy edges merged: {len(pairs)}")

        # 3) 자체 검증 — 사슬 끝에서 머리까지 CHILD_OF*로 연속인가
        head, tail = chain[0]["id"], chain[-1]["id"]
        reachable = session.run(
            """
            MATCH (t:Person {theographic_id: $tail})
            RETURN EXISTS { (t)-[:CHILD_OF*]->(:Person {theographic_id: $head}) } AS ok
            """,
            tail=tail, head=head,
        ).single()["ok"]
        if reachable:
            print(f"OK: {chain[-1]['nameKo']} → {chain[0]['nameKo']} 사슬 연속 (무단절)")
        else:
            raise SystemExit(f"FAIL: {chain[-1]['nameKo']} → {chain[0]['nameKo']} 사슬 단절")

    driver.close()
    print("Done.")


if __name__ == "__main__":
    main()
