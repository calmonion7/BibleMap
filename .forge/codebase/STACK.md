---
last_mapped_commit: 99d42c8518af00f3e0bf4a4ba90f821d84cf42e5
mapped: 2026-07-02
---

# 기술 스택

## 언어 및 런타임

| 계층 | 언어 | 버전 |
|------|------|------|
| 백엔드 | Python | 3.12 (`backend/Dockerfile`: `FROM python:3.12-slim`) |
| 프론트엔드 | JavaScript (ESM) | Node.js (빌드 전용) |

## 백엔드 프레임워크 및 주요 의존성

`backend/requirements.txt`에 선언된 패키지:

| 패키지 | 버전 | 역할 |
|--------|------|------|
| `fastapi` | 0.136.3 | ASGI 웹 프레임워크 — REST API 라우터, 미들웨어 |
| `uvicorn` | 0.49.0 | ASGI 서버 — 컨테이너 진입점 (`app.main:app`, `0.0.0.0:8000`) |
| `neo4j` | 6.2.0 | 공식 Python 드라이버 — Bolt 프로토콜로 Neo4j 통신 |

백엔드 표준 라이브러리만 추가 사용: `os`, `json`, `re`, `urllib.request` (스크립트 전용).

## 프론트엔드 프레임워크 및 주요 의존성

`frontend/package.json` 기준:

### 런타임 의존성 (`dependencies`)

| 패키지 | 버전 | 역할 |
|--------|------|------|
| `react` | ^19.2.6 | UI 프레임워크 |
| `react-dom` | ^19.2.6 | DOM 렌더러 |
| `maplibre-gl` | ^5.24.0 | WebGL 지도 렌더러 |
| `lucide-react` | ^1.17.0 | SVG 아이콘 컴포넌트 |

### 개발 의존성 (`devDependencies`)

| 패키지 | 버전 | 역할 |
|--------|------|------|
| `vite` | ^8.0.12 | 번들러 / 개발 서버 |
| `@vitejs/plugin-react` | ^6.0.1 | Vite React(JSX + Fast Refresh) 플러그인 |
| `eslint` | ^10.3.0 | 린터 |
| `eslint-plugin-react-hooks` | ^7.1.1 | React Hooks 규칙 린트 |
| `eslint-plugin-react-refresh` | ^0.5.2 | Fast Refresh 호환 린트 |
| `@types/react` | ^19.2.14 | React 타입 정의 |
| `@types/react-dom` | ^19.2.3 | ReactDOM 타입 정의 |
| `globals` | ^17.6.0 | ESLint 전역 변수 집합 |

## 빌드 및 번들링

### `frontend/vite.config.js`

- 플러그인: `@vitejs/plugin-react`
- 청크 분리 전략(`manualChunks`):
  - `maplibre-gl` → `maplibre` 청크로 분리
  - 나머지 `node_modules` → `vendor` 청크로 분리
- 출력 디렉터리: `frontend/dist/` (nginx가 정적 파일로 마운트)

### 프론트엔드 빌드 환경변수

`frontend/.env.production`:
```
VITE_API_URL=/api
```
빌드 시 API 호출이 `/api`로 고정되며, 런타임 외부 URL을 별도 주입하지 않는다.

## 인프라 및 컨테이너

### `docker-compose.yml`

3개 서비스:

| 서비스 | 이미지 | 포트 | 역할 |
|--------|--------|------|------|
| `neo4j` | `neo4j:5` | `127.0.0.1:7474`, `127.0.0.1:7687` | 그래프 DB |
| `api` | `./backend` (로컬 빌드) | 내부 8000 | FastAPI 서버 |
| `nginx` | `nginx:alpine` | `0.0.0.0:8080→80` | 리버스 프록시 + 정적 파일 |

- `api` 서비스는 `./data:/app/data` 볼륨을 마운트하여 빌드타임 생성 JSON 데이터를 공유한다.
- `neo4j_data`는 명명된 Docker 볼륨으로 영속화된다.
- 모든 서비스에 `restart: unless-stopped` 적용.

### `backend/Dockerfile`

```
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ ./app/
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

멀티스테이지 없이 단일 스테이지 빌드. `scripts/`는 이미지에 포함하지 않는다.

### `nginx/nginx.conf`

- `/api/` 경로 → `http://api:8000/` 프록시 (경로 재작성 포함: trailing slash strip)
- `index.html` → `Cache-Control: no-cache, no-store, must-revalidate`
- 정적 에셋(`.js`, `.css`, 이미지, 폰트) → `Cache-Control: public, max-age=31536000, immutable`
- 나머지 → SPA fallback (`try_files $uri /index.html`)

## 환경변수

`.env` (실제값, git-ignored) / `.env.example` (템플릿):

| 변수 | 용도 |
|------|------|
| `NEO4J_PASSWORD` | Neo4j 비밀번호. `docker-compose.yml`이 `neo4j/${NEO4J_PASSWORD}`로 `NEO4J_AUTH`를 파생. `api` 서비스에도 동일 값 전달. 미설정 시 compose가 즉시 오류(`?:` 연산자) |

## 배포 스크립트

`deploy.sh`:

1. lock 파일(`/tmp/biblemap-deploy.lock`)로 중복 실행 방지
2. macOS Keychain 우회용 임시 Docker config 디렉터리 생성 (`DOCKER_CONFIG` 재정의)
3. `.env`에서 `NEO4J_PASSWORD` 로드
4. `frontend/`: `npm install && npm run build`
5. `docker compose -p biblemap build api`
6. `docker compose -p biblemap up -d api nginx` (neo4j는 재시작하지 않음)
7. `backend/scripts/inject_ko_names.py` 실행 — Neo4j 준비 대기 최대 15회(2초 간격) 재시도
8. 배포 로그: `/Users/calmonion/Library/Logs/com.biblemap.deploy.log`
