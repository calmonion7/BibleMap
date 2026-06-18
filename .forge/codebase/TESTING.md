---
last_mapped_commit: 6f2cfc1bf163d7327bd86773676223624fa53ff2
mapped: 2026-06-18
---

# BibleMap 테스트 현황

## 자동화 테스트 없음

현재 코드베이스에 자동화 테스트가 **존재하지 않는다**.

- `frontend/` 디렉터리에 `vitest.config.*`, `jest.config.*`, `*.test.*`, `*.spec.*` 파일 없음
- `backend/` 디렉터리에 `pytest.ini`, `pyproject.toml`, `setup.cfg`, `conftest.py`, `test_*.py`, `*_test.py` 파일 없음
- `frontend/package.json`의 `scripts`에 `test` 항목 없음 (`dev`, `build`, `lint`, `preview`만 존재)
- `backend/requirements.txt`에 `pytest`, `httpx`, `unittest` 등 테스트 라이브러리 미포함 (`fastapi`, `neo4j`, `uvicorn` 3개만)

---

## 수동 검증 패턴 (스크립트 내 인라인)

자동화 테스트 대신, 데이터 생성 스크립트 내부에 **육안 검증 출력** 코드가 삽입되어 있다.

### `backend/scripts/generate_event_verses.py`
스크립트 실행 후 `main()` 끝에서 다권 사건(공관복음 평행 기사) 1건을 찾아 콘솔에 출력:
```
for e in events:
    entry = result[e["id"]]
    if len(entry["books"]) >= 2:
        print(f"[검증] 다권 사건: {e['fields'].get('title')} ...")
        for b in entry["books"]: ...
        break
```

### `backend/scripts/generate_verse_text.py`
스크립트 실행 후 알려진 세 절(창 1:1, 마 9:36, event_verses 첫 사건 첫 절)의 ko/en 본문을 콘솔에 출력해 getbible API 연동 정상 여부를 확인.

---

## 런타임 검증: Playwright (비정기)

`memory/feedback_playwright_testing.md`에 UI 동작 검증 방법이 기록되어 있다:
- 도구: Python Playwright (`/opt/homebrew` 설치)
- 패턴: `localhost:8080` 대상 네트워크 캡처 + 스크린샷
- 선행 조건: 프론트 `cd frontend && npm run build` 후 `docker compose up -d --build api`

이 검증은 스크립트화된 자동화 슈트가 아니라 특정 변경사항 확인 시 1회성으로 수행한다.

---

## 테스트 미적용 현황 요약

| 영역 | 상태 |
|------|------|
| 프론트엔드 단위 테스트 (Vitest/Jest) | 없음 |
| 프론트엔드 E2E (Playwright CI) | 없음 (수동 1회성만) |
| 백엔드 단위 테스트 (pytest) | 없음 |
| 백엔드 통합 테스트 (FastAPI TestClient) | 없음 |
| CI 파이프라인 | 없음 (`.github/` 없음) |

---

## 빌드 검증 방법 (현재 운용 중)

테스트 대신 아래 절차로 변경사항을 검증한다 (`memory/project_local_verify_build.md` 참조):

1. 프론트엔드 빌드: `cd frontend && npm run build` (`.env.production`의 `VITE_API_URL=/api` 자동 적용)
2. API 재빌드: `docker compose up -d --build api`
3. Playwright로 `localhost:8080` 수동 스크린샷 확인

린트 검사: `cd frontend && npm run lint` (ESLint, `eslint.config.js` 기준)
