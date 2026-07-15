# 2026-07-15 — 구절 레이어 계기→결과 2단 (API + UI) (task 183, part 2/2)

## Plan vs actual
- What went as planned: `/person/{id}/reliance`가 `trigger`/`outcome`/`sameVerse`/`kind` 반환(지표 %
  무변경 — mode·obeyed만 읽음). `RelianceView` 구절 레이어를 계기 칩 → ↓ → 결과 칩 + 응답 성격 뱃지 +
  절 카드 2단으로 재디자인, sameVerse면 카드 1개·다르면 2개. eslint 0 · build green · Playwright 7컷
  (데스크톱·모바일/라이트·다크, 5 mode + twoVerse) 육안 확인.
- Divergences: 워크플로우 대신 직접 실행(결합 2파일, 팬아웃 아님), 조건부 코드리뷰를 다뷰포트 시각 UAT로 대체.

## Learnings
- Do differently next time: **스키마 마이그레이션을 data-part / consumer-part(API·UI)로 쪼갤 땐 두 파트가
  하나의 배포 단위다.** 새 스키마가 최상위 flat 필드를 제거하면 그 필드를 하드키로 읽는 기존 엔드포인트
  (reliance.py:113-114 `e["verse"]`/`e["label"]`)가 500 — data-part만 push→auto-deploy하면 prod가 깨진다.
  이런 분할 시 셋 중 하나로 설계: (a) 두 파트 함께 커밋·배포(이번 선택), (b) part1에 소비자 하위호환 유지,
  (c) part1이 소비자를 안 깨는 필드-추가-우선 순서. **분할 계획의 Non-goals에 "단독 배포 금지"를 명시**할 것.
  이 프로젝트는 push=auto-deploy·data는 볼륨 마운트라 "봉인=배포"가 아님을 특히 유의(중간 파트는 로컬만).
- Keep: 결합된 2파일(라우트 + 컴포넌트 1개) 순차 변경은 팬아웃이 아니라 직접 실행이 싸고 빠름(#170 하이브리드는
  팬아웃 전용). UAT 스크린샷을 **에이전트가 직접 판독**해 sealable `yes` 도달 — 회고 4of4 "레이아웃은 육안" 충족.

## Doc updates
- CONTEXT.md promotion: part 1 회고에서 [[하나님 상호작용 mode]] 2단·kind 승급 반영(중복 회피).
- ADR added: none (배포 결합은 결정이 아닌 운영 주의 — ADR 3조건[가역불가·난해·트레이드오프] 미충족).
