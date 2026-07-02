---
last_mapped_commit: 99d42c8518af00f3e0bf4a4ba90f821d84cf42e5
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

`frontend/eslint.config.js`(flat config)가 `@eslint/js` recommended + `eslint-plugin-react-hooks` + `eslint-plugin-react-refresh`를 적용. 코드 주석이 react-hooks 규칙(특히 set-state-in-effect)을 의식해 작성돼 있어(`frontend/src/App.jsx`, `frontend/src/EventVerses.jsx`, `frontend/src/useNodeSelection.js`), 린트 통과가 사실상의 합의 기준이다. 백엔드 Python 린터는 미설정.

### 2. 빌드 (타입·구문 깨짐 탐지 + 로컬 검증 선행조건)

```bash
cd frontend && npm run build              # vite build — frontend/dist/ 산출
docker compose -p biblemap build api      # API 이미지 빌드
docker compose -p biblemap up -d api nginx
```

**중요(사용자 메모리 규칙):** 로컬 `:8080`은 `frontend/dist`를 read-only로 마운트하는 정적 서빙이며 HMR이 아니다(`docker-compose.yml`의 `nginx` 서비스 — `./frontend/dist:/usr/share/nginx/html:ro`). 따라서 UI 검증 전 **반드시 `cd frontend && npm run build`로 dist를 갱신**해야 변경이 반영된다. `frontend/.env.production`의 `VITE_API_URL=/api`가 빌드타임 주입돼 nginx 프록시(`/api` → `api:8000`)를 탄다(API는 `:8000` 미노출). API 변경 시 `docker compose -p biblemap up -d --build api`, 데이터만 변경 시(JSON 오버레이·`lru_cache`를 탄 정적 데이터) `docker compose -p biblemap restart api`로 충분하다.

### 3. 엔드포인트 점검 (curl)

백엔드 라우트는 curl로 응답 형상을 직접 확인한다. nginx 프록시 경유(`http://localhost:8080/api/...`) 또는 API 직접 호출(`http://localhost:8000/...`). 자동 assert가 아니라 응답 JSON을 사람이 검토하는 방식이다.

예시 점검 대상:
- `GET /persons/curated` — 인물 목록, `id`/`slug`/`nameKo`/`era`/`eventCount` 형상 확인, 시대 내 시간순 정렬 확인
- `GET /person/{id}/journey` — `stops` 배열, `seq`/`lng`/`lat` 부여 여부
- `GET /node/{id}` — 라벨 분기, `neighbors`/`properties` 형상
- `GET /events` — `books` 배열 포함 여부, `sortKey` 정렬 확인
- `GET /place/{id}/curated-persons` — `persons` 배열, 시대 내 시간순 정렬 확인
- `GET /event/{id}/verses` — `books`별 `verses` 배열, `textKo`/`textEn` 필드 존재 확인

### 4. Python Playwright 화면 테스트 (UI 동작 검증)

사용자 메모리에 정착된 수동 검증 절차. **Python Playwright**를 사용한다(JS Playwright 아님).

#### 실행 환경

- **런타임:** `/opt/homebrew`에 설치된 Python Playwright. `from playwright.sync_api import sync_playwright` 동기 API.
- **대상:** `http://localhost:8080`(nginx가 서빙하는 빌드된 프론트). Vite dev 서버(5173)는 검증 대상이 아니다 — API 기본값이 `localhost:8000`(CORS 미매핑)이라 curl 000 실패.
- **선행 조건:** `npm run build` + 컨테이너 기동이 끝난 상태.

#### 기본 패턴

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1400, "height": 900})
    page.goto('http://localhost:8080', wait_until='networkidle', timeout=15000)
    # ... 셀렉터·inner_text()로 DOM/문구 단언 ...
    page.screenshot(path='/Users/calmonion/Project/BibleMap/.forge/reports/<task>-<step>.png')
    browser.close()
```

- `wait_until='networkidle'`: 페이지 로드 + 최초 API fetch 완료까지 대기.
- `page.wait_for_timeout(N)`: 비동기 state 변화(API 응답 후 렌더) 대기. 클릭 후 1000~1500ms 부여.
- 셀렉터: `page.locator('text=...')`, `page.get_by_text(...)`, `page.locator('button:has-text(...)')` 혼용. DOM 순회가 필요하면 `page.evaluate('() => { ... }')` JS 인라인.
- `inner_text()` / `count()` / `is_visible()` / `click()` / `fill()` 조합으로 UI 동작 단언.

#### 결과 보고 패턴

```python
results = {}
results['some_check'] = 'PASS - 설명' # or 'FAIL - 이유' or 'SKIP'
all_pass = all(v.startswith('PASS') or v.startswith('SKIP') for v in results.values())
for key, val in results.items():
    print(f"  {key}: {val}")
