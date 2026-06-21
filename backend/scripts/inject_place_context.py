"""data/place_context/places.json을 읽어 Neo4j Place 노드에 background·keyVerse를 SET한다."""
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
    os.path.join(SCRIPT_DIR, "..", "..", "data", "place_context", "places.json")
)


def main():
    if not os.path.exists(CONTEXT_PATH):
        raise FileNotFoundError(f"{CONTEXT_PATH} not found — run generate_verse_text.py first")

    with open(CONTEXT_PATH, encoding="utf-8") as f:
        place_context = json.load(f)

    rows = []
    for tid, ctx in place_context.items():
        rows.append({
            "theographic_id": tid,
            "background": ctx.get("background", ""),
            "keyVerse": ctx.get("keyVerse", ""),
            "keyVerseTextKo": ctx.get("keyVerseTextKo"),
            "keyVerseTextEn": ctx.get("keyVerseTextEn"),
        })

    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    with driver.session() as session:
        session.run(
            """
            UNWIND $rows AS row
            MATCH (p:Place {theographic_id: row.theographic_id})
            SET p.background     = row.background,
                p.keyVerse       = row.keyVerse,
                p.keyVerseTextKo = row.keyVerseTextKo,
                p.keyVerseTextEn = row.keyVerseTextEn
            """,
            rows=rows,
        )
        updated = session.run(
            "MATCH (p:Place) WHERE p.background IS NOT NULL RETURN count(p) AS c"
        ).single()["c"]
        print(f"Updated {updated} Place nodes with context")

        # 검증: Bethlehem
        bethlehem = session.run(
            "MATCH (p:Place {theographic_id: 'authored-place-bethlehem'}) "
            "RETURN p.background AS bg LIMIT 1"
        ).single()
        if bethlehem:
            print(f"\nBethlehem background: {bethlehem['bg'][:80]}...")

    driver.close()
    print("Done.")


if __name__ == "__main__":
    main()
