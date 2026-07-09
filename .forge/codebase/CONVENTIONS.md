---
last_mapped_commit: 232fba9c2c3724daf4ee250eba876f1e46f4b6d9
mapped: 2026-07-09
---

# CONVENTIONS

BibleMap은 백엔드(FastAPI + Neo4j, Python)·프론트엔드(React 19 + Vite, JS)·데이터(JSON 오버레이) 세 축으로 나뉘고, 각 축마다 별도의 관례를 따른다. 이 문서는 코드가 어떻게 작성되는지를 다룬다(도메인 용어 정의는 CONTEXT.md 소관).

---

## 1. 언어·포맷·린트 도구

- **백엔드**: Python (`backend/requirements.txt`는 `fastapi==0.136.3`, `neo4j==6.2.0`, `uvicorn==0.49.0`만 고정). **포매터·린터 설정 파일이 없다** — `pyproject.toml`·`ruff.toml`·`setup.cfg`·`.flake8` 모두 부재. 스타일은 파일 내 기존 코드를 눈으로 맞춘다.
- **프론트엔드**: JS + JSX. 린트는 ESLint flat config (`frontend/eslint.config.js`) — `@eslint/js` recommended + `eslint-plugin-react-hooks` flat recommended + `eslint-plugin-react-refresh` vite. `dist`는 `globalIgnores`로 제외. **Prettier·TypeScript 설정 파일 없음**(`@types/react`만 devDependency로 존재, 소스는 순수 JSX). 실행: `cd frontend && npm run lint`.
- **들여쓰기**: 백엔드 4-space, 프론트 2-space. 프론트는 **세미콜론 생략** 스타일(예: `frontend/src/api.js`), 문자열은 작은따옴표.

---

## 2. 명명 규칙

### 파일명

- **백엔드 라우트**: 리소스 복수형 소문자, `backend/app/routes/persons.py`·`places.py`·`events.py`·`books.py`·`tours.py`·`journey.py`·`search.py`·`nodes.py`. 각 파일은 `router = APIRouter()`를 노출하고 `backend/app/main.py`가 `app.include_router(...)`로 등록.
- **백엔드 스크립트**: `동사_명사.py` snake_case, 동사 접두어로 역할을 표시한다 — `load_*`(Neo4j 적재), `generate_*`(파생 데이터 생성), `inject_*`(Neo4j 속성 주입), `enrich_*`(보강). 예: `backend/scripts/load_theographic.py`, `backend/scripts/generate_verse_text.py`, `backend/scripts/inject_ko_names.py`.
- **프론트 컴포넌트**: PascalCase `.jsx` — `frontend/src/RelationsView.jsx`, `SidePanel.jsx`, `PersonHub.jsx`. 뷰 컴포넌트는 `*View.jsx` 접미어.
- **프론트 훅**: `use*.js` camelCase — `frontend/src/useStageNavigation.js`, `useNodeSelection.js`.
- **프론트 비-컴포넌트 모듈**: camelCase `.js` — `frontend/src/api.js`, `urlState.js`, `mapLayers.js`, `mapGeo.js`, `mapRingController.js`, `constants.js`, `dates.js`, `theme.js`.
- **데이터 인물 파일**: `data/person_events/<slug>.json`, slug는 snake_case (`john_the_baptist.json`, `john_the_apostle.json`).

### 식별자

- **Python 함수·변수**: snake_case. 모듈 사설(비공개)은 밑줄 접두어 — `_build_list()`, `_resolve()`, `_ERA`, `_NAME_KO`, `_ERA_ORDER` (`backend/app/routes/persons.py`).
- **Python 상수**: UPPER_SNAKE — `SEARCH_LIMIT = 20` (`search.py`), `MAX_NEIGHBORS_PER_TYPE = 30`·`NODE_NEIGHBOR_LIMIT = 50` (`nodes.py`). 매직 넘버는 파일 상단 모듈 상수로 뽑는다.
- **JS 함수·변수**: camelCase. 컴포넌트·컴포넌트-반환 함수는 PascalCase (`RelationsView.jsx`의 내부 `TypeIcon`, `VerseLayer`).
- **JS 모듈 상수**: UPPER_SNAKE — `MOBILE_BREAKPOINT`·`SHEET_VH`·`JOURNEY_SHEET_VH` (`constants.js`), `VALENCE_COLOR`·`TYPE_ICON`·`TYPE_ORDER` (`RelationsView.jsx`), `API_BASE` (`api.js`).
- **API JSON 키**: **camelCase**. 백엔드가 Neo4j snake_case 속성을 camelCase 응답 키로 변환한다 — 예: `theographic_id` → `id`, `nameKo`, `nameKoMissing`, `neighborTotal`, `eventCount`, `coParticipants` (`nodes.py`, `persons.py`).

