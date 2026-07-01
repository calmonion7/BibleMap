---
last_mapped_commit: 0189ad9fb964e5eb4fcc91776b3202f7014058dd
mapped: 2026-07-02
---

# Codebase Concerns

분석 범위: 데이터 적재 파이프라인(`backend/scripts/*`), 백엔드 라우트(`backend/app/`), 프론트 여정·지도 렌더(`frontend/src/`), 인프라(`deploy.sh`, `docker-compose.yml`, `.github/workflows/deploy.yml`, `frontend/vite.config.js`). 본 문서는 구현 사실만 기록하며, 각 항목은 실제 코드로 검증했다.

---

## Operational / Deployment Concerns

### 큐레이션 인물 데이터의 수동 Neo4j 적재 (최상위 운영 리스크)

`deploy.sh`는 데이터 갱신 단계에서 `backend/scripts/inject_ko_names.py` **하나만** 실행한다(`deploy.sh:49-60`). 큐레이션 인물의 여정 사건을 Neo4j에 적재하는 `backend/scripts/load_person_events.py`·`backend/scripts/load_authored_persons.py`·`backend/scripts/load_authored_events.py`·`backend/scripts/enrich_place_coords.py`·`backend/scripts/generate_person_event_verses.py`는 **배포 스크립트에 포함되지 않으며, 호스트에서 사람이 직접 순서대로 실행**해야 한다.

- 검증: `grep "scripts/" deploy.sh` 결과는 `inject_ko_names.py` 단 한 줄. 위 로더 스크립트들은 어떤 자동화 경로에도 없다. `.github/workflows/deploy.yml`도 `bash deploy.sh` 호출 외에 적재 단계가 없다.
- **적재 순서 제약**: `load_authored_persons.py` → `enrich_place_coords.py` → `load_person_events.py` 순서를 지켜야 `HAS_PARTICIPANT` MATCH가 성립한다(ADR-0008). 순서 위반 시 관계가 조용히 누락된다.
- `docker-compose.yml:22`이 `neo4j_data` named volume을 영속화하므로 평시에는 재적재 불필요. 그러나 **볼륨 리셋(`docker compose down -v` 등) 시 22인 전원을 수동 재적재**해야 하며, 이를 명시한 공개 문서가 없다.
- 현재 큐레이션 22인 중 6인(기드온·드보라·입다·삼손·룻·사울)이 authored Person 노드이며, `load_authored_persons.py`로만 Neo4j에 존재한다. Theographic `rec` id가 없어 `load_theographic.py`로 복구되지 않는다.
- API 컨테이너는 `data/`를 마운트(`docker-compose.yml:19`)하지만 적재는 **호스트에서 `bolt://127.0.0.1:7687`로 직접** 수행한다. 컨테이너 내부에서 스크립트를 실행하는 경로는 없다.
- 이 Neo4j 인스턴스는 Cloudflare Tunnel을 통해 프로덕션 앱과 동일 그래프를 공유한다. 호스트 inject/load 스크립트는 곧바로 운영 데이터를 변경한다.
- 파일: `deploy.sh`, `.github/workflows/deploy.yml`, `backend/scripts/load_authored_persons.py`, `backend/scripts/load_person_events.py`

### `deploy.sh`의 한글 이름 주입이 배포 게이트 (부분 적용 위험)

`deploy.sh:50-60`은 `inject_ko_names.py`를 2초 간격 15회까지 재시도하고, 끝까지 실패하면 `exit 1`로 배포를 중단한다. inject는 컨테이너 재시작(`up -d api nginx`, `deploy.sh:46`) **뒤에** 실행되므로, 주입이 실패하면 컨테이너는 이미 새 코드로 떠 있는데 배포 스크립트만 실패로 종료된다(부분 적용 상태).

- 완화: 프론트가 `nameKo || name` 폴백을 쓰므로 주입 실패 시 영문 이름으로라도 노출돼 치명도는 낮다. CI는 실패로 표시된다.
- 파일: `deploy.sh:46-61`

### CI 워크플로가 특정 머신 절대경로에 묶임

