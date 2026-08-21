# BibleMap 버그 리포트 — 3차 사이클 (task#285)

작성: 2026-08-21 · 대상 HEAD `e478795`(워킹트리 클린, 미추적 `.claude/settings.local.json.doctor-backup` 1건은 이 리포트와 무관)
방법: 배포 게이트 `scripts/check.sh`(32항목)가 **보지 않는 5축**을 렌즈당 2각도(총 10 finder)로 병렬 발굴 → 트리아지(중복 병합 + 드롭 사유 기록) → 후보별 독립 적대적 검증(HIGH는 재현/반증 2각도, 그 외 1각도 — 총 23 스켑틱) → confirmed HIGH 수정.
계수: **원시 23건 → 트리아지 드롭 3건 → 후보 17건 → 적대적 검증 17건 → confirmed 12건 / refuted 5건.**
(2차 리포트의 `refuted 0건`이 "발굴이 전부 진짜였다"로 오독된 전례가 있어, 이번에는 트리아지 드롭 수까지 머리말에 명시한다.)

규칙: confirmed는 캡 없이 전건 수록. **수정은 HIGH만** — MEDIUM/LOW는 리포트에만 남기고 후속으로 넘긴다(계획 Non-goals). HIGH 5건은 전건 수정했다.
주행 중 세 지점에서 사람의 결정을 받았다: `data/*.json` 손 교정 허용(#3·#4) · `enrich_place_coords.py`의 '기존 값 보존' 의미 전환과 그 반영을 위한 Neo4j 쓰기(#5). 에이전트가 스스로 넓히려다 안전 분류기에 차단된 이력이 있어(자세한 경위는 `.forge/run.md`), 이후로는 전부 질문으로 올려 승인받고 진행했다.
심각도는 발굴자 추정을 쓰지 않고 검증자가 독립 재판정했으며, 판정이 갈린 3건(#1·#5 및 refuted C1)은 이 리포트 작성자가 직접 실측해 재정했다(각 절의 «검증 요지»에 명기).

## 요약

| # | 심각도 | 렌즈 | 위치 | 증상 | 처리 |
|---|--------|------|------|------|------|
| 1 | HIGH | L2 프론트 런타임 상태 | `frontend/src/useStageNavigation.js:181-214` | 주소창에 다른 딥링크 해시를 붙여넣으면 `state:null` popstate를 히스토리 시작점으로 오판해 URL이 가리키는 화면 대신 인물 허브로 상태를 파괴한다 | 수정 완료 |
| 2 | HIGH | L5 배포·운영 | `backend/app/routes/reliance.py:146`, `backend/app/routes/books.py:102`, `backend/app/routes/verses.py:47` | 정적 데이터 API가 `public, max-age=3600`+ETag 부재라, 이 프로젝트의 표준 데이터수정 경로(`data/` 편집 + `docker compose restart api`)로 고친 내용이 재방문 브라우저에 최대 1시간 반영되지 않는다 | 수정 완료 |
| 3 | HIGH | L3 데이터 의미 정합 | `data/god_reliance/abraham.json:12-13,21-22,27-28` | `trigger`/`response`/`outcome`의 인용 절이 그 라벨이 서술하는 사건과 다른 절을 가리킨다 — 아브라함 `'칼을 들어 이삭을 잡으려 순종함'`에 창22:12(천사가 저지하는 **정반대** 내용)가 붙었다. 395건 전수 재감사로 26개 파일 79건 | 수정 완료 |
| 4 | HIGH | L3 데이터 의미 정합 | `data/god_reliance/saul.json:35-40` | 아말렉 불순종 판결(15:11)과 그 여파(영이 떠남, 16:14)를 별개 항목 2건으로 쪼개 분모를 이중 계수 — 화면의 사울 의존도가 56%로 표시되나 사건 단위 원칙대로 병합하면 62% | 수정 완료 |
| 5 | HIGH | L4 스크립트 재실행 안전성 | `backend/scripts/enrich_place_coords.py:60-80` | `WHERE pl.latitude IS NULL` 가드가 rec* 11건 전원에서 상시 거짓이라 저작한 좌표 교정이 **한 번도 적용된 적이 없다** — 시내산이 저작 의도보다 위도 0.96°(≈107km) 어긋난 채 서빙 중 | 수정 완료 |
| 6 | MEDIUM | L2 프론트 런타임 상태 | `frontend/src/App.jsx:471-486` | 모바일 하단 시트가 관계·의존 탭 전환 후에도 닫히지 않고 화면 75%를 덮어 콘텐츠를 가린다(데스크톱은 정상 억제) | 후속 |
| 7 | MEDIUM | L3 데이터 의미 정합 | `data/character_traits/people.json:512-518`, `data/character_traits/people.json:619-624` | 야고보 '담대함'(막3:17)·안드레 '겸손'(요1:40) 앵커절이 실제 성품 장면이 아니라 별명 부여·신원 소개 서술뿐 | 후속 |
| 8 | MEDIUM | L4 스크립트 재실행 안전성 | `backend/scripts/apply_event_dedupe.py:31-33` | `save_json()`이 무조건 `json.dump(indent=2)`로 재직렬화해, 1~2건 삭제가 86→122줄 전면 재포맷 diff에 파묻힌다 | 후속 |
| 9 | MEDIUM | L5 배포·운영 | `deploy.sh:10-15` | 배포 락에 PID·mtime 검사가 없고 `trap ... EXIT`은 SIGKILL에 발동하지 않아, 강제종료 1회로 이후 모든 자동배포가 수동 `rm` 전까지 정지한다 | 후속 |
| 10 | LOW | L1 백엔드 라우트 계약 | `backend/app/routes/reliance.py:1-3`, `backend/app/routes/reliance.py:21` | docstring·주석이 ADR-0023 2026-07-15 개정(언약형도 분자 산입) 이전 정의를 그대로 서술해 실제 코드와 반대 — 주석만 보고 '고치면' 정상 동작이 깨진다 | 후속 |
| 11 | LOW | L3 데이터 의미 정합 | `data/character_traits/people.json:99` | 베드로 '통회'(눅22:62) description이 앵커 절 범위를 넘어 그 절에 없는 사후 내러티브(부활 후 회복·교회의 기둥)를 서술 | 후속 |
| 12 | LOW | L5 배포·운영 | `nginx/nginx.conf:35-37` | 확장자 기반 1년 immutable 캐시 규칙이 콘텐츠해시 없는 정적 파일(웹폰트·favicon)에도 적용돼 내용 교체 시 최대 1년간 갱신 불가 | 후속 |

---

### 1. [HIGH] `frontend/src/useStageNavigation.js:181-214` — `state:null` popstate를 히스토리 시작점으로 오판해 딥링크 재진입 시 화면 상태를 파괴

- **렌즈**: L2 프론트 런타임 상태 · 적대적 검증 **CONFIRMED** (2각도 만장일치, 심각도 합의)
- **증상**: SPA가 이미 떠 있는 상태에서 주소창에 다른 딥링크 해시를 붙여넣으면(동일문서 프래그먼트 내비게이션), URL은 요청한 화면을 정확히 가리키는데 실제 화면은 인물 허브로 리셋된다. 탐색 중이던 인물·투어·책·장소 상태가 전부 소실된다.
- **근거**: `frontend/src/useStageNavigation.js`의 popstate 핸들러가 `if (!s) { setActiveStage('hub'); ...전체 null화...; return }`로 `event.state`가 없으면 무조건 허브로 초기화했다(수정 전 186행). 그런데 `state:null`은 서로 다른 두 가지가 뭉뚱그려진 값이다 — ① 진짜 히스토리 시작점, ② 동일문서 프래그먼트 내비게이션이 만든 무상태 엔트리. HTML 명세상 프래그먼트 내비게이션은 `hashchange`와 함께 **`popstate`도 발생**시키므로 ②가 이 분기를 그대로 탄다. 앱 자체 내비게이션은 `pushState`/`replaceState`(state 보유)만 쓰므로 이 분기에 실제로 도달하는 것은 대부분 ②다.
- **재현**: Playwright(chromium 1400×900). ① `http://localhost:8080/#/tour/patriarchs-covenant` 로드 → '언약의 4세대 · 사건 36개' 렌더 확인. ② 캡처 단계 popstate 리스너 주입 후 `location.href='#/tour/creation-to-flood'` 실행. ③ 관측: `popstate events: ['null']`, `location.hash: '#/tour/creation-to-flood'`, 그러나 화면 본문은 `'성경 인물 탐험 … 제1장 원시사'`(인물 허브). 주소창 붙여넣기를 그대로 흉내낸 `page.goto`(같은 오리진·해시만 다름)로도 동일 재현.
- **검증 요지**: 두 검증자가 독립적으로 CONFIRMED/HIGH. 반증 시도 3건이 모두 실패했다 — (a) "프래그먼트 내비게이션은 hashchange만 발생시킨다"(`.forge/codebase/CONCERNS.md`가 전제하던 바)는 실측으로 반증됨(popstate가 실제 발화), (b) "화면은 그대로고 URL만 바뀌는 무해한 현상"은 스크린샷으로 반증됨, (c) "투어 슬러그가 무효해 진입 자체가 실패한 것"은 `curl /api/tours`로 두 슬러그 실재 확인해 반증됨.
- **수정 완료**: `frontend/src/useStageNavigation.js:186-196` — `state:null`일 때 즉시 허브로 리셋하지 않고 **URL을 먼저 재해석**한다. `state`가 없어도 URL은 항상 신뢰 가능한 진실이기 때문이다. 무타깃 판정은 **정본 술어 `isNoTarget`만** 사용했다(`frontend/src/useStageNavigation.js:193`) — ADR `260821-000937`이 "무타깃 판정 지점은 정본 밖 0곳"을 불변식으로 못 박았고 `backend/scripts/validate_intro_entry_route.py`가 이를 게이트에서 강제하므로, 여기서 `'#'`/`'#/'` 리터럴을 새로 비교했다면 게이트가 빨강이 됐을 것이다. 무타깃이면 종전과 동일한 전체 리셋으로 폴백해 기존 동작을 보존한다.
  - **변경 파일**: `frontend/src/useStageNavigation.js`(popstate 핸들러 null 분기 1곳). 새 상태·새 술어·새 의존성 없음.
  - **재현(수정 후)**: 같은 Playwright 스크립트 재실행 → `popstate events: ['null']`(발화 자체는 동일), `location.hash: '#/tour/creation-to-flood'`, 화면 본문 `'창조에서 홍수까지 … 사건 23개'` — **URL과 화면이 일치**. 판정 PASS.
  - **회귀 확인(수정 후)**: 검증자가 지목한 이 수정의 최대 위험은 "진짜 히스토리 시작점이 최근 해시로 되튕기는 회귀"였다. `#/tours` → `#/tour/creation-to-flood` → 뒤로가기 실측 → `#/tours`('인물 허브 · 테마 투어')로 정상 복귀, 되튕김 없음. 판정 PASS. 추가로 `CHECK_STRICT=1 bash scripts/check.sh` 32항목 전부 PASS(`validate_intro_entry_route --selftest` 포함).

### 2. [HIGH] `backend/app/routes/reliance.py:146`, `backend/app/routes/books.py:102`, `backend/app/routes/verses.py:47` — 1시간 캐시가 이 프로젝트의 표준 데이터수정 경로를 무력화한다

- **렌즈**: L5 배포·운영(캐시 무효화) · 적대적 검증 **CONFIRMED** (2각도 만장일치, 심각도 합의)
- **증상**: `data/*.json`을 고치고 `docker compose restart api`로 반영하는 이 프로젝트의 문서화된 표준 데이터수정 경로를 따라도, 그 URL을 이미 한 번 받아간 브라우저는 **최대 1시간 동안 서버에 재문의조차 하지 않고** 옛 JSON을 그대로 보여준다.
- **근거**: 해당 라우트들이 `headers={"Cache-Control": "public, max-age=3600"}`을 내려보내면서 ETag·Last-Modified를 함께 주지 않아, 브라우저는 신선도 판정만으로 캐시를 재사용하고 조건부 GET(304)을 할 기회가 없다. `nginx/nginx.conf`의 `location /api/`는 `proxy_pass`만 하고 헤더를 가공하지 않아 그대로 통과한다. 프론트의 캐시버스터 `frontend/src/api.js:12`(`?v=BUILD_ID`)는 정확히 이 문제를 막으려고 도입됐지만 **빌드타임 리터럴**이라(`vite.config.js`의 define) 프론트를 다시 빌드하지 않는 `restart api`만으로는 값이 바뀌지 않는다. 즉 캐시버스터가 설계상 커버하지 못하는 경로가 하필 표준 데이터수정 경로다.
- **재현**: ① `curl -s -o /dev/null -D - 'http://localhost:8080/api/person/recsU2ZSdzBvDqzgI/reliance'` → `cache-control: public, max-age=3600`, ETag 없음. ② Playwright로 같은 URL을 두 번 fetch → 1회차 `transferSize: 1369`, 2회차 `transferSize: 0, encodedBodySize: 1069` — 두 번째 요청이 네트워크 전송 0바이트로 브라우저 캐시에서 응답됨(서버 재문의 없음)을 실측.
- **검증 요지**: 두 검증자가 독립적으로 CONFIRMED/HIGH. 한쪽은 Playwright `transferSize=0`으로 실측 재현했고, 다른 쪽은 HTTP 캐시 표준(max-age + ETag 부재 → 검증 없는 신선도 판정)이 결정론적이므로 코드 경로만으로 발현이 필연임을 증명했다. `git show`로 `BUILD_ID` 도입 커밋의 전제(전체 재배포)까지 확인해, 이것이 의도된 설계의 사각지대임을 특정했다.
- **수정 완료**: 문제의 6개 응답을 이 코드베이스가 이미 압도적으로 쓰고 있는 관례 `max-age=300`으로 정렬했다(수정 전 분포: `max-age=300` 21곳 · `public, max-age=3600` 6곳 · `no-store` 1곳). 새 장치(ETag 계산·데이터 버전 해시)를 들이지 않고 기존 관례에 맞추는 것이 가장 짧은 동작 diff다.
  - **변경 파일**: `backend/app/routes/reliance.py`(2곳) · `backend/app/routes/books.py`(3곳) · `backend/app/routes/verses.py`(1곳). 로직 무변경, 헤더 문자열만.
  - **재현(수정 후)**: `docker compose up -d --build api` 후 `curl -s -o /dev/null -D - 'http://localhost:8080/api/person/recsU2ZSdzBvDqzgI/reliance'` → `cache-control: max-age=300`. `grep -rn 'max-age=3600' backend/app/` → **0건**. 최대 지연이 60분에서 5분으로 줄었다.
  - **재발 게이트 배선**: 이 결함 **클래스**는 재발 가능하다 — 내일 누가 새 라우트에 긴 캐시를 달면 같은 일이 그대로 반복된다. 그래서 `backend/scripts/validate_api_cache_headers.py`를 새로 만들어 `scripts/check.sh`에 배선했다(게이트 32→34항목). 불변식은 "지금 6곳"이라는 **개수가 아니라 경계**다 — 라우트 응답의 `max-age`는 300초를 넘지 않는다(ADR `260821-000937`). 대조군 `--selftest`가 고의 위반(`max-age=3600`) 주입 시 FAIL하고 주석 안의 예시는 오탐하지 않음을 확인한다(ADR `260820-003946`). 게이트를 풀려면 조건부 GET을 먼저 붙이라는 안내를 실패 메시지와 docstring에 남겼다.
  - **남은 한계(정직하게)**: 이 수정은 창을 12배 좁힐 뿐 **없애지는 않는다**. 5분 이내 재방문은 여전히 옛 데이터를 본다. 근본 해소는 데이터 버전(로더/편집 시점 해시)을 ETag나 쿼리에 반영해 `restart api`만으로도 캐시가 자동 무효화되게 하는 것이며, 이는 프론트·백엔드 협조가 필요해 이번 최소 수정 범위 밖으로 남긴다. 또한 `max-age`를 낮추면 해당 라우트의 요청 빈도가 늘어나는 트레이드오프가 있다(서버 측 `lru_cache`가 받아내므로 비용은 작다).

### 3. [HIGH] `data/god_reliance/abraham.json:12-13,21-22,27-28` — 인용 절이 라벨이 서술하는 사건과 다른 절을 가리킨다 (10개 파일 18건)

- **렌즈**: L3 데이터 의미 정합 · 적대적 검증 **CONFIRMED** (2각도 만장일치, 심각도 합의)
- **증상**: `god_reliance`의 `trigger`/`response`/`outcome`에 붙은 근거 절이, 그 라벨이 말하는 장면이 실제로 서술된 절이 아니라 1~2절 앞선 절(또는 전혀 다른 기사)을 가리킨다. 화면(`frontend/src/RelianceView.jsx`)은 라벨과 `verseTextKo`를 **항상 나란히** 렌더하므로, 사용자는 "칼을 들어 이삭을 잡으려 순종함"이라는 라벨 바로 옆에서 "네 손을 대지 말라"는 정반대 본문을 읽게 된다.
- **근거**: 아브라함 3건이 대표적이다 — `response.verse`=창22:12 라벨 `'칼을 들어 이삭을 잡으려 순종함'`인데 `01022012`은 천사가 저지하는 내용이고 칼을 잡는 서술은 22:10이다. `outcome.verse`=창12:10 라벨 `'바로의 집에 재앙 내려 사래를 건지심'`인데 `01012010`은 기근 서술뿐이고 재앙은 12:17이다. `outcome.verse`=창17:5 라벨 `'순종하여 할례 언약을 받음'`인데 `01017005`은 개명뿐이고 할례는 17:9-14다. 게이트가 이를 통과시키는 이유는 `backend/scripts/validate_god_reliance.py`가 **절의 존재만 확인하고 내용 일치는 검사하지 않기 때문**이다.
- **재현**: `curl -s http://localhost:8080/api/person/reccdFYIq50NyxNej/reliance`로 라이브 응답의 `label`과 `verseTextKo`를 대조하면 3건 모두 어긋남이 그대로 보인다. 이어서 32개 `data/god_reliance/*.json`의 **verse 인용 395개 전수**를 `data/bible/verses.json`으로 해석·대조하는 스캔을 돌려 **10개 파일 18건** 확정: `data/god_reliance/abraham.json` 3건 · `data/god_reliance/moses.json:32` 1건(민20:12는 책망, 반석 침은 20:11) · `data/god_reliance/samuel.json:50-51` 1건(삼상16:4는 도착 장면, 기름부음은 16:13) · `data/god_reliance/solomon.json:6-7` 2건 · `data/god_reliance/jephthah.json:12-13` 1건(삿11:34는 딸의 마중, 서원 이행은 11:39) · `data/god_reliance/joshua.json:18-19` 1건 · `data/god_reliance/saul.json` 3건 · `data/god_reliance/paul.json:29-34` · `data/god_reliance/peter.json:53-58` · `data/god_reliance/isaiah.json:9-15`.
- **검증 요지**: 두 검증자가 서로 다른 경로로 독립 확인했다 — 한쪽은 전수 스캔(395개 인용)으로 18건을 세었고 발굴자 목록에 없던 `paul.json` 추가 1건까지 찾아냈으며, 다른 쪽은 `verses.json` 원문 직접 대조로 abraham 3건 + moses/samuel/paul 3파일을 재검증했다. `data/god_reliance/AUTHORING.md`·ADR-0023 어디에도 이런 불일치를 허용하는 근거가 없고, 오히려 근거 절 규칙을 명시하므로 의도된 설계가 아니다.
- **수정 완료** (사용자가 `data/*.json` 손 교정을 명시 승인한 뒤 적용): 발견 단계가 열거한 18건에 그치지 않고 **395개 인용 전수를 재감사**했다. 라벨의 핵심 내용이 인용 절에 없고 이웃 절에 있는 건을 기계적으로 추린 뒤(문자 바이그램 기준 후보 101건) 작성자가 **전건 육안 판정**해, 의역·요약이거나 같은 절 저작이 정당한 약 35건은 기각하고 **79건을 교정**했다. 예: `abraham[8].response` 창 22:12 → **창 22:10**(`손을 내밀어 칼을 잡고 그 아들을 잡으려 하더니`) · `job[5].outcome` 욥 42:5 → **욥 42:6**(`티끌과 재 가운데서 회개하나이다`) · `paul[7].outcome` 딤후 4:7 → **딤후 4:8**(`의의 면류관이 예비되었으므로`).
  - **범위 인용도 함께 해소**: `창 33:18-20`·`욥 1:20-21`·`삿 11:30-31`·`삼상 11:14-15` 4건은 라벨 내용이 범위의 **뒤쪽 절**에 있었는데, `backend/app/routes/reliance.py:37`의 `_resolve_verse()`가 **범위의 첫 절만** 해석해 화면에는 라벨과 무관한 첫 절 본문이 떴다(task#282가 `event_verses`에서 봉인한 것과 같은 결함 클래스). 각각 내용이 실제로 있는 단일 절로 좁혔고, **새 범위 인용은 하나도 만들지 않았다**.
  - **변경 파일**: `data/god_reliance/` 26개 파일. **서식 보존** — JSON 왕복 재직렬화는 32파일 중 31개를 전면 재포맷하므로(#8과 동종 결함) 쓰지 않고, 라벨을 앵커로 `verse` 값만 바꾸는 외과적 텍스트 치환에 "앵커 유일성·기존값 일치·줄 수 불변" 단언을 걸어 적용했다.
  - **재현(수정 후)**: `docker compose restart api` 후 `curl -s localhost:8080/api/person/reccdFYIq50NyxNej/reliance` → 아브라함 전 단계에서 라벨과 `verseTextKo`가 일치한다(`순종하여 하란을 떠남` ↔ 창 12:4 `아브람이... 하란을 떠날 때에`, `바로의 집에 재앙 내려 사래를 건지심` ↔ 창 12:17 `바로와 그 집에 큰 재앙을 내리신지라`, `칼을 들어 이삭을 잡으려 순종함` ↔ 창 22:10). 수정 전 재현했던 3건 모두 더 이상 재현되지 않는다. `python3 -m backend.scripts.validate_god_reliance` → `OK — 인물 32명 · 항목 194개 · 위반 0`.
  - **남은 한계**: 재발 방지 게이트는 만들지 않았다. `backend/scripts/validate_god_reliance.py`에 '절 본문 ↔ 라벨 정합' 축을 넣으려면 의미 판정이 필요해 기계 불변식으로 환원되지 않는다(이 검증기의 공백이 결함이 게이트를 통과한 직접 원인이다). 후속 과제로 남긴다.

### 4. [HIGH] `data/god_reliance/saul.json:35-46` — 한 불순종 체인을 2건으로 쪼개 분모를 이중 계수, 화면 의존도가 6%p 왜곡된다

- **렌즈**: L3 데이터 의미 정합(통제 어휘·사건 단위) · 적대적 검증 **CONFIRMED** (2각도 만장일치, 심각도 합의)
- **증상**: 사울의 아말렉 명령 위반(삼상15:11 폐위 판결)과 그 판결의 직접 여파(삼상16:14 여호와의 영이 떠남)가 별개의 '독단-어긋남' 2건으로 저작돼, 하나의 신적 이니셔티브 체인이 분모에 두 번 계수된다. 그 결과 화면의 [[하나님 의존도]]가 실제와 다르게 표시된다. 덧붙여 `saul[6]`의 `trigger.label` `'불순종을 지속함'`은 인용한 절 본문에 없는 내용이다.
- **근거**: `data/bible/verses.json`의 `09016014`는 `'여호와의 신이 사울에게서 떠나고 여호와의 부리신 악신이 그를 번뇌케 한지라'`뿐으로, 새로운 불순종 **행위**를 서술하지 않는다 — 즉 이 항목은 앞선 판결의 결과이지 독립된 새 어긋남이 아니다. `data/god_reliance/AUTHORING.md`의 사건 단위 원칙은 하나의 명령/이니셔티브에서 나온 계기→행동→결과를 한 항목으로 묶도록 규정한다.
- **재현**: ① `curl -s http://localhost:8080/api/person/recjMT68aIzFLh6cQ/reliance` → `{"percent": 56, "sampleSize": 9, "modeCounts": {"부르심":3,"물음-응답":1,"독단-어긋남":4,"물음-침묵":1}}` — 현재 사울 의존도가 **56%**로 사용자에게 표시 중. ② `backend/app/routes/reliance.py:78`의 계수식으로 직접 계산: 분자 5 / 분모 9 = 56%. 두 항목을 원칙대로 1건으로 병합하면 분자 5 / 분모 8 = **62%**. 즉 저작 규칙 위반이 화면 수치 **6%p 왜곡**으로 직결된다.
- **검증 요지**: 두 검증자가 만장일치 CONFIRMED/HIGH. 양쪽 모두 `verses.json` 원문 대조로 `16:14`에 새 불순종 행위 서술이 없음을 확인했고, 병합 시 백분율 변화를 각각 독립 계산해 같은 값(56%→62%)에 도달했다. 한 검증자는 `grep "지속" data/god_reliance/*.json`으로 corpus 전역을 재검사해 이 패턴이 **사울 1인·1쌍에 국한**되고 전역 패턴은 아님을 확인했다(과대 일반화 방지).
- **수정 완료** (#3과 같은 승인 하에 적용): `saul[5]`와 `saul[6]`을 하나의 항목으로 병합하고, `[5]`가 두 단 모두에 달고 있던 잘못된 인용(삼상 15:11 — 실제로는 하나님의 후회 선언)을 각 단의 내용이 실제로 서술된 절로 교체했다. 결과 항목:
  `{ "mode": "독단-어긋남", "approxYear": -1042, "trigger": { "label": "아말렉 진멸 명령 어기고 좋은 것을 남겨 둠", "verse": "삼상 15:9" }, "outcome": { "label": "왕위 폐위를 선언받음", "verse": "삼상 15:23" } }`
  삼상 15:9 = `사울과 백성이 아각과 그 양과 소의 가장 좋은 것... 남기고`(= 남겨 둔 행위), 삼상 15:23 = `여호와께서도 왕을 버려 왕이 되지 못하게 하셨나이다`(= 폐위 선언). 근거 없는 `trigger.label` `'불순종을 지속함'`은 그 항목과 함께 사라졌다 — 라벨을 새로 지어내지 않고 이중 계수된 항목을 제거하는 쪽을 택했다.
  - **변경 파일**: `data/god_reliance/saul.json`(항목 9→8). 라벨은 하나도 새로 쓰지 않았다(신규 저작은 계획 Non-goal).
  - **재현(수정 후)**: `curl -s localhost:8080/api/person/recjMT68aIzFLh6cQ/reliance` → `{"percent": 62, "sampleSize": 8, "modeCounts": {"부르심":3,"물음-응답":1,"독단-어긋남":3,"물음-침묵":1}}`. 수정 전 56%/9건에서 **예측한 값 그대로** 62%/8건이 됐다(분자 5는 불변, 분모만 9→8). `validate_god_reliance` → 위반 0(항목 총계 195→194).

### 5. [HIGH] `backend/scripts/enrich_place_coords.py:53-62` — 좌표 교정이 한 번도 적용된 적이 없다 (시내산 ≈107km 어긋남)

- **렌즈**: L4 스크립트 재실행 안전성 · 적대적 검증 **CONFIRMED** (심각도는 검증자 간 HIGH/MEDIUM으로 갈려 작성자가 직접 실측해 HIGH로 재정)
- **증상**: `data/place_coords/places.json`에 저작한 좌표 교정 중 기존 Theographic 장소(`rec*` ID)에 해당하는 것은 **영구히 반영되지 않는다**. 스크립트를 몇 번 다시 돌려도 조용히 스킵된다(에러·경고 없이 요약의 '스킵' 카운트만 증가).
- **근거**: `rec*` 분기가 `MATCH (pl:Place {theographic_id: $id}) WHERE pl.latitude IS NULL SET pl.latitude = $lat, pl.longitude = $lng`로 **좌표가 비어 있을 때만** 갱신한다. 그런데 원본 임포트가 이미 모든 Place에 좌표를 채워 두므로 이 가드는 상시 거짓이다. docstring이 `'기존 값 보존'`이라는 동작 자체는 서술하지만, 그 결과로 **저작된 교정이 영영 반영되지 않는다**는 함의를 인지·수용한 ADR이나 주석은 어디에도 없다.
- **재현**: 읽기전용 cypher로 `places.json`의 `rec*` 11건을 조회해 저작값과 대조: `docker exec biblemap-neo4j-1 cypher-shell -u neo4j -p *** --format plain "MATCH (pl:Place) WHERE pl.theographic_id IN [...] RETURN pl.theographic_id, pl.latitude, pl.longitude"`. 관측: **11건 전부 latitude non-null**(가드 상시 거짓) 이고 **11건 전부 저작값과 불일치**. 대부분은 반올림 수준(Δ≤0.03°)이나 예외가 하나 크다 — **시내산 `rec6V51IWkgvAcnOU`: 저작(28.539, 33.975) vs DB(29.5, 34.0), Δ위도 0.961° ≈ 107km**. 저작값 28.539N/33.975E는 전통적 시내산 동정지(제벨 무사)이고 DB의 29.5N/34.0E는 상류 데이터의 성긴 근사다.
- **검증 요지**: 한 검증자는 CONFIRMED/HIGH, 다른 검증자는 CONFIRMED/MEDIUM으로 갈렸다. 결함의 존재(가드가 상시 거짓 → 교정 미적용)에는 양쪽이 일치했고, 갈린 지점은 **실제 피해 크기**였다. 작성자가 11건의 저작값 대 DB값을 직접 전수 대조해 판정했다: 반올림 수준 오차만이라면 MEDIUM이 맞지만, 시내산 한 건이 107km 어긋나 있어 사용자가 지도에서 **명백히 잘못된 위치**를 보게 되므로 HIGH로 재정한다. MEDIUM 판정 측은 이 divergence 크기를 측정하지 않았다.
- **수정 완료** (두 겹의 벽 — ① '기존 값 보존' 의미를 뒤집는 설계 갈림길 ② 반영에 필요한 Neo4j 쓰기 — 을 사용자에게 각각 올려 승인받은 뒤 적용): 저작 파일이 정본이라는 결정에 따라 `rec*` 분기의 `WHERE pl.latitude IS NULL` 가드를 제거하고 저작 좌표로 덮어쓰도록 바꿨다. 그 결정과 근거(가드가 상시 거짓이었다는 실측)를 docstring에 정본화했다.
  - **조용한 무의미화 방지**: 종전 카운터는 `스킵(기존 좌표 있음)`이라 11건 전부 스킵돼도 정상처럼 보였다. 이제 `좌표 갱신 / 이미 일치 / DB에 없음`으로 나눠 세고, **`DB에 없음`은 `assert`로 실패시킨다**(places.json의 id가 오타이거나 업스트림에서 사라지면 교정이 조용히 유실되므로).
  - **변경 파일**: `backend/scripts/enrich_place_coords.py`(docstring + `rec*` 분기 쿼리 + 카운터/요약). `data/place_coords/places.json`은 무변경 — 저작값이 이미 정답이었고 반영만 막혀 있었다.
  - **재현(수정 후)**: 로더 실행 → `완료 — 신규: 86개  좌표 갱신: 11개  이미 일치: 0개  DB에 없음: 0개`(교정이 처음으로 실제 적용됨). 읽기전용 cypher로 11건 전수 재대조 → **일치 11 · 불일치 0**, 시내산 DB 좌표가 `29.5/34.0` → **`28.539/33.975`**(저작값 = 전통적 동정지)로 이동. 사용자 도달 경로까지 확인: 지도 좌표를 Neo4j에서 읽는 `backend/app/routes/journey.py:30` 경유로 `curl -s localhost:8080/api/person/recjNRR60PAuFtjha/journey` → 시내산 정차지 `lat=28.539 lng=33.975`.
  - **멱등성 확인**: 곧바로 재실행 → `좌표 갱신: 0개  이미 일치: 11개` — 두 번 돌려도 같은 상태에 머문다(L4 렌즈가 보는 재실행 안전성 자체를 만족).
  - **되돌리기**: 변경 전 Place 좌표 252건을 `.forge/scratch/place_coords_pre_task285.json`에 백업해 뒀다.
  - **남은 한계**: 이 로더는 여전히 `deploy.sh`에 배선돼 있지 않아 수동 실행이 필요하다(의도된 기존 결정 — ADR `260801-195022`, 이번 범위 밖). 즉 DB를 새로 적재하면 다시 한 번 돌려야 한다. 재발 게이트는 남기지 않았다 — 이 축의 오라클은 라이브 DB뿐이라 파일 검증기로 환원되지 않고, 게이트를 라이브 DB에 결합시키는 것은 CONCERNS가 이미 별도 위험으로 지목한 방향이다. 대신 위의 `assert`와 카운터 분리를 스크립트 안에 남겼다.

### 6. [MEDIUM] `frontend/src/App.jsx:471-486` — 모바일 하단 시트가 관계·의존 탭에서 닫히지 않아 콘텐츠를 덮는다

- **렌즈**: L2 프론트 런타임 상태(모바일↔데스크톱 분기) · 적대적 검증 **CONFIRMED**
- **증상**: 타임라인 등에서 다른 노드를 클릭해 연 모바일 하단 시트가, 관계·의존 탭으로 전환해도 닫히지 않고 화면의 75%를 덮어 관계 카드·의존 게이지를 가린다. 데스크톱은 같은 상황에서 정상적으로 억제된다.
- **근거**: 모바일 분기(478행)는 `transform: sheetOpen ? 'translateY(0)' : 'translateY(100%)'`로 `exploreView`와 무관하게 판정하는 반면, 데스크톱 분기(485행)는 `exploreView !== 'relations' && exploreView !== 'reliance'` 조건을 함께 본다. 파생값 `sheetOpen`(`frontend/src/useStageNavigation.js:408`)이 `exploreView`를 보지 않으므로 모바일이 뷰별 억제를 상속받지 못한다.
- **재현**: Playwright 모바일 390×844 → `#/person/abraham/timeline` → 사건 노드 클릭(시트 오픈) → '관계' 탭 클릭. 관측: `sheet-open=true`, `transform=matrix(1,0,0,1,0,0)`(=translateY(0)), 시트 bbox `{x:0, y:211, width:390, height:633}` — '아브라함의 관계' 헤더 아래 목록 대부분이 가려짐을 스크린샷으로 확인. 데스크톱 대조군은 정상.
- **검증 요지**: 라이브 Playwright 실측으로 재현. 발굴자 인용 중 `frontend/src/useStageNavigation.js:346`은 **틀린 줄이었고**(346행 부근은 무관한 `handleTopicsBack`), 실제 소비되는 `sheetOpen` 정의는 398행(수정 후 현재 408행)임을 검증자가 정정했다. `frontend/src/App.jsx:471-486`은 정확했다. 이 항목은 `.forge/bug-report-2.md`가 '위치 미특정·후속 사이클에서 특정 필요'로 명시 이월해 둔 건으로, 이번에 파일:줄 근본원인을 특정해 확정 승격했다.

### 7. [MEDIUM] `data/character_traits/people.json:512-518`, `data/character_traits/people.json:619-624` — 성품 앵커절이 실제 성품 장면이 아니다

- **렌즈**: L3 데이터 의미 정합(통제 어휘 경계) · 적대적 검증 **CONFIRMED**
- **증상**: 안드레 '겸손'(요1:40)·야고보 '담대함'(막3:17)의 앵커 절이 그 성품이 드러나는 장면이 아니라 단순 신원 소개·별명 부여 서술이다. `data/character_traits/AUTHORING.md`가 "앵커 절의 장면을 빌려 성품을 서술"하도록 규정한 것을 벗어난다.
- **근거**: 요1:40(`43001040`) 원문은 `'요한의 말을 듣고 예수를 좇는 두 사람 중에 하나는 시몬 베드로의 형제 안드레라'`로 순수 신원 소개인데, description은 `'복음서 전통에서 항상 베드로의 형제로 소개될 만큼 주목받지 않으면서도 묵묵히 섬겼다'`로 절 밖 '복음서 전통' 일반화를 끌어온다. 막3:17(`41003017`)도 보아너게 별명 부여 서술뿐이다.
- **재현**: `python3 -c "import json; d=json.load(open('data/character_traits/people.json')); print(d['recpvMKljbEMuiK9e']['traits'][2]); print(d['rechkAyIwugqcLaaY']['traits'][0])"`로 두 항목을 출력하고, `data/bible/verses.json`의 `43001040`·`41003017` 원문과 대조.
- **검증 요지**: 두 사례 모두 파일을 직접 열어 재현했고 인용 원문이 주장과 정확히 일치했다. `data/character_traits/AUTHORING.md`를 직접 열람해 "칭호 나열 금지"·"앵커 절의 장면을 빌려 서술" 규칙을 확인했으며, `backend/scripts/validate_traits.py`를 읽어 검증기가 라벨·개수·형식만 보고 내용은 보지 않음을 확인했다(게이트 통과 이유).

### 8. [MEDIUM] `backend/scripts/apply_event_dedupe.py:31-33` — 1~2건 삭제가 전면 재포맷 diff에 파묻힌다

- **렌즈**: L4 스크립트 재실행 안전성 · 적대적 검증 **CONFIRMED**
- **증상**: 중복 사건을 1~2건 지우는 실질 변경이, 파일 전체 서식이 다시 펼쳐진 대량 diff에 묻혀 리뷰로 실제 변경을 분간하기 어렵다.
- **근거**: `save_json()`이 입력 서식과 무관하게 무조건 `json.dump(..., indent=2)`로 재직렬화한다. 원본 `data/authored_events/events.json`은 `mappedBookIds`·`participants` 같은 배열을 한 줄로 압축해 두었는데, `indent=2` 재전개가 이를 전부 다중행으로 펼친다. `backend/scripts/apply_event_dedupe.py:126-130`에서 원소가 1건이라도 삭제되면 이 `save_json`이 호출된다.
- **재현**: `python3`로 원본을 읽어 `json.dumps(data, ensure_ascii=False, indent=2)` 결과와 줄 수를 비교 — 관측: `orig lines: 86 → new lines: 122, diff lines: 119`. 내용은 byte-identical(순수 서식 재전개)인데 119줄이 diff로 잡힌다.
- **검증 요지**: 인메모리 재직렬화 비교로 재현(파일 미변경). `.forge/codebase/CONCERNS.md` #7이 같은 인용 라인을 언급하지만 그 맥락은 "`data/`를 되쓴다는 사실 + `git reset --hard` 경합"이라는 배포 절차 이슈로, `indent=2` 재직렬화가 압축 배열 서식과 어긋나 86→122줄로 부푼다는 이번 메커니즘과는 다르다 — 재나열 아님.

### 9. [MEDIUM] `deploy.sh:10-15` — 강제종료 1회로 이후 모든 자동배포가 정지한다

- **렌즈**: L5 배포·운영 · 적대적 검증 **CONFIRMED** (심각도는 검증자 간 HIGH/LOW로 갈려 작성자가 MEDIUM으로 재정)
- **증상**: 배포 중 프로세스가 SIGKILL·전원손실 등으로 강제종료되면 락 파일이 남고, 이후 모든 자동배포가 `'배포 이미 진행 중 (lock 존재), 건너뜀.'`과 함께 `exit 1`로 끝난다. 실제로는 아무것도 진행 중이 아니므로 메시지도 오도한다. 수동 `rm` 전까지 복구되지 않는다.
- **근거**: `deploy.sh:10-15`가 락의 **존재 여부만** 검사하고 PID·mtime을 기록·검증하지 않는다. 정리 수단인 `trap 'rm -f "$LOCK"' EXIT`은 SIGKILL·전원손실에는 **원리적으로 발동하지 않는다**(POSIX 셸의 성질이지 구현 우연이 아니다).
- **재현**: 격리 harness로 동일 로직을 재현해 락 잔존과 이후 실행의 즉시 `exit 1`(무배포)을 직접 관측했다. 실제 `deploy.sh`는 실행하지 않았다(안전 벽).
- **검증 요지**: 코드 사실 관계에는 두 검증자가 일치했고, 갈린 지점은 심각도였다. HIGH 측은 '영구 배포 정지'를, LOW 측은 이 실패모드가 사용자 org 정본 런북에 이미 알려진 현상+수동 복구로 명문화돼 있음을 들었다. 작성자가 가시성을 직접 확인해 MEDIUM으로 재정한다: `.github/workflows/deploy.yml`이 `bash deploy.sh`를 `continue-on-error` 없이 호출하므로 `exit 1`은 **CI 잡을 빨갛게 실패시킨다** — 즉 이 프로젝트가 과거 겪은 '무음 미배포'와 달리 스스로 드러나며, 복구도 `rm` 한 줄이다. 그렇다고 정상 동작은 아니므로 refuted도 아니다.

### 10. [LOW] `backend/app/routes/reliance.py:1-3`, `backend/app/routes/reliance.py:21` — docstring·주석이 ADR-0023 개정 이전 정의를 서술한다

- **렌즈**: L1 백엔드 라우트 계약 · 적대적 검증 **CONFIRMED**
- **증상**: 파일 docstring과 주석이 `'부르심은 obeyed=true만 분자'`라고 단정하지만, 실제 `_percent()`는 `obeyed` 또는 `covenant`면 분자에 넣는다. 코드가 아니라 **주석이 틀렸다** — 주석만 보고 '고치면' ADR이 요구하는 정상 동작이 깨진다.
- **근거**: `backend/app/routes/reliance.py:78`이 `e["mode"] == "부르심" and (e.get("obeyed") or e.get("covenant"))`로 판정하며, 이는 `.forge/adr/0023-god-reliance-metric-definition.md`의 2026-07-15 개정(언약형도 분자 산입)과 정확히 일치한다. 어긋난 것은 1-3행 docstring과 21행 주석뿐이다.
- **재현**: `data/god_reliance/*.json` 전량 스캔에서 `mode=='부르심' & covenant & !obeyed` 조합이 **25건** 실재해 차이가 이론적이지 않음을 확인. 야곱으로 계산 대조: 실제 코드식 7/8=88%, 주석 서술대로면 5/8=62%. 라이브 `curl .../person/recsU2ZSdzBvDqzgI/reliance` → `percent: 88` — 서버는 코드(=ADR)대로 동작하고 주석만 stale임이 확정.
- **검증 요지**: ADR 원문을 직접 열어 코드가 개정을 준수함을 확인했으므로 **코드는 고치지 않는 것이 맞다**(고치면 회귀). `.forge/codebase/CONCERNS.md`·1·2차 리포트에 `reliance` 관련 다른 항목은 있으나 이 stale 주석 건은 없어 신규.

### 11. [LOW] `data/character_traits/people.json:99` — 베드로 '통회' description이 앵커 절 범위를 넘는다

- **렌즈**: L3 데이터 의미 정합 · 적대적 검증 **CONFIRMED**
- **증상**: 베드로 '통회'(눅22:62) 항목의 description이 앵커 절의 장면(통곡)을 넘어 그 절에 없는 사후 내러티브(부활 후 회복, '교회의 기둥')까지 서술한다.
- **근거**: 해당 trait 블록의 `description`은 `'예수를 세 번 부인한 뒤 통렬히 울었으나, 부활하신 주께 회복되어 교회의 기둥이 되었다.'`인데 `verse_textKo`는 `'밖에 나가서 심히 통곡하니라'`뿐이다. `data/character_traits/AUTHORING.md`가 description을 앵커 절 장면에 한정하고 칭호 나열을 금한다.
- **재현**: `python3 -c "import json; d=json.load(open('data/character_traits/people.json',encoding='utf-8')); print(d['recX9MMADoVI2CSP1']['traits'][2])"`. 추가로 읽기전용 cypher로 `Person.theographic_id='recX9MMADoVI2CSP1'`의 `p.traits`에 동일 항목이 이미 주입·서빙 중임을 확인.
- **검증 요지**: 같은 라벨('통회')의 다른 3개 인물 항목은 전부 앵커 절 범위를 지켜, 이 건이 규칙의 예외적 일탈임을 대조로 확인했다. 발굴자 인용 98행은 `verse_ref` 필드였고 `description`은 99행이라 검증자가 정정했다(이 리포트는 정정된 99행을 쓴다).

### 12. [LOW] `nginx/nginx.conf:35-37` — 무해시 정적 파일에도 1년 immutable 캐시가 걸린다

- **렌즈**: L5 배포·운영 · 적대적 검증 **CONFIRMED**
- **증상**: 콘텐츠 해시가 붙지 않는 정적 파일(웹폰트, favicon)도 1년 immutable로 캐시돼, 내용을 교체해도 이미 받아간 브라우저는 최대 1년간 갱신되지 않는다.
- **근거**: `location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff2?)$` 블록이 `add_header Cache-Control "public, max-age=31536000, immutable"`을 확장자만 보고 적용한다. Vite 산출물은 파일명에 콘텐츠 해시가 있어 안전하지만 `public/`의 무해시 자산은 그렇지 않다. `frontend/src/index.css:9`의 웹폰트 참조에는 버전 쿼리가 없다(`frontend/index.html:5`의 favicon만 `?v=2` 수동 버전이 붙어 부분 완화).
- **재현**: `curl -sI http://localhost:8080/favicon.svg`와 `curl -sI http://localhost:8080/fonts/im-fell-english-latin.woff2` → 둘 다 `Cache-Control: public, max-age=31536000, immutable`.
- **검증 요지**: 라이브 헤더로 확인. `.forge/codebase/CONCERNS.md`·1·2차 리포트를 `immutable`·`favicon`·`woff` 3개 키워드로 grep해 전부 0건 매치 — 두 리포트는 gzip 활성화·바인드 마운트 재기동만 다루므로 신규.

---

## 렌즈별 커버리지

배포 게이트가 보지 않는 5축을 각각 2각도(총 10 finder)로 발굴했다. **어느 축도 무음 0건이 아니다** — 소득이 없는 축도 "무엇을 봤는지"를 남기게 강제했고, 총 59건의 `lookedAtButClean` 기록이 나왔다.

- **L1 백엔드 라우트 계약·견고성** (2각도: 응답계약 / 입력견고성 · 깨끗 기록 18건) — confirmed 1건(#10). `backend/app/routes/`의 15개 라우트를 정독하고 의심 지점마다 라이브 `curl`로 계약과 대조했으며, 경로·쿼리 파라미터에 무효 id·빈 문자열·초장문·유니코드를 넣어 직접 때렸다. 500·스택트레이스 유출은 나오지 않았다. 이 축의 후보 2건(C1 단어 count/total, C3 quotations 캐시 축출)은 적대적 검증에서 모두 기각됐다(부록 참조).
- **L2 프론트 런타임 상태** (2각도: 경쟁상태 정독 / 모바일↔데스크톱 Playwright 실측 · 깨끗 기록 6건) — confirmed 2건(#1 HIGH, #6). 2차 헌트에서 이 클래스로 2건이 확정된 이력이 있어 같은 결함 클래스를 다른 파일에서 추적했다. 과거 회고가 못 박은 측정 규칙(상속 계산 스타일로 조준 금지, 0건은 10초 폴링 후 실패 판정, 모바일은 클릭마다 시트 닫기, 2.5초 이상 대기, URL마다 새 컨텍스트)을 그대로 적용했다.
- **L3 데이터 의미 정합** (2각도: 구절 근거 / 통제 어휘 경계, 둘 다 `scripture-reviewer` 역할 · 깨끗 기록 11건) — confirmed 4건(#3 HIGH, #4 HIGH, #7, #11). 기계 검증이 형식·키만 보는 축이라 소득이 가장 컸다. `god_reliance` 32개 파일의 verse 인용 **395개 전수**를 `data/bible/verses.json`으로 해석·대조했고, `character_traits`는 `data/character_traits/AUTHORING.md` 규칙 대비 표본 검토했다.
- **L4 스크립트 재실행 안전성** (2각도: 로더 멱등성 / inject·생성 스크립트 정합 · 깨끗 기록 13건) — confirmed 2건(#5 HIGH, #8). **로더·inject·apply_* 를 한 번도 실행하지 않고** 코드 경로 정독과 읽기전용 cypher 관측만으로 판정했다(실행은 Neo4j·`data/`를 바꾸므로 안전 벽). 검증기 자체의 구멍도 함께 봤고, 그 결과 나온 후보 1건(C12)은 정상 생성 경로에서 도달 불가로 기각됐다.
- **L5 배포·운영** (2각도: 캐시 무효화 / 배포 파이프라인 · 깨끗 기록 11건) — confirmed 3건(#2 HIGH, #9, #12). `deploy.sh`·워크플로·compose·nginx를 정독하고 `bash -n`·`docker compose config`·`--dry-run`·`curl -I` 같은 무변경 관측만 사용했다. `deploy.sh`는 실행하지 않았다.

## CONCERNS.md 대비 신규성

confirmed 12건은 `.forge/codebase/CONCERNS.md` 기재 항목의 재나열이 아니다.

- **CONCERNS 미기재 신규 발견** — #1(popstate state:null 오판정) · #2(1시간 캐시가 표준 데이터수정 경로를 무력화) · #3(god_reliance 인용 절 불일치 18건) · #4(사울 사건 이중 계수) · #7(성품 앵커절이 성품 장면 아님) · #10(reliance docstring이 ADR 개정 이전 정의) · #11(베드로 통회 description 범위 초과) · #12(무해시 정적 파일에 1년 immutable). 각 절의 «검증 요지»에 grep 대조 결과를 기록했다.
- **CONCERNS의 전제를 정면으로 반증** — #1은 CONCERNS가 'SPA는 프래그먼트 내비게이션에서 `hashchange`만 발생시킨다(수동적 무반응)'고 전제한 것을, popstate가 실제로 발화해 핸들러가 **능동적으로 상태를 파괴한다**는 반대 방향 메커니즘으로 반증했다.
- **일반론 → 실제 도달 확정 승격** — #5는 CONCERNS가 `enrich_place_coords.py`를 '배포 파이프라인에 미배선'이라는 절차 문제로만 적어 둔 것과 달리, 스크립트를 제때 돌려도 가드 때문에 교정이 **원리적으로 반영되지 않음**을 11건 전수 대조로 확정했다.
- **같은 인용 라인, 다른 메커니즘** — #8은 CONCERNS #7이 언급한 `apply_event_dedupe.py`의 같은 줄을 가리키지만, 그쪽은 '`data/`를 되쓴다 + 하드리셋 경합'이고 이번은 '`indent=2` 재직렬화가 압축 배열 서식과 어긋나 86→122줄로 부푼다'는 별개 메커니즘이다.
- **미확정 이월 → 파일:줄 확정** — #6은 `.forge/bug-report-2.md`가 '위치 미특정, 후속 사이클에서 특정 필요'로 명시 이월해 둔 항목을 `frontend/src/App.jsx:478` 대 485행의 분기 비대칭으로 근본원인을 특정하고 라이브 재현해 승격한 것이다.
- **기존 org 런북에 알려진 현상** — #9는 사용자 org 정본 런북에 수동 복구 절차가 적혀 있으나, 이 저장소의 CONCERNS·1·2차 리포트에는 기재된 적이 없어 이 저장소 기준으로는 신규다. 이 사실을 심각도 판단(MEDIUM)에 반영했다.

## 부록 — 적대적 검증에서 기각된 항목 (REFUTED 5건)

투명성 기록. 발굴 단계에서 후보로 올라왔으나 적대적 검증에서 무너진 것들이다.

1. **C1 — 단어 화면의 `count`와 `total`이 다른 산식이라 숫자가 어긋난다** (`backend/app/routes/words.py:11-29`, HIGH로 추정됐음). 검증 2각도가 갈렸고 작성자가 재정해 **기각**. `count`는 형태소 등장 **횟수**, `total`은 그 단어를 포함하는 **구절 수**로 정의부터 다른 두 통계량이며, 한 구절에 단어가 여러 번 나오면 `total < count`가 수학적으로 필연이다. 직접 계산으로 distinct-verse-count = 5906이 API `total`과 **정확히 일치**하고 substring raw occurrence 7017이 kiwi `count` 7011에 근접함을 확인했다. 라벨도 `'7011회'`와 `'5906구절'`로 단위가 다르게 붙어 있고, `frontend/src/VerseLayer.jsx:93`·`frontend/src/VerseLayer.jsx:146`이 `position:fixed; inset:0` 스크림이라 클릭 시 워드클라우드가 완전히 가려져 **두 숫자가 같은 화면에 동시에 보이지도 않는다**(CONFIRMED 측 주장의 사실 오류). 두 지표가 다른 개념임을 UI가 더 명시할 여지는 있으나 결함은 아니다.
2. **C3 — `/book/{id}/quotations`의 `lru_cache(maxsize=66)` 헤드룸 0으로 무효 키 1건이 유효 캐시를 축출** (`backend/app/routes/books.py:106`). 메커니즘 자체는 프로세스 내 직접 호출로 재현됐다(66개로 채운 뒤 무효 키 1회 → 가장 오래된 유효 항목 miss). 그러나 `.forge/codebase/CONCERNS.md` §5가 이미 파일·줄·`maxsize`·키·메커니즘·심각도(낮음)까지 구체적으로 기재하고 있어 **재나열**로 기각. 후보가 더한 것은 '유효 키 66개 = maxsize라 헤드룸이 정확히 0'이라는 정량화뿐인데, 이는 축출에 필요한 호출 횟수의 정도차일 뿐 새 도달 경로를 열지 않는다.
3. **C5 — `useExploreJourney`의 리셋 브랜치에 cancelled 가드가 없어 새 선택 상태를 늦게 덮어쓴다** (`frontend/src/useExploreJourney.js:38-53`). **기각** — 이벤트 루프 순서상 발생 불가. 리셋은 커밋 A의 effect 동기 실행 중 스케줄되는 마이크로태스크라 다음 매크로태스크(React passive effect flush)보다 **항상 먼저** 드레인되고, 뒤이은 선택의 `apiGet`은 실제 네트워크 `fetch`라 그 `.then()`은 훨씬 뒤에 온다. 순서가 `리셋 < 다음 effect < fetch.then`으로 고정되어 역전이 원천적으로 불가능하다. StrictMode 이중 호출(멱등)과 언마운트 경합(App 레벨 훅이라 재마운트 없음)도 함께 배제했다.
4. **C12 — `validate_event_verses.py`가 `bookId`↔`bookOrder` 대응 자체는 검증하지 않는다** (`backend/scripts/validate_event_verses.py:41-58`). 검증기가 블록의 `bookOrder`만 신뢰해 기대 verseID를 재계산하고 `bookId`와의 대응은 보지 않는다는 **코드 사실은 맞다**. 그러나 생성기가 `bookId`와 `bookOrder`를 항상 같은 매핑에서 함께 파생시키므로 정상 생성 경로에서 어긋난 조합이 만들어질 수 없어, 발현이 필연도 아니고 재현도 불가하다 → 판정 규칙상 **기각**. 다만 '검증기가 자기일관된 오류를 통과시킬 수 있다'는 게이트 공백 자체는 사실이므로 여기 남긴다.
5. **C16 — `deploy.sh`가 neo4j 서비스를 절대 재조정하지 않아 compose/.env의 neo4j 변경이 영구 무시된다** (`deploy.sh:82-87`). **기각** — 작성자가 직접 실측해 반증했다. `deploy.sh`가 neo4j를 이름으로 부르지 않는 것은 사실이나, api가 neo4j를 `depends_on` 하므로 `docker compose up -d api`가 의존 서비스를 재조정 대상에 포함한다. `NEO4J_PASSWORD`를 바꿔 `docker compose -p biblemap up -d --dry-run api`를 돌리면 계획에 `Container biblemap-neo4j-1 Recreate`가 찍힌다(무변경 dry-run으로 확인). 즉 neo4j 설정 변경은 자동배포 경로에서 실제로 반영된다.

**검증자 판정 흔들림에 대한 정직한 기록**: 재개 실행 과정에서 일부 후보가 두 번 판정됐고 그중 3건(C11·C12·C16)이 서로 다른 결과를 냈다. 이는 단일 검증자 판정이 결정적이지 않음을 보여주므로, 흔들린 3건은 전부 작성자가 직접 실측해 재정했다(#5는 11건 전수 좌표 대조, C12는 생성기 경로 추적, C16은 compose dry-run). C1·C9(HIGH 2각도 중 갈린 건 포함)도 같은 방식으로 처리했다.

## 자체 검증

이 리포트는 다음 기계 검증을 통과한다(`.forge/scratch/verify_bug_report_3.py` — **주행 시작 전에** 작성해 2차 리포트로 대조 검증한 검증기다. 작성자가 자기 답안을 채점하지 못하게 하려는 것이므로 주행 중 수정하지 않았다).

- 요약표 행수 == `### ` 상세 절 수 == confirmed 건수(12)이고 번호가 1..12 연속이다.
- 각 상세 절이 «렌즈»·«증상»·«근거»·«재현»·«검증 요지»를 모두 갖고 CONFIRMED 판정을 명시한다.
- 본문의 모든 백틱 `파일:줄` 인용에 대해 파일 실재와 줄 범위 유효를 스크립트로 확인했다.
- `## 렌즈별 커버리지`가 L1~L5 전부를, `## CONCERNS.md 대비 신규성`이 confirmed 전건(#1~#12)을 커버한다.
- confirmed HIGH **5건 전건이 `수정 완료`**이고, 각 건이 '수정 후' 재현 실측 기록을 갖는다.

추가 실측(리포트 외부):

- `CHECK_STRICT=1 bash scripts/check.sh` → **34항목 전항목 PASS**(스킵 0건). 주행 시작 시점 기준선은 32항목 전항목 PASS였고, #2의 재발 게이트(`validate_api_cache_headers` + 대조군)를 배선해 34항목이 됐다. 즉 이 수정들은 게이트 회귀를 만들지 않았고 커버리지를 2항목 늘렸다.
- 데이터 수정(#3·#4) 후 `python3 -m backend.scripts.validate_god_reliance` → 위반 0(인물 32명·항목 194개), `docker compose restart api`로 반영해 라이브 응답까지 확인했다. `git diff --stat data/god_reliance/` = 26 files changed, 81 insertions(+), 87 deletions(-) — 교체된 79개 `verse` 값 + 병합으로 사라진 항목뿐이고 **서식 재포맷은 0줄**이다.
- #1의 결함 클래스에는 게이트를 새로 남기지 않았다. 그 클래스("무타깃/상태 판정이 정본 밖에서 갈린다")는 이미 `backend/scripts/validate_intro_entry_route.py`가 불변식으로 지키고 있고, 이번 수정이 정본 술어 `isNoTarget`을 그대로 쓰도록 짜였기 때문이다 — 중복 게이트는 남기지 않는다.
- `cd frontend && npm run build` → exit 0.
- 인용 정확성에 대한 주의: 2차 리포트 회고가 "수정 후 되적기가 작성자의 자체검증을 빠져나간다"(수정 문단이 나중에 붙으며 무효 인용을 새로 들여옴)를 남겼다. 이번에는 **수정 완료 문단까지 모두 쓴 뒤에** 위 검증을 돌려 그 구멍을 닫았다.
- 인용 줄번호 기준: #1의 수정 완료 관련 인용은 **수정 후** 파일 기준이다(popstate 핸들러가 10줄 늘어 `useStageNavigation.js`의 이후 줄번호가 밀렸다 — `sheetOpen` 정의도 398→408행). 나머지 인용은 HEAD `e478795`와 수정 후가 동일하다.
