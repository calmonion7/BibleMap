---
last_mapped_commit: fb78d740df63d386e84ceb1bb4249921a5e198b7
mapped: 2026-06-14
---

# External Integrations

**Analysis Date:** 2026-06-14

## Data Storage

**Graph Database:**
- Neo4j 5 (Docker image `neo4j:5`)
  - Connection: Bolt protocol at `bolt://neo4j:7687` (Docker internal) or `bolt://localhost:7687` (local)
  - Client: `neo4j` Python driver 6.2.0 (`backend/app/db.py`)
  - Auth env vars: `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`
  - Driver singleton: `get_driver()` in `backend/app/db.py`
  - Indexes: created at startup via FastAPI lifespan in `backend/app/main.py` (on `theographic_id` for Person, Place, Event, PeopleGroup)
  - Data volume: `neo4j_data` (Docker named volume, persisted on host)

**File Storage:**
- Local filesystem only — static JSON files in `data/names_ko/` (people, places, events, groups)
- Frontend build output: `frontend/dist/` (served by nginx as static files)

**Caching:**
- None

## APIs & External Services

**Map Tiles — ESRI:**
- Raster tile endpoint: `https://server.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}`
- Consumed by: `frontend/src/MapView.jsx` (inline MapLibre GL style config)
- Auth: none (public endpoint)

**Map Glyphs — Protomaps:**
- Font glyphs endpoint: `https://protomaps.github.io/basemaps-assets/fonts/{fontstack}/{range}.pbf`
- Consumed by: `frontend/src/MapView.jsx` (MapLibre GL `glyphs` config)
- Auth: none (public endpoint)

**Source Data — Theographic Bible Metadata:**
- GitHub raw JSON endpoints:
  - `https://raw.githubusercontent.com/robertrouse/theographic-bible-metadata/master/json/people.json`
  - `https://raw.githubusercontent.com/robertrouse/theographic-bible-metadata/master/json/places.json`
  - `https://raw.githubusercontent.com/robertrouse/theographic-bible-metadata/master/json/events.json`
  - `https://raw.githubusercontent.com/robertrouse/theographic-bible-metadata/master/json/peopleGroups.json`
- Consumed by: `backend/scripts/load_theographic.py` (one-time data load script)
- Auth: none (public GitHub raw)

## Internal API (Backend → Frontend)

**FastAPI backend** (`backend/app/`) exposes read-only HTTP endpoints (GET only, all methods in `backend/app/routes/`):
- `GET /node/{node_id}` — node detail + neighbors (`backend/app/routes/nodes.py`)
- `GET /node/{node_id}/places` — geo-coordinates for a node (`backend/app/routes/nodes.py`)
- `GET /node/{node_id}/neighbors/grouped` — neighbors grouped by type (`backend/app/routes/nodes.py`)
- `GET /events` — all events ordered by sortKey (`backend/app/routes/events.py`)
- `GET /search?q=` — full-text search across all node types (`backend/app/routes/search.py`)

**Frontend API client:** `frontend/src/api.js`
- Base URL: `import.meta.env.VITE_API_URL` (build-time) or `http://localhost:8000` (fallback)
- All requests via `apiGet(path, { signal })` helper — GET only, throws on non-OK status

**Nginx reverse proxy** (`nginx/nginx.conf`):
- `/api/*` → `http://api:8000/` (strips `/api` prefix)
- Frontend SPA static files served from `frontend/dist/`
- External port: 8080

**CORS:**
- FastAPI configured with `allow_origins=["*"]`, `allow_methods=["GET"]`, `allow_credentials=False` (`backend/app/main.py`)

## Authentication & Identity

- None. No auth provider. All endpoints are public read-only.

## CI/CD & Deployment

**Hosting:**
- Self-hosted macOS machine (GitHub Actions runner)
- Docker Compose project name: `biblemap`

**CI Pipeline:**
- GitHub Actions: `.github/workflows/deploy.yml`
- Trigger: push to `main` branch
- Steps:
  1. `git fetch && git reset --hard origin/main`
  2. `bash deploy.sh`

**Deploy script** (`deploy.sh`):
1. `npm install && npm run build` — builds frontend to `frontend/dist/`
2. `docker compose build api` — rebuilds API image
3. `docker compose up -d api nginx` — restarts api + nginx containers
4. `python3 backend/scripts/inject_ko_names.py` — writes Korean names from `data/names_ko/*.json` into Neo4j (retries up to 15×)

**Logs:**
- Deploy log: `/Users/calmonion/Library/Logs/com.biblemap.deploy.log`
- Lock file: `/tmp/biblemap-deploy.lock` (prevents concurrent deploys)

## Monitoring & Observability

- Error tracking: None
- Logs: `logging` stdlib in `backend/app/main.py` (index creation failure only); deploy log via `deploy.sh`

## Webhooks & Callbacks

- Incoming: None
- Outgoing: None

## Environment Configuration

**Required env vars (set in `.env` at project root):**
- `NEO4J_PASSWORD` — only required variable (see `.env.example`)

**Derived by Docker Compose (`docker-compose.yml`):**
- `NEO4J_AUTH=neo4j/${NEO4J_PASSWORD}` — injected into `neo4j` service
- `NEO4J_URI=bolt://neo4j:7687` — injected into `api` service
- `NEO4J_USER=neo4j` — injected into `api` service

**Build-time frontend env:**
- `VITE_API_URL=/api` — injected during `npm run build` (hardcoded in `deploy.sh` implicitly via vite defaults; must be set before build for production)

---

*Integration audit: 2026-06-14*
