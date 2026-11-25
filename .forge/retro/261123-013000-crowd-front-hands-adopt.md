# 2026-11-22 — 무리 앞줄 손 가이드 B 채택 회귀: 법궤·기혼 A/B → 기준 위반, 되돌림 (#675)

## Plan vs actual
- What went as planned: 사용자 결정(채택 + 회귀)대로 같은 명세·시드·문항에서 가이드만 A/B로 법궤·기혼 넷 판을 재고, 미리 정한 회귀 기준으로 판정 → 기준 위반(법궤 t.dance 7→4·t.hands-clear-bearers 4→1, 기혼 t.hands-crowd 5→4)이라 되돌림 · 아이 문항 좁힘은 5/5로 검증.
- Divergences: 기혼 고정 절 702에 시드별 크롭 좌표 문항이 있어 새 시드에서 판정이 KeyError로 멈춤 → 크롭 문항을 A·B 공통으로 빼고 견줌. 위반 문항 둘은 무리 밖 인물이라 가이드 B와 직접 닿지 않음(판정 흔들림 추정) — 틀린 문항 합은 두 장면 모두 줄었다.

## Learnings
- Do differently next time: ① 효과를 「노린 결함이 있는 장면」에서만 재고 전 장면 기본값으로 굳히려 하면, 결함 없는 장면에서는 효과 0에 판정 흔들림만 남아 기준을 넘기 어렵다 — 장면 의존 수단은 처음부터 장면별 스위치(명세 칸)로 설계한다. ② 회귀 기준의 「한 문항 3장 하락」은 무리와 무관한 문항까지 세면 흔들림에 걸린다 — 바꾼 꼴이 닿는 문항(무리·손·가드)으로 범위를 좁혀 적는다. ③ 시드별 크롭 좌표가 박힌 고정 절은 다른 시드에 재사용할 수 없다 — 새 판을 만들 때 크롭 문항을 먼저 걸러낸다.

## Doc updates
- CONTEXT.md promotion: none
- ADR added: none

## Follow-up candidates

<!-- followup: fu-4c8b6d87f952 | source: crowd-front-hands-adopt | task: 675 | date: 2026-11-22 | status: open | taken: - -->
- 무리 앞줄 손 가이드 B를 장면별 스위치로: 명세 guide에 무리마다 켜는 칸(예: guide.crowd_hands: front)을 두고 make_guide가 그 무리에만 앞줄 손을 그린다. 앞줄 손이 숨는 장면(t.hands-crowd가 낮은 장면 — 마하나임)만 켜고 회귀는 그 장면 안에서만 잰다. 판정 쪽 아이 문항은 좁힌 문구(745)를 마하나임 다음 고정 절부터 쓴다.
  Evidence: 마하나임 t.hands-crowd 0→5/8(737~740) · 법궤 6→6/8 · 기혼 5→4/8(741~744, scripts/canon/notes/MAHANAIM-STEP23.md task 675 절).
