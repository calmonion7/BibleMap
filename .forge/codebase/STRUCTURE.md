---
last_mapped_commit: 95ba754e0a5b8a8db6f537f88d6d4e60d302d066
mapped: 2026-07-06
---

# STRUCTURE

## 프로젝트 루트

```
BibleMap/
├── docker-compose.yml        # neo4j + api + nginx 서비스 정의
├── deploy.sh                 # self-hosted 러너용 배포 스크립트
├── CLAUDE.md                 # AI 에이전트 행동 지침
├── BIBLEMAP_PLAN.md          # 초기 기획 문서
├── backend/                  # FastAPI 서비스
├── frontend/                 # Vite/React 앱
├── data/                     # JSON 오버레이 + 투어 정의
└── nginx/
    └── nginx.conf
```

## 백엔드 (`backend/`)

```
backend/
├── Dockerfile
├── requirements.txt
├── app/
│   ├── main.py               # FastAPI 앱, lifespan, 라우터 등록
│   ├── db.py                 # Neo4j 드라이버 싱글턴
│   ├── overlays.py           # JSON 파일 _resolve + lru_cache 로더
│   └── routes/
│       ├── nodes.py          # GET /node/{id}, /node/{id}/places, /node/{id}/neighbors/grouped, /person/{id}/event-ids
│       ├── events.py         # GET /events, /event/{id}/verses
│       ├── search.py         # GET /search
│       ├── books.py          # GET /books-overview
│       ├── persons.py        # GET /persons/curated, /person/{id}/connections — _ERA·_NAME_KO 단일 출처
│       ├── journey.py        # GET /person/{id}/journey — _fetch_place_coords 정의
│       ├── places.py         # GET /place/{id}/curated-persons
│       └── tours.py          # GET /tours, /tour/{id} — _build_event_index, _fetch_place_coords 재사용
└── scripts/
    ├── load_theographic.py
    ├── load_books.py
    ├── load_person_events.py
    ├── load_authored_events.py
    ├── load_authored_persons.py
    ├── load_verse_events.py
    ├── generate_book_events.py
    ├── generate_approx_book_verses.py
    ├── generate_event_verses.py
    ├── generate_person_event_verses.py
    ├── generate_book_context.py
    ├── generate_book_context_enrich.py
    ├── generate_verse_text.py
    ├── generate_verse_events.py
    ├── generate_person_traits.py
    ├── inject_ko_names.py
    ├── inject_book_context.py
    ├── inject_place_context.py
    ├── inject_person_traits.py
    └── enrich_place_coords.py
```

## 프론트엔드 (`frontend/src/`)

### 진입점 및 앱 셸

| 파일 | 역할 |
|---|---|
| `main.jsx` | React 마운트 진입점 |
| `App.jsx` | 스테이지 조건 렌더링, journeyStops fetch, 모바일 분기, SidePanel 배치 |

### 상태 훅

| 파일 | 역할 |
|---|---|
| `useStageNavigation.js` | 스테이지 상태 머신(`hub\|explore\|overview\|tours`), URL 해시 딥링크(ADR-0009), 브라우저 뒤로가기 통합(ADR-0010), `explorePersonId`/`exploreTourId` 상호배타 관리 |
| `useNodeSelection.js` | `selectedNode`, history 스택, `personEventIds`, `selectNode`/`selectNodeFresh`/`goBack`/`closePanel`/`handleNodeLoaded` |

### 뷰 컴포넌트

| 파일 | 역할 |
|---|---|
| `PersonHub.jsx` | 허브 스테이지 — 큐레이션 인물 카드(era 그룹), 개요·투어 진입 버튼 |
| `TourList.jsx` | 투어 목록 스테이지 — `GET /tours` 카드 그리드, 카드 클릭 → `onSelectTour(id)` |
| `MapView.jsx` | MapLibre GL 지도 마운트, 여정 경로·마커 렌더, 노드 선택 이벤트 위임 |
| `JourneyList.jsx` | 여정 stops 시간순 아코디언 리스트 — 인물·투어 공용, 데스크톱 인라인/모바일 읽기 모드 분기 |
| `TimelineView.jsx` | 전체 사건 타임라인 — `personFilter`/`bookFilter`로 여정·책 필터링, 구절 인라인 드릴다운 |
| `BibleOverviewView.jsx` | 성경 책 목록 개요 — `GET /books-overview`, 구약/신약 장르별 그룹 |
| `SidePanel.jsx` | 노드 상세 패널 — Place/Person/Event/Book별 섹션, 큐레이션 CTA, 장소-인물 칩, 구절 드릴다운 |
| `EventVerses.jsx` | 사건 근거구절 표시 — `GET /event/{id}/verses`, 데스크톱 인라인/모바일 읽기 모드 |
| `VerseLangTabs.jsx` | 한/영 본문 탭 전환 UI |
| `Spinner.jsx` | 로딩 스피너 |

