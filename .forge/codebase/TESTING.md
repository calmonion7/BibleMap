---
last_mapped_commit: 7a1ef362b1fb247b09edeeaa1380e6449fce5721
mapped: 2026-06-20
---

# TESTING.md — 테스트 및 검증 방식

구현 사실 기록. 도메인 용어 정의는 CONTEXT.md 참조.

---

## 테스트 프레임워크 현황

- **테스트 파일 없음**: `*.test.*`, `*.spec.*`, `test_*.py`, `conftest.py` 하나도 없음.
- `frontend/package.json` scripts: `dev`, `build`, `lint`, `preview` — `test` 스크립트 없음.
- `backend/requirements.txt`: `fastapi`, `neo4j`, `uvicorn` — pytest 없음.
- Jest, Vitest, pytest 등 테스팅 프레임워크 미설치.

---

## 정적 분석 (ESLint)

- 설정 파일: `frontend/eslint.config.js`.
- 사용 플러그인: `eslint-plugin-react-hooks`, `eslint-plugin-react-refresh`.
- 실행 명령: `cd frontend && npm run lint`.
- 빌드 전 "lint clean" 확인이 PR 체크리스트 항목. 모든 태스크 완료 전 필수.

---

## Python Playwright 검증

- 설치 위치: `/opt/homebrew/bin/playwright` (Python Playwright).
- 공식 테스트 파일 없음 — forge 워크플로우의 **검증 단계**에서 일회성 스크립트로 작성·실행.
- 검증 대상 URL: `http://localhost:8080` (nginx → `frontend/dist` 서빙).

### 검증 패턴
- 네트워크 캡처 + 스크린샷으로 UI 동작 확인.
- 검색 드롭다운 (순수 DOM): Playwright 검증 안정적.
- 지도 타일 (WebGL): 헤드리스 렌더 불안정 — 스크린샷 검증 대신 네트워크 요청 확인으로 우회.
- 모바일 시뮬레이션: `page.set_viewport_size({"width": 375, "height": 812})` 로 `window.innerWidth <= 768` 분기 검증.

### UAT 항목 예시 (retro 기록 기준)
- 검색: 실시간 검색 응답, 키보드 탐색, 타입 필터, 모바일 레이아웃.
- 지도: 마커 클릭, 스파이더파이 전개, 클러스터 확장, 링 애니메이션.
- 구절 본문: 언어별(한/영) 렌더링, 공유 토글.
- 콘솔 에러 0건 확인.

---

## 빌드 검증 절차

forge 워크플로우 검증 단계에서 확립된 순서:

1. **lint 확인**: `cd frontend && npm run lint` — 통과 필수.
2. **프론트 빌드**: `cd frontend && npm run build` → `frontend/dist/` 갱신 (HMR 아님, nginx가 dist를 정적 서빙).
3. **백엔드 빌드**: `docker compose up -d --build api` (소스 마운트 아님 — hot-reload 없음).
4. **Playwright 검증**: `localhost:8080`에서 실제 동작 확인.

### 환경변수 참고
- 빌드 시 `.env.production`의 `VITE_API_URL=/api` 자동 적용.
- 백엔드 API는 외부에서 `:8000` 미노출 — nginx `/api` 프록시 경유.

---

## 배포 자동화 (`deploy.sh`)

- 테스트 단계 없음. 배포 자동화만 담당.
- 실행 순서: 프론트 빌드 → api 빌드 → 컨테이너 재시작 → 한글 이름 주입.
