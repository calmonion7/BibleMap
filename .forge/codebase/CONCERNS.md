---
last_mapped_commit: 3837b4f9339ed2efb82a6b72cc1124a3340e2b9c
mapped: 2026-06-27
---

# CONCERNS — 기술 부채 · 버그 · 보안 · 성능 · 취약 영역

HEAD `3837b4f`(task 87·88·89 — 지도뷰 인물 우선 2단계 모델 재설계) 기준으로 전수 재검증했다. 재설계로 검색 UI가 제거되고 인물 허브(`PersonHub.jsx`)·여정선(`/person/{id}/journey`)·장소→인물 점프(`/place/{id}/curated-persons`)가 추가됐다. 직전 맵(`08842f8`)에서 해소·유지된 항목은 갱신하고, 재설계가 새로 만든 부채를 추가했다.

---

## 0. 데이터 결함 (최우선)

### 0.1 `abraham.json` sortKey 역순 — 여정선이 하란→우르로 뒤집힘
`data/person_events/abraham.json`에서 "우르 부르심"(`sortKey: -2091`)과 "하란 출발"(`sortKey: -2091.5`)이 역순이다. 역사적 순서는 우르→하란이나, `-2091.5 < -2091`이므로 오름차순 정렬 시 하란 출발이 우르 부르심보다 **먼저** 온다. 이 재설계에서 이 결함은 단순 사건 목록을 넘어 **여정선에 직접 반영**된다:
- `backend/app/routes/journey.py:39`가 `sorted(events, key=lambda e: e["sortKey"])`로 정렬해 stops를 만들고,
- `frontend/src/mapGeo.js:105`~`133`의 `buildJourneyLineGeoJSON`이 그 순서대로 좌표를 이어 LineString을 그린다.
결과적으로 아브라함 여정선과 정차지 배지 순번이 하란→우르로 뒤집혀 표시된다. 코드는 sortKey대로 정확히 렌더 — **데이터 교정(sortKey 부호/값 수정)이 정공법**. 코드 회피책(예: 동일 startDate 내 보조 정렬)은 권위 데이터 오염을 가린다.

---

## 1. 재설계가 새로 만든 부채 (task 87·88·89)

### 1.1 죽은 `/search` 백엔드 엔드포인트 — 프론트 소비자 소멸
재설계로 검색 UI가 제거되며 `frontend/src/useSearch.js`가 삭제됐고, 프론트 어디에서도 `/search`를 호출하지 않는다(`grep /search frontend/src` 0건). 그러나 백엔드 `backend/app/routes/search.py`는 그대로 남고 `backend/app/main.py:34`가 여전히 라우터를 등록한다. 즉 무인증 공개 상태로 살아 있는 죽은 엔드포인트다. 제거(또는 의도적 보존이면 명시) 대상. (직전 맵의 3.3·4.5에서 다루던 Cypher f-string 주입/인덱스 부재 우려도 이제 이 죽은 경로에 한정된다.)

### 1.2 `_ERA`/`_NAME_KO` 상수 중복 선언
큐레이션 13인의 `slug→era`·`slug→한글이름` 매핑이 두 곳에 통째로 복제돼 있다: `backend/app/routes/persons.py:16`~`47`와 `backend/app/routes/places.py:16`~`46`(places.py 주석은 "단방향 참조를 피하기 위해 여기서 재선언"이라 의도적이라 밝힘). `backend/app/routes/journey.py:13`은 반대로 `from .persons import _ERA, _NAME_KO`로 가져온다. 즉 같은 권위 데이터가 한 곳은 import, 한 곳은 복제로 갈려 있어, 13인 추가/이름 변경 시 두 파일을 동기화해야 하는 조용한 드리프트 위험. `_ERA_ORDER`도 `persons.py:50`·`places.py:48`·`PersonHub.jsx:7`(주석으로 "persons.py와 동일") 3곳에 중복.

