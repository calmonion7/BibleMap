# 2026-06-10 — GraphView 타입별 Compound 그루핑

## 계획 vs 실제

- 계획대로 간 것: `/node/{id}/neighbors/grouped` 엔드포인트, cytoscape-expand-collapse + cose-bilkent 패키지, compound parent 4개(인물/사건/그룹/장소), collapseAll 기본 접힘, buildPositions orphan 제거, 프론트엔드 빌드 성공.
- 발산:
  1. Docker 이중 스택 → `docker cp` + 재시작 임시 해결 (이전 레트로에서 예측됨, 근본 미해결).
  2. Moses의 Place=0 — 예상된 동작(모세는 1-hop Place 이웃 없음). `if (group.length === 0) return`으로 처리.

## 학습

- **버그 발견**: 그룹에 노드가 1개일 때 다른 노드로 이동 불가. `cy.on('tap', 'node', evt => onSelectNode(evt.target.id()))`가 compound parent 노드에도 걸려, expand-collapse 플러그인이 tap을 consume하거나 가짜 compound ID(`group-Person` 등)가 `onSelectNode`로 넘어가는 문제. 후속 작업 후보.
- Docker `wise-sprouting-hellman-neo4j-1` 컨테이너가 Restarting 반복 중 — 리소스 낭비. 이중 스택 근본 해결이 시급해짐.

- 다음에 다르게 할 것:
  - compound parent 노드를 tap 핸들러에서 명시적으로 제외(`if (evt.target.isParent()) return`).
  - 이중 스택 정리(wise-sprouting-hellman 컨테이너 삭제)를 다음 작업 전에 선행.

## 문서 업데이트

- CONTEXT.md 승격: 없음
- ADR 추가: 없음
