---
last_mapped_commit: 4ed4d876d7fa3b06a8eb1647b5b50ed73f906b25
mapped: 2026-06-19
---

# 코드 컨벤션

## 코드 스타일 및 린팅

### 프론트엔드 (JavaScript/JSX)

린트 설정 파일: `frontend/eslint.config.js`

- ESLint v10 flat config 형식 사용
- `@eslint/js` recommended 규칙 적용
- `eslint-plugin-react-hooks` (v7) flat 권장 규칙 적용
- `eslint-plugin-react-refresh` Vite 프리셋 적용
- 대상 파일: `**/*.{js,jsx}`
- 빌드 결과물(`dist`) 는 린트 대상에서 제외
- 별도 Prettier 설정 없음 — 포맷터 미사용

린트 실행: `cd frontend && npm run lint`

### 백엔드 (Python)

- 포맷터·린터 설정 파일 없음 (`pyproject.toml`, `setup.cfg`, `.flake8` 부재)
- 코드 내 스타일은 PEP 8 준수를 암묵적으로 따름
- 타입 어노테이션 미사용 (FastAPI 라우트 매개변수에 기본 타입 힌트만 사용)

---

## 네이밍 컨벤션

### 프론트엔드

| 대상 | 규칙 | 예시 |
|---|---|---|
| 컴포넌트 파일 | PascalCase `.jsx` | `MapView.jsx`, `SidePanel.jsx`, `VerseLangTabs.jsx` |
| 유틸리티/모듈 파일 | camelCase `.js` | `api.js`, `theme.js`, `convexHull.js` |
| React 컴포넌트 함수 | PascalCase | `function App()`, `function VerseLangTabs()` |
| 일반 함수 | camelCase | `handleTabClick`, `onSearchInput`, `selectNode` |
| 상수 (파일·모듈 스코프) | UPPER_SNAKE_CASE | `TABS`, `MOBILE_QUERY`, `SHEET_VH`, `NAV_H`, `SEARCH_LIMIT` |
| 상태 변수 | camelCase | `selectedNode`, `searchQuery`, `isMobile` |
| ref 변수 | camelCase + `Ref` 접미사 | `selectedNodeRef`, `searchBoxRef`, `resultRefs` |
| 이벤트 핸들러 prop | `on` 접두사 | `onSelectNode`, `onBack`, `onNodeLoaded` |
| 이벤트 핸들러 함수 | `handle` 접두사 | `handleTabClick`, `handleSelectResult`, `handleSearchKeyDown` |

### 백엔드

| 대상 | 규칙 | 예시 |
|---|---|---|
| 모듈 파일 | snake_case `.py` | `events.py`, `nodes.py`, `books.py` |
| 함수 | snake_case | `get_events`, `get_person_event_ids`, `get_driver` |
| 내부(private) 함수 | `_` 접두사 + snake_case | `_load_event_verses`, `_compute_events`, `_load_approx_book_index` |
| 상수 | UPPER_SNAKE_CASE | `SEARCH_LIMIT`, `MAX_NEIGHBORS_PER_TYPE`, `NODE_NEIGHBOR_LIMIT` |
| 모듈 전역 변수 | `_` 접두사 | `_driver`, `_EVENT_VERSES_CANDIDATES`, `_BOOK_EVENTS_CANDIDATES` |

---

## import 순서

### 프론트엔드

고정된 eslint-import 규칙은 없으나 관찰된 패턴:

1. React 코어 훅 (`import { useState, useEffect, ... } from 'react'`)
2. 외부 라이브러리 아이콘 등 (`import { Map, Clock } from 'lucide-react'`)
3. 내부 컴포넌트 (`import MapView from './MapView'`)
4. 내부 유틸/상수 (`import { TYPE_ORDER, typeColor } from './theme'`)
5. 내부 API 모듈 (`import { apiGet } from './api'`)

예시: `frontend/src/App.jsx` 상단 6행

### 백엔드

관찰된 패턴:

1. 표준 라이브러리 (`import os`, `import json`, `import functools`)
2. 서드파티 (`from fastapi import ...`)
3. 내부 모듈 (`from ..db import get_driver`)

