---
last_mapped_commit: 8af8f0563294387a7073d0b85e6f7de74b4b7b30
mapped: 2026-07-13
---

# STRUCTURE

리포지토리 디렉터리 레이아웃, 핵심 파일 위치, 데이터/스크립트 명명 규칙을 다룬다.

## 최상위 레이아웃

```
BibleMap/
├── backend/                 # FastAPI 앱 + 데이터 적재 스크립트
├── frontend/                # React(Vite) SPA
├── data/                    # 원천/저작/오버레이 JSON (여러 서브디렉터리)
├── nginx/                   # nginx 리버스 프록시 설정
├── docker-compose.yml       # neo4j + api + nginx 스택
├── deploy.sh                # 빌드→이미지→up→ko-name 주입 배포 스크립트
├── .env / .env.example      # NEO4J_PASSWORD (compose가 NEO4J_AUTH로 파생)
├── .github/workflows/deploy.yml  # self-hosted 러너 CI 배포
├── README.md                # 로컬 실행 순서
├── CLAUDE.md                # 프로젝트 작업 지침
└── BIBLEMAP_PLAN.md         # 초기 기획 문서
```

## backend/

```
backend/
├── Dockerfile               # python:3.12-slim, uvicorn app.main:app :8000
├── requirements.txt         # fastapi / neo4j / uvicorn
├── __init__.py
├── app/                     # 런타임 애플리케이션
│   ├── __init__.py
│   ├── main.py              # FastAPI 엔트리 (lifespan 인덱스, CORS, 9개 라우터 include)
│   ├── db.py                # get_driver() Neo4j 드라이버 싱글턴
│   ├── overlays.py          # 런타임 오버레이 로더 (_resolve/_resolve_dir/_load + 캐시 로더 3종)
│   └── routes/              # API 라우터 (라벨/엔티티별)
│       ├── __init__.py
│       ├── nodes.py         # /node/{id}, /neighbors/grouped, /places, /person/{id}/event-ids
│       ├── events.py        # /events, /event/{id}/verses
│       ├── books.py         # /books-overview
│       ├── persons.py       # /persons/curated, /keypeople-cards, /connections, /relations
│       ├── journey.py       # /person/{id}/journey
│       ├── places.py        # /place/{id}/curated-persons
│       ├── search.py        # /search
│       ├── tours.py         # /tours, /tour/{id}
│       └── family.py        # /person/{id}/family (인물 중심 가계도 서브그래프, ADR-0019)
└── scripts/                 # 빌드타임 배치 (API 밖에서 실행)
    ├── __init__.py
    ├── load_*.py            # Neo4j에 노드/관계 MERGE 적재
    ├── inject_*.py          # 기존 노드에 속성 SET
    ├── generate_*.py        # data/ JSON 생성 (일부 Claude API 사용)
    ├── validate_*.py        # 데이터 규칙 기계 검증
    ├── apply_event_dedupe.py# 중복 이벤트 실삭제 (ADR-0016)
    └── enrich_place_coords.py
```

핵심 파일 위치:

- 앱 진입/설정: `backend/app/main.py`, `backend/app/db.py`, `backend/app/overlays.py`.
- 라우터: `backend/app/routes/` 9개 모듈 (각각 자기 `APIRouter()` 인스턴스, `main.py`에서 include).
- 스크립트: `backend/scripts/` — 전량 `if __name__ == "__main__"` 진입점을 가지며 `NEO4J_URI`/`NEO4J_USER`/`NEO4J_PASSWORD` 환경변수를 읽는다(그래프에 접근하는 것 한정).

## frontend/

