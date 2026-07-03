# 2026-07-03 — 여정 심화 6인 (task 115): 여호수아·다니엘·사무엘·엘리야·엘리사·요셉 +25 사건

## Plan vs actual
- What went as planned: 4-phase Dynamic Workflow(6인 병렬 큐레이션 → 신규 장소 배리어 취합 → place 반영 → 구절베이킹·적재 → 검증)로 S1~S4 수행. 6인 심화 완료(여호수아 11·다니엘 10·사무엘 10·엘리야 11·엘리사 11·요셉 12 = +25). 구절 25건 베이킹, OCCURS_AT 278·HAS_PARTICIPANT 286·CONTAINS_BOOK 295 적재. 저니 API + Neo4j + Playwright(여호수아·엘리사)로 검증, 콘솔에러 0.
- Divergences: (1) 다니엘 +4(10)로 목표 ~11에 1 부족 — 큐레이션 에이전트가 addedCount 5로 과보고, 실제 4개 작성. 밴드 내라 수용. (2) 엘리사 검증 `placesConnected: false`는 오탐(false positive) — occursAt의 `rec5dSSsOutWlH2fW`(요단강)가 authored 아닌 Theographic Place라 places.json엔 없고 Neo4j엔 좌표와 함께 존재. (3) 신규 장소 7개 제안 중 endor 기존존재 dedup → 6개 반영.

## Learnings
- Do differently next time:
  - **occursAt 장소 검증은 rec* id를 Neo4j로 해석하라 — 로컬 `place_coords/places.json`만 보면 오탐.** place_coords는 authored 장소 + rec 장소 좌표 백필용 파일이라, authored 사건이 **기존 Theographic 장소(rec*)를 재사용**하면 그 파일엔 없지만 Neo4j Place로는 정상 존재한다. 검증 에이전트가 파일 기준으로만 봐 엘리사 3사건을 "장소 누락"으로 오탐. 앞으로 여정 검증 완료기준에 "rec* id는 Neo4j MATCH로 확인, authored-place-*만 places.json 대조"를 명시할 것.
  - **fan-out 에이전트의 self-report 개수를 믿지 말고 파일로 실측.** 다니엘 에이전트가 addedCount 5로 반환했으나 실제 4개. sonnet 병렬 큐레이션은 자기 산출 개수를 낙관 보고할 수 있다 — 검증은 `len(json)` 파일 실측이 권위.
  - **공유자원 선반영 패턴이 다시 유효.** 에이전트가 place_coords를 직접 쓰지 않고 newPlaces를 *반환*만 하게 하고 배리어 후 메인이 일괄 반영 → 병렬 쓰기 충돌 0. ot-1of2 회고의 "공유자원 선반영 → fan-out"을 "에이전트는 반환, 오케스트레이터가 병합"으로 구현한 형태. 다인 데이터 큐레이션의 표준 골격으로 재사용.
  - `generate_person_event_verses.py`가 context의 EN 약어를 파싱해 `books`를 자동 생성하므로, 에이전트는 bookId를 손으로 쓸 필요 없이 **context EN 약어만 정확히** 넣으면 된다(오류원·부담 감소). 풀네임 금지 원칙(enrich-thin 회고)이 books·구절본문 둘 다를 좌우.
- Divergences 요약: 계획 대체로 적중(+25/목표+26), 이탈은 다니엘 1 undercount와 검증 오탐 1건뿐.

## Doc updates
- CONTEXT.md promotion: none — 여정·저작 사건·startDate 기존 정의로 충분, 새 용어 없음.
- ADR added: none — 워크플로우 구조·검증 방식은 가역적 프로세스 선택(3조건 미충족). rec*-vs-Neo4j 검증 교훈은 이 retro가 다음 여정 작업 fg-ask/fg-run에 먹이는 fuel.
