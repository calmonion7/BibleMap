---
last_mapped_commit: 4ed4d876d7fa3b06a8eb1647b5b50ed73f906b25
mapped: 2026-06-19
---

# BibleMap — 기술 부채 및 위험 영역

## 1. 보안 우려

### 1-1. `.env` 파일에 실제 비밀번호 커밋 직전 위험
- `/Users/calmonion/Project/BibleMap/.env`에 `NEO4J_PASSWORD=biblemap123`이 평문으로 저장되어 있다.
- `.gitignore`에 `.env`가 명시되어 있어 현재는 Git 추적 대상이 아니다. 그러나 이 파일이 실수로 스테이지되면 비밀번호가 히스토리에 영구 기록된다.
- `.env.example`의 값은 `your-password-here`로 올바르게 처리되어 있으나, 실제 `.env`가 예제와 분리 관리된다는 점을 팀원이 인지해야 한다.

### 1-2. CORS 와일드카드 설정
- `backend/app/main.py` 26~27행: `allow_origins=["*"]`로 모든 오리진 허용.
- 현재는 읽기 전용(GET) API이고 인증 없는 공개 지식 데이터이므로 즉각적 위협은 낮다. 그러나 추후 쓰기 API 추가 시 반드시 오리진을 제한해야 한다.

### 1-3. 인증·레이트리밋 부재
- 모든 API 엔드포인트에 인증 미들웨어, API 키, 레이트리밋이 전혀 없다.
- `/search?q=...` 는 매 요청마다 Neo4j 풀스캔(`MATCH (n)` — 라벨 없는 전체 노드 스캔)을 실행한다. 반복 요청 시 DB 부하가 선형으로 증가한다.

---

## 2. 성능 병목 및 위험

### 2-1. 검색 쿼리 전체 노드 스캔
- `backend/app/routes/search.py` 16행: `MATCH (n)` — 라벨 없이 전체 노드를 스캔한 뒤 `nameKo CONTAINS $q` 또는 `toLower(name) CONTAINS toLower($q)` 필터링.
- `theographic_id` 인덱스는 `main.py`의 `lifespan`에서 생성하지만, `nameKo`·`name` 필드에는 별도 인덱스가 없다. `CONTAINS` 연산자는 인덱스를 활용하지 못하고 전체 노드를 순회한다.
- 데이터셋이 커질수록 검색 응답 시간이 O(n) 증가. 현재 DB 규모에서는 허용 가능하지만, fulltext 인덱스 미적용 상태가 기술 부채다.

### 2-2. `lru_cache` — 단일 프로세스 의존 + 캐시 무효화 불가
- `backend/app/routes/events.py`의 `_compute_events()`, `_load_approx_book_index()`, `_load_event_verses()` 및 `backend/app/routes/books.py`의 `_load_approx()`, `_load_book_events()` 모두 `functools.lru_cache(maxsize=1)`로 메모리에 고정.
- Dockerfile CMD가 `uvicorn` 단일 워커(`--workers` 미지정)이므로 지금은 동작한다. 만약 `--workers 2+` 또는 Gunicorn으로 전환하면 워커마다 독립 캐시를 가져 캐시 일관성이 깨진다.
- 데이터 파일(`data/event_verses/events.json` — 약 130,000줄) 또는 Neo4j 데이터를 갱신해도 서버 재시작 없이는 캐시가 갱신되지 않는다. 캐시 무효화 엔드포인트나 TTL이 없다.

### 2-3. `_compute_events()` 초기 기동 지연
- `_load_approx_book_index()`가 Neo4j 일괄 쿼리(모든 Book ID 조회)를 최초 호출 시 동기 실행한다. 앱 기동 직후 첫 `/events` 요청이 상대적으로 느릴 수 있다.
- lifespan hook에서 인덱스 생성만 하고 데이터 예열(warm-up)은 없다.

### 2-4. `MapView.jsx` — 링 애니메이션과 외부 타일 의존
- `backend/app/routes/nodes.py` 116행의 `/node/{id}/neighbors/grouped` 엔드포인트는 라벨 없는 `MATCH (n {theographic_id: $id})-[r]-(m)` 전체 이웃을 가져온다. `MAX_NEIGHBORS_PER_TYPE=30` 제한은 Python 레이어에서 하고 Cypher 레벨에서는 LIMIT가 없어, 이웃이 많은 노드(대형 인물 등)는 불필요한 데이터를 DB에서 가져온 뒤 버린다.
- `MapView.jsx` 38·43행: MapLibre 글리프(`protomaps.github.io`) 및 ESRI NatGeo 래스터 타일(`server.arcgisonline.com`)을 외부 CDN에서 직접 로드한다. 해당 서비스 중단·정책 변경 시 지도 전체가 렌더링 불가.

---

## 3. 기술 부채

