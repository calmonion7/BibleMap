---
last_mapped_commit: 7522aafe2088e83e8c4bed86a4f0269082db07e0
mapped: 2026-06-20
---

# 코딩 컨벤션

## 언어 및 프레임워크 기준

**프론트엔드**: JavaScript(TypeScript 미사용) + React 19. 파일 확장자는 컴포넌트에 `.jsx`, 순수 유틸·훅에 `.js`.
**백엔드**: Python 3 + FastAPI. 타입 힌트는 라우터 파라미터·반환값 수준에서만 산발적으로 사용하고, 전면 적용하지 않는다.

---

## 파일 네이밍

**프론트엔드 컴포넌트**: PascalCase + `.jsx`
- `App.jsx`, `MapView.jsx`, `SidePanel.jsx`, `TimelineView.jsx`, `BibleOverviewView.jsx`, `Spinner.jsx`, `VerseLangTabs.jsx`

**프론트엔드 훅/유틸**: camelCase + `.js`. 훅은 `use` 접두사 필수.
- `useNodeSelection.js`, `useSearch.js`, `api.js`, `theme.js`, `convexHull.js`

**백엔드 라우터**: 단수형 snake_case + `.py`
- `nodes.py`, `events.py`, `search.py`, `books.py`

**백엔드 스크립트**: 동사_목적어 snake_case
- `load_theographic.py`, `generate_verse_text.py`, `inject_ko_names.py`, `enrich_place_coords.py`

---

## 네이밍 규칙

**React 컴포넌트 함수**: PascalCase (`function MapView`, `function SidePanel`)
**React 훅**: camelCase (`useNodeSelection`, `useSearch`). 훅 내부 상태 이름은 `state` 단일 객체보다 개별 `useState` 선호(`selectedNode`, `error`, `loading` 등을 각각).
**이벤트 핸들러**: `handle` + PascalCase 명사/동사 (`handleTabClick`, `handleSelectResult`, `handleNodeLoaded`) 또는 `on` + PascalCase (`onSearchInput`, `onSheetTouchStart`).
**상수(모듈 수준)**: UPPER_SNAKE_CASE (`TABS`, `MOBILE_QUERY`, `SHEET_VH`, `API_BASE`, `SEARCH_LIMIT`, `MAX_NEIGHBORS_PER_TYPE`)
**Python 함수/변수**: snake_case. 모듈 내부 비공개 함수는 `_` 접두사 (`_load_approx_book_index`, `_compute_events`, `_resolve`, `_load`)

---

## 임포트 스타일

### 프론트엔드(JSX/JS)

```js
// 1. React 훅 (named import)
import { useState, useEffect, useCallback, useRef } from 'react'
// 2. 외부 라이브러리
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
// 3. 내부 모듈 — 상대경로, 확장자 생략
import { TYPE_COLOR, TYPE_KO } from './theme'
import { apiGet } from './api'
import Spinner from './Spinner'
```

경로 alias 미사용. 모두 `./` 상대경로.

### 백엔드(Python)

```python
# 표준 라이브러리 → 서드파티 → 내부 상대 임포트 순
import os
import json
import functools
from fastapi import APIRouter, HTTPException
from ..db import get_driver
from .. import overlays
```

---

## 컴포넌트 설계

**Props 기본값**: 함수 파라미터 기본값으로 선언.
```js
function SidePanel({ nodeId, onSelectNode = () => {}, onBack = () => {}, canGoBack = false, ... }) {
```

**컴포넌트 크기**: 뷰 컴포넌트(`MapView`, `TimelineView`, `SidePanel`)는 300~500줄 이내. 로직이 커지면 커스텀 훅(`useNodeSelection`, `useSearch`)으로 추출.

**스타일**: CSS 파일/모듈 없음. 모든 스타일은 인라인 `style` 객체로 직접 작성. Tailwind 미사용.

---

## 커스텀 훅 패턴

훅은 `src/` 최상위에 `use*.js`로 위치.

```js
// 이름 있는 익스포트(named export). default 미사용.
export function useNodeSelection() {
  const [selectedNode, setSelectedNode] = useState(null)
  // ...
  return { selectedNode, selectNode, goBack, closePanel, ... }
}
```

반환값은 단일 객체로 묶어 구조분해로 사용.

---

## 비동기·fetch 패턴

**API 클라이언트**: `api.js`의 `apiGet` 단일 진입점. 비-OK 응답은 `err.status`를 담은 `Error`로 reject.

