---
last_mapped_commit: 8af8f0563294387a7073d0b85e6f7de74b4b7b30
mapped: 2026-07-13
---

# TESTING

BibleMap이 정확성을 검증하는 방식. 이 프로젝트에는 **정식 유닛 테스트 프레임워크가 없다** — 검증은 (1) 데이터용 기계검증 스크립트, (2) 로더/inject의 자체 검증, (3) 화면 레벨 Playwright 검증, (4) 배포 게이트로 이뤄진다.

---

## 0. 정식 테스트 프레임워크 부재

- pytest·unittest·vitest·jest 없음. `*_test.py`·`*.test.jsx`·`*.spec.*`·`conftest.py` 파일 없음. 백엔드 `requirements.txt`는 `fastapi`/`neo4j`/`uvicorn`만, 프론트 `devDependencies`엔 테스트 러너가 없다.
- 프론트의 유일한 정적 게이트는 ESLint(`cd frontend && npm run lint`, flat config `frontend/eslint.config.js`, react-hooks 규칙 포함).
- 즉 "테스트를 돌린다"의 실체는 아래의 `validate_*` 스크립트 · 로더 자체검증 · Playwright 화면검증이다.

---

## 1. 기계검증 스크립트 (`backend/scripts/validate_*.py`)

데이터 저작이 규칙을 지키는지 확인하는 결정적 검증기. 공통 계약: 위반 목록을 `print`하고 위반이 있으면 `sys.exit(1)`, 없으면 `"... OK — 위반 0"`을 찍는다. **inject 전에 위반 0을 확인**하는 게이트로 쓴다.

- `validate_traits.py` — `data/character_traits/people.json`이 `AUTHORING.md`를 지키는지: ① 라벨이 통제 어휘(`VIRTUES` 24 · `FLAWS` 8) 안 ② 인물당 성품 2~5개·라벨 중복 없음 ③ `verse_ref` 정규식 형식(개역 약어 + 장:절[-절]) ④ 필드 결손. 통제 어휘 집합이 스크립트에 하드코딩돼 AUTHORING.md와 동기화 대상이다.
- `validate_event_chronology.py` — Neo4j를 읽어 연대 이상을 검출: (a) 인물 출생<활동<사망 서사 역전 (b) 사사 승계 순서 역전 (c) 대표 앵커 대비 역전 (d) 교정 창 내 rec 이벤트 목록화 (e) 형제군 고립 이탈(전치 오타 후보) + Person 스캔(사망<출생·수명>1000년). 신학적 참여 화이트리스트를 둔다. `--json PATH`로 구조화 리포트도 저장한다.
- `validate_person_context.py` — 인물 소개(`data/person_context`) 저작 규칙 검증.
- 실행: `python3 backend/scripts/validate_<name>.py` (Neo4j를 읽는 검증기는 `NEO4J_PASSWORD` 환경변수 필요, `.env`에서 로드).

---

## 2. 로더/inject 자체 검증

적재 스크립트는 적재 직후 스스로 결과를 검증하거나 안전장치를 둔다.

- `load_authored_genealogy.py` — 족보 사슬 적재 후 Cypher 도달성 검증: 사슬 끝(후손)에서 `CHILD_OF*`로 사슬 머리(조상)까지 연속인지 `EXISTS { ... }`로 확인하고, 끊겼으면 `raise SystemExit("FAIL: ... 사슬 단절")`.
- `inject_date_corrections.py` — 에코 필드 가드(CONVENTIONS §3.4): DB 현재값이 에코와 불일치하면 스킵+`[WARN]`, 이미 새 값이면 조용히 통과. 멱등·재실행 안전. 결과를 "적용/이미 적용/스킵" 건수로 방출한다.
- `inject_*.py` 공통 — 적재 후 `MATCH ... WHERE <속성> IS NOT NULL RETURN count(...)`로 반영 건수를 `print`하고, 일부는 대표 노드(예: `inject_book_context.py`의 Genesis background)를 샘플 출력해 육안 확인을 돕는다.

---

## 3. 로컬 검증 = 빌드 후 확인 (footgun)

