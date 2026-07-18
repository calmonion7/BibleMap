---
last_mapped_commit: 304eda1c53acff4c4860b838e8627483c666f74c
mapped: 2026-07-18
---

# CONVENTIONS

BibleMap의 코드 스타일·품질 관련 정본. 라우팅 구조·DB 접근·네이밍·React 훅 패턴은 `ARCHITECTURE.md`/`STRUCTURE.md` 소관 — 여기는 **로깅, 에러 처리, 오버레이 데이터 저작 분리, CSS 토큰/테마**만 다룬다. 도메인 용어 정의는 CONTEXT.md 소관.

---

## 1. 백엔드 로깅 방출 규약

- 모듈마다 `logger = logging.getLogger(__name__)`. `backend/app/` 안에서 `print()`·root 로거 직호출 금지(`print`는 `backend/scripts/`에서만 — 아래 §3 참조).
- 메시지는 `[Component]` prefix로 시작한다: `[Startup]`(`backend/app/main.py`)·`[Overlays]`(`backend/app/overlays.py`)·`[Persons]`·`[Places]`·`[Tours]`·`[Nodes]`(각 `backend/app/routes/*.py`).
- 빈값 폴백(오버레이 파일/디렉터리 없음, JSON 파싱 실패, participants 비어 있음)은 `logger.warning`, 기동 예외는 `logger.exception`. 포맷은 lazy `%s` 스타일이며 문자열 f-string을 넣지 않는다. 실측 예:
  - `backend/app/overlays.py`: `logger.warning("[Overlays] 오버레이 파일 없음 — 빈 데이터로 폴백 (%s, 시도: %s)", subpath, bases)`
  - `backend/app/routes/nodes.py`: `logger.warning("[Nodes] Person traits 파싱 실패 — 빈 목록 폴백 (%s): %s", node_id, e)`
  - `backend/app/routes/tours.py`: `logger.warning("[Tours] 투어 파일 로드 실패 — 목록에서 건너뜀 (%s): %s", os.path.basename(path), e)`
  - `backend/app/main.py` lifespan: `logger.exception("[Startup] Neo4j 인덱스 생성 실패 — 인덱스 없이 계속 진행")`
- `backend/app/main.py`의 `_configure_logging()`이 **라우터 import 전**(모듈 최상단, `from .routes import ...` 이전) 1회 호출된다: `logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")`, 수다스러운 서드파티(`neo4j`/`urllib3`/`asyncio`)는 `setLevel(logging.WARNING)`으로 승격, `uvicorn`·`uvicorn.access`는 `propagate = False`로 root 중복 emit을 차단한다 — 단 `uvicorn.error`는 제외한다(자체 핸들러가 없어 propagate를 끊으면 기동/에러 라인이 통째로 사라지기 때문. 코드 주석에 이 이유가 명시돼 있다).
- 새 라우터를 추가할 때는 파일 상단에서 자기 모듈 이름의 `[Component]` prefix를 하나 정하고 그 파일 전체에서 일관되게 쓴다(예: `verses.py`가 `logger = logging.getLogger(__name__)`만 선언해두고 실제 경고 발생 지점이 없는 것도 관례상 허용 범위 — 경고할 실패 케이스가 없으면 로거만 준비해둔다).

---

## 2. 프론트 빈값 폴백 = `console.warn` + `[Component]` prefix

