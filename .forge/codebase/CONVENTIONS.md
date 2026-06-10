---
last_mapped_commit: 26240c7cf18f421b2f8baa4fd6584f40eede57b0
mapped: 2026-06-11
---

# 코딩 컨벤션

BibleMap은 두 개의 독립된 코드베이스로 구성된다.

- 백엔드: Python 3.12 + FastAPI + Neo4j 드라이버 (`backend/`)
- 프론트엔드: React 19 + Vite 8 (`frontend/`)

테스트 프레임워크는 존재하지 않는다 (자세한 내용은 `TESTING.md`).

---

## 1. 언어 / i18n 컨벤션 (한글 이름 매핑)

이 프로젝트의 가장 두드러진 컨벤션. 모든 도메인 엔티티는 원본 영어 이름(`name`)과 한글 이름(`nameKo`)을 함께 갖는다.

### 데이터 계층

- 원본 데이터는 theographic-bible-metadata(영어)에서 적재한다 (`backend/scripts/load_theographic.py`). 노드에는 `name`/`title`만 들어간다.
- 한글 이름은 별도 JSON 매핑 파일에서 후처리로 주입한다 (`backend/scripts/inject_ko_names.py`).
- 매핑 파일은 `data/names_ko/` 아래에 엔티티별로 분리: `people.json`, `places.json`, `events.json`, `groups.json`.
- 매핑 파일 포맷은 `theographic_id` → `{ "ko": "<한글명>", "alias": ["<별칭>", ...] }`. 예시 (`data/names_ko/people.json`):

  ```json
  "reccdFYIq50NyxNej": {
    "ko": "아브라함",
    "alias": ["아브람"]
  }
  ```

- 주입 시 노드에 `nameKo`(문자열)와 `aliasesKo`(배열) 두 프로퍼티를 SET 한다 (`inject_ko_names.py`의 `inject()`).

### API 응답 계층의 폴백 규칙

라우트 핸들러는 한글 이름이 없을 때 영어 이름으로 폴백하는 일관된 패턴을 따른다 (`backend/app/routes/`):

```python
name = props.get("name") or props.get("title", "")
name_ko = props.get("nameKo")
# 응답에는: nameKo = name_ko if name_ko else name
```

- `nameKo` 필드는 항상 채워진 값으로 응답한다(한글 없으면 영어로 폴백).
- 추가로 `nameKoMissing`(불리언) 필드를 함께 내려보내, 클라이언트가 "미번역" 상태를 구분할 수 있게 한다. 판정 기준은 `name_ko is None` (`nodes.py`, `places.py`).
- `Event`는 이름 필드가 `title`이다. `name`이 없으면 `title`로 폴백하는 로직이 곳곳에 반복된다.

### UI 계층의 표기 규칙

- 한글이 있으면 `"<한글> (<영어>)"`, 없으면 `"<영어> (미번역)"` 형태로 표기한다 (`frontend/src/SidePanel.jsx`).
- UI 고정 라벨(관계명, 노드 타입명)은 컴포넌트 최상단의 상수 객체로 한↔영 매핑을 둔다:
  - 관계 한글명: `REL_KO` (`SidePanel.jsx`) — 예: `OCCURS_AT: '발생 장소'`.
  - 노드 타입 한글명: `LABEL_TYPES` (`MapView.jsx`), `TYPE_LABEL_KO` (`GraphView.jsx`).
- 사용자 대면 텍스트는 한국어(예: `검색...`, `결과 없음`, `로딩 중...`, `지도에서 마커를 클릭하세요`).

---

## 2. 백엔드 컨벤션 (Python / FastAPI)

### 모듈 구조

```
backend/
  app/
    main.py          # FastAPI 앱 생성, CORS, 라우터 등록, lifespan 인덱스 생성
    db.py            # Neo4j 드라이버 싱글톤
    routes/          # 엔티티별 라우터 모듈
      nodes.py, places.py, events.py, search.py
  scripts/           # 일회성 데이터 적재/주입 스크립트
    load_theographic.py, inject_ko_names.py
  requirements.txt   # 핀 고정 의존성
  Dockerfile
```