```
frontend/
├── index.html               # HTML 진입 (src/main.jsx 로드)
├── package.json             # react 19 / react-dom / maplibre-gl / lucide-react, vite 8
├── vite.config.js           # @vitejs/plugin-react + manualChunks(maplibre/vendor)
├── eslint.config.js
├── .env.production          # VITE_API_URL=/api (프로덕션 빌드 주입)
├── public/                  # favicon.svg 등 정적 자산
├── dist/                    # 빌드 산출물 (gitignore, nginx가 마운트해 서빙)
├── node_modules/            # (gitignore)
└── src/
    ├── main.jsx             # createRoot + StrictMode 진입
    ├── App.jsx              # 스테이지 상태 머신 + 레이아웃 셸 (6 스테이지 렌더 분기)
    ├── api.js               # apiGet() 단일 API 클라이언트
    ├── index.css            # CSS 변수/전역 스타일
    ├── theme.js             # TYPE_COLOR 등 색상 토큰
    ├── constants.js         # 모바일 브레이크포인트, 시트 높이
    ├── dates.js             # 연대 표기 유틸
    │
    ├── PersonHub.jsx        # 진입 허브 뷰 (hub 스테이지)
    ├── BibleOverviewView.jsx# 성경 책 개요 (overview 스테이지)
    ├── TourList.jsx         # 테마 투어 목록 (tours 스테이지)
    ├── MapView.jsx          # 지도 뷰 (maplibre-gl)
    ├── TimelineView.jsx     # 타임라인 뷰
    ├── RelationsView.jsx    # 관계 뷰 (인물 탐험 전용)
    ├── PersonIntro.jsx      # 인물 소개 뷰 (explore/intro)
    ├── FamilyTree.jsx       # 가계도 뷰 — 손수 SVG 커넥터 + 절대배치 세대 트리 (family 스테이지)
    ├── JourneyList.jsx      # 여정 정차 리스트
    ├── SidePanel.jsx        # 공유 상세 패널 (book 스테이지 페이지로도 재사용)
    ├── VerseLangTabs.jsx    # 절 본문 한/영 탭
    ├── Spinner.jsx
    │
    ├── mapLayers.js         # 지도 레이어 정의
    ├── mapGeo.js            # 지오메트리 유틸
    ├── mapRingController.js # 지도 링(경로) 제어
    │
    ├── useNodeSelection.js  # 노드 선택 훅
    ├── useStageNavigation.js# 스테이지/URL/히스토리 상태 머신 훅 (6 스테이지)
    └── urlState.js          # 해시 URL 직렬화/파싱 (encodeHash/parseHash)
```

## data/

원천·저작·오버레이 JSON을 엔티티/용도별 서브디렉터리로 분리한다.

```
data/
├── authored_events/events.json        # 저작 사건 노드 (authored=true)
├── authored_persons/
│   ├── people.json                    #   저작 인물 노드 [{id, name, nameKo}]
│   └── genealogy.json                 #   마태복음 1장 아브라함→예수 족보 사슬 (chain, ADR-0019)
├── person_events/<slug>.json          # 큐레이션 인물별 여정 사건 (인물당 파일 1개, 35개)
├── verse_events/events.json           # 구절 기반 사건 노드
│
├── bible/verses.json                  # 정본 절 사전 (verseID → {textKo, textEn}, 런타임 오버레이)
├── event_dedupe/dedupe.json           # 중복 이벤트 삭제 대상 테이블 (apply_event_dedupe.py, ADR-0016)
│
├── keypeople/identity.json            # (책,이름) → {kind, id?} 정식 식별 데이터셋 (ADR-0018)
├── keypeople_verses/people.json       # 무id 이름 키 카드 (ADR-0017)
├── person_context/                    # by-id 인물 카드 (본문 프리베이크, Person 속성 주입 + /keypeople-cards)
│   ├── people.json
│   └── AUTHORING.md
│
├── date_corrections/                  # 연대 교정 오버레이 (ADR-0014)
│   ├── events.json                    #   Event startDate/sortKey 교정 테이블
│   └── persons.json                   #   Person 필드 교정 테이블
│
├── names_ko/                          # 한글 이름 주입 소스
│   └── books.json  events.json  groups.json  people.json  places.json
│
├── book_context/books.json            # 권별 배경/주제/대표구절 (Book 속성 주입)
├── book_events/books.json             # {bookId:[eventId]} 추정책 연결 (런타임 오버레이)
├── book_years_approx/books.json       # 추정 연도 책 메타
├── event_verses/events.json           # 사건별 근거 구절 (런타임 오버레이)
├── place_context/places.json          # 장소 배경/대표구절 (Place 속성 주입)
├── place_coords/places.json           # 장소 좌표 (Place 속성 주입)
│
├── character_traits/                  # 인물 성품 (Person traits 속성 주입)
│   ├── people.json
│   └── AUTHORING.md                   #   저작/분류 규칙 (validate_traits.py가 검증)
│
├── person_relations/                  # 관계 오버레이 (런타임) — /relations + family role 라벨
│   ├── relations.json
│   └── AUTHORING.md
│
└── tours/                             # 테마 투어 (event-reference 오버레이, ADR-0011)
    ├── age-of-judges.json             # 투어당 파일 1개 (파일명 = tour id)
    ├── creation-to-flood.json
    ├── david-united-kingdom.json
    ├── elijah-and-elisha.json
    ├── exile-and-return.json
    ├── exodus-to-conquest.json
    ├── gospel-of-jesus.json
    ├── patriarchs-covenant.json
    └── the-early-church.json
```

