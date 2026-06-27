---
last_mapped_commit: 14e0a78c3e0ab7fc7d960c4cabdf3eab3fc297e6
mapped: 2026-06-27
---

# CONVENTIONS.md — 코드 규약

구현 사실 기록. 도메인 용어 정의는 CONTEXT.md 참조.

---

## React 컴포넌트 패턴

### 파일 구조
- 파일당 1 default export 컴포넌트.
- 해당 파일에서만 쓰는 서브컴포넌트는 별도 파일 없이 같은 파일 안에 로컬 정의.
  - `frontend/src/BibleOverviewView.jsx`: `BookCard`, `GenreSection`, `Testament` 로컬 정의
  - `frontend/src/SidePanel.jsx`: `SectionHeader` 로컬 정의
- 모든 컴포넌트 함수는 `function` 선언식 사용. Arrow function 컴포넌트 미사용(`*.jsx` 전체 검증).
- 들여쓰기: 2-space(`.jsx`/`.js` 전체).

### Props 패턴
- 기본값은 구조분해 파라미터에서 직접 지정:
  ```js
  function SidePanel({ nodeId, onSelectNode = () => {}, onBack = () => {}, canGoBack = false, ... })
  ```
- 콜백 props는 항상 `onXxx` 명명.

### Hooks 패턴
- `useEffect` 비동기 패턴: `AbortController` + catch에서 `e.name === 'AbortError'` 구분으로 stale/경쟁 응답 방지.
- effect 동기 본문에서의 `setState` 금지 — react-hooks v7 규칙. `setTimeout`/async 콜백 안에서만 호출(`frontend/src/useSearch.js` 디바운스 effect 주석에 명시).
- `useCallback(fn, [])` + `useRef` 조합으로 최신 값 읽기 — 참조 안정화로 다른 effect 재실행 방지:
  - `useNodeSelection.js`의 `selectNode`는 `useCallback([], [])`, `selectedNodeRef.current`로 최신 `selectedNode` 읽음 (MapView effect 재실행 → expandPlace fetch abort 버그 방지).
- 커스텀 훅은 `useXxx.js` 별도 파일에 `export function useXxx()`: `frontend/src/useNodeSelection.js`, `frontend/src/useSearch.js`. 관련 state·ref·핸들러를 한 객체로 묶어 반환.

### MapView 모듈 분할 패턴 (`frontend/src/MapView.jsx` + 형제 모듈)
`MapView.jsx`는 React 라이프사이클·effect·DOM만 들고, 맵 로직은 형제 순수/팩토리 모듈로 분리한다(컴포넌트 195줄 유지).

- `frontend/src/mapGeo.js` — **모듈 레벨 순수함수**만 모음. 좌표/지오메트리/라벨 배치 계산:
  - `coreBounds(places)` — 원거리 outlier 제외한 core `LngLatBounds`(중앙값 거리 × 3 임계). 밀집/제외 없음이면 `null`(호출 측 전체 bounds 폴백).
  - `placesToGeoJSON(places)` — 최근접 이웃 반대 방향으로 라벨 anchor/offset 계산(화면 세로 `cos(lat)` 보정).
  - `ringLabels(lat, n)`, `ringPositions(lng, lat, n, R)`, `buildEventGeoJSON`, `buildSpiderGeoJSON`, `easeOutCubic(t)`.
  - 내부 헬퍼 `outwardLabel(ex, ny)` — 화면 8방위 text-anchor + text-offset(commit task-74/75).
- `frontend/src/mapLayers.js` — 맵 정적 구성. `setupMapSources(map)`(GeoJSON source + circle/symbol/fill/line 레이어 일괄 추가), `registerEventHandlers(map, {...})`(클릭·마우스 핸들러 단일 함수로 모음), 모듈 상수 `EMPTY_GEOJSON`, 팝업 HTML 빌더 `placePopupHTML`, XSS 방어 `escapeHtml`.
- `frontend/src/mapRingController.js` — **팩토리-클로저 패턴**으로 가변 애니메이션 상태 캡슐화. `createRingController(map, { expandedPlaceRef, setError })`가 클로저 변수(`animFrame`, `spiderState`, `spiderAnimFrame`, `expandAbortCtrl`, `destroyed`)를 숨기고 `{ collapseRing, collapseSpider, expandPlace, spiderifyPlaces, destroy }`를 반환. React state 아님 — `requestAnimationFrame` 프레임마다 `setData`로 직접 갱신, 리렌더 없음.
  - `expandedPlace = expandedPlaceRef` — 컴포넌트 ref를 컨트롤러와 공유(selection effect가 펼침 상태 판단·`registerEventHandlers` 재클릭 판단).
  - 정리: 컴포넌트 unmount effect cleanup에서 `ring.destroy()` 호출(진행 중 `requestAnimationFrame`/`AbortController` 취소).
- `MapView.jsx`는 맵 라이프사이클 effect(`useEffect([onSelectNode])`)와 데이터/선택 반영 effect(`useEffect([selectedNode, mapLoaded])`)를 분리. `expandPlaceRef`/`expandedPlaceRef` React ref를 두 effect 간 공유 브리지로 활용.

