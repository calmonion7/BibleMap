---
last_mapped_commit: 95ba754e0a5b8a8db6f537f88d6d4e60d302d066
mapped: 2026-07-06
---

# 테스트 패턴

## 요약 — 자동화된 유닛/통합 테스트 스위트 없음

이 저장소에는 커밋된 유닛 테스트, 통합 테스트, 테스트 러너 설정이 존재하지 않는다.

확인 근거:
- `frontend/package.json`에 `test` 스크립트 없음. 스크립트는 `dev`/`build`/`lint`/`preview`뿐
- `frontend` devDependencies에 Jest·Vitest·Mocha·Cypress·`@testing-library`·`@playwright/test` 등 테스트 러너가 하나도 없다
- 저장소 어디에도 `*.test.*` / `*.spec.*` / `__tests__/` / `test_*.py` / `conftest.py`가 없다
- `backend/requirements.txt`에 `pytest` 없음 — `fastapi`, `neo4j`, `uvicorn`뿐

품질 검증은 ① ESLint(프론트) ② 수동 Python Playwright UAT 스크립트 ③ 배포 파이프라인 검증 게이트로 이뤄진다.

---

## 로컬 검증 사전 준비 (필수)

`:8080` nginx는 `frontend/dist`를 마운트하며 HMR이 아니다. 소스만 고치면 화면에 반영되지 않는다 — **검증 전 반드시 빌드해야 한다.**

```bash
cd /Users/calmonion/Project/BibleMap/frontend && npm run build
# 백엔드 변경 시
cd .. && docker compose -p biblemap up -d --build api
```

빌드 시 `.env.production`의 `VITE_API_URL=/api`가 자동 적용되어 nginx 프록시(`/api → api:8000`)로 연결된다. API `:8000`은 외부 미노출이므로 직접 curl로는 확인 불가 — nginx 경유 `/api/...`로 접근한다.

- 프론트 `:8080`: `frontend/dist` 마운트 (`docker-compose.yml` nginx 볼륨 `./frontend/dist:/usr/share/nginx/html:ro`)
- API: nginx `/api` 프록시로만 접근
- Neo4j: `127.0.0.1:7474`(브라우저)/`7687`(bolt) 로컬 바인딩

---

## 검증 수단 1 — ESLint (프론트엔드 정적 검사)

프론트엔드에서 자동화된 정적 게이트는 ESLint뿐이다.

설정: `frontend/eslint.config.js` (flat config)
- `@eslint/js` recommended
- `eslint-plugin-react-hooks` (flat.recommended) — 훅 규칙 엄격
- `eslint-plugin-react-refresh` (vite)

```bash
cd frontend && npm run lint   # = eslint .
```

CI(`.github/workflows/deploy.yml`)에서 lint를 별도 스텝으로 호출하지 않는다 — 로컬/수동 실행 도구다.

---

## 검증 수단 2 — Python Playwright UAT 스크립트 (일회성 수동 검증)

프로젝트의 실제 UI·API 검증은 **Python Playwright(sync API)로 작성한 일회성 UAT 스크립트**로 수행한다. 정식 테스트 스위트가 아니라 작업(task)별 수동 수용 검증용이며, 산출물(스크립트 + 스크린샷 + HTML 리포트)이 `.forge/reports/`에 남는다.

현재 `.forge/reports/`에는 `.py` 검증 스크립트 여러 개와 다수의 `.png` 스크린샷이 있다:
`abraham-final.png`, `journey-active-badge.png`, `journey-solomon-full.png`, `adversarial-review-report.html` 등

**프레임워크:** `playwright.sync_api` (Python). 저장소 requirements에 포함되지 않고, 호스트 Homebrew Python에 전역 설치돼 있다:
- 경로: `/opt/homebrew/bin/python3`, `/opt/homebrew/lib/python3.x/site-packages/playwright`
- 기본 `python3`에는 playwright가 없으므로 반드시 Homebrew python으로 실행

**대상:** `http://localhost:8080`. API는 nginx 프록시를 통해 `/api/...`로 접근(`:8000` 직접 노출 없음).

**표준 UAT 스크립트 구조:**

