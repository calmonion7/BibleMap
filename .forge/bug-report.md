# BibleMap 버그 리포트 — 1차 사이클 (task#150)

작성: 2026-07-10 · 대상: 전체 런타임 표면(backend/app 13파일 + frontend/src 23파일) + 데이터 계약 기계검증 · HEAD `a7753bc`
방법: 6렌즈 finder 병렬 발굴(원시 15건) → dedup(15건) → **finding별 독립 적대적 검증**(코드 재추적 + 라이브 API/Neo4j/데이터 실측) → confirmed 12 · refuted 3 · needs-confirmation 0
규칙: 검증 통과분 전건 수록(캡 없음). 이 리포트는 발견·검증·보고만 — 코드 수정은 finding별 후속 태스크.

## 요약

| # | 심각도 | 렌즈 | 위치 | 증상 |
|---|--------|------|------|------|
| 1 | HIGH | 백엔드 견고성 | `backend/app/overlays.py:15` | 오버레이 데이터 파일이 두 후보 경로(DATA_DIR, _REPO_DATA_DIR) 어디에도 없을 때 _resolve/_resolve_dir가 로그 한 줄 없이 … |
| 2 | HIGH | 프론트 견고성 | `backend/scripts/load_books.py:68` | Book.startYear/endYear(Neo4j에 영구 적재되어 TimelineView의 책 범위 필터·배너에 쓰이는 값)가 연-월/연-월-일 정밀도의 … |
| 3 | MEDIUM | 백엔드 정합성 | `backend/app/routes/events.py:118` | GET /event/{id}/verses가 자신의 docstring이 약속한 "정경순(canonical order)"을 지키지 않고 오버레이 JSON에 저장된 … |
| 4 | MEDIUM | 백엔드 정합성 | `backend/app/routes/nodes.py:226` | Book 노드의 "주요 사건"(topEvents)이 CONTAINS_BOOK의 '해당 권에서 실제 발생'과 '해당 권 내 설교/족보에서 회고 인용'을 구분하지 … |
| 5 | MEDIUM | 보안/성능 | `backend/app/routes/persons.py:145` | `_build_connections`가 `@functools.lru_cache(maxsize=None)`로 사용자 제어 `node_id`(URL 경로 … |
| 6 | MEDIUM | 백엔드 정합성 | `backend/app/routes/places.py:33` | `_place_to_persons`가 이벤트의 `occursAt` 배열 전체(모든 인덱스)를 검사해 '이 장소를 지난 인물'로 포함시키지만, … |
| 7 | MEDIUM | 백엔드 견고성 | `backend/app/routes/places.py:21` | /place/{place_id}/curated-persons는 place_id를 검증 없이 그대로 lru_cache(maxsize=None) 키로 사용한다. … |
| 8 | MEDIUM | 백엔드 견고성 | `backend/app/routes/tours.py:70` | _build_event_index()는 _ERA 삽입 순서대로(정렬 없이) 35개 person_events 파일을 순회하며 eventId를 키로 dict에 … |
| 9 | MEDIUM | 데이터 계약 | `data/person_relations/relations.json:23822` | 욥↔엘리후 관계(relations[169], type="친구")의 두 번째 국면 approxYear가 -1897.5로 비정수(float)다. 전체 627국면 중 … |
| 10 | MEDIUM | 프론트 정합성 | `frontend/src/useNodeSelection.js:33` | 인물 탐험 중 지도의 장소(Place)/사건 등 인물이 아닌 노드를 한 번이라도 클릭하면, 그 순간부터 타임라인 뷰의 인물 필터가 조용히 풀려 전체 비필터 … |
| 11 | MEDIUM | 프론트 정합성 | `frontend/src/useStageNavigation.js:88` | PersonHub와 useStageNavigation이 `/persons/curated`를 각자 독립적으로 두 번 호출하는데, 이 둘의 완료 시점이 … |
| 12 | MEDIUM | 프론트 정합성 | `frontend/src/useStageNavigation.js:56` | 딥링크 복원 effect가 `curatedIds` 로드 완료를 기다린 뒤에만 동작하는데, 이 게이트가 인물 slug 해석이 필요 없는 … |

---

## 1. [HIGH] `backend/app/overlays.py:15` — 오버레이 데이터 파일이 두 후보 경로(DATA_DIR, _REPO_DATA_DIR) 어디에도 없을 때 _resolve/_resolve_dir가 로그 한 줄 없이 None을 반환하고, 이를 소비하는 6개 이상의 라우트가 그대로 '정상' 200 빈 …

- **렌즈**: 백엔드 견고성 · 적대적 검증 **CONFIRMED**
- **증상**: 오버레이 데이터 파일이 두 후보 경로(DATA_DIR, _REPO_DATA_DIR) 어디에도 없을 때 _resolve/_resolve_dir가 로그 한 줄 없이 None을 반환하고, 이를 소비하는 6개 이상의 라우트가 그대로 '정상' 200 빈 배열/빈 객체 응답으로 위장한다. 같은 파일의 JSON 파싱 실패(json.JSONDecodeError)는 logger.warning으로 남기면서(overlays.py:37-39), 더 심각한 '파일 자체가 없음' 케이스는 완전 무음이라 로깅 대칭이 깨져 있다.
- **근거**: overlays.py:14-19 `def _resolve(subpath): for base in (os.environ.get("DATA_DIR", "/app/data"), _REPO_DATA_DIR): ... if os.path.isfile(path): return path\n    return None` — return None 분기에 logger 호출 없음. 동일 파일 _load()(30-39)는 path is None이면 `return {}`도 무음. 이 함수를 그대로 호출하는 소비처: persons.py:104-107 `path = _resolve(f"person_events/{slug}.json"); if path is None: continue`(로그 없음), journey.py:21-24, places.py:25-28, tours.py:59-62(_build_event_index) 및 tours.py _tours_dir()→_list_tours()의 `if d is None: return []`도 동일 패턴.
- **재현**: DATA_DIR을 오설정(빈 문자열·오탈자 경로)하거나 docker-compose의 `./data:/app/data` 볼륨이 비어있거나 마운트 실패한 채로 컨테이너가 뜨면: /persons/curated→[], /tours→[], /person/{id}/journey→{stops:[]}, /event/{id}/verses→{books:[]}, /place/{id}/curated-persons→{persons:[]}, /events의 책 연결(book_events_raw 경유)도 조용히 빈 값. 기동 로그에는 'Neo4j 인덱스 준비 완료'만 찍히고 이상 신호가 전혀 없어, 운영자가 전체 오버레이 데이터 유실을 로그만으로는 절대 알아챌 수 없다.
- **검증 요지**: 코드를 전부 추적하고 컨테이너 환경에서 실측까지 했다.

1) overlays.py:14-19 `_resolve`/22-27 `_resolve_dir`는 두 후보 경로 모두 실패 시 `return None`, 로그 호출 없음. `_load`(30-39)도 `path is None`이면 `return {}` 무음 — 반면 같은 함수의 `json.JSONDecodeError`만 `logger.warning`(37-39). 로깅 비대칭은 코드 그대로 존재.

