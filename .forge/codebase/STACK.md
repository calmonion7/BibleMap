---
last_mapped_commit: 60962d0693f3bfaf4b8d24ce6f97d7b392770d85
mapped: 2026-06-11
---

# STACK

BibleMap의 기술 스택, 런타임 버전, 의존성, 빌드 도구, 설정을 정리한 구현 사실 문서.

## 전체 구조

모노레포. 루트에 `docker-compose.yml`, `deploy.sh`, CI 워크플로우가 있고, 두 개의 애플리케이션이 있다.

- `backend/` — Python FastAPI API 서버
- `frontend/` — React + Vite SPA
- `nginx/` — 정적 파일 서빙 + API 리버스 프록시
- `data/names_ko/` — 한글 이름 매핑 JSON (people/places/events/groups)

## 백엔드

- **언어/런타임**: Python. Docker 이미지는 `python:3.12-slim` (`backend/Dockerfile`). 별도 `.python-version`/`pyproject.toml`/`runtime.txt` 없음.
- **프레임워크**: FastAPI.
- **ASGI 서버**: uvicorn. 컨테이너 실행 명령은 `uvicorn app.main:app --host 0.0.0.0 --port 8000` (`backend/Dockerfile`).
- **DB 드라이버**: 공식 `neo4j` Python 드라이버.

### 의존성 (`backend/requirements.txt`)

핀 고정된 3개 패키지뿐.

- `fastapi==0.136.3`
- `neo4j==6.2.0`
- `uvicorn==0.49.0`

### 백엔드 구성 파일

- `backend/app/main.py` — FastAPI 앱 진입점. `lifespan` 컨텍스트에서 Neo4j 인덱스(`Person`/`Place`/`Event`/`PeopleGroup`의 `theographic_id`)를 `CREATE INDEX ... IF NOT EXISTS`로 생성. 실패 시 예외를 로깅하고 인덱스 없이 계속 진행(`logging.exception`). CORS 미들웨어는 `allow_origins=["*"]`, `allow_methods=["GET"]`, `allow_credentials=False`.
- `backend/app/db.py` — Neo4j 드라이버 싱글턴(`get_driver()`).
- `backend/app/routes/nodes.py` — `GET /node/{id}`, `GET /node/{id}/places`, `GET /node/{id}/neighbors/grouped`. 상수 `MAX_NEIGHBORS_PER_TYPE=30`, `NODE_NEIGHBOR_LIMIT=50`.
- `backend/app/routes/events.py` — `GET /events` (응답에 `Cache-Control: no-store`).
- `backend/app/routes/search.py` — `GET /search?q=` (상수 `SEARCH_LIMIT=20`).
- `backend/scripts/load_theographic.py` — Theographic 데이터셋을 원격에서 받아 Neo4j에 적재하는 스크립트 (배치 상수 `BATCH_NODE=500`, `BATCH_REL=1000`).
- `backend/scripts/inject_ko_names.py` — `data/names_ko/*.json`을 읽어 노드에 `nameKo`/`aliasesKo` 속성을 주입하는 스크립트.

## 프론트엔드

- **언어**: JavaScript (JSX), ES 모듈 (`package.json`의 `"type": "module"`).
- **프레임워크**: React 19 (`react ^19.2.6`, `react-dom ^19.2.6`).
- **빌드 도구**: Vite (`vite ^8.0.12`), 플러그인 `@vitejs/plugin-react ^6.0.1`. `frontend/vite.config.js`는 기본 React 플러그인만 설정.
- **린트**: ESLint 10 (flat config, `frontend/eslint.config.js`). `@eslint/js`, `eslint-plugin-react-hooks`, `eslint-plugin-react-refresh`, `globals`.
- **타입 정의**: `@types/react`, `@types/react-dom` (devDependency, 코드 자체는 순수 JS/JSX).

### 런타임 의존성 (`frontend/package.json`)

- `react` ^19.2.6 / `react-dom` ^19.2.6
- `maplibre-gl` ^5.24.0 — 지도 렌더링 (`frontend/src/MapView.jsx`)
- `cytoscape` ^3.34.0 + `cytoscape-cose-bilkent` ^4.1.0 + `cytoscape-expand-collapse` ^4.1.1 — 그래프 시각화 (`frontend/src/GraphView.jsx`)
- `lucide-react` ^1.17.0 — 아이콘 (`frontend/src/App.jsx`)

