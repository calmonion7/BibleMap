---
last_mapped_commit: 6f2cfc1bf163d7327bd86773676223624fa53ff2
mapped: 2026-06-18
---

# BibleMap 기술 부채 및 리스크

## 1. 보안 리스크

### 1-1. Cypher 쿼리 f-string 삽입 (중간)

`backend/app/routes/nodes.py` 157번째 줄:
```python
f"MATCH (n {{theographic_id: $id}})-[r]-(m) RETURN m, type(r) AS rel, labels(m) AS mlabels LIMIT {NODE_NEIGHBOR_LIMIT}",
```
`NODE_NEIGHBOR_LIMIT`은 상수(50)이라 현재는 안전하지만, f-string Cypher 패턴이 관행으로 굳으면 이후 가변값이 들어올 위험이 있다. `search.py` 15번 줄도 마찬가지(`SEARCH_LIMIT=20` 상수 f-string). 예방적으로 파라미터화하거나 Cypher 문자열 접합 패턴을 금지하는 규칙이 없다.

### 1-2. MapView 팝업 setHTML XSS (낮음)

`frontend/src/MapView.jsx` 287~304번째 줄: maplibre `Popup.setHTML()`에 Neo4j에서 받은 `label`(nameKo)이 직접 HTML 문자열로 삽입된다. 현재 데이터는 신뢰 범위지만, Neo4j 데이터가 오염되거나 XSS 페이로드가 포함되면 DOM에 직접 실행된다. `innerText`로 DOM을 구성하거나 이스케이프 처리가 없다.

### 1-3. CORS allow_origins=["*"] (낮음)

`backend/app/main.py` 25~31번째 줄: `allow_origins=["*"]`로 설정돼 있다. `allow_credentials=False`·읽기 전용 API라 현실적 위험은 작지만, 프로덕션 배포 환경에서 출처 제한이 전혀 없다. 도메인이 고정된 시점에 출처 목록을 좁혀야 한다.

---

## 2. 기술 부채

### 2-1. 동기 Neo4j 드라이버 + FastAPI (높음)

`backend/app/db.py` 전체, `backend/app/routes/` 전체: FastAPI는 `async def`를 네이티브 비동기로 실행하지만, 모든 route 핸들러가 `def`(동기)다. neo4j 파이썬 드라이버 5.x는 `AsyncGraphDatabase.driver`를 제공하지만 사용하지 않는다. 동기 핸들러는 uvicorn의 threadpool에서 실행되어 Neo4j 쿼리 블로킹이 발생하며, 동시 요청이 늘면 threadpool 포화로 응답 지연이 생긴다.

### 2-2. Neo4j 드라이버 싱글턴 — 재연결 없음 (중간)

`backend/app/db.py` 4~15번째 줄: `_driver`는 모듈 수준 전역 변수로, 최초 호출 시 한 번 생성 후 재사용된다. Neo4j 재시작·네트워크 단절 후 드라이버가 stale 상태가 되어도 재연결 로직이 없다. 서버 재시작 없이 복구할 방법이 없다. `driver.verify_connectivity()`나 헬스체크 미들웨어가 없다.

### 2-3. lru_cache 함수가 Neo4j를 초기화 시점에 호출 (중간)

`backend/app/routes/events.py` `_load_approx_book_index()` 41~88번째 줄: `@functools.lru_cache(maxsize=1)`로 캐시되지만, 내부에서 `get_driver()`를 호출해 Neo4j에 즉시 쿼리한다. 첫 번째 `/events` 요청 때만 실행되지만, 그 시점에 Neo4j가 아직 준비되지 않았으면 에러 응답을 반환한 뒤 캐시가 빈 dict로 굳어버린다(`_load_event_verses`·`_load_approx` 등 순수 파일 로드와 달리 재시도 불가). Neo4j 재시작 후 앱을 재시작하지 않으면 캐시가 비어있는 상태로 고정된다.

