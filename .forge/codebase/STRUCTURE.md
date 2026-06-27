---
last_mapped_commit: 79f9d9df07c0d79f8fa07940e3f76c8d5424524b
mapped: 2026-06-28
---
# Codebase Structure

**Analysis Date:** 2026-06-28

## Directory Layout

```
BibleMap/
├── frontend/               # React 19 + Vite SPA
│   ├── src/                # 컴포넌트·훅·지도 모듈
│   ├── public/             # 정적 에셋(favicon 등)
│   ├── dist/               # 빌드 산출물 (nginx가 마운트, git ignore)
│   ├── index.html          # SPA 엔트리 HTML
│   ├── vite.config.js      # Vite + manualChunks(maplibre/vendor 분리)
│   ├── eslint.config.js    # flat config (react-hooks·react-refresh)
│   ├── .env.production      # VITE_API_URL=/api (빌드타임 주입)
│   └── package.json
├── backend/                # FastAPI API
│   ├── app/
│   │   ├── main.py         # FastAPI 앱·라우터 등록·CORS·lifespan
│   │   ├── db.py           # Neo4j 드라이버 싱글턴
│   │   ├── overlays.py     # data/*.json 로더(lru_cache)
│   │   └── routes/         # 엔드포인트별 APIRouter
│   ├── scripts/            # 데이터 적재·생성·주입 스크립트(배포·오프라인)
│   ├── Dockerfile          # python:3.12-slim + uvicorn
│   └── requirements.txt    # fastapi·neo4j·uvicorn
├── data/                   # 정적 JSON 오버레이 (컨테이너에 /app/data 마운트)
├── nginx/nginx.conf        # 정적 서빙 + /api 리버스 프록시
├── docker-compose.yml      # neo4j + api + nginx 스택
├── deploy.sh               # 빌드→이미지→재시작→한글주입 배포
├── .github/workflows/      # deploy.yml (self-hosted 러너)
├── .forge/                 # GSD 워크플로 산출물(코드 아님)
├── BIBLEMAP_PLAN.md        # 초기 기획 문서
└── CLAUDE.md               # 행동 가이드라인
```

## Directory Purposes

**`frontend/src/`:**
- Purpose: 모든 프론트엔드 소스(컴포넌트·훅·지도 헬퍼).
- Contains: `.jsx` 컴포넌트, `.js` 유틸/훅, `index.css`
- Key files: `App.jsx`(단계 라우팅), `MapView.jsx`(+ `mapGeo.js`·`mapLayers.js`·`mapRingController.js`), `api.js`(fetch), `theme.js`(팔레트)

**`backend/app/routes/`:**
- Purpose: HTTP 엔드포인트를 도메인별 파일로 분리.
- Contains: `nodes.py`·`events.py`·`search.py`·`books.py`·`persons.py`·`journey.py`·`places.py` (각 `router = APIRouter()`)
- Key files: `nodes.py`(`/node/*`·`/person/*/places`·`/person/*/event-ids`), `journey.py`(`/person/*/journey`)

**`backend/scripts/`:**
- Purpose: Neo4j 적재·오버레이 생성·한글 주입 등 오프라인/배포 시 실행되는 스크립트(런타임 API 아님).
- Contains: `load_*.py`(적재), `generate_*.py`(오버레이 생성), `inject_*.py`(Neo4j 프로퍼티 주입), `enrich_place_coords.py`
- Key files: `inject_ko_names.py`(배포 4단계에서 실행), `load_theographic.py`(초기 그래프 적재)

**`data/`:**
- Purpose: 그래프에 없는 정적 보강 데이터. `overlays._resolve`가 `/app/data` 또는 레포 상대경로에서 해석.
- Contains: 카테고리별 하위 디렉터리, 각각 JSON 한두 개
- Generated: 일부 `backend/scripts/generate_*.py` 산출물
- Committed: 예 (배포 시 docker volume으로 마운트)

**`.forge/`:**
- Purpose: GSD 워크플로 산출물 — 코드베이스 맵·ADR·백로그·완료/회고 기록.
- Contains: `codebase/`(이 문서들), `adr/`, `backlog/`, `done/`, `retro/`, `executed/`, `quick/`, `CONTEXT.md`, `config.json`
- Committed: 예 (코드 아님, 산출물)

## Key File Locations

**Entry Points:**
- `frontend/src/main.jsx`: React 루트 마운트
- `backend/app/main.py`: FastAPI 앱 객체(`uvicorn app.main:app`)

**Configuration:**
- `frontend/vite.config.js`: Vite 빌드 + 청크 분리
- `frontend/eslint.config.js`: ESLint flat config
- `frontend/.env.production`: `VITE_API_URL=/api`
- `docker-compose.yml`: 서비스 정의(neo4j·api·nginx)
- `nginx/nginx.conf`: 라우팅·캐시 헤더
- `.env` / `.env.example`: 루트 환경변수(존재만 — `NEO4J_PASSWORD` 등 비밀값, 절대 읽지 말 것)

