---
last_mapped_commit: cecf0d7de87192b638f428eb7e708e94a58214a6
mapped: 2026-06-20
---
# Codebase Structure

**Analysis Date:** 2026-06-20

## Directory Layout

```
BibleMap/
├── backend/                  # FastAPI 백엔드
│   ├── app/
│   │   ├── main.py           # FastAPI 앱 진입점, 라우터 등록
│   │   ├── db.py             # Neo4j 드라이버 싱글톤
│   │   ├── overlays.py       # JSON 오버레이 로더 (lru_cache)
│   │   ├── __init__.py
│   │   └── routes/
│   │       ├── nodes.py      # /node/* /person/* 엔드포인트
│   │       ├── events.py     # /events /event/* 엔드포인트
│   │       ├── search.py     # /search 엔드포인트
│   │       ├── books.py      # /books /books-overview 엔드포인트
│   │       └── __init__.py
│   └── scripts/              # 데이터 생성·주입 일회성 스크립트
│       ├── generate_*.py     # JSON 오버레이 생성 스크립트
│       ├── inject_*.py       # Neo4j 직접 쓰기 스크립트
│       └── load_*.py         # Neo4j 최초 데이터 로드 스크립트
├── frontend/
│   ├── src/
│   │   ├── main.jsx          # React 진입점 (createRoot)
│   │   ├── App.jsx           # 루트 컴포넌트 (탭, 검색, 패널)
│   │   ├── MapView.jsx       # 지도 탭 뷰
│   │   ├── TimelineView.jsx  # 타임라인 탭 뷰
│   │   ├── BibleOverviewView.jsx  # 성경 개요 탭 뷰
│   │   ├── SidePanel.jsx     # 노드 상세 패널
│   │   ├── VerseLangTabs.jsx # ko/en 언어 탭 (공유 UI)
│   │   ├── useNodeSelection.js  # 노드 선택 상태 커스텀 훅
│   │   ├── useSearch.js      # 검색 상태 커스텀 훅
│   │   ├── api.js            # apiGet() 공유 fetch 헬퍼
│   │   ├── theme.js          # TYPE_COLOR, TYPE_KO 공유 팔레트
│   │   ├── convexHull.js     # Graham scan (MapView 전용)
│   │   ├── index.css         # 전역 스타일
│   │   └── assets/           # 정적 자산 (favicon 등)
│   ├── dist/                 # 빌드 결과 (nginx 서빙, git tracked)
│   ├── public/               # index.html 등 정적 파일
│   ├── package.json
│   └── vite.config.js
├── data/                     # JSON 오버레이 파일 (Docker 마운트)
│   ├── book_events/
│   │   └── books.json        # {bookId: [eventId, ...]}
│   ├── event_verses/
│   │   └── events.json       # 사건별 근거 구절
│   ├── book_years_approx/
│   │   └── books.json        # {bookId: {placementYear, basis, ...}}
│   ├── authored_events/
│   │   └── events.json       # 직접 저작 이벤트 데이터
│   ├── character_traits/
│   │   └── people.json       # 인물 특성
│   ├── book_context/         # 성경책 컨텍스트 메타데이터
│   ├── names_ko/             # 한국어 이름 매핑 (books, events, groups, people, places)
│   └── verse_events/
│       └── events.json       # 구절→사건 매핑
├── nginx/
│   └── nginx.conf            # /api/ 프록시, 정적 파일 서빙, SPA fallback
├── .forge/                   # GSD 워크플로우 문서
│   ├── codebase/             # 코드베이스 분석 문서 (이 파일 포함)
│   ├── done/                 # 완료된 태스크 핸드오프
│   ├── backlog/              # 대기 중 태스크
│   └── adr/                  # Architecture Decision Records
├── .github/
│   └── workflows/            # GitHub Actions CI/CD
├── docker-compose.yml        # neo4j + api + nginx 3-service 스택
├── deploy.sh                 # 배포 스크립트
└── CLAUDE.md                 # AI 에이전트 행동 가이드라인
```

## Directory Purposes

**`backend/app/`:**
- Purpose: FastAPI 앱 코어
- Contains: `main.py`, `db.py`, `overlays.py`, `routes/`
- Key files: `backend/app/main.py`, `backend/app/overlays.py`

**`backend/app/routes/`:**
- Purpose: 엔드포인트별 라우터 모듈
- Contains: `nodes.py`, `events.py`, `search.py`, `books.py`
- 각 파일이 단일 `APIRouter` 인스턴스(`router`)를 export

**`backend/scripts/`:**
- Purpose: 데이터 파이프라인 일회성 스크립트 (앱 서빙 무관)
- Contains: `generate_*.py`(JSON 생성), `inject_*.py`(Neo4j 직접 쓰기), `load_*.py`(초기 로드)
- 서버 실행 중에도 Neo4j에 직접 쓰기 가능

