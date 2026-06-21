---
last_mapped_commit: 70a9781e6523a396ad856f980b5499b1cc814d7a
mapped: 2026-06-21
---

# STACK.md — BibleMap 기술 스택

## 언어 및 런타임

| 계층 | 언어 | 런타임 |
|------|------|--------|
| 프론트엔드 | JavaScript (ESM) | Node.js (빌드타임) |
| 백엔드 | Python 3.12 | CPython 3.12-slim |
| 데이터 파이프라인 스크립트 | Python 3.12 | 호스트 python3 (오프라인 실행) |
| 컨테이너 오케스트레이션 | YAML | Docker Compose v2 |

---

## 프론트엔드

**프레임워크 및 주요 라이브러리** (`frontend/package.json`)

- **React 19.2.6** + **react-dom 19.2.6** — UI 컴포넌트 트리
- **MapLibre GL 5.24.0** — WebGL 기반 벡터 지도 렌더링
- **Lucide React 1.17.0** — 아이콘

**빌드 도구**

- **Vite 8.0.12** — 번들러 / 개발 서버
  - 설정 파일: `frontend/vite.config.js`
  - 플러그인: `@vitejs/plugin-react 6.0.1`
  - 코드 분할(`manualChunks`): `maplibre-gl` → `maplibre` 청크, 나머지 `node_modules` → `vendor` 청크

**린트** (`frontend/package.json` devDependencies)

- `eslint 10.3.0`, `@eslint/js 10.0.1`, `eslint-plugin-react-hooks 7.1.1`, `eslint-plugin-react-refresh 0.5.2`, `globals 17.6.0`
- 스크립트: `npm run lint` → `eslint .`

**npm 스크립트** (`frontend/package.json`): `dev` (vite), `build` (vite build), `lint`, `preview`

**주요 소스 파일**

| 파일 | 역할 |
|------|------|
| `frontend/src/main.jsx` | React 앱 진입점 |
| `frontend/src/App.jsx` | 탭(지도/타임라인/성경개요), 검색바, 반응형 레이아웃 |
| `frontend/src/MapView.jsx` | MapLibre GL 지도, 클러스터링, 스파이더파이, 라벨 배치 |
| `frontend/src/SidePanel.jsx` | 노드 상세 패널 |
| `frontend/src/TimelineView.jsx` | 사건 타임라인, 구절 인라인 뷰 |
| `frontend/src/BibleOverviewView.jsx` | 권별 개요 카드 그리드 |
| `frontend/src/api.js` | API 클라이언트 (`API_BASE` + `apiGet` 단일 헬퍼) |
| `frontend/src/theme.js` | 노드 타입 색상·한글명 팔레트 |
| `frontend/src/constants.js` | 반응형 상수 (`MOBILE_BREAKPOINT=768`, `SHEET_VH=55`) |
| `frontend/src/useNodeSelection.js` | 선택 노드 상태 + 히스토리 훅 |
| `frontend/src/useSearch.js` | 250ms 디바운스 검색 훅 |
| `frontend/src/convexHull.js` | Graham scan 볼록 껍질 순수 함수 |
| `frontend/src/VerseLangTabs.jsx` | 한국어/영어 전환 세그먼트 |
| `frontend/src/Spinner.jsx` | 로딩 스피너 |

---

## 백엔드

**프레임워크 및 주요 라이브러리** (`backend/requirements.txt`)

- **FastAPI 0.136.3** — REST API 서버 (비동기)
- **neo4j 6.2.0** — Neo4j Python 드라이버 (Bolt 프로토콜)
- **uvicorn 0.49.0** — ASGI 서버

> 데이터 파이프라인 스크립트가 쓰는 `anthropic` 패키지는 `requirements.txt`에 **미포함** — 오프라인 스크립트 실행 환경에서만 설치한다.

**주요 소스 파일**

| 파일 | 역할 |
|------|------|
| `backend/app/main.py` | FastAPI 앱 생성, CORS(GET 전용), 라우터 등록, lifespan(인덱스 생성) |
| `backend/app/db.py` | Neo4j 드라이버 싱글턴(`get_driver()`), 환경변수 연결 |
| `backend/app/overlays.py` | JSON 파일 오버레이 로더 (`lru_cache`, `DATA_DIR` → repo `data/` 폴백) |
| `backend/app/routes/nodes.py` | 노드 상세, 이웃, 장소, Person 사건 ID 엔드포인트 |
| `backend/app/routes/events.py` | 타임라인 사건 목록, 사건 구절 엔드포인트 |
| `backend/app/routes/search.py` | 이름 검색 엔드포인트 |
| `backend/app/routes/books.py` | 권 개요, 타임라인 배치용 엔드포인트 |

