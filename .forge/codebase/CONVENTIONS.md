---
last_mapped_commit: 42bd230af7e22bc1839023a1189d6ae696944188
mapped: 2026-06-20
---

# CONVENTIONS.md

## Code Style

### Frontend (JavaScript/JSX)

- **Format**: No Prettier config present. No `.prettierrc` or `prettier` devDependency.
- **Linter**: ESLint v10 via `frontend/eslint.config.js` using flat config format.
  - Extends `@eslint/js` recommended, `eslint-plugin-react-hooks` flat recommended, `eslint-plugin-react-refresh` vite preset.
  - Files: `**/*.{js,jsx}` only — no TypeScript.
  - `dist/` is globally ignored.
- **Module system**: ESM throughout (`"type": "module"` in `frontend/package.json`).
- **JSX**: `.jsx` for components, `.js` for non-JSX modules. No `.ts`/`.tsx`.
- **Indentation**: 2-space indentation, single-quoted strings (observed in all source files).
- **Trailing semicolons**: absent — semicolons are omitted (observed across `api.js`, `theme.js`, `useSearch.js`).
- **Inline styles**: All component styling uses inline `style={{}}` objects — no CSS modules, no Tailwind, no styled-components.

### Backend (Python)

- **Version**: Python 3.12 (Dockerfile: `FROM python:3.12-slim`).
- **Formatter/linter**: No config files found (`pyproject.toml`, `setup.cfg`, `.flake8` absent). Style is consistent PEP 8 by convention.
- **Imports**: stdlib first, then third-party (`fastapi`, `neo4j`), then local (`..db`, `..overlays`).
- **Type annotations**: absent from route function signatures; used only in comments (e.g., `event_to_books: dict`).

---

## Naming Conventions

### Variables and Functions

**Frontend**:
- camelCase for all variables and functions: `selectedNode`, `handleNodeLoaded`, `onSearchInput`, `clearSearch`.
- Boolean state variables use `is`/`can`/`show` prefixes: `isMobile`, `canGoBack`, `showDropdown`.
- Event handler functions are prefixed `handle` or `on`: `handleTabClick`, `handleSelectResult`, `onSheetTouchStart`.
- Constants are ALL_CAPS: `MOBILE_QUERY`, `SHEET_VH`, `NAV_H`, `SEARCH_LIMIT`, `MAX_NEIGHBORS_PER_TYPE`.
- Refs are suffixed `Ref`: `mapContainer`, `mapRef`, `popupRef`, `expandPlaceRef`, `searchBoxRef`.

**Backend**:
- snake_case for all functions and variables: `get_driver`, `get_node`, `book_events_raw`, `event_to_books`.
- Private/internal functions are prefixed `_`: `_load_approx_book_index`, `_compute_events`, `_load`, `_resolve`.
- Module-level cached singletons prefixed `_`: `_driver` in `backend/app/db.py`.

### Files and Directories

**Frontend** (`frontend/src/`):
- React component files: PascalCase `.jsx` — `App.jsx`, `MapView.jsx`, `SidePanel.jsx`, `TimelineView.jsx`, `BibleOverviewView.jsx`, `VerseLangTabs.jsx`, `Spinner.jsx`.
- Custom hook files: camelCase `.js` prefixed `use` — `useNodeSelection.js`, `useSearch.js`.
- Utility/service files: camelCase `.js` — `api.js`, `theme.js`, `convexHull.js`.

**Backend** (`backend/app/`):
- Route modules: lowercase singular noun — `nodes.py`, `events.py`, `search.py`, `books.py`.
- Route modules live in `backend/app/routes/`.
- Shared utilities at app level: `db.py`, `overlays.py`, `main.py`.
- Data-loading scripts: `backend/scripts/`, named `load_<entity>.py` or `generate_<thing>.py` or `inject_<thing>.py`.

### Component Props

