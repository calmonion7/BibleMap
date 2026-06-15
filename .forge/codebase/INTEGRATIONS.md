---
last_mapped_commit: bfc1dd258b0308435ca24c48a82c9c86a9e622f1
mapped: 2026-06-16
---

# INTEGRATIONS

외부 API, 데이터베이스, 데이터 소스, 지도 타일 제공자, 인증, 그리고 프론트↔백엔드 HTTP 연결과 Docker/compose 서비스를 정리한다. 구현 사실만 다루며 도메인 의미는 다루지 않는다(CONTEXT.md 영역).

## 데이터베이스 — Neo4j

- 그래프 DB Neo4j, compose 서비스 이미지 `neo4j:5` (`docker-compose.yml`)
- 백엔드 드라이버 `neo4j==6.2.0` (`backend/requirements.txt`)
- 연결: `backend/app/db.py` — `GraphDatabase.driver(uri, auth=(user, password))`, 싱글톤(`get_driver()`)
  - `NEO4J_URI`(기본 `bolt://localhost:7687`), `NEO4J_USER`(기본 `neo4j`), `NEO4J_PASSWORD`(필수 — 없으면 RuntimeError)
- compose에서 api 서비스로 주입되는 값: `NEO4J_URI=bolt://neo4j:7687`, `NEO4J_USER=neo4j`, `NEO4J_PASSWORD=${NEO4J_PASSWORD}` (`docker-compose.yml`)
- neo4j 포트는 `127.0.0.1:7474`(HTTP), `127.0.0.1:7687`(Bolt)로 로컬 바인딩만 — 외부 노출 없음
- 데이터 볼륨: `neo4j_data:/data`
- 앱 기동 시 `backend/app/main.py` lifespan이 `Person/Place/Event/PeopleGroup/Book` 라벨에 `theographic_id` 인덱스 생성(실패해도 계속 진행)
- 쿼리는 모두 Cypher (`backend/app/routes/*.py`)

### 인증
- 별도 사용자 인증/OAuth/세션 없음. 인증 요소는 Neo4j 접속 비밀번호(`NEO4J_PASSWORD`)뿐이며 사용자 단의 로그인 개념 없음.
- compose가 `NEO4J_AUTH=neo4j/${NEO4J_PASSWORD}`로 neo4j 초기 자격 설정.

## 프론트엔드 ↔ 백엔드 HTTP 연결

### 통합된 API 베이스 URL (최근 통합)
- 공유 클라이언트: `frontend/src/api.js`
  - `export const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'`
  - `apiGet(path, { signal })` — fetch GET → JSON, 비-OK는 status로 throw, AbortError 전파
- 프로덕션은 `VITE_API_URL=/api`를 빌드타임 주입(`frontend/.env.production`) → nginx 프록시 경유
- 모든 프론트 fetch가 이 단일 헬퍼/베이스를 사용(개별 파일에 베이스 URL 흩어져 있지 않음):
  - `frontend/src/App.jsx` — `/search?q=...`
  - `frontend/src/MapView.jsx` — `/node/{id}/places`, `/node/{id}/neighbors/grouped`
  - `frontend/src/SidePanel.jsx` — `/node/{id}`
  - `frontend/src/TimelineView.jsx` — `/events`, `/books`

### 백엔드 CORS (`backend/app/main.py`)
- `allow_origins=["*"]`, `allow_credentials=False`, `allow_methods=["GET"]`, `allow_headers=["*"]` — GET 전용 공개 읽기 API.

### nginx 리버스 프록시 (`nginx/nginx.conf`)
- `location /api/` → `proxy_pass http://api:8000/;` (말미 `/`로 `/api` 접두 제거 후 백엔드 전달)
- `X-Real-IP`, `X-Forwarded-For`, `X-Forwarded-Proto`, `Host` 헤더 전달
- SPA fallback: `location /` → `try_files $uri /index.html`
- 캐시 정책: 정적 에셋(js/css/이미지/폰트) `max-age=31536000, immutable`, `index.html`은 `no-cache`
- 정적 루트: `frontend/dist`를 `/usr/share/nginx/html`로 read-only 마운트

## 외부 API / 서드파티 서비스

