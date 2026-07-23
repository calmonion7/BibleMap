---
last_mapped_commit: 70f5fc64daa7b3c71f2773a4357ad68bba9ae7a5
mapped: 2026-07-24
---

# STRUCTURE

## 최상위 디렉터리 레이아웃

```
BibleMap/
├── backend/            FastAPI 앱 + 데이터 로더/생성 스크립트
│   ├── app/            런타임 앱(라우트·db·overlays)
│   ├── scripts/        빌드타임 로더/주입/생성/검증 스크립트
│   └── Dockerfile      python:3.12-slim, CMD uvicorn app.main:app
├── frontend/           React 19 + Vite SPA
│   ├── src/            컴포넌트·훅·유틸
│   ├── public/
│   ├── dist/           빌드 산출물(nginx가 마운트, git-ignored)
│   ├── vite.config.js  __BUILD_ID__ define + manualChunks(maplibre/vendor)
│   └── eslint.config.js
├── data/               그래프 로더 입력 + 런타임 오버레이 JSON(api가 /app/data로 마운트)
├── nginx/nginx.conf    /api → api:8000 프록시 + 정적 캐시 규칙
├── docker-compose.yml  neo4j · api · nginx (프로젝트명 biblemap)
├── deploy.sh           빌드→컨테이너 재시작→inject_ko_names
├── .github/workflows/deploy.yml   self-hosted 러너, push main
├── .env / .env.example  NEO4J_PASSWORD
├── README.md
├── BIBLEMAP_PLAN.md
└── CLAUDE.md
```

## 백엔드 (`backend/`)

### 런타임 앱 (`backend/app/`)

- `main.py` — FastAPI 진입점. `_configure_logging()`, `lifespan`(인덱스), CORS(GET only), `include_router` 13개.
- `db.py` — `get_driver()` Neo4j 드라이버 싱글턴.
- `overlays.py` — `_resolve`/`_resolve_dir`/`_load` + 오버레이 함수(각 `@lru_cache(maxsize=1)`) + `curated_person_id`.
- `routes/` — 라우터 모듈(각 `router = APIRouter()`, prefix 없이 절대 경로):

  | 파일 | 주요 경로 |
  |---|---|
  | `nodes.py` | `/node/{id}`, `/node/{id}/places`, `/node/{id}/neighbors/grouped`, `/person/{id}/event-ids` |
  | `events.py` | `/events`, `/covenants`, `/messianic-prophecies`, `/topical-verses`, `/parables-miracles`, `/event/{id}/verses` |
  | `stats.py` | `/stats` (그래프 집계, `ERA_BANDS` — TimelineView와 수동 복제) |
  | `books.py` | `/books-overview`, `/book/{id}/chapters`, `/book/{id}/quotations`, `/book/{id}/chapter/{n}` |
  | `persons.py` | `/persons/curated`, `/keypeople-cards`, `/person/{id}/connections`, `/person/{id}/relations` |
  | `journey.py` | `/person/{id}/journey` (+ 공유 헬퍼 `_build_id_to_slug`·`_load_events`·`_fetch_place_coords`) |
  | `tours.py` | `/tours`, `/tour/{id}` |
  | `family.py` | `/person/{id}/family` |
  | `places.py` | `/place/{id}/curated-persons` |
  | `reliance.py` | `/person/{id}/reliance`, `/reliance/ranking` |
  | `words.py` | `/words/{book}`, `/words/{book}/verses` |
  | `verses.py` | `/verse/{id}/persons` |
  | `search.py` | `/search` |

  - overlays를 import하는 라우트: `events.py`·`books.py`·`verses.py`·`words.py`(그 외 `journey.py`·`tours.py`는 `overlays._resolve`/`_resolve_dir` 직접 사용). `stats.py`는 `journey.py`·`persons.py`의 내부 헬퍼를 재사용.

### 스크립트 (`backend/scripts/`)

접두사가 역할을 나타낸다:

