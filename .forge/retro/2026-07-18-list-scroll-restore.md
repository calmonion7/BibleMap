# 2026-07-18 — 목록(인물·성경책)에서 항목 클릭 후 뒤로 오면 스크롤 위치 복원 (task#214) [일괄 승급]

## Plan vs actual
- What went as planned: 3슬라이스 전부 계획대로. 공유 `scrollMemory.js`(plain object) + PersonHub·BibleOverviewView 캡처(패시브 리스너)+복원(useLayoutEffect). 빌드 통과, Playwright 모바일 4경로(hub·overview × 인앱←/OS뒤로) scrollTop 정확 복원. verified: yes.
- Divergences:
  - **워크플로우 대신 직접 실행** — 프론트 2컴포넌트 + 소형 유틸이라 fg-run 비용 규칙에 따라 Dynamic Workflow 생략.
  - **초기 검증 overview-inapp 거짓 FAIL** — 테스트가 "첫 버튼"을 눌러 뒤로 대신 SpineHeader 버튼 클릭. 셀렉터 교정 후 4경로 PASS. 기능 결함 아님.

## Learnings
- Do differently next time:
  - **SPA 뒤로 상태 복원은 "저장소 선택"이 설계의 핵심.** 인앱 "← 뒤로" 버튼은 popstate가 아니라 전진 push라(ADR-0010) `history.state`로는 인앱 뒤로 시 복원되지 않는다. 모듈 스코프 메모리는 리마운트를 견디고 인앱·OS 뒤로 모두 커버한다. **뒤로 관련 상태 복원 작업은 "그 뒤로가 popstate냐 전진 push냐"를 먼저 판별하고 저장소를 고를 것.**
  - **stage 조건부 렌더 = 언마운트/리마운트.** App.jsx가 `{activeStage === 'x' && ...}`로 stage를 조건부 렌더해 목록 컴포넌트가 이탈 시 언마운트된다 → 컴포넌트 내부 state로는 스크롤·기타 위치를 보존할 수 없다. 세션 유지 상태는 모듈 스코프(예: 기존 `hubEntrancePlayed`)에 둬야 리마운트를 견딘다.
  - **SPA Playwright 검증 함정 재확인** — "첫 버튼(.first)"은 상단 전역 헤더(SpineHeader) 버튼을 집을 수 있어 거짓 FAIL을 낸다. 뒤로 버튼은 `button:has-text("←")` 등으로 정확히 지정하고, **URL 해시로 실제 이동(상세 진입/목록 복귀)을 함께 단언**해야 "복원됐다"가 신뢰 가능하다(무이동 시 before==after 거짓 PASS도 방지).
  - **기존 인프라 재사용이 표면적을 줄였다** — BibleOverviewView는 이미 `scrollRef` + [loading] scroll 리스너가 있어 캡처를 그 리스너에 한 줄 얹고 복원만 추가. 새 ref는 PersonHub에만.

## Doc updates
- CONTEXT.md promotion: 「화면 단계」 절 — **stage 조건부 렌더 = 언마운트/리마운트** 노트 승급(세션 유지 상태는 모듈 스코프 메모리로 + 인앱 뒤로=전진 push라 history.state 복원 불가, ADR-0010 참조). *프론트 화면단계·레이아웃 아크 일괄 승급*으로 #215와 함께 반영.
- ADR added: none (모듈 메모리 선택은 ADR-0010 "인앱 뒤로=전진 push" 귀결의 적용 — 새 트레이드오프 아님, 되돌리기 비용 낮음)
