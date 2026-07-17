---
last_mapped_commit: fa9902ef9755f8a2aa2bea544fbb93b8d7f6aaff
mapped: 2026-07-17
---

# TESTING

BibleMap이 정확성을 검증하는 방식. 이 프로젝트에는 **정식 유닛 테스트 프레임워크가 없다** — 검증은 (1) 데이터용 기계검증 스크립트, (2) 로더/빌더/inject의 자체 검증, (3) 화면 레벨 Playwright 검증, (4) 배포 게이트로 이뤄진다.

---

## 0. 정식 테스트 프레임워크 부재

- pytest·unittest·vitest·jest 없음. `*_test.py`·`*.test.jsx`·`*.spec.*`·`conftest.py` 파일 없음. 백엔드 `backend/requirements.txt`는 `fastapi`/`neo4j`/`uvicorn`만, 프론트 `devDependencies`엔 테스트 러너가 없다.
- 프론트의 유일한 정적 게이트는 ESLint(`cd frontend && npm run lint`, flat config `frontend/eslint.config.js`, react-hooks 규칙 포함).
- 즉 "테스트를 돌린다"의 실체는 아래의 `validate_*` 스크립트 · 로더 자체검증 · Playwright 화면검증이다.

---

## 1. 기계검증 스크립트 (`backend/scripts/validate_*.py`)

데이터 저작이 규칙을 지키는지 확인하는 결정적 검증기. 공통 계약: 위반 목록을 `print`하고 위반이 있으면 `sys.exit(1)`, 없으면 `"... OK — 위반 0"`을 찍는다. **inject 전에 위반 0을 확인**하는 게이트로 쓴다.

- `backend/scripts/validate_traits.py` — `data/character_traits/people.json`이 `AUTHORING.md`를 지키는지: ① 라벨이 통제 어휘(`VIRTUES` 24 · `FLAWS` 8) 안 ② 인물당 성품 2~5개·라벨 중복 없음 ③ `verse_ref` 정규식 형식(개역 약어 + 장:절[-절]) ④ 필드 결손. 통제 어휘 집합이 스크립트에 하드코딩돼 AUTHORING.md와 동기화 대상이다.
- `backend/scripts/validate_event_chronology.py` — Neo4j를 읽어 연대 이상을 검출: (a) 인물 출생<활동<사망 서사 역전 (b) 사사 승계 순서 역전 (c) 대표 앵커 대비 역전 (d) 교정 창 내 rec 이벤트 목록화 (e) 형제군 고립 이탈(전치 오타 후보) + Person 스캔(사망<출생·수명>1000년). 신학적 참여 화이트리스트를 둔다. `--json PATH`로 구조화 리포트도 저장한다.
- `backend/scripts/validate_person_context.py` — `data/person_context/people.json`의 인물 소개 검증. 2단 품질 계층(ADR-0027)을 반영해 갱신됨: ① 인물 수 **최소** 86(고정 86 아님 — 가계도 폐포 전원 커버로 1,000명대) ② `role` 비어있지 않음·80자 이하, `intro`는 **있으면** 300자 이하(족보 단역은 intro 없음이 정상) ③ `verses` 1개 이상 ④ `verse_ref` 형식(validate_traits.py의 `REF_RE` 재사용) ⑤ `textKo`/`textEn` 프리베이크 완료(null 아님).
- 실행: `python3 backend/scripts/validate_<name>.py` (Neo4j를 읽는 검증기는 `NEO4J_PASSWORD` 환경변수 필요, `.env`에서 로드).

---

## 2. 로더/빌더/inject 자체 검증

적재·산출 스크립트는 실행 직후 스스로 결과를 검증하거나 안전장치를 둔다.

