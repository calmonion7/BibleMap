---
last_mapped_commit: no-commits-yet
mapped: 2026-06-08
---

# 테스트 전략

> 소스 코드 미존재 단계. 테스트 인프라 없음. BIBLEMAP_PLAN.md의 단계별 검증 기준을 기록.

## 현재 상태

- 테스트 프레임워크 미설정
- CI/CD 미설정
- 개발 방식: 각 Phase의 검증 기준을 통과할 때까지 루프

## Phase별 검증 기준 (수용 테스트)

| Phase | 검증 기준 |
|---|---|
| Phase 0 — Neo4j 적재 | Theographic neo4j export 적재 후 임의 인물의 가계·사건·장소가 Cypher로 조회됨 |
| Phase 1 — 단일 엔티티 상세 | `GET /node/{id}` 가 한글명 포함 이웃 목록 반환, 프론트에서 렌더 |
| Phase 2 — 지도 뷰 | 선택 사건의 발생지가 지도에 핀으로 표시, 클릭 시 사건 상세 |
| Phase 3 — 타임라인 뷰 | 시대 축에 사건 정렬, 선택 시 지도·상세 동기화 |
| Phase 4 — 관계도 뷰 | 인물 선택 시 1~2촌만 표시, 털뭉치(hairball) 없음 |
| Phase 5 — 3뷰 동기화 | 한 노드 선택이 세 뷰를 동시 갱신, 검색·큐레이션 투어 동작 |

## 검증 접근법

- 각 Phase는 수용 기준 통과를 전제로 다음 Phase 진입
- Phase 0~1: Cypher 쿼리 수동 실행 + FastAPI `/docs` (Swagger) 직접 호출
- Phase 2~4: 브라우저에서 직접 기능 확인 (수동 탐색 테스트)
- Phase 5: 전체 흐름 E2E 수동 검증

## 향후 테스트 인프라 (미결정)

- 백엔드: pytest (FastAPI TestClient)
- 프론트엔드: Vitest + React Testing Library
- E2E: Playwright 또는 Cypress
- Neo4j 테스트: 별도 테스트 DB 인스턴스 (docker-compose override)
