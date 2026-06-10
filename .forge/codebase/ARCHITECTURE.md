---
last_mapped_commit: 60962d0693f3bfaf4b8d24ce6f97d7b392770d85
mapped: 2026-06-11
---

# ARCHITECTURE

## 전체 패턴

세 개의 컨테이너로 구성된 단일 페이지 앱(SPA) + 그래프 DB 백엔드 구조다.

- **프론트엔드**: React 19 + Vite로 빌드된 정적 SPA. 빌드 산출물(`frontend/dist/`)을 nginx가 정적 서빙한다.
- **리버스 프록시**: `nginx:alpine`. 정적 자산 서빙과 `/api/` 경로의 백엔드 프록시를 겸한다.
- **백엔드**: FastAPI(`uvicorn` 실행) — `python:3.12-slim` 컨테이너. 읽기 전용 JSON API.
- **데이터베이스**: Neo4j 5 그래프 DB. Bolt 프로토콜(`bolt://neo4j:7687`)로 접속.

오케스트레이션은 `docker-compose.yml`(프로젝트명 `biblemap`)이 담당하며 `neo4j`, `api`, `nginx` 세 서비스를 정의한다.

## 레이어

```
[브라우저]
   │  (정적 HTML/JS/CSS, fetch /api/...)
   ▼
[nginx]  nginx/nginx.conf  (:80 → 호스트 :8080)
   │  location /api/  → proxy_pass http://api:8000/
   │  location /      → try_files $uri /index.html  (SPA fallback)
   ▼
[FastAPI / uvicorn]  backend/app/main.py  (:8000)
   │  라우터: nodes, events, search
   │  Neo4j 드라이버 싱글톤
   ▼
[Neo4j 5]  bolt://neo4j:7687
```

## 데이터 흐름

1. 브라우저가 SPA를 로드한다. 프론트엔드의 API 베이스 URL은 환경변수 `VITE_API_URL`로 주입된다. 프로덕션 빌드는 `frontend/.env.production`에서 `VITE_API_URL=/api`(상대 경로)를 쓰고, 로컬 개발 기본값은 각 컴포넌트에서 `'http://localhost:8000'`이다.
2. 프론트엔드가 `fetch(`${API_BASE}/...`)`로 API를 호출한다 → 프로덕션에서는 `/api/...`로 나간다.
3. nginx가 `location /api/`를 잡아 `http://api:8000/`으로 프록시한다(경로 끝 슬래시로 `/api` prefix가 제거되어 백엔드에는 `/node/...`, `/events`, `/search` 형태로 도달).
4. FastAPI 라우트 핸들러가 `get_driver()`로 Neo4j 드라이버 싱글톤을 얻고, `driver.session()` 블록 안에서 Cypher 쿼리를 실행한다.
5. 쿼리 결과(노드 속성 dict)를 JSON 직렬화해 반환한다.

데이터는 **읽기 전용**이다. API에 쓰기 경로가 없고, 데이터 적재는 별도의 오프라인 스크립트(`backend/scripts/`)로만 이뤄진다.

## 핵심 추상화

### Neo4j 드라이버 싱글톤 — `backend/app/db.py`

`get_driver()` 함수가 모듈 전역 `_driver`를 지연 초기화(lazy)하는 싱글톤. 최초 호출 시 `NEO4J_URI`(기본 `bolt://localhost:7687`), `NEO4J_USER`(기본 `neo4j`), `NEO4J_PASSWORD`(환경변수, 미설정 시 `RuntimeError`)로 `GraphDatabase.driver`를 생성한다. 이후 호출은 같은 인스턴스를 재사용한다. 모든 라우트가 이 함수를 통해 DB에 접근한다.

### FastAPI lifespan 인덱스 생성 — `backend/app/main.py`

`@asynccontextmanager`로 정의된 `lifespan`이 앱 기동 시 한 번 실행된다. `Person`, `Place`, `Event`, `PeopleGroup` 라벨 각각에 대해 `theographic_id` 속성 인덱스를 `CREATE INDEX ... IF NOT EXISTS`로 만든다. 인덱스 생성이 실패하면 `logging.exception`으로 로깅만 하고 인덱스 없이 계속 진행한다(앱 기동을 막지 않는다).

### CORS 설정 — `backend/app/main.py`

`CORSMiddleware`를 다음 설정으로 등록한다:

- `allow_origins=["*"]`
- `allow_credentials=False`
- `allow_methods=["GET"]`
- `allow_headers=["*"]`

GET 전용·자격증명 비허용이라 읽기 전용 공개 API 성격과 일치한다.

### `theographic_id` — 노드 식별 키

모든 노드는 외부 데이터셋(theographic-bible-metadata)의 레코드 id를 `theographic_id` 속성으로 갖는다. API의 `node_id` 경로 파라미터, 검색·이웃 조회, 인덱스가 모두 이 키를 기준으로 동작한다. 프론트엔드가 노드를 선택·연결할 때 쓰는 식별자도 이 값이다(`{ id }`로 직렬화됨).

## 진입점

- **백엔드**: `backend/app/main.py` — `app = FastAPI(lifespan=lifespan)`. `uvicorn app.main:app`(Dockerfile CMD)으로 실행.
- **프론트엔드**: `frontend/src/main.jsx` → `App.jsx` 렌더. `index.html`이 `main.jsx`를 모듈로 로드.

