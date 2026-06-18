---
last_mapped_commit: 6f2cfc1bf163d7327bd86773676223624fa53ff2
mapped: 2026-06-18
---

# BibleMap — 디렉터리 구조

## 최상위 레이아웃

```
BibleMap/
├── backend/          # FastAPI + 데이터 적재 스크립트
├── frontend/         # React SPA (Vite 빌드)
├── data/             # 런타임 오버레이 JSON + 빌드타임 생성 데이터
├── nginx/            # nginx 설정
├── .forge/           # forge 워크플로우 (ADR, CONTEXT, 백로그, 회고)
├── .claude/          # Claude Code 설정 (settings.json, 워크트리)
├── docker-compose.yml
├── deploy.sh
├── .env              # NEO4J_PASSWORD (git 제외)
├── .env.example
├── CLAUDE.md
└── BIBLEMAP_PLAN.md
```

## `backend/` — FastAPI 애플리케이션

```
backend/
├── Dockerfile                    # python:3.12-slim, uvicorn CMD
├── requirements.txt              # fastapi, neo4j, uvicorn (고정 버전)
├── __init__.py
├── app/
│   ├── __init__.py
│   ├── main.py                   # FastAPI 앱 생성, 미들웨어, 라우터 등록, lifespan
│   ├── db.py                     # Neo4j 드라이버 싱글턴 (get_driver)
│   └── routes/
│       ├── __init__.py
│       ├── nodes.py              # GET /node/{id}, /node/{id}/places, /node/{id}/neighbors/grouped
│       ├── events.py             # GET /events, /event/{id}/verses
│       ├── search.py             # GET /search?q=
│       └── books.py              # GET /books
└── scripts/                      # 일회성 데이터 파이프라인 스크립트 (런타임과 무관)
    ├── __init__.py
    ├── load_theographic.py       # Theographic GitHub JSON → Neo4j (Person/Place/Event/PeopleGroup)
    ├── load_books.py             # books.json → Neo4j Book 노드 + CONTAINS_BOOK 관계
    ├── load_authored_events.py   # 저작 사건 Event 노드 적재 (authored:true)
    ├── inject_ko_names.py        # data/names_ko/ → Neo4j nameKo 속성
    ├── inject_person_traits.py   # data/character_traits/ → Neo4j traits 속성
    ├── inject_book_context.py    # data/book_context/ → Neo4j background/themes/keyVerse 속성
    ├── generate_approx_book_verses.py  # 추정책 구절 데이터 생성
    ├── generate_book_context.py  # book_context JSON 생성 (LLM 이용)
    ├── generate_book_events.py   # book_events JSON 생성 (LLM 이용)
    ├── generate_event_verses.py  # event_verses JSON 생성
    ├── generate_person_traits.py # character_traits JSON 생성 (LLM 이용)
    └── generate_verse_text.py    # 구절 본문 프리베이크 (getbible API 호출)
```

## `frontend/` — React SPA

```
frontend/
├── package.json                  # react 19, maplibre-gl 5, lucide-react
├── vite.config.js                # Vite 빌드 설정, manualChunks (maplibre/vendor)
├── eslint.config.js
├── index.html                    # SPA 진입 HTML
├── .env.production               # VITE_API_URL=/api (빌드타임 주입)
├── public/
│   ├── favicon.svg
│   └── icons.svg
└── src/
    ├── main.jsx                  # React DOM 렌더링 진입점
    ├── App.jsx                   # 루트 컴포넌트: 전역 상태(selectedNode/history/verseLang), 탭·검색 UI
    ├── api.js                    # apiGet() — 공유 fetch 헬퍼, VITE_API_URL 베이스
    ├── theme.js                  # TYPE_COLOR/TYPE_KO/TYPE_ORDER/typeColor/typeKo/SELECT_HL — 색·레이블 공유 팔레트
    ├── MapView.jsx               # MapLibre GL 지도, 마커·링·컨벡스헐, /node/{id}/places 소비
    ├── SidePanel.jsx             # 노드 상세 패널, /node/{id} 소비
    ├── TimelineView.jsx          # 사건·성경책 타임라인, /events·/books·/event/{id}/verses 소비
    ├── VerseLangTabs.jsx         # 한국어/영어 구절 언어 전환 탭 (공유 컴포넌트)
    ├── convexHull.js             # Graham scan 컨벡스헐 계산 (MapView 내 장소 영역 표시)
    ├── index.css                 # 전역 CSS 리셋
    └── assets/                   # 정적 에셋
```

## `data/` — 런타임 오버레이 JSON

`./data`가 Docker 볼륨으로 `api` 컨테이너의 `/app/data`에 마운트된다. API 서버가 `lru_cache`로 1회 로드.

