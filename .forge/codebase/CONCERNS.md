---
last_mapped_commit: 09ce447e255b45427219a08968872af4a27d45ca
mapped: 2026-06-30
---

# Codebase Concerns

분석 범위: 데이터 적재 파이프라인(`backend/scripts/*`), 백엔드 라우트(`backend/app/`), 프론트 여정·지도 렌더(`frontend/src/`), 인프라(`deploy.sh`, `docker-compose.yml`, `.github/workflows/deploy.yml`, `frontend/vite.config.js`). 본 문서는 구현 사실만 기록하며, 각 항목은 실제 코드/실행 결과로 검증했다.

## Operational / Deployment Concerns

### 큐레이션 인물 데이터의 수동 Neo4j 적재 (최상위 운영 리스크)

`deploy.sh`는 데이터 갱신 단계에서 `backend/scripts/inject_ko_names.py` **하나만** 실행한다(`deploy.sh:49-60`의 `[4/4] 한글 이름 주입`). 큐레이션 인물의 여정 사건을 Neo4j에 적재하는 `backend/scripts/load_person_events.py`(authored Event 노드 + `OCCURS_AT`/`HAS_PARTICIPANT`/`CONTAINS_BOOK` 관계 생성)·`backend/scripts/load_authored_persons.py`(authored Person 노드 MERGE)·`backend/scripts/enrich_place_coords.py`(authored-place 좌표 주입)·`backend/scripts/generate_person_event_verses.py`(구절 생성)는 **배포 스크립트에 포함되지 않으며, 호스트에서 사람이 직접 순서대로 실행**해야 한다.

- 검증: `grep "scripts/" deploy.sh` 결과는 `inject_ko_names.py` 단 한 줄. 위 로더 스크립트들은 어떤 자동 경로에도 없다.
- `README.md:17-21`의 "데이터 적재 (최초 1회)"는 `load_theographic.py` + `inject_ko_names.py`만 안내하고 authored Person 관련 스크립트는 전혀 나오지 않는다. 인물 적재 절차가 문서화된 곳은 `.forge/done/` 하위 plan/run.md 및 회고뿐이다.
- **적재 순서 제약**: `load_authored_persons.py` → `enrich_place_coords.py` → `load_person_events.py` 순서를 지켜야 `HAS_PARTICIPANT` MATCH가 성립한다(ADR-0008). 순서를 바꾸면 조용히 관계가 누락된다.
- `docker-compose.yml:22`이 `neo4j_data` named volume을 영속화하므로 평시에는 재적재가 불필요하다. 그러나 **볼륨을 리셋하면(`docker compose down -v` 등) 21인 전원을 수동으로 재적재**해야 하며, 이를 명시한 공개 문서가 없다.
- 현재 큐레이션 21인 중 5인(기드온·드보라·입다·삼손·룻)이 authored Person 노드로 추가됐다. 이들은 `load_authored_persons.py`로만 Neo4j에 존재하며, Theographic `rec` id가 없어 `load_theographic.py`로 복구되지 않는다.
- API 컨테이너는 `data/`를 마운트(`docker-compose.yml:19`)하지만 적재는 **호스트에서 `bolt://127.0.0.1:7687`로 직접** 수행한다. 컨테이너 내부에서 스크립트를 실행하는 경로는 없다.
- 이 호스트 Neo4j는 Cloudflare Tunnel을 통해 외부에서 접근하는 앱과 동일 인스턴스, 즉 **프로덕션 데이터와 같은 그래프**다. 호스트 inject/load 스크립트는 곧바로 운영 데이터를 변경한다.
- 영향: 인물 추가 시 ① `data/authored_persons/people.json` 등록 → ② `persons.py` `_ERA`/`_NAME_KO` 등록 → ③ `data/person_events/<slug>.json` 작성 → ④ `generate_person_event_verses.py` 실행(구절) → ⑤ `load_authored_persons.py`(먼저) → ⑥ `enrich_place_coords.py`(좌표) → ⑦ `load_person_events.py`(여정) → ⑧ 빌드·재배포의 다단계 수동 절차가 필요하며, 어느 단계든 누락 시 침묵 발산한다.
- 파일: `deploy.sh`, `README.md:17-21`, `backend/scripts/load_authored_persons.py`, `backend/scripts/load_person_events.py`

