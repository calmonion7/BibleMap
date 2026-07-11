---
last_mapped_commit: 04e9be173b6a321e4daaa417f6f47004dc3cd687
mapped: 2026-07-11
---

# Technology Stack

## 언어 및 런타임

**주요 언어:**
- Python 3.12 — 백엔드 API 및 데이터 파이프라인 스크립트 (`backend/app/`, `backend/scripts/`). 런타임 이미지는 `python:3.12-slim`(`backend/Dockerfile`).
- JavaScript (ES modules, JSX) — 프론트엔드 SPA (`frontend/src/`). TypeScript 미사용, `@types/react`·`@types/react-dom`만 devDependency로 존재한다.

**보조 언어:**
- Bash — 배포 스크립트 (`deploy.sh`), CI 스텝 인라인 (`.github/workflows/deploy.yml`).
- Cypher — Neo4j 쿼리. 라우트(`backend/app/routes/*.py`)와 로더/검증 스크립트(`backend/scripts/*.py`) 내부에 인라인 문자열로 존재한다.

**패키지 매니저:**
- Python: pip (`backend/requirements.txt`, 버전 고정 명시). lockfile 없음.
- Node: npm (`frontend/package-lock.json`, lockfileVersion 3). `frontend/package.json`의 `"type": "module"`.

## 런타임 환경

- Python 3.12 (컨테이너), README는 로컬 개발 시 Python 3.11+ 요구.
- Node.js 18+ (README 기준). 프론트 빌드는 컨테이너 밖 호스트에서 실행되어 `frontend/dist/`를 산출한다(`deploy.sh` [1/3] 단계).
- Docker / docker compose — 3서비스 오케스트레이션 (`docker-compose.yml`, compose 프로젝트명 `biblemap`).

## 프레임워크

**백엔드 (`backend/requirements.txt`):**
- FastAPI 0.136.3 — REST API 프레임워크. 앱 인스턴스는 `backend/app/main.py`의 `app = FastAPI(lifespan=lifespan)`.
- Uvicorn 0.49.0 — ASGI 서버. 컨테이너 CMD: `uvicorn app.main:app --host 0.0.0.0 --port 8000` (`backend/Dockerfile`). 로컬은 `python3 -m uvicorn backend.app.main:app --reload` (README).
- neo4j 6.2.0 — Neo4j 공식 Python 드라이버 (`GraphDatabase.driver`, `backend/app/db.py`).
- 로깅 — `backend/app/main.py`의 `_configure_logging()`이 import 시점(라우터 import 전)에 1회 호출되어 `logging.basicConfig(level=INFO)`를 건다. `neo4j`/`urllib3`/`asyncio` 로거는 WARNING으로 승격, `uvicorn`/`uvicorn.access`는 자체 핸들러 보유로 `propagate=False`(단 `uvicorn.error`는 제외 — 걸면 기동/에러 로그가 사라짐).

**프론트엔드 (`frontend/package.json`):**
- React 19.2.6 + react-dom 19.2.6 — SPA UI. 엔트리 `frontend/src/main.jsx`, 마운트 대상 `#root` (`frontend/index.html`).
- maplibre-gl 5.24.0 — 지도 렌더링 (`frontend/src/MapView.jsx`에서 `import maplibregl`, CSS는 `maplibre-gl/dist/maplibre-gl.css`).
- lucide-react 1.17.0 — 아이콘.

**빌드/개발 도구:**
- Vite 8.0.12 — 번들러/개발 서버 (`frontend/vite.config.js`). `@vitejs/plugin-react` 6.0.1 사용. 스크립트: `dev`(vite), `build`(vite build), `preview`, `lint`.
- ESLint 10.3.0 (flat config, `frontend/eslint.config.js`) — `@eslint/js` recommended + `eslint-plugin-react-hooks` + `eslint-plugin-react-refresh`. `dist`는 무시.

## 데이터 계층

