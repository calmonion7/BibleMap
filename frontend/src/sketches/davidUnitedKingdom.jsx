// 다윗과 통일왕국 — 18개 정차지 장면 (task#226·227 저작 확정본)
import { sw, d } from './lib'
import { Label } from './SceneLabel'
// 인트로 오프닝 몽타주가 쓰는 장면 — 정의는 introMontage.jsx로 옮겼다(task#287).
// 방향이 중요하다: 무거운 투어 모듈이 소형 모듈을 참조해야 인트로가 투어 청크를 끌어오지 않는다.
import { BethlehemAnointingScene } from './introMontage'

// 골리앗 (삼상 17:49-50) — 물매 2회전 → 투석 → 휘청·쓰러짐 → 지면 진동 + 흙먼지
function GoliathScene({ reduce }) {
  return (
    <g>
      {!reduce && (
        <animateTransform attributeName="transform" type="translate"
          values="0 0; 0 1.3; 0 0; 0 0.6; 0 0" keyTimes="0;0.25;0.5;0.75;1"
          begin="7.35s" dur="0.3s" />
      )}
      {/* 무대 — 지면·능선 */}
      <g style={d(0, reduce)}>
        <path d="M4 54 h112" {...sw(1.6)} />
        <path d="M4 41 q13 -10 26 -2" {...sw(1.1, 0.4)} />
        <path d="M84 39 q18 -12 32 -3" {...sw(1.1, 0.4)} />
      </g>
      {/* 시내·자갈·풀 질감 */}
      <g style={d(280, reduce)}>
        <path d="M50 53 q8 -2.5 16 0" {...sw(1.3, 0.55)} />
        <path d="M56 51.5 h2 M62 52 h2 M52 52.5 h1.5" {...sw(1.2, 0.55)} />
        <path d="M14 52.5 l1 -2 l1 2 M42 53 l0.8 -1.6 l0.8 1.6 M78 53 l0.9 -1.8 l0.9 1.8" {...sw(1.1, 0.45)} />
      </g>
      {/* 골리앗 — 실루엣을 크고 단순하게(다윗의 2배 높이), 잔 디테일은 덜어낸다 */}
      <g transform={reduce ? 'rotate(-50 103 41)' : undefined}>
        {/* 다리·정강이받이 — 무릎을 완만하게 굽혀 마름모로 벌어지지 않게 한다(지면 돌출 없이) */}
        <g style={d(560, reduce)}>
          <path d="M96 37 l-1 9 l2.5 8 M111 37 l1 9 l-2.5 8" {...sw(2.6)} />
          <path d="M94.5 41.5 h2 M110.5 41.5 h2 M95.3 50 h2 M109.3 50 h2" {...sw(1.3)} />
          <path d="M97.5 54 h2.5 M108.5 54 h2.5" {...sw(1.6)} />
        </g>
        {/* 몸통 — 어깨는 완만한 호로, 갑주 단은 절반 이하 짧게(상자·가로대로 읽히지 않게) */}
        <g style={d(840, reduce)}>
          <path d="M96 37 q1 -7 -3 -14 M111 37 q-1 -7 3 -14" {...sw(2.8)} />
          <path d="M93 23 q10.5 -3 21 0" {...sw(2.6)} />
          <path d="M99.5 30 h8" {...sw(1.8)} />
        </g>
        {/* 팔 — 방패·창을 쥔 손까지 */}
        <g style={d(1120, reduce)}>
          <path d="M93 23 q-3 3 -4 3" {...sw(2.4)} />
          <path d="M114 23 q-1 6 -2 10" {...sw(2.4)} />
          <path d="M91 25 h2 M111.5 27 h2" {...sw(1.1, 0.5)} />
        </g>
        {/* 투구 — 볼가림·작은 깃(머리 지름을 어깨 폭의 0.5배로 키워 로봇처럼 보이지 않게) */}
        <g style={d(1400, reduce)}>
          <path d="M98 15.3 q5.5 -5 11 0" {...sw(2.6)} />
          <path d="M98 15.3 l-0.8 7.2 M109 15.3 l0.8 7.2" {...sw(2.2)} />
          <path d="M103.5 12 q1 -1 2.5 -0.8" {...sw(1.4)} />
        </g>
        {/* 얼굴 — 위협(눈썹을 아래로 모은다) */}
        <g style={d(1680, reduce)}>
          <path d="M100 17 l3 2.3 M107 17 l-3 2.3" {...sw(1.2)} />
          <path d="M100.3 20 h2 M104.7 20 h2" {...sw(1.2)} />
          <path d="M101.5 21.3 h4" {...sw(1.2)} />
        </g>
        {/* 창 — 쓰러진 뒤 프레임을 벗어나지 않게 x를 몸통 쪽으로 붙인다 */}
        <g style={d(1960, reduce)}>
          <path d="M112 54 V12" {...sw(3)} />
          <path d="M109 18 l3 -6 l3 6" {...sw(2.2)} />
        </g>
        {/* 방패 — 가슴 높이에 둔다(쓰러졌을 때 바퀴처럼 보이거나 지면을 뚫지 않도록) */}
        <g style={d(2240, reduce)}>
          <circle cx="84" cy="27" r="5" {...sw(2.6)} />
          <path d="M84 22 v2 M79 27 h2" {...sw(1.2, 0.5)} />
        </g>
        {!reduce && (
          <animateTransform attributeName="transform" type="rotate"
            values="0 103 41; 5 103 41; -50 103 41" keyTimes="0; 0.22; 1"
            begin="6.65s" dur="0.7s" fill="freeze"
            calcMode="spline" keySplines="0.4 0 0.6 1; 0.55 0 0.85 0.7" />
        )}
      </g>
      {/* 다윗 — 다리(겉·안 두 선) */}
      <g style={d(2520, reduce)}>
        <path d="M23 54 l3 -7 M35 54 l-3 -7" {...sw(2.4)} />
        <path d="M25 54 l1.6 -6 M33 54 l-1.6 -6" {...sw(1.6)} />
        <path d="M22 54 h2.5 M35.5 54 h2.5" {...sw(1.4)} />
      </g>
      {/* 튜닉·주름·허리끈 — 어깨는 호로, 허리끈은 절반 이하 짧게(사다리로 읽히지 않게) */}
      <g style={d(2800, reduce)}>
        <path d="M24.5 47 l2 -7 q2.5 -1.3 5 0 l2 7" {...sw(2.6)} />
        <path d="M28.2 44.2 h2.6" {...sw(1.4)} />
        <path d="M28 43 q0.5 -2 0.3 -4 M31 43.3 q0.3 -2 0 -4" {...sw(1.3, 0.6)} />
      </g>
      {/* 팔·손 — 물매 쥔 손과 반대 손 */}
      <g style={d(3080, reduce)}>
        <path d="M31.5 40.5 q3 -6 5.5 -11.5" {...sw(2.2)} />
        <path d="M26.5 40.5 q-2.5 3 -4.5 5.5" {...sw(2.2)} />
        <path d="M36.3 28.7 q0.9 -0.6 1.7 0.2" {...sw(1.3)} />
      </g>
      {/* 머리 — 곱슬머리 실루엣 */}
      <g style={d(3360, reduce)}>
        <circle cx="29" cy="36" r="4" {...sw(2.6)} />
        <path d="M26.5 33 q0.8 -1 1.6 0 M28.7 32.6 q0.8 -1 1.6 0 M30.8 33 q0.7 -0.9 1.4 0" {...sw(1.4)} />
      </g>
      {/* 얼굴 — 결의(눈썹을 살짝 모아 집중한 표정) */}
      <g style={d(3640, reduce)}>
        <path d="M26.9 34.1 l1.3 0.5 M29.6 34.6 l1.3 -0.5" {...sw(1.1)} />
        <path d="M27 35.6 h1.3 M29.7 35.6 h1.3" {...sw(1.2)} />
        <path d="M27.9 38 h2.2" {...sw(1.2)} />
      </g>
      {/* 물매 — 회전 */}
      <g>
        <g style={d(3920, reduce)}>
          <path d="M37 29 l6 -6" {...sw(1.8)} />
        </g>
        <g style={d(4200, reduce)}>
          <circle cx="43" cy="23" r="1.9" {...sw(2)} />
        </g>
        {!reduce && (
          <animateTransform attributeName="transform" type="rotate"
            from="0 37 29" to="720 37 29" begin="5.6s" dur="0.6s"
            calcMode="spline" keySplines="0.35 0 0.75 1" keyTimes="0;1" />
        )}
      </g>
      <g style={d(4200, reduce)}>
        <path d="M29 22.5 a9.5 9.5 0 1 0 15 2.5" {...sw(1.2, 0.35)} />
      </g>
      {!reduce && (
        <g style={d(4200, false)}>
          <circle cx="43" cy="23" r="2" {...sw(2.2)}>
            <animateMotion path="M0 0 q31 -17 62 -3" begin="6.2s" dur="0.45s" fill="freeze"
              calcMode="spline" keySplines="0.3 0 0.75 1" keyTimes="0;1" />
            <animate attributeName="opacity" to="0" begin="6.65s" dur="0.15s" fill="freeze" />
          </circle>
        </g>
      )}
      {/* 흙먼지 — 마무리 강조 */}
      <g style={d(4480, reduce)} stroke="var(--paper-accent)">
        <path d="M62 44 q-3.5 -4 -7 -4.5 M66.5 41 q-0.5 -5 -3.5 -7.5 M72 41.5 q3 -4.5 7 -5 M76 45 q4 -2 7.5 -1.5" {...sw(1.3)} />
        <circle cx="59" cy="39" r="0.9" {...sw(1.3)} />
        <circle cx="70" cy="36.5" r="0.9" {...sw(1.3)} />
      </g>
      <Label x="20" y="7" at="2.6" reduce={reduce}>다윗</Label><Label x="100" y="7" at="1.6" reduce={reduce}>골리앗</Label>
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
      <Label x="31" y="35" at="1.5" reduce={reduce}>백성</Label><Label x="63" y="36" at="2.3" reduce={reduce}>제비뽑기</Label><Label x="99" y="16" at="3.5" reduce={reduce}>사울</Label>
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
      <Label x="98" y="27" at="0.9" reduce={reduce}>야베스 성</Label><Label x="30" y="34" at="3.2" reduce={reduce}>사울의 군대</Label>
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
      <Label x="40" y="30" at="1.5" reduce={reduce}>화목제</Label><Label x="79" y="21" at="3.3" reduce={reduce}>사울</Label>
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
      <Label x="99" y="12" at="1.7" reduce={reduce}>블레셋 진영</Label><Label x="84" y="30" at="3.7" reduce={reduce}>요나단</Label>
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
      <Label x="30" y="17" at="1.5" reduce={reduce}>사무엘</Label><Label x="55" y="31" at="2.3" reduce={reduce}>사울</Label><Label x="90" y="60" at="3" reduce={reduce}>살려둔 양</Label>
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
      <Label x="30" y="29" at="2.4" reduce={reduce}>다윗</Label><Label x="98" y="28" at="1.5" reduce={reduce}>사울</Label>
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
      <Label x="36" y="34" at="2.8" reduce={reduce}>다윗</Label><Label x="79" y="42" at="1.8" reduce={reduce}>잠든 사울</Label>
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
      <Label x="66" y="17" at="3.2" reduce={reduce}>사무엘의 혼</Label><Label x="95" y="42" at="2.3" reduce={reduce}>사울</Label>
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
      <Label x="44" y="17" at="1.8" reduce={reduce}>사울의 검</Label><Label x="80" y="52" at="3.9" reduce={reduce}>떨어진 왕관</Label>
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
      <Label x="48" y="22" at="1.8" reduce={reduce}>다윗</Label><Label x="88" y="31" at="0.9" reduce={reduce}>헤브론 성문</Label>
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
      <Label x="60" y="21" at="0.9" reduce={reduce}>여부스 요새</Label><Label x="79" y="47" at="2.8" reduce={reduce} anchor="start">물 긷는 통로</Label>
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
      <Label x="59" y="26" at="1.7" reduce={reduce}>언약궤</Label><Label x="22" y="24" at="2.8" reduce={reduce}>춤추는 다윗</Label>
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
      <Label x="88" y="47" at="1" reduce={reduce} anchor="start">다윗의 집</Label>
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
      <Label x="23" y="26" at="1.4" reduce={reduce}>일천번제</Label><Label x="86" y="45" at="2.3" reduce={reduce}>솔로몬</Label><Label x="76" y="35" at="4" reduce={reduce}>지혜의 꿈</Label>
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
      <Label x="44" y="60" at="1.4" reduce={reduce} size="4.2">보아스</Label><Label x="76" y="60" at="1.4" reduce={reduce} size="4.2">야긴</Label><Label x="60" y="20" at="3.2" reduce={reduce}>성전</Label>
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
      <Label x="21" y="33" at="3.4" reduce={reduce}>여호와의 불</Label><Label x="64" y="22" at="0.9" reduce={reduce}>성전</Label>
    </g>
  )
}