로컬에서 변경을 눈으로 확인하려면 **빌드가 선행**돼야 한다. `docker-compose.yml`이 다음을 강제한다:

- 프론트: nginx가 `./frontend/dist:/usr/share/nginx/html:ro`를 마운트한다 — HMR이 아니라 빌드 산출물을 서빙한다. 프론트 변경 확인 전 반드시 `cd frontend && npm run build`(`.env.production`의 `VITE_API_URL=/api` 자동 적용). 소스만 고치고 빌드를 빼먹으면 `localhost:8080`은 옛 화면을 계속 보여준다.
- 백엔드 데이터: `api`가 `./data:/app/data`를 마운트하므로 오버레이 JSON 변경은 재빌드 없이 반영되지만, 백엔드가 `@functools.lru_cache`로 기동 시 메모리 캐시한다(CONVENTIONS §1.3) → **`docker compose restart api`로 캐시를 비워야** 신규 데이터가 보인다. `docker compose up -d api`는 config 무변경 시 컨테이너를 재생성하지 않아("Running") 옛 데이터를 계속 서빙한다.
- 백엔드 코드: 코드 변경은 이미지 재빌드 필요 — `docker compose up -d --build api`.
- 로컬 개발 서버(선택): README는 `python3 -m uvicorn backend.app.main:app --reload`(:8000)와 `npm run dev`(:5173)도 안내하나, 배포본과 동형으로 확인하려면 위의 dist 마운트 경로(:8080)를 쓴다.

---

## 4. Playwright 화면 테스트

UI 동작 검증은 Python Playwright로 한다(`/opt/homebrew`에 설치). 패턴: 네트워크 캡처 + 스크린샷으로 `localhost:8080`(또는 프로덕션 도메인)을 렌더 확인하고 **콘솔/네트워크 에러 0**을 확인한다. 프로덕션은 API `:8000`이 미노출이라 nginx `/api` 프록시를 거친다 — 검증도 `:8080` 기준.

- 저작 검증 흐름 예(`data/person_relations/AUTHORING.md` §8): `/api/persons/curated`로 node_id 확보 → `/api/person/{node_id}/relations`가 국면을 반환하는지 확인 → Playwright로 화면 렌더 확인.
- 디자인/레이아웃 지적은 대개 실폰(배포본) 기준이므로 뷰포트를 먼저 확정하고 Playwright 시나리오에 모바일 폭을 포함한다(MEMORY 교훈).

---

## 5. 저작 → 검증 파이프라인 (정본 순서)

`data/person_relations/AUTHORING.md` §8이 정리한, 저작 후 반드시 밟는 순서:

1. `python3 backend/scripts/generate_verse_text.py` — 멱등, 본문+문맥 프리베이크(getbible UA 우회 내장).
2. (아이콘/프론트 자원 추가 시) `cd frontend && npm run build` — dist 마운트라 빌드 필수.
3. `docker compose restart api` — lru_cache 캐시 비우기(위 §3).
4. API 엔드포인트로 데이터 반환 확인(`/api/persons/curated` → `/api/person/{id}/relations` 등).
5. Playwright로 `localhost:8080` 렌더 확인, 콘솔/네트워크 에러 0.

성품·연대 같은 규칙 데이터는 이 앞에 해당 `validate_*.py`(위 §1)를 돌려 위반 0을 확인한 뒤 inject한다.

---

## 6. CI / 배포 게이트

- `.github/workflows/deploy.yml` — `main` push 시 self-hosted 러너에서 `git reset --hard origin/main` 후 `bash deploy.sh`. **테스트 스텝은 없다** — 검증은 저작 시점의 `validate_*`·Playwright에 위임한다.
- `deploy.sh` 게이트: ① `npm install` + `npm run build`(프론트) ② `docker compose build api` ③ `docker compose up -d api nginx` ④ `inject_ko_names.py`를 Neo4j 준비까지 최대 15회 재시도하고, 끝내 실패하면 배포를 `exit 1`로 중단한다. lock 파일로 동시 배포를 막는다.
- 배포 무음 실패(백엔드가 옛 코드) 의심 시엔 폴러보다 러너부터 확인한다(글로벌 CLAUDE.md 인프라 격리 규칙).
