---
last_mapped_commit: 0189ad9fb964e5eb4fcc91776b3202f7014058dd
mapped: 2026-07-02
---
# 코딩 컨벤션

프론트엔드(`frontend/src/`, React 19 + Vite, JS/JSX)와 백엔드(`backend/app/`, FastAPI + Neo4j, Python 3.12)로 나뉜다. 데이터 적재·생성 스크립트는 `backend/scripts/`에 별도 규칙으로 모여 있다. **사람이 읽는 주석·독스트링·UI 문자열은 전부 한글로, 식별자·키·경로는 영어로** 작성한다.

---

## 네이밍 패턴

### 파일

- **React 컴포넌트:** PascalCase `.jsx` — `MapView.jsx`, `SidePanel.jsx`, `PersonHub.jsx`, `JourneyList.jsx`, `TimelineView.jsx`, `BibleOverviewView.jsx`, `Spinner.jsx`, `VerseLangTabs.jsx`, `EventVerses.jsx`. 파일 1개 = 기본 export 컴포넌트 1개.
- **비컴포넌트 모듈(헬퍼·훅·상수):** camelCase 또는 소문자 `.js` — `api.js`, `theme.js`, `constants.js`, `mapGeo.js`, `mapLayers.js`, `mapRingController.js`, `useNodeSelection.js`.
- **커스텀 훅:** `use` 접두사 + camelCase 파일·함수 — `frontend/src/useNodeSelection.js`의 `export function useNodeSelection()`. 단, `PersonHub.jsx` 내부의 `useIsMobile`은 컴포넌트 파일에 동거하는 로컬 훅.
- **백엔드 라우트 모듈:** 소문자 단수/복수 `.py` — `nodes.py`, `events.py`, `persons.py`, `places.py`, `journey.py`, `books.py`, `search.py`. 라우터 1개 = 모듈 1개.
- **백엔드 스크립트:** `동사_명사.py` 스네이크케이스 — `load_*`(Neo4j 적재), `generate_*`(데이터 산출), `inject_*`(노드 속성 주입), `enrich_*`(좌표 보강). 동사 접두사로 역할을 구분한다(`backend/scripts/`).

### 함수

- **JS:** camelCase. 컴포넌트는 PascalCase. 이벤트 핸들러는 `handle` 접두사(`handleSelectPerson`, `handleBackToHub`, `handleSidePanelNodeLoaded` — `frontend/src/App.jsx`). 콜백 prop은 `on` 접두사(`onSelectPerson`, `onStopSelect`, `onOpenOverview`, `onNodeLoaded`).
- **Python:** snake_case. FastAPI 엔드포인트 함수는 `get_` 접두사 관례(`get_node`, `get_person_journey`, `get_curated_persons`, `get_events`, `get_event_verses` — `nodes.py`/`journey.py`/`persons.py`/`events.py`).
- **모듈 내부 전용 함수:** Python은 `_` 접두사 — `_resolve`/`_load`(`backend/app/overlays.py`), `_build_list`(`persons.py`), `_build_id_to_slug`/`_load_events`/`_fetch_place_coords`(`journey.py`), `_compute_events`/`_load_approx_book_index`/`_book_name_map`(`events.py`), `_place_to_persons`(`places.py`). JS는 헬퍼를 export하지 않는 모듈-로컬 함수로 두며(`outwardLabel`, `compactSeqs` — `mapGeo.js`), 표준 export는 명명 export로 선언한다.

### 변수·상수

- **모듈 레벨 상수:** 양쪽 모두 UPPER_SNAKE. Python — `SEARCH_LIMIT`(`search.py`), `MAX_NEIGHBORS_PER_TYPE`/`NODE_NEIGHBOR_LIMIT`(`nodes.py`), `_ERA`/`_NAME_KO`/`_ERA_ORDER`(앞에 `_`가 붙은 모듈-사적 매핑, `persons.py`에 단일 선언). JS — `API_BASE`(`api.js`), `MOBILE_BREAKPOINT`/`SHEET_VH`(`constants.js`), `TYPE_COLOR`/`TYPE_KO`/`TYPE_ORDER`/`SELECT_HL`(`theme.js`).
- **노드 식별자:** 그래프 노드는 `theographic_id`(Neo4j 속성)를 API 응답에서 `id`로 노출. 프론트는 이 `id`를 그대로 키로 쓴다.

---

## API 경로 규약

