"""data/date_corrections/{events,persons}.json을 읽어 Neo4j에 연대 교정을 SET한다 (task#158 S3).

각 항목은 에코 필드(events: title/oldStartDate, persons: name/oldValue)를 갖는다.
멱등: DB 현재값이 에코와 불일치하면 그 항목은 스킵+경고 출력한다. 단, DB 현재값이
이미 new* 값과 일치하면(재실행) '이미 적용'으로 조용히 통과한다.
근거(ADR-0014)는 각 항목의 rationale 필드 참조.
"""

import json
import os
from pathlib import Path

from neo4j import GraphDatabase

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
if not NEO4J_PASSWORD:
    raise RuntimeError("NEO4J_PASSWORD 환경변수가 설정되지 않았습니다")

DATA_DIR = Path(__file__).parent.parent.parent / "data" / "date_corrections"


def load_json(filename):
    with open(DATA_DIR / filename, encoding="utf-8") as f:
        return json.load(f)


def inject_events(session, corrections):
    applied = already = skipped = 0
    for c in corrections:
        row = session.run(
            "MATCH (e:Event {theographic_id: $id}) RETURN e.title AS title, e.startDate AS startDate",
            id=c["id"],
        ).single()
        if row is None:
            print(f"[WARN] Event {c['id']} 미존재 — 스킵 ({c['title']})")
            skipped += 1
            continue
        if row["title"] != c["title"] or row["startDate"] != c["oldStartDate"]:
            if row["startDate"] == c["newStartDate"]:
                already += 1
                continue
            print(
                f"[WARN] Event {c['id']} 에코 불일치 — 스킵 "
                f"(DB title='{row['title']}' startDate='{row['startDate']}' "
                f"vs 항목 title='{c['title']}' oldStartDate='{c['oldStartDate']}')"
            )
            skipped += 1
            continue
        session.run(
            "MATCH (e:Event {theographic_id: $id}) "
            "SET e.startDate = $newStartDate, e.sortKey = $newSortKey",
            id=c["id"], newStartDate=c["newStartDate"], newSortKey=c["newSortKey"],
        )
        applied += 1
    return applied, already, skipped


def inject_persons(session, corrections):
    applied = already = skipped = 0
    for c in corrections:
        field = c["field"]
        row = session.run(
            f"MATCH (p:Person {{theographic_id: $id}}) "
            f"RETURN p.name AS name, p.{field} AS value",
            id=c["id"],
        ).single()
        if row is None:
            print(f"[WARN] Person {c['id']} 미존재 — 스킵 ({c['name']})")
            skipped += 1
            continue
        if row["name"] != c["name"] or str(row["value"]) != str(c["oldValue"]):
            if str(row["value"]) == str(c["newValue"]):
                already += 1
                continue
            print(
                f"[WARN] Person {c['id']} 에코 불일치 — 스킵 "
                f"(DB name='{row['name']}' {field}='{row['value']}' "
                f"vs 항목 name='{c['name']}' oldValue='{c['oldValue']}')"
            )
            skipped += 1
            continue
        session.run(
            f"MATCH (p:Person {{theographic_id: $id}}) SET p.{field} = $newValue",
            id=c["id"], newValue=c["newValue"],
        )
        applied += 1
    return applied, already, skipped


def main():
    events_corr = load_json("events.json")
    persons_corr = load_json("persons.json")

    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        with driver.session() as session:
            e_applied, e_already, e_skipped = inject_events(session, events_corr)
            p_applied, p_already, p_skipped = inject_persons(session, persons_corr)
    finally:
        driver.close()

    print(
        f"Event corrections applied:  {e_applied} "
        f"(이미 적용 {e_already}, 스킵 {e_skipped}) / 총 {len(events_corr)}"
    )
    print(
        f"Person corrections applied: {p_applied} "
        f"(이미 적용 {p_already}, 스킵 {p_skipped}) / 총 {len(persons_corr)}"
    )


if __name__ == "__main__":
    main()