---

## 3. Import 정리

- **백엔드**: 표준 라이브러리 → 서드파티(`fastapi`, `neo4j`) → 로컬 상대 import 순. 로컬은 상대 경로 — `from ..db import get_driver`, `from ..overlays import _resolve` (`backend/app/routes/persons.py`). 지연 import를 의도적으로 쓰는 곳이 있다: 무거운/순환 위험 모듈은 함수 안에서 import (`main.py` lifespan의 `from .db import get_driver`, `nodes.py`의 `import json as _json`).
- **프론트엔드**: React 훅 → 서드파티(`lucide-react`, `maplibre-gl`) → 로컬 모듈 순, 모두 상대 경로. 경로 별칭(`@/`) 없음. 예: `frontend/src/RelationsView.jsx` 1~5행.

---

## 4. 백엔드 라우트 패턴

- **핸들러 시그니처**: `@router.get("/path/{node_id}")` 데코레이터 + 함수. 경로 파라미터는 타입 힌트로 받는다(`node_id: str`). 쿼리 파라미터는 `Query(...)` — `def search(q: str = Query(""))` (`search.py`).
- **Neo4j 세션**: 매 핸들러가 `driver = get_driver()` → `with driver.session() as session:` 컨텍스트 매니저로 연다. 드라이버는 `backend/app/db.py`의 모듈 전역 싱글턴 `_driver`(lazy init).
- **Cypher 쿼리**: 파라미터는 항상 바인딩(`$id`, `$q`)해 문자열 인터폴레이션으로 값을 넣지 않는다. **상수(limit·label)만** f-string으로 쿼리에 삽입한다 — 예: `nodes.py`의 `[0..{NODE_NEIGHBOR_LIMIT}]`, `f"CREATE INDEX {label.lower()}_tid ..."` (`main.py`). 사용자 입력은 절대 f-string에 넣지 않는다.
- **결과 매핑**: `dict(record["n"])`로 노드 속성을 뽑고, `props.get("name") or props.get("title", "")` 폴백 체인으로 이름을 얻는다. `nameKo`가 없으면 `name`으로 폴백하고 `nameKoMissing: name_ko is None` 플래그를 함께 실는다(프론트가 미번역을 표시). 이 폴백 패턴은 `nodes.py`·`search.py` 전반에 반복된다.
- **응답 형태**: 기본은 dict/list를 그대로 return(FastAPI 자동 JSON). **캐시가 필요한 정적 엔드포인트**는 `JSONResponse(content=..., headers={"Cache-Control": "max-age=300"})`로 직접 감싼다 (`persons.py`의 `/persons/curated`·`/person/{id}/connections`·`/relations`).
- **에러**: 노드 미발견은 `raise HTTPException(status_code=404, detail="Node not found")` (`nodes.py`). 성공 폴백형 엔드포인트(관계 없음 등)는 예외 대신 **빈 배열/빈 dict를 반환**한다 (`persons.py` `_build_relations`는 미큐레이션 id에 `{"relations": []}`).
- **N+1 회피 주석**: 왕복을 줄인 쿼리에는 이유를 주석으로 남긴다 — `nodes.py`의 "이웃 조회 + 총수 — 단일 쿼리로 2 → 1 왕복".

---

## 5. 캐싱 규약 (백엔드)

- 파일 오버레이·파생 카탈로그는 `@functools.lru_cache`로 프로세스 기동 시 1회 로드한다 — `overlays.py`의 `book_events_raw()`·`event_verses()`(`maxsize=1`), `persons.py`의 `_build_list()`(`maxsize=1`)·`_load_relations()`(`maxsize=1`)·`_build_connections(node_id)`·`_build_relations(node_id)`(`maxsize=None`, id별 메모).
- **footgun**: 데이터 JSON은 컨테이너에 마운트 오버레이라 재빌드가 불필요하지만, `lru_cache`가 메모리에 캐시하므로 데이터를 바꾼 뒤에는 **`docker compose restart api`로 캐시를 비워야** 새 데이터가 서빙된다(`data/person_relations/AUTHORING.md` 규칙 8-3). `docker compose up -d api`는 config 무변경 시 컨테이너를 재생성하지 않는다.

