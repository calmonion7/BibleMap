"""data/place_coords/places.json을 읽어 Place 노드를 Neo4j에 멱등 적재한다.

- authored-place-* ID: 신규 Place 노드를 MERGE해 좌표·이름 설정
- rec* ID: 기존 Place 노드의 좌표를 저작 좌표로 덮어씀 (저작 좌표가 정본)

**저작 좌표가 정본인 이유 (task#285 — 3차 버그 헌트 #5).** 종전에는 `WHERE pl.latitude IS NULL`로
"기존 값 보존"을 했는데, 업스트림 임포트(`load_theographic.py`)가 이미 모든 Place에 좌표를 채우므로
그 가드는 **상시 거짓**이었다 — 즉 이 파일에 손으로 적은 좌표 교정이 단 한 번도 반영된 적이 없고,
스크립트를 몇 번 다시 돌려도 에러·경고 없이 '스킵' 카운트만 올랐다. 실측: rec* 11건 전부 저작값과
DB가 불일치했고, 시내산은 저작(28.539)과 DB(29.5)가 위도 0.96°(≈107km) 어긋난 채 서빙되고 있었다.
이 파일은 업스트림 좌표를 고치려고 손으로 저작하는 교정 파일이므로, 충돌 시 저작값이 이긴다."""
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
    created = updated = unchanged = missing = 0

    with driver.session() as session:
        for p in places:
            pid = p["id"]
            if pid.startswith("authored-place-"):
                # 신규 Place 노드 생성
                session.run(
                    """
                    MERGE (pl:Place {theographic_id: $id})
                    SET pl.name     = $name,
                        pl.title    = $name,
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
                # 기존 Theographic Place — 저작 좌표로 덮어쓴다(저작값이 정본, docstring 참조).
                # 이미 저작값과 같으면 '변경 없음'으로 세어, 재실행이 조용히 무의미해지지 않게 한다.
                result = session.run(
                    """
                    MATCH (pl:Place {theographic_id: $id})
                    WITH pl, (pl.latitude <> $lat OR pl.longitude <> $lng) AS differs
                    SET pl.latitude = $lat, pl.longitude = $lng
                    RETURN count(pl) AS n, sum(CASE WHEN differs THEN 1 ELSE 0 END) AS changed
                    """,
                    id=pid,
                    lat=p["lat"],
                    lng=p["lng"],
                )
                row = result.single()
                if row["n"] == 0:
                    missing += 1  # places.json에 있는데 DB에 없는 id — 조용히 넘기지 않는다
                elif row["changed"] > 0:
                    updated += 1
                else:
                    unchanged += 1

    driver.close()
    print(f"완료 — 신규: {created}개  좌표 갱신: {updated}개  이미 일치: {unchanged}개  DB에 없음: {missing}개")
    assert missing == 0, (
        f"places.json의 rec* {missing}건이 Neo4j에 없다 — 저작 교정이 조용히 유실된다. "
        "id 오타이거나 업스트림에서 사라진 Place다."
    )


if __name__ == "__main__":
    main()
