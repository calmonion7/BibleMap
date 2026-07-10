# 2026-07-10 — 타임라인 인물 필터 소실 수정 (task#153, 헌트 #10)

저이탈 세션. 계획 2슬라이스 그대로 — `personEventIds`를 `selectedNode` 결합에서 `explorePersonId` 구동(App.jsx effect, tourEventIds와 대칭)으로 이전, useNodeSelection에서 결합·미사용 `apiGet` import 제거(orphan 정리). Playwright 결정적 repro(여정 stop 클릭 후 필터 유지) PASS, 빌드 클린, 커밋 `6f73d31`. 예상 밖 사항 없음.

## Plan vs actual
- 계획대로: S1(App 이전)·S2(useNodeSelection 정리) 그대로. 필터 의미(`/event-ids` 전체 참여) 유지.
- Divergences: 없음.

## Learnings
- Do differently next time: 없음(신규 교훈 없음 — "탐험 대상 구동으로 상태를 묶는다"는 tourEventIds 선례를 그대로 대칭 적용한 것). 남은 #11+#12는 useStageNavigation curated fetch/게이팅 한 덩어리로 별도 fg-ask.

## Doc updates
- CONTEXT.md promotion: none. ADR added: none (가역 버그픽스).
