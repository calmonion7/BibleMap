---
last_mapped_commit: ff728ccaffbb9b4e38f1f8f32859a50d3555b515
mapped: 2026-06-20
---

# CONCERNS.md — 기술 부채 및 위험 영역

## 보안 취약점

### S1 · CORS 와일드카드 (`allow_origins=["*"]`)
- 파일: `backend/app/main.py` line 27
- 현재는 읽기 전용 공개 API라 실제 피해는 없지만, 미래에 인증이 필요한 엔드포인트를 추가할 경우 Credential-bearing 요청이 불가능해 전면 재작업이 필요하다.

### S2 · nginx 보안 헤더 전무
- 파일: `nginx/nginx.conf`
- `X-Frame-Options`, `X-Content-Type-Options`, `Content-Security-Policy`, `Referrer-Policy` 모두 없음. 외부 타일 소스(ESRI, `protomaps.github.io`)를 허용하는 CSP라도 있어야 한다.

### S3 · API 레이트 리미팅 없음
- 파일: `backend/app/main.py` (전 라우트)
- nginx 레벨도, FastAPI 레벨도 IP 기반 스로틀이 없다. `/events`, `/node/{id}`, `/search` 전부 무제한 호출 가능.

### S4 · 취약한 Neo4j 비밀번호 (.env)
- 파일: `.env` line 1 (`NEO4J_PASSWORD=biblemap123`)
- `.gitignore`에 포함돼 있어 유출 위험은 낮지만, docker-compose에서 포트 `7687`이 외부에 노출될 경우 즉시 크래킹된다. 현재는 `127.0.0.1` 바인딩 중.

### S5 · Docker 이미지 태그 부동(Floating)
- 파일: `docker-compose.yml` lines 3, 22
- `neo4j:5`, `nginx:alpine` 둘 다 floating 태그. CI나 `docker-compose pull` 시 내부 버전이 조용히 변경될 수 있다. `neo4j:5.26`, `nginx:1.27-alpine` 처럼 마이너 버전 고정 권장.

### S6 · `NODE_NEIGHBOR_LIMIT` f-string이 Cypher 인젝션처럼 보임
- 파일: `backend/app/routes/nodes.py` line 169
- 실제 상수라 주입 불가능하지만 자동화 보안 스캐너가 플래그를 세울 수 있다. 별도 변수로 분리하면 해소.

---

## 성능 병목

### P1 · `/node/{id}/neighbors/grouped` — Cypher에 LIMIT 없음 ★
- 파일: `backend/app/routes/nodes.py` lines 115–116
- `MATCH (n {theographic_id: $id})-[r]-(m) RETURN m, type(r) AS rel, labels(m) AS mlabels` — LIMIT 절 없음.
- Python 쪽 `MAX_NEIGHBORS_PER_TYPE=30` cap이 있지만, Neo4j는 전체 엣지를 Bolt로 전송한 뒤 Python이 버린다. 예루살렘 같은 고연결 노드는 수백 건의 불필요 직렬화가 발생.
- 수정 방향: Cypher에 `LIMIT 200` 추가, 또는 `get_node`에서 쓰는 `collect()[0..N]` 패턴 적용.

### P2 · `/node/{id}/places` (PeopleGroup·Book 경로) — Cypher에 LIMIT 없음
- 파일: `backend/app/routes/nodes.py` lines 53–72
- PeopleGroup 경로는 `MEMBER_OF → HAS_PARTICIPANT → OCCURS_AT`, Book 경로는 `CONTAINS_BOOK → OCCURS_AT` 를 전량 페치 후 Python에서 dedup만 한다. 대형 인물 그룹이나 편수 많은 책에서 전량 반환.

### P3 · `/books`, `/books-overview` 캐시 없음
- 파일: `backend/app/routes/books.py` lines 15, 40
- 두 엔드포인트 모두 요청마다 `MATCH (b:Book) RETURN b ORDER BY b.bookOrder ASC` 를 실행한다. `events` 라우트가 `@functools.lru_cache(maxsize=1)`를 쓰는 것과 달리 전혀 캐싱하지 않음. 66권 정적 데이터라 `lru_cache` 한 줄이면 해소.

### P4 · Book 노드 조회 시 Neo4j 세션 4회 개통
- 파일: `backend/app/routes/nodes.py` lines 148–236
- 노드 본체, neighbors, topPersons, topEvents 각각 별도 세션. 파이프라인 또는 단일 세션으로 통합 가능.

### P5 · 7.6 MB `events.json` 전량 메모리 적재
- 파일: `backend/app/overlays.py` line 43, `data/event_verses/events.json`
- `lru_cache`로 전체를 메모리에 유지. 현재 457건은 무방하지만 task 주기마다 파일이 커져 장기적으로 서버 메모리 압박 요인.

### P6 · TimelineView 가상화 없음
- 파일: `frontend/src/TimelineView.jsx` line 273+
- 모든 타임라인 그룹을 동시 렌더링. 이벤트 수가 늘어나면 스크롤 jank 발생. `react-window` 또는 `IntersectionObserver` 기반 지연 렌더링 없음.

