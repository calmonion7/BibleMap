---
author: calmonion
decided: 2026-08-19 23:33
---
# `Book.startYear/endYear`는 교정 후 사건 연대의 파생값이며, 그 파생값은 교정 주입기가 닫는다

## Status

Accepted (2026-08-19, task#273)

## Context

`Book.startYear/endYear`는 그 책이 기록한 사건들의 `startDate` 최소~최대 집계값이고, 이 집계는 `load_books.py`가 수행한다. 그런데 `load_books.py`는 **업스트림 theographic `events.json`을 네트워크로 가져와** 집계한다 — 즉 Ussher형 원본 연대다. ADR-0014가 정한 정본은 그것이 아니라 `data/date_corrections/`가 덮어쓴 **교정 후 연대**다.

그래서 재시드(`load_books.py` 재실행)하면 `Book` 범위만 업스트림 연대계로 되돌아가고, `Event.startDate`는 교정 후 값으로 남아 **한 화면에 두 연대계가 공존**한다. `deploy.sh:55`가 배포마다 `inject_date_corrections.py`를 부르지만 그 스크립트는 `Event.startDate`/`sortKey`만 SET하고 `Book` 범위는 건드리지 않아, 이 갈라짐을 닫는 주체가 아무도 없었다. 실측 시점(HEAD `fcb525f`)의 실제 드리프트는 사무엘상 `endYear` `-1008`(교정 전) 1건이었는데, 재시드하면 폭이 커진다 — 잠복 결함이다.

## Decision

**`Book.startYear/endYear`는 교정 후 `Event.startDate`의 파생값으로 정의하고, 그 파생값을 다시 닫는 책임은 `inject_date_corrections.py`가 진다.** 교정 주입이 끝난 직후 `recompute_book_years()`가 `CONTAINS_BOOK`으로 연결된 사건의 교정 후 `startDate`를 집계해 범위를 다시 SET한다.

- 연도 파싱은 `load_books.py::_parse_year`를 **import해 재사용**한다 — 같은 규칙을 네 번째로 선언하지 않는다(ADR `260819-205242`의 복제 금지 원칙을 파서에 적용).
- 집계 대상은 `CONTAINS_BOOK` **전체**로, 발생과 회고 인용을 구분하지 않는 기존 의미축을 그대로 승계한다(그 구분은 별개 사안).

## Considered Options

- **`load_books.py`가 `date_corrections`를 직접 읽어 집계**: 단독 실행만으로도 정합해지는 장점이 있다. 그러나 교정 해석 로직(에코 필드 대조·이미 적용 판정)이 주입기와 **2벌**이 되고, 두 벌이 갈라지는 순간 어느 쪽이 정본인지 알 수 없다. 또 `deploy.sh`는 의도적으로 `load_*`를 부르지 않으므로(ADR `260801-195022`) 배포 경로에서는 이 수정이 아무 일도 하지 않는다. 기각.
- **별도 재집계 스크립트 신설 + `deploy.sh`에 배선 추가**: 관심사는 깔끔히 분리되지만 배포 배선이 하나 늘고, "교정을 넣었으면 그 파생값도 닫혀야 한다"는 불가분의 두 동작이 서로 잊힐 수 있는 두 스크립트로 쪼개진다. 기각.
- **파생값을 아예 없애고 런타임에 집계**: `Book` 범위는 타임라인 필터·배너가 매 요청 쓰는 값이라 Neo4j 왕복이 늘고, `load_books.py`가 심는 영구 속성을 소비하는 기존 라우트를 전부 고쳐야 한다. 이번 결함 대비 범위가 과하다. 기각.

## Consequences

- `load_books.py` 단독 실행 직후에는 여전히 업스트림 값이 남는다. 이것은 **기존 규약("로더 재실행 후 inject 재실행 필수")에 흡수**되며, 배포 경로는 `deploy.sh:55`가 항상 닫는다.
- `Book` 범위가 정본 연대계를 따르므로 타임라인의 책 필터·범위 배너가 사건 연대와 어긋나지 않는다.
- 파서가 `load_books`에 의존해 `inject_date_corrections.py`가 같은 디렉터리 실행을 전제한다(`deploy.sh`의 호출 형태와 일치).
