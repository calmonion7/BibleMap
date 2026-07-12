# BibleMap — 도메인 용어집

## 구절 근거 원칙 (verse-grounded principle)

이 사이트가 사용자에게 보여주는 모든 분석·서술 정보는 **성경 구절을 근거로 삼는 것이 제1규칙**이다. 근거 구절 없는 진술을 화면에 두지 않으며, 데이터를 만들거나(저작·큐레이션) 지우는(중복 제거 등) 작업은 결과물이 구절 근거를 잃지 않는지를 기준으로 검증한다 — 인물 소개·성품이 진술마다 근거 절을 다는 것, 사건이 근거 구절(📖)을 갖는 것이 모두 이 원칙의 사례.
_Avoid_: "참고 구절"(장식적 인용이라는 뉘앙스 — 구절은 장식이 아니라 근거다)

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

**의미**: `(Book)-[:CONTAINS_BOOK]->(Event)`는 "그 책이 그 사건을 기록한다" = **사건의 성경적 근거**를 뜻한다. 한 사건을 여러 권이 기록할 수 있다(예: 공관복음 평행 기사 → 마/막/눅).

**발생(primary) vs 회고 인용 (ADR-0012)**: 한 사건의 참조가 여러 책에 걸칠 때, **첫 참조(authored=`books[0]`, theographic=`verses[0]`의 책)가 발생 위치**이고 나머지는 **다른 책의 회고 인용**이다(예: 아브라함 부름은 창세기에서 *발생*하고 사도행전 스데반 설교가 *인용*). 관계에 `primary` 불리언으로 구분하며, Book의 "주요 사건(topEvents)·주요 인물(topPersons)·지도 장소"는 `primary` 관계만 집계한다(회고 인용이 그 책 파생 뷰를 오염시키지 않도록). 반대로 사건 행의 📖 근거 칩(사건→기록 책)은 인용도 정당한 근거라 primary로 거르지 않는다. 한계: 서신서가 신학적으로 회고하는 사건(히 11장 믿음의 선진 등)은 verses[0]가 그 서신이라 서신을 발생으로 오판정할 수 있다(서신서는 CONTAINS_BOOK으로 연대·발생 판정 불가 — 실 저작일은 [[저작-사건-authored-event]]). 사건의 날짜가 없는 책(서신서·시편·잠언 등 31권)은 이 관계가 없어 사건 근거 칩으로는 등장하지 않고, 대신 추정연도 단독 마커로 배치된다(아래 "사건의 근거" 참조). 이 31권은 별도의 **book_events 오버레이**(아래 항목)로 "집필 배경·저자·직접 다루는" 사건과 약하게 연결되어 마커 행에 사건 칩이 표시되지만, 이는 `CONTAINS_BOOK`(권위 그래프·구절 교집합)과 별개의 추정 연결이다.

## Character Trait (인물 성품)

Person 노드에 주입되는 속성 `traits` (JSON 문자열 배열). 각 항목: `{trait: "겸손", verse_ref: "민 12:3", description: "..."}`. LLM(Claude API)으로 생성 후 수동 검수, `data/character_traits/people.json` → `inject_person_traits.py`로 Neo4j 주입.

