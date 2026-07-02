---
last_mapped_commit: 689126abab88e741263d1d9a4a73d81b2be617d9
mapped: 2026-07-02
---

# CONCERNS — 기술 부채·알려진 버그·보안·성능 위험

분석 범위: `frontend/src/`, `backend/app/`, `backend/scripts/`, `docker-compose.yml`, `nginx/nginx.conf`. 본 문서는 구현 사실만 기록하며, 각 항목은 실제 코드로 검증했다.

---

## 운영·배포 위험

### 큐레이션 인물 데이터 적재 — 수동 전용, 자동화 없음 (최상위 운영 리스크)

`deploy.sh`의 데이터 갱신 단계는 `inject_ko_names.py` 하나만 실행한다. 큐레이션 인물 여정을 Neo4j에 적재하는 `load_person_events.py`, `load_authored_persons.py`, `load_authored_events.py`, `enrich_place_coords.py`, `generate_person_event_verses.py`는 배포 자동화에 포함되지 않으며 호스트에서 사람이 순서대로 직접 실행해야 한다.

- 적재 순서 제약: `load_authored_persons.py` → `enrich_place_coords.py` → `load_person_events.py`. 순서 위반 시 `HAS_PARTICIPANT` 관계가 조용히 누락된다(ADR-0008).
- `docker-compose.yml:22` `neo4j_data` 볼륨 리셋(`docker compose down -v`) 시 22인 전원을 수동 재적재해야 하며 이를 명시한 공개 런북이 없다.
- 현재 큐레이션 22인 중 기드온·드보라·입다·삼손·룻·사울 등 authored Person 노드는 `load_authored_persons.py`로만 존재하며, `load_theographic.py`로 복구되지 않는다.
- 파일: `backend/scripts/load_authored_persons.py`, `backend/scripts/load_person_events.py`, `deploy.sh`

### `deploy.sh` — 한글 이름 주입 실패 시 부분 적용 상태

`deploy.sh`는 컨테이너 재기동(`up -d api nginx`) 뒤에 `inject_ko_names.py`를 2초 간격 15회까지 재시도하고 끝까지 실패하면 `exit 1`로 종료한다. 컨테이너는 이미 새 코드로 떠 있는데 배포 스크립트만 실패로 끝나는 부분 적용 상태가 가능하다.

- 완화: 프론트가 `nameKo || name` 폴백을 사용하므로 주입 실패 시 영문 이름으로 노출되어 치명도는 낮다.
- 파일: `deploy.sh`

### `lru_cache` — 런타임 데이터 갱신 감지 불가

`persons.py`, `places.py`, `events.py`, `overlays.py`의 `@functools.lru_cache`는 프로세스 생애 동안 결과를 보관한다. 호스트 inject/load 스크립트가 컨테이너 기동 후 Neo4j를 갱신하면, 캐시가 갱신 전 데이터를 들고 있는 시간 창이 생긴다. 배포마다 컨테이너를 재기동하므로 정상 배포 흐름에서는 문제없음. 그러나 핫패치성 데이터 수정 후 컨테이너 재시작을 빠뜨리면 갱신이 반영되지 않는다.

- 파일: `backend/app/routes/events.py:11,53,98`, `backend/app/routes/persons.py:75`, `backend/app/routes/places.py:18`, `backend/app/overlays.py:30,36`

---

## 코드 품질 · 기술 부채

### ESLint 경고 1건: `MapView.jsx` `useEffect` 누락 의존성 `onStopSelect`

`npm run lint` 결과 에러 0, 경고 1건:

```
frontend/src/MapView.jsx
  61:6  warning  React Hook useEffect has a missing dependency: 'onStopSelect'.  react-hooks/exhaustive-deps
```

- `useEffect(() => { ... }, [onSelectNode])` — deps 배열에 `onStopSelect`(= `onJourneyStopClick` 전달 경로)가 빠져 있다.
- 현재 `onStopSelect`는 App에서 `setActiveStopIdx`(stable setter)를 직접 전달하므로 stale-closure 버그는 발생하지 않는다. 단, deps 배열이 의도와 다르게 기록되어 향후 리팩토링 시 함정이 된다.
- 파일: `frontend/src/MapView.jsx:61`

### 스테일 docstring — `persons.py`·`journey.py`의 "13인" 표기

실제 큐레이션 인물은 24인(`_ERA` 딕트 24개 항목, `data/person_events/` 24개 파일)이지만 두 파일 docstring에 여전히 "13인"이 기재되어 있다.

- `backend/app/routes/persons.py:1,104`: "큐레이션된 13인 인물 목록 엔드포인트", "큐레이션된 13인 목록"
- `backend/app/routes/journey.py:6,77`: "큐레이션 13인이 아니면 빈 stops 반환"
- 파일: `backend/app/routes/persons.py:1,104`, `backend/app/routes/journey.py:6,77`

