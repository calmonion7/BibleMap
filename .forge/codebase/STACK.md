---
last_mapped_commit: 7d2210c48a67b08b79cc3f03008c3ee30e885614
mapped: 2026-06-19
---

# Stack

## Languages

- **Python 3.12** — backend API server (`backend/Dockerfile`: `FROM python:3.12-slim`)
- **JavaScript (ESM)** — frontend, all source files under `frontend/src/` use `.js` / `.jsx`

## Runtimes

- Python 3.12 (Docker container via `backend/Dockerfile`)
- Node.js v24.15.0 (local dev; not pinned in any lock file beyond `package-lock.json`)

## Backend Framework

- **FastAPI 0.136.3** (`backend/requirements.txt`)
- **Uvicorn 0.49.0** — ASGI server; started via `CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]` in `backend/Dockerfile`
- Application entry point: `backend/app/main.py`
- Route modules: `backend/app/routes/nodes.py`, `backend/app/routes/events.py`, `backend/app/routes/search.py`, `backend/app/routes/books.py`
- DB connection: `backend/app/db.py` (singleton driver, lazy-initialized via `get_driver()`)

### Backend middleware

- `CORSMiddleware` with `allow_origins=["*"]`, `allow_methods=["GET"]` — read-only API

### In-process caching

`functools.lru_cache(maxsize=1)` on:
- `_compute_events()` in `backend/app/routes/events.py`
- `_load_event_verses()` in `backend/app/routes/events.py`
- `_load_approx_book_index()` in `backend/app/routes/events.py`
- `_load_approx()` in `backend/app/routes/books.py`
- `_load_book_events()` in `backend/app/routes/books.py`

## Database

- **Neo4j 5** (`docker-compose.yml`: `image: neo4j:5`)
- Driver: `neo4j==6.2.0` Python client (`backend/requirements.txt`)
- Protocol: Bolt (`bolt://neo4j:7687` inside Docker network; `bolt://localhost:7687` for local scripts)

## Frontend Framework and Libraries

All declared in `frontend/package.json`:

| Package | Version | Role |
|---|---|---|
| `react` | ^19.2.6 | UI framework |
| `react-dom` | ^19.2.6 | DOM renderer |
| `maplibre-gl` | ^5.24.0 | Map rendering |
| `lucide-react` | ^1.17.0 | Icon set |

Dev dependencies:

| Package | Version | Role |
|---|---|---|
| `vite` | ^8.0.12 | Build tool / dev server |
| `@vitejs/plugin-react` | ^6.0.1 | React JSX transform plugin |
| `eslint` | ^10.3.0 | Linter |
| `eslint-plugin-react-hooks` | ^7.1.1 | Hooks lint rules |
| `eslint-plugin-react-refresh` | ^0.5.2 | HMR lint rules |
| `globals` | ^17.6.0 | ESLint browser globals |
| `@types/react` | ^19.2.14 | TS type hints (JSDoc only) |
| `@types/react-dom` | ^19.2.3 | TS type hints |

Frontend source files: `frontend/src/App.jsx`, `frontend/src/MapView.jsx`, `frontend/src/SidePanel.jsx`, `frontend/src/TimelineView.jsx`, `frontend/src/VerseLangTabs.jsx`, `frontend/src/api.js`, `frontend/src/convexHull.js`, `frontend/src/theme.js`

## Build

- **Vite** builds frontend to `frontend/dist/` (`npm run build` from `frontend/`)
- Vite config: `frontend/vite.config.js`
- Manual chunk splitting: `maplibre-gl` → `maplibre` chunk; all other `node_modules` → `vendor` chunk
- Production env var injection at build time via `frontend/.env.production` (`VITE_API_URL=/api`)
- No HMR in production — nginx serves `frontend/dist/` as static files

## Web Server / Reverse Proxy

- **nginx:alpine** (`docker-compose.yml`)
- Config: `nginx/nginx.conf`
- Port 8080 → container port 80
- `/api/*` proxied to `http://api:8000/`
- Static assets served with `Cache-Control: public, max-age=31536000, immutable`
- `index.html` served with `Cache-Control: no-cache, no-store, must-revalidate`

## Containerization

- `docker-compose.yml` defines three services: `neo4j`, `api`, `nginx`
- Backend Dockerfile: `backend/Dockerfile`
- Data volume: `./data` bind-mounted to `/app/data` in the `api` container

## Configuration Files

| File | Purpose |
|---|---|
| `docker-compose.yml` | Service orchestration |
| `backend/Dockerfile` | Backend image definition |
| `backend/requirements.txt` | Python dependencies |
| `frontend/package.json` | JS dependencies and scripts |
| `frontend/package-lock.json` | Lockfile |
| `frontend/vite.config.js` | Vite build config |
| `frontend/eslint.config.js` | ESLint flat config |
| `frontend/.env.production` | Frontend prod env vars (`VITE_API_URL=/api`) |
| `.env` | Root secrets (`NEO4J_PASSWORD`) — not committed |
| `.env.example` | Env var documentation |
| `nginx/nginx.conf` | Nginx reverse proxy config |

## Environment Variables

| Variable | Set in | Consumed by |
|---|---|---|
| `NEO4J_PASSWORD` | `.env` (root) | `docker-compose.yml` → `api` container, `neo4j` container |
| `NEO4J_URI` | `docker-compose.yml` | `backend/app/db.py` (default: `bolt://localhost:7687`) |
| `NEO4J_USER` | `docker-compose.yml` | `backend/app/db.py` (default: `neo4j`) |
| `VITE_API_URL` | `frontend/.env.production` | `frontend/src/api.js` (default: `http://localhost:8000`) |
| `DATA_DIR` | (optional, not set in compose) | `backend/app/routes/events.py`, `backend/app/routes/books.py` (default: `/app/data`) |
| `ANTHROPIC_API_KEY` | (not in compose; offline scripts only) | `backend/scripts/generate_*.py` |

## Data Pipeline Scripts

All under `backend/scripts/`; run ad-hoc offline, not part of the web server:

| Script | Language | Purpose |
|---|---|---|
| `load_theographic.py` | Python | Load Theographic Bible Metadata into Neo4j |
| `load_books.py` | Python | Load book records into Neo4j |
| `load_authored_events.py` | Python | Load hand-authored events into Neo4j |
| `inject_ko_names.py` | Python | Inject Korean name translations into Neo4j |
| `inject_person_traits.py` | Python | Inject generated person traits into Neo4j |
| `inject_book_context.py` | Python | Inject generated book context into Neo4j |
| `generate_person_traits.py` | Python | Generate person traits via Claude API |
| `generate_book_context.py` | Python | Generate book background via Claude API |
| `generate_book_events.py` | Python | Generate book-event links via Claude API |
| `generate_event_verses.py` | Python | Derive event-verse mapping from Theographic data |
| `generate_approx_book_verses.py` | Python | Assign representative verses for approx-year books |
| `generate_verse_text.py` | Python | Pre-bake verse text from getBible API |
| `generate_verse_events.py` | Python | Generate verse-to-event mapping via Claude API |
| `load_verse_events.py` | Python | Load verse-event mapping into Neo4j |
