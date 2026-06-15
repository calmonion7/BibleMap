---
last_mapped_commit: 22a678c36e40548a3d00ccf9205862505a59d9cb
mapped: 2026-06-16
---

# Testing Patterns

## 자동화 테스트 현황 — 없음

이 프로젝트에는 **자동화된 테스트 스위트가 존재하지 않는다.** 사실 그대로:

- **프론트엔드(`frontend/`):** vitest / jest / @testing-library 등 테스트 프레임워크 미설치. `frontend/package.json`의 `scripts`는 `dev`, `build`, `lint`, `preview` 4개뿐 — `test` 스크립트 없음.
- **백엔드(`backend/`):** `backend/requirements.txt`는 `fastapi`, `neo4j`, `uvicorn` 3개뿐 — pytest/httpx 등 테스트 의존성 없음.
- **테스트 파일 없음:** `*.test.*`, `*.spec.*`, `test_*.py`, `conftest.py`, `__tests__/`, `tests/` 어느 것도 존재하지 않는다(`node_modules` 제외).
- **CI에 테스트 단계 없음:** `.github/workflows/deploy.yml`은 push→배포만 수행하고 테스트를 돌리지 않는다.

**E2E:** Python Playwright가 호스트(`/opt/homebrew`)에 설치돼 있으나 프로젝트 의존성이 아니다. 리포 내 Playwright 설정 파일·고정 스크립트 없음.

## 실제 검증 방식

모든 검증은 수동(lint + build + 브라우저/Playwright UAT)으로 이뤄진다.

### 1. 린트 (유일한 자동 게이트)

프론트엔드 ESLint만 구성돼 있다.

```bash
cd frontend && npm run lint     # eslint . — 전체 검사
```

- Config: `frontend/eslint.config.js` (flat config)
- 대상 `**/*.{js,jsx}`, 무시 `dist/`
- 주요 규칙: `eslint-plugin-react-hooks` v7 (`react-hooks/set-state-in-effect`, exhaustive-deps), `eslint-plugin-react-refresh`
- 포맷터(prettier/biome) 없음. 백엔드 linter/type-checker 없음.

### 2. 빌드

```bash
cd frontend && npm run build    # vite build → frontend/dist/
```

배포 파이프라인(`deploy.sh`)도 `npm install && npm run build`를 거치므로, 빌드 실패는 곧 배포 실패다.

### 3. 로컬 실행

```bash
# 프론트엔드 (Vite dev, hot-reload O)
cd frontend && npm run dev               # localhost:5173

# 백엔드 (Docker, hot-reload 없음 — 코드 변경 시 반드시 재빌드)
docker compose up -d --build api
```

> 백엔드는 hot-reload가 아니다. `backend/app/**` 변경 후에는 `docker compose up -d --build api`로 이미지를 다시 빌드해야 반영된다(자동배포는 재빌드함).

### 4. 프로덕션 배포 검증

- `main`에 push → `.github/workflows/deploy.yml`(self-hosted)이 `git reset --hard origin/main` 후 `deploy.sh` 실행
- `deploy.sh`: frontend 빌드 → `docker compose build api` → `up -d api nginx` → 한글 이름 주입(`inject_ko_names.py`, Neo4j 준비까지 최대 15회 재시도)
- 배포 후 `localhost:8080`(nginx) 브라우저 직접 확인

### 5. Playwright 임시 UAT (ad-hoc)

재사용 가능한 고정 스크립트는 없다. 메모리 기록 패턴(`feedback_playwright_testing.md`): `localhost:8080` 대상, 네트워크 캡처 + 스크린샷으로 1회성 검증.

```python
# 임시 검증 예시 패턴 (리포에 고정 파일 없음)
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    page = p.chromium.launch().new_page()
    page.goto('http://localhost:8080')
    page.screenshot(path='screenshot.png')
```

## 변경 시 권장 검증 순서

1. `cd frontend && npm run lint` — ESLint 통과(특히 `react-hooks/set-state-in-effect` 위반 여부)
2. 백엔드 변경 시 `docker compose up -d --build api` — 재빌드(hot-reload 아님)
3. `localhost:5173`(dev) 또는 `localhost:8080`(배포본)에서 직접 동작 확인
4. 필요 시 Playwright 임시 스크립트로 네트워크 요청/화면 캡처

## 커버리지

**요구 수준 없음** — 측정 도구·기준 미정의.

## 향후 테스트 도입 시 진입점

**프론트엔드(의존성 없는 순수 함수가 1순위):**
- `frontend/src/convexHull.js` — `convexHull(points)` 순수 함수. 입출력이 `{lng,lat}` 배열로 단순, 외부 의존성 0. 단위 테스트 최적.
- `frontend/src/theme.js` — `typeColor`, `typeKo` 순수 함수.
- `frontend/src/api.js` — `apiGet` fetch 래퍼. fetch 모킹으로 테스트 가능(현재 미사용이므로 도입 시 호출부 통일도 함께 검토).

**백엔드(Neo4j 세션 모킹 필요):**
- `backend/app/routes/search.py` — `/search`. rank(정확>STARTS WITH>CONTAINS) 정렬과 응답 shape 검증.
- `backend/app/routes/nodes.py` — `/node/{id}`(`neighbors`/`neighborTotal`/`properties` 포함, Book 타입의 `topPersons`/`topEvents` 추가), `/node/{id}/places`(타입별 Cypher 분기), `/node/{id}/neighbors/grouped`.
- `backend/app/routes/books.py` — 추정연도 오버레이(`yearApprox`, 연도 없는 책 제외) 로직.

**핵심 시나리오:**
- Person 선택 시 hull polygon이 장소 3개 이상에서만 표시(`MapView.jsx`)
- Book 노드 응답에 `topPersons`/`topEvents` 포함, 비-Book엔 미포함
- `Person.traits` JSON 파싱 실패 시 빈 배열 폴백(`nodes.py`)
- 검색 debounce(250ms)·연속 입력 시 직전 요청 abort(`App.jsx`)
- stale 응답 가드: `state.id === nodeId`로 이전 노드 응답 무시(`SidePanel.jsx`)
- `collapsed` 토글: `undefined`→`false`→`undefined` 순환, trait 원문 lazy-fetch는 `verse_ref` 키로 1회만
- `books.py`/`events.py` 응답의 `Cache-Control: no-store` 헤더
