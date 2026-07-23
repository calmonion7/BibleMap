"""예수의 비유·기적 색인 정본(data/jesus_parables_miracles/index.json)을 기계 검증한다 (task#249 S1).

검증 항목:
  a) verseId 전수 실존 — 정본 절 사전(data/bible/verses.json) 대조
  b) type은 "parable"|"miracle" 중 하나
  c) placeId가 있으면 place_coords/places.json에 실존
  d) id 유일
  e) 비유 25~35건, 기적 25~40건

위반이 있으면 목록을 출력하고 종료 코드 1.
"""
import json
import os
import sys

_DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")


def main():
    verses = json.load(open(os.path.join(_DATA, "bible", "verses.json"), encoding="utf-8"))
    places = {p["id"] for p in json.load(open(os.path.join(_DATA, "place_coords", "places.json"), encoding="utf-8"))}
    items = json.load(open(os.path.join(_DATA, "jesus_parables_miracles", "index.json"), encoding="utf-8"))["items"]

    violations = []
    seen_ids = set()
    parable_count = miracle_count = 0
    for i, e in enumerate(items):
        tag = f"[{i}] {e.get('id')}"
        for vid in e.get("verseIds", []):
            if vid not in verses:
                violations.append(f"{tag}: verseId 미실존 {vid}")
        if e.get("type") not in ("parable", "miracle"):
            violations.append(f"{tag}: type 불량 {e.get('type')}")
        elif e["type"] == "parable":
            parable_count += 1
        else:
            miracle_count += 1
        if e.get("placeId") and e["placeId"] not in places:
            violations.append(f"{tag}: placeId 미실존 {e['placeId']}")
        eid = e.get("id")
        if eid in seen_ids:
            violations.append(f"{tag}: id 중복")
        seen_ids.add(eid)

    if not (25 <= parable_count <= 35):
        violations.append(f"비유 수 {parable_count}건 — 25~35 범위 밖")
    if not (25 <= miracle_count <= 40):
        violations.append(f"기적 수 {miracle_count}건 — 25~40 범위 밖")

    print(f"검사: {len(items)}건 (비유 {parable_count}, 기적 {miracle_count})")
    if violations:
        print(f"FAIL — 위반 {len(violations)}건")
        for v in violations[:40]:
            print(" -", v)
        sys.exit(1)
    print("PASS — 탈락 0")


if __name__ == "__main__":
    main()
