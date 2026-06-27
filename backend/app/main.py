import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import nodes, events, search, books, persons, journey, places


@asynccontextmanager
async def lifespan(app):
    try:
        from .db import get_driver
        driver = get_driver()
        with driver.session() as session:
            for label in ['Person', 'Place', 'Event', 'PeopleGroup', 'Book']:
                session.run(
                    f"CREATE INDEX {label.lower()}_tid IF NOT EXISTS "
                    f"FOR (n:{label}) ON (n.theographic_id)"
                )
    except Exception:
        logging.exception("Neo4j 인덱스 생성 실패 — 인덱스 없이 계속 진행합니다")
    yield


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)
app.include_router(nodes.router)
app.include_router(events.router)
app.include_router(search.router)
app.include_router(books.router)
app.include_router(persons.router)
app.include_router(journey.router)
app.include_router(places.router)
