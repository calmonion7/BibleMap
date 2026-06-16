"""각 사건의 근거 구절을 권별로 묶어 오버레이 JSON으로 저장한다.

events.json(사건별 fields.verses = 구절 레코드 ID 배열) + verses.json(구절 레코드)을
받아, 각 사건의 구절을 책별(verses 레코드 fields.book[0] = Book.theographic_id)로
그룹하고 연속 구간을 접은 rangeLabel을 생성한다.

출력: data/event_verses/events.json
  {
    "<event_theographic_id>": {
      "books": [
        {
          "bookId": "<theographic_id>",
          "bookOrder": <int>,
          "rangeLabel": "<str>",
          "verses": [ {"verseID": "<str>", "chapter": <int>, "verse": <int>}, ... ]
        }, ...   # books는 bookOrder 정경순
      ]
    }
  }

사용법:
  python3 generate_event_verses.py
"""
import json
import os
import urllib.request

EVENTS_URL = "https://raw.githubusercontent.com/robertrouse/theographic-bible-metadata/master/json/events.json"
VERSES_URL = "https://raw.githubusercontent.com/robertrouse/theographic-bible-metadata/master/json/verses.json"

SCRIPT_DIR = os.path.dirname(__file__)
OUTPUT_PATH = os.path.normpath(
    os.path.join(SCRIPT_DIR, "..", "..", "data", "event_verses", "events.json")
)


def fetch_json(url):
    with urllib.request.urlopen(url) as resp:
        return json.loads(resp.read().decode("utf-8"))


def parse_verse(verse_id):
    """verseID(BBCCCVVV) → {verseID, bookOrder, chapter, verse}.
    fields.chapter는 레코드 ID라 쓰지 않고 verseID에서 파생한다."""
    return {
        "verseID": verse_id,
        "bookOrder": int(verse_id[:2]),
        "chapter": int(verse_id[2:5]),
        "verse": int(verse_id[5:8]),
    }


def build_range_label(verses):
    """verseID 오름차순 verses를 받아, verseID가 1씩 증가하는 연속 구간을 접은 라벨.
    한 장 안 구간은 'C:Vstart–Vend'(단일 절이면 'C:V'), 장 경계를 넘는 연속 구간은
    'C1:Vs–C2:Ve'. 비연속 구간들은 ', '로 연결."""
    runs = []  # 각 run = (start_verse, end_verse)  (parse_verse dict)
    for v in verses:
        if runs and int(v["verseID"]) == int(runs[-1][1]["verseID"]) + 1:
            runs[-1] = (runs[-1][0], v)
        else:
            runs.append((v, v))

    parts = []
    for start, end in runs:
        if start["verseID"] == end["verseID"]:
            parts.append(f"{start['chapter']}:{start['verse']}")
        elif start["chapter"] == end["chapter"]:
            parts.append(f"{start['chapter']}:{start['verse']}–{end['verse']}")
        else:
            parts.append(
                f"{start['chapter']}:{start['verse']}–{end['chapter']}:{end['verse']}"
            )
    return ", ".join(parts)


def main():
    print("Fetching events.json ...")
    events = fetch_json(EVENTS_URL)
    print(f"  {len(events)} events fetched")

    print("Fetching verses.json (~15MB) ...")
    verses = fetch_json(VERSES_URL)
    print(f"  {len(verses)} verses fetched")

    # 구절 레코드 ID → 레코드
    verse_by_id = {v["id"]: v for v in verses}

    result = {}
    for e in events:
        event_id = e["id"]
        # 책 theographic_id → 파싱된 구절 리스트
        books = {}
        for vid in e["fields"].get("verses", []):
            rec = verse_by_id.get(vid)
            if rec is None:
                continue
            book_ids = rec["fields"].get("book") or []
            verse_id = rec["fields"].get("verseID")
            if not book_ids or not verse_id:
                continue
            book_tid = book_ids[0]
            books.setdefault(book_tid, []).append(parse_verse(verse_id))

        book_entries = []
        for book_tid, vlist in books.items():
            vlist.sort(key=lambda x: x["verseID"])
            book_entries.append({
                "bookId": book_tid,
                "bookOrder": vlist[0]["bookOrder"],
                "rangeLabel": build_range_label(vlist),
                "verses": [
                    {"verseID": x["verseID"], "chapter": x["chapter"], "verse": x["verse"]}
                    for x in vlist
                ],
            })
        # books는 bookOrder 정경순
        book_entries.sort(key=lambda b: b["bookOrder"])
        result[event_id] = {"books": book_entries}

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    n_with_books = sum(1 for v in result.values() if v["books"])
    print(f"\nDone. {len(result)} events ({n_with_books} with verses) written to {OUTPUT_PATH}")

    # 공관복음 평행 사건 1건(books >= 2) 육안 검증 출력
    for e in events:
        entry = result[e["id"]]
        if len(entry["books"]) >= 2:
            print(f"\n[검증] 다권 사건: {e['fields'].get('title')} (id={e['id']})")
            for b in entry["books"]:
                print(f"  bookId={b['bookId']} bookOrder={b['bookOrder']} "
                      f"rangeLabel={b['rangeLabel']} ({len(b['verses'])}절)")
            break


if __name__ == "__main__":
    main()
