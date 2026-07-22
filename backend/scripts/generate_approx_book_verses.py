"""추정 연도 책(31권)의 집필 배경 사건과 대표 구절 구조를 생성한다.

book_events/books.json의 31쌍 각각에 대해 책의 집필 맥락을 가장 잘 드러내는
대표 구절(텍스트 없음)을 선정해 event_verses/events.json에 merge한다.
기존 CONTAINS_BOOK 엔트리(근거 구절)는 보존하고, 같은 eventId에 books 배열만 추가.

텍스트(textKo/textEn)는 generate_verse_text.py 실행 시 채워진다(멱등).

선정 기준: 책의 저자 서문 / 역사적 출발점 / 집필 배경을 가장 명시적으로 드러내는 구절.
역대하는 사건별로 다른 장에서 그 시대의 왕통을 시작하는 절을 선택.

사용법:
  python3 generate_approx_book_verses.py
"""
import json
import os
import sys

SCRIPT_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "..", "data"))
BOOK_EVENTS_PATH = os.path.join(DATA_DIR, "book_events", "books.json")
EVENT_VERSES_PATH = os.path.join(DATA_DIR, "event_verses", "events.json")

# (bookId, eventId) → [(chapter, verse), ...] — 대표 구절 목록
# bookOrder: 성경 정경순(Genesis=1 … Revelation=66)
# verseID: f"{bookOrder:02d}{chapter:03d}{verse:03d}"
VERSE_MAP = {
    # 레위기 (bookOrder=3): 십계명 수여 / 성막 건축 — 하나님이 회막에서 모세를 부르심
    ("rec6qL6gTvX4tUw4A", "reca8LvAmFPl1tmnN"): {"bookOrder": 3,  "verses": [(1, 1), (1, 2)]},
    ("rec6qL6gTvX4tUw4A", "recvA947nCyo8kadV"): {"bookOrder": 3,  "verses": [(1, 1), (1, 2)]},
    # 룻기 (bookOrder=8): 사사 시대 배경 사건 — "사사들이 치리하던 때에"
    ("recZuCb9Bn0RErpsL", "reczOHadpTVOuiidp"): {"bookOrder": 8,  "verses": [(1, 1)]},
    ("recZuCb9Bn0RErpsL", "recSRPo1LlWZ7tNaO"): {"bookOrder": 8,  "verses": [(1, 1)]},
    # 역대하 (bookOrder=14): 5개 사건 — 각 왕통 시작절
    ("rec410yOewjNfbeE3", "recKTbnO8VY7lXLeX"): {"bookOrder": 14, "verses": [(1, 1)]},      # 솔로몬 통치
    ("rec410yOewjNfbeE3", "recYlpu8OdsUJoG8g"): {"bookOrder": 14, "verses": [(3, 1)]},      # 성전 건축
    ("rec410yOewjNfbeE3", "recX0KzMJywvbeM6D"): {"bookOrder": 14, "verses": [(10, 1)]},     # 르호보암
    ("rec410yOewjNfbeE3", "recRusMYR5At9TlEV"): {"bookOrder": 14, "verses": [(29, 1)]},     # 히스기야
    ("rec410yOewjNfbeE3", "recVf3eQjAq3nk94o"): {"bookOrder": 14, "verses": [(34, 1)]},     # 요시야
    # 에스라 (bookOrder=15): 학개·스가랴 예언 — 에스라 5:1 "그때에 학개와 스가랴가 예언하니"
    ("recit4Q50QB9nM3q2", "recQPoA7fH3wJi7v2"): {"bookOrder": 15, "verses": [(5, 1), (5, 2)]},
    ("recit4Q50QB9nM3q2", "recebNaZjPvbOqk4r"): {"bookOrder": 15, "verses": [(5, 1), (5, 2)]},
    # 느헤미야 (bookOrder=16): 말라기 예언 — 동시대(아닥사스다 왕)
    ("rec3WEGPl0a1PS0cC", "recpSNqfLiST1KQqq"): {"bookOrder": 16, "verses": [(1, 1)]},
    # 에스더 (bookOrder=17): 페르시아 구원 — 아하수에로 왕 때
    ("rec6yHFZ6w7UUw5Cu", "authored-esther-persia-deliverance"): {"bookOrder": 17, "verses": [(1, 1)]},
    # 시편 (bookOrder=19): 다윗 통치 — 시편 1편 서론
    ("recKXZXO6cJwk2SxO", "reczzYTmzPPDcP3qv"): {"bookOrder": 19, "verses": [(1, 1), (1, 2), (1, 3)]},
    # 잠언 (bookOrder=20): 솔로몬 통치 — "이스라엘 왕 다윗의 아들 솔로몬의 잠언이라"
    ("recRLdYtz1vjdW7yd", "recKTbnO8VY7lXLeX"): {"bookOrder": 20, "verses": [(1, 1), (1, 2), (1, 3)]},
    # 전도서 (bookOrder=21): 솔로몬 통치 — "전도자의 말씀이라"
    ("recd3p656hOWx95Jk", "recKTbnO8VY7lXLeX"): {"bookOrder": 21, "verses": [(1, 1), (1, 2)]},
    # 아가 (bookOrder=22): 솔로몬 통치 — "솔로몬의 아가라"
    ("recnUwcJABJVgZDCI", "recKTbnO8VY7lXLeX"): {"bookOrder": 22, "verses": [(1, 1)]},
    # 예레미야애가 (bookOrder=25): 시드기야 통치 — "슬프다 이 성이여"
    ("recdT4VI6VdkEzixN", "recW2cNLqUyMIV6O7"): {"bookOrder": 25, "verses": [(1, 1), (1, 2), (1, 3)]},
    # 로마서 (bookOrder=45): 3차 선교 여행 / 마게도냐·그리스 — 바울의 인사
    ("recyvIyxRMFob6SoM", "rec4bAiAcAOo9mPwO"): {"bookOrder": 45, "verses": [(1, 1), (1, 2), (1, 3)]},
    ("recyvIyxRMFob6SoM", "recGXoNtdiKu28Wff"): {"bookOrder": 45, "verses": [(1, 1), (1, 2), (1, 3)]},
    # 고린도전서 (bookOrder=46): 에베소 전도 — "우리 주 예수 그리스도의 이름으로 부르심을 받은"
    ("recVtbTyqtbbtqRC5", "rec2buqN0Q38Yuqme"): {"bookOrder": 46, "verses": [(1, 1), (1, 2), (1, 3)]},
    # 고린도후서 (bookOrder=47): 마게도냐·그리스 — 바울의 인사
    ("rec0CTDRtMnNCmQr9", "recGXoNtdiKu28Wff"): {"bookOrder": 47, "verses": [(1, 1), (1, 2)]},
    # 에베소서 (bookOrder=49): 첫 번째 로마 투옥
    ("rec3IwUp30NnnEqSL", "recGrIgOxWnxVl8h0"): {"bookOrder": 49, "verses": [(1, 1), (1, 2)]},
    # 빌립보서 (bookOrder=50): 첫 번째 로마 투옥
    ("recY95JJhNEzOwMNv", "recGrIgOxWnxVl8h0"): {"bookOrder": 50, "verses": [(1, 1), (1, 2), (1, 3)]},
    # 골로새서 (bookOrder=51): 첫 번째 로마 투옥
    ("recY37UhYyyAlabnd", "recGrIgOxWnxVl8h0"): {"bookOrder": 51, "verses": [(1, 1), (1, 2)]},
    # 데살로니가전서 (bookOrder=52): 고린도 전도
    ("recDZc63lmQiSe0gn", "authored-paul-corinth"): {"bookOrder": 52, "verses": [(1, 1), (1, 2), (1, 3)]},
    # 데살로니가후서 (bookOrder=53): 고린도 전도
    ("recnZBkoT7W0SV19v", "authored-paul-corinth"): {"bookOrder": 53, "verses": [(1, 1), (1, 2)]},
    # 디모데전서 (bookOrder=54): 석방기 목회서신
    ("rec2yyoaHMOHZcynX", "authored-paul-release-pastorals"): {"bookOrder": 54, "verses": [(1, 1), (1, 2)]},
    # 디모데후서 (bookOrder=55): 2차 로마 투옥 / 순교
    ("rec28yVZWWOL1gftz", "authored-paul-rome-martyrdom"): {"bookOrder": 55, "verses": [(1, 1), (1, 2)]},
    # 디도서 (bookOrder=56): 석방기 목회서신
    ("recZJmtLFS2QnJG2b", "authored-paul-release-pastorals"): {"bookOrder": 56, "verses": [(1, 1), (1, 2), (1, 3)]},
    # 빌레몬서 (bookOrder=57): 첫 번째 로마 투옥
    ("recZm66X4kEQ7X3j2", "recGrIgOxWnxVl8h0"): {"bookOrder": 57, "verses": [(1, 1), (1, 2), (1, 3)]},
    # 야고보서 (bookOrder=59): 예루살렘 공의회
    ("recDk5A8p9VHMaXAC", "authored-paul-jerusalem-council"): {"bookOrder": 59, "verses": [(1, 1), (1, 2)]},
    # 베드로전서 (bookOrder=60): 베드로 로마 사역
    ("receVE4rg7HzwRays", "authored-peter-rome-martyrdom"): {"bookOrder": 60, "verses": [(1, 1), (1, 2)]},
    # 베드로후서 (bookOrder=61): 베드로 로마 사역
    ("recFNtUGO3RQUDGPv", "authored-peter-rome-martyrdom"): {"bookOrder": 61, "verses": [(1, 1), (1, 2)]},
    # 요한1서 (bookOrder=62): 요한 에베소 만년
    ("recnCKWpaf0b7Q1dy", "authored-john-ephesus-epistles"): {"bookOrder": 62, "verses": [(1, 1), (1, 2), (1, 3)]},
    # 요한2서 (bookOrder=63): 요한 에베소 만년
    ("recvfX2A1wSqR2QiC", "authored-john-ephesus-epistles"): {"bookOrder": 63, "verses": [(1, 1)]},
    # 요한3서 (bookOrder=64): 요한 에베소 만년
    ("recMApftYXBHE8lV5", "authored-john-ephesus-epistles"): {"bookOrder": 64, "verses": [(1, 1)]},
    # 유다서 (bookOrder=65): 거짓 교사 경계
    ("rec2ddtGk1mJxYoy4", "authored-jude-false-teachers"): {"bookOrder": 65, "verses": [(1, 1), (1, 2), (1, 3)]},
    # 요한계시록 (bookOrder=66): 밧모섬 유배
    ("recUbhyLLUrl849r7", "authored-john-patmos-revelation"): {"bookOrder": 66, "verses": [(1, 1), (1, 2), (1, 3)]},
}


