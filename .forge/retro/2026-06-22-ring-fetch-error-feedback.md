# 2026-06-22 — 링 펼침 fetch 실패 무음 → 피드백 (task 79)

## Plan vs actual
- What went as planned: `expandPlace`의 `catch { return }` → `catch (e) { if (e?.name !== 'AbortError' && !destroyed) setError(true); return }`. selectedNode effect의 검증된 line-714 패턴 재사용. 발산 낮음(코드 1줄).
- Divergences: 코드 무관. UAT 하니스에서 한참 헛짚음(아래).

## Learnings
- Do differently next time:
  1. **[중요·재발성] sync Playwright `time.sleep()`은 Playwright 이벤트 루프를 펌프하지 않아, `page.route(...)`로 가로챈 요청의 핸들러(lambda)가 sleep 동안 실행되지 못한다 → 가로챈 fetch가 hang.** 그 결과 "grouped 500인데 catch가 안 도는" 가짜 증상으로 한참 디버깅. **액션을 건 뒤 라우트된 응답이 resolve돼야 하는 대기에는 `time.sleep` 대신 `page.wait_for_timeout()`(또는 `expect`/`wait_for_*`)를 써서 루프를 펌프할 것.** standalone `page.evaluate(fetch)`가 정상이었던 건 evaluate가 루프를 펌프했기 때문. → [[feedback_playwright_testing]]에 반영함.
  2. 비동기 fetch 에러 피드백은 기존 `setError` 배너를 재사용하고 AbortError만 제외(빠른 재클릭·언마운트 무음 유지) — selectedNode effect와 동일 패턴. `setError`는 컴포넌트 useState라 init effect 클로저에서 도달 가능.

## Doc updates
- CONTEXT.md promotion: 없음
- ADR added: 없음
- 메모리: [[feedback_playwright_testing]]에 time.sleep→wait_for_timeout 함정 추가
