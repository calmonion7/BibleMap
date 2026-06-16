# BibleMap — 도메인 용어집

## Theographic ID

Theographic Bible Metadata 레포에서 사용하는 Airtable 레코드 ID. `rec` 접두사로 시작하는 14자 문자열 (예: `recv0dAY2ULzJ687g`). 모든 엔티티(Person, Place, Event, PeopleGroup)의 안정 키. 영문명은 동명이인이 존재하므로 조인·참조 기준으로 사용하지 않는다. Neo4j 노드의 `theographic_id` 속성으로 저장된다.

## publish 레코드

Theographic 데이터에서 `fields.status == "publish"`인 레코드. 데이터가 검수 완료된 상태. `status == "wip"` 레코드는 미완성이므로 BibleMap 적재에서 제외한다.

**엔티티별 status 필드 유무**: Person·Place는 `status` 필드가 있다. Event·PeopleGroup은 `status` 필드가 없으므로 "전체 포함"으로 처리한다(`fields.get("status", "publish") == "publish"` 패턴). Verse·Book·Chapter 등 추가 엔티티를 적재할 때는 `status` 필드 유무를 먼저 확인해야 한다.

## Period

별도의 엔티티 타입 없음. 성경의 시대(족장 시대, 왕국 시대 등)는 `Event` 노드의 `PART_OF` 관계로 표현한다. 상위 Event가 하위 Event들을 포함하는 계층 구조.

## Book

성경 각권을 나타내는 Neo4j 노드 (label: `Book`). Theographic `books.json`에서 적재. 주요 속성: `theographic_id, name, nameKo, testament(구약/신약), genre, authorKo, startYear, endYear, chapterCount`. 추가 속성(LLM 생성 후 주입): `background`(시대적 배경 텍스트), `themes`(성경 주제 배열), `keyVerse`(대표 구절 참조). Book → Event 관계는 `CONTAINS_BOOK`.

**CONTAINS_BOOK 관계 생성 방법**: `Book.verses ∩ Event.verses` 교집합. Theographic events에 scripture 직접 참조 필드가 없으므로, Book이 포함하는 구절 배열과 Event의 구절 배열의 교집합이 비어있지 않으면 `CONTAINS_BOOK` 관계를 생성한다 (`load_books.py`). 파이프라인 재실행·관계 수정 시 이 방식을 유지해야 한다.

**의미**: `(Book)-[:CONTAINS_BOOK]->(Event)`는 "그 책이 그 사건을 기록한다" = **사건의 성경적 근거**를 뜻한다. 한 사건을 여러 권이 기록할 수 있다(예: 공관복음 평행 기사 → 마/막/눅). 사건의 날짜가 없는 책(서신서·시편·잠언 등)은 이 관계가 없어 사건 근거 칩으로는 등장하지 않고, 대신 추정연도 단독 마커로 배치된다(아래 "사건의 근거" 참조).

## Character Trait (인물 성품)

Person 노드에 주입되는 속성 `traits` (JSON 문자열 배열). 각 항목: `{trait: "겸손", verse_ref: "민 12:3", description: "..."}`. LLM(Claude API)으로 생성 후 수동 검수, `data/character_traits/people.json` → `inject_person_traits.py`로 Neo4j 주입.

## Book Context (권별 컨텍스트)

각 Book의 시대적 배경·주제·대표구절을 담는 정적 JSON (`data/book_context/books.json`). LLM(Claude API)으로 생성 후 수동 검수. `inject_book_context.py`로 Book 노드 속성에 주입. Verse 텍스트 자체는 외부 API(getbible.net 등)에서 실시간 fetch.

## selectedNode

프론트엔드 전역 상태. 현재 사용자가 선택한 엔티티의 `theographic_id`와 레이블(Person/Place/Event/Book)을 담는다. MapView / TimelineView 두 뷰가 이 값을 구독해 동시에 갱신된다. (GraphView는 제거됨.)

## 사건의 근거 (Scriptural Evidence)

특정 Event를 기록한 성경 본문. TimelineView의 데이터 흐름은 **연도 → 사건 → 성경권 → 성경구절**이며, 마지막 두 단계가 그 사건의 근거다. 권 단계는 `CONTAINS_BOOK`(사건 ↔ 권, 한 사건에 여러 권 가능), 구절 단계는 원천 theographic `verses`에서 사건·권별로 해석한 절들(인용 범위 + 본문)이다. 타임라인은 사건을 척추로 두고 그 사건의 근거 권을 칩으로 붙여 보여준다. 단, 사건이 없는 책(`startYear` 없음 = `CONTAINS_BOOK` 미연결, 서신서·시편·잠언 등 31권)은 근거 칩이 아니라 추정연도(`book_years_approx`) 단독 마커로 표시되며, 사건이 없으므로 구절 근거 단계는 갖지 않고 클릭 시 권 개요만 보여준다.

## 탐색 관점 (Navigation Perspective)

BibleMap 데이터를 바라보는 세 가지 중심 관점. 관점에 따라 같은 데이터가 다르게 시각화된다.

**인물 중심 (Person-centric)**: 특정 Person이 참여한 Event와 그 Event가 발생한 Place들로 해당 인물의 활동 반경을 구성한다. Person에 좌표가 없는 이유도 여기서 비롯된다 — Person은 `HAS_PARTICIPANT → Event → OCCURS_AT → Place` 경로를 통해 간접적으로 공간을 갖는다.

**장소 중심 (Place-centric)**: 특정 Place에서 발생한 Event와 그 Event에 참여한 Person들을 조회한다. 지도 마커 클릭이 이 관점의 진입점이다.

**시대 중심 (Era/Timeline-centric)**: 특정 시기의 Event 흐름과 그에 연결된 Person·Place를 탐색한다. `Period`(= Event의 `PART_OF` 계층)가 이 관점의 정렬 축이 된다. TimelineView는 사건을 시대순으로 늘어놓고, 각 사건의 "사건의 근거"(성경권 → 구절)를 함께 보여준다.