- `load_*.py` — Neo4j 노드/관계 적재(멱등). `load_theographic.py`(원본), `load_authored_*`·`load_books`·`load_person_events`·`load_verse_events`(저작).
- `inject_*.py` — 기존 노드에 프로퍼티 SET. `inject_ko_names`·`inject_date_corrections`·`inject_book_context`·`inject_person_context`·`inject_person_traits`·`inject_place_context`.
- `generate_*.py` — 오버레이 JSON 산출(일부 Claude API 사용). `generate_bible_text`(→`bible/verses.json`)·`generate_event_verses`·`generate_book_context`·`generate_person_context` 등.
- `build_*.py` — 색인/분포 빌드. `build_word_distribution`(→`word_distribution.json`)·`build_verse_persons`·`build_word_verse_index`.
- `validate_*.py` — 데이터 검증(`validate_covenants`·`validate_messianic_prophecies`·`validate_parables_miracles`·`validate_topical_verses`·`validate_event_chronology`·`validate_traits` 등).
- `apply_event_dedupe.py` — 중복 이벤트 실삭제(`data/event_dedupe/dedupe.json` 기반).

## 프론트엔드 (`frontend/src/`)

### 진입 · 상태 · 유틸

- `main.jsx` — 루트 렌더(StrictMode, 라이트 테마 동기 반영).
- `App.jsx` — 스테이지 조건 렌더 + 스테이지별 내비 바 + 상세 시트/패널.
- `useStageNavigation.js` — 스테이지·URL·히스토리 상태 머신(핸들러 `openBook`·`openStats`·`openTopics` 등 export).
- `useNodeSelection.js` — 노드 선택/히스토리 원시값.
- `urlState.js` — `encodeHash`/`parseHash` 해시 코덱.
- `api.js` — `apiGet` 공유 클라이언트.
- `theme.js` — `TYPE_COLOR`·`TYPE_KO`·`PM_TYPE_COLOR`·`GENRE_META`·`VALENCE_COLOR`.
- `constants.js` — `MOBILE_BREAKPOINT`(768)·`SHEET_VH`·`JOURNEY_SHEET_VH`.
- `dates.js` — 연대 표기 헬퍼.
- `scrollMemory.js` — 스크롤 위치 복원.
- `index.css` — 전역 CSS 변수(테마별 `--type-*`·`--paper*`·`--gold*` 등)·애니메이션.

### 뷰 컴포넌트 (스테이지 본문)

