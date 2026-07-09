---
last_mapped_commit: 232fba9c2c3724daf4ee250eba876f1e46f4b6d9
mapped: 2026-07-09
---
# Codebase Structure

**Analysis Date:** 2026-07-09

## Directory Layout

```
BibleMap/
├── docker-compose.yml      # 3서비스 스택(neo4j·api·nginx) 정의
├── deploy.sh               # 배포 스크립트(프론트 빌드→api 빌드→재시작→ko 이름 주입)
├── BIBLEMAP_PLAN.md        # 프로젝트 계획 문서
├── README.md
├── CLAUDE.md               # 프로젝트 작업 가이드라인
├── backend/
│   ├── Dockerfile          # python:3.12-slim + uvicorn
│   ├── requirements.txt    # fastapi·neo4j·uvicorn
│   ├── app/
│   │   ├── main.py         # FastAPI 앱·lifespan(인덱스)·라우터 등록
│   │   ├── db.py           # Neo4j 싱글턴 드라이버(get_driver)
│   │   ├── overlays.py     # data/*.json 경로 해석·로드·lru_cache
│   │   └── routes/         # 엔드포인트별 APIRouter
│   │       ├── nodes.py    # /node·/person/{id}/event-ids·/node/{id}/places·neighbors
│   │       ├── persons.py  # /persons/curated·/person/{id}/connections·/relations
│   │       ├── journey.py  # /person/{id}/journey
│   │       ├── events.py   # /events·/event/{id}/verses
│   │       ├── tours.py    # /tours·/tour/{id}
│   │       ├── places.py   # /place/{id}/curated-persons
│   │       ├── books.py    # /books-overview
│   │       └── search.py   # /search
│   └── scripts/            # 오프라인 데이터 파이프라인(load_*·generate_*·inject_*)
├── frontend/
│   ├── index.html          # SPA 진입 HTML
│   ├── vite.config.js      # Vite + manualChunks(maplibre/vendor 분리)
│   ├── eslint.config.js
│   ├── .env.production      # VITE_API_URL=/api (빌드타임 주입)
│   ├── package.json        # react 19·maplibre-gl·lucide-react
│   ├── dist/               # 빌드 산출물(nginx가 마운트, git 무시)
│   ├── public/             # favicon.svg
│   └── src/                # 컴포넌트·훅·맵헬퍼·유틸
├── nginx/
│   └── nginx.conf          # SPA 서빙 + /api/ 프록시 + 캐시 정책
├── data/                   # JSON 오버레이(그래프 위 큐레이션 레이어)
└── .github/workflows/
    └── deploy.yml          # main push → self-hosted 러너 → deploy.sh
```

## Directory Purposes

**`backend/app/routes/`:**
- Purpose: 엔드포인트별 `APIRouter` 모듈. 각 파일이 하나의 관심사(노드/인물/여정/사건/투어/장소/책/검색)를 담당.
- Contains: 라우터 인스턴스, 엔드포인트 함수, `functools.lru_cache`로 감싼 빌드/조회 함수.
- Key files: `nodes.py`(가장 큼, 노드 상세 허브), `persons.py`(era/이름 매핑 단일 출처 + 관계 뷰 데이터).

**`backend/scripts/`:**
- Purpose: API 런타임과 분리된 오프라인 데이터 파이프라인. 그래프 적재·오버레이 생성·그래프 속성 주입.
- Contains: `load_*.py`(theographic 원본 → Neo4j), `generate_*.py`(오버레이 JSON 생성), `inject_*.py`(ko 이름·traits·컨텍스트를 그래프 노드에 주입).
- Key files: `load_theographic.py`(원본 그래프 적재), `inject_ko_names.py`(배포 시 자동 실행), `generate_person_event_verses.py`·`generate_verse_text.py`(근거 구절 프리베이크).

