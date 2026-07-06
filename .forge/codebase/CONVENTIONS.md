---
last_mapped_commit: 95ba754e0a5b8a8db6f537f88d6d4e60d302d066
mapped: 2026-07-06
---

# 코딩 컨벤션

프론트엔드(React/Vite/JS)와 백엔드(FastAPI/Python)로 나뉜 모노레포. 각각의 관례가 다르므로 절을 나눠 기술한다.

---

## 네이밍 규칙

### 파일명

**프론트엔드 (`frontend/src/`):**
- React 컴포넌트: PascalCase + `.jsx` — `App.jsx`, `MapView.jsx`, `SidePanel.jsx`, `PersonHub.jsx`, `TimelineView.jsx`, `BibleOverviewView.jsx`, `JourneyList.jsx`, `EventVerses.jsx`, `VerseLangTabs.jsx`, `Spinner.jsx`
- 비컴포넌트 모듈(순수 로직·훅·상수): camelCase 또는 소문자 + `.js` — `api.js`, `constants.js`, `theme.js`, `dates.js`, `mapGeo.js`, `mapLayers.js`, `mapRingController.js`, `urlState.js`
- 커스텀 훅 파일은 `use` 접두사 유지 — `useNodeSelection.js`, `useStageNavigation.js`

**백엔드 (`backend/`):**
- 모든 Python 파일: snake_case — `backend/app/db.py`, `backend/app/overlays.py`, `backend/app/routes/nodes.py`
- 데이터 적재/생성 스크립트: 동사_명사 snake_case. 접두 동사는 `load_`(Neo4j 적재), `generate_`(데이터 생성), `inject_`(기존 노드에 필드 주입), `enrich_`(좌표·문맥 보강)

### 함수·변수

**프론트엔드:**
- 함수·변수: camelCase — `handleSelectPerson`, `apiGet`, `journeyStops`, `explorePersonId`
- 내부 핸들러: `handle` 접두사 — `handleNodeLoaded`, `handleBackToHub` (`useStageNavigation.js:127`)
- 컴포넌트 prop 콜백: `on` 접두사 — `onSelectNode`, `onNodeLoaded`, `onStopSelect`, `onClose`
- 모듈 상수: UPPER_SNAKE_CASE — `MOBILE_BREAKPOINT`, `SHEET_VH`, `JOURNEY_SHEET_VH` (`frontend/src/constants.js`), `TYPE_COLOR`, `TYPE_KO`, `SELECT_HL` (`frontend/src/theme.js`)

**백엔드:**
- 함수·변수: snake_case — `get_driver`, `_build_list`, `person_id`, `place_ids`
- 모듈 상수: UPPER_SNAKE_CASE — `MAX_NEIGHBORS_PER_TYPE`, `NODE_NEIGHBOR_LIMIT` (`backend/app/routes/nodes.py:6-7`), `SEARCH_LIMIT` (`backend/app/routes/search.py:8`)
- 모듈 내부 전용 헬퍼·상수: 언더스코어 접두사 — `_ERA`, `_NAME_KO`, `_ERA_ORDER`, `_build_list`, `_resolve`, `_load`, `_fetch_place_coords`

### API 응답 필드 (JSON key)

- 신규 계산 필드는 camelCase — `nameKo`, `eventCount`, `placeId`, `placeNameKo`
- 노드 식별자는 응답에서 `id`로 재매핑 (`backend/app/routes/nodes.py:259`)
- 한글 이름 필드는 항상 `nameKo`, 원본 영문은 `name`, 누락 여부는 `nameKoMissing`
- `journey` stops 항목 shape: `{ seq, eventId, title, nameKo, sortKey, placeId, placeNameKo, lng, lat }`

---

## 코드 스타일 (프론트엔드)

**포매팅** — Prettier 없음. 기존 파일 스타일을 그대로 따를 것.

