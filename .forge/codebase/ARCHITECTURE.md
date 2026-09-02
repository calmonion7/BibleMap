---
last_mapped_commit: fbd547d83d9d6926216cfde1eae4892ced839083
mapped: 2026-09-02
---

# ARCHITECTURE

## 전체 패턴

세 계층 단방향 읽기 파이프라인이다. 쓰기 경로는 앱에 없고, 그래프를 채우는 일은 전부 빌드타임 스크립트가 한다.

```
저작 JSON(data/) ─┬─► 로더/주입 스크립트(backend/scripts/load_*·inject_*) ─► Neo4j 그래프
                  │                                                              │
                  └─► 런타임 오버레이(backend/app/overlays.py, lru_cache) ───┐    │
                                                                            ▼    ▼
                                                        FastAPI 읽기 API(backend/app/)
                                                                            │
                                                                            ▼
                                       React SPA(frontend/src/) — 스테이지 머신 + 해시 딥링크
```

- API 라우트는 전부 `@router.get` 이고 CORS도 GET만 허용한다(`backend/app/main.py`의 `allow_methods=["GET"]`). 앱은 그래프를 읽기만 한다.
- 그래프 노드로 승격하지 않는 콘텐츠(사건 근거 구절·언약·메시아 예언·비유/기적·주제 성구·절 본문 등)는 `data/` 아래 JSON **오버레이**로 두고 `backend/app/overlays.py`가 `functools.lru_cache`로 1회 로드해 그래프 쿼리 결과와 합성한다.
- 프론트는 라우팅 라이브러리 없이 **스테이지(Stage) 상태 머신 + 해시 딥링크**로 화면을 전환한다(`frontend/src/useStageNavigation.js`·`frontend/src/urlState.js`).
- 이 세 계층 **옆에** 앱과 격리된 네 번째가 있다 — `scripts/canon/`의 **오프라인 이미지 저작 파이프라인**(`.py` 42개). 앱과 다른 런타임에서 돌고(레포 밖 venv·GPU) **앱은 이 코드를 import하지 않는다**(`scripts/canon/params.py` 머리 주석, ADR `260825-065028`). 의존 방향은 한쪽뿐이다: 파이프라인이 `data/bible/verses.json`·`data/person_events/*.json`·`frontend/src/sketches/cast/*.jsx`를 읽어 프롬프트를 파생하고, 산출 이미지는 gitignored인 `.forge/reports/canon-pilot/`에 쌓여 앱으로 들어오지 않는다. 상세는 아래 "저작 파이프라인" 절.

## 계층 상세

### 1. Neo4j 그래프

- 드라이버는 `backend/app/db.py`의 `get_driver()` 싱글턴(`NEO4J_URI`/`NEO4J_USER`/`NEO4J_PASSWORD` 환경변수). 비밀번호 미설정이면 `RuntimeError`로 즉시 실패한다.
- 노드 라벨: `Person`·`Place`·`Event`·`PeopleGroup`·`Book`. 안정 식별자는 모든 라벨에서 `theographic_id` 프로퍼티.
- 앱 기동 시 `backend/app/main.py`의 `lifespan`이 다섯 라벨에 `CREATE INDEX <label>_tid IF NOT EXISTS ... ON (n.theographic_id)`를 실행한다. 실패해도 예외를 삼키고 인덱스 없이 계속 진행한다(`[Startup]` 로그).
- 그래프에는 두 소스가 합쳐진다.
  - **원본 적재**: `backend/scripts/load_theographic.py`가 GitHub `robertrouse/theographic-bible-metadata`의 people/places/events/peopleGroups JSON을 내려받아 노드·관계로 적재. `status=publish`만 적재하되 가족 폐포(closure)로 `wip` 인물도 가족 간선 완전성을 위해 포함(ADR-0021/0022). 시드는 `curated_person_ids()`가 `data/person_events/*.json`에서 뽑는다.
  - **저작 레이어 적재**: `load_authored_events.py`·`load_authored_persons.py`·`load_authored_genealogy.py`·`load_authored_mothers.py`·`load_books.py`·`load_person_events.py`·`load_verse_events.py`가 `data/authored_*`·`data/person_events`·`data/verse_events`를 멱등(MERGE) 적재.
- 적재 뒤 **주입(inject)** 스크립트가 기존 노드에 프로퍼티를 SET한다: `inject_ko_names.py`·`inject_date_corrections.py`·`inject_book_context.py`·`inject_person_context.py`·`inject_person_traits.py`·`inject_place_context.py`. `load_theographic.py`를 다시 돌리면 원본 값이 복원되므로 **inject를 반드시 재실행**해야 한다(`README.md`에 명시).
- `backend/Dockerfile`은 `COPY app/ ./app/`만 한다 — **`backend/scripts/`는 API 이미지에 들어가지 않는다**. 로더·주입·검증 스크립트는 항상 호스트에서 `python3`로 돌린다.

### 2. FastAPI 읽기 API