### 2-4. `Cache-Control: no-store` vs `lru_cache` 불일치 (낮음)

`backend/app/routes/events.py` 128, 137번째 줄, `backend/app/routes/books.py` 92번째 줄: HTTP 응답에 `Cache-Control: no-store`를 붙이면서, 서버 프로세스 내부에서는 `lru_cache`로 데이터를 영구 캐시한다. 런타임에 `data/` 파일을 교체해도 프로세스 재시작 전까지 반영되지 않는다는 점이 문서화되지 않아 운영 혼란을 야기할 수 있다.

### 2-5. Person 인물 성품 traits — Neo4j 직렬화 JSON 파싱 (낮음)

`backend/app/routes/nodes.py` 229~235번째 줄:
```python
if label_val == "Person" and "traits" in clean_props:
    import json as _json
    try:
        clean_props["traits"] = _json.loads(clean_props["traits"])
    except Exception:
        clean_props["traits"] = []
```
`traits`가 Neo4j에 JSON 문자열로 저장돼 있어 API 응답 직전에 파싱된다. `json` 모듈을 함수 내부 `import json as _json`으로 매번 가져오는 것도 불필요한 패턴이다. Neo4j에 native list로 저장하거나 적재 스크립트에서 다루는 것이 맞지만, 현재 아키텍처상 변경 비용이 크다.

### 2-6. deploy.sh `inject_ko_names` 매 배포마다 실행 (낮음)

`deploy.sh` 50~63번째 줄: `inject_ko_names.py`가 매 배포마다 재실행된다. 이 스크립트는 수천 개 노드를 Neo4j에 MERGE SET으로 써서 배포 시간을 늘린다. 한글 이름 데이터가 변경됐을 때만 실행하는 체크 없이 무조건 실행된다. 주입 15회 실패 시 배포가 중단되어 Neo4j 시작 지연(대용량 DB)이 있을 때 배포가 깨진다.

---

## 3. 변경하기 어려운 영역

### 3-1. MapView.jsx — 맵 초기화 useEffect 단일 클로저 (높음)

`frontend/src/MapView.jsx` 31~355번째 줄: 맵 초기화(`new maplibregl.Map`), 애니메이션 상태(`animFrame`, `expandAbortCtrl`, `expandedPlace`), 이벤트 핸들러(click, mouseenter 등), 링 애니메이션 함수(`collapseRing`, `expandPlace`)가 하나의 거대한 `useEffect` 클로저에 들어있다. 481줄 파일에서 이 useEffect가 31~355번째 줄을 차지(약 320줄). 애니메이션·링·이벤트 핸들러를 분리하려면 ref 공유 구조를 전면 재설계해야 한다.

### 3-2. App.jsx — selectedNode + history 상태 흐름 (중간)

`frontend/src/App.jsx`: `selectedNode`, `history`, `selectedNodeMeta`가 App 최상위에 있고 `MapView`, `TimelineView`, `SidePanel` 세 컴포넌트에 props로 전달된다. `selectNode`가 `useCallback([], [])`으로 참조를 고정하고 `selectedNodeRef`를 통해 최신값을 읽는 패턴은 동작하지만 미묘한 클로저 캡처 버그를 유발하기 쉽다. 상태 관리 라이브러리나 Context 없이 props drilling으로 유지되고 있어, 뷰가 추가되면 흐름 추적이 어려워진다.

### 3-3. TimelineView — `openGroup` 팝오버 positioning (낮음)

`frontend/src/TimelineView.jsx` 375~387번째 줄: 날짜 그룹에 여러 사건이 있을 때 "외 N건" 팝오버가 `position: absolute; left: 104; top: 100%`로 하드코딩돼 있다. 뷰포트 하단 경계 감지·overflow clipping이 없어, 타임라인 하단 사건에서 팝오버가 화면 밖으로 잘린다. `maxHeight: 200px` + `overflowY: auto`가 있지만 위치는 보정되지 않는다.

