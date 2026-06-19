---
last_mapped_commit: 06b4012804c00a45ea7dfda9761d014ac11fb
mapped: 2026-06-20
---

# BibleMap 기술부채 및 리스크

## 1. 레트로에서 확인된 열린 이슈

### task-56 fix-forward (미실행, 백로그)
출처: `.forge/retro/2026-06-20-bible-overview-view.md`

- `genre=null`인 책이 `BibleOverviewView`에서 무음으로 사라짐 — null 방어 없음
- `backend/app/routes/books.py`의 `/books` 엔드포인트가 `startYear` 없는 책을 제외하는 타임라인 배치용 필터 로직을 포함하고 있어, `BibleOverviewView`가 일부 책을 표시하지 못함 (다중 소비자에게 오염된 필터)
- 빈 장르 섹션에 대한 빈 상태 UI 없음

### SidePanel.jsx lint 정책 미결
출처: `.forge/retro/2026-06-11-frontend-fetch-error-ui.md` 후속 섹션

- `frontend/src/SidePanel.jsx`의 기존 fetch-in-effect 패턴이 `react-hooks/exhaustive-deps` 룰 위반
- 정책 결정(룰 핀 vs. 리팩터) 보류 상태

---

## 2. 백엔드 API

### 2-1. 무제한 쿼리 (페이지네이션 없음)

**`GET /events`** — `backend/app/routes/events.py` lines 92–128

전체 Event 노드를 DB 레벨 LIMIT 없이 단일 Cypher 쿼리로 가져옴. 현재는 `lru_cache(maxsize=1)`로 1회만 실행되지만, `lru_cache`는 익셉션을 캐시하지 않아 첫 요청 실패 시 매 요청마다 재시도한다.

**`GET /books`** — `backend/app/routes/books.py` line 64

전체 Book 노드를 LIMIT 없이 조회. `Cache-Control: no-store` 설정이라 캐시도 없음.

**`GET /node/{node_id}/places` (PeopleGroup 경로)** — `backend/app/routes/nodes.py` lines 55–64

3-hop 조인(`PeopleGroup → Person → Event → Place`)에 LIMIT 없음. Python에서 `seen` set으로 중복 제거하지만 DB 전송 비용은 그대로.

**`GET /node/{node_id}/neighbors/grouped`** — `backend/app/routes/nodes.py` lines 110–112

쿼리에 LIMIT 없이 전체 이웃을 DB에서 가져온 뒤, Python에서 `MAX_NEIGHBORS_PER_TYPE = 30`으로 필터링. DB 레벨 LIMIT이 없어 관계가 많은 노드에서 불필요한 데이터가 전송됨.

### 2-2. 입력 검증 미흡

**`GET /search?q=`** — `backend/app/routes/search.py` line 9

`q` 길이 제한 없음. 매우 긴 문자열이 `CONTAINS $q`로 Cypher에 전달되면 Neo4j 전체 스캔 비용 증가. `max_length` 파라미터 없음.

**`GET /node/{node_id}` 계열** — `backend/app/routes/nodes.py`

`node_id`를 `str`로 받되 길이·패턴(Theographic ID 형식 `rec` + 14자) 검증 없음. 임의 문자열이 DB로 전달됨.

### 2-3. lru_cache + cold-start 위험

`backend/app/routes/events.py` lines 40–88

`_load_approx_book_index()`와 `_compute_events()`는 `lru_cache` 적용 중. Neo4j 미준비 상태에서 첫 요청이 오면 익셉션이 발생하고, `lru_cache`는 실패를 캐시하지 않으므로 이후 모든 요청이 DB 재연결을 시도함. `GET /events`가 연속 500을 반환하게 됨.

`docker-compose.yml` lines 22–23: `depends_on: neo4j`는 컨테이너 시작만 보장하고 Neo4j 준비는 보장하지 않음 (healthcheck 없음).

### 2-4. 에러 핸들링 누락

**`backend/app/routes/books.py` line 86**

`int(start_year)` 변환에 `try/except` 없음. `startYear`가 비정수 문자열이면 500 익셉션.

**`backend/app/routes/events.py`의 `_compute_events()`**

Neo4j 세션 오류 시 uncaught 익셉션 → FastAPI가 500 반환. 반복 실패 시 `lru_cache` 미캐시로 DB 부하 지속 증가.

