---
last_mapped_commit: 22a678c36e40548a3d00ccf9205862505a59d9cb
mapped: 2026-06-16
---

# 아키텍처

## 전체 패턴

3-tier 컨테이너 스택: **nginx(정적 서빙 + 리버스 프록시) → FastAPI(읽기 전용 REST API) → Neo4j(그래프 DB)**. `docker-compose.yml`이 세 서비스(`neo4j`, `api`, `nginx`)를 묶는다. 데이터 적재는 별도 일회성 스크립트(`backend/scripts/`)로 그래프를 채우는 빌드타임/운영 단계이며 런타임 경로 밖에 있다.

```
브라우저
  │ :8080
  ▼
nginx (docker, nginx/nginx.conf)
  ├─ /api/* → proxy_pass http://api:8000/   (location /api/)
  └─ /*     → /usr/share/nginx/html (frontend/dist) + SPA fallback(try_files $uri /index.html)
       │
       ▼
FastAPI (docker, :8000, backend/app/main.py)
  ├─ GET /search                          (routes/search.py)
  ├─ GET /events                          (routes/events.py)
  ├─ GET /books                           (routes/books.py)
  ├─ GET /node/{id}                       (routes/nodes.py)
  ├─ GET /node/{id}/places                (routes/nodes.py)
  └─ GET /node/{id}/neighbors/grouped     (routes/nodes.py)
       │ bolt://neo4j:7687
       ▼
Neo4j 5 (docker)
  └─ 노드 라벨: Person · Place · Event · PeopleGroup · Book
```

레이어 간 의존은 단방향(브라우저 → nginx → api → neo4j). API는 GET만 제공(`main.py`의 CORS `allow_methods=["GET"]`)하며 그래프를 변경하지 않는다 — 쓰기는 전부 `backend/scripts/` 적재 단계에서만 일어난다.

## 프론트엔드 (React SPA)

Vite 빌드 단일 페이지 앱. 진입은 `frontend/index.html` → `frontend/src/main.jsx`(`createRoot`로 `App` 마운트, `StrictMode` 래핑).

루트 컴포넌트는 `frontend/src/App.jsx`. 책임:

- **전역 상태 보유**: `selectedNode`(선택된 노드 id), `selectedNodeMeta`({label, nameKo, startYear, endYear}), `activeView`('map' | 'timeline'), 검색 상태(query/results/error/loading/dropdown/highlight/typeFilter), `isMobile`(matchMedia), `history`(패널 뒤로가기 스택).
- **탭 전환 뷰**: `activeView`에 따라 `MapView`(`frontend/src/MapView.jsx`) 또는 `TimelineView`(`frontend/src/TimelineView.jsx`)를 전체화면(`position:absolute; inset:0`)으로 렌더. 상단 플로팅 내비바(`zIndex:20`)에 탭 아이콘 + 검색 입력이 들어간다.
- **검색**: 입력 변경 시 250ms 디바운스 + `AbortController`로 경쟁 차단해 `GET /search?q=` 호출(`App.jsx` `useEffect`). 결과는 타입 필터 칩 + 드롭다운 목록으로 표시하며 키보드 내비게이션(`handleSearchKeyDown`)을 지원.
- **SidePanel 오버레이**: `SidePanel`(`frontend/src/SidePanel.jsx`)을 항상 마운트하고 `selectedNode` 유무로 transform 슬라이드(데스크톱 우측 360px 패널 `translateX`, 모바일 하단 시트 `translateY`, 높이 `SHEET_VH=55vh`)로 띄운다 — 뷰 위에 겹치는 오버레이 레이어(`zIndex:10`)이지 별도 라우트가 아니다.

핵심 데이터 흐름은 **`selectedNode`(노드 id) 한 값**으로 모든 뷰가 구동되는 것. `App.selectNode(id)`(`useCallback([])`로 참조 안정화, `selectedNodeRef`로 최신값 읽음)가 단일 진입점이며 검색·지도 마커·타임라인·SidePanel 내부 링크 클릭이 모두 이 콜백을 호출한다. 직전 노드는 `history`에 쌓여 패널 뒤로가기를 만든다.

