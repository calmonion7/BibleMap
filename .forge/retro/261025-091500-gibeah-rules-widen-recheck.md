# 2026-10-25 — task 413 기브아 규칙 넓힘 · 전 명세·승인 그림 재검 (fg-loop 일괄 승급)

## Plan vs actual
- What went as planned: S1~S3 모두 계획대로, 재계획 0/3. 크기 규칙 빈 통과 → 못 잼(명세 35·3·21·20), 사전 look.hold 15, 수금 hug 지시 m17e s7과 바이트 같음, 새로 낡음 승인 그림 0.
- Divergences:
  - 계획 밖으로 `flight_height_errors`도 못 잼으로 넓혔다가 기존 시험 `test_no_flight_needs_nothing`(flight 칸 뺀 기브아 = 통과) 기대를 깸 → 되돌림. 빠진 flight는 `flight_errors`가 이미 실패로 셈 — 넓힘이 중복이었다.
  - 사전 grounds 인용 3개를 기억으로 써서 개역한글과 글자가 달랐다(삼하 6:14 「다윗이」→「때에」 · 삼상 17:7 「자가」→「자는」 · 왕상 3:20 「내 곁에서」 빠짐) — 사전 인용 대조 시험이 잡음.
  - 그림 재검 대조에서 새 규칙 `derive.held-hold`가 7장 「낡음」으로 보였으나 모두 이미 「그림 뒤 명세가 바뀜」으로 전 규칙 낡음이던 그림 — 새 낡음 0. `spec_changed`를 따로 갈라야 거짓 「새 낡음」을 피한다.
  - `recheck.py specs`는 작업 폴더를 읽으므로 커밋한 specs.json에 사용자 미커밋 아둘람 명세가 반영됨(보고에 명시).

## Learnings
- Do differently next time:
  - 「같은 결」로 계획 밖 함수까지 넓히기 전에 그 함수 이름으로 시험 파일을 grep해 기존 기대(특히 `[]` 통과 단언)를 먼저 본다. 기대를 바꿔야 하면 넓히지 않는다(약화 금지).
  - 사전·명세에 성경 인용을 쓸 때는 `check_scenes.VERSES`에서 본문을 먼저 뽑아 그 조각을 붙인다 — 기억으로 쓰지 않는다.
  - 재검 전후 대조는 규칙 칸 비교 + `spec_changed` 갈래로 낸다(새 규칙의 `(새)→낡음`은 새 낡음이 아님).
  - `rules.json`은 손 서식(규칙 한 덩어리 몇 줄)이라 `json.dump`로 다시 쓰면 diff가 수백 줄 — 문자열 삽입으로 고친다. `words.json`은 indent 2로 round-trip이 정확해 load/dump 가능(먼저 확인).
  - 루프 계약 충실성 보강(C7: 승인 원문을 `samples/…/metrics.json`에서 읽어 시험 파일에 전체 단언)은 「바이트 같음」을 꾸밀 수 없게 해 유효했다 — 승인 레시피 재현이 걸린 작업엔 같은 꼴로.

## Doc updates
- CONTEXT.md promotion: 「빈 통과 (Empty Pass)」 — 걸릴 내용은 있는데 잴 칸이 없어 검사가 통과를 내는 것(못 잼·해당 없음과 구분)
- ADR added: none
- eval: none 새로 — 실행 중 `WidenUnmeasured`·`HeldHold` 시험으로 이미 고정, 인용 대조는 기존 시험
