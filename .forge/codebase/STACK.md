---
last_mapped_commit: 23e41eee5bbfdd1fbd7a942d7fb14b1df1620d3d
mapped: 2026-07-16
---

# STACK

BibleMap은 백엔드(FastAPI + Neo4j)와 프론트엔드(React 19 + Vite)로 구성된 단일 저장소이며, Docker Compose(neo4j·api·nginx)로 통합 기동한다. 저장소 루트는 `/Users/calmonion/Project/BibleMap`이다.

## 언어·런타임

- **백엔드**: Python 3.12 (`backend/Dockerfile`의 `FROM python:3.12-slim`). `README.md`는 개발 사전 준비로 Python 3.11+를 표기(런타임 이미지는 3.12).
- **프론트엔드**: JavaScript(ES 모듈), React 19. `frontend/package.json`은 `"type": "module"`.
- **인프라 스크립트**: Bash (`deploy.sh`), zsh 셸 환경.

## 백엔드 (`backend/`)

### 프레임워크·핵심 의존성 (`backend/requirements.txt`)

- `fastapi==0.136.3` — ASGI 웹 프레임워크. 앱은 `backend/app/main.py`의 `app` 객체.
- `neo4j==6.2.0` — 공식 Neo4j Python 드라이버(Bolt). 드라이버 싱글턴은 `backend/app/db.py`의 `get_driver()`가 `NEO4J_URI`/`NEO4J_USER`/`NEO4J_PASSWORD` 환경변수로 생성(비번 미설정 시 `RuntimeError`).
- `uvicorn==0.49.0` — ASGI 서버. 컨테이너 기동 명령은 `uvicorn app.main:app --host 0.0.0.0 --port 8000`.

`requirements.txt` 밖의 스크립트 전용 의존성(런타임 이미지에 미설치):

- `anthropic` — `generate_*` 스크립트 5개가 import (INTEGRATIONS 참조).
- `kiwipiepy` — `backend/scripts/build_word_distribution.py`·`build_word_verse_index.py`가 한국어 명사(NNG·NNP) 추출에 사용. 두 스크립트는 STOPWORDS·토큰화 규약을 공유(후자가 전자에서 import). docstring이 임시 venv(`/tmp/kiwi-venv`) 설치 실행을 안내.

### 앱 구조 (`backend/app/`)

- `backend/app/main.py`(63줄) — FastAPI 앱 생성, CORS 미들웨어(`allow_origins=["*"]`, `allow_methods=["GET"]`, credentials 미허용), `lifespan`에서 `Person·Place·Event·PeopleGroup·Book`의 `theographic_id` 인덱스를 `CREATE INDEX ... IF NOT EXISTS`로 준비(실패해도 경고 후 계속). 로깅은 `_configure_logging()`으로 `logging.basicConfig(level=INFO)` + `neo4j·urllib3·asyncio` WARNING 승격, `uvicorn`/`uvicorn.access` propagate 차단.
- `backend/app/db.py`(15줄) — Neo4j 드라이버 싱글턴.
- `backend/app/overlays.py`(87줄) — `data/` 저작 JSON 오버레이 로더. 탐색 우선순위는 `DATA_DIR`(기본 `/app/data`) → 저장소 `data/`, 파일 없으면 빈 데이터 폴백. `book_events_raw()`·`event_verses()`·`bible_verses()`·`word_distribution()`·`books_ko()`·`word_verse_index()`·`verse_persons()` 7개 로더가 각각 `functools.lru_cache(maxsize=1)` — 데이터 파일 변경 시 API 컨테이너 재시작 필요. `word_verse_index()`는 현재 어떤 라우트도 소비하지 않는 인프라 전용 로더.
- `backend/app/routes/` — 12개 라우터 모듈, 모두 `main.py`에서 `include_router`:
  - `nodes.py`(309줄) — `/node/{id}`, `/node/{id}/places`, `/node/{id}/neighbors/grouped`, `/person/{id}/event-ids`.
  - `persons.py`(324줄) — `/persons/curated`, `/keypeople-cards`, `/person/{id}/connections`, `/person/{id}/relations`. `_NAME_KO`를 `reliance.py`가 재사용.
  - `events.py`(135줄) — `/events`, `/event/{id}/verses`.
  - `books.py`(30줄) — `/books-overview`.
  - `places.py`(76줄) — `/place/{id}/curated-persons`.
  - `journey.py`(137줄) — `/person/{id}/journey`.
  - `tours.py`(158줄) — `/tours`, `/tour/{id}`.
  - `search.py`(43줄) — `/search`.
  - `family.py`(172줄) — `/person/{id}/family` (가계도 서브그래프).
  - `words.py`(44줄) — `/words/{book_id}`, `/words/{book_id}/verses` (단어 분포 — Neo4j 미접근, 오버레이 전용. 구절 매칭은 substring, `VERSE_LIMIT=200`).
  - `verses.py`(48줄, 신규) — `/verse/{verse_id}/persons`. `overlays.verse_persons()`로 rec id 목록을 얻고 Neo4j에서 우리가 적재한 `Person`만 이름 해석(미적재 rec id는 id만 반환).
  - `reliance.py`(174줄, 신규) — `/person/{person_id}/reliance`, `/reliance/ranking`. `data/god_reliance/<slug>.json`을 정본으로 서빙. slug↔`theographic_id` 매핑은 `person_events/<slug>.json`의 `participants[0]`로 역산(`journey.py`와 동형 패턴). 응답에 `Cache-Control: public, max-age=3600` 헤더.

