---
last_mapped_commit: 60716ea24a78866177eb8fe28dee9c43ced5ff0f
mapped: 2026-06-11
---

# TESTING

## 자동화 테스트 현황: 없음

이 프로젝트에는 **자동화 테스트 스위트가 존재하지 않는다.** 현재 커밋 기준 확인한 사실:

- 테스트 파일 없음. `*test*`, `*spec*`, `conftest.py`를 `node_modules`/`.git` 밖에서 검색해도 0건.
- 테스트 프레임워크 의존성 없음:
  - `backend/requirements.txt`에 `pytest`/`unittest` 류 없음 (운영 의존성 `fastapi`, `neo4j`, `uvicorn`뿐).
  - `frontend/package.json`에 `vitest`/`jest`/`@testing-library` 없음.
- 테스트 실행 스크립트 없음: `frontend/package.json`의 `scripts`는 `dev`/`build`/`lint`/`preview`만. `test` 스크립트 자체가 없다.
- 커버리지 도구·설정·리포트 없음.
- CI(`.github/workflows/deploy.yml`)는 테스트를 돌리지 않는다 — push 시 self-hosted 러너에서 `deploy.sh`만 실행한다.

아래는 테스트를 만들어내지 말고, **실제로 변경을 검증하는 방법**(린트/빌드/컴파일/구성검증/수동 curl)을 정리한 것이다.

## 변경 검증 방법 (실제 사용되는 게이트)

### 프론트엔드 — 빌드 & 린트

`frontend/`에서:

