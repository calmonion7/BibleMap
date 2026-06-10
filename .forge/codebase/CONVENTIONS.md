---
last_mapped_commit: 60962d0693f3bfaf4b8d24ce6f97d7b392770d85
mapped: 2026-06-11
---

# CONVENTIONS

BibleMap의 실제 코드 스타일·네이밍·패턴·에러 처리 규약. 백엔드(Python/FastAPI)와 프론트엔드(React)로 나눠 기술한다. 모든 항목은 현재 소스 기준 구현 사실이다.

## 백엔드 (Python / FastAPI)

### 라우트 구조

- 라우터는 `backend/app/routes/` 아래 도메인별 파일로 분리한다: `nodes.py`, `events.py`, `search.py`.
- 각 파일은 모듈 최상단에서 `router = APIRouter()`를 만들고, 핸들러에 `@router.get(...)` 데코레이터를 붙인다. `APIRouter`에는 `prefix`/`tags`를 주지 않고 경로 전체를 데코레이터에 직접 쓴다(예: `@router.get("/node/{node_id}/places")`).
- `backend/app/main.py`가 세 라우터를 import 해 `app.include_router(...)`로 등록한다.
- 등록되는 엔드포인트:
  - `backend/app/routes/nodes.py`: `GET /node/{node_id}/places`, `GET /node/{node_id}/neighbors/grouped`, `GET /node/{node_id}` (구체 경로를 일반 경로보다 먼저 선언해 라우팅 충돌을 피한다).
  - `backend/app/routes/events.py`: `GET /events`.
  - `backend/app/routes/search.py`: `GET /search`.
- 노출하는 메서드는 GET 뿐이다. CORS 미들웨어도 `allow_methods=["GET"]`로 제한한다(`backend/app/main.py`).
- 앱 기동/종료 훅은 `@asynccontextmanager`로 만든 `lifespan` 함수를 `FastAPI(lifespan=lifespan)`에 넘겨 처리한다(`backend/app/main.py`). lifespan은 시작 시 4개 라벨(`Person`, `Place`, `Event`, `PeopleGroup`)에 `theographic_id` 인덱스를 `CREATE INDEX ... IF NOT EXISTS`로 생성한다.

### 네이밍

- 함수/변수: `snake_case` (예: `get_node_places`, `get_driver`, `places_result`, `node_id_val`).
- 핸들러 함수 이름은 `get_<리소스>` 형태(예: `get_events`, `get_node`, `get_node_neighbors_grouped`). 예외: `search.py`의 핸들러는 `search`.
- 모듈 상수: `UPPER_SNAKE_CASE`. 매직넘버는 모듈 최상단에 상수로 끌어올린다:
  - `SEARCH_LIMIT = 20` (`backend/app/routes/search.py`)
  - `MAX_NEIGHBORS_PER_TYPE = 30`, `NODE_NEIGHBOR_LIMIT = 50` (`backend/app/routes/nodes.py`)
  - 적재 스크립트: `BATCH_NODE = 500`, `BATCH_REL = 1000` (`backend/scripts/load_theographic.py`).
- 외부 JSON 필드명은 그래프 속성으로 그대로 옮길 때 원본 camelCase를 유지한다(예: `theographic_id`만 snake, 나머지 `displayTitle`, `featureSubType`, `startDate`, `sortKey`, `nameKo`, `aliasesKo`는 camelCase).
- API 응답 JSON 키는 camelCase(`nameKo`, `nameKoMissing`, `startDate`, `sortKey`, `isPrimary`), 노드 식별자만 `id`.

### 환경변수 읽기 패턴 (중요 — 일관 규약 아님)

DB 접속 정보는 환경변수에서 읽되, 변수마다 처리가 다르다. `backend/app/db.py`가 정본이다:

- `NEO4J_URI`: `os.getenv("NEO4J_URI", "bolt://localhost:7687")` — 기본값 있음.
- `NEO4J_USER`: `os.getenv("NEO4J_USER", "neo4j")` — 기본값 있음.
- `NEO4J_PASSWORD`: `os.environ.get("NEO4J_PASSWORD")`로 **기본값 없이** 읽고, falsy면 `raise RuntimeError("NEO4J_PASSWORD 환경변수가 설정되지 않았습니다")`. 즉 fail-fast이며 비밀번호 기본값은 존재하지 않는다.

