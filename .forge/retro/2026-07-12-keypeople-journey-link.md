# 2026-07-12 — keyPeople 전용 큐레이션 인물에 발자취 링크(여호수아 버그)

## Plan vs actual
- What went as planned:
  - S1 큐레이션 nameKo→id 맵 플럼빙 + S2 keyPeople 전용 이름을 그 맵으로 해석해 발자취 링크. 출애굽기 여호수아가 발자취 칩·클릭 시 여정 진입.
- Divergences:
  - 미세: S2에서 이벤트 인물/keyPeople 전용을 각각 렌더하지 않고 **단일 `mainPersons` 목록**(`{key,name,journeyId}`)으로 통합. journeyId 유무로 발자취 버튼 vs 평문을 한 경로에서 결정 → 중복 제거. 동작 동일.

## Learnings
- Do differently next time:
  - **책의 "주요 인물"은 두 데이터 소스의 합집합이다** — (a) 이벤트 참여 그래프 Person 노드(`topPersons`, id 보유 → 큐레이션이면 여정 링크 가능), (b) 책에 저작된 이름 문자열(`keyPeople`, id 없음). 나오미·보아스는 (b)에만, 여호수아는 이 책 기준 (b)에만 있으나 **다른 곳에선 큐레이션 인물**. 그래서 "발자취 링크 = topPersons 중 큐레이션"으로만 보면 (b)에 있는 큐레이션 인물(여호수아)의 링크를 놓친다. 인물 노출/링크를 만질 땐 **두 소스를 모두 고려**하고, 문자열 이름은 nameKo→id 해석으로 그래프 인물과 이어라. (이 영역은 task 163=비큐레이션 삭제 → 이후 keyPeople 병합 → task 165=keyPeople 큐레이션 링크로 세 번 연속 손댐 — 소스 이원성이 반복 함정.)
  - 이름 매칭은 nameKo 정확 일치라 별칭/이형이 다른 인물은 아직 미매칭 — 향후 링크 누락 신고 시 alias 매핑을 의심.
- Keep:
  - 큐레이션 데이터는 이미 프론트에 로드돼 있으니(useStageNavigation `/persons/curated`) 새 소스는 그 로드에 얹어 state로 추가하면 됨 — 백엔드 무변경으로 해결(eco).

## Doc updates
- CONTEXT.md promotion: none (keyPeople·topPersons는 데이터모델/구현 개념, 도메인 용어 아님)
- ADR added: none (기존 curated 데이터 흐름 확장, 되돌리기 쉬움)
