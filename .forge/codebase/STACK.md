---
last_mapped_commit: 79f9d9df07c0d79f8fa07940e3f76c8d5424524b
mapped: 2026-06-28
---
# 기술 스택

**분석 일자:** 2026-06-28

## 언어

**주력:**
- Python 3.12 — 백엔드 API 및 데이터 적재/생성 스크립트 (`backend/app/`, `backend/scripts/`)
- JavaScript (ESM, JSX) — 프론트엔드 (`frontend/src/`, `"type": "module"` in `frontend/package.json`)

**보조:**
- Cypher — Neo4j 쿼리. 백엔드 라우트와 적재 스크립트에 인라인으로 작성 (`backend/app/routes/*.py`, `backend/scripts/load_*.py`)
- Bash — 배포 스크립트 (`deploy.sh`)
- 설정 언어: YAML (`docker-compose.yml`, `.github/workflows/deploy.yml`), Nginx conf (`nginx/nginx.conf`), Dockerfile (`backend/Dockerfile`)

TypeScript는 사용하지 않음. 프론트엔드는 순수 JS/JSX이며 `@types/react`·`@types/react-dom`는 에디터/린트 보조용으로만 devDependencies에 존재.

## 런타임

**백엔드:**
- Python 3.12 (`backend/Dockerfile`: `FROM python:3.12-slim`)
- ASGI 서버: uvicorn (컨테이너 CMD `uvicorn app.main:app --host 0.0.0.0 --port 8000`)

**프론트엔드:**
- 브라우저 런타임 (정적 SPA). `frontend/dist`가 nginx로 서빙됨
- Node.js (빌드타임 전용). `.nvmrc`·`engines` 명시 없음 — 버전 핀 미설정

**패키지 매니저:**
- 프론트엔드: npm. Lockfile `frontend/package-lock.json` 존재(커밋됨)
- 백엔드: pip + `backend/requirements.txt` (버전 고정). 별도 lockfile 없음

## 프레임워크

**핵심 (백엔드):**
- FastAPI 0.136.3 — REST API 프레임워크 (`backend/app/main.py`). 라우터 7개 등록(`nodes`, `events`, `search`, `books`, `persons`, `journey`, `places`)
- uvicorn 0.49.0 — ASGI 서버
- neo4j 6.2.0 (Python 드라이버) — 그래프 DB 클라이언트 (`backend/app/db.py`, 모든 `backend/scripts/*.py`)

**핵심 (프론트엔드):**
- React 19.2.6 + react-dom 19.2.6 — UI (`frontend/src/App.jsx` 외)
- maplibre-gl 5.24.0 — 지도 렌더링 (`frontend/src/MapView.jsx`, `frontend/src/mapLayers.js`)
- lucide-react 1.17.0 — 아이콘

**테스트:**
- 자동화 테스트 프레임워크 없음. `package.json`·`requirements.txt` 모두 테스트 러너 미포함. 검증은 수동(Playwright 수동 구동, 프로젝트 메모리 참조)

**빌드/개발:**
- Vite 8.0.12 — 프론트엔드 번들러/개발 서버 (`frontend/vite.config.js`)
- @vitejs/plugin-react 6.0.1 — React 플러그인
- ESLint 10.3.0 — 린터 (`frontend/eslint.config.js`, flat config)
  - @eslint/js 10.0.1
  - eslint-plugin-react-hooks 7.1.1
  - eslint-plugin-react-refresh 0.5.2
  - globals 17.6.0

## 주요 의존성

**런타임 핵심:**
- `fastapi==0.136.3` — 백엔드 HTTP 표면 전체
- `neo4j==6.2.0` — 유일한 데이터 저장소 접근 경로. 앱은 런타임에 Neo4j 외 외부 호출 없음
- `uvicorn==0.49.0` — 프로덕션 ASGI 구동
- `maplibre-gl@5.24.0` — 프론트 지도 핵심. Vite에서 별도 청크(`maplibre`)로 분리 (`frontend/vite.config.js`의 `manualChunks`)
- `react@19.2.6` / `react-dom@19.2.6`

