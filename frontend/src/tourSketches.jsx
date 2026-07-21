import { useEffect, useState } from 'react'

// 투어 정차지 장면 스케치 (task#226·227) — eventId 키의 손저작 stroke-only 시퀀스 장면.
// ADR-0025의 선화 규약(stroke=currentColor, pathLength=1, .symbol-draw dash, 얼굴 초상 없음)을
// 따르되 장면용으로 확장: 시네마틱 viewBox 120×64, 단계별 draw 딜레이, SMIL 안무, 양피지 패널.
// 선 굵기 위계(일괄 굵기 금지 — 스케치 원근·주역 강조): 원경 1.1 · 질감/주름 1.3 · 지면 1.6 ·
// 보조 인물/소품 1.8~2 · 주역 2.4~2.6 · 핵심 소품(창·왕관·불) 2.8~3.
// 등록 없는 정차지는 아무것도 안 뜸(그레이스풀).

const P = { pathLength: 1 }
// 굵기 헬퍼 — sw(굵기[, 불투명도]). 모든 stroke 요소는 pathLength=1 정규화 유지.
const sw = (n, o) => (o != null ? { pathLength: 1, strokeWidth: n, opacity: o } : { pathLength: 1, strokeWidth: n })
// 단계 딜레이(ms) — g 래퍼의 --sym-delay로 자식 stroke에 상속. reduce 모드에선 0.
const d = (ms, reduce) => ({ '--sym-delay': reduce ? '0ms' : `${ms}ms` })

// 골리앗 (삼상 17:49-50) — 물매 2회전 → 투석 → 휘청·쓰러짐 → 지면 진동 + 흙먼지
function GoliathScene({ reduce }) {
  return (
    <g>
      {!reduce && (
        <animateTransform attributeName="transform" type="translate"
          values="0 0; 0 1.3; 0 0; 0 0.6; 0 0" keyTimes="0;0.25;0.5;0.75;1"
          begin="4.85s" dur="0.32s" />
      )}
      {/* 무대 — 지면은 중간, 능선은 가늘게(원근), 시내·자갈·풀 질감 */}
      <g style={d(0, reduce)}>
        <path d="M4 54 h112" {...sw(1.6)} />
        <path d="M4 41 q13 -10 26 -2" {...sw(1.1, 0.4)} />
        <path d="M84 39 q18 -12 32 -3" {...sw(1.1, 0.4)} />
        <path d="M50 53 q8 -2.5 16 0" {...sw(1.3, 0.55)} />
        <path d="M56 51.5 h2 M62 52 h2 M52 52.5 h1.5" {...sw(1.2, 0.55)} />
        <path d="M14 52.5 l1 -2 l1 2 M42 53 l0.8 -1.6 l0.8 1.6 M78 53 l0.9 -1.8 l0.9 1.8" {...sw(1.1, 0.45)} />
      </g>
      {/* 골리앗 — 주역 굵기 + 갑주 세부 */}
      <g style={d(700, reduce)} transform={reduce ? 'rotate(-80 103 54)' : undefined}>
        <path d="M98.5 54 l1.5 -13 M108.5 54 l-1.5 -13" {...sw(2.4)} />
        <path d="M99 47 h2.5 M106 47 h2.5 M99.6 50.5 h2 M105.6 50.5 h2" {...sw(1.3)} />
        <path d="M96 41 l2.5 -15 M111 41 l-2.5 -15 M98.5 26 h10" {...sw(2.6)} />
        <path d="M96 41 h15 M97.5 38.5 h12" {...sw(2)} />
        <path d="M99 30.5 q2 2 4 0 q2 2 4 0" {...sw(1.3)} />
        <path d="M98.5 34.5 q2 2 4 0 q2 2 4 0 q1.5 1.5 3 0" {...sw(1.3)} />
        <path d="M100.5 28 v2 M104 28 v2.2 M107.5 28 v2" {...sw(1.1, 0.5)} />
        <path d="M109.5 27 q4.5 3 4 8.5" {...sw(2.2)} />
        <path d="M98 27.5 q-5 3 -5.5 7.5" {...sw(2.2)} />
        <path d="M99.5 21 a4.6 4.6 0 0 1 9.2 0" {...sw(2.4)} />
        <path d="M99 21.3 h10.2 M104.1 21.3 v4.2" {...sw(1.8)} />
        <path d="M102.5 16 q2.5 -6 8.5 -5.5 q-1.5 5 -6 6" {...sw(1.4)} />
        <path d="M105 14.5 q2 -2.5 4.5 -2.8" {...sw(1.1, 0.5)} />
        <path d="M113.5 54 V10" {...sw(3)} />
        <path d="M113.5 10 l-3.5 6.5 m3.5 -6.5 l3.5 6.5" {...sw(2.2)} />
        <circle cx="90.5" cy="37" r="6" {...sw(2.4)} />
        <circle cx="90.5" cy="37" r="4" {...sw(1.2, 0.5)} />
        <circle cx="90.5" cy="37" r="1.7" {...sw(1.4)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="rotate"
            values="0 103 54; 5 103 54; -80 103 54" keyTimes="0; 0.22; 1"
            begin="3.95s" dur="0.95s" fill="freeze"
            calcMode="spline" keySplines="0.4 0 0.6 1; 0.55 0 0.85 0.7" />
        )}
      </g>
      {/* 다윗 — 주역 굵기, 튜닉 주름·발 디테일 */}
      <g style={d(1700, reduce)}>
        <path d="M23 54 l3.5 -9.5 M31 54 l-2.5 -9.5" {...sw(2.2)} />
        <path d="M21.5 54 h3 M29.8 54 h3" {...sw(1.4)} />
        <path d="M25.5 44.5 l3 -10 h3.5 l2.5 10" {...sw(2.4)} />
        <path d="M28 42 q1 -3 0.6 -6 M31.5 42.5 q0.3 -3 -0.2 -6" {...sw(1.3, 0.6)} />
        <path d="M27 40 h6" {...sw(1.4)} />
        <circle cx="30.5" cy="31" r="3" {...sw(2.4)} />
        <path d="M33.5 35.5 q3.5 -4.5 2 -9.5" {...sw(2.2)} />
        <path d="M13.5 53.5 l8.5 -1.8" {...sw(1.3, 0.6)} />
        <g>
          <path d="M35 26 l6.2 -5" {...sw(1.8)} />
          <circle cx="42" cy="20" r="1.9" {...sw(2)} />
          {!reduce && (
            <animateTransform attributeName="transform" type="rotate"
              from="0 35 26" to="720 35 26" begin="2.7s" dur="0.8s"
              calcMode="spline" keySplines="0.35 0 0.75 1" keyTimes="0;1" />
          )}
        </g>
        <path d="M27 19.5 a9.5 9.5 0 1 0 15 2.5" {...sw(1.2, 0.35)} />
      </g>
      {!reduce && (
        <circle cx="42" cy="20" r="2" {...sw(2.2)} style={d(3500, false)}>
          <animateMotion path="M0 0 q31 -17 62 -3" begin="3.5s" dur="0.55s" fill="freeze"
            calcMode="spline" keySplines="0.3 0 0.75 1" keyTimes="0;1" />
          <animate attributeName="opacity" to="0" begin="4.1s" dur="0.15s" fill="freeze" />
        </circle>
      )}
      <g style={d(reduce ? 0 : 5000, reduce)} stroke="var(--paper-accent)">
        <path d="M62 47 q-3.5 -4 -7 -4.5 M66.5 44 q-0.5 -5 -3.5 -7.5 M72 44.5 q3 -4.5 7 -5 M76 48 q4 -2 7.5 -1.5" {...sw(1.3)} />
        <circle cx="59" cy="42" r="0.9" {...sw(1.3)} />
        <circle cx="70" cy="39.5" r="0.9" {...sw(1.3)} />
      </g>
    </g>
  )
}

