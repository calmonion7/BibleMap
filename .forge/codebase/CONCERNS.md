---
last_mapped_commit: 232fba9c2c3724daf4ee250eba876f1e46f4b6d9
mapped: 2026-07-09
---

# CONCERNS

현재 코드베이스에서 확인된 기술 부채·버그 위험·보안·성능·확장성·테스트 공백 목록.
각 항목은 HEAD(`232fba9`)에서 실제 파일·라인을 확인한 뒤 작성했다.

---

## Tech Debt

**시드 파이프라인이 `deploy.sh`와 단절됨 (재현성 최대 리스크):**
- `deploy.sh:57–72`의 [4/4] 단계는 `inject_ko_names.py` 하나만 재실행한다. `backend/scripts/`에는 총 21개 스크립트가 있고 그중 Neo4j 적재·주입 스크립트(`load_theographic.py`, `load_authored_persons.py`, `load_authored_events.py`, `load_books.py`, `load_person_events.py`, `load_verse_events.py`, `enrich_place_coords.py`, `inject_book_context.py`, `inject_place_context.py`, `inject_person_traits.py` 등)는 배포에 포함되지 않는다.
- Neo4j 볼륨(`docker-compose.yml`의 `neo4j_data`)이 살아있는 한 재실행 불필요하지만, **볼륨 삭제·신규 서버 프로비저닝·컨테이너 재생성 시 전체 재적재가 필요**하다. 그 완전한 실행 순서는 어디에도 정본화되어 있지 않다.
- Impact: 볼륨 손실 시 누락·순서 오류로 `HAS_PARTICIPANT` MATCH 실패, trait/context 누락 상태로 서비스 가동.

**시드 스크립트 실행 순서 암묵적:**
- `load_person_events.py`는 `MATCH (b:Book ...)`, `MATCH (p:Place ...)`로 기존 노드를 참조하므로 `load_books.py`·`load_theographic.py`·`enrich_place_coords.py`·`load_authored_persons.py`가 먼저 실행돼야 관계가 생성된다.
- 잘못된 순서로 재시드하면 `MATCH`가 0건을 반환해 관계가 조용히 누락된다(에러 없음).

**대형 프론트엔드 컴포넌트:**
- `frontend/src/SidePanel.jsx` — 705줄. Person/Place/Event/Book/PeopleGroup 5개 노드 타입의 분기 렌더, nodeId별 stale 무효화, 인라인 드릴다운 상태를 여러 `useState`로 한 파일에서 관리. 국소 변경 시 다른 노드 타입 렌더를 깨뜨리기 쉽다.
- `frontend/src/App.jsx` — 411줄. `useStageNavigation.js`·`useNodeSelection.js`로 일부 분리됐지만 상태 머신, fetch orchestration, 레이아웃 분기, RelationsView 두 곳 마운트(`App.jsx:340`, `App.jsx:399`)가 공존.
- `frontend/src/TimelineView.jsx` — 362줄.

**"큐레이션 13인" 주석이 현실과 어긋남 (stale, 확대됨):**
- `backend/app/routes/persons.py:1`(docstring)·`:135`, `backend/app/routes/journey.py:6`·`:77`, `frontend/src/PersonHub.jsx:153`에 "13인"이 고정돼 있으나 실제로는 `_ERA`가 **35개 slug**(`persons.py`), `data/person_events/`도 **35개 json**이다(HEAD에서 `job` 추가로 34→35). 문서·주석과 데이터의 괴리가 관계 시리즈·욥 추가로 더 벌어졌다.

---

## Known Bugs

명시적 런타임 버그는 확인되지 않았다. TODO/FIXME/HACK/XXX/@deprecated 마커는 `backend/app`·`backend/scripts`·`frontend/src` 전역 0건.

