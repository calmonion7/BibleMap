---
last_mapped_commit: 06b4012804c00a45ea7dfda9761d014ac91b11fb
mapped: 2026-06-20
---

# BibleMap — 디렉터리 구조

## 최상위 레이아웃

```
/Users/calmonion/Project/BibleMap/
├── backend/               FastAPI 백엔드
├── frontend/              React SPA
├── data/                  런타임 오버레이 JSON (볼륨 마운트)
├── nginx/                 nginx 설정
├── .forge/                forge 워크플로우 메타데이터
├── .claude/               Claude Code 설정
├── docker-compose.yml     3-서비스 구성 (neo4j, api, nginx)
├── .env / .env.example    NEO4J_PASSWORD 등 환경변수
├── deploy.sh              배포 스크립트
├── CLAUDE.md              Claude 행동 지침
└── BIBLEMAP_PLAN.md       프로젝트 계획 문서
```

## `backend/`

```
backend/
├── Dockerfile             python:3.12-slim, uvicorn 진입점
├── requirements.txt       fastapi, neo4j, uvicorn (버전 고정)
├── __init__.py
├── app/
│   ├── __init__.py
│   ├── main.py            FastAPI 앱 생성, 라우터 등록, lifespan 인덱스 생성
│   ├── db.py              get_driver() — Neo4j 싱글톤 연결
│   └── routes/
│       ├── __init__.py
│       ├── nodes.py       /node/* /person/* 엔드포인트
│       ├── events.py      /events /event/{id}/verses 엔드포인트 + lru_cache
│       ├── books.py       /books 엔드포인트 + lru_cache
│       └── search.py      /search?q= 엔드포인트
└── scripts/               일회성 데이터 적재·생성 스크립트
    ├── load_theographic.py     Theographic GitHub JSON → Neo4j 노드·관계
    ├── load_books.py           Book 노드 + CONTAINS_BOOK 관계
    ├── load_authored_events.py authored=true Event 노드
    ├── load_verse_events.py    구절-사건 관계
    ├── inject_ko_names.py      nameKo 속성 주입
    ├── inject_person_traits.py traits JSON 주입
    ├── inject_book_context.py  background/themes/keyVerse 주입
    ├── generate_approx_book_verses.py  LLM → 추정 구절
    ├── generate_book_context.py        LLM → 권별 컨텍스트
    ├── generate_book_events.py         LLM → 책-사건 연결
    ├── generate_event_verses.py        LLM → 사건 근거 구절
    ├── generate_person_traits.py       LLM → 인물 성품
    ├── generate_verse_events.py        LLM → 구절-사건
    └── generate_verse_text.py          getbible API → 절 본문(ko/en) 미리 저장
```

### 명명 규칙 (backend)

- 라우터 파일: 엔티티/기능 단수 명사 (`nodes.py`, `events.py`, `books.py`, `search.py`).
- 스크립트: 동사_목적어 (`load_theographic.py`, `inject_ko_names.py`, `generate_book_events.py`).
- 내부 캐시 함수: 언더스코어 접두 `_load_*` / `_compute_*`.

## `frontend/`

```
frontend/
├── package.json           React 19, maplibre-gl, lucide-react; Vite 빌드
├── vite.config.js         manualChunks: maplibre / vendor 분리
├── eslint.config.js       eslint-plugin-react-hooks v7
├── index.html             SPA 진입 HTML
├── .env.production        VITE_API_URL=/api (빌드타임 주입)
├── public/
│   ├── favicon.svg        나침반 아이콘
│   └── icons.svg          UI 아이콘 스프라이트
└── src/
    ├── main.jsx           ReactDOM.createRoot 진입점
    ├── App.jsx            최상위 — 전역 상태, 탭 라우팅, 검색, 레이아웃
    ├── api.js             API_BASE + apiGet() 공유 클라이언트
    ├── theme.js           TYPE_COLOR, TYPE_KO, TYPE_ORDER, typeColor(), typeKo(), SELECT_HL
    ├── MapView.jsx        maplibre-gl 지도, 마커, 사건 링, Convex hull
    ├── TimelineView.jsx   타임라인 스크롤, 사건 그룹, 근거 구절 인라인
    ├── BibleOverviewView.jsx  장르별 책 카드 그리드
    ├── SidePanel.jsx      노드 상세 패널 (이웃, 성품, 근거 구절)
    ├── VerseLangTabs.jsx  한국어/영어 본문 전환 탭 컴포넌트
    ├── convexHull.js      Graham scan 구현 — 장소 군집 hull 계산
    └── index.css          전역 CSS (최소, 대부분 inline style)
```

