---
last_mapped_commit: 7a1ef362b1fb247b09edeeaa1380e6449fce5721
mapped: 2026-06-20
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
- 모든 컴포넌트 함수는 `function` 선언식 사용. Arrow function 컴포넌트 미사용.

### Props 패턴
- 기본값은 구조분해 파라미터에서 직접 지정:
  ```js
  function SidePanel({ nodeId, onSelectNode = () => {}, onBack = () => {}, canGoBack = false })
  ```
- 콜백 props는 항상 `onXxx` 명명.

### Hooks 패턴
- `useState` 복합 상태: 관련 상태를 하나의 객체로 묶음.
  ```js
  const [state, setState] = useState({ id: null, node: null, error: null })
  ```
  파생 판별은 필드 비교로: `state.id === nodeId`.
- `useEffect` 비동기 패턴: `cancelled` boolean 플래그로 stale 응답 방지. fetch에는 `AbortController.signal` 전달.
- `useCallback(fn, [])` + `useRef` 조합으로 최신 값 읽기:
  - `selectNode`는 `useCallback([], [])` (MapView effect 재실행 방지)
  - `selectedNodeRef.current`로 최신 `selectedNode` 읽음
- `useMemo`는 순수 데이터 변환에만 사용 (이벤트 그룹핑, 필터링).
- 커스텀 훅은 `useXxx.js` 별도 파일: `frontend/src/useNodeSelection.js`, `frontend/src/useSearch.js`.

### MapView 특수 패턴 (`frontend/src/MapView.jsx`)
- `useEffect([onSelectNode])` 1개로 맵 전체 라이프사이클 관리 (초기화·이벤트 바인딩·cleanup).
- 맵 내부 애니메이션 상태(`animFrame`, `spiderState`)는 React state가 아닌 effect 클로저 변수로 관리 — 리렌더 없이 프레임마다 업데이트.
- `expandPlaceRef`, `expandedPlaceRef` — React ref를 두 useEffect 간 공유 브리지로 활용.
- 데이터 변환 함수는 모듈 레벨 순수함수로 정의: `placesToGeoJSON`, `buildEventGeoJSON`, `buildSpiderGeoJSON`.

### 상태 관리
- 전역 상태 라이브러리 없음. `App.jsx`에서 props drilling 또는 커스텀 훅으로 전달.
- 뷰는 항상 마운트 상태 유지 — CSS `display` 토글로 전환 (지도 상태 보존 목적).

---

## 스타일링 패턴

- CSS-in-JS 라이브러리 없음. 모든 스타일은 인라인 `style={{ ... }}` 객체.
- 글로벌 CSS는 `frontend/src/index.css` (CSS 변수 정의), 실제 컴포넌트는 전부 인라인.
- 색상 팔레트 단일 출처: `frontend/src/theme.js` — `TYPE_COLOR`, `TYPE_KO`, `typeColor()`, `typeKo()`, `SELECT_HL`.
- hover 스타일: `onMouseEnter`/`onMouseLeave`로 `e.currentTarget.style.background` 직접 조작. CSS 클래스/hover 선택자 미사용.
- 글꼴: `fontFamily: 'system-ui, -apple-system, sans-serif'`.
- 모바일 분기: `window.matchMedia('(max-width: 768px)')` → `isMobile` state → 조건부 인라인 스타일 스프레드.
- 로컬 스타일 상수: camelCase (`chipBase`, `verseBoxStyle`).

---

## API 통신 패턴

- 단일 fetch 클라이언트: `frontend/src/api.js` — `apiGet(path, { signal })`.
  - non-OK 응답은 `err.status` 속성을 가진 Error로 throw.
  - 환경변수: `import.meta.env.VITE_API_URL` (없으면 `http://localhost:8000`).
- 모든 컴포넌트는 직접 fetch 없이 `apiGet` 만 사용.

---

## 에러 처리 패턴

### 프론트엔드
- `error` boolean/string state + 조건부 에러 메시지 렌더링.
- fetch catch: `e?.name !== 'AbortError'` 체크 후 `setError`.
- 에러 UI: 한국어 메시지, `color: '#dc3545'` 인라인 스타일.

