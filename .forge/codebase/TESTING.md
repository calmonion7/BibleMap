---
last_mapped_commit: 4ad1d837a3771f69f53877b128938124b68d920b
mapped: 2026-08-21
---

# TESTING

BibleMap이 정확성을 검증하는 방식. 검증은 (1) 배포 전 단일 게이트 `scripts/check.sh`, (2) 데이터 기계검증 스크립트 `backend/scripts/validate_*.py`, (3) **프론트 순수 함수 vitest 유닛 테스트**, (4) 로더/빌더/inject의 자체 검증과 인라인 assert, (5) 커밋되지 않는 ephemeral 정합 감사, (6) Python Playwright 화면 검증, (7) 배포 파이프라인 게이트로 이뤄진다. 백엔드에는 여전히 테스트 러너가 없다(의도된 결정 — 아래 §0).

---

## 0. 테스트 러너 실태 — 프론트만 vitest, 백엔드는 의도적 부재

- **프론트: vitest 도입됨(task#261).** `frontend/package.json`의 `devDependencies`에 `vitest`, 스크립트는 `npm test`(= `vitest run`). 별도 config 파일 없음 — vite 설정을 그대로 쓰고 환경은 기본값(`node`, 대상이 순수 함수라 DOM 불요). 대상 5모듈 88건(실측, `npm test`):
  - `src/urlState.test.js` — `encodeHash`/`parseHash` 왕복 대칭(9필드 조합·빈/부분 상태·알 수 없는 해시 방어)
  - `src/mapGeo.test.js` — 11개 export 전수, 빌더마다 **빈 입력 → 유효한 빈 FeatureCollection** 케이스 포함
  - `src/mapRingController.test.js` — 생성 계약과 조기 반환만(순수부가 없어 나머지는 명시 제외, 파일 상단 주석)
  - `src/dates.test.js` — `parseYear()`의 혼재 연대 문자열 파싱(음수·양수·연-월·제로패딩 등)
  - `src/useReadingProgress.test.js` — 이어읽기 순수 헬퍼 `computeResume()`의 경계 케이스(완독·중간 공백·`last` 없음 등, task#276 결함의 회귀망). §9의 대조군 원칙 실제 사례.
- **백엔드: pytest 미도입 — 의도된 결정**(ADR `260801-195023`). Neo4j 없이 테스트 가능한 라우트가 `tours.py`·`words.py` 둘뿐이라 회수가 적다.
- **React 렌더/상호작용 테스트(jsdom·testing-library)도 미도입** — §5의 Playwright 화면 검증이 이미 덮는다. Playwright는 npm이 아니라 **호스트 Python**(`/opt/homebrew/lib/python3.14/site-packages/playwright`)에 설치돼 있다.
- **커버리지 도구(c8 등) 미도입** — 측정 대상이 다섯 모듈뿐이라 숫자가 의미 없다.
- 프론트의 정적 게이트는 ESLint(`CONVENTIONS.md` §8) — `npm run lint`·`npx eslint src` 모두 0 error / 0 warning(테스트 파일 포함).
- 즉 "테스트를 돌린다"의 실체는 **`bash scripts/check.sh`**(§1, vitest를 포함한다)와 §5의 Playwright 화면 검증이다.

---

## 1. `scripts/check.sh` — 배포 전 검증 게이트 (AI 불요 CI 게이트)

task#255에서 흩어져 있던 검증을 단일 엔트리로 묶은 스크립트. **`deploy.sh`가 데이터 주입·`npm install` 다음, 프론트 빌드보다 앞에서 `CHECK_STRICT=1`로 호출**하며 단독 실행도 가능하다.

```
bash scripts/check.sh                 # 리포지토리 어디서 실행해도 자기 위치로 ROOT 유도
CHECK_STRICT=1 bash scripts/check.sh  # 엄격 모드 — 환경 미충족 스킵을 실패로 승격(배포 경로)
```

- **구성 4블록**
  1. **파일 기반 데이터 검증 20종 + 대조군(`--selftest`) 7건** — `python3 -m backend.scripts.validate_<name>` 모듈 실행으로 순서대로: `covenants` · `messianic_prophecies` · `parables_miracles` · `topical_verses` · `pm_map_coverage` · `scene_coverage` · `chapter_sections` · `chapter_summaries` · `quotations` · `person_context` · `god_reliance` · `traits` · `era_bands_consistency` · `approx_book_verses`(task#274) · `intro_menu_parity`(task#277) · `curated_persons`(task#278) · `intro_gutter`(task#280) · `intro_entry_route`(task#281) · `event_verses`(task#282) · `sortkey_startdate`(task#283). 전부 **하드 게이트**(DB·네트워크 불요). 이어서 이 중 대조군을 갖춘 7개(`intro_menu_parity`·`curated_persons`·`intro_gutter`·`intro_entry_route`·`event_verses`·`sortkey_startdate`·`era_bands_consistency`)의 `--selftest`를 각각 별도 항목으로 돌려 — 이 검사들 자신이 고의 드리프트에 실제로 FAIL하는지 인메모리로 확인한다(§9).
  2. **영구 forge 문서 추적 가드(`validate_forge_docs_tracked`, task#279)** — 데이터 검증이 아니라 git 상태 가드라 위 20종 루프에 넣지 않고 별도 블록으로 둔다. `git rev-parse --is-inside-work-tree`가 실패하면(작업트리 아님) 이 블록 전체를 `skip()`으로 넘기고, 성립하면 기준선 검사 + `--selftest`를 각각 돌린다. `.forge/adr`·`.forge/retro` 아래 **미추적 파일이 하나라도 있으면 FAIL** — `.gitignore`가 화이트리스트 중인데도 `git add`를 빠뜨린 회귀를 재현한다. **배포 경로에서도 살아있는 하드 게이트다**(§8 참조) — `deploy.yml`의 `git reset --hard`는 추적 파일만 되돌리고 미추적 파일은 지우지 않으므로, 미추적 영구 문서가 있으면 `CHECK_STRICT=1` 배포 경로가 그대로 막힌다.
  3. **프론트(ESLint · 유닛 테스트)** — `frontend/node_modules`가 있으면 `npx --no-install eslint src`와 `npm test`(vitest, §0)를 이어서 돌리고, 없으면 둘 다 `⊘ 스킵` 경고(엄격 모드에서는 `✗ 실패`). 두 검사가 같은 `node_modules` 가드를 공유한다.
  4. **연대 정합(Neo4j)** — `.env`를 `set -a`로 로드한 뒤 `127.0.0.1:7687` 소켓 연결이 되면 `python3 -m backend.scripts.validate_event_chronology`, 미기동이면 `⊘ 스킵`(엄격 모드에서는 `✗ 실패`).
- **출력 계약**: 항목마다 `  ✓ <라벨>` / `  ✗ <라벨>` + 실패 시 출력 마지막 8줄. 하나라도 실패하면 `=== check FAILED ===` 후 `exit 1`, 전부 통과면 `=== check PASS ===` 후 0.
- **환경 의존 항목만 스킵-경고**, 파일 기반 검증은 절대 스킵하지 않는다(스크립트 상단 주석의 설계 계약). git 작업트리가 아닐 때의 `validate_forge_docs_tracked` 스킵도 같은 성격(환경 미충족, 파일 위반이 아님).
- **`CHECK_STRICT` 계약(task#259)** — 참이면 위 스킵 분기들이 `skip()` 헬퍼를 통해 `✗ … (CHECK_STRICT: 스킵 불가)` + `fail=1`이 된다. **`check PASS`가 "전 검사를 실제로 통과했다"를 뜻하는 건 엄격 모드일 때뿐이다.** 미설정 시 스킵-경고 동작은 그대로 — Neo4j 없이 파일 검증만 돌리는 단독 개발 실행이 정당한 용법이기 때문(ADR `260801-195022`).
- **신규 `validate_*.py`를 만들면 반드시 `scripts/check.sh`의 목록에도 등록한다** — 안 하면 게이트가 잡지 못한다(`.forge/retro/260724-111705-predeploy-validation-gate.md`). 현재 `backend/scripts/validate_*.py`는 22개다: 20개(파일 기반, 위 1번 루프) + 1개(`forge_docs_tracked`, 2번 블록·git 상태 가드) + 1개(`event_chronology`, Neo4j) — **전수가 게이트에 등록돼 있다.**
- **배포 footgun**: `deploy.sh`가 `check.sh`를 호출하므로 신규 스크립트는 **`deploy.sh` 변경과 반드시 함께 커밋**한다. 러너 체크아웃에 파일이 없으면 게이트가 파일 부재로 배포를 막는다.
- 실측(2026-08-21, Neo4j 기동·`frontend/node_modules` 존재·git 작업트리 상태): 미설정 실행으로 32개 항목(파일 검증 20 + `--selftest` 7 + `forge_docs_tracked` 2 + eslint 1 + vitest 1 + 연대 정합 1) 전부 `✓`, `check PASS`. `frontend/node_modules`가 없거나 git 작업트리 밖인 경우의 스킵 동작은 위와 동일한 `CHECK_STRICT` 계약을 따른다.

---

## 2. 기계검증 스크립트 (`backend/scripts/validate_*.py`)

데이터 저작이 규칙을 지키는지 확인하는 결정적 검증기. **공통 계약**: 위반이 있으면 비0 종료, 없으면 `PASS`/`OK — 위반 0` 계열 메시지. 위반 항목만 거부하고 나머지는 통과시키는 **항목 단위 게이트**가 원칙(`CONVENTIONS.md` §6). 구현은 두 스타일이 공존한다 — 초기 검증기(`validate_traits.py` 등)는 위반을 `errors` 리스트에 모아 `print` 후 명시적 `sys.exit(1)`을 부르고, task#278 이후 신규·재작성 검증기(`validate_curated_persons.py`·`validate_event_verses.py`·`validate_sortkey_startdate.py`·`validate_intro_gutter.py`·`validate_intro_entry_route.py`·`validate_era_bands_consistency.py`)는 같은 방식으로 위반을 모으되 끝에서 `assert not errs, "…" + "\n  ".join(errs)` 한 줄로 낸다 — `AssertionError`가 비0 종료를 대신하므로 계약상 동등하다.

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
| `validate_era_bands_consistency.py` | 소스 6곳 + `covenants.json`/`tours/*.json` (task#255 S1 · task#284에서 3축 추가) | **7축.** ① `frontend/src/eraBands.js`의 `ERA_BANDS`(task#271에 `TimelineView.jsx`에서 승급) ② `backend/app/routes/stats.py`의 `ERA_BANDS` ③ `backend/app/curated.py`의 `ERA_ORDER`(task#278에 `routes/persons.py`의 `_ERA_ORDER`에서 이관) — ①②③을 **정규식으로 파싱**해 이름·순서·경계 일치를 단언. ④ `covenants.json`의 각 `era`가 유효 시대인지 ⑤ `data/tours/*.json`의 각 `era`가 유효 시대인지(저작자 오타 축) ⑥ `frontend/src/PersonHub.jsx`의 `ERA_ORDER` 사본이 `curated.py`와 이름·순서 모두 일치 ⑦ `frontend/src/**/*.{jsx,js}` 전체에서 좌변 식별자 사슬에 `era`/`Era` 토큰이 있는 `=== '문자열'` 비교(era 축 기능 게이트 — 시대 이름을 바꾸면 비유·기적 토글이 **에러 없이** 사라지는 결합점)를 전부 찾아 리터럴이 유효 시대인지 단언. 각 축은 몇 항목을 보았는지 출력에 찍고 **0항목이면 실패**(공허 통과 방지). `-Infinity`(JS)/`float("-inf")`(Py) 정규화 주의. `--selftest`가 7축 전부 + 각 축의 공허 통과를 순회 확인(§9) |
| `validate_curated_persons.py` | `backend/app/curated.py`의 `CURATED`/`ERA_ORDER` ↔ `data/person_events/`·`data/god_reliance/`·`person_slugs/seal_slugs.json` (task#278) | `CURATED` 35 slug ↔ `person_events/*.json` 파일 집합 **양방향**(죽은 키·미커버 파일 둘 다 위반) · `god_reliance` slug ⊆ `CURATED` · `seal_slugs.json` slug ∩ `CURATED` == ∅(인장 상위집합과 큐레이션이 겹치면 중복) · 각 `era` ∈ `ERA_ORDER`. `CURATED`/`ERA_ORDER`는 `ast.literal_eval`로 소스에서 직접 추출(import 부작용 0). `--selftest`가 4개 단언(첫 단언은 양방향)을 순회 확인 |
| `validate_event_verses.py` | `data/event_verses/events.json`의 각 권 블록 ↔ `rangeLabel` ∩ `data/bible/verses.json` (task#282) | **불변식은 개수가 아니라 경계**(ADR `260821-000937`): 모든 블록에서 베이킹된 `verseID` 집합 == `expand_range_label(rangeLabel, bookOrder)`(`generate_person_event_verses.py`에서 import — 파서 2벌 금지). 교차-장·장 단위 범위가 첫 절 1개만 베이킹돼 화면엔 "38:1–42:6"인데 본문은 1절만 보이던 결함(실측 12건)의 재발 방지. 오라클이 저장소 안 파일이라 네트워크 불요. 비공허 짝 — 대상 블록 0개면 실패. `--selftest`가 절 삭제·범위 밖 삽입·라벨 변조·파싱 불가·0블록 5종을 순회 확인 |
| `validate_intro_entry_route.py` | `frontend/src/urlState.js`의 `isNoTarget` ↔ `useStageNavigation.js`의 초기값 계산·마운트 복원 effect (task#281) | 무해시 첫 진입이 인트로 대신 허브로 새는 결함(초기값은 옳게 `'intro'`로 계산되는데 직후 복원 effect가 `parseHash('')`의 `{stage:'hub'}`로 덮음) 재발 방지. **경계 형태**로 4종 단언: (a) 무타깃 판정 지점이 `isNoTarget` 정본 **밖에는 0곳**(개수는 세지 않음 — `'#'`·`'#/'` 함께 보는 것은 정상) + 그 술어가 공허하지 않음 (b) `isNoTarget`이 `urlState.js`에서 export됨 (c) 초기값 계산이 `isNoTarget`을 씀 (d) 마운트 복원 effect가 `applyParsedHash` **호출보다 먼저** `isNoTarget`을 참조. 앱 실행 없이 소스 정적 파싱만. 실측은 검증기가 아니라 `scripts/uat_intro_entry.py`가 한다(§5) — 초기값이 옳게 계산된 **다음** 프레임에서 덮이는 형태라 정적 검사만으론 초록이면서 화면은 허브일 수 있다. `--selftest`가 고의 결함 5종(판정 인라인 복사·복원 가드 제거·타 파일 재주입·export 제거·선언 제거)을 순회 확인 |
| `validate_intro_gutter.py` | `frontend/src/IntroView.jsx`의 인라인 스타일 객체 전수 (task#280) | 인트로 텍스트가 폰에서 화면 양끝에 붙는 결함(전역 `box-sizing` 리셋 부재로 `width:100%`+좌우패딩이 `content-box`에서 시각적 여백 0이 됨, `CONVENTIONS.md` §7.6) 재발 방지. 3종 단언: (a) 명시 폭+좌우패딩을 함께 쓰는 스타일 객체는 `boxSizing:'border-box'` 선언 (b) 그런 객체가 파일 전체에 **정확히 1개**(비트 공용 프레임) (c) 그 프레임은 `wordBreak:'keep-all'` 선언 (d) 텍스트를 담는 비트 5곳(`renderBeat`·`MapBeat`·`MontageBeat`·`MenuScene`·`Destination`)이 그 프레임을 통과. 앱 실행 없이 소스 정적 파싱만. 실측 여백 하한은 `scripts/uat_intro_gutter.py`가 잰다(§5). `--selftest`가 border-box 제거·keep-all 제거·비트별 손패딩 재주입·비트별 프레임 이탈을 순회 확인 |
| `validate_sortkey_startdate.py` | `data/person_events/*.json` 전역(전 파일 sortKey 정렬) (task#283) | **전역·교차파일**로 본다 — 파일 단위로 좁히면 `moses`→`joshua` 경계의 역전이 무음 통과한다(`CONTEXT.md`의 "통합 시간축" 규정 범위). 두 불변식: ① sortKey로 전역 정렬한 인접쌍의 `startDate` 역전 0곳(동값 쌍은 판정 제외, 제외 건수를 출력에 찍음) ② 단일연도 `yearLabel`(`BC N`/`AD N`, `경` 허용)의 연도 == `startDate`, 범위 라벨이면 `startDate`가 범위 안(시대 단위 근사 라벨은 형태로 제외) — `TimelineView`가 저작 사건에서 `startDate`가 아니라 `yearLabel`을 그대로 표시하므로 정렬만 고치고 라벨을 두면 화면은 옛 연도를 보여준다. `startDate`는 관대한 파싱 대신 "부호 있는 정수 문자열"을 단언(월/일 정밀도 유입 시 fail-closed) — 기존 연도 파서 3벌은 재사용하지 않는다(그 파서들이 `NEO4J_PASSWORD` 요구 모듈에 살아 이 검증기가 `.env` 로드 전에 도는 것과 충돌). `--selftest`가 파일 내 역전·교차파일 역전·`startDate`/`sortKey` 형식 위반·라벨 드리프트·범위 라벨 이탈·양쪽 비공허 짝 8종을 순회 확인 |
| `validate_approx_book_verses.py` | `generate_approx_book_verses.py`의 `VERSE_MAP` ↔ `data/book_events/books.json` | **양방향 정합**(task#274). `VERSE_MAP`에 있는데 `book_events`에 없는 "죽은 키"(생성기가 `sys.exit(1)`로 죽는 원인) · `book_events`에 있는데 `VERSE_MAP`에 없는 "미커버 쌍"(구절 없는 ⚡ 연결) 둘 다 위반. 생성기를 실행하지 않고 `ast.literal_eval`로 소스만 읽는다(배포 게이트는 판정자이지 작성자가 아니다) |
| `validate_intro_menu_parity.py` | `frontend/src/IntroView.jsx`의 `SCENES` ↔ `App.jsx`/`ExploreStage.jsx`의 실제 탭 | **인트로 소개 장면 ↔ 실제 하위 메뉴 양방향 정합**(task#277). 부(인물·성경책·투어)별로 (아이콘, 라벨) 쌍 집합을 대조 — 실제에 있고 인트로에 없으면 누락, 인트로에 있고 실제에 없으면 유령. 앱을 실행하지 않고 소스 정적 파싱만으로 판정. `--selftest` 인자로 전 탭에 고의 누락·유령을 순회 주입해 검사가 실제로 FAIL하는지 확인하는 대조군 모드를 갖는다(§9) |
| `validate_forge_docs_tracked.py` | `.forge/adr/`·`.forge/retro/`의 git 추적 상태 (task#279) | **데이터 검증이 아니라 git 상태 가드** — `git ls-files --others --exclude-standard`로 두 루트 아래 미추적 파일이 있으면 FAIL. 영구 문서를 작성하고 `git add`를 빠뜨린 회귀(task#275)의 재발 방지이며, `deploy.yml`이 같은 디렉터리에서 `git reset --hard`만 하고 `git clean`은 안 하므로 **배포 경로에서도 실제로 배포를 막는 하드 게이트**다(§1·§8). git 작업트리가 아니면 자체적으로 exit code 3(`EXIT_NO_GIT`)을 내지만, `check.sh`는 이 경우를 스크립트 호출 전에 `git rev-parse --is-inside-work-tree`로 먼저 걸러 통째로 스킵한다. `--selftest`는 실제 `.forge/adr`·`.forge/retro`를 건드리지 않고 임시 스캔 루트(`.forge/.docs-tracked-selftest/`)에 파일을 놓고 지워 같은 스캔 함수가 검출·해소를 확인한다 |
| `validate_event_chronology.py` | **Neo4j 직독** | (a) 인물 출생<활동<사망 서사 역전 (b) 사사 승계 순서(삿 10–12장) 역전 (c) 대표 앵커(출애굽 -1446·아브라함 소명 -2091·가뭄 선포 -870) 대비 역전 (d) 교정 창(-2200~-600) 내 `rec` 이벤트 목록화 (e) 형제군 ±150년 고립 이탈(전치 오타 후보) + Person 스캔(사망<출생·수명>1000년). 신학적 참여는 `THEOLOGICAL_WHITELIST`로 제외. `--json PATH`로 구조화 리포트 저장 |

- **공통 계약의 예외 3건** — `validate_covenants.py`·`validate_pm_map_coverage.py`·`validate_scene_coverage.py`는 위반 목록을 모으지 않고 **`assert`를 여러 번 걸어 첫 위반에서 즉시 중단**한다(통과 시 `PASS` 출력). 항목 열거가 필요 없는 소규모/집합 대조 검증에 쓰는 변형. (`validate_era_bands_consistency.py`는 task#284 재작성으로 이 변형에서 벗어나 위 "위반을 모아 한 번에 `assert`" 계열로 옮겼다 — 7축 전부를 한 번에 보고하기 위해서다.)
- **실행 방법 두 가지**: `python3 backend/scripts/validate_<name>.py`(문서·AUTHORING.md 표기)와 `python3 -m backend.scripts.validate_<name>`(`scripts/check.sh` 표기). 새 검증기는 둘 다 동작해야 한다.
- **환경 요구**: `validate_event_chronology.py`만 `NEO4J_PASSWORD`(+선택 `NEO4J_URI`/`NEO4J_USER`)가 필요하다 — 나머지는 `data/` JSON과 소스 파일만 읽어 DB 접속 불요.
- 검증기가 참조하는 **정본 절 사전은 `data/bible/verses.json`** 하나다(verseID 실존 확인의 공통 기준, `CONVENTIONS.md` §6.2). `validate_event_verses.py`는 이 사전을 절 존재 오라클로도 쓴다(ADR `260821-125000`) — 라벨 범위를 오프라인으로 전개해 네트워크 의존 없이 판정한다.

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
- **재사용 목적의 UAT는 리포지토리 루트 `scripts/uat_*.py`에 체크인한다**(task#280~281 — `scripts/uat_intro_gutter.py`·`scripts/uat_intro_entry.py`). `.forge/scratch/`의 일회성 조사 스크립트와 달리, 그 화면을 다시 만질 때마다 사람이 반복 호출하는 자다. 상세 관례는 §5.6.
- **스크린샷 산출물은 `.forge/reports/`에 저장하는 것이 현행 관례**다(`.claude/agents/ui-verifier.md`가 명시; `task246_screenshots.py`의 `OUT_DIR = '.../.forge/reports'`). 과거 태스크는 `.forge/scratch/task2NN/`에 스크린샷을 함께 뒀다 — 옛 디렉터리는 그대로 두고 신규는 `reports/`로.
- 파일명은 `<주제>-<뷰포트>.png`(`messianic-thread-desktop.png`·`covenant-timeline-mobile.png`) 또는 `<주제>-<테마>-<장면>.png`(`intro-film-light-map.png`). 전수 UAT는 실패 시 `<site>-<viewport>-ERROR.png`를 따로 남긴다.

### 5.2 스크립트 구조 관례

- `sync_playwright()` + `p.chromium.launch(headless=True)` + `browser.new_page(viewport={...})`. 뷰포트 dict는 상수로(`VIEWPORTS = {"mobile": 393×852, "desktop": 1280×800}` 스타일).
- 진입은 `page.goto(BASE, wait_until='networkidle', timeout=15000)` 후 `page.wait_for_timeout(...)`으로 렌더 안정화. 애니메이션이 있는 화면은 draw-on/입장 모션이 끝날 시간을 기다린 뒤 캡처한다(인장 draw 1초, 카메라 정착 400ms, 스케치 패널 450ms).
- 요소 조작은 한글 표시 텍스트 기준 `page.get_by_text('타임라인', exact=True).first.click()`. 오버레이(SidePanel 등)가 시각적으로 덮어 실제 클릭이 막히는 요소는 `el.evaluate('el => el.click()')`로 JS 직접 디스패치.
- **지도 위 좌표 클릭**: MapLibre 마커는 DOM 셀렉터로 못 잡는다 — `.forge/scratch/task202/uat.py`의 `MAP_HELPER_JS`가 React fiber를 스캔해 map 인스턴스를 `window.__map`에 노출하고, `map.project([lng, lat])` + 캔버스 rect로 화면 좌표를 계산해 `page.mouse.click(x, y)`한다.
- 시나리오 단계마다 `page.screenshot(path=...)` + `print`로 진행 방출. 애니메이션 상태 판정은 `print(f'{label} >> visible={loc.is_visible()}')` 류 텍스트 라인으로 매트릭스 각 항목의 PASS/FAIL을 로그에 남긴다.
- 텍스트 특정 함정: "외 2권" 같은 부분 텍스트만으로 칩을 특정하면 같은 문구의 다른 행이 먼저 매치된다 — 사건명 등으로 **행을 먼저 특정한 뒤 행 내부에서** 클릭한다.
- **`data-*` 속성으로 테스트 훅을 단다(task#267~270 이후 신규 관행)** — 텍스트·구조 매칭이 애매한 새 UI는 전용 `data-*` 속성을 붙여 Playwright가 텍스트 변경에 흔들리지 않고 정확히 특정하게 한다. 실측: `data-bookmark-toggle`·`data-saved-item`/`data-saved-hash`·`data-resume-reading`·`data-reading-progress`·`data-chapter-read`·`data-read-toggle`·`data-verse-id`/`data-verse-highlight`·`data-open-place`·`data-intro-scene`/`data-intro-tabs`/`data-intro-layer`/`data-intro-frame`(task#280 — 비트 공용 프레임 경계, `scripts/uat_intro_gutter.py`가 잉크 여백을 프레임 padding-box 기준으로 계산하는 데 씀). 값은 판정에 쓸 수 있는 실데이터(id·상태)를 담아, 존재 확인뿐 아니라 `getAttribute` 대조도 가능하게 한다. 기존 화면은 소급 추가하지 않는다 — 새 UI·저장/진도류처럼 텍스트가 자주 바뀌는 화면에 한해 적용.

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

### 5.6 체크인 UAT 스크립트 — `scripts/uat_*.py` (task#280~281)

`scripts/uat_intro_gutter.py`(인트로 비트 여백·금선 정렬 실측)와 `scripts/uat_intro_entry.py`(무해시 진입 라우팅 실측)가 이 형태의 정본이다. 둘 다 대응하는 `backend/scripts/validate_*.py`의 **소스 불변식**이 놓치는 축(선언이 실제로 픽셀·화면이 됐는가)을 실제 브라우저로 잰다 — 둘은 서로를 대신하지 못한다(§2의 짝 검증기 참조).

- **`scripts/check.sh`에 배선하지 않는다** — 의도적. `deploy.sh`는 `npm run build` **전**에 `check.sh`를 부르므로 그 시점 `:8080`은 옛 빌드를 서빙한다. 게이트에 넣으면 방금 고친 코드가 아니라 이전 배포본을 재서 초록·빨강이 둘 다 거짓이 된다. 게이트에는 브라우저 없이 항상 도는 소스 불변식만 두고, 이 UAT는 인트로 레이아웃·라우팅을 만질 때 **사람이 직접 부르는 자**다.
- **실패 계층을 자가 구별한다**(회고 `260820-190352`) — 종료 코드 3단: `0`=통과 · `1`=제품 결함 · `2`=측정 환경 이상(`EnvError`: dist가 소스보다 낡음·백지 렌더·헤더 미출현·응답 비-200 등). 백지 렌더나 옛 빌드를 "라우팅/여백 결함"으로 위장해 있지도 않은 결함에 fix-forward를 태우거나, 반대로 진짜 결함을 "환경 탓"으로 덮는 것을 막는다.
- **선행조건 자가 점검(`_freshness()`)** — `frontend/dist/index.html`의 mtime이 감시 대상 소스보다 낡았으면 빌드를 잊었다는 뜻이므로 측정 없이 즉시 `EnvError`로 중단한다.
- **환경 이상은 1회 재시도**한다(`_run_retry`/`_observe_retry`) — 헤드리스 렌더러의 일시 장애 선례가 있어서다(회고 `260820-190352`).
- **URL마다 새 브라우저 컨텍스트**(§5.3의 SPA 원칙을 그대로 따름)와 **실패는 머리부터 전부 출력**(`check.sh`의 `tail -8`과 반대 — 원인이 앞쪽 항목에 있을 수 있어 자르지 않는다).
- **측정 대상은 컨테이너가 아니라 텍스트 잉크다**(`uat_intro_gutter.py`) — `textAlign:center` 아래 블록 요소의 `getBoundingClientRect()`는 프레임 패딩 경계일 뿐이라 결함이 있는 상태에서도 통과를 보고한다. 그래서 텍스트 노드마다 `Range.getClientRects()`로 줄 단위 실제 필적 사각형을 잰다(ADR `260821-000937`의 "실측 자는 실제 대상을 잰다" 원칙의 Playwright 적용).
- **`--selftest`가 이 UAT 자신의 대조군이다**(§9와 같은 원칙, 자가 픽셀-측정형이라는 점만 다르다) — `page.add_style_tag`로 알려진 결함(좌우 패딩 제거·`content-box` 회귀)이나 `localStorage` 플래그 반전을 주입해 검출기가 실제로 발화하는지 확인한다. 발화하지 않으면 "이 UAT는 아무것도 재고 있지 않다"는 뜻이다.

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
- `deploy.sh` 순서(task#259 재배치): lock 파일로 동시 배포 차단(`/tmp/biblemap-deploy.lock`, `trap`으로 해제) → macOS 키체인 우회용 임시 `DOCKER_CONFIG` → `.env` 로드 → `[1/7]` **Neo4j 도달 대기**(소켓 확인 최대 15회, 미도달이면 `exit 1`) → `[2/7]` **주입 2종**(`inject_ko_names.py` · `inject_date_corrections.py`, 둘 다 멱등) → `[3/7]` 프론트 `npm install` → `[4/7]` **`CHECK_STRICT=1 bash scripts/check.sh`(§1) — 실패 시 `exit 1`로 빌드 전에 배포 중단** → `[5/7]` `npm run build` → `[6/7]` `docker compose -p biblemap build api` → `[7/7]` **컨테이너 재시작 2단계**(task#263): `docker compose up -d api` 다음 `docker compose up -d --force-recreate nginx` — nginx는 이미지 빌드가 없고 바인드 마운트 스펙도 불변이라 `nginx.conf`만 바뀌면 Compose가 재생성 필요를 판단하지 못해 no-op이 되기 때문. 정적 서빙 컨테이너라 매 배포 강제 재생성해도 비용은 거의 없다.
- **왜 주입이 게이트 앞인가**: 뒤에 두면 아무 일도 못 한다 — 교정이 롤백된 DB에서는 게이트의 `validate_event_chronology`가 먼저 배포를 막아 주입에 도달하지 못하고, 게이트가 통과하면 이미 적용돼 있어 no-op이다. 주입은 멱등이므로 검증 전에 DB를 정본으로 되돌린다(ADR `260801-195022`). **`npm install`이 게이트 앞인 이유**는 클린 체크아웃에서 ESLint가 스킵되던 순서 버그의 직접 원인이었기 때문.
- 대기와 주입이 분리되면서 주입 호출의 `2>/dev/null`이 제거됐다 — 이전에는 `NEO4J_PASSWORD` 미설정 예외가 "Neo4j 준비 대기 중"으로 위장돼 원인이 숨었다.
- `tee -a "$LOG"` 뒤의 종료코드는 `${PIPESTATUS[0]}`로 포착한다(비-pipefail 환경 관용구).
- **`deploy.sh`는 `load_*`를 실행하지 않는다** — 그래프 적재는 저작 시점 수동(§7).
- 배포 후 확인은 `gh run list`(success). 배포 무음 실패(백엔드가 옛 코드) 의심 시엔 폴러보다 **러너부터** 확인한다(글로벌 인프라 격리 규칙).

---

## 9. 회귀 검증의 대조군 원칙 — 기준선 PASS는 아무것도 증명하지 않는다

task#276·#277에서 승급된 원칙(회고 `260820-003946`, ADR `260820-003946-script-guard-reproduced-in-gate.md`): **새로 만든 검사가 기준선에서 통과한다는 사실만으로는 그 검사가 실제로 무언가를 판정하고 있다는 근거가 안 된다.** 검사 로직 자체가 죽어 있거나(예: 파싱이 조용히 빈 결과를 내고 "위반 0"으로 오판) 대조 대상을 잘못 짚었을 수 있기 때문 — 이 경우 기준선 PASS와 "검사가 고장나 항상 PASS"는 겉으로 구별되지 않는다. 그래서 **회귀 검사·게이트는 "이 검사가 실패할 수 있다"를 스스로 증명하는 대조군을 함께 둔다**: 검사 대상에 알고 있는 결함을 고의로 주입한 사본을 만들어, 그 사본에서는 검사가 반드시 FAIL함을 확인한다.

- **백엔드 검증기의 `--selftest`** — `backend/scripts/validate_intro_menu_parity.py`(§2)가 이 계약의 최초 사례였고, task#278 이후로는 **신규·재작성 검증기의 표준 관행**이 됐다: `--selftest` 인자로 인메모리 사본에 고의 드리프트를 **전 항목/전 축 순회로** 주입해 매번 FAIL하는지 확인한다. 대상을 하나로 고정하면 "그 항목에 우연히 맞춰진 검사"인지 가릴 수 없어서 전수 순회가 계약이다. 실측: `validate_curated_persons.py`(4단언 순회) · `validate_intro_gutter.py`(비트 5곳 순회) · `validate_intro_entry_route.py`(불변식 4종) · `validate_event_verses.py`(고의 드리프트 5종) · `validate_sortkey_startdate.py`(8종) · `validate_era_bands_consistency.py`(7축 + 축별 공허 통과 4종) · `validate_forge_docs_tracked.py`(임시 스캔 루트에 주입·해소). `scripts/check.sh`(§1)가 기준선 실행과 별도 항목으로 이 `--selftest`들을 호출해 배포 게이트에 상시 배선돼 있다.
- **Playwright UAT의 `--selftest`** — 브라우저로 픽셀을 재는 §5.6의 `scripts/uat_intro_gutter.py`·`scripts/uat_intro_entry.py`도 같은 원칙을 진다. 소스를 정적으로 주입할 수 없으므로 `page.add_style_tag`로 알려진 CSS 결함을 주입하거나 `localStorage` 플래그를 뒤집어 검출기가 발화하는지 확인한다 — 백엔드 검증기의 대조군과 같은 값을 Playwright 층에서 낸다.
- **vitest 회귀 테스트의 "수정 전 실패 확인"** — `frontend/src/useReadingProgress.test.js`(§0)는 파일 상단 주석에 "이 테스트는 수정 전 소스(HEAD `0bd58a7`)에서 해당 케이스가 실제로 실패함을 확인한 뒤 추가했다"를 명시한다. 결함을 고친 커밋과 그 결함을 재현하는 테스트를 함께 작성할 때, 테스트가 그 결함을 정말 잡아내는지 **고친 커밋 이전 소스에 대고 한 번 돌려 확인**하는 것이 이 원칙의 최소 실천형이다.
- **적용 기준**: 모든 검사에 대조군을 요구하지 않는다 — 근거가 명확한 구조적 스캔(예: verseID 실존, 통제 어휘 소속)은 로직이 단순해 죽은 검사가 되기 어렵다. 대조군은 **문자열/AST 정규식 파싱으로 소스를 스크래핑하는 검사**(파싱 패턴이 코드 리팩터로 조용히 깨질 수 있음)나 **"완료 기준"처럼 절대어로 판정하는 신규 회귀 테스트**에 우선 적용한다.
- **불변식이 무엇을 재야 하는지는 이 원칙의 범위 밖이다** — "검사가 실패할 수 있음을 증명한다"는 것과 "그 검사가 옳은 것을 재고 있다"는 것은 다른 질문이다. 후자(결함 클래스를 개수가 아니라 경계로 쓰기, 실측 자가 편의 프록시가 아니라 실제 대상을 재기)는 §11이 별도로 다룬다.

---

## 10. 커버리지 실태

- **자동 회귀 안전망이 있는 영역**: 저작 데이터의 스키마·통제 어휘·verseID 실존·집합 커버리지(§2, 20종) · 투어 정차지↔장면 스케치 커버리지(§2 `validate_scene_coverage`) · 시대 결합점 7축 드리프트, 대조군 있음(§2·§9 `validate_era_bands_consistency`) · `VERSE_MAP`↔`book_events` 양방향 정합(§2 `validate_approx_book_verses`) · 인트로↔실제 하위 메뉴 정합, 대조군 있음(§2·§9 `validate_intro_menu_parity`) · 큐레이션 35인 색인 3방향 정합, 대조군 있음(§2·§9 `validate_curated_persons`) · 인트로 비트 여백 소스 불변식, 대조군 있음(§2·§9 `validate_intro_gutter`) · 무타깃 진입 라우팅 단일 선언 불변식, 대조군 있음(§2·§9 `validate_intro_entry_route`) · 근거 절↔라벨 범위 정합, 대조군 있음(§2·§9 `validate_event_verses`) · 통합 시간축 sortKey↔startDate 전역 정합, 대조군 있음(§2·§9 `validate_sortkey_startdate`) · 영구 forge 문서 git 추적, 배포 차단 가드(§2 `validate_forge_docs_tracked`) · Neo4j 연대 이상(§2 `validate_event_chronology`) · 프론트 정적 규칙(ESLint) · **프론트 순수 함수 5모듈(§0, vitest 88건)** · 적재 스크립트의 사슬/건수 자체검증 · `_parse_year` 인라인 assert.
- **소스 불변식만 있고 실측은 사람이 부르는 영역**: 인트로 비트 여백의 실제 픽셀(`validate_intro_gutter`는 소스만 보고, 실측은 `scripts/uat_intro_gutter.py`가 하지만 `check.sh`엔 안 배선됨, §5.6) · 무타깃 진입이 실제로 인트로 화면을 그리는지(`validate_intro_entry_route`↔`scripts/uat_intro_entry.py`, 같은 이유). 둘 다 게이트가 항상 커버하는 건 소스 계약뿐이다.
- **자동 안전망이 없는 영역**: FastAPI 라우트의 응답 계약(엔드포인트 단위 테스트 0건 — 의도된 결정, ADR `260801-195023`) · Cypher 쿼리 결과 · React 컴포넌트 렌더/상호작용 · `mapRingController.js`의 애니메이션 진행·`expandPlace` 경로(맵 인스턴스 의존이라 명시 제외). 이 영역의 회귀는 Playwright 화면 검증과 사용자 피드백에 의존한다.
- **커버리지 수치는 측정되지 않는다** — coverage 도구(pytest-cov·c8 등) 설정이 없다(의도적 — 측정 대상이 다섯 모듈뿐). `scripts/check.sh`의 PASS/FAIL이 유일한 기계 판정이다.

---

## 11. 불변식 설계 원칙 — 결함 클래스는 개수가 아니라 경계로, 자는 실제 대상을 잰다

ADR `260821-000937-invariant-encodes-defect-class.md`(task#280~281)가 승급한 원칙 — §9(대조군)가 "이 검사가 실패할 수 있는가"를 다룬다면, 이 원칙은 **"그 검사가 옳은 것을 재고 있는가"**를 다룬다. 둘 다 "쉬운 쪽"으로 쓰면 **초록인데 결함이 남는** 검사가 된다.

- **① 정적 불변식은 알려진 위반 지점을 열거하지 않고 결함 클래스의 정의를 옮긴다.** 위반 지점이 4곳으로 이미 특정된 상태에서 "이 4곳이 규칙을 지키는가"를 검증기로 쓰면 기준선 PASS·수정 전 FAIL을 다 만족해 자로서 멀쩡해 보이지만, 5번째 위반 지점(새 컨테이너)에는 침묵한다 — 그 침묵이 "위반 없음"인지 "안 보고 있음"인지 구별되지 않는다. `backend/scripts/validate_intro_gutter.py`는 목록이 아니라 "명시 폭 ∧ 좌우 패딩"이라는 **조합**을 스캔해 이 함정을 피한다.
- **② 실측 자는 편의 프록시가 아니라 실제 대상을 잰다.** `getBoundingClientRect()`로 컨테이너를 재는 것이 구현하기 쉽지만, `textAlign:center` 아래서는 프레임 패딩 경계일 뿐이라 결함이 있는 상태에서도 여백이 있다고 보고한다 — **결함이 있는데 통과하는 자**다. `scripts/uat_intro_gutter.py`는 텍스트 노드마다 `Range.getClientRects()`로 줄 단위 잉크 사각형을 재서 이 함정을 피한다(§5.6). 대가는 느리고 코드가 길다는 것 — "자가 더 복잡해지는 대가로 거짓 초록을 못 낸다"는 교환을 받아들인다.
- **부분 개정(task#281) — 클래스를 *개수*로 쓰지 말고 *경계*로 쓴다.** 결함 클래스를 옮기더라도 그것을 "판정 지점이 정확히 1개"라는 개수 형태로 구현하면, 옳은 술어(`isNoTarget(hash)`가 `'#'`와 `'#/'`를 **함께** 비교하는 것)조차 구문상 비교 개수가 2라서 **거짓 빨강**이 된다. 대신 경계 형태로 쓴다: "정본 **밖**에 판정 지점이 0곳" + "정본이 **공허하지 않다**"(개수는 세지 않는다). `backend/scripts/validate_intro_entry_route.py`가 이 형태의 정본 사례다.
- **거짓 빨강도 거짓 초록만큼 비싸다.** 거짓 초록은 결함을 통과시키고, 거짓 빨강은 무인 주행에서 replan을 태우거나 최악의 경우 사람이 **옳은 수정을 되돌리게** 만든다. 방어선은 "수정 **전에** 자를 먼저 돌려 그 자가 왜 그렇게 판정하는지 읽는" 순서뿐이다.
- **비공허 짝(non-vacuous pairing)이 경계 형태의 필수 반쪽이다.** "정본 밖에 0곳"만 단언하면 `return false` 같은 공허한 술어도 통과한다. 그래서 신규 검증기들은 대상이 0건이면 그 자체를 위반으로 본다 — 실측: `validate_event_verses.py`(대상 블록 0개) · `validate_sortkey_startdate.py`(대상 사건 0건·단일연도 라벨 0건 두 축) · `validate_era_bands_consistency.py`(7축 각각 0항목).
- **한계.** 이 원칙은 불변식을 *어떻게 쓰는지*를 다루고 *무엇을 재야 하는지*는 정해주지 않는다 — 결함 클래스 정의 자체를 잘못 짚으면 그 정의를 충실히 옮긴 검증기도 엉뚱한 것을 지킨다. 클래스 정의는 여전히 사람이 실측으로 먼저 특정해야 한다.

---

## 12. 동작 보존 리팩토링의 검증 — 산출 대조 (ADR `260820-204317`)

"동작 보존" 리팩토링(선언 위치만 옮기고 로직은 그대로 두는 작업, 예: task#278의 큐레이션 인물 색인 승급)은 완료 기준을 **구조**(그 선언이 남아있지 않다, import가 새 경로를 가리킨다)로 쓰기 쉽지만, 그 기준만으로는 **통과하면서 동작이 깨질 수 있다**. task#278 실측 — `stats._compute_longest_journeys()`가 옛 딕셔너리의 **삽입 순서**를 `stopCount` 동률 타이브레이크로 암묵 의존했고, 재배선 후 순회 원천이 바뀌자 순서가 뒤집혀 `/stats` 응답이 달라졌다. 이 의존은 어디에도 적혀 있지 않아 `grep`으로는 빈 결과였다.

그래서 이런 리팩토링의 정지조건은 **산출 대조**로 둔다 — 영향 범위 엔드포인트 전량을 리팩토링 **전**에 캡처해 두고, 후 캡처와 `diff -r`가 빈 결과여야 한다. 구조 기준(`grep`)은 버리지 않되 **보조**로만 둔다.

- **기준선은 첫 코드 변경 전에 뜬다** — 사후엔 그 상태가 사라진다(리팩토링을 되돌려야 재현 가능).
- **기준선은 두 번 떠서 서로 같은지 먼저 증명한다** — 응답에 비결정성(딕셔너리 순회 순서·타임스탬프·부동소수)이 있으면 대조는 영구히 실패하고, 실패가 코드 결함인지 응답 비결정성인지 구별할 수 없다. task#278은 2회 캡처 437파일 바이트 동일을 먼저 확인했다.
- **검사 자신이 컨테이너를 재빌드한다** — 이 프로젝트의 API는 컨테이너로 서비스되므로, 재빌드 없이 캡처하면 옛 코드의 응답을 떠서 거짓 통과한다. 사람이 기억해야 하는 전제는 전제가 아니라 지뢰다(§9의 정신과 같다).
- **영향 범위를 빠뜨리면 그만큼 구멍이다** — task#278은 손대는 8개 모듈의 **모든** 라우트가 14개 엔드포인트로 덮이는지 먼저 대조했다. "주요 엔드포인트 몇 개"는 이 방식의 값을 대부분 버린다.
- **이 방식으로도 못 잡는 축** — 단일 요청 대조는 **요청 간 상태 오염**(공유 `lru_cache` 반환값을 호출자가 제자리 변형)을 못 본다. 1회차는 정상이고 2회차부터 달라지기 때문이다. task#278은 같은 엔드포인트를 연속 2회 호출해 drift를 보는 검토를 별도 축으로 돌렸다. 산출 대조는 한 축일 뿐 만능이 아니다.
- 이 검증 방식은 리포지토리에 스크립트로 커밋돼 있지 않다 — task 수행 중 즉석으로 짜서 쓰고 버리는 §4의 ephemeral 감사와 같은 성격이다. 남는 재사용 후보(시대 상수 잔여 통합, 연도 파서 3벌 소거, 프론트 응답 무효화 훅화 등)는 같은 형태를 그대로 재사용할 수 있다.
