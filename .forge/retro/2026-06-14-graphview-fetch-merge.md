# 2026-06-14 — GraphView 이중 fetch 단일화 + 잘림 표시 + fit 안정화

## 계획 대비 실제
- 계획대로 된 것: S1(단일 fetch + 클라이언트 그룹핑), S2(잘림 표시), S3(fit 이중 호출 제거) 모두 계획 범위 내 완료. eslint 0건, build 성공.
- 차이: (1) Dynamic Workflow 생략 — 21줄 수정 규모라 단일 세션 직접 구현이 더 빠름. (2) S3 시각 검증("깜빡임 줄어듦")은 헤드리스 환경에서 정량 측정 불가, 코드 논리 확인으로 대체. (3) 개발 서버 Playwright 트레이스: StrictMode 탓에 `/node/` 2회 기록 → 프로덕션(nginx)에서 1회 재확인 필요.

## 학습
- 다음엔 이렇게: 개발 서버(localhost:8081)에서 네트워크 트레이스를 찍으면 React StrictMode로 effect 2회 실행됨 — 호출 횟수 검증은 반드시 프로덕션 빌드(localhost:8080/nginx)에서 확인. 헤드리스 Playwright로는 animation/fit 시각 변화를 확인할 수 없음 — 시각적 회귀 비교가 필요한 슬라이스는 수동 확인 또는 픽셀 diff 도구를 별도로 사용.

## 문서 업데이트
- CONTEXT.md 승급: 없음
- ADR 추가: 없음
