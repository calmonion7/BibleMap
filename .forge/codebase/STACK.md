---
last_mapped_commit: 3837b4f9339ed2efb82a6b72cc1124a3340e2b9c
mapped: 2026-06-27
---

# STACK

BibleMap은 단일 저장소(monorepo)로, React 프론트엔드 + FastAPI 백엔드 + Neo4j 그래프 DB를 Docker Compose로 묶고 nginx가 정적 자산과 API 프록시를 담당하는 구성이다.

## Languages & Runtimes

- **프론트엔드**: JavaScript (ESM, `"type": "module"`), JSX. 빌드 산출물은 `frontend/dist/`로 정적 파일.
- **백엔드**: Python 3.12 (`backend/Dockerfile`의 `FROM python:3.12-slim`). 로컬 개발 캐시에는 `cpython-314` 바이트코드도 보인다.
- **데이터/스크립트**: Python 3 (`backend/scripts/*.py`).
- 저장소에 별도 `pyproject.toml`/`setup.py`는 없다. 백엔드 런타임 의존성은 `backend/requirements.txt` 한 파일로만 핀.

## Frontend (Vite + React)

- 패키지 매니페스트: `frontend/package.json`. `lockfileVersion: 3`의 `frontend/package-lock.json`로 잠금.
- 런타임 의존성:
  - `react` ^19.2.6, `react-dom` ^19.2.6 (React 19)
  - `maplibre-gl` ^5.24.0 (지도 렌더링)
  - `lucide-react` ^1.17.0 (아이콘)
- 개발 의존성: `vite` ^8.0.12, `@vitejs/plugin-react` ^6.0.1, `eslint` ^10.3.0, `@eslint/js`, `eslint-plugin-react-hooks` ^7.1.1, `eslint-plugin-react-refresh`, `globals`, `@types/react`·`@types/react-dom`.
- npm 스크립트(`frontend/package.json`): `dev`(`vite`), `build`(`vite build`), `lint`(`eslint .`), `preview`(`vite preview`).
- Vite 설정(`frontend/vite.config.js`): `@vitejs/plugin-react` 플러그인. `build.rollupOptions.output.manualChunks`로 `node_modules` 중 `maplibre-gl`을 `maplibre` 청크, 나머지를 `vendor` 청크로 코드 스플리팅.
- ESLint 설정(`frontend/eslint.config.js`): flat config. `js.configs.recommended` + react-hooks + react-refresh(vite). `dist`는 글로벌 무시, 대상은 `**/*.{js,jsx}`, 브라우저 globals.
- 엔트리: `frontend/index.html`이 `/src/main.jsx`를 모듈 스크립트로 로드. `<title>BibleMap</title>`, 파비콘 `/favicon.svg`.
- 빌드 산출물은 nginx 컨테이너에 `frontend/dist`를 읽기 전용 마운트해서 서빙(`docker-compose.yml`) — HMR 아님. 로컬 검증 전 `npm run build` 필요.
- 소스 구성(`frontend/src/`): 셸 `main.jsx`·`App.jsx`. 지도 `MapView.jsx`(컨테이너)·`mapGeo.js`·`mapLayers.js`·`mapRingController.js`. 인물 우선 2단계 뷰 `PersonHub.jsx`·`JourneyList.jsx`. 보조 뷰/패널 `BibleOverviewView.jsx`·`TimelineView.jsx`·`SidePanel.jsx`·`VerseLangTabs.jsx`·`Spinner.jsx`. 공유 유틸 `api.js`(fetch 클라이언트)·`constants.js`(`MOBILE_BREAKPOINT=768`, `SHEET_VH=55`)·`theme.js`·`useNodeSelection.js`(훅). 스타일 `index.css`.

## Backend (FastAPI + uvicorn)

- 런타임 의존성 핀(`backend/requirements.txt`): `fastapi==0.136.3`, `neo4j==6.2.0`, `uvicorn==0.49.0`. (그 외 표준 라이브러리만 사용; `anthropic`은 런타임 이미지에 포함되지 않는 빌드타임 전용 — INTEGRATIONS.md 참조.)
- 앱 진입점: `backend/app/main.py`의 `app = FastAPI(lifespan=...)`.
  - `lifespan`에서 부팅 시 Neo4j에 `Person/Place/Event/PeopleGroup/Book` 라벨별 `theographic_id` 인덱스를 `CREATE INDEX ... IF NOT EXISTS`로 보장하며, 실패해도 로깅 후 계속 진행.
  - CORS: `CORSMiddleware`로 `allow_origins=["*"]`, `allow_methods=["GET"]`, `allow_credentials=False`.
  - 라우터 포함: `nodes`, `events`, `search`, `books`, `persons`, `journey`, `places` (`backend/app/routes/`).
