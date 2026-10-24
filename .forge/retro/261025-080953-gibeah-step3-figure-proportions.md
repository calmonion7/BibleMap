# 2026-10-25 — task 404 인물 비율 (fg-loop 일괄 승급)

## Plan vs actual
- What went as planned: 배움 대부분은 실행 중 규칙 원장(rules.json)·시험·메모리로 이미 승급.
- Divergences:
  - 스텝별 가이드(generate.split-control)·5표(judge.single-image-reps)는 원장에 있음.
  - repair-r9: 한 장(고정 시드)으로는 규칙 효과와 바탕 흔들림을 못 가름 → 사람 결정으로 8시드 통과율 측정(r10) — 메모리 「8시드 제비뽑기 금지」와 충돌처럼 보였음.

## Learnings
- Do differently next time:
  - 역할 나눔: 결함 진단·규칙 고침은 한 장(고정 시드, 5표) 반복 · 규칙집 효과는 8시드 통과율로 측정 · 금지는 「8장 뽑아 통과 장 고르기로 규칙을 대신함」(메모리 feedback_one_image_rule_loop 보강).

## Doc updates
- CONTEXT.md promotion: none
- ADR added: none
- 기타: 메모리 feedback_one_image_rule_loop 보강
