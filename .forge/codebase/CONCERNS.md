---
last_mapped_commit: 7d2210c48a67b08b79cc3f03008c3ee30e885614
mapped: 2026-06-19
---

# CONCERNS.md — BibleMap 기술 부채 및 위험 영역

## 1. 보안 우려

### 1.1 MapView 팝업 XSS — `label` 값 비이스케이프 삽입
- **파일**: `frontend/src/MapView.jsx:287-304`
- **문제**: `maplibregl.Popup.setHTML()` 호출에 `${label}`과 `${typeLabel}` 값을 HTML 이스케이프 없이 직접 삽입한다. `label` 값은 Neo4j `nameKo` 프로퍼티에서 오는데, 데이터에 `<script>` 태그나 HTML 이벤트 핸들러가 포함될 경우 XSS가 가능하다.
- **경로**: Neo4j `nameKo` 필드 → `/node/{id}/neighbors/grouped` → `grouped.Event[].label` → GeoJSON feature property → maplibre 클릭 이벤트 → `setHTML()`.
- **완화 조건**: 현재 데이터는 신뢰할 수 있는 출처(theographic 데이터 + Claude 생성)이므로 즉각적 위협은 낮지만, DB 직접 쓰기 시(MEMORY.md에 언급된 Neo4j 호스트 직접 접근 가능) 취약점이 노출된다.

### 1.2 inject_ko_names.py의 f-string Cypher — `label` 파라미터화 미흡
- **파일**: `backend/scripts/inject_ko_names.py:26`
- **문제**: `f"MATCH (p:{label} {{theographic_id: $id}}) ..."` — `label` 값("Person", "Place" 등)은 Cypher 파라미터가 아니라 f-string으로 직접 삽입된다. 이 스크립트 자체는 하드코딩된 라벨 값을 `inject()` 함수에 넘기므로 현재 실행 경로에서는 주입 불가하지만, 라벨 출처를 외부에서 받도록 코드가 바뀌면 Cypher 주입이 된다.
- **CORS 설정**: `backend/app/main.py:27` — `allow_origins=["*"]`. 현재 읽기 전용(GET만) 서비스이고 인증이 없으므로 위험도는 낮지만, 나중에 쓰기 엔드포인트가 추가될 때 재검토 필요.

### 1.3 보안 헤더 누락
- **파일**: `nginx/nginx.conf` 전체
- `X-Frame-Options`, `Content-Security-Policy`, `X-Content-Type-Options` 등 기본 보안 헤더가 하나도 설정되어 있지 않다. CSP 부재는 위 XSS 위험을 가중시킨다.

---

## 2. 성능 위험

### 2.1 `/search` — 레이블 미지정 + CONTAINS + toLower 풀스캔
- **파일**: `backend/app/routes/search.py:17-27`
- Cypher: `MATCH (n) WHERE (n.nameKo CONTAINS $q OR toLower(n.name) CONTAINS toLower($q))`.
- `MATCH (n)` 는 라벨 없이 전체 노드를 풀스캔한다. `CONTAINS`는 Neo4j 기본 B-트리 인덱스를 타지 않는다(풀텍스트 인덱스 필요). `toLower(n.name)` 계산도 매 row마다 발생한다. 그래프가 커질수록 응답 지연이 선형 이상으로 증가한다.
- 디바운스(250ms)가 있어 타이핑 중 과부하는 제한되지만 단일 요청 자체가 느릴 수 있다.
- Neo4j Fulltext Index(`CALL db.index.fulltext.createNodeIndex`)를 생성하면 수십 배 개선 가능하다.

### 2.2 `/node/{id}/places` — 라벨 미지정 노드 조회 이중 왕복
- **파일**: `backend/app/routes/nodes.py:25-82`
- 첫 번째 `session.run()`으로 라벨을 가져온 뒤, 두 번째 `session.run()`으로 장소를 조회한다(동일 `with driver.session()` 블록 내 직렬). 라벨을 `MATCH (n {theographic_id: $id})` 로 조회할 때도 라벨 힌트가 없어 full node scan에 의존한다. `theographic_id` 인덱스가 라벨별로만 생성되어 있으므로(lifespan 참고) 라벨 미지정 MATCH는 인덱스를 100% 활용하지 못할 수 있다.
- **동일 패턴**: `get_node_neighbors_grouped()`의 `MATCH (n {theographic_id: $id})-[r]-(m)` (line 116), `get_node()`의 `MATCH (n {theographic_id: $id})` (line 151)도 같음.

### 2.3 `/get_node` Book — 단일 세션 내 3회 직렬 쿼리
- **파일**: `backend/app/routes/nodes.py:148-258`
- Book 노드 조회 시 `get_node()` 함수가 동일 세션 내에서 노드 조회 → 이웃 조회 → 주요 인물 → 주요 사건을 직렬로 실행한다. 최소 3-4번 왕복. 분리된 async 쿼리나 단일 Cypher UNION으로 줄일 수 있다.

