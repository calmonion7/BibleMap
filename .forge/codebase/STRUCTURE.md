---
last_mapped_commit: 7a1ef362b1fb247b09edeeaa1380e6449fce5721
mapped: 2026-06-20
---

# 디렉터리 구조

## 루트

```
BibleMap/
├── backend/          FastAPI 애플리케이션 + 데이터 파이프라인 스크립트
├── frontend/         React SPA (Vite)
├── data/             오버레이 JSON 데이터 (정적 파일, Neo4j 외부)
├── nginx/            nginx 설정
├── .forge/           forge 워크플로 관리 파일
├── docker-compose.yml
├── .env              NEO4J_PASSWORD 정의 (gitignore)
└── .env.example      환경변수 예시
```

---

## frontend/

```
frontend/
├── src/
│   ├── main.jsx                진입점 — React DOM 마운트
│   ├── App.jsx                 최상위 컴포넌트 — 뷰 전환, 검색, 노드 선택, 오버레이 패널
│   ├── api.js                  단일 HTTP 클라이언트 (apiGet 헬퍼, VITE_API_URL 베이스)
│   ├── theme.js                노드 타입 색·한글 라벨·표시 순서 팔레트 (공유)
│   ├── MapView.jsx             maplibre-gl 지도 뷰 — 마커/클러스터/스파이더파이/사건 링/볼록 껍질
│   ├── TimelineView.jsx        사건 타임라인 뷰 — startDate 그룹, 책 칩, 인라인 구절 드릴다운
│   ├── BibleOverviewView.jsx   성경 개요 뷰 — 구약·신약 장르별 북 카드 그리드
│   ├── SidePanel.jsx           노드 상세 오버레이 패널 — 이웃 그룹, 인물 성품, 책 전용 뷰
│   ├── useNodeSelection.js     노드 선택·히스토리·인물 사건 ID 관리 커스텀 훅
│   ├── useSearch.js            검색 쿼리·결과·드롭다운·디바운스 커스텀 훅
│   ├── convexHull.js           Graham scan 볼록 껍질 순수 유틸
│   ├── VerseLangTabs.jsx       구절 언어 전환 탭 (한국어/영어) 공유 UI
│   ├── Spinner.jsx             로딩 스피너 공유 UI
│   ├── index.css               글로벌 스타일 (최소)
│   └── assets/                 정적 에셋 (hero.png 등)
├── public/                     Vite 정적 루트 (favicon.svg 등)
├── dist/                       빌드 결과물 — nginx 마운트 대상
├── index.html                  SPA HTML 쉘
├── vite.config.js              Vite 설정 (maplibre 코드 분할)
└── package.json                의존성 (react 19, maplibre-gl 5, lucide-react)
```

### 파일 명명 규칙

- 뷰 컴포넌트: PascalCase + `View` 접미어 (`MapView.jsx`, `TimelineView.jsx`, `BibleOverviewView.jsx`)
- 공유 패널: `SidePanel.jsx`
- 커스텀 훅: camelCase + `use` 접두어, `.js` 확장자 (`useNodeSelection.js`, `useSearch.js`)
- 순수 유틸: camelCase, `.js` 확장자 (`convexHull.js`, `api.js`, `theme.js`)
- 공유 UI 컴포넌트: PascalCase, `.jsx` 확장자 (`Spinner.jsx`, `VerseLangTabs.jsx`)

---

## backend/

```
backend/
├── app/
│   ├── main.py                 FastAPI 앱 정의, 라우터 등록, lifespan(인덱스 생성)
│   ├── db.py                   Neo4j 드라이버 싱글턴 (get_driver)
│   ├── overlays.py             오버레이 JSON 로더 (lru_cache — book_events_raw, approx_years, event_verses)
│   └── routes/
│       ├── nodes.py            /node/{id}, /node/{id}/places, /node/{id}/neighbors/grouped, /person/{id}/event-ids
│       ├── events.py           /events, /event/{id}/verses
│       ├── search.py           /search?q=
│       └── books.py            /books, /books-overview
├── scripts/
│   ├── load_theographic.py    GitHub Theographic Bible Metadata → Neo4j 벌크 로드
│   ├── load_books.py          Book 노드 로드
│   ├── load_person_events.py  인물별 사건 로드
│   ├── load_authored_events.py 저작 사건 로드
│   ├── load_verse_events.py   구절-사건 연결 로드
│   ├── generate_book_context.py   LLM으로 책 컨텍스트 생성
│   ├── generate_book_context_enrich.py  책 컨텍스트 보강
│   ├── generate_book_events.py    LLM으로 책 사건 생성
│   ├── generate_approx_book_verses.py  추정 책-구절 생성
│   ├── generate_event_verses.py   사건 근거 구절 생성
│   ├── generate_verse_events.py   구절-사건 매핑 생성
│   ├── generate_verse_text.py     구절 본문 텍스트 생성
│   ├── generate_person_traits.py  인물 성품 생성
│   ├── generate_person_event_verses.py 인물 사건 구절 생성
│   ├── inject_book_context.py     책 컨텍스트 Neo4j 주입
│   ├── inject_ko_names.py         한국어 이름 Neo4j 주입
│   ├── inject_person_traits.py    인물 성품 Neo4j 주입
│   └── enrich_place_coords.py     장소 좌표 보강
├── Dockerfile                  python:3.12-slim, uvicorn app.main:app :8000
└── requirements.txt            fastapi, neo4j, uvicorn
```

