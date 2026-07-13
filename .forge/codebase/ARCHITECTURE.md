---
last_mapped_commit: 8af8f0563294387a7073d0b85e6f7de74b4b7b30
mapped: 2026-07-13
---

# ARCHITECTURE

BibleMap은 성경 인물·장소·사건 그래프를 탐색하는 3-tier 웹 애플리케이션이다. 그래프 DB(Neo4j)를 단일 진실원(source of truth)으로 두고, FastAPI 백엔드가 그 위에 읽기 전용 API를 얹고, React(Vite) 프론트가 이를 소비한다. 세 계층 모두 `docker-compose`로 컨테이너화되며 nginx가 정적 프론트 자산을 서빙하고 `/api`를 백엔드로 프록시한다.

## 전체 패턴

```
data/*.json  ──(load/inject/generate 스크립트)──▶  Neo4j 그래프  ──▶  FastAPI  ──▶  nginx  ──▶  React SPA
                                                        ▲                 │
                                         런타임 오버레이 JSON (data/*) ────┘  (요청 시 파일 직접 읽음)
```

- **빌드타임 파이프라인**: `data/` 하위의 JSON을 스크립트가 읽어 Neo4j에 노드/관계로 적재(`load_*`)하거나 기존 노드에 속성을 SET(`inject_*`)한다. 콘텐츠 JSON 자체를 만드는 것은 `generate_*`, 규칙 검증은 `validate_*`다. 이 스크립트들은 API 서버 밖에서 수동/배포 시점에 실행되는 일회성 배치다.
- **런타임 경로**: 일부 `data/` JSON은 Neo4j에 넣지 않고 API가 요청 시점에 직접 읽는다(런타임 오버레이). `backend/app/overlays.py`가 이 파일 해석/캐시를 담당한다.
- **API 계층**: `backend/app/routes/`의 9개 라우터가 Neo4j Cypher 조회 결과와 런타임 오버레이를 머지해 JSON으로 반환한다. 모두 GET 전용 읽기 API다.
- **프론트 계층**: React SPA가 `apiGet`으로 `/api/*`를 fetch해 지도·타임라인·관계·가계도·상세 패널을 렌더한다. 라우터 라이브러리 없이 자체 스테이지 상태 머신으로 화면을 전환하고 해시 URL로 딥링크한다.

## 계층 상세

### 1. Neo4j 그래프 (진실원)

- 드라이버는 `backend/app/db.py`의 `get_driver()` — `NEO4J_URI`/`NEO4J_USER`/`NEO4J_PASSWORD` 환경변수로 지연 초기화되는 전역 싱글턴이다. `NEO4J_PASSWORD` 미설정 시 `RuntimeError`.
- 노드 라벨: `Person`, `Place`, `Event`, `PeopleGroup`, `Book`. 모든 노드는 `theographic_id` 속성으로 식별되며, 이것이 그래프 전체의 조인 키다.
- 관계 종류(주로 `backend/scripts/load_theographic.py`·`backend/scripts/load_books.py`·`backend/scripts/load_authored_genealogy.py`에서 생성): `PARENT_OF`/`CHILD_OF`, `SIBLING_OF`, `PARTNER_OF`, `MEMBER_OF`(Person→PeopleGroup), `HAS_PARTICIPANT`(Event→Person), `OCCURS_AT`(Event→Place), `PART_OF`(Event→Event), `CONTAINS_BOOK`(Book→Event, `primary` 플래그 보유).
- 인덱스: `backend/app/main.py`의 lifespan 훅과 `load_theographic.py`의 `create_indexes`가 각 라벨의 `theographic_id`에 인덱스를 `IF NOT EXISTS`로 생성한다. lifespan 훅은 실패해도 예외를 삼키고 인덱스 없이 진행한다.

### 2. FastAPI 백엔드 (읽기 API)

- 엔트리: `backend/app/main.py` — `FastAPI(lifespan=...)`. 기동 시 인덱스 생성, `CORSMiddleware`(모든 origin 허용, `GET`만 허용), 9개 라우터 include. `_configure_logging()`가 라우터 import 전에 1회 호출돼 서드파티 로거를 WARNING으로 승격하고 uvicorn 로거 중복 emit을 차단한다(로깅 규약은 `CONVENTIONS.md` §13 참조).
- 라우터(모두 `backend/app/routes/`, prefix 없이 flat 경로):
  - `nodes.py` — `/node/{id}`(노드 상세 + 이웃 + Book이면 `topPersons`/`topEvents`), `/node/{id}/neighbors/grouped`, `/node/{id}/places`, `/person/{id}/event-ids`.
  - `events.py` — `/events`(타임라인 목록), `/event/{id}/verses`(근거 구절 드릴다운).
  - `books.py` — `/books-overview`.
  - `persons.py` — `/persons/curated`, `/keypeople-cards`, `/person/{id}/connections`, `/person/{id}/relations`.
  - `journey.py` — `/person/{id}/journey`(정차지 목록).
  - `places.py` — `/place/{id}/curated-persons`.
  - `search.py` — `/search?q=`(`nameKo`/`name` CONTAINS, LIMIT 20).
  - `tours.py` — `/tours`, `/tour/{id}`.
  - `family.py` — `/person/{id}/family`(인물 중심 가계도 서브그래프, 아래 §5).
