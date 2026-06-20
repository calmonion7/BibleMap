---
last_mapped_commit: cecf0d7de87192b638f428eb7e708e94a58214a6
mapped: 2026-06-20
---

# Technology Stack

**Analysis Date:** 2026-06-20

## Languages

**Primary:**
- JavaScript (ES Module) + JSX — `frontend/src/` 전체
- Python 3.12 — `backend/app/`, `backend/scripts/`

**Secondary:**
- Cypher — Neo4j 쿼리 (각 route 파일 내 인라인 문자열)

## Runtime

**Environment:**
- Node.js 24.15.0 — 프론트엔드 빌드·개발
- Python 3.12-slim — 백엔드 Docker 컨테이너 (`backend/Dockerfile`)
- Python 3.14.5 — 로컬 호스트 (스크립트 실행)

**Package Manager:**
- npm — `frontend/package.json`
- pip — `backend/requirements.txt`

## Frameworks

**Backend:**
- FastAPI 0.136.3 — REST API 서버 (`backend/app/main.py`)
- Uvicorn 0.49.0 — ASGI 서버, `--host 0.0.0.0 --port 8000`

**Frontend:**
- React 19.2.6 — UI 프레임워크 (`frontend/src/`)
- React DOM 19.2.6

**Build/Dev:**
- Vite 8.0.12 — 빌드 번들러 + dev 서버 (`frontend/vite.config.js`)
- `@vitejs/plugin-react` 6.0.1 — Babel 기반 React transform

## Key Dependencies

**Critical:**
- `maplibre-gl` 5.24.0 — 지도 렌더링 (`frontend/src/MapView.jsx`)
- `neo4j` 6.2.0 (Python) — Neo4j Bolt 드라이버 (`backend/app/db.py`)
- `lucide-react` 1.17.0 — 아이콘 (`frontend/src/`)

**Infrastructure:**
- `nginx:alpine` — 정적 파일 서빙 + `/api/` 역방향 프록시 (`nginx/nginx.conf`)
- `neo4j:5` — 그래프 DB Docker 이미지 (`docker-compose.yml`)

## Configuration

**Environment:**
- `.env` (루트) — `NEO4J_PASSWORD` 단일 변수 (`.env.example` 참조)
- `frontend/.env.production` — `VITE_API_URL=/api` (빌드타임 주입)
- 백엔드 런타임 주입 (`docker-compose.yml`): `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`
- `DATA_DIR` 환경변수로 데이터 디렉터리 오버라이드 가능 (`backend/app/overlays.py`)
- 데이터 생성 스크립트 전용: `ANTHROPIC_API_KEY`

**Build:**
- `frontend/vite.config.js` — Rollup manual chunks: `maplibre` 청크 + `vendor` 청크 분리
- `frontend/eslint.config.js` — ESLint 10, `eslint-plugin-react-hooks`, `eslint-plugin-react-refresh`

## Platform Requirements

**Development:**
- Docker Compose로 백엔드 실행: `docker compose up -d --build api`
- 프론트 빌드 후 검증: `cd frontend && npm run build`
- 접근 포트: `localhost:8080` (nginx), Neo4j Browser `127.0.0.1:7474`

**Production:**
- 셀프-호스트 macOS 서버 (`self-hosted` GitHub Actions runner)
- `deploy.sh` + `git reset --hard origin/main` 배포 방식
- `.github/workflows/deploy.yml` — main 브랜치 push 트리거

---

*Stack analysis: 2026-06-20*