- 비치명적 로드 실패(fetch 실패, 하위 리소스 없음)는 조용히 폴백하고 `.catch(e => ...)` 안에서 `console.warn`으로만 기록한다. 실패해도 UI는 해당 요소만 빠진 채 나머지는 정상 동작한다 — `console.error`는 실제 프로그래밍 오류(잘못된 타입 전달 등, 예: `frontend/src/TimelineView.jsx:41`의 `personFilter must be a Set` 방어 로그) 1건에만 쓰이는 예외 케이스다.
- 메시지는 `[Component]` prefix로 시작한다. 실측 예(2026-07-18 기준):
  - `frontend/src/App.jsx`: `console.warn('[App] 인물 여정 로드 실패', e)`, `console.warn('[App] 책 목록 로드 실패 — 정경 내비 미노출', e)`
  - `frontend/src/SidePanel.jsx`: `console.warn('[SidePanel] 인용 관계 로드 실패', e)`(task#210 인용 관계 UI도 동일 패턴 재사용), `console.warn('[SidePanel] 인물 연결 로드 실패', e)`
  - `frontend/src/ChapterReader.jsx`(신규): `console.warn('[ChapterReader] 장 본문 로드 실패', e)`
  - `frontend/src/FamilyTree.jsx`·`RelationsView.jsx`·`RelianceView.jsx`·`WordDistributionView.jsx`·`PersonMiniCard.jsx`·`PersonIntro.jsx`·`JourneyList.jsx` 모두 동형.
  - 예외(prefix 없음, 잔존): `frontend/src/useStageNavigation.js`의 두 곳(`/persons/curated 로드 실패 — ...`, `/keypeople-cards 로드 실패 — ...`) — 새 코드는 prefix를 갖추되, 이 두 줄은 발견 시 별건으로만 고친다.
- 취소 판정은 두 가지 관용구가 공존한다: `if (e?.name !== 'AbortError')`(`AbortController` 기반, `MapView.jsx`·`RelianceView.jsx`·`WordDistributionView.jsx`·`FamilyTree.jsx`·`ChapterReader.jsx`·`PersonMiniCard.jsx`)와 `if (!cancelled)`(`let cancelled = false` 클로저 가드, `App.jsx`·`PersonIntro.jsx`·`RelationsView.jsx`·`SidePanel.jsx`·`WordDistributionView.jsx`의 다른 fetch). 어느 쪽이든 취소된 요청의 실패는 경고하지 않는다. `frontend/src/api.js` 상단 주석이 이 계약을 명시한다: "요청 취소(AbortError)는 fetch에서 그대로 전파 — 호출부가 `e.name === 'AbortError'`로 구분한다."
- 실패 상태를 화면에 노출할 땐 전용 불리언 state(`failed`)를 두고 인라인으로 안내 문구를 렌더한다 — 공용 배너 컴포넌트는 없음. 실측: `frontend/src/RelianceView.jsx` `{failed && <div style={{ color: 'var(--danger)', fontSize: 13 }}>의존도를 불러오지 못했습니다.</div>}`, `frontend/src/WordDistributionView.jsx` 동형. `frontend/src/MapView.jsx`는 `error`/`noLocation` 두 불리언을 분리해 지도 위 배너로 각각 렌더한다.

---

## 3. 오버레이 데이터 저작 패턴 — LLM 저작 ↔ 기계 검증 분리

**핵심 원칙**: 저작(사람/LLM이 쓰는 콘텐츠)과 검증(스크립트가 규칙을 강제)을 서로 다른 파일·다른 실행 시점으로 분리한다. 저작자는 원문 스키마만 채우고, `validate_*.py`가 사후에 불변식을 전수 검사한다. 위반이 있어도 통과 대상은 통과시키고 위반 항목만 골라 보고하는 것이 관례(항목 단위 게이트).

### 3.1 오버레이 파일 접근 — `backend/app/overlays.py`

- `_resolve(subpath)`/`_resolve_dir(subpath)`는 `DATA_DIR` 환경변수(기본 `/app/data`, 컨테이너 마운트) → 리포지토리 `data/` 순으로 파일/디렉터리를 찾고, 없으면 `logger.warning` 후 `None`을 반환한다(§1의 로깅 규약과 동일 계약).
- `_load(subpath)`는 파일 없음·JSON 파싱 실패 모두 `logger.warning` 후 빈 dict로 폴백한다 — 오버레이 결손이 500 에러가 되지 않게 한다(§4의 에러 처리 원칙과 직결).
- 새 오버레이는 `overlays.py`에 `@functools.lru_cache(maxsize=1)` 로더 함수를 추가한다. 최근 추가분: `chapter_summaries()`(`data/chapter_summaries/books.json`)·`chapter_sections()`(`data/chapter_sections/books.json`)·`quotations()`(`data/quotations/quotations.json`, 리스트 반환)·`verse_persons()`(`data/verse_persons/index.json`) — 기존 `book_events_raw`/`event_verses`/`bible_verses`/`word_distribution`/`books_ko`와 동일 패턴.

### 3.2 저작 규칙 문서 — `data/<도메인>/AUTHORING.md`

- 규칙이 있는 저작 도메인은 `data/<도메인>/AUTHORING.md`에 스키마·통제 어휘·검증 파이프라인을 정본으로 둔다: `data/person_context/AUTHORING.md`·`data/person_relations/AUTHORING.md`·`data/character_traits/AUTHORING.md`·`data/god_reliance/AUTHORING.md`.
- 본문 필드(`textKo`/`textEn` 등)는 저작자가 손으로 쓰지 않는다 — 저작자는 **구절 참조만**(`verse`/`ref`, 개역 약어 + "장:절") 쓰고, `backend/scripts/generate_verse_text.py` 같은 빌드타임 스크립트가 getbible에서 본문을 채운다. 이 분리는 통제 어휘·연대·인용 저작에도 반복 적용된다.

### 3.3 통제 어휘는 문서·검증 스크립트 동시 갱신

- 저작 통제 어휘는 AUTHORING.md와 대응하는 `validate_*.py`에 **이중으로** 산다. 예: `data/character_traits/AUTHORING.md`의 미덕 24·결함 8 어휘는 `backend/scripts/validate_traits.py`의 `VIRTUES`/`FLAWS` 집합과, `data/god_reliance/AUTHORING.md`의 `mode` 5종(`물음-응답`·`물음-침묵`·`독단-개입`·`독단-어긋남`·`부르심`)은 `backend/scripts/validate_god_reliance.py`의 `MODES` 집합과 정확히 일치해야 한다. 어휘 확장 시 문서와 스크립트를 함께 고친다(스크립트 주석이 "문서와 함께 갱신할 것"을 명시).

### 3.4 에코 필드 멱등성 (inject 스크립트)

- 기존 노드 값을 덮어쓰는 `inject_*.py`는 각 항목에 **에코 필드**(수정 전 예상값)를 넣어 멱등·안전하게 만든다. `backend/scripts/inject_date_corrections.py`가 정본 패턴: DB 현재값이 에코와 일치하면 교정 적용, 이미 새 값이면 조용히 통과, 에코 불일치(예상 못 한 상태)면 스킵 + `[WARN]` 출력.
- 대량 저작 시에도 이 "에코 필드 + 기계검증" 조합으로 잘못된 항목만 거부하고 나머지는 통과시키는 것이 관례다(예: `backend/scripts/validate_quotations.py`가 verseID 미실존·측 위반·라벨 자기불일치·중복 쌍을 각각 독립 항목으로 거부).

### 3.5 대량 병렬 저작 = 저작 에이전트는 파일 미접촉

- 수백~수천 항목의 병렬 저작은 **저작 에이전트가 파일을 직접 만지지 않고 JSON만 반환**하고, 별도 병합 스크립트가 기계검증 후 정본 파일에 반영하는 구도를 쓴다. 정본 예시는 `.forge/scratch/task203/validate_and_merge.py`(사건 근거 구절 반영)·`.forge/scratch/genealogy-authoring/`의 `s1_classify.py`/`merge_validate.py`(가계도 전원 저작). 저작 프롬프트에는 근거 인정 경계와 "스킵 허용"을 항상 명시해 억지 인용을 막는다.
- 2026-07-18(`장 묶음` 저작, task#212) 회고에서 확인된 이 구도의 실전 이점: 계정 사용량 한도로 병렬 워크플로가 중도 실패해 절반은 서브에이전트, 절반은 메인 세션이 직접 저작했지만 **저자가 누구든 `validate_chapter_sections.py`가 61권 전수 불변식을 보증**해 산출물 품질에 차이가 없었다(`.forge/retro/2026-07-18-chapter-sections.md`).

---

## 4. 에러 처리

- **백엔드**: 알 수 없는 리소스 id는 `raise HTTPException(status_code=404, detail="...")`로 답한다(`backend/app/routes/books.py`의 unknown book, `backend/app/routes/nodes.py`의 Node not found, `backend/app/routes/words.py`의 unknown book). 그 밖의 파싱/파일 실패는 예외를 올리지 않고 §1·§3.1의 로깅 + 빈 값/빈 목록 폴백으로 흡수한다 — 오버레이 결손이나 JSON 파싱 실패가 500으로 전파되지 않는 것이 원칙(`backend/app/routes/nodes.py`의 traits/verses JSON 파싱 `except Exception as e: logger.warning(...); clean_props["traits"] = []`가 대표 패턴).
- **프론트**: fetch 에러는 §2의 `console.warn` + 폴백 state로 흡수한다. `AbortError`(요청 취소)는 에러가 아니므로 경고·폴백 모두에서 제외한다. 사용자에게 실패를 알려야 하는 화면은 전용 `failed` 불리언으로 인라인 안내를 렌더하고(§2 말미), 지도처럼 이미 진행 중인 렌더를 막지 않아야 하는 화면은 부분 실패를 별도 배너로 얹는다.
- **로더/빌더 스크립트**(`backend/scripts/`)는 반환값이 아니라 프로세스 종료 코드로 실패를 알린다: 사슬 단절·건수 불일치 등은 `raise SystemExit("FAIL: ...")`(`load_authored_genealogy.py`·`load_authored_mothers.py`), 통제 어휘 미분류가 있으면 `sys.exit(...)`로 산출을 중단(`build_word_distribution.py`) — 상세는 `TESTING.md` §1·§2.

---

## 5. CSS 토큰 / 듀얼 테마

### 5.1 인라인 스타일 + CSS 변수 (CSS 라이브러리 없음)

- CSS Module·styled-components·Tailwind 등을 쓰지 않는다. 컴포넌트는 `style={{ ... }}` 인라인 객체로 스타일링한다(`frontend/src/App.jsx`·`frontend/src/SpineHeader.jsx`가 대표적).
- 디자인 토큰의 단일 출처는 `frontend/src/index.css`의 `:root` 커스텀 프로퍼티: `--bg-0..3`·`--line`/`--line-strong`·`--ink`/`--ink-dim`/`--ink-faint`·`--gold`/`--gold-dim`·`--paper*`·`--type-*`(6종)·`--valence-*`(3종)·`--select-hl`·`--danger`·`--r-s/m/l`·`--shadow-1/2`·`--z-verse`/`--scrim`·`--serif`/`--sans`·모션 토큰 `--dur-*`/`--ease-*`(§5.3). 인라인 스타일은 `var(--gold)` 식으로 참조한다.
- 알파 결합은 hex 이어붙임 대신 `color-mix(in srgb, ${color} 13%, transparent)`를 쓴다(var() 참조도 받음 — `frontend/src/Spinner.jsx`·`SpineHeader.jsx`).
- 클래스가 필요한 특수 케이스만 `index.css`에 둔다: `.rel-chip`·`.pressable`(`:active` — 인라인 background/transform이 이기는 특이성 문제 회피), keyframe 애니메이션 클래스.

### 5.2 다크 기본 + 라이트 옵트인 (ADR-0020)

- 다크(Night Atlas)가 기본, 라이트(Day Atlas)는 옵트인. 같은 토큰 계약에 값만 두 벌 — `index.css`의 `:root`(다크) + `:root[data-theme='light']` 오버라이드 블록(각각 `color-scheme` 선언 포함).
- 테마 상태의 정본은 `localStorage`의 `biblemap-theme` 키 + `document.documentElement.dataset.theme`. `frontend/src/main.jsx`가 **렌더 전에 동기 반영**해 첫 페인트 깜빡임을 막는다. 토글(`frontend/src/SpineHeader.jsx`)은 React 리렌더 없이 `dataset.theme`을 직접 조작한다(색이 전부 CSS 변수라 충분).
- 테마 불변 영역: 양피지(`--paper`/`--paper-ink`/`--paper-accent`, 성경 구절 본문 전용 배경)와 지도(`frontend/src/MapView.jsx`·`frontend/src/mapLayers.js`의 리터럴 색) — 라이트 블록에 이 토큰들의 오버라이드는 없다.
- 새 색을 넣을 땐 테마 민감한 색이면 `index.css` 두 블록 모두에 토큰을 정의하고 var로 참조한다. 에러색은 `--danger`(§4의 실패 배너가 실사용 예). 라이트 값은 명도를 낮춰 대비를 확보한다(본문 4.5:1·칩 3:1 목표).
- JS 팔레트 상수는 `frontend/src/theme.js`(`TYPE_COLOR`/`TYPE_KO`/`TYPE_ORDER`/`VALENCE_COLOR`/`SELECT_HL`/`GENRE_META`) — 값의 정본은 `index.css`의 `--type-*`/`--valence-*`이고 `theme.js`는 `'var(--type-person)'` 같은 **var 참조 문자열**만 갖는다(인라인 style 전용, 캔버스/maplibre류에는 못 씀).

### 5.3 모션 토큰 (ADR-0024)

- 모션 정본은 `index.css` `:root`의 `--dur-fast`(150ms)/`--dur-base`(250ms)/`--dur-slow`(400ms)/`--dur-draw`(1000ms) + `--ease-out`/`--ease-in-out`/`--ease-drawer`/`--ease-pop`. 새 duration·easing을 리터럴로 하드코딩하지 않고 이 토큰만 참조한다.
- 애니메이트 가능한 속성은 **transform·opacity**(+ 선화의 `stroke-dashoffset`)만 — 레이아웃 속성 금지. 입장(enter)만 만들고 exit는 즉시 언마운트로 처리한다.
- `@media (prefers-reduced-motion: reduce)`에서 `--dur-*` 전부와 `animation-delay`를 1ms/0ms로 붕괴시키는 **토큰 붕괴 가드**가 개별 컴포넌트의 reduce 분기를 대체한다(`index.css`). CSS 트랜지션이 아닌 JS `requestAnimationFrame` 애니메이션(`RelianceView.jsx`의 `Donut`)은 이 가드로 가려지지 않아 `window.matchMedia(...)`를 직접 분기한다.
- 정본 참조: `.forge/adr/0024-motion-system-css-tokens-no-library.md`.

### 5.4 인물/책 상징물 선화 (ADR-0025)

- 인물·책 대표 이미지는 얼굴 초상/외부 이미지가 아니라 **손저작 stroke-only SVG 선화**다. 정본은 `frontend/src/personSymbols.jsx`의 `SYMBOLS`(인물, slug 키)와 `frontend/src/bookSymbols.jsx`의 `SYMBOLS`(책, theographic_id 키 — 책은 slug가 없음).
- 공통 저작 규격: `viewBox 64×64`, `stroke="currentColor"`(듀얼 테마 자동 추종), `strokeWidth 2`, fill 없음, 모든 stroke 요소에 `pathLength={1}`(`.symbol-draw`의 dash 1 = 전체 선 draw-on 전제). 미등록 키는 범용 폴백 인장으로 렌더해 부분 저작 상태에서도 화면이 깨지지 않는다.
