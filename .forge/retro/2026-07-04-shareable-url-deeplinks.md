# 2026-07-04 — 공유·북마크용 해시 기반 딥링크 (URL↔내비 상태 동기화)

## Plan vs actual
- What went as planned: `urlState.js`(순수 encode/parse) + `App.jsx` 배선(id↔slug 맵·로드 1회 복원·복원 후 `replaceState` 반영). 범위 B 준수(뒤로가기 통합·selectedNode/verseLang·경로기반·라우터 전부 미착수). 모바일 Playwright fresh-page 5/5 통과. ADR-0009대로.
- Divergences (중간): 실행 중 런타임 크래시 2건 + UAT 방법 함정을 잡고 넘어감(아래 학습).

## Learnings
- Do differently next time:
  - **`App.jsx`에서 전역 `Map`·`history`가 가려져 있다 — 새 코드에서 `new Map()`/`history.*`를 그냥 쓰면 크래시.** ① `import { Map, Clock, BookOpen } from 'lucide-react'`가 전역 `Map`을 섀도 → `new Map()`이 아이콘 컴포넌트를 `new` 호출 → "r is not a constructor"로 앱 전체 블랙(미니파이돼 원인 파악 어려움, 소스맵 스택으로 `Ae`=App 특정). plain object(`{}`+`Object.fromEntries`)나 `globalThis.Map` 사용. ② line 33에서 `useNodeSelection`의 `history`(배열)를 구조분해 → 전역 `history` 가려짐 → `window.history.replaceState` 명시. 두 지점에 함정 주석 남김. **App.jsx에 전역명과 겹치는 import/구조분해가 있는지 먼저 확인할 것.**
  - **SPA 해시 라우팅 검증은 시나리오마다 새 페이지(fresh mount)로.** `pg.goto`는 **해시만 다르면 페이지를 리로드하지 않아**(브라우저 표준), 같은 페이지에서 `goto('...#/books')`하면 이전 상태가 잔류해 **거짓 통과**한다. 딥링크 "직접 진입/새 탭 열기"의 실제 복원을 검증하려면 `browser.new_page()`로 매번 fresh mount. ([[feedback_playwright_testing]] 보강.)
  - 미니파이 런타임 크래시는 `vite build --sourcemap true` + Playwright `pageerror` 스택으로 컴포넌트(minified 함수명)까지 특정 가능 — 블랙 페이지 디버깅의 첫 수단.

## Doc updates
- CONTEXT.md promotion: none (딥링크 URL 스킴은 도메인 용어가 아니라 ADR 사안).
- ADR added: none 신규 — `.forge/adr/0009-hash-url-shareable-navigation-state.md`가 fg-ask 그릴링에서 이미 기록됨(해시·무라이브러리·인코딩 범위·공개 계약).