### `deploy.sh`의 한글 이름 주입이 배포 게이트 (부분 적용 위험)

`deploy.sh:50-60`은 `inject_ko_names.py`를 2초 간격 15회까지 재시도하고, 끝까지 실패하면 `exit 1`로 배포를 중단한다. inject는 컨테이너 재시작(`up -d api nginx`, `deploy.sh:46`) **뒤에** 실행되므로, 주입이 실패하면 컨테이너는 이미 새 코드로 떠 있는데 배포 스크립트만 실패로 종료된다(부분 적용 상태).

- 파일: `deploy.sh:46-61`
- 완화: 프론트가 `nameKo || name` 폴백을 쓰므로 주입 실패 시 영문 이름으로라도 노출돼 치명도는 낮다. CI는 실패로 표시된다.

### CI 워크플로가 특정 머신 절대경로에 묶임

`.github/workflows/deploy.yml`이 `runs-on: self-hosted` + `cd /Users/calmonion/Project/BibleMap`로 한 머신의 self-hosted 러너 경로에 하드코딩돼 있고, `git reset --hard origin/main`으로 워크트리의 로컬 변경을 무조건 폐기한다.

- 파일: `.github/workflows/deploy.yml`
- 영향: 러너 머신/경로 변경 또는 러너 오프라인 시 무음 미배포 가능. 현 단일 self-hosted 스택 전제에선 의도된 설계다.

### `lru_cache`가 런타임 데이터 갱신을 가림

`persons.py`·`places.py`·`events.py`·`overlays.py`의 `@functools.lru_cache`(예 `persons.py:59` `_build_list`)는 프로세스 생애 동안 결과를 보관한다. 배포마다 컨테이너를 `up -d`로 재기동하므로 배포 단위로는 캐시가 비워져 실질 문제는 낮으나, 호스트 inject/load 스크립트가 **컨테이너 기동 후** Neo4j를 갱신하는 동안에는 캐시가 갱신 전 데이터를 들고 있을 수 있다.

## Tech Debt

### 스테일 docstring — `persons.py`·`journey.py`의 "13인" 표기

실제 큐레이션 인물은 21인(`_ERA` 딕트 21개 항목, `data/person_events/` 21개 파일)이지만 두 파일의 docstring에 여전히 "13인"이 기재돼 있다.

- `backend/app/routes/persons.py:1`: `"""큐레이션된 13인 인물 목록 엔드포인트.`
- `backend/app/routes/persons.py:97`: `"""활동범위가 그려지는 큐레이션된 13인 목록.`
- `backend/app/routes/journey.py:6`: `큐레이션 13인이 아니면 빈 stops 반환(404 아님).`
- `backend/app/routes/journey.py:77`: `큐레이션 13인이 아니면 stops=[] 빈 응답 반환.`
- 검증: `grep -n "13인" persons.py` 2건, `grep -n "13인" journey.py` 2건, `_ERA` 항목 수 21개.

### 동명이지(同名異地) 재사용 충돌 위험

authored-place를 새 인물 여정에 재사용할 때 영문 지명이 같아도 다른 지점인 경우가 있다. 기드온 추가 시 `authored-place-succoth`(이집트 숙곳, lat 30.56)와 요단 동편 숙곳(lat 32.20)이 충돌해 `authored-place-succoth-jordan`을 별도 신설한 실사례가 있다.

- 현재 authored-place에 동일 영문 이름이 두 개 이상인 것: `Succoth`→`authored-place-succoth`(이집트)/`authored-place-succoth-jordan`(요단).
- 잠재 충돌 후보로 명시된 곳: `authored-place-mizpah`(베냐민 미스바, lat 31.878) vs `authored-place-mizpah-gilead`(길르앗 미스바, lat 32.05) — 둘 다 존재하나 입다 여정 추가 등 후속 큐레이션에서 "미스바" 검색으로 잘못된 id를 재사용할 수 있다.
- 규칙: 재사용 전 `data/place_coords/places.json`에서 id·좌표를 대조해 의도한 지점인지 확인 필수. 동명이지는 새 id 신설.
- 파일: `data/place_coords/places.json`, `.forge/retro/2026-06-30-curate-judges-era-1of2.md`

