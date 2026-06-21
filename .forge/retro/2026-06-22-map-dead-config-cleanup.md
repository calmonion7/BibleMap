# 2026-06-22 — 맵 라벨 dead config 정리 (task 81)

## Plan vs actual
- 계획대로, 발산 없음. `text-justify: 'auto'` 3곳(기본값과 동일) + `cosLat || 1` 2곳 제거. 라벨 렌더 불변(Playwright 확인).

## Learnings
- `cosLat || 1`은 죽은 가드였다 — JS `Math.cos(90°)=6.12e-17`(truthy)라 `|| 1`은 어느 위도에서도 발화 안 하고, 데이터(26~37°N)는 애초에 0 근처 미도달. false-safety는 제거가 정답.

## Doc updates
- CONTEXT.md promotion: 없음
- ADR added: 없음