// ── 다윗과 통일왕국 17장면 (task#227) — 굵기 위계 + 디테일 보강판 ──

// 미스바 제비뽑기 (삼상 10:17-24)
function MizpahChosenScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M8 42 q14 -9 27 -2" {...sw(1.1, 0.4)} />
        <path d="M12 52.8 l1 -2 l1 2 M48 53 l0.9 -1.8 l0.9 1.8" {...sw(1.1, 0.45)} />
      </g>
      {/* 무리 — 보조 굵기 */}
      <g style={d(600, reduce)}>
        <circle cx="20" cy="43" r="2.6" {...sw(1.8)} />
        <path d="M20 45.6 v5.4 M17.5 54 l2.5 -3 l2.5 3" {...sw(1.8)} />
        <circle cx="31" cy="44" r="2.6" {...sw(1.8)} />
        <path d="M31 46.6 v4.9 M28.5 54 l2.5 -3 l2.5 3" {...sw(1.8)} />
        <circle cx="42" cy="43.5" r="2.6" {...sw(1.8)} />
        <path d="M42 46.1 v5.4 M39.5 54 l2.5 -3 l2.5 3" {...sw(1.8)} />
        <path d="M18.6 47 q1.4 1 2.8 0 M29.6 48 q1.4 1 2.8 0" {...sw(1.2, 0.5)} />
      </g>
      {/* 제비 항아리 — 핵심 소품 */}
      <g style={d(1400, reduce)}>
        <path d="M55 54 h14 M57 54 v-4 h10 v4" {...sw(1.8)} />
        <path d="M59 50 q-1.5 -7 3.5 -8 q5 1 3.5 8" {...sw(2.6)} />
        <path d="M60.5 42.5 h5" {...sw(1.4)} />
        <path d="M60 46.5 q2.5 1.2 5 0" {...sw(1.2, 0.5)} />
      </g>
      <g style={d(2000, reduce)}>
        <path d="M84 54 q0 -6 6 -6 q6 0 6 6" {...sw(2)} />
        <path d="M91 48.5 q-1 -4.5 3.5 -5 q4.5 0.5 4 5.5 q2 0.5 1.5 5" {...sw(1.4)} />
        <path d="M87 50.5 q2 1.5 4 0.5 M93.5 47 l1.5 1.5" {...sw(1.2, 0.5)} />
      </g>
      {/* 사울 — 주역 굵기 */}
      <g transform={reduce ? undefined : 'translate(0 9)'} style={d(2400, reduce)}>
        <circle cx="93" cy="26" r="3.4" {...sw(2.5)} />
        <path d="M93 29.6 v10 M86.5 34 q6.5 -3.5 13 0" {...sw(2.5)} />
        <path d="M90 31.5 q3 1.2 6 0" {...sw(1.3, 0.6)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="translate" from="0 9" to="0 0"
            begin="2.6s" dur="0.8s" fill="freeze" calcMode="spline" keySplines="0.3 0 0.4 1" keyTimes="0;1" />
        )}
      </g>
      <g style={d(reduce ? 0 : 3700, reduce)} stroke="var(--paper-accent)">
        <path d="M17 46 l-3 -4 M23 46 l3 -4 M28 47 l-3 -4 M34 47 l3 -4" {...sw(1.4)} />
      </g>
    </g>
  )
}

// 야베스 길르앗 구원 (삼상 11)
function JabeshRescueScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M88 54 v-16 h20 v16 M90 44 h16 M92 38 v-6 h7 v6" {...sw(2)} />
        <path d="M93.5 34 h1.8 m2 0 h1.8 M91 48 h2 m3 0 h2 m3 0 h2 M92.5 51 h2 m3 0 h2" {...sw(1.2, 0.55)} />
        <path d="M20 53 l0.9 -1.8 l0.9 1.8 M70 53.2 l0.8 -1.6 l0.8 1.6" {...sw(1.1, 0.45)} />
      </g>
      <g style={d(800, reduce)}>
        <path d="M50 54 l6 -9 l6 9 M54.5 54 l1.5 -3 l1.5 3" {...sw(1.8)} />
        <path d="M66 54 l5 -7.5 l5 7.5" {...sw(1.6, 0.8)} />
        <path d="M53 50 l2.2 -3.2 M69 50.5 l2 -3" {...sw(1.2, 0.5)} />
      </g>
      <g transform={reduce ? undefined : 'translate(0 5)'} style={d(1500, reduce)}>
        <path d="M12 54 a7 7 0 0 1 14 0" {...sw(2.4)} />
        <path d="M19 43.5 v-3 M10.5 47 l-2.2 -2.2 M27.5 47 l2.2 -2.2 M14 44.5 l-1.4 -2 M24 44.5 l1.4 -2" {...sw(1.3)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="translate" from="0 5" to="0 0"
            begin="1.6s" dur="1.1s" fill="freeze" />
        )}
      </g>
      {/* 돌격 창 — 핵심 */}
      <g transform={reduce ? undefined : 'translate(-14 0)'} style={d(2300, reduce)}>
        <path d="M28 52.5 l11 -6 M29 47 l11 -5.5 M27 45 l10 -5" {...sw(2.6)} />
        <path d="M39 46.5 l3.2 -1.7 M40 41.5 l3.2 -1.5 M37 40 l3 -1.5" {...sw(1.6)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="translate" from="-14 0" to="5 0"
            begin="2.5s" dur="0.9s" fill="freeze" calcMode="spline" keySplines="0.4 0 0.6 1" keyTimes="0;1" />
        )}
      </g>
    </g>
  )
}

