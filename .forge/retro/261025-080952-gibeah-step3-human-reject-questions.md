# 2026-10-25 — task 402 사람 거절 사유 → 문항 (fg-loop 일괄 승급)

## Plan vs actual
- What went as planned: 배움 대부분은 실행 중 규칙 원장(rules.json)·시험·메모리로 이미 승급.
- Divergences:
  - 거절 사유를 문항으로 옮겨 거절 그림에 먼저 묻는 길은 judge.human-reject-to-question으로 승급됨.
  - 실행자 눈(Claude가 원래 크기로 직접 보는 확인)이 기계 통과 그림의 창 거꾸로(촉 방향)를 걸러냄 — 402~412 내내 반복된 역할이나 정의가 없음.

## Learnings
- Do differently next time:
  - 기계 통과 장은 사람 화면 전에 실행자 눈으로 원래 크기 확인 → 짚은 결함은 사람 화면에 「짚을 수 있는 점」으로 밝힘(402~412 관행).
  - CONTEXT 용어 후보 「실행자 눈」 — CONTEXT.md 미커밋 변경이 정리된 뒤 사람 확인 받아 승급.

## Doc updates
- CONTEXT.md promotion: none (후보 「실행자 눈」 — 사람 확인 대기)
- ADR added: none
