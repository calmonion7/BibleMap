---
last_mapped_commit: 7522aafe2088e83e8c4bed86a4f0269082db07e0
mapped: 2026-06-20
---

# 아키텍처

## 전체 구조

BibleMap은 3티어 구조다: **프론트엔드(React SPA) — API 서버(FastAPI) — 그래프 DB(Neo4j)**. nginx가 리버스 프록시로 정적 빌드 파일과 API를 단일 포트(8080)로 노출한다.

```
┌──────────────────────────────────────────────────────────┐
│            브라우저 (React SPA, :8080)                   │
│  App.jsx → [MapView | TimelineView | BibleOverviewView]  │
│              └── SidePanel (오버레이)                    │
└──────────────┬───────────────────────────────────────────┘
               │ HTTP /api/...  (nginx proxy_pass → :8000)
┌──────────────▼───────────────────────────────────────────┐
│            FastAPI (uvicorn, :8000)                      │
│  routes/nodes.py · events.py · books.py · search.py     │
│              └── overlays.py (JSON 파일 캐시)            │
└──────────────┬───────────────────────────────────────────┘
               │ Bolt :7687
┌──────────────▼───────────────────────────────────────────┐
│            Neo4j 5 (그래프 DB)                           │
│  노드: Person · Place · Event · PeopleGroup · Book       │
│  관계: HAS_PARTICIPANT · OCCURS_AT · MEMBER_OF           │
│        CONTAINS_BOOK · PARENT_OF · CHILD_OF 등           │
└──────────────────────────────────────────────────────────┘
               ↑
         data/ (JSON 오버레이 파일)
         scripts/ (Neo4j 적재 · 데이터 생성 스크립트)
```

## 패턴: 라우터 레이어 + 오버레이 캐시

백엔드는 별도 서비스/리포지터리 계층 없이 라우터가 직접 Neo4j 세션을 열고 쿼리를 실행한다. 오버레이 데이터(JSON 파일)는 `overlays.py`에서 `functools.lru_cache`로 프로세스 수명 동안 메모리에 유지한다.

### 백엔드 레이어

**라우터 레이어** (`backend/app/routes/`):
- `nodes.py` — 노드 상세 조회(`/node/{id}`), 장소 조회(`/node/{id}/places`), 이웃 조회(`/node/{id}/neighbors/grouped`), 인물 이벤트 ID 목록(`/person/{id}/event-ids`)
- `events.py` — 타임라인 사건 목록(`/events`), 사건별 근거 구절(`/event/{id}/verses`). `_compute_events()`는 `lru_cache`로 1회만 Neo4j를 쿼리한다.
- `books.py` — 타임라인용 성경책 목록(`/books`), 개요용 성경책 목록(`/books-overview`)
- `search.py` — 전문 검색(`/search?q=`)

**DB 레이어** (`backend/app/db.py`):
- 모듈 전역 싱글턴 `_driver`를 `get_driver()`로 지연 초기화한다.
- `NEO4J_URI` / `NEO4J_USER` / `NEO4J_PASSWORD` 환경변수로 연결 설정.

**오버레이 레이어** (`backend/app/overlays.py`):
- `DATA_DIR` 환경변수(컨테이너: `/app/data`) 또는 저장소 루트 `data/` 를 순서대로 탐색한다.
- `book_events_raw()`, `approx_years()`, `event_verses()` — 각각 `lru_cache(maxsize=1)`.

**앱 진입점** (`backend/app/main.py`):
- `lifespan` 컨텍스트 매니저에서 Neo4j 인덱스 5종을 `IF NOT EXISTS`로 보장한다.
- CORS 설정: `allow_origins=["*"]`, `allow_methods=["GET"]`. GET 전용 읽기 전용 API.

### 프론트엔드 레이어

**진입점** (`frontend/src/main.jsx` → `App.jsx`):
- React 19, Vite 빌드. `StrictMode` 적용.

**전역 상태 관리** (`frontend/src/App.jsx`):
- 뷰 탭 상태(`activeView`: `'map'|'timeline'|'overview'`)
- 노드 선택 상태는 `useNodeSelection` 훅으로 위임.
- 검색 상태는 `useSearch` 훅으로 위임.
- `verseLang('ko'|'en')` — 절 본문 언어. `SidePanel`과 `TimelineView`가 공유하는 유일한 앱 수준 UI 상태.
- 모바일 분기(`isMobile`) — `window.matchMedia('(max-width: 768px)')` 변화 감지.
- 세 뷰는 항상 마운트된 채 CSS `display` 토글로 상태를 보존한다(`unmount 없음`).

