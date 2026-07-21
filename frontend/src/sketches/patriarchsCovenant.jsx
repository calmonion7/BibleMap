// 언약의 4세대 — 19개 정차지 장면 (task#228, #227 표준)
import { sw, d, Label } from './lib'

// 우르의 부르심 (창 12:1-3)
function CallUrScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        {/* 우르 지구라트 — 원경 */}
        <path d="M76 54 h34 M80 54 v-7 h26 v7 M85 47 v-6 h16 v6 M89 41 v-5 h8 v5" {...sw(1.4, 0.55)} />
        <path d="M92 36 v-3 h2 v3" {...sw(1.2, 0.45)} />
      </g>
      {/* 별 — 부르심의 밤 */}
      <g style={d(900, reduce)}>
        <path d="M20 12 v2.6 m-1.3 -1.3 h2.6 M44 8 v2.6 m-1.3 -1.3 h2.6 M60 16 v2 m-1 -1 h2" {...sw(1.3, 0.7)} />
      </g>
      {/* 아브람 — 주역: 지팡이 짚고 서쪽으로 */}
      <g transform={reduce ? 'translate(-12 0)' : undefined} style={d(1700, reduce)}>
        <circle cx="46" cy="36.5" r="2.9" {...sw(2.5)} />
        <path d="M46 39.4 v7.6 M43 54 l3 -6.5 M50 53.5 l-3 -6" {...sw(2.5)} />
        <path d="M43.5 41 l-4 10 M48.5 40.5 l5 -2.5 q2.5 0 3.5 2" {...sw(2)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="translate" from="0 0" to="-12 0"
            begin="2.5s" dur="2.2s" fill="freeze" calcMode="spline" keySplines="0.3 0 0.7 1" keyTimes="0;1" />
        )}
      </g>
      <Label x="93" y="31" at="1" reduce={reduce}>갈대아 우르</Label>
      <Label x="36" y="27" at="2.3" reduce={reduce}>아브람</Label>
    </g>
  )
}

// 세겜의 약속 (창 12:6-7)
function ShechemPromiseScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M10 43 q12 -7 24 -2" {...sw(1.1, 0.4)} />
      </g>
      {/* 모레 상수리나무 — 핵심 */}
      <g style={d(700, reduce)}>
        <path d="M78 54 q-1.5 -12 -2.5 -20" {...sw(2.6)} />
        <path d="M75 34 q-13 -1 -15 -11 q9 -4 15 2 q0 -9 8 -11 q6 4 4 11 q10 -3 13 5 q-4 9 -15 7 q-4 2 -10 -3" {...sw(2)} />
        <path d="M73 44 q-4 -1 -6 -4 M79 46 q4 -2 5.5 -5" {...sw(1.3, 0.5)} />
      </g>
      {/* 제단 */}
      <g style={d(1600, reduce)}>
        <path d="M42 54 v-6 h13 v6 M40 48 h17" {...sw(2.2)} />
        <path d="M44 51.2 h3 m4 0 h3" {...sw(1.2, 0.55)} />
      </g>
      {/* 아브람 — 무릎 */}
      <g style={d(2300, reduce)}>
        <circle cx="26" cy="41" r="2.8" {...sw(2.5)} />
        <path d="M26 43.8 l-1.5 5.2 M19.5 54 h10 M24.8 49 q-3.5 1.8 -5 5 M25 46 q4 0.5 6.5 2.5" {...sw(2.5)} />
      </g>
      <g style={d(reduce ? 0 : 3200, reduce)} stroke="var(--paper-accent)">
        <path d="M48 40 v-3.5 M42 42 l-2.4 -2.4 M54 42 l2.4 -2.4" {...sw(1.4)} />
      </g>
      <Label x="26" y="32" at="2.7" reduce={reduce}>아브람</Label>
      <Label x="79" y="10" at="1.3" reduce={reduce}>세겜 상수리나무</Label>
    </g>
  )
}

// 횃불 언약 (창 15:9-21)
function CovenantCeremonyScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M18 10 v2.6 m-1.3 -1.3 h2.6 M92 8 v2.6 m-1.3 -1.3 h2.6 M104 18 v2 m-1 -1 h2 M32 16 v2 m-1 -1 h2" {...sw(1.3, 0.7)} />
      </g>
      {/* 쪼갠 제물 — 두 줄로 마주 놓임 */}
      <g style={d(900, reduce)}>
        <path d="M30 46 q3 -3 7 -2 q2 2 0 4 q-4 1.5 -7 -2 M50 45 q3 -3 7 -2 q2 2 0 4 q-4 1.5 -7 -2 M70 46 q3 -3 7 -2 q2 2 0 4 q-4 1.5 -7 -2" {...sw(1.8)} />
        <path d="M30 34 q3 3 7 2 q2 -2 0 -4 q-4 -1.5 -7 2 M50 35 q3 3 7 2 q2 -2 0 -4 q-4 -1.5 -7 2 M70 34 q3 3 7 2 q2 -2 0 -4 q-4 -1.5 -7 2" {...sw(1.8)} />
      </g>
      {/* 횃불 — 핵심: 제물 사이 통과 */}
      <g style={d(2000, reduce)}>
        <g transform={reduce ? 'translate(66 0)' : undefined}>
          <path d="M22 40 h7" {...sw(2.4)} />
          <path d="M30 40 q-1.5 -3.5 1 -6 q2.5 2 1.5 6 q-1 2 -2.5 0" {...sw(2.8)} />
          {!reduce && (
            <animateTransform attributeName="transform" type="translate" from="0 0" to="66 0"
              begin="2.4s" dur="1.8s" fill="freeze" calcMode="spline" keySplines="0.35 0 0.65 1" keyTimes="0;1" />
          )}
        </g>
      </g>
      <Label x="60" y="58" at="1.3" reduce={reduce}>쪼갠 제물 사이로</Label>
      <Label x="30" y="26" at="2.6" reduce={reduce}>타는 횃불</Label>
    </g>
  )
}

