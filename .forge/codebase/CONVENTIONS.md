---
last_mapped_commit: 79f9d9df07c0d79f8fa07940e3f76c8d5424524b
mapped: 2026-06-28
---
# 코딩 컨벤션

**분석일:** 2026-06-28

두 언어 영역으로 나뉜다. 프론트엔드 `frontend/src/`(React 19 + Vite, JS/JSX, ESM)와 백엔드 `backend/app/`(FastAPI + Neo4j, Python 3.12). 데이터 적재·생성 스크립트는 `backend/scripts/`에 별도 규칙으로 모여 있다.

---

## 네이밍 패턴

### 파일

- **React 컴포넌트:** PascalCase `.jsx` — `MapView.jsx`, `SidePanel.jsx`, `PersonHub.jsx`, `JourneyList.jsx`, `TimelineView.jsx`, `BibleOverviewView.jsx`, `Spinner.jsx`, `VerseLangTabs.jsx`. 파일 1개 = 기본 export 컴포넌트 1개.
- **비컴포넌트 모듈(헬퍼·훅·상수):** camelCase 또는 소문자 `.js` — `api.js`, `theme.js`, `constants.js`, `mapGeo.js`, `mapLayers.js`, `mapRingController.js`, `useNodeSelection.js`.
- **커스텀 훅:** `use` 접두사 + camelCase 파일·함수 — `useNodeSelection.js`의 `export function useNodeSelection()`. 단, `PersonHub.jsx` 내부의 `useIsMobile`은 컴포넌트 파일에 동거하는 로컬 훅.
- **백엔드 라우트 모듈:** 소문자 단수/복수 `.py` — `backend/app/routes/nodes.py`, `events.py`, `persons.py`, `places.py`, `journey.py`, `books.py`, `search.py`. 라우터 1개 = 모듈 1개.
- **백엔드 스크립트:** `동사_명사.py` 스네이크 케이스 — `load_*`(Neo4j 적재), `generate_*`(LLM·데이터 산출), `inject_*`(노드 속성 주입), `enrich_*`(좌표 보강). 동사 접두사로 역할을 구분한다(`backend/scripts/`).

### 함수

- **JS:** camelCase. 컴포넌트는 PascalCase. 이벤트 핸들러는 `handle` 접두사(`handleSelectPerson`, `handleBackToHub`, `handleNodeLoaded` — `App.jsx`). 콜백 prop은 `on` 접두사(`onSelectNode`, `onStopSelect`, `onSelectPerson`).
- **Python:** snake_case. FastAPI 엔드포인트 함수는 `get_` 접두사가 관례(`get_node`, `get_person_journey`, `get_curated_persons` — `nodes.py`/`journey.py`/`persons.py`).
- **모듈 내부 전용 함수:** Python은 `_` 접두사 언더스코어 — `_resolve`, `_load`(`overlays.py`), `_build_list`(`persons.py`), `_build_id_to_slug`/`_load_events`/`_fetch_place_coords`(`journey.py`), `_compute_events`/`_load_approx_book_index`(`events.py`). JS는 헬퍼를 export하지 않는 함수로 둔다(`outwardLabel`/`compactSeqs`는 `mapGeo.js`에서 비-export).

### 변수·상수

- **모듈 상수:** JS·Python 공통 UPPER_SNAKE — `MOBILE_BREAKPOINT`/`SHEET_VH`(`constants.js`), `TYPE_COLOR`/`TYPE_KO`/`TYPE_ORDER`/`SELECT_HL`(`theme.js`), `MAX_NEIGHBORS_PER_TYPE`/`NODE_NEIGHBOR_LIMIT`(`nodes.py`), `SEARCH_LIMIT`(`search.py`), `EMPTY_GEOJSON`(`mapLayers.js`).
- **컴포넌트 로컬 색·테마 상수:** UPPER_SNAKE를 컴포넌트 파일 상단에 둔다 — `PERSON_BLUE`/`GOLD`/`GROUND`/`TEXT`/`CARD_BG`(`PersonHub.jsx`), `BOOK_COLOR`/`EVENT_COLOR`(`TimelineView.jsx`).
- **Python 모듈 캐시 매핑:** `_` 접두사 + 타입힌트 부착 dict — `_ERA: dict[str, str]`, `_NAME_KO: dict[str, str]`, `_ERA_ORDER`(`persons.py`/`places.py`). 동일 상수가 `persons.py`·`places.py`에 의도적으로 중복 선언돼 있다(주석: "단방향 참조를 피하기 위해 여기서 재선언").