**`frontend/src/`:**
- Purpose: React SPA 소스. Stage별 화면·지도·타임라인·관계 뷰·상세 패널.
- Contains: `*.jsx` 뷰 컴포넌트, `use*.js` 훅, `map*.js` MapLibre 헬퍼, `*.js` 유틸(api·urlState·dates·theme·constants).
- Key files: `App.jsx`(렌더 트리·Stage 분기), `useStageNavigation.js`(내비 상태머신), `MapView.jsx`·`RelationsView.jsx`·`TimelineView.jsx`·`SidePanel.jsx`(뷰).

**`data/`:**
- Purpose: 그래프 위에 얹는 큐레이션 오버레이 JSON. 백엔드가 `overlays.py`/직접 로드로 병합.
- Contains: 하위 디렉터리별 오버레이 타입(아래 표 참조).
- git 추적됨. 컨테이너에는 `docker-compose.yml`이 `./data:/app/data`로 마운트.

## `data/` 오버레이 디렉터리 상세

| 디렉터리 | 파일 | 내용 | 읽는 곳 |
|----------|------|------|---------|
| `person_events/` | `<slug>.json` (35개) | 인물별 시간순 사건(id·title·nameKo·startDate·sortKey·occursAt·participants·books) | `journey.py`·`persons.py`·`places.py`·`tours.py` |
| `person_relations/` | `relations.json` + `AUTHORING.md` | 인물 쌍 관계 카탈로그(type·endpoints·phases) — 관계 뷰 소스 | `persons.py:_load_relations` |
| `event_verses/` | `events.json` | 사건별 근거 구절(권별 그룹) | `events.py:get_event_verses` |
| `book_events/` | `books.json` | {bookId:[eventId]} 추정책 오버레이 | `overlays.book_events_raw` |
| `tours/` | `<id>.json` (9개) | 테마 투어(id·title·era·stops:[eventId]) — event-reference 오버레이 | `tours.py` |
| `place_coords/` | `places.json` (84 entries) | 장소 좌표 보강 데이터 | `enrich_place_coords.py`(주입 스크립트) |
| `character_traits/` | `people.json` | {theographic_id: traits} — 그래프 주입용 | `inject_person_traits.py` |
| `authored_persons/` | `people.json` | 저작 인물(저작 노드 연결) | `load_authored_persons.py` |
| `authored_events/`·`verse_events/`·`book_context/`·`place_context/`·`names_ko/`·`book_years_approx/` | 각 1개 이상 | 각각 저작 사건·구절-사건·책/장소 컨텍스트·한글 이름·추정 연대 오버레이(대부분 스크립트가 소비) | `backend/scripts/*` |

## Key File Locations

**Entry Points:**
- `backend/app/main.py`: FastAPI 앱 진입(uvicorn `app.main:app`)
- `frontend/src/main.jsx`: React 마운트 → `App.jsx`
- `frontend/index.html`: SPA 셸

**Configuration:**
- `docker-compose.yml`: 서비스·볼륨·환경변수(`NEO4J_PASSWORD` 필수)
- `nginx/nginx.conf`: `/api/` 프록시 + SPA try_files + 캐시 헤더
- `frontend/vite.config.js`: 빌드·청크 분리
- `frontend/.env.production`: `VITE_API_URL=/api`
- `backend/Dockerfile`·`backend/requirements.txt`: API 이미지
- `.env`(git 무시): `NEO4J_PASSWORD` 등 시크릿. 실제 값은 커밋 금지.

**Core Logic:**
- `backend/app/db.py`: Neo4j 접근 단일 출처
- `backend/app/overlays.py`: 오버레이 로드 단일 출처
- `backend/app/routes/persons.py`: era/이름/slug 매핑 단일 출처(타 라우터가 import)
- `frontend/src/useStageNavigation.js`: 내비 상태머신
- `frontend/src/api.js`: 프론트 fetch 단일 출처

