---
last_mapped_commit: 14e0a78c3e0ab7fc7d960c4cabdf3eab3fc297e6
mapped: 2026-06-27
---

# 디렉터리 구조

## 루트

```
BibleMap/
├── backend/          FastAPI 애플리케이션 + 데이터 파이프라인 스크립트
├── frontend/         React SPA (Vite)
├── data/             정적 JSON 데이터 (Neo4j inject 소스 또는 런타임 오버레이)
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
│   ├── App.jsx                 최상위 컴포넌트 — 뷰 전환, 검색, 노드 선택, 오버레이 패널, 모바일 분기, / 단축키
│   ├── api.js                  단일 HTTP 클라이언트 (apiGet 헬퍼, VITE_API_URL 베이스)
│   ├── theme.js                노드 타입 색·한글 라벨·표시 순서 팔레트 + typeColor/typeKo 헬퍼, SELECT_HL (공유)
│   ├── constants.js            공유 상수 — MOBILE_BREAKPOINT(768px), SHEET_VH(55vh)
│   ├── MapView.jsx             maplibre-gl 지도 뷰 — 컴포넌트 셸(약 193줄): 지도 생성·effect 3개·에러/위치없음 UI
│   ├── mapGeo.js               지도 순수 기하/GeoJSON/라벨 앵커 계산 (coreBounds·ringLabels·placesToGeoJSON·easeOutCubic·ringPositions·buildEventGeoJSON·buildSpiderGeoJSON·outwardLabel) — placesToGeoJSON은 동일/근접 좌표 2개+면 라벨을 ringLabels로 방사 분산(task-84)
│   ├── mapLayers.js            지도 정적 설정 (EMPTY_GEOJSON·setupMapSources·registerEventHandlers·placePopupHTML·escapeHtml)
│   ├── mapRingController.js    사건 링/스파이더 애니메이션 컨트롤러 팩토리 (createRingController → collapseRing·expandPlace·spiderifyPlaces·collapseSpider·destroy + 공유 가변 상태)
│   ├── TimelineView.jsx        사건 타임라인 뷰 — startDate 그룹, 책 칩, 인라인 구절 드릴다운
│   ├── BibleOverviewView.jsx   성경 개요 뷰 — 구약·신약 장르별 북 카드 그리드
│   ├── SidePanel.jsx           노드 상세 오버레이 패널 — 이웃 그룹 + Person/Book/Place 전용 블록
│   ├── useNodeSelection.js     노드 선택·히스토리·인물 사건 ID 관리 커스텀 훅
│   ├── useSearch.js            검색 쿼리·결과·타입필터·드롭다운·디바운스 커스텀 훅
│   ├── convexHull.js           Graham scan 볼록 껍질 순수 유틸
│   ├── VerseLangTabs.jsx       구절 언어 전환 탭 (한국어/영어) 공유 UI
│   ├── Spinner.jsx             로딩 스피너 공유 UI
│   ├── index.css               글로벌 스타일 (최소)
│   └── assets/                 정적 에셋
├── public/                     Vite 정적 루트
├── dist/                       빌드 결과물 — nginx 마운트 대상
├── index.html                  SPA HTML 쉘
├── vite.config.js              Vite 설정 (maplibre 코드 분할)
├── .env.production             VITE_API_URL=/api (프로덕션 빌드 고정)
└── package.json                의존성 (react 19, maplibre-gl 5, lucide-react, vite 8)
```

### 파일 명명 규칙

- 뷰 컴포넌트: PascalCase + `View` 접미어 (`MapView.jsx`, `TimelineView.jsx`, `BibleOverviewView.jsx`)
- 공유 패널: `SidePanel.jsx`
- 커스텀 훅: camelCase + `use` 접두어, `.js` 확장자 (`useNodeSelection.js`, `useSearch.js`)
- 순수 유틸·상수·팔레트: camelCase, `.js` 확장자 (`convexHull.js`, `api.js`, `theme.js`, `constants.js`)
- MapView 보조 모듈: `map` 접두어 camelCase, `.js` 확장자 (`mapGeo.js` 순수 계산, `mapLayers.js` 정적 설정, `mapRingController.js` 컨트롤러 팩토리) — `MapView.jsx`가 이 3개를 import
- 공유 UI 컴포넌트: PascalCase, `.jsx` 확장자 (`Spinner.jsx`, `VerseLangTabs.jsx`)

