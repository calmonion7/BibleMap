import { useEffect, useState } from 'react'

// 투어 정차지 장면 스케치 (task#226 프로토타입) — eventId 키의 손저작 stroke-only 시퀀스 장면.
// ADR-0025의 선화 규약(stroke=currentColor, pathLength=1, .symbol-draw dash, 얼굴 초상 없음)을
// 따르되 장면용으로 확장: 시네마틱 viewBox 96×64, 단계별 draw 딜레이, SMIL 안무(물매 회전·
// 돌 비행·쓰러짐·지면 진동)로 "짧은 동영상" 연출. 지도 가독성을 위해 양피지(--paper) 패널 위에 그린다.
// 등록 없는 정차지는 아무것도 안 뜸(그레이스풀). 골리앗 예제 1편 — 평가 후 확대는 별도 태스크.

const P = { pathLength: 1 }
const thin = { pathLength: 1, strokeWidth: 1.4 }   // 세부(갑주 비늘·자갈·깃털)
const heavy = { pathLength: 1, strokeWidth: 2.6 }  // 강조(창 자루)
// 단계 딜레이(ms) — g 래퍼의 --sym-delay로 자식 stroke에 상속. reduce 모드에선 0.
const d = (ms, reduce) => ({ '--sym-delay': reduce ? '0ms' : `${ms}ms` })