실제 관찰 스타일:
- 세미콜론 미사용. 한 줄에 여러 문장을 이어 쓸 때만 인라인 `;`로 구분 (`frontend/src/api.js:9`)
- 작은따옴표(`'`) 문자열 기본
- 들여쓰기 2칸
- 인라인 스타일 객체 사용 — CSS 파일·CSS-in-JS 없이 `style={{ ... }}` JSX 인라인 스타일로 UI를 구성한다. 전역 스타일만 `frontend/src/index.css`에 둔다
- 노드 타입 색은 반드시 `frontend/src/theme.js`의 `TYPE_COLOR` 팔레트를 공유 — 중복 정의 금지. 과거 뷰마다 색이 어긋나던 버그를 통일한 이력이 있다

**ESLint** — `frontend/eslint.config.js` (flat config):
- `@eslint/js` recommended
- `eslint-plugin-react-hooks` (flat.recommended) — 훅 규칙 엄격 적용
- `eslint-plugin-react-refresh` (vite)
- 실행: `cd frontend && npm run lint`

---

## 코드 스타일 (백엔드)

**포매터·린터 설정 없음.** black/ruff/flake8 설정이 저장소에 없다. PEP 8을 따르되 기존 스타일 유지.

- 들여쓰기 4칸, 큰따옴표 문자열 기본
- 타입 힌트 적극 사용 — `dict[str, str]`, `list[dict]`, `-> "str | None"` (`backend/app/overlays.py:11`, `backend/app/routes/persons.py`)
- 모듈 최상단 docstring으로 파일 목적 설명(한글). 예: `backend/app/routes/persons.py:1`, `backend/app/routes/journey.py:1`
- 라우트 함수에 한글 docstring으로 엔드포인트 계약(응답 shape) 명시 (`backend/app/routes/journey.py:74`)

---

## import 정리

**프론트엔드 순서** (예: `SidePanel.jsx`, `MapView.jsx`, `TimelineView.jsx`):
1. React / 외부 라이브러리 — `import { useState, useEffect } from 'react'`, `import maplibregl from 'maplibre-gl'`
2. CSS/에셋 side-effect import — `import 'maplibre-gl/dist/maplibre-gl.css'`
3. 로컬 공유 모듈 — `import { apiGet } from './api'`, `import { TYPE_COLOR } from './theme'`
4. 로컬 컴포넌트 — `import Spinner from './Spinner'`, `import VerseLangTabs from './VerseLangTabs'`

경로 별칭(alias) 미사용 — `vite.config.js`에 `@/` 설정 없음. 모두 `./` 상대경로.

배럴 파일(`index.js` re-export) 없음 — 각 파일을 직접 import.

**백엔드 순서** (예: `backend/app/routes/journey.py`):
1. 표준 라이브러리 — `import json`, `import functools`, `import os`
2. 서드파티 — `from fastapi import APIRouter`, `from fastapi.responses import JSONResponse`
3. 로컬 상대 import — `from ..db import get_driver`, `from ..overlays import _resolve`, `from .persons import _ERA, _NAME_KO`

---

## API 호출 패턴 (프론트엔드)

**단일 API 클라이언트.** 모든 fetch는 `frontend/src/api.js`의 `apiGet(path, { signal })`을 거친다. 컴포넌트에서 `fetch()`를 직접 부르지 말 것.

```js
// frontend/src/api.js
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'
export async function apiGet(path, { signal } = {}) {
  const res = await fetch(API_BASE + path, { signal })
  if (!res.ok) { const err = new Error(String(res.status)); err.status = res.status; throw err }
  return res.json()
}
```

프로덕션 base URL은 빌드타임 `VITE_API_URL=/api`로 주입. 비-OK 응답은 `status`를 담은 Error로 throw.

**effect 안에서 fetch하는 두 가지 표준 패턴:**

```js
// 방식 A: AbortController (frontend/src/App.jsx:57-70)
useEffect(() => {
  const ctrl = new AbortController()
  apiGet(`/person/${explorePersonId}/journey`, { signal: ctrl.signal })
    .then(({ stops }) => { setJourneyStops(stops); setActiveStopIdx(null) })
    .catch((e) => { if (e?.name !== 'AbortError') setJourneyStops([]) })
  return () => ctrl.abort()
}, [explorePersonId])

// 방식 B: cancelled 플래그 (frontend/src/SidePanel.jsx:67-81)
useEffect(() => {
  if (!nodeId) return
  let cancelled = false
  apiGet('/node/' + nodeId)
    .then(data => { if (!cancelled) setState({ id: nodeId, node: data, error: null }) })
    .catch(e => { if (!cancelled) setState({ id: nodeId, node: null, error: e?.status ?? String(e) }) })
  return () => { cancelled = true }
}, [nodeId, onNodeLoaded])
```

