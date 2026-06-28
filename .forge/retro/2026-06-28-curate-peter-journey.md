# 2026-06-28 — 베드로 큐레이션 인물 추가 (전 생애 아크 17사건)

## Plan vs actual
- What went as planned:
  - Paul(task 92) 표준 절차 그대로: peter.json authored 큐레이션 → persons.py 2줄 등록 → generate(context 참조→books+본문) → load(neo4j 수동) → api 재빌드 → Playwright. 17사건(목표 16-18 중앙), 갈릴리 부르심→복음서 핵심→오순절→고넬료 이방선교→투옥/구출→공의회→로마 순교.
  - Run-all 배치 1/2로 직접 실행(워크플로우 불필요).
- Divergences (다음 루프가 읽을 연료):
  - **무장소 사건은 occursAt `[]`로 포함** — Paul은 18 stops 전원 좌표였으나 베드로는 복음서 형성기 사건 4개(사도 택함·물 위·반석 고백·변화산)가 장소 없음. `journey.py`가 좌표 없는 stop을 `seq:null`로 stops에 포함하고 JourneyList가 '·' 배지로 트리에만 렌더함을 코드+Playwright로 확인 → 드롭하지 않고 포함. 지도 마커만 생략.
  - **sortKey 소수점**(28.5·29.4·30.1 등): 복음서기(AD28-30)에 사건이 몰려 연내 순서가 필요. 백엔드 events.py가 `float(sortKey)` 캐스팅, TimelineView 연도필터도 숫자 처리라 호환. (Paul은 연도가 흩어져 정수로 충분했음.)
  - **Theographic 참여태그 밖 장면도 authored 자유로 추가**: 디베랴 호숫가 회복(요 21:15–19)은 베드로 Theographic 사건엔 없지만 부인→회복 아크 완성을 위해 큐레이션. occursAt 좌표는 갈릴리 노드로 해소.

## Learnings
- Do differently next time:
  - 신약 사도/예수처럼 **복음서 형성기 사건이 많은 인물은 무장소 사건이 다수** 생긴다 — occursAt `[]`로 포함하면 트리에 구절과 함께 표시되니 좌표 없다고 빼지 말 것(여정 충실도↑).
  - 사건이 한 연도에 몰리면 **sortKey 소수점**으로 연내 순서를 매긴다(yearLabel은 정수 연도).
  - occursAt 좌표는 그 인물 Theographic 사건에서 추출하되, **아크 완성에 필요한 장면은 태그에 없어도 authored로 추가**(occursAt만 실재 Place로 해소).

## Doc updates
- CONTEXT.md promotion: none (여정·저작 사건 용어 기존재)
- ADR added: none (authored 사건→Neo4j Event 결정은 ADR-0005가 커버; 위는 절차 지식이라 회고 로그 보존)
