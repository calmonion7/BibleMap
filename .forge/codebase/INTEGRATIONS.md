---
last_mapped_commit: ecdb7cb2ea1bf665b0690e62b4cf51261761072c
mapped: 2026-06-15
---

# External Integrations

## 데이터 저장소

**그래프 데이터베이스 — Neo4j 5:**
- Docker 이미지: `neo4j:5`
- 연결 프로토콜: Bolt (`bolt://neo4j:7687` Docker 내부 / `bolt://localhost:7687` 로컬)
- Python 드라이버: `neo4j` 6.2.0 (`backend/app/db.py`)
- 드라이버 싱글톤: `get_driver()` in `backend/app/db.py`
- 인덱스: FastAPI lifespan 기동 시 자동 생성 (`backend/app/main.py`) — Person·Place·Event·PeopleGroup·Book 노드의 `theographic_id`
- 인증 환경변수: `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`
- 데이터 볼륨: Docker named volume `neo4j_data` (호스트에 영속)

**파일 스토리지 — 로컬 JSON:**
- `data/names_ko/` — 한글 이름 매핑 (people, places, events, groups)
- `data/book_context/books.json` — 성경 권별 배경·주제·대표 구절 (Claude API 생성)
- `data/character_traits/people.json` — 인물 성품 키워드 (Claude API 생성)
- `frontend/dist/` — 프론트엔드 빌드 결과물 (nginx가 정적 서빙)

**캐시:**
- 없음

## 외부 API · 서비스

**지도 타일 — ESRI ArcGIS (공개 엔드포인트):**
- URL: `https://server.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}`
- 소비처: `frontend/src/MapView.jsx` (MapLibre GL 스타일 설정 인라인)
- 인증: 없음 (무료 공개 래스터 타일)

**지도 글리프 — Protomaps (공개 엔드포인트):**
- URL: `https://protomaps.github.io/basemaps-assets/fonts/{fontstack}/{range}.pbf`
- 소비처: `frontend/src/MapView.jsx` (MapLibre GL `glyphs` 설정)
- 인증: 없음

**원본 데이터 — Theographic Bible Metadata (GitHub Raw):**
- `https://raw.githubusercontent.com/robertrouse/theographic-bible-metadata/master/json/people.json`
- `https://raw.githubusercontent.com/robertrouse/theographic-bible-metadata/master/json/places.json`
- `https://raw.githubusercontent.com/robertrouse/theographic-bible-metadata/master/json/events.json`
- `https://raw.githubusercontent.com/robertrouse/theographic-bible-metadata/master/json/peopleGroups.json`
- 소비처: `backend/scripts/load_theographic.py` (일회성 데이터 적재 스크립트)
- `backend/scripts/generate_book_context.py` 에서 `books.json`도 동일 저장소에서 추가 fetch
- `backend/scripts/generate_person_traits.py` 에서 `people.json`, `events.json` fetch
- 인증: 없음 (공개 GitHub raw)

**LLM API — Anthropic Claude:**
- 클라이언트: `anthropic` Python SDK
- 모델: `claude-haiku-4-5-20251001`
- 소비처:
  - `backend/scripts/generate_book_context.py` — 성경 권별 배경/주제/대표구절 JSON 생성
  - `backend/scripts/generate_person_traits.py` — 인물 성품 키워드 JSON 생성
- 인증 환경변수: `ANTHROPIC_API_KEY`
- 사용 시점: 데이터 파이프라인 일회성 실행 시만 (런타임 API 호출 없음)
- 출력은 `data/book_context/books.json`, `data/character_traits/people.json`에 파일로 저장

## 내부 API (백엔드 → 프론트엔드)

**FastAPI 백엔드** (`backend/app/`) — GET 전용, 읽기 전용:

| 엔드포인트 | 소스 파일 | 설명 |
|---|---|---|
| `GET /node/{node_id}` | `backend/app/routes/nodes.py` | 노드 상세 + 이웃 목록 (Book은 topPersons·topEvents 추가) |
| `GET /node/{node_id}/places` | `backend/app/routes/nodes.py` | 노드에 연결된 지리좌표 목록 |
| `GET /node/{node_id}/neighbors/grouped` | `backend/app/routes/nodes.py` | 이웃 노드를 타입별로 그룹화 |
| `GET /events` | `backend/app/routes/events.py` | 전체 Event 목록 (sortKey ASC) |
| `GET /search?q=` | `backend/app/routes/search.py` | nameKo·name 전문 검색 (최대 20건) |

**프론트엔드 API 클라이언트:** `frontend/src/api.js`
- 기본 URL: `import.meta.env.VITE_API_URL` (빌드 타임) 또는 `http://localhost:8000` (폴백)
- 공통 헬퍼: `apiGet(path, { signal })` — GET, 비-OK 시 status 코드로 reject

**Nginx 리버스 프록시** (`nginx/nginx.conf`):
- `/api/*` → `http://api:8000/` (prefix 제거)
- 정적 파일: `frontend/dist/` (js/css/font은 1년 캐시, index.html은 no-cache)
- SPA fallback: 알 수 없는 경로 → `index.html`
- 외부 포트: 8080

**CORS:**
- `allow_origins=["*"]`, `allow_methods=["GET"]`, `allow_credentials=False` (`backend/app/main.py`)

## 인증 · 사용자 관리

- 없음. 모든 엔드포인트 공개 읽기 전용. 사용자 계정 없음.

## CI/CD · 배포

**호스팅:**
- Self-hosted macOS GitHub Actions 러너
- Docker Compose 프로젝트명: `biblemap`

**CI 파이프라인:**
- GitHub Actions: `.github/workflows/deploy.yml`
- 트리거: `main` 브랜치 push
- 실행 단계:
  1. `git fetch && git reset --hard origin/main`
  2. `bash deploy.sh`

**배포 스크립트** (`deploy.sh`):
1. `npm install && npm run build` — 프론트엔드 빌드 → `frontend/dist/`
2. `docker compose build api` — API 이미지 재빌드
3. `docker compose up -d api nginx` — api + nginx 컨테이너 재시작
4. `python3 backend/scripts/inject_ko_names.py` — `data/names_ko/*.json` → Neo4j 한글 이름 주입 (15회 재시도)

**로그 / 잠금:**
- 배포 로그: `/Users/calmonion/Library/Logs/com.biblemap.deploy.log`
- 잠금 파일: `/tmp/biblemap-deploy.lock` (동시 배포 방지)

## 모니터링 · 관측

- 에러 추적: 없음 (외부 서비스 미사용)
- 로그: `logging` stdlib — `backend/app/main.py` (인덱스 생성 실패 시만); 배포 로그 (`deploy.sh`)

## 웹훅 · 콜백

- 인바운드: 없음
- 아웃바운드: 없음

## 환경 변수 전체 목록

| 변수 | 설정 위치 | 용도 |
|---|---|---|
| `NEO4J_PASSWORD` | `.env` (호스트) | Neo4j 비밀번호 — 유일한 필수 설정값 |
| `NEO4J_URI` | `docker-compose.yml` (api 서비스) | `bolt://neo4j:7687` (Docker 내부) |
| `NEO4J_USER` | `docker-compose.yml` (api 서비스) | `neo4j` |
| `NEO4J_AUTH` | `docker-compose.yml` (neo4j 서비스) | `neo4j/${NEO4J_PASSWORD}` 로 자동 파생 |
| `VITE_API_URL` | 빌드 타임 (`npm run build`) | `/api` (프로덕션 nginx 프록시 경로) |
| `ANTHROPIC_API_KEY` | 스크립트 실행 환경 | Claude API — 스크립트 단독 실행 시만 |
