---
last_mapped_commit: e53ec23d634a48d16bd1abf3e131c340cfbaac1f
mapped: 2026-07-14
---

# INTEGRATIONS

BibleMap이 의존하는 외부 데이터·서비스·인프라와 그 연결점을 정리한다. 런타임 API(`backend/app/`)는 외부 HTTP를 일절 호출하지 않는다 — 모든 외부 수집은 빌드타임/오프라인 스크립트가 수행하고 산출물을 `data/`에 커밋한다.

## 외부 데이터 소스 (빌드타임/오프라인 수집)

### theographic-bible-metadata (GitHub raw JSON)

성경 인물·장소·사건 그래프의 1차 원본. 적재/생성 스크립트가 `urllib.request`로 GitHub raw를 직접 fetch한다. 베이스 URL은 `https://raw.githubusercontent.com/robertrouse/theographic-bible-metadata/master/json/`:

- `people.json`, `places.json`, `events.json`, `peopleGroups.json` — `backend/scripts/load_theographic.py`가 배치 적재.
- `books.json` — `backend/scripts/load_books.py`, `generate_book_context.py`, `generate_verse_events.py`.
- `events.json`·`verses.json` — `backend/scripts/generate_event_verses.py`(사건→구절 매핑), `generate_verse_events.py`.
- `people.json` — `backend/scripts/generate_person_context.py`, `generate_person_traits.py`.

theographic 원본은 Ussher 연대계라 저작 레이어(보수 연대계)와 충돌하는 연대가 있으며, `backend/scripts/inject_date_corrections.py`가 `data/date_corrections/`의 교정 테이블을 DB에 SET한다(`load_theographic.py` 재적재 시 반드시 재실행 — `README.md`·ADR-0014).

### getbible v2 API (성경 본문)

한국어·영어 성경 본문 수집원(빌드타임 전용, ADR-0003 미리굽기). `backend/scripts/generate_bible_text.py`가 전체 번역본 단일 파일 `https://api.getbible.net/v2/{slug}.json`을 번역본당 1회 fetch(korean + kjv). `backend/scripts/generate_verse_text.py`·`generate_person_event_verses.py`는 장 단위 `https://api.getbible.net/v2/{slug}/{book_order}/{chapter}.json` 사용. 결과 정본은 `data/bible/verses.json`(키 BBCCCVVV) — 런타임 API는 이 파일에서 본문을 합성한다(ADR-0015).

### Anthropic Claude API (저작 콘텐츠 생성)

`generate_*` 스크립트 중 5개가 Claude로 문맥/특성/사건 텍스트를 생성한다: `backend/scripts/generate_book_events.py`, `generate_book_context.py`, `generate_person_context.py`, `generate_person_traits.py`, `generate_verse_events.py`.

- SDK: `import anthropic` → `anthropic.Anthropic(api_key=...)`. `backend/requirements.txt`에는 없는 스크립트 전용 의존성.
- 모델: 확인된 값은 모두 `claude-haiku-4-5-20251001`.
- 인증: `ANTHROPIC_API_KEY` 환경변수(미설정 시 `RuntimeError`). 키 값은 저장소에 없음.

오프라인 저작 단계에서만 실행되며, 산출물은 `data/` 하위 JSON으로 커밋되어 런타임 API가 오버레이로 읽는다(런타임에 Claude를 호출하지 않음).

### 저작 데이터 레이어 (`data/`)

런타임 API(`backend/app/overlays.py`)가 읽는 저장소 내 JSON 오버레이. 탐색 우선순위는 `DATA_DIR`(기본 `/app/data`, compose가 `./data`를 마운트) → 저장소 `data/`. 로더는 `lru_cache(maxsize=1)`이므로 데이터 변경 반영은 `docker compose restart api`.

- 하위 디렉터리: `authored_events/`, `authored_persons/`, `bible/`, `book_context/`, `book_events/`, `book_years_approx/`, `character_traits/`, `date_corrections/`, `event_dedupe/`, `event_verses/`, `keypeople/`, `keypeople_verses/`, `names_ko/`, `person_context/`, `person_events/`, `person_relations/`, `place_context/`, `place_coords/`, `tours/`, `verse_events/`.
- 루트 파일: `data/word_distribution.json`(책별·전체 상위 명사+극성 정본, `backend/scripts/build_word_distribution.py` 산출)·`data/word_sentiment.json`(단어→positive|negative|neutral 큐레이션) — `backend/app/routes/words.py`의 `/words/*` 엔드포인트가 소비.

## Neo4j 데이터베이스

