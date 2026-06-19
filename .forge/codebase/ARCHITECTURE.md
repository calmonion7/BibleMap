---
last_mapped_commit: 06b4012804c00a45ea7dfda9761d014ac91b11fb
mapped: 2026-06-20
---

# BibleMap — 아키텍처

## 전체 구조

SPA + REST API 이중 스택. 세 개의 Docker 서비스(`neo4j`, `api`, `nginx`)로 구성된 단일 `docker-compose.yml` 아래서 동작한다. 프론트엔드는 Vite 빌드 결과물을 nginx가 정적 서빙하며, 백엔드 API 요청은 nginx가 `/api/` → `api:8000/`으로 프록시한다.

```
브라우저
  → :8080 nginx
      ├── /api/*  → api:8000 (FastAPI, uvicorn)
      │                └─ bolt://neo4j:7687 (Neo4j 5)
      └── /*      → frontend/dist (Vite SPA)
```

## 레이어

### 데이터 레이어 — Neo4j 그래프

- `bolt://neo4j:7687`에서 실행, Docker named volume `neo4j_data`로 영속화.
- 노드 레이블: `Person`, `Place`, `Event`, `PeopleGroup`, `Book`.
- 주요 관계: `HAS_PARTICIPANT`(Event→Person), `OCCURS_AT`(Event→Place), `MEMBER_OF`(Person→PeopleGroup), `PART_OF`(Event→Event 계층), `CONTAINS_BOOK`(Book→Event, 구절 교집합으로 생성).
- 모든 노드에 `theographic_id` 인덱스(`CREATE INDEX ... ON (n.theographic_id)`) — 앱 기동 시 `lifespan` 훅에서 자동 생성(`backend/app/main.py`).
- 연결: `backend/app/db.py`의 `get_driver()` — 싱글톤 `neo4j.GraphDatabase.driver`, 환경변수 `NEO4J_URI`/`NEO4J_USER`/`NEO4J_PASSWORD`.

### 백엔드 레이어 — FastAPI

- 진입점: `backend/app/main.py`. `FastAPI` 앱에 4개 라우터 등록, CORS `GET` only.
- 라우터별 역할:
  - `nodes.py` — 단일 노드 조회 `/node/{id}`, 이웃 그룹 `/node/{id}/neighbors/grouped`, 장소 `/node/{id}/places`, 인물 참여 사건 ID `/person/{id}/event-ids`.
  - `events.py` — 타임라인 사건 목록 `/events`, 사건별 근거 구절 `/event/{id}/verses`.
  - `books.py` — 책 목록 `/books`.
  - `search.py` — 전문 검색 `/search?q=`.
- Neo4j 접근 방식: 라우터 함수에서 직접 `driver.session()` → Cypher 실행. ORM 없음.
- 캐싱: `events.py`의 `_compute_events()`, `_load_event_verses()`, `_load_approx_book_index()`는 `functools.lru_cache(maxsize=1)`. 앱 재시작 전까지 결과를 메모리에 보관. `/events` 응답에 `Cache-Control: max-age=300` 헤더.
- 런타임 오버레이: Neo4j에 저장하지 않는 추정 데이터(추정연도, 책-사건 연결, 사건 구절)는 JSON 파일로 `/app/data` 볼륨 마운트에서 로드해 응답에 병합. 탐색 경로: `DATA_DIR` 환경변수 → 레포 상대 경로 `data/` 순 폴백.

### 프론트엔드 레이어 — React SPA

- 빌드: Vite + `@vitejs/plugin-react`. 번들 분할: `maplibre-gl` → `maplibre` 청크, 나머지 `node_modules` → `vendor` 청크.
- API 클라이언트: `frontend/src/api.js` — `API_BASE`(빌드타임 `VITE_API_URL=/api`)로 단일화, `apiGet(path)` GET 헬퍼.
- 최상위 상태 관리: `App.jsx`가 `selectedNode`, `activeView`, `searchQuery`, `verseLang`, `personEventIds`, `history` 등을 `useState`로 보유. 프레임워크 없음, props/callback으로 자식에 전달.
- 뷰 라우팅: 탭 버튼 클릭으로 `activeView` 전환, 조건부 렌더링으로 세 뷰를 전환(`MapView`, `TimelineView`, `BibleOverviewView`). 라우터 라이브러리 미사용.

## 데이터 흐름

### 노드 선택 흐름