### 3-4. VERSE_MAP 하드코딩 (낮음)

`backend/scripts/generate_approx_book_verses.py` 27~98번째 줄: `book_events/books.json`의 모든 `(bookId, eventId)` 쌍이 `VERSE_MAP` 딕셔너리에 수동으로 하드코딩돼 있다. `generate_book_events.py`가 LLM으로 매핑을 재생성하면 `VERSE_MAP`이 오래된 상태가 되어 스크립트가 오류(`sys.exit(1)`)를 낸다(131~137번째 줄 검증). book_events 연결을 바꿀 때마다 VERSE_MAP도 수동으로 갱신해야 한다.

---

## 4. 성능 병목

### 4-1. `/node/{id}` — 3회 Neo4j 쿼리 + Book 5회 (중간)

`backend/app/routes/nodes.py` 134~250번째 줄: `GET /node/{id}` 응답 한 번에 최소 3개 쿼리(노드 조회, 이웃 조회, 이웃 총수)가 순차 실행되고, Book이면 추가로 `top_persons`·`top_events` 2개 쿼리가 더 붙어 5개가 된다. 모든 쿼리가 동기 블로킹이다. 이웃 총수 쿼리(`count(m)`)는 LIMIT 없이 전체 그래프를 스캔한다.

### 4-2. `/node/{id}/places` — Person·PeopleGroup 쿼리 비용 (중간)

`backend/app/routes/nodes.py` 43~50번째 줄(PeopleGroup): 집단 선택 시 `(PeopleGroup)<-[:MEMBER_OF]-(Person)`, `(Event)-[:HAS_PARTICIPANT]->(Person)`, `(Event)-[:OCCURS_AT]->(Place)` 3단 JOIN을 인덱스 없이 실행한다. 큰 집단(이스라엘 민족 등)이면 풀 탐색이 발생할 수 있다. `theographic_id` 인덱스 외에 관계 방향별 인덱스가 없다.

### 4-3. `/events` — 매 요청마다 Neo4j 쿼리 (낮음)

`backend/app/routes/events.py` 99~128번째 줄: 타임라인 전체 사건 목록을 매 요청마다 Neo4j에서 읽는다. `_load_approx_book_index()`는 캐시되지만 실제 Event 쿼리는 캐시가 없다. 사건 수가 늘어날수록 응답 크기·쿼리 시간이 함께 증가한다. `Cache-Control: no-store`로 HTTP 캐시도 막혀 있어 브라우저 재방문마다 전량 재조회된다.

### 4-4. `event_verses/events.json` 파일 크기 (낮음)

`data/event_verses/events.json`은 현재 약 130,000줄(~4MB 추정). `_load_event_verses()`가 이 파일을 프로세스 메모리에 통째로 로드해 캐시한다. 사건·구절이 늘수록 메모리 사용이 비례해 증가하고, 초기 로드 시 API 첫 응답이 지연된다.

---

## 5. 알려진 동작 불일치·잠재 버그

### 5-1. MapView 탭 전환 시 maplibre 재마운트 (중간)

`frontend/src/App.jsx` 308~323번째 줄: `activeView === 'map'` 조건부 렌더링으로 타임라인 탭으로 이동 후 지도 탭으로 돌아오면 `MapView`가 언마운트-재마운트된다. maplibre는 재초기화되어 타일을 다시 로드하고, 링 상태·줌·위치가 초기화된다. 탭 전환 비용이 높고 사용자 탐색 맥락이 소실된다. `display: none`/`visibility: hidden` 방식으로 유지하는 대신 매번 파괴하는 패턴이다.

### 5-2. `sortKey` 타입 불일치 — Event vs authored Event (낮음)