- 모든 패키지 디렉터리에 빈 `__init__.py`가 있다.
- 의존성은 정확한 버전으로 핀 고정 (`backend/requirements.txt`): `fastapi==0.136.3`, `neo4j==6.2.0`, `uvicorn==0.49.0`. 테스트/린트 의존성 없음.

### 라우터 패턴

각 라우트 모듈은 동일한 구조를 따른다 (`backend/app/routes/*.py`):

```python
from fastapi import APIRouter
from ..db import get_driver

router = APIRouter()

@router.get("/places")
def get_places():
    driver = get_driver()
    with driver.session() as session:
        result = session.run("MATCH ... RETURN ...")
        ...
        return [...]
```

- 라우터는 `main.py`에서 prefix 없이 `app.include_router(...)`로 등록한다. 경로는 라우트 데코레이터에 풀 패스로 적는다 (`/node/{node_id}`, `/places`, `/events`, `/search`).
- 핸들러는 **동기 함수**(`def`)다 — `async def`가 아니다. Neo4j 드라이버는 동기 세션을 사용한다.
- DB 접근은 항상 `with driver.session() as session:` 컨텍스트 매니저로 감싼다.

### Neo4j / Cypher 컨벤션

- 드라이버는 모듈 전역 싱글톤(`_driver`)으로 지연 초기화 (`backend/app/db.py`의 `get_driver()`).
- 노드 식별자는 외부 키 `theographic_id`. 모든 조회는 `{theographic_id: $id}` 패턴으로 매칭하고, 시작 시 라벨별 인덱스를 생성한다 (`main.py` lifespan, `load_theographic.py`의 `create_indexes`).
- Cypher 파라미터는 항상 바인딩(`$id`, `$q`, `$rows`) — 문자열 보간 금지. 단, **라벨명만은 f-string으로 동적 삽입**한다 (인덱스 생성: `f"CREATE INDEX {label.lower()}_tid ..."`).
- 여러 줄 Cypher는 삼중따옴표 문자열로 작성하고, 적재 스크립트에서는 가독성을 위해 `SET` 절을 컬럼 정렬한다 (`load_theographic.py`).
- Neo4j 노드 → dict 변환은 `dict(record["n"])` 후 `.get()`으로 안전 접근. 좌표 등 수치는 명시적 `float(...)` 캐스팅 (`places.py`, `nodes.py`).
- 결과 중복 제거가 필요할 때 `seen = set()` + `theographic_id` 키로 수동 dedup (`nodes.py`의 `get_node_places`).
- 결과 개수 상한은 Cypher `LIMIT`(검색 20, 이웃 50) 또는 파이썬 측 카운터(`get_node_neighbors_grouped`의 타입별 30개 상한)로 건다.

### 적재 스크립트 컨벤션 (`backend/scripts/`)

- 환경변수는 `os.getenv`/`os.environ.get`로 읽고 기본값을 둔다: `NEO4J_URI`(`bolt://localhost:7687`), `NEO4J_USER`(`neo4j`), `NEO4J_PASSWORD`(`biblemap123`).
- 적재는 `UNWIND $rows` + `MERGE` 패턴으로 멱등하게 작성. 배치 크기 상수: `BATCH_NODE = 500`, `BATCH_REL = 1000`. 공통 헬퍼 `run_batched()`로 청크 처리.
- 함수는 `load_<entity>` / `load_<rel>_rels` 단위로 잘게 나누고, 각 단계마다 `print(...)`로 진행 로그를 남긴다.
- 양방향 관계(`SIBLING_OF`, `PARTNER_OF`)는 `tuple(sorted([a, b]))`를 `seen` 집합에 넣어 중복 생성 방지.
- 스크립트는 `if __name__ == "__main__":` 가드로 실행. `driver.close()`로 명시적 정리.

