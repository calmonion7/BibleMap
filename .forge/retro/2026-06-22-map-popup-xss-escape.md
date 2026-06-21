# 2026-06-22 — 맵 팝업 XSS label 이스케이프 (task 78)

## Plan vs actual
- What went as planned: `escapeHtml` 헬퍼 + `placePopupHTML`에 적용. 계획의 최소-diff 권장(escapeHtml) 그대로. 발산 없음.
- Divergences: 없음.

## Learnings
- Do differently next time:
  - **maplibre `.setHTML()`/`.setDOMContent()`가 앱 유일의 미이스케이프 sink.** 나머지(SidePanel/Timeline/Overview)는 JSX 텍스트 보간이라 자동 이스케이프된다. 향후 맵 팝업/오버레이에 Neo4j 등 신뢰 불가 데이터를 HTML 문자열로 넣을 때는 반드시 `escapeHtml`(이제 MapView에 존재) 경유. 새 `setHTML` 추가 = XSS 감사 포인트.

## Doc updates
- CONTEXT.md promotion: 없음 (구현 세부)
- ADR added: 없음 (가역적 단순 수정)