예시: `backend/app/routes/events.py` 상단 4행

---

## 에러 핸들링 패턴

### 프론트엔드

- **fetch 에러**: `apiGet` (`frontend/src/api.js`) 에서 `res.ok` 가 아니면 `status` 프로퍼티를 가진 `Error` 를 throw
- **AbortError 구분**: `e.name === 'AbortError'` 조건으로 경쟁 요청 취소를 무시 (`frontend/src/App.jsx`)
- **UI 에러 상태**: `searchError` 같은 별도 boolean 상태로 관리하고 조건부 렌더링으로 표시
- **디바운스 + AbortController**: 실시간 검색에서 이전 요청은 `ctrl.abort()` 로 취소 (`frontend/src/App.jsx`)

### 백엔드

- **404**: `fastapi.HTTPException(status_code=404)` 사용 (`backend/app/routes/nodes.py`)
- **스타트업 에러**: `lifespan` 내 인덱스 생성 실패는 `logging.exception` 후 계속 진행 — 앱을 멈추지 않음 (`backend/app/main.py`)
- **파일 로드 실패**: 후보 경로를 순서대로 시도하고 모두 실패 시 빈 dict/list 폴백 (`backend/app/routes/events.py` — `_load_event_verses`)
- **Neo4j 비밀번호 미설정**: `RuntimeError` raise (`backend/app/db.py`)

---

## 상태 관리 패턴

프론트엔드에 외부 상태 라이브러리 없음. React 내장 훅만 사용.

- **전역 공유 상태**: 최상위 `App.jsx` 에서 `useState` 로 선언하고 props로 하위 전달
  - 예: `verseLang` / `setVerseLang` 을 `TimelineView`, `SidePanel`, `VerseLangTabs` 가 공유
- **파생 값**: `useMemo` 없이 렌더 중 직접 계산 (예: `typeCounts`, `filteredResults`)
- **안정화된 콜백**: `useCallback([], [])` — 의존성 없는 빈 배열로 참조 고정. 최신 상태는 `useRef` 로 읽음 (`selectedNodeRef`)
- **사이드이펙트 분리**: 각 관심사당 별도 `useEffect` (미디어쿼리, 검색 디바운스, 드롭다운 바깥클릭, 스크롤 등)
- **히스토리 스택**: 배열 `useState` 로 뒤로가기 구현 (`history` 상태, `App.jsx`)

---

## 주석 컨벤션

### 프론트엔드

- 파일 최상단에 파일 목적을 짧게 설명하는 한 줄 주석 (`// 공유 API 클라이언트 —`)
- 상수 정의 위에 의도·배경을 설명하는 인라인 주석 (예: `MOBILE_QUERY`, `SHEET_VH` 위의 주석)
- JSX 블록 앞에 `{/* 섹션명 */}` 형식의 블록 주석 (예: `{/* 내비게이션 바 */}`, `{/* 타입 필터 칩 */}`)
- 비직관적 결정(버그 회피 이유 등)은 코드 바로 위에 한 문장으로 설명

### 백엔드

- 함수 docstring: 한국어로 기능과 반환 형식 설명 (`backend/app/routes/events.py`)
- 모듈 전역 변수 위에 역할 설명 한 줄 주석
- Cypher 쿼리 블록 자체는 주석 없음 — 함수 docstring 으로 의도 설명

---

## 공유 유틸리티 패턴

- **타입 팔레트**: `frontend/src/theme.js` — `TYPE_COLOR`, `TYPE_KO`, `TYPE_ORDER`, `typeColor()`, `typeKo()`, `SELECT_HL` 을 모든 뷰가 import
- **API 클라이언트**: `frontend/src/api.js` — `apiGet(path, { signal })` 단일 헬퍼로 모든 fetch 통일
- **Neo4j 드라이버 싱글톤**: `backend/app/db.py` — `get_driver()` 모듈 전역 `_driver` lazy init
- **캐싱**: `@functools.lru_cache(maxsize=1)` 로 무거운 연산(Neo4j + JSON 파일 로드)을 프로세스 수명 동안 캐시 (`backend/app/routes/events.py`)
