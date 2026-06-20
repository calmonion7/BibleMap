---
last_mapped_commit: 7522aafe2088e83e8c4bed86a4f0269082db07e0
mapped: 2026-06-20
---

# 디렉터리 구조

## 전체 레이아웃

```
BibleMap/
├── backend/                # FastAPI 백엔드
│   ├── app/                # 애플리케이션 패키지
│   │   ├── main.py         # FastAPI 앱 생성·CORS·lifespan
│   │   ├── db.py           # Neo4j 드라이버 싱글턴
│   │   ├── overlays.py     # JSON 오버레이 파일 로더(lru_cache)
│   │   └── routes/         # API 라우터 모듈
│   │       ├── nodes.py    # /node/* · /person/* 엔드포인트
│   │       ├── events.py   # /events · /event/* 엔드포인트
│   │       ├── books.py    # /books · /books-overview 엔드포인트
│   │       └── search.py   # /search 엔드포인트
│   ├── scripts/            # Neo4j 데이터 적재·생성 스크립트(일회성)
│   ├── Dockerfile          # python:3.12-slim, uvicorn 실행
│   └── requirements.txt    # fastapi · neo4j · uvicorn 3종
│
├── frontend/               # React 19 SPA (Vite)
│   ├── src/
│   │   ├── main.jsx        # React 진입점(createRoot)
│   │   ├── App.jsx         # 루트 컴포넌트·전역 상태·네비게이션
│   │   ├── MapView.jsx     # MapLibre GL 지도 뷰
│   │   ├── TimelineView.jsx# 타임라인 뷰
│   │   ├── BibleOverviewView.jsx # 성경 개요 뷰
│   │   ├── SidePanel.jsx   # 노드 상세 오버레이 패널
│   │   ├── VerseLangTabs.jsx     # 한/영 절 본문 언어 전환 탭
│   │   ├── Spinner.jsx     # 로딩 스피너
│   │   ├── api.js          # 공유 fetch 클라이언트(API_BASE + apiGet)
│   │   ├── theme.js        # 타입 색·라벨·순서 팔레트
│   │   ├── convexHull.js   # Graham scan 볼록 껍질
│   │   ├── useNodeSelection.js   # 노드 선택·히스토리·메타 훅
│   │   ├── useSearch.js    # 검색 디바운스·필터 훅
│   │   ├── index.css       # 전역 CSS 리셋
│   │   └── assets/         # 정적 에셋(hero.png 등)
│   ├── public/             # Vite public 루트(favicon 등)
│   ├── dist/               # 프로덕션 빌드 출력 (gitignored)
│   ├── vite.config.js      # Vite 설정(maplibre-gl 청크 분리)
│   ├── eslint.config.js    # ESLint(react-hooks, react-refresh)
│   └── package.json        # 의존성 목록
│
├── data/                   # JSON 오버레이 파일(컨테이너: /app/data 마운트)
│   ├── book_events/
│   │   └── books.json      # {bookId: [eventId]} — 성경책→사건 매핑
│   ├── book_years_approx/
│   │   └── books.json      # {bookId: {placementYear, basis}} — 추정 연도
│   ├── event_verses/
│   │   └── events.json     # {eventId: {books:[{bookId, verses:[...]}]}} — 근거 구절
│   ├── authored_events/    # 인물별 저작 사건 JSON (로드 스크립트 입력)
│   ├── book_context/       # 성경책 시대적 배경 텍스트
│   ├── character_traits/   # 인물 성품 데이터
│   ├── names_ko/           # 한글 이름 매핑
│   ├── person_events/      # 인물별 사건 연결 데이터
│   ├── place_coords/       # 장소 좌표 보완 데이터
│   └── verse_events/       # 구절→사건 역매핑 데이터
│
├── nginx/
│   └── nginx.conf          # /api/ 프록시 + 정적 파일 서빙 + SPA fallback
│
├── .forge/                 # GSD 워크플로 메타데이터
│   ├── codebase/           # 코드베이스 분석 문서(이 파일 위치)
│   ├── done/               # 완료된 태스크 기록
│   ├── backlog/            # 대기 중인 태스크
│   ├── adr/                # 아키텍처 의사결정 기록
│   ├── retro/              # 회고 문서
│   ├── reports/            # 실행 리포트
│   └── CONTEXT.md          # 프로젝트 도메인 용어·배경
│
├── .github/
│   └── workflows/
│       └── deploy.yml      # 자기 호스팅 러너 자동 배포(main 브랜치 push)
│
├── docker-compose.yml      # neo4j · api · nginx 3 서비스
├── deploy.sh               # git pull + 빌드 + docker compose up
├── CLAUDE.md               # Claude 행동 지침
└── .env                    # NEO4J_PASSWORD 설정(gitignored)
```

