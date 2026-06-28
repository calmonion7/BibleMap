---
last_mapped_commit: 65056c34bc13a5543c3d620dd818fa61507ac600
mapped: 2026-06-28
---

# ARCHITECTURE

## 전체 패턴

3계층 단일 스택이다. **React SPA(frontend) → FastAPI(backend) → Neo4j(graph DB)**, 그 사이를 nginx가 정적 파일 서빙 + `/api` 리버스 프록시로 묶는다. 데이터의 권위(authority)는 Neo4j 그래프에 있고, 그 위에 빌드타임에 생성된 **JSON 오버레이**(`data/`)가 얹혀 런타임 응답을 풍부하게 만든다.

핵심 데이터 흐름은 **큐레이션 인물 → 여정(journey) → 사건(event) → 구절(verse)** 드릴다운이다. 사용자가 인물 허브에서 인물을 고르면, 그 인물의 시간순 정차지(stops)가 지도에 여정선으로 펼쳐지고, 각 정차지(사건)를 펼치면 근거 구절 본문이 권별로 표시된다.

## 백엔드 (FastAPI)

진입점은 `backend/app/main.py`. `app = FastAPI(lifespan=...)`로 앱을 만들고 7개 라우터를 `include_router`로 등록한다 — `nodes`, `events`, `search`, `books`, `persons`, `journey`, `places`. CORS는 `allow_origins=["*"]`, `allow_methods=["GET"]`로 GET 전용 읽기 API다.

`lifespan` 훅(`main.py:8-21`)은 앱 기동 시 Neo4j에 `Person`/`Place`/`Event`/`PeopleGroup`/`Book` 라벨마다 `theographic_id` 인덱스를 `IF NOT EXISTS`로 생성한다. 인덱스 생성 실패는 로깅만 하고 계속 진행한다.

### DB 접근 — `backend/app/db.py`

`get_driver()`가 모듈 전역 `_driver`에 Neo4j 드라이버 싱글톤을 lazy 생성한다. URI/USER는 `NEO4J_URI`/`NEO4J_USER` 환경변수(기본 `bolt://localhost:7687`, `neo4j`), 비밀번호는 `NEO4J_PASSWORD` 필수(없으면 `RuntimeError`). 모든 라우트가 `with driver.session() as session:` 블록으로 Cypher를 실행한다.

### 오버레이 로더 — `backend/app/overlays.py`

런타임에 `data/` JSON을 읽는 공통 모듈. `_resolve(subpath)`가 `DATA_DIR`(기본 `/app/data`, 컨테이너 마운트 경로) → 레포 `data/`(`_REPO_DATA_DIR`) 순으로 파일을 탐색한다. `_load`는 JSON을 읽되 디코드 실패 시 `{}` 반환. `@functools.lru_cache(maxsize=1)`로 감싼 `book_events_raw()`(`{bookId: [eventId, ...]}`)와 `event_verses()`(사건별 근거 구절)는 1회 로드 후 메모리 캐시한다.

### 라우트 모듈 (`backend/app/routes/`)