2) 이 경로가 "도달 불가"라는 반박은 성립하지 않는다. `backend/Dockerfile`을 확인하니 `COPY app/ ./app/`만 수행 — 레포 전체가 아니라 `app/` 디렉터리만 이미지에 들어간다. `_REPO_DATA_DIR = dirname(dirname(dirname(__file__)))`는 컨테이너 기준 `/app/app/overlays.py` → `/`(루트), 즉 컨테이너 안에는 `_REPO_DATA_DIR`(`/data`)가 애초에 존재하지 않는다. 따라서 프로덕션에서 유일한 실경로는 `docker-compose.yml`의 `./data:/app/data` …
- **제안 수정방향**: _resolve/_resolve_dir가 두 base 모두에서 못 찾았을 때 logger.warning(subpath, 시도한 두 경로)을 남기도록 한다. 최소한 _load()의 path is None 분기에도 JSONDecodeError 분기와 동일하게 로그를 추가.

## 2. [HIGH] `backend/scripts/load_books.py:68` — Book.startYear/endYear(Neo4j에 영구 적재되어 TimelineView의 책 범위 필터·배너에 쓰이는 값)가 연-월/연-월-일 정밀도의 startDate를 만나면 그 사건을 조용히 집계에서 빠뜨려 잘못된(너무 좁은) 범위를 …

- **렌즈**: 프론트 견고성 · 적대적 검증 **CONFIRMED**
- **증상**: Book.startYear/endYear(Neo4j에 영구 적재되어 TimelineView의 책 범위 필터·배너에 쓰이는 값)가 연-월/연-월-일 정밀도의 startDate를 만나면 그 사건을 조용히 집계에서 빠뜨려 잘못된(너무 좁은) 범위를 저장한다.
- **근거**: load_books.py:66-72
```python
start_raw = e["fields"].get("startDate", "")
try:
    year = int(str(start_raw).replace("BC", "").strip())
    if "BC" in str(start_raw):
        year = -year
except (ValueError, TypeError):
    continue
```
이 스크립트는 startDate가 텍스트 'BC'를 포함한다고 가정하지만, 이 데이터셋의 실제 형식은 부호(-) 접두 + 선택적 '-월[-일]' 조각이다(BC 텍스트는 존재하지 않음 — `frontend/src/dates.js:1-2`, `backend/app/routes/nodes.py:240-241`, `.forge/CONTEXT.md:43` 모두 동일하게 '-1451-01', '0049-10-01' 형식을 명시). `int("-1451-01")`은 하이픈이 두 개라 `ValueError`를 던지고 `except`가 그 사건 전체를 `continue`로 건너뛴다 — 단순 연도('-4003','30')만 우연히(파이썬 int()가 선행 부호를 직접 처리하므로) 통과한다. 이 '-1451-01' 값은 실제 이 프로젝트 히스토리에서 반복 인용된 …
- **재현**: 재시드(`backend/scripts/load_books.py` 재실행, 예: Neo4j 볼륨 손실 후 복구나 정기 재시드) 시, 어떤 책의 연대상 최초/최후 사건의 startDate가 '-YYYY-MM' 또는 '0YYY-MM-DD' 형식이면(이 데이터셋에 실제 존재가 문서로 확인됨) 그 사건이 min/max 집계에서 빠져 startYear 또는 endYear가 실제보다 좁게(더 늦게 시작하거나 더 일찍 끝나는 값으로) 저장된다. 결과: TimelineView에서 그 책을 선택했을 때 배너의 연대 범위 표기가 틀리고, 실제로는 그 책 범위 안에 있는 사건이 `inFilter()`에 의해 부당하게 제외된다.
- **검증 요지**: Read backend/scripts/load_books.py:66-72 — the parser does `int(str(start_raw).replace("BC","").strip())`, i.e. it only strips a literal "BC" substring and never splits on '-' before calling int(). Any startDate with month/day precision (e.g. "0030-05-01") fails int() and hits `except (ValueError, TypeError): continue`, silently dropping that event from the min/max aggregation for whatever Book its verses map to. Confirmed the dataset's real format via frontend/src/dates.js:1-2, backend/app/routes/nodes.py:240-241 ("_year" helper), and .forge/CONTEXT.md:41-43 — sign-prefixed years with …
- **제안 수정방향**: load_books.py의 파싱을 dates.js `parseYear`/nodes.py `_year`와 동일한 규칙(부호 분리 후 첫 '-' 이전 파트만 정수화)으로 통일 — 예: `_year()` 헬퍼를 세 곳이 import/이식해 쓰거나 최소한 동일 로직으로 재작성.

## 3. [MEDIUM] `backend/app/routes/events.py:118` — GET /event/{id}/verses가 자신의 docstring이 약속한 "정경순(canonical order)"을 지키지 않고 오버레이 JSON에 저장된 순서를 그대로 반환 — 특정 사건은 신약 후반 책(눅/막)이 전반 책(마태)보다 먼저 …

- **렌즈**: 백엔드 정합성 · 적대적 검증 **CONFIRMED**
- **증상**: GET /event/{id}/verses가 자신의 docstring이 약속한 "정경순(canonical order)"을 지키지 않고 오버레이 JSON에 저장된 순서를 그대로 반환 — 특정 사건은 신약 후반 책(눅/막)이 전반 책(마태)보다 먼저 나온다.
- **근거**: events.py:112-119: `"""사건의 근거 구절을 권별로 그룹·정경순으로 반환(드릴다운용)."""` 이라 문서화했지만, 실제 로직은 `for b in entry.get("books", []): enriched_books.append({**b, "bookNameKo": ...})` 뿐 — `bookOrder` 기준 정렬 코드가 전혀 없다. 반면 형제 엔드포인트들은 명시적으로 정렬한다: `/events`(_compute_events, events.py:62 `WITH e, b ORDER BY b.bookOrder ASC`)와 nodes.py Book 분기(:252 Python 정렬)는 모두 canonical order를 강제한다. `data/event_verses/events.json`을 직접 검사하면 4건이 실제로 역순 저장돼 있다: `authored-peter-call-galilee`→[42,40], `authored-peter-apostle-named`→[42,41], `authored-peter-denial`→[42,40], `authored-john-call-zebedee`→[41,40] (bookOrder 40=Matthew, 41=Mark, 42=Luke).
- **재현**: `curl http://localhost:8080/api/event/authored-peter-call-galilee/verses` 실행 → 응답 `books[0].bookOrder == 42`(누가복음), `books[1].bookOrder == 40`(마태복음) — 마태복음보다 누가복음이 먼저 나옴. 프론트 SidePanel 드릴다운에서 사용자는 이 사건의 근거 구절을 성경 순서 역순(눅→마)으로 보게 된다. 실제 API 호출로 직접 확인함.
- **검증 요지**: 코드·데이터 실측으로 반박 실패, finding 확정(confirmed).

