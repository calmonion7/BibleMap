---
last_mapped_commit: 288b14e23c889de294d34d0f794867d4e313a421
mapped: 2026-06-11
---

# 테스팅 / 검증

이 문서는 BibleMap에서 변경을 **실제로 어떻게 검증하는지**를 정직하게 기록한다. 추측한 테스트를 지어내지 않는다.

---

## 1. 자동화된 테스트 프레임워크 — 없음

리포지토리 안에 **자동화 테스트 스위트가 전혀 없다.**

- **프론트엔드**: 테스트 프레임워크 미설치. `frontend/package.json`의 `devDependencies`에 `vitest`/`jest`/`@testing-library/*`/`playwright`/`cypress` 등이 없고, `scripts`에도 `test`가 없다(`dev`/`build`/`lint`/`preview`만 존재). `*.test.jsx`·`*.spec.jsx` 파일도 없다.
- **백엔드**: 테스트 스위트·`pytest` 미설치. `backend/requirements.txt`는 런타임 의존성(`fastapi`, `neo4j`, `uvicorn`)만 담고 `pytest`/`httpx` 등 테스트 의존성이 없다. `conftest.py`·`pytest.ini`·`tests/` 디렉터리·`test_*.py` 파일이 어디에도 없다.
- 리포 전체에서 발견되는 유일한 "test" 매칭 파일은 이 문서(`.forge/codebase/TESTING.md`) 자신뿐이다.

따라서 "테스트를 돌린다"는 개념이 없고, 검증은 아래의 정적 검사 + 빌드 + 수동 확인으로 이뤄진다.

## 2. 실제 검증 루프

변경 후 다음 순서로 확인한다:

1. **`npx eslint .`** (= `npm run lint`, `frontend/`에서 실행) — 정적 분석. `eslint.config.js`의 `js.recommended` + `eslint-plugin-react-hooks` v7(`reactHooks.configs.flat.recommended`) + `eslint-plugin-react-refresh`(vite preset)를 적용한다. 특히 react-hooks의 `set-state-in-effect` 규칙이 핵심 게이트다(CONVENTIONS.md §3 참조). **현재 exit 0으로 완전히 clean.**
2. **`npm run build`** (= `vite build`, `frontend/`) — 프로덕션 번들이 깨지지 않는지 확인. 백엔드는 빌드 단계가 없고 컨테이너 이미지 빌드(`docker compose ... build api`)로 대신한다.
3. **수동 브라우저 확인** — 실행 중인 백엔드를 가리키는 Vite dev 서버(Claude Preview)를 띄워 지도 마커 클릭, 사이드패널/그래프/타임라인 전환, 검색, 모바일 하단 시트 등을 눈으로 검증한다. 자동화된 E2E는 없으므로 UI 동작 확인은 전적으로 수동이다.

런타임 의존성상 백엔드 검증은 **살아 있는 Neo4j**가 필요하다(`db.py`의 `get_driver()`가 `NEO4J_PASSWORD` 없으면 즉시 `RuntimeError`). 데이터가 적재돼 있어야 라우트가 의미 있는 응답을 준다.

## 3. 데이터 적재 / 주입 스크립트 (테스트 아님, 검증의 전제)

`backend/scripts/`의 두 스크립트는 테스트가 아니라 **DB 상태를 만드는 일회성 ETL**이다. 검증 환경의 전제 조건이므로 함께 기록한다.

- `load_theographic.py` — Theographic 원천 JSON(GitHub raw)을 받아 `MERGE` 기반으로 노드·관계를 적재(idempotent, 배치 `UNWIND`). `if __name__ == "__main__"`로 직접 실행. 검증 출력은 `print` 진행 로그("Published: N people ...", 각 적재 단계, "Done.")로만 확인한다 — assert 없음.
- `inject_ko_names.py` — 로컬 `data/names_ko/*.json`의 한글명/별칭을 `nameKo`/`aliasesKo` 프로퍼티로 주입. `result.consume().counters.properties_set // 2`로 갱신 건수를 세어 `print`로 보고한다(이것이 사실상 유일한 "성공 카운트" 자기 점검).

## 4. 배포 시 자동 검증 (CI)

`.github/workflows/deploy.yml`은 `main` 푸시 시 self-hosted 러너에서 `deploy.sh`를 돌린다. 이 스크립트가 사실상의 통합 게이트 역할을 한다(`deploy.sh`):

- `[1/3] 프론트엔드 빌드`: `npm install` + `npm run build`. `set -e`라 빌드 실패 시 배포 전체가 중단된다.
- `[2/3] API 이미지 빌드` → `[3/4] 컨테이너 재시작`: `docker compose -p biblemap build api` 후 `up -d api nginx`.
- `[4/4] 한글 이름 주입`: `inject_ko_names.py`를 **최대 15회(2초 간격) 재시도**하며 Neo4j가 뜰 때까지 기다린다. 끝까지 실패하면 `exit 1`로 배포 중단. 즉 "주입 스크립트가 성공해야 배포 성공"이라는 가벼운 스모크 체크가 들어가 있다.
- 동시 배포 방지를 위해 `/tmp/biblemap-deploy.lock` 락 파일을 쓴다.

CI 파이프라인에 lint·build 외의 **테스트 단계는 없다.** `deploy.yml`은 빌드/배포만 수행하고, 별도의 lint/test job을 두지 않는다(빌드 실패와 주입 실패만이 자동 게이트).

## 5. 요약

| 항목 | 상태 |
|---|---|
| 프론트 단위/통합/E2E 테스트 | 없음 |
| 백엔드 단위/통합 테스트 (`pytest`) | 없음 |
| 정적 분석 | `npx eslint .` (현재 clean, exit 0) |
| 빌드 검증 | `npm run build` (vite), `docker compose build api` |
| 런타임 검증 | 수동 브라우저 확인(Claude Preview dev 서버 → 실행 중 백엔드) |
| CI | `deploy.yml` → `deploy.sh`: build + 컨테이너 재시작 + 한글 주입 재시도(스모크) |

새 검증 수단을 도입하기 전까지, 변경의 신뢰도는 "lint clean + build 성공 + 직접 눈으로 확인"에 달려 있다.
