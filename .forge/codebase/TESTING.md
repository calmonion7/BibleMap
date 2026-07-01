---
last_mapped_commit: 0189ad9fb964e5eb4fcc91776b3202f7014058dd
mapped: 2026-07-02
---
# 테스트 패턴

## 자동화 테스트 프레임워크: 없음

리포지터리에 단위·통합 테스트 인프라가 **존재하지 않는다**(2026-07-02 HEAD 기준). 검증은 엔드포인트 점검(curl)과 Python Playwright UI 테스트로 수행하는 수동·일회성 운용이다.

- **테스트 파일 0건:** `*.test.*`, `*.spec.*`, `test_*.py`, `*_test.py`, `conftest.py` 전수 검색 결과 없음(`node_modules` 제외).
- **테스트 러너 설정 없음:** `jest.config.*`, `vitest.config.*`, `playwright.config.*`, `pytest.ini`, `setup.cfg`, `tox.ini`, `pyproject.toml` 모두 없음.
- **`frontend/package.json` scripts:** `dev`/`build`/`lint`/`preview`만 존재 — `test` 스크립트 없음.
- **`backend/requirements.txt`:** `fastapi==0.136.3`, `neo4j==6.2.0`, `uvicorn==0.49.0` 3개뿐 — `pytest`·`httpx`·테스트 라이브러리 미포함.
- **CI에 테스트 단계 없음:** 배포 파이프라인(`deploy.sh`)은 빌드 → 이미지 빌드 → 컨테이너 재시작 → 스크립트 실행만 수행. 테스트 게이트 없음.

---

## 현재 검증 방식

### 1. 린트 (프론트엔드 정적 검사)

자동 검사로 사실상 유일하게 강제되는 게이트.

```bash
cd frontend && npm run lint     # eslint . — react-hooks 규칙 포함
```

`frontend/eslint.config.js`(flat config)가 `@eslint/js` recommended + `eslint-plugin-react-hooks` + `eslint-plugin-react-refresh`를 적용. 코드 주석이 react-hooks 규칙(특히 set-state-in-effect)을 의식해 작성돼 있어(`App.jsx`, `EventVerses.jsx`, `useNodeSelection.js`), 린트 통과가 사실상의 합의 기준이다. 백엔드 Python 린터는 미설정.

### 2. 빌드 (타입·구문 깨짐 탐지 + 로컬 검증 선행조건)

```bash
cd frontend && npm run build              # vite build — frontend/dist/ 산출
docker compose -p biblemap build api      # API 이미지 빌드
docker compose -p biblemap up -d api nginx
```

**중요(사용자 메모리 규칙):** 로컬 `:8080`은 `frontend/dist`를 read-only로 마운트하는 정적 서빙이며 HMR이 아니다(`docker-compose.yml`의 `nginx`). 따라서 UI 검증 전 **반드시 `cd frontend && npm run build`로 dist를 갱신**해야 변경이 반영된다. `frontend/.env.production`의 `VITE_API_URL=/api`가 빌드타임 주입돼 nginx 프록시(`/api` → `api:8000`)를 탄다(API는 `:8000` 미노출). API 변경 시 `docker compose -p biblemap up -d --build api`, 데이터만 변경 시(JSON 오버레이·`lru_cache`를 탄 정적 데이터) `docker compose -p biblemap restart api`로 충분하다.

### 3. 엔드포인트 점검 (curl)

백엔드 라우트는 curl로 응답 형상을 직접 확인한다. nginx 프록시 경유(`http://localhost:8080/api/...`) 또는 API 직접 호출(`http://localhost:8000/...`). 자동 assert가 아니라 응답 JSON을 사람이 검토하는 방식이다.

예시 점검 대상:
- `GET /persons/curated` — 22인 slug 목록, `id`/`slug`/`nameKo`/`era`/`eventCount` 형상 확인
- `GET /person/{id}/journey` — `stops` 배열, `seq`/`lng`/`lat` 부여 여부
- `GET /node/{id}` — 라벨 분기, `neighbors`/`properties` 형상
- `GET /events` — `books` 배열 포함 여부, `sortKey` 정렬 확인
- `GET /place/{id}/curated-persons` — `persons` 배열, 시대 내 시간순 정렬 확인

### 4. Python Playwright 화면 테스트 (UI 동작 검증)

사용자 메모리에 정착된 수동 검증 절차. **Python Playwright**를 사용한다(JS Playwright 아님).

