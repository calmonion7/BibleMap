---
last_mapped_commit: fbd547d83d9d6926216cfde1eae4892ced839083
mapped: 2026-09-02
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
│   ├── src/                  컴포넌트·훅·유틸(대체로 플랫 — 하위는 sketches/ 와 그 안의 cast/·cast/props/)
│   ├── public/               favicon.svg · fonts/ (+ scene-color/ 채색층 자산, git-ignored)
│   ├── dist/                 빌드 산출물(nginx가 마운트, git-ignored)
│   ├── index.html
│   ├── vite.config.js        __BUILD_ID__ define + manualChunks(maplibre/vendor)
│   ├── eslint.config.js      flat config, __BUILD_ID__ 전역 선언
│   └── .env.production       VITE_API_URL=/api
├── data/                     그래프 로더 입력 + 런타임 오버레이 JSON(api가 /app/data로 마운트)
├── scripts/check.sh          배포 전 검증 게이트(AI 불요, 단독 실행 가능)
├── scripts/check_*.py        게이트가 파일 경로로 부르는 저작물 소스 불변식(check_cast_axes · check_mask_ranges)
├── scripts/render_scene.py   장면 하나를 빌드→렌더→고배율 촬영(저작자용 시각 피드백 루프, playwright)
├── scripts/uat_*.py          브라우저 실측 UAT 4종(check.sh 미배선 — deploy.sh가 빌드 전에 check.sh를 부르므로 :8080이 옛 빌드일 때가 있어서다)
├── scripts/canon/            오프라인 이미지 저작 파이프라인(앱과 다른 런타임·GPU, 앱이 import하지 않음)
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
| `validate_*` | 데이터·소스 검증(22종 `scripts/check.sh` 루프 항목 + Neo4j 필요 1종 + 별도 절로 도는 가드 2종) | `validate_covenants`, `validate_messianic_prophecies`, `validate_parables_miracles`, `validate_topical_verses`, `validate_pm_map_coverage`, `validate_scene_coverage`(투어 정차지↔장면 스케치 커버리지, task#259), `validate_chapter_sections`, `validate_chapter_summaries`, `validate_quotations`, `validate_person_context`, `validate_god_reliance`, `validate_traits`, `validate_era_bands_consistency`(시대 이름·순서·경계 7축, task#255→284), `validate_approx_book_verses`(생성기 `VERSE_MAP`↔`book_events` 정합, task#274), `validate_intro_menu_parity`(인트로 소개 장면↔실제 하위 메뉴 정합, task#277), `validate_curated_persons`(CURATED↔person_events/god_reliance/seal_slugs 정합, task#278), `validate_intro_gutter`(인트로 비트 프레임의 `boxSizing`·여백 규약, task#280), `validate_intro_entry_route`(무타깃 진입 판정 단일 선언, task#281), `validate_event_verses`(근거 절↔rangeLabel 경계 정합, task#282), `validate_sortkey_startdate`(sortKey↔startDate 역전 + yearLabel 정합, task#283), `validate_api_cache_headers`(라우트 응답 `max-age` 상한 300, task#285), `validate_scene_sketch_detail`(장면 저작 규약 경계 B1~B12 + 인물 정본 인라인 전개, task#286~307 — 927줄로 이 디렉터리 최대), `validate_event_chronology`(Neo4j 필요), `validate_canon_pipeline`(저작 파이프라인 `params.py` 재선언 금지 + `scripts/` 미추적 0건, 별도 절·배포 차단, task#316), `validate_forge_docs_tracked`(`.forge/adr`·`.forge/retro` 미추적 0건 — 데이터 검증이 아닌 로컬 위생 가드, 별도 절로 실행, task#279). 상당수가 `--selftest`로 고의 결함 주입 대조군을 갖는다(ADR 260820-003946) |
| `apply_*` / `enrich_*` | 일회성 데이터 조작 | `apply_event_dedupe`(`data/event_dedupe/dedupe.json` 기반 실삭제), `enrich_place_coords` |
| `_*`(밑줄) | 검증기들이 공유하는 사적 헬퍼 | `_svgpath.py`(SVG `path d` → 절대 좌표 점 목록 — 선분 대 상자 교차 판정용. 바운딩 박스로 재면 가로로 긴 능선 하나가 띠 전체를 덮은 것으로 잡혀 과대평가된다) |

## 프론트엔드 (`frontend/src/`)

디렉터리는 `sketches/`(+ 그 안의 `cast/`·`cast/props/`) 하나뿐이고 나머지는 전부 플랫이다.

### 진입 · 상태 · 유틸

| 파일 | 역할 |
|---|---|
| `main.jsx` | 루트 렌더(StrictMode) + 라이트 테마 동기 반영 |
| `App.jsx` | 스테이지 조건 렌더(14종) + `StageNav` 조립 + 상세 시트/패널 + 검색 오버레이 + 여정·재생·개인화 훅 소유(task#257~258로 988줄→535줄 분해) |
| `CastSheet.jsx` | `cast` — 개발 전용 설정화 시트(`#/cast`, ADR `260823-190821`). `import.meta.glob`로 `sketches/cast/*.jsx`와 `sketches/cast/props/*.jsx`를 **별도 glob**으로 열거해(합치면 지물이 "안 쓴 인물 정본"으로 잡혀 B12 게이트가 거짓 빨강) 주역·보조·원경 세 배율로 깐다. lazy 로드 |
| `StageNav.jsx` | 스테이지 하위 내비 공용 껍데기(`onBack`·`lead`·`auxLabel`·`trailing` 슬롯 + `StageNav.Tab`/`StageNav.Title`, `NAV_H` export) — 과거 스테이지별 `render<X>Nav()` 9개를 대체 |
| `ExploreStage.jsx` | `explore` 스테이지 전용(지도·연표·관계·소개·의존·족보 6뷰 조립) — App.jsx에서 분리(task#257), `journey`·`playback`은 prop으로 주입받음 |
| `useStageNavigation.js` | 스테이지·URL·히스토리 상태 머신(모든 `open*`/`*Back` 핸들러 export) |
| `useNodeSelection.js` | 노드 선택/히스토리 원시값 |
| `useExploreJourney.js` | 탐험 여정 데이터(정차지·투어 메타·인물 사건 Set) — **App에서만 호출**(ExploreStage 언마운트 시 상태 유실 방지, 파일 상단 주석 근거) |
| `useTourPlayback.js` | 투어 자동재생 시퀀서 훅(상태만, 카메라는 App/MapView) + `stepDuration(note)` **export**(`9000 + min(note.length*40, 5000)`) — 장면 채색 예산과 검증기 경계가 이 함수에서 파생된다 |
| `useBookmarks.js` | 북마크·최근 이어보기(task#268, `localStorage` 전용, 서버 쓰기 없음) |
| `useReadingProgress.js` | 장 단위 읽음 표시 + 이어읽기 판정 `computeResume`(task#269, `localStorage` 전용) |
| `urlState.js` | `encodeHash`/`parseHash` 해시 코덱 + `isNoTarget(hash)`(무타깃 진입 판정 단일 정본, task#281). `#/cast`도 여기서 왕복한다 |
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
| `CastSheet.jsx` | `cast` — 인물 정본·지물 참고 도상 격자(개발 전용 `#/cast`, task#307) |
| `SearchPanel.jsx` | 전역(스테이지 무관) — `/` 단축키·헤더 검색 버튼으로 여는 통합 검색 오버레이(`/search`, task#267) |

### 지원 모듈

- 지도: `mapLayers.js`(소스·레이어·핸들러, `EMPTY_GEOJSON`)·`mapGeo.js`(GeoJSON 변환·기하)·`mapRingController.js`(`createRingController`).
- 절/구절: `VerseLayer.jsx`(포털 모달 쉘, `paperTextStyle`·`VerseBookTabs` export)·`VerseLangTabs.jsx`.
- 투어: `TourPlayback.jsx`(해설 카드, `tourSketches` lazy import)·`tourSketches.jsx`(`TOUR_MODULES` 투어별 동적 로드 + `SceneSvg` 렌더·계측, `TourSketchPanel` export / default export `TourSketch`는 인트로 몽타주 전용)·`sketches/`.
- 심볼: `personSymbols.jsx`(`PersonSymbol` default + `hasSymbol`)·`bookSymbols.jsx`(`BookSymbol` default).
- 개인화: `BookmarkToggle.jsx`(저장 토글 컴포넌트, `useBookmarks`가 넘긴 `saved`/`onToggle`만 받는 순수 표시).
- 기타: `SpineHeader.jsx`(전역 헤더 + 검색 버튼, `HEADER_H`·`RIBBON_OVERHANG` export)·`JourneyList.jsx`·`PersonMiniCard.jsx`·`Spinner.jsx`·`BookStageMap.jsx`.

### 장면 스케치 (`frontend/src/sketches/`)

투어 하나 = 파일 하나(camelCase). 현재 9개: `creationToFlood`·`patriarchsCovenant`·`exodusToConquest`·`ageOfJudges`·`davidUnitedKingdom`·`elijahAndElisha`·`exileAndReturn`·`gospelOfJesus`·`theEarlyChurch`. 각 파일은 `Scene` 컴포넌트들을 정의하고 파일 끝에서 `{ '<eventId>': { Scene, desc, caption, mood?, letterLast?, color? } }` 레지스트리를 default export한다. 이 파일 목록이 곧 **청크 목록**이다 — `tourSketches.jsx`의 `TOUR_MODULES`(투어 id → `() => import('./sketches/<tour>')`)가 투어 단위로만 내려받는다(task#287). 여기에 더해:

- `lib.jsx` — 순수 헬퍼(`P`·`W`·`sw`·`d`)와 **저작 규약 정본 주석**. 선 굵기 위계·draw 규약뿐 아니라 경계 B1~B12(밀도·단계 상한/하한·시간 예산·절정 순서·종속 관계·구조 밀도·배경 상한·연출 완료·배치 분리·구조 연결·정본 강제), 신체 조립 규칙, "상자·사다리로 읽히는 실패" 목록, 배치 레시피(상단 띠 y≤8 / 그림 y10~55 / 하단 띠 y≥57), 정본 컴포넌트 규약이 전부 이 파일 주석에 산다.
- `SceneLabel.jsx` — 장면 이름표 컴포넌트 `Label`. `lib.jsx`에서 분리된 이유는 `react-refresh/only-export-components` 규칙. `at=`(수동 초) 외에 `after=`(드로인 완료 뒤 스태거, `--reveal-end` 파생) 옵트인이 있다.
- `introMontage.jsx` — 인트로 오프닝 몽타주 5씬 **정의**와 그 소형 레지스트리(default export). 각 투어 모듈이 자기 레지스트리를 위해 여기서 되가져간다 — 참조 방향이 반대면(소형 모듈이 투어 모듈을 재수출) 롤업이 `INEFFECTIVE_DYNAMIC_IMPORT`로 분할을 무효화한다.
- `cast/*.jsx` — 인물 정본(현재 `david`·`goliath`). 여러 장면이 공유하는 머리(윤곽·머리카락·수염·머리쓰개)를 강제 컴포넌트로 두고 이목구비는 슬롯으로 비운다. 호출 prop은 `cx`·`cy`·`scale`·`delay` **숫자 리터럴만**이고 `transform`·조건 분기가 금지된다(`validate_scene_sketch_detail.py`가 소스를 정적으로 읽어 인라인 전개하기 때문). 파일이 `export const AXES`(5축)·`export const aliases`를 함께 내보내며, 그래서 `frontend/eslint.config.js`가 이 디렉터리에만 `react-refresh/only-export-components`를 끈다.
- `cast/props/*.jsx` — 지물 참고 도상(현재 `altar`). **비강제**이며 자체 완결(props 없음)이라 장면이 import하지 않는다. `cast/` 직속과 반드시 별 glob으로 갈라 읽는다.

## 데이터 (`data/`)

`api` 컨테이너가 `/app/data`로 마운트하고 `DATA_DIR` 기본값이 이를 가리킨다. 서브디렉터리 하나가 대체로 오버레이 함수 하나 또는 로더 하나에 대응한다.

- 절 본문·색인: `bible/verses.json` · `verse_persons/index.json` · `verse_events/events.json` · `word_verse_index/index.json` · `word_distribution.json` · `word_sentiment.json`(최상위 파일 2개)
- 사건·연대: `event_verses/events.json` · `book_events/books.json` · `book_years_approx/books.json` · `date_corrections/{events,persons}.json` · `event_dedupe/dedupe.json` · `authored_events/events.json`
- 인물: `authored_persons/{people,genealogy,mothers}.json` · `person_events/<slug>.json`(35개) · `person_context/people.json` · `person_relations/relations.json` · `person_slugs/seal_slugs.json` · `character_traits/people.json` · `god_reliance/<slug>.json`(32개) · `keypeople/identity.json` · `keypeople_verses/people.json` · `names_ko/{books,events,groups,people,places}.json`
- 장소·책: `place_coords/places.json` · `place_context/places.json` · `book_context/books.json` · `chapter_summaries/books.json` · `chapter_sections/books.json`
- 주제 콘텐츠: `covenants/covenants.json` · `messianic_prophecies/prophecies.json` · `topical_verses/topics.json` · `jesus_parables_miracles/index.json`
- 인용·투어: `quotations/quotations.json` · `tours/<id>.json`(9개, 파일명 = 투어 id = URL slug)
- 저작 규칙: `character_traits/AUTHORING.md` · `person_context/AUTHORING.md` · `person_relations/AUTHORING.md` — 통제 어휘와 저작 경계 규칙이 데이터 옆에 산다.

## 스크립트 (`scripts/`)

`backend/scripts/`(앱 데이터 계층)와 **별개 소속**이다. 이 아래에는 게이트가 파일 경로로 부르는 소스 불변식, 브라우저 실측 UAT, 저작자용 렌더 도구, 그리고 오프라인 이미지 저작 파이프라인이 산다. `backend/scripts/validate_canon_pipeline.py` 축2가 **이 트리의 미추적 파일 하나에도 배포를 막는다** — `check.sh`가 여기 있는 파일을 부르므로, 미추적이면 새 클론·CI에서 게이트 자신이 깨진다.

| 파일/디렉터리 | 역할 |
|---|---|
| `check.sh` | 배포 전 검증 게이트(단독 실행 가능, `CHECK_STRICT=1`이면 스킵이 실패로 승격) |
| `check_cast_axes.py` | 인물 정본 `cast/*.jsx`의 `AXES` 5축 조합 중복 0(구별성 1단, task#314) |
| `check_mask_ranges.py` | `GoliathScene`의 인물별 `delay` 범위 연속·비중첩(+`--selftest`, task#315). `derive_ranges()`를 저작 파이프라인의 `make_masks.py`가 재사용한다 |
| `render_scene.py` | 장면 하나를 빌드→렌더→고배율 촬영(playwright). `--at`(시각 스크럽)·`--min-stroke-width`(굵기 계단)·`--delay-range`·`--cast`(설정화 시트 촬영). 굵기 임계는 `lib.jsx`의 `W`에서 파생 |
| `uat_*.py` | 브라우저 실측 UAT 4종 — `uat_intro_gutter`·`uat_intro_entry`·`uat_scene_detail_pilot`(task#286)·`uat_tour_chunk_split`(task#287). 종료코드 0/1/2로 통과·제품 결함·측정 환경 이상을 자가 구별한다. `check.sh` 미배선 |
| `canon/` | 오프라인 이미지 저작 파이프라인(아래) |

### 저작 파이프라인 (`scripts/canon/`)

앱과 다른 런타임에서 돈다 — 소스만 레포 안에 있고, venv·모델 캐시는 레포 밖(`~/.local/biblemap-imggen/`)이며 산출 이미지는 gitignored인 `.forge/reports/canon-pilot/`에 쌓인다(`params.OUT_ROOT`). 추적 파일 177개.

```
scripts/canon/
├── params.py            [[생성 파라미터]] 정본 — 모델 ID·STEPS·GUIDANCE·CN/IP 강도·캔버스·시드
├── derive_prompts.py    프롬프트 파생(cast/*.jsx의 AXES + person_events의 sortKey) → notes/prompts.json
├── gen_*.py             생성 21개 — 현행 정본은 gen_scripture_scene.py(8단계 인페인팅 + 판 합성)
├── judge_*.py           판정 8개 — 현행 정본은 judge_scene.py(축 C1~C5, GPU 0)
├── try_prompt.py        프롬프트 연습대(--check는 토큰만, GPU 0)
├── freeze_*.py · prep_cond.py · make_masks.py · make_montage.py · probe_cn.py · arm_sweep.py · sweep_cause.py · long_prompt.py · cond_shoot_heads.py
├── requirements.txt     런타임 박제 + **재현 미결 3축**을 미결로 적은 머리 주석
├── notes/               판단 문서 20(.md, 대문자) + 판정 결과 37(.json)
├── reference/           정답지 10장 — 축 A(화풍) 임계의 양성 기준(직속 *.png가 전부 읽힌다 = 여기 넣는 것이 곧 임계 변경). 후보·승인 이력은 task 번호 서브디렉터리로
├── setup/               설정화 시트(그래서 reference/ 밖) — SETUP.md가 그 경계를 적어 둔다
├── samples/             [[전신 표본]] — 인물 레퍼런스(SAMPLES.md)
├── frozen/              동결 얼굴 2장(FROZEN.md) — 얼굴 크롭이라 IP로 물리면 프레이밍이 전이된다
├── scene_ref/           장면 구도 앵커(SCENE_REF.md)
└── conti/               폐기된 콘티 경로 — 자립 HTML·렌더러(render_conti.py)·마스크 파생(make_conti_masks.py)
```

- **`notes/`의 두 종류**가 이 파이프라인의 문서 규약이다. 대문자 `.md`는 사람이 읽는 판단 문서(`SCENE-1SAM17.md` 장면 명세 정본 · `PROMPTING.md` 실측 규칙 · `PROCESS.md` 순서·판정 구조 · `AXES.md`·`SCALE.md`·`JUDGE-*.md`·`ZIMAGE.md` 등), 소문자 `.json`은 기계가 쓴 판정 결과(`s0-baseline.json`·`s1-baseline.json`이 임계 정본, `final-verdict-<라벨>.json`이 판마다 하나, `prompts.json`이 파생 프롬프트).
- **자산 디렉터리가 여섯으로 갈린 이유는 임계다.** `judge_style.reference_paths()`가 `reference/*.png`를 전부 읽어 축 A 구간을 파생하므로, 다른 성격의 이미지를 그 디렉터리에 넣으면 임계가 부작용으로 바뀐다 — 각 디렉터리의 `*.md`가 자기가 왜 `reference/`가 아닌지를 적어 둔다.
- 각 서브디렉터리는 `README.md`/대문자 `.md`로 자기 자산의 출처와 승인 이력을 남긴다(`reference/approved-322/`·`candidate-322b~e/`처럼 **태스크 번호가 붙은 후보 묶음**이 그 관행이다).

## 명명 규약

- **Neo4j 식별자**: 모든 라벨의 안정 키는 `theographic_id`. 큐레이션 인물만 별도 `slug`(파일명·URL용). 책은 slug가 없다.
- **URL**: 인물·투어는 slug(`#/person/<slug>`·`#/tour/<slug>`), 책·가계도·단어는 id(`#/book/<theographic_id>` 등).
- **API 경로**: kebab-case(`/books-overview`·`/keypeople-cards`·`/messianic-prophecies`·`/topical-verses`·`/parables-miracles`).
- **백엔드 내부 헬퍼**: 밑줄 접두사(`_compute_events`·`_fetch_place_coords`·`_resolve`). `curated.py`의 공개 헬퍼(`person_events`·`curated_index`·`id_to_slug` 등)는 예외 — 여러 라우트가 import하는 공유 정본이라 밑줄 없이 공개 이름을 쓴다. 캐시는 `@functools.lru_cache(maxsize=...)`.
- **프론트 파일**: 뷰·컴포넌트는 PascalCase `.jsx`(`StatsView.jsx`), 훅은 camelCase `use*.js`(`useTourPlayback.js`), 순수 유틸은 camelCase `.js`(`urlState.js`·`mapGeo.js`). 심볼·스케치처럼 JSX를 반환하는 비컴포넌트 모듈은 camelCase `.jsx`(`personSymbols.jsx`·`tourSketches.jsx`·`sketches/introMontage.jsx`). **스케치 모듈 파일명은 그 자체가 배선 키**다 — 투어 모듈은 투어 id의 camelCase(`gospel-of-jesus` → `gospelOfJesus.jsx`), 인물 정본·지물은 소문자 대상명(`sketches/cast/david.jsx`·`sketches/cast/props/altar.jsx`, 컴포넌트를 default export해도 파일명은 소문자다).
- **데이터**: 디렉터리는 snake_case(`jesus_parables_miracles`·`messianic_prophecies`), 파일은 대체로 `<복수명>.json`(`covenants.json`·`prophecies.json`·`topics.json`·`index.json`) 또는 `<slug>.json`. 투어 파일명은 kebab-case(`gospel-of-jesus.json`).
- **스크립트**: 동사 접두사 + snake_case 대상. 소속마다 접두사 집합이 다르다.
  - `backend/scripts/` — `load_`·`inject_`·`generate_`·`build_`·`validate_`·`apply_`·`enrich_`(호스트 실행, `scripts/check.sh`가 `--selftest` 지원 검증기를 대조군으로 부른다). 밑줄 시작(`_svgpath.py`)은 검증기들이 공유하는 사적 헬퍼.
  - 최상위 `scripts/` — `uat_*.py`는 브라우저를 실제로 띄워 픽셀·렌더·네트워크를 재는 **실측** UAT로 `check.sh`에 배선하지 않는다(`deploy.sh`가 빌드 전에 `check.sh`를 부르므로 그 시점 :8080이 옛 빌드일 수 있어서다, task#280~281). `check_*.py`는 반대로 브라우저 없이 소스만 읽는 불변식이라 게이트가 **파일 경로로** 부른다(모듈 경로가 아니다).
  - `scripts/canon/` — `gen_`(생성)·`judge_`(판정)·`derive_`(파생)·`freeze_`(동결)·`prep_`/`probe_`/`sweep_`/`arm_`(조건 준비·탐침·스윕)·`make_`(마스크·몽타주 등 산출물 조립). `gen_`↔`judge_` 대응이 **생성과 판정을 가르는 규율**의 이름 표현이고, 판정자는 생성자를 import하지 않는다.
- **프론트 테스트**: 대상 모듈과 같은 디렉터리에 `<name>.test.js`(vitest, task#261). 예: `mapGeo.js`↔`mapGeo.test.js`.
- **로깅**: 백엔드는 모듈 logger + `[Component]` prefix(`[Overlays]`·`[Tours]`·`[Nodes]`·`[Startup]`), 프론트 빈값-폴백 catch는 `console.warn('[Component] ...')`. 상세는 `.forge/codebase/CONVENTIONS.md`의 로깅 방출 규약 절.
- **주석·문서**: 한글. 코드 주석이 결정 번호(ADR-0009 해시 딥링크, ADR-0010 뒤로가기, ADR-0011 투어 오버레이, ADR-0014 보수 연대, ADR-0020 라이트 테마, ADR-0024 모션, ADR-0026 책등 헤더, ADR-0028 투어 note, ADR-0029 스케치 모듈)와 task 번호를 상호 참조한다. 최근 결정은 번호 대신 타임스탬프 id로 참조된다(`260821-174855`/`174856` 장면 밀도·체류 시간, `260823-112503`/`112504` 채색층·식자 순서, `260823-190821` 인물 정본, `260823-221839` 정본 단일화, `260825-013557` 임계 선취 금지, `260825-065028` 파이프라인 런타임 분리). ADR 본문은 `.forge/adr/`.

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

- 기존 투어면 해당 `frontend/src/sketches/<tour>.jsx`에 `Scene` 컴포넌트를 추가하고 파일 끝 레지스트리에 `'<eventId>': { Scene, desc, caption, mood?, letterLast?, color? }` 항목을 넣는다. **그 정차지가 속한 투어의 모듈이어야 한다** — 키가 다른 모듈에 있으면 동적 로드 구조에서는 아무것도 렌더되지 않고, `validate_scene_coverage.py`가 이를 "F 오배치"로 잡는다(task#287).
- 새 투어면 `frontend/src/sketches/<tourCamelCase>.jsx`를 만들고 `frontend/src/tourSketches.jsx`의 `TOUR_MODULES`에 `'<투어 id>': () => import('./sketches/<tourCamelCase>')`를 추가한다(정적 import·`SCENES` 스프레드는 없어졌다).
- 헬퍼는 `sketches/lib.jsx`(`sw`로 선 굵기, `d`로 단계 딜레이), 이름표는 `sketches/SceneLabel.jsx`의 `Label`. viewBox는 `0 0 120 64`(`tourSketches.jsx`가 고정).
- **저작 경계 B1~B12를 `lib.jsx` 주석에서 읽고 시작한다**(밀도 ≥35선·단계당 3선 이하·드로인 총 길이 ≤10,000ms·절정은 드로인 뒤·구조 선 ≥12개·반투명 40% 이하·이름표 상자에 선 침입 금지·구조 선 연결·인물 정본 사용). `backend/scripts/validate_scene_sketch_detail.py`가 배포 게이트에서 이를 강제하고, 경계값은 `index.css`(`--dur-draw-scene`)·`tourSketches.jsx`(패널 대기 450ms)·`useTourPlayback.js`(`stepDuration`)·`data/tours/*.json`(note 길이)에서 파생하므로 **타이밍을 바꾸면 경계가 함께 움직인다**.
- 이름표가 붙은 인물에게 정본(`sketches/cast/<name>.jsx`)이 있으면 그 정본 컴포넌트를 써야 한다(B12).
- 좌표를 눈 없이 쓰지 말 것 — `python3 scripts/render_scene.py <SceneName> --at <ms>`로 실제 렌더를 보고 "사람인가 물건인가"를 판정한다(`lib.jsx`가 이 명령을 판단 기준으로 못박아 뒀다).

### 새 인물 정본(`sketches/cast/`)

1. `frontend/src/sketches/cast/<name>.jsx`에 머리(윤곽·머리카락·수염·머리쓰개)만 그린다 — 이목구비는 슬롯으로 비운다(표정은 장면이 그린다).
2. 호출 규약을 지킨다: prop은 `cx`·`cy`·`scale`·`delay` 숫자 리터럴만, `transform` 금지, 내부 조건 분기 금지, 좌표는 `cx + N * scale` 패턴, `stroke-width`는 `scale`을 곱하지 않는다. 규약 정본과 그 이유는 `sketches/lib.jsx`의 "정본 컴포넌트 규약" 절.
3. `export const AXES`(5축)와 `export const aliases`(이름표 별칭)를 같은 파일에서 내보낸다 — `scripts/check_cast_axes.py`가 5축 조합 중복을, `validate_scene_sketch_detail.py`가 별칭·좌표를 그 소스 하나에서 읽는다(파일 분리는 이 계약을 깬다).
4. 파일 상단 주석에 소비 단계 수·간격과 `scale=1` 머리 지름을 규격으로 적는다(뒤 단계 지연과 어깨 폭 계산의 입력이다).
5. `#/cast`(`CastSheet.jsx`)에서 주역·보조·원경 세 배율의 실루엣을 확인한다 — 명단을 박지 않고 `import.meta.glob`으로 열거하므로 파일만 추가하면 실린다. 촬영은 `python3 scripts/render_scene.py --cast`.
- 지물 참고 도상은 `sketches/cast/props/<name>.jsx`(비강제·자체 완결·장면이 import하지 않음). `cast/` 직속에 두면 "안 쓴 인물 정본"으로 잡혀 B12가 거짓 빨강이 된다.

### 새 데이터 파일(오버레이)

1. `data/<snake_case>/<name>.json` 저작.
2. `backend/app/overlays.py`에 `@functools.lru_cache(maxsize=1)` 로더 함수 추가(docstring에 스키마 한 줄).
3. 소비할 라우트에서 호출. `verseID`만 들고 있는 데이터면 라우트에서 `overlays.bible_verses()`로 본문을 합성해 응답에 동봉한다.
4. 검증이 필요하면 `backend/scripts/validate_<name>.py`를 만들고 `scripts/check.sh`의 22종 루프 목록에 이름을 추가한다(고의 결함 대조군을 두려면 `--selftest` 분기를 만들고 별도 `run` 줄로 함께 배선한다, ADR 260820-003946).
5. 반영에는 **API 재시작**이 필요하다(`docker compose restart api`) — 로더가 `lru_cache`라 파일만 바꿔서는 안 바뀐다. `data/`는 볼륨 마운트라 이미지 재빌드는 불필요.

### 새 스크립트

앱 데이터 계층을 만지는 것이면 `backend/scripts/<verb>_<target>.py`, 브라우저·저작물·이미지 파이프라인 쪽이면 최상위 `scripts/`에 둔다(위 "스크립트" 절의 소속별 접두사 표를 따른다). Neo4j를 만지면 `NEO4J_URI`/`NEO4J_USER`/`NEO4J_PASSWORD`를 읽고 비밀번호 부재 시 `RuntimeError`로 죽는 기존 패턴을 그대로 쓰고, `load_*`/`inject_*`는 재실행 안전(멱등)해야 한다. `data/` 경로는 `Path(__file__).parent.parent.parent / "data"` 관행. 배포 게이트에 넣을 검증기라면 `python3 -m backend.scripts.<name>`으로 실행되고 실패 시 비0 종료해야 한다.

### 새 API 라우트

- 기존 도메인에 속하면 `backend/app/routes/<domain>.py`에 `@router.get(...)`만 추가한다.
- 새 파일이면 `router = APIRouter()`를 선언하고 `backend/app/main.py`의 import 라인과 `app.include_router(...)` 두 곳을 함께 고친다.
- 반환은 `JSONResponse(content=..., headers={"Cache-Control": "max-age=300"})` 관행이고 **300이 상한**이다(`validate_api_cache_headers.py`, task#285) — 불변처럼 보이는 데이터라도 더 긴 수명을 주지 않는다. 올려야 하면 ETag/조건부 GET을 먼저 붙이라는 조건이 그 검증기 docstring에 적혀 있다. 사용자 입력 없는 전역 응답은 `@functools.lru_cache(maxsize=1)` 계산 함수로 감싸고, 입력이 있으면 유한 `maxsize`를 준다.
- 없는 리소스는 도메인에 따라 갈린다 — 큐레이션 밖 인물·투어는 404가 아니라 빈 결과(soft-empty, `journey.py`·`tours.py`), 잘못된 책 id는 `HTTPException(404)`(`words.py`·`books.py`).
- 프론트 소비는 반드시 `frontend/src/api.js`의 `apiGet`을 통한다(캐시 버스팅·에러 시맨틱 일관).

### 새 투어

`data/tours/<kebab-id>.json`에 `{id, title, subtitle, era, description, stops:[{id, note}]}`를 쓴다. `era`는 `backend/app/curated.py`의 `ERA_ORDER` 값 중 하나여야 목록 정렬이 맞는다(`tours._list_tours`) — `validate_era_bands_consistency`가 이 축도 검사한다(task#284). `stops[].id`는 `data/person_events/*.json`에 존재하는 사건 id여야 하고, 모르는 id는 조용히 제거된다. Neo4j 적재는 필요 없다(ADR-0011). 정차지 삽화가 필요하면 위 "새 스케치" 절차를 따르고, **그 투어 id를 `tourSketches.jsx`의 `TOUR_MODULES`에도 등록한다** — 빠지면 그 투어 전체가 무음이 된다(`validate_scene_coverage.py`의 "E 투어 미연결"). 그 검증기(task#259 → #287)가 배포 게이트에서 모든 `stops[].id`에 **그 투어 모듈 안의** 스케치가 있는지 강제하므로(정당한 미저작 예외 목록 `EXPECTED_UNCOVERED`은 비어 있는 것이 정본), 스케치 없는 정차지를 추가하면 배포가 막힌다.

### 새 저작 파이프라인 실험(`scripts/canon/`)

- 손잡이 값(모델 ID·스텝·guidance·CN/IP 강도·캔버스·시드)은 `scripts/canon/params.py`에서만 바꾼다 — 다른 파일에서 같은 이름을 모듈 레벨로 재대입하면 `validate_canon_pipeline.py` 축1이 배포를 막는다.
- 프롬프트 문구는 `try_prompt.py --check`(GPU 0, 1초)로 토큰부터 본다 — 77토큰을 넘으면 에러 없이 잘려 뒤의 화풍 블록이 사라진다. 문장의 출처는 `notes/SCENE-1SAM17.md`(요소마다 출처 절)이고, 새 서술을 생성기 안에서 발명하지 않는다.
- 임계는 `notes/s0-baseline.json`·`s1-baseline.json`에서 읽고 결과를 보고 고치지 않는다(ADR `260825-013557`). 새 이미지를 `reference/`에 넣는 것은 곧 축 A 임계 변경이므로 성격이 다른 자산은 `setup/`·`samples/`·`scene_ref/`에 둔다.
- 새 파일은 반드시 커밋한다 — `scripts/` 아래 미추적 파일 하나로 배포가 막힌다(`validate_canon_pipeline.py` 축2). 반대로 **산출 이미지는 레포에 두지 않는다**(`.forge/reports/canon-pilot/`는 gitignored, 재현 명령이 곧 산출물).
