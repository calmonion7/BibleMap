# 2026-06-08 — Phase 1: FastAPI /node/{id} + 한글 매핑 + React 프론트엔드

## 계획 vs 실제

- 계획대로: API 응답 형식(nameKo/nameKoMissing/neighbors), 한글 주입 스크립트, SidePanel 표시 로직, CORS·환경변수 설정 모두 계획과 일치.
- 발산:
  - 프론트엔드에 Phase 2–4 기능(MapView, TimelineView, /places·/events 엔드포인트) 포함 → **의도된 선행 구현**이었음. 계획이 현실보다 보수적이었던 것.
  - people.json 20명(계획 20~30), places.json 9곳(계획 10~15, 베들레헴 미포함). 수량 하한 충족.
  - Moses(Person)가 지도 마커에 없음 → Person은 좌표가 없고 Event → Place 경로로만 공간을 가짐. (설계 의도 확인됨)

## 학습

- 다음에 다르게 할 것:
  - Phase 경계를 넘는 선행 구현이 의도된 경우, 계획 내 비목표 항목에 "의도적 선행 구현"임을 명시하면 fg-run/회고에서 발산으로 오인되지 않음.
  - /places·/events 같은 지원 엔드포인트는 그것을 필요로 하는 프론트 슬라이스와 함께 계획하면 범위가 명확해짐.
  - Person이 지도에 직접 표현되지 않는 이유(활동 반경 = Event → Place 경로)를 계획 단계에서 명시하면 검증 기준을 "Moses 클릭"이 아닌 "Person 관련 Event·Place 조회"로 올바르게 설정할 수 있음.

## 문서 업데이트

- CONTEXT.md 항목 추가: **탐색 관점 (Navigation Perspective)** — 인물·장소·시대 세 관점과 `Person → Event → Place` 경로 설명
- ADR 추가: 없음
