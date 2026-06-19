---
last_mapped_commit: 7d2210c48a67b08b79cc3f03008c3ee30e885614
mapped: 2026-06-19
---

# Testing

## Current State: No Automated Tests

There are no test files in this repository. Confirmed by exhaustive search:
- No `*.test.js`, `*.spec.js`, `*.test.jsx`, `*.spec.jsx` files under `frontend/src/`
- No `test_*.py` or `*_test.py` files under `backend/`
- No `conftest.py`, `pytest.ini`, or `pyproject.toml` in the backend
- No `jest.config.*` or `vitest.config.*` in the frontend

## No Test Framework Configured

### Frontend
- `frontend/package.json` has no test script, no Jest/Vitest dependency, no `@testing-library` packages
- `frontend/eslint.config.js` only covers linting; no test-related plugins

### Backend
- `backend/requirements.txt` lists only `fastapi`, `neo4j`, `uvicorn` — no `pytest`, `httpx`, or any test dependency
- No `pyproject.toml` with `[tool.pytest.ini_options]`

## No CI Test Step

`/.github/workflows/deploy.yml` contains one job (`deploy`) that pulls the latest `main` branch and runs `bash deploy.sh`. There is no lint, build-check, or test step.

## Manual Verification Approach

Per project memory, UI behavior is validated manually using Python Playwright (`/opt/homebrew` install) against `localhost:8080`. The pattern used is network capture + screenshot. This is ad-hoc per-task verification, not a regression suite.

Frontend must be built (`cd frontend && npm run build`) before verification because `frontend/dist` is served statically by nginx — there is no HMR dev server in the Docker stack.

## Recommendations (not implemented)

If tests are added in the future, the natural choices would be:
- **Backend**: `pytest` + `httpx` (FastAPI's `TestClient` uses httpx under the hood)
- **Frontend**: Vitest (already using Vite; zero config) + `@testing-library/react`
