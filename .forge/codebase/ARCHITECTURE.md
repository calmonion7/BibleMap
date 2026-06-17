---
last_mapped_commit: 1003d7beae209835a39266883039d287158e9e92
mapped: 2026-06-18
---

# ARCHITECTURE

BibleMap의 전체 구조와 데이터 흐름을 코드 사실 기준으로 기술한다. (용어 정의는 별도 CONTEXT.md 참조)

## 1. 전체 패턴

3계층 + Docker Compose 단일 호스트 배포 구조다.

- **프론트엔드**: React 19 + Vite SPA. MapLibre GL 지도 + 사이드패널 + 타임라인. 빌드 산출물(`frontend/dist/`)은 nginx가 정적 서빙한다.
- **백엔드**: FastAPI(Python 3.12) REST API. Neo4j 그래프 DB에 Cypher 질의 + 일부 데이터는 `data/` JSON 오버레이로 보강.
- **데이터 저장소**: Neo4j 5 (그래프). 정적 보강 데이터는 `data/` 디렉터리의 JSON 파일.
- **리버스 프록시**: nginx — 정적 자산 서빙 + `/api/` → `api:8000` 프록시.

컨테이너 구성은 `docker-compose.yml`에 정의된 3개 서비스다.

| 서비스 | 이미지/빌드 | 포트(호스트) | 역할 |
|---|---|---|---|
| `neo4j` | `neo4j:5` | `127.0.0.1:7474`, `127.0.0.1:7687` | 그래프 DB. 볼륨 `neo4j_data` |
| `api` | `./backend` (Dockerfile) | (외부 노출 없음) | FastAPI. `./data`를 `/app/data`로 마운트 |
| `nginx` | `nginx:alpine` | `8080:80` | 정적 서빙 + API 프록시 |

`NEO4J_PASSWORD`는 루트 `.env`(예시는 `.env.example`)에서 주입되며, 미설정 시 compose가 기동 거부한다(`?` 연산자).

## 2. 백엔드 계층

### 진입점
- `backend/app/main.py` — FastAPI 앱(`app`) 생성. CORS(GET만, origin `*`) 미들웨어. `lifespan`에서 5개 라벨(`Person/Place/Event/PeopleGroup/Book`)의 `theographic_id` 인덱스를 `CREATE INDEX ... IF NOT EXISTS`로 보장(실패해도 계속 진행). 4개 라우터(`nodes/events/search/books`)를 등록.
- Docker `CMD`: `uvicorn app.main:app --host 0.0.0.0 --port 8000` (`backend/Dockerfile`).

### DB 접근
- `backend/app/db.py` — `get_driver()`가 모듈 전역 단일 드라이버를 lazy 초기화(`GraphDatabase.driver`). 환경변수 `NEO4J_URI`/`NEO4J_USER`/`NEO4J_PASSWORD` 사용. 비밀번호 없으면 `RuntimeError`.
- 라우트는 매 요청 `with driver.session()`을 열고 Cypher를 직접 실행한다. ORM/쿼리빌더 없음, raw Cypher 문자열.

### 라우트(엔드포인트 단위로 함수)
`backend/app/routes/` 아래 4개 모듈, 각각 `APIRouter()`:

- `backend/app/routes/nodes.py`
  - `GET /node/{node_id}` — 노드 1개 + 이웃(`-[r]-(m)`, `NODE_NEIGHBOR_LIMIT=50` 제한) + 전체 이웃 수(`neighborTotal`). `Book` 라벨이면 `topPersons`/`topEvents` 추가 질의. `Person`이면 `traits` 속성을 JSON 파싱.
  - `GET /node/{node_id}/places` — 라벨별로 분기한 Cypher로 위경도 있는 `Place` 목록 반환(`isPrimary` 플래그 포함). Person→참여 사건의 장소, Event→직접 OCCURS_AT, PeopleGroup→구성원의 사건 장소, Book→포함 사건의 장소.
  - `GET /node/{node_id}/neighbors/grouped` — 타입별(`Person/Event/PeopleGroup/Place`)로 묶은 이웃. 타입당 `MAX_NEIGHBORS_PER_TYPE=30` 제한. 지도의 사건 링(event ring) 펼침에 사용.
