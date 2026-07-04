---
last_mapped_commit: 815433397ff74c133b2de5d1cafe1c8764b5303c
mapped: 2026-07-04
---
# 코드베이스 구조

**분석일:** 2026-07-04

## 디렉터리 레이아웃

```
BibleMap/
├── frontend/               # React SPA (Vite)
│   ├── src/                # 컴포넌트·헬퍼 소스
│   ├── public/             # 정적 에셋
│   ├── dist/               # 빌드 산출물(gitignore, nginx가 서빙)
│   ├── index.html          # HTML 셸
│   ├── vite.config.js      # Vite 설정(maplibre 청크 분리)
│   └── package.json        # 프론트 의존성·스크립트
├── backend/                # FastAPI + 시드 스크립트
│   ├── app/                # API 애플리케이션
│   │   ├── main.py         # FastAPI 앱·라우터 등록·lifespan
│   │   ├── db.py           # Neo4j 드라이버 싱글턴
│   │   ├── overlays.py     # data/*.json 로더(_resolve/_load)
│   │   └── routes/         # 엔드포인트별 라우터 파일
│   ├── scripts/            # Neo4j 적재·주입 스크립트(21개)
│   ├── Dockerfile          # python:3.12-slim + uvicorn
│   └── requirements.txt    # fastapi/neo4j/uvicorn 핀 버전
├── data/                   # JSON 오버레이 데이터(카테고리별 하위 디렉터리)
├── nginx/nginx.conf        # 리버스 프록시 + 정적 서빙 설정
├── docker-compose.yml      # neo4j + api + nginx 스택
├── deploy.sh               # 프론트 빌드→이미지 빌드→재시작→한글 주입
├── .github/workflows/      # deploy.yml(self-hosted 러너)
├── .env / .env.example     # NEO4J_PASSWORD(비밀값, .env는 gitignore)
├── BIBLEMAP_PLAN.md        # 프로젝트 기획 문서
└── CLAUDE.md / README.md   # 지침·안내
```

## 디렉터리 목적

**`frontend/src/`:**
- 목적: React SPA 소스 전부
- 포함: 화면 컴포넌트(`*.jsx`), 순수 헬퍼·훅(`*.js`), 전역 스타일(`index.css`)
- 핵심 파일: `App.jsx`(루트 상태 머신), `main.jsx`(마운트 진입점), `api.js`(fetch 헬퍼)

**`backend/app/`:**
- 목적: FastAPI 애플리케이션
- 포함: 앱 부팅(`main.py`), DB 드라이버(`db.py`), 오버레이 로더(`overlays.py`), 라우터(`routes/`)
- 핵심 파일: `main.py`(진입점), `routes/nodes.py`(가장 큰 라우터, 노드 상세/이웃/장소)

**`backend/app/routes/`:**
- 목적: URL 경로별 엔드포인트 정의. 각 파일이 `router = APIRouter()`를 노출하고 `main.py`가 include
- 포함: `nodes.py`, `events.py`, `journey.py`, `persons.py`, `places.py`, `books.py`, `search.py`
- 규칙: 라우트 함수는 동기 `def`, 응답은 `dict` 또는 `JSONResponse`(+`Cache-Control`)

**`backend/scripts/`:**
- 목적: Neo4j 시드 및 오버레이 데이터 주입(호스트에서 직접 실행, API 컨테이너 밖)
- 포함: `load_*`(적재), `inject_*`(주입), `generate_*`(오버레이 파일 생성), `enrich_*`(보강)
- 핵심 파일: `load_theographic.py`(Theographic 원본→Neo4j 기본 노드·관계), `inject_ko_names.py`(deploy.sh가 매 배포 후 실행)

**`data/`:**
- 목적: Neo4j 외부의 큐레이션 JSON 오버레이. compose에서 `./data:/app/data`로 API에 마운트
- 포함: 카테고리별 하위 디렉터리(각 하위엔 1개 이상의 JSON)

## 주요 파일 위치

**진입점:**
- `frontend/src/main.jsx`: React 루트 마운트
- `frontend/src/App.jsx`: 앱 상태 머신·레이아웃(hub/explore/overview)
- `backend/app/main.py`: FastAPI 앱·라우터 등록

