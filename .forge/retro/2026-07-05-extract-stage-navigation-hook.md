# 2026-07-05 — App.jsx 내비/히스토리 상태 머신을 useStageNavigation 훅으로 추출 (task 124)

## Plan vs actual
- What went as planned: (A) 응집 훅 `frontend/src/useStageNavigation.js` 신설 — 화면 단계 상태·URL/히스토리/딥링크/popstate effect 4개·전환 핸들러 5개·`sheetOpen` 단일 계산 이관, `useNodeSelection`은 미변경·주입만. App.jsx 재배선, line 434 모바일 시트 transform이 훅의 `sheetOpen` 소비(중복 제거). 비목표(여정 fetch·isMobile·verseLang·스와이프·SidePanel 분리·테스트 인프라) 전부 잔류. 검증 Playwright fresh-page 31/31 PASS, build·lint 통과.
- Divergences: 낮음. 코드 verbatim 이동. 딥링크 복원 effect에 `eslint-disable-next-line react-hooks/exhaustive-deps` + 의도 주석 1줄 추가 — 원본 App.jsx가 미억제로 방치한 사전 존재 경고이며, 바로 아래 popstate effect가 같은 이유로 이미 억제 중이라 추출 파일 내 일관성 위해 맞춤(런타임 무영향, 빌드 시 제거).

## Learnings
- Do differently next time:
  - **전역명 섀도잉 크래시 클래스는 사이트별 패치가 아니라 "섀도 유발 이름을 import하지 않는 파일로 코드를 옮기는 구조적 격리"로 근본 해결한다.** task 122의 `new Map()`(lucide `Map` 섀도)·`history.replaceState`(useNodeSelection `history` 배열 섀도) 두 크래시가, 해당 로직을 lucide를 import하지 않고 `history`를 구조분해하지 않는 훅 파일로 옮기자 원천 소멸했다. App에 남은 `window.history.back()` 2곳은 명시적이라 무해. 다음에도 "전역명과 겹치는 import/구조분해" 반복 버그는 파일 경계 격리를 우선 검토. ([[feedback_fix_adjacent_bugs]] 영역이 아니라 구조 리팩터로 예방한 사례.)
  - **순수 구조 리팩터(동작 무변경)의 회귀 하네스는 task 122·123의 검증 도구를 그대로 재사용하면 된다** — fresh-page(해시만 다르면 리로드 안 함 함정 회피)·`history.length` 계측(forward=push vs 토글=replace 구분)·`history.state` 판독·`pageerror`/`console.error` 감시. 31/31로 관측 가능 동작이 동일함을 확인. **인라인 스타일 앱이라 DOM 셀렉터가 약해, stage/view/시트 상태의 단언 축을 DOM이 아니라 `history.state`로 잡은 게 견고했다** — 이 앱의 SPA 내비 회귀 검증 기본 패턴으로 삼을 것. ([[feedback_playwright_testing]] 보강.)
  - **eco 모드에서 단일 파일 응집 리팩터는 Dynamic Workflow가 아니라 직접 실행이 옳다** — S2가 S1에 직렬 의존이라 병렬 여지 0, fragile 코드는 전체 맥락을 쥔 한 에이전트가 일관 편집하는 게 안전·저렴. fg-run 규정("단일 에이전트 규모면 워크플로우 건너뛰기")과 일치.
  - 추출 경계로 (C) 최소(effect만 빼고 상태는 App 잔류)가 아니라 (A) 응집 훅을 고른 판단이 맞았다 — URL 미러는 그것이 반영하는 단계 상태와 한 몸이라, 상태를 두고 effect만 빼면 setter 8개+ 주입으로 인터페이스가 넓고 지저분해진다. "적게 옮기기"가 아니라 "응집 단위로 한 번에"가 에코적으로도 옳다.

## Doc updates
- CONTEXT.md promotion: none — 신규 도메인 용어 없음(화면 단계(Stage)·상세 시트(Detail Sheet) 기존 용어 보존, 훅 이름은 구현 세부).
- ADR added: none — 훅 추출은 되돌리기 쉽고 놀랍지 않으며 ADR-0009(해시 스킴)·ADR-0010(히스토리 통합) 계약을 보존(fg-ask 그릴링에서 이미 "신규 ADR 없음" 확정). 승급 3조건 미충족.
