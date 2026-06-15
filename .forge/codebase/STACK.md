---
last_mapped_commit: 22a678c36e40548a3d00ccf9205862505a59d9cb
mapped: 2026-06-16
---

# STACK

BibleMap의 기술 스택, 런타임, 빌드 도구, 설정, 실행 방법을 정리한다. 도메인 용어는 다루지 않는다(그건 CONTEXT.md 영역).

## 구성 개요

3개 컴포넌트로 나뉘며 모두 `docker-compose.yml`로 묶인다.

- **frontend** — React SPA. 빌드 산출물(`frontend/dist/`)을 nginx가 정적 서빙.
- **backend** — FastAPI(`api` 서비스). uvicorn으로 구동.
- **neo4j** — 그래프 DB(`neo4j` 서비스). 데이터는 named volume에 영속.
- **nginx** — 정적 파일 서빙 + `/api/` 리버스 프록시(`nginx` 서비스).

## Frontend

- 언어/프레임워크: **React 19** (`react` ^19.2.6, `react-dom` ^19.2.6) — `frontend/package.json`.
- 빌드 도구: **Vite 8** (`vite` ^8.0.12), 플러그인 `@vitejs/plugin-react` ^6.0.1 — `frontend/vite.config.js` (플러그인 한 줄 외 추가 설정 없음).
- 모듈 타입: ESM (`"type": "module"`).
- 주요 의존성:
  - `maplibre-gl` ^5.24.0 — 지도 렌더링. `frontend/src/MapView.jsx`에서 사용.
  - `lucide-react` ^1.17.0 — 아이콘(`frontend/src/App.jsx`에서 Map/Clock/Search/X).
- 린트: **ESLint 10** (`eslint` ^10.3.0) + `@eslint/js`, `eslint-plugin-react-hooks` ^7.1.1, `eslint-plugin-react-refresh` — 설정은 `frontend/eslint.config.js`.
- npm 스크립트(`frontend/package.json`): `dev`(vite 개발 서버), `build`(vite build), `lint`(eslint .), `preview`.
- 진입점: `frontend/index.html` → `frontend/src/main.jsx` → `frontend/src/App.jsx`.
- 소스 구조: `frontend/src/` 에 `App.jsx`, `MapView.jsx`, `TimelineView.jsx`, `SidePanel.jsx`, `api.js`, `theme.js`, `convexHull.js`, CSS 파일.
- 색·라벨 팔레트는 `frontend/src/theme.js`로 단일화(`TYPE_COLOR`, `TYPE_KO`, `TYPE_ORDER`)되어 App/SidePanel/MapView가 import.

## Backend

- 언어/런타임: **Python 3.12** (`backend/Dockerfile` — `python:3.12-slim`).
- 프레임워크: **FastAPI** 0.136.3 — `backend/requirements.txt`.
- ASGI 서버: **uvicorn** 0.49.0. 컨테이너 실행 커맨드 `uvicorn app.main:app --host 0.0.0.0 --port 8000`.
- DB 드라이버: **neo4j** 6.2.0 (Python Bolt 드라이버).
- 앱 진입점: `backend/app/main.py` — `FastAPI` 인스턴스 생성, CORS 미들웨어(`allow_origins=["*"]`, `allow_methods=["GET"]`), 라우터 4개 포함, `lifespan`에서 5개 라벨(Person/Place/Event/PeopleGroup/Book)의 `theographic_id` 인덱스를 멱등 생성.
- 라우트: `backend/app/routes/nodes.py`, `events.py`, `search.py`, `books.py`. DB 드라이버는 `backend/app/db.py`의 싱글턴(`get_driver()`).
- 데이터 적재/주입 스크립트: `backend/scripts/` — `load_theographic.py`, `load_books.py`, `inject_ko_names.py`, `inject_book_context.py`, `inject_person_traits.py`, `generate_book_context.py`, `generate_person_traits.py`. (적재·주입 출처와 동작은 INTEGRATIONS.md 참조.)

## 컨테이너 / 실행

`docker-compose.yml` 서비스:

