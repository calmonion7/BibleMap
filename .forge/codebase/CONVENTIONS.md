---
last_mapped_commit: 43f987cb37c2341c3cfeb54e4cf4dc33b4549c64
mapped: 2026-08-01
---

# CONVENTIONS

BibleMap의 코드 스타일·규약 정본. 라우팅/데이터 흐름의 **구조**는 `ARCHITECTURE.md`·`STRUCTURE.md`, 검증·테스트는 `TESTING.md` 소관이며, 도메인 용어 정의는 `CONTEXT.md` 소관이다. 여기는 **어떻게 쓰는가**(네이밍·로깅·에러·상태·저작 규칙·스타일 토큰·린트)만 다룬다.

---

## 1. 로깅 방출 규약

> 이 절은 프로젝트 `CLAUDE.md`가 이름으로 참조한다 — **절 이름을 바꾸지 말 것**(번호는 재매핑마다 밀릴 수 있음).

### 1.1 백엔드 — 모듈 logger 통일 + `[Component]` prefix

- 모듈마다 `logger = logging.getLogger(__name__)`. **`backend/app/` 안에서 `print()`·root 로거 직호출 금지**(현재 위반 0 — `grep -rn "print(" backend/app/`가 비어 있다). `print`는 `backend/scripts/`에서만 쓴다(§7.3).
- 로거를 선언한 모듈(커밋 `43f987c` 기준): `backend/app/overlays.py`·`backend/app/main.py`·`backend/app/routes/persons.py`·`places.py`·`tours.py`·`nodes.py`·`family.py`·`verses.py`·`stats.py`. 경고할 실패 케이스가 없는 라우터(`books.py`·`events.py`·`journey.py`·`reliance.py`·`search.py`·`words.py`)는 로거를 선언하지 않는 것도 관례 허용 범위다 — 반대로 `verses.py`·`stats.py`처럼 선언만 해두고 방출 지점이 없는 형태도 허용된다.
- 메시지는 `[Component]` prefix로 시작한다: `[Overlays]`·`[Startup]`(`main.py` lifespan)·`[Persons]`·`[Places]`·`[Tours]`·`[Nodes]`. 새 라우터를 추가하면 파일 상단에서 prefix를 하나 정하고 그 파일 전체에서 일관되게 쓴다.
- 빈값 폴백(오버레이 파일/디렉터리 없음, JSON 파싱 실패, `participants` 비어 있음)은 `logger.warning`, 기동 예외는 `logger.exception`, 정상 기동 완료는 `logger.info`. 포맷은 **lazy `%s` 스타일**이며 f-string을 넣지 않는다. 실측:
  - `backend/app/overlays.py:20` — `logger.warning("[Overlays] 오버레이 파일 없음 — 빈 데이터로 폴백 (%s, 시도: %s)", subpath, bases)`
  - `backend/app/routes/nodes.py:291` — `logger.warning("[Nodes] Person traits 파싱 실패 — 빈 목록 폴백 (%s): %s", node_id, e)`
  - `backend/app/routes/tours.py:43` — `logger.warning("[Tours] 투어 파일 로드 실패 — 목록에서 건너뜀 (%s): %s", os.path.basename(path), e)`
  - `backend/app/main.py:38` — `logger.exception("[Startup] Neo4j 인덱스 생성 실패 — 인덱스 없이 계속 진행")`
- `backend/app/main.py`의 `_configure_logging()`이 **라우터 import 전**(모듈 최상단, `from .routes import ...` 이전 줄 19)에 1회 호출된다: `logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")`, 수다스러운 서드파티(`neo4j`·`urllib3`·`asyncio`)는 `setLevel(logging.WARNING)`, `uvicorn`·`uvicorn.access`는 `propagate = False`로 root 중복 emit 차단. **`uvicorn.error`는 제외** — 자체 핸들러 없이 부모로 전파해 출력하므로 propagate를 끊으면 기동/에러 라인이 통째로 사라진다(코드 주석에 이유 명시).

### 1.2 프론트 — 빈값 폴백 catch는 `console.warn` + `[Component]` prefix

- 비치명적 로드 실패(fetch 실패, 하위 리소스 없음)는 조용히 폴백하고 `.catch(e => ...)` 안에서 **`console.warn`으로만** 기록한다. `console.error`는 실제 프로그래밍 오류 1건에만 쓰인다 — `frontend/src/TimelineView.jsx:43`의 `console.error('TimelineView: personFilter must be a Set, got', personFilter)` 방어 로그.
- 메시지는 `[Component]` prefix로 시작한다. 실측 컴포넌트: `[App]`·`[Timeline]`·`[MapView]`·`[SidePanel]`·`[Stats]`·`[TopicalVerses]`·`[BibleOverview]`·`[ChapterReader]`·`[PersonIntro]`·`[PersonMiniCard]`·`[FamilyTree]`·`[Relations]`·`[Reliance]`·`[WordDistribution]`·`[JourneyList]`.
- 예외(prefix 없음, 잔존 2건): `frontend/src/useStageNavigation.js:70`(`/persons/curated 로드 실패 — 여정 탐험 CTA 미노출`)·`:84`(`/keypeople-cards 로드 실패 — keyPeople 칩 미노출`). 새 코드는 prefix를 갖추되 이 두 줄은 발견 시 별건으로만 고친다.
- 취소 판정은 두 관용구가 공존한다 — `if (e?.name !== 'AbortError')`(`AbortController` 기반: `MapView.jsx`·`ChapterReader.jsx`·`FamilyTree.jsx`·`PersonMiniCard.jsx`·`RelianceView.jsx`·`WordDistributionView.jsx`·`App.jsx`의 여정 fetch)와 `if (!cancelled)`(`let cancelled = false` 클로저 가드: `App.jsx`·`PersonIntro.jsx`·`RelationsView.jsx`·`SidePanel.jsx`·`StatsView.jsx`·`TopicalVersesView.jsx`·`BibleOverviewView.jsx`). 어느 쪽이든 **취소된 요청의 실패는 경고하지 않는다**. `frontend/src/api.js` 상단 주석이 계약을 명시: "요청 취소(AbortError)는 fetch에서 그대로 전파 — 호출부가 `e.name === 'AbortError'`로 구분한다."
- 열려 있는 항목에만 반영해야 하는 fetch는 ref 가드로 늦은 응답을 버린다: `if (openEventRef.current === ev.id) { ... }`(`TimelineView.jsx:177`·`JourneyList.jsx:56`·`SidePanel.jsx:260`).

