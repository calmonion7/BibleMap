# 2026-10-26 — 규칙 후보 둘(royal · 넓은 뒷벽 재질) 다른 장면 A/B — 둘 다 재현 안 됨, 승급 없음

## 계획과 실제
- 계획대로 된 것: 같은 시드 A/B 4장 · 한 묶음 · 장면 전 문항 · 장마다 5표 · 재현 안 되면 PROMPTING 30에 기록만 · 재검·시험·미커밋 해시 회귀 가드. fg-loop 한 번(재계획 0/3)에 끝남.
- 어긋난 것:
  - **「royal」이 확인 장면에 실리지 않았다** — david-prime 다른 4장면은 판 경로라 카드 차림이 파생 문구에 안 실리고 다윗이 「lean young man」(생애 단계 나눔 전 낡은 말)으로만 나옴. 나단 판 문구의 그 말을 카드 서술로 바꿔 A를 지어냄(고정 절 a_from). 지금 「royal」이 실제로 실리는 파생 장면은 없음.
  - **1차 판정 「재현 예」가 거짓이었다** — 축 문항 「후광 없음」이 「둥근 빛 번짐·후광·아치 벽감」을 묶어 A의 옆벽 아치 문·스테인드글라스 창을 잡음(이유 4/5). 후광/교회 도상으로 나눠 4장 전부 다시 판정 → 재현 아니오.
  - 뒷벽 장면은 새 검사 전이라 조건(방 바탕 가이드) 장면 넷 중 출생과 가장 가까운 두 여인을 고름.

## 배운 것
- 다음엔 다르게:
  - **규칙 후보 A/B 전에 그 낱말이 지금 어느 파생 문구에 실리는지부터 `route_prompt` 전 명세로 grep한다.** 실리는 곳이 없으면 「재현되면 카드 고침(4장면 함께)」 같은 효과 추정이 성립하지 않고, 확인 장면을 지어내야 한다(이번엔 a_from).
  - **기계 축 문항은 결함 하나만 묻는다.** 「후광·아치 벽감」처럼 성화 도상을 한 문항에 묶으면 다른 것(드나드는 문)을 잡아 결론이 뒤집힌다. 판정 뒤엔 다수결 수만 보지 말고 **틀림 이유를 읽어** 축 결함을 본 것인지 확인 — 기준표대로 「예」였어도 이유가 다른 것이면 문항 결함이다.
  - **A/B에서 「축 밖 문항이 크게 달라짐」은 규칙 근거가 아니다.** 두 여인 B가 칼·교회 도상·가드 3문항에서 나았지만 문구 하나에 구도 전체가 바뀐 한 시드 흔들림 — 축 문항(결함 조건)이 A에서 아예 안 나왔으면 재현 아님으로 닫는다.
  - 출생 한 장면에서 본 결(금띠·후광)은 장면 맥락(궁 안 선 왕 · 아기 안은 어머니 도상)에 매여 있을 수 있다 — 8시드 근거라도 다른 장면 한 장으로 먼저 걸러 본 것이 원장 오염을 막았다.

## 문서 반영
- CONTEXT.md 올림: 없음
- ADR 추가: 없음
- 시험(eval): 없음(축 문항 묶음은 기계로 못 잼 · 낱말 실림 grep은 일회 확인)
- 프로젝트 노트: scripts/canon/notes/RULE-AB.md · PROMPTING 30 「task 423」 줄 · RECHECK.md 「승급 없음」 절(실행 중)
- 메모리: feedback_judge_reproducibility 덧붙임(축 문항 하나 · 이유 읽기)

## 후속 후보
<!-- followup: fu-7e2d75cb2372 | source: rule-candidates-royal-backwall | task: 423 | date: 2026-10-26 | status: open | taken: - -->
- 다윗 장년 판 경로 4장면(헤브론 즉위·예루살렘 정복·궤·나단 언약) 판 문구가 「an ancient Israelite lean young man」 — 카드 david-prime(40대 왕)와 어긋난 생애 단계 나눔(task 355) 전 낡은 말. 재검 규칙이 못 잡음(판 경로 인물 문구 ↔ cast 나이대 대조 검사 후보).
  근거: task 423 S1 — `derive_scene.route_prompt` 네 장면 출력 · notes/RULE-AB.md.

<!-- followup: fu-723581cdf048 | source: rule-candidates-royal-backwall | task: 423 | date: 2026-10-26 | status: open | taken: - -->
- 두 여인 단계 ②에서 뒷벽 재질 문구 대조 8시드 — task 423 한 시드에서 문구를 더한 B가 칼 자리 1→5 · 교회 도상(스테인드글라스) 0→5 · 가드 0→5로 나았으나 뒷벽 원리가 아닌 구도 흔들림일 수 있음. 규칙 후보 아님 — 단계 ② 시도의 대조군으로.
  근거: notes/RULE-AB.md 결과 표 · samples/rule-ab/back-wall-{A,B}-s11.png.

<!-- followup: fu-59f97a5dcb8c | source: rule-candidates-royal-backwall | task: 423 | date: 2026-10-26 | status: open | taken: - -->
- 요단 귀환 david-elder `cast_override_why` 금관 근거에 삼하 12:30(「다윗이 머리에 쓰니라」 — 귀환 앞의 [추론] 근거)이 없고 1:10(사울의 면류관)만 있음 · 12:30은 「보석 있는 한 금 달란트」 면류관인데 문구는 「a thin gold circlet」 — scripture-reviewer로 근거·모양 대조.
  근거: notes/RULE-AB.md 「요단 본문 확인」 · scenes/authored-david-returns-jerusalem.json.
