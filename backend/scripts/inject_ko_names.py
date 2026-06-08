#!/usr/bin/env python3
"""Inject Korean name properties into Neo4j Person and Place nodes."""

import json
import os
from pathlib import Path

from neo4j import GraphDatabase

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "biblemap123")

DATA_DIR = Path(__file__).parent.parent.parent / "data" / "names_ko"


def load_json(filename):
    with open(DATA_DIR / filename, encoding="utf-8") as f:
        return json.load(f)


def inject(driver, label, mappings):
    query = (
        f"MATCH (p:{label} {{theographic_id: $id}}) "
        "SET p.nameKo = $ko, p.aliasesKo = $alias"
    )
    count = 0
    with driver.session() as session:
        for tid, data in mappings.items():
            result = session.run(query, id=tid, ko=data["ko"], alias=data["alias"])
            summary = result.consume()
            count += summary.counters.properties_set // 2
    return count


def main():
    people = load_json("people.json")
    places = load_json("places.json")

    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        person_count = inject(driver, "Person", people)
        place_count = inject(driver, "Place", places)
    finally:
        driver.close()

    print(f"Person nodes updated: {person_count}")
    print(f"Place nodes updated:  {place_count}")
    print(f"Total:                {person_count + place_count}")


if __name__ == "__main__":
    main()