- 캐싱: 조회 비용이 큰 계산은 `functools.lru_cache`로 프로세스 메모리에 보관한다(예: `events.py`의 `_compute_events`, `tours.py`의 `_list_tours`, `places.py`의 `_place_to_persons`, `persons.py`의 `_build_list`·`_build_connections`·`_build_relations`, `family.py`의 `_family_role_pairs`). 캐시 무효화는 앱 재시작으로만 이뤄지므로, 오버레이/그래프 변경 후 반영하려면 `api` 컨테이너 재시작이 필요하다. 응답에는 대체로 `Cache-Control` 헤더를 붙인다.

### 3. 런타임 오버레이 vs 그래프 노드

`backend/app/overlays.py`가 요청 시점에 읽는 JSON 오버레이의 로더/해석기다.

- 경로 해석: `_resolve(subpath)`/`_resolve_dir(subpath)`가 `DATA_DIR` 환경변수(컨테이너 기본 `/app/data`) → 리포지토리 `data/`(`_REPO_DATA_DIR`) 순으로 탐색한다. 파일이 없으면 경고 로그 후 빈 데이터로 폴백한다(서버가 죽지 않음).
- `overlays.py` 자체 캐시 로더 3종(`lru_cache(maxsize=1)`): `book_events_raw()`(`data/book_events/books.json`), `event_verses()`(`data/event_verses/events.json`), `bible_verses()`(`data/bible/verses.json` — `verseID → {textKo, textEn}` 정본 절 사전). 그 밖의 오버레이 파일은 각 라우터가 `_resolve`로 직접 열고 자체 `lru_cache`에 담는다.
- 그래프에 **넣지 않고** API가 직접 읽는 오버레이:
  - `data/book_events/books.json` — `events.py`가 `{bookId:[eventId]}`를 역방향 인덱스로 뒤집어 각 사건에 추정책을 부착.
  - `data/event_verses/events.json` — `events.py`의 `/event/{id}/verses`가 권별 근거 구절을 반환.
  - `data/bible/verses.json` — 절 본문(한/영) 정본 사전.
  - `data/person_events/*.json` — `persons.py`(`/persons/curated`, `/connections`), `journey.py`(`/journey`), `places.py`(`/curated-persons`)가 인물별 여정 파일을 직접 파싱.
  - `data/person_relations/relations.json` — `persons.py`의 `/relations`(국면·근거 구절)와 `family.py`의 `_family_role_pairs`(가족 관계 role 라벨)가 함께 읽음.
  - `data/keypeople/identity.json` + `data/person_context/people.json` + `data/keypeople_verses/people.json` — `persons.py`의 `/keypeople-cards`가 세 파일을 조인해 책별 keyPeople 카드를 조립(ADR-0017·0018).
  - `data/tours/*.json` — `tours.py`가 event-reference 오버레이로 읽음(ADR-0011: Neo4j 노드 추가/주입 없음).

즉 "그래프에 상주하는 데이터"와 "요청 시점에만 파일로 읽는 오버레이"가 공존하며, 라우터가 둘을 머지해 응답을 만든다.

### 4. React 프론트엔드 (Vite, SPA)

프론트는 **React 19 + Vite 8**이다(`frontend/src/`에 `App.jsx`·`main.jsx` 등 JSX, `react`/`react-dom`/`@vitejs/plugin-react` 의존). Vue 아님.

