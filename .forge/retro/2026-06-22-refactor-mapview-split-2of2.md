# 2026-06-22 — MapView 분할 2/2 애니메이션 컨트롤러 추출 (task 83, part 2/2)

## Plan vs actual
- What went as planned: 4개 애니메이션 클로저 + 공유 가변 상태를 `createRingController(map, {expandedPlaceRef, setError})`(`mapRingController.js`, 163줄)로 추출, init effect 얇아짐(`const ring = ...` + `ring.destroy()`). MapView.jsx 341→193줄. 팩토리 형태(계획 권장) 그대로. 전체 Playwright 회귀 PASS. 발산 낮음.
- Divergences: 없음(범위·접근 계획대로).

## Learnings
- Do differently next time:
  1. **컴포넌트 ref를 alias로 쓰던 클로저를 추출할 때, 컴포넌트에 남은 alias 참조를 ref로 바꿔야 한다.** init effect 안 `const expandedPlace = expandedPlaceRef`를 컨트롤러로 옮기면, 컴포넌트 cleanup의 `expandedPlace.current = null`은 더는 정의 안 됨 → `expandedPlaceRef.current = null`로 변경 필요. lint(no-undef)가 잡아주지만, 추출 시 "이 alias를 컴포넌트가 어디서 또 읽나" 사전 점검 습관. (직전 const-popup-handlers 회고의 "ref 의존성 체크" 연장선.)
  2. **spiderify는 zoom > clusterMaxZoom(13)에서만 발동한다.** 그 아래에선 같은/근접 좌표 점들이 `places-source`(cluster:true)에 의해 묶여 `places-cluster`로 렌더 → 클릭이 클러스터 핸들러(easeTo)로 감. 개별 `places-circle`가 겹쳐 `queryRenderedFeatures>1`이 되는 건 줌이 clusterMaxZoom을 넘겨 클러스터가 풀린 뒤. 회귀 테스트에서 zoom 12로 두니 spiderify가 안 잡혔고(클러스터됨), zoom 15로 올려야 재현됨. 향후 spiderify 관련 작업/테스트는 줌 조건 인지.
  3. 팩토리 클로저 추출은 함수 본문을 그대로 옮기고 공유 상태를 팩토리 스코프에 두면 거동 보존 — 전체 회귀(링 펼침/접힘·spider/collapse·에러·무크래시)로 확인됨.

## 후속 (이번 범위 밖)
- **fg-map 재실행**: MapView가 751→193 + mapGeo/mapLayers/mapRingController 3모듈로 분리돼 STRUCTURE.md stale. 리팩토링(Part 1+2) 완료 시점이라 지금이 재매핑 적기.
- **clusterRadius 40↔18 결정** (task-76 코드 유실, 이전 회고에서 발견) — 여전히 미결.

## Doc updates
- CONTEXT.md promotion: 없음 (구현 세부)
- ADR added: 없음