### 큐레이션 인물 표시 이름 이중 출처

인물 표시 이름의 출처가 두 곳이다. 프론트 탐험 헤더(`App.jsx:85,141-144`)는 Neo4j Person 노드의 `nameKo`(inject_ko_names.py 주입값)를, 큐레이션 목록·여정 응답은 `persons.py:36-53`의 하드코딩 `_NAME_KO` 딕트를 사용한다. 두 값이 어긋나면 헤더와 목록이 서로 다른 이름을 표시한다. 일치를 강제하는 코드·테스트가 없다.

- 파일: `frontend/src/App.jsx`, `backend/app/routes/persons.py:36-53`, `data/names_ko/people.json`

### 자동화 테스트 전무

프론트·백엔드 모두 테스트 0건. `frontend/package.json`의 scripts에는 `lint`만 있고 vitest/jest 의존성이 없다. 백엔드에도 pytest 설정·`test_*.py`가 없다. 좌표 dedup, 순번 압축(`compactSeqs`), 여정 정차지 인덱싱 등 회귀가 잦은 순수 로직에 안전망이 없으며 검증은 수동 Playwright에 의존한다.

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

### 모바일 읽기 모드: 지도 노출 영역 탭 캐처 크기 협소

`App.jsx:270-274`: `readingEventId`가 열릴 때 투명 탭 캐처를 `{ top:0, left:0, right:0, bottom:'90dvh', zIndex:4 }`로 배치한다. 레이아웃은 전체 100dvh 중 상단 nav(48px) 아래 나머지를 지도+오버레이 영역으로 사용하므로, 탭 캐처 실제 높이는 `(100dvh - 48px) - 90dvh ≈ 10dvh - 48px`(기기 높이 약 10% 미만)이다.

- 탭 캐처가 동작은 하나 탭 가능 영역이 매우 좁다. 주 닫기 경로는 오버레이 내 ▾ 버튼이다.
- SidePanel 하단 시트(`zIndex:10`)와 JourneyList 오버레이(`zIndex:5`)가 동시에 표시될 때 탭 캐처(`zIndex:4`)가 SidePanel 아래에 가려 지도 탭 닫기 동작이 작동하지 않을 수 있다.
- 파일: `frontend/src/App.jsx:270-274`

### `generate_person_event_verses.py` — 자유 텍스트 정규식 파싱

인물 사건의 `context` 한글 문장에서 괄호 안 구절 참조를 정규식으로 파싱해 `books` 필드와 본문을 생성한다.

- `parse_context_refs`(`generate_person_event_verses.py:78`)가 `re.findall(r"\(([^)]+)\)", context)`로 괄호 덩어리를 뽑고 책 약어와 장:절 패턴을 매칭한다.
- 정규식이 인식하지 못하는 표기는 조용히 `continue`로 스킵된다. 사건에 참조가 하나도 안 잡히면 `books: []`로 저장돼 📖 근거 칩이 비게 된다.
- 같은 권 중복은 첫 번째만 채택(`seen_book_ids`)이라 한 사건이 한 권의 여러 비인접 구간을 참조해도 첫 구간만 본문 fetch된다.
- 빌드타임 외부 의존: 본문은 `https://api.getbible.net`에서 HTTP fetch한다(`generate_person_event_verses.py`, `generate_verse_text.py`). 실패 시 `None` 캐싱 후 진행하므로 빌드는 죽지 않지만 일부 절 본문이 조용히 비어 적재될 수 있다.
- 파일: `backend/scripts/generate_person_event_verses.py:78-216`, `backend/scripts/generate_verse_text.py`

### 좌표 없는 사건 = 지도에 안 찍히는 정차지

`journey.py`는 `occursAt[0]`의 Place 노드 좌표를 Neo4j에서 조회하는데, 좌표가 없거나 `occursAt: []`이면 `seq=null, lng/lat=null`인 정차지로 처리한다(`journey.py:101-128`). 의도된 동작이지만, 일부 큐레이션 사건에 실제로 `occursAt: []`인 케이스가 있다.

- `data/person_events/john_the_apostle.json`, `data/person_events/peter.json`, `data/person_events/jesus.json` 등에 좌표 없는 stop이 존재한다.
- 이 사건들은 지도에 점이 찍히지 않고 리스트·타임라인에서만 보인다.
- 파일: `backend/app/routes/journey.py:101-128`

### `_build_id_to_slug()` — 요청마다 JSON 전량 재파싱 (캐시 누락)

`backend/app/routes/journey.py:18-30`의 `_build_id_to_slug()`는 `/person/{id}/journey` 요청마다 모든 `person_events/*.json`(현재 24개)을 `open`+`json.load`해 역매핑을 새로 만든다. `persons.py`·`places.py`의 동일 파일 로드는 `@functools.lru_cache`로 캐시되는데 이 함수만 누락되어 있다.