- **단수 리소스 + 동사:** `/person/{id}/journey`, `/person/{id}/event-ids`, `/place/{id}/curated-persons`, `/node/{id}`, `/node/{id}/places`, `/node/{id}/neighbors/grouped`, `/event/{id}/verses`.
- **복수 목록:** `/events`, `/persons/curated`, `/books-overview`, `/search`.
- 모든 라우터는 `backend/app/main.py`에서 `app.include_router(...)` 7회로 등록.

---

## 백엔드 (Python / FastAPI / Neo4j)

### 라우트 모듈 구조

모든 라우트 모듈은 동일 골격을 따른다(`backend/app/routes/*.py`):

1. 표준 라이브러리 → FastAPI → 상대 임포트(`from ..db import get_driver`, `from ..overlays import ...`) 순.
2. `router = APIRouter()`를 모듈 최상단에 하나.
3. `_` 접두사 내부 헬퍼(데이터 적재·머지·캐시) 정의.
4. `@router.get(...)` 데코레이터 엔드포인트가 헬퍼를 호출해 응답을 조립.

엔드포인트는 대부분 `JSONResponse(content=..., headers={"Cache-Control": ...})`로 반환해 캐시 정책을 명시한다(`max-age=300` — 인물 목록·여정·장소별 인물·이벤트 목록·구절 등 Neo4j 또는 파일 기반 동적 결과, `no-store` — `/books-overview`). 순수 리스트/딕트를 그대로 반환하는 엔드포인트(`search.py`, `nodes.py` 일부)는 FastAPI 자동 직렬화에 맡긴다.

### `lru_cache` 오버레이 적재 패턴

JSON 오버레이·파일 기반 정적 데이터는 `@functools.lru_cache(maxsize=1)`로 감싼 빌더 함수에서 한 번 로드해 프로세스 메모리에 보관한다. 앱 재시작 전까지 디스크/Neo4j를 재조회하지 않는다.

- `backend/app/overlays.py`: `_resolve(subpath)`가 `$DATA_DIR`(기본 `/app/data`) → 리포 내 `data/`를 순서대로 탐색해 첫 존재 파일 경로 반환(없으면 `None`). `_load`는 그 위에서 JSON을 읽고 `JSONDecodeError`·부재 시 빈 dict로 폴백. `book_events_raw()`·`event_verses()`가 `@lru_cache(maxsize=1)` 오버레이.
- `events.py`의 `_load_approx_book_index`/`_compute_events`/`_book_name_map`, `persons.py`의 `_build_list`는 모두 `@lru_cache(maxsize=1)` — Neo4j 1회 조회 + 오버레이 머지 결과를 캐시.
- `places.py`의 `_place_to_persons(place_id)`는 인자별 캐시가 필요해 `@functools.lru_cache(maxsize=None)`.
- `/persons/curated`, `/place/{id}/curated-persons`는 파일만으로 결정적인 응답이므로 Neo4j를 타지 않는다. 독스트링에 "단순성 우선"으로 명시.

### 단일 출처 상수 — `persons.py`

큐레이션 인물의 시대·이름·정렬 기준 상수는 `backend/app/routes/persons.py`에만 선언된다. 다른 모듈은 **재선언 없이 임포트**해 드리프트를 방지한다:

- `persons.py`: `_ERA`, `_NAME_KO`, `_ERA_ORDER` 하드코딩.
- `journey.py`: `from .persons import _ERA, _NAME_KO` 임포트.
- `places.py`: `from .persons import _ERA, _NAME_KO, _ERA_ORDER` 임포트.

`places.py` 모듈 독스트링이 이 단일 출처 원칙을 "드리프트 방지"로 명시하고 있다.

### 큐레이션 인물 정렬 패턴

`persons.py`의 `_build_list`와 `places.py`의 `_place_to_persons`는 동일한 정렬 규칙을 쓴다:

1. 각 인물의 여정 사건 최소 `sortKey`를 임시 `_anchor` 필드에 담는다.
2. `(_ERA_ORDER.index(era), _anchor, slug)` 3-튜플로 정렬 — 시대 내 시간순, 동시각 slug tie-break.
3. 응답 전 `del p["_anchor"]`로 temp 필드를 제거한다.

`places.py` 주석이 "persons.py `_build_list`와 동일 규칙"임을 명시한다.

### Neo4j 접근

