# 2026-10-21 — 요단 구도 가이드 (task 388, 일괄 승급 2026-10-22)

## 계획 대비 실제
- 차이: 문구 파생이 다윗을 「On the left」로 부르는데 가이드의 바르실래(인물 칸 아님) 실루엣을 더 왼쪽에 둬서 모델이 왕을 맨 왼쪽 칸에 그렸다 — 시험 한 장에서 잡힘(notes/JORDAN-GUIDE.md).

## 배운 것
- 다음엔 다르게: `derive_scene._side`는 구역 중심 절대 위치 낱말이라, 가이드에 한 사람 꼴 칸을 둘 때는 위치 낱말을 받는 인물보다 바깥에 두지 않는다. 가이드를 다른 장면으로 넓히는 것이 정해진 방향(rules `spec.placement-by-guide`)이라 다시 날 수 있다.

## 문서 반영
- CONTEXT.md 승격: 없음
- ADR 추가: 없음
- 시험(eval): `scripts/canon/test_whole_prompt.py` `GuideSide` — 「on the left/right」 인물보다 바깥에 한 사람 꼴(person·person_bow·kneel_bow·seated) 가이드 칸이 있으면 실패. red(바르실래 칸을 다윗 왼쪽으로 옮긴 사본에서 실패) → green(지금 37명세)
