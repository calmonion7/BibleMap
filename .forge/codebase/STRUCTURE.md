---
last_mapped_commit: fb78d740df63d386e84ceb1bb4249921a5e198b7
mapped: 2026-06-14
---

# Codebase Structure

**Analysis Date:** 2026-06-14

## Directory Layout

```
BibleMap/
├── backend/                  # Python FastAPI 서버
│   ├── app/                  # 앱 패키지
│   │   ├── main.py           # FastAPI 앱 초기화, CORS, lifespan
│   │   ├── db.py             # Neo4j 드라이버 싱글톤
│   │   └── routes/           # 라우터 모듈
│   │       ├── nodes.py      # /node/* 엔드포인트
│   │       ├── events.py     # /events 엔드포인트
│   │       └── search.py     # /search 엔드포인트
│   ├── scripts/              # 일회성 데이터 적재 스크립트 (런타임 외)
│   │   ├── load_theographic.py   # Theographic JSON → Neo4j 배치 적재
│   │   └── inject_ko_names.py    # 한국어 이름 Neo4j 주입
│   ├── Dockerfile            # python:3.12-slim, uvicorn CMD
│   └── requirements.txt      # fastapi, neo4j, uvicorn
│
├── frontend/                 # React SPA (Vite)
│   ├── src/                  # 소스 코드
│   │   ├── main.jsx          # React 루트 마운트
│   │   ├── App.jsx           # 루트 컴포넌트, 전역 상태
│   │   ├── MapView.jsx       # maplibre-gl 지도 뷰
│   │   ├── TimelineView.jsx  # 이벤트 타임라인 뷰
│   │   ├── GraphView.jsx     # cytoscape 그래프 뷰
│   │   ├── SidePanel.jsx     # 노드 상세 사이드패널
│   │   ├── api.js            # 공유 API 클라이언트 (apiGet)
│   │   ├── theme.js          # 공유 색·라벨 팔레트
│   │   ├── App.css           # App 컴포넌트 스타일
│   │   ├── index.css         # 글로벌 스타일
│   │   └── assets/           # 정적 에셋 (이미지 등)
│   ├── public/               # 빌드에 그대로 복사되는 정적 파일
│   │   ├── favicon.svg
│   │   └── icons.svg
│   ├── dist/                 # 빌드 결과물 (nginx에서 서빙, git 미추적)
│   ├── index.html            # SPA 진입 HTML
│   ├── vite.config.js        # Vite 설정 (react 플러그인만)
│   ├── eslint.config.js      # ESLint 설정
│   └── package.json          # 의존성 선언
│
├── nginx/
│   └── nginx.conf            # /api/* 프록시 + SPA fallback 설정
│
├── data/
│   └── names_ko/             # 한국어 이름 JSON (스크립트 입력)
│       ├── people.json
│       ├── places.json
│       ├── events.json
│       └── groups.json
│
├── .forge/                   # 프로젝트 관리 (GSD/forge 워크플로우)
│   ├── CONTEXT.md            # 도메인 용어집
│   ├── codebase/             # 코드베이스 분석 문서 (이 파일 위치)
│   ├── backlog/              # 대기 중인 작업 카드
│   ├── done/                 # 완료된 작업 기록
│   ├── adr/                  # Architecture Decision Records
│   ├── retro/                # 회고 기록
│   └── quick/                # 빠른 메모
│
├── .github/workflows/
│   └── deploy.yml            # main 푸시 → self-hosted runner → deploy.sh
│
├── docker-compose.yml        # neo4j + api + nginx 3-서비스 구성
├── deploy.sh                 # 프로덕션 배포 스크립트 (git reset + build + compose up)
├── .env                      # NEO4J_PASSWORD (git 미추적)
├── .env.example              # 환경변수 템플릿
└── CLAUDE.md                 # LLM 행동 가이드라인
```

## Directory Purposes

**`backend/app/`:**
- Purpose: FastAPI 런타임 패키지 — API 서버로 배포되는 코드만 포함
- Contains: `main.py`, `db.py`, `routes/` 패키지
- Key files: `backend/app/main.py` (FastAPI 앱 객체), `backend/app/db.py` (드라이버 싱글톤)

**`backend/app/routes/`:**
- Purpose: HTTP 엔드포인트 별 라우터. 각 파일이 `APIRouter` 인스턴스를 내보내고 `main.py`에서 `include_router`
- Contains: `nodes.py`, `events.py`, `search.py`

**`backend/scripts/`:**
- Purpose: 일회성 데이터 파이프라인. 서버 런타임과 무관. 운영자가 직접 실행
- Contains: `load_theographic.py` (외부 Theographic JSON → Neo4j), `inject_ko_names.py` (한국어 이름 주입)

**`frontend/src/`:**
- Purpose: React SPA 소스. Vite로 빌드 → `frontend/dist/`
- Contains: 컴포넌트(`.jsx`), 공유 유틸(`.js`), 스타일(`.css`)
- Key files: `frontend/src/App.jsx` (루트), `frontend/src/api.js` (fetch), `frontend/src/theme.js` (팔레트)

