---
last_mapped_commit: e160d65cf9c7d0b54c8d9fc2d031639a712bfb86
mapped: 2026-06-16
---

# STACK

BibleMap의 언어·런타임·프레임워크·빌드·도구·설정·컨테이너 구성 정리. 모놀리식 레포 안에 백엔드(FastAPI)·프론트엔드(React/Vite)·데이터 ETL 스크립트가 함께 있고, Docker Compose로 묶어 배포한다.

## 1. 언어 / 런타임

- **Python 3.12** — 백엔드 API 컨테이너 런타임. `backend/Dockerfile`에서 `FROM python:3.12-slim`.
- **Python 3.14** — 호스트에서 ETL/주입 스크립트 직접 실행 시 사용(`backend/app/__pycache__/*.cpython-314.pyc`, 로컬 `python3 --version` = 3.14.5). 즉 컨테이너(3.12)와 호스트(3.14)가 다른 Python을 쓴다.
- **Node.js v24** (로컬 기준) — 프론트엔드 빌드/개발 런타임. `frontend/package.json`은 `"type": "module"`(ESM).
- **JavaScript / JSX** — 프론트엔드. TypeScript는 사용하지 않으나 `@types/react`, `@types/react-dom`가 devDependency로 존재(에디터 타입 힌트용).

## 2. 백엔드 — FastAPI

- 진입점 `backend/app/main.py` — `FastAPI(lifespan=...)` 앱. CORS 미들웨어(`allow_origins=["*"]`, `allow_methods=["GET"]`). 라우터 4개 등록: `nodes`, `events`, `search`, `books`.
- 라우터: `backend/app/routes/nodes.py`, `backend/app/routes/events.py`, `backend/app/routes/search.py`, `backend/app/routes/books.py`.
- DB 드라이버 싱글턴 `backend/app/db.py` — `neo4j.GraphDatabase.driver(...)` 모듈 레벨 캐시.
- `lifespan` 훅이 기동 시 `Person`/`Place`/`Event`/`PeopleGroup`/`Book` 라벨에 `theographic_id` 인덱스를 `CREATE INDEX ... IF NOT EXISTS`로 생성(실패해도 인덱스 없이 진행).
- ASGI 서버: **uvicorn** — `CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]` (`backend/Dockerfile`).

### 백엔드 의존성 (`backend/requirements.txt`)

| 패키지 | 버전(고정) | 용도 |
| --- | --- | --- |
| fastapi | 0.136.3 | 웹 프레임워크 |
| neo4j | 6.2.0 | Neo4j Bolt 드라이버 |
| uvicorn | 0.49.0 | ASGI 서버 |

- ETL 스크립트가 쓰는 `anthropic`(Claude SDK)는 `requirements.txt`에 없다 — `backend/scripts/generate_book_context.py`, `backend/scripts/generate_person_traits.py`가 `import anthropic`하지만 API 컨테이너에 포함되지 않으므로 호스트에서 별도 설치 후 수동 실행하는 일회성 도구다.
- 의존성 매니저: pip(`requirements.txt`). 락파일 없음.

## 3. 프론트엔드 — React + Vite

- 진입 HTML `frontend/index.html` → `frontend/src/main.jsx`.
- 주요 소스: `frontend/src/App.jsx`, `frontend/src/MapView.jsx`, `frontend/src/SidePanel.jsx`, `frontend/src/TimelineView.jsx`, `frontend/src/api.js`(공유 fetch 클라이언트), `frontend/src/getbible.js`(외부 성경 API 헬퍼), `frontend/src/theme.js`(타입 색·라벨 팔레트), `frontend/src/convexHull.js`, `frontend/src/index.css`.

### 프론트엔드 의존성 (`frontend/package.json`)

런타임 dependencies:

| 패키지 | 버전 범위 | 용도 |
| --- | --- | --- |
| react | ^19.2.6 | UI |
| react-dom | ^19.2.6 | DOM 렌더 |
| maplibre-gl | ^5.24.0 | 지도 렌더(WebGL) — `frontend/src/MapView.jsx` |
| lucide-react | ^1.17.0 | 아이콘 |