`.github/workflows/deploy.yml`이 `runs-on: self-hosted` + `cd /Users/calmonion/Project/BibleMap`로 한 머신의 self-hosted 러너 경로에 하드코딩돼 있고, `git reset --hard origin/main`으로 워크트리의 로컬 변경을 무조건 폐기한다.

- 영향: 러너 머신/경로 변경 또는 러너 오프라인 시 무음 미배포 가능. 현 단일 self-hosted 스택 전제에선 의도된 설계다.
- 파일: `.github/workflows/deploy.yml`

### `lru_cache`가 런타임 데이터 갱신을 가림

`persons.py`·`places.py`·`events.py`·`overlays.py`의 `@functools.lru_cache`는 프로세스 생애 동안 결과를 보관한다. 배포마다 컨테이너를 재기동하므로 배포 단위로는 캐시가 비워지나, 호스트 inject/load 스크립트가 컨테이너 기동 후 Neo4j를 갱신하는 동안에는 캐시가 갱신 전 데이터를 들고 있을 수 있다.

---

## Tech Debt

### 스테일 docstring — `persons.py`·`journey.py`의 "13인" 표기

실제 큐레이션 인물은 22인(`_ERA` 딕트 22개 항목, `data/person_events/` 22개 파일)이지만 두 파일의 docstring에 여전히 "13인"이 기재돼 있다.

- `backend/app/routes/persons.py:1`: `"""큐레이션된 13인 인물 목록 엔드포인트.`
- `backend/app/routes/persons.py:104`: `"""활동범위가 그려지는 큐레이션된 13인 목록.`
- `backend/app/routes/journey.py:6`: `큐레이션 13인이 아니면 빈 stops 반환(404 아님).`
- `backend/app/routes/journey.py:77`: `큐레이션 13인이 아니면 stops=[] 빈 응답 반환.`
- 검증: `grep -n "13인"` 결과 persons.py 2건, journey.py 2건 모두 현재 코드에서 확인.

### 동명이지(同名異地) 재사용 충돌 위험

authored-place를 새 인물 여정에 재사용할 때 영문 지명이 같아도 다른 지점인 경우가 있다. 기드온 추가 시 `authored-place-succoth`(이집트 숙곳, lat 30.56)와 요단 동편 숙곳(lat 32.20)이 충돌해 `authored-place-succoth-jordan`을 별도 신설한 실사례가 있다.

- 현재 authored-place에 동일 영문 이름이 두 개 이상인 것: `Succoth` → `authored-place-succoth`(이집트)/`authored-place-succoth-jordan`(요단).
- 잠재 충돌 후보: `authored-place-mizpah`(베냐민 미스바, lat 31.878) vs `authored-place-mizpah-gilead`(길르앗 미스바, lat 32.05) — 후속 큐레이션에서 "미스바" 검색으로 잘못된 id를 재사용할 수 있다.
- 규칙: 재사용 전 `data/place_coords/places.json`에서 id·좌표를 대조해 의도한 지점인지 확인 필수. 동명이지는 새 id 신설.
- 파일: `data/place_coords/places.json`

### 학자 추정 좌표 — 고고학적 논쟁지

`data/place_coords/places.json`의 다음 항목은 정확한 위치가 학술적으로 확정되지 않은 지점의 근사 좌표다.

| id | 좌표(lat/lng) | 비고 |
|---|---|---|
| `authored-place-mizpah-gilead` | 32.05 / 35.72 | 길르앗 미스바, 추정 지점 |
| `authored-place-aroer` | 31.95 / 35.85 | 암몬 랍바 앞 아로엘, 추정 |
| `authored-place-lehi` | 31.72 / 34.96 | 라맛레히, 추정 |
| `authored-place-timnah` | 31.776 / 34.925 | 삼손 혼인 딤나, 추정 |
| `authored-place-endor` | (places.json 내 항목) | 엔돌, 추정 |
| `authored-place-gilboa` | (places.json 내 항목) | 길보아 산, 추정 |

- 지도에 핀이 찍히므로 이 좌표가 "정확한 성경 유적지"처럼 보일 수 있다.
- 파일: `data/place_coords/places.json`

### 큐레이션 인물 표시 이름의 이중 출처

