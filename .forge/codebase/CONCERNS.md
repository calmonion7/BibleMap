---
last_mapped_commit: bfc1dd258b0308435ca24c48a82c9c86a9e622f1
mapped: 2026-06-16
---

# Codebase Concerns

> 직전 맵(commit 22a678c) 이후 리팩토링 4-파트 시리즈로 일부 항목이 해소됐다. 해소분은 맨 아래 "직전 맵에서 해소된 항목"에 별도 기록하고, 본문에는 **현존 concern만** 남긴다.

## Known Bugs

**SidePanel Book 연도 칩 — 신약 책도 항상 "BC" 표기 (미해결):**
- `frontend/src/SidePanel.jsx:254`: `${Math.abs(node.properties.startYear)}BC~${Math.abs(node.properties.endYear)}BC` — 양수(AD/신약) 연도도 무조건 "BC"로 표기. 예: 요한계시록 같은 신약 책이 "95BC~95BC"로 잘못 표시된다.
- 같은 파일 `SidePanel.jsx:358`(event 표시)은 `e.startDate < 0 ? 'BC ...' : 'AD ...'`로 부호를 올바르게 분기하고, `TimelineView.jsx`도 `fmtYear`로 BC/AD를 구분한다 — 즉 같은 책이 뷰/필드별로 다르게 보인다.
- 수정: `startYear < 0 ? 'BC' : 'AD'` 분기 필요.

**MapView 에러 배너 — 네비게이션 바 아래 가려짐 (미해결, 추적 칩 task_c16549df):**
- `/places` 실패 시 에러 배너(`frontend/src/MapView.jsx:461` `top: 12`, `zIndex: 10`)가 플로팅 네비(`frontend/src/App.jsx:173` `zIndex: 20`) 뒤에 가려진다.
- 단, `noLocation` 안내 배너(`MapView.jsx:471`)는 `top: 60`으로 네비(48px) 아래에 두어 회피함 — 에러 배너만 미수정. `top`/`zIndex`를 noLocation 배너와 동일하게 맞추면 됨.

## Data Accuracy

**추정 연도 데이터 — 큐레이션 추정치, 일부 근거 박약:**
- `data/book_years_approx/books.json`이 시대 연도(`startYear`)가 없는 책의 배치 연도를 수동 큐레이션 추정치로 보유한다. 각 항목 `basis` 필드에 근거가 적혀 있다.
- 특히 약한 항목(데이터에 명시됨): 야고보서(AD49) basis "**가장 불확실(리서치 미확정)**", 잠언(BC950) basis "**근거 약함**".
- UI는 이를 `frontend/src/TimelineView.jsx`의 "추정" 마커(점선 보더 + `yearBasis` 툴팁, `b.yearApprox` 분기)로 표면화한다. 코드 버그 아님 — 데이터의 본질적 불확실성. 재검증 시 `basis` 문구 갱신 필요.

**Book startYear/endYear — event.startDate 집계로 추정:**
- `backend/scripts/load_books.py` `build_book_year_range()`(L57~)가 책에 직접 연도가 없을 때 책에 속한 event들의 `startDate` min/max로 도출한다. 이벤트 연결이 빈약한 책은 연도 범위가 왜곡될 수 있다.
- BC 판별이 문자열 `"BC"` 포함 여부에 의존(`load_books.py:68~69` `int(str(start_raw).replace("BC","").strip())` + `if "BC" in str(start_raw)`) — theographic 원본 형식이 바뀌면(예: 음수 정수) 부호가 반전된다. 현재는 정적 데이터라 문제 없음.

## Architecture / 패턴 분기

