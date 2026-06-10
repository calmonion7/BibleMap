---
last_mapped_commit: 26240c7cf18f421b2f8baa4fd6584f40eede57b0
mapped: 2026-06-11
---

# 기술 부채 · 알려진 이슈 · 리스크 영역

## 보안

### CORS 전체 개방 + credentials 허용 조합
`backend/app/main.py:24-30`에서 `allow_origins=["*"]`와 `allow_credentials=True`를 함께 설정한다. 이 조합은 브라우저 스펙상 무효(쿠키/인증정보가 와일드카드 origin에 전송되지 않음)이며, 동시에 모든 출처에서의 API 호출을 허용한다. 인증 자체가 없는 읽기 전용 API라 현재는 위험도가 낮지만, 설정이 의도와 어긋난 상태다.

### 기본 Neo4j 비밀번호가 코드 곳곳에 하드코딩
`biblemap123`이 fallback 비밀번호로 4곳에 박혀 있다: `backend/app/db.py:11`, `backend/scripts/load_theographic.py:9`, `backend/scripts/inject_ko_names.py:12`, `docker-compose.yml:10,18`. 운영에서 환경변수를 누락하면 약한 기본 비밀번호로 조용히 동작한다. `.env`(gitignore됨, 로컬에 존재)에도 동일한 `NEO4J_AUTH=neo4j/biblemap123`가 들어 있다.

### Cypher 쿼리에 라벨을 f-string으로 직접 보간
`backend/app/main.py:14-17`(인덱스 생성)과 `backend/scripts/inject_ko_names.py:23`(`f"MATCH (p:{label} ...)"`)에서 라벨을 문자열 포매팅으로 쿼리에 끼워 넣는다. 값은 모두 코드 내부 상수라 현재는 주입 위험이 없지만, 외부 입력이 라벨 경로로 흘러들 경우 취약해질 구조다. 값 파라미터(`$id`, `$q` 등)는 올바르게 바인딩되고 있어 사용자 입력 경로는 안전하다.

## 반복적으로 패치된 취약 영역 (커밋 히스토리 기준)

전체 22개 커밋 중 12개가 `fix:` 커밋이다. 특정 영역이 집중적으로 재작업됐다.

