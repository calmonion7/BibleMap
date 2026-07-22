---
last_mapped_commit: f5e17ae2993e228f8b7481dba03478ddec8616f4
mapped: 2026-07-22
---

# INTEGRATIONS

BibleMap이 의존하는 외부 데이터·서비스·인프라와 그 연결점을 정리한다. 런타임 API(`backend/app/`)는 외부 HTTP를 일절 호출하지 않는다 — 모든 외부 수집은 빌드타임/오프라인 스크립트(`backend/scripts/`)가 수행하고 산출물을 `data/`에 커밋한다.

## 외부 데이터 소스 (빌드타임/오프라인 수집)

### theographic-bible-metadata (GitHub raw JSON)

성경 인물·장소·사건 그래프의 1차 원본. 적재/생성/색인 스크립트가 `urllib.request`로 GitHub raw를 직접 fetch한다. 베이스 URL은 `https://raw.githubusercontent.com/robertrouse/theographic-bible-metadata/master/json/`:

- `people.json`, `places.json`, `events.json`, `peopleGroups.json` — `backend/scripts/load_theographic.py`가 배치 적재.
- `books.json` — `backend/scripts/load_books.py`, `generate_book_context.py`, `generate_verse_events.py`.
- `events.json`·`verses.json` — `backend/scripts/generate_event_verses.py`(사건→구절 매핑), `generate_verse_events.py`.
- `people.json` — `backend/scripts/generate_person_context.py`, `generate_person_traits.py`.
- `verses.json` — `backend/scripts/build_verse_persons.py`: 각 절 레코드의 `verseID`(우리 정본 사전과 동일 키 규약 BBCCCVVV)와 `people`(등장/언급 인물 rec id 배열) 필드를 그대로 투영해 `data/verse_persons/index.json`을 산출(저작 아닌 원본 로드+투영). theographic는 "하나님(God)"도 people로 포함.

theographic 원본은 Ussher 연대계라 저작 레이어(보수 연대계)와 충돌하는 연대가 있으며, `backend/scripts/inject_date_corrections.py`가 `data/date_corrections/`의 교정 테이블을 DB에 SET한다(`load_theographic.py` 재적재 시 반드시 재실행 — `README.md`).

### getbible v2 API (성경 본문)

한국어·영어 성경 본문 수집원(빌드타임 전용 — "미리굽기"). `backend/scripts/generate_bible_text.py`가 전체 번역본 단일 파일 `https://api.getbible.net/v2/{slug}.json`을 번역본당 1회 fetch(korean + kjv)해 정본 절 사전 `data/bible/verses.json`(키 BBCCCVVV)을 만든다. 장 단위 엔드포인트 `https://api.getbible.net/v2/{slug}/{book_order}/{chapter}.json`은 두 스크립트가 소비: `backend/scripts/generate_verse_text.py`(`book_context`·`character_traits`·`place_context`·`person_relations`·`person_context`의 인용 절 본문 인라인 채움), `backend/scripts/generate_person_event_verses.py`(`data/person_events/*.json` 사건 context에서 파싱한 구절 참조의 본문 채움). getbible는 기본 `Python-urllib` UA에 403을 주므로 세 스크립트 모두 브라우저류 UA 헤더(`Mozilla/5.0 (compatible; BibleMap-build/1.0)`)로 요청한다.

런타임 API는 `data/bible/verses.json`에서 본문을 합성해 서빙한다(`backend/app/overlays.py`의 `bible_verses()`) — `backend/app/routes/books.py`의 `/book/{id}/chapter/{n}`(장 본문), `/book/{id}/quotations`(인용 절 대조)이 이 사전을 직접 소비. `backend/scripts/build_word_verse_index.py`도 같은 `data/bible/verses.json`을 입력으로 소비하지만 네트워크 fetch는 하지 않는다(로컬 파일 → kiwipiepy 형태소 분석 → 역색인).

### Anthropic Claude API (저작 콘텐츠 생성)

