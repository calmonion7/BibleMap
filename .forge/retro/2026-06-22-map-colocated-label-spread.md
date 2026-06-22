# 2026-06-22 — 동일좌표 소수 장소 라벨 방사 배치 (task 84)

## Plan vs actual
- What went as planned: `clusterMinPoints: 4`(mapLayers.js) + `placesToGeoJSON` 동일좌표 그룹 라벨 방사(mapGeo.js). 마커는 한 점 유지, 라벨만 분산. 호렙·시내산 둘 다 표시, 버블 0, spiderify·떨어진 장소 회귀 없음(Playwright). 발산 낮음.
- Divergences: 없음.

## Learnings
- Do differently next time:
  1. **동일좌표 라벨은 `outwardLabel(0,0)`에서 퇴화한다.** 두 장소가 정확히 같은 좌표면 최근접-이웃 방향이 (0,0) → `outwardLabel`이 첫 분기(`ax>=ay*RATIO`, 0>=0 참)로 빠져 **둘 다 같은 'left' 앵커** → `text-allow-overlap:false` 충돌 엔진이 한 라벨을 숨긴다(겉보기엔 "라벨 하나 누락"). 해결: 좌표 그룹핑(toFixed(4)≈11m) 후 그룹 내 라벨을 `ringLabels(lat, groupSize)` 방사 앵커로 배치. 떨어진 장소는 기존 outward 유지. (CONCERNS 1-4 "단일 고정 앵커 → 라벨 숨김" 회귀 벡터의 구체 사례.)
  2. **"소수 비클러스터"의 레버는 `clusterMinPoints`이지 `clusterRadius`가 아니다.** 동일좌표(거리 0)는 줌 ≤ clusterMaxZoom에서 어떤 반경이든 항상 묶이므로 radius로는 못 푼다. `clusterMinPoints: N`이 "반경 내 N개 미만은 클러스터 안 함"을 직접 제어 → 2~3개 동일점은 개별 마커+라벨, 4개+만 버블. task-76(radius)·task-84(minPoints)는 독립 레버.
  3. 데이터에 **정확히 동일한 좌표의 별개 장소**가 존재(호렙=시내산 33.921682,28.58771). 동일좌표 처리는 가정이 아니라 실제 케이스.

## Doc updates
- CONTEXT.md promotion: 없음 (구현 세부)
- ADR added: 없음
