---
last_mapped_commit: 22a678c36e40548a3d00ccf9205862505a59d9cb
mapped: 2026-06-16
---

# INTEGRATIONS

외부 API, 데이터베이스, 데이터 소스, 인증, 그리고 프론트↔백엔드 HTTP 연결을 정리한다. 도메인 의미는 다루지 않는다(CONTEXT.md 영역).

## Neo4j (그래프 DB)

- 단일 데이터 저장소. `neo4j:5` 컨테이너(`docker-compose.yml`), Bolt 프로토콜.
- 연결: `backend/app/db.py`의 `get_driver()` — `neo4j.GraphDatabase.driver(uri, auth=(user, password))`를 모듈 전역 싱글턴(`_driver`)으로 lazy 생성. URI/USER/PASSWORD는 환경변수(`NEO4J_URI` 기본 `bolt://localhost:7687`, `NEO4J_USER` 기본 `neo4j`, `NEO4J_PASSWORD` 필수 — 없으면 `RuntimeError`).
- compose가 api 서비스에 `NEO4J_URI=bolt://neo4j:7687`, `NEO4J_USER=neo4j`, `NEO4J_PASSWORD` 주입. 인증은 `NEO4J_AUTH=neo4j/${NEO4J_PASSWORD}`(compose가 파생).
- 인덱스: `backend/app/main.py`의 `lifespan`이 앱 시작 시 Person/Place/Event/PeopleGroup/Book 라벨의 `theographic_id` 인덱스를 `CREATE INDEX ... IF NOT EXISTS`로 보장(실패해도 예외 로깅 후 계속).
- 노드 식별자 키는 모든 라벨에서 `theographic_id`. 모든 라우트가 이 키로 MATCH/MERGE.

## 데이터 소스 — theographic-bible-metadata (GitHub)

원천 데이터는 GitHub raw JSON에서 빌드/적재 시점에 fetch한다(`urllib.request`). 저장소: `robertrouse/theographic-bible-metadata` (master 브랜치 `json/`).

- `backend/scripts/load_theographic.py` — people/places/events/peopleGroups JSON을 fetch해 노드·관계 적재.
  - URL: `https://raw.githubusercontent.com/robertrouse/theographic-bible-metadata/master/json/{people,places,events,peopleGroups}.json`.
  - `status == "publish"`만 필터(status 없는 엔티티는 포함). 배치 UNWIND로 노드 적재 후 관계 적재(PARENT_OF/CHILD_OF, SIBLING_OF, PARTNER_OF, MEMBER_OF, HAS_PARTICIPANT, OCCURS_AT, PART_OF).
- `backend/scripts/load_books.py` — books.json + events.json을 fetch해 Book 노드 적재, Book↔Event `CONTAINS_BOOK` 관계 생성(event.verses → book 역매핑). Book의 `startYear`/`endYear`는 event.startDate 집계로 추정. `nameKo`는 `data/names_ko/books.json`에서 병합.

## 한글 이름·콘텐츠 주입 스크립트

런타임 앱과 분리된 일회성 주입 스크립트(`backend/scripts/`). 모두 Neo4j에 직접 연결(`GraphDatabase.driver`, 동일 NEO4J_* 환경변수).

- `inject_ko_names.py` — `data/names_ko/{people,places,events,groups}.json`을 읽어 각 노드에 `nameKo`/`aliasesKo` SET. 배포 시 `deploy.sh` 4단계에서 실행.
- `inject_book_context.py` — `data/book_context/books.json` → Book 노드의 `background`/`themes`/`keyVerse` SET.
- `inject_person_traits.py` — `data/character_traits/people.json` → Person 노드의 `traits`(JSON 문자열 직렬화) SET. (`nodes.py`의 `/node/{id}`가 응답 시 다시 `json.loads`로 역직렬화.)

## 외부 API — Anthropic Claude (콘텐츠 생성 전용)

- `backend/scripts/generate_book_context.py`, `generate_person_traits.py` — `anthropic` SDK(`anthropic.Anthropic`)로 Claude(`claude-haiku-4-5-20251001`) 호출해 책 배경/주제/대표구절, 인물 성품을 생성하여 `data/book_context/`·`data/character_traits/`에 JSON 저장.
- 인증: `ANTHROPIC_API_KEY` 환경변수(없으면 `RuntimeError`). **빌드 타임 콘텐츠 생성 전용** — 런타임 앱(api 컨테이너)은 Claude를 호출하지 않으며 이 키도 필요 없다.

## 외부 API — getbible.net (성경 본문)

