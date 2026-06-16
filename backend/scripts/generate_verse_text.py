"""세 생성 데이터(event_verses·book_context·character_traits)의 인용 절 본문을
빌드타임에 getbible에서 한국어(korean)+영어(kjv)로 받아 각 파일에 인라인 저장한다.

런타임 getbible 호출을 없애기 위한 미리굽기(ADR-0003). 앱이 표시하는 절 집합은 이 세
데이터에서 빌드타임에 완전히 결정되므로, 본문을 한 번 받아 함께 저장하면 런타임 외부
호출이 사라진다. 유니크 (번역, 책, 장)당 1회만 fetch·캐시하고, 이미 본문이 있는 항목은
스킵(멱등). 못 받은 본문은 null로 기록(재실행 시 재시도).

대상 파일과 추가 필드:
  event_verses/events.json      books[].verses[]   → textKo / textEn
  book_context/books.json       keyVerse("창 1:1") → keyVerseTextKo / keyVerseTextEn
  character_traits/people.json  traits[].verse_ref → verse_textKo / verse_textEn

book_context·character_traits는 개역 약어("창","마")를 canonical bookOrder로 해석한다
(SidePanel.jsx의 BOOK_ABBR_ORDER / resolveVerseRef를 포팅). 범위 참조는 첫 절만 쓴다.
event_verses의 verse 레코드는 bookOrder/chapter/verse가 이미 있어 파싱이 불필요하다.

사용법:
  python3 generate_verse_text.py
"""
import json
import os
import re
import urllib.request

# 본문 언어 → getbible v2 번역 슬러그. en 기본은 kjv(빌드 첫 실행에서 실호출로 검증, ADR-0003).
TRANSLATIONS = (("textKo", "korean"), ("textEn", "kjv"))

SCRIPT_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "..", "data"))
EVENT_VERSES_PATH = os.path.join(DATA_DIR, "event_verses", "events.json")
BOOK_CONTEXT_PATH = os.path.join(DATA_DIR, "book_context", "books.json")
TRAITS_PATH = os.path.join(DATA_DIR, "character_traits", "people.json")

# 개역 약어 → canonical bookOrder(1~66). SidePanel.jsx BOOK_ABBR_ORDER 포팅(단일 출처 이동).
BOOK_ABBR_ORDER = {
    "창": 1, "출": 2, "레": 3, "민": 4, "신": 5, "수": 6, "삿": 7, "룻": 8,
    "삼상": 9, "삼하": 10, "왕상": 11, "왕하": 12, "대상": 13, "대하": 14, "스": 15, "느": 16,
    "에": 17, "욥": 18, "시": 19, "잠": 20, "전": 21, "아": 22, "사": 23, "렘": 24,
    "애": 25, "겔": 26, "단": 27, "호": 28, "욜": 29, "암": 30, "옵": 31, "욘": 32,
    "미": 33, "나": 34, "합": 35, "습": 36, "학": 37, "슥": 38, "말": 39, "마": 40,
    "막": 41, "눅": 42, "요": 43, "행": 44, "롬": 45, "고전": 46, "고후": 47, "갈": 48,
    "엡": 49, "빌": 50, "골": 51, "살전": 52, "살후": 53, "딤전": 54, "딤후": 55, "딛": 56,
    "몬": 57, "히": 58, "약": 59, "벧전": 60, "벧후": 61, "요일": 62, "요이": 63, "요삼": 64,
    "유": 65, "계": 66,
}

# "창 1:1" / "창 6:4-5"에서 책 약어 + chapter + 첫 verse 추출. (SidePanel.jsx resolveVerseRef 포팅)
_REF_RE = re.compile(r"^\s*([^\d\s]+)\s*(\d+):(\d+)")

# getbible는 기본 urllib UA(Python-urllib)에 403을 준다 → 브라우저류 UA로 요청(curl은 통과, retro 2026-06-15 교훈).
_UA = "Mozilla/5.0 (compatible; BibleMap-build/1.0)"

# 장(chapter) JSON 캐시 — (slug, bookOrder, chapter) → {verse:int -> text}. 실패는 캐시 안 함(재시도 가능).
_chapter_cache = {}
_fetch_count = 0


def resolve_ref(ref):
    """'창 1:1' → (bookOrder, chapter, firstVerse). 약어 미매핑·형식 불일치 시 None."""
    if not ref:
        return None
    m = _REF_RE.match(ref)
    if not m:
        return None
    book_order = BOOK_ABBR_ORDER.get(m.group(1))
    if not book_order:
        return None
    return book_order, int(m.group(2)), int(m.group(3))