선택 노드의 메타 정보는 SidePanel이 `GET /node/{id}` 응답을 받은 뒤 `onNodeLoaded` 콜백으로 App에 역전파(`handleNodeLoaded`) — 별도 fetch 없이 공유한다. 이 메타의 `label === 'Book'`이면 TimelineView에 `bookFilter`로, `label`은 MapView에 `selectedNodeLabel`로 전달된다.

### MapView (`frontend/src/MapView.jsx`)

MapLibre GL 지도. 베이스맵은 Esri NatGeo 래스터 타일. 주요 메커니즘:

- **초기화 effect**(`[onSelectNode]` 의존)에서 맵 생성 + `load` 시 GeoJSON source/layer 등록: `hull-source`(인물 활동범위 볼록껍질 폴리곤), `places-source`(장소 마커: shadow/circle/label 레이어), `event-ring-source`(사건 링 버블). 애니메이션은 `requestAnimationFrame` + 로컬 변수로 돌리며 React state를 쓰지 않는다(프레임마다 리렌더 방지).
- **선택 effect**(`[selectedNode, mapLoaded]` 의존)에서 `GET /node/{id}/places`를 호출(AbortController) → 마커 GeoJSON 갱신 + `fitBounds`로 카메라 이동. `label === 'Person'`이고 장소 3개 이상이면 `convexHull`(`frontend/src/convexHull.js`, Graham scan)로 활동범위 폴리곤을 그린다.
- **사건 링 펼침**: 장소 마커 클릭 또는 isPrimary 장소 자동 선택 시 `expandPlace`가 `GET /node/{placeId}/neighbors/grouped`로 인접 사건을 받아 장소 중심에서 방사형으로 fly-out 애니메이션. `expandPlaceRef`/`expandedPlaceRef`로 클릭 핸들러와 선택 effect가 펼침 상태를 공유한다.
- 위치 없는 노드(`places` 빈 배열)는 `noLocation` 안내 배너로 표시, fetch 실패는 `error` 배너로 표시.

### TimelineView (`frontend/src/TimelineView.jsx`)

마운트 시 `GET /events`(연도순 사건)와 `GET /books`(연도 가진 책)를 각각 fetch해 **연도(sortKey/startYear) 기준으로 합친 통합 타임라인**을 렌더. 같은 `startDate` 사건은 그룹으로 묶어 대표 1건 + "외 N건" 펼침으로 보인다. `bookFilter`(App에서 Book 선택 시 전달)가 있으면 책 연대 범위로 사건을 필터링하는 sticky 배너를 띄운다. 책 마커는 `yearApprox`면 점선 + "추정" 배지로 구분한다(아래 `/books` 오버레이 참조).

### SidePanel (`frontend/src/SidePanel.jsx`)

`nodeId` prop이 바뀌면 `GET /node/{id}`를 fetch(stale 응답은 `state.id === nodeId` 비교로 무시). 노드 `label`에 따라 분기 렌더:

- **Person**: `properties.traits`(성품) 섹션을 이웃 그룹보다 위에 표시. 각 trait의 `verse_ref`는 클릭 시 외부 한국어 성경 API(getbible v2)로 원문을 lazy fetch(`traitVerses` 캐시).
- **Book**: 메타 칩 + 시대적 배경/핵심 주제/대표 구절(`keyVerse` 원문도 getbible로 fetch) + `topPersons`/`topEvents`. 이웃 그룹은 표시 안 함.
- **기타**: 이웃을 타입별(`Person/Place/Event/PeopleGroup/Unknown`)로 그룹핑해 관계 한글 라벨(`REL_KO`)과 함께 링크 목록으로 표시. `neighborTotal > neighbors.length`면 잘림 신호("이웃 N개 중 M개 표시")를 띄운다.

### 공유 모듈

