# 2026-06-13 — 검색 UI/UX 개선 (실시간·키보드·닫기/지우기·관련도 정렬·타입 칩)

## 계획 vs 실제
- 계획대로 간 것: 4슬라이스 전부 계획대로. S1 백엔드 `CASE` 관련도 정렬, S2 디바운스 실시간 검색+키보드+닫기/지우기, S3 타입 필터 칩+팔레트, S4 데스크톱·모바일 Playwright 검증. 질문 2의 (가) 평면 랭킹+칩 구조 그대로. eslint 0 / vite build / py OK.
- 발산: 구현/검증 디테일 수준(아래 학습). 목표·구조 이탈 없음 → 재그릴링 불필요.

## 학습
- 다음에 다르게 할 것:
  - **백엔드는 hot-reload가 아니다 — 로컬 검증 전 api 재빌드 필요.** `docker-compose.yml`의 `api`는 `build: ./backend`(소스 마운트/`--reload` 없음). `search.py`를 고쳐도 실행 컨테이너에 자동 반영 안 됨 → `docker compose up -d --build api` 후에야 `localhost:8080/api`에 반영된다. 자동배포는 `deploy.sh [2/3] docker compose build api`로 재빌드하므로 push 후엔 정상 반영(검증함). **앞으로 백엔드를 건드리는 작업의 검증 단계는 "api 재빌드"를 반드시 포함.** (프론트는 dist 바인드마운트라 `vite build`만으로 즉시.)
  - **react-hooks v7 `set-state-in-effect` 회피 패턴(재적용).** 실시간 검색 effect의 setState를 전부 `setTimeout`/async 콜백 안에서만 호출하고, 빈 입력 즉시 클리어는 effect 동기 본문이 아니라 `onChange` 이벤트 핸들러에서 처리 → effect 동기 본문에 setState 0개. SidePanel 때 배운 규율을 검색에도 그대로 적용해 한 번에 lint clean.
  - **검증 함정 — 한글 URL은 percent-encode 필수.** `curl '.../search?q=다윗'`처럼 한글을 인코딩 없이 넣으면 HTTP 400 "Invalid HTTP request"(요청라인 비-ASCII 거부). `--data-urlencode`/`urllib.parse.quote` 사용. 브라우저·Playwright는 자동 인코딩.
  - 검색 드롭다운은 **순수 DOM**이라 지도 타일(헤드리스 렌더 불안정)과 달리 Playwright 검증이 안정적 — map 작업보다 수월.

## 문서 업데이트
- CONTEXT.md 승급: 없음 (실시간 검색·타입 칩·관련도 정렬은 UI 구현 용어 — 도메인 용어 아님)
- ADR 추가: 없음 (평면+칩 ↔ 그룹 전환 가능·정렬 방식 가변 — 되돌리기 어려운 결정 아님)
