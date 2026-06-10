---
last_mapped_commit: 60962d0693f3bfaf4b8d24ce6f97d7b392770d85
mapped: 2026-06-11
---

# 기술 부채 · 알려진 이슈 · 리스크 영역

직전 맵(`26240c7`) 이후 보안·설정·데드코드 항목 다수가 정리되었다. 이 문서는 HEAD `60962d0` 기준으로 **현재도 남아 있는** 항목만 기록한다. 이미 해소된 항목은 맨 아래 "해소 확인" 절에 검증 결과만 남긴다.

## 보안

### Cypher 쿼리에 라벨을 f-string으로 직접 보간 (잠재)
`backend/app/main.py:16-17`(lifespan 인덱스 생성, `f"CREATE INDEX {label.lower()}_tid ... FOR (n:{label}) ..."`)와 `backend/scripts/inject_ko_names.py:25-27`(`f"MATCH (p:{label} {{theographic_id: $id}}) ..."`)에서 라벨을 문자열 포매팅으로 쿼리에 끼워 넣는다. 두 경우 모두 보간되는 값이 코드 내부 상수 리스트(`['Person', 'Place', 'Event', 'PeopleGroup']`)라 현재 주입 위험은 없다. 값 파라미터(`$id`, `$q`, `$ko` 등)는 모두 올바르게 바인딩되며 사용자 입력 경로는 안전하다. 외부 입력이 라벨 경로로 흘러들 경우에만 취약해지는 잠재 구조로, 지금은 액션이 필요 없다.

## 반복적으로 패치된 취약 영역 (커밋 히스토리 기준)

