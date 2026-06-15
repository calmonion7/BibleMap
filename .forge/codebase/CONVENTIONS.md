---
last_mapped_commit: 22a678c36e40548a3d00ccf9205862505a59d9cb
mapped: 2026-06-16
---

# Coding Conventions

## 네이밍 패턴

**파일:**
- React 컴포넌트: PascalCase (`frontend/src/MapView.jsx`, `frontend/src/SidePanel.jsx`, `frontend/src/TimelineView.jsx`)
- 유틸리티/공유 모듈: camelCase (`frontend/src/api.js`, `frontend/src/theme.js`, `frontend/src/convexHull.js`)
- CSS: 전역 파일 2개만 존재 (`frontend/src/App.css`, `frontend/src/index.css`). 컴포넌트 범위 CSS 없음.
- 백엔드 라우트: 기능별 snake_case 파일 (`backend/app/routes/nodes.py`, `events.py`, `search.py`, `books.py`)

**React 컴포넌트:**
- 컴포넌트명: PascalCase (`function MapView`, `function SidePanel`, `function SectionHeader`)
- 모든 뷰 컴포넌트는 함수형 + `default export` 단일 함수 (클래스 컴포넌트 없음)
- 파일 내 로컬 서브컴포넌트는 같은 파일 상단에 선언 (`SectionHeader` in `frontend/src/SidePanel.jsx:70`)

**변수 및 함수:**
- camelCase 일관 사용 (`selectNode`, `handleTabClick`, `onSearchInput`, `collapseRing`, `toggleTraitVerse`)
- 이벤트 핸들러: `handle` 접두사(로컬 핸들러) 또는 `on` 접두사(prop 콜백) (`handleTabClick`, `onSelectNode`)
- 모듈 수준 고정값 상수: SCREAMING_SNAKE_CASE (`MOBILE_QUERY`, `SHEET_VH`, `NAV_H`, `SEARCH_LIMIT`, `MAX_NEIGHBORS_PER_TYPE`, `NODE_NEIGHBOR_LIMIT`, `BOOK_COLOR`, `EMPTY_GEOJSON`)
- boolean 상태 변수: `is` / `show` / `can` / `-ed` 접두/접미사 (`isMobile`, `showDropdown`, `canGoBack`, `mapLoaded`, `filterDismissed`, `noLocation`)

**Props:**
- 콜백 prop: `on` 접두사 (`onSelectNode`, `onBack`, `onNodeLoaded`, `onToggle`)
- boolean prop: `can` 접두사 (`canGoBack`)
- 기본값은 디폴트 파라미터로 (`onSelectNode = () => {}`, `canGoBack = false` in `SidePanel.jsx:89`)

**Python (백엔드):**
- 함수명: snake_case (`get_driver`, `get_node`, `get_node_places`, `get_node_neighbors_grouped`, `inject`, `load_json`, `_load_approx`)
- 상수: SCREAMING_SNAKE_CASE (`MAX_NEIGHBORS_PER_TYPE`, `NODE_NEIGHBOR_LIMIT`, `SEARCH_LIMIT`)
- 모듈 수준 singleton/private: 언더스코어 접두사 (`_driver`, `_DATA_DIR`, `_APPROX_PATH`, `_load_approx`)

## 언어 컨벤션 (한국어)

- **UI 문자열은 전부 한국어:** placeholder(`"검색..."`), 안내문(`"지도에서 마커를 클릭하세요"`, `"로딩 중..."`, `"이 항목은 지도에 표시할 위치 정보가 없습니다 — 그래프·타임라인에서 살펴보세요"`), 에러문(`"불러오지 못했습니다"`, `"검색에 실패했습니다"`, `"장소를 불러오지 못했습니다"`), 버튼(`"← 뒤로"`, `"× 닫기"`).
- **코드 주석은 전부 한국어:** 프론트엔드·백엔드 모두. 파일 상단 목적 설명도 한국어.
- **백엔드 도메인 예외 메시지도 한국어:** `RuntimeError("NEO4J_PASSWORD 환경변수가 설정되지 않았습니다")` (`backend/app/db.py:13`).
- 한국어 라벨 매핑은 모듈 수준 객체로: `REL_KO`(`SidePanel.jsx:6`, 관계 타입→한글), `BOOK_ABBR_ORDER`(`SidePanel.jsx:47`, 개역 약어→책 번호), `TYPE_KO`(`theme.js`).

