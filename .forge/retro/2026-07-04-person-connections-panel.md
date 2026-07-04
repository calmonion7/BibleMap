# 2026-07-04 — 인물 상세 시트에 "함께 등장한 인물"·"동시대 인물" 연결 섹션 추가

## Plan vs actual
- What went as planned: 백엔드 `/person/{id}/connections`(persons.py, 큐레이션 매핑 단일 출처에 배치)와 SidePanel 두 칩 섹션(인물 성품 아래·이웃 그룹 위, 기본 접힘, 빈 목록 숨김)을 계획대로 구현. 기존 "이 곳을 지난 인물" fetch·칩 패턴을 그대로 이식. curl 3케이스 + 모바일 Playwright 3케이스로 검증(예수 함께등장 5인·다윗 함께등장 숨김·아브라함 칩→여정 점프).
- Divergences: 칩 핸들러를 계획의 `onExplorePerson` → `onExploreJourney`로 교체(1건). `onExplorePerson`(=`handleExplorePerson`)는 `explorePersonId`만 바꾸고 `setActiveStage('explore')`를 안 해, overview 단계(둘러보기→책→인물)에서 연 상세 시트에서는 칩을 눌러도 여정으로 전환되지 않았다. 검증 중 발견해 CTA가 쓰는 `onExploreJourney`(=`handleSelectPerson`, 단계 전환 포함)로 바로잡음.

## Learnings
- Do differently next time:
  - **"이 인물 여정 탐험" 류 컨트롤이 overview·explore 양쪽에서 뜰 수 있으면 반드시 `onExploreJourney`(=`handleSelectPerson`, 단계 전환 포함)를 써라.** `onExplorePerson`(=`handleExplorePerson`)는 이미 explore 단계인 경우에만 동작한다(장소-인물 칩이 explore 전용이라 무사했던 케이스). App.jsx의 두 핸들러 차이는 `setActiveStage('explore')` 유무 하나뿐 — 상세 시트에 인물 점프 컨트롤을 새로 얹을 땐 이 함정을 먼저 확인.
  - **그래프 밀도 의존 기능은 fg-ask 단계의 데이터 프로브가 값을 크게 좌우한다.** 이번엔 함께등장 2-hop을 Neo4j에 직접 물어 "34인 중 15인만 존재(다윗·솔로몬 등은 단일참여자 authored 사건이라 0)"를 미리 확인해, 빈 기능 착시와 범위 오판을 막고 ②동시대(era)를 신뢰 backbone으로 앉혔다. 그래프 관계를 새로 노출하는 기능은 짓기 전에 실제 밀도부터 쿼리할 것.

## Doc updates
- CONTEXT.md promotion: none (용어 "인물 연결"은 fg-ask 그릴링에서 이미 정착, 실행 중 의미 변화 없음)
- ADR added: none (핸들러 차이는 코드베이스 함정이지 되돌리기 어려운 결정 아님)
