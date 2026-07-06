# 2026-07-06 — 테마 큐레이션 투어 메커니즘 + 다윗과 통일왕국 투어 (v1)

## Plan vs actual
- What went as planned:
  - 5슬라이스 골격 그대로. ADR-0011 오버레이 모델이 깔끔히 성립 — 투어를 `data/tours/<slug>.json`의 eventId 참조로만 정의, 백엔드가 person_events에서 `eventId→본문` 인덱스로 해석하고 `journey.py`의 `_fetch_place_coords`·stop 구조를 재사용. **신규 Neo4j 노드·주입 0**, 배포 시드 단계 추가 불필요.
  - explore 스테이지 재사용 전략 유효 — 지도·JourneyList·타임라인 렌더 신규 코드 없이 "인물 대신 투어가 stops 공급"으로 성립. `explorePersonId=null` 경로는 overview 스테이지 선례라 SidePanel·인물 크롬이 안전했다.
  - 하이브리드 실행(독립 S1·S2는 sonnet 백그라운드 병렬, 리스크 높은 프론트 상태머신은 본 세션 직접)이 적중 — 상태머신 통합에서 실제 버그가 나왔고, 이를 직접 다뤄 즉시 잡았다.
- Divergences:
  - **런타임 크래시(UAT 포착)**: `TimelineView`가 `personFilter`를 `Set.has()`로 소비하는데 투어 필터를 배열(`journeyStops.map`)로 넘겨 `O.has is not a function`. TimelineView는 map 뷰에서도 `display:none`으로 항상 마운트돼 **투어 진입 즉시** 터졌다. → `useMemo`로 참조 안정화한 `Set`(`tourEventIds`)으로 수정.
  - **계획 밖 보강 — 투어 지도 초기 프레이밍**: person 모드는 personId 기반 places fetch가 `fitBounds`로 지도를 맞추나, 투어(personId=null)는 그 경로를 안 타 초기 지도가 중동 전체로 남았다. `MapView` journeyStops effect에 `!personId` 게이트 `fitBounds` 추가.
  - **서브에이전트 잔여물**: S2 에이전트가 테스트용 `data/tours/david-life.json`(1정차지 샘플)을 임의 생성 → non-goal 위반이라 제거.

## Learnings
- Do differently next time:
  - **공유 컴포넌트에 새 데이터원을 물릴 때, 기존 prop의 자료형 계약을 먼저 확인하라.** `personFilter`가 Set(`.has()`)인지 배열(`.includes()`)인지 같은 계약은 타입 없는 JS에선 호출부만 봐선 안 보인다. 소비처(`.has(`/`.includes(` 사용) 한 줄 grep이 크래시를 사전 차단했을 것.
  - **explore 같은 화면을 "다른 구동원"으로 재사용할 땐, 기존 구동원(personId)이 *암묵적으로* 하던 부수효과를 목록화하라.** 지도 프레이밍은 personId에 얹혀 있어 투어엔 자동 전이되지 않았다. 재사용 전 "personId가 트리거하던 것"을 훑었으면 프레이밍 공백을 계획에 넣었을 것.
  - **eco 서브에이전트 출력은 검수·정리 대상.** sonnet 에이전트가 명세 밖 테스트 스캐폴딩(샘플 투어)을 남겼다 — 위임 결과는 diff를 확인하고 잔여물을 치운다.
  - **항상 마운트되는 숨은 뷰(`display:none`)를 잊지 말 것.** 타임라인은 map 뷰에서도 마운트돼 있어 "타임라인 탭을 아직 안 눌렀는데" 크래시가 났다. 조건부 렌더가 아니라 CSS 토글이면 진입 즉시 렌더 경로가 돈다.

## Doc updates
- CONTEXT.md promotion: **화면 단계 (Stage)** — explore 정의를 "선택한 인물의 여정 또는 테마 투어" + 상호배타로 갱신, tours 스테이지 추가(3→4단계). ([[테마 투어]] 용어는 fg-ask 그릴링 시 이미 추가됨)
- ADR added: none (투어 오버레이 모델은 그릴링 시 ADR-0011로 이미 기록)