## 공유 팔레트 모듈 (`frontend/src/theme.js`)

노드 타입별 색·한글 라벨·표시 순서는 `frontend/src/theme.js` 단일 파일에 집중. 모든 뷰가 여기서 import한다. (이전엔 각 컴포넌트에 따로 정의돼 GraphView만 값이 달라 충돌했던 이력 — 파일 상단 주석에 기록.)

```js
// frontend/src/theme.js
export const TYPE_COLOR = {
  Person: '#7c9cfc', Place: '#4a90d9', Event: '#f5a623',
  PeopleGroup: '#2bb6a8', Book: '#a78bfa', Unknown: '#9aa5b8',
}
export const TYPE_KO = { Person: '인물', Place: '장소', Event: '사건', PeopleGroup: '집단', Book: '성경책', Unknown: '기타' }
export const TYPE_ORDER = ['Person', 'Place', 'Event', 'PeopleGroup', 'Book']
export const typeColor = (label) => TYPE_COLOR[label] || TYPE_COLOR.Unknown
export const typeKo   = (label) => TYPE_KO[label] || label
export const SELECT_HL = 'rgba(124,156,252,0.18)'  // 선택 강조 틴트(뷰 공통)
```

**규칙:** 타입 색을 컴포넌트 파일 안에 중복 정의하지 않는다. 반드시 `theme.js`에서 import.
- `SidePanel.jsx` → `TYPE_COLOR`, `TYPE_KO`
- `App.jsx` → `TYPE_ORDER`, `typeColor`, `typeKo`, `SELECT_HL`
- `TimelineView.jsx` → `SELECT_HL`

**예외(현존 미준수):** `MapView.jsx`는 maplibre paint 표현식에 색을 하드코딩(`'#f5a623'`, `'#4a90d9'`, `'#9b59b6'`, hull `'#f97316'`)하고 `theme.js`를 import하지 않는다. `theme.js`의 `TYPE_COLOR.Person`('#7c9cfc')과 `SidePanel`이 쓰는 헤더 색은 같으나, App 네비의 active 밑줄(`'#7c9cfc'`)·`TimelineView`의 `BOOK_COLOR`('#a78bfa')처럼 로컬 상수로 둔 값도 일부 있다.

## API 클라이언트

공유 헬퍼는 `frontend/src/api.js`에 정의돼 있으나 **사실상 미사용**이다. 각 컴포넌트는 파일 상단에 직접 `const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'`을 선언하고 `fetch`를 직접 호출한다(`MapView.jsx`, `SidePanel.jsx`, `TimelineView.jsx`, `App.jsx`).

```js
// frontend/src/api.js — 정의는 있으나 호출부 없음
export const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'
export async function apiGet(path, { signal } = {}) {
  const res = await fetch(API_BASE + path, { signal })
  if (!res.ok) throw res.status   // 비-OK는 status(숫자) throw
  return res.json()
}
```

직접 fetch도 동일 시맨틱을 따른다:
- 비-OK 응답: `r.ok ? r.json() : Promise.reject(r.status)` (숫자 reject) 패턴
- AbortError: 호출부에서 `e?.name === 'AbortError'` / `e.name === 'AbortError'`로 구분해 무시
- 프로덕션은 `VITE_API_URL=/api`(빌드타임 주입)로 nginx 프록시(`/api` → `api:8000`)를 탄다.

## Import 순서

```js
import { useState, useEffect, useRef } from 'react'   // 1. React hooks
import maplibregl from 'maplibre-gl'                   // 2. 외부 라이브러리
import 'maplibre-gl/dist/maplibre-gl.css'
import { Map, Clock, Search, X } from 'lucide-react'
import { TYPE_COLOR, TYPE_ORDER } from './theme'       // 3. 내부 공유 모듈
import { convexHull } from './convexHull'
import MapView from './MapView'                        // 4. 내부 컴포넌트
```

## 스타일 패턴