// 소돔 중보 (창 18:22-33)
function SodomIntercessionScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        {/* 소돔 원경 — 골짜기 아래 */}
        <path d="M88 54 v-5 h4 v5 m3 0 v-7 h4 v7 m3 0 v-4 h4 v4" {...sw(1.3, 0.5)} />
        <path d="M84 54 q10 -3 26 -2" {...sw(1.1, 0.4)} />
      </g>
      {/* 마므레 상수리 — 보조 */}
      <g style={d(800, reduce)}>
        <path d="M16 54 q-1 -9 -1.5 -14 M14 40 q-8 -1 -9 -7 q6 -2 9 2 q1 -6 6 -6 q3 3 2 7 q6 -1 7 4 q-3 6 -10 4 q-2 1 -4.5 -4" {...sw(1.6, 0.7)} />
      </g>
      {/* 아브라함 — 주역: 손을 들어 간구 */}
      <g style={d(1600, reduce)}>
        <circle cx="42" cy="35" r="3" {...sw(2.5)} />
        <path d="M42 38 v9 M39 54 l3 -7 l3 7" {...sw(2.5)} />
        <path d="M42 40.5 q-3.5 1.5 -4.5 5.5 M42 40 q4.5 -3 6 -7.5" {...sw(2.3)} />
      </g>
      {/* 주님 — 마주 선 이 */}
      <g style={d(2400, reduce)}>
        <circle cx="64" cy="32" r="3" {...sw(2.2)} />
        <path d="M59.5 54 l2.3 -19 h4.4 l2.3 19 M59.5 54 h9" {...sw(2.2)} />
        <path d="M62.5 40 q0.4 7 0 12 M65.5 40 q0.3 7 0 12" {...sw(1.2, 0.5)} />
      </g>
      <Label x="42" y="25" at="2.1" reduce={reduce}>아브라함</Label>
      <Label x="98" y="42" at="1" reduce={reduce}>소돔</Label>
    </g>
  )
}

// 이삭 결박 — 여호와 이레 (창 22:9-14)
function IsaacBindingScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M6 54 q30 -16 54 -18 q30 -2 54 12" {...sw(1.4, 0.5)} />
      </g>
      {/* 제단 + 장작 + 이삭(누움) */}
      <g style={d(800, reduce)}>
        <path d="M48 44 v-6 h20 v6 M46 44 h24" {...sw(2.2)} />
        <path d="M50 40.5 l6 -1.5 m2 1 l6 -1.5" {...sw(1.4)} />
        <circle cx="53" cy="35.5" r="2" {...sw(1.8)} />
        <path d="M55 36 q6 0.8 11 0.4" {...sw(1.8)} />
      </g>
      {/* 아브라함 — 주역: 든 손이 멈춤 */}
      <g style={d(1600, reduce)}>
        <circle cx="32" cy="28" r="2.9" {...sw(2.5)} />
        <path d="M32 30.9 v9.6 M29 44 h6 M29.5 44 l-1.5 10 M35 44 l1.5 10" {...sw(2.5)} />
        <path d="M33.5 32.5 q4.5 -3.5 5 -8" {...sw(2.3)} />
        <path d="M38.5 24.5 l3 -2.5" {...sw(2)} />
      </g>
      {/* 천사의 빛 + 숫양 — 핵심 반전 */}
      <g style={d(2600, reduce)} stroke="var(--paper-accent)">
        <path d="M40 12 v-4 M33 14 l-2.6 -2.6 M47 14 l2.6 -2.6" {...sw(1.8)} />
      </g>
      <g style={d(3200, reduce)}>
        <path d="M90 50.5 q0 -4.5 5.5 -4.5 q5.5 0 5.5 4.5 q0 3.5 -5.5 3.5 q-5.5 0 -5.5 -3.5" {...sw(2.2)} />
        <circle cx="102.5" cy="47" r="2.2" {...sw(2.2)} />
        <path d="M104 45 q3 -2.5 1.5 -5 M101 45 q-3 -2.5 -1.5 -5" {...sw(1.6)} />
        <path d="M86 48 q-3 -2 -3.5 -5 M85 51 q-3 0 -5 -1.5" {...sw(1.3, 0.6)} />
      </g>
      <Label x="30" y="18" at="2.1" reduce={reduce}>아브라함</Label>
      <Label x="60" y="30" at="1.3" reduce={reduce}>이삭</Label>
      <Label x="96" y="61" at="3.7" reduce={reduce}>예비된 숫양</Label>
    </g>
  )
}

