# 노드 없는 keyPeople 인물의 근거 구절 = 이름 키 저작 맵(그래프 노드 미생성)

책 상세 「주요 인물」은 두 소스의 합집합이다 — 이벤트 참여 그래프 Person 노드(`topPersons`, id 보유)와 책에 저작된 `keyPeople` 문자열(id 없음). task#169가 여정도 구절도 없는 **그래프 노드** 인물에 person_context(theographic_id 키) 근거구절을 저작해 `📖 구절` 칩을 부여했으나, `keyPeople` 문자열 중 **어떤 그래프 노드에도 매칭되지 않는 인물**(미리암·나오미·보아스·갈렙·라합 등)은 붙일 노드도 사건 참여도 없어 평문으로 남았다(task#169 Non-goal). task#170에서 이들에게 구절을 연결하며, **그래프 노드를 만들지 않고 이름 키 저작 맵**을 신설하는 방식을 택했다.

- 데이터: `data/keypeople_verses/people.json` — keyPeople 문자열(예: `"미리암"`)을 키로 `{role, intro, verses:[{ref,textKo,textEn}]}`. AUTHORING.md 규칙(근거구절 원칙·톤·분량·ref만 저작) 준용, 본문은 정본 절 사전(`data/bible/verses.json`)에서 채움.
- 소비: 신규 `/keypeople-verses` 엔드포인트가 맵 전체를 반환 → 프론트가 `curatedNameToId`와 동일 경로(useStageNavigation→App→SidePanel)로 로드 → keyPeople 행을 이름으로 조회해 task#169의 구절 칩·모달 재사용.
- 선별: 노드 없는 keyPeople **전체**(개인 + 집단/민족 + 개념/추상 + 호칭 + 비인격)에 관련 구절 저작. **신격(`여호와`·`하나님`)만 제외**(그래프도 `God` 제외, 하나의 대표 구절로 축약 민감) → 맵에 없어 평문 유지. 개인은 인물 근거구절, 비개인은 그 대상의 관련 구절 성격(`role`/`intro`가 대상을 설명 — 예: `이스라엘 백성`→role "언약 백성", `지혜`→role "의인화된 지혜"). 근거구절 원칙은 동일 적용(모든 서술은 verses로 뒷받침).

## Considered Options

- **(채택) 이름 키 저작 맵 + 노드 미생성** — 순수 추가(데이터 파일 + 엔드포인트 + 프론트 조회 한 줄), 그래프 무변경. 되돌리기 쉬움(파일 삭제). 대가: person-verses 저작 체계가 둘(by-id `person_context` + by-name `keypeople_verses`)로 갈림 — 그래서 이 ADR로 이유를 남긴다. 이름 충돌은 keyPeople 문자열이 충분히 구체적(예: "막달라 마리아")이라 실무상 무해.
- **(반려) authored Person 노드 생성 + person_context 통합** — 저작 체계는 하나로 통일되나, **사건 없는 고립 노드 ~60개가 그래프뷰·검색에 등장**(외로운 점, UX 저하)하고 keyPeople 이름→id 해석을 큐레이션 밖으로 확장해야 함. ADR-0008(큐레이션 인물용 authored 노드)은 여정·사건이 있는 인물 전제라 이 무-사건 인물군엔 부적합.
- **(반려) keyPeople를 Book 노드에서 구조 변경(문자열→객체)** — Book 노드에 인물 구절을 인라인하면 관심사 혼입·기존 소비 계약 파손.

## Consequences

- person 구절의 소스가 둘로 나뉜다: **그래프 노드 인물 = `person_context`(by-id, inject로 Neo4j 속성)**, **노드 없는 keyPeople 인물 = `keypeople_verses`(by-name, 파일→엔드포인트, Neo4j 미경유)**. 인물 구절을 만질 땐 대상이 어느 쪽인지 먼저 판별.
- 프론트 keyPeople 분기의 칩 우선순위는 task#169와 동일: journeyId(여정) > verses(구절) > 평문. 맵에 없는 문자열(신격, 그리고 관련 구절을 특정하기 어려운 극소수)만 평문으로 남는다. 「주요 인물」 섹션에 집단/개념(예: `이스라엘 백성`·`지혜`)이 구절 칩과 함께 노출되는데, 이는 keyPeople 원저작이 이미 그렇게 담고 있던 것이라(평문으로 노출 중이던 것에 칩만 추가) 라벨-내용 불일치는 기존 상태를 잇는 것이지 이 작업이 새로 만든 것이 아니다.
- 별칭 불일치(예: keyPeople `"빌라도"` ↔ 노드 `본디오 빌라도`)는 별칭 해석을 만들지 않고 그 문자열로 새로 저작(경미한 중복 감수). 향후 alias 통합이 필요하면 별도 결정.
- 본문은 정본 사전에서 채우므로(ADR-0015) 네트워크 불필요·전사 오류 0.
- **(보강 2026-07-12, task#170) by-id/by-name 분리의 사각지대 — has-node이지만 비-top10 keyPeople 문자열 인물.** 책 상세 「주요 인물」의 렌더 경로는 둘이다: (a) top-10 topPerson = eventPersons 경로가 person_context(by-id) verses를 실어 나름, (b) 그 외 keyPeople 문자열 = by-name 경로가 `curatedNameToId`(여정)·`keypeople_verses`(by-name)만 조회. 따라서 **그래프 노드가 있는 인물이라도 특정 책에서 top-10이 아니고 그 책 keyPeople 문자열로 노출되면 (b)로 렌더돼 by-id person_context에 닿지 못한다** → person_context에 verses를 주입해도 칩이 안 뜨고 평문으로 남는다. task#170의 **도마**가 이 사례(어떤 책에서도 top-10 아님, 마태 rank≈13). 해소책으로 도마는 person_context(by-id, 향후 top-10 승격/Person 직접 조회 대비)와 keypeople_verses(by-name, 요한복음 keyPeople 렌더 노출)에 **양쪽 등재**했다(경미한 중복 감수 — 별칭 중복과 같은 성격). 일반 해법(by-name 렌더가 person_context by-name까지 조회)은 별도 결정으로 남긴다.