같은 패턴이 적재 스크립트에도 복제돼 있다:

- `backend/scripts/inject_ko_names.py`: `os.getenv`로 URI/USER에 기본값, `NEO4J_PASSWORD`는 기본값 없이 읽고 없으면 `RuntimeError`.
- `backend/scripts/load_theographic.py`: `os.environ.get`으로 URI/USER에 기본값, `NEO4J_PASSWORD`는 기본값 없이 읽고 없으면 `RuntimeError`.

오케스트레이션 레이어도 비밀번호를 강제한다: `docker-compose.yml`은 `${NEO4J_PASSWORD:?NEO4J_PASSWORD must be set}`로 미설정 시 compose가 실패하고, `NEO4J_AUTH`는 `neo4j/${NEO4J_PASSWORD}`로 파생한다. 비밀번호는 `.env`에만 두며(`.env`는 `.gitignore` 대상), `.env.example`은 자리표시자만 담는다.

### DB 접근 패턴 (Neo4j)

- 단일 드라이버를 모듈 전역에 지연 초기화한다: `backend/app/db.py`의 `get_driver()`가 `global _driver`를 캐싱한다. 라우트는 매 요청 `driver = get_driver()`로 받는다.
- 세션은 항상 `with driver.session() as session:` 컨텍스트 매니저로 연다.
- 쿼리는 `session.run(cypher, 파라미터)`. **사용자/외부 입력은 Cypher 파라미터(`$id`, `$q`)로 바인딩**한다(인젝션 방지). 단, 코드 내부 상수인 LIMIT 값은 f-string으로 쿼리에 박는다(예: `LIMIT {SEARCH_LIMIT}`, `LIMIT {NODE_NEIGHBOR_LIMIT}`). 라벨 보간(`f"...:{label}..."`)도 내부 상수 리스트에서만 쓴다.
- 단건 조회는 `result.single()`, 다건은 `for record in result:`로 순회한다.
- 노드 속성은 `props = dict(node)`로 변환 후 `props.get("키", 기본값)`으로 꺼낸다.

### 한국어 이름(nameKo) 정규화 관용구

응답 직렬화 시 한국어 이름 폴백·결측 표시 패턴이 라우트 전반에 반복된다:

- 표시 이름: `name = props.get("name") or props.get("title", "")` (Person/Place는 `name`, Event는 `title`).
- `nameKo` 폴백: 값이 없으면 영문 `name`으로 폴백(예: `"nameKo": name_ko if name_ko else name`).
- 결측 플래그: `"nameKoMissing": name_ko is None` (`nodes.py`, `search.py` 일부 응답). `neighbors/grouped`는 `m_name_ko if m_name_ko is not None else m_name`로 `is not None`을 명시.
- 좌표 파싱은 견고하게: `float(props.get("latitude", 0))`를 `try/except (TypeError, ValueError)`로 감싸고 실패 시 `continue`로 해당 장소를 건너뛴다(`nodes.py` `get_node_places`). `events.py`도 `float(props.get("sortKey", 0))`로 캐스팅.
- 중복 제거는 `seen = set()` + `theographic_id` 기준(`nodes.py`).

### 에러 처리 (백엔드)

- 라우트 레벨: 리소스 없음은 `from fastapi import HTTPException` 후 `raise HTTPException(status_code=404, detail="Node not found")` (`nodes.py`의 `get_node`, `get_node_places`).
- 빈 입력은 예외 대신 빈 결과 반환: `search`는 `if not q.strip(): return []`.
- 설정 오류(비밀번호 미설정)는 `RuntimeError`로 즉시 중단(fail-fast). try/except로 감싸지 않는다.
- 기동 시 비치명적 작업은 광범위 catch + 로깅 후 계속: lifespan의 인덱스 생성은 `except Exception:` 안에서 `logging.exception("Neo4j 인덱스 생성 실패 — 인덱스 없이 계속 진행합니다")`로 삼키고 `yield`로 진행한다(`backend/app/main.py`). 인덱스 실패가 앱 기동을 막지 않는다.
- 응답 캐시 제어가 필요한 엔드포인트는 `JSONResponse(content=..., headers={"Cache-Control": "no-store"})`를 직접 반환한다(`events.py`).

