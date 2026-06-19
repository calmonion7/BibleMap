---
last_mapped_commit: 06b4012804c00a45ea7dfda9761d014ac91b11fb
mapped: 2026-06-20
---

# CONVENTIONS.md

## 네이밍 규칙

### 프론트엔드 (JavaScript/JSX)
- React 컴포넌트 파일: PascalCase (`SidePanel.jsx`, `MapView.jsx`, `BibleOverviewView.jsx`)
- 비컴포넌트 JS 파일: camelCase (`api.js`, `theme.js`, `convexHull.js`)
- 상수: SCREAMING_SNAKE_CASE (`MOBILE_QUERY`, `SHEET_VH`, `SELECT_HL`)
- Props 이름: camelCase (`onSelectNode`, `nodeId`, `verseLang`, `setVerseLang`)
- API 응답 필드: camelCase (`nameKo`, `bookOrder`, `sortKey`, `yearApprox`)

### 백엔드 (Python)
- 라우트 파일: 리소스명 snake_case (`nodes.py`, `events.py`, `books.py`, `search.py`)
- 모듈 내 비공개 헬퍼: 선행 언더스코어 + snake_case (`_load_approx`, `_compute_events`, `_driver`)
- 상수: SCREAMING_SNAKE_CASE (`MAX_NEIGHBORS_PER_TYPE`, `NODE_NEIGHBOR_LIMIT`)

## 파일 조직

### 프론트엔드
- 모든 React 소스: `/frontend/src/` 하위 flat 구조 — `components/`, `hooks/`, `utils/` 등 서브디렉터리 없음
- 진입점: `/frontend/src/main.jsx`
- 전역 상수·컬러: `/frontend/src/theme.js`
- fetch 헬퍼: `/frontend/src/api.js`
- 순수 알고리즘 유틸: `/frontend/src/convexHull.js`

### 백엔드
- FastAPI 앱·lifespan: `/backend/app/main.py`
- Neo4j 드라이버 싱글턴: `/backend/app/db.py`
- 라우트: `/backend/app/routes/` (리소스별 1파일)
- 데이터 로딩·생성 일회성 스크립트: `/backend/scripts/` (라우트가 아님)

## Import 패턴

### 프론트엔드
```js
// React 훅: 이름 있는 임포트, namespace 아님
import { useState, useEffect, useCallback, useRef } from 'react'
// 아이콘: 이름 있는 임포트
import { Map, Clock, Search, X, BookOpen } from 'lucide-react'
// 컴포넌트: 기본 임포트
import MapView from './MapView'
// 내부 모듈: 이름 있는 임포트
import { TYPE_ORDER, typeColor, typeKo, SELECT_HL } from './theme'
import { apiGet } from './api'
```

### 백엔드
```python
# 표준 라이브러리 여러 개: 한 줄에 나열
import functools, json, os
# FastAPI: 이름 있는 임포트
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
# 내부 모듈: 상대 임포트
from ..db import get_driver
```

## React 컴포넌트 패턴

- **함수형 컴포넌트만** 사용 — 클래스 컴포넌트 없음
- **기본 export**는 파일 맨 아래: `export default App`
- **밀접하게 결합된 서브컴포넌트**는 같은 파일 안에 named function으로 정의 (`SectionHeader` in `SidePanel.jsx`, `BookCard` in `BibleOverviewView.jsx`)
- **Props 구조 분해**는 시그니처에서 직접, 기본값도 인라인:
  ```js
  function SidePanel({ nodeId, onSelectNode = () => {}, canGoBack = false, verseLang, setVerseLang })
  ```
- `defaultProps` 사용 안 함
- **모든 스타일은 인라인 `style` 객체** — CSS 클래스, CSS 모듈, Tailwind 없음
- **`useRef`**: DOM ref 및 재렌더 없이 값을 유지해야 할 때 (`expandedPlaceRef`, `openEventRef`, `selectedNodeRef`)
- **`useCallback`**: 클로저가 ref를 읽어 안정적인 `[]` deps로 자식 재렌더 방지 (`selectNode`)
- **`useMemo`**: 대형 배열 의존 파생 데이터 (`groups`, `visibleGroups`)
- **취소 가능한 fetch**: AbortController + setTimeout 패턴:
  ```js
  const ctrl = new AbortController()
  const timer = setTimeout(async () => { ... }, 250)
  return () => { clearTimeout(timer); ctrl.abort() }
  ```
