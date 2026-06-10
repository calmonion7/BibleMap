---
last_mapped_commit: 26240c7cf18f421b2f8baa4fd6584f40eede57b0
mapped: 2026-06-11
---

# ARCHITECTURE

## 전체 구조

3티어 구성이다.

1. 데이터 저장소: Neo4j (그래프 DB). 노드 레이블 `Person` / `Place` / `Event` / `PeopleGroup`, 관계 `PARENT_OF` / `CHILD_OF` / `SIBLING_OF` / `PARTNER_OF` / `MEMBER_OF` / `HAS_PARTICIPANT` / `OCCURS_AT` / `PART_OF`. 모든 노드는 `theographic_id` 프로퍼티로 식별된다.
2. 백엔드: FastAPI (Python). Neo4j에 Cypher 쿼리를 던지고 JSON을 반환하는 얇은 read-only API. `backend/app/main.py`가 진입점.
3. 프론트엔드: React 19 + Vite SPA. 세 가지 뷰(Map / Timeline / Graph)가 같은 `selectedNode` 상태를 공유한다. `frontend/src/main.jsx` → `frontend/src/App.jsx`가 진입점.

배포 시에는 nginx가 정적 프론트엔드를 서빙하고 `/api/` 경로를 FastAPI로 리버스 프록시한다.

## 백엔드 — 데이터 서빙

### 진입점과 부팅
- `backend/app/main.py`: `FastAPI` 앱 생성. CORS는 전체 허용(`allow_origins=["*"]`). `lifespan`에서 4개 레이블에 대해 `theographic_id` 인덱스를 `IF NOT EXISTS`로 생성(실패해도 무시). 라우터 4개를 `include_router`로 등록.
- `backend/app/db.py`: `get_driver()` — 모듈 전역 싱글턴 드라이버. 접속 정보는 환경변수 `NEO4J_URI` / `NEO4J_USER` / `NEO4J_PASSWORD`(기본값 `bolt://localhost:7687`, `neo4j`, `biblemap123`).

### 라우트 (모두 GET, 동기 함수, 요청마다 `driver.session()` 열고 닫음)
- `backend/app/routes/nodes.py`
  - `GET /node/{node_id}` — 노드 1개 + 이웃 최대 50개. `name`/`nameKo`/`theographic_id`/`aliasesKo`를 제외한 나머지 프로퍼티를 `properties`로 반환. `nameKoMissing`(한글명 부재 여부) 플래그 포함.
  - `GET /node/{node_id}/neighbors/grouped` — 이웃을 `Person`/`Event`/`PeopleGroup`/`Place` 4개 버킷으로 그룹핑, 버킷당 최대 30개. GraphView가 사용.
  - `GET /node/{node_id}/places` — 노드 레이블에 따라 지도에 찍을 장소를 분기 조회. `Person`은 참여 이벤트의 발생지, `Event`는 직접 발생지(`isPrimary=true`), `PeopleGroup`은 `MEMBER_OF` 구성원의 이벤트 발생지, `Place`는 자기 자신. 위/경도 NULL은 제외. MapView가 사용.
- `backend/app/routes/places.py`
  - `GET /places` — 위/경도가 있는 전체 `Place` 목록. (현재 프론트엔드 어느 뷰도 직접 호출하지 않음. MapView는 `/node/{id}/places`만 사용.)
- `backend/app/routes/events.py`
  - `GET /events` — `startDate`가 있는 전체 `Event`를 `sortKey` 오름차순. `Cache-Control: no-store` 헤더. TimelineView가 사용.
- `backend/app/routes/search.py`
  - `GET /search?q=` — `nameKo` 또는 `name`에 `CONTAINS` 매칭, 최대 20개. App 상단 검색창이 사용.

응답 객체는 `id`(=theographic_id), `name`(영문), `nameKo`(없으면 영문 fallback), `label`(레이블), 관계명(`relation`) 등으로 정규화된다.

### 데이터 적재 (런타임 경로 아님 — 배포/세팅 스크립트)
- `backend/scripts/load_theographic.py`: GitHub의 theographic-bible-metadata JSON(people/places/events/peopleGroups)을 받아 `status == "publish"`만 필터링한 뒤 Neo4j에 노드/관계를 `MERGE`로 배치 적재. `__main__`에서 직접 실행.
- `backend/scripts/inject_ko_names.py`: `data/names_ko/*.json`의 한글명/별칭을 기존 노드에 `nameKo`/`aliasesKo` 프로퍼티로 주입(`MATCH ... SET`). `deploy.sh`의 마지막 단계가 호출.

## 프론트엔드 — 뷰와 상태

### 상태 모델
`frontend/src/App.jsx`가 단일 소스. `useState`로 보유:
- `selectedNode` — 현재 선택 노드의 `theographic_id`(문자열) 또는 `null`. 세 뷰와 SidePanel이 공유하는 핵심 동기화 키.
- `activeView` — `'map'` / `'timeline'` / `'graph'`. 탭 전환.
- `searchQuery` / `searchResults` / `showDropdown` — 상단 검색.

뷰 컴포넌트는 모두 `{ onSelectNode, selectedNode }` 인터페이스를 받는다. 어느 뷰에서 노드를 클릭하든 `setSelectedNode`로 같은 상태를 갱신하므로 뷰 간 선택이 일관된다. `API_BASE`/`API_URL`은 각 파일에서 `import.meta.env.VITE_API_URL || 'http://localhost:8000'`로 정의.

