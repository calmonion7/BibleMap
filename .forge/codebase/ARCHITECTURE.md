---
last_mapped_commit: 7d2210c48a67b08b79cc3f03008c3ee30e885614
mapped: 2026-06-19
---

# BibleMap Architecture

## Overall Pattern

Three-tier layered web application running as Docker Compose services:

```
Browser (SPA)
    ↓ HTTP /api/*
nginx (reverse proxy, port 8080)
    ↓ HTTP proxied to api:8000
FastAPI (REST API, port 8000)
    ↓ Bolt protocol
Neo4j 5 (graph database, port 7687)
```

No server-side rendering. All UI logic lives in the browser. The backend is a thin read-only query layer — no write endpoints exist.

## Layers and Responsibilities

### Infrastructure (`docker-compose.yml`)

- `neo4j` service: graph data store, persisted via named volume `neo4j_data`.
- `api` service: FastAPI application, mounts `./data` at `/app/data` for JSON overlays.
- `nginx` service: serves `frontend/dist` as static files and reverse-proxies `/api/` to `api:8000`.

### Backend (`backend/`)

**Entry point**: `backend/app/main.py`
- Instantiates `FastAPI` with `CORSMiddleware` (GET-only, all origins).
- On startup (`lifespan`), creates Neo4j indexes for `theographic_id` on each node label.
- Registers four routers: `nodes`, `events`, `search`, `books`.

**Database abstraction**: `backend/app/db.py`
- Module-level singleton `_driver` pattern (`get_driver()`).
- Reads `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD` from environment.

**Routers** (`backend/app/routes/`):

| File | Prefix | Responsibility |
|---|---|---|
| `nodes.py` | — | `/node/{id}`, `/node/{id}/places`, `/node/{id}/neighbors/grouped`, `/person/{id}/event-ids` |
| `events.py` | — | `/events` (timeline data), `/event/{id}/verses` (verse drill-down) |
| `search.py` | — | `/search?q=` (full-text across all node labels) |
| `books.py` | — | `/books` (all Book nodes with timeline placement year) |

**Caching strategy** (`events.py`, `books.py`):
- `functools.lru_cache(maxsize=1)` on data-loading functions (`_compute_events`, `_load_approx`, `_load_book_events`, `_load_event_verses`, `_load_approx_book_index`) — results are held in memory for the process lifetime.
- `/events` and `/event/{id}/verses` set `Cache-Control: max-age=300` on responses.
- `/books` sets `Cache-Control: no-store`.

**JSON overlay pattern** (`events.py`, `books.py`):
- Runtime-overlay JSON files in `data/` are loaded via a two-candidate path list: `DATA_DIR env var` (Docker volume) → repository-relative `data/` (local dev).
- These overlays carry estimated/low-authority data that is intentionally kept out of Neo4j (ADR-0004, ADR-0006).

**Data pipeline scripts** (`backend/scripts/`):
- One-shot loader scripts run manually to seed/update Neo4j. Not invoked by the API server.
- `load_theographic.py`: fetches from `robertrouse/theographic-bible-metadata` GitHub, loads Person/Place/Event/PeopleGroup nodes and relationships.
- `load_books.py`: fetches books.json, creates Book nodes and `CONTAINS_BOOK` edges via verse-set intersection.
- `load_authored_events.py`: loads `data/authored_events/events.json` into Neo4j as `Event` nodes with `authored:true`.
- `load_verse_events.py`: writes `data/verse_events/events.json` into Neo4j.
- `inject_*` scripts: enrich existing nodes with LLM-generated data from `data/`.
- `generate_*` scripts: call Claude API to generate JSON written to `data/`.

### Frontend (`frontend/`)

**Entry point**: `frontend/src/main.jsx` → mounts `<App />` into `#root`.

**Root component**: `frontend/src/App.jsx`
- Holds all global UI state: `selectedNode` (theographic_id string), `activeView` ('map'|'timeline'), search state, `verseLang`, `personEventIds`, navigation `history` stack.
- Renders nav bar (tab switcher + search box) and conditionally mounts `MapView` or `TimelineView`.
- `SidePanel` is always mounted as an overlay div; it slides in/out via CSS transform driven by `selectedNode`.
- Mobile layout (≤768px): SidePanel becomes a bottom sheet (55vh). Desktop: right sidebar (360px wide).

