---
last_mapped_commit: 70f5fc64daa7b3c71f2773a4357ad68bba9ae7a5
mapped: 2026-07-24
---

# ARCHITECTURE

## 전체 패턴

세 계층 단방향 읽기 파이프라인이다.

```
Neo4j 그래프(진리의 원천)  ──►  FastAPI 읽기 전용 API  ──►  React SPA(단일 페이지, 해시 라우팅)
        ▲                              ▲
   빌드타임 로더/주입 스크립트      런타임 오버레이(data/*.json, lru_cache)
   (backend/scripts/*)              (backend/app/overlays.py)
```

- 그래프는 **빌드타임에** 로더 스크립트(`backend/scripts/load_*.py`·`inject_*.py`)로 채워지고, 앱은 런타임에 이를 **읽기만** 한다. API 라우트는 전부 `@router.get` — 쓰기 엔드포인트가 없다(`backend/app/main.py:49` `allow_methods=["GET"]`).
- 그래프 노드로 승격하지 않는 콘텐츠(사건 근거 구절, 언약, 메시아 예언, 비유·기적, 주제 성구, 절 본문 등)는 `data/` 아래 JSON **오버레이**로 두고 `backend/app/overlays.py`가 `functools.lru_cache`로 1회 로드해 그래프 쿼리 결과와 합성한다.
- 프론트는 라우팅 라이브러리 없이 **스테이지(Stage) 상태 머신 + 해시 딥링크**로 화면을 전환한다(`frontend/src/useStageNavigation.js`·`frontend/src/urlState.js`).

## 계층 상세

### 1. Neo4j 그래프 — 진리의 원천

- 접속은 `backend/app/db.py`의 `get_driver()` 싱글턴(`GraphDatabase.driver`, `NEO4J_URI`/`NEO4J_USER`/`NEO4J_PASSWORD` 환경변수). 비밀번호 미설정 시 기동하지 않고 `RuntimeError`.
- 노드 라벨: `Person`, `Place`, `Event`, `PeopleGroup`, `Book`. 각 노드의 안정 식별자는 `theographic_id` 프로퍼티.
- 앱 기동 시(`backend/app/main.py:26` `lifespan`) 각 라벨에 `theographic_id` 인덱스를 `CREATE INDEX ... IF NOT EXISTS`로 보장한다(실패해도 계속 진행).
- 그래프 적재는 두 소스가 합쳐진다:
  - **theographic 원본**: `backend/scripts/load_theographic.py`가 GitHub(`robertrouse/theographic-bible-metadata`)의 people/places/events/peopleGroups JSON을 내려받아 노드·관계로 적재. `status=publish`만 적재하되, 가족 폐포(closure) 알고리즘으로 `wip` 인물도 가족 간선 완전성 위해 시드에서 도달 가능하면 포함(ADR-0021/0022).
  - **저작(authored) 레이어**: `load_authored_events.py`·`load_authored_persons.py`·`load_authored_genealogy.py`·`load_authored_mothers.py`·`load_books.py`·`load_person_events.py`·`load_verse_events.py`가 `data/authored_*`·`data/person_events`·`data/verse_events`의 큐레이션 데이터를 멱등 적재.
- 적재 후 **주입(inject) 스크립트**가 노드에 프로퍼티를 SET한다: `inject_ko_names.py`(한글 이름), `inject_date_corrections.py`(Ussher 연대 → 보수 연대 교정, ADR-0014), `inject_book_context.py`·`inject_person_context.py`·`inject_person_traits.py`·`inject_place_context.py`. **`load_theographic.py` 재적재 시 inject를 반드시 재실행**해야 한다(README).

### 2. FastAPI 읽기 API

