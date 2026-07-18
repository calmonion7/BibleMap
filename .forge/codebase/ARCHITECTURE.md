---
last_mapped_commit: 304eda1c53acff4c4860b838e8627483c666f74c
mapped: 2026-07-18
---

# ARCHITECTURE

BibleMap은 성경 인물·장소·사건 그래프를 탐색하는 3-tier 웹 애플리케이션이다. 그래프 DB(Neo4j)를 단일 진실원(source of truth)으로 두고, FastAPI 백엔드가 그 위에 읽기 전용 API를 얹고, React(Vite) 프론트가 이를 소비한다. 세 계층 모두 `docker-compose`로 컨테이너화되며 nginx가 정적 프론트 자산을 서빙하고 `/api`를 백엔드로 프록시한다.

## 전체 패턴

```
data/*.json  ──(load/inject/generate/build 스크립트)──▶  Neo4j 그래프  ──▶  FastAPI  ──▶  nginx  ──▶  React SPA
                                                             ▲                 │
                                              런타임 오버레이 JSON (data/*) ────┘  (요청 시 파일 직접 읽음)
```

- **빌드타임 파이프라인**: `data/` 하위의 JSON을 스크립트가 읽어 Neo4j에 노드/관계로 적재(`load_*`)하거나 기존 노드에 속성을 SET(`inject_*`)한다. 콘텐츠 JSON 자체를 만드는 것은 `generate_*`, 정본 JSON을 다른 정본에서 파생 산출하는 것은 `build_*`(예: `backend/scripts/build_word_distribution.py`, `build_verse_persons.py`, `build_word_verse_index.py`), 규칙 검증은 `validate_*`다. 이 스크립트들은 API 서버 밖에서 수동/배포 시점에 실행되는 일회성 배치다.
- **런타임 경로**: 일부 `data/` JSON은 Neo4j에 넣지 않고 API가 요청 시점에 직접 읽는다(런타임 오버레이). `backend/app/overlays.py`가 이 파일 해석/캐시를 담당한다.
- **API 계층**: `backend/app/routes/`의 12개 라우터가 Neo4j Cypher 조회 결과와 런타임 오버레이를 머지해 JSON으로 반환한다. 모두 GET 전용 읽기 API다.
- **프론트 계층**: React SPA가 `apiGet`으로 `/api/*`를 fetch해 지도·타임라인·관계·가계도·본문 리더·단어 분포·의존도·상세 패널을 렌더한다. 라우터 라이브러리 없이 자체 스테이지 상태 머신으로 화면을 전환하고 해시 URL로 딥링크한다. 전 화면 상단에 "책등" 전역 헤더(`SpineHeader.jsx`, ADR-0026)가 상시 표시된다.

## 계층 상세

### 1. Neo4j 그래프 (진실원)

