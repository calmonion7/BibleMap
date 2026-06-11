---
last_mapped_commit: 288b14e23c889de294d34d0f794867d4e313a421
mapped: 2026-06-11
---

# CONCERNS — 기술 부채 · 알려진 이슈 · 취약 영역

HEAD `288b14e` 기준으로 **현재 열려 있는** 항목만 기록한다. 각 항목은 실제 코드를 읽어
`파일:라인`으로 검증했다. 도메인 용어 정의는 여기서 다루지 않는다(그건 CONTEXT.md 몫). 여기는
구현 사실만 적는다.

심각도 표기: 🔴 운영 위험 / 🟡 잠재·조건부 / 🟢 의도적 수용 또는 사소.

---

## 인프라 · 배포

### 🔴 `deploy.sh`가 dev 메인 저장소에서 `git reset --hard origin/main`을 돈다
`.github/workflows/deploy.yml:13-16` — 셀프호스티드 러너가 `/Users/calmonion/Project/BibleMap`
(= 개발에 쓰는 그 작업 트리)에서 `git fetch origin` 후 `git reset --hard origin/main`을 실행하고
`bash deploy.sh`를 호출한다. 별도 배포용 클론이 아니라 **개발 작업 트리 자체**이므로, push 시점에
커밋되지 않은 추적 파일(WIP)이 있으면 경고 없이 모두 폐기된다. 또 `deploy.sh:4`의 `WORKTREE`는
스크립트 위치 기준이라 같은 디렉터리를 가리킨다. dev 머신이 곧 배포 타깃이라는 구조적 위험.

### 🟡 `deploy.sh` 단계 번호 불일치 `[1/3]`→`[3/4]`
`deploy.sh:34` `[1/3]`, `:41` `[2/3]`로 시작했다가 `:45` `[3/4]`, `:49` `[4/4]`로 바뀐다.
실제 단계는 4개(프론트 빌드 / API 이미지 빌드 / 컨테이너 재시작 / 한글 주입)이므로
앞의 `/3` 두 줄이 오기. 동작에는 영향 없으나 로그만 보면 진행률이 어긋나 보인다.

### 🟡 `inject_ko_names` — healthcheck 없이 고정 15회 재시도
`deploy.sh:51-62` — Neo4j가 뜰 때까지 `python3 ... inject_ko_names.py`를 `seq 1 15` 동안
2초 간격으로(`sleep 2`) 그냥 재시도한다. compose에 Neo4j healthcheck/`depends_on: condition`이
없어서(`docker-compose.yml:2-11`, `:20-23`은 단순 `depends_on`) 준비 신호를 모른 채 최대 ~30초
폴링이다. 머신이 느리거나 첫 부팅 시 인덱스 빌드가 길면 15회로 부족할 수 있고, 실패하면
`exit 1`로 배포 전체가 중단된다(`:59-61`).

### 🟡 `backend/Dockerfile`이 `data/`를 복사하지 않음 — 볼륨 마운트 + 호스트 직접 실행에 의존
`backend/Dockerfile:5`는 `COPY app/ ./app/`만 한다. `data/`(현재 `data/names_ko/`의 4개 JSON:
events·groups·people·places)는 `docker-compose.yml:19-20`의 `./data:/app/data` 볼륨 마운트로만
컨테이너에 들어간다. 게다가 `inject_ko_names.py`는 컨테이너가 아니라 **호스트에서 직접**
실행되며(`deploy.sh:52`), `DATA_DIR = Path(__file__).parent.parent.parent / "data" / "names_ko"`
(`inject_ko_names.py:16`)로 호스트 경로를 읽는다. 즉 이미지는 데이터에 대해 self-contained가
아니고, compose 마운트 또는 호스트 파일 배치가 어긋나면 조용히 빈 데이터가 된다.
`backend/.dockerignore`도 없다.

### 🟢 프론트 번들 >500kB(minified) — Vite chunk-size 경고가 매 빌드 발생
maplibre-gl + cytoscape(+cose-bilkent, expand-collapse) 때문에 메인 청크가 500kB 기본 한계를
넘는다. `frontend/vite.config.js`에 `build.chunkSizeWarningLimit`이나 `manualChunks` 설정이
전혀 없어(현재 `plugins: [react()]`만), `npm run build`(= `deploy.sh:37`)마다 경고가 뜬다.
기능상 문제는 아니나 빌드 로그 노이즈이며 초기 로드 비용 신호.

---

## 프론트엔드

