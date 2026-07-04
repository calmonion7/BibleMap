---
last_mapped_commit: 815433397ff74c133b2de5d1cafe1c8764b5303c
mapped: 2026-07-04
---

# External Integrations

**Analysis Date:** 2026-07-04

## APIs & External Services

**지도 타일/폰트 (프론트엔드 런타임, 클라이언트에서 직접 호출):**
- ESRI ArcGIS World Map 래스터 타일 — `https://server.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}` (`frontend/src/MapView.jsx:33`). 인증 없음, maplibre `raster` source `esri`로 등록
- Protomaps basemaps 글리프(폰트) — `https://protomaps.github.io/basemaps-assets/fonts/{fontstack}/{range}.pbf` (`frontend/src/MapView.jsx:28`). 인증 없음

**빌드타임 데이터 소스 (스크립트, 런타임 불필요):**
- Theographic Bible Metadata (GitHub raw JSON) — `https://raw.githubusercontent.com/robertrouse/theographic-bible-metadata/master/json/{people,places,events,peopleGroups,books,verses}.json`. `backend/scripts/load_theographic.py`, `generate_*.py`에서 `urllib`로 fetch. 인증 없음. Neo4j 그래프의 원본 데이터
- getbible.net v2 — `https://api.getbible.net/v2/{slug}/{book_order}/{chapter}.json` (`backend/scripts/generate_person_event_verses.py:172`, `generate_verse_text.py`). 절 본문을 한국어(`korean`)+영어(`kjv`) 슬러그로 fetch. ADR-0003에 따라 빌드타임에 미리 구워(prebake) 데이터에 인라인 저장 → 런타임 호출 제거

**LLM (빌드타임 데이터 생성, 런타임 불필요):**
- Anthropic Claude API — `anthropic` Python SDK, 모델 `claude-haiku-4-5-20251001` (`backend/scripts/generate_book_context.py:57`, `generate_person_traits.py:59`, `generate_book_events.py`, `generate_verse_events.py`)
  - 인증: `ANTHROPIC_API_KEY` 환경변수 (미설정 시 스크립트가 `RuntimeError`)
  - 산출물은 `data/*` JSON으로 커밋되며 앱은 이 생성 데이터만 소비 (ADR-0006: 데이터 생성은 LLM 직접, 스크립트 아님)

## Data Storage

**Databases:**
- Neo4j 5 (그래프 DB) — `docker-compose.yml` 서비스 `neo4j`, 이미지 `neo4j:5`
  - 접속 포트: `127.0.0.1:7474`(HTTP 브라우저), `127.0.0.1:7687`(Bolt) — 로컬호스트로만 바인딩
  - Driver: Python `neo4j` 6.2.0 (`GraphDatabase.driver`), 런타임 접근은 `backend/app/db.py`의 모듈 전역 싱글턴 `_driver`
  - 연결 설정: `NEO4J_URI`(compose 내 `bolt://neo4j:7687`), `NEO4J_USER`(`neo4j`), `NEO4J_PASSWORD`(env, 필수)
  - 인증 파생: compose가 `NEO4J_AUTH=neo4j/${NEO4J_PASSWORD}`로 자동 조립 (`docker-compose.yml:10`)
  - 세션 사용 패턴: 라우트마다 `with driver.session() as session: session.run(<cypher>, ...)` (`backend/app/routes/nodes.py` 등)
  - 인덱스: 앱 시작 `lifespan`에서 Person/Place/Event/PeopleGroup/Book의 `theographic_id`에 `CREATE INDEX ... IF NOT EXISTS` (`backend/app/main.py:14`)
  - APOC 미사용 — 자체 로더 사용 (ADR-0001)
  - 볼륨: named volume `neo4j_data:/data` (영속)

**오버레이 JSON (런타임, Neo4j 미저장):**
- 추정/큐레이션 데이터는 Neo4j가 아닌 파일 오버레이로 서빙 (ADR-0004). `backend/app/overlays.py`가 `DATA_DIR`(기본 `/app/data`) 또는 레포 `data/`에서 로드, `functools.lru_cache`로 1회 캐시
- `data/` 하위: `book_events/`, `event_verses/`, `book_context/`, `character_traits/`, `place_context/`, `place_coords/`, `person_events/`, `verse_events/`, `book_years_approx/`, `authored_events/`, `authored_persons/`, `names_ko/`
- compose에서 `./data:/app/data` 마운트 (`docker-compose.yml:20`)

