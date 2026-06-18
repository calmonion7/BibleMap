---
last_mapped_commit: 6f2cfc1bf163d7327bd86773676223624fa53ff2
mapped: 2026-06-18
---

# BibleMap 코드 컨벤션

## 코드 스타일 및 포맷

### 프론트엔드 (JavaScript/JSX)
- ESLint 설정 파일: `frontend/eslint.config.js`
- 적용 규칙: `@eslint/js` 권장 + `eslint-plugin-react-hooks` flat recommended + `eslint-plugin-react-refresh` vite 프리셋
- 대상 파일: `**/*.{js,jsx}` (`dist/` 제외)
- `ecmaFeatures.jsx: true` 활성화
- 포매터(Prettier 등) 설정 파일 없음 — 팀 내 자동 포맷 강제 없이 수동 일관성 유지
- 인라인 스타일(`style={{ ... }}`) 방식 전면 사용; CSS 모듈·styled-component 없음
- `index.css` 파일은 존재하나 전역 리셋/폰트 수준만 담당 (`frontend/src/index.css`)

### 백엔드 (Python)
- 포매터·린터 설정 파일(`.pylintrc`, `pyproject.toml`, `setup.cfg`) 없음
- Python 3.12(`Dockerfile` 기준) 타겟; `cpython-314`로 로컬 실행 흔적 존재
- 모듈 임포트는 표준 라이브러리 → 서드파티 → 내부(`from ..db import`) 순서

---

## 네이밍 컨벤션

### 파일 이름
- **프론트엔드**: PascalCase 컴포넌트 파일 (`App.jsx`, `MapView.jsx`, `SidePanel.jsx`, `TimelineView.jsx`, `VerseLangTabs.jsx`), camelCase 유틸 파일 (`api.js`, `theme.js`, `convexHull.js`)
- **백엔드 라우트**: snake_case (`nodes.py`, `events.py`, `search.py`, `books.py`)
- **백엔드 스크립트**: snake_case 동사+명사 (`load_theographic.py`, `inject_ko_names.py`, `generate_event_verses.py`)
- **데이터 파일**: 항상 `data/<category>/<entity>.json` 구조 (예: `data/names_ko/people.json`, `data/event_verses/events.json`)

### 변수·함수
- **프론트엔드**: camelCase 변수/함수 (`selectedNode`, `searchQuery`, `handleTabClick`, `onSelectNode`)
- **백엔드 Python**: snake_case (`get_driver`, `run_batched`, `load_people`, `filter_published`)
- **Neo4j 속성**: camelCase (`theographic_id`, `nameKo`, `aliasesKo`, `startDate`, `bookOrder`)
- **상수**: UPPER_SNAKE_CASE (`SEARCH_LIMIT = 20`, `MAX_NEIGHBORS_PER_TYPE = 30`, `BATCH_NODE = 500`, `MOBILE_QUERY`, `SHEET_VH`)

### 컴포넌트·클래스
- React 컴포넌트: PascalCase, default export (`export default function MapView(...)`)
- 백엔드 클래스 미사용 — FastAPI 라우터를 모듈 수준 함수로 정의

---

## 일관되게 사용되는 패턴

### 프론트엔드

**단일 API 클라이언트** (`frontend/src/api.js`)
- `API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'`
- `apiGet(path, { signal })` 하나로 모든 fetch 통일; 비-OK 응답은 `throw res.status`
- AbortController를 직접 호출부에서 생성해 넘김 (스테일 응답 방지 패턴)

**공유 테마 팔레트** (`frontend/src/theme.js`)
- `TYPE_COLOR`, `TYPE_KO`, `TYPE_ORDER`, `typeColor()`, `typeKo()`, `SELECT_HL` 단일 출처
- 모든 뷰(App, SidePanel, TimelineView, MapView)가 이 파일에서만 색·라벨 가져옴

