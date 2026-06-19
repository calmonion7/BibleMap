---
last_mapped_commit: 7d2210c48a67b08b79cc3f03008c3ee30e885614
mapped: 2026-06-19
---

# Code Conventions

## Code Style & Linting

### Frontend (JavaScript/JSX)
- ESLint config: `frontend/eslint.config.js` — uses flat config format
- Extends: `@eslint/js` recommended, `eslint-plugin-react-hooks` (flat recommended), `eslint-plugin-react-refresh` (vite preset)
- Files covered: `**/*.{js,jsx}`
- No Prettier configured; no `.prettierrc` present
- Lint script: `npm run lint` (runs `eslint .` from `frontend/`)
- No TypeScript; all source files use `.js` / `.jsx` extensions

### Backend (Python)
- No `pyproject.toml`, `setup.cfg`, `.flake8`, or `ruff.toml` present
- No formatter (Black, isort) configured
- `requirements.txt` pins three direct deps only: `fastapi`, `neo4j`, `uvicorn`
- Korean comments are conventional throughout; docstrings also use Korean

---

## Naming Conventions

### Frontend
- **Files**: PascalCase for React components (`App.jsx`, `MapView.jsx`, `SidePanel.jsx`, `TimelineView.jsx`, `VerseLangTabs.jsx`); camelCase for utilities (`api.js`, `theme.js`, `convexHull.js`)
- **Components**: PascalCase function declarations exported at file bottom (`export default MapView`)
- **Variables/state**: camelCase (`searchQuery`, `selectedNode`, `showDropdown`)
- **Constants**: SCREAMING_SNAKE_CASE for module-level config (`MOBILE_QUERY`, `SHEET_VH`, `NAV_H`, `TABS`, `TYPE_COLOR`, `TYPE_KO`, `TYPE_ORDER`, `SELECT_HL`)
- **Props destructuring**: inline in function signature (`function SidePanel({ nodeId, onSelectNode, ... })`)

### Backend (Python)
- **Modules/files**: snake_case (`main.py`, `db.py`, `load_verse_events.py`, `generate_book_context.py`)
- **Functions**: snake_case; private helpers prefixed with `_` (`_load_approx`, `_compute_events`, `_load_event_verses`)
- **Module-level config**: SCREAMING_SNAKE_CASE (`SEARCH_LIMIT`, `MAX_NEIGHBORS_PER_TYPE`, `NODE_NEIGHBOR_LIMIT`)
- **Candidate path lists**: `_*_CANDIDATES` list pattern for Docker-vs-repo path resolution

---

## Common Patterns

### API Client (Frontend)
Single shared helper in `frontend/src/api.js`:
```js
export async function apiGet(path, { signal } = {}) {
  const res = await fetch(API_BASE + path, { signal })
  if (!res.ok) { const err = new Error(String(res.status)); err.status = res.status; throw err }
  return res.json()
}
```
All fetch calls go through `apiGet`. Base URL is `VITE_API_URL` env var (set at build time for prod, falls back to `http://localhost:8000`).

### Async / Effect Pattern (Frontend)
- `useEffect` with abort/cancel guard to prevent stale responses:
  - Search: `AbortController` + `ctrl.abort()` in cleanup
  - SidePanel: `let cancelled = false` guard, `return () => { cancelled = true }`
- `setState` only called inside async callbacks, not in effect sync body (required by `react-hooks` plugin v7 rule)
- Debounce via `setTimeout` + `clearTimeout` in cleanup (e.g., 250 ms for search)

### Error Handling (Frontend)
- `apiGet` rejects with `err.status` on non-OK HTTP; callers check `e.name === 'AbortError'` to ignore cancellations
- UI renders a plain error message string: `<p style={{color:'#dc3545'}}>불러오지 못했습니다 ({error})</p>`
- No error boundaries; errors are per-component local state

### Error Handling (Backend)
- Routes use `raise HTTPException(status_code=404, detail="...")` for not-found cases
- DB connection errors at startup are caught with `logging.exception(...)` and swallowed (no crash)
- File-load helpers use `try/except (FileNotFoundError, json.JSONDecodeError)` with `continue` over candidate paths; fall back to empty dict `{}`

### Data Caching (Backend)
- `@functools.lru_cache(maxsize=1)` on module-level private functions to cache JSON file loads and Neo4j query results for the process lifetime (e.g., `_compute_events`, `_load_event_verses`, `_load_approx`)
- HTTP cache headers set via `JSONResponse(content=..., headers={"Cache-Control": "max-age=300"})` on stable endpoints; `no-store` on volatile ones

### Data Path Resolution (Backend)
Two-candidate list pattern for Docker-vs-repo environment resolution:
```python
_APPROX_CANDIDATES = [
    os.path.join(os.environ.get("DATA_DIR", "/app/data"), "book_years_approx", "books.json"),
    os.path.join(_REPO_DATA_DIR, "book_years_approx", "books.json"),
]
```
Loader iterates candidates and returns on first successful read. Files: `backend/app/routes/books.py`, `backend/app/routes/events.py`.

### FastAPI Router Structure
- Each route module in `backend/app/routes/` creates its own `router = APIRouter()` and is registered in `backend/app/main.py` via `app.include_router(...)`
- Route handlers are synchronous (`def`, not `async def`) because Neo4j driver calls are blocking

### React Component Structure
- Single-file components; no CSS modules or styled-components — all styles are inline `style={{...}}` objects
- Shared theme constants (colors, labels, display order) centralized in `frontend/src/theme.js`; all components import from there
- Sub-components defined in the same file as their parent when small (e.g., `SectionHeader` inside `SidePanel.jsx`)
- Default export at bottom of file

### Import Organization (Frontend)
Order (no enforced linter rule, but consistent in practice):
1. React hooks (`import { useState, useEffect, ... } from 'react'`)
2. Third-party libraries (`import maplibregl from 'maplibre-gl'`)
3. Local components (`import MapView from './MapView'`)
4. Local utilities/constants (`import { apiGet } from './api'`, `import { TYPE_COLOR } from './theme'`)

### Import Organization (Backend)
Standard Python style, no isort enforced:
1. stdlib (`import os`, `import json`, `import functools`, `import logging`)
2. Third-party (`from fastapi import ...`, `from neo4j import ...`)
3. Local (`from ..db import get_driver`)
