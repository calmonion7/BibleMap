---
last_mapped_commit: 99d42c8518af00f3e0bf4a4ba90f821d84cf42e5
mapped: 2026-07-02
---

# STRUCTURE

## 디렉터리 레이아웃

```
BibleMap/
├── backend/            FastAPI 앱 + 데이터 적재·생성 스크립트
│   ├── app/            런타임 API
│   │   ├── routes/     엔드포인트 모듈 7종
│   │   ├── main.py     FastAPI 진입점(라우터 등록 + lifespan 인덱스)
│   │   ├── db.py       Neo4j 드라이버 싱글톤
│   │   └── overlays.py data/ JSON 로더(lru_cache)
│   ├── scripts/        Neo4j 적재(load_*)·주입(inject_*)·생성(generate_*/enrich_*) 스크립트
│   ├── Dockerfile      python:3.12-slim, uvicorn app.main:app
│   └── requirements.txt fastapi / neo4j / uvicorn
├── frontend/           React 19 + Vite SPA
│   ├── src/            컴포넌트·헬퍼·훅
│   ├── public/         favicon.svg
│   ├── dist/           빌드 산출물(nginx가 read-only 마운트)
│   ├── vite.config.js  maplibre/vendor 청크 분리
│   └── package.json    react·react-dom·maplibre-gl·lucide-react
├── data/               빌드타임 생성 JSON 오버레이/원천(서브디렉터리별)
├── nginx/nginx.conf    /api 프록시 + SPA 폴백
├── docker-compose.yml  neo4j / api / nginx 3 서비스
├── deploy.sh           프론트 빌드 → compose build/up → 한글이름 주입
├── .github/workflows/deploy.yml  main push → self-hosted 러너 배포
├── .env / .env.example NEO4J_PASSWORD
├── BIBLEMAP_PLAN.md    설계 문서
└── CLAUDE.md / README.md
```

## 백엔드 (`backend/`)

### 런타임 앱 (`backend/app/`)

- `backend/app/main.py` — 진입점. `FastAPI(lifespan=...)` + 7 라우터 등록 + CORS(GET 전용).
- `backend/app/db.py` — `get_driver()` Neo4j 싱글톤.
- `backend/app/overlays.py` — `_resolve`/`_load` + `book_events_raw()`·`event_verses()` 캐시 로더.
- `backend/app/routes/` 엔드포인트 모듈:
  - `persons.py` — `GET /persons/curated`(파일 기반 큐레이션 **28인** 목록, `_ERA_ORDER` 7시대). `_ERA`·`_NAME_KO`·`_ERA_ORDER` 세 상수의 **단일 출처** — `places.py`·`journey.py`가 이 모듈에서 import한다. `_build_list`는 각 인물의 최소 sortKey를 `_anchor`로 계산해 시대 내 연대순 정렬 후 응답 전 `_anchor` 제거. **"포로" 시대 신설**: `_ERA_ORDER[5]`에 위치, 해당 인물: daniel·esther·nehemiah(3인).
  - `journey.py` — `GET /person/{id}/journey`(여정 정차지, 파일 시퀀스 + Neo4j 좌표). `_ERA`·`_NAME_KO`를 `persons.py`에서 import.
  - `events.py` — `GET /events`, `GET /event/{id}/verses`.
  - `books.py` — `GET /books-overview`.
  - `nodes.py` — `GET /node/{id}`, `/node/{id}/places`, `/node/{id}/neighbors/grouped`, `/person/{id}/event-ids`.
  - `places.py` — `GET /place/{id}/curated-persons`. `_ERA`·`_NAME_KO`·`_ERA_ORDER`를 `persons.py`에서 import(드리프트 방지). `_place_to_persons`의 정렬 로직은 `_build_list`와 동일(`_anchor` = 최소 sortKey).
  - `search.py` — `GET /search?q=`.
- `backend/__init__.py`, `backend/app/__init__.py`, `backend/app/routes/__init__.py`, `backend/scripts/__init__.py` — 패키지 마커.

### 스크립트 (`backend/scripts/`)

세 부류로 나뉜다 — 명명 접두어가 곧 역할이다:

- **`load_*` (Neo4j 멱등 적재)**
  - `load_theographic.py` — Theographic 원본 그래프 적재.
  - `load_books.py` — `Book` 노드 + `CONTAINS_BOOK` 관계.
  - `load_authored_persons.py` — `authored_persons/people.json` → authored Person 노드(ADR-0008). **`load_person_events.py`보다 먼저 실행 필수**(HAS_PARTICIPANT MATCH 성립 조건).
  - `load_authored_events.py` — `authored_events/events.json` → authored Event 노드.
  - `load_person_events.py` — `person_events/*.json` → 인물 여정 Event 노드.
  - `load_verse_events.py` — `verse_events/events.json` → 신규 Event + CONTAINS_BOOK.
