---
last_mapped_commit: cecf0d7de87192b638f428eb7e708e94a58214a6
mapped: 2026-06-20
---

# BibleMap 기술부채 및 리스크

## 1. 열린 이슈 (백로그 및 레트로 기록)

### task-59 백로그 — TimelineView.jsx lint 오류 (미실행)

출처: `.forge/backlog/fix-timelineview-lint.md`

`npm run lint` 결과 **error 1건 + warning 1건**.

- `frontend/src/TimelineView.jsx` line 86: `visibleGroups` 구조분해 후 사용처 없음 → `no-unused-vars` error
- `frontend/src/TimelineView.jsx` line 99: `useMemo` 의존성 배열에 `activeFilter`, `activePersonFilter` 누락 → `react-hooks/exhaustive-deps` warning

수정 방법은 `.forge/backlog/fix-timelineview-lint.md`에 S1·S2로 명시돼 있음.

### task-56 fix-forward (미실행, 레트로 기록)

출처: `.forge/retro/2026-06-20-bible-overview-view.md`

- `frontend/src/BibleOverviewView.jsx` lines 88–103: `book.genre`가 null이면 `GENRE_META` 매핑 실패 → 무음 소멸
- `backend/app/routes/books.py` line 54: `startYear`·추정연도 모두 없는 책은 `continue`로 제외. `/books-overview` 엔드포인트 도입으로 개요 뷰는 별도 엔드포인트로 분리됐으나, `/books` 호출 시 해당 책이 여전히 누락됨
- 빈 장르 섹션에 빈 상태 UI 없음

### SidePanel.jsx lint 정책 미결

출처: `.forge/retro/2026-06-11-frontend-fetch-error-ui.md`

- `frontend/src/SidePanel.jsx` line 50–57: `useEffect` 내 `onNodeLoaded`가 deps 배열에 포함돼 있으나, 호출자가 인라인 함수로 전달하면 무한 재실행 위험. 정책 결정(룰 핀 vs. 리팩터) 보류 상태.

---

## 2. 백엔드 API

### 2-1. 무제한 쿼리 (페이지네이션 없음)

**`GET /events`** — `backend/app/routes/events.py` lines 54–86

전체 Event 노드를 DB 레벨 LIMIT 없이 단일 Cypher 쿼리로 가져옴. `lru_cache(maxsize=1)`로 첫 호출 후 메모리에 보관하지만, `lru_cache`는 예외를 캐시하지 않아 첫 요청 실패 시 매 요청마다 DB 재연결을 시도함.

**`GET /books`** / **`GET /books-overview`** — `backend/app/routes/books.py` lines 14–72

전체 Book 노드를 LIMIT 없이 조회. `Cache-Control: no-store`로 캐시 없음.

**`GET /node/{node_id}/places` (PeopleGroup 경로)** — `backend/app/routes/nodes.py` lines 53–64

3-hop 조인(`PeopleGroup → Person → Event → Place`)에 LIMIT 없음. Python에서 `seen` set으로 중복 제거하지만 DB 전송 비용은 그대로.

**`GET /node/{node_id}/neighbors/grouped`** — `backend/app/routes/nodes.py` lines 111–142

Cypher에 LIMIT 없이 전체 이웃을 가져온 뒤 Python에서 `MAX_NEIGHBORS_PER_TYPE = 30`으로 필터링. (참고: `/node/{node_id}` 엔드포인트는 `NODE_NEIGHBOR_LIMIT = 50`을 DB 레벨 슬라이스로 적용하므로 이 항목은 `/neighbors/grouped` 전용 문제임.)

### 2-2. 입력 검증 미흡

**`GET /search?q=`** — `backend/app/routes/search.py` line 9

`q` 길이 제한 없음. 매우 긴 문자열이 `CONTAINS $q`로 Cypher에 전달되면 Neo4j 전체 스캔 비용 증가.

**`GET /node/{node_id}` 계열** — `backend/app/routes/nodes.py`

`node_id`를 `str`로 받되 길이·패턴 검증 없음. 임의 문자열이 DB로 전달됨.

### 2-3. lru_cache + cold-start 위험

`backend/app/routes/events.py` lines 11–50

`_load_approx_book_index()`와 `_compute_events()`는 `lru_cache` 적용 중. Neo4j 미준비 상태에서 첫 요청이 오면 예외가 발생하고, `lru_cache`는 실패를 캐시하지 않으므로 이후 모든 요청이 DB 재연결을 시도함. `GET /events`가 연속 500을 반환함.

`docker-compose.yml` lines 21–23: `depends_on: neo4j`는 컨테이너 시작만 보장하고 Neo4j 준비는 보장하지 않음 (healthcheck 없음).

### 2-4. 에러 핸들링 누락

**`backend/app/routes/books.py` line 62**

`int(start_year)` 변환에 `try/except` 없음. `startYear`가 비정수 문자열이면 500 예외. 현재는 Neo4j 속성값과 JSON 오버레이(`placementYear`) 모두 숫자이므로 실사용 위험은 낮으나 방어 코드 없음.

**`backend/app/routes/events.py`의 `_compute_events()`**

Neo4j 세션 오류 시 uncaught 예외 → FastAPI가 500 반환. 반복 실패 시 `lru_cache` 미캐시로 DB 부하 지속 증가.