## 디렉터리 목적 상세

### `backend/app/routes/`
라우터 모듈 4개가 역할별로 분리된다. 새 엔드포인트 추가 시 역할에 맞는 파일에 `@router.get()` 핸들러를 추가하고, `main.py`에 `app.include_router()`를 추가하면 된다.

### `backend/scripts/`
Neo4j 최초 적재 및 오버레이 데이터 생성 스크립트. 운영 API와 무관하게 일회성 또는 수동으로 실행된다. 컨테이너 이미지에는 포함되지 않는다(`Dockerfile`에서 `app/`만 복사).

### `data/`
오버레이 JSON 파일. `docker-compose.yml`에서 `./data:/app/data` 볼륨 마운트로 컨테이너에 제공된다. `overlays.py`가 `DATA_DIR` 환경변수를 먼저 탐색하고, 없으면 저장소 루트 `data/`를 폴백으로 사용한다. 직접 수정 또는 스크립트로 생성 후 API를 재시작(lru_cache 초기화)해야 반영된다.

### `frontend/src/`
모든 React 소스가 단일 `src/` 디렉터리 아래 있다. 하위 디렉터리 없이 평탄(flat) 구조를 유지한다. 파일 수가 17개로 작아 이 구조가 유지된다.

### `frontend/dist/`
Vite 프로덕션 빌드 출력. nginx가 이 경로를 마운트해 정적 파일을 서빙한다. git에 추적되지 않으며(`.gitignore`), `deploy.sh`에서 `npm run build`로 재생성된다.

## 파일 명명 규칙

**프론트엔드:**
- 컴포넌트: `PascalCase.jsx` (예: `MapView.jsx`, `SidePanel.jsx`)
- 커스텀 훅: `use` 접두사 + `camelCase.js` (예: `useNodeSelection.js`, `useSearch.js`)
- 유틸리티: `camelCase.js` (예: `convexHull.js`, `api.js`, `theme.js`)

**백엔드:**
- 라우터 모듈: 도메인 복수형 소문자 (예: `nodes.py`, `events.py`, `books.py`)
- 스크립트: `동사_목적어.py` (예: `load_theographic.py`, `generate_book_events.py`, `inject_ko_names.py`)

**데이터:**
- 오버레이 파일: 도메인 단수/복수 폴더 + `books.json` 또는 `events.json`
- 인물별 파일: `{name}.json` 소문자 (예: `abraham.json`, `jesus.json`)

## 새 코드 추가 위치

**새 API 엔드포인트:**
- 역할에 맞는 `backend/app/routes/{module}.py`에 `@router.get()` 핸들러 추가
- 새 도메인이면 신규 라우터 파일 생성 후 `backend/app/main.py`에 `app.include_router()` 추가

**새 프론트엔드 뷰:**
- `frontend/src/{ViewName}View.jsx` 생성
- `App.jsx`의 `TABS` 배열과 뷰 조건부 렌더링 블록에 추가

**새 오버레이 데이터:**
- `data/{category}/` 디렉터리 생성 후 JSON 파일 배치
- `backend/app/overlays.py`에 `@lru_cache` 로더 함수 추가

**새 커스텀 훅:**
- `frontend/src/use{Name}.js` 생성
- `App.jsx`에서 구조분해 후 필요한 컴포넌트에 prop으로 전달

**공유 유틸리티:**
- `api.js` — fetch 패턴 변경 시
- `theme.js` — 새 노드 타입 색/라벨 추가 시

## 모듈 경계

- 백엔드 라우터는 `db.py`와 `overlays.py`에만 의존한다. 라우터 간 직접 임포트는 없다.
- 프론트엔드 컴포넌트는 `api.js`와 `theme.js`를 공통 임포트로 사용한다. 컴포넌트 간 직접 임포트는 없다(SidePanel이 VerseLangTabs를 임포트하는 것이 유일한 예외).
- `App.jsx`가 모든 상태를 소유하고 컴포넌트에 prop으로 전달하는 단방향 흐름이다. 커스텀 훅(`useNodeSelection`, `useSearch`)은 상태 로직만 캡슐화하고 컴포넌트 트리와 무관하다.