// 길갈 왕위 확정 (삼상 11:14-15)
function GilgalCoronationScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M78 41 q16 -9 30 -2" {...sw(1.1, 0.4)} />
        <path d="M14 53 l1 -2 l1 2 M60 53.2 l0.8 -1.6 l0.8 1.6" {...sw(1.1, 0.45)} />
      </g>
      <g style={d(700, reduce)}>
        <path d="M32 54 v-7 h16 v7 M30 47 h20" {...sw(2.2)} />
        <path d="M34 51 h3 m3 0 h3 m3 0 h3 M35.5 48.8 h3 m4 0 h3" {...sw(1.2, 0.55)} />
        <path d="M38 44.5 q-2.5 -4 0 -7 q2.5 3 0 7 M42 44.5 q-2 -4.5 0.5 -7.5" {...sw(2.6)} />
        <path d="M41 36 q-3 -4 0 -8 q3 -3 1.5 -7" {...sw(1.3, 0.6)} />
      </g>
      {/* 사울 — 주역 */}
      <g style={d(1500, reduce)}>
        <circle cx="72" cy="34" r="3.2" {...sw(2.5)} />
        <path d="M72 37.2 v9.3 M69 54 l3 -7.5 l3 7.5 M66.5 42.5 q5.5 -3 11 0" {...sw(2.5)} />
        <path d="M70 40 q2 1.2 4 0 M69.5 44.5 q2.5 1.2 5 0" {...sw(1.3, 0.6)} />
      </g>
      {/* 왕관 — 핵심 */}
      <g transform={reduce ? undefined : 'translate(0 -9)'} style={d(2400, reduce)}>
        <path d="M68.5 29 v-3.2 l1.8 2 l1.7 -3 l1.7 3 l1.8 -2 v3.2 h-7" {...sw(2.8)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="translate" from="0 -9" to="0 0"
            begin="2.6s" dur="0.6s" fill="freeze" calcMode="spline" keySplines="0.3 0 0.5 1" keyTimes="0;1" />
        )}
      </g>
      <g style={d(reduce ? 0 : 3400, reduce)}>
        <circle cx="92" cy="45" r="2.5" {...sw(1.8)} />
        <path d="M92 47.5 v4 M89.8 54 l2.2 -2.5 l2.2 2.5" {...sw(1.8)} />
        <path d="M89 43 l-2.8 -3.6 M95 43 l2.8 -3.6" stroke="var(--paper-accent)" {...sw(1.4)} />
      </g>
    </g>
  )
}

// 믹마스 전투 (삼상 14:6-23)
function MichmashBattleScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M6 44 l14 -14 l10 7 l8 17" {...sw(2.2)} />
        <path d="M114 42 l-12 -18 l-10 8 l-7 22" {...sw(2.2)} />
        <path d="M13 40 l4 -4 M104 34 l-4 -4 M20 34 l3 -2.5 M97 30 l-3 -2.5 M26 42 l3.5 -2 M92 40 l-3.5 -2" {...sw(1.2, 0.45)} />
      </g>
      {/* 적진 창 — 보조(원경) */}
      <g style={d(900, reduce)}>
        <path d="M92 24 l8 -4.5 M96 26.5 l8 -4 M100 29 l7 -3.5" {...sw(1.8)} />
        <path d="M100 19.5 l2.6 -1.3 M104 22.5 l2.6 -1.3" {...sw(1.3)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="rotate"
            values="0 102 24; 2.5 102 24; -2.5 102 24; 0 102 24" keyTimes="0;0.3;0.7;1"
            begin="3.9s" dur="0.5s" />
        )}
      </g>
      {/* 요나단·병기 든 자 — 주역 */}
      <g transform={reduce ? undefined : 'translate(-13 11)'} style={d(2000, reduce)}>
        <circle cx="93" cy="34" r="2.4" {...sw(2.4)} />
        <path d="M93 36.4 l-1.5 5 M91.5 41.5 l-3 3.5 M93.5 38 l3.5 2.5" {...sw(2.4)} />
        <path d="M96.5 40 l2.5 -3.5" {...sw(1.6)} />
        <circle cx="85" cy="42" r="2.2" {...sw(2)} />
        <path d="M85 44.2 l-1.5 4.5 M84 48.5 l-3 3" {...sw(2)} />
        <path d="M86.5 45.5 l2.5 2" {...sw(1.3)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="translate" from="-13 11" to="0 0"
            begin="2.2s" dur="1.4s" fill="freeze" calcMode="spline" keySplines="0.35 0 0.6 1" keyTimes="0;1" />
        )}
      </g>
    </g>
  )
}

