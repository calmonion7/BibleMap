---
last_mapped_commit: 4ed4d876d7fa3b06a8eb1647b5b50ed73f906b25
mapped: 2026-06-19
---

# 기술 스택

## 언어 & 런타임

| 영역 | 언어 | 버전 |
|------|------|------|
| 백엔드 | Python | 3.12 (Docker 이미지 `python:3.12-slim`) |
| 프론트엔드 | JavaScript (ESM) | Node 런타임(빌드 전용), 브라우저 배포 |
| 리버스 프록시 | — | nginx:alpine |

## 프레임워크 & 라이브러리

### 백엔드 (`backend/requirements.txt`)

| 패키지 | 버전 | 용도 |
|--------|------|------|
| `fastapi` | 0.136.3 | REST API 서버 |
| `uvicorn` | 0.49.0 | ASGI 서버 (CMD 진입점) |
| `neo4j` | 6.2.0 | Neo4j 공식 Python 드라이버 |
| `anthropic` | (scripts 전용, pip 별도) | LLM 데이터 생성 스크립트에서만 사용 |

### 프론트엔드 (`frontend/package.json`)

| 패키지 | 버전 | 용도 |
|--------|------|------|
| `react` | ^19.2.6 | UI 라이브러리 |
| `react-dom` | ^19.2.6 | DOM 렌더러 |
| `maplibre-gl` | ^5.24.0 | 지도 렌더링 |
| `lucide-react` | ^1.17.0 | 아이콘 |
| `vite` | ^8.0.12 | 번들러/빌드 도구 |
| `@vitejs/plugin-react` | ^6.0.1 | Vite React 플러그인 |
| `eslint` | ^10.3.0 | 린터 |
| `eslint-plugin-react-hooks` | ^7.1.1 | Hooks 린트 |
| `eslint-plugin-react-refresh` | ^0.5.2 | HMR 린트 |

## 패키지 매니저

- 프론트엔드: `npm` (`frontend/package-lock.json` 존재)
- 백엔드: `pip` (컨테이너 빌드 시 `requirements.txt`로 설치)

## 빌드 도구

- 프론트엔드 번들: `vite build` → `frontend/dist/` 정적 파일 생성
  - `vite.config.js`에서 `manualChunks`로 `maplibre` / `vendor` 청크 분리 (코드 스플리팅)
- 백엔드 컨테이너: `docker compose build api` (Docker 멀티스테이지 없음, 단일 `FROM python:3.12-slim`)
- 배포 자동화: `deploy.sh` (빌드 → Docker Compose 재기동 → 데이터 주입 순서)

## 인프라 / 컨테이너

- 오케스트레이션: `docker-compose.yml` (Docker Compose v2)
- 서비스 구성:
  - `neo4j` — Neo4j 5 공식 이미지, 포트 7474/7687 (localhost 바인딩)
  - `api` — FastAPI/Uvicorn, 포트 8000 (내부 전용)
  - `nginx` — 포트 8080→80 노출, `frontend/dist` 정적 서빙 + `/api/` → `api:8000` 프록시

## 환경 설정 파일 목록

| 파일 | 용도 |
|------|------|
| `.env` | `NEO4J_PASSWORD` 실제 값 (gitignore 대상) |
| `.env.example` | `.env` 템플릿 |
| `frontend/.env.production` | `VITE_API_URL=/api` 빌드타임 주입 |
| `docker-compose.yml` | 서비스·볼륨·포트 정의 |
| `backend/Dockerfile` | API 컨테이너 빌드 정의 |
| `nginx/nginx.conf` | nginx 라우팅·캐시 헤더 설정 |
