---
last_mapped_commit: 815433397ff74c133b2de5d1cafe1c8764b5303c
mapped: 2026-07-04
---

# 코딩 컨벤션

**분석일:** 2026-07-04

프론트엔드(React/Vite/JS)와 백엔드(FastAPI/Python)로 나뉜 모노레포. 각각의 관례가 명확히 다르므로 절을 나눠 기술한다. 실측 근거 파일 경로를 함께 표기한다.

---

## 네이밍 규칙

### 파일명

**프론트엔드 (`frontend/src/`):**
- React 컴포넌트: **PascalCase + `.jsx`** — `App.jsx`, `MapView.jsx`, `SidePanel.jsx`, `PersonHub.jsx`, `TimelineView.jsx`, `BibleOverviewView.jsx`, `JourneyList.jsx`, `EventVerses.jsx`, `VerseLangTabs.jsx`, `Spinner.jsx`.
- 비컴포넌트 모듈(순수 로직·훅·상수): **camelCase 또는 소문자 + `.js`** — `api.js`, `constants.js`, `theme.js`, `dates.js`, `mapGeo.js`, `mapLayers.js`, `mapRingController.js`, `useNodeSelection.js`.
- 커스텀 훅 파일은 `use` 접두사 유지 — `useNodeSelection.js`.

**백엔드 (`backend/`):**
- 모든 Python 파일: **snake_case** — `backend/app/db.py`, `backend/app/overlays.py`, `backend/app/routes/nodes.py`.
- 데이터 적재/생성 스크립트: 동사_명사 snake_case — `backend/scripts/load_books.py`, `backend/scripts/generate_book_events.py`, `backend/scripts/inject_ko_names.py`. 접두 동사는 `load_`(Neo4j 적재), `generate_`(데이터 생성), `inject_`(기존 노드에 필드 주입), `enrich_`로 역할을 구분한다.

### 함수·변수

**프론트엔드:**
- 함수·변수: **camelCase** — `handleSelectPerson`, `apiGet`, `journeyStops`, `explorePersonId`.
- 이벤트 핸들러: `handle` 접두사 — `handleNodeLoaded`, `handleBackToHub`, `handleOpenOverview` (`frontend/src/App.jsx`).
- 컴포넌트 prop으로 넘기는 콜백: `on` 접두사 — `onSelectNode`, `onNodeLoaded`, `onStopSelect`, `onClose`.
- 모듈 상수: **UPPER_SNAKE_CASE** — `MOBILE_BREAKPOINT`, `SHEET_VH` (`frontend/src/constants.js`), `TYPE_COLOR`, `TYPE_KO`, `TYPE_ORDER`, `SELECT_HL` (`frontend/src/theme.js`).

**백엔드:**
- 함수·변수: **snake_case** — `get_driver`, `_build_list`, `person_id`, `place_ids` (`backend/app/routes/persons.py`).
- 모듈 상수: **UPPER_SNAKE_CASE** — `MAX_NEIGHBORS_PER_TYPE`, `NODE_NEIGHBOR_LIMIT` (`backend/app/routes/nodes.py`), `SEARCH_LIMIT` (`backend/app/routes/search.py`).
- 모듈 내부 전용(private) 헬퍼·상수: **언더스코어 접두사** — `_ERA`, `_NAME_KO`, `_ERA_ORDER`, `_build_list`, `_resolve`, `_load`, `_fetch_place_coords` (`backend/app/routes/persons.py`, `backend/app/overlays.py`, `backend/app/routes/journey.py`).

### API 응답 필드 (JSON key)

- 프론트로 나가는 신규 계산 필드 JSON key는 **camelCase**로 통일 — `nameKo`, `eventCount`, `placeId`, `placeNameKo` 등 (`backend/app/routes/journey.py`의 `stops` 항목: `seq`, `eventId`, `nameKo`, `sortKey`, `placeId`, `placeNameKo`, `lng`, `lat`).
- Neo4j 원본 속성명(`theographic_id` 등 snake_case)이 그대로 나가는 경우도 있으나, 노드 식별자는 응답에서 `id`로 재매핑한다 (`backend/app/routes/nodes.py:259`).
- 한글 이름 필드는 항상 `nameKo`. 원본(영문/원어) 이름은 `name`. 누락 여부 플래그는 `nameKoMissing` (`backend/app/routes/nodes.py`).

