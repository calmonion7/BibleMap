---
last_mapped_commit: 60962d0693f3bfaf4b8d24ce6f97d7b392770d85
mapped: 2026-06-11
---

# STRUCTURE

프로젝트 루트: `/Users/calmonion/Project/BibleMap`

## 디렉터리 레이아웃

```
BibleMap/
├── backend/                  FastAPI 백엔드
│   ├── Dockerfile            python:3.12-slim, uvicorn app.main:app
│   ├── requirements.txt      fastapi / neo4j / uvicorn (핀 버전)
│   ├── __init__.py           (빈 파일)
│   ├── app/                  애플리케이션 코드
│   │   ├── __init__.py       (빈 파일)
│   │   ├── main.py           FastAPI 진입점 — lifespan, CORS, 라우터 등록
│   │   ├── db.py             get_driver() Neo4j 드라이버 싱글톤
│   │   └── routes/           API 라우터 모듈
│   │       ├── __init__.py   (빈 파일)
│   │       ├── nodes.py      /node/* 엔드포인트
│   │       ├── events.py     /events 엔드포인트
│   │       └── search.py     /search 엔드포인트
│   └── scripts/              오프라인 데이터 적재 스크립트
│       ├── __init__.py       (빈 파일)
│       ├── load_theographic.py   theographic JSON → Neo4j 노드·관계 적재
│       └── inject_ko_names.py    한글 이름(nameKo/aliasesKo) 주입
│
├── frontend/                 React 19 + Vite SPA
│   ├── index.html            HTML 진입점 (src/main.jsx 로드)
│   ├── package.json          의존성·스크립트 (dev/build/lint/preview)
│   ├── vite.config.js        Vite + @vitejs/plugin-react
│   ├── eslint.config.js      ESLint 설정
│   ├── .env.production        VITE_API_URL=/api (프로덕션 API 베이스)
│   ├── .gitignore
│   ├── README.md
│   ├── public/               정적 자산 (favicon.svg, icons.svg)
│   ├── src/                  소스
│   │   ├── main.jsx          React 루트 마운트 (StrictMode → App)
│   │   ├── App.jsx           셸: 탭 내비 + 검색 + selectedNode 상태
│   │   ├── MapView.jsx       MapLibre GL 지도 뷰
│   │   ├── TimelineView.jsx  사건 연표 뷰
│   │   ├── GraphView.jsx     Cytoscape 그래프 뷰
│   │   ├── SidePanel.jsx     노드 상세·이웃 패널
│   │   ├── App.css / index.css   스타일
│   │   └── assets/           hero.png, react.svg, vite.svg
│   └── dist/                 빌드 산출물 (nginx가 서빙, 커밋됨)
│
├── data/
│   └── names_ko/             한글 이름 매핑 데이터 (JSON)
│       ├── people.json       Person  theographic_id → {ko, alias[]}
│       ├── places.json       Place
│       ├── events.json       Event
│       └── groups.json       PeopleGroup
│
├── nginx/
│   └── nginx.conf            리버스 프록시 + SPA 정적 서빙 설정
│
├── .github/
│   └── workflows/
│       └── deploy.yml        main 푸시 → self-hosted 러너 배포
│
├── scripts/
│   └── auto-deploy-poll.sh   2분 폴링 자동 배포 스크립트
│
├── docker-compose.yml        neo4j / api / nginx 서비스 (프로젝트명 biblemap)
├── deploy.sh                 빌드·배포·한글주입 오케스트레이션
├── .env / .env.example       NEO4J_PASSWORD (compose가 NEO4J_AUTH 파생)
├── CLAUDE.md                 작업 가이드라인 + 프로젝트 컨텍스트
├── README.md
└── BIBLEMAP_PLAN.md          기획 문서
```

## 핵심 파일 위치