### 데이터·스크립트 (`backend/scripts/`)

Python 스크립트 33개(`__init__.py` 제외). 역할별 대별:

- **적재(load_*)**: `load_theographic.py`(theographic 원본 → Neo4j 배치 적재), `load_books.py`, `load_authored_events.py`, `load_authored_persons.py`, `load_authored_genealogy.py`, `load_person_events.py`, `load_verse_events.py`.
- **주입(inject_*)**: `inject_ko_names.py`(한글 이름 — `deploy.sh` 4단계에서 재시도 실행), `inject_date_corrections.py`, `inject_person_traits.py`, `inject_person_context.py`, `inject_book_context.py`, `inject_place_context.py`.
- **생성(generate_*)**: `generate_book_events.py`, `generate_book_context.py`, `generate_book_context_enrich.py`, `generate_person_context.py`, `generate_person_traits.py`, `generate_verse_events.py`, `generate_verse_text.py`, `generate_bible_text.py`, `generate_event_verses.py`, `generate_person_event_verses.py`, `generate_approx_book_verses.py`. 이 중 5개(`generate_book_events.py`·`generate_book_context.py`·`generate_person_context.py`·`generate_person_traits.py`·`generate_verse_events.py`)는 Anthropic Claude API를 호출한다(INTEGRATIONS 참조).
- **집계(build_*)**: `build_word_distribution.py` — `data/bible/verses.json`의 textKo를 kiwipiepy로 형태소 분석해 책별(상위 60)·전체(상위 120) 명사 빈도를 집계하고 `data/word_sentiment.json`의 극성을 병합해 `data/word_distribution.json`을 산출. `build_word_verse_index.py`(신규) — 같은 토큰화 규약(NNG/NNP·len≥2·STOPWORDS, 전자에서 import)으로 `단어(lemma) → [verseID,...]` 역색인 `data/word_verse_index/index.json`을 산출(집계 아닌 색인이라 최소빈도 필터 없음). `build_verse_persons.py`(신규) — theographic `verses.json`의 `people` 필드를 그대로 투영해 `data/verse_persons/index.json`(`verseID → [personRecId,...]`)을 산출(네트워크 fetch, Neo4j 불필요). 세 스크립트 모두 Neo4j 미접근.
- **검증·후처리**: `validate_event_chronology.py`, `validate_traits.py`, `validate_person_context.py`, `validate_god_reliance.py`(신규, `data/god_reliance/*.json` 스키마·근거절 검증), `apply_event_dedupe.py`, `enrich_place_coords.py`(`data/place_coords/places.json` → Place 노드 멱등 적재).

스크립트는 대부분 `urllib.request`로 외부 JSON을 fetch하고 `neo4j.GraphDatabase`로 직접 DB에 쓴다(FastAPI를 거치지 않음). 호스트 직접 실행 시 Neo4j 기본 접속은 `bolt://localhost:7687`.

