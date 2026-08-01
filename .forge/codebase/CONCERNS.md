---
last_mapped_commit: 43f987cb37c2341c3cfeb54e4cf4dc33b4549c64
mapped: 2026-08-01
---

# CONCERNS

현재 코드베이스의 기술 부채·확정 결함·보안 노출·성능 병목·취약 지점·데이터 정합성 위험 목록. 모든 항목을 HEAD(`43f987c`) 기준으로 재추적했고, 다음을 **실제로 실행해** 검증했다.

- `bash scripts/check.sh` 전량 실행 → **12종 파일 검증 + ESLint + 라이브 Neo4j 연대 검증 전부 PASS**
- `frontend/dist/assets/` 실측(raw·gzip 바이트)
- 기동 중인 스택(`localhost:8080` = prod `biblemap.taebro.com`)에 `curl`로 응답 헤더·페이로드 크기·레이턴시 측정
- `data/` ↔ 하드코딩 테이블 교차 대조(파이썬 일회성 대조, 쓰기 없음)
- `frontend/src/` · `backend/` 정적 grep(마커·중복·리스너 부재)

직전 매핑(`70f5fc6`, 2026-07-24) 이후 3커밋(`87846fb` 콘텐츠 5종, `415374f` 후속작업 5종, `43f987c` 비유·기적 era 게이트)에서 **직전 문서가 지적한 항목 다수가 실제로 해소**됐다. 아래 첫 절에서 해소/잔존을 분리한다.

---

## 직전 매핑 지적 사항 사후 검증

### 해소됨 (RESOLVED — 재확인 완료)

