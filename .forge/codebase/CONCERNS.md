---
last_mapped_commit: d0eab1289792c4e191cce498fb574aa2a4f7e300
mapped: 2026-07-03
---

# CONCERNS — 기술 부채·알려진 버그·보안·성능 위험

분석 범위: `frontend/src/`, `backend/app/`, `backend/scripts/`, `docker-compose.yml`, `nginx/nginx.conf`. 본 문서는 구현 사실만 기록하며, 각 항목은 실제 코드로 검증했다.

---

## 운영·배포 위험

### 큐레이션 인물 데이터 적재 — 수동 전용, 자동화 없음 (최상위 운영 리스크)

`deploy.sh`의 데이터 갱신 단계는 `inject_ko_names.py` 하나만 실행한다. 큐레이션 인물 여정을 Neo4j에 적재하는 `load_person_events.py`, `load_authored_persons.py`, `load_authored_events.py`, `enrich_place_coords.py`, `generate_person_event_verses.py`는 배포 자동화에 포함되지 않으며 호스트에서 사람이 순서대로 직접 실행해야 한다.

- 적재 순서 제약: `load_authored_persons.py` → `enrich_place_coords.py` → `load_person_events.py`. 순서 위반 시 `HAS_PARTICIPANT` 관계가 조용히 누락된다. `load_authored_persons.py` docstring 줄 7–8에 명시된 제약이나, 강제하는 코드가 없다.
- `docker-compose.yml:22` `neo4j_data` 볼륨 리셋(`docker compose down -v`) 시 28인 전원을 수동 재적재해야 하며 이를 명시한 공개 런북이 없다.
- 현재 큐레이션 28인 중 기드온·드보라·입다·삼손·룻·사울 등 authored Person 노드는 `load_authored_persons.py`로만 존재하며, `load_theographic.py`로 복구되지 않는다.
- 파일: `backend/scripts/load_authored_persons.py`, `backend/scripts/load_person_events.py`, `deploy.sh`

### 빌드·데이터 파이프라인 시점의 외부 API 의존

`backend/scripts/load_theographic.py` 줄 13–18: DB 초기 구축 시 GitHub Raw URL 4개(people, places, events, peopleGroups)에서 실시간 fetch한다. GitHub 다운·레포 삭제·브랜치 이동 시 DB를 재구축할 수 없다. 버전 고정(태그·커밋 해시 고정)이 없어 upstream 데이터 변경을 탐지할 수단이 없다.

`backend/scripts/generate_event_verses.py` 줄 28–29: 약 15 MB짜리 `events.json`·`verses.json`을 빌드마다 GitHub Raw에서 fetch한다. 로컬 캐시 없음.

`backend/scripts/generate_verse_text.py` 줄 80: `https://api.getbible.net/v2/{slug}/{book_order}/{chapter}.json` — 성경 절 본문 fetch. 줄 91–93에서 `except Exception: return None`으로 실패를 묵인한다. 장애 지속 시 절 본문이 영구 누락된다(§ 무음 실패 참조).

### `deploy.sh` — 한글 이름 주입 실패 시 부분 적용 상태

`deploy.sh`는 컨테이너 재기동(`up -d api nginx`) 뒤에 `inject_ko_names.py`를 2초 간격 15회까지 재시도하고(`deploy.sh` 줄 50–57) 끝까지 실패하면 `exit 1`로 종료한다. 컨테이너는 이미 새 코드로 떠 있는데 배포 스크립트만 실패로 끝나는 부분 적용 상태가 가능하다.

`deploy.sh` 줄 51: `2>/dev/null`로 stderr를 버려 실패 원인 진단이 어렵다.

- 완화: 프론트가 `nameKo || name` 폴백을 사용하므로 주입 실패 시 영문 이름으로 노출되어 치명도는 낮다.
- 파일: `deploy.sh`

### `lru_cache` — 런타임 데이터 갱신 감지 불가

`persons.py`, `places.py`, `events.py`, `overlays.py`의 `@functools.lru_cache`는 프로세스 생애 동안 결과를 보관한다. 호스트 inject/load 스크립트가 컨테이너 기동 후 Neo4j를 갱신하면, 캐시가 갱신 전 데이터를 들고 있는 시간 창이 생긴다. 배포마다 컨테이너를 재기동하므로 정상 배포 흐름에서는 문제없음. 그러나 핫패치성 데이터 수정 후 컨테이너 재시작을 빠뜨리면 갱신이 반영되지 않는다. 캐시 무효화 엔드포인트 없음.

