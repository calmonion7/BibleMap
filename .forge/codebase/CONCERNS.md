---
last_mapped_commit: 04e9be173b6a321e4daaa417f6f47004dc3cd687
mapped: 2026-07-11
---

# CONCERNS

현재 코드베이스에서 확인된 데이터 파이프라인 함정·기술 부채·버그 위험·취약 지점·보안·성능·확장성·테스트 공백 목록.
각 항목은 HEAD(`04e9be17`)에서 실제 파일·라인으로 재확인했다.

이번 갱신 배경: 직전 매핑(`cf024f8`) 이후 task#157(인물 성품 분류 재구성)과 task#158(theographic 원본 연대 이상 교정, ADR-0014)이 들어왔다. task#158은 연대 교정 오버레이(`data/date_corrections/`) + 멱등 inject + 상시 검증 스크립트를 신설했고, 그 과정에서 데이터 파이프라인의 여러 함정이 드러나 아래 최상단에 **Data Pipeline Footguns** 섹션으로 정리했다. task#157은 성품 데이터·검증 스크립트(`validate_traits.py`)를 추가했다. 그 외 백엔드 라우트·프론트 컴포넌트 계열 항목은 코드로 재확인해 유지했다(라인 수·라인 참조는 현재 값으로 갱신).

---

## Data Pipeline Footguns

task#158 연대 교정으로 새로 드러났거나 확대된 데이터 파이프라인 함정들. 시드/재적재 순서에 민감하며, 대부분 **에러 없이 조용히** 잘못된 상태를 만든다.

**`load_books.py` 재실행이 교정 연대를 Ussher 값으로 롤백한다 (잠재 트랩, 잔존):**
- `backend/scripts/load_books.py`는 Book의 `startYear`/`endYear`를 **Neo4j가 아니라 GitHub 원본에서 새로 받은** events.json으로 재계산한다. `:14–15`가 `BOOKS_URL`/`EVENTS_URL`(theographic `master` raw)을 정의하고, `main()`(`:107–113`)이 매 실행마다 둘 다 fresh fetch, `build_book_year_range()`(`:79–103`)가 그 원본(=Ussher 연대) `startDate`를 집계해 `min`/`max`로 책 연도를 만든 뒤 `:119–171`이 `MERGE (b:Book ...) SET b.startYear/b.endYear ...`로 덮어쓴다.
- 따라서 date_corrections 적용 후 `load_books.py`를 그대로 재실행하면 책 연도가 교정 전 Ussher 값으로 **롤백**된다. 게다가 이 스크립트는 Book 메타 전체(`name`/`nameKo`/`testament`/`genre`/...)와 `CONTAINS_BOOK` 관계까지 함께 재구축하므로(`:119–192`), 책 연도 하나 갱신하려다 무관한 부작용까지 딸려온다.
- task#158은 이를 1회성 `recompute_book_years.py`(기존 `CONTAINS_BOOK` + 교정 후 DB `startDate`만 집계)로 우회했으나, **그 스크립트는 레포에 커밋돼 있지 않다**(디스크·git 이력 모두 부재, `.forge/retro/2026-07-11-theographic-chronology-correction.md:16`에만 기록). 즉 우회 수단은 사라졌고 함정만 남았다.
- 함정을 키우는 요인: `.forge/adr/0014-canonical-conservative-chronology.md:20`이 "책 `startYear`는 이벤트 집계 파생이라 교정 후 `load_books.py` 재실행이 필요하다"고 **재실행을 권하는 문구를 그대로 담고 있다** — ADR의 이 Consequence 줄 자체가 롤백을 유발하는 지침이다. README에는 이 트랩 경고가 없다. 근본 해소(스크립트를 Neo4j 소스로 리팩터)는 retro의 후속 과제 후보로만 남아 있다.

