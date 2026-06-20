---
last_mapped_commit: 6bc79bba2bb1a869260e73efee7d9366d96a1cc0
mapped: 2026-06-20
---

# Codebase Structure

**Analysis Date:** 2026-06-20

## Directory Layout

```
BibleMap/                         # repo root
├── backend/                      # Python FastAPI service
│   ├── app/                      # Runtime application package
│   │   ├── main.py               # FastAPI app + lifespan
│   │   ├── db.py                 # Neo4j driver singleton
│   │   ├── overlays.py           # JSON overlay file loader (lru_cache)
│   │   └── routes/               # One file per router group
│   │       ├── nodes.py          # /node/* endpoints
│   │       ├── events.py         # /events, /event/{id}/verses
│   │       ├── search.py         # /search
│   │       └── books.py          # /books, /books-overview
│   ├── scripts/                  # Offline data-prep scripts (not runtime)
│   │   ├── load_theographic.py   # Initial graph load from Theographic dataset
│   │   ├── load_books.py
│   │   ├── load_person_events.py
│   │   ├── load_authored_events.py
│   │   ├── load_verse_events.py
│   │   ├── generate_book_events.py
│   │   ├── generate_book_context.py
│   │   ├── generate_approx_book_verses.py
│   │   ├── generate_book_context.py
│   │   ├── generate_event_verses.py
│   │   ├── generate_person_event_verses.py
│   │   ├── generate_person_traits.py
│   │   ├── generate_verse_events.py
│   │   ├── generate_verse_text.py
│   │   ├── inject_book_context.py
│   │   ├── inject_ko_names.py
│   │   ├── inject_person_traits.py
│   │   └── enrich_place_coords.py
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/                     # Vite + React SPA
│   ├── src/
│   │   ├── main.jsx              # React entry point (createRoot)
│   │   ├── App.jsx               # Root component: tabs, search bar, SidePanel overlay
│   │   ├── MapView.jsx           # maplibre-gl map view
│   │   ├── TimelineView.jsx      # Chronological event list view
│   │   ├── BibleOverviewView.jsx # Book grid by testament/genre
│   │   ├── SidePanel.jsx         # Node detail slide-in panel
│   │   ├── VerseLangTabs.jsx     # KO/EN verse language toggle
│   │   ├── Spinner.jsx           # Loading spinner
│   │   ├── api.js                # Shared apiGet helper + API_BASE
│   │   ├── theme.js              # Node-type color/label palette constants
│   │   ├── convexHull.js         # Graham scan utility (Person hull polygon)
│   │   ├── useNodeSelection.js   # Custom hook: selected node + history stack
│   │   ├── useSearch.js          # Custom hook: debounced search + dropdown state
│   │   └── assets/               # Static images (hero.png, svgs)
│   ├── public/                   # Copied verbatim to dist root (favicon etc.)
│   ├── index.html                # Vite HTML template
│   ├── vite.config.js            # Vite build config (manualChunks: maplibre, vendor)
│   ├── eslint.config.js
│   ├── package.json
│   └── .env.production           # VITE_API_URL=/api (baked at build time)
│
├── data/                         # JSON overlay files (read-only at runtime)
│   ├── book_events/
│   │   └── books.json            # {bookId: [eventId, ...]}
│   ├── book_years_approx/
│   │   └── books.json            # {bookId: {placementYear, basis, ...}}
│   ├── event_verses/
│   │   └── events.json           # {eventId: {books: [{bookId, verses:[{ref,textKo,textEn}]}]}}
│   ├── authored_events/          # Per-person authored event data
│   ├── book_context/             # Book narrative context
│   ├── character_traits/         # Person trait data
│   ├── names_ko/                 # Korean name mappings
│   ├── person_events/            # Per-person event lists
│   ├── place_coords/             # Enriched place coordinates
│   └── verse_events/             # Verse → event mappings
│
├── nginx/
│   └── nginx.conf                # Reverse proxy: /api/* → api:8000, /* → dist/
│
├── .forge/                       # GSD project management
│   ├── CONTEXT.md                # Project domain context (authoritative)
│   ├── codebase/                 # Codebase map documents (this directory)
│   ├── done/                     # Completed task records
│   ├── backlog/                  # Pending tasks
│   └── adr/                      # Architecture decision records
│
├── .github/                      # GitHub Actions CI/CD
├── docker-compose.yml            # Services: neo4j, api, nginx
├── deploy.sh                     # Production deployment helper
├── .env                          # NEO4J_PASSWORD (gitignored)
└── CLAUDE.md                     # LLM behavioral guidelines
```

## Directory Purposes

**`backend/app/`:**
- Purpose: Runtime Python package; imported by uvicorn
- Contains: FastAPI app, route handlers, DB connection, overlay loader
- Key files: `main.py` (app factory), `db.py` (connection), `overlays.py` (JSON cache)

**`backend/app/routes/`:**
- Purpose: One module per logical API resource group
- Contains: APIRouter instances registered in `main.py`
- Key files: `nodes.py` (node graph queries), `events.py` (timeline + verse data), `search.py`, `books.py`

**`backend/scripts/`:**
- Purpose: Offline one-shot data pipeline scripts; not imported by the app
- Contains: Scripts for loading, enriching, and generating overlay JSON data
- Never called at API request time; run manually or via CI to update `data/`

