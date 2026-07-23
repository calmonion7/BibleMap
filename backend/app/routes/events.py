import functools

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from ..db import get_driver
from .. import overlays

router = APIRouter()


@functools.lru_cache(maxsize=1)
def _load_approx_book_index():
    """book_events_raw({bookId:[eventId]}) → 역방향 {eventId:[bookId]} + Neo4j Book 메타.
    반환: event_to_books: {eventId: [{id, nameKo, name, bookOrder}]}"""
    book_events = overlays.book_events_raw()
    if not book_events:
        return {}

    # Neo4j에서 책 메타 일괄 조회
    book_ids = list(book_events.keys())
    driver = get_driver()
    with driver.session() as session:
        rows = session.run(
            "MATCH (b:Book) WHERE b.theographic_id IN $ids "
            "RETURN b.theographic_id AS id, b.nameKo AS nameKo, "
            "b.name AS name, b.bookOrder AS bookOrder",
            ids=book_ids,
        ).data()
    book_meta = {r["id"]: r for r in rows}

    # 역방향 맵 구성
    event_to_books: dict = {}
    for book_id, event_ids in book_events.items():
        meta = book_meta.get(book_id)
        if meta is None:
            continue
        book_entry = {
            "id": meta["id"],
            "nameKo": meta["nameKo"],
            "name": meta["name"],
            "bookOrder": meta["bookOrder"],
        }
        for eid in event_ids:
            event_to_books.setdefault(eid, []).append(book_entry)

    # 각 이벤트의 책 목록 bookOrder 정렬
    for eid in event_to_books:
        event_to_books[eid].sort(key=lambda b: b["bookOrder"])

    return event_to_books


@functools.lru_cache(maxsize=1)
def _compute_events():
    """Neo4j 쿼리 + approx_index 머지. 앱 재시작 전까지 결과를 메모리에 보관."""
    approx_index = _load_approx_book_index()
    event_verses = overlays.event_verses()
    driver = get_driver()
    with driver.session() as session:
        result = session.run(
            "MATCH (e:Event) WHERE e.startDate IS NOT NULL "
            "OPTIONAL MATCH (b:Book)-[:CONTAINS_BOOK]->(e) "
            "WITH e, b ORDER BY b.bookOrder ASC "
            "WITH e, collect(CASE WHEN b IS NULL THEN NULL ELSE "
            "  {id: b.theographic_id, nameKo: b.nameKo, name: b.name, bookOrder: b.bookOrder} "
            "END) AS books "
            "RETURN e, books ORDER BY e.sortKey ASC"
        )
        events = []
        for record in result:
            props = dict(record["e"])
            event_id = props.get("theographic_id", "")
            contains_books = [b for b in record["books"] if b is not None]
            approx_books = approx_index.get(event_id, [])
            contains_ids = {b["id"] for b in contains_books}
            # 추정(⚡) 권은 그 (권,사건)이 event_verses에 근거 구절을 가질 때만 근거 칩에 합류
            # (구절 없는 집필 배경 연결은 책 마커 행 ⚡ 칩으로만 남는다 — CONTEXT.md 'Book Events')
            verse_book_ids = {
                b.get("bookId") for b in event_verses.get(event_id, {}).get("books", [])
            }
            extra = [
                b for b in approx_books
                if b["id"] not in contains_ids and b["id"] in verse_book_ids
            ]
            events.append({
                "id": event_id,
                "title": props.get("title", ""),
                "nameKo": props.get("nameKo"),
                "startDate": props.get("startDate", ""),
                "sortKey": float(props.get("sortKey", 0)),
                "authored": props.get("authored", False),
                "yearLabel": props.get("yearLabel"),
                "books": contains_books + extra,
            })
        return events


@router.get("/events")
def get_events():
    """타임라인 사건 목록. 각 사건에 그 사건을 기록한 성경권(CONTAINS_BOOK)을
    정경순(bookOrder ASC) books 배열로 함께 반환 — 사건의 근거 칩 표시용.
    추정책(집필 배경 연결)은 CONTAINS_BOOK 항목 뒤에 추가된다.
    사건 없는 권은 여기 등장하지 않는다(권→사건 방향이라 OPTIONAL은 사건 기준)."""
    return JSONResponse(content=_compute_events(), headers={"Cache-Control": "max-age=300"})


@functools.lru_cache(maxsize=1)
def _book_name_map() -> dict:
    """theographic_id → nameKo 전수 매핑. Neo4j 1회 조회 후 캐시."""
    driver = get_driver()
    with driver.session() as session:
        rows = session.run(
            "MATCH (b:Book) WHERE b.theographic_id IS NOT NULL "
            "RETURN b.theographic_id AS id, b.nameKo AS nameKo, b.name AS name"
        ).data()
    return {r["id"]: r["nameKo"] or r["name"] or r["id"] for r in rows}


