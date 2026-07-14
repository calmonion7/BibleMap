---
last_mapped_commit: e53ec23d634a48d16bd1abf3e131c340cfbaac1f
mapped: 2026-07-14
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
- `neo4j==6.2.0` — 공식 Neo4j Python 드라이버(Bolt). 드라이버 싱글턴은 `backend/app/db.py`의 `get_driver()`가 `NEO4J_URI`/`NEO4J_USER`/`NEO4J_PASSWORD` 환경변수로 생성(비번 미설정 시 `RuntimeError`).
- `uvicorn==0.49.0` — ASGI 서버. 컨테이너 기동 명령은 `uvicorn app.main:app --host 0.0.0.0 --port 8000`.

`requirements.txt` 밖의 스크립트 전용 의존성(런타임 이미지에 미설치):

- `anthropic` — `generate_*` 스크립트 5개가 import (INTEGRATIONS 참조).
- `kiwipiepy` — `backend/scripts/build_word_distribution.py`가 한국어 명사(NNG·NNP) 추출에 사용. docstring이 임시 venv(`/tmp/kiwi-venv`) 설치 실행을 안내.

### 앱 구조 (`backend/app/`)

- `backend/app/main.py`(61줄) — FastAPI 앱 생성, CORS 미들웨어(`allow_origins=["*"]`, `allow_methods=["GET"]`, credentials 미허용), `lifespan`에서 `Person·Place·Event·PeopleGroup·Book`의 `theographic_id` 인덱스를 `CREATE INDEX ... IF NOT EXISTS`로 준비(실패해도 경고 후 계속). 로깅은 `_configure_logging()`으로 `logging.basicConfig(level=INFO)` + `neo4j·urllib3·asyncio` WARNING 승격, `uvicorn`/`uvicorn.access` propagate 차단.
- `backend/app/db.py`(15줄) — Neo4j 드라이버 싱글턴.
- `backend/app/overlays.py`(73줄) — `data/` 저작 JSON 오버레이 로더. 탐색 우선순위는 `DATA_DIR`(기본 `/app/data`) → 저장소 `data/`, 파일 없으면 빈 데이터 폴백. `book_events_raw()`·`event_verses()`·`bible_verses()`·`word_distribution()`·`books_ko()`가 각각 `functools.lru_cache(maxsize=1)` — 데이터 파일 변경 시 API 컨테이너 재시작 필요.
- `backend/app/routes/` — 10개 라우터 모듈, 모두 `main.py`에서 `include_router`:
  - `nodes.py`(309줄) — `/node/{id}`, `/node/{id}/places`, `/node/{id}/neighbors/grouped`, `/person/{id}/event-ids`.
  - `persons.py`(324줄) — `/persons/curated`, `/keypeople-cards`, `/person/{id}/connections`, `/person/{id}/relations`.
  - `events.py`(135줄) — `/events`, `/event/{id}/verses`.
  - `books.py`(30줄) — `/books-overview`.
  - `places.py`(76줄) — `/place/{id}/curated-persons`.
  - `journey.py`(137줄) — `/person/{id}/journey`.
  - `tours.py`(158줄) — `/tours`, `/tour/{id}`.
  - `search.py`(43줄) — `/search`.
  - `family.py`(172줄) — `/person/{id}/family` (가계도 서브그래프).
  - `words.py`(44줄) — `/words/{book_id}`, `/words/{book_id}/verses` (단어 분포 — Neo4j 미접근, 오버레이 전용. 구절 매칭은 substring, `VERSE_LIMIT=200`).

### 데이터·스크립트 (`backend/scripts/`)

Python 스크립트 30개. 역할별 대별:

- **적재(load_*)**: `load_theographic.py`(theographic 원본 → Neo4j 배치 적재), `load_books.py`, `load_authored_events.py`, `load_authored_persons.py`, `load_authored_genealogy.py`, `load_person_events.py`, `load_verse_events.py`.
- **주입(inject_*)**: `inject_ko_names.py`(한글 이름 — `deploy.sh` 4단계에서 재시도 실행), `inject_date_corrections.py`, `inject_person_traits.py`, `inject_person_context.py`, `inject_book_context.py`, `inject_place_context.py`.
- **생성(generate_*)**: `generate_book_events.py`, `generate_book_context.py`, `generate_book_context_enrich.py`, `generate_person_context.py`, `generate_person_traits.py`, `generate_verse_events.py`, `generate_verse_text.py`, `generate_bible_text.py`, `generate_event_verses.py`, `generate_person_event_verses.py`, `generate_approx_book_verses.py`. 이 중 5개(`generate_book_events.py`·`generate_book_context.py`·`generate_person_context.py`·`generate_person_traits.py`·`generate_verse_events.py`)는 Anthropic Claude API를 호출한다(INTEGRATIONS 참조).
- **집계(build_*)**: `build_word_distribution.py` — `data/bible/verses.json`의 textKo를 kiwipiepy로 형태소 분석해 책별(상위 60)·전체(상위 120) 명사 빈도를 집계하고 `data/word_sentiment.json`의 극성을 병합해 `data/word_distribution.json`을 산출. Neo4j 미접근.
- **검증·후처리**: `validate_event_chronology.py`, `validate_traits.py`, `validate_person_context.py`, `apply_event_dedupe.py`, `enrich_place_coords.py`(`data/place_coords/places.json` → Place 노드 멱등 적재).