### 에러 처리

- 백엔드 에러 처리는 의도적으로 최소화돼 있다 (CLAUDE.md의 "불가능한 시나리오용 에러 처리 금지" 원칙과 일치).
- 조회 실패는 `result.single()`이 falsy일 때 `raise HTTPException(status_code=404, detail="Node not found")` (`nodes.py`).
- `main.py`의 lifespan 인덱스 생성은 `try/except Exception: pass`로 감싸 — Neo4j 미기동 시에도 앱이 뜨도록 한다.
- 입력 검증은 빈 쿼리 가드 정도(`if not q.strip(): return []` — `search.py`).
- `events.py`는 `JSONResponse(..., headers={"Cache-Control": "no-store"})`로 캐시를 명시적으로 비활성화한다.

### 네이밍

- 함수/변수: `snake_case`. 모듈 전역 상수: `UPPER_SNAKE_CASE` (`URLS`, `BATCH_NODE`, `NEO4J_URI`).
- 라우트 핸들러명은 동작을 서술: `get_node`, `get_node_places`, `get_node_neighbors_grouped`, `search`.
- 응답 JSON 키는 `camelCase`(`nameKo`, `nameKoMissing`, `startDate`, `sortKey`, `isPrimary`) — 프론트엔드 소비를 전제로 한다. 내부 Neo4j 프로퍼티도 `camelCase`(`theographic_id`만 snake).

---

## 3. 프론트엔드 컨벤션 (React / Vite)

### 프로젝트 설정

- ESM(`"type": "module"`), JSX, **TypeScript 미사용** — 순수 `.jsx`.
- 빌드/실행: Vite. 스크립트는 `dev`/`build`/`lint`/`preview`만 (`frontend/package.json`). **test 스크립트 없음.**
- 린트: ESLint flat config (`frontend/eslint.config.js`) — `@eslint/js` recommended + `react-hooks` + `react-refresh`. `dist`는 무시. 별도 Prettier 설정은 없다.
- 진입점: `main.jsx`가 `<StrictMode>`로 `<App />`을 마운트 (`frontend/src/main.jsx`).

### 코드 스타일

- 세미콜론을 쓰지 않는다 (no-semicolon 스타일). 작은따옴표 문자열, 2-space 들여쓰기.
- 함수 컴포넌트만 사용. 선언 방식이 혼재한다: `function App()` (`App.jsx`, `SidePanel.jsx`, `TimelineView.jsx`) vs `export default function MapView()` (`MapView.jsx`, `GraphView.jsx`). 둘 다 허용되는 패턴.
- 파일당 한 컴포넌트, 파일명 = 컴포넌트명(`PascalCase.jsx`). 모두 `frontend/src/` 평면 구조(하위 폴더 분리 없음).
- `export default <Component>`로 내보낸다.

### 컴포넌트 구조 패턴

각 뷰 컴포넌트는 동일한 골격을 따른다:

1. 파일 상단에 import → 모듈 상수.
2. `const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'` — **모든 데이터 컴포넌트가 이 한 줄을 각자 중복 선언한다** (공유 모듈 없음). `App.jsx`만 변수명이 `API_BASE`.
3. 한↔영 라벨 매핑 상수 객체(`REL_KO`, `TYPE_COLOR`, `LABEL_TYPES` 등).
4. 순수 변환 헬퍼 함수(`placesToGeoJSON`, `parseYear`).
5. 컴포넌트 본체: `useState` 선언 → `useEffect`로 데이터 패칭/사이드이펙트 → JSX 반환.

### 상태 / 데이터 흐름

