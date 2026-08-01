---
last_mapped_commit: 43f987cb37c2341c3cfeb54e4cf4dc33b4549c64
mapped: 2026-08-01
---

# INTEGRATIONS

BibleMap이 의존하는 외부 데이터·서비스·데이터베이스·인프라와 그 연결점(파일·엔드포인트) 정리. 도메인 용어 정의는 여기 없음(그건 `CONTEXT.md`).

핵심 경계: 런타임 API(`backend/app/`)는 외부 HTTP를 전혀 호출하지 않는다. 외부 수집은 전부 빌드타임/오프라인 스크립트(`backend/scripts/`)가 수행하고 산출물을 `data/`에 커밋 → 런타임은 Neo4j + `data/` 오버레이만 읽는다. 프론트 런타임의 외부 호출은 지도 타일·지도 글리프 2건뿐(폰트는 셀프호스팅).

## 데이터베이스: Neo4j

- 이미지 `neo4j:5`(`docker-compose.yml` 서비스 `neo4j`). 컨테이너 네트워크 내부는 `bolt://neo4j:7687`, 호스트에는 `127.0.0.1:7687`(Bolt)·`127.0.0.1:7474`(HTTP 브라우저)로만 노출(루프백 바인딩 = 외부 미노출). 데이터는 명명 볼륨 `neo4j_data:/data`.
- 인증: `NEO4J_AUTH=neo4j/${NEO4J_PASSWORD}`를 compose가 루트 `.env`의 `NEO4J_PASSWORD`에서 파생. 앱·스크립트는 `NEO4J_URI`/`NEO4J_USER`/`NEO4J_PASSWORD`로 접속(값은 이 문서에 기재하지 않음).
- 런타임 접속점: `backend/app/db.py`의 싱글턴 `get_driver()` 하나뿐. 라우트가 `with driver.session()`으로 Cypher를 직접 실행하며 ORM·쿼리빌더는 없다.
- 인덱스: 기동 시 `backend/app/main.py` lifespan이 `Person`/`Place`/`Event`/`PeopleGroup`/`Book`의 `theographic_id` 인덱스를 `IF NOT EXISTS`로 보장. 적재 스크립트 `backend/scripts/load_theographic.py`도 동일 인덱스를 생성한다.
- 오프라인 접속점(호스트 python3 실행): `backend/scripts/load_*.py`(적재), `inject_*.py`(속성 주입), `validate_event_chronology.py`(연대 검증). 배포 경로에서 실제로 도는 것은 `inject_ko_names.py` 하나(`deploy.sh` 4단계)와, Neo4j가 떠 있을 때의 `validate_event_chronology`(`scripts/check.sh`)다.
- 캐시 특성: 집계·오버레이 응답이 `lru_cache`이므로 Neo4j나 `data/`를 바꾼 뒤에는 API 재시작(`docker compose -p biblemap restart api`)이 있어야 반영된다.

## 외부 데이터 소스 (빌드타임/오프라인 수집 — 런타임 미접촉)

### 1. theographic-bible-metadata (GitHub raw)

- 원본: `https://raw.githubusercontent.com/robertrouse/theographic-bible-metadata/master/json/{people,places,events,peopleGroups,verses,books}.json`. 인증 없음, `urllib.request`로 단순 GET.
- 주 적재: `backend/scripts/load_theographic.py` — `URLS` 딕셔너리로 people/places/events/peopleGroups fetch → `status == publish` 필터 → 가족 폐포용 wip 인물 보충 → Neo4j에 `MERGE (:Person/:Place/:Event/:PeopleGroup {theographic_id})`와 관계(`PARENT_OF`/`CHILD_OF`/`SIBLING_OF`/`PARTNER_OF`/`MEMBER_OF`/`HAS_PARTICIPANT`/`OCCURS_AT`/`PART_OF`) 배치 적재. `theographic_id`가 전 계층 조인 키.
- 같은 raw 소스를 fetch하는 스크립트(총 8개): `load_theographic.py`(people·places·events·peopleGroups), `load_books.py`(books·events), `build_verse_persons.py`(verses), `generate_book_context.py`(books), `generate_person_context.py`(people), `generate_person_traits.py`(people·events), `generate_event_verses.py`(events·verses), `generate_verse_events.py`(books·events·verses).
- 런타임 미접촉: 앱은 이 URL을 호출하지 않고 적재된 Neo4j와 `data/` 산출물만 읽는다.

