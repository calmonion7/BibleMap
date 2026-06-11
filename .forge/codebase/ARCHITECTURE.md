---
last_mapped_commit: 60716ea24a78866177eb8fe28dee9c43ced5ff0f
mapped: 2026-06-11
---

# ARCHITECTURE

## Overall pattern

Three-tier read-only web app: a **React + Vite SPA** queries a **FastAPI** read API, which reads a **Neo4j** graph. In production an **nginx** container serves the built SPA and reverse-proxies `/api/` to the FastAPI service. All HTTP is GET-only; there are no write endpoints. Data is loaded into Neo4j by standalone scripts, not by the running API.

## Layers

### Frontend — React 19 + Vite SPA (`frontend/`)
- Entry: `frontend/index.html` loads `frontend/src/main.jsx`, which mounts `App` via `createRoot` under `<StrictMode>`.
- Root component `frontend/src/App.jsx` holds all shared state with local `useState` and renders one of three full-screen views plus a floating nav bar with search.
- Build output `frontend/dist/` (gitignored) is the static artifact served by nginx.
- Map rendering uses `maplibre-gl`; graph rendering uses `cytoscape` + `cytoscape-cose-bilkent` + `cytoscape-expand-collapse`; icons from `lucide-react`.

### Backend — FastAPI read API (`backend/app/`)
- Entry: `backend/app/main.py` constructs the `FastAPI` app, configures CORS, and registers three routers.
- A `lifespan` async context manager creates `theographic_id` indexes on `Person`, `Place`, `Event`, `PeopleGroup` at startup; index failure is logged and startup continues.
- CORS (`backend/app/main.py`): `allow_origins=["*"]`, `allow_credentials=False`, `allow_methods=["GET"]`.
- Driver access centralized in `backend/app/db.py` (`get_driver()`), a lazily-initialized module-global Neo4j driver. Fails fast with `RuntimeError` if `NEO4J_PASSWORD` is unset.

### Graph store — Neo4j 5 (`docker-compose.yml` service `neo4j`)
- Labels: `Person`, `Place`, `Event`, `PeopleGroup`.
- Relationship types used in queries/UI: `PARENT_OF`, `CHILD_OF`, `SIBLING_OF`, `PARTNER_OF`, `MEMBER_OF`, `HAS_PARTICIPANT`, `OCCURS_AT`, `PART_OF`.
- Nodes keyed by `theographic_id`; Korean fields `nameKo` / `aliasesKo` are injected post-load.
- Bolt on `7687`, browser on `7474`, both bound to `127.0.0.1` only in compose.

### Reverse proxy — nginx (`nginx/nginx.conf`)
- `location /api/` → `proxy_pass http://api:8000/` (strips `/api` prefix).
- Serves the SPA from `/usr/share/nginx/html` (mounted from `frontend/dist`), with SPA fallback `try_files $uri /index.html`.
- Cache headers: `index.html` no-store; hashed JS/CSS/image/font assets `immutable`, 1 year.

## Data flow

### Request path (production)
Browser → nginx `:8080` → `/api/...` proxied to FastAPI `api:8000` (prefix stripped) → `get_driver()` → Neo4j Bolt → Cypher result mapped to JSON → SPA renders. The SPA reads `VITE_API_URL` (`/api` in `frontend/.env.production`, default `http://localhost:8000` in dev) per component.

### Data load / enrichment path (offline)
1. `backend/scripts/load_theographic.py` fetches Theographic Bible metadata JSON from GitHub and batch-loads nodes/relationships into Neo4j (filters records to `status == "publish"`; creates indexes).
2. `backend/scripts/inject_ko_names.py` reads `data/names_ko/{people,places,events,groups}.json` and `SET`s `nameKo` / `aliasesKo` on matching nodes by `theographic_id`. Run by `deploy.sh` step [4/4] with up to 15 retries.

## Key abstractions

- **`theographic_id`** — universal node identity carried through every API response (`id`) and used by the SPA to fetch detail/neighbors/places.
- **Korean-name fallback** — every response that surfaces a name returns `nameKo` (falling back to `name`) plus a `nameKoMissing` boolean so the UI can flag untranslated entities (e.g. `SidePanel.jsx` renders `(미번역)`).
- **Grouped neighbors** — `/node/{id}/neighbors/grouped` buckets neighbors into `Person`/`Event`/`PeopleGroup`/`Place`, each capped at `MAX_NEIGHBORS_PER_TYPE = 30` (`backend/app/routes/nodes.py`).
- **Label-dispatched place lookup** — `/node/{id}/places` runs a different Cypher query per node label (Person via events, Event direct, PeopleGroup via members' events, else Place itself), deduping by id and dropping null/non-numeric coordinates.

## Entry points

| Tier | File |
| --- | --- |
| Backend app | `backend/app/main.py` |
| Frontend bootstrap | `frontend/src/main.jsx` |
| Frontend root component | `frontend/src/App.jsx` |
| Neo4j driver | `backend/app/db.py` |

## API routes

All routers live under `backend/app/routes/` and are registered in `backend/app/main.py`. All GET.

### `nodes.py`
- `GET /node/{node_id}` — node detail: label, name/nameKo/nameKoMissing, `properties` (excludes `name`/`nameKo`/`theographic_id`/`aliasesKo`), and up to `NODE_NEIGHBOR_LIMIT = 50` neighbors.
- `GET /node/{node_id}/neighbors/grouped` — neighbors bucketed by type, each capped at 30.
- `GET /node/{node_id}/places` — map-pin places for the node (label-dispatched Cypher), returning `{id,name,nameKo,lat,lng,isPrimary}`.

### `events.py`
- `GET /events` — all `Event` nodes with a `startDate`, ordered by `sortKey` ascending; returns `{id,title,nameKo,startDate,sortKey}` with `Cache-Control: no-store`.

### `search.py`
- `GET /search?q=` — case-sensitive substring match on `nameKo` or `name`, limited to `SEARCH_LIMIT = 20`; empty/blank `q` returns `[]`.

## Frontend component graph

`App.jsx` owns `selectedNode`, `activeView`, and search state (`searchQuery`/`searchResults`/`searchError`/`showDropdown`) as local `useState`. State flows top-down: `selectedNode` and the `setSelectedNode` setter (passed as `onSelectNode`) are handed to each view and to `SidePanel`.

- `MapView.jsx` — MapLibre map; fetches `/node/{selectedNode}/places`, plots pins, click selects a node.
- `TimelineView.jsx` — fetches `/events` once, groups by parsed year (BC/AD), click selects.
- `GraphView.jsx` — fetches `/node/{id}` + `/node/{id}/neighbors/grouped` (default node `recjNRR60PAuFtjha` = 모세) and renders a Cytoscape graph; replaces `SidePanel` (panel hidden on graph view).
- `SidePanel.jsx` — overlay panel (non-graph views); fetches `/node/{nodeId}` for detail, slides in when `selectedNode` is set.

Each view component independently reads `import.meta.env.VITE_API_URL`; there is no shared API client module.

## Deployment

Push-triggered CI. `.github/workflows/deploy.yml` runs on `push` to `main` on a `self-hosted` runner: `git fetch` + `git reset --hard origin/main` + `bash deploy.sh`. `deploy.sh` builds the frontend (`npm run build`), rebuilds the `api` image, restarts `api` + `nginx` via `docker compose -p biblemap`, then injects Korean names. (The former polling script `scripts/auto-deploy-poll.sh` and the root `scripts/` directory have been removed.)
