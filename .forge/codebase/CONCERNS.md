---
last_mapped_commit: 815433397ff74c133b2de5d1cafe1c8764b5303c
mapped: 2026-07-04
---

# Codebase Concerns

**Analysis Date:** 2026-07-04

## Tech Debt

**시드 파이프라인이 deploy.sh와 단절됨 (재현성 최대 리스크):**
- Issue: `deploy.sh`(`/Users/calmonion/Project/BibleMap/deploy.sh`)의 [4/4] 단계는 `inject_ko_names.py` 하나만 재실행한다. 그러나 Neo4j에 쓰는 스크립트는 총 12개다 — `load_theographic.py`, `load_books.py`, `load_person_events.py`, `load_authored_events.py`, `load_authored_persons.py`, `load_verse_events.py`, `enrich_place_coords.py`, `inject_ko_names.py`, `inject_book_context.py`, `inject_place_context.py`, `inject_person_traits.py`, `generate_book_events.py`. 나머지 11개는 수동 실행이며 배포에 포함되지 않는다.
- Files: `backend/scripts/load_theographic.py`, `backend/scripts/load_books.py`, `backend/scripts/load_person_events.py`, `backend/scripts/load_authored_events.py`, `backend/scripts/enrich_place_coords.py`, `backend/scripts/inject_place_context.py`, `backend/scripts/inject_book_context.py`, `backend/scripts/inject_person_traits.py`
- Impact: 새 인물/사건/장소 데이터를 커밋해도 `data/person_events/*.json` 등이 배포 자동으로 그래프에 반영되지 않는다. Neo4j 볼륨(`neo4j_data`)이 유지되는 한 과거 상태가 조용히 남고, 볼륨을 날리면 전체 재시드를 수동으로 재현해야 한다. 실제 재현 순서가 코드/문서 어디에도 정본화돼 있지 않다.
- Fix approach: 전체 시드를 순서대로 실행하는 단일 오케스트레이션 스크립트(`seed_all.py` 또는 make 타깃)를 만들고, 어떤 스크립트가 배포마다 재실행돼야 하는지(멱등) 명시. `deploy.sh`가 그 스크립트를 호출하도록 연결.

**시드 스크립트 실행 순서가 암묵적 (문서화 부재):**
- Issue: `README.md`는 시드로 `load_theographic.py` + `inject_ko_names.py` 2개만 안내하지만, `backend/scripts/`에는 Neo4j 적재 스크립트 12개가 있고 상호 선후 의존이 있다. 예: `load_person_events.py`는 `MATCH (b:Book ...)`, `MATCH (p:Place ...)`로 기존 노드를 참조하므로 `load_books.py`·`load_theographic.py`·`enrich_place_coords.py`가 먼저 실행돼 있어야 관계가 생성된다. `journey.py`/`persons.py`/`places.py`는 `person_events/*.json`의 `occursAt` place_id가 Place 노드로 존재한다고 가정한다.
- Files: `README.md`(2단계 서술), `backend/scripts/load_person_events.py:53-77`, `backend/scripts/load_books.py:158-166`
- Impact: 잘못된 순서로 재시드하면 `MATCH`가 매칭에 실패해 관계가 조용히 누락되고(에러 없이 0건), 여정/이웃 조회가 부분적으로 비게 된다.
- Fix approach: 시드 스크립트의 선후 의존을 명시한 순서표를 README 또는 오케스트레이션 스크립트에 정본화.

**대형 프론트 컴포넌트 (수정 난이도 상승):**
- Issue: 단일 파일에 상태·effect·렌더가 몰려 있다.
- Files: `frontend/src/SidePanel.jsx`(650줄), `frontend/src/App.jsx`(391줄), `frontend/src/TimelineView.jsx`(359줄), `frontend/src/BibleOverviewView.jsx`(309줄), `frontend/src/PersonHub.jsx`(304줄), `frontend/src/mapLayers.js`(451줄)
- Impact: `SidePanel.jsx`는 Person/Place/Event/Book/PeopleGroup 5개 노드 타입의 분기 렌더를 모두 담고, `nodeId`별 stale 응답 무효화·인라인 드릴다운 상태를 여러 `useState`로 병렬 관리한다. 국소 변경 시 다른 노드 타입 렌더를 깨뜨리기 쉽다.
- Fix approach: 노드 타입별 서브컴포넌트 분리 또는 상태를 커스텀 훅으로 추출. 단, 회귀 테스트가 전무하므로(아래 참조) 리팩터 전 스냅샷/동작 검증 수단부터 확보.

