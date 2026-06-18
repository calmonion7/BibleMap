# 2026-06-19 — 고아 구절 기반 사건 추가 파이프라인 (task 51)

## 계획 대비 실제
- 계획대로 된 것: Neo4j 적재(Event 20개 + CONTAINS_BOOK 20개), 기존 사건 회귀 없음, 타임라인 검색·📖 칩 연동 확인.
- 발산:
  - **S1 실행 방식**: `ANTHROPIC_API_KEY` 없어 generate 스크립트 직접 실행 불가 → LLM이 theographic JSON 조회 후 events.json 직접 생성 (task 47·48과 동일 패턴, 3회 반복).
  - **Neo4j 스키마 전제 오류**: 계획에서 `Event.verses`, `Book.verses` 프로퍼티가 있다고 전제했으나 실제로 두 프로퍼티 모두 없음 → covered_set은 Theographic events.json에서, CONTAINS_BOOK은 book_id 직접 사용으로 대체.
  - **S3 검증**: Playwright 타임라인 행 스크롤 대신 검색창 → SidePanel 경유로 검증.

## 학습
- 다음에 다르게 할 것:
  - **generate 스크립트 = 레시피 아티팩트, 데이터 = LLM 직접 생성** — 계획 단계부터 이 방식으로 기술할 것. 스크립트 실행을 전제하는 슬라이스를 쓰지 않는다 (ADR-0006).
  - **Neo4j 관련 계획 시 그릴링 단계에서 스키마 먼저 확인** — `MATCH (e:Event) RETURN keys(e) LIMIT 1` 같은 간단한 쿼리로 실제 프로퍼티를 검증한 뒤 Cypher를 설계한다.
  - **Playwright 칩 검증은 `has-text()` 선택자로** — `'[class*="chip"]:has-text("룻기")'` 패턴이 DOM 전체 텍스트 검색보다 신뢰도가 높다. 칩 렌더 여부를 실제 DOM 요소로 확인.

## 문서 업데이트
- CONTEXT.md 승급: 없음
- ADR 추가: ADR-0006 (데이터 생성: generate 스크립트 레시피 아티팩트 + LLM 직접 생성 패턴)