// ── 19장면 추가 저작(task#237 대상) ──

// 수금과 위로 (삼상 16:14-23)
function GibeahHarpScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M78 54 h24 M96 54 V32" {...sw(2)} />
        <path d="M96 34 h3 M96 38 h3" {...sw(1.2, 0.5)} />
      </g>
      {/* 사울 — 괴로워하는 자, 보조 */}
      <g style={d(700, reduce)}>
        <circle cx="90" cy="26" r="3.2" {...sw(2.4)} />
        <path d="M90 29.2 v9 M85 47 q3 -5 5 -8.8 M95 47 q-3 -5 -5 -8.8" {...sw(2.4)} />
        <path d="M87.5 24 l-2 -2 M89 22.5 q1.3 1.8 2.6 0" {...sw(1.4)} />
      </g>
      {/* 다윗 — 수금, 주역 */}
      <g style={d(1500, reduce)}>
        <circle cx="26" cy="38" r="2.8" {...sw(2.5)} />
        <path d="M26 40.8 q-1 5 -4 6.5 M19 54 l3.5 -5.5 M31 46.5 l2 6.5" {...sw(2.5)} />
        <path d="M30 41.5 q-1 -8 3 -10 M35.5 41 q1.5 -7.5 -2 -9.5" {...sw(2.2)} />
      </g>
      {/* 하프 줄 울림 — 핵심 */}
      <g style={d(2400, reduce)} stroke="var(--paper-accent)">
        <path d="M31.5 35 v6.2 M33.4 34.5 v6.2 M35.2 34.8 v5.8" {...sw(1.4)}>
          {!reduce && <animate attributeName="opacity" values="1;0.4;1;0.5;1" begin="2.6s" dur="1.6s" />}
        </path>
      </g>
      {/* 잦아드는 괴로움 — 핵심 */}
      <g style={d(reduce ? 0 : 3400, reduce)}>
        <path d="M85 22 q3 -3 6.5 -1.5" stroke="var(--paper-accent)" {...sw(1.3)}>
          {!reduce && <animate attributeName="opacity" values="0.7;0" begin="3.6s" dur="1s" fill="freeze" />}
        </path>
      </g>
      <Label x="26" y="27" at="1.5" reduce={reduce}>다윗</Label><Label x="90" y="19" at="0.7" reduce={reduce}>사울</Label>
    </g>
  )
}