---

## 3. 프론트엔드

### 3-1. BibleOverviewView — /books API 구조적 불일치

`frontend/src/BibleOverviewView.jsx` lines 88–103

- `/books` 엔드포인트는 `startYear` 없는 책을 제외하므로 66권 중 일부가 개요 뷰에 표시되지 않을 수 있음 (task-56 미처리)
- `book.genre`가 null이면 `grouped[key][null]`로 저장돼 `GENRE_META` 매핑 실패 → 무음 소멸
- `book.testament`가 null이면 `grouped[null]` 접근으로 TypeError 가능

### 3-2. TimelineView — 전체 이벤트 프론트 메모리 적재

`frontend/src/TimelineView.jsx` lines 44–47

전체 Event 목록을 메모리에 적재 후 `useMemo`로 필터링. 이벤트 수 증가 시 초기 로드 시간과 메모리 사용량이 선형 증가. 가상화(windowing)나 서버사이드 필터 없음.

### 3-3. MapView — 외부 타일 서비스 단일 의존

`frontend/src/MapView.jsx` lines 38–44

- ArcGIS ESRI NatGeo 타일: 상업 서비스로 사용량 제한·서비스 중단 위험
- Protomaps 글리프: 오픈소스 CDN으로 가용성 보장 없음
- 두 외부 서비스 중 하나라도 다운되면 지도 전체가 빈 화면

### 3-4. 에러 처리 일관성 미흡

`frontend/src/App.jsx` lines 55–60

`/person/{id}/event-ids` 실패 시 인물 필터가 조용히 null로 초기화. 사용자에게 에러 피드백 없음.

---

## 4. 보안 및 배포 설정

### 4-1. Docker 루트 실행

`backend/Dockerfile` 전체에 `USER` 지시어 없음. API 컨테이너가 root로 실행됨.

### 4-2. Docker healthcheck 없음

`docker-compose.yml`: `neo4j` 서비스에 `healthcheck` 없고, `api`의 `depends_on`에 `condition: service_healthy` 없음. 재시작 시 api가 Neo4j 준비 전에 요청을 받아 2-3절의 cold-start 문제 발생.

### 4-3. CORS 와일드카드

`backend/app/main.py` lines 27–28: `allow_origins=["*"]`. `allow_credentials=False`라 쿠키는 차단되지만 어떤 origin에서도 API 접근 가능.

### 4-4. nginx 프록시 타임아웃 없음

`nginx/nginx.conf`의 `/api/` location 블록에 `proxy_read_timeout`, `proxy_connect_timeout`, `proxy_send_timeout` 없음. 느린 Cypher 쿼리 시 nginx 기본값(60초) 적용.

---

## 5. 테스트 커버리지

**자동화 테스트 없음.** `pytest.ini`, `vitest.config.*`, `*.test.*`, `*.spec.*`, `test_*.py` 중 아무것도 존재하지 않음. 검증은 전적으로 Playwright 수동 스크린샷에 의존.

---

## 6. 우선순위 요약

| 우선순위 | 항목 | 위치 |
|---|---|---|
| 높음 | task-56 fix-forward (genre=null 소멸, /books 필터 오염) | `frontend/src/BibleOverviewView.jsx`, `backend/app/routes/books.py` |
| 높음 | docker-compose healthcheck 없음 → cold-start 500 | `docker-compose.yml` |
| 중간 | `/node/{id}/neighbors/grouped` DB 레벨 LIMIT 없음 | `backend/app/routes/nodes.py:110` |
| 중간 | `/node/{id}/places` PeopleGroup 3-hop 무제한 | `backend/app/routes/nodes.py:55` |
| 중간 | `search?q` 길이 제한 없음 | `backend/app/routes/search.py:9` |
| 중간 | `books.py` `int(start_year)` try/except 없음 | `backend/app/routes/books.py:86` |
| 중간 | Docker 루트 실행 | `backend/Dockerfile` |
| 낮음 | SidePanel.jsx lint 정책 미결 | 레트로 기록 |
| 낮음 | 외부 타일 단일 의존 (ArcGIS/Protomaps) | `frontend/src/MapView.jsx:38–44` |
| 낮음 | 자동화 테스트 커버리지 0% | 전체 |