### 타입

TypeScript 미사용(JS/JSX만). 응답 객체 형태는 JSDoc 또는 주석으로 계약을 문서화한다(`PersonHub.jsx` 상단 "Props 계약", `journey.py` docstring의 "stops 각 항목").

---

## 코드 스타일

### 포매팅

- **세미콜론 없음(JS):** 프론트엔드는 세미콜론을 생략하는 스타일. 단, 한 줄에 여러 문장을 압축할 때만 명시적 `;`를 쓴다(`api.js:9` `const err = new Error(...); err.status = ...; throw err`).
- **들여쓰기:** JS 2칸, Python 4칸(PEP8).
- **따옴표:** JS 작은따옴표 `'...'`. Python 큰따옴표 `"..."` 우세(Cypher 쿼리 등).
- **Prettier/Black 미설정:** 포매터 설정 파일 없음. 스타일은 수동 일관성으로 유지.
- **압축 한 줄 함수:** 짧은 헬퍼는 한 줄로 — `mapGeo.js:82` `export function easeOutCubic(t) { return 1 - Math.pow(1 - t, 3) }`, `useNodeSelection.js`의 중첩 setter들.

### 린트

- **ESLint flat config:** `frontend/eslint.config.js`. `@eslint/js` recommended + `eslint-plugin-react-hooks`(flat recommended) + `eslint-plugin-react-refresh`(vite). `dist`는 `globalIgnores`로 제외. 실행: `cd frontend && npm run lint`(= `eslint .`).
- **react-hooks 규칙을 코드가 적극적으로 준수:** 주석에서 반복적으로 "set-state-in-effect 준수", "v7 OK"를 언급한다. effect 본문에서 동기 setState를 피하고, 필요하면 `Promise.resolve().then(() => setState(...))`로 비동기 콜백 안으로 밀어 넣는다(`App.jsx:48`). 비동기 fetch `.then` 콜백 내 setState는 허용으로 본다(`App.jsx:52` "async 콜백 — v7 OK").
- **Python 린터 미설정:** flake8/ruff/mypy 설정 파일 없음.

---

## 임포트 구성

### 프론트엔드 순서(관찰된 관례)

1. React 훅 — `import { useState, useEffect, useRef, useCallback } from 'react'`
2. 외부 라이브러리 — `maplibre-gl`, `lucide-react`(+ `maplibre-gl/dist/maplibre-gl.css`)
3. 로컬 컴포넌트 — `./MapView`, `./SidePanel` 등(확장자 생략 또는 `.jsx` 명시 혼용)
4. 로컬 헬퍼·상수·훅 — `./api`, `./theme`, `./constants`, `./mapGeo`, `./useNodeSelection`

경로 별칭(`@/`) 미사용 — 모두 상대경로 `./`. Vite 기본.

### 백엔드 순서

1. 표준 라이브러리 — `import json`, `import functools`, `import os`, `import logging`
2. 서드파티 — `from fastapi import APIRouter, HTTPException, Query`, `from fastapi.responses import JSONResponse`, `from neo4j import GraphDatabase`
3. 로컬 상대 임포트 — `from ..db import get_driver`, `from ..overlays import _resolve`, `from .persons import _ERA, _NAME_KO`

라우트 간 상수 공유는 상대 임포트(`journey.py`가 `from .persons import _ERA`)로 하되, `places.py`는 의도적으로 재선언으로 결합을 피했다.

---

## 에러 처리

### 프론트엔드