// 막벨라 굴 (창 23)
function SarahBurialScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        {/* 막벨라 동굴 */}
        <path d="M64 54 q2 -22 26 -22 q22 0 24 22" {...sw(2.4)} />
        <path d="M74 54 q1 -12 16 -12 q14 0 15 12" {...sw(1.6, 0.6)} />
        <path d="M70 40 l4 -2.5 M104 38 l-4 -2.5" {...sw(1.2, 0.4)} />
      </g>
      {/* 나무 — 밭의 나무들 */}
      <g style={d(1000, reduce)}>
        <path d="M18 54 v-9 M18 45 q-5 -1 -6 -6 q6 -1 6 6 q0 -7 6 -6 q-1 5 -6 6" {...sw(1.5, 0.65)} />
      </g>
      {/* 아브라함 — 주역: 고개 숙임 */}
      <g style={d(1800, reduce)}>
        <circle cx="42" cy="37.5" r="2.9" {...sw(2.5)} />
        <path d="M41 40.2 q-1 6 -1.5 13.8 M37 54 l2.8 -5.5 M44.5 54 l-2.5 -5.5" {...sw(2.5)} />
        <path d="M41 42 q-3.5 1.5 -4.5 5" {...sw(2.2)} />
        <path d="M39.8 44.5 q1.6 1 3.2 0.3" {...sw(1.3, 0.55)} />
      </g>
      <Label x="42" y="28" at="2.3" reduce={reduce}>아브라함</Label>
      <Label x="89" y="28" at="1.1" reduce={reduce}>막벨라 굴</Label>
    </g>
  )
}

// 이삭의 출생 (창 21:1-3)
function IsaacBirthScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M84 44 q13 -8 26 -2" {...sw(1.1, 0.4)} />
      </g>
      {/* 장막 */}
      <g style={d(800, reduce)}>
        <path d="M62 54 l13 -18 l13 18 M70 54 l5 -8 l5 8" {...sw(2)} />
        <path d="M66 47 l4 -5.5 M84 47 l-4 -5.5" {...sw(1.2, 0.5)} />
      </g>
      {/* 사라 — 주역: 아기 안음 */}
      <g style={d(1600, reduce)}>
        <circle cx="34" cy="35" r="3" {...sw(2.5)} />
        <path d="M29.5 54 l2.2 -16 h4.6 l2.2 16 M29.5 54 h9" {...sw(2.5)} />
        <path d="M32 41 q2 3 4.5 0.5" {...sw(2.2)} />
        <circle cx="36.5" cy="42.5" r="1.7" {...sw(2.2)} />
        <path d="M32.5 44.5 q0.4 5 0 9.5" {...sw(1.2, 0.5)} />
      </g>
      {/* 웃음의 해 */}
      <g style={d(reduce ? 0 : 2800, reduce)} stroke="var(--paper-accent)">
        <circle cx="18" cy="16" r="4.5" {...sw(1.8)} />
        <path d="M18 8.5 v-2.5 M11 18 h-2.5 M12.8 10.8 l-1.8 -1.8 M23.2 10.8 l1.8 -1.8" {...sw(1.3)} />
      </g>
      <Label x="34" y="26" at="2.1" reduce={reduce}>사라와 이삭</Label>
      <Label x="75" y="30" at="1.2" reduce={reduce}>브엘세바 장막</Label>
    </g>
  )
}

// 리브가와의 결혼 (창 24)
function RebekahMarriageScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
      </g>
      {/* 우물 */}
      <g style={d(800, reduce)}>
        <path d="M48 54 v-8 h18 v8 M46 46 h22" {...sw(2.2)} />
        <path d="M50 43 q7 -3 14 0" {...sw(1.3, 0.55)} />
        <path d="M52 51 h3 m5 0 h3" {...sw(1.2, 0.5)} />
      </g>
      {/* 리브가 — 주역: 물동이 인 여인 */}
      <g style={d(1600, reduce)}>
        <circle cx="32" cy="35" r="2.9" {...sw(2.5)} />
        <path d="M28 54 l2 -16 h4 l2 16 M28 54 h8" {...sw(2.5)} />
        <path d="M34 33 q0 -4 -2 -5.5 q4 -1 5 2 q0.5 2.5 -3 3.5" {...sw(2.2)} />
        <path d="M30.5 40 q0.4 6 0 12" {...sw(1.2, 0.5)} />
      </g>
      {/* 낙타 — 보조 */}
      <g style={d(2400, reduce)}>
        <path d="M84 54 l1 -8 M96 54 l-1 -8 M84 46 q6 -6 12 0" {...sw(1.9)} />
        <path d="M96.5 46.5 q4 -1.5 4.5 -6 q2 -0.5 2.5 1.5" {...sw(1.9)} />
        <circle cx="104.5" cy="40" r="1.7" {...sw(1.9)} />
        <path d="M88 45 q2 -2.5 4 0" {...sw(1.3, 0.55)} />
      </g>
      <Label x="32" y="25" at="2.1" reduce={reduce}>리브가</Label>
      <Label x="57" y="36" at="1.2" reduce={reduce}>우물</Label>
    </g>
  )
}

