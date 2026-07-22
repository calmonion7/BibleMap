---
last_mapped_commit: f5e17ae2993e228f8b7481dba03478ddec8616f4
mapped: 2026-07-22
---

# CONCERNS

현재 코드베이스에서 확인된 기술 부채·버그 위험·보안·성능·취약 지점 목록. 각 항목은 HEAD(`f5e17ae`)에서 실제 파일·라인 재추적, 라이브 API(`localhost:8080`, prod와 동일 스택) 조회, ESLint·데이터 검증 스크립트(7종) 재실행으로 확인했다.

이번 갱신 배경: 직전 매핑(`304eda1`, 2026-07-18) 이후 인물 여정 마리아 사건 보강(task#213), 내비·스크롤 복원(task#214·215), 브랜드 헤더(task#216~217), 인물 연표 필터 수정(task#218), 하나님 의존도 재정규화(task#219~220), 테마 투어 개요·자동재생 엔진·정차지 해설(task#222~225), 장면 스케치 애니메이션 9투어 165장면 저작(task#226~231), 투어 서사 순서·사건 커버리지 보강 165→275(task#232~235), 인물 여정 연대계 35파일 전수 감사(task#236), 신약 date_corrections 확장(task#237~238), 가족 이웃 디듀프·죽은 ID 재매핑(직전 HEAD)이 들어왔다.

---

## 직전 매핑 지적 사항 사후 검증

- **가족 이웃 무방향 매치로 인한 2회 노출·라벨 뒤섞임 — `/node/{id}`만 해소, `/node/{id}/neighbors/grouped`는 미해소로 남음.** `backend/app/routes/nodes.py:150-206`(`get_node`)는 HEAD 커밋에서 `startNode(r) = n`을 함께 반환해 이웃 역할 기준으로 `PARENT_OF`/`CHILD_OF`를 정규화하고 `(id, rel)` 디듀프를 추가했다. 그러나 `backend/app/routes/nodes.py:116-147`(`get_node_neighbors_grouped`)는 여전히 `-[r]-(m)`(:121) 무방향 매치이고 정규화·디듀프 둘 다 없다. 라이브 확인(아담 `recyYgUiSETdWFgEP`): `/node/{id}`는 셋·가인·아벨·하나님 각 1회(정규화된 라벨)로 정확히 나오는 반면, `/node/{id}/neighbors/grouped`는 셋·가인·아벨·하나님 각각 `PARENT_OF`와 `CHILD_OF` 두 줄이 동시에 뜬다(하나는 방향이 뒤집힌 오라벨). 다만 이 엔드포인트의 유일한 소비처인 `frontend/src/mapRingController.js:112`는 응답의 `Event` 배열만 쓰고 `Person`은 읽지 않아, 현재 UI에 실사용 영향은 없다 — 향후 이 엔드포인트를 Person 표시에 쓰면 즉시 재현된다.
- **`generate_approx_book_verses.py`의 죽은 theographic ID 키 3건** — 살전·살후·약을 가리키던 `VERSE_MAP` 항목이 `apply_event_dedupe.py`(task#168, ADR-0016)의 event_dedupe 병합으로 죽은 ID를 참조하고 있던 것을 HEAD 커밋이 생존 ID(`authored-paul-corinth`/`authored-paul-jerusalem-council`)로 재매핑해 해소했다. 단, 이 재매핑은 근본 원인(아래 Data Pipeline Footguns 신규 항목)을 없애지 않았다 — 같은 종류의 stale 참조가 향후 dedupe마다 재발할 수 있다.
- 그 외 직전 문서의 나머지 항목(ESLint 0건·사건-책 권수 불일치 해소)은 그대로 유효했으나, **이번 마일스톤에서 ESLint가 다시 깨졌다** — 아래 Test Coverage Gaps 참조(별개 신규 회귀, 이 절의 "해소 확인" 대상 아님).

---

## Cache & Reload-Order Footguns

인메모리 캐시 무효화 수단이 사실상 **`api` 컨테이너 재시작뿐**이고, 재적재 순서를 빠뜨리면 파생 레이어가 소실되는 구조는 그대로다. 이번 마일스톤은 신규 API 엔드포인트를 추가하지 않아 `lru_cache` 개수 자체는 불변(총 36개: `overlays.py` 9·`books.py` 4·`reliance.py` 5·`family.py` 4·`events.py` 3·`persons.py` 7·`places.py` 1·`tours.py` 2).

- `data/`는 `docker-compose.yml:19-20`에서 볼륨 마운트라 파일 수정에 이미지 재빌드는 불필요하지만, 실행 중 프로세스는 이전 값을 계속 서빙한다. 반영은 `docker compose restart api`뿐.
- **`data/date_corrections/` 재적용 누락의 실제 재현 사례(신규 확증)**: `.forge/retro/2026-07-22-nt-date-corrections.md`가 명시 — 이번 task#237·238 작업 중 `persons.json`의 Seth 교정이 DB에서 원복돼 있던 것을 발견, `inject_date_corrections.py` 재실행으로 재적용했다("재적재 드리프트 실사례"). `README.md:20-22`는 `load_theographic.py → inject_ko_names.py → inject_date_corrections.py` 3단계 순서를 명시하지만, `deploy.sh:49`는 여전히 `inject_ko_names.py`만 재실행하고 `inject_date_corrections.py`는 배선돼 있지 않다. 교정 테이블은 이번 마일스톤으로 **`data/date_corrections/events.json` 253건**(직전 대비 대폭 증가, 신약 앵커 이관분 포함)·`persons.json` 1건으로 늘어, 신규 서버·볼륨 재구축 시 절차 누락의 파급 범위도 커졌다.
- `backend/scripts/`는 `__init__.py` 제외 **37개**(직전과 동일 — 이번 마일스톤은 신규 스크립트 없이 기존 스크립트 데이터만 갱신). `load_authored_genealogy.py`·`load_authored_mothers.py`·`load_authored_persons.py`는 여전히 README·deploy.sh 미등록.

---

## 대규모 콘텐츠 저작 파이프라인의 계정 사용량 한도 리스크 (직전 지적, 이번 마일스톤엔 재발 없음)

- `.forge/retro/2026-07-18-chapter-sections.md`가 지적한 61-에이전트 fan-out 계정 사용량 한도 리스크는 이번 마일스톤(장면 스케치 165장면·투어 해설 110건·연대 감사 35파일)의 회고 어디에도 재발 기록이 없다 — 배치를 나눠 진행한 것으로 보이나(task#226~231이 "1/4·2/4·3/4·4/4" 단계로 커밋 분리), 구조적 방지책(배치 분할·메인 세션 폴백을 계획 단계에 강제하는 장치)은 여전히 코드/워크플로 차원에 없다.

---

## Wip Person / 신원 규약

**wip 계약(가족 간선만·검색 제외)이 여전히 분산·암묵적** — `backend/app/routes/search.py:19`의 WHERE 절 한 줄뿐, `nodes.py`의 이웃 쿼리·`family.py` 트리 구성엔 wip 구분 없음. 계약 자체는 `backend/scripts/load_theographic.py`의 `__main__` 배선으로만 보장.

**큐레이션 신원 규약은 단일화 완료, slug "소스"는 계속 다계열** — `events[0].participants[0]` 규약은 `backend/app/overlays.py:102` `curated_person_id()`로 단일화. slug 정의 파일은 여전히 `data/person_events/`(35파일) · `persons.py:98` `_ERA_ORDER` · `data/person_relations/relations.json` · `data/god_reliance/`(32파일) · `data/person_slugs/seal_slugs.json` 다계열. 일치를 강제하는 스키마·테스트 없음.

**`/persons/curated` 3중 독립 fetch (잔존)** — `frontend/src/PersonHub.jsx:201`·`frontend/src/PersonIntro.jsx:69`·`frontend/src/useStageNavigation.js:50` 3곳이 여전히 각자 fetch(`apiGet`은 캐싱·디듀프 없음).

---

## Genealogy / Graph-Derived Concerns

**하나님(God)이 아담의 부모로 그래프 잔존 — 조상 순회에 필터 없음 (잔존, 라이브 재확인):** `family.py:112`·`:161`의 `CHILD_OF*1..100` 조상 순회에 God 제외가 없다. 라이브 확인 결과 아담의 `/node/{id}` 이웃에 `PARENT_OF 하나님`이 정확한 라벨로 뜬다(위 절 참조) — 즉 이번 디듀프 수정은 표시를 정확하게 만들었을 뿐 "하나님이 조상으로 집계되는" 근본 데이터 문제는 그대로다. `persons.py:238`·`nodes.py:223`은 `<> 'God'`로 명시 제외하는 것과 비대칭.

**`family.py`의 예수 노드 id 하드코딩 (`_JESUS_ID = "recgkFqZovgbr3pAi"`, `:92`) 및 "여성 조상은 마리아만" 규칙 (잔존):** 코드에 상수로 박혀 있다.

**동명이인 위험 (잔존):** `family.py:41` `_family_role_pairs`의 `frozenset({nameKoA,nameKoB})`(`:62`) 키 매핑이 nameKo 표기 드리프트 시 role 누락 → gender 폴백.

**theographic `children` 배열은 출생순이 아니다 (잔존):** 출생 순서 정본은 `data/person_relations/relations.json`의 role 라벨뿐.

---

## Data Pipeline Footguns

**하드코딩 이벤트 ID가 `event_dedupe` 정리 대상 밖에 있어 dedupe마다 stale 참조가 재발할 수 있는 구조 (신규 확인):**
- `apply_event_dedupe.py`의 docstring(`:1-6`)은 정리 대상으로 person_events·verse_events·authored_events·tours·book_events·names_ko·date_corrections를 명시한다. 하지만 `backend/scripts/generate_approx_book_verses.py`의 `VERSE_MAP`(파이썬 딕셔너리 리터럴, `:26-91`)은 이 목록에 없다 — 실제로 이번 마일스톤 직전 HEAD 커밋에서 살전·살후·약 3건의 키가 dedupe로 죽은 ID를 참조하고 있던 것을 수동으로 발견·재매핑해야 했다. 조회 실패 시 에러 없이 그 책의 대표 구절 생성만 조용히 스킵되는 구조라, 향후 dedupe 실행마다 같은 종류의 회귀가 재발할 수 있다(자동 검출 없음).

**`load_books.py` 재실행이 교정 연대를 Ussher 값으로 롤백 (잔존):** 매 실행 GitHub 원본을 새로 받아 Book `startYear`/`endYear`를 덮어쓴다. 신약 date_corrections 251건 확장 이후에도 이 재계산 경로는 Neo4j의 교정된 Event.startDate가 아니라 raw events.json에서 값을 다시 뽑아 쓴다(`backend/scripts/load_books.py:80-102`) — 재실행 시 Book 범위가 다시 오염될 여지 그대로.

**Person `birthYear`/`deathYear`가 Event 연대 교정과 별도 관리돼 어긋남이 라이브로 재현됨 (신규 확증):** `validate_event_chronology.py` 실행 결과(HEAD, `.env` 로드) — 인물 출생 대비 참여 이벤트 역전 2건("Terah 참여 이벤트 1건이 출생(-2125)보다 앞섬 — 최악 사례 'Birth of Abraham'(-2166)", "Isaac 참여 이벤트 1건이 출생(-2065)보다 앞섬 — 최악 사례 'Isaac's birth in Beersheba region'(-2066)")과 Person 스캔(사망<출생) 3건(Samson·Ahaziah·Jehoram)으로 총 5건 위반이 현재도 보고된다. task#236의 41건 사건 연대 교정은 Event 노드의 `startDate`/`sortKey`만 갱신했고 Person 노드의 `birthYear`/`deathYear`(theographic 원본, Ussher 연대계)는 별도 필드라 갱신 대상이 아니었던 것으로 추정 — 기존 "Person birthYear/deathYear는 Ussher 연대 잔존" 한계의 구체적 재현이다.

**서신서 Book 연대 범위 오표기 (수용된 한계, 불변):** ADR-0012의 "첫 참조(`verses[0]`)=발생" 규약(`backend/scripts/load_books.py:130`)이 서신서의 회고 인용을 발생으로 오판정 — authored_events 경로가 없는 책이라 근본 해소 불가. ADR-0012 자체가 이를 "범위 밖(잔존)"으로 명시.

**단어 분포 파이프라인의 미등록 의존 (잔존):** kiwipiepy 필요 스크립트가 `backend/requirements.txt`에 미등록.

**수동 저작 데이터의 검증이 전부 수동 실행, CI 미연결 (7종, 이번 재실행 결과):** `validate_god_reliance.py`(OK, 32명·195항목)·`validate_traits.py`(OK, 47명·177개)·`validate_person_context.py`(OK, 1146명)·`validate_chapter_summaries.py`(PASS, 66권 1189장)·`validate_chapter_sections.py`(PASS, 61권 281묶음)·`validate_quotations.py`(PASS, 302쌍) 6종은 위반 0. **`validate_event_chronology.py`만 5건 위반**(위 항목). `data/authored_persons/`는 전용 validate 스크립트 자체가 여전히 없다.

---

## Tech Debt

**시드 파이프라인 ↔ `deploy.sh` 단절 (그대로):** `deploy.sh`의 데이터 주입은 `inject_ko_names.py`(`:49`) 하나. `inject_date_corrections.py`·`load_authored_*` 계열 모두 미배선. 로그 라벨 `[1/3]`·`[2/3]`·`[3/4]`·`[4/4]` 어긋남도 잔존(코스메틱).

**번들 크기 — 메인 청크가 이번 마일스톤에서 2배 이상 증가:** `frontend/dist/assets/index-*.js` **449.16KB**(직전 205.7KB — 장면 스케치 165장면·투어 재생 엔진·개요 페이지가 메인 청크에 편입돼 급증), `maplibre-*.js` 여전히 **1,027.60KB**. `vite build` 경고("Some chunks are larger than 500 kB") 그대로, `chunkSizeWarningLimit` 미설정.

**대형 프론트엔드 컴포넌트 + 신규 대형 디렉터리:** `frontend/src/App.jsx` **936줄**(직전 868 — 투어 재생 스테이지 배선), `frontend/src/SidePanel.jsx` 928줄(불변). **신규 `frontend/src/sketches/` 디렉터리 총 5,744줄**(9개 투어별 모듈 + `lib.jsx`) — `davidUnitedKingdom.jsx` 784줄·`gospelOfJesus.jsx` 734줄·`exileAndReturn.jsx` 679줄·`patriarchsCovenant.jsx` 678줄·`theEarlyChurch.jsx` 616줄·`exodusToConquest.jsx`/`elijahAndElisha.jsx` 각 607줄·`ageOfJudges.jsx` 572줄·`creationToFlood.jsx` 443줄. ADR-0029가 "투어당 1개 모듈로 분리"를 의도적 설계로 명시하나(단일 파일이면 "10k줄, 편집·리뷰 불능"), 결과적으로 코드베이스에 SVG 애니메이션 저작물 5,744줄이 편입된 것은 사실이다. `bookSymbols.jsx`(670줄)·`personSymbols.jsx`(519줄)·`FamilyTree.jsx`(485줄)·`mapLayers.js`(451줄)는 불변.

**ADR-0029가 약속한 "장면 스케치 커버리지 검증 게이트" 스크립트가 아직 없음 (신규 확인):** ADR(`0029-scene-sketches-as-code-modules.md:13`)은 "투어 stops와 장면 레지스트리 집합 대조 스크립트가 커버리지 검증 게이트"라고 명시하지만, `backend/scripts/`·`frontend/`에 이런 대조 스크립트는 없다(grep 0건). 실측: 투어 `stops` 총 275개(9개 투어 전부 note 100% 저작 완료, `data/tours/*.json`)인데 반해 장면 레지스트리(`tourSketches.jsx`의 `SCENES`) 키는 165개뿐 — 110개 정차지는 장면 스케치가 없다. `hasSketch()`가 `false`를 반환해 `TourSketch`가 아무것도 렌더하지 않는 그레이스풀 설계(ADR 명시)라 버그는 아니지만, 향후 정차지 추가 시 스케치 누락이나 eventId 오타로 인한 커버리지 회귀를 잡아줄 자동 검사가 여전히 없다.

**"큐레이션 13인" 주석 드리프트 (잔존):** `backend/app/routes/persons.py:1`·`:136`의 "13인", `:287`의 "34인"이 실제 35 slug와 계속 어긋난다.

**`/persons/curated` 3중 독립 fetch** — 위 신원 규약 절 참조.

**책 인장 66권(`bookSymbols.jsx`)에 전용 데이터 검증 스크립트 없음 (잔존).**

---

## Known Bugs

**`/node/{id}/neighbors/grouped`의 가족 간선 무방향 중복·오라벨 (잔존, 라이브 재확인) — 위 "직전 매핑 지적 사항 사후 검증" 절 참조.** 유일 소비처가 Event만 읽어 현재 UI 영향은 없음.

**topEvents "대표성 절단" 편향 (잔존):** `nodes.py:287`의 연도 오름차순 + `[:10]` 하드 절단(ADR-0012가 범위 밖으로 명시).

**서신서 Book 연대 범위 오표기 (수용된 한계, 불변):** 위 Data Pipeline Footguns 참조.

**`validate_event_chronology.py` 5건 위반이 현재도 라이브로 보고됨 (신규 확인):** 위 Data Pipeline Footguns 참조. CI 미게이팅이라 이 위반들이 배포를 막지 않는다.

---

## Security Considerations

**CORS `allow_origins=["*"]`:** `backend/app/main.py:47`. `allow_methods=["GET"]`(`:49`)·무인증 공개 읽기 API라 즉각 위험 낮음.

**Neo4j는 127.0.0.1에만 바인딩 (양호):** `docker-compose.yml:5-6`, `NEO4J_AUTH` 필수화(`:10`).

**시크릿 취급 (양호):** `.env` gitignore, 하드코딩 시크릿 0건, 인증 계층 자체 없음(공개 읽기).

**Cypher 인젝션 표면 (방어 유지):** 파라미터 바인딩 일관, `nodes.py` f-string 삽입은 상수(`NODE_NEIGHBOR_LIMIT` 등)뿐.

**사용자 제어 키 lru_cache — 유한 상한으로 완화 유지:** `persons.py`·`places.py`의 `maxsize=256`, `books.py` `_chapter_payload`(maxsize=2048, 실도메인 1,189장 상한). `reliance.py`의 `maxsize=None`은 화이트리스트 경유로 도달 불가.

---

## Performance Bottlenecks

**`/words/{book}/verses` — 매 요청 31,103절 전수 substring 스캔 (잔존):** `backend/app/routes/words.py:32-37`. 캐시 없음.

**대용량 오버레이 JSON 전체 인메모리 상주 (잔존):** `data/bible/verses.json`(9.8MB)·`event_verses`·`verse_persons`·`chapter_summaries`·`chapter_sections`·`quotations` 전부 `overlays.py` lru_cache로 프로세스당 상주. uvicorn 단일 워커라 현재는 잠재적.

**`_build_id_to_slug()`에 캐시 없음 (잔존):** `backend/app/routes/journey.py:18`이 `lru_cache` 없이 요청마다 35개 slug JSON을 open/parse.

**전역 노드 스캔 검색 (잔존):** `backend/app/routes/search.py:16-17` `MATCH (n) WHERE ... CONTAINS ...` — 인덱스 미사용 전수 스캔.

---

## Fragile Areas

**SPA 해시 라우팅 — same-document 해시 이동에 미반응 (잔존):** `frontend/src/useStageNavigation.js`는 초기 해시를 마운트 시 1회만 캡처, `hashchange` 리스너 없음.

**`startDate`/연도 파싱·표기 로직 다중 중복 (잔존):** `frontend/src/dates.js` `parseYear`, `nodes.py` `_year`(`:271`), `load_books.py` `_parse_year`, `validate_event_chronology.py` `_year` — 공유 모듈 미추출.

**시대 밴드 8구간이 프론트·백엔드에 이중 하드코딩 (잔존):** `TimelineView.jsx` `ERA_BANDS` ↔ `persons.py:98` `_ERA_ORDER` — 주석 약속뿐.

**오버레이 빈값 폴백이 하류에서 500으로 표출 (잔존):** `overlays.py`의 파일 없음/파싱 실패는 빈 dict/list 폴백인데, `words.py:27`·`books.py:133` 부근이 이를 IndexError/ValueError로 전파.

**프론트 stale 응답 무효화의 수동 관리 (잔존):** `cancelled`/AbortController + `alive` 플래그 패턴이 `SidePanel.jsx`·`WordDistributionView.jsx`·`RelianceView.jsx`·`useStageNavigation.js`·`ChapterReader.jsx`에 반복 구현. 공유 훅 미추출.

**모션 시스템의 재발성 함정 (변화 없음):** `animation-fill-mode: both` keyframe이 종료 후에도 인라인 transform을 덮는 함정. 이번 마일스톤(장면 스케치)은 SVG `symbol-draw` 클래스·`--sym-delay` CSS 변수 기반의 별도 체계(`sketches/lib.jsx`)를 써서 이 특정 함정 자체를 재현하지는 않았으나, ESLint 신규 위반(아래)이 보여주듯 신규 모션/재생 코드의 React 규칙 준수는 느슨해졌다.

---

## Deployment / Ops Risks

**프론트 `:8080`은 `frontend/dist` 정적 마운트 — HMR 아님:** `docker-compose.yml:30`. 소스만 고치고 `npm run build`를 안 하면 이전 빌드를 계속 서빙.

**API `:8000` 외부 미노출:** compose에 host 포트 매핑 없음.

**nginx 속도 제한 없음:** `limit_req` 미설정.

---

## Scaling Limits

**단일 인스턴스 스택, 인메모리 캐시 공유 불가 (잔존):** neo4j 1 + api 1(uvicorn 단일 워커) + nginx 1. `lru_cache`는 프로세스 로컬 — 무효화 수단이 앱 재시작뿐인 것도 그대로.

---

## Dependencies at Risk

**Theographic 데이터를 GitHub `master` HEAD에서 미고정 fetch (잔존).**

**절 본문 프리베이크가 빌드타임 getbible 외부 호출 의존 (잔존):** `generate_verse_text.py`의 UA 403 우회 필요.

**kiwipiepy — requirements 미등록 빌드타임 의존 (잔존).**

**Neo4j 이미지 메이저 버전만 고정 (잔존):** `docker-compose.yml:3` `image: neo4j:5`.

**ESLint 계열 caret 범위 (잔존, 이번에 실제로 재파손):** `frontend/package.json`의 `eslint-plugin-react-hooks: "^7.1.1"` — 버전 자체는 직전과 동일해 캐럿 드리프트가 이번 회귀의 원인은 아니지만, "규칙 추가가 lint 결과를 흔들 수 있다"는 우려대로 lint 미게이팅 구조에서 신규 코드가 기존 규칙을 위반한 채 그대로 머지된 사례가 실측됐다(아래 Test Coverage Gaps).

---

## Test Coverage Gaps

- `*.test.*`/`*.spec.*` 0건, pytest/vitest 설정 전무, `frontend/package.json` scripts에 test 없음 — 이번 재확인에서도 동일.
- **ESLint 0 → 7 errors + 1 warning으로 재파손 (신규 회귀, 실측):** `npx eslint src` 결과 4개 파일에서 위반.
  - `frontend/src/App.jsx:101` — `react-hooks/set-state-in-effect`("Calling setState synchronously within an effect"), `:106` — `react-hooks/exhaustive-deps`(playback 의존성 누락) 경고.
  - `frontend/src/TourPlayback.jsx:16` — `react-refresh/only-export-components`, `:24` — `react-hooks/set-state-in-effect`.
  - `frontend/src/sketches/lib.jsx:6`·`:8`·`:12` — `react-refresh/only-export-components`(상수·헬퍼 함수를 컴포넌트 파일에서 export).
  - `frontend/src/tourSketches.jsx:17` — `react-refresh/only-export-components`.
  - `react-refresh` 위반들은 dev HMR 저하(코스메틱)에 그치지만, `set-state-in-effect` 2건은 React 팀이 명시적으로 "cascading renders" 리스크로 분류하는 패턴이다. lint가 CI/`deploy.sh`에 게이팅돼 있지 않아 배포는 막히지 않는다 — 직전 문서가 우려한 "0 유지 목표가 조용히 무너지는 구조"가 이번에 실제로 재현됐다.
- 데이터 검증 스크립트 7종 중 6종은 위반 0, **`validate_event_chronology.py`는 5건 위반**(위 Data Pipeline Footguns 참조) — CI 미연결·수동 실행 의존은 그대로.
- **투어 장면 스케치 커버리지 검증 게이트(ADR-0029 명시) 미구현** — 위 Tech Debt 참조. 현재 275 stops 중 165(60%)만 스케치 보유, 나머지는 그레이스풀 미표시(설계 의도)지만 회귀를 잡을 자동 대조는 없다.
- `event_dedupe` 정리 대상에 `generate_approx_book_verses.py`의 `VERSE_MAP` 하드코딩 ID가 빠져 있어, 향후 dedupe 실행마다 stale 참조가 자동 검출 없이 재발할 수 있다(위 Data Pipeline Footguns).
- wip 계약·slug 소스 5계열 일치·`ERA_BANDS`/`_ERA_ORDER` 정합·BC/AD 연도 파싱 다중 사본은 여전히 자동 검증 없음(잔존).
- `/node/{id}` vs `/node/{id}/neighbors/grouped` 두 이웃 엔드포인트의 동작 일치를 검사하는 테스트 없음(이번에 라이브 수기 대조로 불일치 확인).
- UI 검증은 Playwright 수동 실행 의존, CI 미연동.