**stale 응답 무시 — `forNodeId`/`id` 키 파생 패턴.** 어느 nodeId의 응답인지를 상태 안에 실어두고, 렌더 시 `state.id === nodeId`일 때만 사용한다. 이 방식으로 effect 내 리셋 setState를 피한다 (`frontend/src/SidePanel.jsx:49`의 `state`, `placeVerseViewRaw`의 `forNodeId` 비교).

```js
// SidePanel.jsx:55 — forNodeId 파생 패턴
const placeVerseView = placeVerseViewRaw?.forNodeId === nodeId ? placeVerseViewRaw : null
```

**AbortController + stale ref 조합 패턴** (`frontend/src/TimelineView.jsx:121-129`):
```js
openEventRef.current = ev.id
apiGet('/event/' + ev.id + '/verses')
  .then(data => { if (openEventRef.current === ev.id) setEventVerses({ id: ev.id, data }) })
  .catch(() => { if (openEventRef.current === ev.id) setEventVerses({ id: ev.id, data: { books: [] } }) })
```

**유한 재시도(지수 백오프)** — 회복 가능한 실패는 1s→2s→4s 3회 재시도 후 console.warn. `PersonHub.jsx:173`, `useStageNavigation.js:44`.

---

## effect 동기 setState 금지 → Promise.resolve().then() 패턴

effect 본문에서 곧바로 상태를 초기화하지 않는다. 초기화가 필요하면 `Promise.resolve().then()`으로 마이크로태스크에 미룬다.

```js
// frontend/src/App.jsx:67 — 인물·투어 미선택 시 초기화
Promise.resolve().then(() => {
  setJourneyStops(null); setActiveStopIdx(null); setReadingEventId(null); setExploreTourName(null)
})
```

딥링크 복원 시에도 동일 패턴 (`useStageNavigation.js:62`):
```js
Promise.resolve().then(() => {
  if (parsed) { setExploreTourId(parsed.tourSlug); setActiveStage('explore') }
  setRestored(true)
})
```

popstate 핸들러에서도 `Promise.resolve().then()`으로 상태 복원:
```js
// useStageNavigation.js:111
Promise.resolve().then(() => {
  if (!s) { setActiveStage('hub'); closePanel(); return }
  setActiveStage(s.stage); setExplorePersonId(s.person ?? null)
})
```

---

## useCallback으로 콜백 참조 안정화

컴포넌트에 넘기는 콜백이 매 렌더 새 참조가 되면 자식의 fetch effect(deps에 해당 콜백 포함)가 재실행된다. 이력: `selectNode`·`handleNodeLoaded`의 참조가 불안정해 MapView `expandPlace` fetch가 abort됐던 버그가 반복 발생했음.

```js
// frontend/src/useNodeSelection.js:33
const selectNode = useCallback((id) => {
  if (id === selectedNodeRef.current) return
  if (selectedNodeRef.current) setHistory(h => [...h, selectedNodeRef.current])
  setSelectedNode(id)
}, [])  // [] — 최신값은 selectedNodeRef로 읽음
```

`useStageNavigation.js`의 `onNodeLoaded`도 `useCallback`으로 감싸며, `explorePersonId` 변경 시에만 갱신한다 (`useStageNavigation.js:184`).

---

## 커스텀 훅 — `useNodeSelection`, `useStageNavigation`