### 1.3 좌표 dedup 로직 3중 복제
"좌표 있는 stop을 좌표키로 중복 제거" 로직이 세 곳에 거의 동일하게 재구현돼 있다: `frontend/src/mapGeo.js:138`~`149`(`buildJourneyStopsGeoJSON`, 권위), `frontend/src/MapView.jsx:176`~`185`(activeStopIdx→stop 역인덱싱), `frontend/src/JourneyList.jsx:21`~`31`(배지 seq→deduped 인덱스). 셋이 같은 `coKey`/`seen`/`dedupedMap` 패턴을 손으로 맞춰야 일치하며(주석도 "동일 로직"이라 명시), 한 곳만 바뀌면 리스트·맵·활성 강조의 인덱스가 어긋난다. 단일 헬퍼 추출이 정공법.

### 1.4 journey 엔드포인트 무캐시 — 매 요청 13파일 파싱
`backend/app/routes/journey.py`의 `_build_id_to_slug()`(`:18`)와 `_load_events()`(`:33`)에 `lru_cache`가 없다. `/person/{id}/journey` 호출마다 `_build_id_to_slug`가 13개 person_events JSON을 열어 파싱해 역매핑을 재구성한다. `persons.py:53`의 `_build_list`·`places.py:51`의 `_place_to_persons`는 캐시하는데 journey만 빠져 일관성·성능 양쪽에서 부채. (빌드타임 고정 데이터 전제 ADR-0003 하에선 캐시가 안전.)

### 1.5 `_place_to_persons` 무한 lru_cache
`backend/app/routes/places.py:51` `@functools.lru_cache(maxsize=None)` — `/place/{place_id}/curated-persons` 호출의 distinct place_id마다 캐시 항목이 무한 증가한다. place_id는 사용자 클릭으로 결정되는 외부 입력(theographic_id)이라, 이론상 존재하는 모든 Place 수만큼 캐시가 자랄 수 있다(현재 데이터 규모에선 작지만 패턴이 무경계). `exclude` 쿼리는 캐시 밖에서 필터링하므로(`:90`~`92`) 캐시 키 폭발은 없으나 maxsize=None은 명시 상한이 낫다.

---

## 2. 직전 항목의 현 상태 (재검증)

### 2.1 testament 값 표기 불일치 (OT/NT vs 구약/신약) — 여전히 열림
`frontend/src/BibleOverviewView.jsx`가 영문(`OT`/`NT`)·한글(`구약`/`신약`) 둘 다 방어적으로 매핑하고, 둘 다 아니면 그 책이 조용히 누락된다. 백엔드(`backend/app/routes/books.py`)는 `testament`를 그대로 전달 — 표준화 지점 없음. 적재 시 한 표기로 정규화가 정공법. (개요 화면은 이제 허브에서 "성경 책 둘러보기"로 진입 — `App.jsx:94`·`PersonHub.jsx:245`.)

### 2.2 MapView 분리 구조 — 유지, 미세 중복 잔존
`frontend/src/MapView.jsx`(227줄)는 React만 남고 지오/라벨(`mapGeo.js`), 소스·레이어·핸들러(`mapLayers.js`), 링/스파이더(`mapRingController.js`)로 분리된 구조가 유지된다. `setupMapSources`가 여정 3소스(`journey-line`/`journey-stops`/`journey-active`, `mapLayers.js:148`~`216`)를 포함해 더 많은 소스·레이어를 한 함수에 직렬 등록하는 점, places-circle/place-spider 페인트 근접 중복은 그대로.

### 2.3 places 좌표 float 변환 — 백엔드측 가드 유지
`backend/app/routes/nodes.py:95`~`99`가 `float(...)`를 `try/except (TypeError, ValueError)`로 감싸 파싱 불가 좌표면 `continue`. 신규 `journey.py:65`~`69`도 `float(lng) if lng is not None`로 None 가드 후 변환. 프론트는 백엔드가 거른 좌표만 쓰므로 안전.

---

## 3. 검증 함정 (방법론 부채)

