---
last_mapped_commit: f5e17ae2993e228f8b7481dba03478ddec8616f4
mapped: 2026-07-22
---

# STACK

BibleMap은 백엔드(FastAPI + Neo4j)와 프론트엔드(React 19 + Vite)로 구성된 단일 저장소이며, Docker Compose(`neo4j`·`api`·`nginx`)로 통합 기동한다. 파일별 디렉터리 구조는 `.forge/codebase/STRUCTURE.md` 참고(이 문서는 언어·프레임워크·의존성·빌드 설정에 집중).

## 언어·런타임

- **백엔드**: Python. 컨테이너 이미지는 `backend/Dockerfile`의 `FROM python:3.12-slim`. `README.md`는 개발 사전 준비로 Python 3.11+를 표기.
- **프론트엔드**: JavaScript(ES 모듈) + JSX, React 19. `frontend/package.json`은 `"type": "module"`.
- **인프라 스크립트**: Bash(`deploy.sh`), zsh 셸 환경(macOS).

## 백엔드 (`backend/`)

### 프레임워크·핵심 의존성 (`backend/requirements.txt`)

- `fastapi==0.136.3` — ASGI 웹 프레임워크. 앱 객체는 `backend/app/main.py`의 `app`.
- `neo4j==6.2.0` — 공식 Neo4j Python 드라이버(Bolt). 싱글턴은 `backend/app/db.py`의 `get_driver()`가 `NEO4J_URI`/`NEO4J_USER`/`NEO4J_PASSWORD` 환경변수로 생성(비번 미설정 시 `RuntimeError`).
- `uvicorn==0.49.0` — ASGI 서버. 컨테이너 기동 명령은 `uvicorn app.main:app --host 0.0.0.0 --port 8000`.

`requirements.txt` 밖의 스크립트 전용 의존성(런타임 이미지엔 미설치, 오프라인 실행 시 별도 설치 필요):

- `anthropic` — `generate_*` 스크립트 5개가 콘텐츠 생성에 사용(상세는 `.forge/codebase/INTEGRATIONS.md`).
- `kiwipiepy` — `backend/scripts/build_word_distribution.py`·`build_word_verse_index.py`가 한국어 형태소 분석(NNG/NNP 추출)에 사용. 두 스크립트 docstring이 임시 venv(`python -m venv /tmp/kiwi-venv && /tmp/kiwi-venv/bin/pip install kiwipiepy`) 설치를 안내.

### 앱 구조 (`backend/app/`)

- `backend/app/main.py` — FastAPI 앱 생성, CORS 미들웨어(`allow_origins=["*"]`, `allow_methods=["GET"]`, `allow_credentials=False`), `lifespan`에서 `Person`·`Place`·`Event`·`PeopleGroup`·`Book`의 `theographic_id` 인덱스를 `CREATE INDEX ... IF NOT EXISTS`로 준비(실패해도 경고 후 계속). `_configure_logging()`이 `logging.basicConfig(level=INFO)` + `neo4j`/`urllib3`/`asyncio` WARNING 승격 + `uvicorn`/`uvicorn.access` propagate 차단을 수행(uvicorn.error는 제외).
- `backend/app/db.py` — Neo4j 드라이버 싱글턴(`get_driver()`).
- `backend/app/overlays.py` — `data/` 저작 JSON 오버레이 로더. 탐색 우선순위는 `DATA_DIR`(기본 `/app/data`) → 저장소 `data/`, 파일 없으면 경고 로그 + 빈 데이터 폴백. 로더는 모두 `functools.lru_cache(maxsize=1)`: `book_events_raw()`·`event_verses()`·`bible_verses()`·`word_distribution()`·`books_ko()`·`chapter_summaries()`·`chapter_sections()`·`quotations()`·`verse_persons()` — 데이터 파일 변경 시 API 컨테이너 재시작 필요.
- `backend/app/routes/` — 12개 라우터 모듈, 모두 `main.py`에서 `include_router`: `nodes.py`, `events.py`, `search.py`, `books.py`(개요·본문 리더 장 목차/장별 본문·인용 관계), `persons.py`, `journey.py`, `places.py`, `tours.py`, `family.py`, `words.py`, `verses.py`, `reliance.py`.

### 데이터 생성/적재 스크립트 (`backend/scripts/`)

37개 독립 스크립트(런타임 API 컨테이너에는 포함되지 않음 — `backend/Dockerfile`은 `app/`만 COPY). 역할별 접두:

- `load_*.py`(8개) — theographic 원본 및 저작 데이터를 Neo4j에 최초 적재(`load_theographic.py`, `load_books.py`, `load_authored_events.py`, `load_authored_persons.py`, `load_authored_genealogy.py`, `load_authored_mothers.py`, `load_person_events.py`, `load_verse_events.py`).
- `inject_*.py`(6개) — Neo4j 기존 노드에 보정 필드 SET(`inject_ko_names.py`, `inject_date_corrections.py`, `inject_person_traits.py`, `inject_person_context.py`, `inject_book_context.py`, `inject_place_context.py`).
- `generate_*.py`(11개) — `data/` JSON 콘텐츠 생성. Anthropic Claude API 호출 5개(`generate_book_events.py`, `generate_book_context.py`, `generate_person_context.py`, `generate_person_traits.py`, `generate_verse_events.py`), getbible fetch 3개(`generate_bible_text.py`, `generate_verse_text.py`, `generate_person_event_verses.py`), theographic fetch 1개(`generate_event_verses.py`), 네트워크 미사용 로컬 산출 2개(`generate_approx_book_verses.py`, `generate_book_context_enrich.py` — 후자는 실행 스크립트가 아니라 재생성 레시피 docstring). 상세는 INTEGRATIONS.md.
- `build_*.py`(3개) — 파생 인덱스 산출(`build_word_distribution.py`, `build_word_verse_index.py`, `build_verse_persons.py`) — 셋 다 Neo4j 미접근.
- `validate_*.py`(7개) — 생성 데이터 정합성 검증, Neo4j 미접근·CI 없이 수동 실행: `validate_event_chronology.py`, `validate_traits.py`, `validate_person_context.py`, `validate_god_reliance.py`, `validate_chapter_summaries.py`, `validate_chapter_sections.py`, `validate_quotations.py`.
- 기타(2개): `apply_event_dedupe.py`, `enrich_place_coords.py`.

