---
last_mapped_commit: 6f2cfc1bf163d7327bd86773676223624fa53ff2
mapped: 2026-06-18
---

# STACK.md — BibleMap 기술 스택

## 언어 및 런타임

| 레이어 | 언어 | 런타임 |
|---|---|---|
| 백엔드 | Python 3.12 | CPython (`python:3.12-slim` 도커 이미지) |
| 프론트엔드 | JavaScript (ESM + JSX) | 브라우저 (빌드타임 Node.js) |
| 데이터 스크립트 | Python 3 | 호스트 python3 직접 실행 |

## 프레임워크 및 주요 라이브러리

### 백엔드 (`backend/requirements.txt`)
- **FastAPI 0.136.3** — HTTP API 서버. CORS 미들웨어(`allow_origins=["*"]`, GET 전용), `lifespan` 훅으로 Neo4j 인덱스 자동 생성
- **Uvicorn 0.49.0** — ASGI 서버. `uvicorn app.main:app --host 0.0.0.0 --port 8000`으로 기동
- **neo4j 6.2.0** — 공식 Python 드라이버. Bolt 프로토콜로 연결(`bolt://neo4j:7687`). 싱글턴 패턴(`backend/app/db.py`)

### 프론트엔드 (`frontend/package.json`)
- **React 19.2.6 + react-dom 19.2.6** — UI 프레임워크. JSX로 작성 (`frontend/src/`)
- **maplibre-gl 5.24.0** — 오픈소스 WebGL 지도 렌더러. Esri NatGeo 래스터 타일 소스를 마운트 (`frontend/src/MapView.jsx`)
- **lucide-react 1.17.0** — 아이콘 라이브러리 (Map, Clock, Search, X 등)

### 빌드 도구 및 패키지 매니저

| 도구 | 버전 | 용도 |
|---|---|---|
| **Vite** | 8.0.12 | 프론트 번들러. `vite build` → `frontend/dist/` |
| **@vitejs/plugin-react** | 6.0.1 | Vite용 React(JSX) 트랜스파일 플러그인 |
| **npm** | (package-lock.json 관리) | 프론트 패키지 매니저 |
| **ESLint** | 10.3.0 | 린터. `eslint-plugin-react-hooks`, `eslint-plugin-react-refresh` 포함 |

## 번들 분리 설정 (`frontend/vite.config.js`)

`manualChunks`로 두 청크를 분리:
- `maplibre` — `maplibre-gl` 단독 청크
- `vendor` — 나머지 node_modules

## 환경 설정 파일

| 파일 | 역할 |
|---|---|
| `.env` | 호스트 환경. `NEO4J_PASSWORD=...` 단 하나의 키 |
| `.env.example` | `.env` 템플릿 |
| `frontend/.env.production` | 빌드타임 주입. `VITE_API_URL=/api` |
| `docker-compose.yml` | 로컬·프로덕션 서비스 오케스트레이션 |

## 인프라 / 컨테이너

### Docker Compose 서비스 (`docker-compose.yml`)

| 서비스 | 이미지 | 포트(호스트) | 역할 |
|---|---|---|---|
| `neo4j` | `neo4j:5` | 7474(HTTP), 7687(Bolt) — localhost 바인드 | 그래프 DB |
| `api` | `./backend` (자체 빌드) | 외부 미노출 (nginx 프록시 경유) | FastAPI 백엔드 |
| `nginx` | `nginx:alpine` | 8080 | 리버스 프록시 + 정적 서빙 |

### Nginx 역할 (`nginx/nginx.conf`)

- `/api/` → `http://api:8000/` 프록시
- `/index.html` — `no-cache` 헤더
- `*.js|*.css|…` — `immutable, max-age=31536000` 장기 캐시
- 그 외 → SPA fallback (`try_files $uri /index.html`)

### 백엔드 Dockerfile (`backend/Dockerfile`)

```
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ ./app/
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 배포 파이프라인

1. **CI** — `.github/workflows/deploy.yml`: `main` 브랜치 push → `self-hosted` 러너에서 `git reset --hard origin/main && bash deploy.sh`
2. **`deploy.sh`** — 순서: npm install → `vite build` → `docker compose build api` → `docker compose up -d api nginx` → `python3 backend/scripts/inject_ko_names.py` (최대 15회 재시도)

## 데이터 파이프라인 스크립트 (`backend/scripts/`)

빌드타임 단독 실행용 Python 스크립트. 런타임 의존 없음.

| 스크립트 | 역할 |
|---|---|
| `load_theographic.py` | Theographic 메타데이터 JSON → Neo4j 일괄 로드 |
| `load_books.py` | 성경 권 데이터 → Neo4j |
| `inject_ko_names.py` | 한국어 이름 데이터 → Neo4j 노드 속성 주입 |
| `inject_book_context.py` | 권별 컨텍스트 → Neo4j |
| `inject_person_traits.py` | 인물 특성 → Neo4j |
| `generate_verse_text.py` | getbible API 호출 → `data/` JSON에 절 본문 인라인 저장 (ADR-0003 미리굽기) |
| `generate_approx_book_verses.py` | 추정책 구절 데이터 생성 |
| `generate_book_context.py` | 권별 컨텍스트 JSON 생성 |
| `generate_book_events.py` | 권별 사건 매핑 생성 |
| `generate_event_verses.py` | 사건별 근거 구절 생성 |
| `generate_person_traits.py` | 인물 특성 생성 |
| `load_authored_events.py` | 저작 사건 데이터 Neo4j 로드 |
