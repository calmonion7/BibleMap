---
last_mapped_commit: 70f5fc64daa7b3c71f2773a4357ad68bba9ae7a5
mapped: 2026-07-24
---

# INTEGRATIONS

BibleMap이 의존하는 외부 데이터·서비스·데이터베이스·인프라와 그 연결점(파일·엔드포인트) 정리. 도메인 용어 정의는 여기 없음(그건 `CONTEXT.md`).

핵심 경계: 런타임 API(`backend/app/`)는 외부 HTTP를 호출하지 않는다. 외부 수집은 전부 빌드타임/오프라인 스크립트(`backend/scripts/`)가 수행하고 산출물을 `data/`에 커밋 → 런타임은 Neo4j + `data/` 오버레이만 읽는다. 프론트 런타임의 외부 호출은 지도 타일/폰트뿐.

## 데이터베이스: Neo4j

- 이미지 `neo4j:5`(`docker-compose.yml` 서비스 `neo4j`). Bolt `bolt://neo4j:7687`(컨테이너 네트워크 내부), 호스트에는 `127.0.0.1:7687`(Bolt)·`127.0.0.1:7474`(HTTP 브라우저)로만 노출. 데이터는 명명 볼륨 `neo4j_data:/data`.
- 인증: `NEO4J_AUTH=neo4j/${NEO4J_PASSWORD}`(compose가 루트 `.env`의 `NEO4J_PASSWORD`에서 파생). 앱은 `NEO4J_URI`/`NEO4J_USER`/`NEO4J_PASSWORD`로 접속.
- 런타임 접속점: `backend/app/db.py` 싱글턴 드라이버 `get_driver()`. 라우트가 `with driver.session()`으로 Cypher 실행.
- 인덱스: 기동 시 `backend/app/main.py` lifespan이 `Person`/`Place`/`Event`/`PeopleGroup`/`Book`의 `theographic_id` 인덱스 `IF NOT EXISTS` 보장. 적재 스크립트 `backend/scripts/load_theographic.py`도 동일 인덱스 생성.
- 캐시 특성: 집계·오버레이 응답이 `lru_cache`라 Neo4j/`data/` 변경 후에는 API 재시작(`docker compose -p biblemap restart api`)이 있어야 반영.

## 외부 데이터 소스 (빌드타임/오프라인 수집)

### theographic-bible-metadata (GitHub raw)

- 원본: `https://raw.githubusercontent.com/robertrouse/theographic-bible-metadata/master/json/{people,places,events,peopleGroups,verses,books}.json`.
- 주 적재: `backend/scripts/load_theographic.py` — `urllib.request`로 people/places/events/peopleGroups fetch → `status == publish` 필터 → 가족 폐포 wip 인물 보충 → Neo4j에 `MERGE (:Person/:Place/:Event/:PeopleGroup {theographic_id})` 및 관계(`PARENT_OF`/`CHILD_OF`/`SIBLING_OF`/`PARTNER_OF`/`MEMBER_OF`/`HAS_PARTICIPANT`/`OCCURS_AT`/`PART_OF`) 배치 적재. `theographic_id`가 전역 조인 키.
- 파생 오버레이 생성 스크립트도 동일 GitHub raw를 fetch: `build_verse_persons.py`(verses.json), `generate_book_context.py`(books.json), `generate_event_verses.py`(events.json + verses.json), `generate_person_context.py`(people.json) 등.
- 런타임 미접촉: 앱은 이 URL을 호출하지 않고 적재된 Neo4j만 읽음.

### getbible v2 API (절 본문)

- 원본: `https://api.getbible.net/v2/{slug}.json`(예 korean, kjv). 기본 urllib UA는 403 → 브라우저류 User-Agent 헤더 지정.
- 프리베이크(ADR-0003): `backend/scripts/generate_bible_text.py`가 한국어+영어 전체 번역본을 받아 정본 절 사전 `data/bible/verses.json`(약 10MB, `verseID → {textKo, textEn}`) 생성. `backend/scripts/generate_verse_text.py`는 생성 데이터(book_context·character_traits·place_context 등)의 인용 절 본문을 빌드타임에 인라인 저장(유니크 번역/책/장당 1회 fetch, 멱등).
- 런타임 미접촉: API는 절 본문을 `data/bible/verses.json`에서 합성(`overlays.bible_verses()`), event_verses 등은 `verseID` 참조만 보유. 런타임 getbible 호출 없음.

## 런타임 외부 서비스 (프론트엔드)

- 지도 타일: ArcGIS NatGeo 래스터 타일 `https://server.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}` — `frontend/src/MapView.jsx`의 maplibre 스타일 `sources.esri`(type raster, tileSize 256). 브라우저가 직접 요청.
- 지도 폰트(glyphs): `https://protomaps.github.io/basemaps-assets/fonts/{fontstack}/{range}.pbf` — 동 `MapView.jsx` 스타일 `glyphs`.
- 그 외 프론트 런타임 외부 호출은 없음(모든 앱 데이터는 `frontend/src/api.js`를 통해 자체 API로만).

