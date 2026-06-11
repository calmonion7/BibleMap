---
last_mapped_commit: 60716ea24a78866177eb8fe28dee9c43ced5ff0f
mapped: 2026-06-11
---

# 기술 부채 · 알려진 이슈 · 리스크 영역

직전 맵(`60962d0`) 이후 CI 배포 경로·죽은 폴 스크립트·프론트 무음 fetch 실패가 정리되었다. 이 문서는 HEAD `60716ea` 기준으로 **현재도 열려 있는** 항목만 기록한다. 이미 해소된 항목은 맨 아래 "해소 확인" 절에 검증 결과만 남긴다.

## 린트 / 빌드 신뢰성

### `eslint-plugin-react-hooks` v7로 인한 lint 실패 — `SidePanel.jsx`가 현재 lint FAIL
`frontend/package.json:27`은 `"eslint-plugin-react-hooks": "^7.1.1"`을 캐럿 범위로 잡고 있다. v7이 새로 도입한 `react-hooks/set-state-in-effect` 규칙이 코드베이스의 effect-내-동기-setState 패턴을 에러로 잡는다. `npx eslint .`를 돌리면 현재 `frontend/src/SidePanel.jsx:23`(`useEffect` 안 `if (!nodeId) { setNode(null); ... }`의 동기 `setNode`)에서 1건 에러로 **lint가 실패**한다(다른 뷰는 fetch-then-setState라 비동기 콜백 안에서 호출돼 이 규칙에 안 걸리지만, `SidePanel`만 effect 본문에서 동기로 호출). 정책 미결: 규칙 핀/다운그레이드 vs effect 리팩터. 캐럿 범위 lint 플러그인은 조용히 드리프트해 다음 `npm install`에서 또 다른 규칙이 추가될 수 있다(`frontend/eslint.config.js:14`이 `reactHooks.configs.flat.recommended`를 그대로 extends).

## 설정 / 배포 부채

### `deploy.sh`가 메인 개발 레포에서 `git reset --hard origin/main` 실행
`.github/workflows/deploy.yml:13-16`은 `/Users/calmonion/Project/BibleMap`(별도 클론이 아닌 **메인 개발 레포**)에서 `git fetch origin` → `git reset --hard origin/main` → `bash deploy.sh`를 돈다(별도 클론 대신 이 옵션이 선택됨). 편집 중 커밋 안 된 추적 파일(WIP)이 있는 상태에서 배포가 발화하면 `reset --hard`가 무경고로 폐기한다. "커밋된 작업만 push" 규율로만 완화되며, 도구적 가드는 없다.

### `deploy.sh` 단계 번호 불일치
`deploy.sh`의 로그가 `[1/3]`(`:34`), `[2/3]`(`:40`)로 시작했다가 `[3/4]`(`:45`), `[4/4]`(`:49`)로 바뀐다. 단계 추가 시 앞 번호를 갱신하지 않은 흔적으로, 기능엔 영향 없으나 손이 덜 닿은 신호.

### `inject_ko_names`를 15회 고정 재시도로 Neo4j 기동 대기
`deploy.sh:50-62`는 2초 간격 15회 루프로 Neo4j 준비를 폴링한다. 헬스체크 대신 고정 재시도라 기동이 약 30초보다 오래 걸리면 한글 이름 주입이 누락된다(단, 15회 모두 실패 시 `exit 1`로 배포를 중단하므로 "조용히 완료"되지는 않는다).

### Dockerfile이 `data/`를 복사하지 않음 — inject 스크립트가 호스트 직접 실행 + 마운트에 의존
`backend/Dockerfile:5`은 `COPY app/ ./app/`만 한다. `data/`는 이미지에 없고 `docker-compose.yml`의 `./data:/app/data` 볼륨 마운트(api 서비스)에 의존한다. `inject_ko_names.py:16`은 `Path(__file__).parent.parent.parent / "data" / "names_ko"`로 경로를 계산하는데, `deploy.sh:52`는 이 스크립트를 **호스트에서 직접**(`python3 .../inject_ko_names.py`) 실행한다. 적재 경로가 호스트 디렉터리 구조에 결합돼 있어 레이아웃이 바뀌면 조용히 깨진다.

## 보안 (잠재)

### Cypher 쿼리에 라벨/타입을 f-string으로 직접 보간 (잠재)
라벨/타입을 문자열 포매팅으로 쿼리에 끼워 넣는 지점들: `backend/app/main.py:16-17`(lifespan 인덱스, `f"CREATE INDEX {label.lower()}_tid ... FOR (n:{label}) ..."`), `backend/app/routes/nodes.py:147`(`f"... LIMIT {NODE_NEIGHBOR_LIMIT}"`), `backend/scripts/inject_ko_names.py:25-27`(`f"MATCH (p:{label} {{theographic_id: $id}}) ..."`). 보간되는 값이 모두 코드 내부 상수(라벨 화이트리스트 `['Person','Place','Event','PeopleGroup']`, 정수 상수)라 현재 주입 위험은 없다. 값 파라미터(`$id`, `$q`, `$ko`, `$alias`)는 모두 올바르게 바인딩되며 사용자 입력 경로는 안전하다. 외부 입력이 라벨/타입 경로로 흘러들 경우에만 취약해지는 잠재 구조.