- `backend/app/routes/events.py` — 타임라인 + 사건→구절 드릴다운(아래 5절 참조).
- `backend/app/routes/search.py` — `GET /search?q=` — `nameKo` 또는 소문자 `name`에 부분일치, 정확/접두/부분 순 랭크, `SEARCH_LIMIT=20`.
- `backend/app/routes/books.py` — `GET /books` — 타임라인 배치용 권 목록. `startYear`가 있으면 그대로, 없으면 `data/book_years_approx/books.json` 오버레이의 `placementYear`(이때 `yearApprox=true`). `data/book_events/books.json` 오버레이의 사건 id 배열도 `events` 필드로 merge. 연도를 못 얻는 권은 제외.

`books.py`와 `events.py`는 JSON 오버레이를 `functools.lru_cache(maxsize=1)`로 1회만 로드한다. 파일 경로는 `DATA_DIR`(기본 `/app/data`, docker 볼륨) 우선, 못 찾으면 레포 상대경로(`_REPO_DATA_DIR = .../data`)로 폴백 — docker/비-docker 양쪽에서 동작.

### 그래프 모델(데이터 적재 스크립트 기준)
`backend/scripts/load_theographic.py`가 정의하는 노드/관계:
- 노드: `Person`, `Place`, `Event`, `PeopleGroup` — 모두 `theographic_id` 키. `Book`은 `backend/scripts/load_books.py`가 적재.
- 저작(authored) 사건은 `backend/scripts/load_authored_events.py`가 `MERGE (e:Event {theographic_id})` + `authored=true` 마킹으로 적재. 식별자는 `authored-<slug>` 형식. `CONTAINS_BOOK` 관계는 만들지 않음(ADR-0005).
- 관계: `PARENT_OF`/`CHILD_OF`, `SIBLING_OF`, `PARTNER_OF`, `MEMBER_OF`(Person→PeopleGroup), `HAS_PARTICIPANT`(Event→Person), `OCCURS_AT`(Event→Place), `PART_OF`(Event→Event), `CONTAINS_BOOK`(Book→Event, `load_books.py`).

## 3. 프론트엔드 계층

### 진입점
- `frontend/index.html` → `frontend/src/main.jsx` — `createRoot`로 `<App/>`를 `StrictMode`에서 렌더.
- `frontend/src/App.jsx` — 루트 컴포넌트. 전역 상태(선택 노드, 활성 뷰, 검색)와 레이아웃(플로팅 nav 바, 전체화면 뷰, 오버레이 패널)을 관장.

### 공유 모듈
- `frontend/src/api.js` — `API_BASE`(빌드타임 `VITE_API_URL`, 프로덕션은 `/api`) + `apiGet(path, {signal})` 단일 GET 헬퍼. 비-OK는 status로 throw, abort는 그대로 전파.
- `frontend/src/theme.js` — 노드 타입 → 색/한글 라벨/표시순서의 **단일 정규 팔레트**(`TYPE_COLOR`, `TYPE_KO`, `TYPE_ORDER`, `typeColor()`, `typeKo()`, `SELECT_HL`). 모든 뷰가 여기서 import.
- `frontend/src/convexHull.js` — `convexHull(points)` Graham scan. 인물의 장소 ≥3개일 때 지도에 영역 폴리곤.
- `frontend/src/VerseLangTabs.jsx` — 절 본문 언어 전환 세그먼트 탭(한국어|영어). `App.jsx`의 `verseLang` 상태에 바인딩 — 한 곳에서 바꾸면 타임라인·SidePanel의 모든 본문이 함께 전환됨.

### 제거된 모듈
- `frontend/src/getbible.js` — 외부 한국어 성경 API fetch 모듈. ADR-0003 이후 절 본문이 `event_verses/events.json`에 빌드타임 베이크되어 런타임 외부 fetch가 불필요해졌음. 코드베이스에서 제거됨.

### 빌드
- `frontend/vite.config.js` — React 플러그인 + `manualChunks`로 `maplibre-gl`을 별도 `maplibre` 청크, 그 외 `node_modules`는 `vendor` 청크로 코드 스플리팅.

## 4. 세 뷰의 연결과 데이터 흐름

`frontend/src/App.jsx`가 허브다. 핵심 상태: `selectedNode`(선택 노드 id), `selectedNodeMeta`({label, nameKo, startYear, endYear}), `activeView`(`'map'`|`'timeline'`), 검색 상태, `history`(패널 뒤로가기 스택), `isMobile`, `verseLang`(절 본문 언어 `'ko'`|`'en'`).