// 라마 나욧으로의 도피 (삼상 19:18-24)
function RamahSamuelScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M10 44 q12 -8 24 -2" {...sw(1.1, 0.4)} />
        <path d="M16 53 l0.9 -1.8 l0.9 1.8" {...sw(1.1, 0.45)} />
      </g>
      {/* 사무엘 — 보조 */}
      <g style={d(700, reduce)}>
        <circle cx="26" cy="27" r="3.2" {...sw(2.2)} />
        <path d="M22 54 l2.2 -20 h5 l2.2 20 M22 54 h10" {...sw(2.2)} />
        <path d="M29 36 q5 1 7 4.5" {...sw(1.8)} />
      </g>
      {/* 다윗 — 달려오는 주역 */}
      <g transform={reduce ? undefined : 'translate(30 0)'} style={d(1500, reduce)}>
        <circle cx="42" cy="41" r="2.6" {...sw(2.5)} />
        <path d="M42 43.6 l-2 8.5 M40 54 l2.5 -6 M45.5 46 l4 -3.5" {...sw(2.5)} />
        <path d="M39 48 l-4 4.5 M46 42.5 l3.5 -4" {...sw(1.8)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="translate" from="30 0" to="0 0"
            begin="1.7s" dur="1.2s" fill="freeze" calcMode="spline" keySplines="0.35 0 0.6 1" keyTimes="0;1" />
        )}
      </g>
      {/* 예언하는 전령들 — 팔 든 무리 */}
      <g style={d(2400, reduce)}>
        <circle cx="70" cy="42" r="2.4" {...sw(1.8)} />
        <path d="M70 44.4 v7 M66 42 l4 2.4 l4 -2.4" {...sw(1.8)} />
        <circle cx="82" cy="41" r="2.4" {...sw(1.8)} />
        <path d="M82 43.4 v7 M78 41 l4 2.4 l4 -2.4" {...sw(1.8)} />
        <circle cx="94" cy="42.5" r="2.2" {...sw(1.6, 0.8)} />
        <path d="M94 44.7 v6.5 M90.3 42.5 l3.7 2.2 l3.7 -2.2" {...sw(1.6, 0.8)} />
      </g>
      {/* 내려놓인 창 — 핵심 */}
      <g style={d(reduce ? 0 : 3200, reduce)} stroke="var(--paper-accent)">
        <path d="M96 54 l10 -3" {...sw(2.4)} />
        <path d="M97.5 53.5 l0.6 -2 M99 53 l0.6 -2" {...sw(1.3)} />
      </g>
      <Label x="26" y="18" at="1.5" reduce={reduce}>사무엘</Label><Label x="42" y="33" at="2.7" reduce={reduce}>다윗</Label><Label x="82" y="33" at="3.5" reduce={reduce}>예언하는 전령들</Label>
    </g>
  )
}

// 놉의 제사장 아히멜렉 (삼상 21:1-9)
function NobPriestsScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M60 54 v-16 M60 38 h-14 v16 M46 54 v-16" {...sw(2)} />
        <path d="M50 44 h6 M50 48 h6" {...sw(1.2, 0.5)} />
      </g>
      {/* 아히멜렉 — 보조 */}
      <g style={d(700, reduce)}>
        <circle cx="52" cy="33" r="3" {...sw(2.2)} />
        <path d="M48 54 l2.2 -18 h4 l2.2 18 M48 54 h8" {...sw(2.2)} />
        <path d="M56.5 41 q4 1.5 5.5 5" {...sw(1.8)} />
      </g>
      {/* 다윗 — 받는 자, 주역 */}
      <g style={d(1500, reduce)}>
        <circle cx="30" cy="42" r="2.6" {...sw(2.5)} />
        <path d="M30 44.6 v6.5 M27.5 54 l2.5 -3 l2.5 3" {...sw(2.5)} />
        <path d="M33 47 l3.5 -3" {...sw(1.8)} />
        <path d="M36 44 h9 v3.5 h-9 z" {...sw(1.8)} />
      </g>
      {/* 도엑 — 기둥 뒤 배경, 옅게 */}
      <g opacity="0.5" style={d(2200, reduce)}>
        <path d="M92 54 V30" {...sw(1.6)} />
        <circle cx="98" cy="41" r="2.2" {...sw(1.6)} />
        <path d="M98 43.2 v7 M96 50 l2 -1.5 l2 1.5" {...sw(1.6)} />
      </g>
      {/* 진설병 + 골리앗의 칼 — 핵심 */}
      <g style={d(reduce ? 0 : 2900, reduce)} stroke="var(--paper-accent)">
        <path d="M62 40 h8 v-2.5 h-8 z" {...sw(1.6)} />
        <path d="M77 54 V33 M74.5 36 l2.5 -3 l2.5 3" {...sw(1.8)} />
      </g>
      <Label x="52" y="24" at="1.5" reduce={reduce}>아히멜렉</Label><Label x="30" y="33" at="2.3" reduce={reduce}>다윗</Label><Label x="98" y="26" at="3.1" reduce={reduce}>도엑</Label>
    </g>
  )
}

// 가드 왕 아기스 앞의 광인 행세 (삼상 21:10-15)
function GathAchishScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M70 54 V20 M70 20 h30 M100 20 v34" {...sw(2.2)} />
        <path d="M74 24 h4 m5 0 h4 m5 0 h4 M76 30 h4 m5 0 h4" {...sw(1.2, 0.5)} />
      </g>
      {/* 아기스와 신하 — 보조 */}
      <g style={d(700, reduce)}>
        <circle cx="90" cy="33" r="2.8" {...sw(2)} />
        <path d="M90 35.8 v7.5 M86.5 47 q3.5 -2 7 0" {...sw(2)} />
        <circle cx="80" cy="38" r="2.2" {...sw(1.6, 0.75)} />
        <path d="M80 40.2 v6 M77.5 48 q2.5 -1.6 5 0" {...sw(1.6, 0.75)} />
      </g>
      {/* 다윗 — 미친 체하는 주역, 문에 긁적임 */}
      <g transform={reduce ? 'rotate(4 26 44)' : undefined} style={d(1500, reduce)}>
        <circle cx="26" cy="35" r="2.8" {...sw(2.5)} />
        <path d="M26 37.8 v9 M23 54 l3 -7 M30 51 l-4 -7" {...sw(2.5)} />
        <path d="M28.5 40 q4 0 6 -3" {...sw(2.2)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="rotate"
            values="0 26 44; 6 26 44; -6 26 44; 4 26 44" keyTimes="0;0.3;0.65;1"
            begin="2.6s" dur="0.7s" fill="freeze" />
        )}
      </g>
      {/* 문에 남긴 자국 + 침 — 세부 */}
      <g style={d(2200, reduce)}>
        <path d="M33 30 l4 -1 M33 34 l4.5 -0.5 M33 38 l4 1" {...sw(1.4)} />
        <path d="M31 40 q0.5 3 -0.5 5.5" {...sw(1.1, 0.5)} />
      </g>
      <Label x="90" y="24" at="0.7" reduce={reduce}>아기스</Label><Label x="26" y="26" at="1.6" reduce={reduce}>다윗</Label>
    </g>
  )
}

// 아둘람 굴의 사람들 (삼상 22:1-2)
function AdullamCaveScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M8 54 q2 -22 20 -26 q18 -4 24 8 q3 8 -2 14" {...sw(2.4)} />
        <path d="M16 40 l3 -3 M30 28 l3.5 -2" {...sw(1.2, 0.4)} />
      </g>
      {/* 다윗 — 굴 앞, 주역 */}
      <g style={d(700, reduce)}>
        <circle cx="24" cy="37" r="2.8" {...sw(2.5)} />
        <path d="M24 39.8 v8.5 M21 54 l3 -5.7 l3 5.7" {...sw(2.5)} />
        <path d="M21.5 42.5 q2.5 1.2 5 0" {...sw(1.3, 0.6)} />
      </g>
      {/* 첫 무리 — 보조 */}
      <g transform={reduce ? undefined : 'translate(14 0)'} style={d(1500, reduce)}>
        <circle cx="60" cy="44" r="2.2" {...sw(1.8)} />
        <path d="M60 46.2 l-1.2 7.8 M58 54 l1 -3.3 M63 51.5 l-1.7 -5.3" {...sw(1.8)} />
        <circle cx="70" cy="43" r="2.2" {...sw(1.8)} />
        <path d="M70 45.2 v8.8 M67.7 54 l1.6 -3.4 M73 52 l-2 -6.8" {...sw(1.8)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="translate" from="14 0" to="0 0"
            begin="1.6s" dur="1.4s" fill="freeze" calcMode="spline" keySplines="0.3 0 0.6 1" keyTimes="0;1" />
        )}
      </g>
      {/* 둘째 무리 — 더 뒤에서, 원경 */}
      <g transform={reduce ? undefined : 'translate(20 0)'} style={d(2200, reduce)}>
        <circle cx="88" cy="45.5" r="2" {...sw(1.5, 0.7)} />
        <path d="M88 47.5 v7 M86 54 l2 -3 l2 3" {...sw(1.5, 0.7)} />
        <circle cx="98" cy="46" r="1.9" {...sw(1.4, 0.6)} />
        <path d="M98 47.9 v6.6 M96.2 54 l1.8 -2.8 l1.8 2.8" {...sw(1.4, 0.6)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="translate" from="20 0" to="0 0"
            begin="2.3s" dur="1.5s" fill="freeze" calcMode="spline" keySplines="0.3 0 0.6 1" keyTimes="0;1" />
        )}
      </g>
      <Label x="24" y="28" at="0.7" reduce={reduce}>다윗</Label><Label x="70" y="36" at="1.6" reduce={reduce}>사백 명의 무리</Label>
    </g>
  )
}

