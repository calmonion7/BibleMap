---
last_mapped_commit: 42bd230af7e22bc1839023a1189d6ae696944188
mapped: 2026-06-20
---

# TESTING.md

## Current State

There are **no automated tests** in this repository. No test files, no test directories, and no test runner configuration exist anywhere in the codebase.

Evidence:
- `frontend/package.json`: no `test` script, no `vitest`/`jest`/`@testing-library` dependencies.
- `frontend/`: no `*.test.*`, `*.spec.*`, or `__tests__/` found.
- `backend/`: no `pytest.ini`, `pyproject.toml`, `setup.cfg`, `conftest.py`, or `test_*.py` files found.
- `backend/requirements.txt` lists only `fastapi`, `neo4j`, `uvicorn` — no `pytest`, `httpx`, or test dependencies.

## Manual / Playwright Verification

Per project memory (`MEMORY.md`), UI behavior verification uses **Python Playwright** installed at `/opt/homebrew`. The pattern is network capture + screenshot against `localhost:8080`. This is an ad-hoc verification step, not an automated test suite.

## How to Run Linting (only automated check available)

```sh
cd frontend
npm run lint
# invokes: eslint .
```

ESLint config: `frontend/eslint.config.js`
Ignores: `dist/`

## Build Verification

The project's primary correctness check is a successful production build:

```sh
cd frontend && npm run build
# outputs to frontend/dist/
```

After building, the full stack runs via:

```sh
docker compose up -d --build api
# nginx serves frontend/dist on :8080
# api runs on :8000 (not externally exposed)
```

`VITE_API_URL=/api` is set at build time via `.env.production` (nginx proxies `/api` → `api:8000`).

## Test Framework Configuration (if tests are added)

No framework is currently configured. The tech stack would accommodate:

**Frontend**: Vitest (Vite-native), `@testing-library/react`
**Backend**: pytest + `httpx` (ASGI transport) for FastAPI endpoint testing

No coverage tool, no coverage thresholds, no CI pipeline configuration exists in the repository.
