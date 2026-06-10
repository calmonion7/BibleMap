---
last_mapped_commit: 26240c7cf18f421b2f8baa4fd6584f40eede57b0
mapped: 2026-06-11
---

# 테스트

## 현황: 자동화 테스트가 전혀 없다

BibleMap에는 테스트 코드, 테스트 프레임워크, 테스트 설정이 **하나도 없다.** (커밋 `26240c7` 기준)

확인한 사실:

- 테스트 파일 없음 — `*test*`, `*spec*`, `conftest.py` 등 어떤 패턴으로도 검색되지 않는다 (`backend/`, `frontend/src/` 전체).
- 백엔드: `backend/requirements.txt`에 `pytest`/`unittest`/`mock` 등 테스트 의존성이 없다. `pyproject.toml`/`setup.cfg`/`tox.ini`/`pytest.ini` 같은 설정 파일도 없다.
- 프론트엔드: `frontend/package.json`에 `test` 스크립트가 없고(`dev`/`build`/`lint`/`preview`만), Jest/Vitest/Testing Library/Playwright 등 테스트 의존성이 없다.
- CI: `.github/workflows/deploy.yml`는 배포만 수행한다. 테스트/린트 게이트가 없다 — `main` push 시 `git reset --hard` 후 곧장 `deploy.sh`를 돌린다.

## 현재 존재하는 검증 수단

테스트는 아니지만 코드 품질·런타임을 확인하는 메커니즘:

- **ESLint** (`frontend/eslint.config.js`) — `npm run lint`로 실행 가능. 정적 분석만, 테스트는 아니다.
- **런타임 진행 로그** — 데이터 적재 스크립트(`backend/scripts/load_theographic.py`, `inject_ko_names.py`)는 단계별 `print(...)`와 처리 건수 출력으로 결과를 사람이 눈으로 검증하게 돼 있다. 자동 단언은 없다.
- **배포 재시도 가드** — `deploy.sh`는 한글 이름 주입을 최대 15회 재시도하며 성공/대기 로그를 남긴다.

수동 검증 흐름은 `README.md`의 로컬 실행 절차(Neo4j 기동 → 데이터 적재 → API 서버 → 프론트엔드 `npm run dev`)에 의존한다.

## 테스트를 도입한다면 (현재 코드 기준 셋업 제안)

요청 시 참고할 수 있는, 기존 스택과 정합하는 최소 셋업:

### 백엔드 (Python / FastAPI + Neo4j)

- 프레임워크: `pytest`를 `backend/requirements.txt`(또는 별도 dev 의존성 파일)에 추가.
- API 테스트: FastAPI의 `TestClient`(starlette) 또는 `httpx`로 라우트 엔드포인트 검증.
- Neo4j 의존성 처리가 핵심 난점 — 라우트 핸들러가 `get_driver()`(전역 싱글톤, `backend/app/db.py`)를 직접 호출하므로 다음 중 하나가 필요하다:
  - `get_driver`를 모킹/패치 (단위 테스트).
  - 또는 `testcontainers`/도커로 일회용 Neo4j 인스턴스를 띄워 통합 테스트.
- 순수 함수(예: `load_theographic.py`의 `filter_published`, `TimelineView`의 연도 파싱 같은 로직)는 DB 없이 단위 테스트하기 쉽다.

### 프론트엔드 (React / Vite)

- 프레임워크: Vitest(Vite 네이티브) + `@testing-library/react` + `jsdom`. `package.json`에 `"test": "vitest"` 스크립트 추가.
- 테스트 대상으로 자연스러운 순수 함수: `placesToGeoJSON` (`MapView.jsx`), `parseYear` (`TimelineView.jsx`).
- 컴포넌트 테스트는 `fetch` 모킹(예: MSW 또는 `vi.fn()`)이 필요하다 — 모든 데이터 컴포넌트가 직접 `fetch`를 호출하기 때문.
- maplibre-gl / cytoscape를 쓰는 컴포넌트(`MapView.jsx`, `GraphView.jsx`)는 캔버스/WebGL 의존성 때문에 jsdom에서 모킹이 필요하다.

### 모킹 / 픽스처

- 현재 모킹 인프라는 전무하다.
- 한글 이름 매핑 픽스처는 `data/names_ko/*.json` 실제 파일을 축약해 재사용할 수 있다.

### 커버리지 / CI

- 커버리지 측정 도구 없음. 도입 시 `pytest-cov`(백엔드), Vitest `--coverage`(프론트).
- CI에 게이트가 없으므로, 테스트를 의미 있게 만들려면 `.github/workflows/`에 테스트 잡을 추가해 배포 전 단계로 걸어야 한다.
