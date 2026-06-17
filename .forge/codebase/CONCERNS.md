---
last_mapped_commit: 1003d7beae209835a39266883039d287158e9e92
mapped: 2026-06-18
---

# CONCERNS

기술 부채, 알려진 위험, 취약 지점을 모은 참조 문서. 도메인 용어 정의는 여기 없음(CONTEXT.md 소관). 구현 사실만 기록한다.

## 1. 대용량 생성 데이터가 git에 커밋됨

- `data/event_verses/events.json` — 약 2.0MB, **93,767줄**의 생성물이 git에 추적됨(`git ls-files data/event_verses/events.json` 확인). 사건별 근거 구절 오버레이 전체를 한 파일에 담음.
- 생성 출처: `backend/scripts/generate_event_verses.py`. Theographic GitHub raw(`events.json` + `~15MB verses.json`)를 받아 가공해 통째로 다시 만들 수 있음 → 사실상 캐시인데 git에 들어가 있음.
- 영향:
  - diff/리뷰 비현실적 — 재생성 시 통째로 바뀜. blame·머지 충돌 시 수동 해결 불가.
  - 저장소 히스토리 비대화(매 재생성마다 ~2MB 스냅샷 누적).
  - **번들에는 들어가지 않음**(프론트 번들과 무관). 백엔드가 디스크에서 읽어 서빙: `backend/app/routes/events.py:23-33`의 `_load_event_verses()`가 `functools.lru_cache(maxsize=1)`로 1회 로드 후 메모리 상주.
  - 파싱본(2MB)이 프로세스 메모리에 전량 상주. 단일 인스턴스 규모에선 무해하나 사실로 기록.
- 같은 패턴의 다른 추적 데이터(작지만 동일 성격): `data/book_context/books.json`(595줄, 44K), `data/names_ko/*.json`, `data/character_traits/people.json`(765줄, 32K), `data/book_years_approx/books.json`, `data/book_events/books.json`, `data/authored_events/events.json`.

## 2. 백엔드 hot-reload 아님 — 로컬 검증 마찰

- 컨테이너 `api`는 `uvicorn app.main:app`를 `--reload` 없이 실행(`backend/Dockerfile:6`). 코드를 바꿔도 자동 반영 안 됨.
- `docker-compose.yml:19-20`은 `./data:/app/data`만 볼륨 마운트하고 **`app/` 코드는 마운트하지 않음**(Dockerfile `COPY app/ ./app/`로 이미지에 구워짐). 즉 백엔드 코드 변경 반영에는 `docker compose up -d --build api`로 이미지 재빌드 필요(MEMORY.md에도 동일 경고).
- 반면 `data/`는 볼륨 마운트라 데이터 파일 교체는 컨테이너 재빌드 없이 반영됨(단 `lru_cache(maxsize=1)` 때문에 이미 로드된 오버레이는 프로세스가 살아있는 한 갱신 안 됨 — 데이터만 바꿔도 `api` 재시작 필요).

## 3. 테스트 전무

- 저장소 전체에 테스트 파일·러너 설정 없음(`*test*`/`*spec*` 검색 0건, `pytest.ini`/`conftest.py`/`vitest`/`jest` 설정 없음).
- CI(`.github/workflows/deploy.yml`)에 테스트·lint 단계 없음 — push 즉시 배포로 직행. 프론트는 `npm run lint`(eslint) 스크립트만 존재(`frontend/package.json:9`)하고 CI에서 호출되지 않음.
- 회귀 안전망 부재. 특히 데이터 재생성·Cypher 쿼리 변경의 검증이 수동.

## 4. 비밀/키 취급

