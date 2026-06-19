---
last_mapped_commit: 7d2210c48a67b08b79cc3f03008c3ee30e885614
mapped: 2026-06-19
---

# BibleMap Directory Structure

## Annotated Tree

```
BibleMap/
├── backend/                        Python FastAPI backend
│   ├── Dockerfile                  Multi-stage build → python:3.12-slim + uvicorn
│   ├── requirements.txt            fastapi, neo4j, uvicorn (pinned versions)
│   ├── __init__.py
│   └── app/                        Application package (served by uvicorn)
│       ├── __init__.py
│       ├── main.py                 FastAPI app instantiation, middleware, router registration
│       ├── db.py                   Neo4j driver singleton (get_driver())
│       └── routes/                 One file per endpoint group
│           ├── __init__.py
│           ├── nodes.py            /node/* and /person/* endpoints
│           ├── events.py           /events, /event/{id}/verses
│           ├── search.py           /search
│           └── books.py            /books
│   └── scripts/                    One-off data pipeline scripts (not imported by app)
│       ├── load_theographic.py     Fetch + load Person/Place/Event/PeopleGroup from GitHub
│       ├── load_books.py           Fetch + load Book nodes, create CONTAINS_BOOK edges
│       ├── load_authored_events.py Load authored_events/events.json → Neo4j Event nodes
│       ├── load_verse_events.py    Load verse_events/events.json → Neo4j
│       ├── inject_book_context.py  Inject book_context/books.json properties into Book nodes
│       ├── inject_ko_names.py      Inject Korean names from names_ko/ into all node types
│       ├── inject_person_traits.py Inject character_traits/people.json into Person nodes
│       ├── generate_approx_book_verses.py  LLM → book_years_approx/books.json
│       ├── generate_book_context.py        LLM → book_context/books.json
│       ├── generate_book_events.py         LLM → book_events/books.json
│       ├── generate_event_verses.py        LLM → event_verses/events.json
│       ├── generate_person_traits.py       LLM → character_traits/people.json
│       ├── generate_verse_events.py        LLM → verse_events/events.json
│       └── generate_verse_text.py          Fetch getbible → embeds textKo/textEn in JSON
│
├── frontend/                       Vite + React 19 SPA
│   ├── index.html                  Shell HTML (root div #root)
│   ├── vite.config.js              React plugin + manual chunk split (maplibre / vendor)
│   ├── package.json                Dependencies: react, react-dom, maplibre-gl, lucide-react
│   ├── eslint.config.js            react-hooks + react-refresh rules
│   ├── .env.production             VITE_API_URL=/api (nginx proxy prefix)
│   ├── public/
│   │   ├── favicon.svg             Compass-style SVG favicon
│   │   └── icons.svg               Sprite sheet for map icons
│   ├── src/
│   │   ├── main.jsx                React root render (StrictMode)
│   │   ├── App.jsx                 Root component — global state, layout, nav bar
│   │   ├── MapView.jsx             MapLibre GL map, place markers, event ring animation
│   │   ├── SidePanel.jsx           Node detail panel (properties, neighbors, traits)
│   │   ├── TimelineView.jsx        Chronological event list, verse drill-down
│   │   ├── VerseLangTabs.jsx       Ko/En language toggle segment control
│   │   ├── api.js                  Shared apiGet() helper (VITE_API_URL base)
│   │   ├── theme.js                TYPE_COLOR, TYPE_KO, TYPE_ORDER, SELECT_HL constants
│   │   ├── convexHull.js           Pure Graham-scan convex hull (used by MapView)
│   │   ├── index.css               Global reset / base styles
│   │   └── assets/                 Static image assets (if any)
│   └── dist/                       Built output (gitignored), mounted by nginx in Docker
│
├── data/                           JSON data files — overlay and seed data
│   ├── authored_events/
│   │   └── events.json             Hand/LLM-authored Event nodes (authored:true, no rec* ID)
│   ├── book_context/
│   │   └── books.json              LLM-generated Book background/themes/keyVerse
│   ├── book_events/
│   │   └── books.json              { bookId: [eventId, ...] } — overlay for 31 approx-year books
│   ├── book_years_approx/
│   │   └── books.json              { bookId: { placementYear, basis } } — estimated timeline year
│   ├── character_traits/
│   │   └── people.json             LLM-generated Person traits with verse refs
│   ├── event_verses/
│   │   └── events.json             { eventId: { books: [{bookId, verses:[{ref,textKo,textEn}]}] } }
│   ├── names_ko/
│   │   ├── books.json              Korean names for Book nodes
│   │   ├── events.json             Korean names for Event nodes
│   │   ├── groups.json             Korean names for PeopleGroup nodes
│   │   ├── people.json             Korean names for Person nodes
│   │   └── places.json             Korean names for Place nodes
│   └── verse_events/
│       └── events.json             Verse-to-event mapping data
│
├── nginx/
│   └── nginx.conf                  Reverse proxy /api/ → api:8000; serve SPA with try_files
│
├── .github/
│   └── workflows/
│       └── deploy.yml              CI/CD pipeline (push → SSH deploy to server)
│
├── .forge/                         Forge task-management system (not app code)
│   ├── CONTEXT.md                  Domain glossary and project decisions
│   ├── adr/                        Architecture Decision Records (ADR-0001 … ADR-0006)
│   ├── backlog/                    Pending task plans
│   ├── codebase/                   Codebase mapping docs (this file + ARCHITECTURE.md)
│   ├── done/                       Completed task archives (one dir per task)
│   ├── executed/                   Executed workflow records
│   ├── quick/LOG.md                Quick-task log
│   └── retro/                      Retrospective notes per task
│
├── .claude/
│   ├── settings.json               Claude Code project settings (bgIsolation: "none")
│   └── settings.local.json         Local overrides
│
├── docker-compose.yml              Services: neo4j, api, nginx
├── .env                            NEO4J_PASSWORD (not committed)
├── .env.example                    Template for .env
├── deploy.sh                       Manual SSH deploy script
├── CLAUDE.md                       Claude Code behavioral guidelines
├── BIBLEMAP_PLAN.md                Original project plan doc
└── README.md                       Project readme
```

