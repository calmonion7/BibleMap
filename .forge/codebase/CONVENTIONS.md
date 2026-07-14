---
last_mapped_commit: e53ec23d634a48d16bd1abf3e131c340cfbaac1f
mapped: 2026-07-14
---

# CONVENTIONS

BibleMap의 코드 스타일·패턴 정본. 백엔드(FastAPI + Neo4j), 프론트(React + Vite), 데이터 저작 세 레이어로 나눈다. 도메인 용어 정의는 CONTEXT.md 소관 — 여기는 "어떻게 쓰는가"만 담는다.

---

## 1. 백엔드 (FastAPI + Neo4j)

### 1.1 라우터 = 엔티티당 1파일

- 모든 엔드포인트는 `backend/app/routes/` 아래 엔티티별 파일에 산다: `nodes.py`·`events.py`·`search.py`·`books.py`·`persons.py`·`journey.py`·`places.py`·`tours.py`·`family.py`·`words.py`(10개).
- 각 파일은 모듈 최상단에서 `router = APIRouter()`를 만들고 함수에 `@router.get("/...")`를 단다. POST/PUT 없음 — 읽기 전용 API다.
- `backend/app/main.py`가 열 라우터를 `app.include_router(...)`로 모두 등록한다. `main.py`에는 라우트 정의가 없다.
- 미지의 리소스 id는 `raise HTTPException(status_code=404, detail="...")`로 답한다(`backend/app/routes/words.py`의 unknown book 등).
- CORS는 `main.py`에서 `allow_origins=["*"]`, `allow_credentials=False`, `allow_methods=["GET"]` — GET 전용을 미들웨어에서도 못 박는다.
- 앱 기동은 `lifespan` 컨텍스트에서 Neo4j 라벨별 `theographic_id` 인덱스를 `CREATE INDEX ... IF NOT EXISTS`로 준비한다(실패해도 `logger.exception` 남기고 계속 진행).

### 1.2 응답 = `JSONResponse` + `Cache-Control` 헤더

- 캐시 가능한 읽기는 `return JSONResponse(content=..., headers={"Cache-Control": "max-age=300"})` 형태가 표준. `persons.py`·`events.py`·`journey.py`·`places.py`·`tours.py`·`family.py` 전부 이 패턴.
- 개요처럼 항상 최신이어야 하는 응답은 `headers={"Cache-Control": "no-store"}`(`books.py` `/books-overview`).
- nginx가 정적 애셋에 `immutable`을, `index.html`에 `no-cache`를 별도로 붙인다(`nginx/nginx.conf`) — API의 `Cache-Control`과 층이 다르다.
- 예외: 단순 라우트는 순수 파이썬 값을 그대로 반환하기도 한다 — `search.py` `/search`는 `list`를, `nodes.py` 일부와 `words.py` 전부는 dict를 `JSONResponse` 없이 돌려준다. 새 엔드포인트는 캐시 의미가 있으면 `JSONResponse` + 헤더 패턴을 따른다.

### 1.3 비싼 읽기 = `functools.lru_cache`

- 앱 생명주기 동안 불변인 결과는 `@functools.lru_cache(maxsize=1)`로 1회 로드 후 메모리에 고정한다: 오버레이 로더(`backend/app/overlays.py`의 `book_events_raw`/`event_verses`/`bible_verses`/`word_distribution`/`books_ko`), 큐레이션 목록(`persons.py` `_build_list`), 타임라인 사건(`events.py` `_compute_events`), 책 이름 맵(`_book_name_map`) 등.
- 노드 id별 결과는 `@functools.lru_cache(maxsize=256)`(`persons.py` `_build_connections`·`_build_relations`).
- **함의(footgun)**: 데이터(오버레이 JSON·Neo4j)가 바뀌어도 프로세스가 살아 있으면 옛 캐시를 계속 서빙한다. 반영하려면 `docker compose restart api`로 컨테이너를 재기동해 캐시를 비운다(TESTING.md·`data/person_relations/AUTHORING.md` §8 참조).

### 1.4 DB 접근