// 놉 성읍의 학살 (삼상 22:18-19)
function NobMassacreScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M80 54 v-14 h10 v14 M92 54 v-18 h8 v18" {...sw(2)} />
        <path d="M82 44 h6 M94 40 h4" {...sw(1.2, 0.5)} />
      </g>
      {/* 사울 — 명하는 자, 원경 */}
      <g opacity="0.7" style={d(700, reduce)}>
        <circle cx="14" cy="30" r="2.6" {...sw(2)} />
        <path d="M14 32.6 v9 M11 47 q3 -3 6 0" {...sw(2)} />
        <path d="M17 34.5 l3 -2" {...sw(1.4)} />
      </g>
      {/* 도엑 — 칼 든 자, 주역 */}
      <g transform={reduce ? 'rotate(35 46 40)' : undefined} style={d(1500, reduce)}>
        <circle cx="46" cy="34" r="2.8" {...sw(2.5)} />
        <path d="M46 36.8 v9.5 M43 54 l3 -7.7 l3 7.7" {...sw(2.5)} />
        <path d="M49 38 l7 -6" {...sw(2.4)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="rotate"
            values="0 46 40; -20 46 40; 35 46 40" keyTimes="0;0.3;1"
            begin="2.6s" dur="0.6s" fill="freeze" calcMode="spline" keySplines="0.4 0 0.6 1;0.5 0 0.7 1" />
        )}
      </g>
      {/* 쓰러진 제사장들 — 핵심 */}
      <g style={d(2200, reduce)}>
        <path d="M60 52 l8 -1.5 M61 50.5 l6 -1" {...sw(2.2)} />
        <path d="M70 53 l7 -2 M71 51.5 l5.5 -1.6" {...sw(2, 0.85)} />
        <path d="M62.5 48 v2.3 M73 47.5 v2.4" {...sw(1.3)} />
      </g>
      {/* 연기 — 원경 */}
      <g style={d(reduce ? 0 : 3200, reduce)}>
        <path d="M85 38 q-3 -5 0 -9 q3 -4 0 -8" {...sw(1.3, 0.6)} />
        <path d="M96 34 q-2.5 -4.5 0 -8.5" {...sw(1.2, 0.5)} />
      </g>
      <Label x="46" y="25" at="2.7" reduce={reduce}>도엑</Label><Label x="69" y="60" at="2.3" reduce={reduce}>제사장들</Label>
    </g>
  )
}

// 사무엘의 죽음과 애곡 (삼상 25:1)
function RamahDeathScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M50 54 q0 -6 8 -6 q8 0 8 6" {...sw(2)} />
        <path d="M54 50 h8" {...sw(1.3, 0.5)} />
      </g>
      {/* 사무엘의 겉옷 — 남겨진 자리 */}
      <g opacity="0.6" style={d(700, reduce)}>
        <path d="M52 49 l3 -2.5 h6 l3 2.5" {...sw(1.8)} />
        <path d="M55.5 47.5 q1.5 1 3 0" {...sw(1.2, 0.5)} />
      </g>
      {/* 애곡하는 무리 — 보조, 차례로 도착 */}
      <g transform={reduce ? undefined : 'translate(-16 0)'} style={d(1500, reduce)}>
        <circle cx="24" cy="43" r="2.4" {...sw(1.8)} />
        <path d="M24 45.4 l-1.5 8.6 M20 51 q2.5 -1.5 5 0" {...sw(1.8)} />
        <circle cx="34" cy="44" r="2.2" {...sw(1.7, 0.85)} />
        <path d="M34 46.2 l-1.3 7.8 M31 51 q2 -1.3 4.3 0" {...sw(1.7, 0.85)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="translate" from="-16 0" to="0 0"
            begin="1.6s" dur="1.5s" fill="freeze" calcMode="spline" keySplines="0.3 0 0.6 1" keyTimes="0;1" />
        )}
      </g>
      <g transform={reduce ? undefined : 'translate(16 0)'} style={d(2200, reduce)}>
        <circle cx="86" cy="44.5" r="2.2" {...sw(1.7, 0.8)} />
        <path d="M86 46.7 l1.3 7.3 M84 52 q1.8 -1.3 3.8 0" {...sw(1.7, 0.8)} />
        <circle cx="96" cy="45.5" r="2" {...sw(1.5, 0.7)} />
        <path d="M96 47.5 l1.2 6.5 M94.3 52.5 q1.6 -1.1 3.4 0" {...sw(1.5, 0.7)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="translate" from="16 0" to="0 0"
            begin="2.3s" dur="1.5s" fill="freeze" calcMode="spline" keySplines="0.3 0 0.6 1" keyTimes="0;1" />
        )}
      </g>
      <Label x="58" y="40" at="0.9" reduce={reduce}>사무엘</Label><Label x="60" y="60" at="2.5" reduce={reduce}>온 이스라엘의 애곡</Label>
    </g>
  )
}

// 시글락 정착 (삼상 27:5-7)
function ZiklagBaseScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M70 54 v-10 h9 v10 M83 54 v-13 h10 v13 M97 54 v-9 h8 v9" {...sw(2)} />
        <path d="M72 48 h5 M85 45 h6 M99 48 h4" {...sw(1.2, 0.5)} />
      </g>
      {/* 아기스 — 허락하는 자, 보조 */}
      <g style={d(700, reduce)}>
        <circle cx="18" cy="33" r="2.6" {...sw(2)} />
        <path d="M18 35.6 v8.5 M15 47 q3 -2 6 0" {...sw(2)} />
        <path d="M21 37 l5 -1" {...sw(1.4)} />
      </g>
      {/* 다윗과 무리 — 주역, 이동해 정착 */}
      <g transform={reduce ? undefined : 'translate(20 0)'} style={d(1500, reduce)}>
        <circle cx="40" cy="40" r="2.6" {...sw(2.5)} />
        <path d="M40 42.6 v7 M37 54 l3 -4.4 l3 4.4" {...sw(2.5)} />
        <circle cx="50" cy="41.5" r="2.2" {...sw(1.9)} />
        <path d="M50 43.7 v6.5 M47.7 54 l2.3 -3.8 l2.3 3.8" {...sw(1.9)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="translate" from="20 0" to="0 0"
            begin="1.6s" dur="1.4s" fill="freeze" calcMode="spline" keySplines="0.3 0 0.6 1" keyTimes="0;1" />
        )}
      </g>
      {/* 장막 — 정착의 핵심 */}
      <g style={d(2200, reduce)}>
        <path d="M56 54 l6 -9 l6 9 M59 54 v-4 M65 54 v-4" {...sw(2.4)} />
        <path d="M58.5 51 h7" {...sw(1.3, 0.6)} />
      </g>
      <Label x="18" y="24" at="0.7" reduce={reduce}>아기스</Label><Label x="44" y="31" at="2.3" reduce={reduce}>다윗의 무리</Label><Label x="62" y="60" at="2.6" reduce={reduce}>시글락</Label>
    </g>
  )
}