### 2.4 `event_verses/events.json` 파일 크기 ~8MB
- **파일**: `data/event_verses/events.json` (7,991,256 bytes)
- `_load_event_verses()` (events.py:28)가 첫 요청 시 8MB JSON을 전체 파싱해 메모리에 올린다. `lru_cache(maxsize=1)` 덕분에 이후 요청은 메모리에서 서빙되지만, 재시작 시 cold start latency가 크다. 구절 데이터는 `event_id` 키로 직접 접근하므로 SQLite나 인덱스 파일로 분리하면 cold start와 메모리 사용을 줄일 수 있다.

### 2.5 `/events` — `_compute_events()`의 `_load_approx_book_index()`가 앱 시작 시 Neo4j 쿼리 실행
- **파일**: `backend/app/routes/events.py:91-124`
- `_load_approx_book_index()`는 Neo4j가 준비되기 전에 첫 요청이 들어오면 연결 오류를 캐시하지 않고 예외를 올린다(`lru_cache`는 예외를 캐시하지 않음). 연속 요청마다 Neo4j 연결을 재시도한다. 반면 Neo4j가 준비된 뒤 한 번 성공하면 영구 캐시되므로 데이터 변경 시 서버 재시작이 필요하다.

### 2.6 `/books` — `Cache-Control: no-store` (불필요한 캐싱 비활성화)
- **파일**: `backend/app/routes/books.py:92`
- `/events`는 `max-age=300`인 반면 `/books`는 `no-store`다. 데이터 빈도가 비슷한데 캐싱 정책이 다르다. `no-store`이면 브라우저와 nginx가 매 페이지 로드마다 재요청해 불필요한 Neo4j 쿼리가 발생한다.

---

## 3. 결합도 및 변경 어려운 영역

### 3.1 모바일 시트 높이 — App.jsx와 MapView.jsx 간 매직 넘버 중복
- **파일**: `frontend/src/App.jsx:17` (`SHEET_VH = 55`), `frontend/src/MapView.jsx:411` (`window.innerHeight * 0.55`)
- 두 파일이 별도 상수로 같은 값(`55vh / 0.55`)을 유지한다. 주석으로 "반드시 일치시킨다"고 명시되어 있지만, 하나를 바꿀 때 다른 것을 놓치면 지도 fitBounds 패딩이 하단 시트와 맞지 않는 레이아웃 버그가 생긴다. 공유 모듈(예: `layout.js`)에 상수 하나로 통합하지 않으면 언제든 재발할 수 있다.

### 3.2 `get_node_places`와 `get_node_neighbors_grouped` — 중복 MATCH 패턴 + 역할 경계 불명확
- **파일**: `backend/app/routes/nodes.py:9-142`
- `get_node_places()`에서 라벨을 먼저 조회한 뒤 라벨에 따라 다른 Cypher를 선택하는 5-branch 분기가 있다. `PeopleGroup` 케이스는 사람→이벤트→장소를 2-hop MATCH로 추적하므로 집단이 크면 결과가 폭발적으로 늘 수 있다(중복 제거를 Python에서 `seen` set으로 처리). Neo4j에서 `DISTINCT` + `LIMIT`을 쿼리 레벨로 내리는 것이 안전하다.

### 3.3 `generate_approx_book_verses.py` — 하드코딩된 (bookId, eventId) 쌍 36개
- **파일**: `backend/scripts/generate_approx_book_verses.py:46-97` (`VERSE_MAP` 딕셔너리)
- 추정연도 31권의 대표 구절이 theographic ID 문자열과 authored-event 슬러그를 키로 하드코딩되어 있다. theographic 데이터의 ID가 바뀌거나 authored 이벤트 슬러그가 변경되면 조용히 깨진다(런타임 오류가 아니라 빈 결과). 변경 감지 메커니즘이 없다.

### 3.4 `build_range_label` 로직 — 두 파일에 중복 구현
- **파일**: `backend/scripts/generate_event_verses.py:57-79`, `backend/scripts/generate_approx_book_verses.py:116-137`
- `build_range_label` 함수가 두 스크립트에 각각 독립적으로 구현되어 있다. 한 쪽 로직이 변경될 때 다른 쪽이 누락되면 생성 결과가 불일치한다. 공통 모듈(`backend/scripts/utils.py`)로 추출이 필요하다.

### 3.5 `SidePanel.jsx` 타입 분기 — Book vs 비-Book 조건부 렌더링 복잡도
- **파일**: `frontend/src/SidePanel.jsx:169-343`
- Book 전용 렌더와 일반 이웃 렌더가 하나의 함수 안에 `node.label === 'Book'` 조건으로 분기되어 있고, Book 뷰 안에서도 background/themes/keyVerse/topPersons/topEvents를 각자 `SectionHeader` 토글로 반복한다. 새 노드 타입을 추가하거나 Book 뷰를 바꿀 때 같은 파일 내 여러 곳을 수정해야 한다.

