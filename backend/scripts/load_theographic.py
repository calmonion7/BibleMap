import json
import os
import urllib.request

from neo4j import GraphDatabase

NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD")
if not NEO4J_PASSWORD:
    raise RuntimeError("NEO4J_PASSWORD 환경변수가 설정되지 않았습니다")

URLS = {
    "people":       "https://raw.githubusercontent.com/robertrouse/theographic-bible-metadata/master/json/people.json",
    "places":       "https://raw.githubusercontent.com/robertrouse/theographic-bible-metadata/master/json/places.json",
    "events":       "https://raw.githubusercontent.com/robertrouse/theographic-bible-metadata/master/json/events.json",
    "peopleGroups": "https://raw.githubusercontent.com/robertrouse/theographic-bible-metadata/master/json/peopleGroups.json",
}

BATCH_NODE = 500
BATCH_REL = 1000


def fetch_json(url):
    with urllib.request.urlopen(url) as resp:
        return json.loads(resp.read().decode("utf-8"))


def filter_published(records):
    # status 필드가 없는 엔티티(Event, PeopleGroup)는 전체 포함
    return [r for r in records if r.get("fields", {}).get("status", "publish") == "publish"]


def create_indexes(session):
    print("Creating indexes...")
    for cypher in [
        "CREATE INDEX person_tid IF NOT EXISTS FOR (n:Person) ON (n.theographic_id)",
        "CREATE INDEX place_tid IF NOT EXISTS FOR (n:Place) ON (n.theographic_id)",
        "CREATE INDEX event_tid IF NOT EXISTS FOR (n:Event) ON (n.theographic_id)",
        "CREATE INDEX pg_tid IF NOT EXISTS FOR (n:PeopleGroup) ON (n.theographic_id)",
    ]:
        session.run(cypher)
    print("Indexes created.")


def run_batched(session, cypher, rows, batch_size, param_key="rows"):
    for i in range(0, len(rows), batch_size):
        session.run(cypher, {param_key: rows[i:i + batch_size]})


def load_people(session, records):
    print(f"Loading {len(records)} Person nodes...")
    rows = []
    for r in records:
        f = r.get("fields", {})
        rows.append({
            "id":           r.get("id"),
            "name":         f.get("displayTitle"),
            "gender":       f.get("gender"),
            "birthYear":    f.get("birthYear"),
            "deathYear":    f.get("deathYear"),
            "displayTitle": f.get("displayTitle"),
            "slug":         f.get("slug"),
        })
    cypher = """
UNWIND $rows AS row
MERGE (p:Person {theographic_id: row.id})
SET p.name         = row.name,
    p.gender       = row.gender,
    p.birthYear    = row.birthYear,
    p.deathYear    = row.deathYear,
    p.displayTitle = row.displayTitle,
    p.slug         = row.slug
"""
    run_batched(session, cypher, rows, BATCH_NODE)
    print("Person nodes loaded.")


def load_places(session, records):
    print(f"Loading {len(records)} Place nodes...")
    rows = []
    for r in records:
        f = r.get("fields", {})
        rows.append({
            "id":             r.get("id"),
            "name":           f.get("kjvName") or f.get("displayTitle"),
            "latitude":       f.get("latitude"),
            "longitude":      f.get("longitude"),
            "featureType":    f.get("featureType"),
            "featureSubType": f.get("featureSubType"),
            "displayTitle":   f.get("displayTitle"),
        })
    cypher = """
UNWIND $rows AS row
MERGE (p:Place {theographic_id: row.id})
SET p.name           = row.name,
    p.latitude       = row.latitude,
    p.longitude      = row.longitude,
    p.featureType    = row.featureType,
    p.featureSubType = row.featureSubType,
    p.displayTitle   = row.displayTitle
"""
    run_batched(session, cypher, rows, BATCH_NODE)
    print("Place nodes loaded.")