**date_corrections 오버레이는 원본 재적재 후 매번 재주입해야 한다:**
- `data/date_corrections/{events,persons}.json`의 교정은 `backend/scripts/inject_date_corrections.py`로 DB에 SET된다. `load_theographic.py`로 원본을 재적재하면(업스트림 갱신 등) 교정이 원본값으로 덮여 사라지므로 **inject를 반드시 재실행**해야 한다.
- `README.md:25–27`이 이 요구를 명시하고, ADR-0014 Consequences(`:19`)도 재확인한다. inject는 멱등이며 에코 필드로 방어한다: events는 `title`/`oldStartDate`, persons는 `name`/`oldValue`가 DB 현재값과 불일치하면 그 항목을 스킵+경고, 이미 new 값과 같으면(재실행) 조용히 통과한다(`inject_date_corrections.py:40–50`·`73–83`). 즉 재실행 자체는 안전하지만, **실행을 빠뜨리면 교정이 조용히 소실**된다.

**Person `birthYear`/`deathYear`는 Ussher 연대에 잔존 — Event 연대(보수계)와 이원화:**
- ADR-0014에 따라 Event `startDate`/`sortKey`는 보수 연대계로 이동했지만 Person `birthYear`/`deathYear`는 재정렬하지 않았다(`0014-...:15`·`:21`). 현재 이 두 필드는 UI 경로 어디서도 노출되지 않는다 — `grep`으로 확인 시 `backend/app/`·`frontend/src/` 전역 0건, 오직 `backend/scripts/load_theographic.py`(적재)와 `backend/scripts/validate_event_chronology.py`(검증)만 참조한다.
- 의도된 수용이지만 **잠재 불일치**: 향후 인물 출생/사망 연도를 UI에 surfacing하면 이벤트(보수계)와 한 화면에서 계가 어긋난다. ADR-0014(`:21`)가 "노출하려면 이 ADR을 먼저 재검토"라고 사전 선언해 두었다.

**"기계 위반 0"이 문자 그대로는 아니다 — 검증 화이트리스트가 3쌍만 하드코딩:**
- `backend/scripts/validate_event_chronology.py`의 `THEOLOGICAL_WHITELIST`(`:55–59`)는 정확히 **3쌍**(`Jesus Christ`↔`Creation of all things`, `Moses`↔`The Transfiguation`, `Elijah`↔`The Transfiguation`)만 예외로 둔다.
- 실제로는 raw 위반 4건(Adam·Seth·Terah·John the Baptist)이 잔존하며, 이들은 스크립트가 아니라 **계획 Non-goals·ADR-0014 문서 근거로만** 소명된다(원시사 불변·Person 연대 잔존·교정 창 밖; `.forge/retro/2026-07-11-theographic-chronology-correction.md:18–19`). 따라서 검증 결과는 "기계 위반 0"이 아니라 "실질 위반 0(문서 대조)"이다 — 다음 실행자가 스크립트 리포트만 보고 판단하면 이 4건의 맥락을 놓친다. retro의 후속 과제 후보로 "Non-goal 예외 4건을 화이트리스트에 데이터화"가 남아 있다.

**Event `startDate`는 혼재 형식 문자열 — 반드시 파싱해 정렬, 사전순 금지:**
- `startDate`는 연도만(`"-4003"`/`"30"`), 연-월(`"-1451-01"`), 제로패딩 연-월-일(`"0049-10-01"`)이 공존하고 BC는 음수 접두다. 사전순 정렬하면 BC 연도가 역전된다(예: `-1451` > `-4003` 문자열 비교). 반드시 부호 분리 후 첫 파트를 정수 파싱해야 한다.
- 규약 헬퍼: 프론트 `frontend/src/dates.js:4–12` `parseYear`, 백엔드 `backend/app/routes/nodes.py:244–253` `_year`(topEvents 정렬용, `:254`에서 오름차순 + `top_events[:10]` 절단), 시드 `backend/scripts/load_books.py:56–68` `_parse_year`(임포트 시점 assert 4개로 회귀 방지, `:72–76`).
- **task#158로 4번째 백엔드 사본이 늘었다**: `backend/scripts/validate_event_chronology.py:64–75` `_year`(같은 규칙, 단 assert 없음). 정렬 자체는 DB `sortKey`가 지배하지만(`events.py:66` `ORDER BY e.sortKey`), 연도 라벨/파싱 규칙은 이제 5곳(위 4개 + `RelationsView.jsx:44` BC/AD 라벨)에 흩어져 공유 모듈이 없다 — 아래 Fragile Areas 참조.

