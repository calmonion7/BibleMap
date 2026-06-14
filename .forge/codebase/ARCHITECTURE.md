---
last_mapped_commit: fb78d740df63d386e84ceb1bb4249921a5e198b7
mapped: 2026-06-14
---

# Architecture

**Analysis Date:** 2026-06-14

## System Overview

```text
┌──────────────────────────────────────────────────────────────┐
│                    Browser (React SPA)                        │
│  App.jsx — 전역 상태(selectedNode, searchQuery, activeView)   │
├────────────┬─────────────┬──────────────┬────────────────────┤
│ MapView    │ TimelineView│  GraphView   │  SidePanel         │
│ .jsx       │ .jsx        │  .jsx        │  .jsx              │
└─────┬──────┴──────┬──────┴──────┬───────┴────────┬───────────┘
      │             │             │                │
      └─────────────┴─────────────┴────────────────┘
                          │ apiGet() via api.js
                          ▼
┌──────────────────────────────────────────────────────────────┐
│              nginx (port 8080)                                │
│  /api/* → proxy_pass http://api:8000/                        │
│  /*      → frontend/dist (static SPA)                        │
└──────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────────┐
│         FastAPI (uvicorn, port 8000)                          │
│   backend/app/main.py                                         │
├──────────────┬───────────────┬──────────────────────────────┤
│  routes/     │  routes/      │  routes/                      │
│  nodes.py    │  events.py    │  search.py                    │
└──────┬───────┴───────────────┴──────────────────────────────┘
       │ neo4j Python driver (bolt)
       ▼
┌──────────────────────────────────────────────────────────────┐
│              Neo4j 5 (bolt://neo4j:7687)                      │
│  Node labels: Person, Place, Event, PeopleGroup               │
│  Key property: theographic_id (indexed per label)             │
└──────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| `App` | 전역 상태 관리(selectedNode, activeView, searchQuery, history), 검색 디바운스, 탭 라우팅, 패널 오버레이 | `frontend/src/App.jsx` |
| `MapView` | maplibre-gl 지도, 장소 마커 레이어, 사건 링 애니메이션(requestAnimationFrame) | `frontend/src/MapView.jsx` |
| `TimelineView` | `/events` 전체 목록 fetch, startDate별 그룹핑, 정렬 후 타임라인 렌더링 | `frontend/src/TimelineView.jsx` |
| `GraphView` | cytoscape + cose-bilkent + expand-collapse 플러그인, 이웃 그래프 시각화 | `frontend/src/GraphView.jsx` |
| `SidePanel` | 선택된 nodeId의 `/node/{id}` fetch, 이웃을 타입별로 그룹 렌더링, 뒤로가기 | `frontend/src/SidePanel.jsx` |
| `api.js` | 단일 `apiGet(path, {signal})` 헬퍼, `VITE_API_URL` 기반 베이스 URL 관리 | `frontend/src/api.js` |
| `theme.js` | `TYPE_COLOR`, `TYPE_KO`, `TYPE_ORDER`, `SELECT_HL` — 뷰 공유 팔레트 | `frontend/src/theme.js` |
| `routes/nodes.py` | `/node/{id}`, `/node/{id}/places`, `/node/{id}/neighbors/grouped` | `backend/app/routes/nodes.py` |
| `routes/events.py` | `/events` — 전체 Event 목록(sortKey 정렬) | `backend/app/routes/events.py` |
| `routes/search.py` | `/search?q=` — nameKo/name 포함 검색, 관련도 rank 정렬 | `backend/app/routes/search.py` |
| `db.py` | Neo4j 드라이버 모듈 싱글톤(`_driver`), 환경변수로 bolt URI/auth 설정 | `backend/app/db.py` |
| `main.py` | FastAPI 앱 초기화, CORS 미들웨어(GET only), lifespan에서 인덱스 생성 | `backend/app/main.py` |

## Pattern Overview

**Overall:** 3-tier — React SPA / FastAPI REST / Neo4j

**Key Characteristics:**
- 프론트엔드: 탭 기반 단일 페이지, 전역 상태를 `App.jsx`가 소유하고 뷰에 props로 내림
- 백엔드: stateless REST(GET only), 각 라우터가 Neo4j 세션을 직접 열고 닫음
- 데이터베이스: 그래프 DB — 노드(Person/Place/Event/PeopleGroup)와 관계(HAS_PARTICIPANT, OCCURS_AT, MEMBER_OF 등)

## Layers

**Frontend — Presentation:**
- Purpose: 사용자 인터랙션, 시각화 렌더링
- Location: `frontend/src/`
- Contains: React 컴포넌트, 공유 유틸(`api.js`, `theme.js`)
- Depends on: FastAPI REST API (`/api/*` via nginx 프록시)
- Used by: 브라우저

**Frontend — Shared Utilities:**
- Purpose: API fetch 추상화, 색·라벨 팔레트
- Location: `frontend/src/api.js`, `frontend/src/theme.js`
- Contains: `apiGet()` 함수, `TYPE_COLOR`, `TYPE_KO`, `TYPE_ORDER`, `SELECT_HL`, `typeColor()`, `typeKo()`
- Depends on: 없음 (순수 JS 모듈)
- Used by: `App.jsx`, `MapView.jsx`, `SidePanel.jsx`, `GraphView.jsx`, `TimelineView.jsx`

**Backend — API:**
- Purpose: HTTP 라우팅, Cypher 실행, JSON 직렬화
- Location: `backend/app/`
- Contains: FastAPI 라우터 3개, db 모듈
- Depends on: Neo4j 드라이버
- Used by: nginx 프록시를 통해 프론트엔드

**Backend — Data Scripts (one-time):**
- Purpose: Theographic 데이터 Neo4j 적재, 한국어 이름 주입
- Location: `backend/scripts/`
- Contains: `load_theographic.py`, `inject_ko_names.py`
- Depends on: Neo4j 드라이버, `data/names_ko/` JSON 파일
- Used by: 운영자가 직접 실행 (서버 런타임과 무관)

**Data:**
- Purpose: 한국어 이름 오버라이드 소스
- Location: `data/names_ko/` (`events.json`, `groups.json`, `people.json`, `places.json`)
- Contains: theographic_id → 한국어 이름 매핑 JSON
- Depends on: 없음
- Used by: `backend/scripts/inject_ko_names.py`

## Data Flow

### 노드 선택 흐름 (MapView 마커 클릭)

1. 사용자가 MapView 마커 클릭 → `places-circle` 레이어 click 이벤트 (`frontend/src/MapView.jsx`)
2. `expandPlace(placeId, lng, lat)` 호출 → `GET /node/{placeId}/neighbors/grouped` (`frontend/src/api.js`)
3. 이웃 이벤트로 사건 링 애니메이션 실행 (`requestAnimationFrame` 루프, `frontend/src/MapView.jsx`)
4. `onSelectNode(placeId)` 호출 → `App.jsx`의 `selectNode(id)` → `setSelectedNode(id)`
5. `SidePanel`이 `nodeId` prop 수신 → `GET /node/{nodeId}` (`frontend/src/SidePanel.jsx`)
6. FastAPI `get_node()` → Neo4j 세션 열기, 노드 + 이웃 50건 + 전체 count 조회 (`backend/app/routes/nodes.py`)
7. SidePanel이 이웃을 타입별로 그룹핑 후 렌더링

### 검색 흐름

1. 사용자 입력 → `onSearchInput` → `setSearchQuery(v)` (`frontend/src/App.jsx`)
2. useEffect 250ms 디바운스 + AbortController로 이전 요청 취소
3. `GET /search?q=...` → FastAPI `search()` → Cypher CONTAINS + rank 정렬 (`backend/app/routes/search.py`)
4. 드롭다운 결과 표시, 타입 필터 칩 렌더링
5. 결과 클릭 → `handleSelectResult()` → `setSelectedNode(result.id)` (히스토리 리셋)

### 지도 초기화 흐름 (selectedNode 변경)

1. `selectedNode` prop 변경 → MapView useEffect 실행
2. `GET /node/{selectedNode}/places` → 좌표 있는 장소 목록 반환
3. `places-source` GeoJSON 업데이트 → maplibre-gl 마커 레이어 갱신
4. 장소가 없으면 `setNoLocation(true)` → 안내 메시지 표시
5. 장소가 있고 Place 타입이면 `expandPlace()` 자동 호출 → 링 펼침

**State Management:**
- `selectedNode` (string | null): App.jsx 소유, props로 MapView/TimelineView/GraphView/SidePanel에 전달
- `history` (string[]): 뒤로가기 스택, App.jsx 소유
- `activeView` ('map' | 'timeline' | 'graph'): App.jsx 소유
- `searchQuery`, `searchResults`, `typeFilter`: App.jsx 소유
- Map 내부 상태(expandedPlace, animFrame 등): MapView 내 mutable refs (React state 아님 — 리렌더 방지)
- GraphView overlay: GraphView 지역 state

## Key Abstractions

**`apiGet(path, {signal})`:**
- Purpose: 모든 프론트 fetch의 단일 진입점. non-OK 시 `throw status`
- Examples: `frontend/src/api.js`
- Pattern: `export async function apiGet(path, { signal } = {}) { ... }`

**`TYPE_COLOR` / `typeColor(label)`:**
- Purpose: 노드 타입 → 색 매핑 단일 정규 팔레트 (이전에 각 뷰가 별도로 정의해 충돌)
- Examples: `frontend/src/theme.js`
- Pattern: `import { TYPE_COLOR, typeColor } from './theme'` — 모든 뷰가 이 모듈을 공유

**Neo4j `theographic_id`:**
- Purpose: 모든 엔티티의 안정 식별자 (영문명은 동명이인 존재)
- Examples: `backend/app/routes/nodes.py` (모든 `MATCH (n {theographic_id: $id})`)
- Pattern: 각 라벨에 인덱스 생성 (`main.py` lifespan), 모든 조회는 이 속성 기준

**`selectedNodeRef`:**
- Purpose: `selectNode` useCallback이 `[]` deps로 참조 안정화하면서도 최신 `selectedNode` 값을 읽기 위한 패턴
- Examples: `frontend/src/App.jsx` (`selectedNodeRef.current`)
- Pattern: `useEffect(() => { selectedNodeRef.current = selectedNode }, [selectedNode])`

## Entry Points

**Frontend (개발):**
- Location: `frontend/src/main.jsx`
- Triggers: `vite dev`
- Responsibilities: React root 생성, `App` 마운트

**Frontend (프로덕션):**
- Location: `frontend/dist/index.html` (빌드 결과물)
- Triggers: nginx `try_files $uri /index.html`
- Responsibilities: SPA 진입, 정적 자산 서빙

**Backend:**
- Location: `backend/app/main.py` (`app` 객체)
- Triggers: `uvicorn app.main:app` (Docker CMD)
- Responsibilities: FastAPI 앱 초기화, CORS, 라우터 등록, lifespan 인덱스 생성

## Architectural Constraints

- **CORS:** `allow_origins=["*"]`, `allow_methods=["GET"]` — 읽기 전용 API. 쓰기 엔드포인트 없음 (`backend/app/main.py`)
- **Neo4j 드라이버:** 모듈 수준 싱글톤 `_driver` (`backend/app/db.py`). 각 요청마다 `driver.session()` 컨텍스트 매니저 사용.
- **핫리로드 없음:** 백엔드는 코드 변경 시 `docker compose up -d --build api` 재빌드 필요.
- **GraphView는 SidePanel 없음:** `activeView === 'graph'`일 때 SidePanel 오버레이가 렌더링되지 않음 (`frontend/src/App.jsx` 306행).
- **이웃 수 상한:** `NODE_NEIGHBOR_LIMIT = 50` (GET /node/{id}), `MAX_NEIGHBORS_PER_TYPE = 30` (GET /node/{id}/neighbors/grouped) (`backend/app/routes/nodes.py`).
- **검색 결과 상한:** `SEARCH_LIMIT = 20` (`backend/app/routes/search.py`).

## Anti-Patterns

### 타입별 색을 각 뷰에서 독립 선언 (해결됨)

**What happens:** 이전에 `App.jsx`, `SidePanel.jsx`, `GraphView.jsx`가 각자 색 상수를 선언했음
**Why it's wrong:** GraphView의 색 값이 달라 같은 타입이 뷰마다 다른 색으로 표시됨
**Do this instead:** `frontend/src/theme.js`에서 `import { TYPE_COLOR, typeColor } from './theme'`

### MapView 내부 상태를 React state로 관리

**What happens:** 지도 렌더링 루프 변수(animFrame, expandedPlace 등)를 React state로 두면 매 프레임 리렌더 발생
**Why it's wrong:** 60fps 애니메이션에서 React reconciler 오버헤드로 성능 저하
**Do this instead:** mutable refs(`useRef`) 사용 — `frontend/src/MapView.jsx` 25-27행 패턴 참조

## Error Handling

**Strategy:** 각 컴포넌트가 개별적으로 fetch 실패를 로컬 error state로 처리

**Patterns:**
- `SidePanel`: `state.error` 있으면 오류 메시지 렌더링 (`frontend/src/SidePanel.jsx`)
- `MapView`: `error` state → 오류 배너(네비게이션 바 뒤 가려짐 이슈 미해결), `noLocation` state → 빈 위치 안내
- `GraphView`: `error` state → 전체화면 오버레이 오류 메시지
- `TimelineView`: `error` state → 전체화면 오류 메시지
- `App` 검색: `searchError` state → 드롭다운 내 오류 메시지, AbortError는 무시
- `apiGet`: non-OK → `throw res.status` (숫자), AbortError → 그대로 전파

## Cross-Cutting Concerns

**Logging:** 백엔드 Python 기본 logging (`logging.exception`). 프론트엔드 로깅 없음.
**Validation:** 없음. 백엔드는 입력을 Neo4j 파라미터 바인딩으로 전달 (SQL-injection 유사 문제 없음).
**Authentication:** 없음. 공개 읽기 전용 서비스.
**Mobile:** `App.jsx`의 `MOBILE_QUERY = '(max-width: 768px)'`로 분기 — 768px 이하에서 SidePanel을 하단 시트로 전환.

---

*Architecture analysis: 2026-06-14*
