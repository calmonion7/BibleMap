---
last_mapped_commit: 7522aafe2088e83e8c4bed86a4f0269082db07e0
mapped: 2026-06-20
---

# 코드베이스 우려 사항 (Codebase Concerns)

## 보안

### CORS 전체 개방 (`allow_origins=["*"]`)

- 위험: `backend/app/main.py:27`에서 `allow_origins=["*"]`로 설정. 공개 읽기 전용 API이므로 즉각적 악용은 낮지만, 향후 쓰기 엔드포인트 추가 시 같은 설정이 그대로 남을 가능성이 있다.
- 현재 완화: `allow_methods=["GET"]`만 허용하고, `allow_credentials=False`.
- 권고: 특정 도메인으로 제한하거나, 프로덕션 빌드 여부를 환경변수로 분기.

### 인증·인가 없음

- 모든 API 엔드포인트가 인증 없이 공개 접근 가능. nginx(`nginx/nginx.conf`)에도 IP 제한, HTTP Basic Auth 등 없음.
- 현재는 읽기 전용 Biblical 데이터이므로 큰 문제는 아니나, 데이터 스크래핑·서비스 남용 가능성 존재.

### 레이트 리밋 없음

- `/search`, `/node/{id}`, `/node/{id}/neighbors/grouped` 등 Neo4j 왕복이 발생하는 엔드포인트에 레이트 리밋이 없다.
- 단일 클라이언트가 반복 요청으로 Neo4j 부하를 유발할 수 있다.
- 파일: `backend/app/routes/search.py`, `backend/app/routes/nodes.py`.

### Cypher 쿼리 내 f-string 사용 (낮은 위험)

- `backend/app/routes/nodes.py:169`에서 `NODE_NEIGHBOR_LIMIT` 상수를 f-string으로 Cypher에 삽입:
  ```python
  f"collect(...)[0..{NODE_NEIGHBOR_LIMIT}] AS rows "
  ```
- `backend/app/routes/search.py:27`에서 `SEARCH_LIMIT` 상수 삽입.
- 두 값 모두 모듈 레벨 상수(정수)이며 사용자 입력이 아니므로 인젝션 위험은 없다. 그러나 패턴 자체가 위험하여 유지보수 시 실수로 사용자 입력을 삽입할 여지를 만든다.
- 권고: `$limit` 파라미터를 Cypher에 전달하거나, 상수 사용임을 명확히 주석 표기.

---

## 기술 부채

### 동기 FastAPI 라우트 핸들러 (전체)

- `backend/app/routes/` 내 모든 라우트 핸들러가 `def`(동기). Neo4j 드라이버의 동기 `driver.session().run()`을 직접 호출한다.
- FastAPI는 동기 함수를 `threadpool`에서 실행하지만, Uvicorn 단일 프로세스 환경에서 Neo4j 응답 대기 중 다른 요청이 블로킹될 수 있다.
- 영향 파일: `backend/app/routes/nodes.py`, `events.py`, `books.py`, `search.py`.
- 권고: `neo4j`의 async driver(`AsyncGraphDatabase`)로 전환하거나, 최소한 `/search`처럼 빠른 응답이 필요한 엔드포인트부터 `async def`화.

### `lru_cache` 기반 인메모리 캐시 — 재시작 없이 갱신 불가

- `backend/app/routes/events.py`의 `_compute_events()`, `_load_approx_book_index()`가 `@functools.lru_cache(maxsize=1)`로 캐시.
- `backend/app/overlays.py`의 `book_events_raw()`, `approx_years()`, `event_verses()`도 동일.
- 데이터(`data/event_verses/events.json` 8MB, `data/book_events/books.json`)가 변경되어도 **컨테이너 재시작 없이는 반영되지 않는다**.
- 배포 스크립트(`deploy.sh`)가 API 컨테이너를 재시작하므로 현재는 실질적 문제가 없으나, 핫패치 시나리오에서 혼란을 유발한다.

### `books-overview`와 `books` 엔드포인트의 중복 Neo4j 쿼리