### 지도 타일 제공자 (`frontend/src/MapView.jsx`)
maplibre-gl 스타일(version 8)에서 직접 외부 타일/폰트를 받는다:
- 래스터 타일: Esri ArcGIS Online — `https://server.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}` (source `esri`, tileSize 256, layer `esri-layer`)
- glyphs(폰트): Protomaps basemaps assets — `https://protomaps.github.io/basemaps-assets/fonts/{fontstack}/{range}.pbf`
- 둘 다 API 키 없이 직접 호출(공개 엔드포인트). 초기 지도 중심 `[35.22, 31.78]`, zoom 5.

### 한국어 성경 구절 API (`frontend/src/SidePanel.jsx`)
- getbible v2 — `https://api.getbible.net/v2/korean/${bookOrder}/${chapter}.json`
- 장(chapter) JSON을 받아 `verses[]`에서 절을 찾는 방식(절 단위 엔드포인트 없음). 실패 시 null.
- 인물 trait의 `verse_ref` 원문 표시에 사용. API 키 없음, 클라이언트에서 직접 호출.

### Theographic Bible Metadata (적재용 데이터 소스, 런타임 아님)
GitHub raw에서 원본 JSON을 받아 Neo4j에 적재/생성:
- `backend/scripts/load_theographic.py` — people/places/events/peopleGroups (`https://raw.githubusercontent.com/robertrouse/theographic-bible-metadata/master/json/*.json`)
- `backend/scripts/load_books.py` — books.json (동일 레포)
- `backend/scripts/generate_book_context.py`, `generate_person_traits.py` — 동일 레포 books/people/events.json 입력

### Anthropic API (콘텐츠 생성 스크립트, 런타임 아님)
- `backend/scripts/generate_book_context.py`, `backend/scripts/generate_person_traits.py`
- `import anthropic`, `anthropic.Anthropic(api_key=...)`, 모델 `claude-haiku-4-5-20251001`, max_tokens 512
- 키: 환경변수 `ANTHROPIC_API_KEY`(없으면 RuntimeError). 생성 결과는 `data/book_context/`, `data/character_traits/`에 저장되어 inject 스크립트로 Neo4j 주입.

## Docker / Compose 서비스 (`docker-compose.yml`)

3개 서비스, 프로젝트명 `biblemap`(`deploy.sh`에서 `-p biblemap`):
- `neo4j` — 이미지 `neo4j:5`, 포트 `127.0.0.1:7474/7687`, 볼륨 `neo4j_data:/data`, `restart: unless-stopped`
- `api` — `build: ./backend`(python:3.12-slim, uvicorn), `data/`를 `/app/data`로 마운트, `depends_on: neo4j`
- `nginx` — 이미지 `nginx:alpine`, 포트 `8080:80`(외부 공개), `frontend/dist`와 `nginx/nginx.conf` read-only 마운트, `depends_on: api`

## 배포 파이프라인

### CI (`.github/workflows/deploy.yml`)
- `main` push 트리거, `runs-on: self-hosted`
- `/Users/calmonion/Project/BibleMap`에서 `git fetch` → `git reset --hard origin/main` → `bash deploy.sh`

### 배포 스크립트 (`deploy.sh`)
- lock 파일(`/tmp/biblemap-deploy.lock`)로 중복 실행 방지, 로그 `~/Library/Logs/com.biblemap.deploy.log`
- macOS 키체인 우회용 임시 `DOCKER_CONFIG` 구성(compose 플러그인 심볼릭 링크)
- `.env`에서 `NEO4J_PASSWORD` 로드
- 단계: 프론트 빌드(`npm install && npm run build`) → `docker compose -p biblemap build api` → `up -d api nginx` → `inject_ko_names.py`로 한글 이름 주입(Neo4j 준비까지 최대 15회 재시도, 실패 시 배포 중단)

## 환경변수 / 시크릿 (값 미기재)
- 루트 `.env` / `.env.example`: `NEO4J_PASSWORD` (`.env`는 `.gitignore`됨)
- `frontend/.env.production`: `VITE_API_URL=/api`
- 백엔드 런타임: `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`(필수), `DATA_DIR`(books 라우트 폴백, 기본 `/app/data`)
- 스크립트 전용: `ANTHROPIC_API_KEY`(generate 스크립트), `NEO4J_*`(inject/load 스크립트)
- 시크릿 값은 본 문서에 포함하지 않는다.
