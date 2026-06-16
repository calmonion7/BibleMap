---
last_mapped_commit: e160d65cf9c7d0b54c8d9fc2d031639a712bfb86
mapped: 2026-06-16
---

# STRUCTURE

디렉터리 레이아웃과 주요 파일 위치, 명명 규약을 기술한다.

## 1. 루트 레이아웃

```
BibleMap/
├── docker-compose.yml      # 3개 서비스(neo4j, api, nginx) 정의
├── deploy.sh               # 빌드·재시작·한글주입 배포 스크립트
├── .env / .env.example     # NEO4J_PASSWORD
├── README.md
├── BIBLEMAP_PLAN.md        # 프로젝트 기획 문서
├── CLAUDE.md               # 작업 가이드라인
├── .github/workflows/deploy.yml   # main 푸시 → self-hosted 러너 → deploy.sh
├── nginx/nginx.conf        # 정적 서빙 + /api/ 프록시
├── backend/                # FastAPI + Neo4j (아래 2절)
├── frontend/               # React + Vite SPA (아래 3절)
└── data/                   # 정적 보강 JSON (아래 4절)
```

## 2. backend/

```
backend/
├── Dockerfile              # python:3.12-slim, uvicorn app.main:app
├── requirements.txt        # fastapi, neo4j, uvicorn
├── __init__.py
├── app/                    # FastAPI 애플리케이션 패키지
│   ├── __init__.py
│   ├── main.py             # 진입점: FastAPI app, CORS, lifespan 인덱스, 라우터 등록
│   ├── db.py               # get_driver() — 전역 단일 Neo4j 드라이버
│   └── routes/             # APIRouter 모듈(엔드포인트 그룹별 1파일)
│       ├── __init__.py
│       ├── nodes.py        # /node/{id}, /node/{id}/places, /node/{id}/neighbors/grouped
│       ├── events.py       # /events, /event/{id}/verses
│       ├── books.py        # /books
│       └── search.py       # /search
└── scripts/                # 일회성 데이터 적재·생성·주입 스크립트(앱과 분리)
    ├── __init__.py
    ├── load_theographic.py # theographic 원본 → Person/Place/Event/PeopleGroup + 관계 적재
    ├── load_books.py       # Book 노드 + CONTAINS_BOOK 관계 적재
    ├── inject_ko_names.py     # data/names_ko/ → 노드 nameKo/aliasesKo SET
    ├── inject_book_context.py # data/book_context/ → Book background/themes/keyVerse SET
    ├── inject_person_traits.py# data/character_traits/ → Person traits SET
    ├── generate_book_context.py  # Claude API → data/book_context/books.json
    ├── generate_person_traits.py # Claude API → data/character_traits/people.json
    └── generate_event_verses.py  # theographic 가공 → data/event_verses/events.json
```

- 앱 코드(`app/`)와 운영 스크립트(`scripts/`)는 분리. `scripts/`는 Dockerfile에 `COPY`되지 않으며 호스트에서 직접 실행(`deploy.sh`가 `python3 backend/scripts/...` 호출).
- 스크립트는 데이터 흐름 방향으로 `load_*`(원본→DB), `generate_*`(원본/LLM→`data/` JSON), `inject_*`(`data/` JSON→DB 속성) 접두사로 명명.

## 3. frontend/

