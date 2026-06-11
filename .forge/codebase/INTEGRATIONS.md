---
last_mapped_commit: 288b14e23c889de294d34d0f794867d4e313a421
mapped: 2026-06-11
---

# INTEGRATIONS

BibleMap이 의존하는 외부/내부 통합 지점 — 데이터베이스, 외부 타일/폰트 서버, 리버스 프록시, 데이터 소스, CI/배포를 정리한다.

## 데이터베이스 — Neo4j (bolt)

그래프 데이터는 전부 Neo4j에 저장된다.
- 드라이버: `neo4j==6.2.0` (Python). 연결은 `backend/app/db.py`의 `get_driver()` 싱글톤이 담당.
- 프로토콜/URI: bolt. 컨테이너 내부에서는 `bolt://neo4j:7687`(`docker-compose.yml`의 `api` 서비스 env), 로컬 폴백 기본값은 `bolt://localhost:7687`.
- 인증: `NEO4J_USER`(기본 `neo4j`) + `NEO4J_PASSWORD`.
- **Fail-fast**: `NEO4J_PASSWORD`가 없으면 `get_driver()`가 `RuntimeError("NEO4J_PASSWORD 환경변수가 설정되지 않았습니다")`를 던진다. `docker-compose.yml`의 `${NEO4J_PASSWORD:?...}` 구문도 미설정 시 compose 자체를 실패시킨다(neo4j·api 양쪽). 데이터 적재 스크립트(`load_theographic.py`, `inject_ko_names.py`)도 동일하게 비밀번호 미설정 시 즉시 예외를 던진다.
- 포트 노출: compose에서 Neo4j 포트(7474/7687)는 `127.0.0.1`에만 바인딩되어 호스트 외부에 노출되지 않는다.
- 인덱스: `backend/app/main.py`의 `lifespan`이 앱 기동 시 `Person`/`Place`/`Event`/`PeopleGroup`의 `theographic_id` 인덱스를 `IF NOT EXISTS`로 생성(실패해도 무시하고 진행). 적재 스크립트도 동일 인덱스를 생성한다.

## 인증 / 인가

애플리케이션 레벨 사용자 인증은 **없다**. FastAPI CORS는 `allow_origins=["*"]`, `allow_methods=["GET"]`, `allow_credentials=False`(`backend/app/main.py`) — 읽기 전용 공개 GET API. 유일한 시크릿은 Neo4j 비밀번호(`NEO4J_PASSWORD`)이며, 호스트 `.env`/컨테이너 환경변수로 주입된다.

## 외부 지도 타일 / 폰트 서버 (폴백 없음)

`frontend/src/MapView.jsx`의 MapLibre GL 스타일이 외부 서비스 2곳에 직접 의존하며 **로컬 폴백이 없다** — 두 서비스가 다운/변경되면 지도가 깨진다:
- **ArcGIS NatGeo 래스터 타일** — `https://server.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}` (`tileSize: 256`, source `esri`, layer `esri-layer`). Esri/ArcGIS Online의 외부 호스팅 타일.
- **protomaps 글리프 폰트** — `glyphs: 'https://protomaps.github.io/basemaps-assets/fonts/{fontstack}/{range}.pbf'`. GitHub Pages(`protomaps.github.io`)에서 PBF 폰트 글리프를 받아 라벨 렌더링에 사용.

이 두 URL은 코드에 하드코딩되어 있고 환경변수로 주입되지 않는다.

## 백엔드 API (프론트엔드 → 백엔드)

프론트엔드는 `VITE_API_URL`(빌드 타임)을 기준 URL로 백엔드 REST API를 호출한다(개발 `http://localhost:8000`, 프로덕션 `/api`; 상세는 `STACK.md`). 사용되는 엔드포인트:
- `GET /node/{id}`, `GET /node/{id}/places`, `GET /node/{id}/neighbors/grouped` (`nodes.py`).
- `GET /events` (`events.py`, `Cache-Control: no-store`).
- `GET /search?q=` (`search.py`).
프론트엔드는 표준 `fetch`로 호출하며(예: `MapView.jsx`가 `AbortController` signal과 함께 `/node/{id}/places` 호출), 외부 SDK/클라이언트 라이브러리는 사용하지 않는다.

## 외부 데이터 소스 (적재 시점)

`backend/scripts/load_theographic.py`가 **Theographic Bible Metadata**를 GitHub raw에서 받아 Neo4j에 적재한다(런타임 아님, 데이터 준비 시점):
- `https://raw.githubusercontent.com/robertrouse/theographic-bible-metadata/master/json/people.json`
- `.../places.json`, `.../events.json`, `.../peopleGroups.json`
- `status == "publish"`인 레코드만 적재(`status` 필드가 없는 Event/PeopleGroup은 전체 포함).

한글 이름은 `backend/scripts/inject_ko_names.py`가 로컬 `data/names_ko/`(`people.json`, `places.json`, `events.json`, `groups.json`)에서 읽어 노드의 `nameKo`/`aliasesKo`로 주입한다. 이 디렉터리는 compose에서 `api` 컨테이너의 `/app/data`로 바인드 마운트되지만, inject 스크립트는 `deploy.sh`가 **호스트의 `python3`로 직접** 실행한다.

## 리버스 프록시 — nginx

`nginx/nginx.conf` (`nginx:alpine` 컨테이너, 호스트 `8080` → 컨테이너 `80`):
- `location /api/` → `proxy_pass http://api:8000/;` — `/api/` 접두사를 떼고 `api` 컨테이너로 전달(`X-Real-IP`/`X-Forwarded-For`/`X-Forwarded-Proto` 헤더 설정). 프로덕션 프론트엔드의 `VITE_API_URL=/api`가 이 경로로 들어온다.
- SPA 서빙: `location /`는 `try_files $uri /index.html`로 클라이언트 라우팅 폴백. `/index.html`은 `no-cache`, 정적 자산(js/css/이미지/woff)은 `max-age=31536000, immutable` 캐시.
- 정적 루트는 `/usr/share/nginx/html` — compose가 호스트의 `./frontend/dist`를 읽기 전용 바인드 마운트한 것.

## CI / 배포 — GitHub Actions (self-hosted)

`.github/workflows/deploy.yml`:
- 트리거: `main` 브랜치 push.
- 러너: `self-hosted` — 동일 개발 Mac에서 도는 self-hosted runner(배포 대상과 같은 머신).
- 단계: `cd /Users/calmonion/Project/BibleMap` → `git fetch origin` → `git reset --hard origin/main` → `bash deploy.sh`.
- 즉 push 한 번이 곧 배포다: 워크트리를 origin/main에 강제 동기화(`--hard`)한 뒤 `deploy.sh`로 프론트 빌드 + api 이미지 빌드 + 컨테이너 재시작 + 한글 이름 주입까지 수행한다(단계 상세는 `STACK.md`).
- 결과 서빙: nginx가 `8080` 포트에서 `./frontend/dist`(읽기 전용 마운트)를 서빙하고 `/api/`를 `api:8000`으로 프록시한다.
