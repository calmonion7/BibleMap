---
last_mapped_commit: 9f47b78ed927ef302cefffb5b62ef71885b6aa94
mapped: 2026-06-19
---

# 기술 스택

## 언어 및 런타임

| 레이어 | 언어 | 버전 |
|--------|------|------|
| 백엔드 | Python | 3.12 (Dockerfile 기준) |
| 프론트엔드 | JavaScript (ESM) | Node 런타임, Vite 번들링 |

## 백엔드

**프레임워크:** FastAPI 0.136.3  
**ASGI 서버:** Uvicorn 0.49.0 (`app.main:app`, 0.0.0.0:8000)  
**DB 클라이언트:** neo4j Python 드라이버 6.2.0 (Bolt 프로토콜)

진입점: `backend/app/main.py`  
DB 연결: `backend/app/db.py` — 싱글턴 드라이버, 환경변수(`NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`)로 구성  
라우터 모듈 4개: `backend/app/routes/nodes.py`, `backend/app/routes/events.py`, `backend/app/routes/search.py`, `backend/app/routes/books.py`

미들웨어: `CORSMiddleware` — `allow_origins=["*"]`, GET 메서드만 허용

시작 시 자동 인덱스 생성 (lifespan): `Person`, `Place`, `Event`, `PeopleGroup`, `Book` 노드의 `theographic_id` 필드

## 프론트엔드

**빌드 도구:** Vite 8.0.12 (`frontend/vite.config.js`)  
**UI 프레임워크:** React 19.2.6 + React DOM 19.2.6  
**지도 라이브러리:** MapLibre GL 5.24.0  
**아이콘:** Lucide React 1.17.0  
**번들 분리:** `manualChunks` — maplibre-gl → `maplibre` 청크, 나머지 node_modules → `vendor` 청크

소스 구성:
- `frontend/src/App.jsx` — 루트 컴포넌트, 탭(지도/타임라인) 전환
- `frontend/src/MapView.jsx` — MapLibre GL 지도, 장소 마커·사건 링 애니메이션
- `frontend/src/TimelineView.jsx` — 사건 타임라인, 구절 드릴다운
- `frontend/src/SidePanel.jsx` — 노드 상세 사이드 패널
- `frontend/src/api.js` — 공유 API 클라이언트 (`apiGet` 헬퍼)
- `frontend/src/VerseLangTabs.jsx` — 구절 언어 탭
- `frontend/src/theme.js` — 색상·타입 상수
- `frontend/src/convexHull.js` — 볼록 껍질 계산 유틸

## 데이터베이스

**Neo4j 5** (Docker 공식 이미지 `neo4j:5`)  
포트: 7474(HTTP), 7687(Bolt) — 호스트에서 127.0.0.1로만 노출  
볼륨: `neo4j_data` (named volume)  
인증: `NEO4J_AUTH=neo4j/<NEO4J_PASSWORD>`

노드 레이블: `Person`, `Place`, `Event`, `PeopleGroup`, `Book`  
주요 관계: `HAS_PARTICIPANT`, `OCCURS_AT`, `MEMBER_OF`, `CONTAINS_BOOK`, `PARENT_OF`, `SIBLING_OF`, `SPOUSE_OF`

## 리버스 프록시

**Nginx Alpine** — 80포트 수신, 외부 8080 매핑  
설정: `nginx/nginx.conf`  
- `/api/` → `http://api:8000/` 프록시 (헤더: Host, X-Real-IP, X-Forwarded-For/Proto)  
- `index.html` → `Cache-Control: no-cache, no-store, must-revalidate`  
- JS/CSS/이미지 정적 애셋 → `Cache-Control: public, max-age=31536000, immutable`  
- 그 외 → `try_files $uri /index.html` (SPA 라우팅)  
서빙 루트: `./frontend/dist` (빌드 산출물 마운트, HMR 아님)

## 오케스트레이션

**Docker Compose** (`docker-compose.yml`)  
서비스 3개: `neo4j`, `api`, `nginx`  
의존성 체인: `nginx` → `api` → `neo4j`

## 설정 파일 목록

| 파일 | 용도 |
|------|------|
| `docker-compose.yml` | 서비스 정의 |
| `backend/Dockerfile` | API 이미지 빌드 |
| `backend/requirements.txt` | Python 의존성 |
| `frontend/package.json` | NPM 의존성 및 스크립트 |
| `frontend/vite.config.js` | Vite 빌드 설정 |
| `frontend/eslint.config.js` | ESLint (flat config) |
| `frontend/.env.production` | `VITE_API_URL=/api` — 프로덕션 빌드 시 주입 |
| `.env` | `NEO4J_PASSWORD` (로컬 시크릿, git-ignore) |
| `.env.example` | 환경변수 템플릿 |
| `nginx/nginx.conf` | Nginx 라우팅 규칙 |

## 데이터 파이프라인 스크립트 (오프라인 실행)

`backend/scripts/` — 런타임 앱과 별개로 Neo4j에 데이터를 적재하거나 오버레이 JSON을 생성하는 스크립트들. Python 3.12 환경에서 직접 실행.

의존성 (스크립트 전용):
- `anthropic` SDK — Claude API 호출 (4개 스크립트)
- `urllib.request` — 외부 JSON 다운로드 (표준 라이브러리)
- `neo4j` — DB 직접 쓰기
