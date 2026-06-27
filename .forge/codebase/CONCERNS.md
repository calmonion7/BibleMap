---
last_mapped_commit: 08842f8ee93eb806810a214fe493a1f7a5f1427e
mapped: 2026-06-27
---

# CONCERNS — 기술 부채 · 버그 · 보안 · 성능 · 취약 영역

현재 워킹트리(HEAD `08842f8`, 일부 미커밋) 기준으로 전수 재검증했다. task 85(죽은 `GET /books` + `approx_years()` 제거)·task 86(Vite 템플릿 잔재 제거, 미커밋)을 반영하여 해소된 것과 여전히 열린 것을 함께 기록한다.

---

## 1. 최근 해소된 항목 (현재 코드로 검증 완료)

### 1.1 죽은 `GET /books` 엔드포인트 + `approx_years()` 헬퍼 — 해소 (task 85)
`backend/app/routes/books.py`에는 이제 `GET /books-overview`(`books.py:9`~`30`) 하나만 남았다. `backend/app/overlays.py`도 `book_events_raw()`(`overlays.py:30`~`33`) + `event_verses()`(`overlays.py:36`~`39`) 둘만 남고 `approx_years()` 류 고아 헬퍼는 없다. 책-사건 오버레이는 이제 `/events`가 `_compute_events()`에서 머지해 실어 보낸다(`backend/app/routes/events.py:53`~`95`, `_load_approx_book_index()`가 `book_events_raw()`를 역방향 인덱싱).

### 1.2 Vite 템플릿 죽은 잔재 — 해소 (task 86, 미커밋)
과거 "데드 템플릿 잔재" 우려는 워킹트리에서 제거됐다(`frontend/src/assets/{hero.png,react.svg,vite.svg}`, `frontend/public/icons.svg` 삭제, `index.css` 미사용 규칙/변수 제거, 불필요 `export`(`API_BASE`·`selectedNodeRef`) 정리). 단 이 정리는 아직 미커밋 상태(`git status`상 `D`/`M`)라 봉인 전이다.

### 1.3 MapView 단일 파일 과부하 — 해소 (task 77~81)
`frontend/src/MapView.jsx`(193줄)는 React 컴포넌트만 남고, 지오/라벨 계산(`mapGeo.js`), 소스·레이어·핸들러(`mapLayers.js` 314줄), 링/스파이더 컨트롤러(`mapRingController.js` 163줄)로 분리됐다. 남은 미세 부채: `setupMapSources`가 4종 소스 + 11개 레이어를 한 함수에 직렬 등록(`mapLayers.js:133`~`314`)하고, places-circle/place-spider-circle 페인트가 거의 중복(`mapLayers.js:148`~`171` vs `224`~`245`)이다.

### 1.4 클러스터 클릭 멈춤 / 팝업 XSS / clusterRadius 불일치 — 해소
- 클러스터 클릭 핸들러가 `await getClusterExpansionZoom` + `zoom != null` 가드(`mapLayers.js:96`~`100`). MapLibre 5.24(`frontend/package.json`)에서 동기 콜백 버그 없음.
- 팝업 라벨은 `escapeHtml`로 이스케이프(`mapLayers.js:5`~`7`, 사용처 `:21`). place-circle/place-spider 두 경로 공통.
- 클러스터 소스는 `clusterRadius: 18`(`mapLayers.js:144`) + `clusterMinPoints: 4`(`:145`) + `clusterMaxZoom: 13`(`:143`)로 코드와 retro가 일치한다.

### 1.5 places 좌표 float 변환 무가드 — 백엔드측 해소
`backend/app/routes/nodes.py:95`~`99`가 `float(...)`를 `try/except (TypeError, ValueError)`로 감싸 파싱 불가 좌표면 `continue`한다. 프론트 `mapGeo.js`는 백엔드가 이미 거른 `p.lng/p.lat`를 그대로 쓰므로(`mapGeo.js:8` 등) 추가 가드가 없어도 현재는 안전.