---

## 코드 스타일 (프론트엔드)

**포매팅 — Prettier·별도 포매터 없음.** `frontend/`에 `.prettierrc`가 없다. 스타일은 관례로만 유지되므로 **기존 파일 스타일을 그대로 따를 것.**

관찰된 실제 스타일:
- **세미콜론 미사용.** 모든 `.jsx`/`.js`에서 문장 끝 세미콜론이 없다(`grep -c ';$'` 결과 전 파일 0). 단, 한 줄에 여러 문장을 이어 쓸 때만 인라인 `;`로 구분 (`frontend/src/api.js:9` — `const err = new Error(...); err.status = ...; throw err`).
- **작은따옴표(`'`)** 문자열 기본. import 경로·문자열 모두 작은따옴표.
- **들여쓰기 2칸.**
- **인라인 스타일 객체** 사용 — CSS 파일·CSS-in-JS 라이브러리 없이 `style={{ ... }}` JSX 인라인 스타일로 UI를 구성한다. 전역 스타일만 `frontend/src/index.css`에 둔다. (`frontend/src/App.jsx`의 `renderExploreNav` 참고 — 색·간격을 모두 인라인 리터럴로 지정.)
- 색상은 hex 리터럴을 인라인으로 쓰되, 노드 타입 색은 반드시 `frontend/src/theme.js`의 `TYPE_COLOR` 팔레트를 공유(중복 정의 금지 — 과거 뷰마다 색이 어긋나던 버그를 통일한 이력).

**린트 — ESLint (flat config).** `frontend/eslint.config.js`:
- `@eslint/js` recommended
- `eslint-plugin-react-hooks` (flat.recommended) — **훅 규칙 엄격 적용.**
- `eslint-plugin-react-refresh` (vite)
- `dist`는 글로벌 무시.
- 실행: `cd frontend && npm run lint` (= `eslint .`).

**React 훅 관련 강한 관례 (react-hooks 규칙 준수 목적):**
- **effect 내 동기 setState 금지.** effect 본문에서 곧바로 상태를 초기화하지 않고, `Promise.resolve().then(...)` 또는 비동기 fetch 콜백 안에서만 setState 한다 (`frontend/src/App.jsx:69`, `frontend/src/SidePanel.jsx`의 `state`/`placeVerseView` 파생 패턴). stale 응답 무시는 상태 대신 `forNodeId`/`id` 키를 응답에 실어 파생값으로 걸러낸다.
- **콜백 참조 안정화(`useCallback`).** 컴포넌트에 넘기는 콜백이 매 렌더 새 참조가 되면 자식의 fetch effect가 재실행되어 요청이 abort되는 버그가 반복 발생했음. `selectNode`, `handleNodeLoaded`는 `useCallback`으로 감싸고, 최신값이 필요하면 `useRef`(`selectedNodeRef`)로 읽는다 (`frontend/src/useNodeSelection.js:33`, `frontend/src/App.jsx:101`).

---

## 코드 스타일 (백엔드)

**포매터·린터 설정 파일 없음.** `black`/`ruff`/`flake8` 설정이 저장소에 없다. PEP 8 관례를 따르되 **기존 파일 스타일을 따를 것.**

- **들여쓰기 4칸**, 큰따옴표(`"`) 문자열 기본.
- 타입 힌트를 적극 사용 — `dict[str, str]`, `list[dict]`, `def _resolve(subpath: str) -> "str | None":` (`backend/app/overlays.py`, `backend/app/routes/persons.py`).
- 모듈 최상단 **docstring**으로 파일 목적 설명(한글). 예: `backend/app/routes/persons.py:1`, `backend/app/routes/journey.py:1`.
- 라우트 함수에 한글 docstring으로 엔드포인트 계약(응답 shape) 명시 (`backend/app/routes/journey.py:74`).

---

## import 정리

**프론트엔드 순서 관례** (예: `frontend/src/SidePanel.jsx`, `MapView.jsx`, `TimelineView.jsx`):
1. React / 외부 라이브러리 — `import { useState, useEffect } from 'react'`, `import maplibregl from 'maplibre-gl'`, `import { Map, Clock } from 'lucide-react'`.
2. CSS/에셋 side-effect import — `import 'maplibre-gl/dist/maplibre-gl.css'`.
3. 로컬 공유 모듈 — `import { apiGet } from './api'`, `import { TYPE_COLOR } from './theme'`, `import { MOBILE_BREAKPOINT } from './constants'`.
4. 로컬 컴포넌트 — `import Spinner from './Spinner'`, `import VerseLangTabs from './VerseLangTabs'`.

