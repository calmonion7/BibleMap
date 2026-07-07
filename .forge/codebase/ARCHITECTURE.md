---
last_mapped_commit: bb75a55a25c08e0ac06f8838ed029deb822762e3
mapped: 2026-07-07
---

# ARCHITECTURE

## 전체 구조

BibleMap은 세 개의 서비스로 구성된다.

- **Neo4j 5** — 성경 그래프 데이터 원본 (Person, Place, Event, Book, PeopleGroup 노드; OCCURS_AT, HAS_PARTICIPANT, CONTAINS_BOOK 등 관계)
- **FastAPI 백엔드** (`backend/`) — Neo4j 조회 + JSON 오버레이 머지, REST API 제공
- **Vite/React 프론트엔드** (`frontend/`) — 스테이지 상태 머신 + MapLibre GL 지도 + 타임라인

`docker-compose.yml`이 세 서비스를 묶는다: neo4j → api → nginx. nginx는 `:8080`을 외부에 노출하고, `/api` 경로를 내부 api 컨테이너(`:8000`)로 프록시한다. 프론트엔드 빌드 결과(`frontend/dist`)는 nginx가 정적 파일로 서빙한다.

## 백엔드 레이어

### 진입점 및 라우터 등록

`backend/app/main.py`가 FastAPI 앱을 생성하고, lifespan에서 Neo4j 인덱스(label별 `theographic_id`)를 생성한다. 아래 라우터를 모두 `include_router`로 등록한다.

| 파일 | 주요 엔드포인트 |
|---|---|
| `backend/app/routes/nodes.py` | `GET /node/{id}`, `GET /node/{id}/places`, `GET /node/{id}/neighbors/grouped`, `GET /person/{id}/event-ids` |
| `backend/app/routes/events.py` | `GET /events`, `GET /event/{id}/verses` |
| `backend/app/routes/search.py` | `GET /search?q=` |
| `backend/app/routes/books.py` | `GET /books-overview` |
| `backend/app/routes/persons.py` | `GET /persons/curated`, `GET /person/{id}/connections` |
| `backend/app/routes/journey.py` | `GET /person/{id}/journey` |
| `backend/app/routes/places.py` | `GET /place/{id}/curated-persons` |
| `backend/app/routes/tours.py` | `GET /tours`, `GET /tour/{id}` |

### Neo4j 접근

`backend/app/db.py`의 `get_driver()`가 싱글턴 드라이버를 반환한다. 연결 정보는 환경변수 `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`로 주입된다.

### JSON 오버레이 시스템

`backend/app/overlays.py`는 파일 경로 결정 로직을 두 함수로 제공한다. 두 함수 모두 동일한 우선순위 탐색 순서를 사용한다: 환경변수 `DATA_DIR`(기본값 `/app/data`) → 레포 내 `data/`.

- `_resolve(subpath)` — `os.path.isfile`로 존재 확인. 파일 경로 반환, 없으면 `None`.
- `_resolve_dir(subpath)` — `os.path.isdir`로 존재 확인. 디렉터리 경로 반환, 없으면 `None`.

`_load(subpath)`는 `_resolve`를 호출해 파일을 열고 JSON 파싱한다. `functools.lru_cache`를 적용한 두 public 로더가 있다.

- `book_events_raw()` — `data/book_events/books.json` → `{bookId: [eventId, ...]}`. `maxsize=1` 캐시.
- `event_verses()` — `data/event_verses/events.json` → 사건별 근거 구절(ADR-0003). `maxsize=1` 캐시.

### 여정(journey) 데이터 흐름

`journey.py`와 `tours.py`는 서로 다른 소스에서 동일한 `stops` 형태를 만들어 낸다.

- **인물 여정** (`GET /person/{id}/journey`): `data/person_events/<slug>.json`을 `sortKey` 기준으로 정렬 → 출현 장소 id 수집 → `_fetch_place_coords(place_ids)`로 Neo4j Place 노드에서 좌표 배치 조회 → stops 조립
- **테마 투어** (`GET /tour/{id}`): `data/tours/<slug>.json`의 `stops` 배열(eventId 참조) → `_build_event_index()`(전 큐레이션 인물의 `person_events/*.json`을 eventId 키로 인덱스) → 이벤트 해결(알 수 없는 id 제거 후 `sortKey` 순 재정렬) → 동일하게 `_fetch_place_coords` 사용 → stops 조립. 각 stop에는 `personNameKo` 필드가 추가된다(`_build_id_to_slug` → `_NAME_KO` 역참조).

