---
last_mapped_commit: ecdb7cb2ea1bf665b0690e62b4cf51261761072c
mapped: 2026-06-15
---

# Coding Conventions

## 네이밍 패턴

**파일:**
- React 컴포넌트: PascalCase (`MapView.jsx`, `SidePanel.jsx`, `TimelineView.jsx`)
- 유틸리티/모듈: camelCase (`api.js`, `theme.js`, `convexHull.js`)
- CSS: 전역 파일 2개만 존재 (`App.css`, `index.css`). 컴포넌트 범위 CSS 없음.

**React 컴포넌트:**
- 컴포넌트명: PascalCase (`function MapView`, `function SidePanel`, `function SectionHeader`)
- 모든 뷰 컴포넌트는 `default export` 단일 함수
- 내부 서브컴포넌트(파일 내 로컬)는 같은 파일 상단에 선언 (`SectionHeader` in `SidePanel.jsx`)

**변수 및 함수:**
- camelCase 일관 사용 (`selectNode`, `handleTabClick`, `onSearchInput`, `collapseRing`)
- 이벤트 핸들러: `handle` 접두사 또는 `on` 접두사 중 하나 (`handleTabClick`, `onSelectNode`)
- 상수(모듈 수준 고정값): SCREAMING_SNAKE_CASE (`MOBILE_QUERY`, `SHEET_VH`, `NAV_H`, `SEARCH_LIMIT`, `MAX_NEIGHBORS_PER_TYPE`, `NODE_NEIGHBOR_LIMIT`)
- boolean 상태 변수: `is` / `show` / `can` 접두사 (`isMobile`, `showDropdown`, `canGoBack`, `mapLoaded`, `filterDismissed`)

**Props:**
- 콜백 prop: `on` 접두사 (`onSelectNode`, `onBack`, `onNodeLoaded`, `onToggle`)
- boolean prop: `can` 접두사 (`canGoBack`)

**Python (백엔드):**
- 함수명: snake_case (`get_driver`, `get_node`, `get_node_places`, `inject`, `load_json`)
- 상수: SCREAMING_SNAKE_CASE (`MAX_NEIGHBORS_PER_TYPE`, `NODE_NEIGHBOR_LIMIT`, `SEARCH_LIMIT`)
- 모듈 수준 singleton: 언더스코어 접두사 (`_driver`)

## 공유 팔레트 모듈

노드 타입별 색·한글 라벨은 `frontend/src/theme.js` 단일 파일에 집중.
모든 뷰(`App.jsx`, `SidePanel.jsx`, `TimelineView.jsx`, `MapView.jsx`)는 여기서 import한다.

```js
// frontend/src/theme.js
export const TYPE_COLOR = {
  Person: '#7c9cfc', Place: '#4a90d9', Event: '#f5a623',
  PeopleGroup: '#2bb6a8', Book: '#a78bfa', Unknown: '#9aa5b8',
}
export const TYPE_ORDER = ['Person', 'Place', 'Event', 'PeopleGroup', 'Book']
export const typeColor = (label) => TYPE_COLOR[label] || TYPE_COLOR.Unknown
export const typeKo = (label) => TYPE_KO[label] || label
export const SELECT_HL = 'rgba(124,156,252,0.18)'
```

**규칙:** 타입 색을 컴포넌트 파일 안에 중복 정의하지 않는다. 반드시 `theme.js`에서 import.
- `SidePanel.jsx`는 `TYPE_COLOR`, `TYPE_KO` import
- `App.jsx`는 `TYPE_ORDER`, `typeColor`, `typeKo`, `SELECT_HL` import
- `TimelineView.jsx`는 `SELECT_HL` import

## API 클라이언트

공유 API 헬퍼는 `frontend/src/api.js`에 정의되어 있으나, 일부 컴포넌트(`MapView.jsx`, `SidePanel.jsx`, `TimelineView.jsx`)는 아직 직접 `fetch`를 사용하고 있다. `api.js`의 `apiGet`은 `App.jsx`의 검색 fetch에서 사용 중이지 않고, 파일만 존재하는 상태다(사실상 미사용).

