---
last_mapped_commit: 3837b4f9339ed2efb82a6b72cc1124a3340e2b9c
mapped: 2026-06-27
---

# ARCHITECTURE

BibleMap은 3-tier 단일 페이지 웹앱이다. React SPA가 nginx를 통해 정적 서빙되고, `/api`
프록시로 FastAPI 백엔드를 호출하며, 백엔드는 Neo4j 그래프 DB에 런타임 JSON 오버레이를
얹어 응답한다. 모든 컨테이너는 `docker-compose.yml` 한 파일로 묶인다.

```
브라우저 ──HTTP──> nginx(:8080→:80) ──정적──> frontend/dist (React 번들)
                       │
                       └─ /api/* ──프록시──> api(FastAPI, :8000)
                                                 │
                                                 ├─ bolt ──> neo4j(:7687)
                                                 └─ 파일 ──> data/*.json (오버레이)
```

## 레이어

### 1. 프론트엔드 — React 19 SPA (`frontend/src/`)

- 빌드 도구는 Vite(`frontend/vite.config.js`), 진입점은 `frontend/src/main.jsx`
  (`createRoot` + `StrictMode`). 루트 컴포넌트는 `frontend/src/App.jsx`.
- 상태 관리 라이브러리 없음. React 훅(`useState`/`useEffect`/`useRef`/`useCallback`)과
  커스텀 훅(`frontend/src/useNodeSelection.js`)만 사용. 라우터 없음 — 화면 전환은
  `App.jsx`의 `activeStage` 상태로 분기한다.
- 지도는 maplibre-gl(`maplibre-gl@5`), 아이콘은 lucide-react.
- 모든 백엔드 호출은 `frontend/src/api.js`의 `apiGet(path, {signal})` 하나를 거친다.
  베이스 URL은 `import.meta.env.VITE_API_URL`(프로덕션 `/api`) 또는
  `http://localhost:8000`(개발). 비-OK 응답은 `status` 필드를 단 Error로 reject,
  취소는 `AbortError`로 전파.

#### 2단계 정보구조 (인물 우선 재설계)

`App.jsx`는 `activeStage`(`'hub' | 'explore' | 'overview'`)로 3개 화면을 토글한다.
범용 검색 UI와 `useSearch.js` 훅은 제거되어 더 이상 존재하지 않는다(파일·참조 모두 부재
확인). 진입 흐름은 "인물 선택 → 탐험"으로 단일화됐다.

- **hub** (`PersonHub.jsx`) — 기본 화면. `GET /persons/curated`로 큐레이션 13인을
  받아 시대별(`족장`/`출애굽·정복`/`왕국`/`선지자`/`신약`) 카드로 보여준다.
  카드 클릭 시 `handleSelectPerson(id)` → 탐험 진입. "성경 책 둘러보기" 버튼으로
  overview 진입.
- **explore** — 인물 선택 후. 상단 네비(허브 복귀 + `지도`/`타임라인` 토글) 아래
  `MapView` 또는 `TimelineView`를 CSS `display` 토글로 항상 마운트한 채 전환(상태 보존).
  데스크톱은 지도 좌측에 `JourneyList`(여정 사건 리스트), 모바일은 지도 하단 미니
  수평 스크롤로 같은 stops를 보여준다.
- **overview** (`BibleOverviewView.jsx`) — `GET /books-overview`로 전체 성경권을
  장르별 카드로 보여주는 보조 화면.

#### 탐험 중 인물 분리 — `explorePersonId`

지도에서 장소를 클릭하면 `selectedNode`(SidePanel·상세 패널의 대상)는 장소로 바뀌지만,
"탐험 중인 인물"은 별도 상태 `explorePersonId`에 보존된다. `App.jsx`는
`explorePersonId`가 바뀔 때 한 번 `GET /person/{id}/journey`를 호출해 `journeyStops`를
받아 `MapView`와 `JourneyList`에 공유한다. `MapView`는 장소 fetch에 `personId ?? selectedNode`를
써서, 장소를 눌러도 지도 장소 집합은 인물 기준을 유지한다(`MapView.jsx` L70).
`SidePanel`의 "이 곳을 지난 인물" 칩(`onExplorePerson`)은 같은 탐험 단계에서 인물만
교체한다(`handleExplorePerson`).

#### 지도 모듈 분리 (4파일)

`MapView`는 셸/오케스트레이션만 맡고, 계산·레이어·애니메이션은 분리돼 있다.
이전의 convexHull 활동범위 면(`convexHull.js`)은 제거됐고(파일·참조 부재 확인),
대신 **여정선**(시간순 경로 + 순번 배지)으로 인물 활동을 표현한다.

- `frontend/src/MapView.jsx` — maplibre 인스턴스 생성/해제, 장소 fetch effect,
  여정선·정차지·활성 강조 effect, fitBounds 카메라 제어, 에러/위치없음 안내 UI.