**인라인 스타일 우선:** JSX에 `style={{ }}` 인라인 객체를 직접 쓴다. CSS 클래스는 사용하지 않는다(전역 reset 제외). 동적 색은 템플릿 리터럴로 (`borderLeft: \`3px solid ${TYPE_COLOR[t]}\``).

**다크 배경 팔레트:**
- 네비 배경 `#1a1a2e`, 드롭다운 배경 `#1e2040`/`#11131f`
- 어두운 배경 텍스트: `white`, `rgba(255,255,255,0.4~0.7)`

**화이트 패널 팔레트(SidePanel):**
- 배경 `white`, `#f8faff`(traits 박스), `#f5f3ff`/`#eef2ff`(구절 박스)
- 보조 텍스트 `#7c8db0`, `#5a6481`, `#9aa5b8`, `#aab2c5` / 구분선 `#eef0f5`

**반응형:** `MOBILE_QUERY = '(max-width: 768px)'`를 `window.matchMedia`로 감지. `App.jsx`가 `isMobile` state를 관리하고, 하위(`MapView.jsx`)는 `window.innerWidth <= 768`을 직접 확인한다. `App.jsx`의 하단 시트 높이(`SHEET_VH=55`)는 `MapView.jsx`의 `fitBounds` 하단 패딩 비율(0.55)과 반드시 일치시켜야 한다(양쪽 주석에 명시).

## React 훅 규칙

**setState 위치 — `react-hooks/set-state-in-effect` 준수:** ESLint `eslint-plugin-react-hooks` v7이 effect 동기 본문에서의 setState를 막는다. 따라서 모든 setState는 `setTimeout`/async/`.then()` 콜백 안에서만 호출한다. 두 곳에 명시 주석:
- `App.jsx:59` — `// setState는 전부 setTimeout/async 콜백 안에서만(effect 동기 본문 setState 금지 — react-hooks v7).`
- `SidePanel.jsx:91` — `// setState는 비동기 콜백에서만 호출(react-hooks set-state-in-effect 준수).`

**stale 응답 가드 (`SidePanel.jsx`의 핵심 패턴):** 상태를 어느 `nodeId`의 결과인지 함께 저장(`{ id, node, error }`)하고, 렌더 시 `state.id === nodeId`로 최신 여부를 판정한다. `loading`은 별도 state가 아니라 `ready = state.id === nodeId`에서 파생된다. setState는 fetch `.then()`/`.catch()`(비동기) 안에서만, 그것도 `cancelled` 플래그가 false일 때만 호출한다.

```js
// SidePanel.jsx — id 추적 + cancelled 플래그 병용
const [state, setState] = useState({ id: null, node: null, error: null })
useEffect(() => {
  if (!nodeId) return
  let cancelled = false
  fetch(API_URL + '/node/' + nodeId)
    .then(r => r.ok ? r.json() : Promise.reject(r.status))
    .then(data => { if (!cancelled) { setState({ id: nodeId, node: data, error: null }); onNodeLoaded?.(data) } })
    .catch(e => { if (!cancelled) setState({ id: nodeId, node: null, error: String(e) }) })
  return () => { cancelled = true }
}, [nodeId])
const ready = state.id === nodeId
const node  = ready ? state.node : null   // stale면 null로 무시
```

**경쟁 조건 방지(전반):**
- `AbortController`로 직전 요청 취소(`App.jsx` 검색 debounce, `MapView.jsx` `/places`·`expandPlace`)
- `cancelled` 플래그 + id 비교 병용(`SidePanel.jsx`)
- `mapRef.current !== map` 비교로 맵 재초기화 후 stale 콜백 차단(`MapView.jsx`)

**`useCallback` 안정화:** 부모→자식 콜백이 자식 `useEffect` 의존성이 되어 불필요한 재실행(→fetch abort)을 유발하는 것을 막기 위해 `useCallback(fn, [])` + `useRef`로 최신값 참조한다.

```js
// App.jsx — selectNode 안정 참조(selectedNodeRef로 최신값 읽음)
const selectedNodeRef = useRef(null)
useEffect(() => { selectedNodeRef.current = selectedNode }, [selectedNode])
const selectNode = useCallback((id) => {
  if (id === selectedNodeRef.current) return
  ...
}, [])
```

