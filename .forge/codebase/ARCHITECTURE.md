---
last_mapped_commit: ecdb7cb2ea1bf665b0690e62b4cf51261761072c
mapped: 2026-06-15
---

# 아키텍처

## 전체 패턴

3-tier 컨테이너 스택: **nginx(정적 서빙 + 리버스 프록시) → FastAPI(REST API) → Neo4j(그래프 DB)**.

```
브라우저
  │ :8080
  ▼
nginx (docker)
  ├─ /api/* → proxy_pass http://api:8000/
  └─ /*     → frontend/dist (SPA fallback)
       │
       ▼
FastAPI (docker, :8000)
  ├─ GET /search
  ├─ GET /events
  ├─ GET /node/{id}
  ├─ GET /node/{id}/places
  └─ GET /node/{id}/neighbors/grouped
       │ bolt://neo4j:7687
       ▼
Neo4j 5 (docker)
  └─ 그래프: Person · Place · Event · PeopleGroup · Book
```

## 컴포넌트 책임

| 컴포넌트 | 책임 | 파일 |
|---------|------|------|
| `App` | 전역 상태(selectedNode, activeView, searchQuery, history), 검색 디바운스, 탭 라우팅, SidePanel 오버레이 | `frontend/src/App.jsx` |
| `MapView` | maplibre-gl 지도, 장소 마커 레이어, 사건 링 애니메이션(rAF), convex hull GeoJSON | `frontend/src/MapView.jsx` |
| `TimelineView` | `/events` 전체 목록 fetch, startDate별 그룹핑, Book 필터 | `frontend/src/TimelineView.jsx` |
| `SidePanel` | 선택 노드 `/node/{id}` fetch, 이웃 타입별 그룹 렌더링, Person traits, Book 상세, 뒤로가기 | `frontend/src/SidePanel.jsx` |
| `api.js` | `apiGet(path, {signal})` 헬퍼, `VITE_API_URL` 기반 `API_BASE` | `frontend/src/api.js` |
| `theme.js` | `TYPE_COLOR`, `TYPE_KO`, `TYPE_ORDER`, `SELECT_HL` — 뷰 공유 팔레트 | `frontend/src/theme.js` |
| `convexHull.js` | Graham scan 볼록 껍질 순수 함수 | `frontend/src/convexHull.js` |
| `routes/nodes.py` | `/node/{id}`, `/node/{id}/places`, `/node/{id}/neighbors/grouped` | `backend/app/routes/nodes.py` |
| `routes/events.py` | `/events` — 전체 Event 목록(sortKey 정렬) | `backend/app/routes/events.py` |
| `routes/search.py` | `/search?q=` — nameKo/name 포함 검색, 관련도 rank 정렬 | `backend/app/routes/search.py` |
| `db.py` | Neo4j 드라이버 모듈 싱글톤(`_driver`), 환경변수로 bolt URI/auth 설정 | `backend/app/db.py` |
| `main.py` | FastAPI 앱 초기화, CORS 미들웨어(GET only), lifespan에서 인덱스 생성 | `backend/app/main.py` |

**GraphView는 제거됨** (`7500fec`). 탭 목록에 'map', 'timeline' 두 개만 존재.

## 레이어 구조

### 백엔드 (Python / FastAPI)

| 레이어 | 위치 | 역할 |
|--------|------|------|
| 진입점 | `backend/app/main.py` | FastAPI 인스턴스 생성, lifespan 훅(인덱스 생성), CORS 미들웨어, 라우터 등록 |
| DB 연결 | `backend/app/db.py` | Neo4j 드라이버 싱글턴(`_driver` 전역 변수). 환경변수 `NEO4J_URI / NEO4J_USER / NEO4J_PASSWORD` |
| 라우터 | `backend/app/routes/` | 기능별 파일 3개 — `nodes.py` / `events.py` / `search.py` |
| 스크립트 | `backend/scripts/` | 일회성 데이터 적재·주입 도구 (런타임에서 import 안 함) |

라우터는 모두 동기 함수(`def`)로 작성돼 있고, `get_driver()`로 드라이버를 가져와 `driver.session()` 컨텍스트 매니저 안에서 Cypher를 실행한다.

