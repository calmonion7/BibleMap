---
last_mapped_commit: 06b4012804c00a45ea7dfda9761d014ac91b11fb
mapped: 2026-06-20
---

# BibleMap 외부 연동

## 1. Neo4j (그래프 데이터베이스)

### 연결 정보
- **드라이버**: `neo4j==6.2.0` (Python 공식 드라이버)
- **프로토콜**: Bolt (`bolt://`)
- **기본 URI**: `bolt://localhost:7687` (로컬), `bolt://neo4j:7687` (Docker 내부)
- **인증**: 사용자명/비밀번호 (`NEO4J_USER` / `NEO4J_PASSWORD`)
- **연결 관리**: 싱글턴 드라이버 패턴 (`backend/app/db.py` → `get_driver()`)

### 사용 위치
- **앱 런타임** (`backend/app/routes/`): 모든 API 라우터가 `get_driver()`를 통해 세션 생성
  - `nodes.py` — `GET /node/{id}`, `/node/{id}/places`, `/node/{id}/neighbors/grouped`, `/person/{id}/event-ids`
  - `events.py` — `GET /events`, `/event/{id}/verses` (lru_cache로 1회 쿼리 후 메모리 유지)
  - `search.py` — `GET /search`
  - `books.py` — `GET /books`
- **데이터 파이프라인 스크립트** (`backend/scripts/`): 직접 `GraphDatabase.driver()` 생성
  - `load_theographic.py`, `load_books.py`, `load_authored_events.py`, `load_verse_events.py`, `inject_ko_names.py`, `inject_person_traits.py`, `inject_book_context.py`
  - `generate_book_events.py` — 스크립트 중 Neo4j 조회 + Claude API 조합

### 노드 레이블 및 주요 관계
앱이 실제로 쿼리하는 레이블: `Person`, `Place`, `Event`, `PeopleGroup`, `Book`

관계 유형:
- `HAS_PARTICIPANT` (Event → Person)
- `OCCURS_AT` (Event → Place)
- `CONTAINS_BOOK` (Book → Event)
- `MEMBER_OF` (Person → PeopleGroup)
- `PARENT_OF` / `CHILD_OF` (Person ↔ Person)
- `SIBLING_OF`, `PARTNER_OF` (Person ↔ Person)
- `PART_OF` (Event → Event)

### 인덱스
앱 시작 시 `lifespan`에서 자동 생성 (`backend/app/main.py`):
- `person_tid`, `place_tid`, `event_tid`, `pg_tid`, `book_tid` — 각 레이블의 `theographic_id` 속성

---

## 2. Theographic Bible Metadata (GitHub Raw)

데이터 파이프라인 스크립트가 빌드타임에 호출하는 공개 GitHub 원시 JSON 엔드포인트.

| 스크립트 | URL |
|---------|-----|
| `load_theographic.py` | `https://raw.githubusercontent.com/robertrouse/theographic-bible-metadata/master/json/people.json` |
| `load_theographic.py` | `https://raw.githubusercontent.com/robertrouse/theographic-bible-metadata/master/json/places.json` |
| `load_theographic.py` | `https://raw.githubusercontent.com/robertrouse/theographic-bible-metadata/master/json/events.json` |
| `load_theographic.py` | `https://raw.githubusercontent.com/robertrouse/theographic-bible-metadata/master/json/peopleGroups.json` |
| `load_books.py` | `.../books.json`, `.../events.json` |
| `generate_book_context.py` | `.../books.json` |
| `generate_person_traits.py` | `.../people.json`, `.../events.json` |
| `generate_verse_events.py` | `.../books.json`, `.../events.json`, `.../verses.json` |

호출 방식: `urllib.request.urlopen()` (표준 라이브러리). 런타임에는 호출 없음.

---

## 3. Anthropic Claude API (데이터 생성 전용)

