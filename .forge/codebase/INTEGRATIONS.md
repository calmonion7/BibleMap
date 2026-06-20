---
last_mapped_commit: 7522aafe2088e83e8c4bed86a4f0269082db07e0
mapped: 2026-06-20
---

# External Integrations

## 데이터베이스

**Neo4j 5.x (그래프 데이터베이스):**
- 역할: 성경 인물·장소·사건·민족·성경책 노드와 관계(HAS_PARTICIPANT, LOCATED_AT, CONTAINS_BOOK 등)를 저장하는 주 데이터스토어.
- 클라이언트: `neo4j` Python SDK 6.2.0 (`backend/requirements.txt`).
- 연결 설정: `backend/app/db.py`의 `get_driver()` — 모듈 레벨 싱글턴 `_driver`.
- 연결 프로토콜: Bolt (`bolt://neo4j:7687` — Docker 네트워크 내부).
- 환경변수: `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`.
- 로컬 개발: `docker-compose.yml`의 `neo4j` 서비스, 포트 `127.0.0.1:7687`(Bolt), `127.0.0.1:7474`(브라우저) 로컬호스트 한정 바인딩.
- 인덱스: 앱 시작 시 `lifespan` 핸들러(`backend/app/main.py`)가 `Person`, `Place`, `Event`, `PeopleGroup`, `Book` 노드의 `theographic_id` 필드에 인덱스를 자동 생성.

## 지도 타일 서비스

**ESRI NatGeo World Map (퍼블릭 타일 API):**
- 역할: MapLibre GL 지도의 래스터 베이스맵 타일 제공.
- URL: `https://server.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}`
- 인증: 없음 (퍼블릭 엔드포인트).
- 구현: `frontend/src/MapView.jsx`의 `maplibregl.Map()` 초기화 시 `style.sources.esri.tiles` 배열.
- API 키 불필요 — 런타임에 브라우저가 직접 호출.

## Anthropic Claude API (데이터 생성 스크립트 전용)

**용도:** 오프라인 데이터 생성. 런타임 앱 서버에서는 호출하지 않음.
- SDK: `anthropic` Python 패키지 (버전 `requirements.txt` 미기재, 스크립트 환경에 별도 설치).
- 인증: `ANTHROPIC_API_KEY` 환경변수.
- 모델: `claude-haiku-4-5-20251001` (모든 생성 스크립트 공통).

**사용 스크립트:**

| 스크립트 | 출력 | 역할 |
|----------|------|------|
| `backend/scripts/generate_book_events.py` | `data/book_events/books.json` | 추정연도 성경책을 타임라인 이벤트에 의미적으로 연결 |
| `backend/scripts/generate_book_context.py` | `data/book_context/books.json` | 각 성경책 요약·핵심 절 생성 |
| `backend/scripts/generate_person_traits.py` | `data/character_traits/people.json` | 주요 인물 특성·성격 정보 생성 |
| `backend/scripts/generate_verse_events.py` | `data/verse_events/` | 절 → 이벤트 역방향 매핑 생성 |

> ADR-0006(`/.forge/adr/0006-data-generation-llm-direct-not-script.md`): 데이터 생성은 LLM 직접 호출 방식 채택.

## GetBible API (데이터 생성 스크립트 전용)

**용도:** 성경 절 본문(한국어·영어)을 빌드타임에 미리 받아 JSON에 인라인 저장. 런타임에는 호출하지 않음 (ADR-0003).
- 엔드포인트: `https://api.getbible.net/v2/{slug}/{book_order}/{chapter}.json`
- 인증: 없음 (퍼블릭).
- 번역 슬러그: `korean` (한국어), `kjv` (영어 KJV).
- 구현: `backend/scripts/generate_verse_text.py`, `backend/scripts/generate_person_event_verses.py`.
- 주의: 기본 Python urllib User-Agent에 403 응답 → 브라우저 UA 사용 필요 (`generate_verse_text.py` 참고).

## Theographic Bible Metadata (데이터 로딩 스크립트 전용)

**용도:** 성경 인물·장소·사건·민족 원본 데이터를 GitHub Raw에서 받아 Neo4j에 로드.
- 출처: `https://raw.githubusercontent.com/robertrouse/theographic-bible-metadata/master/json/`
- 파일: `people.json`, `places.json`, `events.json`, `peopleGroups.json`.
- 인증: 없음 (퍼블릭 GitHub Raw).
- 구현: `backend/scripts/load_theographic.py` — 배치 노드/관계 삽입.

## CI/CD 및 배포

**GitHub Actions:**
- 워크플로우: `.github/workflows/deploy.yml`.
- 트리거: `main` 브랜치 push.
- 실행 환경: `runs-on: self-hosted` — 로컬 macOS 머신(프로덕션 서버 겸용).
- 동작: `git reset --hard origin/main` 후 `deploy.sh` 실행.

**배포 스크립트 (`deploy.sh`):**
1. `npm install && npm run build` (프론트엔드)
2. `docker compose build api`
3. `docker compose up -d api nginx`
4. `python3 backend/scripts/inject_ko_names.py` (Neo4j 한글 이름 주입, 최대 15회 재시도)

## 인증 / 보안

- 사용자 인증 없음. 앱은 읽기 전용 공개 서비스.
- CORS: `allow_origins=["*"]`, `allow_methods=["GET"]` (`backend/app/main.py`).
- Neo4j 포트는 `127.0.0.1` 바인딩으로 외부 직접 접근 차단.
- API 서버는 Docker 네트워크 내부에서만 접근 가능 (nginx `/api/` 프록시 경유).

## 파일 스토리지

- 외부 파일 스토리지 없음.
- `data/` 디렉터리의 JSON 오버레이 파일이 git 저장소에 커밋되어 `./data:/app/data` 바인드 마운트로 컨테이너에 제공.

## 모니터링 / 로깅

- 외부 모니터링 서비스 없음.
- 배포 로그: `/Users/calmonion/Library/Logs/com.biblemap.deploy.log` (`deploy.sh`).
- 앱 로그: `logging.exception()` → uvicorn 표준 출력 (Docker 로그).

---

*Integration audit: 2026-06-20*
