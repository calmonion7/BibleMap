# 2026-06-27 — 죽은 `/books` 엔드포인트 제거 (task 85, 일괄 승급 2026-10-22)

## 계획 대비 실제
- 계획대로: `/books`·`approx_years()` 제거.
- 차이: run.md 「이 데이터·생성 스크립트는 이제 런타임상 죽은 자산」이라 적었지만 용어집은 그대로 둠.

## 배운 것
- 다음엔 다르게: 런타임 경로를 지우면 그 경로를 현재형으로 설명하는 용어집 항목(CONTEXT.md 「추정연도」의 `yearApprox=true` 표시, 「Book Events」의 `/books` 오버레이·TimelineView ⚡ 칩)도 같은 작업에서 고친다 — 10-22 확인: backend/app·frontend/src에 `yearApprox`·`placementYear`·⚡ 0건, `book_events`는 `/events`(`events.py:_load_approx_book_index`)만 읽음.

## 문서 반영
- CONTEXT.md 승격: 「추정연도」(화면이 읽지 않는 저작 입력)·「Book Events」(사건 목록이 뒤집어 읽음, ⚡ 칩·`/books` 설명 뺌) 정정 — 사람 확인 2026-10-22
- ADR 추가: 없음
