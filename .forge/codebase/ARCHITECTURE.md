---
last_mapped_commit: 79f9d9df07c0d79f8fa07940e3f76c8d5424524b
mapped: 2026-06-28
---
<!-- refreshed: 2026-06-28 -->
# Architecture

**Analysis Date:** 2026-06-28

## System Overview

```text
┌─────────────────────────────────────────────────────────────┐
│                  브라우저 (React 19 SPA)                      │
├──────────────────┬──────────────────┬───────────────────────┤
│    PersonHub     │  MapView/Timeline │      SidePanel        │
│  `PersonHub.jsx` │  `MapView.jsx`    │   `SidePanel.jsx`     │
│  (허브 단계)      │  (탐험 단계)       │   (상세 패널)          │
└────────┬─────────┴────────┬─────────┴──────────┬────────────┘
         │  apiGet(path)     │                     │
         ▼ `frontend/src/api.js` (단일 fetch 헬퍼)  ▼
┌─────────────────────────────────────────────────────────────┐
│                nginx (`nginx/nginx.conf`)                    │
│  정적 dist 서빙 + /api/ → api:8000 리버스 프록시              │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│             FastAPI (`backend/app/main.py`)                  │
│  routes/ (nodes·events·search·books·persons·journey·places)  │
│  ├─ Neo4j 그래프 조회 (`backend/app/db.py`)                   │
│  └─ JSON 오버레이 파일 (`backend/app/overlays.py` → `data/`)   │
└────────┬───────────────────────────────┬────────────────────┘
         ▼                                ▼
┌──────────────────────┐       ┌──────────────────────────────┐
│  Neo4j 5 (그래프 DB)  │       │  data/*.json (정적 오버레이)   │
│  bolt://neo4j:7687    │       │  여정·근거구절·한글이름·시대    │
└──────────────────────┘       └──────────────────────────────┘
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| `App` | 단계(hub/explore/overview) 라우팅, 여정 fetch, 패널/시트 레이아웃 | `frontend/src/App.jsx` |
| `useNodeSelection` | 선택 노드·메타·히스토리·인물 사건 ID 상태 훅 | `frontend/src/useNodeSelection.js` |
| `PersonHub` | 큐레이션 13인 시대별 카드 그리드 (탐험 진입점) | `frontend/src/PersonHub.jsx` |
| `MapView` | MapLibre 지도 컨테이너·effect 오케스트레이션 | `frontend/src/MapView.jsx` |
| `mapGeo` | 순수 지오메트리/GeoJSON 빌더 (라벨 앵커·여정선·정차지 그룹) | `frontend/src/mapGeo.js` |
| `mapLayers` | MapLibre source/layer 정의 + 이벤트 핸들러 등록 | `frontend/src/mapLayers.js` |
| `mapRingController` | 사건 링/스파이더 애니메이션 클로저 컨트롤러 | `frontend/src/mapRingController.js` |
| `JourneyList` | 여정 정차지 사이드 리스트 (활성 동기화) | `frontend/src/JourneyList.jsx` |
| `TimelineView` | 시간순 사건 타임라인 + 근거구절 드릴다운 | `frontend/src/TimelineView.jsx` |
| `SidePanel` | 노드 상세 + 이웃 그룹 + 근거구절/인물 칩 | `frontend/src/SidePanel.jsx` |
| `BibleOverviewView` | 성경 66권 장르별 개요 | `frontend/src/BibleOverviewView.jsx` |
| `theme` | 타입 색·한글 라벨 단일 팔레트 | `frontend/src/theme.js` |
| FastAPI 라우터들 | 노드/사건/검색/책/인물/여정/장소 REST 엔드포인트 | `backend/app/routes/` |
| `db.get_driver` | Neo4j 드라이버 싱글턴 | `backend/app/db.py` |
| `overlays` | `data/*.json` 오버레이 로드·lru_cache | `backend/app/overlays.py` |

## Pattern Overview

**Overall:** 클라이언트-서버 SPA. React 19 프론트(상태 끌어올림 + 커스텀 훅) + FastAPI REST 백엔드(라우터별 분리). 데이터는 Neo4j 그래프 + 정적 JSON 오버레이 2원화.

**Key Characteristics:**
- 프론트 상태는 `App.jsx`에 집중하고 props로 하향 전달 — 전역 스토어(Redux 등) 없음.
- 모든 fetch는 `frontend/src/api.js`의 `apiGet` 단일 헬퍼를 경유(베이스 URL·에러·AbortError 일원화).
- 백엔드는 라우터 파일별 책임 분리(`backend/app/routes/*.py`), 각 라우터가 `get_driver()`로 Neo4j 세션을 직접 열고 닫음.
- 비용 큰 조회·파일 파싱은 `functools.lru_cache`로 프로세스 수명 캐시(`events.py`, `persons.py`, `places.py`).
- 지도 렌더는 명령형 MapLibre API를 React effect로 감싸는 형태 — source/layer 정의(`mapLayers.js`), 순수 빌더(`mapGeo.js`), 애니메이션 컨트롤러(`mapRingController.js`)로 분리.

## Layers

**프레젠테이션 (React 컴포넌트):**
- Purpose: UI 렌더·사용자 입력. 단계 전환·패널 표시.
- Location: `frontend/src/*.jsx`
- Contains: 화면 컴포넌트(인라인 스타일), 커스텀 훅
- Depends on: `api.js`, `theme.js`, `constants.js`, MapLibre
- Used by: `main.jsx` 엔트리

**지도 도메인 (MapView 보조 모듈):**
- Purpose: MapLibre source/layer·지오메트리·애니메이션을 컴포넌트에서 분리.
- Location: `frontend/src/mapGeo.js`, `frontend/src/mapLayers.js`, `frontend/src/mapRingController.js`
- Contains: 순수 함수(GeoJSON 빌더, 라벨 앵커 계산), 명령형 MapLibre 헬퍼, requestAnimationFrame 클로저
- Depends on: `maplibre-gl`, `api.js`
- Used by: `MapView.jsx`

**API 클라이언트:**
- Purpose: 단일 fetch 진입점.
- Location: `frontend/src/api.js`
- Contains: `apiGet(path, { signal })`
- Depends on: `import.meta.env.VITE_API_URL`
- Used by: 모든 데이터 fetch 컴포넌트/훅

**REST 라우팅 (FastAPI):**
- Purpose: HTTP 엔드포인트 → 데이터 조회 → JSON.
- Location: `backend/app/routes/`
- Contains: APIRouter별 GET 핸들러
- Depends on: `db.py`, `overlays.py`
- Used by: nginx 프록시를 통한 프론트

**데이터 소스:**
- Purpose: 그래프 사실 + 정적 보강.
- Location: Neo4j(`db.py`) + `data/*.json`(`overlays.py`)
- Contains: 노드/관계, 여정 사건 시퀀스, 근거구절, 한글 이름, 시대 매핑
- Used by: 라우터들

## Data Flow

### 인물 선택 → 지도 여정 표시 (주 경로)

1. `PersonHub`에서 카드 클릭 → `onSelectPerson(id)` (`frontend/src/PersonHub.jsx:41`)
2. `App.handleSelectPerson`이 `explorePersonId` 설정 + 단계를 `explore`로 전환 (`frontend/src/App.jsx:65`)
3. `App`의 effect가 `GET /person/{id}/journey` fetch → `journeyStops` 상태 (`frontend/src/App.jsx:51`)
4. 백엔드 `journey.get_person_journey`가 `data/person_events/{slug}.json`을 sortKey 정렬 + Neo4j에서 Place 좌표 배치 조회 → seq 부여 (`backend/app/routes/journey.py:73`)
5. `MapView`가 `journeyStops` prop 변경 effect에서 `buildJourneyLineGeoJSON`·`buildJourneyStopsGeoJSON`로 여정선/배지 source 갱신 (`frontend/src/MapView.jsx:155`)
6. 별도 effect가 `GET /node/{personId}/places`로 마커 source 갱신 + `fitBounds` 프레이밍 (`frontend/src/MapView.jsx:82`)

### 장소 마커 클릭 → 사건 링 펼침

1. `places-circle` 클릭 핸들러가 겹침 검사 후 `expandPlace(id, lng, lat)` 호출 (`frontend/src/mapLayers.js:32`)
2. `expandPlace`가 `GET /node/{id}/neighbors/grouped` fetch → Event 이웃 추출 (`frontend/src/mapRingController.js:100`)
3. `ringPositions`/`ringLabels`로 링 좌표·라벨 앵커 계산, requestAnimationFrame으로 중심→링 fly-out 애니메이션 (`frontend/src/mapRingController.js:128`)
4. 재클릭 시 `expandedPlaceRef.current.id` 비교로 `collapseRing()` 토글 (`frontend/src/mapLayers.js:43`)

### 여정 정차지 활성 동기화 (지도 ↔ 리스트)

1. `JourneyList`/모바일 미니시트/지도 배지 클릭이 `setActiveStopIdx(dedupIdx)` (`frontend/src/App.jsx:276`, `frontend/src/JourneyList.jsx:60`)
2. 지도 `journey-stop-circle` 클릭은 `seq - 1`을 0-based 인덱스로 변환해 전달 (`frontend/src/mapLayers.js:123`)
3. `MapView`의 `activeStopIdx` effect가 `journeyStopGroups`로 장소 단위 그룹 인덱싱 → 활성 source 갱신 + `easeTo` 카메라 이동 (`frontend/src/MapView.jsx:166`)

**State Management:**
- 단일 책임 상태 끌어올림: `App.jsx`가 `activeStage`·`exploreView`·`explorePersonId`·`journeyStops`·`activeStopIdx`·`verseLang`을 보유하고 props로 하향.
- 노드 선택 상태는 `useNodeSelection` 훅에 캡슐화(selectedNode·history·personEventIds). `selectNode`/`handleNodeLoaded`는 `useCallback([])`로 참조 안정화 — effect 재실행으로 인한 fetch abort 방지(훅 주석 참조).
- 지도 가변 상태(펼친 장소·애니메이션 프레임)는 React state가 아닌 ref/클로저(`expandedPlaceRef`, `createRingController`)로 관리.

## Key Abstractions

**여정 정차지 그룹(journeyStopGroups):**
- Purpose: 같은 좌표의 여러 사건을 한 정차지로 묶고, 사건 순번(seq)을 압축 표기로 라벨링.
- Examples: `frontend/src/mapGeo.js:157` (`journeyStopGroups`), `frontend/src/mapGeo.js:137` (`compactSeqs`)
- Pattern: 좌표 키(`lng,lat`)로 그룹핑 → 첫 등장 순서 유지 → seq 배열을 `"6-8, 10"` 식 압축. 지도 배지·리스트가 동일 사건 순번을 공유해 일치. `JourneyList.jsx`도 같은 dedup 로직을 재구현(coKey→인덱스 매핑).

**라벨 앵커 계산(outwardLabel/ringLabels):**
- Purpose: 마커 라벨을 이웃/링 중심 반대쪽으로 밀어 충돌 회피. 동일 좌표 그룹은 방사 배치.
- Examples: `frontend/src/mapGeo.js:19` (`outwardLabel`), `frontend/src/mapGeo.js:33` (`ringLabels`), `frontend/src/mapGeo.js:41` (`placesToGeoJSON`)
- Pattern: 화면 기준 8방위 text-anchor + text-offset. lng 기준 링은 화면상 세로로 늘어나므로 `cos(lat)` 보정.

**링 컨트롤러 클로저(createRingController):**
- Purpose: 사건 링/스파이더 애니메이션의 가변 상태(animFrame·spiderState·expandedPlace)를 클로저에 캡슐화.
- Examples: `frontend/src/mapRingController.js:7`
- Pattern: `{ collapseRing, collapseSpider, expandPlace, spiderifyPlaces, destroy }` 반환. `expandedPlace`는 컴포넌트 ref와 공유해 클릭 핸들러가 펼침 상태를 읽음.

**오버레이 해석(_resolve):**
- Purpose: 컨테이너(`/app/data`)·레포(`data/`) 양쪽에서 JSON 파일을 찾는 데이터 디렉터리 추상화.
- Examples: `backend/app/overlays.py:11`
- Pattern: `DATA_DIR` 환경변수 → 레포 상대경로 순으로 첫 존재 파일 반환. `journey.py`·`persons.py`·`places.py`가 직접 사용.

**theographic_id 노드 키:**
- Purpose: 모든 그래프 노드의 안정적 외부 식별자.
- Examples: `backend/app/routes/nodes.py` 전반, `backend/app/main.py:14` (인덱스 생성)
- Pattern: 모든 Cypher가 `{theographic_id: $id}`로 매칭. 라벨별(`Person`/`Place`/`Event`/`PeopleGroup`/`Book`) 인덱스를 lifespan에서 생성.

## Entry Points

**프론트엔드 SPA:**
- Location: `frontend/src/main.jsx` → `frontend/src/App.jsx`
- Triggers: 브라우저가 nginx가 서빙한 `index.html` 로드
- Responsibilities: React 루트 마운트(StrictMode), 단계 라우팅

**백엔드 API:**
- Location: `backend/app/main.py` (`uvicorn app.main:app`)
- Triggers: Dockerfile CMD (`backend/Dockerfile:6`)
- Responsibilities: 라우터 등록, CORS(GET only), lifespan에서 Neo4j 인덱스 생성

**배포 스크립트:**
- Location: `deploy.sh`
- Triggers: GitHub Actions self-hosted 러너 (`.github/workflows/deploy.yml`)
- Responsibilities: 프론트 빌드 → API 이미지 빌드 → 컨테이너 재시작 → 한글 이름 주입(`backend/scripts/inject_ko_names.py`)

## Architectural Constraints

- **Threading:** 백엔드는 단일 uvicorn 프로세스. Neo4j 드라이버는 모듈 전역 싱글턴(`db._driver`), 라우터마다 `with driver.session()`으로 세션 생성. 프론트는 단일 스레드(브라우저), 애니메이션은 requestAnimationFrame.
- **Global state:** `db._driver`(전역 드라이버), `overlays`의 `lru_cache`(`book_events_raw`/`event_verses`), `events.py`·`places.py`·`persons.py`의 `@functools.lru_cache` — 데이터 변경 시 프로세스 재시작 필요. 프론트엔드 지도 가변 상태는 `expandedPlaceRef`/컨트롤러 클로저.
- **Circular imports:** `places.py`가 `persons.py`의 상수(`_ERA`/`_NAME_KO`)를 import하지 않고 의도적으로 재선언(단방향 참조 회피, `backend/app/routes/places.py:15` 주석). `journey.py`는 `persons.py`에서 `_ERA`/`_NAME_KO`를 import함.
- **여정 seq 기반 동기화:** 지도 배지·리스트·활성 강조가 모두 사건 seq(좌표 있는 정차지에 1부터 부여)를 기준으로 일치해야 함. 동일 좌표 그룹핑 로직이 `mapGeo.journeyStopGroups`와 `JourneyList.jsx`에 중복 존재 — 한쪽 변경 시 양쪽 동기 필요.

## Anti-Patterns

### 여정 그룹핑 로직 이중 구현

**What happens:** 좌표 dedup + seq→인덱스 매핑이 `frontend/src/mapGeo.js:157`(`journeyStopGroups`)와 `frontend/src/JourneyList.jsx:21-31`에 각각 구현돼 있다.
**Why it's wrong:** 한쪽만 수정하면 지도 배지와 리스트 활성 인덱스가 어긋난다(클릭 시 다른 정차지가 강조됨).
**Do this instead:** 그룹핑은 `mapGeo.journeyStopGroups` 한 곳에서만 계산하고 `JourneyList`도 그 결과(또는 동일 헬퍼)를 import해 쓴다.

### effect 내 동기 setState

**What happens:** `App.jsx`의 여정 effect는 인물 미선택 시 `Promise.resolve().then(() => setJourneyStops(null))`로 비동기 setState한다(`frontend/src/App.jsx:48`).
**Why it's wrong:** eslint `react-hooks` 규칙이 effect 본문 동기 setState를 금지(set-state-in-effect)하기 때문에 우회한 형태로, 의도가 코드만 봐선 불명확하다.
**Do this instead:** 가능하면 파생 상태로 계산하거나 초기화 시점을 명시적 이벤트 핸들러로 옮긴다(현 코드는 주석으로 의도를 표기).

## Error Handling

**Strategy:** 프론트는 fetch 실패를 컴포넌트 로컬 `error`/`noLocation` 상태로 받아 인라인 배너 표시. AbortError는 무시. 백엔드는 노드 미존재 시 `HTTPException(404)`, 그 외는 빈 결과/기본값 반환.

**Patterns:**
- `apiGet`이 비-OK 응답을 `err.status` 포함 Error로 throw, 호출부가 `e.name === 'AbortError'`로 취소를 구분 (`frontend/src/api.js:7`).
- `MapView`는 `mapRef.current !== map` 체크로 언마운트 후 stale 콜백 무시 (`frontend/src/MapView.jsx:83`).
- 백엔드 lifespan의 인덱스 생성 실패는 `logging.exception` 후 계속 진행 (`backend/app/main.py:19`).
- 여정/큐레이션 엔드포인트는 비대상 인물에 404 대신 빈 `stops`/리스트 반환 (`backend/app/routes/journey.py:84`).

## Cross-Cutting Concerns

**Logging:** 백엔드는 표준 `logging`(lifespan 예외만). 배포는 `deploy.sh`가 `com.biblemap.deploy.log`에 기록. 프론트는 console 미사용(인라인 UI 배너).
**Validation:** 입력 검증 최소 — 경로 파라미터를 그대로 Cypher `$id` 바인딩(파라미터화로 injection 방지). `search.py`는 빈 쿼리 가드.
**Authentication:** 없음. CORS `allow_origins=["*"]`, GET 메서드만 허용 (`backend/app/main.py:25`). 읽기 전용 공개 API.
**Caching:** 라우터들이 `Cache-Control` 헤더(`max-age=300`~`3600`, overview는 `no-store`) + 서버측 `lru_cache`. nginx는 해시 에셋 immutable 캐시, `index.html`은 no-store (`nginx/nginx.conf:20`).

---

*Architecture analysis: 2026-06-28*
