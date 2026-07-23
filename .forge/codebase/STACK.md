---
last_mapped_commit: 70f5fc64daa7b3c71f2773a4357ad68bba9ae7a5
mapped: 2026-07-24
---

# STACK

BibleMap의 언어·런타임·프레임워크·의존성·빌드/설정 사실 정리. 도메인 용어 정의는 여기 없음(그건 `CONTEXT.md`). 파일별 디렉터리 구조는 `.forge/codebase/STRUCTURE.md` 참고.

전체 구성: 백엔드 FastAPI + Neo4j Python 드라이버, 프론트 React + Vite + maplibre-gl, docker-compose 3서비스 스택(neo4j + api + nginx), self-hosted 러너 배포.

## 백엔드

- 언어/런타임: Python. 컨테이너 베이스는 `python:3.12-slim`(`backend/Dockerfile`). 다만 배포 스크립트가 호스트에서 직접 실행하는 주입 스크립트(`inject_ko_names.py` 등)는 이 머신의 host python3(`python3 --version` = 3.14.5)로 돈다 — 컨테이너 밖 실행 경로.
- 의존성(`backend/requirements.txt`, 핀 고정):
  - `fastapi==0.136.3`
  - `neo4j==6.2.0` (공식 Neo4j Python 드라이버)
  - `uvicorn==0.49.0` (ASGI 서버)
- 앱 엔트리: `backend/app/main.py` — `FastAPI(lifespan=...)`.
  - `lifespan`에서 Neo4j 인덱스 5종(`Person`/`Place`/`Event`/`PeopleGroup`/`Book`의 `theographic_id`) `CREATE INDEX ... IF NOT EXISTS` 보장. 실패해도 인덱스 없이 계속 진행.
  - `CORSMiddleware`: `allow_origins=["*"]`, `allow_credentials=False`, `allow_methods=["GET"]` — 읽기 전용 공개 API.
  - 라우터 13개 include: `nodes, events, search, books, persons, journey, places, tours, family, words, verses, reliance, stats`.
  - 로깅: `_configure_logging()`를 라우터 import 전에 1회 호출. `neo4j`/`urllib3`/`asyncio`는 WARNING 승격, `uvicorn`/`uvicorn.access`는 `propagate=False`(root 중복 emit 차단).
- Neo4j 드라이버: `backend/app/db.py` — 모듈 전역 싱글턴 `get_driver()`. `NEO4J_URI`(기본 `bolt://localhost:7687`), `NEO4J_USER`(기본 `neo4j`), `NEO4J_PASSWORD`(필수, 없으면 `RuntimeError`) 환경변수 사용.
- 오버레이 로더: `backend/app/overlays.py` — `data/` 하위 JSON을 `functools.lru_cache(maxsize=1)`로 1회 로드. `DATA_DIR`(기본 `/app/data`) → 레포 `data/`(`_REPO_DATA_DIR`) 순으로 파일/디렉터리 해석, 없으면 빈 데이터 폴백. 로더 함수: `book_events_raw`, `event_verses`, `bible_verses`, `word_distribution`, `books_ko`, `chapter_summaries`, `chapter_sections`, `quotations`, `messianic_prophecies`, `covenants`, `parables_miracles`, `place_coords`, `topical_verses`, `verse_persons`.
- 라우트 모듈: `backend/app/routes/*.py` 14개(`nodes, events, search, books, persons, journey, places, tours, family, words, verses, reliance, stats` + `__init__`). `@router.get` 데코레이터 기준 약 30개 GET 엔드포인트(POST 없음). 집계형 응답은 `lru_cache`로 캐시(예: `stats.py`의 `_compute_stats`, `maxsize=1`) → 데이터 변경 시 API 재시작 필요.
- 데이터/스크립트: `backend/scripts/*.py` (약 45개). Neo4j 적재(`load_*.py`), 오버레이 생성(`generate_*.py`), 주입(`inject_*.py`), 검증(`validate_*.py`), 빌드(`build_*.py`). 앱은 이 스크립트를 import하지 않음(빌드타임/운영 전용).

## 프론트엔드

- 언어/런타임: JavaScript(ESM, `"type": "module"`), React JSX. 호스트 Node `v24.15.0`. `frontend/package.json`에 engines 핀 없음.
- 런타임 의존성(`frontend/package.json`):
  - `react@^19.2.6`, `react-dom@^19.2.6`
  - `maplibre-gl@^5.24.0` (지도)
  - `lucide-react@^1.17.0` (아이콘)
- 개발/빌드 의존성:
  - `vite@^8.0.12`, `@vitejs/plugin-react@^6.0.1`
  - `eslint@^10.3.0`, `@eslint/js@^10.0.1`, `eslint-plugin-react-hooks@^7.1.1`, `eslint-plugin-react-refresh@^0.5.2`, `globals@^17.6.0`
  - `@types/react`, `@types/react-dom`(타입만; TS 빌드는 아님)
- 스크립트(`frontend/package.json`): `dev`(vite), `build`(vite build), `lint`(eslint .), `preview`(vite preview).
- Vite 설정(`frontend/vite.config.js`):
  - `plugins: [react()]`
  - `define.__BUILD_ID__ = Date.now()` 문자열 — 빌드마다 바뀌는 식별자. `frontend/src/api.js`가 모든 API 요청에 `?v=<BUILD_ID>`로 실어 배포 직후 캐시 무력화.
  - `build.rollupOptions.output.manualChunks`: `node_modules` 중 `maplibre-gl`은 `maplibre` 청크, 나머지는 `vendor` 청크로 분리.
