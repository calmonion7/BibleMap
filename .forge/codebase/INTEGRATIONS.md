---
last_mapped_commit: 26240c7cf18f421b2f8baa4fd6584f40eede57b0
mapped: 2026-06-11
---

# INTEGRATIONS

BibleMap의 외부 연동 — 데이터베이스, 외부 API/데이터 소스, 지도 타일 서비스, 배포(CI/CD·호스팅). 인증 제공자, 결제, 웹훅 등 별도 연동은 코드베이스에서 발견되지 않았다.

## 데이터베이스 — Neo4j

- **Neo4j** 그래프 데이터베이스가 유일한 영속 저장소다.
- 백엔드 연결: `backend/app/db.py`의 `GraphDatabase.driver(uri, auth=(user, password))`. 환경변수 `NEO4J_URI`(기본 `bolt://localhost:7687`), `NEO4J_USER`(기본 `neo4j`), `NEO4J_PASSWORD`(기본 `biblemap123`)로 설정.
- 프로토콜: **Bolt**(`bolt://`). Docker 환경에서는 `bolt://neo4j:7687`(`docker-compose.yml`의 `api` 서비스 환경변수).
- 컨테이너: `docker-compose.yml`에서 이미지 `neo4j:5`, 포트 7474(HTTP/Neo4j Browser)·7687(Bolt)을 `127.0.0.1`에만 바인딩(외부 노출 안 함), 데이터는 named volume `neo4j_data`에 영속화. 인증은 `NEO4J_AUTH`(기본 `neo4j/biblemap123`).
- 인증 정보: 루트 `.env`의 `NEO4J_AUTH=neo4j/<password>` 형식(`.env.example`). `.env`는 gitignore됨.
- 인덱스: 앱 기동 시(`backend/app/main.py` lifespan) 및 적재 스크립트(`backend/scripts/load_theographic.py`)에서 `Person`, `Place`, `Event`, `PeopleGroup` 라벨의 `theographic_id`에 인덱스를 생성.

## 외부 데이터 소스 — Theographic (GitHub raw)

데이터 적재 스크립트 `backend/scripts/load_theographic.py`가 GitHub에서 원본 JSON을 직접 내려받는다(`urllib.request`).

- 소스 저장소: `robertrouse/theographic-bible-metadata` (GitHub, master 브랜치 raw 콘텐츠)
- 다운로드 URL 4종(`raw.githubusercontent.com`):
  - `.../json/people.json`
  - `.../json/places.json`
  - `.../json/events.json`
  - `.../json/peopleGroups.json`
- 인증 없는 공개 raw 콘텐츠 GET 요청. 적재 후 Neo4j에 노드·관계로 MERGE.
- 한글 이름 데이터는 외부가 아니라 로컬 `data/names_ko/`에서 주입(`backend/scripts/inject_ko_names.py`).

## 지도 타일 / 폰트 서비스 (프론트엔드)

`frontend/src/MapView.jsx`의 MapLibre GL 스타일이 외부 서비스에 직접 의존한다.

- **Esri / ArcGIS Online 래스터 타일** — 베이스맵. 타일 URL:
  `https://server.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}` (NatGeo World Map, `tileSize: 256`)
- **Protomaps basemaps-assets 글리프** — 라벨 폰트:
  `https://protomaps.github.io/basemaps-assets/fonts/{fontstack}/{range}.pbf`
- 두 서비스 모두 API 키·토큰 없이 사용한다. 코드베이스 전체에서 지도/외부 API 키 또는 토큰은 발견되지 않았다.

## 백엔드 ↔ 프론트엔드 연동

- 프론트엔드는 `import.meta.env.VITE_API_URL`(미설정 시 `http://localhost:8000`)을 베이스로 백엔드 REST API를 호출. 호출 엔드포인트: `/search`(`App.jsx`), `/events`(`TimelineView.jsx`), `/node/{id}`·`/node/{id}/places`·`/node/{id}/neighbors/grouped`(`SidePanel.jsx`, `MapView.jsx`, `GraphView.jsx`).
- 프로덕션에서는 `frontend/.env.production`의 `VITE_API_URL=/api`로 설정되어, Nginx가 `/api/`를 `http://api:8000/`로 리버스 프록시(`nginx/nginx.conf`).
- 백엔드 CORS: `backend/app/main.py`에서 모든 오리진/메서드/헤더 허용(`allow_origins=["*"]`).

## 배포 / 호스팅 (CI/CD)

- **GitHub Actions** — `.github/workflows/deploy.yml`. `main` 브랜치 push 시 `self-hosted` 러너에서 실행. 워크트리(`/Users/calmonion/Project/BibleMap/.claude/worktrees/wise-sprouting-hellman`)에서 `git fetch` → `git reset --hard origin/main` → `bash deploy.sh`.
- **자체 호스팅(self-hosted) 배포** — 클라우드 호스팅 PaaS가 아니라 로컬/온프레미스 머신(macOS, 로그 경로 `/Users/calmonion/Library/Logs/...`)에서 Docker Compose로 구동.
- `deploy.sh` — 프론트엔드 빌드(`npm install && npm run build`) → `docker compose -p biblemap build api` → `docker compose -p biblemap up -d api nginx` → `inject_ko_names.py`로 한글 이름 주입(Neo4j 준비될 때까지 최대 15회 재시도). `/tmp/biblemap-deploy.lock` 락 파일로 동시 배포 방지. macOS 키체인 우회를 위해 임시 `DOCKER_CONFIG` 사용.
- `scripts/auto-deploy-poll.sh` — GitHub Actions의 대안/보완 폴링 배포. 2분 주기로 `origin/worktree-wise-sprouting-hellman`을 `git fetch`해 새 커밋 감지 시 `git reset --hard` 후 `deploy.sh` 실행. 동일 락 파일 공유.
- 호스팅 표면: Nginx가 호스트 8080 포트로 정적 프론트엔드 + `/api` 프록시 서빙(`docker-compose.yml`, `nginx/nginx.conf`).

## 발견되지 않은 연동

- 인증/인가 제공자(OAuth, JWT 발급자 등) 없음 — API에 인증 계층 없음.
- 결제, 이메일, 메시징, 분석, 에러 트래킹, 객체 스토리지 등 외부 SaaS 연동 없음.
- 웹훅 수신/발신 엔드포인트 없음(GitHub Actions push 트리거는 표준 CI 이벤트).
