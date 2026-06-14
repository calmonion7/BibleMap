---
last_mapped_commit: fb78d740df63d386e84ceb1bb4249921a5e198b7
mapped: 2026-06-14
---

# Codebase Concerns

**Analysis Date:** 2026-06-14

## Tech Debt

**`/node/{id}` 엔드포인트 — 동일 세션 내 3회 직렬 Neo4j 쿼리:**
- Issue: `get_node()`(`backend/app/routes/nodes.py:125`)가 하나의 HTTP 요청 안에서 `session.run`을 3번 순차 호출한다: 노드 조회(line 129), 이웃 조회 LIMIT 50(line 146), 전체 이웃 수 COUNT(line 167). COUNT 쿼리는 LIMIT 전체 개수를 위해 별도 쿼리로 실행된다.
- Files: `backend/app/routes/nodes.py`
- Impact: 연결이 많은 노드(예: 모세·예수)에서 3회 왕복 레이턴시가 누적된다. SidePanel·GraphView·MapView(사건 링)가 동시에 `/node/{id}`를 호출하면 9회 Neo4j 왕복이 발생한다.
- Fix approach: COUNT를 별도 쿼리 대신 `MATCH...RETURN count(m)`을 첫 번째 쿼리에 WITH로 합치거나, 이웃 쿼리에 `WITH n, count{(n)-[r]-(m)} AS total`을 추가해 단일 왕복으로 줄인다.

**`/node/{id}/places` — 무제한 결과셋 (Person·PeopleGroup):**
- Issue: Person 및 PeopleGroup 타입의 `/places` 쿼리에 LIMIT 절이 없다(`backend/app/routes/nodes.py:23-50`). 이벤트가 많은 인물이나 대형 집단을 선택하면 수백 개의 장소가 반환될 수 있다.
- Files: `backend/app/routes/nodes.py`
- Impact: 대형 PeopleGroup 선택 시 Neo4j에서 세 단계 패턴 매칭(`PeopleGroup→Person→Event→Place`)이 무제한으로 실행되고, 프론트엔드 MapView가 이를 전부 GeoJSON 마커로 렌더링한다.
- Fix approach: 쿼리 끝에 `LIMIT 200`(또는 tuneable 상수) 추가. 클라이언트에서 `seen` 셋으로 이미 중복 제거하므로 LIMIT 위치는 RETURN 절 직전.

**GraphView — `selectedNode` 변경마다 cytoscape 인스턴스 전체 재생성:**
- Issue: `GraphView.jsx`의 메인 useEffect가 `[selectedNode, onSelectNode]` 의존성을 가지므로, 노드를 전환할 때마다 기존 cy 인스턴스를 `cy.destroy()`하고 새로 생성한다(line 156, 83).
- Files: `frontend/src/GraphView.jsx`
- Impact: 레이아웃 계산(`cose-bilkent`, animate:false여도 JS-side)이 매 선택마다 재실행된다. 사용자가 그래프 뷰에서 여러 노드를 빠르게 탐색하면 체감 지연이 발생할 수 있다.
- Fix approach: cy 인스턴스를 유지하고 `cy.json({ elements: [...] })` 또는 `cy.add/remove`로 요소만 교체하는 방식으로 전환. 단, expand-collapse 상태 초기화 처리가 추가로 필요하다.

**`inject_ko_names.py` — 배포마다 전체 한글 이름 무조건 덮어쓰기:**
- Issue: `deploy.sh`(line 52)는 매 배포 시 `inject_ko_names.py`를 실행한다. 스크립트는 `SET p.nameKo = $ko`로 조건 없이 전체 매핑을 덮어쓴다(`backend/scripts/inject_ko_names.py:27`). 데이터가 바뀌지 않아도 항상 전체 쓰기가 발생한다.
- Files: `backend/scripts/inject_ko_names.py`, `deploy.sh`
- Impact: 불필요한 Neo4j 쓰기 부하. 현재 데이터 규모에서는 허용 가능하지만, 매핑 파일 크기가 커지면 배포 시간이 늘어난다.
- Fix approach: `SET p.nameKo = $ko WHERE p.nameKo IS NULL OR p.nameKo <> $ko`로 변경하거나, 배포 스크립트에서 데이터 파일 변경 감지 후 선택적 실행.

