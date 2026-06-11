---
last_mapped_commit: 288b14e23c889de294d34d0f794867d4e313a421
mapped: 2026-06-11
---

# 코딩 컨벤션

BibleMap 코드베이스의 실제 코드에서 관찰된 스타일·패턴 규약. 도메인 용어 정의는 다루지 않는다(그것은 CONTEXT.md 영역).

---

## 1. 프론트엔드 — 스타일링: 인라인 style + JS 상태만 사용

**className 기반 CSS는 쓰지 않는다.** 모든 시각 표현은 JSX의 `style={{ ... }}` 인라인 객체와 JS 상태로 처리한다. `.jsx` 컴포넌트들(`App.jsx`, `MapView.jsx`, `SidePanel.jsx`, `GraphView.jsx`, `TimelineView.jsx`) 어디에도 의미 있는 `className`이 없다.

- 조건부 스타일은 삼항/스프레드로 인라인 분기한다. 예: `App.jsx`의 패널 오버레이는 `...(isMobile ? {...} : {...})`로 모바일/데스크톱 스타일 객체를 통째로 갈아끼운다.
- 호버 효과도 클래스 대신 이벤트 핸들러로 직접 DOM 스타일을 만진다. 예: `SidePanel.jsx` / `App.jsx`의 `onMouseEnter`/`onMouseLeave`에서 `e.currentTarget.style.background`를 직접 토글한다.
- 색상·간격 등 매직값은 인라인 리터럴로 그대로 박혀 있다(CSS 변수 미사용).

### DEAD CODE: Vite 템플릿 잔재 CSS
- `frontend/src/App.css` — 전체가 Vite 스타터 템플릿 잔재(`.counter`, `.hero`, `#next-steps`, `.ticks` 등)다. 어느 컴포넌트도 import하지 않으며(`App.jsx`는 `App.css`를 import하지 않음) 클래스명도 사용되지 않는다. **죽은 코드.**
- `frontend/src/index.css` — `main.jsx`가 `import './index.css'`로 로드하긴 하나, 살아 있는 규칙은 사실상 `body { margin: 0 }`와 `#root { width/height: 100% }`뿐이다. 나머지(`:root`의 `--accent` 등 CSS 변수, `h1/h2`, `code`, prefers-color-scheme 다크 블록)는 인라인 스타일 컴포넌트가 쓰지 않는 Vite 템플릿 잔재다.
- 새 스타일을 추가할 때 이 파일들에 클래스를 더하지 말 것 — 컨벤션은 인라인 style이다.

## 2. 프론트엔드 — 컴포넌트 파일 규약

- 한 파일 = 한 컴포넌트. 파일명·컴포넌트명 모두 **PascalCase**, 파일명과 같은 이름으로 default export. 예: `MapView.jsx` → `export default function MapView(...)`, `SidePanel.jsx` → `function SidePanel(...)` + `export default SidePanel`.
- 함수 컴포넌트만 사용(클래스 컴포넌트 없음). 선언 형태는 `export default function X()`(`MapView`, `GraphView`)와 `function X() { ... } export default X`(`App`, `SidePanel`, `TimelineView`)가 혼재 — 통일돼 있지 않다.
- props 기본값은 디스트럭처링 시 직접 부여. 예: `SidePanel({ nodeId, onSelectNode = () => {}, onBack = () => {}, canGoBack = false })`.
- `import { ... } from 'react'`로 훅을 명시적으로 가져온다. 라우터·전역 상태 라이브러리 없음 — 상태는 `App.jsx`가 보유하고 props로 내려준다(`selectedNode`/`onSelectNode`).
- 들여쓰기 2칸, 세미콜론 없음, 작은따옴표. JSX 주석은 한국어로 의도를 설명한다.

## 3. 프론트엔드 — react-hooks `set-state-in-effect` 준수 패턴 (살아 있는 규약)

`eslint-plugin-react-hooks` v7(`eslint.config.js`의 `reactHooks.configs.flat.recommended`)이 강제하는 규칙이다. **effect 본문에서 동기적으로 `setState`를 호출하지 않는다.** `setState`는 오직 다음에서만 호출한다:

- 비동기 콜백(`fetch(...).then(...)` / `.catch(...)`) 안 — `SidePanel.jsx`, `MapView.jsx`, `GraphView.jsx`, `TimelineView.jsx`의 데이터 로딩 effect 전부 이 형태.
- 이벤트 핸들러 안 — `onChange`, `onClick`, `onKeyDown`, `matchMedia`의 `change` 리스너 등.