### 2. getbible v2 API (절 본문)

- 원본: `https://api.getbible.net/v2/{slug}.json`(번역본 전체) 및 `https://api.getbible.net/v2/{slug}/{book_order}/{chapter}.json`(장 단위). 인증 없음.
- 특이사항: 기본 urllib UA(`Python-urllib`)에는 403을 준다 → 세 스크립트 모두 `User-Agent: Mozilla/5.0 (compatible; BibleMap-build/1.0)` 헤더를 명시(`generate_bible_text.py:27`, `generate_verse_text.py:57`).
- 클라이언트 코드:
  - `backend/scripts/generate_bible_text.py` — `TRANSLATIONS = (("textKo","korean"), ("textEn","kjv"))`, 전체 번역본 2회 fetch로 정본 절 사전 `data/bible/verses.json`(~9.8MB, `verseID → {textKo, textEn}`) 생성.
  - `backend/scripts/generate_verse_text.py` — 생성 데이터(book_context·character_traits·place_context 등)의 인용 절 본문을 장 단위로 fetch해 빌드타임 인라인(번역/책/장당 1회, 멱등).
  - `backend/scripts/generate_person_event_verses.py` — 장 단위 fetch(`_fetch_count` 카운터로 호출 횟수 로그).
- 런타임 미접촉: API는 절 본문을 `overlays.bible_verses()`(= `data/bible/verses.json`)에서 합성하고, `event_verses` 등은 `verseID` 참조만 보유한다.

### 3. Anthropic API (빌드타임 콘텐츠 생성)

- SDK: `anthropic` 파이썬 패키지 — **`backend/requirements.txt`에 없고 호스트 python에만 설치**(현재 0.111.0). API 컨테이너에는 들어가지 않는다.
- 인증: `ANTHROPIC_API_KEY` 환경변수. 각 스크립트가 없으면 `RuntimeError`로 즉시 중단. 사용 모델은 5개 스크립트 모두 `claude-haiku-4-5-20251001`.
- 클라이언트 코드(5개): `backend/scripts/generate_book_context.py`, `generate_book_events.py`, `generate_person_context.py`, `generate_person_traits.py`, `generate_verse_events.py`. 공통 패턴 — `anthropic.Anthropic(api_key=...)` → 응답 텍스트에서 마크다운 코드펜스 제거 → `json.loads` → 산출물 JSON에 즉시 중간 저장(재실행 시 이미 있는 키는 SKIP) → `time.sleep(0.3)` 레이트리밋 여유.
- 런타임·CI 미사용: `deploy.sh`·`scripts/check.sh`·`.github/workflows/deploy.yml` 어디에도 이 키가 필요하지 않다(배포는 이 스크립트를 돌리지 않음).

## 런타임 외부 서비스 (프론트엔드)

- 지도 타일: ArcGIS NatGeo 래스터 `https://server.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}` — `frontend/src/MapView.jsx`의 maplibre 스타일 `sources.esri`(type `raster`, `tileSize: 256`, 단일 레이어 `esri-layer`). 브라우저가 직접 요청하며 API 키 없음.
- 지도 글리프: `https://protomaps.github.io/basemaps-assets/fonts/{fontstack}/{range}.pbf` — 동 `MapView.jsx` 스타일의 `glyphs`.
- 그 외 프론트 런타임 외부 호출 없음. 웹폰트는 셀프호스팅(`frontend/public/fonts/im-fell-english-latin.woff2` ← `frontend/src/index.css` `@font-face`), 아이콘은 번들된 `lucide-react`. 애널리틱스·에러추적·광고 SDK 없음.

## API 프록시 / 클라이언트 배선

