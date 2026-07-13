# 2026-07-13 — 가계도 신규 페이지 (그래프 혈통 파생 에고뷰 + 예수 족보 무단절 + 관계 역할 라벨)

## Plan vs actual
- What went as planned:
  - 4슬라이스 모두 계획대로 달성 — S1 로더 버그 수정(부모-자식 137간선·부모보유 127명, fg-ask 예측치 정확 일치), S2 `/person/{id}/family` 엔드포인트(없는 id 빈 폴백), S3 예수 족보(마태1) 41노드 무단절 저작 보충, S4 손수 SVG/CSS 세대 트리 페이지(`#/family/<id>`, 클릭 재중심화, focus 자동스크롤, 모바일 안전).
  - 그래프 기반 파생(ADR-0019)이 예상대로 충실 — theographic 조상선이 이미 창세기 계보(이삭→…→살라)까지 깊게 나와 저작 보충은 마태1 사슬에만 국소 필요했다.
- Divergences:
  - **실행 방식: 병렬 워크플로우 대신 세션 직접 순차 실행** — 직전 book-detail 회고("직렬 의존+공유 파일 프론트는 직접 순차가 유리")를 반영. 정확히 그 형태였고 판단이 맞았다(충돌·재탐색 없음).
  - **S1 재적재를 전체 load_theographic가 아니라 부모-자식 함수만 타겟 실행** — 가법적 MERGE라 노드 속성·date_corrections 무변경. 더 외과적.
  - **S3 전용 데이터셋(genealogy.json)+전용 로더 신설** — 계획의 "authored_persons 패턴 재사용"으론 부족(간선이 기존↔기존·기존↔저작까지 필요, 노드-전용 로더로 표현 불가) → 연속-쌍 사슬 모델.
  - **동명이인 3건(나손·므낫세·요셉) 저작 노드로 우회** — 그래프 동명 매칭이 전부 다른 인물(Mnason·요셉의아들 므낫세·족장 요셉)이라 오링크 방지(ADR-0018 규율 계승).

## Learnings
- Do differently next time:
  - **신규 "페이지"의 완료 정의에 "실제 착지 뷰에서의 진입 동선"을 포함하라.** 이번 최대 헛디딤: 딥링크 URL(`#/family/<id>`)로 페이지 자체는 Playwright 검증했으나, 인물 선택 시 실제 착지하는 **소개 탭(PersonIntro, SidePanel 아님)** 에 진입 버튼을 안 넣어 사용자가 "안보임" 보고. SidePanel에만 버튼을 둔 게 원인. → 새 페이지 검증은 "딥링크로 열리나"뿐 아니라 "사용자가 실제 시작하는 화면(허브/소개 등)에서 한두 번에 도달하나"까지. book-detail 회고의 "가시성 vs 존재"의 진입-동선판.
  - **레이아웃/진입 지적은 배포본(biblemap.taebro.com, 실폰) 기준으로 확인.** 사용자는 localhost가 아니라 프록시된 prod 도메인을 폰으로 본다. 검증 Playwright를 prod 도메인+모바일 뷰포트로도 돌려 확정했다(메모리 feedback_layout_complaints_mobile 재확인).
  - **데이터 정본 원칙 > 기능 완결.** "첫째/둘째" 요청에 theographic `children` 배열이 출생순이 아님을 확인(아담 [셋,아벨,가인]·이새 David 6번째)하고, **출생순은 큐레이션 person_relations 정본 role에만** 의존, 없으면 성별+구조 폴백까지만 — 지어내지 않았다. 정본·결정성 기조 준수.
  - **배포본을 보며 반복 요청되는 UI는 작은 커밋+배포 사이클로.** 코어 배포 후 사용자가 라이브를 탐색하며 4건 연속 추가(소개 버튼→탭→역할 라벨→인물페이지 버튼), 각각 단일 관심사 커밋으로 즉시 배포. self-hosted 러너가 이 머신이라 prod=이 스택(같은 neo4j)이었고, 매 push마다 `gh run list`로 배포 성공을 특정 커밋으로 확인(무음 미배포 footgun 회피).
- 범위 밖 관찰(후속 후보):
  - **SidePanel "이웃" 중복 표시** — 상호 간선(PARENT_OF+CHILD_OF)+무방향 이웃 쿼리(nodes.py `-[r]-`)로 부모가 "부모"·"자식" 2회 노출. 내 간선 적재가 드러낸 기존 뷰 뉘앙스. → nodes.py 이웃 쿼리 방향성/디듀프.
  - **하나님이 "아버지"로 라벨** — 아담의 father 링크(theographic)+Male gender 파생. 데이터상 정확하나 창조주를 계보 부모로 표시하는 게 어색할 수 있음.
  - **재적재 내구성** — 전체 load_theographic 재실행 후 load_authored_genealogy 재실행 필요(스크립트 docstring·ADR-0019 명시). deploy.sh는 load_theographic 미실행이라 배포로는 소실 안 됨. README 재적재 순서 갱신은 후속.

## Doc updates
- CONTEXT.md promotion: none (가계도 용어는 계획 단계에서 [[가계도-family-tree]]로 이미 등재; 역할 라벨은 기존 [[인물-관계-person-relations]]의 role 개념 재사용, 신규 용어 아님)
- ADR added: none (혈통 원천 결정은 계획 단계 ADR-0019에 이미 기록; 실행 중 새 하드-투-리버스 트레이드오프 없음 — 전용 계보 로더·역할 라벨 소싱은 ADR-0019 구현 세부)
