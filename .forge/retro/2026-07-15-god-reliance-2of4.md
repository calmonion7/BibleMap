# 2026-07-15 — 전체 성경 구절↔인물 색인 적재 (task 179, part 2/4)

## Plan vs actual
- What went as planned: `build_verse_persons.py`로 theographic verses.json에서 구절↔인물 색인 산출(16,513절·28,240링크), `overlays.verse_persons()` + `/verse/{id}/persons` 엔드포인트(우리 적재 Person만 이름 해석). 창12:1→아브라함+하나님, 요3:16→하나님+예수, 없는 절→빈 폴백 실측.
- Divergences: **계획이 예상한 "id 매핑 작업"이 사실상 불필요했다.** theographic verses 레코드가 `verseID`(우리 정본 사전 키 `BBCCCVVV`와 **완전히 동일**)와 `people`(구절별 인물 rec id 배열)을 직접 보유 → 역변환·매핑 없이 그대로 투영. verseID 매핑 실패 0.

## Learnings
- Do differently next time: **theographic verses.json은 구절 단위 교차참조의 보고다** — `verseID`(=BBCCCVVV), `people`, `event`, `chapter`, `book`, `yearNum`을 절마다 들고 있다. 앞으로 구절 단위 데이터(구절↔사건, 절별 연도 등)가 필요하면 저작하지 말고 **이 테이블을 먼저 확인**할 것(로더가 지금 people/places/events/peopleGroups만 fetch하고 verses는 안 불러올 뿐). 오버레이(노드 미주입, ADR-0011)로 다뤄 그래프 31k 노드 확장을 피한 것도 유지.

## Doc updates
- CONTEXT.md promotion: none (데이터 인프라·구현 사실 — 도메인 용어 아님)
- ADR added: none