**최근 수정된 BC/AD 표기 버그 — 해소 확인됨:**
- `frontend/src/RelationsView.jsx:43`의 연도 헬퍼가 과거 `const bc = y => `BC ${Math.abs(y)}``로 부호를 무시해 AD 데이터(신약: 예수·베드로 등, 양수 `approxYear`)를 "BC 30"으로 오표기했다.
- HEAD에서 `const era = y => y < 0 ? `BC ${-y}` : `AD ${y}``로 교정됨(커밋 `409e1d0`). 뷰 내 3개 호출부(`:72` VerseLayer, `:122` 초점 스토리라인, `:177` 개요 칩) 모두 `era()`로 통일. **버그는 해소됨.** 단, 이 로직은 프론트에만 있고 `frontend/src/dates.js`·`backend/app/routes/nodes.py:238`의 유사 파싱과 별도 구현이라 아래 Fragile Areas의 "startDate 파싱 중복"에 새 세 번째 사본이 추가된 셈이다.

아래 Fragile Areas의 항목들이 잠재 결함(silent failure)에 해당한다.

---

## Security Considerations

**CORS `allow_origins=["*"]`:**
- `backend/app/main.py:27`. `allow_methods=["GET"]`(`:29`)로 읽기 전용 제한, `allow_credentials=False`(`:28`). API는 읽기 전용이고 nginx 뒤에서 운영되며 컨테이너 포트는 `127.0.0.1` 바인딩(`docker-compose.yml:5–6`).
- 공개 읽기 API라 즉각 위험은 낮지만, 향후 인증 레이어 추가 시 명시적 오리진 화이트리스트 필요.

**Cypher 인젝션 표면 (현재 방어됨):**
- `backend/app/routes/search.py:16–27`: 사용자값 `q`는 `$q` 파라미터 바인딩, f-string 삽입분은 상수 `SEARCH_LIMIT`만. `backend/app/routes/nodes.py`의 f-string 삽입분도 상수만. 현재 안전. 향후 f-string에 사용자값 직접 삽입 금지.

**시크릿 취급 (현재 양호):**
- `.env`는 `.gitignore:12`로 제외, git에 tracked된 env 파일은 `.env.example`·`frontend/.env.production`(비밀 아님)뿐. `docker-compose.yml`이 `${NEO4J_PASSWORD:?...}`로 필수화, `backend/app/db.py`가 env 누락 시 `RuntimeError`. **하드코딩된 시크릿 값 0건.**

---

## Performance Bottlenecks

**9.4MB `event_verses` JSON 전체 인메모리 상주:**
- `data/event_verses/events.json`가 9.4MB(이전 8.9MB에서 증가)로, `backend/app/overlays.py:44–47`의 `event_verses()` `lru_cache(maxsize=1)`로 프로세스당 상주.
- `backend/app/routes/events.py`의 사건 계산은 이 JSON + Neo4j 결과 병합본을 추가로 보관.
- `backend/Dockerfile`에서 uvicorn 단일 워커라 현재는 문제 잠재적. gunicorn 또는 `--workers N` 전환 시 워커당 중복 배증.

**`_build_id_to_slug()`에 캐시 없음 (여전히 미해결):**
- `backend/app/routes/journey.py:18–30`: `lru_cache` 없이 요청마다 `_ERA`의 **35개 slug JSON**을 순회해 open/parse. `/person/{id}/journey` 호출마다 35개 파일 I/O 반복. `tours.py`에서도 같은 함수를 호출하므로 투어 상세 요청마다 동일 오버헤드 발생. 인물 수 증가(욥·신약 6인 추가)로 파일 수가 늘어 비용이 커졌다.

**`places.py`의 `maxsize=None` 무한 캐시 (여전히 존재):**
- `backend/app/routes/places.py:19` `@functools.lru_cache(maxsize=None)`. 고유 `place_id` 수만큼 항목 무한 누적. 현재 규모라 허용 범위지만 상한이 없다.

**`_build_relations`도 `maxsize=None` (신규 확인):**
- `backend/app/routes/persons.py:206` `@functools.lru_cache(maxsize=None)`. `node_id`별로 캐시 성장. 실사용은 큐레이션 35인으로 사실상 유계지만 상한 미설정이라 임의 `node_id` 요청 시 무한 누적 가능. 그리고 무효화 수단이 앱 재시작뿐이라 `relations.json` 편집 후 재시작 없이 반영 불가.