**한글 이름 주입:**
- `backend/scripts/inject_ko_names.py`가 `data/names_ko/{people,places,...}.json`을 읽어 Neo4j 노드에 `nameKo`·`aliasesKo` 속성 SET. 배포 마지막 단계에서 실행 (`deploy.sh` [4/4])

**File Storage:**
- 로컬 파일시스템만 사용 (외부 오브젝트 스토리지 없음)

**Caching:**
- 애플리케이션 레벨: `functools.lru_cache`(오버레이 JSON, `overlays.py`)
- HTTP: nginx가 정적 자산(js/css/이미지/폰트)에 `Cache-Control: public, max-age=31536000, immutable`, `index.html`에는 `no-cache` (`nginx/nginx.conf:25`, `:20`)

## Authentication & Identity

**사용자 인증:**
- 없음. 공개 읽기 전용 앱. CORS는 모든 origin에 GET만 허용, credentials 비허용 (`backend/app/main.py:25`)

**서비스 자격증명:**
- Neo4j: `NEO4J_PASSWORD` (env)
- Anthropic: `ANTHROPIC_API_KEY` (env, 빌드타임 스크립트만)

## Monitoring & Observability

**Error Tracking:**
- 외부 서비스 없음. 표준 `logging` 사용 (`backend/app/main.py`의 인덱스 생성 실패 시 `logging.exception`)

**Logs:**
- 백엔드: uvicorn/Python stdout
- 배포: `deploy.sh`가 `/Users/calmonion/Library/Logs/com.biblemap.deploy.log`에 tee (`deploy.sh:5`)

## CI/CD & Deployment

**Hosting:**
- self-hosted (사용자 머신 `/Users/calmonion/Project/BibleMap`). Docker Compose 스택 (neo4j + api + nginx)

**CI Pipeline:**
- GitHub Actions — `.github/workflows/deploy.yml`. `main` push 시 `runs-on: self-hosted` 러너가 `git fetch` → `git reset --hard origin/main` → `bash deploy.sh`
- `deploy.sh`는 `/tmp/biblemap-deploy.lock`로 동시 실행 방지, macOS 키체인 우회용 임시 `DOCKER_CONFIG` 생성

**Reverse Proxy:**
- nginx (`nginx:alpine`) — 호스트 `8080:80` 노출 (`docker-compose.yml:28`)
  - `/api/` → `http://api:8000/` 프록시 (`nginx/nginx.conf:12`), `X-Real-IP`/`X-Forwarded-*` 헤더 전달
  - `/` → SPA fallback (`try_files $uri /index.html`)
  - 정적 자산은 `frontend/dist`(read-only 마운트) 서빙

## Environment Configuration

**Required env vars:**
- `NEO4J_PASSWORD` — 런타임 필수 (neo4j·api 서비스, 로더/주입 스크립트)
- `ANTHROPIC_API_KEY` — 데이터 생성 스크립트 실행 시에만 필요

**Optional env vars:**
- `NEO4J_URI`, `NEO4J_USER` — 기본값 존재
- `DATA_DIR` — 오버레이 경로, 기본 `/app/data`
- `VITE_API_URL` — 프론트 빌드타임, 기본 `frontend/.env.production`의 `/api`

**Secrets location:**
- 루트 `.env` 파일 (git 미추적). `.env.example`에 `NEO4J_PASSWORD` 키 이름만 명시(값 없음). `deploy.sh`가 `set -a; . .env; set +a`로 로드

## Webhooks & Callbacks

**Incoming:**
- GitHub push 이벤트가 Actions 워크플로 트리거 (webhook은 GitHub 관리형). 앱 자체 수신 webhook 엔드포인트 없음

**Outgoing:**
- 없음 (런타임). 빌드타임 스크립트만 외부 API로 아웃바운드 호출

---

*Integration audit: 2026-07-04*