## Key File Locations

| Purpose | Path |
|---|---|
| FastAPI app object | `backend/app/main.py` |
| Neo4j driver | `backend/app/db.py` |
| Node detail endpoint | `backend/app/routes/nodes.py` |
| Timeline events endpoint | `backend/app/routes/events.py` |
| Search endpoint | `backend/app/routes/search.py` |
| Books endpoint | `backend/app/routes/books.py` |
| Frontend entry | `frontend/src/main.jsx` |
| Global state / layout | `frontend/src/App.jsx` |
| Map view | `frontend/src/MapView.jsx` |
| Side panel | `frontend/src/SidePanel.jsx` |
| Timeline view | `frontend/src/TimelineView.jsx` |
| API client | `frontend/src/api.js` |
| Shared theme constants | `frontend/src/theme.js` |
| nginx config | `nginx/nginx.conf` |
| Docker Compose | `docker-compose.yml` |
| Domain glossary | `.forge/CONTEXT.md` |
| ADR directory | `.forge/adr/` |

## Naming Conventions

### Backend Python

- Package name: `app` (importable as `from app.db import get_driver`).
- Router files: one word, snake_case, matches resource group (`nodes.py`, `events.py`, `search.py`, `books.py`).
- Private loader functions in routers: prefixed with `_` and named `_load_<resource>()` or `_compute_<resource>()`.
- Script files: verb-noun snake_case — `load_<entity>.py`, `inject_<property>.py`, `generate_<data>.py`.
- Environment variables: `SCREAMING_SNAKE_CASE` (`NEO4J_URI`, `NEO4J_PASSWORD`, `DATA_DIR`).

### Frontend JavaScript/JSX

- Component files: PascalCase `.jsx` (`App.jsx`, `MapView.jsx`, `SidePanel.jsx`, `TimelineView.jsx`, `VerseLangTabs.jsx`).
- Utility/helper files: camelCase `.js` (`api.js`, `theme.js`, `convexHull.js`).
- Exported constants: `SCREAMING_SNAKE_CASE` for palettes/config (`TYPE_COLOR`, `TYPE_KO`, `SELECT_HL`), camelCase functions (`apiGet`, `typeColor`, `typeKo`).
- State variables: camelCase React conventions (`selectedNode`, `activeView`, `searchQuery`).
- Ref variables: suffixed with `Ref` (`mapRef`, `popupRef`, `expandPlaceRef`).

### Data JSON

- Top-level structure per file type:
  - `books.json` (names_ko, book_context, book_events, book_years_approx): `{ "<theographic_id>": { ... } }` keyed by Book theographic_id.
  - `people.json` (names_ko, character_traits): `{ "<theographic_id>": { ... } }` keyed by Person theographic_id.
  - `events.json` (event_verses, authored_events): `{ "<theographic_id>": { ... } }` or flat array.
- Bilingual text fields follow `<property>Ko` / `<property>En` suffix convention (e.g., `textKo`, `textEn`, `nameKo`).
- Korean name translations follow `{ ko: "한글명" }` shape inside names_ko files.
