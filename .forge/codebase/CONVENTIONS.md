---
last_mapped_commit: bfc1dd258b0308435ca24c48a82c9c86a9e622f1
mapped: 2026-06-16
---

# CONVENTIONS

코딩 컨벤션·패턴·에러 처리·린트 설정. 프론트엔드(React/JSX)와 백엔드(Python/FastAPI)를 모두 다룬다.

## 1. 언어·주석

- **주석·UI 문자열·로그는 한국어.** 코드 식별자(변수·함수·필드)는 영어. `props.get`, `nameKo` 같은 식별자는 영어, 그 옆 설명 주석은 한국어가 기본.
- 주석은 "왜"에 집중한다 — 회고에서 발견한 함정을 그 줄에 박아 둔다. 예: `MapView.jsx`의 fitBounds 주석("task 15에서 어긋났던 지점"), `theme.js`의 팔레트 통일 이유, `App.jsx`의 `selectNode` useCallback 안정화 이유.

## 2. 프론트엔드 (React 19 / JSX)

### 파일·모듈
- 컴포넌트는 `frontend/src/*.jsx`, 순수 로직/상수는 `frontend/src/*.js`.
- 컴포넌트 파일은 함수 컴포넌트 1개 + `export default`. 진입점은 `frontend/src/main.jsx`(`StrictMode`로 감쌈).
- 공유 상수/헬퍼는 전용 모듈로 분리: `frontend/src/theme.js`(타입 색·라벨), `frontend/src/api.js`(API 클라이언트), `frontend/src/convexHull.js`(순수 알고리즘).

### import 스타일
- ESM, 세미콜론 없음, 작은따옴표. 예: `import { useState, useEffect } from 'react'`.
- React 훅 → 서드파티(`maplibre-gl`, `lucide-react`) → 로컬 모듈 순.

### 타입 색 테마 — `frontend/src/theme.js` 단일 출처
- 노드 타입 → 색/한글 라벨은 **반드시 `frontend/src/theme.js`에서 import**한다. `TYPE_COLOR`, `TYPE_KO`, `TYPE_ORDER`, `typeColor()`, `typeKo()`, `SELECT_HL`을 export.
- 과거엔 `App.jsx`·`SidePanel.jsx`·(지금은 삭제된) `GraphView.jsx`에 색이 따로 정의돼 같은 색이 다른 타입을 뜻하는 충돌이 있었고, 이를 `theme.js` 하나로 통일했다(`theme.js` 상단 주석 참조). 새 타입색 사용처는 로컬 상수를 만들지 말고 `theme.js`를 import할 것.
- `SidePanel.jsx`는 `TYPE_COLOR`/`TYPE_KO`를 직접 import해 쓰고, `App.jsx`는 헬퍼(`typeColor`/`typeKo`)를 import해 쓴다. `TimelineView.jsx`/`MapView.jsx`는 `SELECT_HL`만 공유로 쓰고 Book/Place 등 뷰 고유색은 파일 상단 로컬 상수로 둔다(예: `TimelineView.jsx`의 `BOOK_COLOR`).

### API 호출 — 통합 베이스 URL 패턴 (`frontend/src/api.js`)
- 모든 프론트 fetch는 `frontend/src/api.js`의 `apiGet(path, { signal })`를 거친다. 직접 `fetch`로 백엔드를 부르지 않는다.
- 베이스 URL: `export const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'`. 프로덕션은 빌드타임 `VITE_API_URL=/api`(`frontend/.env.production`) 주입 → nginx가 `/api → api:8000` 프록시(`nginx/nginx.conf`).
- `apiGet`은 GET→JSON. 비-OK 응답이면 `throw res.status`(숫자 status로 reject). `AbortError`는 fetch에서 그대로 전파되며, 호출부가 `e.name === 'AbortError'`로 구분해 무시한다.
- 예외: 외부 한국어 성경 API(getbible)는 `apiGet`이 아니라 `SidePanel.jsx` 내부 `fetchVerseText`에서 직접 `fetch`(실패 시 `null` 반환).

### 스타일링
- **인라인 `style={{...}}` 객체**가 표준. CSS-in-JS 라이브러리·CSS Modules 없음. 전역 스타일은 `frontend/src/index.css`만.
- 색은 hex/rgba 리터럴(예: `#1a1a2e`, `rgba(255,255,255,0.1)`). 폰트는 `system-ui, -apple-system, sans-serif`.
- 레이아웃 상수는 컴포넌트 내부/상단 상수로(예: `App.jsx`의 `NAV_H = 48`, `SHEET_VH = 55`). 프론트·맵 패딩처럼 서로 맞춰야 하는 값은 주석으로 "일치시켜라"를 명시(`SHEET_VH=55` ↔ `MapView.jsx` 하단 패딩 0.55).

