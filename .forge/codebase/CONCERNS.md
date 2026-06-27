---
last_mapped_commit: 79f9d9df07c0d79f8fa07940e3f76c8d5424524b
mapped: 2026-06-28
---

# Codebase Concerns

**Analysis Date:** 2026-06-28

분석 범위: 프론트(`frontend/src/`)·백엔드(`backend/app/`)·인프라(`docker-compose.yml`·`deploy.sh`·`nginx/nginx.conf`·`.github/workflows/deploy.yml`). 최근 변경이 집중된 지도·여정 렌더 코드(`MapView.jsx`·`mapGeo.js`·`mapLayers.js`·`mapRingController.js`·`JourneyList.jsx`·`backend/app/routes/journey.py`)를 우선 점검했다.

## Known Bugs

**모바일 여정 미니시트의 `activeStopIdx` 의미 불일치:**
- 증상: 데스크톱 `JourneyList`와 지도 배지/활성 강조는 `journeyStopGroups`(좌표 단위 그룹) 기준 인덱스를 쓰는데, 모바일 미니시트만 `seq - 1`(사건 순번 - 1)을 인덱스로 쓴다. 같은 장소에서 여러 사건이 일어나는 인물(예: 아브라함 마므레 사건 6·7·8·10)에서 미니시트 항목을 누르면 다른 정차지가 활성화되거나 활성 강조가 어긋난다.
- 파일: `frontend/src/App.jsx:271-300` (특히 `:272` `stop.seq != null && stop.seq - 1 === activeStopIdx`, `:276` `setActiveStopIdx(stop.seq - 1)`)
- 트리거: 모바일 폭(`MOBILE_BREAKPOINT` 이하)에서 큐레이션 인물 선택 후 하단 미니시트 항목 클릭. 중복 좌표가 있는 인물에서 재현.
- 대조: `frontend/src/MapView.jsx:166-187`(`journeyStopGroups(...)[activeStopIdx]`)·`frontend/src/JourneyList.jsx:31`(`keyToIdx` = deduped 그룹 인덱스)는 그룹 기준. 미니시트만 옛 사건순번 기준이 남아 있음.
- 수정 접근: 미니시트도 `mapGeo.journeyStopGroups(journeyStops)`를 매핑해 그룹 인덱스로 `onStopSelect`를 호출하고, 활성 판정도 그룹 인덱스(`groupIdx === activeStopIdx`)로 바꾼다. `JourneyList`/`MapView`와 동일 헬퍼를 쓰도록 통일.

**`JourneyList`의 dedup 로직 중복 구현:**
- 증상(잠재): `frontend/src/JourneyList.jsx:21-31`이 `mapGeo.journeyStopGroups`와 동일한 좌표 dedup·인덱스 매핑을 손으로 재구현한다. 두 곳의 `coKey`(`${lng},${lat}`) 표기나 그룹핑 규칙이 미래에 한쪽만 바뀌면 리스트와 지도 배지가 다시 어긋난다.
- 파일: `frontend/src/JourneyList.jsx:21-31`, `frontend/src/mapGeo.js:157-180`
- 트리거: 한쪽 헬퍼만 수정 시 침묵 발산.
- 수정 접근: `JourneyList`도 `journeyStopGroups`를 import해 단일 출처로 인덱스를 도출.

## Tech Debt

**큐레이션 13인 매핑 상수 3중 복제:**
- 이슈: `_ERA`/`_NAME_KO`/`_ERA_ORDER`가 `backend/app/routes/persons.py:16-50`과 `backend/app/routes/places.py:16-48`에 통째로 복제돼 있고, 프론트 `frontend/src/PersonHub.jsx:7`(`ERA_ORDER`)에도 한 번 더 있다. `journey.py`는 `from .persons import _ERA, _NAME_KO`로 import하는데 `places.py`만 "단방향 참조 회피"를 이유로 재선언한다(`places.py:15` 주석).
- 파일: `backend/app/routes/persons.py:16-50`, `backend/app/routes/places.py:16-48`, `frontend/src/PersonHub.jsx:7`
- 영향: 인물 추가/시대 라벨 변경 시 3곳을 동기화해야 함. 누락 시 장소→인물 칩이나 허브 정렬이 조용히 어긋남.
- 수정 접근: 백엔드는 한 모듈(예: `persons.py` 또는 별도 `curated.py`)로 단일화하고 `places.py`·`journey.py`가 import. 프론트 `ERA_ORDER`는 백엔드 응답에 era 순서를 실어 보내거나 별도 commit-comment로 동기화 표시.