---

## 3. 프론트엔드

### 3-1. BibleOverviewView — /books-overview의 null 방어 미흡

`frontend/src/BibleOverviewView.jsx` lines 88–103

- `book.genre`가 null이면 `GENRE_META` 매핑 실패 → 무음 소멸 (task-56 미처리)
- `book.testament`가 null이면 `grouped[null]` 접근으로 TypeError 가능

### 3-2. TimelineView — 전체 이벤트 프론트 메모리 적재

`frontend/src/TimelineView.jsx` lines 46–50

전체 Event 목록을 메모리에 적재 후 `useMemo`로 필터링. 이벤트 수 증가 시 초기 로드 시간과 메모리 사용량이 선형 증가. 가상화(windowing)나 서버사이드 필터 없음.

### 3-3. MapView — 외부 타일 서비스 단일 의존

`frontend/src/MapView.jsx` lines 38–44

- ArcGIS ESRI NatGeo 타일: 상업 서비스로 사용량 제한·서비스 중단 위험
- Protomaps 글리프: 오픈소스 CDN으로 가용성 보장 없음
- 두 외부 서비스 중 하나라도 다운되면 지도 전체가 빈 화면

### 3-4. 에러 처리 일관성 미흡

`frontend/src/App.jsx` lines 55–60

`/person/{id}/event-ids` 실패 시 인물 필터가 조용히 null로 초기화. 사용자에게 에러 피드백 없음.

### 3-5. maplibre 청크 크기 경고

`frontend/vite.config.js`

빌드 시 `dist/assets/maplibre-*.js`가 **1,027 kB** (gzip 272 kB). Vite가 500 kB 초과 경고 출력. `manualChunks`로 maplibre를 별도 청크로 분리했으나 청크 자체 크기는 줄지 않음. 초기 로드 시 1 MB 파싱 비용 발생.

---

## 4. 빌드·배포 프로세스

### 4-1. frontend/dist 수동 빌드 필요

`docker-compose.yml` line 30–31: nginx가 `./frontend/dist`를 read-only 마운트. HMR 없음. 프론트엔드 변경 후 반드시 `cd frontend && npm run build` + `docker compose up -d nginx`(또는 전체 재시작)가 필요. 빌드 없이 배포하면 구 버전 서빙.

---

## 5. 보안 및 배포 설정

### 5-1. Docker 루트 실행

`backend/Dockerfile` 전체에 `USER` 지시어 없음. API 컨테이너가 root로 실행됨.

### 5-2. Docker healthcheck 없음

`docker-compose.yml`: `neo4j` 서비스에 `healthcheck` 없고, `api`의 `depends_on`에 `condition: service_healthy` 없음. 재시작 시 api가 Neo4j 준비 전에 요청을 받아 2-3항의 cold-start 문제 발생.

### 5-3. CORS 와일드카드

`backend/app/main.py` lines 27–28: `allow_origins=["*"]`. `allow_credentials=False`라 쿠키는 차단되지만 어떤 origin에서도 API 접근 가능.

### 5-4. nginx 프록시 타임아웃 없음

`nginx/nginx.conf`의 `/api/` location 블록에 `proxy_read_timeout`, `proxy_connect_timeout`, `proxy_send_timeout` 없음. 느린 Cypher 쿼리 시 nginx 기본값(60초) 적용.

---

## 6. 테스트 커버리지

**자동화 테스트 없음.** `pytest.ini`, `vitest.config.*`, `*.test.*`, `*.spec.*`, `test_*.py` 중 아무것도 존재하지 않음. 검증은 전적으로 Playwright 수동 스크린샷에 의존.

---

## 7. 우선순위 요약

| 우선순위 | 항목 | 위치 |
|---|---|---|
| 높음 | task-59: TimelineView lint error (eslint 빌드 차단 가능) | `frontend/src/TimelineView.jsx:86,99` |
| 높음 | task-56: genre=null 무음 소멸·빈 상태 UI | `frontend/src/BibleOverviewView.jsx:88–103` |
| 높음 | docker-compose healthcheck 없음 → cold-start 500 | `docker-compose.yml` |
| 중간 | `/node/{id}/neighbors/grouped` DB 레벨 LIMIT 없음 | `backend/app/routes/nodes.py:116` |
| 중간 | `/node/{id}/places` PeopleGroup 3-hop 무제한 | `backend/app/routes/nodes.py:55–64` |
| 중간 | `search?q` 길이 제한 없음 | `backend/app/routes/search.py:9` |
| 중간 | `books.py` `int(start_year)` try/except 없음 | `backend/app/routes/books.py:62` |
| 중간 | Docker 루트 실행 | `backend/Dockerfile` |
| 중간 | maplibre 청크 1,027 kB 경고 | `frontend/vite.config.js` |
| 낮음 | frontend/dist 수동 빌드 요구 (HMR 없음) | `docker-compose.yml`, `frontend/` |
| 낮음 | SidePanel.jsx lint 정책 미결 | `frontend/src/SidePanel.jsx:50–57` |
| 낮음 | 외부 타일 단일 의존 (ArcGIS/Protomaps) | `frontend/src/MapView.jsx:38–44` |
| 낮음 | 자동화 테스트 커버리지 0% | 전체 |
