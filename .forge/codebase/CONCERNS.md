---
last_mapped_commit: 14e0a78c3e0ab7fc7d960c4cabdf3eab3fc297e6
mapped: 2026-06-27
---

# CONCERNS — 기술 부채 · 버그 · 보안 · 성능 · 취약 영역

현재 워킹트리(HEAD `14e0a78`) 기준. 직전 리팩터(task 77~81)로 여러 항목이 해소되었으므로, 해소된 것과 여전히 열린 것을 함께 기록한다.

---

## 1. 최근 해소된 항목 (현재 상태 검증 완료)

### 1.1 MapView 단일 파일 과부하 — 해소
과거 "MapView.jsx 734줄 단일 파일" 우려는 분리로 해소됐다. 현재 구성:
- `frontend/src/MapView.jsx` (193줄) — React 컴포넌트(맵 생성/선택 effect/에러·noLocation UI)만 남음.
- `frontend/src/mapGeo.js` (101줄) — 순수 지오/라벨 계산(`coreBounds`, `placesToGeoJSON`, `ringPositions`, `ringLabels`, hull GeoJSON 빌더 등).
- `frontend/src/mapLayers.js` (313줄) — `setupMapSources`/`registerEventHandlers`/팝업 HTML.
- `frontend/src/mapRingController.js` (163줄) — 링/스파이더 애니메이션 컨트롤러(클로저 상태 캡슐화).

남은 미세 부채: `mapLayers.js`의 `setupMapSources`가 5종 소스 + 11개 레이어를 한 함수에 직렬 등록(`frontend/src/mapLayers.js:133`~`313`). 동작은 정상이나 레이어 정의가 길고, places/place-spider/event-ring 레이어 페인트 스타일이 거의 중복(`frontend/src/mapLayers.js:147`~`193` vs `223`~`266`)이다.

### 1.2 클러스터 클릭 멈춤 (getClusterExpansionZoom) — 해소
`places-cluster` 클릭 핸들러가 `await`로 변경됨(`frontend/src/mapLayers.js:96`~`100`). MapLibre 5.24(`frontend/package.json` `maplibre-gl: ^5.24.0`)의 `getClusterExpansionZoom`은 `Promise<number>`를 반환하므로 콜백 동기 호출 버그가 사라졌다. `zoom != null` 가드도 있다.

### 1.3 팝업 XSS — 해소
`placePopupHTML`이 `escapeHtml`로 라벨을 이스케이프한다(`frontend/src/mapLayers.js:5`~`7`, 사용처 `:21`). place-circle/place-spider 두 경로 모두 같은 함수를 쓴다.

### 1.4 clusterRadius 설정 불일치 — 해소
과거 "의도된 `clusterRadius: 18`이 커밋 누락돼 실제 코드는 `40`" 우려는 해소됐다. 현재 클러스터 소스는 `clusterRadius: 18`(`frontend/src/mapLayers.js:144`, task-76에서 18 복원)이고 `clusterMinPoints: 4`(`:145`, task-84 추가)가 함께 설정돼 있다(`clusterMaxZoom: 13`, `:143`). 즉 동일/근접 좌표 2~3개는 클러스터 대신 라벨로 표시하고 4개 이상만 클러스터된다. retro와 실제 코드의 어긋남도 사라졌다.

---

## 2. 열린 항목 — 결정 필요

### 2.1 testament 값 표기 불일치 (OT/NT vs 구약/신약)
`BibleOverviewView.jsx`가 영문(`OT`/`NT`)과 한글(`구약`/`신약`) 두 표기를 모두 방어적으로 매핑한다(`frontend/src/BibleOverviewView.jsx:135`~`137`). 둘 중 어느 쪽이든 받아주지만, 데이터 소스에 따라 값이 갈릴 수 있다는 뜻이고 둘 다 아니면 `key = null`로 조용히 누락된다. 백엔드(`backend/app/routes/books.py:22`, `:62`)는 `props.get("testament")`를 그대로 전달 — 표준화 지점이 없다. 데이터 적재 시 한 표기로 정규화하는 것이 정공법.

---

## 3. 보안

### 3.1 인증·레이트리밋 없음
모든 라우트(`backend/app/routes/`)가 무인증 공개. 레이트리밋·요청 제한 없음. 단일 사용자/내부 도구 전제라면 수용 가능하나, 외부 노출 시 위험.

