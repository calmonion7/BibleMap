---
last_mapped_commit: 71c28dc
mapped: 2026-06-20
---

# BibleMap — 디렉터리 구조

## 트리

```
BibleMap/
├── .env                          # NEO4J_PASSWORD 등 시크릿 (git 제외)
├── .env.example
├── docker-compose.yml            # neo4j / api / nginx 3서비스
├── deploy.sh                     # 빌드·컨테이너 재시작·ko 이름 주입
├── CLAUDE.md                     # AI 코딩 가이드라인
├── BIBLEMAP_PLAN.md              # 프로젝트 계획 문서
│
├── .github/
│   └── workflows/
│       └── deploy.yml            # main 푸시 → self-hosted runner deploy.sh
│
├── backend/
│   ├── Dockerfile                # uvicorn 실행, /app/data 볼륨 마운트
│   ├── requirements.txt          # fastapi, neo4j, uvicorn
│   ├── __init__.py
│   └── app/
│       ├── main.py               # FastAPI 앱 + lifespan(인덱스) + 라우터 등록
│       ├── db.py                 # Neo4j 드라이버 싱글턴 get_driver()
│       ├── overlays.py           # data/ JSON 오버레이 lru_cache 로더
│       └── routes/
│           ├── nodes.py          # /node/{id}, /places, /neighbors/grouped, /person/.../event-ids
│           ├── events.py         # /events, /event/{id}/verses
│           ├── books.py          # /books, /books-overview
│           └── search.py         # /search?q=
│
├── backend/scripts/              # 오프라인 데이터 파이프라인 스크립트
│   ├── load_theographic.py       # Theographic GitHub JSON → Neo4j 전체 적재
│   ├── load_books.py             # Book 노드 + CONTAINS_BOOK 관계
│   ├── load_authored_events.py   # authored=true 저작 이벤트 → Neo4j
│   ├── load_person_events.py     # data/person_events/ → Neo4j
│   ├── load_verse_events.py      # data/verse_events/ → Neo4j
│   ├── inject_ko_names.py        # data/names_ko/ → nameKo 속성 주입
│   ├── inject_person_traits.py   # data/character_traits/ → traits 속성 주입
│   ├── inject_book_context.py    # data/book_context/ → themes·keyVerse 속성 주입
│   ├── enrich_place_coords.py    # Place 좌표 보강
│   ├── generate_book_events.py   # LLM → data/book_events/books.json
│   ├── generate_book_context.py  # LLM → data/book_context/books.json
│   ├── generate_person_traits.py # LLM → data/character_traits/people.json
│   ├── generate_event_verses.py  # LLM → data/event_verses/events.json
│   ├── generate_verse_events.py  # LLM → data/verse_events/events.json
│   ├── generate_verse_text.py    # getbible API → 구절 본문 ko/en 프리베이크
│   └── generate_approx_book_verses.py
│
├── data/                         # 오버레이 JSON (docker-compose 볼륨 /app/data 마운트)
│   ├── authored_events/
│   │   └── events.json           # authored 이벤트 정의
│   ├── book_context/
│   │   └── books.json            # themes·keyVerse·background (LLM 생성)
│   ├── book_events/
│   │   └── books.json            # {bookId: [eventId,...]} 추정 연결 오버레이
│   ├── book_years_approx/
│   │   └── books.json            # {bookId: {placementYear, basis}} 추정연도 오버레이
│   ├── character_traits/
│   │   └── people.json           # {personId: [{trait, verse_ref, description},...]}
│   ├── event_verses/
│   │   └── events.json           # {eventId: {books: [{bookId, verses:[...]}]}}
│   ├── names_ko/
│   │   ├── people.json           # {theographic_id: nameKo, ...}
│   │   ├── places.json
│   │   ├── events.json
│   │   ├── groups.json
│   │   └── books.json
│   ├── person_events/
│   │   ├── abraham.json          # 인물별 저작 이벤트 (인물 활동반경용)
│   │   ├── david.json
│   │   ├── moses.json
│   │   ├── jesus.json
│   │   └── ...                   # 총 13인 (구약 10 + 신약 3)
│   ├── place_coords/
│   │   └── places.json           # 좌표 보강 데이터
│   └── verse_events/
│       └── events.json           # 구절 기반 이벤트 데이터
│
├── frontend/
│   ├── index.html                # Vite 진입 HTML
│   ├── vite.config.js            # manualChunks: maplibre / vendor 분리
│   ├── package.json              # react 19, maplibre-gl, lucide-react
│   ├── eslint.config.js
│   ├── .env.production           # VITE_API_URL=/api (nginx 프록시)
│   ├── public/
│   │   ├── favicon.svg
│   │   └── icons.svg
│   └── src/
│       ├── main.jsx              # ReactDOM.createRoot 마운트 엔트리
│       ├── App.jsx               # 탭 라우팅(map/timeline/overview), 검색 UI, SidePanel 오버레이
│       ├── api.js                # apiGet(path) — 단일 fetch 클라이언트
│       ├── theme.js              # TYPE_COLOR, TYPE_KO, TYPE_ORDER, SELECT_HL 공유 팔레트
│       ├── useNodeSelection.js   # selectedNode / history / personEventIds 훅
│       ├── useSearch.js          # 실시간 검색 (250ms 디바운스, AbortController)
│       ├── MapView.jsx           # MapLibre GL JS 지도, 마커·링·convexHull
│       ├── TimelineView.jsx      # 연도별 사건 목록, 구절 드릴다운, Book/Person 필터
│       ├── BibleOverviewView.jsx # 장르별 Book 카드 그리드
│       ├── SidePanel.jsx         # 노드 상세 패널 (traits·neighbors·verses)
│       ├── VerseLangTabs.jsx     # ko/en 구절 언어 탭 전환 (TimelineView·SidePanel 공유)
│       ├── Spinner.jsx           # 로딩 표시
│       ├── convexHull.js         # Convex Hull 좌표 계산 유틸
│       └── index.css             # 전역 스타일 리셋
│
├── nginx/
│   └── nginx.conf                # /api/ → api:8000 프록시, 정적 파일 캐시 설정
│
└── .forge/
    ├── CONTEXT.md                # 도메인 용어집·ADR 결정 기록
    ├── adr/                      # Architecture Decision Records
    │   ├── 0001-no-apoc-own-loader.md
    │   ├── 0002-timeline-event-evidence-model.md
    │   ├── 0003-prebake-bilingual-verse-text.md
    │   ├── 0004-estimated-data-runtime-overlay-not-neo4j.md
    │   └── 0005-authored-events-marked-neo4j-nodes.md
    ├── backlog/                  # 미실행 계획
    ├── done/                     # 완료된 태스크 (날짜-슬러그 디렉터리)
    ├── retro/                    # 태스크별 회고 마크다운
    ├── codebase/                 # 코드베이스 매핑 문서 (이 파일)
    └── quick/LOG.md              # 빠른 작업 로그
```

