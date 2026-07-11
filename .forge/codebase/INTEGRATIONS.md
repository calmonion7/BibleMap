---
last_mapped_commit: 04e9be173b6a321e4daaa417f6f47004dc3cd687
mapped: 2026-07-11
---

# External Integrations

## 데이터베이스 — Neo4j

**서비스:** `docker-compose.yml` 서비스 `neo4j`, 이미지 `neo4j:5`.

**포트 바인딩:** `127.0.0.1:7474`(HTTP 브라우저), `127.0.0.1:7687`(Bolt) — 로컬호스트 전용, 외부 미노출.

**Driver:** Python `neo4j` 6.2.0. `backend/app/db.py`의 모듈 전역 싱글턴 `_driver = GraphDatabase.driver(uri, auth=(user, password))`. `get_driver()` 최초 호출 시 lazy 생성. `backend/scripts/*.py`는 앱 드라이버를 재사용하지 않고 각자 `GraphDatabase.driver(...)`를 직접 연다.

**접속 정보:** `NEO4J_URI`(compose 주입 `bolt://neo4j:7687`; 스크립트는 기본 `bolt://localhost:7687`), `NEO4J_USER`(`neo4j`), `NEO4J_PASSWORD` 환경변수. 비밀번호 미설정 시 `RuntimeError` 발생. 실제 값은 루트 `.env`에만 존재하며 문서에 기록하지 않는다.

**인덱스:** 앱 기동 시 `lifespan`(`backend/app/main.py`)에서 `Person`·`Place`·`Event`·`PeopleGroup`·`Book` 라벨의 `theographic_id` 인덱스를 `IF NOT EXISTS`로 생성. 실패해도 로깅 후 계속 진행. `backend/scripts/load_theographic.py`도 동일 인덱스를 생성한다.

**볼륨:** `neo4j_data:/data` (compose named volume, 영속).

**관계 속성 — `CONTAINS_BOOK.primary`:** `Book-[:CONTAINS_BOOK]->Event` 관계에 boolean 속성 `primary` (ADR-0012). 적재 스크립트 `backend/scripts/load_books.py`(`verses[0]`의 책을 primary로 판정)와 `backend/scripts/load_person_events.py`(`books[0]`을 primary로 판정)에서 `SET r.primary = ...`로 설정.

## 데이터 소스 — Theographic Bible Metadata (GitHub Raw)

빌드/적재 타임에만 사용하는 외부 소스. 런타임 API는 호출하지 않는다.

**출처:** `https://raw.githubusercontent.com/robertrouse/theographic-bible-metadata/master/json/*.json` (`people.json`, `places.json`, `events.json`, `peopleGroups.json`, 일부 스크립트는 `books.json`·`verses.json` 추가 사용).

**사용처:**
- `backend/scripts/load_theographic.py` — 그래프 최초 적재. `urllib.request`로 4개 JSON을 받아 노드(Person/Place/Event/PeopleGroup)와 관계(PARENT_OF, CHILD_OF, SIBLING_OF, PARTNER_OF, MEMBER_OF, HAS_PARTICIPANT, OCCURS_AT, PART_OF)를 `MERGE`. `status == "publish"`만 필터, 배치 UNWIND(노드 500 / 관계 1000).
- `backend/scripts/load_books.py`, `generate_event_verses.py`, `generate_book_context.py`, `generate_verse_events.py`, `generate_person_traits.py` 등 데이터 생성/적재 스크립트가 동일 raw URL을 `urllib.request`로 소비한다.

**인증:** 없음(공개 raw). 클라이언트 라이브러리 없이 표준 `urllib` 사용.

## 데이터 소스 — getBible API

**출처:** `https://api.getbible.net/v2/{slug}/{book_order}/{chapter}.json` — 구절 원문 텍스트(`korean`, `kjv` 번역 슬러그).

**사용처:** `backend/scripts/generate_verse_text.py`, `backend/scripts/generate_person_event_verses.py` (빌드타임 생성 스크립트, ADR-0003 — 런타임 getBible 호출을 없애기 위한 미리굽기). 유니크 (번역, 책, 장)당 1회 fetch·캐시하고 이미 본문이 있으면 스킵(멱등).

**인증:** 없음. 단, 기본 `Python-urllib` User-Agent에는 403을 반환하므로 브라우저류 UA 헤더 필요 — `_UA = "Mozilla/5.0 (compatible; BibleMap-build/1.0)"` (`generate_verse_text.py:55`, retro 2026-06-15 교훈). 요청 timeout 15~30초.

## LLM — Anthropic API (빌드타임 전용)

**용도:** 사건 요약·책 컨텍스트·인물 성품 등 큐레이션 데이터 생성. **런타임 서비스는 Anthropic을 호출하지 않는다** — `data/` JSON 산출용 오프라인 스크립트에서만 쓴다.

**클라이언트:** `anthropic` Python SDK (`anthropic.Anthropic(api_key=...)`). `backend/requirements.txt`에는 없고 스크립트 실행 시 별도 pip 설치하는 개발 전용 의존성.

**모델:** `claude-haiku-4-5-20251001` — `backend/scripts/generate_book_context.py:57`, `generate_book_events.py:75`, `generate_verse_events.py:107`, `generate_person_traits.py:59`.

**사용 스크립트:** `backend/scripts/generate_book_events.py`, `generate_book_context.py`, `generate_verse_events.py`, `generate_person_traits.py`. (`generate_book_context_enrich.py`는 실제 API 호출 없이 재생성 레시피만 담은 참고용 스크립트, ADR-0006.)