- 파일: `backend/app/routes/events.py:11,53`, `backend/app/routes/persons.py:83`, `backend/app/routes/places.py:18`, `backend/app/overlays.py:30,36`

---

## 코드 품질 · 기술 부채

### ESLint 경고 1건: `MapView.jsx` `useEffect` 누락 의존성 `onStopSelect`

`npm run lint` 결과 에러 0, 경고 1건 (2026-07-03 재확인 — 신규 훅 추가에도 경고 증가 없음):

```
frontend/src/MapView.jsx
  61:6  warning  React Hook useEffect has a missing dependency: 'onStopSelect'.  react-hooks/exhaustive-deps
```

- `useEffect(() => { ... }, [onSelectNode])` — deps 배열에 `onStopSelect`(= `onJourneyStopClick` 전달 경로)가 빠져 있다.
- 현재 `onStopSelect`는 App에서 `setActiveStopIdx`(stable setter)를 직접 전달하므로 stale-closure 버그는 발생하지 않는다. 단, deps 배열이 의도와 다르게 기록되어 향후 리팩토링 시 함정이 된다.
- 파일: `frontend/src/MapView.jsx:61`

### 스테일 docstring — `persons.py`·`journey.py`의 "13인" 표기

실제 큐레이션 인물은 28인(`_ERA` 딕트 28개 항목, `data/person_events/` 28개 파일)이지만 두 파일 docstring에 여전히 "13인"이 기재되어 있다.

- `backend/app/routes/persons.py:1`: "큐레이션된 13인 인물 목록 엔드포인트"
- `backend/app/routes/journey.py:6,77`: "큐레이션 13인이 아니면 빈 stops 반환"
- 파일: `backend/app/routes/persons.py:1`, `backend/app/routes/journey.py:6,77`

### 이중 등록 패턴 — 새 인물 추가 시 최소 4곳 수정 필요

큐레이션 인물을 추가하면 최소 4곳을 동기화해야 한다.

| 위치 | 내용 |
|---|---|
| `persons.py` 줄 16–45 `_ERA` 딕트 | slug → era 매핑 |
| `persons.py` 줄 48–77 `_NAME_KO` 딕트 | slug → 한글 이름 |
| `data/names_ko/people.json` | `inject_ko_names.py`가 Neo4j에 주입하는 원본 |
| `data/person_events/<slug>.json` | 여정 사건 파일 신규 생성 |

`_ERA`·`_NAME_KO`의 일치 여부를 강제하는 코드가 없다. `persons.py` 줄 98에서 `_NAME_KO[slug]`를 직접 인덱싱하므로, `_ERA`에는 있고 `_NAME_KO`에 없는 slug가 들어오면 `KeyError`가 발생해 `/persons` 엔드포인트 전체가 500을 반환한다. `journey.py` 줄 133도 동일한 직접 인덱싱.

`places.py` 줄 13은 `persons.py`에서 `_ERA`, `_NAME_KO`, `_ERA_ORDER`를 import해 단일 출처를 유지하므로 이 세 파일 간의 드리프트는 방지된다.

- 파일: `backend/app/routes/persons.py:16-77`, `backend/app/routes/journey.py:133`, `data/names_ko/people.json`

### 큐레이션 인물 표시 이름 이중 출처

인물 표시 이름의 출처가 두 곳이다. 프론트 탐험 헤더(`App.jsx:93,132`)는 Neo4j Person 노드의 `nameKo`(inject_ko_names.py 주입값)를, 큐레이션 목록·여정 응답은 `persons.py:48-77`의 하드코딩 `_NAME_KO` 딕트를 사용한다. 두 값이 어긋나면 헤더와 목록이 서로 다른 이름을 표시한다. 일치를 강제하는 코드·테스트가 없다.

- 파일: `frontend/src/App.jsx`, `backend/app/routes/persons.py:48-77`, `data/names_ko/people.json`

### startDate 연도 파싱 로직 이중 구현 — 백엔드·프론트 독립 복제

`startDate`("-4003", "-1451-01", "30" 형식 혼재 문자열)에서 연도를 뽑는 파싱이 두 곳에 독립 구현되어 있다.

