from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import nodes, places, events, search


@asynccontextmanager
async def lifespan(app):
    try:
        from .db import get_driver
        driver = get_driver()
        with driver.session() as session:
            for label in ['Person', 'Place', 'Event', 'PeopleGroup']:
                session.run(
                    f"CREATE INDEX {label.lower()}_tid IF NOT EXISTS "
                    f"FOR (n:{label}) ON (n.theographic_id)"
                )
    except Exception:
        pass
    yield


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(nodes.router)
app.include_router(places.router)
app.include_router(events.router)
app.include_router(search.router)
