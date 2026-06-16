"""Claude API로 추정연도 성경책(31권)을 타임라인 사건에 연결해 오버레이 JSON으로 저장한다.

startYear가 없어 추정연도(book_years_approx)로 배치되는 31권은 CONTAINS_BOOK(구절 교집합)
관계가 없다. 이 스크립트는 그 책들을 "집필 배경/저자/직접 다루는" 사건에 의미적으로 연결한
오버레이를 생성한다. 결과는 Neo4j에 주입하지 않고 /books 엔드포인트가 런타임에 오버레이한다
(book_years_approx 선례 — CONTAINS_BOOK의 '사건의 근거' 의미는 그대로 유지).

출력: data/book_events/books.json
  { "<bookId(theographic_id)>": ["<eventId>", ...] }   # 연결 없으면 빈 배열

사용법:
  ANTHROPIC_API_KEY=sk-... NEO4J_PASSWORD=... python3 generate_book_events.py
"""
import json
import os

import anthropic
from neo4j import GraphDatabase

NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD")

SCRIPT_DIR = os.path.dirname(__file__)
APPROX_PATH = os.path.normpath(
    os.path.join(SCRIPT_DIR, "..", "..", "data", "book_years_approx", "books.json")
)
OUTPUT_PATH = os.path.normpath(
    os.path.join(SCRIPT_DIR, "..", "..", "data", "book_events", "books.json")
)


def load_events():
    """타임라인 사건(startDate 있는 것 — /events와 동일 집합)을 Neo4j에서 로드.
    반환: [{id, name, sortKey}, ...] sortKey 오름차순."""
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    with driver.session() as session:
        result = session.run(
            "MATCH (e:Event) WHERE e.startDate IS NOT NULL "
            "RETURN e.theographic_id AS id, "
            "       coalesce(e.nameKo, e.title) AS name, "
            "       e.sortKey AS sortKey "
            "ORDER BY e.sortKey ASC"
        )
        events = [{"id": r["id"], "name": r["name"], "sortKey": r["sortKey"]} for r in result]
    driver.close()
    return events


PROMPT_TEMPLATE = """성경의 추정연도 책 31권을 각 책과 가장 관련 깊은 타임라인 사건에 연결하시오.

[연결 기준]
- 서신서: 그 서신의 집필 배경이 된 사도행전 사건 (예: 고린도전서 → 에베소에서의 집필 사건)
- 구약 내러티브: 그 책이 직접 다루는 사건 (예: 역대하 → 솔로몬·유다 왕들의 통치)
- 지혜서/시가: 저자와 관련된 주요 사건 (예: 시편 → 다윗의 통치, 잠언 → 솔로몬의 통치)
- 적절한 사건이 사건 목록에 없으면 빈 배열 []
- 한 책에 여러 사건 연결 가능. 사건 목록에 실제로 존재하는 id만 사용.

[책 목록]
{books}

[사건 목록 (id | 사건명)]
{events}

아래 형식의 순수 JSON만 출력(다른 텍스트 없이):
{{ "<bookId>": ["<eventId>", ...], ... }}
모든 책 id를 키로 포함하시오."""


def generate(client, books, events):
    books_str = "\n".join(f"{tid} | {b['nameKo']} (~{b['placementYear']})" for tid, b in books.items())
    events_str = "\n".join(f"{e['id']} | {e['name']}" for e in events)
    prompt = PROMPT_TEMPLATE.format(books=books_str, events=events_str)
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    text = msg.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())


def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY 환경변수가 설정되지 않았습니다")
    if not NEO4J_PASSWORD:
        raise RuntimeError("NEO4J_PASSWORD 환경변수가 설정되지 않았습니다")

    with open(APPROX_PATH, encoding="utf-8") as f:
        books = json.load(f)
    events = load_events()
    print(f"  {len(books)} approx books, {len(events)} timeline events loaded")

    client = anthropic.Anthropic(api_key=api_key)
    mapping = generate(client, books, events)

    # 유효성 검증: 사건 목록에 없는 id 제거, 모든 책 키 보장
    valid = {e["id"] for e in events}
    cleaned = {}
    for tid in books:
        eids = [e for e in mapping.get(tid, []) if e in valid]
        cleaned[tid] = eids

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(cleaned, f, ensure_ascii=False, indent=2)

    nonempty = sum(1 for v in cleaned.values() if v)
    print(f"\nDone. {len(cleaned)} books ({nonempty} with events) written to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