## API 라우트 — `backend/app/routes/`

라우터는 prefix 없이 등록되며(`APIRouter()`), `main.py`에서 `include_router`로 합쳐진다. 실제 존재하는 라우트는 다음과 같다.

### `backend/app/routes/nodes.py`

- `GET /node/{node_id}/places` — 노드 라벨(Person/Event/PeopleGroup/그 외 Place)에 따라 분기 Cypher로 위·경도가 있는 연관 `Place`를 모은다. `isPrimary` 플래그(Event/Place는 true, Person/PeopleGroup은 false)와 `lat`/`lng`(float 파싱 실패 시 해당 항목 스킵), `nameKo`(없으면 `name` 폴백)를 담은 배열 반환. 중복 `theographic_id`는 제거.
- `GET /node/{node_id}/neighbors/grouped` — 노드의 직접 이웃을 라벨별(`Person`/`Event`/`PeopleGroup`/`Place`)로 묶어 반환. 타입별 최대 `MAX_NEIGHBORS_PER_TYPE = 30`개. `nameKoMissing` 플래그 포함.
- `GET /node/{node_id}` — 노드 단건 + 라벨 + 이웃 목록(`LIMIT NODE_NEIGHBOR_LIMIT = 50`) + 기타 속성(`name`/`nameKo`/`theographic_id`/`aliasesKo` 제외). 없으면 404.

상수: `MAX_NEIGHBORS_PER_TYPE = 30`, `NODE_NEIGHBOR_LIMIT = 50`.

### `backend/app/routes/events.py`

- `GET /events` — `startDate`가 있는 모든 `Event`를 `sortKey` 오름차순으로 반환(`id`/`title`/`nameKo`/`startDate`/`sortKey`). `Cache-Control: no-store` 헤더를 단 `JSONResponse`로 응답.

### `backend/app/routes/search.py`

- `GET /search?q=` — `nameKo` 또는 `name`에 `q`가 포함되고 `theographic_id`가 있는 노드를 `LIMIT SEARCH_LIMIT = 20`개 반환. `q`가 공백이면 빈 배열. 항목은 `id`/`label`/`name`/`nameKo`.

상수: `SEARCH_LIMIT = 20`.

### 제거된 라우트

`GET /places`(전역 장소 목록)는 데드 엔드포인트로 **제거되었다**(커밋 `34bee1d`). 현재 코드에 존재하지 않으며, 장소 조회는 `GET /node/{node_id}/places`로만 가능하다.

## 프론트엔드 뷰 구성 — `frontend/src/`

`App.jsx`가 상단 내비게이션(지도/타임라인/그래프 탭 + 검색)과 선택 노드 상태(`selectedNode`)를 관리하는 셸이다. 세 뷰가 같은 `selectedNode`를 공유한다.

- **MapView** (`MapView.jsx`) — MapLibre GL 지도. 선택 노드의 `/node/{id}/places`를 받아 마커로 표시, `fitBounds`로 줌. 기저 타일은 ArcGIS NatGeo 래스터.
- **TimelineView** (`TimelineView.jsx`) — `/events`를 받아 `startDate`별로 묶고 `sortKey`로 정렬한 연표.
- **GraphView** (`GraphView.jsx`) — Cytoscape(cose-bilkent 레이아웃 + expand-collapse). `/node/{id}`와 `/node/{id}/neighbors/grouped`를 받아 중심 노드 + 타입별 그룹 노드 그래프를 그린다. 기본 중심 노드는 모세(`recjNRR60PAuFtjha`).
- **SidePanel** (`SidePanel.jsx`) — `/node/{id}`를 받아 노드 상세 + 이웃 리스트를 우측 패널에 표시(지도·타임라인 뷰에서만).

## 데이터 적재 (오프라인) — `backend/scripts/`

- `load_theographic.py` — GitHub의 theographic-bible-metadata JSON을 받아 Neo4j에 노드(`Person`/`Place`/`Event`/`PeopleGroup`)와 관계(`PARENT_OF`/`CHILD_OF`/`SIBLING_OF`/`PARTNER_OF`/`MEMBER_OF`/`HAS_PARTICIPANT`/`OCCURS_AT`/`PART_OF`)를 배치 `MERGE`로 적재. 인덱스도 생성.
- `inject_ko_names.py` — `data/names_ko/`의 한글 이름 매핑을 기존 노드에 `nameKo`/`aliasesKo` 속성으로 주입(`SET`). `deploy.sh`가 배포 마지막 단계에서 Neo4j 준비를 기다리며 최대 15회 재시도로 실행한다.

## 배포

- `deploy.sh` — 프론트 빌드 → `api` 이미지 빌드 → `api`·`nginx` 컨테이너 재기동 → 한글 이름 주입. lock 파일(`/tmp/biblemap-deploy.lock`)로 동시 실행 방지. `.env`에서 `NEO4J_PASSWORD` 로드.
- `.github/workflows/deploy.yml` — `main` 푸시 시 self-hosted 러너에서 워크트리를 `origin/main`으로 reset 후 `deploy.sh` 실행.
- `scripts/auto-deploy-poll.sh` — 2분 폴링으로 새 커밋 감지 시 자동 배포(워크트리 브랜치 기준). `deploy.sh`와 같은 lock 공유.
