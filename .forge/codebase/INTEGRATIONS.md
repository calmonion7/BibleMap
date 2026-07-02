---
last_mapped_commit: 689126abab88e741263d1d9a4a73d81b2be617d9
mapped: 2026-07-02
---

# INTEGRATIONS.md

## 데이터베이스 — Neo4j

**이미지**: `neo4j:5` (Docker Hub 공식)

**접속 프로토콜**: Bolt (`bolt://neo4j:7687` — 컨테이너 내부 통신)

**인증**: `NEO4J_AUTH=neo4j/${NEO4J_PASSWORD}` (환경변수, `.env` 루트에서 주입)

**연결 코드 위치**: `backend/app/db.py` — `GraphDatabase.driver(uri, auth=(user, password))` 싱글턴.

**Neo4j 노드 레이블 및 인덱스** (`backend/app/main.py` lifespan):
- `Person`, `Place`, `Event`, `PeopleGroup`, `Book` 각각 `theographic_id` 속성에 인덱스 자동 생성.

**Neo4j 관계 타입** (코드 내 Cypher 기준):
- `HAS_PARTICIPANT` — Event → Person
- `OCCURS_AT` — Event → Place
- `MEMBER_OF` — Person → PeopleGroup
- `CONTAINS_BOOK` — Book → Event

**주요 Cypher 쿼리 위치**:
- `backend/app/routes/nodes.py` — 노드/이웃/장소/책 조회
- `backend/app/routes/events.py` — 사건 목록, 근거 구절 책 조회
- `backend/app/routes/journey.py` — Place 노드 좌표 배치 조회
- `backend/app/routes/search.py` — `nameKo`/`name` 포함 검색

**외부 노출**: `127.0.0.1:7474` (브라우저), `127.0.0.1:7687` (Bolt) — 로컬호스트 한정, 인터넷 미노출.

---

## 지도 타일 서비스 (런타임, 브라우저에서 직접 호출)

### ArcGIS / Esri NatGeo 래스터 타일

- **URL 패턴**: `https://server.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}`
- **타일 크기**: 256px
- **용도**: MapView 배경 지도 레이어
- **연결 위치**: `frontend/src/MapView.jsx` — maplibre-gl `style.sources.esri` 설정
- **인증**: 없음 (공개 서비스)

### Protomaps 글리프 폰트 CDN

- **URL 패턴**: `https://protomaps.github.io/basemaps-assets/fonts/{fontstack}/{range}.pbf`
- **용도**: maplibre-gl 지도 텍스트 렌더링용 글리프
- **연결 위치**: `frontend/src/MapView.jsx` — `style.glyphs` 설정
- **인증**: 없음 (공개 CDN)

---

## 외부 성경 데이터 API — getbible.net (빌드타임 전용)

- **엔드포인트**: `https://api.getbible.net/v2/{translation}/{book_order}/{chapter}.json`
- **번역 슬러그**: `korean` (한국어), `kjv` (영어 KJV)
- **용도**: 구절 본문 텍스트 선(先)저장 (ADR-0003 프리베이킹). 런타임에서는 호출 없음.
- **연결 위치**:
  - `backend/scripts/generate_verse_text.py` (라인 80)
  - `backend/scripts/generate_person_event_verses.py` (라인 172)
- **주의사항**: 기본 `Python-urllib` User-Agent에 403 반환 → 브라우저 UA 헤더 우회 필요. 위 두 스크립트 모두 커스텀 UA 설정으로 처리.
- **인증**: 없음 (공개 API)

---

## Theographic Bible Metadata (빌드타임 전용)

- **소스**: `https://raw.githubusercontent.com/robertrouse/theographic-bible-metadata/master/json/{type}.json`
- **데이터셋**: `people.json`, `places.json`, `events.json`, `peopleGroups.json`
- **용도**: Neo4j 초기 데이터 로드 (Person, Place, Event, PeopleGroup 노드 생성)
- **연결 위치**: `backend/scripts/load_theographic.py` (라인 13-18)
- **필터**: `status == "publish"` 필드 기준 published 엔티티만 로드
- **인증**: 없음 (공개 GitHub Raw)

---

## Anthropic Claude API (빌드타임 데이터 생성 전용)

- **SDK**: `anthropic` Python SDK (런타임 의존성 아님 — `backend/requirements.txt`에 미포함, 스크립트 직접 설치 필요)
- **모델**: `claude-haiku-4-5-20251001`
- **인증**: `ANTHROPIC_API_KEY` 환경변수 (빌드타임 스크립트에서만 참조)
- **용도 및 연결 위치**:
  - `backend/scripts/generate_book_context.py` — 성경 각 권의 맥락 텍스트 생성
  - `backend/scripts/generate_book_events.py` — 권-사건 연결 데이터 생성
  - `backend/scripts/generate_verse_events.py` — 구절-사건 매핑 생성
  - `backend/scripts/generate_person_traits.py` — 인물 특성(traits) 생성
- **출력**: 생성 결과는 `data/` 디렉토리 JSON 파일로 저장 후 배포에 포함. 런타임 Claude 호출 없음.

---

## GitHub Actions (CI/CD)

- **워크플로우 파일**: `.github/workflows/deploy.yml`
- **트리거**: `push` → `branches: [main]`
- **실행 환경**: `runs-on: self-hosted` (macOS 로컬 머신의 GitHub Actions 러너)
- **배포 절차**: `git reset --hard origin/main` 후 `bash deploy.sh` 실행
- **러너 격리**: 레포 전용 러너 디렉토리 사용 (글로벌 CLAUDE.md 참조)

---

## 내부 API (백엔드 ↔ 프론트엔드)

nginx `/api/` → `http://api:8000/` 프록시를 통해 프론트가 호출하는 엔드포인트:

| 엔드포인트 | 메서드 | 데이터 소스 |
|---|---|---|
| `/events` | GET | Neo4j + `data/book_events/books.json` |
| `/event/{id}/verses` | GET | `data/event_verses/events.json` |
| `/node/{id}` | GET | Neo4j |
| `/node/{id}/places` | GET | Neo4j |
| `/node/{id}/neighbors/grouped` | GET | Neo4j |
| `/person/{id}/event-ids` | GET | Neo4j |
| `/persons/curated` | GET | `data/person_events/*.json` (Neo4j 미사용) |
| `/person/{id}/journey` | GET | `data/person_events/*.json` + Neo4j (Place 좌표) |
| `/place/{id}/curated-persons` | GET | `data/person_events/*.json` (Neo4j 미사용) |
| `/books-overview` | GET | Neo4j |
| `/search` | GET | Neo4j (`nameKo`, `name` 검색) |

**프론트 호출 위치**: 모든 fetch는 `frontend/src/api.js`의 `apiGet()` 헬퍼 경유.

---

## 인증 / 권한

별도의 사용자 인증 시스템 없음. 전체 API는 읽기 전용 GET, 인증 없이 공개.
