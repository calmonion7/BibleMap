---
last_mapped_commit: 815433397ff74c133b2de5d1cafe1c8764b5303c
mapped: 2026-07-04
---
# 아키텍처

**분석일:** 2026-07-04

## 시스템 개요

```text
┌─────────────────────────────────────────────────────────────┐
│                    브라우저 (React SPA)                       │
├──────────────────┬──────────────────┬───────────────────────┤
│   PersonHub      │   MapView /      │   BibleOverviewView   │
│  `frontend/src/  │   TimelineView   │   / SidePanel         │
│   PersonHub.jsx` │  `MapView.jsx`   │  `SidePanel.jsx`      │
└────────┬─────────┴────────┬─────────┴──────────┬────────────┘
         │  apiGet() (fetch) │                    │
         ▼                   ▼                    ▼
┌─────────────────────────────────────────────────────────────┐
│                nginx (리버스 프록시 + 정적파일)                │
│  `nginx/nginx.conf`  — /api/ → api:8000, / → dist/index.html │
└──────────────────────────────┬──────────────────────────────┘
         │                      │
         ▼ (정적 dist)          ▼ (/api/*)
┌───────────────────┐  ┌───────────────────────────────────────┐
│  frontend/dist/   │  │        FastAPI (api:8000)              │
│  (Vite 빌드 산출)  │  │  `backend/app/main.py` + routes/*.py  │
└───────────────────┘  └──────────────────┬────────────────────┘
                                          │ Neo4j Bolt 드라이버
                            ┌─────────────┴──────────────┐
                            ▼                             ▼
                 ┌────────────────────┐      ┌──────────────────────┐
                 │  Neo4j (그래프 DB)  │      │  data/ JSON 오버레이  │
                 │  bolt://neo4j:7687 │      │  `backend/app/        │
                 │  Person/Place/     │      │   overlays.py`가 로드 │
                 │  Event/Book/...     │      │  (파일 직접 읽기)     │
                 └────────────────────┘      └──────────────────────┘
```

## 컴포넌트 책임