- 진입점 `backend/app/main.py` — `_configure_logging()`를 라우터 import 전에 1회 호출, `lifespan`으로 인덱스 준비, CORS는 전 오리진 GET 허용. 라우터를 `app.include_router()`로 등록.
- 라우터 모듈: `backend/app/routes/` 아래 `nodes`·`events`·`search`·`books`·`persons`·`journey`·`places`·`tours`·`family`·`words`·`verses`·`reliance`·`stats`.
- 집계·전역 응답 라우트는 대부분 함수 단위 `@functools.lru_cache(maxsize=1)`로 결과를 앱 재시작 전까지 메모리에 보관한다(예: `events.py:_compute_events`, `stats.py:_compute_stats`, `tours.py:_list_tours`). 응답은 `Cache-Control: max-age=300`(집계) 또는 브라우저 캐시.
- 핵심 엔드포인트:
  - `GET /node/{id}`(`nodes.py`) — SidePanel의 범용 노드 상세. 노드 프로퍼티 + 이웃(무방향, 가족 상호쌍 `PARENT_OF`/`CHILD_OF` 정규화·디듀프 후 `NODE_NEIGHBOR_LIMIT` 절단) + `total`. Book이면 top_persons/top_events 추가.
  - `GET /events`(`events.py`) — 타임라인 사건 목록. 그래프 `CONTAINS_BOOK` + `book_events` 오버레이 역방향 인덱스를 머지해 각 사건에 근거 성경권을 정경순(`bookOrder`)으로 첨부.
  - `GET /person/{id}/journey`(`journey.py`)·`GET /tour/{id}`(`tours.py`) — 여정/투어 정차지(장소 좌표는 Neo4j `Place`의 longitude/latitude 배치 조회).
  - `GET /search`·`GET /person/{id}/relations`·`GET /person/{id}/family`·`GET /person/{id}/reliance`·`GET /reliance/ranking`·`GET /words/{book}`·`GET /verse/{id}/persons`·`GET /books-overview`·`GET /keypeople-cards`·`GET /persons/curated` 등.

### 3. 런타임 오버레이 vs 그래프 노드

**핵심 패턴** — `backend/app/overlays.py`:

- `_resolve(subpath)`/`_resolve_dir(subpath)`가 두 베이스(`os.environ["DATA_DIR"]` 기본 `/app/data`, 그리고 리포지토리 `data/`인 `_REPO_DATA_DIR`)를 순서대로 탐색해 첫 존재 경로를 반환. 없으면 경고 로그 후 `None`(빈 데이터 폴백).
- `_load(subpath)`는 파일을 읽어 dict 반환, 파싱 실패 시 `{}` 폴백.
- 각 오버레이는 인자 없는 함수 + `@functools.lru_cache(maxsize=1)` — **1회 로드 후 프로세스 재시작 전까지 캐시**. 따라서 `data/` 변경 후에는 API 컨테이너 재시작이 필요하다(`docker compose restart api`).
- 오버레이 함수 → 데이터 파일 매핑:
  - `book_events_raw()` → `book_events/books.json`
  - `event_verses()` → `event_verses/events.json`
  - `bible_verses()` → `bible/verses.json`(정본 절 사전 `verseID → {textKo, textEn}`)
  - `word_distribution()` → `word_distribution.json`
  - `books_ko()` → `names_ko/books.json`
  - `chapter_summaries()` → `chapter_summaries/books.json`
  - `chapter_sections()` → `chapter_sections/books.json`
  - `quotations()` → `quotations/quotations.json`(`.get("quotations", [])`)
  - `messianic_prophecies()` → `messianic_prophecies/prophecies.json`
  - `covenants()` → `covenants/covenants.json`
  - `parables_miracles()` → `jesus_parables_miracles/index.json`
  - `place_coords()` → `place_coords/places.json`(리스트면 `id` 키 dict로 변환)
  - `topical_verses()` → `topical_verses/topics.json`
  - `verse_persons()` → `verse_persons/index.json`
