---
last_mapped_commit: 288b14e23c889de294d34d0f794867d4e313a421
mapped: 2026-06-11
---

# 아키텍처

## 전체 구조

세 개의 런타임 컨테이너로 구성된 단방향 읽기 전용 시스템이다. `docker-compose.yml`이 묶는다.

```
브라우저
  │  (정적 자산 + /api/* 요청)
  ▼
nginx  ──── /api/  ──▶  api(FastAPI/uvicorn)  ──── bolt  ──▶  neo4j
  │  정적 SPA
  └─ /usr/share/nginx/html  ◀── ./frontend/dist 마운트
```

- `nginx`(`nginx:alpine`): 호스트 `8080:80` 노출. `frontend/dist`를 정적 호스팅하고 `/api/`를 `http://api:8000/`로 프록시한다. `nginx/nginx.conf` 참고.
- `api`(`./backend`에서 빌드): uvicorn으로 `app.main:app` 구동(`backend/Dockerfile`). 컨테이너 내부 8000 포트(호스트 노출 없음 — nginx만 접근).
- `neo4j`(`neo4j:5`): 7474/7687을 `127.0.0.1`에만 바인딩(외부 비노출). 데이터는 `neo4j_data` 볼륨에 영속.

배포는 main 푸시 시 self-hosted 러너에서 `git reset --hard origin/main` 후 `deploy.sh` 실행(`.github/workflows/deploy.yml`).

## 백엔드 — 패턴과 레이어

FastAPI 기반 **읽기 전용 그래프 조회 API**. 쓰기 엔드포인트는 없다(CORS도 `allow_methods=["GET"]`).

레이어:

1. **앱 부트스트랩** — `backend/app/main.py`
   - `lifespan` 컨텍스트 매니저가 시작 시 4개 라벨(`Person`/`Place`/`Event`/`PeopleGroup`)에 대해 `theographic_id` 인덱스를 `IF NOT EXISTS`로 생성한다. 실패해도 `logging.exception` 후 인덱스 없이 계속 진행한다(부팅 비차단).
   - `CORSMiddleware`: `allow_origins=["*"]`, `allow_credentials=False`, `allow_methods=["GET"]`.
   - 라우터 3종을 `include_router`로 등록: `nodes`, `events`, `search`.
2. **라우팅 레이어** — `backend/app/routes/*.py` (라우터별 `APIRouter()`)
3. **DB 접근 레이어** — `backend/app/db.py`
   - 모듈 전역 단일 드라이버(`_driver`)를 지연 생성하는 `get_driver()`. `NEO4J_URI`/`NEO4J_USER` 환경변수(기본 `bolt://localhost:7687`/`neo4j`), `NEO4J_PASSWORD`는 필수이며 없으면 `RuntimeError`.
   - 각 핸들러가 `with driver.session() as session:`으로 세션을 열어 Cypher를 직접 실행한다. ORM/리포지토리 추상화 없음 — 핸들러 안에 Cypher 쿼리가 인라인된다.

### 엔드포인트 목록

| 메서드/경로 | 정의 위치 | 비고 |
|---|---|---|
| `GET /node/{node_id}` | `routes/nodes.py:124` | 노드 1개 + 이웃(최대 `NODE_NEIGHBOR_LIMIT=50`). `name`/`nameKo`/`theographic_id`/`aliasesKo`를 제외한 나머지 속성을 `properties`로 반환. |
| `GET /node/{node_id}/places` | `routes/nodes.py:9` | 노드 라벨(Person/Event/PeopleGroup/그 외=Place)별로 다른 Cypher를 골라 지도 표시용 좌표 목록을 반환. `latitude`/`longitude` 없는 곳은 제외, `isPrimary` 플래그 포함. |
| `GET /node/{node_id}/neighbors/grouped` | `routes/nodes.py:90` | 이웃을 타입별로 그룹화(타입당 최대 `MAX_NEIGHBORS_PER_TYPE=30`). **`GraphView.jsx`가 사용** — 프롬프트의 "UNUSED" 표기와 달리 그래프 뷰에서 실제로 호출된다. |
| `GET /events` | `routes/events.py:7` | `startDate`가 있는 모든 `Event`를 `sortKey` 오름차순으로. 응답에 `Cache-Control: no-store`. |
| `GET /search?q=` | `routes/search.py:8` | `nameKo` 또는 `name`에 `q`가 `CONTAINS`되는 노드 최대 `SEARCH_LIMIT=20`개. 빈 쿼리는 `[]`. |

