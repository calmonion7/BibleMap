---
last_mapped_commit: cecf0d7de87192b638f428eb7e708e94a58214a6
mapped: 2026-06-20
---

# External Integrations

**Analysis Date:** 2026-06-20

## APIs & External Services

**Graph Database:**
- Neo4j 5 — 전체 성경 그래프 데이터 저장 및 쿼리
  - SDK/Client: `neo4j==6.2.0` (Python 공식 드라이버)
  - Auth: `NEO4J_USER` / `NEO4J_PASSWORD` 환경변수
  - 연결 파일: `backend/app/db.py`

**성경 메타데이터 소스 (빌드타임 전용):**
- Theographic Bible Metadata — GitHub Raw JSON 엔드포인트
  - 베이스: `https://raw.githubusercontent.com/robertrouse/theographic-bible-metadata/master/json/`
  - 수집 파일: `people.json`, `places.json`, `events.json`, `peopleGroups.json`, `books.json`, `verses.json`
  - 호출 스크립트: `backend/scripts/load_theographic.py`, `backend/scripts/load_books.py`, `backend/scripts/generate_book_context.py`, `backend/scripts/generate_person_traits.py`, `backend/scripts/generate_event_verses.py`, `backend/scripts/generate_verse_events.py`
  - 호출 방식: `urllib.request.urlopen()` (표준 라이브러리)
  - 런타임 호출: 없음

**성경 구절 본문 API (빌드타임 prebake 전용):**
- GetBible API v2 — 구절 원문 제공
  - 베이스 URL: `https://api.getbible.net/v2/`
  - 엔드포인트 패턴: `/{translation_slug}/{book_order}/{chapter}.json`
  - 번역 슬러그: `korean` (한국어), `kjv` (영어)
  - User-Agent: `Mozilla/5.0 (compatible; BibleMap-build/1.0)` (기본 Python UA는 403 반환)
  - 호출 스크립트: `backend/scripts/generate_verse_text.py`
  - 출력: `data/event_verses/events.json`, `data/book_context/books.json`, `data/character_traits/people.json`에 `textKo`/`textEn` 필드 인라인 저장 (ADR-0003)
  - 런타임 호출: 없음

**LLM (빌드타임 데이터 생성 전용):**
- Anthropic Claude API — 성경 데이터 구조화 생성
  - SDK: `anthropic` Python 패키지 (`requirements.txt` 미포함, 스크립트 전용)
  - 모델: `claude-haiku-4-5-20251001`
  - Auth: `ANTHROPIC_API_KEY` 환경변수
  - 사용 스크립트:

  | 스크립트 | 출력 파일 | 생성 내용 |
  |---------|---------|---------|
  | `backend/scripts/generate_book_context.py` | `data/book_context/books.json` | 권별 배경·주제·대표 구절 |
  | `backend/scripts/generate_person_traits.py` | `data/character_traits/people.json` | 인물 성품·근거 구절 |
  | `backend/scripts/generate_book_events.py` | `data/book_events/books.json` | 추정연도 책 → 연결 사건 매핑 |
  | `backend/scripts/generate_verse_events.py` | `data/verse_events/events.json` | 고아 구절 → 사건 도출 |

  - 런타임 호출: 없음

**지도 타일 (런타임, 브라우저):**
- ESRI NatGeo World Map — 래스터 타일
  - URL 패턴: `https://server.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}`
  - 호출 위치: `frontend/src/MapView.jsx` (MapLibre GL 스타일 소스)
  - 인증: 없음 (공개 엔드포인트)
- Protomaps Basemaps Assets — 글꼴(glyph) CDN
  - URL 패턴: `https://protomaps.github.io/basemaps-assets/fonts/{fontstack}/{range}.pbf`
  - 호출 위치: `frontend/src/MapView.jsx` (MapLibre GL style.glyphs)

## Data Storage

**Databases:**
- Neo4j 5 (그래프 DB)
  - 연결: `bolt://neo4j:7687` (Docker 내부), `bolt://localhost:7687` (로컬)
  - 환경변수: `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`
  - 클라이언트: `neo4j` Python 드라이버, 싱글턴 패턴 (`backend/app/db.py`)
  - 데이터 영속화: Docker named volume `neo4j_data`

**File Storage:**
- JSON 오버레이 파일 — `data/` 디렉터리 (Docker 볼륨 마운트 `./data:/app/data`)
  - `data/book_events/books.json` — 책별 연결 사건 ID 목록
  - `data/book_years_approx/books.json` — 추정 집필 연도
  - `data/event_verses/events.json` — 사건별 근거 구절 + 구절 본문
  - `data/book_context/books.json` — 권별 배경·주제·대표 구절 본문
  - `data/character_traits/people.json` — 인물 성품 + 근거 구절 본문
  - `data/authored_events/` — 집필 배경 사건 데이터
  - `data/verse_events/events.json` — 구절 → 사건 매핑

**Caching:**
- 메모리 캐시 (`functools.lru_cache(maxsize=1)`) — `backend/app/overlays.py` 오버레이 파일 1회 로드
- 메모리 캐시 — `backend/app/routes/events.py` `_compute_events()` 앱 재시작 전까지 유지
- HTTP 캐시 헤더: `/events`, `/event/{id}/verses` → `Cache-Control: max-age=300`

## Authentication & Identity

**Auth Provider:**
- 없음 — 앱 자체 인증 없음. 읽기 전용 공개 서비스.
- FastAPI CORS: `allow_origins=["*"]`, `allow_methods=["GET"]` (`backend/app/main.py`)

## Monitoring & Observability

**Error Tracking:**
- 없음 (외부 서비스 미사용)

**Logs:**
- `logging` 표준 라이브러리 — 앱 시작 시 Neo4j 인덱스 생성 실패 로그 (`backend/app/main.py`)

## CI/CD & Deployment

**Hosting:**
- 셀프-호스트 macOS 서버

**CI Pipeline:**
- GitHub Actions (`self-hosted` runner)
  - 트리거: `push` to `main`
  - 파일: `.github/workflows/deploy.yml`
  - 동작: `git fetch origin && git reset --hard origin/main && bash deploy.sh`

**Deployment:**
- `deploy.sh` 스크립트 (루트)
- 프론트엔드: `frontend/dist` 정적 빌드 → nginx 볼륨 마운트
- 백엔드: Docker Compose `api` 서비스 재빌드

## Webhooks & Callbacks

**Incoming:**
- 없음

**Outgoing:**
- 없음

## Environment Configuration

**Required env vars:**
- `NEO4J_PASSWORD` — `.env` 파일 (루트), `docker-compose.yml` 참조
- `ANTHROPIC_API_KEY` — 데이터 생성 스크립트 실행 시만 필요 (앱 런타임 불필요)

**Build-time env vars:**
- `VITE_API_URL` — `frontend/.env.production` (`/api`)

**Secrets location:**
- `.env` (루트, `.gitignore` 처리) — `NEO4J_PASSWORD`

---

*Integration audit: 2026-06-20*
