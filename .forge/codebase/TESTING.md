---
last_mapped_commit: 04e9be173b6a321e4daaa417f6f47004dc3cd687
mapped: 2026-07-11
---

# TESTING

**요약: BibleMap에는 자동화된 단위·통합 테스트 스위트가 없다.** 검증은 (1) 빌드/린트, (2) 데이터 저작 후 검증 파이프라인, (3) 실행 후 Playwright + API curl 스모크로 이뤄진다. 새 코드도 이 절차를 따르며, 테스트 프레임워크를 새로 도입하지 않는다(요청 시에만).

---

## 1. 테스트 프레임워크 (부재)

- **백엔드**: `pytest`·`unittest` 없음. `backend/requirements.txt`에는 런타임 3개(`fastapi`·`neo4j`·`uvicorn`)만 있고 테스트 의존성이 없다. `test_*.py`·`conftest.py`·`tests/` 디렉터리 없음.
- **프론트엔드**: `vitest`·`jest`·`@testing-library` 없음. `frontend/package.json` scripts는 `dev`·`build`·`lint`·`preview`뿐 — `test` 스크립트 없음. `*.test.js(x)`·`*.spec.js(x)` 파일 없음.
- **E2E 스펙 파일**: 리포에 커밋된 Playwright 스펙(`*.spec.ts` 등)은 없다. Playwright는 아래 4절처럼 **애드혹 검증 도구**로만 쓴다. 스크립트는 `.forge/reports/*.py`(예: `task70_verify_final.py`, `uat_118_primeval.py`)에 태스크별로 남아있지만 재실행용 스위트가 아니라 그 태스크 당시의 1회성 검증 기록이다.
- **커밋된·재실행 가능한 검증 = 데이터 기계검증 스크립트뿐**: `backend/scripts/validate_traits.py`·`validate_event_chronology.py`가 저작 데이터의 불변식을 기계검증하고 위반 시 `sys.exit(1)`로 게이트한다(§3-2). 코드가 아니라 **저작 데이터의 정합성**을 검사하는 것이라 유닛 테스트 스위트는 아니지만, 리포에 남아 반복 실행되는 유일한 자동 검증이다.

> 검증 구멍(CONCERNS 소관): 순수 함수 로직에 회귀 테스트가 없다. 예 — `urlState.js`의 `parseHash`/`encodeHash`(정규식 라우팅), `nodes.py`의 `_year()` BC/AD 연도 파싱 정렬, `persons.py`의 `_build_relations` slug 매칭·`_build_connections` 큐레이션 교집합 제외. 이들은 단위 테스트를 붙이기 좋은 순수 함수이나 현재 미커버.

---

## 2. 실제 검증 수단: 빌드 + 린트

빌드/린트 통과가 사실상의 1차 게이트다.

```bash
# 프론트 린트 (ESLint flat config)
cd frontend && npm run lint

# 프론트 빌드 — :8080은 frontend/dist 마운트(HMR 아님)이므로 로컬 검증 전 필수
cd frontend && npm run build      # .env.production의 VITE_API_URL=/api 자동 주입

# 백엔드 이미지 빌드
docker compose up -d --build api
```

- **로컬 검증 전 빌드 필수**: nginx는 `frontend/dist`를 읽기전용 마운트한다(`docker-compose.yml`) — 소스만 고치고 빌드를 건너뛰면 :8080에 반영되지 않는다.
- **백엔드 API 포트(:8000)는 외부 미노출**. 프론트는 nginx `/api` 프록시로만 접근하고, 로컬 검증도 `http://localhost:8080/api/...`로 친다.

## 3. 데이터 저작 검증 파이프라인

저작 도메인마다 검증 절차가 다르지만 공통 골격은 **저작 → (기계검증 게이트) → 본문 프리베이크 → 주입/재시작 → API·Playwright 확인**이다. 기계검증 게이트(§3-2)가 이 프로젝트에서 코드가 아닌 데이터의 정합성을 강제하는 사실상의 테스트 역할을 한다.

### 3-1. 인물 관계 (`data/person_relations/AUTHORING.md` 규칙 8)