구체 패턴:
- `SidePanel.jsx`: 단일 객체 상태 `{ id, node, error }`를 두고 stale 응답을 막는다. effect 안에서 `let cancelled = false`를 쓰고, `.then`/`.catch`에서 `if (!cancelled) setState(...)`로만 갱신. cleanup에서 `cancelled = true`. `loading`은 별도 상태가 아니라 `state.id === nodeId` 비교로 파생한다(주석에 "loading은 파생, stale 응답은 무시"라고 명시).
- `MapView.jsx`: `AbortController`로 in-flight fetch를 취소하고, 응답 콜백에서 `mapRef.current === map`인지 확인한 뒤에만 `setError(false)`/지도 데이터 갱신. `setError(true)`도 `.catch` 안에서만, `AbortError`는 무시.
- `GraphView.jsx`: `Promise.all([...]).then(...)` 콜백 안에서 `if (!cancelled) setError(false)` 후 cytoscape를 구성. cleanup에서 `cancelled = true`.
- `App.jsx`: `matchMedia(MOBILE_QUERY)`의 `change` 리스너(이벤트 콜백) 안에서만 `setIsMobile(e.matches)`. `useState` 초기값으로 동기 `matchMedia(...).matches`를 쓰는 것은 effect가 아니므로 허용.

`npx eslint .`는 현재 **완전히 clean**(exit 0). 새 effect를 추가할 때 이 패턴을 깨지 말 것.

## 4. 프론트엔드 — 엔티티 타입 → 색상 팔레트 (UI 색상 컨벤션, 앞으로의 기준)

엔티티를 색으로 구분하는 새 UI는 **`SidePanel.jsx`의 팔레트를 재사용**한다. 정의 위치: `frontend/src/SidePanel.jsx`.

```js
const TYPE_ORDER = ['Person', 'Place', 'Event', 'PeopleGroup', 'Unknown']
const TYPE_KO    = { Person: '인물', Place: '장소', Event: '사건', PeopleGroup: '집단', Unknown: '기타' }
const TYPE_COLOR = { Person: '#7c9cfc', Place: '#4a90d9', Event: '#f5a623', PeopleGroup: '#2bb6a8', Unknown: '#9aa5b8' }
```

색 의미:
- `Person #7c9cfc` — 앱 보라 액센트(네비 탭 활성 밑줄 `#7c9cfc`, 검색 드롭다운 라벨 색과 동계).
- `Place #4a90d9` — 지도 related-place 파랑.
- `Event #f5a623` — 지도 주황.
- `PeopleGroup #2bb6a8` — 청록.
- `Unknown #9aa5b8` — 회색.

**Place/Event 색조는 `MapView.jsx`의 마커 색과 의도적으로 동일하다.** `MapView.jsx`의 `places-circle` 레이어: `isPrimary`(선택된 장소)면 `#f5a623`(주황, Event와 동일), 아니면 `#4a90d9`(파랑, Place와 동일). 그림자 레이어는 `rgba(0,0,0,0.2)`. 라벨/팝업 텍스트 본문색은 `#1a1a2e`, 보조 텍스트 `#7c8db0`.

타입 라벨 정규화: `SidePanel.jsx`의 `typeOf(label)`은 `TYPE_COLOR`에 없는 라벨을 `'Unknown'`으로 떨어뜨린다. 이웃 렌더링은 `TYPE_ORDER` 순서로 그룹 출력.

관계(relationship) 타입의 한글 라벨은 별도 상수 `REL_KO`(`SidePanel.jsx`)에 산다: `PARENT_OF:'부모', CHILD_OF:'자녀', SIBLING_OF:'형제·자매', PARTNER_OF:'배우자', MEMBER_OF:'소속', HAS_PARTICIPANT:'참여', OCCURS_AT:'발생 장소', PART_OF:'상위 사건'`. 미매핑 관계는 원문 그대로 표시(`REL_KO[r] || r`).

### 주의: GraphView는 다른(오래된) 팔레트를 쓴다
`GraphView.jsx`는 자체 `TYPE_COLOR = { Person:'#4a90d9', Place:'#27ae60', Event:'#e67e22', PeopleGroup:'#8e44ad' }`와 `TYPE_LABEL_KO`(관련 인물/사건/그룹/장소)를 별도로 갖고 있어 SidePanel/MapView 팔레트와 **일치하지 않는다**. 새 UI 기준은 SidePanel 팔레트이며, GraphView는 cytoscape 셀렉터 스타일(`node[nodeType = "Person"]` 등)로 색을 부여하는 분리된 영역이다.