// 에서와 야곱의 출생 (창 25:21-26)
function TwinsBirthScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M14 54 l12 -16 l12 16 M22 54 l4 -7 l4 7" {...sw(1.8, 0.8)} />
      </g>
      {/* 두 아기 — 핵심: 발꿈치 잡음 */}
      <g style={d(1200, reduce)}>
        <circle cx="62" cy="42" r="3" {...sw(2.5)} />
        <path d="M62 45 q-2 4 -1 7 M60 49 q-2.5 1 -3.5 3" {...sw(2.5)} />
        <path d="M59.8 40 q1 1.6 2.6 1.8 M63 45.5 q2.5 2 5.5 2" {...sw(1.4)} />
        <circle cx="76" cy="44" r="2.8" {...sw(2.4)} />
        <path d="M76 46.8 q1.5 3.5 0.5 6 M74 48 q-3 0.5 -5.5 -0.5" {...sw(2.4)} />
      </g>
      {/* 붉은 털 표시(에서) — 질감 */}
      <g style={d(2200, reduce)}>
        <path d="M60 38.5 q1 -1.4 2.4 -1.2 m-4 2.6 q0.8 -1.2 2 -1.2" {...sw(1.2, 0.6)} />
      </g>
      <g style={d(reduce ? 0 : 3000, reduce)} stroke="var(--paper-accent)">
        <path d="M69 30 v-3 m-1.5 1.5 h3" {...sw(1.4)} />
      </g>
      <Label x="60" y="32" at="1.7" reduce={reduce}>에서</Label>
      <Label x="80" y="36" at="1.7" reduce={reduce}>야곱</Label>
      <Label x="70" y="60" at="2.6" reduce={reduce} size="4.2">발꿈치를 잡고 나오다</Label>
    </g>
  )
}

// 야곱 축복 (창 27)
function BlessingJacobScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M18 54 l11 -15 l11 15" {...sw(1.6, 0.7)} />
      </g>
      {/* 침상의 이삭 — 보조 */}
      <g style={d(800, reduce)}>
        <path d="M56 50 h44 M60 54 v-4 M96 54 v-4" {...sw(2)} />
        <circle cx="92" cy="46.5" r="2.8" {...sw(2.2)} />
        <path d="M89 47.5 q-9 2 -19 1.5" {...sw(2.2)} />
        <path d="M75 49.5 q6 1 11 0.5" {...sw(1.2, 0.5)} />
      </g>
      {/* 야곱 — 주역: 무릎 꿇고 손 얹힘 받음 */}
      <g style={d(1800, reduce)}>
        <circle cx="42" cy="40" r="2.8" {...sw(2.5)} />
        <path d="M42 42.8 l-1.5 5.2 M35.5 54 h10 M40.8 48 q-3.5 1.8 -5 5" {...sw(2.5)} />
      </g>
      {/* 축복의 손 — 핵심 SMIL */}
      <g transform={reduce ? undefined : 'translate(0 -6)'} style={d(2600, reduce)}>
        <path d="M86 43 q-6 -4 -13 -4 q-3 0 -4.5 1.5" {...sw(2.6)} />
        <path d="M68 41 l-1.5 1.8 m3 -1.4 l-1.4 2" {...sw(1.6)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="translate" from="0 -6" to="0 0"
            begin="2.8s" dur="0.7s" fill="freeze" calcMode="spline" keySplines="0.3 0 0.5 1" keyTimes="0;1" />
        )}
      </g>
      <Label x="42" y="31" at="2.3" reduce={reduce}>야곱</Label>
      <Label x="94" y="38" at="1.2" reduce={reduce}>이삭</Label>
    </g>
  )
}

// 벧엘 사닥다리 꿈 (창 28:12-19)
function BethelDreamScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M14 12 v2.6 m-1.3 -1.3 h2.6 M100 8 v2.6 m-1.3 -1.3 h2.6" {...sw(1.3, 0.7)} />
      </g>
      {/* 잠든 야곱 + 돌베개 */}
      <g style={d(800, reduce)}>
        <circle cx="30" cy="48.5" r="2.8" {...sw(2.5)} />
        <path d="M33 49.5 q9 1.5 17 1 M52 51 l6 0.8" {...sw(2.5)} />
        <path d="M24 51 q0 -3.5 3.5 -3.5 q2 0 2.8 1.6" {...sw(1.8)} />
        <path d="M38 51.5 q5 1 9 0.6" {...sw(1.2, 0.5)} />
      </g>
      {/* 사닥다리 — 핵심: 하늘로 */}
      <g style={d(1800, reduce)}>
        <path d="M60 54 L92 10 M70 54 L102 10" {...sw(2.6)} />
        <path d="M66.5 46 l9.5 0 M72 38 l9.5 0 M77.5 30 l9.5 0 M83 22 l9.5 0 M88.5 14 l9.5 0" {...sw(1.6)} />
      </g>
      {/* 오르내리는 천사 — 점 두 개 이동 */}
      {!reduce && (
        <g style={d(2800, false)}>
          <circle cx="76" cy="42" r="1.8" {...sw(1.8)}>
            <animateMotion path="M0 0 L16 -22" begin="3s" dur="1.8s" fill="freeze" />
          </circle>
          <circle cx="94" cy="16" r="1.8" {...sw(1.8)}>
            <animateMotion path="M0 0 L-12 17" begin="3.2s" dur="1.8s" fill="freeze" />
          </circle>
        </g>
      )}
      {reduce && <><circle cx="88" cy="24" r="1.8" {...sw(1.8)} /><circle cx="84" cy="35" r="1.8" {...sw(1.8)} /></>}
      <Label x="30" y="40" at="1.3" reduce={reduce}>야곱</Label>
      <Label x="88" y="7" at="2.4" reduce={reduce}>하늘 사닥다리</Label>
    </g>
  )
}