**경로 별칭(alias) 미사용.** `@/` 등 별칭 설정이 `vite.config.js`에 없다. 모두 상대경로(`./`)로 import 한다.

**백엔드 순서 관례** (예: `backend/app/routes/journey.py`):
1. 표준 라이브러리 — `import json`, `import functools`, `import os`.
2. 서드파티 — `from fastapi import APIRouter`, `from fastapi.responses import JSONResponse`.
3. 로컬 상대 import — `from ..db import get_driver`, `from ..overlays import _resolve`, `from .persons import _ERA, _NAME_KO`.

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

- 프로덕션 base URL은 빌드타임 `VITE_API_URL=/api`(nginx 프록시 `/api → api:8000`)로 주입. 로컬 개발 기본값은 `http://localhost:8000`.
- 비-OK 응답은 `status`를 담은 Error로 throw. 호출부는 `e?.status` 또는 `e?.name === 'AbortError'`로 분기.

**effect 안에서 fetch할 때의 표준 패턴** (요청 취소 + stale 방지):

```js
// 방식 A: AbortController (frontend/src/App.jsx:65)
useEffect(() => {
  const ctrl = new AbortController()
  apiGet(`/person/${explorePersonId}/journey`, { signal: ctrl.signal })
    .then(({ stops }) => { setJourneyStops(stops) })
    .catch((e) => { if (e?.name !== 'AbortError') setJourneyStops([]) })
  return () => ctrl.abort()
}, [explorePersonId])

// 방식 B: cancelled 플래그 (frontend/src/SidePanel.jsx:63)
useEffect(() => {
  if (!nodeId) return
  let cancelled = false
  apiGet('/node/' + nodeId)
    .then(data => { if (!cancelled) setState({ id: nodeId, node: data, error: null }) })
    .catch(e => { if (!cancelled) setState({ id: nodeId, node: null, error: e?.status ?? String(e) }) })
  return () => { cancelled = true }
}, [nodeId, onNodeLoaded])
```

**stale 응답 무시.** 어느 nodeId의 응답인지 `state.id`에 실어두고, 렌더 시 `state.id === nodeId`일 때만 사용 (`frontend/src/SidePanel.jsx:49,55,61`). 이 파생 패턴으로 effect 내 리셋 setState를 피한다.

**유한 재시도(지수 백오프) 패턴.** 실패 시 CTA가 사라지는 것을 자가 회복하기 위해 1s→2s→4s 3회 재시도 후 `console.warn` (`frontend/src/App.jsx:43-56`).

---

## Neo4j 쿼리 패턴 (백엔드)

**드라이버 싱글턴.** `backend/app/db.py`의 `get_driver()`가 모듈 전역 `_driver`를 lazy 초기화해 재사용한다. 라우트마다 `driver = get_driver()` 후 `with driver.session() as session:` 블록에서 쿼리한다.

```python
# backend/app/routes/nodes.py
driver = get_driver()
with driver.session() as session:
    result = session.run(
        "MATCH (n {theographic_id: $id}) RETURN n, labels(n) AS labels",
        id=node_id,
    )
    record = result.single()
    if not record:
        raise HTTPException(status_code=404, detail="Node not found")
```

