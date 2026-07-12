# 2026-07-12 — 노드 없는 keyPeople 135개 근거구절 저작·연결 + 도마 보완 (task#170)

## Plan vs actual
- What went as planned:
  - 하이브리드 실행(계획 Notes·#169 교훈): S2 저작만 Dynamic Workflow(15배치·9개씩·sonnet 병렬·eco), S1·S3~S6 세션 직접. 워크플로우 134 저작·1 스킵·0에러.
  - S3 정본 사전 대조로 **전 ref 400+개 100% 해석·REF_RE 통과·드롭 0·재저작 0** — #169의 "엄격 개역약어 화이트리스트 + 참여 책 문맥 → ref 품질" 3연속 재확인(link-verses-to-verseless-events→#169→#170).
  - 프론트 #169 칩·모달을 by-name 배선(useStageNav→App→SidePanel line 176)으로 그대로 재사용 — journeyId>verses>평문 우선순위가 이미 있어 무변경 점등. eslint 0·build green.
  - S1 도마 person_context 61인·validate 위반 0·Neo4j 주입. UAT: Playwright 모바일에서 미리암(출)·도마(요) 구절칩+모달, 모세 여정칩 불변.

- Divergences (상세 8건은 run.md):
  1. **S2 Workflow `args` 문자열-전달 footgun** — 배열을 args로 넘겼으나 문자열로 도착 → `chunk(str,9)`가 JSON을 9자씩 절단(갈대/아(바벨론) 군대…), 일부 에이전트는 환각. 저널 조기 점검으로 10여 배치 시점 중단·리터럴 임베드로 재실행(정상).
  2. **도마 "top-10 노출" 전제 오류** — 실제로 어떤 책에서도 top-10 아님(마태 rank≈13). person_context(by-id)만으론 요한복음 by-name 렌더 경로에서 칩 미노출 → 도마를 keypeople_verses by-name 맵에도 추가(fix-forward). person_context도 유지.
  3. **비개인 칩: 계획 DoD #4「평문 유지」↔ ADR-0017「칩 노출」모순** — ADR·계획 Note "dead 데이터 없음"·DoD #2를 따라 개인+비개인 전부 칩 노출로 구현. 사용자가 "봉인"으로 현 구현 수용.
  4. S1 본문을 getbible bake 대신 정본 사전 직접 채움(#169 교훈·S3 일관·네트워크 불요). 결과 동일.
  5. 스킵 1건(가이아) — 요한2서에 대응 인물 없음, 서브에이전트 정당 보류.
  6. 미커밋 #169 WIP(people.json·프론트·nodes.py) + 발자취→여정 리네임 WIP 위에 스택(계획 Non-goal 수용).
  7. 저작 서브에이전트에 ECO.md 코드-간결 프리펜드 생략(모델 캡 sonnet만) — 산문 저작엔 부적합, AUTHORING.md ≤300자·담백이 이미 eco 취지.

## Learnings
- Do differently next time:
  - **Dynamic Workflow에 대량 데이터는 `args`로 넘기지 말 것.** args가 문자열로 도착하면 스크립트에서 배열 연산(chunk/map/filter)이 조용히 문자를 순회해 전량 손상된다. **스크립트 본문에 리터럴 const로 임베드**하거나(≤수 KB면 최적) 첫 에이전트가 파일을 읽어 반환하게 하고, `Array.isArray` 가드를 첫 줄에 둔다. 그리고 **긴 워크플로우는 저널(journal.jsonl의 result 이벤트)을 조기 점검**해 손상/환각을 초반에 잡으면 낭비를 막는다(이번엔 조기 발견으로 대부분의 토큰을 아꼈다).
  - **"인물 구절"을 만질 땐 그 인물이 어느 렌더 경로로 노출되는지부터 확인하라.** 책 상세 「주요 인물」은 두 경로다 — (a) top-10 topPerson = eventPersons 경로가 person_context(by-id) verses를 실어 나름, (b) 그 외 keyPeople 문자열 = by-name 경로가 curatedNameToId(여정)·keypeople_verses(by-name)만 조회. **has-node 인물이라도 특정 책에서 top-10이 아니고 keyPeople 문자열로 노출되면 (b)로 렌더돼 person_context에 못 닿는다**(도마 사례). "그래프 노드에 verses 주입"이 곧 "칩 노출"은 아니다 — top-10 여부가 관문. (fg-ask에서 이 렌더 경로 판별을 미리 했으면 도마 전제 오류를 계획 단계에서 잡았을 것.)
  - **계획 DoD와 근거 ADR이 상충하면 ADR(핵심 결정) + 계획 Note의 원칙("dead 데이터 없음")을 우선.** DoD 문구가 저작 범위(비개인 포함)와 표시 정책(비개인 평문)에서 자기모순이었다 — 저작하고 안 보이면 dead. fg-ask 그릴링에서 DoD-ADR 정합성 체크가 이 모순을 사전에 걸러낼 항목.
- Keep:
  - 하이브리드(저작만 워크플로우·나머지 세션 직접) + 정본 사전 ref 검증 감싸기 + by-name 프론트 재사용 = 3연속 저비용·무결성 0 패턴. 대량 저작은 이 틀로.

## Doc updates
- CONTEXT.md promotion: none (렌더 경로 이원성·bake 경로는 데이터모델/구현 개념, 도메인 용어 아님 — #169과 동일 판단).
- ADR: **ADR-0017 Consequences 보강**(신규 ADR 아님) — by-id/by-name 분리의 사각지대(has-node·비-top10·keyPeople 문자열 인물은 by-name 경로로만 렌더 → person_context 미도달)와 도마 예외(양쪽 등재) 기록. 결정의 소재가 ADR-0017 모델 자체라 그 Consequences에 귀속.
- 기타: run.md에 divergence 8건 상세. 후속 이슈 후보 — ① 비개인 칩 노출 최종 정책 확정(현재 노출), ② keyPeople-string 렌더가 person_context by-name까지 일반 조회하도록 확장(도마류 일반화), ③ books.json keyPeople 데이터 정합성(가이아 등 대응 인물 없는 문자열·names_ko 미등재 다수).
