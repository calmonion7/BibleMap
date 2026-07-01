---
last_mapped_commit: 0189ad9fb964e5eb4fcc91776b3202f7014058dd
mapped: 2026-07-02
---

# STACK

BibleMap은 단일 머신에서 Docker Compose로 구동하는 3-tier 스택이다. Neo4j 그래프 DB, FastAPI 백엔드(`api`), 그리고 React 정적 빌드를 서빙하는 nginx 리버스 프록시로 구성된다. 정의 파일은 `docker-compose.yml`.

## Backend (Python / FastAPI)

- **런타임**: Python 3.12 (`backend/Dockerfile`의 `FROM python:3.12-slim`).
- **의존성** (`backend/requirements.txt`, 버전 핀 고정):
  - `fastapi==0.136.3` — 웹 프레임워크.
  - `uvicorn==0.49.0` — ASGI 서버. 컨테이너 진입점은 `uvicorn app.main:app --host 0.0.0.0 --port 8000`.
  - `neo4j==6.2.0` — 공식 Neo4j Python 드라이버.
- **앱 진입점**: `backend/app/main.py`. `FastAPI(lifespan=...)`로 기동되며, lifespan 훅에서 `Person`·`Place`·`Event`·`PeopleGroup`·`Book` 라벨에 대해 `theographic_id` 인덱스를 `CREATE INDEX ... IF NOT EXISTS`로 생성한다(실패 시 로깅 후 인덱스 없이 계속).
- **CORS**: `CORSMiddleware`로 `allow_origins=["*"]`, `allow_methods=["GET"]`, `allow_credentials=False`. API는 읽기 전용 GET만 노출.
- **라우터 구성**: `main.py`가 7개 라우터를 include — `backend/app/routes/`의 `nodes.py`, `events.py`, `search.py`, `books.py`, `persons.py`, `journey.py`, `places.py`. 모든 엔드포인트가 `@router.get(...)` 단일 메서드.
- **DB 접근 계층**: `backend/app/db.py`. 모듈 전역 싱글턴 드라이버(`get_driver()`)를 lazy 초기화. URI/USER/PASSWORD를 환경변수(`NEO4J_URI` 기본 `bolt://localhost:7687`, `NEO4J_USER` 기본 `neo4j`, `NEO4J_PASSWORD` 필수)에서 읽는다.
- **오버레이 헬퍼**: `backend/app/overlays.py`. `DATA_DIR` 환경변수(기본 `/app/data`) → 저장소 `data/` 순으로 JSON을 탐색하고 `lru_cache`로 캐시한다.
- **데이터 적재/생성 스크립트**: `backend/app/`과 무관한 빌드/시드 스크립트가 `backend/scripts/`에 다수 존재(`load_theographic.py`, `inject_ko_names.py`, `generate_*.py` 등). 표준 라이브러리 `urllib.request`로 외부에서 받아 Neo4j에 적재하거나 `data/` JSON에 굽는다(상세는 INTEGRATIONS.md).

## Frontend (React + Vite)

- **빌드 도구**: Vite 8 (`vite` `^8.0.12`), 플러그인 `@vitejs/plugin-react` `^6.0.1`. 설정 파일 `frontend/vite.config.js`.
  - `manualChunks`로 `node_modules` 코드를 분리하며, `maplibre-gl`은 별도 `maplibre` 청크, 나머지는 `vendor` 청크로 묶는다.
- **프레임워크/주요 의존성** (`frontend/package.json`):
  - `react` / `react-dom` `^19.2.6` (React 19).
  - `maplibre-gl` `^5.24.0` — 지도 렌더링(`frontend/src/MapView.jsx`에서 `maplibregl.Map` 사용, CSS도 함께 import).
  - `lucide-react` `^1.17.0` — 아이콘.
