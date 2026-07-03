# 2026-07-03 — /persons/curated 실패 재시도 (task 113): 여정 탐험 CTA 무음 소멸 수정

## Plan vs actual
- 계획대로 된 것: S1 전부 — App.jsx 유한 재시도(백오프+언마운트 정리+최종 warn), 빌드 성공, UAT 3/3(무장애·재시도 회복·전체 실패 열화 유지), 스크린샷 전달. 현장 결정 없음.
- Divergences (경미, 제품 수정 없음): 검증 스크립트 1회 반복 — `/persons/curated`의 제2 호출처(PersonHub 자체 fetch)가 전면 abort 시 허브를 에러 화면으로 굳혀 테스트 동선을 막음 → React 자식 effect 선실행(허브#1→App#2) 순서로 2번째 요청부터 선택 abort해 해결.

## Learnings
- Do differently next time:
  - **엔드포인트 단위 수정은 호출처 전수 grep부터.** 그릴링이 App.jsx의 fetch만 보고 범위를 굳혔는데, 같은 엔드포인트를 PersonHub도 소비하고 있었다 — 그쪽이 오히려 더 큰 무음 열화(허브 전체 에러 화면, 재시도 없음). 수정 대상이 "엔드포인트"라면 URL로 프론트 전수 grep해 호출처 지도를 먼저 그리고 범위를 정할 것.
  - **동일 엔드포인트 다중 호출처의 route abort는 테스트 동선을 막을 수 있다.** URL로는 호출처를 구분 못 하므로, React 자식 effect 선실행 순서(자식 요청이 먼저)를 이용해 N번째 요청만 선택 abort하는 패턴이 유효.
- Divergences 요약: 계획 적중, 이탈은 검증 스크립트 1건.
- 후속 후보: PersonHub `/persons/curated` fetch 재시도 없음(`PersonHub.jsx:168`) — 실패 시 허브 전면 에러 고착. 이번 task와 동일 패턴 적용 가능한 소품.

## Doc updates
- CONTEXT.md promotion: none (검증 기법·범위 교훈 — 도메인 용어집 부적합).
- ADR added: none (재시도 정책은 가역적 구현 결정 — 3조건 미충족).
