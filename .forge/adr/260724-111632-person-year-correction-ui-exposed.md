---
author: calmonion
decided: 2026-07-24 11:16
---
# Person 출생/사망 연도도 교정 대상 — UI 노출로 ADR-0014 Person 조항 부분 개정

## Status

Accepted (2026-07-24) — ADR-0014의 "Person `birthYear`/`deathYear`는 재정렬하지 않는다" 조항을 부분 개정.

## Context

ADR-0014는 Person `birthYear`/`deathYear`를 "백엔드·프론트 어디서도 안 써 UI 미노출"이라는 근거로 교정 대상에서 제외했고(셋 전치 오타만 예외), consequence에 "향후 인물 출생/사망 연도를 UI에 노출하려면 이 ADR을 먼저 재검토"라고 명시했다. 그런데 그 이후 추가된 인물 소개 기능 — `frontend/src/PersonIntro.jsx`(생몰 라벨 `formatLifespan`)·`PersonMiniCard.jsx` — 이 두 필드를 **실제로 화면에 표시**한다. 그 결과 theographic 원본의 내부 모순(사망<출생: Samson, 유다 왕 Ahaziah·Jehoram)이 **깨진 생몰로 사용자에게 노출**됐다. task#252가 `validate_event_chronology` 라이브 위반 5건을 교정하며 이 조항과 정면으로 충돌해, ADR-0014가 예고한 "재검토" 조건이 실제로 발동됐다.

## Decision

- **Person `birthYear`/`deathYear`도 교정 대상에 편입한다** — ADR-0014 Decision의 "재정렬하지 않는다" 제외를 UI 노출 사실에 맞춰 해제. 교정은 동일 메커니즘(`data/date_corrections/persons.json` 오버레이 + `inject_date_corrections.py`, 멱등·에코 검사, theographic_id 매칭)으로, ADR-0014 보수 연대계에서 방어 가능한 값 + rationale과 함께 저작한다.
- **범위는 검증기가 잡는 결함에 한정** — `validate_event_chronology`의 사망<출생·참여 역전 위반을 0으로 만드는 최소 교정. 전 인물의 Ussher→보수계 일괄 재정렬은 여전히 비범위(비용 큼, 별도 결정).
- **게이트로 재발 방지** — `validate_event_chronology`가 배포 전 `scripts/check.sh`(task#255 게이트)에 편입돼, 향후 Person/이벤트 연대 드리프트를 배포 시 차단한다.

## Consequences

- ADR-0014의 "Person 연대는 재정렬 안 함 / UI 미노출" 전제는 더 이상 유효하지 않다(이 조항은 본 ADR로 대체). 전 인물 일괄 재정렬을 안 해 남는 scale 불일치는 검증기가 잡는 결함이 아니므로 여전히 수용.
- Person 연대 교정도 로더 재적재(load_theographic 등) 후 `inject_date_corrections` 재실행이 필수 — ADR-0014의 재적재 드리프트 규약이 그대로 적용된다.
- **되돌리기**: 인물 소개 UI(PersonIntro/PersonMiniCard)에서 생몰 표시를 다시 감추면 이 개정의 근거가 사라진다 — 그 경우 재검토.