---

## 2. 열린 항목 — 결정 필요

### 2.1 testament 값 표기 불일치 (OT/NT vs 구약/신약)
`BibleOverviewView.jsx`가 영문(`OT`/`NT`)·한글(`구약`/`신약`) 두 표기를 모두 방어적으로 매핑한다(`frontend/src/BibleOverviewView.jsx:137`). 둘 다 아니면 `key = null`로 그 책이 조용히 누락된다(`:138`). 백엔드(`backend/app/routes/books.py:21`)는 `props.get("testament")`를 그대로 전달 — 표준화 지점이 없다. 데이터 적재 시 한 표기로 정규화하는 것이 정공법.

### 2.2 문서 드리프트 — CONTEXT.md의 Book Events 용어가 죽은 `/books`를 가리킴
도메인 용어집 `.forge/CONTEXT.md`의 "Book Events" 항목이 아직 "…`/books` 엔드포인트가 런타임에 오버레이해…"라고 서술한다. 그러나 task 85에서 `GET /books`는 제거됐고, 실제로는 `/events`가 각 사건에 책 목록을 실어 보낸다(`backend/app/routes/events.py:84`·`:95`). 코드와 용어집이 어긋난 상태(이 매핑에서 CONTEXT.md는 수정하지 않음 — 드리프트만 기록).

---

## 3. 보안

### 3.1 인증·레이트리밋 없음
모든 라우트(`backend/app/routes/` 4파일)가 무인증 공개이고 레이트리밋·요청 제한이 없다. nginx도 인증/limit_req 지시어 없음(`nginx/nginx.conf`). 단일 사용자/내부 도구 전제면 수용 가능하나, 외부 노출 시 위험.

### 3.2 CORS 와일드카드
`backend/app/main.py:25`~`31` — `allow_origins=["*"]`. `allow_credentials=False`·`allow_methods=["GET"]`로 범위는 좁다(GET 전용·쿠키 미허용). 읽기 전용 API라 실질 위험은 낮으나, 운영 시 오리진 명시가 낫다.

### 3.3 Cypher f-string 주입 — 현재는 안전(주의 유지)
LIMIT/슬라이스 값을 f-string으로 쿼리에 삽입하는 곳이 있다: `backend/app/routes/search.py:27`(`LIMIT {SEARCH_LIMIT}`), `backend/app/routes/nodes.py:169`(`[0..{NODE_NEIGHBOR_LIMIT}]`). 두 값 모두 모듈 상수(`search.py:6` `SEARCH_LIMIT=20`, `nodes.py:7` `NODE_NEIGHBOR_LIMIT=50`)라 현재 주입 위험은 없다. 인덱스 생성도 `label`이 코드 리스트 상수라 안전(`main.py:14`~`18`). 사용자 입력(`q`, `node_id`)은 전부 파라미터 바인딩($q/$id)이다. 향후 이 상수들이 요청 인자로 바뀌면 즉시 취약해지므로 패턴 자체를 위험 신호로 표시.

---

## 4. 성능

### 4.1 lru_cache 메모리 — event_verses 8MB 상주
`backend/app/overlays.py:36`~`39` `event_verses()`는 `@functools.lru_cache(maxsize=1)`로 `data/event_verses/events.json`을 통째로 메모리에 올린다. 실측 파일 크기 약 8.3MB(`data/event_verses/events.json`, 8,344,587 bytes). 파싱된 dict는 더 커진다. 단일 워커에선 한 번 로드되어 상주하나, 워커가 늘면 워커당 사본만큼 곱해진다. `events.py`의 `_load_approx_book_index()`·`_compute_events()`도 각각 `lru_cache(maxsize=1)`로 Neo4j 결과를 앱 재시작까지 메모리 보관(`events.py:11`·`:53`) — 데이터 갱신 시 무효화 경로가 없어 재시작 필요.

