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
def word_verse_index() -> dict:
    """구절↔단어 역색인 정본(단어(lemma) → [verseID, ...]). 1회 로드 캐시.
    build_word_verse_index.py 산출물. lemma 기반이라 substring 매칭과 커버리지가 다름."""
    return _load("word_verse_index/index.json")


@functools.lru_cache(maxsize=1)
def verse_persons() -> dict:
    """구절↔인물 색인 정본(verseID → [personRecId, ...]). 1회 로드 캐시.
    build_verse_persons.py 산출물(theographic verses.people 투영)."""
    return _load("verse_persons/index.json")
