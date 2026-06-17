# 2026-06-18 — 사도행전 이후(AD57+) 후기 10권을 책-기반 저작 사건으로 타임라인 연결 (task 46)

## Plan vs actual
- What went as planned: 5개 슬라이스 전부 완료기준 충족. S1 저작 사건 6개(`data/authored_events/events.json`, 환각 0) → S2 멱등 적재(`load_authored_events.py`, authored Event 6/OCCURS_AT 4/HAS_PARTICIPANT 5, 재실행 불변) → S3 `/events` `authored`·`yearLabel` 노출(비저작 450 회귀 없음) → S4 TimelineView 저작 사건 행 `추정` 배지+범위 라벨(색 `TYPE_COLOR.Event`) → S5 후기 10권 ⚡ 충전(포로후 4권 무손상). **ADR-0005 설계가 실행에서 그대로 검증됨**: `/node/{authored-id}` 6개 모두 200(404 없음 — SidePanel/지도/링 동작), Playwright ⚡칩 클릭→SidePanel 사건 로드. 적대적 코드 리뷰(3렌즈) critical/major 0건.
- Divergences (전부 경미·계획 범위 내):
  - **[중요·정정] Neo4j는 호스트에서 직접 쓰기 가능했다.** 직전 회고(approx-book-event-links)의 "NEO4J_PASSWORD 없어 스크립트 못 돌림"은 *셸 미노출*이지 *부재*가 아니었다 — `.env`의 `NEO4J_PASSWORD` + 호스트 neo4j 6.2.0으로 `bolt://127.0.0.1:7687`에 적재. **백엔드는 컨테이너에 마운트가 아니라 이미지 빌드**라 `docker compose exec api`로는 `scripts` 모듈 import 불가 → load 스크립트는 호스트에서 실행이 정답(ADR-0005가 명시한 "멱등 MERGE load 1개 + 1회 적재" 그대로).
  - 사건 6개로 분할(가이드 ~5-7개 내). Patmos place 노드 부재 → 요한 밧모섬 사건 occursAt 생략(계획의 "없으면 생략" 준수). Jude participants 빈 배열(인물 매칭 근거 약함 — 저작 사건은 인물 링크 없어도 유효).
  - Peter/John 동명이인 핀: `toLower CONTAINS` 검색으로 Simon Peter=`recX9MMADoVI2CSP1`, John the Apostle=`recvAB7vkczUEFH8Z` 식별(계획의 "동명이인 주의" 준수).
  - S3가 `authored`뿐 아니라 `yearLabel`도 노출 — S4(범위 라벨)의 완료기준 충족을 위한 슬라이스 간 계약 보강(비목표 침범 없음).

## Learnings
- Do differently next time:
  - **DB 적재가 걸린 작업은 인프라 사실(시크릿·접근 경로)을 fg-run 착수 전 *실측 프로브*로 확정할 것 — 회고 텍스트만 믿지 말 것.** 이번에 직전 회고의 "NEO4J_PASSWORD 없음"이 워크플로 설계를 "Neo4j 회피"로 오도할 뻔했고, 메인 세션의 사전 프로브(`.env` 소싱 후 throwaway 노드 write 테스트)가 이를 정정했다. 이는 ADR-0004 retro가 지적한 *"retro 로그 캡처가 다음 계획을 못 막았다"*의 재현 — **인프라 사실은 회고 글이 아니라 실측으로 확인**해야 전파 오류가 안 난다. (정정 사실은 메모리에도 기록.)
  - **저작 사건 인물/장소 참조는 동명이인 함정**: `name` 정확 일치로는 Peter/John 매칭 실패. `toLower(name) CONTAINS`로 후보를 본 뒤 사도 본인을 식별하고, 모호하면 생략(빈 participants 허용). 향후 그래프 노드 참조 데이터 저작 시 표준 절차.
  - **`MATCH (e) MATCH (p) MERGE rel` 패턴은 노드 미존재 시 관계를 조용히 누락**(오류 없음). 이번 데이터는 핀 ID가 전부 정확했으나, 향후 데이터 추가 시 스크립트 끝의 카운트 print(occurs/participant)를 기대값과 대조하는 것이 오타 안전망.
- (기록만) `events.json`의 `mappedBookIds`는 load 스크립트가 읽지 않는 문서/감사용 메타. 책↔사건 실제 출처는 `book_events/books.json`(역방향). 두 방향 0 mismatch, ADR-0004 부합(그래프 무오염).

## Doc updates
- CONTEXT.md promotion: **none** — "저작 사건(Authored Event)"·"추정연도(placementYear)" 용어는 fg-ask(2026-06-17) 단계에서 이미 작성됨. 실행 중 새 용어/의미 변화 없음.
- ADR added: **none** — ADR-0005(저작 사건=마킹된 Neo4j Event 노드)가 fg-ask에서 이미 작성됨. 실행은 그 결정을 검증했을 뿐 새 trade-off 결정 없음. Neo4j 호스트 쓰기 정정은 환경/운영 사실(되돌릴 결정 아님)이라 ADR 바 미달 → 이 회고 로그 + 메모리에 기록.