- `frontend/src/theme.js` — 노드 타입 → 색(`TYPE_COLOR`)·한글 라벨(`TYPE_KO`)·표시 순서(`TYPE_ORDER`)·선택 하이라이트(`SELECT_HL`)의 단일 정규 팔레트. App/SidePanel/MapView/Timeline이 import해 색 충돌을 막는다.
- `frontend/src/api.js` — `API_BASE` + `apiGet(path)` GET 헬퍼. 프로덕션은 `VITE_API_URL=/api`(`.env.production`)로 빌드돼 nginx 프록시를 탄다. (단, 일부 컴포넌트는 아직 자체 `fetch` + 인라인 `API_URL` 상수를 쓴다 — `api.js`는 부분 도입 상태.)

## 백엔드 (FastAPI)

진입점 `backend/app/main.py`:

- `lifespan` 컨텍스트매니저가 앱 기동 시 5개 라벨(Person/Place/Event/PeopleGroup/Book)에 `CREATE INDEX ... IF NOT EXISTS FOR (n:Label) ON (n.theographic_id)`를 실행해 조회 인덱스를 보장한다. 실패해도 로그만 남기고 계속 진행(`except Exception`).
- CORS는 `allow_origins=["*"]`, `allow_methods=["GET"]`.
- 라우터 4개를 `include_router`로 등록: `nodes`, `events`, `search`, `books`.

DB 접근은 `backend/app/db.py`의 `get_driver()` — 모듈 전역에 Neo4j 드라이버 싱글톤을 lazy 생성(`NEO4J_URI`/`NEO4J_USER`/`NEO4J_PASSWORD` 환경변수, 비번 없으면 `RuntimeError`). 모든 라우트가 `with driver.session() as session`으로 요청마다 세션을 연다.

### 쿼리 흐름

모든 노드는 `theographic_id`(외부 데이터셋 id)를 안정 키로 쓴다. URL 경로의 `{node_id}`는 이 값이며 모든 Cypher `MATCH (n {theographic_id: $id})`의 파라미터다.

- **`GET /node/{id}`** (`routes/nodes.py` `get_node`): 노드 + 라벨 조회 → 이웃을 `LIMIT 50`(`NODE_NEIGHBOR_LIMIT`)으로, 별도 쿼리로 잘리기 전 전체 이웃 수(`neighborTotal`)도 반환. `properties`에서 name/nameKo/theographic_id/aliasesKo 제외. Person이면 `traits` JSON 문자열을 파싱, Book이면 `topPersons`(이벤트 참여 상위 10) + `topEvents`(startDate 순 10)를 추가 쿼리.
- **`GET /node/{id}/places`** (`get_node_places`): 노드 라벨에 따라 다른 Cypher로 좌표 있는 Place들을 모은다 — Person은 참여 사건의 발생지, Event는 직접 발생지(isPrimary), PeopleGroup은 멤버들의 사건 발생지, Book은 `CONTAINS_BOOK` 사건의 발생지, Place는 자기 자신(isPrimary). 위경도 없는 곳은 제외.
- **`GET /node/{id}/neighbors/grouped`** (`get_node_neighbors_grouped`): 인접 노드를 타입별로 묶어 반환(타입당 최대 `MAX_NEIGHBORS_PER_TYPE=30`). MapView의 사건 링 펼침이 소비.
- **`GET /events`** (`routes/events.py`): `startDate` 있는 Event 전체를 `sortKey` 오름차순으로. `Cache-Control: no-store`.
- **`GET /search?q=`** (`routes/search.py`): `nameKo CONTAINS` 또는 `toLower(name) CONTAINS`로 매칭, 정확일치(0)/접두(1)/포함(2) rank 정렬, `LIMIT 20`.
- **`GET /books`** (`routes/books.py`): 아래 오버레이 참조.

### `/books` 연도 오버레이 (의도된 데이터 분리)