1) events.py:110-123 `get_event_verses`를 직접 읽음 — docstring(112: \"정경순으로 반환\")과 달리 로직은 `for b in entry.get(\"books\", []): enriched_books.append({**b, \"bookNameKo\": ...})` 뿐, bookOrder 정렬 코드 전무. 같은 파일의 형제 함수 `_load_approx_book_index`(:48 `event_to_books[eid].sort(key=lambda b: b[\"bookOrder\"])`)와 `_compute_events`의 Cypher(:62 `ORDER BY b.bookOrder ASC`)는 명시적으로 정렬하는데 이 엔드포인트만 빠져있음을 확인.

2) `overlays.event_verses()` → `overlays._load()`(json.load 그대로 반환, 정렬 없음) 경로도 확인 — 정렬 보정 지점이 파이프라인 어디에도 없음.

3) `data/event_verses/events.json`을 python3로 직접 파싱해 전수 …
- **제안 수정방향**: `enriched_books`를 반환 전에 `enriched_books.sort(key=lambda b: b["bookOrder"])`로 정렬 — 업스트림 JSON의 정렬 상태에 의존하지 않도록 라우트에서 방어적으로 canonical order를 강제.

## 4. [MEDIUM] `backend/app/routes/nodes.py:226` — Book 노드의 "주요 사건"(topEvents)이 CONTAINS_BOOK의 '해당 권에서 실제 발생'과 '해당 권 내 설교/족보에서 회고 인용'을 구분하지 않고, 오름차순 연도 + 상위 10개 절단(top_events[:10])만 적용해 …

- **렌즈**: 백엔드 정합성 · 적대적 검증 **CONFIRMED**
- **증상**: Book 노드의 "주요 사건"(topEvents)이 CONTAINS_BOOK의 '해당 권에서 실제 발생'과 '해당 권 내 설교/족보에서 회고 인용'을 구분하지 않고, 오름차순 연도 + 상위 10개 절단(top_events[:10])만 적용해 정렬한다. 그 결과 신약 책(사도행전·누가복음)의 '주요 사건'이 스데반의 설교나 족보가 인용한 태고사 사건들로 도배되고 정작 그 책의 실제 핵심 사건은 전부 잘려나간다.
- **근거**: nodes.py:226 `MATCH (b:Book {theographic_id: $id})-[:CONTAINS_BOOK]->(e:Event)` 는 '이 책에서 발생'과 '이 책이 인용/회고'를 구분 없이 모두 가져온다. Neo4j 직접 조회로 확인: `authored-abraham-call-ur`(startDate=-2091, 창세기 사건)가 Genesis뿐 아니라 Acts에도 CONTAINS_BOOK로 연결돼 있음(스데반의 설교, 행 7장). nodes.py:252-253의 정렬 `top_events.sort(key=lambda ev: (_year(...) is None, _year(...) or 0)); top_events = top_events[:10]`은 순수 연도 오름차순 + 하드 절단이라, 이 아웃라이어가 항상 1위를 차지하고 나머지는 동일 연도(0030) 이벤트가 Cypher 반환 순서(임의)로 채워진다.
- **재현**: `curl http://localhost:8080/api/node/recF09FMjRr0gzjQk`(사도행전, 111개 사건) → topEvents[0]이 '-2091 God calls Abraham in Ur of the Chaldeans'(창세기 사건), 나머지 9개가 모두 '0030'년 사건뿐 — 바울의 회심(AD 34)·선교여행(AD 46-57)·재판·난파 등 실제 사도행전 핵심 사건은 하나도 없음. `curl .../recclIex2hH0wdTST`(누가복음, 99개 사건) → topEvents가 '-3873 Birth of Seth', '-3678 Birth of Cainan'(눅 3장 예수 족보가 인용한 창세기 인물) 등으로 시작 — 실제 누가복음 내러티브(예수의 사역·비유·부활 등)는 전무. 둘 다 실제 API 호출로 확인함.
- **검증 요지**: nodes.py:226 및 252-253을 직접 읽고, 실행 중인 biblemap-neo4j-1(bolt://localhost:7687)에 대해 라우트와 동일한 Cypher를 그대로 재현해 실측했다.

1) CONTAINS_BOOK에 발생/인용 구분 필드가 없음: `MATCH (b:Book)-[rel:CONTAINS_BOOK]->(e:Event) RETURN DISTINCT keys(rel)` → `[]` (관계에 프로퍼티 자체가 없음). 코드에도 이를 구분하는 WHERE나 별도 relationship type이 전혀 없다 — 가드 없음.

2) 실측 재현 — Acts(`recF09FMjRr0gzjQk`, CONTAINS_BOOK Event 111개)에 라우트와 동일한 정렬(연도 오름차순, top 10 절단)을 적용한 결과:
   `-2091 God calls Abraham in Ur of the Chaldeans (authored-abraham-call-ur)` 가 1위, 나머지 9개는 전부 `0030`년 사건(오순절 설교·나면서 못걷게 된 이 치유·베드로/요한 재판·스데반 연설 등, 행 2~5장 실제 사건). 바울의 …
- **제안 수정방향**: topEvents 산출 시 CONTAINS_BOOK을 '실제 발생'(주 저작 관계) 대 '회고 인용'으로 구분하는 별도 관계/플래그를 쓰거나, 최소한 동률(같은 연도) 시 canonical 순서/이벤트 인덱스로 안정적 2차 정렬을 추가하고 극단적 아웃라이어(다른 책의 far-flashback 참조)를 topEvents 후보에서 제외.

## 5. [MEDIUM] `backend/app/routes/persons.py:145` — `_build_connections`가 `@functools.lru_cache(maxsize=None)`로 사용자 제어 `node_id`(URL 경로 파라미터)를 캐시 키로 받아, 무인증 GET 요청만으로 캐시가 무한 누적된다(프로세스 재시작 전까지 …