**전역 노드 스캔 검색 (여전히 미해결):**
- `backend/app/routes/search.py:16–17`: `MATCH (n) WHERE n.nameKo CONTAINS $q OR toLower(n.name) CONTAINS toLower($q)` — 라벨·인덱스 미사용 전수 스캔. 데이터 규모 확대 시 지연.

---

## Fragile Areas

**인물 관계가 `slug` 문자열 매칭에만 의존 — theographic_id 미사용, 불일치가 조용히 삼켜짐 (신규 핵심 리스크):**
- `data/person_relations/relations.json`의 각 endpoint는 `{nameKo, slug}`만 담는다(총 171쌍, 627국면 확인). **theographic_id를 담지 않는다**(0건).
- `backend/app/routes/persons.py:207–235` `_build_relations`는 `_build_list()`가 만든 큐레이션 목록에서 `id_to_slug`/`slug_to_id`를 만들어 subject를 slug로 매칭하고, 상대 endpoint의 `withId`도 `slug_to_id.get(other["slug"])`로 해결한다.
- 위험: relations.json의 slug가 오타거나 `data/person_events/*.json` 파일명·`_ERA` 키와 어긋나면 `slug_to_id.get()`이 `None`을 반환해 **여정 점프 불가(withId null)** 상태가 되지만 에러는 없다. 비큐레이션 상대(예: 집단·미큐레이션 인물)는 의도적으로 `slug` 없이(현재 endpoint 중 1개가 `slug: None`) `withId: null`이 정상이라, 진짜 오타로 인한 null과 구분되지 않는다.
- 현재 정합성은 맞다(검증 결과: `person_events` 35개 = `_ERA` 35개, 상호 차집합 0; relations의 실 slug는 전부 `person_events`에 존재, 유일한 예외는 의도된 `None`). 그러나 이 3중 slug 소스(파일명 · `_ERA`/`_NAME_KO` dict · relations.json endpoint)의 일치를 **강제하는 스키마·테스트가 없다**. 신규 인물·관계 추가 시 한 곳만 어긋나도 조용히 깨진다.

**관계 뷰 `type`/`valence` 값이 프론트 상수와 암묵 결합 — 미매칭 시 아이콘 소실·회색 폴백:**
- `frontend/src/RelationsView.jsx:12–13`의 `TYPE_ICON`·`TYPE_ORDER`(9종: 하나님·가족·연인·친구·신하·선지자·스승제자·군주·대적)와 `:9` `VALENCE_COLOR`(긍정·부정·중립)가 데이터 값과 하드코딩으로 짝지어져 있다.
- 현재 데이터는 정확히 일치(검증: 데이터 type 9종·valence 3종 모두 상수에 존재). 그러나 `relations.json`에 새 `type`을 추가하면 `TypeIcon`이 `null`을 반환(`:16–19`)하고 `typeRank`가 99로 밀려(`:14`) 정렬 말미에 아이콘 없이 표시되며, 새 `valence`는 `?? '#8a94ad'` 회색 폴백(`:67`,`:119`,`:175`)으로 조용히 뭉개진다. 데이터-코드 동기화 강제 없음.

**`TimelineView.personFilter`는 반드시 `Set`이어야 함 — 타입 계약 미강제:**
- `frontend/src/TimelineView.jsx:104`에서 `activePersonFilter.has(ev.id)`를 직접 호출한다. `Array`를 넘기면 `x.has is not a function` 런타임 크래시.
- `TimelineView.jsx:21–23`에 `import.meta.env.DEV` 가드가 있어 개발 빌드에서만 `console.error` 경고를 낸다. 프로덕션 빌드에서는 가드가 제거되어 Array 전달 시 여전히 크래시. PropTypes/TypeScript 타입 선언 없음.

**`startDate`/연도 파싱 로직이 이제 세 곳에 중복:**
- `"-4003"`, `"-1451-01"`, `"0049-10-01"` 형식 혼재 연도 파싱 + 부호 기반 BC/AD 판정이 서로 독립 구현됨.
  - `frontend/src/dates.js:4–12` `parseYear()`: BC 접두 감지 후 제로패딩 제거·레이블 반환.
  - `backend/app/routes/nodes.py:238–248` `_year()`: 동일 패턴에 `int()` 변환·부호 반전(정렬용 숫자).
  - `frontend/src/RelationsView.jsx:43` `era()`: 부호로 BC/AD 판정(관계 국면 `approxYear`는 이미 정수라 파싱은 없지만 BC/AD 표기 규칙이 중복). 방금 BC/AD 버그가 여기서 났다.