- **런타임:** `/opt/homebrew`에 설치된 Python Playwright. `from playwright.sync_api import sync_playwright` 동기 API.
- **대상:** `http://localhost:8080`(nginx가 서빙하는 빌드된 프론트).
- **데스크톱 + 모바일 둘 다:** 뷰포트를 명시해 두 폭을 모두 점검한다 — 데스크톱은 `new_page(viewport={"width": 1400, "height": 900})`(우측 SidePanel 경로), 모바일은 좁은 뷰포트(`MOBILE_BREAKPOINT` 768px 이하, 하단 시트 경로).
- **패턴:** `page.goto(..., wait_until='networkidle')` → 셀렉터·`inner_text()`로 DOM/문구 단언 → `page.screenshot(path=...)` 저장. 네트워크 요청 캡처 + 스크린샷으로 "사용자가 본 화면 + `/api/*` 응답"을 함께 검증.
- **결과 보고:** PASS/FAIL/SKIP 문자열을 dict에 모아 `print`로 출력하고 최종 `ALL PASS`/`SOME FAILED`를 찍는 형태.
- **선행 조건:** 위 2번대로 `npm run build` + 컨테이너 기동이 끝난 상태여야 한다.

별도 `playwright.config.*`나 스펙 파일은 리포의 소스 트리에 커밋돼 있지 않다. Playwright 스크립트는 검증 시점에 일회성으로 작성·실행되며, 작업 산출물로 `.forge/reports/`에 남는다(`task70_verify.py`, `task70_explore.py`, `task_place_dom_probe.py`, `task_place_context_verify.py` 등 — `.gitignore` 대상으로 소스가 아님). 검증 절차 자체는 `.forge/retro/` 회고에 기록됨.

### 5. Neo4j Cypher 직접 점검

데이터 적재 스크립트 실행 후 또는 그래프 데이터 이상 의심 시 `cypher-shell`로 직접 쿼리해 확인한다.

```cypher
-- authored Event 수 확인
MATCH (e:Event) WHERE e.authored = true RETURN count(e);

-- 특정 인물의 여정 OCCURS_AT 관계 확인
MATCH (e:Event)-[:HAS_PARTICIPANT]->(p:Person {theographic_id: "..."})
MATCH (e)-[:OCCURS_AT]->(pl:Place)
RETURN e.nameKo, pl.nameKo, pl.latitude, pl.longitude LIMIT 20;

-- 큐레이션 장소별 인물 연결 확인
MATCH (pl:Place {theographic_id: "..."})
RETURN pl.nameKo, pl.latitude, pl.longitude;
```

---

## 테스트 작성 시 권장 (인프라 부재 상태에서)

자동 테스트가 없으므로, 코드는 **검증 가능성을 높이는 구조**로 작성돼 있다. 신규 코드도 이를 따른다.

- **순수 함수 분리:** 지오메트리·GeoJSON 변환은 `frontend/src/mapGeo.js`에 부수효과 없는 순수 함수로 모여 있다. 단위 테스트를 도입한다면 이 모듈이 가장 테스트하기 쉬운 진입점이다(입력 배열 → 출력 GeoJSON/bounds, Neo4j·DOM 의존 없음). `JourneyList`의 dedup 로직이 `MapView`의 `buildJourneyStopsGeoJSON`과 동일 로직을 공유한다(주석 명시) — 한쪽을 검증하면 다른 쪽도 보장.
- **백엔드 라우트의 정적 헬퍼:** `persons.py`의 `_build_list`, `places.py`의 `_place_to_persons`, `journey.py`의 `_build_id_to_slug`/`_load_events`는 `data/person_events/*.json`만 읽고 Neo4j를 타지 않아(파일만으로 결정적) DB 없이 검증 가능. 단 `@functools.lru_cache`가 걸려 있어 테스트 간 `cache_clear()`가 필요.
- **DB 의존 경계:** Neo4j를 실제로 타는 코드(`nodes.py`, `search.py`, `books.py`, `events.py`의 Cypher 부분, `journey.py:_fetch_place_coords`)는 통합 검증 영역. `get_driver()`(`backend/app/db.py`)가 모듈 전역 lazy 싱글톤이라 모킹 시 `app.db._driver`를 직접 주입하거나 `get_driver`를 패치하는 방식이 된다.

---

## 데이터 적재·생성 스크립트 검증

`backend/scripts/`의 다수 스크립트(`load_*`, `generate_*`, `inject_*`, `enrich_*`)는 모두 일회성 CLI다.

- **검증 방식:** 실행 후 `print(...)`로 출력하는 집계 카운트를 사람이 확인(예 `inject_ko_names.py`의 노드 갱신 수, `load_person_events.py`의 OCCURS_AT·HAS_PARTICIPANT 관계 수).
- **자동 assert·테스트 없음.** 멱등성·정확성은 출력 수치 육안 확인에 의존.
- **배포 파이프라인 내 검증:** `deploy.sh` `[4/4]` 단계가 `inject_ko_names.py`를 Neo4j 준비까지 최대 15회 재시도(2초 간격)하며 실행하고, 실패 시 배포를 중단(`exit 1`)한다 — 적재 스크립트가 사실상의 배포 후 스모크 역할.

---

## 커버리지

측정·강제 안 함. 커버리지 도구·임계값 미설정.
