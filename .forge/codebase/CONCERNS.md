---
last_mapped_commit: 9c49a838dfe4c6e4695b9383ea961f15c9b117f2
mapped: 2026-07-10
---

# CONCERNS

현재 코드베이스에서 확인된 기술 부채·버그 위험·보안·성능·확장성·테스트 공백 목록.
각 항목은 HEAD(`9c49a838`)에서 실제 파일·라인, 그리고 가능한 경우 실행 중인 스택(`docker compose`, `localhost:8080`)에 대한 실측으로 확인했다.

이번 갱신 배경: task#150 버그 헌트(`.forge/bug-report.md`, confirmed 12·refuted 3)가 6렌즈 병렬 탐색으로 새 결함을 발견했고, task#151~154가 그 12건 전부를 외과적으로 수정했다(#1·#3·#5·#6·#7·#8·#9는 `068fa7b`, #4는 `76115ce`, #10은 `6f73d31`, #11·#12는 `9c49a838`). 아래는 이 수정들을 반영해 해소된 항목은 "해소 확인됨"으로 갱신하고, 그 과정에서 새로 드러났거나 잔존이 확인된 항목을 추가한 결과다.

---

## Tech Debt

**시드 파이프라인이 `deploy.sh`와 단절됨 (재현성 최대 리스크, 여전함):**
- `deploy.sh:49–63`의 [4/4] 단계는 `inject_ko_names.py` 하나만 재실행한다. `backend/scripts/`에는 `__init__.py` 제외 20개 스크립트가 있고, 그중 Neo4j 적재 스크립트(`load_theographic.py`, `load_authored_persons.py`, `load_authored_events.py`, `load_books.py`, `load_person_events.py`, `load_verse_events.py`)와 주입 스크립트(`enrich_place_coords.py`, `inject_book_context.py`, `inject_place_context.py`, `inject_person_traits.py`)는 배포에 포함되지 않는다.
- task#152(`76115ce`)가 `CONTAINS_BOOK.primary` 라이브 마이그레이션(943관계)을 일회성 스크립트로 적용했다고 ADR-0012에 명시(`.forge/adr/0012-contains-book-primary-occurrence-vs-citation.md:14` "CONCERNS의 '재현 자동화 부재'는 이 태스크가 해소하지 않음") — 즉 이번 수정 사이클도 이 갭을 메우지 않았고, 오히려 "재시드 시 `load_books.py`/`load_person_events.py`가 `primary`를 세팅하지만 기존 라이브 데이터는 별도 마이그레이션으로만 맞춰졌다"는 재현 경로가 하나 더 늘었다.
- Neo4j 볼륨(`docker-compose.yml`의 `neo4j_data`)이 살아있는 한 재실행 불필요하지만, **볼륨 삭제·신규 서버 프로비저닝·컨테이너 재생성 시 전체 재적재 + primary 마이그레이션까지 재현해야** 한다. 정본화된 단일 실행 순서는 여전히 없다.

**시드 스크립트 실행 순서 암묵적 (여전함):**
- `load_person_events.py`는 `MATCH (b:Book ...)`, `MATCH (p:Place ...)`로 기존 노드를 참조하므로 `load_books.py`·`load_theographic.py`·`enrich_place_coords.py`·`load_authored_persons.py`가 먼저 실행돼야 관계가 생성된다. 잘못된 순서로 재시드하면 `MATCH`가 0건을 반환해 관계가 조용히 누락된다(에러 없음).