**`useNodeSelection.js`** — 노드 선택 원시값 상태 머신.
- 반환: `selectedNode`, `selectedNodeMeta`, `history`, `personEventIds`, `handleNodeLoaded`, `selectNode`, `selectNodeFresh`, `goBack`, `closePanel`
- `selectNode`: 직전 노드를 `history`에 쌓아 패널 뒤로가기 지원. `useCallback([])`로 참조 안정화.
- `selectNodeFresh`: 히스토리 리셋 후 선택 — 새 탐색 컨텍스트 진입 시 사용.
- `handleNodeLoaded`: `useCallback([])`로 안정화. Person 선택 시 `/person/{id}/event-ids`를 추가 fetch해 `personEventIds`를 `Set`으로 채운다.

**`useStageNavigation.js`** — 화면 단계·URL·브라우저 히스토리 상태 머신(ADR-0009 딥링크·ADR-0010 뒤로가기 통합).
- `selectedNode`/`selectNodeFresh`/`closePanel`/`handleNodeLoaded`를 `useNodeSelection`에서 주입받는다.
- 단계: `'hub'` | `'explore'` | `'overview'` | `'tours'`
- `activeStage`, `explorePersonId`, `exploreTourId`는 상호 연결 — 투어와 인물은 상호배타(`setExploreTourId(null)` / `setExplorePersonId(null)`를 함께 호출).
- `sheetOpen` 파생: `selectedNode != null && selectedNode !== explorePersonId` — 모바일 시트 표시 조건과 history push 판단의 단일 출처.
- 히스토리 동기화 effect: `restored` 상태가 true일 때만 write. `isForward` 조건(stage·person·tour·sheetOpen 변경)이면 pushState, 그 외에는 replaceState.
- `popstateGuard.current`: popstate 복원 중 재-push 방지용 ref.
- 이 파일은 `lucide-react`의 `Map`을 import하지 않는다 — 전역 `Map`/`history` 섀도잉 함정이 구조적으로 없다(과거 런타임 크래시 원인).

---

## TimelineView `personFilter` prop 계약

`TimelineView`에 전달하는 `personFilter`는 **`Set`** 이어야 한다. 내부에서 `activePersonFilter.has(ev.id)`로 사용한다 (`frontend/src/TimelineView.jsx:101`).

```js
// frontend/src/App.jsx:46-49
const tourEventIds = useMemo(
  () => (exploreTourId && journeyStops ? new Set(journeyStops.map(s => s.eventId)) : null),
  [exploreTourId, journeyStops],
)
// 사용
<TimelineView personFilter={explorePersonId != null ? personEventIds : tourEventIds} ... />
```

`personEventIds`는 `useNodeSelection`의 `handleNodeLoaded` 내부에서 Set으로 채워진다. `null`이면 필터 없음, `Set`이면 `.has(ev.id)` 사용.

---

## 해시 URL 상태 인코딩 (`urlState.js`)

라우팅 라이브러리 없이 순수 문자열 매핑으로 구현한다 (`frontend/src/urlState.js`).

| stage | hash |
|---|---|
| hub | `#/` |
| overview | `#/books` |
| tours | `#/tours` |
| explore(인물, 지도) | `#/person/<slug>` |
| explore(인물, 타임라인) | `#/person/<slug>/timeline` |
| explore(투어, 지도) | `#/tour/<slug>` |
| explore(투어, 타임라인) | `#/tour/<slug>/timeline` |

`encodeHash`로 직렬화, `parseHash`로 역직렬화. 알 수 없는 형태는 `null`을 반환해 호출부가 허브로 fallback.

---

## 모바일 반응형

분기점: `MOBILE_BREAKPOINT = 768px` (`frontend/src/constants.js:1`).

모바일에서:
- SidePanel: 하단 시트(`height: ${SHEET_VH}vh = 75vh`, `translateY(100%)` → `translateY(0)`)
- 여정 JourneyList: 지도 위 하단 고정 시트(`height: ${JOURNEY_SHEET_VH}dvh = 42dvh`). 읽기 모드에서 90dvh로 확장.
- `JOURNEY_SHEET_VH`는 App 시트 높이와 MapView의 정차지 카메라 offset의 단일 출처 — 어긋나면 시트 위 중앙정렬이 깨진다 (`frontend/src/constants.js:3`).
- 모바일 정차지 카메라: `map.easeTo({ center, offset: [0, -height/2], duration: 400 })` (`MapView.jsx:205`).
- 뒤로가기: 시트에서 아래로 80px 이상 pull-down 시 `window.history.back()` 위임 (`App.jsx:89`).

