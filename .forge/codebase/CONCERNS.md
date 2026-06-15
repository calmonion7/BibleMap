---
last_mapped_commit: ecdb7cb2ea1bf665b0690e62b4cf51261761072c
mapped: 2026-06-15
---

# Codebase Concerns

## Tech Debt

**`/node/{id}` 엔드포인트 — 동일 세션 내 3~5회 직렬 Neo4j 쿼리:**
- 문제: `get_node()`(`backend/app/routes/nodes.py`)가 단일 HTTP 요청 안에서 최대 5회 `session.run`을 순차 실행한다. 노드 조회 → 이웃 조회(LIMIT 50) → 전체 이웃 수 COUNT → Book인 경우 추가로 top_persons, top_events 쿼리 2회.
- 영향: 연결이 많은 Book(예: 창세기) 선택 시 5회 왕복 레이턴시가 누적된다. SidePanel과 MapView가 동시에 동일 nodeId를 조회하면 실질적으로 10회 Neo4j 왕복.
- 개선 방향: COUNT를 이웃 쿼리와 동일 Cypher로 합치거나, Book 전용 쿼리를 단일 `WITH` 체인으로 통합.

**`/node/{id}/places` — 무제한 결과셋 (Person·PeopleGroup):**
- 문제: Person 및 PeopleGroup 타입의 `/places` 쿼리에 LIMIT 절이 없다(`backend/app/routes/nodes.py` Person 분기, PeopleGroup 분기). PeopleGroup은 `PeopleGroup→Person→Event→Place` 3단계 패턴 매칭으로 잠재적으로 수천 건 반환.
- 영향: 대형 PeopleGroup(예: 이스라엘 자손) 선택 시 Neo4j와 프론트엔드 MapView GeoJSON 렌더링 모두 과부하.
- 개선 방향: 쿼리 RETURN 절 앞에 `LIMIT 200` 상수 추가.

**`inject_ko_names.py` — 배포마다 전체 덮어쓰기:**
- 문제: `deploy.sh`가 매 배포 시 `inject_ko_names.py`를 실행하며, 스크립트는 조건 없이 `SET p.nameKo = $ko`로 전체 매핑을 덮어쓴다(`backend/scripts/inject_ko_names.py`).
- 영향: 데이터 변경 없이도 불필요한 Neo4j 쓰기가 발생한다. 현재 규모에서는 허용 가능하나 매핑 파일 확장 시 배포 시간 증가.
- 개선 방향: `WHERE p.nameKo IS NULL OR p.nameKo <> $ko` 조건 추가, 또는 deploy.sh에서 파일 변경 감지 후 선택 실행.

**`API_URL` / `API_BASE` 중복 선언 — `api.js`가 있음에도 각 파일에 로컬 상수:**
- 문제: `api.js`에 `API_BASE`를 중앙화했으나 `App.jsx`, `MapView.jsx`, `SidePanel.jsx`, `TimelineView.jsx` 4개 파일이 각자 `VITE_API_URL` 폴백 상수를 별도 선언한다. `api.js`의 `apiGet()` 헬퍼는 아직 어떤 파일도 import하지 않는다.
- 영향: 베이스 URL 변경 시 5곳을 동시에 수정해야 한다. 누락되면 프로덕션에서 일부 요청만 `http://localhost:8000`으로 떨어진다.
- 개선 방향: `MapView.jsx`, `SidePanel.jsx`, `TimelineView.jsx`, `App.jsx`가 `api.js`의 `API_BASE`(또는 `apiGet`)를 import하도록 통일.

**`App.css` — Vite 기본 템플릿 잔재:**
- 문제: `frontend/src/App.css`가 Vite 초기 템플릿의 `.counter`, `.hero` 등 미사용 스타일을 포함하고 있다. `App.jsx`는 이 CSS를 import하지 않는 것으로 보인다.
- 영향: 빌드 번들에 포함 여부 불명확. 혼란을 줄 수 있는 데드 코드.
- 개선 방향: `App.css` import 여부 확인 후 제거 또는 실사용 스타일만 유지.

## Known Bugs

**MapView 에러 배너 — 네비게이션 바 아래 가려짐 (미해결):**
- 증상: `/places` 요청 실패 시 표시되는 에러 배너(`MapView.jsx` `top: 12`)가 플로팅 네비게이션 바(App.jsx `zIndex: 20`) 뒤에 가려진다. 배너의 `zIndex: 10` < 네비 `zIndex: 20`.
- 위치: `frontend/src/MapView.jsx` (에러 배너 div) vs `frontend/src/App.jsx` (네비게이션 div).
- 수정: 에러 배너의 `top`을 `NAV_H(48px) + 여백`으로 조정하거나 `zIndex`를 네비보다 높게 설정.

**SidePanel Book 연도 칩 — 신약 책도 항상 "BC" 표기:**
- 증상: Book 상세 패널의 연도 칩(`SidePanel.jsx` line 185)이 `${Math.abs(startYear)}BC~${Math.abs(endYear)}BC` 형식으로 양수(신약) 연도도 무조건 "BC"로 표시한다. 예: 요한계시록이 "96BC~96BC"로 표시됨.
- 위치: `frontend/src/SidePanel.jsx` Book 메타 칩 렌더링 부분.
- 수정: `startYear < 0 ? '...BC' : 'AD...'` 조건 분기로 BC/AD를 구분해야 한다.

