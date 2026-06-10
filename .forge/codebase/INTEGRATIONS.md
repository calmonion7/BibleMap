---
last_mapped_commit: 60962d0693f3bfaf4b8d24ce6f97d7b392770d85
mapped: 2026-06-11
---

# INTEGRATIONS

BibleMap이 의존하는 외부 시스템, 데이터베이스, 외부 서비스, 데이터 소스를 정리한 구현 사실 문서.

## 데이터베이스: Neo4j

유일한 데이터 저장소. 그래프 DB로 인물/장소/사건/그룹 노드와 관계를 보관.

### 연결 (`backend/app/db.py`)

- 공식 `neo4j` Python 드라이버 사용. `GraphDatabase.driver(uri, auth=(user, password))`.
- 모듈 전역 싱글턴(`_driver`), `get_driver()`로 lazy 초기화.
- 연결 파라미터:
  - URI: 환경 변수 `NEO4J_URI` (기본 `bolt://localhost:7687`).
  - 사용자: 환경 변수 `NEO4J_USER` (기본 `neo4j`).
  - 비밀번호: 환경 변수 `NEO4J_PASSWORD`. **기본값 없음** — 미설정 시 `RuntimeError`(fail-fast).

### 배포/컨테이너 (`docker-compose.yml`)

- 이미지 `neo4j:5`. 데이터 볼륨 `neo4j_data:/data`.
- 인증은 `NEO4J_AUTH=neo4j/${NEO4J_PASSWORD:?...}`로 **파생**됨 — `NEO4J_AUTH`를 독립 설정하지 않고 `NEO4J_PASSWORD`에서 조합. 변수 미설정 시 compose가 실패.
- API 컨테이너는 내부 네트워크 호스트명 `neo4j`로 접속(`NEO4J_URI=bolt://neo4j:7687`).
- 포트 `7474`(HTTP)/`7687`(Bolt)는 `127.0.0.1`에만 바인딩되어 호스트 로컬에서만 접근 가능.

### 스키마/인덱스

- 노드 라벨: `Person`, `Place`, `Event`, `PeopleGroup`. 공통 식별자 `theographic_id`.
- 인덱스: 네 라벨의 `theographic_id`에 대해 `CREATE INDEX ... IF NOT EXISTS`. 앱 시작 시 `backend/app/main.py`의 `lifespan`이, 적재 시 `backend/scripts/load_theographic.py`의 `create_indexes()`가 생성.
- 관계 타입: `PARENT_OF`, `CHILD_OF`, `SIBLING_OF`, `PARTNER_OF`, `MEMBER_OF`, `HAS_PARTICIPANT`, `OCCURS_AT`, `PART_OF` (적재는 `backend/scripts/load_theographic.py`, 한글 라벨 매핑은 `frontend/src/SidePanel.jsx`의 `REL_KO`).

## 외부 데이터 소스: Theographic Bible Metadata

성경 메타데이터 원본. GitHub raw로 직접 fetch.

### 적재 스크립트 (`backend/scripts/load_theographic.py`)

- `urllib.request`로 다음 4개 URL을 받아 Neo4j에 적재(`URLS` 딕셔너리):
  - people: `https://raw.githubusercontent.com/robertrouse/theographic-bible-metadata/master/json/people.json`
  - places: `https://raw.githubusercontent.com/robertrouse/theographic-bible-metadata/master/json/places.json`
  - events: `https://raw.githubusercontent.com/robertrouse/theographic-bible-metadata/master/json/events.json`
  - peopleGroups: `https://raw.githubusercontent.com/robertrouse/theographic-bible-metadata/master/json/peopleGroups.json`
- `status == "publish"`인 레코드만 필터(`filter_published`). `status` 필드가 없는 엔티티(Event, PeopleGroup)는 전체 포함.
- 노드(Person/Place/Event/PeopleGroup)와 관계를 `MERGE`로 적재. 위경도가 있는 Place만 지도에서 활용됨.

### 한글 이름 데이터 (로컬)

- `data/names_ko/{people,places,events,groups}.json` — `theographic_id → {ko, alias}` 매핑.
- `backend/scripts/inject_ko_names.py`가 이를 읽어 노드에 `nameKo`/`aliasesKo` 속성을 주입(`SET p.nameKo = $ko, p.aliasesKo = $alias`). `deploy.sh` 4단계에서 실행.

## 프론트엔드 외부 서비스 (지도)

`frontend/src/MapView.jsx`에서 MapLibre GL을 인라인 스타일 객체(`version: 8`)로 구성.

### 타일 서비스

- 래스터 타일 소스: ArcGIS Online NatGeo World Map —
  `https://server.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}` (`tileSize: 256`).

### 글리프(폰트) 서비스

- 글리프 URL: Protomaps basemaps assets —
  `https://protomaps.github.io/basemaps-assets/fonts/{fontstack}/{range}.pbf`.
- 라벨 폰트 스택: `['Noto Sans Regular']` (`places-label` 심볼 레이어).

이 두 외부 호스트는 API 키 없이 직접 호출되며, 별도 토큰/인증이 없음.

## 인증 제공자

없음. 애플리케이션 레벨 인증/인가 없음.

- 백엔드 CORS는 `allow_origins=["*"]`, `allow_credentials=False`, `allow_methods=["GET"]` (`backend/app/main.py`) — 읽기 전용 공개 API.
- Neo4j 자격증명만이 유일한 시크릿이며 환경 변수 `NEO4J_PASSWORD`로 주입(코드에 기본값 없음).

## 백엔드 API 표면 (프론트엔드가 소비)

프론트엔드는 `VITE_API_URL`(프로덕션 `/api`, 개발 `http://localhost:8000`)을 베이스로 다음 엔드포인트를 호출.

- `GET /node/{id}` — 노드 상세 + 이웃 (`SidePanel.jsx`, `GraphView.jsx`).
- `GET /node/{id}/neighbors/grouped` — 타입별 그룹 이웃 (`GraphView.jsx`).
- `GET /node/{id}/places` — 노드와 연관된 지도 표시용 Place 목록 (`MapView.jsx`).
- `GET /events` — 타임라인용 사건 목록 (`TimelineView.jsx`).
- `GET /search?q=` — 한글/영문 이름 검색 (`App.jsx`).

nginx가 `/api/` 요청을 `http://api:8000/`로 프록시(`nginx/nginx.conf`).