## 6. 데이터 접근 오버레이 규약

- 데이터 파일은 `backend/app/overlays.py`의 `_resolve(subpath)`/`_resolve_dir(subpath)`로 찾는다. 우선순위: `$DATA_DIR`(기본 `/app/data`, 컨테이너 마운트) → 리포 내 `data/`(로컬 개발). 없으면 `None` 반환.
- JSON 로드는 `_load()`가 감싸며 `json.JSONDecodeError`는 빈 dict로 삼킨다(파일 부재·파손에 방어적).

---

## 7. 프론트엔드 컴포넌트 패턴

- **함수 컴포넌트 + 훅 전용**. 클래스 컴포넌트·상태 라이브러리(Redux/Zustand) 없음. React 19.
- **상태 관리**: `useState`/`useEffect`/`useRef`/`useCallback`/`useMemo`. 전역 상태는 최상위 `App.jsx`가 소유하고 props로 내려보낸다(prop drilling). 복잡한 상태 머신은 커스텀 훅으로 추출 — 화면 단계·URL·히스토리는 `useStageNavigation.js`, 노드 선택은 `useNodeSelection.js`.
- **fetch effect 패턴**: 데이터 로딩 effect는 취소 가드를 반드시 붙인다. 두 가지 관용구가 공존한다:
  - `let cancelled = false` 플래그 + cleanup에서 `cancelled = true` (`RelationsView.jsx` 26~33행).
  - `AbortController` + `ctrl.abort()` cleanup, `.catch`에서 `e?.name !== 'AbortError'`로 취소를 구분 (`App.jsx` 56~70행). `api.js`의 `apiGet(path, { signal })`가 signal을 지원한다.
- **stale 응답 가드**: 응답을 세팅하기 전 요청 id와 현재 id를 비교한다 — `RelationsView.jsx`의 `setState({ id: personId, relations })` 후 `if (state.id !== personId)` 로딩 표시.
- **effect 동기 setState 금지**: effect 안에서 곧바로 setState 하지 않고 `Promise.resolve().then(() => ...)`로 마이크로태스크에 미루는 규칙이 있다(`useStageNavigation.js` 62·111행, `App.jsx` 68행 주석 "effect 동기 setState 금지 규칙").
- **콜백 참조 안정화**: 자식에 넘기는 콜백이 자식 effect의 dep이면 `useCallback`으로 감싼다 — 인라인 화살표면 매 렌더 새 ref가 되어 자식 effect가 재실행되는 버그(`useStageNavigation.js`의 `onNodeLoaded` 183~189행 주석).
- **의도적 exhaustive-deps 예외**: 마운트 1회 등록·복원 1회 effect는 `// eslint-disable-next-line react-hooks/exhaustive-deps`로 dep을 좁히고, **왜 제외했는지 주석을 반드시 남긴다**(`useStageNavigation.js` 78·123행).

## 8. 스타일링 (CSS)

- **인라인 스타일 우선**. 대부분의 UI는 JSX `style={{ ... }}` 객체로 스타일링한다(`RelationsView.jsx` 전반). 색상은 컴포넌트 상단 상수 팔레트로 뽑아 재사용(`VALENCE_COLOR`).
- **전역 CSS는 `frontend/src/index.css` 하나뿐**(64줄). CSS 변수(`:root`의 `--text`·`--bg`·`--sans`), `prefers-color-scheme: dark` 대응, 그리고 인라인으로 표현 못 하는 것(`:active`·`@keyframes`·`.rel-chip` 누름 피드백)만 담는다. CSS Modules·styled-components·Tailwind 없음.
- **애니메이션**: 인라인 불가한 `@keyframes`는 컴포넌트가 `<style>` 태그로 주입한다(`Spinner.jsx`).
- **반응형**: JS 미디어쿼리(`window.matchMedia`)로 모바일 분기를 판단하고 `constants.js`의 `MOBILE_BREAKPOINT`를 단일 출처로 쓴다(`App.jsx` 16~17행).

