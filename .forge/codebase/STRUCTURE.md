---
last_mapped_commit: 9f47b78ed927ef302cefffb5b62ef71885b6aa94
mapped: 2026-06-19
---

# BibleMap 디렉토리 구조

## 최상위 레이아웃

```
BibleMap/
├── backend/          FastAPI 백엔드 (Python)
├── data/             정적 데이터 JSON (Docker 볼륨 마운트 대상)
├── frontend/         React 프론트엔드 (Vite)
├── nginx/            nginx 설정
├── .claude/          Claude Code 설정 및 워크트리
├── .forge/           forge 작업 관리 디렉토리
├── .github/          GitHub Actions 워크플로우
├── .env              NEO4J_PASSWORD 등 환경변수 (git 제외)
├── .env.example      환경변수 템플릿
├── docker-compose.yml 서비스 정의 (neo4j, api, nginx)
├── deploy.sh         프로덕션 배포 스크립트
├── CLAUDE.md         Claude Code 지침
├── BIBLEMAP_PLAN.md  프로젝트 계획 문서
└── README.md
```

---

## `backend/`

```
backend/
├── Dockerfile        python:3.12-slim, WORKDIR /app, uvicorn 진입
├── requirements.txt  fastapi, neo4j, uvicorn (고정 버전)
├── __init__.py
├── app/
│   ├── __init__.py
│   ├── main.py       FastAPI app 생성, 라우터 등록, 기동 시 Neo4j 인덱스 생성
│   ├── db.py         get_driver() — 전역 싱글턴 Neo4j 드라이버
│   └── routes/
│       ├── __init__.py
│       ├── nodes.py  GET /node/{id}, /node/{id}/places, /node/{id}/neighbors/grouped, /person/{id}/event-ids
│       ├── events.py GET /events, /event/{id}/verses
│       ├── search.py GET /search
│       └── books.py  GET /books
└── scripts/
    ├── __init__.py
    ├── load_theographic.py     Theographic JSON → Neo4j 초기 적재
    ├── load_books.py           Book 노드 + CONTAINS_BOOK 관계 생성
    ├── load_authored_events.py data/authored_events → Neo4j Event 노드
    ├── load_verse_events.py    data/verse_events → Neo4j 적재
    ├── inject_ko_names.py      data/names_ko/*.json → 노드 nameKo 속성 주입 (deploy.sh 호출)
    ├── inject_person_traits.py data/character_traits → Person.traits 주입
    ├── inject_book_context.py  data/book_context → Book 속성 주입
    ├── generate_person_traits.py  LLM → character_traits 생성
    ├── generate_book_context.py   LLM → book_context 생성
    ├── generate_book_events.py    LLM → book_events 생성
    ├── generate_approx_book_verses.py LLM → book_years_approx 보강
    ├── generate_event_verses.py   LLM → event_verses 초안
    ├── generate_verse_events.py   LLM → verse_events 생성
    └── generate_verse_text.py     getbible.net 빌드타임 fetch → textKo/textEn 주입
```

### 네이밍 컨벤션 (backend)

- **라우터 파일**: 복수형 엔티티명 (`nodes.py`, `events.py`, `books.py`) 또는 기능명 (`search.py`)
- **로더 스크립트**: `load_<대상>.py` — Neo4j에 적재하는 스크립트
- **주입 스크립트**: `inject_<대상>.py` — 기존 노드에 속성을 추가하는 스크립트
- **생성 스크립트**: `generate_<대상>.py` — LLM 또는 외부 API로 데이터 파일을 만드는 스크립트

---

## `data/`

```
data/
├── authored_events/
│   └── events.json       저작 사건 정의 (authored:true Event 노드 원본)
├── book_context/
│   └── books.json        Book별 background·themes·keyVerse·절 본문(textKo/textEn)
├── book_events/
│   └── books.json        추정책 → 사건 약연결 오버레이 ({bookId: [eventId,...]})
├── book_years_approx/
│   └── books.json        startYear 없는 Book의 placementYear 추정값 오버레이
├── character_traits/
│   └── people.json       Person별 traits 배열 (trait·verse_ref·description·textKo/textEn)
├── event_verses/
│   └── events.json       Event별 근거 구절 + 절 본문 (textKo/textEn 인라인, ~130K 줄)
├── names_ko/
│   ├── books.json        Book 한국어 이름
│   ├── events.json       Event 한국어 이름
│   ├── groups.json       PeopleGroup 한국어 이름
│   ├── people.json       Person 한국어 이름
│   └── places.json       Place 한국어 이름
└── verse_events/
    └── events.json       구절 → 사건 매핑
```

### 네이밍 컨벤션 (data)

- 디렉토리: `<엔티티_복수형>_<설명>` (`book_events`, `book_years_approx`) 또는 `<엔티티_복수형>` (`authored_events`)
- 파일: 항상 엔티티 복수형 (`events.json`, `books.json`, `people.json`)
- 이 디렉토리는 `docker-compose.yml`에서 `./data:/app/data`로 마운트된다 — JSON만 교체하면 api 재시작 없이 다음 캐시 miss 시 반영

---

## `frontend/`

