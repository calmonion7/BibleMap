---
last_mapped_commit: 8af8f0563294387a7073d0b85e6f7de74b4b7b30
mapped: 2026-07-13
---

# INTEGRATIONS

BibleMap이 의존하는 외부 데이터·서비스·인프라와 그 연결점을 정리한다.

## 외부 데이터 소스 (빌드타임/오프라인 수집)

### theographic-bible-metadata (GitHub raw JSON)

성경 인물·장소·사건 그래프의 1차 원본. 여러 적재/생성 스크립트가 `urllib.request`로 GitHub raw를 직접 fetch한다. 확인된 URL(모두 `https://raw.githubusercontent.com/robertrouse/theographic-bible-metadata/master/json/`):

- `people.json`, `places.json`, `events.json`, `peopleGroups.json` — `backend/scripts/load_theographic.py`가 배치 적재(published 필터, `theographic_id` 인덱스 생성). `status` 필드가 `publish`인 레코드만 취하고, 필드 없는 Event·PeopleGroup은 전량 포함.
- `books.json` — `backend/scripts/generate_book_context.py`.
- `events.json`, `verses.json` — `backend/scripts/generate_event_verses.py`(사건→구절 매핑, `fields.book[0]`로 책 귀속).

theographic 원본은 Ussher 연대계라 저작 레이어(보수 연대계)와 충돌하는 연대가 있으며, `backend/scripts/inject_date_corrections.py`가 `data/date_corrections/`의 교정 테이블을 DB에 SET한다(재적재 시 반드시 재실행 — `README.md`·ADR-0014).

### getbible v2 API (성경 본문)

한국어·영어 성경 본문 수집원. `backend/scripts/generate_bible_text.py`가 전체 번역본 단일 파일 `https://api.getbible.net/v2/{slug}.json`을 번역본당 1회(총 2회) fetch하고, `TRANSLATIONS = (("textKo","korean"), ("textEn","kjv"))`로 매핑. `backend/scripts/generate_verse_text.py`는 장 단위 `https://api.getbible.net/v2/{slug}/{book_order}/{chapter}.json`를 사용. getbible는 기본 urllib UA에 403을 반환하므로 브라우저류 `User-Agent` 헤더를 붙인다. 결과 본문은 `data/bible/verses.json`에 저장.

### Anthropic Claude API (저작 콘텐츠 생성)

`generate_*` 스크립트 중 5개가 Claude로 문맥/특성/연결 텍스트를 생성한다: `backend/scripts/generate_book_events.py`, `generate_book_context.py`, `generate_person_context.py`, `generate_person_traits.py`, `generate_verse_events.py`.

- SDK: `import anthropic` → `anthropic.Anthropic(api_key=...)`. `requirements.txt`에는 없는 스크립트 전용 의존성.
- 모델: 확인된 값은 모두 `claude-haiku-4-5-20251001`.
- 인증: `ANTHROPIC_API_KEY` 환경변수(미설정 시 `RuntimeError`).
- 실행 예: `ANTHROPIC_API_KEY=sk-... NEO4J_PASSWORD=... python3 generate_book_context.py`.

이 스크립트들은 오프라인 저작 단계에서만 실행되며, 산출물은 `data/` 하위 JSON으로 커밋되어 런타임 API가 오버레이로 읽는다(런타임에 Claude를 호출하지 않음).

### 저작 데이터 레이어 (`data/`)

런타임 API(`backend/app/overlays.py`)가 읽는 저장소 내 JSON 오버레이. 탐색 우선순위는 `DATA_DIR`(기본 `/app/data`, compose가 `./data`를 마운트) → 저장소 `data/`. 하위 디렉터리: `authored_events/`, `authored_persons/`, `bible/`, `book_context/`, `book_events/`, `book_years_approx/`, `character_traits/`, `date_corrections/`, `event_dedupe/`, `event_verses/`, `keypeople/`, `keypeople_verses/`, `names_ko/`, `person_context/`, `person_events/`, `person_relations/`, `place_context/`, `place_coords/`, `tours/`, `verse_events/`.

## Neo4j 데이터베이스

- 이미지 `neo4j:5`(`docker-compose.yml`). 포트 7474(HTTP)·7687(Bolt)를 `127.0.0.1`에만 바인딩. 볼륨 `neo4j_data:/data`.
- 인증: `NEO4J_AUTH=neo4j/${NEO4J_PASSWORD}` — compose가 `.env`의 `NEO4J_PASSWORD`에서 파생. 비번 미설정이면 compose가 실패(`:?NEO4J_PASSWORD must be set`).
- API 접속: `api` 서비스는 `NEO4J_URI=bolt://neo4j:7687`, `NEO4J_USER=neo4j`, `NEO4J_PASSWORD`를 환경변수로 받아 `backend/app/db.py`가 Bolt 드라이버 싱글턴 생성. 호스트에서 직접 실행하는 스크립트는 기본 `bolt://localhost:7687`.
- 인덱스: `backend/app/main.py` lifespan과 `load_theographic.py`가 `Person·Place·Event·PeopleGroup·Book`의 `theographic_id`에 인덱스를 생성.
- 스키마 노드 레이블: `Person`, `Place`, `Event`, `PeopleGroup`, `Book`. 간선 예: `PARENT_OF`/`CHILD_OF`(가계).

