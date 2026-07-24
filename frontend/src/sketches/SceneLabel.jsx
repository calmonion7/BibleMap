// 장면 내 이름표 — 대상이 그려진 뒤 페이드인, 양피지색 헤일로로 그림 위에서 판독.
// (task#253: react-refresh/only-export-components 위해 순수 헬퍼 lib.jsx에서 컴포넌트만 분리)
export function Label({ x, y, at = 0, reduce, anchor = 'middle', size = 4.6, children }) {
  return (
    <text x={x} y={y} fontSize={size} fontFamily="var(--serif)" fontWeight="600"
      fill="var(--paper-accent)" stroke="var(--paper)" strokeWidth="2.4" paintOrder="stroke"
      strokeLinejoin="round" textAnchor={anchor} opacity={reduce ? 1 : 0}>
      {children}
      {!reduce && <animate attributeName="opacity" to="1" begin={`${at}s`} dur="0.4s" fill="freeze" />}
    </text>
  )
}
