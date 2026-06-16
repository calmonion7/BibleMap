---
last_mapped_commit: e160d65cf9c7d0b54c8d9fc2d031639a712bfb86
mapped: 2026-06-16
---

# TESTING

## 요약 — 자동화 테스트 없음

**이 레포에는 자동화된 테스트가 전혀 없다.** 테스트 프레임워크 의존성, 테스트 파일, 테스트 설정, CI 테스트 단계 어느 것도 존재하지 않는다. 검증은 전적으로 수동(로컬 실행 + 브라우저 확인)으로 이뤄진다.

---

## 근거 (없음을 입증하는 사실)

### 테스트 파일 부재

- 레포 전체에서 `*test*`, `*spec*`, `conftest*` 패턴의 소스 파일을 검색한 결과 **0건**(`.git/`, `node_modules/`, `.forge/`, `frontend/dist/` 제외).
- `backend/` 하위에 `tests/` 디렉터리 없음. `frontend/src/` 하위에 `.test.jsx`/`.spec.js` 없음.

### 테스트 프레임워크 의존성 부재

- 백엔드 `backend/requirements.txt`는 런타임 3종만 포함 — `fastapi==0.136.3`, `neo4j==6.2.0`, `uvicorn==0.49.0`. `pytest`/`unittest`(서드파티)/`httpx`(테스트 클라이언트용) 없음. dev requirements 파일도 없음.
- 프론트엔드 `frontend/package.json`의 `devDependencies`에 테스트 러너 없음 — `vitest`/`jest`/`@testing-library/*`/`playwright` 어느 것도 선언돼 있지 않음. ESLint·Vite·React 플러그인만 존재.
- 레포 전체에서 `pytest|vitest|jest|@testing-library|playwright|unittest` 문자열을 설정·소스 파일에서 검색한 결과 **0건**.

### 테스트 설정 부재

- `pytest.ini` / `pyproject.toml` / `setup.cfg` / `tox.ini`(Python) 없음. `vitest.config.*` / `jest.config.*`(JS) 없음.
- `frontend/package.json`의 `scripts`에 `test` 항목 없음 — 정의된 스크립트는 `dev`, `build`, `lint`, `preview`뿐.

### CI에 테스트 단계 부재

- `.github/workflows/deploy.yml`은 유일한 워크플로우이며, main push 시 self-hosted 러너에서 `git reset --hard origin/main` 후 `bash deploy.sh`만 실행한다. lint/test 단계 없음.
- `deploy.sh`도 빌드(`npm run build`) → docker 이미지 빌드 → 컨테이너 재시작 → 한글 이름 주입 순서일 뿐, 테스트를 돌리지 않는다.

---

## 실제 검증 방식 (테스트 대용)

자동화 테스트가 없는 대신 다음 수단으로 검증한다.

- **린트**: 프론트엔드만 `npm run lint`(= `eslint .`, 설정 `frontend/eslint.config.js`). 백엔드 린터 없음.
- **수동 실행 검증**:
  - 전체 스택은 `docker compose up`으로 기동(`docker-compose.yml`: `neo4j` + `api` + `nginx`). 프론트는 nginx가 `frontend/dist`를 서빙하고 `:8080`으로 노출.
  - 백엔드는 hot-reload가 아니므로(`backend/Dockerfile` CMD에 `--reload` 없음) 코드 변경 후 `docker compose up -d --build api`로 재빌드해야 반영된다.
  - 프론트 개발은 `npm run dev`(Vite dev server).
- **ETL 스크립트의 인라인 자가 검증**: 일부 `generate_*` 스크립트가 산출물 일부를 표준출력으로 찍어 육안 확인하게 한다. 예: `backend/scripts/generate_event_verses.py:128-136` — 다권(공관복음 평행) 사건 1건을 골라 `bookId`/`rangeLabel`/절 수를 출력하는 `[검증]` 블록. 이는 정식 테스트가 아니라 1회성 실행 시의 sanity check다.
- **브라우저 기반 수동 테스트**: 프로젝트 메모리에 Python Playwright(`/opt/homebrew` 설치)로 `localhost:8080`을 네트워크 캡처 + 스크린샷으로 확인하는 패턴이 기록돼 있으나, 이는 레포에 커밋된 테스트 코드가 아니라 개발 중 임시 검증 절차다.

---

## 커버리지

측정 도구·리포트 없음(테스트 자체가 없으므로 해당 사항 없음). 커버리지 설정(`coverage`, `c8`, `.coveragerc` 등) 파일 부재.

---

## 테스트를 추가한다면 (현재 상태 기준 참고)

이 섹션은 현재 구현 사실이 아니라, 스택에 맞춘 자연스러운 출발점을 메모한 것이다.

- 백엔드: FastAPI 라우트는 동기 `def` 핸들러라 `pytest` + `httpx`/`TestClient`로 테스트 가능하나, 모든 핸들러가 `get_driver()`(`backend/app/db.py`)를 직접 호출하고 의존성 주입을 쓰지 않아 Neo4j 모킹이나 테스트 DB 픽스처 구성이 선행돼야 한다. 순수 함수(예: `generate_event_verses.py`의 `parse_verse`/`build_range_label`, `inject_ko_names.py`의 변환 로직)는 DB 없이 단위 테스트하기 쉽다.
- 프론트엔드: `convexHull.js`(순수 함수)는 러너만 추가하면 바로 단위 테스트 가능. 컴포넌트는 `apiGet`(`frontend/src/api.js`)·`fetchChapter`(`frontend/src/getbible.js`)가 모킹 지점이 된다(현재 모킹 인프라 없음).
