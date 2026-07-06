---
last_mapped_commit: 95ba754e0a5b8a8db6f537f88d6d4e60d302d066
mapped: 2026-07-06
---

# CONCERNS

현재 코드베이스에서 확인된 기술 부채·버그 위험·보안·성능·확장성·테스트 공백 목록.
각 항목은 실제 파일·라인을 확인한 뒤 작성했다.

---

## Tech Debt

**시드 파이프라인이 deploy.sh와 단절됨 (재현성 최대 리스크):**
- `deploy.sh:52`의 [4/4] 단계는 `inject_ko_names.py` 하나만 재실행한다. `backend/scripts/`에는 Neo4j에 쓰는 스크립트가 22개 있는데(`load_theographic.py`, `load_authored_persons.py`, `load_authored_events.py`, `load_books.py`, `load_person_events.py`, `load_verse_events.py`, `enrich_place_coords.py`, `inject_ko_names.py`, `inject_book_context.py`, `inject_place_context.py`, `inject_person_traits.py` 등) 나머지 21개는 배포에 포함되지 않는다.
- Neo4j 볼륨(`docker-compose.yml:37` `neo4j_data`)이 살아있는 한 재실행 불필요하지만, **볼륨 삭제·신규 서버 프로비저닝·컨테이너 재생성 시 전체 재적재가 필요**하다. 그 완전한 실행 순서는 어디에도 정본화되어 있지 않다.
- `README.md:17–22`는 2개 스크립트만 나열. `CONTEXT.md`에 "authored Person → `load_person_events.py` 순서" 제약 일부 기술, 나머지는 `.forge/done/` 커밋 노트에 분산.
- Impact: 볼륨 손실 시 누락·순서 오류로 `HAS_PARTICIPANT` MATCH 실패, trait/context 누락 상태로 서비스 가동.

**시드 스크립트 실행 순서 암묵적:**
- `load_person_events.py`는 `MATCH (b:Book ...)`, `MATCH (p:Place ...)`로 기존 노드를 참조하므로 `load_books.py`·`load_theographic.py`·`enrich_place_coords.py`·`load_authored_persons.py`가 먼저 실행돼야 관계가 생성된다(`backend/scripts/load_person_events.py`).
- 잘못된 순서로 재시드하면 `MATCH`가 0건을 반환해 관계가 조용히 누락된다(에러 없음).

**대형 프론트엔드 컴포넌트:**
- `frontend/src/SidePanel.jsx` — 705줄. Person/Place/Event/Book/PeopleGroup 5개 노드 타입의 분기 렌더, nodeId별 stale 무효화, 인라인 드릴다운 상태를 여러 `useState`로 한 파일에서 관리. 국소 변경 시 다른 노드 타입 렌더를 깨뜨리기 쉽다.
- `frontend/src/App.jsx` — 395줄. `useStageNavigation.js`·`useNodeSelection.js`로 일부 분리됐지만 상태 머신, fetch orchestration, 레이아웃 분기가 공존.
- `frontend/src/TimelineView.jsx` — 359줄.

**"큐레이션 13인" 주석이 현실과 어긋남 (stale):**
- `backend/app/routes/persons.py:1`(docstring), `backend/app/routes/journey.py:6`(주석)에 "13인"이 고정돼 있으나 `_ERA`는 34개 slug, `data/person_events/`도 34개 json.

---

## Known Bugs

명시적 런타임 버그는 확인되지 않았다. TODO/FIXME/HACK/XXX 마커는 소스 전역 0건. 아래 Fragile Areas의 항목들이 잠재 결함에 해당한다.

---

## Security Considerations

**CORS `allow_origins=["*"]`:**
- `backend/app/main.py:27`. `allow_methods=["GET"]`로 읽기 전용 제한, `allow_credentials=False`. API는 읽기 전용이고 nginx 뒤에서 운영되며 컨테이너 포트는 `127.0.0.1` 바인딩.
- 공개 읽기 API라 즉각 위험은 낮지만, 향후 인증 레이어 추가 시 명시적 오리진 화이트리스트 필요.

**Cypher 인젝션 표면 (현재 방어됨):**
- `backend/app/routes/search.py:14–30`: 사용자값 `q`는 `$q` 파라미터 바인딩, f-string 삽입분은 상수 `SEARCH_LIMIT`만. `backend/app/routes/nodes.py:168–170`: f-string 삽입분은 상수 `NODE_NEIGHBOR_LIMIT`만. 현재 안전. 향후 f-string에 사용자값 직접 삽입 금지.

