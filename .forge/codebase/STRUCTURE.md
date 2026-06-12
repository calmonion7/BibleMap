---
last_mapped_commit: 651f526aacfad0cfa86b4df41aaa9f08dcc7da22
mapped: 2026-06-12
---

# 디렉터리 구조

루트는 단일 리포(`/Users/calmonion/Project/BibleMap`)에 백엔드·프론트엔드·인프라·데이터를 함께 둔다.

```
BibleMap/
├── docker-compose.yml          # neo4j + api + nginx 3서비스
├── deploy.sh                   # 배포 스크립트(CI가 호출)
├── .env.example                # NEO4J_PASSWORD 템플릿
├── CLAUDE.md / README.md / BIBLEMAP_PLAN.md
│
├── backend/
│   ├── Dockerfile              # python:3.12-slim, uvicorn app.main:app:8000
│   ├── requirements.txt        # fastapi / neo4j / uvicorn (핀 버전)
│   └── app/
│       ├── main.py             # FastAPI 앱, lifespan 인덱스, CORS, 라우터 등록
│       ├── db.py               # get_driver() 단일 Neo4j 드라이버
│       └── routes/
│           ├── nodes.py        # /node/{id}, /node/{id}/places, /node/{id}/neighbors/grouped
│           ├── events.py       # /events
│           └── search.py       # /search
│   └── scripts/                # 런타임 아님 — 일회성 데이터 적재
│       ├── load_theographic.py # 원본 JSON → Neo4j 노드/관계
│       └── inject_ko_names.py  # data/names_ko/*.json 한글명 주입
│
├── frontend/
│   ├── index.html              # SPA 진입(루트 div + main.jsx 로드)
│   ├── vite.config.js          # @vitejs/plugin-react
│   ├── eslint.config.js
│   ├── package.json            # React 19, maplibre-gl, cytoscape, lucide-react
│   ├── .env.production         # VITE_API_URL=/api
│   ├── dist/                   # 빌드 산출물(nginx가 마운트해 서빙)
│   ├── public/                 # favicon.svg, icons.svg
│   └── src/
│       ├── main.jsx            # createRoot + StrictMode <App/>
│       ├── App.jsx             # 전역 선택/히스토리/반응형, 탭, 검색, 패널 셸
│       ├── MapView.jsx         # MapLibre 지도 뷰
│       ├── TimelineView.jsx    # 사건 타임라인 뷰
│       ├── GraphView.jsx       # cytoscape 그래프 뷰
│       ├── SidePanel.jsx       # 노드 상세 + 이웃 그룹 패널
│       ├── App.css / index.css
│       └── assets/             # hero.png 등
│
├── nginx/
│   └── nginx.conf              # /api/ 프록시 + 정적 SPA + 캐시 헤더
│
├── data/
│   └── names_ko/               # people/places/events/groups.json (한글명 소스)
│
└── .github/workflows/
    └── deploy.yml              # main 푸시 → self-hosted 러너 배포
```

## 주요 파일 위치 표

| 찾는 것 | 위치 |
|---|---|
| FastAPI 앱 진입/부트스트랩 | `backend/app/main.py` |
| Neo4j 드라이버/연결 설정 | `backend/app/db.py` |
| 노드 상세 + 이웃 API | `backend/app/routes/nodes.py` (`get_node`, `get_node_places`, `get_node_neighbors_grouped`) |
| 사건 목록 API | `backend/app/routes/events.py` |
| 검색 API | `backend/app/routes/search.py` |
| 그래프 데이터 적재 | `backend/scripts/load_theographic.py` |
| 한글명 주입 | `backend/scripts/inject_ko_names.py` |
| 한글명 원천 데이터 | `data/names_ko/{people,places,events,groups}.json` |
| 프론트 진입 HTML | `frontend/index.html` |
| React 마운트 | `frontend/src/main.jsx` |
| 전역 상태(선택/히스토리)·탭·검색·반응형 셸 | `frontend/src/App.jsx` |
| 지도 뷰(MapLibre) | `frontend/src/MapView.jsx` |
| 타임라인 뷰 | `frontend/src/TimelineView.jsx` |
| 그래프 뷰(cytoscape) | `frontend/src/GraphView.jsx` |
| 상세 패널 | `frontend/src/SidePanel.jsx` |
| 프론트 의존성/스크립트 | `frontend/package.json` |
| Vite 설정 | `frontend/vite.config.js` |
| 프로덕션 API URL | `frontend/.env.production` (`VITE_API_URL=/api`) |
| nginx 라우팅/프록시/캐시 | `nginx/nginx.conf` |
| 컨테이너 오케스트레이션 | `docker-compose.yml` |
| API 컨테이너 빌드 | `backend/Dockerfile` |
| CI 배포 | `.github/workflows/deploy.yml`, `deploy.sh` |

## 명명/배치 규칙

- **백엔드 라우트**: 엔드포인트 묶음당 한 파일(`routes/<도메인>.py`)이며 각 파일이 자체 `router = APIRouter()`를 만들고 `main.py`가 `include_router`로 모은다. 라우트 핸들러는 평범한 함수, Cypher는 핸들러 내부에 인라인.
- **백엔드 상수**: 조회 한도는 모듈 상단 대문자 상수(`NODE_NEIGHBOR_LIMIT`, `MAX_NEIGHBORS_PER_TYPE`, `SEARCH_LIMIT`).
- **노드 식별자**: 경로 파라미터 `node_id`는 항상 Neo4j `theographic_id` 값.
- **프론트 컴포넌트**: 한 화면 단위 = `PascalCase.jsx` 1파일, default export. 뷰 컴포넌트는 모두 `{ onSelectNode, selectedNode }` prop 시그니처를 공유(`SidePanel`은 추가로 `nodeId`/`onBack`/`canGoBack`).
- **API 베이스 상수**: 각 프론트 파일이 독립적으로 `API_URL`(또는 `App.jsx`의 `API_BASE`)을 `import.meta.env.VITE_API_URL || 'http://localhost:8000'`로 정의 — 공유 모듈 없음.
- **결합 상수 동기화**: `App.jsx`의 `SHEET_VH=55`와 `MapView.jsx`의 `fitBounds` 하단 패딩 비율 `0.55`는 동일 값을 양쪽에서 수동 유지(주석으로 명시).
- **인라인 스타일**: CSS 파일(`App.css`/`index.css`)은 최소. 컴포넌트 스타일은 JSX `style` 객체로 직접 지정하는 것이 지배적 패턴.
- **한국어 라벨 매핑**: 사용자 노출 한글 라벨은 컴포넌트 상단 객체 상수로(`SidePanel.jsx`의 `REL_KO`/`TYPE_KO`/`TYPE_COLOR`, `GraphView.jsx`의 `TYPE_LABEL_KO`/`TYPE_COLOR`).
- **데이터 적재 스크립트**: 런타임 코드(`backend/app/`)와 분리해 `backend/scripts/`에 둔다 — 서버가 임포트하지 않는 일회성 도구.
- **빌드 산출물 커밋**: `frontend/dist/`가 리포에 포함되어 nginx가 그대로 마운트·서빙한다.
