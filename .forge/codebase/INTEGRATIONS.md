---
last_mapped_commit: 14e0a78c3e0ab7fc7d960c4cabdf3eab3fc297e6
mapped: 2026-06-27
---

# INTEGRATIONS

BibleMap의 외부 연동은 두 시점으로 나뉜다. **런타임**(앱 서비스 중)에는 Neo4j와 지도 타일/폰트 외부 호스트만 접근하고, **빌드타임/데이터 적재**(`backend/scripts/*.py` 실행 시)에는 Theographic GitHub 원본, getbible.net, Anthropic API를 호출한다.

## Database — Neo4j (Bolt)

- 드라이버: `neo4j` Python 패키지(`neo4j==6.2.0`). 연결 코드 `backend/app/db.py`의 `GraphDatabase.driver(uri, auth=(user, password))`.
- 접속 정보(환경변수): `NEO4J_URI`(기본 `bolt://localhost:7687`; compose에선 `bolt://neo4j:7687`), `NEO4J_USER`(기본 `neo4j`), `NEO4J_PASSWORD`(필수, 없으면 `RuntimeError`).
- 컨테이너: `neo4j:5` 이미지(`docker-compose.yml`). bolt(7687)·HTTP(7474)는 `127.0.0.1`에만 바인딩. 인증은 `NEO4J_AUTH=neo4j/${NEO4J_PASSWORD}`.
- 부팅 시 `backend/app/main.py` lifespan이 라벨별 `theographic_id` 인덱스를 생성. 노드 식별자는 전반에 걸쳐 `theographic_id` 속성으로 매칭(`MATCH/MERGE (n {theographic_id: ...})`).
- 데이터 적재 스크립트들도 동일 드라이버로 호스트의 Neo4j에 직접 쓴다(`backend/scripts/load_*.py`, `inject_*.py`, `enrich_place_coords.py`).

## Map Tiles & Glyphs (런타임, 프론트)

지도는 MapLibre GL(`maplibre-gl`)로 그리며 `frontend/src/MapView.jsx`의 style 정의에서 외부 호스트를 직접 참조한다(API 키 없음).

- **ESRI 래스터 타일**: `https://server.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}` (`tileSize: 256`, source id `esri`). 베이스맵.
- **Protomaps 글리프(폰트)**: `https://protomaps.github.io/basemaps-assets/fonts/{fontstack}/{range}.pbf`. 라벨 폰트(`Noto Sans Regular`)는 `frontend/src/mapLayers.js`의 symbol 레이어에서 사용.

## Theographic Bible Metadata (빌드타임)

GitHub raw에서 원본 JSON을 받아 Neo4j에 적재하거나 오버레이 생성 입력으로 사용. 베이스 URL은 `https://raw.githubusercontent.com/robertrouse/theographic-bible-metadata/master/json/...`.

- `backend/scripts/load_theographic.py`: `people.json`, `places.json`, `events.json`, `peopleGroups.json` 등을 받아 노드·관계 MERGE.
- `backend/scripts/generate_event_verses.py`, `generate_verse_events.py`: `events.json`, `verses.json` 사용.
- `backend/scripts/generate_book_context.py`: `books.json`(`BOOKS_URL`) 사용.

## getbible.net — 절 본문 (빌드타임, 미리굽기)

- 엔드포인트: `https://api.getbible.net/v2/{slug}/{book_order}/{chapter}.json` (`slug`은 번역 슬러그; 영어 기본 `kjv`, 한국어 `korean`).
- 사용처: `backend/scripts/generate_verse_text.py`(한국어+영어 본문을 받아 데이터 파일에 인라인 저장), `backend/scripts/generate_person_event_verses.py`.
- ADR-0003에 따라 절 본문은 **빌드타임에 미리 받아 저장**하고, 앱 런타임에는 getbible를 호출하지 않는다(`frontend/src/SidePanel.jsx`/`VerseLangTabs.jsx`는 미리저장된 `keyVerseTextKo/En` 등을 `verseLang`으로 선택만 함).
- 주의: getbible는 기본 `Python-urllib` UA에 403을 반환하므로 스크립트가 브라우저류 User-Agent로 요청(`generate_verse_text.py` 주석, retro 2026-06-15 교훈).

## Anthropic API — Claude (빌드타임, 콘텐츠 생성)

- SDK: `anthropic` Python 패키지(`import anthropic`, `anthropic.Anthropic(api_key=...)`). **런타임 이미지(`backend/requirements.txt`)에는 포함되지 않는 빌드타임 전용 의존성**으로, 스크립트 실행 환경에 별도 설치 필요.
- 인증: `ANTHROPIC_API_KEY` 환경변수(미설정 시 `RuntimeError`). 값은 커밋되지 않음.
- 모델: `claude-haiku-4-5-20251001`.
- 사용 스크립트: `backend/scripts/generate_book_events.py`, `generate_book_context.py`, `generate_person_traits.py`, `generate_verse_events.py`. (성경 권별 배경·주제, 추정연도-사건 연결, 인물 특질, 절-사건 매핑 등 오버레이/속성 생성에 사용.)

## Auth / Webhooks

- **인증 없음**: 백엔드 API는 인증 미들웨어가 없고 CORS는 GET 전반 허용(`backend/app/main.py`, `allow_origins=["*"]`). API 자체는 호스트에 미노출이고 nginx(`8080`)를 통해서만 접근(`docker-compose.yml`, `nginx/nginx.conf`).
- **웹훅 없음**: 인바운드 웹훅 엔드포인트는 없다. 유일한 자동화 트리거는 `main` 브랜치 push에 반응하는 GitHub Actions 워크플로우 `.github/workflows/deploy.yml`(self-hosted 러너에서 `deploy.sh` 실행).