- **Neo4j 5** — 그래프 DB (`docker-compose.yml` 서비스 `neo4j`, 이미지 `neo4j:5`). 상세는 `INTEGRATIONS.md` 참고.
- **JSON 오버레이/적재 파일** — `data/` 하위 15개 디렉터리(`authored_events`, `authored_persons`, `book_context`, `book_events`, `book_years_approx`, `character_traits`, `date_corrections`, `event_verses`, `names_ko`, `person_events`, `person_relations`, `place_context`, `place_coords`, `tours`, `verse_events`). API 컨테이너에 `./data:/app/data`로 마운트된다. 이 중 일부(`book_events`, `event_verses`, `tours`, `journey`/`persons`/`places` 관련 파일 등)는 런타임에 라우트가 직접 조회하고, 나머지(`names_ko`, `place_coords`, `book_context`, `character_traits`, `place_context`, `authored_*`, `date_corrections` 등)는 `backend/scripts/`의 적재·주입 스크립트가 Neo4j에 반영하는 입력 소스다. 런타임 조회 헬퍼는 `backend/app/overlays.py`(`DATA_DIR` 우선, 없으면 레포 내 `data/`로 폴백, `book_events`/`event_verses`는 `lru_cache`로 1회 로드).
- **`data/date_corrections/`** — `events.json`·`persons.json` 연대 교정 오버레이(2026-07-11 신설). 런타임 조회 대상이 아니라 `backend/scripts/inject_date_corrections.py`가 Neo4j에 `SET`으로 반영하는 입력 소스다. 상세는 `INTEGRATIONS.md` 데이터 파이프라인 참고.

## 빌드 구성

**백엔드 이미지 (`backend/Dockerfile`):**
- `python:3.12-slim` 기반, `WORKDIR /app`, `requirements.txt` 설치 후 `app/`만 복사. `pip install --no-cache-dir`. `backend/scripts/`는 이미지에 포함되지 않으며 호스트에서 실행한다.

**프론트 번들 (`frontend/vite.config.js`):**
- Rollup `manualChunks`로 청크 분리: `maplibre-gl` → `maplibre` 청크, 그 외 `node_modules` → `vendor` 청크.
- 산출물 `frontend/dist/`는 nginx 컨테이너에 `:ro`로 마운트된다(HMR 아님 — 검증 전 `npm run build` 필요).
- 디자인 토큰은 `frontend/src/index.css`가 정본이다(다크 단일 "Night Atlas", ADR-0013) — `:root`에 표면(`--bg-0`~`--bg-3`), 텍스트(`--ink*`), 브랜드 액센트(`--gold`, `--gold-dim`), 구절 본문 전용 양피지(`--paper*`), 서체(`--serif`/`--sans`) 변수를 선언하고 `color-scheme: dark` 단일. `frontend/src/theme.js`의 `NIGHT` 상수는 이 값들을 JS(MapLibre paint 등 CSS 변수 미적용 지점)에서 쓰기 위한 하드코딩 사본.

**정적 서빙 (`nginx/nginx.conf`):**
- `nginx:alpine`. `/api/` → `http://api:8000/` 프록시. `index.html`은 no-cache, 해시 에셋(js/css/이미지/폰트)은 `max-age=31536000, immutable`. SPA fallback: `try_files $uri /index.html`.

## 설정 (환경변수)

- `NEO4J_PASSWORD` (필수) — 루트 `.env`에서 로드. `docker-compose.yml`가 `${NEO4J_PASSWORD:?...}`로 강제하며, `neo4j` 서비스는 `NEO4J_AUTH=neo4j/${NEO4J_PASSWORD}`로 파생한다. 템플릿은 `.env.example`. 실제 값은 문서에 기록하지 않는다.
- `NEO4J_URI` / `NEO4J_USER` — compose가 API에 `bolt://neo4j:7687` / `neo4j`로 주입. `backend/app/db.py`와 각 스크립트는 미설정 시 `bolt://localhost:7687` / `neo4j` 기본값 사용(호스트에서 스크립트 직접 실행 시 로컬 바인딩으로 접속).
- `DATA_DIR` — 오버레이 조회 기준 경로 (`backend/app/overlays.py`, 기본 `/app/data`, 미탐 시 레포 내 `data/`로 폴백).
- `VITE_API_URL` — 프론트 API 베이스 URL (빌드타임 주입). 프로덕션은 `frontend/.env.production`의 `/api`(→ nginx 프록시), 미설정 시 `http://localhost:8000` (`frontend/src/api.js`).
- `ANTHROPIC_API_KEY` — 데이터 생성 스크립트 전용(런타임 API 미사용). `INTEGRATIONS.md` 참고.

## 플랫폼 요구사항

**개발:**
- Docker Desktop 실행, Python 3.11+, Node.js 18+ (README). 로컬 포트: API 8000, 프론트 dev 5173, Neo4j 7474/7687.

**프로덕션:**
- 단일 호스트 self-hosted 배포. GitHub Actions self-hosted 러너가 `main` push 시 `deploy.sh` 실행(`.github/workflows/deploy.yml`). 노출 포트는 nginx `8080:80`뿐이며, API(8000)는 외부 미노출·Neo4j 포트는 `127.0.0.1` 바인딩.
- compose 프로젝트명 `biblemap`, 재시작 정책 `unless-stopped`, 볼륨 `neo4j_data`.
