---
last_mapped_commit: ecdb7cb2ea1bf665b0690e62b4cf51261761072c
mapped: 2026-06-15
---

# 디렉터리 구조

## 전체 레이아웃

```
BibleMap/
├── backend/                      # Python FastAPI 서버
│   ├── app/                      # 배포 대상 앱 패키지
│   │   ├── main.py               # FastAPI 앱 초기화, CORS, lifespan 훅
│   │   ├── db.py                 # Neo4j 드라이버 싱글톤
│   │   └── routes/               # 라우터 모듈
│   │       ├── nodes.py          # /node/* 엔드포인트
│   │       ├── events.py         # /events 엔드포인트
│   │       └── search.py         # /search 엔드포인트
│   ├── scripts/                  # 일회성 데이터 파이프라인 (런타임 외)
│   │   ├── load_theographic.py   # Theographic GitHub JSON → Neo4j 배치 적재
│   │   ├── load_books.py         # Book 노드 적재 + CONTAINS_BOOK 관계 생성
│   │   ├── inject_ko_names.py    # data/names_ko/ → Neo4j nameKo/aliasesKo 주입
│   │   ├── inject_person_traits.py  # data/character_traits/ → Person.traits 주입
│   │   ├── inject_book_context.py   # data/book_context/ → Book 속성 주입
│   │   ├── generate_book_context.py # LLM으로 book_context JSON 생성
│   │   └── generate_person_traits.py# LLM으로 character_traits JSON 생성
│   ├── Dockerfile                # python:3.12-slim, uvicorn CMD
│   └── requirements.txt          # fastapi==0.136.3, neo4j==6.2.0, uvicorn==0.49.0
│
├── frontend/                     # React 19 SPA (Vite 8)
│   ├── src/
│   │   ├── main.jsx              # ReactDOM 루트 마운트
│   │   ├── App.jsx               # 루트 컴포넌트, 전역 상태, 검색, 탭 라우팅
│   │   ├── MapView.jsx           # maplibre-gl 지도, 마커, 이벤트 링, hull
│   │   ├── TimelineView.jsx      # 연대기 목록, startDate 그룹핑, Book 필터
│   │   ├── SidePanel.jsx         # 노드 상세, 이웃 그룹, Person traits, Book 상세
│   │   ├── api.js                # API_BASE + apiGet() 헬퍼
│   │   ├── theme.js              # TYPE_COLOR, TYPE_KO, TYPE_ORDER, SELECT_HL
│   │   ├── convexHull.js         # Graham scan 볼록 껍질 순수 함수
│   │   ├── App.css               # App 컴포넌트 스타일
│   │   ├── index.css             # 글로벌 스타일
│   │   └── assets/               # 정적 에셋
│   ├── public/
│   │   ├── favicon.svg           # BibleMap 컴파스+십자가 아이콘
│   │   └── icons.svg
│   ├── dist/                     # Vite 빌드 출력 (git 미추적, nginx bind-mount)
│   ├── index.html                # SPA 진입 HTML
│   ├── vite.config.js            # Vite 설정 (react 플러그인만)
│   ├── eslint.config.js
│   ├── .env.production           # VITE_API_URL=/api (빌드타임 주입)
│   └── package.json
│
├── nginx/
│   └── nginx.conf                # /api/* 프록시 + SPA fallback + 캐시 헤더
│
├── data/
│   ├── names_ko/                 # theographic_id → 한국어 이름 매핑 JSON
│   │   ├── people.json
│   │   ├── places.json
│   │   ├── events.json
│   │   └── groups.json
│   ├── character_traits/
│   │   └── people.json           # Person traits 배열 ({trait, verse_ref, description})
│   └── book_context/
│       └── books.json            # Book background/themes/keyVerse
│
├── .forge/                       # forge 워크플로우 프로젝트 관리
│   ├── CONTEXT.md                # 도메인 용어집
│   ├── codebase/                 # 코드베이스 분석 문서 (이 파일 위치)
│   ├── backlog/                  # 대기 중인 작업 카드
│   ├── done/                     # 완료된 작업 기록
│   ├── executed/                 # 실행된 워크플로우 기록
│   ├── adr/                      # Architecture Decision Records
│   ├── retro/                    # 회고 기록
│   └── quick/                    # 빠른 메모 (LOG.md)
│
├── .claude/
│   ├── settings.json             # Claude Code 설정 (bgIsolation: "none")
│   └── settings.local.json
│
├── docker-compose.yml            # neo4j + api + nginx 3-서비스 구성
├── deploy.sh                     # 프로덕션 배포: build → compose up → inject
├── .env                          # NEO4J_PASSWORD (git 미추적)
├── .env.example                  # 환경변수 템플릿
├── CLAUDE.md                     # LLM 행동 가이드라인
└── BIBLEMAP_PLAN.md              # 초기 프로젝트 계획 문서
```