`generate_*` 스크립트 중 5개가 Claude로 문맥/특성/사건 텍스트를 생성한다: `backend/scripts/generate_book_events.py`, `generate_book_context.py`, `generate_person_context.py`, `generate_person_traits.py`, `generate_verse_events.py`.

- SDK: `import anthropic` → `anthropic.Anthropic(api_key=...)`. `backend/requirements.txt`에는 없는 스크립트 전용 의존성.
- 모델: 확인된 값은 모두 `claude-haiku-4-5-20251001`.
- 인증: `ANTHROPIC_API_KEY` 환경변수(미설정 시 `RuntimeError`). 키 값은 저장소에 없음.

오프라인 저작 단계에서만 실행되며, 산출물은 `data/` 하위 JSON으로 커밋되어 런타임 API가 오버레이로 읽는다(런타임에 Claude를 호출하지 않음). `backend/scripts/generate_book_context_enrich.py`는 실행 스크립트가 아니라 재생성 시 필드 목록·절차를 안내하는 docstring 레시피(ADR-0006 — 실제 생성은 Anthropic API 또는 Claude Code로 수행 후 수동 병합). `data/god_reliance/*.json`·`data/person_context/people.json` 등 일부 데이터는 수작업 저작이며 각 디렉터리의 `AUTHORING.md`가 저작 규칙을 문서화하고 `validate_god_reliance.py`·`validate_person_context.py`로 검증한다. `data/chapter_summaries/`·`data/chapter_sections/`(장 개요·장 묶음 저작)·`data/quotations/`(구약↔신약 인용 302쌍)는 `validate_chapter_summaries.py`·`validate_chapter_sections.py`·`validate_quotations.py`로 검증(모두 Neo4j 미접근, 파일 스키마·참조 무결성 검사).

### 저작 데이터 레이어 (`data/`)

런타임 API(`backend/app/overlays.py`)가 읽는 저장소 내 JSON 오버레이. 탐색 우선순위는 `DATA_DIR`(기본 `/app/data`, compose가 `./data`를 마운트) → 저장소 `data/`. 로더는 `lru_cache(maxsize=1)`이므로 데이터 변경 반영은 `docker compose restart api`.

- 하위 디렉터리: `authored_events/`, `authored_persons/`(가계 저작 — `mothers.json`은 어머니-자식 간선 원본, `load_authored_mothers.py`가 적재), `bible/`(정본 절 사전), `book_context/`, `book_events/`, `book_years_approx/`, `chapter_sections/`(장 묶음 정본, `overlays.chapter_sections()`), `chapter_summaries/`(장별 한줄 요약+대표절, `overlays.chapter_summaries()`), `character_traits/`, `date_corrections/`, `event_dedupe/`, `event_verses/`, `god_reliance/`(인물별 하나님 의존 분류 JSON + `AUTHORING.md`), `keypeople/`, `keypeople_verses/`, `names_ko/`, `person_context/`(저작 `people.json` + `AUTHORING.md`), `person_events/`, `person_relations/`, `person_slugs/`(`seal_slugs.json` — 비큐레이션 인장 보유 인물 목록, `backend/app/routes/family.py`가 소비), `place_context/`, `place_coords/`, `quotations/`(구약↔신약 직접 인용 302쌍 정본, `overlays.quotations()`), `tours/`(`{slug}.json`의 `stops`는 `[{id, note}]` 객체 배열 — ADR-0028, `note`는 그 투어 관점의 정차지 해설·nullable, `backend/app/routes/tours.py`는 객체 형식만 파싱), `verse_events/`, `verse_persons/`(`build_verse_persons.py` 산출, `backend/app/routes/verses.py`가 소비), `word_verse_index/`(`build_word_verse_index.py` 산출 — 런타임 로더·소비 라우트 없음, 인프라 전용 산출물).
- 루트 파일: `data/word_distribution.json`(책별·전체 상위 명사+극성 정본, `backend/scripts/build_word_distribution.py` 산출)·`data/word_sentiment.json`(단어→positive|negative|neutral 큐레이션) — `backend/app/routes/words.py`의 `/words/*` 엔드포인트가 소비.

