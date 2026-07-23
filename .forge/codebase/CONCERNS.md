---
last_mapped_commit: 70f5fc64daa7b3c71f2773a4357ad68bba9ae7a5
mapped: 2026-07-24
---

# CONCERNS

현재 코드베이스에서 확인된 기술 부채·버그 위험·보안·성능·취약 지점 목록. 각 항목은 HEAD(`70f5fc6`) + **미커밋 워킹트리** 기준으로 실제 파일·라인 재추적, ESLint(`npx eslint src`) 재실행, 데이터 검증 스크립트(신규 4종 포함 11종) 재실행, 캡처된 스크린샷(`.forge/reports/`) 육안 확인으로 검증했다.

**중요 — 이 스냅샷은 미커밋 워킹트리다**: HEAD(`70f5fc6`)는 인트로 시네마틱 필름 커밋이고, 이 문서가 대상으로 하는 **5개 오버레이 기반 콘텐츠 기능(언약·메시아 예언·비유/기적·주제 성구·통계)은 전부 아직 커밋되지 않은 작업 트리 변경**이다. 신규 라우트 `backend/app/routes/stats.py`, 신규 뷰 `frontend/src/StatsView.jsx`·`frontend/src/TopicalVersesView.jsx`, 신규 데이터 디렉터리 `data/covenants/`·`data/messianic_prophecies/`·`data/topical_verses/`·`data/jesus_parables_miracles/`, 신규 검증 스크립트 4종은 모두 `git status`상 **untracked**이고, `backend/app/main.py`·`overlays.py`·`routes/events.py`·다수 프론트 파일은 **modified(미커밋)**다. 데이터 디렉터리가 커밋되기 전에는 배포(볼륨 마운트)가 이 파일들을 보지 못한다 — 아래 Deployment 절 참조.