### 🔴 `MapView` 외부 타일·폰트 의존, 폴백 없음
`frontend/src/MapView.jsx:34` glyphs를 `https://protomaps.github.io/basemaps-assets/fonts/...`,
`:38-39` 래스터 타일을 `https://server.arcgisonline.com/.../NatGeo_World_Map/...`에서 받는다.
둘 다 외부 무료 호스트이며 폴백/셀프호스팅이 없다. 외부 서비스가 죽거나 차단되면 지도가
바탕 없이 비고, 라벨 폰트(`:80` `'Noto Sans Regular'`)도 깨진다. 코드상 타일/글리프 로드
실패에 대한 에러 처리는 없다(`error` 상태는 `:175`의 `/places` fetch 실패만 잡음).

### 🟡 App↔MapView 시트 높이·모바일 분기 상수가 두 파일에 수동 동기화
- `frontend/src/App.jsx:19` `SHEET_VH = 55` (하단 시트 높이)와
  `frontend/src/MapView.jsx:190` `fitBounds` 패딩의 `window.innerHeight * 0.55`가 **반드시 일치**
  해야 한다. 한쪽만 바꾸면 모바일에서 마커가 시트에 다시 가려진다. 주석으로 경고는 달려 있으나
  (`App.jsx:18`, `MapView.jsx:186-187`) 컴파일러가 강제하지 못하는 수동 결합이다.
- 모바일 분기 임계값도 중복: `App.jsx:17` `MOBILE_QUERY = '(max-width: 768px)'`(matchMedia)
  vs `MapView.jsx:188` `window.innerWidth <= 768`. 768px가 두 군데 하드코딩.

### 🟡 `MapView` 팝업 `.setHTML` 문자열 보간 — 데이터가 외부화되면 XSS 가능
`MapView.jsx:111-128`이 `setHTML`에 `${label}`(장소명)을 직접 끼워 넣는다. 현재 `label`은 우리
DB의 `nameKo`라 사실상 안전하지만, 향후 이름 데이터가 외부/사용자 입력으로 바뀌면 즉시 XSS
경로가 된다. 정적 데이터라는 전제에만 의존.

### 🟡 GraphView fit/cy 타이밍 + selectedNode 변경마다 전체 destroy/recreate
`frontend/src/GraphView.jsx:37-158` — `selectedNode`(또는 `onSelectNode`)가 바뀔 때마다 effect가
cytoscape 인스턴스를 통째로 새로 만들고(`:84`), cleanup에서 `cy.destroy()`(`:157`)한다. 노드
하나 바꿔도 그래프 전체 재생성·재레이아웃이다(`cose-bilkent`, `expandCollapse`,
`collapseAll`). `:32-35`의 fit effect와 `:153`/`:150-151`의 fit 호출이 별도 타이밍으로 얽혀 있어,
오버레이 토글·확장/축소·노드 전환이 겹치면 화면 점프나 깜빡임 여지가 있다.

### 🟢 GraphView 하드코딩 기본 노드 (모세 id)
`GraphView.jsx:9` `DEFAULT_NODE = 'recjNRR60PAuFtjha'`(주석 "모세"). `selectedNode`가 없을 때의
초기 그래프를 이 특정 theographic_id에 고정(`:38`). 이 id가 DB에서 사라지면 초기 그래프가
에러 상태(`:155`, "그래프를 불러오지 못했습니다")가 된다. 정적 데이터라 사실상 안정적.

### 🟢 `/node/{id}/places` 빈 배열에 대한 사용자 피드백 없음
`MapView.jsx:177-194` — `/places`가 `[]`를 주면 `setData(EMPTY_GEOJSON)`만 하고 `fitBounds`도
건너뛴다(`:181`). 좌표가 없는 노드를 고르면 지도가 조용히 비어 "왜 아무것도 안 뜨지?" 상태가
된다. (에러 배너 `:206`은 fetch 실패에만 뜬다.)

---

## 백엔드

### 🟡 Cypher 라벨/타입 f-string 보간 (값은 내부 상수)
다음 위치들이 쿼리 문자열에 파이썬 변수를 f-string으로 끼워 넣는다. 현재 끼우는 값은 전부
내부 상수/리터럴이라 인젝션 표면이 아니지만, 향후 외부 입력이 흘러들면 위험해진다:
- `backend/app/main.py:16-17` — 라벨(`Person`/`Place`/`Event`/`PeopleGroup`)로 인덱스 생성.
- `backend/app/routes/nodes.py:147` — `LIMIT {NODE_NEIGHBOR_LIMIT}`(상수 50).
- `backend/app/routes/search.py:15-21` — `LIMIT {SEARCH_LIMIT}`(상수 20). 검색어 `q`는 정상적으로
  파라미터 바인딩(`q=q`)하므로 안전.
- `backend/scripts/inject_ko_names.py:25-26` — `MATCH (p:{label} ...)` 라벨 보간(`inject` 인자).
- `backend/scripts/load_theographic.py:37-42` — 인덱스 DDL 리터럴.