```js
// frontend/src/api.js
export const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'
export async function apiGet(path, { signal } = {}) {
  const res = await fetch(API_BASE + path, { signal })
  if (!res.ok) throw res.status
  return res.json()
}
```

각 컴포넌트는 `const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'`을 파일 상단에 선언해 직접 사용한다.
- 비-OK 응답: `Promise.reject(r.status)` (숫자 throw) 패턴
- AbortError: 호출부에서 `e?.name === 'AbortError'` 또는 `e.name === 'AbortError'`로 구분

## Import 순서

```js
// 1. React hooks
import { useState, useEffect, useRef } from 'react'
// 2. 외부 라이브러리
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
// 3. 내부 공유 모듈 (theme, api, 유틸)
import { TYPE_COLOR, TYPE_ORDER } from './theme'
import { convexHull } from './convexHull'
// 4. 내부 컴포넌트
import MapView from './MapView'
```

## 스타일 패턴

**인라인 스타일 우선:** 컴포넌트 JSX에 `style={{ }}` 인라인 객체를 직접 사용한다. CSS 클래스는 사용하지 않는다(단, `index.css`의 전역 reset/변수 제외).

**다크 배경 팔레트:**
- 네비게이션 배경: `#1a1a2e`
- 드롭다운 배경: `#1e2040`
- 텍스트(어두운 배경): `white`, `rgba(255,255,255,0.5~0.7)`
- 보조 텍스트: `#7c8db0`, `#aab2c5`

**화이트 패널 팔레트(SidePanel):**
- 배경: `white`, `#f8faff`(traits 섹션), `#f5f3ff`(Book keyVerse)
- 보조 텍스트: `#7c8db0`, `#5a6481`, `#9aa5b8`
- 구분선: `#eef0f5`

**반응형:** `MOBILE_QUERY = '(max-width: 768px)'`를 `window.matchMedia`로 감지. `App.jsx`에서 `isMobile` state를 관리. 하위 컴포넌트는 `window.innerWidth <= 768`을 직접 확인한다(`MapView.jsx`).

## React 훅 규칙

**setState 위치:** `react-hooks` ESLint 플러그인 v7 기준 준수. effect 동기 본문에서 setState 금지. `setTimeout`/async 콜백 안에서만 호출.

```js
// App.jsx — 검색 debounce 패턴
useEffect(() => {
  const ctrl = new AbortController()
  const timer = setTimeout(async () => {
    setSearchLoading(true)
    try {
      const data = await fetch(...)
      setSearchResults(data)     // async 콜백 내부 — OK
    } catch (e) { ... }
  }, 250)
  return () => { clearTimeout(timer); ctrl.abort() }
}, [searchQuery])
```

**`useCallback` 안정화:** 부모→자식 전달 콜백이 자식 `useEffect` 의존성이 되는 경우 `useCallback(fn, [])` + `useRef`로 최신값 참조.

```js
// App.jsx — selectNode 안정 참조 패턴
const selectedNodeRef = useRef(null)
useEffect(() => { selectedNodeRef.current = selectedNode }, [selectedNode])
const selectNode = useCallback((id) => {
  if (id === selectedNodeRef.current) return
  ...
}, [])
```

**경쟁 조건(race condition) 방지:**
- fetch effect: `AbortController` + `cancelled` 플래그 병용 (`SidePanel.jsx`)
- stale 응답 무시: `state.id === nodeId` 비교로 판단 (`ready = state.id === nodeId`)

```js
// SidePanel.jsx 패턴
useEffect(() => {
  let cancelled = false
  fetch(API_URL + '/node/' + nodeId)
    .then(r => r.ok ? r.json() : Promise.reject(r.status))
    .then(data => { if (!cancelled) setState({ id: nodeId, node: data, error: null }) })
    .catch(e => { if (!cancelled) setState({ id: nodeId, node: null, error: String(e) }) })
  return () => { cancelled = true }
}, [nodeId])
```

**`useRef`의 비-DOM 용도:**
- 애니메이션 프레임 핸들 (`animFrame`, `expandAbortCtrl`)
- 맵 인스턴스 (`mapRef`)
- 팝업 인스턴스 (`popupRef`)
- 클로저 공유 함수 참조 (`expandPlaceRef`, `expandedPlaceRef`)