## 가계도(genealogy) 연동 — 최근 추가 기능

혈통 단절을 저작으로 보충하는 경로(ADR-0019):

- 데이터: `data/authored_persons/genealogy.json` — 마태복음 1장 아브라함→예수 단일 사슬. `chain`은 조상→후손 순서이고 연속 쌍이 `PARENT_OF`/`CHILD_OF` 간선이 된다. `authored=true` 노드만 신규 생성(나머지는 기존 theographic id).
- 적재: `backend/scripts/load_authored_genealogy.py` — 저작 노드 MERGE 후 연속 쌍에 양방향 간선을 멱등 적재하고, 사슬 끝에서 `CHILD_OF*`로 사슬 머리 도달 가능성을 자체 검증. `load_theographic.py` 재실행 후 반드시 재실행 필요.
- API: `backend/app/routes/family.py`의 `GET /person/{id}/family` — 인물 중심 서브그래프(조상선 + 자손 2세대 + 형제·배우자)를 `{focus, nodes, parentEdges, siblings, partners}`로 반환. `data/person_relations/relations.json`의 '가족' role 라벨을 `lru_cache`로 병합. 존재하지 않는 id는 404 대신 빈 서브그래프 폴백.
- 프론트: `frontend/src/FamilyTree.jsx` — 라이브러리 없이 손수 SVG 커넥터 + 절대배치 세대 레이아웃으로 가계도를 그리고, 노드 클릭 시 재중심화.

## 프론트엔드 런타임 외부 서비스 (지도 타일·폰트)

`frontend/src/MapView.jsx`가 maplibre-gl 스타일을 인라인 구성하며 두 외부 호스트를 브라우저에서 직접 로드한다:

- 래스터 타일: `https://server.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}` (ArcGIS Online NatGeo World Map).
- 글리프(폰트): `https://protomaps.github.io/basemaps-assets/fonts/{fontstack}/{range}.pbf`.

## nginx 리버스 프록시

`nginx/nginx.conf`(nginx:alpine, `docker-compose.yml`에서 호스트 `8080:80`):

- `location /api/` → `proxy_pass http://api:8000/` — API 프록시(`/api` 프리픽스 제거하여 전달). `X-Forwarded-*` 헤더 세팅.
- `location = /index.html` → `no-cache`.
- 정적 자산(`js|css|png|jpg|...|woff2?`) → `max-age=31536000, immutable`.
- `location /` → `try_files $uri /index.html` (SPA 폴백). 루트는 `/usr/share/nginx/html`이며 compose가 `./frontend/dist`를 읽기전용 마운트.

## docker-compose 서비스 (`docker-compose.yml`)

- `neo4j` — `neo4j:5`, 포트 7474/7687(localhost), 볼륨 `neo4j_data`, `restart: unless-stopped`.
- `api` — `build: ./backend`, Neo4j 환경변수, `./data:/app/data` 마운트, `depends_on: neo4j`. (호스트로 포트 노출 없음 — nginx 프록시로만 접근.)
- `nginx` — `nginx:alpine`, `8080:80`, `./frontend/dist`·`./nginx/nginx.conf` 읽기전용 마운트, `depends_on: api`.

## 배포 (self-hosted GitHub Actions)

- `.github/workflows/deploy.yml` — `on: push branches: [main]`, `runs-on: self-hosted`. 스텝: `cd /Users/calmonion/Project/BibleMap` → `git fetch origin` → `git reset --hard origin/main` → `bash deploy.sh`.
- `deploy.sh` — macOS 로컬 호스트 배포 스크립트:
  1. lock 파일(`/tmp/biblemap-deploy.lock`)·로그(`~/Library/Logs/com.biblemap.deploy.log`)·macOS 키체인 우회용 임시 `DOCKER_CONFIG` 준비, `.env`에서 `NEO4J_PASSWORD` 로드.
  2. `[1/3]` `cd frontend && npm install && npm run build` → `frontend/dist/`.
  3. `[2/3]` `docker compose -p biblemap build api`.
  4. `[3/4]` `docker compose -p biblemap up -d api nginx`.
  5. `[4/4]` `backend/scripts/inject_ko_names.py`를 최대 15회 재시도(Neo4j 준비 대기). 실패 시 배포 중단(exit 1).

Compose 프로젝트명은 `-p biblemap`으로 고정된다.
