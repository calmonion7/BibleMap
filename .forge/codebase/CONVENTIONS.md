---
last_mapped_commit: 6bc79bba2bb1a869260e73efee7d9366d96a1cc0
mapped: 2026-06-20
---

# Coding Conventions

**Analysis Date:** 2026-06-20

## Language Split

- **Frontend:** JavaScript (ES modules, JSX) — no TypeScript
- **Backend:** Python 3.x — FastAPI, sync handlers

---

## Naming Patterns

**Frontend files:**
- React components: `PascalCase.jsx` (`MapView.jsx`, `SidePanel.jsx`, `BibleOverviewView.jsx`)
- Custom hooks: `camelCase.js` prefixed with `use` (`useSearch.js`, `useNodeSelection.js`)
- Pure utilities: `camelCase.js` (`convexHull.js`, `theme.js`, `api.js`)

**Backend files:**
- Route modules: `snake_case.py` (`nodes.py`, `events.py`, `search.py`, `books.py`)
- Script files: `snake_case.py` with verb prefix (`load_theographic.py`, `generate_event_verses.py`, `inject_ko_names.py`)

**Frontend variables/functions:**
- State variables: `camelCase` (`selectedNode`, `searchQuery`, `highlightIndex`)
- Handler functions: `camelCase` with verb prefix (`handleSelectResult`, `handleTabClick`, `handleNodeLoaded`)
- Event callbacks: `on` prefix for props (`onSelectNode`, `onBack`, `onNodeLoaded`)
- Constants: `SCREAMING_SNAKE_CASE` (`TABS`, `MOBILE_QUERY`, `SHEET_VH`, `NAV_H`, `SEARCH_LIMIT`)
- Shared color/label maps: `SCREAMING_SNAKE_CASE` objects (`TYPE_COLOR`, `TYPE_KO`, `TYPE_ORDER`)
- Computed ref values: `camelCase` + `Ref` suffix (`mapRef`, `popupRef`, `expandPlaceRef`, `searchBoxRef`)

**Backend variables/functions:**
- Route handlers: `snake_case` (`get_node`, `get_events`, `search`, `get_books_overview`)
- Internal helpers: `_snake_case` with leading underscore (`_load_approx_book_index`, `_compute_events`, `_load`, `_resolve`)
- Module-level singletons: `_snake_case` (`_driver`)

**Property naming — API shape:**
- Bilingual name fields: `name` (English) + `nameKo` (Korean) pair, always both present
- Missing translation sentinel: `nameKoMissing: bool` alongside the pair
- Graph node identity: `theographic_id` (Neo4j property) → serialized as `id` in API responses

---

## Code Style

**Frontend formatting:**
- No Prettier config present — style inferred from files
- Single quotes for strings
- No semicolons at statement ends (except single-line multi-statement: `setA(x); setB(y)`)
- 2-space indentation
- Arrow functions for inline handlers, `function` declarations for named component/hook functions
- `export default` at file end for components; named exports for utilities (`export function`, `export const`)

**Backend formatting:**
- 4-space indentation (PEP 8)
- Module-level docstrings on cached functions (triple-quoted)
- Inline comments in Korean for domain logic; English for technical mechanics

**ESLint config:** `frontend/eslint.config.js` — `@eslint/js` recommended + `eslint-plugin-react-hooks` recommended + `eslint-plugin-react-refresh`

---

## Import Organization

**Frontend order (observed):**
1. React named imports (`import { useState, useEffect, ... } from 'react'`)
2. Third-party libraries (`import maplibregl from 'maplibre-gl'`)
3. Third-party CSS (`import 'maplibre-gl/dist/maplibre-gl.css'`)
4. Local components (`import MapView from './MapView'`)
5. Local utilities/hooks/theme (`import { typeColor } from './theme'`, `import { apiGet } from './api'`)

