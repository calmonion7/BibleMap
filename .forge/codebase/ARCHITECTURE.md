---
last_mapped_commit: 6bc79bba2bb1a869260e73efee7d9366d96a1cc0
mapped: 2026-06-20
---

# Architecture

**Analysis Date:** 2026-06-20

## System Overview

```text
┌──────────────────────────────────────────────────────────────────────┐
│                         Browser (React SPA)                          │
│                        frontend/src/App.jsx                          │
├─────────────────┬───────────────────┬────────────────────────────────┤
│   MapView.jsx   │  TimelineView.jsx │  BibleOverviewView.jsx         │
│  (maplibre-gl)  │  (scroll list)    │  (genre/book grid)             │
└────────┬────────┴────────┬──────────┴──────────────┬─────────────────┘
         │                 │                          │
         └─────────────────┼──────────────────────────┘
                           │ fetch via api.js (apiGet)
                           ▼
┌──────────────────────────────────────────────────────────────────────┐
│              nginx reverse proxy (:8080)                             │
│              /api/* → http://api:8000/                               │
│              /* → frontend/dist (static SPA)                        │
└──────────────────────────┬───────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────────┐
│               FastAPI backend (uvicorn :8000)                        │
│               backend/app/main.py                                    │
├─────────────┬──────────────┬─────────────┬──────────────────────────┤
│  /node/*    │  /events     │  /search    │  /books, /books-overview  │
│  nodes.py   │  events.py   │  search.py  │  books.py                 │
└─────────────┴──────┬───────┴─────────────┴──────────────────────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
         ▼                       ▼
┌──────────────────┐   ┌─────────────────────────────────────┐
│  Neo4j :7687     │   │  JSON overlay files (data/)          │
│  (graph DB)      │   │  book_events/books.json              │
│  db.py singleton │   │  book_years_approx/books.json        │
│  bolt driver     │   │  event_verses/events.json            │
└──────────────────┘   │  overlays.py (lru_cache loader)      │
                       └─────────────────────────────────────┘
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| App | Tab routing, search bar, SidePanel overlay, responsive layout | `frontend/src/App.jsx` |
| MapView | maplibre-gl map, place markers, cluster/spiderify, event ring animation | `frontend/src/MapView.jsx` |
| TimelineView | Chronological event list, book markers, verse drill-down | `frontend/src/TimelineView.jsx` |
| BibleOverviewView | Book grid grouped by testament/genre, key verse display | `frontend/src/BibleOverviewView.jsx` |
| SidePanel | Node detail panel (name, properties, neighbors); slides in as overlay | `frontend/src/SidePanel.jsx` |
| useNodeSelection | Selected node state, navigation history stack, Person event-id fetch | `frontend/src/useNodeSelection.js` |
| useSearch | Debounced search, type-filter chips, keyboard navigation state | `frontend/src/useSearch.js` |
| api.js | Single `apiGet` helper: base URL, abort signal, error throw | `frontend/src/api.js` |
| theme.js | Canonical node-type → color/label palette shared by all views | `frontend/src/theme.js` |
| convexHull.js | Graham scan implementation for Person activity hull polygon | `frontend/src/convexHull.js` |
| FastAPI app | CORS, lifespan index creation, router registration | `backend/app/main.py` |
| nodes router | `/node/{id}`, `/node/{id}/places`, `/node/{id}/neighbors/grouped`, `/person/{id}/event-ids` | `backend/app/routes/nodes.py` |
| events router | `/events` (cached), `/event/{id}/verses` | `backend/app/routes/events.py` |
| search router | `/search?q=` (Cypher full-text search) | `backend/app/routes/search.py` |
| books router | `/books` (timeline), `/books-overview` | `backend/app/routes/books.py` |
| db.py | Module-level singleton Neo4j driver, lazy-init via `get_driver()` | `backend/app/db.py` |
| overlays.py | `lru_cache` JSON file loader for book_events, approx_years, event_verses | `backend/app/overlays.py` |
| scripts/ | One-off data enrichment/injection scripts (not part of runtime) | `backend/scripts/` |

## Pattern Overview

**Overall:** Single-page application with a thin REST backend. No client-side router — views are always-mounted, toggled via CSS `display` in `App.jsx`.

**Key Characteristics:**
- Three main views (`map`, `timeline`, `overview`) rendered simultaneously; visibility toggled with `display: none / block` to preserve view state across tab switches.
- Global "selected node" state lives in `App.jsx` via `useNodeSelection`; views receive `selectedNode` id as a prop and react to it independently.
- Backend is read-only (GET-only CORS policy). All mutations to the graph are done offline via `backend/scripts/`.
- Overlay data (JSON files) supplements Neo4j with pre-computed enrichment that would be expensive or impossible to derive from the graph alone.

## Layers

**Frontend — UI Layer:**
- Purpose: Renders views, handles user interaction, manages local state
- Location: `frontend/src/`
- Contains: React components (`.jsx`), custom hooks (`.js`), utilities (`.js`)
- Depends on: `api.js` for all data, `theme.js` for visual constants
- Used by: Browser

**Frontend — API Client:**
- Purpose: Single point of contact for HTTP requests
- Location: `frontend/src/api.js`
- Contains: `API_BASE` constant, `apiGet(path, {signal})` function
- Depends on: `VITE_API_URL` env var (set to `/api` in production build)
- Used by: All view components and custom hooks

**Backend — Router Layer:**
- Purpose: HTTP endpoint handlers; transform Neo4j/overlay data into JSON responses
- Location: `backend/app/routes/`
- Contains: `nodes.py`, `events.py`, `search.py`, `books.py`
- Depends on: `db.py` (Neo4j driver), `overlays.py` (JSON files)
- Used by: FastAPI app via `include_router`

**Backend — Data Access:**
- Purpose: Database connection singleton and JSON overlay loader
- Location: `backend/app/db.py`, `backend/app/overlays.py`
- Contains: `get_driver()`, `book_events_raw()`, `approx_years()`, `event_verses()`
- Depends on: `NEO4J_URI/USER/PASSWORD` env vars; `DATA_DIR` env var or `data/` repo dir
- Used by: All routers

**Data Layer:**
- Purpose: Persistent storage
- Consists of: Neo4j graph database (nodes: Person, Place, Event, PeopleGroup, Book) + JSON overlay files in `data/`
- Overlay files are read-only at runtime; written by `backend/scripts/`

## Data Flow

### Node Detail (SidePanel)

1. User clicks map marker or search result → `onSelectNode(id)` called → `selectedNode` state set in `App.jsx` (`frontend/src/App.jsx:74`)
2. `SidePanel` receives `nodeId` prop change → `useEffect` fires `apiGet('/node/' + nodeId)` (`frontend/src/SidePanel.jsx:54`)
3. nginx proxies `/api/node/{id}` → FastAPI `GET /node/{node_id}` (`backend/app/routes/nodes.py:145`)
4. Handler runs two Neo4j Cypher queries (node + neighbors in single round-trip), returns JSON
5. `SidePanel` renders node name, properties, neighbor chips
6. `onNodeLoaded(data)` callback → `useNodeSelection` stores `selectedNodeMeta`; if Person, fetches `/person/{id}/event-ids`

### Map Place Display

1. `selectedNode` prop change detected in `MapView` `useEffect` (`frontend/src/MapView.jsx:580`)
2. `apiGet('/node/{id}/places')` fetches place coordinates
3. Places rendered as GeoJSON into `places-source` (maplibre-gl cluster source)
4. If `label === 'Person'` and 3+ places: convex hull polygon drawn on `hull-source`
5. Primary place auto-expanded: `expandPlace(id, lng, lat)` fetches `/node/{id}/neighbors/grouped`, animates event ring out with `requestAnimationFrame`

### Timeline / Events

1. `TimelineView` mounts → `apiGet('/events')` fetches full event list once (`frontend/src/TimelineView.jsx:49`)
2. Events grouped by `startDate` into accordion groups; filtered by `bookFilter` or `personFilter` props from App
3. Event row expand → `apiGet('/event/{id}/verses')` fetches pre-baked verse text; displayed inline

### Search

1. User types → `useSearch` debounces 250ms → `apiGet('/search?q=...')` with AbortController (`frontend/src/useSearch.js:21`)
2. Results displayed in dropdown with type-filter chips; keyboard nav via arrow keys
3. Result selected → `App.handleSelectResult` → `selectNodeFresh(id)` + tab switch based on node type

## Key Abstractions

**`theographic_id`:**
- Purpose: Universal node identifier across all Neo4j labels
- Used as the id value in all API responses and all frontend state (`selectedNode`)
- Frontend never uses Neo4j internal node IDs

**Overlay files:**
- Purpose: Pre-computed JSON that supplements Neo4j at startup
- Examples: `data/book_events/books.json` (book→event mapping), `data/event_verses/events.json` (event→verse text)
- Pattern: `overlays.py` loads each file once via `functools.lru_cache(maxsize=1)`; merged with Neo4j results in routers

**Node type palette:**
- Purpose: Single source of truth for type → color and Korean label
- Location: `frontend/src/theme.js`
- All views import `TYPE_COLOR`, `TYPE_KO`, `TYPE_ORDER`, `typeColor`, `typeKo`, `SELECT_HL` from this module

## Entry Points

**Frontend:**
- Location: `frontend/src/main.jsx`
- Triggers: Browser loads `index.html`; Vite injects `main.jsx` as module script
- Responsibilities: Mounts `<App />` into `#root`