`d3` 의존성은 `package.json`과 `package-lock.json` 모두에서 부재함(확인됨). 차트/타임라인은 d3 없이 직접 구현됨.

### npm 스크립트

`dev` (vite), `build` (vite build), `lint` (eslint .), `preview` (vite preview).

### 프론트엔드 소스

- `frontend/src/main.jsx` — 진입점. `StrictMode`로 `App`을 렌더링, `./index.css` 임포트.
- `frontend/src/App.jsx` — 탭(지도/타임라인/그래프) + 검색 UI.
- `frontend/src/MapView.jsx` — MapLibre GL 지도 뷰.
- `frontend/src/GraphView.jsx` — Cytoscape 그래프 뷰. 기본 중심 노드 하드코딩 (`DEFAULT_NODE = 'recjNRR60PAuFtjha'`).
- `frontend/src/TimelineView.jsx` — `/events`를 받아 연도순 타임라인 렌더링.
- `frontend/src/SidePanel.jsx` — 선택 노드 상세/이웃 패널.
- `frontend/index.html` — Vite 진입 HTML.

## 빌드/배포 도구

- **컨테이너 오케스트레이션**: Docker Compose (`docker-compose.yml`). 서비스 3개 — `neo4j`(이미지 `neo4j:5`), `api`(`./backend` 빌드), `nginx`(`nginx:alpine`).
- **리버스 프록시**: nginx (`nginx/nginx.conf`). `/api/`를 `http://api:8000/`로 프록시, 정적 자산은 장기 캐시, `index.html`은 no-cache, SPA 폴백(`try_files $uri /index.html`).
- **배포 스크립트**: `deploy.sh` — 프론트엔드 빌드 → API 이미지 빌드 → 컨테이너 재시작(`docker compose -p biblemap up -d api nginx`) → 한글 이름 주입(최대 15회 재시도). 락 파일 `/tmp/biblemap-deploy.lock`. `.env`에서 `NEO4J_PASSWORD`를 로드해 호스트에서 직접 실행하는 inject 스크립트와 공유.
- **CI**: GitHub Actions (`.github/workflows/deploy.yml`). `main` 푸시 시 `self-hosted` 러너에서 워크트리를 `origin/main`으로 hard reset 후 `deploy.sh` 실행.
- **폴링 배포**: `scripts/auto-deploy-poll.sh` — 2분마다 GitHub 폴링, 새 커밋 시 자동 배포(별도 워크트리/브랜치 대상).

## 설정 (환경 변수)

- **`NEO4J_PASSWORD`** — Neo4j 비밀번호. **필수 환경 변수이며 코드에 기본 폴백이 없음.** `backend/app/db.py`, `backend/scripts/load_theographic.py`, `backend/scripts/inject_ko_names.py` 모두 미설정 시 `RuntimeError`를 던지는 fail-fast 구조.
- **`NEO4J_URI`** — 기본값 `bolt://localhost:7687`. compose의 `api` 서비스에서는 `bolt://neo4j:7687`.
- **`NEO4J_USER`** — 기본값 `neo4j`.
- **`VITE_API_URL`** — 프론트엔드 API 베이스 URL. 미설정 시 `http://localhost:8000` 폴백. 프로덕션 빌드는 `frontend/.env.production`에서 `/api`로 설정(nginx 프록시 경로).

### docker-compose 환경 (`docker-compose.yml`)

- `neo4j` 서비스의 `NEO4J_AUTH`는 독립적으로 설정되지 않고 `neo4j/${NEO4J_PASSWORD:?...}` 형태로 **파생**됨(미설정 시 compose가 실패).
- `api` 서비스도 `NEO4J_PASSWORD=${NEO4J_PASSWORD:?...}`로 동일 변수를 요구.
- Neo4j 포트는 `127.0.0.1`에만 바인딩(`7474`, `7687`). nginx만 외부 `8080`으로 노출.

### `.env` 파일

- 루트 `.env`는 gitignore 대상(`.gitignore`의 `# Env / .env`). 개발용 `NEO4J_PASSWORD` 값이 여기에만 존재.
- `.env.example`은 `NEO4J_PASSWORD` 자리표시자만 제공하며 `NEO4J_AUTH`는 compose가 자동 파생한다고 명시.