**`DEFAULT_NODE` 하드코드 (GraphView):**
- Issue: `GraphView.jsx` line 10에 `const DEFAULT_NODE = 'recjNRR60PAuFtjha'`(모세의 theographic_id)가 리터럴로 박혀 있다. 데이터 재적재 시 해당 ID가 바뀌면 GraphView가 404로 에러 상태에 빠진다.
- Files: `frontend/src/GraphView.jsx`
- Impact: 데이터 재로딩·마이그레이션 시 무증상으로 그래프 뷰가 고장날 수 있다.
- Fix approach: 환경변수(`VITE_DEFAULT_NODE`) 또는 `/search?q=모세` 첫 번째 결과로 동적 결정.

## Performance Bottlenecks

**검색(`/search`) — 전체 그래프 스캔:**
- Problem: `search.py`의 Cypher 쿼리가 `MATCH (n) WHERE n.nameKo CONTAINS $q`로 시작한다. 시작 시 생성되는 인덱스(`main.py:16-18`)는 `theographic_id`에만 걸려 있고, `nameKo`·`name` 속성에는 인덱스가 없다.
- Files: `backend/app/routes/search.py`, `backend/app/main.py`
- Cause: 250ms 디바운스 내에 키 입력마다 전체 노드 스캔이 실행된다. 데이터셋이 커질수록 검색 레이턴시가 선형 증가한다.
- Improvement path: Neo4j 전체 텍스트 인덱스(`CREATE FULLTEXT INDEX`) 생성 또는 `theographic_id` 인덱스와 동일 패턴으로 `nameKo`·`name` 속성 인덱스 추가.

**TimelineView — 전체 이벤트 일괄 로드·무한 스크롤 없음:**
- Problem: `TimelineView.jsx`(line 22-25)는 마운트 시 `/events` 전체를 한 번에 가져온다. `/events` 엔드포인트는 LIMIT 없이 `MATCH (e:Event) WHERE e.startDate IS NOT NULL RETURN e`를 실행한다(`events.py:12-13`).
- Files: `frontend/src/TimelineView.jsx`, `backend/app/routes/events.py`
- Cause: 현재 이벤트 수(names_ko/events.json 기준 ~450개 항목)는 허용 범위지만, 가상화(windowing) 없이 DOM에 전부 렌더링되고, 페이지네이션도 없다.
- Improvement path: 서버사이드 페이지네이션(`?offset=&limit=`) 추가 또는 클라이언트 가상 스크롤 도입.

**`/node/{id}` — 단일 요청이 SidePanel·GraphView·MapView 세 곳에서 동시 호출됨:**
- Problem: 노드를 선택하면 SidePanel(`SidePanel.jsx:33`), GraphView(`GraphView.jsx:37`), MapView(`MapView.jsx:367`)가 각각 독립적으로 `/node/{id}`를 호출한다. 같은 응답 데이터임에도 공유하지 않는다.
- Files: `frontend/src/SidePanel.jsx`, `frontend/src/GraphView.jsx`, `frontend/src/MapView.jsx`
- Cause: 뷰 간 공유 상태(캐시)가 없다. App.jsx는 `selectedNode` ID만 전달한다.
- Improvement path: App.jsx에서 선택 노드 데이터를 fetch해 props로 내려주거나, React Query 등 캐싱 레이어 도입.

## Security Considerations

**MapView 팝업 — `setHTML()`에 DB 값 직접 삽입:**
- Risk: `MapView.jsx`(line 292)가 `setHTML()` 템플릿 리터럴 안에 `${label}`(GeoJSON feature의 `label` 속성 = Neo4j `nameKo` 값)을 직접 삽입한다. HTML 이스케이프 없음.
- Files: `frontend/src/MapView.jsx`
- Current mitigation: 데이터 출처가 Theographic 정적 Bible 데이터로 한정되어 있고, inject 스크립트가 관리하는 JSON 파일(`data/names_ko/places.json`)에서만 nameKo가 주입된다. 현재 실질적 공격 경로 없음.
- Recommendations: `label`을 `setHTML()` 대신 `setText()`로 처리하거나, 삽입 전 `label.replace(/</g,'&lt;').replace(/>/g,'&gt;')` 이스케이프 적용.