**`data/names_ko/`:**
- Purpose: `inject_ko_names.py`의 입력 소스. theographic_id → 한국어 이름 JSON 매핑
- Generated: 수동 관리
- Committed: Yes

**`nginx/`:**
- Purpose: nginx 컨테이너 설정. `/api/` → FastAPI 프록시, `/` → `frontend/dist` SPA
- Key files: `nginx/nginx.conf`

**`.forge/`:**
- Purpose: GSD 워크플로우 프로젝트 관리 디렉터리
- Generated: No (수동 + 에이전트 생성)
- Committed: Yes

**`frontend/dist/`:**
- Purpose: Vite 빌드 출력. nginx 컨테이너가 직접 마운트
- Generated: Yes (`npm run build`)
- Committed: No (`.gitignore`)

## Key File Locations

**Entry Points:**
- `frontend/src/main.jsx`: React 앱 루트
- `backend/app/main.py`: FastAPI 앱 객체 (`app`)
- `frontend/index.html`: SPA HTML 셸

**Configuration:**
- `docker-compose.yml`: 전체 서비스 구성 (neo4j, api, nginx)
- `nginx/nginx.conf`: 리버스 프록시 + SPA fallback
- `backend/requirements.txt`: Python 의존성
- `frontend/package.json`: Node.js 의존성
- `frontend/vite.config.js`: Vite 빌드 설정
- `.env`: `NEO4J_PASSWORD` (읽지 말 것)
- `.env.example`: 환경변수 템플릿

**Core Logic:**
- `backend/app/routes/nodes.py`: 노드 조회·이웃·장소 엔드포인트
- `backend/app/routes/search.py`: 전문 검색 엔드포인트
- `backend/app/db.py`: Neo4j 연결 관리
- `frontend/src/App.jsx`: 전역 상태, 검색 로직, 탭 라우팅
- `frontend/src/MapView.jsx`: 지도 + 사건 링 애니메이션
- `frontend/src/theme.js`: 뷰 공유 색·라벨 팔레트

**Testing:**
- 없음. 테스트 파일 미존재.

## Naming Conventions

**Files:**
- React 컴포넌트: PascalCase `.jsx` — `MapView.jsx`, `SidePanel.jsx`
- 공유 유틸 모듈: camelCase `.js` — `api.js`, `theme.js`
- Python 모듈: snake_case `.py` — `nodes.py`, `load_theographic.py`

**Directories:**
- 모두 소문자 kebab-case — `names_ko/`, `routes/`

**React 컴포넌트:**
- 컴포넌트 함수: PascalCase
- 이벤트 핸들러: `on` 접두사 (props), `handle` 접두사 (내부) — `onSelectNode`, `handleTabClick`

**Python:**
- 함수: snake_case — `get_node`, `get_node_places`
- 상수: UPPER_SNAKE_CASE — `MAX_NEIGHBORS_PER_TYPE`, `SEARCH_LIMIT`

**API 엔드포인트:**
- `GET /node/{node_id}` — 단일 노드 상세
- `GET /node/{node_id}/places` — 노드의 지리 장소 목록
- `GET /node/{node_id}/neighbors/grouped` — 타입별 그룹핑된 이웃
- `GET /events` — 전체 Event 목록
- `GET /search?q=` — 이름 검색

## Where to Add New Code

**새 API 엔드포인트:**
- 라우터 파일: `backend/app/routes/` 아래 기존 파일에 `@router.get(...)` 추가 (소규모) 또는 신규 파일 생성
- 신규 파일이면 `backend/app/main.py`에 `app.include_router(new_module.router)` 추가

**새 프론트엔드 뷰 (탭):**
- 컴포넌트: `frontend/src/NewView.jsx`
- `App.jsx`의 `TABS` 배열에 탭 항목 추가
- `App.jsx` JSX에 `activeView === 'newview'` 조건 렌더링 추가

**공유 색·라벨 상수:**
- 유일한 위치: `frontend/src/theme.js`
- 절대 개별 컴포넌트에 색 상수를 선언하지 말 것

**새 API fetch (프론트엔드):**
- 항상 `frontend/src/api.js`의 `apiGet()` 사용
- 직접 `fetch()` 호출 금지

**데이터 적재 스크립트:**
- 위치: `backend/scripts/`
- 서버 런타임 코드(`backend/app/`)와 혼재 금지

## Special Directories

**`frontend/dist/`:**
- Purpose: Vite 빌드 출력. nginx 컨테이너에 bind-mount (`./frontend/dist:/usr/share/nginx/html:ro`)
- Generated: Yes (`npm run build` 또는 `deploy.sh`)
- Committed: No

**`.forge/`:**
- Purpose: 작업 카드, ADR, 회고, 코드베이스 분석을 포함하는 프로젝트 관리 디렉터리
- Generated: 부분 (에이전트 + 수동)
- Committed: Yes

**`.claude/worktrees/`:**
- Purpose: Dynamic Workflow 에이전트가 사용하는 git worktree 격리 경로
- Generated: Yes (에이전트 실행 시)
- Committed: No

---

*Structure analysis: 2026-06-14*
