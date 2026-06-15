---
last_mapped_commit: bfc1dd258b0308435ca24c48a82c9c86a9e622f1
mapped: 2026-06-16
---

# ARCHITECTURE

## 전체 패턴

3-티어 단방향 구성이다. SPA 프론트엔드(React + MapLibre)가 REST 백엔드(FastAPI)를 호출하고, 백엔드는 그래프 DB(Neo4j)와 디스크의 JSON 오버레이 파일을 읽어 응답을 만든다.

```
브라우저(React SPA)
   │  fetch(GET) — apiGet()
   ▼
FastAPI (uvicorn)  ──►  Neo4j (bolt, Cypher)
   │                └►  data/*.json  (디스크 오버레이, /books 라우트만)
   ▼
JSON 응답
```

프로덕션에서는 nginx가 정적 SPA(`frontend/dist/`)를 서빙하고 `/api/` 경로를 API 컨테이너로 프록시한다(`nginx/nginx.conf` 의 `location /api/ → proxy_pass http://api:8000/`). 세 서비스(`neo4j` / `api` / `nginx`)는 `docker-compose.yml` 로 묶인다.

데이터 흐름은 **읽기 전용 단방향**이다. 런타임 API는 모두 `GET`이며(`backend/app/main.py` 의 `allow_methods=["GET"]`), 쓰기는 런타임 경로가 아니라 별도 오프라인 적재 스크립트(`backend/scripts/`)로만 일어난다.

## 레이어

### 1. 프론트엔드 (`frontend/`)
- 빌드: Vite + React 19. 진입점은 `frontend/index.html` → `frontend/src/main.jsx`(`createRoot(...).render(<App/>)`) → `frontend/src/App.jsx`.
- `App.jsx` 가 셸. 상단 플로팅 nav(지도/타임라인 탭 + 검색창), 전체화면 뷰 1개, 오버레이 상세 패널을 한 컴포넌트에서 상태로 제어한다. 핵심 공유 상태: `selectedNode`(선택된 노드 id), `selectedNodeMeta`, `activeView`('map'|'timeline'), 검색 상태, `history`(패널 뒤로가기 스택). 뷰포트 폭으로 모바일 분기(`MOBILE_QUERY = '(max-width: 768px)'`) — 모바일은 상세를 우측 사이드패널 대신 하단 시트(`SHEET_VH = 55`)로 띄운다. 검색은 250ms 디바운스 + `AbortController` 경쟁 차단.
- 뷰 컴포넌트:
  - `frontend/src/MapView.jsx` — MapLibre GL 래스터 지도(ESRI NatGeo 타일). 선택 노드의 장소를 GeoJSON source로 그리고, `convexHull`로 인물 다지점 hull 폴리곤을 그린다. 장소 클릭 시 사건을 방사형 링으로 애니메이션 펼침(`expandPlace`/`collapseRing`, `requestAnimationFrame`). 카메라는 `fitBounds`로 맞춘다. 장소 0개 노드는 `noLocation` 안내 배너.
  - `frontend/src/TimelineView.jsx` — `/events` 와 `/books` 를 연도순으로 합쳐 통합 타임라인을 그린다. 같은 연도 사건은 그룹핑. Book 선택 시 그 연대 범위로 필터(`bookFilter`). 추정연도 책은 점선 마커 + "추정" 배지로 구분.
  - `frontend/src/SidePanel.jsx` — 선택 노드 상세. 이웃을 타입별 그룹으로 접기/펼치기. Person이면 traits 섹션, Book이면 메타·배경·주제·대표구절·주요인물/사건 전용 뷰. 외부 한국어 성경 API(`api.getbible.net`)로 구절 원문을 직접 fetch.
- 공유 모듈:
  - `frontend/src/api.js` — 단일 API 베이스 URL + `apiGet(path, {signal})` 헬퍼. `API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'`. 비-OK 응답은 status로 throw, `AbortError`는 그대로 전파.
  - `frontend/src/theme.js` — 노드 타입 → 색/한글 라벨의 단일 정규 팔레트(`TYPE_COLOR`, `TYPE_KO`, `TYPE_ORDER`, `typeColor()`, `typeKo()`, `SELECT_HL`). 검색·SidePanel·MapView·Timeline이 공유.
  - `frontend/src/convexHull.js` — Graham scan 볼록 껍질(MapView hull 전용).

