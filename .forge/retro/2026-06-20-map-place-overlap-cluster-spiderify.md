# 2026-06-20 — 맵뷰 장소 클러스터링 + 스파이더파이

## 계획 vs 실제
- 계획대로: S1(클러스터링) + S2(스파이더파이) 모두 단일 세션에서 완료. 기존 `ringPositions`/애니메이션 패턴 재활용으로 스파이더파이 구현이 빠르게 수렴.
- 발산: `getClusterExpansionZoom` 콜백 형태 → MapLibre v5에서 동기 반환값으로 변경됨. 계획에 붙인 예제 코드가 구버전 패턴이었고 실행 중 발견해 즉시 수정.

## 배운 것
- 다음엔 다르게: 계획 작성 시 MapLibre 예제 코드를 붙일 때 `node_modules/maplibre-gl/package.json` 버전을 먼저 확인하고, 해당 버전 소스의 실제 함수 시그니처(`grep getClusterExpansionZoom`)로 검증한 뒤 붙인다.

## 문서 업데이트
- CONTEXT.md 승급: 없음 (구현 세부사항, 도메인 용어 해당 없음)
- ADR 추가: 없음 (3조건 미충족)