- `frontend/src/mapGeo.js` — 순수 계산 함수. `coreBounds`(outlier 제외 프레이밍),
  `placesToGeoJSON`(동일좌표 라벨 방사 배치), `ringPositions`/`ringLabels`(사건 링),
  `buildJourneyLineGeoJSON`(누적거리 진행도 포함 LineString),
  `buildJourneyStopsGeoJSON`(동일좌표 dedup된 순번 배지), `buildSpiderGeoJSON`.
- `frontend/src/mapLayers.js` — maplibre source/layer 정의(`setupMapSources`)와
  클릭·hover 핸들러 등록(`registerEventHandlers`). 여정 레이어(`journey-line`,
  `journey-stop-circle`/`-label`, `journey-active-ring`), 장소 클러스터, 사건 링,
  스파이더 레이어를 포함. `EMPTY_GEOJSON` 상수 export.
- `frontend/src/mapRingController.js` — `createRingController(map, ...)` 팩토리.
  사건 링 펼침/접힘·스파이더 펼침/접힘의 가변 애니메이션 상태를 클로저에 캡슐화.

#### 노드 선택 상태 — `useNodeSelection.js`

`selectedNode`/`selectedNodeMeta`/`history`/`personEventIds`를 관리. `selectNode`는
히스토리 push(패널 뒤로가기), `selectNodeFresh`는 히스토리 리셋. `selectNode`는
`useCallback([])` + `selectedNodeRef`로 참조를 안정화해, 노드 변경 시 `MapView` effect의
불필요한 재실행/abort를 막는다. Person 선택 시 `GET /person/{id}/event-ids`로
`personEventIds`(타임라인 필터용 Set)를 채운다.

### 2. 백엔드 — FastAPI (`backend/app/`)

- 진입점 `backend/app/main.py`: `FastAPI(lifespan=...)`. lifespan에서 5개 라벨
  (`Person`/`Place`/`Event`/`PeopleGroup`/`Book`)에 `theographic_id` 인덱스를
  `IF NOT EXISTS`로 생성(실패해도 계속). CORS는 `allow_origins=["*"]`, GET만 허용.
- 라우터는 `app.include_router`로 7개 등록: `nodes`, `events`, `search`, `books`,
  `persons`, `journey`, `places`.
- DB 접근은 `backend/app/db.py`의 `get_driver()` 싱글턴(`bolt://`,
  `NEO4J_PASSWORD` 필수, 없으면 기동 시 RuntimeError). 세션은 라우트마다
  `with driver.session()`으로 연다.
- 런타임 JSON 오버레이는 `backend/app/overlays.py`: `_resolve(subpath)`가
  `DATA_DIR`(컨테이너 `/app/data`) → 레포 `data/` 순으로 파일을 찾고, `book_events_raw()`·
  `event_verses()`는 `functools.lru_cache`로 1회 로드 후 메모리 캐시.

#### 엔드포인트 (HEAD 기준 실재)

| 메서드/경로 | 파일 | 역할 |
|---|---|---|
| `GET /node/{id}` | `nodes.py` | 노드 + 이웃(최대 50) + 이웃 총수. Book이면 `topPersons`/`topEvents` 추가, Person이면 `traits` JSON 파싱 |
| `GET /node/{id}/places` | `nodes.py` | 라벨별 분기 쿼리로 좌표 있는 Place 목록(Person/Event/PeopleGroup/Book/Place) |
| `GET /node/{id}/neighbors/grouped` | `nodes.py` | 타입별 그룹 이웃(타입당 최대 30). 사건 링 펼침이 Event 목록을 여기서 가져옴 |
| `GET /person/{id}/event-ids` | `nodes.py` | 인물 참여 사건 id 목록(타임라인 필터) |
| `GET /events` | `events.py` | 타임라인 사건 + 각 사건의 근거 성경권(CONTAINS_BOOK + 추정책) |
| `GET /event/{id}/verses` | `events.py` | 사건 근거구절(권별 그룹, `bookNameKo` 포함) — 드릴다운용 |
| `GET /search?q=` | `search.py` | nameKo/name 부분일치 검색(상위 20). 프론트 검색 UI는 제거됐으나 라우트는 잔존 |
| `GET /books-overview` | `books.py` | 개요 뷰용 전체 성경권(`Cache-Control: no-store`) |
| `GET /persons/curated` | `persons.py` | 큐레이션 13인 — `person_events/*.json`에서 정적 산출(Neo4j 미조회) |
| `GET /person/{id}/journey` | `journey.py` | 인물 시간순 여정 정차지(파일에서 sortKey 정렬 + Neo4j로 좌표 배치 조회). 13인 외엔 빈 stops |
| `GET /place/{id}/curated-persons` | `places.py` | 그 장소를 여정에 포함한 13인(파일 기반, `exclude` 쿼리 지원) |

