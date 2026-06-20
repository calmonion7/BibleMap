---
last_mapped_commit: 71c28dc
mapped: 2026-06-20
---

# BibleMap — 아키텍처

## 전체 레이어 구조

```
브라우저
  └── React SPA (Vite 빌드, frontend/dist/)
        ↓ fetch /api/*
Nginx (포트 8080)
  ├── /api/* → 리버스 프록시 → FastAPI (api:8000)
  └── /*     → frontend/dist/ (SPA fallback)
FastAPI (백엔드)
  ├── GET 엔드포인트 4종
  ├── overlays.py (JSON 파일 → lru_cache)
  └── db.py (Neo4j 드라이버 싱글턴)
Neo4j 5 (bolt://neo4j:7687)
  └── 그래프 DB — Person, Place, Event, PeopleGroup, Book 노드
data/ (마운트 볼륨, 읽기 전용)
  └── JSON 오버레이 파일 — Neo4j에 주입하지 않는 추정 데이터
```

세 컨테이너(`neo4j`, `api`, `nginx`)는 `docker compose`로 관리된다. nginx만 외부에 노출(8080→80). Neo4j·api는 `127.0.0.1`에만 바인드(호스트 직접 접근용).

---

## 데이터 흐름

### 조회 경로 (런타임)

```
브라우저 useSearch / useNodeSelection / 뷰 컴포넌트
  → api.js apiGet(path)
  → Nginx /api/* 프록시
  → FastAPI 라우터
  → db.py get_driver() → Neo4j Cypher 쿼리
  → overlays.py lru_cache (JSON 오버레이 머지)
  → JSON 응답
```

### 데이터 적재 경로 (오프라인 스크립트)

```
Theographic Bible Metadata (GitHub JSON)
  → load_theographic.py : Person·Place·Event·PeopleGroup 노드 + 관계 일괄 적재
  → load_books.py       : Book 노드 + CONTAINS_BOOK(구절 교집합)
  → inject_ko_names.py  : nameKo 속성 주입 (deploy.sh 4단계)
  → inject_person_traits.py  : traits JSON 주입
  → inject_book_context.py   : themes·keyVerse·keyVerseTextKo 주입
  → load_authored_events.py  : authored=true 저작 이벤트 주입
  → load_verse_events.py     : verse_events 오버레이 → Neo4j
  → load_person_events.py    : person_events JSON → Neo4j
LLM 생성 스크립트 (오프라인 1회성)
  → generate_*.py   : 오버레이 JSON 파일 생성 (data/ 디렉터리)
  → enrich_place_coords.py : Place 좌표 보강
```

---

## 주요 추상화

### 백엔드

**`db.py` — 드라이버 싱글턴**
- 환경변수(`NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`)로 단일 `GraphDatabase.driver` 인스턴스를 생성하고 재사용.

**`overlays.py` — JSON 오버레이 계층**
- `data/` 디렉터리의 JSON 파일을 `lru_cache(maxsize=1)`으로 1회 로드.
- Neo4j 권위 그래프와 분리된 추정·저권위 데이터(추정연도, book_events 맵, event_verses 맵)를 담당.
- `_resolve(subpath)`: 환경변수 `DATA_DIR`(/app/data) → 레포 내 `data/` 순으로 파일 탐색.

**라우터 4개 (`backend/app/routes/`)**
- `nodes.py` — `/node/{id}`, `/node/{id}/places`, `/node/{id}/neighbors/grouped`, `/person/{id}/event-ids`
- `events.py` — `/events` (타임라인 전체 목록, `lru_cache`), `/event/{id}/verses`
- `books.py` — `/books` (타임라인 배치용), `/books-overview` (성경 개요 뷰)
- `search.py` — `/search?q=`

