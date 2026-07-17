---
last_mapped_commit: fa9902ef9755f8a2aa2bea544fbb93b8d7f6aaff
mapped: 2026-07-17
---

# CONCERNS

현재 코드베이스에서 확인된 기술 부채·버그 위험·보안·성능·취약 지점 목록. 각 항목은 HEAD(`fa9902e`)에서 실제 파일·라인 재추적, 라이브 Neo4j 조회, ESLint/데이터 기계검증 재실행으로 확인했다.

이번 갱신 배경: 직전 매핑(`23e41ee`, 2026-07-16) 이후 성경책 몰입 개편(task#192~194), 가계도 개편 3부작(task#195~197, 폐포 전원 저작 1,060명·어머니 간선·인장), 관계 탭 개편·저작 보강(task#198~199), 연표 시대 밴드(task#200), 무좌표 여정(task#201), 구절 레이어 통일 쉘(task#202), 저작 사건 다권 근거 구절 보강(task#203)이 들어왔다. 직전 매핑 당일 후속(`24e8365`)으로 죽은 `word_verse_index` 로더 제거·ESLint 0 복원·slug 신원 `overlays.curated_person_id()` 단일화가 반영됐으나, **ESLint는 task#202에서 다시 5건으로 파손**됐고(아래 Known Bugs), **task#203이 5권을 원칙적으로 스킵하면서 구절 근거 없는 사건–책 연결 4사건·5권이 잔존**한다(아래 신규 절).

---

## bug-report.md 사후 검증 — confirmed 12건 전건 해소 (직전 문서의 오기 정정)

`.forge/bug-report.md`(task#150, 2026-07-10)의 confirmed 12건을 이번에 전건 재추적한 결과 **12건 모두 수정 완료**다. 백엔드 9건(#1~#9)은 직전 매핑에서 이미 해소 확인됐고, 이번에 프론트 3건(#10~#12)도 수정 커밋을 확정했다:

- **#10 인물필터 상태머신** — `6f73d31`(2026-07-10)에서 해소. `frontend/src/useNodeSelection.js`에서 `personEventIds` 관리가 제거되고, `frontend/src/App.jsx:67-81`이 `explorePersonId` 변경 시에만 `/person/{id}/event-ids`를 fetch해 필터를 채운다(선택 노드와 무관 — 장소 클릭으로 풀리지 않음).
- **#11 curated 이중 fetch 경합** — `9c49a83`(2026-07-10)에서 해소. `frontend/src/useStageNavigation.js:134`의 히스토리 동기화 effect deps에 `curatedIds`가 추가돼, 카드 클릭이 slug맵 로드보다 빨라도 로드 완료 시 재실행되어 올바른 pushState가 찍힌다(`:132-133` 주석에 #11 명시).
- **#12 딥링크 게이트 고착** — 같은 `9c49a83`에서 해소. `useStageNavigation.js:81-83`의 복원 게이트가 `parsed?.stage === 'explore' && parsed?.personSlug`일 때만 `curatedIds`를 기다리도록 분리돼, curated API 실패 시에도 `#/books`·`#/tours` 등은 즉시 복원된다.

**직전 CONCERNS.md(2026-07-16 매핑)가 #10~#12를 "미착수 잔존"으로 기재한 것은 오류였다** — 세 수정 커밋 모두 매핑 커밋 `23e41ee`의 조상(2026-07-10)이다. 문서 재검증 시 "잔존" 항목도 커밋 이력까지 재추적해야 한다는 교훈 사례.

**잔존하는 관련 구조(증상 아님):** `/persons/curated`를 `frontend/src/PersonHub.jsx:199`·`frontend/src/PersonIntro.jsx:69`·`frontend/src/useStageNavigation.js:47` **3곳이 여전히 각자 독립 fetch**한다(`frontend/src/api.js`의 `apiGet`은 캐싱·디듀프 없음). 경합 버그는 해소됐지만 화면 진입마다 동일 응답을 최대 3회 받아오는 중복과, 소비처별 재시도 정책 불일치(useStageNavigation만 1s→2s→4s 재시도)는 남아 있다.

---

## 구절 근거 없는 사건–책 연결 5권 잔존 — 칩·레이어 권수 불일치 4사건 (task#203 스킵분, 신규)

task#203(`d084550`)이 저작 사건 21건×누락 37권 중 32권에 근거 구절을 저작했으나, **근거 본문이 실재하지 않는 5권은 원칙대로 스킵**했다(회고 `.forge/retro/2026-07-17-authored-event-multibook-verses.md`가 후속 과제로 명시). 이번 매핑에서 라이브 Neo4j(CONTAINS_BOOK) + `data/book_events/books.json`(추정책 오버레이) 합집합 vs `data/event_verses/events.json`을 전수 비교해 실측 확정한 잔존 불일치:

| 사건 | 칩(그래프+추정책) | 구절 레이어 | 근거 없는 연결 |
|---|---|---|---|
| `authored-jesus-gethsemane-prayer` | 마·막·눅·요 4권 | 3권 | 요한복음 |
| `authored-peter-walks-on-water` | 마·막·요 3권 | 1권 | 마가복음·요한복음 |
| `authored-paul-corinth` | 행·살전·살후 3권 | 2권 | 데살로니가후서 |
| `authored-paul-jerusalem-council` | 행·약 2권 | 1권 | 야고보서 |

- 증상: `frontend/src/TimelineView.jsx:155`의 칩(`"${first.nameKo} 외 ${bks.length - 1}권"`)은 `/events`(`backend/app/routes/events.py` `_compute_events` — CONTAINS_BOOK + 추정책 머지) 기준 권수를 보여주는데, 사건을 열면 `/event/{id}/verses`(`events.py:110` 부근, `event_verses` 오버레이)가 주는 권 탭(`frontend/src/VerseLayer.jsx` `VerseBookTabs`)은 더 적다 — 사용자에게 "외 2권"이라 말해놓고 레이어엔 1권만 나오는 모순.
- 원인: 저작 사건의 "책 연결"(그래프/추정책)과 "근거 구절"(`event_verses`)이 이원화돼 있는데, 이 5건은 연결만 있고 구절이 없다. 물위걸음·겟세마네 건은 그래프 CONTAINS_BOOK, 고린도 살후·공의회 야고보서 건은 `data/book_events/books.json` 추정책 연결이 원천.
- 해소 방향(회고 명시): 연결 자체의 정당성 재검토 — 제거 또는 근거 재정의를 별도 태스크로. 억지 인용으로 채우는 것은 근거 인정 2패턴(평행 기사/집필 정황 자기 언급) 원칙 위반이라 금지.
- 재발 방지 부재: 사건–책 연결과 event_verses 권 집합의 일치를 검사하는 스크립트·CI가 없다(이번 비교도 수기 실행).

---

## Cache & Reload-Order Footguns

가장 조용히(에러 없이) 잘못된 상태를 만드는 부류. 캐시 무효화 수단이 사실상 **`api` 컨테이너 재시작뿐**이고, 재적재 순서를 빠뜨리면 파생 레이어가 소실된다.

**인메모리 캐시 무효화 = `api` 재시작뿐 (`lru_cache` 산재 — 가계도 개편으로 또 증가):**
- `backend/app/overlays.py` 6개(maxsize=1): `book_events_raw`·`event_verses`·`bible_verses`·`word_distribution`·`books_ko`·`verse_persons` (`:46-77`).
- `backend/app/routes/reliance.py` 5개: `_alias_to_bb`(`:27`)·`_slug_to_id`(`:48`)·`_id_to_slug`(`:68`)·`_load_entries`(`:73`, **maxsize=None** — 단 키가 `_id_to_slug()` 화이트리스트 32 slug로만 도달)·`_all_percents`(`:92`).
- `backend/app/routes/family.py` 4개(maxsize=1, 가계도 개편 신규 포함): `_family_role_pairs`(`:39`)·`_id_to_slug`(`:70`)·`_curated_ids`(`:86`)·`_lineage_ids`(`:95`, 메시아 계보 — Neo4j 순회 결과 상주).
- `backend/app/routes/events.py` 3개(`:11`·`:53`·`:98`), `backend/app/routes/persons.py` 5개 maxsize=1 + 2개 maxsize=256(`:221`·`:284`), `backend/app/routes/places.py` 1개 maxsize=256(`:21`), `backend/app/routes/tours.py` 2개(`:30`·`:55`).
- 과거 무한 누적 수정분(bug-report #5/#7): `persons.py:221`·`:284`·`places.py:21`의 `maxsize=256`은 유지 확인. 잔존 무한(`reliance.py:73`)은 위처럼 도달 경로가 막혀 있어 실질 위험 낮음.
- `data/`는 `docker-compose.yml:19-20`에서 api 컨테이너에 볼륨 마운트라 파일 수정에 이미지 재빌드는 불필요하지만, 실행 중 프로세스는 이전 값을 계속 서빙한다. 무효화 API·TTL·mtime 감시 없음 — 반영은 `docker compose restart api`뿐(task#203도 데이터만 바꾸고 재시작으로 반영, 이 운용은 회고로 정착됨).
- API 응답 브라우저 캐시: `reliance.py:155`·`:175`는 `max-age=3600`, 대부분 라우트는 `max-age=300`. `frontend/src/api.js:12`의 `?v=` 빌드 ID로 배포 시 무력화되므로 "재배포 후 옛 데이터"는 api 재시작 누락이 원인일 가능성이 가장 높다.

**그래프 재적재 순서 — 정본 문서 부재 속에 스크립트가 계속 늘어난다:**
- `README.md:20-22`의 적재 순서는 `load_theographic → inject_ko_names → inject_date_corrections` 3단계뿐, `deploy.sh`는 `inject_ko_names.py` 하나만 재실행(`:52`). 그러나 실제 재현에 필요한 재실행 대상은 이번 마일스톤으로 더 늘었다:
  - `backend/scripts/load_authored_genealogy.py`(마태1 저작 계보, ADR-0019) — 기존 미등록 잔존.
  - `backend/scripts/load_authored_mothers.py`(어머니 간선, ADR-0027, 신규) — docstring 스스로 "그래프 초기화 후 load_theographic 재실행 시 이 스크립트도 재실행해야 복원된다"고 명시. README·deploy.sh 미등록.
  - `backend/scripts/load_authored_persons.py`(신규) — docstring에 "**load_person_events.py보다 먼저** 실행돼야 HAS_PARTICIPANT MATCH가 성립"이라는 순서 제약이 있으나 이 제약이 docstring에만 존재.
- `load_theographic.py` 전체 재실행은 노드 속성을 Ussher 연대계 원본으로 되돌린다 → `inject_date_corrections.py` 재실행 필수(ADR-0014). wip 마킹·가족 폐포·큐레이션 rec 시드도 이 스크립트의 `__main__` 배선이 담당.
- `backend/scripts/`는 `__init__.py` 제외 **34개**(직전 33 + `load_authored_mothers.py`; `load_authored_persons.py`는 기존 카운트에 포함돼 있었음). 순서가 틀리면 관계가 0건으로 조용히 누락(에러 없음).

---

## Wip Person / 신원 규약

**wip 계약(가족 간선만·검색 제외)이 여전히 분산·암묵적:**
- wip 필터는 `backend/app/routes/search.py:19`의 `AND (n.status IS NULL OR n.status <> 'wip')` 한 줄뿐. `backend/app/routes/nodes.py`의 이웃 쿼리(`:121`·`:173`)와 `backend/app/routes/family.py` 트리 구성엔 wip 구분 없음(가계도 혈통 완전성을 위한 의도지만, 가계도에서 wip 인물 클릭 시 SidePanel이 빈약해지는 것도 그대로).
- 계약 자체는 `backend/scripts/load_theographic.py`의 `__main__` 배선으로만 보장 — 개별 함수엔 가드 없음.

**큐레이션 신원 규약은 단일화 완료, slug "소스"는 계속 증식:**
- `events[0].participants[0]` 규약은 `backend/app/overlays.py:84` `curated_person_id()`로 단일화 완료 — `persons.py:111`·`places.py:38`·`reliance.py:62`가 공유(해소). `load_theographic.py:37` `curated_person_ids()`는 스크립트 관행상 자체 구현 유지(docstring에 명시).
- 그러나 slug를 정의하는 파일 소스는 늘었다: `data/person_events/` 파일명(35) · `persons.py:98` `_ERA_ORDER`/`_ERA` · `data/person_relations/relations.json` endpoint slug · `data/god_reliance/` 파일명(32) · **`data/person_slugs/seal_slugs.json`(ADR-0025, 신규 — 비큐레이션 인장 인물 slug→id)**. 이들 간 일치를 강제하는 스키마·테스트는 여전히 없다. (이번 기계검증: relations 176관계·636국면의 slug 전건 해석 가능·approxYear 전건 정수 — task#199 저작 보강 이후에도 정합 유지 확인.)

---

## Genealogy / Graph-Derived Concerns

**하나님(God)이 아담의 부모로 그래프 잔존 — 가계도 조상 순회에 필터 없음:**
- 라이브 Neo4j 실측: `MATCH (a:Person {name:'Adam'})-[:CHILD_OF]->(p)` → `God/하나님`. `backend/app/routes/family.py`의 조상 순회(`CHILD_OF*1..100`, `:112` 부근)에 God 제외가 없어, 아담 focus 가계도에서 하나님이 조상 노드로 오르고 `frontend/src/FamilyTree.jsx:116-126` `roleLabel`이 세대+gender 규칙으로 '아버지' 라벨을 붙인다. 인물 연결 축(`persons.py:238`)과 keyPeople 이웃(`nodes.py:212`)은 `<> 'God'`로 명시 제외하는 것과 비대칭.

**SidePanel "이웃"에 부모가 부모·자식으로 이중 표시 (잔존):**
- 부모-자식이 상호 간선(`PARENT_OF`+`CHILD_OF`) MERGE인데 이웃 쿼리는 무방향 — `backend/app/routes/nodes.py:121`·`:173` 모두 `-[r]-`. 같은 인물이 2회 노출. 가계도 개편(task#195~197)은 `family.py`를 새로 짰지만 이 이웃 쿼리는 미수정.

**`family.py`의 예수 노드 id 하드코딩:**
- `_JESUS_ID = "recgkFqZovgbr3pAi"` 상수 + `_lineage_ids()`의 "여성 조상은 마리아만, 나머지 Male만" 규칙이 코드에 박혀 있다. theographic 재적재로 id가 바뀌는 일은 없지만(고정 rec id), 계보 규칙 변경은 코드 수정 사안.

**동명이인 위험 (ADR-0017/0018/0021 잔존):**
- 이름(nameKo) 기반 링크 저작 시 야고보 3인·유다 3인 등 동명이인을 데이터로 못박아야 하는 구조는 그대로. `family.py:39` `_family_role_pairs`의 `frozenset({nameKoA,nameKoB})` 키 매핑도 nameKo 표기 드리프트 시 role이 조용히 누락돼 gender 폴백.

**theographic `children` 배열은 출생순이 아니다 (잔존):**
- 출생 순서 정본은 `data/person_relations/relations.json`의 role 라벨뿐(`family.py:39-66`이 읽어 전달). role 없는 형제 집합은 UI가 순서를 보증하지 못한다.

---

## Data Pipeline Footguns

**`load_books.py` 재실행이 교정 연대를 Ussher 값으로 롤백 (잔존):**
- 매 실행 GitHub 원본을 새로 받아 Book `startYear`/`endYear`를 덮어쓴다. date_corrections 적용 후 재실행 시 책 연도 롤백. (연-월 정밀도 파싱 자체는 bug-report #2 수정으로 해소, self-check assert 유지.)

**Person `birthYear`/`deathYear`는 Ussher 연대 잔존 — UI 미노출 상태 유지.**

**Event `startDate`는 혼재 형식 문자열 — 사전순 정렬 금지 (잔존).** 파싱 로직 다중 사본 문제는 아래 Fragile Areas.

**단어 분포 파이프라인의 미등록 의존:**
- `backend/scripts/build_word_distribution.py`·`build_word_verse_index.py`는 kiwipiepy 필요하나 `backend/requirements.txt`(fastapi·neo4j·uvicorn 3개, 정확 버전 핀)에 없음 — `/tmp` venv 수동 설치 안내가 docstring에만(`build_word_verse_index.py:16-17`). 후자의 산출물 `data/word_verse_index/index.json`(1.7MB)은 런타임 로더가 제거된 뒤에도 데이터·빌드 스크립트가 잔존 — 소비처 없는 오프라인 자산.

**수동 저작 데이터의 검증이 전부 수동 실행:**
- `validate_god_reliance.py`·`validate_traits.py`·`validate_event_chronology.py`·`validate_person_context.py` 모두 CI 미연결. task#195의 `data/authored_persons/`(people·mothers·genealogy 1,060명 규모)는 전용 validate 스크립트 자체가 없다.

---

## Tech Debt

**시드 파이프라인 ↔ `deploy.sh` 단절 (재현성 최대 리스크, 악화 추세):**
- `deploy.sh`의 데이터 주입은 `inject_ko_names.py`(`:52`) 하나. 위 Reload-Order 절의 신규 스크립트들(`load_authored_persons/mothers/genealogy`)까지 포함해, 볼륨 삭제·신규 서버 시 전체 재현 순서의 정본 문서가 없다.
- 부수: `deploy.sh` 로그 라벨 `[1/3]`(`:34`)·`[2/3]`(`:40`)·`[3/4]`(`:45`)·`[4/4]`(`:49`) 어긋남 잔존(코스메틱).

**번들 크기 경고 — maplibre 청크 500kB 한계 초과 (잔존, 실측 재확인):**
- `frontend/dist/assets/maplibre-*.js` **1,027,608B(≈1.0MB)** — `frontend/vite.config.js`의 `manualChunks`가 분리는 하지만 `chunkSizeWarningLimit` 미설정이라 매 빌드 경고. maplibre-gl 특성상 축소 여지가 작아 lazy import 또는 한계 명시가 남은 선택지.

**대형 프론트엔드 컴포넌트 (라인 수 갱신 — 개편 3건으로 상위권 교체):**
- `frontend/src/SidePanel.jsx` 787줄(직전 823 — 구절 레이어 추출로 감소). `frontend/src/App.jsx` 735줄(684→증가). `frontend/src/personSymbols.jsx` **519줄(인장 선화 확대)**. `frontend/src/FamilyTree.jsx` **485줄(가계도 개편)**. `frontend/src/mapLayers.js` 451줄. `frontend/src/RelianceView.jsx` 440줄.

**"큐레이션 13인" 주석 드리프트 잔존:**
- `backend/app/routes/persons.py:1`·`:136`의 "13인", `:287`의 "34인"이 실제 `_ERA` 35 slug·`data/person_events/` 35개와 계속 어긋남.

**`/persons/curated` 3중 독립 fetch** — 위 bug-report 절 참조(경합 증상은 해소, 구조 잔존).

---

## Known Bugs

**ESLint 재파손 — 5 errors, 전부 `frontend/src/VerseLayer.jsx` (task#202 신규):**
- `npm run lint` 실측(이번 매핑): `:21` `paperTextStyle` named export가 컴포넌트 파일에 공존(`react-refresh/only-export-components`), `:86` `_pad` 미사용(`no-unused-vars` — 의도적 구조분해 폐기지만 규칙 위반), `:89`·`:104-105` **렌더 중 ref 접근 3건**(`react-hooks/refs`) — `const dragging = dragFrom.current != null`을 렌더에서 읽어 transition on/off를 결정한다. ref 변경은 리렌더를 유발하지 않으므로 touchstart 직후(setDragY 전) 렌더에는 dragging이 반영되지 않는 실제 미묘함도 내포.
- `24e8365`에서 0 problems 복원 후 하루 만에 재파손 — **lint가 CI/`deploy.sh` 어디에도 게이팅되지 않는 구조적 문제**(배포는 막히지 않고, 파손이 조용히 누적)가 반복 실증됐다.

**topEvents "대표성 절단" 편향 잔존:**
- `backend/app/routes/nodes.py`의 Book 분기 — 발생/인용 구분(`rel.primary`)은 해소됐지만 연도 오름차순 + `[:10]` 하드 절단은 그대로(ADR-0012 범위 밖 명시).

**서신서 Book 연대 범위 오표기 (수용된 한계):**
- "첫 참조=발생" 휴리스틱이 서신서의 회고 인용에 오판정 — authored_events 경로가 없는 책이라 근본 해소 불가.

**칩·레이어 권수 불일치 4사건** — 상단 신규 절 참조.

---

## Security Considerations

**CORS `allow_origins=["*"]`:**
- `backend/app/main.py:47`. `allow_methods=["GET"]`·무인증 공개 읽기 API라 즉각 위험 낮으나 쓰기·인증 추가 시 오리진 화이트리스트 필요.

**Neo4j는 127.0.0.1에만 바인딩 (양호):**
- `docker-compose.yml:5-6` 루프백 노출, `NEO4J_AUTH` 필수화(`:10`). api는 내부 네트워크.

**시크릿 취급 (양호):** `.env` gitignore, 하드코딩 시크릿 0건, 인증 계층 자체 없음(공개 읽기).

**Cypher 인젝션 표면 (방어 유지):** `search.py`·`words.py`·`verses.py` 모두 파라미터 바인딩/파이썬 레벨 처리. `nodes.py` f-string 삽입은 상수뿐.

**사용자 제어 키 lru_cache — 유한 상한으로 완화 유지:**
- `persons.py:221`·`:284`, `places.py:21`의 `maxsize=256`. 임의 문자열 키 구조는 남아 있어 고유 요청 256개 초과 반복 시 캐시 스래싱 여지(약한 잔존, DoS 아님). `reliance.py:73`의 `maxsize=None`은 화이트리스트 경유로 도달 불가.

---

## Performance Bottlenecks

**`/words/{book}/verses` — 매 요청 31,103절 전수 substring 스캔 (잔존):**
- `backend/app/routes/words.py:20-44`가 요청마다 `overlays.bible_verses()` 전체를 순회하며 `w in text` 검사. 결과 캐시 없음, `w`는 strip 외 검증 없어 한 글자 입력도 전수 스캔 유발. lemma 역색인(`data/word_verse_index/index.json`)은 빌드돼 있으나 미배선(로더도 제거됨) — 쓰든지 지우든지 결정이 남아 있다.

**대용량 오버레이 JSON 전체 인메모리 상주:**
- `data/bible/verses.json`(9.8MB)·`data/event_verses/events.json`(task#203으로 +1,060줄 증가)·`data/verse_persons/index.json`(857KB) 등이 `overlays.py` lru_cache로 프로세스당 상주. `backend/Dockerfile:6` uvicorn 단일 워커라 현재는 잠재적, 워커 다중화 시 배증.

**`_build_id_to_slug()`에 캐시 없음 (잔존):**
- `backend/app/routes/journey.py:18`이 `lru_cache` 없이 요청마다 `_ERA` 35개 slug JSON을 open/parse. `tours.py`도 투어 상세마다 재호출.

**전역 노드 스캔 검색 (잔존):**
- `backend/app/routes/search.py:16-17` `MATCH (n) WHERE ... CONTAINS ...` — 라벨·인덱스 미사용 전수 스캔. `main.py:37`의 인덱스 생성 실패 무시(`except Exception:` 후 계속 기동)와 겹치면 악화.

---

## Fragile Areas

**SPA 해시 라우팅 — same-document 해시 이동에 미반응 (잔존):**
- `frontend/src/useStageNavigation.js`는 초기 해시를 마운트 시 1회만 캡처(`:29`), `hashchange` 리스너 없음. 사용자 딥링크는 신선 로드라 정상이지만, Playwright 등이 `goto`로 해시만 바꾸면 거짓 음성/양성 — URL마다 새 브라우저 컨텍스트가 정석.

**`startDate`/연도 파싱·표기 로직 다중 중복 (잔존):**
- `frontend/src/dates.js` `parseYear`, `backend/app/routes/nodes.py` `_year`, `backend/scripts/load_books.py` `_parse_year`, `backend/scripts/validate_event_chronology.py` `_year` — 공유 모듈 미추출, 회귀 assert는 `load_books.py`에만.

**시대 밴드 8구간이 프론트·백엔드에 이중 하드코딩 (task#200 신규):**
- `frontend/src/TimelineView.jsx:13` `ERA_BANDS`(연도 경계 포함)가 `backend/app/routes/persons.py:98` `_ERA_ORDER` 8구간과 "정합"을 주석으로만 약속(`TimelineView.jsx:10`). 한쪽 개편 시 다른 쪽은 컴파일·런타임 어느 단계에서도 안 깨지고 조용히 어긋난다.

**관계·의존도·단어 뷰 어휘가 프론트 상수와 암묵 결합 (잔존):**
- `frontend/src/RelationsView.jsx:14-15` `TYPE_ICON`·`TYPE_ORDER`(9종 — 이번 기계검증에서 데이터 9종과 정합 확인), `frontend/src/theme.js:26` `VALENCE_COLOR`, `RelianceView.jsx`의 `MODE_META` 류. 데이터 통제어휘 변경 시 validate 스크립트는 잡아도 프론트 매핑 갱신은 별도 수작업.

**오버레이 빈값 폴백이 하류에서 500으로 표출 (잔존):**
- `backend/app/overlays.py`의 파일 없음/파싱 실패는 경고 후 빈 dict 폴백인데, `backend/app/routes/words.py:27` 부근은 `books_ko()`가 비면 `book_ids.index(book_id)` ValueError → 500.

**프론트 stale 응답 무효화의 수동 관리 (잔존):**
- `cancelled`/AbortController + id 비교 패턴이 `SidePanel.jsx`·`WordDistributionView.jsx`·`RelianceView.jsx`·`useStageNavigation.js`에 반복 구현. 공유 훅 미추출.

**성품·의존도 통제 어휘의 문서·코드 이중 관리 (잔존):**
- `backend/scripts/validate_traits.py`의 `VIRTUES`/`FLAWS` ↔ `data/character_traits/AUTHORING.md`, `validate_god_reliance.py`의 `MODES`/`KINDS` ↔ `data/god_reliance/AUTHORING.md`.

**모션 시스템의 재발성 함정 (task#189~191·202 회고에서 코드 구조로 남은 것):**
- `animation-fill-mode: both` keyframe은 종료 후에도 인라인 transform을 덮는다 — `frontend/src/VerseLayer.jsx:51`·`:95-96`처럼 입장 keyframe 요소에 드래그 추종 transform을 얹으려면 `onAnimationEnd`에서 클래스를 제거하는 패턴(entered state)이 필수. 새 시트/드로어 도입 시 같은 함정 재발 소지.
- reduced-motion 토큰 붕괴(1ms)는 `animation-delay: 0 !important` 전역 무효화를 동반해야 하고(ADR-0024), rAF 기반 JS 애니메이션은 CSS 가드가 못 지킨다 — `matchMedia` 분기 직접 필요.
- 연속 터치 이벤트 판정은 state 클로저가 아닌 ref로(`VerseLayer.jsx:54` `dragPx` 주석) — 단 위 Known Bugs처럼 렌더에서 ref를 읽으면 lint 위반+미묘한 미갱신이 생기는 긴장 관계가 있다.

---

## Deployment / Ops Risks

**프론트 `:8080`은 `frontend/dist` 정적 마운트 — HMR 아님:**
- `docker-compose.yml:30` `./frontend/dist:...:ro`. 소스만 고치고 `npm run build`를 안 하면 이전 빌드를 계속 서빙(에러 없음).

**API `:8000` 외부 미노출:** compose에 host 포트 매핑 없음 — `nginx/nginx.conf`의 `/api/` 프록시로만 접근.

**nginx 속도 제한 없음:** `limit_req` 미설정(이번 재확인). `words.py` 전수 스캔과 겹치면 악화 조합.

---

## Scaling Limits

**단일 인스턴스 스택, 인메모리 캐시 공유 불가:**
- neo4j 1 + api 1(uvicorn 단일 워커) + nginx 1. `lru_cache`는 프로세스 로컬 — 다중 워커 확장 시 인스턴스별 중복·불일치, 상주 메모리 배증(`family.py` 4개 캐시 신규 가세). 무효화 수단이 앱 재시작뿐인 것도 그대로.

---

## Dependencies at Risk

**Theographic 데이터를 GitHub `master` HEAD에서 미고정 fetch (잔존):**
- `backend/scripts/load_theographic.py:14-17`·`load_books.py:14` 등 커밋 SHA 고정 없이 raw 다운로드. 업스트림 변경 시 재시드 변질 또는 `KeyError` 중단.

**절 본문 프리베이크가 빌드타임 getbible 외부 호출 의존 (잔존):** `generate_verse_text.py`의 UA 403 우회 필요.

**kiwipiepy — requirements 미등록 빌드타임 의존 (잔존):** 위 Data Pipeline 절 참조.

**Neo4j 이미지 메이저 버전만 고정 (잔존):** `docker-compose.yml:3` `image: neo4j:5`.

**ESLint 계열 caret 범위 (잔존):** `frontend/package.json`의 `eslint-plugin-react-hooks: "^7.1.1"` 등 — 규칙 추가가 파이프라인 변경 없이 lint 결과를 흔들 수 있다(이번 5건 중 `react-hooks/refs`도 7.x 신규 규칙 계열). lint 미게이팅이라 배포는 안 막히지만 "0 유지" 목표가 조용히 무너지는 구조.

---

## Test Coverage Gaps

- `*.test.*`/`*.spec.*` 0건, pytest/vitest 설정 전무, `frontend/package.json` scripts에 test 없음 — 이번 재확인에서도 동일.
- 데이터 검증 스크립트 4종은 CI 미연결·수동 실행 의존. `data/authored_persons/`(1,060명)는 validate 스크립트 자체가 없음.
- 특히 위험 높은 미검증 지점:
  - **사건–책 연결 ↔ event_verses 권 집합 일치** — task#203이 실측으로 21건을 찾았고 4건이 원칙적 잔존인데, 이 대조를 자동화한 스크립트가 없다(신규 저작 사건마다 재발 가능).
  - wip 계약(가족 간선만·검색 제외)이 `__main__` 배선+검색 WHERE 한 줄에 분산 — 자동 검증 없음.
  - slug 소스 5계열(person_events 파일명·`_ERA`·relations endpoint·god_reliance 파일명·seal_slugs.json)의 일치 강제 스키마·테스트 없음(이번 수기 기계검증은 통과).
  - `ERA_BANDS`(프론트) ↔ `_ERA_ORDER`(백엔드) 8구간 정합은 주석 약속뿐.
  - BC/AD 연도 파싱 다중 사본 중 assert는 `load_books.py` 하나뿐.
  - date_corrections 롤백·저작 계보/어머니 간선 소실·wip status 드리프트는 자동 감지되지 않는다.
- UI 검증은 Playwright 수동 실행 의존, CI 미연동. 모바일 시트류는 "긴 콘텐츠 스크롤 후 조작" 케이스를 UAT에 포함해야 함(task#202에서 개폐만 확인한 전수 UAT 통과 후 실기기 결함 3건 재작업 실증). SPA 해시 특성상 딥링크 검증은 URL마다 새 브라우저 컨텍스트, 테마 검증은 localStorage `biblemap-theme` 주입 경로.
- ESLint는 실행되나 CI/`deploy.sh` 미게이팅 — 0 복원(`24e8365`) 하루 만에 5건 재파손이 이 갭의 실증.