투어 디렉터리 탐색은 `_tours_dir()`이 담당하며, 내부에서 `_resolve_dir("tours")`를 호출해 경로를 위임한다. 이전에는 경로 탐색 로직이 `_tours_dir()` 안에 직접 구현되어 있었으나 task 127 리팩터에서 `overlays._resolve_dir`로 일원화되었다.

두 엔드포인트 모두 `journey.py`의 `_fetch_place_coords`를 재사용하며 Neo4j 노드 추가 없이 순수 이벤트-참조 방식으로 동작한다(ADR-0011). 인물 여정 stops 형태: `{seq, eventId, title, nameKo, sortKey, placeId, placeNameKo, lng, lat}`. 투어 stops 형태: 동일 + `personNameKo`.

`_list_tours()`는 `_tours_dir()`이 반환한 디렉터리에서 `*.json`을 파일명 알파벳 순으로 스캔한 뒤, `_ERA_ORDER`(persons.py) 기준 시대 순·동시대 내 id 알파벳 순으로 정렬해 반환한다.

### 큐레이션 인물 관련 라우터

`persons.py`는 `_ERA` 딕셔너리(slug → era), `_NAME_KO` 딕셔너리(slug → 한글 이름), `_ERA_ORDER` 리스트(시대 순서)를 단일 출처로 보관한다. 현재 등록된 슬러그는 34개(원시사 6, 족장 4, 출애굽·정복 2, 사사 5, 왕국 4, 선지자 4, 포로 3, 신약 6)이다. `places.py`와 `tours.py`가 이 세 가지를 직접 import해 사용한다.

`GET /persons/curated`는 `person_events/<slug>.json`만으로 id·eventCount를 파생하고(Neo4j 조회 없음), `GET /person/{id}/connections`는 Neo4j에서 2-hop 공동등장 인물을 조회한다.

### 백엔드 스크립트

`backend/scripts/` 아래에는 Neo4j 적재(`load_*.py`)와 오버레이 생성(`generate_*.py`, `inject_*.py`, `enrich_*.py`) 스크립트가 있다. 앱 실행 경로가 아닌 데이터 파이프라인 전용이다.

## 프론트엔드 레이어

### 스테이지 상태 머신

`frontend/src/useStageNavigation.js`가 네 스테이지(`hub | explore | overview | tours`)를 소유한다. `App.jsx`가 이 훅을 소비하고 스테이지에 따라 조건 렌더링을 수행한다.

```
hub      → PersonHub 렌더
overview → BibleOverviewView 렌더
tours    → TourList 렌더
explore  → MapView + JourneyList + TimelineView 렌더
```

`explore` 스테이지에는 두 개의 상호배타 상태가 있다: `explorePersonId`(큐레이션 인물 theographic_id)와 `exploreTourId`(투어 slug). 둘 중 하나만 null이 아닐 수 있다. `MapView`, `JourneyList`, `TimelineView`는 둘 다 동일하게 소비한다 — 인물이면 `GET /person/{id}/journey`, 투어이면 `GET /tour/{id}`에서 stops를 가져와 `journeyStops` state에 저장하고 공유한다.

전환 핸들러 목록(모두 `useStageNavigation` 반환값):
- `selectPerson(id)` — 허브 카드 클릭 → explore(인물)
- `explorePerson(id)` — "이 곳을 지난 다른 인물" 칩 클릭 → explore(인물 전환, 투어 이탈)
- `backToHub()` — explore → hub
- `openOverview()` — hub → overview
- `overviewBack()` — overview → hub
- `openTours()` — hub → tours
- `selectTour(id)` — 투어 카드 선택 → explore(투어, 인물 null)
- `toursBack()` — explore(투어) → tours

### 노드 선택 분리

노드 선택 원시값(`selectedNode`, `history`, `selectNode`, `selectNodeFresh`, `goBack`, `closePanel`, `handleNodeLoaded`, `personEventIds`)은 `frontend/src/useNodeSelection.js`가 소유한다. `useStageNavigation`은 이 값들을 인자로 받아 상태 머신 로직과 섞지 않는다.