### 파일 명명 규칙

- 라우터: 복수 명사형 (`nodes.py`, `events.py`, `search.py`, `books.py`)
- 스크립트: `동사_목적어.py` 패턴 (`load_theographic.py`, `generate_book_events.py`, `inject_ko_names.py`)
- `generate_*` — LLM 호출로 JSON 데이터 생성 → `data/` 저장
- `inject_*` — `data/` JSON을 읽어 Neo4j 노드에 주입
- `load_*` — 원본 소스(GitHub or `data/`)를 Neo4j에 직접 로드

---

## data/

```
data/
├── book_events/
│   └── books.json          {bookId: [eventId, ...]} — 책이 기록한 사건 목록 (오버레이)
├── book_years_approx/
│   └── books.json          {bookId: {placementYear, basis, approx}} — 추정 연도 오버레이
├── event_verses/
│   └── events.json         사건별 근거 구절 (책·절·textKo·textEn prebaked)
├── book_context/
│   └── books.json          책 컨텍스트 (배경, 주제, 핵심 구절 등)
├── character_traits/
│   └── people.json         인물별 성품 트레이트 목록
├── authored_events/
│   └── events.json         LLM 저작 사건 데이터 (추정 연도 포함)
├── person_events/
│   └── {slug}.json         인물별 사건 목록 (abraham.json, jesus.json 등 13명)
├── names_ko/
│   ├── books.json          성경책 한국어 이름
│   ├── events.json         사건 한국어 이름
│   ├── groups.json         집단 한국어 이름
│   ├── people.json         인물 한국어 이름
│   └── places.json         장소 한국어 이름
├── place_coords/
│   └── places.json         장소 좌표 보강 데이터
└── verse_events/
    └── events.json         구절-사건 매핑 데이터
```

### 데이터 파일 규칙

- 서브디렉터리명: 단수 또는 복수 명사 (`book_events/`, `names_ko/`)
- 파일명: 엔티티 복수형 (`books.json`, `events.json`, `people.json`, `places.json`, `groups.json`)
- `person_events/`만 예외 — 인물 슬러그별 개별 파일

---

## nginx/

```
nginx/
└── nginx.conf         /api/* → api:8000 프록시, /* → SPA (try_files /index.html), 정적 에셋 캐시 1년
```

---

## .forge/

```
.forge/
├── CONTEXT.md          도메인 용어·결정 컨텍스트
├── adr/                아키텍처 결정 기록 (ADR-0001~0006)
├── backlog/            대기 중인 작업 계획
├── done/               완료된 작업 슬롯 (날짜-slug 디렉터리)
├── executed/           실행된 워크플로 기록
├── quick/LOG.md        빠른 작업 로그
├── retro/              작업 회고 마크다운
├── reports/            검증 스크린샷·보고서
└── codebase/           코드베이스 맵 문서 (이 파일 포함)
```

---

## 핵심 파일 빠른 참조

| 파일 | 역할 |
|---|---|
| `frontend/src/App.jsx` | 최상위 상태, 탭 라우팅, 검색 UI, 오버레이 패널 |
| `frontend/src/api.js` | 모든 HTTP 요청 단일 베이스 |
| `frontend/src/theme.js` | 노드 타입 색·라벨 팔레트 (공유) |
| `frontend/src/MapView.jsx` | maplibre-gl 지도, 클러스터, 스파이더파이, 사건 링 |
| `frontend/src/SidePanel.jsx` | 노드 상세 패널 |
| `frontend/src/useNodeSelection.js` | 노드 선택·히스토리 훅 |
| `backend/app/main.py` | FastAPI 앱 등록 |
| `backend/app/db.py` | Neo4j 드라이버 싱글턴 |
| `backend/app/overlays.py` | JSON 오버레이 로더 (캐시) |
| `backend/app/routes/nodes.py` | 노드/이웃/장소 API |
| `backend/app/routes/events.py` | 사건 목록·구절 API (캐시) |
| `backend/scripts/load_theographic.py` | 데이터 초기 로드 |
| `data/event_verses/events.json` | 사건별 구절 텍스트 (prebaked) |
| `docker-compose.yml` | 3-서비스 컨테이너 구성 |
| `nginx/nginx.conf` | API 프록시 + SPA 라우팅 |
