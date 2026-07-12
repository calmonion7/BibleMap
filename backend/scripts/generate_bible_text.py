"""성경 전체 절 정본 사전(data/bible/verses.json) 프리베이크.

getbible v2에서 한국어(korean)+영어(kjv) 전체 번역본을 받아
verseID(BBCCCVVV, 책2+장3+절3 zero-pad) → {"textKo", "textEn"} 사전을 만든다.
event_verses 인라인 본문 제거(정규화)의 본문 공급원 — ADR-0003 프리베이크 원칙의 확장.

- 전체 번역본 단일 파일(https://api.getbible.net/v2/{slug}.json) 2회 fetch.
  # eco: 장 단위 2,378회 대신 전체본 2회 — 실패 시 재실행이 곧 재시도
- 기존 data/event_verses/events.json의 인라인 본문이 있으면 그 값을 우선한다
  (앱이 오늘 표시하는 본문과 바이트 동일 보장 — 골든 diff 게이트용). 불일치는 집계 보고.
- 멱등: 재실행 시 기존 verses.json의 non-null 본문은 유지.

사용법: python3 generate_bible_text.py
"""
import json
import os
import urllib.request

SCRIPT_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "..", "data"))
OUT_PATH = os.path.join(DATA_DIR, "bible", "verses.json")
EVENT_VERSES_PATH = os.path.join(DATA_DIR, "event_verses", "events.json")

TRANSLATIONS = (("textKo", "korean"), ("textEn", "kjv"))

# getbible는 기본 urllib UA에 403 → 브라우저류 UA (generate_verse_text.py와 동일 패턴)
_UA = "Mozilla/5.0 (compatible; BibleMap-build/1.0)"


def fetch_translation(slug):
    """전체 번역본 JSON → {verseID: text}."""
    url = f"https://api.getbible.net/v2/{slug}.json"
    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    out = {}
    for book in data["books"]:
        nr = book["nr"]
        for ch in book["chapters"]:
            for v in ch["verses"]:
                out[f"{nr:02d}{ch['chapter']:03d}{v['verse']:03d}"] = v["text"]
    print(f"  {slug}: {len(out)} verses")
    return out


def main():
    existing = {}
    if os.path.exists(OUT_PATH):
        with open(OUT_PATH, encoding="utf-8") as f:
            existing = json.load(f)
        print(f"기존 verses.json {len(existing)}절 로드(멱등 유지)")

    fetched = {field: fetch_translation(slug) for field, slug in TRANSLATIONS}

    all_ids = sorted(set(fetched["textKo"]) | set(fetched["textEn"]) | set(existing))
    verses = {}
    for vid in all_ids:
        prev = existing.get(vid, {})
        verses[vid] = {
            field: prev.get(field) if prev.get(field) is not None else fetched[field].get(vid)
            for field, _ in TRANSLATIONS
        }

    # 인라인 본문 우선(골든 diff 보장): event_verses의 기존 표시 본문과 다르면 인라인 값으로.
    mismatch = {"textKo": 0, "textEn": 0}
    inline_null = {"textKo": 0, "textEn": 0}
    with open(EVENT_VERSES_PATH, encoding="utf-8") as f:
        events = json.load(f)
    for event in events.values():
        for book in event.get("books", []):
            for v in book.get("verses", []):
                vid = v["verseID"]
                entry = verses.setdefault(vid, {"textKo": None, "textEn": None})
                for field, _ in TRANSLATIONS:
                    if field not in v:
                        continue  # 이미 정규화된(본문 없는) 파일 — 재실행 시
                    if v[field] is None:
                        if entry[field] is not None:
                            inline_null[field] += 1  # 인라인은 null인데 사전엔 본문 있음 → 보고만
                        continue
                    if entry[field] != v[field]:
                        mismatch[field] += 1
                        entry[field] = v[field]

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(verses, f, ensure_ascii=False, indent=2)

    n_ko = sum(1 for e in verses.values() if e["textKo"] is not None)
    n_en = sum(1 for e in verses.values() if e["textEn"] is not None)
    print(f"저장: {OUT_PATH} — 총 {len(verses)}절 (textKo {n_ko}, textEn {n_en})")
    print(f"인라인 우선 덮어씀(getbible과 불일치): {mismatch}")
    print(f"인라인 null인데 getbible 본문 존재(보고만, 사전은 본문 유지): {inline_null}")

    # 스팟체크: 창 1:1 / 요 3:16 / 계 22:21
    for vid, ko_kw, en_kw in (("01001001", "태초에", "In the beginning"),
                              ("43003016", "독생자", "only begotten"),
                              ("66022021", "은혜", "grace")):
        e = verses[vid]
        assert e["textKo"] and ko_kw in e["textKo"], f"스팟체크 실패 {vid} ko: {e['textKo']!r}"
        assert e["textEn"] and en_kw in e["textEn"], f"스팟체크 실패 {vid} en: {e['textEn']!r}"
    print("스팟체크 통과: 창1:1 · 요3:16 · 계22:21 (ko/en)")


if __name__ == "__main__":
    main()