- 최상위 상태는 `App.jsx`가 `useState`로 보유: `selectedNode`, `activeView`, `searchQuery`, `searchResults`, `showDropdown`. **상태관리 라이브러리 없음.**
- 자식 뷰에는 `selectedNode`(값)와 `onSelectNode`(세터)를 props로 내려보내는 **lift-state-up** 패턴. 선택 노드가 세 뷰(Map/Timeline/Graph)와 SidePanel을 동기화하는 단일 소스다.
- 데이터 패칭은 컴포넌트 내부 `fetch` + `useEffect`. 라이브러리(axios/react-query) 없음.
- 패칭 패턴 두 가지가 공존:
  - `.then()` 체인 (`SidePanel.jsx`, `TimelineView.jsx`, `GraphView.jsx`)
  - `async/await` (`App.jsx`의 `handleSearch`)
- `useEffect` 클린업으로 리소스/요청을 정리한다:
  - MapView: `AbortController`로 fetch 취소, 언마운트 시 `map.remove()`/popup 정리 (`MapView.jsx`).
  - GraphView: `cy.destroy()`로 cytoscape 인스턴스 정리 (`GraphView.jsx`).
- 명령형 라이브러리(maplibre-gl, cytoscape)는 `useRef`로 인스턴스를 보관하고 `useEffect` 안에서 직접 조작한다. `mapRef`, `cyRef`, `popupRef`, `containerRef` 등.

### 스타일링

- **인라인 `style={{...}}` 객체가 기본 스타일링 방식.** CSS 클래스/모듈은 실질적으로 쓰지 않는다.
- `frontend/src/index.css`, `App.css`는 대부분 Vite 스캐폴드 잔여물(앱 컴포넌트에서 미사용으로 보임).
- 색상은 컴포넌트 안에 하드코딩된 헥스/rgba 리터럴. 반복되는 도메인 색상(노드 타입별)만 `TYPE_COLOR` 상수로 추출 (`GraphView.jsx`).
- 레이아웃은 절대 위치(`position: absolute`/`inset: 0`) + z-index 기반 오버레이. 네비 높이 등 매직넘버는 지역 상수로 (`const NAV_H = 48`).
- 아이콘은 `lucide-react`.

### 에러 처리

- fetch 실패는 대체로 `.catch(() => {})`로 조용히 무시(MapView, TimelineView, GraphView). 사용자에게 노출하지 않는 best-effort 패칭.
- 예외적으로 `SidePanel.jsx`만 `loading`/`error` 상태를 두고 `오류: {error}` / `로딩 중...`을 렌더한다.

---

## 4. 운영 / 배포 컨벤션

- 컨테이너 오케스트레이션: `docker-compose.yml` — `neo4j`(5), `api`(FastAPI), `nginx`(정적 + 리버스 프록시) 3-서비스.
- 환경변수는 `.env`(gitignore됨)에 두고 `.env.example`을 템플릿으로 제공. `NEO4J_AUTH=neo4j/<password>` 포맷.
- 배포는 `deploy.sh` 셸 스크립트: 프론트 빌드 → API 이미지 빌드 → 컨테이너 재시작 → 한글 이름 주입(최대 15회 재시도). lock 파일(`/tmp/biblemap-deploy.lock`)로 동시 실행 방지, 한국어 로그.
- CI: `.github/workflows/deploy.yml` — `main` push 시 self-hosted 러너에서 `git reset --hard origin/main` 후 `deploy.sh` 실행. **빌드/테스트 게이트 없이 곧장 배포만 한다.**

---

## 5. 프로젝트 전반 원칙 (`CLAUDE.md`)

루트 `CLAUDE.md`에 명시된 행동 가이드라인이 코드 스타일을 지배한다:

- **Simplicity First** — 요청된 것 이상의 기능/추상화/설정 금지. 단일 사용처 코드에 추상화 금지.
- **Surgical Changes** — 인접 코드 임의 개선/리팩터/포맷팅 금지, 기존 스타일 준수.
- **Think Before Coding** — 가정은 명시, 불확실하면 질문.

실제 코드도 이 원칙과 일치한다: 공유 유틸 모듈 없이 의도적으로 작은 중복(API_URL 선언, 폴백 로직)을 허용하고, 방어적 에러 처리를 최소화한다.
