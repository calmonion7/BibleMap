# 2026-07-02 — 모바일 여정 구절 읽기 모드 (스트립 42dvh→90dvh 확장)

## Plan vs actual
- What went as planned:
  - 3슬라이스 전부 설계대로 전달. **선택적 prop으로 모드 분기** — `EventVerses`에 `heading`/`onClose`(있으면 읽기 레이아웃: 상단 고정 헤더 + 절 본문 독립 스크롤), `JourneyList`에 `readingEventId`/`onReadingChange`(있으면 controlled=모바일, 여정 행 숨기고 그 사건만 단독 렌더). `App`이 `readingEventId` 소유 → 모바일 오버레이 높이 42↔90dvh 전환 + 노출 지도띠 tap-catcher.
  - 새 컴포넌트·gesture·SidePanel 시트 우선순위 상태머신 없이 완료(그릴링에서 A안 대신 B안 선택한 대로). 백엔드·데이터 무변경.
  - 실기기 경로 Playwright UAT를 처음부터 밟아 조급한 `verified` 회피 — 33절 실제 스크롤 + 헤더 고정 + 데스크톱 인라인 무회귀 확인.
- Divergences (경미, fix-forward 루프 없음):
  - **DoD의 "1364절" 검증 범위 오설정.** 그릴링 때 `event_verses/events.json` *전체*(중앙값 8·p90 45·최대 1364절)를 재서 DoD에 극단치를 넣었으나, 여정 드릴다운이 실제 소비하는 건 **authored `person_events` 사건뿐**이라 실측 최대 **33절**(아브라함 소돔 중보, 창 18:1–33). 1364절은 theographic 사건으로 TimelineView 경로에 있고 읽기 모드와 무관. 읽기 모드는 `overflowY:auto`라 길이 무관하게 흡수하므로 33절로 스크롤+헤더 고정을 검증.
  - **지도띠 tap-catcher가 얇음.** 90dvh 오버레이 + nav 48px → 노출 지도 밴드 실효 ~36px(화면 y≈48~84). 동작은 함(y=66 탭 시 닫힘). 주 닫기는 `▾ 여정으로` 버튼, 지도띠 탭은 보조.

## Learnings
- Do differently next time:
  - **데이터 극단치를 DoD에 인용하기 전에 "그 기능이 실제로 소비하는 경로/부분집합"의 분포를 재라.** 전체 오버레이가 아니라 *해당 화면이 도달하는* 데이터를 측정해야 한다. 이 프로젝트 경로 구분: **여정 구절 = authored `person_events`(≤33절)**, **타임라인 사건 근거 구절 = theographic `event_verses`(최대 1364절)** — 같은 `EventVerses`를 쓰지만 도달하는 데이터 모집단이 다르다.
  - **dvh 오버레이 높이를 정할 때 고정 nav 높이를 빼고 "실효 노출 밴드"를 계산하라.** `100dvh - 90dvh = 10dvh`처럼 보여도 nav 48px를 빼면 실제 탭 가능 밴드는 ~36px. 바깥-탭-닫기를 얇은 밴드에만 걸지 말고, 명시적 닫기 버튼을 주 수단으로.
  - **모바일/데스크톱 분기는 새 컴포넌트 대신 "선택적 prop 유무로 모드 전환"이 깔끔.** 데스크톱 경로를 prop 미전달로 그대로 두면 무회귀가 자동 보장된다(직전 accordion 회고의 "단일 컴포넌트 통일"과 동일 선). [[feedback_playwright_testing]]
  - **Playwright 특정 행 타겟 셀렉터 함정**: `//span[…][ancestor::div[contains(.,'키워드')][1]]`는 전체 리스트 컨테이너까지 조상으로 잡아 `.first`가 엉뚱한 첫 항목을 연다. 특정 행의 자식만 노릴 땐 `parent::div[contains(.,'키워드')]`로 좁혀라(1차 UAT에서 33절 대신 2절 사건을 열었던 오탐 원인).
- Divergences 요약: 계획(B안 = 스트립 확장 읽기 모드)은 그대로 적중. 차이는 검증 범위 인용 오류 + 노출 밴드 얇음 두 경미 사항뿐.

## Doc updates
- CONTEXT.md promotion: none (새 용어 없음 — "읽기 모드"는 UI 기능명, 여정/사건/구절 용어 불변).
- ADR added: none (A→B(전용 시트 vs 스트립 확장) 선택·dvh 높이·prop 분기 모두 가역적 UX/구현 결정 — 3조건 미충족).