- `.env`는 gitignore됨(`.gitignore:12`) — 추적 안 됨(확인: `git ls-files`에 `.env` 없음, `.env.example`만 추적). 양호.
- **`.env` 파일이 작업 트리에 평문 존재**. `NEO4J_PASSWORD` 보관용.
- `deploy.sh:30-32`가 `.env`를 `set -a; . "$WORKTREE/.env"`로 셸 환경에 로드 → 호스트에서 실행되는 inject 스크립트가 같은 비번을 쓰게 함. 비번이 호스트 프로세스 환경에 노출됨(self-hosted 러너 신뢰 전제).
- LLM 키: `backend/scripts/generate_book_context.py`·`generate_person_traits.py`가 `ANTHROPIC_API_KEY`를 환경변수에서만 읽음. 하드코딩 없음. 양호.
- Neo4j 비번 누락 시 명시적 실패: `backend/app/db.py:12-13`, `load_theographic.py:10-11`, `inject_ko_names.py:14`, `load_authored_events.py:14-15`. compose도 `${NEO4J_PASSWORD:?...}`로 미설정 시 기동 거부. 양호.

## 5. CORS 전면 개방

- `backend/app/main.py:25-31` — `allow_origins=["*"]`, `allow_methods=["GET"]`. 모든 출처에서 GET 허용. 인증 없는 읽기 전용 공개 API라 의도된 것으로 보이나, 오리진 화이트리스트 없음을 사실로 기록.

## 6. 하드코딩된 절대경로·호스트 종속 배포

- `deploy.sh:5` — 로그 경로 `/Users/calmonion/Library/Logs/com.biblemap.deploy.log` 하드코딩.
- `.github/workflows/deploy.yml:13` — `cd /Users/calmonion/Project/BibleMap` 하드코딩. `runs-on: self-hosted`(특정 머신 전제).
- 배포는 `git reset --hard origin/main`(`deploy.yml`) → 러너 작업 트리의 로컬 변경을 무조건 폐기. 로컬 미커밋 변경이 있으면 소실.
- 단일 머신·단일 사용자(`calmonion`) 환경에 강결합 — 이식성 없음.

## 7. 배포 시 데이터 주입 불완전

- `deploy.sh:49-63`은 `inject_ko_names.py`만 실행. 같은 종류의 주입 스크립트 `inject_book_context.py`, `inject_person_traits.py`는 배포 파이프라인에서 호출되지 않음(`backend/scripts/`에 존재).
- **`load_authored_events.py`도 배포·CI 파이프라인 밖**: `deploy.sh`·`.github/workflows/deploy.yml` 어디에도 호출 없음. 신규 환경/DB 리셋 후 저작 사건 7건이 Neo4j에 없는 상태로 기동될 수 있음.
- `load_theographic.py`(초기 그래프 적재)도 배포가 아닌 최초 1회 수동(`README.md`).
- 결과: 완전 초기 환경 재현에 필요한 수동 실행 순서가 README에만 있고 자동화되지 않음.

## 8. `load_authored_events.py` — 컨테이너 내부 실행 불가

- `backend/scripts/load_authored_events.py`는 `backend/Dockerfile`에 COPY되지 않음(Dockerfile은 `COPY app/ ./app/`만 수행). 컨테이너 안에서 직접 실행 불가.
- 호스트에서 `python3 backend/scripts/load_authored_events.py`로 실행해야 하며, `NEO4J_URI`가 `bolt://localhost:7687`을 기본값으로 갖고 있어 호스트→컨테이너 Neo4j 접근이 가능한 환경 전제(포트 7687이 expose된 경우만).
- `docker-compose.yml`의 `neo4j` 서비스는 `7687`을 호스트에 명시적으로 publish하지 않음(volumes에도 없음) → 호스트에서 `bolt://localhost:7687`로 접근 가능한지 여부는 compose 설정 상 명시 안 됨. MEMORY.md의 "Neo4j는 호스트에서 직접 쓰기 가능" 메모는 실운영 확인이지 코드 보장이 아님.

## 9. `authored_events/events.json` — `mappedBookIds` 미사용 필드

