# 2026-06-19 — 타임라인 인물 필터 (HAS_PARTICIPANT 기반 사건 필터링)

## 계획 대비 실제
- 계획대로 된 것: S1~S4 전부 예정대로. 44줄 변경, Dynamic Workflow 불필요한 소형 작업이었음.
- 발산: bookFilter sticky `top: 0` → `top: 48` 수정이 계획 외. personFilter 배너 구현 중 nav 바(48px)가 scroll container 전체를 덮는 레이아웃에서 `top: 0`이면 배너가 가려진다는 것을 발견. bookFilter도 같은 버그 → 함께 수정.

## 학습
- 다음에 다르게 할 것:
  - **Sticky 배너는 `top: navHeight`** — scroll container가 `inset: 0`(뷰포트 전체)에서 시작하고 nav 바가 floating 48px이면, sticky `top: 0`은 nav 바 뒤에 숨김. 앞으로 배너 추가 시 `top: 48` 기본값으로 잡을 것.
  - **"동일 스타일" 참조 구현에 버그가 있으면 함께 수정** — 계획 범위 밖이어도 참조 코드가 틀렸으면 같이 고친다. 사용자 확인.
  - **Playwright: SidePanel 열린 상태에서 우측 끝 버튼 클릭** — SidePanel(360px)이 우측을 점유하면 `marginLeft: auto` 버튼이 SidePanel 영역에 놓임. `page.evaluate` JS 클릭 or `force: true` + 정확한 좌표 접근 필요.

## 문서 업데이트
- CONTEXT.md 승급: 없음 (구현 세부 사항)
- ADR 추가: 없음
