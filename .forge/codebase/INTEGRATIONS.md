---
last_mapped_commit: 79f9d9df07c0d79f8fa07940e3f76c8d5424524b
mapped: 2026-06-28
---
# 외부 연동

**분석 일자:** 2026-06-28

## 런타임 vs 빌드타임 경계

핵심 구분: **앱 런타임(FastAPI + 브라우저)은 Neo4j와 지도 타일 외 외부 서비스를 호출하지 않는다.** Theographic·getbible·Anthropic 호출은 전부 **빌드/데이터 준비 스크립트** (`backend/scripts/`)에서만 발생하며, 결과는 Neo4j 또는 `data/*.json`에 미리 구워진다(ADR-0003 "미리굽기"). `backend/app/` 전체에 `urlopen`·`requests`·`anthropic` 임포트가 없음을 grep으로 확인.

## API 및 외부 서비스

**지도 타일/폰트 (프론트엔드 런타임, 브라우저 → 외부 직접):**
- Esri ArcGIS World Map 래스터 타일 — `https://server.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}` (`frontend/src/MapView.jsx`의 maplibre `style.sources.esri`)
- Protomaps basemap 폰트(글리프) — `https://protomaps.github.io/basemaps-assets/fonts/{fontstack}/{range}.pbf` (`frontend/src/MapView.jsx`의 `style.glyphs`)
- 인증 없음(공개 타일/폰트). SDK 없이 maplibre-gl이 직접 요청

**성경 본문 (빌드타임 전용):**
- getbible v2 — `https://api.getbible.net/v2/{slug}/{book_order}/{chapter}.json` (`backend/scripts/generate_verse_text.py`)
  - SDK/클라이언트: `urllib.request` (표준 라이브러리)
  - 인증: 없음. 단, 기본 `Python-urllib` UA에 403을 주므로 브라우저류 User-Agent 헤더로 요청
  - 번역 슬러그: `korean`(한국어), `kjv`(영어) — `TRANSLATIONS` 상수
  - 결과는 `data/event_verses/`, `data/book_context/`, `data/character_traits/`, `data/place_context/` JSON에 `textKo`/`textEn` 등으로 인라인 저장(멱등 캐시)

**LLM 콘텐츠 생성 (빌드타임 전용):**
- Anthropic Claude API — `anthropic.Anthropic` Python SDK, 모델 `claude-haiku-4-5-20251001`
  - SDK/클라이언트: `anthropic` (Python). `requirements.txt`에 없어 스크립트 실행 시 별도 설치
  - 인증: `ANTHROPIC_API_KEY` 환경변수 (미설정 시 RuntimeError)
  - 사용처: `backend/scripts/generate_book_context.py`, `generate_book_events.py`, `generate_person_traits.py`, `generate_verse_events.py`
  - 산출물: `data/book_context/`, `data/book_events/`, `data/character_traits/`, `data/verse_events/` JSON

**성경 메타데이터 시드 (빌드타임 전용):**
- Theographic Bible Metadata (GitHub raw) — `https://raw.githubusercontent.com/robertrouse/theographic-bible-metadata/master/json/{people,places,events,peopleGroups}.json` (`backend/scripts/load_theographic.py`, `enrich_place_coords.py`)
  - SDK/클라이언트: `urllib.request`
  - 인증: 없음(공개 raw 파일)
  - 노드 `theographic_id` 프로퍼티의 출처. Neo4j에 MERGE로 멱등 적재

## 데이터 저장소

