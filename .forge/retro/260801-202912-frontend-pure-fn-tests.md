# 2026-08-01 — 프론트 순수 함수 3모듈에 vitest 도입, 배포 게이트에 배선 (task#261)

## 계획 대비 실제

- **계획대로**: 6슬라이스 전부. vitest devDependency 한 줄 + `"test": "vitest run"`(**config 파일 0개** — 기본 node 환경으로 충분,
  계획이 허용한 "더 게으른 쪽") · `urlState` 27건 · `mapGeo` 38건(11 export 전수, 빌더마다 빈 입력 케이스) ·
  `mapRingController` 8건 · `check.sh` 배선 · 문서 갱신 · 커밋 `55158cd`. **대상 3모듈 소스는 한 줄도 안 바꿨다**(비목표 준수).
- **갈린 점**
  1. `mapGeo.js`가 `maplibre-gl`을 정적 import해 node 환경에서 깨질까 봐 먼저 확인했는데 정상 import됐다 —
     `vi.mock` 스텁 없이 `coreBounds`의 실제 `LngLatBounds`를 `getWest/getEast/...`로 단언할 수 있었다.
  2. **`mapRingController`에 "순수한 부분"이 사실상 없었다** — 유일한 export가 맵 인스턴스·`requestAnimationFrame`·
     `performance.now`·`apiGet`에 묶인 클로저 팩토리다.
  3. `check.sh`에 블록을 새로 만들지 않고 ESLint 블록을 확장했다(둘 다 같은 `node_modules` 가드가 필요).
  4. 테스트 설명 두 곳의 방위 서술을 실행 후 정정했다 — `ringPositions`의 첫 좌표는 `lat − R`이라 화면상 아래(6시)인데 "12시"라 적었다.

## 학습

- **다음에 다르게 할 것**
  - **순수부가 없는 모듈도 "무엇을 하지 않는가"는 단언할 수 있다.** `getSource`/`project`를 호출하면 **예외를 던지는 맵 스텁**을 주면,
    "펼쳐진 것이 없을 때 collapse는 맵을 건드리지 않는다"가 검증 가능한 사실이 된다 — 단순 no-throw 테스트보다 훨씬 강하고,
    목킹 라이브러리도 타이머 하네스도 필요 없다. 클로저 팩토리엔 이 패턴을 먼저 시도할 것.
  - **테스트를 못 쓰는 부분은 사유와 함께 파일 상단에 적어라.** "왜 안 덮었는지"가 없으면 다음 사람이 커버리지 구멍으로 읽고
    불필요한 목킹 인프라를 새로 만든다.
  - **vite가 있으면 vitest 도입 비용은 사실상 0이다** — devDependency 한 줄, config 파일 없음, node 환경 기본값.
    "테스트 인프라가 없어서"는 이 스택에서 더 이상 미도입 사유가 못 된다(백엔드 pytest 미도입은 별개 사유 — ADR `260801-195023`).
  - **`toMatchObject`로 왕복 대칭을 검사하라.** `parseHash`가 항상 `personSlug`/`tourSlug`/`exploreView`를 채워 돌려주므로
    `toEqual`은 입력에 없던 필드 때문에 전부 실패한다. 입력이 명시한 필드만 대조하는 게 맞다.
  - **좌표계 서술은 실행 후 다시 읽어라.** 단언이 통과해도 설명이 반대면 다음 사람이 거꾸로 읽는다(`lat − R`은 화면상 아래).

## 문서 갱신

- CONTEXT.md 승급: 없음 (테스트 기법·인프라 세부 — `codebase/TESTING.md` §0에 실태로 기록)
- ADR 추가: 없음 (`260801-195023-no-backend-unit-tests`는 fg-ask 단계에서 이미 기록됨)
