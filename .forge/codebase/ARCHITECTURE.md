---
last_mapped_commit: 4ed4d876d7fa3b06a8eb1647b5b50ed73f906b25
mapped: 2026-06-19
---

# BibleMap 아키텍처

## 전체 패턴

**계층형 모놀리식 멀티 컨테이너** 구성이다. 단일 Git 저장소 안에 프론트엔드(SPA), 백엔드(REST API), 데이터베이스(Neo4j), 역방향 프록시(Nginx)가 공존하며, Docker Compose로 네 컨테이너를 묶어 실행한다.

```
[브라우저] → Nginx:8080 → {/api/*} → FastAPI:8000 → Neo4j:7687
                        → {정적 파일} → frontend/dist/
```

---

## 레이어 및 책임

### 1. 프레젠테이션 레이어 — `frontend/`

- **기술 스택**: React 19, Vite 8, MapLibre GL
- **진입점**: `frontend/src/main.jsx` (React 마운트) / `frontend/index.html`
- **최상위 상태 관리**: `frontend/src/App.jsx`
  - 선택된 노드(`selectedNode`), 뷰 전환(`activeView`), 검색 상태, 히스토리 스택을 단일 컴포넌트에서 보유
  - `selectedNode`가 `null`이면 패널 숨김, 값이 있으면 SidePanel 슬라이드인(데스크톱) 또는 바텀시트(모바일)
- **뷰 컴포넌트**:
  - `frontend/src/MapView.jsx` — MapLibre GL 지도, 장소 마커, fitBounds
  - `frontend/src/TimelineView.jsx` — 수평 타임라인, 사건·책 배치
  - `frontend/src/SidePanel.jsx` — 선택 노드 상세, 이웃, 성경 구절
- **공유 유틸**:
  - `frontend/src/api.js` — 단일 `apiGet()` 헬퍼; 빌드타임 `VITE_API_URL` 환경변수로 base URL 결정
  - `frontend/src/theme.js` — 노드 타입별 색상, 정렬 순서
  - `frontend/src/convexHull.js` — 장소 군집 볼록껍질 계산

### 2. API 레이어 — `backend/`

- **기술 스택**: FastAPI 0.136, Uvicorn, Python 3.12
- **진입점**: `backend/app/main.py`
  - `lifespan` 핸들러에서 Neo4j 인덱스 생성(Person/Place/Event/PeopleGroup/Book의 `theographic_id`)
  - CORS: GET 전용, `allow_origins=["*"]`
- **라우터 모듈** (`backend/app/routes/`):
  - `nodes.py` — `/node/{id}`, `/node/{id}/places`, `/node/{id}/neighbors/grouped`, `/person/{id}/event-ids`
  - `events.py` — `/events`, `/event/{id}/verses`
  - `books.py` — `/books`
  - `search.py` — `/search?q=`
- **DB 연결**: `backend/app/db.py` — 싱글턴 `GraphDatabase.driver`, 환경변수로 연결정보 주입

### 3. 데이터 레이어 — Neo4j + JSON 오버레이

- **Neo4j 5**: 모든 엔티티(Person/Place/Event/PeopleGroup/Book)를 그래프 노드로 저장. 관계: `HAS_PARTICIPANT`, `OCCURS_AT`, `MEMBER_OF`, `CONTAINS_BOOK`
- **JSON 오버레이** (`data/` 디렉터리, Docker 볼륨 마운트):
  - `event_verses/events.json` — 사건→구절 매핑(드릴다운용)
  - `book_events/books.json` — 책→사건 매핑(추정책 연결)
  - `book_years_approx/books.json` — Neo4j에 없는 책의 추정 연도
  - 위 파일들은 `functools.lru_cache(maxsize=1)`로 프로세스 수명 동안 메모리 캐싱됨

### 4. 역방향 프록시 — `nginx/`

- **역할**: 정적 SPA 서빙 + `/api/` 경로를 FastAPI로 프록시
- **설정**: `nginx/nginx.conf`
  - `/api/` → `http://api:8000/` (trailing slash strip)
  - `*.js|*.css|…` → `max-age=31536000, immutable`
  - `index.html` → `no-cache`
  - 나머지 → `try_files $uri /index.html` (SPA 라우팅)

---

## 데이터 흐름 (요청 → 응답)

### 지도 노드 선택 흐름

```
1. 사용자가 지도 마커 클릭
   → MapView.jsx: onSelectNode(id) 콜백 호출
2. App.jsx: setSelectedNode(id), SidePanel 슬라이드인
3. SidePanel.jsx: apiGet('/node/{id}') fetch
   → Nginx /api/node/{id} → FastAPI GET /node/{id}
   → Neo4j: MATCH (n {theographic_id: $id}) ... RETURN
4. SidePanel: 노드 상세 렌더링, onNodeLoaded 콜백 → App 메타 업데이트
```

### 타임라인 초기 로드 흐름

```
1. TimelineView 마운트
   → apiGet('/events') + apiGet('/books') 병렬 fetch
   → FastAPI: _compute_events() (lru_cache, max-age=300)
              + get_books() (lru_cache approx, no-store)
2. events: Neo4j 쿼리 + book_events.json approx_index 머지
3. books: Neo4j + book_years_approx.json 오버레이 머지
4. 프론트: sortKey/startYear 기준으로 레인 배치 렌더링
```

### 검색 흐름

```
사용자 입력 → 250ms 디바운스 → apiGet('/search?q=')
→ Neo4j: nameKo/name 부분일치, rank(정확→접두→포함) 정렬, LIMIT 20
→ 드롭다운 타입 필터 칩 + 결과 목록
```

---

## 핵심 추상

| 추상 | 위치 | 설명 |
|---|---|---|
| `apiGet()` | `frontend/src/api.js` | 전 fetch의 단일 게이트웨이; AbortController 지원 |
| `get_driver()` | `backend/app/db.py` | 싱글턴 Neo4j 드라이버 |
| `_compute_events()` | `backend/app/routes/events.py` | Neo4j+JSON 머지 결과 lru_cache |
| `theographic_id` | Neo4j 노드 속성 | 모든 엔티티의 공통 식별자; 인덱스 대상 |
| `lru_cache(maxsize=1)` | `events.py`, `books.py` | JSON 오버레이+쿼리 결과 프로세스 수명 캐시 |

---

## 진입점 정리

| 진입점 | 경로 |
|---|---|
| 프론트 React 마운트 | `frontend/src/main.jsx` |
| HTML 쉘 | `frontend/index.html` |
| FastAPI 앱 객체 | `backend/app/main.py` → `app` |
| Uvicorn 실행 | `CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]` (Dockerfile) |
| Docker 오케스트레이션 | `docker-compose.yml` |
| 배포 스크립트 | `deploy.sh` |