- 한쪽만 수정하면 BC/AD 경계·제로패딩 처리가 엇갈릴 수 있다. 셋 다 테스트 없음.

**침묵하는 예외 처리:**
- `backend/app/main.py:16–19`: 인덱스 생성 실패를 `except Exception`으로 삼키고 계속(로깅). 인덱스 없이 기동해 전수 스캔 성능 저하.
- `backend/app/routes/nodes.py:255–257`: Person traits JSON 파싱 실패 시 `except Exception`으로 빈 배열 반환. 데이터 누락이 UI에서 조용히 숨겨짐.
- `backend/app/overlays.py:34–35`: `json.JSONDecodeError`를 빈 dict로 삼킴. 오버레이 파일이 깨져도 서비스는 빈 데이터로 가동.

**프론트 stale 응답 무효화 패턴의 수동 관리:**
- `frontend/src/SidePanel.jsx:47–108`: `cancelled` 플래그 + `state.id`로 stale 판별, `curatedIds?.has(node.id)`로 관계 노출 조건 판별. `frontend/src/RelationsView.jsx:26–37`도 `cancelled` + `state.id !== personId` 가드를 각자 반복 구현. 신규 비동기 fetch 추가 시 이 패턴을 빠뜨리면 이전 노드/인물 데이터가 잠깐 노출됨.

---

## Deployment / Ops Risks

**프론트 `:8080`은 `frontend/dist` 정적 마운트 — HMR 아님, stale 빌드가 조용히 구코드 서빙:**
- `docker-compose.yml:30` `- ./frontend/dist:/usr/share/nginx/html:ro`. nginx는 이 디렉터리를 그대로 서빙(`nginx/nginx.conf`의 `root /usr/share/nginx/html`). 소스만 고치고 `npm run build`를 안 하면 `:8080`은 **이전 빌드를 계속 서빙**하며 아무 에러도 없다. 로컬 검증 전 반드시 `cd frontend && npm run build` 필요(프로젝트 메모리에도 기록됨).
- `frontend/dist`는 git에 tracked 안 됨(0건) — 배포는 `deploy.sh:44–47`가 러너에서 build를 수행해 생성. 로컬 검증과 배포 빌드 경로가 이원화되어 로컬 stale 빌드로 인한 "고쳤는데 안 바뀜" 함정 상존.

**API `:8000` 외부 미노출:**
- `docker-compose.yml`에 api 서비스의 host 포트 매핑 없음. `nginx.conf:12–13`의 `location /api/ { proxy_pass http://api:8000/; }`로만 접근. 컨테이너 밖에서 API 직접 호출 불가 — 검증 시 `:8080/api/...`를 써야 한다.

**nginx 속도 제한 없음:**
- `nginx/nginx.conf`에 `limit_req_zone`/`limit_req` 미설정. 공개 API 과도 스크레이핑 시 uvicorn 단일 프로세스 포화.

---

## Scaling Limits

**단일 인스턴스 스택, 인메모리 캐시 공유 불가:**
- neo4j 1 + api 1 + nginx 1 컨테이너. API가 다수 `lru_cache`(`overlays.py`·`persons.py`·`places.py`)에 의존하므로 워커/컨테이너 다중화 시 캐시 인스턴스별 중복·불일치. 무효화 수단이 앱 재시작뿐.
- 데이터가 정적이라 재시작 무효화로 충분한 규모까지는 안전.

---

## Dependencies at Risk

**Theographic 데이터를 GitHub `master` HEAD에서 미고정 fetch:**
- `backend/scripts/load_theographic.py`·`load_books.py`·`generate_event_verses.py` 등 여러 스크립트가 `https://raw.githubusercontent.com/robertrouse/theographic-bible-metadata/master/json/*.json`을 직접 다운로드. 커밋 SHA 고정·로컬 스냅샷 없음.
- 업스트림 스키마 변경 시 재시드 결과가 달라지거나 `KeyError`로 중단. 네트워크 불가 시 재시드 실패.

