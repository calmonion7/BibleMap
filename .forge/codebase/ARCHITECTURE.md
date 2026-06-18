---
last_mapped_commit: 6f2cfc1bf163d7327bd86773676223624fa53ff2
mapped: 2026-06-18
---

# BibleMap — 아키텍처

## 전체 패턴

3계층 레이어드 아키텍처(Layered Architecture)를 Docker Compose로 단일 호스트에서 실행하는 구조다.

```
[브라우저]
    ↓ HTTP :8080
[nginx (리버스 프록시 + 정적 파일 서빙)]
    ↓ /api/* → proxy_pass http://api:8000/
[FastAPI (REST API)]
    ↓ bolt://neo4j:7687
[Neo4j 5 (그래프 데이터베이스)]
```

## 컨테이너 구성

`docker-compose.yml` 기준 3개 서비스가 단일 네트워크를 공유한다.

| 서비스 | 이미지/빌드 | 역할 |
|--------|------------|------|
| `neo4j` | `neo4j:5` | 그래프 DB. 포트 7474(HTTP), 7687(Bolt)을 127.0.0.1에만 노출 |
| `api` | `./backend` 빌드 | FastAPI REST API. 포트 8000 컨테이너 내부 전용. `./data`를 `/app/data`로 볼륨 마운트 |
| `nginx` | `nginx:alpine` | 정적 파일 서빙 + `/api/` 프록시. 포트 8080:80으로 외부 노출 |

## 레이어별 책임

### 데이터 계층 — Neo4j

- 모든 노드는 `theographic_id`(Airtable 레코드 ID) 속성을 가지며 각 레이블별 인덱스로 조회된다.
- 노드 레이블: `Person`, `Place`, `Event`, `PeopleGroup`, `Book`
- 주요 관계: `HAS_PARTICIPANT`, `OCCURS_AT`, `MEMBER_OF`, `PART_OF`, `CONTAINS_BOOK`
- `neo4j_data` named volume으로 영속화.
- 원본 데이터는 Theographic Bible Metadata GitHub 레포(JSON)에서 `backend/scripts/load_theographic.py`, `load_books.py` 등으로 임포트. 한 번 적재 후 스크립트를 재실행하거나 Neo4j에 직접 쓴다.

### API 계층 — FastAPI

- 진입점: `backend/app/main.py`
- DB 드라이버 싱글턴: `backend/app/db.py` (`get_driver()` — 최초 호출 시 초기화, 이후 재사용)
- 라우터: `backend/app/routes/` 아래 4개 파일로 수직 분할. 모든 엔드포인트는 GET 전용. CORS는 전체 허용(`allow_origins=["*"]`).
- 앱 시작 시 `lifespan` 훅에서 5개 레이블 인덱스를 `CREATE IF NOT EXISTS`로 생성.
- uvicorn으로 실행 (`CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]`)

### 프록시 계층 — nginx

- `nginx/nginx.conf`: `/api/` 경로를 `http://api:8000/`으로 프록시. (슬래시 정규화 포함)
- `index.html`은 `no-cache`, JS/CSS/이미지는 `max-age=31536000 immutable` 캐시 정책.
- SPA 라우팅: `try_files $uri /index.html` — 모든 미매핑 경로를 `index.html`로 폴백.
- 정적 파일 루트: `frontend/dist` 디렉터리 (`:ro` 마운트).

### 프론트엔드 계층 — React SPA

- 빌드: Vite + React 19. 빌드 결과물이 `frontend/dist/`에 생성되어 nginx가 서빙한다(HMR 아님).
- `frontend/.env.production`에서 `VITE_API_URL=/api` 빌드타임 주입 → `api.js`의 `API_BASE`가 nginx 상대 경로를 사용. 개발 시에는 `http://localhost:8000` 폴백.
- 청크 분할: `vite.config.js`의 `manualChunks` — `maplibre-gl` → `maplibre`, 나머지 `node_modules` → `vendor`.

## 데이터 흐름 — 요청 경로

### 일반 GET 요청 (예: 사건 목록)

```
브라우저 fetch("/api/events")
  → nginx: /api/* → proxy_pass http://api:8000/events
    → FastAPI events.router: GET /events
      → Neo4j Bolt: MATCH (e:Event) ...
      → JSON 응답 반환
    → FastAPI가 JSONResponse 반환
  → nginx proxy 전달
→ 브라우저 수신
```

### 오버레이 JSON (추정연도·사건 근거 구절)

API 레이어의 `books.py`, `events.py`는 Neo4j 응답에 로컬 JSON 오버레이를 병합해 반환한다.
- `data/book_years_approx/books.json` — `startYear`가 없는 책의 추정 배치연도 오버레이
- `data/book_events/books.json` — 추정연도 31권과 타임라인 사건의 약한 연결 오버레이
- `data/event_verses/events.json` — 사건별 근거 구절(권·범위·본문) 오버레이

오버레이 파일은 `functools.lru_cache(maxsize=1)`로 프로세스 생존 중 1회만 메모리에 적재된다.
파일 탐색 순서는 `DATA_DIR` 환경변수(Docker 볼륨 `/app/data`) → 레포 상대경로(`data/`) 폴백.

## 핵심 추상

### `theographic_id` 식별자

모든 Neo4j 노드의 1차 키. `rec` 접두사 문자열(Theographic 레코드) 또는 저작 사건은 `authored-<slug>` 형식. 프론트엔드 `selectedNode` 상태, API URL 파라미터, JSON 오버레이 키로 일관되게 사용된다.

### `apiGet(path)` — `frontend/src/api.js`

프론트엔드 fetch 단일 진입점. `VITE_API_URL` 베이스에 path를 붙여 GET 요청, 비-OK 시 status 코드로 reject. `AbortController.signal` 옵션을 지원해 컴포넌트 unmount 또는 재선택 시 in-flight 요청을 취소한다.

### `selectedNode` 전역 상태

`App.jsx`가 관리하는 현재 선택 엔티티 ID(`theographic_id` 문자열). `MapView`, `SidePanel`, `TimelineView`가 props로 공유. 변경 시 이전 노드를 `history` 배열에 push해 SidePanel 뒤로가기를 지원한다.

## 빌드 타임 데이터 파이프라인

`backend/scripts/`에 위치한 일회성 스크립트들은 Neo4j 또는 `data/` JSON에 쓰는 데이터 준비 파이프라인이다. 애플리케이션 런타임과 무관하며, 데이터 재생성 시에만 실행한다.

| 스크립트 | 대상 |
|---------|------|
| `load_theographic.py` | Neo4j: Person/Place/Event/PeopleGroup 노드·관계 |
| `load_books.py` | Neo4j: Book 노드 + `CONTAINS_BOOK` 관계 |
| `inject_ko_names.py` | Neo4j: `nameKo` 속성 주입 |
| `inject_person_traits.py` | Neo4j: `traits` 속성 주입 |
| `inject_book_context.py` | Neo4j: `background`/`themes`/`keyVerse` 속성 주입 |
| `load_authored_events.py` | Neo4j: 저작 사건 Event 노드 (`authored:true`) |
| `generate_verse_text.py` | `data/event_verses/events.json` — 구절 본문 빌드타임 프리베이크 |
| `generate_approx_book_verses.py` | `data/event_verses/` 추정책 구절 데이터 |
| `generate_book_events.py` | `data/book_events/books.json` |
| `generate_book_context.py` | `data/book_context/books.json` |
| `generate_person_traits.py` | `data/character_traits/people.json` |
| `generate_event_verses.py` | `data/event_verses/events.json` |
