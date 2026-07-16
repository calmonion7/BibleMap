---
last_mapped_commit: 23e41eee5bbfdd1fbd7a942d7fb14b1df1620d3d
mapped: 2026-07-16
---

# CONCERNS

현재 코드베이스에서 확인된 기술 부채·버그 위험·보안·성능·취약 지점 목록. 각 항목은 HEAD(`23e41ee`)에서 실제 파일·라인으로 재확인했다.

이번 갱신 배경: 직전 매핑(`e53ec23`, 2026-07-14) 이후 하나님 의존도 기능 전체(데이터+API+UI, task#178~188)와 모션 시스템 개편 3부작(task#189~191)이 들어왔다. `.forge/bug-report.md`(task#150, 2026-07-10)의 confirmed 12건 중 백엔드 9건(#1~#9)은 이번 재확인에서 **전부 해소** 확인(코드 재추적으로 검증) — 프론트 상태 3건(#10~#12)은 미착수로 잔존. maplibre `easeTo` `offset:undefined` 데스크톱 크래시(2026-07-16 발견 당일 수정, `frontend/src/MapView.jsx:207-209` 주석 참조)도 해소되어 이 문서에서 다루지 않는다. 신규로는 사용되지 않는 `word_verse_index` 오버레이(빌드는 되지만 어떤 라우트도 소비하지 않음), ESLint 상태 악화(1 warning → 4 errors + 1 warning), 큐레이션 slug 규약의 소비처 확산(3곳)을 기록했다.

---

## bug-report.md 사후 검증 — 백엔드 9건 해소, 프론트 3건 잔존

`.forge/bug-report.md`(task#150)가 confirmed로 남긴 12건을 코드로 재추적한 결과:

**해소됨(#1~#9, 백엔드) — 이번 재확인으로 확정:**
- #1 오버레이 파일부재 무음: `backend/app/overlays.py:20`·`:30`이 이제 `logger.warning`으로 두 후보 경로를 모두 남긴다.
- #2 load_books.py 재시드 시 월/일 정밀도 startDate 누락: `backend/scripts/load_books.py:56-67` `_parse_year`가 부호 분리 후 `.split("-")[0]`만 정수화하는 공유 규칙으로 교체되고, 회귀 방지 self-check assert 5개(`:72-76`)가 붙었다.
- #3 `/event/{id}/verses` 정경순 미보장: `backend/app/routes/events.py:131` `enriched_books.sort(key=lambda b: b.get("bookOrder", 0))`로 라우트에서 방어적 정렬.
- #4 Book topEvents가 회고 인용과 실제 발생을 미구분: `backend/app/routes/nodes.py:243-244` Cypher가 `WHERE ... rel.primary`로 발생 관계만 취합(`primary` 플래그는 `load_books.py:134-142`·`load_person_events.py:72-83`이 이미 세팅).
- #5 `_build_connections` 무제한 lru_cache: `backend/app/routes/persons.py:222` `maxsize=256`으로 교체.
- #6 `_place_to_persons`가 occursAt 전체 인덱스를 검사해 journey.py(occursAt[0]만 정차지)와 판정 불일치: `backend/app/routes/places.py:34`가 이제 `(evt.get("occursAt") or [None])[0] == place_id`로 첫 인덱스만 검사(주석에 명시적 통일 근거).
- #7 `_place_to_persons` 무제한 lru_cache: `places.py:21` `maxsize=256`.
- #8 tours `_build_event_index` eventId 충돌 무경고 덮어쓰기: `backend/app/routes/tours.py:70-72`이 이제 `logger.warning`으로 중복을 남긴 뒤 덮어쓴다.
- #9 relations.json approxYear 비정수(-1897.5): 전량(627국면) 재검사 결과 비정수 0건 — 정수로 정정됨.

**잔존(#10~#12, 프론트 상태) — 미착수:**
- #10 `frontend/src/useNodeSelection.js:33-39` `selectNode`/`handleNodeLoaded`가 노드 타입 무관 `setPersonEventIds(null)`을 호출해, 인물 탐험 중 지도의 비인물 노드(장소 등) 클릭 한 번으로 타임라인 인물 필터가 조용히 풀린다.
- #11 `frontend/src/PersonHub.jsx`·`frontend/src/useStageNavigation.js:37`가 `/persons/curated`를 각자 독립 fetch — 완료 시점이 어긋나면 `navSyncRef` 미초기화로 이후 히스토리 기록이 push 대신 replace로 잘못 처리될 수 있다.
- #12 `useStageNavigation.js:57`의 딥링크 복원 게이트(`if (!curatedIds || restoredRef.current) return`)가 인물 slug 해석이 필요 없는 `#/books`·`#/tours` 분기까지 감싸, curated API가 최종 실패하면 어떤 딥링크도 복원되지 않는다.

세부 재현 경로·제안 수정방향은 `.forge/bug-report.md` #10~#12 참조.

---

## Cache & Reload-Order Footguns

가장 조용히(에러 없이) 잘못된 상태를 만드는 부류. 캐시 무효화 수단이 사실상 **`api` 컨테이너 재시작뿐**이고, 재적재 순서를 빠뜨리면 파생 레이어가 소실된다.

**인메모리 캐시 무효화 = `api` 재시작뿐 (`lru_cache` 산재, 하나님 의존도 기능으로 다수 추가):**
- `backend/app/overlays.py` **7개** lru_cache(maxsize=1) — 기존 5개(`book_events_raw`·`event_verses`·`bible_verses`·`word_distribution`·`books_ko`)에 `word_verse_index`(`:76`)·`verse_persons`(`:83`)가 신규 추가.
- `backend/app/routes/reliance.py`도 **5개** 신규 lru_cache — `_alias_to_bb`(`:27`, maxsize=1)·`_slug_to_id`(`:48`)·`_id_to_slug`(`:67`)·`_load_entries`(`:72`, maxsize=None이나 키가 god_reliance 파일 32개로 상한됨)·`_all_percents`(`:91`).
- `data/`는 `docker-compose.yml:19-20`에서 api 컨테이너에 **볼륨 마운트**라 파일 수정에 이미지 재빌드는 불필요하지만, 실행 중 프로세스는 이전 값을 계속 서빙한다. 무효화 API·TTL·mtime 감시가 없어 반영은 `docker compose -p biblemap restart api`뿐 — 인물별 하나님 의존도 데이터(`data/god_reliance/*.json`)를 저작 중 반복 수정한 이번 기능(task#182~188에서 실제로 여러 차례 재조정)에서도 매번 재시작이 필요했을 것.
- **API 응답 자체는 `Cache-Control: public, max-age=3600`이 붙어 브라우저에도 1시간 캐시된다**(`reliance.py:154`·`:174`, `verses.py:47`) — `frontend/src/api.js:12`의 `?v=` 빌드 ID 부착(신규, `e679df9`)으로 배포 직후 브라우저 캐시 문제는 해소됐지만, api 프로세스 자체의 lru_cache 무효화(재시작)와는 별개 계층이라 "재시작했는데 안 바뀐다"는 이제 발생하지 않아도 "재배포했는데 옛 데이터가 보인다"는 여전히 재시작 누락이 원인일 수 있다.

**`load_theographic.py` 전체 재실행이 교정·파생 레이어를 되돌린다:**
- 원본을 통째 재적재하면 노드 속성이 GitHub 원본(Ussher 연대계) 값으로 덮여 `backend/scripts/inject_date_corrections.py`를 **반드시 재실행**해야 한다(`README.md:25-27`, ADR-0014).
- 그래프 초기화 후 재적재 시 마태1 저작 계보 간선도 소실 → `backend/scripts/load_authored_genealogy.py` 재실행 필요(ADR-0019). 가법적 MERGE라 노드 속성은 안 건드린다.
- `load_theographic.py`는 wip 마킹까지 담당 — `load_people`이 `p.status = row.status`로 wip/null을 SET하고, 가족 폐포·큐레이션 rec 시드를 `__main__`에서 배선한다. 다른 경로로 Person을 재적재하면 status 마킹이 어긋나 검색 오염 또는 과잉 은닉이 생길 수 있다.
- **README·deploy.sh 어디에도 `load_authored_genealogy.py`가 등록돼 있지 않다** — `README.md:20-22`의 적재 순서는 `load_theographic → inject_ko_names → inject_date_corrections`까지만, `deploy.sh`는 `inject_ko_names.py` 하나만(`:52`). 재적재 순서의 정본 문서가 없다.

---

## Wip Person Data Handling (ADR-0021/0022)

가족 폐포로 적재된 wip 인물(약 900+명)은 "노드+가족 간선만, 검색 제외"가 설계 계약인데, 이 계약이 코드 전반에 **분산·암묵적으로** 구현돼 있다.

**계약이 함수가 아니라 `__main__` 배선으로만 보장:**
- `backend/scripts/load_theographic.py`의 `family_closure_wip` docstring이 스스로 명시 — 이 제약은 실행 경로가 아니라 `__main__`의 배선으로 보장된다. `load_people`·`load_parent_child_rels` 등 개별 함수엔 wip 가드가 없어, 함수를 다른 배선으로 호출하면 계약이 조용히 깨진다.

**wip 필터가 검색에만 있고 이웃·가계도엔 없다:**
- `backend/app/routes/search.py:19`의 `AND (n.status IS NULL OR n.status <> 'wip')`가 유일한 wip 필터. `backend/app/routes/nodes.py`의 이웃 쿼리(`:121`·`:173`)와 `backend/app/routes/family.py`의 트리 구성엔 wip 구분이 없다 — 의도된 동작(가계도 혈통 완전성)이지만, 가계도에서 wip 인물을 클릭하면 SidePanel이 가족 외 데이터가 없는 빈약한 화면이 된다.

**큐레이션 rec 시드 규약이 이제 3개 소비처가 의존하는 단일 실패점:**
- `curated_person_ids()`(`load_theographic.py:37-50`)가 "큐레이션 인물의 정식 id = `data/person_events/<slug>.json`의 `events[0].participants[0]`" 규약으로 시드를 뽑는다. 같은 규약을 `backend/app/routes/places.py:41`(`_place_to_persons`)과 신규 `backend/app/routes/reliance.py:62-63`(`_slug_to_id`)도 각자 재구현해 의존한다. person_events 파일의 첫 사건 participants 순서를 바꾸면 세 소비처가 동시에 조용히 어긋난다 — 이 규약을 검증하는 스키마·테스트·공유 헬퍼가 없다.

---

## Genealogy / Graph-Derived Concerns

**SidePanel "이웃"에 부모가 부모·자식으로 이중 표시 (잔존):**
- 부모-자식이 상호 간선(`PARENT_OF`+`CHILD_OF`)으로 MERGE되는데(`backend/scripts/load_theographic.py`·`load_authored_genealogy.py`), 이웃 쿼리는 무방향 — `backend/app/routes/nodes.py:121`(`get_node_neighbors_grouped`)·`:173`(`get_node`) 모두 `MATCH (n {...})-[r]-(m)`. 같은 인물이 "부모"와 "자식"으로 2회 노출된다. 방향성/디듀프 미도입.

**하나님(God)이 계보상 "아버지"로 라벨 (잔존):**
- theographic에서 아담의 father 링크가 God을 가리키고 gender가 Male이라, `frontend/src/FamilyTree.jsx:86`의 `roleLabel`이 조상 세대+Male → "아버지"로 표시. 인물 연결 축(`persons.py:239` `_build_connections`의 co_participants)은 `p2.name <> 'God'`로 명시 제외하지만 가계도 트리엔 동등 필터가 없다.

**동명이인 위험 — 이름 기반 해석의 구조적 함정 (ADR-0017/0018/0021):**
- 같은 nameKo의 다른 인물이 복수 존재(야고보 3인·유다 3인 등). keyPeople은 `data/keypeople/identity.json`으로 저작 시점 고정(ADR-0018), 계보 이관은 양방향 앵커 고정점 방식으로 해소했으나, 새 이름 기반 링크를 추가할 때마다 동명이인을 데이터로 못박아야 한다. 자동 퍼지 매칭은 오링크를 조용히 만든다.

**theographic `children` 배열은 출생순이 아니다:**
- 출생 순서는 그래프에서 파생 불가 — 유일한 정본은 `data/person_relations/relations.json`의 role 라벨(`backend/app/routes/family.py:32-59` `_family_role_pairs`가 읽어 전달, `FamilyTree.jsx:78`이 role 우선·gender 폴백). role 없는 형제 집합은 UI가 순서를 보증하지 못한다.

---

## Data Pipeline Footguns

**`load_books.py` 재실행이 교정 연대를 Ussher 값으로 롤백:**
- 매 실행 GitHub 원본(`BOOKS_URL`/`EVENTS_URL`)을 새로 받아 Book `startYear`/`endYear`를 재계산·덮어쓴다. date_corrections 적용 후 재실행하면 책 연도가 교정 전으로 롤백.

**Person `birthYear`/`deathYear`는 Ussher 연대 잔존:**
- ADR-0014로 Event 연대는 보수계로 이동했으나 Person 생몰년은 미재정렬. 현재 UI 미노출이라 잠재적이지만 surfacing 시 한 화면에서 연대계가 어긋난다.

**연대 검증 화이트리스트는 3쌍만 하드코딩:**
- `backend/scripts/validate_event_chronology.py:55`의 `THEOLOGICAL_WHITELIST`는 3쌍. 잔존 raw 위반 4건(Adam·Seth·Terah·John the Baptist)은 문서로만 소명.

**Event `startDate`는 혼재 형식 문자열 — 사전순 정렬 금지:**
- 연도만·연-월·제로패딩 연-월-일 혼재, BC는 음수 접두. 파싱 로직 다중 중복(아래 Fragile Areas).

**시드 스크립트 실행 순서 암묵적, 정본화된 문서 없음:**
- `backend/scripts/`에 `__init__.py` 제외 **33개** 스크립트(직전 매핑 대비 `build_verse_persons.py`·`build_word_verse_index.py`·`validate_god_reliance.py` 3개 신규). `load_person_events.py` 등은 기존 Book/Place 노드를 `MATCH`로 참조 — 순서가 틀리면 관계가 0건으로 조용히 누락(에러 없음).

**단어 분포·의존도 파이프라인이 수동 큐레이션·미등록 의존성에 결합:**
- `backend/scripts/build_word_distribution.py`·`build_word_verse_index.py`는 kiwipiepy가 필요한데 `backend/requirements.txt`(fastapi·neo4j·uvicorn뿐)에 없다 — docstring이 `/tmp` venv 수동 설치를 안내하는 빌드타임 전용 의존. `data/god_reliance/*.json`(32인)은 `data/god_reliance/AUTHORING.md` 규약에 따른 수동 저작이며, `validate_god_reliance.py`가 스키마(mode 통제어휘·approxYear 정수·verse 해석 가능 등)를 검사하지만 **CI 미연결·수동 실행 의존**(아래 Test Coverage Gaps).

---

## Tech Debt

**시드 파이프라인이 `deploy.sh`와 단절 (재현성 최대 리스크):**
- `deploy.sh`의 주입 단계는 `inject_ko_names.py`(`:52`) **하나만** 재실행. 모든 `load_*`·나머지 `inject_*`·`build_word_distribution.py`·`build_verse_persons.py`·`build_word_verse_index.py`는 배포에 미포함. Neo4j 볼륨이 살아있는 한 문제없지만 볼륨 삭제·신규 서버 시 전체 재적재+교정 재주입+wip 폐포+저작 계보+구절 색인류를 수동 재현해야 하고 그 정본 순서 문서가 없다.
- 부수: `deploy.sh` 로그 단계 라벨이 `[1/3]`(`:34`)·`[2/3]`(`:40`)·`[3/4]`(`:45`)·`[4/4]`(`:49`)로 어긋나 있다(코스메틱, 잔존).

**번들 크기 경고 — maplibre 청크가 500kB 한계 초과 (잔존, 수치 재확인):**
- `frontend/vite.config.js:12-21`의 `manualChunks`가 maplibre/vendor를 분리하지만, 분리된 maplibre 청크 자체가 **약 1.03MB**(`npm run build` 실측 `maplibre-*.js` 1,027.60 kB)로 Vite 기본 `chunkSizeWarningLimit`(500kB)를 초과 — 매 빌드 경고. maplibre-gl 특성상 축소 여지가 작아 lazy import 또는 경고 한계 명시가 남은 선택지.

**사용되지 않는 오버레이 — `word_verse_index` 오버레이가 어떤 라우트도 소비하지 않음 (신규 발견):**
- `backend/scripts/build_word_verse_index.py`가 산출하는 `data/word_verse_index/index.json`(1.7MB, lemma→verseID 역색인)을 `backend/app/overlays.py:76` `word_verse_index()`가 lru_cache로 로드하지만, 전체 백엔드·프론트엔드 어디에도 `word_verse_index()` 호출부가 없다(grep 0건). `backend/app/routes/words.py`의 단어→구절 검색은 여전히 구식 substring 전수 스캔(아래 Performance Bottlenecks)을 쓰고 있어, kiwipiepy 형태소 분석 인프라를 새로 만들었음에도 실제로 배선되지 않은 상태 — 빌드·유지 비용만 지고 이득이 없는 죽은 데이터/코드.

**대형 프론트엔드 컴포넌트 (라인 수 갱신):**
- `frontend/src/SidePanel.jsx` — 823줄. `frontend/src/App.jsx` — 684줄(직전 666, 모션 개편으로 소폭 증가). `frontend/src/RelianceView.jsx` — **449줄(신규 대형 컴포넌트)**. `frontend/src/PersonHub.jsx` — 387줄. `frontend/src/TimelineView.jsx` — 306줄, `frontend/src/BibleOverviewView.jsx` — 312줄, `frontend/src/WordDistributionView.jsx` — 217줄.

**"큐레이션 13인" 주석 드리프트 잔존:**
- `backend/app/routes/persons.py:1`·`:137`의 "13인", `:288`의 "34인"이 실제 `_ERA` **35 slug**·`data/person_events/` 35개 json과 계속 어긋남.

---

## Known Bugs

**ESLint 상태 악화 — 1 warning → 4 errors + 1 warning (신규 확인):**
- `npm run lint`(=`eslint .`) 실측 결과 문제 5건으로 늘었다: `frontend/src/FamilyTree.jsx:97`·`frontend/src/RelianceView.jsx:89`·`frontend/src/WordDistributionView.jsx:81`이 `react-hooks/set-state-in-effect`(effect 본문에서 동기 setState 호출 금지, `eslint-plugin-react-hooks@7.1.1`)를 위반, `frontend/src/api.js:7`은 vite `define`으로 주입되는 `__BUILD_ID__`(cache-busting, `e679df9`)를 eslint 전역으로 등록하지 않아 `no-undef`. `frontend/src/MapView.jsx:63`의 기존 `exhaustive-deps` 경고는 그대로. `frontend/package.json`의 lint 스크립트를 CI/`deploy.sh` 어디도 게이팅하지 않아 배포 자체는 막히지 않지만, 실질적으로 lint가 깨진 채 방치되는 상태.

**topEvents "대표성 절단" 편향 잔존:**
- `backend/app/routes/nodes.py:271-276` Book 분기 — 발생/인용 구분(`rel.primary`)은 해소됐지만, 연도 오름차순 + `[:10]` 하드 절단은 그대로라 사건 많은 책은 초반부 10개에 몰린다(ADR-0012 범위 밖 명시).

**서신서 Book 연대 범위 오표기 (수용된 한계):**
- "첫 참조=발생" 휴리스틱이 서신서의 회고 인용에 오판정. authored_events 경로가 없는 책이라 근본 해소 불가.

---

## Security Considerations

**CORS `allow_origins=["*"]`:**
- `backend/app/main.py:47`. `allow_methods=["GET"]`·`allow_credentials=False`로 읽기 전용 제한. 신규 `reliance`·`verses` 라우터도 동일 미들웨어 하위라 예외 없음. 공개 읽기 API라 즉각 위험 낮으나 쓰기·인증 추가 시 오리진 화이트리스트 필요.

**Neo4j는 127.0.0.1에만 바인딩 (양호):**
- `docker-compose.yml:4-6` 루프백 노출, api는 내부 네트워크(`bolt://neo4j:7687`). 인증은 `NEO4J_AUTH=neo4j/${NEO4J_PASSWORD:?...}` 필수화(`:10`).

**시크릿 취급 (양호):**
- `.env`는 `.gitignore` 제외. 하드코딩 시크릿 0건. 인증/세션 계층 자체가 없음(공개 읽기 서비스).

**Cypher 인젝션 표면 (현재 방어됨):**
- `search.py`의 `q`, `words.py`의 `w`, `verses.py`의 `verse_id`(`session.run(..., ids=rec_ids)` 파라미터 바인딩) 모두 파라미터/파이썬 레벨 처리. `nodes.py` f-string 삽입은 상수뿐.

**사용자 제어 키 lru_cache — 남은 것은 유한 상한뿐 (bug-report #5/#7 해소 후 잔존 리스크):**
- `persons.py:222`·`:285`, `places.py:21`의 `maxsize=256`은 무한 누적을 막지만, 임의 문자열을 키로 받는 구조 자체는 남아 있어 서로 다른 256개 이상의 고유 요청이 반복되면 캐시가 스래싱(정상 값 축출)될 여지가 있다(약한 잔존 리스크, DoS는 아님). `reliance.py`의 `_load_entries(slug)`는 `maxsize=None`이지만 `slug`가 라우트에서 직접 오지 않고 `_id_to_slug().get(person_id)`로 화이트리스트된 32개 값만 통과해 도달 불가.

---

## Performance Bottlenecks

**`/words/{book}/verses` — 매 요청 31,103절 전수 substring 스캔 (잔존, kiwipiepy 인프라 미활용):**
- `backend/app/routes/words.py:32-37`가 요청마다 `overlays.bible_verses()`(31,103 엔트리, `data/bible/verses.json` 9.8MB) 전체를 순회하며 `w in text` 검사. 결과 캐시 없음, 매칭 전량을 리스트에 모은 뒤 200개(`VERSE_LIMIT`) 절단. `w`는 strip 외 검증 없어 한 글자 입력도 전수 스캔을 유발. lemma 기반 역색인(`word_verse_index`)이 이미 빌드돼 있는데도(위 Tech Debt) 이 라우트가 그걸 쓰지 않아, 인프라 투자 대비 실제 성능 개선이 이뤄지지 않았다.

**대용량 오버레이 JSON 전체 인메모리 상주 (수치 갱신, 신규 2개 추가):**
- `data/bible/verses.json`(9.8MB)·`data/event_verses/events.json`(2.1MB)·`data/word_distribution.json`(280KB)에 더해 **`data/word_verse_index/index.json`(1.7MB, 미사용)**·**`data/verse_persons/index.json`(857KB)**가 `overlays.py` lru_cache(maxsize=1)로 프로세스당 상주. `backend/Dockerfile:6` uvicorn 단일 워커라 현재는 잠재적이나 워커 다중화 시 배증. word_verse_index는 아무도 안 쓰는 채로 메모리만 차지.

**`_build_id_to_slug()`에 캐시 없음 (잔존):**
- `backend/app/routes/journey.py:18`이 `lru_cache` 없이 요청마다 `_ERA` 35개 slug JSON을 open/parse. `tours.py`도 투어 상세마다 재호출.

**전역 노드 스캔 검색 (잔존):**
- `backend/app/routes/search.py`: `MATCH (n) WHERE ... CONTAINS ...` — 라벨·인덱스 미사용 전수 스캔.

---

## Fragile Areas

**SPA 해시 라우팅 — same-document 해시 이동에 미반응 (구조 확인, 잔존):**
- `frontend/src/useStageNavigation.js`는 초기 해시를 마운트 시 1회만 캡처·파싱하고, `hashchange` 리스너가 어디에도 없다. 이미 로드된 문서에서 주소창 해시만 바꾸면 스테이지가 전환되지 않는다. 사용자 딥링크는 신선 로드라 정상 동작하지만, Playwright 등 자동화가 `goto`로 해시만 바꾸면 거짓 음성/양성을 만든다 — URL마다 새 브라우저 컨텍스트가 정석.

**`startDate`/연도 파싱·표기 로직 다중 중복 (잔존):**
- `frontend/src/dates.js` `parseYear`, `backend/app/routes/nodes.py:260-269` `_year`, `backend/scripts/load_books.py:56-67` `_parse_year`, `backend/scripts/validate_event_chronology.py` `_year`, `frontend/src/RelationsView.jsx` BC/AD 라벨, `backend/app/routes/reliance.py`·`backend/scripts/validate_god_reliance.py`의 approxYear는 이미 정수라 별도 파싱 없음. 공유 모듈 미추출, 회귀 assert는 `load_books.py`에만.

**인물 관계·의존도가 `slug` 문자열 매칭에 의존 (잔존, 소비처 확산):**
- `data/person_relations/relations.json` endpoint는 `{nameKo, slug}`만 담고 `persons.py:288` 부근이 `slug_to_id`로 `withId` 해결. `reliance.py:48-64` `_slug_to_id()`도 동일 패턴(person_events participants[0])을 독립 재구현. slug 오타·drift 시 여정 점프·의존도 조회가 `null`/`available:false`로 조용히 실패. 3개 이상의 slug 소스(파일명·`_ERA`·relations endpoint·god_reliance 파일명) 일치를 강제하는 스키마·테스트 없음.

**가계도 role 라벨이 nameKo 문자열 매칭에 의존 (잔존):**
- `backend/app/routes/family.py:32-59`가 "가족" 관계를 `frozenset({nameKoA, nameKoB})` 키로 매핑. nameKo 표기가 큐레이션과 그래프에서 어긋나면 role이 조용히 누락돼 gender 폴백.

**오버레이 빈값 폴백이 하류에서 500으로 표출:**
- `backend/app/overlays.py:34-43`은 파일 없음/파싱 실패 시 경고 후 빈 dict 폴백인데, `backend/app/routes/words.py:27-29`는 `books_ko()`가 비면 `book_ids.index(book_id)`가 ValueError → 500.

**관계 뷰·의존도 뷰의 어휘가 프론트 상수와 암묵 결합:**
- `frontend/src/RelationsView.jsx`의 `TYPE_ICON`·`TYPE_ORDER`, `frontend/src/theme.js:26` `VALENCE_COLOR`, `frontend/src/WordDistributionView.jsx`의 polarity 매핑, 신규 `frontend/src/RelianceView.jsx`의 `MODE_META`·`SEGMENT_ORDER`·`STEP_LABELS`가 데이터 값과 하드코딩 짝. `data/god_reliance/*.json`의 mode/kind 통제어휘가 바뀌면 `validate_god_reliance.py`는 잡아도 프론트 매핑 갱신은 별도 수작업.

**Neo4j 인덱스 생성 실패해도 서비스 계속 기동 (잔존):**
- `backend/app/main.py:37-38`: `except Exception:` 후 계속 기동 — 전수 스캔 성능 저하만 남는다.

**프론트 stale 응답 무효화의 수동 관리 (잔존):**
- `cancelled`/AbortController 플래그 + id 비교 패턴이 `SidePanel.jsx`·`WordDistributionView.jsx`·`RelianceView.jsx`·`useStageNavigation.js`에 반복 구현. 공유 훅 미추출.

**성품 통제 어휘가 문서·코드 이중 관리 (잔존):**
- `backend/scripts/validate_traits.py`의 `VIRTUES`/`FLAWS`가 `data/character_traits/AUTHORING.md §3`을 코드로 복제 — 한쪽만 고치면 어긋난다. 동일 이중관리 패턴이 `validate_god_reliance.py`의 `MODES`/`KINDS`와 `data/god_reliance/AUTHORING.md`에도 신규로 존재.

---

## Deployment / Ops Risks

**프론트 `:8080`은 `frontend/dist` 정적 마운트 — HMR 아님:**
- `docker-compose.yml:30` `./frontend/dist:...:ro`. 소스만 고치고 `npm run build`를 안 하면 이전 빌드를 계속 서빙(에러 없음). `deploy.sh`는 빌드 수행(`:34-38`).

**API `:8000` 외부 미노출:**
- `docker-compose.yml`에 api host 포트 매핑 없음 — `nginx/nginx.conf`의 `location /api/`로만 접근.

**nginx 속도 제한 없음:**
- `nginx/nginx.conf`에 `limit_req_zone`/`limit_req` 미설정. `words.py` 전수 스캔과 겹치면 잔존 리스크 악화 조합.

---

## Scaling Limits

**단일 인스턴스 스택, 인메모리 캐시 공유 불가:**
- neo4j 1 + api 1(uvicorn 단일 워커, `backend/Dockerfile:6`) + nginx 1. `lru_cache`는 프로세스 로컬이라 다중 워커/컨테이너 확장 시 인스턴스별 중복·불일치(이번에 `overlays.py`·`reliance.py`에 캐시 함수가 더 늘어 상주 메모리 배증 폭도 커졌다). 무효화 수단이 앱 재시작뿐인 것도 그대로.

---

## Dependencies at Risk

**Theographic 데이터를 GitHub `master` HEAD에서 미고정 fetch (잔존):**
- `load_theographic.py`·`load_books.py`·`generate_*` 다수가 커밋 SHA 고정 없이 raw 다운로드. 업스트림 스키마 변경 시 재시드 변질 또는 `KeyError` 중단.

**절 본문 프리베이크가 빌드타임 getbible 외부 호출에 의존 (잔존):**
- `backend/scripts/generate_verse_text.py`의 UA 403 우회 필요.

**kiwipiepy — requirements 미등록 빌드타임 의존, 소비처 2개로 확대:**
- `build_word_distribution.py`·`build_word_verse_index.py` 둘 다 요구하나 `backend/requirements.txt` 미포함(의도된 빌드타임 전용). `/tmp` venv 수동 설치 안내가 docstring에만 있어 환경 재현이 사람 손에 달려 있다. 후자는 산출물이 애초에 소비되지 않아(위 Tech Debt) 이 의존을 감수할 실익이 현재 없다.

**Neo4j 이미지 메이저 버전만 고정 (잔존):**
- `docker-compose.yml:3` `image: neo4j:5` — 패치 고정 권장.

**`eslint-plugin-react-hooks` caret 범위(`^7.1.1`)가 lint 결과를 흔든다 (신규 관찰):**
- `frontend/package.json`의 `eslint-plugin-react-hooks: "^7.1.1"`는 마이너/패치 자동 승격 범위라, 규칙 추가(`set-state-in-effect` 등)가 배포 파이프라인 변경 없이도 조용히 lint 결과를 악화시킬 수 있다(위 Known Bugs 참조). lint가 CI 게이트가 아니라 당장 배포를 막지는 않지만, 버전을 좁히거나(`~`) lockfile 신뢰에 의존해야 재현성이 보장된다.

---

## Test Coverage Gaps

- `*.test.*`/`*.spec.*` 0건, pytest/vitest 설정 전무, `frontend/package.json` scripts에 test 없음.
- 데이터 검증 스크립트(`validate_traits.py`·`validate_event_chronology.py`·`validate_person_context.py`·**`validate_god_reliance.py`(신규)**)는 CI 미연결·수동 실행 의존.
- 특히 위험 높은 미검증 지점:
  - wip 계약(가족 간선만·검색 제외·큐레이션 rec 무마킹)이 `__main__` 배선+검색 WHERE 한 줄에 분산 — 자동 검증 없음.
  - `events[0].participants[0]` 파일 규약이 이제 `load_theographic.py`·`places.py`·`reliance.py` **3곳**에서 독립 재구현 — slug↔id 일치를 강제하는 스키마·테스트 없음.
  - `words.py`의 books_ko 순서↔verses.json BB 인덱스 계약은 빌드 스크립트 assert에만 의존.
  - BC/AD 연도 파싱 다중 사본 중 assert는 `load_books.py` 하나뿐.
  - date_corrections 롤백·저작 계보 소실·wip status 드리프트·god_reliance 스키마 위반은 자동 감지되지 않는다(마지막은 `validate_god_reliance.py`로 검사 가능하나 수동 실행해야만 트립).
- UI 검증은 Playwright 수동 실행(로컬)에만 의존, CI 미연동. SPA 해시의 same-document 한계로 딥링크 검증은 URL마다 새 브라우저 컨텍스트가 필수, 테마 검증은 `color_scheme`이 아니라 localStorage `biblemap-theme` 주입 경로여야 유효(`frontend/src/main.jsx:7`).
- ESLint는 실행되나(위 Known Bugs) CI/`deploy.sh` 어디에도 게이팅되지 않아 lint 실패가 배포를 막지 못한다.