`routes/books.py`는 `MATCH (b:Book)`로 책을 조회하되, `startYear`가 그래프에 있으면 그대로(`yearApprox=false`) 쓰고, **없으면 `data/book_years_approx/books.json`의 추정연도(`placementYear`/`basis`)를 런타임에 오버레이**(`yearApprox=true`)한다. 둘 다 없으면 시대순 배치 불가로 제외.

이 추정연도 파일은 **Neo4j에 주입되지 않는다** — 권위 있는 그래프(authoritative)와 근사 데이터를 일부러 분리한 설계다. 파일은 `docker-compose.yml`의 `./data:/app/data` 볼륨 마운트로 컨테이너에 들어오고, `routes/books.py`는 `_DATA_DIR`(기본 `/app/data`) + `book_years_approx/books.json`에서 매 요청 시 읽는다(`_load_approx`, 파일/JSON 오류는 빈 dict로 폴백).

## 데이터 적재 (`backend/scripts/`)

런타임 밖의 일회성 스크립트들. 전부 환경변수로 Neo4j에 직접 접속하며 `MERGE`로 멱등 적재한다.

1. **`load_theographic.py`** — theographic-bible-metadata GitHub raw JSON(people/places/events/peopleGroups)을 받아 노드 + 관계(PARENT_OF/CHILD_OF, SIBLING_OF, PARTNER_OF, MEMBER_OF, HAS_PARTICIPANT, OCCURS_AT, PART_OF)를 배치 적재. status가 publish인 것만 필터.
2. **`load_books.py`** — books.json + events.json을 받아 Book 노드 적재 + Book-Event `CONTAINS_BOOK` 관계 생성. event.startDate 집계로 Book별 startYear/endYear도 추정해 SET.
3. **`inject_ko_names.py`** — `data/names_ko/*.json`을 읽어 Person/Place/Event/PeopleGroup 노드에 `nameKo`/`aliasesKo`를 SET. 배포 스크립트(`deploy.sh`)가 매 배포 시 실행하는 유일한 적재 스텝.
4. **`generate_book_context.py` / `inject_book_context.py`** — 전자는 Claude API로 권별 시대배경·주제·대표구절을 생성해 `data/book_context/books.json`에 저장, 후자는 그 JSON을 Book 노드의 `background`/`themes`/`keyVerse`로 SET.
5. **`generate_person_traits.py` / `inject_person_traits.py`** — 전자는 이벤트 참여 상위 N명에 대해 Claude API로 성품(trait/verse_ref/description)을 생성해 `data/character_traits/people.json`에 저장, 후자는 그 JSON을 Person 노드의 `traits`(JSON 문자열)로 SET.

`generate_*`(Claude API 호출, `ANTHROPIC_API_KEY` 필요, `data/`에 JSON 산출)와 `inject_*`(JSON → Neo4j SET)가 짝을 이루는 2단계 패턴이다.

## 배포

`deploy.sh`(GitHub Actions `.github/workflows/deploy.yml`의 self-hosted runner가 `git reset --hard origin/main` 후 호출): 프론트엔드 `npm run build`(→ `frontend/dist/`) → API 이미지 `docker compose build api` → `up -d api nginx` → `inject_ko_names.py`(Neo4j 준비될 때까지 최대 15회 재시도). nginx가 `frontend/dist/`를 직접 서빙하므로 빌드 산출물이 배포 단위다.

## 핵심 추상화 요약

- **`theographic_id`** — 모든 노드의 안정 식별자이자 API URL 키이자 Cypher 파라미터.
- **`selectedNode`(id 한 값)** — 프론트 전 뷰를 구동하는 단일 상태. App이 소유하고 콜백으로 전파.
- **GET 전용 읽기 API** — 그래프 변경은 적재 스크립트만, 런타임은 읽기만.
- **theme.js 단일 팔레트** — 타입 색/라벨의 단일 출처.
- **권위 그래프 vs 근사 오버레이** — Neo4j는 authoritative, `data/book_years_approx`는 런타임 오버레이로 분리.
