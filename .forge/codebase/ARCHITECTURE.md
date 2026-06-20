---
last_mapped_commit: 7a1ef362b1fb247b09edeeaa1380e6449fce5721
mapped: 2026-06-20
---

# 아키텍처

## 전체 구성

프론트엔드 SPA(React + Vite) → nginx 리버스 프록시 → FastAPI 백엔드 → Neo4j 그래프 DB.
정적 오버레이 데이터는 Neo4j가 아닌 `data/` 디렉터리의 JSON 파일에서 바로 읽는다(ADR-0001, ADR-0004).

```
브라우저
  └─ :8080 nginx
        ├─ /api/* → api:8000 (FastAPI, uvicorn)
        │              └─ bolt://neo4j:7687 (Neo4j 5)
        └─ /*     → frontend/dist (Vite 빌드 결과물, SPA)
```

컨테이너는 `docker-compose.yml`이 `neo4j`, `api`, `nginx` 세 서비스로 구성한다.

---

## 레이어 구조

### 1. 프론트엔드 (React SPA)

**진입점**: `frontend/src/main.jsx` → `frontend/src/App.jsx`

`App.jsx`가 최상위 상태를 소유한다.

| 관심사 | 구현 |
|---|---|
| 노드 선택·히스토리 | `useNodeSelection` 커스텀 훅 |
| 검색 쿼리·결과·드롭다운 | `useSearch` 커스텀 훅 |
| 뷰 전환 | `activeView` state (`map` / `timeline` / `overview`) |
| 구절 언어 토글 | `verseLang` state (ko/en) — 하위 컴포넌트에 prop으로 전달 |

**뷰 컴포넌트**

- `MapView.jsx` — maplibre-gl 지도. 장소 마커, 클러스터, 스파이더파이, 사건 링(방사형), 볼록 껍질(Person 활동 범위).
- `TimelineView.jsx` — 사건을 `startDate` 기준 그룹으로 세로 타임라인 렌더. 책 칩(근거 구절 인라인 드릴다운) 포함.
- `BibleOverviewView.jsx` — `/books-overview` 데이터로 구약·신약을 장르별 카드 그리드로 표시.

세 뷰는 항상 마운트되어 있으며 CSS `display` 토글로 상태를 보존한다.

**공유 패널**: `SidePanel.jsx` — 선택된 노드의 상세 정보(이웃 그룹, 인물 성품, 책 전용 뷰).  
오버레이 패널로 데스크톱은 우측 슬라이드인, 모바일은 하단 시트(SHEET_VH=55vh).

**공유 UI**: `Spinner.jsx`, `VerseLangTabs.jsx`  
**공유 팔레트**: `theme.js` — TYPE_COLOR, TYPE_KO, TYPE_ORDER, SELECT_HL  
**순수 유틸**: `convexHull.js` (Graham scan), `api.js` (단일 apiGet 헬퍼)

---

### 2. API 클라이언트 (api.js)

모든 HTTP 요청의 단일 창구. `VITE_API_URL` 환경변수(빌드타임)로 베이스 URL을 결정한다.

- 개발: `http://localhost:8000`
- 프로덕션 빌드: `/api` (nginx 프록시 경유)

```js
// fetch → JSON, 비-OK는 status로 reject, AbortError는 그대로 전파
export async function apiGet(path, { signal } = {})
```

---

### 3. 백엔드 (FastAPI)

**진입점**: `backend/app/main.py`

시작 시 `lifespan` 핸들러가 Neo4j에 theographic_id 인덱스 5종을 생성(없으면 건너뜀).  
라우터 4개를 `include_router`로 등록. CORS는 GET 전용 `allow_origins=["*"]`.

**라우터 구조**

| 파일 | 엔드포인트 | 역할 |
|---|---|---|
| `routes/nodes.py` | `GET /node/{id}` | 노드 상세 + 이웃(50개 한도) |
| | `GET /node/{id}/neighbors/grouped` | 이웃을 타입별 그룹으로(30개/타입) |
| | `GET /node/{id}/places` | 노드 종류별 관련 장소 목록 |
| | `GET /person/{id}/event-ids` | 인물 참여 사건 ID 목록 |
| `routes/events.py` | `GET /events` | 전체 사건 목록(정경순 책 칩 포함) — `lru_cache` |
| | `GET /event/{id}/verses` | 사건별 근거 구절(JSON 오버레이) |
| `routes/search.py` | `GET /search?q=` | 이름/한국어 이름 CONTAINS 검색 |
| `routes/books.py` | `GET /books` | 타임라인 배치용 책 목록(추정연도 병합) |
| | `GET /books-overview` | 개요 뷰 전용 전체 책 목록 |

