---
last_mapped_commit: 50d8961b1d6148fed2952fc59cb4bed3e634b592
mapped: 2026-10-24
---

# CONCERNS

현재 코드베이스의 기술 부채·확정 결함·보안 노출·성능 병목·취약 지점·데이터 정합성 위험 목록. 최초 전면 매핑은 HEAD `43f987c` 기준이었고, 이후 task#259~316 커밋들이 실어 나른 부분 갱신이 누적됐다. **2026-10-24 증분(HEAD `50d8961`): Tech Debt 10을 실측으로 고치고(PNG 251장 약 200 MB·size-pack 206.77 MiB), Tech Debt 16(그림 파이프라인 모듈 상태·검사 함수 등록·요단 구역 원근 어긋남·로그 누적)을 추가했다. 그 외 절은 미재검증이다.** 앞선 2026-10-10 증분(HEAD `924f501`): 장면 승인 도구 서버·장면 상태 기계·AGE 호환성 판정(막힘)·작업트리 미커밋 편집을 Tech Debt 12~15로 추가했다(그 외 절은 미재검증).** 이전 갱신은 도장 `4ad1d83` 이후 커밋 ∪ 미커밋 작업트리를 증분 반영했다(HEAD `fbd547d`)** — 변경 항목의 압도적 다수(`scripts/canon/` 아래 180건)가 신설된 **로컬 이미지 생성·판정 파이프라인**이라, 이번에 늘어난 절은 대부분 그 서브시스템의 위험이다.

이번 갱신에서 다음을 **실제로 실행해** 검증했다.

- `bash scripts/check.sh` 전량 실행 → **✓41 ✗1**. 파일 기반 데이터 검증 22종 + 정합 대조군(selftest) 10종 + 인물 정본 구별성(`check_cast_axes`) + 마스크 delay 범위(`check_mask_ranges` 본검사·대조군) + 저작 파이프라인 가드(`validate_canon_pipeline` 본검사·대조군) + ESLint + vitest(5파일 **88건**) + 라이브 Neo4j 연대 검증이 전부 PASS이고, **`validate_forge_docs_tracked`만 FAIL** — 미추적 영구 문서 8건(`.forge/adr/` 1 · `.forge/retro/` 7). 즉 **지금 이 작업트리 상태로는 배포가 차단된다**(§배포/운영 5).
- `python3 -m backend.scripts.validate_canon_pipeline` 단독 실행 → `scripts/canon/params.py`가 선언한 31개 이름(모델 ID 3종 포함)이 나머지 45개 파일에 재선언 0건 · `scripts/` 미추적 0건
- `scripts/canon/` 실측: **49 MB / 추적 파일 177건**(그중 PNG 62장 = 49.2 MB) · `.py` 46개(`gen_*` 21 · `judge_*` 8) · `notes/` 판단문서 20 + meta JSON 37
- 레포 **밖** 런타임 실측: `~/.local/biblemap-imggen/` 957 MB(venv + 레포 밖 구 사본 `.py` 5개 + `prompts/`) · `~/.cache/huggingface/` 47 GB · 산출물 `.forge/reports/canon-pilot/` 679 MB(gitignored)
- `frontend/dist/assets/` 실측(**2026-08-26 빌드 — 현 소스보다 옛것**) · `git count-objects -vH`(size-pack **60.86 MiB**) · `git ls-tree -r -l HEAD` 최대 블롭 · `git status`·`git ls-files --others`로 미추적 잔존 확인
- 새 검증기·게이트 4종 원문 확인: `backend/scripts/validate_canon_pipeline.py`·`validate_api_cache_headers.py`·`validate_scene_sketch_detail.py`, 그리고 동적 구조로 재작성된 `validate_scene_coverage.py`

직전 판(HEAD `4ad1d83`)까지의 이력은 이렇게 요약된다 — 최초 전면 매핑 이후 task#253~258이 ESLint 7건·번들 639 KB·`App.jsx` 1,081줄을 닫고, task#259가 배포 게이트의 무음 스킵 2경로를 `CHECK_STRICT`로 막고, task#260이 nginx gzip을, task#261이 vitest를 들였다. task#262~277이 Known Bugs 2건(VERSE_MAP 죽은 키 · `PersonMiniCard` 연도 포맷터)과 `Book.startYear/endYear` 파생값 봉인·ERA_BANDS 모듈 승급·절 전수 스캔 공용화를 처리했고, task#278·280~284가 큐레이션 35 slug 두 벌 병합(+`journey.py` 무캐시 해소)·근거 절 범위 재베이킹·`sortKey`↔`startDate` 역전·era 결합점 4→7축을 닫았다. 아래 각 절이 그 해소/잔존을 항목별로 구분한다.

**이번 갱신에서 새로 닫힌 것은 셋이다.** ① `public, max-age=3600` 6곳이 전부 `max-age=300`으로 내려가고 `validate_api_cache_headers`가 상한을 게이트한다(§Tech Debt 4). ② `enrich_place_coords.py`의 "좌표 없을 때만 SET" 가드가 **상시 거짓**이라 손으로 저작한 좌표 교정이 한 번도 반영된 적 없던 결함이 저작값 우선으로 뒤집혔다(§데이터 정합성 11). ③ `.claude/settings.local.json.doctor-backup` 미추적 잔존이 사라졌다(§Tech Debt 8). 부수적으로 투어 스케치 단일 대청크가 투어별 동적 청크 9개로 갈렸고(§Tech Debt 3), 장면 스케치 저작 규약(B1~B12)·인물 정본 구별성·마스크 delay 범위가 새 게이트 3종으로 강제된다.

**새로 생긴 위험은 저작 파이프라인 쪽에 몰려 있다** — 레포 안 소스 / 레포 밖 런타임 분리가 만든 재현성 구멍(§Tech Debt 9), 커밋된 PNG 49 MB가 팩의 대부분을 차지하는 레포 무게(§Tech Debt 10), 실험 스크립트 46개가 정본과 한 디렉터리에 쌓인 부채(§Tech Debt 11), tracked 소스가 gitignored 자산을 참조하는 채색층 파일럿(§Fragile Areas 9), 그리고 투어별 동적 로드가 새로 만든 "키 오배치" 무음 결함 클래스(§Fragile Areas 10).

---

## 직전 매핑 지적 사항 사후 검증

### 해소됨 (RESOLVED — 재확인 완료)

