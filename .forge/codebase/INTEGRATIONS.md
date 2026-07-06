---
last_mapped_commit: 95ba754e0a5b8a8db6f537f88d6d4e60d302d066
mapped: 2026-07-06
---

# External Integrations

## 데이터베이스 — Neo4j

**서비스:** `docker-compose.yml` 서비스 `neo4j`, 이미지 `neo4j:5`.

**포트 바인딩:** `127.0.0.1:7474`(HTTP 브라우저), `127.0.0.1:7687`(Bolt) — 로컬호스트 전용.

**Driver:** Python `neo4j` 6.2.0. `backend/app/db.py`의 모듈 전역 싱글턴 `_driver = GraphDatabase.driver(uri, auth=(user, password))`.

**연결 환경변수:**
- `NEO4J_URI` — compose 내부: `bolt://neo4j:7687`; 로컬 기본: `bolt://localhost:7687`
- `NEO4J_USER` — 기본 `neo4j`
- `NEO4J_PASSWORD` — 필수. compose가 `NEO4J_AUTH=neo4j/${NEO4J_PASSWORD}`로 자동 조립

**세션 패턴:** 라우트마다 `with driver.session() as session: session.run(<cypher>, ...)`. APOC 미사용.

**인덱스:** 앱 시작 `lifespan`에서 Person/Place/Event/PeopleGroup/Book의 `theographic_id`에 `CREATE INDEX {label}_tid IF NOT EXISTS` (`backend/app/main.py`).

**볼륨:** named volume `neo4j_data:/data` (영속).

## 외부 API — Theographic Bible Metadata (빌드타임)

`backend/scripts/load_theographic.py`가 아래 4개 URL을 `urllib`로 HTTP GET한다.

```
https://raw.githubusercontent.com/robertrouse/theographic-bible-metadata/master/json/people.json
https://raw.githubusercontent.com/robertrouse/theographic-bible-metadata/master/json/places.json
https://raw.githubusercontent.com/robertrouse/theographic-bible-metadata/master/json/events.json
https://raw.githubusercontent.com/robertrouse/theographic-bible-metadata/master/json/peopleGroups.json
```

인증 없음. Neo4j 그래프의 원본 데이터. 배치 삽입: 노드 500개 / 관계 1000개 per transaction. **런타임 호출 없음.**

## 외부 API — getbible v2 (빌드타임 prebake)

`backend/scripts/generate_verse_text.py` 및 `generate_person_event_verses.py`가 아래 패턴 URL로 절 본문을 fetch한다.

```
https://api.getbible.net/v2/{slug}/{book_order}/{chapter}.json
```

슬러그: `korean`(한국어), `kjv`(영어). 대상 파일: `data/event_verses/events.json`, `data/book_context/books.json`, `data/character_traits/people.json`, `data/place_context/places.json`. 이미 text가 있는 항목은 건너뜀(멱등). 결과는 JSON에 인라인 저장 → **런타임에 getbible 호출 없음.**

## 외부 API — Anthropic Claude (빌드타임 데이터 생성)

`backend/scripts/generate_book_context.py`, `generate_person_traits.py`, `generate_book_events.py`, `generate_verse_events.py` 등이 `anthropic` Python SDK를 사용한다.

- 모델: `claude-haiku-4-5-20251001`
- 인증: `ANTHROPIC_API_KEY` 환경변수. 미설정 시 `RuntimeError`.
- 산출물은 `data/` 하위 JSON으로 저장·커밋. 앱은 생성된 JSON만 소비. **런타임 LLM 호출 없음.**

## 지도 타일·폰트 (프론트엔드 런타임 — 클라이언트 직접 호출)

`frontend/src/MapView.jsx`에서 maplibre-gl이 두 외부 서버에 클라이언트 브라우저 직접 요청을 보낸다.

- **ESRI 래스터 타일:** `https://server.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}` — maplibre `raster` source `esri`. 인증 없음.
- **Protomaps 글리프(폰트):** `https://protomaps.github.io/basemaps-assets/fonts/{fontstack}/{range}.pbf` — maplibre glyphs. 인증 없음.

백엔드 서버를 거치지 않는다.

## nginx /api 프록시

`nginx/nginx.conf` `location /api/` 블록:

```
proxy_pass http://api:8000/;
proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto $scheme;
```

path에서 `/api/` prefix를 strip하여 api 컨테이너의 `/` 경로로 전달. 프론트엔드 `VITE_API_URL=/api`가 이 경로를 베이스로 사용 (`frontend/src/api.js`).

## CI/CD — GitHub Push → Self-hosted Runner 자동 배포

`.github/workflows/deploy.yml`: `main` 브랜치 push 이벤트 시 GitHub이 self-hosted 러너에 job을 전달한다. 러너는 로컬 머신에서 실행되며:

1. `git fetch origin`
2. `git reset --hard origin/main`
3. `bash deploy.sh`

`deploy.sh`는 `/tmp/biblemap-deploy.lock`으로 동시 실행을 방지하고, macOS 키체인 우회를 위해 임시 `DOCKER_CONFIG`를 생성한 뒤 프론트 빌드 → api 컨테이너 재빌드 → `up -d` → `inject_ko_names.py` 주입 순서로 실행한다. 배포 로그: `/Users/calmonion/Library/Logs/com.biblemap.deploy.log`.

러너 부재 시 job은 `queued`→24h `cancelled`로 무음 소멸한다 (전역 CLAUDE.md 참조).

## 오버레이 JSON (런타임 파일 서빙)

Neo4j에 저장하지 않는 추정·큐레이션 데이터는 `backend/app/overlays.py`가 `data/` 하위 JSON 파일로 직접 서빙한다. `DATA_DIR` 환경변수(기본 `/app/data`) 경로를 사용하며, compose가 `./data:/app/data`로 마운트한다 (`docker-compose.yml`).

캐시: `functools.lru_cache` — 프로세스 수명 동안 1회만 파일 읽기.

## 인증

사용자 인증 없음. 공개 읽기 전용. CORS: `allow_origins=["*"]`, `allow_credentials=False`, `allow_methods=["GET"]` (`backend/app/main.py`).

서비스 자격증명: Neo4j (`NEO4J_PASSWORD`), Anthropic (`ANTHROPIC_API_KEY`, 빌드타임 전용). 루트 `.env`에 보관(git 미추적), `deploy.sh`가 `set -a; . .env; set +a`로 로드.

## 모니터링·로깅

외부 트래킹 서비스 없음. 표준 Python `logging` 사용 (`backend/app/main.py`의 인덱스 생성 실패 시 `logging.exception`). uvicorn stdout + 배포 로그 파일이 전부.

## Webhooks

**수신:** GitHub push webhook이 Actions 워크플로를 트리거 (GitHub 관리형). 앱 자체 수신 webhook 엔드포인트 없음.

**발신:** 런타임 없음. 빌드타임 스크립트만 외부 아웃바운드 호출.
