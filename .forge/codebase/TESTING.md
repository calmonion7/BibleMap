---
last_mapped_commit: 6bc79bba2bb1a869260e73efee7d9366d96a1cc0
mapped: 2026-06-20
---

# Testing Patterns

**Analysis Date:** 2026-06-20

## Test Framework

**Status: No automated tests exist in this project.**

- No `*.test.*` or `*.spec.*` files found anywhere in the repository
- No `jest.config.*`, `vitest.config.*`, `pytest.ini`, `conftest.py`, or `setup.cfg` present
- `frontend/package.json` contains no test script and no test-related devDependencies
- `backend/requirements.txt` contains only `fastapi`, `neo4j`, `uvicorn`

---

## Manual Verification Method

The project is verified manually using **Python Playwright** against `localhost:8080` after a production build:

1. Build frontend: `cd frontend && npm run build` (writes `frontend/dist/`)
2. Rebuild API container: `docker compose up -d --build api`
3. Run Playwright: Python scripts at `/opt/homebrew` — network capture + screenshot pattern

This is the only verification workflow in use. There is no watch mode, no coverage target, and no CI gate.

---

## Implicit Test Boundaries

Since there are no automated tests, the following areas have zero coverage and would be the highest-priority targets if tests were added:

**Backend route logic (`backend/app/routes/`):**
- `nodes.py` — label-dispatch branching (5 branches: Person/Event/PeopleGroup/Book/Place), neighbor grouping logic, coordinate float-parse guards
- `events.py` — `_compute_events` merge of CONTAINS_BOOK + approx index, `_load_approx_book_index` reverse-map build
- `search.py` — rank ordering (exact=0, prefix=1, contains=2)
- `books.py` — approx-year fallback logic, book exclusion when both sources lack a year

**Frontend pure utilities (`frontend/src/`):**
- `convexHull.js` — Graham scan algorithm (this is the only file with a JSDoc signature, suggesting it was written with testability in mind)
- `theme.js` — `typeColor`, `typeKo` lookup functions

**Frontend hooks (`frontend/src/`):**
- `useSearch.js` — 250ms debounce, AbortController race cancellation, typeFilter/typeCounts derivation
- `useNodeSelection.js` — history stack push/pop, `selectNodeFresh` history reset

**Backend data loading (`backend/app/overlays.py`):**
- `_load` — missing file path returns `{}`, JSON decode error returns `{}`
- Path resolution priority: `DATA_DIR` env var → repo `data/` directory

---

## Recommended Test Stack (not yet implemented)

If tests were added, the following would match the existing project style:

**Backend:**
```bash
pip install pytest pytest-asyncio httpx
pytest backend/
```

**Frontend:**
```bash
npm install --save-dev vitest @testing-library/react
# vitest is the natural choice for a Vite project
```

**Pure algorithm unit test target:**
- `frontend/src/convexHull.js` — `convexHull()` takes `[{lng, lat}]` and returns a subset; testable without DOM or React

---

## Run Commands

```bash
# No test commands configured — manual verification only

# Frontend lint (only automated quality check present)
cd frontend && npm run lint

# Manual verification sequence
cd frontend && npm run build
docker compose up -d --build api
# Then run Playwright scripts against localhost:8080
```

---

*Testing analysis: 2026-06-20*