- `backend/app/db.py`의 `get_driver()`가 모듈 전역 lazy 싱글톤. `NEO4J_PASSWORD` 미설정 시 `RuntimeError`로 즉시 중단.
- 쿼리는 항상 `with driver.session() as session:` 컨텍스트 안에서 실행. 파라미터는 `session.run(cypher, id=...)` 키워드로 바인딩(문자열 보간 금지 — 단, `SEARCH_LIMIT` 같은 상수만 f-string으로 박는 경우 있음, `search.py`/`nodes.py`).
- 노드 라벨 분기는 `labels(n)[0]`를 꺼내 `if label == "Person"/"Event"/...` 식으로 처리(`nodes.py`의 `get_node_places`).
- 좌표·수치는 `float(...)` 캐스팅 시 `try/except (TypeError, ValueError): continue`로 깨진 데이터를 건너뛴다(`nodes.py`).
- `main.py` `lifespan`이 기동 시 5개 라벨(`Person`/`Place`/`Event`/`PeopleGroup`/`Book`)에 `theographic_id` 인덱스를 `IF NOT EXISTS`로 생성하고, 실패하면 `logging.exception(...)` 후 인덱스 없이 계속 진행.

### HTTP Cache-Control 규약

| 엔드포인트 유형 | 헤더 | 예시 |
|---|---|---|
| 목록·조회 전반(Neo4j 또는 파일 기반) | `max-age=300` | `/events`, `/persons/curated`, `/person/{id}/journey`, `/place/{id}/curated-persons`, `/event/{id}/verses` |
| `/books-overview`(책 개요 전체) | `no-store` | `books.py` |
| FastAPI 자동 직렬화(응답 헤더 없음) | — | `search.py`, `nodes.py` 대부분 |

### authored 사건 / person_events JSON 형상

큐레이션 인물의 여정 데이터는 `data/person_events/<slug>.json` 파일에 배열로 산다(현재 21개 slug: `abraham`, `david`, `jesus`, `paul`, `peter`, `john_the_apostle` 등). 각 항목 형상:

```json
{
  "id": "authored-paul-damascus-conversion",
  "title": "Paul's conversion on the road to Damascus",
  "nameKo": "다메섹 도상에서 회심한 바울",
  "startDate": "0034",
  "sortKey": 34,
  "yearLabel": "AD 34경",
  "context": "교회를 박해하던 사울이 ... 시력을 회복함 (행 9:1–19).",
  "authored": true,
  "occursAt": ["recR67sC02MfTx4al"],
  "participants": ["recgkzNX07a7kGFYL"],
  "books": [{ "bookId": "recF09FMjRr0gzjQk", "rangeLabel": "9:1–19" }]
}
```

- **authored 사건 id 규칙:** `authored-<person>-<slug>` 형태(`authored-paul-cypress-mission`). `authored: true` 플래그가 함께 붙는다.
- **`participants`:** theographic_id 배열. **첫 원소 `participants[0]`가 그 인물의 id**라는 불변식에 코드가 의존한다 — `persons.py`/`places.py`/`journey.py`가 `events[0]["participants"][0]`로 person_id를 결정하고, slug↔id 역매핑을 만든다.
- **`occursAt`:** Place theographic_id 배열. 여정 정차지는 `occursAt[0]`를 좌표 조회 키로 쓴다(`journey.py`).
- **`books`:** `{bookId, rangeLabel}` 배열 — 근거 성경권과 절 범위(`"9:1–19"`).
- **`sortKey`:** 숫자 시간 정렬 키. 여정·타임라인이 `sorted(events, key=lambda e: e["sortKey"])`로 시간순 배열.
- **`context`:** 한글 서술 + 괄호 안 절 참조(`(행 9:1–19; 행 11:25–26)`) 패턴. 세미콜론으로 다중 참조를 연결.

### 독스트링·주석

- 모듈/엔드포인트 독스트링은 한글로, "무엇을 반환하는가 + 응답 필드 + 결정 근거"를 적는다(예 `journey.py` 모듈 독스트링이 `stops`의 `seq` 부여 규칙을 명세). 설계 선택 이유("단순성 우선", "404 아님 빈 응답")를 주석에 남긴다.
- ADR 참조를 주석에 직접 박기도 한다(`frontend/src/EventVerses.jsx`의 `ADR-0003 프리베이크 본문`).

### 스크립트 멱등성 패턴

`backend/scripts/`의 Neo4j 적재 스크립트는 모두 `MERGE`(노드·관계)를 사용해 재실행 시 중복을 만들지 않는다. `enrich_place_coords.py`는 `authored-place-*` id에만 MERGE 생성, 기존 `rec*` id는 좌표가 없는 경우에만 SET(기존 값 보존). `inject_ko_names.py`는 단순 SET(덮어쓰기). 스크립트는 실행 후 `print(...)` 집계 카운트로 결과를 사람이 확인하는 구조.

---

## 프론트엔드 (React 19 / Vite / JSX)

모든 소스는 단일 평탄 디렉터리 `frontend/src/`에 모여 있다. 하위 디렉터리 분할 없음.

