# 2026-06-10 — GraphView compound parent 탭 가드

## 계획 vs 실제

- 계획대로 간 것: `isParent()` 가드 1줄 추가, 빌드 성공, 배포 완료.
- 발산:
  1. 메인 frontend/node_modules 미설치 — worktree 정리 후 npm install 선행 필요.
  2. biblemap-nginx-1 bind mount가 워크트리 경로 — worktree dev 환경에서 docker-compose를 내리지 않고 merge·삭제 진행. `docker-compose up --force-recreate nginx`로 수정.

## 학습

- **워크트리 삭제(fg-done) 전에 해당 worktree의 `docker-compose down`을 먼저 실행한다.** 메인 스택 컨테이너가 삭제된 경로를 바라보는 상황을 예방.

- 다음에 다르게 할 것:
  - worktree 작업 종료 시 순서: `docker-compose down` (worktree) → merge → fg-done (worktree 삭제).

## 문서 업데이트

- CONTEXT.md 승격: 없음
- ADR 추가: 없음
