---
last_mapped_commit: 60716ea24a78866177eb8fe28dee9c43ced5ff0f
mapped: 2026-06-11
---

# STRUCTURE

## Directory layout

```
BibleMap/
├── backend/                 # FastAPI read API + data scripts
│   ├── app/
│   │   ├── main.py          # app + CORS + lifespan index creation
│   │   ├── db.py            # lazy Neo4j driver (get_driver)
│   │   └── routes/          # nodes.py, events.py, search.py
│   ├── scripts/             # offline data load + ko-name injection
│   ├── Dockerfile           # python:3.12-slim, uvicorn
│   └── requirements.txt
├── frontend/                # React 19 + Vite SPA
│   ├── src/                 # App.jsx + views + SidePanel + entry
│   ├── public/              # favicon.svg, icons.svg (copied into dist)
│   ├── dist/                # build artifact served by nginx (gitignored)
│   ├── index.html           # Vite entry HTML
│   ├── vite.config.js
│   ├── eslint.config.js
│   ├── package.json
│   └── .env.production      # VITE_API_URL=/api
├── nginx/
│   └── nginx.conf           # SPA serving + /api/ reverse proxy
├── data/
│   └── names_ko/            # ko-name source JSON (people/places/events/groups)
├── .github/workflows/
│   └── deploy.yml           # push-to-main CI deploy
├── docker-compose.yml       # neo4j + api + nginx (project name biblemap)
├── deploy.sh                # build → image → restart → inject ko-names
├── .env.example             # NEO4J_PASSWORD template
├── README.md
├── BIBLEMAP_PLAN.md
└── CLAUDE.md
```

There is **no root `scripts/` directory** — the former `scripts/auto-deploy-poll.sh` polling deploy was removed; deploy is now push-triggered CI (`.github/workflows/deploy.yml`). The only scripts are the offline data scripts under `backend/scripts/`.

## Key file locations

| Concern | File |
| --- | --- |
| Backend app / CORS / startup indexes | `backend/app/main.py` |
| Neo4j driver factory | `backend/app/db.py` |
| Node detail / neighbors / places routes | `backend/app/routes/nodes.py` |
| Events (timeline) route | `backend/app/routes/events.py` |
| Search route | `backend/app/routes/search.py` |
| Initial Neo4j data load (Theographic) | `backend/scripts/load_theographic.py` |
| Korean-name injection | `backend/scripts/inject_ko_names.py` |
| Backend image | `backend/Dockerfile` |
| Python deps (pinned) | `backend/requirements.txt` |
| Frontend bootstrap | `frontend/src/main.jsx` |
| Frontend root component / nav / search | `frontend/src/App.jsx` |
| Map view (MapLibre) | `frontend/src/MapView.jsx` |
| Timeline view | `frontend/src/TimelineView.jsx` |
| Graph view (Cytoscape) | `frontend/src/GraphView.jsx` |
| Node detail overlay panel | `frontend/src/SidePanel.jsx` |
| Vite config | `frontend/vite.config.js` |
| ESLint config | `frontend/eslint.config.js` |
| Frontend prod env | `frontend/.env.production` |
| ko-name source data | `data/names_ko/{people,places,events,groups}.json` |
| Service composition | `docker-compose.yml` |
| nginx config | `nginx/nginx.conf` |
| Deploy script | `deploy.sh` |
| CI deploy workflow | `.github/workflows/deploy.yml` |
| Env template | `.env.example` |

## Naming conventions

- **Backend**: snake_case modules and functions; one `APIRouter` per file in `backend/app/routes/`, each exposing a module-level `router`. Magic numbers are hoisted to UPPER_SNAKE module constants (`MAX_NEIGHBORS_PER_TYPE`, `NODE_NEIGHBOR_LIMIT` in `nodes.py`; `SEARCH_LIMIT` in `search.py`). Comments and error/log messages are in Korean.
- **Frontend**: component files are PascalCase `.jsx` (`MapView.jsx`, `SidePanel.jsx`) with a default-exported component of the same name; `App.jsx` is the root. State is local `useState`; selection flows top-down via `selectedNode` prop and `onSelectNode` callback. Each view independently defines `const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'` (`App.jsx` names it `API_BASE`) — no shared API module.
- **Graph data**: Neo4j node labels are PascalCase (`Person`, `Place`, `Event`, `PeopleGroup`); relationship types are UPPER_SNAKE (`HAS_PARTICIPANT`, `OCCURS_AT`, `MEMBER_OF`, `PART_OF`, `PARENT_OF`, `CHILD_OF`, `SIBLING_OF`, `PARTNER_OF`). Node properties are camelCase (`theographic_id` is the snake_case exception, `nameKo`, `aliasesKo`, `startDate`, `sortKey`).
- **Docker compose project name**: `biblemap` (`docker compose -p biblemap` in `deploy.sh`).

## Environment variables

| Var | Used by | Default / notes |
| --- | --- | --- |
| `NEO4J_PASSWORD` | `backend/app/db.py`, `backend/scripts/*`, `docker-compose.yml` (`neo4j` + `api`) | **Required**; no default. `db.py` and both scripts raise `RuntimeError` if unset; compose uses `${NEO4J_PASSWORD:?...}` (fail-fast) for both `NEO4J_AUTH=neo4j/<pw>` and the `api` service. Single source of truth — `NEO4J_AUTH` is derived. |
| `NEO4J_URI` | `backend/app/db.py`, `backend/scripts/*` | `bolt://localhost:7687`; set to `bolt://neo4j:7687` for the `api` container in compose. |
| `NEO4J_USER` | `backend/app/db.py`, `backend/scripts/*` | `neo4j`. |
| `VITE_API_URL` | All `frontend/src/*.jsx` views (build-time) | Dev default `http://localhost:8000`; prod `/api` (`frontend/.env.production`). |

Local secrets live in `.env` (gitignored, loaded by `deploy.sh` via `set -a; . .env`); `.env.example` is the committed template carrying only the `NEO4J_PASSWORD` placeholder. No secret values are committed.

## Gitignored artifacts

- `frontend/dist/` and `frontend/node_modules/` (root `.gitignore`; `frontend/.gitignore` also ignores `dist`/`node_modules`).
- `.env`, `__pycache__/`, `*.py[cod]`, `.venv/`, `.DS_Store`.
