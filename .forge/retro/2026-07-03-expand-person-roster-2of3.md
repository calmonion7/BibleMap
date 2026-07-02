# 2026-07-03 — 인물 로스터 확장 2of3 (일괄 승급 — 드라이브 자동 스킵분의 늦은 회고, 실행 2026-07-02)

## Plan vs actual
- 계획대로 완료. 이탈: occursAt id 초기 오기입(적재 전 교정, 결과물 영향 없음).

## Learnings
- Do differently next time:
  - **authored Event의 `occursAt` id는 임의 작성 금지 — place_coords/Neo4j에서 조회 후 기입.** 임의 id는 적재 시 MATCH가 조용히 누락돼 장소 연결이 사라진다(여리고·도단·사마리아를 임의 rec id로 넣었다가 `authored-place-*` 실id로 교정한 사례). 인물 큐레이션 데이터 저작 시 장소 id 실측이 선행 단계다.

## Doc updates
- CONTEXT.md promotion: none. ADR added: none.