- `backend/app/routes/nodes.py:238-247`: Book 상세 `topEvents` 연대 정렬용 로컬 함수 `_year()` — 접두 `-` 판정 후 첫 `-` 분절을 int 파싱, 실패 시 `None`.
- `frontend/src/TimelineView.jsx:19-26`: 타임라인 연도 라벨용 `parseYear()` — 동일한 접두 `-` 판정 + 분절 파싱.

같은 형식 규약을 두 언어로 복제한 상태라, startDate 형식이 추가·변경되면 두 곳을 함께 고쳐야 하고 한쪽만 고치면 정렬과 라벨이 어긋난다. 공유 계약(문서·테스트) 없음.

- 파일: `backend/app/routes/nodes.py:238-247`, `frontend/src/TimelineView.jsx:19-26`

### `SidePanel.jsx` Book 기본 펼침 — 섹션 키 8개 하드코딩 동기화 부담

Book 노드 로드 시 전 섹션 기본 펼침을 위해 `SidePanel.jsx:66-71`에서 섹션 키 8개(`book-central`, `book-themes`, `book-keyverse`, `book-background`, `book-structure`, `book-keyppl`, `book-persons`, `book-events`)를 `false`(펼침)로 수동 나열한다. 섹션 렌더 측(`collapsed[key] === false`일 때만 표시)과 이 딕트가 별도 위치라, 새 Book 섹션을 추가하면서 딕트 갱신을 빠뜨리면 그 섹션만 조용히 기본 접힘이 된다. 현재는 8개 키가 렌더 측과 정확히 일치함을 확인했다.

- 파일: `frontend/src/SidePanel.jsx:66-71,345-464`

### 자동화 테스트 전무

프론트·백엔드 모두 테스트 0건. `frontend/package.json`의 scripts에는 `lint`만 있고 vitest/jest 의존성이 없다. 백엔드에도 pytest 설정·`test_*.py`가 없다. 회귀가 잦은 순수 로직에 안전망이 없으며 검증은 수동 Playwright에 의존한다.

테스트 없는 주요 로직:

| 파일 | 미검증 함수 |
|---|---|
| `frontend/src/mapGeo.js` | `coreBounds()`, `compactSeqs()`, `journeyStopGroups()`, `buildJourneyLineGeoJSON()` |
| `backend/scripts/generate_event_verses.py` | `build_range_label()`, `parse_verse()` |
| `backend/scripts/generate_person_event_verses.py` | `parse_context_refs()` |
| `backend/app/routes/persons.py` | `_build_list()` 정렬 로직 |
| `backend/app/routes/nodes.py` | `_year()` startDate 연도 파싱·정렬 |

- 파일: `frontend/package.json`, `backend/requirements.txt`

### 인라인 스타일 색상값 분산 (유지보수 부채)

`SidePanel.jsx`, `App.jsx`, `PersonHub.jsx`, `TimelineView.jsx`, `mapLayers.js` 등 대부분 컴포넌트가 `#1a1a2e`, `rgba(255,255,255,0.07)` 등 동일 색상값을 파일별 리터럴로 반복 선언한다. `theme.js`에 `TYPE_COLOR`, `SELECT_HL`이 있으나 레이아웃·배경 상수는 각 파일에 분산되어 있다. 기능 영향 없음; 색상 일괄 변경 시 다수 파일을 수정해야 하는 유지보수 비용.

---

## 취약 영역 (Fragile Areas)

### `activeStopIdx` 인덱스 의미론 — 지도 마커 클릭 vs. JourneyList 불일치 가능성

`activeStopIdx`는 **deduplicated 장소 그룹 인덱스**(동일 좌표를 첫 등장 순으로 묶은 0-based 인덱스)다. 그런데 지도 마커 클릭 핸들러(`mapLayers.js:123`)는 `onJourneyStopClick(seq - 1)`로 전달하며, `seq`는 좌표 있는 stop에만 1-based로 순차 부여된 원본 번호다.

- `seq - 1`이 dedupIdx와 일치하는 것은 "좌표 있는 stop을 첫 등장 순으로 세면 같다"는 암묵적 전제에 의존한다.
- 동일 장소 재방문(좌표 중복) stop이 있으면 seq 기반 0-based가 dedupIdx와 달라진다. 예: A(lng1)→B(lng2)→A(lng1) 순서면 dedupIdx(A=0,B=1)와 세 번째 stop의 seq 기반 인덱스(=2)가 다르다.
- 현재 큐레이션 데이터에서 이 케이스가 실제 발생하는지 검증되지 않았다. 잠재적 버그 경로다.
- 파일: `frontend/src/mapLayers.js:123`, `frontend/src/mapGeo.js:157-179`, `frontend/src/JourneyList.jsx:54-67`

