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
