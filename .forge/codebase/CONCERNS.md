---
last_mapped_commit: 6bc79bba2bb1a869260e73efee7d9366d96a1cc0
mapped: 2026-06-20
---

# Codebase Concerns

**Analysis Date:** 2026-06-20

## Known Bugs

**클러스터 클릭 시 맵 줌 동작 불가:**
- 증상: 클러스터(여러 마커 묶음) 클릭 시 아무 동작이 없음
- 파일: `frontend/src/MapView.jsx:527-528`
- 원인: maplibre-gl v5에서 `getClusterExpansionZoom(clusterId)`는 `Promise<number>`를 반환한다. 현재 코드는 반환값을 동기 number로 취급해 `if (zoom)` 조건이 Promise 객체(항상 truthy)를 받지만, `map.easeTo({ zoom: Promise })`를 호출해 실제 줌이 발생하지 않는다.
  ```js
  // 현재 (버그)
  const zoom = map.getSource('places-source').getClusterExpansionZoom(feature.properties.cluster_id)
  if (zoom) map.easeTo({ center: feature.geometry.coordinates, zoom, duration: 400 })
  // 수정 필요: .then(zoom => map.easeTo(...)) 또는 async/await
  ```
- 타입 선언 확인: `frontend/node_modules/maplibre-gl/dist/maplibre-gl.d.ts:2438` → `getClusterExpansionZoom(clusterId: number): Promise<number>`

**Book 연도 칩 레이블 오류 (BC/AD 미구분):**
- 증상: NT 책처럼 endYear가 양수(AD)인 경우에도 "XXBC"로 표시됨
- 파일: `frontend/src/SidePanel.jsx:175`
- 원인: `Math.abs(node.properties.endYear)` 뒤에 무조건 `BC`를 붙임. 부호를 보고 "BC" / "AD"를 분기해야 함
  ```js
  // 현재 (버그)
  `${Math.abs(node.properties.startYear)}BC~${Math.abs(node.properties.endYear)}BC`
  ```

## Tech Debt

**JavaScript(JSX) 전용 프론트엔드, TypeScript 미사용:**
- 전체 `frontend/src/` 가 `.js`/`.jsx`로 구성됨. 타입 정보가 없어 API 응답 shape 변경 시 런타임에야 발견됨
- 파일: `frontend/src/*.jsx`, `frontend/src/*.js` (13개 파일)
- 영향: `apiGet()` 반환값이 unknown이어서 잘못된 필드 참조가 빌드 타임에 걸리지 않음
- 전환 비용: vite, eslint 설정 변경 + tsconfig 추가. 현재 eslint는 JS/JSX만 린팅 (`frontend/eslint.config.js:8`)

**lru_cache 캐시 무효화 메커니즘 없음:**
- `_compute_events()`, `_load_approx_book_index()` (`backend/app/routes/events.py:11, 53`), overlay 로더 3개 (`backend/app/overlays.py:30, 36, 42`)가 `@functools.lru_cache(maxsize=1)`로 캐시됨
- Neo4j 데이터 또는 `data/` 파일이 변경되어도 API 컨테이너 재시작 없이는 반영되지 않음
- 캐시 강제 초기화(`cache_clear()`) 엔드포인트나 TTL 기반 무효화가 없음
- HTTP `Cache-Control: max-age=300`은 클라이언트 캐시이고, 서버 lru_cache는 무제한 유지

**places 쿼리 결과 상한 없음:**
- Person, PeopleGroup, Book 노드의 `/node/{id}/places` 응답이 LIMIT 없이 Python `seen` set으로 중복 제거만 함
- 파일: `backend/app/routes/nodes.py:35-82` (각 label 분기)
- 대형 PeopleGroup(이스라엘 민족 등) 또는 큰 Book(창세기)에서 수백 개의 장소 좌표를 한 번에 반환할 수 있음
- 영향: 응답 크기 및 MapView GeoJSON 렌더링 부하

