# 2026-06-15 — Hull 가시성 — 비교 스크린샷 → 스타일 적용

## 계획 대비 실제
- 계획대로 된 것: Playwright 스크린샷 비교 → 값 적용 + 커밋. 빌드 성공.
- 차이:
  - 계획은 "색상 변경 안 함"을 비목표로 설정했으나, 파란 계열 비교 후 사용자가 흰 fill, 빨간/오렌지 계열 추가 요청 → 3 라운드(12장) 촬영 후 최종 오렌지(#f97316) 선택.
  - `window.__bm_map` 노출을 위한 임시 빌드 1회가 계획에 없던 단계로 추가됨.
  - MapLibre `map.getSource(id)._data`로 hull bounds 읽기 시도 → private API라 undefined 반환, fitBounds 포기.

## 학습
- 다음엔 이렇게:
  1. **시각 튜닝 작업은 색상 변경 가능성을 처음부터 플랜에 열어둔다.** opacity/width 조정과 색상 변경은 세트로 탐색되는 경우가 많으므로, 비목표로 닫으면 실제 작업 흐름과 충돌한다.
  2. **MapLibre GeoJSON 소스 데이터는 `_data`(private)로 읽지 않는다.** 대신 `map.querySourceFeatures(id)` 또는 `map.queryRenderedFeatures({ layers: [id] })`를 사용한다. `_data`는 undefined를 반환하므로 bounds 계산 등에 쓸 수 없다.

## 문서 업데이트
- CONTEXT.md 승급: 없음
- ADR 추가: 없음