**여정 정차지 식별이 `${lng},${lat}` 문자열 키에 의존:**
- 이슈: `mapGeo.journeyStopGroups`(`mapGeo.js:159`)와 `JourneyList`(`:22`)·`buildJourneyLineGeoJSON`(`mapGeo.js:108-113`)이 좌표를 raw 부동소수점 그대로 문자열화해 그룹 키로 쓴다. `placesToGeoJSON`(`mapGeo.js:45`)은 `toFixed(4)`로 반올림 키를 쓴다. 좌표 비교 정밀도가 코드 경로마다 다르다.
- 파일: `frontend/src/mapGeo.js:45`(`toFixed(4)`) vs `:108-113`·`:159`(raw `===`)
- 영향: 백엔드가 같은 장소에 미세하게 다른 좌표(예: 동일 Place의 부동소수 표현 차)를 주면 한 경로에선 합쳐지고 다른 경로에선 분리돼 배지/라인이 어긋날 수 있음. 현재는 같은 `journey.py` `_fetch_place_coords`가 동일 Place에 동일 float을 주므로 실질 문제는 낮음.
- 수정 접근: 좌표 dedup 키 정밀도를 한 헬퍼로 통일.

**테스트 부재 — 전 영역:**
- 이슈: 프론트·백엔드 모두 자동화 테스트 0건. `*.test.*`/`*.spec.*`/`test_*.py` 없음, `vitest`/`pytest`/`jest` 설정·의존성 없음(`frontend/package.json` scripts에 `lint`만, `backend/requirements.txt`에 테스트 의존성 없음).
- 파일: `frontend/package.json`, `backend/requirements.txt`
- 영향: 위 여정 인덱스 버그처럼 순수 함수(`mapGeo.js`의 `journeyStopGroups`·`compactSeqs`·`buildJourneyLineGeoJSON`·`coreBounds`)의 회귀를 잡을 안전망이 없음. 검증은 수동 Playwright(메모리 참조)에 의존.
- 수정 접근: 최소한 `mapGeo.js`의 순수 함수에 단위 테스트(vitest) 도입. 백엔드는 `overlays._resolve`·`journey._build_id_to_slug` 등 파일 기반 로직에 pytest.

## Performance Bottlenecks

**`journey.py`가 매 요청마다 13개 JSON을 재파싱:**
- 문제: `_build_id_to_slug()`가 `/person/{id}/journey` 요청마다 13개 `person_events/*.json`을 전부 `open`+`json.load`해 역매핑을 새로 만든다(`journey.py:18-30`). `persons.py`/`places.py`의 동일 파일 로드는 `@functools.lru_cache`로 캐시되는데 `journey.py`만 캐시가 없다.
- 파일: `backend/app/routes/journey.py:18-39, 81`
- 원인: `_build_id_to_slug`·`_load_events`에 캐시 데코레이터 미적용.
- 개선 경로: `_build_id_to_slug`에 `@functools.lru_cache(maxsize=1)` 부착(이미 `persons._build_list`가 같은 패턴). `_load_events`도 slug별 캐시 가능. 응답에 `Cache-Control: max-age=300`은 있으나 서버 측 파싱 비용은 그대로.