**성품의 정의 (task#157)**: 시간·상황을 관통해 반복 확인되는 **지속적 인격 특질** — 미덕과 결함을 모두 포함한다(성경은 인물을 미화하지 않으므로 다윗의 통회·야곱의 기만처럼 결함도 정직하게 싣는다). 행위·사건(예배·찬양), 칭호·신분(하나님의 마음·메시아 계보), 은사·능력(괴력·예언), 시기·이력(말년의 타락)은 성품이 아니다 — 행위는 성품의 *증거*로 verse_ref·description에만 담는다. 라벨은 **통제 어휘**(미덕 24+결함 8) 안에서만 쓰며, 정본 규칙·어휘 표는 `data/character_traits/AUTHORING.md`, 기계검증은 `validate_traits.py`.

## Book Context (권별 컨텍스트)

각 Book의 시대적 배경·주제·대표구절을 담는 정적 JSON (`data/book_context/books.json`). LLM(Claude API)으로 생성 후 수동 검수. `inject_book_context.py`로 Book 노드 속성에 주입. Verse 텍스트(대표구절·인물 성품 인용절)는 **빌드타임에 getbible에서 한국어(`korean`)+영어(`kjv`)로 미리 받아 데이터에 함께 저장**한다(`generate_verse_text.py`, ADR-0003) — 런타임 외부 fetch 없음. 단 **사건 근거 절 본문은 인라인이 아니라 정본 절 사전**(`data/bible/verses.json`, 전권 31,103절 프리베이크)에서 `/event/{id}/verses` 응답 시 합성한다(ADR-0015 — event_verses는 verseID 참조만 보유). Book의 대표구절 본문은 `keyVerseTextKo`/`keyVerseTextEn` 속성으로 주입된다.

## Place Context (장소 컨텍스트)

좌표가 있어 지도에 뜨는 장소(43개)의 **성경적 배경 산문(`background`)·대표구절(`keyVerse`)**을 담는 정적 JSON (`data/place_context/places.json`, dict 키=장소 id). **Book Context의 장소판** — 구조·파이프라인이 동일하다: LLM 직접 생성(ADR-0006, `place_coords`의 `note`를 시드로) → 대표구절 본문 빌드타임 프리베이크(`generate_verse_text.py`의 `bake_place_context`, `keyVerseTextKo`/`keyVerseTextEn`) → `inject_place_context.py`로 Place 노드에 4개 필드(`background`/`keyVerse`/`keyVerseTextKo`/`keyVerseTextEn`)만 SET. **실제 노드의 서술 보강이라 오버레이가 아니라 주입**한다(추정 독립 데이터만 오버레이하는 ADR-0004 원칙 — book_context와 동일 선례). SidePanel은 `node.label === 'Place'` 블록에서 "장소 배경"·"대표 구절"(한/영 탭) 섹션으로 렌더한다. 기존 `note` 필드는 시드로만 쓰고 보존(미렌더).

## 추정연도 (placementYear)

사건-구절 교집합(`CONTAINS_BOOK`)이 없어 `startYear`를 못 얻는 31권에 부여하는 타임라인 배치 연도 (`data/book_years_approx/books.json`의 `placementYear`, `yearApprox=true`로 표시). **기준은 "작성(저작) 시점"이 아니라 "그 책이 속하는 사건/내용 시대"** — 정확연도 책의 `startYear`(그 책이 기록한 사건들의 `startDate` 최소~최대를 `load_books.py`가 집계)와 **같은 의미축**이다. 즉 추정/정확은 *의미*가 다른 게 아니라 *도출 방법*만 다르다 (정확 = 사건 집계 자동, 추정 = 사건이 없어 수동 추정). 구약 내러티브·시가서는 배경 시대로 배치하고(작성 시점은 `basis`에 곁들이되 배치엔 안 씀), 신약 서신서·계시록은 "쓰여 보내진 순간이 곧 그 책의 시대"라 결과적으로 작성 시점과 일치한다. 사건 연결(아래 Book Events ⚡)과는 **독립축** — 연결이 있어도 연도는 여전히 추정이다.

## 사건 연대 (startDate)

Event 노드의 발생 시점 속성. **혼재 형식의 문자열**이다 — 연도만("-4003", "30"), 연-월("-1451-01"), 연-월-일 3파트가 공존하고 BC는 음수 접두. 따라서 **문자열 사전순 정렬은 BC 연도를 역전**시킨다("-1451" < "-4003"). 정렬·비교·필터에 쓸 때는 반드시 연도를 파싱해 수치로 다룬다(부호 분리 후 첫 파트를 정수화 — 프론트 `dates.js`의 `parseYear`, 백엔드 nodes.py `_year`가 같은 규칙). 책의 `startYear`는 이 값을 집계해 파생된다(추정연도 항목 참조).

**정본 연대계는 현대 보수 연대계**다(출애굽 BC 1446 · 다윗 통치 1010–970 · 성전 착공 966, 분열왕국은 Thiele 왕 연대 — ADR-0014). theographic 원본 연대는 Ussher계(출애굽 1491 등)로 기록돼 있어 보수계로 저작된 [[저작-사건-authored-event]]·인물 여정과 한 타임라인에서 충돌했고, 교정 오버레이(`data/date_corrections/`)가 원본 이벤트의 `startDate`/`sortKey`를 정본계로 재정렬한다. Person의 `birthYear`/`deathYear`는 UI 미사용이라 Ussher계로 잔존한다(노출 전 ADR-0014 재검토).

## Book Events (책-사건 연결 오버레이)

추정연도 책(31권 — `startYear` 없어 `CONTAINS_BOOK`이 없는 서신서·시편·잠언 등)을 타임라인 사건에 약하게 연결하는 정적 JSON (`data/book_events/books.json`, 형식 `{ "<bookId>": ["<eventId>", ...] }`). 연결 기준은 **집필 배경**(서신서→사도행전 사건)·**저자**(시편→다윗 통치)·**직접 다루는 사건**(역대하→솔로몬·유다 왕). LLM(Claude API)으로 생성하는 추정 데이터(`generate_book_events.py`)라 **Neo4j에 주입하지 않고** `/books` 엔드포인트가 런타임에 오버레이해 각 책에 `events` 배열로 실어 보낸다(`book_years_approx`와 동일한 분리 원칙 — 추정·권위 낮은 데이터는 권위 그래프 밖 오버레이로 유지, inject·재빌드 불필요). TimelineView의 책 마커 행은 이 `events`를 ⚡ Event색 칩으로 표시하고(클릭 시 그 사건 선택), 데이터가 없는 사건(예: AD57 이후 후기 서신·계시록, 포로귀환)은 빈 배열이라 칩이 없다. **CONTAINS_BOOK의 "사건의 근거"(구절 교집합) 의미와 무관 — 사건 행의 📖 근거 칩은 영향받지 않는다.**

## 저작 사건 (Authored Event)

`startDate`를 가진 theographic 사건이 AD57(바울 1차 로마 투옥)에서 끊겨, 그 이후 쓰인 후기 서신·계시록(추정연도 31권 중 10권: 디모데전후·디도·벧전후·유다·요한1~3·계시록)이 매달릴 타임라인 사건이 그래프에 없다. 이를 메우려고 **그 책들이 쓰인 정황을 거꾸로 도출해 만든 추정 사건**이 저작 사건이다 — 성경 본문 밖 자유 역사 사건(예 예루살렘 함락 AD70)이 아니라 **고아 책 기반**(예: 계시록→요한의 밧모섬 유배(계 1:9), 디모데후서→바울 로마 2차 투옥·순교, 베드로전후→베드로 로마 사역·순교, 요한1~3→요한 에베소 만년 사역). theographic 검증 사건과 달리 LLM/수동 저작이라 권위가 낮다.

**오버레이가 아니라 Neo4j `Event` 노드로 적재하되 `authored:true`로 마킹한다 (ADR-0005)** — 사건은 `/events`·`/node/{id}`·`/node/{id}/places`·사건 링이 소비하는 **일급 엔티티**라, 오버레이로만 두면 ⚡ 칩 클릭 시 `/node/{id}`가 404가 되어 SidePanel·지도·링이 깨지기 때문(이 점이 *연도·링크* 오버레이를 다룬 ADR-0004와 갈리는 지점). `/events`가 `authored` 플래그를 노출하고 TimelineView가 `추정` 배지 + 범위 라벨로 표시한다. theographic ID(`rec` 접두)가 없어 `authored-<slug>` 식별자를 `theographic_id`에 부여한다. **`CONTAINS_BOOK`(📖 근거)을 갖지 않으므로** 사건 근거 칩을 오염시키지 않고, 후기 10권과는 **book_events 오버레이(⚡)** 로 연결된다(`CONTAINS_BOOK`이 아니라). 기존 Place(로마·밧모·에베소)·Person(바울·베드로·요한)에 `OCCURS_AT`/`HAS_PARTICIPANT`로 연결해 지도·링을 살린다. 연도는 정렬용 단일 `sortKey` + 표시용 범위 라벨(`yearLabel`)로 둔다.

## 저작 인물 (Authored Person)

성경인물탐험에 큐레이션하려는 주인공이지만 Theographic 그래프에 Person 노드가 없는 인물(사사시대 드보라·기드온·입다·삼손·룻 등). 기존 큐레이션 16인은 실제 Theographic `rec` id를 재사용하지만, 사사들은 재사용할 노드가 없어 **마킹된 authored Person 노드를 새로 만든다 (ADR-0008)**. `data/authored_persons/people.json` → `load_authored_persons.py`가 `MERGE (p:Person {theographic_id})` + `authored:true` + `name`/`nameKo`로 멱등 적재. 식별자는 `authored-person-<slug>`(저작 사건 `authored-<slug>`·저작 장소 `authored-place-<name>`와 같은 계열). **적재 순서 제약**: authored Person이 `load_person_events.py`보다 먼저 적재돼야 인물 여정 사건의 `HAS_PARTICIPANT` MATCH가 성립한다. authored **사건의 주변 참여자**(네로·에스더 등 — 카드·여정 없음)는 이 대상이 아니라 여전히 노드 없이 둔다(ADR-0005의 경계). 카드·여정·SidePanel·지도가 일급 Person으로 소비하지만 traits 부여는 별도 enrich 경로다.

## 화면 단계 (Stage)

앱 최상위 화면 전환 단위. 네 단계 — **인물 허브(hub)**: 큐레이션 인물 카드 목록, 시작 화면. **탐험(explore)**: 선택한 인물의 여정 또는 [[테마 투어]]의 지도·타임라인 — 인물·투어 중 **하나가** 정차지를 공급하며 둘은 상호배타다(투어 구동 시 선택 인물 없음). **테마 투어 목록(tours)**: 테마 투어 카드 목록, 허브에서 진입. **성경 책 둘러보기(overview)**: 66권을 구약/신약·장르(율법서·역사서 등 10범주)로 훑는 화면. 사용자에게 노출되는 라벨은 **"성경 책 둘러보기"로 통일**한다 — "성경 개요"는 같은 단계를 가리키던 옛 표기로, 진입 버튼("성경 책 둘러보기")과 어긋나 혼동을 주므로 쓰지 않는다.

## 상세 시트 (Detail Sheet)

사용자가 선택한 대상(인물·장소·사건·성경책)의 상세 정보를 보여주는 화면 요소. **대상 종류와 무관하게 하나뿐**이다 — "인물창"·"책 상세창"·"레이어"처럼 따로 있는 게 아니라, 같은 시트가 선택 대상에 따라 담는 내용만 바꾼다. 데스크톱에선 화면 우측에서, 모바일에선 화면 아래에서 올라온다. 탐험 화면에서 지금 탐험 중인 인물 자신은 이 시트로 겹쳐 띄우지 않고(여정 흐름을 가리지 않도록) 그 외 대상을 고르면 뜬다. 허브 화면에는 선택 대상이 없어 시트가 없다. → [[화면-단계-stage]], [[selectednode]]

## selectedNode

프론트엔드 전역 상태. 현재 사용자가 선택한 엔티티의 `theographic_id`와 레이블(Person/Place/Event/Book)을 담는다. MapView / TimelineView 두 뷰가 이 값을 구독해 동시에 갱신된다. (GraphView는 제거됨.)

## 사건의 근거 (Scriptural Evidence)

특정 Event를 기록한 성경 본문. TimelineView의 데이터 흐름은 **연도 → 사건 → 성경권 → 성경구절**이며, 마지막 두 단계가 그 사건의 근거다. 권 단계는 `CONTAINS_BOOK`(사건 ↔ 권, 한 사건에 여러 권 가능), 구절 단계는 원천 theographic `verses`에서 사건·권별로 해석한 절들(인용 범위 + 본문)이다. 원천 theographic 사건 외에 **구절 사건(verse-event)** — 책의 *고아 구절*(어떤 Event에도 안 붙은 절)에서 도출해, 그 구절 없이는 타임라인에 안 뜰 서사에 시대 위치를 준 사건 — 도 근거 구절을 갖는데, 이들의 근거는 theographic event→verses 링크가 아니라 **그 책 고아 구절 범위에 앵커해 저작**한다(책 칩만 있고 구절이 비어 "표시할 구절이 없습니다"가 뜨던 갭을 메움). 타임라인은 사건을 척추로 두고 그 사건의 근거 권을 칩으로 붙여 보여준다. 단, 사건이 없는 책(`startYear` 없음 = `CONTAINS_BOOK` 미연결, 서신서·시편·잠언 등 31권)은 근거 칩이 아니라 추정연도(`book_years_approx`) 단독 마커로 표시되며, 사건이 없으므로 구절 근거 단계는 갖지 않고 클릭 시 권 개요만 보여준다. 다만 이 마커 행에는 **book_events 오버레이**(위 항목)로 그 책과 약하게 연결된 사건이 ⚡ 칩으로 곁들여 표시된다 — 이는 "사건의 근거"(권→사건 기록)가 아니라 책의 집필 배경·저자 맥락이라 방향·의미가 반대다.

## 탐색 관점 (Navigation Perspective)

BibleMap 데이터를 바라보는 세 가지 중심 관점. 관점에 따라 같은 데이터가 다르게 시각화된다.

**인물 중심 (Person-centric)**: 특정 Person이 참여한 Event와 그 Event가 발생한 Place들로 해당 인물의 활동 반경을 구성한다. Person에 좌표가 없는 이유도 여기서 비롯된다 — Person은 `HAS_PARTICIPANT → Event → OCCURS_AT → Place` 경로를 통해 간접적으로 공간을 갖는다. **지도에 표시되는 장소 수는 Theographic 이벤트와 authored 이벤트를 합산해 집계된다** — 따라서 인물 대상 authored 이벤트를 추가 계획할 때는 먼저 기존 Theographic 이벤트가 연결하는 장소 수를 파악해야 실제 필요한 authored 이벤트 수를 산정할 수 있다.

**장소 중심 (Place-centric)**: 특정 Place에서 발생한 Event와 그 Event에 참여한 Person들을 조회한다. 지도 마커 클릭이 이 관점의 진입점이다.

**시대 중심 (Era/Timeline-centric)**: 특정 시기의 Event 흐름과 그에 연결된 Person·Place를 탐색한다. `Period`(= Event의 `PART_OF` 계층)가 이 관점의 정렬 축이 된다. TimelineView는 사건을 시대순으로 늘어놓고, 각 사건의 "사건의 근거"(성경권 → 구절)를 함께 보여준다.

## 여정 (Journey)

한 인물의 **시간순 사건(Event) 묶음**. 여정은 사건 하나가 아니라 사건들의 시퀀스이며, 계층은 **여정 ⊃ 사건(여러 개) ⊃ 그 사건의 근거 구절**이다 — 근거 구절은 여정에 직접 붙는 것이 아니라 여정을 구성하는 **각 사건에** 붙는다. 각 사건은 발생 장소(Place)를 통해 지도상의 한 정차지로 나타난다(좌표 없는 사건은 정차지 없이 목록에만 표시). "인물 중심 관점"의 핵심 산물로, 큐레이션 인물에 대해 정의된다. UI(JourneyList)는 이 계층을 "{인물}의 여정 · 사건 N개 → 각 사건 펼치면 구절" 아코디언으로 보여준다.

## 테마 투어 (Themed Tour)

여러 인물의 [[여정-journey]]을 하나의 주제(시대·서사)로 엮은 큐레이션된 시간순 사건 시퀀스. 여정이 *한 인물*의 사건 묶음인 것과 달리, 테마 투어는 한 인물로는 드러나지 않는 관계(예: 사울-다윗 대립, 족장 4세대 언약)를 여러 인물의 사건을 교차해 보여준다. 계층은 여정과 동일하다 — **투어 ⊃ 사건(여러 개) ⊃ 각 사건의 근거 구절**. 단일 주인공이 없어, 투어를 구성하는 사건들의 참여자가 곧 그 투어의 등장인물이다. 성경 서사 척추(시대)를 따라 큐레이션되며, 각 투어는 기존 여정 사건을 재사용해 엮는다(신규 사건 저작이 아니라 순서·틀 부여). → [[여정-journey]], [[탐색-관점-navigation-perspective]]

## 인물 연결 (Person Connections)

큐레이션 인물([[여정-journey]]을 가진 34인) 상세 시트에서 그 인물과 이어지는 **다른 큐레이션 인물**을 보여주는 두 축. 둘 다 **큐레이션 인물로 한정**되어 모든 항목이 여정으로 점프 가능하다 — 장소판 선례("이 곳을 지난 인물" = `/place/{id}/curated-persons`)의 인물판이다. 기존 SidePanel "이웃"의 가족 관계(부모·자녀·형제·배우자 등 직접 그래프 관계)와는 **다른 축**이며, 그것을 대체하지 않고 별도 섹션으로 얹는다.

- **함께 등장한 인물 (Co-participant)**: 같은 `Event`에 `HAS_PARTICIPANT`로 **함께 참여**한 인물. `Person`끼리는 직접 관계가 없고 `Event`를 경유한 2-hop 공동 등장이라(사건 → 참여자) 가족 관계와 의미가 다르다. **성경상 다른 큐레이션 인물과 같은 사건에 등장하는지에 따라 인물마다 편차가 크다** — 함께 등장하는 인물(왕국 다윗·사울·사무엘·솔로몬, 선지자 엘리야·엘리사, 예수·베드로·야곱 등)엔 잡히고, 어떤 큐레이션 인물과도 공동등장이 없는 고립 인물(사사들·요나·에스더·다니엘 등)은 비어 ②동시대만 남는다. 빈 섹션은 숨기며 — 억지로 만들지 않고 **공백이 곧 그 인물의 고립을 뜻해 정확**하다. 공유 사건 수 내림차순.
- **동시대 인물 (Contemporary)**: 같은 큐레이션 **시대(era)** 에 속한 인물(원시사·족장·출애굽·정복·사사·왕국·선지자·포로·신약 8구간, `persons.py`의 `_ERA`). era는 모든 큐레이션 인물에 부여돼 있고 각 구간에 2인 이상이라 **항상 1명 이상** 나온다 — 함께 등장한 인물이 비는 인물의 유일한 연결 축이 된다. 함께 등장한 인물에 이미 나온 인물은 중복 제거한다.

→ [[여정-journey]], [[탐색-관점-navigation-perspective]]

## 인물 관계 (Person Relations)

한 인물이 다른 인물과 맺는 관계의 **성격(valence)** 과 그 **시간적 변화**를 손큐레이션으로 담아 **전용 화면**으로 보여주는 축. [[인물-연결-person-connections]]이 그래프에서 파생한 *연결의 존재*(누가 누구와 같은 사건에)만 보여주는 것과 달리, 인물 관계는 그 관계가 **긍정·부정·중립 중 무엇이며 시간에 따라 어떻게 변하는지**를 사람이 붙인 라벨로 표현한다 — valence는 사건 참여로 파생 불가라 반드시 큐레이션이다. **네트워크 그래프가 아니다**(GraphView 삭제 결정 유지) — 시간축 기반 레이아웃으로 표현한다.

- **valence (관계 성격)**: `긍정`·`부정`·`중립` 세 값. 그 시점 관계의 지배적 성향.
- **관계 유형 (type)**: valence와 **직교하는 구조적 분류** — 가족·연인·친구·신하·선지자·스승제자·대적·군주·하나님 등(`스승제자` = 랍비-제자·후계 계승, 엘리↔사무엘·엘리야↔엘리사·예수↔제자; `하나님` = 인물↔하나님의 언약·부르심·순종·반역·심판 축으로, 상대 endpoint는 큐레이션 인물이 아닌 `하나님` 이름 라벨이며 valence로 순종·반역·회개의 변화를 국면에 담는다). valence가 시간에 따라 변하는 감정 성향이라면, 유형은 그 인물이 상대와 맺는 **고정된 관계 종류**다(pair 단위 1개). 뷰에서 유형별 아이콘으로 표시하고 유형끼리 모아 정렬한다.
- **국면 (phase)**: 한 관계 = 시간순 국면 배열. 관계는 성경 서사에서 변한다(다윗↔사울: 총애→시기·추격→살려줌). 각 국면은 valence·라벨·**근거 구절**·대략 연도를 가진다. 변하지 않는 관계는 국면이 하나.
- **레인 (lane) / 초점 쌍 (focus pair)**: 표현의 두 층. **레인** = 관계마다 가로 한 줄, 시간축 위 valence 색 띠(교차선 없이 개요). **초점 쌍** = 한 관계를 골랐을 때 두 인물을 마주 세우고 국면을 시간순으로 잇는 상세.
- **근거 구절 레이어 (evidence verse layer)**: 국면을 누르면 그 관계 근거인 성경 구절 **본문**(한/영)을 레이어로 조회. 근거는 두 층 — **앵커 절**(그 국면의 기준이 되는 한 절)과 **문맥 범위**(앵커를 이해하게 하는 같은 장 안의 주변 절들, 앵커 포함). 문맥 범위가 있으면 범위 절들을 앵커 강조와 함께 보여주고, 없으면 앵커 절 하나로 폴백한다. 구절 본문은 빌드타임 getbible 프리베이크(ADR-0003 선례)로 미리 받아 저장.
- **person-centric (한 인물 기준, 비대칭)**: 주체 인물 하나 기준으로 상대들을 담으며 상대는 **큐레이션 인물이 아니어도 된다**(요나단·밧세바·압살롬 등). 상대가 큐레이션이면 그 여정으로 점프 가능, 아니면 이름 라벨로만 남는다.
- **역할 라벨 (role, 원근 비대칭)**: 가족류 관계에서 각 endpoint는 자기 역할 라벨(`role`)을 가지며 — 아담↔아벨은 아담=`아버지`, 아벨=`둘째 아들` — **뷰는 늘 상대 endpoint의 role을 표시**한다. 그래서 아벨 상세엔 아담이 `아버지`로, 아담 상세엔 아벨이 `둘째 아들`로 원근이 맞게 읽힌다(관계는 pair 하나지만 라벨은 양쪽에서 다르다). 상대가 비큐레이션이면 상대를 가리키는 단일 라벨(`note`)로 대신한다.

→ [[여정-journey]], [[인물-연결-person-connections]], [[화면-단계-stage]]

## 가계도 (Family Tree)

한 인물을 중심으로 **혈통(kinship)** 을 세대별로 세워 보여주는 전용 화면. 데이터는 **그래프 혈통 간선** — 부모↔자식(`PARENT_OF`/`CHILD_OF`), 형제(`SIBLING_OF`), 배우자(`PARTNER_OF`) — 에서 파생하며, theographic 원본의 `father`/`mother`(배열)를 적재하는 것이 원천이다. **혈통이 단절되는 지점(부모가 미게시 인물이라 노드가 없거나 원본에 링크가 없는 곳)은 [[저작-인물-authored-person]] 패턴으로 보충**한다(재저작이 아니라 구멍 메우기). 대표 계보 1건(예수의 족보 — 마태복음 1장)은 이 보충으로 뿌리까지 무단절을 보증한다.

세 이웃 개념과 명확히 구분된다:

- **SidePanel "이웃"의 가족(직계 1-hop)** 과 달리, 가계도는 같은 그래프 간선을 **다세대로 확장**한다 — 위로 조상선을 뿌리까지 완전히 펼치고, 아래로 자손 2세대까지, 형제·배우자는 focus 행에 인라인. 아무 노드나 클릭하면 그 인물로 **재중심화(ego-centric)** 한다.
- **[[인물-관계-person-relations]]**(서사 valence·국면)와 달리, 가계도에는 valence·국면·근거구절이 없다 — 오직 **구조적 혈통**만 담는 결정적 그래프 파생 뷰다. (person_relations의 "가족" 유형이 방향 role 라벨을 손큐레이션으로 담는 것과 별개 축이다.)
- **삭제된 GraphView(포스-디렉티드 네트워크)** 와 달리, 가계도는 세대가 축을 이루는 **계층 트리**다 — 자유 배치 네트워크가 아니다. 라이브러리 없이 손수 SVG/CSS로 렌더한다.

→ [[인물-관계-person-relations]], [[저작-인물-authored-person]], [[화면-단계-stage]]

## 인물 소개 (Person Context)

큐레이션 인물의 [[화면-단계-stage]] 소개(intro) 탭에 담기는 **정체성 콘텐츠** — 그 인물이 *누구이고 왜 중요한가*를 한눈에 전한다. 세 요소: **역할(role)** 한 줄 별칭("최초의 사람"), **소개문(intro)** 2–3문장, 그 산문을 뒷받침하는 **근거 구절(verses, 대표+근거 겸함)**. 프로젝트 저작 원칙에 따라 **모든 소개·역할은 성경 구절을 근간으로 하며 근거 구절 없는 진술을 두지 않는다** — [[인물-성품-character-trait]]이 성품마다 근거 구절을 다는 것과 같은 결이다. [[인물-관계-person-relations]](관계의 성격·변화)·[[인물-성품-character-trait]](성품)·[[여정-journey]](행적)과 구분되는 축으로, 소개 탭은 이 셋을 정체성으로 묶고 나머지 깊은 탐색(발자취·타임라인·관계)으로 가는 **관문** 역할을 한다. 손큐레이션 오버레이이며 구절 본문은 빌드타임 프리베이크(ADR-0003 선례). → [[인물-성품-character-trait]], [[인물-관계-person-relations]], [[화면-단계-stage]]


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