### 2. 백엔드 (`backend/app/`)
- FastAPI 앱 진입점은 `backend/app/main.py`. `app = FastAPI(lifespan=lifespan)` 를 만들고 CORS(`allow_origins=["*"]`, `allow_methods=["GET"]`)를 붙인 뒤 4개 라우터를 include한다. `lifespan` 에서 시작 시 Neo4j에 라벨별 `theographic_id` 인덱스(`Person/Place/Event/PeopleGroup/Book`)를 `CREATE INDEX ... IF NOT EXISTS` 로 보장하며, 실패해도 인덱스 없이 계속 진행한다.
- DB 접근은 `backend/app/db.py` 의 `get_driver()` 단일 게이트. 모듈 전역 `_driver` 를 lazy-init하는 싱글턴이고, `NEO4J_URI`/`NEO4J_USER`/`NEO4J_PASSWORD` 환경변수를 읽는다(비밀번호 없으면 `RuntimeError`). 모든 라우트가 `driver.session()` 으로 Cypher를 직접 실행한다 — ORM·쿼리 빌더 레이어 없음.
- 라우트(`backend/app/routes/`, 각 모듈이 `router = APIRouter()` 노출):
  - `backend/app/routes/nodes.py` — `GET /node/{id}`(노드 + 이웃 `LIMIT 50` + 전체 이웃 수; Book이면 `topPersons`/`topEvents` 추가; Person이면 `traits` JSON 파싱), `GET /node/{id}/places`(라벨별 Cypher 분기로 좌표 있는 장소 반환), `GET /node/{id}/neighbors/grouped`(타입별 그룹, 타입당 `MAX_NEIGHBORS_PER_TYPE = 30`).
  - `backend/app/routes/events.py` — `GET /events`(startDate 있는 Event를 `sortKey` 순). `Cache-Control: no-store`.
  - `backend/app/routes/search.py` — `GET /search?q=`(nameKo/name CONTAINS, 정확·접두 매칭 우선 rank, `LIMIT 20`).
  - `backend/app/routes/books.py` — `GET /books`(타임라인 배치용 책 목록). 아래 별도 절 참조.

### 3. 데이터 레이어 (`data/` + Neo4j)
- 1차 그래프 데이터는 Neo4j에 적재된다. 원천은 외부 theographic-bible-metadata(GitHub raw JSON). 노드는 `theographic_id` 키로 식별.
- `data/` 의 JSON 오버레이는 두 경로로 쓰인다.
  - **적재 시점**: `backend/scripts/` 가 디스크 JSON을 읽어 Neo4j 노드에 속성을 SET한다(`inject_ko_names.py` → nameKo/aliasesKo, `inject_book_context.py` → background/themes/keyVerse, `inject_person_traits.py` → traits). `load_theographic.py`/`load_books.py` 가 그래프 자체를 적재한다. `generate_*.py` 스크립트는 Claude API로 `data/book_context/`·`data/character_traits/` JSON을 생성한다. 이 스크립트들은 런타임 API와 무관한 오프라인 도구다.
  - **런타임**: `GET /books` 만 디스크 JSON(`data/book_years_approx/books.json`)을 런타임에 직접 읽는다(아래).

## `/books` 라우트의 추정연도 캐싱 + 데이터 경로 폴백

`backend/app/routes/books.py` 는 `startYear` 가 없는 책의 추정연도 오버레이를 디스크 JSON에서 읽어 덮어쓴다.

- **1회 캐시**: `_load_approx()` 가 `@functools.lru_cache(maxsize=1)` 로 데코레이트되어 오버레이 JSON을 프로세스 수명 동안 단 한 번만 파싱·메모리 캐시한다. 매 `/books` 요청마다 디스크 I/O를 반복하지 않는다.
- **데이터 경로 폴백**: 후보 경로를 순서대로 시도한다(`_APPROX_CANDIDATES`).
  1. `os.environ.get("DATA_DIR", "/app/data")` + `book_years_approx/books.json` — docker 볼륨 마운트(`./data:/app/data`) 기준.
  2. 레포 상대경로(`_REPO_DATA_DIR`, `__file__` 기준 4단계 상위의 `data/`) + 같은 파일 — 비-docker 로컬 실행 폴백.
  - 두 후보 모두 `FileNotFoundError`/`JSONDecodeError` 면 빈 `dict`로 폴백(추정연도 없이 진행).
- **응답 로직**: `MATCH (b:Book) ... ORDER BY b.bookOrder` 로 책을 순회하면서 `startYear` 가 있으면 그대로 쓰고(`yearApprox=false`), 없으면 오버레이의 `placementYear`/`basis`를 채워 `yearApprox=true`로 표시한다. 정확·추정 연도 둘 다 없는 책은 시대순 배치 불가로 제외한다. 응답에 `Cache-Control: no-store` 헤더를 붙인다.

## 핵심 추상화 / 규약

- **`theographic_id`** — 모든 노드의 안정 식별자. 프론트의 `selectedNode`, 모든 `/node/{id}` 경로, Cypher 인덱스가 이 키로 동작한다.
- **노드 라벨(타입) 5종** — `Person`/`Place`/`Event`/`PeopleGroup`/`Book`. 백엔드 Cypher 분기와 프론트 `theme.js` 팔레트가 이 집합을 공유한다(매핑 안 된 라벨은 `Unknown`).
- **단일 API 클라이언트** — 프론트의 모든 백엔드 fetch는 `apiGet()` 한 경로를 거친다. 외부 성경 구절 API(`api.getbible.net`)만 예외로 `SidePanel.jsx` 가 직접 `fetch` 한다.
- **읽기 전용 GET** — CORS와 라우트 모두 GET만. 데이터 변경은 `backend/scripts/` 오프라인 적재로 분리.

## 진입점 요약

| 레이어 | 진입점 |
|---|---|
| 프론트 HTML | `frontend/index.html` |
| 프론트 부트스트랩 | `frontend/src/main.jsx` |
| 프론트 셸 | `frontend/src/App.jsx` |
| 백엔드 앱 | `backend/app/main.py` (`app`, uvicorn `app.main:app`) |
| 백엔드 DB 드라이버 | `backend/app/db.py` (`get_driver()`) |
| 백엔드 라우트 | `backend/app/routes/{nodes,events,search,books}.py` |
| 배포 | `deploy.sh`, `docker-compose.yml`, `nginx/nginx.conf`, `.github/workflows/deploy.yml` |