### 3.2 CORS 와일드카드
`backend/app/main.py:25`~`31` — `allow_origins=["*"]`. `allow_credentials=False`, `allow_methods=["GET"]`로 범위는 좁다(GET 전용·쿠키 미허용). 읽기 전용 API라 현재 실질 위험은 낮으나, 운영 시 오리진을 명시하는 편이 낫다.

### 3.3 Cypher f-string 주입 — 현재는 안전(주의 유지)
LIMIT/슬라이스 값을 f-string으로 쿼리에 삽입하는 곳이 있다: `backend/app/routes/search.py:27`(`LIMIT {SEARCH_LIMIT}`), `backend/app/routes/nodes.py:169`(`[0..{NODE_NEIGHBOR_LIMIT}]`). 두 값 모두 모듈 상수(`search.py:6` `SEARCH_LIMIT=20`, `nodes.py:7` `NODE_NEIGHBOR_LIMIT=50`)라 현재 주입 위험은 없다. 사용자 입력(`q`, `id`)은 전부 파라미터 바인딩($q/$id)이다. 향후 이 상수들이 요청 인자로 바뀌면 즉시 취약해지므로 패턴 자체는 위험 신호로 표시.

---

## 4. 성능

### 4.1 lru_cache 메모리 — event_verses 8MB 상주
`backend/app/overlays.py:42`~`45` `event_verses()`는 `@functools.lru_cache(maxsize=1)`로 `data/event_verses/events.json`을 통째로 메모리에 올린다. 실측 파일 크기 약 8.3MB(`data/event_verses/events.json`, 8,344,587 bytes). 파싱된 dict는 더 커진다. 단일 워커에선 한 번 로드되어 상주. 워커가 늘면 워커당 사본만큼 곱해진다.

### 4.2 코드 스플리팅 — 부분 적용(과거 "없음"은 갱신됨)
`frontend/vite.config.js`에 `manualChunks`가 있어 `maplibre-gl`을 `maplibre` 청크로, 나머지 node_modules를 `vendor`로 분리한다. 앱 코드 자체의 라우트/뷰 단위 lazy-load는 없다(`MapView`/`TimelineView`/`BibleOverviewView`가 정적 import). MapLibre 청크는 별도지만 초기 번들에 함께 로드될 여지.

### 4.3 gzip/압축 없음
`nginx/nginx.conf`에 `gzip` 지시어가 전혀 없다(grep 결과 0건). 정적 자산 캐시 헤더(`max-age=31536000, immutable`)는 설정돼 있으나(`nginx/nginx.conf` 정적 location), 전송 압축이 빠져 maplibre·vendor 청크가 비압축 전송된다.

### 4.4 단일 uvicorn 워커
`backend/Dockerfile` CMD가 `uvicorn app.main:app --host 0.0.0.0 --port 8000` — 워커 수 미지정(기본 1). 동시성/장애 격리가 단일 프로세스에 묶임. 4.1의 8MB 캐시 때문에 워커 증설은 메모리 곱셈 트레이드오프가 있음.

### 4.5 검색 인덱스 부재 (nameKo/name)
`backend/app/routes/search.py:14`~`28` — `n.nameKo CONTAINS $q OR toLower(n.name) CONTAINS toLower($q)`로 전체 노드 스캔. `lifespan`에서 생성하는 인덱스(`backend/app/main.py:13`~`18`)는 `theographic_id` 전용이고, `nameKo`/`name`에는 인덱스가 없다. `WHERE ... AND n.theographic_id IS NOT NULL`도 인덱스로 가속되지 않는 substring 조건이라 데이터가 커지면 검색이 느려진다. Neo4j 풀텍스트 인덱스(nameKo/name) 도입이 정공법.

---

## 5. 취약/주의 영역 (런타임 거동)

### 5.1 fitBounds + 스파이더화 / clusterMaxZoom 경계
`MapView.jsx`의 selection effect는 primary 선택 시 `maxZoom: 7`(`frontend/src/MapView.jsx:142`), 인물/집단은 `maxZoom: 10`(`:149`)으로 fitBounds한다. 클러스터 소스의 `clusterMaxZoom`은 13(`mapLayers.js:143`)이라, fitBounds 후에도 줌이 13 이하면 마커가 여전히 클러스터로 묶일 수 있다. 클러스터 클릭은 `getClusterExpansionZoom` 줌으로 easeTo(`mapLayers.js:96`~`100`)하지만, `places-circle` 클릭 시 같은 지점에 겹친 점이 2개 이상이면 스파이더화(`mapLayers.js:32`~`37`)로 분기한다. 즉 "클러스터 vs 겹친 개별 점" 두 해소 경로가 줌·반경 조합에 따라 미묘하게 갈리며, 현재 설정(`clusterRadius: 18` + `clusterMinPoints: 4` + `clusterMaxZoom: 13`, `mapLayers.js:143`~`145`)이 이 경계 거동을 좌우한다 — 4개 미만이 근접하면 클러스터되지 않고 개별 점/라벨로 남아 스파이더화 경로로 빠진다.