**Backend:**
- Location: `backend/app/main.py` (FastAPI `app` object)
- Triggers: `uvicorn backend.app.main:app` (via Dockerfile CMD)
- Responsibilities: CORS middleware, Neo4j index creation on startup, router mounting

## Architectural Constraints

- **Global state:** `_driver` in `backend/app/db.py` is a module-level singleton. `lru_cache` closures in `overlays.py` and `events.py` hold cached data for the process lifetime.
- **Always-mounted views:** `MapView`, `TimelineView`, `BibleOverviewView` are always in the React tree; hidden via `display: none`. This preserves map instance and timeline scroll position across tab switches. Do not unmount them conditionally.
- **Read-only API:** FastAPI CORS only allows GET. No POST/PUT/DELETE routes exist. All graph writes are done via one-off `backend/scripts/` run outside the web server.
- **Build-time API URL:** `VITE_API_URL` is baked into the JS bundle at `npm run build`. Development (vite dev) uses `http://localhost:8000` directly; production build uses `/api` (nginx proxy). Changing the API host requires a rebuild.
- **Data overlay path resolution:** `overlays.py` checks `DATA_DIR` env var first, then falls back to the repo `data/` directory. In Docker, `data/` is bind-mounted to `/app/data`.

## Anti-Patterns

### Importing TYPE_COLOR/TYPE_KO locally in a component

