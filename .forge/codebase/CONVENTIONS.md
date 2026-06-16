---
last_mapped_commit: e160d65cf9c7d0b54c8d9fc2d031639a712bfb86
mapped: 2026-06-16
---

# CONVENTIONS

BibleMap 코드베이스의 코드 스타일·네이밍·구조·에러 처리 규약을 정리한다.
프론트엔드(React + MapLibre, `frontend/`)와 백엔드(FastAPI + Neo4j, `backend/`)로 나뉜다.

---

## 1. 언어 · 주석

- 코드 식별자(변수·함수·라우트)는 영어, **주석·문자열·UI 라벨은 한국어**가 기본이다.
  - 프론트 주석 예: `frontend/src/App.jsx:14` `// 모바일(좁은 뷰포트) 분기 …`
  - 백엔드 docstring 예: `backend/app/routes/events.py:37` `"""타임라인 사건 목록. …"""`
- 주석은 "왜"를 적는다. 특히 과거 버그·회고를 인라인으로 남긴다.
  - 예: `frontend/src/MapView.jsx:408` `// … task 15에서 어긋났던 지점`
  - 예: `frontend/src/theme.js:1-3` 단일 팔레트로 통일한 이유(GraphView 색 충돌)를 주석으로 보존.
- 사용자에게 보이는 모든 문자열(에러 배너, placeholder, 빈 상태)은 한국어.
  - 예: `frontend/src/MapView.jsx:466` `장소를 불러오지 못했습니다`, `frontend/src/App.jsx:203` `placeholder="검색..."`

---

## 2. 프론트엔드 규약 (`frontend/src/`)

### 2.1 스택 · 모듈 형식

- React 19 + Vite. ESM(`"type": "module"`), 빌드 도구는 Vite 8 (`frontend/package.json`).
- 컴포넌트는 한 파일에 하나, 파일명 = 컴포넌트명(PascalCase + `.jsx`): `App.jsx`, `MapView.jsx`, `SidePanel.jsx`, `TimelineView.jsx`.
- 순수 유틸 모듈은 camelCase `.js`: `api.js`, `theme.js`, `getbible.js`, `convexHull.js`.
- 엔트리: `frontend/src/main.jsx` — `<StrictMode>`로 `App`을 마운트.
- export 스타일은 혼재(허용): 컴포넌트는 `export default function …`(MapView, TimelineView) 또는 함수 선언 후 하단 `export default App`(App, SidePanel). 유틸은 named export.

### 2.2 타입 색 팔레트 — `frontend/src/theme.js` 단일 출처

- **노드 타입 → 색·한글 라벨은 반드시 `frontend/src/theme.js`에서 import한다.** 컴포넌트에 색 상수를 다시 정의하지 않는다.
- 제공 export: `TYPE_COLOR`(타입→hex), `TYPE_KO`(타입→한글), `TYPE_ORDER`(표시 순서 배열), `typeColor(label)`/`typeKo(label)`(fallback 포함 헬퍼), `SELECT_HL`(선택 하이라이트 배경).
- 과거 `App.jsx`·`SidePanel.jsx`·`GraphView.jsx`가 색을 각자 정의해 충돌했던 것을 이 파일 하나로 통일했다(파일 상단 주석 참조). 새 컴포넌트도 이 규약을 따른다.
- 실제 import 예: `App.jsx:6`, `SidePanel.jsx:2`, `TimelineView.jsx:3`(`SELECT_HL`만 사용).
- 단, 도메인 고정색(타입과 무관한 단일 색)은 컴포넌트 로컬 상수로 둔다. 예: `TimelineView.jsx:7` `const BOOK_COLOR = '#a78bfa'`, `MapView.jsx`의 hull(`#f97316`)·ring(`#9b59b6`) 색 리터럴.

### 2.3 스타일링

