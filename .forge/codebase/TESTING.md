---
last_mapped_commit: 815433397ff74c133b2de5d1cafe1c8764b5303c
mapped: 2026-07-04
---

# 테스트 패턴

**분석일:** 2026-07-04

## 요약 — 자동화된 유닛/통합 테스트 스위트 없음

이 저장소에는 **커밋된 유닛 테스트, 통합 테스트, 테스트 러너 설정이 존재하지 않는다.**

확인 근거:
- `frontend/package.json`에 `test` 스크립트가 없다. 스크립트는 `dev`/`build`/`lint`/`preview`뿐 (`frontend/package.json:6-11`).
- `frontend`의 devDependencies에 Jest·Vitest·Mocha·Cypress·`@testing-library`·`@playwright/test` 등 **테스트 러너가 하나도 없다** (`frontend/package.json:18-28`).
- 저장소 어디에도 `*.test.*` / `*.spec.*` / `__tests__/` / `test_*.py` / `conftest.py`가 없다.
- `backend/requirements.txt`에 `pytest` 등 테스트 프레임워크가 없다 — `fastapi`, `neo4j`, `uvicorn`뿐 (`backend/requirements.txt`).
- `pytest.ini`·`tox.ini`·`playwright.config.*` 등 테스트 설정 파일이 없다.

품질 검증은 **① ESLint(프론트) ② 수동 Playwright UAT 스크립트 ③ 배포 파이프라인의 검증 단계**로 이뤄진다. 아래에 각각 기술한다.

---

## 실질 검증 수단 1 — ESLint (프론트엔드 정적 검사)

프론트엔드에서 자동화된 정적 게이트는 ESLint뿐이다.

**설정:** `frontend/eslint.config.js` (flat config)
- `@eslint/js` recommended
- `eslint-plugin-react-hooks` (flat.recommended) — 훅 규칙 엄격
- `eslint-plugin-react-refresh` (vite)
- `dist` 무시

**실행:**
```bash
cd frontend
npm run lint        # = eslint .
```

CI(`.github/workflows/deploy.yml`)에서는 lint를 별도 스텝으로 호출하지 않는다 — 로컬/수동 실행 도구다.

---

## 실질 검증 수단 2 — Playwright UAT/검증 스크립트 (일회성)

프로젝트의 실제 UI·API 검증은 **Python Playwright(sync API)로 작성한 일회성 UAT 스크립트**로 수행한다. 이 스크립트들은 정식 테스트 스위트가 아니라 **작업(task)별 수동 수용 검증**용이며, 산출물(스크립트 + 스크린샷 + HTML 리포트)이 `.forge/reports/`에 남는다.

**위치:** `.forge/reports/` (예: `.forge/reports/uat_118_primeval.py`, `task70_verify.py`, `task70_final.py`, `task_place_context_verify.py`, `task_place_dom_probe.py`). 현재 10개의 `.py` 검증 스크립트 + 다수의 `.png` 스크린샷 + `.html` 리포트가 있다.

**프레임워크:** `playwright.sync_api` (Python). 저장소 requirements에는 포함되지 않고, **호스트의 Homebrew Python에 전역 설치**돼 있다 — `/opt/homebrew/lib/python3.14/site-packages/playwright`, CLI는 `/opt/homebrew/bin/playwright`. (기본 `python3`에는 playwright가 없으므로 Homebrew python으로 실행해야 한다.)

**대상:** 로컬 nginx가 서빙하는 `http://localhost:8080`. API는 nginx 프록시를 통해 `/api/...`로 접근(`:8000`은 직접 노출 안 됨).

**표준 UAT 스크립트 구조** (`.forge/reports/uat_118_primeval.py`):

```python
import json, sys, time, urllib.request
from playwright.sync_api import sync_playwright

BASE = "http://localhost:8080"
SS = "/Users/calmonion/Project/BibleMap/.forge/reports/"   # 스크린샷 저장 경로(절대경로)

def api_get(path):
    with urllib.request.urlopen(f"{BASE}{path}") as r:
        return json.loads(r.read())

results = {}

# 1) API 계약 검증 — urllib로 /api 엔드포인트 직접 호출해 shape/값 assert
curated = api_get("/api/persons/curated")

# 2) UI 검증 — 콘솔 에러·네트워크 실패 캡처 후 상호작용
console_errors, network_errors = [], []
with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1280, "height": 900})
    page.on("console", lambda m: console_errors.append(m.text) if m.type == "error" else None)
    page.on("requestfailed", lambda req: network_errors.append(f"FAIL {req.url}"))

    page.goto(f"{BASE}/", wait_until="networkidle")
    time.sleep(2)
    page.screenshot(path=f"{SS}uat_01_home.png")

    # 한글 텍스트 로케이터로 요소 확인 — text= 셀렉터 위주
    has = page.locator("text=원시사").count() > 0
    page.locator("text=가인").first.click()
    ...
    browser.close()

# 3) 결과를 JSON으로 출력(사람이 읽는 요약은 한글)
print(json.dumps(results, ensure_ascii=False, indent=2))
```

