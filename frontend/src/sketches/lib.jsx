// 투어 장면 스케치 공용 헬퍼 (task#227 표준 확정본 → #228 모듈 분리)
// 선화 규약: stroke=currentColor, pathLength=1(.symbol-draw dash), 얼굴 초상 없음(ADR-0025).
// 선 굵기 위계(일괄 굵기 금지): 원경 1.1 · 질감/주름 1.3 · 지면 1.6 · 보조 1.8~2 · 주역 2.4~2.6 · 핵심 3
// — 전역 배율 W=0.55로 렌더 기준 펜 선 두께. 무드: 어두운 장면은 강조색만 금 → 목탄(패널에서 오버라이드).

export const P = { pathLength: 1 }
export const W = 0.55
export const sw = (n, o) => (o != null
  ? { pathLength: 1, strokeWidth: +(n * W).toFixed(2), opacity: o }
  : { pathLength: 1, strokeWidth: +(n * W).toFixed(2) })
// 단계 딜레이(ms) — g 래퍼의 --sym-delay로 자식 stroke에 상속. reduce 모드에선 0.
export const d = (ms, reduce) => ({ '--sym-delay': reduce ? '0ms' : `${ms}ms` })

// 장면 이름표 컴포넌트(Label)는 SceneLabel.jsx로 분리 — 이 파일은 순수 헬퍼만(react-refresh 규칙, task#253).
