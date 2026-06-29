# 큐레이션 주인공이지만 Theographic에 없는 인물은 마킹된 authored Person 노드로 — 인물 카드는 일급 엔티티라서

성경인물탐험(PersonHub)에 사사시대 인물(드보라·기드온·입다·삼손·룻)을 추가하려는데, 이들은 Theographic 그래프에 Person으로 **단 한 명도 없다**(286 Person 중 사무엘만 존재). 기존 큐레이션 16인은 전부 실제 Theographic `rec` id를 재사용했으나 사사들은 재사용할 노드 자체가 없다. 인물 카드 클릭은 `/node/{id}`(SidePanel)·`/person/{id}/journey`·`/node/{id}/places`(지도)·`/node/{id}/neighbors/grouped`(이웃)를 호출하는데, 이 라우트들은 순수 Cypher로 Person을 **일급 엔티티**로 소비한다 — 노드가 없으면 카드 클릭 시 `/node/{id}`가 404가 되어 SidePanel·지도·여정이 깨진다.

ADR-0005는 "노드가 없는 인물(네로·도미티아누스)은 생성하지 않고 정황 텍스트로만 둔다"고 정했다. 그러나 그 대상은 authored **사건의 주변 참여자**(프로즈에만 언급, 탐험 대상 아님)였다. 사사들은 정반대다 — **성경인물탐험 기능의 주인공**이라 카드·여정·SidePanel을 가진 탐험 가능한 일급 인물이어야 한다. 따라서 ADR-0005의 "Person 노드 미생성" 원칙에 **예외를 명시적으로 판다**: 큐레이션 주인공은 노드를 만들고, 주변 참여자는 여전히 만들지 않는다. authored 사건의 에스더식 처리(`participants:[]` 타임라인 전용)는 이 경계의 반대편 선례다 — 에스더는 카드가 없으므로 노드도 없다.

저작 사건(ADR-0005)과 동일하게, Neo4j에 실제 Person 노드로 넣되 `authored:true`로 마킹해 검증된 theographic 인물과 구분한다.

## Considered Options

- **(채택) 마킹된 Neo4j Person 노드** — `data/authored_persons/people.json` + `load_authored_persons.py`로 `MERGE (p:Person {theographic_id})` + `authored:true` + `name`/`nameKo`. 식별자는 `authored-person-<slug>`. 인물 여정 적재(`load_person_events.py`)의 `HAS_PARTICIPANT`가 MATCH할 노드가 생기므로 카드·여정·SidePanel·지도가 공짜로 동작. 비용: 멱등 load 스크립트 1개 + data 디렉터리 1개. **적재 순서 제약**: authored Person이 `load_person_events.py`보다 먼저 적재돼야 HAS_PARTICIPANT MATCH가 성립한다.
- **(반려) 에스더식 타임라인 전용(`participants:[]`)** — 노드 없이 authored 사건만 둠. 사사가 인물 카드로 탐험되지 못하고 타임라인 점으로만 남아 성경인물탐험 기능의 목적(인물 중심 여정 탐험)을 못 채운다.
- **(반려) 실존 Theographic 인물에 사사 여정을 끼워넣기** — 매칭할 인물이 없어 불가능. 무관한 인물에 붙이면 권위 호도.
- **(반려) 마킹 없이 Neo4j 적재** — theographic 검증 인물과 구분 불가 → 권위 호도(추정/저작인지 검증인지 API·사용자가 알 수 없음).

## Consequences

- ADR-0005를 **폐기가 아니라 보완**한다. 경계가 "Person 노드를 만드냐 마냐"의 일률 금지에서 → **"큐레이션 주인공(카드·여정 소비)은 만들고, authored 사건의 주변 참여자는 안 만든다"**로 정밀해진다. 네로·도미티아누스·에스더는 그대로 노드 없이 둔다.
- `persons.py`의 `_build_list`/`journey.py`의 `_build_id_to_slug`는 이미 `participants[0]`을 person_id로 쓰므로 authored-person id도 그대로 큐레이션 인물로 노출된다 — 라우트 코드 변경 불필요(데이터+로더+레지스트리 2줄만).
- 식별자 규약: authored Person은 `authored-person-<slug>` 안정 키를 `theographic_id` 속성에 부여(접두로 검증 데이터와 구분). authored 사건(`authored-<slug>`)·authored 장소(`authored-place-<name>`)와 같은 계열.
- `inject_ko_names.py`는 `names_ko/people.json`의 theographic id만 MATCH하므로 authored Person을 건드리지 않는다 — nameKo는 노드 생성 시점에 박는다.
- traits 없는 authored Person도 SidePanel·카드는 정상 동작한다(traits는 있을 때만 렌더). 사사 traits 부여는 별도 enrich 경로라 이번 범위 밖.
- 되돌리기 비용 **중간**: 카드·여정·지도가 authored Person을 소비하기 시작하면 "검증 ↔ 저작" 인물 분리가 비싸다(재적재·카드 제거) → 그래서 ADR로 남긴다.
