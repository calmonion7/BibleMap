---
last_mapped_commit: bfc1dd258b0308435ca24c48a82c9c86a9e622f1
mapped: 2026-06-16
---

# STRUCTURE

## 최상위 레이아웃

```
BibleMap/
├── frontend/            React + Vite SPA
├── backend/             FastAPI 앱 + 오프라인 데이터 스크립트
├── data/                Neo4j 적재용 + /books 런타임용 JSON 오버레이
├── nginx/               리버스 프록시 설정
├── .github/workflows/   CI/배포
├── docker-compose.yml   neo4j / api / nginx 3-서비스 정의
├── deploy.sh            빌드 → 컨테이너 재시작 → 한글이름 주입 스크립트
├── .env / .env.example  NEO4J_PASSWORD 등 환경변수
├── CLAUDE.md            프로젝트 지침
├── BIBLEMAP_PLAN.md     기획 문서
└── README.md
```

## 프론트엔드 트리 (`frontend/`)

```
frontend/
├── index.html                진입 HTML (→ src/main.jsx)
├── vite.config.js            Vite 설정 (maplibre/vendor 수동 청크 분리)
├── eslint.config.js          ESLint 플랫 설정
├── package.json              deps: react 19, maplibre-gl, lucide-react
├── .env.production           VITE_API_URL=/api (프로덕션 빌드타임 주입)
├── public/
│   ├── icons.svg
│   └── favicon.svg
├── src/
│   ├── main.jsx              createRoot 부트스트랩
│   ├── App.jsx               셸: nav·검색·뷰 전환·상세 패널 컨테이너
│   ├── MapView.jsx           MapLibre 지도 뷰
│   ├── TimelineView.jsx      연표 뷰
│   ├── SidePanel.jsx         노드 상세 패널
│   ├── api.js                apiGet() + API_BASE 단일 클라이언트
│   ├── theme.js              TYPE_COLOR/TYPE_KO 등 공유 팔레트
│   ├── convexHull.js         Graham scan hull 유틸
│   ├── index.css             전역 스타일
│   └── assets/               hero.png, react.svg, vite.svg
└── dist/                     빌드 산출물 (nginx가 서빙; .gitignore 대상)
```

규약:
- React 컴포넌트 파일은 **PascalCase + `.jsx`**(`MapView.jsx`, `SidePanel.jsx`, `TimelineView.jsx`, `App.jsx`). 각 파일이 동명 컴포넌트 1개를 default export.
- 비-컴포넌트 모듈은 **camelCase/소문자 + `.js`**(`api.js`, `theme.js`, `convexHull.js`).
- 컴포넌트 간 데이터는 props로 내려보내고, 노드 선택은 `onSelectNode(id)` 콜백 + `selectedNode` prop 쌍으로 통일.
- 스타일은 인라인 `style={{...}}` 객체가 주(主), 전역은 `index.css` 만.
- 라우터 라이브러리 없음 — 뷰 전환은 `App.jsx` 의 `activeView` 상태로 처리(단일 라우트 SPA).

## 백엔드 트리 (`backend/`)

```
backend/
├── Dockerfile               python:3.12-slim, uvicorn app.main:app
├── requirements.txt         fastapi / neo4j / uvicorn
├── __init__.py
├── app/
│   ├── __init__.py
│   ├── main.py              FastAPI app, lifespan(인덱스 보장), 라우터 include
│   ├── db.py               get_driver() Neo4j 드라이버 싱글턴
│   └── routes/
│       ├── __init__.py
│       ├── nodes.py        /node/{id}, /node/{id}/places, /node/{id}/neighbors/grouped
│       ├── events.py       /events
│       ├── search.py       /search
│       └── books.py        /books (lru_cache 추정연도 + DATA_DIR 폴백)
└── scripts/                오프라인 데이터 파이프라인 (런타임 무관)
    ├── __init__.py
    ├── load_theographic.py     외부 raw JSON → Neo4j 그래프 적재
    ├── load_books.py           Book 노드 + CONTAINS_BOOK 관계 적재
    ├── inject_ko_names.py      data/names_ko/*.json → 노드 nameKo/alias SET
    ├── inject_book_context.py  data/book_context/books.json → Book background/themes/keyVerse SET
    ├── inject_person_traits.py data/character_traits/people.json → Person traits SET
    ├── generate_book_context.py    Claude API → data/book_context/books.json 생성
    └── generate_person_traits.py   Claude API → data/character_traits/people.json 생성
```

규약:
- Python 모듈은 **snake_case**. 패키지마다 `__init__.py` 존재.
- 각 라우트 모듈은 `router = APIRouter()` 를 모듈 전역으로 노출하고 `main.py` 가 `app.include_router(...)` 로 묶는다. 엔드포인트는 `@router.get(...)` 데코레이터.
- 라우트 핸들러는 `from ..db import get_driver` 로 DB에 접근하고 `with driver.session() as session:` 패턴으로 Cypher 실행.
- 환경변수 게이트(`NEO4J_PASSWORD` 없으면 `RuntimeError`)는 `db.py` 와 모든 `scripts/*.py` 상단에 반복 적용.
- 스크립트 동사 접두로 역할 구분: `load_*`(그래프 적재) / `inject_*`(속성 SET) / `generate_*`(Claude로 JSON 생성).
- 스크립트의 `data/` 경로는 `__file__` 기준 상대(`os.path.dirname(__file__)` + `../../data/...`)로 해석.

## 데이터 트리 (`data/`)

```
data/
├── names_ko/
│   ├── people.json     { "<theographic_id>": { "ko": "...", "alias": [...] } }
│   ├── places.json
│   ├── events.json
│   ├── groups.json
│   └── books.json
├── book_context/
│   └── books.json      { "<theographic_id>": { "background", "themes":[], "keyVerse" } }
├── character_traits/
│   └── people.json     { "<theographic_id>": { "traits": [{ "trait", "verse_ref", "description" }] } }
└── book_years_approx/
    └── books.json      { "<theographic_id>": { "nameKo", "placementYear", "basis", "approx" } }
```

규약:
- 모든 데이터 JSON은 최상위가 **`theographic_id` → 객체** 딕셔너리.
- 디렉터리명은 **snake_case 도메인 카테고리**, 파일명은 노드 종류 복수형(`people.json`/`places.json`/`books.json`/...).
- `book_years_approx/books.json` 만 런타임(`/books`)에서 직접 읽히고, 나머지는 적재 스크립트 입력 전용.

## 인프라 / 설정 파일 위치

| 용도 | 파일 |
|---|---|
| 컨테이너 오케스트레이션 | `docker-compose.yml` (neo4j/api/nginx, `./data:/app/data` 마운트) |
| API 이미지 빌드 | `backend/Dockerfile` |
| 리버스 프록시 | `nginx/nginx.conf` (`/api/` 프록시, SPA fallback, 정적 캐시 헤더) |
| 배포 스크립트 | `deploy.sh` (frontend 빌드 → `docker compose -p biblemap` → inject_ko_names) |
| CI/배포 | `.github/workflows/deploy.yml` |
| 프로덕션 API URL | `frontend/.env.production` (`VITE_API_URL=/api`) |
| 비밀/환경변수 | `.env`, `.env.example` (`NEO4J_PASSWORD`) |
