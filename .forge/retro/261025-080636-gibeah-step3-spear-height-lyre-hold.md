# 2026-10-25 — 기브아 창 높이 = 던진 어깨 · 빗나감 한도 머리 하나 · 수금 안아 넣기 → 사람 m17e s7 채택 (task 412, fg-loop 일괄 승급)

## Plan vs actual
- What went as planned: 메모 둘 → 문항 o0k 거절 2/2 잡음 · 규칙 generate.flight-height · m17e 통과 1/8 → 사람 채택(루프 목표 달성).
- Divergences:
  - 창을 올리자 dodge-clear 고정 한도 0.05와 부딪침 — 기존 시험 기대를 약하게 하지 않는 해법(한도 = 피하는 사람 머리 하나, 기준표)을 찾음. 순수 물리선(서 있는 머리로 겨눔 0.428)은 기존 시험 「머리 높이로 곧장」과 충돌해 뼈대 어깨(0.443)를 씀.
  - 새 검사 함수를 SPEC_CHECKS에 등록하지 않아 생성 관문에서 빠짐 — test_recheck 지킴 시험이 잡음.
  - 수금 쥠: 칠하기 길 세 번 실패(떠 있음 · 덤 막대) → 칠하지 않고 팔을 풀어 준 넣기(hug).
  - 승인 뒤 뒷일 둘: style_judge B 묶음이 승인 최종 그림을 그때그때 읽어 새 승인 판정이 비어 C8 실패 · recheck.source가 국소 편집 바탕을 plain-words로만 가정해 `recheck.py images` 멈춤.

## Learnings
- Do differently next time:
  - 사람 메모의 물리 직관(「던질 때 팔 높이」)은 가이드 뼈대 점에서 바로 파생 — 마무리 꼴 손목이 아니라 놓는 순간의 어깨.
  - 고정 문턱(0.05 같은) 규칙은 배치를 바꾸면 거짓 실패를 냄 — 기준표 단위(머리 하나)로 상대화.
  - 승인을 바꾸면 `batch/style_judge.py judge` · `recheck.py images`까지 돌린 뒤 회귀를 봄(승인은 측정 기록 둘이 함께 읽음).

## Doc updates
- CONTEXT.md promotion: none
- ADR added: none
- 기타: 원장 generate.flight-height · dodge-clear 한도 · 시험 FlightHeight·hug·ApprovedSource(실행 중 추가) · PROMPTING 29
