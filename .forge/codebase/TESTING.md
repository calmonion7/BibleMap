---
last_mapped_commit: 304eda1c53acff4c4860b838e8627483c666f74c
mapped: 2026-07-18
---

# TESTING

BibleMap이 정확성을 검증하는 방식. 이 프로젝트에는 **정식 유닛 테스트 프레임워크가 없다** — 검증은 (1) 데이터용 기계검증 스크립트(`validate_*.py`), (2) 로더/빌더/inject 스크립트의 자체 검증, (3) 화면 레벨 Python Playwright 검증, (4) 배포 게이트로 이뤄진다.

---

## 0. 정식 테스트 프레임워크 부재

- pytest·unittest·vitest·jest 없음. `*_test.py`·`*.test.jsx`·`*.spec.*`·`conftest.py` 파일이 리포지토리에 없다. 백엔드 `backend/requirements.txt`는 `fastapi`/`neo4j`/`uvicorn`만 갖고, 프론트 `devDependencies`엔 테스트 러너가 없다.
- 프론트의 유일한 정적 게이트는 ESLint(`cd frontend && npm run lint`, flat config `frontend/eslint.config.js`, `@eslint/js` 권장 + `eslint-plugin-react-hooks` + `eslint-plugin-react-refresh`).
- 즉 "테스트를 돌린다"의 실체는 아래 §1의 `validate_*` 스크립트 · §2의 로더 자체검증 · §4의 Playwright 화면검증이다.

---

## 1. 기계검증 스크립트 (`backend/scripts/validate_*.py`)

데이터 저작이 규칙을 지키는지 확인하는 결정적 검증기. 공통 계약: 위반 목록을 `print`하고 위반이 있으면 `sys.exit(1)`, 없으면 `"PASS"`/`"OK — 위반 0"` 계열 메시지를 찍는다. inject/반영 전에 위반 0을 확인하는 게이트로 쓴다.

