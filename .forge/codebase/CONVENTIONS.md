---
last_mapped_commit: 9f47b78ed927ef302cefffb5b62ef71885b6aa94
mapped: 2026-06-19
---

# BibleMap 코드 컨벤션

## 언어 및 파일 구조

- **프론트엔드**: React 19 + Vite 8. 파일 확장자 `.jsx`(컴포넌트), `.js`(유틸·설정).
- **백엔드**: Python + FastAPI. 파일 확장자 `.py`.
- **스크립트**: `backend/scripts/` — 데이터 생성·주입 전용 독립 실행 파일. FastAPI 앱과 분리.

## 프론트엔드 네이밍

- 컴포넌트 파일: PascalCase (`MapView.jsx`, `SidePanel.jsx`, `TimelineView.jsx`, `VerseLangTabs.jsx`).
- 유틸·설정 파일: camelCase (`api.js`, `theme.js`, `convexHull.js`).
- 컴포넌트 함수: PascalCase (`function MapView(...)`, `function SidePanel(...)`).
- 로컬 상수·변수: SCREAMING_SNAKE_CASE가 모듈 수준 상수에 사용됨 (`MOBILE_QUERY`, `SHEET_VH`, `EMPTY_GEOJSON`, `NAV_H`).
- 이벤트 핸들러 함수: `handle`/`on` 접두사 (`handleTabClick`, `onSearchInput`, `onSelectNode`).

## 백엔드 네이밍

- 라우터 파일: 소문자 복수형 (`nodes.py`, `events.py`, `books.py`, `search.py`).
- 라우터 변수: 각 파일에서 `router = APIRouter()`.
- 모듈 수준 상수: SCREAMING_SNAKE_CASE (`MAX_NEIGHBORS_PER_TYPE`, `NODE_NEIGHBOR_LIMIT`, `SEARCH_LIMIT`, `BATCH_NODE`, `BATCH_REL`).
- `_` 접두사 변수: 모듈 내부 전용 캐시·경로 변수 (`_driver`, `_EVENT_VERSES_CANDIDATES`, `_chapter_cache`).
- 헬퍼 함수: `_` 접두사 소문자 + 스네이크 케이스 (`_load_event_verses`, `_load_approx_book_index`).

## 공유 색·라벨 팔레트

- `frontend/src/theme.js` 한 파일에서 `TYPE_COLOR`, `TYPE_KO`, `TYPE_ORDER`, `typeColor()`, `typeKo()`, `SELECT_HL`을 export.
- 모든 뷰(MapView, SidePanel, TimelineView, App)가 theme.js를 import해서 사용. 뷰별 로컬 재정의 금지 규칙이 주석으로 명시(`theme.js` 1~3행).

## API 클라이언트

- `frontend/src/api.js` — `API_BASE`(환경변수 `VITE_API_URL` 또는 `http://localhost:8000`)와 `apiGet(path, {signal})` 함수 하나만 export.
- 모든 프론트 fetch는 `apiGet`으로 통일. `fetch` 직접 호출 없음.
- 비-OK 응답은 `throw res.status`(숫자)로 reject. `AbortError`는 호출부에서 `e.name === 'AbortError'`로 판별.

## 상태 관리 패턴

- 전역 상태 없음(Redux/Zustand 미사용). App.jsx가 `selectedNode`, `verseLang`, `personEventIds` 등 공유 상태를 보유하고 prop으로 전달.
- `useRef`로 최신 상태를 읽는 패턴: `selectedNodeRef.current = selectedNode`(effect 내 stale closure 방지).
- `cancelled` 플래그 패턴: useEffect 클린업에서 `cancelled = true`로 경쟁 응답 무시(`SidePanel.jsx` 50~57행).
- 실시간 검색: 250ms 디바운스 + `AbortController`로 직전 요청 취소(`App.jsx` 68~88행).

## React Hooks 규칙