### 연결 정보
- **SDK**: `anthropic` Python 패키지 (requirements.txt 미포함 — 스크립트 전용 설치)
- **모델**: `claude-haiku-4-5-20251001` (4개 스크립트 공통)
- **인증**: `ANTHROPIC_API_KEY` 환경변수

### 사용 스크립트
| 스크립트 | 출력 | 용도 |
|---------|------|------|
| `backend/scripts/generate_book_context.py` | `data/book_context/books.json` | 권별 시대 배경·주제·대표 구절 |
| `backend/scripts/generate_person_traits.py` | `data/character_traits/people.json` | 인물별 성품·근거 구절 |
| `backend/scripts/generate_book_events.py` | `data/book_events/books.json` | 추정연도 책 → 연결 사건 매핑 |
| `backend/scripts/generate_verse_events.py` | `data/verse_events/events.json` | 고아 구절에서 사건 도출 |

모두 빌드타임 1회성 실행 스크립트. 앱 런타임에는 Claude API 호출 없음.

---

## 4. GetBible API (구절 본문 prebake 전용)

### 연결 정보
- **베이스 URL**: `https://api.getbible.net/v2/`
- **엔드포인트 패턴**: `/{translation_slug}/{book_order}/{chapter}.json`
- **번역 슬러그**: `korean` (한국어), `kjv` (영어)
- **User-Agent**: `Mozilla/5.0 (compatible; BibleMap-build/1.0)` (기본 Python UA는 403 반환)
- **호출 방식**: `urllib.request.urlopen()`, 타임아웃 30초, 장(chapter) 단위 캐시

### 사용 스크립트
- `backend/scripts/generate_verse_text.py` — `data/event_verses/events.json`, `data/book_context/books.json`, `data/character_traits/people.json`에 구절 본문(`textKo`/`textEn`)을 인라인 저장 (ADR-0003)

앱 런타임에는 GetBible API 호출 없음. 본문은 JSON 파일에 prebake되어 제공된다.

---

## 5. 데이터 파이프라인 스크립트 실행 순서

```
# 1. Theographic 원본 데이터 로드
python3 backend/scripts/load_theographic.py
python3 backend/scripts/load_books.py

# 2. 한국어 이름 주입
python3 backend/scripts/inject_ko_names.py

# 3. LLM 생성 데이터 (ANTHROPIC_API_KEY 필요)
python3 backend/scripts/generate_book_context.py
python3 backend/scripts/generate_person_traits.py
python3 backend/scripts/generate_book_events.py
python3 backend/scripts/generate_verse_events.py

# 4. 구절 본문 prebake (getbible API)
python3 backend/scripts/generate_verse_text.py

# 5. 추정 연도 책 구절 구조 생성
python3 backend/scripts/generate_approx_book_verses.py

# 6. LLM 생성 데이터 Neo4j 주입
python3 backend/scripts/inject_book_context.py
python3 backend/scripts/inject_person_traits.py
python3 backend/scripts/load_authored_events.py
python3 backend/scripts/load_verse_events.py
```

---

## 6. 런타임 API 엔드포인트 요약

앱 런타임에 외부 호출은 없음. 백엔드가 노출하는 내부 API:

| 메서드 | 경로 | 캐시 |
|--------|------|------|
| GET | `/events` | `Cache-Control: max-age=300` |
| GET | `/event/{event_id}/verses` | `Cache-Control: max-age=300` |
| GET | `/books` | `Cache-Control: no-store` |
| GET | `/node/{node_id}` | — |
| GET | `/node/{node_id}/places` | — |
| GET | `/node/{node_id}/neighbors/grouped` | — |
| GET | `/person/{node_id}/event-ids` | — |
| GET | `/search?q=` | — |

프론트엔드는 `frontend/src/api.js`의 `apiGet()` 헬퍼를 통해 단일 베이스 URL(`VITE_API_URL`)로 접근.
프로덕션에서는 nginx가 `/api/` → `http://api:8000/`으로 프록시.
