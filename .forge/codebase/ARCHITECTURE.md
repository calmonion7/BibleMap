---
last_mapped_commit: 9f47b78ed927ef302cefffb5b62ef71885b6aa94
mapped: 2026-06-19
---

# BibleMap 아키텍처

## 전체 구성

3-레이어 Docker Compose 스택: **Neo4j(그래프 DB) ← FastAPI(API 서버) ← nginx(리버스 프록시 + 정적 파일)**

```
브라우저
  └─ :8080 (nginx)
       ├─ /api/* → api:8000 (FastAPI, uvicorn)
       │              └─ bolt://neo4j:7687 (Neo4j 5 Community)
       └─ /       → frontend/dist (Vite 빌드 산출물, 정적 파일)
```

컨테이너는 `docker-compose.yml` 단일 파일로 정의된다. `neo4j`·`api`·`nginx` 세 서비스, `neo4j_data` 볼륨 하나.

---

## 레이어별 진입점

### Neo4j
- 이미지: `neo4j:5` (Community Edition, APOC 미사용 — ADR-0001)
- 포트: 호스트 `127.0.0.1:7474`(HTTP Browser), `127.0.0.1:7687`(Bolt)
- `theographic_id` 속성에 인덱스(`person_tid` 등 레이블별 5개) — FastAPI 기동 시 `lifespan()`이 `CREATE INDEX … IF NOT EXISTS`로 생성

### FastAPI (백엔드)
- 진입점: `backend/app/main.py`의 `app` 객체
- 런타임: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
- Docker 이미지: `python:3.12-slim`, `/app/data`에 호스트 `./data` 볼륨 마운트
- 의존성: `fastapi 0.136`, `neo4j 6.2`, `uvicorn 0.49`

### nginx
- 이미지: `nginx:alpine`
- `/api/` → `http://api:8000/` 프록시 (trailing slash strip)
- `/` → `/usr/share/nginx/html`(= `frontend/dist`) SPA fallback(`try_files $uri /index.html`)
- 정적 파일: `Cache-Control: public, max-age=31536000, immutable` / `index.html`: `no-cache`

### React 프론트엔드
- 빌드 도구: Vite 8 + `@vitejs/plugin-react`
- 진입점: `frontend/src/main.jsx` → `frontend/index.html`
- 빌드 산출물: `frontend/dist/` (nginx 마운트)
- 코드 분할: `vite.config.js`의 `manualChunks` — `maplibre-gl` → `maplibre` 청크, 나머지 `node_modules` → `vendor` 청크

---

## 데이터 모델 (Neo4j 그래프)

### 노드 레이블 및 주요 속성

| 레이블 | 핵심 속성 |
|---|---|
| `Person` | `theographic_id`, `name`, `nameKo`, `traits`(JSON 문자열) |
| `Place` | `theographic_id`, `name`, `nameKo`, `latitude`, `longitude` |
| `Event` | `theographic_id`, `name`/`title`, `nameKo`, `startDate`, `sortKey`, `authored`(bool), `yearLabel` |
| `PeopleGroup` | `theographic_id`, `name`, `nameKo` |
| `Book` | `theographic_id`, `name`, `nameKo`, `testament`, `bookOrder`, `startYear`, `endYear`, `background`, `themes`, `keyVerse`, `keyVerseTextKo`, `keyVerseTextEn` |

### 관계 타입

| 관계 | 방향 | 의미 |
|---|---|---|
| `CONTAINS_BOOK` | `Book → Event` | 해당 권이 해당 사건을 기록함(구절 교집합으로 결정) |
| `HAS_PARTICIPANT` | `Event → Person` | 사건 참여자 |
| `OCCURS_AT` | `Event → Place` | 사건 발생 장소 |
| `MEMBER_OF` | `Person → PeopleGroup` | 집단 소속 |
| `PART_OF` | `Event → Event` | 하위 사건 → 상위 사건(Period 계층) |
| `PARENT_OF` / `CHILD_OF` / `SIBLING_OF` / `PARTNER_OF` | `Person ↔ Person` | 인물 관계 |

---

## API 레이어

모든 엔드포인트는 GET 전용. CORS는 `allow_origins=["*"]`, `allow_methods=["GET"]`.

### 라우터 구성 (`backend/app/routes/`)