- `overlays.curated_person_id(events)`는 큐레이션 신원 규약의 단일 지점(`person_events/<slug>.json`의 `events[0].participants[0]` = 그 인물의 `theographic_id`). `persons.py`·`places.py`·`reliance.py`가 소비.
- **합성 규칙**: 오버레이 JSON은 대개 `verseID` 참조만 보유하고, 절 본문(textKo/textEn)은 라우트에서 `overlays.bible_verses()`로 해석해 동봉한다. `events.py`의 `/covenants`·`/messianic-prophecies`·`/topical-verses`·`/parables-miracles`·`/event/{id}/verses`가 모두 이 패턴. `/parables-miracles`는 추가로 `placeId`를 `place_coords`에서 lat/lng으로 해석(없으면 항목 자체 lat/lng).

이 세션(미커밋 워킹트리)에서 추가된 오버레이 기반 기능:

| 오버레이 함수 | 라우트(`events.py`) | 데이터 파일 |
|---|---|---|
| `covenants()` | `GET /covenants` | `covenants/covenants.json` |
| `messianic_prophecies()` | `GET /messianic-prophecies` | `messianic_prophecies/prophecies.json` |
| `parables_miracles()` + `place_coords()` | `GET /parables-miracles` | `jesus_parables_miracles/index.json` + `place_coords/places.json` |
| `topical_verses()` | `GET /topical-verses` | `topical_verses/topics.json` |

- `GET /stats`(`backend/app/routes/stats.py`)는 오버레이가 아니라 **그래프 집계** 라우트(`_compute_stats` lru_cache): 헤드라인 총계(`_fetch_totals`)·최다 등장 인물(`_fetch_top_persons`, `HAS_PARTICIPANT`, `God` 제외)·최장 여정(`_compute_longest_journeys`)·시대별 사건 분포(`_fetch_era_distribution`)·책별 장 수(`_fetch_books`). `stats.py`의 `ERA_BANDS`는 `frontend/src/TimelineView.jsx`의 `ERA_BANDS`와 수동 복제 관계(경계 변경 시 함께 갱신 주석).

### 4. React SPA 스테이지 머신

- 엔트리 `frontend/src/main.jsx` → `frontend/src/App.jsx`(`StrictMode`). 라이트 테마는 렌더 전 동기 반영(ADR-0020, `localStorage['biblemap-theme']`).
- **단일 상태 머신** `frontend/src/useStageNavigation.js`가 `activeStage`를 관리. 스테이지 값:
  `intro` · `hub` · `overview` · `book` · `family` · `words` · `reader` · `stats` · `topics` · `tours` · `explore`.
- 무해시 첫 진입 + `localStorage['biblemap-intro'] !== 'off'`이면 초기 스테이지가 `intro`(그 외 `hub`).
- 스테이지 대상 id는 `selectedNode`(SidePanel 선택)와 **분리된** 전용 state로 보관 — `bookId`·`familyId`·`wordsBookId`·`readerBookId`/`readerChapter`·`explorePersonId`·`exploreTourId`. 페이지 안에서 노드를 클릭해 시트를 띄워도 페이지 대상·URL이 흔들리지 않게 하기 위함.
- `explore` 스테이지 내부 서브뷰 `exploreView`: `map` · `timeline` · `relations` · `intro` · `reliance`. 인물 모드는 소개/여정/연표/관계/의존 탭 + 족보 전용 스테이지, 투어 모드는 개요/여정/연표.
- 인물 vs 투어는 상호배타(`explorePersonId`↔`exploreTourId` 하나가 세팅되면 다른 하나 null).
- `App.jsx`가 스테이지별 내비 바(`renderOverviewNav`·`renderBookNav`·`renderReaderNav`·`renderFamilyNav`·`renderWordsNav`·`renderStatsNav`·`renderTopicsNav`·`renderToursNav`·`renderExploreNav`)와 스테이지 본문(`activeStage === '...' && <View/>`)을 조건 렌더. 전역 헤더는 `frontend/src/SpineHeader.jsx`(책등 리본 3부 + 테마 토글, ADR-0026).
- 뷰 컴포넌트: `IntroView`·`PersonHub`·`BibleOverviewView`·`SidePanel`+`ChapterReader`·`FamilyTree`·`WordDistributionView`·`StatsView`·`TopicalVersesView`·`TourList`·`MapView`·`TimelineView`·`RelationsView`·`RelianceView`·`PersonIntro`·`TourIntro`·`JourneyList`·`TourPlayback`.
- 노드 선택 원시값은 `frontend/src/useNodeSelection.js`(selectedNode·history·goBack 등)에서 나와 `useStageNavigation`에 주입된다. `useStageNavigation`이 `lucide-react`의 `Map`을 import하지 않고 history 배열을 구조분해하지 않는 것은 전역 `Map`/`history` 섀도잉 크래시를 구조적으로 막기 위함(파일 주석).
- 개요(overview) 서브 내비 탭(`App.jsx:renderOverviewNav`): 책 둘러보기 · 단어 분포(`openWords('all')`) · 통계(`openStats`) · 주제 성구(`openTopics`) — 이 세션에서 통계·주제 성구 탭이 추가됨.