## 섹션 접기/펼치기 패턴 (SidePanel)

`collapsed` state는 `{ [sectionKey]: false | undefined }` 형태. `undefined`(미설정) = 접힘, `false` = 펼침.

```js
// SidePanel.jsx
const [collapsed, setCollapsed] = useState({})
function toggle(key) {
  setCollapsed(prev => ({ ...prev, [key]: prev[key] === false }))
  // false → undefined(접힘), undefined → false(펼침)
}
const isOpen = collapsed[sectionKey] === false
```

`SectionHeader` 컴포넌트가 toggle 버튼 역할을 담당하며, 실제 콘텐츠는 `{collapsed[key] === false && (...)}` 조건으로 렌더링.

## 오류 처리

**프론트엔드 — fetch 실패:**
- `error` boolean state (`const [error, setError] = useState(false)`)
- 에러 UI는 인라인 스타일 div/p로 직접 표시, 별도 컴포넌트 없음
- AbortError는 무시 (`if (e?.name !== 'AbortError') setError(true)`)
- 빈 결과 안내: 별도 `noLocation` boolean state 사용 (`MapView.jsx`)

**백엔드 — FastAPI:**
- 노드 없음: `raise HTTPException(status_code=404, detail="Node not found")`
- Neo4j 연결 실패: `RuntimeError`로 즉시 실패 (`db.py`)
- 인덱스 생성 실패: `logging.exception(...)` 후 계속 진행 (startup에서 비치명적 처리)
- 라우트 함수는 try/except 없이 작성 — Neo4j 세션 오류는 FastAPI 500으로 자동 전달
- Person `traits` 파싱: `try/except` 후 빈 리스트 폴백 (`nodes.py` 내 inline import json)

## 코멘트 패턴

**왜(why) 위주 설명:** 코드가 이 방식인 이유, 다른 선택지가 있을 때 선택 근거를 인라인 주석으로 기록.

```js
// moveend는 카메라가 안 움직이면 미발화하므로 폴백 타이머(700ms)로 보장, fired로 단발.
// (공유 source 동시 setData 충돌 회피 — radial-ring 회고)
```

**한국어 주석:** 프론트엔드·백엔드 모두 한국어 주석 사용.

**파일 상단 목적 설명:** JSDoc/TSDoc 없음. 1~3줄 한국어 설명만 사용.

```js
// 공유 API 클라이언트 — 모든 프론트 fetch의 단일 베이스 URL + GET 헬퍼.
```

## 유틸리티 모듈

**`frontend/src/convexHull.js`:** Graham scan 알고리즘으로 `{lng, lat}` 좌표 배열을 받아 볼록 껍질 반환. `MapView.jsx`에서 Person 타입 선택 시 hull polygon 렌더에 사용. 순수 함수, 외부 의존성 없음.

## 백엔드 패턴

**라우터 분리:** 기능별로 `backend/app/routes/` 하위 별도 파일 (`nodes.py`, `events.py`, `search.py`).

**DB 접근:** 모든 라우트는 `get_driver()`를 통해 driver를 얻고, `with driver.session() as session:` 블록 안에서 Cypher 실행. ORM 사용 없음.

**응답 형태:** `dict` 리스트를 직접 return(FastAPI 자동 JSON 직렬화). 예외: `events.py`는 `Cache-Control: no-store` 헤더를 위해 `JSONResponse`로 명시적으로 감쌈.

**Cypher 파라미터:** 상수(LIMIT 수치)는 f-string 삽입, 유저 입력은 반드시 `$param` 바인딩.

**CORS:** `allow_origins=["*"]`, `allow_methods=["GET"]` — 읽기 전용 API.

**traits JSON 직렬화:** `Person.traits`는 Neo4j 속성에 JSON 문자열로 저장. 백엔드에서 응답 시 `json.loads()`로 역직렬화 (`nodes.py`).

## ESLint 설정 (`frontend/eslint.config.js`)

- `@eslint/js` recommended
- `eslint-plugin-react-hooks` recommended (v7)
- `eslint-plugin-react-refresh` vite preset
- 대상: `**/*.{js,jsx}`
- 무시: `dist/`
- prettier/biome 미사용 — 포맷터 없음