**`nodes.py`** — 노드 탐색 3종
- `GET /node/{node_id}` — 노드 상세 + 이웃 목록(LIMIT 50) + 총 이웃 수. Book이면 `topPersons`/`topEvents` 추가. Person이면 `traits` JSON 파싱.
- `GET /node/{node_id}/places` — 노드 타입별 관련 좌표 장소 목록(Person→이벤트→장소, Place→직접, Event→직접, PeopleGroup→구성원→이벤트→장소, Book→CONTAINS_BOOK→장소)
- `GET /node/{node_id}/neighbors/grouped` — 이웃을 레이블별로 그룹(Person/Event/PeopleGroup/Place), 타입당 최대 30건
- `GET /person/{node_id}/event-ids` — Person이 참여한 Event의 `theographic_id` 목록 (타임라인 인물 필터용)

**`events.py`** — 타임라인 이벤트
- `GET /events` — 전체 Event 목록, `sortKey` 순. 각 이벤트에 `CONTAINS_BOOK` 근거 책 배열(정경순) + 추정책 오버레이 append. `lru_cache` 인덱스 빌드는 최초 1회.
- `GET /event/{event_id}/verses` — 사건의 근거 구절을 권별 그룹으로 반환(`data/event_verses/events.json` 오버레이, 절 본문 `textKo`/`textEn` 인라인 — ADR-0003)

**`search.py`** — 검색
- `GET /search?q=` — `nameKo`·`name` 부분 일치, LIMIT 20. 완전 일치 → 전방 일치 → 부분 일치 순으로 rank.

**`books.py`** — 성경책 목록
- `GET /books` — 전체 Book 목록, `bookOrder` 순. `startYear` 없는 책은 `data/book_years_approx/books.json` 오버레이(`yearApprox=true`). `data/book_events/books.json` 오버레이로 각 책에 `events` 배열 추가.

### 런타임 오버레이 패턴 (ADR-0004)

추정·보조 데이터는 Neo4j에 넣지 않고 정적 JSON 파일을 `lru_cache(maxsize=1)`로 1회 로드 후 엔드포인트 응답에 병합한다. `./data:/app/data` 볼륨 마운트라 JSON만 교체하면 api 재시작 없이도 다음 콜드 캐시에서 반영된다.

탐색 경로: `DATA_DIR` 환경변수(기본 `/app/data`) 우선 → 레포 상대경로 폴백.

---

## 프론트엔드 아키텍처

### 컴포넌트 계층

```
main.jsx
└─ App.jsx  (전역 상태 허브)
     ├─ MapView.jsx        (지도 뷰, maplibre-gl)
     ├─ TimelineView.jsx   (타임라인 뷰, 순수 CSS/DOM)
     │    └─ VerseLangTabs.jsx
     └─ SidePanel.jsx      (우측 상세 패널 / 모바일 하단 시트)
          └─ VerseLangTabs.jsx
```

### App.jsx — 전역 상태

| 상태 | 타입 | 역할 |
|---|---|---|
| `selectedNode` | `string \| null` | 현재 선택된 노드의 `theographic_id` |
| `selectedNodeMeta` | `object \| null` | 선택 노드의 label·nameKo·startYear·endYear |
| `personEventIds` | `Set \| null` | Person 선택 시 해당 인물 참여 이벤트 ID 집합 (타임라인 필터) |
| `activeView` | `'map' \| 'timeline'` | 현재 활성 뷰 탭 |
| `history` | `string[]` | SidePanel 뒤로가기용 노드 ID 스택 |
| `verseLang` | `'ko' \| 'en'` | 구절 본문 표시 언어 (TimelineView·SidePanel 공유) |

`selectNode` 콜백은 `useCallback([])` + `selectedNodeRef`로 참조를 안정화해 MapView의 fetch abort 버그를 방지한다.

### API 클라이언트

`frontend/src/api.js` — 단일 `apiGet(path, { signal })` 헬퍼. `VITE_API_URL`(프로덕션: `/api`) + path로 fetch, 비-OK면 status 코드 throw. 모든 컴포넌트는 이 함수를 통해서만 API 호출.

### MapView.jsx