- `backend/app/db.py` `get_driver()`가 지연 초기화 싱글턴 드라이버를 준다. `NEO4J_URI`(기본 `bolt://localhost:7687`)·`NEO4J_USER`(기본 `neo4j`)·`NEO4J_PASSWORD`(필수, 없으면 `RuntimeError`)를 환경변수에서 읽는다.
- 라우트는 `driver = get_driver()` 후 `with driver.session() as session:` 블록 안에서 쿼리한다.
- Cypher는 **파라미터 바인딩**($id, $ids, $q)이 규칙. f-string은 라벨명·`LIMIT` 상수처럼 구조적 요소에만 쓴다(`search.py`의 `LIMIT {SEARCH_LIMIT}`, `main.py`의 인덱스명).
- 노드의 정본 식별자 속성은 `theographic_id`. 응답 JSON에선 보통 `id` 키로 노출한다.
- 검색은 `status='wip'` 노드를 제외한다: `search.py`의 `AND (n.status IS NULL OR n.status <> 'wip')` (§3.5 wip 마커 참조).

### 1.5 오버레이 파일

- `backend/app/overlays.py`가 JSON 오버레이 접근을 담당한다. `_resolve(subpath)`/`_resolve_dir(subpath)`는 `DATA_DIR`(기본 `/app/data`, 컨테이너 마운트) → 리포지토리 `data/` 순으로 파일/디렉터리를 찾고, 없으면 `logger.warning` 후 `None`을 반환한다.
- `_load(subpath)`는 파일 없음·JSON 파싱 실패 모두 `logger.warning` 후 빈 dict로 폴백한다 — 오버레이 결손이 500이 되지 않게 한다.
- 새 오버레이는 `overlays.py`에 `@functools.lru_cache(maxsize=1)` 로더 함수를 추가하고 라우트가 `overlays.word_distribution()`처럼 호출한다(`routes/words.py`가 최신 예).
- 라우트가 자체 오버레이를 읽을 땐 `from ..overlays import _resolve`로 경로만 얻어 직접 `open(...)`하는 패턴도 쓴다(`persons.py`의 `person_context`/`keypeople` 로더).

### 1.6 로깅 방출 규약

- 모듈마다 `logger = logging.getLogger(__name__)`. `backend/app/` 안에서 `print()`·root 직호출 금지(`print`는 `backend/scripts/`에서만).
- 메시지는 `[Component]` prefix로 시작한다: `[Startup]`(main)·`[Overlays]`·`[Persons]`·`[Places]`·`[Tours]`·`[Nodes]`.
- 빈값 폴백(오버레이 결손·JSON 파싱 실패·participants 비어 있음)은 `logger.warning`, 기동 예외는 `logger.exception`. 포맷은 lazy `%s`(문자열 f-string 아님).
- `main.py` `_configure_logging()`은 **라우터 import 전** 1회 호출된다: `basicConfig(level=INFO)`, 수다스러운 서드파티(`neo4j`/`urllib3`/`asyncio`)는 WARNING 승격, `uvicorn`·`uvicorn.access`는 `propagate=False`로 root 중복 emit 차단(단 `uvicorn.error`는 제외 — propagate 끊으면 기동/에러 라인이 사라진다).

### 1.7 문서화

- 모듈 docstring·라우트 함수 docstring은 한글로, "무엇을 반환하는가 + 왜 이렇게 하는가"를 적는다(예: `persons.py`·`events.py`·`words.py`의 docstring). ADR 번호를 인라인으로 참조한다(`ADR-0017`·`ADR-0021` 등).

---

## 2. 프론트엔드 (React 19 + Vite 8)

### 2.1 스타일 = 인라인 스타일 + CSS 변수 (CSS 라이브러리 없음)