// 기브온 못가의 전투 (삼하 2:12-23)
function GibeonBattleScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M42 54 q18 6 36 0 q4 -1.5 0 -3 q-18 -6 -36 0 q-4 1.5 0 3 z" {...sw(1.8)} />
      </g>
      {/* 두 편 — 보조, 대치 */}
      <g style={d(700, reduce)}>
        <circle cx="16" cy="42" r="2.2" {...sw(1.8)} />
        <path d="M16 44.2 v7.8 M13.8 54 l2.2 -2.4 l2.2 2.4" {...sw(1.8)} />
        <circle cx="26" cy="41.5" r="2.2" {...sw(1.8)} />
        <path d="M26 43.7 v8 M23.8 54 l2.2 -2.4 l2.2 2.4" {...sw(1.8)} />
        <circle cx="94" cy="41.5" r="2.2" {...sw(1.8)} />
        <path d="M94 43.7 v8 M91.8 54 l2.2 -2.4 l2.2 2.4" {...sw(1.8)} />
        <circle cx="104" cy="42" r="2.2" {...sw(1.8)} />
        <path d="M104 44.2 v7.8 M101.8 54 l2.2 -2.4 l2.2 2.4" {...sw(1.8)} />
      </g>
      {/* 아사헬 — 추격하는 주역 */}
      <g transform={reduce ? 'translate(30 0)' : undefined} style={d(1500, reduce)}>
        <circle cx="48" cy="38" r="2.6" {...sw(2.5)} />
        <path d="M48 40.6 l1 8.5 M47 49 l2 5 M52 46 l4.5 -4" {...sw(2.5)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="translate" from="0 0" to="30 0"
            begin="1.6s" dur="1.4s" fill="freeze" calcMode="spline" keySplines="0.4 0 0.6 1" keyTimes="0;1" />
        )}
      </g>
      {/* 아브넬 — 창을 뒤로 찌르는 주역 */}
      <g style={d(2300, reduce)}>
        <circle cx="88" cy="36" r="2.8" {...sw(2.5)} />
        <path d="M88 38.8 v8.7 M85 54 l3 -6.5 l3 6.5" {...sw(2.5)} />
        <path d="M85.5 41 l-9 3" {...sw(2.4)}>
          {!reduce && (
            <animateTransform attributeName="transform" type="rotate" values="0 88 40; -10 88 40; 0 88 40"
              keyTimes="0;0.4;1" begin="3.1s" dur="0.5s" />
          )}
        </path>
      </g>
      <Label x="48" y="29" at="1.7" reduce={reduce}>아사헬</Label><Label x="88" y="27" at="2.4" reduce={reduce}>아브넬</Label>
    </g>
  )
}

// 여디디야의 탄생 (삼하 12:24-25)
function SolomonBirthScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M30 54 v-14 h50 v14 M36 54 v-14 M74 54 v-14" {...sw(2)} />
        <path d="M40 44 h4 m6 0 h4 m6 0 h4" {...sw(1.2, 0.5)} />
      </g>
      {/* 다윗과 밧세바 — 보조 */}
      <g style={d(700, reduce)}>
        <circle cx="42" cy="38" r="2.6" {...sw(2)} />
        <path d="M42 40.6 v9 M39 54 l3 -4.4 l3 4.4" {...sw(2)} />
        <circle cx="52" cy="38.5" r="2.4" {...sw(1.9)} />
        <path d="M52 40.9 v9 M49.4 54 l2.6 -4.1 l2.6 4.1" {...sw(1.9)} />
        <path d="M45 42 l3 0.4" {...sw(1.3, 0.6)} />
      </g>
      {/* 나단 — 이름 선포, 주역 */}
      <g style={d(1500, reduce)}>
        <circle cx="80" cy="32" r="3" {...sw(2.5)} />
        <path d="M76 54 l2.4 -19 h5 l2.4 19 M76 54 h10" {...sw(2.5)} />
        <path d="M73 40 q4 1.5 6 5" {...sw(1.8)} />
      </g>
      {/* 아기 — 강보, 핵심(은혜의 이름) */}
      <g style={d(2200, reduce)} stroke="var(--paper-accent)">
        <path d="M60 47 q0 -3.5 4 -3.5 q4 0 4 3.5 q0 2.5 -4 2.5 q-4 0 -4 -2.5" {...sw(2)} />
        <path d="M61.5 46 q1.3 -1.2 2.5 -1.2 M64.8 45.8 q1 1 1.6 2" {...sw(1.3)} />
      </g>
      <Label x="47" y="30" at="1.5" reduce={reduce}>다윗과 밧세바</Label><Label x="80" y="23" at="2.3" reduce={reduce}>나단</Label><Label x="64" y="56" at="3" reduce={reduce}>여디디야</Label>
    </g>
  )
}

// 마하나임 도피 (삼하 15:30; 17:27-29)
function MahanaimExileScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M6 40 q20 -22 40 -6 q10 -14 30 -2 q18 -10 38 4" {...sw(2)} />
        <path d="M20 32 l3 -2.5 M56 30 l3 -2" {...sw(1.2, 0.4)} />
      </g>
      {/* 다윗 — 맨발로 걷는 주역, 머리 가림 */}
      <g transform={reduce ? undefined : 'translate(-24 0)'} style={d(700, reduce)}>
        <circle cx="46" cy="42" r="2.6" {...sw(2.5)} />
        <path d="M43.5 40 q2.6 -2.5 5.2 0" {...sw(1.6)} />
        <path d="M46 44.6 v7 M43.3 54 l2.7 -2.4 l2.7 2.4" {...sw(2.5)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="translate" from="-24 0" to="0 0"
            begin="1.6s" dur="1.6s" fill="freeze" calcMode="spline" keySplines="0.3 0 0.6 1" keyTimes="0;1" />
        )}
      </g>
      {/* 마하나임 장막 — 보조 */}
      <g style={d(1800, reduce)}>
        <path d="M84 54 l7 -10 l7 10 M87.5 54 v-4.5 M94.5 54 v-4.5" {...sw(2.2)} />
        <path d="M86.5 50.5 h9" {...sw(1.3, 0.6)} />
      </g>
      {/* 바르실래의 공궤 — 핵심 */}
      <g style={d(2500, reduce)} stroke="var(--paper-accent)">
        <circle cx="70" cy="45" r="1.8" {...sw(1.6)} />
        <path d="M68.2 45 h3.6 M70 43.2 v3.6" {...sw(1.3)} />
        <path d="M72 46 q1.5 3.5 -0.5 6.5" {...sw(1.2, 0.7)} />
      </g>
      <Label x="46" y="34" at="0.9" reduce={reduce}>다윗</Label><Label x="91" y="42" at="2" reduce={reduce}>마하나임</Label>
    </g>
  )
}

// 예루살렘으로의 귀환 (삼하 19:15-40)
function ReturnsJerusalemScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M46 54 q3 -3 0 -6 q-3 -3 0 -6 q3 -3 0 -6 M52 54 q3 -3 0 -6 q-3 -3 0 -6 q3 -3 0 -6" {...sw(1.3, 0.5)} />
      </g>
      {/* 요단을 건너는 다윗 — 주역 */}
      <g transform={reduce ? undefined : 'translate(-20 0)'} style={d(700, reduce)}>
        <circle cx="49" cy="36" r="2.8" {...sw(2.5)} />
        <path d="M49 38.8 v8.5 M46 54 l3 -6.7 l3 6.7" {...sw(2.5)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="translate" from="-20 0" to="0 0"
            begin="1.6s" dur="1.5s" fill="freeze" calcMode="spline" keySplines="0.3 0 0.6 1" keyTimes="0;1" />
        )}
      </g>
      {/* 맞이하는 자 — 보조 */}
      <g style={d(1800, reduce)}>
        <circle cx="20" cy="43" r="2.3" {...sw(1.9)} />
        <path d="M20 45.3 v8 M16.5 46 q3.5 -2.5 7 0" {...sw(1.9)} />
        <circle cx="30" cy="44" r="2.2" {...sw(1.8)} />
        <path d="M30 46.2 v7.6 M27.8 54 l2.2 -2.5 l2.2 2.5" {...sw(1.8)} />
      </g>
      {/* 무릎 꿇고 변명하는 자 — 핵심 */}
      <g style={d(2500, reduce)}>
        <circle cx="76" cy="47" r="2.2" {...sw(2)} />
        <path d="M76 49.2 l-2 4.8 M72 54 h6 M76.8 50 q3 1 4.5 3.5" {...sw(2)} />
        <path d="M74.5 51 q1.3 0.9 2.6 0.4" {...sw(1.3, 0.6)} />
      </g>
      <Label x="49" y="28" at="0.9" reduce={reduce}>다윗</Label><Label x="76" y="41" at="2.7" reduce={reduce}>시므이</Label>
    </g>
  )
}

