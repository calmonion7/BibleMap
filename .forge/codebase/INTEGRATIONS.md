---
last_mapped_commit: 70a9781e6523a396ad856f980b5499b1cc814d7a
mapped: 2026-06-21
---

# INTEGRATIONS.md — BibleMap 외부 통합

## 데이터베이스

### Neo4j 5

- **연결 방식**: Bolt 프로토콜, `bolt://neo4j:7687` (Docker Compose 내부망)
- **드라이버**: `neo4j==6.2.0` Python SDK (`backend/requirements.txt`)
- **싱글턴 관리**: `backend/app/db.py` — `get_driver()` 가 `GraphDatabase.driver()` 를 한 번 생성 후 재사용
- **인증**: `NEO4J_USER` / `NEO4J_PASSWORD` 환경변수 (compose는 `NEO4J_AUTH=neo4j/${NEO4J_PASSWORD}`)
- **외부 노출**: `127.0.0.1:7474` (HTTP), `127.0.0.1:7687` (Bolt) — 로컬호스트만 바인딩, 퍼블릭 미노출 (`docker-compose.yml`)
- **인덱스 자동 생성**: `backend/app/main.py` lifespan에서 앱 기동 시 5개 인덱스(`{label}_tid`) 생성
- **데이터 원본**: Theographic Bible Metadata를 전처리·생성하여 적재 (`backend/scripts/load_*.py`, `inject_*.py`)

---

## 외부 HTTP API

### ESRI NatGeo 타일 서버 (지도 배경)

- **용도**: MapLibre GL 지도 배경 래스터 타일
- **엔드포인트**: `https://server.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}`
- **호출 위치**: `frontend/src/MapView.jsx:428` — `addSource('esri-natgeo', { type: 'raster', tiles: [...] })`
- **런타임 여부**: 런타임 호출 (브라우저 → ESRI CDN)
- **인증**: 없음 (공개 타일 서비스)

### Protomaps 폰트 CDN (지도 글리프)

- **용도**: MapLibre GL 텍스트 레이어 글리프
- **엔드포인트**: `https://protomaps.github.io/basemaps-assets/fonts/{fontstack}/{range}.pbf`
- **호출 위치**: `frontend/src/MapView.jsx:423` — `map.setStyle({ glyphs: ... })`
- **런타임 여부**: 런타임 호출 (브라우저 → GitHub Pages CDN)
- **인증**: 없음

### getbible.net v2 API (성경 구절 본문)

- **용도**: 한국어(`korean`) + 영어(`kjv`) 구절 원문 수집
- **엔드포인트**: `https://api.getbible.net/v2/{slug}/{bookOrder}/{chapter}.json`
- **런타임 여부**: **빌드타임 전용** (ADR-0003) — 오프라인 스크립트에서 미리 굽기, 런타임 호출 없음
- **호출 스크립트**:
  - `backend/scripts/generate_verse_text.py` — 4개 생성 데이터의 인용 절 본문을 인라인 저장 (유니크 번역·책·장당 1회 fetch, 멱등). 기본 UA가 403을 받아 브라우저류 UA로 요청.
  - `backend/scripts/generate_person_event_verses.py` — 인물 여정 사건 구절 본문 수집
- **수집 결과 저장 위치** (`generate_verse_text.py`):
  - `data/event_verses/events.json` → `books[].verses[].textKo / textEn`
  - `data/book_context/books.json` → `keyVerseTextKo / keyVerseTextEn`
  - `data/character_traits/people.json` → `traits[].verse_textKo / verse_textEn`
  - `data/place_context/places.json` → `keyVerseTextKo / keyVerseTextEn` **(신규)**
- **인증**: 없음

---

## Anthropic Claude API (오프라인 콘텐츠 생성)

- **용도**: 성경 권 배경·주제 문구, 인물 성품, 추정책↔사건 연결, 구절 사건 생성
- **SDK**: `anthropic` Python 패키지 (`anthropic.Anthropic(api_key=...)`) — `backend/requirements.txt` **미포함**(별도 로컬 스크립트용)
- **모델**: `claude-haiku-4-5-20251001`
- **런타임 여부**: **오프라인 전용** — 앱 런타임에 호출하지 않음
- **관련 스크립트** (Anthropic 직접 호출):
  - `backend/scripts/generate_book_context.py` — 권 배경/주제/대표구절
  - `backend/scripts/generate_book_events.py` — 추정책 31권 ↔ 사건 의미 연결 오버레이
  - `backend/scripts/generate_verse_events.py` — 구절 기반 사건 생성
  - `backend/scripts/generate_person_traits.py` — 인물 성품
  - `backend/scripts/generate_approx_book_verses.py` — 추정 연대 구절
  - `backend/scripts/generate_book_context_enrich.py` — 재생성 레시피(주석 가이드, 직접 호출 없음)