---

## backend/

```
backend/
├── app/
│   ├── main.py                 FastAPI 앱 정의, 라우터 등록, lifespan(인덱스 생성)
│   ├── db.py                   Neo4j 드라이버 싱글턴 (get_driver)
│   ├── overlays.py             오버레이 JSON 로더 (lru_cache — book_events_raw, event_verses)
│   └── routes/
│       ├── nodes.py            /node/{id}, /node/{id}/places, /node/{id}/neighbors/grouped, /person/{id}/event-ids
│       ├── events.py           /events, /event/{id}/verses (lru_cache + 추정책 머지)
│       ├── search.py           /search?q= (3단 랭크 정렬)
│       └── books.py            /books, /books-overview
├── scripts/
│   ├── load_theographic.py    GitHub Theographic Bible Metadata → Neo4j 벌크 로드
│   ├── load_books.py          Book 노드 로드
│   ├── load_person_events.py  인물별 여정 사건(authored) 로드 + OCCURS_AT/HAS_PARTICIPANT
│   ├── load_authored_events.py 저작 사건(authored=true) Event 노드 로드
│   ├── load_verse_events.py   구절-사건 Event + CONTAINS_BOOK 로드
│   ├── generate_book_context.py        LLM 책 컨텍스트 생성 레시피
│   ├── generate_book_context_enrich.py 책 컨텍스트 보강 레시피(author·verseCount·keyPeople 등)
│   ├── generate_book_events.py         LLM 책 사건 생성 레시피
│   ├── generate_approx_book_verses.py  추정 책-구절 생성 레시피
│   ├── generate_event_verses.py        사건 근거 구절 생성 레시피
│   ├── generate_verse_events.py        구절-사건 매핑 생성 레시피
│   ├── generate_verse_text.py          getbible 절 본문 prebake (4소스: event_verses·book_context·character_traits·place_context)
│   ├── generate_person_traits.py       인물 성품 생성 레시피
│   ├── generate_person_event_verses.py 인물 사건 구절 생성 레시피
│   ├── inject_book_context.py     책 컨텍스트(background·themes·keyVerse) Neo4j 주입
│   ├── inject_ko_names.py         한국어 이름(nameKo·aliasesKo) Neo4j 주입
│   ├── inject_person_traits.py    인물 성품(traits) Neo4j 주입
│   ├── inject_place_context.py    장소 컨텍스트(background·keyVerse·keyVerseTextKo/En) Neo4j 주입
│   └── enrich_place_coords.py     장소 좌표 Neo4j 멱등 적재
├── Dockerfile                  python:3.12-slim, uvicorn app.main:app :8000
└── requirements.txt            fastapi, neo4j, uvicorn
```

### 파일 명명 규칙

- 라우터: 복수 명사형 (`nodes.py`, `events.py`, `search.py`, `books.py`)
- 스크립트: `동사_목적어.py` 패턴 (`load_theographic.py`, `generate_book_events.py`, `inject_place_context.py`)
- `generate_*` — LLM이 생성한 JSON 데이터를 담는 레시피 → `data/` 저장 (ADR-0006). `generate_verse_text.py`만 예외로 getbible에서 절 본문 실호출 후 인라인 저장
- `inject_*` — `data/` JSON을 읽어 기존 Neo4j 노드에 프로퍼티 SET
- `load_*` / `enrich_*` — 원본 소스(GitHub or `data/`)를 Neo4j에 MERGE로 노드·관계 적재(멱등)

---

## data/