응답 정규화 규칙(여러 핸들러 공통): 표시명은 `name` 우선, 없으면 `title`. `nameKo`가 없으면 영문명으로 폴백하고 `nameKoMissing: true`를 함께 내려보내 프론트가 "(미번역)" 배지를 붙인다.

### 그래프 모델(Neo4j)

- 노드 라벨: `Person`, `Place`, `Event`, `PeopleGroup`.
- 관계 타입: `HAS_PARTICIPANT`, `OCCURS_AT`, `MEMBER_OF`, `PART_OF`, `PARENT_OF`, `CHILD_OF`, `SIBLING_OF`, `PARTNER_OF`.
- 모든 노드의 안정 식별자는 `theographic_id`(API 경로의 `node_id`가 이 값).
- 데이터 적재는 런타임이 아닌 별도 스크립트: `backend/scripts/load_theographic.py`(theographic-bible-metadata 원본 JSON을 받아 노드/관계 생성), `backend/scripts/inject_ko_names.py`(`data/names_ko/*.json`의 한글명 주입).

## 프론트엔드 — 패턴과 데이터 흐름

React 19 SPA, Vite 빌드. 진입점 `frontend/index.html` → `frontend/src/main.jsx`(StrictMode로 `<App/>` 마운트) → `frontend/src/App.jsx`.

### 상태 소유와 하향 전달

`App.jsx`가 **단일 선택 상태(`selectedNode`)와 탐색 히스토리 스택을 전적으로 소유**한다. 하위 뷰는 상태를 갖지 않고 prop으로 받는다(top-down).

- 공통 인터페이스: 네 뷰/패널 모두 `selectedNode`(현재 선택 id)와 `onSelectNode`(선택 콜백)를 받는다.
- 모든 뷰의 `onSelectNode`는 `App.jsx`의 `selectNode(id)` 하나로 라우팅된다.

선택/히스토리 로직(`App.jsx`):

- `selectNode(id)`: 같은 노드면 무시. 직전 `selectedNode`가 있으면 `history`에 push한 뒤 새 id로 교체 — 패널 "뒤로가기"의 근거.
- `goBack()`: `history` 마지막 항목을 꺼내 `selectedNode`로 복원하고 스택을 pop.
- `closePanel()`: `history`와 `selectedNode`를 모두 리셋.
- `handleSelectResult(result)`(검색 결과 클릭): 새 검색은 새 탐색 컨텍스트로 보아 `history`를 비우고 선택을 교체.

`SidePanel`은 `onSelectNode`(이웃 클릭), `onBack`(`goBack`), `canGoBack`(`history.length > 0`)을 받는다.

### 반응형(데스크톱 vs 모바일)

`App.jsx`가 `matchMedia(MOBILE_QUERY='(max-width: 768px)')`로 `isMobile` 상태를 두고, `change` 이벤트로 갱신한다.

- 상세 패널은 **데스크톱: 우측 사이드패널(width 360px, `translateX`)**, **모바일: 하단 시트(`height: SHEET_VH=55` vh, `translateY`)**. 선택이 없으면 화면 밖으로 슬라이드아웃.
- 그래프 뷰(`activeView === 'graph'`)에서는 이 오버레이 패널을 띄우지 않는다(`GraphView`가 자체 하단 오버레이를 갖는다).
- `SHEET_VH=55`는 `MapView.jsx`의 `fitBounds` 하단 패딩 비율(`innerHeight * 0.55`)과 **수동으로 동기화**되어야 하는 결합 상수다(양쪽 주석에 명시).