### 상태 관리
- 전역 상태 라이브러리 없음. `App.jsx`에서 props drilling 또는 커스텀 훅(`useNodeSelection`, `useSearch`)으로 전달.
- 뷰는 항상 마운트 상태 유지 — CSS `display: 'block' | 'none'` 토글로 전환(지도 상태 보존 목적, `App.jsx`).

---

## 스타일링 패턴

- CSS-in-JS 라이브러리 없음. 모든 스타일은 인라인 `style={{ ... }}` 객체. `className` 미사용(`*.jsx` 전체 검증).
- 예외: 키프레임 애니메이션은 컴포넌트 내 `<style>{...}</style>` 태그 인라인(`frontend/src/Spinner.jsx`의 `@keyframes spin`). CSS 클래스 셀렉터는 여전히 미사용.
- 글로벌 CSS는 `frontend/src/index.css`(Vite 템플릿 기본 — CSS 변수·`body`·`#root`·기본 타이포 정의). 실제 컴포넌트는 이 변수에 의존하지 않고 전부 인라인.
- 색상 팔레트 단일 출처: `frontend/src/theme.js` — `TYPE_COLOR`, `TYPE_KO`, `TYPE_ORDER`, `typeColor()`, `typeKo()`, `SELECT_HL`.
- hover 스타일: `onMouseEnter`/`onMouseLeave`로 `e.currentTarget.style.background` 직접 조작.
- 글꼴: `fontFamily: 'system-ui, -apple-system, sans-serif'`.
- 모바일 분기: `window.matchMedia(MOBILE_QUERY)` → `isMobile` state → 조건부 인라인 스타일 스프레드(`...(isMobile ? {...} : {...})`).
- 매직넘버 상수는 `frontend/src/constants.js`: `MOBILE_BREAKPOINT = 768`, `SHEET_VH = 55`.
- 로컬 스타일 상수: camelCase (`chipBase`, `verseBoxStyle`, `msgStyle`).

---

## API 통신 패턴

- 단일 fetch 클라이언트: `frontend/src/api.js` — `apiGet(path, { signal })`.
  - non-OK 응답은 `err.status` 속성을 가진 Error로 throw(기존 각 파일의 `Promise.reject(r.status)`와 동일 시맨틱).
  - 요청 취소는 `AbortError`로 그대로 전파 — 호출부가 `e.name === 'AbortError'`로 구분.
  - 환경변수: `import.meta.env.VITE_API_URL`(없으면 `http://localhost:8000`), 모듈에서 `API_BASE`로 export.
- 모든 컴포넌트·훅·`mapRingController.js`는 직접 fetch 없이 `apiGet` 만 사용.

---

## 에러 처리 패턴

### 프론트엔드
- `error` boolean/string state + 조건부 에러 메시지 렌더링.
- fetch catch: `e.name === 'AbortError'`는 early return(무시), 그 외만 `setError`.
- `mapRingController.expandPlace`도 동일 — 링 정보 로드 실패 시 `setError(true)`(무반응 대신 피드백), AbortError·destroyed는 무시.
- 에러 UI: 한국어 메시지, `color: '#dc3545'` 또는 인라인 배너(`rgba(220,53,69,0.95)`).

### 백엔드
- 라우트: `raise HTTPException(status_code=404, detail="Node not found")`.
- 좌표 변환 실패: `try/except (TypeError, ValueError): continue` 패턴.
- JSON 파싱(`traits`) 실패: `except Exception: clean_props["traits"] = []` graceful fallback.
- 앱 시작 인덱스 생성 실패: `lifespan`에서 `except Exception: logging.exception(...)` 후 계속 진행(`backend/app/main.py`).

---

## 데이터 변환 패턴

- `nameKo || name` 폴백 패턴 — 프론트엔드 전역, 백엔드 응답 빌드(`name_ko if name_ko else name`)에서 일관 사용.
- 노드 표시명 추출: `props.get("name") or props.get("title", "")` — `Event`는 `title`을 이름으로 사용.
- `nameKoMissing` boolean 필드: API 응답에 포함(`name_ko is None`), 프론트에서 `nameKo (미번역)` 표시에 사용.
- 연도 표시: `y < 0 ? 'BC ' + (-y) : 'AD ' + y` 패턴(`TimelineView`의 `fmtYear`, `SidePanel` 인라인).
- 노출 불필요 속성 제거:
  ```python
  exclude = {"name", "nameKo", "theographic_id", "aliasesKo"}
  clean_props = {k: v for k, v in props.items() if k not in exclude}
  ```

---

## Python/FastAPI 패턴

### 앱 부트스트랩 (`backend/app/main.py`)
- `app = FastAPI(lifespan=lifespan)` — `@asynccontextmanager` lifespan에서 타입별(`Person/Place/Event/PeopleGroup/Book`) `CREATE INDEX ... IF NOT EXISTS` 실행.
- `CORSMiddleware` 등록: `allow_origins=["*"]`, `allow_credentials=False`, `allow_methods=["GET"]`.
- 라우터는 `app.include_router(...)`로 모듈별 등록(`nodes`, `events`, `search`, `books`).