- `data/authored_events/events.json`의 각 사건에 `mappedBookIds` 배열이 있음. 이 필드를 읽는 코드가 없음(`backend/scripts/load_authored_events.py`, `backend/app/routes/*.py`, `frontend/src/*.jsx` 어디에도 없음).
- `book_events/books.json`(bookId → eventIds 매핑)과 `mappedBookIds`(eventId → bookIds 역매핑)는 같은 연결 정보를 중복 보관. `book_events/books.json`만 실제로 사용됨.
- 데이터 추가 시 두 파일을 수동으로 동기화해야 할 위험 — 현재는 7건이라 작지만, 저작 사건이 늘어날수록 동기화 실수 가능성 증가.

## 10. `authored-esther-persia-deliverance` — OCCURS_AT·HAS_PARTICIPANT 없음

- `data/authored_events/events.json`의 에스더 사건(`sortKey: -480`)은 `occursAt: []`, `participants: []`로 빈 배열 — Susa Place·Esther/Mordecai Person 노드가 Neo4j에 없어서 관계를 못 만들기 때문(파일 context 필드에 명시).
- Neo4j 그래프에 에스더 사건 노드는 존재하나 장소·인물 연결 없음 → SidePanel의 이웃 노드 탐색에서 에스더 사건은 고립(no OCCURS_AT, no HAS_PARTICIPANT). 향후 Susa/Esther/Mordecai 노드 추가 시 별도 `load_authored_events.py` 재실행 필요.

## 11. 외부 런타임 의존 — 가용성·차단 위험

- 프론트가 런타임에 직접 호출하는 외부 서비스(키 없음, 클라이언트에서 직접):
  - 지도 타일: ArcGIS `server.arcgisonline.com/.../NatGeo_World_Map/...`(`MapView.jsx:43`).
  - 글리프 폰트: `protomaps.github.io/basemaps-assets/fonts/...`(`MapView.jsx:38`).
- 이전에 있던 `getbible.js`의 런타임 GetBible API 호출은 ADR-0003에 의해 빌드타임 미리굽기(`generate_verse_text.py`)로 대체됨 — 런타임 의존 제거 완료.
- 지도 타일·글리프는 SLA·키·폴백 없음. 해당 서비스 다운 시 지도 배경과 라벨이 깨짐.

## 12. 응답 캐싱 정책

- `/events`, `/event/{id}/verses`, `/books`가 모두 `Cache-Control: no-store`(`events.py:64,73`, `books.py:92`) — 사실상 정적인 데이터인데 매 요청 DB/디스크 재조회. 성능 우선순위에 의한 의도적 선택이지만(데이터 갱신 즉시 반영), 변하지 않는 데이터에 캐시 헤더가 전혀 없어 불필요한 부하가 발생함.
- nginx는 정적 자산을 `immutable, max-age=1y`로, `/index.html`은 `no-store`로 분리 처리(`nginx/nginx.conf:20-28`) — 프론트 캐싱은 적절. API 캐싱만 위와 같이 없음.

## 13. 쿼리·로직상의 취약 지점

- **검색이 풀스캔**: `backend/app/routes/search.py:14-30`의 `MATCH (n) WHERE n.nameKo CONTAINS $q OR toLower(n.name) CONTAINS toLower($q)` — 라벨/인덱스 없는 전체 노드 스캔 + `CONTAINS`/`toLower`(인덱스 미사용). 생성되는 인덱스(`main.py:14-18`)는 `theographic_id` 단일 속성용이라 이 검색을 가속하지 못함. 그래프가 커지면 선형 저하. 풀텍스트 인덱스 없음.
- **이웃 잘림이 임의적**: `nodes.py:6-7`의 `MAX_NEIGHBORS_PER_TYPE=30`, `NODE_NEIGHBOR_LIMIT=50` 하드코딩. `get_node`의 `LIMIT 50`은 정렬 없는 잘림이라 어떤 50개가 올지 비결정적(`nodes.py:157`). `neighborTotal`(`nodes.py:177-181`)로 잘림 신호만 줌. `get_node_neighbors_grouped`도 타입별 30개 컷이 등장 순서 의존(`nodes.py:118-119`).
- **startup 인덱스 생성이 best-effort**: `main.py:9-21` lifespan에서 인덱스 생성 실패를 `except Exception`으로 삼키고 "인덱스 없이 계속 진행". DB 연결 불가/권한 문제를 조용히 넘겨, 인덱스 없는 상태로 운영될 수 있음(쿼리 성능 저하가 표면화 안 됨).
- **Person `traits` JSON 파싱 실패 무시**: `nodes.py:230-235` — `json.loads` 실패 시 `except Exception`으로 빈 배열 대체. 데이터 깨짐이 조용히 사라짐.
- 좌표 파싱 실패 시 장소 조용히 누락: `nodes.py:84-88`(`except (TypeError, ValueError): continue`).