- **선택 전파**: `selectNode(id)` 콜백(`useCallback([])`으로 참조 안정화 — 변경 시 하위 effect 재실행/abort 방지, 최신값은 `selectedNodeRef`로 읽음)을 모든 뷰·검색·패널에 내려준다. 직전 노드를 `history`에 쌓아 패널 뒤로가기 지원.
- **검색**: nav 바 입력 → 250ms 디바운스 → `apiGet('/search?q=')`(`AbortController`로 경쟁 차단) → 드롭다운(타입 필터 칩 + 키보드 네비). 결과 클릭 → `setSelectedNode`.

### MapView (`frontend/src/MapView.jsx`)
- MapLibre GL 지도(Esri NatGeo 래스터 타일). `selectedNode` 변경 effect가 `GET /node/{id}/places`를 fetch → `places-source` GeoJSON 세팅 + `fitBounds`. 위치 없으면 안내 배너(`noLocation`).
- 인물(`label==='Person'`, 장소 ≥3)이면 `convexHull`로 `hull-source` 폴리곤 표시.
- **사건 링(event ring)**: 마커 클릭/선택 시 `GET /node/{id}/neighbors/grouped`의 `Event`를 받아 장소 둘레로 fly-out 애니메이션(`requestAnimationFrame`, zoom-adaptive 반경). 링 버블 클릭 → `onSelectNode(eventId)`.
- 마커 클릭 → `onSelectNode(placeId)` → App이 선택 노드 갱신 → SidePanel 로드.

### SidePanel (`frontend/src/SidePanel.jsx`)
- `nodeId` prop 변경 시 `GET /node/{nodeId}`를 fetch. 응답을 `state.id`로 묶어 stale 무시. 로드 완료 시 `onNodeLoaded(node)` 콜백으로 App에 메타(`label`, 연도)를 전달 — App은 이를 타임라인의 `bookFilter`로 재사용(별도 fetch 없음).
- 이웃을 타입별 그룹으로 표시(`theme.js` 색). 이웃 클릭 → `onSelectNode`로 재탐색.
- `Book` 전용 뷰: 메타 칩, 시대적 배경/주제/대표 구절(`book_context` 유래 속성), `topPersons`/`topEvents`. `keyVerse`는 절 본문 직접 표시(ADR-0003, 빌드타임 베이크).
- `Person` 전용: `traits`(`character_traits` 유래) 표시. 각 trait의 `verse_ref` 절 본문도 빌드타임 베이크 데이터 활용.
- 데스크톱은 우측 슬라이드인, 모바일(`max-width:768px`)은 하단 시트(`SHEET_VH=55vh`, MapView의 `fitBounds` 하단 패딩과 일치). 레이아웃은 `App.jsx`가 결정.

### TimelineView (`frontend/src/TimelineView.jsx`)
- 마운트 시 `GET /events`(연도 가진 사건 + 각 사건의 근거 권 `books` + `authored`/`yearLabel` 플래그)와 `GET /books`(연도 가진 권 + `events` id 배열)를 fetch.
- 같은 `startDate` 사건을 그룹핑, `sortKey`로 정렬. 사건 그룹 + (사건 없는) 추정연도 권 마커를 연도순 통합 타임라인으로 렌더.
- **저작(authored) 사건 표기**: `ev.authored === true`이면 `추정` 배지(점선 테두리)를 사건 행에 표시. 연도 표시는 `ev.yearLabel`(예: "AD 62–64") 우선, 없으면 `parseYear(startDate)`.
- **책 마커의 배경 사건 칩**: `b.events`(id 배열)를 `eventById` Map으로 풀어 최대 3개 ⚡ 칩 표시. 칩 클릭 → `onSelectNode`. 라벨 "배경"으로 근거(📖)와 구분.
- `bookFilter`(App이 SidePanel 메타로 전달, 선택 노드가 Book일 때) 범위로 타임라인을 좁힌다. "닫기"는 `dismissedFilter`로 추적.
- 사건/권 행 클릭 → `onSelectNode`.

## 5. 사건→구절 드릴다운 데이터 흐름

타임라인에서 사건의 근거 성경 구절을 권→인용범위→절 본문 순으로 드릴다운한다.

1. **백엔드 — 사건별 근거 권**: `GET /events` (`backend/app/routes/events.py::get_events`)
   - `MATCH (e:Event) ... OPTIONAL MATCH (b:Book)-[:CONTAINS_BOOK]->(e)`로 각 사건에 그 사건을 기록한 성경권을 정경순(`bookOrder`)의 `books` 배열로 함께 반환. `books[].id`는 `theographic_id`. `authored`·`yearLabel` 필드도 반환.