- 라우트 표면(모두 GET):
  - `backend/app/routes/nodes.py`: `/person/{node_id}/event-ids`, `/node/{node_id}/places`, `/node/{node_id}/neighbors/grouped`, `/node/{node_id}`.
  - `backend/app/routes/events.py`: `/events`, `/event/{event_id}/verses`.
  - `backend/app/routes/search.py`: `/search?q=`.
  - `backend/app/routes/books.py`: `/books-overview`.
  - `backend/app/routes/persons.py`: `/persons/curated`. Neo4j 미조회 — `data/person_events/<slug>.json` 파일만으로 결정적 구성(slug 매핑 상수 `_ERA`·`_NAME_KO` 내장, `functools.lru_cache`).
  - `backend/app/routes/journey.py`: `/person/{person_id}/journey`. 파일(`person_events`)로 사건 시퀀스 + Neo4j에서 `Place` 좌표 배치 조회.
  - `backend/app/routes/places.py`: `/place/{place_id}/curated-persons`(쿼리 `exclude`). 파일만으로 결정적 필터(`persons.py`와 동일 상수 재선언).
- DB 드라이버: `backend/app/db.py`의 `get_driver()`가 `neo4j.GraphDatabase.driver`를 지연 싱글톤으로 생성. URI/USER/PASSWORD는 환경변수(`NEO4J_URI` 기본 `bolt://localhost:7687`, `NEO4J_USER` 기본 `neo4j`, `NEO4J_PASSWORD` 필수).
- 오버레이 로더: `backend/app/overlays.py`가 `DATA_DIR`(기본 `/app/data`) 또는 저장소 `data/` 아래의 JSON을 `functools.lru_cache`로 1회 로드. `book_events/books.json`, `event_verses/events.json`.
- 컨테이너 실행 커맨드(`backend/Dockerfile`): `uvicorn app.main:app --host 0.0.0.0 --port 8000`.

## Containerization (Docker Compose)

`docker-compose.yml`의 세 서비스:

- **neo4j**: `neo4j:5` 이미지. 포트 `127.0.0.1:7474`(브라우저), `127.0.0.1:7687`(bolt)을 루프백에만 바인딩. 데이터는 named volume `neo4j_data:/data`. 인증은 `NEO4J_AUTH=neo4j/${NEO4J_PASSWORD}`(미설정 시 compose가 에러).
- **api**: `./backend` 빌드(`backend/Dockerfile`). 환경변수로 `NEO4J_URI=bolt://neo4j:7687`, `NEO4J_USER=neo4j`, `NEO4J_PASSWORD`. `./data:/app/data` 마운트. `depends_on: neo4j`. 호스트에 포트 미노출(nginx 통해서만 접근).
- **nginx**: `nginx:alpine`. 호스트 `8080 -> 80`. `./frontend/dist`(정적, ro)와 `./nginx/nginx.conf`(ro) 마운트. `depends_on: api`.
- 모든 서비스 `restart: unless-stopped`.

## nginx (정적 서빙 + API 프록시)

`nginx/nginx.conf`:

- `location /api/` → `proxy_pass http://api:8000/`. `X-Real-IP`, `X-Forwarded-For`, `X-Forwarded-Proto` 헤더 설정.
- `location = /index.html` → `Cache-Control: no-cache, no-store, must-revalidate`.
- 정적 자산(`js|css|png|jpg|jpeg|gif|ico|svg|woff2?`) → `Cache-Control: public, max-age=31536000, immutable`.
- `location /` → SPA 폴백 `try_files $uri /index.html`.

## Build & Deploy

- 배포 스크립트 `deploy.sh`: `.env`에서 `NEO4J_PASSWORD` 로드 → `frontend` `npm install` + `npm run build` → `docker compose -p biblemap build api` → `up -d api nginx` → Neo4j 준비를 최대 15회 재시도하며 `backend/scripts/inject_ko_names.py`로 한글 이름 주입. macOS 키체인 우회를 위해 임시 `DOCKER_CONFIG` 생성.
- CI/CD: `.github/workflows/deploy.yml` — `main` push 시 `self-hosted` 러너에서 `git reset --hard origin/main` 후 `bash deploy.sh` 실행.

## Config & Environment

- 루트 `.env`(gitignore됨): `NEO4J_PASSWORD`만 보유. 예시 `.env.example`에 키 이름·설명만 존재(값은 placeholder).
- 프론트 `frontend/.env.production`: `VITE_API_URL=/api`(빌드타임 주입). 프론트 API 클라이언트 `frontend/src/api.js`의 `API_BASE`는 `import.meta.env.VITE_API_URL`이 없으면 `http://localhost:8000` 폴백.
- `.gitignore`: `.venv/`, `frontend/node_modules/`, `frontend/dist/`, `.env` 등 제외.
- 시크릿 값은 어디에도 커밋되지 않음(환경변수/`.env`로만 주입).