**`/books` 엔드포인트 — 런타임 JSON 파일 로드 (Neo4j inject 컨벤션과 분기):**
- `backend/app/routes/books.py`가 추정 연도 오버레이를 JSON에서 직접 읽는다. (요청마다 재읽기는 `functools.lru_cache(maxsize=1)`로 해소됨 — 아래 해소 항목 참조.)
- 다른 보조 데이터(한글 이름·인물 성품·책 컨텍스트)는 전부 `backend/scripts/inject_*.py`로 Neo4j 노드에 주입하는 컨벤션을 따르는데, 이 오버레이만 Neo4j를 우회한다. 의도된 분리(큐레이션 데이터를 코드 재빌드 없이 JSON 교체)지만 컨벤션 불일치다.
- **부수효과 — lru_cache로 인한 stale:** `_load_approx()`가 프로세스 수명 동안 1회만 로드한다. `books.json`을 교체해도 api 컨테이너를 재시작하기 전까지 반영되지 않는다(JSON만 교체하려던 본래 의도와 상충). 핫스왑이 필요하면 캐시 무효화 경로가 없다.

**inject 스크립트 vs `/books` — data 경로 해석 방식이 다름:**
- inject 스크립트들은 data 경로를 **스크립트 파일 기준 상대경로**로 해석한다(`backend/scripts/inject_ko_names.py:16` `Path(__file__).parent.parent.parent / "data" / "names_ko"`, `load_books.py:18` `os.path.join(SCRIPT_DIR, "..", "..", "data", ...)`) — 호스트에서 직접 실행됨(`deploy.sh` `[4/4]`가 `python3 backend/scripts/inject_ko_names.py`로 호스트 실행).
- 반면 `/books`는 `DATA_DIR` 환경변수(docker 마운트 기준, 기본 `/app/data`)를 우선하고 못 찾으면 레포 상대경로로 폴백한다(`books.py:15~22`).
- 즉 같은 `data/` 디렉터리를 (a) 스크립트는 `__file__` 상대경로, (b) 라우터는 `DATA_DIR`+폴백 으로 가리킨다. 동작은 하지만 신규 데이터 추가 시 양쪽 경로 메커니즘을 모두 인지해야 한다.

**`anthropic` 패키지가 `requirements.txt`에 없음:**
- `backend/scripts/generate_person_traits.py:?`·`generate_book_context.py:?`가 `import anthropic`를 한다. 그러나 `backend/requirements.txt`는 `fastapi==0.136.3`, `neo4j==6.2.0`, `uvicorn==0.49.0`만 명시.
- 이 generate 스크립트들은 호스트 일회성 오프라인 실행(docker 이미지에 미포함)이라 런타임 영향은 없으나, 의존성이 어디에도 선언돼 있지 않아 재실행 환경 구성 시 누락된다. `ANTHROPIC_API_KEY` 환경변수도 필요(코드에서 require, 하드코딩 없음 — OK).

## Performance Bottlenecks

**`/node/{id}/places` — Person·PeopleGroup 분기에 LIMIT 없음:**
- `backend/app/routes/nodes.py:23~52`의 Person·PeopleGroup `/places` 쿼리에 LIMIT 절이 없다. PeopleGroup은 `PeopleGroup<-[:MEMBER_OF]-Person`, `Event-[:HAS_PARTICIPANT]->person`, `Event-[:OCCURS_AT]->Place` 3단계 매칭이라 대형 집단(예: 이스라엘 자손)은 수천 건 반환 가능 → Neo4j + MapView GeoJSON 렌더 과부하. (`seen` set으로 중복은 제거하나 쿼리 자체는 잘리지 않음.)

**`/node/{id}` — 단일 요청 안에서 3~5회 직렬 Neo4j 쿼리:**
- `backend/app/routes/nodes.py` `get_node()`(L134~): 노드 조회 → 이웃(`LIMIT 50`) → 전체 이웃 `count` → (Book이면) top_persons, top_events 2회. 연결 많은 Book(예: 창세기) 선택 시 왕복 레이턴시 누적. SidePanel과 MapView가 동시에 같은 nodeId를 조회하면 사실상 두 배.