| 서비스 | 이미지/빌드 | 포트(호스트→컨테이너) | 비고 |
|--------|-------------|----------------------|------|
| `neo4j` | `neo4j:5` | `127.0.0.1:7474→7474`(HTTP 브라우저), `127.0.0.1:7687→7687`(Bolt) | `NEO4J_AUTH=neo4j/${NEO4J_PASSWORD}`, named volume `neo4j_data:/data`, `restart: unless-stopped`. 포트는 루프백 바인딩(외부 비노출). |
| `api` | `./backend` 빌드 | (compose 내부 8000, 외부 미노출) | env `NEO4J_URI=bolt://neo4j:7687`, `NEO4J_USER=neo4j`, `NEO4J_PASSWORD`. `./data:/app/data` 마운트. `depends_on: neo4j`. |
| `nginx` | `nginx:alpine` | `8080→80` | `./frontend/dist:/usr/share/nginx/html:ro`, `./nginx/nginx.conf:/etc/nginx/nginx.conf:ro`. `depends_on: api`. |

- 외부에 노출되는 단일 진입점은 **`:8080`** (nginx). API와 정적 자산 모두 여기로 들어온다.
- nginx 설정(`nginx/nginx.conf`): `/api/` → `http://api:8000/` 프록시, `index.html`은 no-cache, 정적 자산(js/css/이미지/폰트)은 1년 immutable 캐시, SPA fallback(`try_files $uri /index.html`).
- API 컨테이너는 hot-reload가 아니다(빌드 이미지로 동작) — 백엔드 코드 변경 시 `docker compose ... build api` 후 재기동 필요.

## 환경 변수 / 설정

- `NEO4J_PASSWORD` — **필수**. `docker-compose.yml`에서 `${NEO4J_PASSWORD:?...}`로 강제(미설정 시 compose 실패). `.env`(gitignore됨)에서 로드. 예시는 `.env.example`. `NEO4J_AUTH`는 compose가 `neo4j/<password>`로 자동 파생.
- `NEO4J_URI`, `NEO4J_USER` — compose가 api 서비스에 주입(`bolt://neo4j:7687`, `neo4j`). `backend/app/db.py`의 기본값은 `bolt://localhost:7687` / `neo4j`(로컬 직접 실행용).
- `VITE_API_URL` — 프론트 API 베이스. 프로덕션 빌드는 `frontend/.env.production`에서 `=/api`(nginx 프록시 경유). 미설정 시 코드 기본값 `http://localhost:8000`. `frontend/src/api.js`, `App.jsx`, `MapView.jsx`, `TimelineView.jsx`, `SidePanel.jsx`가 `import.meta.env.VITE_API_URL`로 읽음.
- `ANTHROPIC_API_KEY` — `backend/scripts/generate_*.py`(콘텐츠 생성 스크립트) 실행 시에만 필요(런타임 앱에는 불필요). (상세는 INTEGRATIONS.md.)
- `DATA_DIR` — `backend/app/routes/books.py`가 연도 추정 오버레이를 읽는 디렉터리. 기본 `/app/data`.
- `.env`는 gitignore(`.gitignore`). 영속 forge 문서를 제외한 `.forge/` 휘발 상태도 gitignore.

## 빌드 / 배포

- 배포 스크립트: `deploy.sh` — (1) `frontend`에서 `npm install` + `npm run build`, (2) `docker compose -p biblemap build api`, (3) `docker compose -p biblemap up -d api nginx`, (4) `inject_ko_names.py`를 Neo4j 준비될 때까지 최대 15회 재시도하며 한글 이름 주입. lock 파일(`/tmp/biblemap-deploy.lock`)로 중복 실행 방지, 로그는 `~/Library/Logs/com.biblemap.deploy.log`.
- CI/CD: `.github/workflows/deploy.yml` — `main` push 시 `self-hosted` 러너에서 `git reset --hard origin/main` 후 `bash deploy.sh`.
- 로컬 개발 실행 설정: `.claude/launch.json` — frontend 개발 서버(`npm --prefix frontend run dev`, port 5173).

## 데이터 파일

- `data/` 디렉터리(컨테이너에 `/app/data`로 마운트): `names_ko/`(books/people/places/events/groups.json), `book_years_approx/books.json`(연도 추정 오버레이, `books.py`가 런타임 로드), `book_context/books.json`, `character_traits/people.json`.