2. **프론트 — 근거 권 칩**: `frontend/src/TimelineView.jsx`의 `renderBookChip`이 `ev.books`로 "📖 권이름 외 N권" 칩을 그린다. 칩 클릭 → `toggleVerseView(ev)`.
3. **백엔드 — 사건별 구절 오버레이**: `GET /event/{event_id}/verses` (`events.py::get_event_verses`)
   - DB가 아니라 `data/event_verses/events.json` 오버레이(`functools.lru_cache`)에서 사건 id로 조회. 구조: `{ "<eventId>": { "books": [{ bookId, bookOrder, rangeLabel, verses:[{verseID, chapter, verse, textKo, textEn}] }] } }`. `textKo`/`textEn`은 빌드타임 베이크(ADR-0003) — 런타임 외부 fetch 불필요.
4. **프론트 — 인라인 구절 뷰**: `frontend/src/TimelineView.jsx`
   - `toggleVerseView`가 `apiGet('/event/'+id+'/verses')`를 1회 fetch(`openEventRef`로 out-of-order 응답 stale 무시). 한 번에 한 사건만 펼침.
   - `verseView` 상태({eventId, bookId, expanded})로 권 탭 전환(`selectVerseBook`)과 절 본문 펼침(`toggleVerseText`)을 제어.
   - `renderVerseView`가 `ev.books`(권 이름) + 오버레이(`rangeLabel`·절)를 결합해 표시. `VerseLangTabs`로 한/영 전환 — `textKo`/`textEn`을 즉시 표시(추가 fetch 없음).
   - 저작 사건은 `CONTAINS_BOOK` 없어 `/event/{id}/verses`가 빈 books 반환 → 📖 칩 미표시.

흐름 요약: `Event 노드(Neo4j) ─CONTAINS_BOOK─ Book` → `/events` books 칩 → `/event/{id}/verses`(JSON 오버레이, 절 본문 베이크) → 인라인 렌더.

## 6. 정적 데이터 보강 파이프라인

`data/` JSON은 두 경로로 시스템에 들어온다:
- **DB에 주입**(Neo4j 속성으로 SET): `backend/scripts/inject_ko_names.py`(`data/names_ko/`), `backend/scripts/inject_book_context.py`(`data/book_context/`), `backend/scripts/inject_person_traits.py`(`data/character_traits/`). 한글 이름 주입은 `deploy.sh`가 배포 후 자동 실행(최대 15회 재시도).
- **DB에 Event 노드로 적재**: `backend/scripts/load_authored_events.py`(`data/authored_events/events.json`) — `MERGE` + `authored=true` 마킹. 호스트에서 직접 실행(Dockerfile에 포함 안 됨).
- **런타임 오버레이**(API가 직접 읽음): `data/book_years_approx/`(→ `/books` `startYear`+`yearApprox`), `data/book_events/`(→ `/books` `events` 배열), `data/event_verses/`(→ `/event/{id}/verses`).
- 생성 스크립트: `backend/scripts/generate_book_context.py`/`generate_person_traits.py`(Claude API), `backend/scripts/generate_event_verses.py`(theographic 원본 가공, 절 본문 getbible 베이크).

### 오버레이 vs. 그래프 분리 원칙 (ADR-0004/0005)
- **런타임 오버레이로 유지**: 추정·낮은권위 데이터 — `book_years_approx`(권 추정연도), `book_events`(권↔사건 집필배경 링크). `/books` 단일 엔드포인트만 소비. `CONTAINS_BOOK`에 주입하면 `/events`의 근거 칩이 오염됨 → 금지(ADR-0004).
- **마킹된 Neo4j 노드로 적재**: 저작(authored) 사건 — 사건은 `/events`·`/node/{id}`·지도·사건 링 등 4개 라우트가 일급 엔티티로 소비하므로 오버레이로 두면 모든 라우트에 머지 필요. `authored:true` 마킹으로 검증 사건과 구분(ADR-0005).

## 7. 배포 흐름

- `.github/workflows/deploy.yml` — `main` 푸시 시 self-hosted 러너가 `git reset --hard origin/main` 후 `deploy.sh` 실행.
- `deploy.sh` — (1) 프론트 `npm build` → `frontend/dist/`, (2) `docker compose build api`, (3) `docker compose up -d api nginx`, (4) `inject_ko_names.py` 한글 이름 주입.
- 백엔드는 hot-reload가 아님 — 코드 변경 반영에 이미지 재빌드 필요.
- 저작 사건 적재(`load_authored_events.py`)는 `deploy.sh`에 포함되지 않으며 수동으로 호스트에서 실행한다.