**MapView 이벤트 링·스파이더파이 동시 setData 경쟁:**
- `expandPlace()`(async, AbortController 보유)와 `collapseRing()`이 모두 `event-ring-source`에 `setData()`를 호출함
- `spiderifyPlaces()`는 `collapseRing()`을 호출한 뒤 바로 spider source를 조작하지만, 만약 `expandPlace` fetch가 미완료 상태에서 스파이더파이가 먼저 완료되면 뒤늦은 `expandPlace` 응답이 ring source를 덮어쓸 수 있음
- `expandAbortCtrl.abort()`가 선행 경로에서 호출되므로 대부분은 방어되지만, abort 이후 `then` 콜백이 동기 실행 사이클에서 실행되는 타이밍 엣지 케이스가 남음
- 파일: `frontend/src/MapView.jsx:361-408`, `frontend/src/MapView.jsx:304-330`

**traits JSON 런타임 파싱 (노드 상세 라우트 내부):**
- 파일: `backend/app/routes/nodes.py:239-244`
- Person 노드의 `traits` 필드를 응답 조립 중 `json.loads()`로 파싱함. Neo4j에 문자열로 저장된 JSON이 깨지면 `[]`로 폴백하지만 조용히 실패함
- import도 함수 내부에서 실행(`import json as _json`)
- 개선 경로: Neo4j 저장 시 이미 파싱된 구조를 넣거나, 모듈 최상단 import 사용

**검색 q 파라미터 길이 제한 없음:**
- 파일: `backend/app/routes/search.py:9-11`
- `q`에 길이 제한이 없어 매우 긴 문자열이 Neo4j CONTAINS 쿼리로 전달될 수 있음
- SEARCH_LIMIT(20)으로 결과는 제한되지만 쿼리 실행 비용은 문자열 길이에 비례

## Security Considerations

**XSS: MapView 팝업 setHTML에 DB 데이터 직접 보간:**
- 위험: `label`(Neo4j `nameKo` 필드)을 HTML 이스케이프 없이 `setHTML()` 템플릿 리터럴에 삽입
- 파일: `frontend/src/MapView.jsx:451-469`, `frontend/src/MapView.jsx:495-513`
- 현재 완화: `nameKo`는 관리자만 수정 가능한 내부 DB 데이터이므로 외부 공격자가 직접 주입하기 어려움. 그러나 DB 오염 경로(스크립트 오류, 관리자 실수)가 존재하면 팝업 XSS로 이어짐
- 권장: `label`을 `textContent`로 처리하거나 `maplibregl.Popup().setText()` 사용, 또는 DOM API로 팝업 내용 구성

**API 인증 없음 (공개 읽기 전용):**
- `backend/app/main.py`에 인증 미들웨어가 없음. `allow_origins=["*"]`로 CORS 완전 개방
- 현재: read-only API이고 내부 성경 데이터만 반환하므로 직접 피해는 제한적
- 위험: API가 인터넷에 노출(port 8080)될 경우 무제한 Neo4j 쿼리 실행 가능, rate-limit 없음

**nginx 프록시 타임아웃 미설정:**
- 파일: `nginx/nginx.conf`
- `proxy_read_timeout`, `proxy_connect_timeout`, `proxy_send_timeout`이 nginx 기본값(60s)으로 동작
- 느린 Neo4j 쿼리가 연결을 점유하다 타임아웃되어도 클라이언트에 502가 반환될 뿐 별도 처리 없음

## Performance Bottlenecks

**BibleOverviewView 매 마운트마다 Neo4j 직접 조회:**
- 파일: `backend/app/routes/books.py:11-29` (`/books-overview`)
- `Cache-Control: no-store`로 브라우저 캐시도 금지하고, 서버 lru_cache도 없음
- 탭 전환 시마다 `MATCH (b:Book) RETURN b` 쿼리가 Neo4j에 전송됨
- 개선: lru_cache 추가 또는 `Cache-Control: max-age` 설정

**event_verses.json 8.3MB 전체 메모리 상주:**
- 파일: `backend/app/overlays.py:42-45`, `data/event_verses/events.json`
- `@functools.lru_cache`로 프로세스 전체 수명 동안 8.3MB JSON이 메모리에 유지됨
- 현재 556개 사건 기준이며, 데이터 확장 시 선형 증가
- `/event/{id}/verses` 접근 시 전체 dict을 메모리에서 key lookup — 응답 자체는 빠르지만 메모리 사용량 고정

**places-source GeoJSON 클러스터링 — 필터 없이 전체 장소:**
- 파일: `frontend/src/MapView.jsx:61-67`
- 선택 노드의 전체 장소를 `places-source`에 통째로 세팅. 클러스터링(`cluster: true`)이 있으나 대형 Person(예수, 모세) 선택 시 수십 개의 장소 Feature가 동시에 로드됨
- 현재는 실용적 규모이나 데이터가 늘면 렌더링 부하 증가

