# 2026-07-03 — 솔로몬 여정 확장 (일괄 승급 — 늦은 회고, 실행 2026-07-02)

## Plan vs actual
- 계획대로 완료. 이탈 없음(분기 2건은 기존 동작 확인).

## Learnings
- Do differently next time:
  - **큐레이션 여정 수 ≠ SidePanel "사건 N"(노드 이웃 수).** 이웃 수에는 여정 파일 밖 Theographic 사건도 포함된다(솔로몬 여정 11 vs 이웃 12). 큐레이션 검증에서 두 수가 달라도 회귀가 아니다 — 여정·eventCount의 권위는 `person_events/<slug>.json`.
  - **코드 무변경 데이터 갱신은 `docker compose restart api`로 충분**(데이터는 마운트, lru_cache만 비우면 됨) — 재빌드 불요.

## Doc updates
- CONTEXT.md promotion: none. ADR added: none.
