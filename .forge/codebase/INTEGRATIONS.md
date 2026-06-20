---
last_mapped_commit: 7a1ef362b1fb247b09edeeaa1380e6449fce5721
mapped: 2026-06-20
---

# INTEGRATIONS.md — BibleMap 외부 통합

## 데이터베이스

### Neo4j 5

- **연결 방식**: Bolt 프로토콜, `bolt://neo4j:7687` (Docker Compose 내부망)
- **드라이버**: `neo4j==6.2.0` Python SDK
- **싱글턴 관리**: `backend/app/db.py` — `GraphDatabase.driver()` 한 번 생성 후 재사용
- **인증**: `NEO4J_USER` / `NEO4J_PASSWORD` 환경변수
- **외부 노출**: `127.0.0.1:7474` (HTTP), `127.0.0.1:7687` (Bolt) — 로컬호스트만 바인딩, 퍼블릭 미노출
- **인덱스 자동 생성**: `backend/app/main.py` lifespan에서 앱 기동 시 5개 인덱스 생성
- **데이터 원본**: Theographic Bible Metadata를 전처리하여 Neo4j에 적재 (`backend/scripts/inject_ko_names.py` 등)

---

## 외부 HTTP API

### ESRI NatGeo 타일 서버 (지도 배경)

- **용도**: MapLibre GL 지도 배경 래스터 타일
- **엔드포인트**: `https://server.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}`
- **호출 위치**: `frontend/src/MapView.jsx` — `addSource('esri-natgeo', { type: 'raster', tiles: [...] })`
- **런타임 여부**: 런타임 호출 (브라우저 → ESRI CDN)
- **인증**: 없음 (공개 타일 서비스)

### Protomaps 폰트 CDN (지도 글리프)

- **용도**: MapLibre GL 텍스트 레이어 Noto Sans 글리프
- **엔드포인트**: `https://protomaps.github.io/basemaps-assets/fonts/{fontstack}/{range}.pbf`
- **호출 위치**: `frontend/src/MapView.jsx` — `map.setStyle({ glyphs: ... })`
- **런타임 여부**: 런타임 호출 (브라우저 → GitHub Pages CDN)
- **인증**: 없음

### getbible.net v2 API (성경 구절 본문)

- **용도**: 한국어(`korean`) + 영어(`kjv`) 구절 원문 수집
- **엔드포인트**: `https://api.getbible.net/v2/{slug}/{bookOrder}/{chapter}.json`
- **런타임 여부**: **빌드타임 전용** (ADR-0003) — 오프라인 스크립트에서 미리 굽기, 런타임 호출 없음
- **수집 결과 저장 위치**:
  - `data/event_verses/events.json` (사건별 구절 본문 포함)
  - `data/book_context/books.json` (권별 대표구절 본문 포함)
  - `data/character_traits/people.json` (인물 성품 구절 본문 포함)
- **인증**: 없음

---

## Anthropic Claude API (오프라인 콘텐츠 생성)

- **용도**: 성경 권 배경·주제 문구, 인물 성품 설명 생성
- **SDK**: `anthropic` Python 패키지 (백엔드 requirements.txt 미포함 — 별도 로컬 스크립트용)
- **모델**: `claude-haiku-4-5-20251001`
- **런타임 여부**: **오프라인 전용** — 앱 런타임에 호출하지 않음
- **관련 스크립트**:
  - `backend/scripts/generate_book_context.py` — 권 배경/주제/대표구절
  - `backend/scripts/generate_book_context_enrich.py` — 권 콘텐츠 보강
  - `backend/scripts/generate_person_traits.py` — 인물 성품 (상위 N명)
  - `backend/scripts/generate_approx_book_verses.py` — 추정 연대 구절
- **인증**: `ANTHROPIC_API_KEY` 환경변수 (스크립트 실행 환경에서만 필요)

---

## 정적 데이터 소스

### Theographic Bible Metadata

- **출처**: [github.com/robertrouse/theographic-bible-metadata](https://github.com/robertrouse/theographic-bible-metadata)
- **라이선스**: CC-BY-SA-4.0
- **용도**: 인물·장소·사건·집단·권 원본 데이터 — Neo4j 적재용
- **포함 데이터**: `people.json`, `places.json`, `events.json`, `peopleGroups.json`, `books.json`
- **적재 스크립트**: `backend/scripts/inject_ko_names.py` (deploy.sh 4단계에서 실행)

### JSON 오버레이 파일 (`data/` 디렉토리)

런타임에 Neo4j 쿼리 결과를 보완하는 파일 기반 오버레이. `backend/app/overlays.py`가 `lru_cache`로 읽어 FastAPI 응답에 병합.

| 경로 | 내용 | 소비 엔드포인트 |
|------|------|----------------|
| `data/book_events/books.json` | `{bookId: [eventId, ...]}` | `/books` |
| `data/book_years_approx/books.json` | `{bookId: {placementYear, basis}}` | `/books` |
| `data/event_verses/events.json` | 사건별 구절 + 본문 | `/event/{id}/verses` |
| `data/book_context/books.json` | 권별 배경/주제/대표구절/구조 | `/node/{id}` (Book) |
| `data/character_traits/people.json` | 인물 성품 목록 | `/node/{id}` (Person) |
| `data/names_ko/` | 한국어 이름 오버레이 | 전체 조회 |
| `data/place_coords/places.json` | 장소 위경도 보정 | `/node/{id}/places` |

Docker Compose 볼륨 마운트: `./data:/app/data` (`docker-compose.yml`)
`DATA_DIR` 환경변수로 경로 오버라이드 가능 (`backend/app/overlays.py`).

---

## 인증 / 보안

- **사용자 인증 없음** — 로그인, 세션, JWT 미구현
- **API**: GET 전용, `CORS allow_credentials=False`, `allow_origins=["*"]`
- **Neo4j**: 환경변수 비밀번호 보호, 퍼블릭 포트 미노출 (`127.0.0.1` 바인딩)
- **프론트엔드**: 외부에서 직접 API 접근 불가 — Nginx가 `/api/` 경로로만 프록시

---

## 웹훅 / 이벤트 스트림

- **없음.** 외부 웹훅 수신·발신 없음. 서버-사이드 이벤트(SSE) 없음. WebSocket 없음.