## Fragile Areas

**MapView useEffect 의존성: onSelectNode 안정성:**
- 파일: `frontend/src/MapView.jsx:578` (`}, [onSelectNode]`)
- MapView 초기화 effect가 `onSelectNode`를 의존성으로 가짐. `selectNode`는 `useCallback([], [])`으로 안정화되어 있으나(`useNodeSelection.js:33`), App.jsx에서 `selectNode`를 직접 전달하므로 안정성이 보장됨. 향후 `onSelectNode` 래핑 없이 익명 함수를 전달하면 MapView가 매 렌더마다 재초기화됨

**dismissedFilter / dismissedPersonFilter 동일성 비교 의존:**
- 파일: `frontend/src/TimelineView.jsx:98-99`
- `dismissedFilter !== bookFilter`를 참조 동일성(===)으로 비교. `bookFilter`는 `selectedNodeMeta`에서 파생된 객체 리터럴(`useNodeSelection.js:15-19`)이므로, 같은 Book을 다시 선택하면 새 객체가 생성되어 dismiss 상태가 자동 초기화됨 — 의도된 동작이지만 Object.is 비교임을 모르면 오해하기 쉬움

**personFilter는 Set — 직렬화 불가:**
- 파일: `useNodeSelection.js:22-24`, `App.jsx:259`
- `personEventIds`는 `new Set(data.eventIds)`로 생성되어 TimelineView에 전달됨. Set은 JSON 직렬화 불가이므로, 향후 URL 직렬화나 persist 기능 추가 시 별도 변환이 필요함

**MapView 700ms 폴백 타이머 하드코딩:**
- 파일: `frontend/src/MapView.jsx:653`
- `autoExpandTimer = setTimeout(runExpand, 700)`: moveend 미발화 시 폴백으로 링을 펼치는 타이머. 700ms는 `fitBounds duration: 600`보다 100ms 긴 값이나, 느린 기기에서 애니메이션이 700ms 이상 걸리면 moveend 전에 링이 펼쳐져 반경 R이 이전 줌으로 계산될 수 있음

## Scaling Limits

**Neo4j 드라이버 싱글턴, 연결 풀 설정 없음:**
- 파일: `backend/app/db.py`
- `GraphDatabase.driver()` 기본값으로 생성됨. 동시 요청이 많아지면 연결 풀 소진 가능
- 개선: `max_connection_pool_size`, `connection_acquisition_timeout` 설정 추가

**FastAPI 동기 라우트 + uvicorn 단일 워커:**
- 파일: `backend/Dockerfile` (`CMD ["uvicorn", "app.main:app", ...]`), 모든 라우트 함수가 `def`(동기)
- 동기 라우트는 FastAPI가 내부적으로 threadpool에서 실행하나 Neo4j 블로킹 I/O로 인해 동시성이 제한됨
- 동시 요청 폭증 시 단일 워커 uvicorn이 병목

## Dependencies at Risk

**lucide-react ^1.17.0 — 신규 메이저 버전:**
- 파일: `frontend/package.json`
- v1 계열은 API가 안정화 단계이나 아이콘 이름이 버전 간 변경될 수 있음. 현재 사용 아이콘: `Map, Clock, Search, X, BookOpen` (`App.jsx:2`)

## Test Coverage Gaps

**테스트 파일 전무:**
- 프론트엔드(`frontend/src/`)와 백엔드(`backend/app/`)에 `.test.` 또는 `.spec.` 파일이 없음
- 테스트 러너 설정(jest, vitest, pytest)도 없음
- 위험 영역:
  - `convexHull()` — 경계 케이스(2점, 공선점) 수동 검증됨 (`frontend/src/convexHull.js`)
  - `_compute_events()` 병합 로직 — approx_index와 CONTAINS_BOOK 데이터 결합 (`backend/app/routes/events.py:54-86`)
  - `get_node_places()` 타입별 쿼리 분기 5개 — 각 label마다 다른 Cypher (`backend/app/routes/nodes.py:20-108`)
  - 검색 ranking 로직 — rank 0/1/2 분기 (`backend/app/routes/search.py:19-24`)
- 우선순위: High (데이터 파이프라인·API 응답 shape 검증 부재)

---

*Concerns audit: 2026-06-20*
