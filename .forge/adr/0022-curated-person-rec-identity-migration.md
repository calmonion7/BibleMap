# 큐레이션 인물 신원 = 검증된 theographic 실레코드로 이관 (저작 노드는 "원본에 없을 때만"으로 축소, ADR-0008 부분 개정)

ADR-0021의 가족 폐포 wip 적재 후, 큐레이션 저작 인물([[저작-인물-authored-person]], `authored-person-*` 13명)의 가계도가 **빈 트리**로 드러났다. 원인은 이중 신원: 큐레이션 당시 theographic에 없어(당시 wip) 저작 노드를 만들었는데, 같은 인물의 실레코드가 이제 그래프에 들어오면서(사울·룻) 혈통이 실레코드에만 붙는다. 나머지(기드온·삼손 등)는 실레코드가 **폐포 밖 가족 섬**(publish 성분과 미연결)에 있어 아직 미적재다.

전수 판정: 13명 중 **11명**(사울·룻·기드온·삼손·입다·드보라·엘리사·요나·에스더·느헤미야·욥)은 가족 링크가 성경 사실과 일치하는 실레코드가 특정된다(사울=기스 부·요나단 등 8자녀, 욥=딸 여미마·긋시아·게렌합북 등). **2명은 제외**: 다니엘(동명 rec은 다윗의 아들; 선지자 rec들은 가족 無 — 성경에도 족보 없음), 엘리야(동명 2건 모두 가족 無). 빈 트리가 성경적으로 정확한 경우다.

## Considered Options

- **(채택) 전면 id 이관 + 폐포 시드 확장.** 11명의 정식 신원을 실레코드 id로 교체한다 — `authored-person-*` 참조는 데이터 4곳뿐(authored_persons/people.json·person_events/*.json·character_traits·person_context; 백엔드는 slug 기반, 프론트 0건)이라 기계적 스왑이 가능하다. 로더의 가족 폐포 시드를 `publish ∪ 큐레이션 rec`(person_events 파일들에서 수집)으로 확장해 폐포 밖 가족 섬(기드온 섬 5명 등 약 25명)을 적재하되, **큐레이션 rec 자신은 wip 마킹에서 제외**한다(사람이 검수한 신원이므로 publish급 — 검색 노출 유지, 아니면 사울·룻이 검색에서 사라지는 회귀). 옛 저작 노드는 DETACH DELETE. 마태1 사슬 이관(ADR-0021)과 동일 패턴의 큐레이션판.
- **(반려) API 별칭/브리지(가계도 조회 시 authored→rec 해석).** 참조 무변경이라 싸지만 이중 신원이 영구화된다 — 그래프에 같은 인물 노드 2개(요나단의 아버지 rec 사울 vs 큐레이션 authored 사울)가 남아 SidePanel 이웃·검색·향후 모든 기능에서 분기 처리가 필요해진다. ADR-0018의 정식 식별 규율 위배.
- **(반려) rec 간선을 authored 노드로 복사(머지).** 저작 노드가 theographic 데이터를 흡수해 provenance 마킹(ADR-0008 authored=true)이 거짓이 되고, 전체 재적재 때마다 rec으로 간선이 재생성돼 드리프트한다.

## Consequences

- **저작 인물의 존재 조건이 좁아진다**: "theographic에 검증 가능한 대응 실레코드가 없을 때만" 저작 노드를 만든다/유지한다(다니엘·엘리야 2건 잔존). 신원 검증은 이름이 아니라 **가족 링크의 성경 사실 일치**로 한다(ADR-0018 계승).
- **재적재 계약 갱신**: 폐포 시드 = publish ∪ 큐레이션 rec(person_events에서 수집, 로더 코드에 내장). 큐레이션 rec은 status 무마킹, 그 가족 섬은 wip 마킹. load_theographic → load_authored_persons(11명 제거) → load_person_events → inject 순서 유지.
- 여정·카드·성품·관계는 slug/nameKo 축이라 API 무변경이나, HAS_PARTICIPANT 등 간선이 rec id로 옮겨가므로 **여정 회귀 검증 필수**.
- 새 섬 인물(~25명) 한글 이름을 names_ko에 추가한다(ADR-0006).
