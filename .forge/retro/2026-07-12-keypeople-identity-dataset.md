# 2026-07-12 — keyPeople 정식 식별 데이터셋 + 결정적 카드 표시 (task#171)

## Plan vs actual
- What went as planned:
  - 하이브리드: S1 모호 판정 메인 세션(Opus) 직접, S2 카드 저작만 Dynamic Workflow(31장·0에러·리터럴 임베드), S3~S5 세션 직접. #170 워크플로우 패턴 재사용.
  - identity.json 330쌍 완결(person 138·noid 181·deity 11), books.json 정합 0. person_context 86인(위반 0)·keypeople_verses 140·Neo4j 주입. `/keypeople-cards` 엔드포인트. 프론트 카드맵 재배선.
  - Playwright 8케이스 전부 OK — 숨은 카드 노출(아론)·별칭 여정 회복(요한→사도 요한)·책별 동명이인 정확(마가 야고보≠야고보서 야고보)·기존(미리암·도마·큰물고기·모세) 불변.
- Divergences (상세 7건 run.md):
  1. **alias 매칭 오탐 사전 포착·수정** — names_ko alias로 후보를 넓혔더니 `전도서 전도자→빌립`(빌립 별칭="전도자")·`오바댜 에돔→에서`(에돔=에서 별칭) 2건 오resolution. alias 제외(exact nameKo + endsWith)로 정정. bundle의 "빌립←전도서" 이상값으로 조기 발견.
  2. S1 모호 판정을 워크플로우 대신 Opus 직접(30쌍·고난도, skip-if-small + 품질).
  3. 모호 4인(바로·알렉산더·가이오·유다)을 그래프 노드 무가치라 noid(by-name)로 라우팅.
  4. 카드맵이 여정 통합 → curatedNameToId(#165)·keyPeopleVerses(#170 프론트) 배선 orphan 제거. 회귀 0(큐레이션-무카드 0건).
  5. 성령·사탄도 person 카드(신격 여호와·하나님만 제외, 계획대로).

## Learnings
- Do differently next time:
  - **"판단 가능한 데이터를 먼저, 정식으로" > 런타임 워크어라운드.** 이번 최대 교훈(사용자 통찰). keyPeople 문자열의 모호성(동명이인·별칭 불일치)을 런타임 이름 해석+예외표로 우회하려다, **데이터에 (책,이름)→정체를 못 박는 정식 데이터셋**으로 뿌리를 고쳤다. 실측이 이를 강제함 — 자동 판별은 7/7 실패(같은 이름 3명·서신서 무단서), 즉 데이터에 없는 판단은 런타임에 만들 수 없다. 유사 "두 소스 합집합 + 이름 매칭" 문제는 먼저 "판별 데이터가 존재하나"를 실측하고, 없으면 만들어라.
  - **이름 해석에 alias는 오탐원. exact nameKo + 접미(endsWith)만 쓰라.** names_ko alias("전도자"=빌립, "에돔"=에서)는 일반 단어·개념과 충돌해 오resolution을 낳는다. 이번엔 alias가 정답 0·오답 2 — 정답 케이스(빌라도·마가·요한)는 전부 exact/endsWith였다. 대량 매칭 후 **결과를 이상값(NT 인물이 OT 책에)으로 스캔**하면 조기 포착된다.
  - **동명이인 모호 판정의 근거는 그래프의 사건·관계다.** 야고보 3인을 SIBLING_OF(사도요한/다대오/예수)·대표 사건(변화산·헤롯살해 / 예루살렘 공의회)으로 구별. 단 **책-참여(HAS_PARTICIPANT)로는 안 됨**(서신서 저자는 무참여) — 인물 자체의 사건·관계를 봐야 한다. 후보가 무가치(무사건·오지시)면 억지 연결 대신 by-name 카드로.
  - **소규모(수십)·고난도 판정은 워크플로우(sonnet 위임)보다 메인 세션(Opus) 직접이 낫다.** 대량 균질 저작은 워크플로우, 소수 정밀 판정은 직접 — 하이브리드 안에서 한 번 더 갈린다.
- Keep:
  - #170 교훈 재확인: 리터럴 임베드(args 금지)·저널 조기 점검·정본 사전 ref 검증·기계검증(정합0·validate0·ref100%)로 대량 저작 무결성 확보. 3연속 무결성 0.
  - 단일 결정 계층(identity)로 통합하니 이전 누적 배선(curatedNameToId·keyPeopleVerses)이 깨끗이 orphan화 → 제거로 부채 청산.

## Doc updates
- CONTEXT.md promotion: none (식별(identity)·정체(kind)는 데이터모델/구현 개념, 도메인 용어 아님 — #170과 동일 판단).
- ADR: **ADR-0018 Consequences 보강** — (a) noid는 "그래프 노드 없는 인물/개념"뿐 아니라 **"노드는 있으나 무가치(무사건·오지시)한 인물"도 흡수**(바로·유다 등 by-name), (b) 이름 해석은 exact nameKo+endsWith만(alias 오탐 교훈).
- 기타: run.md에 divergence 7건. 후속 이슈 후보 — books.json keyPeople 데이터 정합성(가이아 등 지시대상 없는 문자열)은 #170·#171 걸쳐 계속 미해결(평문 유지).