### 5. 해시 딥링크

- 라우팅 라이브러리 없이 `frontend/src/urlState.js`의 `encodeHash`/`parseHash`가 스테이지 상태 ↔ 해시 문자열을 순수 매핑(ADR-0009).
- 해시 스킴:
  - `#/`(허브) · `#/intro` · `#/books`(개요) · `#/tours` · `#/stats` · `#/topics`
  - `#/book/<theographic_id>` · `#/read/<id>`(장 그리드)·`#/read/<id>/<n>`(장 본문)
  - `#/family/<id>` · `#/words/<id>`
  - `#/person/<slug>`(+ `/timeline`·`/relations`·`/intro`·`/reliance`)
  - `#/tour/<slug>`(+ `/timeline`)
- `#/stats`·`#/topics`는 이 세션에서 추가됨(`urlState.js` encodeHash `:19-20`, parseHash `:43-44`).
- 히스토리 통합(ADR-0010): `useStageNavigation`의 sync effect가 스테이지/인물/시트 변경을 `pushState`, 뷰 토글·드릴다운·베이스는 `replaceState`로 미러. `popstate`는 `event.state`에서 복원(`popstateGuard`로 재-push 방지). 노드 id는 URL이 아닌 `history.state.node`에만 보관.
- 마운트 시 해시를 1회 파싱해 복원(`restoredRef`), person slug는 `/persons/curated`(slug↔id 맵) 준비 후 해석. 복원 완료 신호는 state(`restored`)로 sync effect 트리거.

### 6. 절 레이어(Verse Layer)