// 기혼 샘의 기름부음 (왕상 1:32-40)
function GihonAnointingScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M10 52 q4 -4 0 -8 q-4 -4 0 -8" {...sw(1.3, 0.5)} />
      </g>
      {/* 노새와 솔로몬 — 주역 */}
      <g style={d(700, reduce)}>
        <path d="M38 54 l3 -9 h10 l3 9 M41 54 v-3 M51 54 v-3" {...sw(2.2)} />
        <path d="M51 45 q4 -1 5 -4.5" {...sw(2)} />
        <circle cx="46" cy="38" r="2.6" {...sw(2.5)} />
        <path d="M46 40.6 v4.5" {...sw(2.5)} />
      </g>
      {/* 사독 — 기름 뿔, 보조 */}
      <g style={d(1500, reduce)}>
        <circle cx="66" cy="35" r="2.8" {...sw(2.2)} />
        <path d="M62 54 l2.4 -19 h5 l2.4 19 M62 54 h10" {...sw(2.2)} />
        <path d="M70 42 q4 -3 8 -1.5 l-0.4 2.3 q-4 -1.2 -7.4 1" {...sw(2)} />
      </g>
      {/* 뿔나팔 + 함성 — 핵심 */}
      <g style={d(reduce ? 0 : 2300, reduce)} stroke="var(--paper-accent)">
        <path d="M90 46 q6 -1 9 -5" {...sw(2.2)} />
        <path d="M99 41 q1.5 -0.6 3 0" {...sw(1.4)} />
        <path d="M84 42 q1.6 -2 3.2 0 M105 40 q1.6 -2 3.2 0" {...sw(1.3)}>
          {!reduce && <animate attributeName="opacity" values="1;0.3;1" begin="2.6s" dur="1s" repeatCount="2" />}
        </path>
      </g>
      <Label x="46" y="30" at="0.9" reduce={reduce}>솔로몬</Label><Label x="66" y="26" at="1.7" reduce={reduce}>사독</Label>
    </g>
  )
}

// 다윗의 마지막 당부 (왕상 2:1-4)
function DavidChargeScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M20 54 h40 v-8 h-40 z" {...sw(2)} />
        <path d="M24 48 h4 m6 0 h4 m6 0 h4" {...sw(1.2, 0.5)} />
      </g>
      {/* 늙은 다윗 — 기대 누운 주역 */}
      <g style={d(700, reduce)}>
        <circle cx="34" cy="41" r="2.8" {...sw(2.4)} />
        <path d="M31 54 h20 M36.5 43 q10 -0.5 14 3.5" {...sw(2.4)} />
        <path d="M32 39 q2.5 1.4 5 0.3" {...sw(1.3, 0.6)} />
      </g>
      {/* 솔로몬 — 무릎 꿇은 자, 보조 */}
      <g style={d(1500, reduce)}>
        <circle cx="70" cy="46" r="2.4" {...sw(2)} />
        <path d="M70 48.4 l-1.6 5.6 M66.5 54 l2 -3.4 M73.5 51 l-2.1 -2.6" {...sw(2)} />
        <path d="M67.8 47.5 q2.2 1.2 4.4 0" {...sw(1.3, 0.6)} />
      </g>
      {/* 당부의 손짓 — 핵심 */}
      <g style={d(reduce ? 0 : 2300, reduce)} stroke="var(--paper-accent)">
        <path d="M50 41 q6 -1 12 3" {...sw(1.6)}>
          {!reduce && <animate attributeName="opacity" values="0;1;1" begin="2.3s" dur="0.6s" fill="freeze" />}
        </path>
      </g>
      <Label x="34" y="32" at="0.9" reduce={reduce}>다윗</Label><Label x="70" y="38" at="1.7" reduce={reduce}>솔로몬</Label>
    </g>
  )
}

// 두 어머니의 재판 (왕상 3:16-28)
function TwoMothersScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M90 54 h20 M100 54 V38" {...sw(2)} />
        <path d="M100 40 h3.5 M100 44 h3.5" {...sw(1.2, 0.5)} />
      </g>
      {/* 두 여인 — 다투는 자, 보조 */}
      <g style={d(700, reduce)}>
        <circle cx="20" cy="43" r="2.6" {...sw(2)} />
        <path d="M20 45.6 v8 M17 54 l3 -3 l3 3" {...sw(2)} />
        <circle cx="34" cy="42.5" r="2.6" {...sw(2)} />
        <path d="M34 45.1 v8.5 M31 54 l3 -3.2 l3 3.2" {...sw(2)} />
        <path d="M22.5 45 l9 -0.7" {...sw(1.4)} />
      </g>
      {/* 칼을 든 시위병 — 핵심(시험) */}
      <g style={d(1500, reduce)}>
        <circle cx="62" cy="38" r="2.4" {...sw(2)} />
        <path d="M62 40.4 v8.6 M59 54 l3 -5 l3 5" {...sw(2)} />
        <path d="M65 44 l7 -8" {...sw(2.4)} />
      </g>
      {/* 솔로몬 + 아기 — 지혜의 판결, 핵심 */}
      <g style={d(2300, reduce)} stroke="var(--paper-accent)">
        <path d="M100 34 v-4 M97.5 32 l-1.6 -1.6 M102.5 32 l1.6 -1.6" {...sw(1.6)} />
        <path d="M14 47 q1.5 3.5 -0.5 6.5" {...sw(1.4)} />
      </g>
      <Label x="27" y="34" at="0.9" reduce={reduce}>두 여인</Label><Label x="100" y="33" at="2.5" reduce={reduce}>솔로몬의 판결</Label>
    </g>
  )
}

// 솔로몬의 궁전 건축 (왕상 7:1-8)
function JerusalemPalaceScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M20 54 h84 M24 50 h76" {...sw(2.2)} />
      </g>
      {/* 레바논 숲 궁 — 기둥 열, 핵심 */}
      <g style={d(900, reduce)}>
        <path d="M28 50 v-16 M36 50 v-16 M44 50 v-16 M52 50 v-16" {...sw(2.4)} />
        <path d="M27 34 h26" {...sw(1.8)} />
        <path d="M29.5 37 h2 m6 0 h2 m6 0 h2" {...sw(1.2, 0.55)} />
      </g>
      {/* 심판하는 낭실 — 보조 */}
      <g style={d(1800, reduce)}>
        <path d="M62 50 v-11 h16 v11" {...sw(2)} />
        <path d="M65 42 h2.5 m5 0 h2.5" {...sw(1.2, 0.5)} />
      </g>
      {/* 바로의 딸 궁 — 보조 */}
      <g style={d(2700, reduce)}>
        <path d="M84 50 v-9 h18 v9" {...sw(1.9)} />
        <path d="M88 44 h3 m5 0 h3" {...sw(1.2, 0.5)} />
      </g>
      {/* 비계·일꾼 — 가늘게 */}
      <g style={d(3600, reduce)}>
        <path d="M14 54 l6 -18" {...sw(1.4)} />
        <circle cx="10" cy="34" r="1.9" {...sw(1.5)} />
        <path d="M10 36 l-1.4 2.8 M9 37.4 l2.8 0.9" {...sw(1.3)} />
      </g>
      <Label x="41" y="27" at="1.4" reduce={reduce} size="4.2">레바논 숲 궁</Label><Label x="70" y="60" at="2.3" reduce={reduce} size="4.2">낭실</Label>
    </g>
  )
}

