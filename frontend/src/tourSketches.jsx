import { useEffect, useState } from 'react'

// 투어 정차지 장면 스케치 (task#226 프로토타입) — eventId 키의 손저작 stroke-only SVG.
// 규격은 personSymbols.jsx(ADR-0025)와 동일: viewBox 64×64, stroke=currentColor, strokeWidth 2,
// pathLength=1 정규화(.symbol-draw dash 1 = 전체 선), 얼굴 초상 없음(사물·장면만).
// 재생 중 카메라 정착 후 지도 중앙에 draw-on — 등록 없는 정차지는 아무것도 안 뜸(그레이스풀).
// 현재 골리앗 예제 1편만 저작 — 평가 후 확대는 별도 태스크.

const P = { pathLength: 1 }

const SKETCHES = {
  // 다윗이 가드 출신 골리앗을 쓰러뜨림 (삼상 17:49-50) —
  // 물매 회전 궤적과 돌, 비행 점선, 쓰러진 거인의 창·방패·투구(사물로 패배를 표현).
  'authored-david-goliath-gath': (
    <>
      {/* 바닥 */}
      <path d="M6 54 h52" {...P} />
      {/* 목동의 지팡이 (왼쪽) */}
      <path d="M14 54 v-15 q0 -6 6 -6" {...P} />
      {/* 물매 회전 궤적 + 돌 */}
      <path d="M24 25 a9 9 0 1 1 -2 -13" {...P} />
      <circle cx="25" cy="23" r="2.2" {...P} />
      {/* 돌의 비행 점선 아크 */}
      <path d="M30 20 q5 -3 10 -3 M45 17 q4 0 7 2" {...P} />
      {/* 기울어 꽂힌 거인의 창 */}
      <path d="M58 20 L45 47" {...P} />
      <path d="M58 20 l-6 0 l5 4" {...P} />
      {/* 넘어진 방패(타원) + 뒤집힌 투구 */}
      <ellipse cx="35" cy="51" rx="7" ry="3" {...P} />
      <path d="M46 51 a6 6 0 0 1 12 0 h-12" {...P} />
    </>
  ),
}

export const hasSketch = (eventId) => Boolean(eventId && SKETCHES[eventId])

function TourSketch({ eventId, size = 150, draw = false }) {
  if (!SKETCHES[eventId]) return null
  return (
    <svg
      viewBox="0 0 64 64"
      width={size}
      height={size}
      className={draw ? 'symbol-draw' : undefined}
      style={{ display: 'block' }}
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {SKETCHES[eventId]}
    </svg>
  )
}

// 재생 오버레이 — 카메라 easeTo(400ms) 정착 후 지도 중앙에 draw 시작, 스케치 없는 정차지로
// 넘어가면 짧게 페이드아웃 후 제거. reduced-motion: 딜레이 없이 즉시(draw 자체도 전역 가드로 즉시 완성).
export function TourSketchOverlay({ eventId, isMobile }) {
  const [shown, setShown] = useState(null)   // 현재 그려진 eventId
  const [leaving, setLeaving] = useState(false)

  useEffect(() => {
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    if (hasSketch(eventId)) {
      setLeaving(false)
      const t = setTimeout(() => setShown(eventId), reduce ? 0 : 450)
      return () => clearTimeout(t)
    }
    // 스케치 없는 정차지 — 떠 있던 스케치는 페이드아웃 후 제거
    setLeaving(true)
    const t = setTimeout(() => { setShown(null); setLeaving(false) }, reduce ? 0 : 250)
    return () => clearTimeout(t)
  }, [eventId])

  if (!shown) return null
  return (
    <div data-sketch-overlay style={{
      position: 'absolute', inset: 0, zIndex: 5, pointerEvents: 'none',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      // 하단 해설 카드 위 가시영역 중앙에 오도록 바닥 여백 확보
      paddingBottom: isMobile ? '32dvh' : 150,
      opacity: leaving ? 0 : 1,
      transition: 'opacity var(--dur-base) var(--ease-out)',
    }}>
      <div key={shown} className="stage-in" style={{ color: 'var(--gold)', filter: 'drop-shadow(0 2px 8px rgba(0,0,0,0.55))' }}>
        <TourSketch eventId={shown} size={isMobile ? 110 : 150} draw />
      </div>
    </div>
  )
}

export default TourSketch