devDependencies:

| 패키지 | 버전 범위 | 용도 |
| --- | --- | --- |
| vite | ^8.0.12 | 번들러/개발 서버 |
| @vitejs/plugin-react | ^6.0.1 | React + Fast Refresh |
| eslint | ^10.3.0 | 린터 |
| @eslint/js | ^10.0.1 | ESLint 권장 규칙 |
| eslint-plugin-react-hooks | ^7.1.1 | hooks 규칙 |
| eslint-plugin-react-refresh | ^0.5.2 | HMR 규칙 |
| globals | ^17.6.0 | 전역 정의 |
| @types/react | ^19.2.14 | 타입 힌트 |
| @types/react-dom | ^19.2.3 | 타입 힌트 |

- 의존성 매니저: npm. 락파일 `frontend/package-lock.json` 존재.

### 빌드 / 번들링

- `frontend/vite.config.js` — `@vitejs/plugin-react` 플러그인 + `build.rollupOptions.output.manualChunks`로 코드 스플리팅: `maplibre-gl`은 `maplibre` 청크, 그 외 `node_modules`는 `vendor` 청크로 분리.
- npm 스크립트(`frontend/package.json`): `dev`(vite), `build`(vite build), `lint`(eslint .), `preview`(vite preview).
- 빌드 산출물은 `frontend/dist/`(gitignore됨) → nginx가 정적 서빙.

### 린트

- `frontend/eslint.config.js` — flat config. `js.configs.recommended` + react-hooks(flat recommended) + react-refresh(vite) extends. `dist` 무시. `globals.browser`, JSX 파서 옵션.

## 4. 데이터베이스 — Neo4j

- 그래프 DB **Neo4j 5**(컨테이너 이미지 `neo4j:5`, `docker-compose.yml`). 드라이버는 Python `neo4j` 6.2.0.
- Bolt 프로토콜(`bolt://neo4j:7687`), HTTP 브라우저(7474). 노출은 `127.0.0.1`에 한정.
- 인증: `NEO4J_AUTH=neo4j/${NEO4J_PASSWORD}`(compose가 파생). 앱은 `NEO4J_URI`/`NEO4J_USER`/`NEO4J_PASSWORD` 환경변수 사용(`backend/app/db.py`).
- 데이터 볼륨: 명명 볼륨 `neo4j_data:/data`.
- 노드 라벨: `Person`, `Place`, `Event`, `PeopleGroup`, `Book`. 모두 `theographic_id`를 키로 사용.

## 5. 데이터 ETL / 적재 스크립트 (`backend/scripts/`)

호스트에서 직접 실행하는 일회성/배치 스크립트. 외부 데이터 소스와 Claude API는 INTEGRATIONS.md 참조.

- `load_theographic.py` — Theographic GitHub raw JSON에서 Person/Place/Event/PeopleGroup 노드 + 관계(PARENT_OF/CHILD_OF/SIBLING_OF/PARTNER_OF/MEMBER_OF/HAS_PARTICIPANT/OCCURS_AT/PART_OF) 적재. 배치 단위(노드 500, 관계 1000) UNWIND+MERGE.
- `load_books.py` — Book 노드 적재 + `CONTAINS_BOOK` 관계(verses→book 역매핑) 생성, event.startDate 집계로 책별 startYear/endYear 추정.
- `inject_ko_names.py` — `data/names_ko/*.json`을 읽어 노드에 `nameKo`/`aliasesKo` SET. 배포 마지막 단계에서 실행(`deploy.sh`).
- `inject_book_context.py` — `data/book_context/books.json`을 Book 노드 background/themes/keyVerse로 SET.
- `inject_person_traits.py` — `data/character_traits/people.json`을 Person 노드 `traits`(JSON 문자열) SET.
- `generate_book_context.py` — Claude API로 책별 배경·주제·대표구절 생성 → `data/book_context/books.json`.
- `generate_person_traits.py` — Claude API로 인물별 성품 생성 → `data/character_traits/people.json`.
- `generate_event_verses.py` — Theographic events.json + verses.json을 받아 사건별 근거 구절을 권별로 묶어 `data/event_verses/events.json` 생성(INTEGRATIONS.md 상세).