- `backend/scripts/load_authored_genealogy.py` — 족보 사슬 적재 후 Cypher 도달성 검증: 사슬 끝(후손)에서 `CHILD_OF*`로 사슬 머리(조상)까지 연속인지 `EXISTS { ... }`로 확인하고, 끊겼으면 `raise SystemExit("FAIL: ... 사슬 단절")`.
- `backend/scripts/load_authored_mothers.py` — 어머니-자식 간선 적재(MATCH 전용 — 노드 신규 생성 없음) 후 `merged: n/len(pairs)` 건수를 대조, 불일치(노드 미존재 쌍)면 `raise SystemExit`. 멱등(`MERGE`), 그래프 초기화 후 재적재 대상.
- `backend/scripts/inject_date_corrections.py` — 에코 필드 가드(CONVENTIONS §3.4): DB 현재값이 에코와 불일치하면 스킵+`[WARN]`, 이미 새 값이면 조용히 통과. 멱등·재실행 안전. 결과를 "적용/이미 적용/스킵" 건수로 방출한다.
- `inject_*.py` 공통 — 적재 후 `MATCH ... WHERE <속성> IS NOT NULL RETURN count(...)`로 반영 건수를 `print`하고, 일부는 대표 노드(예: `inject_book_context.py`의 Genesis background)를 샘플 출력해 육안 확인을 돕는다.
- `backend/scripts/build_word_distribution.py` — 산출 전 게이트 두 겹: ① `data/names_ko/books.json` 66권 `assert` ② 상위 단어 중 `data/word_sentiment.json` 미분류가 있으면 `sys.exit`(메시지로 `--dump-words` 안내) — 극성 큐레이션이 끝나야만 정본이 써진다.

---

## 3. 로컬 검증 = 빌드 후 확인 (footgun)

로컬에서 변경을 눈으로 확인하려면 **빌드가 선행**돼야 한다. `docker-compose.yml`이 다음을 강제한다:

