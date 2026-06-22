---
last_mapped_commit: a25a3a3a9f5473c35aabd6036398d6bb672fee47
mapped: 2026-06-22
---

# TESTING.md — 테스트 및 검증 방식

구현 사실 기록. 도메인 용어 정의는 CONTEXT.md 참조.

---

## 테스트 프레임워크 현황

- **자동화 테스트 프레임워크·테스트 파일 없음**: 레포 전체에 `*.test.*`, `*.spec.*`, `test_*.py`, `conftest.py` 하나도 없음(node_modules 제외, 재확인됨).
- `frontend/package.json` scripts: `dev`, `build`, `lint`, `preview` — `test` 스크립트 없음.
- `backend/requirements.txt`: `fastapi==0.136.3`, `neo4j==6.2.0`, `uvicorn==0.49.0` — pytest 없음.
- Jest, Vitest, pytest 등 테스팅 프레임워크 미설치.
- 검증은 전부 수동: 빌드 → nginx 서빙(`localhost:8080`) → Python Playwright 일회성 스크립트.

---

## 정적 분석 (ESLint)

- 설정 파일: `frontend/eslint.config.js`(flat config).
- extends: `@eslint/js` recommended, `eslint-plugin-react-hooks`(flat recommended), `eslint-plugin-react-refresh`(vite).
- `globalIgnores(['dist'])` — 빌드 산출물 제외. 대상: `**/*.{js,jsx}`.
- 실행 명령: `cd frontend && npm run lint`(`eslint .`).
- react-hooks v7 규칙이 켜져 있어 effect 동기 본문 `setState`를 막음 — 코드 패턴 제약으로 작용(`useSearch.js` 참조).
- 빌드 전 "lint clean" 확인이 PR 체크리스트 항목. 모든 태스크 완료 전 필수.

---

## Python Playwright 검증

- 설치 위치: `/opt/homebrew`(Python Playwright).
- 공식 테스트 파일 없음 — forge 워크플로우의 **검증 단계**에서 일회성 스크립트로 작성·실행.
- 작성된 검증 스크립트·스크린샷은 `.forge/reports/`에 임시로 남음(예: `task70_verify.py`, `task_place_context_verify.py`, `task_place_dom_probe.py`, `task83-A-ring-expanded.png`) — 정식 테스트 스위트 아님, 태스크별 일회성.
- 검증 대상 URL: `http://localhost:8080`(nginx → `frontend/dist` 정적 서빙).

### 검증 패턴
- 네트워크 캡처 + 스크린샷으로 UI 동작 확인.
- 검색 드롭다운(순수 DOM): Playwright 검증 안정적.
- 지도 타일(WebGL): 헤드리스 렌더 불안정 — 스크린샷 검증 대신 네트워크 요청 확인으로 우회.
- 모바일 시뮬레이션: `page.set_viewport_size({"width": 375, "height": 812})` 로 `MOBILE_BREAKPOINT`(768px) 분기 검증.

### UAT 항목 예시 (retro 기록 기준)
- 검색: 실시간 검색 응답, 키보드 탐색, 타입 필터, 모바일 레이아웃.
- 지도: 마커 클릭, 스파이더파이 전개, 클러스터 확장, 링 애니메이션, 라벨 바깥쪽 배치, outlier 제외 프레이밍, 팝업 XSS 이스케이프, 링 fetch 실패 배너.
- 구절 본문: 언어별(한/영) 렌더링, 공유 토글.
- 콘솔 에러 0건 확인.

---

## 빌드 검증 절차

forge 워크플로우 검증 단계에서 확립된 순서:

1. **lint 확인**: `cd frontend && npm run lint` — 통과 필수.
2. **프론트 빌드**: `cd frontend && npm run build` → `frontend/dist/` 갱신(HMR 아님, nginx가 dist를 정적 서빙).
3. **백엔드 빌드**: `docker compose up -d --build api`(소스 마운트 아님 — hot-reload 없음).
4. **Playwright 검증**: `localhost:8080`에서 실제 동작 확인.

### 환경변수 참고
- 빌드 시 `frontend/.env.production`의 `VITE_API_URL=/api` 자동 적용.
- 백엔드 API는 외부에서 `:8000` 미노출 — nginx `/api` 프록시 경유.

---

## 배포 자동화 (`deploy.sh`)

- 테스트 단계 없음. 배포 자동화만 담당.
- 실행 순서: 프론트 빌드(`npm install` → `npm run build`) → api 이미지 빌드 → 컨테이너(api·nginx) 재시작 → 한글 이름 주입(`inject_ko_names.py`, Neo4j 준비까지 최대 15회 재시도).
- lock 파일(`/tmp/biblemap-deploy.lock`)로 중복 실행 차단. 한글 주입 15회 실패 시 배포 중단(exit 1).