// 아말렉 불순종 — 찢어진 옷자락 (삼상 15:27-28)
function GilgalAmalekScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M10 43 q13 -8 25 -2" {...sw(1.1, 0.4)} />
        <path d="M18 53 l0.9 -1.8 l0.9 1.8 M70 53.2 l0.8 -1.6 l0.8 1.6" {...sw(1.1, 0.45)} />
      </g>
      {/* 사무엘 — 주역, 로브 주름 */}
      <g style={d(700, reduce)}>
        <circle cx="30" cy="26" r="3.4" {...sw(2.5)} />
        <path d="M25 54 l2.5 -21 h5 l2.5 21 M25 54 h10" {...sw(2.5)} />
        <path d="M28.5 38 q0.5 8 0 14 M31.8 38 q0.4 8 0 14" {...sw(1.3, 0.55)} />
        <path d="M33.5 36 q6 1 9 4.5" {...sw(2.2)} />
      </g>
      {/* 사울(무릎) — 주역 */}
      <g style={d(1500, reduce)}>
        <circle cx="54" cy="38" r="3" {...sw(2.4)} />
        <path d="M54 41 l-1.5 6.5 M47 54 h11 M52.5 47.5 q-4 2 -5.5 6.5 M52 44 q4.5 0.5 7 3" {...sw(2.4)} />
        <path d="M50.5 45 q1.5 1.5 3.5 1.2" {...sw(1.3, 0.6)} />
      </g>
      {/* 살려둔 양 — 보조 */}
      <g style={d(2200, reduce)}>
        <path d="M84 51 q0 -4.5 5.5 -4.5 q5.5 0 5.5 4.5 q0 3 -5.5 3 q-5.5 0 -5.5 -3" {...sw(1.8)} />
        <circle cx="97" cy="47.5" r="2.2" {...sw(1.8)} />
        <path d="M86 54 v-1 M93 54 v-1 M88.5 54 v-0.8 M91 54 v-0.8" {...sw(1.3)} />
        <path d="M86.5 49 q1.8 1.4 3.6 0 m1 -1.8 q1.6 1.2 3.2 0" {...sw(1.1, 0.5)} />
      </g>
      {/* 옷자락 — 핵심 */}
      <g style={d(2700, reduce)}>
        <path d="M40 45 l4.5 -1.8 l1.5 3.2 l-4.5 1.8 z" {...sw(2.6)}>
          {!reduce && (
            <animateMotion path="M0 0 q6 -5 12 -2" begin="2.9s" dur="0.6s" fill="freeze"
              calcMode="spline" keySplines="0.3 0 0.7 1" keyTimes="0;1" />
          )}
        </path>
      </g>
    </g>
  )
}

// 베들레헴 기름부음 (삼상 16:12-13)
function BethlehemAnointingScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M82 44 q14 -8 28 -2" {...sw(1.1, 0.4)} />
        <path d="M16 53 l1 -2 l1 2 M46 53.2 l0.8 -1.6 l0.8 1.6" {...sw(1.1, 0.45)} />
      </g>
      {/* 사무엘 — 보조(이 장면의 주역은 다윗과 뿔병) */}
      <g style={d(700, reduce)}>
        <circle cx="32" cy="27" r="3.4" {...sw(2.2)} />
        <path d="M27 54 l2.5 -20.5 h5 l2.5 20.5 M27 54 h10" {...sw(2.2)} />
        <path d="M30.5 38 q0.5 7.5 0 13 M33.5 38 q0.4 7.5 0 13" {...sw(1.3, 0.55)} />
        <path d="M35.5 36 q9 -5 16 -4" {...sw(2)} />
      </g>
      {/* 다윗 — 주역 */}
      <g style={d(1500, reduce)}>
        <circle cx="58" cy="40" r="2.8" {...sw(2.5)} />
        <path d="M58 42.8 v6.7 M55.5 54 l2.5 -4.5 l2.5 4.5" {...sw(2.5)} />
        <path d="M56.4 45.5 q1.6 1 3.2 0" {...sw(1.3, 0.6)} />
        <path d="M64 54 l0.5 -10 q0 -2.5 2.5 -2" {...sw(1.4)} />
        <path d="M74 51.5 q0 -3.5 4.5 -3.5 q4.5 0 4.5 3.5 q0 2.5 -4.5 2.5 q-4.5 0 -4.5 -2.5 M83.5 49.5 h2.5" {...sw(1.4, 0.7)} />
        <path d="M75.5 54 v-0.8 M81 54 v-0.8" {...sw(1.2, 0.6)} />
      </g>
      {/* 뿔병 — 핵심 */}
      <g transform={reduce ? 'rotate(-30 52 31)' : undefined} style={d(2400, reduce)}>
        <path d="M52 31 q4 -3.5 9 -2 l-0.5 2.5 q-4.5 -1 -8.5 1.5" {...sw(2.8)} />
        <path d="M59.5 29.6 l1.2 0.4" {...sw(1.4)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="rotate" from="0 52 31" to="-30 52 31"
            begin="2.8s" dur="0.5s" fill="freeze" />
        )}
      </g>
      <g style={d(reduce ? 0 : 3400, reduce)}>
        <path d="M56.5 32 v2 M58 35 v2" {...sw(1.4)} />
      </g>
      <g style={d(reduce ? 0 : 4000, reduce)} stroke="var(--paper-accent)">
        <path d="M58 20 v-4 M49 23 l-3 -3 M67 23 l3 -3 M53 21 l-1.6 -2.6 M63 21 l1.6 -2.6" {...sw(1.4)} />
      </g>
    </g>
  )
}

// 다윗을 시기하여 창을 던짐 (삼상 18:10-11)
function GibeahSpearScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M14 54 V24" {...sw(2.2)} />
        <path d="M14 30 h4 M14 40 h4 M14 26 q2.5 0.5 4 2" {...sw(1.2, 0.5)} />
      </g>
      {/* 왕좌의 사울 — 보조(어둑한 위압) */}
      <g style={d(700, reduce)}>
        <path d="M86 54 h24 M104 54 V36 M94 46 h9" {...sw(2)} />
        <path d="M104 38 h3 M104 42 h3" {...sw(1.2, 0.5)} />
        <circle cx="97" cy="36" r="3" {...sw(2.2)} />
        <path d="M97 39 v7 M93.5 42.5 q3.5 -2 7 -0.5" {...sw(2.2)} />
      </g>
      {/* 수금 타는 다윗 — 주역 */}
      <g transform={reduce ? 'rotate(-9 27 50)' : undefined} style={d(1600, reduce)}>
        <circle cx="27" cy="39" r="2.8" {...sw(2.5)} />
        <path d="M27 41.8 q-1 5 -4.5 6.2 M20 54 l3.5 -5.5 M29 48 l2 6" {...sw(2.5)} />
        <path d="M24.5 45 q1.5 1.3 3.2 0.6" {...sw(1.3, 0.6)} />
        <path d="M31 42.5 q-1 -8 3.5 -9.5 M37 42 q1.5 -7.5 -2.5 -9" {...sw(2.2)} />
        <path d="M32.5 36 v6 M34.5 35.5 v6 M36.2 35.8 v5.6" {...sw(1.2)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="rotate"
            values="0 27 50; -13 27 50; -8 27 50" keyTimes="0;0.5;1"
            begin="3.05s" dur="0.5s" fill="freeze" />
        )}
      </g>
      {/* 창 — 핵심 */}
      {!reduce && (
        <g style={d(2700, false)}>
          <path d="M88 41 l8 -1.5" {...sw(3)}>
            <animateMotion path="M0 0 L-64 6.5" begin="2.9s" dur="0.35s" fill="freeze"
              calcMode="spline" keySplines="0.2 0 0.6 1" keyTimes="0;1" />
          </path>
        </g>
      )}
      {reduce && <path d="M24 47.5 l8 -1.5" {...sw(3)} />}
    </g>
  )
}