**인증:** `ANTHROPIC_API_KEY` 환경변수. 미설정 시 `RuntimeError`. 값은 실행자가 임시 주입하며 레포·`.env`에 저장하지 않는다.

## 데이터 파이프라인 (`backend/scripts/`)

전부 호스트에서 수동 실행하는 오프라인 스크립트(런타임 API 아님). Neo4j·외부 소스 접점 기준으로 분류하면:

**적재 (외부 소스 → Neo4j):**
- `load_theographic.py` — Theographic raw JSON → 노드/관계 `MERGE` (위 데이터 소스 참고).
- `load_books.py` — Book 노드 + `CONTAINS_BOOK` 관계.
- `load_verse_events.py` — `data/verse_events/events.json` → Event 노드 + `CONTAINS_BOOK` 멱등 적재.
- `load_person_events.py` — `data/person_events/*.json` → 인물 여정 Event 멱등 적재.
- `load_authored_events.py` / `load_authored_persons.py` — `data/authored_events/`·`data/authored_persons/` → 저작 Event/Person 멱등 적재.
- `enrich_place_coords.py` — `data/place_coords/places.json` → Place 노드 좌표 멱등 적재.

**생성 (외부 소스/LLM → `data/` JSON):**
- `generate_book_events.py`, `generate_book_context.py`, `generate_verse_events.py`, `generate_person_traits.py` — Anthropic API 사용(위 LLM 참고).
- `generate_event_verses.py`, `generate_approx_book_verses.py`, `generate_book_context_enrich.py` — 구절/배경 구조 생성(LLM 미호출 또는 참고용).
- `generate_verse_text.py`, `generate_person_event_verses.py` — getBible에서 구절 본문 인라인(위 getBible 참고).

**주입 (`data/` JSON → Neo4j `SET`):**
- `inject_ko_names.py` — `data/names_ko/` 한글 이름 주입. **`deploy.sh` [4/4] 단계에서 배포마다 실행**(Neo4j 준비까지 최대 15회 재시도, 실패 시 배포 중단). 나머지 inject 스크립트는 수동 실행.
- `inject_book_context.py` / `inject_place_context.py` — Book/Place 노드에 `background`·`themes`·`keyVerse` 주입.
- `inject_person_traits.py` — Person 노드에 `traits` 주입.
- `inject_date_corrections.py` — `data/date_corrections/{events,persons}.json`을 읽어 Event `startDate`/`sortKey`·Person 연대 필드를 `SET` (task#158, ADR-0014). 각 항목이 에코 필드(`title`/`oldStartDate`, `name`/`oldValue`)를 갖고, DB 현재값이 에코와 불일치하면 스킵+경고·이미 new값이면 조용히 통과하는 멱등 주입.

**검증 (외부 접점 없음, 순수 로컬/DB 검사, 위반 시 종료 코드 1):**
- `validate_event_chronology.py` — Neo4j Event/Person을 읽어 연대 이상(출생<활동<사망 역전, 사사 승계 순서, 대표 앵커 대비 역전, 전치 오타 후보 등)을 검출. `--json PATH`로 구조화 리포트 저장. 외부 HTTP 없음(Neo4j만 접속).
- `validate_traits.py` — `data/character_traits/people.json`이 AUTHORING.md 분류 규칙(통제 어휘·개수·`verse_ref` 형식·필드 결손)을 지키는지 기계검증. DB·네트워크 접점 없이 파일만 읽는다.

## 지도 타일 & 폰트 (프론트엔드, 브라우저 직접 호출)

MapLibre GL 스타일에서 클라이언트가 직접 로드한다 (`frontend/src/MapView.jsx`).

- **베이스맵 래스터 타일:** ESRI ArcGIS Online `NatGeo_World_Map` — `https://server.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}` (`type: raster`, `tileSize: 256`, source id `esri`, `maxzoom` 미지정). API 키 없음.
  - 무라벨 지형(`World_Terrain_Base`)으로 교체했다가 실사용 피드백("현대 지도와 대비해 보는 것이 성경 지리 이해에 더 낫다")으로 NatGeo 원복 — ADR-0013 지도 조항 개정판. 무라벨 재채택 시 z10+ 플레이스홀더(maxzoom 9 필요) 한계에 주의.
  - 지도 오버레이(여정선·정차지 배지·장소 마커)는 `frontend/src/mapLayers.js`에서 금색(`#c9a84c`)·양피지(`#f2ecdc`) 계열 색을 하드코딩해 그린다(Night Atlas 브랜드 액센트, `frontend/src/theme.js`의 `NIGHT` 상수와 동일 값).
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

**배포 스크립트 (`deploy.sh`):** lock 파일(`/tmp/biblemap-deploy.lock`)로 동시 실행 차단. macOS 키체인 우회용 임시 `DOCKER_CONFIG` 구성. 루트 `.env`를 `set -a`로 로드(호스트 실행 inject 스크립트가 동일 비번 사용). 단계: (1) 프론트 `npm install`+`npm run build`, (2) `docker compose -p biblemap build api`, (3) `docker compose -p biblemap up -d api nginx`, (4) `backend/scripts/inject_ko_names.py`로 한글 이름 주입(최대 15회 재시도, 실패 시 배포 중단). 그 외 적재/주입/검증 스크립트는 배포 파이프라인에 포함되지 않고 수동 실행한다.

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
