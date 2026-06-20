# 2026-06-20 — UI/UX 개선 2of2 — 타임라인 자동 스크롤 + 모바일 스와이프

## 계획 대 실제
- 계획대로 된 것: S1·S2 모두 적용.
- 발산: 계획 코드 예시가 effect body 내 직접 setState 호출 → `react-hooks/set-state-in-effect` lint 오류. rAF 콜백으로 이동해 해결.

## 배운 것
- 다음엔 다르게: fg-ask 계획 작성 시 effect 내 setState 예시 코드는 rAF/setTimeout 콜백 패턴으로 제시할 것(프로젝트 lint 규칙 준수).

## 문서 업데이트
- CONTEXT.md 승급: 없음
- ADR 추가: 없음