### 적재 스크립트 관례 (`backend/scripts/`)

- 진입점은 `if __name__ == "__main__":` 블록 또는 `main()` 함수(`inject_ko_names.py`는 `main()`, `load_theographic.py`는 모듈 하단 인라인).
- 대량 쓰기는 `UNWIND $rows AS row ... MERGE`로 배치 처리하고, `run_batched(session, cypher, rows, batch_size, param_key="rows")` 헬퍼로 `batch_size`씩 끊어 보낸다(`load_theographic.py`).
- `MERGE`로 멱등 적재(재실행해도 중복 노드/관계 안 생김).
- 진행 상황은 `print(...)`로 출력(스크립트 한정, 라우트 코드에서는 `print` 미사용).
- 드라이버는 `try/finally` 또는 `with` 블록 끝에서 `driver.close()`로 정리.
- 양방향 관계 쌍은 `tuple(sorted([a_id, b_id]))` 키 + `seen` set으로 중복 제거(`load_sibling_rels`, `load_partner_rels`).

### 의존성·런타임

- `backend/requirements.txt`는 정확한 버전 핀: `fastapi==0.136.3`, `neo4j==6.2.0`, `uvicorn==0.49.0`. (테스트 라이브러리 없음.)
- 컨테이너는 `python:3.12-slim` 기반, `uvicorn app.main:app --host 0.0.0.0 --port 8000`으로 기동(`backend/Dockerfile`).

## 프론트엔드 (React)

### 컴포넌트 구조

- 컴포넌트는 `frontend/src/` 직속 단일 `.jsx` 파일 1개 = 컴포넌트 1개: `App.jsx`, `MapView.jsx`, `TimelineView.jsx`, `GraphView.jsx`, `SidePanel.jsx`. 별도 디렉터리 구조나 배럴 파일 없음.
- 모두 **함수형 컴포넌트 + 훅**. 클래스 컴포넌트 없음.
- export 방식이 혼재한다(통일돼 있지 않음):
  - `export default function MapView(...)` / `export default function GraphView(...)` — 인라인 default export.
  - `function App() {...}` 후 파일 끝에서 `export default App` — `App.jsx`, `SidePanel.jsx`, `TimelineView.jsx`.
- 진입점은 `frontend/src/main.jsx`: `createRoot(...).render(<StrictMode><App /></StrictMode>)`.
- 상태는 컴포넌트 로컬 `useState`만 사용. Redux/Context 등 전역 상태 라이브러리 없음. `selectedNode`(노드 id 문자열) / `onSelectNode`(setter)를 prop으로 위에서 아래로 내려 공유한다.

### 네이밍

- 컴포넌트: `PascalCase` (`MapView`). 파일명도 컴포넌트명과 동일한 PascalCase `.jsx`.
- 함수/변수/핸들러: `camelCase`. 이벤트 핸들러는 `handle<동작>` 접두(`handleTabClick`, `handleSearch`, `handleSelectResult`).
- 모듈 상수: `UPPER_SNAKE_CASE` (`API_BASE`/`API_URL`, `EMPTY_GEOJSON`, `DEFAULT_NODE`, `NAV_H`, `BATCH_*` 없음). 한국어 라벨 매핑 객체도 상수(`REL_KO`, `TYPE_COLOR`, `TYPE_LABEL_KO`, `TABS`).
- prop 콜백은 `on<이벤트>` 접두(`onSelectNode`).

### API 호출 / fetch 패턴

- API 베이스 URL은 매 컴포넌트 상단에서 환경변수 + 폴백으로 정의: `const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'` (`App.jsx`는 변수명만 `API_BASE`). 프로덕션은 `frontend/.env.production`의 `VITE_API_URL=/api` (nginx가 `/api/`를 백엔드로 프록시 — `nginx/nginx.conf`).
- 표준 라이브러리 `fetch`만 사용(axios 등 없음). 두 스타일 혼재:
  - `async/await` + `try/catch`: `App.jsx`의 `handleSearch`는 `await fetch(...)` 후 `catch { setSearchResults([]) }`로 실패 시 빈 배열.
  - 프라미스 체인 + `.catch()`: `useEffect` 안의 데이터 로딩은 `fetch(...).then(r => r.json()).then(setState).catch(() => {})` 형태(`TimelineView.jsx`, `MapView.jsx`, `GraphView.jsx`).
