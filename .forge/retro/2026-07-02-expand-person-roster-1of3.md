# 2026-07-02 — 얇은 인물 2인 보강 (세례요한 4→7 · 이삭 5→8)

## Plan vs actual
- What went as planned: 계획 그대로. 실재-노드 최저비용 레인(restart만) 재검증, proxy(유대 산골→예루살렘, 브엘라해로이→브엘세바)·소수점 sortKey(27.5/28.5, -1963) 지침 그대로 적용. 신규 6사건 books 파싱 성공률 100%(refs 없음 0), 구절 65절 null 0.
- Divergences: 미세 1건 — 어린 양 증거 구절을 요 1:29–36 → 1:29–37로 1절 확장(제자들이 따르는 마무리 절).

## Learnings
- Do differently next time: 여정 API 응답 키는 `events`가 아니라 `stops` — 검증 스크립트 작성 시 `/person/{id}/journey` 응답 형태를 먼저 눈으로 확인할 것(이번엔 잘못 짚어 한 번 헛돌음). 그 외 절차는 기존 enrich-thin-person-events 회고의 체크리스트가 그대로 유효(약어 규율·기존 사건 선확인·proxy).

## Doc updates
- CONTEXT.md promotion: none
- ADR added: none (기존 레인·ADR-0005 커버)
