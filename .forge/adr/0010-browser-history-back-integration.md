# 브라우저 히스토리를 stage/인물/시트 경계에만 통합한다 (뒤로가기 = 시트부터 닫기)

ADR-0009는 공유·북마크(replaceState 미러)만 하고 브라우저 뒤로가기 통합을 "필요하면 별도 작업"으로 미뤘다. 모바일 뒤로 제스처가 앱 내비와 연결되지 않아, 시트를 열고 뒤로 누르면 앱을 이탈했다. 이 ADR이 그 후속으로 뒤로가기를 통합한다.

**결정:** 히스토리 엔트리를 **stage/인물 전환 + 상세 시트 열림 경계**에만 만든다(granularity B). `pushState`는 stage 변경·인물 변경·**시트 열림**(`selectedNode`가 세팅되고 그게 탐험 인물 자신이 아닐 때, 즉 모바일에서 시트가 실제로 보일 때)에서만 발생하고, 지도/타임라인 토글·시트 안 node→node 드릴다운은 `replaceState`(뒤로 스텝 아님). `selectedNode`는 **URL이 아니라 `history.state`에** 실어 뒤로가기 복원에만 쓴다(ADR-0009의 "node는 URL 미인코딩" 유지 — 시트는 transient). `popstate`는 `event.state`에서 stage/인물/뷰/시트를 복원하며, 복원 중 재-push를 막는 가드 플래그를 둔다. 시트 X·스와이프 닫기는 `window.history.back()`에 위임한다.

## Considered Options
- **완전 통합**(`useNodeSelection` 내부 history를 브라우저 히스토리로 흡수): node 드릴다운도 전부 엔트리가 되어 가장 매끄럽지만, `goBack`/`canGoBack`/`closePanel` 공개 API 전면 개편 — 리스크 큼. 채택 안 함.
- **코스만**(stage/인물만, 시트는 히스토리 밖): 저리스크지만 시트 열고 뒤로 시 시트를 건너뛰어 stage 이탈 — 모바일에서 어색. 채택 안 함.

## Consequences
- **`selectedNode`의 이중 의미 주의**: 탐험 진입 시 `selectedNode`가 인물 자신으로 세팅되나 모바일 시트는 숨겨지므로, "시트 열림" 신호는 raw `selectedNode`가 아니라 `selectedNode && selectedNode !== explorePersonId`다. 이 구분이 틀리면 장소 시트 열기가 뒤로 엔트리를 못 만들어 뒤로가 시트를 건너뛴다.
- **`useNodeSelection` 내부 history는 그대로** — 시트 안 "← 뒤로"(node→node 드릴다운)는 브라우저 히스토리와 별개 축으로 남는다. OS 뒤로는 시트를 통째로 닫고(드릴 스택 폐기), 인물 이탈로 이어진다.
- 앱 내 "← 다른 인물"·"인물 허브" 버튼은 (한 스텝 뒤로가 아니라) 목적지로의 직접 이동이라 forward push다 — OS 뒤로만 히스토리를 역행한다.
- 새로고침은 시트를 복원하지 않는다(`history.state`는 새 로드에서 null). stage/인물/뷰는 ADR-0009대로 해시에서 복원.