- **에러는 대체로 조용히 삼킨다**: 대부분 `.catch(() => {})`로 무시. 사용자 메시지를 띄우는 곳은 `SidePanel.jsx`뿐 — `error` 상태를 두고 `setError(String(e))` 후 `오류: {error}` 렌더.
- HTTP 상태 검증은 `SidePanel.jsx`만 명시적으로 함: `.then(r => r.ok ? r.json() : Promise.reject(r.status))`. 나머지는 `r.json()` 바로 호출.
- 로딩/에러 상태 분기(SidePanel): `if (!nodeId) return ...` → `if (loading || !node) return <p>로딩 중...</p>` → `if (error) return <p>오류: {error}</p>` 순서의 가드 패턴.
- 경합/누수 방지:
  - 동시 다발 호출은 `Promise.all([...])`로 묶음(`GraphView.jsx`).
  - `MapView.jsx`는 `AbortController`(`ctrl.signal`)로 effect cleanup 시 `ctrl.abort()` + `mapRef.current === map` 가드로 stale 응답 차단.

### prop 관례

- props는 구조 분해로 받음: `function MapView({ onSelectNode, selectedNode })`.
- 기본값은 분해 시 지정: `function SidePanel({ nodeId, onSelectNode = () => {} })` (콜백 미전달 대비 no-op 기본값).
- PropTypes / TypeScript 미사용. `@types/react`는 devDependency에 있으나 소스는 순수 JSX(`.jsx`).

### 스타일링

- **인라인 스타일(`style={{...}}`) 전면 사용**. CSS Module / styled-components 없음. 공유 CSS는 `frontend/src/index.css`, `frontend/src/App.css`에만.
- 색상은 하드코딩 헥스(`#1a1a2e`, `#7c9cfc`, `#4a90d9` 등). 디자인 토큰/테마 시스템 없음. 타입별 색은 상수 맵으로 분리(`TYPE_COLOR` in `GraphView.jsx`).
- 주석은 한국어, 섹션 구분용(예: `{/* 내비게이션 바 — 지도 위에 플로팅 */}`).

### 한국어 UI 관례

- 한국어 라벨 매핑을 상수 객체로 분리: 관계명 `REL_KO`(`SidePanel.jsx`), 노드 타입 `TYPE_LABEL_KO`(`GraphView.jsx`).
- 미번역 노출 규약: 백엔드 `nameKoMissing`이 true면 `name + ' (미번역)'`, 아니면 `nameKo + ' (' + name + ')'` (`SidePanel.jsx`). 관계 라벨은 `REL_KO[n.relation] || n.relation`로 폴백.
- 연·월 표기는 `parseYear`로 BC/AD 변환(`TimelineView.jsx`): `-`로 시작하면 `BC`, 아니면 `AD`, 선행 0 제거(`replace(/^0+/, '')`).

### 외부 라이브러리 통합 (지도/그래프)

- 지도: `maplibre-gl`. `useRef`로 map/container/popup 인스턴스를 보관하고, `useEffect`에서 `new maplibregl.Map(...)` 생성 후 cleanup에서 `map.remove()` + ref 초기화(`MapView.jsx`).
- 그래프: `cytoscape` + 플러그인(`cytoscape-cose-bilkent`, `cytoscape-expand-collapse`)을 모듈 최상단 `cytoscape.use(...)`로 등록. effect cleanup에서 `cy.destroy()`(`GraphView.jsx`).
- 아이콘: `lucide-react`.
- 명령형 라이브러리 인스턴스는 항상 `useRef`에 담고 effect cleanup에서 명시적으로 해제하는 패턴을 따른다.

### 린트 / 빌드

- ESLint flat config(`frontend/eslint.config.js`): `@eslint/js` recommended + `eslint-plugin-react-hooks` + `eslint-plugin-react-refresh`, `dist` 무시. 스크립트는 `npm run lint`(`eslint .`).
- 빌드/실행: Vite(`frontend/vite.config.js`, `@vitejs/plugin-react`만 등록). `npm run dev`/`build`/`preview`(`frontend/package.json`).
- React 19, 의존성은 caret(`^`) 범위.
