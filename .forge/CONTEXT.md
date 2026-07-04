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

**의미**: `(Book)-[:CONTAINS_BOOK]->(Event)`는 "그 책이 그 사건을 기록한다" = **사건의 성경적 근거**를 뜻한다. 한 사건을 여러 권이 기록할 수 있다(예: 공관복음 평행 기사 → 마/막/눅). 사건의 날짜가 없는 책(서신서·시편·잠언 등 31권)은 이 관계가 없어 사건 근거 칩으로는 등장하지 않고, 대신 추정연도 단독 마커로 배치된다(아래 "사건의 근거" 참조). 이 31권은 별도의 **book_events 오버레이**(아래 항목)로 "집필 배경·저자·직접 다루는" 사건과 약하게 연결되어 마커 행에 사건 칩이 표시되지만, 이는 `CONTAINS_BOOK`(권위 그래프·구절 교집합)과 별개의 추정 연결이다.

## Character Trait (인물 성품)

Person 노드에 주입되는 속성 `traits` (JSON 문자열 배열). 각 항목: `{trait: "겸손", verse_ref: "민 12:3", description: "..."}`. LLM(Claude API)으로 생성 후 수동 검수, `data/character_traits/people.json` → `inject_person_traits.py`로 Neo4j 주입.

## Book Context (권별 컨텍스트)

각 Book의 시대적 배경·주제·대표구절을 담는 정적 JSON (`data/book_context/books.json`). LLM(Claude API)으로 생성 후 수동 검수. `inject_book_context.py`로 Book 노드 속성에 주입. Verse 텍스트(대표구절·사건 근거·인물 성품 인용절)는 **빌드타임에 getbible에서 한국어(`korean`)+영어(`kjv`)로 미리 받아 데이터에 함께 저장**한다(`generate_verse_text.py`, ADR-0003) — 런타임 외부 fetch 없음. Book의 대표구절 본문은 `keyVerseTextKo`/`keyVerseTextEn` 속성으로 주입된다.

## Place Context (장소 컨텍스트)

좌표가 있어 지도에 뜨는 장소(43개)의 **성경적 배경 산문(`background`)·대표구절(`keyVerse`)**을 담는 정적 JSON (`data/place_context/places.json`, dict 키=장소 id). **Book Context의 장소판** — 구조·파이프라인이 동일하다: LLM 직접 생성(ADR-0006, `place_coords`의 `note`를 시드로) → 대표구절 본문 빌드타임 프리베이크(`generate_verse_text.py`의 `bake_place_context`, `keyVerseTextKo`/`keyVerseTextEn`) → `inject_place_context.py`로 Place 노드에 4개 필드(`background`/`keyVerse`/`keyVerseTextKo`/`keyVerseTextEn`)만 SET. **실제 노드의 서술 보강이라 오버레이가 아니라 주입**한다(추정 독립 데이터만 오버레이하는 ADR-0004 원칙 — book_context와 동일 선례). SidePanel은 `node.label === 'Place'` 블록에서 "장소 배경"·"대표 구절"(한/영 탭) 섹션으로 렌더한다. 기존 `note` 필드는 시드로만 쓰고 보존(미렌더).

## 추정연도 (placementYear)

사건-구절 교집합(`CONTAINS_BOOK`)이 없어 `startYear`를 못 얻는 31권에 부여하는 타임라인 배치 연도 (`data/book_years_approx/books.json`의 `placementYear`, `yearApprox=true`로 표시). **기준은 "작성(저작) 시점"이 아니라 "그 책이 속하는 사건/내용 시대"** — 정확연도 책의 `startYear`(그 책이 기록한 사건들의 `startDate` 최소~최대를 `load_books.py`가 집계)와 **같은 의미축**이다. 즉 추정/정확은 *의미*가 다른 게 아니라 *도출 방법*만 다르다 (정확 = 사건 집계 자동, 추정 = 사건이 없어 수동 추정). 구약 내러티브·시가서는 배경 시대로 배치하고(작성 시점은 `basis`에 곁들이되 배치엔 안 씀), 신약 서신서·계시록은 "쓰여 보내진 순간이 곧 그 책의 시대"라 결과적으로 작성 시점과 일치한다. 사건 연결(아래 Book Events ⚡)과는 **독립축** — 연결이 있어도 연도는 여전히 추정이다.

## 사건 연대 (startDate)

