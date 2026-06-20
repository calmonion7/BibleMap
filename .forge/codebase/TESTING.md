---
last_mapped_commit: 7522aafe2088e83e8c4bed86a4f0269082db07e0
mapped: 2026-06-20
---

# 테스트 패턴

## 공식 테스트 프레임워크

**자동화 테스트 프레임워크 없음.** `package.json`에 테스트 스크립트(`test`) 미정의. Jest/Vitest/pytest 설정 파일 없음. 테스트 파일(`*.test.*`, `*.spec.*`, `test_*.py`) 없음.

---

## 검증 접근법

공식 단위 테스트 대신 두 가지 수동·반자동 검증을 사용한다.

### 1. Playwright 브라우저 검증 (UI 동작 검증)

UI 동작을 검증할 때 **Python Playwright**를 사용한다. `/opt/homebrew`에 설치되어 있다.

**패턴**: 네트워크 캡처 + 스크린샷 방식으로 `localhost:8080`을 검증한다.

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()

    # 네트워크 요청 캡처
    captured = []
    page.on('request', lambda req: captured.append(req.url))

    page.goto('http://localhost:8080')
    page.wait_for_timeout(2000)

    # 스크린샷으로 시각 확인
    page.screenshot(path='screenshot.png')
    browser.close()
```

**사전 조건**: 검증 전 반드시 빌드 후 컨테이너 기동.
```bash
cd frontend && npm run build
docker compose up -d --build api
```

프론트엔드는 `frontend/dist`를 nginx로 서빙(HMR 없음). 백엔드 API는 포트 8000 미노출, nginx 프록시(`/api → api:8000`)를 통해서만 접근.

### 2. 수동 Neo4j 쿼리 검증

데이터 적재·변환 스크립트 실행 후 Neo4j Bolt(`localhost:7687`)에 직접 Cypher 쿼리를 실행해 결과를 확인한다.

---

## 빌드 검증 (lint)

테스트 대신 **ESLint**로 코드 품질을 게이트한다.

```bash
# 프론트엔드 lint 실행
cd frontend && npm run lint
```

ESLint 설정 파일: `frontend/eslint.config.js`
- `@eslint/js` recommended
- `eslint-plugin-react-hooks` (hooks 규칙 강제)
- `eslint-plugin-react-refresh` (Vite 호환)
- 대상: `**/*.{js,jsx}`

lint clean 상태가 커밋 기준. "lint clean" 유지가 암묵적 품질 목표.

---

## 테스트 없는 영역과 검증 전략

| 영역 | 검증 방법 |
|------|-----------|
| 프론트엔드 UI 동작 | Playwright 스크린샷 + 네트워크 캡처 |
| 프론트엔드 코드 스타일 | ESLint (`npm run lint`) |
| 백엔드 API 응답 | curl / 브라우저 직접 호출 또는 Playwright 네트워크 캡처 |
| 데이터 적재 스크립트 | Neo4j Cypher 쿼리로 노드·관계 수 직접 확인 |
| 유틸리티 함수 (`convexHull.js` 등) | 별도 테스트 없음 |

---

## 커버리지

측정하지 않는다. 커버리지 수집 도구 미설치.

---

## Playwright 설치 위치

```
/opt/homebrew/  (macOS)
```

실행 시 Python 경로를 명시적으로 지정하거나 Homebrew Python 환경에서 실행.

---

## 향후 테스트 추가 시 고려사항

- 프론트엔드: Vitest(Vite 환경과 통합 용이, 설정 최소화) 적합. Jest는 ESM 설정 부담 있음.
- 백엔드: pytest + httpx(`AsyncClient`)로 FastAPI 라우터 통합 테스트 가능. `pyproject.toml` 없으므로 `pytest.ini` 또는 `setup.cfg`로 시작.
- 테스트 파일 위치: 프론트엔드는 `frontend/src/` 하위 co-located(`*.test.js`), 백엔드는 `backend/tests/` 별도 디렉터리 권장.
