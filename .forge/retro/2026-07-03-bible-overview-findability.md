# 2026-07-03 — 성경 책 둘러보기 찾기 최소행동화 (task 110) 〔일괄 승급 2026-07-03 — 드라이브 자동 스킵분의 늦은 회고〕

## Plan vs actual
- 계획대로: S1(점프 내비 칩 바)·S2(모바일 카드 경량화, 8,350→6,601px)·S3(라벨 통일) 전부 충족.
- Divergences: ① 섹션 추적을 IntersectionObserver 대신 scroll 리스너로(더 결정적·단순). ② scrollIntoView 버그 발견·수정(아래).

## Learnings
- Do differently next time:
  - **`scrollIntoView()`는 overflow:hidden 조상 컨테이너까지 프로그래밍적으로 스크롤시킨다**(translateY 등 transform이 만든 오버플로 포함). BibleMap 앱 루트가 48px 밀려 상단 내비가 사라지고 숨겨둔 모바일 시트 상단이 노출됐다. 중첩 스크롤 레이아웃에서 특정 컨테이너만 이동시키려면 `root.scrollTo(top)`으로 대상 한정할 것.
  - 스크린샷 육안 검토가 assert가 놓친 이상(하단 흰 스트립)을 잡았다 — 수치 assert에 스크린샷 리뷰를 곁들일 것.

## Doc updates
- CONTEXT.md promotion: (실행 당시 fg-ask에서) '화면 단계(Stage)' 신규. 회고 시점 추가 승급 없음.
- ADR added: none.