// 하란 20년 (창 29-31)
function HaranSojournScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M88 44 q11 -7 22 -2" {...sw(1.1, 0.4)} />
      </g>
      {/* 우물 + 돌 */}
      <g style={d(800, reduce)}>
        <path d="M18 54 v-7 h15 v7 M16 47 h19" {...sw(2)} />
        <path d="M20 44 q5.5 -2.5 11 0" {...sw(1.3, 0.5)} />
      </g>
      {/* 양 떼 — 번성 */}
      <g style={d(1600, reduce)}>
        <path d="M50 51.5 q0 -4 5 -4 q5 0 5 4 q0 2.5 -5 2.5 q-5 0 -5 -2.5" {...sw(1.8)} />
        <circle cx="61.5" cy="48.5" r="1.9" {...sw(1.8)} />
        <path d="M68 52 q0 -3.5 4.5 -3.5 q4.5 0 4.5 3.5 q0 2 -4.5 2 q-4.5 0 -4.5 -2" {...sw(1.6, 0.85)} />
        <circle cx="78.5" cy="49.5" r="1.7" {...sw(1.6, 0.85)} />
        <path d="M84 52.5 q0 -3 4 -3 q4 0 4 3 q0 1.5 -4 1.5 q-4 0 -4 -1.5" {...sw(1.4, 0.7)} />
        <path d="M52 54 v-0.8 M56 54 v-0.8 M70 54 v-0.7 M86 54 v-0.6" {...sw(1.2)} />
      </g>
      {/* 야곱 — 주역: 지팡이 목자 */}
      <g style={d(2400, reduce)}>
        <circle cx="42" cy="35" r="2.9" {...sw(2.5)} />
        <path d="M42 37.9 v9.1 M39 54 l3 -7 l3 7" {...sw(2.5)} />
        <path d="M44.5 40 l4 8 M46 39 q0 -3 2.5 -3.5" {...sw(2)} />
      </g>
      {/* 열두 표시 — 별 12? 간략히 12개의 점 */}
      <g style={d(reduce ? 0 : 3400, reduce)} stroke="var(--paper-accent)">
        <path d="M20 16 h1.6 m4 0 h1.6 m4 0 h1.6 m4 0 h1.6 m4 0 h1.6 m4 0 h1.6 m4 0 h1.6 m4 0 h1.6 m4 0 h1.6 m4 0 h1.6 m4 0 h1.6 m4 0 h1.6" {...sw(2)} />
      </g>
      <Label x="42" y="26" at="2.9" reduce={reduce}>야곱</Label>
      <Label x="66" y="40" at="2.1" reduce={reduce}>번성한 양 떼</Label>
      <Label x="60" y="12" at="3.8" reduce={reduce} size="4.2">열두 아들</Label>
    </g>
  )
}

// 브니엘 씨름 (창 32:24-30)
function PenielWrestlingScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M8 50 q8 -2 16 0 q8 -2 16 0" {...sw(1.3, 0.55)} />
        <path d="M12 52.5 q6 -1.5 12 0" {...sw(1.1, 0.4)} />
      </g>
      {/* 동트는 해 — 원경 */}
      <g transform={reduce ? 'translate(0 -2)' : undefined} style={d(900, reduce)}>
        <path d="M96 54 a7 7 0 0 1 14 0" {...sw(1.8, 0.8)} />
        <path d="M103 44 v-2.5" {...sw(1.2, 0.6)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="translate" from="0 2" to="0 -2"
            begin="2s" dur="2.6s" fill="freeze" />
        )}
      </g>
      {/* 씨름하는 두 사람 — 핵심: 맞잡고 기울어짐 */}
      <g style={d(1700, reduce)}>
        <circle cx="52" cy="30" r="3" {...sw(2.6)} />
        <path d="M53.5 32.8 q3 4 3.5 9.2 M57 42 l-2 12 M57 42 l6 11" {...sw(2.6)} />
        <path d="M54.5 33.5 l9 4.5" {...sw(2.4)} />
        <circle cx="68" cy="32" r="3" {...sw(2.4)} />
        <path d="M66.5 34.8 q-3 4 -3.5 9.2 M63 44 l0 10 M63 44 l-6.5 9" {...sw(2.4)} />
        <path d="M65.5 35.5 l-9 3.5" {...sw(2.2)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="rotate"
            values="0 60 44; 3 60 44; -3 60 44; 2 60 44; 0 60 44" keyTimes="0;0.25;0.5;0.75;1"
            begin="2.4s" dur="1.8s" repeatCount="2" />
        )}
      </g>
      <Label x="46" y="20" at="2.2" reduce={reduce}>야곱</Label>
      <Label x="76" y="22" at="2.2" reduce={reduce}>하나님의 사람</Label>
      <Label x="60" y="61" at="4" reduce={reduce} size="4.2">이스라엘이라 불리리라</Label>
    </g>
  )
}

