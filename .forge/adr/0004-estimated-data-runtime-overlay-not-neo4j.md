# 추정·보조 데이터는 Neo4j(권위 그래프) 밖 런타임 오버레이로 유지 — CONTAINS_BOOK 주입 금지

추정연도(`book_years_approx`)·책-사건 약연결(`book_events`) 같은 **추정·낮은권위 데이터는 Neo4j에 주입하지 않고** 정적 JSON으로 두고 `/books` 엔드포인트가 런타임에 각 책에 오버레이한다. 이유: (1) 검증된 theographic **권위 그래프와 추정 데이터를 분리**, (2) inject·마이그레이션·재빌드 스텝 불필요(`./data:/app/data` 마운트라 JSON만 고치면 반영), (3) 특히 `CONTAINS_BOOK`은 "구절 교집합 = 사건의 근거"라는 의미를 갖고 `/events`(events.py)가 이를 **근거 칩으로 내보내므로**, 의미가 다른 추정 연결(집필 배경·저자)을 같은 관계에 주입하면 사건 행의 📖 근거 칩이 오염된다.

## Considered Options

- **(채택) 런타임 JSON 오버레이** — `data/book_events/books.json`을 `/books`가 `events` 배열로 실어 보냄. 권위 그래프 무오염, 마이그레이션 스텝 0, 마운트라 데이터만 고치면 반영. `book_years_approx` 선례와 동일.
- **(반려) Neo4j `CONTAINS_BOOK` 주입** — task 43 계획의 원안. 추정 연결을 권위 관계에 섞어 사건 근거 칩 오염, deploy.sh inject 스텝 추가, 재빌드 필요.
- **(반려) 별도 관계 타입(예: `RELATES_TO_BOOK`)** — 그래프 복잡도만 늘고 "추정 데이터를 권위 그래프에 넣는다"는 근본 문제는 그대로.

## Consequences

- 되돌리기 비용 **중간**: 한번 `CONTAINS_BOOK`에 주입해 `/events`가 근거로 소비하기 시작하면 "진짜 근거 ↔ 추정 링크" 분리가 비싸다(관계에 마커를 새로 달거나 재적재 필요) → 그래서 ADR로 남긴다.
- 이 결정은 **두 번 반복**되었다(2026-06-15 `book_years_approx`, 2026-06-17 `book_events`). 1차 때는 retro 로그(2026-06-15 timeline-scripture-book-markers)에만 "고치려 Neo4j로 옮기지 말 것"으로 남겼으나, **그 캡처가 task 43 계획이 또 주입을 제안하는 것을 막지 못했다** — fg-run이 실행 전 설계 충돌을 다시 surface해야 했다. 그래서 retro 로그보다 눈에 띄는 ADR로 승급한다.
- 앞으로 새 추정·보조 데이터는 동일 패턴(정적 JSON + 엔드포인트 런타임 오버레이)을 따르고, `CONTAINS_BOOK` 등 의미가 정해진 권위 관계에는 주입하지 않는다.
