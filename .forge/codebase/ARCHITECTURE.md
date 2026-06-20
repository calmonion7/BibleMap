---
last_mapped_commit: cecf0d7de87192b638f428eb7e708e94a58214a6
mapped: 2026-06-20
---
# Architecture

**Analysis Date:** 2026-06-20

## System Overview

```text
┌──────────────────────────────────────────────────────────────┐
│                    Browser (React SPA)                        │
│  App.jsx — 탭 라우팅, 검색 오버레이, 노드 선택 상태 루트     │
├──────────────┬───────────────┬──────────────┬────────────────┤
│  MapView     │ TimelineView  │BibleOverview │  SidePanel     │
│ .jsx (481)   │  .jsx (353)   │View.jsx(198) │  .jsx (348)    │
└──────┬───────┴───────┬───────┴──────┬───────┴────────┬───────┘
       │               │              │                │
       └───────────────┴──────────────┴────────────────┘
                              │ apiGet()
                   frontend/src/api.js
                              │ HTTP GET /api/*
                              ▼
┌──────────────────────────────────────────────────────────────┐
│              nginx:8080  (reverse proxy /api/ → api:8000)    │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│           FastAPI (backend/app/main.py)                       │
├────────────┬──────────────┬───────────────┬──────────────────┤
│ routes/    │ routes/      │ routes/       │ routes/          │
│ nodes.py   │ events.py    │ search.py     │ books.py         │
└────────────┴──────┬───────┴───────────────┴──────────────────┘
                    │             │
            backend/app/db.py    overlays.py
                    │             │
                    ▼             ▼
             Neo4j (bolt)     data/ JSON 파일
             docker service    (book_events, event_verses,
                                book_years_approx)
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| `App` | 탭 전환, 검색 오버레이, 노드 선택 전달 | `frontend/src/App.jsx` |
| `useNodeSelection` | 선택 노드 상태, 히스토리, Person event-id fetch | `frontend/src/useNodeSelection.js` |
| `useSearch` | 검색 입력 디바운스, AbortController 경쟁 차단, 타입 필터 | `frontend/src/useSearch.js` |
| `MapView` | MapLibre 지도, 장소 마커, 사건 방사형 링, convex hull | `frontend/src/MapView.jsx` |
| `TimelineView` | 사건 시간축, 그룹 펼침, 구절 인라인 뷰, 필터 배너 | `frontend/src/TimelineView.jsx` |
| `BibleOverviewView` | 성경 66권 장르별 카드 그리드 | `frontend/src/BibleOverviewView.jsx` |
| `SidePanel` | 노드 상세 패널 (데스크톱: 우측 슬라이드인, 모바일: 하단 시트) | `frontend/src/SidePanel.jsx` |
| `VerseLangTabs` | ko/en 언어 탭 UI (TimelineView·SidePanel 공유) | `frontend/src/VerseLangTabs.jsx` |
| `api.js` | `apiGet(path)` 단일 fetch 헬퍼, VITE_API_URL 기반 | `frontend/src/api.js` |
| `theme.js` | TYPE_COLOR, TYPE_KO, TYPE_ORDER, SELECT_HL 공유 팔레트 | `frontend/src/theme.js` |
| `convexHull.js` | Graham scan 알고리즘, MapView 전용 | `frontend/src/convexHull.js` |
| `main.py` | FastAPI 앱 생성, lifespan Neo4j 인덱스, 라우터 등록 | `backend/app/main.py` |
| `db.py` | Neo4j 드라이버 싱글톤 (`_driver` 전역) | `backend/app/db.py` |
| `overlays.py` | JSON 오버레이 로더 (`lru_cache(maxsize=1)` 캐시) | `backend/app/overlays.py` |
| `routes/nodes.py` | `/node/{id}`, `/node/{id}/places`, `/node/{id}/neighbors/grouped`, `/person/{id}/event-ids` | `backend/app/routes/nodes.py` |
| `routes/events.py` | `/events`(lru_cache), `/event/{id}/verses` | `backend/app/routes/events.py` |
| `routes/search.py` | `/search?q=` Neo4j 전문 검색 | `backend/app/routes/search.py` |
| `routes/books.py` | `/books`(타임라인용), `/books-overview`(개요 뷰용) | `backend/app/routes/books.py` |

## Pattern Overview

**Overall:** 3-tier — React SPA / FastAPI REST / Neo4j + JSON 오버레이

**Key Characteristics:**
- 프론트엔드 상태는 `App.jsx`에서 두 커스텀 훅(`useNodeSelection`, `useSearch`)으로 분리 관리. 하위 뷰는 props로만 수신.
- 백엔드에 global mutable singleton(`_driver`, `lru_cache` 결과). 앱 재시작 전까지 캐시 유효.
- Neo4j 원장 데이터 + 로컬 JSON 오버레이 2중 소스. 오버레이는 Neo4j에 없는 연결 정보(추정 연도, 사건-구절 매핑)를 보완.

## Layers

**Frontend 상태 훅:**
- Purpose: App 레벨 공유 상태 캡슐화
- Location: `frontend/src/useNodeSelection.js`, `frontend/src/useSearch.js`
- Contains: useState, useEffect, useCallback, useRef
- Depends on: `api.js`
- Used by: `App.jsx`만 직접 호출, 결과를 props로 하위 뷰에 전달

**Frontend 뷰 컴포넌트:**
- Purpose: 탭별 독립 렌더링
- Location: `frontend/src/MapView.jsx`, `frontend/src/TimelineView.jsx`, `frontend/src/BibleOverviewView.jsx`
- Contains: 각 뷰 전용 fetch 및 렌더 로직
- Depends on: `api.js`, `theme.js`, 전달된 props
- Used by: `App.jsx`

**Frontend 공유 유틸리티:**
- Purpose: 여러 컴포넌트가 공유하는 상수·함수
- Location: `frontend/src/theme.js`, `frontend/src/api.js`, `frontend/src/convexHull.js`, `frontend/src/VerseLangTabs.jsx`
- Depends on: 없음

**Backend 라우터 레이어:**
- Purpose: HTTP 엔드포인트 정의 및 응답 직렬화
- Location: `backend/app/routes/`
- Depends on: `db.py`, `overlays.py`
- Used by: `main.py`에서 `include_router`로 등록

**Backend 데이터 접근 레이어:**
- Purpose: Neo4j 드라이버 싱글톤 + JSON 오버레이 캐시
- Location: `backend/app/db.py`, `backend/app/overlays.py`
- Depends on: 환경변수(`NEO4J_URI`, `NEO4J_PASSWORD`), `data/` 마운트 경로

## Data Flow

### 노드 선택 → 사이드 패널 표시

1. 사용자가 MapView 마커 클릭 → `onSelectNode(id)` 호출 (`frontend/src/App.jsx`)
2. `useNodeSelection.selectNode(id)` — 이전 노드를 `history`에 push, `selectedNode` 업데이트 (`frontend/src/useNodeSelection.js:33`)
3. `SidePanel` props `nodeId` 변경 → `useEffect` 실행 → `apiGet('/node/' + nodeId)` (`frontend/src/SidePanel.jsx:53`)
4. `GET /node/{id}` — Neo4j에서 노드 + 이웃 쿼리, Book이면 topPersons/topEvents 추가 (`backend/app/routes/nodes.py:145`)
5. `onNodeLoaded(data)` 콜백 → `useNodeSelection.handleNodeLoaded` — `selectedNodeMeta` 업데이트, Person이면 `/person/{id}/event-ids` 추가 fetch (`frontend/src/useNodeSelection.js:13`)

### 검색 → 결과 선택

1. 사용자 입력 → `useSearch.onSearchInput` → `searchQuery` 업데이트 (`frontend/src/useSearch.js:54`)
2. `useEffect([searchQuery])` — 250ms 디바운스 + AbortController — `apiGet('/search?q=...')` (`frontend/src/useSearch.js:17`)
3. `App.handleSelectResult` — `clearSearch()` + `selectNodeFresh(id)` (히스토리 리셋) (`frontend/src/App.jsx:57`)

### 타임라인 이벤트 로드

1. `TimelineView` 마운트 → `apiGet('/events')` (`frontend/src/TimelineView.jsx:47`)
2. `GET /events` — `_compute_events()` lru_cache 히트 또는 Neo4j 쿼리 + `overlays.approx_years()` 머지 (`backend/app/routes/events.py:54`)
3. 사건 클릭 → `apiGet('/event/{id}/verses')` — `overlays.event_verses()` JSON 반환 (`backend/app/routes/events.py:99`)

**State Management:**
- 전역 React 상태 없음. `App.jsx`가 두 훅의 결과를 소유하며 props drilling으로 하위에 전달.
- 백엔드 캐시: `db.py`의 `_driver` (프로세스 전역), `overlays.py`의 세 함수(lru_cache), `events.py`의 `_compute_events()`(lru_cache).

## Key Abstractions

**apiGet:**
- Purpose: 모든 프론트 fetch를 단일 경로로 라우팅. VITE_API_URL로 프로덕션/개발 분기.
- Examples: `frontend/src/api.js`
- Pattern: `async function apiGet(path, { signal } = {})` — 비-OK 응답은 `err.status` 포함 throw

**overlays.py:**
- Purpose: Neo4j에 없는 오버레이 데이터를 JSON 파일에서 lru_cache로 1회 로드
- Examples: `backend/app/overlays.py`
- Pattern: `@functools.lru_cache(maxsize=1)` 데코레이터 + `_resolve(subpath)` 경로 탐색(DATA_DIR 환경변수 → repo 기본값 fallback)

**useNodeSelection:**
- Purpose: 선택 노드 상태, 탐색 히스토리, Person 이벤트 ID 세트를 단일 훅으로 캡슐화
- Examples: `frontend/src/useNodeSelection.js`
- Pattern: `selectNode`를 `useCallback([])` 안정화(ref로 최신값 읽음) → MapView의 expandPlace fetch abort 버그 방지

## Entry Points

**Frontend:**
- Location: `frontend/src/main.jsx`
- Triggers: `createRoot(document.getElementById('root')).render(<App />)`
- Responsibilities: React StrictMode 래핑만

**Backend:**
- Location: `backend/app/main.py`
- Triggers: uvicorn이 `app` 객체를 임포트
- Responsibilities: lifespan 훅에서 Neo4j 인덱스 생성, 라우터 4개 등록, CORS 미들웨어(GET만 허용)

## Architectural Constraints

- **Global state:** `backend/app/db.py` — `_driver` 프로세스 전역 싱글톤. `overlays.py`의 lru_cache 3개. `events.py`의 `_compute_events` lru_cache.
- **Cache invalidation:** 앱 프로세스 재시작 전까지 오버레이·이벤트 캐시는 갱신되지 않음. `docker compose up -d --build api`로 재시작 필요.
- **CORS:** `allow_methods=["GET"]` 전용. 쓰기 엔드포인트 없음.
- **빌드 모델:** 프론트엔드는 HMR 아님 — `frontend/dist`를 nginx가 정적 서빙. 검증 전 `npm run build` 필수.
- **데이터 마운트:** `data/` 디렉터리가 Docker volume으로 `/app/data`에 바인드 마운트됨 (`docker-compose.yml:19`).

## Anti-Patterns

### App.jsx에 검색 드롭다운 렌더 로직 인라인 존재

**What happens:** `useSearch` 훅으로 상태는 분리됐지만 드롭다운 JSX(타입 필터 칩, 결과 목록)가 `App.jsx` 안에 직접 작성됨.
**Why it's wrong:** `App.jsx`가 이미 278줄이고 검색 UI 변경이 앱 루트 파일을 건드림.
**Do this instead:** 검색 드롭다운을 별도 컴포넌트(`SearchDropdown.jsx`)로 분리, `frontend/src/` 위치.

### lru_cache(maxsize=1) 런타임 캐시에 의존

**What happens:** `_compute_events()`가 앱 재시작 전까지 Neo4j 결과를 메모리에 보관.
**Why it's wrong:** Neo4j 직접 수정 후 캐시 무효화 수단이 없음.
**Do this instead:** `_compute_events.cache_clear()` 수동 호출 엔드포인트 추가, 또는 TTL 기반 캐시 사용 — `backend/app/routes/events.py:54`.

## Error Handling

**Strategy:** 낙관적 렌더링 + 에러 상태 플래그

**Patterns:**
- `apiGet` throw → 각 컴포넌트의 `setError(true)` or `setError(e?.status)` — 사용자에게 배너/인라인 메시지 표시
- `SidePanel`: `state.error`에 HTTP status 저장 (`frontend/src/SidePanel.jsx:55`)
- 백엔드: Neo4j 인덱스 생성 실패는 `logging.exception`으로 기록 후 계속 진행 (`backend/app/main.py:19`)
- AbortError는 `useSearch`에서 명시적 무시 (`frontend/src/useSearch.js:28`)

## Cross-Cutting Concerns

**Logging:** 백엔드 `logging.exception` (표준 라이브러리). 프론트엔드 로깅 없음.
**Validation:** 백엔드 FastAPI Query 타입 검증만. 추가 입력 검증 없음.
**Authentication:** 없음. CORS GET-only.

---

*Architecture analysis: 2026-06-20*