- 진입점 `backend/app/main.py`: `_configure_logging()`를 **라우터 import 전에** 모듈 최상단에서 1회 호출(서드파티 로거 WARNING 승격, `uvicorn`/`uvicorn.access`는 `propagate=False`), `lifespan`으로 인덱스 준비, CORS(GET), `include_router` 14개.
- 라우터 모듈은 `backend/app/routes/` 아래 14개(`nodes`·`events`·`search`·`books`·`persons`·`journey`·`places`·`tours`·`family`·`words`·`verses`·`reliance`·`stats`·`timeline`). prefix 없이 절대 경로를 선언한다.
- `backend/app/verse_search.py` — 절 본문 substring 검색 공용 헬퍼(`search_verses(term, book_id, match_en)`, `@lru_cache(maxsize=256)`). `overlays.bible_verses()`(31,103절)를 전수 스캔하고, `search.py`(통합 검색 `/search`)와 `words.py`(`/words/{book}/verses`)가 함께 쓴다(task#267 — 두 라우트가 각자 짜던 스캔 로직을 통합).
- 캐싱 관행 두 층:
  - 서버 메모리 — 사용자 입력이 없는 전역/집계 함수는 `@functools.lru_cache(maxsize=1)`(예: `events._compute_events`·`stats._compute_stats`·`tours._list_tours`·`tours._build_event_index`·`curated.curated_index`). 입력이 있는 것은 유한 캐시(`books._chapter_payload` 2048, `persons._build_connections` 256, `places._place_to_persons` 256, `curated.person_events` 64).
  - 브라우저 — `JSONResponse(..., headers={"Cache-Control": ...})`. **상한이 `max-age=300`이다**(`/books-overview`만 `no-store`). task#285에서 `books.py`·`reliance.py`·`verses.py`의 6개 응답이 쓰던 `public, max-age=3600`이 전부 300으로 내려갔다 — 표준 데이터수정 경로(`data/` 편집 + `docker compose restart api`)로 고친 내용이 재방문 브라우저에 최대 1시간 반영되지 않았고, 프론트 캐시버스터(`api.js`의 `?v=BUILD_ID`)는 빌드타임 리터럴이라 백엔드만 재시작하는 그 경로를 원리적으로 못 덮는다. `backend/scripts/validate_api_cache_headers.py`가 "라우트 응답의 max-age는 300을 넘지 않는다"를 **경계**로 게이트한다(위반 지점 열거가 아니라 상한 — 올리려면 ETag/조건부 GET을 먼저 붙이라는 조건이 그 파일 docstring에 적혀 있다).
- 라우트 간 재사용은 헬퍼 직접 import로 한다. task#278부터 큐레이션 인물 레지스트리는 `backend/app/curated.py`(overlays.py와 같은 층 — 라우트를 import하지 않아 순환 import를 차단)로 승급됐다: `CURATED`(slug→`{nameKo, era}`, 35개)·`ERA_ORDER`·`person_events(slug)`(sortKey 정렬, `lru_cache(64)`)·`curated_index()`(id·slug·nameKo·era·eventCount 목록, `lru_cache(1)`, 시대순→최초등장→slug 정렬)·`id_to_slug()`/`slug_to_id()`(`curated_index()` 역매핑)·`seal_id_to_slug()`(인장 조회용 — 큐레이션 35 + `person_slugs/seal_slugs.json`의 비큐레이션 인장 보유 인물, 합쳐 50, ADR-0025). `persons.py`·`journey.py`·`tours.py`·`stats.py`·`places.py`·`reliance.py`·`family.py`·`timeline.py` 8개 라우트가 이를 import한다. 그전엔 `persons.py`가 `_ERA`/`_NAME_KO`/`_ERA_ORDER`를 소유하고 나머지가 이를 참조했는데, `family.py`처럼 라우트 간 순환을 피하려 호출 시점 지연 import(`from .persons import _build_list`)로 우회하던 지점이 이관으로 사라졌다. `stats.py`는 이제 `curated.id_to_slug`·`person_events`·`slug_to_id`와 `journey._fetch_place_coords`를 재사용해 새 쿼리 없이 집계를 만든다(예전엔 `journey._build_id_to_slug`·`_load_events`·`persons._build_list`를 썼다 — 그 헬퍼들은 curated.py로 흡수되며 `journey.py`·`persons.py`에서 제거됐다). 새 큐레이션 인물을 추가할 때는 `curated.py`의 `CURATED` dict에 slug를 더하고 `data/person_events/<slug>.json`을 저작한다 — `backend/scripts/validate_curated_persons.py`가 이 두 축(및 `god_reliance`·`seal_slugs`와의 교차)이 갈리면 배포를 막는다.

### 3. 런타임 오버레이 — 그래프에 없는 콘텐츠

`backend/app/overlays.py`가 이 계층의 전부다.

- `_resolve(subpath)`/`_resolve_dir(subpath)`가 두 베이스를 순서대로 탐색한다: `os.environ.get("DATA_DIR", "/app/data")` → 리포지토리 `data/`(`_REPO_DATA_DIR`). 없으면 `[Overlays]` 경고 후 `None`(빈 데이터 폴백). 컨테이너에서는 앞쪽이, 호스트 직접 실행에서는 뒤쪽이 맞는다.
- `_load(subpath)`는 JSON을 읽어 dict 반환, 파싱 실패 시 `{}` 폴백.
- 모든 오버레이는 **인자 없는 함수 + `@functools.lru_cache(maxsize=1)`** — 프로세스당 1회 로드. 따라서 `data/`를 고친 뒤에는 `docker compose restart api`가 필요하다.
- 오버레이 함수 ↔ 파일 매핑:

  | 함수 | 파일 |
  |---|---|
  | `book_events_raw()` | `data/book_events/books.json` |
  | `event_verses()` | `data/event_verses/events.json` |
  | `bible_verses()` | `data/bible/verses.json` |
  | `word_distribution()` | `data/word_distribution.json` |
  | `books_ko()` | `data/names_ko/books.json` |
  | `chapter_summaries()` | `data/chapter_summaries/books.json` |
  | `chapter_sections()` | `data/chapter_sections/books.json` |
  | `quotations()` | `data/quotations/quotations.json`(`.get("quotations", [])`) |
  | `messianic_prophecies()` | `data/messianic_prophecies/prophecies.json` |
  | `covenants()` | `data/covenants/covenants.json` |
  | `parables_miracles()` | `data/jesus_parables_miracles/index.json` |
  | `place_coords()` | `data/place_coords/places.json`(리스트면 `id` 키 dict로 변환) |
  | `place_context()` | `data/place_context/places.json`(id → background·keyVerse류, `inject_place_context.py`가 읽는 것과 같은 파일, task#270) |
  | `topical_verses()` | `data/topical_verses/topics.json` |
  | `verse_persons()` | `data/verse_persons/index.json` |

- **합성 규칙**: 오버레이 JSON은 `verseID` 참조만 들고 있고, 절 본문(`textKo`/`textEn`)은 라우트에서 `overlays.bible_verses()`로 해석해 응답에 동봉한다(ADR-0003/0015). `events.py`의 `/covenants`·`/messianic-prophecies`·`/topical-verses`·`/parables-miracles`·`/event/{id}/verses`가 모두 같은 모양이다. `/parables-miracles`는 추가로 `placeId`를 `place_coords()`로 lat/lng 해석하고, 없으면 항목 자체 lat/lng를 쓴다.
- `overlays.curated_person_id(events)`는 큐레이션 신원 규약의 단일 지점 — `data/person_events/<slug>.json`의 `events[0].participants[0]`이 그 인물의 `theographic_id`다. `persons.py`·`places.py`·`reliance.py`가 소비하고, `load_theographic.py`는 앱을 import하지 않는 관행 때문에 같은 규약을 자체 구현한다.
- `overlays`를 거치지 않고 `_resolve`/`_resolve_dir`만 직접 쓰는 라우트도 있다(`journey.py`·`tours.py`·`persons.py`·`reliance.py`·`family.py`) — 파일이 slug별로 쪼개져 있어 전역 dict 캐시가 맞지 않는 경우다.
- `stats.py`는 오버레이가 아니라 **그래프 집계** 라우트다: `_fetch_totals`(라벨별 총계)·`_fetch_top_persons`(`HAS_PARTICIPANT` 기준, `name='God'` 제외)·`_compute_longest_journeys`(큐레이션 인물 정차지 수)·`_fetch_era_distribution`·`_fetch_books`.

### 4. React SPA

- 엔트리 `frontend/src/main.jsx` → `frontend/src/App.jsx`(`StrictMode`). 라이트 테마는 렌더 전에 동기 반영한다(ADR-0020, `localStorage['biblemap-theme'] === 'light'`이면 `document.documentElement.dataset.theme = 'light'`).
- 상태는 두 훅으로 분리된다.
  - `frontend/src/useNodeSelection.js` — 노드 선택 원시값(`selectedNode`·`selectedNodeMeta`·`history`·`selectNode`·`selectNodeFresh`·`goBack`·`closePanel`·`handleNodeLoaded`).
  - `frontend/src/useStageNavigation.js` — 스테이지·URL·브라우저 히스토리 상태 머신. 위 원시값을 **주입받는다**. 이 파일은 의도적으로 `lucide-react`의 `Map`을 import하지 않고 `history` 배열을 구조분해하지 않는다(전역 `Map`/`history` 섀도잉 크래시 예방, 파일 주석에 근거).
- `App.jsx`는 task#257~258에서 988줄→535줄로 분해됐다. 지금은 `activeStage === '...' && (...)` 조건 렌더 블록 14개의 집합이고(task#307에서 개발 전용 `cast` 블록이 늘었다), 각 블록은 스테이지별 하위 내비를 `frontend/src/StageNav.jsx`(합성형 slot 컴포넌트 — `onBack`·`backLabel`·`lead`·`auxLabel`·`trailing` 슬롯 + `StageNav.Tab`/`StageNav.Title`)로 조립한다. 과거의 스테이지별 `render<X>Nav()` 함수 9개는 이 공용 껍데기로 대체됐다. 유일하게 동적 탭 배열·인장·색 분기가 필요한 `explore` 스테이지만 `frontend/src/ExploreStage.jsx`로 통째로 빼냈다(지도·연표·관계·소개·의존·족보 6뷰 + 여정 리스트 + 투어 재생, App.jsx가 `journey`·`playback`을 prop으로 주입).
  - **상태 수명 규칙(task#257~258 회고)**: 여정 데이터(`frontend/src/useExploreJourney.js`)와 투어 재생(`useTourPlayback`)은 코드는 훅이어도 **호출은 반드시 App에서** 한다. `explore` 스테이지의 "족보" 탭은 `setExploreView`가 아니라 `openFamily`로 별도 `family` 스테이지에 진입하므로 `activeStage==='explore'`가 꺼져 `ExploreStage`가 언마운트된다 — 그 안에서 훅을 부르면 여정·재생 상태가 언마운트와 함께 사라져 복귀 시 재fetch·초기화 회귀가 생긴다.
  - 개인화 저장(task#268~269)도 같은 이유로 App 레벨 단일 인스턴스다: `frontend/src/useBookmarks.js`(북마크·최근 이어보기, `localStorage['biblemap-bookmarks'/'biblemap-recent']`, 서버 쓰기 없음)와 `frontend/src/useReadingProgress.js`(장 단위 읽음 표시 + 이어읽기 판정 `computeResume`, `localStorage['biblemap-read']`). 둘 다 스키마 버전 필드를 가진 JSON을 쓰고 파손·구버전은 마이그레이션 없이 빈 값 폴백(ADR `260819-191704`). `frontend/src/BookmarkToggle.jsx`는 두 훅과 무관한 순수 토글 컴포넌트(저장 여부·클릭 콜백만 받음).
  - 전역 헤더는 `frontend/src/SpineHeader.jsx`(책등 리본 3부 + 테마 토글 + 검색 버튼, ADR-0026, `HEADER_H`·`RIBBON_OVERHANG` export). 검색 버튼과 `/` 단축키(App.jsx의 `keydown` 리스너, 입력 요소 위에서는 가로채지 않음)가 여는 `frontend/src/SearchPanel.jsx`는 전 스테이지 위에 뜨는 전역 오버레이라 `activeStage` 조건 렌더 밖에 있다.
- 스타일은 CSS-in-JS 없이 **인라인 style + `frontend/src/index.css`의 CSS 변수**로 한다. 토큰(`--bg-*`·`--ink-*`·`--gold*`·`--paper*`·`--type-*`·`--dur-*`·`--ease-*`)의 정본이 `index.css`이고, `frontend/src/theme.js`는 그 `var()`를 감싼 JS 상수다. 모션 클래스도 `index.css`에 모여 있다(`stage-in`·`thread-draw`·`symbol-draw`·`film-fade`·`film-in`·`beat-in`/`beat-out`·`intro-rise`·`intro-line`·`pressable`, ADR-0024).
  - 전역 `box-sizing: border-box` 리셋이 없다(ADR 260820-232144) — 모든 요소가 기본 `content-box`다. `width:'100%'`에 좌우 패딩을 인라인으로 더하면 박스가 패딩 2배만큼 뷰포트보다 넓어지고, 부모의 `alignItems:'center'`가 그 초과분을 좌우 대칭으로 흘려 **소스에 적힌 패딩이 시각적으로 정확히 0이 되는** 함정이 있다(리뷰로 못 잡히는 결함 클래스). `frontend/src/IntroView.jsx`의 `BeatFrame`이 이 국소 규약(폭+패딩을 선언하는 자리엔 `boxSizing:'border-box'`를 동반 + `wordBreak:'keep-all'`)을 인트로 비트 5곳(오프닝·지도·몽타주·메뉴장면·도착지)의 공용 진입점 하나로 모았고, `backend/scripts/validate_intro_gutter.py`가 이 규약을 정적으로 게이트한다(task#280).
- 지연 로드는 세 곳이다 — `frontend/src/TourPlayback.jsx`(`tourSketches.TourSketchPanel`)·`frontend/src/IntroView.jsx`(`tourSketches`의 default `TourSketch` — 인트로 몽타주 전용)·`frontend/src/App.jsx`(`./CastSheet`, `#/cast` 개발 시트). 청크 분할은 `frontend/vite.config.js`의 `manualChunks`(maplibre / vendor)에 더해 **`tourSketches.jsx` 안의 투어별 `import()`**가 함께 진다(task#287, 아래 "장면 스케치 · 인물 정본" 절).

## 프론트 스테이지 상태 머신

### 스테이지

`useStageNavigation`의 `activeStage` 값은 14종이다.

`intro` · `hub` · `overview` · `book` · `family` · `words` · `reader` · `stats` · `topics` · `canon` · `place` · `tours` · `explore` · `cast`

- `cast`(task#307, ADR `260823-190821`)는 **개발 전용 스테이지**다 — 사용자 화면 어디에도 링크가 없어 `#/cast`를 직접 입력해야만 도달한다. 대상 id 없는 고정 뷰라 `stats`/`topics`와 동형이고, `activeSection`에서는 `intro`와 함께 `null`(리본 전체 비활성)로 접힌다. 본문은 lazy로 불러오는 `frontend/src/CastSheet.jsx`.

- 초기값은 lazy initializer가 정한다: `urlState.isNoTarget(window.location.hash)`(해시가 없거나 `'#'`/`'#/'`인 **무타깃 진입** 판정의 단일 정본, task#281)가 참이고 `localStorage['biblemap-intro'] !== 'off'`이면 `intro`, 그 외엔 `hub`. 해시가 있으면(딥링크) 인트로는 무조건 건너뛴다. 이 초기값이 다음 프레임까지 유지되는 것은 아래 마운트 복원 effect가 **같은 `isNoTarget`**으로 무타깃 진입을 걸러내고 조기 반환하기 때문이다 — 두 지점이 서로 다른 판정을 쓰면(예: 복원 effect가 무타깃도 딥링크로 취급) 옳게 계산된 이 초기값이 곧바로 덮인다(task#281이 발견한 결함 클래스, `backend/scripts/validate_intro_entry_route.py`가 정적으로, `scripts/uat_intro_entry.py`가 실측으로 게이트).
- **스테이지 대상 id는 `selectedNode`와 분리된 전용 state**다: `bookId`·`familyId`·`wordsBookId`·`readerBookId`/`readerChapter`·`placeId`·`explorePersonId`·`exploreTourId`. 페이지 안에서 노드를 클릭해 시트를 띄워도 페이지 대상과 URL이 흔들리지 않게 하려는 설계다. `canon`(통사 연표, task#271)과 `stats`/`topics`처럼 대상 id 없는 고정 뷰도 있다.
- `explore` 스테이지만 내부 서브뷰 `exploreView`를 갖는다: `map` · `timeline` · `relations` · `intro` · `reliance`. 인물 모드는 `[소개, 여정, 연표, 관계, 의존, 족보]` 탭(족보는 탭이 아니라 `openFamily`로 전용 스테이지 진입), 투어 모드는 `[개요, 여정, 연표]`.
- `explorePersonId`와 `exploreTourId`는 **상호배타** — 하나를 세팅하는 핸들러가 다른 하나를 null로 만든다.
- 스테이지 전환은 전부 `useStageNavigation`이 export하는 핸들러로만 한다: `selectPerson`·`explorePerson`·`backToHub`·`openIntro`·`openOverview`/`overviewBack`·`openBook`/`bookBack`·`openFamily`/`recenterFamily`/`familyBack`·`openWords`/`selectWordsBook`/`wordsBack`·`openStats`/`statsBack`·`openTopics`/`topicsBack`·`openReader`/`selectChapter`/`readerBack`·`openTours`/`selectTour`/`toursBack`. 진입 지점이 다양한 페이지(`family`·`words`·`stats`·`topics`·`reader`)의 "뒤로"는 `window.history.back()`에 위임한다(ADR-0010).
- `App.jsx`의 `activeSection`이 스테이지를 헤더 리본 3부로 접는다: `overview`/`book`/`words`/`reader`/`stats`/`topics` → `books`, `tours` 및 투어 탐험 → `tours`, 나머지 → `persons`, `intro`·`cast`는 `null`(리본 전체 비활성).

### 해시 딥링크

라우터 없이 `frontend/src/urlState.js`의 `encodeHash`/`parseHash`가 상태 ↔ 해시를 순수 매핑한다(ADR-0009). 같은 파일이 `isNoTarget(hash)`(task#281)도 export한다 — "이 원시 해시가 딥링크가 아니라 무타깃 진입(첫 진입에서 아직 아무 화면도 지정되지 않음)인가"를 판정하는 별개의 질문이고, `parseHash`의 `''`/`'/'` → `{stage:'hub'}` 계약은 건드리지 않는다(`#/`는 정상적인 허브 URL이자 저장·이어보기 카드 복원(`handleGoToHash`)과 공용이라, "딥링크인가"는 `parseHash`가 아니라 `isNoTarget`이 답한다).

| 해시 | 스테이지 |
|---|---|
| `#/` | `hub` |
| `#/intro` | `intro` |
| `#/cast` | `cast`(개발 전용 — 링크 없음, ADR `260823-190821`) |
| `#/books` | `overview` |
| `#/book/<theographic_id>` | `book` |
| `#/read/<id>` · `#/read/<id>/<n>` | `reader`(장 그리드 / 장 본문) |
| `#/family/<id>` | `family` |
| `#/words/<id>`(`all` 포함) | `words` |
| `#/stats` | `stats` |
| `#/topics` | `topics` |
| `#/timeline` | `canon`(통사 연표, task#271) |
| `#/place/<id>` | `place`(task#270) |
| `#/tours` | `tours` |
| `#/person/<slug>`(+`/timeline`·`/relations`·`/intro`·`/reliance`) | `explore`(인물) |
| `#/tour/<slug>`(+`/timeline`) | `explore`(투어) |

- 인식 못 하는 해시는 `parseHash`가 `null`을 반환하고 호출부가 허브로 폴백한다.
- 노드 id는 **URL에 넣지 않는다** — `history.state.node`에만 실린다.

### 히스토리 통합 (ADR-0010)

`useStageNavigation` 안의 세 effect가 순서대로 물린다.

1. **복원 effect** — 가장 먼저 `isNoTarget(initialHashRef.current)`로 무타깃 진입인지 걸러낸다. 무타깃이면 `parseHash`/`applyParsedHash`를 태우지 않고 `restoredRef.current = true` + `setRestored(true)`만 하고 즉시 반환한다(task#281). 이 가드가 없던 시절엔 `parseHash('')`가 반환한 `{stage:'hub'}`가 `applyParsedHash`를 거쳐 위 lazy initializer가 계산한 `activeStage`(무타깃+인트로 켜짐이면 `'intro'`)를 곧바로 덮어써 — 초기값 계산과 이 effect가 "무타깃 진입인가"라는 같은 질문에 서로 다르게 답한 탓에 — 인트로가 켜져 있어도 무해시 첫 진입이 허브로 떨어지는 결함이 있었다. 딥링크(해시 있음)인 경우엔 `curatedIds`(=`/persons/curated` 응답)가 준비되면 마운트 시점 해시(`initialHashRef`)를 1회 파싱해 상태를 복원하고 `setRestored(true)`. person slug만 slug↔id 맵이 필요하므로, `overview`/`tours`/`tourSlug`/`hub`는 curated 로드 실패와 무관하게 즉시 복원된다. setState는 `Promise.resolve().then(...)`으로 마이크로태스크에 미룬다(effect 본문 동기 setState 금지 관행).
2. **sync effect** — `restored` 이후에만 write한다. `encodeHash`로 해시를, `{stage, person, tour, book, family, words, reader, chapter, place, view, node}`로 `history.state`를 만든다. **push 조건**은 `navSyncRef`의 직전 값과 비교해 스테이지/인물/투어/책/가계도/단어/리더/장/장소가 바뀌었거나 시트가 false→true로 열렸을 때이고, 그 외(뷰 토글·같은 대상 재설정·베이스 write)는 `replaceState`. `explore`인데 slug도 tour도 없으면 깨진 URL을 쓰지 않고 조기 반환한다.
3. **popstate effect** — 마운트 1회 등록. `event.state`에서 전 필드를 복원하고, `popstateGuard`를 세워 sync effect가 재-push하지 않게 한다. `state`가 **없을 때는 먼저 URL을 재해석한다** — `isNoTarget(window.location.hash)`가 거짓이면 `parseHash`+`applyParsedHash`로 복원하고, 무타깃일 때만 허브로 리셋한다. `state:null`은 히스토리 시작점과 "주소창에 다른 딥링크 해시를 붙여넣어 발생한 동일문서 프래그먼트 내비게이션"이 뭉뚱그려진 값이라, 구분 없이 허브로 리셋하면 URL이 가리키는 화면 대신 허브가 떴다(3차 버그 헌트 C4). 여기서도 무타깃 판정은 정본 술어(`isNoTarget`)만 쓴다.

`curatedIds`가 sync effect의 dep에 들어 있는 이유는, 카드 클릭이 slug 맵 로드보다 빨라 조기 반환했더라도 맵이 도착하면 재실행돼 올바른 `pushState`가 찍히게 하기 위해서다.

## 뷰 ↔ API 대응

| 스테이지/뷰 | 컴포넌트 | 소비 API |
|---|---|---|
| `intro` | `IntroView.jsx` | (없음 — 순수 연출) |
| `cast` | `CastSheet.jsx` | (없음 — `import.meta.glob`로 `sketches/cast/**` 열거) |
| `hub` | `PersonHub.jsx` | `/persons/curated` |
| `overview` | `BibleOverviewView.jsx` | `/books-overview`, `/messianic-prophecies` |
| `book` | `SidePanel.jsx`(재사용) | `/node/{id}`, `/node/{id}/places`, `/book/{id}/quotations` |
| `reader` | `ChapterReader.jsx` | `/book/{id}/chapters`, `/book/{id}/chapter/{n}` |
| `family` | `FamilyTree.jsx` | `/person/{id}/family` |
| `words` | `WordDistributionView.jsx` | `/books-overview`, `/words/{book}`, `/words/{book}/verses` |
| `stats` | `StatsView.jsx` | `/stats` |
| `topics` | `TopicalVersesView.jsx` | `/topical-verses` |
| `canon` | `CanonTimelineView.jsx` | `/timeline/canon` |
| `place` | `PlaceView.jsx` | `/place/{id}` |
| `tours` | `TourList.jsx` | `/tours` |
| `explore/map` | `MapView.jsx` + `JourneyList.jsx` | `/node/{id}/places`, `/parables-miracles`, `/event/{id}/verses` |
| `explore/timeline` | `TimelineView.jsx` | `/events`, `/covenants`, `/parables-miracles`, `/event/{id}/verses` |
| `explore/relations` | `RelationsView.jsx` | `/person/{id}/relations` |
| `explore/reliance` | `RelianceView.jsx` | `/person/{id}/reliance`, `/reliance/ranking` |
| `explore/intro`(인물) | `PersonIntro.jsx` | `/node/{id}`, `/persons/curated`, `/person/{id}/relations` |
| `explore/intro`(투어) | `TourIntro.jsx` | (App이 넘긴 `/tour/{id}` 응답 재사용) |
| 전역 시트 | `SidePanel.jsx` | `/node/{id}`, `/person/{id}/connections` 등 |
| 전역 검색 오버레이 | `SearchPanel.jsx` | `/search`(디바운스 250ms, 구절 검색은 2자 미만 스킵) |

`App.jsx`가 직접 호출하는 것: `/person/{id}/event-ids`(연표 인물 필터용 Set, `useExploreJourney` 소유), `/person/{id}/journey`, `/tour/{id}`(위 둘 다 `useExploreJourney` 소유), `/books-overview`(책 상세 정경순 이전/다음 내비 + 이어읽기용 `chapterCount`, task#269). `useStageNavigation`이 직접 호출하는 것: `/persons/curated`(유한 재시도 1s→2s→4s), `/keypeople-cards`.

## 투어 · 연표 · 지도 서브시스템의 관계

세 서브시스템은 **`journeyStops` 배열 하나를 공유**한다. `App.jsx`가 인물이면 `/person/{id}/journey`, 투어면 `/tour/{id}`에서 받아 `journeyStops` state에 담고, 백엔드가 두 응답의 `stops` 구조를 동일하게 맞춰 놓았다(`backend/app/routes/tours.py`의 주석 "journey.py 와 동일한 stops 구조": `seq`·`eventId`·`title`·`nameKo`·`sortKey`·`placeId`·`placeNameKo`·`lng`·`lat`, 투어는 여기에 `personNameKo`·`note` 추가).

- **투어 정의**는 `data/tours/<id>.json`(`{id, title, subtitle, era, description, stops:[{id, note}]}`). ADR-0011: 투어는 event-reference 오버레이라 Neo4j 노드를 만들지 않는다. `tours.py`가 `_build_event_index()`로 `data/person_events/*.json` 전체를 스캔해 stop id → event body를 해석하고 `sortKey`로 정렬한 뒤 Neo4j에서 좌표를 배치 조회한다. 미존재 투어는 404가 아니라 빈 stops(soft-empty, `journey.py`와 동일 관행).
- **자동재생**은 `frontend/src/useTourPlayback.js`(순수 시퀀서: `idx`·`playing`·`active`·`start`/`exit`/`toggle`/`next`/`prev`)와 `frontend/src/TourPlayback.jsx`(해설 카드 UI)로 나뉜다. 진행 간격은 `stepDuration(note) = 9000 + min(note.length*40, 5000)` ms이고, 이 함수는 이제 **export된다** — 체류 시간이 장면 드로인 예산에 종속되므로(ADR `260821-174856`) `tourSketches.jsx`가 채색 구간을 계산할 때 같은 함수를 직접 부르고, `backend/scripts/validate_scene_sketch_detail.py`가 이 공식을 소스에서 파싱해 경계를 파생한다. 하한이 4,000 → 5,000(task#286) → 9,000ms로 두 번 올랐는데, 원인은 장면 밀도 상향이다(전 투어 재생시간 약 +42%). `data/tours/*.json` 296정차지 실측 최단 note(84자)로 계산한 `min(stepDuration) = 12,360ms`가 장면 저작 규약 B6·B9의 예산 원천이다. 사건 단위로 진행하며 좌표 없는 정차지도 건너뛰지 않는다(카메라 유지·카드만 교체).
- **재생 ↔ 지도 카메라**의 연결은 `App.jsx`가 한다. `playback.idx`(사건 인덱스)를 `mapGeo.journeyStopGroups`가 만든 **장소 그룹 인덱스**로 `useMemo` 파생(`playbackStopIdx`)하고, 무좌표 사건이면 직전 좌표 사건의 그룹을 유지한다. 재생 중이면 이 파생값이, 아니면 사용자가 클릭한 `activeStopIdx`가 `effectiveStopIdx`로 합쳐져 `MapView`·`JourneyList`에 함께 내려간다. 투어를 벗어나거나 `exploreView`가 `map`이 아니게 되면 effect가 `playback.exit()`.
- **장면 스케치**는 `frontend/src/tourSketches.jsx`가 조회하지만, task#287부터 9모듈을 `SCENES` 하나로 정적 병합하지 **않는다** — `TOUR_MODULES`(투어 id → `() => import('./sketches/<tour>')`)로 **투어 단위 동적 로드**다. 등록 없는 정차지는 아무것도 렌더하지 않고, 모듈 로드 전에도 패널을 내보내지 않는다(카드 높이 점프 방지). `TourSketchPanel`이 카메라 `easeTo`(400ms) 정착 후 450ms 뒤 draw를 시작한다. `IntroView`의 몽타주 비트는 이제 별 모듈 `frontend/src/sketches/introMontage.jsx`에서 온다(ADR-0029). 상세는 아래 "장면 스케치 · 인물 정본" 절.
- **연표**(`TimelineView.jsx`)는 `/events`를 시대 밴드(`ERA_BANDS`)로 접는다. 그룹핑은 startDate 전체 병합이 아니라 **연속 동일 `startDate` 런(run)** 단위다 — `/events`가 `sortKey` 순이라 런 나열이 곧 병합 정렬 순서가 된다(저작 `"0030"` vs 원본 `"30"`처럼 문자열만 다른 층이 그룹을 통째로 갈라 순서를 뒤집던 문제 대응). 인물/투어 필터는 `App.jsx`가 넘기는 `Set`(`personEventIds` 또는 `tourEventIds`)으로 **멤버 단위** 필터링한다.
- **`ERA_BANDS`/시대 이름·순서는 네 곳에 수동 복제**돼 있다: `frontend/src/eraBands.js`(task#271에 `TimelineView.jsx`에서 공용 모듈로 승급 — `eraOf(y)`도 export)·`backend/app/routes/stats.py`(이름·`from` 튜플, `_era_of(year)` 동반)·`backend/app/curated.py`의 `ERA_ORDER`(이름·순서만, task#278에 `persons.py`에서 이관)·`frontend/src/PersonHub.jsx`의 `const ERA_ORDER` 사본. 파일들이 주석으로 서로를 가리키고, `backend/scripts/validate_era_bands_consistency.py`가 정합을 검사한다 — task#284로 3(+1)축에서 **7축**으로 확장돼 위 네 파일 외에 `data/covenants/covenants.json`의 `era`, `data/tours/*.json`의 `era`(저작 오타를 잡는 데이터 축), 그리고 프론트 전역에서 `era`/`Era` 식별자 사슬이 시대 이름 리터럴과 `===` 비교하는 지점(예: `TimelineView`의 `sec.era.name === '신약'`, `ExploreStage`의 `...?.era === '신약'` — 비유·기적 토글의 **유일한** 게이트라 이름이 갈리면 토글이 에러 없이 그냥 사라진다)까지 정적으로 스크래핑해 대조한다(`eraBands.js`의 `const ERA_BANDS = [` 리터럴 모양을 바꾸면 검사가 깨지는 정규식 스크래핑 — fail-closed로 감내하는 취약성, ADR 260819-205242). `CanonTimelineView.jsx`(통사 연표, task#271)도 같은 `eraBands.js`를 소비한다.
- **통사 연표**(`CanonTimelineView.jsx`, task#271)는 인물/투어 탐험의 `explore/timeline`과 별개 스테이지(`canon`)다 — 창세기~계시록 전체를 8개 `ERA_BANDS` 섹션으로 세로로 쌓고, 시대 안에서만 연도 비례축을 쓴다(가로 통 축은 신약 33%가 9.5px로 무너져 폐기, ADR `260819-210927`). 데이터는 `/timeline/canon` 하나(신규 저작 0) — `stats.ERA_BANDS`·`events._compute_events()`·`person_events/<slug>.json`의 `sortKey` min/max(`backend/app/routes/timeline.py`)를 재조합한다.
- **장소 페이지**(`PlaceView.jsx`, task#270)는 지도 마커 클릭·정차지 클릭·상세 시트 어디서든 `openPlace(id)`로 진입하는 전용 전체화면(`place` 스테이지). 데이터는 `/place/{id}` 하나(`overlays.place_context()` + `place_coords()` + `_place_to_persons` + 사건 목록 합성). `mapLayers.js`의 장소 팝업이 "이 장소 보기" 버튼(`wirePlaceLink`)을, 여정 정차지 GeoJSON(`buildJourneyStopsGeoJSON`)이 그룹 대표 `placeId`를 실어 같은 진입점을 공유한다.
- **비유·기적**은 지도와 연표 양쪽에 얹힌다. 지도는 `pm-source`/`pm-circle` 레이어(기본 `visibility:none`)로 `MapView`가 `/parables-miracles`를 1회 fetch한 뒤 토글(`pmVisible`)·종류 필터(`pmFilter`: all|parable|miracle)로 `setLayoutProperty`/`setFilter`만 갱신한다. 연표는 `'신약'` era 섹션 머리에 목록 한 벌을 렌더한다(날짜가 없어 개별 사건 위치에 못 꽂음). 두 UI는 필터 칩 정의를 각자 `PM_FILTERS` 상수로 갖는다(별 파일이라 공유 안 함). 노출 게이트는 `App.jsx`가 계산하는 `pmEnabled = (explorePersonId ? explorePersonEra : exploreTourMeta?.era) === '신약'`이고, era의 원천은 백엔드 `curated.CURATED`(`/persons/curated` 응답, task#278에 `persons._ERA`에서 이관)다. 이 리터럴 비교 자체가 `validate_era_bands_consistency`의 7번째 축(era 기능 게이트) 대상이다(task#284). 지도에 못 얹는 무좌표 항목 수는 `MapView`가 `pmNoLocCount`로 세어 "연표에서 확인" 안내를 띄운다.
- **언약**은 연표 전용이다 — `/covenants`의 `era` 값이 `ERA_BANDS`의 `name`과 그대로 일치한다는 전제로 시대 섹션에 리본으로 얹는다.

## 지도 서브시스템 내부

`frontend/src/MapView.jsx`가 maplibre-gl 지도 인스턴스를 소유하고, 배선은 세 모듈로 나뉜다.

- `frontend/src/mapLayers.js` — `setupMapSources(map)`(소스·레이어 선언)와 `registerEventHandlers(map, {...})`(클릭·팝업). 레이어 그룹: 여정선(`journey-line` + 방향 화살표, `lineMetrics:true`), 정차지 배지(`journey-stop-*`), 활성 강조(`journey-active-*`), 장소(`places-*` 클러스터 + `place-spider-*`), 사건 링(`event-ring-*`), 비유·기적(`pm-circle`). `EMPTY_GEOJSON` 상수도 여기서 export.
- `frontend/src/mapGeo.js` — 순수 GeoJSON 변환·기하 계산(`coreBounds`·`placesToGeoJSON`·`buildJourneyLineGeoJSON`·`buildJourneyStopsGeoJSON`·`journeyStopGroups`·`buildParablesMiraclesGeoJSON`·`buildEventGeoJSON`·`buildSpiderGeoJSON`·`ringPositions`·`ringLabels`·`easeOutCubic`).
- `frontend/src/mapRingController.js` — `createRingController(map, {...})`로 사건 링 펼침/접기 애니메이션과 스파이더 상태를 캡슐화. `MapView`가 `expandPlaceRef`/`expandedPlaceRef`로 selection effect와 공유한다.

`MapView`의 프레이밍은 `clampPadding(map, padding)`을 거친다 — fitBounds 패딩 합이 컨테이너의 60%를 넘으면 maplibre가 줌을 최소로 클램프해 모바일에서 세계축소 뷰로 튀기 때문이다. 팝업 ref는 장소용(`popupRef`)과 비유·기적용(`pmPopupRef`)이 분리돼 있다.

## 절 레이어(VerseLayer)

`frontend/src/VerseLayer.jsx`가 "양피지 구절 모달" 공통 쉘이다. `createPortal`로 `document.body`에 렌더하므로 호출 트리와 무관하고, ≤`MOBILE_BREAKPOINT`(768)는 하단 시트, 그 위는 중앙 모달이다. `paperTextStyle`·`VerseBookTabs`를 함께 export한다. 언어 탭 UI는 `frontend/src/VerseLangTabs.jsx`이고, 표시 언어 state `verseLang`('ko'|'en')는 **`App.jsx`가 소유**해 `TimelineView`·`SidePanel`·`BibleOverviewView`·`TopicalVersesView`·`ChapterReader`·`WordDistributionView`·`JourneyList`·`RelationsView`·`RelianceView`·`PersonIntro`에 prop으로 내려간다. `PlaceView.jsx`는 `verseLang`만 읽기 전용으로 받는다(`setVerseLang` 미주입 — 장소 페이지 자체엔 언어 토글이 없다).

## 심볼 시스템

- `frontend/src/personSymbols.jsx` — 인물 인장. 키는 인물 `slug`, 미등록은 범용 폴백. `hasSymbol(slug)`로 등록 여부를 판정하고(가계도 앵커 등), `PersonSymbol` 컴포넌트가 `draw` prop으로 1회 stroke 애니메이션(`symbol-draw`).
- `frontend/src/bookSymbols.jsx` — 책 상징. 책은 slug가 없으므로 키가 `theographic_id`다.
- `frontend/src/sketches/lib.jsx` — 장면 스케치 공용 헬퍼(`P`·`W`·`sw(n,o)`·`d(ms,reduce)`)만 두는 순수 모듈. 이름표 컴포넌트 `Label`은 `react-refresh/only-export-components` 규칙 때문에 `frontend/src/sketches/SceneLabel.jsx`로 분리돼 있다.

## 장면 스케치 · 인물 정본

투어 정차지 삽화는 세 층으로 나뉘고, **코드 경계가 곧 번들 경계**다(task#287 — ADR-0029가 정한 "투어별 JSX 모듈"을 청크 경계로 승격).

- **투어 모듈** `frontend/src/sketches/<tourCamelCase>.jsx` 9개 — 각자 파일 끝에서 `{ '<eventId>': { Scene, desc, caption, mood?, letterLast?, color? } }` 레지스트리를 default export. `tourSketches.jsx`의 `TOUR_MODULES`(투어 id → `() => import(...)`)가 정차지가 속한 투어의 모듈만 내려받는다.
- **인트로 전용 소형 모듈** `frontend/src/sketches/introMontage.jsx` — 오프닝 몽타주 5씬의 **정의를 여기 두고** 각 투어 모듈이 자기 레지스트리를 위해 되가져간다. 의존 방향이 이 파일의 존재 이유다: 소형 모듈이 무거운 모듈을 참조하면 롤업이 `INEFFECTIVE_DYNAMIC_IMPORT`로 분할을 무효화해 5모듈이 메인 청크에 병합된다(파일 주석에 실측). `tourSketches.jsx`의 default export `TourSketch`는 이제 이 레지스트리만 본다(인트로 전용).
- **인물 정본** `frontend/src/sketches/cast/*.jsx`(현재 `david`·`goliath`)와 **지물 참고 도상** `frontend/src/sketches/cast/props/*.jsx`(현재 `altar`) — ADR `260823-190821`. 정본은 머리 윤곽·머리카락 등만 그리고 이목구비는 슬롯으로 비운다(표정은 장면이 그린다). 호출 규약이 딱딱한데, 이유가 게이트다: `cx`·`cy`·`scale`·`delay`는 **숫자 리터럴만**, `transform`·조건 분기 금지 — `backend/scripts/validate_scene_sketch_detail.py`가 이 소스를 정적으로 읽어 호출부 리터럴로 아핀 변환해 장면 stroke 목록에 **인라인 전개**하기 때문이다(그러지 않으면 정본을 쓴 장면에서 밀도·구조 경계가 조용히 헛돈다). `stroke-width`는 `scale`을 곱하지 않는다(굵기 판정 정규식이 `sw(<리터럴>)`만 읽고, 광학 보정으로도 그쪽이 낫다). 파일이 자기 `export const AXES`(5축)와 `export const aliases`를 함께 선언하므로 `frontend/eslint.config.js`가 이 디렉터리에만 `react-refresh/only-export-components`를 끈다.

렌더·타이밍은 `tourSketches.jsx`의 `SceneSvg`가 진다.

- **draw-on 토큰 분리** — 장면은 `.scene-draw` 클래스 + `--dur-draw-scene`(500ms)를 쓰고, 인물·책 인장(`.symbol-draw`)·가계도 실(`.thread-draw`)·인트로 분할선(`.intro-line`)은 공용 `--dur-draw`(1000ms)를 그대로 쓴다. 장면만 선 천장을 크게 올렸으므로 공용 토큰을 낮추면 무관한 소비자까지 빨라진다는 판단(`index.css` 주석). 장면 드로인 총 길이 = `max(--sym-delay) + --dur-draw-scene`.
- **`letterLast`(옵트인)** — `useLayoutEffect`로 실제 드로인 완료 시각을 계측해 `--reveal-end`에 심고, `sketches/SceneLabel.jsx`의 `Label after={i}`가 그 값에서 CSS 스태거 페이드인을 파생한다(수동 `at=` 초 값 대신 소스 파생, ADR `260823-112504`).
- **`color`(옵트인)** — 채색층 자산 경로(`/scene-color/*.webp`, 실물은 gitignored `frontend/public/scene-color/`). 있으면 3층(채색층 아래 + 저작 잉크 위)을 렌더하고, `<mask>` 안에 Scene을 한 번 더 그린 `.scene-wash` 복제가 저작 붓질 순서를 `--wash-k`로 압축 재생해 "붓이 지나간 자리에 색이 남는" 연출을 만든다. 예산은 `min(stepDuration(note), GLOBAL_MIN_STEP_MS=12360) − 450ms`(전역 보수 상한이 항상 이기게 둔 이중 방어). `<image>` 404는 브라우저 기본 깨진-이미지 아이콘이 마스크를 통과해 얼룩이 되므로 `onError`로 `<image>` 자체를 걷어낸다.
- **확대 오버레이** — 완성된 패널을 탭하면 `createPortal`로 `document.body`에 뜬다(조상 `transform`이 `fixed`의 containing block을 바꾸므로, `VerseLayer.jsx`와 같은 관용구). 새 `<svg>` 인스턴스라 연출이 처음부터 재생되는 것을 막기 위해 열자마자 CSS 애니메이션은 `pause()`+`currentTime`, SMIL은 `setCurrentTime()`으로 종료 시점에 고정한다.

**저작 규약의 정본은 `frontend/src/sketches/lib.jsx`의 주석**이다(경계 B1~B12 · 신체 조립 규칙 · 상자·사다리로 읽히는 실패 목록 · 배치 레시피 · 정본 컴포넌트 규약). 강제는 `backend/scripts/validate_scene_sketch_detail.py`이고, 경계값을 파일에 박지 않고 **실제 소스에서 파생**한다: `--dur-draw-scene`은 `index.css`, 패널 대기(450ms)는 `tourSketches.jsx`, `stepDuration` 공식은 `useTourPlayback.js`, note 길이는 `data/tours/*.json`. 선분 대 상자 교차 판정에 필요한 SVG path 좌표 전개는 `backend/scripts/_svgpath.py`가 공용으로 낸다(바운딩 박스로 재면 가로로 긴 능선 하나가 띠 전체를 덮은 것으로 잡혀 과대평가된다).

**커버리지 게이트도 동적 구조에 맞춰 재정의됐다** — `backend/scripts/validate_scene_coverage.py`는 이제 "키가 있다"가 아니라 "**그 투어의 모듈 안에** 있다"로 판정하고, 일곱 결함 클래스를 각각 다른 메시지로 가른다: A 미저작 · B 고아 키 · C 허용목록 잔존 · D 모듈 미연결 · E 투어 미연결 · F **오배치**(동적 구조가 새로 만든 무음 결함) · G 인트로 미연결(`IntroView.jsx`의 `ERA_SCENES` ↔ `introMontage` 레지스트리). A와 D/E/F는 증상이 같고(무음·무오류) 처방이 정반대라, 뭉뚱그리지 않는 것이 이 게이트의 요점이다.

**저작자의 눈** 둘도 코드에 있다 — 선화 저작 에이전트는 자기 그림을 못 보므로, `frontend/src/CastSheet.jsx`(개발 전용 `#/cast`, `import.meta.glob`로 `cast/`와 `cast/props/`를 **별도 glob**으로 열거해 주역·보조·원경 세 배율로 깐다)와 `scripts/render_scene.py`(빌드→렌더→고배율 촬영, `--at`로 시각 스크럽·`--min-stroke-width`로 굵기 계단·`--cast`로 시트 촬영)가 그 역할이다. `render_scene.py`는 `lib.jsx`의 `W`를 파생해 굵기 임계를 DOM 값으로 환산한다(복사하면 `W` 변경 시 계단이 조용히 어긋난다).

## 저작 파이프라인 (`scripts/canon/`)

앱과 **다른 런타임에서 도는 오프라인 이미지 생성·판정 파이프라인**이다(레포 밖 venv `~/.local/biblemap-imggen/`, GPU). 앱은 이 코드를 import하지 않고, 산출 이미지는 gitignored인 `.forge/reports/canon-pilot/`에 쌓인다 — 그래서 **재현 명령이 곧 산출물**이다(시드 고정).

단계 구조는 다섯이고, 각 단계의 정본이 다른 파일에 산다.

1. **장면 명세** — `scripts/canon/notes/*.md`(대문자 판단 문서 20개). 현행 정본은 `notes/SCENE-1SAM17.md`(요소마다 출처 절을 단 사무엘상 17장 명세 + 요구 항목 10개 체크리스트)이고, 프롬프트 작성 규칙 실측은 `notes/PROMPTING.md`다.
2. **프롬프트 파생** — `derive_prompts.py`가 손으로 쓰지 않고 파생한다: `frontend/src/sketches/cast/*.jsx`의 `export const AXES`를 정규식으로 읽어 영문 어휘로 매핑하고, 나이는 `data/person_events/<slug>.json`의 `sortKey`(출생 대비)에서 계산한다. 산출은 `notes/prompts.json`(생성기들이 읽는다).
3. **생성** — `gen_*.py`(21개). 현행 정본 경로는 `gen_scripture_scene.py`: **콘티(ControlNet) 없이** 본문 파생 서술을 여덟 단계(`S1`·`S1b`·`S1c`·`S2a`·`S2b`·`S3`·`S4`·`S5`)로 인페인팅한다. 단계화의 이유가 기계적이다 — CLIP 창이 77토큰이고 **단계마다 예산이 새로 생기므로** 74 → 합계 444가 된다. 마스크 원천은 이 파일의 `REGIONS`(canvas 분율 상자) 한 곳이고, 인물 단계(`PLATE_STAGES` = `S3`·`S4`·`S5`)는 장면 안에서 그리지 않고 **민 종이 위에 단독으로 그려 종이색 기준으로 오려 붙인다**(판 합성 — 그 대가인 접지는 발 주변 띠만 다듬어 갚는다).
4. **판정** — `judge_*.py`(8개). 현행 정본은 `judge_scene.py`(축 C1 골짜기·C2 군대·C3 이음매·C4 화풍·C5 인물, 다섯 축 통과 시 종료코드 0). **판정자는 생성자를 import하지 않는다** — 하면 `torch`·`diffusers`가 딸려 와 GPU 없이 못 돌기 때문에 `REGIONS` 좌표만 복제하고 `--check`로 대조한다. 콘티를 버리며 파생원을 잃은 축 C·D·G(`judge_s1.py`·`judge_final.py`)는 이 새 판정자로 대체됐고, 화풍 축만 `judge_style.style_metrics`로 살아남았다.
5. **노트 갱신** — 판정 결과가 `notes/s0-baseline.json`·`notes/s1-baseline.json`·`notes/final-verdict-*.json`(37개 meta json)으로 못박히고, 교훈은 다시 1의 `.md`로 돌아간다.

파이프라인 전체를 묶는 규율 셋.

- **[[생성 파라미터]] 정본은 `scripts/canon/params.py` 하나**다(모델 ID·`STEPS`·`GUIDANCE`·CN/IP 강도·캔버스 크기·시드). 다른 `.py`가 같은 이름을 모듈 레벨로 재대입하면 `backend/scripts/validate_canon_pipeline.py` 축1이 배포를 막는다 — 검사 목록을 손으로 유지하지 않고 정본을 AST로 파싱해 **키 집합을 파생**하며, 이름만 바꾼 사본을 잡기 위해 `repo/name` 형태 문자열(모델 ID)은 **값으로도** 본다.
- **임계는 정답지에서 파생하고, 결과를 보고 만지지 않는다**(ADR `260825-013557`). 축 A(화풍)의 양성 기준은 `scripts/canon/reference/`의 정답지 10장이고, `judge_style.reference_paths()`가 그 디렉터리 **직속** `*.png`를 glob으로 전부 읽는다(무엇을 쓸지 손으로 고르지 않는다 — 고르는 순간 유리한 쪽만 남길 여지가 생긴다) — 그래서 **새 이미지를 `reference/` 직속에 넣으면 임계가 부작용으로 바뀐다**. 그래서 설정화 시트는 `scripts/canon/setup/`에, 전신 표본은 `samples/`에, 동결 얼굴은 `frozen/`에, 장면 구도 앵커는 `scene_ref/`에, 폐기된 콘티와 그 마스크 파생은 `conti/`에 각각 따로 산다.
- **`scripts/` 아래 미추적 파일은 배포를 막는다**(`validate_canon_pipeline.py` 축2, git 미가용 시 skip 계약). 위생이 아니라 게이트 자신의 무결성 문제다 — `scripts/check.sh`가 부르는 `check_cast_axes.py`·`check_mask_ranges.py`가 미추적이면 새 클론·CI에서 게이트가 깨진다. 판정 기준인 `reference/`가 gitignored `.forge/reports/`에 있다가 이 자리로 옮겨온 이유도 같다.

**재현은 아직 닫히지 않았다** — `scripts/canon/requirements.txt` 머리 주석이 미결 3축을 미결로 적어 둔다: 모델 리비전 미고정(허브 저장소 이름일 뿐), MPS 결정성 미보장, 재현 미실측. `params.IMAGE_ENCODER`만 스냅샷 해시가 박혀 있는데 그건 이 머신 로컬 캐시의 절대경로라 다른 머신에서 성립하지 않는다.

프롬프트를 손볼 때의 연습대는 `try_prompt.py`다 — `--check`는 GPU·모델 로드 없이 토큰만 재고(77토큰을 넘으면 **에러 없이 잘려** 뒤의 화풍 블록이 통째로 사라지는 것이 이 도구의 존재 이유), 인자 없이 부르면 한 장을 뽑아 세 축 수치를 함께 낸다. 임계는 이 도구가 정하지 않고 `notes/s0-baseline.json`에서 읽는다.

## 데이터 흐름 (엔드투엔드)

### 빌드타임 — 그래프·오버레이 준비

1. `docker compose up -d`로 Neo4j 기동.
2. `python3 backend/scripts/load_theographic.py` — 원본 그래프 적재.
3. `python3 backend/scripts/inject_ko_names.py`, `python3 backend/scripts/inject_date_corrections.py`(및 나머지 저작 로더·inject) — 프로퍼티 SET·저작 레이어 병합. **로더 재실행 시 inject 재실행 필수.**
4. 오버레이 JSON 중 파생물은 `generate_*.py`/`build_*.py`가 만든다(`generate_bible_text.py` → `data/bible/verses.json`, `build_word_distribution.py` → `data/word_distribution.json`, `generate_event_verses.py` → `data/event_verses/events.json`, `build_verse_persons.py` → `data/verse_persons/index.json`, `build_word_verse_index.py` → `data/word_verse_index/index.json`). `covenants`·`messianic_prophecies`·`topical_verses`·`jesus_parables_miracles`·`place_coords`·`tours`는 직접 저작한 정본이라 생성기가 없다.

### 런타임 — 요청 한 번

1. 브라우저가 해시 URL로 진입 → `useStageNavigation`이 `parseHash`로 스테이지 복원.
2. 뷰가 `frontend/src/api.js`의 `apiGet(path, {signal})`로 fetch. 베이스는 `import.meta.env.VITE_API_URL || 'http://localhost:8000'`(프로덕션은 `/api` → nginx 프록시). 모든 요청에 `?v=<BUILD_ID>`가 붙는다 — `frontend/vite.config.js`의 `define.__BUILD_ID__ = Date.now()`라 배포마다 값이 바뀌어 옛 응답 캐시를 무력화하고, 같은 배포 안에서는 고정이라 `max-age` 이점은 유지된다. 비-OK 응답은 `err.status`를 실은 `Error`로 reject하고 `AbortError`는 그대로 전파한다.
3. FastAPI 라우트가 `get_driver()` 그래프 쿼리 + `overlays.*()` 오버레이를 합성해 `JSONResponse`로 반환.
4. 프론트가 렌더. 절 본문 드릴다운은 `VerseLayer` 양피지 모달로.

### 배포

- `push → main` → GitHub Actions `self-hosted` 러너(`.github/workflows/deploy.yml`)가 `git fetch` + `git reset --hard origin/main` 후 `bash deploy.sh`.
- `deploy.sh`는 lock 파일(`/tmp/biblemap-deploy.lock`)로 중복 실행을 막고, macOS 키체인 우회를 위해 임시 `DOCKER_CONFIG`를 만든 뒤(기본 `cli-plugins` 심볼릭 링크 포함) `.env`를 로드한다. **task#259에서 순서가 fail-closed로 재배치**됐다(ADR `260801-195022` — 주입은 멱등이므로 검증 **앞**에서 DB를 정본으로 되돌린 뒤 게이트가 판정해야 하고, 뒤에 두면 검증이 이미 끝난 뒤라 아무 의미가 없다):
  1. Neo4j `127.0.0.1:7687` 도달 대기(최대 15회×2초). 미도달이면 즉시 배포 중단(주입을 대기 실패로 위장시키지 않도록 `2>/dev/null` 없이 실행).
  2. `inject_ko_names.py` + `inject_date_corrections.py` 재적용(둘 다 멱등, 재시도 없이 1회 실행 — 실패 시 배포 중단).
  3. 프론트 `npm install`(게이트의 ESLint·vitest가 스킵되지 않으려면 게이트보다 먼저).
  4. **검증 게이트** — `CHECK_STRICT=1 bash scripts/check.sh`. 실패하면 빌드 전에 배포를 중단한다.
  5. `npm run build` → `frontend/dist`.
  6. `docker compose -p biblemap build api`.
  7. `docker compose -p biblemap up -d api` + `docker compose -p biblemap up -d --force-recreate nginx`(nginx는 이미지 빌드가 없고 바인드 마운트 스펙이 불변이라 `nginx.conf`만 바뀌면 Compose가 변경을 못 잡아 매 배포 강제 재생성한다, task#263).
- **`deploy.sh`는 `inject_ko_names`·`inject_date_corrections` 두 가지만 자동 재적용한다** — `load_*`와 그 밖의 `inject_*`(`inject_book_context`·`inject_person_context`·`inject_person_traits`·`inject_place_context`)는 여전히 수동이다.
- `scripts/check.sh`는 AI 없이 도는 게이트다: 파일 기반 검증 **22종**(기존 15종 `validate_covenants`·`messianic_prophecies`·`parables_miracles`·`topical_verses`·`pm_map_coverage`·`scene_coverage`·`chapter_sections`·`chapter_summaries`·`quotations`·`person_context`·`god_reliance`·`traits`·`era_bands_consistency`·`approx_book_verses`·`intro_menu_parity` + task#278~284로 추가된 `curated_persons`·`intro_gutter`·`intro_entry_route`·`event_verses`·`sortkey_startdate` + task#285~286의 `api_cache_headers`·`scene_sketch_detail`)를 `python3 -m backend.scripts.validate_*`로 돌리고, 그중 10종(`intro_menu_parity`·`curated_persons`·`intro_gutter`·`intro_entry_route`·`event_verses`·`sortkey_startdate`·`era_bands_consistency`·`api_cache_headers`·`scene_sketch_detail`·`scene_coverage`)은 `--selftest`(고의 드리프트를 인메모리로 주입해 게이트 자체가 실제로 FAIL하는지 확인하는 대조군, task#277 이후 관행 — 기준선 PASS만으론 게이트가 살아있음을 증명 못 한다, ADR 260820-003946)를 뒤따라 실행한다. 이어 별도 절로 세 가지를 돌린다. ① **저작물 소스 불변식** — `python3 scripts/check_cast_axes.py`(인물 정본 `cast/*.jsx`의 5축 조합이 서로 겹치지 않는가 = 구별성 1단)와 `python3 scripts/check_mask_ranges.py`(+`--selftest`, `GoliathScene`의 다윗·골리앗 영역 마스크 `delay` 범위가 연속하고 겹치지 않는가 — 이 모듈의 `derive_ranges()`를 저작 파이프라인의 `make_masks.py`가 그대로 가져다 쓴다). 이 둘은 `backend/scripts/`가 아니라 **최상위 `scripts/`**에 있어 모듈 경로가 아니라 파일 경로로 불린다. ② **저작 파이프라인 가드** — `validate_canon_pipeline`(+`--selftest`)을 git 작업트리일 때만(둘째 축이 git을 쓴다). ③ `validate_forge_docs_tracked`(+ `--selftest`)를 git 작업트리일 때만 돌린다 — 데이터 검증이 아니라 `.forge/adr/`·`.forge/retro/`(영구 문서)에 미추적 파일이 있으면 FAIL하는 로컬 위생 가드다(task#279). 이 가드는 배포 경로에서도 살아 있다: `.github/workflows/deploy.yml`이 개발 트리와 같은 디렉터리에서 `git reset --hard origin/main` 후 `deploy.sh`를 부르는데 하드리셋은 추적 파일만 되돌리고 **미추적 파일은 남기므로**(`git clean`이 아님), 미추적 ADR·회고가 있으면 `CHECK_STRICT=1` 배포 경로에서 배포가 중단된다. 그 뒤 ESLint + `npm test`(vitest, task#261)를 `frontend/node_modules` 있을 때만, Neo4j 연대 정합(`validate_event_chronology`)을 `127.0.0.1:7687` 기동 시에만 검사한다. **`CHECK_STRICT=1`이면 위 두 스킵이 실패로 승격**된다(task#259) — 배포 경로는 항상 이 모드로 부른다. 기본(비-strict) 모드는 Neo4j 없이 단독 개발 실행 시 스킵-경고로 남는다. 하드 항목이 하나라도 실패하면 종료 코드 1.
- 브라우저 렌더·픽셀·네트워크가 있어야만 잡히는 축은 `scripts/uat_*.py` **네 개**로 따로 둔다 — `uat_intro_gutter.py`(비트 여백, task#280)·`uat_intro_entry.py`(무타깃 진입, task#281)·`uat_scene_detail_pilot.py`(장면 세밀화 파일럿 3장면 + 필름스트립, task#286 — 애니메이션을 `pause()`+`currentTime`/`pauseAnimations()`+`setCurrentTime()`으로 같은 시각에 고정해 결정론적으로 찍는다)·`uat_tour_chunk_split.py`(투어별 청크 분할, task#287 — 9투어 렌더·인트로 5씬·**격리**(한 투어 재생 중 다른 투어 청크가 요청되지 않음)·카드 높이 점프 0을 네트워크까지 보고 판정한다). 네 개 모두 `check.sh`에는 배선하지 않는다 — `deploy.sh`는 `npm run build`보다 **먼저** `check.sh`를 부르므로 그 시점의 :8080은 옛 빌드를 서빙해, 배선하면 초록·빨강이 둘 다 거짓이 된다. 두 UAT는 URL 형태마다(`/`·`/#`·`/#/`·`#/books` 등) 새 브라우저 컨텍스트로 진입해(SPA 해시 변경은 리마운트가 아니므로 같은 컨텍스트 재사용은 결함을 재현하지 못한다) `location.hash` 수렴과 DOM 마커(`[data-intro-layer]`)를 함께 확인하고, 종료 코드로 제품 결함(1)과 측정 환경 이상(2, 예: dist가 소스보다 낡음)을 자가 구별한다.
- `docker-compose.yml`(프로젝트명 `biblemap`) 서비스 3개: `neo4j`(볼륨 `neo4j_data`, 포트는 `127.0.0.1`에만 바인딩), `api`(`./data:/app/data` 마운트 — 오버레이가 읽는 경로, 외부 포트 미노출), `nginx`(`./frontend/dist` + `./nginx/nginx.conf` 마운트, 8080 노출).
- `nginx/nginx.conf`: `/api/` → `http://api:8000/` 프록시, `index.html`은 `no-store` 계열, 해시 붙은 정적 자산은 `max-age=31536000, immutable`, 나머지는 `try_files $uri /index.html`(SPA 폴백). gzip 활성화(task#260, `gzip_comp_level 5`·`gzip_proxied any` — 이게 없으면 `/api/*` 프록시 응답이 통째로 압축에서 빠진다).
- 프론트 :8080은 `frontend/dist` 마운트라 HMR이 아니다 — 로컬 검증 전에 `cd frontend && npm run build`가 필요하다.

## 핵심 추상화

- **오버레이 로더**(`overlays._load` + `lru_cache(maxsize=1)`) — 그래프에 없는 콘텐츠를 JSON으로 관리하고, `verseID` 참조를 `bible_verses()`로 본문 합성한다.
- **큐레이션 인물 레지스트리**(`backend/app/curated.py`의 `CURATED`/`ERA_ORDER` + `curated_index()`/`id_to_slug()`/`slug_to_id()`/`seal_id_to_slug()`) — slug 목록·시대·한글명·id 해석의 단일 출처(task#278에 `persons.py`에서 승급, overlays.py와 같은 층이라 라우트를 import하지 않는다). `persons`·`journey`·`tours`·`stats`·`places`·`reliance`·`family`·`timeline` 8개 라우트가 import한다.
- **큐레이션 신원 규약**(`overlays.curated_person_id`) — `data/person_events/<slug>.json`의 `events[0].participants[0]`가 그 인물의 `theographic_id`. id↔slug 해석의 단일 출처(위 `curated.py`가 이 규약 위에서 색인을 만든다).
- **스테이지 머신**(`useStageNavigation`) — 대상 id를 `selectedNode`와 분리하고, sync effect가 URL·히스토리를 미러한다.
- **해시 코덱**(`urlState.encodeHash`/`parseHash`/`isNoTarget`) — 라우터 없는 순수 문자열 매핑 + "무타깃 진입(딥링크 아님)"인지 판정하는 단일 정본(task#281).
- **공유 stops 계약** — `/person/{id}/journey`와 `/tour/{id}`가 같은 stops 구조를 반환해 `MapView`·`JourneyList`·`TimelineView`·`TourPlayback`이 분기 없이 재사용한다.
- **양피지 절 레이어**(`VerseLayer`) — 포털 기반 반응형 구절 모달 공통 쉘.
- **공유 API 클라이언트**(`api.apiGet`) — 단일 베이스 URL + 빌드 ID 캐시 버스팅.
- **스케치 레지스트리**(투어 모듈의 default export) — `eventId` → `{Scene, desc, caption, mood?, letterLast?, color?}` 매핑, 미등록은 무렌더. task#287부터 병합 레지스트리가 아니라 `tourSketches.TOUR_MODULES`가 투어 단위로 동적 로드하므로 **키의 소속 모듈이 판정에 들어간다**(오배치 = 무음 결함).
- **인물 정본 컴포넌트**(`sketches/cast/*.jsx`) — 여러 장면이 공유하는 인물의 머리를 강제 컴포넌트로 두고 이목구비는 슬롯으로 비운다. 호출 규약을 숫자 리터럴로 못박은 것은 **게이트가 소스를 정적으로 읽어 인라인 전개**하기 때문이다(파서를 인터프리터로 만들지 않는다). 규약 정본은 `sketches/lib.jsx`.
- **[[생성 파라미터]] 정본**(`scripts/canon/params.py`) — 저작 파이프라인의 모델 ID·샘플링·강도·시드를 한 곳에서만 선언하고, 재선언을 AST 파생 키 집합으로 차단한다(`validate_canon_pipeline` 축1). 값 축은 오탐이 0인 모델 ID로만 한정한 것이 이 불변식이 인코딩한 결함 클래스의 경계다.
- **생성 ↔ 판정 분리**(`gen_*.py` ↔ `judge_*.py`) — 판정자는 생성자를 import하지 않는다. 실용적 이유(판정자는 GPU 없이 돌아야 한다)와 방법론적 이유(임계를 결과 보고 고치는 결론 선취를 막는다)가 겹쳐 있고, 공유가 필요한 좌표는 복제 + `--check` 대조로 잇는다.
- **스테이지 내비 껍데기**(`StageNav`, task#257) — 9개 이상의 스테이지 하위 내비가 공유하는 합성형(slot) 컴포넌트. 실제로 반복되는 스타일 3덩어리(껍데기·뒤로버튼·탭버튼 활성/비활성)만 컴포넌트로 갖고, 조립(어떤 탭을 몇 개 나열할지)은 호출부(`App.jsx`·`ExploreStage.jsx`)에 남긴다 — config로 일반화하면 "config를 해석하는 분기"가 되살아난다는 판단(파일 주석 근거).
- **훅 수명 ≠ 호출 위치**(`useExploreJourney`) — 코드는 훅으로 캡슐화해도, 그 상태가 살아남아야 하는 화면 전환(족보 탭 진입)에서 컴포넌트가 언마운트되면 훅째로 상태가 사라진다. 그래서 호출은 반드시 상위(App)에서 하고 하위(ExploreStage)는 결과만 prop으로 받는다.
- **절 검색 공용 헬퍼**(`verse_search.search_verses`) — `/search`와 `/words/{book}/verses`가 같은 substring 스캔·`ref` 포맷팅을 재사용, 질의 단위 `lru_cache(256)`로 반복 질의를 흡수.
- **개인화 localStorage 계층**(`useBookmarks`·`useReadingProgress`) — 서버 쓰기 경로 없이 이 기기에만 남는 저장(북마크·이어보기·읽기 진도). 스키마 버전 필드 + 파손/구버전 시 마이그레이션 없이 빈 값 폴백이 공통 관행.
- **정적 드리프트 게이트**(`validate_era_bands_consistency`·`validate_intro_menu_parity`·`validate_scene_coverage`·`validate_curated_persons`·`validate_intro_gutter`·`validate_intro_entry_route`·`validate_scene_sketch_detail`·`validate_api_cache_headers`·`validate_canon_pipeline`) — 수동 복제된 상수·UI 목록·판정 지점이 배포 게이트에서 정규식/AST로 소스를 직접 스크래핑해 대조하는 패턴. 앱을 실행하지 않고 소스만 읽는다("게이트는 판정자이지 작성자가 아니다"). task#280~281부터는 대상이 "값의 복제"만이 아니라 "판정 지점의 유일성"(무타깃 판정이 정본 밖에 0곳)이나 "국소 스타일 규약 준수"(비트 프레임이 `boxSizing`을 선언)로도 넓어졌다 — 불변식은 알려진 위반 목록이 아니라 결함 클래스를 진술해야 한다는 원칙(ADR 260821-000937). 각 검증기는 `--selftest`로 자기 자신에 고의 결함을 주입해 실제로 FAIL하는지 대조군을 돌린다.
- **오라클 재사용 게이트**(`validate_event_verses`·`validate_sortkey_startdate`) — "값이 같다"가 아니라 "베이킹된 verseID 집합 == rangeLabel 범위 ∩ 정본 절 사전"처럼 **경계**로 불변식을 진술한다(ADR 260821-000937). 자체 파서를 새로 만들지 않고 생성기의 파서(`generate_person_event_verses.expand_range_label`)를 import해 재사용한다(파서 2벌 금지, ADR 260819-205242) — 오라클도 저장소 안 정본 파일(`data/bible/verses.json`, ADR 260821-125000)이라 네트워크·Neo4j 없이 항상 돈다.

## 진입점

- 백엔드 앱: `backend/app/main.py`의 `app`. 컨테이너 CMD는 `uvicorn app.main:app --host 0.0.0.0 --port 8000`(`backend/Dockerfile`). 로컬은 `python3 -m uvicorn backend.app.main:app --reload`(:8000).
- 프론트 앱: `frontend/src/main.jsx` → `frontend/src/App.jsx`. 로컬 개발 서버는 `cd frontend && npm run dev`(:5173).
- 데이터 적재: `backend/scripts/load_theographic.py`(원본) → `load_authored_*`/`load_books`/`load_person_events`/`load_verse_events`(저작) → `inject_*`. 전부 호스트에서 실행하며 `python3 -m backend.scripts.<name>`으로도 부를 수 있다(`backend/scripts/__init__.py` 존재).
- 개발 전용 화면: `#/cast`(설정화 시트 — `frontend/src/CastSheet.jsx`, 사용자 화면 어디에도 링크가 없다).
- 검증 게이트: `scripts/check.sh`(단독 실행 가능).
- 저작 파이프라인(레포 밖 venv `~/.local/biblemap-imggen/.venv314/bin/python3`으로 실행): 생성 `scripts/canon/gen_scripture_scene.py --seeds 11 --label vNN` → 판정 `scripts/canon/judge_scene.py vNN`(다섯 축 통과 시 0). 프롬프트 연습대는 `scripts/canon/try_prompt.py`(`--check`는 GPU 0), 파라미터 정본은 `scripts/canon/params.py`, 시작점 문서는 `scripts/canon/notes/PROMPTING.md`·`notes/SCENE-1SAM17.md`.
- 저작자용 시각 피드백: `python3 scripts/render_scene.py <SceneName> [--at ms] [--cast]`(빌드→렌더→촬영).
- 배포: `deploy.sh`(러너가 호출), `.github/workflows/deploy.yml`.