- `frontend/src/VerseLayer.jsx` — "양피지 구절 모달" 공통 쉘(task#202). 반응형: ≤768px(`MOBILE_BREAKPOINT`)는 하단 시트(드래그 닫기 80px 임계), >768px는 중앙 모달. `createPortal`로 `document.body`에 렌더, 헤더(제목·한/영 탭·×)는 고정, 본문(`children`)만 스크롤.
- 언어 탭은 `frontend/src/VerseLangTabs.jsx`, 표시 언어 `verseLang`('ko'|'en')는 `App.jsx`가 소유해 타임라인·SidePanel·주제 성구·언약 레이어가 공유.
- 소비처: `TimelineView`(언약 상세·비유/기적 상세), `BibleOverviewView`(메시아 예언→성취), `TopicalVersesView`(주제 성구), SidePanel 인용 대조 등. `paperTextStyle`·`VerseBookTabs`는 이 모듈에서 export.

### 7. 심볼 시스템

- 인물 인장 `frontend/src/personSymbols.jsx` — 키는 인물 `slug`, 미등록이면 범용 폴백(`FALLBACK`). `hasSymbol(slug)`로 등록 여부 판정(가계도 앵커용). `PersonSymbol` 컴포넌트가 `draw` prop으로 1회 stroke 애니메이션.
- 책 상징 `frontend/src/bookSymbols.jsx` — 키는 책 `theographic_id`(책은 slug 없음), `BookSymbol` 컴포넌트.
- 타입 팔레트 `frontend/src/theme.js` — `TYPE_COLOR`/`TYPE_KO`/`TYPE_ORDER`(값의 정본은 `index.css`의 `--type-*`, 테마별). `PM_TYPE_COLOR = { parable, miracle }`는 리터럴 hex(maplibre paint가 CSS var 불가라 `TimelineView`·`mapLayers.js`가 공유). `GENRE_META`(장르 표시명·설명)·`VALENCE_COLOR`도 여기.

### 8. 투어(Tours)

- 정의 파일 `data/tours/<id>.json`(`{id, title, subtitle, era, description, stops:[{id, note}]}`). ADR-0011: 투어는 event-reference 오버레이 — Neo4j 노드 추가 없음. ADR-0028: stops는 객체 배열, `note`는 그 투어 관점의 정차지 해설.
- `backend/app/routes/tours.py` — `GET /tours`(목록, `_list_tours`, 시대순 정렬)·`GET /tour/{id}`(상세, `person_events/*.json`을 `_build_event_index`로 스캔해 stop id → event-body 해석 후 sortKey 정렬, Neo4j에서 좌표 조회). 미존재 투어는 404가 아니라 빈 stops(soft-empty).
- 프론트 자동재생: `frontend/src/TourPlayback.jsx`(`useTourPlayback` 시퀀서)·`App.jsx`가 카메라 동기(`playback.idx` → `journeyStopGroups`). 정차지 장면 삽화는 `frontend/src/tourSketches.jsx`가 `frontend/src/sketches/*.jsx` 모듈 레지스트리(`SCENES`, `hasSketch(eventId)`)를 집계해 렌더.

### 9. 지도 레이어(MapView / mapLayers)

- `frontend/src/MapView.jsx`가 maplibre-gl 지도를 소유, `frontend/src/mapLayers.js`의 `setupMapSources(map)`·`registerEventHandlers(map, ...)`가 소스/레이어/클릭 핸들러를 배선. GeoJSON 변환은 `frontend/src/mapGeo.js`(`placesToGeoJSON`·`buildJourneyLineGeoJSON`·`buildJourneyStopsGeoJSON`·`journeyStopGroups`·`buildParablesMiraclesGeoJSON` 등). 링(사건 마커) 애니메이션은 `frontend/src/mapRingController.js`.
- 레이어: 여정선(`journey-line`+화살표)·정차지 배지(`journey-stop-*`)·활성 강조(`journey-active-*`)·장소(`places-*` 클러스터/스파이더)·사건 링(`event-ring-*`).
- 비유·기적 레이어(`pm-source`/`pm-circle`)는 이 세션 추가(task#249) — 기본 `visibility:none`. `MapView`가 `/parables-miracles`를 1회 fetch(`pmItems`)하고 토글(`pmVisible`)·종류 필터(`pmFilter`: all|parable|miracle)로 `setLayoutProperty`/`setFilter`만 갱신. 팝업은 `pmPopupRef`(장소 팝업 `popupRef`와 분리).

## 데이터 흐름(엔드투엔드)

### 빌드타임(그래프·오버레이 준비)

1. `docker compose up -d`로 Neo4j 기동.
2. `python3 backend/scripts/load_theographic.py` — 원본 그래프 적재.
3. `python3 backend/scripts/inject_ko_names.py`, `inject_date_corrections.py`(및 기타 저작 로더/inject) — 프로퍼티 SET·저작 레이어 병합.
4. 오버레이 JSON은 `generate_*.py`/`build_*.py`로 산출(예: `generate_bible_text.py` → `bible/verses.json`, `build_word_distribution.py` → `word_distribution.json`, `generate_event_verses.py` → `event_verses/events.json`, `build_verse_persons.py` → `verse_persons/index.json`). `covenants`·`messianic_prophecies`·`topical_verses`·`jesus_parables_miracles`·`place_coords`는 `data/` 아래 정본 JSON.

### 런타임(요청)

1. 브라우저가 해시 URL 진입 → `useStageNavigation`이 `parseHash`로 스테이지 복원.
2. 뷰 컴포넌트가 `frontend/src/api.js`의 `apiGet(path)`로 fetch. 프로덕션은 `VITE_API_URL=/api`(빌드타임 주입)로 nginx 프록시(`/api` → `api:8000`)를 탄다. 모든 요청에 `?v=<BUILD_ID>`(빌드마다 갱신, `vite.config.js`의 `define.__BUILD_ID__ = Date.now()`)를 붙여 배포 직후 옛 응답 캐시 재사용을 막는다.
3. FastAPI 라우트가 `get_driver()`로 그래프 쿼리 + `overlays.*()`(lru_cache) 오버레이를 합성해 JSON 반환.
4. 프론트가 결과를 렌더. 절 본문 드릴다운은 `VerseLayer` 양피지 모달로.

### 배포

- `push → main` → GitHub Actions `self-hosted` 러너(`.github/workflows/deploy.yml`)가 `git reset --hard origin/main` 후 `deploy.sh` 실행.
- `deploy.sh`: 프론트 `npm run build`(→ `frontend/dist`) → `docker compose -p biblemap build api` → `up -d api nginx` → `inject_ko_names.py`(Neo4j 준비 대기 재시도). **`deploy.sh`는 `load_*`/기타 inject를 실행하지 않는다** — 데이터 재적재는 수동.
- `docker-compose.yml` 서비스: `neo4j`(볼륨 `neo4j_data`, 127.0.0.1 바인딩), `api`(`./data:/app/data` 마운트 → 오버레이가 이 경로를 읽음, `DATA_DIR` 기본 `/app/data`), `nginx`(`./frontend/dist` + `nginx/nginx.conf` 마운트, 8080 노출).
- 프론트 :8080은 `frontend/dist` 마운트(HMR 아님) — 로컬 검증 전 `cd frontend && npm run build` 필요.

## 핵심 추상화

- **오버레이 로더**(`overlays._load` + `lru_cache`) — 그래프에 없는 콘텐츠를 JSON으로 관리, verseID 참조를 `bible_verses()`로 본문 합성.
- **스테이지 머신**(`useStageNavigation`) — 대상 id를 `selectedNode`와 분리해 페이지 안정성 확보, sync effect가 URL/히스토리 미러.
- **해시 코덱**(`urlState.encodeHash`/`parseHash`) — 라우터 없는 순수 문자열 매핑.
- **양피지 절 레이어**(`VerseLayer`) — 반응형 구절 모달 공통 쉘, 다수 뷰 재사용.
- **공유 API 클라이언트**(`api.apiGet`) — 단일 베이스 URL + 캐시 버스팅.
- **큐레이션 신원 규약**(`overlays.curated_person_id`, `person_events/<slug>.json`의 `events[0].participants[0]`) — id↔slug 해석의 단일 출처.

## 진입점

- 백엔드 앱: `backend/app/main.py`(`app` = FastAPI). 컨테이너 CMD: `uvicorn app.main:app`(`backend/Dockerfile`).
- 프론트 앱: `frontend/src/main.jsx` → `frontend/src/App.jsx`.
- 데이터 적재 진입: `backend/scripts/load_theographic.py`(원본) 이후 inject 스크립트들.
- 배포 진입: `deploy.sh`(러너가 호출), `.github/workflows/deploy.yml`.
- 로컬 개발: 백엔드 `python3 -m uvicorn backend.app.main:app --reload`(:8000), 프론트 `npm run dev`(:5173).
