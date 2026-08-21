---
last_mapped_commit: 4ad1d837a3771f69f53877b128938124b68d920b
mapped: 2026-08-21
---

# CONCERNS

현재 코드베이스의 기술 부채·확정 결함·보안 노출·성능 병목·취약 지점·데이터 정합성 위험 목록. 최초 전면 매핑은 HEAD `43f987c` 기준이었고, 이후 task#259~284 커밋들이 실어 나른 부분 갱신 + 이번 갱신(HEAD `4ad1d83`)까지 누적 반영됐다. 이번 갱신에서 다음을 **실제로 실행해** 검증했다.

- `bash scripts/check.sh` 전량 실행 → **20종 파일 검증 + 정합 대조군(selftest) 7종 + forge 문서 추적 가드 2종 + ESLint + 유닛 테스트(vitest) + 라이브 Neo4j 연대 검증, 총 32항목 전부 PASS**(커밋 `4ad1d83`의 완료기준 `✓32 ✗0`와 재확인 일치)
- `a002881..4ad1d83` 11커밋의 diff·커밋 메시지·관련 ADR·retro 대조(task#278·279·280·281·282~284)
- `backend/app/curated.py`·`validate_curated_persons.py`·`validate_sortkey_startdate.py`·`validate_event_verses.py`·`validate_era_bands_consistency.py`(신설/대폭 확장 5종) 원문 확인
- `git status`로 미커밋 잔존 확인(`.claude/settings.local.json.doctor-backup` 미추적)

직전 매핑(`70f5fc6`, 2026-07-24) 이후 3커밋(`87846fb` 콘텐츠 5종, `415374f` 후속작업 5종, `43f987c` 비유·기적 era 게이트)에서 **직전 문서가 지적한 항목 다수가 실제로 해소**됐다. 아래 첫 절에서 해소/잔존을 분리한다.

이 문서는 이후에도 관련 태스크 커밋(task#259~277)에 실려 그때그때 부분 갱신됐다. `a002881` 갱신은 그 부분 갱신에서 놓친 항목을 마저 닫았다 — **Known Bugs 2건 모두 해소**(VERSE_MAP 죽은 키 · PersonMiniCard 연도 포맷터 분기), **`Book.startYear/endYear`가 교정 연대의 파생값으로 봉인**(§데이터 정합성 2), ERA_BANDS가 `frontend/src/eraBands.js`로 승급, 절 본문 전수 스캔이 `verse_search.py`로 공용화(§성능 4).

**이번 갱신(HEAD `4ad1d83`)은 task#278·280~284가 3개 더 닫았다** — ① 큐레이션 35 slug 두 벌 하드코딩(`_ERA`/`_NAME_KO`)이 `backend/app/curated.py`의 단일 `CURATED` 리터럴로 병합되고 `validate_curated_persons`로 게이트됨(§데이터 정합성 5), 그 부산물로 `journey.py`의 무캐시 슬러그 역매핑도 해소(§성능 3). ② 교차-장·장 단위 근거 절 범위가 대표절 1개만 베이킹되던 결함이 오프라인 절 사전 오라클 기반으로 재베이킹되고 `validate_event_verses`로 게이트됨(§데이터 정합성 9). ③ `sortKey`↔`startDate` 역전 잔존 2건(+신규 발견 1건)이 교정되고 전역·교차파일 `validate_sortkey_startdate`로 게이트됨(§데이터 정합성 1). era 결합점도 4→7축으로 검증 범위가 확장돼 시대명 변경 시 무음 실패하던 경로 대부분이 닫혔다(§데이터 정합성 4). task#280·281은 인트로 화면의 여백·무해시 라우팅 결함 2건을 고치고 각각 소스 불변식 게이트를 남겼다(둘 다 이 문서의 기존 항목이 아니었던 신규 발견·즉시 해소라 별도 절을 두지 않았다).

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
| **투어 정차지 장면 커버리지 자동 게이트 부재** | 스크립트 실행 | `backend/scripts/validate_scene_coverage.py` 신설 — 정차지↔스케치 키 양방향 대조(task#264~266의 출애굽~정복 21건 보강 이후 **296건**↔296건) + `tourSketches.jsx` 미병합 모듈 탐지, `scripts/check.sh` 배선(task#259) |
| **언약 리본 `marginLeft:auto` 클리핑** | 직전 세션 수정 확인 | `frontend/src/TimelineView.jsx` 잔존 없음 |
| **`VERSE_MAP`의 죽은 eventId 4개 — 재실행 즉시 `sys.exit(1)`** | `ast.literal_eval`로 `VERSE_MAP` 추출 후 `data/book_events/books.json`과 교차 대조 | **죽은 키 0 · 미커버 0.** task#273(`2caf509`)이 `authored-*` 신원으로 재매핑했고, task#274(`53c94a1`)가 `backend/scripts/validate_approx_book_verses.py`로 이 조건을 배포 게이트에 **재현**(생성기는 실행하지 않음, ADR `260820-003946`) — `scripts/check.sh`의 15종 검증에 배선. 같은 결함 클래스가 `persons.py`의 `_ERA`/`_NAME_KO` 35 slug에 아직 남아 있다(§데이터 정합성 5) |
| **`PersonMiniCard`의 연도 포맷터가 정본 헬퍼와 갈라짐** | 코드 확인 | task#262(`4353f34`)가 `PersonMiniCard.jsx`의 로컬 `fmtYear`를 지우고 `frontend/src/dates.js`의 `parseYear`를 직접 import — 제로패딩 분기가 사라져 갈라질 수 없다 |
| **`load_books.py` 재실행이 교정 연대를 무시하고 업스트림 값을 쓴다** | `inject_date_corrections.py` diff 확인 + 라이브 실행 없이 정적 대조 | task#273(ADR `260819-233305`)이 `inject_date_corrections.py`에 `recompute_book_years()`를 추가 — 교정 주입 직후 `CONTAINS_BOOK` 사건의 교정 후 `startDate`로 `Book.startYear/endYear`를 재집계해 SET한다. `deploy.sh`가 이미 이 스크립트를 게이트 앞에서 부르므로 배포 경로에서 자동으로 닫힌다(§데이터 정합성 2) |

### 잔존 (아래 각 절에서 상세)

`deploy.sh`의 `load_*` 미배선(의도된 결정 — ADR `260801-195022`) · 캐시 무효화가 재시작 의존 · CORS `*` · `words.py`·`search.py` 공용 절 전수 스캔(`verse_search.py`, task#267로 두 라우트가 공유) · 오버레이 빈 폴백 비대칭 · `api.js` 캐시·디듀프 부재 · SPA `hashchange` 미청취 · 대형 컴포넌트(`SidePanel.jsx`, `App.jsx`는 task#257~258 분해로 이탈) · 대용량 오버레이 상주 · 의존성 caret 미고정 · 백엔드 테스트 0건(의도된 결정 — ADR `260801-195023`) · `content-box`+패딩 결함 클래스가 인트로 5곳만 봉인되고 나머지 화면은 미조사(ADR `260820-232144`) · `validate_curated_persons`가 `person_events` JSON 내용은 파싱하지 않음.

---

## Known Bugs (확정 결함)

**현재 0건 — 이전에 지적된 2건 모두 해소.**

- ~~`generate_approx_book_verses.py`의 `VERSE_MAP` 죽은 키 4개(`authored-*` 재키잉 이전 신원)로 재실행 즉시 `sys.exit(1)`~~ → **해소(task#273~274)**. `backend/scripts/generate_approx_book_verses.py`의 `VERSE_MAP`은 `apply_event_dedupe.py` 병합 이후 신원(`authored-moses-sinai-law` 등)으로 재매핑됐고, 지금은 `data/book_events/books.json`과 **39쌍 양방향 완전 일치**(죽은 키 0·미커버 0, 직접 실행해 확인). 이 조건은 이제 생성기 안에만 갇혀 있지 않다 — `backend/scripts/validate_approx_book_verses.py`가 `VERSE_MAP` 리터럴을 `ast.literal_eval`로 직접 읽어(실행 0) 같은 가드를 배포 게이트에 재현하고(ADR `260820-003946`), `scripts/check.sh`에 배선돼 있다. 같은 결함 클래스(하드코딩 slug 테이블 ↔ 데이터 드리프트)가 `persons.py`의 `_ERA`/`_NAME_KO` 35 slug에는 아직 게이트 없이 남아 있다 — §데이터 정합성 5.
- ~~`PersonMiniCard`의 로컬 `fmtYear`가 제로패딩 처리 누락으로 `frontend/src/dates.js`의 `parseYear`와 갈라질 잠재 위험~~ → **해소(task#262)**. `frontend/src/PersonMiniCard.jsx:4,27`가 이제 `dates.js`의 `parseYear`를 직접 import해 쓴다 — 로컬 사본이 없어 갈라질 수 없다.

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

**(추가 축) 저작 Event들 *사이*의 연대계 불일치 — 구약 잔존.** 위가 Person↔Event 축이라면, 이것은 **저작 사건끼리** 서로 다른 기준연대를 써서 정렬이 뒤집히는 축이다. 인물 파일마다 자기 연대계로 `sortKey`를 잡은 결과이며, task#233·234·235(투어 커버리지)·#236(감사)에서 반복 발견돼 포함분은 그때그때 교정됐다.
- **신약은 해소됨** — task#237·238이 33 앵커 프레임으로 전 구간(세례 26~순교 66)을 이관해 층간 정합 완성.
- **구약은 잔존** — 대표 사례: `이삭 출생 -2000`이 `모리아 번제 -2055`·`사라 장사 -2030`보다 **뒤로** 정렬된다(아브라함 연대계는 부르심 -2091 기준, 이삭 연대계는 출생 -2000 기준). task#233이 기록만 하고 수술적 원칙에 따라 미교정. 교정하려면 **이삭 연대계 전체 재정규화**가 필요해 별도 태스크 감이다. `data/person_events/isaac.json`은 이번 갱신(task#282~284)에서도 손대지 않았다 — 신설된 `validate_sortkey_startdate.py`(아래 자매 축 참조)가 전역 sortKey 인접쌍 역전은 게이트하지만, 이 사례가 그 인접쌍에 걸리는지는 검증되지 않았다(아브라함·이삭 파일 사이에 다른 사건들이 끼어 있으면 비인접 역전은 이 게이트의 판정 범위 밖일 수 있다).
- **검출 수단 없음** — `validate_event_chronology.py`는 앵커 대비 역전과 형제군 이탈은 보지만, "인물 파일별 기준연대가 서로 다름"은 보지 않는다. 새 정차지·사건을 추가할 때는 **인접 앵커와 직접 대조**하는 수밖에 없다(투어 커버리지 3부작이 매번 그렇게 잡았다).
- **자매 축 — `sortKey` 순서와 `startDate` 순서의 역전(task#265 발견) — 해소(task#283).** 위가 "사건들 사이의 기준연대 불일치"라면 이것은 **같은 사건의 두 필드가 서로 다른 순서를 말하는** 축이다. `sortKey`는 서사 순서를, `startDate`는 화면 연도를 결정하므로 역전되면 정렬과 라벨이 갈린다. **기존 잔존 2건**이 교정됐다 — `authored-joshua-divine-commission` `startDate -1407→-1406`(수 1:1 "모세가 죽은 후" — `authored-moses-death-moab`의 -1406과 역전 해소), `authored-joshua-gibeon-alliance` `startDate -1405→-1403`(에발 -1404 ~ 원정 -1402 사이). 같은 라운드에서 파일 내부 역전 1건도 함께 잡혔다: `data/person_events/david.json`의 `authored-david-gibeah-harp` `startDate -1023→-1026`(sortKey -1026과 통일 · 삼상 16:14–23이 기름부음과 같은 서사 단위). `backend/scripts/validate_sortkey_startdate.py`(신설)가 **전 인물 파일을 sortKey로 전역·교차파일 정렬**한 인접쌍의 startDate 역전 0을 게이트로 강제한다(`scripts/check.sh` 배선, `--selftest` 있음) — task#264~266의 "신규분만" 범위 한계(파일 단위로 좁혀 moses→joshua 경계가 무음 통과하던 문제)를 해소했다. 같은 검증기가 **둘째 축**도 본다: `TimelineView`가 저작 사건에 표시하는 연도는 `startDate`가 아니라 `yearLabel`이라, 정렬은 맞아도 화면 라벨이 옛 연도를 보여주는 드리프트 2건(`joshua-divine-commission`·`joshua-farewell-death`의 `yearLabel`)도 같은 커밋에서 함께 교정·게이트됐다. **단, 이 게이트는 "전역 정렬의 인접쌍"만 본다** — 아래 이삭 사례처럼 sortKey 정렬상 인접하지 않은 두 사건 사이의 연대계 불일치(비인접 역전)는 이 검증기의 판정 범위 밖일 수 있다.

### 2. ~~`load_books.py` 재실행이 교정 연대를 무시하고 업스트림(Ussher) 값을 쓴다~~ (해소 — task#273)

**심각도: 중간 · 시급도: 낮음 → 해소**

과거: `backend/scripts/load_books.py:80-102` `build_book_year_range()`는 Book의 `startYear`/`endYear`를 GitHub 원본 이벤트의 `startDate` 집계로 만들어, `data/date_corrections/` 교정을 반영하지 않았다(ADR-0014의 "재실행 필요" 문서와 구현이 어긋났다).

해소(ADR `260819-233305`): `backend/scripts/inject_date_corrections.py`에 `recompute_book_years()`를 추가해, 교정 이벤트 주입 **직후** `CONTAINS_BOOK` 관계로 연결된 사건의 **교정 후** `startDate`를 다시 집계해 `Book.startYear/endYear`를 SET한다. 연도 파싱은 `load_books.py::_parse_year`를 import해 재사용(4번째 파서 선언 금지, ADR `260819-205242`). `deploy.sh`가 이미 이 스크립트를 게이트 앞에서 매 배포 호출하므로(§배포/운영 3), 정본 파생값이 배포 경로에서 자동으로 닫힌다. `load_books.py` **단독** 실행 직후에는 여전히 업스트림 값이 남지만, 이는 기존 "로더 재실행 후 inject 재실행 필수" 규약에 흡수된다.

소비처는 여전히 실재한다: `frontend/src/useNodeSelection.js`가 `startYear`/`endYear`를 읽고 `frontend/src/TimelineView.jsx`가 연표 필터·"책 범위" 배너에 쓴다 — 이제 그 값이 정본 연대계를 따른다.

### 3. `date_corrections` 재적용 footgun — 두 겹

**심각도: 높음 · 시급도: 중간**

- **(a) 로더 재실행이 교정을 되돌린다.** `backend/scripts/load_theographic.py:175-179`가 `SET e.startDate`·`e.sortKey`를 쓰는데 이는 `backend/scripts/inject_date_corrections.py:51-55`가 쓰는 **바로 그 두 속성**이다. `load_theographic.py` 재실행 후 `inject_date_corrections.py`를 잊으면 전 교정이 조용히 소실된다.
- ~~**(b) `deploy.sh`가 재적용하지 않는다.**~~ → **해소(task#259)**: 배포가 게이트 **앞**에서 `inject_ko_names.py`·`inject_date_corrections.py` 2종을 모두 실행한다(둘 다 멱등). 주입이 게이트보다 앞인 이유는 뒤에 두면 아무 일도 못 하기 때문 — 교정이 롤백된 DB에서는 게이트가 먼저 배포를 막고, 게이트가 통과하면 이미 적용돼 있어 no-op이다. **단 `load_*` 로더는 여전히 미배선** — 자동화하면 `build_book_year_range()`가 매 배포마다 교정을 덮어쓴다(위 §2, ADR `260801-195022`).
- **(c) 완화**: `scripts/check.sh`가 배포 전 라이브 `validate_event_chronology`를 돌리므로 교정이 롤백된 상태로는 배포가 **차단된다**. 배포는 `CHECK_STRICT=1`로 부르므로 Neo4j 미기동 시 스킵이 아니라 **실패**다(task#259).
- **(d) 중간값 무음 스킵**: `inject_date_corrections.py:40-51`은 DB 현재값이 `oldStartDate`와도 `newStartDate`와도 다르면 **경고만 찍고 스킵**한다. 교정 테이블의 `newStartDate`만 수정하고 DB가 이전 교정 결과(중간값)를 들고 있으면 재실행이 조용히 아무 일도 안 한다(`.forge/retro/260724-111702-person-chronology-corrections.md`에 실사례).

### 4. 시대(era) 결합점 — 대부분 해소(task#284로 4→7축 게이트)

**심각도: 낮음(과거 중간) · 시급도: 낮음 → 대부분 해소**

시대 이름·경계는 아래 각 곳에 하드코딩돼 있다.

1. `frontend/src/eraBands.js:9-18` — `ERA_BANDS`(이름 + `from` 경계). task#271(ADR `260819-205242`)로 `TimelineView.jsx`에서 이 전용 모듈로 승급.
2. `backend/app/routes/stats.py:24-33` — `ERA_BANDS`(동일 8튜플, 수동 복제).
3. `backend/app/curated.py`의 `ERA_ORDER`(이름·순서만) — task#278로 `persons.py`의 `_ERA_ORDER`에서 이관.
4. `backend/app/curated.py`의 `CURATED`(slug 35개 → `{nameKo, era}`) — task#278로 `persons.py`의 `_ERA`/`_NAME_KO`가 병합됨.
5. `data/tours/*.json`의 `era` 필드 · `data/covenants/covenants.json`의 `era` 필드
6. (문자열 리터럴) `frontend/src/TimelineView.jsx` · `frontend/src/ExploreStage.jsx`의 `=== '신약'` 매직 스트링 — 비유·기적 토글 게이트(task#256).
7. `frontend/src/PersonHub.jsx:9` — `ERA_ORDER` 사본. **이 파일은 여전히 재선언한다**(`ERA_BANDS.map(b => b.name)`으로 대체 가능했으나 손대지 않음) — 단, 아래처럼 이제 게이트가 이 사본을 대조한다.

**task#284가 `backend/scripts/validate_era_bands_consistency.py`를 4→7축으로 확장해 위 1~7 전부를 본다**(신설 3축: ⑤ 투어 `era` · ⑥ `PersonHub.jsx`의 `ERA_ORDER` 사본 == `curated.py` · ⑦ `'신약'` 등 era 기능 게이트 리터럴 전수). ⑦의 판정 경계는 파일 허용목록이 아니라 **`===` 직전 식별자 사슬에 `era`/`Era` 토큰이 있는 문자열 비교**라는 클래스라서, 새 파일에 같은 게이트가 생겨도 자동으로 검사 범위에 든다(직접 실행해 확인: 실 파일 변이 5건이 도입 전에는 전부 무음 통과했고 지금은 전부 FAIL). 각 축은 0항목이면 실패하는 비공허 단언이고 `--selftest`로 7축(+공허 4종+순서/이름 2형태) 전부의 대조군을 확인한다. `scripts/check.sh`에 selftest까지 배선.

**만졌을 때 깨지는 것**은 이제 대부분 없다 — `'신약'` 리터럴을 포함해 시대 이름을 바꾸면 검증기가 즉시 FAIL해 배포를 막는다(이전엔 에러 없이 토글만 사라졌다).

검증기 자체의 취약성은 그대로 남는다: 여전히 **파이썬/JSX 소스를 정규식으로 스크래핑**한다. 포매팅만 바뀌어도 파싱이 깨지고, 그때 `assert`로 실패하므로 배포가 막힌다(fail-closed라 안전 방향). ADR `260819-205242`가 인정하고 남겨둔 결정이다.

### 5. 35 slug 하드코딩 테이블 두 벌 — 병합·게이트로 해소(task#278), 잔존 결함 클래스 1건

**심각도: 낮음(과거 중간) · 시급도: 낮음 → 대부분 해소**

과거: `backend/app/routes/persons.py:20-56`(`_ERA`)와 `:59-95`(`_NAME_KO`)가 35개 slug를 각각 나열한 병렬 딕셔너리였고, 가드 없이 조회하는 지점이 4개 라우트(`persons.py`·`places.py` 2곳·`timeline.py`)로 늘어 두 딕셔너리 중 하나만 갱신하면 `KeyError` → 500이 될 수 있었다.

해소(task#278): 두 딕셔너리가 `backend/app/curated.py`의 단일 `CURATED: dict[str, dict]` 리터럴(slug → `{nameKo, era}`)로 병합됐다. 소비처(`persons.py`·`journey.py`·`places.py`·`reliance.py`·`stats.py`·`timeline.py`·`tours.py`·`family.py`)가 전부 이 한 테이블을 import한다. `backend/scripts/validate_curated_persons.py`(신설)가 `ast.literal_eval`로 `CURATED`를 소스에서 직접 뽑아(테이블 사본 없음) ① `CURATED` 키 집합 == `data/person_events/*.json` 파일 집합(양방향) ② `data/god_reliance/*.json` slug ⊆ `CURATED` ③ `person_slugs/seal_slugs.json` slug ∩ `CURATED` == ∅ ④ 각 `era` ∈ `ERA_ORDER`를 게이트한다. `--selftest`로 4개 단언(첫 단언은 양방향) 전부 고의 드리프트 주입에 FAIL하는지 확인. `scripts/check.sh`에 selftest까지 배선.

**남은 결함 클래스 1건(회고 `260820-204317`이 실행 중 발견, 범위 밖으로 유보)**: `validate_curated_persons.py`는 `os.listdir`로 **파일명 집합만** 대조하고 `person_events/*.json`의 내용은 파싱하지 않는다. JSON이 손상돼도(문법 오류·필드 누락) 이 게이트는 통과한다. 게다가 이 리팩터로 `curated.person_events()`가 `tours.py`가 갖고 있던 `try/except (JSONDecodeError, OSError)` 방어를 승계하지 않았다(의도적 — 다른 5개 소비처의 관용성을 반대로 느슨하게 만들지 않으려고 남긴 이탈). 즉 손상된 `person_events` 파일은 게이트에서 안 잡히고 런타임에서 처리되지 않은 예외로 터질 수 있다. 후속 후보로 `validate_curated_persons.py`에 `person_events` JSON 파싱을 추가하는 안이 이미 지목돼 있다(`seal_slugs.json`은 이미 파싱하므로 형태가 있다).

### 6. 하드코딩 단일 ID에 매달린 기능 — `_JESUS_ID`

**심각도: 낮음 · 시급도: 낮음**

`backend/app/routes/family.py:92` `_JESUS_ID = "rec..."`. 업스트림 theographic이 이 레코드를 재키잉하면 `_lineage_ids()`(`family.py:96-119`)가 자기 자신만 담은 집합을 돌려주고 모든 노드가 조용히 `lineage: False`가 된다 — **에러도 로그도 없다.** `lru_cache(maxsize=1)`이라 잘못된 답이 프로세스 수명 내내 고정된다.

### 7. `apply_event_dedupe.py`가 `data/`를 되쓰는데 배포는 워킹트리를 하드리셋한다

**심각도: 중간 · 시급도: 낮음**

`backend/scripts/apply_event_dedupe.py:31-33`은 DB뿐 아니라 **저장소의 `data/` JSON 자체**를 다시 쓴다(`person_events`·`verse_events`·`authored_events`·`tours`·`book_events`·`names_ko`·`date_corrections`). 실행하면 미커밋 워킹트리 diff가 생긴다. 그런데 `.github/workflows/deploy.yml:15`는 `git reset --hard origin/main`을 배포 머신 워킹트리(`/Users/calmonion/Project/BibleMap` — 개발 머신과 동일)에서 실행한다. **커밋 전에 push가 발생하면 그 편집이 날아간다.** 과거 Known Bugs `VERSE_MAP` 죽은 키(현재 해소)가 바로 이 스크립트의 파생 효과였다 — 근본 원인(재쓰기와 하드리셋의 경합)은 여전히 남아 있고, 다음에 걸리는 것은 다른 하드코딩 테이블일 수 있다.

### 8. 오버레이 빈 폴백이 라우트마다 비대칭

**심각도: 중간 · 시급도: 낮음**

`backend/app/overlays.py:34-43` `_load()`는 파일 부재 시 `{}`, `json.JSONDecodeError` 시 `{}`+WARNING을 돌려준다. `OSError`는 잡지 않아 권한 오류·TOCTOU는 500으로 전파된다. 모든 로더가 `lru_cache(maxsize=1)`(총 **15개**: `overlays.py:46,52,58,64,70,77,83,89,95,101,107,113,121,128,134` — task#270이 `:128` `place_context()`를 추가해 14→15)이라 **기동 시점의 실패가 프로세스 수명 내내 캐시**되고 재시도가 없다.

하류 처리가 갈린다.

- **조용히 빈 200을 주는 쪽**: `backend/app/routes/events.py:119`(`/covenants`)·`:134`(`/messianic-prophecies`)·`:162`(`/topical-verses`)·`:177`(`/parables-miracles`), `backend/app/routes/tours.py:88-94`(주석에 "404 아님" 명시), `backend/app/routes/journey.py:84-88`, `backend/app/routes/persons.py:134`·`:177`, `backend/app/routes/reliance.py:99-101`, `backend/app/routes/family.py:47-48`·`:76-83`(**로그조차 없음**).
- **404를 던지는 쪽**: `backend/app/routes/books.py:89-91`·`:155-157`·`:164-166`, `backend/app/routes/words.py:14-15`·`:25-26`.
- **혼합형(신규, task#270)**: `GET /place/{place_id}`(`backend/app/routes/places.py`)는 `place_context`·`place_coords`·`_place_to_persons`·`_place_events` **네 출처가 전부 비어야** 404이고, 하나라도 있으면 나머지가 비어도 200 + 부분 빈 필드다. 세 번째 분류축이라 "이 라우트가 404를 던지는가"의 답이 라우트 단위가 아니라 **필드 조합 단위**로 갈린다.

즉 `data/names_ko/books.json`이나 `data/word_distribution.json`이 사라지면 책·단어 라우트는 **전 책 404**가 되고, 나머지는 전부 정상 200 + 빈 화면이 된다. 어느 쪽인지 알려줄 헬스/레디니스 엔드포인트가 없다.

---

### 9. 교차-장 구절 범위는 근거 절이 대표절 1개만 베이킹된다

**심각도: 낮음(과거 중간) · 시급도: 낮음 → 해소(task#282)**

과거: `generate_person_event_verses.py`는 저작 사건의 `context` 말미 구절 참조를 파싱해 `data/event_verses/events.json`에 절 본문을 채웠는데, **장 경계를 넘는 범위(`32:1–34:28`)나 장 단위 범위(`29–31`)는 시작 절 1개만 fetch**했다. 실측 12건(기존 6건 + task#264~266이 추가한 4건 등)이 이 상태였다 — UI는 "38:1–42:6"이라 적고 본문은 1절만 보여줬다.

해소(ADR `260821-125000`): 범위 전개를 getbible 장 fetch에서 **정본 절 사전(`data/bible/verses.json`) 키 열거**로 승급했다(`generate_person_event_verses.py`의 `expand_range_label`). rangeLabel이 종점을 무손실로 담고 있으므로 전개를 라벨 구동으로 바꿔, 네트워크 호출 없이 저장소 내 데이터만으로 전체 범위를 재베이킹한다(+895절, 12건 전량). `backend/scripts/validate_event_verses.py`(신설)가 **베이킹된 verseID 집합 == rangeLabel 범위 ∩ 정본 사전**(개수가 아니라 경계)을 게이트한다 — 같은 `expand_range_label`을 import해 생성기와 검증기가 파서 2벌이 되지 않는다. `--selftest` 5종(절 삭제·범위 밖 삽입·라벨 변조·파싱 불가·0블록) 전부 FAIL 확인. `scripts/check.sh`에 selftest까지 배선.

같은 책에 세미콜론·콤마로 두 구간을 적으면 두 번째 세그먼트를 드롭하는 문제는 [[사건의 근거]]가 단일 연속 범위 표기를 규칙으로 못 박아 우회한 채로 남아 있다(별건, 이번에 손대지 않음).

---

### 10. 여호수아 여정 사건의 `participants`가 주인공 1인뿐

**심각도: 낮음 · 시급도: 낮음**

`data/person_events/joshua.json`의 14건은 전부 `participants`가 여호수아(`recLuZtSmAO6erIsc`) 하나다. **`authored-joshua-caleb-hebron`("갈렙의 헤브론 분배 요구", 수 14:6–15)조차 갈렙이 등재돼 있지 않다** — 사건의 주역이 참여자 목록에 없다. `moses.json`은 아론·미리암을 부참여자로 넣는 반면(task#265) joshua 파일은 그러지 않는 비대칭이며, task#266의 구절 검토가 지적했으나 "joshua.json 전체의 기존 관례"이자 범위 밖이라 미수정.

영향: 인물 연표는 엄격 참여자 필터를 쓰므로(→ [[여정 (Journey)]]의 참여자 불변식) **갈렙의 연표에는 자기 사건이 뜨지 않는다**. 다만 갈렙은 현재 큐레이션 인물이 아니라 노출 경로가 없어 시급도는 낮다.

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

`.github/workflows/deploy.yml:13`에 `/Users/calmonion/Project/BibleMap` 절대경로가 박혀 있고 `:15`가 `git reset --hard origin/main`을 한다. 이 디렉터리는 개발 머신 워킹트리이자 `docker-compose.yml:20`의 `./data` 볼륨 마운트 원본이다. push 시점에 **추적 파일에 대한** 미커밋 편집이 있으면 소실된다(§데이터 정합성 7).

**정정(task#279 실측)**: `git reset --hard`는 추적 파일의 수정만 되돌리고 **미추적 파일은 지우지 않는다**(`git clean`이 아니다). task#279가 이 사실을 실측으로 확정했다 — `.forge/adr/`·`.forge/retro/`에 미추적 영구 문서가 있으면 하드리셋을 그대로 살아 넘어와 `deploy.sh`가 게이트로 부르는 `scripts/check.sh`에 노출된다. 그래서 `backend/scripts/validate_forge_docs_tracked.py`(신설)가 이 두 루트의 미추적 파일 0건을 게이트한다 — **당초 계획은 "CI 경로에서는 하드리셋 때문에 공허하게 통과한다"고 전제했으나 위 실측으로 반증됐고, 실제로는 이 미추적 상태가 배포를 중단시킨다**(`CHECK_STRICT=1`이라 스킵이 곧 실패). 이 게이트는 `.forge/adr`·`.forge/retro`만 보고 `data/`나 다른 미추적 파일은 보지 않는다 — §데이터 정합성 7의 위험은 그대로다.

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

### 3. ~~`journey.py`의 슬러그 역매핑이 유일하게 무캐시~~ (해소 — task#278)

**심각도: 낮음(과거 중간) · 시급도: 낮음 → 해소**

과거: `backend/app/routes/journey.py`의 `_build_id_to_slug()`·`_load_events()`에 `@lru_cache`가 없어 요청마다 `data/person_events/*.json` 35개 파일(276 KB)을 열고 파싱·재정렬했다. 같은 일을 하는 형제 모듈(`persons.py`·`places.py`·`tours.py`·`reliance.py`)은 전부 캐시하는데 `journey.py`만 예외였다.

해소(task#278): 두 무캐시 함수가 제거되고, `journey.py`는 `backend/app/curated.py`의 `id_to_slug()`(`@functools.lru_cache(maxsize=1)`)와 `person_events(slug)`(`@functools.lru_cache(maxsize=64)`)를 직접 import해 쓴다. 호출처(`journey.py`의 `GET /person/{id}/journey`, `backend/app/routes/tours.py`의 `GET /tour/{id}`, `stats.py`)가 전부 이 캐시된 경로를 공유한다.

현재 규모에선 체감이 없었다(리팩터 전 실측 `GET /person/{id}/journey` ≈ 10–16 ms) — 그래도 파일 I/O가 요청마다에서 프로세스당 1회로 줄었다.

### 4. `/words/{book}/verses`·`/search`가 매 요청 3만여 절 전수 substring 스캔

**심각도: 중간 · 시급도: 낮음(현재 규모에선 ≈10–20 ms) · 노출 라우트 1→2로 확대(task#267)**

`backend/app/verse_search.py:12` `search_verses()` — 사용자 입력 `term`으로 `overlays.bible_verses()` 전 항목(31,103절, 10.3 MB)을 파이썬 루프로 substring 검사한다. `words.py`가 자체 구현하던 동일 로직을 이 공용 헬퍼로 흡수했고(중복 제거, 좋은 방향), 대신 **`backend/app/routes/search.py`의 통합 검색이 새로 이 스캔을 탄다** — `frontend/src/SearchPanel.jsx`가 250ms 디바운스로 타자마다 질의를 보내므로, 서로 다른 2자 이상 접두어 각각이 새 전수 스캔 1회를 유발한다(동일 접두어 반복은 `lru_cache`가 흡수). `search.py`는 `MIN_VERSE_QUERY=2`로 1자 질의만 걸러 최악값(전체 매칭)을 막는다. 실측(구 `words.py` 단독 기준): `?w=사랑` 9–20 ms / 65 KB 응답 — `/search`가 추가돼도 현재 규모에선 체감 없음.

### 5. `lru_cache` 키가 사용자 입력인 라우트들 — 캐시 축출 표면

**심각도: 낮음 · 시급도: 낮음**

`backend/app/routes/books.py:61`(`maxsize=2048`, 키 `(book_id, n)`에서 `n` 무제한)·`books.py:105`(`maxsize=66`, 키 `book_id`)·`persons.py:221`·`persons.py:284`·`places.py:21`(각 `maxsize=256`)이 **검증되지 않은 경로 파라미터**를 캐시 키로 쓴다. 무의미한 키를 반복 호출하면 유효 엔트리를 밀어낼 수 있다. 무인증 공개 API라 접근은 자유롭다.

같은 부류가 task#267·270으로 2곳 늘었다: `backend/app/verse_search.py:12`의 `search_verses(term, book_id, match_en)`(`maxsize=256`)는 키가 **사용자 검색어 원문**이고, `backend/app/routes/places.py`의 신규 `_place_events(place_id)`(`maxsize=256`)는 `place_id`가 키다. 전자는 `/search`·`/words/{book}/verses` 양쪽에서 같은 캐시를 공유하므로 두 라우트의 서로 다른 질의가 같은 256슬롯을 다툰다.

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
| `/persons/curated` | `frontend/src/useStageNavigation.js:61` · `frontend/src/PersonHub.jsx:201` · `frontend/src/PersonIntro.jsx:69` |
| `/books-overview` | `frontend/src/BibleOverviewView.jsx:198` · `frontend/src/WordDistributionView.jsx:72` · `frontend/src/App.jsx:166` |
| `/event/{id}/verses` | `frontend/src/TimelineView.jsx:175` · `frontend/src/JourneyList.jsx:50` · `frontend/src/SidePanel.jsx:252` |
| `/parables-miracles` | `frontend/src/MapView.jsx:52` · `frontend/src/TimelineView.jsx:80` (둘 다 항상 마운트 — `App.jsx:853`이 MapView를 `display:none`으로 유지) |
| `/node/{id}/places` | `frontend/src/MapView.jsx:124` · `frontend/src/SidePanel.jsx:143` |
| `/person/{id}/relations` | `frontend/src/PersonIntro.jsx:82`(`.length`만 쓰려고 전량 수신) · `frontend/src/RelationsView.jsx:48` |

`useStageNavigation.js:61`과 `PersonHub.jsx:201`은 **지수 백오프 재시도 로직까지 각자 구현**했다. `PersonIntro.jsx:69`는 `useStageNavigation`이 이미 들고 있는 `curatedEraById`/`curatedSlugById`의 한 필드를 얻으려고 전체 목록을 다시 받는다.

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

`frontend/src/useStageNavigation.js`는 해시를 **마운트 시 1회만** 읽는다(`:41` `initialHashRef`, `:16` lazy initializer). 히스토리 리스너는 `:200`의 `popstate` 하나뿐이고 **`frontend/src/` 어디에도 `hashchange` 리스너가 없다.**

프래그먼트만 바뀌는 동일 문서 내비게이션(`<a href="#/books">`, 주소창 해시 직접 수정, 외부 `location.hash` 대입)은 `popstate`가 아니라 `hashchange`만 발생시킨다. → **URL은 바뀌지만 앱 상태는 안 바뀌고**, 다음 상태 변화 때 `replaceState`가 낡은 상태로 사용자 URL을 덮어쓴다. 딥링크가 무시된 것처럼 보인다.

복원은 `:127` `restoredRef`로 1회 게이팅되고 `:149`의 `[curatedIds]` dep이 `/persons/curated` 성공에 의존한다(`:61`의 3회 백오프 재시도로 완화되나 최종 실패 시 인물 딥링크가 미해결로 남는다).

**이 복원 effect 자체는 task#281로 결함 1건이 고쳐지고 게이트가 생겼다** — 무해시 첫 진입에서 이 effect가 `parseHash('')`의 `{stage:'hub'}`를 `applyParsedHash`에 넘겨 인트로 초기값을 덮던 결함(§코드마커현황 인접 참조는 없음, 이 문서 이전 판에는 없던 신규 발견·즉시 해소)이 해소됐다 — `:133`에서 `isNoTarget(initialHashRef.current)`이면 `applyParsedHash`를 부르지 않고 `setRestored(true)`만 태운다. `backend/scripts/validate_intro_entry_route.py`(신설)가 "무타깃 판정이 `urlState.isNoTarget` 정본 하나로만 일어난다"를 소스 불변식으로 게이트하지만, 이는 **이 절이 지적하는 `hashchange` 미청취 자체와는 다른 결함 클래스**이고 그 문제는 그대로 남아 있다.

`:122`·`:174`에 `eslint-disable-next-line react-hooks/exhaustive-deps` 2건(의도적, 주석으로 근거 명시).

**우회 사례(task#268·270, 근본 해결 아님)**: 이어보기·저장한 항목 카드(`PersonHub.jsx`의 `SavedRow`)는 `<a href="#...">`가 아니라 `useStageNavigation.js`의 신설 `handleGoToHash()`를 직접 호출해 해시 파싱→상태 적용을 상태 머신 안에서 태운다. `hashchange`에 의존하지 않고 앱이 스스로 제어하는 경로라 이 특정 상호작용은 안전하지만, **네이티브 앵커 기반 해시 이동이나 외부 `location.hash` 대입 경로는 여전히 무방비**다 — 이 문제의 일반 해법(전역 `hashchange` 리스너)이 아니라 회피다.

### 3. 응답 무효화 패턴이 3종으로 갈리고 27곳에 손으로 반복

**심각도: 낮음 · 시급도: 낮음(프론트 최대 반복 표면)**

- 수동 `let cancelled = false` — 10파일 19곳: `frontend/src/SidePanel.jsx:105,127,142,154,166` · `PersonIntro.jsx:58,68,81` · `App.jsx:85,165` · `BibleOverviewView.jsx:197,224` · `useStageNavigation.js:59,84` · `RelationsView.jsx:47` · `TopicalVersesView.jsx:14` · `StatsView.jsx:54` · `WordDistributionView.jsx:71` · `TourList.jsx:56` · `frontend/src/useExploreJourney.js:27`(신규, task#267~271)
- `AbortController` — 11파일: `App.jsx:121` · `ChapterReader.jsx:16,27` · `FamilyTree.jsx:207` · `mapRingController.js:112` · `MapView.jsx:120` · `PersonMiniCard.jsx:23` · `RelianceView.jsx:227` · `WordDistributionView.jsx:79` · `PlaceView.jsx:13`(신규) · `SearchPanel.jsx:37`(신규) · `CanonTimelineView.jsx:29`(신규) — 신규 3파일은 전부 이 패턴만 쓴다(좋은 방향)
- id 키잉 state 비교 — `PersonIntro.jsx:59-61` · `SidePanel.jsx`의 `forNodeId` 가드

`App.jsx`·`WordDistributionView.jsx`에 이어 `useExploreJourney.js`도 **한 파일 안에서 두 패턴(`cancelled` + `AbortController`)을 섞어 쓴다**. 공유 훅이 없다.

### 4. 지도 레이어 색상이 하드코딩 hex라 라이트 테마를 무시한다

**심각도: 낮음 · 시급도: 낮음**

`frontend/src/mapLayers.js`의 maplibre paint 값에 `#c9a84c`·`#8a6d1f`·`#f2ecdc`·`#1a1a2e`·`#58a4e8` 등이 약 20곳 직접 박혀 있다(`:192,193,216,232-241,261,262,282,284,299,330,332,352,366,368,382,404,406,425,452,454,472,489`). `frontend/src/theme.js:5`가 캔버스 컨텍스트에서 CSS 변수를 못 쓰는 이유를 설명하지만, 결과적으로 **ADR-0020의 라이트/다크 토글이 지도 레이어에는 반영되지 않는다.**

### 5. 연도 파싱·시대 분류 로직이 여러 벌 — task#283으로 신규 파서 1벌 추가

**심각도: 낮음 · 시급도: 낮음**

- 문자열 파서 3벌(동일 규칙, 주석으로 상호 참조): `frontend/src/dates.js:4` `parseYear` · `backend/app/routes/nodes.py:267-276` `_year`(라우트 핸들러 내부 중첩) · `backend/scripts/load_books.py:56-62` `_parse_year` · `backend/scripts/validate_event_chronology.py:66-71` `_year`
- 프론트 표시용 변형 2벌(task#262로 3벌→2벌 — `PersonMiniCard.jsx`가 자기 사본을 지우고 `dates.js`의 `parseYear`를 직접 씀): `frontend/src/TimelineView.jsx:31-33` `fmtYear`(숫자) · `frontend/src/PersonIntro.jsx:16-40` `formatLifespan`(정수)
- 시대 분류 2벌(유지, 위치만 이동): `frontend/src/eraBands.js:20-24` `eraOf`(task#271로 `TimelineView.jsx`에서 승급 — `TimelineView.jsx`는 이제 이걸 import) · `backend/app/routes/stats.py:36-41` `_era_of`
- **신규 1벌(task#283, 의도적 비재사용)**: `backend/scripts/validate_sortkey_startdate.py`가 위 3벌 문자열 파서를 재사용하지 않고 자체 `_INT_RE = re.compile(r"^-?\d+$")`로 "person_events의 startDate는 부호 있는 정수 문자열"을 단언한다. 재사용을 시도했으나 위 3벌이 전부 **import 시점에 `NEO4J_PASSWORD`를 요구하는 모듈**에 있고, `scripts/check.sh`의 파일 검증 루프는 `.env`를 읽기 **전에** 도는 순서라 재사용하면 이 검증기가 항상 FAIL했다(실측으로 기각, 계획 대비 이탈). 관대한 파싱 대신 월/일 정밀도가 들어오면 조용히 절삭하지 않고 fail-closed로 터지는 엄격 파서를 새로 선언했다 — 파서 총 4벌로 늘었지만 파서 3벌의 소거는 별건으로 유보.

### 6. 슬러그 해석 구현이 5벌 → 3벌로 축소(task#278), 집합이 이름에 드러남

**심각도: 낮음(과거 중간) · 시급도: 낮음 → 대부분 해소**

과거: `backend/app/overlays.py`(`curated_person_id`) · `backend/app/routes/persons.py`(`_build_list`) · `backend/app/routes/journey.py`(`_build_id_to_slug`, 무캐시) · `backend/app/routes/reliance.py`(`_slug_to_id`/`_id_to_slug`) · `backend/app/routes/family.py`(`_id_to_slug`, **함수 내부에서 `persons.py`를 import하는 순환회피 워크어라운드**, 인장 slug를 포함한 상위집합)로 5벌이 흩어져 있었고, 같은 패키지에 `_id_to_slug`가 두 개 있는데 키 집합이 달랐다.

해소(task#278): `backend/app/curated.py`로 3벌에 통합됐다 — `curated_index()`(35인 목록, `overlays.curated_person_id`는 그대로 재사용) · `id_to_slug()`/`slug_to_id()`(큐레이션 35) · `seal_id_to_slug()`(35 + `person_slugs/seal_slugs.json`의 비큐레이션 인장 보유 인물 = 50). **이름 자체가 집합 크기를 드러낸다**(35 vs 50)는 것이 이 통합의 핵심 — 이전에는 이름만 보고 어느 함수가 어느 집합인지 구별할 수 없었다. `journey.py`의 무캐시 사본은 제거됐고(§성능 3), `family.py`의 함수 내부 import 워크어라운드도 소거됐다. `reliance.py`의 `_slug_to_id`는 여전히 자기 이름으로 남아 있지만 지금은 `curated.slug_to_id()`를 `god_reliance/*.json` 파일 존재로 제한해 **파생**한다(별도 순회 없음) — 그래서 이름은 5벌처럼 보여도 정본은 하나다.

### 7. 그 외 중복 상수

- `PM_FILTERS` — `frontend/src/MapView.jsx:12`와 `frontend/src/TimelineView.jsx:10`에 동일 배열. `TimelineView.jsx:9` 주석이 "별 파일이라 상수는 각자 보관"으로 자백
- `PURPLE = TYPE_COLOR.Book` — `frontend/src/TourIntro.jsx:8` · `TourList.jsx:9` · `TourPlayback.jsx:8`
- `GROUND = 'var(--bg-0)'` — `frontend/src/TourList.jsx:10` · `PersonHub.jsx:25`
- 모바일 미디어쿼리 문자열 5곳(`frontend/src/VerseLayer.jsx:11` · `App.jsx:32` · `BibleOverviewView.jsx:16,18` · `PersonHub.jsx:33,35`) + `matchMedia` vs `window.innerWidth <= MOBILE_BREAKPOINT`(`MapView.jsx:146,215,257`) **두 가지 모바일 판정 기제 공존** — 후자는 리사이즈에 반응하지 않는다
- `prefers-reduced-motion` 쿼리 4곳: `frontend/src/MapView.jsx:262` · `tourSketches.jsx:46` · `RelianceView.jsx:81` · `IntroView.jsx:13`
- localStorage 키 `'biblemap-intro'`가 리터럴(`frontend/src/useStageNavigation.js:17`)과 상수(`frontend/src/IntroView.jsx:267` `INTRO_STORAGE_KEY`)로 이중 정의
- `build_range_label` — `backend/scripts/generate_approx_book_verses.py:105` 주석이 `generate_event_verses.py`와 동일 로직임을 명시(복붙 자백)

### 8. `content-box` 전제에서 `width:100%`+좌우 패딩 조합이 패딩을 시각적으로 무효화하는 결함 클래스 — 인트로 5곳만 봉인, 나머지 화면은 미조사

**심각도: 중간 · 시급도: 낮음(현재 인트로만 실증)**

이 프로젝트는 전역 `box-sizing: border-box` 리셋이 없어(ADR `260820-232144`가 도입하지 않기로 명시적으로 결정) 모든 요소가 기본 `content-box`다. `width: '100%'`(또는 명시 폭)에 좌우 패딩을 함께 주고 부모가 `alignItems:center`인 컨테이너는 **박스가 패딩의 2배만큼 뷰포트보다 넓어져 좌우 대칭으로 삐져나가고, 선언된 패딩이 시각적으로 정확히 0이 된다**(실측: 375px 폭에서 `left:-22, width:419`). 소스에는 패딩이 멀쩡히 적혀 있어 **코드 리뷰로 잡히지 않는 결함 클래스**다.

task#280이 이 결함을 인트로 화면(`frontend/src/IntroView.jsx`)에서 발견·수정했다 — 손 복사된 컨테이너 삼종(`width`+`maxWidth`+`padding`)을 `BeatFrame` 공용 프레임 하나로 승급해 `boxSizing:'border-box'`·거터 토큰·`wordBreak:'keep-all'`을 한 곳에서만 선언하게 했다. 적용 대상은 `BeatFrame`을 통과하는 **5곳뿐**(오프닝 Hero 포함). `backend/scripts/validate_intro_gutter.py`(신설)가 이 5곳에 대해 소스 불변식(border-box 명시·선언 지점 1곳·keep-all·프레임 통과)을 게이트하고, `scripts/uat_intro_gutter.py`가 `Range.getClientRects()`로 실측 잉크 여백을 잰다.

**전역 리셋은 의도적으로 도입하지 않았다** — 인라인 스타일 위주로 수십 개 화면이 `content-box` 전제에서 눈으로 조정돼 왔고, 자동 테스트가 희박해 전역 전환의 폭발 반경을 회수할 수단이 없다(ADR `260820-232144`). 즉 **인트로 밖의 `width:100%`+패딩 조합**(`frontend/src/` 전역에 `width: '100%'` 리터럴이 27곳 더 있다, IntroView 제외 집계)은 이번에 조사도 수정도 되지 않았다 — 같은 결함 클래스가 다른 화면에도 있는지는 미확인이다.

---

## Tech Debt

### 1. 대형 파일 — 스케치가 프론트 라인 수의 절반 가까이

`frontend/src/sketches/` 11파일 합계 **504,434 B / 10,532줄**(전체 `frontend/src` 21,875줄의 약 48% — task#264~266의 `exodusToConquest.jsx` +829줄 반영). 1,000줄 초과: `sketches/davidUnitedKingdom.jsx`(1,524) · `sketches/patriarchsCovenant.jsx`(1,259) · `sketches/gospelOfJesus.jsx`(1,207) · `sketches/ageOfJudges.jsx`(1,169) · `sketches/elijahAndElisha.jsx`(1,126). 다음 티어: `sketches/theEarlyChurch.jsx`(999) · `frontend/src/SidePanel.jsx`(943 / 50,233 B).

~~`frontend/src/App.jsx`(1,081줄 — 유일한 비스케치 1,000줄 초과)~~ → **해소(task#257~258)**: `App.jsx`가 9개 내비를 `StageNav.jsx`로, 탐험 스테이지를 `ExploreStage.jsx`로 분리해 **535줄 / 26,775 B**로 절반 넘게 줄었다. 이후(task#267~271)의 개인화·검색 기능 추가에도 다시 1,000줄대로 돌아가지 않았다.

스케치는 ADR-0029가 "투어당 1모듈"로 의도한 구조이고 lazy 청크로 격리됐으므로 부채 성격이 다르다. **이제 `SidePanel.jsx`(943줄)만 남은 비스케치 대형 파일이다.**

### 2. ~~"큐레이션 13인" 주석 드리프트~~ (해소 — task#278)

**심각도: 낮음 · 시급도: 낮음 → 해소**

과거: 실제 큐레이션 인물은 35명인데 `persons.py`·`journey.py`·`stats.py`의 여러 주석이 "13인"·"34인"이라 적어 놓았고, `family.py`만 "35"로 정확했다.

해소(task#278): `backend/app/curated.py` 이관과 함께 주석이 정리됐다 — `persons.py:1,23,174`·`journey.py:6,51`·`stats.py:106`이 모두 **"35인"**으로 일치한다(재확인: `grep -n '13인\|34인\|35인' backend/app/routes/*.py`가 "35인"만 반환). `data/person_events/*.json`(35파일) = `curated.py`의 `CURATED` 35키라는 대응도 여전히 유지된다.

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

### 8. 저장소 위생 — `.claude/settings.local.json.doctor-backup` 미추적 잔존

**심각도: 낮음 · 시급도: 낮음**

레포 루트에 `.claude/settings.local.json.doctor-backup`(fg-doctor류 도구가 남긴 백업 파일로 추정)이 미추적 상태로 남아 있다(`git status` 확인, `.gitignore`에 `.claude/` 관련 규칙 없음 — 무시 대상이 아니라 그냥 `git add`가 안 된 것). `backend/scripts/validate_forge_docs_tracked.py`(§배포/운영 5)는 `.forge/adr`·`.forge/retro`만 보므로 이 파일은 그 게이트에도 걸리지 않는다. 기능에 영향은 없지만 다음 커밋에서 실수로 같이 커밋되거나, 반대로 계속 미추적으로 남아 `git status`를 어지럽힐 수 있다.

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

- ~~**자동화 테스트 0건.**~~ → **부분 해소(task#261, 이후 확대)**: 프론트 순수 함수 5모듈에 vitest **88건**(`urlState`·`mapGeo`·`mapRingController`·`dates`·`useReadingProgress`의 `computeResume`), `npm test`로 실행되고 `scripts/check.sh`의 프론트 블록에 배선됐다. `useReadingProgress.test.js`는 task#276이 잡은 회귀(완독한 책의 이어읽기가 없는 장을 가리키던 결함)의 재발 방지 테스트다. **백엔드 pytest는 여전히 0건 — 의도된 결정**(ADR `260801-195023`: Neo4j 없이 테스트 가능한 라우트가 둘뿐이라 회수가 적다). React 렌더 테스트·커버리지 도구도 의도적 미도입.
- **ESLint·유닛 테스트는 PR에서 안 돈다.** `npm run lint`/`npm test`는 수동이거나 배포 게이트 시점. 게이트의 프론트 블록은 `frontend/node_modules` 부재 시 스킵이지만, 배포는 `CHECK_STRICT=1`로 호출하므로 **스킵이 곧 실패**다(task#259). PR 시점 CI가 없는 건 그대로(이 프로젝트는 PR을 쓰지 않는다).
- ~~**ADR-0029가 약속한 투어 정차지 ↔ 장면 스케치 커버리지 대조 스크립트가 없다.**~~ → **해소(task#259)**: `backend/scripts/validate_scene_coverage.py`가 양방향 대조(275↔275) + `tourSketches.jsx` 미병합 모듈까지 잡고 `scripts/check.sh`에 배선됐다.
- ~~**시대 결합 검증이 부분 커버**~~(§데이터 정합성 4) → **대부분 해소(task#284)**: `validate_era_bands_consistency.py`가 4→7축으로 확장돼 투어 JSON `era`·`PersonHub.jsx`의 `ERA_ORDER` 사본·`'신약'` 기능 게이트 리터럴 전수를 이제 검사한다. **소스 정규식 스크래핑**이라는 취약성 자체는 그대로 남아 있다(ADR `260819-205242`가 인정하고 남긴 결정, fail-closed라 안전 방향).
- ~~**`_ERA` ↔ `_NAME_KO` 35키 정합 검증 없음**~~(§데이터 정합성 5) → **해소(task#278)**: 두 테이블이 `curated.py`의 `CURATED` 하나로 병합됐고 `validate_curated_persons.py`가 양방향 정합을 게이트한다. **단 이 게이트는 파일명 집합만 보고 `person_events/*.json`의 내용을 파싱하지 않는다** — 손상된 JSON은 걸리지 않는다(§데이터 정합성 5의 잔존 항목, 후속 후보로 이미 지목됨).
- **`data/authored_persons/` 전용 validate 없음** — 다른 저작 데이터 12종은 검증기가 있다.
- ~~**하드코딩 ID 테이블 스테일 검출 게이트 없음**~~ → **VERSE_MAP 클래스는 해소(task#274)**, **`_ERA`/`_NAME_KO` 클래스도 해소(task#278)** — `validate_approx_book_verses.py`·`validate_curated_persons.py`가 각각 배포 게이트에 배선됐다. ADR `260820-003946`이 예고한 대로 같은 `ast.literal_eval` 소스 추출 형태가 그대로 재사용됐다.
- **Person 생몰 ↔ Event 연대 계 격차 측정 게이트 없음**(§데이터 정합성 1) — 이 축은 여전히 미검증이다. **다른 두 연대 축은 이번에 새로 게이트됨**: `sortKey`↔`startDate` 전역 역전(`validate_sortkey_startdate.py`, task#283)과 근거 절 범위↔라벨 정합(`validate_event_verses.py`, task#282) — 둘 다 §데이터 정합성 1·9 참조.
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

`TODO`/`FIXME`/`HACK`/`XXX`/`나중에`/`임시` 마커는 **`backend/`·`frontend/src/`·`scripts/` 전체에 0건**이다. 이 코드베이스는 `task#NNN`·`ADR-NNNN` 참조 주석을 부채 추적 관용구로 쓴다(예: `frontend/src/MapView.jsx:15` "선재 버그, task#251", `backend/app/routes/stats.py:22-23` "공유 설정이 없어 수동 복제"). 위 항목 다수가 그런 자백 주석에서 출발했다. `eslint-disable`은 4건뿐이며 전부 한 줄 범위 + 근거 주석 동반(`frontend/src/useStageNavigation.js:150,203` · `VerseLayer.jsx:21` · `personSymbols.jsx:488`). `backend/app/`에 `print()`·root logger 직호출 0건으로 `CLAUDE.md`의 로깅 규약을 지키고 있다.