---

## 2. 네이밍·모듈 구조

### 2.1 백엔드 Python (`backend/app/`)

- 파일·함수·변수 snake_case. 모듈 내부 전용은 `_` 접두(`_resolve`·`_load`·`_build_list`·`_era_of`·`_book_bb`·`_fetch_totals`). 상수는 대문자(`ERA_BANDS`·`TOP_PERSONS_LIMIT`·`_ERA_ORDER` — 사설 상수는 `_` + 대문자 혼용).
- 라우터 파일은 도메인 단수/복수 명사(`persons.py`·`places.py`·`books.py`·`events.py`·`tours.py`·`words.py`·`verses.py`·`family.py`·`journey.py`·`reliance.py`·`search.py`·`stats.py`·`nodes.py`). 각 파일은 `router = APIRouter()` 하나만 두고 **prefix 없이** 전체 경로를 데코레이터에 적는다(`@router.get("/person/{node_id}/relations")`). 등록은 `backend/app/main.py`의 `app.include_router(...)` 나열.
- 경로 파라미터는 snake_case(`{node_id}`·`{book_id}`·`{event_id}`·`{verse_id}`·`{person_id}`·`{tour_id}`), URL 세그먼트는 kebab-case(`/books-overview`·`/keypeople-cards`·`/messianic-prophecies`·`/topical-verses`·`/parables-miracles`·`/person/{id}/event-ids`).
- **응답 JSON 키는 camelCase**(`nameKo`·`bookOrder`·`keyVerseTextKo`·`eventIds`·`startDate`) — Python 내부 snake_case와 경계에서 갈린다.
- 모듈·함수 docstring은 **한글**이며 첫 줄에 목적, 필요하면 `(task#NNN)`·`ADR-00NN` 근거를 단다(`backend/app/routes/stats.py` 상단이 대표).

### 2.2 프론트 React/JSX (`frontend/src/`)