- Callbacks passed as props are named `on<Action>`: `onSelectNode`, `onBack`, `onNodeLoaded`.
- State lifters passed down are named `set<State>`: `setVerseLang`.
- Boolean props: plain adjective or `can<X>`: `canGoBack`, `isSelected`, `isVisible`.

---

## Patterns

### Custom Hooks (`frontend/src/`)

Two custom hooks encapsulate stateful logic extracted from `App.jsx`:

- **`useNodeSelection`** (`frontend/src/useNodeSelection.js`): manages `selectedNode`, navigation `history`, `selectedNodeMeta`, and `personEventIds`. Uses `useCallback([])` with a `useRef` mirror (`selectedNodeRef`) to stabilize callback references and prevent spurious effect re-runs in child components.
- **`useSearch`** (`frontend/src/useSearch.js`): manages search query, debounced API fetch (250ms), AbortController race cancellation, dropdown visibility, keyboard highlight index, and type filter. All `setState` calls occur inside `setTimeout`/async callbacks (not in effect body) to comply with `eslint-plugin-react-hooks` v7 rules.

### API Client Pattern

All HTTP calls go through `frontend/src/api.js` (`apiGet`):
- Single base URL from `import.meta.env.VITE_API_URL` or `http://localhost:8000`.
- Returns parsed JSON; throws `Error` with `.status` property on non-OK responses.
- Passes `AbortSignal` through for cancellation; `AbortError` propagates to callers which check `e.name === 'AbortError'`.

### Shared Palette / Theme Module

`frontend/src/theme.js` is the single source of truth for node-type colors (`TYPE_COLOR`), Korean labels (`TYPE_KO`), display order (`TYPE_ORDER`), and selection highlight (`SELECT_HL`). All views import from here — no inline color duplication.

### View Mounting Strategy

All three top-level views (`MapView`, `TimelineView`, `BibleOverviewView`) are always mounted; visibility is toggled via `display: activeView === '...' ? 'block' : 'none'` in `App.jsx`. This preserves map/timeline scroll state across tab switches.

### Backend: Router-per-Resource

Each logical resource has its own `APIRouter` in `backend/app/routes/`:
- `nodes.py` — `/node/{id}`, `/node/{id}/places`, `/node/{id}/neighbors/grouped`, `/person/{id}/event-ids`
- `events.py` — `/events`, `/event/{id}/verses`
- `search.py` — `/search`
- `books.py` — `/books`, `/books-overview`

All routers are included in `backend/app/main.py` via `app.include_router(...)`.

### Backend: Overlay / Static Data

`backend/app/overlays.py` loads JSON files from `data/` as read-only overlays. Each loader is decorated with `@functools.lru_cache(maxsize=1)` — data is loaded once on first call and kept in memory for the process lifetime. The `DATA_DIR` env var overrides the repo-relative path (for Docker: `/app/data`).

### Backend: DB Singleton

`backend/app/db.py` keeps a single `GraphDatabase.driver` instance in a module-level `_driver`. `get_driver()` initializes on first call using `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD` env vars. Missing password raises `RuntimeError` immediately.

### Backend: Heavy Query Caching

Expensive Neo4j aggregations in `events.py` are wrapped in `@functools.lru_cache(maxsize=1)` private functions (`_compute_events`, `_load_approx_book_index`). Results live for the process lifetime; no cache invalidation.

### Error Handling

**Frontend**:
- API errors are caught with `.catch()` and set a boolean `error` state (`setError(true)`). Components render a plain error message string, never re-throw.
- Stale response guard: components track which `id` they rendered last; responses for a different id are discarded (`if (!cancelled)` or `if (id !== nodeId)`).
- AbortError from cancelled fetches is silently ignored (`if (e.name === 'AbortError') return`).

**Backend**:
- Routes raise `HTTPException(status_code=404)` for missing nodes.
- `db.py` raises `RuntimeError` for missing password — deliberate startup failure.
- `overlays.py` returns `{}` on missing file or `json.JSONDecodeError` — silent fallback, no exception propagation.
- `main.py` lifespan catches Neo4j index creation failure with `logging.exception` and continues.