- `backend/app/routes/books.py`의 두 엔드포인트가 동일한 `MATCH (b:Book) RETURN b ORDER BY b.bookOrder ASC` 쿼리를 각각 실행.
- `Cache-Control: no-store`로 설정되어 있어 클라이언트 캐싱도 없다.
- 영향은 소규모(Book 노드가 66개)이나 동일 쿼리 중복이 불필요.

### Neo4j 드라이버 싱글턴 — 연결 오류 복구 없음

- `backend/app/db.py`의 `_driver` 싱글턴은 최초 생성 후 재사용. Neo4j 연결이 끊어지면(`ServiceUnavailable`) 드라이버 재생성 없이 모든 이후 요청이 실패한다.
- Neo4j 연결 장애 시 500 에러가 클라이언트에 그대로 전달된다. 라우트 레벨에 Neo4j 예외 핸들러가 없다.

### `inject_ko_names.py`의 배포 의존성

- `deploy.sh:56`에서 배포 시마다 `inject_ko_names.py`를 실행해 Neo4j에 한글 이름을 주입.
- 이 데이터가 Neo4j에 없으면 UI 전체가 영어 이름으로 표시된다.
- 주입 실패 시 배포가 중단되나(`exit 1`), Neo4j 재프로비저닝 시 데이터 손실 여부를 자동으로 감지하지 않는다.

---

## 성능 병목

### `event_verses/events.json` 8MB 파일 — 시작 시 전체 로드

- `backend/app/overlays.py`의 `event_verses()`가 앱 최초 요청 시 8MB JSON 파일을 메모리에 전부 로드.
- 파일: `data/event_verses/events.json` (8.0M, 135,995줄).
- 현재는 `lru_cache`로 1회만 로드하므로 메모리 상주가 문제. 사건 수가 늘수록 메모리 압박 증가.
- 권고: 사건별 파일 분리 또는 `event_id`를 키로 인덱싱된 경량 조회 구조로 전환.

### `/node/{id}/neighbors/grouped` — 중복 Neo4j 왕복 발생 가능

- 사용자가 지도에서 장소 마커를 클릭하면 `expandPlace()` 함수(`frontend/src/MapView.jsx:108`)가 `/node/${placeId}/neighbors/grouped`를 fetch.
- 동일 장소를 연속 클릭·닫기 시 abort 처리가 있으나, 여러 마커를 빠르게 클릭하면 Neo4j에 다수의 병렬 쿼리가 발생.

### `GET /events` 페이로드 크기 — 전체 사건 목록 단일 응답

- `_compute_events()`가 모든 Event 노드를 한 번에 직렬화해 반환. 사건 수가 증가할수록 페이로드 크기가 선형 증가.
- 현재 `Cache-Control: max-age=300`으로 5분 캐시. 최초 로드 후 브라우저에서 재요청은 억제되나, 캐시 미스 시 전체 재전송.

---

## 취약 영역

### `MapView.jsx` — 매직 넘버 컴포넌트 간 중복

- `frontend/src/App.jsx:20`의 `SHEET_VH = 55`와 `frontend/src/MapView.jsx:411`의 `window.innerHeight * 0.55`가 별도로 유지.
- `frontend/src/App.jsx:18`의 `MOBILE_QUERY = '(max-width: 768px)'`와 `MapView.jsx:410`의 `window.innerWidth <= 768`이 같은 값을 독립적으로 검사.
- 어느 한 쪽만 수정하면 지도 fitBounds 패딩과 시트 높이가 어긋난다.
- 주석으로 연결을 명시(`// App.jsx SHEET_VH=55vh와 일치`)하고 있으나, 공유 상수가 없어 리팩터링 시 버그 유발 위험.

### `MapView.jsx` — maplibregl 맵 인스턴스 생명주기 복잡도