- `setState`는 `setTimeout`/`async` 콜백 안에서만 호출. effect 동기 본문 내 `setState` 금지(`App.jsx` 68행 주석).
- `useCallback([], [...])` 로 참조 안정화: `selectNode`가 `[]` 의존성으로 정의되고 최신 값은 `selectedNodeRef`로 읽음.

## 에러 핸들링

- **프론트**: `try/catch` 안에서 `setError(true)` 등 에러 state 세팅. `AbortError`는 무시하고 return. 에러 UI는 조건부 렌더링으로 인라인 표시.
- **백엔드**: FastAPI 라우터에서 `HTTPException(status_code=404, detail="...")`로 리소스 없음 처리. Neo4j 드라이버 초기화 실패는 `RuntimeError` 발생. 스크립트 외부 API 실패는 `except Exception`으로 잡고 `None` 반환(재시도 가능하도록 캐시 미적재).
- **JSON 파일 로드**: 복수 후보 경로(Docker 볼륨 경로 → 레포 상대 경로) 순서로 시도. `FileNotFoundError`·`json.JSONDecodeError` 모두 잡아 빈 dict 폴백.
- **`@functools.lru_cache(maxsize=1)`**: JSON 오버레이 파일을 프로세스당 1회만 로드. `events.py`, `books.py`에서 사용.

## 인라인 스타일

- 프론트엔드 CSS는 모두 인라인 `style={{...}}` 객체. 별도 CSS 클래스·CSS Module 없음(`index.css`는 전역 리셋만).
- 스타일 객체 공유: `chipBase`, `verseBoxStyle` 등을 로컬 상수로 선언 후 spread(`{...chipBase, ...override}`).
- 컬러 토큰은 theme.js `TYPE_COLOR`에서 가져오고, 뷰별 로컬 상수(`BOOK_COLOR = '#a78bfa'`)는 theme.js 값을 그대로 참조하거나 별도 상수로 선언.

## Cypher(Neo4j) 패턴

- 노드 식별자: `theographic_id` 속성 사용(`n.theographic_id`). id 파라미터명 `$id`.
- 배치 로드: `UNWIND $rows AS row MERGE ...`로 트랜잭션당 500(노드)·1000(관계) 건 일괄 처리.
- 인덱스: 각 레이블에 `theographic_id`에 대한 인덱스. FastAPI lifespan에서 `CREATE INDEX ... IF NOT EXISTS` 실행.
- 인용 절 텍스트 필드명: `nameKo`(노드), `textKo`/`textEn`(절 본문), `keyVerseTextKo`/`keyVerseTextEn`(대표 절).

## 데이터 파이프라인 규칙

- 빌드타임 미리굽기(ADR-0003): 절 본문(`textKo`/`textEn`)은 `generate_verse_text.py`로 `data/` JSON에 삽입. 런타임 외부 API 호출 없음.
- 추정책 연대·사건 연결은 Neo4j에 넣지 않고 `data/book_years_approx/books.json`, `data/book_events/books.json` 런타임 오버레이로 처리(ADR-0004, ADR-0005).
- 스크립트는 `__name__ == "__main__"` 가드로만 실행. FastAPI app import 불가(의존성 없이 독립).

## Vite 빌드

- 프로덕션 `VITE_API_URL=/api` — `frontend/.env.production`에 선언. 개발은 `http://localhost:8000` 폴백.
- 청크 분리: `vite.config.js`의 `manualChunks`로 `maplibre-gl` → `maplibre`, 나머지 `node_modules` → `vendor`.

## Docker/서비스 구성

- 3개 서비스: `neo4j`, `api`, `nginx`.
- `api` 컨테이너는 `./data:/app/data` 볼륨 마운트. 오버레이 JSON을 `/app/data`에서 읽음.
- `nginx`는 `frontend/dist`를 정적으로 서빙. HMR 아님 → 검증 전 `npm run build` 필수.
- 외부 노출: nginx만 `8080:80`. neo4j는 `127.0.0.1`만. api는 미노출.