**검색 쿼리가 전 노드 풀스캔 + 인덱스 미사용:**
- 문제: `/search`가 `MATCH (n) WHERE n.nameKo CONTAINS $q OR toLower(n.name) CONTAINS toLower($q)`로 라벨·인덱스 없이 전체 노드를 스캔한다(`search.py:14-30`). `main.py` lifespan이 만드는 인덱스는 `theographic_id` range 인덱스뿐(`main.py:13-18`)이라 텍스트 CONTAINS에는 무용.
- 파일: `backend/app/routes/search.py:14-30`, `backend/app/main.py:13-18`
- 원인: 부분일치(CONTAINS)는 range/lookup 인덱스가 못 탄다. 노드 수가 커지면 선형 비용.
- 개선 경로: Neo4j full-text 인덱스(`db.index.fulltext.queryNodes`) 도입 또는 노드 규모가 작음을 전제로 현 상태 유지(성경 데이터 규모상 실질 부담은 제한적일 수 있음 — 측정 후 결정).

## Fragile Areas

**`MapView.jsx`의 자동 펼침 effect — 카메라/AbortController/타이머 다중 상태:**
- 파일: `frontend/src/MapView.jsx:63-152`
- 왜 취약: `moveend` 이벤트 + 폴백 타이머(700ms) + `fired` 플래그 + `AbortController` + `mapRef.current === map` 가드 + `expandedPlaceRef` 선점 판단이 한 effect에 얽혀 있다. 주석(`:98-141`)이 "task 15에서 어긋났던 지점", "radial-ring 회고" 등 과거 회귀를 명시할 만큼 미세 타이밍에 민감.
- 안전한 수정: 카메라 이동/펼침 조건(`primary && expandedPlaceRef.current?.id !== primary.id`)을 건드릴 때 mobile/desktop 패딩 분기·`maxZoom`·`moveEndHandler` 해제 경로를 함께 확인. effect cleanup(`:147-151`)에서 `ctrl.abort()`·`map.off`·`clearTimeout`이 모두 호출되는지 유지.

**`mapRingController.js`의 공유 가변 클로저 상태 + RAF 애니메이션:**
- 파일: `frontend/src/mapRingController.js` 전체(`animFrame`·`spiderAnimFrame`·`expandAbortCtrl`·`spiderState`·`destroyed`)
- 왜 취약: ring/spider 두 애니메이션이 각자 RAF 루프를 돌리며 `event-ring-source`·`place-spider-source`에 `setData`한다. `expandedPlaceRef`는 컴포넌트 ref와 공유(`:10`)되어 `MapView` selection effect와 `registerEventHandlers` 클릭 핸들러가 동시에 읽고 쓴다. `destroyed` 플래그로 unmount 후 setData를 막지만, 동일 source에 두 경로가 동시 `setData`하면 마지막 것이 이긴다(주석에서 "공유 source 동시 setData 충돌 회피"로 명시).
- 안전한 수정: 새 애니메이션 시작 전 반드시 기존 `cancelAnimationFrame` + 이전 `setData(EMPTY_GEOJSON)` 정리 패턴 유지. expand/collapse 추가 시 `expandedPlace.current` 갱신 시점을 RAF 시작과 일치시킬 것.
- 테스트 커버리지: 없음(수동 검증만).

**`mapLayers.js`의 레이어 순서 강제 `moveLayer`:**
- 파일: `frontend/src/mapLayers.js:446-450`
- 왜 취약: 여정 배지 레이어 4개를 `event-ring-shadow` 위로 `moveLayer`로 재배치한다. 레이어 id 문자열이나 추가 순서가 바뀌면 `getLayer(id)` 가드가 빠진 항목은 조용히 z-순서가 틀어진다. 같은 좌표에서 장소 점이 배지를 덮는 회귀(주석에 명시)가 재발할 수 있음.
- 안전한 수정: 레이어 추가/이름 변경 시 `:448` 배열과 `event-ring-shadow` 기준점을 함께 갱신.

**`compactSeqs` 텍스트가 원 배지를 넘침(의도된 트레이드오프):**
- 파일: `frontend/src/mapGeo.js:137-150`, `frontend/src/mapLayers.js:219-240`
- 왜 취약: 다중 순번(예 "6-8, 10")은 원(반경 8~10px)을 넘쳐 지도 위로 흐른다. 가독성은 text-halo로 보완(`mapLayers.js:232-238`)하나, 긴 라벨이 인접 배지·라벨과 겹칠 수 있음(`text-allow-overlap: true`·`text-ignore-placement: true`로 충돌 회피 비활성).
- 안전한 수정: 순번 표기 규칙 변경 시 halo·overlap 설정과 함께 검토.