**Shared API client**: `frontend/src/api.js`
- Single export `apiGet(path, opts)`: prepends `VITE_API_URL` (built as `/api` in production, `http://localhost:8000` in dev).

**Views**:

- `frontend/src/MapView.jsx`: MapLibre GL map centered on the Levant. Fetches `/node/{id}/places` on node selection; renders place markers with a radial event-ring animation on click. Draws convex hull polygon for multi-place selections.
- `frontend/src/TimelineView.jsx`: Chronological event list. Fetches `/events` once on mount. Groups events by `startDate` into collapsible rows. Supports book-filter (narrow to a single Book's events) and person-filter (highlight a Person's events). Inline verse drill-down via `/event/{id}/verses`.
- `frontend/src/SidePanel.jsx`: Fetches `/node/{id}` on `nodeId` prop change. Renders node properties, neighbors grouped by type, and (for Person nodes) verse-referenced trait cards.

**Utilities**:

- `frontend/src/theme.js`: canonical color palette and Korean labels for all node types (`TYPE_COLOR`, `TYPE_KO`, `TYPE_ORDER`). Imported by App, SidePanel, TimelineView, MapView.
- `frontend/src/convexHull.js`: pure Graham-scan implementation, no external dependency. Used by MapView.
- `frontend/src/VerseLangTabs.jsx`: language-toggle segment control (한국어/영어), shared between TimelineView and SidePanel.

## Data Flow — Request Lifecycle

### Map interaction (place marker click)

1. User clicks marker → MapView calls `onSelectNode(id)` → App sets `selectedNode`.
2. SidePanel receives new `nodeId`, fires `GET /api/node/{id}` → renders node detail.
3. MapView effect fires `GET /api/node/{id}/places` → updates marker layer.
4. If node is Person: App fetches `GET /api/person/{id}/event-ids` → stores set for timeline highlighting.

### Search

1. User types in nav bar search input → 250ms debounce → `GET /api/search?q=`.
2. Dropdown renders; user selects result → `selectNode(id)` called → same flow as above.

### Timeline verse drill-down

1. TimelineView mounts, fetches `GET /api/events` once, caches in state.
2. User clicks event group → expands to show events + book chips.
3. User clicks 📖 book chip → `GET /api/event/{id}/verses` → inline verse text rendered (pre-baked textKo/textEn, no further fetch).

## Key Abstractions

**`theographic_id`**: stable string key (Airtable record ID, `rec…` prefix) used across Neo4j nodes, API responses, frontend state, and JSON overlays to join entities.

**Overlay JSON pattern**: low-authority or estimated data (`book_years_approx`, `book_events`, `event_verses`) lives in `data/*.json` files, not Neo4j. API reads them at startup and merges with Neo4j query results at response time.

**Neo4j relationship schema**:
- `(Event)-[:HAS_PARTICIPANT]->(Person)`
- `(Event)-[:OCCURS_AT]->(Place)`
- `(Person)-[:MEMBER_OF]->(PeopleGroup)`
- `(Book)-[:CONTAINS_BOOK]->(Event)` — verse-set intersection, represents scriptural evidence
- `(Event)-[:PART_OF]->(Event)` — period hierarchy
- `(Person)-[:PARENT_OF|CHILD_OF|SIBLING_OF|PARTNER_OF]->(Person)`

## Entry Points

| Layer | Entry point |
|---|---|
| Frontend app | `frontend/src/main.jsx` |
| Frontend root component | `frontend/src/App.jsx` |
| Backend ASGI app | `backend/app/main.py` (`app` object) |
| Backend Docker image | `CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]` in `backend/Dockerfile` |
| nginx config | `nginx/nginx.conf` |
| Compose orchestration | `docker-compose.yml` |
| CI/CD | `.github/workflows/deploy.yml` |
| Manual deploy | `deploy.sh` |