## 5. 프론트엔드 — 모바일 분기와 결합 상수

모바일 브레이크포인트는 **768px**. 두 곳에서 따로 판정하므로 **반드시 동기화**해야 한다:
- `App.jsx`: `const MOBILE_QUERY = '(max-width: 768px)'` + `window.matchMedia(MOBILE_QUERY)`.
- `MapView.jsx`: `const isMobile = window.innerWidth <= 768` (fitBounds 패딩 계산용).

하단 시트 높이도 두 파일에 걸친 결합 상수다:
- `App.jsx`: `const SHEET_VH = 55` — 모바일 패널이 `height: '55vh'`로 하단에서 슬라이드업.
- `MapView.jsx`: `fitBounds`의 모바일 하단 패딩 `Math.round(window.innerHeight * 0.55) + 20` — 시트가 가리는 만큼 마커를 상단 띠로 밀어올린다. `0.55`는 `SHEET_VH/100`과 일치시켜야 한다(양쪽 주석에 명시됨).

기타 인라인 레이아웃 상수: `App.jsx`의 네비 높이 `const NAV_H = 48`(패널 `top`, 그래프 뷰 컨테이너 `top`에 재사용). 패널 슬라이드 전환은 `transform 0.25s ease`로 데스크톱은 `translateX`, 모바일은 `translateY`.

## 6. 프론트엔드 — API 호출 규약

- 모든 컴포넌트가 동일 패턴으로 베이스 URL을 잡는다: `const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'` (`App.jsx`만 상수명이 `API_BASE`, 나머지는 `API_URL`).
- `fetch` 직후 `.then(r => r.ok ? r.json() : Promise.reject(r.status))`로 HTTP 에러를 거부로 변환하는 관용구가 반복된다. `.catch`에서 에러 상태 플래그(`setError(true)` / `setState({..., error})`)를 세운다.
- 사용자 향 에러는 한국어 인라인 메시지로 표시: "검색에 실패했습니다"(`App.jsx`), "불러오지 못했습니다 ({error})"(`SidePanel.jsx`), "장소를 불러오지 못했습니다"(`MapView.jsx`), "그래프를 불러오지 못했습니다"(`GraphView.jsx`), "사건을 불러오지 못했습니다"(`TimelineView.jsx`).
- 쿼리스트링은 `encodeURIComponent`로 인코딩(`App.jsx`의 검색).

## 7. 백엔드 — Python 스타일 (FastAPI + Neo4j)

- **snake_case** 함수·변수명. 파일·모듈도 snake_case (`nodes.py`, `events.py`, `load_theographic.py`, `inject_ko_names.py`).
- **라우트 파일 1개당 `APIRouter` 1개**, 모듈 레벨에 `router = APIRouter()` 변수로 둔다(`routes/nodes.py`, `routes/events.py`, `routes/search.py`). `main.py`가 `app.include_router(...)`로 모두 등록.
- `routes/__init__.py`는 빈 패키지 마커(1줄). 라우터 import는 `main.py`에서 `from .routes import nodes, events, search`.
- **매직 넘버는 모듈 레벨 UPPER_SNAKE 상수로 호이스팅.** 예: `nodes.py`의 `MAX_NEIGHBORS_PER_TYPE = 30`, `NODE_NEIGHBOR_LIMIT = 50`; `search.py`의 `SEARCH_LIMIT = 20`; 적재 스크립트의 `BATCH_NODE = 500`, `BATCH_REL = 1000`.
- **주석·로그·에러 메시지는 한국어.** 예: `db.py`의 `"NEO4J_PASSWORD 환경변수가 설정되지 않았습니다"`, `main.py`의 `"Neo4j 인덱스 생성 실패 — 인덱스 없이 계속 진행합니다"`. (단 적재/주입 스크립트의 `print`는 영어 진행 로그 — "Loading ... nodes", "Done." 등으로 혼재.)
- DB 핸들은 `db.py`의 모듈 전역 `_driver` 싱글턴 + `get_driver()` 게으른 초기화. 환경변수 `NEO4J_URI`/`NEO4J_USER`는 기본값 있음, `NEO4J_PASSWORD`는 없으면 `RuntimeError`로 즉시 실패(fail-fast).
- 세션은 `with driver.session() as session:` 컨텍스트 매니저로 매 요청 열고 닫는다.

## 8. 백엔드 — Cypher / 쿼리 규약

