# 2026-07-08 — 관계 뷰 사건 클릭 깜빡임/누름 피드백 (task 135)

## Plan vs actual
- What went as planned: 구절 레이어(모달)를 스크롤 컨테이너 **밖**으로 빼는 구조(비스크롤 relative 루트 > 내부 `overflowY:auto` 스크롤 div > `{VerseLayer()}` 형제, 백드롭 `fixed`→`absolute inset:0`). 스크롤 후 모달 화면 중앙·부모 스크롤 위치 유지 검증.
- Divergences: **초기 진단이 틀렸다.** "부모 영역 깜빡"을 스크롤 컨테이너 리페인트로 보고 모달을 밖으로 뺐으나(배포까지), 사용자 확인 결과 실제 증상은 **클릭 시 나타나는 사각형 = 모바일 탭 하이라이트(`-webkit-tap-highlight-color` 기본 반투명)**. 관계 뷰 루트에 `WebkitTapHighlightColor:'transparent'`(상속)로 해결. 이어 탭 하이라이트를 끄니 누름 피드백이 사라져("사건 클릭 느낌 안 남") `.rel-chip:active`(배경 틴트 + `scale(0.94)`)로 의도된 누름 감을 복원. 한 task 안에서 3회 반복(모달-이동 → 탭하이라이트 → 누름피드백).

## Learnings
- Do differently next time:
  - **모바일 "클릭 시 사각형 깜빡"은 먼저 `-webkit-tap-highlight-color`(브라우저 기본 하이라이트)를 의심하라.** 리페인트·리마운트 같은 깊은 가설보다 이 기본값이 흔한 원인 — `transparent`로 끄면 사라진다. (깊은 가설로 먼저 뛰어 모달-이동 헛걸음.)
  - **모바일 탭 하이라이트·`:active` 등 "누를 때만" 보이는 시각은 헤드리스 Playwright로 검증 불가 → 반드시 기기 확인.** 이번에 오진 수정(모달-이동)에 `verified: yes`를 붙였다가 "아직 안됨"으로 회귀했다. **사용자가 보고한 정확한 증상을 재현·확인**할 것(모바일 상호작용 특히). 헤드리스로는 속성 적용까지만 증거로 쓰고 시각은 기기로.
  - **탭 하이라이트를 끄면 누름 피드백도 사라지니 의도된 `:active`(배경 틴트+`scale`)로 대체하라.** 그리고 **인라인 `background`는 클래스 `:active` 배경을 못 이긴다**(인라인 특이성 우선) → 기본 배경/테두리를 클래스로 이관해 `:active`가 오버라이드하게, 또는 `transform`/`filter`(인라인과 안 겹쳐 안전).
  - (부수, 구조) 모달을 `overflow:auto` 스크롤 컨테이너 **자식**으로 두면 `fixed`가 스크롤 시 오배치되고 부모 리페인트도 유발 → 비스크롤 루트의 **형제**로 두고 `absolute inset:0`. 오진 수정이었으나 구조상 옳아 유지.

## Doc updates
- CONTEXT.md promotion: none (새 도메인 용어 아님 — 프론트 구현 gotcha).
- ADR added: none (되돌리기 어려운 결정 아님).
- 프론트 gotcha(탭 하이라이트·:active·inline vs class·모달 스크롤)는 메모리 [[project-biblemap-status]]에 이미 요약됨.