## 14. 의존성 / 버전

- **`anthropic` 패키지가 어디에도 핀되지 않음**. `backend/scripts/generate_book_context.py`·`generate_person_traits.py`가 `import anthropic` 하지만 `backend/requirements.txt`에는 `fastapi`/`neo4j`/`uvicorn` 3개뿐. 데이터 생성 스크립트 실행 환경에 `anthropic`을 별도 수동 설치해야 함(재현성 부재).
- LLM 모델 ID 하드코딩: `claude-haiku-4-5-20251001`(`generate_book_context.py:57`, `generate_person_traits.py:59`). 모델 폐기 시 스크립트 수정 필요.
- neo4j 드라이버 `6.2.0`(requirements) — 메이저 버전 고정. 서버 이미지는 `neo4j:5`(`docker-compose.yml:3`, 마이너 태그 없음 → 5.x 최신을 따라감). 서버 태그가 부동(浮動)이라 재현성 약함.
- 프론트 의존성이 최신 메이저 대거 사용: React 19, vite 8, eslint 10, maplibre-gl 5(`frontend/package.json`). 빠른 메이저 추적은 잠재적 깨짐 위험.

## 15. 프론트엔드 복잡 영역(취약·검증 어려움)

- `frontend/src/MapView.jsx`(481줄) — 가장 복잡. requestAnimationFrame 기반 링 펼침/접힘 애니메이션, `AbortController` 다중, `moveend` 이벤트 + 700ms 폴백 타이머, ref 공유 상태 머신이 얽혀 있음(`MapView.jsx:108-153`, `404-444`). 주석이 과거 회고("task 15에서 어긋났던 지점", `MapView.jsx:408`)를 참조 — 경합/타이밍 버그가 반복 발생했던 영역. 테스트 없음(3번 참조) → 회귀 시 수동 검증만.
- 인라인 스타일 다수(`MapView.jsx`의 에러/안내 배너, 팝업 HTML 문자열 `setHTML` `MapView.jsx:287-304`) — 디자인 토큰(`theme.js`) 밖.
- `TimelineView.jsx`의 `verseView` 상태는 단일 사건만 열 수 있고, 그룹 팝업(`openGroup`)이 열린 상태에서 내부 사건의 📖 칩을 클릭하면 `verseView`는 열리나 팝업 닫힘 동작이 별도 처리 없음(`TimelineView.jsx:392-404`). 클릭 이벤트 전파 차단(`e.stopPropagation()`)이 일부 경로에서 중첩 처리됨.

## 우선순위 요약

- 높음: 검색 풀스캔 성능(13), 테스트 전무 + CI 게이트 없음(3), 배포 주입 불완전·`load_authored_events.py` 자동화 없음(7,8), `anthropic` 미핀(14).
- 중간: 대용량 생성물 git 커밋(1), 하드코딩 호스트 종속 배포(6), 외부 런타임 의존 폴백 부재(11), 인덱스 생성 best-effort 무음 실패(13), `mappedBookIds` 중복/미사용(9).
- 낮음/사실 기록: 백엔드 hot-reload 부재(2), CORS 개방(5), API no-store 캐싱(12), MapView 복잡도(15), 에스더 사건 고립(10).