**대형 프론트엔드 컴포넌트 (라인 수 갱신):**
- `frontend/src/SidePanel.jsx` — 705줄(변동 없음). Person/Place/Event/Book/PeopleGroup 5개 노드 타입 분기 렌더 + nodeId별 stale 무효화 패턴을 한 파일에서 관리.
- `frontend/src/App.jsx` — 425줄(이전 411줄에서 증가, task#153의 explorePersonId 구동 `personEventIds` effect 추가분). `useStageNavigation.js`·`useNodeSelection.js`로 상태 일부 분리됐지만 여전히 상태 머신·fetch orchestration·레이아웃 분기가 공존.
- `frontend/src/TimelineView.jsx` — 362줄(변동 없음).
- (이전 맵의 "RelationsView 두 곳 마운트" 항목은 현재 코드에서 확인되지 않음 — `App.jsx`에 `RelationsView` 마운트 지점 1곳(`:354`)만 존재. 해소됨/오기재였던 것으로 보여 제거.)

**"큐레이션 13인" 주석이 현실과 계속 어긋남 (여전함):**
- `backend/app/routes/persons.py:1`(docstring)·`:137`, `backend/app/routes/journey.py:6`·`:77`, `frontend/src/PersonHub.jsx:153`에 "13인"이 고정돼 있으나 `_ERA`는 여전히 **35개 slug**(`persons.py:20–56`), `data/person_events/`도 35개 json(파일명 집합과 `_ERA` 키 집합 diff 0 — 기계 검증 완료). 이번 사이클(task#150~154)은 인물 데이터를 추가하지 않아 괴리 폭 자체는 그대로지만, 다음 인물 추가 시마다 벌어진다.

---

## Known Bugs

**버그 헌트 1차 사이클(task#150) — confirmed 12건, task#151~154에서 전부 수정 완료:**
- `.forge/bug-report.md`에 6렌즈 병렬 발굴 → dedup → finding별 적대적 검증(코드 재추적 + 라이브 API/Neo4j 실측) 과정과 결과가 남아있다. HIGH 2건(#1 오버레이 무음, #2 Book 연도 파싱)·MEDIUM 10건 전부 confirmed, 수정도 전부 라이브 코드에서 재확인됨(아래 각 섹션에 반영). refuted 3건(dates.js 0-연도 비대칭, mapLayers 언마운트 경합, place_coords.json 누락)도 투명성을 위해 리포트에 남아있다 — 코드상 현상 자체는 사실이나 실제 도달 불가/무해로 반박됐다.
- TODO/FIXME/HACK/XXX/@deprecated 마커는 `backend/app`·`backend/scripts`·`frontend/src` 전역 여전히 0건.

**히브리서 등 서신서의 Book 연대 범위 오표기 (라이브 확인, 수용된 한계):**
- task#152(ADR-0012)가 CONTAINS_BOOK에 `primary`(발생 vs 인용) 구분을 도입해 사도행전·누가복음의 topEvents 오염은 해소했지만, "첫 참조=발생" 휴리스틱이 서신서의 신학적 회고 인용에는 오판정을 낳는다. 라이브 확인: `curl localhost:8080/api/node/recKvTNUismk1ckEr`(히브리서) → `startYear: -3899, endYear: -3899` — 실제 집필 시기(AD 60년대, 같은 응답의 `writtenDate: "AD 60년대"`)와 무관하게 히 11:4(아벨의 믿음, verses[0])가 발생으로 오판정되어 범위가 BC 3899로 고정됨. `.forge/retro/2026-07-10-topevents-occurrence-vs-citation.md:7`에 "내재적 한계"로 명시적으로 기록된 기지(既知) 이슈 — 서신서는 CONTAINS_BOOK으로 연대를 정할 수 없다는 것이 근본 원인(ADR-0005)이며, 별도 후속(authored_events 경로 도입) 없이는 해소 불가.

**topEvents "대표성 절단" 편향 잔존 (라이브 확인):**
- primary 필터(task#152)가 다른 책의 인용 오염은 제거했지만, `nodes.py:249–259`의 정렬 로직(연도 오름차순 + `top_events[:10]` 하드 절단)은 그대로다. 라이브 확인: `curl localhost:8080/api/node/recF09FMjRr0gzjQk`(사도행전) → topEvents 10개 전부 `startDate` `0030`(오순절~스데반 순교 등 초반 사건)뿐 — 바울의 회심(AD34)·선교여행(AD46-57)·재판·로마행 등 사도행전 후반 핵심 서사가 전부 절단된다. ADR-0012 Consequences(`:16`)에 "범위 밖(잔존)"으로 명시된 별개 curation 이슈.

---

## Security Considerations

**CORS `allow_origins=["*"]` (변동 없음):**
- `backend/app/main.py:47`. `allow_methods=["GET"]`(`:49`)·`allow_credentials=False`(`:48`)로 읽기 전용 제한. API는 nginx 뒤 `127.0.0.1` 바인딩(`docker-compose.yml`에 api 서비스 host 포트 매핑 없음). 공개 읽기 API라 즉각 위험은 낮지만, 향후 인증 레이어 추가 시 명시적 오리진 화이트리스트 필요.

**Cypher 인젝션 표면 (현재 방어됨, 변동 없음):**
- `backend/app/routes/search.py:14–29`: 사용자값 `q`는 `$q` 파라미터 바인딩, f-string 삽입분은 상수 `SEARCH_LIMIT`뿐. `backend/app/routes/nodes.py:172–175`의 f-string도 상수 `NODE_NEIGHBOR_LIMIT`만 삽입. 안전.

**시크릿 취급 (현재 양호, 변동 없음):**
- `.env`는 `.gitignore:12`로 제외, git tracked인 env 파일은 `.env.example`·`frontend/.env.production`(비밀 아님)뿐. `docker-compose.yml`이 `${NEO4J_PASSWORD:?...}`로 필수화. 하드코딩된 시크릿 값 0건.

**RESOLVED — 사용자 제어 키 무한 lru_cache (구 finding #5/#7 + 인접 `_build_connections`):**
- `068fa7b`가 `persons.py:145`(`_build_connections`)·`persons.py:208`(`_build_relations`)·`places.py:21`(`_place_to_persons`) 세 곳 모두 `maxsize=None → maxsize=256`으로 교체 확인됨. 인증 없는 임의 문자열 대량 요청으로 인한 무한 메모리 누적(DoS)은 해소.
- **잔존 비대칭(신규 확인)**: `places.py`의 정당한 key space(실제 좌표 있는 Place 노드 수)를 라이브 Neo4j로 직접 세어보니 **239개**(`MATCH (p:Place) WHERE p.latitude IS NOT NULL RETURN count(p)` → 239) — `maxsize=256`과 마진이 17뿐이라, 사용자가 여러 장소를 정상적으로 돌아다니기만 해도 캐시가 포화에 가까워지고 소수의 무의미한 id 요청만으로 정당한 항목이 축출되는 "캐시 스래싱"이 재현 가능하다(메모리 무한 증가는 아니므로 원래 DoS보다는 훨씬 약한 잔존 리스크). 반면 `persons.py`의 두 캐시는 정당한 key space가 큐레이션 35인으로 한정되어 256 대비 마진이 넉넉해 이 리스크가 사실상 없다. id 검증(존재하는 Place/Person인지 확인 후에만 캐시) 없이 여전히 임의 문자열이 그대로 캐시 키가 된다는 점은 동일.

---

## Performance Bottlenecks

**9.4MB `event_verses` JSON 전체 인메모리 상주 (변동 없음):**
- `data/event_verses/events.json`가 9.4MB로, `backend/app/overlays.py`의 `event_verses()` `lru_cache(maxsize=1)`로 프로세스당 상주. `backend/Dockerfile`이 uvicorn 단일 워커(`CMD ["uvicorn", ...]`, `--workers` 미지정)라 현재는 문제 잠재적이나, 워커 다중화 시 워커당 중복 배증.

**`_build_id_to_slug()`에 캐시 없음 (여전히 미해결):**
- `backend/app/routes/journey.py:18–30`: `lru_cache` 없이 요청마다 `_ERA`의 35개 slug JSON을 순회해 open/parse. `/person/{id}/journey`·`tours.py`의 투어 상세 요청마다 반복 I/O.

**RESOLVED — places/persons 계열 lru_cache 무한 누적:**
- `places.py:21`·`persons.py:145`·`persons.py:208` 모두 `maxsize=256`로 상한 설정 확인됨(위 Security 섹션의 잔존 비대칭 참고).

**전역 노드 스캔 검색 (여전히 미해결):**
- `backend/app/routes/search.py:16–17`: `MATCH (n) WHERE n.nameKo CONTAINS $q OR toLower(n.name) CONTAINS toLower($q)` — 라벨·인덱스 미사용 전수 스캔.

---

## Fragile Areas

**인물 관계가 `slug` 문자열 매칭에만 의존 — theographic_id 미사용 (변동 없음):**
- `data/person_relations/relations.json`의 각 endpoint는 `{nameKo, slug}`만 담는다(171쌍, 627국면 — task#148의 국면 문맥 절 보완 이후도 국면 수 동일, phase 개수 자체는 안 늘었고 각 phase에 context 필드만 보강됨). `backend/app/routes/persons.py:209–235` `_build_relations`가 `slug_to_id.get(other["slug"])`로 `withId`를 해결한다. slug 오타·drift 시 여정 점프가 `null`로 조용히 실패하지만 에러는 없다. 3중 slug 소스(파일명·`_ERA`/`_NAME_KO`·relations endpoint) 일치를 강제하는 스키마·테스트는 여전히 없다.

**관계 뷰 `type`/`valence` 값이 프론트 상수와 암묵 결합 (변동 없음):**
- `frontend/src/RelationsView.jsx:12`의 `TYPE_ICON`(9종)·`:13` `TYPE_ORDER`와 `:9` `VALENCE_COLOR`(3종)가 데이터 값과 하드코딩으로 짝지어져 있다. 현재 데이터는 정확히 일치(task#150 기계검증: 데이터 type 9종·valence 3종 모두 상수에 존재, PASS). 새 `type`/`valence` 추가 시 `TypeIcon`이 `null`(`:17`)·회색 폴백(`:67`,`:119`,`:175`)으로 조용히 뭉개지는 구조는 그대로.

**`TimelineView.personFilter`는 반드시 `Set`이어야 함 — 타입 계약 미강제 (변동 없음):**
- `frontend/src/TimelineView.jsx:104`에서 `activePersonFilter.has(ev.id)` 직접 호출. `:22`의 `import.meta.env.DEV` 가드는 개발 빌드에서만 경고, 프로덕션 빌드에서는 Array 전달 시 여전히 크래시. task#153이 `personEventIds`를 `App.jsx`의 `useState(null) + useEffect`로 명시적으로 `Set`만 만들도록 옮겨(App.jsx:53–64) 현재 호출 경로는 안전하지만, 타입 계약 자체가 코드로 강제되는 것은 아니다.

**`startDate`/연도 파싱 로직이 이제 네 곳에 중복 (3곳→4곳, 신규 확인):**
- 기존 3곳에 더해 task#151(#2 수정)이 `backend/scripts/load_books.py:56–68`에 `_parse_year()`를 새로 추가했다 — `frontend/src/dates.js:4–12` `parseYear()`, `backend/app/routes/nodes.py:238–248` `_year()`(변동 없음, 같은 로직)와 동일 규칙(부호 분리 후 첫 `-` 이전만 정수화)을 네 번째로 재구현한 것.
  - `frontend/src/RelationsView.jsx:43` `const era = y => y < 0 ? \`BC ${-y}\` : \`AD ${y}\`` — 관계 phase의 `approxYear`는 이미 정수라 파싱은 없지만 BC/AD 표기 규칙 자체는 중복.
  - `load_books.py:65–68`에 회귀 방지 `assert` 4개(`_parse_year("-1451-01") == -1451` 등)가 추가됐다 — 이 저장소에서 **유일하게 존재하는 자동 검증**(import 시점 실행, CI 아님)이지만, 정작 이 로직을 공유 모듈로 추출하진 않아 넷 중 셋(`dates.js`/`nodes.py`/`RelationsView.jsx`)은 여전히 무보증이다.

**RESOLVED — 침묵하는 예외 처리 (overlays 파일 부재):**
- `backend/app/overlays.py:14–22`의 `_resolve`/`_resolve_dir`가 두 후보 경로 모두 실패 시 `logger.warning("[Overlays] 오버레이 파일/디렉터리 없음 — 빈 데이터로 폴백 ...")`을 남기도록 수정 확인됨(`:20`,`:30`). `_load`의 `json.JSONDecodeError` 로깅(`:42`)과 대칭 회복.
- **배경(신규 확인)**: 이 경고가 왜 실전에서 중요한지 — `backend/Dockerfile:5` `COPY app/ ./app/`는 레포 전체가 아니라 `app/` 디렉터리만 이미지에 넣는다. `overlays.py:9–12`의 `_REPO_DATA_DIR`(레포 루트 기준 `data/`)는 컨테이너 안에서 `/app/app/overlays.py` 기준 상위 경로라 **애초에 존재하지 않는 죽은 폴백**이고, 프로덕션의 유일한 실경로는 `docker-compose.yml:20`의 `./data:/app/data` 볼륨 마운트뿐이다. 이 마운트가 실패하면 이제 로그로 즉시 드러난다.

**RESOLVED(개선) — Person traits 파싱 실패 로깅:**
- `backend/app/routes/nodes.py:255–260`: `except Exception`은 여전히 넓지만 `logger.warning("[Nodes] Person traits 파싱 실패 — 빈 목록 폴백 (%s): %s", node_id, e)`로 원인이 로그에 남는다(task#149 로깅 규약 정본화, `4a3d925`). 데이터는 여전히 빈 배열로 조용히 폴백되나 관측 가능.

**부분 개선 — Neo4j 인덱스 생성 실패:**
- `backend/app/main.py:37–40`: `except Exception:`이 `logger.exception(...)`으로 전체 스택트레이스를 남기도록 개선됐다(task#149). 다만 인덱스 없이 계속 기동하는 동작 자체는 그대로 — 실패해도 서비스는 뜨고 전수 스캔 성능 저하만 남는다.

**프론트 stale 응답 무효화 패턴의 수동 관리 (변동 없음, 라인 갱신):**
- `frontend/src/SidePanel.jsx:65–107`: 3개의 독립된 `cancelled` 플래그 + `nodeId`/`state.id` 비교로 stale 판별(노드 fetch·장소 경유 인물·인물 연결 각각). `frontend/src/RelationsView.jsx:26–32`도 같은 패턴을 반복 구현. 신규 비동기 fetch 추가 시 이 패턴을 빠뜨리면 이전 노드/인물 데이터가 잠깐 노출된다 — 공유 훅으로 추출되지 않음.

---

## Deployment / Ops Risks

**프론트 `:8080`은 `frontend/dist` 정적 마운트 — HMR 아님 (변동 없음):**
- `docker-compose.yml:30` `- ./frontend/dist:/usr/share/nginx/html:ro`. 소스만 고치고 `npm run build`를 안 하면 `:8080`은 이전 빌드를 계속 서빙하며 에러 없음. `data/person_relations/AUTHORING.md:66,67`의 검증 파이프라인 규칙 8도 "npm run build" + "docker compose restart api"(단순 `up -d`는 컨테이너 재생성 안 해 옛 데이터 계속 서빙)를 명시적 footgun으로 문서화하고 있다.

**API `:8000` 외부 미노출 (변동 없음):**
- `docker-compose.yml`에 api 서비스 host 포트 매핑 없음. `nginx/nginx.conf:12–13`의 `location /api/`로만 접근.

**nginx 속도 제한 없음 (변동 없음):**
- `nginx/nginx.conf`에 `limit_req_zone`/`limit_req` 미설정. lru_cache가 256으로 상한 설정됐어도(위 Security 참고), rate limit 부재는 places.py 캐시 스래싱류 잔존 리스크를 그대로 악화시킬 수 있는 조합이다.

---

## Scaling Limits

**단일 인스턴스 스택, 인메모리 캐시 공유 불가 (변동 없음):**
- neo4j 1 + api 1(uvicorn 단일 워커) + nginx 1 컨테이너. API의 `lru_cache`들(`overlays.py`·`persons.py`·`places.py`, 이제 상한 1 또는 256)은 프로세스 로컬이라 다중 워커/컨테이너 확장 시 인스턴스별 중복·불일치. 무효화 수단이 앱 재시작뿐인 것도 그대로(`AUTHORING.md:66` 규칙 8이 이를 수동 절차로 문서화).

---

## Dependencies at Risk

**Theographic 데이터를 GitHub `master` HEAD에서 미고정 fetch (변동 없음):**
- `load_theographic.py`·`load_books.py`·`generate_event_verses.py`·`generate_verse_events.py`·`generate_book_context.py`·`generate_person_traits.py` 등이 `https://raw.githubusercontent.com/robertrouse/theographic-bible-metadata/master/json/*.json`을 커밋 SHA 고정 없이 직접 다운로드. 업스트림 스키마 변경 시 재시드 결과 변질 또는 `KeyError` 중단 위험.

**절 본문 프리베이크가 빌드타임 getbible 외부 호출에 의존 (변동 없음):**
- `backend/scripts/generate_verse_text.py`의 `_UA`(`:55`)로 getbible 기본 UA 403을 우회. task#150 기계검증(2026-07-10)에서 relations 627국면 전건 `verseTextKo` null 0건 확인, task#151이 `bake_relations()`에 `approxYear` 정수 assert(`:222–225`)까지 추가해 저작 실수 조기 발견력이 늘었다. 여전히 새 절 추가마다 getbible 가용성·정책 변경에 의존.

**Neo4j 이미지 메이저 버전만 고정 (변동 없음):**
- `docker-compose.yml:3` `neo4j:5`. `neo4j:5.x.y` 고정 권장.

**프론트 의존성 버전 (수치 갱신):**
- `frontend/package.json`: `react@^19.2.6`, `react-dom@^19.2.6`, `maplibre-gl@^5.24.0`, `lucide-react@^1.17.0`. `maplibre-gl`은 지도 렌더 핵심, `lucide-react`는 `RelationsView.jsx:12`의 관계 유형 아이콘 9종에 직접 의존. lockfile 유지로 재현성 확보 중.

---

## Missing Critical Features

**시드 전체 재현 자동화 부재 (변동 없음, ADR로 재확인):**
- `deploy.sh`는 여전히 프론트 빌드·API 이미지 빌드·컨테이너 재시작·`inject_ko_names.py`만 수행. ADR-0012(`:14`)가 task#152의 `primary` 라이브 마이그레이션도 "이 태스크가 재현 자동화를 해소하지 않음"이라고 명시적으로 남겨, 재현 갭이 줄지 않고 오히려 재현해야 할 단계(마이그레이션)가 하나 늘었음을 스스로 기록했다.

**관계·인물 데이터 정합성 검증기 부재 (부분 완화, 자동화는 여전히 없음):**
- task#150이 slug 3중 소스 일치·type/valence 매칭·approxYear 정수성·tours stops 참조 무결성을 python 스크립트로 1회 기계검증했다(`.forge/bug-report.md` "데이터 계약 기계검증 결과" 표, 7개 검사 중 6 PASS·1 FAIL→approxYear는 이후 수정). 하지만 이 검증 스크립트는 **레포에 커밋되지 않은 1회성 실행**이었다(`.forge/reports/`는 git 미추적 스크래치 디렉터리). `AUTHORING.md:64–69`의 "규칙 8 검증 파이프라인"도 사람이 5단계를 수동 실행하는 체크리스트이지 CI/자동화가 아니다. 다음 저작 사이클에서 slug/타입 드리프트가 재발해도 자동으로 잡히지 않는다.

---

## Test Coverage Gaps

- `*.test.*`/`*.spec.*` 파일 0건, pytest/vitest/jest 설정·`conftest.py`·`pytest.ini` 전무. `frontend/package.json` scripts에 test 없음(dev/build/lint/preview만).
- 이 저장소에서 유일하게 존재하는 자동 검증은 `backend/scripts/load_books.py:65–68`의 `assert` 4개(`_parse_year` 회귀 방지, import 시점 실행)와 `generate_verse_text.py:222–225`의 `approxYear` 정수 assert뿐 — 둘 다 CI에 연결되지 않고, 스크립트를 수동 실행해야만 트립된다.
- 특히 위험 높은 미검증 지점(갱신):
  - `frontend/src/dates.js:4–12` `parseYear` · `backend/app/routes/nodes.py:238–248` `_year` · `frontend/src/RelationsView.jsx:43` `era` · `backend/scripts/load_books.py:56–68` `_parse_year` — BC/AD 연도 파싱·표기 로직 4중 사본 중 3곳은 assert도 없다.
  - `backend/app/routes/persons.py:209–235` `_build_relations` — slug↔id 매핑 계약, withId null 판정, note 폴백 로직 미검증.
  - `backend/app/routes/nodes.py:207–260` Book 분기 — `rel.primary` 필터·topEvents 정렬/절단 로직(서신서 엣지케이스 포함) 미검증.
  - `backend/app/routes/tours.py:56–72` `_build_event_index` — 중복 eventId 경고 가드(task#151 신규) 미검증.
  - `backend/app/overlays.py:14–31` `_resolve`/`_resolve_dir`/`_load` — 새로 추가된 로깅 대칭(파일 부재 경로) 미검증.
- UI 검증은 Playwright 수동 실행(로컬)에만 의존, CI 미연동. BC/AD 표기 회귀, slug 3중 소스 드리프트, relations type/valence 미매칭, `rel.primary` 세팅 누락, 시드 순서 오류로 인한 관계 누락 모두 자동으로 감지되지 않는다.
