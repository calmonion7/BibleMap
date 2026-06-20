# 2026-06-20 — 성경 주요 장소 데이터 보강 (authored-place 16개 신규 생성)

## 계획 vs 실제
- 계획대로 된 것: 핵심 여정 장소 신규 생성(16개), places.json 형식, enrich 스크립트 레시피 아티팩트, Neo4j 적재.
- 달라진 점:
  - "기존 노드 좌표 보강"은 실질적으로 발생 안 함. Theographic Place 대부분 이미 좌표 보유; 좌표 없는 5개(Eden/Gihon/Havilah/Nod/Pison)는 여정 무관 전설 지명.
  - authored-place 노드에 `title`만 설정하고 `name` 미설정 → API `places` 응답에서 name이 빈 문자열로 반환되는 버그 발생. Neo4j 직접 패치 + 스크립트 수정으로 즉시 수정.

## 배운 것
- 다음에 다르게 할 것:
  - authored Place 노드 생성 시 **`name`과 `title` 양쪽 모두 설정**. API `/api/node/{id}/places`는 `props.get("name", "")` → 빈 문자열 방지.
  - 장소 좌표 보강 작업 시작 전, 먼저 `MATCH (p:Place) WHERE p.latitude IS NULL RETURN p.title, p.theographic_id` 쿼리로 실제 갭을 확인하라. 계획에서 "기존 좌표 없는 노드 보강"이라 해도 Theographic DB 상태에 따라 실작업이 0건일 수 있음.

## 문서 업데이트
- CONTEXT.md 승급: 없음 (구현 상세)
- ADR 추가: 없음