### `MapView` 팝업 HTML 문자열 주입 (잠재)
`frontend/src/MapView.jsx:111-128`의 `.setHTML(...)`에 `${label}`(장소명 `nameKo`)과 `${typeLabel}`을 직접 보간한다. 장소명은 통제된 정적 데이터셋에서 오므로 현재 XSS 위험은 없으나, 이름 데이터가 외부 입력으로 확장될 경우에만 취약해지는 잠재 구조.

## 반복적으로 패치된 취약 영역 (커밋 히스토리 기준)

### GraphView 레이아웃/fit 타이밍 + 노드 변경마다 cy 전파괴·재생성
`frontend/src/GraphView.jsx`의 렌더링·fit 타이밍은 과거 다수 패치된 핫스팟이다. 현재 코드에도 fit 호출이 3곳에 분산돼 타이밍 의존이 남아 있다: `overlay` 변경 시 fit(`GraphView.jsx:32-35`), 초기 fit(`:153`), expand/collapse 후 fit(`:149-151`). 또한 메인 useEffect(`:37-158`)의 deps가 `[selectedNode, onSelectNode]`라 `selectedNode`가 바뀔 때마다 cleanup에서 `cy.destroy()`(`:157`)하고 두 번의 fetch(`:42-45`) 후 cytoscape 인스턴스를 통째로 재생성하며 `expandCollapse`/`collapseAll`(`:137-143`)을 다시 초기화한다. 노드 전환이 잦으면 매번 cose-bilkent 레이아웃을 재계산해 비용이 크다. 이 둘은 같은 뿌리의 부채.

### `MapView` 비동기 fetch 경쟁 조건 가드 (잔재)
`frontend/src/MapView.jsx:178`의 `if (mapRef.current === map)` 및 `:191`의 동일 가드는 과거 경쟁 조건 패치의 잔재로, 비동기 fetch 응답이 맵 재생성 이후 도착하는 케이스를 방어한다(추가로 `AbortController` `:173,194`도 함께 사용). 맵 재생성 트리거(`onSelectNode` deps, `:160`)가 바뀌면 다시 깨질 수 있는 영역.

## 버그 가능성 / 취약한 로직

### `/events`의 sortKey 무가드 `float()` 파싱
`backend/app/routes/events.py:24`는 `float(props.get("sortKey", 0))`를 try/except 없이 호출한다. `nodes.py`의 좌표 파싱(`nodes.py:74-78`)은 try/except로 견고화됐으나 `events.py`의 sortKey 파싱에는 같은 가드가 없다. 데이터에 숫자 파싱 불가능한 `sortKey`가 섞이면 `/events` 요청 전체가 500으로 실패한다. 현재 데이터는 정상이라 잠재적이며, 좌표 견고화와 짝이 안 맞는 비대칭.

### `/node/{id}/places`가 빈 배열일 때 무피드백
`backend/app/routes/nodes.py:9-87`은 노드가 없으면 404(`:18-19`)를 반환하지만, 노드는 있으나 연결된 장소가 없으면 빈 리스트를 반환한다. 프론트(`MapView.jsx:181`)는 `places.length > 0`만 확인해 빈 결과를 조용히 처리하므로 "선택했는데 지도에 아무것도 안 뜬다"는 무피드백 상태가 발생할 수 있다(이 클래스 버그가 `26240c7`에서 PeopleGroup 경로에 대해 실제로 수정된 전례 있음).

### 좌표 누락 노드의 무음 스킵 (의도된 동작이나 사용자엔 무피드백)
`backend/app/routes/nodes.py:74-78`은 위경도 `float()` 파싱 실패 시 해당 장소를 `continue`로 건너뛴다(요청은 500 없이 성공). 견고화 자체는 의도된 동작이지만, 스킵된 장소에 대한 사용자/로그 피드백이 전혀 없어 "일부 마커가 조용히 누락"될 수 있다.

## 성능