- **인라인 `style={{}}` 객체 전용.** CSS Module·styled-components·className 기반 스타일 없음.
- 전역 CSS는 `frontend/src/index.css` 하나뿐(폰트·다크모드 변수·`#root` 크기). 컴포넌트는 이를 거의 쓰지 않고 인라인으로 직접 지정.
- 색은 hex 또는 `rgba(...)` 리터럴. 반복되는 UI 색(예: `#1a1a2e` 진한 텍스트, `#7c8db0` 보조 텍스트, `#eef0f5` 옅은 배경)이 인라인으로 흩어져 있음(상수화돼 있지 않음).
- 레이아웃 상수는 컴포넌트 상단 const로: `App.jsx`의 `NAV_H = 48`, `SHEET_VH = 55`, `MOBILE_QUERY`. 프론트 시트 높이와 지도 패딩처럼 두 곳이 맞물리는 값은 주석으로 일치 요구를 명시(`App.jsx:16` ↔ `MapView.jsx:411`).

### 2.4 상태 · 이펙트 패턴 (react-hooks v7 준수)

- `useState`/`useEffect`/`useRef`/`useCallback`만 사용. 외부 상태 라이브러리 없음. 데이터 패칭 라이브러리 없음(직접 `fetch`).
- **effect 동기 본문에서 `setState` 금지** — `setTimeout`/`async` 콜백 안에서만 호출(eslint react-hooks v7 규칙). 명시 주석: `App.jsx:58`, `SidePanel.jsx:84`.
- **경쟁 조건(race) 방어가 일관된 규약:**
  - 비동기 결과를 `nodeId`/`eventId` 등 식별자로 묶어 저장하고, 렌더 시 현재 id와 대조해 stale 응답을 무시한다. 예: `SidePanel.jsx:85` `{ id, node, error }`, `TimelineView.jsx:37` `eventVerses { id, data }`, `openEventRef`(`TimelineView.jsx:42`).
  - `AbortController`로 직전 요청 취소. 검색 디바운스(`App.jsx:62`), `/places` fetch(`MapView.jsx:369`), 링 펼침(`MapView.jsx:109`).
  - cleanup 플래그(`let cancelled = false`)로 unmount 후 setState 방지: `SidePanel.jsx:93`, `:110`.
  - `useCallback([])`로 콜백 참조를 안정화해 하위 effect 재실행을 막고, 최신값은 ref로 읽는다: `App.jsx:109` `selectNode` + `selectedNodeRef`.
- 디바운스는 250ms(`App.jsx:63`), 자동 펼침 폴백 타이머 700ms(`MapView.jsx:430`), MapLibre 링 애니메이션 400ms / `easeOutCubic`(`MapView.jsx:84`).
- MapLibre처럼 명령형(imperative) 라이브러리는 `useRef`에 map 인스턴스를 담고, React state가 아닌 클로저 지역 변수로 애니메이션 프레임을 관리(`MapView.jsx:52` `// 애니메이션 상태 (React state 아님 …)`).

### 2.5 API 호출

- 모든 백엔드 fetch는 `frontend/src/api.js`의 `apiGet(path, { signal })`를 거친다. 단일 베이스 URL(`API_BASE`), 비-OK 응답은 `throw res.status`(숫자 reject), `AbortError`는 그대로 전파.
- 베이스 URL은 빌드타임 env: `import.meta.env.VITE_API_URL || 'http://localhost:8000'`. 프로덕션은 `frontend/.env.production`의 `VITE_API_URL=/api`로 nginx 프록시를 탄다.
- 예외: 외부 한국어 성경 API는 `frontend/src/getbible.js`의 `fetchChapter(bookOrder, chapter)`로 직접 `fetch`(모듈 레벨 `Map` 캐시로 동일 장 재요청 방지). `apiGet`을 쓰지 않는 유일한 fetch 경로.

### 2.6 에러 · 로딩 · 빈 상태 (프론트)