// 벧엘 귀환 (창 35:1-7)
function BethelReturnScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M10 43 q12 -7 24 -2" {...sw(1.1, 0.4)} />
      </g>
      {/* 제단 — 핵심: 돌을 쌓아 올림(단계 draw) */}
      <g style={d(900, reduce)}>
        <path d="M52 54 h18" {...sw(2.2)} />
        <path d="M54 54 v-4 h14 v4" {...sw(2.2)} />
      </g>
      <g style={d(1600, reduce)}>
        <path d="M56 50 v-4 h10 v4" {...sw(2.2)} />
      </g>
      <g style={d(2300, reduce)}>
        <path d="M58 46 v-3.5 h6 v3.5" {...sw(2.2)} />
        <path d="M60 40 q-1.6 -2.8 0 -5 q1.6 2.2 0 5" {...sw(2.4)} />
      </g>
      {/* 야곱 가족 — 보조 */}
      <g style={d(2900, reduce)}>
        <circle cx="30" cy="38" r="2.9" {...sw(2.5)} />
        <path d="M30 40.9 v6.6 M27 54 l3 -6.5 l3 6.5 M32.5 43 q4 -1 6.5 1" {...sw(2.5)} />
        <circle cx="20" cy="42" r="2.2" {...sw(1.8)} />
        <path d="M20 44.2 v4.3 M18 54 l2 -5.5 l2 5.5" {...sw(1.8)} />
      </g>
      <g style={d(reduce ? 0 : 3600, reduce)} stroke="var(--paper-accent)">
        <path d="M61 30 v-3.5 M55 32 l-2.4 -2.4 M67 32 l2.4 -2.4" {...sw(1.4)} />
      </g>
      <Label x="30" y="29" at="3.3" reduce={reduce}>야곱</Label>
      <Label x="61" y="60" at="2" reduce={reduce}>벧엘의 제단</Label>
    </g>
  )
}

// 도단 구덩이 (창 37:17-28)
function DothanPitScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M84 44 q13 -8 26 -2" {...sw(1.1, 0.4)} />
      </g>
      {/* 구덩이 단면 — 핵심 */}
      <g style={d(800, reduce)}>
        <path d="M40 54 q-2 0 -2 -3 v-10 q0 -4 4 -4 h16 q4 0 4 4 v10 q0 3 -2 3" {...sw(2.4)} />
        <path d="M42 40 l-2 -1.5 M60 40 l2 -1.5" {...sw(1.3, 0.5)} />
      </g>
      {/* 구덩이 속 요셉 — 주역 */}
      <g style={d(1600, reduce)}>
        <circle cx="50" cy="45" r="2.6" {...sw(2.5)} />
        <path d="M50 47.6 v4.4 M48 52 h4" {...sw(2.5)} />
        <path d="M50 48.5 q-3 -2.5 -3.5 -5.5 M50 48.5 q3 -2.5 3.5 -5.5" {...sw(2.2)} />
      </g>
      {/* 형들 — 위에서 내려봄 */}
      <g style={d(2300, reduce)}>
        <circle cx="30" cy="32" r="2.4" {...sw(1.9)} />
        <path d="M30 34.4 v6.1 M28 43 l2 -3 l2 3" {...sw(1.9)} />
        <circle cx="72" cy="31" r="2.4" {...sw(1.9)} />
        <path d="M72 33.4 v6.1 M70 42 l2 -3 l2 3" {...sw(1.9)} />
        <path d="M31.8 36 q4 2 7 4.5 M70.2 35 q-4 2.5 -6.5 5" {...sw(1.5)} />
      </g>
      {/* 은전 — 팔림 */}
      <g style={d(reduce ? 0 : 3200, reduce)}>
        <circle cx="88" cy="35" r="2" {...sw(1.6)} />
        <circle cx="93" cy="37" r="2" {...sw(1.6)} />
        <path d="M87 35 h2 m3 2 h2" {...sw(1.1)} />
      </g>
      <Label x="50" y="61" at="2" reduce={reduce}>요셉</Label>
      <Label x="30" y="23" at="2.7" reduce={reduce}>형들</Label>
      <Label x="91" y="28" at="3.6" reduce={reduce}>은 이십</Label>
    </g>
  )
}

// 애굽 총리 (창 41:39-43)
function PrimeMinisterScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        {/* 애굽 기둥 두 개 — 원경 */}
        <path d="M14 54 v-28 M26 54 v-28 M11 26 h18 M12.5 23 h15" {...sw(1.4, 0.55)} />
        <path d="M16 32 h8 m-8 6 h8" {...sw(1.1, 0.4)} />
      </g>
      {/* 곡식 창고 — 보조: 피라미드형 곳간 + 이삭 */}
      <g style={d(900, reduce)}>
        <path d="M86 54 l11 -14 l11 14" {...sw(1.8)} />
        <path d="M92 54 l5 -7 l5 7" {...sw(1.3, 0.55)} />
        <path d="M78 54 v-5 M78 49 q-2.5 -1 -3 -4 q3.5 0 3 4 q0.5 -4 3.5 -4 q-0.5 3 -3.5 4" {...sw(1.3, 0.6)} />
      </g>
      {/* 요셉 — 주역: 서 있는 총리 */}
      <g style={d(1700, reduce)}>
        <circle cx="52" cy="32" r="3" {...sw(2.6)} />
        <path d="M52 35 v11.5 M48.5 54 l3.5 -7.5 l3.5 7.5" {...sw(2.6)} />
        <path d="M52 37.5 q-4 1 -5.5 4.5 M52 37.5 q4 1 5.5 4.5" {...sw(2.3)} />
        <path d="M50 41.5 q2 1.2 4 0" {...sw(1.3, 0.6)} />
      </g>
      {/* 목걸이·인장 — 핵심: 내려와 걸림 */}
      <g transform={reduce ? undefined : 'translate(0 -8)'} style={d(2600, reduce)}>
        <path d="M47 36 q5 5 10 0" {...sw(2.4)} stroke="var(--paper-accent)" />
        <circle cx="52" cy="39.5" r="1.6" {...sw(2)} stroke="var(--paper-accent)" />
        {!reduce && (
          <animateTransform attributeName="transform" type="translate" from="0 -8" to="0 0"
            begin="2.8s" dur="0.6s" fill="freeze" calcMode="spline" keySplines="0.3 0 0.5 1" keyTimes="0;1" />
        )}
      </g>
      <Label x="52" y="23" at="2.2" reduce={reduce}>총리 요셉</Label>
      <Label x="97" y="34" at="1.3" reduce={reduce}>일곱 해 곡식</Label>
    </g>
  )
}