def load_events(session, records):
    print(f"Loading {len(records)} Event nodes...")
    rows = []
    for r in records:
        f = r.get("fields", {})
        rows.append({
            "id":        r.get("id"),
            "title":     f.get("title"),
            "startDate": f.get("startDate"),
            "duration":  f.get("duration"),
            "sortKey":   f.get("sortKey"),
        })
    cypher = """
UNWIND $rows AS row
MERGE (e:Event {theographic_id: row.id})
SET e.title     = row.title,
    e.startDate = row.startDate,
    e.duration  = row.duration,
    e.sortKey   = row.sortKey
"""
    run_batched(session, cypher, rows, BATCH_NODE)
    print("Event nodes loaded.")


def load_people_groups(session, records):
    print(f"Loading {len(records)} PeopleGroup nodes...")
    rows = []
    for r in records:
        f = r.get("fields", {})
        rows.append({
            "id":           r.get("id"),
            "name":         f.get("displayTitle"),
            "displayTitle": f.get("displayTitle"),
        })
    cypher = """
UNWIND $rows AS row
MERGE (g:PeopleGroup {theographic_id: row.id})
SET g.name         = row.name,
    g.displayTitle = row.displayTitle
"""
    run_batched(session, cypher, rows, BATCH_NODE)
    print("PeopleGroup nodes loaded.")


def load_parent_child_rels(session, people_records):
    print("Loading PARENT_OF / CHILD_OF relationships...")
    pairs = []
    for r in people_records:
        child_id = r.get("id")
        f = r.get("fields", {})
        for parent_field in ("father", "mother"):
            parent_id = f.get(parent_field)
            if parent_id:
                pairs.append({"parentId": parent_id, "childId": child_id})
    cypher = """
UNWIND $pairs AS pair
MATCH (parent:Person {theographic_id: pair.parentId})
MATCH (child:Person  {theographic_id: pair.childId})
MERGE (parent)-[:PARENT_OF]->(child)
MERGE (child)-[:CHILD_OF]->(parent)
"""
    run_batched(session, cypher, pairs, BATCH_REL, param_key="pairs")
    print(f"PARENT_OF / CHILD_OF: {len(pairs)} pairs loaded.")


def load_sibling_rels(session, people_records):
    print("Loading SIBLING_OF relationships...")
    seen = set()
    pairs = []
    for r in people_records:
        a_id = r.get("id")
        siblings = r.get("fields", {}).get("siblings") or []
        for b_id in siblings:
            key = tuple(sorted([a_id, b_id]))
            if key not in seen:
                seen.add(key)
                pairs.append({"aId": key[0], "bId": key[1]})
    cypher = """
UNWIND $pairs AS pair
MATCH (a:Person {theographic_id: pair.aId})
MATCH (b:Person {theographic_id: pair.bId})
MERGE (a)-[:SIBLING_OF]-(b)
"""
    run_batched(session, cypher, pairs, BATCH_REL, param_key="pairs")
    print(f"SIBLING_OF: {len(pairs)} pairs loaded.")


def load_partner_rels(session, people_records):
    print("Loading PARTNER_OF relationships...")
    seen = set()
    pairs = []
    for r in people_records:
        a_id = r.get("id")
        partners = r.get("fields", {}).get("partners") or []
        for b_id in partners:
            key = tuple(sorted([a_id, b_id]))
            if key not in seen:
                seen.add(key)
                pairs.append({"aId": key[0], "bId": key[1]})
    cypher = """
UNWIND $pairs AS pair
MATCH (a:Person {theographic_id: pair.aId})
MATCH (b:Person {theographic_id: pair.bId})
MERGE (a)-[:PARTNER_OF]-(b)
"""
    run_batched(session, cypher, pairs, BATCH_REL, param_key="pairs")
    print(f"PARTNER_OF: {len(pairs)} pairs loaded.")


