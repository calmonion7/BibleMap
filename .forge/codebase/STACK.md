---
last_mapped_commit: 26240c7cf18f421b2f8baa4fd6584f40eede57b0
mapped: 2026-06-11
---

# STACK

BibleMap의 기술 스택 — 언어, 런타임, 프레임워크, 의존성, 빌드/설정 파일. 백엔드와 프론트엔드를 모두 다룬다.

## 전체 구조

모노레포 형태로 단일 Git 저장소 안에 백엔드(`backend/`)와 프론트엔드(`frontend/`)가 함께 있다. 배포는 Docker Compose 기반이며 Neo4j, FastAPI API, Nginx 세 컨테이너로 구성된다.

- `backend/` — Python FastAPI API 서버 + 데이터 적재 스크립트
- `frontend/` — React + Vite SPA
- `data/names_ko/` — 한글 이름 매핑 JSON 데이터(`events.json`, `groups.json`, `people.json`, `places.json`)
- `nginx/nginx.conf` — 정적 파일 서빙 + API 리버스 프록시
- `docker-compose.yml` — 3개 서비스 오케스트레이션
- `deploy.sh`, `scripts/auto-deploy-poll.sh` — 배포 스크립트

## 백엔드

### 언어 / 런타임

- **Python 3.12** — 빌드 이미지 기준(`backend/Dockerfile`의 `FROM python:3.12-slim`). README(`README.md`)는 로컬 개발 사전 준비로 Python 3.11+를 명시한다.
- 패키지 매니저: **pip**(`pip install --no-cache-dir -r requirements.txt`).

### 프레임워크 / 핵심 의존성

`backend/requirements.txt`에 고정 버전으로 명시:

- **fastapi 0.136.3** — 웹 프레임워크(`backend/app/main.py`에서 `FastAPI`, `CORSMiddleware`, `APIRouter` 사용)
- **uvicorn 0.49.0** — ASGI 서버. 컨테이너 기동 명령은 `uvicorn app.main:app --host 0.0.0.0 --port 8000`(`backend/Dockerfile`), 로컬은 `python3 -m uvicorn backend.app.main:app --reload`(`README.md`)
- **neo4j 6.2.0** — Neo4j 공식 Python 드라이버(`backend/app/db.py`에서 `GraphDatabase.driver` 사용)

### 애플리케이션 구조

- `backend/app/main.py` — 앱 진입점. CORS 미들웨어(`allow_origins=["*"]`), lifespan 훅에서 Neo4j 인덱스 생성, 4개 라우터 등록
- `backend/app/db.py` — Neo4j 드라이버 싱글턴(`get_driver`)
- `backend/app/routes/` — API 라우터 모듈
  - `nodes.py` — `GET /node/{node_id}`, `GET /node/{node_id}/places`, `GET /node/{node_id}/neighbors/grouped`
  - `places.py` — `GET /places`
  - `events.py` — `GET /events`
  - `search.py` — `GET /search`(쿼리 파라미터)
- `backend/scripts/` — 일회성 데이터 적재 스크립트(`load_theographic.py`, `inject_ko_names.py`)

라우트는 직접 Cypher 쿼리를 실행한다(`session.run(...)`). ORM/쿼리 빌더 계층은 없다.

## 프론트엔드

### 언어 / 런타임 / 빌드

- **JavaScript(JSX, ESM)** — `frontend/package.json`의 `"type": "module"`
- **Node.js 18+**(`README.md`), 패키지 매니저: **npm**(`frontend/package-lock.json` 존재)
- **Vite 8.0.12** — 빌드 도구 겸 개발 서버(`frontend/vite.config.js`). 설정은 `@vitejs/plugin-react`만 적용한 최소 구성
- 스크립트(`frontend/package.json`): `dev`(vite), `build`(vite build), `lint`(eslint .), `preview`(vite preview)

### 프레임워크 / 핵심 의존성

`frontend/package.json` dependencies:

- **react 19.2.6 / react-dom 19.2.6** — UI 프레임워크
- **maplibre-gl 5.24.0** — 지도 렌더링(`frontend/src/MapView.jsx`, `maplibre-gl/dist/maplibre-gl.css` 임포트)
- **cytoscape 3.34.0** + **cytoscape-cose-bilkent 4.1.0** + **cytoscape-expand-collapse 4.1.1** — 그래프 뷰 렌더링/레이아웃/접기·펼치기(`frontend/src/GraphView.jsx`)
- **d3 7.9.0** — 데이터 시각화(타임라인 등)
- **lucide-react 1.17.0** — 아이콘

devDependencies: **eslint 10.3.0**(+ `@eslint/js`, `eslint-plugin-react-hooks`, `eslint-plugin-react-refresh`, `globals`), `@vitejs/plugin-react 6.0.1`, `@types/react`, `@types/react-dom`.

### 애플리케이션 구조 (`frontend/src/`)

- `main.jsx` — React 진입점
- `App.jsx` — 루트 컴포넌트, 검색(`/search` 호출) 및 뷰 조정
- `MapView.jsx` — MapLibre GL 지도 뷰
- `GraphView.jsx` — Cytoscape 그래프 뷰
- `TimelineView.jsx` — 타임라인 뷰(`/events` 호출)
- `SidePanel.jsx` — 노드 상세 패널(`/node/{id}` 호출)
- `index.css`, `App.css` — 스타일
- `index.html` — Vite 엔트리 HTML
- `public/` — 정적 자산(`favicon.svg`, `icons.svg`)
- `eslint.config.js` — flat config 형식 ESLint 설정(`dist` 무시, JS/JSX 대상)

빌드 산출물은 `frontend/dist/`(gitignore됨, `frontend/.gitignore` 및 루트 `.gitignore`).

## 설정 / 환경 파일

- 루트 `.env` / `.env.example` — `NEO4J_AUTH=neo4j/<password>` 형식. `.env`는 gitignore됨(`.gitignore`)
- `frontend/.env.production` — `VITE_API_URL=/api`(프로덕션에서 Nginx 프록시 경로 사용)
- 프론트엔드 API 베이스는 `import.meta.env.VITE_API_URL`을 읽고, 미설정 시 `http://localhost:8000`으로 폴백(`App.jsx`, `MapView.jsx`, `GraphView.jsx`, `TimelineView.jsx`, `SidePanel.jsx`)

## 컨테이너 / 인프라

- `backend/Dockerfile` — `python:3.12-slim` 베이스, requirements 설치 후 `app/` 복사, uvicorn 기동
- `docker-compose.yml` — 3개 서비스
  - `neo4j` — 이미지 `neo4j:5`, 포트 7474/7687을 `127.0.0.1`에만 바인딩, 데이터 볼륨 `neo4j_data`
  - `api` — `./backend` 빌드, `./data`를 `/app/data`로 마운트, neo4j 의존
  - `nginx` — 이미지 `nginx:alpine`, 호스트 8080→컨테이너 80, `frontend/dist`와 `nginx/nginx.conf`를 읽기 전용 마운트
- `nginx/nginx.conf` — `/api/`를 `http://api:8000/`로 프록시, SPA fallback(`try_files $uri /index.html`), 정적 자산 캐시 헤더

## 데이터

- `data/names_ko/` — 한글 이름·별칭 매핑 JSON 4종. `backend/scripts/inject_ko_names.py`가 이 디렉터리를 읽어 Neo4j 노드에 `nameKo`, `aliasesKo` 속성을 주입
- 원본 그래프 데이터는 외부 소스에서 적재(상세는 `INTEGRATIONS.md` 참조)