- **`persons.py`** — `GET /persons/curated`. Neo4j를 **쓰지 않고** `person_events/<slug>.json` 파일만으로 큐레이션 16인 목록을 정적 구성한다. 모듈 상수 `_ERA`(slug→시대), `_NAME_KO`(slug→한글명), `_ERA_ORDER`(시대 표시 순서)를 들고, 각 slug 파일 첫 이벤트의 `participants[0]`을 `theographic_id`로 삼아 `{id, slug, nameKo, era, eventCount}`를 반환한다. `@lru_cache`로 목록 1회 구성.
- **`journey.py`** — `GET /person/{person_id}/journey`. 큐레이션 인물의 시간순 여정 정차지. `persons.py`의 `_ERA`/`_NAME_KO`를 import해 `theographic_id→slug` 역매핑을 만들고(`_build_id_to_slug`), 해당 slug의 `person_events/<slug>.json`을 `sortKey`로 정렬한다(`_load_events`). 각 이벤트의 `occursAt[0]` place_id에 대해 Neo4j에서 `Place` 노드의 `longitude`/`latitude`/`nameKo`를 배치 조회(`_fetch_place_coords`)하고, 좌표가 있는 정차지에만 1부터 `seq`를 부여한다. 큐레이션 인물이 아니면 `stops=[]` 빈 응답(404 아님). 즉 **여정 = 파일 기반 사건 시퀀스 + Neo4j 좌표 조인**.
- **`events.py`** — `GET /events`(타임라인 사건 목록)와 `GET /event/{event_id}/verses`(사건 근거 구절 드릴다운). `_compute_events()`(`@lru_cache`)는 Neo4j에서 `startDate IS NOT NULL`인 `Event`를 `sortKey` 순으로 조회하면서 `(Book)-[:CONTAINS_BOOK]->(Event)`로 연결된 책을 `bookOrder` 순 `books` 배열로 모으고, `authored`·`yearLabel`을 함께 반환한다. 여기에 오버레이 `book_events_raw()`를 역방향 인덱스(`_load_approx_book_index`, eventId→책 메타)로 머지해 **그래프 관계가 없는 추정책(집필 배경 연결)을 CONTAINS_BOOK 항목 뒤에 덧붙인다** — 그래프와 오버레이의 대표적 합류 지점. `/event/{id}/verses`는 오버레이 `event_verses()`에서 해당 사건의 권별 구절을 꺼내 Neo4j Book 이름맵(`_book_name_map`)으로 `bookNameKo`를 보강해 반환한다.
- **`books.py`** — `GET /books-overview`. Neo4j `Book` 노드 전체를 `bookOrder` 순으로 반환(개요 뷰 전용, startYear 조건 없음). `testament`/`genre`/`themes`/`keyVerse`/`authorKo` 등 메타 포함, `Cache-Control: no-store`.
- **`nodes.py`** — 범용 노드 API. `GET /node/{id}`(노드 + 이웃 + 총 이웃수, Book이면 `topPersons`/`topEvents` 추가, Person이면 `traits` JSON 파싱), `GET /node/{id}/neighbors/grouped`(타입별 그룹 이웃), `GET /node/{id}/places`(노드 라벨별 분기 Cypher로 관련 Place 좌표 — Person/Event/PeopleGroup/Book/Place 각각 다른 쿼리), `GET /person/{id}/event-ids`(인물 참여 사건 id 집합). 상수 `MAX_NEIGHBORS_PER_TYPE=30`, `NODE_NEIGHBOR_LIMIT=50`.
- **`places.py`** — `GET /place/{place_id}/curated-persons`. 특정 장소를 여정에 포함하는 큐레이션 인물 목록. Neo4j 없이 `person_events/<slug>.json`의 `occursAt` 배열을 검사해 필터링(`_place_to_persons`, `@lru_cache`). `exclude` 쿼리로 현재 탐험 인물 제외. `persons.py`와 동일한 `_ERA`/`_NAME_KO`/`_ERA_ORDER`를 **단방향 참조 회피를 위해 여기서 재선언**한다(현재 13인만, paul/peter/john_the_apostle 미포함).
- **`search.py`** — `GET /search?q=`. `nameKo`/`name` CONTAINS 매칭을 exact→prefix→contains 랭크로 정렬, `LIMIT 20`.

## 그래프 + 오버레이 모델

### Neo4j (권위 그래프)

노드 라벨: `Person`, `Place`, `Event`, `PeopleGroup`, `Book`. 모든 노드는 `theographic_id`로 식별된다(Theographic 데이터셋 출처). 주요 관계: `HAS_PARTICIPANT`(Event→Person), `OCCURS_AT`(Event→Place), `MEMBER_OF`(Person→PeopleGroup), `CONTAINS_BOOK`(Book→Event), `PART_OF`(상위 사건). `Place`는 `latitude`/`longitude`를 가진다.

### Authored-event 모델

타임라인을 메우기 위해 손으로 저작한(authored) 사건이 Neo4j `Event` 노드로 적재되며 `authored:true` 속성을 단다. 원천 데이터는 두 종류 JSON이다:
- `data/authored_events/events.json` — 독립 저작 사건(`id`, `title`, `nameKo`, `sortKey`, `startDate`, `yearLabel`, `context`, `occursAt`, `participants`, `mappedBookIds`). Place/Person 노드가 없으면 `occursAt`/`participants`를 빈 배열로 두고 책에만 매핑한다.
- `data/person_events/<slug>.json` — 큐레이션 인물의 여정 사건. `id`(예 `authored-jesus-bethlehem-birth`), `sortKey`, `occursAt`(place_id 배열), `participants`(인물 theographic_id), `context`, `books`(`{bookId, rangeLabel}`). `authored:true`.