`AUTHORING.md` 규칙 8이 정본. 인물 관계·이벤트 데이터를 저작한 뒤 반드시 순서대로 실행한다:

```bash
# 1) 절/문맥 본문 프리베이크 (멱등, getbible UA 우회 내장)
python3 backend/scripts/generate_verse_text.py

# 2) 새 유형 아이콘을 추가했으면 프론트 재빌드 (dist 마운트)
cd frontend && npm run build

# 3) 백엔드 재시작 — lru_cache 캐시를 반드시 비운다 (up -d로는 재생성 안 됨)
docker compose restart api

# 4) API로 관계 반환 확인
curl -s http://localhost:8080/api/persons/curated              # node_id 확보
curl -s http://localhost:8080/api/person/<node_id>/relations   # 국면 배열 확인
```

- **footgun (규칙 8-3)**: 데이터는 마운트 오버레이라 재빌드 불필요하나, 백엔드가 관계 카탈로그를 `@functools.lru_cache`로 기동 시 메모리 캐시하므로 **`docker compose restart api`**로 캐시를 비워야 신규 데이터가 보인다. `docker compose up -d api`는 config 무변경 시 컨테이너를 재생성하지 않아("Running") 옛 데이터를 계속 서빙한다.
- **저작 스크립트 자체 검증**: `generate_verse_text.py`는 멱등이다 — 이미 본문이 있는 항목은 스킵하고, 못 받은 본문은 `null`로 기록해 재실행 시 재시도한다(스크립트 헤더 docstring).

### 3-2. 성품·연대 교정 — 기계검증 게이트(`validate_*.py`) + 에코 필드 주입

