---
last_mapped_commit: 6bc79bba2bb1a869260e73efee7d9366d96a1cc0
mapped: 2026-06-20
---

# External Integrations

**Analysis Date:** 2026-06-20

## Data Storage

**Graph Database:**
- Neo4j 5 (Docker image `neo4j:5`)
  - Protocol: Bolt (`bolt://neo4j:7687` in production compose; `bolt://localhost:7687` in dev)
  - Connection: `backend/app/db.py` — module-level singleton driver via `get_driver()`
  - Auth env vars: `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`
  - Client library: `neo4j` 6.2.0 (Python driver)
  - Index creation at startup: `backend/app/main.py` lifespan handler creates `theographic_id` indexes on `Person`, `Place`, `Event`, `PeopleGroup`, `Book` labels

**File Storage:**
- Local filesystem only — data files under `data/` directory (mounted into API container as `/app/data`)
- Subdirectories: `authored_events/`, `book_context/`, `book_events/`, `book_years_approx/`, `character_traits/`, `event_verses/`, `names_ko/`, `person_events/`, `place_coords/`, `verse_events/`

**Caching:**
- None

## Maps & Tile Services

**Raster Tiles:**
- ESRI NatGeo World Map (no-key public endpoint)
  - URL pattern: `https://server.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}`
  - Used in: `frontend/src/MapView.jsx`

**Map Glyphs (fonts):**
- Protomaps public CDN
  - URL pattern: `https://protomaps.github.io/basemaps-assets/fonts/{fontstack}/{range}.pbf`
  - Used in: `frontend/src/MapView.jsx`

**Map Client:**
- MapLibre GL JS 5.24.0 (`maplibre-gl`) — renders tiles in WebGL; no API key required for the above sources

## AI / LLM (data pipeline scripts only)

**Anthropic Claude API:**
- Used exclusively in offline data-generation scripts; NOT called at runtime by the API server
- Scripts: `backend/scripts/generate_book_events.py`, `backend/scripts/generate_book_context.py`, `backend/scripts/generate_verse_events.py`, `backend/scripts/generate_person_traits.py`
- Client: `anthropic` Python SDK
- Model: `claude-haiku-4-5-20251001` (used in all four scripts)
- Auth env var: `ANTHROPIC_API_KEY` (read via `os.environ.get("ANTHROPIC_API_KEY")`)

## External Data Sources (data pipeline scripts only)

**Theographic Bible Metadata (GitHub raw):**
- Used in data-loading and generation scripts; fetched at pipeline runtime, not at API runtime
- Base URL: `https://raw.githubusercontent.com/robertrouse/theographic-bible-metadata/master/json/`
- Files fetched: `books.json`, `events.json`, `verses.json`, `people.json`, `places.json`, `peopleGroups.json`
- Scripts: `backend/scripts/load_theographic.py`, `backend/scripts/load_books.py`, `backend/scripts/generate_verse_events.py`, `backend/scripts/generate_event_verses.py`, `backend/scripts/generate_person_traits.py`, `backend/scripts/generate_book_context.py`

**GetBible API:**
- Fetches Bible verse text by book/chapter
- URL pattern: `https://api.getbible.net/v2/{slug}/{book_order}/{chapter}.json`
- Scripts: `backend/scripts/generate_verse_text.py`, `backend/scripts/generate_person_event_verses.py`
- No API key required

## Internal API

**Frontend → Backend:**
- All requests via `frontend/src/api.js` using the native `fetch` API
- Base URL: `VITE_API_URL` env var (`/api` in production, `http://localhost:8000` in dev)
- HTTP method: GET only (CORS configured for GET in `backend/app/main.py`)
- Routing: Nginx proxies `/api/` → `http://api:8000/` (strips `/api/` prefix)

## Authentication & Identity

**End-user auth:** None — the application has no login, session, JWT, or cookie mechanism.

**Service auth:**
- Neo4j: username/password via `NEO4J_USER` / `NEO4J_PASSWORD` env vars
- Anthropic: API key via `ANTHROPIC_API_KEY` env var (scripts only)

## Monitoring & Observability

**Error Tracking:** None detected

**Logs:**
- Backend uses Python `logging` module (`backend/app/main.py`); logs to stdout
- No structured log aggregation configured

## CI/CD & Deployment

**Hosting:** Docker Compose (local or self-hosted); no cloud provider configuration detected

**CI Pipeline:** None detected

## Webhooks & Callbacks

**Incoming:** None
**Outgoing:** None

---

*Integration audit: 2026-06-20*
