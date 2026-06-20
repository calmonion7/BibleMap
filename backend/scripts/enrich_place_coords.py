"""data/place_coords/places.json을 읽어 Place 노드를 Neo4j에 멱등 적재한다.

- authored-place-* ID: 신규 Place 노드를 MERGE해 좌표·이름 설정
- rec* ID: 기존 Place 노드 좌표가 없을 때만 SET (기존 값 보존)"""
import json
import os

from neo4j import GraphDatabase

NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD")
if not NEO4J_PASSWORD:
    raise RuntimeError("NEO4J_PASSWORD 환경변수가 설정되지 않았습니다")

SCRIPT_DIR = os.path.dirname(__file__)
PLACES_PATH = os.path.normpath(
    os.path.join(SCRIPT_DIR, "..", "..", "data", "place_coords", "places.json")
)


def main():
    with open(PLACES_PATH, encoding="utf-8") as f:
        places = json.load(f)

    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    created = updated = skipped = 0

    with driver.session() as session:
        for p in places:
            pid = p["id"]
            if pid.startswith("authored-place-"):
                # 신규 Place 노드 생성
                session.run(
                    """
                    MERGE (pl:Place {theographic_id: $id})
                    SET pl.title    = $name,
                        pl.nameKo   = $nameKo,
                        pl.latitude  = $lat,
                        pl.longitude = $lng,
                        pl.note      = $note,
                        pl.authored  = true
                    """,
                    id=pid,
                    name=p["name"],
                    nameKo=p.get("nameKo"),
                    lat=p["lat"],
                    lng=p["lng"],
                    note=p.get("note", ""),
                )
                created += 1
            else:
                # 기존 Theographic Place — 좌표 없는 경우에만 업데이트
                result = session.run(
                    """
                    MATCH (pl:Place {theographic_id: $id})
                    WHERE pl.latitude IS NULL
                    SET pl.latitude = $lat, pl.longitude = $lng
                    RETURN count(pl) AS n
                    """,
                    id=pid,
                    lat=p["lat"],
                    lng=p["lng"],
                )
                n = result.single()["n"]
                if n > 0:
                    updated += 1
                else:
                    skipped += 1

    driver.close()
    print(f"완료 — 신규: {created}개  좌표 추가: {updated}개  스킵(기존 좌표 있음): {skipped}개")


if __name__ == "__main__":
    main()
