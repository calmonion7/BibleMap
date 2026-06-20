---
last_mapped_commit: 6bc79bba2bb1a869260e73efee7d9366d96a1cc0
mapped: 2026-06-20
---

# Technology Stack

**Analysis Date:** 2026-06-20

## Languages

**Primary:**
- JavaScript (ES Modules, JSX) — Frontend (`frontend/src/`)
- Python 3.12 — Backend (`backend/app/`, `backend/scripts/`)

**Secondary:**
- CSS — Frontend styles (`frontend/src/index.css`)

## Runtime

**Frontend:**
- Browser (ES2020+ target via Vite)

**Backend:**
- Python 3.12 (Docker: `python:3.12-slim`)
- ASGI via Uvicorn 0.49.0

**Package Manager:**
- Frontend: npm — lockfile: `frontend/package-lock.json` (present)
- Backend: pip — lockfile: none (pinned via `backend/requirements.txt`)

## Frameworks

**Backend Core:**
- FastAPI 0.136.3 — REST API server (`backend/app/main.py`)

**Frontend Core:**
- React 19.2.6 — UI component framework (`frontend/src/`)
- React DOM 19.2.6

**Build/Dev:**
- Vite 8.0.12 — frontend build tool and dev server (`frontend/vite.config.js`)
- `@vitejs/plugin-react` 6.0.1 — React JSX transform plugin

## Key Dependencies

**Frontend:**
- `maplibre-gl` 5.24.0 — WebGL map rendering (`frontend/src/MapView.jsx`)
- `lucide-react` 1.17.0 — icon components (`frontend/src/`)

**Backend:**
- `neo4j` 6.2.0 — official Neo4j Python driver (`backend/app/db.py`)
- `uvicorn` 0.49.0 — ASGI server

**Scripts (data pipeline, not part of runtime API):**
- `anthropic` — Anthropic Claude API client (`backend/scripts/generate_*.py`)

## Linting

- ESLint 10.3.0 — config at `frontend/eslint.config.js`
- Plugins: `eslint-plugin-react-hooks` 7.1.1, `eslint-plugin-react-refresh` 0.5.2

## Configuration

**Frontend environment:**
- Build-time: `frontend/.env.production` sets `VITE_API_URL=/api`
- Dev fallback: `VITE_API_URL` defaults to `http://localhost:8000` in `frontend/src/api.js`

**Backend environment (runtime):**
- `NEO4J_URI` — Bolt connection string (default: `bolt://localhost:7687`)
- `NEO4J_USER` — Neo4j username (default: `neo4j`)
- `NEO4J_PASSWORD` — required; no default; raises `RuntimeError` if absent
- Template: `.env.example` at project root

**Build:**
- `frontend/vite.config.js` — configures Rollup chunk splitting: `maplibre-gl` → `maplibre` chunk, remaining `node_modules` → `vendor` chunk
- `backend/Dockerfile` — builds from `python:3.12-slim`, exposes port 8000

## Serving Architecture

**Production:**
- Nginx (Alpine) — serves `frontend/dist/` as static files on port 8080; proxies `/api/` → `api:8000`; config at `nginx/nginx.conf`
- FastAPI + Uvicorn — backend container on internal port 8000
- Neo4j 5 — graph database container on internal port 7687; data persisted to Docker volume `neo4j_data`

**Orchestration:**
- Docker Compose — `docker-compose.yml` defines three services: `neo4j`, `api`, `nginx`

## Platform Requirements

**Development:**
- Node.js (version not pinned; no `.nvmrc`)
- Python 3.12
- Docker + Docker Compose

**Production:**
- Docker Compose deployment
- Environment variable: `NEO4J_PASSWORD` must be set in `.env`

---

*Stack analysis: 2026-06-20*
