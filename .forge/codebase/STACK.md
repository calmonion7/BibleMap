---
last_mapped_commit: 06b4012804c00a45ea7dfda9761d014ac91b11fb
mapped: 2026-06-20
---

# BibleMap 기술 스택

## 백엔드

### 언어 및 런타임
- **Python 3.12** (Docker 이미지 기준: `python:3.12-slim`)
- 로컬 개발 환경: Python 3.14.5

### 프레임워크 및 주요 라이브러리
- **FastAPI 0.136.3** — REST API 서버
- **Uvicorn 0.49.0** — ASGI 서버, 포트 8000 바인딩 (`0.0.0.0:8000`)
- **neo4j 6.2.0** — Neo4j Python 드라이버 (Bolt 프로토콜)
- **anthropic** (requirements.txt 미포함, 스크립트 전용) — 데이터 생성 스크립트에서만 사용

### 설정 파일
- `backend/requirements.txt` — 런타임 의존성 3개 (fastapi, neo4j, uvicorn)
- `backend/Dockerfile` — `python:3.12-slim` 기반, `/app` 워크디렉터리, 포트 8000

### 환경변수 (백엔드)
| 변수 | 기본값 | 용도 |
|------|--------|------|
| `NEO4J_URI` | `bolt://localhost:7687` | Neo4j 연결 URI |
| `NEO4J_USER` | `neo4j` | Neo4j 사용자명 |
| `NEO4J_PASSWORD` | (필수) | Neo4j 비밀번호 |
| `DATA_DIR` | `/app/data` | JSON 오버레이 데이터 루트 경로 |
| `ANTHROPIC_API_KEY` | (필수, 스크립트 전용) | 데이터 생성 스크립트 Claude API 키 |

---

## 프론트엔드

### 언어 및 런타임
- **JavaScript (ES Module)** + JSX
- **Node.js 24.15.0** (로컬)

### 프레임워크 및 주요 라이브러리
- **React 19.2.6** — UI 컴포넌트
- **react-dom 19.2.6** — DOM 렌더러
- **MapLibre GL 5.24.0** — 지도 렌더링 (`MapView.jsx`)
- **Lucide React 1.17.0** — 아이콘

### 빌드 도구
- **Vite 8.0.12** — 빌드 번들러 및 개발 서버
- **@vitejs/plugin-react 6.0.1** — JSX 트랜스파일
- Rollup 수동 청크 분할: `maplibre` 청크, `vendor` 청크 (`vite.config.js`)

### 린터
- **ESLint 10.3.0** (`eslint.config.js`)
- `eslint-plugin-react-hooks 7.1.1`
- `eslint-plugin-react-refresh 0.5.2`

### 설정 파일
- `frontend/package.json`
- `frontend/vite.config.js`
- `frontend/eslint.config.js`
- `frontend/.env.production` — `VITE_API_URL=/api` (빌드 타임 주입)

### 환경변수 (프론트엔드)
| 변수 | 기본값 | 용도 |
|------|--------|------|
| `VITE_API_URL` | `http://localhost:8000` | API 베이스 URL (`frontend/src/api.js`) |

빌드 결과물은 `frontend/dist/`에 정적 파일로 출력된다.

---

## 인프라

### Docker
- **Docker Compose** (`docker-compose.yml`) — 3개 서비스 정의
  - `neo4j` — `neo4j:5` 이미지, 포트 `127.0.0.1:7474/7687`
  - `api` — `./backend` Dockerfile 빌드, 포트 미노출 (nginx 내부 통신)
  - `nginx` — `nginx:alpine` 이미지, 포트 `8080:80`

### Nginx
- 설정 파일: `nginx/nginx.conf`
- `/api/` → `http://api:8000/` 역방향 프록시
- 정적 파일 (`/frontend/dist`): JS/CSS `max-age=31536000, immutable`, `index.html` `no-cache`
- SPA fallback: `try_files $uri /index.html`

### 데이터 볼륨
- `neo4j_data` (named volume) — Neo4j 데이터 영속화
- `./data:/app/data` — JSON 오버레이 파일 마운트 (읽기 전용으로 api 컨테이너에 주입)
- `./frontend/dist:/usr/share/nginx/html:ro` — 빌드된 프론트엔드 정적 파일

### 루트 설정 파일
- `.env` / `.env.example` — `NEO4J_PASSWORD` 단일 변수
- `deploy.sh` — 배포 스크립트
