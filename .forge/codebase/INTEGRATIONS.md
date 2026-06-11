---
last_mapped_commit: 60716ea24a78866177eb8fe28dee9c43ced5ff0f
mapped: 2026-06-11
---

# INTEGRATIONS

BibleMap이 의존하는 외부 시스템, 데이터베이스, 배포 통합, 외부 서비스, 데이터 소스를 정리한 구현 사실 문서.

## 데이터베이스: Neo4j

유일한 데이터 저장소.

### 연결 (`backend/app/db.py`)

- 공식 `neo4j` Python 드라이버. `GraphDatabase.driver(uri, auth=(user, password))`.
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
- 비밀번호는 커밋되지 않음(`.env.example`은 자리표시자만 보유, 실값은 루트 `.env`).

### 스키마/인덱스

- 노드 라벨: `Person`, `Place`, `Event`, `PeopleGroup`. 공통 식별자 `theographic_id`.
- 인덱스: 네 라벨의 `theographic_id`에 대해 `CREATE INDEX ... IF NOT EXISTS`. 앱 시작 시 `backend/app/main.py`의 `lifespan`이, 적재 시 `backend/scripts/load_theographic.py`의 `create_indexes()`가 생성.
- 관계 타입: `PARENT_OF`, `CHILD_OF`, `SIBLING_OF`, `PARTNER_OF`, `MEMBER_OF`, `HAS_PARTICIPANT`, `OCCURS_AT`, `PART_OF` (적재는 `backend/scripts/load_theographic.py`).

## 외부 데이터 소스: Theographic Bible Metadata (GitHub)

### 적재 스크립트 (`backend/scripts/load_theographic.py`)

- `urllib.request`로 `raw.githubusercontent.com`의 `robertrouse/theographic-bible-metadata` 저장소(`master` 브랜치) JSON 4개를 받아 Neo4j에 적재(`URLS` 딕셔너리):
  - people: `https://raw.githubusercontent.com/robertrouse/theographic-bible-metadata/master/json/people.json`
  - places: `https://raw.githubusercontent.com/robertrouse/theographic-bible-metadata/master/json/places.json`
  - events: `https://raw.githubusercontent.com/robertrouse/theographic-bible-metadata/master/json/events.json`
  - peopleGroups: `https://raw.githubusercontent.com/robertrouse/theographic-bible-metadata/master/json/peopleGroups.json`
- `status == "publish"`인 레코드만 필터(`filter_published`). `status` 필드가 없는 엔티티(Event, PeopleGroup)는 전체 포함.
- 노드(Person/Place/Event/PeopleGroup)와 관계를 `theographic_id` 기준 `MERGE`로 배치 적재.
- 일회성/수동 시딩 스크립트(스케줄 없음, 직접 실행).

### 한글 이름 데이터 (로컬)

- `data/names_ko/{people,places,events,groups}.json` — `theographic_id → {ko, alias}` 매핑.
- `backend/scripts/inject_ko_names.py`가 이를 읽어 노드에 `nameKo`/`aliasesKo` 속성을 주입(`SET p.nameKo = $ko, p.aliasesKo = $alias`). 외부 네트워크 호출 없이 Neo4j와만 통신. `deploy.sh` 4단계에서 매 배포마다 실행(Neo4j 준비까지 최대 15회 재시도).

## 프론트엔드 외부 서비스 (지도)

`frontend/src/MapView.jsx`에서 MapLibre GL을 인라인 스타일 객체(`version: 8`)로 구성. 두 외부 엔드포인트를 브라우저에서 직접 호출(프록시 없음).

### 타일 서비스

- 래스터 타일 소스: ArcGIS Online NatGeo World Map —
  `https://server.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}` (`tileSize: 256`).

### 글리프(폰트) 서비스

- 글리프 URL: Protomaps basemaps assets —
  `https://protomaps.github.io/basemaps-assets/fonts/{fontstack}/{range}.pbf`.
- 라벨 폰트 스택: `['Noto Sans Regular']` (`places-label` 심볼 레이어).

이 두 외부 호스트는 API 키 없이 직접 호출되며, 별도 토큰/인증이 없음.

## 인증 / 웹훅

- 애플리케이션 레벨 인증/인가 없음.
- 백엔드 CORS는 `allow_origins=["*"]`, `allow_credentials=False`, `allow_methods=["GET"]`, `allow_headers=["*"]` (`backend/app/main.py`) — 읽기 전용 공개 API.
- 앱에서 나가는 인증 토큰/시크릿 없음. Neo4j 자격증명(`NEO4J_PASSWORD`)만이 유일한 시크릿.
- 웹훅은 아래 GitHub Actions의 `push` 트리거가 유일.

## 백엔드 API 표면 (프론트엔드가 소비)

프론트엔드는 `VITE_API_URL`(프로덕션 `/api`, 개발 폴백 `http://localhost:8000`)을 베이스로 다음 엔드포인트를 호출. `api` 서비스는 호스트로 직접 노출되지 않으며 nginx만 경유(`location /api/ -> http://api:8000/`, `nginx/nginx.conf`).

- `GET /node/{id}` — 노드 상세 + 이웃 (`SidePanel.jsx`, `GraphView.jsx`).
- `GET /node/{id}/neighbors/grouped` — 타입별 그룹 이웃 (`GraphView.jsx`).
- `GET /node/{id}/places` — 노드와 연관된 지도 표시용 Place 목록 (`MapView.jsx`).
- `GET /events` — 타임라인용 사건 목록 (`TimelineView.jsx`).
- `GET /search?q=` — 한글/영문 이름 검색 (`App.jsx`).

## 배포 통합: GitHub Actions + self-hosted 러너

### 워크플로우 (`.github/workflows/deploy.yml`)

- 이름 "Deploy to Production". 트리거: `main` 브랜치 `push`.
- `runs-on: self-hosted` — 이 macOS/ARM64 머신(러너 `calmonionui-MacBookPro-biblemap`).
- 단일 스텝: `cd /Users/calmonion/Project/BibleMap` → `git fetch origin` → `git reset --hard origin/main` → `bash deploy.sh`.

### 배포 스크립트 (`deploy.sh`, 호스트에서 실행)

1. 락 파일 `/tmp/biblemap-deploy.lock`로 동시 실행 방지. 로그는 `~/Library/Logs/com.biblemap.deploy.log`.
2. **`DOCKER_CONFIG`를 `mktemp -d`의 임시 디렉터리로 오버라이드**(빈 `{"auths":{}}` config 작성)하여 macOS 키체인 우회. `$HOME/.docker/cli-plugins`를 그 임시 디렉터리에 심링크해 `docker compose`(V2 플러그인)가 해석되도록 함.
3. 루트 `.env`에서 `NEO4J_PASSWORD`(및 기타 변수)를 로드 — 호스트에서 직접 실행하는 inject 스크립트가 동일 비번을 쓰도록.
4. 프론트엔드 빌드(`npm install` + `npm run build` → `frontend/dist/`).
5. API 이미지 빌드: `docker compose -p biblemap build api`.
6. 컨테이너 재시작: `docker compose -p biblemap up -d api nginx`.
7. `backend/scripts/inject_ko_names.py`를 호스트에서 실행(Neo4j 준비 대기, 2초 간격 최대 15회 재시도). 끝내 실패하면 배포 중단(`exit 1`).

### 폴링 배포 (제거됨)

- 이전의 `scripts/auto-deploy-poll.sh` 폴링 메커니즘은 **제거됨**. 배포는 이제 GitHub Actions `push` 트리거 전용.
