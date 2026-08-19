import functools
import json
import logging
import os

logger = logging.getLogger(__name__)

_REPO_DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "data",
)


def _resolve(subpath: str) -> "str | None":
    bases = (os.environ.get("DATA_DIR", "/app/data"), _REPO_DATA_DIR)
    for base in bases:
        path = os.path.join(base, subpath)
        if os.path.isfile(path):
            return path
    logger.warning("[Overlays] 오버레이 파일 없음 — 빈 데이터로 폴백 (%s, 시도: %s)", subpath, bases)
    return None


def _resolve_dir(subpath: str) -> "str | None":
    bases = (os.environ.get("DATA_DIR", "/app/data"), _REPO_DATA_DIR)
    for base in bases:
        path = os.path.join(base, subpath)
        if os.path.isdir(path):
            return path
    logger.warning("[Overlays] 오버레이 디렉터리 없음 — 빈 데이터로 폴백 (%s, 시도: %s)", subpath, bases)
    return None


def _load(subpath: str) -> dict:
    path = _resolve(subpath)
    if path is None:
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.warning("[Overlays] 오버레이 JSON 파싱 실패 — 빈 데이터로 폴백 (%s): %s", path, e)
        return {}


@functools.lru_cache(maxsize=1)
def book_events_raw() -> dict:
    """{bookId: [eventId, ...]} 오버레이. 1회 로드 캐시."""
    return _load("book_events/books.json")


@functools.lru_cache(maxsize=1)
def event_verses() -> dict:
    """사건별 근거 구절 오버레이. 1회 로드 캐시."""
    return _load("event_verses/events.json")


@functools.lru_cache(maxsize=1)
def bible_verses() -> dict:
    """정본 절 사전(verseID → {textKo, textEn}) 오버레이. 1회 로드 캐시."""
    return _load("bible/verses.json")


@functools.lru_cache(maxsize=1)
def word_distribution() -> dict:
    """책별 단어 분포 정본(bookId | "all" → {nameKo?, words}). 1회 로드 캐시."""
    return _load("word_distribution.json")


@functools.lru_cache(maxsize=1)
def books_ko() -> dict:
    """책 한글명·약칭 정본(theographic_id → {ko, alias}, 정경 순). 1회 로드 캐시."""
    return _load("names_ko/books.json")



@functools.lru_cache(maxsize=1)
def chapter_summaries() -> dict:
    """장 개요 정본(bookId → [{chapter, summary, keyVerseId}]) 오버레이. 1회 로드 캐시."""
    return _load("chapter_summaries/books.json")


@functools.lru_cache(maxsize=1)
def chapter_sections() -> dict:
    """장 묶음 정본(bookId → [{title, startChapter, endChapter}]) 오버레이. 1회 로드 캐시. 단장권은 부재."""
    return _load("chapter_sections/books.json")


@functools.lru_cache(maxsize=1)
def quotations() -> list:
    """구약↔신약 직접 인용 쌍 정본([{ntVerseIds, otVerseIds, ntRangeLabel, otRangeLabel, note?}]). 1회 로드 캐시."""
    return _load("quotations/quotations.json").get("quotations", [])


@functools.lru_cache(maxsize=1)
def messianic_prophecies() -> dict:
    """메시아 예언↔성취 정본({"prophecies": [{id, theme, otVerseIds, ntVerseIds, otRangeLabel, ntRangeLabel, note}]}). 1회 로드 캐시."""
    return _load("messianic_prophecies/prophecies.json")


@functools.lru_cache(maxsize=1)
def covenants() -> dict:
    """주요 언약 정본({"covenants": [{id, name, nameEn, parties, promise, sign, keyVerseIds, startDate, era}]}). 1회 로드 캐시."""
    return _load("covenants/covenants.json")


@functools.lru_cache(maxsize=1)
def parables_miracles() -> dict:
    """예수의 비유·기적 색인 정본({"items": [{id, type, name, placeName, placeId, lat, lng, verseIds, note}]}). 1회 로드 캐시."""
    return _load("jesus_parables_miracles/index.json")


@functools.lru_cache(maxsize=1)
def place_coords() -> dict:
    """저작 장소 좌표 정본(id → {name, nameKo, lat, lng, note}). place_coords/places.json 리스트를
    id 키 dict로 변환. 1회 로드 캐시."""
    raw = _load("place_coords/places.json")
    return raw if isinstance(raw, dict) else {p["id"]: p for p in raw}


@functools.lru_cache(maxsize=1)
def place_context() -> dict:
    """장소 컨텍스트 정본(id → {background, keyVerse, keyVerseTextKo, keyVerseTextEn}). 1회 로드 캐시.
    Neo4j 주입본(inject_place_context.py)과 같은 파일을 읽는다 — 장소 페이지(task#270)의 단일 출처."""
    return _load("place_context/places.json")


@functools.lru_cache(maxsize=1)
def topical_verses() -> dict:
    """주제별 큐레이션 성구 정본({"topics": [{id, name, description, verseIds}]}). 1회 로드 캐시."""
    return _load("topical_verses/topics.json")


@functools.lru_cache(maxsize=1)
def verse_persons() -> dict:
    """구절↔인물 색인 정본(verseID → [personRecId, ...]). 1회 로드 캐시.
    build_verse_persons.py 산출물(theographic verses.people 투영)."""
    return _load("verse_persons/index.json")


def curated_person_id(events: list) -> str | None:
    """큐레이션 신원 규약의 단일 지점 — person_events/<slug>.json의 events[0].participants[0]이
    그 인물의 theographic_id (파일 내 모든 이벤트의 첫 participant 동일 검증 완료).
    소비처: persons.py·places.py·reliance.py (load_theographic.py 스크립트는 자체 구현 — 앱 미임포트 관행)."""
    if not events or not events[0].get("participants"):
        return None
    return events[0]["participants"][0]
