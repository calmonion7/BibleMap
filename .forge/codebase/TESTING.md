---
last_mapped_commit: 3837b4f9339ed2efb82a6b72cc1124a3340e2b9c
mapped: 2026-06-27
---

# TESTING.md — 테스트 및 검증 방식

구현 사실 기록. 도메인 용어 정의는 CONTEXT.md 참조.

---

## 테스트 프레임워크 현황

- **자동화 유닛/통합 테스트 프레임워크·테스트 파일 없음**: 레포 전체에 `*.test.*`, `*.spec.*`, `test_*.py`, `conftest.py` 하나도 없음(node_modules 제외, 재확인됨).
- `frontend/package.json` scripts: `dev`, `build`, `lint`, `preview` — `test` 스크립트 없음. Jest/Vitest 미설치.
- `backend/requirements.txt`: `fastapi`, `neo4j`, `uvicorn`, `anthropic` 등 런타임 의존성만 — pytest 없음.
- 검증은 전부 수동 3종 조합: **ESLint(`npm run lint`) → 빌드(`npm run build`) → Python Playwright 일회성 검증(`localhost:8080`)**.

---

## 정적 분석 (ESLint)

- 설정 파일: `frontend/eslint.config.js`(flat config, `defineConfig` + `globalIgnores`).
- extends: `@eslint/js` recommended, `eslint-plugin-react-hooks`(`reactHooks.configs.flat.recommended`), `eslint-plugin-react-refresh`(`reactRefresh.configs.vite`).
- `globalIgnores(['dist'])` — 빌드 산출물 제외. 대상: `**/*.{js,jsx}`. `languageOptions.globals = globals.browser`.
- 실행 명령: `cd frontend && npm run lint`(`eslint .`).
- **react-hooks v7 규칙이 켜져 있어 effect 동기 본문 `setState`를 막음** — 코드 패턴 제약으로 작용한다. 회피 패턴은 CONVENTIONS.md "Hooks 패턴" 참조(async `.then` 콜백, `Promise.resolve().then(...)` 마이크로태스크, `setTimeout`). 실제로 직전 커밋 `85b1163`이 이 규칙 위반 2건(effect 동기 setState → 마이크로태스크, unused label 제거)을 lint 픽스로 처리.
- 빌드 전 "lint clean" 확인이 PR 체크리스트 항목. 모든 태스크 완료 전 필수.
- 백엔드(Python)용 린터·포매터 설정 파일은 없음.

---

## Python Playwright 수동 검증

- 설치 위치: `/opt/homebrew`(Python Playwright). 공식 테스트 파일 없음 — forge 워크플로우의 **검증 단계**에서 일회성 스크립트로 작성·실행.
- 작성된 검증 스크립트·스크린샷은 `.forge/reports/`에 임시로 남음(태스크별 일회성, 정식 테스트 스위트 아님).
- 검증 대상 URL: `http://localhost:8080`(nginx → `frontend/dist` 정적 서빙).

### 검증 패턴
- 네트워크 캡처 + 스크린샷으로 UI 동작 확인.
- 순수 DOM 영역(인물 허브 카드 그리드, 검색 드롭다운, 여정 사이드 리스트): Playwright 스크린샷·클릭 검증 안정적.
- 지도 타일(WebGL): 헤드리스 렌더 불안정 — 스크린샷 검증 대신 네트워크 요청 확인으로 우회.
- 모바일 시뮬레이션: `page.set_viewport_size({"width": 375, "height": 812})` 로 `MOBILE_BREAKPOINT`(768px) 분기 검증(허브 헤더 패딩, 하단 시트 패널, 모바일 여정 미니 수평 스크롤).

### UAT 항목 예시 (화면 단계별)
- 인물 허브(`'hub'`): `/persons/curated` 응답, 시대별 카드 그룹핑, 카드 클릭→탐험 전환, "성경 책 둘러보기" 버튼→개요 진입.
- 탐험(`'explore'`): 인물 선택 후 여정(`/person/{id}/journey`) 로드, JourneyList 항목 클릭→해당 stop 활성, 지도·타임라인 토글, "다른 인물" 복귀.
- 지도: 마커 클릭, 스파이더파이 전개, 클러스터 확장, 링 애니메이션, 라벨 바깥쪽 배치, outlier 제외 프레이밍, 팝업 XSS 이스케이프, 링 fetch 실패 배너.
- 장소 패널: "이 곳을 지난 다른 인물"(`/place/{id}/curated-persons?exclude=`) 칩 클릭→인물 전환.
- 구절 본문: 언어별(한/영) 렌더링, 공유 토글.
- 콘솔 에러 0건 확인.

---

## 빌드 검증 절차

forge 워크플로우 검증 단계에서 확립된 순서:

1. **lint 확인**: `cd frontend && npm run lint` — 통과 필수.
2. **프론트 빌드**: `cd frontend && npm run build` → `frontend/dist/` 갱신. **HMR 아님** — nginx가 `dist`를 정적 서빙(`docker-compose.yml`이 `./frontend/dist:/usr/share/nginx/html:ro` 마운트)하므로 빌드 없이는 화면이 안 바뀜.
3. **백엔드 빌드**: `docker compose up -d --build api`. **소스 마운트 아님 → hot-reload 없음**(`docker-compose.yml` api 서비스는 `build: ./backend`만, 코드 볼륨 마운트는 `./data:/app/data` 데이터뿐). 백엔드 코드를 고치면 반드시 `--build`로 이미지 재빌드해야 반영된다.
4. **Playwright 검증**: `localhost:8080`에서 실제 동작 확인.

### 환경변수 참고
- 빌드 시 `frontend/.env.production`의 `VITE_API_URL=/api` 자동 적용.
- 백엔드 API는 외부에서 `:8000` 미노출 — nginx `/api` 프록시 경유(`nginx/nginx.conf`).
- Neo4j는 `127.0.0.1:7687`(bolt)/`:7474`(http)로 호스트 로컬바인드 — 호스트에서 직접 쿼리 가능. `NEO4J_PASSWORD` 환경변수 필수(미설정 시 compose·드라이버 모두 에러).

---

## 배포 자동화 (`deploy.sh`)

- 테스트 단계 없음. 배포 자동화만 담당.
- 실행 순서: 프론트 빌드(`npm install` → `npm run build`) → api 이미지 빌드 → 컨테이너(api·nginx) 재시작 → 한글 이름 주입(`inject_ko_names.py`, Neo4j 준비까지 최대 15회 재시도).
- lock 파일(`/tmp/biblemap-deploy.lock`)로 중복 실행 차단. 한글 주입 15회 실패 시 배포 중단(exit 1).
- CI: `.github/workflows/deploy.yml`(self-hosted 러너 전제) — 멀티프로젝트 러너 격리 주의사항은 사용자 글로벌 메모리 참조.