### Book 상세 `topEvents`·`topPersons` — 데이터 값 의존 필터·정렬

`backend/app/routes/nodes.py`의 Book 상세 응답 구성에 데이터 값에 결합된 하드코딩이 두 건 있다.

- `nodes.py:206`: `WHERE ... AND p.name <> 'God'` — 주요 인물 랭킹에서 God을 문자열 리터럴 일치로 제외한다. upstream 데이터의 `name` 값이 바뀌면(표기 변경 등) 필터가 조용히 무력화된다.
- `nodes.py:218-249`: `topEvents`는 Cypher에서 LIMIT 없이 해당 책의 사건을 전부 가져와 Python `_year()`로 연대 파싱 후 정렬·상위 10개 절단한다(문자열 사전순 정렬의 BC 역전 방지 — 의도된 설계). 파싱 실패(`None`) 사건은 튜플 키로 맨 뒤에 밀리며 경고가 없다. 데이터 규모(책당 사건 수십 건)에선 전량 fetch 부담은 무시 가능.
- 파일: `backend/app/routes/nodes.py:206,218-249`

### `SidePanel.jsx` 주요 사건 BC/AD 라벨 — 문자열 숫자 강제변환 의존

`SidePanel.jsx:481`: `e.startDate < 0 ? BC ${Math.abs(e.startDate)} : AD ${e.startDate}` — `startDate`는 문자열이다. `"-4003" < 0`은 숫자 강제변환으로 동작하지만, 월 접미 형식 `"-1451-01"`은 `Number()` 변환이 `NaN`이 되어 `NaN < 0 === false` → **"AD -1451-01"로 오표시**된다. `nodes.py:236` 주석이 명시하듯 월 접미 형식이 실데이터에 존재하므로, 해당 사건이 topEvents 상위 10에 들면 실제 노출되는 표시 버그 경로다. `TimelineView.jsx`의 `parseYear()`는 이 케이스를 올바르게 처리한다 — 재사용하지 않고 별도 인라인 비교를 쓴 것이 원인.

- 파일: `frontend/src/SidePanel.jsx:479-481`, `backend/app/routes/nodes.py:236`

### `BibleOverviewView.jsx` 점프 내비 — sticky 칩 바 높이와 하드코딩 오프셋 결합

장르 점프 내비의 두 오프셋이 sticky 칩 바의 실제 렌더 높이(padding 10px×2 + 칩 높이 + border ≈ 55px)와 별도로 하드코딩되어 있다.

- `BibleOverviewView.jsx:156`: 스크롤 추적 임계 `top - rootTop <= 64` — 칩 바 아래 64px 기준으로 활성 장르 판정.
- `BibleOverviewView.jsx:176`: 점프 목표 위치 `... - 56` — 칩 바 높이만큼 내려 앉히는 보정.
- 칩 바 높이가 변하면(폰트·패딩 조정, 칩 줄바꿈 발생 등) 점프 착지 위치와 활성 칩 추적이 어긋난다. 두 상수와 칩 바 스타일(`BibleOverviewView.jsx:247-254`)을 함께 고쳐야 한다는 연결이 코드에 없다.
- 스크롤마다 `querySelectorAll('[data-genre]')` 전수 순회(섹션 10개)로 현재 데이터 규모에선 성능 영향 없음.
- 파일: `frontend/src/BibleOverviewView.jsx:150-177,246-254`

### 모바일 읽기 모드: 지도 노출 영역 탭 캐처 크기 협소

`App.jsx:286`: `readingEventId`가 열릴 때 투명 탭 캐처를 `{ top:0, left:0, right:0, bottom:'90dvh', zIndex:4 }`로 배치한다. 레이아웃은 전체 100dvh 중 상단 nav(48px) 아래 나머지를 지도+오버레이 영역으로 사용하므로, 탭 캐처 실제 높이는 `(100dvh - 48px) - 90dvh ≈ 10dvh - 48px`(기기 높이 약 10% 미만)이다.