- **렌즈**: 보안/성능 · 적대적 검증 **CONFIRMED**
- **증상**: `_build_connections`가 `@functools.lru_cache(maxsize=None)`로 사용자 제어 `node_id`(URL 경로 파라미터)를 캐시 키로 받아, 무인증 GET 요청만으로 캐시가 무한 누적된다(프로세스 재시작 전까지 해제 불가).
- **근거**: persons.py:145-153 `@functools.lru_cache(maxsize=None)\ndef _build_connections(node_id: str) -> dict:\n    curated = _build_list()\n    by_id = {p["id"]: p for p in curated}\n    me = by_id.get(node_id)\n    if me is None:\n        return {"coParticipants": [], "contemporaries": []}` 그리고 persons.py:187-188 `@router.get("/person/{node_id}/connections")\ndef get_person_connections(node_id: str):` — node_id는 인증·검증 없이 그대로 캐시 함수에 전달됨. 실제 실행 중인 스택(docker compose)에 대해 임의 문자열로 반복 호출해 확인: `curl http://localhost:8080/api/person/attacker-garbage-id-12345/connections` → `{"coParticipants":[],"contemporaries":[]}` (200 OK, 존재하지 않는 id도 즉시 캐시에 영구 저장됨). CONCERNS.md는 같은 취약 패턴을 `places.py:21 …
- **재현**: 공격자가 인증 없이 `/api/person/<임의의 고유 문자열>/connections`를 대량으로, 매번 다른 node_id로 반복 호출 → nginx에는 rate limit(`limit_req`)이 없어 제한 없이 가능(nginx/nginx.conf 전체 확인, limit_req_zone 없음) → 매 고유 문자열이 `_build_connections`의 lru_cache 딕셔너리에 영구 엔트리로 남아 uvicorn 단일 프로세스 메모리가 무한정 증가(재시작 전까지 회수 불가) — 자원 고갈 DoS.
- **검증 요지**: 코드·실측 모두 finding을 뒷받침한다.

1) 코드 확인 — backend/app/routes/persons.py:145-146 `@functools.lru_cache(maxsize=None)\ndef _build_connections(node_id: str) -> dict:` 이후 라우트 :187-188 `@router.get("/person/{node_id}/connections")\ndef get_person_connections(node_id: str):` — node_id에 대한 검증·화이트리스트·인증이 전무. `main.py`에는 CORSMiddleware 외 미들웨어 없음, 인증(Depends 등)도 전무.

2) 실측 — 실행 중인 스택(`biblemap-api-1`)에 대해 `curl http://localhost:8080/api/person/attacker-garbage-id-12345/connections` → `200 {"coParticipants":[],"contemporaries":[]}`. 즉 존재하지 않는 임의 id도 200으로 응답하며 그 과정에서 `_build_connections(node_id)`가 호출·캐시됨(파이썬 …
- **제안 수정방향**: `functools.lru_cache(maxsize=None)` → 상한이 있는 값으로 교체(예: `maxsize=256`, 큐레이션 35인 규모에 맞춰), 또는 `by_id.get(node_id) is None`인 경우(비큐레이션 id)는 캐시하지 않고 즉시 빈 응답을 반환하도록 분기.

## 6. [MEDIUM] `backend/app/routes/places.py:33` — `_place_to_persons`가 이벤트의 `occursAt` 배열 전체(모든 인덱스)를 검사해 '이 장소를 지난 인물'로 포함시키지만, journey.py/tours.py는 `occursAt[0]`(첫 장소)만 정차지 좌표로 사용한다. 결과: …

- **렌즈**: 백엔드 정합성 · 적대적 검증 **CONFIRMED**
- **증상**: `_place_to_persons`가 이벤트의 `occursAt` 배열 전체(모든 인덱스)를 검사해 '이 장소를 지난 인물'로 포함시키지만, journey.py/tours.py는 `occursAt[0]`(첫 장소)만 정차지 좌표로 사용한다. 결과: 어떤 이벤트의 occursAt이 2개 이상이고 조회 대상 place_id가 [0]이 아니면, 그 장소 상세 화면은 해당 인물을 '지난 인물'로 보여주지만 그 인물의 실제 여정(journey) 지도에는 그 장소가 정차지로 전혀 나타나지 않는다.
- **근거**: places.py:33 `visited = any(place_id in evt.get("occursAt", []) for evt in events)` — 배열 전체 검사. journey.py:93-97 `place_ids = list({e["occursAt"][0] for e in events if e.get("occursAt")})` 및 journey.py:103 `place_id = event["occursAt"][0] if event.get("occursAt") else None` — occursAt[0]만 사용. `data/person_events/moses.json`의 `authored-moses-spies-hebron` 이벤트가 `occursAt: [recJSfVnIcPibY6aX(헤브론), recRxBBePxyyV6TFO(가나안)]`로 2개 장소를 가짐.
- **재현**: `curl http://localhost:8080/api/place/recRxBBePxyyV6TFO/curated-persons`(가나안) → `{"persons":[{"id":"recjNRR60PAuFtjha","slug":"moses",...}]}` — 모세가 '이 곳을 지난 인물'로 나옴. 그러나 `curl http://localhost:8080/api/person/recjNRR60PAuFtjha/journey` → 13개 stops 중 `placeId=="recRxBBePxyyV6TFO"`인 항목 0건(해당 이벤트의 stop은 `placeId: recJSfVnIcPibY6aX`(헤브론)만 기록). SidePanel.jsx:630-633의 '이 곳을 지난 인물' 목록에서 모세를 클릭(`onExploreJourney`)해도 가나안 지점은 그의 여정 경로에 전혀 표시되지 않아 UI 주장과 실제 지도가 모순됨. 동일 패턴이 …
- **검증 요지**: 코드·데이터를 직접 실행/추적해 finding의 핵심 주장이 사실임을 확인했다.

1) places.py:33 `visited = any(place_id in evt.get("occursAt", []) for evt in events)` — occursAt 배열 전체를 검사(그대로 확인됨).
2) journey.py:93-97, 103 — `place_ids = list({e["occursAt"][0] ... })`, `place_id = event["occursAt"][0] if event.get("occursAt") else None` — occursAt[0]만 사용(그대로 확인됨).
3) 실제 데이터: data/person_events/moses.json의 `authored-moses-spies-hebron` 이벤트가 `occursAt: ["recJSfVnIcPibY6aX"(헤브론), "recRxBBePxyyV6TFO"(가나안)]`로 확인됨(names_ko/places.json에서 각각 '헤브론', '가나안'으로 매핑됨).
4) `_place_to_persons` 함수를 실제로 import해 실행: …
- **제안 수정방향**: `_place_to_persons`도 journey.py와 동일하게 `occursAt[0]`만 검사하도록 통일하거나, 반대로 journey.py의 정차지 좌표 산출을 occursAt 전체 순회로 확장 — 두 엔드포인트가 '방문/정차' 판정 기준을 반드시 일치시켜야 함.

## 7. [MEDIUM] `backend/app/routes/places.py:21` — /place/{place_id}/curated-persons는 place_id를 검증 없이 그대로 lru_cache(maxsize=None) 키로 사용한다. 캐시 미스(=이전에 없던 임의 문자열)일 때마다 person_events 35개 파일 전부를 …

