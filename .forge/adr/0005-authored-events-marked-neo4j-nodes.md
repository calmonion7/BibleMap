# 저작(authored) 사건은 오버레이가 아니라 마킹된 Neo4j Event 노드로 — 사건은 일급 엔티티라서

사도행전 이후(AD57+) 후기 서신·계시록 등 `startDate` 없는 책들이 타임라인에 매달릴 사건이 그래프에 없다. 이를 위해 그 책들이 쓰인 정황을 거꾸로 도출한 추정(저작) 사건을 만든다. ADR-0004는 "추정·낮은권위 데이터는 Neo4j 밖 런타임 오버레이"라 했으나, 그 원칙이 다룬 대상은 **연도(`book_years_approx`)와 책↔사건 링크(`book_events`)뿐이고 둘 다 `/books` 한 곳에서만 소비**된다. 사건 노드는 다르다 — `/events`·`/node/{id}`(SidePanel)·`/node/{id}/places`(지도)·`/node/{id}/neighbors/grouped`(사건 링) 네 라우트가 모두 순수 Cypher로 Event를 **일급 엔티티**로 소비한다. 사건을 오버레이로만 두면 그 사건의 ⚡ 칩 클릭 → `/node/{id}`가 404 → SidePanel·지도·링이 깨진다. 따라서 저작 사건은 Neo4j에 실제 Event 노드로 넣되 `authored:true`로 마킹해 검증된 theographic 사건과 구분하고, `/events`가 플래그를 노출하며 UI는 `추정` 배지로 표시한다. 저작 사건은 `CONTAINS_BOOK`을 갖지 않으므로(서신서는 사건을 "기록"하지 않음) ADR-0004가 막으려던 📖 근거 칩 오염은 발생하지 않는다.

## Considered Options

- **(채택) 마킹된 Neo4j Event 노드** — `MERGE (e:Event {theographic_id})` + `authored:true` + (대상 노드 존재 시) `OCCURS_AT`/`HAS_PARTICIPANT`. 4개 라우트가 공짜로 동작(클릭·지도·사건 링), `CONTAINS_BOOK` 미사용으로 근거 칩 무오염, 마킹으로 권위 구분. 비용: 멱등 MERGE load 스크립트 1개 + 영속 Neo4j에 1회 적재.
- **(반려) 오버레이 사건(`book_years_approx` 선례 확장)** — 권위 그래프는 무오염이지만, 사건이 일급 엔티티라 `/events` 외 3개 노드 라우트(SidePanel·지도·링)까지 전부 오버레이 머지해야 하고, 안 하면 ⚡ 클릭이 그 사건에서 깨진다. 표면적 과다.
- **(반려) 마킹 없이 Neo4j 적재** — theographic 검증 사건과 구분 불가 → 권위 호도(추정인지 검증인지 사용자·API가 알 수 없음).

## Consequences

- ADR-0004를 **폐기가 아니라 보완**한다. 분리 기준이 "오버레이냐 그래프냐"가 아니라 **"일급 엔티티(사건)는 그래프에 마킹해서, 책에 붙는 추정 메타(연도·링크)는 오버레이로"**. `book_years_approx`·`book_events`는 그대로 오버레이로 둔다(고아 아님).
- 저작 사건을 기존 Place/Person에 `OCCURS_AT`(로마·밧모·에베소)/`HAS_PARTICIPANT`(바울·베드로·요한)로 연결하면 지도·사건 링·인물 활동반경이 살아난다. **부작용**: 바울/요한 등 인물 뷰에 추정 사건이 이웃으로 섞인다(사건 노드는 `authored`로 식별되나 관계 자체엔 마킹이 없다). 노드가 없는 인물(네로·도미티아누스)은 생성하지 않고 정황 텍스트로만 둔다.
- 저작 사건은 theographic `verses`가 없어 `/event/{id}/verses`가 빈 배열 → 📖 근거 구절 드릴다운이 없다(의도된 것 — ⚡ 정황 앵커이지 📖 근거 사건이 아님).
- 식별자 규약: 저작 사건은 theographic `rec` ID가 없으므로 `authored-<slug>` 형식 안정 키를 `theographic_id` 속성에 부여한다(접두로 검증 데이터와 구분).
- 연도는 정렬용 단일 `sortKey`(점 배치, 필수) + 표시용 범위 라벨(`yearLabel`, 못 박을 때 "AD 85–95" 등)로 둔다. 타임라인을 구간 막대(span)로 바꾸지 않는다.
- 되돌리기 비용 **중간**: `/events`·SidePanel·지도가 저작 사건을 소비하기 시작하면 "검증 ↔ 저작" 분리가 비싸다(재적재·마커 제거) → 그래서 ADR로 남긴다.