@router.get("/covenants")
def get_covenants():
    """주요 언약 목록(task#247) — 연표를 가로지르는 주제 실. 각 언약의 keyVerseIds를
    정본 절 사전(bible_verses)으로 해석해 절 본문(한/영)을 keyVerses로 동봉한다."""
    bible = overlays.bible_verses()
    result = []
    for c in overlays.covenants().get("covenants", []):
        key_verses = [
            {"verseId": vid, "textKo": bible.get(vid, {}).get("textKo"), "textEn": bible.get(vid, {}).get("textEn")}
            for vid in c.get("keyVerseIds", [])
        ]
        result.append({**c, "keyVerses": key_verses})
    return JSONResponse(content=result, headers={"Cache-Control": "max-age=300"})


@router.get("/messianic-prophecies")
def get_messianic_prophecies():
    """메시아 예언↔성취 쌍 목록(task#246) — 주제(theme)별로 그룹핑. 각 쌍의 otVerseIds·
    ntVerseIds를 정본 절 사전(bible_verses)으로 해석해 절 본문(한/영)을 동봉한다."""
    bible = overlays.bible_verses()

    def resolve(ids):
        return [
            {"verseId": vid, "textKo": bible.get(vid, {}).get("textKo"), "textEn": bible.get(vid, {}).get("textEn")}
            for vid in ids
        ]

    themes: dict = {}
    for p in overlays.messianic_prophecies().get("prophecies", []):
        pair = {
            "id": p["id"],
            "otRangeLabel": p["otRangeLabel"],
            "ntRangeLabel": p["ntRangeLabel"],
            "note": p.get("note"),
            "otVerses": resolve(p.get("otVerseIds", [])),
            "ntVerses": resolve(p.get("ntVerseIds", [])),
        }
        themes.setdefault(p["theme"], []).append(pair)

    result = [{"theme": theme, "pairs": pairs} for theme, pairs in themes.items()]
    return JSONResponse(content=result, headers={"Cache-Control": "max-age=300"})


@router.get("/topical-verses")
def get_topical_verses():
    """주제별 큐레이션 성구 색인(task#250) — 믿음·사랑·용서 등 주제마다 verseIds를
    정본 절 사전(bible_verses)으로 해석해 절 본문(한/영)을 verses로 동봉한다."""
    bible = overlays.bible_verses()
    result = []
    for t in overlays.topical_verses().get("topics", []):
        verses = [
            {"verseId": vid, "textKo": bible.get(vid, {}).get("textKo"), "textEn": bible.get(vid, {}).get("textEn")}
            for vid in t.get("verseIds", [])
        ]
        result.append({**t, "verses": verses})
    return JSONResponse(content=result, headers={"Cache-Control": "max-age=300"})


@router.get("/parables-miracles")
def get_parables_miracles():
    """예수의 비유·기적 색인(task#249) — 지도·연표에 종류(type: parable|miracle)로 필터되는 레이어용.
    각 항목의 verseIds를 정본 절 사전(bible_verses)으로 해석해 절 본문(한/영)을 verses로 동봉하고,
    placeId가 있으면 place_coords 오버레이에서 lat/lng을 해석해 채운다(없으면 항목 자체 lat/lng 사용)."""
    bible = overlays.bible_verses()
    places = overlays.place_coords()
    result = []
    for item in overlays.parables_miracles().get("items", []):
        verses = [
            {"verseId": vid, "textKo": bible.get(vid, {}).get("textKo"), "textEn": bible.get(vid, {}).get("textEn")}
            for vid in item.get("verseIds", [])
        ]
        place_id = item.get("placeId")
        lat, lng = item.get("lat"), item.get("lng")
        if place_id and place_id in places:
            lat, lng = places[place_id].get("lat"), places[place_id].get("lng")
        result.append({**item, "lat": lat, "lng": lng, "verses": verses})
    return JSONResponse(content=result, headers={"Cache-Control": "max-age=300"})


@router.get("/event/{event_id}/verses")
def get_event_verses(event_id: str):
    """사건의 근거 구절을 권별로 그룹·정경순으로 반환(드릴다운용). 책 키 bookId는
    /events books의 id(theographic_id)와 일치. bookNameKo 추가(SidePanel 직접 표시용)."""
    overlay = overlays.event_verses()
    entry = overlay.get(event_id, {"books": []})
    name_map = _book_name_map()
    bible = overlays.bible_verses()
    enriched_books = []
    for b in entry.get("books", []):
        nb = {**b, "bookNameKo": name_map.get(b["bookId"], b["bookId"])}
        if "verses" in nb:
            # 본문은 오버레이가 아니라 정본 절 사전에서 합성(event_verses는 verseID 참조만 보유)
            nb["verses"] = [
                {**v,
                 "textKo": bible.get(v["verseID"], {}).get("textKo"),
                 "textEn": bible.get(v["verseID"], {}).get("textEn")}
                for v in nb["verses"]
            ]
        enriched_books.append(nb)
    # 오버레이 JSON 저장 순서에 의존하지 않고 라우트에서 정경순 강제(docstring 약속)
    enriched_books.sort(key=lambda b: b.get("bookOrder", 0))
    return JSONResponse(
        content={"books": enriched_books},
        headers={"Cache-Control": "max-age=300"},
    )