- 컴포넌트 단위로 `error`(boolean) state를 두고, 실패 시 한국어 인라인 메시지/배너 렌더. 예외 객체를 화면에 직접 노출하지 않음(`SidePanel`만 `(...)`에 status 코드 표시, `SidePanel.jsx:126`).
- 로딩은 별도 state로 두기보다 데이터 유무로 파생하는 경우가 많음(`SidePanel.jsx:117` `ready = state.id === nodeId`).
- 키보드 접근성: 검색 드롭다운은 ArrowUp/Down/Enter/Escape 처리(`App.jsx:147`), `aria-label` 부여(`App.jsx:214`).

---

## 3. 백엔드 규약 (`backend/`)

### 3.1 구조 · 라우트 등록

- FastAPI 앱 패키지 `backend/app/`. 엔트리 `backend/app/main.py` — `app = FastAPI(lifespan=…)` 생성, CORS 미들웨어(`allow_origins=["*"]`, `allow_methods=["GET"]`), 그리고 라우터 4개를 `include_router`로 등록.
- **라우트는 도메인별 모듈로 분리**, 각 모듈이 자체 `router = APIRouter()`를 노출: `backend/app/routes/nodes.py`(`/node/...`), `events.py`(`/events`, `/event/{id}/verses`), `search.py`(`/search`), `books.py`(`/books`).
  - `backend/app/routes/__init__.py`는 빈 파일(패키지 마커). 라우터 모듈은 `main.py`에서 직접 import.
- 라우트 데코레이터는 `@router.get("/path")`, 핸들러는 평범한 `def`(동기 함수, async 아님). 경로 파라미터는 `{node_id}` → 함수 인자 `node_id: str`. 쿼리 파라미터는 `q: str = Query("")`.
- DB 의존성 주입(FastAPI `Depends`) 없음 — 각 핸들러가 `get_driver()`를 직접 호출.
- Pydantic 응답 모델 없음 — 핸들러가 dict/list를 그대로 반환(FastAPI가 직렬화).

### 3.2 Neo4j 접근 패턴

- 드라이버는 `backend/app/db.py`의 `get_driver()` 싱글톤(모듈 전역 `_driver`, lazy 초기화). 연결 정보는 env(`NEO4J_URI`/`NEO4J_USER`/`NEO4J_PASSWORD`), 비번 미설정 시 `RuntimeError` raise.
- 핸들러마다 `with driver.session() as session:` 블록 안에서 `session.run(cypher, params)`. 파라미터는 키워드(`id=node_id`) 또는 dict.
- 노드 식별자는 항상 `theographic_id` 프로퍼티로 매칭(`MATCH (n {theographic_id: $id})`). 내부 Neo4j id는 노출하지 않는다.
- Cypher는 트리플쿼트 멀티라인 문자열. **사용자 입력은 항상 `$param`으로 바인딩**(인젝션 방지). 상수 LIMIT만 f-string으로 삽입(`nodes.py:157` `LIMIT {NODE_NEIGHBOR_LIMIT}`, `search.py:27`).
- 응답 매핑 공통 관용구: `props = dict(node)` → `props.get(...)`. `name` 폴백은 `props.get("name") or props.get("title", "")`(Event는 `title` 필드). `nameKo` 미존재 시 영문 `name`으로 폴백하고, 누락 여부를 `nameKoMissing: name_ko is None`로 함께 반환(`nodes.py:170`, `search.py`).
- 제한 상수는 모듈 상단 대문자 const: `nodes.py:6` `MAX_NEIGHBORS_PER_TYPE = 30`, `NODE_NEIGHBOR_LIMIT = 50`, `search.py:6` `SEARCH_LIMIT = 20`.

### 3.3 정적 데이터 오버레이 (`data/`)