**GraphView.jsx는 존재하지 않음** — `7500fec`에서 완전 제거됨. 탭은 `map`, `timeline` 두 개만.

## 주요 파일 위치

**진입점:**
- `frontend/src/main.jsx` — React 앱 루트
- `backend/app/main.py` — FastAPI 앱 객체(`app`)
- `frontend/index.html` — SPA HTML 셸

**설정:**
- `docker-compose.yml` — 전체 서비스 구성 (neo4j, api, nginx)
- `nginx/nginx.conf` — 리버스 프록시 + SPA fallback + 캐시 헤더
- `backend/requirements.txt` — Python 의존성
- `frontend/package.json` — Node.js 의존성
- `frontend/.env.production` — `VITE_API_URL=/api` (프로덕션 빌드용)

**핵심 로직:**
- `backend/app/routes/nodes.py` — 노드 조회·이웃·장소 엔드포인트 (레이블별 Cypher 분기)
- `backend/app/routes/search.py` — 전문 검색 (CONTAINS + rank 정렬)
- `backend/app/db.py` — Neo4j 연결 관리
- `frontend/src/App.jsx` — 전역 상태, 검색 디바운스(250ms), 탭 라우팅
- `frontend/src/MapView.jsx` — 지도 + 사건 링 애니메이션 + convex hull
- `frontend/src/theme.js` — 뷰 공유 색·라벨 팔레트 (유일한 정의처)

**데이터 파이프라인 (스크립트):**
- `backend/scripts/load_theographic.py` — Person/Place/Event/PeopleGroup 적재
- `backend/scripts/load_books.py` — Book 적재 + CONTAINS_BOOK 관계
- `backend/scripts/inject_ko_names.py` — `deploy.sh`에서 자동 실행
- `backend/scripts/inject_person_traits.py` — 수동 실행
- `backend/scripts/inject_book_context.py` — 수동 실행

**정적 데이터 (수동 관리, git 추적):**
- `data/names_ko/` — 한국어 이름 매핑 JSON
- `data/character_traits/people.json` — Person traits
- `data/book_context/books.json` — Book context

**테스트:** 없음.

## 네이밍 컨벤션

**파일:**
- React 컴포넌트: PascalCase `.jsx` — `MapView.jsx`, `SidePanel.jsx`
- 공유 유틸 모듈: camelCase `.js` — `api.js`, `theme.js`, `convexHull.js`
- Python 모듈: snake_case `.py` — `nodes.py`, `load_theographic.py`

**디렉터리:** 소문자 snake_case — `names_ko/`, `book_context/`, `character_traits/`

**React 컴포넌트:**
- 컴포넌트 함수: PascalCase
- props 핸들러: `on` 접두사 — `onSelectNode`, `onNodeLoaded`
- 내부 핸들러: `handle` 접두사 — `handleTabClick`, `handleSelectResult`

**Python:**
- 함수: snake_case — `get_node`, `get_node_places`
- 상수: UPPER_SNAKE_CASE — `MAX_NEIGHBORS_PER_TYPE`, `SEARCH_LIMIT`, `NODE_NEIGHBOR_LIMIT`

**API 엔드포인트:**
- `GET /node/{node_id}` — 단일 노드 상세
- `GET /node/{node_id}/places` — 노드의 지리 장소 목록
- `GET /node/{node_id}/neighbors/grouped` — 타입별 그룹핑된 이웃
- `GET /events` — 전체 Event 목록
- `GET /search?q=` — 이름 검색

## 새 코드를 추가할 위치

**새 API 엔드포인트:**
- 기존 라우터 파일(`backend/app/routes/`)에 `@router.get(...)` 추가
- 신규 파일이면 `backend/app/main.py`에 `app.include_router(new_module.router)` 추가

**새 프론트엔드 탭 뷰:**
- `frontend/src/NewView.jsx` 생성
- `App.jsx`의 `TABS` 배열에 탭 항목 추가
- `App.jsx` JSX에 `activeView === 'newview'` 조건 렌더링 추가

**타입 색·라벨 상수:** 반드시 `frontend/src/theme.js`에만 정의. 컴포넌트 내부 선언 금지.

**프론트 API fetch:** `frontend/src/api.js`의 `apiGet()` 사용 권장. `MapView.jsx`·`SidePanel.jsx`는 아직 내부 `API_URL` + 직접 `fetch()` 패턴이 남아 있음(부분 마이그레이션 상태).

**데이터 적재 스크립트:** `backend/scripts/` — `backend/app/`과 혼재 금지.

## 특수 디렉터리

**`frontend/dist/`:** Vite 빌드 출력. nginx 컨테이너에 bind-mount (`./frontend/dist:/usr/share/nginx/html:ro`). git 미추적.

**`.forge/`:** forge 워크플로우 프로젝트 관리. ADR·회고·작업 카드 포함. git 추적.

**`.claude/worktrees/`:** Dynamic Workflow 에이전트가 사용하는 git worktree 격리 경로. git 미추적.