```
data/
├── book_events/
│   └── books.json          {bookId: [eventId, ...]} — 책이 기록한 사건 목록 (오버레이)
├── book_years_approx/
│   └── books.json          {bookId: {placementYear, basis, approx}} — 추정 연도 (빌드타임 입력, generate_book_events.py)
├── event_verses/
│   └── events.json         사건별 근거 구절 (books[].verses[].textKo·textEn prebaked) (오버레이)
├── book_context/
│   └── books.json          책 컨텍스트 (background·themes·keyVerse·keyVerseTextKo/En 등) (inject)
├── place_context/
│   └── places.json         장소 컨텍스트 (background·keyVerse·keyVerseTextKo/En, place id 키, 43개) (inject)
├── character_traits/
│   └── people.json         인물별 성품 트레이트 (trait·verse_ref·description·verse_textKo/En) (inject)
├── place_coords/
│   └── places.json         장소 좌표 보강 데이터 (load/enrich)
├── authored_events/
│   └── events.json         LLM 저작 사건 데이터 (load)
├── person_events/
│   └── {slug}.json         인물별 여정 사건 (abraham.json, jesus.json 등 13명) (load)
├── verse_events/
│   └── events.json         구절-사건 매핑 데이터 (load)
└── names_ko/
    ├── books.json          성경책 한국어 이름
    ├── events.json         사건 한국어 이름
    ├── groups.json         집단 한국어 이름
    ├── people.json         인물 한국어 이름
    └── places.json         장소 한국어 이름 (inject)
```

### 데이터 파일 규칙

- 서브디렉터리명: 단수 또는 복수 명사 (`book_events/`, `place_context/`, `names_ko/`)
- 파일명: 엔티티 복수형 (`books.json`, `events.json`, `people.json`, `places.json`, `groups.json`)
- `person_events/`만 예외 — 인물 슬러그별 개별 파일
- **소비 경로 구분**: `book_events`·`event_verses`는 런타임 오버레이(`overlays.py`, Neo4j 미주입). `book_years_approx`는 빌드타임 입력(`generate_book_events.py`)으로만 소비(task-85에서 런타임 로더 제거). 나머지는 `inject_*`/`load_*`/`enrich_*`로 Neo4j에 들어간다.

---

## nginx/

```
nginx/
└── nginx.conf         /api/* → api:8000 프록시, /* → SPA (try_files /index.html),
                       index.html no-cache, 정적 에셋 1년 immutable 캐시
```

---

## .forge/

```
.forge/
├── CONTEXT.md          도메인 용어·결정 컨텍스트(용어 정의는 여기, 본 맵은 구현 사실만)
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
| `frontend/src/App.jsx` | 최상위 상태, 탭 라우팅, 검색 UI, 오버레이 패널, 모바일 분기 |
| `frontend/src/api.js` | 모든 HTTP 요청 단일 베이스 |
| `frontend/src/theme.js` | 노드 타입 색·라벨 팔레트 + typeColor/typeKo 헬퍼 (공유) |
| `frontend/src/constants.js` | 공유 상수 (MOBILE_BREAKPOINT, SHEET_VH) |
| `frontend/src/MapView.jsx` | maplibre-gl 지도 뷰 컴포넌트 셸 (mapGeo/mapLayers/mapRingController 조합) |
| `frontend/src/mapGeo.js` | 지도 순수 기하·GeoJSON·라벨 앵커 계산 |
| `frontend/src/mapLayers.js` | 지도 소스/레이어 등록·이벤트 핸들러·팝업 |
| `frontend/src/mapRingController.js` | 사건 링/스파이더 애니메이션 컨트롤러 팩토리 |
| `frontend/src/SidePanel.jsx` | 노드 상세 패널 (Person/Book/Place 전용 블록) |
| `frontend/src/useNodeSelection.js` | 노드 선택·히스토리 훅 |
| `backend/app/main.py` | FastAPI 앱 등록 |
| `backend/app/db.py` | Neo4j 드라이버 싱글턴 |
| `backend/app/overlays.py` | JSON 오버레이 로더 (캐시) |
| `backend/app/routes/nodes.py` | 노드/이웃/장소 API |
| `backend/app/routes/events.py` | 사건 목록·구절 API (캐시) |
| `backend/scripts/load_theographic.py` | 데이터 초기 로드 |
| `backend/scripts/generate_verse_text.py` | 절 본문 prebake (4소스) |
| `backend/scripts/inject_place_context.py` | 장소 컨텍스트 Neo4j 주입 |
| `data/event_verses/events.json` | 사건별 구절 텍스트 (prebaked, 오버레이) |
| `data/place_context/places.json` | 장소 배경·대표 구절 (inject 소스) |
| `docker-compose.yml` | 3-서비스 컨테이너 구성 |
| `nginx/nginx.conf` | API 프록시 + SPA 라우팅 |
