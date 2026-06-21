# 2026-06-20 — MapView.jsx 상수·팝업·이벤트핸들러 추출

## 계획 vs 실제
- 계획대로 된 것: S1(constants.js 추출), S2(placePopupHTML 헬퍼), S4(빌드·UAT) 완전 일치
- 이탈: S3 — `registerEventHandlers` 서명에 `expandedPlaceRef` 미포함. 계획은 `{ collapseRing, collapseSpider, expandPlace, spiderifyPlaces, onSelectNode, popupRef }`였으나 실제로는 `expandedPlaceRef`가 필요했다. `places-circle` 핸들러가 "같은 장소 재클릭 → 링 접힘" 판단을 위해 `expandedPlace.current`를 직접 참조해야 했기 때문.

## 학습
- 다음에 다르게 할 것:
  - **핸들러 추출 계획 시 ref 의존성도 체크**: 클로저 함수 목록만 추적하지 말고, 핸들러가 직접 읽는 ref(`useRef` 반환값)도 서명에 포함할지 검토해야 한다. 클로저 함수는 effect 내부에 남기는 결정과 독립적으로, ref는 값 전달이 가능하므로 파라미터에 넣을 수 있다.
  - **pre-clear 로직 흡수 패턴 재활용 가능**: effect 지역 mutable 변수(`animFrame`, `expandAbortCtrl`)를 핸들러가 직접 참조해야 하는 경우, 해당 로직을 핵심 async 함수 시작부에 흡수하면 핸들러 의존성을 제거할 수 있다. 이번에 `expandPlace` 시작부에 animFrame 취소·링 즉시 초기화를 넣어 핸들러 의존성을 `expandedPlaceRef` 하나로 줄인 것이 좋은 예.
  - **`registerEventHandlers`가 맵 이벤트 추가의 단일 진입점**: 이후 MapView에 새 이벤트 핸들러를 추가할 때는 이 함수 안에 등록한다.

## Doc 업데이트
- CONTEXT.md 승급: 없음
- ADR 추가: 없음