### 함수 컴포넌트 + 인라인 스타일 객체

- 전부 함수 컴포넌트. `export default function Name(props)` 또는 `function Name(){}` + 하단 `export default`(`VerseLangTabs.jsx`). 클래스 컴포넌트·외부 CSS 프레임워크 없음.
- **스타일은 인라인 `style={{ ... }}` 객체가 표준.** CSS 모듈·styled-components 미사용. 전역 CSS는 `frontend/src/index.css`만 최소로 둠. 재사용 스타일은 모듈 상단에 `const boxStyle = {...}` 객체 상수로 추출해 스프레드(`{ ...boxStyle, color: ... }`)로 변형.
- 색·치수는 `frontend/src/theme.js`(`TYPE_COLOR`/`SELECT_HL`)·`frontend/src/constants.js`(`MOBILE_BREAKPOINT`/`SHEET_VH`) 같은 단일 정본 상수에서 가져온다. 컴포넌트 로컬 색은 파일 상단 상수로(`GOLD`/`PERSON_BLUE` — `PersonHub.jsx`).
- 애니메이션이 필요하면 컴포넌트가 인라인 `<style>{keyframes}</style>`를 직접 렌더(`Spinner.jsx`).

### 훅 사용 패턴

- `useState`/`useEffect`/`useRef`/`useCallback`만 사용. 상태 로직이 재사용되면 커스텀 훅으로 분리(`frontend/src/useNodeSelection.js`가 선택 노드·히스토리·뒤로가기·person event-ids를 캡슐화).
- **AbortController로 fetch 취소:** 데이터 fetch effect는 `const ctrl = new AbortController()` → `apiGet(path, { signal: ctrl.signal })` → cleanup `return () => ctrl.abort()` 패턴. `AbortError`는 `if (e?.name !== 'AbortError')`로 무시(`App.jsx`, `EventVerses.jsx`, `PersonHub.jsx`).
- **set-state-in-effect 회피(react-hooks v7 lint):** effect 내 동기 setState를 피하고, async `.then(...)` 콜백 안에서만 setState하거나 `Promise.resolve().then(() => setX(...))`로 다음 틱에 미룬다(`App.jsx` 주석이 이 규칙을 명시).
- **참조 안정화(useCallback):** 콜백 prop을 인라인 화살표로 넘기면 매 렌더 새 참조가 되어 자식 effect가 재실행되는 버그를 막으려고 `useCallback`으로 감싼다. `useNodeSelection.js`의 `selectNode`(`useCallback([])` + `selectedNodeRef`로 최신값 읽기), `App.jsx`의 `handleSidePanelNodeLoaded`. 이유가 주석으로 남아 있다.
- **반응형:** `window.matchMedia(`(max-width: ${MOBILE_BREAKPOINT}px)`)` effect에서 `change` 리스너 등록·해제(`App.jsx`, `PersonHub.jsx`의 `useIsMobile`).

### 공유 API 클라이언트 (`apiGet`)

- 모든 fetch는 `frontend/src/api.js`의 `apiGet(path, { signal })` 단일 헬퍼를 거친다. 컴포넌트에서 `fetch`를 직접 부르지 않는다.
- 베이스 URL은 `import.meta.env.VITE_API_URL || 'http://localhost:8000'`. 프로덕션은 빌드타임 `frontend/.env.production`의 `VITE_API_URL=/api` 주입으로 nginx 프록시(`/api → api:8000`)를 탄다.
- 비-OK 응답이면 `err.status`를 단 `Error`로 reject. `AbortError`는 fetch에서 그대로 전파.

### ko/en 절 본문 언어 패턴 (verseLang)

- 절 본문 한국어/영어 토글 상태는 `App.jsx`의 `const [verseLang, setVerseLang] = useState('ko')`(기본 `ko`)가 정본. `verseLang`/`setVerseLang`을 prop으로 타임라인·SidePanel·`EventVerses`에 내려준다.
- 토글 UI는 `frontend/src/VerseLangTabs.jsx`(한국어|영어 세그먼트, `color` prop로 테마 색 주입). 클릭 시 `e.stopPropagation()`으로 상위 행 선택과 분리.
- 본문 선택은 `(verseLang === 'ko' ? v.textKo : v.textEn) || '원문이 없습니다'` — 응답 절 객체가 `textKo`/`textEn`을 모두 들고 있다(ADR-0003 프리베이크).

### JourneyList 인터랙션 규약

`frontend/src/JourneyList.jsx`는 여정 정차지를 "여정 > 사건 > 구절" 아코디언 트리로 표시한다.