---

## Tech Debt

**시드 파이프라인이 `deploy.sh`와 단절됨 (재현성 최대 리스크, 여전함):**
- `deploy.sh:50–63`의 주입 단계는 `inject_ko_names.py`(`:52`) 하나만 재실행한다. `backend/scripts/`에는 `__init__.py` 제외 **24개** 스크립트가 있고(task#157·158로 `validate_traits.py`·`validate_event_chronology.py`·`inject_date_corrections.py` 추가), 적재 스크립트(`load_theographic.py`, `load_authored_persons.py`, `load_authored_events.py`, `load_books.py`, `load_person_events.py`, `load_verse_events.py`)·주입 스크립트(`enrich_place_coords.py`, `inject_book_context.py`, `inject_place_context.py`, `inject_person_traits.py`, **`inject_date_corrections.py`**)는 배포에 포함되지 않는다.
- 특히 `inject_date_corrections.py`가 deploy에서 빠져 있어, 볼륨 삭제·신규 프로비저닝으로 원본을 재적재하는 경로에서는 연대 교정이 자동으로 재적용되지 않는다(수동 재실행 의존).
- Neo4j 볼륨(`docker-compose.yml`의 `neo4j_data`)이 살아있는 한 재실행 불필요하지만, 볼륨 삭제·신규 서버·컨테이너 재생성 시 전체 재적재 + 교정 재주입 + `CONTAINS_BOOK.primary` 마이그레이션(ADR-0012)까지 수동 재현해야 한다. 정본화된 단일 실행 순서는 여전히 없다.

**시드 스크립트 실행 순서 암묵적 (여전함):**
- `load_person_events.py`는 `MATCH (b:Book ...)`·`MATCH (p:Place ...)`로 기존 노드를 참조하므로 `load_books.py`·`load_theographic.py`·`enrich_place_coords.py`·`load_authored_persons.py`가 먼저 실행돼야 한다. 잘못된 순서로 재시드하면 `MATCH`가 0건을 반환해 관계가 조용히 누락된다(에러 없음). `inject_date_corrections.py`는 이벤트/인물 적재 후에 와야 하고, `load_books.py`의 롤백 함정과 순서상 충돌한다(위 Data Pipeline Footguns).

**대형 프론트엔드 컴포넌트 (라인 수 갱신):**
- `frontend/src/SidePanel.jsx` — **731줄**(직전 702). Person/Place/Book 노드 타입 분기 렌더 + nodeId별 stale 무효화 패턴을 한 파일에서 관리.
- `frontend/src/App.jsx` — **449줄**(직전 426). `useStageNavigation.js`·`useNodeSelection.js`로 일부 분리됐으나 상태 머신·fetch orchestration·레이아웃 분기가 공존.
- `frontend/src/TimelineView.jsx` — **352줄**. task#158로 연대계 정합 관련 변경 포함.
- `frontend/src/RelationsView.jsx` — 195줄. 레이아웃 3단이 한 파일에 공존하나 각 분기가 짧고 독립적.

**"큐레이션 13인" 주석이 현실과 계속 어긋남 (여전함):**
- `backend/app/routes/persons.py:1`(docstring)·`:137`, `backend/app/routes/journey.py`, `frontend/src/PersonHub.jsx`에 "13인"이 고정돼 있으나 `_ERA`는 여전히 **35개 slug**(`persons.py:20`), `data/person_events/`도 35개 json(재확인).
- `persons.py:211`의 "34인이면 withId를 해결" 문구도 실제 35인과 어긋난다 — 같은 숫자 드리프트가 한 파일에 두 번(13, 34) 서로 다른 값으로 박혀 있다. task#157(성품 47인 재구성)은 `data/character_traits/people.json`을 건드렸을 뿐 이 큐레이션 목록(35 slug)과는 별개 축이라, 두 인원수(성품 대상 인물 수 vs 큐레이션 여정 인물 수)가 다른 것도 혼동 소지.

---

## Known Bugs

**`MapView.jsx` useEffect 의존성 경고 (HEAD 이전부터 존재):**
- 맵 초기화 effect가 `map.on('load', ...)` 콜백 안에서 참조하는 콜백을 deps 배열에 넣지 않아 `npm run lint`에서 `missing dependency` 경고가 난다(이 저장소 유일 ESLint 경고). 맵 인스턴스를 마운트당 1회만 만들려는 의도로 보이나 `eslint-disable`로 의도를 명시하지 않아 경고가 노출된다. stale closure 실동작 영향은 별도 검증 필요.

**서신서 Book 연대 범위 오표기 (수용된 한계):**
- `CONTAINS_BOOK.primary`(ADR-0012)로 사도행전·누가복음 topEvents 오염은 해소됐지만, "첫 참조=발생" 휴리스틱이 서신서의 신학적 회고 인용에는 오판정을 낳는다. authored_events 경로가 없는 책이라 CONTAINS_BOOK만으로는 연대를 정할 수 없는 것이 근본 원인.

**topEvents "대표성 절단" 편향 잔존:**
- `backend/app/routes/nodes.py:244–255`의 정렬(연도 오름차순 + `top_events[:10]` 하드 절단, `:255`)로, 사건이 많은 책은 topEvents 10개가 전부 초반부에 몰리고 후반 핵심 서사가 절단된다. ADR-0012 Consequences에 "범위 밖(잔존)"으로 명시된 별개 curation 이슈.

**TODO/FIXME/HACK/XXX 마커는 `backend/app`·`backend/scripts`·`frontend/src` 전역 0건** (재확인).

---

## Security Considerations

**CORS `allow_origins=["*"]`:**
- `backend/app/main.py:47`. `allow_methods=["GET"]`(`:49`)·`allow_credentials=False`(`:48`)로 읽기 전용 제한, API는 nginx 뒤에서만 노출(`docker-compose.yml`에 api host 포트 매핑 없음). 공개 읽기 API라 즉각 위험은 낮으나 향후 인증 추가 시 명시적 오리진 화이트리스트 필요.

**Cypher 인젝션 표면 (현재 방어됨):**
- `backend/app/routes/search.py:16–27`의 사용자값 `q`는 `$q` 파라미터 바인딩, f-string 삽입은 상수 `SEARCH_LIMIT`(`:6`)뿐. `nodes.py`의 f-string도 상수만 삽입. 단, `inject_date_corrections.py:60–89` `inject_persons`가 교정 파일의 `field` 값을 f-string으로 Cypher에 직접 삽입한다(`p.{field}`) — 입력이 레포 내 신뢰된 `data/date_corrections/persons.json`(현재 `deathYear` 등 정적 값)이라 실질 위험은 없으나, 이 파일을 신뢰 경계 밖에서 채우면 안 되는 구조적 제약.

**시크릿 취급 (양호):**
- `.env`는 `.gitignore`로 제외, git tracked env는 `.env.example`·`frontend/.env.production`(비밀 아님)뿐. `docker-compose.yml`이 `${NEO4J_PASSWORD:?...}`로 필수화. 모든 시드/검증 스크립트가 `NEO4J_PASSWORD` 미설정 시 `RuntimeError`로 즉시 중단(`load_books.py:11–12`, `inject_date_corrections.py:18–19`, `validate_event_chronology.py:28–29` 등). 하드코딩 시크릿 값 0건.

**사용자 제어 키 lru_cache — 무한 증가는 해소, 잔존 비대칭 유지:**
- `backend/app/routes/persons.py:145`·`:208`, `backend/app/routes/places.py`의 캐시 모두 `maxsize=256`. `places.py`의 정당한 key space(좌표 있는 Place 수)가 256에 근접하면 "캐시 스래싱"이 가능(원 DoS보다 약한 잔존 리스크). id 검증 없이 임의 문자열이 그대로 캐시 키가 되는 점은 동일.

---

## Performance Bottlenecks

**대용량 `event_verses` JSON 전체 인메모리 상주:**
- `data/event_verses/events.json`이 `backend/app/overlays.py`의 `lru_cache(maxsize=1)`로 프로세스당 상주. `backend/Dockerfile`이 uvicorn 단일 워커라 현재는 잠재적이나, 워커 다중화 시 워커당 중복 배증.

**`_build_id_to_slug()`에 캐시 없음:**
- `backend/app/routes/journey.py`: `lru_cache` 없이 요청마다 `_ERA`의 35개 slug JSON을 순회해 open/parse. `tours.py`의 재호출도 매 투어 상세 요청마다 이 무캐시 함수를 다시 돈다.

**전역 노드 스캔 검색:**
- `backend/app/routes/search.py:16–17`: `MATCH (n) WHERE n.nameKo CONTAINS $q OR toLower(n.name) CONTAINS toLower($q)` — 라벨·인덱스 미사용 전수 스캔.

---

## Fragile Areas

**`startDate`/연도 파싱·표기 로직이 다섯 곳에 중복 (task#158로 확대):**
- `frontend/src/dates.js:4–12` `parseYear`, `backend/app/routes/nodes.py:244–253` `_year`, `backend/scripts/load_books.py:56–68` `_parse_year`, **`backend/scripts/validate_event_chronology.py:64–75` `_year`(신규)**, `frontend/src/RelationsView.jsx:44` BC/AD 라벨. 규칙은 동일하나 공유 모듈로 추출되지 않았다.
- 회귀 방지 assert는 `load_books.py:72–76`(4개, 임포트 시점 실행)에만 있고 나머지 넷은 무보증 — 특히 새로 추가된 `validate_event_chronology.py`의 사본에도 assert가 없다.

**인물 관계가 `slug` 문자열 매칭에만 의존 — theographic_id 미사용:**
- `data/person_relations/relations.json`의 endpoint는 `{nameKo, slug}`만 담고, `backend/app/routes/persons.py:233`이 `slug_to_id.get(other["slug"])`로 `withId`를 해결한다. slug 오타·drift 시 여정 점프가 `null`로 조용히 실패(에러 없음). 3중 slug 소스(파일명·`_ERA`/`_NAME_KO`·relations endpoint) 일치를 강제하는 스키마·테스트는 없다.

**관계 뷰 `type`/`valence` 값이 프론트 상수와 암묵 결합:**
- `frontend/src/RelationsView.jsx`의 `TYPE_ICON`·`TYPE_ORDER`와 `theme.js`의 `VALENCE_COLOR`가 데이터 값과 하드코딩으로 짝지어져 있다. 새 값 추가 시 `null`·중립색으로 조용히 폴백.

**`TimelineView.personFilter`는 반드시 `Set`이어야 함 — 타입 계약 미강제:**
- `frontend/src/TimelineView.jsx`에서 `.has(...)`를 직접 호출. `import.meta.env.DEV` 가드는 개발 빌드에서만 경고, 프로덕션 빌드에서 Array 전달 시 크래시. 현재 호출 경로(`App.jsx`가 `Set`만 생성)는 안전하나 계약이 코드로 강제되지 않음.

**Neo4j 인덱스 생성 실패 시에도 서비스는 계속 기동:**
- `backend/app/main.py:37–38`: `except Exception:` → `logger.exception(...)` 후 인덱스 없이 계속 기동. 실패해도 서비스는 뜨고 전수 스캔 성능 저하만 남는다.

**프론트 stale 응답 무효화 패턴의 수동 관리:**
- `frontend/src/SidePanel.jsx`의 독립 `cancelled` 플래그 + `nodeId` 비교 패턴이 `RelationsView.jsx`·`App.jsx`에도 반복 구현. 공유 훅으로 추출되지 않아, 신규 비동기 fetch 추가 시 빠뜨리면 이전 데이터가 잠깐 노출된다.

**성품 통제 어휘가 문서·코드 이중 관리:**
- `backend/scripts/validate_traits.py`의 `VIRTUES`/`FLAWS` 집합(`:15` 이하)이 `data/character_traits/AUTHORING.md §3` 통제 어휘를 코드로 복제한다("문서와 함께 갱신할 것" 주석 명시). 한쪽만 고치면 검증이 문서와 어긋난다.

---

## Deployment / Ops Risks

**프론트 `:8080`은 `frontend/dist` 정적 마운트 — HMR 아님:**
- `docker-compose.yml`의 nginx 서비스 `- ./frontend/dist:/usr/share/nginx/html:ro`. 소스만 고치고 `npm run build`를 안 하면 `:8080`은 이전 빌드를 계속 서빙(에러 없음).

**API `:8000` 외부 미노출:**
- `docker-compose.yml`에 api host 포트 매핑 없음. `nginx/nginx.conf`의 `location /api/`로만 접근.

**nginx 속도 제한 없음:**
- `nginx/nginx.conf`에 `limit_req_zone`/`limit_req` 미설정. lru_cache가 256 상한이어도 rate limit 부재는 `places.py` 캐시 스래싱류 잔존 리스크를 악화시킬 조합.

---

## Scaling Limits

**단일 인스턴스 스택, 인메모리 캐시 공유 불가:**
- neo4j 1 + api 1(uvicorn 단일 워커) + nginx 1. API의 `lru_cache`들은 프로세스 로컬이라 다중 워커/컨테이너 확장 시 인스턴스별 중복·불일치. 무효화 수단이 앱 재시작뿐인 것도 그대로.

---

## Dependencies at Risk

**Theographic 데이터를 GitHub `master` HEAD에서 미고정 fetch:**
- `load_theographic.py`·`load_books.py`(`:14–15`)·`generate_event_verses.py`·`generate_verse_events.py`·`generate_book_context.py`·`generate_person_traits.py`가 `https://raw.githubusercontent.com/robertrouse/theographic-bible-metadata/master/json/*.json`을 커밋 SHA 고정 없이 직접 다운로드. 업스트림 스키마 변경 시 재시드 결과 변질 또는 `KeyError` 중단 위험. **`load_books.py`의 경우 이 미고정 fetch가 위 연대 롤백 함정과 결합** — 업스트림 원본이 곧 롤백 소스다.

**절 본문 프리베이크가 빌드타임 getbible 외부 호출에 의존:**
- `backend/scripts/generate_verse_text.py`의 UA 403 우회 로직이 여전히 필요. 새 절 추가마다 getbible 가용성·정책에 의존.

**Neo4j 이미지 메이저 버전만 고정:**
- `docker-compose.yml`의 `image: neo4j:5`. `neo4j:5.x.y` 패치 고정 권장.

---

## Test Coverage Gaps

- `*.test.*`/`*.spec.*` 파일 0건, pytest/vitest/jest 설정·`conftest.py`·`vitest.config.*` 전무. `frontend/package.json` scripts에 test 없음(dev/build/lint/preview).
- task#157·158로 **커밋된 데이터 검증 스크립트가 2개 생겼다** — `backend/scripts/validate_traits.py`(성품 통제 어휘·개수·형식), `backend/scripts/validate_event_chronology.py`(연대 역전·앵커·전치 오타). 종료코드 1로 위반을 신호하나 **둘 다 CI에 연결되지 않고 수동 실행 의존**이며, 위 Data Pipeline Footguns에서 지적한 대로 `validate_event_chronology.py`는 화이트리스트 3쌍만 알아 잔존 4건은 문서 대조로만 소명된다.
- 임포트 시점 assert는 `load_books.py:72–76`(`_parse_year` 회귀 4개)와 `generate_verse_text.py`의 `approxYear` 정수 assert뿐 — CI 미연결, 스크립트를 수동 실행해야 트립.
- 특히 위험 높은 미검증 지점:
  - BC/AD 연도 파싱·표기 5중 사본 중 assert 있는 것은 `load_books.py` 하나뿐(`dates.js`·`nodes.py`·`validate_event_chronology.py`·`RelationsView.jsx` 무보증).
  - `backend/app/routes/persons.py:209–237` `_build_relations` — slug↔id 매핑 계약·withId null 판정 미검증.
  - `backend/app/routes/nodes.py` Book 분기 — `rel.primary` 필터·topEvents 정렬/절단(서신서 엣지케이스 포함) 미검증.
  - date_corrections 파이프라인 — inject 재실행 누락·`load_books.py` 롤백은 자동 감지되지 않는다(연대 검증 스크립트를 사람이 돌려야 발견).
- UI 검증은 Playwright 수동 실행(로컬)에만 의존, CI 미연동.