## Security Considerations

**CORS가 모든 오리진 허용:**
- 위험: `app.add_middleware(CORSMiddleware, allow_origins=["*"], ...)` (`backend/app/main.py:25-31`). GET 전용·credentials 비활성이라 노출면은 좁지만, API가 직접 인터넷에 노출되면 임의 사이트가 데이터를 읽을 수 있음.
- 파일: `backend/app/main.py:25-31`
- 현재 완화: `docker-compose.yml`에서 Neo4j 포트만 `127.0.0.1` 바인딩(`docker-compose.yml:6-8`), API 컨테이너는 호스트 포트 미노출(nginx만 `:8080` 공개), nginx `/api/` 프록시를 통해서만 접근. 즉 실배포에서 API는 내부망 한정.
- 권장: 공개 데이터 읽기 전용이므로 현 상태 수용 가능. 장차 쓰기/인증 추가 시 `allow_origins`를 실제 도메인으로 제한.

**인증·인가 부재(설계상):**
- 위험: 모든 엔드포인트가 무인증 공개. 쓰기 엔드포인트가 없고 공개 성경 데이터만 다루므로 현재 위험은 낮음.
- 파일: `backend/app/routes/*` 전체(`@router.get`만 존재)
- 현재 완화: GET-only(`main.py:29` `allow_methods=["GET"]`), 데이터 변경은 호스트 `inject_*` 스크립트로만(`deploy.sh:55-67`).
- 권장: 읽기 전용 공개 앱이라는 전제를 유지. 변경 시 재평가.

**Cypher 쿼리 — 파라미터 바인딩은 안전, f-string은 상수만:**
- 검토 결과: 사용자 입력(`node_id`·`q`)은 모두 `$id`/`$q` 파라미터 바인딩(`nodes.py`·`search.py`)으로 안전. `search.py:15`·`nodes.py:168-170`의 f-string은 `SEARCH_LIMIT`·`NODE_NEIGHBOR_LIMIT` 등 코드 내 상수만 끼우므로 인젝션 경로 아님. `main.py:16` 인덱스 생성 f-string도 하드코딩 라벨 목록(`['Person',...]`)만 사용.
- 파일: `backend/app/routes/search.py:14-30`, `backend/app/routes/nodes.py:166-172`, `backend/app/main.py:13-18`
- 권장: 향후 동적 라벨/속성을 f-string으로 끼우지 않도록 주의(현재는 문제 없음).

**비밀값 관리:**
- `.env`(`NEO4J_PASSWORD`)는 `.gitignore`에 포함돼 추적 제외(`.gitignore:13`). `deploy.sh:33-35`가 `.env`를 source해 inject 스크립트에 비번 전달. `docker-compose.yml`은 `${NEO4J_PASSWORD:?...}`로 미설정 시 기동 실패하도록 강제(`docker-compose.yml:11,18`). 누출 흔적 없음.

## Operational / Deployment Concerns

**`deploy.sh`의 한글 이름 주입이 배포 게이트(단일 실패점):**
- 문제: `deploy.sh:55-67`이 `inject_ko_names.py`를 15회까지 재시도하고 끝까지 실패하면 `exit 1`로 배포를 중단한다. inject 단계는 컨테이너 재시작(`up -d`) 뒤에 실행되므로, 주입 실패 시 컨테이너는 이미 새 코드로 떠 있는데 배포 스크립트만 실패로 끝난다(부분 적용 상태).
- 파일: `deploy.sh:55-72`
- 영향: 주입 실패 시 한글 이름이 누락된 데이터로 서비스가 떠 있을 수 있음. CI는 실패로 표시되지만 사용자에겐 영문 이름 폴백(`nameKo || name`)으로 노출.
- 개선 접근: inject를 컨테이너 기동 전/헬스 확인 후로 옮기거나, 실패 시 롤백. 단 현재 폴백(`nameKo` 없으면 `name`)이 있어 치명도는 낮음.

