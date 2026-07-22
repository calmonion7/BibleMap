---
last_mapped_commit: f5e17ae2993e228f8b7481dba03478ddec8616f4
mapped: 2026-07-22
---

# STRUCTURE

리포지토리 디렉터리 레이아웃, 핵심 파일 위치, 데이터/스크립트 명명 규칙을 다룬다.

## 최상위 레이아웃

```
BibleMap/
├── backend/                 # FastAPI 앱 + 데이터 적재 스크립트
├── frontend/                # React(Vite) SPA
├── data/                    # 원천/저작/오버레이 JSON (여러 서브디렉터리 + 최상위 파일 2개)
├── nginx/                   # nginx 리버스 프록시 설정
├── docker-compose.yml       # neo4j + api + nginx 스택
├── deploy.sh                # 빌드→이미지→up→ko-name 주입 배포 스크립트
├── .env / .env.example      # NEO4J_PASSWORD (compose가 NEO4J_AUTH로 파생)
├── .github/workflows/deploy.yml  # self-hosted 러너 CI 배포
├── README.md                # 로컬 실행 순서
├── CLAUDE.md                # 프로젝트 작업 지침
└── BIBLEMAP_PLAN.md         # 초기 기획 문서
```

## backend/

```
backend/
├── Dockerfile               # python:3.12-slim, uvicorn app.main:app :8000
├── requirements.txt         # fastapi / neo4j / uvicorn
├── __init__.py
├── app/                     # 런타임 애플리케이션
│   ├── __init__.py
│   ├── main.py              # FastAPI 엔트리 (lifespan 인덱스, CORS, 12개 라우터 include)
│   ├── db.py                # get_driver() Neo4j 드라이버 싱글턴
│   ├── overlays.py          # 런타임 오버레이 로더 (_resolve/_resolve_dir/_load + 캐시 로더 9종 + curated_person_id)
│   └── routes/              # API 라우터 (라벨/엔티티별)
│       ├── __init__.py
│       ├── nodes.py         # /node/{id}, /neighbors/grouped, /places, /person/{id}/event-ids
│       ├── events.py        # /events, /event/{id}/verses
│       ├── books.py         # /books-overview, /book/{id}/chapters, /book/{id}/chapter/{n}, /book/{id}/quotations
│       ├── persons.py       # /persons/curated, /keypeople-cards, /connections, /relations(withSlug 포함)
│       ├── journey.py       # /person/{id}/journey
│       ├── places.py        # /place/{id}/curated-persons
│       ├── search.py        # /search (status='wip' 제외)
│       ├── tours.py         # /tours, /tour/{id} (stops는 {id, note} 객체 배열, ADR-0028)
│       ├── family.py        # /person/{id}/family (가계도 서브그래프 + mothers·slug·lineage 확장, ADR-0019·task#196)
│       ├── words.py         # /words/{book}, /words/{book}/verses (단어 분포, 오버레이 전용)
│       ├── verses.py        # /verse/{id}/persons (구절→인물, 색인만 구축·프론트 미사용)
│       └── reliance.py      # /person/{id}/reliance, /reliance/ranking (하나님 의존도, ADR-0023)
└── scripts/                 # 빌드타임 배치 (API 밖에서 실행)
    ├── __init__.py
    ├── load_*.py            # Neo4j에 노드/관계 MERGE 적재
    ├── inject_*.py          # 기존 노드에 속성 SET
    ├── generate_*.py        # data/ JSON 생성 (일부 Claude API 사용)
    ├── build_*.py           # 정본 JSON에서 파생 정본 산출 (build_word_distribution.py, build_verse_persons.py, build_word_verse_index.py)
    ├── validate_*.py        # 데이터 규칙 기계 검증 (validate_god_reliance.py, validate_person_context.py, validate_quotations.py 포함)
    ├── apply_event_dedupe.py# 중복 이벤트 실삭제 (ADR-0016)
    └── enrich_place_coords.py
```

핵심 파일 위치:

- 앱 진입/설정: `backend/app/main.py`, `backend/app/db.py`, `backend/app/overlays.py`.
- 라우터: `backend/app/routes/` 12개 모듈 (각각 자기 `APIRouter()` 인스턴스, `main.py`에서 include).
- 스크립트: `backend/scripts/` — 전량 `if __name__ == "__main__"` 진입점을 가지며, 그래프에 접근하는 것은 `NEO4J_URI`/`NEO4J_USER`/`NEO4J_PASSWORD` 환경변수를 읽는다. `build_word_distribution.py`·`build_word_verse_index.py`는 그래프 미접근(kiwipiepy venv 필요, 도큐스트링 참조). `build_verse_persons.py`는 그래프 미접근이지만 GitHub raw JSON을 네트워크 fetch한다. `validate_quotations.py`도 그래프 미접근(정본 절 사전 대조만, task#209).

## frontend/

```
frontend/
├── index.html               # HTML 진입 (src/main.jsx 로드)
├── package.json             # react 19 / react-dom / maplibre-gl / lucide-react, vite 8
├── vite.config.js           # @vitejs/plugin-react + manualChunks(maplibre/vendor) + define.__BUILD_ID__(빌드 타임스탬프)
├── eslint.config.js
├── .env.production          # VITE_API_URL=/api (프로덕션 빌드 주입)
├── public/                  # favicon.svg 등 정적 자산
│   └── fonts/               # 자체 호스팅 웹폰트 — im-fell-english-latin.woff2 + IM-Fell-English-OFL.txt (헤더 워드마크 전용, ADR-0026 리뉴얼)
├── dist/                    # 빌드 산출물 (gitignore, nginx가 마운트해 서빙)
├── node_modules/            # (gitignore)
└── src/
    ├── main.jsx             # 테마 동기 반영(localStorage biblemap-theme, ADR-0020) + createRoot/StrictMode
    ├── App.jsx              # SpineHeader + 스테이지 상태 머신 + 레이아웃 셸 (8 스테이지 렌더 분기 + 스테이지별 내비 바 + 무좌표 여정 분기 + 책 정경 순서 내비)
    ├── api.js               # apiGet() 단일 API 클라이언트 — 모든 요청에 ?v=__BUILD_ID__ 부착(캐시 무력화)
    ├── index.css            # CSS 변수/전역 스타일 — 듀얼 테마 토큰 두 벌 + 모션 토큰·keyframes·클래스(ADR-0024) + --z-verse/--scrim
    ├── theme.js             # TYPE_COLOR 등 색상 토큰 (값은 var(--type-*) 참조 — CSS 컨텍스트 전용)
    ├── constants.js         # 모바일 브레이크포인트, 시트 높이
    ├── dates.js             # 연대 표기 유틸
    ├── scrollMemory.js      # 목록 스테이지(hub·overview) 스크롤 위치 기억 — saveScroll/loadScroll (task#214)
    │
    ├── SpineHeader.jsx      # 책등 전역 헤더 — 리본 3부 + 테마 토글 + 브랜드 마크(CompassCrossMark), HEADER_H·RIBBON_OVERHANG export (ADR-0026, task#216·217)
    ├── PersonHub.jsx        # 인물 목차(대문) 뷰 (hub 스테이지) — 시대 8구간 장 섹션 + 인장 카드 + book-open 입장 + 스크롤 위치 복원(task#214)
    ├── BibleOverviewView.jsx# 성경 책 개요 (overview 스테이지) — 책 인장(BookSymbol) 카드 + 스크롤 위치 복원(task#214)
    ├── TourList.jsx         # 테마 투어 목록 (tours 스테이지) — description 2줄 미리보기(task#222)
    ├── TourIntro.jsx        # 투어 개요 뷰 (explore/intro, 투어 모드) — subtitle·description·정차지 조망 + 재생 CTA (task#222)
    ├── TourPlayback.jsx     # 투어 자동재생 — useTourPlayback 훅 + TourPlaybackCard 해설 카드 (task#223, ADR-0028)
    ├── MapView.jsx          # 지도 뷰 (maplibre-gl) — playbackIdx prop으로 재생 점진 경로선 구동
    ├── BookStageMap.jsx     # 책의 무대 미니맵 — 잠긴(비대화형) 소형 지도, SidePanel Book 섹션 전용 (task#207)
    ├── TimelineView.jsx     # 타임라인 뷰 — 8구간 시대 밴드 sticky 헤더 + 연속 레일 (task#200)
    ├── RelationsView.jsx    # 관계 뷰 — 유형 섹션·인장 카드·초점 쌍·타축 푸터 (task#198)
    ├── PersonIntro.jsx      # 인물 소개 뷰 (explore/intro) — 인장 히어로
    ├── FamilyTree.jsx       # 가계도 뷰 — 앵커+접힘·어머니 그룹·노드 3계층·메시아의 실, DOM 플로우 + 실측 SVG 커넥터 (task#195~197)
    ├── PersonMiniCard.jsx   # 가계도 노드 탭 바텀시트 — 즉시 렌더 + /node/{id} 지연 fetch (task#197)
    ├── personSymbols.jsx    # 인물 상징물 선화 50점(SYMBOLS) + PersonSymbol/hasSymbol (ADR-0025)
    ├── bookSymbols.jsx      # 책 상징물 선화 66권 + BookSymbol(bookId) — 인물 인장의 "책판" (ADR-0025, task#208)
    ├── tourSketches.jsx     # 투어 장면 스케치 집계·렌더 — SCENES 병합, hasSketch/TourSketchPanel (ADR-0029)
    ├── sketches/            # 투어당 1개 장면 레지스트리 모듈 (task#223~231) — 아래 별도 목록
    ├── WordDistributionView.jsx # 단어 분포 워드클라우드 (words 스테이지) — 자체 나선 배치 layoutCloud()
    ├── ChapterReader.jsx    # 본문 리더 (reader 스테이지) — 장 그리드(개요/묶음 헤더)↔장 본문, 프리베이크 절 사전만 소비 (task#205·206·212)
    ├── RelianceView.jsx     # 하나님 의존도 뷰 (explore/reliance 탭) — 도넛 게이지 + mode 막대 + 생애 궤적
    ├── JourneyList.jsx      # 여정 정차 리스트 — 인장 헤더 + mapless 전면 리스트 모드 (task#201)
    ├── SidePanel.jsx        # 공유 상세 패널 (book 스테이지 페이지로도 재사용) — Book 섹션에 인용 관계(pill 필터 + 대조 레이어, task#210) 포함
    ├── VerseLayer.jsx       # 양피지 구절 레이어 공통 쉘 — 모바일 시트/데스크톱 모달, VerseBookTabs·paperTextStyle export (task#202)
    ├── VerseLangTabs.jsx    # 절 본문 한/영 탭
    ├── Spinner.jsx
    │
    ├── mapLayers.js         # 지도 레이어 정의
    ├── mapGeo.js            # 지오메트리 유틸
    ├── mapRingController.js # 지도 링(경로) 제어
    │
    ├── useNodeSelection.js  # 노드 선택 훅
    ├── useStageNavigation.js# 스테이지/URL/히스토리 상태 머신 훅 (8 스테이지, explorePersonSlug·getPersonSlug 포함, 투어 진입 기본 뷰 'intro')
    └── urlState.js          # 해시 URL 직렬화/파싱 (encodeHash/parseHash)
```

`src/sketches/` — 투어 장면 스케치 레지스트리 모듈(ADR-0029). 파일명은 투어 id(케밥케이스)를 카멜케이스로 변환한 이름:

```
sketches/
├── lib.jsx                  # 공용 표준 정본 — 선 굵기 위계·전역 배율 W·sw()/d() 딜레이 헬퍼·Label 이름표
├── creationToFlood.jsx      # tours/creation-to-flood.json 대응
├── patriarchsCovenant.jsx   # tours/patriarchs-covenant.json 대응
├── exodusToConquest.jsx     # tours/exodus-to-conquest.json 대응
├── ageOfJudges.jsx          # tours/age-of-judges.json 대응
├── davidUnitedKingdom.jsx   # tours/david-united-kingdom.json 대응
├── elijahAndElisha.jsx      # tours/elijah-and-elisha.json 대응
├── exileAndReturn.jsx       # tours/exile-and-return.json 대응
├── gospelOfJesus.jsx        # tours/gospel-of-jesus.json 대응
└── theEarlyChurch.jsx       # tours/the-early-church.json 대응
```

## data/

원천·저작·오버레이 JSON을 엔티티/용도별 서브디렉터리로 분리한다. 단어 분포 정본 2개만 예외적으로 최상위 파일이다.

```
data/
├── authored_events/events.json        # 저작 사건 노드 (authored=true)
├── authored_persons/
│   ├── people.json                    #   저작 인물 노드 — ADR-0022 이관 후 엘리야·다니엘 2명만 잔존
│   ├── genealogy.json                 #   마태복음 1장 족보 사슬 (chain: [{id, nameKo, name, inserted?}], ADR-0019→0021)
│   └── mothers.json                   #   성경 명시 어머니-자식 보강 간선 2쌍 (ADR-0027, load_authored_mothers.py)
├── person_events/<slug>.json          # 큐레이션 인물별 여정 사건 (인물당 파일 1개, 35개)
├── verse_events/events.json           # 구절 기반 사건 노드
│
├── bible/verses.json                  # 정본 절 사전 (verseID(BBCCCVVV) → {textKo, textEn}, 런타임 오버레이) — 31,103절
├── event_dedupe/dedupe.json           # 중복 이벤트 삭제 대상 테이블 (apply_event_dedupe.py, ADR-0016)
│
├── word_distribution.json             # 책별(+"all") 단어 분포 정본 — build_word_distribution.py 산출, /words 서빙 (최상위 파일)
├── word_sentiment.json                # 단어 감정 극성 큐레이션 (word → positive|negative|neutral, 최상위 파일)
│
├── word_verse_index/index.json        # 단어(lemma)→[verseID] 역색인 — build_word_verse_index.py 산출, 현재 API 미사용(로더도 제거됨)
├── verse_persons/index.json           # verseID→[personRecId] 색인 — build_verse_persons.py 산출, verses.py가 서빙
│
├── person_slugs/seal_slugs.json       # 비큐레이션 인장 보유 인물 slug→theographic_id 정본 15명 (ADR-0025, family.py가 합성)
│
├── god_reliance/<slug>.json           # 인물별 하나님-상호작용 순간 배열 (32명, ADR-0023) — /person/{id}/reliance 서빙
│   └── AUTHORING.md                   #   mode 통제어휘·계기/행동/결과 스키마·사건 단위 원칙
│
├── keypeople/identity.json            # (책,이름) → {kind, id?} 정식 식별 데이터셋 (ADR-0018)
├── keypeople_verses/people.json       # 무id 이름 키 카드 (ADR-0017)
├── person_context/                    # by-id 인물 카드 — ADR-0027로 가계도 폐포 전원 ~1,060명 2단 저작
│   ├── people.json                    #   서사 인물: role+intro+verses / 족보 단역: role 한줄+verses (intro 없음)
│   └── AUTHORING.md
│
├── date_corrections/                  # 연대 교정 오버레이 (ADR-0014)
│   ├── events.json                    #   Event startDate/sortKey 교정 테이블
│   └── persons.json                   #   Person 필드 교정 테이블
│
├── names_ko/                          # 한글 이름 주입 소스 (books.json은 절 키 BB 순서·/words의 ref 조립에도 사용)
│   └── books.json  events.json  groups.json  people.json  places.json
│
├── book_context/books.json            # 권별 배경/주제/대표구절 (Book 속성 주입)
├── book_events/books.json             # {bookId:[eventId]} 추정책 연결 (런타임 오버레이)
├── book_years_approx/books.json       # 추정 연도 책 메타
├── chapter_summaries/books.json       # 장별 한줄 요약 + 대표절 (bookId → [{chapter, summary, keyVerseId}], 1,189장, 런타임 오버레이, task#206)
├── chapter_sections/books.json        # 장 묶음 (bookId → [{title, startChapter, endChapter}], 61권 — 단장권 부재, 런타임 오버레이, task#212)
├── quotations/quotations.json         # 구약↔신약 직접 인용 정본 302쌍 ({quotations:[{ntVerseIds, otVerseIds, ntRangeLabel, otRangeLabel, note?}]}, 런타임 오버레이, task#209)
├── event_verses/events.json           # 사건별 근거 구절 (런타임 오버레이) — task#203부터 다권(여러 책) 근거 확대
├── place_context/places.json          # 장소 배경/대표구절 (Place 속성 주입)
├── place_coords/places.json           # 장소 좌표 (Place 속성 주입)
│
├── character_traits/                  # 인물 성품 (Person traits 속성 주입)
│   ├── people.json
│   └── AUTHORING.md                   #   저작/분류 규칙 (validate_traits.py가 검증)
│
├── person_relations/                  # 관계 오버레이 (런타임) — /relations + family role 라벨
│   ├── relations.json
│   └── AUTHORING.md
│
└── tours/                             # 테마 투어 (event-reference 오버레이, ADR-0011). stops는 {id, note} 객체 배열(ADR-0028, note는 정차지 해설·nullable)
    ├── age-of-judges.json             # 투어당 파일 1개 (파일명 = tour id), 9개
    ├── creation-to-flood.json
    ├── david-united-kingdom.json
    ├── elijah-and-elisha.json
    ├── exile-and-return.json
    ├── exodus-to-conquest.json
    ├── gospel-of-jesus.json
    ├── patriarchs-covenant.json
    └── the-early-church.json
```

## 명명 규칙

### 데이터 파일

- **컬렉션형 오버레이**: `<entity_or_topic>/<collection>.json` 꼴. 컬렉션 파일명은 담는 엔티티 복수형(`events.json`, `people.json`, `places.json`, `books.json`, `groups.json`, `relations.json`, `verses.json`, `identity.json`, `dedupe.json`, `genealogy.json`, `mothers.json`, `index.json`, `seal_slugs.json`, `quotations.json`)이다. 예: `book_events/books.json`, `event_verses/events.json`, `bible/verses.json`, `chapter_summaries/books.json`, `person_slugs/seal_slugs.json`, `quotations/quotations.json`(디렉터리명과 파일명이 같은 유일한 예외 — 컬렉션이 "quotations" 자체). 예외: `data/word_distribution.json`·`data/word_sentiment.json`은 서브디렉터리 없이 최상위에 놓인 단일 파일이다.
- **엔티티별 분할 파일**: 인물 여정은 인물당 한 파일 `person_events/<slug>.json`(`david.json`, `moses.json` …). 하나님 의존도도 같은 패턴 `god_reliance/<slug>.json`(32명). 투어는 투어당 한 파일 `tours/<tour-id>.json`, 파일명 자체가 tour id다(`tours.py`가 파일명을 id로 사용).
- **AUTHORING.md**: 손으로 저작하는 디렉터리(`character_traits/`, `person_context/`, `person_relations/`, `god_reliance/`)에 저작·분류 규칙 문서를 동봉한다.
- **식별자**: 모든 노드의 조인 키는 `theographic_id`. 원본은 `recXXXX` 형태, 저작 노드는 `authored-*` 슬러그(예: `authored-place-bethlehem`, `authored-person-elijah`). 큐레이션 인물은 별도로 사람이 읽는 `slug`(`david`, `moses` …)를 가진다 — 정식 rec id는 `person_events/<slug>.json`의 `events[0].participants[0]` 규약으로 해석하며, 이 규약의 단일 구현이 `backend/app/overlays.py`의 `curated_person_id()`다(`persons.py`·`places.py`·`reliance.py` 공용, `load_theographic.py`만 자체 구현 — ADR-0022). 비큐레이션 인장 보유 인물 15명의 slug↔id는 `data/person_slugs/seal_slugs.json`이 정본이다(큐레이션 35인의 slug는 이 파일에 두지 않는다). 책은 slug 없이 `theographic_id`로 직접 키잉(`bookSymbols.jsx`의 `BookSymbol({bookId})`).
- **절 키**: `bible/verses.json`의 키는 `BBCCCVVV` 8자리 — `BB` = `names_ko/books.json` 키 순서(정경 66권)의 책 번호(1~66), `CCC` 장, `VVV` 절. `quotations.json`의 `ntVerseIds`/`otVerseIds`도 같은 키 규약을 쓴다.
- **한/영 필드 접미사**: 한글 값은 `nameKo`/`textKo`/`verseTextKo`/`keyVerseTextKo`, 영문은 접미사 없는 `name`/`title` 또는 `...En`/`textEn`.

### 스크립트 (동사 접두 규칙, 모두 `backend/scripts/`)

- `load_*` — Neo4j에 노드/관계를 `MERGE`로 신규 적재. 예: `load_theographic.py`(GitHub 원본 + 가족 폐포 wip, ADR-0021·0022), `load_books.py`(Book + CONTAINS_BOOK), `load_authored_events.py`, `load_authored_persons.py`, `load_authored_genealogy.py`(족보 사슬 + 자체 검증), `load_authored_mothers.py`(어머니-자식 보강 간선, 노드 신규 생성 없음 — ADR-0027), `load_person_events.py`, `load_verse_events.py`. `load_theographic.py` 재적재 후 `load_authored_genealogy.py`·`load_authored_mothers.py`·`inject_date_corrections.py`는 재실행 필수.
- `inject_*` — 이미 존재하는 노드에 속성만 `SET`. 예: `inject_ko_names.py`, `inject_date_corrections.py`, `inject_book_context.py`, `inject_place_context.py`, `inject_person_context.py`, `inject_person_traits.py`.
- `generate_*` — `data/` 아래 JSON을 생성(일부는 Claude API로 콘텐츠 생성, 일부는 theographic 원본 가공). 예: `generate_book_context.py`, `generate_book_context_enrich.py`, `generate_book_events.py`, `generate_bible_text.py`, `generate_event_verses.py`, `generate_person_context.py`, `generate_person_event_verses.py`, `generate_person_traits.py`, `generate_verse_events.py`, `generate_verse_text.py`, `generate_approx_book_verses.py`.
- `build_*` — 기존 정본 JSON에서 파생 정본을 산출(그래프 미접근). 예: `build_word_distribution.py`(`bible/verses.json` + `word_sentiment.json` → `word_distribution.json`, kiwipiepy 형태소 분석), `build_word_verse_index.py`(동일 토큰화 규약 재사용 → `word_verse_index/index.json` 역색인), `build_verse_persons.py`(theographic verses.json의 `people` 필드 투영 → `verse_persons/index.json`).
- `validate_*` — 데이터 규칙을 기계 검증. 예: `validate_event_chronology.py`, `validate_traits.py`, `validate_person_context.py`(ADR-0027 2단 계층 반영 — 최소 86명·role ≤80자·intro는 있을 때만 300자 검사), `validate_god_reliance.py`, `validate_quotations.py`(절 실존·측 위반·rangeLabel 자기일치·중복 쌍, task#209), `validate_chapter_sections.py`, `validate_chapter_summaries.py`.
- `apply_*` — 파괴적 정리 배치. 예: `apply_event_dedupe.py`(`data/event_dedupe/dedupe.json` 기반 중복 이벤트 실삭제).
- `enrich_*` — 기존 데이터 보강. 예: `enrich_place_coords.py`.

### 프론트엔드

- 컴포넌트: PascalCase `.jsx`(`SidePanel.jsx`, `FamilyTree.jsx`, `PersonIntro.jsx`, `SpineHeader.jsx`, `VerseLayer.jsx`, `PersonMiniCard.jsx`, `ChapterReader.jsx`, `BookStageMap.jsx`, `TourIntro.jsx`). 뷰 컴포넌트는 접미사 `View`(`MapView`, `TimelineView`, `RelationsView`, `BibleOverviewView`, `WordDistributionView`, `RelianceView`); `PersonHub`·`PersonIntro`·`FamilyTree`·`TourList`·`TourIntro`·`JourneyList`·`SidePanel`·`SpineHeader`·`VerseLayer`·`PersonMiniCard`·`ChapterReader`·`BookStageMap`은 예외 없이 전체화면/패널/쉘/미니맵 단위 컴포넌트다. `personSymbols.jsx`·`bookSymbols.jsx`·`tourSketches.jsx`는 컴포넌트(`PersonSymbol`/`BookSymbol`/`TourSketchPanel`)와 데이터(`SYMBOLS`/`SCENES`)를 함께 담는 카멜케이스 `.jsx` 예외다. `frontend/src/sketches/<tourId 카멜케이스>.jsx`(투어 id의 케밥케이스를 카멜케이스로 변환, 예: `age-of-judges` → `ageOfJudges.jsx`)는 투어별 장면 레지스트리 모듈 — 표준은 `sketches/lib.jsx`.
- 훅: `useXxx.js` 카멜케이스(`useNodeSelection.js`, `useStageNavigation.js`), 또는 컴포넌트 파일 내 export(`useTourPlayback` in `TourPlayback.jsx`).
- 비컴포넌트 모듈: 카멜케이스 `.js`(`api.js`, `theme.js`, `mapLayers.js`, `urlState.js`, `scrollMemory.js`).
- 스타일: 컴포넌트 인라인 스타일 + `index.css`의 CSS 변수(`var(--bg-1)`, `var(--gold)`, `var(--type-person)`, `var(--paper)`, `var(--z-verse)` 등) + 모션 클래스(`stage-in`, `modal-in`, `overlay-in`, `sheet-in`, `card-in`, `cloud-in`, `word-in`, `bar-reveal`, `stop-bar-in`, `symbol-draw`, `thread-draw`, `book-open`, `pressable` — ADR-0024~0026). 테마별 값은 `index.css`에서 다크(기본)와 `:root[data-theme='light']` 두 벌로 갈리고, `theme.js` 상수는 리터럴이 아닌 `var(...)` 참조다(ADR-0020). 양피지 토큰(`--paper*`)은 테마 불변 — 성경 구절 본문 전용. 모션 duration/easing은 `--dur-*`/`--ease-*` 토큰만 참조(하드코딩 금지). 별도 CSS 모듈/스타일 라이브러리 없음.