Event 노드의 발생 시점 속성. **혼재 형식의 문자열**이다 — 연도만("-4003", "30"), 연-월("-1451-01"), 연-월-일 3파트가 공존하고 BC는 음수 접두. 따라서 **문자열 사전순 정렬은 BC 연도를 역전**시킨다("-1451" < "-4003"). 정렬·비교·필터에 쓸 때는 반드시 연도를 파싱해 수치로 다룬다(부호 분리 후 첫 파트를 정수화 — 프론트 `dates.js`의 `parseYear`, 백엔드 nodes.py `_year`가 같은 규칙). 책의 `startYear`는 이 값을 집계해 파생된다(추정연도 항목 참조).

## Book Events (책-사건 연결 오버레이)

추정연도 책(31권 — `startYear` 없어 `CONTAINS_BOOK`이 없는 서신서·시편·잠언 등)을 타임라인 사건에 약하게 연결하는 정적 JSON (`data/book_events/books.json`, 형식 `{ "<bookId>": ["<eventId>", ...] }`). 연결 기준은 **집필 배경**(서신서→사도행전 사건)·**저자**(시편→다윗 통치)·**직접 다루는 사건**(역대하→솔로몬·유다 왕). LLM(Claude API)으로 생성하는 추정 데이터(`generate_book_events.py`)라 **Neo4j에 주입하지 않고** `/books` 엔드포인트가 런타임에 오버레이해 각 책에 `events` 배열로 실어 보낸다(`book_years_approx`와 동일한 분리 원칙 — 추정·권위 낮은 데이터는 권위 그래프 밖 오버레이로 유지, inject·재빌드 불필요). TimelineView의 책 마커 행은 이 `events`를 ⚡ Event색 칩으로 표시하고(클릭 시 그 사건 선택), 데이터가 없는 사건(예: AD57 이후 후기 서신·계시록, 포로귀환)은 빈 배열이라 칩이 없다. **CONTAINS_BOOK의 "사건의 근거"(구절 교집합) 의미와 무관 — 사건 행의 📖 근거 칩은 영향받지 않는다.**

## 저작 사건 (Authored Event)

`startDate`를 가진 theographic 사건이 AD57(바울 1차 로마 투옥)에서 끊겨, 그 이후 쓰인 후기 서신·계시록(추정연도 31권 중 10권: 디모데전후·디도·벧전후·유다·요한1~3·계시록)이 매달릴 타임라인 사건이 그래프에 없다. 이를 메우려고 **그 책들이 쓰인 정황을 거꾸로 도출해 만든 추정 사건**이 저작 사건이다 — 성경 본문 밖 자유 역사 사건(예 예루살렘 함락 AD70)이 아니라 **고아 책 기반**(예: 계시록→요한의 밧모섬 유배(계 1:9), 디모데후서→바울 로마 2차 투옥·순교, 베드로전후→베드로 로마 사역·순교, 요한1~3→요한 에베소 만년 사역). theographic 검증 사건과 달리 LLM/수동 저작이라 권위가 낮다.

**오버레이가 아니라 Neo4j `Event` 노드로 적재하되 `authored:true`로 마킹한다 (ADR-0005)** — 사건은 `/events`·`/node/{id}`·`/node/{id}/places`·사건 링이 소비하는 **일급 엔티티**라, 오버레이로만 두면 ⚡ 칩 클릭 시 `/node/{id}`가 404가 되어 SidePanel·지도·링이 깨지기 때문(이 점이 *연도·링크* 오버레이를 다룬 ADR-0004와 갈리는 지점). `/events`가 `authored` 플래그를 노출하고 TimelineView가 `추정` 배지 + 범위 라벨로 표시한다. theographic ID(`rec` 접두)가 없어 `authored-<slug>` 식별자를 `theographic_id`에 부여한다. **`CONTAINS_BOOK`(📖 근거)을 갖지 않으므로** 사건 근거 칩을 오염시키지 않고, 후기 10권과는 **book_events 오버레이(⚡)** 로 연결된다(`CONTAINS_BOOK`이 아니라). 기존 Place(로마·밧모·에베소)·Person(바울·베드로·요한)에 `OCCURS_AT`/`HAS_PARTICIPANT`로 연결해 지도·링을 살린다. 연도는 정렬용 단일 `sortKey` + 표시용 범위 라벨(`yearLabel`)로 둔다.

## 저작 인물 (Authored Person)

