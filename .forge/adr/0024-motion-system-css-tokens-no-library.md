# 모션 시스템: 무의존 CSS 토큰 + reduced-motion 토큰 붕괴 가드

앱이 사실상 정적(transition 19곳·keyframes 2개·reduced-motion 대응 0)이던 상태에서 모션 레이어를 신설하며(task#189~191), 모션 라이브러리(framer-motion 등) 도입 대신 **무의존 CSS 토큰 체계**를 채택했다.

- **토큰 계약**: `index.css`의 `--dur-fast/base/slow` + `--ease-out/in-out/drawer/pop`이 정본. 컴포넌트는 duration·easing을 하드코딩하지 않고 이 토큰만 참조한다(인라인 스타일 포함). 값 제안 정본은 `.forge/reports/motion-opportunities.md`(task#189 오디트).
- **reduced-motion은 토큰 붕괴로**: `@media (prefers-reduced-motion: reduce)`에서 `--dur-*`를 1ms로 붕괴시켜 토큰 참조 모션 전부가 즉시 최종 상태로 완료되게 한다(+ 스태거 `animation-delay` 전역 0). 개별 컴포넌트가 reduce 분기를 따로 짤 필요가 없다. Spinner(로딩 상태 표시)는 의도적 예외.
- **속성 제약**: transform·opacity만 애니메이트(레이아웃 속성 금지 — 모바일 60fps). 입장은 enter만, exit는 즉시 언마운트(React 언마운트 지연 상태기계 비용 회피). 지도(MapLibre 캔버스)는 비대상 — flyTo 자체 이징 유지(ADR-0013 지도 조항과 정합).
- **근거**: ① 필요한 모션 총량이 적다(오디트 평결 — 고빈도 동선은 무모션이 정답이라 라이브러리 표현력이 남는다), ② 번들·의존 비용 0(eco·lazy 원칙), ③ 기존 어휘 씨앗(.rel-chip·cloud-in·시트 슬라이드)이 이미 CSS라 연속적.

되돌리기 비싼 이유: 토큰이 전 컴포넌트 인라인 스타일에 퍼진 뒤 라이브러리로 전환하면 전면 재작업이다. 스프링 물리·제스처 연동(드래그 속도 기반 dismiss 등)이 실제로 필요해지는 시점에만 재검토하고, 그때도 토큰 값은 라이브러리 설정의 정본으로 유지한다.