**빌드/스크립트 전용 (앱 런타임 아님):**
- `anthropic` (Python SDK) — 데이터 생성 스크립트에서만 사용. `requirements.txt`에 없음 → 스크립트 실행 시 별도 설치 필요. 사용처: `backend/scripts/generate_book_context.py`, `generate_book_events.py`, `generate_person_traits.py`, `generate_verse_events.py` (모델 `claude-haiku-4-5-20251001`)
- `urllib.request` (표준 라이브러리) — Theographic/getbible 빌드타임 fetch (`backend/scripts/load_theographic.py`, `enrich_place_coords.py`, `generate_verse_text.py`)

**인프라:**
- `neo4j:5` (Docker 이미지) — 그래프 DB (`docker-compose.yml`)
- `nginx:alpine` (Docker 이미지) — 정적 서빙 + `/api` 리버스 프록시 (`docker-compose.yml`, `nginx/nginx.conf`)
- `python:3.12-slim` (Docker 베이스) — API 이미지 (`backend/Dockerfile`)

## 설정

**환경 변수:**
- 정본 `.env` (루트, gitignore 대상). 템플릿 `.env.example`은 `NEO4J_PASSWORD`만 정의
- compose는 `NEO4J_AUTH=neo4j/${NEO4J_PASSWORD}`로 파생하며, 미설정 시 `${NEO4J_PASSWORD:?...}`로 기동 실패 (`docker-compose.yml`)
- 백엔드 런타임: `NEO4J_URI`(기본 `bolt://localhost:7687`, compose는 `bolt://neo4j:7687`), `NEO4J_USER`(기본 `neo4j`), `NEO4J_PASSWORD`(필수, 미설정 시 `get_driver()`가 RuntimeError) — `backend/app/db.py`
- 스크립트 전용: `ANTHROPIC_API_KEY`(generate_* 스크립트), 각 스크립트도 동일 `NEO4J_*`를 직접 읽음

**프론트엔드 빌드 설정:**
- `frontend/.env.production`: `VITE_API_URL=/api` — 빌드타임 주입. 미설정 시 `frontend/src/api.js`가 `http://localhost:8000`로 폴백
- `frontend/vite.config.js`: `manualChunks`로 `maplibre-gl` → `maplibre` 청크, 나머지 `node_modules` → `vendor` 청크 분리

**빌드 설정 파일:**
- `frontend/vite.config.js`, `frontend/eslint.config.js`, `frontend/index.html`
- `backend/Dockerfile` (단일 스테이지: requirements 설치 → `app/` 복사)

## 플랫폼 요구사항

**개발:**
- Docker + docker compose (compose 플러그인). 로컬 :8080은 `frontend/dist` 마운트(HMR 아님) → 검증 전 `cd frontend && npm run build` 필요
- Python 3.12 (스크립트 직접 실행 시), Node.js (프론트 빌드 시)

**프로덕션:**
- 단일 self-hosted 스택. GitHub Actions self-hosted 러너가 `main` push 시 `git reset --hard origin/main` 후 `deploy.sh` 실행 (`.github/workflows/deploy.yml`)
- `deploy.sh` 단계: ① 프론트 `npm install && npm run build` → ② `docker compose -p biblemap build api` → ③ `docker compose -p biblemap up -d api nginx` → ④ `backend/scripts/inject_ko_names.py`로 한글 이름 주입(최대 15회 재시도)
- compose 프로젝트명 `biblemap`. 노출 포트: nginx `8080:80`. Neo4j는 `127.0.0.1`에만 바인딩(`7474`, `7687`). API(:8000)는 호스트 미노출 — nginx 프록시만 경유
- macOS 키체인 우회를 위해 `deploy.sh`가 임시 `DOCKER_CONFIG` 생성

---

*스택 분석: 2026-06-28*