### 학자 추정 좌표 — 고고학적 논쟁지

`data/place_coords/places.json`의 다음 항목은 정확한 위치가 학술적으로 확정되지 않은 지점의 근사 좌표다.

| id | 좌표(lat/lng) | 비고 |
|---|---|---|
| `authored-place-mizpah-gilead` | 32.05 / 35.72 | 길르앗 미스바, 추정 지점 |
| `authored-place-aroer` | 31.95 / 35.85 | 암몬 랍바 앞 아로엘, 추정 |
| `authored-place-lehi` | 31.72 / 34.96 | 라맛레히, 추정 |
| `authored-place-kishon` | 32.60 / 35.18 | 기손 강 전투지, 범위 내 근사점 |
| `authored-place-timnah` | 31.776 / 34.925 | 삼손 혼인 딤나, 추정 |

- 지도에 핀이 찍히므로 이 좌표가 "정확한 성경 유적지"처럼 보일 수 있다.
- 파일: `data/place_coords/places.json`

### 큐레이션 인물 매핑 상수의 이중 출처 (인물 이름 동기화 결합)

인물 표시 이름의 출처가 두 곳이다. 프론트 헤더(`App.jsx:82,116,138-141`)는 Neo4j Person 노드의 `nameKo`(inject_ko_names.py 주입값)를, 큐레이션 목록·여정 응답은 `persons.py:36-53`의 하드코딩 `_NAME_KO` 딕트를 출처로 한다. 두 값이 어긋나면 헤더와 목록이 서로 다른 이름을 표시한다. 일치를 강제하는 코드/테스트는 없다.

- 파일: `frontend/src/App.jsx:82,116,138-141`, `backend/app/routes/persons.py:36-53`, `backend/app/routes/journey.py:13`, `data/names_ko/people.json`

### slug→era/이름 매핑의 다중 복제 — `places.py`가 이미 드리프트됨 (실제 버그)

`persons.py:16-56`의 `_ERA`/`_NAME_KO`/`_ERA_ORDER`가 정본이다. `journey.py:13`은 이를 `import`해 항상 동기화되지만, **`places.py:15-48`은 "단방향 참조를 피하려" 같은 상수를 별도 재선언**해 두어 인물이 추가될 때마다 수동 동기화가 필요한데 **이미 어긋나 있다**:

- `persons.py` `_ERA`는 현재 21인이나 `places.py` `_ERA`는 **13인뿐** — 누락 8인: 바울·베드로·사도 요한(task 92~94) + 기드온·드보라·입다·삼손·룻(사사, task 95~96).
- `places.py` `_ERA_ORDER`(`:48`)에는 `"사사"`가 없다. 따라서 가령 `places.py` `_ERA`에 사사 인물을 더해도 `_place_to_persons`의 `result.sort(... _ERA_ORDER.index(p["era"]) ...)`(`:77`)가 `"사사"`에서 `ValueError`를 던질 잠재 크래시가 있다.
- **결과(기능 갭)**: `/place/{place_id}/curated-persons`(장소 중심 뷰 — 지도 마커 클릭 시 그 장소를 지난 큐레이션 인물 목록)가 위 8인을 **표시하지 않는다**. 예: 가사 클릭 시 삼손, 로마 관련 장소에서 바울/베드로가 누락.
- **권장 수정**: `places.py`가 `persons.py`의 `_ERA`/`_NAME_KO`/`_ERA_ORDER`를 `import`(`journey.py`와 동일 패턴)해 재선언을 제거하면 드리프트가 근본적으로 사라진다. docstring "13인"도 함께 갱신 필요.

- 파일: `backend/app/routes/places.py:15-48,77`, `backend/app/routes/persons.py:16-56`, `backend/app/routes/journey.py:13`

### 자동화 테스트 전무

프론트·백엔드 모두 테스트 0건. `frontend/package.json` scripts에는 `lint`만 있고 vitest/jest 의존성이 없으며, 백엔드에도 pytest 설정·`test_*.py`가 없다. 좌표 dedup, 순번 압축, 여정 정차지 인덱싱 같은 회귀가 잦은 순수 로직에 안전망이 없고 검증은 수동 Playwright에 의존한다.