| 파일 | 스테이지/역할 |
|---|---|
| `IntroView.jsx` | `intro` — 오토플레이 시네마틱 관문 |
| `PersonHub.jsx` | `hub` — 인물 선택 |
| `BibleOverviewView.jsx` | `overview` — 책 둘러보기 + 메시아 예언→성취 스레드(task#246) |
| `SidePanel.jsx` | `book` 본문 + 우측/시트 노드 상세 |
| `ChapterReader.jsx` | `reader` — 본문 읽기 |
| `FamilyTree.jsx` | `family` — 가계도 |
| `WordDistributionView.jsx` | `words` — 단어 분포 |
| `StatsView.jsx` | `stats` — 성경 통계(이 세션 신규, `/stats` 소비) |
| `TopicalVersesView.jsx` | `topics` — 주제 성구(이 세션 신규, `/topical-verses` 소비) |
| `TourList.jsx` | `tours` — 투어 목록 |
| `MapView.jsx` | `explore/map` — 지도(비유·기적 pm 레이어 토글 포함) |
| `TimelineView.jsx` | `explore/timeline` — 연표 + 언약 리본(task#247) + 비유·기적 레이어(task#249) |
| `RelationsView.jsx` | `explore/relations` |
| `RelianceView.jsx` | `explore/reliance` |
| `PersonIntro.jsx` / `TourIntro.jsx` | `explore/intro`(인물/투어) |

### 지원 컴포넌트 · 지도 · 심볼

- 지도: `mapLayers.js`(소스/레이어/핸들러)·`mapGeo.js`(GeoJSON 변환)·`mapRingController.js`(링 애니메이션).
- 절/구절: `VerseLayer.jsx`(양피지 모달 쉘, `paperTextStyle`·`VerseBookTabs` export)·`VerseLangTabs.jsx`.
- 투어: `TourPlayback.jsx`(`useTourPlayback`)·`tourSketches.jsx` + `sketches/*.jsx`(투어별 장면 모듈 + `lib.jsx` 표준).
- 심볼: `personSymbols.jsx`(인물 인장, `hasSymbol`)·`bookSymbols.jsx`(책 상징).
- 기타: `SpineHeader.jsx`(전역 헤더, `HEADER_H`·`RIBBON_OVERHANG` export)·`JourneyList.jsx`·`PersonMiniCard.jsx`·`Spinner.jsx`·`BookStageMap.jsx`.

## 데이터 (`data/`)

`api` 컨테이너가 `/app/data`로 마운트하며 오버레이 로더의 `DATA_DIR` 기본값이 이를 가리킨다. 서브디렉터리 하나가 대체로 오버레이 함수 하나에 대응한다.

- 절 본문/색인: `bible/`(verses.json)·`verse_persons/`·`verse_events/`·`word_verse_index/`·`word_distribution.json`·`word_sentiment.json`.
- 사건/연대: `event_verses/`·`book_events/`·`book_years_approx/`·`date_corrections/`·`event_dedupe/`·`authored_events/`.
- 인물: `authored_persons/`·`person_events/`(slug별)·`person_context/`·`person_relations/`·`person_slugs/`·`character_traits/`·`god_reliance/`·`keypeople/`·`keypeople_verses/`·`names_ko/`.
- 장소/책: `place_coords/`·`place_context/`·`book_context/`·`chapter_summaries/`·`chapter_sections/`.
- 주제 콘텐츠(이 세션 신규 소비): `covenants/covenants.json`·`messianic_prophecies/prophecies.json`·`topical_verses/topics.json`·`jesus_parables_miracles/index.json`.
- 인용/투어: `quotations/`·`tours/<id>.json`.

## 명명 규약

- **Neo4j 식별자**: 노드 안정 키는 `theographic_id`. 인물 큐레이션은 별도 `slug`(파일명·URL용).
- **URL slug**: 인물·투어는 `#/person/<slug>`·`#/tour/<slug>`, 책은 slug 없이 `#/book/<theographic_id>`.
- **백엔드 내부 헬퍼**: 밑줄 접두사(`_compute_events`·`_load_events`·`_fetch_place_coords`·`_resolve`). 라우트 캐시 함수는 `@functools.lru_cache(maxsize=1)`.
- **프론트 파일**: 뷰/컴포넌트는 PascalCase `.jsx`(`StatsView.jsx`), 훅은 camelCase `use*.js`(`useStageNavigation.js`), 순수 유틸은 camelCase `.js`(`urlState.js`·`mapGeo.js`).
- **API 경로**: kebab-case(`/messianic-prophecies`·`/topical-verses`·`/parables-miracles`·`/books-overview`·`/keypeople-cards`).
- **데이터 파일**: 디렉터리는 snake_case(`jesus_parables_miracles`·`messianic_prophecies`), 내부 JSON은 대체로 `<복수명>.json`(`covenants.json`·`prophecies.json`·`topics.json`·`index.json`).
- **스크립트**: 동사 접두사(`load_`·`inject_`·`generate_`·`build_`·`validate_`·`apply_`) + 대상.
- **주석/문서**: 한글. 로깅은 `[Component]` prefix 규약(`.forge/codebase/CONVENTIONS.md` 로깅 방출 규약).
- **ADR 참조**: 코드 주석이 결정 번호(ADR-0009 해시 딥링크, ADR-0010 뒤로가기 통합, ADR-0011 투어 오버레이, ADR-0020 라이트 테마, ADR-0026 책등 헤더 등)로 상호 참조.