인물 표시 이름의 출처가 두 곳이다. 프론트 헤더(`App.jsx:82,116,138-141`)는 Neo4j Person 노드의 `nameKo`(inject_ko_names.py 주입값)를, 큐레이션 목록·여정 응답은 `persons.py:36-53`의 하드코딩 `_NAME_KO` 딕트를 출처로 한다. 두 값이 어긋나면 헤더와 목록이 서로 다른 이름을 표시한다. 일치를 강제하는 코드/테스트는 없다.

- 파일: `frontend/src/App.jsx`, `backend/app/routes/persons.py:36-53`, `data/names_ko/people.json`

### 자동화 테스트 전무

프론트·백엔드 모두 테스트 0건. `frontend/package.json` scripts에는 `lint`만 있고 vitest/jest 의존성이 없으며, 백엔드에도 pytest 설정·`test_*.py`가 없다. 좌표 dedup, 순번 압축, 여정 정차지 인덱싱 같은 회귀가 잦은 순수 로직에 안전망이 없고 검증은 수동 Playwright에 의존한다.

- 파일: `frontend/package.json`, `backend/requirements.txt`

---

## Fragile Areas

### `generate_person_event_verses.py`의 정규식 구절 참조 파싱

인물 사건의 `context` 한글 문장에서 **괄호 안 구절 참조를 정규식으로 파싱**해 `books` 필드와 본문을 생성한다. 자유 텍스트를 정규식으로 긁는 구조라 본질적으로 취약하다.

- `parse_context_refs`(`generate_person_event_verses.py:78`)가 `re.findall(r"\(([^)]+)\)", context)`로 괄호 덩어리를 뽑고, `;`로 분리한 뒤 책 약어와 장:절 패턴을 정규식으로 매칭한다. 교차 장 범위(`4:19–5:12`)는 별도 정규식으로 선처리한다.
- 정규식이 인식하지 못하는 표기는 **조용히 매칭 실패** → `continue`로 스킵. 사건에 참조가 하나도 안 잡히면 `books: []`로 저장돼 📖 근거 칩이 비게 된다.
- 같은 권 중복은 "첫 번째만" 채택(`seen_book_ids`)이라, 한 사건이 한 권의 여러 비인접 구간을 참조해도 첫 구간만 본문 fetch된다.
- 교차 장 범위·장만 범위는 "첫 절만 fetch"하는 단순화가 들어가 있어 범위 전체 본문이 들어오지 않는다.
- **빌드타임 외부 의존**: 본문은 `https://api.getbible.net`에서 HTTP fetch한다(`generate_person_event_verses.py:172`, `generate_verse_text.py:80`). 실패 시 `None` 캐싱 후 진행하므로 빌드는 죽지 않지만, 네트워크/외부 API 상태에 따라 일부 절 본문이 조용히 비어 적재될 수 있다. 타임아웃 15초, User-Agent 위장 헤더 사용. 런타임 fetch는 ADR-0003으로 제거돼 있다.
- 파일: `backend/scripts/generate_person_event_verses.py:78-216`, `backend/scripts/generate_verse_text.py`

### 좌표 없는 사건 = place-less 정차지

`journey.py`는 `occursAt[0]`의 Place 노드 좌표를 Neo4j에서 조회하는데, 좌표가 없으면 `seq=null`, `lng/lat=null`인 정차지로 처리한다(`journey.py:101-128`). 의도된 동작이지만, 실제로 일부 큐레이션 사건에 `occursAt: []`인 경우가 있다.

- 검증: `data/person_events/john_the_apostle.json` 4건(첫 제자·보아너게·변형·밧모 섬 등), `data/person_events/peter.json` 4건, `data/person_events/jesus.json` 1건.
- 이 사건들은 여정 지도에 점이 찍히지 않고 리스트/타임라인에서만 보인다.
- 파일: `backend/app/routes/journey.py:101-128`, `data/person_events/john_the_apostle.json`, `backend/scripts/enrich_place_coords.py:32-41`

### `journey.py`가 매 요청마다 JSON 전량 재파싱 (캐시 누락)