이번 세션 요약(HEAD 이후 워킹트리): 5개 기능 추가 — 언약(`/covenants`, task#247)·메시아 예언↔성취(`/messianic-prophecies`, task#246)·예수 비유/기적 색인(`/parables-miracles`, task#249)·주제별 성구(`/topical-verses`, task#250)·그래프 집계 통계(`/stats`, task#248). 모두 `overlays._load()` 런타임 파일 읽기 기반(비유/기적은 `place_coords` 오버레이로 좌표 해석)이고, 통계는 기존 그래프 노드 집계다. 신규 저작 데이터의 Neo4j 적재 단계는 없다.

---

## 직전 매핑 지적 사항 사후 검증

- **언약 리본 `marginLeft:auto` 클리핑 버그 — 이번 세션에 수정 완료(FIXED).** `frontend/src/TimelineView.jsx:254-255` 주석이 수정 경위를 명시: 언약 리본의 표징 span을 `marginLeft:auto`로 우측 끝까지 밀면 데스크톱 상세 시트(`SidePanel`, `zIndex:10`)가 덮는 우측 360px 폭 안에 들어가 완전히 안 보이던 버그를, 표징을 이름·연도 바로 옆에 이어 배치(`:256`)하도록 고쳤다. 동일 패턴을 비유/기적 섹션(`renderPmSection`, `:296-297`)에도 선제 적용했다. (task#249 비유/기적 작업 중 발견 → 같이 수정.)
- **가족 이웃 무방향 매치 오라벨(`/node/{id}/neighbors/grouped`) — 잔존.** `backend/app/routes/nodes.py`는 이번 세션 워킹트리 변경 대상이 아니다(diff 없음). `get_node_neighbors_grouped`(`nodes.py:116-147`)는 여전히 `-[r]-(m)` 무방향 매치·정규화/디듀프 없음. 유일 소비처 `frontend/src/mapRingController.js:112`가 응답의 Event만 읽어 현재 UI 영향은 없음.
- **`generate_approx_book_verses.py` 죽은 ID 재매핑 — 이전 HEAD에서 해소, 근본 원인은 잔존.** 이 스크립트/`VERSE_MAP`은 이번 세션 미변경. 아래 Data Pipeline Footguns 참조.
- **ESLint 0 유지 목표 붕괴 — 잔존(동일 셋, 라인만 밀림).** 아래 Test Coverage Gaps 참조. 이번 신규 뷰(`StatsView.jsx`·`TopicalVersesView.jsx`)는 위반 0건 추가.
- **Person `birthYear`/`deathYear` Ussher 드리프트 5건 — 데이터 불변으로 잔존.** 아래 Data Pipeline Footguns 참조.

---

## Known Bugs (신규 확정)

### 모바일 MapView가 성지에 프레이밍하지 못하고 세계 축소 뷰로 렌더 (선재 버그, 육안 확인)

**증상 확인**: `.forge/reports/parables-miracles-map-mobile-plain.png`(모바일 ~390px, 예수의 여정 24정차지) — 지도가 성지(이스라엘/팔레스타인)가 아니라 **적도 아프리카(Congo·Kinshasa·Tanzania·Seychelles가 하단에 보이는) 세계 축소 뷰**로 렌더된다. 상단 절반가량은 타일 밖 배경(어두움). 동일 인물의 데스크톱 캡처(`.forge/reports/pm-map-zoomed-out.png`, 아브라함)는 성지에 정확히 프레이밍된다 — **모바일 전용 회귀**. 비유/기적 레이어와 무관(여정 프레이밍 경로의 문제이므로 PM 토글을 켜지 않아도 재현).

**코드 근거(`frontend/src/MapView.jsx`)**:
- 마운트 시 카메라는 `center: [35.22, 31.78], zoom: 5`(`:39-40`) — 이것 자체는 성지다. 즉 스크린샷의 아프리카 세계 뷰는 **초기 카메라가 아니라 `fitBounds`가 최소 줌 근처로 클램프된 결과**다(초기 카메라라면 성지 zoom 5가 보여야 함).
- 성지로의 초기 `fitBounds`가 없다. 카메라 프레이밍은 오직 (a) places effect의 `map.fitBounds(...)`(`:150`·`:157`), (b) journeyStops effect의 `map.fitBounds(bounds, ...)`(`:194`)에서만 일어난다. 투어/인물 여정이 있을 때 (b) 경로가 프레이밍을 담당한다.
- 모바일 `fitBounds` 패딩이 과대하다: `journeyStops` effect(`:191-194`)에서 `sheet = round(innerHeight * JOURNEY_SHEET_VH/100)`, 패딩 `{ top: 70, bottom: sheet + 20, left/right: 40 }`. `JOURNEY_SHEET_VH = 42`(`frontend/src/constants.js:3`)라 844px 뷰포트에서 `sheet ≈ 354px` → 세로 패딩 합 `≈ 444px`. `fitBounds` 시점에 지도 컨테이너의 실효 높이가 이 패딩보다 작으면(레이아웃 미확정/숨김 상태에서 생성된 캔버스 크기), maplibre는 bounds를 남은 영역에 맞출 수 없어 **줌을 최소값 근처로 클램프**한다(스크린샷의 아프리카 세계 뷰).
- `resize()` 재프레이밍 부재로 회복되지 않는다: `isVisible` effect(`:257-259`)는 `if (isVisible && mapRef.current) …resize()` 조건인데 `mapRef.current`는 `map.on('load')` 핸들러(`:66`)에서야 설정된다. 초기 모바일 진입에서 `isVisible`은 마운트부터 true라 그 뒤 값 변화가 없고, load 후 effect가 재실행되지 않아 **최초 프레이밍에 대해 `resize()`가 사실상 호출되지 않는다.** 컨테이너가 뒤늦게 커져도 카메라를 다시 맞추는 경로가 없다.

**책임 소재**: 이 프레이밍/리사이즈 로직은 이번 세션 미변경(diff는 PM 소스·토글 effect `:30-34`·`:242-255`만 추가, 카메라 미접촉)이라 **선재 버그**다. 데스크톱은 패딩이 `80`(작음)이고 컨테이너가 처음부터 실치수라 재현되지 않는다.

---

## New Features — Overlay/Deploy Reproducibility (신규 검토)

**5개 신규 기능은 로더 배선 없이 배포 재현 가능 — 단, 데이터가 아직 미커밋.**

- **런타임 파일 읽기만, Neo4j 적재 불필요(확인)**: 언약·메시아 예언·주제 성구·비유/기적 4종은 전부 `backend/app/overlays.py`의 `_load()`(`:34-43`, 순수 파일 open/parse) 경유다 — `covenants()`(`overlays.py:101`)·`messianic_prophecies()`(`:95`)·`topical_verses()`(`:121`)·`parables_miracles()`(`:107`). 라우트(`backend/app/routes/events.py:119`·`:134`·`:162`·`:177`)는 오버레이 + `bible_verses()` 절 본문 합성만 하고 그래프에 새 노드를 심지 않는다. 통계(`backend/app/routes/stats.py`)는 기존 `Person/Event/Place/Book` 노드 집계라 역시 신규 적재가 없다. → **`load_*` 계열 배선 불필요**, 데이터 편집 반영은 다른 오버레이와 동일하게 `docker compose restart api`(lru_cache 초기화)면 충분.
- **하지만 데이터 디렉터리가 untracked**: `data/covenants/`·`data/messianic_prophecies/`·`data/topical_verses/`·`data/jesus_parables_miracles/`는 `git status`상 미커밋. `data/`는 `docker-compose.yml`에서 워크트리 볼륨 마운트라 **커밋(또는 워크트리 존재) 없이는 새 서버·클린 체크아웃 배포가 이 파일들을 보지 못한다** — `_load()`가 빈 dict로 폴백하고 신규 기능이 조용히 빈 상태가 된다(에러 없음, `overlays.py:20` WARN 로그만).
- **기존 배포 단절 개념은 그대로**: `deploy.sh`의 데이터 주입은 `inject_ko_names.py`(`deploy.sh:52`) 하나뿐. `README.md:20-22`는 3단계(`load_theographic.py → inject_ko_names.py → inject_date_corrections.py`)를 명시하지만 `deploy.sh`는 `inject_date_corrections.py`·`load_authored_*` 계열 전부 미배선. **신규 5기능은 이 단절을 키우지 않는다**(적재 자체가 없으므로).

---

## ERA_BANDS 3중(+1) 중복 — JS↔Python 공유 설정 부재 (신규 확정)

시대 경계가 이제 프론트·백엔드·다른 백엔드 라우트에 **세 벌**로 하드코딩됐다(+ 데이터 파일이 네 번째 결합점).

- `frontend/src/TimelineView.jsx:15-24` — `ERA_BANDS`(8구간, `{name, from, range}`).
- `backend/app/routes/persons.py:98` — `_ERA_ORDER`(직전 매핑 지적, 잔존).
- `backend/app/routes/stats.py:24-33` — **신규** `ERA_BANDS`(8튜플 `(name, from)`), `_era_of()`(`:36-41`)가 사건 `sortKey`를 시대로 분류. `stats.py:22-23` 주석이 명시적으로 "`frontend/src/TimelineView.jsx`의 `ERA_BANDS`와 동일해야 한다. 공유 설정이 없어 수동 복제 — 프론트 경계 변경 시 이 목록도 함께 갱신할 것"이라고 적어 결합을 자백한다.
- **데이터 결합점(4번째)**: `data/covenants/covenants.json`의 각 언약 `era` 문자열이 `ERA_BANDS`의 `name`과 그대로 일치해야 리본이 렌더된다(`TimelineView.jsx:91-95` `covenantsByEra`). 현재 5건 전부 일치 확인(`원시사`·`족장`·`출애굽·정복`·`왕국`·`신약`)했으나, 경계명 변경 시 리본이 조용히 사라진다(에러 없음). 정합을 강제하는 스키마·테스트 없음.

세 벌 사이 정합을 검사하는 자동 게이트가 없다.

---

## Cache & Reload-Order Footguns

인메모리 캐시 무효화 수단이 사실상 `api` 컨테이너 재시작뿐인 구조는 그대로.

- **`overlays.py` lru_cache가 증가**: 이번 세션에 `covenants()`·`messianic_prophecies()`·`parables_miracles()`·`topical_verses()`·`verse_persons()`·`place_coords()`가 더해져 `backend/app/overlays.py`의 `@functools.lru_cache(maxsize=1)` 함수는 **14개**다(`book_events_raw`·`event_verses`·`bible_verses`·`word_distribution`·`books_ko`·`chapter_summaries`·`chapter_sections`·`quotations`·`messianic_prophecies`·`covenants`·`parables_miracles`·`place_coords`·`topical_verses`·`verse_persons`). 라우트 캐시도 `events.py`에 `_load_approx_book_index`·`_compute_events`·`_book_name_map` 3개, `stats.py`에 `_compute_stats` 1개 신규. 전부 `maxsize=1`(무입력 전역 집계) — 상한 안전하나 반영은 재시작뿐.
- `data/`는 볼륨 마운트라 파일 수정에 이미지 재빌드 불필요하지만 실행 프로세스는 이전 값 서빙. 반영은 `docker compose restart api`뿐.
- **`data/date_corrections/` 재적용 누락 실사례(잔존)**: `README.md`가 `inject_date_corrections.py` 3단계를 명시하나 `deploy.sh`는 미배선. `.forge/retro/2026-07-22-nt-date-corrections.md`가 재적재 드리프트 실사례를 기록. 이번 세션은 date_corrections·load 스크립트 미변경.

---

## Data Pipeline Footguns

- **하드코딩 이벤트 ID가 `event_dedupe` 정리 대상 밖 (잔존):** `backend/scripts/generate_approx_book_verses.py`의 `VERSE_MAP`(`:26-91`)이 `apply_event_dedupe.py` 정리 목록에 없어 dedupe마다 stale 참조 재발 가능(자동 검출 없음). 이번 세션 미변경.
- **`load_books.py` 재실행이 교정 연대를 Ussher 값으로 롤백 (잔존):** `backend/scripts/load_books.py:80-102`. 이번 세션 미변경.
- **Person `birthYear`/`deathYear` ↔ Event 연대 교정 어긋남 5건 (데이터 불변으로 잔존):** 직전 매핑에서 `validate_event_chronology.py` 라이브 실행이 5건 위반(Terah·Isaac 참여 이벤트 역전 2건 + Person 사망<출생 3건: Samson·Ahaziah·Jehoram)을 보고했다. 이번 세션은 Person/Event 연대 데이터·`data/date_corrections/`·load 스크립트를 일절 건드리지 않았다(워킹트리 diff 없음)므로 위반 내용·건수 동일하게 잔존한다. 이번 세션 라이브 재실행은 시도했으나 Neo4j 자격증명 접근이 정책상 차단돼(교차 프로젝트 자원 보호) 미실행 — 데이터 불변으로 논리적 잔존 판정.
- **서신서 Book 연대 범위 오표기 (수용된 한계, 불변):** ADR-0012 "첫 참조=발생" 규약(`load_books.py:130`). 근본 해소 불가로 명시.
- **단어 분포 파이프라인 미등록 의존 (잔존):** kiwipiepy가 `backend/requirements.txt`에 미등록(재확인 — grep 0건).
- **수동 저작 데이터 검증 전부 수동 실행, CI 미연결 (11종으로 증가, 이번 재실행):** 신규 4종 전부 PASS — `validate_covenants.py`(5건 언약, keyVerseId 전수 실존·startDate 파싱 OK)·`validate_messianic_prophecies.py`(25쌍 PASS)·`validate_parables_miracles.py`(65건: 비유 30·기적 35, PASS)·`validate_topical_verses.py`(12주제·74 verseId PASS). 기존 6종(god_reliance·traits·person_context·chapter_summaries·chapter_sections·quotations)은 직전대로 위반 0. `validate_event_chronology.py`는 라이브 5건(위 항목). `data/authored_persons/`는 여전히 전용 validate 없음.
- **비유/기적 지도 색인의 조용한 부분 노출 (신규):** `data/jesus_parables_miracles/index.json` 65건 중 **17건(placeId·lat/lng 둘 다 없는 비유들: good-samaritan·prodigal-son 등)이 지도 레이어에서 조용히 누락**된다 — `frontend/src/mapGeo.js:207`의 `buildParablesMiraclesGeoJSON`이 `lat==null`을 필터. 좌표 해석 결과 48/65만 지도에 뜬다(placeId 28건은 `place_coords`로 해석, 직접 lat/lng 20건). 연표 섹션(`TimelineView.jsx renderPmSection`)은 65건 전부 노출하므로 지도↔연표 커버리지가 불일치. 경고·표기 없음(설계상 위치 없는 비유는 지도에 못 얹는 것이나 문서화 안 됨).

---

## Tech Debt

- **번들 크기 — 신규 뷰 편입으로 메인 청크 재증가 (2026-07-24 실측, 워킹트리 빌드):** `frontend/dist/assets/index-pFaUDbXS.js` **639,438 bytes(≈639.44 kB, gzip 137,932 ≈137.93 kB)** — 직전 매핑 614.43 kB에서 ~25 kB 증가(`StatsView.jsx`·`TopicalVersesView.jsx` 신규 뷰가 lazy 없이 메인 청크에 편입). `vendor-BEFIG7g-.js` 197,604(gzip 62,124), `maplibre-DntM08T7.js` **1,027,608(≈1027.61 kB, gzip 270,093)** 불변. `vite.config.js`에 `manualChunks`(maplibre + vendor 분리)가 있으나 **뷰/라우트 단위 lazy import는 없어** 모든 뷰(스케치·StatsView·TopicalVersesView 포함)가 진입 시 메인 청크로 함께 로드된다. `vite build`의 500 kB 초과 경고 그대로, `chunkSizeWarningLimit` 미설정.
- **대형 프론트엔드 컴포넌트 재증가:** `frontend/src/App.jsx` **51,147 bytes(신규 stats·topics 스테이지 배선 + 5기능 상태로 증가)**, `SidePanel.jsx` 49,485 불변. `frontend/src/sketches/` 디렉터리(9투어 모듈 + `lib.jsx`)는 이번 세션 미변경(9,692줄대). 신규 뷰는 소형(`StatsView.jsx` 6,192 bytes·`TopicalVersesView.jsx` 3,298 bytes).
- **투어 stops ↔ 장면 스케치 커버리지 자동 게이트 부재 (잔존):** ADR-0029가 약속한 대조 스크립트 여전히 없음(grep 0건). 이번 세션 미변경.
- **"큐레이션 13인" 주석 드리프트 (잔존):** `backend/app/routes/persons.py:1`·`:136`의 "13인", `:287`의 "34인"이 실제 35 slug(`data/person_events/` 35파일)와 어긋남.
- **비유/기적 필터 상수 이중 정의 (신규, 코스메틱):** `[['all','전체'],['parable','비유'],['miracle','기적']]`가 `frontend/src/MapView.jsx:12`와 `frontend/src/TimelineView.jsx:10`에 각각 하드코딩(주석이 "별 파일이라 각자 보관"으로 자백). `PM_TYPE_COLOR`(`frontend/src/theme.js:29`)만 공유.
- **`/parables-miracles` 3중 독립 fetch (신규):** `frontend/src/MapView.jsx:31`·`frontend/src/TimelineView.jsx:80`이 각자 `/parables-miracles`를 fetch(`apiGet`은 캐싱·디듀프 없음). `/persons/curated` 3중 fetch 패턴(잔존)에 더해진 동종 사례.

---

## Security Considerations

- **CORS `allow_origins=["*"]`:** `backend/app/main.py:47`. `allow_methods=["GET"]`(`:49`)·무인증 공개 읽기 API라 즉각 위험 낮음. 이번 세션 미변경.
- **Neo4j 127.0.0.1 바인딩·`NEO4J_AUTH` 필수 (양호, 불변).**
- **시크릿 취급 (양호):** `.env` gitignore, 하드코딩 시크릿 0건, 인증 계층 없음(공개 읽기). 신규 라우트도 동일.
- **Cypher 인젝션 표면 (방어 유지):** 신규 `stats.py`·`events.py`의 f-string 삽입은 상수(`TOP_PERSONS_LIMIT` 등)뿐이고 사용자 입력은 파라미터 바인딩(`_load_approx_book_index`의 `ids=book_ids` 등). `events.py`의 `get_event_verses(event_id)` 등 경로변수는 전부 파라미터 바인딩.

---

## Performance Bottlenecks

- **`stats.py`의 인물별 N Neo4j 왕복 (신규, 캐시로 완화):** `_compute_longest_journeys`(`backend/app/routes/stats.py:105-121`)가 큐레이션 13인마다 `_fetch_place_coords()`를 1회씩 호출(journey.py 재사용) → 콜드 캐시에서 N+1 성격. 단 `_compute_stats`가 `lru_cache(maxsize=1)`(`:124`)라 프로세스 수명당 1회로 한정.
- **`journey._build_id_to_slug()` 캐시 없음 (잔존, 소비처 증가):** `backend/app/routes/journey.py:18`이 여전히 `lru_cache` 없이 요청마다 35 slug JSON open/parse. 이제 `stats.py:107`도 이를 호출(단 `_compute_stats` 캐시 내부라 실질 1회).
- **`/words/{book}/verses` 매 요청 전수 substring 스캔 (잔존):** `backend/app/routes/words.py:32-37`. 이번 세션 미변경.
- **대용량 오버레이 JSON 인메모리 상주 (잔존, 증가):** 기존 `bible/verses.json`(9.8MB) 등에 더해 `jesus_parables_miracles/index.json`(30KB)·`messianic_prophecies/prophecies.json`(8.8KB) 등 신규 오버레이도 프로세스당 상주. uvicorn 단일 워커라 잠재적.
- **전역 노드 스캔 검색 (잔존):** `backend/app/routes/search.py:16-17`. 이번 세션 미변경.

---

## Fragile Areas

- **모바일 지도 프레이밍·리사이즈 타이밍 (위 Known Bugs 참조):** `MapView.jsx`의 `isVisible→resize()` 게이팅과 성지 초기 프레이밍 부재가 모바일 세계 축소 뷰 버그의 근원.
- **SPA 해시 라우팅 same-document 미반응 (잔존):** `frontend/src/useStageNavigation.js`(이번 세션 modified) — 신규 stats·topics 스테이지·URL 상태가 추가됐으나 초기 해시 1회 캡처·`hashchange` 리스너 부재 패턴 자체는 유지.
- **연도 파싱·표기 다중 중복 (잔존, 증가):** `frontend/src/dates.js` `parseYear`, `nodes.py` `_year`, `load_books.py` `_parse_year`, `validate_event_chronology.py` `_year`, 그리고 이제 `stats.py` `_era_of`·`TimelineView.jsx` `eraOf`까지 시대 분류 로직도 사실상 중복. 공유 모듈 미추출.
- **오버레이 빈값 폴백이 하류에서 표출 (잔존, 신규 라우트는 방어적):** `overlays.py`의 파일 없음/파싱 실패는 빈 dict/list 폴백(`:36-43`). 신규 `events.py` 라우트들(`get_covenants` 등)은 `.get("covenants", [])` 식으로 방어해 빈 폴백을 조용히 빈 목록으로 흡수 — 에러 없이 신규 기능이 빈 상태가 된다(데이터 미커밋 시 실제 발생 가능). 반면 기존 `words.py:27`·`books.py:133`은 빈 폴백을 IndexError/ValueError로 전파(비대칭).
- **프론트 stale 응답 무효화 수동 관리 (잔존, 신규 사례 추가):** `cancelled` 플래그 패턴이 이제 `StatsView.jsx:54-58`·`TopicalVersesView.jsx:14-18`에도 반복. 공유 훅 미추출.

---

## Deployment / Ops Risks

- **신규 데이터 디렉터리 4종이 미커밋 (당장의 배포 위험):** `data/covenants/`·`data/messianic_prophecies/`·`data/topical_verses/`·`data/jesus_parables_miracles/`가 untracked. `data/`는 볼륨 마운트라 커밋 전에는 클린 체크아웃 배포에서 `_load()`가 빈 폴백 → 5기능 중 4개가 조용히 빈 상태(통계는 그래프 기반이라 영향 없음).
- **프론트 `:8080`은 `frontend/dist` 정적 마운트 — HMR 아님:** 소스만 고치고 `npm run build` 미실행 시 이전 빌드 서빙. (현재 dist는 워킹트리 반영 최신 빌드가 존재.)
- **`deploy.sh` 데이터 주입 단절 (잔존):** `inject_date_corrections.py`·`load_authored_*` 미배선. 로그 라벨 `[1/3]`·`[3/4]`·`[4/4]` 어긋남(`deploy.sh:34/45/49`)도 잔존(코스메틱).
- **API `:8000` 외부 미노출·nginx 속도 제한 없음 (잔존).**

---

## Scaling Limits

- **단일 인스턴스 스택, 인메모리 캐시 공유 불가 (잔존):** neo4j 1 + api 1(uvicorn 단일 워커) + nginx 1. `lru_cache`는 프로세스 로컬 — 무효화가 앱 재시작뿐. 신규 캐시들도 동일.

---

## Dependencies at Risk

- **Theographic 데이터 GitHub `master` HEAD 미고정 fetch (잔존).**
- **절 본문 프리베이크 빌드타임 getbible 외부 호출 의존 (잔존).**
- **kiwipiepy — requirements 미등록 빌드타임 의존 (잔존, 재확인).**
- **Neo4j 이미지 메이저 버전만 고정 (잔존):** `docker-compose.yml:3` `image: neo4j:5`.
- **ESLint 계열 caret 범위 (잔존):** `frontend/package.json`의 `eslint-plugin-react-hooks: "^7.1.1"`. lint 미게이팅 구조라 규칙 드리프트가 조용히 위반을 남김.

---

## Test Coverage Gaps

- `*.test.*`/`*.spec.*` 0건, pytest/vitest 설정 전무, `frontend/package.json` scripts에 test 없음 — 재확인 동일.
- **ESLint 7 errors + 1 warning 잔존 (2026-07-24 재실행, 동일 셋·라인만 밀림, 신규 뷰 0건 추가):** `npx eslint src` 결과 —
  - `frontend/src/App.jsx:104` — `react-hooks/set-state-in-effect`, `:109` — `react-hooks/exhaustive-deps`('playback' 누락) 경고. (직전 `:101`·`:106`에서 신규 스테이지 배선으로 라인 밀림.)
  - `frontend/src/TourPlayback.jsx:16` — `react-refresh/only-export-components`, `:24` — `react-hooks/set-state-in-effect`.
  - `frontend/src/sketches/lib.jsx:6`·`:8`·`:12` — `react-refresh/only-export-components`.
  - `frontend/src/tourSketches.jsx:17` — `react-refresh/only-export-components`.
  - `set-state-in-effect` 2건은 React 팀이 "cascading renders" 리스크로 분류. lint가 CI/`deploy.sh` 미게이팅이라 배포 미차단. **신규 `StatsView.jsx`·`TopicalVersesView.jsx`는 위반 0**(cancelled 플래그·의존성 규칙 준수).
- 데이터 검증 11종 중 10종 위반 0(신규 4종 포함), `validate_event_chronology.py`만 라이브 5건 — CI 미연결·수동 실행 의존.
- **신규 검증 4종도 수동 실행 전용 (기존 7종과 동일):** `validate_covenants.py`·`validate_messianic_prophecies.py`·`validate_parables_miracles.py`·`validate_topical_verses.py` 어디에도 CI/`deploy.sh` 훅 없음.
- **ERA_BANDS 3벌 정합 검사 없음 (신규):** TimelineView.jsx ↔ persons.py `_ERA_ORDER` ↔ stats.py ERA_BANDS ↔ covenants.json `era`.
- **비유/기적 지도↔연표 커버리지 불일치 검사 없음 (신규):** 65건 중 48건만 지도, 17건 누락을 잡는 게이트 없음.
- wip 계약·slug 소스 다계열 일치·BC/AD 파싱 다중 사본 여전히 자동 검증 없음(잔존).
- `/node/{id}` vs `/node/{id}/neighbors/grouped` 동작 일치 테스트 없음(잔존).
- UI 검증은 Playwright 수동 실행 의존, CI 미연동(신규 5기능 UAT도 `.forge/reports/` 수동 캡처로만 확인).