**CI 워크플로가 절대경로 하드코딩:**
- 문제: `.github/workflows/deploy.yml`이 `cd /Users/calmonion/Project/BibleMap`로 특정 머신의 self-hosted 러너 경로에 묶여 있다. `git reset --hard origin/main`으로 워크트리 로컬 변경을 무조건 폐기.
- 파일: `.github/workflows/deploy.yml`
- 영향: 러너 머신/경로 변경 시 무음 실패 가능(글로벌 메모리의 "배포 무음 실패 시 러너부터" 주의와 직결). 러너 디스크의 미커밋 변경은 매 배포마다 소실.
- 개선 접근: 현 단일 self-hosted 스택 전제에선 의도된 설계. 경로 의존을 인지하고 러너 격리 규칙(글로벌 CLAUDE.md) 준수.

**`lru_cache`가 데이터 갱신을 가림(런타임 stale):**
- 문제: `events.py`·`persons.py`·`places.py`·`overlays.py`의 `@functools.lru_cache`(`maxsize=1` 또는 `None`)는 프로세스 생애 동안 결과를 보관한다(`events.py:53` `_compute_events`는 Neo4j 쿼리 결과까지 캐시). `data/*.json`이나 Neo4j 데이터가 바뀌어도 API 재시작 전엔 옛 응답을 반환.
- 파일: `backend/app/routes/events.py:11,53,98`, `backend/app/routes/persons.py:53`, `backend/app/routes/places.py:51`, `backend/app/overlays.py:30,36`
- 영향: `deploy.sh`가 매 배포 컨테이너를 `up -d`(재기동)하므로 배포 단위로는 캐시가 비워져 실제 운영 문제는 낮음. 다만 inject 스크립트(`deploy.sh:55`)가 컨테이너 기동 후 Neo4j를 갱신하면, 그 사이 캐시된 `_compute_events`/`_book_name_map`이 갱신 전 데이터를 들고 있을 수 있음.
- 개선 접근: 데이터 갱신이 컨테이너 재시작과 항상 묶이도록 유지하거나(현 상태), 명시적 캐시 무효화 엔드포인트 추가.

## Test Coverage Gaps

**여정/지도 순수 함수 — 무테스트:**
- 미검증: `mapGeo.js`의 `journeyStopGroups`·`compactSeqs`·`buildJourneyLineGeoJSON`·`buildJourneyStopsGeoJSON`·`coreBounds`·`placesToGeoJSON`. 좌표 dedup, 순번 압축("6-8, 10"), 진행도 그라데이션 등 회귀가 잦았던 로직.
- 파일: `frontend/src/mapGeo.js`
- 위험: 위 "모바일 미니시트 인덱스" 버그류가 자동으로 안 잡힘.
- 우선순위: 높음(순수 함수라 테스트 비용 낮고 회귀 빈도 높음).

**백엔드 라우트 — 무테스트:**
- 미검증: `journey._build_id_to_slug`(participants[0] 가정)·`places._place_to_persons`·`nodes.get_node_places`의 라벨 분기·`events._compute_events`의 approx 머지.
- 파일: `backend/app/routes/journey.py`, `backend/app/routes/places.py`, `backend/app/routes/nodes.py`, `backend/app/routes/events.py`
- 위험: 데이터 스키마 가정(`events[0]["participants"][0]`이 항상 그 인물, `occursAt[0]`이 대표 장소)이 깨지면 침묵 오류.
- 우선순위: 중간.

**데이터 무결성 가정 — 미검증:**
- 미검증: `journey.py:28`은 "각 slug json의 첫 participants[0]이 그 인물"임을, `persons.py:63` 주석은 "파일 내 모든 이벤트의 첫 participant가 동일인임을 검증 완료"라고 가정한다. 이 불변식을 강제하는 코드/테스트는 없다.
- 파일: `backend/app/routes/journey.py:18-30`, `backend/app/routes/persons.py:53-76`, `data/person_events/*.json`
- 위험: 새 인물 JSON 추가 시 participants[0]이 다른 인물이면 매핑이 조용히 틀림.
- 우선순위: 중간(데이터 추가 시점에 검증 스크립트 권장).

---

*Concerns audit: 2026-06-28*