- **모듈 형식**: `"type": "module"` (ESM).
- **npm 스크립트**: `dev`(`vite`), `build`(`vite build`), `lint`(`eslint .`), `preview`(`vite preview`).
- **린트**: ESLint 10 flat config (`frontend/eslint.config.js`). `@eslint/js` recommended + `eslint-plugin-react-hooks` + `eslint-plugin-react-refresh`(vite preset), `dist`는 globalIgnore. 브라우저 globals, JSX 활성.
- **API 클라이언트**: `frontend/src/api.js`. 단일 베이스 URL `import.meta.env.VITE_API_URL || 'http://localhost:8000'` + `apiGet()` GET 헬퍼(비-OK 응답은 status를 담은 Error로 reject, `AbortError` 전파).
- **빌드타임 환경**: `frontend/.env.production`에 `VITE_API_URL=/api`. 프로덕션 빌드는 `/api`로 주입되어 nginx 프록시(`/api → api:8000`)를 탄다.
- **엔트리**: `frontend/index.html` + `frontend/src/main.jsx` → `App.jsx`.

## Neo4j (graph DB)

- **이미지**: `neo4j:5` (`docker-compose.yml`).
- **인증**: `NEO4J_AUTH=neo4j/${NEO4J_PASSWORD}` 형식으로 compose가 비밀번호로부터 파생(`.env`의 `NEO4J_PASSWORD`만 설정).
- **포트**: `127.0.0.1:7474`(HTTP 브라우저)와 `127.0.0.1:7687`(Bolt)을 **루프백에만** 바인딩 — 호스트 외부 비노출.
- **영속성**: 명명 볼륨 `neo4j_data:/data`.

## Docker Compose 스택

`docker-compose.yml`은 프로젝트명 `biblemap`(deploy.sh의 `-p biblemap`)로 3개 서비스를 정의:

- **`neo4j`**: 위 참조. `restart: unless-stopped`.
- **`api`**: `build: ./backend`. 환경변수로 `NEO4J_URI=bolt://neo4j:7687`(compose 네트워크 내부 DNS), `NEO4J_USER`, `NEO4J_PASSWORD` 주입. `./data:/app/data` 볼륨 마운트, `depends_on: [neo4j]`. **호스트로 포트 publish 없음**(외부 직접 접근 불가, nginx 프록시 경유만).
- **`nginx`**: `nginx:alpine`. 호스트 `8080 → 80` publish. `./frontend/dist:/usr/share/nginx/html:ro`(정적 빌드 산출물)와 `./nginx/nginx.conf:/etc/nginx/nginx.conf:ro` 마운트. `depends_on: [api]`.

`NEO4J_PASSWORD`는 compose의 `${NEO4J_PASSWORD:?...}` 가드로 미설정 시 기동 실패. 호스트 `.env`(`.env.example` 참조)에서 공급.

## nginx (reverse proxy)

`nginx/nginx.conf`:

- `location /api/` → `proxy_pass http://api:8000/`(트레일링 슬래시로 `/api` prefix 제거). `Host`·`X-Real-IP`·`X-Forwarded-For`·`X-Forwarded-Proto` 헤더 전달.
- `location = /index.html` → `Cache-Control: no-cache, no-store, must-revalidate`(항상 최신).
- 정적 에셋(`js|css|png|jpg|jpeg|gif|ico|svg|woff2?`) → `Cache-Control: public, max-age=31536000, immutable`(1년).
- `location /` → `try_files $uri /index.html`(SPA 폴백).

## Build / Config 요약

- **프론트 빌드 산출물**: `frontend/dist`(nginx가 read-only 마운트). HMR 아님 — 로컬 검증 전 `npm run build` 필요.
- **배포 자동화**: `deploy.sh`(상세 INTEGRATIONS.md) — 프론트 빌드 → `docker compose -p biblemap build api` → `up -d api nginx` → 한글 이름 주입 스크립트 실행.
- **시드/생성 데이터**: 저장소 `data/` 하위에 카테고리별 JSON(`authored_events`, `book_context`, `book_events`, `book_years_approx`, `character_traits`, `event_verses`, `names_ko`, `person_events`, `place_context`, `place_coords`, `verse_events`).
