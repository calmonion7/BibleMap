---
last_mapped_commit: ecdb7cb2ea1bf665b0690e62b4cf51261761072c
mapped: 2026-06-15
---

# Testing Patterns

## 자동화 테스트 현황

**단위/통합 테스트:** 없음.
- 프론트엔드(`frontend/`): jest, vitest, testing-library 등 테스트 프레임워크 미설치. `package.json`에 test 스크립트 없음.
- 백엔드(`backend/`): pytest, httpx 등 테스트 패키지 미포함. `requirements.txt`에 테스트 의존성 없음.
- 테스트 파일(`.test.*`, `.spec.*`, `test_*.py`) 없음.

**E2E 테스트:** Python Playwright가 `/opt/homebrew`에 호스트 설치됨 (프로젝트 의존성 아님). 프로젝트 내 Playwright 설정 파일·스크립트 없음.

## 수동 검증 패턴

프로젝트의 모든 검증은 수동 방식으로 진행된다.

**로컬 실행:**
```bash
# 프론트엔드
cd frontend && npm run dev     # localhost:5173

# 백엔드 (hot-reload 없음 — 코드 변경 시 반드시 재빌드)
docker compose up -d --build api
```

**프로덕션 배포 검증:**
- GitHub push → 자동 배포 파이프라인 실행
- 배포 후 프로덕션 URL에서 브라우저 직접 확인

**Playwright 임시 검증 (ad-hoc):**
메모리에 기록된 패턴(`feedback_playwright_testing.md`): `localhost:8080` 대상, 네트워크 캡처 + 스크린샷. 재사용 가능한 스크립트 없음 — 필요 시 1회성으로 작성.

```python
# 임시 검증 예시 패턴 (고정 파일 없음)
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto('http://localhost:8080')
    page.screenshot(path='screenshot.png')
    browser.close()
```

## 린트

프론트엔드에서 ESLint만 구성되어 있다.

```bash
cd frontend && npm run lint     # ESLint 전체 검사
```

- Config: `frontend/eslint.config.js`
- 대상: `**/*.{js,jsx}`
- 주요 규칙: react-hooks v7 (`exhaustive-deps`, setState-in-effect), react-refresh
- 포맷터(prettier/biome) 없음

백엔드에 linter/type-checker 설정 없음.

## 새 기능 추가 시 검증 순서

1. `cd frontend && npm run lint` — ESLint 통과 확인 (특히 react-hooks 위반)
2. `docker compose up -d --build api` — 백엔드 코드 변경 시 재빌드
3. 브라우저에서 `localhost:5173`(개발) 또는 배포 URL에서 직접 동작 확인
4. 필요 시 Playwright 임시 스크립트로 네트워크 요청/화면 캡처 검증

## 커버리지

**요구 수준:** 없음 (도구·기준 미정의).

## 향후 테스트 도입 시 참고

**프론트엔드 추천 진입점 (의존성 없는 순수 함수):**
- `frontend/src/convexHull.js` — `convexHull(points)` 순수 함수, 입력·출력이 단순한 배열. 단위 테스트에 가장 적합.
- `frontend/src/theme.js` — `typeColor`, `typeKo` 순수 함수. 의존성 없음.
- `frontend/src/api.js` — `apiGet` fetch 래퍼. fetch 모킹으로 단위 테스트 가능.

**백엔드 추천 진입점:**
- `backend/app/routes/search.py` — `/search` 라우트. Neo4j 세션 모킹 후 Cypher 쿼리 결과 shape 검증.
- `backend/app/routes/nodes.py` — `/node/{id}` 라우트. 응답에 `neighbors`, `neighborTotal`, `properties` 포함 여부, Book 타입의 `topPersons`/`topEvents` 필드 검증.

**주요 테스트 시나리오:**
- Person 선택 시 hull polygon이 3개 이상 장소에서만 표시되는지
- Book 노드 응답에 `topPersons`, `topEvents` 포함 여부
- `traits` JSON 파싱 실패 시 빈 배열 폴백 동작
- 검색 debounce: 250ms 이내 입력 변경 시 이전 요청 abort
- `collapsed` 토글: `undefined` → `false` → `undefined` 순환
