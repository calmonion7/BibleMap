# 2026-06-16 — 타임라인 사건-중심 재구성 (Part 1/2): 사건별 근거 성경권 칩

## Plan vs actual
- What went as planned: S1~S4 전부 계획대로. `/events`에 정경순 `books` 배열 추가(450개 사건 전부 ≥1권), TimelineView 단독 책 행을 `yearApprox` 31권으로 한정(35권은 사건 칩으로), 단권 칩→Book 패널·다권 칩→권 목록+첫 권 디폴트. :8080 UAT 통과(추정마커 정확히 31, 단권/다권 칩 노드 fetch, 콘솔 에러 0).
- Divergences (모두 경미):
  - **다권 권 목록: "팝오버" → "인라인 확장".** 플랜 S3은 "권 목록 팝오버"였으나, 다권 사건은 "외 N건" 이벤트 팝오버(`overflowY:auto, maxHeight 200`) 안에도 칩으로 등장하므로 중첩 absolute 팝오버가 잘린다. 칩 옆에 sub-chip을 인라인으로 펼치는 방식으로 전환 — 본 행/팝오버 양쪽에서 잘림 없이 동작, 첫 권 디폴트 오픈은 동일.
  - **근거 칩 클릭 시 기존 `bookFilter`(연도범위 필터)가 발동.** 책 선택→`selectedNodeMeta.label==='Book'`→타임라인이 그 권 범위로 좁혀지고 배너 노출. 기존 동작이라 그대로 둠(배너 "닫기"로 해제).

## Learnings
- Do differently next time:
  - **[Part 2 직결] 구절 뷰는 인라인 확장으로 가는 게 일관적이다.** Part 2(task 41) S3에 "구절 뷰 위치: 인라인 vs SidePanel 새 모드"라는 열린 설계점이 있는데, Part 1에서 다권 권 목록을 이미 **사건 아래 인라인 확장**으로 구현했다. 권→구절도 같은 인라인 영역에 이어 붙이면 칩→권목록→구절이 한 흐름으로 자연스럽다. 플랜의 인라인 디폴트를 그대로 진행 권장.
  - **플로팅 nav 바가 콘텐츠 최상단을 가린다(반복 이슈).** 타임라인 최상단 칩/마커는 z-index 20 nav 바(높이 48) 뒤에 들어가 좌표 기반 클릭이 nav에 가로채인다. Playwright UAT에서 `el.click()` JS dispatch로 우회했다. (기존 미해결 칩 "MapView 에러배너 nav 뒤 가려짐"과 같은 뿌리 — nav가 absolute 오버레이라 콘텐츠 상단 패딩만으론 안 가려짐. Part 2 UAT도 동일 우회 필요.)
  - **bookFilter가 UAT의 "칩 개수 비교"를 교란.** 책 선택 시 타임라인이 좁혀져 가시 칩 수가 변한다. 펼침 검증은 개수 대신 화살표 `▸→▾` 플립 같은 상태 직결 신호로 할 것.
  - **공개 API 계약 변경은 코드리뷰가 값어치를 한다.** `/events` Cypher의 `collect(CASE WHEN b IS NULL THEN NULL ...)`(NULL drop으로 빈 배열 보장)·pre-collect `ORDER BY bookOrder`(정경순)·집계 후 `e.sortKey` 정렬을 리뷰로 교차 확인 — 버그 0이지만 OPTIONAL+collect의 미묘한 지점을 빠르게 검증했다.

## Doc updates
- CONTEXT.md promotion: none (사건의 근거·Book·CONTAINS_BOOK 이미 정의됨, 새/변경 용어 없음)
- ADR added: none (사건-근거 모델은 ADR-0002에 기수록; Part 1은 그 결정을 계획대로 구현)