### 전체 노드 스캔 검색 (인덱스 미사용) — 의도적으로 받아들인 결정
`backend/app/routes/search.py:14-23`의 검색은 `MATCH (n) WHERE (n.nameKo CONTAINS $q OR n.name CONTAINS $q)`로 전체 노드를 풀스캔한다. 생성되는 인덱스(`main.py:16-17`)는 `theographic_id` 단일 키라 이 `CONTAINS` 검색을 가속하지 못하며 풀텍스트 인덱스는 없다. **다만 데이터셋이 정적 ~930개 노드 규모라 실질적 성능 문제가 아니다.** 선행 작업에서 풀텍스트 인덱스 추가를 "조숙한 최적화"로 판단해 의도적으로 드롭했다. 긴급 부채가 아니라 기록용 결정 사항.

## 기타 견고성

### MapView 외부 타일/폰트 서버 의존 — 폴백 없음
`frontend/src/MapView.jsx:34`(protomaps 폰트 glyphs, `protomaps.github.io/...`), `:39`(ArcGIS NatGeo 타일, `server.arcgisonline.com/...`)가 외부 서비스에 하드코딩돼 있다. 해당 서비스 다운·정책 변경·요청 제한 시 지도가 깨진다. 폴백이 없다.

### 이웃 컷 매직 넘버로 인한 무음 누락
이웃 제한은 `nodes.py:6-7`의 `MAX_NEIGHBORS_PER_TYPE = 30`, `NODE_NEIGHBOR_LIMIT = 50` 상수로 추출돼 매직 넘버 자체는 정리됐다. 다만 큰 허브 노드(예: 다윗, 예수)는 타입별 30개 컷(`nodes.py:108`)과 LIMIT 50(`nodes.py:147`)으로 인해 일부 이웃이 조용히 누락되며, 사용자에게 "더 있음" 표시가 없다.

### GraphView 기본 노드 하드코딩
`frontend/src/GraphView.jsx:9` `DEFAULT_NODE = 'recjNRR60PAuFtjha' // 모세`로 모세의 theographic_id가 박혀 있다. 데이터 재적재 시 이 ID가 바뀌면 그래프 초기 화면이 빈 상태(혹은 fetch 실패 → 에러 UI)가 된다.

## 해소 확인 (직전 맵 `60962d0` 대비 — 더 이상 열린 이슈 아님)

직전 CONCERNS에 열린 이슈로 있었으나 HEAD `60716ea`에서 해소된 항목들. 검증 결과만 남긴다.

- **CI 배포가 제거된 워크트리 절대 경로에 하드코딩** → 해소. `.github/workflows/deploy.yml:13`이 `cd /Users/calmonion/Project/BibleMap`(메인 레포)로 수정되어 push→deploy가 동작(`1f0e772`, `60716ea`). (단, 동일 레포 `git reset --hard`로 인한 WIP 폐기 리스크는 위 "설정/배포 부채"에 별도 기록.)
- **`scripts/auto-deploy-poll.sh` (낡은 경로/머지된 브랜치 폴링)** → 해소. 파일이 제거됨(`scripts/` 디렉터리 자체가 없고 `git ls-files scripts/`가 0건, `1f0e772`).
- **프론트엔드 fetch 실패의 무음 처리 / 에러 UI 부재** → 해소. 모든 뷰가 한글 에러 UI를 노출(`b75b1c5`): `App.jsx:30-39`(검색, `searchError` 상태 → `:114-115` "검색에 실패했습니다"), `MapView.jsx:190-191`(`setError(true)` → `:200-208` "장소를 불러오지 못했습니다"), `TimelineView.jsx:25`(`setError(true)` → `:58-64` "사건을 불러오지 못했습니다"), `GraphView.jsx:155`(`setError(true)` → `:164-172` "그래프를 불러오지 못했습니다"). `SidePanel.jsx:31,36`도 `error` 상태를 화면에 노출.
- **CORS 전체 개방 + credentials 조합** → 해소(유지). `backend/app/main.py:27-29`이 `allow_credentials=False`, `allow_methods=["GET"]`.
- **기본 Neo4j 비밀번호 하드코딩** → 해소(유지). `backend/app/db.py:11-13`, `inject_ko_names.py:12-14` 모두 `NEO4J_PASSWORD` 미설정 시 `RuntimeError` fail-fast. `docker-compose.yml`은 `${NEO4J_PASSWORD:?...}`를 쓰고 `NEO4J_AUTH`를 거기서 파생.
- **lifespan 인덱스 `except Exception: pass` 무음 삼킴** → 해소(유지). `main.py:19-20`이 `logging.exception(...)`으로 로깅.
- **TimelineView 정렬 키 타입 혼합** → 해소(유지). `TimelineView.jsx:48`이 `members[0].sortKey ?? 0`(숫자 폴백)으로 일원화.
- **좌표 `float()` 무가드 파싱** → `nodes.py:74-78`에서 try/except로 견고화(깨진 좌표는 해당 장소만 스킵, 500 없음). 단, `events.py:24` sortKey 파싱에는 동일 가드가 없어 위 "버그 가능성"에 별도 기록.
