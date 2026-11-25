# 2026-11-22 — 무리 앞줄 손 2차: 가이드 B + 여인 차림 → 5/8, 기준 한 장 모자라 되돌림 (#674)

## Plan vs actual
- What went as planned: 673 회고대로 크롭에서 찾은 원인(앞줄 여인 망토·머리천이 팔을 덮음)에 맞춰 문구를 더하고 가이드 B를 되살려 D판 740 한 판을 잼 → t.hands-crowd 5/8(15/24표) · 기준 6/8 미달로 멈춤 갈래(가이드·시험 되돌림 · 시험 OK · 명세 재검 23/40) · DoD를 갈래별로 적어 둔 덕에 멈춤 갈래 판정이 바로 됨.
- Divergences: 측정 흐름 737 0 → 738 2 → 739 4 → 740 5/8로 수단마다 꾸준히 오르는데, 채택 기준 6/8은 fg-ask가 사람 확인 없이 추천안으로 정한 값이라 한 장 차이로 두 번째 되돌림이 났다. s42 무리의 노란 무늬 인형 같은 아이를 t.children-natural이 통과시킴(문항 분해능 약함).

## Learnings
- Do differently next time: ① 같은 축을 여러 판에 걸쳐 올리는 작업은 채택 기준을 사람에게 한 번 확인받거나, 「기준 근처(±1장)는 사람 결정」 갈래를 계획에 미리 둔다 — 추천안 기준이 한 장 차이로 좋은 수단을 두 번 되돌리게 했다. ② 파생 문구가 512토큰에 가까워지면(485, 남은 27) 다음 문구를 더하기 전에 겹치는 말(「their hands」 두 번)부터 줄인다.

## Doc updates
- CONTEXT.md promotion: none
- ADR added: none

## Follow-up candidates

<!-- followup: fu-edb8606ecaf0 | source: crowd-front-hands-attire | task: 674 | date: 2026-11-22 | status: open | taken: - -->
- 무리 앞줄 손 가이드 B(무리 맨 앞줄 손을 몸 앞에, 아래팔·손 밝기 ×1.25)를 채택 기준 6/8에 못 미친 5/8에서 채택할지 사람이 정한다 — 채택하면 규칙 generate.crowd-front-hands(rules.json + test_scene_rules.CrowdFrontHands)로 굳히고 다른 무리 장면 회귀를 잰다. 또 t.children-natural이 노란 무늬 인형 아이(740 s42)를 통과시킨 분해능 약함을 문항 문구로 좁힌다.
  Evidence: t.hands-crowd 737 0/8 · 738 2/8 · 739 4/8 · 740 5/8(scripts/canon/notes/MAHANAIM-STEP23.md 737~740 절) · 740 s42 무리 크롭.
