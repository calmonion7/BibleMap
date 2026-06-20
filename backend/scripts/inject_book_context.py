"""data/book_context/books.json을 읽어 Neo4j Book 노드에 background·themes·keyVerse를 SET한다."""
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
    os.path.join(SCRIPT_DIR, "..", "..", "data", "book_context", "books.json")
)


def main():
    if not os.path.exists(CONTEXT_PATH):
        raise FileNotFoundError(f"{CONTEXT_PATH} not found — run generate_book_context.py first")

    with open(CONTEXT_PATH, encoding="utf-8") as f:
        book_context = json.load(f)

    rows = []
    for tid, ctx in book_context.items():
        rows.append({
            "theographic_id": tid,
            "background": ctx.get("background", ""),
            "themes": ctx.get("themes", []),
            "keyVerse": ctx.get("keyVerse", ""),
            "keyVerseTextKo": ctx.get("keyVerseTextKo"),
            "keyVerseTextEn": ctx.get("keyVerseTextEn"),
            "author": ctx.get("author", ""),
            "writtenDate": ctx.get("writtenDate", ""),
            "verseCount": ctx.get("verseCount"),
            "keyPeople": ctx.get("keyPeople", []),
            "centralMessage": ctx.get("centralMessage", ""),
            "structure": ctx.get("structure", ""),
        })

    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    with driver.session() as session:
        session.run(
            """
            UNWIND $rows AS row
            MATCH (b:Book {theographic_id: row.theographic_id})
            SET b.background     = row.background,
                b.themes         = row.themes,
                b.keyVerse       = row.keyVerse,
                b.keyVerseTextKo = row.keyVerseTextKo,
                b.keyVerseTextEn = row.keyVerseTextEn,
                b.authorKo         = row.author,
                b.writtenDate      = row.writtenDate,
                b.verseCount       = row.verseCount,
                b.keyPeople        = row.keyPeople,
                b.centralMessage   = row.centralMessage,
                b.structure        = row.structure
            """,
            rows=rows,
        )
        updated = session.run(
            "MATCH (b:Book) WHERE b.background IS NOT NULL RETURN count(b) AS c"
        ).single()["c"]
        print(f"Updated {updated} Book nodes with context")

        # 검증: Genesis
        genesis = session.run(
            "MATCH (b:Book {slug: 'gen'}) RETURN b.background AS bg LIMIT 1"
        ).single()
        if genesis:
            print(f"\nGenesis background: {genesis['bg'][:80]}...")

    driver.close()
    print("Done.")


if __name__ == "__main__":
    main()