- CSS Module·styled-components·Tailwind 등 스타일 라이브러리를 쓰지 않는다. 컴포넌트는 `style={{ ... }}` 인라인 객체로 스타일링한다(`frontend/src/App.jsx`가 대표적 — 내비 바·시트가 전부 인라인).
- 디자인 토큰은 `frontend/src/index.css` `:root`의 CSS 커스텀 프로퍼티가 단일 출처: `--bg-0..3`·`--line`/`--line-strong`·`--ink`/`--ink-dim`/`--ink-faint`·`--gold`/`--gold-dim`·`--paper*`·`--type-*`(6종)·`--valence-*`(3종)·`--select-hl`·`--danger`·`--r-s/m/l`·`--shadow-1/2`·`--serif`/`--sans`. 인라인 스타일에서 `var(--gold)` 식으로 참조한다.
- 알파 결합은 hex 이어붙임(`${GOLD}22`) 대신 `color-mix(in srgb, ${color} 13%, transparent)` — var() 참조도 받는다(`frontend/src/Spinner.jsx`·`PersonHub.jsx`).
- 클래스가 필요한 특수 케이스만 `index.css`에 둔다: `.rel-chip`(`:active` — 인라인 background가 `:active`를 이기는 특이성 gotcha 회피), `.cloud-in`/`.word-in`(keyframe 애니메이션 — 인라인 불가). keyframe의 종료값을 요소별로 바꿔야 하면 인라인 CSS 변수로 전달한다(`word-in`의 `--w-op` — `animation-fill-mode: both`가 inline `opacity`를 덮는 gotcha 우회, `WordDistributionView.jsx`).

### 2.1a 듀얼 테마 — 다크 기본 + 라이트 옵트인 (ADR-0020)

- 다크(Night Atlas)가 기본, 라이트(Day Atlas)는 옵트인. 같은 토큰 계약에 값만 두 벌 — `index.css`의 `:root`(다크) + `:root[data-theme='light']` 오버라이드 블록(각각 `color-scheme` 선언 포함).
- 테마 상태의 정본은 `localStorage`의 `biblemap-theme` 키 + `document.documentElement.dataset.theme`. `frontend/src/main.jsx`가 **렌더 전에 동기 반영**해 첫 페인트 깜빡임을 막고, 토글(`frontend/src/PersonHub.jsx` 해/달 버튼)은 React 리렌더 없이 `dataset.theme`을 직접 조작한다(색이 전부 CSS 변수라 충분; state는 아이콘 표시용).
- 테마 불변 영역: 양피지(`--paper`/`--paper-ink`/`--paper-accent`)와 지도(MapView·`mapLayers.js`의 리터럴 색). 라이트 블록에 이 토큰들의 오버라이드는 없다.
- 새 색을 넣을 때: 테마 민감한 색이면 `index.css` 두 블록에 토큰을 정의하고 var로 참조. 에러색은 `--danger`. 라이트 값은 명도를 낮춰 대비를 확보한다(본문 4.5:1·칩 3:1 목표).

### 2.1b JS 팔레트 상수 = `theme.js` (var 참조)

- `frontend/src/theme.js`가 노드 타입 색·한글 라벨(`TYPE_COLOR`/`TYPE_KO`/`TYPE_ORDER`)·관계 valence 색(`VALENCE_COLOR`)·선택 강조(`SELECT_HL`)·장르 메타(`GENRE_META`)의 정규 팔레트다(과거 파일별로 흩어져 색 충돌났던 것을 통일).
- 값의 정본은 `index.css`의 `--type-*`/`--valence-*`/`--select-hl` — theme.js 상수는 `'var(--type-person)'` 같은 **var 참조 문자열**이라 CSS 컨텍스트(인라인 style) 전용이다. 리터럴 hex가 필요한 캔버스·maplibre류엔 못 쓴다(지도는 이 팔레트를 안 쓰고 `mapLayers.js`에 자체 리터럴).

### 2.1c 양피지 레이어 패턴 (구절 표시 정본)

- 성경 구절 본문은 밝은 양피지 표면에 띄운다. 두 형태:
  - **포털 모달**: `createPortal`로 `document.body`에, 스크림 `rgba(20,26,40,0.45)` 고정 오버레이(클릭 시 닫힘, 내부는 `stopPropagation`) 안에 `background: 'var(--paper)'`·`color: 'var(--paper-ink)'`·`borderRadius: 'var(--r-m)'`·`boxShadow: 'var(--shadow-2)'`·`maxWidth: 520`·`maxHeight: '80%'` 카드. 원본은 `frontend/src/SidePanel.jsx`의 구절 모달, `WordDistributionView.jsx`가 동일 패턴을 복제.
  - **인라인 카드**: `SidePanel.jsx`의 `var(--paper)` + `--shadow-1` 카드(라이트 테마 경계용 `--line-strong` 테두리 포함).
