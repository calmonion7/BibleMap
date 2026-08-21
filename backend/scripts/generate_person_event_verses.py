"""data/person_events/*.json의 context 필드에서 구절 참조를 파싱해
books 필드를 추가하고 data/event_verses/events.json에 authored 항목을 머지한다.

출력:
  a) 각 data/person_events/<name>.json에 books: [{bookId, rangeLabel}] 인플레이스 추가
  b) data/event_verses/events.json에 authored event 항목 머지(기존 항목 유지)

멱등: books 필드가 이미 있는 이벤트는 스킵. event_verses 기존 항목도 유지.
"""
import json
import os
import re
import urllib.request
import glob as glob_module

SCRIPT_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "..", "data"))
PERSON_EVENTS_DIR = os.path.join(DATA_DIR, "person_events")
BOOKS_PATH = os.path.join(DATA_DIR, "names_ko", "books.json")
EVENT_VERSES_PATH = os.path.join(DATA_DIR, "event_verses", "events.json")
VERSES_PATH = os.path.join(DATA_DIR, "bible", "verses.json")

_UA = "Mozilla/5.0 (compatible; BibleMap-build/1.0)"
_chapter_cache: dict = {}
_fetch_count = 0

# 영어 약어 → bookOrder(1-66)
EN_ABBR_ORDER: dict = {
    "Gen": 1, "Exod": 2, "Lev": 3, "Num": 4, "Deut": 5,
    "Josh": 6, "Judg": 7, "Ruth": 8, "1Sam": 9, "2Sam": 10,
    "1Kgs": 11, "2Kgs": 12, "1Chr": 13, "2Chr": 14, "Ezra": 15,
    "Neh": 16, "Esth": 17, "Job": 18, "Ps": 19, "Prov": 20,
    "Eccl": 21, "Song": 22, "Isa": 23, "Jer": 24, "Lam": 25,
    "Ezek": 26, "Dan": 27, "Hos": 28, "Joel": 29, "Amos": 30,
    "Obad": 31, "Jonah": 32, "Mic": 33, "Nah": 34, "Hab": 35,
    "Zeph": 36, "Hag": 37, "Zech": 38, "Mal": 39,
    "Matt": 40, "Mark": 41, "Luke": 42, "John": 43, "Acts": 44,
    "Rom": 45, "1Cor": 46, "2Cor": 47, "Gal": 48, "Eph": 49,
    "Phil": 50, "Col": 51, "1Thess": 52, "2Thess": 53, "1Tim": 54,
    "2Tim": 55, "Titus": 56, "Phlm": 57, "Heb": 58, "Jas": 59,
    "1Pet": 60, "2Pet": 61, "1John": 62, "2John": 63, "3John": 64,
    "Jude": 65, "Rev": 66,
}