| 항목 | 검증 방법 | 결과 |
|---|---|---|
| **ESLint 7 errors + 1 warning** | `scripts/check.sh`의 `npx --no-install eslint src` | **0건.** `frontend/src/sketches/SceneLabel.jsx` 분리·`frontend/src/useTourPlayback.js` 분리·`set-state-in-effect` 제거로 규칙 완화 없이 해소(`415374f`, task#253) |
| **메인 번들 ≈639KB** | `frontend/dist/assets/` 실측 | **`index-CBiAjk8N.js` 250,811 B(gzip 61,426).** 투어 스케치 9모듈이 `tourSketches-Dwfi4Y4b.js` 391,399 B로 분리 — `frontend/src/IntroView.jsx:5`·`frontend/src/TourPlayback.jsx:5`의 `lazy(() => import('./tourSketches'))` |
| **Person 생몰 Ussher 드리프트 검증 위반 5건** | 라이브 `backend/scripts/validate_event_chronology.py`(Neo4j 접속) | **위반 0.** `data/date_corrections/events.json`·`persons.json` 교정 + ADR `260724-111632`로 ADR-0014 Person 조항 부분 개정. **단, "계(scale) 불일치" 자체는 미해소 — 아래 데이터 정합성 §1 참조** |
| **모바일 지도 세계축소(아프리카) 프레이밍 버그** | 코드 확인 | `frontend/src/MapView.jsx:17-33` `clampPadding`(축별 패딩 합을 컨테이너의 60%로 클램프) + `:88` `map.on('load')` 내 `map.resize()`를 `setMapLoaded` **이전에** 호출해 프레이밍 effect보다 선행 |
| **신규 데이터 디렉터리 4종 미커밋** | `git status` | 전부 커밋됨(`87846fb`). `data/covenants/`·`data/messianic_prophecies/`·`data/topical_verses/`·`data/jesus_parables_miracles/` 모두 추적 중 |
| **ERA_BANDS 3중 중복에 정합 게이트 없음** | 스크립트 실행 | `backend/scripts/validate_era_bands_consistency.py` 신설 — TimelineView↔stats.py 경계·이름·순서 + persons.py `_ERA_ORDER` 순서 + covenants.json `era` 유효성 검사, `scripts/check.sh` 배선. **단 커버리지 부분적 — 아래 데이터 정합성 §4** |
| **비유·기적 지도↔연표 커버리지 무경고 누락 17건** | 스크립트 실행 + 코드 확인 | `backend/scripts/validate_pm_map_coverage.py`가 누락 17건을 `EXPECTED_UNMAPPABLE` 정본으로 고정(회귀·미해석 `placeId` 탐지). UI도 `frontend/src/MapView.jsx:336-342`에서 "위치 없는 비유 N건은 연표에서" 안내 |
| **데이터 검증 스크립트 CI 미연결** | `deploy.sh` 게이트 단계 | `scripts/check.sh`가 배포 전 하드 게이트로 배선. 실패 시 `exit 1`로 배포 중단. 무음 스킵 경로 2개는 `CHECK_STRICT=1`로 **해소**(task#259, 배포/운영 §1) |
| **투어 정차지 장면 커버리지 자동 게이트 부재** | 스크립트 실행 | `backend/scripts/validate_scene_coverage.py` 신설 — 정차지 275건↔스케치 키 275건 양방향 대조 + `tourSketches.jsx` 미병합 모듈 탐지, `scripts/check.sh` 배선(task#259) |
| **언약 리본 `marginLeft:auto` 클리핑** | 직전 세션 수정 확인 | `frontend/src/TimelineView.jsx` 잔존 없음 |

### 잔존 (아래 각 절에서 상세)

`deploy.sh`의 `load_*` 미배선(의도된 결정 — ADR `260801-195022`) · 캐시 무효화가 재시작 의존 · "큐레이션 13인" 주석 드리프트 · CORS `*` · `words.py` 전수 스캔 · `search.py` 전역 스캔 · `journey.py` 무캐시 · 오버레이 빈 폴백 비대칭 · `api.js` 캐시·디듀프 부재 · SPA `hashchange` 미청취 · 대형 컴포넌트 · 대용량 오버레이 상주 · 의존성 caret 미고정 · 백엔드 테스트 0건(의도된 결정 — ADR `260801-195023`).

---

## Known Bugs (확정 결함)

### 1. `generate_approx_book_verses.py`의 `VERSE_MAP`이 이미 죽어 있다 — 실행 즉시 종료

**심각도: 중간 · 시급도: 중간(재실행 시점에 100% 실패)**

`backend/scripts/generate_approx_book_verses.py`의 `VERSE_MAP`(39항목) 중 **7항목(고유 eventId 4개)이 `data/book_events/books.json`에 더는 존재하지 않는다**. 4개 모두 `data/event_dedupe/dedupe.json` 원장에 등장 — 즉 `backend/scripts/apply_event_dedupe.py`가 병합·삭제하고 `data/book_events/books.json`을 다시 쓰면서 `VERSE_MAP`만 남겨둔 결과다.

죽은 eventId(파일 내 `(bookId, eventId)` 쌍): `reca8LvAmFPl1tmnN` · `recYlpu8OdsUJoG8g` · `rec2buqN0Q38Yuqme` · `recGrIgOxWnxVl8h0`(4개 bookId에 중복 등장).

역방향도 어긋난다 — `data/book_events/books.json`의 `authored-*` eventId **7건**(`authored-moses-sinai-law`·`authored-solomon-jerusalem-temple-build`·`authored-paul-ephesus`·`authored-paul-rome-house-arrest` 등)이 `VERSE_MAP`에 미등록이다.

**만졌을 때 깨지는 것**: 스크립트 자신의 가드(`generate_approx_book_verses.py:131-138`)가 첫 죽은 키에서 `sys.exit(1)`을 내므로 **아무 작업도 못 하고 즉시 실패**한다. 책별 근사 절 매핑을 재생성할 수 없다. `scripts/check.sh`는 이 파일을 보지 않는다(생성기이지 검증기가 아니라 게이트 밖).

### 2. `PersonMiniCard`의 연도 포맷터가 정본 헬퍼와 갈라진다 (잠재)

**심각도: 낮음 · 시급도: 낮음(현재 데이터로는 미발현)**

`frontend/src/dates.js:4` `parseYear`는 제로패딩을 벗기지만(`.replace(/^0+/, '')`), `frontend/src/PersonMiniCard.jsx:11-15`의 사본 `fmtYear`에는 그 처리가 없다. `frontend/src/dates.js:1-3` 주석이 `"0049-10-01"` 같은 제로패딩 형식이 실재함을 명시한다. 현재 이 함수는 `birthYear`/`deathYear`(`PersonMiniCard.jsx:33`)에만 쓰이고 라이브 API로 확인한 큐레이션 35인의 값은 전부 비패딩(`'-1085'`·`'30'` 형태)이라 **아직 발현하지 않는다**. 제로패딩 값이 하나라도 들어오면 같은 인물이 화면 위치에 따라 `AD 0049` / `AD 49`로 갈린다.

---

## 데이터 정합성 위험

### 1. Person 생몰 연도와 Event 연대가 서로 다른 연대계 — UI에 나란히 노출 (수용된 한계, 그러나 가시적)

**심각도: 중간 · 시급도: 낮음(명시적으로 수용된 결정)**

`validate_event_chronology.py`의 위반은 0이지만, 그 검증기의 Person 검사(`backend/scripts/validate_event_chronology.py:310` `check_person_scan`)는 **사망<출생**과 **수명>1000년**만 본다. Person의 `birthYear`/`deathYear`를 대응 Event의 `startDate`와 비교하지 않는다(`:112` `check_person_bio_reversal`는 "Birth/Death of X" *이벤트*와 *참여 이벤트*를 비교할 뿐).

라이브 API 실측 대조:

| 인물 | `Person.birthYear`/`deathYear` (Ussher 계) | 대응 Event `startDate` (ADR-0014 보수계) | 격차 |
|---|---|---|---|
| 아브라함 | `-1997` / `-1821` | `Birth of Abraham` = `-2166`, `Death of Abraham` = `-1990` | 169년 |
| 모세 | `-1571` / `-1452` | `Death of Moses` = `-1406` | 46년 |
| 다윗 | `-1085` / `-1015` | `Death of David` = `-970` | 45년 |

두 값이 **동시에 화면에 뜬다** — `frontend/src/PersonIntro.jsx:16-40`(`formatLifespan`)·`:100`이 생몰을, 연표(`frontend/src/TimelineView.jsx`)가 이벤트 연대를 보여준다. ADR `260724-111632`가 "전 인물 일괄 재정렬은 비범위, 남는 scale 불일치는 수용"이라고 명시적으로 인정한 한계다. 다만 **어떤 게이트도 이 격차를 측정하지 않으므로** 향후 확대돼도 검출되지 않는다.

### 2. `load_books.py` 재실행이 교정 연대를 무시하고 업스트림(Ussher) 값을 쓴다

**심각도: 중간 · 시급도: 낮음(수동 실행 스크립트)**

`backend/scripts/load_books.py:80-102` `build_book_year_range()`는 Book의 `startYear`/`endYear`를 **GitHub에서 방금 받아온 원본 이벤트**(`load_books.py:15` `EVENTS_URL`, `:112` `fetch_json`)의 `startDate` 집계로 만든다. 즉 **DB에 적용된 `data/date_corrections/` 교정을 전혀 반영하지 않는다.** `backend/scripts/inject_date_corrections.py`도 Book 노드는 건드리지 않는다.

ADR-0014는 "교정 후 `load_books.py` 재실행이 필요하다"고 적었지만, 실제로 재실행하면 교정과 무관한 Ussher 파생 범위가 다시 쓰인다 — **문서와 구현이 어긋난다.**

**만졌을 때 깨지는 것**: 소비처가 실재한다. `frontend/src/useNodeSelection.js:16-17`이 `startYear`/`endYear`를 읽고 → `frontend/src/TimelineView.jsx:132-133`이 그것으로 연표를 필터링하며 `:375`에 "책 범위" 배너를 띄운다. 라이브 확인: 창세기 `startYear=-4003`(Ussher 창조), `endYear=-1406`. 범위 필터가 보수계 이벤트를 잘못 걸러낼 수 있다.

### 3. `date_corrections` 재적용 footgun — 두 겹

**심각도: 높음 · 시급도: 중간**

- **(a) 로더 재실행이 교정을 되돌린다.** `backend/scripts/load_theographic.py:175-179`가 `SET e.startDate`·`e.sortKey`를 쓰는데 이는 `backend/scripts/inject_date_corrections.py:51-55`가 쓰는 **바로 그 두 속성**이다. `load_theographic.py` 재실행 후 `inject_date_corrections.py`를 잊으면 전 교정이 조용히 소실된다.
- ~~**(b) `deploy.sh`가 재적용하지 않는다.**~~ → **해소(task#259)**: 배포가 게이트 **앞**에서 `inject_ko_names.py`·`inject_date_corrections.py` 2종을 모두 실행한다(둘 다 멱등). 주입이 게이트보다 앞인 이유는 뒤에 두면 아무 일도 못 하기 때문 — 교정이 롤백된 DB에서는 게이트가 먼저 배포를 막고, 게이트가 통과하면 이미 적용돼 있어 no-op이다. **단 `load_*` 로더는 여전히 미배선** — 자동화하면 `build_book_year_range()`가 매 배포마다 교정을 덮어쓴다(위 §2, ADR `260801-195022`).
- **(c) 완화**: `scripts/check.sh`가 배포 전 라이브 `validate_event_chronology`를 돌리므로 교정이 롤백된 상태로는 배포가 **차단된다**. 배포는 `CHECK_STRICT=1`로 부르므로 Neo4j 미기동 시 스킵이 아니라 **실패**다(task#259).
- **(d) 중간값 무음 스킵**: `inject_date_corrections.py:40-51`은 DB 현재값이 `oldStartDate`와도 `newStartDate`와도 다르면 **경고만 찍고 스킵**한다. 교정 테이블의 `newStartDate`만 수정하고 DB가 이전 교정 결과(중간값)를 들고 있으면 재실행이 조용히 아무 일도 안 한다(`.forge/retro/260724-111702-person-chronology-corrections.md`에 실사례).

### 4. 시대(era) 결합점이 5곳인데 검증기는 3곳만 본다

**심각도: 중간 · 시급도: 중간**

시대 이름·경계는 아래 다섯 곳에 각각 하드코딩돼 있다.

1. `frontend/src/TimelineView.jsx:15-24` — `ERA_BANDS`(이름 + `from` 경계)
2. `backend/app/routes/stats.py:24-33` — `ERA_BANDS`(동일 8튜플). `:22-23` 주석이 수동 복제임을 자백
3. `backend/app/routes/persons.py:98` — `_ERA_ORDER`(이름·순서만)
4. `backend/app/routes/persons.py:20-56` — `_ERA`(slug 35개 → era 값)
5. `data/tours/*.json`의 `era` 필드 · `data/covenants/covenants.json`의 `era` 필드
6. (문자열 리터럴) `frontend/src/App.jsx:889` · `frontend/src/TimelineView.jsx:397`의 `=== '신약'` 매직 스트링 — 비유·기적 토글 게이트(task#256)
7. `frontend/src/PersonHub.jsx:9` — `ERA_ORDER` 사본

`backend/scripts/validate_era_bands_consistency.py`는 **1·2·3과 covenants.json만** 검사한다. `_ERA` **값**의 유효성, `data/tours/*.json`의 `era`, `App.jsx`의 `'신약'` 리터럴, `PersonHub.jsx`의 `ERA_ORDER`는 **미검사**다. (일회성 대조 결과 현재는 전부 정합 — `_ERA` 35항목 값·투어 9개 era 전부 유효, `_ERA` slug 집합 == `data/person_events/*.json` 35파일.)

검증기 자체도 취약하다: `validate_era_bands_consistency.py:31`·`:37`이 **파이썬/JSX 소스를 정규식으로 스크래핑**한다(`re.search(r"ERA_BANDS = \[(.*?)\]", ...)`). 포매팅만 바뀌어도 파싱이 깨지고, 그때 `assert tl, "..."`로 실패하므로 배포가 막힌다(fail-closed라 안전 방향이긴 하다).

**만졌을 때 깨지는 것**: `App.jsx:889`의 `'신약'`은 검증 밖이라, 시대 이름을 바꾸면 **비유·기적 토글이 어디서도 안 뜨게 되고 에러도 안 난다.**

### 5. 35 slug 하드코딩 테이블 두 벌이 키 정합을 강제받지 않는다

**심각도: 중간 · 시급도: 낮음**

`backend/app/routes/persons.py:20-56`(`_ERA`)와 `:59-95`(`_NAME_KO`)는 35개 slug를 각각 나열한 병렬 딕셔너리다. `persons.py:119`·`backend/app/routes/places.py:46`이 가드 없이 `_NAME_KO[slug]`를 하므로, `data/person_events/`에 파일을 추가하며 두 딕셔너리 중 하나만 갱신하면 **`KeyError` → 500**이다. 이를 잡는 검증 스크립트가 없다.

### 6. 하드코딩 단일 ID에 매달린 기능 — `_JESUS_ID`

**심각도: 낮음 · 시급도: 낮음**

`backend/app/routes/family.py:92` `_JESUS_ID = "rec..."`. 업스트림 theographic이 이 레코드를 재키잉하면 `_lineage_ids()`(`family.py:96-119`)가 자기 자신만 담은 집합을 돌려주고 모든 노드가 조용히 `lineage: False`가 된다 — **에러도 로그도 없다.** `lru_cache(maxsize=1)`이라 잘못된 답이 프로세스 수명 내내 고정된다.

### 7. `apply_event_dedupe.py`가 `data/`를 되쓰는데 배포는 워킹트리를 하드리셋한다

**심각도: 중간 · 시급도: 낮음**

`backend/scripts/apply_event_dedupe.py:31-33`은 DB뿐 아니라 **저장소의 `data/` JSON 자체**를 다시 쓴다(`person_events`·`verse_events`·`authored_events`·`tours`·`book_events`·`names_ko`·`date_corrections`). 실행하면 미커밋 워킹트리 diff가 생긴다. 그런데 `.github/workflows/deploy.yml:15`는 `git reset --hard origin/main`을 배포 머신 워킹트리(`/Users/calmonion/Project/BibleMap` — 개발 머신과 동일)에서 실행한다. **커밋 전에 push가 발생하면 그 편집이 날아간다.** 위 Known Bugs §1의 `VERSE_MAP` 스테일이 바로 이 스크립트의 파생 효과다.

### 8. 오버레이 빈 폴백이 라우트마다 비대칭

**심각도: 중간 · 시급도: 낮음**

`backend/app/overlays.py:34-43` `_load()`는 파일 부재 시 `{}`, `json.JSONDecodeError` 시 `{}`+WARNING을 돌려준다. `OSError`는 잡지 않아 권한 오류·TOCTOU는 500으로 전파된다. 모든 로더가 `lru_cache(maxsize=1)`(총 **14개**: `overlays.py:46,52,58,64,70,77,83,89,95,101,107,113,121,127`)이라 **기동 시점의 실패가 프로세스 수명 내내 캐시**되고 재시도가 없다.

하류 처리가 갈린다.

- **조용히 빈 200을 주는 쪽**: `backend/app/routes/events.py:119`(`/covenants`)·`:134`(`/messianic-prophecies`)·`:162`(`/topical-verses`)·`:177`(`/parables-miracles`), `backend/app/routes/tours.py:88-94`(주석에 "404 아님" 명시), `backend/app/routes/journey.py:84-88`, `backend/app/routes/persons.py:134`·`:177`, `backend/app/routes/reliance.py:99-101`, `backend/app/routes/family.py:47-48`·`:76-83`(**로그조차 없음**).
- **404를 던지는 쪽**: `backend/app/routes/books.py:89-91`·`:155-157`·`:164-166`, `backend/app/routes/words.py:14-15`·`:25-26`.

즉 `data/names_ko/books.json`이나 `data/word_distribution.json`이 사라지면 책·단어 라우트는 **전 책 404**가 되고, 나머지는 전부 정상 200 + 빈 화면이 된다. 어느 쪽인지 알려줄 헬스/레디니스 엔드포인트가 없다.

---

## Deployment / Ops Risks

### 1. 배포 게이트가 두 경로에서 무음으로 무력화된다 — 그중 하나는 순서 버그 (**해소 — task#259**)

**심각도: 높음 · 시급도: 높음 → 해소**

과거: `scripts/check.sh`가 `frontend/node_modules` 부재 시 ESLint를, `127.0.0.1:7687` 미기동 시 `validate_event_chronology`를 `⊘` 한 줄만 찍고 통과시켰다. 게다가 `deploy.sh`가 `npm install`보다 **먼저** 게이트를 불러 **클린 체크아웃의 첫 배포에서는 ESLint가 항상 스킵**됐다.

해소(ADR `260801-195022`): ① `check.sh`에 `skip()` 헬퍼 도입 — `CHECK_STRICT`가 참이면 두 스킵 분기가 `✗` + `fail=1`이 된다. ② `deploy.sh`가 `CHECK_STRICT=1`로 호출한다. ③ `npm install`·주입 2종을 게이트 **앞**으로 재배치했다. 순서만 고치지 않고 게이트 안에 보증을 내린 이유는, 순서 수정만으로는 누군가 다시 재배치했을 때 같은 무음 통과가 재발하기 때문. 스킵-경고 계약 자체는 단독 개발 실행용으로 남는다(엄격 모드는 배포 호출자만 켠다).

`scripts/check.sh:7`은 여전히 `set -u`만 쓰고 `set -e`/`set -o pipefail`이 없다(`run()` 헬퍼가 종료코드를 개별 수집하므로 치명적이진 않다).

### 2. PR 시점 CI가 전무 — 게이트는 머지 이후에만 돈다

**심각도: 중간 · 시급도: 중간**

`.github/workflows/deploy.yml`이 유일한 워크플로(16줄). `on: push: branches: [main]`만 있고 **`pull_request` 트리거가 없다.** 린트·테스트·빌드 확인이 PR에서 돌지 않는다. 유일한 검증은 `deploy.sh:35`의 `check.sh` — 즉 **main에 머지된 뒤 배포 시점**이다. 빌드 실패도 배포 단계에서야 드러난다.

### 3. 검증 게이트가 라이브 DB 상태에 결합

**심각도: 낮음 · 시급도: 낮음**

`scripts/check.sh`의 연대 검증은 **현재 기동 중인 DB**를 본다. DB가 드리프트하면 코드와 무관한 배포까지 전부 막힌다(fail-closed라 방향은 옳지만, 급한 프론트 수정 배포가 데이터 문제로 블록되는 시나리오가 성립).

### 4. `deploy.sh`의 오류 은폐와 시크릿 취급

**심각도: 중간 · 시급도: 중간**

- ~~`deploy.sh:60` — 주입 호출의 `2>/dev/null`이 stderr 전량을 버려 `NEO4J_PASSWORD` 미설정 예외가 "Neo4j 준비 대기 중" 재시도로 위장됐다~~ → **해소(task#259)**: 도달 대기(소켓 확인)와 주입이 분리되면서 `2>/dev/null`이 제거됐다. 주입 실패는 이제 `set -e`가 그대로 잡는다(`| tee`를 쓰지 않는 이유 — 파이프라인 종료코드가 삼켜져 fail-closed가 깨진다).
- `deploy.sh:29-31` — `.env`를 `set -a`로 export한다. 게이트 호출이 `check.sh` 출력을 `/Users/calmonion/Library/Logs/com.biblemap.deploy.log`에 `tee`하므로, 환경을 덤프하는 하위 프로세스가 하나라도 생기면 자격증명이 로그로 새어 나간다(현재 그런 경로는 없음 — 잠재 위험).
- `backend/scripts/apply_event_dedupe.py:23`만 `os.environ["NEO4J_PASSWORD"]`(맨 `KeyError`)를 쓰고 나머지 스크립트는 친절한 `RuntimeError`를 쓴다 — 비일관.

### 5. 배포 워크플로가 개발 워킹트리를 하드리셋 + 절대경로 하드코딩

**심각도: 중간 · 시급도: 낮음**

`.github/workflows/deploy.yml:13`에 `/Users/calmonion/Project/BibleMap` 절대경로가 박혀 있고 `:15`가 `git reset --hard origin/main`을 한다. 이 디렉터리는 개발 머신 워킹트리이자 `docker-compose.yml:20`의 `./data` 볼륨 마운트 원본이다. push 시점에 미커밋 데이터 편집이 있으면 소실된다(§데이터 정합성 7).

### 6. `deploy.sh` 단계 라벨 어긋남 (코스메틱) (**해소 — task#259**)

과거 `[1/3]`·`[2/3]`·`[3/4]`·`[4/4]`로 분모가 섞였고 검증 단계엔 번호가 없었다. 재배치와 함께 `[1/7]`~`[7/7]`로 통일했다(대기 → 주입 → `npm install` → 게이트 → 빌드 → 이미지 → 기동).

### 7. 프론트 `:8080`은 `frontend/dist` 정적 마운트 (HMR 아님)

`docker-compose.yml:30`. 소스만 고치고 `npm run build`를 안 하면 이전 빌드가 계속 서빙된다. `frontend/dist/`는 `.gitignore:11`로 미추적이라 배포 머신에서 매번 재빌드된다.

---

## Performance Bottlenecks

### 1. nginx에 gzip이 없다 — 정적 자산·API 응답 전부 무압축 전송 (**해소 — task#260**)

**심각도: 높음 · 시급도: 높음 → 해소**

`nginx/nginx.conf`의 `http` 블록에 `gzip on` + `gzip_types`(js/css/json/geo+json/svg/xml) · `gzip_min_length 1024` · `gzip_proxied any` · `gzip_vary on` · `gzip_comp_level 5`를 넣었다. `gzip_proxied any`가 없으면 `/api/*` 프록시 응답이 통째로 빠진다.

배포 후 실측(2026-08-01, `localhost:8080`):

| 경로 | raw | gzip 전송 | 절감 |
|---|---|---|---|
| `vendor-BEFIG7g-.js` | 197,604 | 62,697 | −68.3% |
| `maplibre-B2k4QVOw.css` | 69,808 | 10,152 | −85.5% |
| `/api/stats` | 10,321 | 2,945 | −71.5% |
| `/api/events` | 209,079 | 38,865 | −81.4% |

`frontend/dist/assets/`의 js+css 전체 집계는 **1,935,810 B → 491,063 B (−74.6%)**.

- **레벨 5인 이유**: 사전압축(`gzip_static`)이 없어 요청마다 재압축한다. `vendor.js` 기준 레벨 5는 62,716 B이고 레벨 9도 61,990 B — **0.4% 더 줄이자고 CPU를 더 쓸 이유가 없다**(설정에 `eco:` 주석으로 근거 기록).
- **미도입**: `gzip_static`(vite가 `.gz`를 내지 않음) · brotli(`nginx:alpine`에 모듈 없음). 둘 다 새 빌드 플러그인이나 커스텀 이미지가 필요하다.
- **footgun (신규 확인)**: `docker-compose.yml:31`은 `nginx.conf`를 **단일 파일 bind mount**한다. 에디터가 파일을 inode 교체 방식으로 저장하면 컨테이너는 **옛/잘린 내용을 계속 본다**(이번에 45줄 파일이 컨테이너에서 25줄로 보였다). `docker compose restart nginx`로는 안 고쳐지고 **`up -d --force-recreate nginx`가 필요**하다. 설정 검증은 prod를 건드리기 전에 일회용 컨테이너로 하는 편이 안전하다: `docker run --rm --network biblemap_default -v "$PWD/nginx/nginx.conf:/etc/nginx/nginx.conf:ro" nginx:alpine nginx -t`.

### 2. `maplibre-gl`(1 MB)이 모든 화면의 크리티컬 패스에 있다

**심각도: 중간 · 시급도: 중간**

`frontend/src/MapView.jsx:2-3`이 `maplibre-gl`과 그 CSS를 정적 import하고, `frontend/src/App.jsx:4`가 `MapView`를 정적 import한다. 결과적으로 인트로·인물 허브·통계·성경 리더 등 지도를 전혀 안 쓰는 진입에도 1,027,608 B + 69,808 B CSS가 함께 내려간다. `frontend/vite.config.js:14-19`의 `manualChunks`는 별 청크로 **분리만** 할 뿐 지연 로드하지 않는다. `chunkSizeWarningLimit` 미설정이라 vite 500 kB 경고가 매 빌드 발생하고 무시되고 있다.

### 3. `journey.py`의 슬러그 역매핑이 유일하게 무캐시

**심각도: 중간 · 시급도: 중간**

`backend/app/routes/journey.py:17-30` `_build_id_to_slug()`에 `@lru_cache`가 **없다** — 요청마다 `data/person_events/*.json` **35개 파일**(276 KB)을 열고 파싱한다. `backend/app/routes/journey.py:33-38` `_load_events()`도 무캐시로 매번 재읽기·재정렬한다. 호출처: `journey.py:81`(`GET /person/{id}/journey`), `backend/app/routes/tours.py:119`(`GET /tour/{id}`), `backend/app/routes/stats.py:108`.

같은 일을 하는 형제 모듈은 전부 캐시한다(`backend/app/routes/persons.py:101`·`places.py:21`·`tours.py:57`·`reliance.py:49`). `journey.py`만 예외.

현재 규모에선 체감이 없다(실측 `GET /person/{id}/journey` ≈ 10–16 ms).

### 4. `/words/{book}/verses`가 매 요청 3만여 절 전수 substring 스캔

**심각도: 중간 · 시급도: 낮음(현재 규모에선 ≈10–20 ms)**

`backend/app/routes/words.py:31-37` — 사용자 입력 `w`로 `overlays.bible_verses()` 전 항목(31,103절, 10.3 MB)을 파이썬 루프로 substring 검사한다. 캐시 없음. `:44`의 `total = len(matches)`도 200건만 반환하면서 전수를 센다. 실측: `?w=사랑` 9–20 ms / 65 KB 응답.

### 5. `lru_cache` 키가 사용자 입력인 라우트들 — 캐시 축출 표면

**심각도: 낮음 · 시급도: 낮음**

`backend/app/routes/books.py:61`(`maxsize=2048`, 키 `(book_id, n)`에서 `n` 무제한)·`books.py:105`(`maxsize=66`, 키 `book_id`)·`persons.py:221`·`persons.py:284`·`places.py:21`(각 `maxsize=256`)이 **검증되지 않은 경로 파라미터**를 캐시 키로 쓴다. 무의미한 키를 반복 호출하면 유효 엔트리를 밀어낼 수 있다. 무인증 공개 API라 접근은 자유롭다.

### 6. `stats.py`의 인물별 Neo4j 왕복 (N+1)

**심각도: 낮음 · 시급도: 낮음(상위 캐시로 완화)**

`backend/app/routes/stats.py:105-121` `_compute_longest_journeys()`가 35 slug 루프 안에서 `_fetch_place_coords()`를 호출(`:112`) → 35회 Bolt 왕복 + 35회 무캐시 파일 읽기(`:110`). 상위 `_compute_stats()`가 `lru_cache(maxsize=1)`(`stats.py:124`)이라 프로세스 수명당 1회로 제한된다.

### 7. Cypher가 아니라 파이썬에서 자르는 무제한 쿼리

**심각도: 낮음 · 시급도: 낮음**

`backend/app/routes/nodes.py:17-21`(`/person/{id}/event-ids`)·`:120-123`(`/node/{id}/neighbors/grouped`)이 전 행을 가져와 파이썬에서 truncate(`nodes.py:134`)한다. `backend/app/routes/stats.py:87`도 전 `Event.sortKey`를 끌어와 파이썬에서 시대별로 버킷팅한다(Cypher `CASE` 집계면 8행 1회). `backend/app/routes/family.py:145-195`는 요청당 6회 순차 쿼리를 낸다.

### 8. 대용량 오버레이 JSON 영구 상주

**심각도: 중간 · 시급도: 낮음**

`data/` 총 20 MB / 117 파일. 최대 파일: `data/bible/verses.json` 10,284,836 B · `data/event_verses/events.json` 2,184,907 · `data/word_verse_index/index.json` 1,725,004 · `data/person_relations/relations.json` 1,216,657 · `data/person_context/people.json` 936,603 · `data/verse_persons/index.json` 857,251 · `data/word_distribution.json` 283,953. 전부 `lru_cache(maxsize=1)`로 한 번 접근되면 프로세스 종료까지 파이썬 객체로 상주한다(실제 RSS는 원본 바이트보다 훨씬 크다). uvicorn 단일 워커라 현재는 1벌이지만 워커를 늘리면 워커당 곱해진다.

### 9. `apiGet`에 캐시·디듀프가 없어 같은 엔드포인트를 여러 컴포넌트가 각자 fetch

**심각도: 낮음 · 시급도: 낮음**

`frontend/src/api.js` 전체가 17줄짜리 `fetch` 래퍼다 — 인플라이트 맵도, 메모도, SWR류도 없다. 서버 `Cache-Control`(대부분 `max-age=300`, 일부 `public, max-age=3600`)과 `?v=__BUILD_ID__` 캐시버스터가 유일한 완화책이라, 콜드 로드의 동시 요청은 실제로 중복 전송된다.

| 엔드포인트 | fetch 하는 곳 |
|---|---|
| `/persons/curated` | `frontend/src/useStageNavigation.js:58` · `frontend/src/PersonHub.jsx:201` · `frontend/src/PersonIntro.jsx:69` |
| `/books-overview` | `frontend/src/BibleOverviewView.jsx:198` · `frontend/src/WordDistributionView.jsx:72` · `frontend/src/App.jsx:166` |
| `/event/{id}/verses` | `frontend/src/TimelineView.jsx:175` · `frontend/src/JourneyList.jsx:50` · `frontend/src/SidePanel.jsx:252` |
| `/parables-miracles` | `frontend/src/MapView.jsx:52` · `frontend/src/TimelineView.jsx:80` (둘 다 항상 마운트 — `App.jsx:853`이 MapView를 `display:none`으로 유지) |
| `/node/{id}/places` | `frontend/src/MapView.jsx:124` · `frontend/src/SidePanel.jsx:143` |
| `/person/{id}/relations` | `frontend/src/PersonIntro.jsx:82`(`.length`만 쓰려고 전량 수신) · `frontend/src/RelationsView.jsx:48` |

`useStageNavigation.js:58`과 `PersonHub.jsx:201`은 **지수 백오프 재시도 로직까지 각자 구현**했다. `PersonIntro.jsx:69`는 `useStageNavigation`이 이미 들고 있는 `curatedEraById`/`curatedSlugById`의 한 필드를 얻으려고 전체 목록을 다시 받는다.

### 10. `MapView`의 `/parables-miracles` fetch에 취소 가드가 없다

`frontend/src/MapView.jsx:52-54` — `.catch`는 있으나 `cancelled`/`AbortController` 가드가 없어 언마운트 후 `setPmItems`가 호출될 수 있다. 같은 파일의 다른 fetch(`:120`)는 `AbortController`를 쓴다.

### 11. `search.py` 전역 노드 스캔 (잔존)

`backend/app/routes/search.py:15-31` — 라벨 제약 없는 전역 매치 후 `LIMIT {SEARCH_LIMIT}`. `q`는 파라미터 바인딩이라 인젝션은 아니다.

---

## Security Considerations

- **CORS `allow_origins=["*"]`** — `backend/app/main.py:46-50`. `allow_credentials=False` + `allow_methods=["GET"]` + 무인증 공개 읽기 API라 즉각 위험은 낮지만 완전 개방이다. **심각도: 낮음**
- **Cypher 인젝션 표면 — 라우트 계층은 깨끗하다.** `backend/app/routes/*.py`의 f-string 삽입은 전부 모듈 상수뿐이다(`search.py:15-31`의 `SEARCH_LIMIT`, `stats.py:67-73`의 `TOP_PERSONS_LIMIT`, `family.py:111-116`·`:159-167`의 `MAX_GENERATIONS`, `nodes.py:176-183`의 `NODE_NEIGHBOR_LIMIT`, `main.py:34-35`의 고정 라벨 목록). 사용자 입력은 전부 `$` 파라미터 바인딩.
- **데이터 파일이 Cypher 속성명이 되는 지점** — `backend/scripts/inject_date_corrections.py:66`·`:85`가 `data/date_corrections/persons.json`의 `field` 값을 `p.{field}`로 보간한다. Cypher가 속성명을 파라미터화할 수 없어 구조적으로 불가피하지만 **허용목록 검사가 없다**(현재 값은 `birthYear`·`deathYear` 2종뿐). 저장소 데이터라 외부 입력은 아니다. **심각도: 낮음**
- **시크릿 취급 (양호)** — `.env`는 `.gitignore:14`, 커밋 이력 없음, `.env.example`은 플레이스홀더만. `frontend/.env.production`은 `VITE_API_URL=/api`뿐. `docker-compose.yml:10`·`:18`이 `${NEO4J_PASSWORD:?...}` fail-fast. LLM 저작 스크립트는 `ANTHROPIC_API_KEY`를 환경변수로만 읽는다(`backend/scripts/generate_book_context.py:71-73`·`generate_book_events.py:88-90`). 하드코딩 시크릿 0건.
- **Neo4j 바인딩 (양호)** — `docker-compose.yml:4-6`이 `127.0.0.1`로만 노출. API `:8000`도 호스트 미노출(`docker-compose.yml`의 api 서비스에 ports 없음).
- **레이트리밋·요청 크기 제한 없음** — `nginx/nginx.conf`에 `limit_req`/`limit_conn` 없음. §Performance 4·5의 비용 큰 엔드포인트가 그대로 열려 있다. **심각도: 낮음(공개 읽기 전용) · 시급도: 낮음**
- **배포 로그로의 잠재 유출** — §배포/운영 4 참조.

---

## Fragile Areas

### 1. `MapView`에 리사이즈 리스너가 전혀 없다

**심각도: 중간 · 시급도: 중간**

`frontend/src/MapView.jsx`의 `resize()` 호출은 두 곳뿐이다 — `:88`(`map.on('load')` 내부 1회)과 `:282-284`(`isVisible`/`mapLoaded` 전환 시). **`window` resize 리스너도 `ResizeObserver`도 없다.** 같은 프로젝트의 `frontend/src/FamilyTree.jsx:292`·`WordDistributionView.jsx:65`·`RelianceView.jsx:156`은 `ResizeObserver`를 쓴다 — MapView만 예외.

`App.jsx:853`이 MapView를 `display:none`으로 계속 마운트해 두므로, **브라우저 리사이즈·기기 회전·모바일 URL바 접힘** 시 캔버스가 낡은 크기로 남는다. 게다가 프레이밍 패딩을 만드는 `isMobile`/`sheet` 값은 `window.innerWidth`/`innerHeight` 스냅샷(`MapView.jsx:146-147`·`:215-216`·`:257`)이라 회전 후에도 재계산되지 않는다.

카메라 effect가 5개(`:104`·`:200`·`:227`·`:240`·`:275`)로 흩어져 `mapLoaded` + 겹치는 deps를 공유한다. `:207` 주석이 인물 모드/투어 모드 프레이밍이 서로 카메라를 다툴 수 있어 수동 배제했음을 명시한다. `:259-261`은 `easeTo`에 `offset: undefined`를 넘기면 `Point.convert`가 던져 **React 루트가 통째로 언마운트되던** 크래시를 조건부 스프레드로 우회했음을 기록한다.

### 2. SPA 해시 라우팅이 `hashchange`를 듣지 않는다

**심각도: 중간 · 시급도: 낮음**

`frontend/src/useStageNavigation.js`는 해시를 **마운트 시 1회만** 읽는다(`:38` `initialHashRef`, `:14` lazy initializer). 히스토리 리스너는 `:171`의 `popstate` 하나뿐이고 **`frontend/src/` 어디에도 `hashchange` 리스너가 없다.**

프래그먼트만 바뀌는 동일 문서 내비게이션(`<a href="#/books">`, 주소창 해시 직접 수정, 외부 `location.hash` 대입)은 `popstate`가 아니라 `hashchange`만 발생시킨다. → **URL은 바뀌지만 앱 상태는 안 바뀌고**, 다음 상태 변화 때 `:170-171`의 `replaceState`가 낡은 상태로 사용자 URL을 덮어쓴다. 딥링크가 무시된 것처럼 보인다.

복원은 `:88` `restoredRef`로 1회 게이팅되고 `:87`이 `/persons/curated` 성공에 의존한다(`:58`의 3회 백오프 재시도로 완화되나 최종 실패 시 인물 딥링크가 미해결로 남는다).

`:122`·`:174`에 `eslint-disable-next-line react-hooks/exhaustive-deps` 2건(의도적, 주석으로 근거 명시).

### 3. 응답 무효화 패턴이 3종으로 갈리고 27곳에 손으로 반복

**심각도: 낮음 · 시급도: 낮음(프론트 최대 반복 표면)**

- 수동 `let cancelled = false` — 10파일 19곳: `frontend/src/SidePanel.jsx:105,127,142,154,166` · `PersonIntro.jsx:58,68,81` · `App.jsx:85,165` · `BibleOverviewView.jsx:197,224` · `useStageNavigation.js:56,81` · `RelationsView.jsx:47` · `TopicalVersesView.jsx:14` · `StatsView.jsx:54` · `WordDistributionView.jsx:71` · `TourList.jsx:56`
- `AbortController` — 8파일: `App.jsx:121` · `ChapterReader.jsx:16,27` · `FamilyTree.jsx:207` · `mapRingController.js:112` · `MapView.jsx:120` · `PersonMiniCard.jsx:23` · `RelianceView.jsx:227` · `WordDistributionView.jsx:79`
- id 키잉 state 비교 — `PersonIntro.jsx:59-61` · `SidePanel.jsx`의 `forNodeId` 가드

`App.jsx`와 `WordDistributionView.jsx`는 한 파일 안에서 두 패턴을 섞어 쓴다. 공유 훅이 없다.

### 4. 지도 레이어 색상이 하드코딩 hex라 라이트 테마를 무시한다

**심각도: 낮음 · 시급도: 낮음**

`frontend/src/mapLayers.js`의 maplibre paint 값에 `#c9a84c`·`#8a6d1f`·`#f2ecdc`·`#1a1a2e`·`#58a4e8` 등이 약 20곳 직접 박혀 있다(`:192,193,216,232-241,261,262,282,284,299,330,332,352,366,368,382,404,406,425,452,454,472,489`). `frontend/src/theme.js:5`가 캔버스 컨텍스트에서 CSS 변수를 못 쓰는 이유를 설명하지만, 결과적으로 **ADR-0020의 라이트/다크 토글이 지도 레이어에는 반영되지 않는다.**

### 5. 연도 파싱·시대 분류 로직이 6벌

**심각도: 낮음 · 시급도: 낮음**

- 문자열 파서 3벌(동일 규칙, 주석으로 상호 참조): `frontend/src/dates.js:4` `parseYear` · `backend/app/routes/nodes.py:267-276` `_year`(라우트 핸들러 내부 중첩) · `backend/scripts/load_books.py:56-62` `_parse_year` · `backend/scripts/validate_event_chronology.py:66-71` `_year`
- 프론트 표시용 변형 3벌: `frontend/src/TimelineView.jsx:31-33` `fmtYear`(숫자) · `frontend/src/PersonMiniCard.jsx:11-15` `fmtYear`(문자열, **제로패딩 처리 누락** — Known Bugs §2) · `frontend/src/PersonIntro.jsx:16-40` `formatLifespan`(정수)
- 시대 분류 2벌: `frontend/src/TimelineView.jsx:25-28` `eraOf` · `backend/app/routes/stats.py:36-41` `_era_of`

### 6. 슬러그 해석 구현이 5벌 — 같은 이름의 함수가 다른 집합을 돌려준다

**심각도: 중간 · 시급도: 낮음**

`backend/app/overlays.py:134`(`curated_person_id`) · `backend/app/routes/persons.py:102`(`_build_list`) · `backend/app/routes/journey.py:18`(`_build_id_to_slug`, 무캐시) · `backend/app/routes/reliance.py:49,69`(`_slug_to_id`/`_id_to_slug`) · `backend/app/routes/family.py:71`(`_id_to_slug`, **인장 slug를 포함한 상위집합**). 같은 패키지에 `_id_to_slug`가 두 개 있고 키 집합이 다르다.

### 7. 그 외 중복 상수

- `PM_FILTERS` — `frontend/src/MapView.jsx:12`와 `frontend/src/TimelineView.jsx:10`에 동일 배열. `TimelineView.jsx:9` 주석이 "별 파일이라 상수는 각자 보관"으로 자백
- `PURPLE = TYPE_COLOR.Book` — `frontend/src/TourIntro.jsx:8` · `TourList.jsx:9` · `TourPlayback.jsx:8`
- `GROUND = 'var(--bg-0)'` — `frontend/src/TourList.jsx:10` · `PersonHub.jsx:25`
- 모바일 미디어쿼리 문자열 5곳(`frontend/src/VerseLayer.jsx:11` · `App.jsx:32` · `BibleOverviewView.jsx:16,18` · `PersonHub.jsx:33,35`) + `matchMedia` vs `window.innerWidth <= MOBILE_BREAKPOINT`(`MapView.jsx:146,215,257`) **두 가지 모바일 판정 기제 공존** — 후자는 리사이즈에 반응하지 않는다
- `prefers-reduced-motion` 쿼리 4곳: `frontend/src/MapView.jsx:262` · `tourSketches.jsx:46` · `RelianceView.jsx:81` · `IntroView.jsx:13`
- localStorage 키 `'biblemap-intro'`가 리터럴(`frontend/src/useStageNavigation.js:16`)과 상수(`frontend/src/IntroView.jsx:267` `INTRO_STORAGE_KEY`)로 이중 정의
- `build_range_label` — `backend/scripts/generate_approx_book_verses.py:105` 주석이 `generate_event_verses.py`와 동일 로직임을 명시(복붙 자백)

---

## Tech Debt

### 1. 대형 파일 — 스케치가 프론트 라인 수의 절반

`frontend/src/sketches/` 11파일 합계 **462,928 B / 9,703줄**(전체 `frontend/src` 19,584줄의 약 50%). 1,000줄 초과: `sketches/davidUnitedKingdom.jsx`(1,524) · `sketches/patriarchsCovenant.jsx`(1,259) · `sketches/gospelOfJesus.jsx`(1,207) · `sketches/ageOfJudges.jsx`(1,169) · `sketches/elijahAndElisha.jsx`(1,126) · `frontend/src/App.jsx`(1,081줄 / 51,736 B — **유일한 비스케치 1,000줄 초과**). 다음 티어: `sketches/theEarlyChurch.jsx`(999) · `frontend/src/SidePanel.jsx`(928 / 49,485 B).

스케치는 ADR-0029가 "투어당 1모듈"로 의도한 구조이고 lazy 청크로 격리됐으므로 부채 성격이 다르다. **`App.jsx`·`SidePanel.jsx`가 실질적 부채다.**

### 2. "큐레이션 13인" 주석 드리프트 — 실제는 35인, 새 사례까지 추가됨

**심각도: 낮음 · 시급도: 낮음**

실제 큐레이션 인물은 **35명**(`data/person_events/` 35파일 = `persons.py:20-56` `_ERA` 35키, 일회성 대조 확인). 그런데 주석은:

- `backend/app/routes/persons.py:1` · `:136` — "13인"
- `backend/app/routes/persons.py:287` — "34인"
- `backend/app/routes/journey.py:1` · `:77` — "13인"
- `backend/app/routes/stats.py:105` — **"큐레이션 13인"(신규 유입)**

`backend/app/routes/family.py:16`·`:72`만 "35"로 정확하다.

### 3. `chunkSizeWarningLimit` 미설정 + 앱 코드 분할 없음

`frontend/vite.config.js:12-21`의 `manualChunks`는 `node_modules`만 `maplibre`/`vendor`로 가른다. 앱 코드는 `tourSketches` 하나만 lazy(§Performance 2). 500 kB 경고가 매 빌드 발생한다.

### 4. `Cache-Control` 정책이 라우트마다 제각각

`max-age=300`(대다수, `public` 없음) / `public, max-age=3600`(`backend/app/routes/books.py:101,158,167` · `verses.py:47` · `reliance.py:155,175`) / `no-store`(`backend/app/routes/books.py:33`). `frontend/src/api.js:5` 주석은 `max-age=3600`만 언급해 실제와 어긋난다.

### 5. `deploy.sh`가 재적용하지 않는 DB 쓰기 스크립트 14종

`deploy.sh`가 도는 건 `inject_ko_names.py` 하나, `README.md:20-22`가 문서화한 건 3종. **나머지는 문서에도 배포에도 없다**: `backend/scripts/load_books.py` · `load_person_events.py` · `load_verse_events.py` · `load_authored_events.py` · `load_authored_persons.py` · `load_authored_genealogy.py` · `load_authored_mothers.py` · `inject_book_context.py` · `inject_person_context.py` · `inject_person_traits.py` · `inject_place_context.py` · `apply_event_dedupe.py` · `enrich_place_coords.py` · `generate_book_events.py`. 로더 재적재 후 이들이 전부 드리프트한다.

### 6. 캐시 무효화 수단이 사실상 `docker compose restart api` 하나

`data/`는 볼륨 마운트(`docker-compose.yml:20`)라 파일 수정에 이미지 재빌드가 불필요하지만, `overlays.py`의 14개 `lru_cache(maxsize=1)` + 라우트 레벨 캐시(`events.py`의 `_load_approx_book_index`·`_compute_events`·`_book_name_map`, `stats.py:124`의 `_compute_stats` 등)가 프로세스 로컬이라 **반영은 재시작뿐**이다. TTL도 무효화 API도 없다.

### 7. 배치되지 않은 행 단위 쓰기

`backend/scripts/inject_ko_names.py:31-32`와 `backend/scripts/inject_date_corrections.py:31-56,62-88`이 `UNWIND` 배치 대신 파이썬 루프에서 행마다 쿼리를 낸다(events 교정 256건 × 2쿼리). `deploy.sh`의 주입 단계가 느린 이유.

---

## Dependencies at Risk

- **`anthropic` · `kiwipiepy`가 어디에도 선언돼 있지 않다.** `backend/requirements.txt`는 `fastapi==0.136.3` · `neo4j==6.2.0` · `uvicorn==0.49.0` 3줄뿐이다. `anthropic`은 5개 스크립트가 import한다(`backend/scripts/generate_book_events.py:17` · `generate_book_context.py:20` · `generate_person_context.py:25` · `generate_verse_events.py:16` · `generate_person_traits.py:21`). `kiwipiepy`는 `backend/scripts/build_word_verse_index.py:35,45`와 `build_word_distribution.py:37`이 함수 내부에서 import하며, 도커스트링(`build_word_verse_index.py:17`)이 임시 venv 설치를 안내한다 — **현재 이 머신에 미설치**(확인함). `requirements-dev.txt`·락파일·파이썬 버전 고정 없음. **심각도: 중간 · 시급도: 낮음**
- **`backend/Dockerfile:5`가 `app/`만 복사한다** — `scripts/`가 이미지에 없다. 그래서 `deploy.sh:60`이 **호스트 `python3`**로 주입 스크립트를 돌린다(호스트에 우연히 깔린 패키지에 의존). 재현성 구멍.
- **theographic 원본을 GitHub `master` HEAD에서 미고정 fetch** — `backend/scripts/load_books.py:14-15`(`BOOKS_URL`·`EVENTS_URL`), `load_theographic.py` 동일 패턴. 업스트림이 바뀌면 재적재 결과가 조용히 달라진다.
- **프론트 의존성 전부 caret, 고정 0건** — `frontend/package.json`: `react ^19.2.6` · `react-dom ^19.2.6` · `maplibre-gl ^5.24.0` · `lucide-react ^1.17.0` · `vite ^8.0.12` · `eslint ^10.3.0` · `eslint-plugin-react-hooks ^7.1.1` 등. `package-lock.json`이 있어 평시엔 고정되지만, 락 재생성 시 `deploy.sh:44`의 `npm install`이 그대로 프로덕션 빌드로 간다.
- **`docker-compose.yml:3` `image: neo4j:5`** — 메이저만 고정, 마이너/패치는 부동.
- **빌드타임 외부 API 의존** — 절 본문 프리베이크(getbible)·LLM 저작 스크립트(Anthropic API). 재현에 외부 서비스와 API 키가 필요하다.

---

## Test Coverage Gaps

- ~~**자동화 테스트 0건.**~~ → **부분 해소(task#261)**: 프론트 순수 함수 3모듈에 vitest 73건(`urlState`·`mapGeo`·`mapRingController`), `npm test`로 실행되고 `scripts/check.sh`의 프론트 블록에 배선됐다. **백엔드 pytest는 여전히 0건 — 의도된 결정**(ADR `260801-195023`: Neo4j 없이 테스트 가능한 라우트가 둘뿐이라 회수가 적다). React 렌더 테스트·커버리지 도구도 의도적 미도입.
- **ESLint·유닛 테스트는 PR에서 안 돈다.** `npm run lint`/`npm test`는 수동이거나 배포 게이트 시점. 게이트의 프론트 블록은 `frontend/node_modules` 부재 시 스킵이지만, 배포는 `CHECK_STRICT=1`로 호출하므로 **스킵이 곧 실패**다(task#259). PR 시점 CI가 없는 건 그대로(이 프로젝트는 PR을 쓰지 않는다).
- ~~**ADR-0029가 약속한 투어 정차지 ↔ 장면 스케치 커버리지 대조 스크립트가 없다.**~~ → **해소(task#259)**: `backend/scripts/validate_scene_coverage.py`가 양방향 대조(275↔275) + `tourSketches.jsx` 미병합 모듈까지 잡고 `scripts/check.sh`에 배선됐다.
- **시대 결합 검증이 부분 커버**(§데이터 정합성 4) — `_ERA` 값·투어 JSON `era`·`App.jsx:889`의 `'신약'` 리터럴 미검사. 게다가 `validate_era_bands_consistency.py`가 **소스 정규식 스크래핑** 방식이라 포매팅 변경에 취약.
- **`_ERA` ↔ `_NAME_KO` 35키 정합 검증 없음**(§데이터 정합성 5).
- **`data/authored_persons/` 전용 validate 없음** — 다른 저작 데이터 12종은 검증기가 있다.
- **하드코딩 ID 테이블 스테일 검출 게이트 없음** — Known Bugs §1이 그 부재의 직접 결과.
- **Person 생몰 ↔ Event 연대 계 격차 측정 게이트 없음**(§데이터 정합성 1).
- **`/node/{id}` vs `/node/{id}/neighbors/grouped` 동작 일치 테스트 없음** — `backend/app/routes/nodes.py:120-147`의 `get_node_neighbors_grouped`는 여전히 `-[r]-(m)` 무방향 매치에 정규화·디듀프가 없다. 유일 소비처 `frontend/src/mapRingController.js:112`가 응답의 Event만 읽어 현재 UI 영향은 없다.
- **UI 검증은 Playwright 수동 실행 의존**, CI 미연동. 증적은 `.forge/reports/`의 수동 캡처뿐.
- **헬스/레디니스 엔드포인트 없음** — 오버레이 로딩 실패(§데이터 정합성 8)나 Neo4j 인덱스 생성 실패(`backend/app/main.py:37-38`이 예외를 삼키고 계속 진행)를 외부에서 알 방법이 없다.

---

## Scaling Limits

- **단일 인스턴스 스택** — neo4j 1 + api 1 + nginx 1(`docker-compose.yml`). `backend/Dockerfile:6`의 CMD에 `--workers` 없음 → uvicorn 단일 워커. 요청 처리가 한 프로세스에 직렬화된다(비용 큰 동기 엔드포인트 §Performance 4가 이벤트 루프를 점유).
- **`lru_cache`가 프로세스 로컬** — 공유 캐시 계층이 없어 워커를 늘리면 §Tech Debt 8의 20 MB JSON 상주가 워커 수만큼 곱해지고, 무효화도 워커별로 갈린다.
- **정적 자산·API 모두 무압축**(§Performance 1) — 대역폭이 인스턴스 수보다 먼저 병목이 된다.

---

## 코드 마커 현황 (참고)

`TODO`/`FIXME`/`HACK`/`XXX`/`나중에`/`임시` 마커는 **`backend/`·`frontend/src/`·`scripts/` 전체에 0건**이다. 이 코드베이스는 `task#NNN`·`ADR-NNNN` 참조 주석을 부채 추적 관용구로 쓴다(예: `frontend/src/MapView.jsx:15` "선재 버그, task#251", `backend/app/routes/stats.py:22-23` "공유 설정이 없어 수동 복제"). 위 항목 다수가 그런 자백 주석에서 출발했다. `eslint-disable`은 4건뿐이며 전부 한 줄 범위 + 근거 주석 동반(`frontend/src/useStageNavigation.js:122,174` · `VerseLayer.jsx:21` · `personSymbols.jsx:488`). `backend/app/`에 `print()`·root logger 직호출 0건으로 `CLAUDE.md`의 로깅 규약을 지키고 있다.
