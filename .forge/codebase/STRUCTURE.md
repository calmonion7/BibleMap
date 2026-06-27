---
last_mapped_commit: 3837b4f9339ed2efb82a6b72cc1124a3340e2b9c
mapped: 2026-06-27
---

# STRUCTURE

레포 루트는 프론트(`frontend/`)·백엔드(`backend/`)·데이터(`data/`)·인프라
(`nginx/`, `docker-compose.yml`, `deploy.sh`)·forge 메타(`.forge/`)로 나뉜다.

## 최상위 레이아웃

```
BibleMap/
├── frontend/            React 19 + Vite SPA
├── backend/             FastAPI 앱 + 데이터 적재/생성 스크립트
├── data/                Neo4j 외 보조 JSON 오버레이(도메인별 디렉터리)
├── nginx/nginx.conf     정적 서빙 + /api 프록시
├── docker-compose.yml   neo4j + api + nginx 3 서비스
├── deploy.sh            빌드→재시작→한글이름 주입 배포 스크립트
├── .github/workflows/deploy.yml   self-hosted 러너 CI
├── .forge/              forge 루프 상태·코드베이스 맵·ADR·회고
├── CLAUDE.md            행동 가이드 + 프로젝트 컨텍스트
├── BIBLEMAP_PLAN.md     프로젝트 계획 문서
└── README.md
```

## frontend/

```
frontend/
├── index.html               Vite 진입 HTML
├── vite.config.js           maplibre/vendor manualChunks 분할
├── eslint.config.js         react-hooks 등 플랫 config
├── .env.production          VITE_API_URL=/api (빌드타임 주입)
├── public/favicon.svg
├── dist/                    빌드 산출물 — nginx가 직접 서빙(HMR 아님, git ignore)
└── src/
    ├── main.jsx             createRoot + StrictMode 진입점
    ├── App.jsx              루트 — activeStage(hub|explore|overview) 2단계 IA
    ├── index.css
    ├── api.js               apiGet(path,{signal}) 단일 클라이언트
    ├── theme.js             TYPE_COLOR/TYPE_KO/SELECT_HL 공유 팔레트
    ├── constants.js         MOBILE_BREAKPOINT(768), SHEET_VH(55)
    ├── useNodeSelection.js  노드 선택/히스토리/personEventIds 훅
    ├── PersonHub.jsx        허브 — 큐레이션 13인 시대별 카드
    ├── JourneyList.jsx      탐험 여정 사건 리스트(지도와 양방향 동기)
    ├── MapView.jsx          지도 셸 — maplibre 인스턴스·fetch·카메라·여정 effect
    ├── mapGeo.js            순수 지오메트리 계산(여정선/스톱/링/프레이밍)
    ├── mapLayers.js         maplibre source/layer 정의 + 이벤트 핸들러
    ├── mapRingController.js 사건 링·스파이더 애니메이션 컨트롤러(팩토리)
    ├── TimelineView.jsx     타임라인 + 근거구절 드릴다운
    ├── BibleOverviewView.jsx 성경 개요(장르별 책 카드)
    ├── SidePanel.jsx        노드 상세 패널(Person/Place/Book/이웃 그룹)
    ├── VerseLangTabs.jsx    한국어|영어 절 본문 토글 세그먼트
    └── Spinner.jsx          로딩 스피너
```

핵심 위치:
- 화면 분기·전역 상태 합류 지점: `App.jsx`.
- 지도 관련 4파일은 `MapView.jsx`(셸) / `mapGeo.js`(계산) / `mapLayers.js`(레이어) /
  `mapRingController.js`(애니메이션)로 관심사 분리.
- 제거됨(부재 확인): `useSearch.js`(범용 검색 훅), `convexHull.js`(활동범위 면 계산).

## backend/