// 에시온게벨의 함대 (왕상 9:26-28)
function EzionGeberFleetScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 50 q6 -3 12 0 q6 -3 12 0 q6 -3 12 0 q6 -3 12 0 q6 -3 12 0 q6 -3 12 0 q6 -3 12 0 q6 -3 12 0" {...sw(1.4)} />
        <path d="M6 54 q6 -2.5 12 0 q6 -2.5 12 0 q6 -2.5 12 0 q6 -2.5 12 0 q6 -2.5 12 0 q6 -2.5 12 0 q6 -2.5 12 0 q6 -2.5 12 0" {...sw(1.6)} />
      </g>
      {/* 배 — 주역 */}
      <g style={d(700, reduce)}>
        <path d="M40 48 l-6 6 h44 l-6 -6 z" {...sw(2.4)} />
        <path d="M62 48 V24" {...sw(2.2)} />
      </g>
      {/* 돛 — 핵심 */}
      <g transform={reduce ? 'rotate(-8 62 26)' : undefined} style={d(1500, reduce)}>
        <path d="M62 26 v20 l16 -3 q1 -12 -16 -17" {...sw(2)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="rotate" from="0 62 26" to="-8 62 26"
            begin="1.7s" dur="1s" fill="freeze" calcMode="spline" keySplines="0.3 0 0.6 1" keyTimes="0;1" />
        )}
      </g>
      {/* 선원 — 보조 */}
      <g style={d(2400, reduce)}>
        <circle cx="46" cy="43" r="2" {...sw(1.8)} />
        <path d="M46 45 v3" {...sw(1.8)} />
        <circle cx="54" cy="43" r="2" {...sw(1.8)} />
        <path d="M54 45 v3" {...sw(1.8)} />
      </g>
      {/* 오빌의 금 — 핵심 */}
      <g style={d(reduce ? 0 : 3100, reduce)} stroke="var(--paper-accent)">
        <path d="M34 50 h6 v3 h-6 z" {...sw(1.6)} />
      </g>
      <Label x="62" y="20" at="0.9" reduce={reduce}>함대</Label><Label x="37" y="60" at="3.3" reduce={reduce}>오빌의 금</Label>
    </g>
  )
}

// 스바 여왕의 방문 (왕상 10:1-9)
function JerusalemShebaScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M84 54 h22 M95 54 V34" {...sw(2)} />
        <path d="M95 36 h3.5 M95 40 h3.5" {...sw(1.2, 0.5)} />
      </g>
      {/* 솔로몬 — 왕좌, 보조 */}
      <g style={d(700, reduce)}>
        <circle cx="95" cy="28" r="3" {...sw(2.4)} />
        <path d="M95 31 v10 M90 47 q5 -3 10 0" {...sw(2.4)} />
      </g>
      {/* 스바 여왕과 시종 — 도착하는 주역 */}
      <g transform={reduce ? undefined : 'translate(-24 0)'} style={d(1500, reduce)}>
        <circle cx="28" cy="38" r="2.8" {...sw(2.5)} />
        <path d="M28 40.8 v8.5 M25 54 l3 -4.7 l3 4.7" {...sw(2.5)} />
        <circle cx="18" cy="42" r="2" {...sw(1.6, 0.75)} />
        <path d="M18 44 v6.5 M16 54 l2 -3.5 l2 3.5" {...sw(1.6, 0.75)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="translate" from="-24 0" to="0 0"
            begin="1.6s" dur="1.5s" fill="freeze" calcMode="spline" keySplines="0.3 0 0.6 1" keyTimes="0;1" />
        )}
      </g>
      {/* 놀라는 손짓 — 세부 */}
      <g style={d(2300, reduce)}>
        <path d="M32 34 q2.5 -1.5 4.5 -3.5" {...sw(1.6)} />
      </g>
      {/* 찬양의 고백 — 핵심 */}
      <g style={d(reduce ? 0 : 3000, reduce)} stroke="var(--paper-accent)">
        <path d="M50 20 q2 -2 4 0 q2 -2 4 0 M60 16 q1.8 -1.8 3.6 0" {...sw(1.4)}>
          {!reduce && <animate attributeName="opacity" values="0;1" begin="3s" dur="0.6s" fill="freeze" />}
        </path>
      </g>
      <Label x="95" y="20" at="0.9" reduce={reduce}>솔로몬</Label><Label x="24" y="30" at="1.7" reduce={reduce}>스바 여왕</Label>
    </g>
  )
}

// 솔로몬의 배교와 심판 선고 (왕상 11:1-13)
function JerusalemApostasyScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M84 54 q0 -8 6 -8 q6 0 6 8" {...sw(2.2)} />
        <path d="M86 50 q4 1.3 8 0" {...sw(1.3, 0.55)} />
      </g>
      {/* 이방 아내들 — 보조, 배경 */}
      <g opacity="0.65" style={d(700, reduce)}>
        <circle cx="20" cy="42" r="2.2" {...sw(1.8)} />
        <path d="M20 44.2 v8 M17.5 54 l2.5 -3 l2.5 3" {...sw(1.8)} />
        <circle cx="30" cy="41.5" r="2.2" {...sw(1.8)} />
        <path d="M30 43.7 v8.3 M27.5 54 l2.5 -3.1 l2.5 3.1" {...sw(1.8)} />
      </g>
      {/* 늙은 솔로몬 — 돌아서는 주역 */}
      <g transform={reduce ? 'rotate(20 58 44)' : undefined} style={d(1500, reduce)}>
        <circle cx="58" cy="37" r="2.8" {...sw(2.5)} />
        <path d="M58 39.8 v9 M55 54 l3 -5.2 l3 5.2" {...sw(2.5)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="rotate" from="0 58 44" to="20 58 44"
            begin="2.6s" dur="0.9s" fill="freeze" calcMode="spline" keySplines="0.4 0 0.6 1" keyTimes="0;1" />
        )}
      </g>
      {/* 향 연기 — 우상 숭배 */}
      <g style={d(2400, reduce)}>
        <path d="M90 44 q-2.5 -4 0 -7.5 q2.5 3.5 0 7.5" {...sw(1.3, 0.6)} />
      </g>
      {/* 찢기는 나라 — 심판 선고, 핵심 */}
      <g style={d(2900, reduce)}>
        <path d="M66 50 l5 -1.6 l1.3 3 l-5 1.6 z" {...sw(2.6)}>
          {!reduce && (
            <animateMotion path="M0 0 q7 -5 14 -2" begin="3.1s" dur="0.7s" fill="freeze"
              calcMode="spline" keySplines="0.3 0 0.7 1" keyTimes="0;1" />
          )}
        </path>
      </g>
      <Label x="90" y="34" at="0.9" reduce={reduce}>우상</Label><Label x="58" y="29" at="1.7" reduce={reduce}>솔로몬</Label>
    </g>
  )
}