## Neo4j 데이터베이스

- 이미지 `neo4j:5`(`docker-compose.yml`). 포트 7474(HTTP)·7687(Bolt)를 `127.0.0.1`에만 바인딩. 볼륨 `neo4j_data:/data` — 호스트에서 직접 Bolt 쓰기 가능.
- 인증: `NEO4J_AUTH=neo4j/${NEO4J_PASSWORD}` — compose가 `.env`의 `NEO4J_PASSWORD`에서 파생. 미설정이면 compose가 실패(`:?NEO4J_PASSWORD must be set`).
- API 접속: `api` 서비스는 `NEO4J_URI=bolt://neo4j:7687`, `NEO4J_USER=neo4j`, `NEO4J_PASSWORD`를 환경변수로 받아 `backend/app/db.py`가 Bolt 드라이버 싱글턴 생성. 호스트에서 직접 실행하는 스크립트는 기본 `bolt://localhost:7687`(`deploy.sh`가 `.env`를 로드해 동일 비번 공유).
- 인덱스: `backend/app/main.py`의 `lifespan`이 `Person`·`Place`·`Event`·`PeopleGroup`·`Book`의 `theographic_id` 인덱스를 생성.
- 노드 레이블: `Person`, `Place`, `Event`, `PeopleGroup`, `Book`. 가계 간선: `PARENT_OF`/`CHILD_OF` — `backend/scripts/load_authored_genealogy.py`·`load_authored_mothers.py`가 양방향(`MERGE` 양쪽 SET) 멱등 적재하고 `backend/app/routes/family.py`가 서브그래프 조회. 무방향 이웃 조회 시 같은 쌍이 2행으로 겹칠 수 있어 `backend/app/routes/nodes.py`의 `get_node()`가 `startNode(r) = n` 비교로 방향 정규화 후 디듀프.
- 하이브리드 조회 사례: `backend/app/routes/verses.py`의 `/verse/{verse_id}/persons`는 `overlays.verse_persons()`(JSON 색인)로 rec id를 얻은 뒤 Neo4j `MATCH (p:Person) WHERE p.theographic_id IN $ids`로 이름만 해석 — 오버레이·그래프 DB를 한 엔드포인트에서 함께 사용.

## 프론트엔드 런타임 외부 서비스 (지도 타일·폰트)

`frontend/src/MapView.jsx`가 maplibre-gl 스타일을 인라인 구성하며 두 외부 호스트를 브라우저에서 직접 로드한다(키·인증 없음):

- 래스터 타일: `https://server.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}` (ArcGIS Online NatGeo World Map).
- 글리프(폰트): `https://protomaps.github.io/basemaps-assets/fonts/{fontstack}/{range}.pbf`.

지도 이외 UI 폰트(IM Fell English)는 `frontend/public/fonts/`에 자체 호스팅(외부 CDN 미사용) — STACK.md 참고.

## 인증·보안 표면

- 사용자 인증 없음 — 공개 읽기 전용 API. `backend/app/main.py`의 CORS는 `allow_origins=["*"]`, `allow_methods=["GET"]`, `allow_credentials=False`.
- 시크릿은 `.env`의 `NEO4J_PASSWORD`와 저작 스크립트 실행 시의 `ANTHROPIC_API_KEY` 환경변수뿐(둘 다 값은 저장소 밖). 웹훅 수신 엔드포인트 없음.

## nginx 리버스 프록시

`nginx/nginx.conf`(nginx:alpine, `docker-compose.yml`에서 호스트 `8080:80`):

