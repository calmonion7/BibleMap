# 2026-06-10 — Map 마커 UX — GeoJSON 레이어 + 레이블

## 계획 vs 실제

- 계획대로 간 것: `/node/{id}/places` 엔드포인트, GeoJSON `places-source`/`places-circle`/`places-label` 레이어, 초기 마커 없음(EMPTY_GEOJSON), 레이블 겹침 방지 모두 계획과 일치.
- 발산:
  1. `HAS_PARTICIPANT` 관계 방향 오류 — `(Person)→[:HAS_PARTICIPANT]→(Event)` 로 작성했으나 실제 방향은 `(Event)→[:HAS_PARTICIPANT]→(Person)`. 빈 배열 반환으로 발견, 수정.
  2. Docker 이중 스택 — `biblemap-*`와 `wise-sprouting-hellman-*` 두 스택 병존. nginx가 `biblemap-api-1`을 바라봐서 `docker cp`로 임시 해결. 근본 원인 미해결.
  3. uvicorn `--reload` 없음 — 코드 변경 시 수동 재시작 필요. 개발 불편.

## 학습

- 다음에 다르게 할 것:
  - Cypher 쿼리 작성 전 CONTEXT.md의 관계 방향(탐색 관점 항목)을 먼저 크로스 체크.
  - Docker 이중 스택 근본 원인 해결 필요 (후속 작업 후보).
  - uvicorn `--reload` 추가 필요 (후속 작업 후보).

## 문서 업데이트

- CONTEXT.md 승격: 없음
- ADR 추가: 없음
