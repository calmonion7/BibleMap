---
last_mapped_commit: e53ec23d634a48d16bd1abf3e131c340cfbaac1f
mapped: 2026-07-14
---

# CONCERNS

현재 코드베이스에서 확인된 기술 부채·버그 위험·보안·성능·취약 지점 목록. 각 항목은 HEAD(`e53ec23`)에서 실제 파일·라인으로 재확인했다.

이번 갱신 배경: 직전 매핑(`8af8f05`) 이후 가족 폐포 wip 인물 적재(ADR-0021)·큐레이션 인물 rec 이관(ADR-0022)·라이트 테마(ADR-0020)·단어 분포 페이지(task#176/177)가 들어왔다. wip 인물 처리, `words` 라우트의 전수 스캔, 번들 크기 경고, SPA 해시 라우팅의 same-document 한계를 신규/보강 기록했고, 기존 항목은 현행 라인으로 재검증해 유지했다.

---

## Cache & Reload-Order Footguns

가장 조용히(에러 없이) 잘못된 상태를 만드는 부류. 캐시 무효화 수단이 사실상 **`api` 컨테이너 재시작뿐**이고, 재적재 순서를 빠뜨리면 파생 레이어가 소실된다.

**인메모리 캐시 무효화 = `api` 재시작뿐 (`lru_cache` 산재, 이번에 2개 추가):**
- 오버레이 JSON과 파생 데이터는 프로세스 로컬 `lru_cache`로 1회 로드 후 상주 — `backend/app/overlays.py` **5개**(`book_events_raw`·`event_verses`·`bible_verses`·**`word_distribution`**·**`books_ko`**, `:46`·`:52`·`:58`·`:64`·`:70`), `backend/app/routes/events.py` 3개(`:11`·`:53`·`:98`), `backend/app/routes/tours.py` 2개(`:30`·`:55`), `backend/app/routes/persons.py` 다수(`:101`·`:145`·`:156`·`:167`·`:274` maxsize=1, `:222`·`:285` maxsize=256), `backend/app/routes/places.py:21`(256), `backend/app/routes/family.py:31`(`_family_role_pairs`, maxsize=1).
- `data/`는 `docker-compose.yml:20`에서 api 컨테이너에 **볼륨 마운트**라 파일 수정에 이미지 재빌드는 불필요하지만, 실행 중 프로세스는 이전 값을 계속 서빙한다. 무효화 API·TTL·mtime 감시가 없어 반영은 `docker compose -p biblemap restart api`(또는 `up -d api`)뿐. "오버레이를 고쳤는데 안 바뀐다"의 첫 번째 용의자(2026-07-14 rec 이관 작업에서도 재확인 — 재빌드 불요·재시작만 필요였음, `.forge/retro/2026-07-14-curated-person-rec-migration.md`).

**`load_theographic.py` 전체 재실행이 교정·파생 레이어를 되돌린다:**
- 원본을 통째 재적재하면 노드 속성이 GitHub 원본(Ussher 연대계) 값으로 덮여 `backend/scripts/inject_date_corrections.py`를 **반드시 재실행**해야 한다(`README.md:26–27`, ADR-0014).
- 그래프 초기화 후 재적재 시 마태1 저작 계보 간선도 소실 → `backend/scripts/load_authored_genealogy.py` 재실행 필요(스크립트 docstring `:9–10`, ADR-0019). 가법적 MERGE라 노드 속성은 안 건드린다.
- **(NEW)** `load_theographic.py`는 이제 wip 마킹까지 담당한다 — `load_people`(`:100–131`)이 `p.status = row.status`로 wip/null을 SET하고, 가족 폐포(`family_closure_wip`, `:53–80`)·큐레이션 rec 시드(`curated_person_ids`, `:37–50`)를 `__main__`(`:356–374`)에서 배선한다. 다른 경로로 Person을 재적재하면 status 마킹이 어긋나 검색 오염(wip 노출) 또는 과잉 은닉이 생길 수 있다.
- **README·deploy.sh 어디에도 `load_authored_genealogy.py`가 등록돼 있지 않다** — `README.md:20–22`의 적재 순서는 `load_theographic → inject_ko_names → inject_date_corrections`까지만, `deploy.sh`는 `inject_ko_names.py` 하나만(`:52`). 재적재 순서의 정본 문서가 없다.

---

## Wip Person Data Handling (ADR-0021/0022)

가족 폐포로 적재된 wip 인물(약 900+명)은 "노드+가족 간선만, 검색 제외"가 설계 계약인데, 이 계약이 코드 전반에 **분산·암묵적으로** 구현돼 있다.

**계약이 함수가 아니라 `__main__` 배선으로만 보장:**
- `backend/scripts/load_theographic.py`의 `family_closure_wip` docstring(`:57–61`)이 스스로 명시 — "이 제약은 실행 경로가 아니라 __main__의 배선으로 보장된다". `load_people`·`load_parent_child_rels` 등 개별 함수엔 wip 가드가 없어, 함수를 다른 배선으로 호출하면(예: memberOf·사건 간선에 `family_people`을 넘기면) 계약이 조용히 깨진다.

**wip 필터가 검색에만 있고 이웃·가계도엔 없다:**
- `backend/app/routes/search.py:19`의 `AND (n.status IS NULL OR n.status <> 'wip')`가 유일한 wip 필터. `backend/app/routes/nodes.py`의 이웃 쿼리(`:121`·`:173`)와 `backend/app/routes/family.py`의 트리 구성엔 wip 구분이 없다 — 의도된 동작(가계도 혈통 완전성)이지만, 가계도에서 wip 인물을 클릭하면 SidePanel이 가족 외 데이터가 없는 빈약한 화면이 된다. 유명 wip 인물(압살롬 등)의 검색 노출 재검토는 후속 후보로 열려 있음(`.forge/retro/2026-07-14-genealogy-wip-family-closure.md`).

**큐레이션 rec 시드가 파일 규약에 암묵 의존:**
- `curated_person_ids()`(`load_theographic.py:37–50`)가 "큐레이션 인물의 정식 id = `data/person_events/<slug>.json`의 `events[0].participants[0]`" 규약으로 시드를 뽑는다. person_events 파일의 첫 사건 participants 순서를 바꾸면 시드가 조용히 어긋난다(에러 없음). 이 규약을 검증하는 스키마·테스트 없음.

---

## Genealogy / Graph-Derived Concerns

**SidePanel "이웃"에 부모가 부모·자식으로 이중 표시 (잔존):**
- 부모-자식이 상호 간선(`PARENT_OF`+`CHILD_OF`)으로 MERGE되는데(`backend/scripts/load_theographic.py:180–199`, `load_authored_genealogy.py`) 이웃 쿼리는 무방향 — `backend/app/routes/nodes.py:121`(`get_node_neighbors_grouped`)·`:173`(`get_node`) 모두 `MATCH (n {...})-[r]-(m)`. 같은 인물이 "부모"와 "자식"으로 2회 노출된다. 방향성/디듀프 미도입(retro 2건에서 후속 후보로 반복 기록).

**하나님(God)이 계보상 "아버지"로 라벨 (잔존):**
- theographic에서 아담의 father 링크가 God을 가리키고 gender가 Male이라, `frontend/src/FamilyTree.jsx:77–86`의 `roleLabel`이 조상 세대+Male → "아버지"(`:86`)로 표시. 인물 연결 축(`persons.py`의 co_participants/contemporaries)은 God을 명시 제외하지만 가계도 트리엔 필터 없음.

**동명이인 위험 — 이름 기반 해석의 구조적 함정 (ADR-0017/0018/0021):**
- 같은 nameKo의 다른 인물이 복수 존재(야고보 3인·유다 3인, 룻=Ruth/Lud 표기 충돌 등). keyPeople은 `data/keypeople/identity.json`으로 저작 시점 고정(ADR-0018), 계보 이관은 양방향 앵커 고정점 방식으로 해소했으나(retro `2026-07-14-genealogy-wip-family-closure.md`), **새 이름 기반 링크를 추가할 때마다 동명이인을 데이터로 못박아야** 한다. 자동 퍼지 매칭은 오링크를 조용히 만든다. 검색 결과의 동명이인은 구분 정보 없이 나란히 노출된다(후속 후보).

**theographic `children` 배열은 출생순이 아니다:**
- 출생 순서("맏아들/둘째")는 그래프에서 파생 불가 — 유일한 정본은 `data/person_relations/relations.json`의 role 라벨(`backend/app/routes/family.py:31–59` `_family_role_pairs`가 읽어 전달, `frontend/src/FamilyTree.jsx:78`이 role 우선·gender 폴백). role 없는 형제 집합은 UI가 순서를 보증하지 못한다.

---

## Data Pipeline Footguns

**`load_books.py` 재실행이 교정 연대를 Ussher 값으로 롤백:**
- `backend/scripts/load_books.py`는 매 실행 GitHub 원본(`BOOKS_URL`/`EVENTS_URL`, theographic master raw, `:14–15`)을 새로 받아 Book `startYear`/`endYear`를 재계산·덮어쓴다. date_corrections 적용 후 재실행하면 책 연도가 교정 전으로 롤백. 우회 스크립트(`recompute_book_years.py`)는 레포에 커밋돼 있지 않다.

**Person `birthYear`/`deathYear`는 Ussher 연대 잔존:**
- ADR-0014로 Event 연대는 보수계로 이동했으나 Person 생몰년은 미재정렬. 현재 UI 미노출이라 잠재적이지만 surfacing 시 한 화면에서 연대계가 어긋난다.

**연대 검증 화이트리스트는 3쌍만 하드코딩:**
- `backend/scripts/validate_event_chronology.py:55`의 `THEOLOGICAL_WHITELIST`는 3쌍. 잔존 raw 위반 4건(Adam·Seth·Terah·John the Baptist)은 문서(계획 Non-goals·ADR-0014)로만 소명 — 리포트만 보면 맥락을 놓친다.

**Event `startDate`는 혼재 형식 문자열 — 사전순 정렬 금지:**
- 연도만·연-월·제로패딩 연-월-일 혼재, BC는 음수 접두. 파싱 로직 다중 중복(아래 Fragile Areas).

**시드 스크립트 실행 순서 암묵적:**
- `load_person_events.py`는 기존 Book/Place 노드를 `MATCH`로 참조 — 순서가 틀리면 관계가 0건으로 조용히 누락(에러 없음). `backend/scripts/`에 `__init__.py` 제외 **30개** 스크립트(직전 29 + `build_word_distribution.py`)가 있으나 정본화된 단일 실행 순서 문서가 없다.

**단어 분포 파이프라인이 수동 큐레이션·미등록 의존성에 결합:**
- `backend/scripts/build_word_distribution.py`는 kiwipiepy가 필요한데 `backend/requirements.txt`(fastapi·neo4j·uvicorn뿐)에 없다 — docstring(`:8–11`)이 `/tmp` venv 수동 설치를 안내하는 빌드타임 전용 의존. 절 본문(`data/bible/verses.json`)이 바뀌면 재실행 + **미분류 신규 단어를 `data/word_sentiment.json`에 수동 큐레이션**(현재 966단어, 신명은 neutral 통일 규칙 — 규칙의 정본이 회고와 JSON에만 있고 코드·스키마 검증 없음, `.forge/retro/2026-07-14-word-distribution-page.md`)해야 한다. deploy.sh와 단절.

---

## Tech Debt

**시드 파이프라인이 `deploy.sh`와 단절 (재현성 최대 리스크):**
- `deploy.sh`의 주입 단계는 `inject_ko_names.py`(`:52`) **하나만** 재실행. 모든 `load_*`(theographic·books·authored_persons·authored_events·person_events·verse_events·authored_genealogy)와 나머지 inject(date_corrections·person_traits·book_context·place_context·enrich_place_coords), `build_word_distribution.py`는 배포에 미포함. Neo4j 볼륨(`neo4j_data`)이 살아있는 한 문제없지만 **볼륨 삭제·신규 서버 시 전체 재적재+교정 재주입+wip 폐포+저작 계보를 수동 재현**해야 하고 그 정본 순서 문서가 없다.
- 부수: `deploy.sh` 로그 단계 라벨이 `[1/3]`(`:34`)·`[2/3]`(`:40`)·`[3/4]`(`:45`)·`[4/4]`(`:49`)로 어긋나 있다(코스메틱).

**번들 크기 경고 — maplibre 청크가 500kB 한계 초과:**
- `frontend/vite.config.js:10–15`의 `manualChunks`가 maplibre/vendor를 분리하지만, 분리된 maplibre 청크 자체가 **약 1.03MB**(`frontend/dist/assets/maplibre-*.js` 1,027,608 bytes 실측)로 Vite 기본 `chunkSizeWarningLimit`(500kB)를 초과 — 매 빌드 경고. maplibre-gl 특성상 축소 여지가 작아 lazy import 또는 경고 한계 명시(의도 문서화)가 남은 선택지.

**대형 프론트엔드 컴포넌트 (라인 수 갱신):**
- `frontend/src/SidePanel.jsx` — 823줄. `frontend/src/App.jsx` — **666줄**(직전 542, 스테이지 추가마다 증가 추세). `frontend/src/PersonHub.jsx` — 374줄(테마 토글 추가). `frontend/src/TimelineView.jsx` — 306줄, `frontend/src/BibleOverviewView.jsx` — 301줄, `frontend/src/WordDistributionView.jsx` — 217줄(신규).

**"큐레이션 13인" 주석 드리프트 잔존:**
- `backend/app/routes/persons.py:1`·`:137` docstring의 "13인", `:288`의 "34인"이 실제 `_ERA` **35 slug**·`data/person_events/` 35개 json과 계속 어긋남(재확인 — `_ERA` 키와 파일명은 정확히 일치).

---

## Known Bugs

**`MapView.jsx` useEffect 의존성 경고 (라인 이동):**
- `frontend/src/MapView.jsx:63` — `onStopSelect` missing dependency 경고(이 저장소 유일 ESLint 경고, `npx eslint`로 재확인). 마운트당 1회 의도로 보이나 `eslint-disable` 명시 없음.

**topEvents "대표성 절단" 편향 잔존:**
- `backend/app/routes/nodes.py:271–276` Book 분기 — 연도 오름차순 + `[:10]` 하드 절단으로 사건 많은 책은 초반부 10개에 몰린다(ADR-0012 범위 밖 명시).

**서신서 Book 연대 범위 오표기 (수용된 한계):**
- "첫 참조=발생" 휴리스틱이 서신서의 회고 인용에 오판정. authored_events 경로가 없는 책이라 근본 해소 불가.

**TODO/FIXME/HACK/XXX 마커는 `backend/app`·`backend/scripts`·`frontend/src` 전역 0건** (재확인).

---

## Security Considerations

**CORS `allow_origins=["*"]`:**
- `backend/app/main.py:47`. `allow_methods=["GET"]`·`allow_credentials=False`로 읽기 전용 제한. 공개 읽기 API라 즉각 위험 낮으나 쓰기·인증 추가 시 오리진 화이트리스트 필요.

**Neo4j는 127.0.0.1에만 바인딩 (양호):**
- `docker-compose.yml:4–6` 루프백 노출, api는 내부 네트워크(`bolt://neo4j:7687`). 인증은 `NEO4J_AUTH=neo4j/${NEO4J_PASSWORD:?...}` 필수화(`:10`).

**시크릿 취급 (양호):**
- `.env`는 `.gitignore` 제외. `backend/app/db.py`와 시드 스크립트가 `NEO4J_PASSWORD` 미설정 시 즉시 중단. 하드코딩 시크릿 0건. 인증/세션 계층 자체가 없음(공개 읽기 서비스).

**Cypher 인젝션 표면 (현재 방어됨):**
- `backend/app/routes/search.py`의 `q`와 `backend/app/routes/words.py`의 `w`는 파라미터/파이썬 레벨 처리(Cypher 미경유). `nodes.py` f-string 삽입은 상수뿐. 단 `inject_date_corrections.py`의 `inject_persons`는 교정 파일 `field` 값을 f-string으로 `p.{field}`에 직삽 — 레포 내 신뢰 파일 전제의 구조적 제약.

**사용자 제어 키 lru_cache — 잔존 비대칭:**
- `persons.py:222`·`:285`, `places.py:21`의 maxsize=256 캐시가 임의 문자열을 키로 받아 캐시 스래싱 여지(약한 잔존 리스크). 신규 `words.py`는 캐시가 아예 없어 이 리스크 대신 아래 전수 스캔 비용을 진다.

---

## Performance Bottlenecks

**`/words/{book}/verses` — 매 요청 31,103절 전수 substring 스캔 (신규):**
- `backend/app/routes/words.py:19–44`가 요청마다 `overlays.bible_verses()`(31,103 엔트리, `data/bible/verses.json` 9.8MB) 전체를 순회하며 `w in text` 검사. 결과 캐시 없음, 매칭 전량을 리스트에 모은 뒤 200개(`VERSE_LIMIT`) 절단. `w`는 strip 외 검증 없어 한 글자 입력도 전수 스캔을 유발. 단일 사용자엔 수용 가능하나 트래픽 증가·다중 워커 시 첫 병목 후보. nginx 속도 제한 부재(아래)와 겹치는 지점.

**대용량 오버레이 JSON 전체 인메모리 상주:**
- `data/event_verses/events.json`(2.1MB)·`data/bible/verses.json`(9.8MB)·`data/word_distribution.json`(280KB) 등이 `overlays.py` `lru_cache(maxsize=1)`로 프로세스당 상주. `backend/Dockerfile:6` uvicorn 단일 워커라 현재는 잠재적이나 워커 다중화 시 배증.

**`_build_id_to_slug()`에 캐시 없음 (잔존):**
- `backend/app/routes/journey.py:18`이 `lru_cache` 없이 요청마다 `_ERA` 35개 slug JSON을 open/parse. `tours.py`도 투어 상세마다 재호출.

**전역 노드 스캔 검색 (잔존):**
- `backend/app/routes/search.py`: `MATCH (n) WHERE ... CONTAINS ...` — 라벨·인덱스 미사용 전수 스캔(wip 필터 추가로 조건만 늘었다).

---

## Fragile Areas

**SPA 해시 라우팅 — same-document 해시 이동에 미반응 (구조 확인):**
- `frontend/src/useStageNavigation.js`는 초기 해시를 마운트 시 1회만 캡처·파싱하고(`initialHashRef` `:29`, 복원 effect `:75–104`), **`hashchange` 리스너가 어디에도 없다**(`frontend/src/` 전역 grep 0건). 이미 로드된 문서에서 주소창 해시만 바꾸면 스테이지가 전환되지 않고, `popstate`는 `e.state`만 읽어 state 없는 히스토리 엔트리는 허브로 리셋된다(`:139`). 사용자 딥링크는 신선 로드라 정상 동작하지만, **Playwright 등 자동화가 `goto`로 해시만 바꾸면 거짓 음성/양성**을 만든다 — 실제로 두 작업에서 반복 발생(URL마다 새 브라우저 컨텍스트가 정석, `.forge/retro/2026-07-14-genealogy-wip-family-closure.md`·`2026-07-14-words-unified-cloud.md`).

**`startDate`/연도 파싱·표기 로직 다중 중복 (잔존):**
- `frontend/src/dates.js` `parseYear`, `backend/app/routes/nodes.py:260–269` `_year`, `backend/scripts/load_books.py` `_parse_year`, `backend/scripts/validate_event_chronology.py` `_year`, `frontend/src/RelationsView.jsx` BC/AD 라벨. 공유 모듈 미추출, 회귀 assert는 `load_books.py`에만.

**인물 관계가 `slug` 문자열 매칭에 의존 (잔존):**
- `data/person_relations/relations.json` endpoint는 `{nameKo, slug}`만 담고 `persons.py:288` 부근이 `slug_to_id`로 `withId` 해결. slug 오타·drift 시 여정 점프가 `null`로 조용히 실패. 3중 slug 소스(파일명·`_ERA`·relations endpoint) 일치를 강제하는 스키마·테스트 없음.

**가계도 role 라벨이 nameKo 문자열 매칭에 의존 (잔존):**
- `backend/app/routes/family.py:31–59`가 "가족" 관계를 `frozenset({nameKoA, nameKoB})` 키로 매핑. nameKo 표기가 큐레이션과 그래프에서 어긋나면 role이 조용히 누락돼 gender 폴백. 동명이인 nameKo 충돌 시 오적용 여지.

**오버레이 빈값 폴백이 하류에서 500으로 표출:**
- `backend/app/overlays.py:34–43`은 파일 없음/파싱 실패 시 경고 후 빈 dict 폴백인데, `backend/app/routes/words.py:27–29`는 `books_ko()`가 비면 `book_ids.index(book_id)`가 ValueError → 500. 빈 폴백 설계가 이 라우트에선 명시적 에러 대신 런타임 예외로 새는 지점. 또한 `word_distribution.json`의 책 키와 `names_ko/books.json` 키 순서 일치를 빌드 스크립트(`build_word_distribution.py:34`의 assert 66)만 보증한다.

**관계 뷰 `type`/`valence`·단어 polarity가 프론트 상수와 암묵 결합:**
- `frontend/src/RelationsView.jsx`의 `TYPE_ICON`·`TYPE_ORDER`, `frontend/src/theme.js:26` `VALENCE_COLOR`, 그리고 `frontend/src/WordDistributionView.jsx`의 polarity(positive/negative/neutral) 매핑이 데이터 값과 하드코딩 짝. 새 값 추가 시 조용히 폴백.

**Neo4j 인덱스 생성 실패해도 서비스 계속 기동 (잔존):**
- `backend/app/main.py:37–38`: `except Exception:` 후 계속 기동 — 전수 스캔 성능 저하만 남는다.

**프론트 stale 응답 무효화의 수동 관리 (잔존):**
- `cancelled` 플래그 + id 비교 패턴이 `SidePanel.jsx`·`WordDistributionView.jsx`(`:75`·`:84` 등)·`useStageNavigation.js`에 반복 구현. 공유 훅 미추출 — 신규 fetch에서 빠뜨리면 이전 데이터 잠깐 노출.

**성품 통제 어휘가 문서·코드 이중 관리 (잔존):**
- `backend/scripts/validate_traits.py`의 `VIRTUES`/`FLAWS`가 `data/character_traits/AUTHORING.md §3`을 코드로 복제 — 한쪽만 고치면 어긋난다.

---

## Deployment / Ops Risks

**프론트 `:8080`은 `frontend/dist` 정적 마운트 — HMR 아님:**
- `docker-compose.yml:30` `./frontend/dist:...:ro`. 소스만 고치고 `npm run build`를 안 하면 이전 빌드를 계속 서빙(에러 없음). `deploy.sh`는 빌드 수행(`:34–37`).

**API `:8000` 외부 미노출:**
- `docker-compose.yml`에 api host 포트 매핑 없음 — `nginx/nginx.conf`의 `location /api/`로만 접근. 로컬 검증도 `:8080` 경유 필요.

**nginx 속도 제한 없음:**
- `nginx/nginx.conf`에 `limit_req_zone`/`limit_req` 미설정(재확인). `words.py` 전수 스캔·lru_cache 256 상한과 겹치면 잔존 리스크 악화 조합.

---

## Scaling Limits

**단일 인스턴스 스택, 인메모리 캐시 공유 불가:**
- neo4j 1 + api 1(uvicorn 단일 워커, `backend/Dockerfile:6`) + nginx 1. `lru_cache`는 프로세스 로컬이라 다중 워커/컨테이너 확장 시 인스턴스별 중복·불일치. 무효화 수단이 앱 재시작뿐인 것도 그대로.

---

## Dependencies at Risk

**Theographic 데이터를 GitHub `master` HEAD에서 미고정 fetch (잔존):**
- `load_theographic.py`·`load_books.py`(`:14–15`)·`generate_*` 다수가 커밋 SHA 고정 없이 raw 다운로드. 업스트림 스키마 변경 시 재시드 변질 또는 `KeyError` 중단.

**절 본문 프리베이크가 빌드타임 getbible 외부 호출에 의존 (잔존):**
- `backend/scripts/generate_verse_text.py`의 UA 403 우회 필요. 새 절 추가마다 getbible 가용성 의존.

**kiwipiepy — requirements 미등록 빌드타임 의존 (신규):**
- `build_word_distribution.py`가 요구하나 `backend/requirements.txt` 미포함(의도된 빌드타임 전용). `/tmp` venv 수동 설치 안내가 docstring에만 있어 환경 재현이 사람 손에 달려 있다.

**Neo4j 이미지 메이저 버전만 고정 (잔존):**
- `docker-compose.yml:3` `image: neo4j:5` — 패치 고정 권장.

---

## Test Coverage Gaps

- `*.test.*`/`*.spec.*` 0건, pytest/vitest 설정 전무, `frontend/package.json` scripts에 test 없음(재확인 — dev/build/lint/preview).
- 데이터 검증 스크립트(`validate_traits.py`·`validate_event_chronology.py`·`validate_person_context.py`)는 CI 미연결·수동 실행 의존. `load_authored_genealogy.py`의 사슬 자체 검증도 실행자가 손으로 돌려야 트립.
- 특히 위험 높은 미검증 지점:
  - wip 계약(가족 간선만·검색 제외·큐레이션 rec 무마킹)이 `__main__` 배선+검색 WHERE 한 줄에 분산 — 자동 검증 없음.
  - `curated_person_ids()`의 `events[0].participants[0]` 파일 규약, slug↔id 3중 소스 일치, keyPeople identity 조인 미검증.
  - `words.py`의 books_ko 순서↔verses.json BB 인덱스 계약은 빌드 스크립트 assert에만 의존.
  - BC/AD 연도 파싱 다중 사본 중 assert는 `load_books.py` 하나뿐.
  - date_corrections 롤백·저작 계보 소실·wip status 드리프트는 자동 감지되지 않는다.
- UI 검증은 Playwright 수동 실행(로컬)에만 의존, CI 미연동. SPA 해시의 same-document 한계로 **딥링크 검증은 URL마다 새 브라우저 컨텍스트**가 필수(거짓 음성 2회 실측), 테마 검증은 `color_scheme`이 아니라 localStorage `biblemap-theme` 주입 경로여야 유효(`frontend/src/main.jsx:7`이 부트 시 이 키만 읽는다).