- **행(row) 클릭 = 지도 선택만.** 좌표가 있는 정차지면 `onStopSelect(dedupIdx)`로 지도 활성 정차지를 바꾸고, 열려 있던 구절은 닫는다(`setExpandedId(null)`).
- **📖 칩 = 구절 토글, 단일 오픈.** `expandedId`(eventId 하나) 상태로 한 번에 하나만 펼친다. 칩은 `e.stopPropagation()`으로 행 onClick을 억제.
- **활성 하이라이트·자동 스크롤:** 지도 마커로 선택이 바뀌면 활성 정차지로 `scrollIntoView`. 리스트에서 직접 클릭한 경우는 `suppressScrollRef`로 자동 스크롤을 억제.
- **동일좌표 dedup:** `(lng,lat)` 키로 정차지를 dedup해 배지 seq↔deduped 인덱스를 매핑(`MapView`의 `buildJourneyStopsGeoJSON`과 동일 로직, 주석으로 명시). 동일 좌표가 여러 사건에 걸치면 '첫' 정차지만 스크롤 타깃.

### mapGeo.js 순수 함수 모듈

`frontend/src/mapGeo.js`는 MapLibre·DOM 의존이 없는 순수 변환 함수만 모은다.

- `placesToGeoJSON(places)` — Place 배열 → GeoJSON FeatureCollection. 동일좌표 그룹은 방사 라벨 배치(`ringLabels`), 단독 좌표는 최근접 이웃 반대 방향 라벨.
- `buildJourneyLineGeoJSON(stops)` — 좌표 있는 stops를 시간순 LineString으로. 연속 중복 좌표를 합쳐 0길이 세그먼트를 방지. `coordProgress` 배열을 properties에 포함(MapLibre line-gradient용).
- `journeyStopGroups(stops)` — stops를 장소 단위로 그룹핑. `seqLabel`은 그 장소의 여정 순번 압축 표기(`compactSeqs`).
- `buildJourneyStopsGeoJSON(stops)` — `journeyStopGroups` 결과를 Point FeatureCollection으로.
- `coreBounds(places)` — 원거리 outlier 장소를 fitBounds 범위에서 제외한 core bounds. median 중심 거리 기반 임계(중앙값×3).

### 맵 클러스터 설정

`frontend/src/mapLayers.js`의 `setupMapSources`에서 `places-source` GeoJSON 소스에 클러스터를 설정한다:
- `clusterRadius: 18` — 마커 원이 실제 겹칠 때만 클러스터(마커 지름 ~21~27px 기준).
- `clusterMinPoints: 4` — 동일/근접 좌표 2~3개는 버블 대신 방사 라벨 표시, 4개 이상만 클러스터.

---

## 에러 처리

- **백엔드:** 진짜 운영 실패만 처리한다. `get_node`/`get_node_places`는 노드 부재 시 `raise HTTPException(status_code=404, ...)`. 큐레이션 여정 엔드포인트는 의도적으로 404 대신 빈 응답(`stops=[]`)(`journey.py` 독스트링 명시). `get_driver()`는 비번 미설정 시 `RuntimeError`. JSON 파싱 실패는 빈 dict 폴백(`overlays._load`), `traits` 파싱 실패는 빈 배열 폴백(`nodes.py`). 좌표 캐스팅 실패는 `continue`로 스킵.
- **프론트엔드:** fetch 실패는 컴포넌트별 사용자향 한글 메시지로 표면화 — 로딩 중 `Spinner`, 에러 시 빨강 텍스트(`인물 목록을 불러오지 못했습니다 — {error}`, `PersonHub.jsx`), 빈 결과 시 안내 문구(`표시할 구절이 없습니다`, `EventVerses.jsx`). `AbortError`는 항상 무시.

---

## 정적 검사 / 빌드 게이트

- **ESLint(flat config, `frontend/eslint.config.js`):** `@eslint/js` recommended + `eslint-plugin-react-hooks`(flat recommended) + `eslint-plugin-react-refresh`(vite). `dist` 무시. `npm run lint`(= `eslint .`). 코드 주석이 react-hooks 규칙(set-state-in-effect 등)을 의식해 쓰여 있어 린트 통과가 사실상의 합의 기준.
- **백엔드 린터·포매터 미설정.** `backend/requirements.txt`는 `fastapi`/`neo4j`/`uvicorn` 3개뿐.
- 코드 스타일: JS는 세미콜론 생략·작은따옴표 우세. Python은 4-space, 타입 힌트는 부분적(`dict[str, str]`, `list[dict]` 신문법 사용).
