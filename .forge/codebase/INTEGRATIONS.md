---
last_mapped_commit: 7d2210c48a67b08b79cc3f03008c3ee30e885614
mapped: 2026-06-19
---

# Integrations

## Neo4j (Graph Database)

- **Image**: `neo4j:5` (docker-compose.yml)
- **Protocol**: Bolt
- **Internal URI** (Docker network): `bolt://neo4j:7687`
- **Local URI** (scripts): `bolt://localhost:7687`
- **Ports exposed to host**: `127.0.0.1:7474` (HTTP browser), `127.0.0.1:7687` (Bolt) — both loopback-only
- **Auth**: `NEO4J_AUTH=neo4j/<NEO4J_PASSWORD>` set via `docker-compose.yml`
- **Driver init**: `backend/app/db.py` — singleton `GraphDatabase.driver(uri, auth=(user, password))`
- **Data volume**: Docker named volume `neo4j_data:/data`
- **Indexes created at startup** (`backend/app/main.py` lifespan): `theographic_id` on `Person`, `Place`, `Event`, `PeopleGroup`, `Book`
- **Node labels used**: `Person`, `Place`, `Event`, `PeopleGroup`, `Book`
- **Relationships used**: `HAS_PARTICIPANT`, `OCCURS_AT`, `MEMBER_OF`, `CONTAINS_BOOK`, `PARENT_OF`, `SPOUSE_OF`

## Anthropic Claude API (Offline data generation only)

- **SDK**: `anthropic` Python package (imported in scripts, not in `backend/requirements.txt` — must be installed separately for script runs)
- **Model**: `claude-haiku-4-5-20251001` (used in `generate_book_context.py`, `generate_book_events.py`, `generate_person_traits.py`, `generate_verse_events.py`)
- **Auth**: `ANTHROPIC_API_KEY` environment variable (not set in `docker-compose.yml`; required only when running generation scripts)
- **Usage pattern**: batch offline generation; results written to `data/` JSON files and committed to repo (ADR-0006)
- **Calling scripts**:
  - `backend/scripts/generate_book_context.py` — per-book background/themes/keyVerse
  - `backend/scripts/generate_book_events.py` — book-to-event association
  - `backend/scripts/generate_person_traits.py` — person character traits
  - `backend/scripts/generate_verse_events.py` — verse-to-event mapping

## Theographic Bible Metadata (GitHub raw JSON, offline)

- **Source**: `https://raw.githubusercontent.com/robertrouse/theographic-bible-metadata/master/json/`
- **Files fetched**: `people.json`, `places.json`, `events.json`, `peopleGroups.json`, `verses.json`, `books.json`
- **Consumed by**: `backend/scripts/load_theographic.py`, `backend/scripts/generate_event_verses.py`, `backend/scripts/generate_person_traits.py`, `backend/scripts/generate_book_context.py`, `backend/scripts/generate_book_events.py`
- **Usage**: one-time data load into Neo4j; not called at runtime

## getBible API (Offline verse text pre-baking)

- **Endpoint pattern**: `https://api.getbible.net/v2/{translation}/{bookOrder}/{chapter}.json`
- **Translations used**: `korean` (Korean NKRV), `kjv` (English KJV)
- **Consumed by**: `backend/scripts/generate_verse_text.py`
- **Usage**: build-time pre-baking of verse text into `data/event_verses/events.json`, `data/book_context/books.json`, `data/character_traits/people.json` (ADR-0003); not called at runtime
- **Note**: requires browser-like User-Agent header to avoid 403 (documented in retro 2026-06-15)

## ESRI ArcGIS Online (Map tiles, runtime)

- **URL**: `https://server.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}`
- **Tile type**: raster, 256px
- **Consumed by**: `frontend/src/MapView.jsx` via `maplibre-gl` map style definition
- **Auth**: none (public endpoint)
- **Usage**: base map tiles fetched by the user's browser at runtime

## Protomaps Basemaps Assets (Map glyphs, runtime)

- **URL**: `https://protomaps.github.io/basemaps-assets/fonts/{fontstack}/{range}.pbf`
- **Consumed by**: `frontend/src/MapView.jsx` (`glyphs` field of maplibre-gl style)
- **Auth**: none (public CDN)
- **Usage**: map label fonts fetched by the user's browser at runtime

## Internal API (frontend → backend)

- **Base URL (dev)**: `http://localhost:8000` (default in `frontend/src/api.js`)
- **Base URL (prod)**: `/api` (set via `frontend/.env.production` → `VITE_API_URL=/api`; nginx proxies `/api/` → `http://api:8000/`)
- **Client**: `frontend/src/api.js` — shared `apiGet(path, {signal})` helper used by all frontend components
- **Endpoints**:
  - `GET /events` — timeline events list with book refs; `Cache-Control: max-age=300`
  - `GET /event/{event_id}/verses` — per-event verse groups; `Cache-Control: max-age=300`
  - `GET /books` — books with placement years; `Cache-Control: no-store`
  - `GET /node/{node_id}` — node detail (Person/Place/Event/PeopleGroup/Book)
  - `GET /node/{node_id}/places` — geographic locations for a node
  - `GET /node/{node_id}/neighbors/grouped` — grouped neighbors by label
  - `GET /person/{node_id}/event-ids` — event IDs a person participates in
  - `GET /search?q=` — full-text search across all node types (limit 20)

## Static Data Files (runtime overlay, mounted volume)

JSON files under `data/` are bind-mounted into the `api` container at `/app/data` and read at process startup (cached in-process thereafter):

| File | Consumed by |
|---|---|
| `data/event_verses/events.json` | `backend/app/routes/events.py` (`_load_event_verses`) |
| `data/book_events/books.json` | `backend/app/routes/events.py` (`_load_approx_book_index`), `backend/app/routes/books.py` (`_load_book_events`) |
| `data/book_years_approx/books.json` | `backend/app/routes/books.py` (`_load_approx`) |