- 구절 텍스트 스타일은 `fontFamily: 'var(--serif)'`·`fontSize: 15.5`·`lineHeight: 1.8`·`color: 'var(--paper-ink)'`, 장절 라벨·보조 텍스트·닫기 버튼은 `var(--paper-accent)`. 언어 전환은 `frontend/src/VerseLangTabs.jsx` 공용 컴포넌트.

### 2.2 파일·컴포넌트 네이밍

- View/컴포넌트는 PascalCase `.jsx`: `App`·`MapView`·`SidePanel`·`TimelineView`·`RelationsView`·`BibleOverviewView`·`PersonHub`·`PersonIntro`·`FamilyTree`·`TourList`·`JourneyList`·`WordDistributionView`·`Spinner`·`VerseLangTabs`.
- 비컴포넌트 모듈은 camelCase `.js`: `api`·`theme`·`constants`·`dates`·`urlState`·`mapGeo`·`mapLayers`·`mapRingController`.
- 커스텀 훅은 `useXxx.js`: `useNodeSelection.js`(선택 노드·히스토리 상태), `useStageNavigation.js`(화면 단계·URL·브라우저 히스토리 상태 머신). App에서 무거운 상태 로직을 훅으로 추출하는 패턴.
- 매직 넘버는 `constants.js`에 명명 상수로(`MOBILE_BREAKPOINT`·`SHEET_VH`·`JOURNEY_SHEET_VH`).

### 2.3 API 클라이언트 = `apiGet`

- 모든 fetch는 `frontend/src/api.js`의 `apiGet(path, { signal })` 하나를 거친다. 베이스 URL은 `import.meta.env.VITE_API_URL || 'http://localhost:8000'` — 프로덕션은 빌드타임에 `/api`가 주입돼 nginx 프록시(`/api → api:8000`)를 탄다.
- 비-OK 응답은 `.status`를 단 `Error`를 throw. `AbortError`는 fetch에서 그대로 전파되며, 호출부가 `e?.name !== 'AbortError'`로 취소를 구분한다.

### 2.4 해시 기반 내비게이션 (라우터 라이브러리 없음)

- 라우팅 라이브러리 없이 `frontend/src/urlState.js`의 `encodeHash`/`parseHash`가 해시 URL ↔ 내비 상태를 순수 문자열로 매핑한다(`#/`, `#/books`, `#/book/<id>`, `#/family/<id>`, `#/words/<bookId>`, `#/person/<slug>`, `#/person/<slug>/timeline` 등). ADR-0009.
- `useStageNavigation.js`가 상태 머신 + 히스토리 동기화를 담당한다: 마운트 해시 1회 복원, 이후 stage/인물/시트 변경은 `pushState`, 뷰 토글·베이스는 `replaceState`, `popstate`로 뒤로/앞으로 복원(ADR-0010). 닫기·뒤로는 `window.history.back()`에 위임한다.
- 전체화면 페이지 스테이지는 **focus id를 selectedNode와 분리한 전용 상태**로 구동하는 것이 관례: `bookId`(책 상세)·`familyId`(가계도)·`wordsBookId`(단어 분포)가 동형. 페이지 내 대상 교체(트리 재중심화·드롭다운 책 전환)는 그 id만 바꾼다. 새 스테이지 추가 시 `encodeHash`/`parseHash`/`pushState` state 객체/`popstate` 복원/`useEffect` deps에 모두 배선한다(`useStageNavigation.js`의 words 배선이 최신 예).

### 2.5 빈값 폴백 = `console.warn` + `[Component]` prefix

- 비치명적 로드 실패는 조용히 폴백하고 `console.warn`으로만 기록한다. 실패해도 UI는 해당 요소만 빠진 채 동작한다.
- 메시지는 `[Component]` prefix로 시작한다: `[App]`·`[SidePanel]`·`[Timeline]`·`[JourneyList]`·`[Relations]`·`[PersonIntro]`·`[FamilyTree]`·`[WordDistribution]` (예외: `useStageNavigation.js`의 초기 2곳은 무prefix 잔존).
- `AbortError`는 폴백/경고에서 제외한다(`if (e?.name !== 'AbortError')`).