관례:
- **파라미터 바인딩 필수.** 사용자 입력은 항상 `$id`, `$q`, `$ids` 등 named parameter로 바인딩. Cypher 문자열에 직접 보간(f-string 삽입)하는 것은 **상수 리밋값(`LIMIT {SEARCH_LIMIT}`, `[0..{NODE_NEIGHBOR_LIMIT}]`)에만** 허용 (`backend/app/routes/search.py:27`, `backend/app/routes/nodes.py:169`). 값(입력)은 절대 보간하지 않는다.
- **노드 식별자는 `theographic_id`.** 모든 매칭이 `{theographic_id: $id}`를 키로 쓴다. 앱 시작 시 lifespan에서 label별 인덱스를 생성한다 (`backend/app/main.py:8-21`).
- **레코드 → dict 변환.** 노드는 `props = dict(record["n"])`로 풀고 `props.get("name") or props.get("title", "")` 형태로 안전 접근. `labels(n)`의 첫 원소를 라벨로 쓰되 `labels[0] if labels else "Unknown"` fallback (`backend/app/routes/search.py:38`, `nodes.py:196`).
- **한글 이름 coalesce.** `nameKo`가 없으면 `name`으로 폴백. Cypher 내에서 `coalesce(p.nameKo, p.name, p.title)`, 또는 Python에서 `name_ko if name_ko else name` (`backend/app/routes/journey.py:57`, `nodes.py:263`).
- **배치 조회는 UNWIND.** 여러 place 좌표를 한 번에 가져올 때 `UNWIND $ids AS tid MATCH (p:Place {theographic_id: tid}) ...` (`backend/app/routes/journey.py:50`).
- **왕복 축소.** 이웃과 총개수를 한 쿼리로 합침 — `WITH count(m) AS total, collect({...})[0..LIMIT] AS rows RETURN rows, total` (`backend/app/routes/nodes.py:167-172`).
- **라벨 분기.** 노드 label(Person/Event/PeopleGroup/Book/기타)에 따라 다른 Cypher를 실행하는 if/elif 분기 (`backend/app/routes/nodes.py:34-82`).
- Cypher 관례: 관계 타입·라벨 UPPER, 여러 줄 쿼리는 삼중 따옴표 `"""` 블록으로.

**파일 기반 오버레이 데이터.** Neo4j에 없는 정적 데이터(사건별 근거구절, 큐레이션 인물 여정 등)는 `data/` 하위 JSON에서 읽는다. `backend/app/overlays.py`의 `_resolve(subpath)`가 `DATA_DIR`(기본 `/app/data`) → 저장소 `data/` 순으로 파일을 찾고, `@functools.lru_cache(maxsize=1)`로 1회 로드 캐시한다 (`backend/app/overlays.py:11,30`). 큐레이션 목록·역매핑도 `lru_cache`로 캐시 (`backend/app/routes/persons.py:95`).

---

## FastAPI 라우트 패턴

- **라우터 분리.** 도메인별 `APIRouter`를 `backend/app/routes/*.py`에 두고 `backend/app/main.py`에서 `include_router`로 등록. 신규 엔드포인트는 관련 라우트 파일에 `@router.get(...)`로 추가.
- **GET 전용.** CORS는 `allow_methods=["GET"]`, `allow_origins=["*"]`, `allow_credentials=False` (`backend/app/main.py:25`). 쓰기 API는 없다(데이터 적재는 별도 스크립트).
- **경로 컨벤션.** 리소스 상세는 `/node/{node_id}`, 하위는 `/node/{node_id}/places`·`/person/{node_id}/event-ids`·`/person/{person_id}/journey`. 쿼리 파라미터는 `Query("")` (`backend/app/routes/search.py:9`).
- **캐시 헤더.** 정적·준정적 응답은 `JSONResponse(content=..., headers={"Cache-Control": "max-age=300"})`로 5분 캐시 (`persons.py`, `journey.py`, `events.py`, `places.py`). 자주 바뀌는 목록은 `"no-store"` (`backend/app/routes/books.py:30`).

---

## 에러 처리

**프론트엔드:**
- fetch 실패는 `.catch`로 잡아 **조용히 폴백**하는 것이 기본 — 빈 배열/`null`로 상태를 세팅하고 UI를 비운다 (`setJourneyStops([])`, `setPersonEventIds(null)`).
- AbortError(요청 취소)는 정상 흐름으로 간주해 무시 — `if (e?.name !== 'AbortError')`로 걸러낸 뒤에만 에러 상태 반영 (`frontend/src/App.jsx:74`).
- 회복 가능한 실패는 지수 백오프 재시도 후 `console.warn` (`frontend/src/App.jsx:51`). 사용자에게 에러 토스트를 띄우는 전역 처리기는 없다.

