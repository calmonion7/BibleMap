"""중복 이벤트 실삭제 적용 — data/event_dedupe/dedupe.json 대장 기반, 멱등 (task#168, ADR-0016).

클러스터별로: ① remove의 연결(PART_OF 부모/자식·OCCURS_AT·HAS_PARTICIPANT·CONTAINS_BOOK)을
keep으로 이관 ② keep의 근거 절이 비어 있으면 remove의 verseID 참조 이관(구절 근거 원칙)
③ data/ 원천·참조 정리(person_events·verse_events·authored_events 엔트리 제거, tours·book_events
리매핑, names_ko·date_corrections 고아 정리) ④ 그래프 DETACH DELETE.

파이프라인 재적재(load_*) 후 재실행하면 중복이 다시 제거된다(멱등 — 이미 없는 것은 skip).
Neo4j 접속: NEO4J_URI(기본 bolt://neo4j:7687, 호스트에선 bolt://localhost:7687), NEO4J_PASSWORD.

사용법: python3 apply_event_dedupe.py
"""
import json
import os

from neo4j import GraphDatabase

SCRIPT_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "..", "data"))
LEDGER_PATH = os.path.join(DATA_DIR, "event_dedupe", "dedupe.json")

URI = os.environ.get("NEO4J_URI", "bolt://neo4j:7687")
PASSWORD = os.environ["NEO4J_PASSWORD"]


def load_json(rel):
    with open(os.path.join(DATA_DIR, rel), encoding="utf-8") as f:
        return json.load(f)