- **공유 fetch 헬퍼:** 모든 GET은 `api.js`의 `apiGet(path, { signal })`을 거친다. 비-OK 응답이면 `status` 필드를 단 `Error`를 throw, AbortError는 fetch에서 그대로 전파.
- **AbortError 구분이 표준:** fetch effect의 `.catch`에서 거의 항상 `if (e?.name !== 'AbortError')`로 취소를 정상 흐름과 분리한다(`App.jsx:53`, `MapView.jsx:144`, `mapRingController.js:114`). cleanup에서 `AbortController.abort()` 호출.
- **stale 응답 가드 2종:**
  - `cancelled` 로컬 플래그 + cleanup(`SidePanel.jsx:62-69`, `PersonHub.jsx:165-178`).
  - id-스탬프 상태 객체 — `{ id, node, error }`를 통째로 저장하고 `state.id === nodeId`일 때만 표시(`SidePanel.jsx:48,86`). 응답 순서 뒤바뀜은 `openEventRef`/`placeOpenEventRef` 같은 ref와 대조해 막는다(`SidePanel.jsx:144`, `TimelineView.jsx:41`).
- **사용자 노출 에러는 항상 한글:** "불러오지 못했습니다", "장소를 불러오지 못했습니다", "이 항목은 지도에 표시할 위치 정보가 없습니다" 등. 빨강 토스트 `rgba(220,53,69,...)`(`MapView.jsx`).

### 백엔드

- **404는 `HTTPException(status_code=404, detail=...)`:** 노드 미존재 시(`nodes.py:30,156`). detail은 영어("Node not found").
- **빈 응답 vs 예외:** 큐레이션 대상이 아니면 404 대신 빈 배열을 반환하는 게 관례 — `journey.py`(큐레이션 13인 아니면 `stops=[]`), `search.py`(빈 쿼리면 `[]`).
- **설정 누락은 즉시 `RuntimeError`(한글):** `db.py:13`, `inject_ko_names.py:14` — `NEO4J_PASSWORD` 없으면 시작 시 중단.
- **앱 시작 인덱스 생성은 best-effort:** `main.py`의 `lifespan`에서 인덱스 생성 실패를 `logging.exception(...)`으로 삼키고 계속 진행한다(한글 로그 메시지).
- **방어적 파싱:** 좌표 변환 실패는 `try/except (TypeError, ValueError)`로 해당 레코드를 `continue` 스킵(`nodes.py:95-99`). JSON 파싱 실패는 `except Exception` 후 빈 리스트(`nodes.py:243`), `except json.JSONDecodeError`로 빈 dict(`overlays.py:26`).

---

## 로깅

- **백엔드:** 표준 `logging` 모듈. 앱 코드에서는 `main.py`의 `logging.exception(...)` 1곳만 사용. 스크립트는 `print(...)`로 진행상황·집계 출력(`inject_ko_names.py:53-57`).
- **프론트엔드:** `console.*` 직접 호출 없음(소스 grep 0건). 오류는 UI 상태(`error`/`noLocation`)로 표면화한다.
- **배포 스크립트:** `deploy.sh`의 `log()` 함수가 타임스탬프 prefix로 `tee -a $LOG`. 메시지 한글, 단계는 `[1/4]` 형식.

---

## 주석

- **언어: 한글.** 거의 모든 인라인 주석·docstring이 한글이다. 사용자 메모리 규칙("실행내역 한글로")과 일치.
- **"왜"를 적는다(설계 결정·버그 회피):** 주석이 단순 설명이 아니라 결정의 근거·과거 버그·튜닝값 출처를 담는다. 예:
  - `useNodeSelection.js:31-32` — `useCallback([])`로 참조 안정화한 이유(MapView effect 재실행 → fetch abort 버그 방지).
  - `mapLayers.js:275-276` — `clusterRadius: 18`/`clusterMinPoints: 4`의 근거를 task 번호(`task-76`, `task-84`)와 함께.
  - `App.jsx:77-79` — 인라인 화살표 대신 `useCallback`을 쓰는 이유.
  - ADR 참조 — `SidePanel.jsx:109`, `TimelineView.jsx:37`이 "ADR-0003"을 인용(빌드타임 미리저장 절 본문).