> 참고: 과거 `GET /books` 엔드포인트와 `approx_years()` 헬퍼는 제거됐다(부재 확인).

### 3. 데이터 — Neo4j + JSON 오버레이

- 그래프 노드는 `theographic_id`로 식별. 관계 예: `HAS_PARTICIPANT`, `OCCURS_AT`,
  `CONTAINS_BOOK`, `MEMBER_OF`, `PARENT_OF` 등(`SidePanel.jsx` `REL_KO` 매핑 참고).
- 그래프에 없는 보조 데이터(한글 이름, 사건-구절, 인물 여정, 장소 맥락 등)는 레포
  `data/<도메인>/*.json` 오버레이로 둔다. 일부는 앱 기동 시 Neo4j에 주입
  (`backend/scripts/inject_*.py`), 일부는 백엔드가 런타임에 직접 읽는다
  (`overlays.py`, `persons.py`/`journey.py`/`places.py`의 `person_events/`).

## 데이터 흐름 예시

### 인물 탐험 (대표 흐름)

1. 앱 기동 → `PersonHub`가 `GET /persons/curated` → 13인 카드 렌더.
2. 카드 클릭 → `App.handleSelectPerson(id)`: `selectNodeFresh(id)` +
   `setExplorePersonId(id)` + `activeStage='explore'`.
3. `explorePersonId` effect → `GET /person/{id}/journey` → `journeyStops` 설정.
4. `MapView`가 `journeyStops`로 여정선·순번 배지를 그리고, `GET /node/{id}/places`로
   인물 활동 장소 마커를 찍은 뒤 `coreBounds`로 프레이밍.
5. 동시에 `SidePanel`이 `GET /node/{id}`로 인물 상세(성품 traits 등) 표시.
6. 지도에서 장소 클릭 → `selectNode(placeId)`(SidePanel은 장소로), 단 지도 장소·여정은
   `explorePersonId` 기준 유지. SidePanel은 `GET /place/{id}/curated-persons`로
   "이 곳을 지난 인물" 칩 표시 → 칩 클릭 시 같은 탐험에서 인물 교체.

### 사건 링 펼침

장소 마커 클릭 → `mapLayers` 핸들러 → `mapRingController.expandPlace` →
`GET /node/{placeId}/neighbors/grouped`의 `Event`를 현재 줌의 화면 80px 반경 링으로
애니메이션 배치.

### 타임라인 + 근거구절

`exploreView='timeline'` → `TimelineView`가 `GET /events`로 전 사건을 받아 연도순 표시
(`personFilter`로 인물 사건만 필터). 사건의 "구절" 칩 → `GET /event/{id}/verses` 드릴다운.
절 본문(textKo/textEn)은 응답에 미리저장돼 추가 fetch 없이 `verseLang`으로 토글.

## 인프라 / 배포

- `docker-compose.yml`: `neo4j`(5, 127.0.0.1 바인딩), `api`(`backend/Dockerfile`,
  uvicorn, `./data:/app/data` 마운트), `nginx`(:8080→:80, `frontend/dist`와
  `nginx/nginx.conf`를 읽기전용 마운트).
- **빌드 산출물 마운트 (HMR 아님)**: nginx는 `frontend/dist`를 그대로 서빙하므로
  프론트 변경은 `npm run build` 후에만 반영된다. `.env.production`의
  `VITE_API_URL=/api`가 빌드타임에 주입돼 nginx `/api/` 프록시(`http://api:8000/`)를 탄다.
  API 포트(:8000)는 외부 노출 없음.
- `nginx/nginx.conf`: `/api/`는 프록시, `index.html`은 no-cache, 해시 에셋은
  1년 immutable, 그 외는 SPA fallback(`try_files $uri /index.html`).
- `deploy.sh`: 프론트 빌드 → `docker compose -p biblemap build api` → `up -d api nginx`
  → `inject_ko_names.py`로 한글 이름 주입(Neo4j 준비까지 최대 15회 재시도). CI는
  self-hosted 러너에서 `.github/workflows/deploy.yml`로 트리거.

## 추상화 요약

- 단일 API 클라이언트(`api.js`) — 베이스 URL·에러·취소 시맨틱 일원화.
- 타입 팔레트 단일 정규화(`theme.js` `TYPE_COLOR`/`TYPE_KO`) — 모든 뷰 공유.
- 지도 관심사 분리 — 셸(MapView) / 순수계산(mapGeo) / 레이어(mapLayers) /
  애니메이션 상태(mapRingController).
- DB 드라이버 싱글턴(`db.py`)과 오버레이 캐시(`overlays.py` lru_cache).
- 큐레이션 13인 상수(`_ERA`/`_NAME_KO`/`_ERA_ORDER`)는 `persons.py`/`places.py`/
  `journey.py`·프론트 `PersonHub.jsx`에 각각 선언(순환참조 회피 위해 중복 허용).
