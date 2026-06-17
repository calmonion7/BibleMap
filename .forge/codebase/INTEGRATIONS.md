---
last_mapped_commit: 1003d7beae209835a39266883039d287158e9e92
mapped: 2026-06-18
---

# INTEGRATIONS

BibleMap이 의존하는 외부 API·데이터 소스·DB·서드파티 서비스 정리. 인증 제공자나 웹훅은 없다(공개 데이터 소비형 앱). 모든 외부 호출은 무인증 공개 엔드포인트다.

## 1. 데이터베이스 — Neo4j (내부 서비스)

- 그래프 DB. compose 서비스 `neo4j`(이미지 `neo4j:5`), Bolt `bolt://neo4j:7687`.
- 접속 코드: `backend/app/db.py` — `GraphDatabase.driver(uri, auth=(user, password))`. URI/USER/PASSWORD는 환경변수(`NEO4J_URI`/`NEO4J_USER`/`NEO4J_PASSWORD`).
- 비밀번호 미설정 시 `backend/app/db.py`가 `RuntimeError`. compose는 `NEO4J_AUTH=neo4j/${NEO4J_PASSWORD}`로 초기 계정 생성.
- 외부 노출 아님(`127.0.0.1` 바인딩, `docker-compose.yml`).

## 2. Theographic Bible Metadata — 외부 데이터 소스 (GitHub raw)

오픈 데이터셋 `robertrouse/theographic-bible-metadata`의 GitHub raw JSON. ETL 스크립트가 `urllib.request`로 직접 fetch한다. 인증 없음.

- 기준 URL 패턴: `https://raw.githubusercontent.com/robertrouse/theographic-bible-metadata/master/json/<name>.json`.
- 소비처:
  - `backend/scripts/load_theographic.py` — `people.json`, `places.json`, `events.json`, `peopleGroups.json` → Neo4j 노드·관계. `fields.status == "publish"`만 적재(Event/PeopleGroup은 status 없어 전체 포함).
  - `backend/scripts/load_books.py` — `books.json`, `events.json` → Book 노드 + `CONTAINS_BOOK` 관계.
  - `backend/scripts/generate_event_verses.py` — `events.json`, `verses.json`(약 15MB) → `data/event_verses/events.json` 생성(아래 4절).
  - `backend/scripts/generate_book_context.py`, `backend/scripts/generate_person_traits.py` — `books.json`/`people.json`/`events.json`을 Claude 프롬프트 입력으로 fetch.
- 식별자: 각 레코드의 `id`가 곧 그래프 노드의 `theographic_id`(전 시스템의 join 키). verse 레코드의 `verseID`는 `BBCCCVVV`(책 2자리·장 3자리·절 3자리) 포맷.

## 3. GetBible API v2 — 빌드타임 미리굽기 전용 (런타임 호출 없음)

ADR-0003에 따라 런타임 GetBible 호출이 제거됨. 절 본문은 `backend/scripts/generate_verse_text.py`가 빌드타임에 미리 받아 데이터 파일에 인라인 저장하며, 앱 런타임에서 GetBible을 직접 호출하지 않는다.

- 엔드포인트(빌드타임 스크립트에서만): `https://api.getbible.net/v2/{slug}/{bookOrder}/{chapter}.json`. 번역 슬러그 `korean`(한국어), `kjv`(영어).
- 인증 없음. `Python-urllib` User-Agent에 403 반환 이슈 → 스크립트가 브라우저류 UA 사용.
- 소비 스크립트: `backend/scripts/generate_verse_text.py` — `event_verses/events.json`, `book_context/books.json`, `character_traits/people.json`에 `textKo`/`textEn`(또는 `keyVerseTextKo/En`, `verse_textKo/En`) 필드 인라인 저장. 멱등(기존 본문 있는 항목 스킵). 유니크 (번역, 책, 장)당 1회 fetch+캐시.
- 프론트엔드에서 `getbible.js`가 삭제/미사용 상태 — `TimelineView.jsx`와 `SidePanel.jsx`는 API 응답에 이미 포함된 `textKo`/`textEn`을 직접 표시.

## 4. 생성 데이터 파일 — `data/event_verses/events.json`

대형 생성 데이터(~93,767줄, ~2MB). 사건별 근거 성경 구절을 권별로 묶은 오버레이. 각 절에 `textKo`/`textEn` 본문이 인라인 저장돼 런타임 외부 호출 없이 표시된다(ADR-0003).

### 생성 방법 (`backend/scripts/generate_event_verses.py`)

1. Theographic GitHub raw에서 두 JSON을 fetch:
   - `EVENTS_URL` = `.../master/json/events.json` (사건별 `fields.verses` = 구절 레코드 id 배열)
   - `VERSES_URL` = `.../master/json/verses.json` (~15MB, 구절 레코드)
2. verse 레코드를 `id`로 인덱싱. 각 사건의 `fields.verses`를 따라 구절 레코드를 찾고, 레코드의 `fields.book[0]`(= Book의 theographic_id)으로 권별 그룹핑.
3. `verseID`(`BBCCCVVV`)를 파싱해 `{verseID, bookOrder, chapter, verse}` 생성(레코드의 `fields.chapter`는 레코드 ID라 쓰지 않고 verseID에서 파생).
4. 권별로 `verseID` 정렬 후 `build_range_label`로 연속 구간을 접어 `rangeLabel` 생성(예 `1:1–31, 2:1–3`; 장 경계 넘는 연속은 `C1:Vs–C2:Ve`).
5. 권 배열은 `bookOrder` 정경순 정렬.
6. 출력: `data/event_verses/events.json`, 구조 `{ "<event_theographic_id>": { "books": [ {bookId, bookOrder, rangeLabel, verses:[{verseID, chapter, verse, textKo, textEn}]} ] } }`. `textKo`/`textEn`은 `generate_verse_text.py` 실행 후 채워짐.