```python
import json, sys, time, urllib.request
from playwright.sync_api import sync_playwright

BASE = "http://localhost:8080"
SS = "/Users/calmonion/Project/BibleMap/.forge/reports/"

def api_get(path):
    with urllib.request.urlopen(f"{BASE}{path}") as r:
        return json.loads(r.read())

# 1) API 계약 검증 — urllib로 /api 엔드포인트 직접 호출해 shape/값 assert
curated = api_get("/api/persons/curated")
assert len(curated) > 0

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

    # 한글 텍스트 로케이터로 요소 확인
    has = page.locator("text=원시사").count() > 0
    page.locator("text=가인").first.click()
    browser.close()

# 3) 결과를 JSON으로 출력(사람이 읽는 요약은 한글)
print(json.dumps(results, ensure_ascii=False, indent=2))
```

**실행:**
```bash
/opt/homebrew/bin/python3 .forge/reports/<script>.py
```

**UAT 관찰 관례:**
- API + UI 이중 검증: `urllib.request`로 `/api/...` JSON 계약 먼저 검사 후 Playwright로 화면 상호작용
- 콘솔·네트워크 오류 수집: `page.on("console", ...)` + `page.on("requestfailed", ...)`
- 로케이터: 한글 `text=` 셀렉터 위주(`page.locator("text=원시사")`). 구조가 불확실하면 `[class*='stop']`처럼 부분 클래스 매칭으로 시도 후 예외를 삼킴
- 뷰포트 분기: 데스크톱(`1280×900`)·모바일(`390×844`) 각각 열어 반응형 확인. 스크린샷 파일명에 `desktop`/`mobile` 접두
- 대기: `wait_until="networkidle"` + 명시적 `time.sleep(1~2)`. 지도(maplibre) 렌더 안정화용
- 스크린샷 증거: 각 단계마다 `.forge/reports/`에 `.png`로 저장. task 번호를 파일명에 부여
- 결과 요약은 한글로 작성, JSON은 `ensure_ascii=False`

---

## 검증 수단 3 — 배포 파이프라인 검증 게이트

`deploy.sh`가 포함하는 런타임 검증:
- 프론트 빌드(`npm run build`) 성공
- API 이미지 빌드 성공
- **한글 이름 주입 스크립트 재시도 게이트** — `backend/scripts/inject_ko_names.py`를 최대 15회(2초 간격) 재시도. 15회 후에도 실패하면 배포 중단(`exit 1`). Neo4j 준비 완료 + 데이터 정합성을 사실상 검증한다

---

## 백엔드 엔드포인트 수동 검증

API는 `:8000` 미노출이므로 curl은 nginx 경유로 한다:

```bash
curl http://localhost:8080/api/persons/curated | python3 -m json.tool | head -30
curl http://localhost:8080/api/person/P-Moses/journey | python3 -m json.tool
curl "http://localhost:8080/api/search?q=아브라함"
```

---

## 테스트 유형별 현황

| 유형 | 상태 |
|------|------|
| 유닛 테스트 | 없음 |
| 통합 테스트 | 없음 |
| E2E/UI 테스트 | 정식 스위트 없음. 일회성 Playwright UAT 스크립트로 대체 (`.forge/reports/*.py`) |
| 정적 분석 | ESLint (프론트만, `npm run lint`) |
| 백엔드 검증 | 배포 시 `inject_ko_names.py` 재시도 게이트 (`deploy.sh`) |
| CI 게이트 | `.github/workflows/deploy.yml` — 배포만 수행, 테스트/lint 스텝 없음 |

---

## 신규 테스트를 추가한다면

정식 러너가 없으므로 새로 도입해야 한다.

**UI/E2E:** 기존 Python Playwright(sync) 패턴을 따르고 `.forge/reports/`에 두거나, 정식화하려면 프론트에 `@playwright/test`를 별도 도입한다. `BASE=http://localhost:8080`, API 계약 검증(`urllib`) + 콘솔/네트워크 오류 수집 + 스크린샷 증거 패턴 유지.

**백엔드 유닛:** `pytest`를 `backend/requirements.txt`에 추가하고 `backend/tests/`에 배치. 우선 대상 순수 함수: `backend/app/overlays.py`의 `_resolve`/`_load`, `backend/app/routes/persons.py`의 `_build_list` 정렬, `backend/app/routes/nodes.py`의 `_year` startDate 파서.

**프론트 유닛:** Vitest 도입 시 검증 가치 높은 순수 로직: `frontend/src/dates.js`의 `parseYear`, `frontend/src/urlState.js`의 `encodeHash`/`parseHash`, `frontend/src/mapGeo.js`의 `placesToGeoJSON`, `frontend/src/theme.js`의 `typeColor`/`typeKo`.
