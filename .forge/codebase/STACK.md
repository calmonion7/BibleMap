---
last_mapped_commit: 60716ea24a78866177eb8fe28dee9c43ced5ff0f
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

- **언어/런타임**: Python. Docker 이미지는 `python:3.12-slim` (`backend/Dockerfile`). 별도 `.python-version`/`pyproject.toml`/`runtime.txt` 없음. 호스트에서 직접 실행되는 `backend/scripts/inject_ko_names.py`는 호스트의 `python3`로 구동됨(`deploy.sh`).
- **프레임워크**: FastAPI.
- **ASGI 서버**: uvicorn. 컨테이너 실행 명령은 `uvicorn app.main:app --host 0.0.0.0 --port 8000` (`backend/Dockerfile`).
- **DB 드라이버**: 공식 `neo4j` Python 드라이버.

### 의존성 (`backend/requirements.txt`)

핀 고정된 3개 패키지뿐(버전 범위 없음).

- `fastapi==0.136.3`
- `neo4j==6.2.0`
- `uvicorn==0.49.0`

테스트/린트/포매터 의존성은 백엔드에 선언되어 있지 않음.

### 백엔드 구성 파일

- `backend/app/main.py` — FastAPI 앱 진입점. `lifespan` 컨텍스트에서 Neo4j 인덱스(`Person`/`Place`/`Event`/`PeopleGroup`의 `theographic_id`)를 `CREATE INDEX ... IF NOT EXISTS`로 생성. 실패 시 예외를 로깅하고 인덱스 없이 계속 진행(`logging.exception`). CORS 미들웨어는 `allow_origins=["*"]`, `allow_methods=["GET"]`, `allow_credentials=False`, `allow_headers=["*"]`.
- `backend/app/db.py` — Neo4j 드라이버 싱글턴(`get_driver()`).
- `backend/app/routes/nodes.py`, `events.py`, `search.py` — API 라우터들.
- `backend/scripts/load_theographic.py` — Theographic 데이터셋을 원격에서 받아 Neo4j에 적재하는 스크립트 (배치 상수 `BATCH_NODE=500`, `BATCH_REL=1000`).
- `backend/scripts/inject_ko_names.py` — `data/names_ko/*.json`을 읽어 노드에 `nameKo`/`aliasesKo` 속성을 주입하는 스크립트.

## 프론트엔드

- **언어**: JavaScript (JSX), ES 모듈 (`package.json`의 `"type": "module"`). TypeScript 컴파일러는 사용하지 않으며 `@types/react`/`@types/react-dom`만 에디터 지원용으로 존재.
- **프레임워크**: React 19 (`react ^19.2.6`, `react-dom ^19.2.6`).
- **빌드 도구**: Vite (`vite ^8.0.12`), 플러그인 `@vitejs/plugin-react ^6.0.1`. `frontend/vite.config.js`는 기본 React 플러그인만 설정.
- **린트**: ESLint 10 (`eslint ^10.3.0`, `@eslint/js ^10.0.1`, flat config — `frontend/eslint.config.js`).

### 런타임 의존성 (`frontend/package.json`)

- `react` ^19.2.6 / `react-dom` ^19.2.6
- `maplibre-gl` ^5.24.0 — 지도 렌더링 (`frontend/src/MapView.jsx`)
- `cytoscape` ^3.34.0 + `cytoscape-cose-bilkent` ^4.1.0 + `cytoscape-expand-collapse` ^4.1.1 — 그래프 시각화 (`frontend/src/GraphView.jsx`)
- `lucide-react` ^1.17.0 — 아이콘 (`frontend/src/App.jsx`)

### dev 의존성 (`frontend/package.json`)

- `vite ^8.0.12`, `@vitejs/plugin-react ^6.0.1`
- `eslint ^10.3.0`, `@eslint/js ^10.0.1`
- `eslint-plugin-react-hooks ^7.1.1` — **v7**. flat 프리셋 `reactHooks.configs.flat.recommended`로 적용.
- `eslint-plugin-react-refresh ^0.5.2` — `reactRefresh.configs.vite` 사용.
- `globals ^17.6.0` — ESLint 브라우저 글로벌.
- `@types/react ^19.2.14`, `@types/react-dom ^19.2.3`

### npm 스크립트

`dev` (vite), `build` (vite build), `lint` (eslint .), `preview` (vite preview).

### 빌드 도구 상세