1. 사용자가 검색/맵 마커/타임라인 항목 클릭 → `App.selectNode(id)`.
2. `selectedNode` 상태 갱신 → `SidePanel`에 `nodeId` prop으로 전달.
3. `SidePanel`이 `GET /node/{id}` 호출 → Neo4j `MATCH (n {theographic_id: $id})` 조회.
4. 응답의 `label`이 `Person`이면 `App`에서 추가로 `GET /person/{id}/event-ids` 호출 → `personEventIds` Set 생성 → `TimelineView`에 전달해 필터링.
5. `MapView`도 `selectedNode` 변화 감지 → `GET /node/{id}/places` → 장소 마커 갱신 → Convex hull 렌더.

### 검색 흐름

1. 입력 이벤트 → 250ms 디바운스 AbortController 패턴.
2. `GET /search?q=` → Neo4j 전문 검색(nameKo CONTAINS / name toLower CONTAINS), 20건 제한.
3. 결과 드롭다운 표시 → 항목 선택 → `selectNode`.

### 타임라인 사건 흐름

1. `TimelineView` 마운트 시 `GET /events` 호출.
2. 응답: `sortKey ASC`로 정렬된 사건 배열 + 각 사건에 `books`(CONTAINS_BOOK 실제 권 + approx_index 추정권 병합).
3. 사건 클릭 → `GET /event/{id}/verses` → `data/event_verses/events.json` 오버레이에서 권별 절 목록 반환(textKo/textEn 사전 저장, 런타임 외부 fetch 없음).
4. `bookFilter`(Book 선택 시) 또는 `personFilter`(Person 선택 시 — personEventIds Set)로 클라이언트 측 필터링.

### 책 오버뷰 흐름

1. `BibleOverviewView` 마운트 시 `GET /books` 호출.
2. Neo4j Book 노드 + `data/book_years_approx/books.json`(추정연도) + `data/book_events/books.json`(책-사건 연결) 병합.
3. 장르별 그리드로 렌더. 카드 클릭 → `selectNode`.

## 핵심 추상

- **theographic_id**: 모든 엔티티의 안정 키. `rec` 접두 14자 문자열(Airtable origin). 저작 사건은 `authored-<slug>`.
- **오버레이 패턴**: 권위 낮은 추정 데이터(추정연도·book_events·event_verses·authored_events)는 Neo4j에 주입하지 않고 JSON 파일로 분리, 런타임에 Neo4j 응답과 병합. `lru_cache`로 1회 로드.
- **authored flag**: 저작 사건(`authored_events/`)은 Neo4j `Event` 노드로 적재하되 `authored=true` 마킹 → TimelineView에서 `추정` 배지 표시.
- **CONTAINS_BOOK**: Book↔Event 연결의 유일한 권위 축. 구절 교집합(`load_books.py`)으로 생성. 추정 book_events 오버레이와 의미 분리.

## 프론트엔드-백엔드 통신

- 프로토콜: HTTP GET + JSON only. CORS `allow_methods=["GET"]`.
- 프로덕션: nginx `/api/*` 프록시 → `api:8000`. `VITE_API_URL=/api` 빌드타임 환경변수로 주입(`frontend/.env.production`).
- 개발: `VITE_API_URL` 미설정 시 `api.js`가 `http://localhost:8000`으로 직접 연결.
- 오류 처리: `apiGet`이 non-OK 응답을 `Error`로 reject(`err.status` 부착). 호출부가 `.catch()`에서 처리. `AbortError`는 컴포넌트 언마운트/재요청 취소로 무시.

## 데이터 적재 파이프라인 (일회성 스크립트)

`backend/scripts/`에 위치. Docker 서비스 밖에서 직접 실행.

1. `load_theographic.py` — Theographic GitHub JSON(people/places/events/peopleGroups) → Neo4j 노드·관계 일괄 적재.
2. `load_books.py` — 책 노드 적재 + CONTAINS_BOOK 관계 생성(구절 교집합).
3. `inject_ko_names.py` — `data/names_ko/` JSON → nameKo 속성 주입.
4. `inject_person_traits.py` / `inject_book_context.py` — LLM 생성 데이터 → Neo4j 속성 주입.
5. `load_authored_events.py` — `data/authored_events/events.json` → Neo4j `Event` 노드 (authored=true).
6. `load_verse_events.py` — `data/verse_events/` → Neo4j 관계.
7. LLM 생성 스크립트(`generate_*.py`) — Claude API 직접 호출해 JSON 생성, `data/` 하위에 저장.