**`frontend/src/`:**
- Purpose: All application source — components, hooks, utilities
- No subdirectories; all files are at the top level of `src/`
- Contains: View components (`*View.jsx`), shared components (`SidePanel.jsx`, `Spinner.jsx`, `VerseLangTabs.jsx`), custom hooks (`use*.js`), utilities (`api.js`, `theme.js`, `convexHull.js`)

**`data/`:**
- Purpose: Pre-computed JSON overlays that the backend reads at startup
- Generated by: `backend/scripts/generate_*` and `backend/scripts/inject_*`
- Committed to the repo (not gitignored); bind-mounted into Docker at `/app/data`

## Key File Locations

**Entry Points:**
- `frontend/src/main.jsx`: React SPA entry, mounts `<App />`
- `backend/app/main.py`: FastAPI app object (`app`), imported as `backend.app.main:app`
- `nginx/nginx.conf`: nginx entry; routes `/api/*` to backend, serves SPA otherwise

**Configuration:**
- `docker-compose.yml`: Service topology (neo4j, api, nginx), volumes, env vars
- `frontend/.env.production`: `VITE_API_URL=/api` baked into production bundle
- `frontend/vite.config.js`: Build chunking (maplibre-gl into its own chunk)
- `backend/requirements.txt`: Python dependencies (fastapi, neo4j, uvicorn)
- `.env`: `NEO4J_PASSWORD` secret (gitignored; required at runtime)

**Core Logic:**
- `frontend/src/App.jsx`: Tab state, search orchestration, SidePanel overlay, responsive layout
- `frontend/src/useNodeSelection.js`: Navigation history, Person event-id fetch
- `frontend/src/useSearch.js`: Debounced search, AbortController, type-filter state
- `frontend/src/api.js`: `apiGet` — the only function that calls `fetch`
- `frontend/src/theme.js`: `TYPE_COLOR`, `TYPE_KO`, `TYPE_ORDER`, `SELECT_HL` — shared palette
- `backend/app/db.py`: `get_driver()` — the only place that creates a Neo4j connection
- `backend/app/overlays.py`: `book_events_raw()`, `approx_years()`, `event_verses()` — cached overlay loaders

## Naming Conventions

**Files:**
- React components: PascalCase with `.jsx` extension (`MapView.jsx`, `SidePanel.jsx`, `BibleOverviewView.jsx`)
- Custom hooks: camelCase prefixed with `use`, `.js` extension (`useNodeSelection.js`, `useSearch.js`)
- Utility modules: camelCase `.js` (`api.js`, `theme.js`, `convexHull.js`)
- Python modules: snake_case (e.g., `nodes.py`, `overlays.py`, `load_theographic.py`)
- Data overlay dirs: snake_case matching the data type (`book_events/`, `event_verses/`, `book_years_approx/`)

**Directories:**
- Frontend views share the `View` suffix in their filename (not a directory — all files are flat in `src/`)
- Backend scripts prefixed by action verb: `load_*`, `generate_*`, `inject_*`, `enrich_*`

**Identifiers:**
- Node IDs: `theographic_id` property in Neo4j, exposed as `id` in all API responses and frontend state
- Korean name field: `nameKo` (camelCase) in both Neo4j properties and API JSON
- Node type labels: PascalCase matching Neo4j labels (`Person`, `Place`, `Event`, `PeopleGroup`, `Book`)

## Where to Add New Code

**New view tab:**
- Add entry to `TABS` array in `frontend/src/App.jsx:11`
- Create `frontend/src/MyNewView.jsx`
- Add always-mounted `<div style={{ display: ... }}>` block in `App.jsx` render, matching the pattern at lines 246–269
- Register the tab key in `handleSelectResult` `tabMap` if search results should navigate here

**New API endpoint:**
- Add to the appropriate existing router file in `backend/app/routes/` (group by resource: nodes, events, books, search)
- If a genuinely new resource group: create `backend/app/routes/mynew.py`, add `app.include_router(mynew.router)` in `backend/app/main.py`

**New data overlay:**
- Add generation script to `backend/scripts/generate_mynew.py`
- Add a loader function to `backend/app/overlays.py` using the same `@functools.lru_cache(maxsize=1)` + `_load(subpath)` pattern
- Place output JSON under `data/mynew/`

**New node-type color or label:**
- Edit `frontend/src/theme.js` only — `TYPE_COLOR`, `TYPE_KO`, `TYPE_ORDER`
- Do not define per-component color maps

**Shared UI utilities:**
- Stateless display components: `frontend/src/` (e.g., `Spinner.jsx`, `VerseLangTabs.jsx`)
- Stateful logic reused across components: custom hook in `frontend/src/use*.js`

## Special Directories

**`.forge/`:**
- Purpose: GSD project management (tasks, retros, context, codebase maps)
- Generated: No (hand-maintained and agent-written)
- Committed: Yes (partially — volatile subdirs like `retro/` may be excluded per `.gitignore`)

**`frontend/dist/`:**
- Purpose: Vite production build output; served by nginx
- Generated: Yes (`npm run build`)
- Committed: No (gitignored in `frontend/.gitignore`)

**`backend/__pycache__/`:**
- Purpose: Python bytecode cache
- Generated: Yes
- Committed: No

---

*Structure analysis: 2026-06-20*