**API 엔드포인트 요약** (모두 GET)

| 경로 | 정의 위치 | 설명 |
|------|-----------|------|
| `/node/{id}` | `routes/nodes.py` | 노드 상세 + 이웃(`NODE_NEIGHBOR_LIMIT=50`), Book이면 topPersons/topEvents 추가 |
| `/node/{id}/neighbors/grouped` | `routes/nodes.py` | 타입별 이웃 그룹핑(`MAX_NEIGHBORS_PER_TYPE=30`) |
| `/node/{id}/places` | `routes/nodes.py` | 관련 장소(위경도) — 레이블별 쿼리 분기 |
| `/person/{id}/event-ids` | `routes/nodes.py` | Person 사건 ID 목록 |
| `/events` | `routes/events.py` | 타임라인 사건 전체 (lru_cache, `Cache-Control: max-age=300`) |
| `/event/{id}/verses` | `routes/events.py` | 사건 근거 구절 (`event_verses` 오버레이) |
| `/search?q=` | `routes/search.py` | 이름 검색 (`SEARCH_LIMIT=20`) |
| `/books-overview` | `routes/books.py` | 권별 개요 (`Cache-Control: no-store`) |
| `/books` | `routes/books.py` | 타임라인용 권 목록 (`approx_years`·`book_events_raw` 오버레이 머지) |

---

## 데이터베이스

- **Neo4j 5** (Docker 이미지 `neo4j:5`)
- 프로토콜: Bolt (`bolt://neo4j:7687`, compose 내부망)
- 인증: `NEO4J_AUTH=neo4j/${NEO4J_PASSWORD}` 환경변수 (compose가 비밀번호로 파생)
- 노드 레이블: `Person`, `Place`, `Event`, `PeopleGroup`, `Book`
- 인덱스 5개: `{label}_tid` (`theographic_id` 기준, `backend/app/main.py` lifespan에서 앱 기동 시 자동 생성)
- 관계: `HAS_PARTICIPANT`, `OCCURS_AT`, `MEMBER_OF`, `PARENT_OF`, `CHILD_OF`, `SIBLING_OF`, `PARTNER_OF`, `PART_OF`, `CONTAINS_BOOK`
- 포트 바인딩: `127.0.0.1:7474` (HTTP), `127.0.0.1:7687` (Bolt) — 로컬호스트 전용

---

## 컨테이너화

**Docker Compose**: `docker-compose.yml`

| 서비스 | 이미지 / 빌드 | 퍼블릭 포트 |
|--------|--------------|-------------|
| `neo4j` | `neo4j:5` | 127.0.0.1:7474, 127.0.0.1:7687 |
| `api` | `./backend` (Dockerfile) | 내부망만 (8000, 미노출) |
| `nginx` | `nginx:alpine` | 0.0.0.0:8080 → 80 |

**백엔드 Dockerfile**: `backend/Dockerfile`
- 베이스: `python:3.12-slim`
- `pip install --no-cache-dir -r requirements.txt` → `COPY app/` → `uvicorn app.main:app --host 0.0.0.0 --port 8000`

**Nginx 설정**: `nginx/nginx.conf`
- `/api/` → `proxy_pass http://api:8000/` (FastAPI 역방향 프록시)
- `*.js|css|png|jpg|…|woff2?` → `Cache-Control: public, max-age=31536000, immutable`
- `/index.html` → `no-cache, no-store, must-revalidate`
- SPA fallback: `try_files $uri /index.html`

**볼륨 마운트** (`docker-compose.yml`)
- `./frontend/dist:/usr/share/nginx/html:ro` — 정적 프론트 서빙 (HMR 아님, 빌드 산출물 마운트)
- `./data:/app/data` — JSON 오버레이 파일 (api 서비스)
- `./nginx/nginx.conf:/etc/nginx/nginx.conf:ro`
- 명명 볼륨 `neo4j_data:/data`

---

## 데이터 파이프라인 (오프라인 적재/생성)

런타임 외부에서 호스트 `python3`로 실행하는 빌드타임 스크립트 모음(`backend/scripts/`). Neo4j 적재(load/inject)와 데이터 생성(generate)으로 나뉜다.

