# 2026-07-03 — 여정 정차지 선택 시 지도 줌인 (task 116)

## Plan vs actual
- What went as planned: 계획대로 `MapView.jsx`의 정차지 선택 `easeTo`에 `zoom: Math.max(map.getZoom(), 8)` 한 줄 추가. 직접 실행(eco). 모바일 Playwright로 다메섹(줌5→8 확대)·멜리데(이동+줌 유지) 확인, 콘솔에러 0.
- Divergences: 없음.

## Learnings
- Do differently next time: 특기사항 없음 — 무편차 사소 변경. `Math.max(현재, 목표)` 패턴이 "누르면 줌인, 이미 확대 시 유지"를 한 줄로 해결(줌아웃 역효과 방지). 향후 카메라 확대 동작에 재사용 가능.

## Doc updates
- CONTEXT.md promotion: none.
- ADR added: none (가역적 UI 카메라 조정).