**Backend order (observed):**
1. Standard library (`import functools`, `import json`, `import os`)
2. Third-party (`from fastapi import ...`)
3. Local app modules (`from ..db import get_driver`, `from .. import overlays`)

---

## API Client Pattern

All frontend fetches go through `frontend/src/api.js`:

```js
// Single entry point — never call fetch() directly in components
export async function apiGet(path, { signal } = {}) {
  const res = await fetch(API_BASE + path, { signal })
  if (!res.ok) { const err = new Error(String(res.status)); err.status = res.status; throw err }
  return res.json()
}
```

- `AbortController` is used in every long-lived effect to cancel in-flight requests on cleanup
- `AbortError` is distinguished by `e.name === 'AbortError'` and silently ignored
- Non-OK HTTP status becomes `err.status` on the thrown Error object

---

## Error Handling

**Frontend:**
- Async effects: `try/catch` inside `setTimeout` or `.then().catch()` chains
- AbortError is always silently ignored: `if (e.name === 'AbortError') return`
- Error state stored as boolean (`setError(true)`) or as `e?.status ?? String(e)`
- UI shows inline error message strings, never throws to boundary

**Backend:**
- `HTTPException(status_code=404, detail="Node not found")` for missing nodes in `nodes.py`
- Coordinate parsing wrapped in `try/except (TypeError, ValueError): continue` (skip bad records)
- JSON parse fallback: `except Exception: clean_props["traits"] = []`
- Startup index creation: `except Exception: logging.exception(...)` then continue (non-fatal)
- Overlay loading: returns `{}` on `json.JSONDecodeError` (silent degraded mode)
- `db.get_driver()` raises `RuntimeError` if `NEO4J_PASSWORD` is not set (fail-fast at startup)

---

## State Management Pattern

**Custom hooks extract stateful logic from components:**
- `useNodeSelection.js` — selected node, navigation history, personEventIds
- `useSearch.js` — search query, results, debounce timer, dropdown state

**`useCallback([], [])` for stable references:**
```js
// selectNode is stable — avoids spurious MapView useEffect re-runs
const selectNode = useCallback((id) => { ... }, [])
// Latest value read via ref, not closure
useEffect(() => { selectedNodeRef.current = selectedNode }, [selectedNode])
```

**CSS-toggle view preservation:**
All three top-level views (`MapView`, `TimelineView`, `BibleOverviewView`) stay mounted and are toggled with `display: none / block` to preserve state across tab switches.

---

## Comments

**When to comment:**
- Explain non-obvious behavior or constraints at the top of a module or function
- Korean for domain/product rationale; English for technical mechanics (both appear)
- Inline comments for cross-cutting constraints that would be confusing without context (e.g., "react-hooks v7 OK", "R은 표시 줌에서 계산")

**JSDoc:**
- Used only in `convexHull.js` for the pure algorithm function
- Not used for React components or hooks

---

## Module Design

**Exports:**
- One default export per file (component or hook)
- Theme constants use named exports: `export const TYPE_COLOR`, `export function typeColor`
- No barrel (`index.js`) files — all imports use direct file paths

**Shared constants location:**
- Color palette, Korean labels, display order: `frontend/src/theme.js`
- API base URL and `apiGet` helper: `frontend/src/api.js`

**Backend caching:**
- `@functools.lru_cache(maxsize=1)` for data loaded once from disk or Neo4j at startup
- Applied to `_compute_events`, `_load_approx_book_index`, `book_events_raw`, `approx_years`, `event_verses`
- Cache invalidated only on process restart

---

## Styling

- All styling is inline `style={{...}}` objects on JSX elements — no CSS files, no CSS modules, no Tailwind
- Dark UI base color: `#1a1a2e` (navbar), `#1e2040` (dropdowns/cards)
- Shared color constants centralized in `frontend/src/theme.js`
- Responsive layout: `window.matchMedia('(max-width: 768px)')` checked in `App.jsx`, result passed as props

---

*Convention analysis: 2026-06-20*
