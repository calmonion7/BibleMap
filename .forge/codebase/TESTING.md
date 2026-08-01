---
last_mapped_commit: 43f987cb37c2341c3cfeb54e4cf4dc33b4549c64
mapped: 2026-08-01
---

# TESTING

BibleMap이 정확성을 검증하는 방식. 이 프로젝트에는 **정식 유닛 테스트 프레임워크가 없다** — 검증은 (1) 배포 전 단일 게이트 `scripts/check.sh`, (2) 데이터 기계검증 스크립트 `backend/scripts/validate_*.py`, (3) 로더/빌더/inject의 자체 검증과 인라인 assert, (4) 커밋되지 않는 ephemeral 정합 감사, (5) Python Playwright 화면 검증, (6) 배포 파이프라인 게이트로 이뤄진다.

---

## 0. 정식 테스트 프레임워크 부재

- pytest·unittest·vitest·jest 없음. `*_test.py`·`*.test.jsx`·`*.spec.*`·`conftest.py` 파일이 리포지토리에 **하나도 없다**(`git ls-files | grep -iE "test|spec|conftest"` 결과가 이 문서 자신뿐).
- 백엔드 `backend/requirements.txt`는 `fastapi`/`neo4j`/`uvicorn` 3줄이고, 프론트 `frontend/package.json`의 `devDependencies`엔 테스트 러너·`@testing-library`·`@playwright/test`가 없다. Playwright는 npm이 아니라 **호스트 Python**(`/opt/homebrew/lib/python3.14/site-packages/playwright`)에 설치돼 있다(§5).
- 프론트의 유일한 정적 게이트는 ESLint(`CONVENTIONS.md` §8) — 커밋 `43f987c` 기준 `npm run lint`·`npx eslint src` 모두 0 error / 0 warning.
- 즉 "테스트를 돌린다"의 실체는 **`bash scripts/check.sh`**(§1)와 §5의 Playwright 화면 검증이다.

---

## 1. `scripts/check.sh` — 배포 전 검증 게이트 (AI 불요 CI 게이트)

task#255에서 흩어져 있던 검증을 단일 엔트리로 묶은 스크립트. **`deploy.sh`가 데이터 주입·`npm install` 다음, 프론트 빌드보다 앞에서 `CHECK_STRICT=1`로 호출**하며 단독 실행도 가능하다.

```
bash scripts/check.sh                 # 리포지토리 어디서 실행해도 자기 위치로 ROOT 유도
CHECK_STRICT=1 bash scripts/check.sh  # 엄격 모드 — 환경 미충족 스킵을 실패로 승격(배포 경로)
```

- **구성 3블록**
  1. **파일 기반 데이터 검증 13종** — `python3 -m backend.scripts.validate_<name>` 모듈 실행으로 순서대로: `covenants` · `messianic_prophecies` · `parables_miracles` · `topical_verses` · `pm_map_coverage` · `scene_coverage` · `chapter_sections` · `chapter_summaries` · `quotations` · `person_context` · `god_reliance` · `traits` · `era_bands_consistency`. 전부 **하드 게이트**(DB·네트워크 불요).
  2. **ESLint** — `frontend/node_modules`가 있으면 `npx --no-install eslint src`, 없으면 `⊘ 스킵` 경고(엄격 모드에서는 `✗ 실패`).
  3. **연대 정합(Neo4j)** — `.env`를 `set -a`로 로드한 뒤 `127.0.0.1:7687` 소켓 연결이 되면 `python3 -m backend.scripts.validate_event_chronology`, 미기동이면 `⊘ 스킵`(엄격 모드에서는 `✗ 실패`).
