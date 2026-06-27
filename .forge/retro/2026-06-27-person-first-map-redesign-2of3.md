# 2026-06-27 — 여정선 + 사이드 사건 리스트 (Part 2/3) [일괄 승급]

> fg-next all 자동 진행으로 retro skip됐던 것을 사후 일괄 승급(2026-06-27). 원천: `.forge/done/2026-06-27-person-first-map-redesign-2of3/run.md`.

## 계획 vs 실제
- 계획대로: 4슬라이스(여정선 line+순번 배지+방향, convexHull 제거, 사이드 사건 리스트, 양방향 동기) 전부. build/lint clean, Playwright 6/6 + 다윗 여정선 시각확인.
- 발산: 모바일 여정 리스트를 "접이식 시트" 대신 하단 110px 수평 스트립으로(기존 SidePanel 하단 시트와 z-layer 충돌 회피). activeStopIdx를 dedup 0-based로 통일.

## 배운 것 (다음에 다르게 할 것)
- **여정선처럼 데이터 `sortKey`를 직접 시각화하는 기능은 데이터 정합성 결함을 드러낸다.** `person_events/abraham.json`이 "우르 부르심"(sortKey -2091)과 "하란 출발"(-2091.5)을 역순으로 둬, 여정이 하란→우르로 뒤집혀 보인다(역사적으론 우르→하란). 코드는 sortKey대로 정확. → **person_events sortKey 검수**가 후속 과제(13인 전체 시간순 점검 권장).
- **장소 표시명은 한글 우선(`coalesce(nameKo, name, title)`).** journey 엔드포인트가 `p.title`(영문 가능)을 쓰던 것을 메인 세션에서 한글 우선으로 수정. 한글 UI에서 Place 표시명은 nameKo 우선 규율.
- **워크플로 정적검증(AST/build)은 백엔드 표시·런타임 버그를 못 잡는다.** 검증 에이전트가 컨테이너를 안 띄워 영문 장소명을 통과시킴 → 백엔드 변경 검증엔 **실엔드포인트 호출**이 필수(api 재빌드 후 curl). #87·#89와 반복된 교훈.

## 문서 업데이트
- CONTEXT.md 승급: 없음 (여정선은 UI 구현 용어; "인물 중심"은 기존 등재).
- ADR 추가: 없음 (sortKey 검수·한글 표시명·정적검증 한계는 코딩 규율/프로세스 — 코드베이스 맵 CONVENTIONS·CONCERNS에 반영, 프로젝트 아키텍처 결정 아님).
