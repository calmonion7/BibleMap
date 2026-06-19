---
last_mapped_commit: 9f47b78ed927ef302cefffb5b62ef71885b6aa94
mapped: 2026-06-19
---

# 외부 연동

## 데이터베이스

### Neo4j

- **프로토콜:** Bolt (`bolt://`)
- **연결 설정:** `backend/app/db.py` — 환경변수 `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`
- **기본값:** `bolt://localhost:7687`, user `neo4j`
- **Docker 내:** `bolt://neo4j:7687` (compose 내부 DNS)
- **드라이버:** neo4j Python 6.2.0, 싱글턴 `_driver` 패턴 (`get_driver()`)
- **세션 방식:** 동기 `driver.session()`, 컨텍스트 매니저
- **호스트 직접 접근:** 포트 7474/7687이 `127.0.0.1`에만 바인딩되므로 로컬에서 직접 쿼리 가능

## 외부 API

### Anthropic Claude API (오프라인 스크립트 전용)

런타임 API 서버(`backend/app/`)에서는 사용하지 않음. 데이터 사전 생성 스크립트에서만 호출.

| 스크립트 | 모델 | 용도 |
|----------|------|------|
| `backend/scripts/generate_book_events.py` | `claude-haiku-4-5-20251001` | 추정연도 책 → 타임라인 사건 연결 매핑 생성 |
| `backend/scripts/generate_book_context.py` | `claude-haiku-4-5-20251001` | 책 배경 컨텍스트 JSON 생성 |
| `backend/scripts/generate_verse_events.py` | `claude-haiku-4-5-20251001` | 구절 → 사건 매핑 생성 |
| `backend/scripts/generate_person_traits.py` | `claude-haiku-4-5-20251001` | 인물 특성(traits) JSON 생성 |

- **인증:** 환경변수 `ANTHROPIC_API_KEY` (각 스크립트 실행 시 주입)
- **SDK:** `anthropic` Python 패키지 (`backend/requirements.txt`에 없음 — 스크립트 전용 의존성)
- **호출 방식:** `client.messages.create(model=..., max_tokens=4096, messages=[...])`
- **산출물:** `data/` 디렉터리의 JSON 파일 (런타임에 API 서버가 파일로 읽음)

### GetBible API

- **스크립트:** `backend/scripts/generate_verse_text.py`
- **엔드포인트:** `https://api.getbible.net/v2/{slug}/{book_order}/{chapter}.json`
- **인증:** 없음 (공개 API)
- **용도:** 성경 본문(구절 텍스트) 취득 → `data/event_verses/` 오버레이에 저장

### Theographic Bible Metadata (GitHub Raw)

- **스크립트:** `backend/scripts/load_theographic.py`, `backend/scripts/load_books.py`
- **베이스 URL:** `https://raw.githubusercontent.com/robertrouse/theographic-bible-metadata/master/json/`
- **수신 파일:**
  - `people.json`
  - `places.json`
  - `events.json`
  - `peopleGroups.json`
  - `books.json`
- **인증:** 없음 (공개 GitHub Raw)
- **용도:** Neo4j 초기 데이터 적재 (`load_theographic.py`, `load_books.py` 1회 실행)

## 지도 타일 서비스 (프론트엔드 런타임)

### ESRI ArcGIS Online (NatGeo World Map)

- **URL 패턴:** `https://server.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}`
- **참조 위치:** `frontend/src/MapView.jsx` — MapLibre GL `sources.esri` 래스터 소스
- **인증:** 없음 (공개 타일)
- **타일 크기:** 256px

### Protomaps 폰트 CDN

- **URL 패턴:** `https://protomaps.github.io/basemaps-assets/fonts/{fontstack}/{range}.pbf`
- **참조 위치:** `frontend/src/MapView.jsx` — MapLibre GL `glyphs` 설정
- **용도:** 지도 레이블 렌더링 (`Noto Sans Regular`)
- **인증:** 없음 (공개 CDN)

## 인증 제공자

없음. 현재 애플리케이션에 사용자 인증 없음.

## 웹훅

없음.

## 환경변수 요약

| 변수 | 사용처 | 필수 여부 |
|------|--------|-----------|
| `NEO4J_PASSWORD` | `backend/app/db.py`, `docker-compose.yml`, 각 스크립트 | 필수 |
| `NEO4J_URI` | `backend/app/db.py`, 각 스크립트 | 선택 (기본: `bolt://localhost:7687`) |
| `NEO4J_USER` | `backend/app/db.py`, 각 스크립트 | 선택 (기본: `neo4j`) |
| `ANTHROPIC_API_KEY` | 데이터 생성 스크립트 4개 | 스크립트 실행 시 필수 |
| `VITE_API_URL` | `frontend/src/api.js` (빌드타임) | 선택 (기본: `http://localhost:8000`); 프로덕션은 `/api` |
| `DATA_DIR` | `backend/app/routes/events.py`, `backend/app/routes/books.py` | 선택 (기본: `/app/data`) |
