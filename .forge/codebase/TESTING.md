---
last_mapped_commit: 9c49a838dfe4c6e4695b9383ea961f15c9b117f2
mapped: 2026-07-10
---

# TESTING

**요약: BibleMap에는 자동화된 단위·통합 테스트 스위트가 없다.** 검증은 (1) 빌드/린트, (2) 데이터 저작 후 검증 파이프라인, (3) 실행 후 Playwright + API curl 스모크로 이뤄진다. 새 코드도 이 절차를 따르며, 테스트 프레임워크를 새로 도입하지 않는다(요청 시에만).

---

## 1. 테스트 프레임워크 (부재)

- **백엔드**: `pytest`·`unittest` 없음. `backend/requirements.txt`에는 런타임 3개(`fastapi`·`neo4j`·`uvicorn`)만 있고 테스트 의존성이 없다. `test_*.py`·`conftest.py`·`tests/` 디렉터리 없음.
- **프론트엔드**: `vitest`·`jest`·`@testing-library` 없음. `frontend/package.json` scripts는 `dev`·`build`·`lint`·`preview`뿐 — `test` 스크립트 없음. `*.test.js(x)`·`*.spec.js(x)` 파일 없음.
- **E2E 스펙 파일**: 리포에 커밋된 Playwright 스펙(`*.spec.ts` 등)은 없다. Playwright는 아래 4절처럼 **애드혹 검증 도구**로만 쓴다.

> 검증 구멍(CONCERNS 소관): 순수 함수 로직에 회귀 테스트가 없다. 예 — `urlState.js`의 `parseHash`/`encodeHash`(정규식 라우팅), `nodes.py`의 `_year()` BC/AD 연도 파싱 정렬, `persons.py`의 `_build_relations` slug 매칭·`_build_connections` 큐레이션 교집합 제외. 이들은 단위 테스트를 붙이기 좋은 순수 함수이나 현재 미커버.

---

## 2. 실제 검증 수단: 빌드 + 린트

빌드/린트 통과가 사실상의 1차 게이트다.

```bash
# 프론트 린트 (ESLint flat config)
cd frontend && npm run lint

# 프론트 빌드 — :8080은 frontend/dist 마운트(HMR 아님)이므로 로컬 검증 전 필수
cd frontend && npm run build      # .env.production의 VITE_API_URL=/api 자동 주입

# 백엔드 이미지 빌드
docker compose up -d --build api
```

- **로컬 검증 전 빌드 필수**: nginx는 `frontend/dist`를 읽기전용 마운트한다(`docker-compose.yml`) — 소스만 고치고 빌드를 건너뛰면 :8080에 반영되지 않는다.
- **백엔드 API 포트(:8000)는 외부 미노출**. 프론트는 nginx `/api` 프록시로만 접근하고, 로컬 검증도 `http://localhost:8080/api/...`로 친다.

## 3. 데이터 저작 검증 파이프라인

`data/person_relations/AUTHORING.md` 규칙 8이 정본. 인물 관계·이벤트 데이터를 저작한 뒤 반드시 순서대로 실행한다:

```bash
# 1) 절/문맥 본문 프리베이크 (멱등, getbible UA 우회 내장)
python3 backend/scripts/generate_verse_text.py

# 2) 새 유형 아이콘을 추가했으면 프론트 재빌드 (dist 마운트)
cd frontend && npm run build

# 3) 백엔드 재시작 — lru_cache 캐시를 반드시 비운다 (up -d로는 재생성 안 됨)
docker compose restart api

# 4) API로 관계 반환 확인
curl -s http://localhost:8080/api/persons/curated              # node_id 확보
curl -s http://localhost:8080/api/person/<node_id>/relations   # 국면 배열 확인
```

- **footgun (규칙 8-3)**: 데이터는 마운트 오버레이라 재빌드 불필요하나, 백엔드가 관계 카탈로그를 `@functools.lru_cache`로 기동 시 메모리 캐시하므로 **`docker compose restart api`**로 캐시를 비워야 신규 데이터가 보인다. `docker compose up -d api`는 config 무변경 시 컨테이너를 재생성하지 않아("Running") 옛 데이터를 계속 서빙한다.
- **저작 스크립트 자체 검증**: `generate_verse_text.py`는 멱등이다 — 이미 본문이 있는 항목은 스킵하고, 못 받은 본문은 `null`로 기록해 재실행 시 재시도한다(스크립트 헤더 docstring).

## 4. 실행 후 스모크: Playwright + 네트워크 캡처

UI 동작 검증은 Python Playwright로 한다(`/opt/homebrew` 설치). 패턴: `localhost:8080`(:8000 미노출) 렌더 확인 + 네트워크 캡처 + 스크린샷.

- **합격 기준**: 콘솔 에러 0, 네트워크(fetch) 에러 0, 대상 뷰가 기대대로 렌더.
- **적용 대상**: 관계 뷰·여정 지도·타임라인 등 상호작용 화면. AUTHORING.md 규칙 8-5가 데이터 저작의 마지막 게이트로 이 스모크를 요구한다.

## 5. 배포 검증

`deploy.sh`가 프로덕션 배포 시 인라인 검증을 수행한다(별도 테스트 대신):

- `NEO4J_PASSWORD`가 준비될 때까지 `inject_ko_names.py`를 **최대 15회 재시도**(2초 간격)하며, 15회 후에도 실패하면 `exit 1`로 배포를 중단한다(`deploy.sh` [4/4]).
- 배포 락(`/tmp/biblemap-deploy.lock`)으로 중복 배포를 막는다.
- 배포 무음 실패 시(백엔드가 옛 코드) self-hosted 러너 상태부터 의심한다(`gh run list`로 `queued`/`cancelled(24h)` 확인).

## 6. 백엔드의 내장 방어(테스트 대체 성격)

명시적 테스트가 없는 대신, 런타임 방어 코드가 계약을 강제한다:

- `backend/app/db.py`: `NEO4J_PASSWORD` 미설정 시 `RuntimeError`로 기동 실패(조용한 오작동 방지).
- `backend/app/main.py` lifespan: 인덱스 생성 실패를 `logging.exception`으로 잡고 인덱스 없이 계속 진행(가용성 우선).
- `backend/app/overlays.py` `_load()`: `json.JSONDecodeError`를 빈 dict로 삼켜 파손 파일에 방어.
- `backend/app/routes/persons.py` `_build_list()`: `events[0].participants`가 비면 `logging.warning` 후 해당 slug 건너뜀.

---

## 새 코드 검증 방법 (권장 절차)

1. 백엔드 라우트를 추가/변경 → `docker compose up -d --build api` 후 `curl -s http://localhost:8080/api/<path>`로 응답 형태 확인.
2. 데이터를 저작 → 위 3절 파이프라인 전체 실행.
3. 프론트를 변경 → `npm run lint` → `npm run build` → Playwright 스모크(콘솔/네트워크 에러 0).
4. 순수 함수(라우팅·파싱·정렬)를 새로 쓸 때 회귀 위험이 크면, 테스트 프레임워크 부재를 감안해 최소한 애드혹 `python3 -c`/`node -e` 스니펫으로 경계값을 손검증한다.

---

*Testing analysis: 2026-07-10*