- 엔트리: `frontend/index.html` → `frontend/src/main.jsx`(`createRoot`, `StrictMode`) → `frontend/src/App.jsx`.
- API 클라이언트: `frontend/src/api.js` — 단일 베이스 URL(`import.meta.env.VITE_API_URL || 'http://localhost:8000'`) + `apiGet(path, {signal})` 헬퍼. 프로덕션 빌드는 `frontend/.env.production`의 `VITE_API_URL=/api`로 주입돼 nginx 프록시를 탄다.
- 화면 구조: 라우터 라이브러리 없이 `App.jsx`가 스테이지 상태 머신을 운용한다(아래 §6). 상태·URL·브라우저 히스토리 동기화는 훅 `frontend/src/useStageNavigation.js` + `frontend/src/urlState.js`, 노드 선택은 `frontend/src/useNodeSelection.js`가 담당한다.
- 주요 뷰 컴포넌트: `PersonHub.jsx`(진입 허브), `BibleOverviewView.jsx`, `TourList.jsx`, `MapView.jsx`(지도 — `maplibre-gl`), `TimelineView.jsx`, `RelationsView.jsx`, `PersonIntro.jsx`(인물 소개 뷰), `FamilyTree.jsx`(가계도 뷰), `JourneyList.jsx`, `SidePanel.jsx`(공유 상세 패널, 책 상세 페이지로도 재사용), `VerseLangTabs.jsx`, `Spinner.jsx`.
- 지도 서브시스템: `MapView.jsx` + `mapLayers.js` + `mapGeo.js` + `mapRingController.js`.
- 공유 모듈: `theme.js`(`TYPE_COLOR` 등), `constants.js`(모바일 브레이크포인트·시트 높이), `dates.js`, `index.css`(CSS 변수 기반 인라인 스타일).
- 번들 분할: `frontend/vite.config.js`가 `maplibre-gl`을 별도 청크(`maplibre`), 나머지 `node_modules`를 `vendor`로 `manualChunks` 분리.

### 5. 가계도 엔드포인트 (`/person/{id}/family`, ADR-0019)

`backend/app/routes/family.py`의 `get_person_family`는 인물 중심(ego-centric) 가계 서브그래프를 반환한다.

- Cypher 3종 조회: ① `CHILD_OF*1..100`으로 focus의 조상 집합을 모은 뒤 그 조상들 사이/조상→focus의 `PARENT_OF` 간선만 추림(순수 조상선 — 사촌·삼촌 계열 배제), ② focus→자녀→손주 2세대의 `PARENT_OF`, ③ focus의 `SIBLING_OF`·`PARTNER_OF` 상대.
- 응답 필드: `focus`(요청 id 에코), `nodes`(`{id, name, nameKo, gender, authored}` 목록), `parentEdges`(`[parentId, childId]` 배열), `siblings`, `partners`, `roles`(focus 기준 큐레이션 정본 role 맵).
- `roles`는 `data/person_relations/relations.json`의 `type=="가족"` 관계에서 손큐레이션된 원근 라벨(맏아들·둘째 아들 등)이다. theographic엔 출생순이 없어(children 배열 비정렬) 첫째/둘째의 유일한 정본 원천이다.
- 존재하지 않는 인물 id는 404가 아니라 빈 서브그래프로 폴백한다.
- 프론트 `FamilyTree.jsx`가 이 응답을 소비한다. `parentEdges`를 DAG 완화(relaxation)로 걸어 세대 번호(focus=0, 조상 양수, 자손 음수)를 매기고, 절대배치로 세대별 행을 그린 뒤 부모→자식을 손수 `<svg>` 베지어 커넥터로 잇는다(트리 라이브러리 없음). 노드 클릭 시 `onRecenter(id)`로 focus를 교체(재중심화)하고, `roleLabel`은 서버 `roles`가 있으면 그대로, 없으면 세대·gender로 폴백 라벨을 만든다. `authored` 노드엔 점 마커를 표시한다.

### 6. 프론트 스테이지 상태 머신

`frontend/src/useStageNavigation.js`가 `activeStage`를 6개 값으로 관리한다: `hub` | `overview` | `book` | `family` | `tours` | `explore`.

- **hub** — `PersonHub` 진입 화면. 인물 카드·"성경 책 둘러보기"·"테마 투어" 세 진입점.
- **overview** — `BibleOverviewView`. 책 카드 클릭 시 `openBook(id)`로 book 스테이지 진입.
- **book** — 책 상세 전용 전체화면. `bookId`(selectedNode와 분리된 별도 상태)로 `SidePanel`을 재사용해 렌더.
- **family** — 가계도 전용 전체화면. `familyId`(bookId와 동형으로 selectedNode와 분리)로 `FamilyTree` 렌더. 인물 상세/소개의 "가계도"에서 `openFamily(id)`로 진입, 트리 노드 클릭은 `recenterFamily(id)`로 focus만 교체, 뒤로는 `window.history.back()` 위임.
- **tours** — `TourList`. 투어 선택 시 explore로.
- **explore** — 인물/투어 탐험. 내부 `exploreView` 토글(`intro`·`map`·`timeline`·`relations`)로 `PersonIntro`/`MapView`/`TimelineView`/`RelationsView`를 전환. `explorePersonId`/`exploreTourId`는 상호배타이며 `selectedNode`와 분리된다.
- 상세 패널(`SidePanel`)은 hub를 제외한 스테이지에서 공유되며, 데스크톱은 우측 슬라이드인, 모바일은 하단 시트로 나타난다. 시트 열림 판정(`selectedNode != null && selectedNode !== explorePersonId`)이 모바일 표시와 history push의 단일 출처다.