성경인물탐험에 큐레이션하려는 주인공이지만 Theographic 그래프에 Person 노드가 없는 인물(사사시대 드보라·기드온·입다·삼손·룻 등). 기존 큐레이션 16인은 실제 Theographic `rec` id를 재사용하지만, 사사들은 재사용할 노드가 없어 **마킹된 authored Person 노드를 새로 만든다 (ADR-0008)**. `data/authored_persons/people.json` → `load_authored_persons.py`가 `MERGE (p:Person {theographic_id})` + `authored:true` + `name`/`nameKo`로 멱등 적재. 식별자는 `authored-person-<slug>`(저작 사건 `authored-<slug>`·저작 장소 `authored-place-<name>`와 같은 계열). **적재 순서 제약**: authored Person이 `load_person_events.py`보다 먼저 적재돼야 인물 여정 사건의 `HAS_PARTICIPANT` MATCH가 성립한다. authored **사건의 주변 참여자**(네로·에스더 등 — 카드·여정 없음)는 이 대상이 아니라 여전히 노드 없이 둔다(ADR-0005의 경계). 카드·여정·SidePanel·지도가 일급 Person으로 소비하지만 traits 부여는 별도 enrich 경로다.

## 화면 단계 (Stage)

앱 최상위 화면 전환 단위. 세 단계 — **인물 허브(hub)**: 큐레이션 인물 카드 목록, 시작 화면. **탐험(explore)**: 선택한 인물의 지도·타임라인. **성경 책 둘러보기(overview)**: 66권을 구약/신약·장르(율법서·역사서 등 10범주)로 훑는 화면. 사용자에게 노출되는 라벨은 **"성경 책 둘러보기"로 통일**한다 — "성경 개요"는 같은 단계를 가리키던 옛 표기로, 진입 버튼("성경 책 둘러보기")과 어긋나 혼동을 주므로 쓰지 않는다.

## 상세 시트 (Detail Sheet)

사용자가 선택한 대상(인물·장소·사건·성경책)의 상세 정보를 보여주는 화면 요소. **대상 종류와 무관하게 하나뿐**이다 — "인물창"·"책 상세창"·"레이어"처럼 따로 있는 게 아니라, 같은 시트가 선택 대상에 따라 담는 내용만 바꾼다. 데스크톱에선 화면 우측에서, 모바일에선 화면 아래에서 올라온다. 탐험 화면에서 지금 탐험 중인 인물 자신은 이 시트로 겹쳐 띄우지 않고(여정 흐름을 가리지 않도록) 그 외 대상을 고르면 뜬다. 허브 화면에는 선택 대상이 없어 시트가 없다. → [[화면-단계-stage]], [[selectednode]]

## selectedNode

프론트엔드 전역 상태. 현재 사용자가 선택한 엔티티의 `theographic_id`와 레이블(Person/Place/Event/Book)을 담는다. MapView / TimelineView 두 뷰가 이 값을 구독해 동시에 갱신된다. (GraphView는 제거됨.)

## 사건의 근거 (Scriptural Evidence)

특정 Event를 기록한 성경 본문. TimelineView의 데이터 흐름은 **연도 → 사건 → 성경권 → 성경구절**이며, 마지막 두 단계가 그 사건의 근거다. 권 단계는 `CONTAINS_BOOK`(사건 ↔ 권, 한 사건에 여러 권 가능), 구절 단계는 원천 theographic `verses`에서 사건·권별로 해석한 절들(인용 범위 + 본문)이다. 타임라인은 사건을 척추로 두고 그 사건의 근거 권을 칩으로 붙여 보여준다. 단, 사건이 없는 책(`startYear` 없음 = `CONTAINS_BOOK` 미연결, 서신서·시편·잠언 등 31권)은 근거 칩이 아니라 추정연도(`book_years_approx`) 단독 마커로 표시되며, 사건이 없으므로 구절 근거 단계는 갖지 않고 클릭 시 권 개요만 보여준다. 다만 이 마커 행에는 **book_events 오버레이**(위 항목)로 그 책과 약하게 연결된 사건이 ⚡ 칩으로 곁들여 표시된다 — 이는 "사건의 근거"(권→사건 기록)가 아니라 책의 집필 배경·저자 맥락이라 방향·의미가 반대다.

## 탐색 관점 (Navigation Perspective)

BibleMap 데이터를 바라보는 세 가지 중심 관점. 관점에 따라 같은 데이터가 다르게 시각화된다.

**인물 중심 (Person-centric)**: 특정 Person이 참여한 Event와 그 Event가 발생한 Place들로 해당 인물의 활동 반경을 구성한다. Person에 좌표가 없는 이유도 여기서 비롯된다 — Person은 `HAS_PARTICIPANT → Event → OCCURS_AT → Place` 경로를 통해 간접적으로 공간을 갖는다. **지도에 표시되는 장소 수는 Theographic 이벤트와 authored 이벤트를 합산해 집계된다** — 따라서 인물 대상 authored 이벤트를 추가 계획할 때는 먼저 기존 Theographic 이벤트가 연결하는 장소 수를 파악해야 실제 필요한 authored 이벤트 수를 산정할 수 있다.

