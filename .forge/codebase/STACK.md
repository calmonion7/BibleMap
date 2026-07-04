---
last_mapped_commit: 815433397ff74c133b2de5d1cafe1c8764b5303c
mapped: 2026-07-04
---

# Technology Stack

**Analysis Date:** 2026-07-04

## Languages

**Primary:**
- Python 3.12 — 백엔드 API 및 데이터 로드/생성 스크립트 (`backend/app/`, `backend/scripts/`)
- JavaScript (ES modules, JSX) — 프론트엔드 SPA (`frontend/src/`). TypeScript 미사용, 순수 JS + `@types/react`만 devDependency로 존재

**Secondary:**
- Bash — 배포 스크립트 (`deploy.sh`)
- Cypher — Neo4j 쿼리 (백엔드 라우트 및 로더 스크립트 내 인라인 문자열)

## Runtime

**백엔드 환경:**
- Python 3.12 (`backend/Dockerfile` → `python:3.12-slim`). 루트에 `.python-version` 핀 파일 없음
- ASGI 서버: uvicorn (`app.main:app`, `--host 0.0.0.0 --port 8000`)

**프론트엔드 환경:**
- Node.js (버전 핀 파일 `.nvmrc` 없음)
- ESM (`frontend/package.json` → `"type": "module"`)

**Package Manager:**
- Python: pip (`backend/requirements.txt`, lockfile 없음 — 버전 고정 명시)
- Node: npm — lockfile `frontend/package-lock.json` 존재 (lockfileVersion 3)

## Frameworks

**백엔드 Core:**
- FastAPI 0.136.3 — REST API 프레임워크 (`backend/app/main.py`). `APIRouter`로 라우트 분할, `CORSMiddleware`(모든 origin GET 허용), `lifespan` 훅에서 Neo4j 인덱스 생성
- uvicorn 0.49.0 — ASGI 서버

**프론트엔드 Core:**
- React 19.2 (설치 해석 버전 19.2.7) — UI 라이브러리 (`react`, `react-dom`)
- Vite 8.0 (설치 해석 버전 8.0.16) — 빌드 도구 및 dev 서버 (`frontend/vite.config.js`)
- maplibre-gl 5.24.0 — 지도 렌더링 (`frontend/src/MapView.jsx`, `mapLayers.js`, `mapGeo.js`)
- lucide-react 1.17.0 — 아이콘

**Testing:**
- 자동화 테스트 프레임워크 미검출 (`*.test.*`/`*.spec.*` 파일 없음, jest/vitest 설정 없음). 검증은 수동 + Python Playwright 스크린샷 방식(프로젝트 메모리 참조)

**Build/Dev:**
- Vite 8 — 프론트엔드 번들. `vite.config.js`에서 `manualChunks`로 `maplibre-gl`을 별도 `maplibre` 청크, 그 외 node_modules를 `vendor` 청크로 분리
- `@vitejs/plugin-react` 6.0 (설치 해석 6.0.2) — React 지원

## Key Dependencies

**Critical:**
- neo4j 6.2.0 (Python driver) — 그래프 DB 접근 (`backend/app/db.py`, 모든 로더/주입 스크립트)
- fastapi 0.136.3 — API 프레임워크
- maplibre-gl 5.24.0 — 지도 UI 핵심

**빌드타임 데이터 생성 (requirements.txt 미포함, 별도 설치 필요):**
- anthropic (Python SDK) — Claude API 호출로 성경 권별 배경·인물 성품·사건 데이터 생성 (`backend/scripts/generate_book_context.py`, `generate_person_traits.py`, `generate_book_events.py`, `generate_verse_events.py`). 런타임 앱 코드에는 포함되지 않음
- urllib (표준 라이브러리) — 외부 JSON/절 본문 fetch (모든 `generate_*`/`load_*` 스크립트)

## Configuration

**Linting/Formatting:**
- ESLint 10.3 (설치 해석 10.4.1) — flat config `frontend/eslint.config.js`. `js.configs.recommended` + `eslint-plugin-react-hooks` + `eslint-plugin-react-refresh`, `dist` 무시
- Prettier 설정 파일 없음

**환경 변수 (백엔드 런타임):**
- `NEO4J_URI` — 기본 `bolt://localhost:7687`, compose에서는 `bolt://neo4j:7687`
- `NEO4J_USER` — 기본 `neo4j`
- `NEO4J_PASSWORD` — 필수, 미설정 시 `db.py`가 `RuntimeError` 발생. 루트 `.env`/`.env.example`에 키 이름만 정의(값은 미기재)
- `DATA_DIR` — 오버레이 JSON 조회 경로, 기본 `/app/data` (`backend/app/overlays.py`)

**환경 변수 (데이터 생성 스크립트):**
- `ANTHROPIC_API_KEY` — Claude API 호출용 (`generate_book_context.py` 등). 런타임 불필요

**환경 변수 (프론트엔드 빌드타임):**
- `VITE_API_URL` — API 베이스 URL. 프로덕션은 `frontend/.env.production`에서 `/api`(nginx 프록시 경유), 미설정 시 `frontend/src/api.js`에서 `http://localhost:8000`

**Build 설정 파일:**
- `frontend/vite.config.js` — Vite 빌드/청크
- `frontend/eslint.config.js` — ESLint flat config
- `backend/Dockerfile` — API 이미지 빌드 (python:3.12-slim, requirements 설치, uvicorn 실행)
- `docker-compose.yml` — 서비스 오케스트레이션 (프로젝트명 `biblemap`)
- `nginx/nginx.conf` — 정적 서빙 + `/api` 리버스 프록시

## Platform Requirements

**Development:**
- Docker + Docker Compose (neo4j·api·nginx 3서비스)
- Node.js + npm (프론트 빌드)
- Python 3.12 (데이터 스크립트 호스트 직접 실행 가능)

**Production:**
- self-hosted 배포. GitHub Actions `self-hosted` 러너가 push→`deploy.sh` 실행 (`.github/workflows/deploy.yml`)
- `deploy.sh`: 프론트 `npm install && npm run build` → `docker compose -p biblemap build api` → `up -d api nginx` → `inject_ko_names.py`로 한글 이름 주입(Neo4j 준비까지 최대 15회 재시도)
- nginx가 호스트 `8080:80` 노출, 프론트 `frontend/dist`를 read-only 마운트하여 서빙

---

*Stack analysis: 2026-07-04*