- DB에 없는 보조 데이터(추정 연도, 사건 구절)는 `data/<topic>/*.json`에 두고 라우트가 읽어 합친다.
- 로드는 `@functools.lru_cache(maxsize=1)`로 프로세스당 1회 캐시: `books.py:25` `_load_approx()`, `events.py:23` `_load_event_verses()`.
- **경로 폴백 규약**: `DATA_DIR`(기본 `/app/data`, docker 볼륨) → 레포 상대경로(`data/`) 순으로 후보 리스트를 순회. 어느 후보도 못 읽으면 빈 dict 폴백. docker/비-docker 양쪽에서 동작(`books.py:19-35`, `events.py:17-33`).
- 자주 바뀌는 응답은 `JSONResponse(content=…, headers={"Cache-Control": "no-store"})`로 캐싱 방지(`/events`, `/event/{id}/verses`, `/books`).

### 3.4 에러 처리 (백엔드)

- 노드 미존재는 `raise HTTPException(status_code=404, detail="Node not found")` (`nodes.py:19`, `:145`).
- 파일·JSON 실패는 폴백으로 흡수(빈 dict/배열). 예외를 클라이언트에 전파하지 않는 데이터 오버레이 경로와 대비된다.
- 앱 시작 시 인덱스 생성은 `lifespan`에서 try/except로 감싸고 실패해도 진행(`main.py:19` `logging.exception(...)`).
- JSON 파싱 가드: Person `traits` 프로퍼티는 문자열로 저장 → 응답 시 `json.loads`, 실패 시 `[]`로 폴백(`nodes.py:230`).

### 3.5 ETL / 운영 스크립트 (`backend/scripts/`)

- 1회성·운영 스크립트는 `backend/app/`이 아닌 `backend/scripts/`에 둔다. `if __name__ == "__main__":` 진입점 + `main()` 패턴, **`print(...)`로 진행 상황 로깅**(서버 코드의 `logging`과 구분).
- 네이밍 동사 컨벤션:
  - `load_*` — 외부 소스→Neo4j 적재: `load_theographic.py`, `load_books.py`.
  - `generate_*` — `data/` 산출물 JSON 생성: `generate_event_verses.py`, `generate_book_context.py`, `generate_person_traits.py`.
  - `inject_*` — `data/` JSON을 Neo4j에 SET: `inject_ko_names.py`, `inject_person_traits.py`, `inject_book_context.py`.
- 적재는 `UNWIND $rows`로 배치 처리(`run_batched`, `BATCH_NODE=500`/`BATCH_REL=1000`), `MERGE`로 멱등 보장(`load_theographic.py:46`).
- env 비번 미설정 시 모듈 로드 시점에 `RuntimeError`(서버 `db.py`와 동일 관용구).

---

## 4. 린팅 · 빌드

- **프론트엔드만 린트 설정 있음**: `frontend/eslint.config.js`(flat config). `@eslint/js` recommended + `eslint-plugin-react-hooks`(flat recommended) + `eslint-plugin-react-refresh`(vite). `dist`는 ignore. 실행: `npm run lint`(= `eslint .`).
- 빌드: `npm run build`(= `vite build`). `frontend/vite.config.js`에서 `manualChunks`로 `maplibre-gl`을 `maplibre` 청크, 나머지 `node_modules`를 `vendor` 청크로 코드 스플리팅.
- 포매터(Prettier 등) 설정 파일 없음. 들여쓰기는 JS 2-space, Python 4-space(PEP8풍). 세미콜론은 JS에서 대체로 생략(ASI 의존).
- **백엔드 린트/포맷 설정 없음**(flake8/black/ruff/mypy 미사용, 설정 파일 부재).
- CI(`.github/workflows/deploy.yml`)는 lint/test를 돌리지 않는다 — main push 시 self-hosted 러너가 `git reset --hard` 후 `deploy.sh`만 실행.
- 백엔드는 hot-reload가 아니다(`backend/Dockerfile` CMD에 `--reload` 없음). 로컬 검증 전 `docker compose up -d --build api` 필요.