### 상태·effect 규칙 (react-hooks v7 — set-state-in-effect)
- **effect의 동기 본문에서 직접 `setState` 금지.** `setState`는 비동기 콜백(`fetch().then`, `setTimeout`, async 콜백) 안에서만 호출한다. 이 규칙은 린트로 강제되며 코드는 lint-clean하게 유지된다(아래 commit `a84d855` 참조).
- 동기 reset이 필요하면 **파생 상태(derived state)** 로 대체한다:
  - `SidePanel.jsx`: 응답을 `{ id, node, error }`로 묶어 저장하고, 렌더에서 `state.id === nodeId`일 때만 사용(stale 응답 무시). `collapsed` 리셋은 fetch `.then` 안으로 이동. `keyVerse`는 `{ id, text }`로 키잉.
  - `TimelineView.jsx`: "닫기"를 boolean+effect 대신 `dismissedFilter`(어느 필터를 닫았는지 식별자)로 추적 → effect 제거, 새 필터(다른 참조)면 자동 재표시.
- 콜백 prop은 `useCallback([])`으로 참조를 안정화한다. 예: `App.jsx`의 `selectNode`/`handleNodeLoaded`는 deps `[]`로 안정화해 `MapView`의 effect가 불필요하게 재실행돼 진행 중 fetch가 abort되는 버그를 막는다(최신값은 `selectedNodeRef`로 읽음).
- 비동기 경쟁(race)은 두 방식으로 차단: (a) `AbortController`로 직전 요청 abort(검색 디바운스 `App.jsx`, places fetch `MapView.jsx`, 링 확장 `MapView.jsx`), (b) effect 정리에서 `cancelled` 플래그(`SidePanel.jsx`).
- 검색은 250ms 디바운스(`App.jsx`), 매 입력마다 직전 요청 abort.

### MapView 특이 패턴 (`frontend/src/MapView.jsx`)
- maplibre 인스턴스·애니메이션 상태는 **React state가 아니라 ref/지역변수**로 관리(프레임마다 리렌더 방지). `mapRef`, `popupRef`, `expandPlaceRef`, `expandedPlaceRef`, 그리고 effect 내부 `let animFrame`/`expandAbortCtrl`/`destroyed`.
- React state는 렌더가 필요한 것만(`mapLoaded`, `error`, `noLocation`).
- effect 정리에서 `destroyed = true`, `cancelAnimationFrame`, abort, popup remove, `map.remove()`를 반드시 수행. 콜백마다 `if (mapRef.current !== map) return` / `if (destroyed) return`로 stale 맵 가드.

## 3. 백엔드 (Python 3.12 / FastAPI)

### 구조
- 앱 패키지 `backend/app/`. 진입점 `backend/app/main.py`가 `FastAPI()`를 만들고 라우터를 `include_router`로 등록.
- 라우트는 도메인별 모듈로 분리: `backend/app/routes/{nodes,events,search,books}.py`. 각 모듈은 자체 `router = APIRouter()`를 만들고 `@router.get(...)`으로 핸들러를 단다.
- DB 드라이버는 `backend/app/db.py`의 `get_driver()` 싱글톤(`global _driver`, 지연 초기화)으로 한 곳에서만 생성.
- 데이터 적재/생성 스크립트는 `backend/app/`이 아니라 별도 `backend/scripts/`(런타임 API와 분리).

### 코드 스타일
- 표준 라이브러리 → 서드파티 → 로컬(`..db`, `.routes`) 순 import. 4-스페이스 들여쓰기, double-quote 문자열.
- 모듈/함수 docstring은 한국어(예: `books.py`의 `_load_approx`, `get_books`).
- 라우트 핸들러는 타입 힌트를 붙임: `def get_node(node_id: str):`, `def search(q: str = Query("")):`.
- 매직 넘버는 모듈 상수로: `nodes.py`의 `MAX_NEIGHBORS_PER_TYPE = 30`, `NODE_NEIGHBOR_LIMIT = 50`; `search.py`의 `SEARCH_LIMIT = 20`.

### Neo4j 접근 패턴
- 항상 `with driver.session() as session:` 컨텍스트. 쿼리는 `session.run(cypher, **params)`.
- **사용자 입력은 Cypher 파라미터(`$id`, `$q`)로만** 전달(인젝션 방지). 단, LIMIT 같은 상수는 검증된 모듈 상수를 f-string으로 인라인(`f"... LIMIT {NODE_NEIGHBOR_LIMIT}"`).
- 노드 식별자는 비즈니스 키 `theographic_id`로 매칭(`MATCH (n {theographic_id: $id})`). 응답 `id` 필드도 `theographic_id`.
- 레코드 속성은 `dict(record["n"])`로 풀고 `props.get(...)`로 안전 접근.
- 한글 이름 폴백 일관 패턴: `nameKo if nameKo else name`(또는 `or`), 그리고 `nameKoMissing = name_ko is None` 플래그를 응답에 함께 실어 프론트가 "(미번역)" 표기.

