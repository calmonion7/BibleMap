---
last_mapped_commit: 4ad1d837a3771f69f53877b128938124b68d920b
mapped: 2026-08-21
---

# STRUCTURE

## 최상위 레이아웃

```
BibleMap/
├── backend/                  FastAPI 앱 + 데이터 로더/생성/검증 스크립트
│   ├── app/                  런타임 앱(routes·db·overlays) — 이미지에 들어가는 유일한 부분
│   ├── scripts/              빌드타임 스크립트(호스트 실행)
│   ├── requirements.txt      fastapi · neo4j · uvicorn (3줄)
│   └── Dockerfile            python:3.12-slim, COPY app/ 만, CMD uvicorn app.main:app
├── frontend/                 React 19 + Vite SPA
│   ├── src/                  컴포넌트·훅·유틸(플랫, 하위 디렉터리는 sketches/ 하나뿐)
│   ├── public/               favicon.svg · fonts/
│   ├── dist/                 빌드 산출물(nginx가 마운트, git-ignored)
│   ├── index.html
│   ├── vite.config.js        __BUILD_ID__ define + manualChunks(maplibre/vendor)
│   ├── eslint.config.js      flat config, __BUILD_ID__ 전역 선언
│   └── .env.production       VITE_API_URL=/api
├── data/                     그래프 로더 입력 + 런타임 오버레이 JSON(api가 /app/data로 마운트)
├── scripts/check.sh          배포 전 검증 게이트(AI 불요, 단독 실행 가능)
├── scripts/uat_*.py          브라우저 실측 UAT(check.sh 미배선 — deploy.sh가 빌드 전에 check.sh를 부르므로 :8080이 옛 빌드일 때가 있어서다)
├── nginx/nginx.conf          /api → api:8000 프록시 + 정적 캐시 규칙 + SPA 폴백
├── docker-compose.yml        neo4j · api · nginx (프로젝트명 biblemap)
├── deploy.sh                 Neo4j 대기 → inject 2종 → npm install → 검증(엄격) → 빌드 → api 이미지 → up -d(nginx는 강제 재생성)
├── .github/workflows/deploy.yml   push main → self-hosted 러너 → deploy.sh
├── .forge/                   forge 루프 상태 + 영구 문서(CONTEXT.md·adr/·retro/·codebase/)
├── .claude/agents/           프로젝트 도메인 서브에이전트 카드 5종
├── .env / .env.example       NEO4J_PASSWORD (.env는 git-ignored)
├── README.md                 로컬 실행 순서(적재 → API → 프론트)
├── BIBLEMAP_PLAN.md          초기 기획 문서
└── CLAUDE.md                 프로젝트 규칙(로깅 규약 포인터)
```

## 백엔드 (`backend/`)

### 런타임 앱 (`backend/app/`)