### 4.2 코드 스플리팅 — 부분 적용
`frontend/vite.config.js:10`~`16`의 `manualChunks`가 `maplibre-gl`을 `maplibre` 청크로, 나머지 node_modules를 `vendor`로 분리한다. 그러나 앱 코드의 라우트/뷰 단위 lazy-load는 없다 — `MapView`/`TimelineView`/`BibleOverviewView`가 `App.jsx:3`~`6`에서 정적 import이라 초기 번들에 함께 들어간다(`React.lazy`/`Suspense` 미사용).

### 4.3 gzip/압축 없음
`nginx/nginx.conf`에 `gzip` 지시어가 전혀 없다(grep 0건). 정적 자산 캐시 헤더(`max-age=31536000, immutable`)는 있으나(`nginx.conf:25`~`28`), 전송 압축이 빠져 maplibre·vendor 청크가 비압축 전송된다.

### 4.4 단일 uvicorn 워커
`backend/Dockerfile:6` CMD가 `uvicorn app.main:app --host 0.0.0.0 --port 8000` — 워커 수 미지정(기본 1). 동시성/장애 격리가 단일 프로세스에 묶임. 4.1의 8MB 캐시 때문에 워커 증설은 메모리 곱셈 트레이드오프가 있다.

### 4.5 검색 인덱스 부재 (nameKo/name)
`backend/app/routes/search.py:16`~`27` — `n.nameKo CONTAINS $q OR toLower(n.name) CONTAINS toLower($q)`로 전체 노드 스캔 후 `n.theographic_id IS NOT NULL`로 필터. `lifespan`이 생성하는 인덱스(`main.py:13`~`18`)는 라벨별 `theographic_id` 전용이고, `nameKo`/`name`에는 인덱스가 없다. substring 매칭은 그 인덱스로 가속되지 않아 데이터가 커지면 검색이 느려진다. Neo4j 풀텍스트 인덱스(nameKo/name) 도입이 정공법.

---

## 5. 취약/주의 영역 (런타임 거동)

### 5.1 클러스터 vs 겹친 개별 점 — 줌·반경 경계 거동
`MapView.jsx`의 selection effect는 primary 선택 시 `maxZoom: 7`(`MapView.jsx:142`), 인물/집단은 `maxZoom: 10`(`:149`)으로 fitBounds한다. 클러스터 소스의 `clusterMaxZoom`은 13(`mapLayers.js:143`)이라 fitBounds 후에도 줌이 13 이하면 마커가 클러스터로 묶일 수 있다. 클러스터 클릭은 `getClusterExpansionZoom` 줌으로 easeTo(`mapLayers.js:96`~`100`)하지만, `places-circle` 클릭 시 같은 점에 2개 이상 겹치면 스파이더화(`mapLayers.js:32`~`37`)로 분기한다. 즉 "클러스터(4개+)" vs "겹친 개별 점(4개 미만→스파이더)" 두 해소 경로가 `clusterRadius: 18`+`clusterMinPoints: 4`+`clusterMaxZoom: 13`(`mapLayers.js:143`~`145`) 조합에 따라 미묘하게 갈린다.

### 5.2 자동 펼침 moveend 폴백 타이머
검색·사이드패널로 primary를 선택하면 fitBounds 후 `moveend`에서 링을 펼친다. 카메라가 안 움직이면 `moveend`가 미발화하므로 700ms 폴백 타이머로 보장한다(`MapView.jsx:121`~`142`). `fired` 단발 가드(`:126`~`134`)·언마운트 정리(`:157`~`161`)는 있으나, 타이밍 의존 로직이라 회귀에 취약(retro에서 task 15·radial-ring 이슈로 언급).

### 5.3 공유 GeoJSON 소스 동시 setData
링/스파이더가 `event-ring-source`·`place-spider-source`를 requestAnimationFrame 루프에서 setData한다(`mapRingController.js:31`·`:63`·`:89`·`:144`). selection effect와 클릭 핸들러가 같은 소스를 건드릴 수 있어, 컨트롤러가 `destroyed`/`expandAbortCtrl`/단발 가드로 충돌을 막는다. 가드는 촘촘하나, 상태가 클로저+ref 공유(`expandedPlace`를 컴포넌트와 컨트롤러가 공유 — `mapRingController.js:10`, `MapView.jsx:17`·`:43`·`:48`)라 추론 난이도가 높은 영역.

