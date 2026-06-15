---
last_mapped_commit: bfc1dd258b0308435ca24c48a82c9c86a9e622f1
mapped: 2026-06-16
---

# STACK

BibleMap의 기술 스택, 런타임 버전, 프레임워크, 의존성, 빌드 도구, 설정 파일을 정리한다. 구현 사실만 다루며 도메인 용어는 다루지 않는다(그건 CONTEXT.md 영역).

## 전체 구성

- 프론트엔드: React SPA (Vite 번들), `frontend/`
- 백엔드: FastAPI(Python) REST API, `backend/`
- 데이터베이스: Neo4j 그래프 DB
- 정적/프록시: nginx
- 배포: Docker Compose 3-서비스 (neo4j / api / nginx)
- 정적 데이터: `data/` (JSON 오버레이/주입용)

## 프론트엔드

### 런타임/언어
- JavaScript(ESM), `"type": "module"` — `frontend/package.json`
- JSX (React) — `frontend/src/*.jsx`
- TypeScript 미사용(`@types/react`만 devDependency로 존재, 타입 검사 단계 없음)

### 의존성 (`frontend/package.json`)
dependencies:
- `react` ^19.2.6
- `react-dom` ^19.2.6
- `maplibre-gl` ^5.24.0 — 지도 렌더링 (`frontend/src/MapView.jsx`에서 `import maplibregl`)
- `lucide-react` ^1.17.0 — 아이콘

devDependencies:
- `vite` ^8.0.12 (rolldown 기반 — `frontend/dist/assets/rolldown-runtime-*.js` 산출물 확인됨)
- `@vitejs/plugin-react` ^6.0.1
- `eslint` ^10.3.0, `@eslint/js` ^10.0.1
- `eslint-plugin-react-hooks` ^7.1.1
- `eslint-plugin-react-refresh` ^0.5.2
- `globals` ^17.6.0
- `@types/react` ^19.2.14, `@types/react-dom` ^19.2.3

lockfile: `frontend/package-lock.json` (lockfileVersion 3, npm)

### 스크립트 (`frontend/package.json`)
- `dev`: `vite`
- `build`: `vite build` → `frontend/dist/`
- `lint`: `eslint .`
- `preview`: `vite preview`

### 빌드 도구 — Vite 코드 스플리팅 (`frontend/vite.config.js`)
`build.rollupOptions.output.manualChunks(id)`로 `node_modules` 의존성을 청크 분리한다:
- `maplibre-gl`을 포함하는 모듈 → 별도 `maplibre` 청크
- 그 외 `node_modules` → `vendor` 청크
- 앱 코드 → `index` 청크

산출 확인 (`frontend/dist/assets/`): `maplibre-*.js`(~1MB), `vendor-*.js`(~190KB), `index-*.js`(~33KB), `maplibre-*.css`, `index-*.css`, `rolldown-runtime-*.js`. 대형 maplibre-gl 번들을 vendor에서 떼어내 캐싱/초기 로드를 분리하는 의도.

### Lint 설정 (`frontend/eslint.config.js`)
플랫 config. `js.configs.recommended` + `reactHooks.configs.flat.recommended` + `reactRefresh.configs.vite`. `dist` 무시, 대상 `**/*.{js,jsx}`, `globals.browser`, JSX 파서 옵션.

### HTML 엔트리 (`frontend/index.html`)
`<div id="root">` + `<script type="module" src="/src/main.jsx">`. 진입점 `frontend/src/main.jsx`.

### 프론트 소스 파일 (`frontend/src/`)
- `main.jsx` — 엔트리
- `App.jsx` — 루트 컴포넌트(검색 포함)
- `MapView.jsx` — maplibre 지도
- `SidePanel.jsx` — 상세 패널
- `TimelineView.jsx` — 타임라인
- `api.js` — 공유 API 클라이언트(베이스 URL + GET 헬퍼)
- `theme.js` — 타입별 색/한글 라벨 팔레트(공유)
- `convexHull.js` — 지도 영역 헐 계산
- `index.css` — 전역 스타일
- `assets/` — 이미지(hero.png 등)

## 백엔드

### 런타임/언어
- Python 3.12 (`backend/Dockerfile`: `FROM python:3.12-slim`)
- ASGI 서버: uvicorn (`uvicorn app.main:app --host 0.0.0.0 --port 8000`)

### 의존성 (`backend/requirements.txt`)
- `fastapi==0.136.3`
- `neo4j==6.2.0` — Neo4j 파이썬 드라이버
- `uvicorn==0.49.0`

참고: `anthropic` SDK는 `requirements.txt`에 없다. 데이터 생성 스크립트(`backend/scripts/generate_*.py`)에서 `import anthropic`로 쓰이며, 런타임 API가 아닌 별도 실행 도구이므로 환경에 별도 설치 가정.

### 앱 구조 (`backend/app/`)
- `main.py` — FastAPI 앱 생성, CORS 미들웨어, lifespan에서 Neo4j 인덱스 생성, 라우터 포함
- `db.py` — Neo4j 드라이버 싱글톤(`get_driver()`)
- `routes/nodes.py` — `/node/{id}`, `/node/{id}/places`, `/node/{id}/neighbors/grouped`
- `routes/events.py` — `/events`
- `routes/search.py` — `/search`
- `routes/books.py` — `/books` (추정연도 JSON 1회 캐시 `functools.lru_cache`, DATA_DIR→레포 상대경로 폴백)

### 데이터/스크립트 (`backend/scripts/`, 런타임 아님 — 적재/생성 도구)
- `load_theographic.py` — theographic 원본 JSON을 GitHub raw에서 받아 Neo4j 적재
- `load_books.py` — books.json 적재
- `inject_ko_names.py` — `data/names_ko/*.json` → Neo4j nameKo 주입
- `inject_book_context.py` — `data/book_context/books.json` 주입
- `inject_person_traits.py` — `data/character_traits/people.json` 주입
- `generate_book_context.py`, `generate_person_traits.py` — Anthropic API로 생성(모델 `claude-haiku-4-5-20251001`, max_tokens 512)

## 정적 데이터 (`data/`)
- `data/book_years_approx/books.json` — `/books` 추정연도 오버레이(백엔드가 직접 읽음)
- `data/book_context/`, `data/character_traits/`, `data/names_ko/` — 주입 스크립트 입력

## 설정 파일
- `docker-compose.yml` — 3 서비스 정의(neo4j/api/nginx), 볼륨, 환경변수
- `backend/Dockerfile` — API 이미지(python:3.12-slim)
- `nginx/nginx.conf` — 정적 서빙 + `/api/` 프록시 + 캐시 헤더
- `deploy.sh` — 빌드/재시작/한글주입 배포 스크립트
- `.github/workflows/deploy.yml` — self-hosted runner CI(main push → deploy.sh)
- `.env` / `.env.example` — `NEO4J_PASSWORD`(값 미기재)
- `frontend/.env.production` — `VITE_API_URL=/api`
- `frontend/eslint.config.js`, `frontend/vite.config.js`

## 실행 방법(요약)
- 로컬 프론트: `cd frontend && npm install && npm run dev`
- 전체 스택: `docker compose -p biblemap up -d --build`(`NEO4J_PASSWORD` 필요)
- 백엔드는 hot-reload 아님 — 변경 후 `docker compose up -d --build api` 재빌드 필요
- 외부 포트: nginx `8080:80`(공개), neo4j는 `127.0.0.1`로만 바인딩(7474/7687)
