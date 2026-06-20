---
last_mapped_commit: 42bd230af7e22bc1839023a1189d6ae696944188
mapped: 2026-06-20
---

# Integrations

## Database: Neo4j

- **Driver**: `neo4j==6.2.0` (Python) via `backend/app/db.py`
- **Protocol**: Bolt (`bolt://`)
- **Docker image**: `neo4j:5` (Community Edition)
- **Ports** (host-restricted): `127.0.0.1:7474` (HTTP browser), `127.0.0.1:7687` (Bolt)
- **Volume**: `neo4j_data` Docker named volume → `/data`
- **Auth**: `NEO4J_AUTH=neo4j/<NEO4J_PASSWORD>` set by Compose

### Connection (runtime)

Resolved in `backend/app/db.py` via environment variables:

| Env Var | Default | Source |
|---------|---------|--------|
| `NEO4J_URI` | `bolt://localhost:7687` | Compose sets `bolt://neo4j:7687` |
| `NEO4J_USER` | `neo4j` | Compose hardcodes `neo4j` |
| `NEO4J_PASSWORD` | *(required, no default)* | `docker-compose.yml` `${NEO4J_PASSWORD}` |

### Node Labels Used

`Person`, `Place`, `Event`, `PeopleGroup`, `Book`

### Indexes Created on Startup (`backend/app/main.py`)

`theographic_id` property index on each of the five labels above.

### Relationship Types Referenced in Queries

| Relationship | Used in |
|-------------|---------|
| `HAS_PARTICIPANT` | `nodes.py` — person places, neighbors |
| `OCCURS_AT` | `nodes.py` — event/person/group places |
| `MEMBER_OF` | `nodes.py` — group places |
| `CONTAINS_BOOK` | `nodes.py` (book places), `events.py`, `books.py` |

## External Map Services (Frontend, no API key required)

### ESRI NatGeo World Map (raster tiles)

- **URL pattern**: `https://server.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}`
- **Usage**: Base map layer in `frontend/src/MapView.jsx`
- **Auth**: None (public tile endpoint)

### Protomaps Basemaps Assets (vector glyphs)

- **URL pattern**: `https://protomaps.github.io/basemaps-assets/fonts/{fontstack}/{range}.pbf`
- **Usage**: MapLibre GL font glyphs in `frontend/src/MapView.jsx`
- **Auth**: None (public CDN)

## Reverse Proxy (nginx)

- **Config**: `nginx/nginx.conf`
- **Port**: `8080` on host → `80` inside container
- **API routing**: `location /api/` → `http://api:8000/` (strips `/api` prefix via `proxy_pass`)
- **SPA routing**: `try_files $uri /index.html` for all non-asset paths
- **Static files**: `frontend/dist/` mounted read-only at `/usr/share/nginx/html`

## Environment Variables Summary

| Variable | Where Set | Consumed By |
|----------|-----------|-------------|
| `NEO4J_PASSWORD` | `.env` (host), `docker-compose.yml` interpolation | `neo4j` container auth, `api` container connection |
| `NEO4J_URI` | `docker-compose.yml` (`bolt://neo4j:7687`) | `backend/app/db.py` |
| `NEO4J_USER` | `docker-compose.yml` (`neo4j`) | `backend/app/db.py` |
| `VITE_API_URL` | `frontend/.env.production` (`/api`) | `frontend/src/api.js` at build time |
| `DATA_DIR` | Not set in Compose (falls back to `/app/data`) | `backend/app/overlays.py` file resolution |

## Static Data Files (Local JSON Overlays)

Not a network integration — JSON files on disk mounted via Docker volume `./data:/app/data`. Loaded by `backend/app/overlays.py` using `functools.lru_cache`.

| Overlay | File Path | API consumer |
|---------|-----------|-------------|
| Book→Event map | `data/book_events/books.json` | `events.py` `_load_approx_book_index()`, `books.py` `get_books()` |
| Approx composition years | `data/book_years_approx/books.json` | `books.py` `get_books()` |
| Event→Verse map | `data/event_verses/events.json` | `events.py` `get_event_verses()` |

## Auth / Security

- No authentication layer on the API. CORS middleware in `backend/app/main.py` allows all origins (`allow_origins=["*"]`), methods restricted to `GET` only.
- No external auth provider (no OAuth, JWT, sessions, or API keys in the codebase).
- Neo4j port binding is restricted to `127.0.0.1` (loopback only) in `docker-compose.yml` — not exposed externally.