**시크릿 취급 (현재 양호):**
- `.env` gitignore, `docker-compose.yml:10` `${NEO4J_PASSWORD:?...}`로 필수화, `backend/app/db.py:12` env 누락 시 `RuntimeError`. 하드코딩된 시크릿 값 0건.

---

## Performance Bottlenecks

**8.9MB event_verses JSON 전체 인메모리 상주:**
- `data/event_verses/events.json` 8.9MB가 `backend/app/overlays.py:36–39`의 `lru_cache`로 프로세스당 상주.
- `backend/app/routes/events.py:54` `_compute_events()`는 이 JSON + Neo4j 결과 병합본을 추가로 보관.
- 현재 `backend/Dockerfile:6`에서 uvicorn 단일 워커라 문제 잠재적. gunicorn 또는 `--workers N` 전환 시 워커당 중복 배증.

**`places.py`의 `maxsize=None` 무한 캐시:**
- `backend/app/routes/places.py:18` `@functools.lru_cache(maxsize=None)`. 고유 `place_id` 수만큼 항목 무한 누적. 현재 43개 장소라 허용 범위지만 상한이 없다.

**`_build_id_to_slug()`에 캐시 없음:**
- `backend/app/routes/journey.py:18–30`: `lru_cache` 없이 요청마다 `_ERA` 34개 slug JSON을 순회해 open/parse. `/person/{id}/journey` 호출마다 34개 파일 I/O 반복.

**전역 노드 스캔 검색:**
- `backend/app/routes/search.py:16`: `MATCH (n) WHERE n.nameKo CONTAINS ...` — 인덱스 미사용 전수 스캔. 데이터 규모 확대 시 지연.

---

## Fragile Areas

**`TimelineView.personFilter`는 반드시 `Set`이어야 함 — 타입 계약 미강제:**
- `frontend/src/TimelineView.jsx:101`에서 `personFilter.has(ev.id)`를 직접 호출한다. `Array`를 넘기면 `O.has is not a function` 런타임 크래시.
- 호출부(`App.jsx:330`)는 `App.jsx:45` 주석으로 `Set`임을 명시하나, PropTypes/TypeScript 타입 선언 없음. 테마 투어 와이어링 중 실제로 이 버그가 발생한 전례 있음.
- `personEventIds`는 `useNodeSelection.js:23`에서 `new Set(...)` 생성. `tourEventIds`는 `App.jsx:47`에서 `new Set(...)` 생성. 신규 호출자가 Array를 넘기면 즉시 크래시.

**`_tours_dir()`가 `overlays._resolve` 경로 해석 로직을 복제:**
- `backend/app/routes/tours.py:22–30` `_tours_dir()`은 `DATA_DIR` env 우선 → repo-relative fallback 패턴을 직접 구현.
- `backend/app/overlays.py:11–16` `_resolve()`와 동일한 패턴이나 별도 구현. `DATA_DIR` 처리 방식이 두 곳에 분리되어 향후 경로 해석 규칙 변경 시 한 쪽만 수정되는 드리프트 위험.

**`startDate` 파싱 로직 중복:**
- `"-4003"`, `"-1451-01"`, `"0049-10-01"` 형식의 혼재 연도 문자열 파싱이 두 곳에 독립 구현됨.
- `frontend/src/dates.js:4–12` `parseYear()`: BC 접두 감지 후 `slice(1).split('-')[0]` + 제로패딩 제거, 레이블 반환.
- `backend/app/routes/nodes.py:238–248` `_year()`: 동일 패턴에 `int()` 변환·부호 반전 추가(정렬용 숫자 반환).
- 한쪽만 수정하면 BC/AD 경계·제로패딩 처리가 엇갈릴 수 있다. 테스트 없음.

**`events[0]["participants"][0]`를 인물 대표 ID로 신뢰:**
- `backend/app/routes/persons.py:106`, `backend/app/routes/places.py:34`, `backend/app/routes/journey.py:28`이 슬러그 json 첫 이벤트의 첫 participant를 인물 ID로 사용.
- 방어 코드 없음. 새 `person_events/*.json`에서 `participants[0]`가 사건마다 다르거나 빈 배열이면 `IndexError` 또는 잘못된 인물 매핑.

