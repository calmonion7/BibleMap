# 2026-06-17 — 타임라인뷰 맨 아래 행 하단 잘림 수정 (box-sizing 함정)

## Plan vs actual
- What went as planned:
  - TimelineView 스크롤 컨테이너 하단 잘림을 같은 컨테이너 인라인 style 한 줄 수정으로 해결.
  - 플랜의 non-goal(`100dvh`/safe-area, 레이아웃 구조 변경, 상단 nav 겹침) 전부 유지.
- Divergences:
  - **근본 원인이 플랜 가설과 달랐다.** 플랜은 "하단 패딩 없음"을 단일 원인으로 보고 `paddingBottom` 한 줄을 처방했으나, 실제 원인은 컨테이너가 기본 `box-sizing: content-box` + `height: 100%`라 패딩(상16+하48=64px)이 100% 높이 **바깥에 더해져** 요소가 뷰포트보다 64px 커지고 마지막 행(요한계시록)이 fold 아래 16px로 밀린 것.
  - **`paddingBottom` 단독은 역효과.** 요소만 더 커지고 마지막 행은 같이 밀려, gapAboveFold가 −16px로 그대로(오히려 악화 방향).
  - **실제 수정 = 2속성:** `boxSizing: 'border-box'` 추가로 `height:100%`가 패딩을 포함 → 컨테이너 clientH = innerHeight, 48px 하단 패딩이 마지막 행을 fold 위 48px로 들어 올림. Playwright 실측 데스크톱/모바일 모두 gapAboveFold +48 확인.

## Learnings
- Do differently next time:
  - **`height:100%`(또는 `100vh`) + 패딩 컨테이너는 `box-sizing`을 먼저 의심하라.** content-box에선 패딩이 선언 높이 밖에 더해져 부모를 넘친다. 이런 컨테이너에서 하단 잘림은 `paddingBottom`만으로 안 되고 `border-box`가 핵심. (전역 box-sizing 리셋이 없는 프로젝트라 더 그렇다.)
  - **뷰포트/레이아웃 잘림 버그는 처음부터 충실한 렌더러로 검증하라.** 코드만 본 fg-ask 근본원인 가설이 box-sizing 오버플로우를 놓쳤다. Claude preview(5173)와 Playwright가 **동일 수치**(컨테이너 clientH가 뷰포트보다 64px 큼)를 재현 → 아티팩트가 아니라 실제 버그였음. 측정치가 이상해 보여도 두 렌더러가 일치하면 믿어라.
  - **프론트 시각 검증 표면(중요·재사용):** Vite dev 서버(5173)는 로컬에서 API에 못 닿는다(`api.js`의 `API_BASE` 기본값이 `localhost:8000`인데 호스트 미매핑, curl 000). 또 장기 실행 인스턴스는 소스가 stale해진다. 신뢰 경로 = `npm --prefix frontend run build` → nginx가 `frontend/dist`를 `localhost:8080`로 서빙(백엔드 CORS `*`) → Playwright(`/opt/homebrew` python3.14)로 측정+스크린샷. (preview로 빠른 확인은 가능하나 픽셀 정밀 잘림은 8080+Playwright로 확정.)

## Doc updates
- CONTEXT.md promotion: none (box-sizing은 구현 디테일 — 용어집 비대상)
- ADR added: none (3요건 미충족 — 즉시 되돌릴 수 있고 진짜 대안 트레이드오프 아님)
