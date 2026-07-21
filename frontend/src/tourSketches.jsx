import { useEffect, useState } from 'react'

// 투어 정차지 장면 스케치 (task#226 프로토타입) — eventId 키의 손저작 stroke-only 시퀀스 장면.
// ADR-0025의 선화 규약(stroke=currentColor, pathLength=1, .symbol-draw dash, 얼굴 초상 없음)을
// 따르되 장면용으로 확장: 시네마틱 viewBox 120×64, 단계별 draw 딜레이, SMIL 안무(물매 회전·
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
        <path d="M4 54 h112" {...P} />
        <path d="M4 41 q13 -10 26 -2" {...thin} opacity="0.45" />
        <path d="M84 39 q18 -12 32 -3" {...thin} opacity="0.45" />
        <path d="M50 53 q8 -2.5 16 0" {...thin} opacity="0.6" />
        <path d="M56 51.5 h2 M62 52 h2 M52 52.5 h1.5" {...thin} opacity="0.6" />
      </g>

      {/* 1단계 — 골리앗의 위용(우측, 신장 ~44px): 깃털 투구·비늘 갑주·버팀 창·대형 방패 */}
      <g style={d(700, reduce)} transform={reduce ? 'rotate(-80 103 54)' : undefined}>
        {/* 다리·정강이받이 */}
        <path d="M98.5 54 l1.5 -13 M108.5 54 l-1.5 -13" {...P} />
        <path d="M99 47 h2.5 M106 47 h2.5" {...thin} />
        {/* 몸통(넓은 어깨)·허리띠·갑주 자락 */}
        <path d="M96 41 l2.5 -15 M111 41 l-2.5 -15 M98.5 26 h10" {...P} />
        <path d="M96 41 h15 M97.5 38.5 h12" {...P} />
        {/* 비늘 갑주 2열(물결) */}
        <path d="M99 30.5 q2 2 4 0 q2 2 4 0" {...thin} />
        <path d="M98.5 34.5 q2 2 4 0 q2 2 4 0 q1.5 1.5 3 0" {...thin} />
        {/* 팔 — 오른손 창·왼팔 방패 */}
        <path d="M109.5 27 q4.5 3 4 8.5" {...P} />
        <path d="M98 27.5 q-5 3 -5.5 7.5" {...P} />
        {/* 투구(정면 — 얼굴 없음): 돔·챙·코가리개·깃털 장식 */}
        <path d="M99.5 21 a4.6 4.6 0 0 1 9.2 0" {...P} />
        <path d="M99 21.3 h10.2 M104.1 21.3 v4.2" {...P} />
        <path d="M102.5 16 q2.5 -6 8.5 -5.5 q-1.5 5 -6 6" {...thin} />
        {/* 창(베틀 채 같은 — 굵게) + 창날 */}
        <path d="M113.5 54 V10" {...heavy} />
        <path d="M113.5 10 l-3.5 6.5 m3.5 -6.5 l3.5 6.5" {...P} />
        {/* 대형 원형 방패 + 중심 돌기 */}
        <circle cx="90.5" cy="37" r="6" {...P} />
        <circle cx="90.5" cy="37" r="1.7" {...thin} />
        {/* 휘청 → 앞으로(다윗 쪽) 쓰러짐 — 발치 기준. reduce는 정적 최종 상태 */}
        {!reduce && (
          <animateTransform attributeName="transform" type="rotate"
            values="0 103 54; 5 103 54; -80 103 54" keyTimes="0; 0.22; 1"
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
          <animateMotion path="M0 0 q31 -17 62 -3" begin="3.5s" dur="0.55s" fill="freeze"
            calcMode="spline" keySplines="0.3 0 0.75 1" keyTimes="0;1" />
          {/* 명중 직후 소멸 — 공중 잔상 방지 */}
          <animate attributeName="opacity" to="0" begin="4.1s" dur="0.15s" fill="freeze" />
        </circle>
      )}

      {/* 4단계 — 착지 흙먼지(강조색): 피어오르는 호 + 튀는 자갈 */}
      <g style={d(reduce ? 0 : 5000, reduce)} stroke="var(--paper-accent)">
        <path d="M62 47 q-3.5 -4 -7 -4.5 M66.5 44 q-0.5 -5 -3.5 -7.5 M72 44.5 q3 -4.5 7 -5 M76 48 q4 -2 7.5 -1.5" {...thin} />
        <circle cx="59" cy="42" r="0.9" {...thin} />
        <circle cx="70" cy="39.5" r="0.9" {...thin} />
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
      viewBox="0 0 120 64"
      width={width}
      height={typeof width === 'number' ? Math.round(width * 64 / 120) : undefined}
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

// 카드 상단 삽화 패널 — 해설 카드에 통합(그림·설명이 한 장으로 읽히도록, 사용자 피드백 5차).
// 카메라 easeTo(400ms) 정착 후 draw 시작(그 전엔 자리만 확보해 카드 높이 점프 방지).
// 스케치 없는 정차지는 아무것도 렌더하지 않음. reduce: 딜레이 없이 최종 장면 정적 표시.
export function TourSketchPanel({ eventId }) {
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  const [ready, setReady] = useState(reduce)
  useEffect(() => {
    if (reduce) return
    const t = setTimeout(() => setReady(true), 450)
    return () => clearTimeout(t)
  }, [reduce])

  if (!hasSketch(eventId)) return null
  const caption = SCENES[eventId]?.caption
  return (
    <div data-sketch-panel style={{
      background: 'var(--paper)', color: 'var(--paper-ink)',
      borderBottom: '1px solid color-mix(in srgb, var(--paper-accent) 40%, transparent)',
      padding: '12px 16px 6px',
    }}>
      {/* draw 시작 전에도 동일 비율 자리 확보 — 카드 높이 점프 방지 */}
      <div style={{ aspectRatio: '120 / 64', width: '100%' }}>
        {ready && <TourSketch eventId={eventId} width="100%" reduce={reduce} />}
      </div>
      {caption && (
        <div style={{
          marginTop: 4, textAlign: 'center',
          fontFamily: 'var(--serif)', fontSize: 11.5, letterSpacing: '0.04em',
          color: 'var(--paper-accent)',
        }}>{caption}</div>
      )}
    </div>
  )
}

export default TourSketch