## 프론트엔드 (`frontend/`)

### 프레임워크·의존성 (`frontend/package.json`)

런타임 의존성:

- `react ^19.2.6`, `react-dom ^19.2.6` — React 19.
- `maplibre-gl ^5.24.0` — 지도 렌더링(WebGL). `frontend/src/MapView.jsx`에서 인라인 스타일 구성.
- `lucide-react ^1.17.0` — 아이콘.

개발 의존성:

- `vite ^8.0.12` + `@vitejs/plugin-react ^6.0.1` — 빌드/개발 서버.
- `eslint ^10.3.0` + `@eslint/js ^10.0.1` + `eslint-plugin-react-hooks ^7.1.1` + `eslint-plugin-react-refresh ^0.5.2` + `globals ^17.6.0` (`frontend/eslint.config.js`).
- `@types/react ^19.2.14`, `@types/react-dom ^19.2.3`.

### 스크립트 (`frontend/package.json`)

`dev`(vite), `build`(vite build), `lint`(eslint .), `preview`(vite preview).

### 빌드 설정 (`frontend/vite.config.js`)

`@vitejs/plugin-react` 사용. `define.__BUILD_ID__`에 `JSON.stringify(String(Date.now()))`를 주입 — 빌드마다 바뀌는 문자열 상수로, `frontend/src/api.js`가 모든 API 요청에 `?v=`로 실어 배포 직후 브라우저의 옛 캐시 응답(백엔드 `max-age=3600`) 재사용을 막는다(같은 빌드 안에서는 값 고정이라 1시간 캐시 이점 유지). `build.rollupOptions.output.manualChunks`로 `node_modules` 중 `maplibre-gl`을 `maplibre` 청크로, 나머지를 `vendor` 청크로 분리.

### 엔트리·소스 구성

- `frontend/index.html` — 루트 `#root`, `/src/main.jsx` 모듈 로드, `frontend/public/favicon.svg`.
- `frontend/src/main.jsx`(15줄) → `App.jsx`(684줄) 마운트.
- API 접근은 `frontend/src/api.js`(16줄)의 `apiGet()` 단일 헬퍼로 통일. 베이스 URL은 `import.meta.env.VITE_API_URL || 'http://localhost:8000'`, 모든 요청에 `__BUILD_ID__` 기반 `?v=` 캐시버스터를 부착.

`frontend/src/` 전체 27개 파일, 합계 6038줄. 파일별 줄 수(오름차순):

| 파일 | 줄 수 |
|---|---|
| `constants.js` | 3 |
| `dates.js` | 12 |
| `main.jsx` | 15 |
| `api.js` | 16 |
| `Spinner.jsx` | 16 |
| `VerseLangTabs.jsx` | 28 |
| `theme.js` | 43 |
| `urlState.js` | 46 |
| `useNodeSelection.js` | 52 |
| `TourList.jsx` | 76 |
| `mapRingController.js` | 163 |
| `RelationsView.jsx` | 194 |
| `FamilyTree.jsx` | 207 |
| `mapGeo.js` | 215 |
| `WordDistributionView.jsx` | 217 |
| `MapView.jsx` | 242 |
| `index.css` | 249 |
| `PersonIntro.jsx` | 251 |
| `JourneyList.jsx` | 282 |
| `useStageNavigation.js` | 299 |
| `TimelineView.jsx` | 306 |
| `BibleOverviewView.jsx` | 312 |
| `PersonHub.jsx` | 387 |
| `RelianceView.jsx` | 449 |
| `mapLayers.js` | 451 |
| `App.jsx` | 684 |
| `SidePanel.jsx` | 823 |

`theme.js`(43줄)는 듀얼 테마(다크 기본 + `data-theme='light'` 라이트, ADR-0020) 값 참조. `FamilyTree.jsx`는 라이브러리 없는 SVG 가계도. `WordDistributionView.jsx`는 감정 3영역 워드클라우드 + 구절 시트. `RelianceView.jsx`(신규, 449줄)는 하나님 의존도 탭 UI.

### 모션 시스템 (`frontend/src/index.css`)

`index.css`에 CSS 커스텀 프로퍼티로 정의된 모션 토큰과, 그 토큰만 참조하는 재사용 애니메이션 클래스 집합:

- **토큰**: `--dur-fast: 150ms`(마이크로 피드백·칩·탭), `--dur-base: 250ms`(모달·시트·스테이지 전환), `--dur-slow: 400ms`(입장 스태거·게이지류), `--ease-out`, `--ease-in-out`, `--ease-drawer`(시트/드로어), `--ease-pop`(오버슛 팝, 워드클라우드). `:root`에 선언, 새 duration/easing 하드코딩 대신 이 토큰만 참조하는 것이 규약.
- **reduced-motion 가드**: `@media (prefers-reduced-motion: reduce)`에서 세 duration 토큰을 `1ms`로 붕괴시키고 `animation-delay`를 `0ms !important`로 무효화. `Spinner.jsx`의 0.7s 하드코딩 회전은 로딩 상태 표시라 예외 처리(가드 미적용).
- **애니메이션 클래스**: `.cloud-in`/`@keyframes cloud-in`(단어 분포 클라우드 컨테이너 페이드인), `.word-in`/`@keyframes word-in`(클라우드 단어별 스태거, `--w-op` 인라인 var로 빈도 농도 반영), `.stage-in`(최상위 화면 전환 브리지), `.overlay-in`(포털 레이어 오버레이 페이드), `.modal-in`(모달 카드 스케일 입장), `.card-in`(허브·투어·책 카드 스태거), `.bar-reveal`(막대 성장, `transform: scaleX`만), `.stop-bar-in`(여정 정차지 좌측 바), `.pressable`/`:active`(카드·버튼 공용 누름 피드백, `transform: scale(0.97)`).
- 모두 `transform`·`opacity`만 애니메이트(레이아웃 트리거 속성 회피). 사용처는 `frontend/src/App.jsx`, `BibleOverviewView.jsx`, `FamilyTree.jsx`, `JourneyList.jsx`, `PersonHub.jsx`, `PersonIntro.jsx`, `RelianceView.jsx`, `SidePanel.jsx`, `TourList.jsx`, `WordDistributionView.jsx` 등 10개 이상 컴포넌트.
- 라이트 테마(`:root[data-theme='light']`)는 같은 토큰 계약에 값만 다른 벌 — 양피지(`--paper*`)와 지도·지도 오버레이 색은 테마 불변이라 라이트 블록 밖.

### 프론트엔드 환경변수

- `frontend/.env.production` — `VITE_API_URL=/api`(빌드타임 주입, nginx 프록시 경로). 개발 시엔 폴백 `http://localhost:8000` 사용.

## 빌드·구성·배포 파일

- `docker-compose.yml` — `neo4j`(image `neo4j:5`)·`api`(build `./backend`)·`nginx`(image `nginx:alpine`) 3서비스. INTEGRATIONS에 상세.
- `backend/Dockerfile` — `python:3.12-slim`, `requirements.txt` 설치 후 `app/`만 복사(스크립트·데이터 미포함), uvicorn 기동.
- `nginx/nginx.conf` — 정적 자산 서빙 + `/api/` 리버스 프록시.
- `deploy.sh` — 프론트 빌드 → API 이미지 빌드 → 컨테이너 재기동 → 한글 이름 주입의 4단계 배포 스크립트(macOS 로컬 호스트 대상, lock 파일·로그 포함). `load_*`·`inject_*`(ko_names 제외)는 실행하지 않는다.
- `.github/workflows/deploy.yml` — `main` push 시 self-hosted 러너에서 `deploy.sh` 실행.
- `.env` / `.env.example` — 루트 레벨, 키는 `NEO4J_PASSWORD`뿐(compose가 `NEO4J_AUTH`를 `neo4j/<password>`로 파생).

## 실행 방법 요약 (`README.md`)

개발: `docker compose up -d`(Neo4j) → `load_theographic.py`·`inject_ko_names.py`·`inject_date_corrections.py`로 데이터 적재 → `python3 -m uvicorn backend.app.main:app --reload`(:8000) → `cd frontend && npm run dev`(:5173). 로컬 통합 검증은 `frontend/dist`를 nginx가 마운트하므로 `npm run build` 후 `docker compose up -d --build api`로 확인(:8080).