표준 라이브러리 `urllib.request`로 GitHub raw를 직접 fetch한다(별도 HTTP 클라이언트 의존성 없음).

## 6. 정적 데이터 (`data/`)

API 컨테이너에 `./data:/app/data` 볼륨으로 마운트(`docker-compose.yml`). 백엔드는 `DATA_DIR`(기본 `/app/data`) → 레포 상대경로 순으로 폴백 탐색(`backend/app/routes/books.py`, `backend/app/routes/events.py`).

- `data/names_ko/{people,places,events,groups,books}.json` — 한국어 이름/별칭 매핑(`{theographic_id: {ko, alias[]}}`).
- `data/book_years_approx/books.json` — startYear 없는 책의 추정 배치연도(`{tid: {nameKo, placementYear, basis, approx}}`).
- `data/book_context/books.json` — Claude 생성 책 배경/주제/대표구절.
- `data/character_traits/people.json` — Claude 생성 인물 성품.
- `data/event_verses/events.json` — 생성된 사건별 근거 구절(~93,767줄, ~2MB). 사건 id → `{books:[{bookId, bookOrder, rangeLabel, verses[]}]}`.

## 7. 설정 / 환경변수

- 루트 `.env`(gitignore) / `.env.example` — `NEO4J_PASSWORD`만 정의. compose가 `NEO4J_AUTH`/앱 `NEO4J_PASSWORD`로 주입.
- `frontend/.env.production` — `VITE_API_URL=/api`(빌드타임 주입, nginx 프록시 경유). 개발 기본값은 `http://localhost:8000`(`frontend/src/api.js`).
- 백엔드 런타임 환경변수: `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`(필수, 없으면 RuntimeError), 데이터 경로 `DATA_DIR`.

## 8. Docker / Compose

`docker-compose.yml` 3개 서비스:

- **neo4j** — `neo4j:5`, 포트 `127.0.0.1:7474`/`127.0.0.1:7687`, 볼륨 `neo4j_data`, `restart: unless-stopped`.
- **api** — `build: ./backend`(상기 Dockerfile). env: `NEO4J_URI=bolt://neo4j:7687`, `NEO4J_USER`, `NEO4J_PASSWORD`. 볼륨 `./data:/app/data`. `depends_on: neo4j`.
- **nginx** — `nginx:alpine`, 포트 `8080:80`. `./frontend/dist`(읽기전용)와 `./nginx/nginx.conf` 마운트. `depends_on: api`.

`backend/Dockerfile`: `python:3.12-slim`, `pip install -r requirements.txt`, `app/`만 복사(스크립트·데이터 미포함), uvicorn 기동.

### nginx 라우팅 (`nginx/nginx.conf`)

- `/api/` → `http://api:8000/`(트레일링 슬래시로 prefix 제거 프록시). X-Forwarded-* 헤더 전달.
- `/index.html` → no-cache. 정적 에셋(`.js|.css|.png|...`) → `max-age=31536000, immutable`. 그 외 → SPA fallback(`try_files $uri /index.html`).

## 9. 배포 / CI

- `deploy.sh` — 자체 호스트 배포 스크립트: lock 파일 → `.env` 로드 → 프론트 `npm install && npm run build` → `docker compose -p biblemap build api` → `up -d api nginx` → `inject_ko_names.py`(Neo4j 준비까지 최대 15회 재시도). macOS 키체인 우회용 임시 `DOCKER_CONFIG` 구성.
- `.github/workflows/deploy.yml` — `push: branches:[main]` 트리거, `runs-on: self-hosted`. 워크플로우가 `git fetch` + `git reset --hard origin/main` 후 `bash deploy.sh` 실행.
- compose 프로젝트명 `biblemap`(`-p biblemap`)은 deploy.sh에서만 사용(compose 파일엔 명시 없음).