def make_verse_id(book_order, chapter, verse):
    return f"{book_order:02d}{chapter:03d}{verse:03d}"


def build_range_label(verse_list):
    """[(chapter, verse), ...] → 연속 구간을 접은 rangeLabel."""
    # generate_event_verses.py의 build_range_label과 동일 로직
    parsed = [{"verseID": make_verse_id(0, ch, v), "chapter": ch, "verse": v}
              for ch, v in verse_list]
    runs = []
    for pv in parsed:
        if runs and int(pv["verseID"]) == int(runs[-1][1]["verseID"]) + 1:
            runs[-1] = (runs[-1][0], pv)
        else:
            runs.append((pv, pv))
    parts = []
    for start, end in runs:
        if start["verseID"] == end["verseID"]:
            parts.append(f"{start['chapter']}:{start['verse']}")
        elif start["chapter"] == end["chapter"]:
            parts.append(f"{start['chapter']}:{start['verse']}–{end['verse']}")
        else:
            parts.append(f"{start['chapter']}:{start['verse']}–{end['chapter']}:{end['verse']}")
    return ", ".join(parts)


def main():
    with open(BOOK_EVENTS_PATH, encoding="utf-8") as f:
        book_events = json.load(f)

    # 검증: VERSE_MAP의 모든 (bookId, eventId)가 book_events에 있는지
    for (book_id, event_id) in VERSE_MAP:
        if book_id not in book_events:
            print(f"[오류] bookId {book_id} not in book_events.json", file=sys.stderr)
            sys.exit(1)
        if event_id not in book_events[book_id]:
            print(f"[오류] eventId {event_id} not in book_events[{book_id}]", file=sys.stderr)
            sys.exit(1)

    # VERSE_MAP에서 book_events 커버 100% 확인
    missing = []
    for book_id, event_ids in book_events.items():
        for eid in event_ids:
            if (book_id, eid) not in VERSE_MAP:
                missing.append((book_id, eid))
    if missing:
        print(f"[경고] VERSE_MAP 미커버 {len(missing)}쌍:", file=sys.stderr)
        for pair in missing:
            print(f"  {pair}", file=sys.stderr)

    with open(EVENT_VERSES_PATH, encoding="utf-8") as f:
        event_verses = json.load(f)

    added = 0
    for (book_id, event_id), meta in VERSE_MAP.items():
        book_order = meta["bookOrder"]
        verse_pairs = meta["verses"]
        range_label = build_range_label(verse_pairs)
        verse_entries = [
            {"verseID": make_verse_id(book_order, ch, v), "chapter": ch, "verse": v}
            for ch, v in verse_pairs
        ]
        book_entry = {
            "bookId": book_id,
            "bookOrder": book_order,
            "rangeLabel": range_label,
            "verses": verse_entries,
        }
        entry = event_verses.setdefault(event_id, {"books": []})
        existing_ids = {b["bookId"] for b in entry["books"]}
        if book_id not in existing_ids:
            entry["books"].append(book_entry)
            # bookOrder 정경순 유지
            entry["books"].sort(key=lambda b: b["bookOrder"])
            added += 1

    with open(EVENT_VERSES_PATH, "w", encoding="utf-8") as f:
        json.dump(event_verses, f, ensure_ascii=False, indent=2)

    n_events = len(event_verses)
    n_with_books = sum(1 for v in event_verses.values() if v["books"])
    print(f"Done. {added}건 추가 → event_verses/events.json ({n_events} events, {n_with_books} with books)")


if __name__ == "__main__":
    main()