- 탭 캐처가 동작은 하나 탭 가능 영역이 매우 좁다. 주 닫기 경로는 오버레이 내 ▾ 버튼이다.
- SidePanel 하단 시트(`zIndex:10`)와 JourneyList 오버레이(`zIndex:5`)가 동시에 표시될 때 탭 캐처(`zIndex:4`)가 SidePanel 아래에 가려 지도 탭 닫기 동작이 작동하지 않을 수 있다.
- 파일: `frontend/src/App.jsx:286`

### `generate_person_event_verses.py` — 자유 텍스트 정규식 파싱

인물 사건의 `context` 한글 문장에서 괄호 안 구절 참조를 정규식으로 파싱해 `books` 필드와 본문을 생성한다.

- `parse_context_refs`(`generate_person_event_verses.py:78`)가 `re.findall(r"\(([^)]+)\)", context)`로 괄호 덩어리를 뽑고 책 약어와 장:절 패턴을 매칭한다.
- 정규식이 인식하지 못하는 표기(약어 불일치·비표준 범위 표기)는 줄 99–100에서 조용히 `continue`로 스킵된다. 사건에 참조가 하나도 안 잡히면 `books: []`로 저장돼 📖 근거 칩이 비게 된다. 경고·로그 없음.
- 같은 권 중복은 첫 번째만 채택(`seen_book_ids`)이라 한 사건이 한 권의 여러 비인접 구간을 참조해도 첫 구간만 본문 fetch된다.
- 빌드타임 외부 의존: 본문은 `https://api.getbible.net`에서 HTTP fetch한다. 실패 시 `None` 캐싱 후 진행하므로 빌드는 죽지 않지만 일부 절 본문이 조용히 비어 적재될 수 있다.
- 파일: `backend/scripts/generate_person_event_verses.py:78-216`, `backend/scripts/generate_verse_text.py:80-93`

### 지도 fitBounds outlier 처리 — 엣지 케이스

`frontend/src/mapGeo.js` 줄 5–15의 `coreBounds()`:

- `places.length < 4`이면 outlier 제외 없이 전체 bounds 사용. 마커 3개 이하인 인물은 항상 전체 bounds.
- `medD * 3` 임계값이 하드코딩. 장소가 크게 분산된 경우 중앙 클러스터 내 장소가 잘려나갈 수 있다.
- `null` 반환 케이스가 3가지(places<4, medD<0.01, 제외 없음)여서 호출 측의 폴백 동작을 예측하기 어렵다.

`MapView.jsx` 줄 139: `map.fitBounds(coreBounds(places) || bounds, ...)`.

- 파일: `frontend/src/mapGeo.js:5-15`, `frontend/src/MapView.jsx:139`

### 좌표 없는 사건 = 지도에 안 찍히는 정차지

`journey.py`는 `occursAt[0]`의 Place 노드 좌표를 Neo4j에서 조회하는데, 좌표가 없거나 `occursAt: []`이면 `seq=null, lng/lat=null`인 정차지로 처리한다(`journey.py:101-128`). 의도된 동작이지만, 일부 큐레이션 사건에 실제로 `occursAt: []`인 케이스가 있다.

- `data/person_events/john_the_apostle.json`, `data/person_events/peter.json`, `data/person_events/jesus.json` 등에 좌표 없는 stop이 존재한다.
- 이 사건들은 지도에 점이 찍히지 않고 리스트·타임라인에서만 보인다.
- 파일: `backend/app/routes/journey.py:101-128`

---

## 무음 실패 지점

### `/persons/curated` fetch 실패 시 여정 탐험 CTA 전체 미노출 — 무경고

`App.jsx:41-46`: 앱 마운트 시 `/persons/curated`를 1회 fetch해 `curatedIds` Set을 만들고, SidePanel의 "여정 탐험" CTA는 `curatedIds?.has(node.id)`(`SidePanel.jsx:254`)일 때만 렌더된다. fetch 실패는 `.catch(() => {})`로 삼켜져 `curatedIds`가 `null`로 남고, **모든 인물에서 CTA가 조용히 사라진다**. 에러 표시·재시도·로그 없음. 나머지 화면은 정상 동작하므로 회귀를 눈치채기 어렵다.

- 파일: `frontend/src/App.jsx:41-46`, `frontend/src/SidePanel.jsx:254`

### `_build_id_to_slug()` — 요청마다 JSON 전량 재파싱 (캐시 누락)