- **오래된 응답 가드**: boolean flag 패턴:
  ```js
  let cancelled = false
  apiGet('/node/' + nodeId).then(data => { if (!cancelled) setState(...) })
  return () => { cancelled = true }
  ```
- **로딩/에러 상태 shape**: `{ id, node, error }` 단일 객체 — 별도 `loading` boolean 없음, `loading`은 `state.id !== nodeId`로 도출
- **접힘/펼침 상태**: 문자열 키 객체 `collapsed[sectionKey] === false`이 열림(truthy/falsy 반전 패턴)
- **상태 끌어올리기**: `verseLang`/`setVerseLang`는 `App.jsx`가 소유, props로 전달
- Redux, Context API, 외부 상태관리 라이브러리 없음

## Python/FastAPI 규칙

- **파일당 `APIRouter` 1개**, `main.py`에서 `app.include_router()`로 등록
- **`functools.lru_cache(maxsize=1)`**: 정적 JSON 데이터 및 Neo4j 계산 결과 인메모리 캐싱:
  ```python
  @functools.lru_cache(maxsize=1)
  def _compute_events(): ...
  ```
- **Neo4j 드라이버 싱글턴**: 모듈 레벨 `_driver = None`, `get_driver()`에서 lazy init
- **`driver.session()` context manager**: 요청마다 새 세션, 요청 간 세션 재사용 없음
- **라우트 함수 반환값**: 기본 dict (FastAPI 자동 직렬화), 커스텀 헤더가 필요할 때만 `JSONResponse(content=..., headers={...})`
- **에러 처리**: 노드 미존재 시 `HTTPException(status_code=404)`만 사용; 다른 에러는 흡수 후 fallback 반환
- **`@asynccontextmanager` lifespan**: 시작 로직(Neo4j 인덱스 생성)에 사용, 광범위한 `except Exception` + `logging.exception`
- **타입 애너테이션**: 라우트 파라미터에만 제한적 사용 (`node_id: str`, `q: str = Query("")`); 요청/응답 body에 Pydantic 모델 없음
- **데이터 파일 경로**: 후보 목록 패턴:
  ```python
  _CANDIDATES = [
      os.path.join(os.environ.get("DATA_DIR", "/app/data"), "..."),
      os.path.join(_REPO_DATA_DIR, "..."),
  ]
  ```
- Python 3.12 (`/backend/Dockerfile`: `FROM python:3.12-slim`)
- 최소 핀된 의존성: `fastapi==0.136.3`, `neo4j==6.2.0`, `uvicorn==0.49.0`

## 인라인 코멘트 스타일

**모든 코멘트는 한국어로 작성.**

### 프론트엔드 (JS)
- 관련 블록 위에 단일 행 `//` 코멘트, 이유(why) 설명:
  ```js
  // 모바일(좁은 뷰포트) 분기 — ...
  // setState는 전부 setTimeout/async 콜백 안에서만(effect 동기 본문 setState 금지 — react-hooks v7)
  ```
- JSX 주요 섹션 앞: `{/* 헤더 */}`

### 백엔드 (Python)
- 블록 위 단일 행 `#` 코멘트:
  ```python
  # 역방향 맵 구성
  # 사건별 근거 구절 오버레이...
  ```
- 캐시된 헬퍼 함수에 docstring (라우트 핸들러가 아님):
  ```python
  def _load_event_verses():
      """사건별 구절 오버레이 JSON을 1회만 로드(캐시). DATA_DIR → 레포 상대경로 순으로..."""
  ```
- 라우트 핸들러에는 API 계약과 데이터 의미론 설명 docstring

## 에러 처리 패턴

### 프론트엔드
- **이진 에러 상태**: `const [error, setError] = useState(false)` — 에러 메시지 미저장
- 에러 시: JSX에 한국어 에러 문자열 직접 렌더링
- `AbortError`는 명시적으로 감지 후 무시: `if (e.name === 'AbortError') return`
- `apiGet`은 `.status` 속성이 붙은 `Error` 객체를 throw; catch 지점에서 `e?.status ?? String(e)` 사용

### 백엔드
- `HTTPException(status_code=404, detail="Node not found")`: 미존재 노드에만 사용
- 데이터 파일 로딩: `except (FileNotFoundError, json.JSONDecodeError): continue` + fallback 빈 dict
- 시작 에러: `except Exception: logging.exception(...)` 후 실행 계속
- json 파싱 에러: bare `except Exception: clean_props["traits"] = []`
- 커스텀 예외 클래스 없음, 미들웨어 레벨 에러 처리 없음