- 이미지 `neo4j:5`(`docker-compose.yml`). 포트 7474(HTTP)·7687(Bolt)를 `127.0.0.1`에만 바인딩. 볼륨 `neo4j_data:/data` — 호스트에서 직접 Bolt 쓰기 가능.
- 인증: `NEO4J_AUTH=neo4j/${NEO4J_PASSWORD}` — compose가 `.env`의 `NEO4J_PASSWORD`에서 파생. 미설정이면 compose가 실패(`:?NEO4J_PASSWORD must be set`).
- API 접속: `api` 서비스는 `NEO4J_URI=bolt://neo4j:7687`, `NEO4J_USER=neo4j`, `NEO4J_PASSWORD`를 환경변수로 받아 `backend/app/db.py`가 Bolt 드라이버 싱글턴 생성. 호스트에서 직접 실행하는 스크립트는 기본 `bolt://localhost:7687`(`deploy.sh`가 `.env`를 로드해 동일 비번 공유).
- 인덱스: `backend/app/main.py` lifespan이 `Person·Place·Event·PeopleGroup·Book`의 `theographic_id` 인덱스를 생성.
- 노드 레이블: `Person`, `Place`, `Event`, `PeopleGroup`, `Book`. 가계 간선: `PARENT_OF`/`CHILD_OF`(`backend/scripts/load_authored_genealogy.py`가 양방향 멱등 적재, `backend/app/routes/family.py`가 서브그래프 조회).

## 프론트엔드 런타임 외부 서비스 (지도 타일·폰트)

`frontend/src/MapView.jsx`가 maplibre-gl 스타일을 인라인 구성하며 두 외부 호스트를 브라우저에서 직접 로드한다(키·인증 없음):

- 래스터 타일: `https://server.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}` (ArcGIS Online NatGeo World Map).
- 글리프(폰트): `https://protomaps.github.io/basemaps-assets/fonts/{fontstack}/{range}.pbf`.

## 인증·보안 표면

- 사용자 인증 없음 — 공개 읽기 전용 API. `backend/app/main.py`의 CORS는 `allow_origins=["*"]`, `allow_methods=["GET"]`, `allow_credentials=False`.
- 시크릿은 `.env`의 `NEO4J_PASSWORD`와 저작 스크립트 실행 시의 `ANTHROPIC_API_KEY` 환경변수뿐(둘 다 값은 저장소 밖). 웹훅 수신 엔드포인트 없음.

## nginx 리버스 프록시

`nginx/nginx.conf`(nginx:alpine, `docker-compose.yml`에서 호스트 `8080:80`):

- `location /api/` → `proxy_pass http://api:8000/` — API 프록시(`/api` 프리픽스 제거하여 전달), `X-Forwarded-*` 헤더 세팅.
- `location = /index.html` → `no-cache, no-store, must-revalidate`.
- 정적 자산(`js|css|png|...|woff2?`) → `max-age=31536000, immutable`.
- `location /` → `try_files $uri /index.html` (SPA 폴백). 루트 `/usr/share/nginx/html`은 compose가 `./frontend/dist`를 읽기전용 마운트 — 프론트 검증 전 `npm run build` 필요(HMR 아님).

## docker-compose 서비스 (`docker-compose.yml`)

- `neo4j` — `neo4j:5`, 포트 7474/7687(localhost 한정), 볼륨 `neo4j_data`, `restart: unless-stopped`.
- `api` — `build: ./backend`, Neo4j 환경변수 3종, `./data:/app/data` 마운트, `depends_on: neo4j`. 호스트로 포트 미노출(nginx 프록시로만 접근).
- `nginx` — `nginx:alpine`, `8080:80`, `./frontend/dist`·`./nginx/nginx.conf` 읽기전용 마운트, `depends_on: api`.

## 배포 인프라 (self-hosted GitHub Actions)

- `.github/workflows/deploy.yml` — `on: push branches: [main]`, `runs-on: self-hosted`. 단일 스텝: `cd /Users/calmonion/Project/BibleMap` → `git fetch origin` → `git reset --hard origin/main` → `bash deploy.sh`.
- 러너: 이 macOS 머신의 전용 디렉터리 `~/actions-runner-biblemap`(runner 2.334.0), launchd 서비스 `~/Library/LaunchAgents/actions.runner.calmonion7-BibleMap.calmonionui-MacBookPro-biblemap.plist`. 같은 머신에 PortfoliOn·lab-taebro 러너가 별도 디렉터리로 공존한다(레포별 격리).
- `deploy.sh` — macOS 로컬 호스트 배포 스크립트:
  1. lock 파일(`/tmp/biblemap-deploy.lock`)·로그(`~/Library/Logs/com.biblemap.deploy.log`)·macOS 키체인 우회용 임시 `DOCKER_CONFIG`(cli-plugins 심링크 포함) 준비, `.env`에서 `NEO4J_PASSWORD` 로드.
  2. `[1/3]` `cd frontend && npm install && npm run build` → `frontend/dist/`.
  3. `[2/3]` `docker compose -p biblemap build api`.
  4. `[3/4]` `docker compose -p biblemap up -d api nginx`.
  5. `[4/4]` `backend/scripts/inject_ko_names.py`를 최대 15회 재시도(Neo4j 준비 대기). 실패 시 배포 중단(exit 1). 그 외 `load_*`·`inject_*` 스크립트는 실행하지 않는다.
- Compose 프로젝트명은 `-p biblemap`으로 고정.
- 공개 도메인: `https://biblemap.taebro.com` — 이 머신의 스택을 Cloudflare Tunnel(cloudflared, PortfoliOn과 공유 터널의 ingress 규칙)로 노출한다(`BIBLEMAP_PLAN.md` 배포 절). 터널 설정 파일은 이 저장소 밖(머신 레벨). 따라서 `localhost:8080` == 프로덕션(동일 컨테이너·동일 Neo4j).