```
data/
├── book_years_approx/
│   └── books.json               # {bookId: {placementYear, basis}} — startYear 없는 31권 추정연도
├── book_events/
│   └── books.json               # {bookId: [eventId,...]} — 추정연도 책↔사건 약한 연결 (⚡ 칩)
├── event_verses/
│   └── events.json              # {eventId: {books: [{bookId, verses:[...]}]}} — 구절 본문 프리베이크
├── book_context/
│   └── books.json               # {bookId: {background, themes, keyVerse, ...}} — 권별 컨텍스트
├── authored_events/
│   └── events.json              # 저작 사건 정의 (load_authored_events.py 입력)
├── character_traits/
│   └── people.json              # {personId: [{trait, verse_ref, description},...]}
└── names_ko/
    ├── books.json               # {bookId: {ko: "..."}}
    ├── events.json              # {eventId: {ko: "..."}}
    ├── groups.json              # {groupId: {ko: "..."}}
    ├── people.json              # {personId: {ko: "..."}}
    └── places.json              # {placeId: {ko: "..."}}
```

## `nginx/`

```
nginx/
└── nginx.conf                   # /api/ 프록시, 정적 파일 캐시 정책, SPA try_files 폴백
```

## `.forge/` — forge 워크플로우 문서

```
.forge/
├── CONTEXT.md                   # 도메인 용어집 (Theographic ID, Book, 추정연도, 저작 사건 등)
├── adr/                         # Architecture Decision Records (0001~0005)
├── backlog/                     # 대기 중인 작업 계획
├── codebase/                    # 코드베이스 맵 문서 (ARCHITECTURE.md, STRUCTURE.md)
├── done/                        # 완료된 작업 (날짜-슬러그 디렉터리)
├── executed/                    # 실행된 워크플로우
├── quick/LOG.md                 # 빠른 작업 로그
└── retro/                       # 회고 문서
```

## 주요 파일 위치

| 역할 | 경로 |
|------|------|
| FastAPI 앱 진입점 | `backend/app/main.py` |
| Neo4j 드라이버 | `backend/app/db.py` |
| 노드 조회 엔드포인트 | `backend/app/routes/nodes.py` |
| 사건 엔드포인트 | `backend/app/routes/events.py` |
| 검색 엔드포인트 | `backend/app/routes/search.py` |
| 성경책 엔드포인트 | `backend/app/routes/books.py` |
| 프론트 API 클라이언트 | `frontend/src/api.js` |
| 색·레이블 팔레트 | `frontend/src/theme.js` |
| 지도 컴포넌트 | `frontend/src/MapView.jsx` |
| 사이드패널 컴포넌트 | `frontend/src/SidePanel.jsx` |
| 타임라인 컴포넌트 | `frontend/src/TimelineView.jsx` |
| 추정연도 오버레이 | `data/book_years_approx/books.json` |
| 사건-책 연결 오버레이 | `data/book_events/books.json` |
| 구절 본문 오버레이 | `data/event_verses/events.json` |
| 초기 데이터 적재 | `backend/scripts/load_theographic.py` |
| 컨테이너 오케스트레이션 | `docker-compose.yml` |
| nginx 설정 | `nginx/nginx.conf` |

## 네이밍 규칙

- **백엔드 Python**: 스네이크 케이스 파일명, 모듈명. `load_*`는 Neo4j 직접 쓰기, `generate_*`는 JSON 파일 생성, `inject_*`는 기존 Neo4j 노드에 속성 추가.
- **프론트엔드**: PascalCase 컴포넌트 파일 (`MapView.jsx`, `SidePanel.jsx`), 카멜케이스 유틸 파일 (`api.js`, `theme.js`, `convexHull.js`).
- **API 경로**: `/node/{id}`, `/node/{id}/places`, `/node/{id}/neighbors/grouped`, `/events`, `/event/{id}/verses`, `/search`, `/books`. 복수형은 컬렉션, 단수형은 단일 리소스.
- **데이터 파일**: `data/<도메인명>/` 하위에 엔티티 타입별 JSON(`books.json`, `events.json`, `people.json`, `places.json`).
- **forge 작업 디렉터리**: `YYYY-MM-DD-<kebab-slug>` 패턴.

## 모듈 조직 원칙

- 프론트엔드는 뷰 단위 수직 분할(`MapView`, `SidePanel`, `TimelineView`) + 공유 횡단 파일(`api.js`, `theme.js`, `VerseLangTabs.jsx`).
- 백엔드 라우터는 도메인 엔티티 단위 분할(`nodes`, `events`, `search`, `books`). 공통 DB 접근은 `db.py` 단일 모듈로 집중.
- 오버레이 JSON은 Neo4j 권위 그래프 밖에서 관리 — 추정·권위 낮은 데이터는 `data/` JSON으로 분리, API 레이어에서 병합(ADR-0004 원칙).
