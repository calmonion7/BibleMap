# 2026-11-23 — 다윗의 유언 막힘 풀기 1/2: 누운 꼴·누운 몸 크기 규칙·말 속 곁 장면 → 관문 통과 (#676)

## Plan vs actual
- What went as planned: 막힘 셋(figure-scale·height-ratio 못 잼 · speech-inset)을 GPU 없이 풀어 `spec_failures` `([], {})` · 다른 26장면 가이드 화소 불변 · 시험 240 → 246 · 명세 재검 23/40 → 25/41. 기준표 → 꼴 → 규칙 → 명세 순서가 그대로 맞았다.
- Divergences: ① 기준표 `lying_rise`를 처음 0.31로 셈하며 머리 둥근 끝을 빠뜨려 그림에서 머리가 구역 위로 나감 → 0.35. ② 꼴이 세 번 다듬어짐(가는 막대 위몸 → 굵게 하니 머리가 묻힘 → 옆에서 본 가슴 두께로). ③ 새 침상 상자가 먼저 쓴 구름 틀과 겹쳐 구름을 줄임 — 곁 장면(S5)을 구역 확정(S4)보다 먼저 병렬로 돌린 탓. ④ 구절 검토가 두 번 돌고(틀림 4 → 1) 마지막은 검토자 제안 문구를 그대로 넣었는데, 그 문구의 인용(「백향목 기둥 위에 백향목 들보」)이 원문 글자와 달라 `spec.quote-matches-verse`에 걸림 → 원문으로 고침. ⑤ 같은 과대(아 3:11 [직접])가 나단 곁 장면에도 있어 글만 같이 고침.

## Learnings
- Do differently next time: ① 새 가이드 꼴은 코드보다 먼저 기준표 셈을 「그려지는 모든 부위의 끝점」(머리 둥근 끝·몸 두께)까지 적고, 첫 그림을 구역 테두리와 함께 그려 넘침부터 본다. ② 곁 장면 구름 자리는 인물 구역에 기대므로 구역을 바꾸는 슬라이스 뒤에 두거나, 병렬로 돌리면 구역 확정 뒤 `inset_errors`를 다시 돌리는 단계를 계획에 적는다. ③ 검토자가 낸 고침 문구도 인용은 원문 파일(`data/bible/verses.json`)에서 글자 그대로 옮긴다 — 관문 검사가 잡아 주지만 한 바퀴 버린다. ④ 같은 근거 문구를 다른 장면에서 복사해 왔으면(cast_override_why) 검토 지적을 받은 즉시 원본 장면도 같이 고친다.
- Confirmed: 막힘을 「못 잼」인 채 두고 빈 통과(선 사람만 가이드)를 거부한 단계 ① 판단이 맞았다 — 누운 몸 규칙이 옛 상자(침상 길이의 1.4배)를 실제로 잡았다.

## Doc updates
- CONTEXT.md promotion: none
- ADR added: none
- 그 밖: rules.json `generate.lying-scale` · scale.json body 넷 · scene-authoring 함정 한 줄 · notes/CHARGE-STEP1.md·CHARGE-STEP23.md