**"큐레이션 13인" 주석이 34인 현실과 어긋남 (stale 문서):**
- Issue: 여러 파일 주석·docstring이 "큐레이션 13인"으로 고정돼 있으나 `_ERA` 딕셔너리는 34개 slug를 담고 `data/person_events/`에도 34개 json이 있다.
- Files: `backend/app/routes/persons.py:1`(docstring), `backend/app/routes/journey.py:6,77`(주석 "큐레이션 13인")
- Impact: 문서-코드 드리프트. 신규 인물 추가 시 어느 게 진짜 개수인지 오해 유발.
- Fix approach: 개수 하드코딩 문구 제거하고 "`_ERA`에 등록된 인물" 식으로 서술.

## Known Bugs

명시적으로 확인된 런타임 버그는 발견되지 않았다. TODO/FIXME/HACK/XXX 마커도 소스 전역에 0건이다(`backend/`, `frontend/src/`). 아래 "Fragile Areas"의 항목들이 잠재 결함에 해당한다.

## Security Considerations

**CORS 전면 허용:**
- Risk: 모든 오리진에서 API 호출 가능.
- Files: `backend/app/main.py:25-31`(`allow_origins=["*"]`, `allow_methods=["GET"]`)
- Current mitigation: 메서드를 GET으로만 제한, `allow_credentials=False`. API는 읽기 전용이고 nginx 프록시(`/api → api:8000`) 뒤에 있으며 컨테이너 포트는 `127.0.0.1`로만 바인딩(`docker-compose.yml`).
- Recommendations: 읽기 전용·공개 데이터라 위험은 낮지만, 배포 도메인이 확정되면 오리진 화이트리스트로 좁히는 것이 안전.

**시크릿 취급 (현재 양호, 유지 필요):**
- Risk: Neo4j 비밀번호 노출.
- Files: `.env`(gitignore됨 — `git ls-files`에 미추적 확인), `.env.example`(플레이스홀더만), `docker-compose.yml`(`${NEO4J_PASSWORD:?...}`로 필수화, 하드코딩 없음), `deploy.sh:33-35`(`.env` 소싱)
- Current mitigation: `.gitignore`에 `.env` 등재, 코드/스크립트는 `os.environ`에서만 읽고 없으면 `RuntimeError`. 하드코딩된 시크릿 값은 발견되지 않았다.
- Recommendations: 현행 유지. 로그(`deploy.sh` 로그 경로 `~/Library/Logs/com.biblemap.deploy.log`)에 비번이 흘러가지 않는지 스크립트 추가 시 주의.

**Cypher 인젝션 표면 (현재 파라미터 바인딩으로 방어됨):**
- Risk: 사용자 입력이 Cypher에 삽입될 여지.
- Files: `backend/app/routes/search.py:14-30`(f-string으로 쿼리를 조립하나 사용자값 `q`는 `$q` 파라미터 바인딩, f-string 삽입분은 상수 `SEARCH_LIMIT`뿐), `backend/app/routes/nodes.py:168-170`(f-string 삽입분은 상수 `NODE_NEIGHBOR_LIMIT`)
- Current mitigation: 사용자 입력은 전부 `$id`/`$q` 등 파라미터로 전달돼 인젝션 위험 없음.
- Recommendations: 이 패턴 유지. 향후 f-string에 사용자값을 직접 넣지 말 것.

## Performance Bottlenecks

**9.3MB event_verses JSON 전체를 메모리 상주:**
- Problem: 가장 큰 데이터 파일을 `functools.lru_cache`로 프로세스 메모리에 통째 로드해 상주시킨다.
- Files: `data/event_verses/events.json`(9,377,620 bytes ≈ 9.3MB), `backend/app/overlays.py:36-39`(`event_verses()` lru_cache), `backend/app/routes/events.py:114`(사용처)
- Cause: 단일 프로세스 인메모리 캐시. 앱 재시작 전까지 유지되며 워커/프로세스 수만큼 중복 상주한다.
- Improvement path: 단일 인스턴스 규모에서는 허용 범위지만, uvicorn 워커를 늘리면 워커당 9.3MB가 곱해진다. 필요 시 사건 ID별 지연 조회 또는 Neo4j 이관 검토.