### 명명 규칙 (frontend)

- 컴포넌트 파일: PascalCase (`MapView.jsx`, `SidePanel.jsx`, `VerseLangTabs.jsx`).
- 유틸·클라이언트: camelCase (`api.js`, `convexHull.js`, `theme.js`).
- 확장자: 컴포넌트 `.jsx`, 유틸 `.js`.
- 인라인 스타일 중심, 전역 CSS는 `index.css` 최소화.

## `data/`

Docker 볼륨으로 api 컨테이너에 `/app/data`로 마운트. 런타임 오버레이 전용 — Neo4j에 주입하지 않는 추정 데이터와 사전 계산 데이터.

```
data/
├── authored_events/
│   └── events.json        저작 사건 정의 (authored=true로 Neo4j 적재됨)
├── book_context/
│   └── books.json         권별 배경·주제·대표구절 (LLM 생성, inject_book_context.py로 Neo4j 주입)
├── book_events/
│   └── books.json         추정연도 책→연결 사건 오버레이 ({bookId:[eventId]})
├── book_years_approx/
│   └── books.json         추정연도 오버레이 ({bookId:{placementYear, basis}})
├── character_traits/
│   └── people.json        인물 성품 (inject_person_traits.py로 Neo4j 주입)
├── event_verses/
│   └── events.json        사건별 근거 구절 + textKo/textEn 사전 저장
├── names_ko/
│   ├── books.json
│   ├── events.json
│   ├── groups.json
│   ├── people.json
│   └── places.json        엔티티별 한글명 매핑 (inject_ko_names.py로 Neo4j 주입)
└── verse_events/
    ├── books.json
    ├── events.json
    └── people.json        구절-사건 연결 데이터
```

## `nginx/`

```
nginx/
└── nginx.conf    단일 server 블록:
                  /api/*  → proxy_pass http://api:8000/
                  /       → SPA fallback (try_files $uri /index.html)
                  정적 자산 max-age=31536000, index.html no-cache
```

## `.forge/`

forge 워크플로우 메타데이터. 실행 코드 없음.

```
.forge/
├── CONTEXT.md             도메인 용어집 (핵심 ADR·설계 결정 기록)
├── adr/                   0001~0006 Architecture Decision Records
├── backlog/               실행 대기 중인 계획 파일
├── done/                  완료된 태스크 (날짜-슬러그 디렉터리)
├── codebase/              코드베이스 매핑 문서 (이 파일 포함)
├── executed/              실행 완료 워크플로우
├── quick/LOG.md           빠른 작업 로그
├── reports/               감사·리뷰 리포트
└── retro/                 태스크별 회고 파일
```

## `.claude/`

```
.claude/
├── settings.json          bgIsolation: "none" (worktree 에이전트 파일 쓰기 허용)
├── settings.local.json    로컬 전용 설정
├── launch.json            앱 실행 설정
└── worktrees/             forge Dynamic Workflow 격리 워크트리
```

## 주요 파일 위치 요약

| 용도 | 경로 |
|------|------|
| FastAPI 앱 진입점 | `backend/app/main.py` |
| Neo4j 연결 | `backend/app/db.py` |
| 타임라인 API + 캐시 | `backend/app/routes/events.py` |
| 책 목록 API + 오버레이 | `backend/app/routes/books.py` |
| 노드 조회 API | `backend/app/routes/nodes.py` |
| 검색 API | `backend/app/routes/search.py` |
| React 진입점 | `frontend/src/main.jsx` |
| 전역 상태·탭 라우팅 | `frontend/src/App.jsx` |
| API 클라이언트 | `frontend/src/api.js` |
| 색상·레이블 팔레트 | `frontend/src/theme.js` |
| 지도 컴포넌트 | `frontend/src/MapView.jsx` |
| 타임라인 컴포넌트 | `frontend/src/TimelineView.jsx` |
| 책 오버뷰 컴포넌트 | `frontend/src/BibleOverviewView.jsx` |
| 노드 상세 패널 | `frontend/src/SidePanel.jsx` |
| 컨테이너 오케스트레이션 | `docker-compose.yml` |
| nginx 프록시 설정 | `nginx/nginx.conf` |
| 사건 근거 구절 오버레이 | `data/event_verses/events.json` |
| 추정연도 오버레이 | `data/book_years_approx/books.json` |
| 책-사건 연결 오버레이 | `data/book_events/books.json` |
| 도메인 용어집 + ADR | `.forge/CONTEXT.md` |
