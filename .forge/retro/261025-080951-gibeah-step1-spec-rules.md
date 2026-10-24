# 2026-10-25 — task 399 장면 1 단계 ① 명세 규칙 (fg-loop 일괄 승급)

## Plan vs actual
- What went as planned: 배움 대부분은 실행 중 규칙 원장(rules.json)·시험·메모리로 이미 승급.
- Divergences:
  - 명세 관문·성경 검토(사울 약 70세)는 원장·메모리에 들어감.
  - 던진 창을 사울 prop(「a spear」)으로 두면 그림이 창을 손에 남기고 판정자도 「창이 있음」으로 속음 → prop none.

## Learnings
- Do differently next time:
  - 던진·놓은 지물은 던진 사람 prop에 두지 않음 — 이제 recheck.flight_errors가 잡음(시험 FlightPosition.test_thrower_holding_thrown_prop_fails, 2026-10-25 일괄 승급).

## Doc updates
- CONTEXT.md promotion: none
- ADR added: none
- 기타: eval recheck.flight_errors 던진 지물 prop 검사 + 시험