**여정/장소 엔드포인트가 요청마다 34개 JSON을 순회:**
- Problem: `journey.py`의 `_build_id_to_slug()`와 `places.py`의 `_place_to_persons()`는 `_ERA` 34개 slug의 json을 파일에서 읽어 순회한다.
- Files: `backend/app/routes/journey.py:18-30`(`_build_id_to_slug` — lru_cache 없음, 요청마다 34개 파일 open/parse), `backend/app/routes/places.py:18-50`(`_place_to_persons` — place_id별 lru_cache 있음)
- Cause: `journey.py:_build_id_to_slug`에 캐시가 없어 `/person/{id}/journey` 호출마다 34개 파일을 다시 읽는다(`places.py`는 캐시됨 — 비대칭).
- Improvement path: `_build_id_to_slug`에 `functools.lru_cache(maxsize=1)` 추가로 파일 I/O 반복 제거. slug 수가 늘수록 격차 확대.

**여러 조회 엔드포인트가 무제한 스캔:**
- Problem: 라벨/인덱스 없는 전역 MATCH.
- Files: `backend/app/routes/search.py:16`(`MATCH (n) WHERE n.nameKo CONTAINS ...` — 전체 노드 스캔, 인덱스 미사용), `backend/app/routes/books.py:14`(`MATCH (b:Book) RETURN b` — 전권 반환)
- Cause: `CONTAINS`는 인덱스를 타지 않아 노드 전수 스캔. 데이터 규모가 커지면 검색 지연.
- Improvement path: 데이터 규모 확대 시 풀텍스트 인덱스(Neo4j fulltext) 도입 검토.

## Fragile Areas

**`events[0]["participants"][0]`를 인물 대표 ID로 신뢰:**
- Files: `backend/app/routes/persons.py:106`, `backend/app/routes/places.py:34`, `backend/app/routes/journey.py:28`
- Why fragile: 슬러그 json 안 모든 이벤트의 첫 participant가 동일인이라는 암묵 계약에 의존한다. 오늘 34개 파일 전수 검증상 계약은 성립하나(모든 파일에서 `participants[0]`가 상수), 방어 코드가 없다. 새 인물 json에서 `participants[0]`가 사건마다 다르거나 빈 배열이면 `IndexError` 또는 잘못된 인물 매핑이 발생한다.
- Safe modification: 새 `person_events/*.json` 추가 시 "모든 이벤트의 `participants[0]`가 동일 인물"을 반드시 지킬 것. 이상적으로는 슬러그 파일에 명시적 `personId` 필드를 두고 그걸 읽도록 변경.
- Test coverage: 없음.

**혼재 startDate 문자열 파싱:**
- Files: `frontend/src/dates.js:4-12`(`parseYear`), `backend/app/routes/nodes.py:236-249`(`_year` 로컬 함수), `data/*/events.json`의 `startDate`(`"-4003"`, `"-1451-01"`, `"0049-10-01"`, `"30"` 등 형식 혼재)
- Why fragile: BC 음수 접두·연월·제로패딩이 공존해 숫자 강제변환·사전순 정렬이 함정(BC 연도 역전). `nodes.py`와 `dates.js`에 파싱 로직이 중복 존재해 한쪽만 수정하면 드리프트한다. `dates.js` 주석이 `.forge/CONTEXT.md`를 참조하도록 경고해둔 상태.
- Safe modification: 두 파서(`dates.js:parseYear`, `nodes.py:_year`)를 함께 검토. 새 startDate 형식이 등장하면 양쪽 모두 반영.
- Test coverage: 없음.

**침묵하는 예외 처리:**
- Files: `backend/app/main.py:19-20`(인덱스 생성 실패를 `except Exception`으로 로깅만 하고 계속), `backend/app/routes/nodes.py:255-257`(traits JSON 파싱 실패 시 `except Exception`으로 `[]`)
- Why fragile: 인덱스 생성 실패 시 앱은 뜨지만 검색/조회가 전수 스캔으로 느려질 수 있고, 로그를 안 보면 인지 못 한다. traits 파싱 실패는 조용히 빈 배열이 돼 데이터 누락이 UI에서 드러나지 않는다.
- Safe modification: 인덱스는 `load_theographic.py`/`load_books.py`에서도 생성되므로 이중 안전망이 있으나, 운영 시 로그 모니터링 필요.
- Test coverage: 없음.

