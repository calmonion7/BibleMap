# 2026-06-11 — 프론트엔드 fetch 실패 시 에러 UI 추가 (task 10)

## 계획 vs 실제

- 계획대로 간 것:
  - 4개 슬라이스(App 검색 / TimelineView / MapView / GraphView) 모두 구현. SidePanel 패턴(로컬 `error` `useState` + 조건부 인라인 렌더)으로 일관, `r.ok` 검증을 4곳 모두 `r.ok ? r.json() : Promise.reject(...)`로 통일.
  - 비목표 준수: 로딩 스피너·재시도 버튼·공유 토스트·전역 상태 도입 안 함, SidePanel 미변경, raw status 비노출.
  - 검증: eslint 내 변경분 0 신규, vite build green, 브라우저 런타임(백엔드 차단)으로 검색/연표/그래프 에러 메시지 실표시 + 지도 배너 표시·해제 확인.
- 발산:
  1. **eslint-plugin-react-hooks v7 caret 범프로 신규 룰 `react-hooks/set-state-in-effect` 발동.** 계획 완료기준 "lint clean"이 pristine HEAD에서도 `SidePanel.jsx:26`(기존 코드)로 이미 1건 실패 중이었음 — 직전 회고의 "eslint clean"은 범프 이전 기준. 내 작업 무관 환경 드리프트.
  2. **처음엔 SidePanel의 기존 패턴(effect 본문 동기 `setError(false)`)을 그대로 따라** MapView/GraphView에 넣어 신규 lint 2건 추가됨 → `setError(false)` 리셋을 async 콜백(`.then` 성공 / `.catch`)으로 이동해 신규 0건으로 정리. 결과: 내 변경분 0 신규, 기존 SidePanel 1건만 잔존.
  3. **MapView 렌더 가드 `selectedNode &&` 추가**(계획 외, 실행 중 결정). 동기 리셋 제거로 선택 해제 시 배너 잔존 가능 → `{error && selectedNode && ...}`로 해소.
  4. **MapView fetch→catch 경로는 런타임 미실행 검증.** 프리뷰 샌드박스가 외부 타일/폰트 서버(protomaps·ArcGIS)를 차단 → maplibre `load` 미발동 → `mapLoaded=false`·`mapRef.current=null` → places fetch 자체가 안 일어남. 나머지 3뷰와 동일 관용구 + 빌드 통과로 구조 보증, 렌더 가드만 fiber 상태 주입으로 직접 검증.

## 학습

- 다음에 다르게 할 것:
  1. **"lint clean"을 완료기준으로 쓸 땐 pristine HEAD의 lint 베이스라인을 먼저 확인할 것.** 린트 플러그인이 caret(`^`) 범위면 조용히 범프돼 기존 통과 코드가 깨질 수 있다(여기선 react-hooks v7의 `set-state-in-effect`). cleanup/품질 계획의 완료기준은 절대값 "clean"보다 **"내 변경분 무신규 에러"**가 견고하다. 기존 위반은 별도 후속으로 분리.
  2. **코드베이스 기존 패턴을 따랐다고 lint-safe가 아니다.** SidePanel의 "effect 본문 동기 setState" fetch 패턴은 react-hooks v7에서 위반이다. 같은 비동기 fetch-in-effect라면 상태 리셋을 **effect 본문이 아니라 `.then`/`.catch` 비동기 콜백**에 두는 게 새 룰과 호환된다.
  3. **외부 서비스에 게이트된 컴포넌트는 무네트워크 샌드박스에서 내부 로직이 도달 불가일 수 있다.** MapView는 maplibre `load`(외부 타일) 없이는 fetch 경로 진입조차 안 된다. 이런 컴포넌트의 에러 경로는 (a) 동일 관용구의 다른 뷰로 구조 보증 + (b) 렌더 상태 직접 주입으로 가드만 검증, 으로 나눠 접근. (직전 `map-marker-label-ux`·`graphview-uat-bugfix` 회고의 "런타임에서만 검증 가능" 결과 연장선.)
  4. fiber 상태 주입(`__reactContainer$` → BFS로 컴포넌트 fiber → `hook.queue.dispatch`)은 백엔드 없이 React 상태 의존 UI를 검증하는 유효한 수단. 다만 hook 순서 의존이라 fragile — 검증 한정 용도.

## 문서 업데이트

- CONTEXT.md 승격: 없음 (새 도메인 용어 없음 — 전부 구현/프로세스 디테일, 글로서리 오염 방지).
- ADR 추가: 없음 (react-hooks 룰 처리 방침은 미결 후속이라 박을 결정이 없음; 스코핑 결정은 가역적·비아키텍처).

## 후속 (이번 범위 밖)
- **SidePanel.jsx 기존 lint 위반 + react-hooks v7 룰 정책 결정.** `react-hooks/set-state-in-effect`가 코드베이스 기존 fetch-in-effect 패턴(SidePanel)을 깬다. 플러그인 caret 범프가 원인. 선택지 — (a) SidePanel 등 effect를 async-콜백 리셋으로 리팩터, (b) 룰 다운그레이드/플러그인 핀. 프로젝트 전역 정책 → fg-quick(핀) 또는 fg-ask(정책 결정)로 처리 권장.
