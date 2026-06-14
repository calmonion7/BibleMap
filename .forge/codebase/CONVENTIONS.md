---
last_mapped_commit: fb78d740df63d386e84ceb1bb4249921a5e198b7
mapped: 2026-06-14
---

# Coding Conventions

**Analysis Date:** 2026-06-14

## Naming Patterns

**Files:**
- React 컴포넌트: PascalCase (e.g., `MapView.jsx`, `SidePanel.jsx`, `GraphView.jsx`)
- 유틸리티/모듈: camelCase (e.g., `api.js`, `theme.js`)
- CSS: 컴포넌트 범위 없음 — `App.css`, `index.css` 전역 파일 2개만 존재

**React 컴포넌트:**
- 컴포넌트명: PascalCase (`function MapView`, `function SidePanel`)
- 모든 뷰 컴포넌트는 `default export` 단일 함수

**변수 및 함수:**
- camelCase 일관 사용 (`selectNode`, `handleTabClick`, `onSearchInput`)
- 이벤트 핸들러는 `handle` 접두사 또는 `on` 접두사 중 하나 (`handleTabClick`, `onSelectNode`)
- 상수(모듈 수준 고정값): SCREAMING_SNAKE_CASE (`MOBILE_QUERY`, `SHEET_VH`, `NAV_H`, `SEARCH_LIMIT`, `MAX_NEIGHBORS_PER_TYPE`)
- boolean 상태 변수: `is` / `show` / `can` 접두사 (`isMobile`, `showDropdown`, `canGoBack`)

**Props:**
- 콜백 prop: `on` 접두사 (`onSelectNode`, `onBack`)
- boolean prop: `can` 접두사 (`canGoBack`)

**Python (백엔드):**
- 함수명: snake_case (`get_driver`, `get_node`, `get_node_places`)
- 상수: SCREAMING_SNAKE_CASE (`MAX_NEIGHBORS_PER_TYPE`, `NODE_NEIGHBOR_LIMIT`, `SEARCH_LIMIT`)
- 모듈 수준 singleton: 언더스코어 접두사 (`_driver`)

## 공유 팔레트 모듈

노드 타입별 색·한글 라벨은 `frontend/src/theme.js` 단일 파일에 집중.
모든 뷰(`App.jsx`, `SidePanel.jsx`, `GraphView.jsx`, `TimelineView.jsx`, `MapView.jsx`)는 여기서 import한다.

```js
// frontend/src/theme.js
export const TYPE_COLOR = { Person: '#7c9cfc', Place: '#4a90d9', Event: '#f5a623', PeopleGroup: '#2bb6a8', Unknown: '#9aa5b8' }
export const TYPE_ORDER = ['Person', 'Place', 'Event', 'PeopleGroup']
export const typeColor = (label) => TYPE_COLOR[label] || TYPE_COLOR.Unknown
export const typeKo = (label) => TYPE_KO[label] || label
export const SELECT_HL = 'rgba(124,156,252,0.18)'
```

**규칙:** 타입 색을 컴포넌트 파일 안에 중복 정의하지 않는다. 반드시 `theme.js`에서 import.

## API 클라이언트

모든 프론트엔드 fetch는 `frontend/src/api.js`의 `apiGet`을 통해 한다.

```js
// frontend/src/api.js
export const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'
export async function apiGet(path, { signal } = {}) {
  const res = await fetch(API_BASE + path, { signal })
  if (!res.ok) throw res.status
  return res.json()
}
```

- 비-OK 응답: `res.status`(숫자)를 throw
- AbortError: fetch에서 그대로 전파 — 호출부에서 `e.name === 'AbortError'`로 구분
- 직접 `fetch`를 쓰지 않는다

## Import 순서

```js
// 1. React hooks
import { useState, useEffect, useRef } from 'react'
// 2. 외부 라이브러리
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
// 3. 내부 공유 모듈 (theme, api)
import { TYPE_COLOR, TYPE_ORDER } from './theme'
import { apiGet } from './api'
// 4. 내부 컴포넌트
import MapView from './MapView'
```

## 스타일 패턴

**인라인 스타일 우선:** 컴포넌트 JSX에 `style={{ }}` 인라인 객체를 직접 사용한다. CSS 클래스는 사용하지 않는다(단, `index.css`의 전역 reset/변수 제외).

**다크 배경 팔레트:**
- 네비게이션 배경: `#1a1a2e`
- 드롭다운 배경: `#1e2040`
- 텍스트(어두운 배경): `white`, `rgba(255,255,255,0.5~0.7)`
- 보조 텍스트: `#7c8db0`

