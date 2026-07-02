---
last_mapped_commit: 689126abab88e741263d1d9a4a73d81b2be617d9
mapped: 2026-07-02
---

# STACK.md

## 런타임 버전

| 레이어 | 런타임 / 이미지 | 버전 |
|---|---|---|
| 백엔드 컨테이너 | `python:3.12-slim` | Python 3.12 |
| 데이터베이스 | `neo4j` (Docker Hub 공식) | Neo4j 5.x |
| 프론트엔드 빌드 | Node.js (호스트 직접 실행) | deploy.sh가 `npm install`로 암묵 결정 |
| 리버스 프록시 | `nginx:alpine` | Alpine 기반 최신 stable |

---

## 백엔드

**언어**: Python 3.12

**프레임워크 및 주요 의존성** (`backend/requirements.txt`):

| 패키지 | 버전 |
|---|---|
| `fastapi` | 0.136.3 |
| `uvicorn` | 0.49.0 |
| `neo4j` (Python 드라이버) | 6.2.0 |

**진입점**: `backend/app/main.py` → `uvicorn app.main:app --host 0.0.0.0 --port 8000`

**Dockerfile**: `backend/Dockerfile` — `python:3.12-slim` 베이스, `WORKDIR /app`, app/ 디렉토리 복사.

**라우터 모듈** (`backend/app/routes/`):
- `nodes.py` — `/node/{id}`, `/node/{id}/places`, `/node/{id}/neighbors/grouped`, `/person/{id}/event-ids`
- `events.py` — `/events`, `/event/{id}/verses`
- `search.py` — `/search`
- `books.py` — `/books-overview`
- `persons.py` — `/persons/curated`
- `journey.py` — `/person/{id}/journey`
- `places.py` — `/place/{id}/curated-persons`

**DB 연결**: `backend/app/db.py` — 싱글턴 `GraphDatabase.driver` (Bolt 프로토콜). `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD` 환경변수 참조.

**오버레이 로더**: `backend/app/overlays.py` — `/app/data` 또는 레포 루트의 `data/` 에서 JSON 파일 로드. `functools.lru_cache`로 런타임 1회 캐시.

**CORS 설정**: `allow_origins=["*"]`, `allow_methods=["GET"]` (GET 전용 API).

**응답 캐시**: `Cache-Control: max-age=300` 헤더를 대부분 엔드포인트에 직접 부여. `/books-overview`만 `no-store`.

**스타트업 인덱스 생성**: `lifespan` 함수가 `Person`, `Place`, `Event`, `PeopleGroup`, `Book` 노드의 `theographic_id`에 Neo4j 인덱스를 자동 생성한다.

---

## 프론트엔드

**언어**: JavaScript (JSX), ES Module

**빌드 도구**: Vite `^8.0.12` (`frontend/package.json`)

**주요 의존성**:

| 패키지 | 버전 |
|---|---|
| `react` | ^19.2.6 |
| `react-dom` | ^19.2.6 |
| `maplibre-gl` | ^5.24.0 |
| `lucide-react` | ^1.17.0 |

**devDependencies**:
- `@vitejs/plugin-react` ^6.0.1
- `eslint` ^10.3.0
- `eslint-plugin-react-hooks` ^7.1.1
- `eslint-plugin-react-refresh` ^0.5.2
- `@types/react` ^19.2.14

**빌드 명령**: `cd frontend && npm run build` → `frontend/dist/` 생성. nginx가 이 정적 결과물을 마운트.

**환경 변수 (빌드타임)**:
- `VITE_API_URL` — 미설정 시 기본값 `http://localhost:8000`. 프로덕션 빌드는 `frontend/.env.production`의 `VITE_API_URL=/api`로 고정. `frontend/src/api.js`에서 참조.

**주요 소스 파일** (`frontend/src/`):
- `main.jsx` — React 마운트 진입점
- `App.jsx` — 루트 컴포넌트, 상태 관리 및 라우팅
- `api.js` — 공유 HTTP 클라이언트 (`apiGet` 헬퍼)
- `MapView.jsx` — maplibre-gl 지도 컴포넌트
- `mapGeo.js`, `mapLayers.js`, `mapRingController.js` — 지도 GeoJSON/레이어/링 로직
- `TimelineView.jsx` — 타임라인 컴포넌트
- `BibleOverviewView.jsx` — 성경 개요 뷰
- `PersonHub.jsx` — 인물 선택 허브 뷰
- `SidePanel.jsx` — 우측(데스크탑) / 하단 시트(모바일) 상세 패널
- `JourneyList.jsx` — 여정 정차지 목록
- `EventVerses.jsx`, `VerseLangTabs.jsx` — 구절 본문 표시
- `useNodeSelection.js` — 노드 선택 커스텀 훅
- `constants.js` — `MOBILE_BREAKPOINT=768px`, `SHEET_VH=55`
- `theme.js` — 색상 등 테마 상수