- ESLint(`frontend/eslint.config.js`, flat config): `js.recommended` + react-hooks + react-refresh(vite). `dist` 무시. `globals.browser` + `__BUILD_ID__: 'readonly'`, JSX 파서 옵션.
- 엔트리: `frontend/index.html`(`#root`, `/src/main.jsx` 모듈 스크립트) → `frontend/src/main.jsx`. 최상위 뷰 컴포넌트는 `frontend/src/App.jsx` 및 `frontend/src/*.jsx` 다수(MapView, TimelineView, PersonHub, StatsView, IntroView 등).
- API 클라이언트: `frontend/src/api.js` — 단일 `apiGet(path, {signal})`. `API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'`.
- 프론트 환경변수: `frontend/.env.production` → `VITE_API_URL=/api`(프로덕션은 nginx 프록시 경유). 개발 기본은 `http://localhost:8000` 직접.

## Docker / 배포 스택

- `docker-compose.yml` — 3 서비스:
  - `neo4j`: 이미지 `neo4j:5`. 포트 `127.0.0.1:7474`(HTTP), `127.0.0.1:7687`(Bolt) — 루프백 바인딩. 볼륨 `neo4j_data:/data`. 환경 `NEO4J_AUTH=neo4j/${NEO4J_PASSWORD}`(compose가 파생). `restart: unless-stopped`.
  - `api`: `build: ./backend`(`backend/Dockerfile`). 환경 `NEO4J_URI=bolt://neo4j:7687`, `NEO4J_USER=neo4j`, `NEO4J_PASSWORD=${NEO4J_PASSWORD}`. 볼륨 `./data:/app/data`(데이터 = 볼륨 마운트, 이미지 미포함). `depends_on: neo4j`. 컨테이너 내부 uvicorn `0.0.0.0:8000`(호스트 미노출).
  - `nginx`: 이미지 `nginx:alpine`. 포트 `8080:80`. 볼륨 `./frontend/dist:/usr/share/nginx/html:ro`, `./nginx/nginx.conf:/etc/nginx/nginx.conf:ro`(읽기 전용 마운트). `depends_on: api`.
  - 명명 볼륨: `neo4j_data`. compose 프로젝트명은 `deploy.sh`에서 `-p biblemap`으로 고정.
- `backend/Dockerfile`: `python:3.12-slim` → `requirements.txt` 설치 → `app/` 복사 → `CMD uvicorn app.main:app --host 0.0.0.0 --port 8000`.
- 환경변수(루트 `.env`, `.env.example`): `NEO4J_PASSWORD`만 필수. compose가 `NEO4J_AUTH`를 `neo4j/<password>`로 파생. 미설정 시 compose가 `:?` 확장으로 실패.
- 프론트 정적 자산: `frontend/dist`는 HMR이 아니라 nginx가 마운트로 서빙 → 로컬 검증 전 `cd frontend && npm run build` 필요.

## 배포 파이프라인

- `.github/workflows/deploy.yml`: `push`(branches `main`) → `runs-on: self-hosted`. 러너에서 `cd /Users/calmonion/Project/BibleMap && git fetch origin && git reset --hard origin/main && bash deploy.sh`.
- `deploy.sh`(레포 루트):
  - `/tmp/biblemap-deploy.lock` 락으로 중복 배포 차단, `EXIT` 트랩으로 해제. 로그 `~/Library/Logs/com.biblemap.deploy.log`.
  - macOS 키체인 우회용 임시 `DOCKER_CONFIG`(빈 `auths`)에 `~/.docker/cli-plugins` 심링크(compose 플러그인 인식용).
  - 루트 `.env`를 `set -a`로 로드(호스트 주입 스크립트가 동일 비번 사용).
  - [1] `frontend`에서 `npm install --silent && npm run build --silent`.
  - [2] `docker compose -p biblemap build api`.
  - [3] `docker compose -p biblemap up -d api nginx`.
  - [4] `python3 backend/scripts/inject_ko_names.py` 최대 15회 재시도(Neo4j 준비 대기), 실패 시 배포 중단(`exit 1`).
  - 주의: `deploy.sh`는 `load_*` 적재 스크립트를 실행하지 않음 — Neo4j 데이터 적재는 별도 수동 실행.

## 세션 중 신규 추가(작업 트리, 미커밋 — 검증됨)

- 라우트: `backend/app/routes/stats.py`(신규, `main.py`에서 include됨). `GET /stats` — 그래프 집계(headline 총계·최다 등장 인물·최장 여정·시대별 사건 분포·책별 장수), `lru_cache(maxsize=1)` + `Cache-Control: max-age=300`.
- 런타임 오버레이 데이터셋(모두 `git status`에서 untracked):
  - `data/covenants/covenants.json`
  - `data/messianic_prophecies/prophecies.json`
  - `data/jesus_parables_miracles/index.json`
  - `data/topical_verses/topics.json`
  - 각 오버레이는 `backend/app/overlays.py`의 로더(`covenants`/`messianic_prophecies`/`parables_miracles`/`topical_verses`)로 로드되어 `backend/app/routes/events.py`가 서빙(엔드포인트는 `INTEGRATIONS.md` 참조).
