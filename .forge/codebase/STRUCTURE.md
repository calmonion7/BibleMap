---
last_mapped_commit: 43f987cb37c2341c3cfeb54e4cf4dc33b4549c64
mapped: 2026-08-01
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
├── nginx/nginx.conf          /api → api:8000 프록시 + 정적 캐시 규칙 + SPA 폴백
├── docker-compose.yml        neo4j · api · nginx (프로젝트명 biblemap)
├── deploy.sh                 검증 → 프론트 빌드 → api 이미지 빌드 → up -d → inject_ko_names
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
| `main.py` | FastAPI 진입점. `_configure_logging()`(라우터 import 전 1회) → `lifespan`(인덱스) → CORS(GET) → `include_router` 13개 |
| `db.py` | `get_driver()` Neo4j 드라이버 싱글턴 |
| `overlays.py` | `_resolve`/`_resolve_dir`/`_load` + 오버레이 함수 14개(각 `@lru_cache(maxsize=1)`) + `curated_person_id` |
| `routes/` | 라우터 모듈 13개(각 `router = APIRouter()`, prefix 없이 절대 경로) |

`backend/app/routes/` 파일별 주요 경로:

| 파일 | 경로 |
|---|---|
| `nodes.py` | `/node/{id}`, `/node/{id}/places`, `/node/{id}/neighbors/grouped`, `/person/{id}/event-ids` |
| `events.py` | `/events`, `/covenants`, `/messianic-prophecies`, `/topical-verses`, `/parables-miracles`, `/event/{id}/verses` |
| `stats.py` | `/stats` (그래프 집계, `ERA_BANDS` — `TimelineView.jsx`와 수동 복제) |
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

라우트 간 결합에서 알아야 할 것:

- `persons.py`의 모듈 상수 `_ERA`(slug→시대, 현재 35개)·`_NAME_KO`(slug→한글명)·`_ERA_ORDER`가 큐레이션 인물 레지스트리다. `journey.py`·`tours.py`·`stats.py`가 이를 import한다(모듈 docstring에 남은 "13인"은 오래된 표현이며 실제는 35 slug).
- `stats.py`는 자체 헬퍼 대신 `journey._build_id_to_slug`·`_load_events`·`_fetch_place_coords`와 `persons._build_list`·`_NAME_KO`를 재사용한다.
- `overlays` 모듈을 통째로 import하는 라우트는 `events.py`·`books.py`·`words.py`·`verses.py`. 나머지(`journey.py`·`tours.py`·`persons.py`·`reliance.py`·`family.py`·`places.py`)는 slug별 파일을 직접 읽어야 해서 `overlays._resolve`/`_resolve_dir`만 가져다 쓴다.

### 스크립트 (`backend/scripts/`)

접두사가 곧 역할이다. 전부 호스트에서 실행하며(`backend/Dockerfile`이 `app/`만 COPY), `python3 -m backend.scripts.<name>` 형태도 가능하다(`__init__.py` 있음).

| 접두사 | 역할 | 예 |
|---|---|---|
| `load_*` | Neo4j 노드·관계 멱등 적재 | `load_theographic`(원본), `load_authored_events`/`_persons`/`_genealogy`/`_mothers`, `load_books`, `load_person_events`, `load_verse_events` |
| `inject_*` | 기존 노드에 프로퍼티 SET | `inject_ko_names`, `inject_date_corrections`, `inject_book_context`, `inject_person_context`, `inject_person_traits`, `inject_place_context` |
| `generate_*` | 오버레이 JSON 산출(일부 LLM 사용, ADR-0006) | `generate_bible_text`, `generate_event_verses`, `generate_book_context`(+`_enrich`), `generate_book_events`, `generate_person_context`, `generate_person_event_verses`, `generate_person_traits`, `generate_verse_events`, `generate_verse_text`, `generate_approx_book_verses` |
| `build_*` | 색인·분포 빌드 | `build_word_distribution`, `build_verse_persons`, `build_word_verse_index` |
| `validate_*` | 데이터 검증(대부분 `scripts/check.sh` 게이트 항목) | `validate_covenants`, `validate_messianic_prophecies`, `validate_parables_miracles`, `validate_topical_verses`, `validate_pm_map_coverage`, `validate_chapter_sections`, `validate_chapter_summaries`, `validate_quotations`, `validate_person_context`, `validate_god_reliance`, `validate_traits`, `validate_era_bands_consistency`, `validate_event_chronology`(Neo4j 필요) |
| `apply_*` / `enrich_*` | 일회성 데이터 조작 | `apply_event_dedupe`(`data/event_dedupe/dedupe.json` 기반 실삭제), `enrich_place_coords` |

## 프론트엔드 (`frontend/src/`)

디렉터리는 `sketches/` 하나뿐이고 나머지는 전부 플랫이다.