**`load_books.py` startDate BC 파싱 — "BC" 문자열 포함 여부에 의존:**
- 증상: `build_book_year_range()`가 `startDate` 문자열에 `"BC"`가 포함되는지로 BC/AD를 판단한다. Theographic 원본의 `startDate` 실제 형식이 변경되거나 음수 정수로 제공될 경우 연도 부호가 반전된다.
- 위치: `backend/scripts/load_books.py` `build_book_year_range()` 함수.
- 현재 상태: 데이터가 정적이므로 즉각 문제 없음. 재적재 시 주의 필요.

## Performance Bottlenecks

**검색(`/search`) — `nameKo`·`name` 속성에 인덱스 없음:**
- 문제: `search.py`의 Cypher 쿼리 `MATCH (n) WHERE n.nameKo CONTAINS $q`는 전체 노드 스캔이다. `main.py`의 lifespan에서 생성하는 인덱스는 `theographic_id`에만 걸려 있다.
- 영향: 250ms 디바운스 내 키 입력마다 전체 그래프 스캔. 현재 노드 수(수천 개)에서는 허용 범위이나, 데이터셋 확장 시 선형 증가.
- 개선 방향: `CREATE FULLTEXT INDEX` 생성 또는 `nameKo`·`name` 속성 복합 인덱스 추가.

**TimelineView — `/events` 전체 일괄 로드, 페이지네이션·가상 스크롤 없음:**
- 문제: `TimelineView.jsx`가 마운트 시 `/events` 전체를 한 번에 fetch하고, 가상화 없이 DOM에 전부 렌더링한다. `events.py`는 LIMIT 없이 전체 반환.
- 영향: 현재 이벤트 수(~450개)에서는 허용 가능. 데이터 확장 시 초기 로딩과 DOM 렌더 비용 증가.
- 개선 방향: 서버 측 페이지네이션(`?offset=&limit=`) 또는 클라이언트 가상 스크롤(예: `react-window`).

**동기 FastAPI 라우터 — uvicorn 쓰레드풀 소진 가능성:**
- 문제: 모든 라우터 함수가 `def`(동기)로 선언되어 있어 FastAPI가 기본 쓰레드풀(uvicorn 기본: CPU 수)에서 실행한다. 다수 동시 요청 시 Neo4j 대기가 쓰레드풀을 소진시킬 수 있다.
- 파일: `backend/app/routes/nodes.py`, `search.py`, `events.py`
- 현재 위험: 단일 사용자 환경에서는 미발현. 공개 배포 후 동시 사용자 증가 시 리스크.
- 개선 방향: `async def` + neo4j `AsyncDriver`로 전환.

## Security Considerations

**MapView 팝업 — `setHTML()`에 DB 값 직접 삽입 (XSS 잠재 가능성):**
- 위험: `MapView.jsx`의 `setHTML()` 템플릿 리터럴 안에 `${label}`(Neo4j `nameKo` 값)을 HTML 이스케이프 없이 삽입한다.
- 현재 완화 요소: 데이터 출처가 Theographic 정적 데이터 + 관리형 JSON(`data/names_ko/`)으로 한정. 사용자 입력 경로 없음.
- 권장: `setHTML()` 대신 `setText()` 사용 또는 삽입 전 `<` `>` 이스케이프 적용.

**CORS `allow_origins=["*"]`:**
- 위험: `backend/app/main.py`에서 모든 오리진 허용.
- 현재 완화 요소: `allow_credentials=False`, `allow_methods=["GET"]`으로 범위 제한. 읽기 전용 API.
- 권장: 프로덕션 도메인으로 오리진 화이트리스트 제한.

**`search.py` — Cypher에 f-string + Python 상수 주입:**
- 위험: `search.py`의 Cypher 쿼리가 f-string이며 `LIMIT {SEARCH_LIMIT}` 상수를 Python 변수로 주입한다. 사용자 입력 `$q`는 파라미터화되어 안전하나, 구조적으로 f-string Cypher 패턴은 유지·확장 시 Cypher 인젝션 위험을 높인다. `nodes.py`의 `NODE_NEIGHBOR_LIMIT`도 동일 패턴.
- 현재 위험: f-string에 삽입되는 값이 Python 모듈 상수이므로 실질적 인젝션 경로 없음.
- 권장: 한도 값을 쿼리 파라미터(`session.run(cypher, {"limit": LIMIT})`) 또는 쿼리 문자열 상수로 분리해 f-string 의존 제거.

## Fragile Areas

