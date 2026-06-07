---
last_mapped_commit: no-commits-yet
mapped: 2026-06-08
---

# 디렉터리 구조 맵 — BibleMap

> 이 구조는 설계 문서(`BIBLEMAP_PLAN.md`) 기반의 계획이다. 아직 실제 디렉터리는 존재하지 않는다.

---

## 전체 레이아웃

```
BibleMap/
  data/
    names_ko/               # 한글 이름 매핑 JSON 파일 (개역개정 기준)
      people.json           # { "<theographic_id>": { "ko": "모세", "alias": ["모세스"] } }
      places.json           # 동일 구조, 장소 이름
      events.json           # 동일 구조, 사건 제목 (서술형, 전수 큐레이션)
      periods.json          # 동일 구조, 시대 제목 (서술형, 전수 큐레이션)
  backend/                  # FastAPI 앱 (계획)
    main.py                 # FastAPI 앱 진입점, 라우터 등록
    routers/                # 엔드포인트별 라우터 모듈
    db/                     # Neo4j 드라이버 연결 모듈
  frontend/                 # React 19 + Vite 앱 (계획)
    src/
      views/                # MapView, TimelineView, GraphView 컴포넌트
      components/           # 공용 UI 컴포넌트
      store/                # selectedNode 공유 상태
  docker-compose.yml        # neo4j + api 두 서비스 정의
  .forge/
    codebase/               # 이 코드베이스 맵 문서
```

---

## 디렉터리별 설명

### `data/names_ko/`

한글 매핑 레이어의 진실 원천(source of truth). 파일을 레포에서 버전 관리한다.

- **키**: `theographic_id` (Theographic 원본 export의 안정 식별자)
- **값**: `{ "ko": string, "alias": string[] }`
  - `ko`: 기본 표시명 (개역개정 표기)
  - `alias`: 검색용 이형·별칭 (선택, 생략 가능)
- 인물(`people.json`)과 장소(`places.json`)는 Tier 1 수동 큐레이션 후 Tier 2 위키데이터(CC0) 자동 채움
- 사건(`events.json`)과 시대(`periods.json`)는 수가 적어 전수 큐레이션

### `backend/`

FastAPI 앱. Python 코드 전반에 snake_case 네이밍 적용.

- `main.py`: 앱 생성, 라우터 include, 시작/종료 이벤트
- `routers/`: 라우터 모듈. 엔드포인트 그룹별 분리
  - 예: `nodes.py` (`/node/{id}`, `/node/{id}/neighbors`), `search.py` (`/search`), `periods.py` (`/period/{id}/events`)
- `db/`: Neo4j Python 드라이버 세션 팩토리. compose 내부 서비스명 `bolt://neo4j:7687`으로 연결

### `frontend/`

React 19 + Vite 앱. JS/TS 코드 전반에 camelCase 네이밍 적용.

- `src/views/`: 세 뷰 컴포넌트
  - `MapView`: MapLibre GL 기반 지도 렌더링
  - `TimelineView`: vis-timeline 또는 D3 기반 시간 축 렌더링
  - `GraphView`: react-force-graph 또는 Cytoscape.js 기반 관계도 렌더링
- `src/components/`: 검색창, 엔티티 상세 패널 등 공용 UI 컴포넌트
- `src/store/`: `selectedNode` 전역 상태. 세 뷰가 이 상태를 구독해 동기화됨

### `docker-compose.yml`

두 서비스를 단일 compose 네트워크에 묶는다.

- `neo4j` 서비스: `neo4j:5` 공식 이미지 (arm64 지원), 데이터는 볼륨 마운트로 영속화. 호스트 포트는 `127.0.0.1:7474:7474` / `127.0.0.1:7687:7687`으로 로컬 전용 바인딩
- `api` 서비스: FastAPI, 포트 8000 publish. `restart: unless-stopped`로 상시 가동

---

## 네이밍 컨벤션

| 영역 | 컨벤션 |
|---|---|
| Python (backend) | snake_case |
| JavaScript/TypeScript (frontend) | camelCase |
| 엔티티 안정 키 | `theographic_id` |
| 한글명 속성 | `nameKo` |
| 한글 별칭 속성 | `aliasesKo` |
| 미번역 플래그 | `nameKoMissing` |

---

## 현재 상태

실제로 존재하는 파일:

- `BIBLEMAP_PLAN.md` — 설계 문서 (진입점)
- `CLAUDE.md` — 개발 가이드라인
- `.forge/codebase/ARCHITECTURE.md` — 아키텍처 맵
- `.forge/codebase/STRUCTURE.md` — 이 파일

소스 코드 디렉터리(`backend/`, `frontend/`, `data/`, `docker-compose.yml`)는 아직 생성되지 않았다. Phase 0 착수 시 `backend/`, `data/names_ko/`부터 생성된다.