이 사건들은 `backend/scripts/load_authored_events.py`·`load_person_events.py`로 멱등 적재된다. 즉 **여정 사건은 Neo4j에도 Event 노드로 존재하지만(타임라인·그래프 조회용), 정차지 시퀀스 자체는 JSON 파일이 권위**다 — 백엔드 `journey.py`/`persons.py`/`places.py`는 파일을 직접 읽어 결정적으로 응답한다.

### 런타임 오버레이 vs 그래프

| 구분 | 권위 | 런타임 사용처 |
|------|------|--------------|
| 노드/관계/좌표 | Neo4j 그래프 | `nodes.py`, `events.py`, `books.py`, `search.py`, `journey.py`(좌표) |
| 여정 정차지 시퀀스 | `data/person_events/*.json` | `journey.py`, `persons.py`, `places.py` |
| 사건 근거 구절 본문 | `data/event_verses/events.json` 오버레이 | `events.py` `/event/{id}/verses`, 프론트 `EventVerses` |
| 사건↔추정책 매핑 | `data/book_events/books.json` 오버레이 | `events.py` `/events` 머지 |
| 한글 이름 | `data/names_ko/*` → Neo4j SET | `inject_ko_names.py`(배포 시 주입) |

이름·성품(traits)·책 배경·장소 배경은 빌드타임에 JSON으로 생성된 뒤 `inject_*.py` 스크립트로 **Neo4j 노드 속성에 주입**(SET)된다 — 이 부류는 그래프로 흡수돼 응답 시점엔 그래프 속성으로 읽힌다. 반면 구절 본문·추정책 매핑은 그래프에 넣지 않고 응답 시점에 오버레이 파일을 직접 읽어 머지한다.

## 프론트엔드 (React 19 + MapLibre)

진입점 `frontend/src/main.jsx` → `App.jsx`. 단일 API 클라이언트 `frontend/src/api.js`의 `apiGet(path, {signal})`이 모든 fetch를 담당한다. 베이스 URL은 `import.meta.env.VITE_API_URL`(프로덕션은 `/api`, 빌드타임 주입) → 폴백 `http://localhost:8000`.

### 화면 단계(stage) 흐름 — `App.jsx`

`activeStage` 상태가 `'hub' | 'explore' | 'overview'` 3단계를 토글한다:
- **hub** — `PersonHub`. `/persons/curated`로 큐레이션 인물을 시대별 카드 그리드로. 카드 클릭 → `handleSelectPerson(id)` → explore 단계.
- **explore** — 인물 선택 후. 상단 nav로 `exploreView`(`'map' | 'timeline'`) 토글. 인물 선택 시 `/person/{id}/journey`를 한 번 fetch해 `journeyStops`에 담고 `MapView`·`JourneyList`가 공유한다.
- **overview** — `BibleOverviewView`. `/books-overview`를 장르별로 그룹핑.

`explorePersonId`를 `selectedNode`와 분리해, 장소 클릭으로 상세 패널이 다른 노드로 바뀌어도 여정·지도 장소 기준은 탐험 인물로 유지한다. 노드 선택 로직은 커스텀 훅 `useNodeSelection.js`(`selectNode`/`selectNodeFresh`/`goBack`/`closePanel`/`history`/`personEventIds`)가 캡슐화한다 — 참조 안정화(`useCallback`)로 MapView effect 재실행/abort 버그를 방지한다.

데스크톱은 우측 슬라이드인 `SidePanel`, 모바일(`MOBILE_BREAKPOINT=768`)은 하단 시트(`SHEET_VH=55`). 절 본문 언어 `verseLang`(`'ko'|'en'`)는 `TimelineView`·`SidePanel`·`EventVerses`가 공유하며 `VerseLangTabs`로 전환한다.

### 주요 컴포넌트

