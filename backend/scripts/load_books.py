"""Book 노드를 Neo4j에 적재하고 Book-Event CONTAINS_BOOK 관계를 생성한다."""
import json
import os
import urllib.request

from neo4j import GraphDatabase

NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD")
if not NEO4J_PASSWORD:
    raise RuntimeError("NEO4J_PASSWORD 환경변수가 설정되지 않았습니다")

BOOKS_URL = "https://raw.githubusercontent.com/robertrouse/theographic-bible-metadata/master/json/books.json"
EVENTS_URL = "https://raw.githubusercontent.com/robertrouse/theographic-bible-metadata/master/json/events.json"

SCRIPT_DIR = os.path.dirname(__file__)
NAMES_KO_PATH = os.path.join(SCRIPT_DIR, "..", "..", "data", "names_ko", "books.json")


def fetch_json(url):
    with urllib.request.urlopen(url) as resp:
        return json.loads(resp.read().decode("utf-8"))


def load_names_ko():
    path = os.path.normpath(NAMES_KO_PATH)
    if not os.path.exists(path):
        print(f"[WARN] {path} not found, nameKo will be empty")
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_book_rows(books, names_ko):
    rows = []
    for b in books:
        tid = b["id"]
        f = b["fields"]
        testament = f.get("testament", "")
        testament_ko = "구약" if "Old" in testament else "신약"
        rows.append({
            "theographic_id": tid,
            "name": f.get("bookName"),
            "nameKo": names_ko.get(tid, {}).get("ko", f.get("bookName", "")),
            "testament": testament_ko,
            "genre": f.get("bookDiv", ""),
            "osisName": f.get("osisName", ""),
            "chapterCount": f.get("chapterCount", 0),
            "slug": f.get("slug", ""),
            "bookOrder": f.get("bookOrder", 0),
        })
    return rows


def _parse_year(s):
    """startDate("-4003"/"-1451-01"/"0049-10-01"/"30") → 부호 있는 연도 정수 또는 None.
    nodes.py `_year`·dates.js `parseYear`와 동일 규칙(부호 분리 후 첫 '-' 이전만)."""
    if not s:
        return None
    s = str(s)
    neg = s.startswith("-")
    body = s[1:] if neg else s
    try:
        y = int(body.split("-")[0])
    except ValueError:
        return None
    return -y if neg else y


# 파서 셀프체크: 월/일 정밀도가 int()로 조용히 누락되던 버그(task#151 #2) 회귀 방지
assert _parse_year("-1451-01") == -1451
assert _parse_year("0049-10-01") == 49
assert _parse_year("-4003") == -4003
assert _parse_year("30") == 30
assert _parse_year("") is None


def build_book_year_range(books, events):
    """Book별 startYear/endYear를 event.startDate 집계로 추정한다."""
    # verse IDs → book theographic_id 역매핑
    verse_to_book = {}
    for b in books:
        for vid in b["fields"].get("verses", []):
            verse_to_book[vid] = b["id"]

    book_years = {}
    for e in events:
        year = _parse_year(e["fields"].get("startDate", ""))
        if year is None:
            continue
        for vid in e["fields"].get("verses", []):
            bid = verse_to_book.get(vid)
            if not bid:
                continue
            if bid not in book_years:
                book_years[bid] = []
            book_years[bid].append(year)

    result = {}
    for bid, years in book_years.items():
        result[bid] = {"startYear": min(years), "endYear": max(years)}
    return result


def main():
    print("Fetching books.json ...")
    books = fetch_json(BOOKS_URL)
    print(f"  {len(books)} books fetched")

    print("Fetching events.json ...")
    events = fetch_json(EVENTS_URL)
    print(f"  {len(events)} events fetched")

    names_ko = load_names_ko()
    rows = build_book_rows(books, names_ko)
    year_range = build_book_year_range(books, events)

    for row in rows:
        yr = year_range.get(row["theographic_id"], {})
        row["startYear"] = yr.get("startYear")
        row["endYear"] = yr.get("endYear")

    # verse_id → book theographic_id (for CONTAINS_BOOK)
    verse_to_book = {}
    for b in books:
        for vid in b["fields"].get("verses", []):
            verse_to_book[vid] = b["id"]

    # event → book 관계 (1 event : N books). verses[0]의 책=발생(primary), 나머지=회고 인용 (ADR-0012)
    event_book_rels = []
    for e in events:
        verses = e["fields"].get("verses", [])
        primary_bid = next((verse_to_book[v] for v in verses if verse_to_book.get(v)), None)
        bid_set = set()
        for vid in verses:
            bid = verse_to_book.get(vid)
            if bid:
                bid_set.add(bid)
        for bid in bid_set:
            event_book_rels.append({
                "event_id": e["id"], "book_id": bid, "primary": bid == primary_bid,
            })

    print(f"  {len(event_book_rels)} Book-Event relationships to create")

    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    with driver.session() as session:
        print("Creating Book index ...")
        session.run(
            "CREATE INDEX book_tid IF NOT EXISTS FOR (n:Book) ON (n.theographic_id)"
        )

        print(f"Loading {len(rows)} Book nodes ...")
        session.run(
            """
            UNWIND $rows AS row
            MERGE (b:Book {theographic_id: row.theographic_id})
            SET b.name         = row.name,
                b.nameKo       = row.nameKo,
                b.testament    = row.testament,
                b.genre        = row.genre,
                b.osisName     = row.osisName,
                b.chapterCount = row.chapterCount,
                b.slug         = row.slug,
                b.bookOrder    = row.bookOrder,
                b.startYear    = row.startYear,
                b.endYear      = row.endYear
            """,
            rows=rows,
        )

        count = session.run("MATCH (b:Book) RETURN count(b) AS c").single()["c"]
        print(f"  Book nodes in Neo4j: {count}")

        print("Creating CONTAINS_BOOK relationships ...")
        batch_size = 500
        for i in range(0, len(event_book_rels), batch_size):
            session.run(
                """
                UNWIND $rels AS rel
                MATCH (b:Book {theographic_id: rel.book_id})
                MATCH (e:Event {theographic_id: rel.event_id})
                MERGE (b)-[r:CONTAINS_BOOK]->(e)
                SET r.primary = rel.primary
                """,
                rels=event_book_rels[i:i + batch_size],
            )
        rel_count = session.run(
            "MATCH ()-[r:CONTAINS_BOOK]->() RETURN count(r) AS c"
        ).single()["c"]
        print(f"  CONTAINS_BOOK relationships: {rel_count}")

    driver.close()
    print("Done.")


if __name__ == "__main__":
    main()