```
frontend/
├── index.html              # 진입 HTML, src/main.jsx 로드
├── vite.config.js          # React 플러그인 + maplibre/vendor 청크 분리
├── package.json            # react 19, maplibre-gl, lucide-react
├── eslint.config.js
├── .env.production         # VITE_API_URL=/api
├── public/                 # 정적 자산(favicon.svg, icons.svg)
├── dist/                   # 빌드 산출물(nginx가 서빙) — git 추적
└── src/
    ├── main.jsx            # 진입점: createRoot(<App/>)
    ├── App.jsx             # 루트 컴포넌트: nav 바, 검색, 뷰 전환, 오버레이 패널
    ├── MapView.jsx         # MapLibre 지도 + 장소 마커 + 사건 링
    ├── SidePanel.jsx       # 노드 상세 패널(이웃/Book/Person 뷰)
    ├── TimelineView.jsx    # 연대순 사건·권 타임라인 + 사건→구절 드릴다운
    ├── api.js              # API_BASE + apiGet() 공유 fetch 헬퍼
    ├── theme.js            # 타입 색/한글라벨 단일 팔레트(전 뷰 공유)
    ├── getbible.js         # 외부 한국어 성경 API 장 fetch + 캐시
    ├── convexHull.js       # Graham scan(인물 장소 영역 폴리곤)
    ├── index.css
    └── assets/             # hero.png 등 번들 자산
```

- 컴포넌트 파일은 `PascalCase.jsx`(컴포넌트당 1파일, default export). 유틸/모듈은 `camelCase.js`(`api.js`, `theme.js`, `getbible.js`, `convexHull.js`).
- 라우팅 라이브러리 없음 — 뷰 전환은 `App.jsx`의 `activeView` 상태로 처리.

## 4. data/

정적 보강 JSON. `docker-compose.yml`이 `./data`를 api 컨테이너 `/app/data`로 마운트. 백엔드는 `DATA_DIR`(기본 `/app/data`) 또는 레포 상대경로(`backend/`에서 `../../data`)로 접근.

```
data/
├── names_ko/               # 노드 한글 이름·별칭 (inject_ko_names.py)
│   ├── people.json         #   { "<tid>": { "ko": "...", "alias": [...] } }
│   ├── places.json
│   ├── events.json
│   ├── groups.json
│   └── books.json
├── book_context/
│   └── books.json          # 권별 background/themes/keyVerse (inject_book_context.py)
├── character_traits/
│   └── people.json         # 인물 traits[{trait, verse_ref, description}] (inject_person_traits.py)
├── book_years_approx/
│   └── books.json          # 권 추정연도 { "<tid>": {nameKo, placementYear, basis, approx} } (런타임 오버레이 → /books)
└── event_verses/           # 사건별 근거 구절 오버레이 (런타임 → /event/{id}/verses)
    └── events.json         #   { "<eventTid>": { "books": [{bookId, bookOrder, rangeLabel, verses:[{verseID, chapter, verse}]}] } }
```

- 하위 디렉터리 = 도메인 영역(snake_case), 파일명 = 그 영역의 엔티티 종류(`people.json`/`places.json`/`events.json`/`books.json`/`groups.json`).
- 최상위 키는 theographic 레코드 id(`theographic_id`, 예 `recIFusdNl6d8dj3L`). 노드 join 키로 일관되게 사용.
- `event_verses/`와 `book_years_approx/`는 DB에 주입되지 않고 API가 런타임에 직접 읽는 오버레이.

## 5. 명명·경로 규약 요약

- **노드 식별자**: `theographic_id`(theographic-bible-metadata의 `rec...` id). 모든 `data/` JSON 키이자 노드 join 키.
- **이름 필드**: DB·API 응답에서 영어 `name`(Event는 `title`) + 한글 `nameKo` + `aliasesKo`. 미번역 노드는 `nameKoMissing` 플래그.
- **백엔드 라우트 파일**: 엔드포인트 그룹별 모듈(`nodes`/`events`/`books`/`search`), 각각 `router = APIRouter()`를 `main.py`가 `include_router`.
- **프론트 색/라벨**: 반드시 `frontend/src/theme.js`에서 import(중복 정의 금지 — 과거 충돌 회고).
- **프론트 API 호출**: 반드시 `frontend/src/api.js`의 `apiGet` 경유(단일 베이스 URL).
- **빌드 산출물**: `frontend/dist/`는 git에 추적되어 nginx 볼륨으로 직접 서빙(배포 시 `deploy.sh`가 재빌드).