```
backend/
├── Dockerfile               python:3.12-slim + uvicorn
├── requirements.txt         fastapi / neo4j / uvicorn
├── __init__.py
├── app/
│   ├── __init__.py
│   ├── main.py              FastAPI 앱·lifespan(인덱스 생성)·라우터 등록
│   ├── db.py                get_driver() Neo4j 드라이버 싱글턴
│   ├── overlays.py          _resolve/_load + book_events/event_verses 캐시
│   └── routes/
│       ├── __init__.py
│       ├── nodes.py         /node/* (상세·places·grouped), /person/{id}/event-ids
│       ├── events.py        /events, /event/{id}/verses
│       ├── search.py        /search (프론트 UI 제거됐으나 라우트 잔존)
│       ├── books.py         /books-overview
│       ├── persons.py       /persons/curated (큐레이션 13인, 파일 기반)
│       ├── journey.py       /person/{id}/journey (시간순 여정 정차지)
│       └── places.py        /place/{id}/curated-persons (그 장소 지난 13인)
└── scripts/                 데이터 적재·생성·주입 CLI (런타임 앱 비의존)
    ├── load_*.py            data/*.json → Neo4j 적재 (load_books/theographic/
    │                        person_events/authored_events/verse_events)
    ├── generate_*.py        외부/LLM 생성 단계 (generate_book_events/event_verses/
    │                        verse_text/verse_events/book_context[_enrich]/
    │                        person_traits/person_event_verses/approx_book_verses)
    ├── inject_*.py          생성 데이터 → Neo4j 주입 (inject_ko_names/book_context/
    │                        place_context/person_traits)
    └── enrich_place_coords.py  장소 좌표 보강
```

핵심 위치:
- 라우트 추가 시 `routes/<name>.py`에 `router = APIRouter()` 후 `main.py`에서
  `app.include_router` 등록.
- 런타임 파일 읽기는 항상 `overlays._resolve` 또는 직접 `_resolve` 임포트를 거쳐
  `DATA_DIR`(컨테이너) → 레포 `data/` 폴백.
- `scripts/`는 배포/적재 도구로, 실행 중 FastAPI 앱과 분리(앱은 `app/`만 의존).
  단 `deploy.sh`가 배포 4단계에서 `inject_ko_names.py`를 호출.

## data/ (도메인별 JSON 오버레이)

```
data/
├── names_ko/            한글 이름(books/events/groups/people/places.json)
├── person_events/       큐레이션 13인 슬러그별 사건 배열(abraham.json … jesus.json)
├── event_verses/        사건별 근거구절(events.json)
├── verse_events/        구절→사건 매핑(events.json)
├── authored_events/     집필 사건(events.json)
├── book_events/         {bookId:[eventId]} (events.py 추정책 역매핑)
├── book_context/        성경권 시대배경·주제 등(books.json)
├── book_years_approx/   책별 추정 연도(books.json)
├── character_traits/    인물 성품(people.json)
├── place_context/       장소 배경·대표구절(places.json)
└── place_coords/        장소 좌표(places.json)
```

`person_events/`는 슬러그(`abraham`, `john_the_baptist` 등) 단위 파일이고,
`persons.py`/`journey.py`/`places.py`가 런타임에 직접 읽는다. 각 파일의
`events[0].participants[0]`가 그 인물의 `theographic_id`로 쓰인다.

## .forge/

```
.forge/
├── codebase/            이 맵 문서들(ARCHITECTURE/STRUCTURE/STACK/CONVENTIONS/
│                        CONCERNS/INTEGRATIONS/TESTING.md)
├── adr/                 결정 기록(retired/ 포함)
├── retro/               작업 회고
├── backlog/ done/ quick/  forge 루프 상태
├── config.json          forge 설정(eco 등)
└── reports/             (미커밋, git status untracked)
```

## 명명 규칙

- 프론트 컴포넌트는 PascalCase `.jsx`(`PersonHub.jsx`), 훅·유틸은 camelCase `.js`
  (`useNodeSelection.js`, `mapGeo.js`, `api.js`). 커스텀 훅은 `use` 접두.
- 백엔드 모듈·라우트는 snake_case `.py`. 라우트 파일명은 도메인 단수/복수를 그대로
  씀(`nodes.py`, `events.py`, `persons.py`, `journey.py`, `places.py`, `books.py`,
  `search.py`).
- 스크립트는 동사 접두로 단계 구분: `load_*`(Neo4j 적재) / `generate_*`(생성) /
  `inject_*`(주입) / `enrich_*`(보강).
- 데이터는 `data/<도메인_스네이크>/<엔티티>.json` (`names_ko/people.json`,
  `place_coords/places.json`). 인물 사건만 슬러그 단위 파일.
- 그래프 식별자는 `theographic_id`, 한글 이름 필드는 `nameKo`, 영문은 `name`/`title`,
  미번역 표시는 `nameKoMissing`(백엔드 산출 → 프론트 "(미번역)" 표기).
- 노드 라벨 5종: `Person`/`Place`/`Event`/`PeopleGroup`/`Book`(+ 프론트 `Unknown`).
- 시대 상수 순서 `_ERA_ORDER`(백엔드)·`ERA_ORDER`(프론트)는 동일 값을 각 파일에 중복
  선언(순환참조 회피).