**캐시 전략**
- `/events`: `_compute_events()` `lru_cache(maxsize=1)` — 재시작 전 메모리 보관, `Cache-Control: max-age=300`
- `/books`·`/books-overview`: `Cache-Control: no-store` (매 요청 Neo4j 조회)
- `overlays.*`: `lru_cache(maxsize=1)` — 앱 수명 내 1회 로드

### 프론트엔드

**`api.js` — 단일 fetch 클라이언트**
- `API_BASE = VITE_API_URL || 'http://localhost:8000'`
- `apiGet(path, {signal})`: 비-OK → `Error(status)` throw, AbortError 전파.
- 프로덕션 빌드 시 `VITE_API_URL=/api`(`.env.production`)로 nginx 프록시 경유.

**`useNodeSelection.js` — 전역 노드 선택 상태**
- `selectedNode` (theographic_id), `selectedNodeMeta` (label·연도), `history` (뒤로가기 스택), `personEventIds` (Set).
- `selectNode` → 히스토리 push 후 선택. `selectNodeFresh` → 히스토리 초기화 후 선택.
- `selectedNodeRef`로 최신값 동기화 — MapView useEffect 재실행으로 인한 fetch abort 버그 방지.

**`useSearch.js` — 실시간 검색**
- 입력 250ms 디바운스 → `apiGet('/search?q=...')` → AbortController로 경쟁 차단.

**`theme.js` — 타입 색상·한글 라벨 단일 정규화**
- `TYPE_COLOR`, `TYPE_KO`, `TYPE_ORDER`, `SELECT_HL` 상수를 모든 뷰 컴포넌트가 공유.

---

## 엔트리 포인트

| 레이어 | 파일 | 역할 |
|---|---|---|
| 프론트 | `frontend/src/main.jsx` | React DOM 마운트 |
| 프론트 | `frontend/src/App.jsx` | 탭 라우팅, 검색 UI, SidePanel 오버레이 조합 |
| 백엔드 | `backend/app/main.py` | FastAPI 앱 생성, lifespan(인덱스 보장), 라우터 등록 |
| 컨테이너 | `docker-compose.yml` | 3서비스 오케스트레이션 |
| 배포 | `deploy.sh` | 프론트 빌드 → api 이미지 빌드 → 컨테이너 재시작 → ko 이름 주입 |
| CI | `.github/workflows/deploy.yml` | main 푸시 → self-hosted runner에서 deploy.sh 실행 |

---

## Neo4j 그래프 스키마

**노드 레이블**: `Person`, `Place`, `Event`, `PeopleGroup`, `Book`

**관계**:
```
(Event)-[:HAS_PARTICIPANT]->(Person)
(Event)-[:OCCURS_AT]->(Place)
(Event)-[:PART_OF]->(Event)         # 상위 사건 계층
(Person)-[:PARENT_OF]->(Person)
(Person)-[:CHILD_OF]->(Person)
(Person)-[:SIBLING_OF]-(Person)
(Person)-[:PARTNER_OF]-(Person)
(Person)-[:MEMBER_OF]->(PeopleGroup)
(Book)-[:CONTAINS_BOOK]->(Event)    # 구절 교집합 기반, "사건의 성경적 근거"
```

**공통 속성**: 모든 노드에 `theographic_id` (안정 키, 인덱싱됨). 한국어 이름은 `nameKo`. 저작 이벤트는 `authored: true`, `theographic_id: "authored-<slug>"`.

---

## 뷰 구성 (프론트)

`App.jsx`가 세 뷰를 `display: none/block` CSS 토글로 항상 마운트 유지(상태 보존):

- **MapView** — MapLibre GL JS, ESRI NatGeo 타일, Convex Hull, 사건 링(radial ring)
- **TimelineView** — `/events` 전체 목록, 연도 그룹, Book/Person 필터, 근거 구절 인라인 드릴다운
- **BibleOverviewView** — `/books-overview`, 장르별 카드 그리드

SidePanel은 절대 위치 오버레이. 데스크톱: 우측 360px 슬라이드인, 모바일(≤768px): 하단 55vh 시트.