**React 비동기 state 패턴**
- `useEffect` 내부에서 `cancelled` 플래그로 stale 응답 무시 (`SidePanel.jsx`)
- `useRef`로 최신값을 동기적으로 읽어 `useCallback([])` 참조 안정화 (`App.jsx` `selectNode`, `selectedNodeRef`)
- react-hooks v7 준수: setState는 비동기 콜백 내부에서만 호출 (`App.jsx` 검색 effect 주석 참조)

**인라인 스타일 레이아웃**
- 모든 UI 스타일을 인라인 `style={{ }}` 객체로 정의 (CSS 파일 미사용, 예외: `maplibre-gl.css` import)
- 다크 배경 기본 컬러: `#1a1a2e` (네비게이션 바, 검색 드롭다운)

**이중언어 텍스트 처리**
- Neo4j 속성: `name`(영문 원본), `nameKo`(한국어), `nameKoMissing` 플래그
- 없는 경우 `nameKo ?? name` 폴백 패턴 전 코드에서 일관 사용
- 구절 본문: `verseLang` 상태(`'ko'|'en'`)로 `textKo`/`textEn` 필드 선택 (ADR-0003)

### 백엔드

**싱글턴 Neo4j 드라이버** (`backend/app/db.py`)
- 모듈 수준 `_driver = None` + `get_driver()` 패턴으로 프로세스당 하나의 연결 유지

**`functools.lru_cache(maxsize=1)` 파일 캐시 패턴**
- `_load_approx()`, `_load_event_verses()`, `_load_approx_book_index()`, `_load_book_events()` 등 JSON 오버레이 파일을 프로세스 시작 후 1회만 로드

**멀티 경로 폴백 탐색** (`backend/app/routes/events.py`, `books.py`)
- `_XXX_CANDIDATES = ["/app/data/...", os.path.join(_REPO_DATA_DIR, "...")]` 목록을 순서대로 시도
- Docker 볼륨 마운트 경로 우선, 실패 시 레포 상대경로로 폴백

**배치 Cypher 실행** (`backend/scripts/`)
- `run_batched(session, cypher, rows, batch_size)` 헬퍼로 Neo4j 적재 시 일정 크기 배치 처리
- 노드 적재: `BATCH_NODE = 500`, 관계 적재: `BATCH_REL = 1000`

**스크립트 `__name__ == "__main__"` 진입점**
- 모든 `backend/scripts/*.py`는 직접 실행용 스탠드얼론 스크립트; FastAPI 앱과 분리

---

## 에러 처리

### 프론트엔드
- API 실패: `apiGet` 자체가 `throw res.status`(숫자)를 발생; 호출부가 `.catch(e => ...)` 처리
- AbortError: `e.name === 'AbortError'` 로 구분 후 무시 (최신 요청이 진행 중)
- UI 수준: 로딩/에러/노데이터 세 상태를 조건부 렌더로 표시 (예: `SidePanel.jsx` `if (!ready) return ...`)

### 백엔드
- Neo4j 인덱스 생성 실패: `except Exception: logging.exception(...)` 후 계속 진행 (`main.py`)
- 노드 없음: `raise HTTPException(status_code=404, detail="Node not found")`
- 환경변수 미설정: 모듈 최상단 `if not NEO4J_PASSWORD: raise RuntimeError(...)` 즉시 중단
- JSON 파일 로드 실패: `except (FileNotFoundError, json.JSONDecodeError): continue` 후 다음 후보 시도, 최종 실패 시 빈 dict/빈 배열 폴백

---

## Import/Export 컨벤션

### 프론트엔드
- ES Module (`"type": "module"` in `package.json`)
- 컴포넌트: `export default function ComponentName`
- 유틸/상수: named export (`export const TYPE_COLOR = ...`, `export function apiGet(...)`)
- 사용처: named import(`import { apiGet } from './api'`, `import { TYPE_COLOR, TYPE_KO } from './theme'`), default import for 컴포넌트

### 백엔드
- FastAPI 라우터: 각 모듈 상단에서 `router = APIRouter()` 생성 후 `@router.get(...)` 데코레이터
- `main.py`에서 `app.include_router(nodes.router)` 방식으로 등록
- 상대 import 사용: `from ..db import get_driver`, `from .routes import nodes, events, search, books`