`backend/app/routes/journey.py:18-30`의 `_build_id_to_slug()`는 `/person/{id}/journey` 요청마다 모든 `person_events/*.json`(현재 28개)을 `open`+`json.load`해 역매핑을 새로 만든다. `persons.py`·`places.py`의 동일 파일 로드는 `@functools.lru_cache`로 캐시되는데 이 함수만 누락되어 있다.

- 개선: `@functools.lru_cache(maxsize=1)` 부착으로 즉시 해결 가능.
- 파일: `backend/app/routes/journey.py:18-30`

### `places.py` `_place_to_persons` — `maxsize=None` 무한 캐시

`backend/app/routes/places.py:18`: `@functools.lru_cache(maxsize=None)`. `place_id` 문자열을 키로 사용하며 고유 장소 ID 수만큼 캐시가 무한 증가 가능하다. 각 값은 작은 dict 리스트이므로 현재 데이터 규모에서는 문제없지만 명시적 상한(`maxsize=512` 등)이 더 방어적이다.

- 파일: `backend/app/routes/places.py:18`

### `overlays.py` JSON 파싱 실패 — 로그 없이 빈 dict 반환

`backend/app/overlays.py` 줄 26–27: `except json.JSONDecodeError: return {}`. JSON 파일 손상 시 로그 없이 빈 dict 반환. 런타임에서 오버레이 전체(이벤트 구절 뷰, book 칩)가 빈 채 서빙된다.

- 파일: `backend/app/overlays.py:26-27`

### 앱 시작 시 인덱스 생성 실패 무시

`backend/app/main.py` 줄 19–20: 인덱스 생성 실패를 로그만 남기고 앱이 정상 기동된다. 인덱스 없이 전체 노드 스캔으로 동작한다.

- 파일: `backend/app/main.py:19-20`

### journey.py occursAt MATCH 실패 — 경고 없음

`backend/app/routes/journey.py` 줄 53–69의 `_fetch_place_coords()`: MATCH 결과에 없는 place_id는 `coords` dict에 항목이 없다. 줄 104–116에서 `place_info is None`이면 `seq = None`으로 정차지가 좌표 없이 기록되며 경고가 없다. 잘못된 occursAt ID를 입력했을 때 실패를 탐지할 수단이 없다.

- 파일: `backend/app/routes/journey.py:53-69,104-116`

---

## 수동 ID·좌표 입력 위험

### Theographic ID 수동 입력

`data/person_events/<slug>.json`의 `occursAt` 배열(예: `"recgQtoCtBjbsPwAw"`)과 `participants` 배열은 Theographic 레코드 ID를 수동으로 입력한다. 잘못된 ID를 입력하면 `load_person_events.py` 줄 53–58의 `MATCH (p:Place {theographic_id: $place_id})`가 매칭되지 않아 `OCCURS_AT` 관계가 조용히 누락된다. 검증 수단 없음.

`data/authored_events/events.json`도 동일 패턴. `load_authored_events.py`의 MATCH 실패 시 관계 미생성.

- 파일: `data/person_events/`, `data/authored_events/`, `backend/scripts/load_person_events.py:50-58`

### 좌표 수동 입력

`data/place_coords/places.json`에 위도·경도가 수동 하드코딩돼 있다. 좌표 정확도 검증 수단이 없다. `enrich_place_coords.py` 재실행 시 기존 좌표가 덮어써진다.

- 파일: `data/place_coords/places.json`, `backend/scripts/enrich_place_coords.py`

### 동명이지(同名異地) 재사용 충돌 위험

authored-place를 새 인물 여정에 재사용할 때 영문 지명이 같아도 다른 지점인 경우가 있다. `authored-place-succoth`(이집트 숙곳)와 요단 동편 숙곳이 충돌해 `authored-place-succoth-jordan`을 별도 신설한 실사례가 있다.

- 잠재 충돌 후보: `authored-place-mizpah`(베냐민 미스바) vs `authored-place-mizpah-gilead`(길르앗 미스바) — 후속 큐레이션에서 "미스바" 검색으로 잘못된 id를 재사용할 수 있다.
- 규칙: 재사용 전 `data/place_coords/places.json`에서 id·좌표를 대조해 의도한 지점인지 확인 필수.
- 파일: `data/place_coords/places.json`

### 데이터 무결성 가정 — 미강제

`journey.py:18-30`과 `persons.py:83-94`는 "각 slug json의 첫 사건 `participants[0]`이 그 인물"임을 가정한다. 이 불변식을 강제하는 코드·테스트가 없다. 새 인물 JSON에서 `participants[0]`이 다른 인물이면 역매핑이 조용히 틀린다.