---

## 알려진 버그 / 오류 처리 공백

### E1 · `goBack()`이 `personEventIds` 초기화 안 함
- 파일: `frontend/src/useNodeSelection.js` lines 49–52
- `goBack()`이 `selectedNode`를 히스토리에서 복원하지만 `selectedNodeMeta`·`personEventIds`는 초기화하지 않는다. Person → Place → goBack() 시퀀스에서 `TimelineView`의 personFilter가 stale 데이터로 남을 수 있다. `handleNodeLoaded`가 호출되면 해소되지만 그 전까지 잘못된 필터가 적용된 상태로 렌더링.

### E2 · `overlays._load()` JSON 파싱 실패 시 `{}` 반환 후 무음 진행
- 파일: `backend/app/overlays.py` lines 19–27
- `books.json` 또는 `events.json` 파일이 손상되면 빈 dict 반환 후 로그 없이 계속 동작. 결과적으로 `yearApprox` 없는 책들이 타임라인에서 조용히 누락.

### E3 · SidePanel API 오류 시 재시도 없음
- 파일: `frontend/src/SidePanel.jsx` line 67
- API 실패 시 정적 한국어 에러 문자열("불러오지 못했습니다 (404)")만 표시, 재시도 버튼 없음. 마커를 다시 클릭해야만 복구 가능. `ErrorBoundary`도 없음.

### E4 · `generate_book_events.py` — API 키 검증 전 Neo4j 조회 실행
- 파일: `backend/scripts/generate_book_events.py` lines 36–46, 88–92
- Neo4j에서 데이터를 모두 페치한 뒤 `ANTHROPIC_API_KEY` 를 확인. API 키 누락 시 Neo4j 왕복이 낭비.

---

## 취약 구조 / 복잡도

### F1 · `MapView.jsx` — 485줄, 복잡도 최고 ★
- 파일: `frontend/src/MapView.jsx`
- 지도 초기화, `requestAnimationFrame` 애니메이션 루프, 이벤트 링 확장/축소 상태 머신, 장소 선택, 마커 클릭 핸들러가 한 컴포넌트에 집중. `useEffect` 내부 클로저로 `animFrame`, `expandedPlace`, `destroyed` ref 관리 — 정확하지만 디버깅 어려움. 훅 21개 사용.

### F2 · `SidePanel.jsx` — 인라인 스타일 57개
- 파일: `frontend/src/SidePanel.jsx`
- 전체 레이아웃이 `style={{...}}` 인라인. CSS 클래스 없음. 테마 변경이나 반응형 조정 시 전면 교체 필요.

### F3 · `lru_cache` 이중 의존으로 캐시 무효화 불가
- 파일: `backend/app/routes/events.py` lines 11–53
- `_load_approx_book_index()`와 `_compute_events()`가 각각 독립적으로 `lru_cache` 적용. 디스크의 `books.json`이 변경돼도 프로세스 재시작 없이는 두 캐시 모두 갱신 안 됨.

### F4 · `load_theographic.py` — 320줄 단일 ETL 스크립트
- 파일: `backend/scripts/load_theographic.py`
- 스키마 인덱스 생성, 엔티티 병렬 페치, 배치 MERGE, 관계 구성이 한 파일. 일회성 ETL이라 허용 범위지만 수정 시 사이드 이펙트 추적 어려움.

---

## 번들 크기 / 프론트엔드 의존성

### B1 · 외부 타일/글리프 호스트 단일 장애점
- 파일: `frontend/src/MapView.jsx`
- ESRI 타일 URL과 `protomaps.github.io` 글리프 URL이 하드코딩. 해당 호스트 장애 시 지도가 전체 불능. fallback 없음.

### B2 · `frontend/package-lock.json` 커밋 여부 불명확
- 파일: `frontend/package.json`
- 의존성이 `^` 부동 버전(`react@^19.2.6`, `maplibre-gl@^5.24.0`, `vite@^8.0.12`). lock 파일이 git에 없으면 CI `npm install` 마다 버전이 달라질 수 있다.

### B3 · `frontend/src/assets/hero.png` 사용 여부 불명확
- 파일: `frontend/src/assets/hero.png`
- 소스 파일 어디서도 참조가 확인되지 않음. 미사용 바이너리 자산일 가능성.

---

## 의존성 위험

### D1 · 자동화된 취약점 스캔 없음
- `dependabot.yml`, `renovate.json`, `pip-audit`, `npm audit` CI 단계 없음. `.github/workflows/` 디렉터리 자체가 없다.

### D2 · Python 의존성 버전 핀닝 확인 필요
- 파일: `backend/requirements.txt`
- `fastapi==0.136.3`, `neo4j==6.2.0`, `uvicorn==0.49.0` — 버전 번호가 매우 높음(2025–2026 추정). PyPI 실제 존재 여부 및 최신 CVE 확인 권장. `pip-audit` 미설정.
