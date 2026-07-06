---
last_mapped_commit: 95ba754e0a5b8a8db6f537f88d6d4e60d302d066
mapped: 2026-07-06
---

# Technology Stack

## 언어 및 런타임

**주요 언어:**
- Python 3.12 — 백엔드 API 및 데이터 파이프라인 스크립트 (`backend/app/`, `backend/scripts/`)
- JavaScript (ES modules, JSX) — 프론트엔드 SPA (`frontend/src/`). TypeScript 미사용, `@types/react`만 devDependency로 존재

**보조 언어:**
- Bash — 배포 스크립트 (`deploy.sh`)
- Cypher — Neo4j 쿼리 (라우트·로더 스크립트 내 인라인 문자열)

**패키지 매니저:**
- Python: pip (`backend/requirements.txt`, 버전 고정 명시, lockfile 없음)
- Node: npm (`frontend/package-lock.json` lockfileVersion 3)

## 백엔드

### 프레임워크 및 핵심 의존성

`backend/requirements.txt`에 세 패키지만 선언한다.

| 패키지 | 버전 | 역할 |
|---|---|---|
| `fastapi` | 0.136.3 | REST API 프레임워크 |
| `neo4j` | 6.2.0 | Neo4j Python 드라이버 |
| `uvicorn` | 0.49.0 | ASGI 서버 |

컨테이너 이미지: `python:3.12-slim` (`backend/Dockerfile`). 진입점: `uvicorn app.main:app --host 0.0.0.0 --port 8000`.

### 애플리케이션 구조

진입점 `backend/app/main.py`. `lifespan` 컨텍스트 매니저에서 Person/Place/Event/PeopleGroup/Book 다섯 레이블의 `theographic_id`에 인덱스를 생성하고, CORS 미들웨어를 `allow_origins=["*"]` / 메서드 GET 전용으로 등록한다.

DB 연결은 `backend/app/db.py`의 모듈 전역 싱글턴 `_driver`. `NEO4J_URI` / `NEO4J_USER` / `NEO4J_PASSWORD` 환경변수를 읽고, `NEO4J_PASSWORD` 미설정 시 `RuntimeError` 발생.

데이터 파일 경로 해석은 `backend/app/overlays.py`. `DATA_DIR` 환경변수(기본 `/app/data`)를 먼저, 없으면 레포 상대 `data/`를 탐색한다. `functools.lru_cache`로 프로세스당 1회 캐시.

등록된 라우터 (`backend/app/routes/`):

- `nodes.py` — `GET /node/{node_id}`, `/node/{node_id}/places`, `/node/{node_id}/neighbors/grouped`, `/person/{node_id}/event-ids`
- `events.py` — `GET /events`, `/event/{event_id}/verses`
- `search.py` — `GET /search?q=` (nameKo/name 전문 검색, limit 20)
- `books.py` — `GET /books-overview`
- `persons.py` — `GET /persons/curated` (34인 목록), `/person/{node_id}/connections`
- `journey.py` — `GET /person/{person_id}/journey`
- `places.py` — `GET /place/{place_id}/curated-persons`
- `tours.py` — `GET /tours`, `GET /tour/{tour_id}` (이벤트 ID → 좌표 포함 stop 보강)

### seed/파이프라인 스크립트

`backend/scripts/`에 20개 스크립트. 역할별 분류:

**Theographic 데이터 로드 (초기 1회)**
- `load_theographic.py` — robertrouse/theographic-bible-metadata GitHub raw JSON 4개(people, places, events, peopleGroups)를 `urllib`로 fetch, Neo4j 일괄 삽입. 배치 크기: 노드 500, 관계 1000.
- `load_books.py`, `load_authored_events.py`, `load_authored_persons.py`, `load_person_events.py`, `load_verse_events.py`

**데이터 생성 (빌드타임 사전 계산)**
- `generate_book_events.py`, `generate_event_verses.py`, `generate_verse_events.py`
- `generate_verse_text.py` — getbible v2 API로 `korean`·`kjv` 번역 본문 prebake. 이미 text가 있는 항목은 건너뜀(멱등).
- `generate_book_context.py`, `generate_book_context_enrich.py`, `generate_approx_book_verses.py`
- `generate_person_event_verses.py`, `generate_person_traits.py`
- `enrich_place_coords.py`

**Neo4j 주입 (배포 시마다)**
- `inject_ko_names.py` — `data/names_ko/*.json`에서 `nameKo`·`aliasesKo`를 읽어 Person·Place 노드에 쓴다. `deploy.sh` 4단계에서 Neo4j 준비까지 최대 15회(2초 간격) 재시도.
- `inject_book_context.py`, `inject_person_traits.py`, `inject_place_context.py`

**빌드타임 LLM 사용 (런타임 불필요):**
- `generate_book_context.py`, `generate_person_traits.py`, `generate_book_events.py`, `generate_verse_events.py` 등이 `anthropic` Python SDK(모델 `claude-haiku-4-5-20251001`)를 호출. `ANTHROPIC_API_KEY` 환경변수 필요. `requirements.txt`에는 미포함(별도 설치).

## 프론트엔드

### 프레임워크 및 핵심 의존성

`frontend/package.json` 선언 기준:

| 패키지 | 버전 범위 | 역할 |
|---|---|---|
| `react` | ^19.2.6 | UI 프레임워크 |
| `react-dom` | ^19.2.6 | DOM 렌더러 |
| `maplibre-gl` | ^5.24.0 | WebGL 지도 렌더링 |
| `lucide-react` | ^1.17.0 | 아이콘 컴포넌트 |

### 빌드 도구

