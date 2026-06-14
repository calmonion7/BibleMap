# 2026-06-14 — Book 데이터 파이프라인 (파트 2/4)

## 계획 vs 실제
- 계획대로 진행된 것: Book 66개 Neo4j 적재, CONTAINS_BOOK 588개, book_context/books.json 생성·주입, character_traits/people.json 31명 생성.
- 편차:
  - Book-Event 연결: 계획의 `Event.scripture` 파싱 불가 (Theographic events에 해당 필드 없음) → `Book.verses ∩ Event.verses` 교집합 방식으로 구현.
  - Person traits 대상 9명 제외(Theographic published 데이터 미수록) → 31명으로 축소.
  - ANTHROPIC_API_KEY 환경 없음 → 워크플로 서브에이전트로 LLM 생성 대체.

## 학습
- 다음에 다르게 할 것: Theographic data 구조를 가정하지 말고 적재 전 필드 존재 여부를 먼저 확인. scripture 같은 "당연히 있을 것 같은" 필드도 실제 데이터에 없을 수 있음.
- `Book.verses ∩ Event.verses` 교집합은 CONTAINS_BOOK 관계의 현재 생성 방법 — 재실행·수정 시 동일 로직 유지 필요.

## 문서 업데이트
- CONTEXT.md 승급: Book 섹션에 CONTAINS_BOOK 관계 생성 방법 추가
- ADR 추가: 없음
