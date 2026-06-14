---
last_mapped_commit: fb78d740df63d386e84ceb1bb4249921a5e198b7
mapped: 2026-06-14
---

# Technology Stack

**Analysis Date:** 2026-06-14

## Languages

**Primary:**
- JavaScript (ES Modules) — frontend (`frontend/src/`)
- Python 3.12 — backend (`backend/app/`)

**Secondary:**
- JSX — React component files (`frontend/src/*.jsx`)

## Runtime

**Frontend:**
- Browser (ES Module bundle served via nginx)
- Build-time: Node.js (managed by npm)

**Backend:**
- Python 3.12-slim (Docker container, `backend/Dockerfile`)

**Package Manager:**
- Frontend: npm — lockfile: `frontend/package-lock.json`
- Backend: pip — lockfile: none (pinned in `backend/requirements.txt`)

## Frameworks

**Frontend Core:**
- React 19.2.6 — UI component tree (`frontend/src/`)
- React DOM 19.2.6 — DOM rendering (`frontend/src/main.jsx`)

**Backend Core:**
- FastAPI 0.136.3 — HTTP API (`backend/app/main.py`)
- Uvicorn 0.49.0 — ASGI server (CMD in `backend/Dockerfile`)

**Build/Dev:**
- Vite 8.0.12 — frontend dev server and bundler (`frontend/vite.config.js`)
- `@vitejs/plugin-react` 6.0.1 — JSX transform plugin

**Linting:**
- ESLint 10.3.0 — configured in `frontend/eslint.config.js`
- `eslint-plugin-react-hooks` 7.1.1
- `eslint-plugin-react-refresh` 0.5.2

## Key Dependencies

**Frontend:**
- `maplibre-gl` 5.24.0 — map rendering (`frontend/src/MapView.jsx`)
- `cytoscape` 3.34.0 — graph rendering (`frontend/src/GraphView.jsx`)
- `cytoscape-cose-bilkent` 4.1.0 — graph layout algorithm
- `cytoscape-expand-collapse` 4.1.1 — compound node expand/collapse
- `lucide-react` 1.17.0 — icon set (`frontend/src/SidePanel.jsx`, `frontend/src/App.jsx`)

**Backend:**
- `neo4j` 6.2.0 — Neo4j Python driver (`backend/app/db.py`)

## Configuration

**Environment variables:**
- `NEO4J_PASSWORD` — required at runtime; loaded from `.env` (see `.env.example`)
- `NEO4J_URI` — defaults to `bolt://localhost:7687`; set to `bolt://neo4j:7687` in Docker
- `NEO4J_USER` — defaults to `neo4j`
- `VITE_API_URL` — build-time inject; set to `/api` for production (nginx proxy path)

**Build config files:**
- `frontend/vite.config.js` — Vite config (minimal: React plugin only)
- `frontend/eslint.config.js` — ESLint flat config
- `docker-compose.yml` — service topology (neo4j, api, nginx)
- `backend/Dockerfile` — Python 3.12-slim image, pip install, uvicorn CMD

## Platform Requirements

**Development:**
- Node.js (version unspecified; no `.nvmrc`)
- Python 3.12
- Docker + Docker Compose (for neo4j + api services)

**Production:**
- Self-hosted macOS runner (GitHub Actions workflow `self-hosted`)
- Docker Compose services: `neo4j` (image `neo4j:5`), `api` (built from `backend/Dockerfile`), `nginx` (image `nginx:alpine`)
- Port 8080 exposed publicly via nginx

---

*Stack analysis: 2026-06-14*