- **컴포넌트 파일 = PascalCase `.jsx`**, 파일명과 default export 컴포넌트명을 맞춘다(`MapView.jsx`·`SidePanel.jsx`·`TimelineView.jsx`·`ChapterReader.jsx`·`StatsView.jsx`·`TopicalVersesView.jsx`). 예외: `TourPlayback.jsx`가 `TourPlaybackCard`를 default export.
- **훅 파일 = `use*.js`**, named export(`useNodeSelection.js`·`useStageNavigation.js`·`useTourPlayback.js`).
- **순수 헬퍼/데이터 모듈 = camelCase `.js`**(`api.js`·`theme.js`·`urlState.js`·`dates.js`·`constants.js`·`mapGeo.js`·`mapLayers.js`·`mapRingController.js`·`scrollMemory.js`). SVG를 반환하는 저작 모듈만 `.jsx`(`personSymbols.jsx`·`bookSymbols.jsx`·`tourSketches.jsx`·`sketches/*.jsx`).
- **컴포넌트 파일에서 비-컴포넌트 상수를 export하지 않는다**(`react-refresh/only-export-components`, §8). 공유 상수는 전용 모듈로 옮긴다 — `GENRE_META`는 `BibleOverviewView.jsx`에서 `theme.js`로 이동했고(주석이 이유 명시), 장면 이름표 컴포넌트 `Label`은 순수 헬퍼 `sketches/lib.jsx`에서 `sketches/SceneLabel.jsx`로 분리됐다(task#253). 불가피한 2건만 `// eslint-disable-next-line react-refresh/only-export-components`(`VerseLayer.jsx:21`·`personSymbols.jsx:488`).
- 주석은 한글이며 "왜"를 적는다 — 특히 과거 버그의 재발 방지 근거(`useNodeSelection.js`의 `useCallback([])` 참조 안정화 주석, `scrollMemory.js`의 전역 `Map` 섀도잉 회피 주석).

### 2.3 데이터 JSON (`data/`)

- **도메인 디렉터리 1개 = 정본 파일 1개** 관례: `data/<도메인>/<집합명>.json`. 집합명은 담긴 대상의 복수형 — `books.json`(`book_events`·`book_context`·`chapter_summaries`·`chapter_sections`·`names_ko`·`book_years_approx`), `people.json`(`character_traits`·`person_context`·`keypeople_verses`·`authored_persons`), `events.json`(`event_verses`·`authored_events`·`date_corrections`), `places.json`(`place_coords`), `verses.json`(`bible`), `topics.json`(`topical_verses`), `prophecies.json`(`messianic_prophecies`), `covenants.json`, `quotations.json`, `identity.json`(`keypeople`), `index.json`(`jesus_parables_miracles`·`word_verse_index`·`verse_persons`).
- **인물/투어 단위 저작만 파일 분할**: `data/person_events/<slug>.json`·`data/god_reliance/<slug>.json`·`data/tours/<slug>.json`. slug는 kebab-case 또는 snake_case가 혼재한다(`david-united-kingdom.json` vs `john_the_baptist.json`) — 기존 디렉터리 관례를 따른다.
- **키는 camelCase가 현행 표준**(`verseIds`·`keyVerseIds`·`otVerseIds`/`ntVerseIds`·`otRangeLabel`·`startDate`·`sortKey`·`nameKo`·`placeId`·`approxYear`·`oldStartDate`/`newStartDate`). 초기 도메인 일부만 snake_case가 잔존한다(`data/character_traits/people.json`의 `verse_ref`·`verse_textKo`·`verse_textEn`) — 그 도메인 안에서는 기존 키를 유지하고, 새 도메인은 camelCase로 만든다.
- 최상위는 도메인 이름의 래퍼 객체 아니면 리스트다: `{"covenants": [...]}`·`{"prophecies": [...]}`·`{"topics": [...]}`·`{"items": [...]}`·`{"quotations": [...]}` vs `data/date_corrections/*.json`·`data/person_events/*.json`(리스트). 오버레이 로더(`backend/app/overlays.py`)가 이 차이를 흡수한다(`quotations()`는 `.get("quotations", [])`로 리스트 반환, `place_coords()`는 리스트를 `id` 키 dict로 정규화).

### 2.4 스크립트 (`backend/scripts/`, `scripts/`)

- 접두사가 역할을 뜻한다: `load_*`(그래프 적재)·`inject_*`(기존 노드 속성 덮어쓰기)·`generate_*`(외부/원본에서 산출)·`build_*`(파생 색인 산출)·`enrich_*`·`apply_*`·`validate_*`(기계검증). 파일명은 snake_case.
- 공통 골격: 한글 docstring(첫 줄 목적 + `(task#NNN)`/ADR 근거) → `import` → 모듈 상수(`NEO4J_URI`/`NEO4J_USER`/`NEO4J_PASSWORD` 또는 `DATA`/`_ROOT` 경로) → 함수 → `def main()` → `if __name__ == "__main__": main()`.
- 경로는 스크립트 위치 기준 상대 해석 — `os.path.normpath(os.path.join(SCRIPT_DIR, "..", "..", "data", ...))` 또는 `Path(__file__).resolve().parents[2] / "data"`. 하드코딩 절대경로 금지.
- Neo4j 비밀번호는 `os.environ.get("NEO4J_PASSWORD")`로 읽고 없으면 즉시 `raise RuntimeError("NEO4J_PASSWORD 환경변수가 설정되지 않았습니다")`(`backend/app/db.py`와 동일 문구). **비밀번호를 파일에 적지 않는다** — `.env`는 gitignore.
- 실행 형태는 두 가지가 공존한다: 문서·README는 `python3 backend/scripts/<name>.py`, `scripts/check.sh`는 **모듈 실행** `python3 -m backend.scripts.validate_<name>`(리포지토리 루트 기준, `backend/__init__.py`·`backend/scripts/__init__.py`가 있어 가능). 새 검증기는 두 방식 모두로 돌아가야 한다.
- 셸 스크립트는 리포지토리 루트 `scripts/`(현재 `scripts/check.sh` 하나)와 루트 `deploy.sh`. `check.sh`는 `ROOT="$(cd "$(dirname "$0")/.." && pwd)"`로 자기 위치에서 루트를 유도한다.

---

## 3. 에러 처리

- **백엔드**: 알 수 없는 리소스 id만 `raise HTTPException(status_code=404, detail="...")`(`backend/app/routes/books.py`의 unknown book, `nodes.py`의 Node not found, `words.py`의 unknown book). 그 밖의 파일/파싱 실패는 예외를 올리지 않고 §1.1의 로깅 + 빈 값/빈 목록 폴백으로 흡수한다 — **오버레이 결손이나 JSON 파싱 실패가 500으로 전파되지 않는 것이 원칙**. 대표 패턴은 `backend/app/routes/nodes.py`의 `except Exception as e: logger.warning(...); clean_props["traits"] = []`.
- **프론트**: fetch 에러는 §1.2의 `console.warn` + 폴백 state로 흡수한다. `AbortError`는 에러가 아니므로 경고·폴백 모두에서 제외. `frontend/src/api.js`의 `apiGet`이 비-OK 응답을 `Error(String(res.status))`(+`err.status`)로 reject하는 단일 지점이다.
- 사용자에게 실패를 알려야 하는 화면은 **전용 불리언 state(`failed`)** 를 두고 인라인 안내를 렌더한다 — 공용 배너 컴포넌트는 없다. 실측: `RelianceView.jsx`·`WordDistributionView.jsx`·`StatsView.jsx`·`TopicalVersesView.jsx`·`ChapterReader.jsx`. `MapView.jsx`는 `error`/`noLocation` 두 불리언을 분리해 지도 위 배너로 각각 렌더한다.
- 조용히 사라지면 곤란한 부트스트랩 fetch는 **유한 지수 재시도**를 붙인다 — `useStageNavigation.js`의 `/persons/curated` 로더(1s→2s→4s, 3회 후 `console.warn`).
- **로더/빌더/inject 스크립트**는 반환값이 아니라 **프로세스 종료 코드**로 실패를 알린다: 사슬 단절·건수 불일치는 `raise SystemExit("FAIL: ...")`(`load_authored_genealogy.py:74`·`load_authored_mothers.py:46`), 통제 어휘 미분류는 `sys.exit(...)`로 산출 중단(`build_word_distribution.py:71`). 상세는 `TESTING.md`.

---

## 4. 백엔드 데이터 접근 패턴

### 4.1 오버레이 파일 접근 — `backend/app/overlays.py`

- `_resolve(subpath)`/`_resolve_dir(subpath)`는 `DATA_DIR` 환경변수(기본 `/app/data`, 컨테이너 마운트) → 리포지토리 `data/` 순으로 찾고, 없으면 `logger.warning` 후 `None`을 반환한다.
- `_load(subpath)`는 파일 없음·JSON 파싱 실패 모두 `logger.warning` 후 **빈 dict 폴백**(§3의 원칙).
- 새 오버레이는 `overlays.py`에 `@functools.lru_cache(maxsize=1)` 로더 함수를 하나 추가하고 한글 docstring에 스키마 요약을 적는다. 커밋 `43f987c` 기준 로더 전체(선언 순): `book_events_raw()`·`event_verses()`·`bible_verses()`·`word_distribution()`·`books_ko()`·`chapter_summaries()`·`chapter_sections()`·`quotations()`·`messianic_prophecies()`·`covenants()`·`parables_miracles()`·`place_coords()`·`topical_verses()`·`verse_persons()`.
- `overlays.py`에는 캐시 로더가 아닌 순수 헬퍼 1개가 함께 산다: `curated_person_id(events)` — `person_events/<slug>.json`의 `events[0].participants[0]`을 그 인물의 `theographic_id`로 해석하는 **큐레이션 신원 규약의 단일 지점**(소비처 `persons.py`·`places.py`·`reliance.py`; 로더 캐시가 아니라 데코레이터 없음).

### 4.2 캐시 두 겹 — `lru_cache` + `Cache-Control`

- 사용자 입력이 없는 전역 집계는 라우트 안에서 `@functools.lru_cache(maxsize=1)` 헬퍼로 1회 계산한다(`events.py`·`books.py`·`persons.py`·`reliance.py`·`stats.py`·`tours.py`·`family.py`). id별 결과는 `maxsize=256`/`2048`/`66` 등 상한을 둔다(`persons.py:221`·`books.py:53`·`books.py:105`·`places.py:21`).
- 응답은 `JSONResponse(content=..., headers={"Cache-Control": ...})`로 감싼다. 현행 값: 대부분 `max-age=300`(`events.py`·`journey.py`·`places.py`·`tours.py`·`family.py`는 5분), 절 본문처럼 불변에 가까운 것은 `public, max-age=3600`(`books.py`의 장/인용/본문), 예외적으로 `no-store`(`books.py`의 `/books-overview`).
- **결과**: `data/` JSON을 고쳐도 `docker compose restart api` 전까지 반영되지 않는다(`TESTING.md`의 footgun 절). 프론트는 `api.js`가 모든 요청에 `?v=<BUILD_ID>`를 붙여 브라우저 측 캐시만 배포마다 무효화한다.

### 4.3 중복 상수는 "공유 대신 정합 검증"

- 시대 경계 `ERA_BANDS`는 **3곳에 수동 복제**돼 있다: `frontend/src/TimelineView.jsx:15`(`{name, from, range}`)·`backend/app/routes/stats.py:24`(`(name, from)` 튜플)·`backend/app/routes/persons.py:98`(`_ERA_ORDER`, 이름 순서만) + `data/covenants/covenants.json`의 각 `era` 값. 프론트/백엔드가 코드를 공유할 수단이 없어 근본 통합 대신 **드리프트 검증 게이트**를 뒀다 — `backend/scripts/validate_era_bands_consistency.py`가 세 파일을 정규식으로 파싱해 이름·순서·경계를 대조하고 `covenants.json`의 `era`가 유효 시대인지 단언한다. 경계를 고칠 땐 세 곳을 함께 고치고 이 스크립트로 확인한다(`stats.py` 주석이 이 규약을 명시).

---

## 5. 프론트 상태 처리 패턴

### 5.1 상태 소유의 계층

- **`useNodeSelection`**(`frontend/src/useNodeSelection.js`) — 선택 노드·메타·패널 히스토리 원시값만. `selectNode`는 `useCallback([])` + `selectedNodeRef`로 참조를 안정화한다(참조가 흔들리면 `MapView`의 effect가 재실행돼 진행 중 fetch가 abort되던 버그 방지 — 주석에 근거 명시).
- **`useStageNavigation`**(`frontend/src/useStageNavigation.js`) — 화면 단계(Stage)·해시 URL·브라우저 히스토리 상태 머신. 노드 선택 원시값을 **주입받아** 조합한다. 이 파일은 `lucide-react`의 `Map`을 import하지 않고 `history` 배열을 구조분해하지 않는다 — 과거 두 차례 런타임 크래시를 낸 전역 `Map`/`history` 섀도잉을 구조적으로 막기 위한 규약(파일 상단 주석).
- **`useTourPlayback`**(`frontend/src/useTourPlayback.js`) — 투어 자동재생 시퀀서. 상태만 갖고 카메라·경로선은 `App`/`MapView`가 `idx`를 구독해 구동한다. 반환 객체는 `useMemo`로 안정화해 소비처 effect의 의존성으로 안전하게 쓰인다.
- **페이지 대상 id는 `selectedNode`와 분리해 별도 state로 둔다** — `bookId`·`familyId`·`wordsBookId`·`readerBookId`/`readerChapter`·`explorePersonId`·`exploreTourId`. 페이지 안에서 노드를 눌러 시트를 띄워도 페이지 대상과 URL이 흔들리지 않게 하는 대칭 패턴.

### 5.2 URL = 해시 문자열 매핑 (라우팅 라이브러리 없음)

- `frontend/src/urlState.js`의 `encodeHash(state)`/`parseHash(hash)` 한 쌍이 정본이며 파일 상단 주석이 전체 딥링크 표를 담는다: `#/`·`#/intro`·`#/books`·`#/book/<id>`·`#/read/<id>[/<n>]`·`#/family/<id>`·`#/words/<id>`·`#/stats`·`#/topics`·`#/tours`·`#/tour/<slug>[/timeline]`·`#/person/<slug>[/timeline|/relations|/intro|/reliance]`.
- **알 수 없는 형태는 `null` 반환 → 호출부가 허브로 폴백**. 새 스테이지를 추가하면 `encodeHash`·`parseHash` 양쪽을 함께 고친다(왕복 대칭이 계약).

### 5.3 effect 안의 동기 `setState` 금지 (react-hooks v7)

`eslint-plugin-react-hooks` v7의 `set-state-in-effect`가 켜져 있어(§8), 현행 코드는 세 관용구로 이를 지킨다.

- **파생 상태로 승격**: effect+setState 대신 `useMemo`. 실측 — `App.jsx:101` `playbackStopIdx`(재생 인덱스 → 정차지 그룹 인덱스, task#253 리팩터), `App.jsx:75` `tourEventIds`.
- **비동기 콜백으로 이동**: 타이머·프라미스 콜백 안의 setState는 규칙에 걸리지 않는다. 초기화가 필요하면 `Promise.resolve().then(() => { ... })`로 마이크로태스크에 미룬다(`App.jsx:96`·`App.jsx:137`·`useStageNavigation.js`의 딥링크 복원). fetch `.then` 안의 setState는 그대로 둔다(`// async 콜백 — v7 OK` 주석: `App.jsx:124`·`MapView.jsx:129`).
- **키 기반 무효화**: 리셋용 effect 대신 결과 state에 대상 키를 함께 담고 렌더에서 대조한다 — `SidePanel.jsx`의 `{ forNodeId, ... }` 패턴(`:64`·`:69` 주석이 "set-state-in-effect 준수" 명시).
- 남은 `// eslint-disable-next-line react-hooks/exhaustive-deps`는 `useStageNavigation.js:122`·`:174` 두 곳뿐이다(딥링크 복원/히스토리 동기화의 의도적 1회 실행).

### 5.4 기타 상태 관용구

- 전역 상태 라이브러리 없음(Redux/Zustand/Context 미사용). 공유가 필요한 값은 `App.jsx`가 소유하고 props로 내려준다(`verseLang`·`journeyStops`·`isMobile`).
- 모바일 분기는 `window.matchMedia(MOBILE_QUERY)` 구독 state — 브레이크포인트 값의 단일 출처는 `frontend/src/constants.js`(`MOBILE_BREAKPOINT`·`SHEET_VH`·`JOURNEY_SHEET_VH`; 마지막 값은 App 시트 높이와 MapView 카메라 offset이 공유해야 하는 값이라 주석이 이유를 명시).
- 목록 스크롤 위치는 React state가 아니라 **모듈 스코프 plain object**로 기억한다(`frontend/src/scrollMemory.js`) — 인앱 "뒤로"가 popstate가 아니라 전진 push라 `history.state`로는 복원되지 않기 때문(ADR-0010). 전역 `Map` 섀도잉 함정 회피를 위해 `Map`이 아닌 plain object.
- `startDate`는 혼재 형식 문자열이므로 **숫자 강제변환·사전순 정렬 금지** — 라벨 변환은 반드시 `frontend/src/dates.js`의 `parseYear()`를 거친다. 백엔드 대응 구현은 `backend/scripts/load_books.py`의 `_parse_year()`·`backend/app/routes/nodes.py`의 `_year`(세 구현이 같은 규칙을 따라야 한다고 docstring이 명시).

---

## 6. 데이터 저작 규약 — 저작(사람/LLM) ↔ 검증(스크립트) 분리

**핵심 원칙**: 저작과 검증을 서로 다른 파일·다른 실행 시점으로 분리한다. 저작자는 원문 스키마만 채우고 `backend/scripts/validate_*.py`가 사후에 불변식을 전수 검사한다. 위반이 있어도 통과 대상은 통과시키고 **위반 항목만 골라 보고**하는 항목 단위 게이트가 관례다.

### 6.1 저작 규칙 문서 — `data/<도메인>/AUTHORING.md`

- 손저작 도메인 4곳이 규칙 정본을 갖는다: `data/character_traits/AUTHORING.md`·`data/god_reliance/AUTHORING.md`·`data/person_context/AUTHORING.md`·`data/person_relations/AUTHORING.md`. 각 문서는 스키마·통제 어휘·저작 규칙·검증 절차를 담는다.
- **본문 필드는 손으로 쓰지 않는다** — 저작자는 **구절 참조만**(`verse`/`ref`/`verse_ref`) 쓰고, `backend/scripts/generate_verse_text.py` 같은 빌드타임 스크립트가 정본 절 사전에서 `textKo`/`textEn`을 프리베이크한다(ADR-0003).
- **근거 인정 경계**: 한 사건의 근거 구절로 인정되는 패턴은 (a) 평행 기사, (b) 집필 정황 자기 언급 두 가지뿐. 어느 쪽도 아니면 구절을 만들지 않는다(억지 인용 금지, 스킵 허용) — `.claude/agents/data-author.md`가 이 규칙을 에이전트 계약으로 고정한다.

### 6.2 성경 참조 표기 — 라벨 vs verseID (verse-grounding)

두 표현이 공존하며 역할이 다르다.

- **사람이 쓰는 범위 라벨**: 개역 약어 + `장:절[-절[:절]]` — `"창 32:26"`·`"창 18:2-5"`·`"마 5:3-12"`. 필드명은 `verse`·`ref`·`verse_ref`·`rangeLabel`·`otRangeLabel`/`ntRangeLabel`. 형식 정규식의 정본은 `backend/scripts/validate_traits.py:23`의 `REF_RE`(`^[가-힣]{1,4}(?:[전후상하]|[0-9])?\s\d+:\d+(?:-\d+(?::\d+)?)?$`)이며 `validate_person_context.py`가 같은 정규식을 복제해 쓴다. 약어→권 번호 해석은 `data/names_ko/books.json`의 `alias` 배열이 정본이다.
- **기계 정본 verseID**: `BBCCCVVV` 8자리 문자열(권 2 + 장 3 + 절 3, 예 `40005003` = 마 5:3). 필드명은 `verseIds`·`keyVerseIds`·`keyVerseId`·`otVerseIds`/`ntVerseIds`.
- **불변식**: 참조를 가진 오버레이는 verseID 배열이 정본이며, 모든 verseID는 정본 절 사전 `data/bible/verses.json`(로더 `overlays.bible_verses()`)에 **실존해야** 한다. 라벨과 verseID의 자기일치(라벨 파싱 결과 = verseID 배열)는 대응 `validate_*.py`가 강제한다(`TESTING.md`).
- 연대는 **현대 보수 연대계가 정본**(ADR-0014) — theographic 원본은 Ussher계/AD30계라 그대로 믿지 않는다. 교정은 `data/date_corrections/{events,persons}.json`에 항목으로 쌓고 `inject_date_corrections.py`가 반영한다.

### 6.3 통제 어휘는 문서·검증 스크립트 이중 관리

- 통제 어휘는 AUTHORING.md와 대응 `validate_*.py`에 **이중으로** 산다. 어휘를 확장하면 두 곳을 함께 고친다(스크립트 주석이 "문서와 함께 갱신할 것"을 명시).
  - 성품: `data/character_traits/AUTHORING.md` §3의 미덕 24 · 결함 8 ↔ `backend/scripts/validate_traits.py`의 `VIRTUES`/`FLAWS`.
  - 하나님 의존: `data/god_reliance/AUTHORING.md` §2의 `mode` 5종(`물음-응답`·`물음-침묵`·`독단-개입`·`독단-어긋남`·`부르심`)과 §3의 `kind` 5종(`이룸`·`더하심`·`다르게`·`거절`·`침묵`) ↔ `backend/scripts/validate_god_reliance.py`의 `MODES`/`ASK_MODES`/`KINDS`.
  - 관계 유형: `data/person_relations/AUTHORING.md`의 유형 어휘표(하나님·가족·연인·친구·신하·선지자·스승제자·군주·대적) ↔ `frontend/src/RelationsView.jsx`의 `TYPE_ICON`/`TYPE_ORDER`. **미등록 유형은 아이콘 없이 렌더**되므로 신규 유형은 프론트 등록이 필수(문서가 명시).
- 비유·기적 `type`은 `"parable"`|`"miracle"` 2값(`validate_parables_miracles.py`), 언약·인물의 `era`는 §4.3의 시대 이름 집합이 통제 어휘 역할을 한다.

### 6.4 에코 필드 멱등성 (inject 스크립트)

- 기존 노드 값을 덮어쓰는 `inject_*.py`는 각 항목에 **에코 필드**(수정 전 예상값)를 넣어 멱등·안전하게 만든다. 정본 패턴은 `backend/scripts/inject_date_corrections.py` — `events`는 `title`/`oldStartDate`, `persons`는 `name`/`field`/`oldValue`가 에코다. DB 현재값이 에코와 일치하면 교정 적용, 이미 새 값이면 "이미 적용"으로 조용히 통과, 에코 불일치면 스킵 + 경고.
- 각 항목은 `rationale` 필드에 판단 근거(앵커 산술·오타 판정 등)를 한글로 남긴다 — 사후 재검토 가능성을 데이터 안에 보존하는 관례.

### 6.5 대량 병렬 저작 = 저작 에이전트는 파일 미접촉

- 수백~수천 항목의 병렬 저작은 **저작 에이전트가 파일을 직접 만지지 않고 JSON만 반환**하고, 별도 병합 스크립트가 기계검증 후 정본 파일에 반영한다. 정본 예시: `.forge/scratch/task203/validate_and_merge.py`·`.forge/scratch/genealogy-authoring/`의 `s1_classify.py`/`merge_validate.py`. 저작 프롬프트에는 근거 인정 경계와 "스킵 허용"을 항상 명시한다.
- **예외 — 긴 산문은 단일 컨텍스트로**: 항목이 짧은 구조화 라벨이 아니라 문체 일관성이 중요한 서술(투어 정차지 해설 등)이면 병렬 분업 대신 단일 세션이 전량 저작한다(`.forge/retro/2026-07-22-tour-event-coverage.md`: 해설 110건). 검증은 여전히 항목 단위 기계 게이트로 닫는다.
- 역할은 `.claude/agents/` 카드로 고정돼 있다 — `data-author`(저작·교정)·`scripture-reviewer`(구절 정합 판정, 읽기 전용)·`line-artist`(선화·장면 스케치)·`frontend-dev`·`ui-verifier`(Playwright 검증, 읽기 전용).

### 6.6 투어 정차지 해설은 투어 파일 안에 (ADR-0028)

- 투어의 `stops`는 `["eventId", ...]`가 아니라 `[{"id": "eventId", "note": "..."}]` **객체 배열**이다(`data/tours/*.json`, 파서는 `backend/app/routes/tours.py`).
- `note`는 그 **투어 관점**의 해설(2~3문장, nullable)이며 사건 본문(`data/person_events/`)에 병합하지 않는다 — 같은 사건이 여러 투어에 속할 때 투어마다 다른 서술이 필요하기 때문.
- `tours.py`는 **객체 형식만 파싱**한다(이중 파서 없음). 새 정차지의 `note`는 `null`로 두고 나중에 채워도 된다(그레이스풀 부분 저작).

---

## 7. 스타일 — CSS 토큰 / 듀얼 테마 / 모션 / 선화

### 7.1 인라인 스타일 + CSS 변수 (CSS 라이브러리 없음)

- CSS Module·styled-components·Tailwind 등을 쓰지 않는다. 컴포넌트는 `style={{ ... }}` 인라인 객체로 스타일링한다.
- 디자인 토큰의 단일 출처는 `frontend/src/index.css`의 `:root` 커스텀 프로퍼티: `--bg-0..3`·`--line`/`--line-strong`·`--ink`/`--ink-dim`/`--ink-faint`·`--gold`/`--gold-dim`·`--paper`/`--paper-ink`/`--paper-accent`·`--type-*`(6종)·`--valence-*`(3종)·`--select-hl`·`--danger`·`--r-s/m/l`·`--shadow-1/2`·`--z-verse`/`--scrim`·`--serif`/`--sans`/`--serif-display`·모션 토큰 `--dur-*`/`--ease-*`(§7.3). 인라인 스타일은 `var(--gold)` 식으로 참조한다.
- 알파 결합은 hex 이어붙임 대신 `color-mix(in srgb, ${color} 13%, transparent)`(`Spinner.jsx`·`SpineHeader.jsx`·`tourSketches.jsx`).
- 클래스는 인라인으로 못 하는 것만 `index.css`에 둔다: `.rel-chip`·`.pressable`(`:active` — 인라인 background/transform이 이기는 특이성 회피), keyframe 애니메이션 클래스.
- 웹폰트는 브랜드 워드마크 1곳뿐 — `--serif-display`(IM Fell English, `frontend/public/fonts/`). 로드 실패·로딩 중엔 `var(--serif)` 폴백이며 `font-weight: 400`만 쓴다(이 폰트는 400 하나만 있어 임의 굵기는 faux-bold 유발). 본문/UI는 시스템 명조·산스.

### 7.2 다크 기본 + 라이트 옵트인 (ADR-0020)

- 다크(Night Atlas)가 기본, 라이트(Day Atlas)는 옵트인. 같은 토큰 계약에 값만 두 벌 — `index.css:14`의 `:root`(다크)와 `index.css:100`의 `:root[data-theme='light']` 오버라이드 블록(각각 `color-scheme` 선언 포함).
- 테마 상태의 정본은 `localStorage`의 `biblemap-theme` + `document.documentElement.dataset.theme`. `frontend/src/main.jsx`가 **렌더 전에 동기 반영**해 첫 페인트 깜빡임을 막는다. 토글(`frontend/src/SpineHeader.jsx:67`)은 React 리렌더 없이 `dataset.theme`을 직접 조작한다.
- 테마 불변 영역: 양피지 3색(`--paper`/`--paper-ink`/`--paper-accent`, 성경 본문 전용 배경)과 지도(`frontend/src/mapLayers.js`의 리터럴 hex) — 라이트 블록에 이 토큰들의 오버라이드가 없다.
- JS 팔레트 상수는 `frontend/src/theme.js`(`TYPE_COLOR`/`TYPE_KO`/`TYPE_ORDER`/`VALENCE_COLOR`/`SELECT_HL`/`GENRE_META`) — 값의 정본은 `index.css`이고 `theme.js`는 `'var(--type-person)'` 같은 **var 참조 문자열**만 갖는다(인라인 style 전용). **예외 1건**: `PM_TYPE_COLOR = { parable: '#8b5cf6', miracle: '#2f9e63' }`은 리터럴 hex다 — maplibre `paint`가 CSS 변수를 받지 못해 `mapLayers.js`와 `TimelineView.jsx`가 같은 리터럴을 공유해야 하기 때문(주석에 이유 명시).
- `localStorage` 키는 `biblemap-` 접두를 공유한다: `biblemap-theme`(값이 `'light'`인지로 판정)과 `biblemap-intro`(`frontend/src/IntroView.jsx:11`이 `INTRO_STORAGE_KEY`로 export). 후자는 **키의 존재 자체가 상태** — `'off'`면 숨김, 키 부재(기본)면 노출(`useStageNavigation.js:16`이 무해시 진입 시 `intro`/`hub` 시작 스테이지를 분기).

### 7.3 모션 토큰 (ADR-0024)

- 모션 정본은 `index.css` `:root`의 `--dur-fast`(150ms)/`--dur-base`(250ms)/`--dur-slow`(400ms)/`--dur-draw`(1000ms) + `--ease-out`/`--ease-in-out`/`--ease-drawer`/`--ease-pop`. duration·easing을 리터럴로 하드코딩하지 않는다.
- 애니메이트 가능한 속성은 **transform·opacity**(+ 선화의 `stroke-dashoffset`)만 — 레이아웃 속성 금지. 입장(enter)만 만들고 exit는 즉시 언마운트.
- `@media (prefers-reduced-motion: reduce)`(`index.css:137`)에서 `--dur-*` 전부와 `animation-delay`를 1ms/0ms로 붕괴시키는 **토큰 붕괴 가드**가 개별 컴포넌트의 reduce 분기를 대체한다. CSS 트랜지션이 아닌 JS 애니메이션(`RelianceView.jsx`의 `Donut`)과 SMIL/타이머 기반 연출(`tourSketches.jsx`·`IntroView.jsx`·`sketches/*`)은 이 가드로 가려지지 않아 `window.matchMedia('(prefers-reduced-motion: reduce)')`를 직접 분기한다.
- 애니메이션 클래스 목록(`index.css`): `.cloud-in`·`.word-in`·`.stage-in`·`.overlay-in`·`.modal-in`·`.sheet-in`·`.thread-draw`·`.card-in`·`.bar-reveal`·`.stop-bar-in`·`.symbol-draw`·`.book-open`·`.intro-rise`·`.intro-line`·`.film-in`·`.film-fade`·`.beat-in`/`.beat-out`.
- 사이트 인트로(`frontend/src/IntroView.jsx`)는 오토플레이 시네마틱 필름이다 — phase 상태 머신이 `setTimeout`으로 6비트(`BEAT_MS = [3000, 5000, 5000, 3000, 3000, 3000]`)를 순차 진행하고, 비트 전환은 **겹치지 않는 순차 디졸브**(이전 비트가 `.beat-out`으로 빠진 뒤 새 비트가 `.beat-in`으로 진입). 비트 안의 씬 요소는 `.film-fade` + 인라인 `animationDelay` 스태거, 선 그리기는 `.thread-draw`(`--thread-delay` CSS 변수).
- **잔존 사각(정리 대상)**: 구 스크롤 리빌 클래스 `.intro-sec`/`.intro-seen`(`index.css:328~332`)은 어느 컴포넌트도 더 이상 참조하지 않는다.

### 7.4 인물/책 상징물 선화 (ADR-0025)

- 인물·책 대표 이미지는 얼굴 초상/외부 이미지가 아니라 **손저작 stroke-only SVG 선화**다. 정본은 `frontend/src/personSymbols.jsx`의 `SYMBOLS`(인물, slug 키)와 `frontend/src/bookSymbols.jsx`의 `SYMBOLS`(책, `theographic_id` 키 — 책은 slug가 없음).
- 공통 저작 규격: `viewBox 64×64`, `stroke="currentColor"`(듀얼 테마 자동 추종), `strokeWidth 2`, fill 없음, 모든 stroke 요소에 `pathLength={1}`(`.symbol-draw`의 dash 1 = 전체 선 draw-on 전제). **미등록 키는 범용 폴백 인장**으로 렌더해 부분 저작 상태에서도 화면이 깨지지 않는다.

### 7.5 투어 장면 스케치 — 투어당 1개 JSX 코드 모듈 (ADR-0029)

- 투어 재생 정차지의 삽화 시퀀스는 SVG/JSON 데이터가 아니라 **`frontend/src/sketches/` 아래 투어당 1개 JSX 모듈**로 저작한다: `creationToFlood.jsx`·`patriarchsCovenant.jsx`·`exodusToConquest.jsx`·`ageOfJudges.jsx`·`davidUnitedKingdom.jsx`·`elijahAndElisha.jsx`·`exileAndReturn.jsx`·`gospelOfJesus.jsx`·`theEarlyChurch.jsx`(9개, `data/tours/*.json` 9개와 1:1). 각 모듈은 eventId를 키로 하는 레지스트리 객체(`{ Scene, mood, desc, caption }`)를 default export한다.
- 공용 표준의 정본은 **순수 헬퍼 모듈** `frontend/src/sketches/lib.jsx`: 선 굵기 위계(원경 1.1 · 질감 1.3 · 지면 1.6 · 보조 1.8~2 · 주역 2.4~2.6 · 핵심 3, 전역 배율 `W = 0.55`)를 `sw(n, opacity?)`로 적용, 단계 딜레이는 `d(ms, reduce)`가 CSS 변수 `--sym-delay`로 자식 stroke에 상속, `P = { pathLength: 1 }`. 장면 이름표 컴포넌트 `Label`은 `frontend/src/sketches/SceneLabel.jsx`로 분리돼 있다(§2.2의 react-refresh 규약).
- `frontend/src/tourSketches.jsx`가 9개 레지스트리를 한 `SCENES` 맵으로 스프레드 병합하고, default export `TourSketch`(viewBox `0 0 120 64`)와 named export `TourSketchPanel`(양피지 패널; `mood: 'dark'`면 `--paper-accent`만 목탄색(`#5f584c`)으로 오버라이드하고 종이 배경은 항상 크림 유지)을 제공한다. `hasSketch`는 모듈 내부 전용(un-export, task#253). **등록 없는 정차지는 아무것도 렌더하지 않는다** — §7.4와 같은 그레이스풀 부분 저작 원칙.
- 무거운 자산이라 **지연 로드**한다: `IntroView.jsx:5` `lazy(() => import('./tourSketches'))`, `TourPlayback.jsx:5` `lazy(() => import('./tourSketches').then(m => ({ default: m.TourSketchPanel })))`, 둘 다 `<Suspense fallback={null}>`로 감싼다(task#254 — 메인 청크 640→250KB).
- 데이터(투어 `stops`)와 코드(장면 레지스트리)가 eventId로 페어링되므로 커버리지는 **집합 대조**(stops의 id ⊆ 레지스트리 키)로 검증한다(`TESTING.md`).

---

## 8. 린트·포맷·빌드 도구 설정

- **포매터 없음** — Prettier·Black·ruff 설정 파일이 리포지토리에 없다. 스타일은 위 규약과 기존 코드 모방으로 유지한다(들여쓰기: JS 2칸 + 세미콜론 없음, Python 4칸).
- **ESLint(프론트 전용)** — flat config `frontend/eslint.config.js`. `globalIgnores(['dist'])` + `**/*.{js,jsx}`에 `@eslint/js` recommended · `eslint-plugin-react-hooks` flat recommended · `eslint-plugin-react-refresh` vite 프리셋. `languageOptions.globals`에 `...globals.browser`와 함께 **`__BUILD_ID__: 'readonly'`**(vite `define` 주입값)를 등록한다.
- 버전(`frontend/package.json`): `eslint ^10.3.0` · `eslint-plugin-react-hooks ^7.1.1` · `eslint-plugin-react-refresh ^0.5.2` · `@eslint/js ^10.0.1` · `globals ^17.6.0`. react-hooks v7이 `set-state-in-effect` 등 신규 규칙을 켜므로 §5.3의 관용구가 필요하다.
- 실행: `cd frontend && npm run lint`(= `eslint .`) 또는 게이트가 쓰는 `npx --no-install eslint src`(`scripts/check.sh`). 커밋 `43f987c` 기준 **둘 다 0 error / 0 warning**이며, 규칙 비활성화가 아니라 코드 리팩터로 달성한 상태다(task#253) — 규칙을 끄는 방향의 수정은 사용자 확인 없이 하지 않는다.
- `eslint-disable` 잔존은 4곳뿐: `VerseLayer.jsx:21`·`personSymbols.jsx:488`(`react-refresh/only-export-components`), `useStageNavigation.js:122`·`:174`(`react-hooks/exhaustive-deps`).
- **빌드(Vite)** — `frontend/vite.config.js`: `@vitejs/plugin-react`, `define.__BUILD_ID__ = JSON.stringify(String(Date.now()))`(배포마다 바뀌는 캐시버스터, `api.js`가 소비), `build.rollupOptions.output.manualChunks`로 `node_modules` 중 `maplibre-gl`은 `maplibre` 청크·나머지는 `vendor` 청크로 분리. 앱 코드 추가 분할은 §7.5의 `React.lazy`로 한다.
- **환경변수** — `frontend/.env.production`의 `VITE_API_URL=/api`(nginx `/api` 프록시). 개발 기본값은 `api.js`의 `'http://localhost:8000'` 폴백. 비밀값은 리포지토리 루트 `.env`(gitignore, 템플릿은 `.env.example`)에만 두고 `docker-compose.yml`이 `${NEO4J_PASSWORD:?...}`로 필수 주입한다.
- **백엔드 의존성**은 핀 고정 3개뿐(`backend/requirements.txt`): `fastapi==0.136.3`·`neo4j==6.2.0`·`uvicorn==0.49.0`. 린터·포매터·테스트 러너는 포함되지 않는다.
- 배포 전 품질 게이트는 `scripts/check.sh`(데이터 검증 12종 + ESLint + Neo4j 연대 정합)이며 `deploy.sh`가 빌드 앞단에서 호출한다 — 상세는 `TESTING.md`.
