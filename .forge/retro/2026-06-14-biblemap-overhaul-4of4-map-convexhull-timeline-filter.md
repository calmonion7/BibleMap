# 2026-06-14 — MapView Convex Hull + TimelineView Book 필터 (파트 4/4)

## 계획 vs 실제
- 계획대로 진행된 것: S2(hull polygon), S3(타임라인 필터) 구현. 빌드 성공, UAT 통과.
- 편차:
  - S1(convexHull.js)·S4(백엔드 Book 쿼리)가 이전 세션에서 이미 구현되어 있었음 — 작업 범위가 실질적으로 절반으로 줄었음.
  - `/places` 응답이 배열 → `{label, places}` 객체로 이미 변경되어 있었으나 MapView는 아직 배열로 처리 중이던 잠재 버그를 S2 작업 중 발견·수정.
  - `selectedNodeLabel` prop(App.jsx → MapView)을 hull 판단에 쓰지 않고 `/places` 응답의 `label` 필드를 직접 사용 — API fetch와 hull 렌더가 원자적으로 묶임.

## 학습
- 다음에 다르게 할 것: 백엔드 API 응답 형식을 변경할 때(배열→객체 등) 프론트엔드 fetch 핸들러를 같은 커밋에 동기화해야 함. 분산 커밋은 워킹트리에 잠재 버그를 남기고, 다음 작업에서 뒤늦게 발견된다.
- `sortKey`는 `연도 + 미세 보정 float`이므로 year 정수처럼 비교해도 무방함 — 같은 연도 내 순서 조정용이라 필터링 정밀도에 영향 없음.

## 문서 업데이트
- CONTEXT.md 승급: 없음
- ADR 추가: 없음
