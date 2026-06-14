# 2026-06-13 — MapView 장소 선택 시 사건 링 자동 펼침 + 보기좋게 줌 (task 15)

> 실행은 2026-06-12, 회고/봉인은 2026-06-13(후속 task 16과 함께 묶어 정리).

## 계획 vs 실제
- 계획대로 간 것: `expandPlaceRef`/`expandedPlaceRef` 노출, selection effect에서 `isPrimary` 마커 자동 fly-out(id 가드), 인물/집단 자동 펼침 없음, fitBounds 패딩 확대 + maxZoom 하향, 모바일 시트 위 가시 영역 확보. lint 0 / build green.
- 발산:
  1. `expandedPlace`를 ref로 "승급"하되 init effect 내부 참조 7곳 일괄 치환 대신 `const expandedPlace = expandedPlaceRef` 별칭 → 기존 코드 무변경(surgical).
  2. 플랜은 `map.once('moveend')` 디퍼만 가정했으나 **fitBounds가 카메라를 안 움직이면 moveend 미발화** 케이스가 브라우저에서 재현(자동 펼침 통째 생략 → `/neighbors/grouped` 미호출). 700ms(≈fitBounds duration) 폴백 타이머 + `fired` 단발 가드로 보강.
  3. 프레이밍 수치(여백/줌)는 시작값으로 두고 실서버 사용자 눈으로 마무리하기로 — 이 미뤄둔 사람 눈 UAT가 후속 task 16(과도 줌)으로 이어짐.

## 학습
- 다음에 다르게 할 것:
  - **MapLibre `fitBounds`는 카메라가 실제로 이동하지 않으면 `moveend`를 발화하지 않는다.** `map.once('moveend')`에 후속 동작(R 계산·펼침)을 걸 때는 폴백 타이머(≈duration) + 단발 가드를 항상 함께 둘 것. 순차 처리를 moveend 단독에 의존하면 조용히 누락된다.
  - **지도 시각 검증은 헤드리스가 불안정하다.** Claude in Chrome은 navigate CDP 타임아웃으로 폐기. Claude Preview/헤드리스는 외부 타일·글리프(arcgis·protomaps)가 간헐적으로 안 떠 프레이밍/링 렌더 캡처가 불안정. **실서버(localhost:8080)에서 Playwright 네트워크+스크린샷**으로 검증하고, 최종 줌/여백 심미는 사용자 눈으로 마무리하는 패턴을 표준으로.

## 문서 업데이트
- CONTEXT.md 승급: 없음 (구현 디테일 — 도메인 용어 아님)
- ADR 추가: 없음 (되돌리기 쉬운 UI 동작 — 하드-투-리버스 아님)