`selectNode`는 이전 노드를 history 스택에 쌓아 SidePanel 뒤로가기를 지원하며, `selectNodeFresh`는 history를 리셋한다(딥링크 복원·허브 진입에 사용).

### 해시 URL 딥링크 및 브라우저 뒤로가기

`frontend/src/urlState.js`가 URL 해시 ↔ 내비 상태 문자열 변환을 담당한다(라우팅 라이브러리 없음, ADR-0009).

```
#/                          hub
#/books                     overview
#/tours                     tours
#/person/<slug>             explore(인물, 지도)
#/person/<slug>/timeline    explore(인물, 타임라인)
#/tour/<slug>               explore(투어, 지도)
#/tour/<slug>/timeline      explore(투어, 타임라인)
```

`useStageNavigation`의 히스토리 동기화 effect(ADR-0010)가 스테이지·인물·투어 변경 및 시트 열림(false→true) 시 `pushState`, 그 외(뷰 토글·replace)에는 `replaceState`를 호출한다. `popstate` 이벤트는 `event.state`에서 직접 내비 상태를 복원한다. 재-push 방지를 위해 `popstateGuard` ref를 사용한다.

딥링크 복원 흐름: 마운트 시 `window.location.hash`를 `initialHashRef`에 캡처 → `/persons/curated`(slug↔id 매핑) 로드 완료 후 1회 파싱·상태 복원 → `setRestored(true)` → 이후 sync effect가 URL을 덮어쓰지 않도록 `restored` state를 gate로 사용.

### 지도 레이어

`frontend/src/MapView.jsx`가 MapLibre GL 지도를 마운트한다. 타일 소스는 ArcGIS NatGeo(라스터). 지도 관련 로직은 세 모듈로 분리된다.

- `mapGeo.js` — GeoJSON 생성(장소 피처, 여정 라인, 여정 stops, 아웃라이어 제외 bounds)
- `mapLayers.js` — 소스·레이어 초기화(`setupMapSources`), 클릭/호버 이벤트 핸들러 등록(`registerEventHandlers`)
- `mapRingController.js` — 장소 클릭 시 관련 사건 링 fly-out 애니메이션 제어

여정 stops는 MapView에도 전달되어 경로 라인과 번호 마커로 렌더된다. `activeStopIdx`(JourneyList ↔ MapView 공유 state, App이 소유)로 지도-리스트 양방향 동기화를 한다.

### 모바일·데스크톱 분기

`MOBILE_BREAKPOINT = 768px` 기준(MediaQueryList). 탐험 스테이지에서:
- **데스크톱**: JourneyList가 좌측 290px 고정 패널로, SidePanel이 우측 360px 슬라이드인으로 표시
- **모바일**: JourneyList가 지도 위 하단 42dvh 시트(`JOURNEY_SHEET_VH`)로, SidePanel이 75vh 하단 시트(`SHEET_VH`)로 표시. SidePanel은 탐험 인물 자신은 시트 열림 판정(`sheetOpen`)에서 제외해 여정 시트가 가려지지 않게 한다.
- 모바일 JourneyList의 📖 탭 클릭 시 `readingEventId`(App 소유)가 세팅되고 90dvh 읽기 모드로 확장된다.

### API 클라이언트

`frontend/src/api.js`의 `apiGet(path, {signal})` 함수가 모든 HTTP GET의 단일 진입점이다. `VITE_API_URL` 빌드타임 환경변수로 베이스 URL을 결정한다(프로덕션: `/api`, 개발: `http://localhost:8000`).

## 데이터 흐름 요약

```
data/person_events/<slug>.json  →  journey.py, tours.py(_build_event_index)
data/tours/<slug>.json          →  tours.py  (eventId 참조 resolve)
                                   tours.py._tours_dir() → overlays._resolve_dir("tours")
data/book_events/books.json     →  overlays.py → events.py (approx 책 연결)
data/event_verses/events.json   →  overlays.py → events.py /event/{id}/verses
Neo4j 그래프 노드/관계           →  nodes.py, events.py, search.py,
                                    books.py, persons.py(connections만),
                                    journey.py(_fetch_place_coords)
                                 →  REST JSON (Cache-Control: max-age=300)
                                 →  api.js (apiGet)
                                 →  App.jsx (journeyStops, selectedNode 등)
                                 →  MapView, JourneyList, TimelineView, SidePanel
```