- **인증**: `ANTHROPIC_API_KEY` 환경변수 (스크립트 실행 환경에서만 필요)

---

## 정적 데이터 소스

### Theographic Bible Metadata

- **출처**: [github.com/robertrouse/theographic-bible-metadata](https://github.com/robertrouse/theographic-bible-metadata)
- **라이선스**: CC-BY-SA-4.0
- **용도**: 인물·장소·사건·집단·권 원본 데이터 — Neo4j 적재용
- **수집 방식**: 로컬 파일이 아니라 **`raw.githubusercontent.com/.../master/json/*.json` 에서 빌드타임에 직접 fetch**
- **사용 데이터셋**: `people.json`, `places.json`, `events.json`, `peopleGroups.json`, `books.json`
- **적재 스크립트**: `backend/scripts/load_theographic.py`(인물·장소·사건·집단), `load_books.py`(권)
- **한글명 적재**: `inject_ko_names.py` (`deploy.sh` 4단계에서 실행)

### JSON 오버레이 파일 (`data/` 디렉토리) — 런타임 소비

런타임에 Neo4j 쿼리 결과를 보완하는 파일 기반 오버레이. `backend/app/overlays.py` 가 `lru_cache` 로 읽어 FastAPI 응답에 병합. **런타임에 실제로 읽는 파일은 아래 3개뿐**이다(`overlays.py` 의 세 함수).

| 경로 | 로더 함수 | 소비 엔드포인트 |
|------|-----------|----------------|
| `data/book_events/books.json` | `book_events_raw()` | `/books`, `/events`(역방향 인덱스) |
| `data/book_years_approx/books.json` | `approx_years()` | `/books` |
| `data/event_verses/events.json` | `event_verses()` | `/event/{id}/verses` |

`DATA_DIR` 환경변수로 경로 오버라이드 가능, 없으면 repo `data/` 폴백 (`overlays.py:_resolve`). Compose 볼륨 마운트: `./data:/app/data`.

### JSON 데이터 파일 (`data/` 디렉토리) — Neo4j 주입 전용

아래 파일들은 **런타임 오버레이가 아니라** 빌드타임 inject/load 스크립트로 Neo4j 노드에 SET·적재된다(런타임 코드는 직접 읽지 않음).

| 경로 | 적재 스크립트 | 대상 |
|------|--------------|------|
| `data/names_ko/` | `inject_ko_names.py` | Person·Place 한글명 |
| `data/book_context/books.json` | `inject_book_context.py` | Book 속성 |
| `data/character_traits/people.json` | `inject_person_traits.py` | Person `traits` |
| `data/place_context/places.json` **(신규)** | `inject_place_context.py` | Place `background`·`keyVerse`·`keyVerseTextKo/En` |
| `data/place_coords/places.json` | `enrich_place_coords.py` | Place 좌표 |
| `data/person_events/*.json` | `load_person_events.py` | authored Event 노드/관계 |
| `data/verse_events/events.json` | `load_verse_events.py` | Event 노드 + `CONTAINS_BOOK` |
| `data/authored_events/events.json` | `load_authored_events.py` | authored Event 노드 |

---

## 인증 / 보안

- **사용자 인증 없음** — 로그인, 세션, JWT 미구현
- **API**: GET 전용 (`allow_methods=["GET"]`), `allow_credentials=False`, `allow_origins=["*"]` (`backend/app/main.py`)
- **Neo4j**: 환경변수 비밀번호 보호, 퍼블릭 포트 미노출 (`127.0.0.1` 바인딩)
- **프론트엔드**: 외부에서 직접 API 접근 불가 — Nginx가 `/api/` 경로로만 프록시

---

## 웹훅 / 이벤트 스트림

- **없음.** 외부 웹훅 수신·발신 없음. 서버-사이드 이벤트(SSE) 없음. WebSocket 없음.