**백엔드:**
- 리소스 없음은 `raise HTTPException(status_code=404, detail="Node not found")` (`backend/app/routes/nodes.py:30,156`).
- 도메인상 "해당 없음"(큐레이션 인물이 아닌 대상의 journey 등)은 404가 아니라 **빈 결과(`stops: []`) 200 응답**으로 다룬다 (`backend/app/routes/journey.py:84`).
- 설정 누락은 기동 시 즉시 실패 — `NEO4J_PASSWORD` 미설정 시 `raise RuntimeError(...)` (`backend/app/db.py:13`).
- 부트스트랩성 실패는 삼켜서 계속 진행 — 인덱스 생성 실패는 `logging.exception(...)` 후 무시 (`backend/app/main.py:19`). JSON 파싱 실패는 빈 dict/list 폴백 (`backend/app/overlays.py:26`, `nodes.py:257`).
- 좌표 파싱은 방어적 — `try/except (TypeError, ValueError)` 후 해당 항목 skip (`backend/app/routes/nodes.py:95-99`).

---

## 로깅

- **백엔드:** 표준 `logging` 모듈. 기동/부트스트랩 예외는 `logging.exception(...)` (`backend/app/main.py:19`). 데이터 스크립트는 `print("[WARN] ...")` / `print` 진행 로그 (`backend/scripts/load_books.py:29`). 로그 메시지는 한글로 작성.
- **프론트엔드:** 프레임워크 없이 `console.warn`만 회복 실패 로깅에 사용 (`frontend/src/App.jsx:51`).
- **배포 스크립트:** `deploy.sh`의 `log()` 헬퍼가 타임스탬프 + `tee`로 로그 파일에 기록 (`deploy.sh:8`).

---

## 주석

- **왜(WHY)를 적는다.** 코드 위에 "무엇을"이 아니라 "왜 이렇게" 했는지 배경·과거 버그 이력을 한글 주석으로 남기는 것이 강한 관례. 예: 콜백 참조 안정화 이유 (`frontend/src/App.jsx:98-100`), effect 동기 setState 회피 이유 (`frontend/src/App.jsx:66-69`), 색 팔레트 통일 배경 (`frontend/src/theme.js:1-3`), startDate 정렬 함정 (`backend/app/routes/nodes.py:236-237`).
- **파일 상단 목적 주석/docstring.** 프론트 모듈은 `// 목적...` 한 줄 주석, 백엔드는 `"""..."""` docstring (`backend/app/routes/persons.py:1`).
- 모든 주석은 **한글**로 작성.
- JSDoc/TSDoc은 사용하지 않음(TypeScript 미사용). 백엔드 라우트 함수는 응답 계약을 docstring으로 기술 (`backend/app/routes/journey.py:74-82`).

---

## 함수·모듈 설계

**프론트엔드:**
- 파일당 1개 컴포넌트 `function`, 파일 하단 `export default App` (`frontend/src/App.jsx:391`).
- 공유 상수/헬퍼는 named export로 모듈에 모은다 — `frontend/src/theme.js`(색·라벨 + `typeColor`/`typeKo` 헬퍼), `frontend/src/constants.js`, `frontend/src/api.js`.
- 컴포넌트 내부 소규모 렌더 헬퍼는 컴포넌트 안에서 함수로 정의 — `renderExploreNav`, `renderOverviewNav` (`frontend/src/App.jsx:141,201`).
- prop 콜백은 기본값을 인라인으로 — `onSelectNode = () => {}` (`frontend/src/SidePanel.jsx:46`).
- 상태 로직 재사용은 커스텀 훅으로 추출 — `useNodeSelection()` (`frontend/src/useNodeSelection.js`). 지도 관련 순수 로직은 훅이 아닌 모듈(`mapGeo.js`, `mapLayers.js`, `mapRingController.js`)로 분리.
- **배럴 파일(`index.js` re-export) 없음.** 각 파일을 직접 import.

**백엔드:**
- 라우트 파일 하나당 `router = APIRouter()` 하나, 엔드포인트 함수들, 그리고 그 파일 전용 헬퍼(`_`접두). 순수/재사용 로직은 `_build_id_to_slug`, `_load_events`처럼 private 함수로 (`backend/app/routes/journey.py`).
- 크로스 모듈 재사용 상수는 한 곳에 두고 import — `_ERA`, `_NAME_KO`는 `persons.py`에 정의하고 `journey.py`가 가져다 씀 (`backend/app/routes/journey.py:13`).
- **프론트-백 동기화 주의.** 시대 순서 등 양쪽에 중복 정의되는 값은 주석으로 상대 파일을 명시 — `frontend/src/PersonHub.jsx`의 시대 순서 주석("persons.py _ERA_ORDER와 동일").

---

*컨벤션 분석: 2026-07-04*