## API 프록시 / 클라이언트 배선

- nginx 프록시(`nginx/nginx.conf`, 서비스 `nginx` `8080:80`):
  - `location /api/` → `proxy_pass http://api:8000/`(경로 `/api/` 프리픽스 제거, `Host`/`X-Real-IP`/`X-Forwarded-*` 헤더 전달).
  - `location = /index.html` → `Cache-Control: no-cache, no-store, must-revalidate`.
  - 정적 자산(`.js/.css/이미지/폰트`) → `Cache-Control: public, max-age=31536000, immutable`.
  - `location /` → SPA 폴백 `try_files $uri /index.html`(루트 `/usr/share/nginx/html` = `frontend/dist` 마운트).
- 프론트 API 클라이언트(`frontend/src/api.js`): `API_BASE`는 `VITE_API_URL`(프로덕션 `/api` → nginx 프록시, 개발 기본 `http://localhost:8000`). 모든 요청에 `?v=<__BUILD_ID__>` 캐시버스터 부착 → 배포 직후 `max-age` 응답 캐시 무력화.

## 인증 / 웹훅

- 사용자 인증 없음. API는 공개 읽기 전용(`CORSMiddleware` `allow_origins=["*"]`, `allow_methods=["GET"]`, `backend/app/main.py`). 자격증명·세션·토큰 없음.
- 유일한 인증은 Neo4j 비밀번호(`NEO4J_PASSWORD`, 루트 `.env`).
- 웹훅: 애플리케이션 레벨 웹훅 없음. 유일한 인바운드 트리거는 GitHub `push`(main) → self-hosted 러너 배포(`.github/workflows/deploy.yml`).

## 인프라 / 배포

- self-hosted 배포: `.github/workflows/deploy.yml`(`runs-on: self-hosted`)이 이 머신에서 `git reset --hard origin/main` 후 `bash deploy.sh` 실행. `deploy.sh`가 프론트 빌드 → api 이미지 빌드 → `docker compose -p biblemap up -d api nginx` → `python3 backend/scripts/inject_ko_names.py`(호스트 실행, 최대 15회 재시도).
- 프로덕션(`biblemap.taebro.com`)은 이 머신 스택의 프록시 — `localhost:8080` == prod, 동일 Neo4j. `data/`는 볼륨 마운트라 데이터 변경 후 `docker compose -p biblemap restart api`만으로 반영(lru_cache).

## API 엔드포인트 인벤토리 (런타임, GET 전용)

`backend/app/routes/*.py`의 라우트(약 30개). 모두 Neo4j + `data/` 오버레이에서 응답 합성:

- `nodes.py`: `/node/{node_id}`, `/node/{node_id}/places`, `/node/{node_id}/neighbors/grouped`
- `search.py`: `/search`
- `events.py`: `/events`, `/covenants`, `/messianic-prophecies`, `/topical-verses`, `/parables-miracles`
- `books.py`: `/books-overview`, `/book/{book_id}/chapters`, `/book/{book_id}/chapter/{n}`, `/book/{book_id}/quotations`
- `persons.py`: `/persons/curated`, `/person/{node_id}/family`, `/person/{node_id}/connections`, `/person/{node_id}/relations`, `/person/{node_id}/event-ids`, `/keypeople-cards`
- `journey.py`: `/person/{person_id}/journey`
- `places.py`: `/place/{place_id}/curated-persons`
- `tours.py`: `/tours`, `/tour/{tour_id}`
- `verses.py`: `/verse/{verse_id}/persons`, `/event/{event_id}/verses`
- `words.py`: `/words/{book_id}`, `/words/{book_id}/verses`
- `reliance.py`: `/reliance/ranking`, `/person/{person_id}/reliance`
- `stats.py`: `/stats` (세션 중 신규)

## 세션 중 신규 추가(작업 트리, 미커밋 — 검증됨)

- `backend/app/routes/stats.py` + `GET /stats`(위 인벤토리 참조).
- 런타임 오버레이 데이터셋(untracked)과 이를 서빙하는 `events.py` 엔드포인트/`overlays.py` 로더:
  - `data/covenants/covenants.json` → `overlays.covenants()` → `GET /covenants`
  - `data/messianic_prophecies/prophecies.json` → `overlays.messianic_prophecies()` → `GET /messianic-prophecies`
  - `data/jesus_parables_miracles/index.json` → `overlays.parables_miracles()` → `GET /parables-miracles`
  - `data/topical_verses/topics.json` → `overlays.topical_verses()` → `GET /topical-verses`
  - 네 데이터셋 모두 앱 자체 정본(`data/` 커밋 산출물)으로, 외부 API 없이 큐레이션됨.
