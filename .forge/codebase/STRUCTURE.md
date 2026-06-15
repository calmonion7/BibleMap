---
last_mapped_commit: 22a678c36e40548a3d00ccf9205862505a59d9cb
mapped: 2026-06-16
---

# 디렉터리 구조

## 최상위 레이아웃

```
BibleMap/
├── frontend/          React SPA (Vite)
├── backend/           FastAPI 앱 + 적재 스크립트
├── data/              한글 이름·문맥·성품·추정연도 JSON (Neo4j 외부 데이터)
├── nginx/             nginx 리버스 프록시 설정
├── docker-compose.yml 3서비스 오케스트레이션 (neo4j / api / nginx)
├── deploy.sh          빌드+컨테이너 재시작+한글이름 주입 배포 스크립트
├── .github/workflows/deploy.yml  self-hosted runner 자동 배포
├── .env / .env.example           NEO4J_PASSWORD
├── CLAUDE.md          프로젝트 행동 지침
├── BIBLEMAP_PLAN.md   기획 문서
└── README.md
```

## `frontend/` — React SPA

```
frontend/
├── index.html          진입 HTML (src/main.jsx 로드, <div id="root">)
├── vite.config.js      Vite + @vitejs/plugin-react
├── eslint.config.js    ESLint (react-hooks v7 규칙)
├── package.json        deps: react 19, maplibre-gl, lucide-react
├── .env.production      VITE_API_URL=/api (빌드타임 주입 → nginx 프록시)
├── public/             favicon.svg, icons.svg (정적 자산)
├── dist/               빌드 산출물 (nginx가 서빙; deploy.sh가 생성)
└── src/
    ├── main.jsx         createRoot → <App/> 마운트 (StrictMode)
    ├── App.jsx          루트 컴포넌트 — 전역 상태·탭 전환·검색·SidePanel 오버레이
    ├── MapView.jsx      MapLibre 지도 뷰 (마커·hull·사건 링)
    ├── TimelineView.jsx 연도순 통합 타임라인 (사건 + 책)
    ├── SidePanel.jsx    선택 노드 상세 패널 (Person/Book/기타 분기)
    ├── theme.js         타입 색·한글 라벨·표시 순서 단일 팔레트
    ├── api.js           API_BASE + apiGet() GET 헬퍼 (부분 도입)
    ├── convexHull.js    Graham scan 볼록껍질 (MapView 인물 활동범위)
    ├── App.css / index.css   전역 스타일
    └── assets/          hero.png, react.svg, vite.svg
```

`src/` 파일 명명: 컴포넌트는 **PascalCase + `.jsx`**(`App.jsx`, `MapView.jsx`, `TimelineView.jsx`, `SidePanel.jsx`). 비컴포넌트 모듈은 **camelCase + `.js`**(`theme.js`, `api.js`, `convexHull.js`). 한 파일 = 한 컴포넌트(default export). 인라인 스타일 객체를 직접 쓰는 방식(CSS 모듈/styled 미사용).

## `backend/` — FastAPI

```
backend/
├── Dockerfile          python:3.12-slim, uvicorn app.main:app :8000
├── requirements.txt    fastapi, neo4j, uvicorn
├── __init__.py
├── app/
│   ├── __init__.py
│   ├── main.py         FastAPI 진입 — lifespan 인덱스 생성 + 라우터 등록 + CORS
│   ├── db.py           get_driver() — Neo4j 드라이버 싱글톤
│   └── routes/
│       ├── __init__.py
│       ├── nodes.py    GET /node/{id}, /node/{id}/places, /node/{id}/neighbors/grouped
│       ├── events.py   GET /events
│       ├── search.py   GET /search
│       └── books.py    GET /books (추정연도 오버레이)
└── scripts/            일회성 적재 스크립트 (런타임 밖)
    ├── __init__.py
    ├── load_theographic.py    노드+관계 적재 (people/places/events/peopleGroups)
    ├── load_books.py          Book 노드 + CONTAINS_BOOK + 연도범위 추정
    ├── inject_ko_names.py     data/names_ko/* → 노드 nameKo/aliasesKo SET
    ├── generate_book_context.py   Claude API → data/book_context/books.json
    ├── inject_book_context.py     그 JSON → Book background/themes/keyVerse SET
    ├── generate_person_traits.py  Claude API → data/character_traits/people.json
    └── inject_person_traits.py    그 JSON → Person traits SET
```

`backend/app/` 명명: 라우트 모듈은 **소문자 명사 + `.py`**(`nodes.py`, `events.py`, `search.py`, `books.py`)이며 각자 `router = APIRouter()`를 노출. 핸들러 함수는 `get_<엔티티>` 스네이크케이스. 라우트당 모듈 상수로 한계값 정의(`NODE_NEIGHBOR_LIMIT`, `MAX_NEIGHBORS_PER_TYPE`, `SEARCH_LIMIT`).

`backend/scripts/` 명명: 적재는 **`load_*`**, AI 생성은 **`generate_*`**, 그래프 SET 주입은 **`inject_*`** 동사 접두로 단계를 구분한다. `generate_*` ↔ `inject_*`가 `data/<카테고리>/` JSON 파일을 매개로 짝을 이룬다. 모든 스크립트는 환경변수로 Neo4j 접속하고 `if __name__ == "__main__": main()` 패턴을 따른다.

## `data/` — 그래프 외부 데이터 (`./data:/app/data` 마운트)

```
data/
├── names_ko/           theographic_id → {ko, alias} 한글 이름 (inject_ko_names.py가 소비)
│   ├── people.json
│   ├── places.json
│   ├── events.json
│   ├── groups.json
│   └── books.json
├── book_context/
│   └── books.json      theographic_id → {background, themes, keyVerse} (generate/inject_book_context)
├── character_traits/
│   └── people.json     theographic_id → {traits:[{trait, verse_ref, description}]} (generate/inject_person_traits)
└── book_years_approx/
    └── books.json      theographic_id → {nameKo, placementYear, basis, approx}
                        — Neo4j에 주입 안 함. routes/books.py가 런타임 오버레이로만 읽음.
```

`data/` 명명 규칙: **`<카테고리>/<엔티티복수>.json`** 디렉터리 구조. 최상위 키는 모두 노드의 `theographic_id`. `names_ko`/`book_context`/`character_traits`는 `inject_*` 스크립트로 그래프에 들어가지만, **`book_years_approx`만 그래프에 주입되지 않고** `backend/app/routes/books.py`가 매 요청 시 직접 읽는 런타임 오버레이 데이터다.

## `nginx/`

```
nginx/
└── nginx.conf   :80 — /api/ → http://api:8000/ 프록시,
                       정적 자산 long-cache, /index.html no-cache, SPA fallback
```

## 주요 파일 빠른 참조

| 무엇 | 경로 |
|---|---|
| 프론트 진입 | `frontend/index.html` → `frontend/src/main.jsx` → `frontend/src/App.jsx` |
| 백엔드 진입 | `backend/app/main.py` |
| Neo4j 드라이버 | `backend/app/db.py` |
| 노드/이웃/장소 API | `backend/app/routes/nodes.py` |
| 검색 API | `backend/app/routes/search.py` |
| 타임라인 사건 API | `backend/app/routes/events.py` |
| 책+추정연도 API | `backend/app/routes/books.py` |
| 타입 색/라벨 팔레트 | `frontend/src/theme.js` |
| 추정연도 오버레이 데이터 | `data/book_years_approx/books.json` |
| 컨테이너 오케스트레이션 | `docker-compose.yml` |
| 배포 스크립트 | `deploy.sh`, `.github/workflows/deploy.yml` |