스크립트는 대부분 `urllib.request`로 외부 JSON을 fetch하고 `neo4j.GraphDatabase`로 직접 DB에 쓴다(FastAPI를 거치지 않음). 호스트 직접 실행 시 Neo4j 기본 접속은 `bolt://localhost:7687`.

## 프론트엔드 (`frontend/`)

### 프레임워크·의존성 (`frontend/package.json`)

런타임 의존성:

- `react ^19.2.6`, `react-dom ^19.2.6` — React 19.
- `maplibre-gl ^5.24.0` — 지도 렌더링(WebGL). `frontend/src/MapView.jsx`에서 인라인 스타일 구성.
- `lucide-react ^1.17.0` — 아이콘.

개발 의존성:

- `vite ^8.0.12` + `@vitejs/plugin-react ^6.0.1` — 빌드/개발 서버.
- `eslint ^10.3.0` + `@eslint/js ^10.0.1` + `eslint-plugin-react-hooks ^7.1.1` + `eslint-plugin-react-refresh ^0.5.2` + `globals ^17.6.0` (`frontend/eslint.config.js`).
- `@types/react ^19.2.14`, `@types/react-dom ^19.2.3`.

### 스크립트 (`frontend/package.json`)

`dev`(vite), `build`(vite build), `lint`(eslint .), `preview`(vite preview).

### 빌드 설정 (`frontend/vite.config.js`)

`@vitejs/plugin-react` 사용. `build.rollupOptions.output.manualChunks`로 `node_modules` 중 `maplibre-gl`을 `maplibre` 청크로, 나머지를 `vendor` 청크로 분리.

### 엔트리·소스 구성

- `frontend/index.html` — 루트 `#root`, `/src/main.jsx` 모듈 로드, `frontend/public/favicon.svg`.
- `frontend/src/main.jsx`(15줄) → `App.jsx`(666줄) 마운트.
- 주요 컴포넌트·모듈(줄 수): `SidePanel.jsx`(823), `App.jsx`(666), `mapLayers.js`(451), `PersonHub.jsx`(374), `TimelineView.jsx`(306), `BibleOverviewView.jsx`(301), `useStageNavigation.js`(299), `JourneyList.jsx`(281), `PersonIntro.jsx`(251), `MapView.jsx`(240), `WordDistributionView.jsx`(217, 감정 3영역 워드클라우드 + 구절 시트), `mapGeo.js`(215), `FamilyTree.jsx`(207, 라이브러리 없는 SVG 가계도), `RelationsView.jsx`(194), `mapRingController.js`(163), `index.css`(158), `TourList.jsx`(57), `useNodeSelection.js`(52), `urlState.js`(45), `theme.js`(43, 듀얼 테마 — 다크 기본), `VerseLangTabs.jsx`(28), `Spinner.jsx`(16), `dates.js`(12), `api.js`(11), `constants.js`(3). `frontend/src/` 합계 약 5428줄.
- API 접근은 `frontend/src/api.js`의 `apiGet()` 단일 헬퍼로 통일. 베이스 URL은 `import.meta.env.VITE_API_URL || 'http://localhost:8000'`.

### 프론트엔드 환경변수

- `frontend/.env.production` — `VITE_API_URL=/api`(빌드타임 주입, nginx 프록시 경로). 개발 시엔 폴백 `http://localhost:8000` 사용.

## 빌드·구성·배포 파일

- `docker-compose.yml` — `neo4j`(image `neo4j:5`)·`api`(build `./backend`)·`nginx`(image `nginx:alpine`) 3서비스. INTEGRATIONS에 상세.
- `backend/Dockerfile` — `python:3.12-slim`, `requirements.txt` 설치 후 `app/`만 복사(스크립트·데이터 미포함), uvicorn 기동.
- `nginx/nginx.conf` — 정적 자산 서빙 + `/api/` 리버스 프록시.
- `deploy.sh` — 프론트 빌드 → API 이미지 빌드 → 컨테이너 재기동 → 한글 이름 주입의 4단계 배포 스크립트(macOS 로컬 호스트 대상, lock 파일·로그 포함). `load_*`·`inject_*`(ko_names 제외)는 실행하지 않는다.
- `.github/workflows/deploy.yml` — `main` push 시 self-hosted 러너에서 `deploy.sh` 실행.
- `.env` / `.env.example` — 루트 레벨, 키는 `NEO4J_PASSWORD`뿐(compose가 `NEO4J_AUTH`를 `neo4j/<password>`로 파생).

## 실행 방법 요약 (`README.md`)

개발: `docker compose up -d`(Neo4j) → `load_theographic.py`·`inject_ko_names.py`·`inject_date_corrections.py`로 데이터 적재 → `python3 -m uvicorn backend.app.main:app --reload`(:8000) → `cd frontend && npm run dev`(:5173). 로컬 통합 검증은 `frontend/dist`를 nginx가 마운트하므로 `npm run build` 후 `docker compose up -d --build api`로 확인(:8080).
