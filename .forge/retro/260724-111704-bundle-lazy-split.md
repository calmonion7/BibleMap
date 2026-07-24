# 2026-07-24 — 메인 번들 lazy 분할 (task#254) [일괄 승급]

## Plan vs actual
- 투어 스케치 9모듈을 React.lazy로 분리, 메인 청크 640→250KB. 세부는 `.forge/done/260724-110144-bundle-lazy-split/run.md`.

## Learnings
- Do differently next time:
  - **번들 최대 기여자부터**: 투어 스케치 9모듈(~9.7천 줄, 391KB)을 `lazy(() => import('./tourSketches'))`로. **딥링크 진입은 인트로를 스킵**하므로(useStageNavigation) 인트로/재생 전용 무거운 자산의 lazy는 딥링크 초기 번들에서 통째로 빠져 특히 효과적.
  - `<Suspense fallback={null}>`로 인트로 몽타주·재생 카드 스케치 지연 로드 — 깜빡임/크래시 없이 draw. 딥링크 초기 로드에 청크 미요청 → 재생 시작 시 온디맨드, network로 검증.
  - **소형 뷰(StatsView 6KB·TopicalVersesView 3KB)는 lazy 이득 미미 → 스킵**(eco YAGNI). 계획이 열거해도 목표(메인 대폭 감소) 달성에 불필요하면 제외.
  - vite 500KB 경고: 앱 코드(index)를 500 아래로 내리면 잔존 경고는 maplibre 벤더뿐(별 manualChunk, 범위 밖).

## Doc updates
- CONTEXT.md: none. ADR: none.