- 파일: `backend/app/routes/journey.py:18-30`, `backend/app/routes/persons.py:83-94`

---

## 성능 위험

### maplibre 번들 1.0 MB — Vite 500 kB 초과 경고

`frontend/dist/assets/maplibre-DntM08T7.js`가 **1.0 MB**(gzip ~273 kB). Vite 빌드 시 "Some chunks are larger than 500 kB after minification" 경고가 발생한다. `vite.config.js`의 `manualChunks`로 maplibre를 별도 청크로 분리했지만 라이브러리 자체 크기다. 동적 import 코드 스플리팅이나 라이브러리 교체 없이는 개선 불가하다.

- 파일: `frontend/vite.config.js`, `frontend/dist/assets/`

### ESRI 타일 서버 + Protomaps 글리프 — 외부 의존

`frontend/src/MapView.jsx:32-35`: `https://server.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}` (ESRI 타일), `MapView.jsx:28`: `https://protomaps.github.io/basemaps-assets/fonts/...` (글리프 서버). 두 외부 서버 모두 SLA 없이 의존한다. ESRI 무료 타일은 사용 정책 위반 시 접근 차단 가능. 오프라인·폐쇄망 배포 시 지도가 전혀 표시되지 않는다.

- 파일: `frontend/src/MapView.jsx:22-40`

---

## 보안 고려사항

### XSS 표면: `setHTML` 사용 — 현재 `escapeHtml`로 완화됨

`frontend/src/mapLayers.js:58,83`: `.setHTML(placePopupHTML(label, isPrimary))` — `label`은 Neo4j에서 조회한 장소 이름이다. `escapeHtml(s)` 함수(L5-7)가 `&`, `<`, `>`, `"`, `'`를 이스케이프하므로 현재는 XSS가 불가능하다. 그러나 향후 팝업 HTML에 다른 필드(예: `properties.background`)를 직접 주입할 때 `escapeHtml` 호출을 빠뜨리기 쉬운 고위험 패턴이다.

- 파일: `frontend/src/mapLayers.js:5-29,58,83`

### CORS `allow_origins=["*"]` — 전 도메인 허용

`backend/app/main.py:25-31`: `CORSMiddleware(allow_origins=["*"], allow_credentials=False, allow_methods=["GET"])`. GET-only + `allow_credentials=False` 조합이므로 실질적 인증 우회 위험은 없다. 유료 서비스 전환 또는 내부 서비스화 시 화이트리스트로 교체해야 하는 기술 부채다.

- 파일: `backend/app/main.py:25-31`

### Cypher 쿼리 f-string 인터폴레이션 — 상수 한정, 현재 안전

`backend/app/routes/nodes.py:169`: f-string으로 `{NODE_NEIGHBOR_LIMIT}` 상수를 쿼리에 삽입. `backend/app/routes/search.py:15,27`: `LIMIT {SEARCH_LIMIT}` 상수 삽입. 두 경우 모두 Python int 상수를 삽입하므로 실질적 인젝션 위험은 없다. 그러나 패턴 자체가 향후 사용자 입력 변수를 실수로 f-string에 넣을 위험 경로를 열어 둔다. Cypher 파라미터(`$param`)로 교체하는 것이 더 안전한 패턴이다.

- 파일: `backend/app/routes/nodes.py:169`, `backend/app/routes/search.py:15,27`

### Neo4j 비밀번호 — 환경변수 단일 의존, 현재 구조는 적절

`backend/app/db.py:11`: `os.environ.get("NEO4J_PASSWORD")`; 없으면 `RuntimeError`. `docker-compose.yml:11,18`: `${NEO4J_PASSWORD:?must be set}`로 미설정 시 compose 실행 자체가 실패한다. `.env`는 `.gitignore`에 포함되어 있다. nginx 루트는 `frontend/dist`이고 `.env`는 그 위 디렉터리이므로 현재는 노출 위험 없음. 단, `.env`의 `NEO4J_PASSWORD` 값이 단순한 사전식 값이므로 프로덕션 배포 전 변경이 필요하다.

- 파일: `backend/app/db.py`, `docker-compose.yml`, `.gitignore`, `.env`

---

*CONCERNS audit: 2026-07-03 (HEAD d0eab1289792c4e191cce498fb574aa2a4f7e300)*
