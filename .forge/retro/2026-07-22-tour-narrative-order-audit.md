# 2026-07-22 — 투어 서사 순서 전수 정비 (task#232) [일괄 승급]

## Plan vs actual
- What went as planned: 전수 감사→교정→검증 3슬라이스 그대로. 교정 규약(연도 오류=startDate·yearLabel·sortKey 동시 / 연내 순서만=소수 sortKey 오프셋) 확립.
- Divergences(중간): 위반 규모가 계획 예상(예수 방문 1건+동률 6건)의 몇 배 — 3군집 16사건(출애굽 BC1406 뒤엉킴 8건, 야곱 축복 -1870 오배치, 마리아 십자가 34).

## Learnings
- Do differently next time:
  - **"기지 위반 N건 교정" 태스크도 전수 감사를 계획에 넣어라** — 예상 밖 발견(1건→16건)이 이 태스크의 실제 가치였다. 이후 #233~236·#237~238에서 같은 패턴이 반복 적중(추정 불변 35건→실제 10건 등).
  - 연대 교정 규약 2형(연도 자체 오류 = 3필드 동시 이동, 서사 순서만 = 소수 오프셋+yearLabel 불변)은 이후 전 연대 태스크의 표준이 됐다 — yearLabel 변경엔 성경 서사 근거 필수.
- 특이사항: 잔존 동률 0을 assert에 포함한 것이 이후 태스크의 "인접 동률" 검출 표준이 됨.

## Doc updates
- CONTEXT.md promotion: (아크 공통 — nt-date-corrections 회고에서 일괄, "사건 연대" 절)
- ADR added: none (교정 규약은 ADR-0014 계열의 적용)