`backend/app/routes/events.py` 123번째 줄: `sortKey: float(props.get("sortKey", 0))`. theographic Event의 `sortKey`는 원래 정수이지만, `authored_events/events.json`의 authored 사건은 `63.5`, `66.0` 같은 소수점 값을 가진다. `TimelineView.jsx` `sortKeyToYear()` 함수(14~17번째 줄)는 `number`면 그대로 반환하므로 당장은 동작하지만, sortKey 기반 연도 계산이 확장될 경우 소수점 값이 예상과 다른 동작을 낼 수 있다.

### 5-3. 검색 `typeFilter` + `highlightIndex` 경계 불일치 (낮음)

`frontend/src/App.jsx` 149~163번째 줄: `handleSearchKeyDown`에서 `filteredResults`를 기준으로 키보드 인덱스를 계산하지만, `typeFilter` 칩을 클릭할 때 `setHighlightIndex(-1)` 리셋만 하고 `filteredResults.length` 변화는 다음 렌더 이후에 반영된다. 빠르게 칩 선택 후 Enter를 누르면 이전 `filteredResults` 기준 인덱스로 잘못된 항목이 선택될 수 있다.

### 5-4. Book 연도 칩 — endYear 음수 처리 (낮음)

`frontend/src/SidePanel.jsx` 174번째 줄:
```jsx
node.properties.startYear && `${Math.abs(node.properties.startYear)}BC~${Math.abs(node.properties.endYear)}BC`
```
`startYear`가 양수(AD)인 책의 경우 칩 라벨이 여전히 `BC~BC` 형식으로 표시된다. 신약 서신서 등 AD 연도 Book에서 잘못된 레이블이 렌더된다.

### 5-5. `_load_approx_book_index` 에러 시 빈 dict 반환 패턴 차이 (낮음)

`backend/app/routes/events.py` 54~55번째 줄:
```python
if not book_events:
    return {}
```
`book_events.json`을 못 읽으면 `{}`(dict)를 반환하지만 이후 `event_to_books`(dict)를 반환해야 할 함수가 `{}`를 반환한다. 정상 경로와 타입이 같아 호출부는 에러를 감지 못한 채 빈 데이터로 동작한다. 모든 사건에서 추정책 칩이 사라지지만 로그에 아무것도 남지 않는다.

---

## 6. 데이터 파이프라인 취약점

### 6-1. LLM 생성 데이터 재현 불가 (중간)

`backend/scripts/generate_book_events.py`의 Claude API 호출(`claude-haiku-4-5-20251001`)은 `temperature`를 제어하지 않아 매 실행마다 다른 결과를 낼 수 있다. `data/book_events/books.json`이 git으로 추적되어 현재 값은 고정되지만, 스크립트를 재실행하면 현재 값을 덮어쓴다. 재실행 가이드·버전 태그·검증 절차가 없어, 실수로 재실행 시 수동 데이터(`VERSE_MAP`)와의 불일치가 발생한다.

### 6-2. getbible 외부 의존 — 빌드타임 한정 (낮음)

`backend/scripts/generate_verse_text.py`는 빌드타임에 `https://api.getbible.net/v2/`에서 구절 본문을 받아 데이터에 직접 저장한다(ADR-0003). getbible API가 응답하지 않으면 본문이 `null`로 기록되고, 재실행 시 재시도된다. 그러나 null 본문이 있는 데이터가 git에 커밋되면 UI에서 "원문이 없습니다" 메시지가 표시된다. null 비율을 체크하는 CI 단계나 경보가 없다.

### 6-3. `deploy.sh` — inject_ko_names 실패가 전체 배포를 중단 (낮음)

`deploy.sh` 59~62번째 줄: 한글 이름 주입 실패 시 `exit 1`로 배포가 중단된다. Neo4j 컨테이너 시작 지연(대용량 볼륨 초기화) 때 15회 × 2초 = 30초 내에 준비되지 않으면 배포 실패가 된다. 실제로는 이미 실행 중인 컨테이너(nginx·api)는 정상이고 inject만 실패한 상황에서 롤백도 안 되고 기존 서비스도 중단되지 않는 불명확한 상태가 된다.