**관찰된 UAT 관례:**
- **API + UI 이중 검증.** `urllib.request`로 `/api/...` JSON 계약을 먼저 검사한 뒤(응답 키·개수·값 매칭), Playwright로 화면 상호작용을 검증한다.
- **콘솔·네트워크 오류 수집.** `page.on("console", ...)`로 error 레벨 콘솔 로그를, `page.on("requestfailed", ...)`로 실패 요청을 모아 결과에 포함한다.
- **로케이터.** 한글 `text=` 셀렉터 위주(`page.locator("text=원시사")`). 구조가 불확실하면 `[class*='stop'], [class*='event']`처럼 부분 클래스 매칭으로 시도 후 예외를 삼킨다.
- **뷰포트 분기.** 데스크톱(`1280×900`)·모바일 뷰포트를 각각 열어 반응형(하단 시트 vs 사이드패널)을 확인. 스크린샷 파일명에 `desktop`/`mobile` 접두 (예: `task112-desktop-timeline.png`, `task112-mobile-timeline.png`).
- **대기 전략.** `wait_until="networkidle"` + 명시적 `time.sleep(1~2)`. 지도(maplibre) 렌더 안정화를 위해 sleep을 병용한다.
- **스크린샷 증거.** 각 단계마다 `.forge/reports/`에 `.png`로 남겨 육안 회귀 확인. task 번호를 파일명에 부여(`task112-...`, `task113-...`, `uat_118_...`).
- **한글 리포트.** 사람이 읽는 결과 요약은 한글로 작성(프로젝트 메모리의 "실행내역 한글로" 규칙).
- **JSON 파싱은 `ensure_ascii=False`** — 한글이 이스케이프되지 않게 출력.

**실행 예:**
```bash
# 사전 조건: 로컬 스택이 :8080에서 서빙 중이어야 함
/opt/homebrew/bin/python3 .forge/reports/uat_118_primeval.py
```

---

## 실질 검증 수단 3 — 배포 파이프라인의 검증 단계

`deploy.sh`는 정식 테스트는 아니지만 배포 성공을 좌우하는 **런타임 검증 게이트**를 포함한다:
- 프론트 빌드(`npm run build`) 성공 (`deploy.sh:34-37`).
- API 이미지 빌드 성공 (`deploy.sh:41-42`).
- **한글 이름 주입 스크립트 재시도 게이트** — `backend/scripts/inject_ko_names.py`를 최대 15회(2초 간격) 재시도, 15회 후에도 실패하면 **배포 중단(`exit 1`)** (`deploy.sh:50-62`). Neo4j 준비 완료 + 데이터 정합성을 사실상 검증한다.

---

## 로컬 검증 사전 준비 (중요)

로컬 UI 검증 전 반드시 프론트를 빌드해야 한다. `:8080` nginx는 `frontend/dist`를 마운트하며 HMR이 아니다 — 소스만 고치면 화면에 반영되지 않는다.

```bash
cd frontend && npm run build          # .env.production의 VITE_API_URL=/api 자동 적용
cd .. && docker compose -p biblemap up -d --build api   # 백엔드 변경 시
```

- 프론트 `:8080`은 `frontend/dist`(빌드 산출물) 마운트 (`docker-compose.yml`의 nginx 볼륨 `./frontend/dist:/usr/share/nginx/html:ro`).
- API `:8000`은 외부 미노출 — nginx `/api` 프록시로만 접근.
- Neo4j는 `127.0.0.1:7474`(브라우저)/`7687`(bolt)에 로컬 바인딩 (`docker-compose.yml`).

---

## 테스트 유형별 현황

| 유형 | 상태 |
|------|------|
| 유닛 테스트 | 없음 |
| 통합 테스트 | 없음 |
| E2E/UI 테스트 | 정식 스위트 없음. 일회성 Playwright UAT 스크립트로 대체 (`.forge/reports/*.py`) |
| 정적 분석 | ESLint (프론트만, `npm run lint`) |
| 백엔드 검증 | 배포 시 `inject_ko_names.py` 재시도 게이트 (`deploy.sh`) |
| CI 게이트 | `.github/workflows/deploy.yml`은 배포만 수행 — 테스트/lint 스텝 없음 |

---

## 신규 테스트를 추가한다면 (관례 기준 권고)

정식 러너가 없으므로 새로 도입해야 한다. 기존 관례에 맞추려면:
- **UI/E2E 검증:** 기존 Python Playwright(sync) 패턴을 그대로 따르고 스크립트를 `.forge/reports/`에 두거나, 정식화하려면 프론트에 `@playwright/test`를 별도 도입한다. `BASE=http://localhost:8080`, API 계약 검증(`urllib`) + 콘솔/네트워크 오류 수집 + 스크린샷 증거 패턴을 유지.
- **백엔드 유닛:** `pytest`를 `backend/requirements.txt`에 추가하고 `backend/tests/`에 배치. `backend/app/overlays.py`의 `_resolve`/`_load`, `backend/app/routes/persons.py`의 `_build_list` 정렬·나눔 로직, `backend/app/routes/nodes.py`의 `_year` startDate 파서 등 순수 함수가 우선 대상.
- **프론트 유닛:** Vitest를 도입한다면 순수 로직 모듈(`frontend/src/dates.js`의 `parseYear`, `frontend/src/mapGeo.js`, `frontend/src/theme.js`의 `typeColor`/`typeKo`)이 컴포넌트보다 검증 가치가 높다.

---

*테스트 분석: 2026-07-04*
