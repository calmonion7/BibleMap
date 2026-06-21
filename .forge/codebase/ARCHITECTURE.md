---
last_mapped_commit: 70a9781e6523a396ad856f980b5499b1cc814d7a
mapped: 2026-06-21
---

# 아키텍처

## 전체 구성

프론트엔드 SPA(React + Vite) → nginx 리버스 프록시 → FastAPI 백엔드 → Neo4j 그래프 DB.
정적·보조 데이터는 Neo4j에 주입하거나, Neo4j 밖 `data/` 디렉터리의 JSON 파일을 런타임 오버레이로 바로 읽는다(ADR-0001, ADR-0004).

```
브라우저
  └─ :8080 nginx
        ├─ /api/* → api:8000 (FastAPI, uvicorn)
        │              └─ bolt://neo4j:7687 (Neo4j 5)
        └─ /*     → frontend/dist (Vite 빌드 결과물, SPA)
```

컨테이너는 `docker-compose.yml`이 `neo4j`, `api`, `nginx` 세 서비스로 구성한다.
`api`는 `./data`를 `/app/data`로 마운트(오버레이 읽기), `nginx`는 `./frontend/dist`를 정적 서빙한다.
`neo4j`/`api`의 `NEO4J_PASSWORD`는 미설정 시 compose가 실패한다(`:?` 가드).

---

## 레이어 구조

### 1. 프론트엔드 (React SPA)

**진입점**: `frontend/src/main.jsx` → `frontend/src/App.jsx`

`App.jsx`가 최상위 상태를 소유한다.

| 관심사 | 구현 |
|---|---|
| 노드 선택·히스토리·인물 사건 ID | `useNodeSelection` 커스텀 훅 (`useNodeSelection.js`) |
| 검색 쿼리·결과·타입 필터·드롭다운 | `useSearch` 커스텀 훅 (`useSearch.js`) |
| 뷰 전환 | `activeView` state (`map` / `timeline` / `overview`), `TABS` 배열 |
| 구절 언어 토글 | `verseLang` state (ko/en) — 하위 컴포넌트에 prop으로 전달 |
| 모바일 분기 | `isMobile` state — `matchMedia(MOBILE_QUERY)`, `MOBILE_BREAKPOINT` 기준 |
| `/` 단축키 검색 포커스 | `App.jsx` keydown 리스너 |

검색 결과 선택 시 타입별 탭으로 이동한다(`handleSelectResult`의 `tabMap`: Person/Place→map, Event→timeline, Book→overview).

**뷰 컴포넌트**

- `MapView.jsx` — maplibre-gl 지도. 장소 마커, 클러스터, 스파이더파이, 사건 링(방사형), 볼록 껍질(Person 활동 범위). 모듈 레벨에 순수 함수 추출(`placePopupHTML`, `registerEventHandlers`, `setupMapSources`, `outwardLabel`, `ringLabels`, `placesToGeoJSON`, `ringPositions`, `buildEventGeoJSON`, `buildSpiderGeoJSON`).
- `TimelineView.jsx` — 사건을 `startDate` 기준 그룹으로 세로 타임라인 렌더. 책 칩(근거 구절 인라인 드릴다운, out-of-order 응답 가드) 포함.
- `BibleOverviewView.jsx` — `/books-overview` 데이터로 구약·신약을 장르별(`OT_GENRE_ORDER`/`NT_GENRE_ORDER`, `GENRE_META`) 카드 그리드로 표시.

세 뷰는 항상 마운트되어 있으며 CSS `display` 토글로 상태를 보존한다.

**공유 패널**: `SidePanel.jsx` — 선택된 노드의 상세 정보(이웃 그룹 + 타입별 전용 블록).
`App.jsx`의 오버레이 패널 안에 렌더되며 데스크톱은 우측 슬라이드인, 모바일은 하단 시트(`SHEET_VH`=55vh, 스와이프-다운 닫기).
섹션은 `SectionHeader` 접기/펼치기(기본 접힘), 노드 라벨별 전용 렌더 분기:

| 라벨 | 전용 블록 |
|---|---|
| `Person` | 인물 성품(traits — 절 본문 ko/en 토글) + 이웃 그룹 |
| `Book` | 메타 칩·시대적 배경·핵심 주제·대표 구절·중심 메시지·핵심 인물·구조 개요·주요 인물·주요 사건 (이웃 그룹은 숨김) |
| `Place` | 장소 배경(prose) + 대표 구절(keyVerse·ko/en 절 본문) — Book 블록 미러, 이어서 이웃 그룹 |

**공유 UI**: `Spinner.jsx`, `VerseLangTabs.jsx`(SidePanel·TimelineView 공유)
**공유 팔레트**: `theme.js` — `TYPE_COLOR`, `TYPE_KO`, `TYPE_ORDER`, `SELECT_HL` + `typeColor()`/`typeKo()` 헬퍼
**공유 상수**: `constants.js` — `MOBILE_BREAKPOINT`(768px), `SHEET_VH`(55vh)
**순수 유틸**: `convexHull.js` (Graham scan), `api.js` (단일 apiGet 헬퍼)