**Neo4j 연결**: `app/db.py` — `_driver` 싱글턴. `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD` 환경변수.

---

### 4. 오버레이 데이터 계층 (overlays.py)

Neo4j에 없는 보조 데이터를 JSON 파일로 관리. `functools.lru_cache(maxsize=1)`로 프로세스 수명 동안 1회만 읽는다.

| 함수 | 소스 파일 | 용도 |
|---|---|---|
| `book_events_raw()` | `data/book_events/books.json` | `{bookId: [eventId, ...]}` — 책이 기록한 사건 목록 |
| `approx_years()` | `data/book_years_approx/books.json` | `{bookId: {placementYear, basis, ...}}` — Neo4j startYear 없는 책의 추정 연도 |
| `event_verses()` | `data/event_verses/events.json` | 사건별 근거 구절 텍스트(한국어·영어 prebaked, ADR-0003) |

경로 해석: `DATA_DIR` 환경변수 → `_REPO_DATA_DIR`(빌드 컨텍스트 내 `data/`) 순으로 fallback.

---

### 5. Neo4j 그래프 모델

노드 레이블 5종: `Person`, `Place`, `Event`, `PeopleGroup`, `Book`  
공통 식별자: `theographic_id` 프로퍼티 (Theographic Bible Metadata 원본 ID)

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

---

## 데이터 흐름

### 지도 뷰

```
사용자 검색·노드 선택
  → App.jsx: selectNode(id)
  → MapView useEffect: apiGet(/node/{id}/places)
    → FastAPI nodes.py: Neo4j 쿼리(노드 종류별 장소 패턴)
    → 장소 GeoJSON → maplibre-gl places-source
  → 장소 클릭: expandPlace() → apiGet(/node/{placeId}/neighbors/grouped)
    → 사건 링 애니메이션(requestAnimationFrame)
  → SidePanel: apiGet(/node/{id}) → 노드 상세 표시
```

### 타임라인 뷰

```
최초 마운트: apiGet(/events)
  → FastAPI events.py: Neo4j 사건 쿼리 + approx_index 머지 (lru_cache)
  → 클라이언트: startDate 기준 그룹핑·정렬 (useMemo)
  → 책 칩 클릭: apiGet(/event/{id}/verses) → 인라인 구절 뷰
```

### 성경 개요 뷰

```
최초 마운트: apiGet(/books-overview)
  → FastAPI books.py: Neo4j Book 쿼리 (bookOrder ASC)
  → 클라이언트: testament·genre로 그루핑 → 카드 그리드
```

---

## 데이터 파이프라인 (scripts/)

일회성 또는 수동 실행 스크립트. 실행 결과는 Neo4j에 직접 쓰거나 `data/` 하위 JSON 파일로 저장된다.

1. `load_theographic.py` — GitHub의 Theographic Bible Metadata JSON을 Neo4j에 벌크 로드(500/1000 배치 MERGE)
2. `load_books.py` — Book 노드 생성
3. 기타 `generate_*`, `inject_*`, `load_*` — LLM 생성 데이터를 Neo4j 노드 프로퍼티에 주입하거나 `data/` JSON 파일에 기록

---

## 배포 및 빌드

- **프론트엔드**: `npm run build` → `frontend/dist/` (nginx 정적 서빙)
- **백엔드**: `docker build backend/` → uvicorn 0.0.0.0:8000
- **프록시**: nginx `/api/` → `api:8000/` 스트립 후 전달
- **환경변수**: `NEO4J_PASSWORD` 필수. `VITE_API_URL`은 `.env.production`에서 `/api`로 고정.
- **코드 분할**: `vite.config.js` manualChunks — maplibre-gl 별도 청크, 나머지 vendor 묶음
