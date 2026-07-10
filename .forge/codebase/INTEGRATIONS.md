---
last_mapped_commit: 9c49a838dfe4c6e4695b9383ea961f15c9b117f2
mapped: 2026-07-10
---

# External Integrations

## 데이터베이스 — Neo4j

**서비스:** `docker-compose.yml` 서비스 `neo4j`, 이미지 `neo4j:5`.

**포트 바인딩:** `127.0.0.1:7474`(HTTP 브라우저), `127.0.0.1:7687`(Bolt) — 로컬호스트 전용, 외부 미노출.

**Driver:** Python `neo4j` 6.2.0. `backend/app/db.py`의 모듈 전역 싱글턴 `_driver = GraphDatabase.driver(uri, auth=(user, password))`. `get_driver()` 최초 호출 시 lazy 생성.

**접속 정보:** `NEO4J_URI`(compose 주입 `bolt://neo4j:7687`), `NEO4J_USER`(`neo4j`), `NEO4J_PASSWORD` 환경변수. 비밀번호 미설정 시 `RuntimeError` 발생. 실제 값은 루트 `.env`에만 존재하며 문서에 기록하지 않는다.

**인덱스:** 앱 기동 시 `lifespan`(`backend/app/main.py`)에서 `Person`·`Place`·`Event`·`PeopleGroup`·`Book` 라벨의 `theographic_id` 인덱스를 `IF NOT EXISTS`로 생성. 실패해도 로깅 후 계속 진행.

**볼륨:** `neo4j_data:/data` (compose named volume, 영속).

**관계 속성 — `CONTAINS_BOOK.primary`:** `Book-[:CONTAINS_BOOK]->Event` 관계에 boolean 속성 `primary` (ADR-0012). 발생 언급(첫 인용, `primary=true`) vs 회고적 인용(`primary=false`)을 구분한다. 적재 스크립트 `backend/scripts/load_books.py`(`verses[0]`의 책을 primary로 판정)와 `backend/scripts/load_person_events.py`(`books[0]`을 primary로 판정)에서 `SET r.primary = ...`로 설정.

## 데이터 소스 — Theographic Bible Metadata (GitHub Raw)

빌드/적재 타임에만 사용하는 외부 소스. 런타임 API는 호출하지 않는다.

**출처:** `https://raw.githubusercontent.com/robertrouse/theographic-bible-metadata/master/json/*.json` (`people.json`, `places.json`, `events.json`, `peopleGroups.json`, 일부 스크립트는 `books.json`·`verses.json` 추가 사용).

**사용처:**
- `backend/scripts/load_theographic.py` — 그래프 최초 적재. `urllib.request`로 4개 JSON을 받아 노드(Person/Place/Event/PeopleGroup)와 관계(PARENT_OF, CHILD_OF, SIBLING_OF, PARTNER_OF, MEMBER_OF, HAS_PARTICIPANT, OCCURS_AT, PART_OF)를 `MERGE`. `status == "publish"`만 필터, 배치 UNWIND(노드 500 / 관계 1000).
- `backend/scripts/generate_event_verses.py`, `generate_book_context.py`, `generate_verse_events.py` 등 데이터 생성 스크립트가 동일 raw URL을 `urllib.request`로 소비한다.

**인증:** 없음(공개 raw). 클라이언트 라이브러리 없이 표준 `urllib` 사용.

## 데이터 소스 — getBible API

**출처:** `https://api.getbible.net/v2/{slug}/{book_order}/{chapter}.json` — 구절 원문 텍스트.

**사용처:** `backend/scripts/generate_verse_text.py`, `backend/scripts/generate_person_event_verses.py` (빌드타임 생성 스크립트).

**인증:** 없음. 단, 기본 `Python-urllib` User-Agent에는 403을 반환하므로 브라우저류 UA 헤더 필요 — `_UA = "Mozilla/5.0 (compatible; BibleMap-build/1.0)"` (`generate_verse_text.py:55`, retro 2026-06-15 교훈). 요청 timeout 15~30초.

## LLM — Anthropic API (빌드타임 전용)

**용도:** 사건 요약·책 컨텍스트·인물 성품 등 큐레이션 데이터 생성. **런타임 서비스는 Anthropic을 호출하지 않는다** — `data/` JSON 산출용 오프라인 스크립트에서만 쓴다.