**CORS `allow_origins=["*"]`:**
- Risk: `main.py:27`에서 모든 오리진에 대한 CORS 허용. 현재 API는 읽기 전용(GET만 허용)이어서 실질 위험은 낮다.
- Files: `backend/app/main.py`
- Current mitigation: `allow_credentials=False`, `allow_methods=["GET"]`으로 범위 제한됨.
- Recommendations: 프로덕션 도메인으로 오리진 화이트리스트 제한(`allow_origins=["https://biblemap.example.com"]`).

## Fragile Areas

**MapView — `expandPlaceRef` / `expandedPlaceRef` 공유 뮤터블 ref 패턴:**
- Files: `frontend/src/MapView.jsx`
- Why fragile: `expandPlaceRef`(함수)와 `expandedPlaceRef`(상태)는 maplibre 초기화 useEffect 내부 클로저와 selection useEffect 사이에서 ref를 통해 공유된다. 두 effect의 실행 순서나 cleanup 타이밍이 어긋나면 오래된 클로저가 이미 destroy된 맵 인스턴스에 접근할 수 있다. 현재 `destroyed` 플래그로 일부 방어되어 있다(line 57, 57→343).
- Safe modification: `expandPlaceRef`·`expandedPlaceRef` 접근 전 항상 `destroyed` 및 `mapRef.current` 존재 여부를 확인할 것. 새 링 관련 로직은 반드시 maplibre `load` 이벤트 핸들러 안에서 초기화해야 한다.
- Test coverage: Playwright로 마커 클릭·탭 전환 시나리오가 검증되나, 빠른 연속 탭 전환 중 링 상태 정합성 테스트는 없다.

**`moveend` 이벤트 + 폴백 타이머(700ms) 경합:**
- Files: `frontend/src/MapView.jsx` (line 395-407)
- Why fragile: `map.once('moveend', ...)` + `setTimeout(runExpand, 700)` 중 먼저 발화한 쪽이 `fired` 플래그로 나머지를 차단한다. 카메라 애니메이션 시간(`duration: 600ms`)과 폴백(700ms)이 100ms 마진으로 설계되어 있어, 느린 환경에서 두 쪽이 거의 동시에 실행될 수 있다.
- Safe modification: 폴백 타이머를 `duration + 200ms` 이상(예: 850ms)으로 늘리거나, `fitBounds`의 `duration` 상수를 변경할 때 폴백 타이머를 함께 조정할 것.
- Test coverage: Playwright로 검색 → 선택 → 링 펼침은 검증됨. 저사양·고지연 환경 시뮬레이션은 없음.

## Test Coverage Gaps

**자동화 테스트 없음 (단위·통합):**
- What's not tested: 백엔드 Neo4j 쿼리 로직(routes/*.py), 프론트엔드 컴포넌트 단위, API 응답 스키마 정합성. 현재 유일한 검증 수단은 배포 후 Playwright 시나리오.
- Files: `backend/app/routes/`, `frontend/src/`
- Risk: 엔드포인트 응답 구조 변경, Neo4j 쿼리 오류가 배포 전 자동으로 감지되지 않는다.
- Priority: Medium — 현재 팀 규모(단일 개발자 + AI)에서 회귀 위험은 낮지만, 데이터셋 확장·신규 엔드포인트 추가 시 빠르게 높아진다.

**백엔드 동기 라우터 — FastAPI 쓰레드풀 소진 가능성:**
- What's not tested: `def`(sync) 라우터 함수가 FastAPI 기본 쓰레드풀(uvicorn 기본: CPU 수)을 점유하는 상황. 다수 동시 요청 시 Neo4j 대기가 쓰레드풀을 소진시킬 수 있다.
- Files: `backend/app/routes/nodes.py`, `backend/app/routes/search.py`, `backend/app/routes/events.py`
- Risk: 현재 단일 사용자 환경에서는 발현 안 됨. 공개 배포 후 동시 사용자 증가 시 리스크 증가.
- Priority: Low — `async def`로 전환하거나 neo4j AsyncDriver 사용이 장기 개선 방향.

---

*Concerns audit: 2026-06-14*
