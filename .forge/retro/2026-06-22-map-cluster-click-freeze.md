# 2026-06-22 — 맵뷰 클러스터 버블 클릭 후 맵 멈춤 수정 (task 77)

## Plan vs actual
- What went as planned: S1 단일 변경(클릭 핸들러 `async`+`await`+`zoom != null` 가드)으로 수렴. 빌드/lint clean. Playwright 전/후 검증 계획대로 수행, 스크린샷 `.forge/reports/`.
- Divergences: 낮음. 단 버그가 진단보다 강했음 — Promise를 `easeTo({zoom})`에 넘기면 줌이 NaN이 되는 정도가 아니라, maplibre 내부 `_calcMatrices`에서 동기 예외(`TypeError: Cannot read properties of null`)가 터져 transform이 깨지고 맵이 멈춤. 원인(동기 숫자로 취급한 Promise)·수정(await)은 동일해 계획 변경 없음.

## Learnings
- Do differently next time:
  1. **`getClusterExpansionZoom` 시그니처 함정 — 이번이 두 번째.** 직전 회고(2026-06-20 cluster-spiderify)가 "MapLibre v5에서 동기 반환값으로 변경됨"이라 적었으나 **그 결론이 틀렸다**. `node_modules/maplibre-gl/dist/maplibre-gl.d.ts` 실제 시그니처는 `getClusterExpansionZoom(clusterId: number): Promise<number>`. 그 잘못된 메모 탓에 클러스터 클릭 확대는 처음부터 동작한 적이 없었고 멈춤 버그가 잠복했다. → API 시그니처 검증은 "실행되더라" 수준이 아니라 **`.d.ts`의 반환 타입을 직접 확인**할 것(Promise/콜백/동기). MapLibre 클러스터 API(`getClusterExpansionZoom`/`getClusterChildren`/`getClusterLeaves`)는 5.x에서 모두 Promise 반환.
  2. **Promise는 항상 truthy.** `const zoom = src.getClusterExpansionZoom(...); if (zoom)` 형태의 가드는 await를 빼먹어도 통과해 버그를 숨긴다. 비동기 API 결과를 동기 값처럼 가드하지 말 것.
  3. **인터랙션 핸들러 UAT는 '렌더링'이 아니라 '클릭 후 상태'까지.** 클러스터가 그려지는 것만 확인하면 클릭→멈춤을 놓친다. 카메라/transform을 건드리는 핸들러는 클릭 후 `getZoom()`/`getCenter()` 유한성 + 후속 드래그로 맵이 살아있는지까지 검증해야 한다(이번 Playwright A/B 패턴: 옛 코드 메커니즘 재현 + 수정 핸들러 실제 클릭 + 드래그 이동).
  4. **검증용 임시 노출 패턴.** maplibre 맵 인스턴스가 window에 없을 때 `window.__map = map`를 UAT 동안만 붙였다가 제거·재빌드하면, dist에 흔적 없이 `queryRenderedFeatures`/`project`로 캔버스 위 클러스터를 정확히 클릭할 수 있다.

## Doc updates
- CONTEXT.md promotion: 없음 (구현 세부 — 새 도메인 용어 없음)
- ADR added: 없음 (가역적 1줄 수정, 3조건 미충족)