**커스텀 훅**:

`useNodeSelection` (`frontend/src/useNodeSelection.js`):
- `selectedNode`, `history`, `selectedNodeMeta`, `personEventIds` 관리.
- `selectNode(id)` — 직전 노드를 히스토리에 쌓고 교체. `useCallback([])` + `selectedNodeRef`로 참조 안정화(MapView `useEffect` 재실행 방지).
- `selectNodeFresh(id)` — 히스토리 리셋 후 선택(검색 결과 클릭 경로).
- `handleNodeLoaded(node)` — SidePanel이 노드 상세를 받으면 콜백으로 메타 정보 수신. `Person`이면 `/person/{id}/event-ids` 추가 fetch.

`useSearch` (`frontend/src/useSearch.js`):
- 250ms 디바운스 + `AbortController`로 경쟁 요청 차단.
- `typeFilter` — 검색 결과 타입 필터(Person/Place/Event/PeopleGroup).

**뷰 컴포넌트**:

`MapView` (`frontend/src/MapView.jsx`):
- MapLibre GL JS 5.x 지도. ESRI NatGeo 래스터 타일 기반.
- `selectedNode` 변경 시 `/node/{id}/places`를 fetch해 GeoJSON 마커를 갱신한다.
- 장소 클릭 → `expandPlace()` 비동기 함수가 `/node/{placeId}/neighbors/grouped`로 이벤트를 가져와 방사형 링(radial ring) 애니메이션을 실행한다. `requestAnimationFrame` 루프 기반.
- Person 선택 시 좌표 3개 이상이면 볼록 껍질(convex hull) 폴리곤을 `hull-source`에 그린다.
- `isVisible` prop 변경 시 `map.resize()`를 호출해 CSS 숨김 탭에서 전환될 때 지도 크기를 보정한다.

`TimelineView` (`frontend/src/TimelineView.jsx`):
- 마운트 시 `/events` 1회 fetch. 이후 `useMemo`로 날짜별 그룹 계산.
- `bookFilter` prop — 선택된 `Book` 노드의 `startYear`/`endYear`로 연도 범위 필터.
- `personFilter` prop — 선택된 `Person`의 이벤트 ID Set으로 해당 인물이 참여한 사건만 필터.
- 사건 행의 📖 칩 클릭 → `/event/{id}/verses` fetch 후 인라인 구절 뷰 표시. 한 번에 한 사건만 열림.
- 선택 사건 자동 스크롤: `selectedNode`가 이벤트 ID이면 `groupRefs`로 해당 그룹을 `scrollIntoView`.

`BibleOverviewView` (`frontend/src/BibleOverviewView.jsx`):
- `/books-overview`를 1회 fetch. OT/NT 분리, 장르별 그룹(`OT_GENRE_ORDER`, `NT_GENRE_ORDER`) 가로 스크롤 카드 배열.

`SidePanel` (`frontend/src/SidePanel.jsx`):
- `/node/{id}` fetch. `nodeId` prop 변화 시 재요청. `cancelled` 플래그로 stale 응답 무시.
- Book 노드는 별도 레이아웃(메타 칩, 시대적 배경, 핵심 주제, 대표 구절, 주요 인물, 주요 사건).
- Person 노드는 traits 섹션 + 이웃 그룹. Book 제외 나머지는 타입별 이웃 그룹만 표시.
- `onNodeLoaded` 콜백으로 `useNodeSelection` 훅에 메타 정보를 역으로 전달한다.

**공유 모듈**:
- `api.js` — `API_BASE`(`VITE_API_URL` 환경변수 또는 `http://localhost:8000`)와 `apiGet(path, {signal})` 함수. 모든 fetch의 단일 진입점.
- `theme.js` — `TYPE_COLOR`, `TYPE_KO`, `TYPE_ORDER`, `typeColor()`, `typeKo()`, `SELECT_HL`. 모든 뷰가 공유하는 색/라벨 팔레트.
- `convexHull.js` — Graham scan 볼록 껍질 알고리즘(MapView 전용).
- `Spinner.jsx` — CSS 애니메이션 스피너(SidePanel, TimelineView, BibleOverviewView).
- `VerseLangTabs.jsx` — 한국어/영어 절 본문 전환 버튼(SidePanel, TimelineView 공유).