- `location /api/` → `proxy_pass http://api:8000/` — API 프록시(`/api` 프리픽스 제거하여 전달), `X-Forwarded-*` 헤더 세팅.
- `location = /index.html` → `no-cache, no-store, must-revalidate`.
- 정적 자산(`js|css|png|...|woff2?`) → `max-age=31536000, immutable`.
- `location /` → `try_files $uri /index.html` (SPA 폴백). 루트 `/usr/share/nginx/html`은 compose가 `./frontend/dist`를 읽기전용 마운트 — 프론트 검증 전 `npm run build` 필요(HMR 아님).

프론트가 API GET 응답에 `?v=<빌드ID>` 캐시버스터(`frontend/src/api.js` + `vite.config.js`의 `__BUILD_ID__`)를 부착하는 것은 이 nginx 계층과 무관한 별도 방어선 — API 응답 자체의 `Cache-Control`(예: `books.py`·`reliance.py`의 `public, max-age=3600`, `books.py`의 목차 엔드포인트는 `no-store`)을 배포 시점에 무력화해, 데이터가 바뀐 배포 직후에도 브라우저가 옛 응답을 재사용하지 않게 한다.

## docker-compose 서비스 (`docker-compose.yml`)

- `neo4j` — `neo4j:5`, 포트 7474/7687(localhost 한정), 볼륨 `neo4j_data`, `restart: unless-stopped`.
- `api` — `build: ./backend`, Neo4j 환경변수 3종, `./data:/app/data` 마운트, `depends_on: neo4j`. 호스트로 포트 미노출(nginx 프록시로만 접근).
- `nginx` — `nginx:alpine`, `8080:80`, `./frontend/dist`·`./nginx/nginx.conf` 읽기전용 마운트, `depends_on: api`.

## 배포 인프라 (self-hosted GitHub Actions)

- `.github/workflows/deploy.yml` — `on: push branches: [main]`, `runs-on: self-hosted`. 단일 스텝: `cd /Users/calmonion/Project/BibleMap` → `git fetch origin` → `git reset --hard origin/main` → `bash deploy.sh`.
- 러너: 이 macOS 머신의 전용 디렉터리 `~/actions-runner-biblemap`(확인됨), launchd 서비스 `~/Library/LaunchAgents/actions.runner.calmonion7-BibleMap.calmonionui-MacBookPro-biblemap.plist`(확인됨). 같은 머신에 다른 프로젝트 러너가 별도 디렉터리로 공존(레포별 격리).
- `deploy.sh` — macOS 로컬 호스트 배포 스크립트:
  1. lock 파일(`/tmp/biblemap-deploy.lock`)·로그(`~/Library/Logs/com.biblemap.deploy.log`)·macOS 키체인 우회용 임시 `DOCKER_CONFIG`(cli-plugins 심링크 포함) 준비, `.env`에서 `NEO4J_PASSWORD` 로드.
  2. `[1/3]` `cd frontend && npm install && npm run build` → `frontend/dist/`.
  3. `[2/3]` `docker compose -p biblemap build api`.
  4. `[3/4]` `docker compose -p biblemap up -d api nginx`.
  5. `[4/4]` `backend/scripts/inject_ko_names.py`를 최대 15회 재시도(Neo4j 준비 대기). 실패 시 배포 중단(exit 1). 그 외 `load_*`·`inject_*` 스크립트는 실행하지 않는다.
- Compose 프로젝트명은 `-p biblemap`으로 고정.
- 공개 도메인: `https://biblemap.taebro.com` — 이 머신의 스택을 Cloudflare Tunnel(cloudflared, `~/.cloudflared/config.yml`의 공유 터널 ingress 규칙, `service: http://localhost:8080`)로 노출한다(`BIBLEMAP_PLAN.md` 배포 절). 터널 설정 파일은 이 저장소 밖(머신 레벨). cloudflared는 outbound 전용 연결이라 인바운드 포트를 열지 않으며, ingress에 등록된 것(nginx의 8080)만 외부 접근 가능 — Neo4j는 구조적으로 차단. 따라서 `localhost:8080` == 프로덕션(동일 컨테이너·동일 Neo4j).