### GraphView 레이아웃/fit 타이밍 — 최소 8회 패치
`frontend/src/GraphView.jsx`의 렌더링·fit 타이밍이 반복적으로 깨졌다: `02473c1`(cy.resize+fit), `e69af6b`(concentric fit+padding, setTimeout), `dc4d874`(preset 레이아웃으로 교체), `8d8c4da`/`bd41423`(범례 토글 추가→완전 제거), `0ee7668`(#root 리셋), `e7b2f49`(오버레이 시 cy.fit 재조정), `e32e424`(GroupParent 탭 가드 + expand 후 re-fit), `26240c7`(MEMBER_OF 경로). 현재 코드에도 `overlay` 변경 시 fit(`GraphView.jsx:31-34`), 초기 fit(`:150`), expand/collapse 후 fit(`:146-148`) 등 fit 호출이 3곳에 분산돼 있어 타이밍 의존이 여전히 남아 있다.

### MapView 마커 클릭/경쟁 조건 — 3회 패치
`1d00870`(마커 클릭 시 점 사라짐), `1cfe47c`(경쟁 조건 + case 표현식 명시적 boolean 비교), `1c3795e`(관련 장소 관계 방향). `frontend/src/MapView.jsx:184`의 `if (mapRef.current === map)` 가드는 이 경쟁 조건 패치의 잔재로, 비동기 fetch 응답이 맵 재생성 이후 도착하는 케이스를 방어한다.

## 버그 가능성 / 취약한 로직

### TimelineView 정렬 키의 타입 혼합
`frontend/src/TimelineView.jsx:47`에서 `const sortKey = members[0].sortKey ?? startDate`로 정렬 키를 정하는데, `sortKey`는 백엔드에서 숫자(`events.py:24` `float(...)`)이고 `startDate`는 문자열이다. `sortKey`가 falsy가 아닌 `null/undefined`일 때만 `startDate`로 폴백하므로 보통은 숫자끼리 비교되지만, 일부 그룹만 `startDate`(문자열) 폴백이 발생하면 `:52-53`의 `<`/`>` 비교가 숫자와 문자열을 섞어 비교해 정렬이 어긋날 수 있다.

### 좌표 누락 노드의 무음 폴백
`backend/app/routes/places.py:24-25`, `backend/app/routes/nodes.py:75-76`에서 `float(props.get("latitude", 0))`로 위경도를 읽는다. 쿼리 단계에서 `latitude/longitude IS NOT NULL`을 거르므로 정상 경로에선 0이 나오지 않지만, 값이 숫자 파싱 불가능한 문자열일 경우 `float()`가 예외를 던지며 요청 전체가 500으로 실패한다.

### `/node/{id}/places`는 존재하지 않는 노드에 404를 던지나, places 자체가 없으면 빈 배열
`backend/app/routes/nodes.py:14-16`은 노드가 없으면 404를 반환하지만, 노드는 있으나 연결된 장소가 없으면 빈 리스트를 반환한다. 프론트(`MapView.jsx:186`)는 `places.length > 0`만 확인해 빈 결과를 조용히 처리하므로, "선택했는데 지도에 아무것도 안 뜬다"는 무피드백 상태가 발생할 수 있다. (이 클래스의 버그가 `26240c7`에서 PeopleGroup에 대해 실제로 수정됐다.)

## 누락된 에러 처리

### lifespan 인덱스 생성의 광범위 except 삼킴
`backend/app/main.py:18`의 `except Exception: pass`는 인덱스 생성 실패를 완전히 무음 처리한다. Neo4j 미기동·인증 실패 등 어떤 원인이든 로그 한 줄 없이 넘어가, 인덱스 없이 앱이 떠서 쿼리 성능이 조용히 저하될 수 있다.

### 프론트엔드 fetch 실패의 무음 처리
모든 뷰가 `.catch(() => {})`로 네트워크 오류를 삼킨다: `frontend/src/App.jsx:27-33`(검색은 catch조차 없어 미처리 rejection 발생 가능), `MapView.jsx:195`, `TimelineView.jsx:24`, `GraphView.jsx:152`. 사용자에게 표시되는 에러 UI가 없는 곳이 대부분이다. `SidePanel.jsx:31`만 유일하게 `error` 상태를 화면에 노출한다.

### App.jsx 검색 핸들러의 미처리 reject
`frontend/src/App.jsx:27-33` `handleSearch`는 `await fetch(...)`에 try/catch가 없다. API 장애 시 unhandled rejection이 발생한다.

## 성능

### 전체 노드 스캔 검색 (인덱스 미사용)
`backend/app/routes/search.py:12-20`의 검색은 `MATCH (n) WHERE n.nameKo CONTAINS $q OR n.name CONTAINS $q`로 전체 노드를 풀스캔한다. 생성되는 인덱스(`main.py:13` / `load_theographic.py:35-38`)는 `theographic_id` 단일 키 인덱스라 이 `CONTAINS` 검색을 가속하지 못한다. 데이터 규모가 커지면 검색 지연이 선형 증가한다. 풀텍스트 인덱스가 없다.

### `/places`는 좌표 있는 모든 장소를 무제한 반환
`backend/app/routes/places.py:10-11`에 LIMIT이 없어 좌표를 가진 전체 Place를 한 번에 반환한다. (현재 이 엔드포인트를 호출하는 프론트 코드는 확인되지 않아 데드 가능성 있음 — 아래 참조.)

### GraphView가 노드 변경마다 cytoscape 인스턴스를 전파괴·재생성
`frontend/src/GraphView.jsx:36-155` useEffect는 `selectedNode`가 바뀔 때마다 cy 인스턴스를 `destroy()`하고 두 번의 fetch 후 통째로 새로 만든다. 노드 전환이 잦으면 매번 레이아웃(cose-bilkent)을 다시 계산해 비용이 크다.

## 설정 / 배포 부채

### Dockerfile이 `data/`를 복사하지 않음 — inject 스크립트는 호스트 마운트에 의존
`backend/Dockerfile:5`은 `COPY app/ ./app/`만 한다. `data/`는 이미지에 없고, `docker-compose.yml:19-20`의 `./data:/app/data` 볼륨 마운트에 의존한다. `inject_ko_names.py:14`는 `Path(__file__).parent.parent.parent / "data" / "names_ko"`로 경로를 계산하는데, `deploy.sh:41`은 이 스크립트를 **호스트에서 직접**(`python3 .../inject_ko_names.py`) 실행한다. 즉 적재 경로가 컨테이너 내부 구조와 호스트 디렉터리 구조 양쪽에 동시에 결합돼 있어, 어느 한쪽 레이아웃이 바뀌면 조용히 깨진다.

### CI 워크플로우가 특정 사용자 절대 경로에 하드코딩
`.github/workflows/deploy.yml:13`은 `/Users/calmonion/Project/BibleMap/.claude/worktrees/wise-sprouting-hellman`라는 특정 머신·워크트리 경로에 묶여 있다. self-hosted 러너 환경이 바뀌면 배포가 깨진다. `git reset --hard origin/main`은 러너 측 로컬 변경을 무경고로 폐기한다.

### deploy.sh 단계 번호 불일치
`deploy.sh`의 로그가 `[1/3]`, `[2/3]`으로 시작했다가 `[3/4]`, `[4/4]`로 바뀐다(`:24,30,35,39`). 단계 추가 시 앞 번호를 갱신하지 않은 흔적으로, 기능엔 영향 없으나 손이 닿은 곳이 덜 정리된 신호다.

### inject_ko_names를 15회 재시도로 Neo4j 기동 대기
`deploy.sh:40-44`은 2초 간격 15회 루프로 Neo4j 준비를 폴링한다. 헬스체크 대신 고정 재시도라, 기동이 30초보다 오래 걸리면 한글 이름 주입이 누락된 채 "완료" 로그가 찍힌다(`break` 실패해도 루프를 빠져나와 다음 로그로 진행).

## 데드/미사용 코드

### `d3` 의존성 미사용
`frontend/package.json`에 `d3 ^7.9.0`가 의존성으로 있으나 `frontend/src` 전체에 import가 없다. 번들·설치 비용만 발생.

### `/places` 엔드포인트 호출처 불명
`backend/app/routes/places.py`의 `GET /places`를 호출하는 프론트 코드가 확인되지 않는다(MapView는 `/node/{id}/places`만 사용). 초기 전체 마커 표시용으로 추정되나 현재 미사용으로 보임 — 삭제 전 호출처 재확인 필요.

### MapView의 사용되지 않는 prop
`frontend/src/MapView.jsx:27`이 `selectedNodeLabel` prop을 받지만 컴포넌트 본문에서 쓰지 않으며, `App.jsx:137`도 이 prop을 넘기지 않는다.

### 빌드 산출물이 git에 커밋됨
`.gitignore`에 `frontend/dist/`가 있으나 `frontend/dist/`(index.html, assets/index-*.js/css 등)가 리포지터리에 추적된 채 남아 있다. 소스와 산출물이 어긋날 수 있는 상태.

## 기타 견고성

### MapView 외부 타일/폰트 서버 의존
`frontend/src/MapView.jsx:40`(protomaps 폰트 glyphs), `:45`(ArcGIS NatGeo 타일)가 외부 서비스에 하드코딩돼 있다. 해당 서비스 다운·정책 변경·요청 제한 시 지도가 깨진다. 폴백 없음.

### 검색 결과 매직 넘버 / 이웃 제한
`backend/app/routes/search.py:18` `LIMIT 20`, `nodes.py:100` 타입별 `>= 30` 컷, `nodes.py:139` `LIMIT 50`이 코드에 상수로 박혀 있다. 큰 허브 노드(예: 다윗, 예수)는 이 컷으로 인해 일부 이웃이 조용히 누락된다.

### GraphView 기본 노드 하드코딩
`frontend/src/GraphView.jsx:9` `DEFAULT_NODE = 'recjNRR60PAuFtjha' // 모세`로 모세의 theographic_id가 박혀 있다. 데이터 재적재 시 이 ID가 바뀌면 그래프 초기 화면이 빈 상태가 된다.