// 골리앗 장면 (삼상 17:49-50) — 안무: 골짜기 → 골리앗 위용 → 다윗 등장 → 물매 2회전 →
// 투석 → 휘청이다 앞으로 쓰러짐 → 지면 진동 + 흙먼지.
function GoliathScene({ reduce }) {
  return (
    <g>
      {/* 지면 진동 — 쓰러짐 착지 순간 장면 전체가 짧게 흔들림 */}
      {!reduce && (
        <animateTransform attributeName="transform" type="translate"
          values="0 0; 0 1.3; 0 0; 0 0.6; 0 0" keyTimes="0;0.25;0.5;0.75;1"
          begin="4.85s" dur="0.32s" />
      )}

      {/* 0단계 — 엘라 골짜기: 지평선·양쪽 능선·시내와 자갈 */}
      <g style={d(0, reduce)}>
        <path d="M4 54 h88" {...P} />
        <path d="M4 41 q13 -10 26 -2" {...thin} opacity="0.45" />
        <path d="M62 39 q16 -12 30 -3" {...thin} opacity="0.45" />
        <path d="M38 53 q7 -2.5 14 0" {...thin} opacity="0.6" />
        <path d="M43 51.5 h2 M48 52 h2 M40 52.5 h1.5" {...thin} opacity="0.6" />
      </g>

      {/* 1단계 — 골리앗의 위용(우측, 신장 ~44px): 깃털 투구·비늘 갑주·버팀 창·대형 방패 */}
      <g style={d(700, reduce)} transform={reduce ? 'rotate(-80 77 54)' : undefined}>
        {/* 다리·정강이받이 */}
        <path d="M72.5 54 l1.5 -13 M82.5 54 l-1.5 -13" {...P} />
        <path d="M73 47 h2.5 M80 47 h2.5" {...thin} />
        {/* 몸통(넓은 어깨)·허리띠·갑주 자락 */}
        <path d="M70 41 l2.5 -15 M85 41 l-2.5 -15 M72.5 26 h10" {...P} />
        <path d="M70 41 h15 M71.5 38.5 h12" {...P} />
        {/* 비늘 갑주 2열(물결) */}
        <path d="M73 30.5 q2 2 4 0 q2 2 4 0" {...thin} />
        <path d="M72.5 34.5 q2 2 4 0 q2 2 4 0 q1.5 1.5 3 0" {...thin} />
        {/* 팔 — 오른손 창·왼팔 방패 */}
        <path d="M83.5 27 q4.5 3 4 8.5" {...P} />
        <path d="M72 27.5 q-5 3 -5.5 7.5" {...P} />
        {/* 투구(정면 — 얼굴 없음): 돔·챙·코가리개·깃털 장식 */}
        <path d="M73.5 21 a4.6 4.6 0 0 1 9.2 0" {...P} />
        <path d="M73 21.3 h10.2 M78.1 21.3 v4.2" {...P} />
        <path d="M76.5 16 q2.5 -6 8.5 -5.5 q-1.5 5 -6 6" {...thin} />
        {/* 창(베틀 채 같은 — 굵게) + 창날 */}
        <path d="M87.8 54 V10" {...heavy} />
        <path d="M87.8 10 l-3.5 6.5 m3.5 -6.5 l3.5 6.5" {...P} />
        {/* 대형 원형 방패 + 중심 돌기 */}
        <circle cx="64.5" cy="37" r="6" {...P} />
        <circle cx="64.5" cy="37" r="1.7" {...thin} />
        {/* 휘청 → 앞으로(다윗 쪽) 쓰러짐 — 발치 기준. reduce는 정적 최종 상태 */}
        {!reduce && (
          <animateTransform attributeName="transform" type="rotate"
            values="0 77 54; 5 77 54; -80 77 54" keyTimes="0; 0.22; 1"
            begin="3.95s" dur="0.95s" fill="freeze"
            calcMode="spline" keySplines="0.4 0 0.6 1; 0.55 0 0.85 0.7" />
        )}
      </g>

      {/* 2단계 — 다윗(좌측, 뒷모습 실루엣): 내딛는 다리·튜닉·물매 든 팔, 내려놓은 지팡이 */}
      <g style={d(1700, reduce)}>
        <path d="M23 54 l3.5 -9.5 M31 54 l-2.5 -9.5" {...P} />
        <path d="M25.5 44.5 l3 -10 h3.5 l2.5 10" {...P} />
        <path d="M27 40 h6" {...thin} />
        <circle cx="30.5" cy="31" r="3" {...P} />
        <path d="M33.5 35.5 q3.5 -4.5 2 -9.5" {...P} />
        <path d="M13.5 53.5 l8.5 -1.8" {...thin} opacity="0.7" />
        {/* 물매 — 손(35,26) 기준 회전 그룹: 끈 + 주머니. 회전 전엔 정지 드로우 */}
        <g>
          <path d="M35 26 l6.2 -5" {...P} />
          <circle cx="42" cy="20" r="1.9" {...P} />
          {!reduce && (
            <animateTransform attributeName="transform" type="rotate"
              from="0 35 26" to="720 35 26" begin="2.7s" dur="0.8s"
              calcMode="spline" keySplines="0.35 0 0.75 1" keyTimes="0;1" />
          )}
        </g>
        {/* 회전 잔상 호 */}
        <path d="M27 19.5 a9.5 9.5 0 1 0 15 2.5" {...thin} opacity="0.4" />
      </g>

      {/* 3단계 — 물매 돌: 드로우 인과 동시에 포물선 비행(투구를 향해). reduce는 명중 후 시점이라 미표시 */}
      {!reduce && (
        <circle cx="42" cy="20" r="2" {...P} style={d(3500, false)}>
          <animateMotion path="M0 0 q18 -12 36 -2" begin="3.5s" dur="0.45s" fill="freeze"
            calcMode="spline" keySplines="0.3 0 0.75 1" keyTimes="0;1" />
          {/* 명중 직후 소멸 — 공중 잔상 방지 */}
          <animate attributeName="opacity" to="0" begin="4.0s" dur="0.15s" fill="freeze" />
        </circle>
      )}

      {/* 4단계 — 착지 흙먼지(강조색): 피어오르는 호 + 튀는 자갈 */}
      <g style={d(reduce ? 0 : 5000, reduce)} stroke="var(--paper-accent)">
        <path d="M39 47 q-3.5 -4 -7 -4.5 M43.5 44 q-0.5 -5 -3.5 -7.5 M49 44.5 q3 -4.5 7 -5 M52 48 q4 -2 7.5 -1.5" {...thin} />
        <circle cx="36" cy="42" r="0.9" {...thin} />
        <circle cx="47" cy="39.5" r="0.9" {...thin} />
      </g>
    </g>
  )
}

const SCENES = {
  'authored-david-goliath-gath': { Scene: GoliathScene, caption: '다윗과 골리앗 — 사무엘상 17장' },
}

export const hasSketch = (eventId) => Boolean(eventId && SCENES[eventId])

function TourSketch({ eventId, width = 280, reduce = false }) {
  const entry = SCENES[eventId]
  if (!entry) return null
  const { Scene } = entry
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
  const caption = SCENES[shown]?.caption
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
        borderRadius: 12, padding: '14px 16px 8px',
        boxShadow: 'var(--shadow-2)',
      }}>
        <TourSketch eventId={shown} width={isMobile ? 210 : 300} reduce={reduce} />
        {caption && (
          <div style={{
            marginTop: 6, textAlign: 'center',
            fontFamily: 'var(--serif)', fontSize: 11.5, letterSpacing: '0.04em',
            color: 'var(--paper-accent)',
          }}>{caption}</div>
        )}
      </div>
    </div>
  )
}

export default TourSketch
