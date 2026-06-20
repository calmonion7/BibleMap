---
last_mapped_commit: 7522aafe2088e83e8c4bed86a4f0269082db07e0
mapped: 2026-06-20
---

# Technology Stack

## 언어

**프론트엔드:**
- JavaScript (ES Module) — `frontend/src/` 전체. JSX 문법 사용 (`.jsx` 확장자).
- TypeScript는 사용하지 않음. `@types/react`, `@types/react-dom` 은 devDependency로 선언되어 있으나 실제 소스는 순수 JS.

**백엔드:**
- Python 3.12 — `backend/app/` 및 `backend/scripts/`. `backend/Dockerfile`에서 `python:3.12-slim` 베이스 이미지 지정.

## 런타임

**프론트엔드 빌드 도구:**
- Vite 8.x (`frontend/vite.config.js`) — 개발 서버 및 프로덕션 번들링.
- `@vitejs/plugin-react` 6.x — React JSX 트랜스폼.
- 번들 분리: `vite.config.js`의 `manualChunks`로 `maplibre-gl` → `maplibre` 청크, 나머지 `node_modules` → `vendor` 청크로 분리.

**백엔드 ASGI 서버:**
- uvicorn 0.49.0 — `CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]` (`backend/Dockerfile`).

**패키지 관리자:**
- npm — `frontend/package.json`. `package-lock.json` 존재 여부는 `.gitignore` 확인 필요.
- pip — `backend/requirements.txt`. lockfile 없음(핀 버전만 지정).

## 프레임워크

**프론트엔드:**
- React 19.x (`frontend/package.json`) — 함수형 컴포넌트 + Hooks 방식. 라우터 없음(단일 페이지 상태 분기).
- 상태관리 라이브러리 없음 — `useState` / `useEffect` / 커스텀 훅(`useNodeSelection.js`, `useSearch.js`) 직접 사용.

**백엔드:**
- FastAPI 0.136.3 (`backend/requirements.txt`) — `backend/app/main.py`에서 `FastAPI` 인스턴스 생성.
- `lifespan` 핸들러에서 앱 시작 시 Neo4j 인덱스 자동 생성.
- CORS: `allow_origins=["*"]`, `allow_methods=["GET"]` — 읽기 전용 공개 API.

## 핵심 의존성

**프론트엔드:**

| 패키지 | 버전 | 역할 |
|--------|------|------|
| `maplibre-gl` | ^5.24.0 | 지도 렌더링 (`frontend/src/MapView.jsx`) |
| `lucide-react` | ^1.17.0 | 아이콘 (`frontend/src/SidePanel.jsx` 등) |
| `react` | ^19.2.6 | UI 프레임워크 |
| `react-dom` | ^19.2.6 | DOM 렌더링 |

**백엔드:**

| 패키지 | 버전 | 역할 |
|--------|------|------|
| `fastapi` | 0.136.3 | REST API 프레임워크 |
| `neo4j` | 6.2.0 | Neo4j 공식 Python 드라이버 (`backend/app/db.py`) |
| `uvicorn` | 0.49.0 | ASGI 서버 |
| `anthropic` | (스크립트만) | 데이터 생성 스크립트에서만 사용. `backend/requirements.txt` 미포함 — 스크립트 실행 시 별도 설치 필요. |

> `anthropic` 패키지는 `backend/scripts/generate_book_events.py`, `generate_book_context.py`, `generate_person_traits.py`, `generate_verse_events.py`에서 import하지만 `requirements.txt`에 없음. 스크립트는 앱 컨테이너 외부에서 수동 실행 용도.

## 인프라

**컨테이너 오케스트레이션:**
- Docker Compose (`docker-compose.yml`) — `neo4j`, `api`, `nginx` 세 서비스.

**서비스 구성:**

| 서비스 | 이미지/빌드 | 노출 포트 |
|--------|------------|-----------|
| `neo4j` | `neo4j:5` (공식) | `127.0.0.1:7474`, `127.0.0.1:7687` (로컬호스트 한정) |
| `api` | `./backend` (Dockerfile 빌드) | 컨테이너 내부 `:8000` (외부 미노출) |
| `nginx` | `nginx:alpine` | `:8080 → 80` |

**볼륨:**
- `neo4j_data` — 네임드 볼륨으로 그래프 데이터 영속.
- `./data:/app/data` — 오버레이 JSON 파일(`data/` 디렉터리) api 컨테이너에 바인드 마운트.
- `./frontend/dist:/usr/share/nginx/html:ro` — Vite 빌드 산출물을 nginx에 읽기전용 마운트.

## 설정 및 환경변수

**루트 수준 (`.env`, `.env.example`):**
- `NEO4J_PASSWORD` — Neo4j 비밀번호. `docker-compose.yml`이 `NEO4J_AUTH=neo4j/${NEO4J_PASSWORD}`로 파생.

**프론트엔드 (`frontend/.env.production`):**
- `VITE_API_URL=/api` — 프로덕션 빌드 시 nginx 프록시 경로 사용. 개발 시 미설정이면 `http://localhost:8000` fallback (`frontend/src/api.js`).

**백엔드 (컨테이너 환경변수, `docker-compose.yml`):**
- `NEO4J_URI=bolt://neo4j:7687`
- `NEO4J_USER=neo4j`
- `NEO4J_PASSWORD=${NEO4J_PASSWORD}`
- `DATA_DIR` — 선택적. 미설정 시 `/app/data` fallback (`backend/app/overlays.py`).

**스크립트 전용:**
- `ANTHROPIC_API_KEY` — Claude API 호출 스크립트에서 필요. 앱 컨테이너에는 불필요.

## 빌드 절차

**프론트엔드 (수동/CI):**
```bash
cd frontend && npm install && npm run build
# 출력: frontend/dist/
```
`.env.production`의 `VITE_API_URL=/api`가 빌드타임에 자동 주입됨.

**API 이미지:**
```bash
docker compose -p biblemap build api
```

**전체 배포 (`deploy.sh`):**
```bash
bash deploy.sh  # 프론트 빌드 → API 이미지 빌드 → 컨테이너 재시작 → 한글 이름 주입
```

## 코드 품질

**Linting:**
- ESLint 10.x (`frontend/eslint.config.js`) — `eslint-plugin-react-hooks`, `eslint-plugin-react-refresh` 포함.
- 대상 파일: `**/*.{js,jsx}`. `dist/` 디렉터리 제외.

**테스트:**
- 자동화 테스트 없음. Playwright(`/opt/homebrew` 설치)로 UI 동작을 수동 검증.

## 데이터 파일 레이어

`data/` 디렉터리의 JSON 파일은 데이터 생성 스크립트(`backend/scripts/`)가 오프라인으로 생성하고 git 커밋. 런타임에 `backend/app/overlays.py`가 읽어 Neo4j 쿼리 결과와 병합:

| 디렉터리 | 내용 |
|---------|------|
| `data/book_events/` | 성경책 → 타임라인 이벤트 매핑 |
| `data/book_years_approx/` | 추정 연도 배치 데이터 |
| `data/book_context/` | 책별 요약·핵심 절 |
| `data/character_traits/` | 인물 특성 및 절 인용 |
| `data/event_verses/` | 이벤트 → 절 매핑 (8MB JSON) |
| `data/authored_events/` | 저자 이벤트 오버레이 |
| `data/person_events/` | 주요 인물별 이벤트 |
| `data/place_coords/` | 장소 좌표 보강 |
| `data/names_ko/` | 한국어 이름 매핑 |
| `data/verse_events/` | 절 → 이벤트 역방향 매핑 |

---

*Stack analysis: 2026-06-20*