---

## 4. 알려진 버그 / 취약한 동작

### 4.1 `TimelineView.jsx` — `members[0].sortKey ?? 0` — 정렬 키 오류 가능성
- **파일**: `frontend/src/TimelineView.jsx:73`
- 같은 `startDate`를 가진 이벤트 그룹의 `sortKey`를 그룹 첫 번째 멤버(`members[0]`)에서 읽는다. 멤버 순서가 API 응답 순서에 의존하므로, 같은 날짜 이벤트들의 `sortKey`가 다를 경우 어떤 `sortKey`가 그룹 대표가 될지 비결정적이다. 현재는 `/events`가 `sortKey ASC`로 정렬되어 있어 실질적 영향은 없지만, 정렬 보장이 없는 경우 그룹 간 순서가 틀릴 수 있다.

### 4.2 `SidePanel.jsx` — trait 인덱스를 React key로 사용
- **파일**: `frontend/src/SidePanel.jsx:133`
- `{node.properties.traits.map((t, i) => <div key={i}>...)}` — 배열 인덱스를 key로 사용한다. traits 배열이 재정렬되거나 부분 업데이트되면 React가 잘못된 컴포넌트와 state를 연결한다. `t.trait`(성품 키워드) 또는 `t.verse_ref`로 대체하는 것이 안전하다.

### 4.3 `SidePanel.jsx` — `meta chip`의 BC 연대 하드코딩 음수 처리
- **파일**: `frontend/src/SidePanel.jsx:174`
- `${Math.abs(node.properties.startYear)}BC~${Math.abs(node.properties.endYear)}BC` — `endYear`가 양수(AD)인 책(예: 신약)에서도 `BC`를 붙인다. 실제로 신약은 `startYear`가 양수이므로 chip 조건 `node.properties.startYear &&` 가 걸러줄 수 있지만, AD 연대 책에서 `startYear`가 있을 때 "AD 50BC~AD 70BC" 같은 잘못된 표시가 나올 수 있다.

### 4.4 `MapView.jsx` — `expandPlace` abort 후 `destroyed=true` 체크 없이 `getSource` 호출 가능성
- **파일**: `frontend/src/MapView.jsx:108-152`
- `expandPlace()` 내부 `apiGet()` 이후 `if (destroyed) return;` 체크가 있지만, 그 시점에 `collapseRing()`이 이미 `map.getSource('event-ring-source').setData(EMPTY_GEOJSON)`를 호출한 뒤라면, 이후 `animate()` 콜백이 다시 `setData()`를 호출할 때 `destroyed`가 이미 true이면 정상 종료되지만, `cancelAnimationFrame`이 cleanup에서만 처리되어 cleanup 전 타이밍 윈도우에서 `animFrame`이 실행될 수 있다. 현재까지 실제 오류 보고는 없지만 race condition 가능성이 존재한다.

### 4.5 `deploy.sh` — 로그 경로 macOS 하드코딩
- **파일**: `deploy.sh:6`
- `LOG="/Users/calmonion/Library/Logs/com.biblemap.deploy.log"` — 개인 macOS 경로가 하드코딩되어 있다. 다른 사용자나 리눅스 서버에서 실행하면 `tee` 실패로 배포 스크립트가 깨질 수 있다(단, `tee` 자체가 에러를 내지 않으면 무시될 수도 있음).

---

## 5. 데이터 생성 스크립트 취약 영역

### 5.1 Claude API 응답 JSON 파싱 — `json.loads()` 직접 호출, 예외 처리 없음
- **파일**: `backend/scripts/generate_person_traits.py:65`, `backend/scripts/generate_book_events.py:81`, `backend/scripts/generate_book_context.py:59`
- 세 스크립트 모두 LLM 응답에서 `json.loads(text.strip())`를 try/except 없이 호출한다. LLM이 비-JSON(예: 설명 텍스트, 마크다운 블록 불완전 제거)을 반환하면 `json.JSONDecodeError`로 스크립트 전체가 중단된다. `generate_person_traits.py:70`의 `try/except Exception as e`는 있지만 단순히 빈 traits로 폴백할 뿐이다. `generate_book_events.py`와 `generate_book_context.py`는 파싱 실패 시 재시도나 폴백이 없다.

### 5.2 `generate_verse_text.py` — getbible 외부 API 의존, UA 우회 필요
- **파일**: `backend/scripts/generate_verse_text.py:51-52`, `backend/scripts/generate_verse_text.py:89`
- 빌드 파이프라인이 `https://api.getbible.net/v2/` 외부 서비스에 의존한다. 이 API가 변경되거나 비활성화되면 본문 데이터를 재생성할 수 없다. 또한 기본 Python `urllib` UA에 403을 반환한다는 점이 주석에 명시되어 있어 브라우저 UA를 우회로 쓰고 있는데, 이는 언제든 깨질 수 있다.

