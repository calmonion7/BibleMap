# 2026-10-26 — 두 여인 단계 ②③ 8시드 · 뒷벽 문구 B 채택(+4) · 통과 B 4/8

## 계획과 실제
- 계획대로 된 것: 고정 절 판정 전 기록 · A·B 16장 한 묶음 × 3표 · 미리 정한 채택 규칙 그대로 적용(예) · 명세 B · recheck·시험·미커밋 해시 회귀 가드 · 틀림 이유 읽기(문항 결함 없음).
- 어긋난 것:
  - 채택 「예」(+4)의 4점 중 3점이 s11 A 한 장(칼 여인 발치 · 스테인드글라스 · 덧붙은 막대) — 장 수 차 규칙은 한 장에 몰린 결함을 여러 점으로 센다. 가드 차이(서명 · 종이 띠 · 유령 그림자)도 벽 문구와 무관한 흔들림.
  - 423 s11의 「A도 뒷벽 돌 블록 5/5」는 한 시드 결 — 8시드 A 2/8 · B 6/8. 그래서 계획엔 없던 PROMPTING 30 닫는 줄을 덧붙임(채택이면 건드리지 않기로 했으나 옛 줄이 틀린 채 남음).
  - 판정자가 s42 칼(가운데 여인 발치)을 2/3 맞음으로 너그럽게 봄 → 엄하게 B 3/8.

## 배운 것
- 다음엔 다르게:
  - **대조군 채택 규칙은 「장 수 차」에 「이득이 퍼진 시드 수」를 함께 건다** — 예: 축 문항 셋 중 하나라도 B만 맞은 시드가 A만 맞은 시드보다 3개 이상 많을 것. 한 장 결함 묶음(칼·창·가드가 한 그림에서 같이 무너짐)이 여러 점이 되는 걸 거른다. 다음 rule_ab 고정 절 `adopt`에 칸으로.
  - **한 시드 A/B에서는 대조군(A) 관측도 결론으로 적지 않는다** — 423 「A도 블록 5/5」처럼 기준 쪽 관측이 틀리면 「재현 안 됨」 판단 자체가 흔들린다.
  - 문구의 직접 효과는 그 문구가 말하는 기록 문항(뒷벽 재질)에서 먼저 본다 — 거르기 문항 이득은 부수 효과라 약한 근거.

## 문서 반영
- CONTEXT.md 올림: 없음
- ADR 추가: 없음
- 시험(eval): test_rule_ab(실행 중 추가 — 고정 절 고르기·시드별 경로·채택 규칙) · 더 없음
- 프로젝트 노트: notes/TWO-MOTHERS-STEP23.md · PROMPTING 30 「task 432」 줄
- 메모리: feedback_judge_reproducibility 덧붙임(채택 규칙 퍼짐 조건)

## 후속 후보
<!-- followup: fu-62713f7a7248 | source: two-mothers-step23-backwall | task: 432 | date: 2026-10-26 | status: open | taken: - -->
- 두 여인 단계 ④ 사람 판정 화면 — B 기계 통과 4장(s42 s11 s23 s101) + 기계 불통과 표본(칼 자리 s7·s5)을 한 질문씩 폰 화면으로. s42는 칼이 가운데 여인 발치(판정자 너그러움)라 사람 눈으로 갈라 볼 장.
  근거: notes/TWO-MOTHERS-STEP23.md 결과·눈 확인 · samples/two-mothers-step23/back-wall-B-s*.png.

<!-- followup: fu-b3f0cc55b565 | source: two-mothers-step23-backwall | task: 432 | date: 2026-10-26 | status: open | taken: - -->
- 두 여인 칼 자리 수리 — 「a straight iron sword lying on the floor before the king's wooden seat」인데 8시드 중 B 3장이 여인 발치·두 자루(A는 벽에 기댐 포함 4장). 가이드에 칼 자리(왕 자리 앞 바닥)를 넣거나 지물 편집(edit.held-prop-add 꼴)으로 — fg-loop 수리 반복 몫.
  근거: notes/TWO-MOTHERS-STEP23.md 칼 틀림 이유 · rule_ab report t.sword A 4/8 · B 5/8.