```
frontend/
├── index.html        SPA 루트 HTML (Vite 진입점)
├── package.json      의존성: react 19, react-dom 19, maplibre-gl 5, lucide-react
├── vite.config.js    빌드 설정 (manualChunks: maplibre → 별도 청크, 나머지 vendor)
├── eslint.config.js
├── .env.production   VITE_API_URL=/api (빌드타임 주입)
├── .gitignore
├── public/
│   ├── favicon.svg   나침반 아이콘
│   └── icons.svg     UI 아이콘 스프라이트
├── src/
│   ├── main.jsx      ReactDOM.createRoot 진입점
│   ├── App.jsx       최상위 컴포넌트, 전역 상태 관리, 레이아웃
│   ├── api.js        apiGet() 헬퍼, VITE_API_URL 기반 단일 fetch 클라이언트
│   ├── theme.js      TYPE_COLOR·TYPE_KO·TYPE_ORDER·SELECT_HL 공유 팔레트
│   ├── convexHull.js Graham scan 볼록 껍질 유틸리티 (좌표 배열 → 폴리곤)
│   ├── MapView.jsx   maplibre-gl 지도 뷰, 마커·링·볼록 껍질 렌더링
│   ├── TimelineView.jsx 타임라인 뷰, 사건 그룹화·구절 인라인 펼침
│   ├── SidePanel.jsx 노드 상세 패널 (우측 슬라이드인 / 모바일 하단 시트)
│   ├── VerseLangTabs.jsx 한국어/영어 절 본문 언어 전환 탭 (공유 컴포넌트)
│   ├── index.css     전역 CSS 리셋
│   └── assets/       정적 이미지 (hero.png 등)
└── dist/             Vite 빌드 산출물 (nginx 마운트 대상, git 제외)
```

### 네이밍 컨벤션 (frontend/src)

- **컴포넌트 파일**: PascalCase (`MapView.jsx`, `SidePanel.jsx`, `VerseLangTabs.jsx`)
- **유틸리티 파일**: camelCase (`api.js`, `theme.js`, `convexHull.js`)
- 확장자: JSX 컴포넌트는 `.jsx`, 순수 JS 유틸리티는 `.js`

---

## `nginx/`

```
nginx/
└── nginx.conf    단일 server 블록, /api/ 프록시 + SPA fallback
```

---

## `.forge/`

```
.forge/
├── CONTEXT.md        도메인 용어집 (Theographic ID, Book, 추정연도 등)
├── adr/              Architecture Decision Records
│   ├── 0001-no-apoc-own-loader.md
│   ├── 0002-timeline-event-evidence-model.md
│   ├── 0003-prebake-bilingual-verse-text.md
│   ├── 0004-estimated-data-runtime-overlay-not-neo4j.md
│   ├── 0005-authored-events-marked-neo4j-nodes.md
│   └── 0006-data-generation-llm-direct-not-script.md
├── backlog/          실행 대기 중인 forge 태스크 플랜
├── done/             완료된 forge 태스크 (날짜-슬러그 디렉토리)
├── executed/         실행된 워크플로우 기록
├── codebase/         코드베이스 분석 문서 (이 파일 위치)
├── retro/            태스크별 회고 로그 (날짜-슬러그.md)
└── quick/
    └── LOG.md        빠른 작업 로그
```

---

## `.github/`

```
.github/
└── workflows/
    └── deploy.yml    self-hosted runner, main 브랜치 push → deploy.sh 실행
```

---

## `.claude/`

```
.claude/
├── settings.json       Claude Code 프로젝트 설정 (bgIsolation: "none" 포함)
├── settings.local.json 로컬 오버라이드
├── launch.json
└── worktrees/          forge Dynamic Workflow 격리 워크트리
```

---

## 주요 파일 위치 요약

| 목적 | 경로 |
|---|---|
| FastAPI 앱 객체 | `backend/app/main.py` |
| Neo4j 드라이버 | `backend/app/db.py` |
| 노드 상세 API | `backend/app/routes/nodes.py` |
| 이벤트/구절 API | `backend/app/routes/events.py` |
| 책 목록 API | `backend/app/routes/books.py` |
| 검색 API | `backend/app/routes/search.py` |
| 전역 상태 컴포넌트 | `frontend/src/App.jsx` |
| API fetch 헬퍼 | `frontend/src/api.js` |
| 색·라벨 팔레트 | `frontend/src/theme.js` |
| 지도 컴포넌트 | `frontend/src/MapView.jsx` |
| 타임라인 컴포넌트 | `frontend/src/TimelineView.jsx` |
| 사이드패널 | `frontend/src/SidePanel.jsx` |
| Vite 빌드 설정 | `frontend/vite.config.js` |
| nginx 프록시 설정 | `nginx/nginx.conf` |
| Docker Compose | `docker-compose.yml` |
| 배포 스크립트 | `deploy.sh` |
| 도메인 용어집 | `.forge/CONTEXT.md` |
| 사건별 근거 구절 오버레이 | `data/event_verses/events.json` |
| 추정책 연도 오버레이 | `data/book_years_approx/books.json` |
| 추정책-사건 연결 오버레이 | `data/book_events/books.json` |
| 저작 사건 원본 | `data/authored_events/events.json` |
| 한국어 이름 원본 | `data/names_ko/*.json` |