### 2.6 React 패턴 관례

- 참조 안정화를 위해 콜백은 `useCallback([...])`로 감싼다 — 인라인 화살표를 props로 넘기면 자식 effect(deps에 그 콜백)가 매 렌더 재실행돼 fetch가 abort되는 버그를 피한다(`useNodeSelection`·`useStageNavigation`의 주석 참조).
- 취소 가능한 fetch는 `AbortController` + `ctrl.abort()` 정리, 또는 `let cancelled = false` 가드 + 정리 함수.
- effect 안에서의 동기 setState는 피하고 `Promise.resolve().then(() => ...)`로 마이크로태스크에 미룬다(복원/초기화 로직).
- 최신값을 effect deps 없이 읽어야 할 땐 `useRef` 미러(`selectedNodeRef`).
- 컨테이너 크기 추적은 `useLayoutEffect` + `ResizeObserver`(`WordDistributionView.jsx`의 클라우드 폭).
- 아이콘은 `lucide-react`. `main.jsx`는 `<StrictMode>`로 감싼다.

### 2.7 린트·빌드

- 빌드는 Vite(`npm run build` → `frontend/dist/`), 린트는 ESLint flat config(`frontend/eslint.config.js`, `npm run lint`) — `@eslint/js` 권장 + `eslint-plugin-react-hooks` + `eslint-plugin-react-refresh`, `dist` 무시.
- TypeScript는 쓰지 않는다(`.jsx`, `@types/react`는 에디터 지원용 devDependency일 뿐). Prettier 설정 없음.

---

## 3. 데이터 저작

### 3.1 디렉터리·AUTHORING.md

- 저작 데이터는 `data/<도메인>/` 아래에 산다(`person_context`·`person_relations`·`character_traits`·`book_context`·`date_corrections`·`authored_persons`·`tours`·`names_ko` 등). 단일 파일 정본도 있다(`data/word_distribution.json`·`data/word_sentiment.json`).
- 규칙이 있는 도메인은 `data/<도메인>/AUTHORING.md`에 정본 저작 규칙(스키마·통제 어휘·검증 파이프라인)을 둔다: `data/person_context/AUTHORING.md`·`data/person_relations/AUTHORING.md`·`data/character_traits/AUTHORING.md`.

### 3.2 스크립트 접두사 taxonomy (`backend/scripts/`)

- `load_*` — 원본/저작 데이터를 Neo4j에 적재(`load_theographic.py`·`load_authored_genealogy.py`·`load_books.py` 등).
- `generate_*` — JSON을 파생/프리베이크(`generate_verse_text.py`가 getbible에서 본문을 받아 채움 등).
- `build_*` — 원본 텍스트에서 빌드타임 정본 JSON을 산출, Neo4j 미접근(`build_word_distribution.py` — kiwipiepy 형태소 분석으로 `data/word_distribution.json`을 씀, venv 별도 설치 필요. 극성 정본 `data/word_sentiment.json`에 미분류 단어가 있으면 `sys.exit`로 중단하는 게이트 내장, `--dump-words`로 미분류 목록 출력).
- `inject_*` — 저작 JSON을 읽어 기존 Neo4j 노드 속성에 `SET`(`inject_book_context.py`·`inject_person_traits.py`·`inject_date_corrections.py`).
- `validate_*` — 기계 검증, 위반 시 종료 코드 1(TESTING.md).
- `apply_*`/`enrich_*` — 병합·좌표 보강(`apply_event_dedupe.py`·`enrich_place_coords.py`).
- 스크립트 공통: Neo4j 접근 스크립트는 `NEO4J_*` 환경변수 읽기(비번 없으면 `RuntimeError`), 경로는 `os.path.dirname(__file__)`(또는 `Path(__file__).resolve().parents[2]`) 기준 상대 계산, 결과 건수를 `print`로 방출.

### 3.3 본문·파생물 프리베이크 분리 (ADR-0003)