**데이터베이스:**
- Neo4j 5 (그래프 DB) — 앱의 유일한 데이터 저장소
  - 연결: `NEO4J_URI`(compose 내부 `bolt://neo4j:7687`, 로컬 기본 `bolt://localhost:7687`), `NEO4J_USER`, `NEO4J_PASSWORD`
  - 클라이언트: `neo4j` Python 드라이버 6.2.0. 모듈 전역 싱글톤 드라이버 (`backend/app/db.py`의 `get_driver()`, `_driver` 캐시)
  - 라우트는 `driver.session()` 컨텍스트로 인라인 Cypher 실행 (`backend/app/routes/*.py`)
  - 인덱스: 앱 lifespan 기동 시 `Person`/`Place`/`Event`/`PeopleGroup`/`Book`의 `theographic_id` 인덱스를 `IF NOT EXISTS`로 생성 (`backend/app/main.py`). 실패해도 인덱스 없이 진행
  - 포트는 `127.0.0.1`에만 바인딩 — 외부 비노출 (`docker-compose.yml`)

**파일 저장소:**
- 로컬 파일시스템만. `data/`가 API 컨테이너에 `./data:/app/data`로 마운트 (`docker-compose.yml`). 시드/생성 JSON은 git 커밋됨

**시드/소스 데이터 (`data/` 하위, 빌드타임 산출):**
- `place_coords/`, `place_context/`, `person_events/`(인물별 파일), `authored_events/`, `book_events/`, `book_context/`, `book_years_approx/`, `character_traits/`, `event_verses/`, `verse_events/`, `names_ko/`(books·events·groups 등 한글명)

**캐싱:**
- 없음(별도 캐시 서비스 미사용). getbible 본문은 빌드타임 인메모리 + JSON 파일 캐시로 런타임 호출을 제거

## 인증 및 신원

- 최종 사용자 인증 없음. 앱은 공개 읽기 전용 SPA
- API CORS: `allow_origins=["*"]`, `allow_credentials=False`, `allow_methods=["GET"]` (`backend/app/main.py`). GET 전용 공개 API
- Neo4j 인증: `NEO4J_AUTH=neo4j/<NEO4J_PASSWORD>` (compose가 파생)
- 외부 자격증명: getbible·Esri·Protomaps·Theographic은 모두 인증 없음. Anthropic만 `ANTHROPIC_API_KEY`(스크립트 한정)

## 모니터링 및 관측성

**에러 추적:**
- 외부 서비스 없음. 백엔드는 표준 `logging`만 사용(예: Neo4j 인덱스 생성 실패 시 `logging.exception`, `backend/app/main.py`)

**로그:**
- 배포 로그: `deploy.sh`가 `/Users/calmonion/Library/Logs/com.biblemap.deploy.log`에 append
- 컨테이너 로그: docker 기본(stdout)

## CI/CD 및 배포

**호스팅:**
- self-hosted 단일 머신(docker compose, 프로젝트명 `biblemap`). nginx가 `8080`에서 SPA 서빙 + `/api/` → `api:8000` 프록시 (`nginx/nginx.conf`)

**CI 파이프라인:**
- GitHub Actions, `runs-on: self-hosted` (`.github/workflows/deploy.yml`)
  - 트리거: `main` push
  - 동작: `git fetch origin` → `git reset --hard origin/main` → `bash deploy.sh`
- 원격: `https://github.com/calmonion7/BibleMap.git`

## 환경 설정

**필수 환경변수:**
- `NEO4J_PASSWORD` — 앱 런타임·compose·스크립트 공통(필수)
- `NEO4J_URI`, `NEO4J_USER` — 기본값 존재(런타임/스크립트)
- `ANTHROPIC_API_KEY` — generate_* 스크립트 한정
- `VITE_API_URL` — 프론트 빌드타임(프로덕션 `/api`, `frontend/.env.production`)

**시크릿 위치:**
- 루트 `.env` (gitignore). `.env.example`은 `NEO4J_PASSWORD` 자리표시자만 포함
- `deploy.sh`가 `.env`를 `set -a; . "$WORKTREE/.env"`로 로드(호스트 직접 실행 스크립트가 동일 비번 사용)

## 웹훅 및 콜백

**수신:**
- 애플리케이션 웹훅 없음. GitHub → self-hosted 러너 트리거(push)가 유일한 인커밍 이벤트

**발신:**
- 없음

---

*연동 감사: 2026-06-28*