**`useRef`의 비-DOM 용도:** 애니메이션 프레임 핸들(`animFrame`), abort 컨트롤러(`expandAbortCtrl`), 맵/팝업 인스턴스(`mapRef`, `popupRef`), 클로저 공유 함수·상태 참조(`expandPlaceRef`, `expandedPlaceRef`). 프레임마다 리렌더가 필요 없는 값은 state가 아닌 ref/로컬 변수로 둔다(`MapView.jsx:53` 주석 참고).

## 섹션 접기/펼치기 컨벤션 (SidePanel)

`collapsed` state는 `{ [sectionKey]: false | undefined }`. **`false` = 펼침, `undefined`(미설정) = 접힘(기본).** 토글은 `false`↔`undefined`를 오간다.

```js
// SidePanel.jsx
const [collapsed, setCollapsed] = useState({})
function toggle(key) {
  setCollapsed(prev => ({ ...prev, [key]: prev[key] === false }))  // false→undefined, undefined→false
}
const isOpen = collapsed[sectionKey] === false        // 펼침 판정
// 콘텐츠 렌더: {collapsed[key] === false && (...)}
```

`SectionHeader`(`SidePanel.jsx:70`)가 토글 버튼이고, 노드가 바뀌면 `useEffect`에서 `setCollapsed({})`로 전부 접는다.

## Lazy-fetch + 캐시 키잉 패턴 (SidePanel)

펼칠 때 1회만 외부 fetch하고, 결과를 키로 캐시해 재fetch와 stale을 동시에 방지한다.
- **trait 원문**: `traitVerses` state를 **노드가 아닌 `verse_ref`(구절 참조 문자열)로 키잉**한다 — 노드 무관·동일 구절 재fetch 방지·stale 안전. 값은 `{ status: 'loading'|'done'|'error', text? }`. `toggleTraitVerse(i, ref)`가 펼침일 때 `traitVerses[ref] === undefined`인 경우에만 fetch(`SidePanel.jsx:155`).
- **Book keyVerse 원문**: `keyVerseText` state, `state`/`nodeId` 의존 effect에서 fetch하되 `cancelled` 플래그로 stale 무시.

외부 구절 API는 getbible v2(`https://api.getbible.net/v2/korean/{bookOrder}/{chapter}.json`)에서 장 JSON을 받아 `verses[]`에서 절을 찾는 헬퍼(`fetchVerseText`)로 통일.

## 오류 처리

**프론트엔드:**
- `error` boolean state(`useState(false)`), 빈 결과는 별도 boolean(`noLocation`, `searchError`)
- 에러 UI는 인라인 스타일 div/p로 직접 표시(전용 컴포넌트 없음)
- AbortError는 무시(`if (e?.name !== 'AbortError') setError(true)`)
- `eslint-disable` 주석은 코드 전반에 0건 — 규칙을 끄지 않고 패턴으로 우회한다.

**백엔드 (FastAPI):**
- 노드 없음: `raise HTTPException(status_code=404, detail="Node not found")`
- Neo4j 비번 누락: `RuntimeError`로 즉시 실패(`db.py`)
- startup 인덱스 생성 실패: `logging.exception(...)` 후 비치명적으로 계속(`main.py` lifespan)
- 라우트는 대체로 try/except 없이 작성 — 세션 오류는 FastAPI 500으로 자동 전달
- 외부 파일/JSON 로드 실패는 빈 dict 폴백(`books.py` `_load_approx`의 `except (FileNotFoundError, json.JSONDecodeError)`)
- `Person.traits` 파싱: inline `import json as _json` 후 `try/except`로 빈 리스트 폴백(`nodes.py:230`)

## 코멘트 패턴

**왜(why) 위주:** 이 방식인 이유·대안 대비 선택 근거·과거 회고에서 얻은 교훈을 인라인 주석으로 남긴다.

```js
// moveend는 카메라가 안 움직이면 미발화하므로 폴백 타이머(700ms)로 보장, fired로 단발.
// (공유 source 동시 setData 충돌 회피 — radial-ring 회고)
```

