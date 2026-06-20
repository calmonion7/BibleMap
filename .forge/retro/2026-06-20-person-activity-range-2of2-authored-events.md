# 2026-06-20 — 다윗·아브라함·모세 저작 이벤트 Neo4j 적재

## 계획 vs 실제
- 계획대로 된 것: david.json(17개)·abraham.json(13개)·moses.json(13개) 생성, load_person_events.py 레시피 작성, Neo4j 멱등 적재, Playwright 지도 마커 검증.
- 달라진 점:
  - **authored-place `name` 누락 버그**: task-60 enrich_place_coords.py에서 `title`만 설정하고 `name` 미설정 → API `name` 빈 문자열. task-61 실행 중 발견·수정. (task-60 retro에 공동 기록됨.)
  - **아브라함 장소 수 기대치 초과**: 목표 7개 → 실제 16개. Theographic 기존 이벤트가 아브라함에게 이미 13개 장소를 연결하고 있어, authored 이벤트 없이도 기준 달성이 가능했음. 계획 시 기존 Theographic 장소 수를 확인하지 않아 실제 authored 이벤트 필요량을 과대 산정할 수 있었음.
  - **S1·S2 직렬 처리**: 계획에서 병렬 가능으로 표시했지만 맥락 유지를 위해 직렬 처리. 결과에 영향 없음.
  - **JSON 필드명 불일치**: 계획의 pseudo-format(`places`, `titleKo`)이 실제 코드베이스 컨벤션(`occursAt`, `nameKo`)과 달랐음. 코드를 참조해 올바른 필드명 사용.

## 배운 것
- 다음에 다르게 할 것:
  - 인물 대상 authored 이벤트 추가 계획 시, **먼저 `MATCH (e:Event)-[:HAS_PARTICIPANT]->(p:Person {theographic_id: $id}) MATCH (e)-[:OCCURS_AT]->(pl:Place) RETURN count(DISTINCT pl)` 쿼리로 기존 장소 수 확인**. Theographic 이벤트가 이미 충분한 장소를 연결하고 있을 수 있음.
  - authored person event JSON 작성 시 필드명은 기존 `events.json` 형식(`occursAt`, `nameKo`, `startDate`, `sortKey`, `yearLabel`, `context`)을 그대로 따름. 계획의 pseudo-format을 맹신하지 말고 실제 코드 컨벤션 우선.

## 문서 업데이트
- CONTEXT.md 승급: **탐색 관점 — 인물 중심** 항목에 "지도 장소 수는 Theographic + authored 이벤트 합산 집계" 추가.
- ADR 추가: 없음