**MapView — `expandPlaceRef` / `expandedPlaceRef` 공유 뮤터블 ref:**
- 파일: `frontend/src/MapView.jsx`
- 취약 이유: maplibre 초기화 useEffect 내부 클로저와 selection useEffect가 `expandPlaceRef`(함수), `expandedPlaceRef`(상태)를 ref로 공유한다. 두 effect의 cleanup 순서가 어긋나면 이미 destroy된 맵 인스턴스에 접근 가능. `destroyed` 플래그로 일부 방어되어 있으나 ref 공유 구조 자체의 복잡성이 높다.
- 안전 수정 지침: `expandPlaceRef`·`expandedPlaceRef` 접근 전 항상 `destroyed` 플래그 및 `mapRef.current` 존재 여부 확인. 링 관련 신규 로직은 반드시 `map.on('load', ...)` 핸들러 안에서 초기화.
- 테스트 공백: 빠른 연속 탭 전환 중 링 상태 정합성을 검증하는 자동화 테스트 없음.

**`moveend` 이벤트 + 폴백 타이머(700ms) 경합:**
- 파일: `frontend/src/MapView.jsx` (selection useEffect, `runExpand` 함수)
- 취약 이유: `map.once('moveend', ...)` + `setTimeout(runExpand, 700)` 중 먼저 발화한 쪽이 `fired` 플래그로 차단한다. `fitBounds` 애니메이션 `duration: 600ms`와 폴백 700ms 사이 여유가 100ms뿐이어서 저사양 환경에서 양쪽이 거의 동시에 실행될 수 있다.
- 안전 수정 지침: `fitBounds`의 `duration` 상수 변경 시 폴백 타이머를 반드시 `duration + 200ms` 이상으로 함께 조정.

**LLM 생성 JSON 파싱 — 마크다운 코드펜스 처리가 취약:**
- 파일: `backend/scripts/generate_person_traits.py`, `backend/scripts/generate_book_context.py`
- 취약 이유: LLM 응답에서 마크다운 코드펜스를 제거하는 로직이 `text.split("```")[1]`로 단순 분할한다. LLM이 중첩 코드블록이나 다른 형식으로 응답하면 `json.loads`가 실패하고, 오류 시 `{"traits": []}` 빈 값으로 저장된다(데이터 손실).
- 현재 완화 요소: 오프라인 일회성 스크립트이므로 실패 즉시 확인 가능. 재실행 시 기존 결과 스킵(`tid in result`).
- 안전 수정 지침: 파싱 실패 시 원본 텍스트를 로그에 남겨 수동 확인 가능하게 할 것.

**외부 지도 타일 서버 및 폰트 서버 의존:**
- 파일: `frontend/src/MapView.jsx`
- 의존 서비스: ArcGIS NatGeo 타일(`server.arcgisonline.com`) + Protomaps 폰트 CDN(`protomaps.github.io`). 이 두 외부 서버가 다운되거나 정책 변경 시 지도 자체가 표시되지 않는다.
- 현재 위험: 두 서비스 모두 무료 공개 엔드포인트이나 SLA가 없다. ArcGIS 타일은 ToS상 대량 트래픽 제한이 있을 수 있다.
- 권장: 장기적으로 자체 호스팅 타일(Protomaps PMTiles) 또는 유료 타일 서비스 전환 검토.

**외부 성경 텍스트 API(`getbible.net`) 의존:**
- 파일: `frontend/src/SidePanel.jsx` (`fetchVerseText`)
- 취약 이유: Book 상세 패널에서 대표 구절 텍스트를 `https://api.getbible.net/v2/kor/` 실시간 fetch한다. 이 API가 CORS를 허용하지 않거나 다운되면 구절 텍스트가 조용히 표시 안 됨(오류 처리는 `null` 반환으로만 처리). SLA·버전 변경 보장 없음.
- 현재 완화 요소: 실패 시 구절 텍스트만 미표시되고 나머지 Book 정보는 정상 표시됨.
- 권장: 구절 텍스트를 백엔드에서 프록시하거나, 정적 성경 텍스트 파일로 번들링.

## Test Coverage Gaps

**자동화 테스트 없음 (단위·통합):**
- 백엔드 Neo4j 쿼리 로직(`backend/app/routes/`), 프론트엔드 컴포넌트 단위, API 응답 스키마 정합성 모두 미검증. 유일한 검증 수단이 배포 후 Playwright 시나리오.
- 위험: 엔드포인트 응답 구조 변경, Neo4j 쿼리 오류가 배포 전 자동 감지 불가.
- 우선순위: Medium — 단일 개발자 환경에서 현재 회귀 위험은 낮으나 신규 엔드포인트 추가 시 빠르게 높아짐.

**`backend/` hot-reload 비지원 — 로컬 검증 마찰:**
- 문제: 백엔드는 Docker 이미지 빌드 후 컨테이너 재시작이 필요하다(`docker compose up -d --build api`). 변경 → 검증 사이클이 느리다.
- 현재 워크플로: MEMORY.md에 명시된 대로 로컬 검증 전 반드시 재빌드 필요. 이를 잊으면 이전 코드로 검증하게 된다.
- 개선 방향: `volumes`에 코드 마운트 + uvicorn `--reload` 옵션 적용으로 개발 시 hot-reload 활성화.

---

*Concerns audit: 2026-06-15*