- 개선: `@functools.lru_cache(maxsize=1)` 부착으로 즉시 해결 가능.
- 파일: `backend/app/routes/journey.py:18-30`

### `places.py` `_place_to_persons` — `maxsize=None` 무한 캐시

`backend/app/routes/places.py:18`: `@functools.lru_cache(maxsize=None)`. `place_id` 문자열을 키로 사용하며 고유 장소 ID가 수천 개이므로 캐시가 무한 증가 가능하다. 각 값은 작은 dict 리스트이므로 현재 데이터 규모에서는 문제없지만 명시적 상한(`maxsize=512` 등)이 더 방어적이다.

- 파일: `backend/app/routes/places.py:18`

### 데이터 무결성 가정 — 미강제

`journey.py:19`와 `persons.py:72-81`은 "각 slug json의 첫 사건 `participants[0]`이 그 인물"임을 가정한다. 이 불변식을 강제하는 코드·테스트가 없다. 새 인물 JSON에서 `participants[0]`이 다른 인물이면 역매핑이 조용히 틀린다.

- 파일: `backend/app/routes/journey.py:18-30`, `backend/app/routes/persons.py:72-81`

### 동명이지(同名異地) 재사용 충돌 위험

authored-place를 새 인물 여정에 재사용할 때 영문 지명이 같아도 다른 지점인 경우가 있다. `authored-place-succoth`(이집트 숙곳, lat 30.56)와 요단 동편 숙곳이 충돌해 `authored-place-succoth-jordan`을 별도 신설한 실사례가 있다.

- 잠재 충돌 후보: `authored-place-mizpah`(베냐민 미스바, lat 31.878) vs `authored-place-mizpah-gilead`(길르앗 미스바, lat 32.05) — 후속 큐레이션에서 "미스바" 검색으로 잘못된 id를 재사용할 수 있다.
- 규칙: 재사용 전 `data/place_coords/places.json`에서 id·좌표를 대조해 의도한 지점인지 확인 필수.
- 파일: `data/place_coords/places.json`

---

## 성능 위험

### maplibre 번들 1.0 MB — Vite 500 kB 초과 경고

`frontend/dist/assets/maplibre-DntM08T7.js`가 **1.0 MB**(gzip ~273 kB). Vite 빌드 시 "Some chunks are larger than 500 kB after minification" 경고가 발생한다. `vite.config.js`의 `manualChunks`로 maplibre를 별도 청크로 분리했지만 라이브러리 자체 크기다. 동적 import 코드 스플리팅이나 라이브러리 교체 없이는 개선 불가하다.

- 파일: `frontend/vite.config.js`, `frontend/dist/assets/`

### ESRI 타일 서버 + Protomaps 글리프 — 외부 의존

`frontend/src/MapView.jsx:32-35`: `https://server.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}` (ESRI 타일), `MapView.jsx:29`: `https://protomaps.github.io/basemaps-assets/fonts/...` (글리프 서버). 두 외부 서버 모두 SLA 없이 의존한다. ESRI 무료 타일은 사용 정책 위반 시 접근 차단 가능. 오프라인·폐쇄망 배포 시 지도가 전혀 표시되지 않는다.

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

`backend/app/routes/nodes.py:168-170`: f-string으로 `{NODE_NEIGHBOR_LIMIT}` 상수를 쿼리에 삽입. `backend/app/routes/search.py:15,27`: `LIMIT {SEARCH_LIMIT}` 상수 삽입. 두 경우 모두 Python int 상수를 삽입하므로 실질적 인젝션 위험은 없다. 그러나 패턴 자체가 향후 사용자 입력 변수를 실수로 f-string에 넣을 위험을 열어 둔다. Cypher 파라미터(`$param`)로 교체하는 것이 더 안전한 패턴이다.

- 파일: `backend/app/routes/nodes.py:168-170`, `backend/app/routes/search.py:15,27`

### Neo4j 비밀번호 — 환경변수 단일 의존, 현재 구조는 적절

`backend/app/db.py:11`: `os.environ.get("NEO4J_PASSWORD")`; 없으면 `RuntimeError`. `docker-compose.yml:11,18`: `${NEO4J_PASSWORD:?must be set}`로 미설정 시 compose 실행 자체가 실패한다. `.env`는 `.gitignore`에 포함되어 있다. nginx 루트는 `frontend/dist`이고 `.env`는 그 위 디렉터리이므로 현재는 노출 위험 없음.

- 파일: `backend/app/db.py`, `docker-compose.yml`, `.gitignore`

---

*CONCERNS audit: 2026-07-02 (HEAD 689126abab88e741263d1d9a4a73d81b2be617d9)*
