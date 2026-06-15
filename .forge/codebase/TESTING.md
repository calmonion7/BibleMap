---
last_mapped_commit: bfc1dd258b0308435ca24c48a82c9c86a9e622f1
mapped: 2026-06-16
---

# TESTING

## 요약: 자동화 테스트 없음

이 레포에는 **자동화 테스트가 전혀 없다.** 다음을 모두 확인했다.

- 테스트 파일 없음 — `*test*`, `*spec*`, `*.test.js(x)`, `conftest.py`, `pytest.ini` 검색 결과 0건.
- 프론트엔드 테스트 의존성 없음 — `frontend/package.json`에 vitest/jest/testing-library/playwright/cypress 없음. `scripts`는 `dev`/`build`/`lint`/`preview`뿐, `test` 스크립트 없음.
- 백엔드 테스트 의존성 없음 — `backend/requirements.txt`는 `fastapi`, `neo4j`, `uvicorn` 3개뿐(pytest/unittest 도구 없음).
- 테스트 디렉터리(`tests/`, `__tests__/`) 없음.

따라서 모킹 프레임워크·픽스처·커버리지 측정 도구도 없다. 품질 보증은 아래의 정적 검사·수동 검증·배포 게이트로 이뤄진다.

## 1. 정적 검사 (자동화된 유일한 게이트)

- **프론트엔드 ESLint.** `cd frontend && npm run lint`(= `eslint .`, 설정 `frontend/eslint.config.js`). `eslint-plugin-react-hooks` v7의 set-state-in-effect 규칙이 비동기 외 effect setState를 잡는다. 현재 **lint-clean(exit 0)** 이며, 커밋 본문에 "npm run lint exit 0"을 검증 근거로 적는다.
- 백엔드에는 린터/타입체커 설정 파일이 없다.

## 2. 빌드 검증

- 프론트엔드: `cd frontend && npm run build`(Vite). 번들은 `frontend/dist/`. `frontend/vite.config.js`의 `manualChunks`로 `maplibre-gl`을 `maplibre` 청크, 그 외 `node_modules`를 `vendor` 청크로 분리.
- 백엔드: `backend/Dockerfile`(`python:3.12-slim`)로 이미지 빌드. **hot-reload가 아니므로** 로컬에서 백엔드 변경을 검증하려면 재빌드해야 한다: `docker compose up -d --build api`(자동배포는 매번 재빌드함).

## 3. 수동/화면 검증 (실제 검증 수단)

- 기능 검증은 **수동 UAT**로 한다. 커밋 본문에 "UAT 통과", 코드 주석에 "task N에서 어긋났던 지점" 같은 회고 기반 검증 메모가 남아 있다(자동 회귀 테스트 대신 주석으로 함정을 고정).
- **Playwright 화면 테스트(프로젝트 운영 관행).** UI 동작 검증 시 Python Playwright(`/opt/homebrew` 설치)로 `localhost:8080`(nginx)을 띄워 네트워크 캡처 + 스크린샷 패턴으로 확인한다. 단, 이 스크립트들은 레포에 커밋돼 있지 않다(애드혹 검증 도구).
- 로컬 개발 실행 절차는 `README.md` 참조: Neo4j(`docker compose up -d`) → 데이터 적재(`backend/scripts/load_theographic.py`, `inject_ko_names.py`) → API(`python3 -m uvicorn backend.app.main:app --reload`) → 프론트(`cd frontend && npm run dev`).

## 4. 배포 게이트 (사실상의 통합 체크)

자동 테스트가 없는 대신, 배포 파이프라인 자체가 통합 검증 역할을 한다.

- `main` push → GitHub Actions(`.github/workflows/deploy.yml`, self-hosted) → `git reset --hard origin/main` 후 `bash deploy.sh`.
- `deploy.sh` 단계: (1) 프론트 `npm install` + `npm run build` → `frontend/dist/`, (2) `docker compose -p biblemap build api`, (3) `docker compose -p biblemap up -d api nginx`, (4) **한글 이름 주입 게이트** — `inject_ko_names.py`를 Neo4j 준비될 때까지 최대 15회(2초 간격) 재시도, 15회 후에도 실패하면 `exit 1`로 배포 중단. 이 주입 성공이 배포 성공의 사실상 헬스체크다.
- compose 서비스(`docker-compose.yml`): `neo4j`(:7474/:7687, localhost 바인딩), `api`(FastAPI, `./data:/app/data` 볼륨), `nginx`(:8080→80, `frontend/dist`와 `nginx/nginx.conf` 마운트).

## 5. 자동 테스트를 추가한다면

- 백엔드 라우트(`backend/app/routes/*.py`)는 Neo4j 드라이버를 `backend/app/db.py`의 `get_driver()` 싱글톤으로만 잡으므로, 이 함수를 모킹하거나 테스트용 Neo4j에 연결해 `fastapi.testclient.TestClient`로 테스트하기 쉬운 구조다.
- 순수 함수 `frontend/src/convexHull.js`(Graham scan)는 외부 의존이 없어 단위 테스트 후보로 가장 명확하다.

## 관련 파일

- `frontend/package.json` / `frontend/eslint.config.js` — 린트만 있음(테스트 스크립트 없음).
- `backend/requirements.txt` — 런타임 의존만(테스트 도구 없음).
- `frontend/vite.config.js` — 빌드 청크 분리.
- `backend/Dockerfile` — 백엔드 이미지(hot-reload 아님 → 재빌드 필요).
- `deploy.sh` / `.github/workflows/deploy.yml` — 배포 게이트(한글 주입 재시도가 헬스체크).
- `docker-compose.yml` — 로컬·프로덕션 서비스 구성.
- `README.md` — 로컬 실행 절차.