### 지도 유틸

| 파일 | 역할 |
|---|---|
| `mapGeo.js` | `coreBounds`, `placesToGeoJSON`, `buildJourneyLineGeoJSON`, `buildJourneyStopsGeoJSON`, `journeyStopGroups`, `ringLabels` |
| `mapLayers.js` | `setupMapSources`, `registerEventHandlers`, `EMPTY_GEOJSON` |
| `mapRingController.js` | 사건 링 fly-out 컨트롤러 생성·파괴 |

### 공유 유틸/상수

| 파일 | 역할 |
|---|---|
| `api.js` | `apiGet(path, {signal})` — 모든 fetch의 단일 진입점, `VITE_API_URL` 기반 |
| `urlState.js` | `encodeHash`, `parseHash` — 해시 ↔ 내비 상태 문자열 변환(ADR-0009) |
| `constants.js` | `MOBILE_BREAKPOINT=768`, `SHEET_VH=75`, `JOURNEY_SHEET_VH=42` |
| `theme.js` | `TYPE_COLOR`, `TYPE_KO`, `TYPE_ORDER`, `SELECT_HL` — 노드 타입 팔레트 단일 출처 |
| `dates.js` | `parseYear` — startDate 문자열 파싱 유틸 |

## 데이터 디렉터리 (`data/`)

```
data/
├── person_events/            # 큐레이션 인물별 여정 사건 배열 (<slug>.json × 34명)
│   ├── jesus.json
│   ├── paul.json
│   ├── moses.json
│   └── … (abraham, david, solomon 등 총 34개)
├── tours/                    # 테마 투어 정의 — eventId 참조 목록
│   └── david-united-kingdom.json
├── book_events/
│   └── books.json            # {bookId: [eventId, ...]} — 책-사건 근사 연결
├── event_verses/
│   └── events.json           # 사건별 근거 구절(프리베이크 본문 포함, ADR-0003)
├── authored_events/
│   └── events.json
├── authored_persons/
│   └── people.json
├── book_context/
│   └── books.json
├── book_years_approx/
│   └── books.json
├── character_traits/
│   └── people.json
├── names_ko/                 # 노드별 한글 이름 오버레이
│   ├── books.json
│   ├── events.json
│   ├── groups.json
│   ├── people.json
│   └── places.json
├── place_context/
│   └── places.json
├── place_coords/
│   └── places.json
└── verse_events/
    └── events.json
```

### `data/tours/<slug>.json` 형식

```json
{
  "id": "david-united-kingdom",
  "title": "다윗과 통일왕국",
  "subtitle": "...",
  "era": "왕국",
  "description": "...",
  "stops": ["authored-saul-mizpah-chosen", "authored-david-goliath-gath", ...]
}
```

`stops` 배열의 각 항목은 `data/person_events/<slug>.json` 내 이벤트의 `id`값(eventId)이다. `tours.py`의 `_build_event_index()`가 전 큐레이션 인물의 파일을 스캔해 이 id로 이벤트 본체를 해결한다.

## 네이밍 컨벤션

- **백엔드 라우터**: `routes/<resource>.py`, 함수명 `get_<resource>` / `list_<resource>`
- **캐시 헬퍼**: `_build_*` / `_load_*` / `_compute_*` + `@functools.lru_cache`
- **프론트엔드 컴포넌트**: PascalCase `.jsx`
- **프론트엔드 훅**: `use<Name>.js`, `camelCase` 함수명
- **프론트엔드 유틸**: `camelCase.js`
- **person_events 슬러그**: 영문 소문자, 언더스코어 구분 (`john_the_baptist`)
- **tour 슬러그**: 영문 소문자, 하이픈 구분 (`david-united-kingdom`)
- **theographic_id**: 외부 Theographic 데이터셋의 식별자, Neo4j 노드의 키 속성

## 인프라 파일

| 파일 | 역할 |
|---|---|
| `docker-compose.yml` | neo4j + api + nginx 서비스, `neo4j_data` 볼륨 |
| `nginx/nginx.conf` | `/api` → `api:8000` 프록시, 정적 파일 서빙 |
| `backend/Dockerfile` | FastAPI 이미지 빌드 |
| `frontend/vite.config.js` | Vite 빌드 설정 |
| `deploy.sh` | self-hosted 러너 배포 진입점 |