const SCENES = {
  'authored-saul-mizpah-chosen': { Scene: MizpahChosenScene, desc: '백성의 요구에 응답해 제비뽑기로 첫 왕이 세워지다', caption: '미스바의 제비뽑기 — 사무엘상 10장' },
  'authored-saul-jabesh-rescue': { Scene: JabeshRescueScene, desc: '하나님의 영에 사로잡힌 사울이 새벽에 야베스를 구원하다', caption: '야베스 길르앗 구원 — 사무엘상 11장' },
  'authored-saul-gilgal-coronation': { Scene: GilgalCoronationScene, desc: '온 백성이 길갈에서 사울을 왕으로 세우고 화목제를 드리다', caption: '길갈의 대관식 — 사무엘상 11장' },
  'authored-saul-michmash-battle': { Scene: MichmashBattleScene, desc: '요나단이 병기 든 자와 단둘이 절벽을 올라 적진을 치다', caption: '믹마스 협곡의 기습 — 사무엘상 14장' },
  'authored-saul-gilgal-amalek': { Scene: GilgalAmalekScene, mood: 'dark', desc: '순종이 제사보다 낫다 — 옷자락처럼 왕국이 찢기다', caption: '찢어진 옷자락 — 사무엘상 15장' },
  'authored-samuel-bethlehem-david-anointing': { Scene: BethlehemAnointingScene, desc: '사무엘이 이새의 막내 다윗에게 기름을 붓다', caption: '베들레헴의 기름부음 — 사무엘상 16장' },
  'authored-david-gibeah-harp': { Scene: GibeahHarpScene, desc: '악신에 시달리는 사울을 다윗의 수금 소리가 위로하다', caption: '수금과 위로 — 사무엘상 16장' },
  'authored-saul-gibeah-spear': { Scene: GibeahSpearScene, mood: 'dark', desc: '수금 타는 다윗에게 시기에 사로잡힌 사울이 창을 던지다', caption: '수금과 창 — 사무엘상 18장' },
  'authored-david-goliath-gath': { Scene: GoliathScene, desc: '물매 돌 하나가 가드의 거인을 쓰러뜨리다', caption: '다윗과 골리앗 — 사무엘상 17장' },
  'authored-david-ramah-samuel': { Scene: RamahSamuelScene, desc: '창을 피해 도망친 다윗이 사무엘에게로 가고 왕의 전령들마저 예언하다', caption: '라마 나욧으로의 도피 — 사무엘상 19장' },
  'authored-david-nob-priests': { Scene: NobPriestsScene, desc: '아히멜렉이 굶주린 다윗에게 진설병과 골리앗의 칼을 내어주다', caption: '놉의 제사장 아히멜렉 — 사무엘상 21장' },
  'authored-david-gath-achish': { Scene: GathAchishScene, desc: '가드 왕 아기스 앞에서 다윗이 미친 체하여 목숨을 건지다', caption: '가드 왕 앞의 광인 행세 — 사무엘상 21장' },
  'authored-david-adullam-cave': { Scene: AdullamCaveScene, desc: '환난 당한 자와 빚진 자와 마음이 원통한 자들이 굴로 모여들다', caption: '아둘람 굴의 사람들 — 사무엘상 22장' },
  'authored-saul-nob-massacre': { Scene: NobMassacreScene, mood: 'dark', desc: '다윗을 도운 죄로 사울이 도엑을 시켜 놉의 제사장들을 진멸하다', caption: '놉 성읍의 학살 — 사무엘상 22장' },
  'authored-david-en-gedi-saul': { Scene: EnGediScene, desc: '다윗이 잠든 사울의 옷자락만 베고 목숨은 살려주다', caption: '엔게디 동굴의 자비 — 사무엘상 24장' },
  'authored-samuel-ramah-death': { Scene: RamahDeathScene, mood: 'dark', desc: '두 왕에게 기름 부은 사무엘이 죽어 온 이스라엘이 애곡하다', caption: '사무엘의 죽음 — 사무엘상 25장' },
  'authored-david-ziklag-base': { Scene: ZiklagBaseScene, desc: '아기스가 내어준 시글락이 다윗 무리의 새 거점이 되다', caption: '시글락 정착 — 사무엘상 27장' },
  'authored-saul-endor-medium': { Scene: EndorMediumScene, mood: 'dark', desc: '버림받은 왕이 신접한 여인에게 죽은 사무엘을 불러내다', caption: '엔돌의 밤 — 사무엘상 28장' },
  'authored-saul-gilboa-death': { Scene: GilboaDeathScene, mood: 'dark', desc: '사울이 길보아 산에서 아들들과 함께 최후를 맞다', caption: '길보아 산의 최후 — 사무엘상 31장' },
  'authored-david-hebron-king-judah': { Scene: HebronKingScene, desc: '유다 지파가 헤브론에서 다윗을 왕으로 세우다', caption: '헤브론의 유다 왕 — 사무엘하 2장' },
  'authored-david-gibeon-battle': { Scene: GibeonBattleScene, mood: 'dark', desc: '기브온 못가의 싸움에서 아사헬이 아브넬의 창에 죽다', caption: '기브온 못가의 전투 — 사무엘하 2장' },
  'authored-david-jerusalem-conquest': { Scene: JerusalemConquestScene, desc: '다윗이 물 긷는 통로로 여부스 요새를 빼앗아 수도로 삼다', caption: '다윗 성 정복 — 사무엘하 5장' },
  'authored-david-ark-jerusalem': { Scene: ArkJerusalemScene, desc: '다윗이 춤추며 언약궤를 예루살렘으로 모셔 오다', caption: '언약궤의 입성 — 사무엘하 6장' },
  'authored-david-nathan-covenant': { Scene: NathanCovenantScene, desc: '네 집과 네 나라가 영원히 보전되리라 — 언약의 밤', caption: '다윗 언약의 밤 — 사무엘하 7장' },
  'authored-solomon-jerusalem-birth': { Scene: SolomonBirthScene, desc: '참회 뒤에 태어난 아들에게 여호와께서 여디디야라는 이름을 주시다', caption: '여디디야의 탄생 — 사무엘하 12장' },
  'authored-david-mahanaim-exile': { Scene: MahanaimExileScene, desc: '압살롬을 피해 도망친 다윗이 마하나임에서 바르실래의 공궤를 받다', caption: '마하나임 도피 — 사무엘하 15-17장' },
  'authored-david-returns-jerusalem': { Scene: ReturnsJerusalemScene, desc: '압살롬의 죽음을 통곡한 다윗이 요단을 건너 예루살렘으로 돌아오다', caption: '예루살렘으로의 귀환 — 사무엘하 19장' },
  'authored-solomon-gihon-anointing': { Scene: GihonAnointingScene, desc: '다윗의 명으로 사독과 나단이 기혼 샘에서 솔로몬에게 기름을 붓다', caption: '기혼 샘의 기름부음 — 열왕기상 1장' },
  'authored-solomon-jerusalem-david-charge': { Scene: DavidChargeScene, desc: '죽음을 앞둔 다윗이 솔로몬에게 힘써 대장부가 되라 당부하다', caption: '다윗의 마지막 당부 — 열왕기상 2장' },
  'authored-solomon-gibeon-dream': { Scene: GibeonDreamScene, desc: '일천번제 후 꿈에 나타나신 하나님께 지혜를 구하다', caption: '기브온의 꿈 — 열왕기상 3장' },
  'authored-solomon-jerusalem-two-mothers': { Scene: TwoMothersScene, desc: '아기를 두고 다투는 두 여인 앞에서 솔로몬의 지혜가 드러나다', caption: '두 어머니의 재판 — 열왕기상 3장' },
  'authored-solomon-jerusalem-temple-build': { Scene: TempleBuildScene, desc: '모리아산에 하나님의 이름을 둘 성전이 세워지다', caption: '성전 건축 — 열왕기상 6장' },
  'authored-solomon-jerusalem-palace': { Scene: JerusalemPalaceScene, desc: '레바논 숲 궁과 심판하는 낭실이 십삼 년에 걸쳐 세워지다', caption: '솔로몬의 궁전 건축 — 열왕기상 7장' },
  'authored-solomon-jerusalem-temple-dedication': { Scene: TempleDedicationScene, desc: '봉헌 기도에 불이 내려오고 영광이 성전에 가득하다', caption: '성전 봉헌의 불 — 열왕기상 8장' },
  'authored-solomon-ezion-geber-fleet': { Scene: EzionGeberFleetScene, desc: '에시온게벨에서 지은 함대가 오빌의 금을 실어 오다', caption: '에시온게벨의 함대 — 열왕기상 9장' },
  'authored-solomon-jerusalem-sheba': { Scene: JerusalemShebaScene, desc: '스바 여왕이 솔로몬의 지혜를 보고 여호와를 송축하다', caption: '스바 여왕의 방문 — 열왕기상 10장' },
  'authored-solomon-jerusalem-apostasy': { Scene: JerusalemApostasyScene, mood: 'dark', desc: '이방 신에게 마음을 빼앗긴 솔로몬에게 나라가 찢기리라는 선고가 내리다', caption: '솔로몬의 배교와 심판 선고 — 열왕기상 11장' },
}

export default SCENES