인물 성품(task#157)·연대 교정(task#158)은 대량 손저작이라 **주입 전에 `validate_*.py`로 기계검증**하고, 주입 스크립트는 **에코 필드**로 멱등·드리프트 안전을 확보한다. 이 두 장치가 이 프로젝트에서 유닛 테스트를 대신하는 데이터 검증의 핵심이다.

```bash
# 성품(character_traits): 파일 검사 게이트 → 통과해야 주입
python3 backend/scripts/validate_traits.py        # 위반 시 목록 출력 + exit 1
python3 backend/scripts/generate_verse_text.py     # verse_textKo/En 프리베이크(ADR-0003)
python3 backend/scripts/inject_person_traits.py    # Neo4j 주입

# 연대 교정(date_corrections): DB 질의 검출 → 교정 오버레이 주입
python3 backend/scripts/validate_event_chronology.py --json .forge/scratch/chrono.json  # 역전 검출
python3 backend/scripts/inject_date_corrections.py # 에코 대조 후 SET (재적재 때마다 필수)
```

- **기계검증 게이트**: `validate_traits.py`는 `people.json`을 순수 파일 검사(통제 어휘·인물당 2~5개·라벨 중복·`verse_ref` 정규식·필드 결손), `validate_event_chronology.py`는 Neo4j를 질의해 연대 역전 6종(인물 출생/참여/사망 역전·사사 승계·앵커·형제군 고립 이탈·rec 이벤트 목록화·Person 수명 스캔)을 검출한다. **위반이 있으면 목록 출력 후 `sys.exit(1)`** — 저작 규칙(`AUTHORING.md`·ADR-0014)을 코드로 강제하는 회귀 게이트다. 신학적 참여는 `THEOLOGICAL_WHITELIST`로 위반에서 뺀다. `--json PATH`로 구조화 리포트를 남긴다(CONVENTIONS §11-4).
- **에코 필드 멱등(`inject_date_corrections.py`)**: 각 교정 항목이 DB의 현재 기대값 에코(events `title`+`oldStartDate`, persons `name`+`oldValue`)를 실어, 주입 시 DB 현재값과 대조한다 — 에코 일치 → SET, 이미 `new*` 값 → 조용히 통과(재실행), 드리프트 → **스킵 + `[WARN]`**(맹목 덮어쓰기 방지). 그래서 `load_theographic.py` 재적재 후 재실행해도 안전하다(README·ADR-0014 재실행 계약, CONVENTIONS §11-5).
- **효과**: 에코 필드 + 기계검증 조합으로 대량 교정 제안의 거부 0을 달성했다(retro `2026-07-11-theographic-chronology-correction.md`).

## 4. 실행 후 스모크: Playwright + 네트워크 캡처

UI 동작 검증은 Python Playwright로 한다(`/opt/homebrew/bin/playwright`, Python 패키지 — Node.js 패키지가 아니다). `sync_api`·`async_api` 둘 다 동작. 패턴: `http://localhost:8080`(:8000은 외부 미노출) 렌더 확인 + 네트워크 캡처 + 스크린샷.

- **합격 기준**: 콘솔 에러 0, 네트워크(fetch) 에러 0, 대상 뷰가 기대대로 렌더.
- **적용 대상**: 관계 뷰·여정 지도·타임라인 등 상호작용 화면. AUTHORING.md 규칙 8-5가 데이터 저작의 마지막 게이트로 이 스모크를 요구한다. 대규모 회귀 확인(디자인 리뉴얼 등)은 데스크톱·모바일 두 뷰포트로 화면별 전/후 스크린샷을 남긴다(`.forge/reports/design-audit/{desktop,mobile}/`·`design-after/{desktop,mobile}/`, 각 16장).

### 4-1. 화면 전환·셀렉터 함정과 패턴

이 항목들은 실제 검증 세션에서 재현된 함정과 그 대응이다(`~/.claude/projects/.../memory/feedback_playwright_testing.md`에 승격된 교훈):

- **캐시버스터로 화면별 독립 내비게이션 보장**: `page.goto()`는 해시만 바뀌면 SPA를 리로드하지 않아(`#/person/a/...` → `#/person/b/...` 전환 시 이전 화면에 머묾, task#148) 화면마다 상태가 누적될 위험이 있다. `page.reload()` 대신 `?v=<screen-name>` 형태의 캐시버스터 쿼리를 URL에 붙이면 화면당 독립적인 풀 문서 내비게이션이 보장된다(reload보다 상태 오염이 적음, task#155).
- **CSS 토글로 숨긴 뷰가 DOM에 잔존**: display 토글로 숨긴 뷰(예: 타임라인 화면에 숨어있는 여정 리스트)의 텍스트가 `get_by_text(...)`/`text=...` 매칭에 걸려 TimeoutError를 낸다. 텍스트 로케이터는 기본적으로 **`page.locator("text=... >> visible=true")`**로 가시 필터를 붙인다(task#155).
- **`get_by_text` 클릭은 유일성 보장이 없음**: 같은 텍스트가 내비 칩·섹션 라벨·카드에 중복 매치될 수 있다(예: '사도행전' 3곳, task#112). 클릭 후 목표 상태의 지표 텍스트(예: 책 상세의 '중심 메시지')를 확인할 때까지 후보를 순회하는 방식이 필요하다.
- **lucide 아이콘은 이모지 텍스트로 매칭 불가**: 아이콘 자체가 텍스트가 아니므로 인접 텍스트로 클릭한다(task#155).
- **관계(Relations) 화면에서 상대 인물 이름을 직접 클릭하지 않는다**: 큐레이션 인물이면 이름이 여정 점프 버튼(`stopPropagation`)이라 화면을 이탈한다. 근거 구절 레이어는 오버뷰의 `.rel-chip`(국면 라벨 칩)을 직접 클릭해서 연다(task#148).
- **인라인 스타일 문자열을 assert 키로 쓰지 않는다**: CSSOM이 저작값을 정규화해 반환한다(저작 `translateY(0)` → 반환 `translateY(0px)`). 상태 판별은 rect 기하 측정(예: 시트 `top` ≥ viewport height = 숨김)으로 한다(task#111).
- **`scrollIntoView()`는 `overflow:hidden` 조상까지 스크롤시킨다**(transform이 만든 오버플로 포함) — 앱 루트가 밀려 내비가 사라지거나 숨긴 시트가 노출되는 부작용. 컨테이너 한정 스크롤은 `root.scrollTo(top)`을 쓴다(task#110).
- **동일 엔드포인트를 여러 컴포넌트가 각각 호출**: `/persons/curated`는 `App`(CTA용)과 `PersonHub`(허브 카드용)가 각각 fetch한다. `page.route(...)`로 전면 abort하면 관련 없는 호출부까지 막혀 동선이 끊긴다(task#113) — URL만으로 호출처를 구분할 수 없으면 자식 effect의 선실행 순서(자식 요청이 먼저 나감)를 이용해 N번째 요청만 선택적으로 abort한다.
- **수치 assert만으로는 부족**: 스크린샷 육안 검토를 병행한다 — assert가 전부 통과해도 스크린샷에서만 드러나는 레이아웃 버그가 있다(task#110의 "하단 흰 스트립").
- **sync Playwright의 `time.sleep()`은 이벤트 루프를 펌프하지 않는다**: `page.route(...)`로 가로챈 요청 핸들러가 `sleep` 동안 실행되지 못해 가로챈 fetch가 행(hang)한다(task#79). 대기에는 `time.sleep` 대신 `page.wait_for_timeout(ms)`(루프 펌프) 또는 `expect`/`wait_for_*`를 쓴다. `page.evaluate(fetch)`는 evaluate 자체가 루프를 펌프하므로 정상 동작.
- **화면의 단계(Stage) 소속을 먼저 확인**: 지도/타임라인 토글 같은 요소는 허브가 아니라 인물 탐험 단계 내부에 있다. 검증 시나리오는 진입 경로(허브→인물→토글)를 먼저 그리고 시작한다(task#112).

### 4-2. WebGL(지도) 화면 — GPU 플래그 필수

- **기본 헤드리스(SwiftShader, 소프트웨어 GL)는 MapLibre 캔버스를 부분 페인트할 수 있다**: 캔버스 위에 불투명 오버레이(모바일 하단 시트 등)가 있으면 지도 상단이 검게 비는 렌더 아티팩트가 생긴다 — 앱 버그가 아니라 실브라우저에선 재현되지 않는 헤드리스 합성 결함이다(task#156).
- **대응**: 지도가 포함된 화면을 캡처할 때는 `chromium.launch(args=["--enable-gpu", "--use-angle=metal"])`로 GPU를 켠다. WebGL 화면에서 시각 이상이 보이면 **CSS/앱 이분 탐색을 시작하기 전에 GPU 플래그 A/B를 먼저 1분 테스트**한다 — task#156에서 이 순서를 지키지 않아 앱 회귀로 오판, CSS 이분 탐색으로 여러 빌드를 태운 뒤에야 원인(헤드리스 아티팩트)에 도달했다.
- **MapLibre 캔버스는 래스터 타일 + 마커 오버레이가 한 캔버스를 공유**: 지도 톤 조정을 CSS `filter`로 하면 오버레이(마커·팝업)까지 같이 틴트된다. 톤 조정은 래스터 레이어 paint 속성(`raster-saturation`·`raster-brightness-max`·`raster-contrast`, `frontend/src/MapView.jsx`)으로 한다.
- **맵 인스턴스 접근**: `MapView.jsx`는 `mapRef.current`만 쓰고 `window`에 노출하지 않는다. 캔버스 위 클러스터/마커를 정확히 클릭하려면 UAT 동안만 `window.__map = map`을 임시로 추가해 `queryRenderedFeatures`/`project`로 픽셀을 산출하고, 검증이 끝나면 제거·재빌드한다(dist에 무흔적, task#77~80).

### 4-3. 모바일 뷰포트 함정

- **헤드리스는 모바일 브라우저 크롬(주소창·내비바)이 없어 `100vh` == 가시 높이**: 실기기에선 `100vh` 루트에서 `bottom:0` 요소가 가시 영역 아래로 잘리는데, 헤드리스는 이를 구조적으로 검출하지 못한다. 실제로 "모바일 첫 로딩 여정 안보임"(task#90)이 헤드리스 검증은 통과했으나 실기기(`biblemap.taebro.com`)에서 재발했다(원인: `100vh` → `100dvh`로 수정, task#91). 모바일 레이아웃·하단 고정 요소는 프로덕션 도메인(`biblemap.taebro.com`, self-hosted 배포 대상, localhost:8080과 동일 번들)이나 실기기로 확인하고, `100vh` 사용처는 기본적으로 의심한다.
- **Vite dev 서버(5173)는 로컬에서 API에 닿지 않는다**: `api.js`의 `API_BASE` 기본값이 `localhost:8000`인데 호스트에 매핑되어 있지 않다(curl 000). 픽셀 정밀 레이아웃 검증은 5173이 아니라 build → 8080 → Playwright로 확정한다.

## 5. 배포 검증

`deploy.sh`가 프로덕션 배포 시 인라인 검증을 수행한다(별도 테스트 대신):

- `NEO4J_PASSWORD`가 준비될 때까지 `inject_ko_names.py`를 **최대 15회 재시도**(2초 간격)하며, 15회 후에도 실패하면 `exit 1`로 배포를 중단한다(`deploy.sh` [4/4]).
- 배포 락(`/tmp/biblemap-deploy.lock`)으로 중복 배포를 막는다.
- 배포 무음 실패 시(백엔드가 옛 코드) self-hosted 러너 상태부터 의심한다(`gh run list`로 `queued`/`cancelled(24h)` 확인).

## 6. 백엔드의 내장 방어(테스트 대체 성격)

명시적 테스트가 없는 대신, 런타임 방어 코드가 계약을 강제한다:

- `backend/app/db.py`: `NEO4J_PASSWORD` 미설정 시 `RuntimeError`로 기동 실패(조용한 오작동 방지).
- `backend/app/main.py` lifespan: 인덱스 생성 실패를 `logging.exception`으로 잡고 인덱스 없이 계속 진행(가용성 우선).
- `backend/app/overlays.py` `_load()`: `json.JSONDecodeError`를 빈 dict로 삼켜 파손 파일에 방어.
- `backend/app/routes/persons.py` `_build_list()`: `events[0].participants`가 비면 `logging.warning` 후 해당 slug 건너뜀.

---

## 7. 커버리지 현황 요약

| 영역 | 커버리지 |
|---|---|
| 백엔드 순수 함수(`_year()` 파싱, slug 매칭 등) | 0 — 단위 테스트 없음, 애드혹 손검증만 |
| 백엔드 라우트 | 0 — curl 스모크로만 응답 형태 확인 |
| 프론트 순수 함수(`parseHash`/`encodeHash` 등) | 0 |
| 프론트 컴포넌트 | 0 — Playwright 애드혹 스모크로 렌더/상호작용만 확인 |
| E2E(회귀 스위트로 재실행 가능한 형태) | 없음 — `.forge/reports/*.py`는 태스크별 1회성 스크립트 |
| 빌드/린트 게이트 | 있음(`npm run lint`·`npm run build`), CI 강제 여부는 ARCHITECTURE/INTEGRATIONS 소관 |
| 저작 데이터 기계검증(`validate_traits.py`·`validate_event_chronology.py`) | 있음 — 리포에 커밋된 유일한 재실행 자동 검증. 코드가 아닌 데이터 정합성을 검사, 위반 시 `exit 1` (§3-2) |
| 데이터 저작 파이프라인 검증 | 있음(AUTHORING.md 규칙 8, §3-1) |
| 배포 검증 | 있음(`deploy.sh` 인라인 재시도·락, §5) |

---

## 새 코드 검증 방법 (권장 절차)

1. 백엔드 라우트를 추가/변경 → `docker compose up -d --build api` 후 `curl -s http://localhost:8080/api/<path>`로 응답 형태 확인.
2. 데이터를 저작 → 위 3절 파이프라인 실행(관계는 §3-1, 성품·연대 교정은 §3-2 — 대량 저작이면 먼저 `validate_*.py` 게이트를 통과시킨 뒤 주입한다).
3. 프론트를 변경 → `npm run lint` → `npm run build` → Playwright 스모크(콘솔/네트워크 에러 0, §4의 셀렉터·GPU 플래그 패턴 적용).
4. 순수 함수(라우팅·파싱·정렬)를 새로 쓸 때 회귀 위험이 크면, 테스트 프레임워크 부재를 감안해 최소한 애드혹 `python3 -c`/`node -e` 스니펫으로 경계값을 손검증한다.

---

*Testing analysis: 2026-07-11*