**lifespan 훅**: 앱 시작 시 5개 레이블(`Person Place Event PeopleGroup Book`)에 `theographic_id` 인덱스를 `CREATE INDEX IF NOT EXISTS`로 멱등 생성한다.

### 프론트엔드 (React 19 / Vite)

전역 상태를 `App.jsx`가 소유하고 props로 뷰 컴포넌트에 내린다. 탭 전환은 조건부 렌더링(`activeView`)으로 처리한다.

## 데이터 흐름

### 노드 선택 흐름

```
사용자 클릭(지도 마커 / 검색 결과 / SidePanel 링크)
  → App.selectNode(id)        -- useCallback([])으로 참조 안정화
  → selectedNode state 갱신
  → SidePanel: GET /node/{id} fetch
  → App.handleNodeLoaded(node) 콜백 → selectedNodeMeta 갱신
  → MapView: GET /node/{id}/places fetch → 마커 갱신 + convex hull 갱신
  → TimelineView: bookFilter prop 반응(Book 선택 시만)
```

### 검색 흐름

```
onSearchInput → searchQuery state
  → useEffect(searchQuery): 250ms 디바운스
  → GET /search?q=...  (AbortController로 경쟁 차단)
  → searchResults state → 드롭다운 렌더
  → 선택 → handleSelectResult → selectNode(id)
```

### 지도 마커 → 이벤트 링 흐름

```
마커 클릭(Place 노드)
  → expandPlace(placeId, lng, lat)
  → GET /node/{placeId}/neighbors/grouped
  → events 배열 추출
  → ringPositions() 계산 (zoom-adaptive 반경: 화면 80px → degrees 변환)
  → requestAnimationFrame 루프로 마커를 링 형태로 이동(400ms easeOutCubic)
  → 이벤트 마커 클릭 → selectNode(eventId)
```

### convex hull 흐름

```
selectedNode 변경 → MapView places fetch 완료
  → places 좌표 배열 → convexHull(points) 호출
  → hull-source GeoJSON 갱신
  → hull-fill(fill) + hull-outline(line) 레이어 렌더
  (Person 선택 시: 오렌지 계열, opacity 0.12 fill + 0.8 outline)
```

### 데이터 적재 파이프라인 (운영시 일회성 실행)

```
Theographic GitHub JSON
  → load_theographic.py      # Person / Place / Event / PeopleGroup 적재

data/names_ko/*.json
  → inject_ko_names.py       # nameKo / aliasesKo 주입

load_books.py                # Book 노드 적재, CONTAINS_BOOK 관계 생성
                             # (Book.verses ∩ Event.verses 교집합 기준)

data/character_traits/people.json
  → inject_person_traits.py  # Person.traits (JSON 문자열) 주입

data/book_context/books.json
  → inject_book_context.py   # Book.background / themes / keyVerse 주입
```

LLM 생성 도구 (오프라인):
- `generate_book_context.py` → `data/book_context/books.json`
- `generate_person_traits.py` → `data/character_traits/people.json`

## 주요 API 엔드포인트

| 메서드·경로 | 반환 | 비고 |
|------------|------|------|
| `GET /search?q=` | `[{id, label, name, nameKo}]` | 최대 20건, 정확도 rank 정렬 |
| `GET /events` | `[{id, title, nameKo, startDate, sortKey}]` | `Cache-Control: no-store` |
| `GET /node/{id}` | 노드 상세 + neighbors(최대 50) + neighborTotal | Book이면 topPersons·topEvents 추가 |
| `GET /node/{id}/places` | `{label, places:[{id, name, nameKo, lat, lng, isPrimary}]}` | 레이블별 Cypher 분기 |
| `GET /node/{id}/neighbors/grouped` | `{Person, Place, Event, PeopleGroup}` 각 최대 30건 | 이벤트 링 전용 |

`/node/{id}`의 Book 노드 응답 추가 필드: `topPersons`(이벤트 참여 횟수 상위 10인), `topEvents`(startDate 정렬 상위 10건).

Person 노드의 `traits` 속성: Neo4j에 JSON 문자열로 저장 → `get_node()`에서 파싱 후 배열로 반환.

## Neo4j 그래프 스키마