| 파일 | 내용 |
|---|---|
| `main.py` | FastAPI 진입점. `_configure_logging()`(라우터 import 전 1회) → `lifespan`(인덱스) → CORS(GET) → `include_router` 14개 |
| `db.py` | `get_driver()` Neo4j 드라이버 싱글턴 |
| `overlays.py` | `_resolve`/`_resolve_dir`/`_load` + 오버레이 함수 15개(각 `@lru_cache(maxsize=1)`) + `curated_person_id` |
| `curated.py` | 큐레이션 인물 색인의 정본(task#278, `persons.py`에서 승급). `CURATED`(slug→{nameKo,era}, 35)·`ERA_ORDER`·`person_events(slug)`·`curated_index()`·`id_to_slug()`/`slug_to_id()`·`seal_id_to_slug()`(50) — 8개 라우트가 import |
| `verse_search.py` | `search_verses(term, book_id, match_en)` — 절 본문 substring 검색 공용 헬퍼(`@lru_cache(256)`), `search.py`·`words.py` 공유 |
| `routes/` | 라우터 모듈 14개(각 `router = APIRouter()`, prefix 없이 절대 경로) |

`backend/app/routes/` 파일별 주요 경로:

| 파일 | 경로 |
|---|---|
| `nodes.py` | `/node/{id}`, `/node/{id}/places`, `/node/{id}/neighbors/grouped`, `/person/{id}/event-ids` |
| `events.py` | `/events`, `/covenants`, `/messianic-prophecies`, `/topical-verses`, `/parables-miracles`, `/event/{id}/verses` |
| `stats.py` | `/stats` (그래프 집계, `ERA_BANDS` — `frontend/src/eraBands.js`와 수동 복제) |
| `timeline.py` | `/timeline/canon` (통사 연표, task#271 — 신규 저작 0, `stats.ERA_BANDS`·`events._compute_events`·`person_events/*.json`을 재조합) |
| `books.py` | `/books-overview`, `/book/{id}/chapters`, `/book/{id}/quotations`, `/book/{id}/chapter/{n}` |
| `persons.py` | `/persons/curated`, `/keypeople-cards`, `/person/{id}/connections`, `/person/{id}/relations` |
| `journey.py` | `/person/{id}/journey` (+ 공유 헬퍼 `_fetch_place_coords`; slug↔id·이벤트 로드는 task#278에 `curated.py`로 이관) |
| `tours.py` | `/tours`, `/tour/{id}` |
| `family.py` | `/person/{id}/family` |
| `places.py` | `/place/{id}/curated-persons`, `/place/{id}`(장소 페이지, task#270) |
| `reliance.py` | `/person/{id}/reliance`, `/reliance/ranking` |
| `words.py` | `/words/{book}`, `/words/{book}/verses`(`verse_search.search_verses` 재사용) |
| `verses.py` | `/verse/{id}/persons` |
| `search.py` | `/search`(통합 검색, task#267 — 노드 + 절 본문 `{nodes, verses}`, `verse_search.search_verses` 재사용) |

라우트 간 결합에서 알아야 할 것:

- `backend/app/curated.py`(`overlays.py`와 같은 층 — 라우트를 import하지 않아 순환 import 차단)가 큐레이션 인물 레지스트리의 정본이다: `CURATED`(slug→{nameKo,era}, 35개)·`ERA_ORDER`·`person_events(slug)`·`curated_index()`·`id_to_slug()`/`slug_to_id()`·`seal_id_to_slug()`(인장 조회용 50). `persons.py`·`journey.py`·`tours.py`·`stats.py`·`places.py`·`reliance.py`·`family.py`·`timeline.py` 8개 라우트가 이를 import한다(task#278 — 그전엔 `persons.py`가 `_ERA`/`_NAME_KO`/`_ERA_ORDER`를 소유했고, `family.py`는 순환 회피용 지연 import(`from .persons import _build_list`)로 우회했다; 둘 다 이관으로 사라졌다). "13인" 같은 오래된 docstring 표현도 이 이관 과정에서 35로 정정됐다.
- `stats.py`는 자체 헬퍼 대신 `curated.id_to_slug`·`person_events`·`slug_to_id`와 `journey._fetch_place_coords`를 재사용한다. `timeline.py`는 여기에 더해 `stats.ERA_BANDS`·`_era_of`와 `events._compute_events`를 재사용한다(신규 쿼리·저작 없이 세 출처를 재조합).
- `overlays` 모듈을 통째로 import하는 라우트는 `events.py`·`books.py`·`words.py`·`verses.py`·`places.py`(task#270부터 — `place_context()`·`place_coords()` 소비). 나머지(`journey.py`·`tours.py`·`persons.py`·`reliance.py`·`family.py`)는 slug별 파일을 직접 읽어야 해서 `overlays._resolve`/`_resolve_dir`만 가져다 쓴다. `verse_search.py`도 `overlays.bible_verses()`·`books_ko()`를 통째 import로 쓴다(라우트는 아니지만 `search.py`·`words.py`가 위임하는 공용 모듈).
- 새 큐레이션 인물을 추가하려면 `curated.py`의 `CURATED` dict에 slug를 더하고 `data/person_events/<slug>.json`을 저작한다. `backend/scripts/validate_curated_persons.py`가 `CURATED` 키 집합 ↔ `data/person_events/*.json`(양방향) · `data/god_reliance/*.json`의 slug ⊆ `CURATED` · `person_slugs/seal_slugs.json`과 `CURATED`의 교집합 == ∅ · 각 era ∈ `ERA_ORDER`를 게이트에서 검사한다(task#278).

### 스크립트 (`backend/scripts/`)

접두사가 곧 역할이다. 전부 호스트에서 실행하며(`backend/Dockerfile`이 `app/`만 COPY), `python3 -m backend.scripts.<name>` 형태도 가능하다(`__init__.py` 있음).

| 접두사 | 역할 | 예 |
|---|---|---|
| `load_*` | Neo4j 노드·관계 멱등 적재 | `load_theographic`(원본), `load_authored_events`/`_persons`/`_genealogy`/`_mothers`, `load_books`, `load_person_events`, `load_verse_events` |
| `inject_*` | 기존 노드에 프로퍼티 SET | `inject_ko_names`, `inject_date_corrections`, `inject_book_context`, `inject_person_context`, `inject_person_traits`, `inject_place_context` |
| `generate_*` | 오버레이 JSON 산출(일부 LLM 사용, ADR-0006) | `generate_bible_text`, `generate_event_verses`, `generate_book_context`(+`_enrich`), `generate_book_events`, `generate_person_context`, `generate_person_event_verses`, `generate_person_traits`, `generate_verse_events`, `generate_verse_text`, `generate_approx_book_verses` |
| `build_*` | 색인·분포 빌드 | `build_word_distribution`, `build_verse_persons`, `build_word_verse_index` |
| `validate_*` | 데이터 검증(20종 `scripts/check.sh` 게이트 항목 + Neo4j 필요 1종 + 독립 위생 가드 1종) | `validate_covenants`, `validate_messianic_prophecies`, `validate_parables_miracles`, `validate_topical_verses`, `validate_pm_map_coverage`, `validate_scene_coverage`(투어 정차지↔장면 스케치 커버리지, task#259), `validate_chapter_sections`, `validate_chapter_summaries`, `validate_quotations`, `validate_person_context`, `validate_god_reliance`, `validate_traits`, `validate_era_bands_consistency`(시대 이름·순서·경계 7축, task#255→284), `validate_approx_book_verses`(생성기 `VERSE_MAP`↔`book_events` 정합, task#274), `validate_intro_menu_parity`(인트로 소개 장면↔실제 하위 메뉴 정합, task#277), `validate_curated_persons`(CURATED↔person_events/god_reliance/seal_slugs 정합, task#278), `validate_intro_gutter`(인트로 비트 프레임의 `boxSizing`·여백 규약, task#280), `validate_intro_entry_route`(무타깃 진입 판정 단일 선언, task#281), `validate_event_verses`(근거 절↔rangeLabel 경계 정합, task#282), `validate_sortkey_startdate`(sortKey↔startDate 역전 + yearLabel 정합, task#283), `validate_event_chronology`(Neo4j 필요), `validate_forge_docs_tracked`(`.forge/adr`·`.forge/retro` 미추적 0건 — 데이터 검증이 아닌 로컬 위생 가드, 별도 절로 실행, task#279). 상당수가 `--selftest`로 고의 결함 주입 대조군을 갖는다(ADR 260820-003946) |
| `apply_*` / `enrich_*` | 일회성 데이터 조작 | `apply_event_dedupe`(`data/event_dedupe/dedupe.json` 기반 실삭제), `enrich_place_coords` |

## 프론트엔드 (`frontend/src/`)

디렉터리는 `sketches/` 하나뿐이고 나머지는 전부 플랫이다.

### 진입 · 상태 · 유틸

| 파일 | 역할 |
|---|---|
| `main.jsx` | 루트 렌더(StrictMode) + 라이트 테마 동기 반영 |
| `App.jsx` | 스테이지 조건 렌더(13종) + `StageNav` 조립 + 상세 시트/패널 + 검색 오버레이 + 여정·재생·개인화 훅 소유(task#257~258로 988줄→535줄 분해) |
| `StageNav.jsx` | 스테이지 하위 내비 공용 껍데기(`onBack`·`lead`·`auxLabel`·`trailing` 슬롯 + `StageNav.Tab`/`StageNav.Title`, `NAV_H` export) — 과거 스테이지별 `render<X>Nav()` 9개를 대체 |
| `ExploreStage.jsx` | `explore` 스테이지 전용(지도·연표·관계·소개·의존·족보 6뷰 조립) — App.jsx에서 분리(task#257), `journey`·`playback`은 prop으로 주입받음 |
| `useStageNavigation.js` | 스테이지·URL·히스토리 상태 머신(모든 `open*`/`*Back` 핸들러 export) |
| `useNodeSelection.js` | 노드 선택/히스토리 원시값 |
| `useExploreJourney.js` | 탐험 여정 데이터(정차지·투어 메타·인물 사건 Set) — **App에서만 호출**(ExploreStage 언마운트 시 상태 유실 방지, 파일 상단 주석 근거) |
| `useTourPlayback.js` | 투어 자동재생 시퀀서 훅(상태만, 카메라는 App/MapView) |
| `useBookmarks.js` | 북마크·최근 이어보기(task#268, `localStorage` 전용, 서버 쓰기 없음) |
| `useReadingProgress.js` | 장 단위 읽음 표시 + 이어읽기 판정 `computeResume`(task#269, `localStorage` 전용) |
| `urlState.js` | `encodeHash`/`parseHash` 해시 코덱 + `isNoTarget(hash)`(무타깃 진입 판정 단일 정본, task#281) |
| `eraBands.js` | `ERA_BANDS`·`eraOf(y)` — task#271에 `TimelineView.jsx`에서 공용 모듈로 승급(`backend/app/curated.py`의 `ERA_ORDER`·`backend/app/routes/stats.py`·`PersonHub.jsx`의 `ERA_ORDER`와 수동 복제, `validate_era_bands_consistency`가 7축으로 검사) |
| `api.js` | `apiGet(path, {signal})` 공유 클라이언트 |
| `theme.js` | `TYPE_COLOR`·`TYPE_KO`·`TYPE_ORDER`·`typeColor`/`typeKo`·`VALENCE_COLOR`·`PM_TYPE_COLOR`·`SELECT_HL`·`GENRE_META` |
| `constants.js` | `MOBILE_BREAKPOINT`(768)·`SHEET_VH`(75)·`JOURNEY_SHEET_VH`(42) |
| `dates.js` | `parseYear(startDate)` 연대 표기 |
| `scrollMemory.js` | `saveScroll`/`loadScroll` |
| `index.css` | 테마별 CSS 변수 정본 + keyframe/모션 클래스 |

순수 함수 모듈 일부는 `vitest`(task#261) 단위 테스트가 같은 디렉터리에 나란히 있다: `dates.test.js`·`mapGeo.test.js`·`mapRingController.test.js`·`urlState.test.js`·`useReadingProgress.test.js`. `npm test`(=`vitest run`)로 실행, `scripts/check.sh`가 배포 게이트에 배선한다.

### 뷰 컴포넌트 (스테이지 본문)

| 파일 | 스테이지 / 역할 |
|---|---|
| `IntroView.jsx` | `intro` — 7비트 오토플레이 시네마틱 필름(`INTRO_STORAGE_KEY` export) |
| `PersonHub.jsx` | `hub` — 인물 선택 |
| `BibleOverviewView.jsx` | `overview` — 책 둘러보기 + 메시아 예언→성취 스레드 |
| `SidePanel.jsx` | `book` 본문(전체화면 재사용) + 우측/시트 노드 상세 |
| `ChapterReader.jsx` | `reader` — 장 그리드 / 장 본문 |
| `FamilyTree.jsx` | `family` — 가계도 |
| `WordDistributionView.jsx` | `words` — 단어 분포 |
| `StatsView.jsx` | `stats` — 성경 통계(`/stats`) |
| `TopicalVersesView.jsx` | `topics` — 주제 성구(`/topical-verses`) |
| `CanonTimelineView.jsx` | `canon` — 통사 연표(`/timeline/canon`, task#271) |
| `PlaceView.jsx` | `place` — 장소 페이지(`/place/{id}`, task#270) |
| `TourList.jsx` | `tours` — 투어 목록 |
| `MapView.jsx` | `explore/map` — maplibre 지도 + 비유·기적 토글 |
| `TimelineView.jsx` | `explore/timeline` — 연표 + 언약 리본 + 비유·기적 섹션 |
| `RelationsView.jsx` | `explore/relations` |
| `RelianceView.jsx` | `explore/reliance` |
| `PersonIntro.jsx` / `TourIntro.jsx` | `explore/intro`(인물 / 투어) |
| `SearchPanel.jsx` | 전역(스테이지 무관) — `/` 단축키·헤더 검색 버튼으로 여는 통합 검색 오버레이(`/search`, task#267) |

### 지원 모듈

- 지도: `mapLayers.js`(소스·레이어·핸들러, `EMPTY_GEOJSON`)·`mapGeo.js`(GeoJSON 변환·기하)·`mapRingController.js`(`createRingController`).
- 절/구절: `VerseLayer.jsx`(포털 모달 쉘, `paperTextStyle`·`VerseBookTabs` export)·`VerseLangTabs.jsx`.
- 투어: `TourPlayback.jsx`(해설 카드, `tourSketches` lazy import)·`tourSketches.jsx`(`SCENES` 레지스트리 병합, `TourSketchPanel` export)·`sketches/`.
- 심볼: `personSymbols.jsx`(`PersonSymbol` default + `hasSymbol`)·`bookSymbols.jsx`(`BookSymbol` default).
- 개인화: `BookmarkToggle.jsx`(저장 토글 컴포넌트, `useBookmarks`가 넘긴 `saved`/`onToggle`만 받는 순수 표시).
- 기타: `SpineHeader.jsx`(전역 헤더 + 검색 버튼, `HEADER_H`·`RIBBON_OVERHANG` export)·`JourneyList.jsx`·`PersonMiniCard.jsx`·`Spinner.jsx`·`BookStageMap.jsx`.

### 장면 스케치 (`frontend/src/sketches/`)

투어 하나 = 파일 하나(camelCase). 현재 9개: `creationToFlood`·`patriarchsCovenant`·`exodusToConquest`·`ageOfJudges`·`davidUnitedKingdom`·`elijahAndElisha`·`exileAndReturn`·`gospelOfJesus`·`theEarlyChurch`. 각 파일은 `Scene` 컴포넌트들을 정의하고 파일 끝에서 `{ '<eventId>': { Scene, desc, caption, mood? } }` 레지스트리를 default export한다. 여기에 더해:

- `lib.jsx` — 순수 헬퍼만(`P`·`W`·`sw`·`d`). 선 굵기 위계·draw 규약이 주석에 정본으로 있다.
- `SceneLabel.jsx` — 장면 이름표 컴포넌트 `Label`. `lib.jsx`에서 분리된 이유는 `react-refresh/only-export-components` 규칙.

## 데이터 (`data/`)

`api` 컨테이너가 `/app/data`로 마운트하고 `DATA_DIR` 기본값이 이를 가리킨다. 서브디렉터리 하나가 대체로 오버레이 함수 하나 또는 로더 하나에 대응한다.

- 절 본문·색인: `bible/verses.json` · `verse_persons/index.json` · `verse_events/events.json` · `word_verse_index/index.json` · `word_distribution.json` · `word_sentiment.json`(최상위 파일 2개)
- 사건·연대: `event_verses/events.json` · `book_events/books.json` · `book_years_approx/books.json` · `date_corrections/{events,persons}.json` · `event_dedupe/dedupe.json` · `authored_events/events.json`
- 인물: `authored_persons/{people,genealogy,mothers}.json` · `person_events/<slug>.json`(35개) · `person_context/people.json` · `person_relations/relations.json` · `person_slugs/seal_slugs.json` · `character_traits/people.json` · `god_reliance/<slug>.json`(33개) · `keypeople/identity.json` · `keypeople_verses/people.json` · `names_ko/{books,events,groups,people,places}.json`
- 장소·책: `place_coords/places.json` · `place_context/places.json` · `book_context/books.json` · `chapter_summaries/books.json` · `chapter_sections/books.json`
- 주제 콘텐츠: `covenants/covenants.json` · `messianic_prophecies/prophecies.json` · `topical_verses/topics.json` · `jesus_parables_miracles/index.json`
- 인용·투어: `quotations/quotations.json` · `tours/<id>.json`(9개, 파일명 = 투어 id = URL slug)
- 저작 규칙: `character_traits/AUTHORING.md` · `person_context/AUTHORING.md` · `person_relations/AUTHORING.md` — 통제 어휘와 저작 경계 규칙이 데이터 옆에 산다.

## 명명 규약

- **Neo4j 식별자**: 모든 라벨의 안정 키는 `theographic_id`. 큐레이션 인물만 별도 `slug`(파일명·URL용). 책은 slug가 없다.
- **URL**: 인물·투어는 slug(`#/person/<slug>`·`#/tour/<slug>`), 책·가계도·단어는 id(`#/book/<theographic_id>` 등).
- **API 경로**: kebab-case(`/books-overview`·`/keypeople-cards`·`/messianic-prophecies`·`/topical-verses`·`/parables-miracles`).
- **백엔드 내부 헬퍼**: 밑줄 접두사(`_compute_events`·`_fetch_place_coords`·`_resolve`). `curated.py`의 공개 헬퍼(`person_events`·`curated_index`·`id_to_slug` 등)는 예외 — 여러 라우트가 import하는 공유 정본이라 밑줄 없이 공개 이름을 쓴다. 캐시는 `@functools.lru_cache(maxsize=...)`.
- **프론트 파일**: 뷰·컴포넌트는 PascalCase `.jsx`(`StatsView.jsx`), 훅은 camelCase `use*.js`(`useTourPlayback.js`), 순수 유틸은 camelCase `.js`(`urlState.js`·`mapGeo.js`). 심볼·스케치처럼 JSX를 반환하는 비컴포넌트 모듈은 camelCase `.jsx`(`personSymbols.jsx`·`tourSketches.jsx`).
- **데이터**: 디렉터리는 snake_case(`jesus_parables_miracles`·`messianic_prophecies`), 파일은 대체로 `<복수명>.json`(`covenants.json`·`prophecies.json`·`topics.json`·`index.json`) 또는 `<slug>.json`. 투어 파일명은 kebab-case(`gospel-of-jesus.json`).
- **스크립트**: 동사 접두사(`load_`·`inject_`·`generate_`·`build_`·`validate_`·`apply_`·`enrich_`) + snake_case 대상. `backend/scripts/`(호스트 실행, `scripts/check.sh`가 `--selftest` 지원 검증기를 대조군으로 부른다) 소속. 최상위 `scripts/uat_*.py`(예: `uat_intro_gutter.py`·`uat_intro_entry.py`)는 별개 접두사 — 브라우저를 실제로 띄워 픽셀·렌더 결과를 재는 **실측** UAT로, `check.sh`에는 배선하지 않는다(`deploy.sh`가 빌드 전에 `check.sh`를 부르므로 그 시점 :8080이 옛 빌드일 수 있어서다, task#280~281).
- **프론트 테스트**: 대상 모듈과 같은 디렉터리에 `<name>.test.js`(vitest, task#261). 예: `mapGeo.js`↔`mapGeo.test.js`.
- **로깅**: 백엔드는 모듈 logger + `[Component]` prefix(`[Overlays]`·`[Tours]`·`[Nodes]`·`[Startup]`), 프론트 빈값-폴백 catch는 `console.warn('[Component] ...')`. 상세는 `.forge/codebase/CONVENTIONS.md`의 로깅 방출 규약 절.
- **주석·문서**: 한글. 코드 주석이 결정 번호(ADR-0009 해시 딥링크, ADR-0010 뒤로가기, ADR-0011 투어 오버레이, ADR-0014 보수 연대, ADR-0020 라이트 테마, ADR-0024 모션, ADR-0026 책등 헤더, ADR-0028 투어 note, ADR-0029 스케치 모듈)와 task 번호를 상호 참조한다. ADR 본문은 `.forge/adr/`.

## 새 것을 어디에 추가하나

### 새 뷰(스테이지)

1. `frontend/src/<Name>View.jsx` 생성.
2. `frontend/src/useStageNavigation.js` — 대상 id가 필요하면 state 추가, `handleOpen<X>`/`handle<X>Back` 작성(대상 없는 고정 뷰는 `handleOpenStats`/`handleStatsBack`이 최소 템플릿), return 객체에 export.
3. `frontend/src/urlState.js` — `encodeHash`에 분기, `parseHash`에 패턴 추가.
4. `useStageNavigation.js`의 **복원 effect**(`parsed.stage === '...'` 분기), **sync effect**(`encodeHash` 인자·`state` 객체·`navSyncRef`·`isForward` 비교), **popstate effect**(`s.<field>` 복원) 세 곳을 함께 갱신. 대상 id가 없는 뷰면 3·4는 스테이지 분기만 추가하면 된다.
5. `frontend/src/App.jsx` — `activeStage === '<x>' && (...)` 조건 렌더 블록 추가, 그 안에서 `<StageNav onBack=... backLabel=...><StageNav.Tab .../></StageNav>`로 하위 내비를 조립(대상 없는 고정 뷰는 `stats`/`topics`/`canon` 블록이 최소 템플릿), `activeSection` 계산에 스테이지 편입.
6. 실제 하위 메뉴에 탭을 추가/변경했다면 `frontend/src/IntroView.jsx`의 해당 `SCENES` 항목 `tabs`도 같은 아이콘·라벨로 갱신한다 — `backend/scripts/validate_intro_menu_parity.py`가 배포 게이트에서 인트로↔실제 탭을 양방향 대조한다(task#277).

### 새 탐험 서브뷰(`exploreView` 탭)

`frontend/src/ExploreStage.jsx` 상단의 탭 상수(`EXPLORE_TABS`/`INTRO_TAB`/`RELATIONS_TAB`/`RELIANCE_TAB`/`FAMILY_TAB`/`TOUR_INTRO_TAB`)에 항목을 더하고, 같은 파일의 탭 배열 조립부(`StageNav.Tab` 나열)와 그 아래 `exploreView === '<key>' && ...` 렌더 블록, `urlState.js`의 person 서브패스 정규식·`encodeHash` 분기를 함께 고친다. 이 탭도 `IntroView.jsx`의 인물/투어 `SCENES` 항목과 정합해야 한다(위 5번과 동일 게이트).

### 새 스케치(투어 정차지 삽화)

- 기존 투어면 해당 `frontend/src/sketches/<tour>.jsx`에 `Scene` 컴포넌트를 추가하고 파일 끝 레지스트리에 `'<eventId>': { Scene, desc, caption, mood? }` 항목을 넣는다.
- 새 투어면 `frontend/src/sketches/<tourCamelCase>.jsx`를 만들고 `frontend/src/tourSketches.jsx`의 import + `SCENES` 스프레드에 추가한다.
- 헬퍼는 `sketches/lib.jsx`(`sw`로 선 굵기, `d`로 단계 딜레이), 이름표는 `sketches/SceneLabel.jsx`의 `Label`. viewBox는 `0 0 120 64`(`tourSketches.jsx`가 고정).

### 새 데이터 파일(오버레이)

1. `data/<snake_case>/<name>.json` 저작.
2. `backend/app/overlays.py`에 `@functools.lru_cache(maxsize=1)` 로더 함수 추가(docstring에 스키마 한 줄).
3. 소비할 라우트에서 호출. `verseID`만 들고 있는 데이터면 라우트에서 `overlays.bible_verses()`로 본문을 합성해 응답에 동봉한다.
4. 검증이 필요하면 `backend/scripts/validate_<name>.py`를 만들고 `scripts/check.sh`의 20종 루프 목록에 이름을 추가한다(고의 결함 대조군을 두려면 `--selftest` 분기를 만들고 별도 `run` 줄로 함께 배선한다, ADR 260820-003946).
5. 반영에는 **API 재시작**이 필요하다(`docker compose restart api`) — 로더가 `lru_cache`라 파일만 바꿔서는 안 바뀐다. `data/`는 볼륨 마운트라 이미지 재빌드는 불필요.

### 새 스크립트

`backend/scripts/<verb>_<target>.py`에 둔다. 접두사는 위 명명 규약 표를 따른다. Neo4j를 만지면 `NEO4J_URI`/`NEO4J_USER`/`NEO4J_PASSWORD`를 읽고 비밀번호 부재 시 `RuntimeError`로 죽는 기존 패턴을 그대로 쓰고, `load_*`/`inject_*`는 재실행 안전(멱등)해야 한다. `data/` 경로는 `Path(__file__).parent.parent.parent / "data"` 관행. 배포 게이트에 넣을 검증기라면 `python3 -m backend.scripts.<name>`으로 실행되고 실패 시 비0 종료해야 한다.

### 새 API 라우트

- 기존 도메인에 속하면 `backend/app/routes/<domain>.py`에 `@router.get(...)`만 추가한다.
- 새 파일이면 `router = APIRouter()`를 선언하고 `backend/app/main.py`의 import 라인과 `app.include_router(...)` 두 곳을 함께 고친다.
- 반환은 `JSONResponse(content=..., headers={"Cache-Control": "max-age=300"})` 관행(불변 데이터면 `public, max-age=3600`). 사용자 입력 없는 전역 응답은 `@functools.lru_cache(maxsize=1)` 계산 함수로 감싸고, 입력이 있으면 유한 `maxsize`를 준다.
- 없는 리소스는 도메인에 따라 갈린다 — 큐레이션 밖 인물·투어는 404가 아니라 빈 결과(soft-empty, `journey.py`·`tours.py`), 잘못된 책 id는 `HTTPException(404)`(`words.py`·`books.py`).
- 프론트 소비는 반드시 `frontend/src/api.js`의 `apiGet`을 통한다(캐시 버스팅·에러 시맨틱 일관).

### 새 투어

`data/tours/<kebab-id>.json`에 `{id, title, subtitle, era, description, stops:[{id, note}]}`를 쓴다. `era`는 `backend/app/curated.py`의 `ERA_ORDER` 값 중 하나여야 목록 정렬이 맞는다(`tours._list_tours`) — `validate_era_bands_consistency`가 이 축도 검사한다(task#284). `stops[].id`는 `data/person_events/*.json`에 존재하는 사건 id여야 하고, 모르는 id는 조용히 제거된다. Neo4j 적재는 필요 없다(ADR-0011). 정차지 삽화가 필요하면 위 "새 스케치" 절차를 따른다 — `validate_scene_coverage.py`(task#259)가 배포 게이트에서 모든 `stops[].id`에 스케치가 있는지 강제하므로(정당한 미저작 예외 목록 `EXPECTED_UNCOVERED`은 비어 있는 것이 정본), 스케치 없는 정차지를 추가하면 배포가 막힌다.
