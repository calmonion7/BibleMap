---
last_mapped_commit: 42bd230af7e22bc1839023a1189d6ae696944188
mapped: 2026-06-20
---

# Stack

## Languages

- **Python 3.12** — backend (pinned in `backend/Dockerfile`: `FROM python:3.12-slim`)
- **JavaScript (ESM)** — frontend (`"type": "module"` in `frontend/package.json`)
- **JSX** — React components in `frontend/src/`

## Runtime Versions

| Component | Runtime | Version |
|-----------|---------|---------|
| Backend | Python | 3.12 (slim) |
| Frontend build | Node.js | not pinned (Vite 8.x implies ≥18) |
| Database | Neo4j | 5.x (`neo4j:5` image in `docker-compose.yml`) |
| Reverse proxy | nginx | alpine (`nginx:alpine` in `docker-compose.yml`) |

## Frameworks & Core Libraries

### Backend — `backend/requirements.txt`

| Package | Version |
|---------|---------|
| fastapi | 0.136.3 |
| uvicorn | 0.49.0 |
| neo4j (Python driver) | 6.2.0 |

### Frontend — `frontend/package.json`

| Package | Version |
|---------|---------|
| react | ^19.2.6 |
| react-dom | ^19.2.6 |
| maplibre-gl | ^5.24.0 |
| lucide-react | ^1.17.0 |

### Frontend devDependencies

| Package | Version |
|---------|---------|
| vite | ^8.0.12 |
| @vitejs/plugin-react | ^6.0.1 |
| eslint | ^10.3.0 |
| eslint-plugin-react-hooks | ^7.1.1 |
| eslint-plugin-react-refresh | ^0.5.2 |
| @types/react | ^19.2.14 |
| @types/react-dom | ^19.2.3 |
| globals | ^17.6.0 |
| @eslint/js | ^10.0.1 |

## Build Tools

- **Vite 8** — frontend bundler; config at `frontend/vite.config.js`
  - `@vitejs/plugin-react` plugin
  - Manual chunk split: `maplibre-gl` → `maplibre` chunk, other `node_modules` → `vendor` chunk
  - Output written to `frontend/dist/`
- **npm** — frontend package manager (`frontend/package-lock.json`)
- **Docker Compose** — orchestration (`docker-compose.yml`)
  - Services: `neo4j`, `api`, `nginx`
  - `api` built from `backend/Dockerfile`
- **uvicorn** — ASGI server; command `uvicorn app.main:app --host 0.0.0.0 --port 8000`

## Key Source Files

### Backend (`backend/`)

| File | Role |
|------|------|
| `backend/app/main.py` | FastAPI app factory, CORS middleware, Neo4j index creation on startup |
| `backend/app/db.py` | Singleton `GraphDatabase.driver` factory; reads env vars |
| `backend/app/overlays.py` | JSON file loader with `lru_cache`; serves static data overlays |
| `backend/app/routes/nodes.py` | Node detail, neighbors, place, and person-event-ids endpoints |
| `backend/app/routes/events.py` | Timeline events endpoint with approx-book index merge |
| `backend/app/routes/search.py` | Full-text search endpoint (Neo4j Cypher `CONTAINS`) |
| `backend/app/routes/books.py` | Books overview and timeline-placement endpoints |
| `backend/Dockerfile` | `python:3.12-slim`, installs requirements, copies `app/` |

### Frontend (`frontend/src/`)

| File | Role |
|------|------|
| `frontend/src/main.jsx` | React entry point |
| `frontend/src/App.jsx` | Root component, view routing |
| `frontend/src/api.js` | Shared `apiGet()` helper; `API_BASE` from `VITE_API_URL` env |
| `frontend/src/MapView.jsx` | MapLibre GL map, clustering, spiderify, place ring animation |
| `frontend/src/SidePanel.jsx` | Node detail sidebar |
| `frontend/src/TimelineView.jsx` | Event timeline |
| `frontend/src/BibleOverviewView.jsx` | Bible overview grid |
| `frontend/src/theme.js` | Shared color palette and type labels |
| `frontend/src/convexHull.js` | Convex hull geometry utility |
| `frontend/src/useNodeSelection.js` | Node selection state hook |
| `frontend/src/useSearch.js` | Search state and keyboard shortcut (`/`) hook |
| `frontend/src/VerseLangTabs.jsx` | Verse language tab component |
| `frontend/src/Spinner.jsx` | Loading spinner |

## Configuration Files

| File | Purpose |
|------|---------|
| `docker-compose.yml` | Service orchestration, port bindings, volume mounts |
| `backend/Dockerfile` | Backend container build |
| `nginx/nginx.conf` | Reverse proxy: `/api/` → `http://api:8000/`; static SPA from `/usr/share/nginx/html` |
| `frontend/vite.config.js` | Vite build configuration with manual chunk splitting |
| `frontend/eslint.config.js` | ESLint configuration |
| `.env` | Local secrets (gitignored) |
| `.env.example` | Documents `NEO4J_PASSWORD` variable |
| `frontend/.env.production` | `VITE_API_URL=/api` — injected at build time |

## Static Data Overlays (`data/`)

JSON files mounted into the API container at `/app/data`. Loaded once per process via `lru_cache` in `backend/app/overlays.py`.

| Subdirectory | Content |
|--------------|---------|
| `data/book_events/books.json` | `{bookId: [eventId, ...]}` — book→event mapping |
| `data/book_years_approx/books.json` | `{bookId: {placementYear, basis, ...}}` — estimated composition years |
| `data/event_verses/events.json` | `{eventId: {books: [...]}}` — event→verse mapping |
| `data/authored_events/` | Authored event data files |
| `data/book_context/` | Book contextual data files |
| `data/character_traits/` | Per-person trait data |
| `data/names_ko/` | Korean name mappings |
| `data/person_events/` | Person-to-event associations |
| `data/place_coords/` | Place coordinate data |
| `data/verse_events/` | Verse-to-event associations |
