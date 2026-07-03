# 2026-07-03 — 모바일 여정 정차지 시트 위 가시영역 중앙 배치 (task 117)

## Plan vs actual
- What went as planned: 계획대로 `MapView` 정차지 `easeTo`에 모바일 offset(`-(innerHeight×42dvh)/2`) 추가. `JOURNEY_SHEET_VH=42` 상수 신설로 App 42dvh와 단일화, `isMobile`은 기존 MapView 패턴 재사용. 직접 실행(eco). 모바일 Playwright로 이미지2 상태(정차지가 시트 위 가시영역 중앙) 재현, 콘솔에러 0.
- Divergences: 없음.

## Learnings
- Do differently next time: 특기사항 없음 — 무편차. 다만 MapView가 이미 fitBounds에서 하단 시트 padding(SHEET_VH, 상세패널용)을 쓰고 있었고, 정차지 easeTo는 **여정 리스트 시트(JOURNEY_SHEET_VH=42)** 맥락이라 별도 상수로 구분한 게 핵심 — "하단 시트"가 상황(상세패널 75 vs 여정리스트 42)마다 다르므로 카메라 보정 시 어느 시트가 떠 있는지 먼저 확인할 것.

## Doc updates
- CONTEXT.md promotion: none (JOURNEY_SHEET_VH는 구현 상수, 도메인 용어 아님).
- ADR added: none (가역적 UI 카메라 배치).