- **`inject_*` (생성 JSON을 Neo4j 노드 속성에 SET)**
  - `inject_ko_names.py` — Person/Place 한글 이름(배포 시 `deploy.sh`가 호출).
  - `inject_person_traits.py` — `character_traits/people.json` → Person `traits`.
  - `inject_book_context.py` — `book_context/books.json` → Book 배경·주제·keyVerse.
  - `inject_place_context.py` — `place_context/places.json` → Place 배경·keyVerse.
- **`generate_*` / `enrich_*` (오버레이/원천 JSON 생성, 일부 Claude API 사용)**
  - `generate_event_verses.py` — 사건별 근거 구절을 권별 묶음 오버레이로.
  - `generate_person_event_verses.py` — `person_events` context의 구절 참조 파싱.
  - `generate_book_events.py` — 추정연도 책(31권)을 사건에 연결(Claude API).
  - `generate_verse_events.py` — 고아 구절 → Event 데이터.
  - `generate_approx_book_verses.py` — 추정연도 책 집필 배경 사건·대표 구절.
  - `generate_verse_text.py` — 생성 데이터의 인용 절 본문 채움.
  - `generate_person_traits.py` — 인물별 성품(Claude API).
  - `generate_book_context.py` / `generate_book_context_enrich.py` — 권별 배경·주제(Claude API).
  - `enrich_place_coords.py` — `place_coords/places.json` → Place 노드 멱등 적재.

## 데이터 오버레이 (`data/`)

서브디렉터리별로 단일(또는 소수) JSON 파일을 둔다. 파일명 관례: 대상 라벨의 복수형(`books.json`·`events.json`·`people.json`·`places.json`·`groups.json`). 예외로 `person_events/`만 인물 slug별 개별 파일이다.

| 디렉터리 | 파일 | 형태/내용 |
|----------|------|-----------|
| `data/person_events/` | `<slug>.json` **×28** (abraham, isaac, jacob, joseph, moses, joshua, gideon, deborah, jephthah, samson, ruth, samuel, saul, david, solomon, elijah, elisha, jonah, isaiah, daniel, esther, nehemiah, john_the_baptist, jesus, mary, paul, peter, john_the_apostle) | 인물 여정 사건 배열. `id`·`sortKey`·`occursAt`·`participants`·`context`·`books`. **여정 정차지의 권위 원천** |
| `data/authored_persons/` | `people.json` (**12인**) | authored Person 노드 원천. `{id, name, nameKo}`. `load_authored_persons.py`가 Neo4j에 멱등 적재(ADR-0008) |
| `data/authored_events/` | `events.json` (배열) | 독립 authored 사건. `mappedBookIds` 포함 |
| `data/event_verses/` | `events.json` (617+ 키) | `{eventId: {books: [{bookId, bookOrder, rangeLabel, verses: [{verseID, chapter, verse, textKo, textEn}]}]}}` — 구절 본문 프리베이크 |
| `data/book_events/` | `books.json` (31 키) | `{bookId: [eventId, ...]}` 추정책↔사건 매핑(events.py가 역방향 머지) |
| `data/names_ko/` | `books.json`·`events.json`·`groups.json`·`people.json`·`places.json` | `{theographic_id: {ko, alias: []}}` 한글 이름 |
| `data/character_traits/` | `people.json` (**43 키**) | `{personId: {traits: [{trait, verse_ref, description, verse_textKo, verse_textEn}]}}` |
| `data/book_context/` | `books.json` | 권별 배경·주제·keyVerse |
| `data/book_years_approx/` | `books.json` | 추정 집필 연도 |
| `data/place_context/` | `places.json` | 장소 배경·keyVerse |
| `data/place_coords/` | `places.json` (배열, **74건**) | `{id, name, nameKo, lat, lng, note}` authored 장소 좌표 |
| `data/verse_events/` | `events.json` | 고아 구절 기반 사건 |

## 프론트엔드 (`frontend/src/`)

진입: `main.jsx`(`createRoot` + `<StrictMode>`) → `App.jsx`. 모든 소스가 단일 `src/` 평면 디렉터리에 있다(서브폴더 없음). 명명 관례: **컴포넌트는 PascalCase `.jsx`, 헬퍼/훅/상수는 camelCase `.js`**.