- nginx(`nginx/nginx.conf`, 서비스 `nginx`가 `8080:80`):
  - `location /api/` → `proxy_pass http://api:8000/`(끝 슬래시로 `/api/` 프리픽스 제거). `Host`/`X-Real-IP`/`X-Forwarded-For`/`X-Forwarded-Proto` 전달.
  - `location = /index.html` → `Cache-Control: no-cache, no-store, must-revalidate`.
  - `location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff2?)$` → `Cache-Control: public, max-age=31536000, immutable`.
  - `location /` → SPA 폴백 `try_files $uri /index.html`(root `/usr/share/nginx/html` = `frontend/dist` 읽기전용 마운트).
- 프론트 API 클라이언트(`frontend/src/api.js`): `API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'`. 프로덕션 빌드는 `frontend/.env.production`의 `VITE_API_URL=/api`로 nginx 프록시를 탄다(API 컨테이너 포트는 호스트에 노출되지 않음). 모든 요청에 `?v=<__BUILD_ID__>` 캐시버스터를 붙여 배포 직후 옛 `max-age` 응답 재사용을 막는다.
- 백엔드 응답 캐시 헤더: 라우트별 `Cache-Control: max-age=300`(대부분) 또는 `public, max-age=3600`(`books.py` 장/인용, `reliance.py`, `verses.py`), 예외로 `/books-overview`는 `no-store`.

## 인증 / 웹훅

- 사용자 인증·세션·토큰 없음. API는 공개 읽기 전용 — `backend/app/main.py`의 `CORSMiddleware`가 `allow_origins=["*"]`, `allow_credentials=False`, `allow_methods=["GET"]`. 라우트 30개 전부 GET이며 쓰기 엔드포인트가 존재하지 않는다.
- 시스템에 존재하는 비밀은 두 개뿐: Neo4j 비밀번호(`NEO4J_PASSWORD`, 루트 `.env` — gitignore됨)와 빌드타임 전용 `ANTHROPIC_API_KEY`. OAuth·API 게이트웨이·JWT·레이트리밋 미들웨어 없음.
- 애플리케이션 레벨 웹훅 없음. 유일한 인바운드 트리거는 GitHub `push`(main) 이벤트 → self-hosted 러너 배포.

## CI/CD · 인프라 · 배포 표면

- 리모트: `https://github.com/calmonion7/BibleMap.git`(origin). 워크플로는 `.github/workflows/deploy.yml` 하나뿐 — 테스트·린트 전용 워크플로 없음(린트/검증은 `deploy.sh`가 부르는 `scripts/check.sh`에서 배포 직전에 돈다).
- 워크플로: `on: push` (`branches: [main]`) → `runs-on: self-hosted` → 단일 스텝이 `cd /Users/calmonion/Project/BibleMap && git fetch origin && git reset --hard origin/main && bash deploy.sh`. 체크아웃 액션도 없이 러너 머신의 작업 디렉터리(= 이 레포 클론)를 직접 리셋한다. GitHub Secrets 사용 없음(비밀은 머신 로컬 `.env`에서 온다).
- self-hosted 러너: 이 레포 전용 디렉터리 `/Users/calmonion/actions-runner-biblemap` + 전용 launchd 서비스 `~/Library/LaunchAgents/actions.runner.calmonion7-BibleMap.calmonionui-MacBookPro-biblemap.plist`. 같은 머신에 다른 프로젝트 러너(`actions-runner-lab-taebro`, `actions-runner-portfolion`)가 공존하므로 러너 디렉터리를 재사용/재등록하면 이 레포가 무음 미배포된다.
- 배포 실행체 `deploy.sh`: 락(`/tmp/biblemap-deploy.lock`) → 임시 `DOCKER_CONFIG`(macOS 키체인 우회, `~/.docker/cli-plugins` 심링크로 compose 플러그인 인식) → `.env` 로드 → `scripts/check.sh` 게이트 → 프론트 빌드 → `docker compose -p biblemap build api` → `up -d api nginx` → `python3 backend/scripts/inject_ko_names.py`(최대 15회 재시도, 실패 시 배포 중단). 로그는 `~/Library/Logs/com.biblemap.deploy.log`. `load_*` 적재는 배포가 하지 않는다.
- 프로덕션 도메인은 이 머신 스택 앞단의 프록시라 `localhost:8080` == prod이며 동일 Neo4j를 본다. `data/`가 볼륨 마운트이므로 데이터만 바뀌면 `docker compose -p biblemap restart api`로 충분(lru_cache 비우기).
- 컨테이너 레지스트리 미사용(이미지는 로컬 빌드), 클라우드 PaaS·CDN·오브젝트 스토리지 연동 없음.