**프론트 stale 응답 무효화 패턴의 손수 관리:**
- Files: `frontend/src/SidePanel.jsx:47-77`(`cancelled` 플래그 + `state.id`로 stale 판별), `frontend/src/SidePanel.jsx:54-61`(`forNodeId` 키로 드릴다운 상태 무효화)
- Why fragile: 노드 전환 시 이전 요청 응답을 버리는 로직이 각 effect마다 수동으로 반복된다. 새 비동기 데이터를 추가할 때 동일 패턴을 빠뜨리면 이전 노드 데이터가 잠깐 노출된다.
- Safe modification: `frontend/src/api.js:apiGet`이 `signal`(AbortController)을 받으므로 신규 fetch는 abort 시그널 연결 권장.
- Test coverage: 없음.

## Scaling Limits

**단일 인스턴스 self-hosted 스택:**
- Current capacity: neo4j 1 + api 1 + nginx 1 컨테이너, 포트 `8080`(nginx)만 외부 노출, Neo4j/API는 `127.0.0.1` 바인딩(`docker-compose.yml`).
- Limit: API가 다수 인메모리 lru_cache(events, event_verses 9.3MB, book maps)에 의존하므로 수평 확장(워커/컨테이너 다중화) 시 캐시가 인스턴스별로 중복·불일치. 캐시 무효화 수단이 앱 재시작뿐이다.
- Scaling path: 데이터가 정적이라 재시작 무효화로 충분한 규모까지는 안전. 확장 필요 시 공유 캐시(Redis) 또는 Neo4j 직조회로 이관.

## Dependencies at Risk

**Theographic 데이터를 GitHub master에서 실시간 fetch (버전 미고정):**
- Risk: `load_theographic.py`가 외부 레포의 `master` 브랜치 raw URL 4개에서 직접 다운로드한다. 커밋 핀 없음.
- Files: `backend/scripts/load_theographic.py:13-18`(`.../theographic-bible-metadata/master/json/*.json`)
- Impact: 업스트림이 스키마를 바꾸거나(`fields.displayTitle`, `fields.status`, `fields.participants` 등 의존) 레코드를 삭제하면 재시드 시 조용히 다른 그래프가 만들어진다. 재현 불가능한 시드. 네트워크/레포 접근 불가 시 재시드 실패.
- Migration plan: 특정 커밋 SHA로 URL 핀 고정, 또는 원본 JSON을 `data/`에 커밋(현재 파생 데이터만 커밋되고 원천 4개 파일은 미커밋)해 재현성 확보.

**프론트 React 19 + 소수 의존성:**
- Risk: `react@^19.2.6`, `maplibre-gl@^5.24.0`, `lucide-react@^1.17.0`(`frontend/package.json`). 캐럿 범위로 마이너 업데이트 자동 허용.
- Impact: 낮음 — 의존성 수가 적다. `maplibre-gl`은 지도 렌더 핵심이라 메이저 변경 시 `mapLayers.js`/`mapGeo.js`/`mapRingController.js` 영향.
- Migration plan: lockfile(`frontend/package-lock.json`) 유지로 재현성 확보. 메이저 업그레이드는 지도 3파일 회귀 검증 후.

## Missing Critical Features

**시드 재현 자동화 부재:**
- Problem: 위 Tech Debt에서 서술한 대로 전체 그래프를 처음부터 재구성하는 단일 진입점이 없다. README는 2단계만, `deploy.sh`는 1스크립트만 실행.
- Blocks: Neo4j 볼륨 손실 시 신뢰할 수 있는 복구, 신규 환경 부트스트랩, 데이터 커밋의 자동 반영.

## Test Coverage Gaps

**테스트가 전무:**
- What's not tested: 프로젝트 전체. `*.test.*`/`*.spec.*` 파일 0건, pytest/vitest/jest 설정 없음, `frontend/package.json` scripts에 test 없음(dev/build/lint/preview만).
- Files: 전 코드베이스 — 특히 리스크 높은 미검증 지점: `frontend/src/dates.js`(연대 파싱), `backend/app/routes/nodes.py`(`_year` 정렬·노드 조회 분기), `backend/app/routes/journey.py`(여정 stop 생성·seq 부여), `backend/app/routes/persons.py`/`places.py`(slug↔person_id 매핑), `backend/app/routes/events.py`(approx book 머지)
- Risk: startDate 파싱 회귀, 슬러그↔인물 매핑 드리프트, 시드 순서 오류로 인한 관계 누락이 모두 조용히 통과한다. UI 검증은 Playwright 수동 실행(프로젝트 메모리 참조)에 의존.
- Priority: High — 특히 `dates.js`/`nodes.py:_year` 연대 로직과 slug 매핑 계약은 순수 함수라 단위 테스트 비용이 낮고 회귀 위험이 크다.

---

*Concerns audit: 2026-07-04*