---

## Neo4j 쿼리 패턴 (백엔드)

**드라이버 싱글턴.** `backend/app/db.py`의 `get_driver()`가 모듈 전역 `_driver`를 lazy 초기화. 라우트마다 `driver = get_driver()` 후 `with driver.session() as session:` 블록.

**파라미터 바인딩 필수.** 사용자 입력은 항상 named parameter(`$id`, `$q`, `$ids`)로 바인딩. Cypher 문자열 직접 보간은 상수 리밋값(`LIMIT {SEARCH_LIMIT}`, `[0..{NODE_NEIGHBOR_LIMIT}]`)에만 허용 — 값은 절대 보간하지 않는다 (`backend/app/routes/nodes.py:169`).

**노드 식별자는 `theographic_id`.** 모든 매칭이 `{theographic_id: $id}`. 앱 시작 시 lifespan에서 label별 인덱스를 생성한다 (`backend/app/main.py:8-21`).

**레코드 → dict 변환.** `props = dict(record["n"])`으로 풀고 `props.get("name") or props.get("title", "")` 형태로 접근. `labels(n)` 첫 원소를 라벨로 쓰되 `labels[0] if labels else "Unknown"` fallback.

**한글 이름 coalesce.** Cypher 내 `coalesce(p.nameKo, p.name, p.title)` 또는 Python에서 `name_ko if name_ko else name` (`backend/app/routes/journey.py:57`).

**배치 조회는 UNWIND.** 여러 place 좌표 조회: `UNWIND $ids AS tid MATCH (p:Place {theographic_id: tid}) ...` (`backend/app/routes/journey.py:50`).

**왕복 축소.** 이웃과 총개수를 한 쿼리로: `WITH count(m) AS total, collect({...})[0..LIMIT] AS rows RETURN rows, total` (`backend/app/routes/nodes.py:167-172`).

**라벨 분기.** Person/Event/PeopleGroup/Book/기타에 따라 다른 Cypher를 if/elif로 실행 (`backend/app/routes/nodes.py:34-82`).

Cypher 관례: 관계 타입·라벨 UPPER, 여러 줄 쿼리는 삼중 따옴표 `"""` 블록.

---

## `_resolve` 데이터 경로 패턴 + `lru_cache` 오버레이

`backend/app/overlays.py`의 `_resolve(subpath)`는 `DATA_DIR`(기본 `/app/data`) → 저장소 `data/` 순으로 파일을 탐색한다.

```python
# backend/app/overlays.py:11
def _resolve(subpath: str) -> "str | None":
    for base in (os.environ.get("DATA_DIR", "/app/data"), _REPO_DATA_DIR):
        path = os.path.join(base, subpath)
        if os.path.isfile(path):
            return path
    return None
```

파일 기반 정적 데이터(사건별 근거구절, 큐레이션 인물 여정 등)는 이 패턴으로 로드하고, `@functools.lru_cache(maxsize=1)`로 1회 캐시한다. `maxsize=None`은 키마다 캐시(예: `_place_to_persons(place_id)`, `_build_connections(node_id)`). `maxsize=1`은 전체 목록의 단발 캐시(예: `book_events_raw()`, `_compute_events()`).

`tours.py`의 `_tours_dir()`도 동일한 우선순위로 디렉터리를 찾는다 (`backend/app/routes/tours.py:22`).

---

## FastAPI 라우트 패턴

- 라우터 분리: 도메인별 `APIRouter`를 `backend/app/routes/*.py`에 두고 `main.py`에서 `include_router`로 등록
- GET 전용: `allow_methods=["GET"]`, `allow_origins=["*"]`, `allow_credentials=False` (`main.py:25`)
- 경로 관례: 리소스 상세 `/node/{node_id}`, 하위 `/node/{node_id}/places`·`/person/{node_id}/event-ids`·`/person/{person_id}/journey`
- 쿼리 파라미터: `Query("")` 또는 `Query(default=None, description="...")`
- 캐시 헤더: 정적·준정적 응답은 `JSONResponse(content=..., headers={"Cache-Control": "max-age=300"})`. 자주 바뀌는 목록은 `"no-store"` (`backend/app/routes/books.py:30`)
- "해당 없음" 응답은 404 아닌 빈 결과 200 — 큐레이션 비대상 journey는 `stops: []` 반환 (`backend/app/routes/journey.py:84`)