### 뷰별 데이터 흐름
- 지도 `frontend/src/MapView.jsx` — MapLibre GL. ESRI NatGeo 래스터 타일. `selectedNode`가 바뀌면 `GET /node/{id}/places`를 호출해 GeoJSON 소스(`places-source`)를 갱신하고 `fitBounds`로 화면 이동. 마커 클릭 → `onSelectNode(id)` + 팝업. `selectedNode`가 없으면 마커를 비운다. `AbortController`로 이전 요청 취소.
- 타임라인 `frontend/src/TimelineView.jsx` — 마운트 시 `GET /events` 1회. 같은 `startDate`끼리 클라이언트에서 그룹핑 후 `sortKey`로 정렬. 단건은 행 클릭, 그룹은 "외 N건" 드롭다운. 선택 항목은 `selectedNode`와 비교해 하이라이트.
- 그래프 `frontend/src/GraphView.jsx` — Cytoscape + cose-bilkent 레이아웃 + expand-collapse 플러그인. `selectedNode`(없으면 기본값 모세 `recjNRR60PAuFtjha`)에 대해 `GET /node/{id}`와 `GET /node/{id}/neighbors/grouped`를 `Promise.all`로 동시 호출. 중심 노드 1개 + 타입별 컴파운드 부모 노드(`GroupParent`) + 이웃 노드로 그래프 구성, 초기에 `collapseAll()`. 노드 탭 → `onSelectNode`(단, `GroupParent`는 무시). 하단 오버레이로 선택 노드 요약 표시.
- 사이드패널 `frontend/src/SidePanel.jsx` — Map/Timeline 뷰에서만 표시(Graph는 자체 오버레이 사용, `App.jsx`에서 `activeView !== 'graph'` 조건). `GET /node/{id}`로 노드 + 이웃 리스트를 받아 렌더. 이웃 버튼 클릭 → `onSelectNode`로 재탐색(드릴다운).

### 뷰 ↔ 패널 배치 (App.jsx)
- 상단 48px 플로팅 내비게이션 바(탭 + 검색 드롭다운).
- 전체화면 뷰 컨테이너. Graph만 내비 높이만큼 top 오프셋.
- 우측 360px 슬라이드인 오버레이 패널(SidePanel), `selectedNode` 유무로 `translateX` 토글. Graph 뷰에서는 렌더하지 않음.

## 데이터 플로우 요약

선택(클릭/검색) → `App.selectedNode` 갱신 → 활성 뷰 + SidePanel이 각자 `GET /node/{id}...` 류 호출 → FastAPI가 Cypher 실행 후 정규화 JSON 반환 → 뷰 갱신. 검색은 `GET /search` → 드롭다운 → 선택 시 `selectedNode` 설정.

## 인프라 / 배포

- `docker-compose.yml`: `neo4j`(neo4j:5, 7474/7687을 127.0.0.1에만 바인딩), `api`(`./backend` 빌드, `NEO4J_URI=bolt://neo4j:7687`, `./data`를 `/app/data`로 마운트), `nginx`(nginx:alpine, 호스트 8080 → 컨테이너 80, `frontend/dist`를 read-only 서빙). Compose 프로젝트명 `biblemap`.
- `nginx/nginx.conf`: `/api/`를 `http://api:8000/`로 프록시(경로 prefix 제거), `index.html`은 no-cache, 해시 정적 자산은 1년 immutable, SPA fallback `try_files $uri /index.html`. 프로덕션에서 프론트엔드의 `VITE_API_URL`은 `/api`(`frontend/.env.production`).
- `backend/Dockerfile`: python:3.12-slim, `uvicorn app.main:app --host 0.0.0.0 --port 8000`.
- `deploy.sh`: 프론트 빌드(`npm install && npm run build`) → API 이미지 빌드 → `api`/`nginx` 재기동 → Neo4j 준비될 때까지 재시도하며 `inject_ko_names.py` 실행. `/tmp/biblemap-deploy.lock`으로 동시 실행 방지.
- 자동 배포: `.github/workflows/deploy.yml`(self-hosted runner, main push 시 worktree에서 `git reset --hard` 후 `deploy.sh`)와 `scripts/auto-deploy-poll.sh`(2분 폴링, 새 커밋 시 동일 배포). 둘 다 같은 lock 파일을 공유.

## 핵심 추상화 / 규약

- `theographic_id`가 전 계층 공통 식별자. 백엔드 응답의 `id`, 프론트의 `selectedNode`, 검색/이웃 링크가 모두 이 값.
- `nameKo` 우선 + 영문 `name` fallback, `nameKoMissing` 플래그로 미번역 표시. 한글명은 별도 적재 단계(`inject_ko_names.py`)로 주입되는 오버레이.
- 백엔드는 상태 비저장 read-only. 비즈니스 로직은 라우트 함수 안의 Cypher에 인라인되어 있고 별도 서비스/리포지토리 레이어는 없다.
- 프론트엔드는 상태 라이브러리 없이 `App.jsx`의 `useState` + props drilling. 데이터 페칭은 각 컴포넌트의 `useEffect` 안에서 `fetch` 직접 호출(공용 API 클라이언트 모듈 없음).