### 5.3 `generate_event_verses.py` — theographic 원격 데이터 15MB 매번 다운로드
- **파일**: `backend/scripts/generate_event_verses.py:24-26`
- 스크립트 실행마다 GitHub raw에서 `verses.json` (~15MB)을 다운로드한다. 로컬 캐시나 저장 경로가 없어 반복 실행 시 네트워크 비용이 크다. GitHub raw URL이 변경되거나 reorg 되면 스크립트가 깨진다.

---

## 6. 인프라 / 운영 우려

### 6.1 Neo4j 이미지 미버전 고정 — `neo4j:5`
- **파일**: `docker-compose.yml:3`
- `neo4j:5`는 `5.x` 최신 패치를 자동으로 가져온다. 마이너 버전 업에서 Bolt 프로토콜이나 Cypher 구문 변경이 생기면 `neo4j==6.2.0` Python 드라이버와 호환 문제가 생길 수 있다. `neo4j:5.26.0` 같은 구체적 태그를 사용하는 것이 안전하다.

### 6.2 Health check 엔드포인트 없음
- **파일**: `backend/app/main.py` 전체, `docker-compose.yml` 전체
- API 컨테이너에 `/health`나 `/ready` 엔드포인트가 없고, `docker-compose.yml`에 `healthcheck` 설정도 없다. `deploy.sh`에서 Neo4j 준비를 15회 sleep 재시도로 처리하는 것도 동일 이유다. 컨테이너가 기동되어도 Neo4j 미연결 상태에서 API 요청이 들어오면 500을 반환한다.

### 6.3 앱 레벨 Neo4j 드라이버 종료 미처리
- **파일**: `backend/app/db.py:4-15`, `backend/app/main.py:8-21`
- `_driver` 글로벌 인스턴스가 생성되지만 lifespan의 cleanup(yield 이후) 단계에서 `driver.close()`가 호출되지 않는다. 프로세스 종료 시 Neo4j 연결 풀이 그레이스풀하게 닫히지 않는다.

### 6.4 `_load_approx_book_index()`의 Neo4j 호출이 lru_cache 안에 있음
- **파일**: `backend/app/routes/events.py:40-88`
- `_load_approx_book_index()`는 `@functools.lru_cache`가 달려 있고 내부에서 Neo4j를 동기 호출한다. FastAPI는 sync 함수를 threadpool에서 실행하므로 문제는 없지만, 이 함수가 처음 호출될 때 Neo4j 연결이 느리면 해당 요청이 블록된다. 동시 요청이 많을 경우 동일 함수가 여러 스레드에서 동시에 호출될 수 있어 lru_cache의 thread-safety에 의존하게 된다(CPython GIL 덕분에 실제로는 안전하지만, 의도적 설계는 아니다).

---

## 7. 코드 스타일 / 경미한 기술 부채

### 7.1 `nodes.py` — `import json as _json` 함수 내부에서
- **파일**: `backend/app/routes/nodes.py:241`
- `json` 모듈을 파일 최상단이 아닌 함수(`get_node`) 내부에서 임포트한다. 성능 영향은 미미하지만 관례에 어긋난다. 파일 상단 임포트로 이동하면 된다.

### 7.2 `theme.js` 주석의 GraphView 참조 — 삭제된 컴포넌트 언급
- **파일**: `frontend/src/theme.js:2`
- `// (이전엔 App.jsx·SidePanel.jsx·GraphView.jsx에 따로 정의돼...)` — `GraphView.jsx`는 현재 코드베이스에 존재하지 않는다(이전 리팩터링에서 제거됨). 주석이 stale 상태다.

### 7.3 `TimelineView.jsx` — `visibleGroups`가 계산되지만 직접 사용되지 않음
- **파일**: `frontend/src/TimelineView.jsx:86-98`
- `useMemo`에서 `{ visibleGroups, timeline }` 두 값을 반환하지만 렌더 코드에서 `visibleGroups`는 사용되지 않고 `timeline`만 사용된다. `visibleGroups`를 별도 `useMemo`로 유지할 이유가 없으며 제거 가능하다.

### 7.4 `books.py`의 `_REPO_DATA_DIR` 경로 계산 — `events.py`와 중복
- **파일**: `backend/app/routes/books.py:15-28`, `backend/app/routes/events.py:13-24`
- 두 파일 모두 `os.path.dirname(__file__)` 기반으로 `_REPO_DATA_DIR`과 후보 경로 리스트를 동일 패턴으로 선언한다. 경로 해석 로직이 중복이라 변경 시 두 곳 수정 필요.