| 항목 | 검증 방법 | 결과 |
|---|---|---|
| **ESLint 7 errors + 1 warning** | `scripts/check.sh`의 `npx --no-install eslint src` | **0건.** `frontend/src/sketches/SceneLabel.jsx` 분리·`frontend/src/useTourPlayback.js` 분리·`set-state-in-effect` 제거로 규칙 완화 없이 해소(`415374f`, task#253) |
| **메인 번들 ≈639KB** | `frontend/dist/assets/` 실측(2026-08-26 빌드) | **`index-CEJ_CwE4.js` 273,366 B(gzip 69,662).** 투어 스케치는 한 청크(391 KB)에서 **투어별 9청크(29~78 KB)**로 재분할됐다(task#287, §Tech Debt 3) — `frontend/src/tourSketches.jsx`의 `TOUR_MODULES`가 투어 id별 `import()`를 들고 있고, `tourSketches-*.js`는 6,781 B 로더만 남았다 |
| **Person 생몰 Ussher 드리프트 검증 위반 5건** | 라이브 `backend/scripts/validate_event_chronology.py`(Neo4j 접속) | **위반 0.** `data/date_corrections/events.json`·`persons.json` 교정 + ADR `260724-111632`로 ADR-0014 Person 조항 부분 개정. **단, "계(scale) 불일치" 자체는 미해소 — 아래 데이터 정합성 §1 참조** |
| **모바일 지도 세계축소(아프리카) 프레이밍 버그** | 코드 확인 | `frontend/src/MapView.jsx:17-33` `clampPadding`(축별 패딩 합을 컨테이너의 60%로 클램프) + `:88` `map.on('load')` 내 `map.resize()`를 `setMapLoaded` **이전에** 호출해 프레이밍 effect보다 선행 |
| **신규 데이터 디렉터리 4종 미커밋** | `git status` | 전부 커밋됨(`87846fb`). `data/covenants/`·`data/messianic_prophecies/`·`data/topical_verses/`·`data/jesus_parables_miracles/` 모두 추적 중 |
| **ERA_BANDS 3중 중복에 정합 게이트 없음** | 스크립트 실행 | `backend/scripts/validate_era_bands_consistency.py` 신설 — TimelineView↔stats.py 경계·이름·순서 + persons.py `_ERA_ORDER` 순서 + covenants.json `era` 유효성 검사, `scripts/check.sh` 배선. **단 커버리지 부분적 — 아래 데이터 정합성 §4** |
| **비유·기적 지도↔연표 커버리지 무경고 누락 17건** | 스크립트 실행 + 코드 확인 | `backend/scripts/validate_pm_map_coverage.py`가 누락 17건을 `EXPECTED_UNMAPPABLE` 정본으로 고정(회귀·미해석 `placeId` 탐지). UI도 `frontend/src/MapView.jsx:336-342`에서 "위치 없는 비유 N건은 연표에서" 안내 |
| **데이터 검증 스크립트 CI 미연결** | `deploy.sh` 게이트 단계 | `scripts/check.sh`가 배포 전 하드 게이트로 배선. 실패 시 `exit 1`로 배포 중단. 무음 스킵 경로 2개는 `CHECK_STRICT=1`로 **해소**(task#259, 배포/운영 §1) |
| **투어 정차지 장면 커버리지 자동 게이트 부재** | 스크립트 실행 | `backend/scripts/validate_scene_coverage.py` 신설 — 정차지↔스케치 키 양방향 대조(task#264~266의 출애굽~정복 21건 보강 이후 **296건**↔296건) + `tourSketches.jsx` 미병합 모듈 탐지, `scripts/check.sh` 배선(task#259) |
| **언약 리본 `marginLeft:auto` 클리핑** | 직전 세션 수정 확인 | `frontend/src/TimelineView.jsx` 잔존 없음 |
| **`VERSE_MAP`의 죽은 eventId 4개 — 재실행 즉시 `sys.exit(1)`** | `ast.literal_eval`로 `VERSE_MAP` 추출 후 `data/book_events/books.json`과 교차 대조 | **죽은 키 0 · 미커버 0.** task#273(`2caf509`)이 `authored-*` 신원으로 재매핑했고, task#274(`53c94a1`)가 `backend/scripts/validate_approx_book_verses.py`로 이 조건을 배포 게이트에 **재현**(생성기는 실행하지 않음, ADR `260820-003946`) — `scripts/check.sh`의 파일 검증 루프(현재 **22종**)에 배선. 같은 결함 클래스가 `persons.py`의 `_ERA`/`_NAME_KO` 35 slug에 아직 남아 있었으나 그쪽은 task#278로 해소됐다(§데이터 정합성 5) |
| **`PersonMiniCard`의 연도 포맷터가 정본 헬퍼와 갈라짐** | 코드 확인 | task#262(`4353f34`)가 `PersonMiniCard.jsx`의 로컬 `fmtYear`를 지우고 `frontend/src/dates.js`의 `parseYear`를 직접 import — 제로패딩 분기가 사라져 갈라질 수 없다 |
| **`load_books.py` 재실행이 교정 연대를 무시하고 업스트림 값을 쓴다** | `inject_date_corrections.py` diff 확인 + 라이브 실행 없이 정적 대조 | task#273(ADR `260819-233305`)이 `inject_date_corrections.py`에 `recompute_book_years()`를 추가 — 교정 주입 직후 `CONTAINS_BOOK` 사건의 교정 후 `startDate`로 `Book.startYear/endYear`를 재집계해 SET한다. `deploy.sh`가 이미 이 스크립트를 게이트 앞에서 부르므로 배포 경로에서 자동으로 닫힌다(§데이터 정합성 2) |

### 잔존 (아래 각 절에서 상세)

`deploy.sh`의 `load_*`·`enrich_place_coords` 미배선(의도된 결정 — ADR `260801-195022`) · 캐시 무효화가 재시작 의존 · CORS `*` · `words.py`·`search.py` 공용 절 전수 스캔(`verse_search.py`, task#267로 두 라우트가 공유) · 오버레이 빈 폴백 비대칭 · `api.js` 캐시·디듀프 부재 · SPA `hashchange` 미청취 · 대형 컴포넌트(`SidePanel.jsx`, `App.jsx`는 task#257~258 분해로 이탈) · 대용량 오버레이 상주 · 의존성 caret 미고정 · 백엔드 테스트 0건(의도된 결정 — ADR `260801-195023`) · `content-box`+패딩 결함 클래스가 인트로 5곳만 봉인되고 나머지 화면은 미조사(ADR `260820-232144`) · `validate_curated_persons`가 `person_events` JSON 내용은 파싱하지 않음.

**이번 갱신에서 잔존 목록에서 빠진 것**: `Cache-Control` 3600/300 혼재(→ 전량 300 + 상한 게이트, §Tech Debt 4) · `.claude/settings.local.json.doctor-backup` 미추적(→ 파일 자체가 사라짐, §Tech Debt 8) · "앱 코드 분할이 `tourSketches` 하나뿐"(→ 투어별 9청크 + `introMontage` + `CastSheet`, §Tech Debt 3).

**이번 갱신에서 잔존 목록에 새로 든 것**: 저작 파이프라인의 재현성 3축 미결(§Tech Debt 9) · 커밋된 PNG 49 MB(§Tech Debt 10) · 실험 스크립트 46개 혼재(§Tech Debt 11) · `frontend/public/scene-color/` gitignored 자산 참조(§Fragile Areas 9) · 동적 투어 청크의 키 오배치 클래스(§Fragile Areas 10) · `god_reliance` 근거 절이 진술을 뒷받침하는지 재는 기계 게이트 부재(§데이터 정합성 12).

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

### 11. 저작 장소 좌표가 DB에 한 번도 반영되지 않던 결함 — 해소(task#285), 배포 미배선은 잔존

**심각도: 높음(과거) · 시급도: 낮음 → 해소, 단 반영 경로는 수동**

과거: `backend/scripts/enrich_place_coords.py`가 `rec*` ID(업스트림 theographic Place)에 대해 `WHERE pl.latitude IS NULL`로 "기존 값 보존"을 했다. 그런데 `load_theographic.py` 임포트가 이미 모든 Place에 좌표를 채우므로 **그 가드는 상시 거짓**이었다 — `data/place_coords/places.json`에 손으로 적은 좌표 교정이 단 한 번도 DB에 반영된 적이 없고, 재실행해도 에러·경고 없이 '스킵' 카운트만 올랐다. 실측: `rec*` 11건 전부 저작값과 DB가 불일치했고, 시내산은 저작(28.539)과 DB(29.5)가 위도 0.96°(≈107 km) 어긋난 채 서빙됐다.

해소(task#285): 정본 방향이 뒤집혔다 — 이 파일은 업스트림 좌표를 고치려고 손으로 저작하는 교정 파일이므로 **충돌 시 저작값이 이긴다**. 쿼리가 `WITH pl, (pl.latitude <> $lat OR pl.longitude <> $lng) AS differs` + 무조건 `SET`으로 바뀌었고, 카운터가 `created/updated/unchanged/missing` 4종으로 갈렸다. `missing`(places.json에 있는데 DB에 없는 id)을 따로 세는 것이 핵심 — 이전 `skipped` 한 통에 "이미 같음"과 "대상 없음"이 섞여 재실행이 조용히 무의미해졌다.

**잔존**: 이 스크립트는 여전히 `deploy.sh`에 배선돼 있지 않다(§Tech Debt 5의 14종 목록에 포함). 즉 **고친 로직이 좌표를 실제로 옮기려면 사람이 수동으로 돌려야 한다**. 그리고 `data/place_coords/places.json` ↔ DB 좌표의 일치를 재는 게이트는 없다 — `scripts/check.sh`의 라이브 검증은 `validate_event_chronology`(연대)뿐이라 좌표 드리프트는 검출 대상이 아니다.

### 12. `god_reliance` 근거 절 오지정 — 교정됐으나 재발 방지 게이트 없음

**심각도: 중간 · 시급도: 낮음**

`data/god_reliance/*.json` **26파일**에서 `verse` 값을 담은 줄 83개가 81개로 교체됐다(항목 총수는 195 → 194 — 항목 1건이 함께 정리돼 수가 어긋난다). 예: `abraham.json`의 "순종하여 하란을 떠남"이 창 12:1 → 창 12:4, "바로의 집에 재앙 내려 사래를 건지심"이 창 12:10 → 창 12:17, `saul.json`의 "나하스의 위협에 하나님의 영이 임하심"이 삼상 11:1 → 11:6 / 그 `outcome`이 11:1 → 11:11. 패턴이 일관된다 — **`trigger`의 절을 `outcome`에 그대로 복사해 둔 것**이 지배적 원인이고, 결과가 실제로 기록된 뒤쪽 절을 가리키지 않았다. 즉 한 항목의 두 필드가 같은 절을 말하고 있었다.

`backend/scripts/validate_god_reliance.py`는 **이 상태에서 통과하고 있었다**(직접 실행해 재확인 — 지금도 PASS). 그 검증기가 보는 축은 7개다(mode 통제어휘 5종 · `trigger.verse`·`outcome.verse`가 정본 절 사전에서 **해석되는지** · `obeyed`가 `mode=="부르심"`일 때만 불리언 · `approxYear` 정수 · label 결손 · `kind` 통제어휘 · 구 스키마 잔존). 오지정된 절도 **실재하는 절이므로 ②를 통과한다** — 즉 이 게이트는 "절이 있는가"를 보고 "그 절이 이 진술을 뒷받침하는가"는 보지 않는다. 후자는 기계 신호가 아니라 본문 판독이라 판정 범위 밖이고, 같은 오지정이 새로 저작되면 게이트는 초록이다. 검출 수단은 사람(또는 `scripture-reviewer` 역할)의 절 대조뿐이고, 이번 교정이 그렇게 잡혔다.

같은 결함 클래스는 근거 절을 손으로 적는 다른 저작 데이터(`person_events`의 `context` 말미 참조 등)에도 열려 있다 — `validate_event_verses.py`(task#282)가 게이트하는 것은 **라벨 범위 ↔ 베이킹된 절 집합의 경계 일치**이지 절이 진술을 뒷받침하는지가 아니다.

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

**현재 상태(2026-09-02 실측): 이 게이트가 빨강이다.** `.forge/adr/` 1건 + `.forge/retro/` 7건이 미추적이라 `bash scripts/check.sh`가 `✗ validate_forge_docs_tracked`로 실패한다(다른 41항목은 전부 PASS). 배포 경로는 `CHECK_STRICT=1`이므로 **이 상태로 push하면 배포가 중단된다** — 실패 메시지가 파일 목록을 지목하니 무음은 아니고, 해소는 `git add` 하나다. 아울러 `.forge/dropped/`는 `.gitignore`에도 이 게이트의 스캔 루트에도 없어(현재 미추적 3디렉터리) 어느 쪽에도 걸리지 않는다 — 배포를 막지는 않지만 `git status`를 어지럽힌다.

### 6. `deploy.sh` 단계 라벨 어긋남 (코스메틱) (**해소 — task#259**)

과거 `[1/3]`·`[2/3]`·`[3/4]`·`[4/4]`로 분모가 섞였고 검증 단계엔 번호가 없었다. 재배치와 함께 `[1/7]`~`[7/7]`로 통일했다(대기 → 주입 → `npm install` → 게이트 → 빌드 → 이미지 → 기동).

### 7. 프론트 `:8080`은 `frontend/dist` 정적 마운트 (HMR 아님)

`docker-compose.yml:30`. 소스만 고치고 `npm run build`를 안 하면 이전 빌드가 계속 서빙된다. `frontend/dist/`는 `.gitignore:9`로 미추적이라 배포 머신에서 매번 재빌드된다.

### 8. `scripts/` 미추적이 배포 차단 사유가 됐다 — 게이트가 스스로를 지킨다

**심각도: 낮음 · 시급도: 낮음(의도된 강도)**

`backend/scripts/validate_canon_pipeline.py`(신설, task#316)의 둘째 축은 `git ls-files --others --exclude-standard -- scripts`가 비어 있음을 단언한다. 위생 규칙이 아니라 **게이트 자기보호**다 — `scripts/check.sh`가 부르는 `scripts/check_cast_axes.py`·`scripts/check_mask_ranges.py`가 미추적이면 새 클론·CI에서 게이트 자신이 깨진다. `validate_forge_docs_tracked.py`와 같은 스캔 형태·같은 git 미가용 skip 계약(`EXIT_NO_GIT=3`)이고, `check.sh`가 `git rev-parse --is-inside-work-tree`로 분기해 부른다.

부작용: **`scripts/` 아래에 임시 스크립트를 하나 놓아 두면 배포가 막힌다.** 저작·실험 스크립트가 계속 늘어나는 디렉터리라(§Tech Debt 11) 이 결합은 앞으로도 걸릴 자리다. 약화하려면 스캔 루트를 `check.sh`가 실제로 부르는 파일 집합으로 좁히는 안이 있으나, 그러면 "새 게이트를 추가하고 커밋을 잊는" 원래 결함이 다시 열린다.

첫째 축(정본 재선언 금지)이 **소스만 읽어** 판정하는 것은 GPU도 생성 venv도 없는 `check.sh` 실행 환경 때문이다. 그래서 이 게이트의 초록은 "파이프라인이 돈다"가 아니라 "이 불변식이 아는 재선언이 없다"뿐이다 — 검증기 도크스트링이 그 한계를 스스로 적어 두었다.

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

`frontend/src/MapView.jsx:2-3`이 `maplibre-gl`과 그 CSS를 정적 import하고, `frontend/src/ExploreStage.jsx:7`이 `MapView`를 정적 import하며 `App.jsx:10`이 `ExploreStage`를 정적 import한다(task#257~258 분해 이후 경로가 한 단 늘었을 뿐 지연 로드는 아니다). 결과적으로 인트로·인물 허브·통계·성경 리더 등 지도를 전혀 안 쓰는 진입에도 1,027,608 B + 69,808 B CSS가 함께 내려간다. `frontend/vite.config.js:14-19`의 `manualChunks`는 `maplibre`를 별 청크로 **분리만** 할 뿐 지연 로드하지 않는다. `chunkSizeWarningLimit` 미설정이라 vite 500 kB 경고가 매 빌드 발생하고 무시되고 있다(현재 유일한 초과가 이 청크다).

`frontend/dist/assets/` 실측(2026-08-26 빌드 — **현 소스보다 옛것이니 절대값은 참고치**): `maplibre-DgANBuI6.js` **1,027,608 B**(단일 최대) · `index-CEJ_CwE4.js` 273,366 · `vendor-q2EswsIf.js` 198,991 · `maplibre-B2k4QVOw.css` 69,808. 투어 스케치는 task#287로 투어별 청크 9개(29,245~78,136 B)로 갈렸고 `tourSketches-BGO6HHXr.js`는 6,781 B의 로더만 남았다(§Tech Debt 3) — 즉 **지도가 이제 두 번째로 큰 청크의 3.8배**로, 프론트 전송량의 지배 요인이 명확히 maplibre 하나다. js+css 합계 2,061,363 B.

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

`data/` 총 19 MB / 117 파일. 최대 파일: `data/bible/verses.json` 10,284,836 B · `data/event_verses/events.json` **2,382,141**(task#282 재베이킹으로 +197 KB) · `data/word_verse_index/index.json` 1,725,004 · `data/person_relations/relations.json` 1,216,657 · `data/person_context/people.json` 936,603 · `data/verse_persons/index.json` 857,251 · `data/word_distribution.json` 283,953. 전부 `lru_cache(maxsize=1)`로 한 번 접근되면 프로세스 종료까지 파이썬 객체로 상주한다(실제 RSS는 원본 바이트보다 훨씬 크다). uvicorn 단일 워커라 현재는 1벌이지만 워커를 늘리면 워커당 곱해진다.

### 9. `apiGet`에 캐시·디듀프가 없어 같은 엔드포인트를 여러 컴포넌트가 각자 fetch

**심각도: 낮음 · 시급도: 낮음**

`frontend/src/api.js` 전체가 17줄짜리 `fetch` 래퍼다 — 인플라이트 맵도, 메모도, SWR류도 없다. 서버 `Cache-Control`(이제 전량 `max-age=300`, §Tech Debt 4)과 `?v=__BUILD_ID__` 캐시버스터가 유일한 완화책이라, 콜드 로드의 동시 요청은 실제로 중복 전송된다. 상한이 3600→300으로 내려간 만큼 이 중복의 재발 주기는 오히려 짧아졌다.

| 엔드포인트 | fetch 하는 곳 |
|---|---|
| `/persons/curated` | `frontend/src/useStageNavigation.js:61` · `frontend/src/PersonHub.jsx:232` · `frontend/src/PersonIntro.jsx:69` |
| `/books-overview` | `frontend/src/BibleOverviewView.jsx:208` · `frontend/src/WordDistributionView.jsx:72` · `frontend/src/App.jsx:64` |
| `/event/{id}/verses` | `frontend/src/TimelineView.jsx:158` · `frontend/src/JourneyList.jsx:50` · `frontend/src/SidePanel.jsx:252` |
| `/parables-miracles` | `frontend/src/MapView.jsx:56` · `frontend/src/TimelineView.jsx:63` (둘 다 항상 마운트 — `frontend/src/ExploreStage.jsx:135`이 MapView를 `display:none`으로 유지) |
| `/node/{id}/places` | `frontend/src/MapView.jsx:128` · `frontend/src/SidePanel.jsx:143` |
| `/person/{id}/relations` | `frontend/src/PersonIntro.jsx:82`(`.length`만 쓰려고 전량 수신) · `frontend/src/RelationsView.jsx:48` |

`useStageNavigation.js:61`과 `PersonHub.jsx:232`는 **지수 백오프 재시도 로직까지 각자 구현**했다. `PersonIntro.jsx:69`는 `useStageNavigation`이 이미 들고 있는 `curatedEraById`/`curatedSlugById`의 한 필드를 얻으려고 전체 목록을 다시 받는다.

### 10. `MapView`의 `/parables-miracles` fetch에 취소 가드가 없다

`frontend/src/MapView.jsx:56-58` — `.catch`는 있으나 `cancelled`/`AbortController` 가드가 없어 언마운트 후 `setPmItems`가 호출될 수 있다. 같은 파일의 다른 fetch(`:124-128`)는 `AbortController`를 쓴다.

### 11. `search.py` 전역 노드 스캔 (잔존)

`backend/app/routes/search.py:15-31` — 라벨 제약 없는 전역 매치 후 `LIMIT {SEARCH_LIMIT}`. `q`는 파라미터 바인딩이라 인젝션은 아니다.

---

## Security Considerations

- **CORS `allow_origins=["*"]`** — `backend/app/main.py:46-50`. `allow_credentials=False` + `allow_methods=["GET"]` + 무인증 공개 읽기 API라 즉각 위험은 낮지만 완전 개방이다. **심각도: 낮음**
- **Cypher 인젝션 표면 — 라우트 계층은 깨끗하다.** `backend/app/routes/*.py`의 f-string 삽입은 전부 모듈 상수뿐이다(`search.py:15-31`의 `SEARCH_LIMIT`, `stats.py:67-73`의 `TOP_PERSONS_LIMIT`, `family.py:111-116`·`:159-167`의 `MAX_GENERATIONS`, `nodes.py:176-183`의 `NODE_NEIGHBOR_LIMIT`, `main.py:34-35`의 고정 라벨 목록). 사용자 입력은 전부 `$` 파라미터 바인딩.
- **데이터 파일이 Cypher 속성명이 되는 지점** — `backend/scripts/inject_date_corrections.py:66`·`:85`가 `data/date_corrections/persons.json`의 `field` 값을 `p.{field}`로 보간한다. Cypher가 속성명을 파라미터화할 수 없어 구조적으로 불가피하지만 **허용목록 검사가 없다**(현재 값은 `birthYear`·`deathYear` 2종뿐). 저장소 데이터라 외부 입력은 아니다. **심각도: 낮음**
- **시크릿 취급 (양호)** — `.env`는 `.gitignore:13`, 커밋 이력 없음, `.env.example`은 플레이스홀더만. `frontend/.env.production`은 `VITE_API_URL=/api`뿐. `docker-compose.yml:10`·`:18`이 `${NEO4J_PASSWORD:?...}` fail-fast. LLM 저작 스크립트는 `ANTHROPIC_API_KEY`를 환경변수로만 읽는다(`backend/scripts/generate_book_context.py:71-73`·`generate_book_events.py:88-90`). 하드코딩 시크릿 0건.
- **Neo4j 바인딩 (양호)** — `docker-compose.yml:4-6`이 `127.0.0.1`로만 노출. API `:8000`도 호스트 미노출(`docker-compose.yml`의 api 서비스에 ports 없음).
- **레이트리밋·요청 크기 제한 없음** — `nginx/nginx.conf`에 `limit_req`/`limit_conn` 없음. §Performance 4·5의 비용 큰 엔드포인트가 그대로 열려 있다. **심각도: 낮음(공개 읽기 전용) · 시급도: 낮음**
- **저작 파이프라인의 시크릿 표면 (양호) · 대신 머신 경로가 커밋된다** — `scripts/canon/` 46개 스크립트에 API 키·토큰 패턴 **0건**(로컬 GPU 추론만 하고 외부 서비스 호출이 없다). 대신 `/Users/<사용자>` 형태의 절대경로가 **추적 파일 26건**에 박혀 있다 — 20건은 도크스트링의 실행 예시(레포 밖 venv 인터프리터 경로), 1건은 `scripts/canon/params.py`의 `IMAGE_ENCODER`(허깅페이스 로컬 캐시 스냅샷 절대경로, 도크스트링이 아니라 **실제 코드 값**), 나머지는 `notes/*.json` meta의 산출물 경로. 자격증명은 아니지만 사용자 홈 디렉터리 구조가 공개 커밋에 남고 다른 머신에서는 성립하지 않는다(§Tech Debt 9). **심각도: 낮음**
- **배포 로그로의 잠재 유출** — §배포/운영 4 참조.

---

## Fragile Areas

### 1. `MapView`에 리사이즈 리스너가 전혀 없다

**심각도: 중간 · 시급도: 중간**

`frontend/src/MapView.jsx`의 `resize()` 호출은 두 곳뿐이다 — `:88`(`map.on('load')` 내부 1회)과 `:282-284`(`isVisible`/`mapLoaded` 전환 시). **`window` resize 리스너도 `ResizeObserver`도 없다.** 같은 프로젝트의 `frontend/src/FamilyTree.jsx:292`·`WordDistributionView.jsx:65`·`RelianceView.jsx:156`은 `ResizeObserver`를 쓴다 — MapView만 예외.

`frontend/src/ExploreStage.jsx:135`(주석이 "MapView는 언마운트하지 않고 display:none(항상 마운트 규약 유지)"으로 명시)이 MapView를 계속 마운트해 두므로, **브라우저 리사이즈·기기 회전·모바일 URL바 접힘** 시 캔버스가 낡은 크기로 남는다. 게다가 프레이밍 패딩을 만드는 `isMobile`/`sheet` 값은 `window.innerWidth`/`innerHeight` 스냅샷(`MapView.jsx:146-147`·`:215-216`·`:257`)이라 회전 후에도 재계산되지 않는다.

카메라 effect가 5개(`:104`·`:200`·`:227`·`:240`·`:275`)로 흩어져 `mapLoaded` + 겹치는 deps를 공유한다. `:207` 주석이 인물 모드/투어 모드 프레이밍이 서로 카메라를 다툴 수 있어 수동 배제했음을 명시한다. `:259-261`은 `easeTo`에 `offset: undefined`를 넘기면 `Point.convert`가 던져 **React 루트가 통째로 언마운트되던** 크래시를 조건부 스프레드로 우회했음을 기록한다.

### 2. SPA 해시 라우팅이 `hashchange`를 듣지 않는다

**심각도: 중간 · 시급도: 낮음**

`frontend/src/useStageNavigation.js`는 해시를 **마운트 시 1회만** 읽는다(`:41` `initialHashRef`, `:16-18` lazy initializer). 히스토리 리스너는 `:211`의 `popstate` 하나뿐이고 **`frontend/src/` 어디에도 `hashchange` 리스너가 없다.**

프래그먼트만 바뀌는 동일 문서 내비게이션(`<a href="#/books">`, 주소창 해시 직접 수정, 외부 `location.hash` 대입)은 `popstate`가 아니라 `hashchange`만 발생시킨다. → **URL은 바뀌지만 앱 상태는 안 바뀌고**, 다음 상태 변화 때 `replaceState`가 낡은 상태로 사용자 URL을 덮어쓴다. 딥링크가 무시된 것처럼 보인다.

복원은 `:128` `restoredRef`로 1회 게이팅되고 `:153`의 `[curatedIds]` dep이 `/persons/curated` 성공에 의존한다(`:61`의 3회 백오프 재시도로 완화되나 최종 실패 시 인물 딥링크가 미해결로 남는다).

**이 복원 effect 자체는 task#281로 결함 1건이 고쳐지고 게이트가 생겼다** — 무해시 첫 진입에서 이 effect가 `parseHash('')`의 `{stage:'hub'}`를 `applyParsedHash`에 넘겨 인트로 초기값을 덮던 결함(§코드마커현황 인접 참조는 없음, 이 문서 이전 판에는 없던 신규 발견·즉시 해소)이 해소됐다 — `:134`에서 `isNoTarget(initialHashRef.current)`이면 `applyParsedHash`를 부르지 않고 `setRestored(true)`만 태운다. `backend/scripts/validate_intro_entry_route.py`(신설)가 "무타깃 판정이 `urlState.isNoTarget` 정본 하나로만 일어난다"를 소스 불변식으로 게이트하지만, 이는 **이 절이 지적하는 `hashchange` 미청취 자체와는 다른 결함 클래스**이고 그 문제는 그대로 남아 있다.

`:151`·`:214`에 `eslint-disable-next-line react-hooks/exhaustive-deps` 2건(의도적, 주석으로 근거 명시).

**우회 사례(task#268·270, 근본 해결 아님)**: 이어보기·저장한 항목 카드(`PersonHub.jsx`의 `SavedRow`)는 `<a href="#...">`가 아니라 `useStageNavigation.js:118`의 `handleGoToHash()`를 직접 호출해 해시 파싱→상태 적용을 상태 머신 안에서 태운다. `hashchange`에 의존하지 않고 앱이 스스로 제어하는 경로라 이 특정 상호작용은 안전하지만, **네이티브 앵커 기반 해시 이동이나 외부 `location.hash` 대입 경로는 여전히 무방비**다 — 이 문제의 일반 해법(전역 `hashchange` 리스너)이 아니라 회피다.

### 3. 응답 무효화 패턴이 3종으로 갈리고 30곳에 손으로 반복

**심각도: 낮음 · 시급도: 낮음(프론트 최대 반복 표면)**

- 수동 `let cancelled = false` — **11파일 18곳**: `frontend/src/SidePanel.jsx:105,127,142,154,166` · `PersonIntro.jsx:58,68,81` · `BibleOverviewView.jsx:207,234` · `useStageNavigation.js:84` · `App.jsx:63` · `RelationsView.jsx:47` · `TopicalVersesView.jsx:14` · `StatsView.jsx:54` · `WordDistributionView.jsx:71` · `TourList.jsx:56` · `useExploreJourney.js:27`
- `AbortController` — **11파일 12곳**: `ChapterReader.jsx:19,30` · `FamilyTree.jsx:207` · `mapRingController.js:107` · `MapView.jsx:124` · `PersonMiniCard.jsx:17` · `RelianceView.jsx:227` · `WordDistributionView.jsx:79` · `PlaceView.jsx:13` · `SearchPanel.jsx:37` · `CanonTimelineView.jsx:29` · `useExploreJourney.js:39`
- id 키잉 state 비교 — `PersonIntro.jsx:59-61` · `SidePanel.jsx`의 `forNodeId` 가드

`App.jsx`는 이번 갱신에서 이 표면에서 거의 빠졌다(`cancelled` 1곳만 남고 `AbortController`는 0 — 여정·재생 fetch가 `useExploreJourney.js`·`ExploreStage.jsx`로 이관된 결과). 반면 `WordDistributionView.jsx`와 `useExploreJourney.js`는 여전히 **한 파일 안에서 두 패턴을 섞어 쓴다**. 공유 훅은 여전히 없다.

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
- 모바일 미디어쿼리 문자열 5곳(`frontend/src/VerseLayer.jsx:11` · `App.jsx:34` · `BibleOverviewView.jsx:16,18` · `PersonHub.jsx:33,35`) + `matchMedia` vs `window.innerWidth <= MOBILE_BREAKPOINT`(`MapView.jsx:146,215,257`) **두 가지 모바일 판정 기제 공존** — 후자는 리사이즈에 반응하지 않는다
- `prefers-reduced-motion` 쿼리 4곳: `frontend/src/MapView.jsx:262` · `tourSketches.jsx:46` · `RelianceView.jsx:81` · `IntroView.jsx:13`
- localStorage 키 `'biblemap-intro'`가 리터럴(`frontend/src/useStageNavigation.js:17`)과 상수(`frontend/src/IntroView.jsx:267` `INTRO_STORAGE_KEY`)로 이중 정의
- `build_range_label` — `backend/scripts/generate_approx_book_verses.py:105` 주석이 `generate_event_verses.py`와 동일 로직임을 명시(복붙 자백)

### 8. `content-box` 전제에서 `width:100%`+좌우 패딩 조합이 패딩을 시각적으로 무효화하는 결함 클래스 — 인트로 5곳만 봉인, 나머지 화면은 미조사

**심각도: 중간 · 시급도: 낮음(현재 인트로만 실증)**

이 프로젝트는 전역 `box-sizing: border-box` 리셋이 없어(ADR `260820-232144`가 도입하지 않기로 명시적으로 결정) 모든 요소가 기본 `content-box`다. `width: '100%'`(또는 명시 폭)에 좌우 패딩을 함께 주고 부모가 `alignItems:center`인 컨테이너는 **박스가 패딩의 2배만큼 뷰포트보다 넓어져 좌우 대칭으로 삐져나가고, 선언된 패딩이 시각적으로 정확히 0이 된다**(실측: 375px 폭에서 `left:-22, width:419`). 소스에는 패딩이 멀쩡히 적혀 있어 **코드 리뷰로 잡히지 않는 결함 클래스**다.

task#280이 이 결함을 인트로 화면(`frontend/src/IntroView.jsx`)에서 발견·수정했다 — 손 복사된 컨테이너 삼종(`width`+`maxWidth`+`padding`)을 `BeatFrame` 공용 프레임 하나로 승급해 `boxSizing:'border-box'`·거터 토큰·`wordBreak:'keep-all'`을 한 곳에서만 선언하게 했다. 적용 대상은 `BeatFrame`을 통과하는 **5곳뿐**(오프닝 Hero 포함). `backend/scripts/validate_intro_gutter.py`(신설)가 이 5곳에 대해 소스 불변식(border-box 명시·선언 지점 1곳·keep-all·프레임 통과)을 게이트하고, `scripts/uat_intro_gutter.py`가 `Range.getClientRects()`로 실측 잉크 여백을 잰다.

**전역 리셋은 의도적으로 도입하지 않았다** — 인라인 스타일 위주로 수십 개 화면이 `content-box` 전제에서 눈으로 조정돼 왔고, 자동 테스트가 희박해 전역 전환의 폭발 반경을 회수할 수단이 없다(ADR `260820-232144`). 즉 **인트로 밖의 `width:100%`+패딩 조합**(`frontend/src/` 전역에 `width: '100%'` 리터럴이 27곳 더 있다, IntroView 제외 집계)은 이번에 조사도 수정도 되지 않았다 — 같은 결함 클래스가 다른 화면에도 있는지는 미확인이다.

### 9. 추적 소스가 gitignored 자산을 참조한다 — 채색층 파일럿

**심각도: 낮음 · 시급도: 낮음(현재 1장면 파일럿)**

`frontend/src/sketches/ageOfJudges.jsx:1530`이 정차지 `authored-samuel-circuit-judge`에 `color: '/scene-color/samuel-circuit.webp'`를 달아 놓았다. 그런데 그 자산이 사는 `frontend/public/scene-color/`는 이번 갱신에서 **`.gitignore:10`에 추가됐다** — 즉 **추적된 소스가 추적되지 않는 파일을 참조한다.** 개발 머신에는 파일이 있고(52 KB, `.webp` 1장) `git reset --hard`가 미추적 파일을 지우지 않으므로 배포 머신에서도 지금은 살아남지만, **새 클론·다른 머신에서는 없다.**

폴백은 있다 — `frontend/src/tourSketches.jsx:65`의 `colorOk` state가 `<image onError>`로 404를 잡아 다음 렌더에서 `<image>` 자체를 걷어낸다. 이 처리를 굳이 넣은 이유가 주석에 실측으로 적혀 있다: 404면 Chromium이 "아무것도 안 그리는" 게 아니라 **깨진-이미지 아이콘을 뷰박스 전체에 늘려 마스크를 통과시켜 얼룩으로 번진다**. 따라서 자산이 없을 때의 결과는 크래시가 아니라 **잉크 선화만 그려지는 조용한 강등**이다.

문제는 그 조용함이다 — **파일럿이 레포에서 재현되지 않고, 재현 안 됨을 알려주는 신호도 없다.** `validate_scene_coverage.py`는 정차지↔스케치 키 대응만 보고 `color` 경로의 존재는 검사하지 않으며, `validate_scene_sketch_detail.py`의 B1~B12에도 자산 존재 축이 없다. 296장면 중 1건이라 지금은 표면이 좁지만, 채색층을 확대하면 그 수만큼 늘어난다.

### 10. 투어별 동적 청크가 새로 만든 "키 오배치" 무음 결함 클래스

**심각도: 중간 · 시급도: 낮음(게이트 있음)**

`frontend/src/tourSketches.jsx`가 9모듈을 한 레지스트리로 정적 병합하던 구조에서 **투어 id → `() => import('./sketches/<모듈>')`** 매핑(`TOUR_MODULES`)으로 바뀌었다(task#287). 부작용으로 **판정 기준이 달라졌다** — 예전엔 스케치 키가 어느 모듈에 있든 렌더됐지만, 지금은 키가 **그 정차지가 속한 투어의 모듈 밖**에 있으면 아무것도 렌더되지 않는다. 병합 구조에는 존재하지 않던 결함 클래스이고, 증상은 무음(에러도 로그도 없이 삽화 자리가 빈다)이다.

`backend/scripts/validate_scene_coverage.py`가 이 클래스를 A~G 7종으로 갈라 게이트한다(A 미저작 · B 고아 키 · C 허용목록 잔존 · D 모듈 미연결 · E 투어 미연결 · **F 오배치** · G 인트로 미연결). 대조군이 특히 **A(미저작)와 D/E/F(미연결)를 다른 메시지로 구분하는지**를 단언하는데, 이유가 실무적이다 — 두 결함은 증상이 같고 처방이 정반대다(그림을 그려야 하나, 배선을 고쳐야 하나).

잔존 위험 둘. ① 게이트는 **소스 정규식 스크래핑**이다(`_TOUR_MODULE` 정규식이 `'id': () => import('./sketches/Name')` 형태를 그대로 요구) — 포매팅이나 표기가 바뀌면 파싱이 깨지고, 그때 assert로 실패하므로 fail-closed 방향이지만 취약하다. ② 인트로 오프닝 몽타주는 5개 투어에 흩어진 5씬을 쓰므로 `frontend/src/sketches/introMontage.jsx`가 그것만 **재수출**한다(인트로가 투어 청크 5개를 끌어오지 않도록) — 즉 같은 씬이 두 레지스트리에 등재되는 이중 등록이 구조적으로 필요하고, 그 정합은 G축 하나에 걸려 있다.

### 11. `#/cast` 개발 전용 라우트가 프로덕션 번들에 실린다

**심각도: 낮음 · 시급도: 낮음**

`frontend/src/urlState.js`의 `parseHash`/`encodeHash`에 `#/cast` 분기가 추가되고(`stage: 'cast'`), `frontend/src/App.jsx`가 `lazy(() => import('./CastSheet'))`로 렌더한다. 사용자 화면 어디에도 이 라우트로의 링크가 없어(ADR `260823-190821` 4항) 주소를 직접 입력해야만 들어가지만, **빌드 산출물에는 그대로 포함된다**(`CastSheet-*.js` 7,268 B + `cast/*.jsx`의 인물 정본 청크). 저작 에이전트가 자기 그림을 보기 위한 화면이므로 데이터 노출은 없고 부작용도 없지만, 프로덕션에서 접근 가능한 개발 표면이라는 점은 남는다. `frontend/eslint.config.js:21-28`이 이 디렉터리에만 `react-refresh/only-export-components`를 끄는 예외도 함께 생겼다(정본 파일이 컴포넌트와 `aliases`/`AXES` 선언을 같은 파일에 둬야 검증기가 하나만 읽으면 되기 때문).

---

## Tech Debt

### 1. 대형 파일 — 스케치가 프론트 라인 수의 절반을 넘었다

`frontend/src/sketches/` **15파일 합계 606,404 B / 12,241줄**(전체 `frontend/src` 23,975줄의 약 **51%** — 밀도 상향 task#286·303·305~316이 반영돼 절반을 넘어섰다). 1,000줄 초과 6개: `sketches/davidUnitedKingdom.jsx`(1,929) · `sketches/exodusToConquest.jsx`(1,630) · `sketches/ageOfJudges.jsx`(1,534) · `sketches/gospelOfJesus.jsx`(1,510) · `sketches/patriarchsCovenant.jsx`(1,259) · `sketches/elijahAndElisha.jsx`(1,126). 다음 티어: `sketches/theEarlyChurch.jsx`(968) · `frontend/src/SidePanel.jsx`(943 / 50,233 B). 신규 소형 모듈 4개는 반대 방향이다 — `sketches/introMontage.jsx`(211) · `sketches/cast/props/altar.jsx`(155) · `sketches/cast/david.jsx`(85) · `sketches/cast/goliath.jsx`(63).

~~`frontend/src/App.jsx`(1,081줄 — 유일한 비스케치 1,000줄 초과)~~ → **해소(task#257~258)**: `App.jsx`가 9개 내비를 `StageNav.jsx`로, 탐험 스테이지를 `ExploreStage.jsx`로 분리해 절반 넘게 줄었고, 이후의 개인화·검색·`#/cast` 추가에도 **553줄**에 머물렀다.

스케치는 ADR-0029가 "투어당 1모듈"로 의도한 구조이고 이제 **번들 경계까지 투어별로 갈렸으므로**(task#287, §Tech Debt 3) 부채 성격이 다르다 — 한 파일이 커져도 그 투어를 보는 사람만 내려받는다. **`SidePanel.jsx`(943줄)가 여전히 유일한 비스케치 대형 파일이다.**

### 2. ~~"큐레이션 13인" 주석 드리프트~~ (해소 — task#278)

**심각도: 낮음 · 시급도: 낮음 → 해소**

과거: 실제 큐레이션 인물은 35명인데 `persons.py`·`journey.py`·`stats.py`의 여러 주석이 "13인"·"34인"이라 적어 놓았고, `family.py`만 "35"로 정확했다.

해소(task#278): `backend/app/curated.py` 이관과 함께 주석이 정리됐다 — `persons.py:1,23,174`·`journey.py:6,51`·`stats.py:106`이 모두 **"35인"**으로 일치한다(재확인: `grep -n '13인\|34인\|35인' backend/app/routes/*.py`가 "35인"만 반환). `data/person_events/*.json`(35파일) = `curated.py`의 `CURATED` 35키라는 대응도 여전히 유지된다.

### 3. `chunkSizeWarningLimit` 미설정 — 앱 코드 분할은 투어별로 확대(task#287)

`frontend/vite.config.js:11-22`의 `manualChunks`는 여전히 `node_modules`만 `maplibre`/`vendor`로 가른다. 500 kB 경고도 그대로다(유일한 초과가 `maplibre` 1.03 MB, §Performance 2).

**앱 코드 분할은 확대됐다** — 이전에 "`tourSketches` 하나만 lazy"였던 것이 지금은 `frontend/src/tourSketches.jsx`의 `TOUR_MODULES`(투어 id → 동적 `import()`)로 **투어별 청크 9개**가 되고, 여기에 `sketches/introMontage.jsx`(인트로 몽타주 전용 재수출)와 `CastSheet`(`App.jsx`의 `lazy`)가 더해졌다. 동기는 성능이었다 — 병합 레지스트리가 425 KB 단일 청크를 만들었고 밀도 상향 후엔 maplibre(1.03 MB)보다 커질 궤적이었다. ADR-0029가 정한 "투어당 1모듈"이라는 **코드 경계를 번들 경계로 승격**한 형태다. 실측 청크: `exileAndReturn` 29,245 B ~ `davidUnitedKingdom` 78,136 B, 로더 `tourSketches-*.js`는 6,781 B.

대가는 §Fragile Areas 10 — 키가 그 투어의 모듈 밖에 있으면 무음으로 안 뜨는 결함 클래스가 새로 생겼다.

### 4. ~~`Cache-Control` 정책이 라우트마다 제각각~~ (해소 — task#285)

**심각도: 중간(과거) · 시급도: 중간 → 해소, 주석 드리프트만 잔존**

과거: `max-age=300`(대다수) / `public, max-age=3600`(6곳) / `no-store`(1곳)가 섞여 있었다. 3차 버그 헌트가 확정한 실제 결함은 혼재 자체가 아니라 **긴 `max-age`가 ETag 없이 붙어 이 프로젝트의 표준 데이터수정 경로(`data/` 편집 + `docker compose restart api`)로 고친 내용이 재방문 브라우저에 최대 1시간 반영되지 않던 것**이다. 프론트 캐시버스터(`api.js`의 `?v=__BUILD_ID__`)는 **빌드타임 리터럴**이라 백엔드만 재시작하는 그 경로를 원리적으로 못 덮는다.

해소: 6곳이 전부 `max-age=300`으로 내려갔다(`backend/app/routes/books.py` 3곳 · `reliance.py` 2곳 · `verses.py` 1곳). 현재 분포는 `max-age=300` **27곳** · `no-store` 1곳뿐이다(직접 집계). `backend/scripts/validate_api_cache_headers.py`(신설)가 `backend/app/routes/*.py`의 `"Cache-Control"` 헤더 리터럴을 스캔해 **`max-age <= 300`이라는 경계**를 게이트한다 — "지금 6곳"을 세지 않는 것이 요점이고(알려진 위반 목록을 박으면 새 위반은 통과한다), `no-store`는 수명 미선언이라 통과시킨다. 주석에 나온 예시가 오탐되지 않게 `_COMMENT`로 먼저 주석을 공백 치환한다. `--selftest`는 인메모리 사본에 고의 위반을 주입해 같은 스캔 함수가 FAIL하는지 본다. 게이트를 푸는 조건도 도크스트링에 못 박혀 있다 — 조건부 GET(ETag/Last-Modified)을 먼저 붙이고 상한을 올려라.

**잔존(코스메틱)**: 주석 2곳이 이제 반대 방향으로 어긋난다 — `frontend/src/api.js:5-7`은 "옛 응답(max-age=3600 캐시)"·"1시간 캐시 이점"이라 적고 `frontend/vite.config.js:7`은 "API 응답 캐시(max-age=3600)를 배포 시 무력화"라 적는데, 실제로 3600은 코드베이스에 더 없다.

### 5. `deploy.sh`가 재적용하지 않는 DB 쓰기 스크립트 14종

`deploy.sh`가 도는 건 `inject_ko_names.py` 하나, `README.md:20-22`가 문서화한 건 3종. **나머지는 문서에도 배포에도 없다**: `backend/scripts/load_books.py` · `load_person_events.py` · `load_verse_events.py` · `load_authored_events.py` · `load_authored_persons.py` · `load_authored_genealogy.py` · `load_authored_mothers.py` · `inject_book_context.py` · `inject_person_context.py` · `inject_person_traits.py` · `inject_place_context.py` · `apply_event_dedupe.py` · `enrich_place_coords.py` · `generate_book_events.py`. 로더 재적재 후 이들이 전부 드리프트한다.

**이 목록 중 `enrich_place_coords.py`는 이번 갱신으로 비용이 올랐다** — task#285가 이 스크립트의 좌표 우선순위를 뒤집어 "저작값이 정본"으로 만들었으므로(§데이터 정합성 11), 배포에 배선되지 않은 지금은 **고친 로직이 좌표를 실제로 옮기려면 사람이 수동으로 돌려야 한다.** 미배선 자체는 의도된 결정이지만(ADR `260801-195022` — 자동화하면 `load_books.py`의 `build_book_year_range()`가 매 배포마다 교정을 덮는다), 그 결정의 근거는 `load_*` 로더에 있고 `enrich_place_coords.py`는 로더가 아니라 교정 주입 계열이다. `inject_ko_names.py`·`inject_date_corrections.py`가 게이트 앞에 배선된 것과 대칭이 맞지 않는 자리다.

### 6. 캐시 무효화 수단이 사실상 `docker compose restart api` 하나

`data/`는 볼륨 마운트(`docker-compose.yml:20`)라 파일 수정에 이미지 재빌드가 불필요하지만, `overlays.py`의 **15개** `lru_cache(maxsize=1)`(§데이터 정합성 8과 같은 집계) + 라우트 레벨 캐시(`events.py`의 `_load_approx_book_index`·`_compute_events`·`_book_name_map`, `stats.py:124`의 `_compute_stats` 등)가 프로세스 로컬이라 **반영은 재시작뿐**이다. TTL도 무효화 API도 없다. 이 "편집 + `restart api`"가 표준 경로라는 사실이 §Tech Debt 4의 긴 `max-age`를 실제 결함으로 만든 원인이었다.

### 7. 배치되지 않은 행 단위 쓰기

`backend/scripts/inject_ko_names.py:31-32`와 `backend/scripts/inject_date_corrections.py:31-56,62-88`이 `UNWIND` 배치 대신 파이썬 루프에서 행마다 쿼리를 낸다(events 교정 256건 × 2쿼리). `deploy.sh`의 주입 단계가 느린 이유.

### 8. ~~저장소 위생 — `.claude/settings.local.json.doctor-backup` 미추적 잔존~~ (해소)

**심각도: 낮음 · 시급도: 낮음 → 해소**

그 백업 파일은 사라졌고(`ls .claude/`로 확인), 레포 루트의 미추적 파일 중 `.forge/` 밖 항목은 **0건**이다(`git status --porcelain`로 확인). 다만 같은 부류의 위생 위험은 위치를 옮겨 남아 있다 — 미추적 영구 forge 문서 8건(§배포/운영 5, **현재 배포 차단 중**)과 어느 게이트에도 안 걸리는 `.forge/dropped/` 3디렉터리다. `scripts/` 아래는 이제 `validate_canon_pipeline`의 둘째 축이 미추적 0건을 강제한다(§배포/운영 8).

### 9. 저작 파이프라인의 재현성 — 레포 안 소스 / 레포 밖 런타임, 그리고 스스로 선언한 미결 3축

**심각도: 중간 · 시급도: 낮음(앱 배포 경로와 무관)**

`scripts/canon/`(46개 `.py`)는 **소스만** 저장소에 있고 런타임은 전부 레포 밖이다 — 실행 인터프리터는 `~/.local/biblemap-imggen/.venv314/bin/python`(957 MB), 모델 가중치는 `~/.cache/huggingface/`(**47 GB**), 산출물은 `.forge/reports/canon-pilot/`(679 MB, gitignored). 이 분리는 의도된 결정이고(ADR `260825-065028` — 앱과 다른 런타임, `backend/requirements.txt`와 별개이며 앱 배포는 `scripts/canon/requirements.txt`를 설치하지 않는다) `scripts/canon/params.py`의 `OUT_ROOT`가 산출물을 gitignored 경로로 못 박아 54 MB급 이미지가 커밋을 따라오지 않게 한다.

**재현은 닫히지 않았고, 그 사실이 문서에 명시돼 있다** — `scripts/canon/requirements.txt` 머리 주석이 미결 3축을 스스로 열거한다(ADR `260822-220823`의 "위임된 정본은 미결을 미결로 표시해야 한다"를 따른 형태).

1. **모델 리비전 미고정** — `params.py`의 `CN_MODEL`·`SDXL_BASE`·`IP_ADAPTER_REPO`는 허브 **저장소 이름**일 뿐 커밋/리비전이 아니다. 업스트림이 가중치를 갱신하면 같은 코드가 다른 그림을 낸다. 유일한 예외 `IMAGE_ENCODER`는 스냅샷 해시가 박힌 대신 **이 머신의 로컬 캐시 절대경로**라 다른 머신에서는 성립하지 않는다 — 즉 "고정했다"로 읽으면 안 되는 자리다.
2. **MPS 결정성 미보장** — Apple Silicon MPS 백엔드는 시드를 고정해도 비트 단위 재현을 보장하지 않는다. 스크립트들의 sha256 전수-상이 단정은 "서로 다르다"만 보고 "다시 돌리면 같다"는 보지 않는다.
3. **재현 미실측** — 위 둘을 고정한 채 같은 그림이 다시 나오는지 **재본 적이 없다**.

여기에 실측으로 확인된 축이 하나 더 붙는다. **레포 밖 런타임 디렉터리에 구 사본이 남아 있다** — `~/.local/biblemap-imggen/`에 `gen.py`·`cn_sweep.py`·`combo.py`·`controlnet_test.py`·`scenes.py` + `prompts/`(2026-08-22자)가 그대로 있고, 이들은 `scripts/canon/`으로 옮겨진 소스의 이전 세대다. 버전 관리 밖이고 정본과 갈라져 있으므로, 그쪽을 실행하면 게이트가 아는 정본과 다른 파라미터로 돈다.

배포 게이트가 이 서브시스템에 관해 단언할 수 있는 것은 **소스뿐**이다 — `validate_canon_pipeline`은 GPU도 생성 venv도 없는 `check.sh` 환경에서 돌아야 하므로 AST·텍스트 스캔만 한다(§배포/운영 8). 파이프라인이 실제로 도는지, 같은 그림을 다시 내는지는 어떤 게이트도 보지 않는다.

### 10. 커밋된 이미지 자산 — 이제 저장소 무게의 대부분 (2026-10-24 실측: PNG 251장 약 200 MB · size-pack 206.77 MiB, 아래 수치는 10-10 당시)

**심각도: 중간 · 시급도: 낮음**

`scripts/canon/` 추적 파일 177건 중 **PNG 62장이 49.2 MB**다(디렉터리 총 49 MB). `git count-objects -vH`의 size-pack이 **60.86 MiB**이므로, 클론 무게의 압도적 다수가 이 이미지들이다. 최대 블롭 순위에서도 `data/bible/verses.json`(10.3 MB) 다음이 전부 canon PNG다 — `setup/ref-scale-armor.png` 2.45 MB · `reference/candidate-322d/goliath-profile-portrait-src.png` 1.79 MB · `reference/sheet-s200.png` 1.70 MB · `frozen/david.png` 1.59 MB · `frozen/goliath.png` 1.57 MB 등. 하위 디렉터리 분포: `reference/` 26 MB · `setup/` 12 MB · `samples/` 5.3 MB · `frozen/` 3.0 MB · `scene_ref/` 800 KB · `conti/` 316 KB.

**전부 의도적 추적이다.** `params.py`가 각 디렉터리의 역할을 주석으로 못 박는다 — `frozen/`은 장면 생성의 정체성 입력(동결 얼굴 2장), `reference/`는 판정 축의 양성 기준(사용자가 목표로 지정한 그림이라 지어낼 수 없고, 임계가 이 집합에서 파생된다), `notes/`는 판단 문서 20 + meta JSON 37. 즉 이 이미지들은 산출물이 아니라 **판정의 입력**이므로 gitignore 대상이 아니라는 판단이 서 있다.

남는 부담은 셋이다. ① PNG는 델타 압축이 안 먹으므로 이미지를 교체·재동결할 때마다 팩이 그만큼 커진다(되돌릴 수 없다 — 히스토리에 남는다). ② `frontend/dist` 미추적·`data/` 19 MB 시절 기준으로 잡힌 클론·CI 비용 감각이 5배로 어긋난다. ③ 이미지 자산에 대한 정합 게이트가 없다 — `reference/REFERENCE.md`·`frozen/FROZEN.md`·`samples/SAMPLES.md`가 무엇이 정답지인지 글로 적지만, 그 목록과 실제 파일 집합의 대응을 재는 검증기는 없다(`validate_canon_pipeline`은 `.py`만 본다).

### 11. 실험 스크립트 46개가 정본과 한 디렉터리에 쌓여 있다 + 죽은 경로 참조

**심각도: 중간 · 시급도: 낮음**

`scripts/canon/`의 `.py` 46개 중 `gen_*` **21개**, `judge_*` **8개**다. 이름이 실험 축을 그대로 담고 있어(`gen_cge_sweep` · `gen_cn_curve` · `gen_contrast_flip` · `gen_knee_ip` · `gen_oil_probe` · `gen_prompt_axis` · `gen_cause_probe` · `sweep_cause` · `arm_sweep` · `probe_cn` …) 어느 것이 현재 정본 경로이고 어느 것이 지나간 스윕인지 파일 목록만으로는 갈리지 않는다. 실제 정본 진입점은 `notes/PROMPTING.md`(실측 규칙)와 `try_prompt.py`(연습대), 그리고 현행 장면 생성기 `gen_scripture_scene.py`인데 이는 문서를 읽어야 알 수 있다. `notes/`에도 같은 층이 쌓였다 — `final-verdict-*.json` 22개를 포함해 meta JSON 37개가 라운드별로 누적됐다.

폐기 판단이 코드에 반영되지 않은 자리도 있다. 예: `gen_scripture_scene.py`(미커밋 작업트리)의 도크스트링은 "**콘티를 쓰지 않는다**"고 사용자 지시를 명시하는데, `scripts/canon/conti/`(316 KB — `render_conti.py`·`make_conti_masks.py`·`goliath_scene.html` + PNG 10장)는 그대로 추적 중이다. 폐기가 정당한 이력 보존일 수도 있고 정리 누락일 수도 있는데, 코드만 봐서는 구별되지 않는다.

**죽은 경로 참조(확인됨)**: task#316이 스크립트를 `.forge/reports/canon-pilot/`에서 `scripts/canon/`으로 옮겼는데 문서 참조가 따라오지 않았다. `scripts/check_mask_ranges.py:5`가 "`.forge/reports/canon-pilot/make_masks.py`가 `derive_ranges()`를 그대로 가져다 쓴다"고 적지만 그 경로에 파일이 없고(실제는 `scripts/canon/make_masks.py`), `:9`가 가리키는 `.forge/reports/canon-pilot/MASKS.md`도 실제로는 `scripts/canon/notes/MASKS.md`다. `notes/MASKS.md:122-125`·`notes/SCALE-INPUT.md`·`notes/SCALE.md`에도 같은 구 경로 참조가 남아 있다. 산출물 경로 참조(`try_prompt.py:26`의 `.forge/reports/canon-pilot/try/` 등)는 유효하므로, **같은 접두어의 유효 참조와 죽은 참조가 섞여 있어** 일괄 치환으로는 못 고친다.

### 12. 장면 승인 도구 로컬 HTTP 서버 — 바인딩·경로·인증 (2026-10 증분)

`scripts/canon/tool/server.py`(ThreadingHTTPServer, 기본 `127.0.0.1:8100`)는 GPU 생성을 돌리고 `scripts/canon/scenes/*.json` 명세를 고친다. 바깥 접근은 레포 밖 Cloudflare Tunnel + Access에 의존한다(소스에 없는 외부 전제).
- **바인딩**: `SCENE_TOOL_BIND`가 루프백 밖이면 `SCENE_TOOL_TOKEN` 또는 `SCENE_TOOL_USERS`가 없을 때 `main()`이 종료하고, `SCENE_TOOL_DEV=1`도 루프백 밖이면 종료한다. 시작 가드는 있으나 토큰/허용목록이 비어 있지 않다는 것만 보며 강도는 보지 않는다. 시크릿 값은 환경변수에만 있고 소스에 없다.
- **경로**: 이미지 서빙은 `IMG_ROOT`(`.forge/reports`) 접두 검사(`server.py:328`)로 탈출을 403 처리한다. `startswith(IMG_ROOT + os.sep)` 비교라 정규화(realpath) 선행 여부와 심볼릭 링크 처리는 이 가드가 보장하지 않는다 — 수정 시 재확인 자리.
- **상태가 프로세스 메모리**: `JOBS`·`COMPOSE`·`CUR`(진행 중 서브프로세스)가 전역 딕셔너리/큐라 재시작 시 큐·진행 중 생성이 사라진다. 단일 GPU 워커 스레드 전제.
- **환경 하드코딩**: `SCENE_TOOL_VENV` 기본값이 `/Users/calmonion/.local/biblemap-imggen/.venv314/bin/python`(레포 밖 런타임 — §Tech Debt 9와 같은 재현성 구멍). 스모크용 `SCENE_TOOL_FAKE_GEN`·`*_DIR` 환경 오버라이드가 실제 산출 트리를 덮은 사고(2026-09-05 adullam-cave a001)가 주석으로 남아 있다.
- 검증은 `scripts/canon/tool/uat_scene_tool.py`(UAT)와 `scripts/canon/test_scene_state.py`뿐이며 `scripts/check.sh`에는 배선되지 않았다.

### 13. 장면 상태 기계 `scripts/canon/scene_state.py` — 취약 지점

`ladder_hashes`·`live_stages`·`stale`·`board`가 명세 해시로 "어느 단계 승인이 낡았는지"를 계산한다. 낡음 판정은 `_h`가 해시에 넣는 필드 집합에 전적으로 의존하므로 명세에 새 필드를 추가하고 해시 대상에 넣지 않으면 승인이 낡지 않은 채 남는다(무음). 승인·시도 기록은 `scripts/canon/attempts/*.json`·`scenes/*.json`에 파일로 쌓여 동시 쓰기 잠금이 없다(도구는 단일 사용자 전제). 코드 마커(TODO/FIXME)는 없다.

### 14. 작업트리 미커밋 편집 (2026-10-10 실측)

`git status`상 `scripts/canon/attempts/authored-david-adullam-cave.json`·`scripts/canon/scenes/authored-david-adullam-cave.json`·`scripts/canon/tool/glossary.json`이 수정 상태, `.forge/dropped/` 5디렉터리(`david-tour-scenes-loop`·`scene-eye-defects`·`scene-figures-inscene-anchor`·`scene-followup-2of2-task322`·`scene-style-transfer-pilot`)가 미추적. 앞 셋은 사람 관문(길갈 대관식 장면 진행) 중의 도구 산출물이라 커밋 전 push는 `deploy.yml`의 `git reset --hard`로 소실될 수 있다(§Deploy 5). `.forge/dropped/`는 `validate_forge_docs_tracked` 스캔 루트 밖이라 배포는 막지 않는다.

### 15. Apache AGE 호환성 점검 판정 "막힘" — neo4j 유지

`scripts/age_compat/REPORT.md`(task#340, 하네스 `run_check.py`·`age_adapter.py`·`docker-compose.yml`): 호출 지점 94 중 막힘 4·기계적 치환 7. 막힘은 `backend/app/routes/family.py:97`(`all(n IN nodes(p)[1..] ...)` 리스트 술어 미지원), `backend/app/routes/nodes.py:175`(agtype 컨테이너 내부 오류), `backend/app/routes/search.py:23`(문자열 정렬 순서가 neo4j와 다름), `backend/scripts/apply_event_dedupe.py:45`(`CALL (r,k) {}` 서브쿼리 미지원). 지연도 9/45 엔드포인트가 10배 이상 느리고 최악 `/person/{jesus}/family` 24.4s(neo4j 48ms). ADR `261010-110220-keep-neo4j-as-standard-db-exception`이 neo4j를 표준 DB 예외로 확정했다. 위험: 하네스가 레포에 남아 있어 neo4j 쿼리가 바뀌면 보고서가 낡는다(재실행 `python3 scripts/age_compat/run_check.py`), 하네스는 `check.sh`에 배선되지 않았다.


### 16. 그림 파이프라인 — 모듈 상태·검사 함수 등록·요단 구역·산출물 누적 (2026-10-24 증분)

- **모듈 전역 상태로 넘기는 값**: `scripts/canon/batch/make_guide.py`의 `BODY`(몸 너비·무릎·`big_tip`·`leaf_tip`)와 `PERSP["hy"]`(장면 지평선)는 꼴 함수 서명 `(d, 상자, v)`를 유지하려고 모듈 딕셔너리로 전달된다. `make()`가 인물마다 바꾸고 `pop`으로 되돌리는 구조라 예외·중단 시 값이 남아 다음 호출에 새고, 병렬 호출에 안전하지 않다.
- **생성 층 검사 함수 미등록**: `scripts/canon/recheck.py`는 `SPEC_CHECKS`에 없는 생성 층 규칙을 재검에서 조용히 뺀다(`r["check"] in SPEC_CHECKS` 필터). 이제 `scripts/canon/test_recheck.py`가 등록 누락을 막지만, `scripts/canon/test_*.py`는 `scripts/check.sh`에 배선돼 있지 않다(2026-10-24 확인 — 저작 파이프라인 게이트는 `validate_canon_pipeline` 하나) — 작업마다 DoD 명령으로 손수 돌려야 걸린다.
- **요단 장면 구역과 원근 어긋남**: `scripts/canon/notes/SCALE-CROWD.md` 재검 목록 기준 — `generate.figure-scale`(사람 수 2055 대비 구역 0.62)·`generate.eye-level-perspective`(시바·유다 무리 구역이 원근보다 낮음) 실패, 유다 족속(gilgal) 구역은 지평선 위 둑이라 셈 밖. 사람 결정 대기이며 요단 가이드 구역 재저작이 필요하다.
- **산출물 누적**: `scripts/canon/batch/*.log` 146개가 미추적으로 쌓여 있고(`.gitignore` 미적용, 추적 로그 0) `scripts/canon/samples/` 382개 파일이 추적된다. `git add -A` 한 번에 로그가 커밋에 딸려 갈 수 있다.

---

## Dependencies at Risk

- **`anthropic` · `kiwipiepy`가 어디에도 선언돼 있지 않다.** `backend/requirements.txt`는 `fastapi==0.136.3` · `neo4j==6.2.0` · `uvicorn==0.49.0` 3줄뿐이다. `anthropic`은 5개 스크립트가 import한다(`backend/scripts/generate_book_events.py:17` · `generate_book_context.py:20` · `generate_person_context.py:25` · `generate_verse_events.py:16` · `generate_person_traits.py:21`). `kiwipiepy`는 `backend/scripts/build_word_verse_index.py:35,45`와 `build_word_distribution.py:37`이 함수 내부에서 import하며, 도커스트링(`build_word_verse_index.py:17`)이 임시 venv 설치를 안내한다 — **현재 이 머신에 미설치**(확인함). `requirements-dev.txt`·락파일·파이썬 버전 고정 없음. **심각도: 중간 · 시급도: 낮음**
- **`backend/Dockerfile:5`가 `app/`만 복사한다** — `scripts/`가 이미지에 없다. 그래서 `deploy.sh:60`이 **호스트 `python3`**로 주입 스크립트를 돌린다(호스트에 우연히 깔린 패키지에 의존). 재현성 구멍.
- **theographic 원본을 GitHub `master` HEAD에서 미고정 fetch** — `backend/scripts/load_books.py:14-15`(`BOOKS_URL`·`EVENTS_URL`), `load_theographic.py` 동일 패턴. 업스트림이 바뀌면 재적재 결과가 조용히 달라진다.
- **프론트 의존성 전부 caret, 고정 0건** — `frontend/package.json`: `react ^19.2.6` · `react-dom ^19.2.6` · `maplibre-gl ^5.24.0` · `lucide-react ^1.17.0` · `vite ^8.0.12` · `eslint ^10.3.0` · `eslint-plugin-react-hooks ^7.1.1` 등. `package-lock.json`이 있어 평시엔 고정되지만, 락 재생성 시 `deploy.sh:44`의 `npm install`이 그대로 프로덕션 빌드로 간다.
- **`docker-compose.yml:3` `image: neo4j:5`** — 메이저만 고정, 마이너/패치는 부동.
- **빌드타임 외부 API 의존** — 절 본문 프리베이크(getbible)·LLM 저작 스크립트(Anthropic API). 재현에 외부 서비스와 API 키가 필요하다.
- **저작 파이프라인 의존성은 별 파일로 박제됐다 — 다만 락이 아니라 스냅샷이다.** `scripts/canon/requirements.txt`(신설, task#316)가 `torch==2.13.0` · `diffusers==0.40.0` · `transformers==5.15.1` · `accelerate==1.14.0` 등 **46줄 전부 `==` 고정**이다. 생성 방식이 주석에 적혀 있다 — `~/.local/biblemap-imggen/.venv314`의 `pip freeze`(2026-08-25). 즉 **선언이 아니라 사후 스냅샷**이고, `backend/requirements.txt`(3줄)와 별개이며 앱 배포는 설치하지 않는다(ADR `260825-065028`). 그래서 파이썬 버전 고정도, 이 파일로 venv를 다시 만들어 봤다는 실측도 없다. 무엇보다 **여기 고정된 것은 파이썬 패키지뿐이고 모델 가중치는 리비전이 없다**(§Tech Debt 9의 미결 1축) — 패키지가 전부 같아도 업스트림이 가중치를 갱신하면 그림이 달라진다.
- **`anthropic`·`kiwipiepy` 미선언과 대비되는 비일관** — 저작 파이프라인은 46줄 `==` 고정을 받았는데, 같은 저장소의 LLM 저작 스크립트 5종이 쓰는 `anthropic`과 한국어 형태소 인덱스 2종이 쓰는 `kiwipiepy`는 여전히 어느 파일에도 선언이 없다(위 첫 항목). 요구사항 선언의 강도가 서브시스템마다 다르다.

---

## Test Coverage Gaps

- ~~**자동화 테스트 0건.**~~ → **부분 해소(task#261, 이후 확대)**: 프론트 순수 함수 5모듈에 vitest **88건**(`urlState`·`mapGeo`·`mapRingController`·`dates`·`useReadingProgress`의 `computeResume`), `npm test`로 실행되고 `scripts/check.sh`의 프론트 블록에 배선됐다. `useReadingProgress.test.js`는 task#276이 잡은 회귀(완독한 책의 이어읽기가 없는 장을 가리키던 결함)의 재발 방지 테스트다. **백엔드 pytest는 여전히 0건 — 의도된 결정**(ADR `260801-195023`: Neo4j 없이 테스트 가능한 라우트가 둘뿐이라 회수가 적다). React 렌더 테스트·커버리지 도구도 의도적 미도입.
- **ESLint·유닛 테스트는 PR에서 안 돈다.** `npm run lint`/`npm test`는 수동이거나 배포 게이트 시점. 게이트의 프론트 블록은 `frontend/node_modules` 부재 시 스킵이지만, 배포는 `CHECK_STRICT=1`로 호출하므로 **스킵이 곧 실패**다(task#259). PR 시점 CI가 없는 건 그대로(이 프로젝트는 PR을 쓰지 않는다).
- ~~**ADR-0029가 약속한 투어 정차지 ↔ 장면 스케치 커버리지 대조 스크립트가 없다.**~~ → **해소(task#259) · task#287로 판정 기준 재작성**: `backend/scripts/validate_scene_coverage.py`가 이제 결함 클래스 **A~G 7종**을 갈라 본다(미저작 · 고아 키 · 허용목록 잔존 · 모듈 미연결 · 투어 미연결 · **오배치** · 인트로 미연결). 동적 로드 전환으로 "키가 있다"가 더 이상 "렌더된다"를 뜻하지 않게 됐기 때문이다(§Fragile Areas 10). `EXPECTED_UNCOVERED`는 **빈 집합이 정본**이다 — 새 정차지는 스케치를 함께 저작한다.
- ~~**시대 결합 검증이 부분 커버**~~(§데이터 정합성 4) → **대부분 해소(task#284)**: `validate_era_bands_consistency.py`가 4→7축으로 확장돼 투어 JSON `era`·`PersonHub.jsx`의 `ERA_ORDER` 사본·`'신약'` 기능 게이트 리터럴 전수를 이제 검사한다. **소스 정규식 스크래핑**이라는 취약성 자체는 그대로 남아 있다(ADR `260819-205242`가 인정하고 남긴 결정, fail-closed라 안전 방향).
- ~~**`_ERA` ↔ `_NAME_KO` 35키 정합 검증 없음**~~(§데이터 정합성 5) → **해소(task#278)**: 두 테이블이 `curated.py`의 `CURATED` 하나로 병합됐고 `validate_curated_persons.py`가 양방향 정합을 게이트한다. **단 이 게이트는 파일명 집합만 보고 `person_events/*.json`의 내용을 파싱하지 않는다** — 손상된 JSON은 걸리지 않는다(§데이터 정합성 5의 잔존 항목, 후속 후보로 이미 지목됨).
- **`data/authored_persons/` 전용 validate 없음** — 다른 저작 데이터 12종은 검증기가 있다.
- ~~**하드코딩 ID 테이블 스테일 검출 게이트 없음**~~ → **VERSE_MAP 클래스는 해소(task#274)**, **`_ERA`/`_NAME_KO` 클래스도 해소(task#278)** — `validate_approx_book_verses.py`·`validate_curated_persons.py`가 각각 배포 게이트에 배선됐다. ADR `260820-003946`이 예고한 대로 같은 `ast.literal_eval` 소스 추출 형태가 그대로 재사용됐다.
- **Person 생몰 ↔ Event 연대 계 격차 측정 게이트 없음**(§데이터 정합성 1) — 이 축은 여전히 미검증이다. **다른 두 연대 축은 이번에 새로 게이트됨**: `sortKey`↔`startDate` 전역 역전(`validate_sortkey_startdate.py`, task#283)과 근거 절 범위↔라벨 정합(`validate_event_verses.py`, task#282) — 둘 다 §데이터 정합성 1·9 참조.
- **`/node/{id}` vs `/node/{id}/neighbors/grouped` 동작 일치 테스트 없음** — `backend/app/routes/nodes.py:120-147`의 `get_node_neighbors_grouped`는 여전히 `-[r]-(m)` 무방향 매치에 정규화·디듀프가 없다. 유일 소비처 `frontend/src/mapRingController.js:112`가 응답의 Event만 읽어 현재 UI 영향은 없다.
- **UI 검증은 Playwright 수동 실행 의존**, CI 미연동. 증적은 `.forge/reports/`의 수동 캡처뿐. 이번 갱신으로 수동 UAT 스크립트가 2종 늘었다 — `scripts/uat_scene_detail_pilot.py`(애니메이션을 `pause()`+`currentTime` / `pauseAnimations()`+`setCurrentTime()`으로 고정해 필름스트립을 찍는다, 그래야 비결정적이지 않다)와 `scripts/uat_tour_chunk_split.py`(**네트워크를 본다** — 정적 청크 목록만 보면 "쪼갰지만 어차피 전부 로드"가 통과하므로, 한 투어 재생 중 다른 투어 청크가 요청되지 않는지를 격리 축으로 잰다). **둘 다 `check.sh`에 배선되지 않는다** — `deploy.sh`가 빌드 **전에** 게이트를 부르므로 그 시점 `:8080`은 옛 빌드를 서빙해 초록·빨강이 둘 다 거짓이 된다(`uat_intro_gutter.py`·`uat_intro_entry.py`와 같은 이유).
- **저작 파이프라인은 실행 축이 전혀 검증되지 않는다.** `scripts/canon/`의 게이트는 `validate_canon_pipeline` 하나뿐이고, 그것도 **소스만** 본다(정본 재선언 0건 · `scripts/` 미추적 0건). GPU도 생성 venv도 없는 `check.sh` 환경이라 실행형 검사가 애초에 성립하지 않는다는 것이 도크스트링의 설명이다. 판정 도구(`judge_*.py` 10개)는 파이프라인 산출물을 채점하는 저작 도구이지 게이트가 아니며 `check.sh`에 배선되지 않는다. 같은 이유로 `scripts/render_scene.py`(저작자용 시각 피드백)도 배선 밖이다 — 도크스트링이 "판정 게이트가 아니다"라고 명시한다. 즉 **이 서브시스템의 초록은 "선언이 한 곳에 있다"까지이고 "그림이 나온다"는 사람이 본다.**
- **장면 저작 규약 게이트의 미결 축(B12)** — `backend/scripts/validate_scene_sketch_detail.py`가 B1~B12를 강제하는데, B12(인물 정본 컴포넌트 사용 강제)의 판정 신호가 **이름표(`<Label>`)의 존재**다. 이름표 없이 그려진 인물은 기계 신호가 없어 강제 대상에서 빠진다 — 도크스트링이 "대안 없음(미결로 남긴다)"이라 적었다. 또한 이 검증기는 정본 컴포넌트 호출부(`<David cx={..} .../>`)를 소스에서 읽어 리터럴로 치환·평가해 인라인 전개하므로(`expand_cast`), **호출 규약(숫자 리터럴 인자, `transform`·조건 분기 금지)을 어기면 전개가 깨진다** — 규약을 지키는 한 초록이지만 규약 자체를 강제하는 축은 이 파일 안에 없다.
- **정본 구별성은 5축 조합 중복만 본다** — `scripts/check_cast_axes.py`가 `cast/*.jsx`의 `export const AXES` 5축(머리카락·수염·머리쓰개·나이대·성별) 조합이 파일 간 겹치지 않는지 단정한다. 조합이 같으면 서로 다른 인물이 같은 얼굴로 그려질 수 있다는 것이 근거다. 정본이 2개(david·goliath)인 현재는 표면이 좁고, **축이 5개뿐이라 인물이 늘면 조합이 고갈된다** — 그때 이 검사는 "겹쳤다"고 빨강을 낼 뿐 축을 늘려 주지는 않는다.
- **헬스/레디니스 엔드포인트 없음** — 오버레이 로딩 실패(§데이터 정합성 8)나 Neo4j 인덱스 생성 실패(`backend/app/main.py:37-38`이 예외를 삼키고 계속 진행)를 외부에서 알 방법이 없다.

---

## Scaling Limits

- **단일 인스턴스 스택** — neo4j 1 + api 1 + nginx 1(`docker-compose.yml`). `backend/Dockerfile:6`의 CMD에 `--workers` 없음 → uvicorn 단일 워커. 요청 처리가 한 프로세스에 직렬화된다(비용 큰 동기 엔드포인트 §Performance 4가 이벤트 루프를 점유).
- **`lru_cache`가 프로세스 로컬** — 공유 캐시 계층이 없어 워커를 늘리면 §Performance 8의 19 MB JSON 상주가 워커 수만큼 곱해지고, 무효화도 워커별로 갈린다.
- **정적 자산·API 모두 무압축**(§Performance 1) — 대역폭이 인스턴스 수보다 먼저 병목이 된다.

---

## 코드 마커 현황 (참고)

`TODO`/`FIXME`/`HACK`/`XXX` 마커는 **`backend/`·`frontend/src/`·`scripts/` 전체에 0건**이다(재확인 — `scripts/canon/` 46개 스크립트를 포함한 집계). 이 코드베이스는 `task#NNN`·`ADR-NNNN` 참조 주석을 부채 추적 관용구로 쓴다(예: `frontend/src/MapView.jsx:15` "선재 버그, task#251", `backend/app/routes/stats.py:22-23` "공유 설정이 없어 수동 복제"). 위 항목 다수가 그런 자백 주석에서 출발했다.

새 서브시스템은 그 관용구를 더 강하게 쓴다 — `scripts/canon/params.py`·`requirements.txt`·`backend/scripts/validate_canon_pipeline.py`·`validate_scene_sketch_detail.py`의 도크스트링이 **자기 게이트의 한계를 스스로 열거**한다("초록은 이 불변식이 아는 재선언이 없다는 뜻이지 드리프트가 없다는 뜻이 아니다", "재현을 닫지 않는다 — 미결 3축", "대안 없음(미결로 남긴다)"). 이 문서의 §Tech Debt 9·11과 §Test Coverage Gaps 다수가 거기서 그대로 옮겨온 것이다.

`eslint-disable` 인라인은 **4건**으로 그대로이며 전부 한 줄 범위 + 근거 주석 동반(`frontend/src/useStageNavigation.js:151,214` · `VerseLayer.jsx:21` · `personSymbols.jsx:488`). 단 이번에 **설정 파일 수준의 규칙 해제가 1건 생겼다** — `frontend/eslint.config.js:21-28`이 `src/sketches/cast/**/*.jsx`에서만 `react-refresh/only-export-components`를 끈다(§Fragile Areas 11). 인라인 4건과 달리 이건 디렉터리 전체에 걸리므로, 그 디렉터리에 새 파일이 늘 때 자동으로 예외에 든다.

`backend/app/`에 `print()`·root logger 직호출 0건으로 `CLAUDE.md`의 로깅 규약을 지키고 있다(재확인). 다만 `scripts/canon/`은 이 규약의 대상이 아니라 전부 `print(..., flush=True)`로 진행 상황을 찍는다 — 앱 모듈이 아닌 CLI 저작 도구라 의도된 이탈이다.
