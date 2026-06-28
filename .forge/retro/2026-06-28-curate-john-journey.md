# 2026-06-28 — 사도 요한 큐레이션 인물 추가 ("사랑하시던 제자" 13사건)

## Plan vs actual
- What went as planned:
  - Paul/베드로 표준 절차 동일. slug `john_the_apostle`(기존 `john_the_baptist`="세례 요한"과 충돌 회피), nameKo "사도 요한". ~12-14 목표→13사건. Run-all 배치 2/2 직접 실행.
  - Theographic 참여태그가 10개뿐이라 거기 갇히지 않고 "사랑하시던 제자" 아크를 authored 자유로 큐레이션(부름→최후만찬→십자가·빈무덤→디베랴→초대교회→에베소→밧모).
- Divergences (다음 루프가 읽을 연료):
  - **노드 nameKo 불일치 발견·수정(핵심)**: 여정 헤더("…의 여정")는 `/persons/curated`의 _NAME_KO가 아니라 **선택된 Person 노드의 nameKo**(App.jsx `explorePersonName`)에서 온다. 사도 요한 노드 nameKo가 "요한"이라 카드("사도 요한")와 헤더("요한의 여정")가 어긋남 → `data/names_ko/people.json`(deploy `inject_ko_names.py` 소스) + 라이브 neo4j 노드를 "사도 요한"으로 수정해 카드·헤더·검색 일관. 베드로는 노드 nameKo="베드로"라 일치해 무관(통과).
  - **장소 노드 부재 대체**: Golgotha/Calvary 노드 없음 → 십자가 곁·빈 무덤 occursAt=예루살렘(최근접 실재 Place). 밧모는 노드 없어 occursAt `[]`(무장소 → 트리에 계시록 구절만 표시, 지도 마커 생략).
  - 에베소 사역 구절은 단일 사건 절이 없는 전승이라 요한 서신 증언(요일 1:1–4)을 근거로 사용.

## Learnings
- Do differently next time:
  - **큐레이션 인물 추가 시 노드 nameKo를 _NAME_KO(카드 라벨)와 반드시 맞출 것** — 다르면 여정 헤더가 어긋난다. 검증 항목에 "여정 헤더 이름 == 카드 이름" 추가. 동명 인물(요한·야고보 등)은 `data/names_ko/people.json`에서 구분 명칭으로 분리.
  - 큐레이션 장면의 장소 노드가 없으면 **최근접 실재 Place로 대체하거나 occursAt `[]`(무장소)** — 새 Place 노드 생성은 보류(YAGNI). (밧모 지도 마커가 필요하면 후속 quick: 좌표 ~37.3N 26.5E.)
  - 절이 특정되지 않는 전승 사역은 그 인물의 저술/증언 본문을 근거 구절로 연결.

## Doc updates
- CONTEXT.md promotion: none
- ADR added: none (절차/데이터 정합 지식이라 회고 로그 보존)