- **출력 계약**: 항목마다 `  ✓ <라벨>` / `  ✗ <라벨>` + 실패 시 출력 마지막 8줄. 하나라도 실패하면 `=== check FAILED ===` 후 `exit 1`, 전부 통과면 `=== check PASS ===` 후 0.
- **환경 의존 항목만 스킵-경고**, 파일 기반 검증은 절대 스킵하지 않는다(스크립트 상단 주석의 설계 계약).
- **`CHECK_STRICT` 계약(task#259)** — 참이면 위 두 스킵 분기가 `skip()` 헬퍼를 통해 `✗ … (CHECK_STRICT: 스킵 불가)` + `fail=1`이 된다. **`check PASS`가 "전 검사를 실제로 통과했다"를 뜻하는 건 엄격 모드일 때뿐이다.** 미설정 시 스킵-경고 동작은 그대로 — Neo4j 없이 파일 검증만 돌리는 단독 개발 실행이 정당한 용법이기 때문(ADR `260801-195022`).
- **신규 `validate_*.py`를 만들면 반드시 `scripts/check.sh`의 목록에도 등록한다** — 안 하면 게이트가 잡지 못한다(`.forge/retro/260724-111705-predeploy-validation-gate.md`). 현재 `backend/scripts/validate_*.py`는 14개이며 13개(파일 기반) + 1개(Neo4j)로 **전수가 게이트에 등록돼 있다**.
- **배포 footgun**: `deploy.sh`가 `check.sh`를 호출하므로 신규 스크립트는 **`deploy.sh` 변경과 반드시 함께 커밋**한다. 러너 체크아웃에 파일이 없으면 게이트가 파일 부재로 배포를 막는다.
- 실측(2026-08-01, task#259, Neo4j 기동 상태): `CHECK_STRICT=1`로 15개 항목 전부 `✓`, `check PASS`. `frontend/node_modules`가 없는 트리에서는 미설정 시 `⊘` + `check PASS`(exit 0), `CHECK_STRICT=1`은 `✗ eslint src` + `check FAILED`(exit 1).

---

## 2. 기계검증 스크립트 (`backend/scripts/validate_*.py`)

데이터 저작이 규칙을 지키는지 확인하는 결정적 검증기. **공통 계약**: 위반 목록을 `print`하고 위반이 있으면 `sys.exit(1)`, 없으면 `PASS`/`OK — 위반 0` 계열 메시지. 위반 항목만 거부하고 나머지는 통과시키는 **항목 단위 게이트**가 원칙(`CONVENTIONS.md` §6).

| 스크립트 | 대상 | 검사 요지 |
| --- | --- | --- |
| `validate_traits.py` | `data/character_traits/people.json` | 라벨이 통제 어휘(`VIRTUES` 24·`FLAWS` 8) 안 · 인물당 2~5개·중복 없음 · `verse_ref`가 `REF_RE` 만족 · 필드 결손 |
| `validate_person_context.py` | `data/person_context/people.json` | 인물 수 ≥ `MIN_COUNT`(86) · `role` 비어있지 않음·≤80자 · `intro`는 있으면 ≤300자(족보 단역은 부재 정상, ADR-0027) · `verses` ≥1 · `verse_ref` 형식(`validate_traits.REF_RE` 복제) · `textKo`/`textEn` 프리베이크 완료 |
| `validate_god_reliance.py` | `data/god_reliance/*.json` | `mode` 5종 통제어휘 · `trigger.verse`/`outcome.verse`(+있으면 `response.verse`)가 정본 절 사전에서 해석됨 · `obeyed`/`covenant`는 `부르심` 전용·택일 · `approxYear` 정수 · 라벨 결손 · `kind`는 물음 계열 outcome에만 5값 · 구 스키마 잔존. 표본 6건 미만(`LOW_SAMPLE`) 인물은 실패가 아닌 별도 보고 |
| `validate_chapter_summaries.py` | `data/chapter_summaries/books.json` | 66권 전수 · 권별 장 수가 정본 절 사전에서 도출한 BB→최대 CCC와 일치·장 번호 연속 · `summary` 1~60자 한글 · `keyVerseId`가 실존하며 그 권·그 장 소속 |
| `validate_chapter_sections.py` | `data/chapter_sections/books.json` | 다장권(장 수≥2) 61권 전수·미지 bookId 없음 · 묶음이 연속·전수·비중첩(첫 시작=1, 끝=총 장 수) · 제목 1~24자. 단장권 5권은 부재가 정상 |
| `validate_quotations.py` | `data/quotations/quotations.json` | verseID 전수 실존 · 측 위반 없음(NT측 BB≥40, OT측 BB≤39) · `rangeLabel` 파싱 결과가 `verseIds`와 자기일치 · (`ntVerseIds`,`otVerseIds`) 중복 쌍 0 |
| `validate_messianic_prophecies.py` | `data/messianic_prophecies/prophecies.json` | `otVerseIds`/`ntVerseIds` 전수 실존 · `otRangeLabel`/`ntRangeLabel`(별칭은 `names_ko/books.json`) 자기일치 · 쌍마다 ot·nt ≥1 + `theme` 존재 · `id` 유일 · 쌍 수 20~30 |
| `validate_topical_verses.py` | `data/topical_verses/topics.json` | 주제 수 10~14 · 주제당 `verseIds` ≥3 · verseID 전수 실존 · `id` 유일 |
| `validate_parables_miracles.py` | `data/jesus_parables_miracles/index.json` | `verseIds` 전수 실존 · `type` ∈ {`parable`,`miracle`} · `placeId`가 있으면 `place_coords`에 실존 · `id` 유일 · 비유 25~35 · 기적 25~40 |
| `validate_pm_map_coverage.py` | 위 색인 ↔ `data/place_coords/places.json` | **지도↔연표 커버리지 간극 고정**. `/parables-miracles`(`backend/app/routes/events.py`)와 동일한 mappable 판정으로 좌표 없는 항목 집합을 계산해 `EXPECTED_UNMAPPABLE`(17건 정본)과 대조 — 예상 밖 누락(회귀)·이제 뜨는 항목·해석 안 되는 `placeId`를 각각 `assert`로 잡는다 |
| `validate_scene_coverage.py` | `data/tours/*.json` ↔ `frontend/src/sketches/*.jsx` ↔ `tourSketches.jsx` | **투어 정차지↔장면 스케치 양방향 커버리지**. 정차지 `stops[].id` 집합과 스케치 레지스트리 키(좁은 정규식 `'authored-…':`)를 대조해 (a) 미저작 정차지(`EXPECTED_UNCOVERED` 허용목록, 현재 비어 있음) (b) 정차지에 없는 고아 키 (c) 허용목록 잔존 (d) **`tourSketches.jsx`에 import·스프레드되지 않은 모듈**을 `assert`로 잡는다. (d)가 없으면 키는 있는데 앱은 아무것도 렌더하지 않는 구멍이 통과한다 |
| `validate_covenants.py` | `data/covenants/covenants.json` | 언약 수 5~6 · `keyVerseIds` 전수 실존 · `startDate` `int()` 파싱 가능 |
| `validate_era_bands_consistency.py` | 소스 3곳 + `covenants.json` | `frontend/src/TimelineView.jsx`의 `ERA_BANDS` · `backend/app/routes/stats.py`의 `ERA_BANDS` · `backend/app/routes/persons.py`의 `_ERA_ORDER`를 **정규식으로 파싱**해 이름·순서·경계 일치를 단언하고, `covenants.json`의 `era`가 유효 시대인지 확인(`CONVENTIONS.md` §4.3). `-Infinity`(JS)/`float("-inf")`(Py) 정규화 주의 |
| `validate_event_chronology.py` | **Neo4j 직독** | (a) 인물 출생<활동<사망 서사 역전 (b) 사사 승계 순서(삿 10–12장) 역전 (c) 대표 앵커(출애굽 -1446·아브라함 소명 -2091·가뭄 선포 -870) 대비 역전 (d) 교정 창(-2200~-600) 내 `rec` 이벤트 목록화 (e) 형제군 ±150년 고립 이탈(전치 오타 후보) + Person 스캔(사망<출생·수명>1000년). 신학적 참여는 `THEOLOGICAL_WHITELIST`로 제외. `--json PATH`로 구조화 리포트 저장 |

- **공통 계약의 예외 4건** — `validate_covenants.py`·`validate_pm_map_coverage.py`·`validate_scene_coverage.py`·`validate_era_bands_consistency.py`는 위반 목록을 모으지 않고 **`assert`로 첫 위반에서 즉시 중단**한다(통과 시 `PASS` 출력). 항목 열거가 필요 없는 소규모/집합 대조 검증에 쓰는 변형.
- **실행 방법 두 가지**: `python3 backend/scripts/validate_<name>.py`(문서·AUTHORING.md 표기)와 `python3 -m backend.scripts.validate_<name>`(`scripts/check.sh` 표기). 새 검증기는 둘 다 동작해야 한다.
- **환경 요구**: `validate_event_chronology.py`만 `NEO4J_PASSWORD`(+선택 `NEO4J_URI`/`NEO4J_USER`)가 필요하다 — 나머지는 `data/` JSON과 소스 파일만 읽어 DB 접속 불요.
- 검증기가 참조하는 **정본 절 사전은 `data/bible/verses.json`** 하나다(verseID 실존 확인의 공통 기준, `CONVENTIONS.md` §6.2).

---

## 3. 로더/빌더/inject 자체 검증과 인라인 assert

적재·산출 스크립트는 실행 직후 스스로 결과를 검증하거나 안전장치를 둔다(`CONVENTIONS.md` §3의 종료 코드 규약).

- `backend/scripts/load_authored_genealogy.py:74` — 족보 사슬 적재 후 Cypher 도달성 검증(`EXISTS { ... CHILD_OF* ... }`), 끊겼으면 `raise SystemExit("FAIL: ... 사슬 단절")`.
- `backend/scripts/load_authored_mothers.py:46` — 어머니-자식 간선(`MATCH` 전용, 노드 신규 생성 없음) 적재 후 `merged: n/len(pairs)` 건수 대조, 불일치면 `raise SystemExit`. `MERGE`라 멱등.
- `backend/scripts/load_books.py:72~76` — **리포지토리에서 유닛 테스트에 가장 가까운 형태**: `_parse_year()`의 모듈 최상단 셀프체크 assert 5줄(`"-1451-01"→-1451`, `"0049-10-01"→49`, `"-4003"`, `"30"`, `""→None`). 주석이 "월/일 정밀도가 `int()`로 조용히 누락되던 버그(task#151 #2) 회귀 방지"를 명시하며, import만 해도 실행된다.
- `backend/scripts/build_word_distribution.py` — 산출 전 게이트 두 겹: ① `data/names_ko/books.json` 66권 `assert` ② 상위 단어 중 `data/word_sentiment.json` 미분류가 있으면 `sys.exit`(메시지로 `--dump-words` 안내). 극성 큐레이션이 끝나야만 정본이 써진다.
- `backend/scripts/generate_bible_text.py:100~101` — 프리베이크 결과에 대한 키워드 스팟체크 `assert`(ko/en 각각).
- `backend/scripts/apply_event_dedupe.py:193~194` — 삭제 후 `removed id` 잔존 0 · `after == before - deleted` 건수 등식 `assert`.
- `backend/scripts/inject_date_corrections.py` — 에코 필드 가드(`CONVENTIONS.md` §6.4). 결과를 "적용/이미 적용/스킵" 건수로 방출한다. **건수 해석 주의**(task#238 학습): 라벨만 안 바뀐 교정(`old == newStartDate`)도 매 실행 동일값 `SET`으로 "적용"에 잡히므로 **회귀 신호는 스킵/경고 건수만 본다** — "적용 건수 증가"는 회귀 판정 근거가 아니다.
- `inject_*.py` 공통 — 적재 후 `MATCH ... WHERE <속성> IS NOT NULL RETURN count(...)`로 반영 건수를 `print`하고, 일부는 대표 노드를 샘플 출력해 육안 확인을 돕는다.
- 대량 병렬 저작의 병합·재스캔 스크립트(`.forge/scratch/task203/validate_and_merge.py`·`rescan.py`, `.forge/scratch/genealogy-authoring/merge_validate.py`·`verify_tree*.py`)도 같은 원칙 — 저작 산출 JSON을 항목 단위로 기계검증한 뒤 정본에 반영하고, 마지막에 API 레벨 전수 재스캔으로 닫는다.

---

## 4. 정합 감사 — ephemeral API assert · 앵커 산술 · 커버리지 등식

대량 연대 교정·투어 커버리지 보강 같은 감사성 작업에서 반복되는, `validate_*.py`로 커버되지 않는 3가지 관행. **대체로 리포지토리에 커밋되지 않는다** — 태스크 중 즉석으로 작성해 실행하고 버린다.

- **API assert 스크립트**: 실행 중인 API(`/events`·`/tour/{id}`·`/person/{id}/events` 등)를 호출해 알려진 연대·순서 관계("이삭 출생 < 모리아", "오순절 > 승천")를 개별 assert로 판정하는 일회성 스크립트. 회고 실측 규모: 전역 타임라인 17~20건, 9투어 275정차지 단조성·인접 동률 0건, 인물 연표 4~5명. `validate_event_chronology.py`가 **구조적 이상을 자동 스캔**하는 것과 달리, 이쪽은 그 감사에서 도출된 **특정 known-good 관계**를 하나씩 확인하는 손저작 체크리스트다.
- **앵커 산술 감사**: 3축 판정 — ① 파일 내 서사 순서 ② 파일 간 동일 장면 정합 ③ **정본 앵커 체인 대비 절대값 대조**(성전 966 → 출애굽 1446 → 애굽 이주 1876 → 야곱 2006 → 이삭 2066 → 아브라함 2091, 창 47:9·왕상 6:1 등 성경 내부 연산으로 도출). 핵심 교훈: ①·②만으로는 파일 전체가 통째로 오프셋된 이탈을 못 잡는다 — 절대 앵커 대조가 있어야 드러난다.
- **커버리지 등식 게이트**: 대량 삽입/저작에서 "잔여 = 제외 목록"이 산술적으로 맞는지 확인하는 집합 대조. 투어 정차지 보강(165→275/306)에서 "채택"인데 삽입 목록에 없던 1건을 이 등식이 잡았다. 같은 원리를 **영속화한 사례**가 `backend/scripts/validate_pm_map_coverage.py`의 `EXPECTED_UNMAPPABLE`(§2) — 반복 회귀 위험이 있는 커버리지 간극은 ephemeral로 두지 말고 정본 집합으로 고정해 게이트에 등록한다. `frontend/src/sketches/`의 장면 스케치 커버리지(투어 `stops`의 id ⊆ 레지스트리 키)도 아직 스크립트화되지 않은 같은 유형의 대조다.

---

## 5. Playwright 화면 검증

UI 동작 검증은 **Python Playwright**(sync API, `/opt/homebrew`의 Python 3.14에 설치)로 한다. 패턴: 네트워크 캡처 + 스크린샷으로 `localhost:8080`을 렌더 확인하고 **콘솔/네트워크 에러 0**을 확인한다. 프로덕션은 API `:8000`이 미노출이라 nginx `/api` 프록시를 거친다 — 검증도 `:8080` 기준. 역할 계약은 `.claude/agents/ui-verifier.md`(읽기 전용, 소스 수정 금지)에 고정돼 있다.

### 5.1 스크립트·산출물 배치

- 일회성 검증 스크립트는 `.forge/scratch/`에 둔다(`task246_screenshots.py`·`covenant_timeline_shots.py`·`task158_screenshots.py`, 그리고 태스크별 하위 디렉터리 `.forge/scratch/task202/`~`task211/`).
- **스크린샷 산출물은 `.forge/reports/`에 저장하는 것이 현행 관례**다(`.claude/agents/ui-verifier.md`가 명시; `task246_screenshots.py`의 `OUT_DIR = '.../.forge/reports'`). 과거 태스크는 `.forge/scratch/task2NN/`에 스크린샷을 함께 뒀다 — 옛 디렉터리는 그대로 두고 신규는 `reports/`로.
- 파일명은 `<주제>-<뷰포트>.png`(`messianic-thread-desktop.png`·`covenant-timeline-mobile.png`) 또는 `<주제>-<테마>-<장면>.png`(`intro-film-light-map.png`). 전수 UAT는 실패 시 `<site>-<viewport>-ERROR.png`를 따로 남긴다.

### 5.2 스크립트 구조 관례

- `sync_playwright()` + `p.chromium.launch(headless=True)` + `browser.new_page(viewport={...})`. 뷰포트 dict는 상수로(`VIEWPORTS = {"mobile": 393×852, "desktop": 1280×800}` 스타일).
- 진입은 `page.goto(BASE, wait_until='networkidle', timeout=15000)` 후 `page.wait_for_timeout(...)`으로 렌더 안정화. 애니메이션이 있는 화면은 draw-on/입장 모션이 끝날 시간을 기다린 뒤 캡처한다(인장 draw 1초, 카메라 정착 400ms, 스케치 패널 450ms).
- 요소 조작은 한글 표시 텍스트 기준 `page.get_by_text('타임라인', exact=True).first.click()`. 오버레이(SidePanel 등)가 시각적으로 덮어 실제 클릭이 막히는 요소는 `el.evaluate('el => el.click()')`로 JS 직접 디스패치.
- **지도 위 좌표 클릭**: MapLibre 마커는 DOM 셀렉터로 못 잡는다 — `.forge/scratch/task202/uat.py`의 `MAP_HELPER_JS`가 React fiber를 스캔해 map 인스턴스를 `window.__map`에 노출하고, `map.project([lng, lat])` + 캔버스 rect로 화면 좌표를 계산해 `page.mouse.click(x, y)`한다.
- 시나리오 단계마다 `page.screenshot(path=...)` + `print`로 진행 방출. 애니메이션 상태 판정은 `print(f'{label} >> visible={loc.is_visible()}')` 류 텍스트 라인으로 매트릭스 각 항목의 PASS/FAIL을 로그에 남긴다.
- 텍스트 특정 함정: "외 2권" 같은 부분 텍스트만으로 칩을 특정하면 같은 문구의 다른 행이 먼저 매치된다 — 사건명 등으로 **행을 먼저 특정한 뒤 행 내부에서** 클릭한다.

### 5.3 뷰포트 = 데스크톱 + 모바일 (필수)

- 디자인·레이아웃 지적은 대개 실폰(배포본) 기준이다. `maxWidth` 중앙정렬류 수정은 데스크톱만 먹으므로 **모바일 폭을 반드시 포함**한다. 실측 조합: 데스크톱 1280×800(또는 ×900) + 모바일 390×844 / 393×852.
- SPA 특성상 **URL(딥링크)마다 새 브라우저 컨텍스트/페이지**로 여는 것이 안전하다 — 같은 문서에서 해시만 바꾸면 스테이지가 리마운트되지 않아 상태가 오염된다.
- 딥링크 정본 목록은 `frontend/src/urlState.js` 주석과 `.claude/agents/ui-verifier.md`에 있다.
- **모바일 전용 UI(바텀시트 등)의 UAT엔 "긴 콘텐츠 스크롤 후 조작" 케이스를 반드시 포함**한다 — 개폐·ESC만 확인한 전수 UAT가 통과하고도 스크롤 상호작용 결함이 실기기 피드백으로 돌아온 실사례가 있다. 터치 제스처는 Playwright 합성 디스패치에서 이벤트가 한 태스크에 몰려 state 클로저 레이스가 재현된다 — 판정 로직이 ref를 쓰는지 확인한다.
- **정렬/그룹핑 UI 검증은 API assert(§4)만으론 불충분**: 데이터가 정합해도 렌더 순서가 뒤집힐 수 있다. 실사례(task#238) — `TimelineView`가 `startDate`를 문자열 그대로 그룹핑해 표기 차이("0030" vs "30")만으로 같은 시점이 갈라졌고, API assert는 통과했지만 스크린샷으로만 드러났다. 연대·순서가 걸린 검증엔 항상 실제 렌더 스크린샷을 포함한다.
- **지도 프레이밍처럼 "육안이 유일 판정"인 버그는 before/after 캡처로 확증**한다(task#251): 대상 파일만 `git stash` → 빌드 → 캡처 → 복원 → 수정본 캡처. 프론트 빌드가 ~200ms대라 저렴하다.

### 5.4 테마 검증 = localStorage `biblemap-theme` 주입

- 앱 테마는 CSS `prefers-color-scheme`이 아니라 localStorage + `documentElement.dataset.theme`으로 구동된다(`frontend/src/main.jsx`, ADR-0020). 따라서 Playwright의 `color_scheme='light'`는 **무효** — 헛통과 footgun.
- 라이트 강제는 페이지 로드 **전** init script로:
  ```python
  page.add_init_script("localStorage.setItem('biblemap-theme', 'light')")
  page.goto(BASE, wait_until='networkidle')
  ```
- 인트로 노출/스킵도 같은 방식으로 제어한다 — `localStorage.setItem('biblemap-intro', 'off')`이면 허브로 바로 진입(키 부재가 기본=인트로 노출, `CONVENTIONS.md` §7.2).

### 5.5 모션 검증 매트릭스 (ADR-0024)

모션 토큰 도입 이후의 화면 검증은 §5.3~5.4의 테마×뷰포트에 **reduced-motion on/off** 축을 더한 3축 매트릭스로 짠다.

- `page.emulate_media(reduced_motion='reduce')`로 강제하고 다크/라이트 × 데스크톱/모바일 × reduce on/off를 화면별 판정 항목 단위로 통과시킨다(`.forge/reports/intro-film-*-reduced.png`가 실측 산출물).
- 헤드리스 크로미움은 소프트웨어 GL(SwiftShader)로 렌더링해 MapLibre 캔버스 위 오버레이가 부분 페인트되는 아티팩트를 낼 수 있다 — `chromium.launch(args=["--enable-gpu", "--use-angle=metal"])`(macOS) A/B 비교를 최우선 1분 테스트로 돌려 환경 아티팩트인지 앱 회귀인지부터 가른다.
- reduced-motion 판정은 **토큰 붕괴(1ms) 직후 최소 1프레임 뒤에 샘플링**한다 — 같은 프레임에서 즉시 읽으면 전환 종료 전 값을 관측해 오탐한다.
- 세션 1회 재생 스태거(`card-in`·`book-open`)는 같은 컨텍스트에서 페이지에 두 번 진입시켜 두 번째엔 재생되지 않음을 확인한다.
- **자동재생 검증 대기는 최대 stepDuration을 넘겨야 한다** — `frontend/src/useTourPlayback.js`의 `stepDuration()`은 4000ms + note 길이×35(최대 +4000) = **최대 8초**다. 6초 대기로 "미진행" 거짓경보를 낸 실사례가 있다(task#253). 재생 로직 리팩터는 자동진행·수동 next/prev·종료 개요복원까지 Playwright 전수로 확인한다.
- 배포 직후 검증인데 옛 화면이 남아 있으면, `api.js`의 자동 `?v=<BUILD_ID>` 캐시버스터가 실제로 최신 빌드값을 싣고 있는지 네트워크 캡처로 확인한다.

---

## 6. 로컬 검증 전제 = 빌드·재시작·재적재 (footgun)

로컬에서 변경을 눈으로 확인하려면 선행 조건이 있다. `docker-compose.yml`이 이를 강제한다.

- **프론트**: nginx가 `./frontend/dist:/usr/share/nginx/html:ro`를 마운트한다 — HMR이 아니라 빌드 산출물을 서빙. 확인 전 반드시 `cd frontend && npm run build`(`.env.production`의 `VITE_API_URL=/api` 자동 적용). 소스만 고치고 빌드를 빼먹으면 `localhost:8080`은 옛 화면을 계속 보여준다.
- **백엔드 데이터**: `api`가 `./data:/app/data`를 마운트해 오버레이 JSON은 재빌드 없이 반영되지만, 백엔드가 `@functools.lru_cache`로 메모리 캐시한다 → **`docker compose restart api`로 캐시를 비워야** 신규 데이터가 보인다. `docker compose up -d api`는 config 무변경 시 컨테이너를 재생성하지 않아 옛 데이터를 계속 서빙한다.
- **백엔드 코드**: 이미지 재빌드 필요 — `docker compose up -d --build api`.
- **라우트별 데이터 소스가 다르다**(task#236 학습): 인물 여정·투어·장소 라우트는 오버레이 JSON을 직독하므로 `restart api`로 충분하지만, **전역 타임라인 `/events`는 Neo4j를 직접 읽는다** — `data/person_events/`를 교정해도 `restart api`로는 반영되지 않고 **`python3 backend/scripts/load_person_events.py` 재실행이 필수**다(멱등, `MERGE+SET`). 연대 교정처럼 여러 라우트에 걸친 검증은 라우트마다 데이터 소스(JSON 직독 vs Neo4j)를 먼저 확인한다.
- **브라우저 측 API 캐시**는 해소돼 있다 — `frontend/src/api.js`의 `apiGet`이 모든 요청에 `?v=<BUILD_ID>`를 자동 부착한다. 남는 footgun은 백엔드 `lru_cache`(컨테이너 재기동 전까지 유지)뿐.
- **로컬 개발 서버(선택)**: README는 `python3 -m uvicorn backend.app.main:app --reload`(:8000)와 `npm run dev`(:5173)도 안내하나, 배포본과 동형으로 확인하려면 dist 마운트 경로(:8080)를 쓴다.
- API만 먼저 확인할 땐 curl로 계약을 훑는다(반환 형태·substring 매칭·미지 id 404).

---

## 7. 저작 → 검증 파이프라인 (정본 순서)

데이터 저작 후 밟는 순서(`data/person_relations/AUTHORING.md` 저작 절차 + `.claude/agents/data-author.md` 반영 절차):

0. 해당 `backend/scripts/validate_*.py`(또는 통째로 `bash scripts/check.sh`)로 **위반 0** 확인.
1. `python3 backend/scripts/generate_verse_text.py` — 멱등, 본문+문맥 프리베이크.
2. (아이콘/프론트 자원 추가 시) `cd frontend && npm run build` — dist 마운트라 빌드 필수.
3. `docker compose restart api` — `lru_cache` 비우기(§6). Neo4j 직독 라우트를 검증할 땐 restart로 부족하다.
4. API 엔드포인트로 데이터 반환 확인.
5. Playwright로 `localhost:8080` 렌더 확인, 콘솔/네트워크 에러 0.

단어 분포는 1 대신 `build_word_distribution.py`(자체 게이트, §3)로 정본을 재산출한 뒤 2~5를 밟는다.

**그래프 초기화 후 재적재 순서**(README + 회고): `load_theographic.py` → `inject_ko_names.py` → `inject_date_corrections.py` → `load_authored_genealogy.py`·`load_authored_mothers.py` → `load_person_events.py`. **이 순서를 생략하면 무음으로 원복된다** — task#238 실사례: `load_theographic.py` 재적재 후 `inject_date_corrections.py`를 건너뛰어 교정값이 업스트림 원본으로 되돌아가 있었고, 다음 inject 실행 때서야 발견됐다. **inject 계열은 항상 로더 재실행 다음**에 온다.

---

## 8. CI / 배포 게이트

- `.github/workflows/deploy.yml` — `main` push 시 self-hosted 러너에서 `git fetch origin` → `git reset --hard origin/main` → `bash deploy.sh`. **워크플로 자체에는 테스트 스텝이 없다** — 게이트는 `deploy.sh` 안으로 내려가 있다.
- `deploy.sh` 순서(task#259 재배치): lock 파일로 동시 배포 차단(`/tmp/biblemap-deploy.lock`, `trap`으로 해제) → macOS 키체인 우회용 임시 `DOCKER_CONFIG` → `.env` 로드 → `[1/7]` **Neo4j 도달 대기**(소켓 확인 최대 15회, 미도달이면 `exit 1`) → `[2/7]` **주입 2종**(`inject_ko_names.py` · `inject_date_corrections.py`, 둘 다 멱등) → `[3/7]` 프론트 `npm install` → `[4/7]` **`CHECK_STRICT=1 bash scripts/check.sh`(§1) — 실패 시 `exit 1`로 빌드 전에 배포 중단** → `[5/7]` `npm run build` → `[6/7]` `docker compose -p biblemap build api` → `[7/7]` `up -d api nginx`.
- **왜 주입이 게이트 앞인가**: 뒤에 두면 아무 일도 못 한다 — 교정이 롤백된 DB에서는 게이트의 `validate_event_chronology`가 먼저 배포를 막아 주입에 도달하지 못하고, 게이트가 통과하면 이미 적용돼 있어 no-op이다. 주입은 멱등이므로 검증 전에 DB를 정본으로 되돌린다(ADR `260801-195022`). **`npm install`이 게이트 앞인 이유**는 클린 체크아웃에서 ESLint가 스킵되던 순서 버그의 직접 원인이었기 때문.
- 대기와 주입이 분리되면서 주입 호출의 `2>/dev/null`이 제거됐다 — 이전에는 `NEO4J_PASSWORD` 미설정 예외가 "Neo4j 준비 대기 중"으로 위장돼 원인이 숨었다.
- `tee -a "$LOG"` 뒤의 종료코드는 `${PIPESTATUS[0]}`로 포착한다(비-pipefail 환경 관용구).
- **`deploy.sh`는 `load_*`를 실행하지 않는다** — 그래프 적재는 저작 시점 수동(§7).
- 배포 후 확인은 `gh run list`(success). 배포 무음 실패(백엔드가 옛 코드) 의심 시엔 폴러보다 **러너부터** 확인한다(글로벌 인프라 격리 규칙).

---

## 9. 커버리지 실태

- **자동 회귀 안전망이 있는 영역**: 저작 데이터의 스키마·통제 어휘·verseID 실존·집합 커버리지(§2, 13종) · 시대 경계 3중복 드리프트(§2 `validate_era_bands_consistency`) · Neo4j 연대 이상(§2 `validate_event_chronology`) · 프론트 정적 규칙(ESLint) · 적재 스크립트의 사슬/건수 자체검증(§3) · `_parse_year` 인라인 assert(§3).
- **자동 안전망이 없는 영역**: FastAPI 라우트의 응답 계약(엔드포인트 단위 테스트 0건) · Cypher 쿼리 결과 · React 컴포넌트 렌더/상호작용 · `frontend/src/mapGeo.js`·`mapRingController.js`·`urlState.js` 같은 순수 함수 모듈(왕복 대칭 테스트 없음) · 투어 장면 스케치 커버리지(§4의 집합 대조가 아직 스크립트화되지 않음). 이 영역의 회귀는 전적으로 §5의 Playwright 수동 검증과 사용자 피드백에 의존한다.
- **커버리지 수치는 측정되지 않는다** — coverage 도구(pytest-cov·c8 등) 설정이 없고, CI에 품질 리포트도 없다. `scripts/check.sh`의 PASS/FAIL이 유일한 기계 판정이다.