| 컴포넌트 | 책임 | 파일 |
|-----------|----------------|------|
| React SPA | 단일 페이지 앱, 3단계(hub/explore/overview) 상태 머신 | `frontend/src/App.jsx` |
| API 클라이언트 | 단일 base URL + GET 헬퍼(`apiGet`), AbortError 전파 | `frontend/src/api.js` |
| 노드 선택 훅 | 선택 노드 id·메타·히스토리·인물 사건 id 집합 상태 소유 | `frontend/src/useNodeSelection.js` |
| FastAPI 앱 | 라우터 등록, 기동 시 Neo4j 인덱스 생성(lifespan) | `backend/app/main.py` |
| Neo4j 드라이버 | 프로세스 전역 싱글턴 드라이버(`get_driver`) | `backend/app/db.py` |
| JSON 오버레이 로더 | data/*.json을 lru_cache로 로드(book_events, event_verses) | `backend/app/overlays.py` |
| 시드 스크립트 | Theographic 원본 → Neo4j 적재, 한글·좌표·문맥 주입 | `backend/scripts/*.py` |

## 패턴 개요

**전체:** 3계층 웹앱 — React SPA(프론트) ↔ FastAPI(백엔드) ↔ Neo4j 그래프 DB. nginx가 정적 서빙 + `/api` 리버스 프록시를 담당하는 docker-compose 단일 스택.

**핵심 특징:**
- 백엔드는 라우터별 파일로 분리된 얇은 REST 계층. 모든 엔드포인트가 `GET`만 노출(CORS `allow_methods=["GET"]`).
- 데이터는 **두 출처의 병합**: Neo4j 그래프(정본 엔티티·관계) + `data/*.json` 오버레이(한글 이름, 좌표, 큐레이션 여정, 근거 구절). 오버레이는 Neo4j를 거치지 않고 파일에서 직접 읽는 경우가 많다(`persons.py`, `journey.py`, `places.py`).
- 계산 비용이 큰 조회는 `functools.lru_cache`로 프로세스 메모리에 1회 캐시(`events.py`, `persons.py`, `overlays.py`). 앱 재시작 전까지 유지.
- 프론트는 라우팅 라이브러리 없이 `App.jsx`의 `activeStage`/`exploreView` 상태로 화면 전환(전체화면 뷰는 CSS `display` 토글로 언마운트 없이 상태 보존).

## 계층

**프론트엔드 (React SPA):**
- 목적: 사용자 인터랙션·지도·타임라인·상세 패널 렌더링
- 위치: `frontend/src/`
- 포함: 화면 컴포넌트(`*.jsx`), 순수 헬퍼 모듈(`*.js`)
- 의존: `apiGet`(`api.js`)로 백엔드 REST, `maplibre-gl`로 지도 렌더
- 사용처: 브라우저 (nginx가 `frontend/dist/` 정적 서빙)

**API (FastAPI):**
- 목적: REST 엔드포인트, Neo4j 조회 + JSON 오버레이 병합
- 위치: `backend/app/`
- 포함: `main.py`(앱), `db.py`(드라이버), `overlays.py`(파일 로더), `routes/*.py`(엔드포인트)
- 의존: Neo4j Bolt 드라이버, `data/` 볼륨(compose에서 `./data:/app/data` 마운트)
- 사용처: 프론트엔드 fetch, nginx 프록시(`/api/` → `api:8000/`)

**그래프 스토어 (Neo4j):**
- 목적: 성경 엔티티·관계 정본 저장
- 위치: `bolt://neo4j:7687` (compose 서비스 `neo4j`, 볼륨 `neo4j_data`)
- 노드 라벨: `Person`, `Place`, `Event`, `Book`, `PeopleGroup`
- 관계: `HAS_PARTICIPANT`, `OCCURS_AT`, `MEMBER_OF`, `CONTAINS_BOOK` 등(라우트 Cypher 참조)
- 시드: `backend/scripts/load_theographic.py`가 Theographic 원본을 적재, 이후 inject 스크립트가 한글·좌표·문맥을 병합

**데이터 오버레이 (JSON 파일):**
- 목적: Neo4j에 없는 큐레이션 데이터(한글 이름, 여정, 근거 구절, 좌표)
- 위치: `data/*/`
- 로더: `backend/app/overlays.py`의 `_resolve`/`_load`. `DATA_DIR`(기본 `/app/data`) → 리포 `data/` 순으로 탐색

## 데이터 흐름

### 주요 요청 경로 — 인물 여정 탐험

1. 초기 로드: `App.jsx`가 `GET /persons/curated`로 큐레이션 인물 id 집합을 받아 CTA 노출 판단 (`frontend/src/App.jsx:44`)
2. 허브에서 인물 카드 클릭 → `handleSelectPerson` → `activeStage='explore'`, `explorePersonId` 설정 (`frontend/src/App.jsx:86`)
3. `explorePersonId` 변경 effect가 `GET /person/{id}/journey` 호출 → `journeyStops` 상태에 저장 (`frontend/src/App.jsx:72`)
4. 백엔드 `journey.py`: `person_events/{slug}.json`을 sortKey순 정렬 후, `occursAt` place_id들의 좌표를 Neo4j 배치 조회(`_fetch_place_coords`)해 병합 (`backend/app/routes/journey.py:73`)
5. `journeyStops`가 `MapView`·`JourneyList`에 공유되어 지도 여정선·정차지·좌측 리스트로 렌더 (`frontend/src/App.jsx:280`, `:269`)

### 보조 흐름 — 노드 상세 패널

1. 지도/타임라인/개요에서 노드 클릭 → `selectNode(id)` (`frontend/src/useNodeSelection.js:33`)
2. `SidePanel`이 `GET /node/{id}` fetch → 노드 속성·이웃·이웃 총수 렌더 (`backend/app/routes/nodes.py:145`)
3. 로드 완료 시 `onNodeLoaded` 콜백 → `useNodeSelection`이 label이 Person이면 `GET /person/{id}/event-ids`로 타임라인 필터용 사건 id 집합 조회 (`frontend/src/useNodeSelection.js:21`)
4. Book 노드는 `/node/{id}`가 `topPersons`·`topEvents`를 추가 반환 (`backend/app/routes/nodes.py:200`)

**상태 관리:**
- 라우팅 라이브러리·전역 스토어 없음. `App.jsx`가 상위 상태(activeStage, exploreView, journeyStops, verseLang 등)를 소유하고 props drilling으로 전달.
- 노드 선택 관련 상태는 `useNodeSelection` 커스텀 훅에 캡슐화. `selectNode`는 `useCallback([])`로 참조 안정화해 하위 effect 재실행(fetch abort) 방지.

## 핵심 추상화

**apiGet (프론트 fetch 단일 진입점):**
- 목적: base URL 통일 + 비-OK 응답을 status를 담은 Error로 reject
- 예시: `frontend/src/api.js`
- 패턴: 모든 컴포넌트가 이 헬퍼만 사용. `VITE_API_URL`(빌드타임)로 프로덕션은 `/api` 프록시를 탐

**JSON 오버레이 (`_resolve`/`_load`):**
- 목적: Neo4j 외부의 큐레이션 데이터를 파일에서 읽기
- 예시: `backend/app/overlays.py`, `backend/app/routes/persons.py`(`_resolve` 재사용)
- 패턴: `DATA_DIR` → 리포 `data/` 순 경로 탐색. `lru_cache`로 1회 로드

**큐레이션 인물 매핑 (단일 출처):**
- 목적: slug ↔ 시대(era) ↔ 한글 이름 매핑을 한 곳에 고정
- 예시: `backend/app/routes/persons.py`의 `_ERA`, `_NAME_KO`, `_ERA_ORDER`
- 패턴: `journey.py`·`places.py`가 이 딕셔너리를 import 재사용해 드리프트 방지

## 진입점

**프론트엔드:**
- 위치: `frontend/src/main.jsx` → `createRoot(...).render(<App/>)`
- HTML 셸: `frontend/index.html`
- 트리거: 브라우저가 nginx `/` → `frontend/dist/index.html` 로드
- 책임: `App.jsx` 마운트(StrictMode)

**백엔드:**
- 위치: `backend/app/main.py`의 `app = FastAPI(lifespan=...)`
- 실행: `uvicorn app.main:app --host 0.0.0.0 --port 8000` (`backend/Dockerfile` CMD)
- 트리거: docker-compose `api` 서비스, nginx `/api/` 프록시
- 책임: 라우터 등록, 기동 시 Neo4j `theographic_id` 인덱스 생성(lifespan)

**배포:**
- 위치: `deploy.sh` (self-hosted 러너가 `.github/workflows/deploy.yml`에서 호출)
- 트리거: `main` 브랜치 push
- 책임: frontend 빌드 → api 이미지 빌드 → 컨테이너 재시작 → `inject_ko_names.py`로 한글 이름 주입(최대 15회 재시도)

## 아키텍처 제약

- **스레딩:** FastAPI 라우트는 동기 함수(`def`). Neo4j 세션을 `with driver.session()` 블록에서 열고 닫음. 드라이버는 전역 싱글턴이라 스레드 안전 재사용.
- **전역 상태:** `backend/app/db.py`의 `_driver`가 모듈 전역 싱글턴. `lru_cache`로 캐시된 조회 결과(`events.py`, `persons.py`, `overlays.py`)는 프로세스 재시작 전까지 무효화 안 됨 — 데이터 변경 시 API 컨테이너 재시작 필요.
- **HTTP 메서드:** CORS가 `GET`만 허용(`main.py:29`). 쓰기 API 없음 — 모든 데이터 변경은 시드/inject 스크립트로 호스트에서 직접 수행.
- **좌표 출처 이원화:** Place 좌표는 Neo4j에 있으나 `data/place_coords/places.json` 오버레이로 보강. 여정은 오버레이 사건 파일 + Neo4j 좌표 배치 조회로 병합.

## 안티패턴

### effect 내 인라인 화살표 콜백을 하위 fetch effect의 deps로 전달

**무슨 일이 일어나는가:** `SidePanel`의 `onNodeLoaded`를 인라인 화살표로 넘기면 매 렌더마다 새 참조가 되어, deps에 이를 포함한 `/node` fetch effect가 매번 재실행되고 펼침 상태가 리셋된다.
**왜 문제인가:** 섹션이 안 펼쳐지는 버그. `MapView`도 `selectNode`가 재생성되면 `expandPlace` fetch가 abort된다.
**대신 이렇게:** 콜백을 `useCallback`으로 참조 안정화한다. `App.jsx:101`의 `handleSidePanelNodeLoaded`, `useNodeSelection.js:33`의 `selectNode`가 이 패턴을 따른다.

### effect 본문에서 동기 setState

**무슨 일이 일어나는가:** effect 진입 즉시 여러 상태를 동기로 초기화하면 React 19 StrictMode에서 경고·재실행 문제가 발생한다.
**왜 문제인가:** effect 동기 setState 금지 규칙 위반.
**대신 이렇게:** `Promise.resolve().then(() => setState(...))`로 마이크로태스크로 미룬다(`App.jsx:69`).

## 에러 처리

**전략:** 백엔드는 조회 실패 시 빈 결과·404를 반환하고, 파일/DB 예외는 삼켜 부분 동작을 유지(graceful degradation).

**패턴:**
- 노드 미존재 → `HTTPException(404)` (`nodes.py:29`, `:155`)
- Neo4j 인덱스 생성 실패 → `logging.exception` 후 계속 진행(`main.py:19`)
- 오버레이 파일 부재/파싱 실패 → 빈 dict 반환(`overlays.py:26`)
- 프론트 `apiGet`은 비-OK를 status 담은 Error로 throw; 호출부가 `e.name === 'AbortError'`로 취소를 구분(`api.js:9`, `App.jsx:74`)
- CTA 로드 실패는 유한 재시도(1s→2s→4s)로 자가 회복(`App.jsx:44`)

## 횡단 관심사

**로깅:** 백엔드 `logging` 모듈(lifespan 인덱스 실패), 프론트 `console.warn`. 배포는 `deploy.sh`가 `com.biblemap.deploy.log`에 기록.
**검증:** FastAPI 경로 파라미터·`Query` 기본 검증. 도메인 검증 로직은 별도 없음(읽기 전용 API).
**인증:** 없음. 공개 읽기 API. Neo4j 비밀번호만 `NEO4J_PASSWORD` 환경변수로 보호.
**캐싱:** 백엔드 응답에 `Cache-Control` 헤더(`max-age=300` / `no-store`), 프로세스 메모리 `lru_cache`, nginx 정적 자산 immutable 캐시.

---

*아키텍처 분석: 2026-07-04*