### 백엔드
- 라우트: `raise HTTPException(status_code=404, detail="Node not found")`.
- 좌표 변환 실패: `try/except (TypeError, ValueError): continue` 패턴.
- JSON 파싱(`traits`) 실패: `except Exception: clean_props["traits"] = []` graceful fallback.

---

## 데이터 변환 패턴

- `nameKo || name` 폴백 패턴 — 프론트엔드 전역에서 일관 사용.
- `nameKoMissing` boolean 필드: API 응답에 포함, 프론트에서 `nameKo (미번역)` 표시에 사용.
- 연도 표시: `y < 0 ? 'BC ' + (-y) : 'AD ' + y` 패턴 (`TimelineView`의 `fmtYear`, `SidePanel` 인라인).
- 노출 불필요 속성 제거:
  ```python
  exclude = {"name", "nameKo", "theographic_id", "aliasesKo"}
  clean_props = {k: v for k, v in props.items() if k not in exclude}
  ```

---

## Python/FastAPI 패턴

### 라우터 구조
- 파일당 `router = APIRouter()` 1개.
- `backend/app/main.py`에서 `app.include_router(router)` 등록.
- 라우트 함수: 동기 `def` (async 없음) — Neo4j는 blocking 드라이버 사용.
- 매 라우트 호출 패턴: `get_driver()` → `with driver.session() as session: ...`.

### DB 패턴 (`backend/app/db.py`)
- 모듈 레벨 `_driver = None` 싱글턴, `get_driver()` lazy init.
- 환경변수: `os.getenv("NEO4J_URI", "bolt://localhost:7687")`, `os.environ.get("NEO4J_PASSWORD")`.
- password 없으면 `RuntimeError` raise.

### Neo4j Cypher 패턴
- `session.run(query, id=node_id)` — 키워드 인수로 파라미터 바인딩.
- `result.single()` — 단일 레코드 반환.
- `dict(record["n"])` — Neo4j 노드를 Python dict로 변환.
- `labels(n)` 반환받아 `labels[0]` 로 첫 라벨 추출.

### 오버레이 패턴 (`backend/app/overlays.py`)
- `functools.lru_cache(maxsize=1)` — 앱 재시작 전까지 JSON 파일 1회만 읽음.
- `DATA_DIR` 우선순위: 환경변수 `DATA_DIR` → 레포 `data/` 경로.
- 추정/낮은권위 데이터는 Neo4j 주입 없이 JSON 오버레이로 유지 (ADR-0004).

### 응답 캐싱 패턴
- 이벤트 목록: `JSONResponse(content=..., headers={"Cache-Control": "max-age=300"})`.
- 추정 데이터 포함 응답: `"Cache-Control": "no-store"`.
- 일반 라우트: dict 직접 반환 (FastAPI 자동 JSON 직렬화).

### 스크립트 구조 (`backend/scripts/`)
- 공통 구조: 상수 정의 → 함수 정의 → `def main():` → `if __name__ == "__main__": main()`.
- Neo4j 배치 주입: `UNWIND $rows AS row / MATCH ... / SET` 패턴.
- 멱등 원칙: 이미 값이 있는 항목 스킵, null인 항목 재시도 (`backend/scripts/generate_verse_text.py`).
- LLM 생성 스크립트 (`backend/scripts/generate_person_traits.py`): `anthropic` 패키지, `claude-haiku-4-5-20251001` 모델, `client.messages.create(...)`.

---

## 네이밍 규약

| 대상 | 규약 | 예시 |
|------|------|------|
| React 컴포넌트 파일 | PascalCase.jsx | `SidePanel.jsx` |
| React 훅·유틸 파일 | camelCase.js | `useSearch.js`, `api.js` |
| Python 변수·함수 | snake_case | `get_driver`, `node_id` |
| Python 내부 헬퍼 | `_` prefix | `_load_approx_book_index` |
| Python 경로 상수 | SCREAMING_SNAKE_CASE | `DATA_DIR`, `OUTPUT_PATH` |
| 콜백 props | `onXxx` | `onSelectNode`, `onBack` |
| 노드 타입 리터럴 | PascalCase 문자열 | `'Person'`, `'Place'`, `'Event'` |
| 로컬 스타일 상수 | camelCase | `chipBase`, `verseBoxStyle` |
