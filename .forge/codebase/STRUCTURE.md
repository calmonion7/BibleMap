---
last_mapped_commit: 4ed4d876d7fa3b06a8eb1647b5b50ed73f906b25
mapped: 2026-06-19
---

# BibleMap 디렉터리 구조

## 최상위 레이아웃

```
BibleMap/
├── backend/          # FastAPI 백엔드 (Python 3.12)
├── frontend/         # React SPA (Vite + MapLibre GL)
├── nginx/            # Nginx 역방향 프록시 설정
├── data/             # JSON 오버레이 데이터 파일 (Docker 볼륨 마운트)
├── .forge/           # forge 워크플로우 산출물 (계획·ADR·메모리)
├── .claude/          # Claude Code 설정 (settings.json, 워크트리)
├── .github/          # GitHub Actions 워크플로우
├── docker-compose.yml
├── deploy.sh
├── .env              # NEO4J_PASSWORD 등 런타임 비밀
├── .env.example
├── CLAUDE.md
└── BIBLEMAP_PLAN.md
```

---

## 디렉터리별 상세

### `backend/`

FastAPI 애플리케이션. Docker 이미지로 빌드되어 포트 8000에서 실행된다.

```
backend/
├── Dockerfile              # python:3.12-slim, uvicorn 실행
├── requirements.txt        # fastapi, neo4j, uvicorn (고정 버전)
├── __init__.py
└── app/
    ├── __init__.py
    ├── main.py             # FastAPI 앱 객체, lifespan, CORS, 라우터 등록
    ├── db.py               # 싱글턴 Neo4j 드라이버 (get_driver)
    └── routes/
        ├── __init__.py
        ├── nodes.py        # /node/{id}, /node/{id}/places, /node/{id}/neighbors/grouped, /person/{id}/event-ids
        ├── events.py       # /events, /event/{id}/verses
        ├── books.py        # /books
        └── search.py       # /search?q=
```

`backend/scripts/` — 데이터 적재·생성 스크립트(운영 런타임과 무관, 개발·배포 시 수동 실행):

| 파일 | 역할 |
|---|---|
| `load_theographic.py` | Theographic 원본 데이터 → Neo4j 적재 |
| `load_books.py` | 성경 책 목록 적재 |
| `load_verse_events.py` | 구절-사건 관계 적재 |
| `load_authored_events.py` | 저자 사건 적재 |
| `inject_ko_names.py` | 한글 이름 주입 |
| `inject_book_context.py` | 책 컨텍스트 주입 |
| `inject_person_traits.py` | 인물 특성 주입 |
| `generate_*.py` | JSON 오버레이 파일 생성 (data/ 산출) |

---

### `frontend/`

Vite 빌드 결과물(`dist/`)을 Nginx가 정적 서빙한다. HMR 불가 — 변경 후 `npm run build` 필요.

```
frontend/
├── index.html              # HTML 진입점 (<div id="root">)
├── vite.config.js          # Vite 빌드 설정
├── package.json            # 의존성: react 19, maplibre-gl 5, lucide-react
├── eslint.config.js
├── .env.production         # VITE_API_URL=/api (빌드타임 주입)
├── dist/                   # 빌드 산출물 (Nginx 마운트 대상)
└── src/
    ├── main.jsx            # React DOM 마운트 진입점
    ├── App.jsx             # 최상위 상태·레이아웃·검색·라우팅
    ├── MapView.jsx         # MapLibre GL 지도 뷰
    ├── TimelineView.jsx    # 수평 타임라인 뷰
    ├── SidePanel.jsx       # 노드 상세 패널 (이웃·구절)
    ├── VerseLangTabs.jsx   # 성경 구절 언어 탭(ko/en) 공유 UI
    ├── api.js              # apiGet() 헬퍼, VITE_API_URL 기반 base URL
    ├── theme.js            # 노드 타입 색상·순서·한글 라벨 상수
    ├── convexHull.js       # 장소 군집 볼록껍질 알고리즘
    └── index.css           # 전역 스타일
```

---

### `data/`

런타임 JSON 오버레이 파일. `docker-compose.yml`에서 `./data:/app/data` 볼륨으로 마운트된다. `backend/scripts/generate_*.py`로 생성한다.

```
data/
├── event_verses/
│   └── events.json         # {eventId: {books: [{bookId, verseRanges}]}} — 구절 드릴다운
├── book_events/
│   └── books.json          # {bookId: [eventId, ...]} — 책→사건 추정 연결
├── book_years_approx/
│   └── books.json          # {bookId: {placementYear, basis}} — 추정 연도
├── authored_events/        # 저자 사건 데이터
├── book_context/           # 책 컨텍스트 데이터
├── character_traits/       # 인물 특성 원본
├── names_ko/               # 한글 이름 매핑
└── verse_events/           # 구절-사건 매핑 원본
```

---

### `nginx/`

```
nginx/
└── nginx.conf              # /api/ 프록시, SPA try_files, 정적 캐시 정책
```

---

### `.forge/`

forge 워크플로우 디렉터리.

```
.forge/
├── CONTEXT.md              # 프로젝트 도메인 컨텍스트 (도메인 용어·결정)
├── adr/                    # Architecture Decision Records
├── backlog/                # 실행 대기 계획 슬러그 파일
├── done/                   # 완료된 태스크 아카이브
├── executed/               # 실행된 계획 파일
├── quick/                  # 빠른 메모
├── retro/                  # 회고 로그
└── codebase/               # 코드베이스 매핑 문서 (이 파일 포함)
```

---

## 주요 파일 위치 요약

| 역할 | 경로 |
|---|---|
| FastAPI 앱 객체 | `backend/app/main.py` |
| DB 연결 | `backend/app/db.py` |
| API 라우터 (노드) | `backend/app/routes/nodes.py` |
| API 라우터 (사건) | `backend/app/routes/events.py` |
| API 라우터 (책) | `backend/app/routes/books.py` |
| API 라우터 (검색) | `backend/app/routes/search.py` |
| React 마운트 | `frontend/src/main.jsx` |
| 앱 최상위 | `frontend/src/App.jsx` |
| API 클라이언트 | `frontend/src/api.js` |
| 색상·테마 상수 | `frontend/src/theme.js` |
| Nginx 설정 | `nginx/nginx.conf` |
| Docker 오케스트레이션 | `docker-compose.yml` |
| 배포 스크립트 | `deploy.sh` |
| 런타임 비밀 | `.env` |

---

## 명명 규칙

| 대상 | 규칙 | 예시 |
|---|---|---|
| 프론트엔드 컴포넌트 | PascalCase `.jsx` | `MapView.jsx`, `SidePanel.jsx` |
| 프론트엔드 유틸 | camelCase `.js` | `api.js`, `theme.js`, `convexHull.js` |
| 백엔드 라우터 모듈 | snake_case `.py` (복수형 리소스) | `nodes.py`, `events.py`, `books.py` |
| 백엔드 스크립트 | `load_*.py` / `generate_*.py` / `inject_*.py` | 역할 접두어로 동작 명시 |
| Neo4j 속성 | camelCase | `theographic_id`, `nameKo`, `bookOrder` |
| Neo4j 관계 | UPPER_SNAKE_CASE | `HAS_PARTICIPANT`, `OCCURS_AT`, `CONTAINS_BOOK` |
| JSON 오버레이 파일 | 단수형 디렉터리 + `books.json` / `events.json` | `event_verses/events.json` |