**What happens:** A component defines its own `{ Person: '#color', ... }` map instead of importing from `theme.js`.
**Why it's wrong:** Creates a second palette that diverges silently; different views show different colors for the same node type.
**Do this instead:** `import { typeColor, typeKo } from './theme'` — this is what `App.jsx`, `SidePanel.jsx`, `MapView.jsx`, and `TimelineView.jsx` all do.

### Setting state synchronously in a `useEffect` body

**What happens:** `setState(value)` called directly in the synchronous body of a `useEffect` (not inside a callback/promise).
**Why it's wrong:** Violates `eslint-plugin-react-hooks` v7 rule; causes double-render and stale-closure bugs.
**Do this instead:** All `setState` calls in effects are inside `setTimeout`, `.then()`, or `async` callbacks — see `useSearch.js:32–34` and `SidePanel.jsx:55`.

## Error Handling

**Strategy:** Optimistic display with inline error states; no global error boundary.

**Patterns:**
- API errors in view components set a local `error` boolean and render an inline error message (e.g., `SidePanel.jsx:67`, `TimelineView.jsx:51`)
- `apiGet` throws an `Error` with `.status` property on non-OK HTTP responses; `AbortError` is caught and silently ignored by callers
- MapView sets `noLocation` state when `/places` returns empty array; shows a banner instead of error

## Cross-Cutting Concerns

**Logging:** None at runtime. Backend uses Python's `logging.exception` only on Neo4j startup index failure (`backend/app/main.py:19`).
**Validation:** None on the frontend. Backend relies on FastAPI query parameter typing and Neo4j query binding for injection prevention.
**Authentication:** None. The app is read-only and open.

---

*Architecture analysis: 2026-06-20*
