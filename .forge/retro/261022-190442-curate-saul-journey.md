# 2026-07-01 — 사울 여정 큐레이션 (task 97, 일괄 승급 2026-10-22)

## 계획 대비 실제
- 계획대로: 사울 저작 사건·여정 큐레이션.
- 차이: 믹마스 context 「1Sam 13:8–14; 14:6–23」의 두 번째 구간이 books·본문에 안 실림 — 그때는 우회만 하고 넘어감.

## 배운 것
- 다음엔 다르게: 「규칙으로 우회」한 결함은 검사가 없으면 쌓인다 — 2026-10-22 재측정에서 같은 책 두 구간 누락이 15사건 16구간(기브아 창 19:9–10 포함). 원인은 `generate_person_event_verses.process_event`의 같은 bookId 중복 제거(첫 번째만). 파서와 `expand_range_label`(쉼표 여러 구간)은 이미 다 처리할 수 있었다.

## 문서 반영
- CONTEXT.md 승격: 없음
- ADR 추가: 없음
- 시험(eval): 데이터 15사건 수정이 함께 필요해 회고 안에서 바로 쓰지 않고 백로그 task 398(`person-event-same-book-ranges`)로 — `validate_event_verses`에 「context 구간 ⊆ books 라벨」 + selftest red 사례