## 명명 규칙

### 데이터 파일

- **컬렉션형 오버레이**: `<entity_or_topic>/<collection>.json` 꼴. 컬렉션 파일명은 담는 엔티티 복수형(`events.json`, `people.json`, `places.json`, `books.json`, `groups.json`, `relations.json`, `verses.json`, `identity.json`, `dedupe.json`, `genealogy.json`)이다. 예: `book_events/books.json`, `event_verses/events.json`, `bible/verses.json`, `keypeople/identity.json`.
- **엔티티별 분할 파일**: 인물 여정은 인물당 한 파일 `person_events/<slug>.json`(`david.json`, `moses.json` …). 투어는 투어당 한 파일 `tours/<tour-id>.json`, 파일명 자체가 tour id다(`tours.py`가 파일명을 id로 사용).
- **AUTHORING.md**: 손으로 저작하는 디렉터리(`character_traits/`, `person_context/`, `person_relations/`)에 저작·분류 규칙 문서를 동봉한다.
- **식별자**: 모든 노드의 조인 키는 `theographic_id`. 원본은 `recXXXX` 형태, 저작 노드는 `authored-*` 슬러그(예: `authored-mt1-perez`, `authored-place-bethlehem`, `authored-person-gideon`). 큐레이션 인물은 별도로 사람이 읽는 `slug`(`david`, `moses` …)를 가진다(`persons.py`의 slug↔id 맵, `person_events/<slug>.json` 파일명).
- **한/영 필드 접미사**: 한글 값은 `nameKo`/`textKo`/`verseTextKo`/`keyVerseTextKo`, 영문은 접미사 없는 `name`/`title` 또는 `...En`/`textEn`.

### 스크립트 (동사 접두 규칙, 모두 `backend/scripts/`)

- `load_*` — Neo4j에 노드/관계를 `MERGE`로 신규 적재. 예: `load_theographic.py`(GitHub 원본), `load_books.py`(Book + CONTAINS_BOOK), `load_authored_events.py`, `load_authored_persons.py`, `load_authored_genealogy.py`(족보 사슬 + 자체 검증), `load_person_events.py`, `load_verse_events.py`.
- `inject_*` — 이미 존재하는 노드에 속성만 `SET`. 예: `inject_ko_names.py`, `inject_date_corrections.py`, `inject_book_context.py`, `inject_place_context.py`, `inject_person_context.py`, `inject_person_traits.py`.
- `generate_*` — `data/` 아래 JSON을 생성(일부는 Claude API로 콘텐츠 생성, 일부는 theographic 원본 가공). 예: `generate_book_context.py`, `generate_book_context_enrich.py`, `generate_book_events.py`, `generate_bible_text.py`, `generate_event_verses.py`, `generate_person_context.py`, `generate_person_event_verses.py`, `generate_person_traits.py`, `generate_verse_events.py`, `generate_verse_text.py`, `generate_approx_book_verses.py`.
- `validate_*` — 데이터 규칙을 기계 검증. 예: `validate_event_chronology.py`, `validate_traits.py`, `validate_person_context.py`.
- `apply_*` — 파괴적 정리 배치. 예: `apply_event_dedupe.py`(`data/event_dedupe/dedupe.json` 기반 중복 이벤트 실삭제).
- `enrich_*` — 기존 데이터 보강. 예: `enrich_place_coords.py`.

### 프론트엔드

- 컴포넌트: PascalCase `.jsx`(`SidePanel.jsx`, `FamilyTree.jsx`, `PersonIntro.jsx`). 뷰 컴포넌트는 접미사 `View`(`MapView`, `TimelineView`, `RelationsView`, `BibleOverviewView`); `PersonHub`·`PersonIntro`·`FamilyTree`·`TourList`·`JourneyList`·`SidePanel`은 예외 없이 전체화면/패널 단위 컴포넌트다.
- 훅: `useXxx.js` 카멜케이스(`useNodeSelection.js`, `useStageNavigation.js`).
- 비컴포넌트 모듈: 카멜케이스 `.js`(`api.js`, `theme.js`, `mapLayers.js`, `urlState.js`).
- 스타일: 컴포넌트 인라인 스타일 + `index.css`의 CSS 변수(`var(--bg-1)`, `var(--gold)`, `var(--line-strong)` 등). 별도 CSS 모듈/스타일 라이브러리 없음.