## API 엔드포인트 인벤토리 (런타임, GET 전용 30개)

`backend/app/routes/*.py`. 모두 Neo4j + `data/` 오버레이에서 응답을 합성한다.

- `nodes.py` (4): `/person/{node_id}/event-ids`, `/node/{node_id}/places`, `/node/{node_id}/neighbors/grouped`, `/node/{node_id}`
- `search.py` (1): `/search`
- `events.py` (6): `/events`, `/covenants`, `/messianic-prophecies`, `/topical-verses`, `/parables-miracles`, `/event/{event_id}/verses`
- `books.py` (4): `/books-overview`, `/book/{book_id}/chapters`, `/book/{book_id}/quotations`, `/book/{book_id}/chapter/{n}`
- `persons.py` (4): `/persons/curated`, `/keypeople-cards`, `/person/{node_id}/connections`, `/person/{node_id}/relations`
- `family.py` (1): `/person/{node_id}/family`
- `journey.py` (1): `/person/{person_id}/journey`
- `places.py` (1): `/place/{place_id}/curated-persons`
- `tours.py` (2): `/tours`, `/tour/{tour_id}`
- `verses.py` (1): `/verse/{verse_id}/persons`
- `words.py` (2): `/words/{book_id}`, `/words/{book_id}/verses`
- `reliance.py` (2): `/person/{person_id}/reliance`, `/reliance/ranking`
- `stats.py` (1): `/stats` — 그래프 전역 집계(headline 총계·최다 등장 인물 Top10·최장 여정·시대별 사건 분포·책별 장수). `lru_cache(maxsize=1)` + `Cache-Control: max-age=300`.

## 오버레이 데이터셋 ↔ 로더 ↔ 엔드포인트 배선

`backend/app/overlays.py`의 로더 14종이 `data/` 정본 파일을 읽고 라우트가 서빙한다. 외부 API 없이 레포에 커밋된 정본만 사용:

| `data/` 경로 | `overlays.py` 로더 | 주 소비처 |
| --- | --- | --- |
| `book_events/books.json` | `book_events_raw()` | `events.py` (`_load_approx_book_index`) |
| `event_verses/events.json` | `event_verses()` | `events.py` `/event/{id}/verses` |
| `bible/verses.json` | `bible_verses()` | 절 본문 합성 전반(`verses.py`·`books.py` 등) |
| `word_distribution.json` | `word_distribution()` | `words.py` |
| `names_ko/books.json` | `books_ko()` | `books.py`·`stats.py` |
| `chapter_summaries/books.json` | `chapter_summaries()` | `books.py` |
| `chapter_sections/books.json` | `chapter_sections()` | `books.py` |
| `quotations/quotations.json` | `quotations()` | `books.py` `/book/{id}/quotations` |
| `messianic_prophecies/prophecies.json` | `messianic_prophecies()` | `events.py` `/messianic-prophecies` |
| `covenants/covenants.json` | `covenants()` | `events.py` `/covenants` |
| `jesus_parables_miracles/index.json` | `parables_miracles()` | `events.py` `/parables-miracles` |
| `place_coords/places.json` | `place_coords()` | `events.py`·`journey.py`·`stats.py` |
| `topical_verses/topics.json` | `topical_verses()` | `events.py` `/topical-verses` |
| `verse_persons/index.json` | `verse_persons()` | `verses.py` `/verse/{id}/persons` |

- `data/names_ko/*`(people·places·events·groups)는 오버레이가 아니라 `backend/scripts/inject_ko_names.py`가 배포 시 Neo4j 노드 속성(`nameKo`/`aliasesKo`)으로 주입한다.
- 지도 표출 커버리지는 `backend/scripts/validate_pm_map_coverage.py`가 고정한다 — `/parables-miracles`와 동일한 해석 규칙(항목의 `lat`/`lng` 또는 `placeId`의 `place_coords` 해석)으로 좌표 없는 항목 집합을 정본화해 회귀를 막는다.