프론트엔드가 **브라우저에서 직접** 호출(백엔드 경유 없음). `frontend/src/SidePanel.jsx`.

- 번역 키: `korean`. getbible v2에는 절 단위 엔드포인트가 없어 **장(chapter) 단위 JSON**을 받아 클라이언트에서 해당 절을 찾는다.
- 엔드포인트: `https://api.getbible.net/v2/korean/{bookOrder}/{chapter}.json` — `fetchVerseText(bookOrder, chapter, verse)`가 호출, 응답 `verses[]`에서 `v.verse === verse`인 항목의 `text`를 사용(실패 시 `null`).
- `bookOrder`는 canonical 1~66. trait의 `verse_ref`(예: "창 15:6")는 `SidePanel.jsx`의 `BOOK_ABBR_ORDER`(개역 약어→번호) 맵과 `resolveVerseRef()`로 해석. Book의 `keyVerse`는 `parseVerseRef()`로 chapter/verse 추출(책 번호는 노드의 `bookOrder` 속성 사용).
- 용도: 인물 성품(trait)의 근거 구절 원문 lazy fetch, Book의 대표 구절(keyVerse) 원문 표시. 결과는 `verse_ref` 키로 컴포넌트 상태에 캐시.

## Frontend ↔ Backend HTTP

- 베이스 URL: `import.meta.env.VITE_API_URL || 'http://localhost:8000'`. 프로덕션은 `frontend/.env.production`의 `VITE_API_URL=/api`로 nginx 프록시(`/api/` → `http://api:8000/`)를 경유. 외부 노출 포트는 nginx `:8080`(`docker-compose.yml`, `nginx/nginx.conf`).
- 공유 클라이언트 `frontend/src/api.js` — `apiGet(path, {signal})`: GET → JSON, 비-OK면 status로 throw, AbortError는 전파. (단, App/MapView/TimelineView/SidePanel은 대부분 직접 `fetch`를 호출하고 `VITE_API_URL`로 베이스만 공유.)

호출되는 FastAPI 엔드포인트(모두 GET):

| 엔드포인트 | 정의 | 호출처(프론트) |
|-----------|------|---------------|
| `GET /node/{id}` | `backend/app/routes/nodes.py` `get_node` — 노드 + 이웃(최대 50) + `neighborTotal`; Person이면 `traits` 파싱, Book이면 `topPersons`/`topEvents` 추가 | `frontend/src/SidePanel.jsx` |
| `GET /node/{id}/places` | `nodes.py` `get_node_places` — 라벨별(Person/Event/PeopleGroup/Book/Place) 좌표 있는 Place 목록 | `frontend/src/MapView.jsx` |
| `GET /node/{id}/neighbors/grouped` | `nodes.py` `get_node_neighbors_grouped` — 타입별 이웃(각 타입 최대 30) | `frontend/src/MapView.jsx` |
| `GET /events` | `backend/app/routes/events.py` — startDate 있는 Event를 sortKey 순. `Cache-Control: no-store` | `frontend/src/TimelineView.jsx` |
| `GET /books` | `backend/app/routes/books.py` — Book 목록(bookOrder 순); startYear 없으면 `data/book_years_approx/books.json` 오버레이(`yearApprox=true`), 연도 없으면 제외. `Cache-Control: no-store` | `frontend/src/TimelineView.jsx` |
| `GET /search?q=` | `backend/app/routes/search.py` — nameKo/name CONTAINS 매칭, exact→prefix→contains 랭킹, LIMIT 20 | `frontend/src/App.jsx` |

- 요청 취소: 검색(`App.jsx`)·지도 fetch(`MapView.jsx`)는 `AbortController`로 직전 요청 abort(경쟁 조건 방지).

## 지도 타일 (외부)

`frontend/src/MapView.jsx`의 MapLibre GL 스타일은 외부 리소스를 직접 참조(API 키 없음):

- 래스터 타일: ArcGIS `https://server.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}` (`source: esri`, tileSize 256).
- 글리프(폰트): `https://protomaps.github.io/basemaps-assets/fonts/{fontstack}/{range}.pbf`.

## 인증 / 웹훅

- 사용자 인증·세션·웹훅 없음. 공개 읽기 전용 API(CORS `allow_origins=["*"]`, `allow_methods=["GET"]` — `backend/app/main.py`).
- 유일한 시크릿은 Neo4j 비밀번호(`NEO4J_PASSWORD`)와 콘텐츠 생성 스크립트의 `ANTHROPIC_API_KEY`.
