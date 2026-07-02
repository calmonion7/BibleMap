---
last_mapped_commit: 99d42c8518af00f3e0bf4a4ba90f821d84cf42e5
mapped: 2026-07-02
---

# 외부 연동 (Integrations)

## 1. 데이터베이스 — Neo4j

### 연결 방식

`backend/app/db.py`의 싱글턴 드라이버:

- URI: 환경변수 `NEO4J_URI` (기본값 `bolt://localhost:7687`)
- 사용자: 환경변수 `NEO4J_USER` (기본값 `neo4j`)
- 비밀번호: 환경변수 `NEO4J_PASSWORD` (필수; 미설정 시 `RuntimeError`)
- 드라이버: `neo4j` Python 패키지 v6.2.0, Bolt 프로토콜

### 포트 노출

`docker-compose.yml` 기준:

| 포트 | 바인딩 | 용도 |
|------|--------|------|
| 7687 | `127.0.0.1:7687` | Bolt (앱·스크립트 연결) |
| 7474 | `127.0.0.1:7474` | HTTP Browser UI |

컨테이너 내부에서 `api` 서비스는 `bolt://neo4j:7687`로 접속 (Docker 내부 DNS 사용).

### 스타트업 인덱스

`backend/app/main.py`의 `lifespan` 훅에서 기동 시 자동 생성:
- `Person`, `Place`, `Event`, `PeopleGroup`, `Book` 5개 레이블 각각 `theographic_id` 속성에 `CREATE INDEX IF NOT EXISTS`

### 한글 이름 주입

배포마다 `backend/scripts/inject_ko_names.py`가 실행되어 `data/names_ko/`의 JSON 파일을 읽고 Neo4j `Person`·`Place` 노드에 `nameKo`, `aliasesKo` 속성을 `SET`한다.

---

## 2. Theographic Bible Metadata — 데이터 소스

빌드타임 스크립트 여러 개가 동일 GitHub raw CDN에서 JSON을 직접 `urllib`/`requests`로 fetch한다.

베이스 URL: `https://raw.githubusercontent.com/robertrouse/theographic-bible-metadata/master/json/`

| 파일 | 사용 스크립트 |
|------|--------------|
| `people.json` | `load_theographic.py`, `generate_person_traits.py` |
| `places.json` | `load_theographic.py` |
| `events.json` | `load_theographic.py`, `load_books.py`, `generate_event_verses.py`, `generate_verse_events.py`, `generate_person_traits.py` |
| `peopleGroups.json` | `load_theographic.py` |
| `books.json` | `load_books.py`, `generate_book_context.py`, `generate_verse_events.py` |
| `verses.json` | `generate_event_verses.py`, `generate_verse_events.py` |

이 호출은 모두 **개발·데이터 파이프라인 전용**이며 런타임 API 요청 경로에는 포함되지 않는다.

---

## 3. getbible.net — 성경 본문 API (빌드타임 전용)

`backend/scripts/generate_verse_text.py`가 빌드타임에 구절 본문을 미리 굽기(pre-bake)한다.

- 엔드포인트 패턴: `https://api.getbible.net/v2/{slug}/{book_order}/{chapter}.json`
- 사용 번역:
  - `korean` — 한국어 개역
  - `kjv` — 영어 KJV
- 캐시 단위: `(slug, bookOrder, chapter)` 튜플 — 같은 장은 한 번만 fetch
- User-Agent: `Mozilla/5.0 (compatible; BibleMap-build/1.0)` (기본 `Python-urllib` UA에 403 응답, 브라우저류 UA 필요 — `retro 2026-06-15` 교훈)
- 결과 저장: `data/event_verses/events.json`, `data/book_context/books.json`, `data/character_traits/people.json`, `data/place_context/places.json`에 `textKo`/`textEn` 필드로 인라인 저장
- ADR-0003에 의해 런타임 호출 없음: 앱이 구절 본문을 표시할 때 위 JSON 파일에서 직접 읽는다.

---

## 4. 지도 타일 — Esri NatGeo (런타임 브라우저 요청)

`frontend/src/MapView.jsx`의 MapLibre GL 초기화:

- 타일 소스 유형: `raster`
- 타일 URL 패턴: `https://server.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}`
- `tileSize`: 256
- 제공사: Esri ArcGIS Online (NatGeo World Map 서비스) — 무료 공개 타일, 별도 API 키 없음

---

## 5. 지도 폰트 글리프 — Protomaps (런타임 브라우저 요청)

`frontend/src/MapView.jsx` MapLibre 스타일 설정:

- `glyphs`: `https://protomaps.github.io/basemaps-assets/fonts/{fontstack}/{range}.pbf`
- 제공사: Protomaps GitHub Pages CDN — 무료 공개, 별도 인증 없음
- 용도: 지도 레이블 렌더링용 PBF 폰트 글리프

---

## 6. GitHub Actions — CI/CD 파이프라인

`.github/workflows/deploy.yml`:

- 트리거: `main` 브랜치 push
- 실행 환경: `runs-on: self-hosted` (macOS 로컬 머신의 GitHub Actions 러너)
- 단계:
  1. 프로젝트 디렉터리(`/Users/calmonion/Project/BibleMap`)에서 `git fetch origin && git reset --hard origin/main`
  2. `bash deploy.sh` 실행 (빌드 → 컨테이너 재시작 → 한글 이름 주입)
- 웹훅, Secrets, 외부 Action 없음 — 순수 self-hosted 단순 배포 구조

---

## 7. 인증 / 인가

런타임 인증 레이어 없음. `backend/app/main.py`의 CORS 설정:
- `allow_origins=["*"]`
- `allow_credentials=False`
- `allow_methods=["GET"]` (읽기 전용 API)
