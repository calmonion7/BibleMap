---
last_mapped_commit: 8af8f0563294387a7073d0b85e6f7de74b4b7b30
mapped: 2026-07-13
---

# STACK

BibleMap은 백엔드(FastAPI + Neo4j)와 프론트엔드(React 19 + Vite)로 구성된 단일 저장소이며, Docker Compose(neo4j·api·nginx)로 통합 기동한다. 저장소 루트는 `/Users/calmonion/Project/BibleMap`이다.

## 언어·런타임

- **백엔드**: Python 3.12 (`backend/Dockerfile`의 `FROM python:3.12-slim`). `README.md`는 개발 사전 준비로 Python 3.11+를 표기(런타임 이미지는 3.12).
- **프론트엔드**: JavaScript(ES 모듈), React 19. `frontend/package.json`은 `"type": "module"`.
- **인프라 스크립트**: Bash (`deploy.sh`), zsh 셸 환경.

## 백엔드 (`backend/`)

### 프레임워크·핵심 의존성 (`backend/requirements.txt`)

- `fastapi==0.136.3` — ASGI 웹 프레임워크. 앱은 `backend/app/main.py`의 `app` 객체.
- `neo4j==6.2.0` — 공식 Neo4j Python 드라이버(Bolt). 단일 드라이버 싱글턴은 `backend/app/db.py`의 `get_driver()`가 `NEO4J_URI`/`NEO4J_USER`/`NEO4J_PASSWORD` 환경변수로 생성.
- `uvicorn==0.49.0` — ASGI 서버. 컨테이너 기동 명령은 `uvicorn app.main:app --host 0.0.0.0 --port 8000`.

`generate_*` 스크립트(아래)가 `import anthropic` 하지만 `requirements.txt`에는 없다 — 저작 스크립트 전용 의존성으로, API 런타임 이미지에는 설치되지 않는다.

### 앱 구조

- `backend/app/main.py` — FastAPI 앱 생성, CORS 미들웨어(`allow_origins=["*"]`, `allow_methods=["GET"]`), `lifespan`에서 `Person·Place·Event·PeopleGroup·Book`의 `theographic_id` 인덱스를 `CREATE INDEX ... IF NOT EXISTS`로 준비. 로깅은 `_configure_logging()`으로 `logging.basicConfig(level=INFO)` + `neo4j·urllib3·asyncio` WARNING 승격, `uvicorn`/`uvicorn.access` propagate 차단.
- `backend/app/db.py` — Neo4j 드라이버 싱글턴.
- `backend/app/overlays.py` — 런타임에 `data/` 디렉터리의 저작 JSON 오버레이를 로드하는 헬퍼(`_resolve`/`_resolve_dir`/`_load`). 탐색 우선순위는 `DATA_DIR`(기본 `/app/data`) → 저장소 `data/`. 파일 없으면 빈 데이터 폴백.
- `backend/app/routes/` — 9개 라우터 모듈, 모두 `main.py`에서 `include_router`:
  - `nodes.py` (309줄) — `/node/{id}`, `/node/{id}/places`, `/node/{id}/neighbors/grouped`, `/person/{id}/event-ids`.
  - `persons.py` (324줄) — `/persons/curated`, `/keypeople-cards`, `/person/{id}/connections`, `/person/{id}/relations`.
  - `events.py` (135줄) — `/events`, `/event/{id}/verses`.
  - `books.py` (30줄) — `/books-overview`.
  - `places.py` (76줄) — `/place/{id}/curated-persons`.
  - `journey.py` (137줄) — `/person/{id}/journey`.
  - `tours.py` (158줄) — `/tours`, `/tour/{id}`.
  - `search.py` (42줄) — `/search`.
  - `family.py` (172줄) — `/person/{id}/family` (가계도 서브그래프, 최근 추가 기능).

### 데이터·스크립트 (`backend/scripts/`)

`ls backend/scripts/*.py` 기준 30개. 역할별로 대별된다:

- **적재(load_*)**: `load_theographic.py`(theographic 원본 → Neo4j 노드·간선 배치 적재), `load_books.py`, `load_authored_events.py`, `load_authored_persons.py`, `load_person_events.py`, `load_verse_events.py`, `load_authored_genealogy.py`(족보 사슬 적재, 최근 추가 기능).
- **주입(inject_*)**: `inject_ko_names.py`(한글 이름 — `deploy.sh` 4단계에서 재시도 실행), `inject_date_corrections.py`, `inject_person_traits.py`, `inject_person_context.py`, `inject_book_context.py`, `inject_place_context.py`.
- **생성(generate_*)**: `generate_book_events.py`, `generate_book_context.py`, `generate_book_context_enrich.py`, `generate_person_context.py`, `generate_person_traits.py`, `generate_verse_events.py`, `generate_verse_text.py`, `generate_bible_text.py`, `generate_event_verses.py`, `generate_person_event_verses.py`, `generate_approx_book_verses.py`. 이 중 5개(`generate_book_events.py`·`generate_book_context.py`·`generate_person_context.py`·`generate_person_traits.py`·`generate_verse_events.py`)는 Anthropic Claude API를 호출한다(INTEGRATIONS 참조).
- **검증·후처리**: `validate_event_chronology.py`, `validate_traits.py`, `validate_person_context.py`, `apply_event_dedupe.py`, `enrich_place_coords.py`.