- 프론트: nginx가 `./frontend/dist:/usr/share/nginx/html:ro`를 마운트한다 — HMR이 아니라 빌드 산출물을 서빙한다. 프론트 변경 확인 전 반드시 `cd frontend && npm run build`(`.env.production`의 `VITE_API_URL=/api` 자동 적용). 소스만 고치고 빌드를 빼먹으면 `localhost:8080`은 옛 화면을 계속 보여준다.
- 백엔드 데이터: `api`가 `./data:/app/data`를 마운트하므로 오버레이 JSON 변경은 재빌드 없이 반영되지만, 백엔드가 `@functools.lru_cache`로 기동 시 메모리 캐시한다(CONVENTIONS §1.3) → **`docker compose restart api`로 캐시를 비워야** 신규 데이터가 보인다. `docker compose up -d api`는 config 무변경 시 컨테이너를 재생성하지 않아("Running") 옛 데이터를 계속 서빙한다.
- 백엔드 코드: 코드 변경은 이미지 재빌드 필요 — `docker compose up -d --build api`.
- 브라우저 측 API 캐시(footgun 일부 해소): `frontend/src/api.js`의 `apiGet`이 모든 요청에 빌드 식별자 `?v=<BUILD_ID>`를 자동 부착해(CONVENTIONS §2.3) 배포로 데이터가 바뀐 직후에도 브라우저가 `Cache-Control: max-age`가 걸린 옛 API 응답을 재사용하는 문제는 해소됐다. 남는 footgun은 위 백엔드 `lru_cache`(컨테이너 재기동 전까지 유지)뿐이다.
- 로컬 개발 서버(선택): README는 `python3 -m uvicorn backend.app.main:app --reload`(:8000)와 `npm run dev`(:5173)도 안내하나, 배포본과 동형으로 확인하려면 위의 dist 마운트 경로(:8080)를 쓴다.
- API만 먼저 확인할 땐 curl로 계약을 훑는다(예: `/api/words/{id}` 60단어 반환·substring 매칭·미지 book 404 — task#176 검증 방식).

---

## 4. Playwright 화면 테스트

UI 동작 검증은 **Python Playwright**(sync API, `/opt/homebrew`에 설치)로 한다. 패턴: 네트워크 캡처 + 스크린샷으로 `localhost:8080`(또는 프로덕션 도메인)을 렌더 확인하고 **콘솔/네트워크 에러 0**을 확인한다. 프로덕션은 API `:8000`이 미노출이라 nginx `/api` 프록시를 거친다 — 검증도 `:8080` 기준.

### 4.1 스크립트 구조 관례

일회성 검증 스크립트는 `.forge/scratch/`에 둔다. 최근 관례는 **태스크별 하위 디렉터리**(`.forge/scratch/task202/`·`.forge/scratch/task203/`)에 스크립트와 스크린샷을 함께 모으는 것 — 전수 UAT `uat.py`, 개별 수정 검증 `*_verify.py`, 탐색용 `explore_*.py`/`debug*.py`가 공존한다(구식 단일 파일 예시는 `.forge/scratch/task158_screenshots.py`, 공용 스크린샷 보관은 `.forge/reports/`).

- `sync_playwright()` + `p.chromium.launch(headless=True)` + `browser.new_page(viewport={...})`. 전수 UAT는 뷰포트 dict를 상수로 — `.forge/scratch/task202/uat.py`의 `VIEWPORTS = {"mobile": 393×852, "desktop": 1280×800}` 스타일.
- 진입은 `page.goto(BASE, wait_until='networkidle', timeout=15000)` 후 `page.wait_for_timeout(...)`으로 렌더 안정화.
- 요소 조작은 한글 표시 텍스트 기준 `page.get_by_text('타임라인', exact=True).first.click()`. 오버레이(SidePanel 등)가 시각적으로 덮어 실제 클릭이 막히는 요소는 `el.evaluate('el => el.click()')`로 JS 직접 디스패치.
- **지도 위 좌표 클릭**: MapLibre 마커는 DOM 셀렉터로 못 잡는다 — `uat.py`의 `MAP_HELPER_JS`가 React fiber를 스캔해 map 인스턴스를 `window.__map`에 노출하고, `map.project([lng, lat])` + 캔버스 rect로 화면 좌표를 계산해 `page.mouse.click(x, y)`한다.
- 시나리오 단계마다 `page.screenshot(path=...)` + `print`로 진행 방출. 사이트×뷰포트 전수 UAT는 `<site>-<viewport>.png`로 저장하고 **실패 시 `<site>-<viewport>-ERROR.png`**를 따로 남긴다(task202 산출물 명명).
- 텍스트 특정 함정: "외 2권" 같은 부분 텍스트만으로 칩을 특정하면 같은 문구의 다른 행이 먼저 매치된다 — 사건명 등으로 **행을 먼저 특정한 뒤 행 내부에서** 클릭한다(task#203 교정, `xpath=following::button[...]` 체이닝은 `uat.py` 참조).

### 4.2 뷰포트 = 데스크톱 + 모바일

- 디자인/레이아웃 지적은 대개 실폰(배포본) 기준이므로 뷰포트를 먼저 확정하고 시나리오에 **모바일 폭을 반드시 포함**한다(MEMORY 교훈). 최근 실측 조합: 데스크톱 1280(×800/900) + 모바일 390~393.
- SPA 특성상 URL(딥링크)마다 **새 브라우저 컨텍스트**로 여는 것이 안전하다(MEMORY 교훈 — 같은 페이지에서 해시만 바꾸면 상태가 오염된다).
- **모바일 전용 UI(바텀시트 등)의 UAT엔 "긴 콘텐츠 스크롤 후 조작" 케이스를 반드시 포함**한다 — 개폐·ESC만 확인한 전수 UAT(2뷰포트×10사이트)가 통과하고도 스크롤 상호작용 결함 3건이 실기기 피드백으로 돌아온 실사례(task#202 회고). 터치 제스처는 Playwright 합성 디스패치에서 이벤트가 한 태스크에 몰려 state 클로저 레이스가 재현된다 — 판정 로직이 ref를 쓰는지 확인(CONVENTIONS §2.6).

### 4.3 테마 검증 = localStorage `biblemap-theme` 주입

- 앱 테마는 CSS `prefers-color-scheme`이 아니라 localStorage `biblemap-theme` + `documentElement.dataset.theme`으로 구동된다(`frontend/src/main.jsx`, ADR-0020). 따라서 Playwright의 `color_scheme='light'`는 **무효** — 헛 통과 footgun(task#176 회고에서 실측).
- 라이트 테마 강제는 페이지 로드 전 init script로 키를 주입한다:
  ```python
  page.add_init_script("localStorage.setItem('biblemap-theme', 'light')")
  page.goto(BASE, wait_until='networkidle')
  ```
- 테마가 얽힌 UI 변경은 두 테마 × 데스크톱/모바일 매트릭스로 스크린샷 검수한다(task#173 라이트 테마가 8개 화면 × 2테마 × 2뷰포트로 검증한 전례).

### 4.4 모션 검증 매트릭스 (ADR-0024, task#189~191)

모션 토큰(CONVENTIONS §2.1d) 도입 이후의 화면 검증은 기존 §4.2~4.3의 테마×뷰포트 매트릭스에 **reduced-motion on/off** 축을 더한 3축 매트릭스로 짠다.

- Playwright의 `page.emulate_media(reduced_motion='reduce')`로 강제하고, 다크/라이트 × 데스크톱/모바일 × reduce on/off 조합을 화면별 판정 항목 단위로 통과시킨다(실측: task#189 13/13, task#190 7/7, task#191 7/7 PASS — 수치는 3축 조합 수가 아니라 화면·항목별 판정 개수).
- 헤드리스 크로미움은 소프트웨어 GL(SwiftShader)로 렌더링해 MapLibre 캔버스 위 오버레이가 부분 페인트되는 아티팩트를 낼 수 있어 앱 버그로 오인하기 쉽다(task#173 실사례). `chromium.launch(args=["--enable-gpu", "--use-angle=metal"])`(macOS 기준) 같은 **GPU 플래그 A/B 비교를 최우선 1분 테스트**로 돌려 환경 아티팩트인지 앱 회귀인지부터 가른다.
- 배포 직후 검증인데 옛 화면이 남아 있으면, `api.js`의 자동 `?v=<BUILD_ID>` 캐시버스터(위 §3, CONVENTIONS §2.3)가 실제로 최신 빌드값을 싣고 있는지부터 확인한다 — 네트워크 캡처로 요청 URL의 `?v=` 값이 최신 빌드 타임스탬프인지 대조.
- 애니메이션 상태 판정(요소 등장 여부)은 스크린샷과 함께 `print(f'{label} >> visible={loc.is_visible()}')` 류의 텍스트 라인으로 방출해 매트릭스 각 항목의 PASS/FAIL을 로그로 남긴다(§4.1 print 관례의 모션 확장).
- reduced-motion 판정은 **토큰 붕괴(1ms) 직후 최소 1프레임 뒤에 샘플링**한다 — 같은 프레임에서 즉시 읽으면 전환이 끝나기 전 값을 관측해 오탐할 수 있다(task#190에서 검증 스크립트 자체의 레이스 결함으로 실측·수정).
- 세션 1회 재생 스태거(카드 `card-in`·책 펼침 `book-open` — CONVENTIONS §2.1d)는 같은 브라우저 컨텍스트에서 페이지에 두 번 진입시켜, 두 번째 진입에 해당 클래스/애니메이션이 재생되지 않음을 확인한다.

### 4.5 저작 검증 흐름 예

`data/person_relations/AUTHORING.md` §8: `/api/persons/curated`로 node_id 확보 → `/api/person/{node_id}/relations`가 국면을 반환하는지 확인 → Playwright로 화면 렌더 확인.

---

## 5. 저작 → 검증 파이프라인 (정본 순서)

`data/person_relations/AUTHORING.md` §8이 정리한, 저작 후 반드시 밟는 순서:

1. `python3 backend/scripts/generate_verse_text.py` — 멱등, 본문+문맥 프리베이크(getbible UA 우회 내장).
2. (아이콘/프론트 자원 추가 시) `cd frontend && npm run build` — dist 마운트라 빌드 필수.
3. `docker compose restart api` — lru_cache 캐시 비우기(위 §3).
4. API 엔드포인트로 데이터 반환 확인(`/api/persons/curated` → `/api/person/{id}/relations` 등).
5. Playwright로 `localhost:8080` 렌더 확인, 콘솔/네트워크 에러 0.

성품·연대 같은 규칙 데이터는 이 앞에 해당 `validate_*.py`(위 §1)를 돌려 위반 0을 확인한 뒤 inject한다. 단어 분포는 `build_word_distribution.py`(자체 게이트, 위 §2)로 정본을 재산출한 뒤 3~5를 밟는다. 그래프 초기화 후 재적재 시엔 `load_theographic.py` 다음에 `load_authored_genealogy.py`·`load_authored_mothers.py`도 재실행해야 저작 간선이 복원된다(스크립트 docstring 명시).

### 5.1 대량 저작 = 저작(창의) ↔ 검증(기계) 분리 (task#195·#203 구도)

수백~수천 항목의 병렬 저작은 **저작 에이전트는 파일을 만지지 않고 JSON만 반환**하고, 별도 병합자 스크립트가 기계검증 후 정본에 반영하는 구도로 신뢰를 확보한다. 정본 예시는 `.forge/scratch/task203/validate_and_merge.py`(사건 다권 근거 구절 21건×32권 반영, 탈락 0):

1. 저작 산출 JSON(`input.json`)을 모아 병합자가 verseID(BBCCCVVV) 계산 등 파생값을 전담한다 — 저작자는 장:절만 쓴다(CONVENTIONS §3.3과 동일 원칙).
2. 기계 검증 항목별 통과/거부 목록을 만든다(task#203의 4항목: verseID가 `data/bible/verses.json`에 존재 · canonOrder가 `data/names_ko/books.json` 순번과 일치 · 자기일치 · rangeLabel 형식). 거부는 항목 단위 — 나머지는 통과시킨다(§3.4 에코 필드 관행과 동일 철학).
3. 본문 표본 대조(사건당 1절 `textKo` 출력)로 사람이 눈으로 훑는 층을 남긴다.
4. 반영 후 **전수 재스캔 스크립트**로 정합성을 API 레벨에서 닫는다 — `.forge/scratch/task203/rescan.py`가 `/api/events`의 칩 권수 vs `/api/event/{id}/verses`의 권수를 전수 대조해 불일치 목록을 `print` + 결과 JSON으로 저장하는 패턴.

가계도 전원 저작(task#195)도 같은 구도: `.forge/scratch/genealogy-authoring/`의 배치 분류(`s1_classify.py`)·병합검증(`merge_validate.py`)·트리 검증(`verify_tree*.py`) 스크립트 군. 저작 프롬프트에는 근거 인정 경계(2패턴)와 **스킵 허용**을 명시해 억지 인용을 막는다(CONVENTIONS §3.8).

---

## 6. CI / 배포 게이트

- `.github/workflows/deploy.yml` — `main` push 시 self-hosted 러너에서 `git reset --hard origin/main` 후 `bash deploy.sh`. **테스트 스텝은 없다** — 검증은 저작 시점의 `validate_*`·Playwright에 위임한다.
- `deploy.sh` 게이트: ① `npm install` + `npm run build`(프론트) ② `docker compose build api` ③ `docker compose up -d api nginx` ④ `inject_ko_names.py`를 Neo4j 준비까지 최대 15회 재시도하고, 끝내 실패하면 배포를 `exit 1`로 중단한다. lock 파일로 동시 배포를 막는다. `deploy.sh`는 `load_*`를 실행하지 않는다 — 그래프 적재는 저작 시점 수동.
- 배포 후 확인은 `gh run list`(success)로. 배포 무음 실패(백엔드가 옛 코드) 의심 시엔 폴러보다 러너부터 확인한다(글로벌 CLAUDE.md 인프라 격리 규칙).
