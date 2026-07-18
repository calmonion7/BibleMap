# 2026-07-18 — 장 묶음 저작(task#212): 다장권 61권 연속 묶음 + 목차 헤더 UI

## Plan vs actual
- What went as planned: 3슬라이스 전부 계획대로 산출·배포·검증. 다장권 61권 281묶음(연속·전수·비중첩) 저작, `validate_chapter_sections.py` 불변식 전수 검증 PASS(탈락 0), 본문 리더 목차에 묶음 헤더(제목+"N–M장") 렌더. 단장권 5권은 non-goal대로 묶음 미저작→평면 폴백. 저작 연료로 task#206 장 개요를 재사용해 서사 전환점에서 경계를 그음. "저작↔검증 분리" 패턴 유지.
- Divergences:
  1. **[중대] S1 저작 절반이 워크플로가 아니라 메인 세션에서 이뤄짐.** 61-에이전트 Dynamic Workflow(sonnet)가 실행 중 계정 **사용량 한도**(5:20am KST 리셋)에 걸려 12권만 서브에이전트 저작·49권 실패. 재-fanout이 같은 한도에 다시 걸릴 위험(직전 런 110에이전트·565k토큰)이 커서 나머지 49권을 메인 세션이 직접 저작. **불변식은 저자 무관하게 validate 스크립트가 61권 전수 보증** → 산출물 DoD 충족.
  2. **[경미] Workflow `args`가 파싱된 배열이 아니라 JSON 문자열로 스크립트에 도달** → `pipeline() expects an array` 즉시 실패(에이전트 0). 방어 파싱 후 재실행으로 해소.
  3. **[경미] eco 적용 조정** — ECO.md(코드 단순화 규율)를 콘텐츠 저작 에이전트에 전문 prepend은 오도 소지 → 모델 캡(sonnet)+짧은 "JSON만 반환" 지시로 갈음.

## Learnings
- Do differently next time:
  - **대규모 콘텐츠 fan-out은 계정 사용량 한도를 중간에 소진할 수 있다.** 60+ sonnet 에이전트를 한 워크플로로 돌리면 런당 수십만 토큰이라 세션 한도에 걸려 후반부가 통째로 실패한다. 대안: (a) 동시성/웨이브를 잘게 쪼개 배치, 또는 (b) 메인 세션 결정론적 폴백을 처음부터 준비. **이번엔 validate 스크립트가 기계 게이트라 저자 혼합(에이전트 12 + 메인 49)에도 품질이 보증됐다** — 저작↔검증 분리 구도의 실전 이점. 데이터 저작 계획 땐 "한도 초과 시 메인 세션이 이어 쓰고 validator가 보증한다"를 기본 회복 경로로 둘 것.
  - **Workflow `args`는 스크립트에서 JSON 문자열로 올 수 있다.** 재사용 워크플로 첫 줄에 `const X = Array.isArray(args) ? args : JSON.parse(args)` 방어 파싱을 관용으로. `pipeline(args, …)` 직접 사용 금지.
  - **fg-run eco 주입(ECO.md prepend)은 코드 서브에이전트 전제다.** 콘텐츠 저작 에이전트엔 모델 캡(sonnet) + 산출 형식 지시(JSON only)만 적용하는 게 맞다.
  - 워크플로 부분 실패 시 성공분은 output 파일 `result`에서 회수해 재사용(재저작 낭비 방지). 성공/실패 분리→저작→병합→검증 순.

## Doc updates
- CONTEXT.md promotion: none (새 도메인 용어 없음 — `장 묶음`은 fg-ask 때 이미 추가·집행 중, 의미 변화 없음)
- ADR added: none (divergence는 프로젝트 도메인 결정이 아니라 forge 워크플로 사용 교훈 — 되돌리기·트레이드오프 조건 미충족. 회고 로그로 충분)