**침묵하는 예외 처리:**
- `backend/app/main.py:19–20`: 인덱스 생성 실패를 `except Exception`으로 로깅만 하고 계속. 인덱스 없이 기동해 전수 스캔 성능 저하.
- `backend/app/routes/nodes.py:254–257`: traits JSON 파싱 실패 시 `except Exception`으로 빈 배열 반환. 데이터 누락이 UI에서 조용히 숨겨짐.

**프론트 stale 응답 무효화 패턴의 수동 관리:**
- `frontend/src/SidePanel.jsx:47–77`: `cancelled` 플래그 + `state.id`로 stale 판별, `forNodeId` 키로 드릴다운 상태 무효화. 각 effect마다 수동 반복. 신규 비동기 fetch 추가 시 패턴을 빠뜨리면 이전 노드 데이터가 잠깐 노출됨.

---

## Scaling Limits

**단일 인스턴스 스택, 인메모리 캐시 공유 불가:**
- neo4j 1 + api 1 + nginx 1 컨테이너. API가 다수 `lru_cache`에 의존하므로 워커/컨테이너 다중화 시 캐시 인스턴스별 중복·불일치. 무효화 수단이 앱 재시작뿐.
- 데이터가 정적이라 재시작 무효화로 충분한 규모까지는 안전.

---

## Dependencies at Risk

**Theographic 데이터를 GitHub `master` HEAD에서 미고정 fetch:**
- `backend/scripts/load_theographic.py:14–18`, `backend/scripts/load_books.py:14–15`, `backend/scripts/generate_event_verses.py:28–29` 등 여러 스크립트가 `https://raw.githubusercontent.com/robertrouse/theographic-bible-metadata/master/json/*.json`을 직접 다운로드. 커밋 SHA 고정·로컬 스냅샷 없음.
- 업스트림 스키마 변경 시 재시드 결과가 달라지거나 `KeyError`로 중단. 네트워크 불가 시 재시드 실패.

**Neo4j 이미지 메이저 버전만 고정 (`neo4j:5`):**
- `docker-compose.yml:3`. 마이너·패치가 자동 적용되어 드라이버 호환성 문제 가능. `neo4j:5.x.y` 형태로 고정 권장.

**프론트 React 19 + 캐럿 범위 의존성:**
- `frontend/package.json`: `react@^19.2.6`, `maplibre-gl@^5.24.0`, `lucide-react@^1.17.0`. `maplibre-gl`은 지도 렌더 핵심이라 메이저 변경 시 `mapLayers.js`/`mapGeo.js`/`mapRingController.js` 영향. lockfile 유지로 재현성 확보 중.

---

## Missing Critical Features

**시드 전체 재현 자동화 부재:**
- 전체 그래프를 처음부터 재구성하는 단일 진입점 없음. README는 2단계, `deploy.sh`는 1스크립트만 실행. 볼륨 손실 시 신뢰할 수 있는 복구 경로·신규 환경 부트스트랩·데이터 커밋의 자동 반영 모두 차단됨.

**nginx 속도 제한 없음:**
- `nginx/nginx.conf`에 `limit_req_zone`/`limit_req` 미설정. 공개 API 과도 스크레이핑 시 uvicorn 단일 프로세스 포화.

---

## Test Coverage Gaps

- `*.test.*`/`*.spec.*` 파일 0건, pytest/vitest/jest 설정 없음. `frontend/package.json` scripts에 test 없음(dev/build/lint/preview만).
- 특히 위험 높은 미검증 지점:
  - `frontend/src/dates.js:4–12` `parseYear` — BC/AD 혼재 연도 파싱 순수 함수. 테스트 비용 낮고 회귀 위험 큼.
  - `backend/app/routes/nodes.py:238–248` `_year` — 동일 로직 Python판. 테스트 없음.
  - `backend/app/overlays.py:11–16` `_resolve` — 환경변수 우선순위 검증 불가.
  - `backend/app/routes/journey.py` — 여정 stop 생성·seq 부여 로직.
  - `backend/app/routes/persons.py`/`places.py` — slug↔person_id 매핑 계약.
  - `backend/app/routes/events.py` — approx book 인덱스 머지.
- UI 검증은 Playwright 수동 실행(로컬)에만 의존. CI 미연동.
- startDate 파싱 회귀, slug 매핑 드리프트, 시드 순서 오류로 인한 관계 누락 모두 자동으로 감지되지 않는다.