### 7. 해시 딥링크 (ADR-0009 · ADR-0010)

`frontend/src/urlState.js`가 스테이지 ↔ 해시 문자열을 순수 매핑한다(라우팅 라이브러리 없음).

- `#/` 허브, `#/books` 개요, `#/tours` 투어 목록.
- `#/book/<id>` 책 상세(id = `theographic_id`, 책은 slug 없음).
- `#/family/<id>` 가계도(id = focus 인물 `theographic_id`).
- `#/person/<slug>` 탐험(인물), 뷰 접미사 `/timeline`·`/relations`·`/intro`.
- `#/tour/<slug>` 탐험(투어), 뷰 접미사 `/timeline`.
- `useStageNavigation`이 마운트 시 해시를 1회 파싱해 상태를 복원하고(인물 slug 해석은 `/persons/curated`의 slug↔id 맵 준비 후), 이후 상태 변화를 `pushState`/`replaceState`로 미러한다. push 조건은 stage/인물/투어/책/가계도 변경 또는 시트 열림(false→true), 그 외(뷰 토글·베이스)는 replace. `popstate`는 `history.state`에서 내비 상태를 복원한다.

## 데이터 흐름 (엔드투엔드)

1. **원천**: theographic 원본은 `robertrouse/theographic-bible-metadata` GitHub raw JSON에서 fetch(`load_theographic.py`·`load_books.py`). 저작/보정/콘텐츠 데이터는 `data/` 하위 JSON에 손으로/`generate_*` 스크립트로 작성.
2. **적재**: `load_*` 스크립트가 Neo4j에 노드/관계를 `MERGE`로 멱등 적재. `inject_*` 스크립트가 기존 노드에 속성을 `SET`. `apply_event_dedupe.py`가 중복 이벤트를 실삭제(구절 게이트, ADR-0016).
3. **런타임 머지**: API가 Neo4j 조회 + 런타임 오버레이(`data/book_events`, `data/event_verses`, `data/bible`, `data/person_events`, `data/person_relations`, `data/keypeople*`, `data/person_context`, `data/tours`)를 합쳐 JSON 반환.
4. **소비**: 프론트가 `/api/*`를 fetch해 렌더.

## 노드 provenance 모델 (authored vs theographic originals vs runtime overlays)

그래프에 상주하는 노드는 출처(provenance)에 따라 두 부류로 나뉘고, 세 번째 부류는 아예 그래프에 넣지 않는다.

- **theographic originals** — `load_theographic.py`가 GitHub theographic JSON을 fetch해 각 레코드의 `id`를 `theographic_id`로 `MERGE`한 노드. Person/Place/Event/PeopleGroup 및 그 사이 관계. `filter_published`로 `status == "publish"`만 적재(status 없는 Event/PeopleGroup은 전량). `theographic_id`는 `recXXXX` 형태의 원본 레코드 id 문자열이다.
- **authored 노드** — `data/authored_events/events.json`, `data/authored_persons/people.json`, `data/authored_persons/genealogy.json`, `data/person_events/*.json`, `data/verse_events/events.json`에 손으로 작성한 노드를 `load_authored_events.py`·`load_authored_persons.py`·`load_authored_genealogy.py`·`load_person_events.py`·`load_verse_events.py`가 `MERGE ... SET authored = true`로 적재. `theographic_id`는 `authored-*`(예: `authored-mt1-perez`, `authored-place-bethlehem`) 슬러그 문자열이다. `authored` 불리언 마커로 API가 원본과 저작본을 구분한다(예: `nodes.py`·`family.py` 응답의 `authored` 필드).
- **runtime overlays** — 그래프 노드로 만들지 않고 API가 요청 시 파일로 읽는 JSON(위 §3). tours가 대표적으로 ADR-0011에 따라 "event-reference 오버레이"이며 노드 주입이 없다.

