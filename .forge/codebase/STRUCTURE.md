---
last_mapped_commit: 26240c7cf18f421b2f8baa4fd6584f40eede57b0
mapped: 2026-06-11
---

# STRUCTURE

## 루트 레이아웃

```
BibleMap/
├── backend/          FastAPI + Neo4j 백엔드, 데이터 적재 스크립트
├── frontend/         React 19 + Vite SPA
├── data/             한글 이름 오버레이 JSON
├── nginx/            리버스 프록시 설정
├── scripts/          자동 배포 폴링 스크립트
├── .github/workflows/ CI 배포 워크플로우
├── docker-compose.yml
├── deploy.sh         빌드·재기동·한글명 주입 배포 스크립트
├── .env / .env.example
├── BIBLEMAP_PLAN.md  초기 기획 문서
├── CLAUDE.md         프로젝트 작업 가이드라인
└── README.md
```

## backend/

```
backend/
├── Dockerfile              python:3.12-slim, uvicorn app.main:app
├── requirements.txt        fastapi, neo4j, uvicorn (핀 버전)
├── __init__.py
├── app/
│   ├── __init__.py
│   ├── main.py             ★ 백엔드 진입점: FastAPI 앱, CORS, lifespan 인덱스 생성, 라우터 등록
│   ├── db.py               get_driver() — Neo4j 드라이버 싱글턴
│   └── routes/
│       ├── __init__.py
│       ├── nodes.py        GET /node/{id}, /node/{id}/neighbors/grouped, /node/{id}/places
│       ├── places.py       GET /places
│       ├── events.py       GET /events
│       └── search.py       GET /search?q=
└── scripts/
    ├── __init__.py
    ├── load_theographic.py 원본 theographic JSON → Neo4j 노드/관계 적재
    └── inject_ko_names.py  data/names_ko/*.json → 노드에 nameKo/aliasesKo 주입
```

- API 라우트를 찾을 곳: `backend/app/routes/`. 라우트 파일별로 `router = APIRouter()`를 만들고 `main.py`가 `include_router`한다. URL prefix는 데코레이터의 절대 경로로 직접 지정(라우터 prefix 미사용).
- DB 접속 코드: `backend/app/db.py` 한 군데. 모든 라우트가 `from ..db import get_driver` 후 `with driver.session()`.
- 데이터 적재/세팅은 `backend/scripts/`. 런타임 API 경로가 아니라 배포/초기화용. `load_theographic.py`는 직접 실행, `inject_ko_names.py`는 `deploy.sh`가 호출.

## frontend/

```
frontend/
├── index.html              루트 HTML, <div id="root">, /src/main.jsx 로드
├── package.json            React 19, vite, maplibre-gl, cytoscape(+coseBilkent,+expandCollapse), d3, lucide-react
├── vite.config.js          @vitejs/plugin-react 만 사용 (프록시 설정 없음)
├── eslint.config.js
├── .env.production         VITE_API_URL=/api
├── public/
│   ├── favicon.svg
│   └── icons.svg
├── dist/                   빌드 산출물 (nginx가 서빙)
└── src/
    ├── main.jsx            ★ 프론트 진입점: createRoot → <App/>
    ├── App.jsx             ★ 루트 컴포넌트: selectedNode/activeView 상태, 탭·검색, 뷰·패널 배치
    ├── MapView.jsx         지도 뷰 (MapLibre GL)
    ├── TimelineView.jsx    타임라인 뷰
    ├── GraphView.jsx       그래프 뷰 (Cytoscape)
    ├── SidePanel.jsx       우측 상세 패널 (Map/Timeline 전용)
    ├── App.css / index.css 전역 스타일
    └── assets/             hero.png, react.svg, vite.svg
```

- 뷰 컴포넌트는 `frontend/src/` 최상위에 평평하게 위치. 컴포넌트 디렉터리 분리 없음. 파일명 = PascalCase 컴포넌트명(`MapView.jsx`, `GraphView.jsx`, `TimelineView.jsx`, `SidePanel.jsx`).
- 컴포넌트 인터페이스 규약: 뷰는 `{ onSelectNode, selectedNode }`, SidePanel은 `{ nodeId, onSelectNode }`.
- API 베이스 URL은 각 파일이 자체 정의: `const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'`. 공용 API 클라이언트/상수 모듈은 없음.
- 스타일은 인라인 `style={{}}` 객체가 지배적. CSS 파일(`App.css`/`index.css`)은 최소.
- 한글 라벨 매핑은 각 컴포넌트 상단 상수 객체로 흩어져 있음: 관계명 `REL_KO`(`SidePanel.jsx`), 타입 라벨 `LABEL_TYPES`(`MapView.jsx`)·`TYPE_LABEL_KO`(`GraphView.jsx`), 타입 색상 `TYPE_COLOR`(`GraphView.jsx`).

## data/

```
data/names_ko/
├── people.json   Person  theographic_id → { ko, alias[] }
├── places.json   Place
├── events.json   Event
└── groups.json   PeopleGroup
```

- 한글 이름 오버레이 데이터. 키는 `theographic_id`, 값은 `{ "ko": "한글명", "alias": [...] }`. `inject_ko_names.py`가 읽어 Neo4j에 주입. compose에서 `./data`가 `api` 컨테이너의 `/app/data`로 마운트.
- 원본 성서 메타데이터(노드/관계) 자체는 리포에 없고 `load_theographic.py`가 GitHub에서 받아온다.

## 인프라 / 배포 파일 위치

- `docker-compose.yml` (루트): `neo4j` / `api` / `nginx` 3개 서비스, 프로젝트명 `biblemap`.
- `nginx/nginx.conf`: `/api/` 프록시 + SPA fallback + 캐시 정책.
- `deploy.sh` (루트): 프론트 빌드 → API 이미지 빌드 → `api`/`nginx` 재기동 → `inject_ko_names.py`. lock 파일 `/tmp/biblemap-deploy.lock`.
- `.github/workflows/deploy.yml`: self-hosted runner, main push 시 worktree에서 `deploy.sh` 실행.
- `scripts/auto-deploy-poll.sh`: 2분 폴링 자동 배포 (worktree `worktree-wise-sprouting-hellman` 브랜치 기준).
- 환경변수: 루트 `.env`/`.env.example`은 `NEO4J_AUTH=neo4j/<password>`. 프론트 `frontend/.env.production`은 `VITE_API_URL=/api`. 백엔드는 `NEO4J_URI`/`NEO4J_USER`/`NEO4J_PASSWORD`.

## 무엇을 어디서 찾나 (빠른 색인)

- 새 API 엔드포인트 추가 → `backend/app/routes/`에 라우트 작성 + `backend/app/main.py`에 `include_router`.
- Cypher 쿼리 / 그래프 스키마(레이블·관계) 확인 → `backend/app/routes/nodes.py`(조회), `backend/scripts/load_theographic.py`(적재 시 정의).
- 지도 동작/마커/타일 → `frontend/src/MapView.jsx`.
- 그래프 레이아웃/색상/그룹핑 → `frontend/src/GraphView.jsx`.
- 타임라인 그룹핑/연도 파싱 → `frontend/src/TimelineView.jsx`.
- 전역 상태·탭·검색·패널 레이아웃 → `frontend/src/App.jsx`.
- 노드 상세 패널·이웃 드릴다운 → `frontend/src/SidePanel.jsx`.
- 한글 이름 수정 → `data/names_ko/*.json` 편집 후 `inject_ko_names.py` 재실행(또는 재배포).
- 배포 흐름 → `deploy.sh`, `docker-compose.yml`, `nginx/nginx.conf`.
