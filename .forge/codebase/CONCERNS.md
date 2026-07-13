---
last_mapped_commit: 8af8f0563294387a7073d0b85e6f7de74b4b7b30
mapped: 2026-07-13
---

# CONCERNS

현재 코드베이스에서 확인된 데이터 파이프라인 함정·기술 부채·버그 위험·취약 지점·보안·성능·확장성·테스트 공백 목록. 각 항목은 HEAD(`8af8f05`)에서 실제 파일·라인으로 재확인했다.

이번 갱신 배경: 직전 매핑 이후 이벤트 중복 제거(task#168, ADR-0016), 정본 절 사전(ADR-0015), keyPeople 정식 식별 데이터셋(ADR-0017/0018), 그리고 **가계도 신규 페이지(ADR-0019, `.forge/retro/2026-07-13-genealogy-page.md`)** 가 들어왔다. 가계도 작업이 `load_theographic.py`의 부모-자식 로더 잠복 버그를 고쳐 `PARENT_OF`/`CHILD_OF` 간선을 그래프에 새로 살려냈고, 이로 인해 재적재 순서·이웃 뷰·계보 라벨 관련 새 함정이 생겨 아래에 정리했다. 기존 데이터 파이프라인/라우트/프론트 항목은 코드로 재확인해 유지했다(라인 수·참조 갱신).

---

## Cache & Reload-Order Footguns

가장 조용히(에러 없이) 잘못된 상태를 만드는 부류. 캐시 무효화 수단이 사실상 **`api` 컨테이너 재시작뿐**이고, 재적재 순서를 빠뜨리면 저작 레이어가 소실된다.

**인메모리 캐시 무효화 = `api` 재시작뿐 (`lru_cache(maxsize=1)`가 라우트 전반에 산재):**
- 오버레이 JSON과 파생 데이터는 프로세스 로컬 `lru_cache`로 1회 로드 후 상주한다 — `backend/app/overlays.py`(3개: `book_events_raw`·`event_verses`·`bible_verses`, `:46`·`:52`·`:58`), `backend/app/routes/events.py`(3개, `:11`·`:53`·`:98`), `backend/app/routes/tours.py`(2개, `:30`·`:55`), `backend/app/routes/persons.py`(다수, `:101`·`:145`·`:156`·`:167`·`:274` maxsize=1, `:222`·`:285` maxsize=256), `backend/app/routes/places.py:21`(256), `backend/app/routes/family.py:31`(`_family_role_pairs`, maxsize=1).
- 따라서 `data/` 오버레이 파일(예: `event_verses/events.json`·`person_relations/relations.json`·`keypeople/identity.json`)을 고치거나 Neo4j 그래프를 재적재해도 **실행 중 프로세스는 이전 값을 계속 서빙**한다. 무효화 API·TTL·파일 mtime 감시가 없어 반영하려면 `docker compose -p biblemap up -d api`(또는 재시작)로 프로세스를 다시 띄워야 한다. 로컬 검증에서 "오버레이를 고쳤는데 안 바뀐다"의 첫 번째 용의자.

**`load_theographic.py` 재실행이 date_corrections를 되돌리고, 저작 계보 간선 복원엔 별도 로더 재실행이 필요하다:**
- `load_theographic.py`로 원본을 통째 재적재하면 노드 속성이 GitHub 원본(Ussher 연대계) 값으로 덮여 date_corrections 교정이 사라지므로 `backend/scripts/inject_date_corrections.py`를 **반드시 재실행**해야 한다(멱등·재실행 안전, `README.md:26–27`·ADR-0014 명시).
- **(NEW, ADR-0019)** 그래프를 초기화한 뒤 재적재하면 마태복음 1장 예수 족보의 **저작 계보 간선도 함께 소실**되므로 `backend/scripts/load_authored_genealogy.py`를 **재실행**해야 사슬(무단절)이 복원된다. 이 스크립트 docstring(`:9–10`)과 ADR-0019 Consequences(`.forge/adr/0019-*.md:17`)에 명시돼 있다. 단, 가법적 MERGE라 노드 속성/date_corrections는 건드리지 않는다.
- 뉘앙스: 가계도 태스크의 부모-자식 간선은 `load_theographic.py`의 `load_parent_child_rels`(`:151–170`)가 적재하는데, **이 함수만 타겟 재실행하면** MERGE라 date_corrections·저작 계보를 훼손하지 않는다(retro `2026-07-13-genealogy-page.md:9`). 위험한 것은 **전체 `load_theographic.py` 재실행**이다.
- **README·deploy.sh 어디에도 `load_authored_genealogy.py`가 등록돼 있지 않다**(재확인: `README.md`의 데이터 적재 순서는 `load_theographic → inject_ko_names → inject_date_corrections`까지만, `deploy.sh`는 `inject_ko_names`만). 즉 재적재 순서의 정본 문서가 새 로더를 아직 반영하지 못한 상태다(retro `:22`가 "README 재적재 순서 갱신은 후속"으로 남겨둠).

---

## Genealogy / Graph-Derived Concerns

`PARENT_OF`/`CHILD_OF` 간선이 그래프에 새로 살아나면서(ADR-0019) 드러난 계보 관련 함정. 데이터는 정확하나 표시가 어색하거나, 기존 이웃 뷰에 회귀성 노출을 만든다.

**SidePanel "이웃"에 부모가 부모·자식으로 이중 표시:**
- `load_parent_child_rels`(`backend/scripts/load_theographic.py:151–170`)와 `load_authored_genealogy.py`가 부모-자식을 **상호 간선(`PARENT_OF` + `CHILD_OF`)** 으로 함께 MERGE한다. 한편 이웃 쿼리는 무방향(`-[r]-`)이다 — `backend/app/routes/nodes.py`의 `get_node_neighbors_grouped`(`:121`)와 `get_node`(`:173`)가 모두 `MATCH (n {...})-[r]-(m)`. 그 결과 한 부모 노드가 `PARENT_OF`(들어오는)·`CHILD_OF`(나가는) 두 간선으로 각각 걸려 **같은 인물이 "부모"와 "자식"으로 2회** 노출된다. `type(r)`만 relation으로 실어 방향·상호성 디듀프가 없다. 계보 로더 도입이 드러낸 기존 뷰 뉘앙스로, retro `2026-07-13-genealogy-page.md:20`이 후속 후보로 기록. 해소하려면 이웃 쿼리에 방향성/디듀프 도입 필요.

**하나님(God)이 계보상 "아버지"로 라벨:**
- theographic에서 아담의 `father` 링크가 God을 가리키고 God의 `gender`가 Male이라, 가계도 렌더의 `roleLabel`(`frontend/src/FamilyTree.jsx:77–86`)이 조상 세대(`g > 0`) + Male → **"아버지"**(`:86`)로 표시한다. 데이터상 정확한 파생이나 창조주를 혈통 부모로 표시하는 게 어색할 수 있다(retro `:21`). 참고로 인물 연결 축(`persons.py:225`·`:257` `co_participants`/`contemporaries`)에서는 God을 명시 제외하지만, 가계도 트리에는 그런 필터가 없다.

**동명이인(homonym) 위험 — 이름 기반 해석의 구조적 함정 (ADR-0017/0018):**
- 그래프에 같은 nameKo를 가진 다른 인물이 복수 존재한다(야고보 3인·유다 3인 등, ADR-0018 서두). keyPeople 문자열은 자유 텍스트라 런타임 이름 해석으로는 결정 불가능(실측 7/7 실패)해, ADR-0018이 `data/keypeople/identity.json`으로 (책,이름)→`{kind, id?}` 정식 식별을 **저작 시점에 데이터로 고정**하는 방식으로 해소했다(`backend/app/routes/persons.py:168`·`:180`이 이 identity를 조인). 별칭(alias)은 오resolution을 낳아 쓰지 않고 exact nameKo + endsWith만 쓴다(ADR-0018 보강 `:24`).
- 가계도 태스크도 동명이인 3건(나손·므낫세·요셉)을 그래프 동명 매칭이 전부 다른 인물이라 **저작 노드로 우회**했다(retro `:11`). 즉 이름 기반 해석 경로(keyPeople·계보 사슬)는 새 이름을 붙일 때마다 동명이인을 데이터로 못박아야 하며, 자동 퍼지 매칭에 의존하면 오링크가 조용히 발생한다.

**theographic `children` 배열은 출생순이 아니다 — 출생 순서는 그래프에서 파생 불가:**
- theographic의 `children`/부모-자식 간선엔 출생순 정보가 없다(아담 `[셋,아벨,가인]`, 이새가 David를 6번째로 나열 등). 따라서 "맏아들/둘째" 같은 출생 순서는 그래프에서 결정적으로 도출할 수 없고, **오직 큐레이션 `data/person_relations/relations.json`의 role 라벨**이 유일한 정본 원천이다(`backend/app/routes/family.py:31–59` `_family_role_pairs`가 "가족" 관계의 role을 읽어 프론트에 전달, `frontend/src/FamilyTree.jsx:78`이 role 우선·없으면 gender 폴백). role이 없으면 성별+구조 폴백까지만 하고 순서를 지어내지 않는다(retro `:17`, ADR-0019). 큐레이션 role이 없는 형제 집합은 UI에서 출생 순서를 보증하지 못한다.

---

## Data Pipeline Footguns

시드/재적재 순서에 민감하고 대부분 에러 없이 조용히 잘못된 상태를 만든다.

**`load_books.py` 재실행이 교정 연대를 Ussher 값으로 롤백한다:**
- `backend/scripts/load_books.py`는 Book의 `startYear`/`endYear`를 Neo4j가 아니라 **GitHub 원본에서 새로 받은** events.json으로 재계산한다(`BOOKS_URL`/`EVENTS_URL`은 theographic `master` raw, `:14–15`). 매 실행마다 fresh fetch 후 원본(Ussher) `startDate`를 집계해 `SET b.startYear/b.endYear`로 덮어쓰고, Book 메타 전체·`CONTAINS_BOOK` 관계까지 재구축한다. date_corrections 적용 후 그대로 재실행하면 책 연도가 교정 전으로 롤백된다.
- ADR-0014 Consequences가 "책 연도는 이벤트 집계 파생이라 교정 후 `load_books.py` 재실행 필요"라는 **롤백 유발 문구**를 담고 있고, 1회성 우회 스크립트(`recompute_book_years.py`)는 레포에 커밋돼 있지 않다(디스크·git 이력 부재, retro에만 기록). 근본 해소(스크립트를 Neo4j 소스로 리팩터)는 미완.

**Person `birthYear`/`deathYear`는 Ussher 연대에 잔존 — Event 연대(보수계)와 이원화:**
- ADR-0014로 Event `startDate`/`sortKey`는 보수 연대계로 이동했으나 Person `birthYear`/`deathYear`는 재정렬하지 않았다. 현재 이 두 필드는 UI 경로 어디서도 노출되지 않고 `load_theographic.py`(적재)와 `validate_event_chronology.py`(검증)만 참조한다. 향후 UI에 surfacing하면 이벤트(보수계)와 한 화면에서 계가 어긋난다(ADR-0014가 "노출 전 재검토"를 사전 선언).

**연대 검증의 "기계 위반 0"이 문자 그대로는 아니다 — 화이트리스트가 3쌍만 하드코딩:**
- `backend/scripts/validate_event_chronology.py`의 `THEOLOGICAL_WHITELIST`는 정확히 3쌍만 예외로 둔다. 실제로는 raw 위반 4건(Adam·Seth·Terah·John the Baptist)이 잔존하며 스크립트가 아니라 계획 Non-goals·ADR-0014 문서 근거로만 소명된다. 즉 리포트만 보면 이 4건의 맥락을 놓친다.

**Event `startDate`는 혼재 형식 문자열 — 반드시 파싱해 정렬, 사전순 금지:**
- 연도만(`"-4003"`/`"30"`)·연-월(`"-1451-01"`)·제로패딩 연-월-일(`"0049-10-01"`)이 공존하고 BC는 음수 접두다. 사전순 정렬하면 BC 연도가 역전된다. 부호 분리 후 첫 파트 정수 파싱 필수. 파싱 로직이 여러 곳에 중복(아래 Fragile Areas 참조).

**시드 스크립트 실행 순서 암묵적:**
- `load_person_events.py`는 `MATCH (b:Book ...)`·`MATCH (p:Place ...)`로 기존 노드를 참조하므로 `load_books.py`·`load_theographic.py`·`enrich_place_coords.py`·`load_authored_persons.py`가 먼저 실행돼야 한다. 잘못된 순서면 `MATCH`가 0건을 반환해 관계가 조용히 누락된다(에러 없음). `inject_date_corrections.py`는 적재 후에 와야 하고 `load_books.py` 롤백 함정과 순서상 충돌한다. `backend/scripts/`에는 `__init__.py` 제외 **29개** 스크립트가 있으나 정본화된 단일 실행 순서 문서가 없다.

---

## Tech Debt

**시드 파이프라인이 `deploy.sh`와 단절됨 (재현성 최대 리스크):**
- `deploy.sh`의 주입 단계는 `inject_ko_names.py`(`:52`) **하나만** 재실행한다. 모든 `load_*` 적재 스크립트(`load_theographic`·`load_books`·`load_authored_persons`·`load_authored_events`·`load_person_events`·`load_verse_events`·**`load_authored_genealogy`**)와 나머지 inject 스크립트(`inject_date_corrections`·`inject_person_traits`·`inject_book_context`·`inject_place_context`·`enrich_place_coords`)는 배포에 포함되지 않는다.
- Neo4j 볼륨(`neo4j_data`)이 살아있는 한 재실행 불필요하나, **볼륨 삭제·신규 서버·컨테이너 재생성 시** 전체 재적재 + date_corrections 재주입 + 저작 계보(`load_authored_genealogy`) 재적재 + `CONTAINS_BOOK.primary` 마이그레이션(ADR-0012)까지 수동 재현해야 하고, 그 정본 순서는 문서화돼 있지 않다. 즉 "fresh/다른 Neo4j"는 부모-자식·저작 계보 등 파생 간선을 통째로 잃는다.

**대형 프론트엔드 컴포넌트 (라인 수 갱신):**
- `frontend/src/SidePanel.jsx` — **823줄**(직전 731). Person/Place/Book 노드 타입 분기 렌더 + nodeId별 stale 무효화를 한 파일에서 관리.
- `frontend/src/App.jsx` — **542줄**(직전 449). 상태 머신·fetch orchestration·레이아웃 분기 공존.
- `frontend/src/TimelineView.jsx` — **307줄**, `frontend/src/RelationsView.jsx` — 195줄, `frontend/src/FamilyTree.jsx` — 207줄(신규, 손수 SVG 세대 트리 + role 라벨).

**"큐레이션 13인" 주석이 현실과 계속 어긋남:**
- `backend/app/routes/persons.py:1`·`:137`(docstring)에 "13인"이 고정돼 있으나 `_ERA`는 여전히 **35 slug**이고 `data/person_events/`도 35개 json(재확인). `persons.py:288`의 "34인이면 withId 해결" 문구도 실제 35인과 어긋난다 — 같은 파일에 13·34 서로 다른 값이 박혀 있는 인원수 드리프트.

---

## Known Bugs

**`MapView.jsx` useEffect 의존성 경고:**
- `frontend/src/MapView.jsx`의 맵 초기화 effect(`:21`)가 `map.on('load', ...)` 콜백 안에서 참조하는 콜백을 deps에 넣지 않아 `npm run lint`에서 `missing dependency` 경고가 난다(이 저장소 유일 ESLint 경고). 마운트당 1회 생성 의도로 보이나 `eslint-disable`로 의도가 명시돼 있지 않다.

**topEvents "대표성 절단" 편향 잔존:**
- `backend/app/routes/nodes.py`의 Book 분기 topEvents 정렬(연도 오름차순 + `top_events[:10]` 하드 절단, `:271–276`)로 사건이 많은 책은 초반부에 10개가 몰리고 후반 핵심 서사가 절단된다(ADR-0012 "범위 밖"으로 명시된 curation 이슈).

**서신서 Book 연대 범위 오표기 (수용된 한계):**
- `CONTAINS_BOOK.primary`(ADR-0012)로 topEvents 오염은 해소됐지만 "첫 참조=발생" 휴리스틱이 서신서의 신학적 회고 인용에 오판정을 낳는다. authored_events 경로가 없는 책이라 근본 해소 불가.

**TODO/FIXME/HACK/XXX 마커는 `backend/app`·`backend/scripts`·`frontend/src` 전역 0건** (재확인).

---

## Security Considerations

**CORS `allow_origins=["*"]`:**
- `backend/app/main.py:47`. `allow_methods=["GET"]`(`:49`)·`allow_credentials=False`(`:48`)로 읽기 전용 제한. 공개 읽기 API라 즉각 위험은 낮으나 향후 쓰기·인증 추가 시 명시적 오리진 화이트리스트 필요.

**Neo4j는 127.0.0.1에만 바인딩 (양호):**
- `docker-compose.yml`이 `- "127.0.0.1:7474:7474"`·`- "127.0.0.1:7687:7687"`로 루프백에만 노출(`:4–6`). API 컨테이너는 내부 네트워크(`bolt://neo4j:7687`)로 접근하고 host 포트 매핑이 없어 외부 미노출. 인증은 `NEO4J_AUTH=neo4j/${NEO4J_PASSWORD:?...}`로 필수화(`:10`).

**시크릿 취급 (양호):**
- `.env`는 `.gitignore` 제외, git tracked env는 비밀 아닌 `.env.example`·`frontend/.env.production`뿐. `docker-compose.yml`이 `${NEO4J_PASSWORD:?...}`로 필수화하고, `backend/app/db.py:11–13`과 모든 시드/검증 스크립트가 `NEO4J_PASSWORD` 미설정 시 즉시 `RuntimeError`로 중단(`load_authored_genealogy.py:20–21` 등). 하드코딩 시크릿 값 0건. 인증/세션 계층 자체가 없다(공개 읽기 서비스).

**Cypher 인젝션 표면 (현재 방어됨):**
- `backend/app/routes/search.py`의 사용자값 `q`는 `$q` 파라미터 바인딩. `nodes.py`의 f-string 삽입은 상수(`NODE_NEIGHBOR_LIMIT`·`MAX_NEIGHBORS_PER_TYPE`)뿐. 단, `inject_date_corrections.py`의 `inject_persons`가 교정 파일 `field` 값을 f-string으로 `p.{field}`에 직접 삽입한다 — 입력이 레포 내 신뢰된 정적 파일이라 실질 위험은 없으나, 이 파일을 신뢰 경계 밖에서 채우면 안 되는 구조적 제약.

**사용자 제어 키 lru_cache — 잔존 비대칭:**
- `persons.py:222`·`:285`, `places.py:21`의 캐시가 `maxsize=256`. id 검증 없이 임의 문자열이 캐시 키가 되므로 정당 key space가 256에 근접하면 캐시 스래싱 가능(원 DoS보다 약한 잔존 리스크).

---

## Performance Bottlenecks

**대용량 오버레이 JSON 전체 인메모리 상주:**
- `data/event_verses/events.json`·`data/bible/verses.json` 등이 `overlays.py`의 `lru_cache(maxsize=1)`로 프로세스당 상주. `backend/Dockerfile`이 uvicorn 단일 워커라 현재는 잠재적이나, 워커 다중화 시 워커당 중복 배증.

**`_build_id_to_slug()`에 캐시 없음:**
- `backend/app/routes/journey.py`가 `lru_cache` 없이 요청마다 `_ERA`의 35개 slug JSON을 순회해 open/parse. `tours.py`도 매 투어 상세 요청마다 이 무캐시 함수를 다시 돈다.

**전역 노드 스캔 검색:**
- `backend/app/routes/search.py`: `MATCH (n) WHERE n.nameKo CONTAINS $q OR toLower(n.name) CONTAINS toLower($q)` — 라벨·인덱스 미사용 전수 스캔.

---

## Fragile Areas

**`startDate`/연도 파싱·표기 로직 다중 중복:**
- `frontend/src/dates.js` `parseYear`, `backend/app/routes/nodes.py:260–269` `_year`, `backend/scripts/load_books.py` `_parse_year`, `backend/scripts/validate_event_chronology.py` `_year`, `frontend/src/RelationsView.jsx` BC/AD 라벨. 규칙은 동일하나 공유 모듈로 추출되지 않았고, 회귀 방지 assert는 `load_books.py`의 `_parse_year`(임포트 시점 실행)에만 있다.

**인물 관계가 `slug` 문자열 매칭에 의존:**
- `data/person_relations/relations.json` endpoint는 `{nameKo, slug}`만 담고 `persons.py:288` 부근이 `slug_to_id.get(...)`로 `withId`를 해결한다. slug 오타·drift 시 여정 점프가 `null`로 조용히 실패(에러 없음). 3중 slug 소스(파일명·`_ERA`/`_NAME_KO`·relations endpoint) 일치를 강제하는 스키마·테스트가 없다.

**가계도 role 라벨이 nameKo 문자열 매칭에 의존:**
- `backend/app/routes/family.py:31–59` `_family_role_pairs`가 person_relations "가족" 관계를 `frozenset({nameKoA, nameKoB})` 키로 매핑하고 focus의 nameKo로 조회한다(`:151–160`). nameKo 표기가 큐레이션과 그래프에서 어긋나면 role이 조용히 누락돼 gender 폴백으로 떨어진다. 동명이인 두 인물이 같은 nameKo면 role이 오적용될 여지도 있다(theographic_id 아닌 이름 키).

**관계 뷰 `type`/`valence`가 프론트 상수와 암묵 결합:**
- `frontend/src/RelationsView.jsx`의 `TYPE_ICON`·`TYPE_ORDER`와 `theme.js`의 `VALENCE_COLOR`가 데이터 값과 하드코딩 짝. 새 값 추가 시 `null`·중립색으로 조용히 폴백.

**Neo4j 인덱스 생성 실패해도 서비스 계속 기동:**
- `backend/app/main.py:37–38`: `except Exception:` → `logger.exception(...)` 후 인덱스 없이 계속 기동. 실패해도 서비스는 뜨고 전수 스캔 성능 저하만 남는다.

**프론트 stale 응답 무효화의 수동 관리:**
- `SidePanel.jsx`의 `cancelled` 플래그 + `nodeId` 비교 패턴이 여러 컴포넌트에 반복 구현. 공유 훅으로 추출되지 않아 신규 비동기 fetch 추가 시 빠뜨리면 이전 데이터가 잠깐 노출된다.

**성품 통제 어휘가 문서·코드 이중 관리:**
- `backend/scripts/validate_traits.py`의 `VIRTUES`/`FLAWS` 집합이 `data/character_traits/AUTHORING.md §3` 통제 어휘를 코드로 복제한다("문서와 함께 갱신할 것" 주석 명시). 한쪽만 고치면 검증이 문서와 어긋난다.

---

## Deployment / Ops Risks

**프론트 `:8080`은 `frontend/dist` 정적 마운트 — HMR 아님:**
- `docker-compose.yml`의 nginx가 `- ./frontend/dist:/usr/share/nginx/html:ro`. 소스만 고치고 `npm run build`를 안 하면 `:8080`은 이전 빌드를 계속 서빙(에러 없음). `deploy.sh`는 배포 시 `npm run build`를 수행한다.

**API `:8000` 외부 미노출:**
- `docker-compose.yml`에 api host 포트 매핑 없음. `nginx/nginx.conf`의 `location /api/`로만 접근.

**nginx 속도 제한 없음:**
- `nginx/nginx.conf`에 `limit_req_zone`/`limit_req` 미설정. lru_cache 256 상한이어도 rate limit 부재는 캐시 스래싱류 잔존 리스크를 악화시킬 조합.

---

## Scaling Limits

**단일 인스턴스 스택, 인메모리 캐시 공유 불가:**
- neo4j 1 + api 1(uvicorn 단일 워커) + nginx 1. API의 `lru_cache`들은 프로세스 로컬이라 다중 워커/컨테이너 확장 시 인스턴스별 중복·불일치. 무효화 수단이 앱 재시작뿐인 것도 그대로(위 Cache & Reload-Order Footguns).

---

## Dependencies at Risk

**Theographic 데이터를 GitHub `master` HEAD에서 미고정 fetch:**
- `load_theographic.py`·`load_books.py`(`:14–15`)·`generate_event_verses.py`·`generate_verse_events.py`·`generate_book_context.py`·`generate_person_traits.py`가 `https://raw.githubusercontent.com/robertrouse/theographic-bible-metadata/master/json/*.json`을 커밋 SHA 고정 없이 다운로드. 업스트림 스키마 변경 시 재시드 결과 변질 또는 `KeyError` 중단 위험. `load_books.py`의 경우 이 미고정 fetch가 연대 롤백 함정의 소스와 동일하다.

**절 본문 프리베이크가 빌드타임 getbible 외부 호출에 의존:**
- `backend/scripts/generate_verse_text.py`의 UA 403 우회 로직이 여전히 필요. 새 절 추가마다 getbible 가용성·정책에 의존.

**Neo4j 이미지 메이저 버전만 고정:**
- `docker-compose.yml`의 `image: neo4j:5`. `neo4j:5.x.y` 패치 고정 권장.

---

## Test Coverage Gaps

- `*.test.*`/`*.spec.*` 파일 0건, pytest/vitest/jest 설정·`conftest.py`·`vitest.config.*` 전무. `frontend/package.json` scripts에 test 없음(dev/build/lint/preview).
- 커밋된 데이터 검증 스크립트(`validate_traits.py`·`validate_event_chronology.py`·`validate_person_context.py`)는 종료코드로 위반을 신호하나 **CI 미연결·수동 실행 의존**이고, `validate_event_chronology.py`는 화이트리스트 3쌍만 알아 잔존 4건은 문서 대조로만 소명된다.
- `load_authored_genealogy.py`는 적재 후 사슬 끝→머리 `CHILD_OF*` 도달 가능성을 **스크립트 내부에서 자체 검증**(`:62–74`, 단절 시 `SystemExit`)하지만 별도 테스트/CI에는 연결돼 있지 않다 — 실행자가 손으로 돌려야 트립.
- 특히 위험 높은 미검증 지점:
  - BC/AD 연도 파싱·표기 다중 사본 중 assert 있는 것은 `load_books.py` 하나뿐.
  - `persons.py`의 keyPeople identity 조인·slug↔id 매핑 계약·withId null 판정 미검증.
  - `nodes.py` 이웃 쿼리(`-[r]-`) 방향 중복·Book topEvents 정렬/절단 미검증.
  - date_corrections 파이프라인(inject 재실행 누락·`load_books.py` 롤백)과 계보 저작 소실(`load_authored_genealogy` 재실행 누락)은 자동 감지되지 않는다.
- UI 검증은 Playwright 수동 실행(로컬)에만 의존, CI 미연동.
