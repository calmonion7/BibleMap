---
last_mapped_commit: cf024f8e79a4864f4489aca0b0fd4c84caebeaf6
mapped: 2026-07-11
---
# ARCHITECTURE

**Analysis Date:** 2026-07-11

## System Overview

BibleMap은 세 개의 컨테이너 서비스로 구성된다(`docker-compose.yml`). Neo4j 그래프 DB가 정경 그래프(인물·장소·사건·책)를 담고, FastAPI 백엔드가 그 그래프 + JSON 오버레이(`data/`)를 병합해 읽기 전용 API로 노출하며, Vite/React SPA를 nginx가 정적 서빙하면서 `/api/`를 백엔드로 프록시한다.

```text
┌─────────────────────────────────────────────────────────────┐
│                    브라우저 (React SPA)                        │
│   `frontend/src/App.jsx` — Stage 상태머신 + 뷰 렌더           │
│   MapView / TimelineView / RelationsView / SidePanel …        │
│   디자인: Night Atlas 다크 단일 토큰(`index.css`, ADR-0013)   │
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
│   main.py (앱+lifespan+로깅+라우터 등록)                       │
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
| FastAPI 앱 | 앱 생성·로깅 설정·CORS·lifespan(인덱스 보장)·라우터 등록 | `backend/app/main.py` |
| Neo4j 드라이버 | 싱글턴 드라이버 lazy 생성(`get_driver`) | `backend/app/db.py` |
| 오버레이 로더 | `data/*.json` 경로 해석·로드·lru_cache, 파일 부재 시 경고 로그 | `backend/app/overlays.py` |
| 노드 라우터 | 노드 상세·이웃·장소·Book 상위 인물/사건(CONTAINS_BOOK.primary 필터) | `backend/app/routes/nodes.py` |
| 인물 라우터 | 큐레이션 인물 목록·연결·관계(관계 뷰 데이터) | `backend/app/routes/persons.py` |
| 여정 라우터 | 인물 시간순 정차지(좌표 배치조회) | `backend/app/routes/journey.py` |
| 사건 라우터 | 타임라인 사건 목록·사건 근거 구절 | `backend/app/routes/events.py` |
| 투어 라우터 | 테마 투어 목록·상세(event-ref 오버레이) | `backend/app/routes/tours.py` |
| 장소 라우터 | 장소를 지나는 큐레이션 인물 | `backend/app/routes/places.py` |
| 책 라우터 | 개요 뷰 전체 책 목록 | `backend/app/routes/books.py` |
| 검색 라우터 | nameKo/name CONTAINS 검색 — 등록만 되어 있고 프론트에서 호출되지 않는 잔존 엔드포인트(ADR-0007이 검색 UI 제거) | `backend/app/routes/search.py` |
| SPA 진입 | Stage 렌더 트리·상세 패널·여정/타임라인 필터 fetch | `frontend/src/App.jsx` |
| Stage 상태머신 | 단계·URL 해시·브라우저 히스토리 동기화 | `frontend/src/useStageNavigation.js` |
| 노드 선택 | 선택 노드·히스토리 | `frontend/src/useNodeSelection.js` |
| 지도 | MapLibre GL 지도·무라벨 지형 타일·여정 라인·사건 링 | `frontend/src/MapView.jsx` + `map*.js` |
| 관계 뷰 | 관계 레인 개요·초점 쌍·근거 구절 레이어(양피지 모달) | `frontend/src/RelationsView.jsx` |
| 디자인 토큰 | Night Atlas 다크 단일 CSS 변수(정본) + JS 상수 미러 | `frontend/src/index.css`, `frontend/src/theme.js`(`NIGHT`) |

## Pattern Overview

**Overall:** 그래프 백본 + JSON 오버레이 병합 위에 얹은 읽기 전용 REST API, 그리고 라우팅 라이브러리 없이 해시 딥링크로 구동되는 단일 페이지 Stage 상태머신. 프론트는 다크 단일("Night Atlas") 디자인 시스템(ADR-0013)으로 통일되어 있다.

**Key Characteristics:**
- 백엔드는 **읽기 전용**이다. CORS는 `allow_methods=["GET"]`만 허용(`backend/app/main.py:49`). 쓰기는 전부 `backend/scripts/`의 오프라인 로더/인젝터가 담당한다.
- **그래프(불변 정경 사실) + 오버레이(큐레이션 데이터) 분리.** Neo4j는 theographic 원본 그래프, `data/*.json`은 여정·관계·근거 구절 등 프로젝트 큐레이션 레이어이며 라우터가 요청 시 둘을 병합한다.
- **그래프 관계 자체에 발생/인용 구분 속성을 부여**(`CONTAINS_BOOK.primary`, ADR-0012) — 오버레이가 아니라 그래프 스키마 레벨에서 "이 사건이 이 책에서 실제로 일어났는가(발생) vs 다른 책이 이 사건을 인용/회고했는가"를 태깅해, 파생 집계(Book 상위 인물/사건/장소)가 회고 인용에 오염되지 않게 한다.
- **엔드포인트 결과는 `functools.lru_cache`로 메모리 캐시** — 프로세스 재시작 전까지 유지(`backend/app/routes/events.py:53`, `backend/app/routes/persons.py:101`). 인물별 조회 캐시(`_build_connections`/`_build_relations`/`_place_to_persons`)는 무한 누적을 막기 위해 `maxsize=256`으로 상한을 둔다. 데이터가 바뀌면 컨테이너 재시작이 필요하다.
- **soft-empty 패턴**: 큐레이션 대상이 아닌 id는 404 대신 빈 배열/빈 stops를 반환한다(`journey.py:84-88`, `tours.py:87-92`, `persons.py:217-218`).
- 프론트는 **모든 화면 상태가 URL 해시에 미러**되어 딥링크·뒤로가기가 동작한다(`urlState.js`, `useStageNavigation.js`).
- **디자인은 다크 단일 + 예외 둘("Night Atlas", ADR-0013)**: CSS 변수(`index.css`)가 표면/잉크/금색/양피지 토큰의 정본이고, JS 계산이 필요한 지점(예: `color+'22'`로 border 알파를 합성하는 `Spinner`)만 `theme.js`의 `NIGHT` 상수 미러를 쓴다. 밝은 표면은 성경 구절 본문(`--paper*`)과 지도(무라벨 지형 타일) 둘로 한정된다.

## Layers

**API 라우팅 계층:**
- Purpose: HTTP 요청 → 응답. 각 라우터가 독립 `APIRouter`를 만들어 `main.py`에서 등록.
- Location: `backend/app/routes/`
- Contains: 엔드포인트 함수, 응답 조립, 캐시된 빌드 함수
- Depends on: `..db`(Neo4j), `..overlays`(JSON)
- Used by: nginx `/api/` 프록시 경유 프론트

**데이터 접근 계층(2갈래):**
- Neo4j: `backend/app/db.py`의 싱글턴 드라이버. 라우터가 `with driver.session()`으로 Cypher 실행.
- 오버레이: `backend/app/overlays.py`의 `_resolve`/`_resolve_dir`/`_load`. `DATA_DIR`(기본 `/app/data`) → 레포 `data/` 순으로 경로 탐색. 두 경로 모두 없으면 경고 로그 후 빈 데이터 폴백.
- Depends on: 환경변수 `NEO4J_URI`/`NEO4J_USER`/`NEO4J_PASSWORD`, `DATA_DIR`
- Used by: 모든 라우터

**오프라인 데이터 파이프라인:**
- Purpose: 원본 수집·가공·Neo4j 주입·근거 구절 프리베이크. API 런타임과 분리.
- Location: `backend/scripts/`
- Contains: `load_*.py`(그래프 적재), `generate_*.py`(오버레이 JSON 생성), `inject_*.py`(그래프 속성 주입)
- 진입: 배포 시 `deploy.sh`가 `inject_ko_names.py`를 실행. 나머지는 수동 실행.

**프론트 프레젠테이션 계층:**
- Purpose: Stage별 화면 렌더 + 지도/타임라인/관계 시각화. Night Atlas 다크 단일 디자인 토큰 적용.
- Location: `frontend/src/`
- Contains: `*.jsx` 컴포넌트, `use*.js` 훅, `map*.js` MapLibre 헬퍼, `urlState.js`/`api.js` 유틸, `index.css`(디자인 토큰 정본)·`theme.js`(색 팔레트 + JS 토큰 미러).
- Depends on: `/api/*` 엔드포인트, MapLibre GL, lucide-react 아이콘.

## Data Flow

### 큐레이션 인물 여정(주 흐름)

1. 허브에서 인물 카드 클릭 → `handleSelectPerson`이 stage를 `explore`로, `explorePersonId` 설정 (`useStageNavigation.js:132`)
2. `App.jsx`의 effect가 `apiGet('/person/{id}/journey')` 호출 (`App.jsx:74`)
3. 백엔드 `journey.py`가 `person_events/{slug}.json`(오버레이)의 사건을 sortKey순 정렬하고, occursAt 장소 좌표만 Neo4j에서 배치 조회해 병합 (`journey.py:73-137`)
4. `journeyStops`를 MapView·JourneyList가 공유 — 지도에 여정 라인/정차지(금색 그라데이션, ADR-0013), 리스트에 사건 칩

### Book 상세 — CONTAINS_BOOK.primary가 topEvents/topPersons/장소를 구동 (task#152, ADR-0012)

Neo4j의 `Book-[:CONTAINS_BOOK]->Event` 관계는 사건의 모든 성경 참조(실제 발생 위치 + 다른 책의 회고 인용)를 무차별로 연결한다 — 사건의 `verses`(theographic) 또는 `books`(authored) 배열이 여러 책에 걸치기 때문이다. 이를 `primary` 불리언으로 구분해 파생 집계를 정화한다.

1. **시딩**: `backend/scripts/load_books.py`(theographic 사건)와 `backend/scripts/load_person_events.py`(저작 사건) 둘 다 각 사건의 **첫 번째 참조 책**을 발생(`primary=true`)으로, 나머지 책 참조를 회고 인용(`primary=false`)으로 태깅해 `CONTAINS_BOOK` 관계에 SET 한다.
2. **소비 — `backend/app/routes/nodes.py`의 `get_node`(Book 라벨 분기)**:
   - topPersons: `MATCH (b)-[rel:CONTAINS_BOOK]->(e:Event) WHERE rel.primary` 후 `HAS_PARTICIPANT`로 인물 집계, 사건 수 desc 상위 10 (`nodes.py:206-224`).
   - topEvents: 동일하게 `WHERE rel.primary`로 필터한 사건만 모아 `startDate` 파싱(연도 부호 처리, `_year` 헬퍼) 오름차순 상위 10 (`nodes.py:226-255`).
3. **소비 — `backend/app/routes/nodes.py`의 `get_node_places`(Book 라벨 분기)**: 지도에 뿌릴 Book의 장소 목록도 `WHERE rel.primary`로 필터해 회고 인용 사건의 장소가 섞이지 않게 한다(`nodes.py:68-78`).
4. **효과**: 예컨대 사도행전 topEvents 1위가 스데반 설교에서 인용된 BC2091 아브라함 소명 사건으로 뜨는 오염, 누가복음 topEvents에 족보가 인용한 창세기 인물 탄생이 섞이는 오염이 사라진다. `book_events` 추정책 오버레이(`overlays.book_events_raw`, `events.py`의 타임라인용 역방향 인덱스)는 이 필터와 별개 경로이며 영향받지 않는다.

### 인물 관계 뷰(RelationsView) 흐름

1. 탐험 내비의 "관계" 토글은 인물 모드에서만 노출된다(`App.jsx:149`, 투어 모드엔 없음). `exploreView === 'relations'`가 되면 `RelationsView`가 전체화면으로 마운트되고 우측 상세 패널은 덮이지 않는다(`App.jsx:353-365`, `App.jsx:389`).
2. `RelationsView`가 `apiGet('/person/{id}/relations')` 호출(`RelationsView.jsx:29`). `personId`가 `key`라 인물 변경 시 리마운트된다(`App.jsx:356`).
3. 백엔드 `persons.py`의 `_build_relations`가 `person_relations/relations.json`(오버레이)에서 이 인물(slug)이 낀 pair만 필터, 상대 endpoint·시간순 phases를 반환(`persons.py:208-237`). phase에는 valence·label·verse·approxYear + 빌드타임 프리베이크된 `verseTextKo/En`·`contextKo/En`이 담긴다(각 국면의 서사적 맥락 — task#148).
4. 프론트 렌더 3단계: (a) 레인 개요 — 관계 유형순 군집·유형아이콘·사건 칩 valence 색점(`VALENCE_COLOR`), (b) 초점 쌍 — 두 인물 국면 세로 스토리라인, (c) 근거 구절 레이어 — 칩 클릭 시 절 본문 모달(양피지 카드, `var(--paper)`). 전역 시간축 없이 각 관계가 자기 줄에 사건을 균등 배치한다.
5. 상대가 큐레이션 인물이면 `withId`가 해결되어 이름 클릭으로 그 인물 여정으로 점프 가능(`onExploreJourney` → `selectPerson`).

### 타임라인 사건 흐름

1. "타임라인" 토글 → `TimelineView` (CSS 토글로 상태 보존, `App.jsx:341`)
2. `apiGet('/events')` → `events.py`의 `_compute_events`가 Neo4j Event(startDate 있는 것) + `book_events`(추정책 오버레이) 병합, sortKey순 반환 (`events.py:53-86`)
3. 사건 칩 드릴다운 → `/event/{id}/verses` → `event_verses.json` 오버레이를 권별 그룹으로, 응답 직전 `bookOrder` 오름차순 강제 정렬해 반환 (`events.py:110-125`)
4. **인물/투어 타임라인 필터**: `personEventIds`는 `explorePersonId`가 바뀔 때 `App.jsx`의 전용 effect가 `/person/{id}/event-ids`를 fetch해 채운다(`App.jsx:55-65`) — `selectedNode`(장소 등 다른 노드 클릭)에는 더 이상 묶이지 않는다. 투어의 `tourEventIds`와 대칭 구조. 이 분리는 "지도에서 장소를 클릭하면 타임라인 인물 필터가 사라지는" 버그(task#151 헌트 #10)의 수정 결과다.

## State Management

- 서버 상태(내비/단계): `useStageNavigation.js`가 단일 출처. `useNodeSelection.js`가 선택 노드·히스토리(더 이상 인물 사건 필터를 겸하지 않는다 — `App.jsx`로 이전됨).
- URL 해시가 화면 상태의 미러(딥링크). React 컨텍스트나 전역 스토어는 없다 — props drilling으로 전달.
- 백엔드는 무상태(요청마다 세션), 단 `lru_cache`가 프로세스 수명 캐시 역할(상한 있는 캐시는 위 참고).
- **딥링크 복원 게이팅**: 마운트 시 해시 복원은 `stage==='explore' && personSlug`인 경우에만 큐레이션 slug↔id 맵(`/persons/curated` 로드 완료)을 기다린다(`useStageNavigation.js:61`). `overview`/`tours`/투어 slug 딥링크는 큐레이션 로드 실패·지연과 무관하게 즉시 복원된다 — 과거엔 게이트가 모든 stage에 걸려 큐레이션 fetch가 실패하면 `#/books`·`#/tours` 딥링크까지 허브로 고착되는 버그가 있었다(task#151 헌트 #12).
- **히스토리 동기화 재실행 조건**: sync effect의 deps에 `curatedIds`가 포함된다(`useStageNavigation.js:109`) — 인물 카드 클릭이 slug 맵 로드보다 먼저 일어나 조기 반환되더라도, 맵이 도착하면 effect가 재실행되어 뒤늦게라도 올바른 해시로 `pushState`한다(task#151 헌트 #11).
- **디자인 토큰 상태**: 전역 상태가 아니라 정적 CSS 변수(`index.css:3-55`) — 라이트/다크 전환 로직 자체가 없다(`color-scheme: dark` 고정, `index.css:44`). 과거 존재했던 `prefers-color-scheme` 미디어쿼리 분기는 다크 단일 전환(ADR-0013)으로 제거됐다.

## Key Abstractions

**theographic_id:**
- Purpose: 그래프 노드와 오버레이 사이 공통 식별자. 모든 노드 조회의 키.
- Examples: `nodes.py`의 모든 `MATCH (n {theographic_id: $id})`, 인덱스 생성(`main.py:32-36`).
- Pattern: 라벨별 `{label}_tid` 인덱스로 조회 최적화.

**CONTAINS_BOOK.primary (발생 vs 인용):**
- Purpose: Book↔Event 관계에서 "이 책이 이 사건의 실제 발생 무대인가"를 표시하는 불리언 관계 속성. 파생 집계(topEvents/topPersons/Book 장소)가 인용에 오염되지 않게 하는 그래프 스키마 단의 장치.
- Examples: `load_books.py`(theographic, verses[0]의 책이 primary), `load_person_events.py`(authored, books[0]이 primary), `nodes.py`의 `WHERE rel.primary` 3곳.
- Pattern: 새 사건-책 관계를 만드는 시딩 스크립트는 반드시 첫 참조=발생 규약으로 `primary`를 세팅해야 하며, 파생 집계 쿼리는 `primary` 관계만 골라 쓴다. 상세 근거는 ADR-0012.

**slug ↔ theographic_id 매핑:**
- Purpose: URL(사람이 읽는 `abraham`) ↔ 그래프 id 상호변환.
- Examples: `persons.py`의 `_ERA`/`_NAME_KO`(slug 고정 매핑, 35인), `journey.py:_build_id_to_slug`(각 slug json 첫 participant[0]로 역매핑).
- Pattern: `persons.py`가 era/이름 매핑의 단일 출처. `places.py`·`journey.py`·`tours.py`가 여기서 import(드리프트 방지).

**오버레이 pair(관계):**
- Purpose: 인물 쌍의 관계 카탈로그. endpoints(양측 slug/nameKo/role) + phases(국면, 각 국면에 valence·근거 구절·서사 문맥).
- Examples: `data/person_relations/relations.json`(약 1.2MB), 저작 규칙 `data/person_relations/AUTHORING.md`.
- Pattern: subject 관점으로 필터해 상대 endpoint·phases 반환. role은 상대 관점 역할 우선(`persons.py:231`).

**Stage:**
- Purpose: SPA 최상위 화면 단계 — `hub` | `explore` | `overview` | `tours`.
- Examples: `useStageNavigation.js:11`, `App.jsx`의 `activeStage ===` 분기 렌더.
- Pattern: exploreView(`map`|`timeline`|`relations`)가 explore 하위 토글. 인물/투어는 상호배타.

**Night Atlas 디자인 토큰(ADR-0013):**
- Purpose: 다크 단일 UI의 표면·잉크·액센트·양피지 색을 CSS 변수로 정본화하고, JS에서 계산이 필요한 지점(문자열 결합)에만 동일 값을 상수로 미러링.
- Examples: `index.css:3-55`(정본 — `--bg-0~3`, `--ink*`, `--gold*`, `--paper*`, `--serif`/`--sans`, `--r-*`, `--shadow-*`), `theme.js:31-37`의 `NIGHT` 객체(순수 hex/rgba 리터럴), `theme.js:5-12`의 `TYPE_COLOR`·`theme.js:25`의 `VALENCE_COLOR`.
- Pattern: 인라인 스타일에서 값이 그대로 CSS로 흘러가면 `var(--token)` 문자열을 직접 쓴다. `Spinner`처럼 JS가 `color+'22'` 형태로 알파를 문자열 결합해야 하는 지점은 `var()`를 CSS 엔진 밖에서 이어붙일 수 없으므로 `NIGHT`의 hex 리터럴을 대신 넘긴다(`SidePanel.jsx:122`, `RelationsView.jsx:37`, `TimelineView.jsx:169`, `EventVerses.jsx:81` 등 4곳 이상에서 반복되는 명시적 주석 패턴). 밝은 예외는 성경 구절 본문(`--paper*`)과 지도(무라벨 지형 타일) 둘로 고정 — 새 화면·컴포넌트를 추가할 때 이 둘 외의 라이트 표면을 만들지 않는다.

## Entry Points

**FastAPI 앱:**
- Location: `backend/app/main.py`
- Triggers: Dockerfile `CMD uvicorn app.main:app` (`backend/Dockerfile:6`)
- Responsibilities: import 시점에 로깅 설정(`_configure_logging`), lifespan에서 라벨별 theographic_id 인덱스 보장, 8개 라우터 등록.

**SPA:**
- Location: `frontend/src/main.jsx` → `App.jsx`
- Triggers: `frontend/index.html`이 nginx로 서빙
- Responsibilities: Stage 상태머신 마운트, 딥링크 해시 복원, `index.css` 임포트(디자인 토큰 전역 적용).

**배포:**
- Location: `.github/workflows/deploy.yml` → `deploy.sh`
- Triggers: `main` push(self-hosted 러너)
- Responsibilities: 프론트 빌드 → API 이미지 빌드 → 컨테이너 재시작 → `inject_ko_names.py` 주입(최대 15회 재시도).

## Architectural Constraints

- **Threading:** FastAPI 라우터는 동기 함수(`def`)라 스레드풀에서 실행된다. Neo4j 드라이버는 `db.py`의 모듈 전역 싱글턴(`_driver`).
- **Global state:** `db.py:_driver` 싱글턴. 라우터 다수의 `functools.lru_cache` 결과가 프로세스 수명 동안 모듈 전역에 상주 → 오버레이/그래프 변경 시 재시작 필요. 인물별 조회 캐시는 `maxsize=256`으로 상한.
- **Circular imports:** `journey.py`·`places.py`·`tours.py`가 `persons.py`에서 매핑을 import, `tours.py`가 `journey.py`도 import한다. 단방향(persons가 가장 아래)이라 순환은 없다.
- **캐시 무효화 없음:** 런타임에 오버레이/그래프를 갱신해도 `lru_cache`가 옛 결과를 반환한다. 데이터 갱신은 컨테이너 재시작을 전제한다.
- **API 미노출:** api 컨테이너는 호스트 포트를 열지 않는다(`docker-compose.yml`엔 api ports 없음). 외부 접근은 nginx `/api/` 프록시만.
- **MapLibre 캔버스는 래스터+오버레이 공유:** 지도 톤 조정은 CSS `filter`가 아니라 래스터 레이어 자체의 `paint`(`raster-saturation`/`raster-brightness-max`/`raster-contrast`, `MapView.jsx:41-47`)로 해야 한다 — CSS filter는 단일 `<canvas>` 위에 그려지는 여정선·배지 오버레이까지 함께 물들인다(design-renewal 2/2 회고).
- **외부 타일 서비스의 줌 상한:** `esri` 소스(`World_Terrain_Base`)는 z10+에서 "data not yet available" 플레이스홀더를 반환하므로 `maxzoom: 9`로 오버줌 처리한다(`MapView.jsx:37`). 타일 서비스를 교체할 때는 줌 피라미드를 먼저 프로브해야 한다.

## Anti-Patterns

### effect 안에서 동기 setState

**What happens:** effect 본문에서 곧바로 `setState`를 호출하면 딥링크 복원·popstate 복원 로직이 렌더 사이클과 얽혀 딥링크 해시가 hub write로 덮이는 버그를 낸다.
**Why it's wrong:** 실제 딥링크 유실 버그 이력이 있다.
**Do this instead:** `Promise.resolve().then(() => setState(...))`로 마이크로태스크에 미룬다 (`useStageNavigation.js:65`·`116`, `App.jsx:62`).

### 노드 선택(selectedNode)에 파생 필터를 결합

**What happens:** 인물 타임라인 필터(`personEventIds`)를 `selectedNode` 변경에 묶으면, 지도에서 장소 등 다른 노드를 클릭하는 순간 필터가 null로 리셋되어 사라진다.
**Why it's wrong:** "탐험 인물"과 "현재 선택된 노드"는 독립적인 개념인데 하나로 묶여 실제 버그(task#151 헌트 #10)로 이어졌다.
**Do this instead:** 탐험 컨텍스트에서 파생되는 값은 `explorePersonId`/`exploreTourId`에 직접 묶는다(`App.jsx:55-65`의 `personEventIds` effect, `tourEventIds`와 대칭).

### 인라인 화살표 콜백을 자식 fetch effect deps에 전달

**What happens:** `App.jsx`에서 `onNodeLoaded={(d) => ...}`처럼 인라인 함수를 넘기면 매 렌더 새 참조가 되어 자식(`SidePanel`)의 `/node` fetch effect가 매번 재실행되고 접힘 상태가 리셋된다.
**Why it's wrong:** 섹션이 안 펼쳐지는 실제 버그로 이어졌다.
**Do this instead:** `useCallback`으로 참조를 안정화한다 (`useStageNavigation.js:191-194` onNodeLoaded, `useNodeSelection.js:24-29` selectNode).

### Map/history 전역 섀도잉

**What happens:** lucide-react의 `Map` 아이콘이나 `history` 배열을 상태머신 파일에서 구조분해하면 전역 `window.history`/`Map`을 가려 런타임 크래시가 났다.
**Why it's wrong:** 과거 두 차례 크래시 원인.
**Do this instead:** `useStageNavigation.js`는 의도적으로 `Map` import·`history` 구조분해를 피한다(파일 상단 주석 `useStageNavigation.js:6` 참조).

### startDate 문자열 사전순 정렬

**What happens:** `startDate`가 `"-4003"`/`"-1451-01"`/`"30"` 혼재 문자열이라 사전순 정렬하면 BC 연도가 역전된다. 부호 분리 후 첫 `-` 이전만 취하지 않으면 월/일 정밀도가 조용히 누락되는 2차 버그도 있었다(task#151 #2).
**Why it's wrong:** BC 연대 순서가 뒤집히거나 파싱 정밀도가 깨진다.
**Do this instead:** 연도를 파싱해 부호를 반영하는 헬퍼로 정렬한다(`nodes.py:244`의 `_year`, `frontend/src/dates.js`의 `parseYear` — 둘 다 프론트/백엔드에 독립 구현되어 있으므로 새 정렬 지점은 반드시 재사용하거나 동일 로직을 이식해야 한다).

### 다크 UI에서 CSS `filter`로 MapLibre 지도 톤 조정

**What happens:** 지도를 세피아·다크 틴트로 물들이려고 지도 컨테이너에 CSS `filter`(예: `sepia()`/`brightness()`)를 걸면, 여정선·정차지 배지 등 지도 위 모든 오버레이가 같은 `<canvas>`에 그려지므로 함께 물든다 — 의도한 지형 톤만 바꿀 수 없다.
**Why it's wrong:** 목업(별도 `<img>`)과 실제 앱(단일 WebGL 캔버스)의 구조 차이를 계획 단계에서 놓쳐 실제로 겪은 이탈이다(design-renewal 2/2 회고).
**Do this instead:** 래스터 소스 레이어 자체의 `paint`에 `raster-saturation`/`raster-brightness-max`/`raster-contrast`를 건다(`MapView.jsx:41-47`) — 오버레이 레이어는 영향받지 않는다.

### `color+'22'` 알파 문자열 결합에 CSS 변수 전달

**What happens:** `Spinner`처럼 `border: 3px solid ${color}22`로 16진 알파를 문자열 결합하는 컴포넌트에 `var(--token)` 문자열을 넘기면 `var(--gold)22`같은 무효 CSS 값이 되어 스타일이 조용히 깨진다.
**Why it's wrong:** CSS 커스텀 프로퍼티는 브라우저가 렌더 시점에 치환하므로 JS 문자열 결합 시점에는 아직 `var(...)` 리터럴 그대로다 — 알파 접미를 붙일 수 없다.
**Do this instead:** 이런 JS 계산 지점에는 `theme.js`의 `NIGHT` 상수(순수 hex/rgba 리터럴)를 넘긴다. 코드베이스에 이미 4곳 이상 명시적 주석으로 표시돼 있다(`SidePanel.jsx:120-122`, `RelationsView.jsx:36-37`, `TimelineView.jsx:168-169`, `EventVerses.jsx:80-81`).

## Error Handling

**Strategy:** 백엔드는 조회 실패/빈 대상을 예외 대신 빈 응답으로 흡수(soft-empty). 진짜 없는 노드만 `HTTPException(404)`(`nodes.py:34`·`161`). lifespan 인덱스 실패·오버레이 파일 부재는 모듈 logger로 경고 후 계속 진행(`main.py:37-40`, `overlays.py:20`·`30`).

**Patterns:**
- 프론트 fetch는 `apiGet`이 비-OK를 `err.status`로 throw(`api.js:9`). 호출부는 `.catch`에서 빈 상태로 폴백하며 `console.warn`으로 실패를 남긴다.
- `AbortController`로 요청 취소, `e.name === 'AbortError'`는 무시(`App.jsx:76`·`80`).
- 큐레이션 목록 로드는 지수백오프 유한 재시도(1s→2s→4s, `useStageNavigation.js:36-51`, `PersonHub.jsx:174-193`).

## Cross-Cutting Concerns

**Logging:** `backend/app/main.py`의 `_configure_logging()`이 import 시점(라우터 import 전) 1회 `logging.basicConfig(INFO)`를 설정하고, 서드파티 로거(neo4j/urllib3/asyncio)는 WARNING으로 승격, `uvicorn`/`uvicorn.access`는 root 중복 emit을 차단하되 `uvicorn.error`는 제외한다(propagate 차단 시 기동/에러 라인 자체가 사라지는 footgun이 있어 의도적으로 뺐다). 각 라우터/오버레이 모듈은 `logging.getLogger(__name__)`으로 모듈 logger를 쓰고 `[Startup]`/`[Persons]`/`[Places]`/`[Overlays]`/`[Nodes]`/`[Tours]`처럼 대괄호 태그를 접두한다. 방출 규약 정본은 `.forge/codebase/CONVENTIONS.md` §13(task#149). 프론트는 실패 폴백 지점에서 `console.warn`.
**Validation:** 별도 검증 계층 없음 — FastAPI 경로 파라미터 타입만. 오버레이 파일 결손은 로그 경고 후 건너뜀.
**Authentication:** 없음. 읽기 전용 공개 API, CORS는 GET 전면 허용(`main.py:45-51`).
**Caching:** 응답 헤더 `Cache-Control: max-age=300`(대부분 라우터), books-overview는 `no-store`. 정적 자산은 nginx immutable 1년(`nginx.conf`).
**Theming(디자인 토큰):** `index.css`의 `:root` 블록이 표면(`--bg-0~3`)·경계(`--line*`)·잉크(`--ink*`)·액센트(`--gold*`)·양피지(`--paper*`)·형태(`--r-*`/`--shadow-*`)·서체(`--serif`/`--sans`)를 정의하는 단일 출처다(ADR-0013). `color-scheme: dark`로 고정되어 있어 OS 라이트 모드와 무관하게 항상 다크로 렌더된다. 지도(MapLibre raster paint)와 성경 구절 본문 카드(`--paper*`)만 밝은 표면 예외로 허용된다.

---

*Architecture analysis: 2026-07-11*