## 9. 라우팅 (프론트)

- 라우팅 라이브러리 없음. `frontend/src/urlState.js`가 해시 URL ↔ 내비 상태를 순수 문자열 매핑으로 처리한다(`encodeHash`/`parseHash`). 히스토리 통합·popstate는 `useStageNavigation.js`. 미지 해시는 `parseHash`가 `null` 반환 → 호출부가 허브로 폴백.

---

## 10. 주석 규약

- **한국어 평서체**(–한다체)로 쓴다. 코드 전반이 한글 주석. "왜"를 설명하고, 특히 과거에 물렸던 함정(footgun)·회귀 원인을 명시한다 — 예: `useStageNavigation.js`의 "과거 두 차례 런타임 크래시 원인", `generate_verse_text.py`의 "getbible UA 우회(retro 2026-06-15 교훈)", AUTHORING.md 규칙 8의 재시작 footgun.
- **모듈/함수 docstring**: Python은 파일·함수 최상단 `"""..."""` docstring으로 책임과 계약을 적는다(`persons.py` 파일 헤더, `_build_connections`·`_build_relations` docstring, `generate_verse_text.py` 20줄 헤더에 대상 파일·필드·사용법). 설계 결정은 `ADR-000N` 번호로 인용한다(`ADR-0003`·`ADR-0004`·`ADR-0006`·`ADR-0009`·`ADR-0010`).
- **프론트**: JSDoc 태그(`@param` 등)는 쓰지 않는다. 일반 `//` 한 줄/블록 주석으로 의도를 적는다. 섹션 구분은 JSX 안에서 `{/* ... */}`.

## 11. 데이터 저작 규약

- **정본 규칙 문서**: `data/person_relations/AUTHORING.md` — 인물 관계 데이터 저작의 정본. 새 인물 관계를 만들 때 반드시 따른다.
- **핵심 저작 원칙**:
  - **저작 vs 프리베이크 분리**: 저작자는 `verse`(개역 약어 + "장:절", 예 `삼상 16:13`)·`context`(같은 장 내 "장:절-절" 범위)만 손으로 쓴다. 본문 필드(`verseTextKo`/`verseTextEn`·`contextKo`/`contextEn`)는 **절대 손으로 쓰지 않고** `backend/scripts/generate_verse_text.py`가 빌드타임에 getbible(한국어 개역 + KJV)에서 받아 채운다(멱등, ADR-0003).
  - **정본 pair·중복 금지**: 관계는 pair당 1개만 저장한다. 두 endpoint가 모두 큐레이션이면 백엔드 slug 매칭으로 양쪽 상세에 자동으로 뜬다 — 기존 pair를 재생성하지 말고 재사용한다.
  - **valence는 국면(phase)마다, type은 관계마다**(직교). 시간에 따른 변화는 `phases` 배열로 표현하고 `approxYear` 오름차순 정렬(BC는 음수).
  - **밀도 비례·공백 강요 금지**: 서사가 뒷받침하고 valence를 가진 관계만 저작한다. 억지 관계 금지.
  - **slug 일치**: endpoint의 `slug`는 `backend/app/routes/persons.py`의 `_NAME_KO` 큐레이션 로스터와 정확히 일치해야 한다. 관계 유형(`type`)은 `frontend/src/RelationsView.jsx`의 `TYPE_ICON`/`TYPE_ORDER`와 일치해야 한다(미등록 유형은 아이콘 없이 렌더).
- **JSON 스타일**: 2-space 들여쓰기, `data/person_relations/relations.json`은 `{ "relations": [ ... ] }` 단일 파일에 append. person_events는 파일당 이벤트 배열.

---

## 12. 환경변수·시크릿

- 시크릿 값은 코드/문서/커밋에 절대 넣지 않는다. **이름으로만** 참조: `NEO4J_URI`·`NEO4J_USER`·`NEO4J_PASSWORD`(백엔드, `db.py`가 `NEO4J_PASSWORD` 미설정 시 `RuntimeError`), `DATA_DIR`(오버레이 경로), `VITE_API_URL`(프론트 빌드타임 주입, 프로덕션은 `/api`). 로컬 값은 git-ignored `.env`에, 예시는 `.env.example`에 둔다.

---

*Convention analysis: 2026-07-09*