- JSDoc은 순수 유틸 1곳만(`convexHull.js`의 `@param`/`@returns`). 그 외는 1~3줄 한국어 설명.
- 파일 상단에 모듈 목적 1~2줄(`api.js`, `theme.js`, `convexHull.js`, 각 inject 스크립트).

## 백엔드 라우트 컨벤션

**APIRouter 분리:** 각 기능 파일이 `router = APIRouter()`를 만들고 `@router.get(...)`으로 핸들러를 등록. `main.py`가 `app.include_router(...)`로 전부 마운트한다(`nodes`, `events`, `search`, `books`).

**DB 접근:** 항상 `driver = get_driver()` → `with driver.session() as session:` 블록 안에서 `session.run(cypher, **params)`. ORM 없음.

**노드 → dict prop 매핑:** Neo4j 노드를 `props = dict(node)`로 펼친 뒤 `props.get(...)`으로 읽어 응답 dict를 조립한다. 반복되는 관용구:
- 이름 폴백: `name = props.get("name") or props.get("title", "")`
- 한국어 이름 + 미번역 신호: `name_ko = props.get("nameKo")` → 응답에 `nameKo: name_ko if name_ko else name`, `nameKoMissing: name_ko is None`
- id: `props.get("theographic_id", "")`
- `properties` 클린업: `exclude = {"name","nameKo","theographic_id","aliasesKo"}`로 거른 `clean_props`만 노출(`nodes.py:184`)

**응답 형태:** 기본은 dict/list를 그대로 return(FastAPI 자동 JSON 직렬화). **`Cache-Control: no-store` 헤더가 필요한 라우트만 `JSONResponse(content=..., headers={"Cache-Control": "no-store"})`로 명시적으로 감싼다 — `events.py`, `books.py`(`search.py`·`nodes.py`는 plain return).**

**Cypher 파라미터화:** 사용자 입력은 반드시 `$param` 바인딩(`id=node_id`, `q=q`). 상수 LIMIT 수치만 f-string으로 삽입(`nodes.py:157` `LIMIT {NODE_NEIGHBOR_LIMIT}`, `search.py:27` `LIMIT {SEARCH_LIMIT}`). Cypher 중괄호 충돌은 `{{ }}`로 이스케이프.

**타입별 분기:** `labels(n)[0]`로 라벨을 뽑아 `if label == "Person"/"Event"/"PeopleGroup"/"Book"/else`로 분기(`nodes.py` `/places`). Book 노드만 응답에 `topPersons`/`topEvents` 추가 필드를 붙인다.

**CORS:** `allow_origins=["*"]`, `allow_methods=["GET"]`, `allow_credentials=False` — 읽기 전용 API(`main.py`).

**환경변수:** `os.getenv(..., default)` 패턴. `NEO4J_PASSWORD`만 디폴트 없이 필수(없으면 RuntimeError). 데이터 경로는 `os.environ.get("DATA_DIR", "/app/data")`.

## 데이터/스크립트 컨벤션 (`backend/scripts/`)

- 일회성 로드/주입 스크립트는 `#!/usr/bin/env python3` shebang + 모듈 docstring(영문/한글 혼용)으로 시작.
- 모듈 상단에서 `NEO4J_URI/USER/PASSWORD`를 `os.getenv`로 읽고, 비번 누락 시 즉시 RuntimeError.
- 데이터 경로는 `Path(__file__).parent...`로 리포 내 `data/` 하위(`names_ko`, `character_traits`, `book_context`, `book_years_approx`)를 가리킨다.
- `data/`는 런타임 볼륨(`./data:/app/data`)으로도 마운트되어 API가 직접 읽는다(`books.py`의 추정연도 오버레이).

## ESLint 설정 (`frontend/eslint.config.js`)

flat config(`defineConfig`):
- `@eslint/js` recommended
- `eslint-plugin-react-hooks` v7 `configs.flat.recommended` (핵심: `react-hooks/set-state-in-effect`, exhaustive-deps)
- `eslint-plugin-react-refresh` `configs.vite`
- 대상 `**/*.{js,jsx}`, 무시 `dist/`, 브라우저 globals
- **포맷터(prettier/biome) 없음.** 백엔드에 linter/type-checker 설정 없음.