**클라이언트:** `anthropic` Python SDK (`anthropic.Anthropic(api_key=...)`). `backend/requirements.txt`에는 없고 스크립트 실행 시 별도 pip 설치하는 개발 전용 의존성.

**모델:** `claude-haiku-4-5-20251001` (`generate_book_events.py:75`, `generate_person_traits.py:59`).

**사용 스크립트:** `backend/scripts/generate_book_events.py`, `generate_book_context.py`, `generate_verse_events.py`, `generate_person_traits.py` 등.

**인증:** `ANTHROPIC_API_KEY` 환경변수. 미설정 시 `RuntimeError`. 값은 실행자가 임시 주입하며 레포·`.env`에 저장하지 않는다.

## 지도 타일 & 폰트 (프론트엔드, 브라우저 직접 호출)

MapLibre GL 스타일에서 클라이언트가 직접 로드한다 (`frontend/src/MapView.jsx`).

- **베이스맵 래스터 타일:** ESRI ArcGIS Online `NatGeo World Map` — `https://server.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}` (`type: raster`, `tileSize: 256`, source id `esri`). API 키 없음.
- **글리프(폰트) PBF:** Protomaps basemaps assets — `https://protomaps.github.io/basemaps-assets/fonts/{fontstack}/{range}.pbf` (스타일 `glyphs`).
- 지도 초기 뷰: center `[35.22, 31.78]`, zoom 5.

## 인증 / 아이덴티티

- 최종 사용자 인증 없음. 공개 읽기 전용 앱.
- API CORS: `allow_origins=["*"]`, `allow_methods=["GET"]`, `allow_credentials=False` (`backend/app/main.py`). GET 전용 공개 API.

## 모니터링 / 관측성

- 에러 트래킹 서비스 없음. 백엔드는 표준 `logging`(`logging.exception`)으로 예외 기록.
- 로깅 설정: `backend/app/main.py`의 `_configure_logging()`이 import 시점(라우터 import 전) 1회 `logging.basicConfig(level=INFO)`를 건다. `neo4j`/`urllib3`/`asyncio`는 WARNING 승격, `uvicorn`/`uvicorn.access`는 `propagate=False`(중복 emit 차단), `uvicorn.error`는 제외(부모로 전파해야 기동/에러 로그가 출력됨).
- 배포 로그: `deploy.sh`가 `/Users/calmonion/Library/Logs/com.biblemap.deploy.log`에 append.

## CI/CD & 배포

**호스팅:** 단일 self-hosted 호스트 (docker compose + nginx).

**파이프라인:** `.github/workflows/deploy.yml` — `main` push 트리거, `runs-on: self-hosted`. 스텝: `git fetch` → `git reset --hard origin/main` → `bash deploy.sh`.

**배포 스크립트 (`deploy.sh`):** lock 파일(`/tmp/biblemap-deploy.lock`)로 동시 실행 차단. macOS 키체인 우회용 임시 `DOCKER_CONFIG` 구성. 단계: (1) 프론트 `npm install`+`npm run build`, (2) `docker compose -p biblemap build api`, (3) `docker compose -p biblemap up -d api nginx`, (4) `backend/scripts/inject_ko_names.py`로 한글 이름 주입(최대 15회 재시도, 실패 시 배포 중단).

## API 표면 (내부, nginx `/api/` 프록시)

FastAPI 라우트(`backend/app/routes/`, 전부 GET). 프론트는 `frontend/src/api.js`의 `apiGet`으로 호출.

- `search.py`: `/search`
- `nodes.py`: `/person/{id}/event-ids`, `/node/{id}/places`, `/node/{id}/neighbors/grouped`, `/node/{id}`
- `events.py`: `/events`, `/event/{id}/verses`
- `books.py`: `/books-overview`
- `persons.py`: `/persons/curated`, `/person/{id}/connections`, `/person/{id}/relations`
- `journey.py`: `/person/{id}/journey`
- `places.py`: `/place/{id}/curated-persons`
- `tours.py`: `/tours`, `/tour/{id}`

## Webhook / 콜백

- 수신·발신 웹훅 없음.

## 환경변수 요약 (외부 연동 관점)

- 런타임: `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`, `DATA_DIR`, `VITE_API_URL`(빌드타임).
- 빌드타임 스크립트 전용: `ANTHROPIC_API_KEY`.
- 비밀 저장 위치: 루트 `.env`(gitignore됨). 템플릿은 `.env.example`. `ANTHROPIC_API_KEY`는 실행 시 임시 주입.