---

### 2. API 클라이언트 (api.js)

모든 HTTP 요청의 단일 창구. `VITE_API_URL` 환경변수(빌드타임)로 베이스 URL을 결정한다.

- 개발: `http://localhost:8000`
- 프로덕션 빌드: `/api` (nginx 프록시 경유, `frontend/.env.production`에서 고정)

```js
// fetch → JSON, 비-OK는 status를 담은 Error로 throw, AbortError는 그대로 전파
export async function apiGet(path, { signal } = {})
```

---

### 3. 백엔드 (FastAPI)

**진입점**: `backend/app/main.py`

시작 시 `lifespan` 핸들러가 Neo4j에 theographic_id 인덱스 5종(레이블별)을 생성(실패 시 로깅 후 인덱스 없이 진행).
라우터 4개를 `include_router`로 등록. CORS는 GET 전용 `allow_origins=["*"]`.

**라우터 구조**

| 파일 | 엔드포인트 | 역할 |
|---|---|---|
| `routes/nodes.py` | `GET /node/{id}` | 노드 상세 + 이웃(50개 한도, 단일 쿼리로 총수 동시 조회). Book은 topPersons/topEvents 추가, Person은 traits JSON 파싱 |
| | `GET /node/{id}/neighbors/grouped` | 이웃을 타입별 그룹으로(30개/타입) |
| | `GET /node/{id}/places` | 노드 라벨별 관련 장소 목록(좌표 있는 Place만, 라벨별 패턴 분기) |
| | `GET /person/{id}/event-ids` | 인물 참여 사건 ID 목록 |
| `routes/events.py` | `GET /events` | 전체 사건 목록(정경순 책 칩 포함, 추정책 머지) — `lru_cache`, `Cache-Control: max-age=300` |
| | `GET /event/{id}/verses` | 사건별 근거 구절(JSON 오버레이) |
| `routes/search.py` | `GET /search?q=` | 이름/한국어 이름 CONTAINS 검색(완전일치/시작일치/포함 3단 랭크 정렬, 20개 한도) |
| `routes/books.py` | `GET /books` | 타임라인 배치용 책 목록(추정연도 병합·yearApprox 플래그, 연도 없는 책 제외) |
| | `GET /books-overview` | 개요 뷰 전용 전체 책 목록(`Cache-Control: no-store`) |

**Neo4j 연결**: `app/db.py` — `_driver` 싱글턴. `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD` 환경변수(비밀번호 필수).

---

### 4. 오버레이 데이터 계층 (overlays.py)

Neo4j에 주입하지 않는 보조 데이터를 JSON 파일로 관리. `functools.lru_cache(maxsize=1)`로 프로세스 수명 동안 1회만 읽는다.

| 함수 | 소스 파일 | 용도 |
|---|---|---|
| `book_events_raw()` | `data/book_events/books.json` | `{bookId: [eventId, ...]}` — 책이 기록한 사건 목록 |
| `approx_years()` | `data/book_years_approx/books.json` | `{bookId: {placementYear, basis, ...}}` — Neo4j startYear 없는 책의 추정 연도 |
| `event_verses()` | `data/event_verses/events.json` | 사건별 근거 구절 텍스트(한국어·영어 prebaked, ADR-0003) |

경로 해석: `DATA_DIR` 환경변수(기본 `/app/data`) → `_REPO_DATA_DIR`(저장소 내 `data/`) 순으로 fallback.
`routes/events.py`의 `_load_approx_book_index()`도 `book_events_raw()`를 역방향 인덱스로 가공해 사건→책 칩을 만들고, `_compute_events()`가 Neo4j 사건 쿼리와 머지한다(둘 다 lru_cache).

---

### 5. Neo4j 그래프 모델

노드 레이블 5종: `Person`, `Place`, `Event`, `PeopleGroup`, `Book`
공통 식별자: `theographic_id` 프로퍼티 (Theographic Bible Metadata 원본 ID, 저작 데이터는 `authored-*` ID)

릴레이션십:

| 관계 | 방향 |
|---|---|
| `PARENT_OF`, `CHILD_OF` | Person → Person |
| `SIBLING_OF`, `PARTNER_OF` | Person ↔ Person |
| `MEMBER_OF` | Person → PeopleGroup |
| `HAS_PARTICIPANT` | Event → Person |
| `OCCURS_AT` | Event → Place |
| `PART_OF` | Event → Event |
| `CONTAINS_BOOK` | Book → Event |

주입 프로퍼티: Book에 `background`/`themes`/`keyVerse`/메타(inject_book_context), Person에 `traits`(inject_person_traits),
Place에 `background`/`keyVerse`/`keyVerseTextKo`/`keyVerseTextEn`(inject_place_context), 전 레이블에 `nameKo`/`aliasesKo`(inject_ko_names).