---

## 핵심 파일 위치

| 역할 | 경로 |
|---|---|
| FastAPI 앱 정의 | `backend/app/main.py` |
| Neo4j 연결 | `backend/app/db.py` |
| JSON 오버레이 로더 | `backend/app/overlays.py` |
| 노드 조회 라우터 | `backend/app/routes/nodes.py` |
| 이벤트 라우터 | `backend/app/routes/events.py` |
| 책 라우터 | `backend/app/routes/books.py` |
| 검색 라우터 | `backend/app/routes/search.py` |
| fetch 클라이언트 | `frontend/src/api.js` |
| 색상·라벨 팔레트 | `frontend/src/theme.js` |
| 노드 선택 훅 | `frontend/src/useNodeSelection.js` |
| 검색 훅 | `frontend/src/useSearch.js` |
| nginx 프록시 설정 | `nginx/nginx.conf` |
| 컨테이너 오케스트레이션 | `docker-compose.yml` |
| 배포 스크립트 | `deploy.sh` |
| CI 워크플로 | `.github/workflows/deploy.yml` |
| Theographic 원본 적재 | `backend/scripts/load_theographic.py` |
| 도메인 용어·ADR | `.forge/CONTEXT.md` |

---

## 명명 규칙

**파이썬 스크립트**
- `load_*.py` — Theographic·생성 데이터를 Neo4j에 직접 주입
- `inject_*.py` — 기존 노드에 속성만 추가(MERGE + SET)
- `generate_*.py` — LLM 호출로 `data/` JSON 파일 생성 (Neo4j 미접촉)

**data/ 서브디렉터리**
- 각 디렉터리는 단일 JSON 파일(`books.json`, `events.json`, `people.json`, `places.json`)을 담음.
- `person_events/` 만 예외 — 인물별로 분리된 `<slug>.json` 파일.

**프론트엔드 파일**
- 뷰 컴포넌트: `*View.jsx` (MapView, TimelineView, BibleOverviewView)
- 커스텀 훅: `use*.js` (useNodeSelection, useSearch)
- 단일 책임 유틸: `convexHull.js`, `theme.js`, `api.js`

**Neo4j 속성**
- 영문 원문: `name` (Person·Place·PeopleGroup), `title` (Event)
- 한국어: `nameKo`
- 식별자: `theographic_id` (모든 노드, `rec` 접두 또는 `authored-<slug>`)
- 저작 이벤트 구분자: `authored: true`
- 추정 배치용: `sortKey` (정렬 숫자), `yearLabel` (표시 문자열)