- 빌드 통과 여부: `npm run build` (= `vite build`). 빌드가 깨지지 않으면 1차 통과로 간주한다. 배포 스크립트도 이 명령으로 산출물을 만든다(`deploy.sh` `[1/3] 프론트엔드 빌드` → `npm install --silent && npm run build --silent`).
- 정적 분석: `npm run lint` (= `eslint .`). flat config(`frontend/eslint.config.js`)는 `@eslint/js` recommended + `eslint-plugin-react-hooks` **v7**의 `flat.recommended` + `eslint-plugin-react-refresh`(`configs.vite`)를 적용하고 `dist`를 무시한다. react-hooks v7의 `flat.recommended`에는 `react-hooks/set-state-in-effect` 규칙이 포함돼 effect 본문 내 동기 setState를 플래그하므로, 린트 실행 시 `SidePanel.jsx`의 effect(본문에서 `setLoading(true)`/`setError(null)` 호출)가 이 규칙을 위반한다(기존 위반, 미수정). (단, `deploy.sh`는 lint를 실행하지 않으므로 lint는 수동 게이트다.)
- 로컬 동작 확인: `npm run dev` (Vite, http://localhost:5173).

### 백엔드 — 문법 컴파일 체크

자동 테스트가 없으므로 최소 게이트는 Python 컴파일이다(프로젝트 루트 기준 절대경로 사용):

```bash
python3 -m py_compile \
  backend/app/main.py \
  backend/app/db.py \
  backend/app/routes/nodes.py \
  backend/app/routes/events.py \
  backend/app/routes/search.py \
  backend/scripts/inject_ko_names.py \
  backend/scripts/load_theographic.py
```

import 그래프까지 확인하려면 의존성 설치 후 모듈 import가 깨지지 않는지 본다: `pip install -r backend/requirements.txt` 후 `python3 -c "import backend.app.main"`. 단, `backend/app/db.py`의 `get_driver()`는 지연 초기화이고 import 시점에는 DB에 붙지 않으므로, import만으로는 `NEO4J_PASSWORD` 미설정 `RuntimeError`가 나지 않는다(드라이버를 실제로 쓸 때 터진다).

### 구성(Compose) 검증

스택 정의가 유효한지 확인:

```bash
docker compose config
```

`docker-compose.yml`은 `NEO4J_PASSWORD`를 `${NEO4J_PASSWORD:?...}`로 강제하므로, `NEO4J_PASSWORD`가 환경/`.env`에 없으면 `docker compose config`/`up`이 실패한다. 검증 시 `.env`(루트, `.gitignore` 대상)에 비밀번호가 있어야 한다.

### 수동 / 라이브 검증 (curl로 실제 스택 확인)

기능 검증은 실제로 스택을 띄워 엔드포인트를 호출하는 식으로 한다. 기동 순서는 `README.md` 참고:

1. `docker compose up -d` (Neo4j 기동).
2. 최초 1회 데이터 적재: `python3 backend/scripts/load_theographic.py` → `python3 backend/scripts/inject_ko_names.py` (두 스크립트 모두 `NEO4J_PASSWORD` 필요, 미설정 시 즉시 `RuntimeError`).
3. API: `python3 -m uvicorn backend.app.main:app --reload` (http://localhost:8000). (README 주의: `uvicorn` 직접 호출은 PATH 문제 소지가 있어 `python3 -m uvicorn` 사용.)
4. 프론트엔드: `cd frontend && npm install && npm run dev`.

API가 떴으면 라이브 curl로 라우트를 확인한다(엔드포인트는 모두 GET):

```bash
curl 'http://localhost:8000/search?q=모세'
curl 'http://localhost:8000/node/<theographic_id>'
curl 'http://localhost:8000/node/<theographic_id>/places'
curl 'http://localhost:8000/node/<theographic_id>/neighbors/grouped'
curl 'http://localhost:8000/events'
```

검증 포인트:
- 없는 노드는 404 + `{"detail":"Node not found"}` (`backend/app/routes/nodes.py`).
- 빈 검색어는 200 + `[]` (`backend/app/routes/search.py`, `if not q.strip(): return []`).
- `/events`는 `Cache-Control: no-store` 헤더 동반(`backend/app/routes/events.py`).
- 응답에 `nameKo`/`nameKoMissing` 필드가 한국어 이름 주입 결과를 반영하는지(주입은 `inject_ko_names.py`).
- 좌표 결측 Place가 `/node/.../places`에서 제외되는지(`float` 캐스팅 실패 시 `continue`).

### 배포 파이프라인이 사실상의 통합 검증

`deploy.sh`(self-hosted GitHub Actions 러너가 `main` push마다 실행, `.github/workflows/deploy.yml`)가 "끝까지 도느냐"가 통합 게이트 역할을 한다:

1. `npm install` + `npm run build` (프론트 빌드 깨지면 `set -e`로 중단).
2. `docker compose -p biblemap build api` (백엔드 이미지 빌드).
3. `docker compose -p biblemap up -d api nginx` (재기동).
4. `python3 backend/scripts/inject_ko_names.py`를 최대 15회 재시도하며 Neo4j 준비를 기다림. 15회 모두 실패하면 `exit 1`로 배포 중단. → 한국어 이름 주입(=DB 연결+쓰기)이 성공해야만 배포가 성공으로 간주된다.

## 모킹

모킹 프레임워크·픽스처·스텁이 **없다**. 테스트가 없으므로 mock도 없다. 외부 의존성(Neo4j, ArcGIS 타일, theographic GitHub raw JSON)은 모두 라이브 호출로만 검증된다.

## 새 테스트를 추가하려는 경우 (참고)

현재 도입된 게 없으므로, 추가한다면 다음이 자연스러운 후보다(아직 미설정 — 추가 시 의존성·스크립트도 함께 넣어야 함):

- 백엔드: `pytest` + FastAPI `TestClient`. Neo4j 의존을 끊으려면 `backend/app/db.py`의 `get_driver()`를 모킹/주입해야 한다(현재는 전역 싱글턴 지연 초기화라 그대로는 단위 테스트가 어렵다).
- 프론트엔드: `vitest` + `@testing-library/react` (Vite 프로젝트이므로 vitest가 정합).