스크립트는 대부분 `urllib.request`로 외부 JSON을 fetch하거나 `neo4j.GraphDatabase`로 직접 DB에 쓴다(FastAPI를 거치지 않음). 호스트에서 직접 실행 시 Neo4j 기본 접속은 `bolt://localhost:7687`. README.md의 최초 셋업 순서: `load_theographic.py` → `inject_ko_names.py` → `inject_date_corrections.py`.

## 프론트엔드 (`frontend/`)

### 프레임워크·의존성 (`frontend/package.json`)

런타임 의존성: `react ^19.2.6`, `react-dom ^19.2.6`, `maplibre-gl ^5.24.0`(WebGL 지도, `frontend/src/MapView.jsx`), `lucide-react ^1.17.0`(아이콘).

개발 의존성: `vite ^8.0.12` + `@vitejs/plugin-react ^6.0.1`, `eslint ^10.3.0` + `@eslint/js` + `eslint-plugin-react-hooks` + `eslint-plugin-react-refresh` + `globals`(`frontend/eslint.config.js`), `@types/react`/`@types/react-dom`.

스크립트: `dev`(vite), `build`(vite build), `lint`(eslint .), `preview`(vite preview).

### 빌드 설정 (`frontend/vite.config.js`)

`define.__BUILD_ID__`에 `JSON.stringify(String(Date.now()))` 주입 — 빌드마다 바뀌는 문자열 상수로, `frontend/src/api.js`가 모든 API 요청에 `?v=`로 실어 배포 직후 브라우저의 옛 캐시 응답(백엔드 `Cache-Control: max-age=...`) 재사용을 막는다. `build.rollupOptions.output.manualChunks`로 `node_modules` 중 `maplibre-gl`은 `maplibre` 청크, 나머지는 `vendor` 청크로 분리.

### 엔트리·API 접근

- `frontend/index.html` → `frontend/src/main.jsx` → `App.jsx` 마운트.
- API 접근은 `frontend/src/api.js`의 `apiGet()` 단일 헬퍼로 통일. 베이스 URL은 `import.meta.env.VITE_API_URL || 'http://localhost:8000'`. 저장소 전체에서 다른 fetch 호출 지점 없음(확인됨).
- 산출물 `frontend/dist/`(`.gitignore` 처리) — docker-compose가 nginx 컨테이너에 read-only 마운트.
- `frontend/public/fonts/im-fell-english-latin.woff2` — 자체 호스팅 웹폰트(IM Fell English, OFL 라이선스 `frontend/public/fonts/IM-Fell-English-OFL.txt`), 외부 폰트 CDN 미사용.

### 프론트엔드 환경변수

`frontend/.env.production` — `VITE_API_URL=/api`(빌드타임 주입, nginx 프록시 경로).

## 빌드·구성·배포 파일

- `docker-compose.yml` — `neo4j`(image `neo4j:5`)·`api`(build `./backend`)·`nginx`(image `nginx:alpine`) 3서비스. 상세는 INTEGRATIONS.md.
- `backend/Dockerfile` — `python:3.12-slim`, `requirements.txt` 설치 후 `app/`만 복사(스크립트·데이터 미포함), uvicorn 기동.
- `nginx/nginx.conf` — 정적 자산 서빙 + `/api/` 리버스 프록시.
- `deploy.sh` — 프론트 빌드 → API 이미지 빌드 → 컨테이너 재기동 → 한글 이름 주입의 4단계 배포 스크립트(lock 파일 + 로그 포함). `load_*`·`inject_*`(`inject_ko_names.py` 제외)는 실행하지 않는다.
- `.github/workflows/deploy.yml` — `main` push 시 self-hosted 러너에서 `deploy.sh` 실행.
- `.env` / `.env.example` — 루트 레벨, 키는 `NEO4J_PASSWORD`뿐(compose가 `NEO4J_AUTH`를 `neo4j/<password>`로 파생). `.env`는 `.gitignore` 처리.

## 실행 방법 요약 (`README.md`)

개발: `docker compose up -d`(Neo4j) → `load_theographic.py`·`inject_ko_names.py`·`inject_date_corrections.py`로 데이터 적재 → `python3 -m uvicorn backend.app.main:app --reload`(:8000) → `cd frontend && npm run dev`(:5173). 로컬 통합 검증은 `frontend/dist`를 nginx가 read-only 마운트하므로 `npm run build` 후 `docker compose up -d --build api`로 확인(:8080, HMR 아님).