이 외에 **속성 주입 오버레이**가 있다. 그래프 노드는 이미 존재하고, `inject_*` 스크립트가 별도 JSON을 읽어 노드 속성만 `SET`한다: `inject_ko_names.py`(`data/names_ko/*.json` → `nameKo`/`aliasesKo`), `inject_book_context.py`(`data/book_context/books.json`), `inject_place_context.py`(`data/place_context/places.json`), `inject_person_context.py`(`data/person_context/people.json`), `inject_person_traits.py`(`data/character_traits/people.json` → `traits`를 JSON 문자열로 저장하며 `nodes.py`가 응답 시 파싱), `inject_date_corrections.py`(아래). 이들은 런타임 오버레이와 달리 결과가 그래프에 상주한다.

### 족보 저작 보충 (ADR-0019)

`data/authored_persons/genealogy.json`은 마태복음 1장 아브라함→예수 단일 사슬(`chain`)이다. `load_authored_genealogy.py`가 `authored:true` 노드만 신규 `MERGE`하고(나머지는 기존 theographic id 참조), 연속 쌍 (chain[i], chain[i+1]) = (부모, 자식)에 `PARENT_OF`/`CHILD_OF`를 양방향 `MERGE`한 뒤, 사슬 끝(후손)에서 `CHILD_OF*`로 머리(조상)에 도달 가능한지 자체 검증한다(무단절). `load_theographic.py` 재적재 후엔 이 스크립트를 반드시 재실행해야 사슬이 복원된다.

## date_corrections 교정 오버레이 + inject 패턴 (ADR-0014)

theographic 원본은 Ussher형 연대계라 저작 레이어(보수 연대계)와 충돌하는 연대를 가진다. 이를 **원본을 직접 덮어쓰지 않고** 별도 교정 테이블로 다루는 것이 date_corrections 패턴이다.

- 데이터: `data/date_corrections/events.json`(항목: `{id, title, oldStartDate, newStartDate, newSortKey, rationale}`), `data/date_corrections/persons.json`(항목: `{id, name, field, oldValue, newValue, ...}`).
- 주입: `backend/scripts/inject_date_corrections.py`가 매칭 Event/Person 노드에 `startDate`/`sortKey`(events) 또는 지정 `field`(persons)를 `SET`한다.
- **에코 필드 멱등성**: 각 항목의 에코 필드(events: `title`/`oldStartDate`, persons: `name`/`oldValue`)가 DB 현재값과 일치할 때만 교정하고, 이미 `new*`면 조용히 통과, 불일치면 스킵+경고 — 잘못된 대상 덮어쓰기 방지의 기계 검증이다.
- **재실행 규칙**: `load_theographic.py`로 원본을 재적재하면 교정이 되돌아가므로 실행 시마다 `inject_date_corrections.py`를 반드시 재실행해야 한다. 이상 검출 보조 스크립트로 `backend/scripts/validate_event_chronology.py`.

## 엔트리 포인트 요약

- 백엔드 앱: `backend/app/main.py`(FastAPI, lifespan 인덱스, 9개 라우터 include).
- Neo4j 드라이버: `backend/app/db.py`(`get_driver` 싱글턴).
- 오버레이 로더: `backend/app/overlays.py`.
- 프론트 앱: `frontend/src/main.jsx` → `frontend/src/App.jsx`. HTML 진입 `frontend/index.html`.
- 프론트 API 클라이언트: `frontend/src/api.js`.

## 배포 위상

- 컨테이너: `docker-compose.yml` — `neo4j`(neo4j:5, 볼륨 `neo4j_data`, 127.0.0.1로만 노출), `api`(`build: ./backend`, `./data:/app/data` 마운트로 오버레이 접근), `nginx`(nginx:alpine, `frontend/dist`와 `nginx/nginx.conf` 마운트, `8080:80` 노출). API 포트는 외부 미노출 — 프론트는 nginx 프록시로만 접근.
- 백엔드 이미지: `backend/Dockerfile`(python:3.12-slim, `uvicorn app.main:app --host 0.0.0.0 --port 8000`). 의존성 `backend/requirements.txt`(fastapi==0.136.3 / neo4j==6.2.0 / uvicorn==0.49.0).
- 리버스 프록시: `nginx/nginx.conf` — `location /api/` → `http://api:8000/`, 정적 자산 장기 캐시(immutable), `location /` SPA 폴백(`try_files $uri /index.html`), `index.html`은 no-cache.
- 배포 스크립트: `deploy.sh` — 프론트 빌드 → api 이미지 빌드 → `docker compose -p biblemap up -d api nginx` → `inject_ko_names.py` 재주입(Neo4j 준비까지 최대 15회 재시도). CI는 `.github/workflows/deploy.yml`(self-hosted 러너).