// 엔게디의 자비 (삼상 24)
function EnGediScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M12 54 q3 -27 38 -29 q36 -2 44 29" {...sw(2.4)} />
        <path d="M30 32 l4 -3 M52 27 l4 -2 M76 30 l4 2 M22 40 l3.5 -2.5 M92 40 l-3.5 -2.5 M64 28 l4 -1" {...sw(1.2, 0.4)} />
      </g>
      {/* 잠든 사울 — 보조 + 왕관·창 */}
      <g style={d(1000, reduce)}>
        <circle cx="80" cy="48.5" r="2.8" {...sw(2)} />
        <path d="M77 49.5 q-10 2.5 -21 2 M55 51.5 l-8 1.2" {...sw(2)} />
        <path d="M62 50.5 q4 1.4 8 0.8" {...sw(1.3, 0.55)} />
        <path d="M86 54 l2 -13 M88 41 l-2.5 4 m2.5 -4 l2.5 4" {...sw(2.6)} />
        <path d="M83 45.5 v-2 l1.2 0.9 l1.1 -1.4 l1.1 1.4 l1.2 -0.9 v2" {...sw(1.4)} />
      </g>
      {/* 다윗 — 주역 */}
      <g style={d(2000, reduce)}>
        <circle cx="36" cy="42" r="2.6" {...sw(2.5)} />
        <path d="M36 44.6 q-2 4 -5.5 5 M28 54 l4.5 -5 M39 46 l4.5 1.5" {...sw(2.5)} />
        <path d="M33.5 47.5 q1.6 1 3.2 0.4" {...sw(1.3, 0.6)} />
        <path d="M43.5 47.5 l3.5 1" {...sw(1.6)} />
      </g>
      {/* 옷자락 — 핵심 */}
      <g style={d(2800, reduce)}>
        <path d="M58 51 l4 -1.3 l1.2 2.6 l-4 1.3 z" {...sw(2.6)}>
          {!reduce && (
            <animateMotion path="M0 0 q-7 -5 -13 -3" begin="3.1s" dur="0.7s" fill="freeze"
              calcMode="spline" keySplines="0.3 0 0.7 1" keyTimes="0;1" />
          )}
        </path>
      </g>
    </g>
  )
}

// 엔돌의 밤 (삼상 28)
function EndorMediumScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M8 22 q22 9 42 5 M66 18 q24 7 40 12" {...sw(1.2, 0.45)} />
        <path d="M18 26 q10 4 20 3 M78 24 q12 3.5 22 6" {...sw(1.1, 0.3)} />
      </g>
      {/* 화로 — 보조 + 연기 */}
      <g style={d(800, reduce)}>
        <path d="M32 54 q0 -5 6 -5 q6 0 6 5" {...sw(2)} />
        <path d="M34 49.5 l-2 4.5 M42 49.5 l2 4.5" {...sw(1.4)} />
        <path d="M38 47 q-4 -5 0 -9 q4 -4 0 -8 q-3 -3 -1 -6" {...sw(1.3, 0.7)} />
        <path d="M40.5 44 q-2.5 -3.5 -0.5 -7" {...sw(1.1, 0.45)} />
      </g>
      {/* 혼 — 가늘고 옅게(스산함) */}
      <g opacity="0.55" transform={reduce ? undefined : 'translate(0 8)'} style={d(2200, reduce)}>
        <circle cx="66" cy="29" r="3" {...sw(1.8)} />
        <path d="M61 44 l2 -11 h6 l2 11 M61 44 h10" {...sw(1.8)} />
        <path d="M64.5 36 q0.4 5 0 8 M67.5 36 q0.3 5 0 8" {...sw(1.1, 0.6)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="translate" from="0 8" to="0 -1"
            begin="2.5s" dur="1.3s" fill="freeze" calcMode="spline" keySplines="0.3 0 0.5 1" keyTimes="0;1" />
        )}
      </g>
      {/* 엎드러진 사울 — 주역 */}
      <g style={d(1500, reduce)}>
        <circle cx="93" cy="48" r="2.8" {...sw(2.5)} />
        <path d="M95.5 49.5 q6 -2.5 10 1.5 M90.5 50 l-4.5 3.5" {...sw(2.5)} />
        <path d="M96.5 51.5 q3.5 -1.2 6.5 0.8" {...sw(1.3, 0.6)} />
        <path d="M83 52.5 v-2 l1.4 1 l1.3 -1.6 l1.3 1.6 l1.4 -1 v2" {...sw(1.6)} />
      </g>
    </g>
  )
}

// 길보아 산의 최후 (삼상 31)
function GilboaDeathScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M6 52 L38 28 L62 38 L94 20 L114 30" {...sw(2.2)} />
        <path d="M28 36 l4 -3 M50 36 l3 -1.5 M80 28 l4 -2.5 M100 25 l3 1.5" {...sw(1.2, 0.4)} />
      </g>
      {/* 칼·화살 — 칼이 핵심 */}
      <g style={d(1000, reduce)}>
        <path d="M50 24 l-3.5 11" {...sw(3)} />
        <path d="M44.5 28.5 l6.5 2 M51 21 l-1 3.5" {...sw(2)} />
        <path d="M70 33 l5 -7 M72.5 27.5 l2.5 -1.5 m-1.5 3 l2.5 -1.5" {...sw(1.5)} />
        <path d="M84 28 l5 -6.5 M86.5 23 l2.4 -1.4 m-1.4 2.9 l2.4 -1.4" {...sw(1.5)} />
      </g>
      {/* 왕관 — 핵심(굴러떨어짐) */}
      <g style={d(2400, reduce)}>
        <path d="M54 32 v-2.6 l1.5 1.6 l1.4 -2.4 l1.4 2.4 l1.5 -1.6 v2.6 h-5.8" {...sw(2.8)}>
          {!reduce && (
            <animateMotion path="M0 0 q9 7 17 14" begin="2.8s" dur="0.9s" fill="freeze"
              calcMode="spline" keySplines="0.35 0 0.7 1" keyTimes="0;1" />
          )}
        </path>
      </g>
      <g style={d(reduce ? 0 : 3900, reduce)}>
        <path d="M94 13 q2 -2 4 0 q2 -2 4 0 M102 18 q1.8 -1.8 3.6 0 q1.8 -1.8 3.6 0" {...sw(1.3)} />
      </g>
    </g>
  )
}