def save_json(rel, data):
    with open(os.path.join(DATA_DIR, rel), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def transfer_and_delete(session, keep, remove_ids):
    """remove들의 연결을 keep으로 이관 후 DETACH DELETE. 반환: 실제 삭제 수."""
    deleted = 0
    for rid in remove_ids:
        exists = session.run(
            "MATCH (r:Event {theographic_id: $rid}) RETURN count(r) AS n", rid=rid
        ).single()["n"]
        if not exists:
            continue  # 멱등 — 이미 삭제됨
        session.run(
            """
            MATCH (r:Event {theographic_id: $rid}), (k:Event {theographic_id: $kid})
            // 나가는 연결 이관 (자기참조 제외)
            CALL (r, k) {
              MATCH (r)-[:PART_OF]->(p) WHERE p <> k
              MERGE (k)-[:PART_OF]->(p)
            }
            CALL (r, k) {
              MATCH (r)-[:OCCURS_AT]->(pl)
              MERGE (k)-[:OCCURS_AT]->(pl)
            }
            CALL (r, k) {
              MATCH (r)-[:HAS_PARTICIPANT]->(per)
              MERGE (k)-[:HAS_PARTICIPANT]->(per)
            }
            // 들어오는 PART_OF(자식) 재지향
            CALL (r, k) {
              MATCH (c:Event)-[:PART_OF]->(r) WHERE c <> k
              MERGE (c)-[:PART_OF]->(k)
            }
            // 기록 책: keep에 없는 책 연결은 인용(primary:false)으로 이관
            CALL (r, k) {
              MATCH (b:Book)-[rel:CONTAINS_BOOK]->(r)
              WHERE NOT (b)-[:CONTAINS_BOOK]->(k)
              CREATE (b)-[:CONTAINS_BOOK {primary: false}]->(k)
            }
            DETACH DELETE r
            """,
            rid=rid, kid=keep,
        )
        deleted += 1
    return deleted


def main():
    ledger = load_json("event_dedupe/dedupe.json".replace("/", os.sep))
    clusters = ledger["clusters"]
    all_removes = [r["id"] for c in clusters for r in c["remove"]]
    print(f"대장: 클러스터 {len(clusters)}, 제거 대상 {len(all_removes)}")

    # --- ① 구절 이관 + 고아 정리 (event_verses) ---
    ev = load_json("event_verses/events.json")
    verses_moved = orphans = 0
    for c in clusters:
        kid = c["keepId"]
        keep_entry = ev.get(kid)
        keep_has = keep_entry and any(b.get("verses") for b in keep_entry.get("books", []))
        if not keep_has:
            # keep의 빈 books(구절 없는 자리표시)는 버리고 remove의 실구절 books로 대체
            merged_books = []
            for r in c["remove"]:
                rent = ev.get(r["id"])
                if rent and any(b.get("verses") for b in rent.get("books", [])):
                    merged_books.extend(b for b in rent["books"] if b.get("verses"))
                    verses_moved += 1
            if merged_books:
                ev[kid] = {"books": merged_books}
    for rid in all_removes:
        if rid in ev:
            del ev[rid]
            orphans += 1
    if verses_moved or orphans:
        save_json("event_verses/events.json", ev)
    print(f"event_verses: 구절 이관 {verses_moved}건(keep 절 공백 채움), 고아 엔트리 제거 {orphans}건")

    # --- ② 원천 파일에서 저작 계열 제거 (재적재해도 안 생김) ---
    removed_src = 0
    for fname in sorted(os.listdir(os.path.join(DATA_DIR, "person_events"))):
        rel = os.path.join("person_events", fname)
        events = load_json(rel)
        kept = [e for e in events if e["id"] not in all_removes]
        if len(kept) != len(events):
            removed_src += len(events) - len(kept)
            save_json(rel, kept)
    ve = load_json("verse_events/events.json")
    kept_ve = [e for e in ve["events"] if e["id"] not in all_removes]
    if len(kept_ve) != len(ve["events"]):
        removed_src += len(ve["events"]) - len(kept_ve)
        ve["events"] = kept_ve
        save_json("verse_events/events.json", ve)
    ae = load_json("authored_events/events.json")
    kept_ae = [e for e in ae if e["id"] not in all_removes]
    if len(kept_ae) != len(ae):
        removed_src += len(ae) - len(kept_ae)
        save_json("authored_events/events.json", kept_ae)
    print(f"원천(person_events/verse_events/authored_events) 엔트리 제거: {removed_src}건")

    # --- ③ 참조 리매핑: tours(stops), book_events(목록) ---
    keep_of = {r["id"]: c["keepId"] for c in clusters for r in c["remove"]}
    remapped = 0
    for fname in sorted(os.listdir(os.path.join(DATA_DIR, "tours"))):
        rel = os.path.join("tours", fname)
        tour = load_json(rel)
        new_stops, seen = [], set()
        for s in tour.get("stops", []):
            # 스톱은 {id, note} 객체(ADR-0028) — id만 리매핑·디듀프하고 note는 보존
            sid = keep_of.get(s["id"], s["id"])
            if sid not in seen:
                new_stops.append({**s, "id": sid})
                seen.add(sid)
        if new_stops != tour.get("stops", []):
            remapped += 1
            tour["stops"] = new_stops
            save_json(rel, tour)
    be = load_json("book_events/books.json")
    be_changed = False
    for bid, ids in be.items():
        new_ids, seen = [], set()
        for i in ids:
            i2 = keep_of.get(i, i)
            if i2 not in seen:
                new_ids.append(i2)
                seen.add(i2)
        if new_ids != ids:
            be[bid] = new_ids
            be_changed = True
    if be_changed:
        save_json("book_events/books.json", be)
    print(f"리매핑: tours 파일 {remapped}건 갱신, book_events {'갱신' if be_changed else '변경 없음'}")

    # --- ④ 고아 정리: names_ko(사전), date_corrections(교정) ---
    nk = load_json("names_ko/events.json")
    nk_removed = [k for k in list(nk) if k in set(all_removes)]
    for k in nk_removed:
        del nk[k]
    if nk_removed:
        save_json("names_ko/events.json", nk)
    dc = load_json("date_corrections/events.json")
    kept_dc = [e for e in dc if e["id"] not in all_removes]
    if len(kept_dc) != len(dc):
        save_json("date_corrections/events.json", kept_dc)
    print(f"고아 정리: names_ko {len(nk_removed)}건, date_corrections {len(dc) - len(kept_dc)}건")

    # --- ⑤ 그래프: 연결 이관 → DETACH DELETE ---
    driver = GraphDatabase.driver(URI, auth=("neo4j", PASSWORD))
    with driver.session() as s:
        before = s.run("MATCH (e:Event) RETURN count(e) AS n").single()["n"]
        deleted = 0
        for c in clusters:
            deleted += transfer_and_delete(s, c["keepId"], [r["id"] for r in c["remove"]])
        after = s.run("MATCH (e:Event) RETURN count(e) AS n").single()["n"]
        remaining = s.run(
            "MATCH (e:Event) WHERE e.theographic_id IN $ids RETURN count(e) AS n",
            ids=all_removes,
        ).single()["n"]
    driver.close()
    print(f"그래프: {before} → {after} (이번 실행 삭제 {deleted}), removed-id 잔존 {remaining}")
    assert remaining == 0, "removed id가 그래프에 잔존"
    assert after == before - deleted


if __name__ == "__main__":
    main()