### 3.1 백엔드 hot-reload 아님 — 정적검증이 못 잡는 클래스
`backend/Dockerfile:6` CMD에 `--reload`가 없다. 신규/변경 엔드포인트(`/person/.../journey`, `/place/.../curated-persons`, `/persons/curated`)는 `docker compose up -d --build api` 후 **실엔드포인트 호출로만** 검증된다. 워크플로의 정적검증(AST/build)은 런타임·렌더루프·데이터 버그를 못 잡는다. 실증: 직전 사이클에서 SidePanel `onNodeLoaded`가 인라인 화살표라 매 렌더 새 ref→`/node` fetch effect 재실행→`setCollapsed({})` 섹션 펼침 리셋 버그가 **런타임에서만** 드러났고 `useCallback`으로 수정됨(`App.jsx:77`~`83`, `useNodeSelection.js:13`). 0.1의 여정선 역순도 build/AST로는 안 보이고 화면에서만 드러나는 부류.

### 3.2 프론트 :8080은 dist 마운트(HMR 아님)
프론트 검증 전 `cd frontend && npm run build` 필요(`.env.production`의 `VITE_API_URL=/api`). 빌드 없이 소스만 고치면 :8080에 반영 안 됨(프로젝트 메모리 기록).

---

## 4. 보안

### 4.1 인증·레이트리밋 없음
모든 라우트(`backend/app/routes/` 7파일: nodes/events/search/books/persons/journey/places)가 무인증 공개이고 레이트리밋·요청 제한이 없다. nginx(`nginx/nginx.conf`)도 인증/limit_req 없음. 단일 사용자/내부 도구 전제면 수용 가능하나 외부 노출 시 위험. 1.1의 죽은 `/search`도 이 표면에 포함.

### 4.2 CORS 와일드카드
`backend/app/main.py:25`~`31` — `allow_origins=["*"]`. `allow_credentials=False`·`allow_methods=["GET"]`로 범위는 좁다(GET 전용·쿠키 미허용). 읽기 전용 API라 실질 위험은 낮으나 운영 시 오리진 명시가 낫다.

### 4.3 Cypher f-string 주입 — 현재는 안전(주의 유지)
LIMIT/슬라이스 값을 f-string으로 삽입하는 곳: `backend/app/routes/search.py:27`(`LIMIT {SEARCH_LIMIT}`, 단 1.1로 죽은 경로), `backend/app/routes/nodes.py`의 이웃 슬라이스 상수. 모두 모듈 상수라 현재 주입 위험 없음. 사용자 입력(`q`, `node_id`, `place_id`, `person_id`)은 전부 파라미터 바인딩($q/$id/$ids). 인덱스 생성도 `label`이 코드 리스트 상수(`main.py:14`). 이 상수들이 요청 인자로 바뀌면 즉시 취약 — 패턴 자체를 위험 신호로 표시.

---

## 5. 성능

### 5.1 lru_cache 메모리 — event_verses 8.3MB 상주
`backend/app/overlays.py`의 `event_verses()`가 `@functools.lru_cache(maxsize=1)`로 `data/event_verses/events.json`을 통째로 메모리에 올린다(실측 8,344,587 bytes, 파싱 dict는 더 큼). 단일 워커에선 한 번 로드되나 워커가 늘면 워커당 사본만큼 곱해진다. `events.py`의 `_load_approx_book_index()`·`_compute_events()`·`_book_name_map()`도 각각 `lru_cache(maxsize=1)`로 Neo4j 결과를 앱 재시작까지 보관(`events.py:11`·`:53`·`:98`) — 갱신 무효화 경로 없어 재시작 필요(5.4 연계).

### 5.2 코드 스플리팅 — 부분 적용
`frontend/vite.config.js`의 `manualChunks`가 `maplibre-gl`을 `maplibre` 청크로, 나머지 node_modules를 `vendor`로 분리한다. 그러나 라우트/뷰 단위 lazy-load는 없다 — `MapView`/`TimelineView`/`BibleOverviewView`/`PersonHub`/`JourneyList`가 `App.jsx:3`~`8`에서 정적 import이라 초기 번들에 함께 들어간다(`React.lazy`/`Suspense` 미사용). maplibre 청크는 ~1MB로 >500kB 빌드 경고 대상(code-splitting됨).