**검색(`/search`) — `nameKo`·`name`에 인덱스 없음, 전체 노드 스캔:**
- `backend/app/routes/search.py:14~30`의 `MATCH (n) WHERE (n.nameKo CONTAINS $q OR toLower(n.name) CONTAINS toLower($q))`는 라벨·인덱스 없는 전체 그래프 스캔. `backend/app/main.py` lifespan이 만드는 인덱스는 `theographic_id`에만 존재(Person/Place/Event/PeopleGroup/Book). 250ms 디바운스 키 입력마다 전체 스캔. 현재 노드 수(수천)에서는 허용 범위.

**TimelineView — `/events` 전체 일괄 로드, 가상화 없음:**
- `backend/app/routes/events.py`가 LIMIT 없이 전체 Event 반환(`MATCH (e:Event) WHERE e.startDate IS NOT NULL ... ORDER BY e.sortKey`), `frontend/src/TimelineView.jsx`가 마운트 시 일괄 fetch 후 가상 스크롤 없이 전부 DOM 렌더. 현재 이벤트 수에서는 허용 가능, 확장 시 선형 증가.

**동기 FastAPI 라우터 — uvicorn 쓰레드풀 의존:**
- 모든 라우터가 `def`(동기) 선언 → FastAPI가 기본 쓰레드풀에서 실행. 다수 동시 요청 시 Neo4j 블로킹 대기가 쓰레드풀을 소진할 수 있다(CORS `*`로 공개 배포 시 리스크 상승). 단일 사용자 환경에서는 미발현.

## Tech Debt / Dead Code

**`inject_ko_names.py` — 배포마다 조건 없는 전체 덮어쓰기:**
- `deploy.sh` `[4/4]`가 매 배포 시 실행하며 한글 이름/별칭을 무조건 `SET`. 데이터 변동이 없어도 전체 재기록. 현재 규모에서는 허용 가능.

## Security Considerations

**CORS `allow_origins=["*"]`:**
- `backend/app/main.py:25~31`에서 모든 오리진 허용. 완화 요소: `allow_credentials=False`, `allow_methods=["GET"]`로 읽기 전용 범위 제한. 권장: 프로덕션 도메인 화이트리스트.

**MapView 팝업 — `setHTML()`에 DB 값 직접 삽입 (XSS 잠재):**
- `frontend/src/MapView.jsx:287~304`의 `setHTML()` 템플릿 리터럴에 `${label}`(Neo4j `nameKo`)과 `${typeLabel}`을 HTML 이스케이프 없이 삽입. 완화: 데이터 출처가 theographic 정적 + 관리형 JSON(`data/names_ko/`)으로 한정, 사용자 입력 경로 없음. 권장: `setText()` 사용 또는 이스케이프.

**`search.py`·`nodes.py` — f-string Cypher에 Python 상수 주입:**
- `LIMIT {SEARCH_LIMIT}`(`backend/app/routes/search.py:27`), `LIMIT {NODE_NEIGHBOR_LIMIT}`(`backend/app/routes/nodes.py:157`)를 f-string으로 삽입. 사용자 입력 `$q`/`$id`는 파라미터화돼 안전하고 삽입값은 모듈 상수라 실 인젝션 경로 없음. 구조적 위험만 존재 — 확장 시 파라미터화 권장.

**비밀 관리 — 커밋된 시크릿 없음 (확인됨):**
- `.env`는 `.gitignore`(L12)에 등록돼 추적되지 않으며 git 히스토리에도 없음(`git log --all -- .env` 빈 결과, `git ls-files` 미포함). `.env.example`은 placeholder만.
- `NEO4J_PASSWORD`: `backend/app/db.py`가 환경변수에서 읽고 미설정 시 `RuntimeError`(하드코딩 폴백 없음). `docker-compose.yml`은 `${NEO4J_PASSWORD:?...}`로 미설정 시 compose 자체 실패. `NEO4J_AUTH=neo4j/${NEO4J_PASSWORD}`로 파생.
- `ANTHROPIC_API_KEY`: generate 스크립트가 환경변수에서만 읽음.
- Neo4j 포트는 `127.0.0.1`에 바인딩(`docker-compose.yml` `127.0.0.1:7474`, `127.0.0.1:7687`) — 외부 노출 안 됨. 다만 기본 `NEO4J_USER=neo4j`.