- 파일: `frontend/package.json`, `backend/requirements.txt`

## Fragile Areas

### `generate_person_event_verses.py`의 정규식 구절 참조 파싱

이 스크립트는 인물 사건의 `context` 한글 문장에서 **괄호 안 구절 참조를 정규식으로 파싱**해 `books` 필드와 본문을 생성한다. 자유 텍스트를 정규식으로 긁는 구조라 본질적으로 취약하다.

- 동작: `parse_context_refs`(`generate_person_event_verses.py:78`)가 `re.findall(r"\(([^)]+)\)", context)`로 괄호 덩어리를 뽑고, `;`로 분리한 뒤 책 약어(`EN_ABBR_ORDER`/`KO_ABBR_ORDER`)와 장:절 패턴을 정규식으로 매칭한다(`:91-161`). 교차 장 범위(`4:19–5:12`)는 별도 정규식(`:112`)으로 선처리한다.
- 취약점:
  - 정규식이 인식하지 못하는 표기(약어 누락, 비표준 구분자, 괄호 안 비-구절 텍스트)는 **조용히 매칭 실패** → 해당 세그먼트는 `continue`로 스킵된다(`:99-100,136-137`). 사건에 참조가 하나도 안 잡히면 `books: []`로 저장돼 📖 근거 칩이 비게 된다.
  - 같은 권 중복은 "첫 번째만" 채택(`process_event`의 `seen_book_ids`, `:230-236`)이라, 한 사건이 한 권의 여러 비인접 구간을 참조해도 첫 구간만 본문 fetch된다.
  - 교차 장 범위·장만 범위는 "첫 절만 fetch"하는 단순화(`:125,243-250`)가 들어가 있어 범위 전체 본문이 들어오지 않는다.
- 외부 의존: 본문은 `https://api.getbible.net`에서 HTTP fetch(`fetch_chapter`, `:166-184`)한다. 실패 시 예외를 잡아 `None` 캐싱 후 진행하므로(`:181-184`) 빌드는 죽지 않지만, **네트워크/외부 API에 빌드타임 의존**하며 일부 절 본문이 조용히 비어 적재될 수 있다. 타임아웃 15초, User-Agent 위장 헤더 사용.
- 파일: `backend/scripts/generate_person_event_verses.py:78-216`

### 좌표 없는 사건 = place-less 정차지 (일부 큐레이션 사건에 Place 노드 부재)

`journey.py`는 `occursAt[0]`의 Place 노드 좌표를 Neo4j에서 조회하는데, 좌표가 없으면 `seq=null`, `lng/lat=null`인 정차지로 처리한다(`journey.py:101-128`). 이는 의도된 동작이지만, 실제로 일부 큐레이션 사건에 좌표(또는 Place 노드 자체)가 없다.

- 검증: `data/person_events/*.json`에서 `occursAt: []`(빈 배열)인 사건 — `jesus.json` 1건(변형), `john_the_apostle.json` 4건(첫 제자·보아너게·변형·밧모 섬 유배 `authored-john-patmos`), `peter.json` 4건.
- 이 사건들은 여정 지도에 점이 찍히지 않고(좌표 없음), 리스트/타임라인에서만 보인다.
- authored-place는 `enrich_place_coords.py`가 `authored-place-*` id에 한해 Place 노드를 MERGE하고 좌표를 세팅한다(`enrich_place_coords.py:32-41`). 좌표를 부여하지 않은 사건/장소는 place-less로 남는다.
- 파일: `backend/app/routes/journey.py:101-128`, `data/person_events/john_the_apostle.json`, `backend/scripts/enrich_place_coords.py:32-41`

### `journey.py`가 매 요청마다 JSON 전량 재파싱 (캐시 누락)

`_build_id_to_slug()`(`journey.py:18-30`)는 `/person/{id}/journey` 요청마다 모든 `person_events/*.json`(현재 21개)을 `open`+`json.load`해 theographic_id→slug 역매핑을 새로 만든다. `persons.py`/`places.py`의 동일 파일 로드는 `@functools.lru_cache`로 캐시되는데 `journey.py`만 캐시가 없다.

