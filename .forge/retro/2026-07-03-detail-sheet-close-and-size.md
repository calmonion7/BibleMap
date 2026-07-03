# 2026-07-03 — 상세 시트 닫기 버튼 수정 + 시트 크기 확대 (task 114)

## Plan vs actual
- What went as planned: S1(X 버튼 → sticky 헤더 이동)·S2(SHEET_VH 55→75) 전부. 모바일 390×844 Playwright 기하 측정 + 스크린샷 2종으로 통과(닫기 40px 원, 상단·스크롤후 y=237 고정, 시트 top=211/844=75vh, 닫힘 OK, 콘솔에러 0).
- Divergences (경미): 버튼 44→40px(제목 행 정렬 시 과하지 않게); 모바일 드래그 바(sticky) 아래로 헤더를 고정하려 `stickyTop` prop 신설; 인물 시트 별도 스크린샷 생략(코드가 동일 공유물이라 책 시트로 대표).

## Learnings
- Do differently next time:
  - **"A를 B처럼" 요청은 A·B가 실제로 별개인지 코드로 먼저 확인.** 사용자는 "인물창과 동일하게"를 요청했지만 인물·장소·사건·책 상세는 이미 **하나의 공유 SidePanel**(App.jsx 337-393)이었다 → 별도 컴포넌트 통일 같은 중복 작업 대신 단일점 수정으로 수렴했고, "동일하게"는 자동 충족. 그릴링 단계의 탐색이 이걸 잡아 계획 범위를 크게 줄였다.
  - **`position:absolute`를 `overflowY:auto` 컨테이너 안에 두면 콘텐츠와 함께 스크롤돼 사라진다.** 닫기 버튼이 스크롤 시 소멸하던 근본 원인. 항상 보여야 하는 컨트롤은 `position:sticky` 헤더에 태운다(이미 우측 44px 예약돼 있던 SidePanel 헤더가 자연스러운 자리였다). 이 상세 시트 영역의 기존 교훈들(task 110 `scrollIntoView`가 overflow 조상까지 스크롤, task 111 CSSOM 정규화)과 같은 계열 — 이 시트는 sticky·overflow·translateY가 얽혀 배치에 주의가 필요한 지점.
  - **중첩 sticky-top 요소는 같은 `top:0`에서 겹친다.** 모바일 드래그 핸들 바(sticky top:0, ~16px)와 SidePanel 헤더(sticky)가 스크롤 시 겹치므로, 아래 요소의 sticky `top`을 위 요소 높이(16px)만큼 밀어야 한다(`stickyTop` prop). 하드코딩 16은 드래그 바 padding(8+4)+pill(4)에서 나온 값 — 바 치수를 바꾸면 같이 조정.
  - 검증은 rect 기하 측정(task 111 교훈) + 스크린샷 육안(task 110 교훈) 조합 재사용 성공 — 스크롤 후 닫기버튼 위치 불변을 수치(y=237)로 확정해 "스크롤하면 사라짐" 회귀를 봉인.
- Divergences 요약: 계획 적중, 이탈은 버튼 크기·stickyTop prop 등 구현 세부뿐.

## Doc updates
- CONTEXT.md promotion: none — "상세 시트(Detail Sheet)" 용어는 fg-ask 그릴링 시점에 이미 추가(인물창/책 상세창/레이어 → 하나의 시트로 정리). 회고 시점 추가 승급 없음.
- ADR added: none — 전부 가역적 UI 스타일/배치 결정(ADR 3조건 미충족).
