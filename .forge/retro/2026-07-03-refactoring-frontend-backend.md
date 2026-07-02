# 2026-07-03 — 프론트·백엔드 리팩터링 (일괄 승급 — 늦은 회고, 실행 2026-06-19)

## Plan vs actual
- 계획대로 완료. 이탈: S4 Cypher 문법 1건(아래).

## Learnings
- Do differently next time:
  - **Cypher에서 `collect() AS all … size(all)` 패턴은 이 Neo4j 버전에서 집계 alias에 `size()`를 못 쓴다**("Insufficient parameters for function 'size'"). 총계+상위 N을 함께 뽑을 땐 `WITH count(m) AS total, collect(...)[0..50] AS rows` 순서로 집계를 분리할 것 — 의미 동일, 결과 일치 확인됨.

## Doc updates
- CONTEXT.md promotion: none. ADR added: none.