- `frontend/src/MapView.jsx`가 485줄로 프론트엔드에서 가장 복잡한 파일.
- 하나의 `useEffect` 안에 맵 초기화, 이벤트 핸들러 등록, 애니메이션 루프(`requestAnimationFrame`), Abort 제어, `expandPlace` 비동기 fetch, 링 펼침 애니메이션이 모두 얽혀 있다.
- `destroyed` 플래그로 클린업을 수동 관리. Ref가 4개(`mapContainer`, `mapRef`, `popupRef`, `expandPlaceRef`, `expandedPlaceRef`) 사용.
- 수정 시 클린업 순서 오류, 상태 덮어쓰기, 메모리 누수가 발생하기 쉽다.

### `SidePanel.jsx` — Book 노드 연도 칩 하드코딩 음수 처리

- `frontend/src/SidePanel.jsx:175`:
  ```jsx
  node.properties.startYear && `${Math.abs(node.properties.startYear)}BC~${Math.abs(node.properties.endYear)}BC`
  ```
  AD 연도(양수)인 권(예: 신약)에도 `BC`가 표시된다. `endYear`가 `null`이면 `Math.abs(null)` → `0BC` 출력.

### `TimelineView.jsx` — 그룹 팝오버 위치 고정

- `frontend/src/TimelineView.jsx:328`에서 `position: 'absolute', left: 104, top: '100%'`로 팝오버 위치가 픽셀 하드코딩.
- 연도 컬럼 너비가 변경되면 팝오버가 타임라인 선과 어긋난다.

### `nodes.py` — `import json` 함수 내부에서 지연 임포트

- `backend/app/routes/nodes.py:240`:
  ```python
  import json as _json
  ```
  `get_node()` 함수 본문 내부에서 임포트. 모듈 수준으로 이동해야 하나, 기능상 문제는 없다.

---

## 테스트 커버리지

### 자동화 테스트 전무

- 백엔드(`backend/`) 및 프론트엔드(`frontend/src/`) 모두 테스트 파일이 없다.
- `pytest.ini`, `jest.config.*`, `vitest.config.*` 등 테스트 설정 파일도 없다.
- 무결성 검증을 Playwright 수동 스크린샷 방식에만 의존.
- 영향이 큰 미테스트 영역:
  - `backend/app/routes/nodes.py` — `get_node()` 함수 (5개 분기, 259줄 라우트 파일 중 가장 복잡)
  - `backend/app/routes/events.py` — `_compute_events()` (approx_index 머지 로직)
  - `frontend/src/useNodeSelection.js` — `selectNode` / `goBack` / `closePanel` 상태 전환
  - `frontend/src/convexHull.js` — 볼록 껍질 알고리즘

---

## 배포 위험

### 프론트엔드 `dist/` 수동 빌드 의존

- `nginx` 컨테이너가 `frontend/dist`를 직접 마운트(`docker-compose.yml:25`). `dist/`가 없거나 오래된 빌드라면 빈 화면 또는 구버전 UI가 배포된다.
- `deploy.sh`가 `npm run build`를 자동 실행하므로 정상 배포 경로에서는 문제없으나, 수동 `docker compose up` 시 누락 가능.

### Neo4j 헬스체크 없음

- `docker-compose.yml`에 `healthcheck`가 정의되지 않아 Neo4j가 준비되기 전에 API 컨테이너가 요청을 받을 수 있다.
- `deploy.sh`의 `inject_ko_names.py` 재시도(15회)가 이를 보완하지만, API가 Neo4j 미준비 상태에서 500을 반환하는 창이 최대 30초 존재.

### 데이터 파이프라인 스크립트 — 실행 순서 문서화 부재

- `backend/scripts/`에 14개의 generate/load/inject 스크립트가 있으나, 실행 순서나 의존 관계를 정의하는 Makefile, README, 또는 orchestration 스크립트가 없다.
- 잘못된 순서로 실행하면 Neo4j 데이터가 불완전해지며, 오류 메시지가 불분명하다.

### 외부 맵 타일·폰트 서비스 의존

- `frontend/src/MapView.jsx:43`에서 ArcGIS 타일(`server.arcgisonline.com`) 사용.
- `frontend/src/MapView.jsx:37`에서 Protomaps CDN 폰트(`protomaps.github.io`) 사용.
- 두 서비스 중 하나라도 중단되면 지도 렌더링 전체 실패. Self-hosted 대안 없음.