**설정:**
- `docker-compose.yml`: 3서비스 스택(neo4j/api/nginx), 포트·볼륨·env
- `nginx/nginx.conf`: `/api/` 프록시, 정적 캐시 정책
- `frontend/vite.config.js`: 빌드·청크 설정
- `.env.example`: 필요 환경변수 구조(`NEO4J_PASSWORD`)

**핵심 로직:**
- `backend/app/db.py`: Neo4j 드라이버 싱글턴(`get_driver`)
- `backend/app/overlays.py`: 오버레이 경로 탐색·로드(`_resolve`/`_load`)
- `backend/app/routes/persons.py`: 큐레이션 인물 매핑 단일 출처(`_ERA`/`_NAME_KO`/`_ERA_ORDER`)
- `frontend/src/api.js`: fetch 단일 진입점(`apiGet`)
- `frontend/src/useNodeSelection.js`: 노드 선택 상태 훅

**그래프 렌더 (프론트 지도):**
- `frontend/src/MapView.jsx`: maplibre 지도 컨테이너·라이프사이클
- `frontend/src/mapGeo.js`: 좌표→GeoJSON 변환 헬퍼
- `frontend/src/mapLayers.js`: 소스·레이어 설정·이벤트 핸들러 등록
- `frontend/src/mapRingController.js`: 장소 클릭 시 사건 링 fly-out 제어

**테스트:**
- 자동화 테스트 없음. 검증은 Python Playwright 스크린샷/네트워크 캡처로 수동 수행(프로젝트 메모리 관례).

## 성경 데이터·시드 파일 위치

**인물/사건 큐레이션 (여정용):**
- `data/person_events/<slug>.json`: 큐레이션 인물별 시간순 사건 배열. 각 사건에 `id`, `title`, `nameKo`, `sortKey`, `occursAt`(place id), `participants`(person id), `books`(근거 구절 범위). `journey.py`·`persons.py`·`places.py`가 이 파일들을 직접 읽음. slug 매핑은 `persons.py` `_ERA`/`_NAME_KO`에 고정.
- `data/authored_events/events.json`, `data/authored_persons/people.json`: 큐레이션 저작(authored) 사건·인물. `load_authored_events.py`·`load_authored_persons.py`가 Neo4j에 적재.

**근거 구절:**
- `data/event_verses/events.json`: 사건별 근거 구절(권별 그룹). `events.py`의 `/event/{id}/verses`가 `overlays.event_verses()`로 로드.
- `data/verse_events/events.json`: 절→사건 매핑.

**성경권 문맥·연대:**
- `data/book_events/books.json`: `{bookId: [eventId]}` — 사건을 기록한 권 역매핑(`overlays.book_events_raw()`).
- `data/book_context/books.json`, `data/book_years_approx/books.json`: 권 문맥·추정 연대.

**한글 이름 (주입 소스):**
- `data/names_ko/{books,events,groups,people,places}.json`: 엔티티별 영문→한글 이름 매핑. `inject_ko_names.py`가 Neo4j 노드의 `nameKo` 속성으로 주입(매 배포 후 실행).

**좌표·장소 문맥:**
- `data/place_coords/places.json`: Place 좌표 보강. `enrich_place_coords.py`.
- `data/place_context/places.json`: 장소 설명. `inject_place_context.py`.

**인물 특성:**
- `data/character_traits/people.json`: 인물 traits. `inject_person_traits.py`가 Neo4j `traits`(JSON 문자열) 속성으로 주입, `nodes.py`가 조회 시 파싱.

## 컴포넌트·라우트·쿼리 위치 요약

**프론트 화면 컴포넌트 (`frontend/src/`):**
- `PersonHub.jsx` — 인물 선택 허브(시작 화면)
- `MapView.jsx` + `mapGeo.js`/`mapLayers.js`/`mapRingController.js` — 지도 뷰
- `TimelineView.jsx` — 타임라인 뷰
- `BibleOverviewView.jsx` — 성경 책 개요
- `SidePanel.jsx` — 노드 상세 패널(가장 큰 컴포넌트, 650줄)
- `JourneyList.jsx` — 여정 정차지 리스트
- `EventVerses.jsx` / `VerseLangTabs.jsx` — 근거 구절·언어 탭
- `Spinner.jsx` — 로딩 인디케이터