- **렌즈**: 백엔드 견고성 · 적대적 검증 **CONFIRMED**
- **증상**: /place/{place_id}/curated-persons는 place_id를 검증 없이 그대로 lru_cache(maxsize=None) 키로 사용한다. 캐시 미스(=이전에 없던 임의 문자열)일 때마다 person_events 35개 파일 전부를 열어 파싱하는 비용을 치르고, 그 결과가 매치 0건(빈 리스트)이어도 해당 문자열이 프로세스 종료까지 캐시에 영구 보존된다.
- **근거**: places.py:21-28 `@functools.lru_cache(maxsize=None)\ndef _place_to_persons(place_id: str) -> list[dict]:\n    result = []\n    for slug in _ERA:\n        path = _resolve(f"person_events/{slug}.json")\n        ...` — place_id가 실제 Place인지 확인하는 코드가 전혀 없다. places.py:68 `persons = _place_to_persons(place_id)`에서 검증 없이 바로 호출. main.py:45-51에서 CORS는 `allow_origins=["*"]`(GET 전용)이라 브라우저发 스크립트로도 제약 없이 대량 호출 가능.
- **재현**: 공개 GET 엔드포인트에 서로 다른 임의 문자열로 `/place/<random>/curated-persons`를 대량 요청(curl 루프 또는 악성 페이지의 브라우저 fetch)하면, 요청마다 person_events 35개 파일 I/O(디스크 오픈+JSON 파싱)가 발생하고 결과 무관하게 그 키가 영구 캐시돼 프로세스 메모리가 요청한 고유 문자열 수만큼 무한정 누적된다. CONCERNS.md는 '고유 place_id 수만큼' 성장한다고 전제했지만 실제로는 place_id 존재 여부 검증이 전혀 없어 실재하지 않는 임의 문자열도 그대로 영구 캐시 키가 된다는 점이 문서화되지 않았다.
- **검증 요지**: 코드와 실측 모두 finding을 뒷받침한다. places.py:21 `@functools.lru_cache(maxsize=None)\ndef _place_to_persons(place_id: str)`에는 place_id가 실제 Place 노드인지 검증하는 코드가 전혀 없고, places.py:68에서 라우트 핸들러가 검증 없이 바로 호출한다. main.py:39-46은 인증/레이트리밋 미들웨어가 전혀 없고 CORS는 `allow_origins=["*"], allow_methods=["GET"]`이며, nginx.conf에도 `limit_req` 등 속도 제한이 없다(grep 결과 전 백엔드에 slowapi/Limiter/throttle 전무).

실제로 backend에서 모듈을 import해 임의 UUID 200개로 `_place_to_persons`를 호출한 결과:
`CacheInfo(hits=0, misses=200, maxsize=None, currsize=200)`
— 존재하지 않는 무작위 문자열 200개가 그대로 영구 캐시 엔트리로 남았고, 캐시가 unbounded(maxsize=None)이므로 프로세스 종료까지 절대 축출되지 않는다. 미스마다 …
- **제안 수정방향**: place_id를 먼저 실제 Place 집합(화이트리스트 또는 Neo4j 존재 확인)으로 검증한 뒤에만 결과를 캐시하거나, 캐시를 유한 maxsize로 제한하거나, 매치 0건인 place_id는 애초에 캐시하지 않고 바로 반환.

## 8. [MEDIUM] `backend/app/routes/tours.py:70` — _build_event_index()는 _ERA 삽입 순서대로(정렬 없이) 35개 person_events 파일을 순회하며 eventId를 키로 dict에 쓰는데, 서로 다른 두 큐레이션 인물 파일에 같은 eventId가 등장하면 검증·경고 없이 …