### 5.3 gzip/압축 없음
`nginx/nginx.conf`에 `gzip` 지시어가 전혀 없다(grep 0건). 정적 자산 캐시 헤더는 있으나 전송 압축이 빠져 maplibre·vendor 청크가 비압축 전송된다.

### 5.4 단일 uvicorn 워커 + 캐시 무효화 부재
`backend/Dockerfile:6` CMD가 워커 수 미지정(기본 1). 동시성/장애 격리가 단일 프로세스에 묶임. 5.1의 8.3MB 캐시 때문에 워커 증설은 메모리 곱셈 트레이드오프. 또한 `events.py`/`overlays.py`/`persons.py`/`places.py`의 lru_cache된 파생 결과가 Neo4j·오버레이 JSON 갱신을 프로세스 재시작 전엔 반영하지 않는다(빌드타임 고정 전제 ADR-0003에 의존 — 런타임 갱신 시나리오 생기면 함정).

### 5.5 nameKo/name 풀텍스트 인덱스 부재 — 죽은 경로 한정
`backend/app/routes/search.py:16`~`27`의 substring 매칭은 `lifespan`이 만드는 `theographic_id` 인덱스(`main.py:13`~`18`)로 가속되지 않아 데이터가 커지면 느려진다. 단 1.1로 프론트 소비자가 없어 실사용 영향은 죽은 엔드포인트 안에 갇혀 있다.

---

## 6. 취약/주의 영역 (런타임 거동)

### 6.1 자동 펼침 moveend 폴백 타이머
검색·사이드패널로 primary를 선택하면 fitBounds 후 `moveend`에서 사건 링을 펼친다. 카메라가 안 움직이면 `moveend`가 미발화하므로 700ms 폴백 타이머로 보장한다(`MapView.jsx:111`~`132`). `fired` 단발 가드(`:116`~`124`)·언마운트 정리(`:147`~`151`)는 있으나 타이밍 의존 로직이라 회귀에 취약(retro에서 task 15·radial-ring로 언급).

### 6.2 공유 GeoJSON 소스 동시 setData — 여정 소스 3종 추가로 표면 확대
링/스파이더가 `event-ring-source`·`place-spider-source`를 rAF 루프에서 setData하고(`mapRingController.js`), selection effect와 클릭 핸들러가 같은 소스를 건드린다. 재설계로 `journey-line-source`/`journey-stops-source`/`journey-active-source`가 추가돼(`MapView.jsx:160`~`196`) setData 대상이 늘었다. 이들은 별도 effect(journeyStops·activeStopIdx 의존)에서 갱신돼 링/스파이더와 직접 경합하진 않으나, `expandedPlaceRef`를 컴포넌트와 컨트롤러가 클로저+ref로 공유(`mapRingController.js`·`MapView.jsx:16`·`42`~`47`)하는 추론 난도 높은 구조는 그대로.

### 6.3 activeStopIdx 인덱스 정합성 — deduped 기준 3곳 동시 의존
활성 정차지 인덱스는 "좌표 dedup 후 0-based"라는 한 가지 의미를 `mapGeo.js`(배지 seq), `MapView.jsx`(카메라 이동 대상 역인덱싱), `JourneyList.jsx`(클릭→dedupIdx)·`App.jsx:271`~`300`(모바일 미니시트는 `seq-1`로 매핑)이 각자 계산한다(1.3). dedup 규칙이 어긋나면 리스트 클릭과 맵 강조·카메라가 다른 정차지를 가리키는 조용한 불일치가 난다.

### 6.4 좌표 없는 정차지 처리 — null seq 폴백
`journey.py:100`~`128`은 좌표 있는 stop에만 1부터 seq를 부여하고 없으면 `seq=null, lng/lat=null`로 stops에 포함한다. 프론트는 이를 비활성(클릭 불가, opacity 0.45)으로 렌더하고(`JourneyList.jsx:46`~`71`) 여정선/배지에선 제외한다(`mapGeo.js:106`·`:139`). 의도된 거동이나, "표시되지만 클릭 안 되는 항목"은 발견성 함정이 될 수 있다.