**API 라우트 (`backend/app/routes/`):**
- `nodes.py` — `/node/{id}`, `/node/{id}/neighbors/grouped`, `/node/{id}/places`, `/person/{id}/event-ids`
- `events.py` — `/events`, `/event/{id}/verses`
- `journey.py` — `/person/{id}/journey`
- `persons.py` — `/persons/curated`
- `places.py` — `/place/{id}/curated-persons`
- `books.py` — `/books-overview`
- `search.py` — `/search`

**그래프 쿼리:** Cypher는 각 라우트 파일 내부에 인라인 문자열로 작성(`session.run("MATCH ...")`). 전용 쿼리 모듈 없음.

## 명명 규칙

**파일:**
- 프론트 React 컴포넌트: `PascalCase.jsx` (예: `MapView.jsx`, `SidePanel.jsx`)
- 프론트 헬퍼·훅: `camelCase.js` (예: `useNodeSelection.js`, `mapGeo.js`, `api.js`)
- 백엔드 모듈·스크립트: `snake_case.py` (예: `load_theographic.py`, `inject_ko_names.py`)
- 데이터 파일: 카테고리 디렉터리 안에 `<복수명사>.json`(`people.json`, `events.json`) 또는 slug별 `<slug>.json`(`abraham.json`)

**디렉터리:**
- 프론트: `frontend/src` 평면(하위 디렉터리 거의 없음)
- 백엔드: `app`(런타임) / `scripts`(오프라인) 분리, `app/routes`로 라우터 그룹화
- 데이터: 카테고리별 `snake_case/` (예: `person_events/`, `place_coords/`, `book_events/`)

**식별자:**
- Neo4j 노드 키: `theographic_id`(문자열), 이름 속성 `name`(영문)·`nameKo`(한글)·`title`(사건)
- 큐레이션 인물: `slug`(영문 소문자, `john_the_baptist`처럼 `_` 구분)

## 새 코드를 어디에 둘까

**새 API 엔드포인트:**
- 관련 라우터 파일에 추가(`backend/app/routes/<도메인>.py`), 신규 도메인이면 새 파일 + `main.py`에 `app.include_router(...)` 등록
- Neo4j 조회는 `get_driver()` + `with driver.session()`, 응답은 `JSONResponse`에 `Cache-Control` 헤더

**새 프론트 화면/컴포넌트:**
- `frontend/src/<PascalCase>.jsx`로 생성, `App.jsx`에서 임포트·조건부 렌더
- fetch는 반드시 `apiGet`(`api.js`) 경유, 취소 필요 시 `AbortController` signal 전달

**새 프론트 헬퍼/훅:**
- 순수 로직·훅은 `frontend/src/<camelCase>.js`

**새 오버레이 데이터:**
- `data/<카테고리>/<파일>.json` 추가, `overlays.py`에 로더 함수(`lru_cache`) 또는 라우트에서 `_resolve` 사용
- Neo4j 주입이 필요하면 `backend/scripts/inject_*.py` 또는 `load_*.py` 추가

**새 큐레이션 인물:**
- `data/person_events/<slug>.json` 추가 + `persons.py`의 `_ERA`·`_NAME_KO`에 slug 등록(단일 출처)

## 특수 디렉터리

**`frontend/dist/`:**
- 목적: Vite 빌드 산출물. nginx가 `/usr/share/nginx/html`로 마운트해 서빙
- 생성됨: 예(`npm run build`)
- 커밋됨: 아니오(gitignore). 로컬 검증 전 반드시 빌드 필요

**`.forge/`:**
- 목적: 포지(forge) 루프 상태·영구 문서. `codebase/`·`adr/`·`retro/`·`CONTEXT.md`만 커밋, 나머지 루프 상태는 gitignore
- 커밋됨: 부분(화이트리스트, `.gitignore` 참조)

**`data/`:**
- 목적: 오버레이 JSON. 커밋됨(예). API 컨테이너에 볼륨 마운트

**`.env`:**
- 목적: `NEO4J_PASSWORD` 비밀값
- 커밋됨: 아니오(gitignore). 구조는 `.env.example` 참조

---

*구조 분석: 2026-07-04*
