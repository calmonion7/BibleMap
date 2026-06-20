---
last_mapped_commit: 42bd230af7e22bc1839023a1189d6ae696944188
mapped: 2026-06-20
---

# BibleMap Architecture

## Architectural Pattern

Three-tier web application with a static frontend, REST API backend, and graph database. All three tiers run as Docker containers orchestrated via `docker-compose.yml`.

```
Browser → nginx (port 8080) → FastAPI (internal) → Neo4j (Bolt internal)
```

No microservices — single backend process serves all API routes.

## Layers

### Frontend

- **Technology:** React 19 + Vite 8, plain JSX (no TypeScript), MapLibre GL for the map tile layer
- **Build:** `frontend/` is built with `npm run build` into `frontend/dist/`. nginx serves the static files from that directory.
- **Routing:** No client-side router. `App.jsx` controls which of three views is visible via CSS `display` toggle (all views always mounted, state preserved across tab switches).

### Backend

- **Technology:** FastAPI (Python), async lifespan for startup tasks
- **Entry point:** `backend/app/main.py` — creates the `FastAPI` app, registers four routers, adds CORS middleware (GET-only, all origins)
- **Connection:** `backend/app/db.py` — singleton Neo4j driver (`GraphDatabase.driver`), connection string from `NEO4J_URI` env var

### Database

- **Technology:** Neo4j 5 graph database (Docker volume `neo4j_data`)
- **Access:** Bolt protocol (`bolt://neo4j:7687` inside Docker network, `127.0.0.1:7687` for local scripts)
- **Indices:** Created at startup in `main.py` lifespan for labels `Person`, `Place`, `Event`, `PeopleGroup`, `Book` on `theographic_id`

## Node Labels and Relationships

Graph schema (from query patterns in `backend/app/routes/`):

- Node labels: `Person`, `Place`, `Event`, `PeopleGroup`, `Book`
- Key relationships:
  - `(Event)-[:HAS_PARTICIPANT]->(Person)`
  - `(Event)-[:OCCURS_AT]->(Place)`
  - `(Person)-[:MEMBER_OF]->(PeopleGroup)`
  - `(Book)-[:CONTAINS_BOOK]->(Event)`
  - `(Person)-[:PARENT_OF|CHILD_OF|SIBLING_OF|PARTNER_OF]->(Person)`
- Universal node identity field: `theographic_id` (string, indexed)

## Data Flow

### Map view selection flow

1. User selects a node (map marker, search result, or SidePanel link)
2. `useNodeSelection.js` → `selectNode(id)` updates `selectedNode` state in `App.jsx`
3. `SidePanel.jsx` fetches `GET /node/{id}` → renders name, properties, neighbors
4. `MapView.jsx` fetches `GET /node/{id}/places` → renders GeoJSON markers on the map

### Search flow

1. User types in the search box; `useSearch.js` debounces 250ms
2. `GET /search?q=...` → backend queries Neo4j on `nameKo CONTAINS $q OR name CONTAINS $q`
3. Results ranked (exact match → prefix → contains), displayed in dropdown with type-filter chips

### Timeline flow

1. `TimelineView.jsx` mounts → fetches `GET /events` (cached 5 minutes)
2. Events grouped by `startDate`, displayed in chronological order
3. On event expand → `GET /event/{id}/verses` returns pre-stored verse text (no additional fetch per verse)

### Overlay data flow

Some data is served from flat JSON files in `data/` rather than Neo4j:
- `backend/app/overlays.py` resolves paths: checks `DATA_DIR` env var first, then repo `data/` directory
- Three overlays, each `lru_cache(maxsize=1)` in memory after first load:
  - `data/book_events/books.json` — `{bookId: [eventId, …]}` mapping
  - `data/book_years_approx/books.json` — `{bookId: {placementYear, basis}}` approx year data
  - `data/event_verses/events.json` — `{eventId: {books: [{bookId, verses}]}}` verse text cache

## Key Abstractions

### Backend

| File | Role |
|---|---|
| `backend/app/main.py` | App factory, lifespan, router registration |
| `backend/app/db.py` | Neo4j driver singleton (`get_driver()`) |
| `backend/app/overlays.py` | JSON overlay loader with `lru_cache` |
| `backend/app/routes/nodes.py` | Node detail, neighbor, and place endpoints |
| `backend/app/routes/events.py` | Timeline events + verse drilldown |
| `backend/app/routes/search.py` | Full-text search endpoint |
| `backend/app/routes/books.py` | Book list for timeline and overview views |

### Frontend

| File | Role |
|---|---|
| `frontend/src/main.jsx` | React tree mount point |
| `frontend/src/App.jsx` | Root component — tab navigation, search bar, panel overlay, mobile/desktop layout |
| `frontend/src/api.js` | Shared `apiGet(path)` helper; `API_BASE` from `VITE_API_URL` env var |
| `frontend/src/theme.js` | Canonical type-to-color and type-to-Korean-label maps (`TYPE_COLOR`, `TYPE_KO`, `TYPE_ORDER`) |
| `frontend/src/useNodeSelection.js` | Selected node state, navigation history, back/close |
| `frontend/src/useSearch.js` | Debounced search, dropdown state, type filter chips |
| `frontend/src/MapView.jsx` | MapLibre GL map; clustering, spiderify (ring fly-out), convex hull overlay |
| `frontend/src/TimelineView.jsx` | Chronological event list; book filter, person filter, verse drilldown |
| `frontend/src/SidePanel.jsx` | Node detail panel (properties + grouped neighbors) |
| `frontend/src/BibleOverviewView.jsx` | Bible book grid grouped by testament and genre |
| `frontend/src/convexHull.js` | Graham scan convex hull utility (used by MapView for group boundary) |
| `frontend/src/VerseLangTabs.jsx` | KO/EN verse language toggle (shared state from App.jsx) |
| `frontend/src/Spinner.jsx` | Loading indicator component |

## Entry Points

### Backend

- `backend/app/main.py` — `app = FastAPI(lifespan=lifespan)` is the ASGI entry point
- `backend/Dockerfile` (not read, but inferred): uvicorn or gunicorn launches `app.main:app`

### API routes registered in `main.py`

- `nodes.router` → endpoints: `GET /node/{id}`, `GET /node/{id}/places`, `GET /node/{id}/neighbors/grouped`, `GET /person/{id}/event-ids`
- `events.router` → endpoints: `GET /events`, `GET /event/{id}/verses`
- `search.router` → endpoint: `GET /search`
- `books.router` → endpoints: `GET /books`, `GET /books-overview`

### Frontend

- `frontend/index.html` → loads `frontend/src/main.jsx` → mounts `<App />` into `#root`

### nginx proxy

- `GET /api/*` → stripped of `/api` prefix → forwarded to `http://api:8000/*`
- All other paths → `frontend/dist/` static files (SPA fallback to `index.html`)

## Data Loading Scripts

`backend/scripts/` contains one-off ETL scripts used to populate Neo4j and generate the JSON overlays. They are not part of the runtime API:

- `load_theographic.py` — loads base Theographic dataset into Neo4j
- `load_books.py`, `load_person_events.py`, `load_authored_events.py` — supplemental node/relationship loads
- `inject_ko_names.py`, `inject_person_traits.py`, `inject_book_context.py` — property enrichment
- `enrich_place_coords.py` — geocoordinate enrichment
- `generate_*` scripts — produce JSON files written to `data/` subdirectories (overlays)
