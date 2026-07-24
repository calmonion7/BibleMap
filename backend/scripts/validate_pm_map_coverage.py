"""비유·기적 색인의 지도↔연표 커버리지 간극을 고정한다 (task#251 S3).

배경: data/jesus_parables_miracles/index.json 65건 중, placeId(→place_coords 해석)나 직접
lat/lng을 가진 48건만 지도(pm-circle)에 뜨고, 좌표가 없는 17건("가르침" 비유)은 지도에서
조용히 누락된다(연표는 65건 전부 노출). 이 스크립트는 그 누락 집합을 정본으로 고정해,
예상 밖 항목이 지도에서 빠지거나(회귀) 새 placeId가 place_coords에서 해석되지 않으면 실패한다.

해석 로직은 backend/app/routes/events.py의 /parables-miracles와 동일:
  mappable = (placeId가 place_coords에 있고 lat/lng 보유) 또는 (항목 자체 lat/lng 보유).
"""
import json
import os

_DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")

# 좌표가 없어 지도에 얹지 못하는 "가르침" 비유·기적 정본 집합(task#251 기준 17건).
# 연표(TimelineView)는 전건 노출하므로 지도 UI가 "위치 없는 비유 N건은 연표에서"로 안내한다.
EXPECTED_UNMAPPABLE = {
    "barren-fig-tree", "deaf-mute-decapolis", "feeding-4000", "friend-at-midnight",
    "good-samaritan", "lost-coin", "lost-sheep", "man-with-dropsy", "persistent-widow",
    "pharisee-tax-collector", "prodigal-son", "rich-fool", "rich-man-lazarus",
    "ten-lepers", "two-debtors", "unjust-steward", "workers-in-vineyard",
}


def _place_coords():
    raw = json.load(open(os.path.join(_DATA, "place_coords", "places.json"), encoding="utf-8"))
    return {p["id"]: p for p in raw} if isinstance(raw, list) else raw


def main():
    items = json.load(open(os.path.join(_DATA, "jesus_parables_miracles", "index.json"), encoding="utf-8"))["items"]
    places = _place_coords()

    def mappable(it):
        pid = it.get("placeId")
        if pid and pid in places:
            p = places[pid]
            return p.get("lat") is not None and p.get("lng") is not None
        return it.get("lat") is not None and it.get("lng") is not None

    unmappable = {it["id"] for it in items if not mappable(it)}
    # placeId가 있는데 place_coords에서 해석되지 않는 항목(조용한 누락 위험) — 별도 신호.
    bad_place_id = {it["id"] for it in items if it.get("placeId") and it["placeId"] not in places and it.get("lat") is None}

    added = unmappable - EXPECTED_UNMAPPABLE      # 새로 지도에서 빠진 항목(회귀)
    removed = EXPECTED_UNMAPPABLE - unmappable     # 이제 지도에 뜨는 항목(정본 갱신 필요)

    assert not bad_place_id, f"placeId가 place_coords에서 미해석(조용한 지도 누락): {sorted(bad_place_id)}"
    assert not added, f"예상 밖 지도 누락(회귀): {sorted(added)} — 좌표를 채우거나 EXPECTED_UNMAPPABLE 갱신"
    assert not removed, f"이제 지도에 뜨는 항목: {sorted(removed)} — EXPECTED_UNMAPPABLE에서 제거 필요"

    print(f"검사: 총 {len(items)}건, 지도 노출 {len(items) - len(unmappable)}건 / 위치 없음 {len(unmappable)}건")
    print("PASS — 커버리지 정본 일치, 미해석 placeId 0")


if __name__ == "__main__":
    main()