**`frontend/src/`:**
- Purpose: React 앱 전체 소스 — 빌드 시 `frontend/dist/`로 번들됨
- Contains: 뷰 컴포넌트 (`*View.jsx`), 커스텀 훅 (`use*.js`), 공유 유틸 (`api.js`, `theme.js`, `convexHull.js`)

**`data/`:**
- Purpose: Neo4j 미포함 오버레이 JSON (Docker volume으로 `/app/data` 마운트)
- Generated: `backend/scripts/generate_*.py` 로 생성
- Committed: Yes (git tracked)

**`.forge/`:**
- Purpose: GSD 에이전트 워크플로우 전용 디렉터리
- Generated: No (사람/에이전트가 직접 작성)
- Committed: Yes

## Key File Locations

**Entry Points:**
- `frontend/src/main.jsx`: React DOM 진입점
- `backend/app/main.py`: FastAPI `app` 객체 (uvicorn이 임포트)

**Configuration:**
- `docker-compose.yml`: 3-service 스택 정의 (neo4j, api, nginx)
- `nginx/nginx.conf`: `/api/` 프록시 및 SPA fallback 라우팅
- `frontend/vite.config.js`: Vite 빌드 설정
- `frontend/.env.production`: `VITE_API_URL=/api` (빌드타임 주입)

**Core Logic:**
- `backend/app/overlays.py`: JSON 오버레이 로더 (세 함수 모두 여기)
- `backend/app/db.py`: Neo4j 드라이버 싱글톤
- `frontend/src/api.js`: 모든 HTTP fetch의 단일 게이트
- `frontend/src/useNodeSelection.js`: 선택 상태 + 히스토리 관리
- `frontend/src/useSearch.js`: 검색 디바운스 + 타입 필터

**Testing:**
- Not detected (테스트 파일 없음)

## Naming Conventions

**Files:**
- React 컴포넌트: PascalCase `.jsx` (예: `MapView.jsx`, `SidePanel.jsx`)
- 커스텀 훅: camelCase `use` 접두사 `.js` (예: `useNodeSelection.js`, `useSearch.js`)
- 공유 유틸: camelCase `.js` (예: `api.js`, `theme.js`, `convexHull.js`)
- Python 모듈: snake_case `.py` (예: `overlays.py`, `nodes.py`)
- 데이터 스크립트: `generate_`, `inject_`, `load_` 접두사 + snake_case

**Directories:**
- 기능 단위: snake_case (예: `book_events/`, `event_verses/`)
- 프레임워크 관례: `routes/`, `app/`, `src/`, `dist/`

## Where to Add New Code

**새 API 엔드포인트:**
- 라우터 파일: `backend/app/routes/` 아래 기존 파일에 추가하거나 새 `.py` 파일 생성
- 새 파일이면 `backend/app/main.py`에 `app.include_router(new_module.router)` 추가

**새 JSON 오버레이 소스:**
- 생성 스크립트: `backend/scripts/generate_*.py`
- 출력 디렉터리: `data/<category>/` (예: `data/new_overlay/`)
- 로더 함수: `backend/app/overlays.py`에 `@functools.lru_cache(maxsize=1)` 함수 추가

**새 탭/뷰:**
- 뷰 컴포넌트: `frontend/src/<Name>View.jsx`
- `App.jsx`의 `TABS` 배열에 항목 추가, 렌더 분기 추가

**새 커스텀 훅:**
- 위치: `frontend/src/use<Name>.js`
- `App.jsx`에서 호출, 결과를 props로 하위 컴포넌트에 전달하는 패턴 유지

**공유 UI 컴포넌트:**
- 위치: `frontend/src/<Name>.jsx`
- `theme.js`의 색상 팔레트 사용 (`TYPE_COLOR`, `SELECT_HL`)

**데이터 주입 스크립트:**
- 위치: `backend/scripts/inject_*.py` 또는 `load_*.py`
- Neo4j에 직접 쓰기. `backend/app/db.py`의 `get_driver()` 재사용 가능.

## Special Directories

**`frontend/dist/`:**
- Purpose: Vite 빌드 결과물. nginx가 정적 파일로 서빙.
- Generated: Yes (`npm run build`)
- Committed: Yes (배포 파이프라인이 dist를 git에서 읽음)

**`.claude/worktrees/`:**
- Purpose: GSD 에이전트 병렬 작업용 git worktree 체크아웃
- Generated: Yes
- Committed: No

**`data/`:**
- Purpose: JSON 오버레이 (Docker volume으로 api 컨테이너에 마운트)
- Generated: `backend/scripts/generate_*.py`로 생성, 수동 편집도 가능
- Committed: Yes

---

*Structure analysis: 2026-06-20*