- `backend/scripts/validate_traits.py` — `data/character_traits/people.json`이 `data/character_traits/AUTHORING.md`를 지키는지: ① 라벨이 통제 어휘(`VIRTUES` 24·`FLAWS` 8) 안 ② 인물당 성품 2~5개·라벨 중복 없음 ③ `verse_ref`가 정규식(개역 약어 + 장:절[-절[:절]])을 만족 ④ 필드 결손. 통제 어휘 집합이 스크립트에 하드코딩돼 있어 AUTHORING.md와 동기화 대상.
- `backend/scripts/validate_person_context.py` — `data/person_context/people.json`의 인물 소개 검증(2단 품질 계층 ADR-0027 반영): ① 인물 수 **최소 86**(고정 아님) ② `role` 비어있지 않음·80자 이하, `intro`는 있으면 300자 이하(족보 단역은 intro 없음이 정상) ③ `verses` 1개 이상 ④ `verse_ref` 형식(`validate_traits.py`의 `REF_RE` 재사용) ⑤ `textKo`/`textEn` 프리베이크 완료(null 아님).
- `backend/scripts/validate_event_chronology.py` — Neo4j를 직접 읽어 연대 이상을 검출: (a) 인물 출생<활동<사망 서사 역전 (b) 사사 승계 순서 역전 (c) 대표 앵커(출애굽·아브라함 소명 등) 대비 역전 (d) 교정 창(-2200~-600) 내 rec 이벤트 목록화 (e) 형제군 고립 이탈(±150년, 전치 오타 후보) + Person 스캔(사망<출생·수명>1000년). 신학적 참여(예수↔창조 등)는 화이트리스트로 제외. `--json PATH`로 구조화 리포트도 저장한다.
- `backend/scripts/validate_god_reliance.py` — `data/god_reliance/*.json`(인물별 파일)이 AUTHORING.md 스키마를 지키는지: ① `mode`가 통제어휘 5종(`물음-응답`·`물음-침묵`·`독단-개입`·`독단-어긋남`·`부르심`) 안 ② `trigger.verse`/`outcome.verse`(있으면 `response.verse`도)가 정본 절 사전(`data/bible/verses.json`)에서 해석됨 ③ `obeyed`/`covenant`는 `mode=="부르심"`일 때만, 명령형·언약형 중 정확히 하나만 존재 ④ `approxYear` 정수 ⑤ `trigger`/`outcome` 라벨 결손 ⑥ `kind`는 물음 계열(`물음-응답`·`물음-침묵`) outcome에만 5값 통제어휘(`이룸`·`더하심`·`다르게`·`거절`·`침묵`) ⑦ 구 스키마(최상위 `verse`/`label`) 잔존 검출. 표본 6개 미만인 인물 목록도 별도 보고(실패는 아님).
- `backend/scripts/validate_chapter_sections.py`(task#212) — `data/chapter_sections/books.json`(다장권의 장 묶음, 목차 헤더용)이 규칙을 지키는지: ① 다장권(장 수≥2) 61권 전수 존재, 미지 bookId 없음 ② 각 권의 묶음이 연속·전수·비중첩(첫 시작=1, 끝=해당 권 총 장 수, 경계 연속) ③ 제목이 비어있지 않은 1~24자. 단장권 5권은 묶음 부재가 정상.
- `backend/scripts/validate_chapter_summaries.py`(task#206) — `data/chapter_summaries/books.json`(장별 한줄 요약+대표절)이 규칙을 지키는지: ① 66권 전수, 권별 장 수가 정본 절 사전(`data/bible/verses.json`에서 도출한 BB→최대 CCC)과 정확히 일치, 장 번호 1..N 연속 ② `summary`가 1~60자 한글 ③ `keyVerseId`(BBCCCVVV)가 정본 절 사전에 실존하고 그 권·그 장 소속.
- `backend/scripts/validate_quotations.py`(task#209) — `data/quotations/quotations.json`(구약↔신약 직접 인용 쌍)이 규칙을 지키는지: ① verseID 전수가 정본 절 사전에 실존 ② 측 위반 없음(NT측 verseID는 신약 권 BB≥40, OT측은 구약 권 BB≤39) ③ `rangeLabel`(예: "마 5:3-12") 파싱 결과가 `verseIds` 배열과 자기일치 ④ (`ntVerseIds`, `otVerseIds`) 조합 중복 쌍 0.
- 실행: `python3 backend/scripts/validate_<name>.py`. Neo4j를 읽는 검증기(`validate_event_chronology.py`)는 `NEO4J_PASSWORD` 환경변수 필요(`.env`에서 로드), 나머지는 `data/` JSON만 읽어 DB 접속 불필요.

---

## 2. 로더/빌더/inject 자체 검증

적재·산출 스크립트는 실행 직후 스스로 결과를 검증하거나 안전장치를 둔다.

- `backend/scripts/load_authored_genealogy.py` — 족보 사슬 적재 후 Cypher 도달성 검증: 사슬 끝(후손)에서 `CHILD_OF*`로 사슬 머리(조상)까지 연속인지 `EXISTS { ... }`로 확인하고, 끊겼으면 `raise SystemExit("FAIL: ... 사슬 단절")`.
- `backend/scripts/load_authored_mothers.py` — 어머니-자식 간선 적재(`MATCH` 전용 — 노드 신규 생성 없음) 후 `merged: n/len(pairs)` 건수를 대조, 불일치(노드 미존재 쌍)면 `raise SystemExit`. 멱등(`MERGE`), 그래프 초기화 후 재적재 대상.
- `backend/scripts/inject_date_corrections.py` — 에코 필드 가드(`CONVENTIONS.md` §3.4): DB 현재값이 에코와 불일치하면 스킵+`[WARN]`, 이미 새 값이면 조용히 통과. 멱등·재실행 안전. 결과를 "적용/이미 적용/스킵" 건수로 방출한다.
- `inject_*.py` 공통 — 적재 후 `MATCH ... WHERE <속성> IS NOT NULL RETURN count(...)`로 반영 건수를 `print`하고, 일부는 대표 노드를 샘플 출력해 육안 확인을 돕는다.
- `backend/scripts/build_word_distribution.py` — 산출 전 게이트 두 겹: ① `data/names_ko/books.json` 66권 `assert` ② 상위 단어 중 `data/word_sentiment.json` 미분류가 있으면 `sys.exit`(메시지로 `--dump-words` 안내) — 극성 큐레이션이 끝나야만 정본이 써진다.
- 대량 병렬 저작의 병합·재스캔 스크립트(`.forge/scratch/task203/validate_and_merge.py`·`rescan.py`, `.forge/scratch/genealogy-authoring/merge_validate.py`·`verify_tree*.py`)도 같은 원칙 — 저작 산출 JSON을 항목 단위로 기계검증한 뒤 정본에 반영, 마지막에 API 레벨 전수 재스캔으로 정합성을 닫는다.

---

## 3. 로컬 검증 = 빌드 후 확인 (footgun)

로컬에서 변경을 눈으로 확인하려면 **빌드가 선행**돼야 한다. `docker-compose.yml`이 다음을 강제한다:

- 프론트: nginx가 `./frontend/dist:/usr/share/nginx/html:ro`를 마운트한다 — HMR이 아니라 빌드 산출물을 서빙한다. 프론트 변경 확인 전 반드시 `cd frontend && npm run build`(`.env.production`의 `VITE_API_URL=/api` 자동 적용). 소스만 고치고 빌드를 빼먹으면 `localhost:8080`은 옛 화면을 계속 보여준다.
- 백엔드 데이터: `api`가 `./data:/app/data`를 마운트하므로 오버레이 JSON 변경은 재빌드 없이 반영되지만, 백엔드가 `@functools.lru_cache`로 기동 시 메모리 캐시한다(`CONVENTIONS.md` §3.1) → **`docker compose restart api`로 캐시를 비워야** 신규 데이터가 보인다. `docker compose up -d api`는 config 무변경 시 컨테이너를 재생성하지 않아 옛 데이터를 계속 서빙한다.
- 백엔드 코드: 코드 변경은 이미지 재빌드 필요 — `docker compose up -d --build api`.
- 브라우저 측 API 캐시(footgun 일부 해소): `frontend/src/api.js`의 `apiGet`이 모든 요청에 빌드 식별자 `?v=<BUILD_ID>`를 자동 부착해 배포 직후 브라우저가 `Cache-Control: max-age`가 걸린 옛 API 응답을 재사용하는 문제는 해소됐다. 남는 footgun은 백엔드 `lru_cache`(컨테이너 재기동 전까지 유지)뿐이다.
- 로컬 개발 서버(선택): README는 `python3 -m uvicorn backend.app.main:app --reload`(:8000)와 `npm run dev`(:5173)도 안내하나, 배포본과 동형으로 확인하려면 위의 dist 마운트 경로(:8080)를 쓴다.
- API만 먼저 확인할 땐 curl로 계약을 훑는다(예: `/api/words/{id}` 반환 형태, substring 매칭, 미지 book 404).

---

## 4. Playwright 화면 테스트

UI 동작 검증은 **Python Playwright**(sync API, `/opt/homebrew`에 설치)로 한다. 패턴: 네트워크 캡처 + 스크린샷으로 `localhost:8080`(또는 프로덕션 도메인)을 렌더 확인하고 **콘솔/네트워크 에러 0**을 확인한다. 프로덕션은 API `:8000`이 미노출이라 nginx `/api` 프록시를 거친다 — 검증도 `:8080` 기준.

### 4.1 스크립트 구조 관례

일회성 검증 스크립트는 `.forge/scratch/`에 둔다. 최근 관례는 **태스크별 하위 디렉터리**(`.forge/scratch/task202/`·`.forge/scratch/task203/`·`.forge/scratch/task210/`·`.forge/scratch/task211/`)에 스크립트와 스크린샷을 함께 모으는 것 — 전수 UAT `uat.py`, 개별 수정 검증 `*_verify.py`, 탐색용 `explore_*.py`/`debug*.py`가 공존한다. 스크린샷 산출물만 남고 검증 스크립트는 회수된 사례도 있다(`.forge/scratch/task210/`·`task211/`엔 데스크톱/모바일 스크린샷 6장씩만 잔존).

- `sync_playwright()` + `p.chromium.launch(headless=True)` + `browser.new_page(viewport={...})`. 전수 UAT는 뷰포트 dict를 상수로 — `.forge/scratch/task202/uat.py`의 `VIEWPORTS = {"mobile": 393×852, "desktop": 1280×800}` 스타일.
- 진입은 `page.goto(BASE, wait_until='networkidle', timeout=15000)` 후 `page.wait_for_timeout(...)`으로 렌더 안정화.
- 요소 조작은 한글 표시 텍스트 기준 `page.get_by_text('타임라인', exact=True).first.click()`. 오버레이(SidePanel 등)가 시각적으로 덮어 실제 클릭이 막히는 요소는 `el.evaluate('el => el.click()')`로 JS 직접 디스패치.
- **지도 위 좌표 클릭**: MapLibre 마커는 DOM 셀렉터로 못 잡는다 — `uat.py`의 `MAP_HELPER_JS`가 React fiber를 스캔해 map 인스턴스를 `window.__map`에 노출하고, `map.project([lng, lat])` + 캔버스 rect로 화면 좌표를 계산해 `page.mouse.click(x, y)`한다.
- 시나리오 단계마다 `page.screenshot(path=...)` + `print`로 진행 방출. 사이트×뷰포트 전수 UAT는 `<site>-<viewport>.png`로 저장하고 **실패 시 `<site>-<viewport>-ERROR.png`**를 따로 남긴다.
- 텍스트 특정 함정: "외 2권" 같은 부분 텍스트만으로 칩을 특정하면 같은 문구의 다른 행이 먼저 매치된다 — 사건명 등으로 **행을 먼저 특정한 뒤 행 내부에서** 클릭한다(`xpath=following::button[...]` 체이닝은 `uat.py` 참조).

### 4.2 뷰포트 = 데스크톱 + 모바일

- 디자인/레이아웃 지적은 대개 실폰(배포본) 기준이므로 뷰포트를 먼저 확정하고 시나리오에 **모바일 폭을 반드시 포함**한다. 최근 실측 조합: 데스크톱 1280(×800/900) + 모바일 390~393. task#210(인용 관계 UI)·task#211(정경 순서 내비)도 각각 데스크톱/모바일 두 폭 스크린샷을 남겼다.
- SPA 특성상 URL(딥링크)마다 **새 브라우저 컨텍스트**로 여는 것이 안전하다 — 같은 페이지에서 해시만 바꾸면 상태가 오염된다.
- **모바일 전용 UI(바텀시트 등)의 UAT엔 "긴 콘텐츠 스크롤 후 조작" 케이스를 반드시 포함**한다 — 개폐·ESC만 확인한 전수 UAT가 통과하고도 스크롤 상호작용 결함이 실기기 피드백으로 돌아온 실사례가 있다. 터치 제스처는 Playwright 합성 디스패치에서 이벤트가 한 태스크에 몰려 state 클로저 레이스가 재현된다 — 판정 로직이 ref를 쓰는지 확인한다.

### 4.3 테마 검증 = localStorage `biblemap-theme` 주입

- 앱 테마는 CSS `prefers-color-scheme`이 아니라 localStorage `biblemap-theme` + `documentElement.dataset.theme`으로 구동된다(`frontend/src/main.jsx`, ADR-0020). 따라서 Playwright의 `color_scheme='light'`는 **무효** — 헛통과 footgun.
- 라이트 테마 강제는 페이지 로드 전 init script로 키를 주입한다:
  ```python
  page.add_init_script("localStorage.setItem('biblemap-theme', 'light')")
  page.goto(BASE, wait_until='networkidle')
  ```
- 테마가 얽힌 UI 변경은 두 테마 × 데스크톱/모바일 매트릭스로 스크린샷 검수한다.

### 4.4 모션 검증 매트릭스 (ADR-0024)

모션 토큰(`CONVENTIONS.md` §5.3) 도입 이후의 화면 검증은 §4.2~4.3의 테마×뷰포트 매트릭스에 **reduced-motion on/off** 축을 더한 3축 매트릭스로 짠다.

- Playwright의 `page.emulate_media(reduced_motion='reduce')`로 강제하고, 다크/라이트 × 데스크톱/모바일 × reduce on/off 조합을 화면별 판정 항목 단위로 통과시킨다.
- 헤드리스 크로미움은 소프트웨어 GL(SwiftShader)로 렌더링해 MapLibre 캔버스 위 오버레이가 부분 페인트되는 아티팩트를 낼 수 있어 앱 버그로 오인하기 쉽다. `chromium.launch(args=["--enable-gpu", "--use-angle=metal"])`(macOS 기준) 같은 GPU 플래그 A/B 비교를 최우선 1분 테스트로 돌려 환경 아티팩트인지 앱 회귀인지부터 가른다.
- 배포 직후 검증인데 옛 화면이 남아 있으면, `api.js`의 자동 `?v=<BUILD_ID>` 캐시버스터가 실제로 최신 빌드값을 싣고 있는지부터 네트워크 캡처로 확인한다.
- 애니메이션 상태 판정(요소 등장 여부)은 스크린샷과 함께 `print(f'{label} >> visible={loc.is_visible()}')` 류의 텍스트 라인으로 방출해 매트릭스 각 항목의 PASS/FAIL을 로그로 남긴다.
- reduced-motion 판정은 **토큰 붕괴(1ms) 직후 최소 1프레임 뒤에 샘플링**한다 — 같은 프레임에서 즉시 읽으면 전환이 끝나기 전 값을 관측해 오탐할 수 있다.
- 세션 1회 재생 스태거(카드 `card-in`·책 펼침 `book-open`)는 같은 브라우저 컨텍스트에서 페이지에 두 번 진입시켜, 두 번째 진입에 해당 클래스/애니메이션이 재생되지 않음을 확인한다.

### 4.5 저작 검증 흐름 예

`data/person_relations/AUTHORING.md` §8: `/api/persons/curated`로 node_id 확보 → `/api/person/{node_id}/relations`가 국면을 반환하는지 확인 → Playwright로 화면 렌더 확인. 인용 관계(task#209/210)도 동형: `/api/book/{id}/quotations`(또는 대응 엔드포인트)로 데이터 반환 확인 → SidePanel 인용 섹션 렌더를 Playwright로 확인.

---

## 5. 저작 → 검증 파이프라인 (정본 순서)

`data/person_relations/AUTHORING.md` §8이 정리한, 저작 후 반드시 밟는 순서:

1. `python3 backend/scripts/generate_verse_text.py` — 멱등, 본문+문맥 프리베이크(getbible UA 우회 내장).
2. (아이콘/프론트 자원 추가 시) `cd frontend && npm run build` — dist 마운트라 빌드 필수.
3. `docker compose restart api` — lru_cache 캐시 비우기(위 §3).
4. API 엔드포인트로 데이터 반환 확인.
5. Playwright로 `localhost:8080` 렌더 확인, 콘솔/네트워크 에러 0.

성품·연대·의존도·인용·장 개요/묶음 같은 규칙 데이터는 이 앞에 해당 `validate_*.py`(위 §1)를 돌려 위반 0을 확인한 뒤 반영한다. 단어 분포는 `build_word_distribution.py`(자체 게이트, 위 §2)로 정본을 재산출한 뒤 3~5를 밟는다. 그래프 초기화 후 재적재 시엔 `load_theographic.py` 다음에 `load_authored_genealogy.py`·`load_authored_mothers.py`도 재실행해야 저작 간선이 복원된다.

---

## 6. CI / 배포 게이트

- `.github/workflows/deploy.yml` — `main` push 시 self-hosted 러너에서 `git reset --hard origin/main` 후 `bash deploy.sh`. **테스트 스텝은 없다** — 검증은 저작 시점의 `validate_*`·Playwright에 위임한다.
- `deploy.sh` 게이트: ① `npm install` + `npm run build`(프론트) ② `docker compose build api` ③ `docker compose up -d api nginx` ④ `inject_ko_names.py`를 Neo4j 준비까지 최대 15회 재시도하고, 끝내 실패하면 배포를 `exit 1`로 중단한다. lock 파일로 동시 배포를 막는다. `deploy.sh`는 `load_*`를 실행하지 않는다 — 그래프 적재는 저작 시점 수동.
- 배포 후 확인은 `gh run list`(success)로. 배포 무음 실패(백엔드가 옛 코드) 의심 시엔 폴러보다 러너부터 확인한다(글로벌 CLAUDE.md 인프라 격리 규칙).
