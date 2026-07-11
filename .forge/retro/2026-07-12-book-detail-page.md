# 2026-07-12 — 성경책 상세를 독립 전체화면 스테이지(딥링크 페이지)로 승격 + 주요 인물 섹션 정리

## Plan vs actual
- What went as planned:
  - 3 슬라이스(주요 인물 정리 → book 스테이지 → 딥링크) 모두 계획대로. 목표·DoD 정확히 달성.
  - `여정 ▸`을 구절 칩(placeChipBase, 📖 구절 ▸)과 동일 패턴으로, 여정 없는 인물 제거, keyPeople 폴백 보정.
  - 책 URL은 slug 없이 `#/book/<theographic_id>`(non-goal 유지) — 식별자가 실제론 Airtable rec id(`recIFusdNl6d8dj3L`)로 예상보다 더 불투명하나 기능 정상.
- Divergences:
  - **핵심: book 전용 상태 `bookId`를 `selectedNode`와 분리 도입**(계획엔 "SidePanel 재사용"만 명시). 책을 selectedNode에 묶으면 페이지 안에서 사건 클릭 시 selectedNode가 사건 id로 바뀌어 `#/book/<id>` URL이 오염되고 페이지가 사건으로 뒤바뀜. bookId 분리로 URL 안정 + 사건 시트 드릴다운(오버레이) 보존.
  - 계획의 `asPage` prop **불필요** — SidePanel 헤더 크롬(X·← 뒤로)은 `onClose`/`canGoBack` prop이 있을 때만 렌더 → 안 넘기면 크롬 없이 본문만.
  - 계획 S2의 "시트 래퍼에서 book 제외" **폐기** — bookId 분리 결과 시트 래퍼는 그대로(selectedNode로 구동), 책 진입 시 selectedNode=null이라 자동으로 숨겨지고 사건 클릭 때만 오버레이. 이중 마운트 없음.

## Learnings
- Do differently next time:
  - **페이지급 뷰를 추가할 땐 그 페이지의 "대상 상태"를 `selectedNode`와 분리하라**(explore의 `explorePersonId`와 동형). selectedNode는 시트/드릴다운용이라, 페이지가 자기 URL을 유지하면서 자식 노드(사건 등)를 시트로 열려면 대상 상태가 독립이어야 한다. 이번 book 스테이지는 이 패턴의 세 번째 사례(person·tour·book).
  - **계획은 WHAT까지만, HOW(재사용 vs 추출·prop 신설 여부)는 실행에서.** 이번엔 `asPage` 신설·시트 제외 같은 HOW를 계획이 미리 못박았으나 실행에서 더 단순한 경로(prop 게이팅 활용)가 드러나 폐기됨. 재사용 방식은 실제 결합도를 보고 정하는 게 맞다.
  - **직렬 의존 + 공유 파일 프론트 작업은 병렬 워크플로우보다 세션 직접 순차 실행이 유리**(충돌·재탐색 비용 회피, eco·작업 크기 맞추기). 이번 4파일 겹침 편집이 그 예.
  - **Playwright 검증: DOM 존재가 아니라 가시성으로 확인하라.** 숨긴 시트(off-screen translateY)의 드래그 핸들 노드가 DOM에 남아 `width==36 && height==4` 매칭으로 "핸들 present: True" 거짓 양성이 났다. 스크린샷/visibility로 판정해야 함.

## Doc updates
- CONTEXT.md promotion: none (bookId·여정 칩은 구현 세부, 도메인 용어 아님)
- ADR added: none (bookId 분리는 기존 explore 패턴 답습, 책 페이지화는 ADR-0009 확장 — 새 트레이드오프 아님)
