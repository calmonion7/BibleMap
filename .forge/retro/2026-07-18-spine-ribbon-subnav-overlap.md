# 2026-07-18 — 상단 책갈피 리본이 스테이지 내비 탭을 덮는 겹침 해소

## Plan vs actual
- What went as planned: 계획 4슬라이스 그대로. `RIBBON_OVERHANG` 상수 단일화(S1) → 헤더 아래 bg-1 스페이서(S2) → 사이드패널 오프셋 보정(S3) → 빌드+Playwright 검증(S4). 규모가 작아 Dynamic Workflow 없이 직접 실행(계획이 예상한 소형 경로).
- Divergences: 없음. 완료기준 4/4 충족.

## Learnings
- Do differently next time: **책갈피 리본 드레이프 관용구(ADR-0026)는 "헤더 밑에 하위 내비 없는 화면"(허브)만 기준으로 설계돼, 하위 내비 바가 헤더 바로 밑에 붙는 나머지 스테이지(탐험·개요·책·족보·리더 등)에서 리본 꼬리가 탭을 덮는 겹침이 있었다.** 전역 헤더 밑에 무언가를 드리우거나 덧대는 요소를 추가·수정할 땐 "하위 내비 있는 스테이지 / 없는 스테이지" 두 경우를 함께 확인할 것. 이번엔 헤더 바로 밑 전역 스페이서(overhang 높이) 한 개로 두 경우를 동시에 처리.
- 드레이프 깊이가 `SpineHeader`(리본 높이)와 `App`(여백·패널 오프셋) 두 곳에서 맞아야 해서 `RIBBON_OVERHANG` 상수를 export해 단일 출처로 뒀다 — 매직넘버 13이 흩어지면 어긋나는 종류의 결합.

## Doc updates
- CONTEXT.md promotion: none (신규 도메인 용어 없음 — `RIBBON_OVERHANG`은 구현 상수)
- ADR added: none (되돌리기 쉬운 레이아웃 조정 — ADR 3조건 미충족. ADR-0026 관용구는 유지)
