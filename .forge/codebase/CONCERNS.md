---
last_mapped_commit: 304eda1c53acff4c4860b838e8627483c666f74c
mapped: 2026-07-18
---

# CONCERNS

현재 코드베이스에서 확인된 기술 부채·버그 위험·보안·성능·취약 지점 목록. 각 항목은 HEAD(`304eda1`)에서 실제 파일·라인 재추적, 라이브 API(`localhost:8080`, prod와 동일 스택) 조회, ESLint/데이터 기계검증 재실행으로 확인했다.

이번 갱신 배경: 직전 매핑(`fa9902e`, 2026-07-17) 이후 본문 리더 신설(task#205), 장 개요 저작(task#206), 책의 무대 미니맵(task#207), 책 인장 66권(task#208), 인용 관계 데이터+UI(task#209~210), 정경 순서 내비(task#211), 장 묶음 저작(task#212)이 들어왔다. 이 과정에서 **직전 문서가 지적한 두 가지 Known Bugs가 모두 해소**됐다(아래 첫 절) — 문서 재검증 원칙(잔존 주장은 커밋까지 재추적)에 따라 실측 확인했다.

---

## 직전 매핑 지적 사항 사후 검증 — 2건 모두 해소 확인

- **ESLint 5건(`VerseLayer.jsx` 렌더 중 ref 접근)** — `b3fadd2`(드래그 플래그를 state화)로 해소. `npm run lint` 실측(이번 매핑) 0 problems.
- **구절 근거 없는 사건–책 연결 4사건 불일치(겟세마네·물위걸음·고린도·예루살렘 공의회)** — `9f89118`(task#204)으로 해소. 겟세마네(요한복음 구절 저작)·물위걸음(막·요 구절 저작)은 근거 구절을 실제로 채웠고, 고린도·예루살렘 공의회는 `backend/app/routes/events.py:75-82` `_compute_events`가 "추정(⚡) 권은 그 (권,사건)이 `event_verses`에 근거 구절을 가질 때만 근거 칩에 합류"하도록 바뀌어 **칩과 구절 레이어가 항상 일치**하게 됐다. `.forge/CONTEXT.md`(Book Events 절)가 이 규칙을 정본 문서화 — 구절 근거 없는 ⚡ 연결(살후→고린도, 약→예루살렘 공의회)은 이제 "버그"가 아니라 "책 마커 행에만 남고 사건 근거로는 승격 안 됨"이 설계 의도다.
- 라이브 API(`GET /events`) 실측 재확인: `authored-jesus-gethsemane-prayer`(4권/4권)·`authored-peter-walks-on-water`(3권/3권)·`authored-paul-corinth`(2권/2권)·`authored-paul-jerusalem-council`(1권/1권) — 전건 칩=레이어 권수 일치.
- 단, **사건–책 연결과 event_verses 권 집합의 일치를 검사하는 자동 스크립트는 여전히 없다** — 이번 재확인도 API 응답 수기 대조. 신규 저작 사건마다 같은 불일치가 재발할 수 있는 구조 자체는 남아 있다(아래 Test Coverage Gaps).

---

## Cache & Reload-Order Footguns

가장 조용히(에러 없이) 잘못된 상태를 만드는 부류. 캐시 무효화 수단이 사실상 **`api` 컨테이너 재시작뿐**이고, 재적재 순서를 빠뜨리면 파생 레이어가 소실된다.

**인메모리 캐시 무효화 = `api` 재시작뿐 (`lru_cache` 산재 — 본문 리더·장 개요·인용 관계로 또 증가):**
- `backend/app/overlays.py` **9개**(maxsize=1, 직전 6개에서 +3): `book_events_raw`·`event_verses`·`bible_verses`·`word_distribution`·`books_ko`·`verse_persons`에 이번 마일스톤 신규 `chapter_summaries`(`:78`)·`chapter_sections`(`:84`)·`quotations`(`:90`)가 가세.
- `backend/app/routes/books.py` — **이번에 lru_cache 계열에 신규 편입된 라우트 파일**: `_book_bb`(`:37`, maxsize=1)·`_book_meta`(`:43`, maxsize=1, Book 노드 nameKo/chapterCount)·`_chapter_payload`(`:54`, **maxsize=2048** — 장 단위, 전체 1,189장보다 여유)·`_quotations_payload`(`:106`, maxsize=66 — 책당 1). 장 개요·장 묶음·인용 관계 데이터를 고치고 `docker compose restart api` 없이는 반영되지 않는 경로가 하나 늘었다.
- `backend/app/routes/reliance.py` 5개: `_alias_to_bb`(`:27`)·`_slug_to_id`(`:48`)·`_id_to_slug`(`:68`)·`_load_entries`(`:73`, maxsize=None — 도달 경로는 32 slug 화이트리스트로 제한)·`_all_percents`(`:92`).
- `backend/app/routes/family.py` 4개(maxsize=1): `_family_role_pairs`·`_id_to_slug`·`_curated_ids`·`_lineage_ids`.
- `backend/app/routes/events.py` 3개, `backend/app/routes/persons.py` 5개 maxsize=1 + 2개 maxsize=256(`:221`·`:284`), `backend/app/routes/places.py` 1개 maxsize=256(`:21`), `backend/app/routes/tours.py` 2개.
- `data/`는 `docker-compose.yml:19-20`에서 api 컨테이너에 볼륨 마운트라 파일 수정에 이미지 재빌드는 불필요하지만, 실행 중 프로세스는 이전 값을 계속 서빙한다. 무효화 API·TTL·mtime 감시 없음 — 반영은 `docker compose restart api`뿐(task#206·#208~#212 데이터 저작 전부 이 운용 전제).
- API 응답 브라우저 캐시: `books.py`의 신규 엔드포인트(`/book/{id}/chapters`·`/book/{id}/quotations`·`/book/{id}/chapter/{n}`)도 기존 관행대로 `max-age=3600`(`:101`·`:158`·`:167`). `frontend/src/api.js`의 `?v=` 빌드 ID로 배포 시 무력화되므로 "재배포 후 옛 데이터"는 api 재시작 누락이 원인일 가능성이 가장 높다.

**그래프 재적재 순서 — 정본 문서 부재는 그대로:**
- `README.md`의 적재 순서는 `load_theographic → inject_ko_names → inject_date_corrections` 3단계뿐, `deploy.sh`는 `inject_ko_names.py` 하나만 재실행(`:52`). 이번 마일스톤(task#205~212)은 전부 오버레이 JSON+lru_cache 경로(Neo4j 재적재 스크립트 신규 없음)라 이 절 자체는 악화되지 않았으나, 기존 미등록 스크립트는 그대로 잔존:
  - `backend/scripts/load_authored_genealogy.py`(마태1 저작 계보) — README·deploy.sh 미등록.
  - `backend/scripts/load_authored_mothers.py`(어머니 간선) — docstring이 재실행 필요성을 명시하나 미등록.
  - `backend/scripts/load_authored_persons.py` — "`load_person_events.py`보다 먼저" 순서 제약이 docstring에만 존재.
- `load_theographic.py` 전체 재실행은 노드 속성을 Ussher 연대계 원본으로 되돌린다 → `inject_date_corrections.py` 재실행 필수(ADR-0014).
- `backend/scripts/`는 `__init__.py` 제외 **37개**(직전 34 + `validate_chapter_summaries.py`·`validate_chapter_sections.py`·`validate_quotations.py`). 순서가 틀리면 관계가 0건으로 조용히 누락(에러 없음).

---

## 대규모 콘텐츠 저작 파이프라인의 계정 사용량 한도 리스크 (신규, task#212 회고 실증)

- `.forge/retro/2026-07-18-chapter-sections.md`가 명시: 61-에이전트 Dynamic Workflow(sonnet)로 장 묶음을 병렬 저작하던 중 **계정 사용량 한도(5:20am KST 리셋)에 걸려 12권만 서브에이전트가 저작하고 나머지 49권은 메인 세션이 직접 저작**해야 했다. 재-fanout이 같은 한도에 다시 걸릴 위험(직전 런 110에이전트·565k토큰)을 피하려 폴백한 것.
- 완화 요인: `validate_chapter_sections.py`가 저자(서브에이전트 vs 메인 세션) 무관하게 불변식을 기계 검증해 산출물 품질은 보증됐다(저작↔검증 분리 패턴의 실전 이점). 하지만 **60+ 에이전트 규모의 콘텐츠 fan-out을 CI/자동화 없이 재현하려 하면 같은 실패가 재발**할 수 있는 구조적 리스크는 문서화만 됐을 뿐 코드/워크플로 차원의 방지책은 없다(다음 대규모 저작 작업의 계획 단계에서 배치 분할 또는 메인 세션 폴백을 처음부터 준비해야 한다는 교훈만 남음).

---

## Wip Person / 신원 규약

**wip 계약(가족 간선만·검색 제외)이 여전히 분산·암묵적:**
- wip 필터는 `backend/app/routes/search.py:19`의 `AND (n.status IS NULL OR n.status <> 'wip')` 한 줄뿐. `backend/app/routes/nodes.py`의 이웃 쿼리(`:121`·`:173`)와 `family.py` 트리 구성엔 wip 구분 없음.
- 계약 자체는 `backend/scripts/load_theographic.py`의 `__main__` 배선으로만 보장 — 개별 함수엔 가드 없음.

**큐레이션 신원 규약은 단일화 완료, slug "소스"는 계속 다계열:**
- `events[0].participants[0]` 규약은 `backend/app/overlays.py:102` `curated_person_id()`로 단일화 완료 — `persons.py`·`places.py`·`reliance.py`가 공유.
- slug를 정의하는 파일 소스는 여전히 여러 계열: `data/person_events/` 파일명(35) · `persons.py:98` `_ERA_ORDER`/`_ERA` · `data/person_relations/relations.json` endpoint slug · `data/god_reliance/` 파일명(32) · `data/person_slugs/seal_slugs.json`(비큐레이션 인장 인물 slug→id). 이들 간 일치를 강제하는 스키마·테스트는 없다.
- `/persons/curated`를 `frontend/src/PersonHub.jsx:199`·`frontend/src/PersonIntro.jsx:69`·`frontend/src/useStageNavigation.js:50` **3곳이 여전히 각자 독립 fetch**한다(`frontend/src/api.js`의 `apiGet`은 캐싱·디듀프 없음). 경합 버그는 과거에 해소됐지만(직전 문서 참조) 화면 진입마다 동일 응답을 최대 3회 받아오는 중복은 남아 있다.

---

## Genealogy / Graph-Derived Concerns

**하나님(God)이 아담의 부모로 그래프 잔존 — 가계도 조상 순회에 필터 없음:**
- 라이브 Neo4j: `Adam -[:CHILD_OF]-> God/하나님`. `family.py`의 조상 순회(`CHILD_OF*1..100`)에 God 제외가 없어 아담 focus 가계도에서 하나님이 조상 노드로 오른다. 인물 연결 축(`persons.py:238`)과 keyPeople 이웃(`nodes.py:212`)은 `<> 'God'`로 명시 제외하는 것과 비대칭.

**SidePanel "이웃"에 부모가 부모·자식으로 이중 표시 (잔존):**
- 부모-자식이 상호 간선(`PARENT_OF`+`CHILD_OF`) MERGE인데 이웃 쿼리는 무방향 — `backend/app/routes/nodes.py:121`·`:173` 모두 `-[r]-`. 같은 인물이 2회 노출.

**`family.py`의 예수 노드 id 하드코딩:**
- `_JESUS_ID = "recgkFqZovgbr3pAi"` 상수 + `_lineage_ids()`의 "여성 조상은 마리아만, 나머지 Male만" 규칙이 코드에 박혀 있다.

**동명이인 위험 (잔존):**
- 이름(nameKo) 기반 링크 저작 시 야고보 3인·유다 3인 등 동명이인을 데이터로 못박아야 하는 구조는 그대로. `family.py:39` `_family_role_pairs`의 `frozenset({nameKoA,nameKoB})` 키 매핑도 nameKo 표기 드리프트 시 role이 조용히 누락돼 gender 폴백.

**theographic `children` 배열은 출생순이 아니다 (잔존):**
- 출생 순서 정본은 `data/person_relations/relations.json`의 role 라벨뿐.

---

## Data Pipeline Footguns

**`load_books.py` 재실행이 교정 연대를 Ussher 값으로 롤백 (잔존):**
- 매 실행 GitHub 원본을 새로 받아 Book `startYear`/`endYear`를 덮어쓴다.

**Person `birthYear`/`deathYear`는 Ussher 연대 잔존 — UI 미노출 상태 유지.**

**Event `startDate`는 혼재 형식 문자열 — 사전순 정렬 금지 (잔존).** 파싱 로직 다중 사본 문제는 아래 Fragile Areas.

**단어 분포 파이프라인의 미등록 의존:**
- `backend/scripts/build_word_distribution.py`·`build_word_verse_index.py`는 kiwipiepy 필요하나 `backend/requirements.txt`에 없음. 후자의 산출물 `data/word_verse_index/index.json`(1.7MB)은 런타임 로더가 제거된 뒤에도 잔존 — 소비처 없는 오프라인 자산(`grep`으로 백엔드 코드 참조 0건 재확인).

**수동 저작 데이터의 검증이 전부 수동 실행 — 이번 마일스톤으로 대상 3건 증가:**
- 기존 `validate_god_reliance.py`·`validate_traits.py`·`validate_event_chronology.py`·`validate_person_context.py`에 이번 마일스톤 `validate_chapter_summaries.py`(1,189장 개요)·`validate_chapter_sections.py`(281묶음 연속·전수·비중첩 불변식)·`validate_quotations.py`(302쌍 실존·측·라벨 자기일치·중복)가 추가됐다. 7종 모두 CI 미연결, 수동 실행 의존. `data/authored_persons/`(1,060명 규모)는 전용 validate 스크립트 자체가 여전히 없다.

---

## Tech Debt

**시드 파이프라인 ↔ `deploy.sh` 단절 (재현성 최대 리스크, 그대로):**
- `deploy.sh`의 데이터 주입은 `inject_ko_names.py`(`:52`) 하나. `load_authored_persons/mothers/genealogy` 등은 볼륨 삭제·신규 서버 시 전체 재현 순서의 정본 문서가 없다.
- 부수: `deploy.sh` 로그 라벨 `[1/3]`(`:34`)·`[2/3]`(`:40`)·`[3/4]`(`:45`)·`[4/4]`(`:49`) 어긋남 잔존(코스메틱, 이번 재확인).

**번들 크기 경고 — maplibre 청크 500kB 한계 초과 (잔존, 실측 재확인):**
- `frontend/dist/assets/maplibre-*.js` **1,027,600B(≈1.0MB)**, 메인 `index-*.js` 205.7KB — `frontend/vite.config.js`의 `manualChunks`가 분리는 하지만 `chunkSizeWarningLimit` 미설정이라 매 빌드 경고. 이번 마일스톤(리더·미니맵·인장·인용 UI)으로 메인 청크도 늘었지만 maplibre 대비 작다.

**대형 프론트엔드 컴포넌트 (본문 리더·인용 UI·인장으로 순위 재교체):**
- `frontend/src/SidePanel.jsx` **928줄**(직전 787 — 책의 무대·인용 관계 섹션 추가). `frontend/src/App.jsx` **868줄**(직전 735 — 리더 스테이지·정경 내비). `frontend/src/bookSymbols.jsx` **670줄**(신규, task#208 — 66권 손저작 SVG, `personSymbols.jsx` 519줄보다 큼). `frontend/src/personSymbols.jsx` 519줄. `frontend/src/FamilyTree.jsx` 485줄. `frontend/src/mapLayers.js` 451줄. `frontend/src/RelianceView.jsx` 440줄.

**"큐레이션 13인" 주석 드리프트 잔존:**
- `backend/app/routes/persons.py:1`·`:136`의 "13인", `:287`의 "34인"이 실제 `_ERA` 35 slug·`data/person_events/` 35개와 계속 어긋난다.

**`/persons/curated` 3중 독립 fetch** — 위 신원 규약 절 참조.

**책 인장 66권(`bookSymbols.jsx`)에 전용 데이터 검증 스크립트 없음:**
- `personSymbols.jsx`와 마찬가지로 SVG는 코드 파일이라 `validate_*.py` 계열 대상이 아니다(수기/에이전트 리뷰로 66권 커버리지 확인, 별도 스크립트 부재). 회귀 시(키 누락·중복 등) 잡아줄 자동 검사가 없다는 점은 personSymbols와 동형의 기존 한계.

---

## Known Bugs

**topEvents "대표성 절단" 편향 잔존:**
- `backend/app/routes/nodes.py`의 Book 분기 — 발생/인용 구분(`rel.primary`)은 해소됐지만 연도 오름차순 + `[:10]`(`:276`) 하드 절단은 그대로(ADR-0012 범위 밖 명시).

**서신서 Book 연대 범위 오표기 (수용된 한계):**
- "첫 참조=발생" 휴리스틱이 서신서의 회고 인용에 오판정 — authored_events 경로가 없는 책이라 근본 해소 불가.

(직전 문서의 ESLint 5건·사건-책 권수 불일치 4건은 상단 "해소 확인" 절 참조 — 둘 다 해소.)

---

## Security Considerations

**CORS `allow_origins=["*"]`:**
- `backend/app/main.py:47`. `allow_methods=["GET"]`·무인증 공개 읽기 API라 즉각 위험 낮으나 쓰기·인증 추가 시 오리진 화이트리스트 필요.

**Neo4j는 127.0.0.1에만 바인딩 (양호):**
- `docker-compose.yml:5-6` 루프백 노출, `NEO4J_AUTH` 필수화(`:10`). api는 내부 네트워크.

**시크릿 취급 (양호):** `.env` gitignore, 하드코딩 시크릿 0건, 인증 계층 자체 없음(공개 읽기).

**Cypher 인젝션 표면 (방어 유지):** `search.py`·`words.py`·`verses.py` 모두 파라미터 바인딩/파이썬 레벨 처리. `nodes.py` f-string 삽입은 상수뿐.

**사용자 제어 키 lru_cache — 유한 상한으로 완화 유지:**
- `persons.py:221`·`:284`, `places.py:21`의 `maxsize=256`. `books.py`의 신규 `_chapter_payload`(maxsize=2048)는 키가 (bookId, 장번호) 조합으로 실제 도메인(1,189장)에 상한이 자연히 걸려 있어 스래싱 여지 낮음. `reliance.py:73`의 `maxsize=None`은 화이트리스트 경유로 도달 불가.

---

## Performance Bottlenecks

**`/words/{book}/verses` — 매 요청 31,103절 전수 substring 스캔 (잔존):**
- `backend/app/routes/words.py:32-37`가 요청마다 `overlays.bible_verses()` 전체를 순회하며 `w in text` 검사. 결과 캐시 없음, 한 글자 입력도 전수 스캔 유발. lemma 역색인(`data/word_verse_index/index.json`)은 빌드돼 있으나 미배선.

**대용량 오버레이 JSON 전체 인메모리 상주 (대상 확대):**
- `data/bible/verses.json`(9.8MB)·`data/event_verses/events.json`·`data/verse_persons/index.json`(857KB)에 이번 마일스톤 `data/chapter_summaries/books.json`(6,079줄)·`data/chapter_sections/books.json`(1,529줄)·`data/quotations/quotations.json`(3,483줄)이 가세 — 전부 `overlays.py` lru_cache로 프로세스당 상주. `backend/Dockerfile` uvicorn 단일 워커라 현재는 잠재적, 워커 다중화 시 배증.

**`_build_id_to_slug()`에 캐시 없음 (잔존):**
- `backend/app/routes/journey.py:18`이 `lru_cache` 없이 요청마다 `_ERA` 35개 slug JSON을 open/parse.

**전역 노드 스캔 검색 (잔존):**
- `backend/app/routes/search.py:16-17` `MATCH (n) WHERE ... CONTAINS ...` — 라벨·인덱스 미사용 전수 스캔. `main.py:37`의 인덱스 생성 실패 시 `logger.exception` 후 계속 기동(에러 삼킴은 아니고 로깅은 되지만 인덱스 없이 기동)과 겹치면 악화.

---

## Fragile Areas

**SPA 해시 라우팅 — same-document 해시 이동에 미반응 (잔존):**
- `frontend/src/useStageNavigation.js`는 초기 해시를 마운트 시 1회만 캡처, `hashchange` 리스너 없음. 신규 `#/read/<id>[/<n>]` 리더 스테이지도 기존 `words` 패턴과 동형으로 배선돼(popstate 상태 복원 포함) 이 한계를 그대로 물려받는다 — Playwright 등이 `goto`로 해시만 바꾸면 거짓 음성/양성, URL마다 새 브라우저 컨텍스트가 정석.

**`startDate`/연도 파싱·표기 로직 다중 중복 (잔존):**
- `frontend/src/dates.js` `parseYear`, `backend/app/routes/nodes.py` `_year`, `backend/scripts/load_books.py` `_parse_year`, `backend/scripts/validate_event_chronology.py` `_year` — 공유 모듈 미추출, 회귀 assert는 `load_books.py`에만.

**시대 밴드 8구간이 프론트·백엔드에 이중 하드코딩 (잔존):**
- `frontend/src/TimelineView.jsx` `ERA_BANDS`(연도 경계 포함)가 `backend/app/routes/persons.py:98` `_ERA_ORDER` 8구간과 "정합"을 주석으로만 약속. 한쪽 개편 시 다른 쪽은 컴파일·런타임 어느 단계에서도 안 깨지고 조용히 어긋난다.

**오버레이 빈값 폴백이 하류에서 500으로 표출 (대상 확대):**
- `backend/app/overlays.py`의 파일 없음/파싱 실패는 경고 후 빈 dict/list 폴백인데, `words.py:27` 부근은 `books_ko()`가 비면 `book_ids.index(book_id)` ValueError → 500과 같은 패턴이 `books.py:133` `_quotations_payload`에도 있다 — `books_ko()`가 비면 `tids = list(books_ko)`가 빈 리스트가 되어 `tids[int(other_ids[0][:2]) - 1]`이 IndexError → 500. 오버레이 파일이 정상 배포돼 있는 한 실제 트리거는 낮지만, 폴백 경로 자체는 신규 엔드포인트로 한 곳 더 늘었다.

**프론트 stale 응답 무효화의 수동 관리 (잔존, ChapterReader도 동일 패턴 채택):**
- `cancelled`/AbortController + `alive` 플래그 패턴이 `SidePanel.jsx`·`WordDistributionView.jsx`·`RelianceView.jsx`·`useStageNavigation.js`에 이어 신규 `frontend/src/ChapterReader.jsx:15-23`·`:25-35`(장 목차·장 본문 두 effect 모두)에도 반복 구현됐다. 공유 훅 미추출.

**성품·의존도 통제 어휘의 문서·코드 이중 관리 (잔존):**
- `backend/scripts/validate_traits.py`의 `VIRTUES`/`FLAWS` ↔ `data/character_traits/AUTHORING.md`, `validate_god_reliance.py`의 `MODES`/`KINDS` ↔ `data/god_reliance/AUTHORING.md`. 이번 마일스톤 신규 데이터(장 개요·장 묶음·인용)는 자유 텍스트/구조화 스키마라 통제 어휘 이중관리 대상이 아님(해당 없음, 악화 없음).

**모션 시스템의 재발성 함정 (task#189~191·202 회고에서 코드 구조로 남은 것, 변화 없음):**
- `animation-fill-mode: both` keyframe은 종료 후에도 인라인 transform을 덮는다 — 새 시트/드로어 도입 시 같은 함정 재발 소지. 이번 마일스톤(리더·미니맵·인용 대조)은 기존 VerseLayer·시트 컴포넌트를 재사용해 신규 모션 코드가 거의 없어 이 절의 위험은 늘지 않았다.

---

## Deployment / Ops Risks

**프론트 `:8080`은 `frontend/dist` 정적 마운트 — HMR 아님:**
- `docker-compose.yml:30` `./frontend/dist:...:ro`. 소스만 고치고 `npm run build`를 안 하면 이전 빌드를 계속 서빙(에러 없음). 리더·인용 UI 등 신규 프론트 코드도 동일 제약.

**API `:8000` 외부 미노출:** compose에 host 포트 매핑 없음 — `nginx/nginx.conf`의 `/api/` 프록시로만 접근.

**nginx 속도 제한 없음:** `limit_req` 미설정(이번 재확인). `words.py` 전수 스캔과 겹치면 악화 조합.

---

## Scaling Limits

**단일 인스턴스 스택, 인메모리 캐시 공유 불가:**
- neo4j 1 + api 1(uvicorn 단일 워커) + nginx 1. `lru_cache`는 프로세스 로컬 — 다중 워커 확장 시 인스턴스별 중복·불일치, 상주 메모리 배증(`books.py` 4개 캐시 신규 가세로 계속 증가). 무효화 수단이 앱 재시작뿐인 것도 그대로.

---

## Dependencies at Risk

**Theographic 데이터를 GitHub `master` HEAD에서 미고정 fetch (잔존):**
- `backend/scripts/load_theographic.py`·`load_books.py` 등 커밋 SHA 고정 없이 raw 다운로드.

**절 본문 프리베이크가 빌드타임 getbible 외부 호출 의존 (잔존):** `generate_verse_text.py`의 UA 403 우회 필요. 본문 리더(task#205)·장 개요(task#206)·인용 관계(task#209~210) 전부 이 프리베이크 산출물(`data/bible/verses.json`)에 의존해 대상 확대.

**kiwipiepy — requirements 미등록 빌드타임 의존 (잔존).**

**Neo4j 이미지 메이저 버전만 고정 (잔존):** `docker-compose.yml:3` `image: neo4j:5`.

**ESLint 계열 caret 범위 (잔존):** `frontend/package.json`의 `eslint-plugin-react-hooks: "^7.1.1"` 등 — 규칙 추가가 파이프라인 변경 없이 lint 결과를 흔들 수 있다. lint 미게이팅이라 배포는 안 막히지만(과거 5건 재파손 실증) "0 유지" 목표가 조용히 무너지는 구조는 그대로.

---

## Test Coverage Gaps

- `*.test.*`/`*.spec.*` 0건, pytest/vitest 설정 전무, `frontend/package.json` scripts에 test 없음 — 이번 재확인에서도 동일.
- 데이터 검증 스크립트 **7종**(기존 4 + 신규 `validate_chapter_summaries.py`·`validate_chapter_sections.py`·`validate_quotations.py`) 모두 CI 미연결·수동 실행 의존. `data/authored_persons/`(1,060명)는 validate 스크립트 자체가 없음.
- 특히 위험 높은 미검증 지점:
  - **사건–책 연결 ↔ event_verses 권 집합 일치** — task#204가 4건을 실측 해소했지만, 이 대조를 자동화한 스크립트는 여전히 없다(신규 저작 사건마다 재발 가능).
  - wip 계약(가족 간선만·검색 제외)이 `__main__` 배선+검색 WHERE 한 줄에 분산 — 자동 검증 없음.
  - slug 소스 5계열의 일치 강제 스키마·테스트 없음.
  - `ERA_BANDS`(프론트) ↔ `_ERA_ORDER`(백엔드) 8구간 정합은 주석 약속뿐.
  - BC/AD 연도 파싱 다중 사본 중 assert는 `load_books.py` 하나뿐.
  - **60+ 에이전트 규모 콘텐츠 fan-out의 계정 사용량 한도 리스크** — validate 스크립트가 산출물 품질은 보증하지만 fan-out 실행 자체의 안정성(배치 분할·폴백)을 강제하는 장치는 없음(위 신규 절 참조).
- UI 검증은 Playwright 수동 실행 의존, CI 미연동. SPA 해시 특성상 딥링크 검증은 URL마다 새 브라우저 컨텍스트가 정석.
- ESLint는 실행되나 CI/`deploy.sh` 미게이팅 — 과거 0 복원 하루 만에 5건 재파손된 사례가 이 갭의 실증(이번엔 재파손 없이 유지 확인).