**절 본문 프리베이크가 빌드타임 getbible 외부 호출에 의존:**
- `backend/scripts/generate_verse_text.py`가 event_verses·book_context·character_traits·place_context·relations의 인용 절 본문을 빌드타임에 getbible에서 fetch해 인라인 저장(ADR-0003). 실패분은 `null`로 기록해 재시도 가능하고 런타임엔 외부 호출이 없다. 현재 `relations.json`의 627국면 verseTextKo null 0건(전부 프리베이크 완료). 다만 새 절 추가 시마다 getbible 가용성에 의존하며, getbible는 기본 urllib UA에 403을 주므로(`generate_verse_text.py`의 `_UA` 우회) 업스트림 정책 변경에 취약.

**Neo4j 이미지 메이저 버전만 고정 (`neo4j:5`):**
- `docker-compose.yml:3`. 마이너·패치가 자동 적용되어 드라이버 호환성 문제 가능. `neo4j:5.x.y` 형태로 고정 권장.

**프론트 React 19 + 캐럿 범위 의존성:**
- `frontend/package.json`: `react@^19.x`, `maplibre-gl@^5.x`, `lucide-react@^1.x`. `maplibre-gl`은 지도 렌더 핵심이라 메이저 변경 시 `mapLayers.js`/`mapGeo.js`/`mapRingController.js` 영향. `lucide-react`는 `RelationsView.jsx:2`의 관계 유형 아이콘 9종에 직접 의존. lockfile 유지로 재현성 확보 중.

---

## Missing Critical Features

**시드 전체 재현 자동화 부재:**
- 전체 그래프를 처음부터 재구성하는 단일 진입점 없음. `deploy.sh`는 프론트 빌드·API 이미지 빌드·컨테이너 재시작·`inject_ko_names.py`만 수행한다. 볼륨 손실 시 신뢰할 수 있는 복구 경로·신규 환경 부트스트랩·데이터 커밋의 자동 반영 모두 차단됨.

**관계·인물 데이터 정합성 검증기 부재:**
- slug 3중 소스 일치(파일명 · `_ERA`/`_NAME_KO` · relations.json endpoint), relations `type`/`valence`의 프론트 상수 매칭, `withId` 해결 성공 여부를 확인하는 CI/스크립트가 없다. `data/person_relations/AUTHORING.md`에 저작 규칙은 정본화됐으나 자동 검증은 없다. 위 Fragile Areas의 slug/타입 드리프트가 감지되지 않는다.

---

## Test Coverage Gaps

- `*.test.*`/`*.spec.*` 파일 0건, pytest/vitest/jest 설정 없음. `frontend/package.json` scripts에 test 없음(dev/build/lint/preview만).
- 특히 위험 높은 미검증 지점:
  - `frontend/src/dates.js:4–12` `parseYear` · `backend/app/routes/nodes.py:238–248` `_year` · `frontend/src/RelationsView.jsx:43` `era` — BC/AD 연도 파싱·표기 로직 3중 사본. 방금 BC/AD 버그가 여기서 났고, 순수 함수라 테스트 비용 낮고 회귀 위험 크다.
  - `backend/app/routes/persons.py:207–235` `_build_relations` — slug↔id 매핑 계약. withId null 판정·note 폴백·유형 통과 로직 미검증.
  - `backend/app/routes/journey.py` — 여정 stop 생성·seq 부여 로직, `_build_id_to_slug` 35파일 순회.
  - `backend/app/routes/tours.py` — 투어 stop 조립, era 정렬, event_index 빌드.
  - `backend/app/overlays.py:11–16` `_resolve` — DATA_DIR 우선순위 검증 불가.
- UI 검증은 Playwright 수동 실행(로컬)에만 의존. CI 미연동.
- BC/AD 표기 회귀, slug 3중 소스 드리프트, relations type/valence 미매칭, 시드 순서 오류로 인한 관계 누락 모두 자동으로 감지되지 않는다.