### 3-1. 하드코딩된 Airtable 레코드 ID
- `backend/scripts/generate_approx_book_verses.py` 29~97행: `BOOK_VERSE_MAP` 딕셔너리에 Airtable theographic_id(`rec...` 14자리) 39개가 하드코딩.
- 원본 Airtable 데이터가 바뀌거나 레코드 ID가 재발급되면 스크립트 전체를 수동 갱신해야 한다. 이 매핑은 런타임이 아닌 스크립트 전용이므로 즉각 장애로 이어지지는 않지만, 재실행 시 잘못된 결과를 낼 위험이 있다.

### 3-2. 모바일 하단 시트 높이 마법 숫자 이중 관리
- `frontend/src/App.jsx` 17행의 `SHEET_VH = 55`와 `frontend/src/MapView.jsx` 411행의 `window.innerHeight * 0.55`가 별도 파일에서 동기화 없이 유지된다.
- 주석(`App.jsx SHEET_VH=55vh와 일치`)으로 경고하고 있지만, 공유 상수 모듈이 없어 한쪽을 바꾸면 다른 쪽을 놓치기 쉽다.

### 3-3. `import json as _json` 함수 내부 임포트
- `backend/app/routes/nodes.py` 240행: `Person` 트레잇 파싱을 위해 함수 내부에서 `import json as _json`을 매 호출마다 실행. 기능에 영향은 없지만 관례에 어긋난다.

### 3-4. `get_node_neighbors_grouped` 와 `get_node` 의 쿼리 중복
- `backend/app/routes/nodes.py`: `/node/{id}/neighbors/grouped`(116행)와 `/node/{id}`(151행 이후)가 각각 별도 DB 왕복으로 이웃을 가져온다. SidePanel은 `/node/{id}`만 호출하고, MapView 링 펼침은 `/neighbors/grouped`만 호출하므로 현재는 중복 호출이 없다. 그러나 두 엔드포인트의 이웃 데이터 구조(필드 명칭·순서)가 다르게 유지되어 향후 혼동 가능성이 있다.

### 3-5. 검색 응답에 `nameKoMissing` 필드 없음
- `backend/app/routes/search.py` 40행의 검색 결과 항목에는 `nameKoMissing` 필드가 없다.
- `frontend/src/SidePanel.jsx`는 `nameKoMissing`을 사용해 "(미번역)" 표시를 결정하지만, 검색 드롭다운(`App.jsx`)은 `nameKo`만 표시하므로 현재 UI에서는 문제가 없다. 추후 검색 결과에 동일 표시를 추가하려면 백엔드 응답도 함께 수정해야 한다.

---

## 4. 테스트 커버리지 부재

- 프로젝트 전체에 단위 테스트·통합 테스트 파일이 존재하지 않는다(`*.test.*`, `*.spec.*`, `test_*.py` 0건).
- 고위험 미검증 영역:
  - `backend/app/routes/search.py`: 특수문자(따옴표, 슬래시 등) 검색어가 Cypher에서 어떻게 처리되는지 테스트 없음. `$q` 파라미터 바인딩을 사용하므로 주입은 차단되지만, 빈 문자열·None 엣지케이스의 실제 쿼리 결과를 검증한 테스트가 없다.
  - `backend/app/routes/events.py`의 `_compute_events()`: 데이터 파일 누락·손상 시 폴백 거동이 테스트되지 않음.
  - `frontend/src/convexHull.js`: 동일 극각 중복점, 1점, 2점 케이스를 함수 내부 가드로만 처리하며 테스트 없음.
  - `MapView.jsx`의 링 애니메이션 타이머 경쟁(moveend + 700ms fallback): `fired` 플래그가 경쟁을 막지만, 실제 타이밍 시나리오에 대한 자동화 테스트 없음.

---

## 5. 기타 단편 위험

### 5-1. Neo4j 연결 오류 시 앱 전체 응답 불가
- `backend/app/db.py`에서 `NEO4J_PASSWORD` 미설정 시 `RuntimeError`를 발생시키고, `main.py` lifespan에서 인덱스 생성 실패는 `logging.exception`으로 무시하고 계속 진행한다. 하지만 실제 쿼리 엔드포인트에서는 DB 연결 실패 시 예외가 HTTP 500으로 전파된다. FastAPI의 기본 예외 핸들러가 처리하지만, 사용자에게 의미 있는 오류 메시지를 반환하는 커스텀 핸들러는 없다.

### 5-2. nginx TLS 미적용
- `nginx/nginx.conf`는 80 포트 HTTP만 설정. HTTPS 종단 처리가 nginx 외부(상위 리버스 프록시 또는 Cloudflare 등)에 위임되어 있다고 가정되는데, 이를 보장하는 코드·문서가 없다.

### 5-3. Book 노드 조회 시 다중 DB 왕복
- `backend/app/routes/nodes.py`에서 `Book` 라벨이면 `topPersons`(`209행`)와 `topEvents`(`223행`)를 각각 별도 쿼리로 추가 조회한다. 메인 노드 쿼리(`151행`) + 이웃 쿼리(`168행`) + 인물 쿼리 + 사건 쿼리 = 4회 왕복. 단일 트랜잭션이 아니므로 중간에 연결 오류 시 부분 응답 가능성이 있다.
