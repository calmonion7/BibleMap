---
last_mapped_commit: 288b14e23c889de294d34d0f794867d4e313a421
mapped: 2026-06-11
---

# STACK

BibleMap은 백엔드(Python/FastAPI), 프론트엔드(React/Vite), 그래프 DB(Neo4j)를 Docker Compose로 묶고 nginx로 서빙하는 단일 저장소 프로젝트다. 이 문서는 언어·런타임·프레임워크·의존성·설정·빌드/배포 도구를 다룬다.

## 백엔드

### 런타임 / 언어
- Python 3.12 (`backend/Dockerfile`의 `FROM python:3.12-slim`).
- ASGI 서버는 uvicorn으로 `app.main:app`을 `0.0.0.0:8000`에서 구동 (`backend/Dockerfile`의 `CMD`).

### 프레임워크 / 의존성
`backend/requirements.txt`에 핀 고정된 3개:
- `fastapi==0.136.3`
- `neo4j==6.2.0` (공식 Neo4j Python 드라이버)
- `uvicorn==0.49.0`

### 앱 구조
- `backend/app/main.py` — FastAPI 앱 진입점. `lifespan` 컨텍스트에서 Neo4j 인덱스(`Person`/`Place`/`Event`/`PeopleGroup`의 `theographic_id`)를 `CREATE INDEX ... IF NOT EXISTS`로 생성하며, 실패해도 로그만 남기고 계속 진행한다. CORS 미들웨어는 `allow_origins=["*"]`, `allow_methods=["GET"]`, `allow_credentials=False`로 GET 전용 개방 설정. 라우터 3개(`nodes`, `events`, `search`)를 포함한다.
- `backend/app/db.py` — Neo4j 드라이버 싱글톤(`get_driver()`). 자세한 연결·환경변수는 `INTEGRATIONS.md` 참조.
- `backend/app/routes/nodes.py` — `/node/{id}`, `/node/{id}/places`, `/node/{id}/neighbors/grouped`. Cypher 쿼리로 노드·이웃·장소를 조회. `MAX_NEIGHBORS_PER_TYPE=30`, `NODE_NEIGHBOR_LIMIT=50` 상한.
- `backend/app/routes/events.py` — `/events`. `Cache-Control: no-store` 헤더로 응답.
- `backend/app/routes/search.py` — `/search?q=`. `name`/`nameKo` CONTAINS 검색, `SEARCH_LIMIT=20`.

### 데이터 적재 스크립트 (런타임 의존성 아님, 운영 도구)
- `backend/scripts/load_theographic.py` — Theographic Bible Metadata JSON을 GitHub raw에서 받아 Neo4j에 적재. `urllib.request`만 사용(추가 의존성 없음). 배치 크기 `BATCH_NODE=500`, `BATCH_REL=1000`.
- `backend/scripts/inject_ko_names.py` — `data/names_ko/`의 한글 이름 매핑(JSON)을 Neo4j 노드의 `nameKo`/`aliasesKo` 프로퍼티로 주입. `deploy.sh`가 배포 마지막 단계에서 호스트의 `python3`로 직접 실행한다(컨테이너 밖).

## 프론트엔드

### 런타임 / 빌드 도구
- `frontend/package.json` — `"type": "module"`, ESM. 빌드 도구는 Vite 8 (`vite ^8.0.12`), React 플러그인 `@vitejs/plugin-react ^6.0.1`.
- 스크립트: `dev`(vite), `build`(vite build), `lint`(eslint .), `preview`(vite preview).
- `frontend/vite.config.js` — `@vitejs/plugin-react`만 등록한 기본 설정. 프록시·별칭 등 추가 설정 없음.
- 진입점은 `frontend/index.html` → `src/main.jsx` (React `StrictMode` + `createRoot`).

### 런타임 의존성 (`dependencies`)
- `react ^19.2.6`, `react-dom ^19.2.6` (React 19).
- `maplibre-gl ^5.24.0` — 지도 렌더링 (`MapView.jsx`).
- `cytoscape ^3.34.0` + 확장 `cytoscape-cose-bilkent ^4.1.0`(레이아웃), `cytoscape-expand-collapse ^4.1.1`(노드 접기/펼치기) — 그래프 시각화 (`GraphView.jsx`).
- `lucide-react ^1.17.0` — 아이콘.

