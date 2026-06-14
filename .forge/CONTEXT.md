# BibleMap — 도메인 용어집

## Theographic ID

Theographic Bible Metadata 레포에서 사용하는 Airtable 레코드 ID. `rec` 접두사로 시작하는 14자 문자열 (예: `recv0dAY2ULzJ687g`). 모든 엔티티(Person, Place, Event, PeopleGroup)의 안정 키. 영문명은 동명이인이 존재하므로 조인·참조 기준으로 사용하지 않는다. Neo4j 노드의 `theographic_id` 속성으로 저장된다.

## publish 레코드

Theographic 데이터에서 `fields.status == "publish"`인 레코드. 데이터가 검수 완료된 상태. `status == "wip"` 레코드는 미완성이므로 BibleMap 적재에서 제외한다.

**엔티티별 status 필드 유무**: Person·Place는 `status` 필드가 있다. Event·PeopleGroup은 `status` 필드가 없으므로 "전체 포함"으로 처리한다(`fields.get("status", "publish") == "publish"` 패턴). Verse·Book·Chapter 등 추가 엔티티를 적재할 때는 `status` 필드 유무를 먼저 확인해야 한다.

## Period

별도의 엔티티 타입 없음. 성경의 시대(족장 시대, 왕국 시대 등)는 `Event` 노드의 `PART_OF` 관계로 표현한다. 상위 Event가 하위 Event들을 포함하는 계층 구조.

## selectedNode

프론트엔드 전역 상태. 현재 사용자가 선택한 엔티티의 `theographic_id`와 레이블(Person/Place/Event)을 담는다. MapView / TimelineView / GraphView 세 뷰가 이 값을 구독해 동시에 갱신된다.

## 탐색 관점 (Navigation Perspective)

BibleMap 데이터를 바라보는 세 가지 중심 관점. 관점에 따라 같은 데이터가 다르게 시각화된다.

**인물 중심 (Person-centric)**: 특정 Person이 참여한 Event와 그 Event가 발생한 Place들로 해당 인물의 활동 반경을 구성한다. Person에 좌표가 없는 이유도 여기서 비롯된다 — Person은 `HAS_PARTICIPANT → Event → OCCURS_AT → Place` 경로를 통해 간접적으로 공간을 갖는다.

**장소 중심 (Place-centric)**: 특정 Place에서 발생한 Event와 그 Event에 참여한 Person들을 조회한다. 지도 마커 클릭이 이 관점의 진입점이다.

**시대 중심 (Era/Timeline-centric)**: 특정 시기의 Event 흐름과 그에 연결된 Person·Place를 탐색한다. `Period`(= Event의 `PART_OF` 계층)가 이 관점의 정렬 축이 된다.