# 한국어 약어 → bookOrder(1-66). generate_verse_text.py BOOK_ABBR_ORDER 동일.
KO_ABBR_ORDER: dict = {
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


def build_lookups() -> dict:
    """books.json → {abbr: {bookId, bookOrder}} 통합 매핑."""
    books_raw = json.load(open(BOOKS_PATH, encoding="utf-8"))
    order_to_id = {i + 1: bid for i, bid in enumerate(books_raw.keys())}

    result: dict = {}
    for abbr, order in EN_ABBR_ORDER.items():
        result[abbr] = {"bookId": order_to_id[order], "bookOrder": order}
    for abbr, order in KO_ABBR_ORDER.items():
        result[abbr] = {"bookId": order_to_id[order], "bookOrder": order}
    return result


def _make_abbr_pattern(abbr_to_info: dict) -> re.Pattern:
    """약어를 긴 것 우선으로 정렬한 OR 패턴 컴파일."""
    abbrs = sorted(abbr_to_info.keys(), key=len, reverse=True)
    pat = "|".join(re.escape(a) for a in abbrs)
    return re.compile(pat)


def parse_context_refs(context: str, abbr_to_info: dict, abbr_pat: re.Pattern) -> list:
    """context 문자열 → [{bookId, bookOrder, rangeLabel}]

    rangeLabel이 범위의 유일한 직렬화다 — 절 전개는 이 라벨만 보고 expand_range_label이 한다.
    """
    results = []
    parens = re.findall(r"\(([^)]+)\)", context)

    for paren in parens:
        segments = re.split(r";", paren)
        last_abbr: str | None = None

        for seg in segments:
            seg = seg.strip()

            # 세그먼트 앞에서 책 약어 추출
            book_match = re.match(rf"^({abbr_pat.pattern})\s+(.+)", seg)
            if book_match:
                last_abbr = book_match.group(1)
                ref_part = book_match.group(2).strip()
            elif last_abbr and re.match(r"^\d", seg):
                # 이전 책 이어쓰기 (예: "Gen 16:6–14; 21:14–19"의 "21:14–19")
                ref_part = seg
            else:
                last_abbr = None
                continue

            if last_abbr not in abbr_to_info:
                continue

            # 장:절 파싱. 4가지 패턴 처리:
            #   "12:1–3"  ch:v1-v2
            #   "12:1"    ch:v1
            #   "12–15"   ch-chEnd (장 범위)
            #   "12"      ch만

            # 교차 장 범위 "4:19–5:12" 먼저 시도
            m_cross = re.match(r"^(\d+):(\d+)[–\-](\d+):(\d+)", ref_part)
            if m_cross:
                ch = int(m_cross.group(1))
                v1 = int(m_cross.group(2))
                ch_end_cross = int(m_cross.group(3))
                v2_cross = int(m_cross.group(4))
                # 종점 정보는 rangeLabel이 무손실로 담는다("4:19–5:12") — 별도 배관 불요.
                # 전개는 expand_range_label이 이 라벨만 보고 오프라인으로 수행한다.
                range_label = f"{ch}:{v1}–{ch_end_cross}:{v2_cross}"
                results.append({
                    "bookId": abbr_to_info[last_abbr]["bookId"],
                    "bookOrder": abbr_to_info[last_abbr]["bookOrder"],
                    "rangeLabel": range_label,
                })
                continue

            m = re.match(
                r"^(\d+)"
                r"(?::(\d+)(?:[–\-](\d+))?)?"
                r"(?:\s*[–\-]\s*(\d+))?장?",
                ref_part,
            )
            if not m:
                continue

            ch = int(m.group(1))
            v1 = int(m.group(2)) if m.group(2) else None
            v2 = int(m.group(3)) if m.group(3) else None
            ch_end = int(m.group(4)) if m.group(4) else None

            if v1 and v2:
                range_label = f"{ch}:{v1}–{v2}"
            elif v1:
                range_label = f"{ch}:{v1}"
            elif ch_end:
                range_label = f"{ch}–{ch_end}"
            else:
                range_label = str(ch)

            results.append({
                "bookId": abbr_to_info[last_abbr]["bookId"],
                "bookOrder": abbr_to_info[last_abbr]["bookOrder"],
                "rangeLabel": range_label,
            })

    return results


# ─────────────────────────────────────────────────────────────────────────────
# 범위 전개 — 오라클은 네트워크 원본이 아니라 정본 절 사전이다 (ADR 260821-125000)
#
# event_verses에 저장되는 절은 {verseID, chapter, verse} 참조뿐이고 본문은 응답 시점에
# GET /event/{id}/verses가 verses.json에서 다시 합성한다. 따라서 getbible에서 받아온
# 본문은 저장도 사용도 되지 않고 남는 역할은 "그 절이 존재하는가"라는 존재 오라클 하나뿐인데,
# 그 오라클은 이미 저장소 안에 있다 — verses.json은 BBCCCVVV 키 31,103개로 정경 전량을
# 담고 그 키 형식이 verseID와 같다. 그래서 전개는 오프라인·결정적이다(fetch 0회).
#
# 전개를 rangeLabel 구동으로 두는 이유: 라벨이 종점 정보를 무손실로 담으므로(교차-장
# "4:19–5:12", 장 단위 "29–31") 파싱 결과를 따로 배관할 필요가 없고, 검증기가 이 함수를
# 그대로 import해 **같은 오라클**로 판정할 수 있다(파서 2벌 금지 — ADR 260819-205242).
# 생성기와 검증기가 다른 진리원을 보면 검증기는 전개 버그가 아니라 두 원본의 차이를 잡는다.
#
# 존재 판정은 본문이 아니라 **키**로 한다. textKo가 null인 절이 19개 있어 "본문 비어있지
# 않음"으로 판정하면 정상 데이터를 위반으로 지목한다(거짓 빨강 — ADR 260821-000937).
# ─────────────────────────────────────────────────────────────────────────────

_verse_keys_cache: dict | None = None


def verse_keys_by_book() -> dict:
    """정본 절 사전의 verseID 키를 bookOrder별 집합으로 (프로세스 내 1회 로드)."""
    global _verse_keys_cache
    if _verse_keys_cache is None:
        with open(VERSES_PATH, encoding="utf-8") as f:
            keys = list(json.load(f).keys())
        cache: dict = {}
        for k in keys:
            cache.setdefault(int(k[:2]), set()).add(k)
        _verse_keys_cache = cache
    return _verse_keys_cache


def _segment_bounds(seg: str, book_order: int) -> tuple | None:
    """구간 문자열 → (하한 verseID, 상한 verseID). 파싱 불가 시 None.

    verseID가 BBCCCVVV 고정폭·단조라 사전식 비교로 범위 판정이 족하다.
    """
    def vid(c: int, v: int) -> str:
        return f"{book_order:02d}{c:03d}{v:03d}"

    m = re.fullmatch(r"(\d+):(\d+)-(\d+):(\d+)", seg)      # 교차-장  "4:19-5:12"
    if m:
        c1, v1, c2, v2 = (int(x) for x in m.groups())
        return vid(c1, v1), vid(c2, v2)
    m = re.fullmatch(r"(\d+):(\d+)-(\d+)", seg)             # 같은 장   "38:1-11"
    if m:
        c, v1, v2 = (int(x) for x in m.groups())
        return vid(c, v1), vid(c, v2)
    m = re.fullmatch(r"(\d+):(\d+)", seg)                    # 단일 절   "4:2"
    if m:
        c, v = (int(x) for x in m.groups())
        return vid(c, v), vid(c, v)
    m = re.fullmatch(r"(\d+)-(\d+)", seg)                    # 장 범위   "29-31"
    if m:
        c1, c2 = (int(x) for x in m.groups())
        return vid(c1, 1), vid(c2, 999)
    m = re.fullmatch(r"(\d+)", seg)                          # 장 전체   "19"
    if m:
        c = int(m.group(1))
        return vid(c, 1), vid(c, 999)
    return None


def expand_range_label(label: str, book_order: int, keys_by_book: dict | None = None) -> set | None:
    """rangeLabel → 그 범위 안에서 verses.json에 존재하는 verseID 집합. 파싱 불가 시 None.

    콤마로 구간을 여럿 적은 라벨("1:1–31, 2:1–3")도 각 구간을 합집합으로 전개한다.
    """
    text = (label or "").replace("–", "-").replace("—", "-").strip()
    if not text:
        return None
    present = (keys_by_book if keys_by_book is not None else verse_keys_by_book()).get(book_order, set())
    out: set = set()
    for seg in (x.strip() for x in text.split(",")):
        if not seg:
            continue
        bounds = _segment_bounds(seg, book_order)
        if bounds is None:
            return None
        lo, hi = bounds
        out |= {k for k in present if lo <= k <= hi}
    return out


def verses_for_label(label: str, book_order: int, keys_by_book: dict | None = None) -> list:
    """rangeLabel → 베이킹용 절 참조 [{verseID, chapter, verse}] (verseID 오름차순)."""
    ids = expand_range_label(label, book_order, keys_by_book)
    if ids is None:
        return []
    return [{"verseID": k, "chapter": int(k[2:5]), "verse": int(k[5:8])} for k in sorted(ids)]


# ─── 아래 getbible 경로는 과도기 비대칭으로 남아 있다 (ADR 260821-125000) ───
# 범위 전개가 오프라인으로 넘어간 뒤 이 두 함수는 **현재 어디서도 호출되지 않는다.**
# 걷어내지 않는 이유는 그 ADR의 수술적 범위(바꾸는 것은 범위 전개뿐) 때문이다 —
# 새 참조를 처음 베이킹할 때의 기존 흐름을 이 결정이 폐기하지는 않았다.
# 다시 쓰게 되면 verses.json에 없는 절을 근거로 만들 수 있음을 유의할 것: 화면 본문은
# verses.json에서 오므로 그런 절은 "근거 있음"으로 통과하면서 화면에는 빈 줄로 뜬다.


def fetch_chapter(slug: str, book_order: int, chapter: int) -> dict | None:
    """(slug, bookOrder, chapter) 장 JSON → {verse_num: text}. 실패 시 None."""
    global _fetch_count
    key = (slug, book_order, chapter)
    if key in _chapter_cache:
        return _chapter_cache[key]
    url = f"https://api.getbible.net/v2/{slug}/{book_order}/{chapter}.json"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": _UA})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        verse_map = {int(v["verse"]): v["text"] for v in data.get("verses", [])}
        _chapter_cache[key] = verse_map
        _fetch_count += 1
        return verse_map
    except Exception as exc:
        print(f"    [fetch 실패] {url}: {exc}")
        _chapter_cache[key] = None
        return None


def fetch_verses(book_order: int, chapter: int, v_start: int | None, v_end: int | None) -> list:
    """지정 범위 절 fetch → [{verseID, chapter, verse, textKo, textEn}]."""
    ko_map = fetch_chapter("korean", book_order, chapter)
    en_map = fetch_chapter("kjv", book_order, chapter)
    if ko_map is None and en_map is None:
        return []

    if v_start is None:
        # 절 지정 없으면 첫 절만
        verse_nums = [1]
    elif v_end is None:
        verse_nums = [v_start]
    else:
        verse_nums = list(range(v_start, v_end + 1))

    verses = []
    for vn in verse_nums:
        verse_id = f"{book_order:02d}{chapter:03d}{vn:03d}"
        text_ko = (ko_map or {}).get(vn)
        text_en = (en_map or {}).get(vn)
        if text_ko is None and text_en is None:
            continue
        verses.append({
            "verseID": verse_id,
            "chapter": chapter,
            "verse": vn,
            "textKo": text_ko,
            "textEn": text_en,
        })
    return verses


def process_event(ev: dict, abbr_to_info: dict, abbr_pat: re.Pattern) -> list:
    """이벤트 하나의 context → [{bookId, bookOrder, rangeLabel, verses}]."""
    context = ev.get("context", "")
    if not context:
        return []

    refs = parse_context_refs(context, abbr_to_info, abbr_pat)
    if not refs:
        return []

    keys = verse_keys_by_book()

    # 같은 bookId 중복 제거 (여러 세그먼트에서 같은 권 참조 시 첫 번째만)
    seen_book_ids: set = set()
    book_entries = []
    for ref in refs:
        bid = ref["bookId"]
        if bid in seen_book_ids:
            continue
        seen_book_ids.add(bid)

        # 라벨이 가리키는 범위 전량을 오프라인으로 전개한다 — 교차-장·장 단위도 첫 절만
        # 채우지 않는다(ADR 260821-125000). 네트워크 호출 0회.
        verses = verses_for_label(ref["rangeLabel"], ref["bookOrder"], keys)

        book_entries.append({
            "bookId": bid,
            "bookOrder": ref["bookOrder"],
            "rangeLabel": ref["rangeLabel"],
            "verses": verses,
        })

    return book_entries


def rebake_range_labels(dry_run: bool = False) -> int:
    """기존 event_verses 블록의 절 집합을 rangeLabel 범위로 재전개한다 (task#282 S2).

    main()의 멱등 스킵(`if "books" in ev: continue` · `if ev_id not in event_verses`)은
    생성기를 재실행해도 **이미 있는 블록을 갱신하지 않는다.** 그래서 라벨과 절이 어긋난
    기존 블록은 생성기를 몇 번 돌려도 고쳐지지 않는다 — 이 모드가 그 스킵을 우회한다.

    라벨과 절이 **어긋난 블록만** 고쳐 쓴다. 이미 정합인 블록은 손대지 않으므로
    부수 변경(예: 일부 블록에 남아 있는 textKo/textEn 잔여 필드 탈락)이 생기지 않는다.
    """
    keys = verse_keys_by_book()
    event_verses: dict = json.load(open(EVENT_VERSES_PATH, encoding="utf-8"))

    fixed = 0
    unparsed = []
    for ev_id in sorted(event_verses):
        for block in event_verses[ev_id].get("books", []):
            label = block.get("rangeLabel")
            book_order = block.get("bookOrder")
            expected = expand_range_label(label, book_order, keys)
            if expected is None:
                unparsed.append((ev_id, label))
                continue
            baked = {v["verseID"] for v in block.get("verses", [])}
            if baked == expected:
                continue
            print(f"  {ev_id} bk{book_order:02d} '{label}': {len(baked)}절 → {len(expected)}절")
            if not dry_run:
                block["verses"] = verses_for_label(label, book_order, keys)
            fixed += 1

    for ev_id, label in unparsed:
        print(f"  [파싱불가] {ev_id}: {label!r} — 손대지 않음")

    if fixed and not dry_run:
        with open(EVENT_VERSES_PATH, "w", encoding="utf-8") as f:
            json.dump(event_verses, f, ensure_ascii=False, indent=2)
        print(f"  event_verses/events.json 저장: {fixed}개 블록 재전개")
    elif fixed:
        print(f"  (dry-run) 재전개 대상 {fixed}개 블록")
    else:
        print("  재전개 대상 없음 — 모든 블록이 라벨 범위와 정합")
    return fixed


def main() -> None:
    abbr_to_info = build_lookups()
    abbr_pat = _make_abbr_pattern(abbr_to_info)

    # 기존 event_verses 로드
    event_verses: dict = json.load(open(EVENT_VERSES_PATH, encoding="utf-8"))
    ev_verses_updated = False

    person_event_files = sorted(glob_module.glob(os.path.join(PERSON_EVENTS_DIR, "*.json")))
    total_events = 0
    updated_events = 0
    total_books = 0
    no_refs = 0

    for fpath in person_event_files:
        fname = os.path.basename(fpath)
        events: list = json.load(open(fpath, encoding="utf-8"))
        file_changed = False

        for ev in events:
            total_events += 1

            # 멱등: 이미 books 필드가 있으면 스킵
            if "books" in ev:
                continue

            book_entries = process_event(ev, abbr_to_info, abbr_pat)
            ev_id = ev["id"]

            if not book_entries:
                no_refs += 1
                ev["books"] = []
                file_changed = True
                continue

            # person_events에 {bookId, rangeLabel}만 저장
            ev["books"] = [{"bookId": b["bookId"], "rangeLabel": b["rangeLabel"]} for b in book_entries]
            total_books += len(ev["books"])
            file_changed = True
            updated_events += 1

            # event_verses에 full 구조 머지 (기존 항목 유지)
            if ev_id not in event_verses:
                event_verses[ev_id] = {
                    "books": [
                        {
                            "bookId": b["bookId"],
                            "bookOrder": b["bookOrder"],
                            "rangeLabel": b["rangeLabel"],
                            "verses": b["verses"],
                        }
                        for b in book_entries
                    ]
                }
                ev_verses_updated = True

        if file_changed:
            with open(fpath, "w", encoding="utf-8") as f:
                json.dump(events, f, ensure_ascii=False, indent=2)
            print(f"  {fname}: 저장 완료")

    if ev_verses_updated:
        with open(EVENT_VERSES_PATH, "w", encoding="utf-8") as f:
            json.dump(event_verses, f, ensure_ascii=False, indent=2)
        print(f"  event_verses/events.json: authored 항목 추가됨")

    print(f"\n완료:")
    print(f"  처리 이벤트: {total_events}개")
    print(f"  books 추가: {updated_events}개 이벤트 ({total_books}개 권 참조)")
    print(f"  refs 없음: {no_refs}개 이벤트")
    print(f"  getbible fetch: {_fetch_count}회")


if __name__ == "__main__":
    import sys

    if "--rebake" in sys.argv:
        rebake_range_labels(dry_run="--dry-run" in sys.argv)
    else:
        main()