### 라우터 구조
- 파일당 `router = APIRouter()` 1개.
- 라우트 함수: 동기 `def`(async 없음) — Neo4j는 blocking 드라이버 사용.
- 매 라우트 호출 패턴: `get_driver()` → `with driver.session() as session: ...`.
- 라우트 상한값은 모듈 레벨 상수: `MAX_NEIGHBORS_PER_TYPE`, `NODE_NEIGHBOR_LIMIT`, `SEARCH_LIMIT`.

### DB 패턴 (`backend/app/db.py`)
- 모듈 레벨 `_driver = None` 싱글턴, `get_driver()` lazy init.
- 환경변수: `os.getenv("NEO4J_URI", "bolt://localhost:7687")`, `os.getenv("NEO4J_USER", "neo4j")`, `os.environ.get("NEO4J_PASSWORD")`.
- password 없으면 한국어 메시지로 `RuntimeError` raise.

### Neo4j Cypher 패턴
- `session.run(query, id=node_id)`/`q=q` — 키워드 인수로 파라미터 바인딩($id/$q). 상한값만 f-string으로 쿼리에 삽입(`[0..{NODE_NEIGHBOR_LIMIT}]`, `LIMIT {SEARCH_LIMIT}`).
- `result.single()` — 단일 레코드. 없으면 404.
- `dict(record["n"])` — Neo4j 노드를 Python dict로 변환.
- `labels(n)` 반환받아 `labels[0] if labels else "Unknown"` 로 첫 라벨 추출.
- 라벨 분기(`Person/Event/PeopleGroup/Book/...`)로 서로 다른 Cypher 실행(`get_node_places`).

### 오버레이 패턴 (`backend/app/overlays.py`)
- `functools.lru_cache(maxsize=1)` — 앱 재시작 전까지 JSON 파일 1회만 읽음(`book_events_raw`, `event_verses`). `events.py`의 `_load_approx_book_index`, `_compute_events`도 동일 캐시(Neo4j 쿼리 결과 메모리 보관).
- `_resolve(subpath)` 경로 우선순위: 환경변수 `DATA_DIR`(기본 `/app/data`) → 레포 `data/` 경로(`_REPO_DATA_DIR`).
- 파일 없음/파싱 실패는 `{}` 반환 graceful fallback.
- 추정/낮은권위 데이터는 Neo4j 주입 없이 JSON 오버레이로 유지(ADR-0004).

### 응답 캐싱 패턴
- 이벤트 목록·구절: `JSONResponse(content=..., headers={"Cache-Control": "max-age=300"})`.
- 개요용 책 목록(`/books-overview`): `"Cache-Control": "no-store"`.
- 그 외 라우트: dict/list 직접 반환(FastAPI 자동 JSON 직렬화).

### 스크립트 구조 (`backend/scripts/`)
- 공통 구조: docstring(사용법 포함) → import → 경로 상수(`SCRIPT_DIR`, `OUTPUT_PATH` 등) → 함수 정의 → `def main():` → `if __name__ == "__main__": main()`.
- 외부 데이터: theographic GitHub raw JSON을 `urllib.request`로 fetch(`fetch_json`).
- Neo4j 배치 주입: `UNWIND $rows AS row / MATCH ... / SET` 패턴.
- 멱등 원칙: 이미 값이 있는 항목 스킵, null인 항목 재시도(`backend/scripts/generate_verse_text.py`).
- LLM 생성 스크립트(`generate_person_traits.py`, `generate_book_context.py`, `generate_book_events.py`, `generate_verse_events.py`): `anthropic` 패키지, `claude-haiku-4-5-20251001` 모델, `anthropic.Anthropic(api_key=...)` → `client.messages.create(...)`. API 키는 `ANTHROPIC_API_KEY` 환경변수(없으면 한국어 `RuntimeError`).

---

## 네이밍 규약

| 대상 | 규약 | 예시 |
|------|------|------|
| React 컴포넌트 파일 | PascalCase.jsx | `SidePanel.jsx` |
| React 훅·유틸 파일 | camelCase.js | `useSearch.js`, `api.js`, `constants.js`, `mapGeo.js`, `mapLayers.js`, `mapRingController.js` |
| Python 변수·함수 | snake_case | `get_driver`, `node_id` |
| Python 내부 헬퍼 | `_` prefix | `_load_approx_book_index`, `_resolve`, `_load` |
| Python 경로/상한 상수 | SCREAMING_SNAKE_CASE | `DATA_DIR`, `OUTPUT_PATH`, `SEARCH_LIMIT` |
| JS 모듈 상수 | SCREAMING_SNAKE_CASE | `MOBILE_BREAKPOINT`, `TYPE_COLOR`, `EMPTY_GEOJSON` |
| 콜백 props | `onXxx` | `onSelectNode`, `onBack` |
| 노드 타입 리터럴 | PascalCase 문자열 | `'Person'`, `'Place'`, `'Event'` |
| 로컬 스타일 상수 | camelCase | `chipBase`, `verseBoxStyle` |