**반응형:** `MOBILE_QUERY = '(max-width: 768px)'`를 `window.matchMedia`로 감지. `App.jsx`에서 `isMobile` state를 관리해 하위 컴포넌트에 전달하지 않고, 각 컴포넌트가 필요 시 `window.innerWidth <= 768`을 직접 확인.

## React 훅 규칙

**setState 위치:** `react-hooks` ESLint 플러그인 v7 기준 준수. effect 동기 본문에서 setState 금지. `setTimeout`/async 콜백 안에서만 호출.

```js
// App.jsx — 검색 debounce 패턴
useEffect(() => {
  const ctrl = new AbortController()
  const timer = setTimeout(async () => {
    setSearchLoading(true)
    try {
      const data = await apiGet(...)
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

**경쟁 조건(race condition) 방지:** 비동기 fetch effect는 `AbortController` + `cancelled` 플래그를 병용한다.

```js
// SidePanel.jsx 패턴
useEffect(() => {
  let cancelled = false
  apiGet('/node/' + nodeId)
    .then(data => { if (!cancelled) setState(...) })
    .catch(e => { if (!cancelled) setState(...) })
  return () => { cancelled = true }
}, [nodeId])
```

**`useRef`의 비-DOM 용도:** 애니메이션 프레임 핸들, 맵 인스턴스, 팝업 인스턴스 등 React state 밖의 가변값 저장.

## 오류 처리

**프론트엔드 — fetch 실패:**
- `error` boolean state로 관리 (`const [error, setError] = useState(false)`)
- 에러 UI는 인라인 스타일 div/p로 표시, 별도 컴포넌트 없음
- AbortError는 무시 (`if (e?.name !== 'AbortError') setError(true)`)
- 로딩 UI: `ready = state.id === nodeId` 패턴으로 stale 응답 무시 (`SidePanel.jsx`)

**백엔드 — FastAPI:**
- 노드 없음: `raise HTTPException(status_code=404, detail="Node not found")`
- Neo4j 연결 실패: `RuntimeError`로 즉시 실패 (`db.py`)
- 인덱스 생성 실패: `logging.exception(...)` 후 계속 진행 (startup에서 비치명적 처리)
- 라우트 함수는 try/except 없이 작성 — Neo4j 세션 오류는 FastAPI 500으로 자동 전달

## 코멘트 패턴

**왜(why) 위주 설명:** 코드가 이 방식인 이유, 다른 선택지가 있을 때 선택 근거를 인라인 주석으로 기록.

```js
// moveend는 카메라가 안 움직이면 미발화하므로 폴백 타이머(700ms)로 보장, fired로 단발.
// (공유 source 동시 setData 충돌 회피 — radial-ring 회고)
```

**한국어 주석:** 프론트엔드·백엔드 모두 한국어 주석 사용.

**JSDoc/TSDoc:** 사용하지 않음. 파일 상단에 1~3줄 목적 설명만 사용.

```js
// 공유 API 클라이언트 — 모든 프론트 fetch의 단일 베이스 URL + GET 헬퍼.
```

## 백엔드 패턴

**라우터 분리:** 기능별로 `backend/app/routes/` 하위 별도 파일 (`nodes.py`, `events.py`, `search.py`).

**DB 접근:** 모든 라우트는 `get_driver()`를 통해 driver를 얻고, `with driver.session() as session:` 블록 안에서 Cypher 실행. ORM 사용 없음.

**응답 형태:** `dict` 리스트를 직접 return(FastAPI 자동 JSON 직렬화). 예외: `events.py`는 `Cache-Control: no-store` 헤더를 위해 `JSONResponse`로 명시적으로 감쌈.

**Cypher 파라미터:** 문자열 포맷팅(`f-string`)으로 상수(LIMIT 수치)만 삽입하고, 유저 입력은 반드시 `$param` 바인딩.

**CORS:** `allow_origins=["*"]`, `allow_methods=["GET"]` — 읽기 전용 API.

## ESLint 설정 (`frontend/eslint.config.js`)

- `@eslint/js` recommended
- `eslint-plugin-react-hooks` recommended (v7)
- `eslint-plugin-react-refresh` vite preset
- 대상: `**/*.{js,jsx}`
- 무시: `dist/`
- prettier/biome 미사용 — 포맷터 없음

---

*Convention analysis: 2026-06-14*