### 진입 · 상태 · 유틸

| 파일 | 역할 |
|---|---|
| `main.jsx` | 루트 렌더(StrictMode) + 라이트 테마 동기 반영 |
| `App.jsx` | 스테이지 조건 렌더 + 스테이지별 내비 바 + 상세 시트/패널 + 여정 데이터 소유 |
| `useStageNavigation.js` | 스테이지·URL·히스토리 상태 머신(모든 `open*`/`*Back` 핸들러 export) |
| `useNodeSelection.js` | 노드 선택/히스토리 원시값 |
| `useTourPlayback.js` | 투어 자동재생 시퀀서 훅(상태만, 카메라는 App/MapView) |
| `urlState.js` | `encodeHash`/`parseHash` 해시 코덱 |
| `api.js` | `apiGet(path, {signal})` 공유 클라이언트 |
| `theme.js` | `TYPE_COLOR`·`TYPE_KO`·`TYPE_ORDER`·`typeColor`/`typeKo`·`VALENCE_COLOR`·`PM_TYPE_COLOR`·`SELECT_HL`·`GENRE_META` |
| `constants.js` | `MOBILE_BREAKPOINT`(768)·`SHEET_VH`(75)·`JOURNEY_SHEET_VH`(42) |
| `dates.js` | `parseYear(startDate)` 연대 표기 |
| `scrollMemory.js` | `saveScroll`/`loadScroll` |
| `index.css` | 테마별 CSS 변수 정본 + keyframe/모션 클래스 |

### 뷰 컴포넌트 (스테이지 본문)

| 파일 | 스테이지 / 역할 |
|---|---|
| `IntroView.jsx` | `intro` — 6비트 오토플레이 시네마틱 필름(`INTRO_STORAGE_KEY` export) |
| `PersonHub.jsx` | `hub` — 인물 선택 |
| `BibleOverviewView.jsx` | `overview` — 책 둘러보기 + 메시아 예언→성취 스레드 |
| `SidePanel.jsx` | `book` 본문(전체화면 재사용) + 우측/시트 노드 상세 |
| `ChapterReader.jsx` | `reader` — 장 그리드 / 장 본문 |
| `FamilyTree.jsx` | `family` — 가계도 |
| `WordDistributionView.jsx` | `words` — 단어 분포 |
| `StatsView.jsx` | `stats` — 성경 통계(`/stats`) |
| `TopicalVersesView.jsx` | `topics` — 주제 성구(`/topical-verses`) |
| `TourList.jsx` | `tours` — 투어 목록 |
| `MapView.jsx` | `explore/map` — maplibre 지도 + 비유·기적 토글 |
| `TimelineView.jsx` | `explore/timeline` — 연표 + 언약 리본 + 비유·기적 섹션 |
| `RelationsView.jsx` | `explore/relations` |
| `RelianceView.jsx` | `explore/reliance` |
| `PersonIntro.jsx` / `TourIntro.jsx` | `explore/intro`(인물 / 투어) |

### 지원 모듈

- 지도: `mapLayers.js`(소스·레이어·핸들러, `EMPTY_GEOJSON`)·`mapGeo.js`(GeoJSON 변환·기하)·`mapRingController.js`(`createRingController`).
- 절/구절: `VerseLayer.jsx`(포털 모달 쉘, `paperTextStyle`·`VerseBookTabs` export)·`VerseLangTabs.jsx`.
- 투어: `TourPlayback.jsx`(해설 카드, `tourSketches` lazy import)·`tourSketches.jsx`(`SCENES` 레지스트리 병합, `TourSketchPanel` export)·`sketches/`.
- 심볼: `personSymbols.jsx`(`PersonSymbol` default + `hasSymbol`)·`bookSymbols.jsx`(`BookSymbol` default).
- 기타: `SpineHeader.jsx`(전역 헤더, `HEADER_H`·`RIBBON_OVERHANG` export)·`JourneyList.jsx`·`PersonMiniCard.jsx`·`Spinner.jsx`·`BookStageMap.jsx`.

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
- **백엔드 내부 헬퍼**: 밑줄 접두사(`_compute_events`·`_load_events`·`_fetch_place_coords`·`_resolve`). 캐시는 `@functools.lru_cache(maxsize=...)`.
- **프론트 파일**: 뷰·컴포넌트는 PascalCase `.jsx`(`StatsView.jsx`), 훅은 camelCase `use*.js`(`useTourPlayback.js`), 순수 유틸은 camelCase `.js`(`urlState.js`·`mapGeo.js`). 심볼·스케치처럼 JSX를 반환하는 비컴포넌트 모듈은 camelCase `.jsx`(`personSymbols.jsx`·`tourSketches.jsx`).
- **데이터**: 디렉터리는 snake_case(`jesus_parables_miracles`·`messianic_prophecies`), 파일은 대체로 `<복수명>.json`(`covenants.json`·`prophecies.json`·`topics.json`·`index.json`) 또는 `<slug>.json`. 투어 파일명은 kebab-case(`gospel-of-jesus.json`).
- **스크립트**: 동사 접두사(`load_`·`inject_`·`generate_`·`build_`·`validate_`·`apply_`·`enrich_`) + snake_case 대상.
- **로깅**: 백엔드는 모듈 logger + `[Component]` prefix(`[Overlays]`·`[Tours]`·`[Nodes]`·`[Startup]`), 프론트 빈값-폴백 catch는 `console.warn('[Component] ...')`. 상세는 `.forge/codebase/CONVENTIONS.md`의 로깅 방출 규약 절.
- **주석·문서**: 한글. 코드 주석이 결정 번호(ADR-0009 해시 딥링크, ADR-0010 뒤로가기, ADR-0011 투어 오버레이, ADR-0014 보수 연대, ADR-0020 라이트 테마, ADR-0024 모션, ADR-0026 책등 헤더, ADR-0028 투어 note, ADR-0029 스케치 모듈)와 task 번호를 상호 참조한다. ADR 본문은 `.forge/adr/`.