`_build_id_to_slug()`(`journey.py:18-30`)는 `/person/{id}/journey` 요청마다 모든 `person_events/*.json`(현재 22개)을 `open`+`json.load`해 theographic_id→slug 역매핑을 새로 만든다. `persons.py`/`places.py`의 동일 파일 로드는 `@functools.lru_cache`로 캐시되는데 `_build_id_to_slug`만 캐시가 없다.

- 개선: `@functools.lru_cache(maxsize=1)` 부착(이미 `persons._build_list`가 같은 패턴).
- 파일: `backend/app/routes/journey.py:18-30`

### 데이터 무결성 가정 — 미강제

`journey.py:19`와 `persons.py:72-81`은 "각 slug json의 첫 사건 `participants[0]`이 그 인물"임을 가정한다(`persons.py:81` 주석 "파일 내 모든 이벤트의 첫 번째 participant가 동일인임을 검증 완료"). 이 불변식을 강제하는 코드/테스트는 없어, 새 인물 JSON에서 `participants[0]`이 다른 인물이면 역매핑이 조용히 틀린다.

- 파일: `backend/app/routes/journey.py:18-30`, `backend/app/routes/persons.py:72-81`

---

## Performance Bottlenecks

### maplibre 번들이 1MB 초과 (빌드 경고)

`npm run build` 결과에서 maplibre 청크가 **1,027.60 kB**(gzip 272.93 kB)로 빌드되며, "Some chunks are larger than 500 kB after minification" 경고가 뜬다.

- `vite.config.js:10-15`의 `manualChunks`가 `maplibre-gl`을 별도 `maplibre` 청크로, 나머지 node_modules를 `vendor`로 분리하고 있으나, maplibre 자체가 단일 청크 1MB를 넘는다.
- 영향: 첫 로드 전송량 증가. 동적 import 코드 스플리팅이나 `chunkSizeWarningLimit` 조정이 개선 경로지만 현재 미적용.
- 파일: `frontend/vite.config.js`

---

## Code Quality

### 표준 lint 경고 1건 — `MapView.jsx` useEffect 누락 의존성

`npm run lint` 결과: 에러 0, **경고 1건**.

```
frontend/src/MapView.jsx
  61:6  warning  React Hook useEffect has a missing dependency: 'onStopSelect'. ...  react-hooks/exhaustive-deps
```

- `eslint .`는 종료코드 0(경고는 빌드를 막지 않음).
- 파일: `frontend/src/MapView.jsx:61`

---

## Security Considerations

### Neo4j는 외부 미노출, API는 nginx 프록시 뒤 (구조적 차단)

- `docker-compose.yml:5-7`이 Neo4j 포트를 `127.0.0.1:7474`/`127.0.0.1:7687`로만 바인딩한다. API 컨테이너는 호스트 포트를 노출하지 않고, nginx만 `8080:80`을 공개한다.
- Cloudflare Tunnel(cloudflared)은 outbound 전용 연결로 Neo4j(7474/7687)는 구조적으로 외부 접근 불가다.

### CORS 전체 허용 + 무인증 (읽기 전용 전제)

- `main.py`의 CORS가 모든 오리진을 허용하고 모든 엔드포인트가 무인증 공개다. 단 `allow_methods=["GET"]`로 GET 전용이고 쓰기 엔드포인트가 없으며 공개 성경 데이터만 다룬다.
- 파일: `backend/app/main.py`, `backend/app/routes/*`

### 비밀값 관리

- `NEO4J_PASSWORD`는 `.env`로만 공급되며 `.gitignore`로 추적 제외된다. `docker-compose.yml:11,18`이 `${NEO4J_PASSWORD:?...}`로 미설정 시 기동 실패를 강제한다.
- 모든 데이터 적재/inject 스크립트는 `NEO4J_PASSWORD` 환경변수를 요구하며 없으면 즉시 중단한다. 평문/하드코딩 비밀값 흔적 없음.
- Cypher 쿼리는 사용자 입력을 `$id`/`$q` 파라미터 바인딩으로 처리해 인젝션 경로가 아니다.

---

*Concerns audit: 2026-07-02 (commit 0189ad9)*
