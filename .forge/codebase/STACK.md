---
last_mapped_commit: ecdb7cb2ea1bf665b0690e62b4cf51261761072c
mapped: 2026-06-15
---

# Technology Stack

## 언어

**주 언어:**
- JavaScript (ES Modules) — 프론트엔드 (`frontend/src/`)
- Python 3.12 — 백엔드 (`backend/app/`, `backend/scripts/`)

**보조:**
- JSX — React 컴포넌트 파일 (`frontend/src/*.jsx`)

## 런타임

**프론트엔드:**
- 브라우저 (ES Module 번들; nginx가 서빙)
- 빌드 타임: Node.js + npm (`frontend/package-lock.json`)

**백엔드:**
- Python 3.12-slim Docker 컨테이너 (`backend/Dockerfile`)
- ASGI 서버: Uvicorn 0.49.0 (Dockerfile `CMD`)

**패키지 관리:**
- 프론트엔드: npm — 잠금 파일 `frontend/package-lock.json`
- 백엔드: pip — 버전 고정 `backend/requirements.txt` (잠금 파일 없음)

## 프레임워크

**프론트엔드:**
- React 19.2.6 — UI 컴포넌트 트리 (`frontend/src/`)
- React DOM 19.2.6 — DOM 렌더링 (`frontend/src/main.jsx`)

**백엔드:**
- FastAPI 0.136.3 — HTTP API (`backend/app/main.py`)
- Uvicorn 0.49.0 — ASGI 서버

**빌드/개발 도구:**
- Vite 8.0.12 — 개발 서버 및 번들러 (`frontend/vite.config.js`)
- `@vitejs/plugin-react` 6.0.1 — JSX transform 플러그인

**린팅:**
- ESLint 10.3.0 (`frontend/eslint.config.js`)
- `eslint-plugin-react-hooks` 7.1.1
- `eslint-plugin-react-refresh` 0.5.2

## 주요 의존성

**프론트엔드 런타임 (`frontend/package.json`):**
- `maplibre-gl` 5.24.0 — 지도 렌더링 (`frontend/src/MapView.jsx`)
- `lucide-react` 1.17.0 — 아이콘 세트 (`frontend/src/App.jsx`, `frontend/src/SidePanel.jsx`)

> 참고: GraphView 제거(overhaul part 1) 이후 `cytoscape` 및 관련 플러그인은 `package.json`에서 삭제됨.

**백엔드 (`backend/requirements.txt`):**
- `neo4j` 6.2.0 — Neo4j Python 드라이버 (`backend/app/db.py`)
- `fastapi` 0.136.3
- `uvicorn` 0.49.0

**스크립트 전용 의존성 (별도 설치 필요):**
- `anthropic` — Claude API 클라이언트 (`backend/scripts/generate_book_context.py`, `backend/scripts/generate_person_traits.py`)

## 공유 모듈

- `frontend/src/theme.js` — 노드 타입 색상(`TYPE_COLOR`), 한글 라벨(`TYPE_KO`), 표시 순서(`TYPE_ORDER`), 헬퍼 함수. App·MapView·SidePanel·TimelineView가 모두 import.
- `frontend/src/api.js` — API 기본 URL(`API_BASE`) 및 공통 GET 헬퍼(`apiGet`). 모든 fetch는 여기를 경유.
- `frontend/src/convexHull.js` — MapView용 Convex Hull 계산 유틸리티.

## 설정

**환경 변수:**
- `NEO4J_PASSWORD` — 런타임 필수; `.env`에서 로드 (`.env.example` 참고)
- `NEO4J_URI` — 기본값 `bolt://localhost:7687`; Docker 내부는 `bolt://neo4j:7687`
- `NEO4J_USER` — 기본값 `neo4j`
- `VITE_API_URL` — 빌드 타임 주입; 프로덕션에서는 `/api` (nginx 프록시 경로)
- `ANTHROPIC_API_KEY` — 스크립트 전용; `generate_book_context.py`, `generate_person_traits.py` 실행 시만 필요

**설정 파일:**
- `frontend/vite.config.js` — Vite 설정 (React 플러그인만)
- `frontend/eslint.config.js` — ESLint flat config
- `docker-compose.yml` — 서비스 토폴로지 (neo4j, api, nginx)
- `backend/Dockerfile` — Python 3.12-slim 이미지, pip install, uvicorn CMD
- `nginx/nginx.conf` — `/api/*` → `api:8000` 리버스 프록시, SPA fallback

## 플랫폼 요구사항

**개발:**
- Node.js (버전 미지정; `.nvmrc` 없음)
- Python 3.12
- Docker + Docker Compose (neo4j + api 로컬 실행용)
- 백엔드 hot-reload 없음 → 변경 후 `docker compose up -d --build api` 필요

**프로덕션:**
- Self-hosted macOS GitHub Actions 러너
- Docker Compose 프로젝트명: `biblemap`
- 서비스: `neo4j` (이미지 `neo4j:5`), `api` (빌드: `backend/Dockerfile`), `nginx` (이미지 `nginx:alpine`)
- 외부 포트: 8080 (nginx)