**노드 레이블**: `Person · Place · Event · PeopleGroup · Book`

**관계 타입**:
- `HAS_PARTICIPANT`: Event → Person
- `OCCURS_AT`: Event → Place
- `MEMBER_OF`: Person → PeopleGroup
- `PART_OF`: Event → Event (계층)
- `PARENT_OF / CHILD_OF / SIBLING_OF / PARTNER_OF`: Person ↔ Person
- `CONTAINS_BOOK`: Book → Event

**공통 속성**: `theographic_id`(전 노드 인덱스 키), `name`, `nameKo`, `aliasesKo`

**Book 전용 속성**: `testament`, `genre`, `authorKo`, `startYear`, `endYear`, `chapterCount`, `background`, `themes`, `keyVerse`

**Person 전용 속성**: `traits` (JSON 문자열 → API 레이어에서 배열로 파싱)

## 주요 추상화

**`theme.js`**: 타입 색·라벨의 유일한 정의처. `App / SidePanel / MapView / TimelineView`가 import. 이 파일 밖에서 타입 색을 직접 상수로 정의하면 안 된다.

**`api.js`**: `API_BASE` 상수와 `apiGet` 헬퍼. 단, `MapView.jsx`와 `SidePanel.jsx`는 아직 내부 `API_URL` 상수를 직접 선언해 `fetch()`를 호출하는 패턴이 공존한다(부분 마이그레이션 상태).

**`convexHull.js`**: 맵과 무관한 순수 기하 함수. `MapView`에서만 사용.

**`selectedNodeRef`**: `selectNode` useCallback이 `[]` deps로 참조 안정화하면서도 최신 `selectedNode` 값을 읽기 위한 패턴. `frontend/src/App.jsx` 참조.

## 상태 관리

- `selectedNode` (string | null): `App.jsx` 소유, props로 `MapView / TimelineView / SidePanel`에 전달
- `selectedNodeMeta` ({label, nameKo, startYear, endYear} | null): SidePanel의 `onNodeLoaded` 콜백으로 수신
- `history` (string[]): 뒤로가기 스택, `App.jsx` 소유
- `activeView` ('map' | 'timeline'): `App.jsx` 소유
- `searchQuery`, `searchResults`, `typeFilter`: `App.jsx` 소유
- 지도 내부 상태(expandedPlace, animFrame 등): `MapView` 내 mutable refs (React state 아님 — 리렌더 방지)

## 아키텍처 제약

- **CORS:** `allow_origins=["*"]`, `allow_methods=["GET"]` — 읽기 전용 API
- **Neo4j 드라이버:** 모듈 수준 싱글톤 `_driver`. 각 요청마다 `driver.session()` 컨텍스트 매니저 사용
- **핫리로드 없음:** 백엔드 코드 변경 시 `docker compose up -d --build api` 재빌드 필요
- **이웃 수 상한:** `NODE_NEIGHBOR_LIMIT = 50` (GET /node/{id}), `MAX_NEIGHBORS_PER_TYPE = 30` (GET /node/{id}/neighbors/grouped)
- **검색 결과 상한:** `SEARCH_LIMIT = 20`

## 오류 처리

각 컴포넌트가 개별적으로 fetch 실패를 로컬 error state로 처리한다.

- `SidePanel`: `state.error` → 오류 메시지 렌더링
- `MapView`: `error` state → 오류 배너(nav 뒤 가려짐 이슈 미해결, `task_c16549df`), `noLocation` state → 빈 위치 안내
- `TimelineView`: `error` state → 전체화면 오류 메시지
- `App` 검색: `searchError` state → 드롭다운 내 오류 메시지, AbortError는 무시
- `apiGet`: non-OK → `throw res.status` (숫자), AbortError → 그대로 전파

## 배포

`deploy.sh` 순서:
1. `npm run build` → `frontend/dist/`
2. `docker compose build api` (백엔드 이미지)
3. `docker compose up -d api nginx`
4. `inject_ko_names.py` 실행 (Neo4j 준비까지 최대 15회 재시도)

프론트는 `frontend/.env.production`의 `VITE_API_URL=/api`로 빌드되어 nginx 프록시(`/api → api:8000`)를 경유한다.
