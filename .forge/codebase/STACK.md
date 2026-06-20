---
last_mapped_commit: 7a1ef362b1fb247b09edeeaa1380e6449fce5721
mapped: 2026-06-20
---

# STACK.md — BibleMap 기술 스택

## 언어 및 런타임

| 계층 | 언어 | 런타임 |
|------|------|--------|
| 프론트엔드 | JavaScript (ESM) | Node.js 22 (빌드타임) |
| 백엔드 | Python 3.12 | CPython 3.12-slim |
| 컨테이너 오케스트레이션 | YAML | Docker Compose v2 |

---

## 프론트엔드

**프레임워크 및 주요 라이브러리**

- **React 19.2.6** — UI 컴포넌트 트리
- **MapLibre GL 5.24.0** — WebGL 기반 벡터 지도 렌더링
- **Lucide React 1.17.0** — 아이콘

**빌드 도구**

- **Vite 8.0.12** — 번들러 / 개발 서버
  - 설정 파일: `frontend/vite.config.js`
  - 플러그인: `@vitejs/plugin-react 6.0.1`
  - 코드 분할: `maplibre-gl` → `maplibre` 청크, 나머지 `node_modules` → `vendor` 청크

**린트**

- `eslint 10.3.0`, `eslint-plugin-react-hooks 7.1.1`, `eslint-plugin-react-refresh 0.5.2`

**주요 소스 파일**

| 파일 | 역할 |
|------|------|
| `frontend/src/main.jsx` | React 앱 진입점 |
| `frontend/src/App.jsx` | 탭(지도/타임라인/성경개요), 검색바, 반응형 레이아웃 |
| `frontend/src/MapView.jsx` | MapLibre GL 지도, 클러스터링, 스파이더파이 |
| `frontend/src/SidePanel.jsx` | 노드 상세 패널 |
| `frontend/src/TimelineView.jsx` | 사건 타임라인, 구절 인라인 뷰 |
| `frontend/src/BibleOverviewView.jsx` | 권별 개요 카드 그리드 |
| `frontend/src/api.js` | API 클라이언트 (`apiGet` 단일 함수) |
| `frontend/src/theme.js` | 노드 타입 색상·한글명 팔레트 |
| `frontend/src/useNodeSelection.js` | 선택 노드 상태 + 히스토리 훅 |
| `frontend/src/useSearch.js` | 250ms 디바운스 검색 훅 |
| `frontend/src/convexHull.js` | Graham scan 볼록 껍질 순수 함수 |
| `frontend/src/VerseLangTabs.jsx` | 한국어/영어 전환 세그먼트 |

**패키지 파일**: `frontend/package.json`

---

## 백엔드

**프레임워크 및 주요 라이브러리**

- **FastAPI 0.136.3** — REST API 서버 (비동기)
- **neo4j 6.2.0** — Neo4j Python 드라이버 (Bolt 프로토콜)
- **uvicorn 0.49.0** — ASGI 서버

**의존성 파일**: `backend/requirements.txt`

**주요 소스 파일**

| 파일 | 역할 |
|------|------|
| `backend/app/main.py` | FastAPI 앱 생성, CORS, 라우터 등록, lifespan(인덱스 생성) |
| `backend/app/db.py` | Neo4j 드라이버 싱글턴, 환경변수 연결 |
| `backend/app/overlays.py` | JSON 파일 오버레이 로더 (lru_cache) |
| `backend/app/routes/nodes.py` | 노드 상세, 이웃, 장소, Person 사건 ID 엔드포인트 |
| `backend/app/routes/events.py` | 타임라인 사건 목록, 사건 구절 엔드포인트 |
| `backend/app/routes/search.py` | 이름 검색 엔드포인트 |
| `backend/app/routes/books.py` | 권 개요, 타임라인 배치용 엔드포인트 |

**API 엔드포인트 요약**

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/node/{id}` | 노드 상세 + 이웃 |
| GET | `/node/{id}/neighbors/grouped` | 이웃 그룹핑 |
| GET | `/node/{id}/places` | 관련 장소(위경도) |
| GET | `/person/{id}/event-ids` | Person 사건 ID 목록 |
| GET | `/events` | 타임라인 사건 전체 |
| GET | `/event/{id}/verses` | 사건 근거 구절 |
| GET | `/search?q=` | 이름 검색 |
| GET | `/books-overview` | 권별 개요 |
| GET | `/books` | 타임라인용 권 목록 |

---

## 데이터베이스

- **Neo4j 5** (Docker 이미지 `neo4j:5`)
- 프로토콜: Bolt (`bolt://neo4j:7687`, compose 내부망)
- 인증: `NEO4J_AUTH=neo4j/${NEO4J_PASSWORD}` 환경변수
- 노드 레이블: `Person`, `Place`, `Event`, `PeopleGroup`, `Book`
- 인덱스 5개: `{label}_tid` (theographic_id 기준, lifespan에서 자동 생성)
- 관계: `HAS_PARTICIPANT`, `OCCURS_AT`, `MEMBER_OF`, `PARENT_OF`, `CHILD_OF`, `SIBLING_OF`, `PARTNER_OF`, `PART_OF`, `CONTAINS_BOOK`
- Web UI 포트: `127.0.0.1:7474` (로컬호스트 전용)

---

## 컨테이너화

**Docker Compose**: `docker-compose.yml`

| 서비스 | 이미지 / 빌드 | 퍼블릭 포트 |
|--------|--------------|-------------|
| `neo4j` | `neo4j:5` | 127.0.0.1:7474, 127.0.0.1:7687 |
| `api` | `./backend` (Dockerfile) | 내부망만 |
| `nginx` | `nginx:alpine` | 0.0.0.0:8080 |

**백엔드 Dockerfile**: `backend/Dockerfile`
- 베이스: `python:3.12-slim`
- `pip install -r requirements.txt` → `COPY app/` → `uvicorn app.main:app --host 0.0.0.0 --port 8000`

**Nginx 설정**: `nginx/nginx.conf`
- `/api/` → `proxy_pass http://api:8000/` (FastAPI 역방향 프록시)
- `*.js|css|png…` → `Cache-Control: max-age=31536000, immutable`
- SPA fallback: `try_files $uri /index.html`

**정적 파일 서빙**: `frontend/dist` 볼륨 마운트 (`/usr/share/nginx/html`)

---

## 빌드 파이프라인

**배포 스크립트**: `deploy.sh`

1. `cd frontend && npm install && npm run build` → `frontend/dist/` 생성
2. `docker compose -p biblemap build api`
3. `docker compose -p biblemap up -d api nginx`
4. `python3 backend/scripts/inject_ko_names.py` (Neo4j 준비 대기, 15회 재시도)

---

## 환경 설정

| 파일 | 범위 | 주요 변수 |
|------|------|-----------|
| `.env` | 로컬 개발 (git 추적) | `NEO4J_PASSWORD` |
| `.env.example` | 템플릿 | `NEO4J_PASSWORD=your-password-here` |
| `frontend/.env.production` | 프론트 빌드타임 | `VITE_API_URL=/api` |

**백엔드 환경변수** (`backend/app/db.py` 참조)

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `NEO4J_URI` | `bolt://localhost:7687` | Neo4j Bolt 연결 |
| `NEO4J_USER` | — | Neo4j 사용자명 |
| `NEO4J_PASSWORD` | — | Neo4j 비밀번호 |
| `DATA_DIR` | `/app/data` | JSON 오버레이 파일 루트 |

**프론트엔드 환경변수** (`frontend/src/api.js` 참조)

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `VITE_API_URL` | `http://localhost:8000` | API 베이스 URL |