- **`PersonHub.jsx`** — 큐레이션 인물 허브. 시대(era)별 카드 섹션. 계약: `onSelectPerson(id)`, `onOpenOverview()`.
- **`MapView.jsx`** — MapLibre GL 지도. ESRI NatGeo 래스터 타일 기반. effect 3종: (1) `personId ?? selectedNode`로 `/node/{id}/places` fetch → `places-source`에 GeoJSON 세팅 + 카메라 프레이밍 + primary 장소의 사건 링 자동 펼침, (2) `journeyStops` 변경 시 여정선(`journey-line-source`)·정차지 배지(`journey-stops-source`) 갱신, (3) `activeStopIdx` 변경 시 활성 정차지 강조 + 카메라 이동. 지도 로직은 3개 헬퍼 모듈로 분리:
  - `mapGeo.js` — 순수 GeoJSON/기하 함수(`placesToGeoJSON`, `buildJourneyLineGeoJSON`, `buildJourneyStopsGeoJSON`, `journeyStopGroups`, `coreBounds`, `ringPositions`, `ringLabels`, 라벨 방사 배치).
  - `mapLayers.js` — `setupMapSources`(소스·레이어 정의: places 클러스터링 `clusterRadius:18`/`clusterMinPoints:4`, 여정선 그라데이션, 정차지 배지, 사건 링, 스파이더), `registerEventHandlers`(클릭/호버), `EMPTY_GEOJSON`. 팝업 HTML은 `escapeHtml`로 XSS 이스케이프.
  - `mapRingController.js` — `createRingController`로 사건 링 fly-out·스파이더 애니메이션 상태를 클로저에 캡슐화(`expandPlace`/`collapseRing`/`spiderifyPlaces`/`collapseSpider`/`destroy`). 링 펼침 시 사건을 가져와 방사 배치한다.
- **`JourneyList.jsx`** — 여정 정차지를 "여정 > 사건 > 구절" 아코디언 트리로. 데스크톱은 좌측 290px, 모바일은 지도 위 하단 트리(동일 컴포넌트 재사용). 📖 칩으로 사건별 `EventVerses`를 한 번에 하나만 펼친다. 좌표 중복 정차지를 deduplicate해 지도 `activeStopIdx`(장소 단위 인덱스)와 동기화.
- **`EventVerses.jsx`** — `/event/{id}/verses`로 권별 구절을 fetch해 권 칩 선택 + 언어 탭으로 본문 표시. 구절 본문은 오버레이에 프리베이크된 `textKo`/`textEn`.
- **`TimelineView.jsx`** — `/events`로 사건을 연도순 타임라인에. `bookFilter`(선택 책)·`personFilter`(`personEventIds`)로 필터, `authored` 사건 라벨링.
- **`SidePanel.jsx`** — 노드 상세(611줄). `/node/{id}` + 이웃 그룹 + Place 구절 드릴다운 + "이 곳을 지난 다른 인물" 칩(`/place/{id}/curated-persons` → `onExplorePerson`). 관계 한글 라벨 `REL_KO`.
- **`BibleOverviewView.jsx`** — 66권 개요, 장르(`OT_GENRE_ORDER`/`NT_GENRE_ORDER`)별 카드.
- 공유: `theme.js`(타입 색·한글 라벨 단일 팔레트), `constants.js`(`MOBILE_BREAKPOINT`/`SHEET_VH`), `Spinner.jsx`, `VerseLangTabs.jsx`.

## 배포 / 인프라

`docker-compose.yml`이 3 서비스를 띄운다 — `neo4j`(neo4j:5, 7474/7687을 127.0.0.1에만 바인드), `api`(`./backend` 빌드, `./data:/app/data` 마운트, neo4j depends_on), `nginx`(nginx:alpine, 8080:80, `frontend/dist`를 read-only 마운트 + `nginx/nginx.conf` 프록시). 비밀번호는 `.env`의 `NEO4J_PASSWORD`(compose가 `NEO4J_AUTH`를 `neo4j/<pw>`로 파생).

`nginx/nginx.conf`: `/api/` → `http://api:8000/` 프록시, 정적 자산 immutable 캐시, `index.html` no-cache, SPA 폴백 `try_files $uri /index.html`.

`deploy.sh`: 프론트 빌드 → `docker compose -p biblemap build api` → `up -d api nginx` → `inject_ko_names.py`로 한글 이름 주입(Neo4j 준비까지 15회 재시도). macOS 키체인 우회를 위해 임시 `DOCKER_CONFIG` 생성. `.github/workflows/deploy.yml`이 `main` push 시 self-hosted 러너에서 `git reset --hard origin/main` 후 `deploy.sh` 실행.