### 개발 의존성 (`devDependencies`)
- ESLint 10 (`eslint ^10.3.0`, `@eslint/js ^10.0.1`), flat config (`frontend/eslint.config.js`).
- `eslint-plugin-react-hooks ^7.1.1` — **캐럿 범위(`^7`)로 고정되어 버전 드리프트 위험이 있다.** 메이저 7 내 마이너/패치 업그레이드가 자동으로 끌려올 수 있어, react-hooks 룰 강화로 기존 코드가 새로 lint 에러를 낼 가능성이 있다(과거 SidePanel 리팩터 이력 참조). 재현 가능한 빌드를 원하면 정확한 버전 고정을 검토.
- `eslint-plugin-react-refresh ^0.5.2`, `globals ^17.6.0`, `@types/react ^19.2.14`/`@types/react-dom ^19.2.3`.
- ESLint flat config: `dist` 무시, `js.configs.recommended` + `reactHooks.configs.flat.recommended` + `reactRefresh.configs.vite` 확장, 브라우저 globals, JSX 활성화.

### 프론트엔드 환경변수
- `VITE_API_URL` — **빌드 타임** 주입(번들에 인라인됨). 5개 소스(`App.jsx`, `MapView.jsx`, `GraphView.jsx`, `SidePanel.jsx`, `TimelineView.jsx`)가 모두 `import.meta.env.VITE_API_URL || 'http://localhost:8000'` 패턴으로 읽는다(`App.jsx`만 상수명이 `API_BASE`).
  - 개발 기본값: `http://localhost:8000` (env 미설정 시 폴백).
  - 프로덕션: `frontend/.env.production`에 `VITE_API_URL=/api` (nginx 리버스 프록시 경로). 별도의 `.env`/`.env.development` 파일은 없다.

## 인프라 / 오케스트레이션

### Docker Compose (`docker-compose.yml`)
3개 서비스, 프로젝트명 `biblemap`(deploy.sh의 `-p biblemap`):
- `neo4j` — 이미지 `neo4j:5`. 포트는 **`127.0.0.1`에만 바인딩**(7474 HTTP, 7687 bolt) — 외부 비노출. `neo4j_data` 명명 볼륨으로 영속. `NEO4J_AUTH=neo4j/${NEO4J_PASSWORD:?...}`로 인증, 비밀번호 미설정 시 compose가 실패(fail-fast).
- `api` — `./backend` 빌드. `./data`를 `/app/data`로 바인드 마운트. `NEO4J_URI=bolt://neo4j:7687`, `NEO4J_USER=neo4j`, `NEO4J_PASSWORD`(fail-fast). `neo4j`에 `depends_on`.
- `nginx` — 이미지 `nginx:alpine`. 호스트 `8080` → 컨테이너 `80`. `./frontend/dist`를 `/usr/share/nginx/html`에 **읽기 전용(`:ro`)** 바인드 마운트, `./nginx/nginx.conf`도 `:ro`로 마운트. `api`에 `depends_on`.
- 모든 서비스 `restart: unless-stopped`.

### 빌드 / 배포 도구
- `deploy.sh` — 호스트에서 실행되는 배포 스크립트. 단계: (1) `frontend`에서 `npm install` + `npm run build` → `frontend/dist/` 생성, (2) `docker compose -p biblemap build api`, (3) `docker compose -p biblemap up -d api nginx`, (4) Neo4j 준비될 때까지 최대 15회 재시도하며 `inject_ko_names.py` 실행. lock 파일(`/tmp/biblemap-deploy.lock`)로 동시 실행 방지, 로그는 `~/Library/Logs/com.biblemap.deploy.log`. macOS 키체인 우회를 위해 임시 `DOCKER_CONFIG`를 만들고 `~/.docker/cli-plugins`를 심볼릭 링크해 `docker compose` 플러그인을 인식시킨다. `.env`가 있으면 로드해 `NEO4J_PASSWORD`를 inject 스크립트와 공유.
- 빌드 산출물(`frontend/dist`)은 컨테이너 안에서 빌드되지 않고 호스트에서 빌드된 뒤 nginx 컨테이너에 마운트되는 구조다. 즉 nginx는 정적 파일만 서빙하며 프론트엔드 빌드 책임은 `deploy.sh`에 있다.

CI(GitHub Actions self-hosted runner)와 배포 트리거의 자세한 흐름은 `INTEGRATIONS.md` 참조.
