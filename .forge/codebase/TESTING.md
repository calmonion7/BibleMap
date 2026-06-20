---
last_mapped_commit: ff728ccaffbb9b4e38f1f8f32859a50d3555b515
mapped: 2026-06-20
---

# 테스트 패턴

## 현황: 자동화 테스트 없음

BibleMap 프로젝트에는 **자동화 테스트가 전혀 존재하지 않는다.**

확인 경로:
- `frontend/` — `*.test.js`, `*.test.jsx`, `*.spec.js`, `*.spec.jsx` 파일 0개
- `backend/` — `test_*.py`, `*_test.py` 파일 0개
- `frontend/package.json` — `scripts`에 `test` 항목 없음 (`dev`, `build`, `lint`, `preview`만 존재)
- `frontend/` — `vitest.config.*`, `jest.config.*` 파일 없음
- `frontend/package.json` `devDependencies` — `vitest`, `jest`, `@testing-library/*` 없음
- `backend/` — `pytest`, `unittest` 관련 설정 파일 없음

## 부재 이유 (추정)

`frontend/package.json`과 커밋 히스토리를 보면 프로젝트는 초기 개발 단계부터 지금까지 테스트 인프라를 설치하지 않았다. 프론트엔드는 Playwright를 수동 검증 도구로 사용(`MEMORY.md` 참조)하며, 백엔드는 Neo4j에 직접 적재 후 사람이 눈으로 확인하는 방식으로 검증한다.

## 수동 검증 방식

자동화 테스트 대신 다음 방식으로 동작을 확인한다:

### 프론트엔드

- `cd frontend && npm run build` 후 `docker compose up -d --build api`로 전체 스택 기동.
- **Python Playwright**로 `localhost:8080` 네트워크 캡처 + 스크린샷. (`/opt/homebrew`에 설치)
- 확인 대상: UI 렌더링, API 응답 구조, 지도 상호작용.

### 백엔드 / ETL

- ETL 스크립트는 `MERGE`+`SET` 멱등 패턴으로 작성 → 반복 실행해도 부작용 없음.
- Neo4j Browser 또는 API 엔드포인트로 직접 조회해 데이터 확인.

## 테스트 도입 시 권장 구조

향후 테스트를 추가한다면 기존 스택(Vite + React)에 자연스럽게 맞는 구성:

### 프론트엔드

```
frontend/
  src/
    hooks/
      useSearch.test.js    # 커스텀 훅 단위 테스트
      useNodeSelection.test.js
    utils/
      convexHull.test.js   # 순수 함수 단위 테스트
  vitest.config.js
```

- 프레임워크: **Vitest** (Vite 네이티브, 설정 최소)
- 컴포넌트 테스트: `@testing-library/react`
- 목킹: `vi.mock()` (Vitest 내장)

### 백엔드

```
backend/
  tests/
    test_routes_bible.py
    test_routes_search.py
  pytest.ini (또는 pyproject.toml [tool.pytest.ini_options])
```

- 프레임워크: **pytest** + **httpx** (`AsyncClient`로 FastAPI 라우터 테스트)
- Neo4j 목킹: `pytest-mock` + `unittest.mock.patch('app.db.get_driver', ...)`

## 커버리지

현재 커버리지 설정 없음. 도구도 미설치.
