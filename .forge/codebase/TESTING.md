---
last_mapped_commit: 79f9d9df07c0d79f8fa07940e3f76c8d5424524b
mapped: 2026-06-28
---
# 테스트 패턴

**분석일:** 2026-06-28

## 자동화 테스트 프레임워크: 없음

리포지터리에 단위·통합 테스트 인프라가 **존재하지 않는다**(2026-06-28 HEAD 기준).

- **테스트 파일 0건:** `*.test.*`, `*.spec.*`, `test_*.py`, `*_test.py`, `conftest.py` 전수 검색 결과 없음(`node_modules` 제외).
- **테스트 러너 설정 없음:** `jest.config.*`, `vitest.config.*`, `pytest.ini`, `setup.cfg`, `tox.ini`, `pyproject.toml` 없음.
- **`frontend/package.json` scripts:** `dev`/`build`/`lint`/`preview`만 존재 — `test` 스크립트 없음.
- **`backend/requirements.txt`:** `fastapi`, `neo4j`, `uvicorn` 3개뿐 — `pytest`·`httpx`·테스트 라이브러리 미포함.
- **CI에 테스트 단계 없음:** `.github/workflows/deploy.yml`은 `git fetch → reset --hard → bash deploy.sh`만 수행. 테스트 게이트 없음.

신규 코드를 검증할 때는 아래 "현재 검증 방식"을 따른다.

---

## 현재 검증 방식

### 1. 린트(프론트엔드 정적 검사)

자동 검사로 사실상 유일하게 강제되는 게이트.

```bash
cd frontend && npm run lint     # eslint . — react-hooks 규칙 포함
```

코드 주석이 react-hooks lint 규칙(특히 set-state-in-effect)을 의식해 작성돼 있어(`App.jsx`, `SidePanel.jsx`), 린트 통과가 사실상의 합의 기준이다. 백엔드 Python 린터는 미설정.

### 2. 빌드(타입·구문 깨짐 탐지)

```bash
cd frontend && npm run build    # vite build — dist/ 산출
docker compose -p biblemap build api   # API 이미지 빌드
```

**중요(사용자 메모리 규칙):** 로컬 `:8080`은 `frontend/dist`를 마운트하는 정적 서빙이며 HMR이 아니다. 따라서 UI 검증 전 **반드시 `cd frontend && npm run build`로 dist를 갱신**해야 변경이 반영된다. `.env.production`의 `VITE_API_URL=/api`가 빌드타임 주입돼 nginx 프록시(`/api` → `api:8000`)를 탄다. API도 변경 시 `docker compose up -d --build api`.

### 3. Playwright 화면 테스트(UI 동작 검증)

사용자 메모리에 정착된 수동 검증 절차. **Python Playwright**를 사용한다(JS Playwright 아님).

- **런타임:** `/opt/homebrew`에 설치된 Python Playwright.
- **대상:** `http://localhost:8080`(nginx가 서빙하는 빌드된 프론트).
- **패턴:** 네트워크 요청 캡처 + 스크린샷. 사용자가 본 화면과 `/api/*` 응답을 함께 검증하는 방식.
- **선행 조건:** 위 2번대로 `npm run build` + 컨테이너 기동이 끝난 상태여야 한다(`docker-compose.yml`의 `nginx`가 `frontend/dist`를 read-only 마운트, `:8080` 노출).

별도 `playwright.config.*`나 스펙 파일은 리포에 커밋돼 있지 않다 — 검증 시점에 일회성 스크립트로 실행하는 운용.

---

## 테스트 작성 시 권장(인프라 부재 상태에서)

자동 테스트가 없으므로, 코드는 **검증 가능성을 높이는 구조**로 작성돼 있다. 신규 코드도 이를 따른다.

- **순수 함수 분리:** 지오메트리·GeoJSON 변환은 `frontend/src/mapGeo.js`에 부수효과 없는 순수 함수로 모여 있다(`coreBounds`, `placesToGeoJSON`, `buildJourneyLineGeoJSON`, `journeyStopGroups`, `compactSeqs` 등). 만약 단위 테스트를 도입한다면 이 모듈이 가장 테스트하기 쉬운 진입점이다(입력 배열 → 출력 GeoJSON/bounds, Neo4j·DOM 의존 없음).
- **백엔드 라우트의 정적 헬퍼:** `persons.py`의 `_build_list`, `places.py`의 `_place_to_persons`, `journey.py`의 `_build_id_to_slug`/`_load_events`는 `data/person_events/*.json`만 읽고 Neo4j를 타지 않아(파일만으로 결정적) DB 없이 검증 가능. 단 `@functools.lru_cache`가 걸려 있어 테스트 간 `cache_clear()`가 필요.
- **DB 의존 경계:** Neo4j를 실제로 타는 코드(`nodes.py`, `search.py`, `books.py`, `events.py`의 Cypher 부분, `journey.py:_fetch_place_coords`)는 통합 검증 영역. `get_driver()`(`db.py`)가 모듈 전역 lazy 싱글톤이라 모킹 시 `app.db._driver`를 직접 주입하거나 `get_driver`를 패치하는 방식이 된다.

---

## 데이터 적재·생성 스크립트 검증

`backend/scripts/`의 18개 스크립트(`load_*`, `generate_*`, `inject_*`, `enrich_*`)는 모두 `if __name__ == "__main__": main()` 형태의 일회성 CLI다.

- **검증 방식:** 실행 후 `print(...)`로 출력하는 집계 카운트를 사람이 확인(예 `inject_ko_names.py`의 `Person nodes updated: N` ... `Total: N`).
- **자동 assert·테스트 없음.** 멱등성·정확성은 출력 수치 육안 확인에 의존.
- **배포 파이프라인 내 검증:** `deploy.sh` `[4/4]` 단계가 `inject_ko_names.py`를 Neo4j 준비까지 최대 15회 재시도하며 실행하고, 실패 시 배포를 중단(`exit 1`)한다 — 적재 스크립트가 사실상의 배포 후 스모크 역할.

---

## 커버리지

측정·강제 안 함. 커버리지 도구·임계값 미설정.

---

*테스트 분석: 2026-06-28*