---

## 데이터 흐름

### 지도 뷰

```
사용자 검색·노드 선택
  → App.jsx: selectNode(id)
  → MapView selection effect: apiGet(/node/{id}/places)
    → FastAPI nodes.py: Neo4j 쿼리(노드 라벨별 장소 패턴)
    → 장소 GeoJSON → maplibre-gl places-source (cluster:true)
    → Person이고 장소 3개↑면 convexHull로 hull-source 폴리곤(활동 범위)
    → primary(선택된 장소)는 fitBounds 정착 후 사건 링 자동 펼침
  → 장소 클릭: expandPlace() → apiGet(/node/{placeId}/neighbors/grouped)
    → 사건 링 애니메이션(ringPositions + requestAnimationFrame, easeOutCubic).
    → 같은 점에 겹친 마커가 여럿이면 spiderifyPlaces()로 방사 분산.
  → 라벨 배치: 최근접 이웃/링 중심의 반대 방향으로 text-anchor·text-offset 계산
    (outwardLabel/ringLabels/placesToGeoJSON, cos(lat) 세로 보정).
  → SidePanel: apiGet(/node/{id}) → 노드 상세 표시(Place면 배경·대표 구절 블록)
```

### 타임라인 뷰

```
최초 마운트: apiGet(/events)
  → FastAPI events.py: Neo4j 사건 쿼리 + approx_index 머지 (lru_cache)
  → 클라이언트: startDate 기준 그룹핑·정렬 (useMemo)
  → 책 칩 클릭: apiGet(/event/{id}/verses) → 인라인 구절 뷰(openEventRef로 out-of-order 가드)
```

### 성경 개요 뷰

```
최초 마운트: apiGet(/books-overview)
  → FastAPI books.py: Neo4j Book 쿼리 (bookOrder ASC)
  → 클라이언트: testament·genre로 그루핑 → 카드 그리드
```

---

## 데이터 파이프라인 (scripts/)

일회성 또는 수동 실행 스크립트(ADR-0006: `generate_*`는 LLM 직접 생성 결과를 담는 레시피 아티팩트, 실데이터는 LLM이 채운다).
경로 패턴: **LLM 생성 정적 JSON → (선택) getbible 절 본문 prebake → ① Neo4j inject/load 또는 ② 런타임 오버레이 → 프론트가 읽음.**

1. **로드(Neo4j MERGE)** — `load_theographic.py`(GitHub Theographic 원본 4파일 → Person/Place/Event/PeopleGroup 벌크 MERGE, 500/1000 배치), `load_books.py`(Book 노드), `load_authored_events.py`·`load_person_events.py`·`load_verse_events.py`(authored=true Event 노드 + 관계, ADR-0005), `enrich_place_coords.py`(`data/place_coords/` → Place 좌표 멱등 적재).
2. **주입(Neo4j SET)** — `inject_ko_names.py`(`names_ko/` → nameKo/aliasesKo), `inject_book_context.py`(`book_context/` → Book), `inject_person_traits.py`(`character_traits/` → Person traits), `inject_place_context.py`(`place_context/` → Place background·keyVerse·keyVerseTextKo/En).
3. **절 본문 prebake** — `generate_verse_text.py`가 getbible v2에서 한국어(korean)+영어(kjv) 본문을 빌드타임에 받아 4개 소스 파일에 인라인 저장: `event_verses`, `book_context`, `character_traits`, `place_context`(`bake_place_context()`, `PLACE_CONTEXT_PATH`). 멱등·캐시·재시도(ADR-0003).
4. **생성 레시피** — `generate_book_context*.py`, `generate_book_events.py`, `generate_approx_book_verses.py`, `generate_event_verses.py`, `generate_verse_events.py`, `generate_person_traits.py`, `generate_person_event_verses.py`.

오버레이로만 쓰여 Neo4j에 들어가지 않는 데이터: `book_events/`, `book_years_approx/`, `event_verses/`(ADR-0004 — 추정·보조 데이터는 그래프 밖 유지, CONTAINS_BOOK 주입 금지).

---

## 배포 및 빌드

- **프론트엔드**: `npm run build` → `frontend/dist/` (nginx 정적 서빙). 로컬 검증 전 빌드 필요(HMR 아님).
- **백엔드**: `docker build backend/` → uvicorn 0.0.0.0:8000
- **프록시**: nginx `/api/` → `api:8000/` 스트립 후 전달. index.html은 no-cache, 정적 에셋(js/css/png 등)은 1년 immutable.
- **환경변수**: `NEO4J_PASSWORD` 필수(compose `:?` 가드). `VITE_API_URL`은 `.env.production`에서 `/api`로 고정.
- **코드 분할**: `vite.config.js` manualChunks — maplibre-gl 별도 청크, 나머지 vendor 묶음.
- **의존성**: react 19, react-dom 19, maplibre-gl 5, lucide-react. Vite 8, eslint 10.