def load_member_of_rels(session, people_records):
    print("Loading MEMBER_OF relationships...")
    pairs = []
    for r in people_records:
        person_id = r.get("id")
        member_of = r.get("fields", {}).get("memberOf") or []
        for group_id in member_of:
            pairs.append({"personId": person_id, "groupId": group_id})
    cypher = """
UNWIND $pairs AS pair
MATCH (p:Person      {theographic_id: pair.personId})
MATCH (g:PeopleGroup {theographic_id: pair.groupId})
MERGE (p)-[:MEMBER_OF]->(g)
"""
    run_batched(session, cypher, pairs, BATCH_REL, param_key="pairs")
    print(f"MEMBER_OF: {len(pairs)} pairs loaded.")


def load_has_participant_rels(session, event_records):
    print("Loading HAS_PARTICIPANT relationships...")
    pairs = []
    for r in event_records:
        event_id = r.get("id")
        participants = r.get("fields", {}).get("participants") or []
        for person_id in participants:
            pairs.append({"eventId": event_id, "personId": person_id})
    cypher = """
UNWIND $pairs AS pair
MATCH (e:Event  {theographic_id: pair.eventId})
MATCH (p:Person {theographic_id: pair.personId})
MERGE (e)-[:HAS_PARTICIPANT]->(p)
"""
    run_batched(session, cypher, pairs, BATCH_REL, param_key="pairs")
    print(f"HAS_PARTICIPANT: {len(pairs)} pairs loaded.")


def load_occurs_at_rels(session, event_records):
    print("Loading OCCURS_AT relationships...")
    pairs = []
    for r in event_records:
        event_id = r.get("id")
        locations = r.get("fields", {}).get("locations") or []
        for place_id in locations:
            pairs.append({"eventId": event_id, "placeId": place_id})
    cypher = """
UNWIND $pairs AS pair
MATCH (e:Event {theographic_id: pair.eventId})
MATCH (p:Place {theographic_id: pair.placeId})
MERGE (e)-[:OCCURS_AT]->(p)
"""
    run_batched(session, cypher, pairs, BATCH_REL, param_key="pairs")
    print(f"OCCURS_AT: {len(pairs)} pairs loaded.")


def load_part_of_rels(session, event_records):
    print("Loading PART_OF relationships...")
    pairs = []
    for r in event_records:
        child_id = r.get("id")
        part_of = r.get("fields", {}).get("partOf") or []
        for parent_id in part_of:
            pairs.append({"childId": child_id, "parentId": parent_id})
    cypher = """
UNWIND $pairs AS pair
MATCH (child:Event  {theographic_id: pair.childId})
MATCH (parent:Event {theographic_id: pair.parentId})
MERGE (child)-[:PART_OF]->(parent)
"""
    run_batched(session, cypher, pairs, BATCH_REL, param_key="pairs")
    print(f"PART_OF: {len(pairs)} pairs loaded.")


if __name__ == "__main__":
    print("Fetching data from GitHub...")
    raw_people = fetch_json(URLS["people"])
    raw_places = fetch_json(URLS["places"])
    raw_events = fetch_json(URLS["events"])
    raw_groups = fetch_json(URLS["peopleGroups"])
    print("Fetch complete.")

    people = filter_published(raw_people)
    places = filter_published(raw_places)
    events = filter_published(raw_events)
    groups = filter_published(raw_groups)
    print(f"Published: {len(people)} people, {len(places)} places, {len(events)} events, {len(groups)} peopleGroups")

    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    with driver.session() as session:
        create_indexes(session)

        load_people(session, people)
        load_places(session, places)
        load_events(session, events)
        load_people_groups(session, groups)

        load_parent_child_rels(session, people)
        load_sibling_rels(session, people)
        load_partner_rels(session, people)
        load_member_of_rels(session, people)
        load_has_participant_rels(session, events)
        load_occurs_at_rels(session, events)
        load_part_of_rels(session, events)

    driver.close()
    print("Done.")