---

## 에러 처리

**프론트엔드:**
- fetch 실패는 `.catch`로 잡아 빈 배열/`null`로 폴백하고 UI를 비운다 — 전역 에러 토스트 처리기 없음
- AbortError는 정상 흐름 — `if (e?.name !== 'AbortError')`로 걸러낸 뒤에만 에러 상태 반영
- 회복 가능한 실패는 지수 백오프 재시도 후 `console.warn` (`App.jsx:51`)

**백엔드:**
- 리소스 없음: `raise HTTPException(status_code=404, detail="Node not found")`
- 설정 누락: 기동 시 즉시 실패 — `NEO4J_PASSWORD` 미설정 시 `raise RuntimeError(...)` (`db.py:13`)
- 부트스트랩 실패는 삼켜서 계속 — 인덱스 생성 실패는 `logging.exception(...)` 후 무시 (`main.py:19`)
- JSON 파싱 실패: 빈 dict/list 폴백 (`overlays.py:26`, `nodes.py:257`)
- 좌표 파싱: 방어적 `try/except (TypeError, ValueError)` 후 해당 항목 skip (`nodes.py:95-99`)

---

## 한국어 UI 문자열

모든 사용자 대면 텍스트는 한국어다. 대표 문자열:

- SidePanel: `지도에서 마커를 클릭하세요`, `불러오지 못했습니다`, `← 뒤로`, `이웃 {n}개 중 {m}개 표시`, `이 곳을 지난 인물`, `함께 등장한 인물`, `동시대 인물`, `인물 성품`, `여정 탐험 — 지도에서 보기`
- PersonHub: `성경 인물 탐험`, `성경 책 둘러보기`, `테마 투어`, `사건 {n}`
- 에러/피드백: `사건을 불러오지 못했습니다`, `이 항목은 지도에 표시할 위치 정보가 없습니다 — 그래프·타임라인에서 살펴보세요`, `표시할 구절이 없습니다`, `원문이 없습니다`
- 탐험 내비: `다른 인물`, `테마 목록`, `지도`, `타임라인`, `인물 허브`, `성경 책 둘러보기`
- JourneyList: `{personName}의 여정`, `사건 {n}개 · 📖 눌러 구절 보기`, `▾ 여정으로`
- `REL_KO` 관계 번역 (`SidePanel.jsx:8-17`): PARENT_OF → 부모, PARTNER_OF → 배우자, MEMBER_OF → 소속 등
- `TYPE_KO` (`theme.js:13-15`): Person → 인물, Place → 장소, Event → 사건, PeopleGroup → 집단, Book → 성경책
- 날짜 포맷 (`dates.js`): BC 연도는 `BC {n}`, AD는 `AD {n}`. `parseYear(startDate)` 헬퍼가 혼재 형식(`-4003`, `0049-10-01`, `30`)을 파싱 — 사전순 정렬은 BC 연도가 역전되므로 이 헬퍼를 반드시 거쳐야 한다

---

## 주석

- **왜(WHY)를 적는다.** 코드 위에 배경·과거 버그 이력을 한글 주석으로 남기는 것이 강한 관례. 예: `useStageNavigation.js:7`(Map/history 섀도잉 함정), `App.jsx:66`(effect 동기 setState 금지), `theme.js:1-3`(색 팔레트 통일 배경), `nodes.py:236`(startDate 정렬 함정)
- 파일 상단 목적 주석/docstring: 프론트 모듈은 `// 목적...` 한 줄, 백엔드는 `"""..."""` docstring
- 모든 주석은 한글로 작성
- JSDoc/TSDoc 미사용(TypeScript 미사용)