// 헤브론의 유다 왕 (삼하 2:4)
function HebronKingScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M78 54 v-18 q10 -8 20 0 v18 M82 54 v-13 q6 -5 12 0 v13" {...sw(2)} />
        <path d="M80 40 h16 M80 45 h2 m4 0 h4 m4 0 h2 M81 49.5 h2 m10 0 h2" {...sw(1.2, 0.5)} />
        <path d="M14 53 l1 -2 l1 2" {...sw(1.1, 0.45)} />
      </g>
      {/* 다윗 — 주역 */}
      <g style={d(1000, reduce)}>
        <circle cx="48" cy="33" r="3.2" {...sw(2.5)} />
        <path d="M48 36.2 v10 M45 54 l3 -7.5 l3 7.5 M42.5 41.5 q5.5 -3 11 0" {...sw(2.5)} />
        <path d="M46 39 q2 1.2 4 0 M45.5 44 q2.5 1.3 5 0" {...sw(1.3, 0.6)} />
      </g>
      {/* 왕관 — 핵심 */}
      <g transform={reduce ? undefined : 'translate(0 -9)'} style={d(2000, reduce)}>
        <path d="M44.5 28 v-3.2 l1.8 2 l1.7 -3 l1.7 3 l1.8 -2 v3.2 h-7" {...sw(2.8)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="translate" from="0 -9" to="0 0"
            begin="2.2s" dur="0.6s" fill="freeze" calcMode="spline" keySplines="0.3 0 0.5 1" keyTimes="0;1" />
        )}
      </g>
      <g style={d(reduce ? 0 : 3000, reduce)}>
        <circle cx="20" cy="45" r="2.5" {...sw(1.8)} />
        <path d="M20 47.5 v4 M17.8 54 l2.2 -2.5 l2.2 2.5" {...sw(1.8)} />
        <circle cx="30" cy="46" r="2.4" {...sw(1.8)} />
        <path d="M30 48.4 v3.1 M28 54 l2 -2.4 l2 2.4" {...sw(1.8)} />
        <path d="M17 43 l-2.8 -3.5 M23 43 l2.6 -3.4 M33 44 l2.6 -3.4" stroke="var(--paper-accent)" {...sw(1.4)} />
      </g>
    </g>
  )
}

// 다윗 성 정복 (삼하 5:6-9)
function JerusalemConquestScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M26 54 q6 -14 20 -17 M94 54 q-6 -14 -20 -17" {...sw(2)} />
        <path d="M46 37 h28 v-11 h-28 z" {...sw(2.4)} />
        <path d="M48 26 v-2.5 h3 v2.5 m4 0 v-2.5 h3 v2.5 m4 0 v-2.5 h3 v2.5 m4 0 v-2.5 h3 v2.5" {...sw(1.6)} />
        <path d="M50 30 h4 m5 0 h4 m5 0 h4 M52 33.5 h4 m7 0 h4" {...sw(1.2, 0.5)} />
        <path d="M34 46 l4 -3 M86 46 l-4 -3" {...sw(1.2, 0.4)} />
      </g>
      <g style={d(1000, reduce)}>
        <path d="M60 54 V37" {...sw(1.8)} strokeDasharray="2.5 2" />
      </g>
      {/* 오르는 용사 — 주역 */}
      <g transform={reduce ? undefined : 'translate(0 13)'} style={d(1800, reduce)}>
        <circle cx="60" cy="41" r="2.2" {...sw(2.4)} />
        <path d="M60 43.2 v4 M57.5 45 h5 M58 50 l2 -2.8 l2 2.8" {...sw(2.2)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="translate" from="0 13" to="0 0"
            begin="2.3s" dur="1.4s" fill="freeze" calcMode="spline" keySplines="0.35 0 0.6 1" keyTimes="0;1" />
        )}
      </g>
      {/* 깃발 — 핵심 */}
      <g style={d(reduce ? 0 : 4000, reduce)} stroke="var(--paper-accent)">
        <path d="M60 26 v-9" {...sw(2.2)} />
        <path d="M60 17 q4 1.5 7 0 l0 4.5 q-3 1.5 -7 0" {...sw(1.6)} />
      </g>
    </g>
  )
}

// 언약궤의 입성 (삼하 6:14-15)
function ArkJerusalemScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M96 42 q10 -7 18 -2" {...sw(1.1, 0.4)} />
        <path d="M36 53 l0.9 -1.8 l0.9 1.8 M88 53.2 l0.8 -1.6 l0.8 1.6" {...sw(1.1, 0.45)} />
      </g>
      {/* 행렬 — 궤가 핵심, 메는 이는 보조 */}
      <g transform={reduce ? undefined : 'translate(-8 0)'} style={d(900, reduce)}>
        <path d="M42 41 h36" {...sw(2)} />
        <path d="M52 41 v-8 h14 v8 M50 33 h18" {...sw(2.6)} />
        <path d="M54 38 h10 M56 35.5 h6" {...sw(1.2, 0.5)} />
        <path d="M56 32.5 q-3 -5 2 -6 M62 32.5 q3 -5 -2 -6" {...sw(1.4)} />
        <circle cx="46" cy="37.5" r="2.6" {...sw(1.9)} />
        <path d="M46 40.1 v7 M43.5 54 l2.5 -7 l2.5 7" {...sw(1.9)} />
        <circle cx="74" cy="37.5" r="2.6" {...sw(1.9)} />
        <path d="M74 40.1 v7 M71.5 54 l2.5 -7 l2.5 7" {...sw(1.9)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="translate" from="-8 0" to="4 0"
            begin="2.1s" dur="2.4s" fill="freeze" calcMode="spline" keySplines="0.3 0 0.7 1" keyTimes="0;1" />
        )}
      </g>
      {/* 춤추는 다윗 — 주역 */}
      <g style={d(2000, reduce)}>
        <circle cx="22" cy="34" r="2.8" {...sw(2.5)} />
        <path d="M22 36.8 v8 M19 54 l3 -9 M26 53 l-4 -8.5" {...sw(2.5)} />
        <path d="M22 39 q-4.5 -3.5 -5.5 -8 M22 39 q4.5 -3.5 5.5 -8" {...sw(2.3)} />
        <path d="M20.5 41.5 q1.5 1.2 3 0.4" {...sw(1.3, 0.6)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="rotate"
            values="-8 22 45; 8 22 45; -6 22 45; 0 22 45" keyTimes="0;0.35;0.7;1"
            begin="2.4s" dur="1.6s" />
        )}
      </g>
      <g style={d(reduce ? 0 : 3800, reduce)} stroke="var(--paper-accent)">
        <path d="M12 24 v-4 M15.5 22 v-4" {...sw(1.4)} />
        <circle cx="11" cy="24.6" r="1" {...sw(1.4)} />
        <circle cx="14.5" cy="22.6" r="1" {...sw(1.4)} />
      </g>
    </g>
  )
}