def fetch_chapter(slug, book_order, chapter):
    """(slug, bookOrder, chapter)의 장 JSON을 받아 {verse: text} 맵으로 캐시. 실패 시 None."""
    global _fetch_count
    key = (slug, book_order, chapter)
    if key in _chapter_cache:
        return _chapter_cache[key]
    url = f"https://api.getbible.net/v2/{slug}/{book_order}/{chapter}.json"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": _UA})
        with urllib.request.urlopen(req, timeout=30) as resp:
            d = json.loads(resp.read().decode("utf-8"))
        verses = {v["verse"]: v["text"] for v in d.get("verses", [])}
        _chapter_cache[key] = verses
        _fetch_count += 1
        if _fetch_count % 50 == 0:
            print(f"  ... {_fetch_count} chapters fetched")
        return verses
    except Exception as e:  # noqa: BLE001 — 외부 API 어떤 실패든 null 처리, 재시도 가능하게 캐시 안 함
        print(f"  ! fetch 실패 {url}: {e}")
        return None


def verse_text(slug, book_order, chapter, verse):
    verses = fetch_chapter(slug, book_order, chapter)
    if verses is None:
        return None
    return verses.get(verse)


def fill(obj, field, slug, resolved):
    """obj[field]가 없거나 null이면 본문을 받아 채운다(멱등). resolved 없으면 null 기록.
    반환: 'kept'|'filled'|'null' (통계용)."""
    if obj.get(field) is not None:
        return "kept"
    if resolved is None:
        obj[field] = None
        return "null"
    obj[field] = verse_text(slug, *resolved)
    return "filled" if obj[field] is not None else "null"


def bake_events():
    with open(EVENT_VERSES_PATH, encoding="utf-8") as f:
        data = json.load(f)
    stats = {"kept": 0, "filled": 0, "null": 0}
    for event in data.values():
        for book in event.get("books", []):
            order = book.get("bookOrder")
            for v in book.get("verses", []):
                resolved = (order, v["chapter"], v["verse"]) if order else None
                for field, slug in TRANSLATIONS:
                    stats[fill(v, field, slug, resolved)] += 1
    with open(EVENT_VERSES_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"event_verses: {stats}")
    return data


def bake_book_context():
    with open(BOOK_CONTEXT_PATH, encoding="utf-8") as f:
        data = json.load(f)
    stats = {"kept": 0, "filled": 0, "null": 0}
    for ctx in data.values():
        resolved = resolve_ref(ctx.get("keyVerse"))
        for src_field, slug in TRANSLATIONS:
            field = "keyVerseTextKo" if src_field == "textKo" else "keyVerseTextEn"
            stats[fill(ctx, field, slug, resolved)] += 1
    with open(BOOK_CONTEXT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"book_context: {stats}")
    return data


def bake_traits():
    with open(TRAITS_PATH, encoding="utf-8") as f:
        data = json.load(f)
    stats = {"kept": 0, "filled": 0, "null": 0}
    for person in data.values():
        for trait in person.get("traits", []):
            resolved = resolve_ref(trait.get("verse_ref"))
            for src_field, slug in TRANSLATIONS:
                field = "verse_textKo" if src_field == "textKo" else "verse_textEn"
                stats[fill(trait, field, slug, resolved)] += 1
    with open(TRAITS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"character_traits: {stats}")
    return data


def main():
    print("Baking book_context ...")
    books = bake_book_context()
    print("Baking character_traits ...")
    people = bake_traits()
    print("Baking event_verses (장 수 많음, 수 분 소요) ...")
    events = bake_events()
    print(f"\nDone. {_fetch_count} unique chapters fetched (캐시 적용).")

    # 육안 검증 — 알려진 절의 ko/en 본문 출력.
    print("\n[검증] book_context 창 1:1:")
    for ctx in books.values():
        if ctx.get("keyVerse") == "창 1:1":
            print(f"  ko: {ctx.get('keyVerseTextKo')}")
            print(f"  en: {ctx.get('keyVerseTextEn')}")
            break
    print("[검증] character_traits 마 9:36:")
    for person in people.values():
        for t in person.get("traits", []):
            if t.get("verse_ref") == "마 9:36":
                print(f"  ko: {t.get('verse_textKo')}")
                print(f"  en: {t.get('verse_textEn')}")
                break
        else:
            continue
        break
    print("[검증] event_verses 첫 사건 첫 절:")
    for event in events.values():
        if event.get("books") and event["books"][0].get("verses"):
            v0 = event["books"][0]["verses"][0]
            print(f"  {v0['chapter']}:{v0['verse']} ko: {v0.get('textKo')}")
            print(f"  {v0['chapter']}:{v0['verse']} en: {v0.get('textEn')}")
            break


if __name__ == "__main__":
    main()