- **Vite** ^8.0.12 + **@vitejs/plugin-react** ^6.0.1 (`frontend/vite.config.js`). Vite 8는 rolldown 기반 번들러.
- 수동 청크 분리: `maplibre-gl` → `maplibre` 청크, 나머지 `node_modules` → `vendor` 청크.
- `npm run dev` — HMR dev 서버. `npm run build` → `frontend/dist/`.
- 프로덕션에서 nginx는 `dist/`를 `/usr/share/nginx/html`로 read-only 마운트한다. **HMR 아님 — 검증 전 반드시 `npm run build` 필요.**

### API 연결

`frontend/src/api.js`의 `apiGet(path)` 단일 함수가 모든 백엔드 호출을 담당한다. `VITE_API_URL` 빌드타임 변수(`frontend/.env.production`에 `/api`)를 베이스 URL로 사용. 런타임 외부 API 호출 없음.

### 소스 파일 구조

`frontend/src/` 주요 파일:

- `App.jsx` — 최상위 컴포넌트. 스테이지(`hub`→`explore`|`overview`|`tours`) 진입점.
- `useStageNavigation.js` — 내비게이션·히스토리 상태 머신 훅 (task 124에서 App.jsx로부터 추출).
- `useNodeSelection.js` — 노드 선택 상태 훅
- `urlState.js` — 해시 기반 딥링크, URL↔내비 상태 동기화 (task 122)
- `MapView.jsx` — maplibre-gl 지도 뷰
- `mapGeo.js`, `mapLayers.js`, `mapRingController.js` — 지도 레이어·지오메트리·링 컨트롤러
- `SidePanel.jsx` — 사이드패널 / 모바일 바텀시트
- `PersonHub.jsx` — 인물 허브 뷰
- `JourneyList.jsx` — 여정 목록
- `TourList.jsx` — 큐레이션 여정(tours) 목록
- `BibleOverviewView.jsx` — 성경 개요 뷰
- `TimelineView.jsx` — 타임라인 뷰
- `EventVerses.jsx`, `VerseLangTabs.jsx` — 이벤트 절·언어 탭
- `api.js`, `constants.js`, `dates.js`, `theme.js` — 유틸리티
- `Spinner.jsx` — 로딩 스피너

상수 (`frontend/src/constants.js`): `MOBILE_BREAKPOINT=768px`, `SHEET_VH=75vh`, `JOURNEY_SHEET_VH=42dvh`.

**Lint:** ESLint 10.3 flat config (`frontend/eslint.config.js`). Prettier 설정 없음. 자동화 테스트 프레임워크 미검출(*.test.*/vitest/jest 없음).

## 인프라 및 배포

### Docker Compose

루트 `docker-compose.yml`이 세 서비스를 정의한다.

| 서비스 | 이미지/빌드 | 노출 포트 |
|---|---|---|
| `neo4j` | `neo4j:5` | 127.0.0.1:7474, 127.0.0.1:7687 |
| `api` | `./backend` 빌드 | 외부 미노출 |
| `nginx` | `nginx:alpine` | 8080→80 |

`api` 서비스는 `./data`를 컨테이너 `/app/data`로 마운트. `neo4j_data` 네임드 볼륨으로 영속성 유지. 프로젝트명 `-p biblemap`.

### nginx

`nginx/nginx.conf`:
- `location /api/` → `proxy_pass http://api:8000/` (path strip, X-Real-IP·X-Forwarded 헤더 전달)
- `location = /index.html` → `Cache-Control: no-cache, no-store, must-revalidate`
- `location ~* .(js|css|…)$` → `Cache-Control: public, max-age=31536000, immutable`
- `location /` → SPA fallback `try_files $uri /index.html`

### deploy.sh

루트 `deploy.sh` 4단계:
1. 잠금 파일 `/tmp/biblemap-deploy.lock` 획득. 로그 `/Users/calmonion/Library/Logs/com.biblemap.deploy.log` tee.
2. macOS 키체인 우회: 임시 `DOCKER_CONFIG` 디렉터리 + `~/.docker/cli-plugins` 심링크 생성.
3. `cd frontend && npm install && npm run build`
4. `docker compose -p biblemap build api` → `up -d api nginx`
5. `inject_ko_names.py` 최대 15회 재시도 (2초 간격, Neo4j 준비 대기).

### GitHub Actions

`.github/workflows/deploy.yml`: `main` push → `self-hosted` 러너 → `git reset --hard origin/main` → `bash deploy.sh`.

## 환경 변수

**백엔드 런타임:**
- `NEO4J_URI` — 기본 `bolt://localhost:7687`, compose에서 `bolt://neo4j:7687`
- `NEO4J_USER` — 기본 `neo4j`
- `NEO4J_PASSWORD` — 필수. 미설정 시 `RuntimeError`
- `DATA_DIR` — 오버레이 경로, 기본 `/app/data`

**데이터 생성 스크립트 (빌드타임):**
- `ANTHROPIC_API_KEY` — Claude API 호출용. 런타임 불필요.

**프론트엔드 빌드타임:**
- `VITE_API_URL` — 기본 `frontend/.env.production`의 `/api`

루트 `.env` (git 미추적). `.env.example`에 키 이름만 명시. `deploy.sh`가 `set -a; . .env; set +a`로 로드.

## 데이터 디렉터리

`data/` 하위:
```
authored_events/    authored_persons/   book_context/     book_events/
book_years_approx/  character_traits/   event_verses/     names_ko/
person_events/      place_context/      place_coords/     tours/
verse_events/
```

`data/person_events/` — 큐레이션 34인 JSON 파일 (abel.json ~ solomon.json).

`data/tours/` — 현재 1개 파일: `david-united-kingdom.json` (18개 이벤트 ID stop, era: "왕국").
