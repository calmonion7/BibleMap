---
last_mapped_commit: 4ed4d876d7fa3b06a8eb1647b5b50ed73f906b25
mapped: 2026-06-19
---

# 테스팅

## 현황 요약

**이 프로젝트에는 자동화 테스트가 존재하지 않습니다.**

프론트엔드와 백엔드 모두 테스트 파일, 테스트 러너 설정, 테스트 디렉터리가 없음이 확인되었습니다.

---

## 프론트엔드

- `frontend/package.json` 에 테스트 스크립트(`test`) 없음
- `vitest.config.*`, `jest.config.*` 파일 없음
- `@testing-library/*`, `vitest`, `jest` 등 테스트 관련 의존성 없음
- `*.test.{js,jsx}`, `*.spec.{js,jsx}` 파일 없음

사용 중인 devDependencies (`frontend/package.json`):
- `vite` — 번들러
- `@vitejs/plugin-react` — Vite React 플러그인
- `eslint` + 플러그인들 — 린터
- `@types/react`, `@types/react-dom` — TypeScript 타입 (타입 체크는 미사용)

---

## 백엔드

- `backend/requirements.txt` 에 `pytest`, `httpx`, `anyio` 등 테스트 의존성 없음
- `pytest.ini`, `pyproject.toml`, `setup.cfg`, `tox.ini` 없음
- `conftest.py` 없음
- `test_*.py`, `*_test.py` 파일 없음

사용 중인 의존성 (`backend/requirements.txt`):
- `fastapi` — 웹 프레임워크
- `neo4j` — DB 드라이버
- `uvicorn` — ASGI 서버

---

## UI 수동 검증 패턴

자동화 테스트 대신, 프로젝트 메모리(MEMORY.md)에 따르면 UI 동작 검증은 Python Playwright로 수동 수행합니다.

- 도구: Python Playwright (`/opt/homebrew` 에 설치)
- 대상 URL: `http://localhost:8080`
- 방법: 네트워크 캡처 + 스크린샷 패턴
- 검증 전 선행 조건: `cd frontend && npm run build` (프론트는 `frontend/dist` 정적 마운트, HMR 아님), `docker compose up -d --build api`

이 Playwright 검증은 CI가 아닌 로컬 수동 실행입니다.

---

## 테스트 추가 시 참고

테스트를 도입하려면:

### 프론트엔드
- `vitest` + `@testing-library/react` 를 `frontend/package.json` devDependencies에 추가
- `frontend/vite.config.js` 에 `test` 블록 추가 또는 `vitest.config.js` 별도 생성

### 백엔드
- `pytest` + `httpx` (FastAPI 비동기 테스트 클라이언트) 를 `backend/requirements.txt` 에 추가
- `backend/tests/` 디렉터리 생성 후 `conftest.py` 에 FastAPI `TestClient` 픽스처 작성
