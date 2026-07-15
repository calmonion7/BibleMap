# 2026-07-15 — 하나님 의존 탭 API+UI (task 181, part 4/4)

## Plan vs actual
- What went as planned: `/person/{id}/reliance`·`/reliance/ranking`(id↔slug는 person_events participants[0], journey 동형) + `RelianceView`(도넛 게이지·6세그 mode 막대·생애 궤적·은혜 하이라이트·랭킹 모달·표본적음 뱃지·방법론 주석·양피지 구절 레이어) + 내비 탭·`#/person/<slug>/reliance` 딥링크. 랭킹(1)·은혜 하이라이트(2)·순위/백분위(4) 포함, 대비 페어(3) 비목표. Playwright 데스크톱+모바일 전 항목 통과·eslint 0·build green.
- Divergences:
  1. **데스크톱 SidePanel이 reliance 뷰를 덮었다 → 억제 조건에 reliance 추가(App.jsx:643, relations와 동형).** 자동 UAT(텍스트·API·JS에러)는 전부 통과했는데도 발생.
  2. reliance API를 slug 아닌 **id 키**로(프론트가 explorePersonId를 들고 있어 journey와 자연스러움). 랭킹 클릭은 `selectPerson(id,'reliance')`로 그 인물 의존 뷰로 직행(handleSelectPerson의 view 인자 활용) — 새 스테이지 배선 불요.

## Learnings
- Do differently next time:
  - **자동 UAT가 통과해도 레이아웃은 스크린샷 육안으로 봐야 한다.** 텍스트·API·JS에러 체크는 전부 초록이었지만 상세 패널이 콘텐츠 우측을 가리고 있었다 — 육안으로만 잡혔다. [[feedback_layout_complaints_mobile]]("레이아웃 지적은 폰 기준")와 같은 결: **인물 전용 전체화면 뷰를 새로 추가하면 App.jsx:643의 데스크톱 패널 억제 조건에 그 exploreView를 반드시 추가**(relations·intro·reliance가 자기 상세 패널을 억제한다). 모바일은 sheetOpen(selectedNode≠explorePersonId)이 이미 자기 억제.
- Keep: 새 인물 탐험 탭은 relations 뷰를 템플릿으로(exploreView 값 + 조건부 본문 + urlState 접미사 + 패널 억제) 복제하면 배선 누락이 적다.

## Doc updates
- CONTEXT.md promotion: none (part 3에서 [[하나님 의존도]]·[[하나님 상호작용 mode]] 이미 반영; 여기 학습은 프론트 배선 관행 — 구현 세부)
- ADR added: none
