---
last_mapped_commit: 232fba9c2c3724daf4ee250eba876f1e46f4b6d9
mapped: 2026-07-09
---
<!-- refreshed: 2026-07-09 -->
# ARCHITECTURE

**Analysis Date:** 2026-07-09

## System Overview

BibleMap은 세 개의 컨테이너 서비스로 구성된다(`docker-compose.yml`). Neo4j 그래프 DB가 정경 그래프(인물·장소·사건·책)를 담고, FastAPI 백엔드가 그 그래프 + JSON 오버레이(`data/`)를 병합해 읽기 전용 API로 노출하며, Vite/React SPA를 nginx가 정적 서빙하면서 `/api/`를 백엔드로 프록시한다.

```text
┌─────────────────────────────────────────────────────────────┐
│                    브라우저 (React SPA)                        │
│   `frontend/src/App.jsx` — Stage 상태머신 + 뷰 렌더           │
│   MapView / TimelineView / RelationsView / SidePanel …        │
└───────────────────────────┬─────────────────────────────────┘
                            │ fetch(API_BASE + path)  `frontend/src/api.js`
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    nginx (`nginx/nginx.conf`)                 │
│   `/`  → frontend/dist 정적 서빙 (SPA try_files)              │
│   `/api/` → proxy_pass http://api:8000/                       │
└───────────────────────────┬─────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│               FastAPI 백엔드 (`backend/app/`)                 │
│   main.py (앱+lifespan+라우터 등록)                           │
│   routes/*.py  ─── db.py (Neo4j 드라이버) ── overlays.py      │
│                     (Cypher 쿼리 계층)   (JSON 오버레이 로더) │
└──────────┬──────────────────────────────────┬───────────────┘
           │ bolt://neo4j:7687                 │ 파일 읽기
           ▼                                   ▼
┌────────────────────────┐         ┌──────────────────────────┐
│   Neo4j (그래프 DB)    │         │  JSON 오버레이 (`data/`)  │
│   Person/Place/Event/  │         │  person_events·relations· │
│   Book/PeopleGroup     │         │  event_verses·tours …     │
└────────────────────────┘         └──────────────────────────┘
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| FastAPI 앱 | 앱 생성·CORS·lifespan(인덱스 보장)·라우터 등록 | `backend/app/main.py` |
| Neo4j 드라이버 | 싱글턴 드라이버 lazy 생성(`get_driver`) | `backend/app/db.py` |
| 오버레이 로더 | `data/*.json` 경로 해석·로드·lru_cache | `backend/app/overlays.py` |
| 노드 라우터 | 노드 상세·이웃·장소·Book 상위 인물/사건 | `backend/app/routes/nodes.py` |
| 인물 라우터 | 큐레이션 인물 목록·연결·관계(관계 뷰 데이터) | `backend/app/routes/persons.py` |
| 여정 라우터 | 인물 시간순 정차지(좌표 배치조회) | `backend/app/routes/journey.py` |
| 사건 라우터 | 타임라인 사건 목록·사건 근거 구절 | `backend/app/routes/events.py` |
| 투어 라우터 | 테마 투어 목록·상세(event-ref 오버레이) | `backend/app/routes/tours.py` |
| 장소 라우터 | 장소를 지나는 큐레이션 인물 | `backend/app/routes/places.py` |
| 책 라우터 | 개요 뷰 전체 책 목록 | `backend/app/routes/books.py` |
| 검색 라우터 | nameKo/name CONTAINS 검색 | `backend/app/routes/search.py` |
| SPA 진입 | Stage 렌더 트리·상세 패널·여정 fetch | `frontend/src/App.jsx` |
| Stage 상태머신 | 단계·URL 해시·브라우저 히스토리 동기화 | `frontend/src/useStageNavigation.js` |
| 노드 선택 | 선택 노드·히스토리·personEventIds | `frontend/src/useNodeSelection.js` |
| 지도 | MapLibre GL 지도·여정 라인·사건 링 | `frontend/src/MapView.jsx` + `map*.js` |
| 관계 뷰 | 관계 레인 개요·초점 쌍·근거 구절 레이어 | `frontend/src/RelationsView.jsx` |

## Pattern Overview

**Overall:** 그래프 백본 + JSON 오버레이 병합 위에 얹은 읽기 전용 REST API, 그리고 라우팅 라이브러리 없이 해시 딥링크로 구동되는 단일 페이지 Stage 상태머신.

**Key Characteristics:**
- 백엔드는 **읽기 전용**이다. CORS는 `allow_methods=["GET"]`만 허용(`backend/app/main.py:29`). 쓰기는 전부 `backend/scripts/`의 오프라인 로더/인젝터가 담당한다.
- **그래프(불변 정경 사실) + 오버레이(큐레이션 데이터) 분리.** Neo4j는 theographic 원본 그래프, `data/*.json`은 여정·관계·근거 구절 등 프로젝트 큐레이션 레이어이며 라우터가 요청 시 둘을 병합한다.
- **엔드포인트 결과는 `functools.lru_cache`로 메모리 캐시** — 프로세스 재시작 전까지 유지(`backend/app/routes/events.py:53`, `persons.py:99`). 데이터가 바뀌면 컨테이너 재시작이 필요하다.
- **soft-empty 패턴**: 큐레이션 대상이 아닌 id는 404 대신 빈 배열/빈 stops를 반환한다(`journey.py:84`, `tours.py:81`, `persons.py:238`).
- 프론트는 **모든 화면 상태가 URL 해시에 미러**되어 딥링크·뒤로가기가 동작한다(`urlState.js`, `useStageNavigation.js`).

## Layers

**API 라우팅 계층:**
- Purpose: HTTP 요청 → 응답. 각 라우터가 독립 `APIRouter`를 만들어 `main.py`에서 등록.
- Location: `backend/app/routes/`
- Contains: 엔드포인트 함수, 응답 조립, 캐시된 빌드 함수
- Depends on: `..db`(Neo4j), `..overlays`(JSON)
- Used by: nginx `/api/` 프록시 경유 프론트

**데이터 접근 계층(2갈래):**
- Neo4j: `backend/app/db.py`의 싱글턴 드라이버. 라우터가 `with driver.session()`으로 Cypher 실행.
- 오버레이: `backend/app/overlays.py`의 `_resolve`/`_resolve_dir`/`_load`. `DATA_DIR`(기본 `/app/data`) → 레포 `data/` 순으로 경로 탐색.
- Depends on: 환경변수 `NEO4J_URI`/`NEO4J_USER`/`NEO4J_PASSWORD`, `DATA_DIR`
- Used by: 모든 라우터

**오프라인 데이터 파이프라인:**
- Purpose: 원본 수집·가공·Neo4j 주입·근거 구절 프리베이크. API 런타임과 분리.
- Location: `backend/scripts/`
- Contains: `load_*.py`(그래프 적재), `generate_*.py`(오버레이 JSON 생성), `inject_*.py`(그래프 속성 주입)
- 진입: 배포 시 `deploy.sh`가 `inject_ko_names.py`를 실행. 나머지는 수동 실행.

**프론트 프레젠테이션 계층:**
- Purpose: Stage별 화면 렌더 + 지도/타임라인/관계 시각화.
- Location: `frontend/src/`
- Contains: `*.jsx` 컴포넌트, `use*.js` 훅, `map*.js` MapLibre 헬퍼, `urlState.js`/`api.js` 유틸.
- Depends on: `/api/*` 엔드포인트, MapLibre GL, lucide-react 아이콘.

## Data Flow

### 큐레이션 인물 여정(주 흐름)

1. 허브에서 인물 카드 클릭 → `handleSelectPerson`이 stage를 `explore`로, `explorePersonId` 설정 (`useStageNavigation.js:127`)
2. `App.jsx`의 effect가 `apiGet('/person/{id}/journey')` 호출 (`App.jsx:58`)
3. 백엔드 `journey.py`가 `person_events/{slug}.json`(오버레이)의 사건을 sortKey순 정렬하고, occursAt 장소 좌표만 Neo4j에서 배치 조회해 병합 (`journey.py:73`)
4. `journeyStops`를 MapView·JourneyList가 공유 — 지도에 여정 라인/정차지, 리스트에 사건 칩

### 인물 관계 뷰(RelationsView) 흐름

1. 탐험 내비의 "관계" 토글은 인물 모드에서만 노출된다(`App.jsx:134`, 투어 모드엔 없음). `exploreView === 'relations'`가 되면 `RelationsView`가 전체화면으로 마운트되고 우측 상세 패널은 덮이지 않는다(`App.jsx:337`, `App.jsx:373`).
2. `RelationsView`가 `apiGet('/person/{id}/relations')` 호출 (`RelationsView.jsx:29`). `personId`가 `key`라 인물 변경 시 리마운트된다(`App.jsx:342`).
3. 백엔드 `persons.py`의 `_build_relations`가 `person_relations/relations.json`(오버레이)에서 이 인물(slug)이 낀 pair만 필터, 상대 endpoint·시간순 phases를 반환 (`persons.py:206`). phase에는 valence·label·verse·approxYear + 빌드타임 프리베이크된 `verseTextKo/En`·`contextKo/En`이 담긴다.
4. 프론트 렌더 3단계: (a) 레인 개요 — 관계 유형(`TYPE_ORDER`)순 군집·유형아이콘·사건 칩 valence 색점, (b) 초점 쌍 — 두 인물 국면 세로 스토리라인(`focusIdx`), (c) 근거 구절 레이어 — 칩 클릭 시 절 본문 모달(`versePhase`, `VerseLayer()`). 전역 시간축 없이 각 관계가 자기 줄에 사건을 균등 배치한다.
5. 상대가 큐레이션 인물이면 `withId`가 해결되어 이름 클릭으로 그 인물 여정으로 점프 가능(`onExploreJourney` → `selectPerson`, `RelationsView.jsx:44`·`108`).

### 타임라인 사건 흐름

1. "타임라인" 토글 → `TimelineView` (CSS 토글로 상태 보존, `App.jsx:326`)
2. `apiGet('/events')` → `events.py`의 `_compute_events`가 Neo4j Event(startDate 있는 것) + `book_events`(추정책 오버레이) 병합, sortKey순 반환 (`events.py:53`)
3. 사건 칩 드릴다운 → `/event/{id}/verses` → `event_verses.json` 오버레이를 권별 그룹으로 반환 (`events.py:110`)

**State Management:**
- 서버 상태(내비/단계): `useStageNavigation.js`가 단일 출처. `useNodeSelection.js`가 선택 노드·히스토리.
- URL 해시가 화면 상태의 미러(딥링크). React 컨텍스트나 전역 스토어는 없다 — props drilling으로 전달.
- 백엔드는 무상태(요청마다 세션), 단 `lru_cache`가 프로세스 수명 캐시 역할.

## Key Abstractions

**theographic_id:**
- Purpose: 그래프 노드와 오버레이 사이 공통 식별자. 모든 노드 조회의 키.
- Examples: `nodes.py`의 모든 `MATCH (n {theographic_id: $id})`, 인덱스 생성(`main.py:14`).
- Pattern: 라벨별 `{label}_tid` 인덱스로 조회 최적화.

**slug ↔ theographic_id 매핑:**
- Purpose: URL(사람이 읽는 `abraham`) ↔ 그래프 id 상호변환.
- Examples: `persons.py:_ERA`/`_NAME_KO`(slug 고정 매핑), `journey.py:_build_id_to_slug`(각 slug json 첫 participant[0]로 역매핑).
- Pattern: `persons.py`가 era/이름 매핑의 단일 출처. `places.py`·`journey.py`·`tours.py`가 여기서 import(드리프트 방지).

**오버레이 pair(관계):**
- Purpose: 인물 쌍의 관계 카탈로그. endpoints(양측 slug/nameKo/role) + phases(국면).
- Examples: `data/person_relations/relations.json`, 저작 규칙 `data/person_relations/AUTHORING.md`.
- Pattern: subject 관점으로 필터해 상대 endpoint·phases 반환. role은 상대 관점 역할 우선(`persons.py:229`).

**Stage:**
- Purpose: SPA 최상위 화면 단계 — `hub` | `explore` | `overview` | `tours`.
- Examples: `useStageNavigation.js:11`, `App.jsx`의 `activeStage ===` 분기 렌더.
- Pattern: exploreView(`map`|`timeline`|`relations`)가 explore 하위 토글. 인물/투어는 상호배타.

## Entry Points

**FastAPI 앱:**
- Location: `backend/app/main.py`
- Triggers: Dockerfile `CMD uvicorn app.main:app` (`backend/Dockerfile:6`)
- Responsibilities: lifespan에서 라벨별 theographic_id 인덱스 보장, 8개 라우터 등록.

**SPA:**
- Location: `frontend/src/main.jsx` → `App.jsx`
- Triggers: `frontend/index.html`이 nginx로 서빙
- Responsibilities: Stage 상태머신 마운트, 딥링크 해시 복원.

**배포:**
- Location: `.github/workflows/deploy.yml` → `deploy.sh`
- Triggers: `main` push(self-hosted 러너)
- Responsibilities: 프론트 빌드 → API 이미지 빌드 → 컨테이너 재시작 → `inject_ko_names.py` 주입(최대 15회 재시도).

## Architectural Constraints

- **Threading:** FastAPI 라우터는 동기 함수(`def`)라 스레드풀에서 실행된다. Neo4j 드라이버는 `db.py`의 모듈 전역 싱글턴(`_driver`).
- **Global state:** `db.py:_driver` 싱글턴. 라우터 다수의 `functools.lru_cache` 결과가 프로세스 수명 동안 모듈 전역에 상주 → 오버레이/그래프 변경 시 재시작 필요.
- **Circular imports:** `journey.py`·`places.py`·`tours.py`가 `persons.py`에서 매핑을 import, `tours.py`가 `journey.py`도 import한다. 단방향(persons가 가장 아래)이라 순환은 없다.
- **캐시 무효화 없음:** 런타임에 오버레이/그래프를 갱신해도 `lru_cache`가 옛 결과를 반환한다. 데이터 갱신은 컨테이너 재시작을 전제한다.
- **API 미노출:** api 컨테이너는 호스트 포트를 열지 않는다(`docker-compose.yml`엔 api ports 없음). 외부 접근은 nginx `/api/` 프록시만.

## Anti-Patterns

### effect 안에서 동기 setState

**What happens:** effect 본문에서 곧바로 `setState`를 호출하면 딥링크 복원·popstate 복원 로직이 렌더 사이클과 얽혀 딥링크 해시가 hub write로 덮이는 버그를 낸다.
**Why it's wrong:** 실제 딥링크 유실 버그 이력이 있다.
**Do this instead:** `Promise.resolve().then(() => setState(...))`로 마이크로태스크에 미룬다 (`useStageNavigation.js:62`·`111`, `App.jsx:68`).

### 인라인 화살표 콜백을 자식 fetch effect deps에 전달

**What happens:** `App.jsx`에서 `onNodeLoaded={(d) => ...}`처럼 인라인 함수를 넘기면 매 렌더 새 참조가 되어 자식(`SidePanel`)의 `/node` fetch effect가 매번 재실행되고 접힘 상태가 리셋된다.
**Why it's wrong:** 섹션이 안 펼쳐지는 실제 버그로 이어졌다.
**Do this instead:** `useCallback`으로 참조를 안정화한다 (`useStageNavigation.js:186`, `useNodeSelection.js:33` selectNode).

### Map/history 전역 섀도잉

**What happens:** lucide-react의 `Map` 아이콘이나 `history` 배열을 상태머신 파일에서 구조분해하면 전역 `window.history`/`Map`을 가려 런타임 크래시가 났다.
**Why it's wrong:** 과거 두 차례 크래시 원인.
**Do this instead:** `useStageNavigation.js`는 의도적으로 `Map` import·`history` 구조분해를 피한다(파일 상단 주석 `useStageNavigation.js:6` 참조).

### startDate 문자열 사전순 정렬

**What happens:** `startDate`가 `"-4003"`/`"-1451-01"`/`"30"` 혼재 문자열이라 사전순 정렬하면 BC 연도가 역전된다.
**Why it's wrong:** BC 연대 순서가 뒤집힌다.
**Do this instead:** 연도를 파싱해 부호를 반영하는 `_year` 헬퍼로 정렬한다 (`nodes.py:238`).

## Error Handling

**Strategy:** 백엔드는 조회 실패/빈 대상을 예외 대신 빈 응답으로 흡수(soft-empty). 진짜 없는 노드만 `HTTPException(404)`(`nodes.py:30`·`156`). lifespan 인덱스 실패는 로깅 후 계속 진행(`main.py:19`).

**Patterns:**
- 프론트 fetch는 `apiGet`이 비-OK를 `err.status`로 throw(`api.js:9`). 호출부는 `.catch`에서 빈 상태로 폴백.
- `AbortController`로 요청 취소, `e.name === 'AbortError'`는 무시(`App.jsx:61`).
- 큐레이션 목록 로드는 지수백오프 유한 재시도(1s→2s→4s, `useStageNavigation.js:34`).

## Cross-Cutting Concerns

**Logging:** 백엔드는 표준 `logging`(경고/예외). 프론트는 `console.warn` 소수. 배포는 `deploy.sh`가 `com.biblemap.deploy.log`에 기록.
**Validation:** 별도 검증 계층 없음 — FastAPI 경로 파라미터 타입만. 오버레이 파일 결손은 로그 경고 후 건너뜀.
**Authentication:** 없음. 읽기 전용 공개 API, CORS는 GET 전면 허용(`main.py:26`).
**Caching:** 응답 헤더 `Cache-Control: max-age=300`(대부분 라우터), books-overview는 `no-store`. 정적 자산은 nginx immutable 1년(`nginx.conf:25`).

---

*Architecture analysis: 2026-07-09*