- 저작자(LLM)는 **구절 참조만** 쓴다(`verse`/`ref`, 개역 약어 + "장:절"). `textKo`/`textEn`·`verseTextKo/En`·`contextKo/En` 같은 본문 필드는 **손으로 쓰지 않는다** — `generate_verse_text.py`가 getbible(개역 + KJV)에서 빌드타임에 채운다. AUTHORING.md들이 이를 반복 명시한다.
- 단어 분포도 같은 원칙: 런타임 형태소 분석 없이 `build_word_distribution.py`가 빌드타임에 `data/word_distribution.json`을 산출하고 `/words` API는 그 정본을 서빙만 한다(`routes/words.py` 주석).

### 3.4 에코 필드 멱등성 (inject 스크립트)

- 기존 노드 값을 덮어쓰는 inject는 각 항목에 **에코 필드**(수정 전 예상값)를 넣어 멱등·안전하게 만든다. `inject_date_corrections.py`가 정본 패턴: events 항목은 `title`/`oldStartDate`, persons 항목은 `name`/`oldValue`를 에코로 갖는다.
  - DB 현재값이 에코와 일치 → 교정 적용.
  - DB 현재값이 이미 `new*`와 일치(재실행) → "이미 적용"으로 조용히 통과.
  - 에코 불일치(예상 못 한 상태) → 스킵 + `[WARN]` 출력. 재실행 안전.
- 대량 제안 저작 시에도 에코 필드 + 기계검증 조합으로 잘못된 항목만 거부하고 나머지는 통과시키는 것이 관례(MEMORY 교훈).

### 3.5 노드 신원 마커 — `authored=true`·`status='wip'` (ADR-0008·0021·0022)

- 저작으로 신규 생성한 노드는 `MERGE (p:Person {theographic_id: $id}) SET p.authored = true`로 마킹한다(`load_authored_genealogy.py`). 원본 재적재(`load_theographic.py`)는 이 저작 간선/마커를 건드리지 않는다.
- `load_theographic.py`는 publish 레코드 외에 **가족 폐포 wip Person**도 적재한다(`family_closure_wip` — publish ∪ 큐레이션 rec 시드에서 가족 필드로 도달 가능한 wip만, 고아 섬 제외). wip은 `status: 'wip'` 속성으로 마킹하고(publish는 속성 미보유 = null), **노드·가족 간선에만** 포함한다 — memberOf·사건 참여 등 나머지 간선은 publish 전용.
- 큐레이션 rec id(사람이 검수한 신원, `data/person_events/<slug>.json`의 `events[0].participants[0]`)는 wip이어도 무마킹 — 검색 노출 유지(ADR-0022).
- 소비 측 계약: `search.py`가 `n.status IS NULL OR n.status <> 'wip'`로 wip을 검색에서 제외한다. wip 소비 로직을 추가할 땐 이 필터를 따른다.

### 3.6 런타임 오버레이 vs Neo4j 적재 (ADR-0004)

- 모든 저작 데이터가 Neo4j로 들어가는 건 아니다. `data/person_relations/relations.json`은 DB에 넣지 않고 `GET /person/{node_id}/relations`가 런타임 오버레이로 `slug` 매칭해 반환한다(`persons.py` `_load_relations`/`_build_relations`). book_events·event_verses·bible/verses·word_distribution·names_ko/books도 `overlays.py`가 파일에서 서빙한다.

### 3.7 통제 어휘는 문서·검증 스크립트 동시 갱신

- 저작 통제 어휘는 AUTHORING.md와 `validate_*.py`에 **이중으로** 산다. `data/character_traits/AUTHORING.md` §3의 미덕 24·결함 8 어휘는 `backend/scripts/validate_traits.py`의 `VIRTUES`/`FLAWS` 집합과 정확히 일치해야 하며, 어휘 확장 시 문서와 스크립트를 함께 고친다(스크립트 주석이 "문서와 함께 갱신할 것"으로 못 박음). 관계 유형 어휘표도 `RelationsView.jsx`의 `TYPE_ICON`/`TYPE_ORDER`와 일치시킨다.
- 단어 극성도 같은 구조: `data/word_sentiment.json`(word → positive|negative|neutral 큐레이션 정본)이 통제 어휘 역할을 하고, `build_word_distribution.py`가 미분류 단어를 게이트로 잡는다(§3.2).