## Fragile Areas

**MapView — `expandPlaceRef`/`expandedPlaceRef` 공유 뮤터블 ref:**
- `frontend/src/MapView.jsx`. maplibre 초기화 effect 클로저와 selection effect가 ref(함수·상태)를 공유한다. cleanup 순서가 어긋나면 이미 `map.remove()`된 인스턴스에 접근 가능 — `destroyed` 플래그와 `mapRef.current === map` 체크로 방어. 링 신규 로직은 반드시 `map.on('load')` 핸들러 안에서 초기화하고, ref 접근 전 `destroyed`/`mapRef` 확인 필요. 빠른 연속 탭 전환 정합성 자동 테스트 없음.

**`moveend` 이벤트 + 폴백 타이머(700ms) 경합:**
- `frontend/src/MapView.jsx` selection effect `runExpand`. `map.once('moveend')` + `setTimeout(runExpand, 700)` 중 먼저 발화한 쪽이 `fired` 플래그로 차단. `fitBounds` `duration: 600ms`와 폴백 700ms 사이 여유 100ms뿐 → 저사양에서 거의 동시 실행 가능. `duration` 변경 시 폴백도 `duration + 200ms` 이상으로 함께 조정 필요.

**LLM 생성 JSON 파싱 — 코드펜스 처리 취약:**
- `backend/scripts/generate_person_traits.py:65`(`text = text.split("```")[1]`), `generate_book_context.py:64` 동일 패턴. LLM이 중첩 코드블록/다른 형식으로 응답하면 파싱 실패 → `except`에서 `{"traits": []}`(generate_person_traits.py:121) 빈 값 저장(데이터 손실). 완화: 오프라인 일회성, 재실행 시 `tid in result` 스킵. 파싱 실패 시 원본 로깅 권장.

## External Dependencies (런타임 의존)

**외부 지도 타일·폰트 서버 — 다운 시 지도 자체 미표시:**
- `frontend/src/MapView.jsx:43` ArcGIS NatGeo 타일(`server.arcgisonline.com`) + `MapView.jsx:38` Protomaps 폰트 CDN(`protomaps.github.io`). 둘 다 무료 공개 엔드포인트, SLA 없음. ArcGIS는 ToS상 대량 트래픽 제한 가능. 다운/정책 변경 시 지도 렌더 실패. 권장: 자체 호스팅 타일(PMTiles) 검토.

**`getbible.net` 성경 텍스트 API — 캐시 없음, 실패 시 조용히 null:**
- `frontend/src/SidePanel.jsx:25~` `fetchVerseText()`가 `https://api.getbible.net/v2/korean/${bookOrder}/${chapter}.json`를 클라이언트에서 직접 fetch(대표 구절 + 인물 성품 verse_ref 원문). 캐시는 컴포넌트 상태(`traitVerses`, L96)에만 — 페이지 리로드 시 소실. API가 CORS 거부/다운되면 `catch`에서 `null` 반환(L9~10, L32~33) → 구절 텍스트만 조용히 미표시(다른 정보는 정상). v2는 절 단위 엔드포인트가 없어 장(chapter) 전체를 받아 클라이언트에서 절을 찾는다(과다 전송). 권장: 백엔드 프록시 + 캐시 또는 정적 번들링.

**theographic GitHub 원본 — 데이터 적재 시점 의존:**
- `backend/scripts/load_theographic.py:14~17`, `load_books.py:14~15`, `generate_*.py`가 적재/생성 시 `raw.githubusercontent.com/robertrouse/theographic-bible-metadata/master/...`를 fetch. `master` 브랜치를 가리켜 핀이 없음 — 업스트림이 스키마(필드명)나 데이터를 바꾸면 재적재가 깨질 수 있다. 런타임(요청 처리)에는 영향 없음(적재는 오프라인). 네트워크 실패 시 예외로 중단(silent 아님).

## Operational

**백엔드 hot-reload 비지원 — 로컬 검증 마찰:**
- `backend/Dockerfile`이 `app/`을 COPY(마운트 아님)하고 uvicorn `--reload` 없음. 코드 변경 → `docker compose up -d --build api`로 재빌드·재시작 필요. 자동 배포(`deploy.sh`)는 재빌드하지만, 로컬에서 재빌드를 잊으면 이전 코드로 검증하게 된다. 개선: 개발용 `volumes` 코드 마운트 + `--reload`.

**`deploy.sh` — 한글 이름 주입 실패 시 배포 중단(15회 재시도):**
- `deploy.sh` `[4/4]`가 Neo4j 준비를 15회(×2초=최대 30초) 폴링하며 `inject_ko_names.py` 실행, 실패 시 `exit 1`로 배포 중단. Neo4j 초기 기동이 30초를 넘으면 배포가 실패한다. CI는 `self-hosted` 러너에서 실행(`.github/workflows/deploy.yml`).
- 사소: `deploy.sh` 단계 라벨이 `[1/3] [2/3] [3/4] [4/4]`로 분모가 섞여 있음(표기 불일치, 동작 영향 없음).

## Test Coverage Gaps

**자동화 테스트 전무 (단위·통합):**
- 백엔드 Neo4j 쿼리 로직(`backend/app/routes/`), 프론트 컴포넌트, API 응답 스키마 정합성 모두 미검증. 유일한 검증 수단이 수동 Playwright 시나리오(MEMORY.md). 엔드포인트 응답 구조 변경·Cypher 오류가 배포 전 자동 감지 불가. (프론트 lint는 현재 clean — 아래 해소 항목 참조.)

---

## 직전 맵(22a678c)에서 해소된 항목 (재검증 결과 — 더 이상 concern 아님)

- **lint `react-hooks/set-state-in-effect` 3건 + exhaustive-deps 1건:** `npm --prefix frontend run lint` 현재 exit 0, 무경고. `frontend/src/SidePanel.jsx`의 effect들이 setState를 `.then()` 콜백 내부로 이동(L102 `setCollapsed({})`, L118 `setKeyVerseState`), `frontend/src/TimelineView.jsx`도 정리됨. **lint clean.**
- **프론트 단일 번들 >500kB 경고:** `frontend/vite.config.js`에 `build.rollupOptions.output.manualChunks` 추가 — `maplibre-gl`은 `maplibre` 청크, 나머지 node_modules는 `vendor` 청크로 분리. 단일 1.25MB 청크 경고 해소.
- **API 베이스 URL 4중 중복:** `frontend/src/api.js`의 `apiGet()`/`API_BASE`가 이제 실제 사용됨 — `App.jsx`, `MapView.jsx`, `SidePanel.jsx`, `TimelineView.jsx` 전부 `import { apiGet } from './api'`로 통합. 개별 `const API_URL = ...` 선언 전부 제거됨(grep 결과 0건).
- **`/books` 요청마다 JSON 재읽기 (캐시 없음):** `backend/app/routes/books.py`에 `@functools.lru_cache(maxsize=1)`로 1회 로드 캐시 추가. (대신 stale 부수효과 신규 — 위 Architecture 섹션 참조.)
- **`/books` 경로 의존성 — DATA_DIR 미설정 시 조용히 `{}`:** `books.py`가 `_APPROX_CANDIDATES`로 `DATA_DIR`(docker) → 레포 상대경로(`_REPO_DATA_DIR`) 순 폴백 추가 — docker/비-docker 모두에서 파일을 찾는다. (어느 후보에서도 못 읽으면 여전히 `{}` 폴백이지만, 비-docker 직접 실행 시 누락 시나리오는 해소.)
- **Dead code:** `frontend/src/App.css`(미import 잔재) 삭제됨(파일 부재). `App.jsx`가 `MapView`에 넘기던 orphan prop `selectedNodeLabel` 제거됨(grep 0건).

---

*Concerns audit: 2026-06-16*