- **모듈 헤더 docstring:** 백엔드 라우트는 모듈·함수 상단에 한글 docstring으로 응답 형태와 계약을 명시(`journey.py`, `persons.py`, `places.py`, `events.py`).
- **JSDoc:** 드물게 사용. `PersonHub.jsx:148-157`이 `/** ... */`로 Props 계약·데이터 출처를 문서화한 유일에 가까운 예.

---

## 함수·컴포넌트 설계

- **단일 export 기본:** 컴포넌트 파일은 `export default`로 하나. `App.jsx`는 함수 선언 후 마지막에 `export default App`, 다른 컴포넌트는 선언부에서 바로 `export default function ...`.
- **Props 구조분해 + 기본값:** `function SidePanel({ nodeId, onSelectNode = () => {}, onBack = () => {}, canGoBack = false, ... })` — 콜백 prop에 no-op 기본값을 주는 패턴(`SidePanel.jsx:45`).
- **헬퍼는 순수 함수로 분리:** 지오메트리·GeoJSON 변환은 `mapGeo.js`에 순수 함수로(`placesToGeoJSON`, `buildJourneyLineGeoJSON`, `journeyStopGroups` 등) 모아 컴포넌트에서 호출. 부수효과(애니메이션·소스 setData)는 `mapRingController.js`의 클로저 컨트롤러로 캡슐화한다(가변 상태를 클로저에 가두고 `{ collapseRing, collapseSpider, expandPlace, spiderifyPlaces, destroy }` 반환).
- **인라인 스타일이 표준:** CSS 모듈·styled-components·Tailwind 미사용. 모든 스타일은 JSX `style={{ ... }}` 객체. 전역 스타일은 `index.css`만(+ `Spinner.jsx`가 `<style>{keyframes}</style>`로 keyframe 주입).
- **상태 끌어올리기:** 교차 뷰 상태(`selectedNode`, `verseLang`, `journeyStops`, `activeStopIdx`)는 `App.jsx`에서 보유하고 props로 내린다. 선택 로직은 `useNodeSelection` 훅으로 추출.
- **Python 캐싱 규약:** 파일·Neo4j 결과는 `@functools.lru_cache(maxsize=1)`(전역 1회) 또는 `maxsize=None`(키별, `places.py:_place_to_persons`)로 메모리 보관. 주석에 "앱 재시작 전까지 결과를 메모리에 보관" 명시(`events.py:54`).
- **모듈 싱글톤:** Neo4j 드라이버는 `db.py`의 모듈 전역 `_driver` + lazy `get_driver()`로 1개만 유지.

---

## 모듈·데이터 설계

- **데이터 파일 해석 단일 진입점:** 오버레이·정적 JSON은 `overlays.py`의 `_resolve(subpath)`를 통해 찾는다 — `$DATA_DIR`(컨테이너 `/app/data`) → repo `data/` 순으로 폴백. 이 함수를 다른 라우트(`persons.py`, `journey.py`, `places.py`)가 임포트해 재사용한다.
- **theographic_id가 노드 식별 표준 키:** 모든 Cypher가 `{theographic_id: $id}`로 매칭. 응답 객체의 `id` 필드 = `theographic_id`.
- **nameKo 폴백 사다리:** 한글 이름 부재 시 영어 `name`(또는 `title`)으로 폴백하고 `nameKoMissing: bool` 플래그를 함께 내린다(`nodes.py:137`, `search.py:40`). 프론트는 `nameKoMissing`이면 "(미번역)" 라벨을 붙인다(`SidePanel.jsx:103,585`).
- **응답에 캐시 헤더:** 정적·결정적 엔드포인트는 `JSONResponse(content=..., headers={"Cache-Control": "max-age=300"})` 패턴. 값은 엔드포인트별로 다름(`persons/curated`는 3600, `books-overview`는 `no-store`).
- **배럴 파일 없음:** `index.js` re-export 패턴 미사용. 직접 경로 임포트.

---

*컨벤션 분석: 2026-06-28*