| 역할 | 경로 |
| --- | --- |
| 백엔드 진입점 | `backend/app/main.py` |
| Neo4j 드라이버 싱글톤 | `backend/app/db.py` (`get_driver()`) |
| 노드 API | `backend/app/routes/nodes.py` |
| 사건 API | `backend/app/routes/events.py` |
| 검색 API | `backend/app/routes/search.py` |
| 백엔드 컨테이너 정의 | `backend/Dockerfile` |
| 데이터 적재(초기) | `backend/scripts/load_theographic.py` |
| 한글 이름 주입 | `backend/scripts/inject_ko_names.py` |
| 프론트엔드 진입점 | `frontend/src/main.jsx`, `frontend/src/App.jsx` |
| 지도 뷰 | `frontend/src/MapView.jsx` |
| 연표 뷰 | `frontend/src/TimelineView.jsx` |
| 그래프 뷰 | `frontend/src/GraphView.jsx` |
| 상세 패널 | `frontend/src/SidePanel.jsx` |
| 한글 이름 데이터 | `data/names_ko/*.json` |
| 프록시 설정 | `nginx/nginx.conf` |
| 컨테이너 오케스트레이션 | `docker-compose.yml` |
| 배포 스크립트 | `deploy.sh`, `scripts/auto-deploy-poll.sh` |
| CI 워크플로 | `.github/workflows/deploy.yml` |

## 네이밍 컨벤션

### 백엔드 (Python)

- 모듈·파일: 소문자 스네이크 케이스 (`db.py`, `load_theographic.py`).
- 라우트 핸들러 함수: `get_<리소스>` (`get_node`, `get_events`, `search`).
- 모듈 레벨 상수: 대문자 스네이크 케이스 (`MAX_NEIGHBORS_PER_TYPE`, `NODE_NEIGHBOR_LIMIT`, `SEARCH_LIMIT`, `BATCH_NODE`, `BATCH_REL`).
- 각 패키지 디렉터리에 빈 `__init__.py` 존재.
- 주석·로그·예외 메시지는 한국어가 섞여 있다(`"NEO4J_PASSWORD 환경변수가 설정되지 않았습니다"` 등).

### Neo4j 그래프 모델

- 노드 라벨: PascalCase 단수 (`Person`, `Place`, `Event`, `PeopleGroup`).
- 관계 타입: UPPER_SNAKE_CASE (`PARENT_OF`, `CHILD_OF`, `SIBLING_OF`, `PARTNER_OF`, `MEMBER_OF`, `HAS_PARTICIPANT`, `OCCURS_AT`, `PART_OF`).
- 노드 속성: camelCase (`theographic_id`는 예외적 스네이크, `nameKo`, `aliasesKo`, `startDate`, `sortKey`, `displayTitle`, `featureType` 등).
- 식별 키는 일관되게 `theographic_id`. 인덱스 이름은 `<label소문자>_tid` (`person_tid` 등; 단 적재 스크립트에서 PeopleGroup은 `pg_tid`).

### 프론트엔드 (React/JSX)

- 컴포넌트 파일: PascalCase `.jsx` (`MapView.jsx`, `SidePanel.jsx`).
- 기본 내보내기(`default export`) 컴포넌트가 파일명과 일치.
- API 베이스 URL 상수: 각 컴포넌트에서 `API_URL`(또는 `App.jsx`는 `API_BASE`) = `import.meta.env.VITE_API_URL || 'http://localhost:8000'`.
- 모듈 레벨 상수: 대문자 스네이크 (`EMPTY_GEOJSON`, `DEFAULT_NODE`, `TYPE_COLOR`, `TYPE_LABEL_KO`, `REL_KO`, `TABS`).
- 한국어 UI 문자열을 인라인으로 사용(`'검색...'`, `'로딩 중...'`, `'결과 없음'` 등).
- 스타일은 대부분 인라인 `style` 객체. 전역 CSS는 `App.css`, `index.css`.

### 데이터 (JSON)

- `data/names_ko/<엔티티>.json` 형태. 최상위가 `theographic_id` → `{ "ko": "<한글명>", "alias": [<별칭...>] }` 매핑인 객체.

## 환경변수

- `NEO4J_PASSWORD` (필수) — `.env`에 정의, compose가 `NEO4J_AUTH=neo4j/<password>`로 파생. 백엔드·적재 스크립트가 직접 읽음.
- `NEO4J_URI`, `NEO4J_USER` — 컨테이너 환경에서 `bolt://neo4j:7687` / `neo4j`로 주입(기본값 존재).
- `VITE_API_URL` — 프론트엔드 빌드 시 API 베이스 경로(프로덕션 `/api`).