// 형들과 상봉 (창 45:4-9)
function FamilyReunionScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M14 54 v-24 M11 30 h7" {...sw(1.3, 0.5)} />
      </g>
      {/* 포옹하는 두 사람 — 핵심 */}
      <g style={d(1000, reduce)}>
        <circle cx="52" cy="31" r="3" {...sw(2.6)} />
        <path d="M52 34 q1.5 6 2 12 M52.5 46 l-2.5 8 M54.5 46 l2 8" {...sw(2.6)} />
        <path d="M54 35 q5 1.5 8.5 5" {...sw(2.4)} />
        <circle cx="65" cy="33" r="2.9" {...sw(2.4)} />
        <path d="M64 35.8 q-1 6 -1.5 11 M62 46.5 l-2 7.5 M64.5 46.5 l2.5 7.5" {...sw(2.4)} />
        <path d="M63 36.5 q-4.5 1 -8 4" {...sw(2.2)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="rotate"
            values="0 58 44; 1.6 58 44; -1.6 58 44; 0 58 44" keyTimes="0;0.33;0.66;1"
            begin="2s" dur="1.4s" repeatCount="2" />
        )}
      </g>
      {/* 엎드린 형들 — 보조 */}
      <g style={d(2200, reduce)}>
        <circle cx="90" cy="49" r="2.3" {...sw(1.8)} />
        <path d="M92 50.2 q4.5 -1.8 7.5 1 M88 50.5 l-3.5 3" {...sw(1.8)} />
        <circle cx="102" cy="50.5" r="2" {...sw(1.5, 0.8)} />
        <path d="M103.5 51.5 q3.5 -1.2 6 0.8" {...sw(1.5, 0.8)} />
      </g>
      <Label x="46" y="21" at="1.5" reduce={reduce}>요셉</Label>
      <Label x="72" y="24" at="1.5" reduce={reduce}>베냐민</Label>
      <Label x="96" y="42" at="2.7" reduce={reduce}>형들</Label>
    </g>
  )
}

// 에브라임·므낫세 축복 (창 48:8-20)
function EphraimManassehScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
      </g>
      {/* 침상의 야곱 */}
      <g style={d(800, reduce)}>
        <path d="M18 50 h40 M22 54 v-4 M54 54 v-4" {...sw(2)} />
        <circle cx="26" cy="45" r="2.8" {...sw(2.4)} />
        <path d="M29 46.5 q8 2 16 1.5" {...sw(2.4)} />
      </g>
      {/* 두 손자 — 무릎 */}
      <g style={d(1600, reduce)}>
        <circle cx="74" cy="42" r="2.5" {...sw(2.2)} />
        <path d="M74 44.5 l-1.2 4.5 M68.5 54 h9" {...sw(2.2)} />
        <circle cx="92" cy="42" r="2.5" {...sw(2.2)} />
        <path d="M92 44.5 l-1.2 4.5 M86.5 54 h9" {...sw(2.2)} />
      </g>
      {/* 엇갈린 팔 — 핵심: X자 */}
      <g style={d(2500, reduce)}>
        <path d="M34 40 q22 -8 56 1" {...sw(2.6)} />
        <path d="M36 44 q20 6 52 -3" {...sw(2.6)} />
        <path d="M88 40.5 l-1.6 1.8 m3.2 -1.2 l-1.5 2 M72 40.5 l-1.5 1.6 m3 -1 l-1.4 1.8" {...sw(1.5)} />
      </g>
      <Label x="26" y="36" at="1.3" reduce={reduce}>야곱</Label>
      <Label x="74" y="33" at="2" reduce={reduce}>에브라임</Label>
      <Label x="94" y="33" at="2" reduce={reduce}>므낫세</Label>
      <Label x="60" y="61" at="3" reduce={reduce} size="4.2">엇바꾼 손</Label>
    </g>
  )
}