## API 엔드포인트 목록

| 메서드 | 경로 | 설명 | 캐시 |
|--------|------|------|------|
| GET | `/node/{node_id}` | 노드 상세 + 이웃 + Book 전용 필드 | 없음 |
| GET | `/node/{node_id}/places` | 노드 관련 장소 목록(위도·경도 보유 장소만) | 없음 |
| GET | `/node/{node_id}/neighbors/grouped` | 이웃 타입별 그룹(최대 30개/타입) | 없음 |
| GET | `/person/{node_id}/event-ids` | 인물의 이벤트 ID 목록 | 없음 |
| GET | `/events` | 전체 타임라인 사건 목록 + 성경책 chips | max-age=300 |
| GET | `/event/{event_id}/verses` | 사건별 근거 구절 오버레이 | max-age=300 |
| GET | `/books` | 타임라인용 성경책 목록(연도 보유분만) | no-store |
| GET | `/books-overview` | 개요용 전체 성경책 목록 | no-store |
| GET | `/search?q=` | 이름·한글명 검색(최대 20건) | 없음 |

## 데이터 흐름

### 노드 선택 흐름

1. 사용자 인터랙션(지도 마커 클릭, 검색 결과 선택, SidePanel 이웃 클릭)
2. `App.jsx`의 `selectNode(id)` 또는 `selectNodeFresh(id)` 호출
3. `selectedNode` state 변경 → MapView와 SidePanel이 각각 독립적으로 재fetch
   - MapView: `GET /node/{id}/places` → 마커 갱신, hull 계산, 링 자동 펼침
   - SidePanel: `GET /node/{id}` → 상세 패널 렌더링 → `onNodeLoaded` 콜백으로 메타 정보 역전달
4. `handleNodeLoaded(node)` — Person이면 `GET /person/{id}/event-ids` 추가 fetch
5. `personEventIds`(Set)가 `TimelineView`의 `personFilter` prop으로 전달되어 타임라인 필터링

### 사건 구절 드릴다운 흐름

1. TimelineView의 📖 칩 클릭 → `toggleVerseView(ev)` 호출
2. `GET /event/{id}/verses` → `overlays.event_verses()` JSON 파일 응답
3. 권별 탭, 인용 범위, 절 본문(한/영 미리저장) 인라인 렌더링

### 검색 흐름

1. 입력 → 250ms 디바운스 → `GET /search?q=`
2. Neo4j CONTAINS 쿼리(한글명 우선) → 최대 20건 반환
3. 드롭다운 결과 클릭 → `handleSelectResult` → 타입별 탭 이동(`Book` → overview, `Event` → timeline, 나머지 → map) + `selectNodeFresh`

## 오버레이 데이터 전략

Neo4j에 직접 적재하기 어렵거나 집필 관계처럼 추정 데이터인 경우 `data/` 하위 JSON 파일로 유지한다. `overlays.py`가 `lru_cache`로 한 번만 로드한다. `/events`와 `/books` 엔드포인트는 Neo4j 쿼리 결과와 오버레이 데이터를 서버 측에서 머지하여 반환한다.

## 오류 처리

- 백엔드: FastAPI 기본 `HTTPException`. Neo4j 연결 실패는 lifespan에서 catch 후 warn log로 계속 진행(인덱스 생성 실패 허용).
- 프론트엔드: 각 컴포넌트가 `catch`로 오류 state를 세팅하고 인라인 오류 배너를 렌더링. `AbortError`는 무시.

## 배포 구조

- `docker compose`로 세 컨테이너(`neo4j`, `api`, `nginx`) 운영.
- nginx가 `:8080`에서 `/api/*` → `api:8000`으로 프록시. 나머지는 정적 파일 서빙(SPA fallback `/index.html`).
- GitHub Actions 자기 호스팅 러너가 `main` 브랜치 push 시 `deploy.sh`를 실행해 `frontend/dist` 재빌드 + 컨테이너 재시작.
- 프론트 빌드 시 `VITE_API_URL=/api`를 `.env.production`으로 주입해 브라우저가 nginx를 경유하게 한다.