**Map(지도):**
- `frontend/src/MapView.jsx`: MapLibre 지도 컨테이너·수명주기
- `frontend/src/mapGeo.js`: GeoJSON 빌더(여정 라인/정차지)
- `frontend/src/mapLayers.js`: 소스/레이어 셋업·이벤트 핸들러
- `frontend/src/mapRingController.js`: 장소 사건 링 펼침 제어

## Naming Conventions

**Files:**
- 백엔드 라우터: 도메인 복수형 소문자 — `persons.py`, `events.py`, `places.py`
- 백엔드 스크립트: 동사 접두 — `load_*.py`(적재), `generate_*.py`(생성), `inject_*.py`(주입)
- 프론트 컴포넌트: PascalCase `.jsx` — `MapView.jsx`, `RelationsView.jsx`, `SidePanel.jsx`
- 프론트 훅: `use` 접두 camelCase — `useStageNavigation.js`, `useNodeSelection.js`
- 프론트 유틸: camelCase `.js` — `urlState.js`, `mapGeo.js`, `api.js`

**Directories:**
- 오버레이: `<도메인>_<타입>` snake_case — `person_events`, `person_relations`, `event_verses`, `place_coords`
- 내부 헬퍼 함수: `_` 접두(모듈 프라이빗) — `_build_list`, `_resolve`, `_fetch_place_coords`

## Where to Add New Code

**새 API 엔드포인트:**
- 기존 도메인이면 해당 `backend/app/routes/<domain>.py`에 함수 추가.
- 새 도메인이면 `backend/app/routes/<domain>.py` 생성 → `router = APIRouter()` → `main.py`의 `include_router` 목록에 등록(`backend/app/main.py:5`·`32`).
- era/이름/slug가 필요하면 `persons.py`에서 import(재정의 금지, 드리프트 방지).

**새 오버레이 데이터 타입:**
- 데이터: `data/<domain>_<type>/*.json` 신규 디렉터리.
- 캐시 로더: 정형 파일은 `backend/app/overlays.py`에 `@functools.lru_cache` 함수 추가, 라우터별 특수 로드는 해당 라우터에서 `_resolve(...)` 직접 사용.
- 생성 스크립트가 있으면 `backend/scripts/generate_<...>.py`.

**새 프론트 뷰/컴포넌트:**
- 컴포넌트: `frontend/src/<Name>.jsx`(PascalCase).
- Stage 하위 뷰면 `App.jsx` 렌더 트리·`useStageNavigation.js` 상태·`urlState.js` 해시 인코딩/파싱 세 곳을 함께 갱신(관계 뷰가 이 패턴의 최근 사례 — `exploreView === 'relations'`).
- 데이터 fetch는 반드시 `frontend/src/api.js`의 `apiGet` 사용(직접 `fetch` 금지).

**공유 헬퍼:**
- 지도 관련: `frontend/src/mapGeo.js`(GeoJSON)·`mapLayers.js`(레이어)·`mapRingController.js`(링).
- 상수: `frontend/src/constants.js`(브레이크포인트·시트 높이). 날짜: `dates.js`. 테마: `theme.js`.

## Special Directories

**`frontend/dist/`:**
- Purpose: Vite 빌드 산출물. nginx가 `docker-compose.yml`에서 `:ro` 마운트.
- Generated: 예(`npm run build`)
- Committed: 아니오(git 무시). 로컬 검증 전 `cd frontend && npm run build` 필요(HMR 아님 — dist 마운트).

**`backend/app/__pycache__/`·`routes/__pycache__/`:**
- Purpose: 파이썬 바이트코드 캐시.
- Generated: 예 / Committed: 아니오

**`.forge/`:**
- Purpose: forge 유틸 산출물(이 코드베이스 맵 포함).
- Committed: 예(코드베이스 맵). `.forge/reports/`·`.forge/scratch/`는 작업 산출물.

**`.claude/worktrees/`:**
- Purpose: Dynamic Workflow 에이전트 워크트리(`bgIsolation: "none"` 설정 관련).
- Committed: 아니오

---

*Structure analysis: 2026-07-09*
