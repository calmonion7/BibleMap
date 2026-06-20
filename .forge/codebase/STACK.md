---
last_mapped_commit: ff728ccaffbb9b4e38f1f8f32859a50d3555b515
mapped: 2026-06-20
---

# 기술 스택

## 프론트엔드

- **언어**: JavaScript (ESM, JSX)
- **런타임**: 브라우저
- **프레임워크**: React 19.2.6
- **빌드 도구**: Vite 8.0.12 (`frontend/vite.config.js`)
- **주요 의존성**
  - `maplibre-gl` 5.24.0 — 지도 렌더링
  - `lucide-react` 1.17.0 — 아이콘
  - `react-dom` 19.2.6
- **빌드 설정**
  - `frontend/.env.production`: `VITE_API_URL=/api` (빌드타임 주입)
  - Rollup `manualChunks`: maplibre-gl → `maplibre` 청크, 나머지 npm → `vendor` 청크
  - 출력 디렉터리: `frontend/dist/`
- **린터**: ESLint 10.3.0 + `eslint-plugin-react-hooks` 7.1.1 + `eslint-plugin-react-refresh` 0.5.2
- **핵심 소스 파일**
  - `frontend/src/App.jsx` — 최상위 뷰 라우팅 및 검색 UI
  - `frontend/src/MapView.jsx` — MapLibre GL 지도 + 이벤트 링 애니메이션
  - `frontend/src/TimelineView.jsx` — 시대순 사건 목록
  - `frontend/src/BibleOverviewView.jsx` — 성경 개요 뷰
  - `frontend/src/SidePanel.jsx` — 노드 상세 패널
  - `frontend/src/api.js` — 단일 API 클라이언트 (`API_BASE`, `apiGet`)
  - `frontend/src/useNodeSelection.js`, `frontend/src/useSearch.js` — 커스텀 훅
  - `frontend/src/convexHull.js` — 볼록 껍질 계산 (활동 반경 폴리곤)
  - `frontend/src/VerseLangTabs.jsx`, `frontend/src/Spinner.jsx`, `frontend/src/theme.js`

## 백엔드

- **언어**: Python 3.12
- **런타임**: CPython 3.12-slim (Docker)
- **프레임워크**: FastAPI 0.136.3
- **ASGI 서버**: Uvicorn 0.49.0
- **주요 의존성** (`backend/requirements.txt`)
  - `neo4j` 6.2.0 — Neo4j Python 드라이버 (Bolt 프로토콜)
- **핵심 소스 파일**
  - `backend/app/main.py` — FastAPI 앱 초기화, CORS, lifespan 인덱스 생성
  - `backend/app/db.py` — Neo4j 드라이버 싱글턴 (`get_driver`)
  - `backend/app/overlays.py` — JSON 파일 오버레이 로더 (`lru_cache`)
  - `backend/app/routes/nodes.py` — `/node/*`, `/person/*` 엔드포인트
  - `backend/app/routes/events.py` — `/events`, `/event/{id}/verses` 엔드포인트
  - `backend/app/routes/search.py` — `/search` 엔드포인트
  - `backend/app/routes/books.py` — `/books`, `/books-overview` 엔드포인트
- **CORS**: `allow_origins=["*"]`, `allow_methods=["GET"]`, `allow_credentials=False`
- **포트**: 컨테이너 내부 8000

## 데이터베이스

- **Neo4j** 5 (Docker 공식 이미지 `neo4j:5`)
- Bolt 프로토콜, 포트 7687 (로컬호스트 바인드)
- HTTP 콘솔 포트 7474 (로컬호스트 바인드)
- 볼륨: `neo4j_data` (named volume)
- 자동 인덱스: `Person`, `Place`, `Event`, `PeopleGroup`, `Book` 노드의 `theographic_id` 필드

## 인프라 / 배포

- **컨테이너**: Docker Compose (`docker-compose.yml`)
  - 서비스: `neo4j`, `api`, `nginx`
  - 프로젝트명: `biblemap` (`docker compose -p biblemap`)
- **리버스 프록시**: nginx:alpine — 포트 8080:80
  - `/api/` → `http://api:8000/` 프록시 (`nginx/nginx.conf`)
  - `frontend/dist` → `/usr/share/nginx/html` (read-only)
  - SPA fallback: `try_files $uri /index.html`
  - 정적 자산 캐시: `max-age=31536000, immutable`; `index.html`: `no-cache`
- **배포 스크립트**: `deploy.sh`
  - 순서: npm 빌드 → API 이미지 빌드 → 컨테이너 재시작 → `inject_ko_names.py` 실행 (최대 15회 재시도)
  - 환경변수: `.env` 파일에서 `NEO4J_PASSWORD` 로드
  - 로그: `/Users/calmonion/Library/Logs/com.biblemap.deploy.log`
  - 락 파일: `/tmp/biblemap-deploy.lock`

## 데이터 파이프라인 스크립트 (`backend/scripts/`)

- Python 단독 실행 스크립트 (FastAPI 앱과 별도)
- `load_theographic.py` — theographic-bible-metadata GitHub raw JSON 다운로드 후 Neo4j 적재
- `load_books.py`, `load_person_events.py`, `load_verse_events.py`, `load_authored_events.py`
- `inject_ko_names.py` — `data/names_ko/*.json`을 Neo4j 노드에 주입 (배포 후 자동 실행)
- `inject_book_context.py`, `inject_person_traits.py`
- `enrich_place_coords.py` — 장소 좌표 보강
- `generate_*.py` 시리즈 — 오버레이 JSON 생성 (approx_book_verses, book_context, book_events, event_verses, person_traits, verse_events, verse_text)

## 오버레이 데이터 (`data/`)

- `data/names_ko/` — 한글 이름 매핑 (people, places, events, groups, books)
- `data/person_events/` — 인물별 사건 JSON (아브라함·다윗·모세 등 13인)
- `data/book_events/books.json` — 책↔사건 연결
- `data/book_years_approx/books.json` — 집필 추정 연도
- `data/event_verses/events.json` — 사건↔구절 매핑
- `data/verse_events/events.json`, `data/authored_events/events.json`
- `data/place_coords/places.json`, `data/character_traits/people.json`, `data/book_context/books.json`