### 🟡 `events.py` 가드 없는 `float(sortKey)`
`backend/app/routes/events.py:24` `"sortKey": float(props.get("sortKey", 0))`. `sortKey`가 None이
아닌 비숫자 문자열이면 `ValueError`로 `/events` 응답 전체가 500이 된다. `get`의 기본값 0은
키 부재만 막고, 잘못된 타입은 못 막는다. 데이터 적재(`load_theographic.py:117`)가 원천
`f.get("sortKey")`를 그대로 넣으므로 원천 데이터 형태에 의존.

### 🟡 이웃 컷 매직넘버 — 조용한 잘림
`backend/app/routes/nodes.py:6-7` `MAX_NEIGHBORS_PER_TYPE = 30`, `NODE_NEIGHBOR_LIMIT = 50`.
- `/node/{id}`(`:147`)는 이웃을 50개로 LIMIT — 51번째부터는 응답에서 그냥 사라지고
  SidePanel은 잘렸다는 표시 없이 일부만 보여준다.
- `/node/{id}/neighbors/grouped`(`:108`)는 타입별 30개를 넘으면 `continue`로 버린다.
두 경로 모두 "더 있음" 신호가 없어 사용자는 전체를 봤다고 오인한다.

### 🟢 검색 풀스캔 `CONTAINS` (정적 ~930노드 전제로 의도적 수용)
`backend/app/routes/search.py:16-22` — `MATCH (n) WHERE n.nameKo CONTAINS $q OR n.name CONTAINS $q`.
인덱스 없는 전체 노드 substring 스캔이다. 노드가 ~930개로 작고 정적이라 의도적으로 받아들인
선택. 데이터가 크게 늘면 풀텍스트 인덱스로 교체 필요.

### 🟢 CORS `allow_origins=["*"]`
`backend/app/main.py:27` 모든 오리진 허용. `allow_credentials=False`, `allow_methods=["GET"]`로
읽기 전용 공개 API라는 전제. 인증/쓰기가 생기면 재검토 대상.

---

## 해소 확인 (resolved since last map)

### ✅ SidePanel react-hooks `set-state-in-effect` lint 실패 — 해소
task 13에서 SidePanel을 재작성. 이제 effect 안에서 setState를 비동기 fetch 콜백에서만
호출하고(`frontend/src/SidePanel.jsx:31-39`), loading/ready는 `state.id === nodeId` 파생으로
계산한다(`:41-43`). **검증:** `cd frontend && npx eslint .` 실행 결과 **exit 0**(경고·에러 0건).

### ✅ 모바일 "지도 마커가 패널에 가려짐" — 해소
task 12에서 App을 반응형 하단 시트로 바꿈. `frontend/src/App.jsx:189-204`가 `isMobile`일 때
패널을 우측 사이드패널 대신 하단 시트로 띄우고(`bottom:0, height:55vh`), `MapView.jsx:188-192`가
`fitBounds` 패딩에 시트 높이만큼(`innerHeight*0.55+20`)을 더해 마커를 가려지지 않는 상단 띠로
모은다. **검증:** 두 파일에서 반응형 분기와 패딩 보정 로직을 코드로 확인.

---

## 정정 (이번 맵에서 사실 확인 후 수정)

### ⚠️ `/node/{id}/neighbors/grouped`는 dead 엔드포인트가 **아님**
직전 추정과 달리, 이 엔드포인트(`backend/app/routes/nodes.py:90-121`)는 **GraphView가 실제로
사용 중**이다. `frontend/src/GraphView.jsx:42-45`가 `/node/${id}`와
`/node/${id}/neighbors/grouped`를 `Promise.all`로 동시에 호출해 그룹별 노드를 그린다
(`:46-82`에서 `grouped[type]`로 부모-자식 노드 구성). SidePanel만 `/node/{id}` 단일 호출로
클라이언트에서 그룹핑(`frontend/src/SidePanel.jsx:31-56`)할 뿐이다. **검증:**
`grep -rn "neighbors/grouped"` → `GraphView.jsx:44` 호출 + `nodes.py:90` 정의 두 곳 매칭.
따라서 이 항목은 미해결 부채가 아니라 **활성 엔드포인트**다.

부수적으로 GraphView는 같은 노드 데이터를 두 엔드포인트(`/node/{id}` + `.../neighbors/grouped`)로
중복 조회한다는 점은 남는다 — `/node/{id}`도 이미 `label`+`relation`을 가진 `neighbors`를
주므로(`nodes.py:157-164`), 한 번의 호출로 합칠 여지가 있는 잠재 정리 거리(🟢).