- **쿼리 파라미터는 항상 바인딩**한다 — 사용자 입력을 쿼리 문자열에 직접 끼워넣지 않는다. 노드 조회는 `$id`(예: `MATCH (n {theographic_id: $id})`), 검색은 `$q`(예: `WHERE (n.nameKo CONTAINS $q OR n.name CONTAINS $q)`)로 바인딩.
- 단, **상수 LIMIT는 f-string으로 삽입**된다(상수이므로 주입 위험 없음): `nodes.py`의 `... LIMIT {NODE_NEIGHBOR_LIMIT}`, `search.py`의 `LIMIT {SEARCH_LIMIT}`. 라벨로 분기하는 인덱스 생성도 f-string(`f"CREATE INDEX {label.lower()}_tid ..."`, `main.py`). 값(value)은 바인딩, 구조(label/limit)는 f-string이라는 분리.
- 노드 식별자는 도메인 키 `theographic_id`(원천 데이터의 `id`)로 매칭하며, 라벨별 인덱스 `{label}_tid`를 둔다(`main.py` lifespan, `load_theographic.py` `create_indexes`).
- 적재(`load_theographic.py`)는 전부 `MERGE` 기반 idempotent. 노드/관계를 `run_batched(...)`로 배치 `UNWIND`. 양방향 관계(SIBLING_OF, PARTNER_OF)는 정렬된 키 튜플로 중복 제거 후 무방향 `MERGE (a)-[:REL]-(b)`. PARENT_OF/CHILD_OF는 쌍방향 두 관계로 명시 생성.

## 9. 백엔드 — 응답 직렬화 규약

- Neo4j 노드를 `dict(node)`로 펼친 뒤 필요한 필드만 골라 JSON dict로 재구성한다.
- **이름 폴백 규약**(여러 라우트에서 반복): 표시명은 `name`(인물/장소) 또는 `title`(사건) 중 존재하는 것 — `props.get("name") or props.get("title", "")`. 한글명은 `nameKo`가 있으면 그것, 없으면 영문명으로 폴백 — `name_ko if name_ko else name` 또는 `props.get("nameKo") or name`.
- **`nameKoMissing` 플래그**: `nameKo`가 `None`이면 `True`. 프론트는 이걸로 "(미번역)" 접미사를 붙인다(`SidePanel.jsx`, `node.nameKoMissing ? `${node.name} (미번역)` : node.nameKo`).
- 라벨은 `labels(n)[0]`(첫 라벨)을 대표 라벨로, 없으면 `"Unknown"`.
- `nodes.py`의 `get_node`는 민감/중복 필드 `{"name","nameKo","theographic_id","aliasesKo"}`를 `properties`에서 제외하고 나머지를 `clean_props`로 반환.
- 좌표는 `float(...)` 변환, `TypeError/ValueError` 시 해당 장소를 `continue`로 스킵(`nodes.py` `get_node_places`). `theographic_id`로 `seen` 집합 중복 제거.
- `events.py`만 캐시를 명시적으로 끈다: `JSONResponse(content=events, headers={"Cache-Control": "no-store"})`.

## 10. 백엔드 — 에러 처리 규약

- 노드 미존재는 `raise HTTPException(status_code=404, detail="Node not found")`(`nodes.py`).
- 빈 검색어는 빈 리스트 즉시 반환(`search.py`, `if not q.strip(): return []`).
- 앱 시작 시 인덱스 생성은 try/except로 감싸 실패해도 `logging.exception(...)` 후 진행(`main.py` lifespan) — DB가 아직 안 떴을 때 부팅을 막지 않으려는 의도.
- CORS는 전부 개방하되 메서드는 GET만(`main.py`: `allow_origins=["*"]`, `allow_methods=["GET"]`, `allow_credentials=False`). API가 읽기 전용임을 반영.

## 11. 스택 / 설정 메모

- 프론트: React 19 + Vite 8, `lucide-react` 아이콘, `maplibre-gl`(지도), `cytoscape`(+`cose-bilkent`, `expand-collapse` 플러그인, 그래프). `main.jsx`는 `<StrictMode>`로 감싼다.
- 프론트 lint 설정(`eslint.config.js`): flat config, `dist` 무시, `js.recommended` + `reactHooks.configs.flat.recommended` + `reactRefresh.configs.vite`. 브라우저 globals, JSX 활성.
- 백엔드: FastAPI 0.136 + neo4j 6.2 + uvicorn 0.49 (`backend/requirements.txt`).