### 에러 처리
- 없는 리소스: `raise HTTPException(status_code=404, detail="Node not found")`.
- 좌표 파싱 실패는 건너뜀: `try: float(...) except (TypeError, ValueError): continue`.
- 앱 시작 시 인덱스 생성은 best-effort — 실패해도 `logging.exception(...)` 후 계속(`main.py` `lifespan`).
- JSON 오버레이 로드는 후보 경로를 순회하다 `(FileNotFoundError, json.JSONDecodeError)`면 다음 후보, 전부 실패 시 빈 dict 폴백(`books.py` `_load_approx`).
- Person `traits` 같은 JSON 문자열 파싱은 `try/except Exception` → 실패 시 `[]`(`nodes.py`).

### 설정·시크릿
- 설정은 환경변수: `NEO4J_URI`/`NEO4J_USER`는 기본값 있는 `os.getenv`, `NEO4J_PASSWORD`는 기본값 없이 읽은 뒤 없으면 `raise RuntimeError("NEO4J_PASSWORD 환경변수가 설정되지 않았습니다")`. 시크릿 기본값·하드코딩 없음.
- 데이터 경로는 docker/비-docker 양쪽을 위한 폴백: `DATA_DIR`(기본 `/app/data`, compose가 `./data` 볼륨 마운트) 우선 → 레포 상대경로 폴백(`books.py`). compose 볼륨은 `docker-compose.yml`의 `./data:/app/data`.

### 캐싱·응답 헤더
- 변하지 않는 1회 로드 데이터는 `@functools.lru_cache(maxsize=1)`(`books.py` `_load_approx`). 백엔드는 hot-reload가 아니라 변경 시 재빌드가 필요하다.
- 항상 새 데이터를 줘야 하는 엔드포인트는 `JSONResponse(content=..., headers={"Cache-Control": "no-store"})`(`/books`, `/events`).
- CORS는 전역 미들웨어, `allow_methods=["GET"]`(읽기 전용 API).

### 스크립트 (`backend/scripts/`)
- 모듈 docstring(한국어, 사용법 포함) → 상수(URL·경로) → 함수 → `def main()` → `if __name__ == "__main__": main()`.
- 경로는 `os.path.join(os.path.dirname(__file__), "..", "..", "data", ...)` + `os.path.normpath`(또는 `pathlib.Path(__file__).parent...`)로 스크립트 기준 상대 계산.
- Neo4j 대량 적재는 `UNWIND $rows AS row ... MERGE`, 관계는 `batch_size = 500`으로 청크(`load_books.py`).
- AI 생성 스크립트(`generate_person_traits.py` 등)는 `import anthropic` + `client.messages.create(model="claude-haiku-4-5-20251001", ...)`, 프롬프트는 모듈 상수 `PROMPT_TEMPLATE`로 두고 순수 JSON 출력을 요구. API 키는 `ANTHROPIC_API_KEY` 환경변수.

## 4. 린트 설정

- 프론트엔드만 린트 대상. `frontend/eslint.config.js`(flat config): `@eslint/js` recommended + `eslint-plugin-react-hooks` flat recommended(v7) + `eslint-plugin-react-refresh` vite. `dist` 무시, `**/*.{js,jsx}`에 적용, `globals.browser`.
- 실행: `cd frontend && npm run lint`(= `eslint .`). **현재 lint-clean(exit 0).**
- 최근 작업으로 set-state-in-effect 위반(에러 3 + 경고 1)을 해소해 클린화했다 — commit `a84d855`("refactor(frontend): lint set-state-in-effect 해소 → lint clean (2/4)"), 대상 `SidePanel.jsx`·`TimelineView.jsx`. 동기 effect setState를 파생 상태/콜백 안 setState로 옮긴 것이 핵심(2절 "상태·effect 규칙" 참조).
- 백엔드에는 린터/포매터 설정 파일이 없다(flake8/ruff/black/mypy 등 없음).

## 5. 커밋 메시지

- Conventional Commits + 한국어 본문. 타입(scope) 접두사 사용: `refactor(frontend):`, `refactor(backend):`, `docs:`. 시리즈 작업은 제목 끝에 `(N/M)` 표기.
- 본문은 한국어 불릿으로 무엇을·왜·검증(예: "npm run lint exit 0", "UAT 통과")을 적는다.
- 푸터: `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`.

## 관련 파일

- `frontend/src/theme.js` — 타입 색·라벨 단일 출처(반드시 import).
- `frontend/src/api.js` — 통합 API 클라이언트(`API_BASE`, `apiGet`).
- `frontend/eslint.config.js` — 린트 설정(flat).
- `frontend/.env.production` — `VITE_API_URL=/api`.
- `backend/app/main.py` / `backend/app/db.py` / `backend/app/routes/*.py` — FastAPI 앱·드라이버·라우트.
- `backend/scripts/*.py` — 데이터 적재·AI 생성 스크립트.
- `nginx/nginx.conf` — `/api` 프록시·캐시 헤더.
- `docker-compose.yml` — `./data` 볼륨 마운트.