### 탭(뷰 전환)

`App.jsx`의 `TABS`(map/timeline/graph)가 lucide-react 아이콘 버튼으로 렌더되고 `activeView`로 어떤 뷰를 마운트할지 결정한다. 상단 검색 입력은 모든 탭 공통.

### 각 뷰의 책임과 fetch

- **`MapView.jsx`** — MapLibre GL. ESRI NatGeo 래스터 타일 베이스맵. `places-source`(GeoJSON) 하나에 circle-shadow/circle/label 세 레이어. `selectedNode`가 바뀌면 `GET /node/{id}/places`를 `AbortController`로 가져와 소스 데이터를 교체하고 `fitBounds`로 화면을 맞춘다. **반응형 패딩**: 모바일이면 하단에 `innerHeight*0.55 + 20`(시트 가림 보정), 데스크톱이면 균일 80. 마커 클릭 시 팝업 표시 후 `onSelectNode(id)`.
- **`TimelineView.jsx`** — 마운트 시 `GET /events` 1회. 같은 `startDate`끼리 그룹핑 후 `sortKey`로 정렬. 단일 사건은 행 클릭, 다건은 대표 사건 클릭/드롭다운("외 N건")으로 개별 선택. 외부 클릭 시 드롭다운 닫기.
- **`GraphView.jsx`** — cytoscape + cose-bilkent 레이아웃 + expand-collapse 플러그인. `selectedNode || DEFAULT_NODE`('모세' id)에 대해 `GET /node/{id}`와 `GET /node/{id}/neighbors/grouped`를 `Promise.all`로 동시 호출. 타입별 부모 노드(compound) 아래에 이웃을 묶고 시작 시 전부 collapse. 노드 tap 시 `onSelectNode`, 선택이 있으면 하단 오버레이(상세 요약) 표시.
- **`SidePanel.jsx`** — `nodeId`가 바뀌면 `GET /node/{id}` fetch. 단일 `state={id,node,error}`로 응답을 추적해 stale 응답을 무시(`ready = state.id === nodeId`), `setState`는 비동기 콜백에서만 호출(eslint react-hooks set-state-in-effect 준수). 이웃을 노드 타입별로 그룹핑해 타입→색 팔레트(`TYPE_COLOR`)와 한글 라벨(`TYPE_KO`)·관계 한글명(`REL_KO`)으로 렌더. `canGoBack`이면 "← 뒤로" 버튼.

### API 베이스 URL — 공유 모듈 없음

각 프론트 파일이 **독립적으로** API 베이스를 정의한다. 공유 api 클라이언트/모듈이 없다.

- `App.jsx`: `const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'`
- `MapView.jsx`/`TimelineView.jsx`/`GraphView.jsx`/`SidePanel.jsx`: 각자 `const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'`

프로덕션에서는 `frontend/.env.production`의 `VITE_API_URL=/api`로 빌드되어 nginx 프록시(`/api/` → api:8000)를 탄다. 개발 시 폴백은 `http://localhost:8000`.

## 핵심 진입점 요약

| 영역 | 진입점 | 부트스트랩 책임 |
|---|---|---|
| 백엔드 | `backend/app/main.py` | lifespan 인덱스 생성, CORS, 라우터 등록 |
| 프론트 | `frontend/index.html` → `frontend/src/main.jsx` → `frontend/src/App.jsx` | StrictMode 마운트, 전역 선택/히스토리/반응형 상태 |
| 인프라 | `docker-compose.yml` | 3 서비스 오케스트레이션 |
| 배포 | `.github/workflows/deploy.yml` → `deploy.sh` | main 푸시 자동 배포 |
