# 2026-06-28 — 맵뷰 여정 정차지 선택 시 근거구절 표시

## Plan vs actual
- What went as planned:
  - 3슬라이스 모두 설계대로 전달 — S1 `EventVerses.jsx`(공유, `/event/{id}/verses` 재사용 + 권별 그룹 + ko/en 탭 + 빈상태), S2 데스크톱 `JourneyList` 인라인 구절, S3 모바일 칩 스트립 위 구절. 백엔드 무변경, 신규 ADR/CONTEXT 없음.
  - `VerseLangTabs`/`Spinner`가 이미 독립 컴포넌트라 그대로 import — 구절 렌더 마크업 재사용 의도 달성.
- Divergences:
  - **조급한 `verified: yes`**: 최초 Playwright UAT를 통과시켰으나, 실제 사용자 진입 경로를 안 밟아 3건의 결함을 놓침. 배포 후 사용자 UAT에서 드러나 fix-forward 3회(커밋 08bd624·8f8e5e5).
  - ① PC: 200px 여정 컬럼에 구절이 짓눌림 → 컬럼 290px + 구절 블록 좌측 들여쓰기 제거.
  - ② 모바일: 인물 선택 시 `handleSelectPerson`의 `selectNodeFresh`가 인물 노드까지 선택 → 상세 하단 시트 자동 오픈이 여정 칩 스트립을 덮음 → 모바일 시트를 `selectedNode !== explorePersonId`일 때만 표시(자기 자신 자동선택은 숨김, SidePanel은 DOM 잔류로 데이터는 로드).
  - ③ 동일좌표 그룹(마므레 6·7·8)은 같은 `dedupIdx` → `isActive=dedupIdx===activeStopIdx`가 그룹 전체 활성 → 6 클릭 시 6·7·8 구절 모두 펼침 → `openEventId`로 클릭한 정차지 하나만 펼치고, 외부(지도·모바일) 활성화 시 그룹 첫 정차지 기본 표시.
  - S1 lint: effect 본문 동기 `setState`(`set-state-in-effect`) 위반 → SidePanel의 `state.id===id` staleness-파생 패턴으로 전환.

## Learnings
- Do differently next time:
  - **UAT는 사용자의 실제 진입 경로를 그대로 밟는다**: 선택 직후 *무클릭 첫 화면* 상태(모바일 시트가 무엇을 덮는지)와 가독성(좁은 컬럼 실제 폭)을 평가할 것. "엔드포인트가 fetch되고 텍스트가 뜬다"만 보면 레이아웃·가림·granularity 결함을 못 잡는다.
  - **deduped 선택 인덱스를 쓸 때 granularity를 처음부터 분리**: `activeStopIdx`는 좌표 그룹 단위(dedupIdx)인데 구절 표시는 정차지(사건) 단위 — 이 차이가 동일좌표 그룹에서 다중 펼침으로 터졌다. "그룹 활성"과 "항목 표시"를 별도 상태로 설계했어야 함.
  - **테스트 데이터는 엣지 형상을 포함**: 아브라함을 썼으면서도 단일좌표 정차지(하란/우르)만 클릭하고, 같은 인물의 마므레 동일좌표 그룹(6·7·8)·모바일 시트 가림은 안 밟았다. 대상 인물의 다중-동일좌표 그룹을 반드시 포함할 것.
  - **표면별 `activeStopIdx` 의미 불일치(데스크톱 dedupIdx vs 지도/모바일 `seq-1`)는 선재 부채**(CONCERNS 기록) — 이번 그룹 버그의 토양. 다음에 여정 선택을 건드리면 이 인덱스 의미를 통일하는 걸 고려.

## Doc updates
- CONTEXT.md promotion: none (여정/정차지/근거구절은 기존 용어, 나머지는 구현 디테일)
- ADR added: none (인라인 배치·모바일 시트 규칙·openEventId 추적 모두 가역적 UX/구현 결정 — 세 조건 미충족)