```js
// api.js
export async function apiGet(path, { signal } = {}) {
  const res = await fetch(API_BASE + path, { signal })
  if (!res.ok) { const err = new Error(String(res.status)); err.status = res.status; throw err }
  return res.json()
}
```

**useEffect 내 fetch**: AbortController로 경쟁 차단. 취소된 요청은 `e.name === 'AbortError'`로 식별해 무시.

```js
useEffect(() => {
  let cancelled = false
  apiGet('/node/' + nodeId)
    .then(data => { if (!cancelled) setState({ ... }) })
    .catch(e => { if (!cancelled) setState({ error: e?.status ?? String(e) }) })
  return () => { cancelled = true }
}, [nodeId])
```

**디바운스 fetch**: `setTimeout` + `AbortController` 조합으로 구현(`useSearch.js`).

**react-hooks 규칙**: `useEffect` 동기 본문에서 `setState` 직접 호출 금지 — 항상 비동기 콜백(`then`/`catch`/`setTimeout` 내부)에서만 호출. (`useSearch.js` 주석 참조)

---

## 에러 처리

### 프론트엔드

- fetch 에러는 컴포넌트 지역 `error` state로 관리. 콘솔 로깅 없음.
- `AbortError`는 에러로 취급하지 않고 조용히 무시.
- UI는 에러 상태를 인라인 메시지로 표시.

```jsx
if (error) return <p style={{ color: '#dc3545' }}>불러오지 못했습니다 ({error})</p>
```

### 백엔드

- 노드 없으면 `HTTPException(status_code=404)` raise.
- Neo4j 연결 실패는 `RuntimeError` (환경변수 미설정 시).
- 앱 기동 중 인덱스 생성 실패는 `logging.exception`으로 기록 후 계속 진행(`lifespan` 참조).
- `try/except Exception: pass` 패턴은 사용하지 않고 구체적 예외(`TypeError`, `ValueError`)를 명시.

---

## 상태 공유 패턴

**테마/팔레트**: `theme.js` 단일 출처. 색상·한글 라벨·정렬 순서를 exports로 노출.
```js
// theme.js
export const TYPE_COLOR = { Person: '#7c9cfc', ... }
export const typeColor = (label) => TYPE_COLOR[label] || TYPE_COLOR.Unknown
```

**뷰 간 공유 상태**: `App.jsx`에 끌어올려 props로 전달 (`verseLang`, `selectedNode` 등).

**뷰 상태 보존**: 탭 전환 시 뷰를 언마운트하지 않고 `display: 'none'/'block'` CSS 토글로 상태 유지.

---

## 백엔드 캐싱 패턴

**메모리 캐시**: `functools.lru_cache(maxsize=1)`. 앱 재시작 전까지 결과 보관.
```python
@functools.lru_cache(maxsize=1)
def _compute_events():
    ...
```

**HTTP 캐시 헤더**: `JSONResponse(..., headers={"Cache-Control": "max-age=300"})` (이벤트 목록). `Cache-Control: no-store` (책 목록).

---

## 데이터 접근 패턴

**Neo4j 드라이버**: `db.py`의 `get_driver()` 싱글턴. 모든 라우터가 `from ..db import get_driver`로 가져와 `with driver.session() as session:` 블록에서 사용.

**오버레이 JSON**: 런타임 파일 읽기 + `lru_cache`(`overlays.py`). 추정 데이터(book_years_approx, book_events, event_verses)는 Neo4j 주입 없이 오버레이로만 제공.

---

## 주석 스타일

- 한국어 인라인 주석으로 의도·배경 설명. 영어 주석 거의 없음.
- 복잡한 로직 결정 근거는 파일 상단 모듈 docstring 또는 인라인으로 기록.
- 백엔드 스크립트는 파일 맨 위에 목적·출력·사용법을 한국어 docstring으로 명시.
- JSDoc/TSDoc 미사용. 단, 공개 유틸 함수(`convexHull`)에는 JSDoc으로 파라미터·반환값 기술.

---

## 모듈 익스포트

**프론트엔드 컴포넌트**: `export default`(기본 익스포트).
**훅/유틸 함수**: named export.
**상수/헬퍼**: named export (`export const`, `export function`).

```js
// 컴포넌트
export default function MapView({ ... }) { ... }

// 훅
export function useSearch() { ... }

// 상수
export const TYPE_COLOR = { ... }
export const typeColor = (label) => ...
```
