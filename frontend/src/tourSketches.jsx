import { useEffect, useState } from 'react'

// 투어 정차지 장면 스케치 (task#226 프로토타입) — eventId 키의 손저작 stroke-only 시퀀스 장면.
// ADR-0025의 선화 규약(stroke=currentColor, strokeWidth 2, pathLength=1, .symbol-draw dash,
// 얼굴 초상 없음)을 따르되, 장면용으로 확장: 시네마틱 viewBox 96×64 + 단계별 draw 딜레이 +
// SMIL 모션(돌 비행·쓰러짐)으로 "짧은 동영상" 연출. 지도 가독성을 위해 양피지(--paper) 패널 위에 그린다.
// 등록 없는 정차지는 아무것도 안 뜸(그레이스풀). 골리앗 예제 1편 — 평가 후 확대는 별도 태스크.

const P = { pathLength: 1 }
// 단계 딜레이(ms) — g 래퍼의 --sym-delay로 자식 stroke에 상속. reduce 모드에선 0.
const d = (ms, reduce) => ({ '--sym-delay': reduce ? '0ms' : `${ms}ms` })

// 골리앗 장면 (삼상 17:49-50) — 5단계: 무대 → 다윗·물매 → 골리앗 → 돌 비행 → 앞으로 쓰러짐 → 흙먼지.
function GoliathScene({ reduce }) {
  return (
    <>
      {/* 0단계 — 엘라 골짜기 무대: 바닥 + 능선 */}
      <g style={d(0, reduce)}>
        <path d="M4 54 h88" {...P} />
        <path d="M4 42 q12 -9 24 -1" {...P} opacity="0.5" />
        <path d="M58 40 q16 -11 34 -3" {...P} opacity="0.5" />
      </g>
      {/* 1단계 — 다윗(뒷모습 실루엣, 얼굴 없음): 다리·몸·머리·치켜든 팔·물매 회전 궤적 + 지팡이 */}
      <g style={d(600, reduce)}>
        <path d="M24 54 l2 -10 M30 54 l-2 -10" {...P} />
        <path d="M26 44 q1 -7 4 -10" {...P} />
        <circle cx="31" cy="30" r="3" {...P} />
        <path d="M31 33 q4 -3 2 -8" {...P} />
        <path d="M26 20 a7 7 0 1 0 10 4" {...P} />
        <path d="M17 54 l3 -13" {...P} />
      </g>
      {/* 2단계 — 골리앗(대형, 투구·갑주·창·방패 — 얼굴 없음, 투구 정면) */}
      <g id="goliath" style={d(1400, reduce)} transform={reduce ? 'rotate(-78 77 54)' : undefined}>
        <path d="M73 54 l1 -12 M81 54 l-1 -12" {...P} />
        <path d="M71 42 l2 -13 M83 42 l-2 -13 M72 29 h10" {...P} />
        <path d="M71 42 h12 M73 34 h8 M73 38 h8" {...P} />
        <path d="M73 24 a5 5 0 0 1 9 0 l-0.5 5 M77 24 v4" {...P} />
        <path d="M77 19 q4 -4 7 -2" {...P} />
        <path d="M88 54 V14 M88 14 l-3 6 m3 -6 l3 6" {...P} />
        <ellipse cx="66" cy="37" rx="4.5" ry="7" {...P} />
        {/* 쓰러짐 — 돌 명중 직후 발치 기준 앞으로(다윗 쪽) 회전. reduce는 정적 최종 상태 */}
        {!reduce && (
          <animateTransform
            attributeName="transform" type="rotate"
            from="0 77 54" to="-78 77 54"
            begin="3.3s" dur="0.7s" fill="freeze"
            calcMode="spline" keySplines="0.5 0 0.8 0.6" keyTimes="0;1"
          />
        )}
      </g>
      {/* 3단계 — 물매 돌 비행(드로우 인 + SMIL 포물선). reduce는 미표시(이미 명중한 시점) */}
      {!reduce && (
        <circle cx="30" cy="22" r="2.2" {...P} style={d(2600, false)}>
          <animateMotion path="M0 0 q24 -14 45 -3" begin="2.6s" dur="0.55s" fill="freeze"
            calcMode="spline" keySplines="0.3 0 0.7 1" keyTimes="0;1" />
        </circle>
      )}
      {/* 4단계 — 착지 흙먼지 */}
      <g style={d(reduce ? 0 : 4100, reduce)} stroke="var(--paper-accent)">
        <path d="M36 46 l-3 -3 M41 43 l-2 -4 M46 44 l1 -4 M32 50 l-4 -1" {...P} />
      </g>
    </>
  )
}

const SCENES = {
  'authored-david-goliath-gath': GoliathScene,
}

export const hasSketch = (eventId) => Boolean(eventId && SCENES[eventId])

function TourSketch({ eventId, width = 260, reduce = false }) {
  const Scene = SCENES[eventId]
  if (!Scene) return null
  return (
    <svg
      viewBox="0 0 96 64"
      width={width}
      height={Math.round(width * 64 / 96)}
      className={reduce ? undefined : 'symbol-draw'}
      style={{ display: 'block' }}
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <Scene reduce={reduce} />
    </svg>
  )
}

// 재생 오버레이 — 카메라 easeTo(400ms) 정착 후 양피지 패널 위에 장면이 그려진다(짧은 동영상 연출).
// 스케치 없는 정차지로 넘어가면 짧게 페이드아웃 후 제거. reduce: 딜레이·모션 없이 최종 장면 정적 표시.
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
    setLeaving(true)
    const t = setTimeout(() => { setShown(null); setLeaving(false) }, reduce ? 0 : 250)
    return () => clearTimeout(t)
  }, [eventId])

  if (!shown) return null
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  return (
    <div data-sketch-overlay style={{
      position: 'absolute', inset: 0, zIndex: 5, pointerEvents: 'none',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      // 하단 해설 카드 위 가시영역 중앙에 오도록 바닥 여백 확보
      paddingBottom: isMobile ? '32dvh' : 170,
      opacity: leaving ? 0 : 1,
      transition: 'opacity var(--dur-base) var(--ease-out)',
    }}>
      {/* 양피지 패널 — 지도 위 가독성(사용자 피드백). 밝은 표면 예외는 구절 양피지 관용구를 따른다. */}
      <div key={shown} className="stage-in" style={{
        background: 'var(--paper)', color: 'var(--paper-ink)',
        border: '1px solid color-mix(in srgb, var(--paper-accent) 45%, transparent)',
        borderRadius: 12, padding: '14px 16px 10px',
        boxShadow: 'var(--shadow-2)',
      }}>
        <TourSketch eventId={shown} width={isMobile ? 200 : 280} reduce={reduce} />
      </div>
    </div>
  )
}

export default TourSketch