### 5.2 자동 펼침 moveend 폴백 타이머
검색·사이드패널로 primary를 선택하면 fitBounds 후 `moveend`에서 링을 펼친다. 카메라가 안 움직이면 `moveend`가 미발화하므로 700ms 폴백 타이머로 보장한다(`frontend/src/MapView.jsx:121`~`142`). `fired` 단발 가드·언마운트 정리(`:157`~`161`)는 있으나, 타이밍 의존 로직이라 회귀에 취약한 구간(회고에서 task 15·radial-ring 이슈로 언급).

### 5.3 공유 GeoJSON 소스 동시 setData
링/스파이더가 `event-ring-source`·`place-spider-source`를 requestAnimationFrame 루프에서 setData한다(`frontend/src/mapRingController.js`). selection effect와 클릭 핸들러가 같은 소스를 건드릴 수 있어, 컨트롤러가 `destroyed`/`expandAbortCtrl`/단발 가드로 충돌을 막는다. 가드가 촘촘하지만 상태가 클로저+ref 공유(`expandedPlaceRef`를 컴포넌트와 컨트롤러가 공유, `mapRingController.js:10`, `MapView.jsx:17`·`:48`)라 추론 난이도가 높은 영역.

### 5.4 places 좌표 float 변환 무가드
`backend/app/routes/nodes.py:96`~`97`이 `float(props.get("latitude", 0))`/`longitude`를 한다. 쿼리 WHERE에서 `IS NOT NULL`은 거르지만(`:39` 등), 좌표가 숫자로 파싱 불가한 문자열이면 예외 가능. 현재 데이터가 정상이라는 전제에 의존.

---

## 6. 데이터 파이프라인 · 외부 의존

### 6.1 적재/생성 스크립트 실행 순서 미문서화
`backend/scripts/`에 적재(`load_*.py` 5개)와 생성(`generate_*.py`, `inject_*.py` 다수)이 있으나, README는 `load_theographic.py` → `inject_ko_names.py` 두 단계만 기술한다(`README.md:18`~`22`). `load_books`/`load_person_events`/`load_verse_events`/`load_authored_events`, 그리고 `generate_*`(book_context/book_events/event_verses/verse_text 등) → `inject_*`의 의존 순서가 코드/문서 어디에도 명시돼 있지 않다. 새 환경에서 데이터를 재구축할 때 순서를 알 수 없는 운영 부채.

### 6.2 외부 서비스 의존 (빌드타임)
데이터 생성이 외부 서비스에 의존:
- theographic raw GitHub: `load_theographic.py:14`~`17`, `generate_event_verses.py:28`~`29`, `generate_verse_events.py:18`~`20`, `generate_book_context.py:22` 등 — `raw.githubusercontent.com/robertrouse/theographic-bible-metadata`.
- Anthropic API: `generate_book_context.py:20`·`:88`, `generate_book_events.py:17`·`:99`, `generate_verse_events.py:16`·`:144` 등 — `ANTHROPIC_API_KEY` 필요.
- getbible: `generate_verse_text.py`가 절 본문을 빌드타임에 getbible v2에서 받아 인라인 저장(`:1`~`16`, `:53` — 기본 urllib UA에 403을 줘서 브라우저류 UA로 우회). 런타임 호출은 없음(미리굽기, ADR-0003).
이 소스들이 사라지거나 스키마가 바뀌면 데이터 재생성이 깨진다. getbible UA 우회는 서비스 측 변경에 특히 취약.

---

## 7. 테스트

### 7.1 자동화 테스트 전무
`test`/`spec` 파일 검색 결과 0건(node_modules 제외). 백엔드 pytest·프론트 단위/E2E 모두 없다. 회귀 검증은 수동(메모리상 Python Playwright로 localhost:8080 화면 확인). 위 5장의 타이밍·상태 공유 로직과 클러스터 임계값(`clusterRadius`/`clusterMinPoints`) 같은 거동이 테스트 없이 회귀에 노출돼 있다(과거 `clusterRadius: 18` 유실 사례가 이를 방증).
