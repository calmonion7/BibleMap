"""Theographic GitHub JSON에서 각 책의 고아 구절(어떤 Event에도 속하지 않는 구절)을 찾고,
Claude API로 주요 사건을 도출해 data/verse_events/events.json에 저장한다.

사용법:
  ANTHROPIC_API_KEY=sk-... python3 generate_verse_events.py

출력: data/verse_events/events.json
  { "events": [ {id, title, nameKo, startDate, sortKey, yearLabel, book_id}, ... ] }
"""
import json
import os
import re
import time
import urllib.request

import anthropic

BOOKS_URL = "https://raw.githubusercontent.com/robertrouse/theographic-bible-metadata/master/json/books.json"
EVENTS_URL = "https://raw.githubusercontent.com/robertrouse/theographic-bible-metadata/master/json/events.json"
VERSES_URL = "https://raw.githubusercontent.com/robertrouse/theographic-bible-metadata/master/json/verses.json"

SCRIPT_DIR = os.path.dirname(__file__)
OUTPUT_PATH = os.path.normpath(
    os.path.join(SCRIPT_DIR, "..", "..", "data", "verse_events", "events.json")
)

# 고아 구절 수가 이 이하면 스킵 (너무 적으면 의미 있는 사건 도출 어려움)
MIN_ORPHAN_VERSES = 5
# 책당 최대 도출 사건 수
MAX_EVENTS_PER_BOOK = 5

PROMPT_TEMPLATE = """성경 {book_name}의 다음 구절들을 분석하여 주요 사건을 최대 {max_events}개 도출하시오.
이 구절들은 기존 사건 데이터베이스에 등록되지 않은 구절들입니다.

[구절 목록 (OSIS참조: 영문 본문)]
{verse_list}

각 사건에 대해 아래 JSON 형식으로 응답하시오(순수 JSON 배열만, 다른 텍스트 없이):
[
  {{
    "title": "영문 사건명 (간결하게)",
    "nameKo": "한글 사건명",
    "startDate": "연도 문자열 (예: '-1000', '30', '-586')",
    "sortKey": 정수형_연도 (예: -1000, 30, -586),
    "yearLabel": "표시용 연도 (예: 'BC 1000경', 'AD 30경')",
    "verses": ["Gen.1.1", "Gen.1.2"]
  }}
]

주의:
- verses 배열에는 위 구절 목록에 있는 OSIS 참조만 사용할 것
- 구절 목록에 없는 구절 추가 금지
- sortKey는 BC면 음수, AD면 양수
- 사건이 없으면 빈 배열 [] 반환"""


def fetch_json(url):
    with urllib.request.urlopen(url) as resp:
        return json.loads(resp.read().decode("utf-8"))


def slugify(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")[:60]


def build_verse_map(verses_data):
    """verse record id → {osisRef, verseText} 매핑 구성."""
    vm = {}
    for v in verses_data:
        f = v.get("fields", {})
        osis = f.get("osisRef")
        if osis:
            vm[v["id"]] = {"osisRef": osis, "verseText": f.get("verseText", "")}
    return vm


def build_covered_set(events_data):
    """theographic events.json의 모든 verse record id 합집합."""
    covered = set()
    for ev in events_data:
        for vid in ev.get("fields", {}).get("verses", []):
            covered.add(vid)
    return covered


def generate_events(client, book_name, book_id, orphan_verses, verse_map):
    """Claude API로 사건 도출. 오류 시 빈 목록 반환."""
    verse_lines = []
    for vid in orphan_verses[:200]:  # 토큰 절약: 최대 200구절만
        info = verse_map.get(vid)
        if info:
            verse_lines.append(f"{info['osisRef']}: {info['verseText'][:120]}")

    if not verse_lines:
        return []

    prompt = PROMPT_TEMPLATE.format(
        book_name=book_name,
        max_events=MAX_EVENTS_PER_BOOK,
        verse_list="\n".join(verse_lines),
    )

    try:
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        text = msg.content[0].text.strip()
        # 코드블록 제거
        if text.startswith("```"):
            text = "\n".join(text.split("\n")[1:])
            if "```" in text:
                text = text[: text.index("```")]
        return json.loads(text.strip())
    except Exception as e:
        print(f"  [경고] {book_name} 사건 도출 실패: {e}")
        return []


def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY 환경변수가 설정되지 않았습니다")

    print("Theographic 데이터 로딩...")
    books_data = fetch_json(BOOKS_URL)
    events_data = fetch_json(EVENTS_URL)
    print(f"  {len(books_data)} books, {len(events_data)} events 로드")

    print("verses.json 로딩 (31102개, 잠시 대기)...")
    verses_data = fetch_json(VERSES_URL)
    verse_map = build_verse_map(verses_data)
    print(f"  {len(verse_map)} verse records 매핑")

    covered = build_covered_set(events_data)
    print(f"  covered verse ids: {len(covered)}")

    # books를 bookOrder 순으로 정렬
    books_sorted = sorted(books_data, key=lambda b: b.get("fields", {}).get("bookOrder", 99))

    client = anthropic.Anthropic(api_key=api_key)

    all_events = []
    existing_titles = set()

    for book in books_sorted:
        f = book.get("fields", {})
        book_name = f.get("bookName", "")
        book_id = book["id"]  # Airtable record id = theographic_id in Neo4j
        book_verses = f.get("verses", [])

        orphan = [vid for vid in book_verses if vid not in covered]
        if len(orphan) < MIN_ORPHAN_VERSES:
            continue

        print(f"  [{f.get('bookOrder'):2d}] {book_name}: 총 {len(book_verses)}구절 중 고아 {len(orphan)}개 → Claude 호출")

        events = generate_events(client, book_name, book_id, orphan, verse_map)
        time.sleep(0.3)  # rate limit 방지

        added = 0
        for ev in events:
            title = ev.get("title", "").strip()
            if not title or title.lower() in existing_titles:
                print(f"    스킵(중복): {title}")
                continue

            ev_id = f"verse-event-{slugify(title)}"
            ev["id"] = ev_id
            ev["book_id"] = book_id
            existing_titles.add(title.lower())
            all_events.append(ev)
            added += 1

        if added:
            print(f"    → {added}개 사건 추가")

    # 중복 id 제거 (안전망)
    seen_ids = set()
    deduped = []
    for ev in all_events:
        if ev["id"] not in seen_ids:
            seen_ids.add(ev["id"])
            deduped.append(ev)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump({"events": deduped}, f, ensure_ascii=False, indent=2)

    print(f"\nDone. {len(deduped)}개 사건 → {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
