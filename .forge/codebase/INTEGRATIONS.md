---
last_mapped_commit: 6f2cfc1bf163d7327bd86773676223624fa53ff2
mapped: 2026-06-18
---

# INTEGRATIONS.md — BibleMap 외부 연동

## 데이터베이스

### Neo4j 5 (그래프 DB)

- **타입**: 그래프 데이터베이스 (Bolt 프로토콜)
- **연결 패턴**: `backend/app/db.py` — 모듈 수준 싱글턴 `_driver`. 첫 `get_driver()` 호출 시 초기화 후 재사용
- **연결 파라미터** (환경변수에서 읽음):
  - `NEO4J_URI` — 기본값 `bolt://localhost:7687`. docker-compose에서 `bolt://neo4j:7687`으로 오버라이드
  - `NEO4J_USER` — 기본값 `neo4j`
  - `NEO4J_PASSWORD` — 필수값. 미설정 시 `RuntimeError`
- **인덱스 자동 생성** (`backend/app/main.py` lifespan): 앱 기동 시 `Person`, `Place`, `Event`, `PeopleGroup`, `Book` 각 레이블의 `theographic_id` 속성에 인덱스 생성
- **Docker 볼륨**: `neo4j_data` named volume → `/data`

## 환경변수 목록

| 변수명 | 선언 위치 | 용도 |
|---|---|---|
| `NEO4J_PASSWORD` | `.env`, `docker-compose.yml` | Neo4j 인증 비밀번호 |
| `NEO4J_URI` | `docker-compose.yml` (api 서비스) | Neo4j Bolt 접속 URI |
| `NEO4J_USER` | `docker-compose.yml` (api 서비스) | Neo4j 사용자명 |
| `VITE_API_URL` | `frontend/.env.production` | 프론트 API 베이스 URL (`/api`). 미설정 시 `http://localhost:8000` |
| `DATA_DIR` | `backend/app/routes/events.py`, `books.py` | 오버레이 JSON 파일 탐색 루트. 기본값 `/app/data` |

## 외부 서비스 / API

### 1. getbible API v2 (빌드타임 전용)

- **사용 시점**: 빌드타임 스크립트 `backend/scripts/generate_verse_text.py`에서만 호출. 런타임에는 미호출 (ADR-0003)
- **엔드포인트 패턴**: `https://api.getbible.net/v2/{slug}/{bookOrder}/{chapter}.json`
- **사용 번역**: `korean` (한국어), `kjv` (영어 King James Version)
- **인증**: 없음 (공개 API). 단, Python 기본 `urllib` UA(`Python-urllib`)에 403 반환 → `User-Agent: Mozilla/5.0 (compatible; BibleMap-build/1.0)` 헤더 필요
- **캐시 전략**: 모듈 내 `_chapter_cache` dict로 동일 `(slug, bookOrder, chapter)` 튜플은 1회만 fetch
- **결과 저장**: `data/event_verses/events.json`, `data/book_context/books.json`, `data/character_traits/people.json`에 인라인으로 저장 (멱등, 이미 본문 있으면 스킵)

### 2. Theographic Bible Metadata (빌드타임 전용)

- **사용 시점**: `backend/scripts/load_theographic.py`, `load_books.py`, `generate_book_context.py`, `generate_event_verses.py`, `generate_person_traits.py`
- **소스**: GitHub raw 파일 (`https://raw.githubusercontent.com/robertrouse/theographic-bible-metadata/master/json/`)
- **가져오는 파일**: `people.json`, `places.json`, `events.json`, `peopleGroups.json`, `books.json`, `verses.json`
- **인증**: 없음 (GitHub 공개 저장소)
- **연결 방식**: `urllib.request.urlopen` (동기, 단발 fetch)

### 3. Esri ArcGIS Online (런타임 — 클라이언트 직접 호출)

- **사용 시점**: 프론트엔드 `frontend/src/MapView.jsx` — maplibre-gl 지도 초기화 시 래스터 타일 소스로 등록
- **타일 URL**: `https://server.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}`
- **인증**: 없음 (공개 타일 서비스)
- **사용 라이브러리**: maplibre-gl 5.24.0

## CI/CD 연동

### GitHub Actions (`.github/workflows/deploy.yml`)

- **트리거**: `main` 브랜치 push
- **러너**: `self-hosted` (로컬 macOS 호스트)
- **동작**: `git fetch origin && git reset --hard origin/main && bash deploy.sh`
- **외부 인증 없음**: GitHub → self-hosted runner 간 네트워크 연결만 사용

## 프론트엔드 → 백엔드 통신

- **단일 클라이언트**: `frontend/src/api.js` — `API_BASE` + `apiGet(path)` 헬퍼
- **프로덕션 경로**: 브라우저 → Nginx `/api/` → `http://api:8000/` (내부 프록시)
- **개발 경로**: 브라우저 → `http://localhost:8000` (직접)
- **메서드**: GET 전용 (백엔드 CORS도 GET만 허용)
- **호출 엔드포인트**:
  - `GET /node/{id}` — 노드 상세 (`backend/app/routes/nodes.py`)
  - `GET /node/{id}/places` — 노드 연관 장소
  - `GET /node/{id}/neighbors/grouped` — 이웃 노드 그룹
  - `GET /events` — 타임라인 사건 목록 (`backend/app/routes/events.py`)
  - `GET /event/{id}/verses` — 사건 근거 구절
  - `GET /books` — 타임라인 권 목록 (`backend/app/routes/books.py`)
  - `GET /search?q=` — 전문 검색 (`backend/app/routes/search.py`)

## 런타임 오버레이 파일 (외부 API 대체)

런타임에 외부 API를 직접 호출하지 않고, 빌드타임에 생성된 로컬 JSON 파일을 메모리 캐시(`functools.lru_cache`)로 읽어 사용:

| 파일 | 사용 라우터 | 내용 |
|---|---|---|
| `data/event_verses/events.json` | `routes/events.py` | 사건별 근거 구절 + 절 본문(ko/en) |
| `data/book_events/books.json` | `routes/events.py`, `routes/books.py` | 권 → 연결 사건 ID 매핑 |
| `data/book_years_approx/books.json` | `routes/books.py` | 추정 집필연도 오버레이 |