- `maplibre-gl` 5.x로 ESRI NatGeo 래스터 타일 렌더링. 초기 중심: 이스라엘(`[35.22, 31.78]`, zoom 5).
- `selectedNode` 변경 시 `GET /node/{id}/places`로 마커 갱신.
- 장소 마커 클릭 → `expandPlace`: 해당 장소의 사건들을 **방사형 링**으로 애니메이션 펼침(requestAnimationFrame, easeOutCubic).
- 볼록 껍질(`frontend/src/convexHull.js`, Graham scan 구현)로 다수 마커의 외곽 폴리곤 표시.
- 모바일(`max-width: 768px`) 분기: 하단 시트 패딩(`SHEET_VH=55`)에 맞춰 fitBounds 하단 패딩 조정.

### TimelineView.jsx

- 마운트 시 `GET /events` 1회 fetch. 동일 `startDate`끼리 그룹화 후 `sortKey` 오름차순 정렬.
- `bookFilter`(Book 선택 시 해당 연대 범위 하이라이트) / `personFilter`(Person 선택 시 `personEventIds`로 해당 사건만 표시) 지원.
- 사건 클릭 → `GET /event/{id}/verses`로 근거 구절 로드, 탭 전환 없이 인라인 펼침(`verseView` state). `openEventRef`로 out-of-order 응답 무시.
- `authored:true` 사건은 "추정" 배지 + `yearLabel`(범위 라벨) 표시.

### SidePanel.jsx

- `nodeId` prop 변경 시 `GET /node/{nodeId}` fetch. `cancelled` 플래그로 stale 응답 무시.
- 이웃 노드 그룹(Person/Place/Event/PeopleGroup/Unknown) 기본 접힘, 헤더 클릭으로 토글.
- Book 노드: `topPersons`·`topEvents`·`keyVerseTextKo/En` 표시.
- Person 노드: `traits` 배열(trait·verse_ref·description) 렌더링 + 구절 본문(`textKo`/`textEn`).
- 데스크톱: 우측 360px 슬라이드인, 모바일: 하단 `55vh` 시트.

---

## 데이터 파이프라인 (스크립트)

### 초기 적재 (`backend/scripts/`)

| 스크립트 | 역할 |
|---|---|
| `load_theographic.py` | GitHub `robertrouse/theographic-bible-metadata` JSON 직접 fetch → Neo4j MERGE. APOC 미사용(ADR-0001). `status=="publish"` 필터. |
| `load_books.py` | Theographic `books.json` 적재 + `Book.verses ∩ Event.verses` 교집합으로 `CONTAINS_BOOK` 관계 생성. `startYear`는 연결 사건 `startDate` 집계. |
| `load_authored_events.py` | `data/authored_events/events.json`을 Neo4j `Event` 노드로 적재. `authored:true` 마킹(ADR-0005). `rec` 접두 없이 `authored-<slug>` ID 사용. |
| `load_verse_events.py` | `data/verse_events/events.json` 적재 |
| `inject_ko_names.py` | `data/names_ko/*.json`의 한국어 이름을 기존 노드에 `nameKo` 속성으로 주입. deploy.sh가 호출. |
| `inject_person_traits.py` | `data/character_traits/people.json` → Person 노드 `traits` 속성 주입 |
| `inject_book_context.py` | `data/book_context/books.json` → Book 노드 `background`·`themes`·`keyVerse`·`keyVerseTextKo/En` 주입 |

### LLM 생성 스크립트 (빌드타임 데이터 생성, ADR-0006)

| 스크립트 | 생성 데이터 |
|---|---|
| `generate_person_traits.py` | `data/character_traits/people.json` |
| `generate_book_context.py` | `data/book_context/books.json` |
| `generate_book_events.py` | `data/book_events/books.json` (추정책 → 사건 오버레이) |
| `generate_approx_book_verses.py` | `data/book_years_approx/books.json` 보강 |
| `generate_event_verses.py` | `data/event_verses/events.json` 초안 |
| `generate_verse_events.py` | `data/verse_events/events.json` |
| `generate_verse_text.py` | getbible.net에서 한/영 절 본문 빌드타임 1회 fetch, 3개 데이터에 `textKo`/`textEn` 주입(ADR-0003) |

---

## 배포

- GitHub Actions (`.github/workflows/deploy.yml`): `main` 브랜치 push → self-hosted runner에서 `git reset --hard origin/main && bash deploy.sh`
- `deploy.sh` 순서: (1) `npm run build` → `frontend/dist/` (2) `docker compose build api` (3) `docker compose up -d api nginx` (4) `inject_ko_names.py` (Neo4j 준비 대기 최대 30초)
- `.env`의 `NEO4J_PASSWORD`가 docker compose와 inject 스크립트 모두에서 사용됨