print(f"\n최종: {'ALL PASS' if all_pass else 'SOME FAILED'}")
```

PASS/FAIL/SKIP 문자열을 dict에 모아 `print`로 출력하고 최종 `ALL PASS`/`SOME FAILED`를 찍는 형태가 표준.

#### 데스크톱·모바일 이중 검증

뷰포트를 명시해 두 폭을 모두 점검한다:
- **데스크톱:** `new_page(viewport={"width": 1400, "height": 900})` — 우측 SidePanel 슬라이드인 경로.
- **모바일:** 좁은 뷰포트(`MOBILE_BREAKPOINT` 768px 이하) — 하단 시트·여정 스트립 경로.

#### 스크린샷 저장 위치

검증 시점에 일회성으로 작성·실행하며, 작업 산출물로 `.forge/reports/`에 남긴다. 예:
- `.forge/reports/task70_verify.py` / `.forge/reports/task70_verify.png`
- `.forge/reports/task_place_context_verify.py` / `.forge/reports/place_hebron_ko.png`

소스 트리에 별도 `playwright.config.*`나 스펙 파일은 커밋하지 않는다. 검증 절차 자체는 `.forge/retro/` 회고에 기록됨.

#### 네트워크 캡처 + DOM 단언 복합 패턴

일부 검증 스크립트는 DOM 확인과 함께 API 응답 내용을 간접 검증한다(`task_place_context_verify.py` 참조 패턴):

```python
# API 응답이 UI에 반영됐는지 DOM 텍스트로 확인
body_text = page.locator('body').inner_text()
has_author = '모세' in body_text
# 특정 섹션 헤더 클릭 → 펼침 확인
hdr = page.locator("button:has-text('장소 배경')").first
hdr.click()
page.wait_for_timeout(400)
# 보라 박스 border-left 스타일로 구절 컨테이너 선택
box = page.locator("div[style*='border-left'][style*='#f5f3ff']").first
ko_text = box.inner_text(timeout=1500).strip()
# 언어 탭 전환
page.locator("button:has-text('영어')").first.click()
```

### 5. 데이터 파이프라인 null 검증 (구절 본문 품질 점검)

`backend/scripts/generate_verse_text.py` 실행 후 `null` 카운트를 콘솔에서 확인하는 관행. 이것이 구절 본문 파이프라인의 유일한 품질 지표다.

```
event_verses: {'kept': N, 'filled': N, 'null': N}
book_context: {'kept': N, 'filled': N, 'null': N}
character_traits: {'kept': N, 'filled': N, 'null': N}
place_context: {'kept': N, 'filled': N, 'null': N}
```

**신규 사건 구절 null 0 확인이 완료 기준.** 예시:

- 사울 사건 신규 추가 후: "사울 114구절 null 0" — 사울과 무관한 기존 24건 null은 versification 차이(KJV엔 있으나 개역 절번호 미존재)로 무시 가능한 상수.
- 솔로몬 신규 6사건 56구절 null 0, 엘리야·다니엘 등 신규 사건 null 0 기준으로 task 완료 판정.

`backend/scripts/generate_verse_text.py`의 `main()`은 마지막에 알려진 절(창 1:1, 마 9:36, 첫 event_verses 사건 첫 절)의 ko·en 본문을 `print`로 육안 확인용으로 출력한다.

### 6. Neo4j Cypher 직접 점검

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

-- 인물 시대 내 시간순 정렬 확인 (persons/curated 정렬과 동일 기준)
MATCH (e:Event) WHERE e.authored = true RETURN e.nameKo, e.sortKey ORDER BY e.sortKey;
```

---

## 테스트 작성 시 권장 (인프라 부재 상태에서)

자동 테스트가 없으므로, 코드는 **검증 가능성을 높이는 구조**로 작성돼 있다. 신규 코드도 이를 따른다.

- **순수 함수 분리:** 지오메트리·GeoJSON 변환은 `frontend/src/mapGeo.js`에 부수효과 없는 순수 함수로 모여 있다. 단위 테스트를 도입한다면 이 모듈이 가장 테스트하기 쉬운 진입점이다(입력 배열 → 출력 GeoJSON/bounds, Neo4j·DOM 의존 없음). `frontend/src/JourneyList.jsx`의 dedup 로직이 `frontend/src/mapGeo.js`의 `buildJourneyStopsGeoJSON`과 동일 로직을 공유한다(주석 명시) — 한쪽을 검증하면 다른 쪽도 보장.
- **백엔드 라우트의 정적 헬퍼:** `backend/app/routes/persons.py`의 `_build_list`, `backend/app/routes/places.py`의 `_place_to_persons`, `backend/app/routes/journey.py`의 `_build_id_to_slug`/`_load_events`는 `data/person_events/*.json`만 읽고 Neo4j를 타지 않아(파일만으로 결정적) DB 없이 검증 가능. 단 `@functools.lru_cache`가 걸려 있어 테스트 간 `cache_clear()`가 필요.
- **DB 의존 경계:** Neo4j를 실제로 타는 코드(`backend/app/routes/nodes.py`, `backend/app/routes/search.py`, `backend/app/routes/books.py`, `backend/app/routes/events.py`의 Cypher 부분, `backend/app/routes/journey.py`의 `_fetch_place_coords`)는 통합 검증 영역. `backend/app/db.py`의 `get_driver()`가 모듈 전역 lazy 싱글톤이라 모킹 시 `app.db._driver`를 직접 주입하거나 `get_driver`를 패치하는 방식이 된다.

---

## 데이터 적재·생성 스크립트 검증

`backend/scripts/`의 다수 스크립트(`load_*`, `generate_*`, `inject_*`, `enrich_*`)는 모두 일회성 CLI다.

- **검증 방식:** 실행 후 `print(...)`로 출력하는 집계 카운트를 사람이 확인(예 `backend/scripts/inject_ko_names.py`의 노드 갱신 수, `backend/scripts/load_person_events.py`의 OCCURS_AT·HAS_PARTICIPANT 관계 수).
- **자동 assert·테스트 없음.** 멱등성·정확성은 출력 수치 육안 확인에 의존.
- **배포 파이프라인 내 검증:** `deploy.sh` 최종 단계가 `backend/scripts/inject_ko_names.py`를 Neo4j 준비까지 최대 15회 재시도(2초 간격)하며 실행하고, 실패 시 배포를 중단(`exit 1`)한다 — 적재 스크립트가 사실상의 배포 후 스모크 역할.

---

## 커버리지

측정·강제 안 함. 커버리지 도구·임계값 미설정.