- **렌즈**: 백엔드 견고성 · 적대적 검증 **CONFIRMED**
- **증상**: _build_event_index()는 _ERA 삽입 순서대로(정렬 없이) 35개 person_events 파일을 순회하며 eventId를 키로 dict에 쓰는데, 서로 다른 두 큐레이션 인물 파일에 같은 eventId가 등장하면 검증·경고 없이 나중에 순회된 slug의 사본으로 조용히 덮어써진다. 투어 상세(/tour/{id})에 노출되는 title/nameKo/participants가 의도치 않은 다른 인물의 버전으로 바뀔 수 있다.
- **근거**: tours.py:59-70 `for slug in _ERA:\n    path = _resolve(...)\n    ...\n    for e in events:\n        index[e["id"]] = e` — 중복 eventId 검사 없음. persons.py의 _build_list()는 `sorted(_ERA.keys())`로 결정적 정렬을 쓰는 것과 달리 여기는 _ERA dict 리터럴의 선언 순서(미정렬) 그대로 순회하므로, 승자는 코드상 나중에 선언된 slug(예: 'peter'가 'adam'보다 항상 우선)로 암묵 결정된다.
- **재현**: 현재 data/person_events/*.json 전수 검사 결과 eventId 중복 0건(재현 안 됨, 스크립트로 확인). 다만 향후 두 큐레이션 인물 파일이 같은 사건을 서로 다른 title/nameKo/participants로 각자 기록하면(공유 사건을 양쪽에 저작), 그 eventId가 포함된 투어의 stop에서 에러 없이 잘못된 인물 라벨/제목이 노출된다.
- **검증 요지**: tours.py:56-70 `_build_event_index()`와 tours.py:100-142 `get_tour()`를 실제로 읽고, 레포 외부 임시 디렉터리(/tmp/biblemap_repro)에 `adam.json`/`peter.json` 두 파일로 동일 eventId("shared-event-1")를 심어 DATA_DIR을 그쪽으로 돌린 뒤, 레포의 수정되지 않은 `_build_event_index()`를 그대로 import·실행해 재현했다. 결과: _ERA 딕셔너리 리터럴(persons.py:20-55)에서 peter가 adam보다 뒤에 선언되어 있으므로 index[e["id"]]=e가 아무 경고 없이 Peter 쪽 사본으로 덮어쓰는 것을 실측 확인({'title': "Peter's Version", ...}). 이 event_index는 get_tour()에서 event["title"]/event["nameKo"]/event["participants"][0]로 그대로 소비돼(tours.py:130-141) 투어 stop에 잘못된 인물 라벨이 노출되는 경로도 코드로 확인. 가드 존재 여부 확인 결과 …
- **제안 수정방향**: _build_event_index() 구성 시 동일 eventId가 이미 존재하면 logger.warning으로 경고하거나, 저작 시점 검증 스크립트(person_relations/AUTHORING.md류)에 person_events 전체 eventId 유일성 검사를 추가.

## 9. [MEDIUM] `data/person_relations/relations.json:23822` — 욥↔엘리후 관계(relations[169], type="친구")의 두 번째 국면 approxYear가 -1897.5로 비정수(float)다. 전체 627국면 중 유일한 예외로, AUTHORING.md 규약("대략 연도... 국면 시간순 정렬 키", …

- **렌즈**: 데이터 계약 · 적대적 검증 **CONFIRMED**
- **증상**: 욥↔엘리후 관계(relations[169], type="친구")의 두 번째 국면 approxYear가 -1897.5로 비정수(float)다. 전체 627국면 중 유일한 예외로, AUTHORING.md 규약("대략 연도... 국면 시간순 정렬 키", 정수 예시만 사용)과 CONCERNS.md가 명시한 전제("이미 정수라 파싱은 없지만")를 둘 다 어긴다.
- **근거**: data/person_relations/relations.json:23818-23822 — { "valence": "중립", "label": "고난의 교육적 의미를 변론", "verse": "욥 36:15", "approxYear": -1897.5, ... } (직전 국면은 approxYear: -1898 정수). 소비처 frontend/src/RelationsView.jsx:43 — const era = y => y < 0 ? `BC ${-y}` : `AD ${y}` — 이 함수가 정수를 전제로 부호만 뒤집어 문자열에 꽂는다. 세 호출부(:72 VerseLayer, :122 초점 스토리라인, :177 개요 칩) 모두 동일.
- **재현**: 인물 상세에서 욥→엘리후 관계 카드를 열고 두 번째 국면("고난의 교육적 의미를 변론")의 칩/상세 레이어를 보면 era(-1897.5)가 그대로 계산되어 "BC 1897.5"로 렌더된다 — 나머지 626개 국면이 전부 "BC 1898" 같은 정수 연도로 표시되는 것과 형식이 어긋난다.
- **검증 요지**: 데이터·코드·산출 결과 모두 실측 확인함.

1. data/person_relations/relations.json:23822 — 욥↔엘리후 관계 두 번째 국면의 approxYear가 실제로 -1897.5 (직전 국면 :23791은 -1898, 정수). `grep -c approxYear`로 전체 627국면 중 `.5`가 붙은 값은 이 한 건뿐 — 유일한 예외라는 finding의 주장이 정확함.

2. AUTHORING.md:34,60이 "대략 연도... 국면 시간순 정렬 키"·"국면은 시간순 — approxYear 오름차순"이라 명시하고 예시는 전부 정수(-1025 등)이며, .forge/codebase/CONCERNS.md:101이 "관계 국면 approxYear는 이미 정수라 파싱은 없지만"이라고 전제함 — 이 -1897.5가 두 문서의 전제를 모두 깨는 것도 확인됨.

3. 소비 경로 추적: backend/app/routes/persons.py `_build_relations()`는 phases를 `pair.get("phases", [])`로 그대로 통과시킴(반올림/정수화 없음) → `/person/{id}/relations` API가 …
- **제안 수정방향**: 저작 실수로 보이므로 -1897.5를 의도된 정수(-1897 또는 -1898)로 정정. 재발 방지로 generate_verse_text.py 검증 단계나 별도 스크립트에 approxYear가 int인지 확인하는 체크 추가 권장.

## 10. [MEDIUM] `frontend/src/useNodeSelection.js:33` — 인물 탐험 중 지도의 장소(Place)/사건 등 인물이 아닌 노드를 한 번이라도 클릭하면, 그 순간부터 타임라인 뷰의 인물 필터가 조용히 풀려 전체 비필터 타임라인이 보인다.

- **렌즈**: 프론트 정합성 · 적대적 검증 **CONFIRMED**
- **증상**: 인물 탐험 중 지도의 장소(Place)/사건 등 인물이 아닌 노드를 한 번이라도 클릭하면, 그 순간부터 타임라인 뷰의 인물 필터가 조용히 풀려 전체 비필터 타임라인이 보인다.
- **근거**: useNodeSelection.js:33-39 `selectNode`가 노드 선택 시마다 무조건 `setPersonEventIds(null)`을 호출하고, `handleNodeLoaded`(13-28)도 `node.label !== 'Person'`이면 `setPersonEventIds(null)`로 재차 초기화한다. 이 값은 App.jsx:331 `personFilter={explorePersonId != null ? personEventIds : tourEventIds}`로 그대로 TimelineView에 전달되고, TimelineView.jsx:93 `activePersonFilter = personFilter && ... ? personFilter : null` → `personEventIds`가 null이면 `activePersonFilter`도 null이 되어 104행 필터(`!activePersonFilter || ...`)가 전부 통과한다. 투어 모드의 동등 값인 `tourEventIds`(App.jsx:47-50)는 `journeyStops`에서만 파생되어 노드 선택과 무관하므로 이 비대칭이 의도된 설계가 아님을 뒷받침한다.
- **재현**: PersonHub에서 큐레이션 인물 P 선택(explorePersonId=P) → 지도에서 P의 여정 정거장인 장소 마커 아무거나 클릭(selectNode(placeId) 호출, personEventIds→null) → '타임라인' 탭으로 전환. 기대: P의 사건만 필터된 타임라인. 실제: personFilter가 null이 되어 성경 전체 이벤트가 무필터로 표시되고, '○○이 언급된 사건' 칩(TimelineView.jsx:253)도 사라져 사용자는 필터가 깨졌다는 신호조차 못 받는다. 장소 마커 클릭은 인물 여정 탐험의 핵심 동선이라 재현 난도가 낮다.
- **검증 요지**: 코드 추적 결과 finding이 정확함을 확인.

호출 체인 실측:
1. `mapLayers.js:61,86,111` — 지도의 `places-circle`/`place-spider-circle`/`event-ring-circle` 클릭 핸들러가 노드 종류를 가리지 않고 무조건 `onSelectNode(id)`를 호출한다. 이는 MapView(`onSelectNode={selectNode}`, App.jsx:285)를 통해 인물 여정의 정거장 마커를 포함한 모든 장소/사건 마커 클릭에 해당하는, 지도 탐험의 가장 기본적인 상호작용이다.
2. `useNodeSelection.js:33-39` `selectNode`는 노드 타입 무관 `setPersonEventIds(null)`을 무조건 호출. 뒤이어 `SidePanel`이 `/node/{id}`를 fetch해 `handleNodeLoaded`(13-28)를 호출하는데, 장소 노드는 `node.label !== 'Person'`이므로 다시 `setPersonEventIds(null)`(26행) — 이중으로 null 확정.
3. `useStageNavigation.js:14,127-133` — …
- **제안 수정방향**: handleNodeLoaded/selectNode에서 personEventIds를 무조건 초기화하지 말고, explorePersonId 자신에 대한 event-ids를 별도 상태로 유지(예: useStageNavigation에서 explorePersonId 변경 시에만 fetch)하거나, App.jsx의 personFilter 계산을 selectedNode가 아닌 explorePersonId 기준으로 독립시켜야 한다.

## 11. [MEDIUM] `frontend/src/useStageNavigation.js:88` — PersonHub와 useStageNavigation이 `/persons/curated`를 각자 독립적으로 두 번 호출하는데, 이 둘의 완료 시점이 어긋나면(예: 한쪽만 일시 실패해 재시도 백오프에 들어간 경우) 사용자가 카드를 클릭해도 URL …

- **렌즈**: 프론트 정합성 · 적대적 검증 **CONFIRMED**
- **증상**: PersonHub와 useStageNavigation이 `/persons/curated`를 각자 독립적으로 두 번 호출하는데, 이 둘의 완료 시점이 어긋나면(예: 한쪽만 일시 실패해 재시도 백오프에 들어간 경우) 사용자가 카드를 클릭해도 URL 해시가 갱신되지 않고, `navSyncRef`가 미초기화 상태로 남아 다음 히스토리 기록이 push 대신 replace로 잘못 처리된다.
- **근거**: PersonHub.jsx:169-192가 카드 렌더용으로 `/persons/curated`를 자체 fetch하고, useStageNavigation.js:34-52가 slug 매핑용으로 같은 엔드포인트를 별도로 다시 fetch한다(curatedIdToSlug/curatedSlugToId는 후자에만 채워짐). 사용자가 handleSelectPerson(127-133)으로 explorePersonId를 세팅했는데 이 시점에 useStageNavigation 쪽 fetch가 아직 안 끝났다면, 동기화 effect(85-104)의 88행 `if (activeStage === 'explore' && !slug && !exploreTourId) return`이 조기 반환되며, 이 반환은 `navSyncRef.current`(26행, 101행) 갱신 이전이라 `initialized` 플래그가 그대로 false로 남는다. 이후 curatedIds가 로드되어 exploreView 토글 등으로 effect가 다시 돌면 `prev.initialized`가 false이므로 99행 `isForward`가 항상 false가 되어 `pushState` 대신 `replaceState`(103행)가 실행된다.
- **재현**: 네트워크가 불안정해 useStageNavigation의 `/persons/curated` 요청만 1차 실패(PersonHub의 동일 요청은 성공)하는 상태에서 사용자가 카드를 즉시 클릭 → activeStage='explore'로 바뀌지만 해시는 `#/`에 고정. curatedIds 재시도 성공 후 사용자가 '타임라인' 탭을 누르면 그제서야 해시가 써지는데 replaceState로 기록되어, hub→explore 전환이 별도 히스토리 항목으로 남지 않는다. 이후 브라우저 뒤로가기를 누르면 hub를 건너뛰고 그 이전 페이지(또는 히스토리 부재)로 튄다.
- **검증 요지**: 코드를 끝까지 추적한 결과 이 finding은 사실상 confirmed다. 핵심 근거:

1. **독립된 이중 fetch 확인**: PersonHub.jsx:174 `apiGet('/persons/curated')`와 useStageNavigation.js:37 `apiGet('/persons/curated')`는 완전히 독립된 useEffect에서 각자 호출된다. api.js의 apiGet은 단순 fetch 래퍼로 캐싱/디듀프가 전혀 없다(`const res = await fetch(API_BASE + path, { signal })`) — 두 요청은 실제 별도 네트워크 호출이다.

2. **PersonHub는 useStageNavigation의 준비 상태를 전혀 기다리지 않음**: App.jsx:228-236에서 `{activeStage === 'hub' && <PersonHub onSelectPerson={selectPerson} .../>}` — curatedIds나 restored를 prop으로 넘기거나 게이팅하지 않는다. 실제로 useStageNavigation의 반환 객체(194-206행)에는 `restored`가 아예 노출되지도 않는다. 즉 …
- **제안 수정방향**: 동일 `/persons/curated` fetch를 하나로 합쳐(App 레벨에서 한 번 fetch해 props로 내려주기 등) 두 컴포넌트의 준비 시점을 일치시키거나, 88행 조기 반환 전에도 `navSyncRef.current`를 최신 activeStage/person/tour로 갱신해 다음 write의 isForward 판정이 어긋나지 않게 한다.

## 12. [MEDIUM] `frontend/src/useStageNavigation.js:56` — 딥링크 복원 effect가 `curatedIds` 로드 완료를 기다린 뒤에만 동작하는데, 이 게이트가 인물 slug 해석이 필요 없는 `#/books`·`#/tours` 같은 해시에도 그대로 걸려 있어, curated API가 최종 실패하면 어떤 …

- **렌즈**: 프론트 정합성 · 적대적 검증 **CONFIRMED**
- **증상**: 딥링크 복원 effect가 `curatedIds` 로드 완료를 기다린 뒤에만 동작하는데, 이 게이트가 인물 slug 해석이 필요 없는 `#/books`·`#/tours` 같은 해시에도 그대로 걸려 있어, curated API가 최종 실패하면 어떤 딥링크도 영원히 복원되지 않고 hub에 고착된다.
- **근거**: useStageNavigation.js:56-79의 복원 effect 시작부 `if (!curatedIds || restoredRef.current) return`가 `parsed.stage === 'overview'`(64행)·`'tours'`(65행) 분기까지 포함한 전체 복원 로직을 감싼다. `curatedIds`는 34-52행의 `/persons/curated` fetch가 성공해야만 세팅되며, 이 fetch가 3회 재시도(1s→2s→4s) 후에도 실패하면(47행 `console.warn`만 남기고) `curatedIds`는 계속 null로 남는다. 이후 68-104행의 히스토리 동기화 effect도 `if (!restored) return`으로 막혀 있어(85행), 잘못된 해시를 되돌려 쓰는 자가치유조차 일어나지 않는다.
- **재현**: `/persons/curated`가 지속적으로 실패하는 상태(백엔드 일시 장애 등)에서 사용자가 `#/books` 딥링크로 진입 → curatedIds가 끝내 null로 남아 `parseHash`는 정상 파싱되지만 setActiveStage('overview') 호출부 자체가 실행되지 않아 앱은 hub 화면에 멈추고, 주소창 해시도 교정되지 않은 채 `#/books`로 남는다(공유된 링크가 무한정 깨진 것처럼 보임).
- **검증 요지**: 코드를 끝까지 추적한 결과 finding 그대로 재현됨.

1. useStageNavigation.js:57 `if (!curatedIds || restoredRef.current) return` — 이 게이트가 62-76행 전체(overview·tours·explore 3분기)를 감싼다.
2. urlState.js:27-28에서 `parseHash('#/books')` → `{stage:'overview', ...}`, `parseHash('#/tours')` → `{stage:'tours', ...}` — 두 분기 모두 `curatedIdToSlug`/`curatedSlugToId`를 전혀 참조하지 않는다(useStageNavigation.js:64-65 `setActiveStage('overview')`/`setActiveStage('tours')`만 호출). 즉 이 두 분기는 curatedIds에 대한 실질적 의존이 없는데도 게이트에 걸려 있다.
3. curatedIds 로드(34-52행)는 실패 시 1s→2s→4s(총 7s) 재시도 후 41-47행에서 `console.warn`만 남기고 영구 포기 — 성공 브랜치(38-43행)만 …
- **제안 수정방향**: curatedIds 의존성은 personSlug 분기에만 걸고, overview/tours(및 tourSlug) 분기는 curatedIds 로드 여부와 무관하게 즉시 복원하도록 gating을 분리한다.

---

## 적대적 검증에서 기각된 항목 (refuted 3 — 투명성 기록)

- `frontend/src/dates.js:7` — parseYear()가 BC 분기와 AD 분기에서 '연도부가 전부 0'인 퇴화 입력을 서로 다르게 처리한다 — BC 쪽은 'BC 0'을, AD 쪽은 'AD 1'을 반환해 같은 개념의 입력에 비대칭 출력을 낸다.
  - 기각 사유: 기계적 주장 자체는 참(직접 실행 확인): parseYear('-0000')→'BC 0', parseYear('0000-01-01')→'AD 1', parseYear('-0')→'BC 0', parseYear('0')→'AD 1' — 코드상 BC/AD 폴백이 '0'/'1'로 다른 것은 사실.

다만 "실제 발생 가능한 버그"로서는 반박됨:

1) 도달 가능성 — 데이터상 발생 불가: startDate는 person_events/verse_events/authored_events/person_relations 등 data/ 전체(15개 하위 디렉터리, 고유 startDate 패턴 201개)에서 정규식 전수 조사 결과 '-0000'/'0000'/'-0'/'0' 등 "연도부 전부 0"인 값이 **0건**. …
- `frontend/src/mapLayers.js:96` — places-cluster 클릭 핸들러가 비동기(getClusterExpansionZoom)로 await한 뒤 map.easeTo를 호출하는데, 그 사이 MapView가 언마운트(map.remove() 호출)되어도 …
  - 기각 사유: 코드는 finding 인용대로 맞다 — mapLayers.js:96-100의 places-cluster 핸들러엔 실제로 destroyed 가드가 없고, mapRingController.js의 expandPlace(:100-137)와 대조적으로 비대칭인 것도 사실이다. 하지만 maplibre-gl 5.24.0(frontend/node_modules/maplibre-gl/dist/maplibre-gl-dev.js, package.json:14 "^5.24.0")의 실제 구현을 끝까지 추적하면 이 비대칭이 실질적 버그로 이어지지 않는다.

핵심: getClusterExpansionZoom()가 반환하는 Promise는 GeoJSONSource.getClusterExpansionZoom (48825줄) → …
- `data/place_coords/places.json:1` — person_events의 occursAt이 참조하는 장소 id 110개(occursAt[0]만 쓰면 109개) 중 25~26개가 data/place_coords/places.json(84건)에 없다 — 이 파일만 …
  - 기각 사유: 코드·라이브 데이터 양쪽으로 확인한 결과 이 finding은 "실제 버그"가 아니라는 자체 결론이 맞다 — 반박 성공(REFUTED).

1) 소비 경로 재확인: backend/app/routes/journey.py:42-70 _fetch_place_coords는 data/place_coords/places.json을 전혀 읽지 않고 Neo4j에 `MATCH (p:Place {theographic_id: tid}) RETURN p.longitude, p.latitude`로 직접 조회한다(line 53-57). get_person_journey(line 73-137)도 이 결과만 사용한다. JSON 파일은 백엔드 요청 경로에 전혀 관여하지 않는다.

2) 수치 재현: places.json은 84개 …
---

## 데이터 계약 기계검증 결과 (렌즈⑤ 실측 — 주장 아닌 실행)

`data/` 오버레이 ↔ 소비 코드 계약을 python3 읽기 전용 스크립트로 재실행(2026-07-10, HEAD `a7753bc`):

| 검사 | 결과 | 상세 |
|------|------|------|
| ① person_events 파일명 == `_ERA` 키 | ✅ PASS | 파일 35 == _ERA 35, 차집합 없음 |
| ② relations endpoint slug ⊆ person_events | ✅ PASS | 고유 slug 35, 미해결 0 |
| ③a relations `type` ⊆ `TYPE_ICON`(9종) | ✅ PASS | 데이터 9종 전부 상수에 존재 |
| ③b phase `valence` ⊆ `VALENCE_COLOR`(3종) | ✅ PASS | 긍정·부정·중립만 사용 |
| ④a phase `approxYear` 정수 | ❌ **FAIL** | 627국면 중 1건 비정수 `-1897.5` → **finding #9** |
| ④b 인용절 `verseTextKo` null | ✅ PASS | null 0건(전부 프리베이크 완료) |
| ⑥ tours stops ⊆ person_events 사건 id | ✅ PASS | 투어 9개, 미해결 0 |

CONCERNS.md가 우려한 slug 3중 소스 드리프트·type/valence 미매칭은 **현재 정합**(강제 스키마·테스트는 여전히 부재 — 신규 저작 시 재드리프트 가능). ⑤ occursAt 좌표는 finding #6(place↔journey 판정 불일치)로 별도 수록, 파일 부재≠무좌표(journey는 Neo4j 좌표 우선 조회 — refuted 3번째 참조).

## CONCERNS.md 대비 신규성

이 리포트의 confirmed 12건은 CONCERNS.md 기재 항목의 재나열이 아니라 **새 실패 경로**다:
- #1(overlays 파일부재 무음)·#5·#7(lru_cache 무한): CONCERNS가 "상한 없음"을 일반론으로 적었으나, 여기서 **무인증·무검증 사용자 제어 키로 실제 도달 가능**함을 라이브 실측으로 확정(200개 UUID → currsize=200).
- #2(load_books BC 파싱)·#3(정경순 위반)·#4(topEvents 오염)·#6(place/journey 불일치)·#8(eventId 덮어쓰기)·#10~#12(프론트 상태): CONCERNS 미기재 신규 발견.
- #9(approxYear float): CONCERNS가 "이미 정수라 파싱 없음"이라 전제한 것을 정면으로 반증.

## 후속

확정 12건은 심각도순으로 finding별 후속 fg-ask 수정 태스크로 분리(이 루프 밖). HIGH 2건(#1 오버레이 무음, #2 재시드 연도 파싱) 우선 권장.
