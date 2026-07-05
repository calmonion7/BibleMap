# 2026-07-05 — 브라우저 뒤로가기 통합 (모바일 뒤로 = 시트 닫기 → 인물 이탈)

## Plan vs actual
- What went as planned: `App.jsx`만 수정(push/replace 인식 sync effect + `popstate` 복원 + X/스와이프 `history.back()` 위임), `useNodeSelection` 미변경, range B·ADR-0010대로. 모바일 5/5 통과. `sheetOpen = selectedNode && selectedNode!==explorePersonId` 함정도 계획대로 반영.
- Divergences (중간): 검증 중 베이스 엔트리 버그 1건을 잡고 넘어감(아래 학습).

## Learnings
- Do differently next time:
  - **effect가 "반응"해야 하는 완료/준비 신호는 ref가 아니라 state로 두고 dep에 넣어라.** 이번엔 복원 완료를 `restoredRef`(ref)로 두고 sync effect의 dep는 `[stage/person/view/node]`뿐이었다 → ref가 켜지는 시점(curatedIds 로드)은 sync dep이 아니라, **허브에서의 베이스 `replaceState`가 아예 안 돌았다**. 그 결과 첫 인물 클릭이 `navSyncRef.initialized=false`라 베이스(replace)로 취급돼 허브 엔트리를 덮어썼고 → 뒤로가 앱 이탈(about:blank). `restored`를 **state**로 바꿔 dep에 넣고 `setRestored(true)`를 복원 마이크로태스크 안(복원 stage 적용 뒤)으로 옮겨 해결. ref는 "값을 읽되 재실행 트리거는 아님", state는 "변경이 렌더·effect를 트리거" — 이 구분을 먼저 따질 것.
  - **SPA 히스토리 push/replace 버그는 `page.evaluate("history.length")`·`history.state`로 계측하면 즉시 특정된다.** "뒤로가 앱을 벗어난다"는 증상만으로는 원인 불명 → length가 안 늘면 push가 replace로 새고 있는 것. (task 122의 "fresh page로 SPA 검증" 교훈과 세트 — [[feedback_playwright_testing]] 영역.)
  - `useNodeSelection` 내부 드릴 history를 안 건드리고(range B) 브라우저 히스토리를 시트 열림 경계에만 얹은 분담은 잘 작동했다 — 완전 통합(리스크 큼)을 피한 선택이 옳았다.

## Doc updates
- CONTEXT.md promotion: none (구현 함정이라 용어 아님).
- ADR added: none 신규 — `.forge/adr/0010-browser-history-back-integration.md`가 fg-ask에서 이미 기록(granularity B·history.state·내부 history 분담, ADR-0009 뒤로가기 미룸 해소).