스크립트는 대부분 `urllib.request`로 외부 JSON을 fetch하고 `neo4j.GraphDatabase`로 직접 DB에 쓴다(FastAPI를 거치지 않음).

## 프론트엔드 (`frontend/`)

### 프레임워크·의존성 (`frontend/package.json`)

런타임 의존성:

- `react ^19.2.6`, `react-dom ^19.2.6` — React 19.
- `maplibre-gl ^5.24.0` — 지도 렌더링(WebGL). `frontend/src/MapView.jsx`에서 직접 지도 스타일을 구성.
- `lucide-react ^1.17.0` — 아이콘.

개발 의존성:

- `vite ^8.0.12` + `@vitejs/plugin-react ^6.0.1` — 빌드/개발 서버.
- `eslint ^10.3.0` + `@eslint/js ^10.0.1` + `eslint-plugin-react-hooks ^7.1.1` + `eslint-plugin-react-refresh ^0.5.2` + `globals ^17.6.0`.
- `@types/react ^19.2.14`, `@types/react-dom ^19.2.3`.

### 스크립트 (`frontend/package.json`)

`dev`(vite), `build`(vite build), `lint`(eslint .), `preview`(vite preview).

### 빌드 설정 (`frontend/vite.config.js`)

`@vitejs/plugin-react` 사용. `build.rollupOptions.output.manualChunks`로 `node_modules` 중 `maplibre-gl`을 `maplibre` 청크로, 나머지를 `vendor` 청크로 분리한다.

### 엔트리·소스 구성

- `frontend/index.html` — 루트 `#root`, `/src/main.jsx` 모듈 로드, `title` BibleMap, `favicon.svg`.
- `frontend/src/main.jsx`(10줄) → `App.jsx`(542줄) 마운트.
- 주요 컴포넌트·모듈(줄 수): `SidePanel.jsx`(823), `App.jsx`(542), `mapLayers.js`(451), `PersonHub.jsx`(341), `TimelineView.jsx`(307), `BibleOverviewView.jsx`(302), `JourneyList.jsx`(281), `useStageNavigation.js`(274), `PersonIntro.jsx`(251), `MapView.jsx`(240), `mapGeo.js`(215), `FamilyTree.jsx`(207, 가계도 SVG 레이아웃 — 최근 추가), `RelationsView.jsx`(195), `mapRingController.js`(163), `TourList.jsx`(58), `useNodeSelection.js`(52), `theme.js`(51), `urlState.js`(42), `VerseLangTabs.jsx`(28), `dates.js`(12), `api.js`(11), `Spinner.jsx`(15), `constants.js`(3). `frontend/src/` 합계 약 4874줄.
- API 접근은 `frontend/src/api.js`의 `apiGet()` 단일 헬퍼로 통일. 베이스 URL은 `import.meta.env.VITE_API_URL || 'http://localhost:8000'`.
- `frontend/src/constants.js` — `MOBILE_BREAKPOINT=768`, 시트 높이 상수 등.

### 프론트엔드 환경변수

- `frontend/.env.production` — `VITE_API_URL=/api`(빌드타임 주입, nginx 프록시 경로). 개발 시엔 폴백 `http://localhost:8000` 사용.

## 빌드·구성·배포 파일

- `docker-compose.yml` — `neo4j`(image `neo4j:5`)·`api`(build `./backend`)·`nginx`(image `nginx:alpine`) 3서비스. INTEGRATIONS에 상세.
- `backend/Dockerfile` — `python:3.12-slim`, `requirements.txt` 설치 후 `app/` 복사, uvicorn 기동.
- `nginx/nginx.conf` — 정적 자산 서빙 + `/api/` 리버스 프록시.
- `deploy.sh` — 프론트 빌드 → API 이미지 빌드 → 컨테이너 재기동 → 한글 이름 주입의 4단계 배포 스크립트(macOS 로컬 호스트 대상, lock 파일·로그 포함).
- `.github/workflows/deploy.yml` — `main` push 시 self-hosted 러너에서 `deploy.sh` 실행.
- `.env` / `.env.example` — 루트 레벨, `NEO4J_PASSWORD`만 정의(compose가 `NEO4J_AUTH`를 `neo4j/<password>`로 파생).

## 실행 방법 요약 (`README.md`)

개발: `docker compose up -d`(Neo4j) → `load_theographic.py`·`inject_ko_names.py`·`inject_date_corrections.py`로 데이터 적재 → `python3 -m uvicorn backend.app.main:app --reload`(:8000) → `cd frontend && npm run dev`(:5173). 로컬 통합 검증은 `frontend/dist`를 nginx가 마운트하므로 `npm run build` 후 `docker compose up -d --build api`로 확인(:8080).