// 다윗 언약의 밤 (삼하 7:12-16)
function NathanCovenantScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M48 54 v-12 l12 -8 l12 8 v12 M56 54 v-7 h8 v7" {...sw(2.4)} />
        <path d="M50 45 h3 m14 0 h3 M52 49 h2 m12 0 h2" {...sw(1.2, 0.5)} />
      </g>
      {/* 별 — 가늘게, 차례로 */}
      <g style={d(1000, reduce)}>
        <path d="M20 20 v3 m-1.5 -1.5 h3" {...sw(1.3)} />
        <path d="M34 12 v3 m-1.5 -1.5 h3" {...sw(1.3)} />
        <path d="M90 16 v3 m-1.5 -1.5 h3" {...sw(1.3)} />
      </g>
      <g style={d(1800, reduce)}>
        <path d="M102 26 v3 m-1.5 -1.5 h3" {...sw(1.2, 0.8)} />
        <path d="M12 32 v3 m-1.5 -1.5 h3" {...sw(1.2, 0.8)} />
        <path d="M78 8 v3 m-1.5 -1.5 h3" {...sw(1.2, 0.8)} />
        <path d="M26 27 v2 m-1 -1 h2 M96 8 v2 m-1 -1 h2" {...sw(1.1, 0.6)} />
      </g>
      {/* 왕관 — 핵심 */}
      <g style={d(2600, reduce)}>
        <path d="M56.5 30 v-3 l1.6 1.8 l1.9 -2.8 l1.9 2.8 l1.6 -1.8 v3 h-7" {...sw(2.8)} />
      </g>
      {/* 큰 별 — 핵심(맥동) */}
      <g style={d(reduce ? 0 : 3400, reduce)} stroke="var(--paper-accent)">
        <path d="M60 10 v4 m-2 -2 h4 M57 8.5 l-1.6 -1.6 M63 8.5 l1.6 -1.6 M57 13.5 l-1.6 1.6 M63 13.5 l1.6 1.6" {...sw(2)}>
          {!reduce && <animate attributeName="opacity" values="1;0.45;1;0.6;1" begin="4.2s" dur="1.6s" />}
        </path>
        <path d="M60 17 v2 m0 3 v2 m0 3 v2" {...sw(1.3)} />
      </g>
    </g>
  )
}

// 기브온의 꿈 (왕상 3:5-12)
function GibeonDreamScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M16 54 v-6 h14 v6 M14 48 h18" {...sw(2.2)} />
        <path d="M18 51.5 h3 m4 0 h3" {...sw(1.2, 0.55)} />
      </g>
      {/* 번제의 불 — 핵심 */}
      <g style={d(800, reduce)}>
        <path d="M21 45.5 q-2.5 -5 0 -8.5 q2.5 3.5 0 8.5 M25.5 45.5 q-2 -5.5 0.8 -9" {...sw(2.8)} />
        <path d="M23.5 43 q-1 -2.5 0.3 -4.5" {...sw(1.3, 0.6)} />
        <path d="M24 34 q-3 -4 0 -8 q3 -3 1.5 -6.5" {...sw(1.2, 0.6)} />
      </g>
      {/* 잠든 솔로몬 — 주역 */}
      <g style={d(1600, reduce)}>
        <circle cx="76" cy="50" r="2.8" {...sw(2.5)} />
        <path d="M79 51 q10 1.5 17 0.5 M74 52.5 l-5 1" {...sw(2.5)} />
        <path d="M82 52.3 q6 1 11 0.4" {...sw(1.3, 0.55)} />
      </g>
      {/* 꿈 구름 — 가늘게 */}
      <g style={d(2400, reduce)}>
        <circle cx="72" cy="43" r="1.2" {...sw(1.3)} />
        <circle cx="69" cy="38" r="1.8" {...sw(1.3)} />
        <path d="M56 30 q0 -7 8 -7 q3 -5 10 -4 q8 -1 9 6 q6 2 3 6.5 q-4 4 -12 3 q-9 2 -14 -1 q-5 -1.5 -4 -3.5" {...sw(1.6)} />
      </g>
      {/* 등불 — 핵심 */}
      <g style={d(reduce ? 0 : 3400, reduce)} stroke="var(--paper-accent)">
        <path d="M72 27 h8 M74 27 q0 -2.5 2 -2.5 q2 0 2 2.5" {...sw(2)} />
        <path d="M76 22.5 q-1.3 -2.5 0 -4.5 q1.3 2 0 4.5" {...sw(1.6)} />
      </g>
    </g>
  )
}