**원본 적재 (Theographic → Neo4j)**

| 스크립트 | 역할 |
|----------|------|
| `load_theographic.py` | people/places/events/peopleGroups 노드 + 관계 적재 (raw github에서 직접 fetch) |
| `load_books.py` | Book 노드 + `CONTAINS_BOOK` 관계 |
| `load_person_events.py` | `data/person_events/*.json` → authored Event 노드 + 관계 |
| `load_verse_events.py` | `data/verse_events/events.json` → Event 노드 + `CONTAINS_BOOK` |
| `load_authored_events.py` | `data/authored_events/events.json` → authored Event 노드 |

**Neo4j 속성 주입 (data/ JSON → 노드 SET)**

| 스크립트 | 대상 | 입력 |
|----------|------|------|
| `inject_ko_names.py` | Person·Place 한글명 | `data/names_ko/` |
| `inject_book_context.py` | Book background·themes·keyVerse 등 | `data/book_context/books.json` |
| `inject_person_traits.py` | Person `traits` | `data/character_traits/people.json` |
| `inject_place_context.py` | **(신규)** Place `background`·`keyVerse`·`keyVerseTextKo/En` | `data/place_context/places.json` |
| `enrich_place_coords.py` | Place 좌표 멱등 적재 | `data/place_coords/places.json` |

**콘텐츠 생성 (외부 API 호출 — Anthropic / getbible)**

| 스크립트 | 출력 |
|----------|------|
| `generate_book_context.py`, `generate_book_context_enrich.py` | `data/book_context/books.json` |
| `generate_book_events.py` | `data/book_events/books.json` (추정책↔사건 오버레이) |
| `generate_event_verses.py` | `data/event_verses/events.json` |
| `generate_verse_events.py` | `data/verse_events/events.json` |
| `generate_person_traits.py` | `data/character_traits/people.json` |
| `generate_person_event_verses.py` | `data/person_events/*.json` + `data/event_verses/events.json` 머지 |
| `generate_approx_book_verses.py` | 추정 연대 구절 |
| `generate_verse_text.py` | 4개 생성 데이터(event_verses·book_context·character_traits·**place_context**)에 getbible 본문 인라인 굽기 |

자세한 외부 연동은 `INTEGRATIONS.md` 참조.

---

## 배포 파이프라인

**배포 스크립트**: `deploy.sh` (lock 파일 + macOS 키체인 우회 + `.env` 로드)

1. `[1/3] cd frontend && npm install && npm run build` → `frontend/dist/` 생성
2. `[2/3] docker compose -p biblemap build api`
3. `[3/4] docker compose -p biblemap up -d api nginx`
4. `[4/4] python3 backend/scripts/inject_ko_names.py` (Neo4j 준비 대기, 15회 재시도, 실패 시 배포 중단)

> 그 외 load/inject/generate 스크립트는 `deploy.sh`에 포함되지 않으며 수동/오프라인으로 실행한다.

---

## 환경 설정

| 파일 | 범위 | 주요 변수 |
|------|------|-----------|
| `.env` | 로컬 개발 (git 추적) | `NEO4J_PASSWORD` |
| `.env.example` | 템플릿 | `NEO4J_PASSWORD=your-password-here` |
| `frontend/.env.production` | 프론트 빌드타임 | `VITE_API_URL=/api` |

**백엔드 환경변수** (`backend/app/db.py`, `backend/app/overlays.py`)

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `NEO4J_URI` | `bolt://localhost:7687` | Neo4j Bolt 연결 |
| `NEO4J_USER` | `neo4j` | Neo4j 사용자명 |
| `NEO4J_PASSWORD` | — | Neo4j 비밀번호 (없으면 `get_driver()` 가 RuntimeError) |
| `DATA_DIR` | `/app/data` | JSON 오버레이 파일 루트 (없으면 repo `data/` 폴백) |

**데이터 스크립트 환경변수**

| 변수 | 필요 스크립트 | 설명 |
|------|--------------|------|
| `NEO4J_URI`/`NEO4J_USER`/`NEO4J_PASSWORD` | load_*/inject_* | Neo4j 연결 |
| `ANTHROPIC_API_KEY` | generate_*(Anthropic 호출분) | Claude API 키 |

**프론트엔드 환경변수** (`frontend/src/api.js`)

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `VITE_API_URL` | `http://localhost:8000` | API 베이스 URL (프로덕션 빌드는 `/api`) |
