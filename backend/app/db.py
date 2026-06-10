import os
from neo4j import GraphDatabase

_driver = None

def get_driver():
    global _driver
    if _driver is None:
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.environ.get("NEO4J_PASSWORD")
        if not password:
            raise RuntimeError("NEO4J_PASSWORD 환경변수가 설정되지 않았습니다")
        _driver = GraphDatabase.driver(uri, auth=(user, password))
    return _driver