---

## 인프라 / 배포

**컨테이너 오케스트레이션**: `docker-compose.yml` — 3개 서비스(`neo4j`, `api`, `nginx`), Docker 네트워크 내부 통신.

**포트 매핑**:
- `8080:80` — nginx (외부 진입점)
- `127.0.0.1:7474:7474` — Neo4j 브라우저 (로컬호스트만)
- `127.0.0.1:7687:7687` — Neo4j Bolt (로컬호스트만)
- API(8000)는 외부 미노출, nginx 내부 프록시로만 접근

**볼륨**:
- `neo4j_data` — Neo4j 영속 데이터
- `./data:/app/data` — JSON 데이터 파일 바인드 마운트
- `./frontend/dist:/usr/share/nginx/html:ro` — 프론트엔드 정적 파일 마운트

**nginx 설정** (`nginx/nginx.conf`):
- `/api/` 경로 → `http://api:8000/` 프록시
- `index.html` — `no-cache`
- JS/CSS 등 정적 자산 — 1년 immutable 캐시
- SPA fallback: `try_files $uri /index.html`

**배포 스크립트** (`deploy.sh`):
1. `frontend/` `npm install && npm run build`
2. `docker compose -p biblemap build api`
3. `docker compose -p biblemap up -d api nginx`
4. `python3 backend/scripts/inject_ko_names.py` (최대 15회 재시도)

**lock 파일**: `/tmp/biblemap-deploy.lock` — 중복 배포 방지.
**배포 로그**: `/Users/calmonion/Library/Logs/com.biblemap.deploy.log`

**CI/CD**: `.github/workflows/deploy.yml` — `push: branches: [main]` 트리거, `runs-on: self-hosted` (macOS 로컬 러너).

---

## 환경 변수

| 변수명 | 설정 위치 | 용도 |
|---|---|---|
| `NEO4J_PASSWORD` | `.env` (루트), `docker-compose.yml` | Neo4j 인증 비밀번호 (필수) |
| `NEO4J_URI` | `docker-compose.yml` | Bolt URI (`bolt://neo4j:7687`) |
| `NEO4J_USER` | `docker-compose.yml` | Neo4j 사용자명 (`neo4j`) |
| `VITE_API_URL` | `frontend/.env.production` | 프론트 API 베이스 URL (`/api`) |
| `DATA_DIR` | 런타임 선택적 | 데이터 디렉토리 경로 오버라이드 (기본 `/app/data`) |
| `ANTHROPIC_API_KEY` | 빌드타임 스크립트 전용 | 데이터 생성 스크립트에서 Claude 호출 시 사용 |

---

## 데이터 생성 스크립트 (`backend/scripts/`)

런타임이 아닌 **빌드타임 오프라인 실행** 전용. 생성 결과물은 `data/`에 JSON으로 저장되어 배포된다.

**데이터 로더 스크립트**:
- `load_theographic.py` — Theographic GitHub Raw JSON → Neo4j 로드
- `load_books.py`, `load_person_events.py`, `load_authored_events.py`, `load_authored_persons.py`, `load_verse_events.py`
- `inject_ko_names.py` — `data/names_ko/` JSON → Neo4j 노드에 `nameKo` 주입 (배포마다 실행)
- `inject_book_context.py`, `inject_person_traits.py`, `inject_place_context.py`

**LLM 의존 생성 스크립트** (빌드타임, `anthropic` SDK 사용):
- `generate_book_context.py` — `claude-haiku-4-5-20251001` 모델로 책 맥락 생성
- `generate_book_events.py` — 동일 모델
- `generate_verse_events.py` — 동일 모델
- `generate_person_traits.py` — 동일 모델

**외부 데이터 Fetch 스크립트** (빌드타임):
- `generate_verse_text.py` — `api.getbible.net/v2/{slug}/{book}/{chapter}.json` 호출, 한국어(`korean`) + 영어(`kjv`) 구절 본문 선(先)저장
- `generate_person_event_verses.py` — 동일 엔드포인트 호출
- `enrich_place_coords.py`, `generate_approx_book_verses.py`, `generate_book_context_enrich.py`, `generate_event_verses.py`
