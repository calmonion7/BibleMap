---
last_mapped_commit: 9f47b78ed927ef302cefffb5b62ef71885b6aa94
mapped: 2026-06-19
---

# BibleMap 테스트 현황

## 테스트 프레임워크

**자동화 테스트 없음.** `package.json`에 test 스크립트 미선언. `pytest`, `unittest`, `vitest`, `jest` 등 테스트 러너 미설치.

- `frontend/package.json` 스크립트: `dev`, `build`, `lint`, `preview` 4개만.
- `backend/requirements.txt`: `fastapi`, `neo4j`, `uvicorn` 3개만(테스트 라이브러리 없음).

## 수동 검증 패턴

### 스크립트 내장 육안 검증

데이터 생성 스크립트(`backend/scripts/`)가 실행 끝에 알려진 값을 출력해 육안으로 확인하는 패턴이 공통으로 사용된다.

- `generate_event_verses.py` 끝: 다권 사건 1건을 출력해 bookId·bookOrder·rangeLabel·절 수 확인.
- `generate_verse_text.py` 끝: `창 1:1` ko/en, `마 9:36` ko/en, 첫 사건 첫 절 ko/en을 출력.
- 이 패턴은 CI에서 자동으로 실행되지 않으며 개발자가 직접 출력을 확인한다.

### Playwright 화면 테스트

메모리(`MEMORY.md`)에 따르면 Python Playwright가 `/opt/homebrew`에 설치돼 있고, UI 동작 검증 시 사용한다.

- 검증 대상: `localhost:8080` (nginx 서빙 `frontend/dist`).
- 패턴: 네트워크 캡처 + 스크린샷 조합.
- 사전 조건: `cd frontend && npm run build`로 `dist` 갱신 후 `docker compose up -d --build api` 실행.

## 린트

- `frontend/eslint.config.js`: `@eslint/js` 권장 규칙 + `eslint-plugin-react-hooks` + `eslint-plugin-react-refresh`.
- `eslint-plugin-react-hooks`의 `flat.recommended`로 exhaustive-deps 등 React hooks 규칙 적용.
- 실행: `cd frontend && npm run lint`.
- 백엔드 린트 도구 미설치(flake8·ruff·mypy 없음).

## 커버리지

자동화 테스트가 없으므로 커버리지 측정 없음.

## 검증이 필요한 코드 경로

스크립트에 육안 검증이 내장된 경로:

| 파일 | 검증 대상 |
|------|-----------|
| `backend/scripts/generate_event_verses.py` | 다권 사건 rangeLabel, bookOrder 정렬 |
| `backend/scripts/generate_verse_text.py` | getbible API 절 본문 ko/en 정합성 |
| `backend/scripts/inject_ko_names.py` | Neo4j nodes updated 카운트 출력 |
| `backend/scripts/load_theographic.py` | 각 로드 함수 완료 로그 |

## 주요 부재 사항

- 단위 테스트: `build_range_label()`(구절 범위 접기), `convexHull()`(Graham scan) 등 순수 함수에 단위 테스트 없음.
- API 통합 테스트: FastAPI `TestClient` 미사용. `/events`, `/node/{id}`, `/search` 엔드포인트 자동 검증 없음.
- E2E 테스트: Playwright가 설치돼 있으나 테스트 파일·스크립트 없음(임시 수동 실행만).
- CI 파이프라인: `.github/workflows/deploy.yml`은 배포만 수행. 테스트 스텝 없음.