- **Vite** (`frontend/vite.config.js`): `defineConfig({ plugins: [react()] })` — 최소 설정, 별도 빌드/출력 오버라이드 없음. 빌드 산출물은 `frontend/dist/` (`deploy.sh`, nginx 볼륨 마운트, ESLint의 `globalIgnores(['dist'])`가 참조).
- **ESLint flat config** (`frontend/eslint.config.js`): `eslint/config`의 `defineConfig`/`globalIgnores` 사용. `dist` 무시. `**/*.{js,jsx}` 대상. extends에 `js.configs.recommended`, `reactHooks.configs.flat.recommended`, `reactRefresh.configs.vite`. `languageOptions`는 `globals.browser`와 `parserOptions: { ecmaFeatures: { jsx: true } }`.

### 프론트엔드 소스

- `frontend/src/main.jsx` — 진입점. `StrictMode`로 `App`을 렌더링.
- `frontend/src/App.jsx` — 탭(지도/타임라인/그래프) + 검색 UI.
- `frontend/src/MapView.jsx` — MapLibre GL 지도 뷰.
- `frontend/src/GraphView.jsx` — Cytoscape 그래프 뷰.
- `frontend/src/TimelineView.jsx` — `/events`를 받아 연도순 타임라인 렌더링.
- `frontend/src/SidePanel.jsx` — 선택 노드 상세/이웃 패널.

## 설정 (환경 변수)

- **`NEO4J_PASSWORD`** — Neo4j 비밀번호. **필수 환경 변수이며 코드에 기본 폴백이 없음.** `backend/app/db.py`, `backend/scripts/load_theographic.py`, `backend/scripts/inject_ko_names.py` 모두 미설정 시 `RuntimeError`를 던지는 fail-fast 구조. 루트 `.env`에서 공급.
- **`NEO4J_URI`** — 기본값 `bolt://localhost:7687`. compose의 `api` 서비스에서는 `bolt://neo4j:7687`.
- **`NEO4J_USER`** — 기본값 `neo4j`.
- **`VITE_API_URL`** — 프론트엔드 API 베이스 URL. 미설정 시 각 컴포넌트가 `http://localhost:8000`으로 폴백(`App.jsx`, `MapView.jsx`, `GraphView.jsx`, `TimelineView.jsx`, `SidePanel.jsx`). 프로덕션 빌드는 `frontend/.env.production`에서 `/api`로 설정(nginx 프록시 경로).
- `.env.example`은 `NEO4J_PASSWORD` 자리표시자만 제공하며 `NEO4J_AUTH`는 compose가 `neo4j/<password>`로 자동 파생한다고 명시.

## Docker 설정

- **`backend/Dockerfile`**: `python:3.12-slim`, `WORKDIR /app`, `pip --no-cache-dir`로 `requirements.txt` 설치, `app/` 복사, uvicorn을 8000 포트로 실행.
- **`docker-compose.yml`** (`version:` 키 없음 — Docker Compose V2 플러그인; `deploy.sh`에서 `-p biblemap`로 프로젝트명 지정). 서비스 3개:
  - `neo4j` — 이미지 `neo4j:5`. 포트는 루프백 전용 바인딩(`127.0.0.1:7474` HTTP, `127.0.0.1:7687` Bolt). 네임드 볼륨 `neo4j_data:/data`. `NEO4J_AUTH=neo4j/${NEO4J_PASSWORD:?...}` (미설정 시 compose 실패). `restart: unless-stopped`.
  - `api` — `./backend` 빌드. 환경: `NEO4J_URI=bolt://neo4j:7687`, `NEO4J_USER=neo4j`, `NEO4J_PASSWORD=${NEO4J_PASSWORD:?...}`. `./data:/app/data` 마운트. `depends_on: neo4j`. 호스트로 직접 노출 안 됨(nginx 경유). `restart: unless-stopped`.
  - `nginx` — 이미지 `nginx:alpine`. 호스트 `8080 -> 80` 노출. `./frontend/dist`(읽기 전용) 웹 루트, `./nginx/nginx.conf`(읽기 전용) 마운트. `depends_on: api`. `restart: unless-stopped`.
  - 네임드 볼륨: `neo4j_data`.
- **`nginx/nginx.conf`**: 80 포트 단일 서버. `/api/`를 `http://api:8000/`로 프록시(`/api` 프리픽스 제거). SPA를 `/usr/share/nginx/html`에서 `try_files $uri /index.html`로 서빙. `index.html`은 `no-cache`, 해시된 정적 자산(`js|css|png|jpg|jpeg|gif|ico|svg|woff2?`)은 `max-age=31536000, immutable`.