수동 실행(`python3 generate_event_verses.py` → `python3 generate_verse_text.py`)하는 일회성 빌드 단계. 출력 파일이 git에 커밋되어 배포된다.

### 소비 방법

- `backend/app/routes/events.py`의 `GET /event/{event_id}/verses` — `events.json`을 `functools.lru_cache(maxsize=1)`로 1회 로드 후 사건 id로 조회해 반환. 파일 탐색은 `DATA_DIR`(기본 `/app/data`) → 레포 상대경로 폴백.
- 프론트(`frontend/src/TimelineView.jsx`)가 이 응답의 `bookId`를 `/events`의 책 id와 join해 권별 탭으로 표시하고, `verses[].textKo`/`textEn`을 `verseLang` 상태에 따라 직접 렌더링(런타임 외부 호출 없음).

## 5. 저작 사건 데이터 — `data/authored_events/events.json`

수기로 작성된 저작 사건 7건. Theographic 데이터에 없는 서신서·묵시록 집필 배경 사건을 보완한다.

- 파일: `data/authored_events/events.json`. 각 레코드: `id`(`authored-*` prefix), `title`, `nameKo`, `sortKey`, `startDate`, `yearLabel`, `context`, `occursAt`(Place theographic_id[]), `participants`(Person theographic_id[]), `mappedBookIds`(Book theographic_id[], 참조용).
- 적재: `backend/scripts/load_authored_events.py` — `MERGE (e:Event {theographic_id: $id})`로 멱등 적재. `authored=true` 속성. `CONTAINS_BOOK` 관계는 생성하지 않음(ADR-0005: 서신서는 사건을 '기록'하지 않음).
- 소비:
  - `backend/app/routes/events.py`의 `GET /events` — `authored` 속성을 그대로 반환(`authored: props.get("authored", False)`).
  - `backend/app/routes/books.py`의 `GET /books` — `data/book_events/books.json` 오버레이를 통해 bookId → authored eventId[] 연결을 `events` 필드로 반환.
  - `frontend/src/TimelineView.jsx` — `rep.authored === true`이면 추정 마커(번개 칩) 표시.

## 6. Anthropic Claude API — 빌드타임 콘텐츠 생성 (서드파티)

오프라인 데이터 생성에만 쓰이는 서드파티 LLM. 런타임 앱에는 포함되지 않는다.

- SDK: Python `anthropic`(`requirements.txt`엔 없고 호스트 환경에 별도 설치 전제).
- 인증: `ANTHROPIC_API_KEY` 환경변수(없으면 스크립트가 RuntimeError).
- 모델: `claude-haiku-4-5-20251001` (`backend/scripts/generate_book_context.py`, `backend/scripts/generate_person_traits.py` 모두 `max_tokens=512`).
- 소비처/산출물:
  - `generate_book_context.py` — 책별 배경·주제·대표구절 → `data/book_context/books.json`. 재실행 시 기존 항목 스킵, 항목마다 중간 저장 + `time.sleep(0.3)` rate-limit 여유.
  - `generate_person_traits.py` — 이벤트 참여 상위 N명(기본 `--top 100`)의 성품 → `data/character_traits/people.json`. 동일 스킵/중간저장/sleep 패턴.
- 생성물은 `inject_book_context.py`/`inject_person_traits.py`가 Neo4j 노드 속성으로 주입(런타임 노출). `generate_verse_text.py`가 이후 절 본문을 인라인 추가.

## 7. 지도 타일 / 폰트 — 외부 정적 자원 (프론트엔드 런타임)

`frontend/src/MapView.jsx`가 MapLibre GL 스타일에 직접 지정한 외부 자원. 인증 없음(공개).

- 래스터 타일(베이스맵): Esri ArcGIS Online `NatGeo_World_Map` —
  `https://server.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}` (`tileSize: 256`, 소스 id `esri`, 레이어 `esri-layer`).
- 글리프(폰트): Protomaps basemaps-assets —
  `https://protomaps.github.io/basemaps-assets/fonts/{fontstack}/{range}.pbf`.
- MapLibre 스타일은 인라인 정의(`version: 8`) — 외부 style URL이나 MapTiler 등 키 기반 서비스는 쓰지 않는다.

## 8. 자체 백엔드 API (프론트 ↔ 백엔드)

외부 통합은 아니지만 프론트가 의존하는 내부 계약. 단일 클라이언트 `frontend/src/api.js`(`apiGet`)가 `API_BASE`(prod `/api`, dev `http://localhost:8000`)로 호출.

- `GET /node/{id}`, `GET /node/{id}/places`, `GET /node/{id}/neighbors/grouped` (`backend/app/routes/nodes.py`)
- `GET /events`, `GET /event/{id}/verses` (`backend/app/routes/events.py`)
- `GET /search?q=` (`backend/app/routes/search.py`)
- `GET /books` (`backend/app/routes/books.py`)

모두 GET. CORS는 백엔드에서 `*` 전체 허용(`backend/app/main.py`), 응답 헤더 `Cache-Control: no-store`(events/books).

## 9. 인증 / 웹훅 — 없음

- 사용자 인증 제공자 없음(공개 읽기 전용 앱). Neo4j 자체 인증만 존재.
- 외부로 나가는 웹훅·콜백 없음. 인바운드 웹훅 없음.
- 유일한 자동화 트리거는 `.github/workflows/deploy.yml`(GitHub `push` → self-hosted 러너 배포)로, 외부 서비스 연동이 아닌 CI다.
