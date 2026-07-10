# 2026-07-10 — topEvents 발생/인용 구분 (task#152, 헌트 #4) + #2 range 교정

## Plan vs actual
- What went as planned: 5슬라이스 전부 — primary 판정 맵(793/793) → 라이브 마이그레이션(사건당 primary=true 1개) → 시드 스크립트 2개 → nodes.py primary 필터 → range 재계산. ADR-0012 구현. 사도행전·누가 오염 라이브 소거 확인, #2 range 동반 교정, 커밋 `76115ce`.
- Divergences:
  1. **primary 필터를 계획(topEvents)보다 넓게 — topPersons + Book 지도까지.** 같은 #4 오염이 세 파생 뷰(topEvents·topPersons·`/node/{id}/places`)에 동일 `primary` 속성으로 발현. 인접 수정 규칙으로 셋 다 필터. `events.py`(사건→기록 책, 반대 방향)는 📖 인용 칩이 정당해 미변경.
  2. **서신서 verses[0] 엣지케이스(알려진 한계).** "Abel's faith"(Heb 11:4=verses[0]) 등 신학적 회고 사건이 그 서신을 발생으로 오판정 → 히브리서 range=(-3899). 옛값도 BC라 악화 없음. "첫 참조=발생" 규약(ADR-0012)의 내재적 한계.
  3. #2 의존 역전 해소: task#151 회고가 "#2 라이브 교정 ← #4 선결"이라 예고했고, #4의 primary 필터가 range 재계산의 인용 오염을 걷어내 실제로 #2가 안전히 풀렸다(예측 적중).

## Learnings
- Do differently next time:
  - **"첫 참조=발생" 규약은 내러티브 사건엔 맞지만 서신서 신학적 회고엔 어긋난다.** verses[0]/books[0] 휴리스틱은 플래시백 인용(NT가 OT사건 인용) 케이스를 정확히 잡지만, 서신이 고대 사건을 신학적으로 논하는 경우(히 11장) 그 서신을 발생으로 오판정. 서신서는 CONTAINS_BOOK으로 연대·발생을 못 정하는 게 근본(ADR-0005) — 서신서 대표성/연대는 authored_events로만 가능. 후속에서 서신서 topEvents/range를 다룰 땐 CONTAINS_BOOK이 아닌 authored 경로를 봐야 함.
  - **파생 뷰 정화는 같은 소스 관계를 쓰는 뷰 전수를 봐야 한다.** #4가 topEvents로 보고됐지만 topPersons·지도도 같은 CONTAINS_BOOK 오염. 소스 관계에 속성을 추가하면 그 관계의 모든 소비처를 grep해 일괄 처리(단, 방향이 반대인 정당한 소비처는 제외 — events.py 📖 칩).
  - **의존 역전을 회고에 적으면 다음 태스크가 순서를 바로 잡는다.** task#151 회고의 "#2 ← #4" 예고가 이번 순서(#4 먼저)를 정확히 이끌었다. 얽힌 finding은 회고에 의존 방향을 남기는 게 값어치 있음.
- Keep: 라이브 마이그레이션 전 드라이런(판정 커버리지·mismatch 0 확인 후 적용)으로 793/793 무결 적용. primary 유일성 검사(사건당 1개)를 적용 직후 검증에 넣은 것.

## Doc updates
- CONTEXT.md promotion: **CONTAINS_BOOK 항목에 "발생(primary) vs 회고 인용" 정제 추가** — 기존 도메인 용어의 의미 refinement(첫 참조=발생, primary 필터, 서신서 한계). ADR-0012 상호참조.
- ADR added: none (ADR-0012는 fg-ask에서 이미 작성. 서신서 한계는 ADR-0012 Consequences에 유사 기술 — 신규 불요).