---

## 7. UX 주의

### 7.1 SidePanel 섹션 기본 접힘 — 점프 칩 발견성
SidePanel 섹션은 기본 접힘이다(`SidePanel.jsx:25`~27 주석: `collapsed[key] !== false → 접힘`). 장소의 "이 곳을 지난 인물" 점프 칩(`SidePanel.jsx:533`~`554`, `/place/{id}/curated-persons` 소비)을 보려면 "이 곳을 지난 인물" 섹션을 한 번 펼쳐야 한다. 인물 전환의 핵심 동선이 기본 숨김이라 발견성 부채.

### 7.2 큐레이션 13인 외 인물 — 빈 여정
`/person/{id}/journey`는 큐레이션 13인(`persons.py:16`~30)이 아니면 404가 아니라 `stops=[]` 빈 응답을 준다(`journey.py:84`~88). 허브는 13인만 노출하므로 정상 동선에선 안 닿으나, 사이드패널 이웃 탐색으로 13인 밖 Person에 도달하면 여정선·리스트가 조용히 비는 거동.

---

## 8. 데이터 파이프라인 · 외부 의존

### 8.1 적재/생성 스크립트 실행 순서 미문서화
`backend/scripts/`에 적재(`load_*.py`)·생성·주입(`generate_*.py`/`inject_*.py`)이 있으나 `README.md`는 `load_theographic.py`→`inject_ko_names.py` 두 단계만 기술. `load_books`/`load_person_events`/`load_verse_events`/`load_authored_events`, `generate_*`(book_context/book_events/event_verses/verse_text 등)→`inject_*`의 의존 순서가 코드/문서 어디에도 없다. 새 환경 재구축 시 순서 미상의 운영 부채.

### 8.2 외부 서비스 의존 (빌드타임)
데이터 생성이 외부에 의존: theographic raw GitHub(`load_theographic.py`·`load_books.py`·`generate_event_verses.py` 등 — `raw.githubusercontent.com/robertrouse/theographic-bible-metadata`), Anthropic API(`generate_book_context.py`·`generate_book_events.py`·`generate_person_traits.py` — `ANTHROPIC_API_KEY` 필요), getbible(`generate_verse_text.py`가 절 본문을 빌드타임에 받아 인라인 저장, 기본 UA에 403→브라우저류 UA로 우회). 런타임 호출은 없음(미리굽기, ADR-0003). 소스 소멸/스키마 변경 시 재생성 깨짐 — getbible UA 우회는 특히 취약.

### 8.3 `data/book_years_approx/` — 빌드타임 전용 입력(의도적 유지, 부채 아님)
`data/book_years_approx/books.json`은 런타임 소비자가 없고 `backend/scripts/generate_book_events.py:26`만 읽는다(task 85 확인·유지). 죽은 데이터가 아니라 의도적 보존 파이프라인 소스이므로 삭제 대상으로 보지 않는다. (추정 데이터 권위 분리 — book_years_approx/book_events 등은 Neo4j 밖 런타임 오버레이로, `/events`가 `_compute_events()`에서 머지: `events.py:53`~88.)

---

## 9. 테스트

### 9.1 자동화 테스트 전무
코드 테스트 0건(`backend/requirements.txt`에 pytest 없음, `frontend/package.json`에 jest/vitest/cypress/playwright 없음). 회귀 검증은 수동(메모리상 Python Playwright로 localhost:8080 화면 확인). 6장의 타이밍·상태 공유 로직, 1.3의 dedup 3중 복제, 1.2의 상수 중복, 2.1의 testament 정규화 누락, 그리고 0.1의 데이터 정렬 버그 같은 조용한 실패가 테스트 없이 회귀에 노출돼 있다(과거 `clusterRadius: 18` 유실 사례가 이를 방증).
