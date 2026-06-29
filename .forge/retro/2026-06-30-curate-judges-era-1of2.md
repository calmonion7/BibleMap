# 2026-06-30 — 사사시대 인물탐험 (1/2): authored Person 인프라 + "사사" era + 기드온 파일럿

## Plan vs actual
- What went as planned:
  - S1~S6 전부 완료. authored Person 인프라(`data/authored_persons/people.json` + `load_authored_persons.py`, load_authored_events.py 미러) 신설 → "사사" era 그룹(persons.py·PersonHub.jsx) → 기드온 7사건을 카드→여정→지도→구절까지 입증.
  - 인프라·ADR-0008·"저작 인물" 용어는 **fg-ask 그릴링 단계에서 이미 확정·문서화**된 대로 그대로 안착. 실행 중 새로 깨진 용어·새 하드결정 없음.
  - 적재 순서(Person 먼저 → 장소 → 여정) 준수로 HAS_PARTICIPANT MATCH 성립, 좌표 누락 0, API·Playwright 전 경로 통과(콘솔 에러 0).
- Divergences (다음 루프가 읽을 연료):
  - **동명이지(同名異地) 충돌 — 가장 값진 학습**: 기존 `authored-place-succoth`는 출애굽의 이집트 숙곳(30.56/32.02)이라 기드온이 추격한 요단 동편 숙곳과 **다른 장소**. 이름만 보고 재사용했으면 좌표가 틀렸을 것 → `authored-place-succoth-jordan`(32.20/35.62) 신설. **part 2 입다의 "미스바"도 베냐민 미스바 vs 길르앗 미스바 충돌 가능** — 기존 authored-place 재사용 전 반드시 좌표가 의도한 위치인지 확인.
  - **브누엘 재사용은 정당**: 야곱의 브니엘 = 기드온의 브누엘(얍복 나루 동일 지점)이라 기존 `authored-place-peniel` 재사용. 동명'동'지는 재사용, 동명'이'지는 신설 — 판단 기준은 좌표.
  - **직접 실행(워크플로우 미사용)**: 기드온 1인 + 신규 로더의 직렬 파이프라인이라 peter·paul 선례대로 Dynamic Workflow 생략. 적중.
  - **sortKey BC 소수점**: 캠페인이 한 해(BC 1191경)에 몰려 -1191.6→-1191.1, 에봇 -1190.0으로 연내 순서 부여. peter 회고의 AD 소수점 선례의 BC판(오름차순=시간순). journey.py·events.py float 처리 호환.

## Learnings
- Do differently next time:
  - **authored-place 재사용 전 좌표 대조 필수** — 같은 영문 지명이라도 다른 시대·다른 지점일 수 있다(숙곳: 이집트 vs 요단). part 2 미스바·라마·기브아 등 다용도 지명에 특히 주의.
  - **part 2(드보라·입다·삼손·룻)는 직접 실행으로 충분하나 4인 병렬이라 워크플로우 fan-out도 후보** — 단 각 인물의 신규 장소 좌표 결정은 동명이지 확인이 필요해 완전 기계적이진 않다.
  - 신규 큐레이션 인물 추가 시 인프라·용어·ADR은 **그릴링 단계에서 확정**해두면 실행 회고가 절차 로그만 남는 깔끔한 흐름이 된다(이번처럼 CONTEXT/ADR 추가 승급 0).

## Doc updates
- CONTEXT.md promotion: none (저작 인물 용어는 fg-ask 단계에서 이미 추가)
- ADR added: none (ADR-0008이 fg-ask 단계에서 이미 도입; 위 분기는 절차 지식이라 회고 로그 보존)