// 유골의 맹세 (창 50:22-26)
function DeathBonesScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M14 54 v-22 M11 32 h7 M92 54 v-22 M89 32 h7" {...sw(1.3, 0.5)} />
      </g>
      {/* 석관 — 핵심 */}
      <g style={d(900, reduce)}>
        <path d="M38 54 v-10 h44 v10 M36 44 h48" {...sw(2.4)} />
        <path d="M40 41 q20 -5 40 0" {...sw(2.2)} />
        <path d="M44 49 h6 m6 0 h6 m6 0 h6" {...sw(1.2, 0.5)} />
      </g>
      {/* 맹세하는 형제들 — 손 든 실루엣 */}
      <g style={d(1800, reduce)}>
        <circle cx="24" cy="40" r="2.5" {...sw(2)} />
        <path d="M24 42.5 v5 M22 54 l2 -6.5 l2 6.5 M25.8 44 q3 -3 3.5 -6.5" {...sw(2)} />
      </g>
      {/* 약속의 땅 별 — 서쪽 하늘 */}
      <g style={d(reduce ? 0 : 2800, reduce)} stroke="var(--paper-accent)">
        <path d="M60 20 v4 m-2 -2 h4 M57 17.5 l-1.6 -1.6 M63 17.5 l1.6 -1.6" {...sw(1.8)} />
        <path d="M60 27 v2 m0 3 v2" {...sw(1.3)} />
      </g>
      <Label x="60" y="61" at="1.5" reduce={reduce}>요셉의 관</Label>
      <Label x="60" y="10" at="3.2" reduce={reduce} size="4.2">내 해골을 메고 올라가라</Label>
    </g>
  )
}

const SCENES = {
  'authored-abraham-call-ur': { Scene: CallUrScene, desc: '고향 우르를 떠나라는 부르심을 따라나서다', caption: '부르심 — 창세기 12장' },
  'authored-abraham-shechem-promise': { Scene: ShechemPromiseScene, desc: '가나안 첫 자리에서 땅의 약속을 받고 단을 쌓다', caption: '세겜의 약속 — 창세기 12장' },
  'authored-abraham-covenant-ceremony': { Scene: CovenantCeremonyScene, desc: '쪼갠 제물 사이로 타는 횃불이 지나가다', caption: '횃불 언약 — 창세기 15장' },
  'authored-abraham-sodom-intercession': { Scene: SodomIntercessionScene, desc: '열 명의 의인을 두고 소돔을 위해 간구하다', caption: '중보 — 창세기 18장' },
  'authored-abraham-isaac-binding': { Scene: IsaacBindingScene, desc: '모리아 산에서 하나님이 숫양을 예비하시다', caption: '여호와 이레 — 창세기 22장' },
  'authored-abraham-sarah-burial': { Scene: SarahBurialScene, mood: 'dark', desc: '사라를 장사하며 약속의 땅 첫 소유를 얻다', caption: '막벨라 굴 — 창세기 23장' },
  'authored-isaac-birth-beersheba': { Scene: IsaacBirthScene, desc: '백 세 아브라함에게 약속의 아들이 태어나다', caption: '이삭의 출생 — 창세기 21장' },
  'authored-isaac-rebekah-marriage': { Scene: RebekahMarriageScene, desc: '종의 기도에 응답된 리브가가 아내가 되다', caption: '우물가의 리브가 — 창세기 24장' },
  'authored-isaac-esau-jacob-birth': { Scene: TwinsBirthScene, desc: '발꿈치를 잡은 야곱과 에서가 태어나다', caption: '쌍둥이 — 창세기 25장' },
  'authored-isaac-blessing-jacob': { Scene: BlessingJacobScene, desc: '눈 어두운 이삭이 야곱에게 장자의 복을 빌다', caption: '축복 — 창세기 27장' },
  'authored-jacob-bethel-dream': { Scene: BethelDreamScene, desc: '돌베개 위 꿈에서 하늘 사닥다리를 보다', caption: '벧엘의 꿈 — 창세기 28장' },
  'authored-jacob-haran-sojourn': { Scene: HaranSojournScene, desc: '라반의 집 20년, 열두 아들과 양 떼를 얻다', caption: '하란 체류 — 창세기 29-31장' },
  'authored-jacob-peniel-wrestling': { Scene: PenielWrestlingScene, desc: '얍복 나루의 씨름 끝에 이스라엘이 되다', caption: '브니엘 — 창세기 32장' },
  'authored-jacob-bethel-return': { Scene: BethelReturnScene, desc: '서원대로 벧엘에 돌아와 제단을 쌓다', caption: '벧엘 귀환 — 창세기 35장' },
  'authored-joseph-dothan-pit': { Scene: DothanPitScene, mood: 'dark', desc: '형들이 요셉을 구덩이에 던지고 팔아넘기다', caption: '도단 구덩이 — 창세기 37장' },
  'authored-joseph-egypt-prime-minister': { Scene: PrimeMinisterScene, desc: '바로의 꿈을 풀어 애굽의 총리가 되다', caption: '애굽 총리 — 창세기 41장' },
  'authored-joseph-egypt-family-reunion': { Scene: FamilyReunionScene, desc: '요셉이 형들 앞에 정체를 밝히고 울다', caption: '상봉 — 창세기 45장' },
  'authored-joseph-jacob-blesses-ephraim-manasseh': { Scene: EphraimManassehScene, desc: '야곱이 손을 엇바꾸어 두 손자를 축복하다', caption: '엇바꾼 축복 — 창세기 48장' },
  'authored-joseph-egypt-death-bones': { Scene: DeathBonesScene, desc: '내 해골을 메고 올라가라 — 마지막 유언', caption: '유골의 맹세 — 창세기 50장' },
}

export default SCENES