### GraphView 레이아웃/fit 타이밍 — 최소 8~9회 패치
`frontend/src/GraphView.jsx`의 렌더링·fit 타이밍이 반복적으로 깨졌다. `git log -- frontend/src/GraphView.jsx`가 10개 커밋을 반환하며 그중 fix가 다수다: `02473c1`(cy.resize+fit), `e69af6b`(concentric fit+padding, setTimeout), `dc4d874`(preset 레이아웃으로 교체), `8d8c4da`/`bd41423`(범례 토글 추가→완전 제거), `0ee7668`(#root 리셋), `e7b2f49`(오버레이 시 cy.fit 재조정), `e32e424`(GroupParent 탭 가드 + expand 후 re-fit). 현재 코드에도 fit 호출이 3곳에 분산돼 있어 타이밍 의존이 남아 있다: `overlay` 변경 시 fit(`GraphView.jsx:31-34`), 초기 fit(`:150`), expand/collapse 후 fit(`:146-148`). 이 영역은 향후 변경 시 깨지기 쉬운 핫스팟이다.

### GraphView가 노드 변경마다 cytoscape 인스턴스를 전파괴·재생성
`frontend/src/GraphView.jsx:36-155`의 useEffect는 deps가 `[selectedNode, onSelectNode]`로, `selectedNode`가 바뀔 때마다 cy 인스턴스를 cleanup에서 `destroy()`(`:154`)하고 두 번의 fetch(`:40-43`) 후 통째로 새로 만든다. 노드 전환이 잦으면 매번 cose-bilkent 레이아웃을 재계산하고 expand/collapse를 다시 초기화(`:134-141`)해 비용이 크다. 위의 fit 타이밍 부채와 같은 뿌리다.

### MapView 마커 클릭/경쟁 조건 — 3회 패치
`1d00870`(마커 클릭 시 점 사라짐), `1cfe47c`(경쟁 조건 + case 표현식 명시적 boolean 비교), `1c3795e`(Person 관련 장소 관계 방향). `frontend/src/MapView.jsx:177`의 `if (mapRef.current === map)` 가드는 이 경쟁 조건 패치의 잔재로, 비동기 fetch 응답이 맵 재생성 이후 도착하는 케이스를 방어한다. (`git log -- frontend/src/MapView.jsx` 기준 7개 커밋.)

## 버그 가능성 / 취약한 로직

### `/events`의 sortKey 무가드 float 파싱
`backend/app/routes/events.py:24`는 `float(props.get("sortKey", 0))`를 try/except 없이 호출한다. `nodes.py`의 좌표 파싱은 `60962d0` 이전 작업에서 try/except로 견고화됐으나(`nodes.py:74-78`), `events.py`의 sortKey 파싱에는 같은 가드가 없다. 데이터에 숫자 파싱 불가능한 `sortKey`가 섞이면 `/events` 요청 전체가 500으로 실패한다. 현재 데이터는 정상이라 잠재적이며, 좌표 견고화와 짝이 맞지 않는 비대칭이 남아 있다.

### `/node/{id}/places`가 빈 배열일 때 무피드백
`backend/app/routes/nodes.py:9-87`은 노드가 없으면 404(`:19`)를 반환하지만, 노드는 있으나 연결된 장소가 없으면 빈 리스트를 반환한다. 프론트(`MapView.jsx:179`)는 `places.length > 0`만 확인해 빈 결과를 조용히 처리하므로, "선택했는데 지도에 아무것도 안 뜬다"는 무피드백 상태가 발생할 수 있다. (이 클래스의 버그가 `26240c7`에서 PeopleGroup 경로에 대해 실제로 수정된 전례가 있다.)

### 좌표 누락 노드의 무음 스킵 (의도된 동작이나 사용자엔 무피드백)
`backend/app/routes/nodes.py:74-78`은 위경도 `float()` 파싱 실패 시 해당 장소를 `continue`로 건너뛴다(요청은 500 없이 성공). 견고화 자체는 의도된 동작이지만, 스킵된 장소에 대한 사용자/로그 피드백이 전혀 없어 "일부 마커가 조용히 누락"될 수 있다.

## 누락된 에러 처리

### 프론트엔드 fetch 실패의 무음 처리 / 에러 UI 부재
대부분의 뷰가 네트워크 오류를 화면 피드백 없이 삼킨다: `frontend/src/App.jsx:33`(검색, try/catch로 결과를 빈 배열로만 리셋), `MapView.jsx:188`(`.catch(() => {})`), `TimelineView.jsx:24`(`.catch(() => {})`), `GraphView.jsx:152`(`.catch(() => {})`). `SidePanel.jsx:31,36`만 유일하게 `error` 상태를 화면에 노출한다. API 장애 시 사용자는 빈 화면/무반응만 보게 된다.

## 성능

### 전체 노드 스캔 검색 (인덱스 미사용) — 의도적으로 받아들인 결정
`backend/app/routes/search.py:14-22`의 검색은 `MATCH (n) WHERE (n.nameKo CONTAINS $q OR n.name CONTAINS $q)`로 전체 노드를 풀스캔한다. 생성되는 인덱스(`main.py:16-17`, `load_theographic.py:37-40`)는 `theographic_id` 단일 키라 이 `CONTAINS` 검색을 가속하지 못하며 풀텍스트 인덱스는 없다. **다만 데이터셋이 정적 ~930개 노드 규모라 실질적 성능 문제가 아니다.** 선행 작업에서 풀텍스트 인덱스 추가를 "조숙한 최적화"로 판단해 의도적으로 드롭했다. 긴급 부채가 아니라 기록용 결정 사항으로 둔다.

## 설정 / 배포 부채

### CI 워크플로우가 특정 사용자·워크트리 절대 경로에 하드코딩
`.github/workflows/deploy.yml:13`은 `/Users/calmonion/Project/BibleMap/.claude/worktrees/wise-sprouting-hellman`라는 특정 머신·워크트리 경로에 묶여 있다. self-hosted 러너 환경/워크트리가 바뀌면 배포가 깨진다. `:15`의 `git reset --hard origin/main`은 러너 측 로컬 변경을 무경고로 폐기한다.

### auto-deploy-poll.sh도 동일한 하드코딩 + 머지된 브랜치 폴링
`scripts/auto-deploy-poll.sh:6-7`은 같은 워크트리 절대 경로와 `worktree-wise-sprouting-hellman` 브랜치를 폴링한다. 이 브랜치는 이미 `a66b239`에서 main으로 머지됐으므로, 폴러가 main이 아닌 (이제는 보조적인) 브랜치를 추적하는 상태다. `:33`도 `git reset --hard`로 로컬 변경을 무경고 폐기한다.

### deploy.sh 단계 번호 불일치
`deploy.sh`의 로그가 `[1/3]`(`:29`), `[2/3]`(`:35`)로 시작했다가 `[3/4]`(`:40`), `[4/4]`(`:44`)로 바뀐다. 단계 추가 시 앞 번호를 갱신하지 않은 흔적으로, 기능엔 영향 없으나 손이 덜 닿은 신호다.

### inject_ko_names를 15회 고정 재시도로 Neo4j 기동 대기
`deploy.sh:45-57`은 2초 간격 15회 루프로 Neo4j 준비를 폴링한다. 헬스체크 대신 고정 재시도라, 기동이 약 30초보다 오래 걸리면 한글 이름 주입이 누락된다. (단, 현재 구현은 15회 모두 실패 시 `exit 1`로 배포를 중단하므로 "조용히 완료"되지는 않는다.)

### Dockerfile이 `data/`를 복사하지 않음 — inject 스크립트가 호스트 마운트에 의존
`backend/Dockerfile:5`은 `COPY app/ ./app/`만 한다. `data/`는 이미지에 없고 `docker-compose.yml:19-20`의 `./data:/app/data` 볼륨 마운트에 의존한다. `inject_ko_names.py:16`은 `Path(__file__).parent.parent.parent / "data" / "names_ko"`로 경로를 계산하는데, `deploy.sh:47`은 이 스크립트를 **호스트에서 직접**(`python3 .../inject_ko_names.py`) 실행한다. 적재 경로가 컨테이너 내부 구조와 호스트 디렉터리 구조 양쪽에 동시에 결합돼 있어, 어느 한쪽 레이아웃이 바뀌면 조용히 깨진다.

## 기타 견고성

### MapView 외부 타일/폰트 서버 의존 — 폴백 없음
`frontend/src/MapView.jsx:33`(protomaps 폰트 glyphs, `protomaps.github.io/...`), `:38`(ArcGIS NatGeo 타일, `server.arcgisonline.com/...`)가 외부 서비스에 하드코딩돼 있다. 해당 서비스 다운·정책 변경·요청 제한 시 지도가 깨진다. 폴백이 없다.

### 이웃 컷 매직 넘버로 인한 무음 누락
검색 LIMIT은 `search.py:6`의 `SEARCH_LIMIT = 20` 상수로 추출됐고, 이웃 제한도 `nodes.py:6-7`의 `MAX_NEIGHBORS_PER_TYPE = 30`, `NODE_NEIGHBOR_LIMIT = 50` 상수로 정리됐다(매직 넘버 자체는 해소). 다만 큰 허브 노드(예: 다윗, 예수)는 타입별 30개 컷(`nodes.py:108`)과 LIMIT 50(`nodes.py:147`)으로 인해 일부 이웃이 조용히 누락되며, 사용자에게 "더 있음" 표시가 없다.

### GraphView 기본 노드 하드코딩
`frontend/src/GraphView.jsx:9` `DEFAULT_NODE = 'recjNRR60PAuFtjha' // 모세`로 모세의 theographic_id가 박혀 있다. 데이터 재적재 시 이 ID가 바뀌면 그래프 초기 화면이 빈 상태가 된다.

### MapView 팝업 HTML 문자열 주입 (잠재)
`frontend/src/MapView.jsx:110-127`의 `setHTML(...)`에 `${label}`(장소명, `nameKo`)을 직접 보간한다. 장소명은 통제된 정적 데이터셋에서 오므로 현재 XSS 위험은 없으나, 이름 데이터가 외부 입력으로 확장될 경우에만 취약해지는 잠재 구조다.

## 해소 확인 (직전 맵 대비 — 더 이상 열린 이슈 아님)

직전 CONCERNS(`26240c7`)에 있었으나 HEAD `60962d0`에서 해소되어 **열린 이슈로 나열하지 않는** 항목들. 검증 결과만 남긴다.

- **CORS 전체 개방 + credentials 조합** → 해소. `backend/app/main.py:25-31`이 `allow_credentials=False`, `allow_methods=["GET"]`로 변경됨(`22b1899`).
- **기본 Neo4j 비밀번호 하드코딩(4곳)** → 해소. `backend/app/db.py:11-13`, `load_theographic.py:9-11`, `inject_ko_names.py:12-14` 모두 `NEO4J_PASSWORD` 미설정 시 `RuntimeError` fail-fast. `docker-compose.yml:10,18`은 `${NEO4J_PASSWORD:?...}`를 쓰고 `NEO4J_AUTH`를 거기서 파생(`60962d0`).
- **`d3` 미사용 의존성** → 해소. `frontend/package.json`에서 제거됨(`5080500`).
- **데드 `GET /places` 엔드포인트** → 해소. `places.py` 라우트 파일이 없고 `nodes.py`/`search.py`/`events.py` 어디에도 `/places` 라우트가 없음(장소 로직은 `/node/{id}/places`로만 존재).
- **`MapView` 미사용 `selectedNodeLabel` prop** → 해소. `MapView.jsx:20` 시그니처가 `{ onSelectNode, selectedNode }`로 정리됨(`5080500`).
- **lifespan 인덱스 `except Exception: pass` 무음 삼킴** → 해소. `main.py:19-20`이 `logging.exception(...)`으로 로깅(`34bee1d`).
- **App.jsx 검색 핸들러 미처리 reject** → 해소. `App.jsx:29-37`에 try/catch 추가(`a111578`).
- **TimelineView 정렬 키 타입 혼합** → 해소. `TimelineView.jsx:47`이 `members[0].sortKey ?? 0`(숫자 폴백)으로 일원화(`b7928de`).
- **검색/이웃 매직 넘버** → 해소. `SEARCH_LIMIT`(`search.py:6`), `MAX_NEIGHBORS_PER_TYPE`·`NODE_NEIGHBOR_LIMIT`(`nodes.py:6-7`)로 추출(`6ceb3fb`). (단, 컷으로 인한 무음 누락 자체는 위 "기타 견고성"에 별도 기록.)
- **좌표 `float()` 무가드 파싱** → `nodes.py:74-78`에서 try/except로 견고화(깨진 좌표는 해당 장소만 스킵, 500 없음)(`6ceb3fb`). (단, `events.py:24` sortKey 파싱에는 동일 가드가 없어 위 "버그 가능성"에 별도 기록.)
- **빌드 산출물 git 추적(`frontend/dist/`)** → 해소(또는 직전 맵의 오기록). `git ls-files`에 `frontend/dist/` 항목이 0개이며, 로컬에는 untracked로만 존재. `.gitignore:9`의 `frontend/dist/`가 정상 적용됨.
- **`.pyc`/`__pycache__` 추적** → 추적 항목 0개. `.gitignore:1-3` 정상 적용. (`backend/app/__pycache__/` 등은 로컬 untracked.)