- 단계/오케스트레이션: `App.jsx`(stage 토글·레이아웃·모바일 읽기 모드 소유), `useNodeSelection.js`(노드 선택 훅).
- 화면 컴포넌트: `PersonHub.jsx`, `MapView.jsx`, `TimelineView.jsx`, `BibleOverviewView.jsx`, `SidePanel.jsx`, `JourneyList.jsx`, `EventVerses.jsx`.
- 지도 헬퍼(MapView 분리): `mapGeo.js`(기하·GeoJSON), `mapLayers.js`(소스·레이어·이벤트 핸들러), `mapRingController.js`(링/스파이더 애니메이션).
- 공유 모듈: `api.js`(`apiGet`), `theme.js`(`TYPE_COLOR`/`TYPE_KO`/`typeColor`/`SELECT_HL`), `constants.js`(`MOBILE_BREAKPOINT`/`SHEET_VH`).
- 작은 공통 UI: `Spinner.jsx`, `VerseLangTabs.jsx`.
- 전역 스타일: `index.css`. HTML 셸: `frontend/index.html`. 빌드 설정: `vite.config.js`(maplibre/vendor manualChunks), `eslint.config.js`.

### 모바일 읽기 모드 관련 파일 위치

- `App.jsx:43` — `readingEventId` 상태 선언.
- `App.jsx:267-295` — 모바일 여정 블록: 컨테이너 높이 토글(`42dvh`↔`90dvh`) + 지도 밴드 탭 캐처 + `JourneyList` controlled 렌더.
- `JourneyList.jsx:14` — `readingEventId`/`onReadingChange` props 수신. `onReadingChange != null`이면 controlled 모드.
- `JourneyList.jsx:37-49` — controlled 모드에서 `readingEventId`가 있으면 리스트 대신 `EventVerses` 단독 표시.
- `EventVerses.jsx:45` — `heading`/`onClose` props 존재 여부로 읽기 레이아웃 vs 인라인 레이아웃 분기.
- `EventVerses.jsx:27-33` — 읽기 모드 전용 스타일 상수(`readWrapStyle`/`readHeadStyle`/`readTopStyle`/`readBodyStyle`/`closeBtnStyle`).

## 최상위 (top-level)

- `docker-compose.yml` — neo4j(127.0.0.1:7474/7687) / api(`./data:/app/data`) / nginx(8080:80, `frontend/dist` ro 마운트).
- `nginx/nginx.conf` — `/api/`→`api:8000` 프록시, 정적 immutable 캐시, `try_files … /index.html` SPA 폴백.
- `deploy.sh` — 빌드·재배포·한글이름 주입 파이프라인(lock 파일 `/tmp/biblemap-deploy.lock`, 로그 `~/Library/Logs/com.biblemap.deploy.log`).
- `.github/workflows/deploy.yml` — `push: branches:[main]` → `runs-on: self-hosted` → `git reset --hard origin/main` → `bash deploy.sh`.
- `.env` / `.env.example` — `NEO4J_PASSWORD`(compose가 `NEO4J_AUTH` 파생).
- `backend/Dockerfile` — `python:3.12-slim`, `requirements.txt` 설치, `app/` 복사, `CMD uvicorn app.main:app --host 0.0.0.0 --port 8000`.
- `BIBLEMAP_PLAN.md` — 설계 문서("하나의 그래프, 세 가지 렌더링"·Neo4j 확정 등 원칙). `CLAUDE.md` — 작업 가이드라인. `README.md`.

## 네이밍 컨벤션 요약

- **`theographic_id`** — 모든 그래프 노드의 식별자 키. 프론트·백엔드 응답 전반에서 `id`로 노출.
- **slug** — 큐레이션 인물 파일/매핑 키(`abraham`, `john_the_apostle` 등 snake_case). 백엔드 `_ERA`/`_NAME_KO` dict 키.
- **authored 사건 id** — `authored-<인물>-<장소>-<사건>` 패턴(예 `authored-jesus-bethlehem-birth`).
- **authored 장소 id** — `authored-place-<name>` 패턴.
- **authored 인물 id** — `authored-person-<slug>` 패턴(예 `authored-person-gideon`, `authored-person-daniel`). Theographic에 없는 큐레이션 주인공에만 사용. 현재 **12인**(`data/authored_persons/people.json`).
- **백엔드 모듈 내부 함수**: 캐시·헬퍼는 `_` 접두 비공개(`_build_list`, `_compute_events`, `_resolve`), 다수 `@functools.lru_cache`.
- **API 경로**: 리소스 단수 + 동작(`/person/{id}/journey`, `/event/{id}/verses`, `/node/{id}/places`); 목록은 복수(`/events`, `/persons/curated`, `/books-overview`).
- **사람이 읽는 라벨·docstring은 한글**, 식별자/키/경로는 영문.