- 드라이버는 `backend/app/db.py`의 `get_driver()` — `NEO4J_URI`/`NEO4J_USER`/`NEO4J_PASSWORD` 환경변수로 지연 초기화되는 전역 싱글턴이다. `NEO4J_PASSWORD` 미설정 시 `RuntimeError`.
- 노드 라벨: `Person`, `Place`, `Event`, `PeopleGroup`, `Book`. 모든 노드는 `theographic_id` 속성으로 식별되며, 이것이 그래프 전체의 조인 키다.
- 관계 종류(주로 `backend/scripts/load_theographic.py`·`backend/scripts/load_books.py`·`backend/scripts/load_authored_genealogy.py`·`backend/scripts/load_authored_mothers.py`에서 생성): `PARENT_OF`/`CHILD_OF`, `SIBLING_OF`, `PARTNER_OF`, `MEMBER_OF`(Person→PeopleGroup), `HAS_PARTICIPANT`(Event→Person), `OCCURS_AT`(Event→Place), `PART_OF`(Event→Event), `CONTAINS_BOOK`(Book→Event, `primary` 플래그 보유).
- 인덱스: `backend/app/main.py`의 lifespan 훅과 `load_theographic.py`의 `create_indexes`가 각 라벨의 `theographic_id`에 인덱스를 `IF NOT EXISTS`로 생성한다. lifespan 훅은 실패해도 예외를 삼키고 인덱스 없이 진행한다.
- **가족 폐포 wip 인물 (ADR-0021·0022)**: `load_theographic.py`의 `family_closure_wip()`가 publish 인물 ∪ 큐레이션 rec id를 시드로 가족 필드(`father`/`mother`/`children`/`partners`/`siblings`)로 도달 가능한 wip Person 레코드를 골라, **노드와 가족 간선(PARENT_OF·SIBLING_OF·PARTNER_OF)에만** 포함해 적재한다. `MEMBER_OF`·사건 참여 등 나머지 간선은 publish 전용을 유지한다. wip 노드는 `status = "wip"`로 마킹되고 publish는 `status` 속성이 없다(null). 큐레이션 rec는 wip이어도 무마킹(검수된 신원 — 검색 노출 유지). `backend/app/routes/search.py`가 `status <> 'wip'` 필터로 wip을 검색에서 제외한다.
- **어머니 간선 저작 보강 (ADR-0027, task#195)**: theographic 원본이 커버 못 하는, 성경에 어머니가 명시된 모자 관계 2쌍(`data/authored_persons/mothers.json`)을 `backend/scripts/load_authored_mothers.py`가 `PARENT_OF`/`CHILD_OF` 양방향 `MERGE`로 적재한다. 어머니·자식 모두 기존 노드여야 한다(`MATCH` — 노드 신규 생성 없음). `load_theographic.py` 재적재 후 재실행 필수(`load_authored_genealogy.py`와 동일 규칙).

### 2. FastAPI 백엔드 (읽기 API)

- 엔트리: `backend/app/main.py` — `FastAPI(lifespan=...)`. 기동 시 인덱스 생성, `CORSMiddleware`(모든 origin 허용, `GET`만 허용), 12개 라우터 include. `_configure_logging()`가 라우터 import 전에 1회 호출돼 서드파티 로거를 WARNING으로 승격하고 uvicorn 로거 중복 emit을 차단한다(로깅 규약은 `CONVENTIONS.md` "로깅 방출 규약" 절 참조).
- 라우터(모두 `backend/app/routes/`, prefix 없이 flat 경로, `main.py`가 `nodes, events, search, books, persons, journey, places, tours, family, words, verses, reliance` 순으로 include):
  - `nodes.py` — `/node/{id}`(노드 상세 + 이웃 + Book이면 `topPersons`/`topEvents`), `/node/{id}/neighbors/grouped`, `/node/{id}/places`, `/person/{id}/event-ids`.
  - `events.py` — `/events`(타임라인 목록), `/event/{id}/verses`(근거 구절 드릴다운, task#203부터 다권 근거 구절 확대).
  - `books.py` — `/books-overview`, `/book/{id}/chapters`(장 목차 — 장별 개요·대표절 + 장 묶음, task#206·212), `/book/{id}/chapter/{n}`(장 본문 리더, task#205), `/book/{id}/quotations`(구약↔신약 인용 관계, task#210).
  - `persons.py` — `/persons/curated`, `/keypeople-cards`, `/person/{id}/connections`, `/person/{id}/relations`(관계 항목에 `withSlug` 포함 — 인장 선화 렌더용, 큐레이션 상대만 존재).
  - `journey.py` — `/person/{id}/journey`(정차지 목록).
  - `places.py` — `/place/{id}/curated-persons`.
  - `search.py` — `/search?q=`(`nameKo`/`name` CONTAINS, `status='wip'` 제외, LIMIT 20).
  - `tours.py` — `/tours`, `/tour/{id}`.
  - `family.py` — `/person/{id}/family`(인물 중심 가계도 서브그래프, 아래 §5).
  - `words.py` — `/words/{book_id}`, `/words/{book_id}/verses?w=`(`VERSE_LIMIT=200`). 그래프 미접근 — 오버레이만 읽는다(아래 §6).
  - `verses.py` — `/verse/{verse_id}/persons`(그 절에 등장/언급되는 인물 목록). `overlays.verse_persons()` 색인에서 rec id를 얻고 Neo4j에서 이름을 해석. **현재 프론트 어느 화면도 이 엔드포인트를 호출하지 않는다** — 색인 인프라만 먼저 구축된 상태.
  - `reliance.py` — `/person/{id}/reliance`, `/reliance/ranking`(인물별 하나님 의존도, 아래 §9).
- **큐레이션 신원 규약의 단일 지점**: `backend/app/overlays.py`의 `curated_person_id(events)` — `data/person_events/<slug>.json`의 `events[0].participants[0]`이 그 인물의 `theographic_id`라는 규약(ADR-0022)을 함수 하나로 승격했다. 소비처는 `persons.py`(`_build_list`)·`places.py`(`_place_to_persons`)·`reliance.py`(`_slug_to_id`). `load_theographic.py` 스크립트만 자체 구현(앱 미임포트 관행).
- 캐싱: 조회 비용이 큰 계산은 `functools.lru_cache`로 프로세스 메모리에 보관한다(예: `events.py`의 `_compute_events`, `tours.py`의 `_list_tours`, `places.py`의 `_place_to_persons`, `persons.py`의 `_build_list`·`_build_connections`·`_build_relations`, `books.py`의 `_book_bb`·`_book_meta`·`_chapter_payload`·`_quotations_payload`, `family.py`의 `_family_role_pairs`·`_id_to_slug`·`_curated_ids`·`_lineage_ids`, `reliance.py`의 `_slug_to_id`·`_load_entries`·`_all_percents`). 캐시 무효화는 앱 재시작으로만 이뤄지므로, 오버레이/그래프 변경 후 반영하려면 `api` 컨테이너 재시작이 필요하다. 응답에는 대체로 `Cache-Control: public, max-age=3600` 헤더를 붙인다. 이 서버측 캐시와 별개로 브라우저 캐시 무력화는 프론트 `api.js`의 빌드 버전 쿼리(§4 하단)가 맡는다.

### 3. 런타임 오버레이 vs 그래프 노드

`backend/app/overlays.py`가 요청 시점에 읽는 JSON 오버레이의 로더/해석기다.

- 경로 해석: `_resolve(subpath)`/`_resolve_dir(subpath)`가 `DATA_DIR` 환경변수(컨테이너 기본 `/app/data`) → 리포지토리 `data/`(`_REPO_DATA_DIR`) 순으로 탐색한다. 파일이 없으면 경고 로그 후 빈 데이터로 폴백한다(서버가 죽지 않음).
- `overlays.py` 자체 캐시 로더 9종(`lru_cache(maxsize=1)`): `book_events_raw()`(`data/book_events/books.json`), `event_verses()`(`data/event_verses/events.json`), `bible_verses()`(`data/bible/verses.json` — `verseID → {textKo, textEn}` 정본 절 사전), `word_distribution()`(`data/word_distribution.json`), `books_ko()`(`data/names_ko/books.json` — `theographic_id → {ko, alias}`, 정경 순), `chapter_summaries()`(`data/chapter_summaries/books.json` — `bookId → [{chapter, summary, keyVerseId}]`, task#206), `chapter_sections()`(`data/chapter_sections/books.json` — `bookId → [{title, startChapter, endChapter}]` 장 묶음, task#212. 단장권은 부재), `quotations()`(`data/quotations/quotations.json`의 `quotations` 배열, task#209), `verse_persons()`(`data/verse_persons/index.json` — `verseID→[personRecId]` 색인, `verses.py`가 소비). 과거의 `word_verse_index()` 로더는 미사용이라 제거됐다(데이터 파일 `data/word_verse_index/index.json`은 잔존). 그 밖의 오버레이 파일은 각 라우터가 `_resolve`로 직접 열고 자체 `lru_cache`에 담는다.
- 그래프에 **넣지 않고** API가 직접 읽는 오버레이:
  - `data/book_events/books.json` — `events.py`가 `{bookId:[eventId]}`를 역방향 인덱스로 뒤집어 각 사건에 추정책을 부착.
  - `data/event_verses/events.json` — `events.py`의 `/event/{id}/verses`가 권별 근거 구절을 반환.
  - `data/bible/verses.json` — 절 본문(한/영) 정본 사전. `books.py`의 장 본문 리더(`/book/{id}/chapter/{n}`)와 인용 관계(`/book/{id}/quotations`)가 여기서 본문을 합성하고, `words.py`의 구절 substring 검색과 `reliance.py`의 계기/결과 구절 합성도 이 사전을 순회/조회한다(ADR-0003·0015 — 절 본문은 항상 이 정본 사전에서 합성, 개별 오버레이에 중복 인라인하지 않음).
  - `data/chapter_summaries/books.json` + `data/chapter_sections/books.json` — `books.py`의 `/book/{id}/chapters`가 장 목차(장별 한줄 요약+대표절 + 장 묶음 헤더)로 합성해 반환.
  - `data/quotations/quotations.json` — `books.py`의 `/book/{id}/quotations`가 302쌍 중 그 책이 낀 쌍만 골라 권별 집계 + 절 본문 합성으로 반환(구약 권은 `quotedBy`, 신약 권은 `quotes` 방향).
  - `data/word_distribution.json` — `words.py`가 서빙하는 책별 단어 분포 정본(빌드타임 산출물, 아래 §6).
  - `data/verse_persons/index.json` — 구절→인물 색인 정본, `verses.py`가 소비.
  - `data/person_events/*.json` — `persons.py`(`/persons/curated`, `/connections`), `journey.py`(`/journey`), `places.py`(`/curated-persons`), `reliance.py`(`_slug_to_id`)가 인물별 여정 파일을 직접 파싱.
  - `data/person_relations/relations.json` — `persons.py`의 `/relations`(국면·근거 구절)와 `family.py`의 `_family_role_pairs`(가족 관계 role 라벨)가 함께 읽음.
  - `data/person_slugs/seal_slugs.json` — 비큐레이션 인장 보유 인물 15명의 slug→rec id 정본(ADR-0025). `family.py`의 `_id_to_slug()`가 큐레이션 35인 slug 맵에 합성해 가계도 노드의 `slug` 필드를 채운다.
  - `data/keypeople/identity.json` + `data/person_context/people.json` + `data/keypeople_verses/people.json` — `persons.py`의 `/keypeople-cards`가 세 파일을 조인해 책별 keyPeople 카드를 조립(ADR-0017·0018).
  - `data/tours/*.json` — `tours.py`가 event-reference 오버레이로 읽음(ADR-0011: Neo4j 노드 추가/주입 없음).
  - `data/god_reliance/<slug>.json` — `reliance.py`가 인물별 하나님-상호작용 순간 배열을 읽음(아래 §9).

즉 "그래프에 상주하는 데이터"와 "요청 시점에만 파일로 읽는 오버레이"가 공존하며, 라우터가 둘을 머지해 응답을 만든다.

### 4. React 프론트엔드 (Vite, SPA)

프론트는 **React 19 + Vite 8**이다(`frontend/src/`에 `App.jsx`·`main.jsx` 등 JSX, `react`/`react-dom`/`@vitejs/plugin-react` 의존).

- 엔트리: `frontend/index.html` → `frontend/src/main.jsx`(`createRoot`, `StrictMode`). `main.jsx`는 렌더 전에 `localStorage['biblemap-theme'] === 'light'`면 `document.documentElement.dataset.theme = 'light'`를 동기 반영한다(첫 페인트 깜빡임 방지, ADR-0020) → `frontend/src/App.jsx`.
- API 클라이언트: `frontend/src/api.js` — 단일 베이스 URL(`import.meta.env.VITE_API_URL || 'http://localhost:8000'`) + `apiGet(path, {signal})` 헬퍼. 프로덕션 빌드는 `frontend/.env.production`의 `VITE_API_URL=/api`로 주입돼 nginx 프록시를 탄다. 모든 요청에 `?v=<BUILD_ID>` 쿼리를 부착한다 — `BUILD_ID`는 `frontend/vite.config.js`의 `define.__BUILD_ID__`로 빌드 시점에 박히는 타임스탬프이며, 배포마다 값이 바뀌어 백엔드의 `Cache-Control: max-age=3600` 응답 캐시를 배포 직후 무력화한다.
- **책등 전역 헤더 (ADR-0026, task#192~194)**: `frontend/src/SpineHeader.jsx`가 전 스테이지 상시 표시되는 높이 40px(`HEADER_H` export — `App.jsx`의 사이드패널 top 오프셋 계산에 공유) 헤더를 렌더한다. 표제(BibleMap, 클릭 시 대문) + 책갈피 리본 3부(인물·성경책·투어 — 활성 부만 길게 드리워지는 clip-path 리본) + 테마 토글(`localStorage['biblemap-theme']`). `App.jsx`가 `activeStage`에서 활성 부를 파생하고(`overview`/`book`/`words`/`reader`→성경책, `tours`/투어 탐험→투어, 나머지→인물), 리본 클릭은 기존 내비 콜백 조합(`backToHub`/`openOverview`/`openTours`)만 호출한다.
- 화면 구조: 라우터 라이브러리 없이 `App.jsx`가 스테이지 상태 머신을 운용한다(아래 §7). 상태·URL·브라우저 히스토리 동기화는 훅 `frontend/src/useStageNavigation.js` + `frontend/src/urlState.js`, 노드 선택은 `frontend/src/useNodeSelection.js`가 담당한다.
- 주요 뷰 컴포넌트: `PersonHub.jsx`(인물 목차 대문), `BibleOverviewView.jsx`, `TourList.jsx`, `MapView.jsx`(지도 — `maplibre-gl`), `TimelineView.jsx`, `RelationsView.jsx`, `PersonIntro.jsx`, `FamilyTree.jsx`, `WordDistributionView.jsx`, `ChapterReader.jsx`(본문 리더, 아래 §14), `RelianceView.jsx`, `JourneyList.jsx`, `SidePanel.jsx`(공유 상세 패널, 책 상세 페이지로도 재사용), `PersonMiniCard.jsx`(가계도 노드 바텀시트), `VerseLayer.jsx`(공통 구절 레이어 쉘, 아래 §11), `VerseLangTabs.jsx`, `Spinner.jsx`.
- 지도 서브시스템: `MapView.jsx` + `mapLayers.js` + `mapGeo.js` + `mapRingController.js`. 책 상세 전용 미니맵은 별도 컴포넌트 `BookStageMap.jsx`(§14 인접, task#207 — 상호작용 잠금, 같은 NatGeo 타일).
- 공유 모듈: `theme.js`(`TYPE_COLOR` 등), `constants.js`(모바일 브레이크포인트·시트 높이), `dates.js`, `personSymbols.jsx`(인물 인장 선화, 아래 §12), `bookSymbols.jsx`(책 인장 선화, 아래 §16), `index.css`(CSS 변수 기반 인라인 스타일 + 모션 토큰/클래스, 아래 §10).
- **듀얼 테마 (ADR-0020)**: 다크(Night Atlas)가 기본, 라이트(Day Atlas)는 옵트인. `frontend/src/index.css`가 같은 토큰 계약(`--type-*`, `--valence-*`, `--select-hl`, 표면/잉크 변수)에 값 두 벌을 정의하고 `:root[data-theme='light']`로 분기한다. `frontend/src/theme.js`의 `TYPE_COLOR`/`VALENCE_COLOR`/`SELECT_HL`은 리터럴 hex가 아니라 `var(--type-person)` 같은 **CSS var 참조**라 CSS 컨텍스트(인라인 style) 전용이다. 토글 UI는 `SpineHeader.jsx`에 있다.
- 번들 분할: `frontend/vite.config.js`가 `maplibre-gl`을 별도 청크(`maplibre`), 나머지 `node_modules`를 `vendor`로 `manualChunks` 분리.

### 5. 가계도 엔드포인트 + 뷰 (`/person/{id}/family`, ADR-0019 → task#195~197 개편)

`backend/app/routes/family.py`의 `get_person_family`는 인물 중심(ego-centric) 가계 서브그래프를 반환한다.

- Cypher 조회: ① `CHILD_OF*1..100`으로 focus의 조상 집합을 모은 뒤 순수 조상선의 `PARENT_OF` 간선만 추림, ② focus→자녀→손주 2세대의 `PARENT_OF`, ③ focus의 `SIBLING_OF`·`PARTNER_OF` 상대, ④ focus 자식의 다른 부모(어머니 그룹핑용 — 여성 부모 우선).
- 응답 필드: `focus`, `nodes`, `parentEdges`, `siblings`, `partners`, `mothers`(`{자식id: 다른부모id}` — task#196), `roles`(focus 기준 큐레이션 정본 role 맵, `data/person_relations/relations.json`의 `type=="가족"`에서).
- **노드 확장 필드(task#196)**: `slug`(인장 조회용 — `_id_to_slug()`가 큐레이션 35인 + `data/person_slugs/seal_slugs.json`의 인장 보유 15인 합성), `curated`/`hasIntro`(미니 카드 데이터 계층 플래그, ADR-0027), `role`(신분 한줄), `lineage`(예수 계보 여부 — `_lineage_ids()`가 예수(`_JESUS_ID`)에서 남계 사슬만 따라 오른 조상 + 마리아를 Cypher로 재현. 간선의 계보 여부는 양 끝 노드가 모두 lineage면 참으로 파생).
- 존재하지 않는 인물 id는 404가 아니라 빈 서브그래프로 폴백한다. 혈통 완전성은 §1의 가족 폐포 wip 적재 + 어머니 간선 보강이 뒷받침한다.
- **프론트 `FamilyTree.jsx`(task#195~197 3부 개편)**: `parentEdges`를 DAG 완화로 세대 번호(focus=0, 조상 양수, 자손 음수)를 매긴 뒤 — ① 조상선은 **앵커 행**(인장 보유 또는 focus 직계 3세대 `ANCHOR_GEN`)만 노출하고 비앵커 연속 구간은 "…N대" 접힌 세그먼트 칩으로 축약(탭 시 인라인 펼침), ② 자식 세대는 **어머니 그룹 컨테이너**(응답 `mothers` 기반, 그룹당 커넥터 1개)로 묶고 손주는 그룹별 요약 칩, ③ 노드는 3계층(focus 큰 카드/앵커 칩/일반 소형 칩). 레이아웃은 절대배치가 아닌 DOM 플로우(flex wrap)이고, 커넥터는 렌더 후 실측한 SVG 경로다. `lineage` 간선은 "메시아의 실" — 금색 `.thread-draw` 드로인(위→아래 스태거), 접힌 세그먼트를 지나는 구간은 금 점선. 노드 탭은 재중심화가 아니라 `PersonMiniCard.jsx` 바텀시트를 연다(즉시 렌더 + `/node/{id}` 지연 fetch, 재중심화·인물 페이지 이동 버튼은 카드 안).

### 6. 단어 분포 파이프라인 + 엔드포인트 (task#176)

빌드타임 정본 산출 → 오버레이 서빙 → 워드클라우드 렌더의 3단이다. **런타임 형태소 분석은 없다.**

- **빌드타임**: `backend/scripts/build_word_distribution.py`가 `data/bible/verses.json`(textKo)에서 kiwipiepy로 일반명사(NNG)·고유명사(NNP)를 추출해 책별 상위 60개 + 성경 전체(`"all"`) 상위 120개를 집계하고, 감정 극성 정본 `data/word_sentiment.json`(손큐레이션)을 병합해 `data/word_distribution.json`을 쓴다. 미분류 단어가 있으면 실패로 중단. 그래프 미접근, kiwipiepy는 별도 venv로 실행. 같은 STOPWORDS/토큰화 규약을 `build_word_verse_index.py`가 import해 재사용한다.
- **API**: `backend/app/routes/words.py` — `/words/{book_id}`는 `overlays.word_distribution()`을 그대로 서빙, `/words/{book_id}/verses?w=`는 `overlays.bible_verses()`를 순회해 `textKo` substring 매칭 구절을 최대 200건 반환. 구절 ref 표기는 `overlays.books_ko()`의 약칭(alias)으로 조립.
- **프론트**: `frontend/src/WordDistributionView.jsx` — 단일 타이포그래피 클라우드(감정 극성은 색+범례). 폰트 크기 ∝ √(빈도/최대빈도)(13~34px), 배치는 canvas `measureText` + 아르키메데스 나선의 자체 `layoutCloud()`. 단어 탭 → 구절 레이어(`VerseLayer` 공통 쉘, §11). 책 선택 드롭다운으로 같은 스테이지에서 대상 책만 교체.

### 7. 프론트 스테이지 상태 머신

`frontend/src/useStageNavigation.js`가 `activeStage`를 8개 값으로 관리한다: `hub` | `overview` | `book` | `family` | `words` | `reader` | `tours` | `explore`. 전 스테이지 위에 `SpineHeader`가 상시 얹힌다(§4).

- **hub** — `PersonHub` 인물 목차(대문). 시대(era) 8구간 장(章) 섹션으로 큐레이션 인물 카드를 배열하고, 카드에 인장 선화(`PersonSymbol`)를 얹는다. 세션 첫 진입 시 `book-open`(책 펼침 원근 회전) 입장. 책/투어 진입점과 테마 토글은 `SpineHeader` 리본으로 이관돼 props가 `onSelectPerson` 하나로 줄었다.
- **overview** — `BibleOverviewView`. 책 카드 클릭 시 `openBook(id)`로 book 스테이지 진입. 내비 바 하위 메뉴 탭(책 둘러보기 · 단어 분포)에서 `openWords('all')`.
- **book** — 책 상세 전용 전체화면. `bookId`로 `SidePanel`을 재사용해 렌더. 내비 바 하위 메뉴 탭(책 정보 · 본문 읽기 · 단어 분포)에서 `openReader(bookId)`/`openWords(bookId)`. 페이지 하단에 **정경 순서 내비(task#211)** — `/books-overview` 순서(`booksOrder` state, book 스테이지 진입 시 1회 로드)로 이전/다음 권 버튼을 붙이고(끝 권은 미노출), 클릭 시 같은 스테이지에서 `bookId`만 교체.
- **family** — 가계도 전용 전체화면. `familyId`로 `FamilyTree` 렌더. 내비 바에 focus 인물 인장(`PersonSymbol`, `key` 리마운트로 재중심화 시 1회 draw). 인물 상세/소개의 "가계도"에서 `openFamily(id)` 진입, 재중심화는 `recenterFamily(id)`(미니 카드 경유), 뒤로는 `window.history.back()` 위임.
- **words** — 단어 분포 전용 전체화면. `wordsBookId`(`'all'` 가능)로 `WordDistributionView` 렌더. 책 드롭다운은 `selectWordsBook(id)`, 뒤로는 `history.back()` 위임.
- **reader** — 본문 리더 전용 전체화면(task#205). `readerBookId`·`readerChapter`(null=장 그리드)로 `ChapterReader` 렌더. 책 상세 "본문 읽기" 탭에서 `openReader(bookId)` 진입, 장 이동은 `selectChapter(n)`(같은 스테이지에서 장만 교체), 뒤로는 `history.back()` 위임(아래 §14).
- **tours** — `TourList`. 투어 선택 시 explore로.
- **explore** — 인물/투어 탐험. 내부 `exploreView` 토글로 뷰를 전환하며, 인물 모드에서는 `intro`·`map`·`timeline`·`relations`·`reliance` 5개 값 + 전용 스테이지 진입점인 `family` 탭을, 투어 모드에서는 `map`·`timeline` 2개 값만 쓴다(`App.jsx`의 `EXPLORE_TABS` 등 상수). 내비 뒤로가기 버튼에 탐험 인물의 인장이 표시된다(`explorePersonSlug` — `useStageNavigation`이 `/persons/curated` 맵에서 파생). **무좌표 여정 분기(task#201)**: `App.jsx`가 여정 정차 전부에 좌표가 없으면(`journeyMapless` — 셋·아벨·에녹) map 뷰에서 지도 대신 `JourneyList`를 전면 리스트(`mapless` prop)로 렌더한다(MapView는 언마운트하지 않고 `display:none` — 항상 마운트 규약 유지).
- 상세 패널(`SidePanel`)은 hub를 제외한 스테이지에서 공유되며, 데스크톱은 우측 슬라이드인(top 오프셋 `HEADER_H + NAV_H`), 모바일은 하단 시트로 나타난다. 시트 열림 판정(`selectedNode != null && selectedNode !== explorePersonId`)이 모바일 표시와 history push의 단일 출처다. `relations`·`reliance`(그리고 `intro`에서 본인 선택)일 땐 SidePanel을 우측으로 밀어 넣어 숨긴다.

### 8. 해시 딥링크 (ADR-0009 · ADR-0010)

`frontend/src/urlState.js`가 스테이지 ↔ 해시 문자열을 순수 매핑한다(라우팅 라이브러리 없음).

- `#/` 허브, `#/books` 개요, `#/tours` 투어 목록.
- `#/book/<id>` 책 상세(id = `theographic_id`, 책은 slug 없음).
- `#/family/<id>` 가계도(id = focus 인물 `theographic_id`).
- `#/words/<id>` 단어 분포(id = 책 `theographic_id` 또는 `all`).
- `#/read/<id>` 본문 리더 장 그리드, `#/read/<id>/<n>` 장 본문(id = 책 `theographic_id`, n = 장 번호).
- `#/person/<slug>` 탐험(인물), 뷰 접미사 `/timeline`·`/relations`·`/intro`·`/reliance`.
- `#/tour/<slug>` 탐험(투어), 뷰 접미사 `/timeline`.
- `useStageNavigation`이 마운트 시 해시를 1회 파싱해 상태를 복원하고(인물 slug 해석은 `/persons/curated`의 slug↔id 맵 준비 후), 이후 상태 변화를 `pushState`/`replaceState`로 미러한다. push 조건은 stage/인물/투어/책/가계도/단어책/리더책/리더장 변경 또는 시트 열림(false→true), 그 외(뷰 토글·베이스)는 replace. `popstate`는 `history.state`에서 내비 상태를 복원한다.

### 9. 하나님 의존도 엔드포인트 + 뷰 (`/person/{id}/reliance`, ADR-0023)

`backend/app/routes/reliance.py`는 인물별 "하나님-상호작용 순간"을 계기(trigger)→(선택적)행동(response)→결과(outcome)의 2~3단 구조로 서빙한다. 정본은 `data/god_reliance/<slug>.json`(32명), 스키마·저작 규칙은 `data/god_reliance/AUTHORING.md`.

- 각 항목의 `mode`는 통제어휘 5종(`물음-응답`·`물음-침묵`·`부르심`·`독단-개입`·`독단-어긋남`) 중 하나. `부르심`은 `obeyed` 또는 `covenant: true` 중 정확히 하나를 추가로 가진다. **사건 단위 원칙**: 하나의 하나님-상호작용 사건은 하나의 순간으로만 센다.
- `reliance.py`가 하는 일: ① `_slug_to_id()`로 슬러그↔인물 id 매핑(`overlays.curated_person_id` 사용), ② `verse` 참조("창 2:7")를 `_resolve_verse()`로 정본 절 키(`BBCCCVVV`)로 변환해 `overlays.bible_verses()`에서 본문 합성, ③ `_percent()`로 의존도 % 계산(분자 = `물음-*` 전체 + `obeyed`/`covenant`인 `부르심`), ④ 전 인물 백분위/순위. `/reliance/ranking`은 전 인물 랭킹 배열.
- 검증: `backend/scripts/validate_god_reliance.py`.
- **프론트**: `frontend/src/RelianceView.jsx` — 도넛 게이지(0→목표값 스윕) + mode 색상 세그먼트 막대 + 연대순 "생애 궤적"(뱀 배치 + 베지어 커넥터). 궤적 점 클릭 시 구절 레이어(`VerseLayer` 공통 쉘)에 계기→(행동)→결과를 연다. "인물 랭킹" 버튼이 `/reliance/ranking`을 지연 로드해 모달로 띄운다.

### 10. 모션 클래스 레이어 (ADR-0024 → 0025·0026 확장)

`frontend/src/index.css`가 정의하는 무의존(라이브러리 없는) CSS 애니메이션 토큰·클래스 체계.

- **토큰**: `--dur-fast`(150ms)·`--dur-base`(250ms)·`--dur-slow`(400ms)·`--dur-draw`(1000ms, 선화 draw-on) + `--ease-out`/`--ease-in-out`/`--ease-drawer`/`--ease-pop`. 컴포넌트는 duration·easing을 하드코딩하지 않고 이 토큰만 참조한다. 전역 포털 레이어 공용으로 `--z-verse`(1000)·`--scrim` 토큰도 여기 정의(task#202).
- **reduced-motion 가드**: `@media (prefers-reduced-motion: reduce)`가 `--dur-*`를 전부 1ms로 붕괴시키고 `animation-delay`를 전역 0으로 무효화한다. `Spinner`만 의도적 예외.
- **클래스**: `stage-in`(스테이지 전환), `overlay-in`/`modal-in`(포털 배경/카드 입장), `sheet-in`(바텀시트 드로어 입장 — `PersonMiniCard`·`VerseLayer` 모바일), `card-in`(카드 스태거), `cloud-in`/`word-in`(워드클라우드), `bar-reveal`·`stop-bar-in`(막대 성장), `symbol-draw`(인장 선화 draw-on — `personSymbols.jsx`/`bookSymbols.jsx`의 `pathLength=1` 정규화 전제, 지연은 `--sym-delay`), `thread-draw`(가계도 메시아의 실 금색 드로인, 지연은 `--thread-delay`), `book-open`(허브 대문 책 펼침 원근 회전, 세션 첫 진입 1회), `pressable`(`:active` 눌림 피드백).
- **제약**: transform·opacity만 애니메이트. 입장(enter)만 있고 exit는 즉시 언마운트 — 단 `VerseLayer` 모바일 시트의 퇴장은 드래그 추종 위치에서 이어 내려가야 해서 인라인 transform 트랜지션으로 처리하는 **의도된 예외**다(시트 한정). 지도(MapLibre 캔버스)는 이 체계 밖.

### 11. 구절 레이어 공통 쉘 (`VerseLayer.jsx`, task#202)

`frontend/src/VerseLayer.jsx`는 여러 파일에 흩어져 있던 "양피지 구절 모달" 골격을 하나로 승격한 공통 쉘이다. 소비처: `JourneyList.jsx`·`TimelineView.jsx`·`RelationsView.jsx`·`PersonIntro.jsx`·`SidePanel.jsx`(사건/성품/여정없는 인물/**인용 대조 — task#210**)·`RelianceView.jsx`·`WordDistributionView.jsx`·`ChapterReader.jsx`(장 본문 자체가 양피지 카드).

- **반응형 프리젠테이션**: 뷰포트 ≤768px(`MOBILE_BREAKPOINT`)는 하단 시트(maxHeight 80vh · minHeight 38vh), 초과는 중앙 모달(maxWidth 520). 양쪽 다 `createPortal(document.body)` + `role="dialog" aria-modal` + ESC 닫기.
- **존 분리**: 헤더(그랩 핸들·색 점·제목·한/영 탭 `VerseLangTabs`·× 버튼·refLine)는 고정 존, 본문(`children`)만 스크롤 — 긴 구절에서도 닫기·언어 전환이 항상 손에 닿는다.
- **모바일 닫기 제스처**: 핸들·헤더 존 전용 터치 드래그(손가락 추종 → 80px(`CLOSE_DRAG_PX`) 초과 시 슬라이드다운 닫힘, 미만은 스프링백) — 본문 스크롤과 완전 분리. 데스크톱 모달은 즉시 언마운트.
- **부속 export**: `VerseBookTabs`(다권 근거 구절의 pill 탭 — task#203 다권 데이터와 짝), `paperTextStyle`(구절 본문 공통 타이포 — fontSize 15.5 통일 기준). 카드 배경은 테마 불변 양피지 토큰(`--paper*`) — 성경 구절 본문 전용 원칙.
- 각 소비처는 자기 데이터 fetch/로딩/빈 상태만 `children`으로 얹는다(예: `JourneyList.jsx`의 `renderVerseLayer()`, `SidePanel.jsx`의 `renderQuoteLayer()` — 인용문(신약)/원문(구약) 2단 대조).

### 12. 인장(상징물 선화) 시스템 — 인물 (`personSymbols.jsx`, ADR-0025)

`frontend/src/personSymbols.jsx`는 인물별 상징물 선화(stroke-only SVG) 50점(큐레이션 35 + 계보 인장 15)의 단일 정본이다.

- 규격: viewBox 64×64, `stroke=currentColor`·`fill` 없음, 모든 stroke 요소 `pathLength=1` 정규화(`index.css` `.symbol-draw`의 dash 1 = 전체 선). 얼굴 초상 없음 — 인물별 상징 장면/사물만(신학적 민감성·품질 일관성).
- export: 기본 `PersonSymbol({slug, size, draw, delayMs, style})`(미등록 slug는 범용 "펼쳐진 책" `FALLBACK`), `hasSymbol(slug)`(가계도 앵커 판정용 — 폴백 렌더와 구별).
- 사용처: `PersonHub.jsx`(허브 카드), `PersonIntro.jsx`(소개 히어로), `App.jsx`(탐험 내비 인장·가계도 내비 인장), `FamilyTree.jsx`(앵커/focus 노드), `PersonMiniCard.jsx`(카드 헤더), `RelationsView.jsx`(상대 아바타 — 없으면 유형 아이콘 폴백), `JourneyList.jsx`(여정 헤더).
- 비큐레이션 인장 인물의 slug↔id 정본은 `data/person_slugs/seal_slugs.json`이며 백엔드 `family.py`가 이를 합성해 응답 `slug`로 내려준다(§5).

### 13. 연표 시대 밴드 + 관계 탭 + 여정 리스트 (task#198~201)

- **`frontend/src/TimelineView.jsx`(task#200)**: 사건을 8구간 시대 밴드(`ERA_BANDS` — ADR-0014 보수 연대 경계, `persons.py`의 `_ERA_ORDER`와 정합: 원시사~신약)로 섹션화한다. 각 시대 헤더는 `position: sticky`, 섹션 본문은 연속 세로 레일 위 사건 도트, 필터 배너(책/인물 필터)는 스크롤 밖 상단 고정. 근거 구절은 `VerseLayer` + `VerseBookTabs`.
- **`frontend/src/RelationsView.jsx`(task#198·199)**: `/person/{id}/relations`를 유형 섹션(`TYPE_ORDER` 9유형, lucide 아이콘)으로 군집한 관계 카드 개요(인장 아바타 `PartnerAvatar` + 사건 칩) ↔ 초점 쌍(`focusIdx` — 두 인물 사이 국면 스토리라인) 2단 구조. 하단에 "다른 축 안내" 푸터(`onSwitchView`/`onOpenFamily`로 타임라인·가계도 점프). 전역 시간축 없음 — 시간은 칩의 연도로.
- **`frontend/src/JourneyList.jsx`(task#201)**: 여정 정차 리스트. `personSlug`가 있으면 헤더에 소형 인장. `mapless` 모드(무좌표 여정)는 지도 없이 전면 리스트로 렌더되고 상단에 지도 미표시 안내 한 줄 + 본문 폭 제한. 구절은 📖 칩 → `VerseLayer`.

### 14. 본문 리더 + 장 개요/장 묶음 (`/book/{id}/chapters`·`/book/{id}/chapter/{n}`, task#205·206·212)

`ChapterReader.jsx` + `backend/app/routes/books.py`가 프리베이크 정본 절 사전(`bible/verses.json`)만으로 신규 저작 없이 통독 화면을 만든다(ADR-0003·0015).

- **장 목차(장 그리드)**: `chapter == null`일 때 `/book/{id}/chapters` 응답을 렌더. `data/chapter_summaries/books.json` 오버레이가 있으면 "읽히는 목차"(장 번호 + 한줄 요약 행)로, 없으면 숫자만의 그리드로 폴백. `data/chapter_sections/books.json`(장 묶음, 61권 — 단장권은 부재)이 있으면 목차 행 사이에 묶음 제목 헤더(예: "아브라함 언약" 12~25장)를 끼워 구조화한다.
- **장 본문**: `/book/{id}/chapter/{n}`이 그 장의 절을 절 키(`BBCCCVVV`) 순으로 반환. 응답에 `chapter_summaries`의 그 장 한줄 요약(있으면)도 동봉해 리더 헤더 아래 표시. 양피지 카드(`--paper*`) + 한/영 탭(`VerseLangTabs`) + 이전/다음 장 버튼.
- 두 엔드포인트 모두 `_book_bb()`(`books_ko()` 순서로 도출한 정경 순번, 절 키의 `BB` 부분)와 `_book_meta()`(Book 노드의 `nameKo`/`chapterCount`, 1회 Neo4j 조회 캐시)를 공유해 조립한다. 미지의 책은 404, 범위 밖 장은 빈 목록.
- 진입: 책 상세(`book` 스테이지) 내비 바 "본문 읽기" 탭 → `reader` 스테이지(`readerBookId`/`readerChapter`, §7). 딥링크 `#/read/<id>[/<n>]`(§8).

### 15. 인용 관계 — 구약↔신약 직접 인용 (`/book/{id}/quotations`, task#209·210)

정본 `data/quotations/quotations.json`(302쌍, `{ntVerseIds, otVerseIds, ntRangeLabel, otRangeLabel, note?}`)을 `backend/scripts/validate_quotations.py`가 절 실존·측(신약/구약) 위반·라벨 자기일치·중복을 기계 검증한다.

- `backend/app/routes/books.py`의 `_quotations_payload(book_id)`가 그 책이 낀 쌍만 골라 반환한다. 구약 권 요청은 방향 `quotedBy`("이 책을 인용한 신약"), 신약 권 요청은 `quotes`("이 책이 인용한 구약")로 라벨링하고, 상대편 책별 집계(`books: [{bookId, nameKo, count}]`, 정경순)와 쌍별 본문(`pairs: [{counterpartBookId, nt:{rangeLabel,verses}, ot:{rangeLabel,verses}, note?}]`)을 함께 내려준다. 절 본문은 `bible_verses()` 정본 사전에서 합성.
- **프론트**: `SidePanel.jsx`의 Book 섹션 "인용 관계"(0건 권은 섹션 미렌더, 기본 접힘) — 상대 책별 pill 필터(`quoteFilter`) + 쌍 목록(신약↔구약 range label 행, 클릭 시 `renderQuoteLayer()`가 `VerseLayer`로 인용문(신약)/원문(구약) 2단 대조를 연다, §11).

### 16. 인장(상징물 선화) 시스템 — 책 (`bookSymbols.jsx`, ADR-0025, task#208)

`frontend/src/bookSymbols.jsx`는 성경 66권의 상징 선화(stroke-only SVG) 정본이다. 규격·`pathLength=1` 드로인 전제는 `personSymbols.jsx`(§12)와 동일 — 두 파일은 자매 모듈이며 인물 인장의 "책판"에 해당한다.

- export: 기본 `BookSymbol({bookId, size, draw, delayMs, style})`. 키는 책 `theographic_id`(책은 slug가 없어 인물 인장과 달리 id로 직접 키잉).
- 사용처 2곳: `BibleOverviewView.jsx`(둘러보기 카드, 소형) · `SidePanel.jsx`의 Book 헤더(책 상세 히어로, 노드 변경 시 `key` 리마운트로 1회 draw-on — §4 헤더 렌더 참조).

## 데이터 흐름 (엔드투엔드)

1. **원천**: theographic 원본은 `robertrouse/theographic-bible-metadata` GitHub raw JSON에서 fetch(`load_theographic.py`·`load_books.py`·`build_verse_persons.py`). 저작/보정/콘텐츠 데이터는 `data/` 하위 JSON에 손으로/`generate_*` 스크립트로 작성. 파생 정본은 `build_*` 스크립트로 산출.
2. **적재**: `load_*` 스크립트가 Neo4j에 노드/관계를 `MERGE`로 멱등 적재(가족 폐포 wip 규칙은 §1, 어머니 간선은 `load_authored_mothers.py`). `inject_*` 스크립트가 기존 노드에 속성을 `SET`. `apply_event_dedupe.py`가 중복 이벤트를 실삭제(ADR-0016).
3. **런타임 머지**: API가 Neo4j 조회 + 런타임 오버레이(`data/book_events`, `data/event_verses`, `data/bible`, `data/chapter_summaries`, `data/chapter_sections`, `data/quotations`, `data/word_distribution.json`, `data/verse_persons`, `data/person_events`, `data/person_relations`, `data/person_slugs`, `data/keypeople*`, `data/person_context`, `data/tours`, `data/god_reliance`)를 합쳐 JSON 반환.
4. **소비**: 프론트가 `/api/*`를 fetch해(모든 요청에 캐시 무력화용 `?v=<BUILD_ID>` 부착) 렌더.

## 노드 provenance 모델 (authored vs theographic originals vs runtime overlays)

그래프에 상주하는 노드는 출처(provenance)에 따라 두 부류로 나뉘고, 세 번째 부류는 아예 그래프에 넣지 않는다.

- **theographic originals** — `load_theographic.py`가 GitHub theographic JSON을 fetch해 각 레코드의 `id`를 `theographic_id`로 `MERGE`한 노드. Person은 publish분 + 가족 폐포 wip분(`status="wip"` 마킹), 나머지 라벨은 publish만. `theographic_id`는 `recXXXX` 형태의 원본 레코드 id 문자열이다.
- **authored 노드** — `data/authored_events/events.json`, `data/authored_persons/people.json`, `data/person_events/*.json`, `data/verse_events/events.json`에 손으로 작성한 노드를 `load_authored_events.py`·`load_authored_persons.py`·`load_person_events.py`·`load_verse_events.py`가 `MERGE ... SET authored = true`로 적재. `theographic_id`는 `authored-*` 슬러그 문자열. **ADR-0021·0022 이관 이후 authored Person은 `authored-person-elijah`·`authored-person-daniel` 2명만 남았다.**
- **runtime overlays** — 그래프 노드로 만들지 않고 API가 요청 시 파일로 읽는 JSON(위 §3). tours가 대표(ADR-0011 event-reference 오버레이). `god_reliance`·`quotations`도 동형(quotations는 Event/Person이 아닌 책 자체에 대한 절 대 절 관계라 애초에 그래프 모델에 대응하는 개체가 없다).

이 외에 **속성 주입 오버레이**가 있다. 그래프 노드는 이미 존재하고, `inject_*` 스크립트가 별도 JSON을 읽어 노드 속성만 `SET`한다: `inject_ko_names.py`(`data/names_ko/*.json` → `nameKo`/`aliasesKo`), `inject_book_context.py`, `inject_place_context.py`, `inject_person_context.py`(`data/person_context/people.json` → `role`/`intro`/`verses` — ADR-0027로 가계도 폐포 전원 ~1,060명 2단 저작: 서사 인물은 role+intro+구절, 족보 단역은 role 한줄+구절. `validate_person_context.py`가 최소 86명·role ≤80자·intro 선택 규칙을 검증), `inject_person_traits.py`, `inject_date_corrections.py`(아래). 이들은 런타임 오버레이와 달리 결과가 그래프에 상주한다. `family.py`의 `hasIntro` 플래그와 `PersonMiniCard.jsx`의 계층 폴백 표시가 이 2단 계층의 소비처다.

### 족보 저작 보충 (ADR-0019 → ADR-0021 이관)

`data/authored_persons/genealogy.json`은 마태복음 1장 아브라함→예수 단일 사슬(`chain`)이다. ADR-0021 가족 폐포 적재 이후 사슬 전 인물이 theographic 실레코드가 되어 사슬엔 authored 노드가 남지 않는다. 마태1이 생략한 실제 세대는 `inserted: true`로 실혈통에 삽입된다. `load_authored_genealogy.py`가 연속 쌍에 `PARENT_OF`/`CHILD_OF`를 양방향 `MERGE`한 뒤 사슬 무단절을 자체 검증한다. `load_theographic.py` 재적재 후엔 이 스크립트(그리고 `load_authored_mothers.py`)를 반드시 재실행해야 한다.

## date_corrections 교정 오버레이 + inject 패턴 (ADR-0014)

theographic 원본은 Ussher형 연대계라 저작 레이어(보수 연대계)와 충돌하는 연대를 가진다. 이를 **원본을 직접 덮어쓰지 않고** 별도 교정 테이블로 다루는 것이 date_corrections 패턴이다.

- 데이터: `data/date_corrections/events.json`, `data/date_corrections/persons.json`.
- 주입: `backend/scripts/inject_date_corrections.py`가 매칭 Event/Person 노드에 `startDate`/`sortKey`(events) 또는 지정 `field`(persons)를 `SET`한다.
- **에코 필드 멱등성**: 각 항목의 에코 필드(events: `title`/`oldStartDate`, persons: `name`/`oldValue`)가 DB 현재값과 일치할 때만 교정하고, 이미 `new*`면 조용히 통과, 불일치면 스킵+경고.
- **재실행 규칙**: `load_theographic.py`로 원본을 재적재하면 교정이 되돌아가므로 실행 시마다 `inject_date_corrections.py`를 반드시 재실행해야 한다. 이상 검출 보조 스크립트로 `backend/scripts/validate_event_chronology.py`.

## 엔트리 포인트 요약

- 백엔드 앱: `backend/app/main.py`(FastAPI, lifespan 인덱스, 12개 라우터 include).
- Neo4j 드라이버: `backend/app/db.py`(`get_driver` 싱글턴).
- 오버레이 로더: `backend/app/overlays.py`(캐시 로더 9종 + `curated_person_id`).
- 프론트 앱: `frontend/src/main.jsx`(테마 동기 반영 → createRoot) → `frontend/src/App.jsx`(SpineHeader + 8스테이지 분기). HTML 진입 `frontend/index.html`.
- 프론트 API 클라이언트: `frontend/src/api.js`(빌드 버전 쿼리는 `frontend/vite.config.js`의 `define.__BUILD_ID__`).

## 배포 위상

- 컨테이너: `docker-compose.yml` — `neo4j`(neo4j:5, 볼륨 `neo4j_data`, 127.0.0.1로만 노출), `api`(`build: ./backend`, `./data:/app/data` 마운트로 오버레이 접근), `nginx`(nginx:alpine, `frontend/dist`와 `nginx/nginx.conf` 마운트, `8080:80` 노출). API 포트는 외부 미노출 — 프론트는 nginx 프록시로만 접근.
- 백엔드 이미지: `backend/Dockerfile`(python:3.12-slim, `uvicorn app.main:app --host 0.0.0.0 --port 8000`). 의존성 `backend/requirements.txt`(fastapi / neo4j / uvicorn).
- 리버스 프록시: `nginx/nginx.conf` — `location /api/` → `http://api:8000/`, 정적 자산 장기 캐시(immutable), `location /` SPA 폴백(`try_files $uri /index.html`), `index.html`은 no-cache.
- 배포 스크립트: `deploy.sh` — 프론트 빌드(빌드 시점에 `__BUILD_ID__`가 새로 박힘) → api 이미지 빌드 → `docker compose -p biblemap up -d api nginx` → `inject_ko_names.py` 재주입(Neo4j 준비까지 최대 15회 재시도). `load_*` 스크립트는 실행하지 않는다. CI는 `.github/workflows/deploy.yml`(self-hosted 러너, `main` push 시 `git reset --hard origin/main` 후 `deploy.sh` 실행).