**장소 중심 (Place-centric)**: 특정 Place에서 발생한 Event와 그 Event에 참여한 Person들을 조회한다. 지도 마커 클릭이 이 관점의 진입점이다.

**시대 중심 (Era/Timeline-centric)**: 특정 시기의 Event 흐름과 그에 연결된 Person·Place를 탐색한다. `Period`(= Event의 `PART_OF` 계층)가 이 관점의 정렬 축이 된다. TimelineView는 사건을 시대순으로 늘어놓고, 각 사건의 "사건의 근거"(성경권 → 구절)를 함께 보여준다.

## 여정 (Journey)

한 인물의 **시간순 사건(Event) 묶음**. 여정은 사건 하나가 아니라 사건들의 시퀀스이며, 계층은 **여정 ⊃ 사건(여러 개) ⊃ 그 사건의 근거 구절**이다 — 근거 구절은 여정에 직접 붙는 것이 아니라 여정을 구성하는 **각 사건에** 붙는다. 각 사건은 발생 장소(Place)를 통해 지도상의 한 정차지로 나타난다(좌표 없는 사건은 정차지 없이 목록에만 표시). "인물 중심 관점"의 핵심 산물로, 큐레이션 인물에 대해 정의된다. UI(JourneyList)는 이 계층을 "{인물}의 여정 · 사건 N개 → 각 사건 펼치면 구절" 아코디언으로 보여준다.

## 인물 연결 (Person Connections)

큐레이션 인물([[여정-journey]]을 가진 34인) 상세 시트에서 그 인물과 이어지는 **다른 큐레이션 인물**을 보여주는 두 축. 둘 다 **큐레이션 인물로 한정**되어 모든 항목이 여정으로 점프 가능하다 — 장소판 선례("이 곳을 지난 인물" = `/place/{id}/curated-persons`)의 인물판이다. 기존 SidePanel "이웃"의 가족 관계(부모·자녀·형제·배우자 등 직접 그래프 관계)와는 **다른 축**이며, 그것을 대체하지 않고 별도 섹션으로 얹는다.

- **함께 등장한 인물 (Co-participant)**: 같은 `Event`에 `HAS_PARTICIPANT`로 **함께 참여**한 인물. `Person`끼리는 직접 관계가 없고 `Event`를 경유한 2-hop 공동 등장이라(사건 → 참여자) 가족 관계와 의미가 다르다. **여정 사건의 다참여자 밀도에 의존해 인물마다 편차가 크다** — 신약·족장 클러스터(예수·베드로·야곱)엔 여럿 잡히지만, 여정이 단일 참여자 authored 사건으로 채워진 인물(다윗·솔로몬·사울·사무엘·엘리야 등)은 그래프상 공동 참여자가 없어 비며(현재 34인 중 15인만 존재), 빈 섹션은 숨긴다. 공유 사건 수 내림차순.
- **동시대 인물 (Contemporary)**: 같은 큐레이션 **시대(era)** 에 속한 인물(원시사·족장·출애굽·정복·사사·왕국·선지자·포로·신약 8구간, `persons.py`의 `_ERA`). era는 모든 큐레이션 인물에 부여돼 있고 각 구간에 2인 이상이라 **항상 1명 이상** 나온다 — 함께 등장한 인물이 비는 인물의 유일한 연결 축이 된다. 함께 등장한 인물에 이미 나온 인물은 중복 제거한다.

→ [[여정-journey]], [[탐색-관점-navigation-perspective]]


---

# Coding principles

You are a lazy senior developer. Lazy means efficient, not careless. The best code is the code never written.

Before writing any code, stop at the first rung that holds:

1. Does this need to be built at all? (YAGNI)
2. Does the standard library already do this? Use it.
3. Does a native platform feature cover it? Use it.
4. Does an already-installed dependency solve it? Use it.
5. Can this be one line? Make it one line.
6. Only then: write the minimum code that works.

Rules:

- No abstractions that weren't explicitly requested.
- No new dependency if it can be avoided.
- No boilerplate nobody asked for.
- Deletion over addition. Boring over clever. Fewest files possible.
- Question complex requests: "Do you actually need X, or does Y cover it?"
- Pick the edge-case-correct option when two stdlib approaches are the same size.
- Mark intentional simplifications with a `ponytail:` comment naming the ceiling and upgrade path.

Not lazy about: input validation at trust boundaries, error handling that prevents data loss, security, accessibility, anything explicitly requested.
