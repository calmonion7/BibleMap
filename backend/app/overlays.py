import functools
import json
import os

_REPO_DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "data",
)


def _resolve(subpath: str) -> "str | None":
    for base in (os.environ.get("DATA_DIR", "/app/data"), _REPO_DATA_DIR):
        path = os.path.join(base, subpath)
        if os.path.isfile(path):
            return path
    return None


def _resolve_dir(subpath: str) -> "str | None":
    for base in (os.environ.get("DATA_DIR", "/app/data"), _REPO_DATA_DIR):
        path = os.path.join(base, subpath)
        if os.path.isdir(path):
            return path
    return None


def _load(subpath: str) -> dict:
    path = _resolve(subpath)
    if path is None:
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}


@functools.lru_cache(maxsize=1)
def book_events_raw() -> dict:
    """{bookId: [eventId, ...]} 오버레이. 1회 로드 캐시."""
    return _load("book_events/books.json")


@functools.lru_cache(maxsize=1)
def event_verses() -> dict:
    """사건별 근거 구절 오버레이. 1회 로드 캐시."""
    return _load("event_verses/events.json")