- 파일: `backend/app/routes/journey.py:18-39`
- 개선: `_build_id_to_slug`에 `@functools.lru_cache(maxsize=1)` 부착(이미 `persons._build_list`가 같은 패턴).

### 데이터 무결성 가정 — 미강제

`journey.py:28`과 `persons.py:69-70`은 "각 slug json의 첫 사건 `participants[0]`이 그 인물"임을 가정한다(`persons.py:69` 주석은 "파일 내 모든 이벤트의 첫 participant가 동일인임을 검증 완료"라 명시). 이 불변식을 강제하는 코드/테스트는 없어, 새 인물 JSON에서 `participants[0]`이 다른 인물이면 역매핑이 조용히 틀린다.

- 파일: `backend/app/routes/journey.py:18-30`, `backend/app/routes/persons.py:59-79`

## Performance Bottlenecks

### maplibre 번들이 1MB 초과 (빌드 경고)

`npm run build` 결과에서 maplibre 청크가 **1,027.60 kB**(gzip 272.93 kB)로 빌드되며, "Some chunks are larger than 500 kB after minification" 경고가 뜬다. `dist/assets/`의 파일 크기로 확인: `maplibre-DntM08T7.js` 1,027,608 bytes.

- `vite.config.js:10-15`의 `manualChunks`가 `maplibre-gl`을 별도 `maplibre` 청크로, 나머지 node_modules를 `vendor`로 분리하고 있으나, maplibre 자체가 단일 청크 1MB를 넘는다.
- 영향: 첫 로드 전송량 증가. 동적 import 코드 스플리팅이나 `chunkSizeWarningLimit` 조정이 개선 경로지만 현재는 미적용.
- 파일: `frontend/vite.config.js`, `frontend/dist/assets/maplibre-DntM08T7.js`

## Code Quality

### 표준 lint 경고 1건 — `MapView.jsx` useEffect 누락 의존성

`npm run lint` 결과: 에러 0, **경고 1건**.

```
frontend/src/MapView.jsx
  61:6  warning  React Hook useEffect has a missing dependency: 'onStopSelect'. ...  react-hooks/exhaustive-deps
```

- `eslint .`는 종료코드 0(경고는 빌드를 막지 않음).
- 파일: `frontend/src/MapView.jsx:61`

## Security Considerations

### Neo4j는 외부 미노출, API는 nginx 프록시 뒤 (구조적 차단)

- `docker-compose.yml:5-7`이 Neo4j 포트를 `127.0.0.1:7474`/`127.0.0.1:7687`로만 바인딩한다. API 컨테이너는 호스트 포트를 노출하지 않고(`docker-compose.yml:13-21`에 ports 없음), nginx만 `8080:80`을 공개한다(`docker-compose.yml:30`).
- Cloudflare Tunnel(cloudflared)은 outbound 전용 연결로 ingress에 적은 것만 외부에 노출하며, Neo4j(7474/7687)는 구조적으로 외부 접근 불가다.

### CORS 전체 허용 + 무인증 (읽기 전용 전제)

- `main.py`의 CORS가 모든 오리진을 허용하고 모든 엔드포인트가 무인증 공개다. 단 `allow_methods=["GET"]`로 GET 전용이고 쓰기 엔드포인트가 없으며 공개 성경 데이터만 다룬다.
- 파일: `backend/app/main.py`(CORS 미들웨어), `backend/app/routes/*`(모두 `@router.get`)

### 비밀값 관리

- `NEO4J_PASSWORD`는 `.env`로만 공급되며 `.gitignore`로 추적 제외된다. `docker-compose.yml:11,18`이 `${NEO4J_PASSWORD:?...}`로 미설정 시 기동 실패를 강제한다.
- 모든 데이터 적재/inject 스크립트는 `NEO4J_PASSWORD` 환경변수를 요구하며 없으면 즉시 중단한다. 평문/하드코딩 비밀값 흔적 없음.
- Cypher 쿼리는 사용자 입력을 `$id`/`$q` 파라미터 바인딩으로 처리해 인젝션 경로가 아니다.

---

*Concerns audit: 2026-06-30 (commit 09ce447)*
