# 2026-10-25 — task 397 기브아 새 명세로 다시 그리기 (fg-loop 일괄 승급)

## Plan vs actual
- What went as planned: 배움 대부분은 실행 중 규칙 원장(rules.json)·시험·메모리로 이미 승급.
- Divergences:
  - C 장면 8장 기계 통과 0/8 — 창 8/8 손에 남음 · 수금 류트(뒤 task 400·405 규칙으로 풀림).
  - 판정 문항 e.spear의 괄호 부정문(「~ 아님」을 괄호 안에 섞음)이 모호해 판정이 갈림 → 400에서 긍정문 둘로 나눔.
  - RECHECK.md 해시 차이를 「사용자 미커밋 탓」으로 짚고 되돌렸으나 399에서 정상 갱신(원장 판 바뀜)으로 확인 — 잘못된 원인으로 되돌림.

## Learnings
- Do differently next time:
  - 판정 문항에 여러 조건이 섞이면 긍정문 하나씩으로 나눔 — 「무엇이 아님」은 대표 틀린 꼴 하나만 예로.
  - 생성·측정 파일 해시가 바뀌면 되돌리기 전에 원장 판(`recheck.py ledger`)·최근 커밋과 대조 — 원인을 못 짚으면 되돌리지 않음.

## Doc updates
- CONTEXT.md promotion: none
- ADR added: none