## 새 것을 어디에 추가하나

### 새 뷰(스테이지)

1. `frontend/src/<Name>View.jsx` 생성.
2. `frontend/src/useStageNavigation.js` — 대상 id가 필요하면 state 추가, `handleOpen<X>`/`handle<X>Back` 작성(대상 없는 고정 뷰는 `handleOpenStats`/`handleStatsBack`이 최소 템플릿), return 객체에 export.
3. `frontend/src/urlState.js` — `encodeHash`에 분기, `parseHash`에 패턴 추가.
4. `useStageNavigation.js`의 **복원 effect**(`parsed.stage === '...'` 분기), **sync effect**(`encodeHash` 인자·`state` 객체·`navSyncRef`·`isForward` 비교), **popstate effect**(`s.<field>` 복원) 세 곳을 함께 갱신. 대상 id가 없는 뷰면 3·4는 스테이지 분기만 추가하면 된다.
5. `frontend/src/App.jsx` — `render<X>Nav()` 추가, `activeStage === '<x>' && (...)` 조건 렌더 블록 추가, `activeSection` 계산에 스테이지 편입.

### 새 탐험 서브뷰(`exploreView` 탭)

`App.jsx` 상단의 탭 상수(`EXPLORE_TABS`/`INTRO_TAB`/`RELATIONS_TAB`/`RELIANCE_TAB`/`FAMILY_TAB`/`TOUR_INTRO_TAB`)에 항목을 더하고, `renderExploreNav`의 탭 배열 조립부와 `App.jsx` 하단의 `exploreView === '<key>' && ...` 렌더 블록, `urlState.js`의 person 서브패스 정규식·`encodeHash` 분기를 함께 고친다.

### 새 스케치(투어 정차지 삽화)

- 기존 투어면 해당 `frontend/src/sketches/<tour>.jsx`에 `Scene` 컴포넌트를 추가하고 파일 끝 레지스트리에 `'<eventId>': { Scene, desc, caption, mood? }` 항목을 넣는다.
- 새 투어면 `frontend/src/sketches/<tourCamelCase>.jsx`를 만들고 `frontend/src/tourSketches.jsx`의 import + `SCENES` 스프레드에 추가한다.
- 헬퍼는 `sketches/lib.jsx`(`sw`로 선 굵기, `d`로 단계 딜레이), 이름표는 `sketches/SceneLabel.jsx`의 `Label`. viewBox는 `0 0 120 64`(`tourSketches.jsx`가 고정).

### 새 데이터 파일(오버레이)

1. `data/<snake_case>/<name>.json` 저작.
2. `backend/app/overlays.py`에 `@functools.lru_cache(maxsize=1)` 로더 함수 추가(docstring에 스키마 한 줄).
3. 소비할 라우트에서 호출. `verseID`만 들고 있는 데이터면 라우트에서 `overlays.bible_verses()`로 본문을 합성해 응답에 동봉한다.
4. 검증이 필요하면 `backend/scripts/validate_<name>.py`를 만들고 `scripts/check.sh`의 12종 루프 목록에 이름을 추가한다.
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

`data/tours/<kebab-id>.json`에 `{id, title, subtitle, era, description, stops:[{id, note}]}`를 쓴다. `era`는 `backend/app/routes/persons.py`의 `_ERA_ORDER` 값 중 하나여야 목록 정렬이 맞는다(`tours._list_tours`). `stops[].id`는 `data/person_events/*.json`에 존재하는 사건 id여야 하고, 모르는 id는 조용히 제거된다. Neo4j 적재는 필요 없다(ADR-0011). 정차지 삽화가 필요하면 위 "새 스케치" 절차를 따른다.
