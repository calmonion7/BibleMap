import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def _configure_logging():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    # chatty 서드파티는 WARNING 승격, uvicorn 로거는 root 중복 emit 차단
    for _noisy in ("neo4j", "urllib3", "asyncio"):
        logging.getLogger(_noisy).setLevel(logging.WARNING)
    # uvicorn/uvicorn.access는 자체 핸들러 보유 → root 중복 emit 차단.
    # uvicorn.error는 제외 — 자체 핸들러 없이 부모 uvicorn으로 전파해 출력하므로
    # propagate=False를 걸면 기동/에러 라인이 통째로 사라진다.
    for _uv in ("uvicorn", "uvicorn.access"):
        logging.getLogger(_uv).propagate = False


_configure_logging()  # import 시점(라우터 import 전) 1회

from .routes import nodes, events, search, books, persons, journey, places, tours, family, words, verses, reliance

logger = logging.getLogger(__name__)


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
        logger.exception("[Startup] Neo4j 인덱스 생성 실패 — 인덱스 없이 계속 진행")
    else:
        logger.info("[Startup] Neo4j 인덱스 준비 완료")
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
app.include_router(tours.router)
app.include_router(family.router)
app.include_router(words.router)
app.include_router(verses.router)
app.include_router(reliance.router)