**Core Logic:**
- `frontend/src/App.jsx`: 단계 라우팅·여정/패널 오케스트레이션
- `frontend/src/MapView.jsx` + `mapGeo.js` + `mapLayers.js` + `mapRingController.js`: 지도 렌더(4파일 분리)
- `backend/app/routes/`: REST 핸들러
- `backend/app/db.py`·`backend/app/overlays.py`: 데이터 접근

**Testing:**
- 자동화 테스트 디렉터리 없음. UI 검증은 Python Playwright 스크립트로 수동(`localhost:8080`).

## Naming Conventions

**Files:**
- React 컴포넌트: PascalCase `.jsx` — `MapView.jsx`, `PersonHub.jsx`, `SidePanel.jsx`
- 훅/유틸/지도 헬퍼: camelCase `.js` — `useNodeSelection.js`, `api.js`, `mapGeo.js`, `mapLayers.js`, `mapRingController.js`
- 백엔드 모듈/라우터: snake_case `.py` — `db.py`, `journey.py`, `inject_ko_names.py`
- 데이터 파일: 소문자 — 카테고리 디렉터리 + `books.json`/`events.json`/`people.json`/`places.json`/`groups.json`, 인물별은 slug `abraham.json`

**Directories:**
- 프론트는 평면 구조(`frontend/src/`에 하위 폴더 없이 모두 배치)
- 백엔드는 `app/`(런타임) vs `scripts/`(오프라인) 분리, 라우터는 `app/routes/`
- 데이터는 `data/<category>/`(예: `person_events/`, `event_verses/`, `place_coords/`)

## Where to Add New Code

**새 화면/뷰 컴포넌트:**
- 구현: `frontend/src/<PascalCase>.jsx` (평면 — 하위 폴더 만들지 말 것)
- `App.jsx`의 단계/토글 분기에 마운트 추가, fetch는 `apiGet` 사용
- 타입 색·라벨은 `theme.js` 재사용, 모바일 분기는 `constants.js`(`MOBILE_BREAKPOINT`/`SHEET_VH`)

**지도 기능 추가:**
- 순수 지오메트리/GeoJSON 빌더: `frontend/src/mapGeo.js`
- 새 source/layer 정의·이벤트 핸들러: `frontend/src/mapLayers.js` (`setupMapSources`/`registerEventHandlers`)
- 애니메이션 상태: `frontend/src/mapRingController.js`
- effect 오케스트레이션·prop 와이어링: `frontend/src/MapView.jsx`
- (여정 정차지 그룹핑 변경 시 `mapGeo.journeyStopGroups`와 `JourneyList.jsx`를 함께 수정)

**새 API 엔드포인트:**
- 기존 도메인이면 해당 `backend/app/routes/*.py`에 핸들러 추가
- 새 도메인이면 `backend/app/routes/<name>.py`에 `router = APIRouter()` 만들고 `backend/app/main.py`의 `include_router`에 등록
- Neo4j는 `from ..db import get_driver`, 정적 데이터는 `from ..overlays import _resolve`(또는 `overlays` 헬퍼). 비용 큰 조회는 `@functools.lru_cache`

**새 정적 데이터:**
- `data/<category>/<file>.json`에 추가, `backend/app/overlays.py`에 lru_cache 로더 추가(필요 시)
- 생성 스크립트는 `backend/scripts/generate_*.py`, Neo4j 주입은 `backend/scripts/inject_*.py`

**공유 상수/유틸:**
- 프론트 타입 팔레트: `frontend/src/theme.js`
- 프론트 레이아웃 상수: `frontend/src/constants.js`
- 백엔드 큐레이션 인물 상수(`_ERA`/`_NAME_KO`): `backend/app/routes/persons.py`(정본), `places.py`는 의도적 재선언

## Special Directories

**`frontend/dist/`:**
- Purpose: Vite 빌드 산출물. nginx가 `:ro`로 마운트해 서빙.
- Generated: 예 (`npm run build`)
- Committed: 아니오 (gitignore)

**`frontend/node_modules/` / `backend/__pycache__/`:**
- Purpose: 의존성·바이트코드
- Generated: 예
- Committed: 아니오

**`data/`:**
- Purpose: 런타임 오버레이 (docker volume 마운트 `./data:/app/data`)
- Generated: 일부 스크립트 산출
- Committed: 예

**`.forge/`:**
- Purpose: GSD 산출물(맵·ADR·기록)
- Generated: 워크플로
- Committed: 예 (`.forge/reports/`는 현재 미추적 상태)

---

*Structure analysis: 2026-06-28*