### 5.4 lru_cache된 파생 결과의 데이터 갱신 무효화 부재
`events.py`의 `_load_approx_book_index()`/`_compute_events()`(`events.py:11`·`:53`)와 `overlays.py`의 두 로더가 모두 `lru_cache(maxsize=1)`라, Neo4j나 오버레이 JSON을 갱신해도 프로세스 재시작 전에는 반영되지 않는다. 데이터가 빌드타임 고정이라는 전제(ADR-0003)에 의존하는 설계이며, 런타임 갱신 시나리오가 생기면 함정이 된다.

---

## 6. 데이터 파이프라인 · 외부 의존

### 6.1 적재/생성 스크립트 실행 순서 미문서화
`backend/scripts/`에 적재(`load_*.py` 5개)와 생성·주입(`generate_*.py`/`inject_*.py` 다수)이 있으나, `README.md:20`~`21`은 `load_theographic.py` → `inject_ko_names.py` 두 단계만 기술한다. `load_books`/`load_person_events`/`load_verse_events`/`load_authored_events`, 그리고 `generate_*`(book_context/book_events/event_verses/verse_text 등) → `inject_*`의 의존 순서가 코드/문서 어디에도 명시돼 있지 않다. 새 환경에서 데이터를 재구축할 때 순서를 알 수 없는 운영 부채.

### 6.2 외부 서비스 의존 (빌드타임)
데이터 생성이 외부 서비스에 의존:
- theographic raw GitHub: `load_theographic.py:14`~`17`, `load_books.py:14`~`15`, `generate_event_verses.py:28`~`29`, `generate_book_context.py:22`, `generate_person_traits.py:23`~`24` 등 — `raw.githubusercontent.com/robertrouse/theographic-bible-metadata`.
- Anthropic API: `generate_book_context.py`·`generate_book_events.py`·`generate_person_traits.py` 등 — `ANTHROPIC_API_KEY` 필요(예: `generate_book_events.py:88`~`99`).
- getbible: `generate_verse_text.py`가 절 본문을 빌드타임에 getbible v2에서 받아 인라인 저장(`:2`~`4`, `:53` — 기본 urllib UA에 403을 줘서 브라우저류 UA로 우회). 런타임 호출은 없음(미리굽기, ADR-0003).

이 소스들이 사라지거나 스키마가 바뀌면 데이터 재생성이 깨진다. getbible UA 우회는 서비스 측 변경에 특히 취약.

### 6.3 `data/book_years_approx/` — 빌드타임 전용 입력(의도적 유지, 부채 아님)
`data/book_years_approx/books.json`(약 4.8KB)은 런타임 소비자가 없고, 오직 `backend/scripts/generate_book_events.py:26`만 읽는다(task 85에서 확인·유지 결정). 즉 죽은 데이터가 아니라 의도적으로 보존된 파이프라인 소스이므로 삭제 대상 부채로 보지 않는다.

---

## 7. 테스트

### 7.1 자동화 테스트 전무
`test`/`spec` 파일 검색 결과 코드 테스트 0건(node_modules 제외, `.forge/codebase/TESTING.md`만 매칭). `backend/requirements.txt`에 pytest 없음, `frontend/package.json`에 jest/vitest/cypress/playwright 없음. 회귀 검증은 수동(메모리상 Python Playwright로 localhost:8080 화면 확인). 위 5장의 타이밍·상태 공유 로직과 클러스터 임계값(`clusterRadius`/`clusterMinPoints`) 같은 거동, 그리고 testament 정규화 누락(2.1) 같은 조용한 실패가 테스트 없이 회귀에 노출돼 있다(과거 `clusterRadius: 18` 유실 사례가 이를 방증).