// 성전 건축 (왕상 6) — draw 자체가 건축
function TempleBuildScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M28 54 h64 M32 50 h56" {...sw(2.2)} />
        <path d="M36 52 h4 m6 0 h4 m6 0 h4 m6 0 h4 m6 0 h4 m6 0 h4" {...sw(1.2, 0.5)} />
      </g>
      {/* 두 기둥(야긴·보아스) — 핵심 */}
      <g style={d(900, reduce)}>
        <path d="M44 50 v-19 M76 50 v-19" {...sw(2.8)} />
        <path d="M41.5 31 h5 M73.5 31 h5" {...sw(2.2)} />
        <path d="M42.5 33.5 h4 M74.5 33.5 h4" {...sw(1.3, 0.6)} />
      </g>
      <g style={d(1800, reduce)}>
        <path d="M36 50 v-15 M84 50 v-15" {...sw(2.2)} />
        <path d="M56 50 v-10 h8 v10" {...sw(2.2)} />
        <path d="M60 50 v-10 M40 40 h2.5 m37.5 0 h2.5 M37.5 44 h2 m43 0 h2" {...sw(1.3, 0.55)} />
      </g>
      <g style={d(2700, reduce)}>
        <path d="M32 35 L60 22 L88 35" {...sw(2.6)} />
        <path d="M38 32.2 L82 32.2" {...sw(1.2, 0.5)} />
        <path d="M46 29 L74 29" {...sw(1.1, 0.4)} />
      </g>
      {/* 비계·일꾼 — 가늘게 */}
      <g style={d(3600, reduce)}>
        <path d="M96 54 l7 -20 M96.8 50 h4.5 M98.2 45 h4.5 M99.6 40 h4.4" {...sw(1.4)} />
        <circle cx="90" cy="30" r="2" {...sw(1.6)} />
        <path d="M90 32 l-1.5 3 M89 33.5 l3 1" {...sw(1.4)} />
      </g>
      <g style={d(reduce ? 0 : 4400, reduce)} stroke="var(--paper-accent)">
        <path d="M60 16 v-3.5 M52 18 l-2.4 -2.4 M68 18 l2.4 -2.4" {...sw(1.4)} />
      </g>
    </g>
  )
}

// 성전 봉헌의 불 (왕상 8; 대하 7:1)
function TempleDedicationScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M34 54 h60 M42 50 h44" {...sw(2)} />
        <path d="M48 50 v-14 M80 50 v-14 M38 36 L64 25 L90 36" {...sw(2.4)} />
        <path d="M60 50 v-8 h8 v8" {...sw(2)} />
        <path d="M44 40 h2 m38 0 h2 M46 44.5 h2 m32 0 h2 M64 50 v-8" {...sw(1.2, 0.5)} />
      </g>
      <g style={d(1000, reduce)}>
        <path d="M16 54 v-5 h10 v5 M14 49 h14" {...sw(2)} />
        <path d="M18 51.5 h2.5 m3 0 h2.5" {...sw(1.2, 0.55)} />
      </g>
      {/* 엎드린 무리 — 보조 */}
      <g style={d(1800, reduce)}>
        <circle cx="104" cy="47" r="2.5" {...sw(1.8)} />
        <path d="M106 48.5 q5 -2 8 1 M102 49 l-4 3.5" {...sw(1.8)} />
        <circle cx="99" cy="50" r="2" {...sw(1.5, 0.8)} />
        <path d="M100.5 51.2 q3.5 -1.4 6 0.8" {...sw(1.5, 0.8)} />
      </g>
      {/* 내려오는 불 — 핵심 */}
      <g transform={reduce ? undefined : 'translate(0 -30)'} style={d(2500, reduce)}>
        <path d="M21 46 q-2.8 -5 0 -9.5 q2.8 4.5 0 9.5 M24.8 46 q-2 -5.5 0.8 -9" {...sw(2.8)} />
        <path d="M23 43.5 q-1 -2.5 0.3 -4.5" {...sw(1.3, 0.6)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="translate" from="0 -30" to="0 0"
            begin="2.7s" dur="0.5s" fill="freeze" calcMode="spline" keySplines="0.4 0 0.8 1" keyTimes="0;1" />
        )}
      </g>
      {/* 영광 — 강조색 아치 */}
      <g style={d(reduce ? 0 : 3600, reduce)} stroke="var(--paper-accent)">
        <path d="M34 18 q30 -12 60 0" {...sw(1.8)} />
        <path d="M40 13 q24 -9 48 0" {...sw(1.3)} />
      </g>
    </g>
  )
}

const SCENES = {
  'authored-saul-mizpah-chosen': { Scene: MizpahChosenScene, caption: '미스바의 제비뽑기 — 사무엘상 10장' },
  'authored-saul-jabesh-rescue': { Scene: JabeshRescueScene, caption: '야베스 길르앗 구원 — 사무엘상 11장' },
  'authored-saul-gilgal-coronation': { Scene: GilgalCoronationScene, caption: '길갈의 대관식 — 사무엘상 11장' },
  'authored-saul-michmash-battle': { Scene: MichmashBattleScene, caption: '믹마스 협곡의 기습 — 사무엘상 14장' },
  'authored-saul-gilgal-amalek': { Scene: GilgalAmalekScene, caption: '찢어진 옷자락 — 사무엘상 15장' },
  'authored-samuel-bethlehem-david-anointing': { Scene: BethlehemAnointingScene, caption: '베들레헴의 기름부음 — 사무엘상 16장' },
  'authored-saul-gibeah-spear': { Scene: GibeahSpearScene, caption: '수금과 창 — 사무엘상 18장' },
  'authored-david-goliath-gath': { Scene: GoliathScene, caption: '다윗과 골리앗 — 사무엘상 17장' },
  'authored-david-en-gedi-saul': { Scene: EnGediScene, caption: '엔게디 동굴의 자비 — 사무엘상 24장' },
  'authored-saul-endor-medium': { Scene: EndorMediumScene, caption: '엔돌의 밤 — 사무엘상 28장' },
  'authored-saul-gilboa-death': { Scene: GilboaDeathScene, caption: '길보아 산의 최후 — 사무엘상 31장' },
  'authored-david-hebron-king-judah': { Scene: HebronKingScene, caption: '헤브론의 유다 왕 — 사무엘하 2장' },
  'authored-david-jerusalem-conquest': { Scene: JerusalemConquestScene, caption: '다윗 성 정복 — 사무엘하 5장' },
  'authored-david-ark-jerusalem': { Scene: ArkJerusalemScene, caption: '언약궤의 입성 — 사무엘하 6장' },
  'authored-david-nathan-covenant': { Scene: NathanCovenantScene, caption: '다윗 언약의 밤 — 사무엘하 7장' },
  'authored-solomon-gibeon-dream': { Scene: GibeonDreamScene, caption: '기브온의 꿈 — 열왕기상 3장' },
  'authored-solomon-jerusalem-temple-build': { Scene: TempleBuildScene, caption: '성전 건축 — 열왕기상 6장' },
  'authored-solomon-jerusalem-temple-dedication': { Scene: TempleDedicationScene, caption: '성전 봉헌의 불 — 열왕기상 8장' },
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
