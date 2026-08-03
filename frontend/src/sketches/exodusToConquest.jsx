// 출애굽에서 가나안까지 — 18개 정차지 장면 (task#229, #227 표준)
import { sw, d } from './lib'
import { Label } from './SceneLabel'

// 아기 모세 (출 1:22-2:10)
function BirthEgyptScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M6 50 q10 -3 20 0 q10 -3 20 0 q10 -3 20 0 q10 -3 20 0 q10 -3 20 0" {...sw(1.1, 0.5)} />
      </g>
      {/* 갈대 — 강가 */}
      <g style={d(700, reduce)}>
        <path d="M14 54 q-1 -12 1 -20 M18 54 q1 -14 -1 -22 M22 54 q-1 -10 2 -16" {...sw(1.3, 0.6)} />
      </g>
      {/* 갈 상자의 아기 — 핵심 */}
      <g style={d(1400, reduce)}>
        <path d="M40 51.5 q4 1.5 8 0 q4 1.5 8 0" {...sw(1.1, 0.4)} />
        <g>
          <path d="M42 50 q6 -3 12 0 q0 3 -6 3.5 q-6 -0.5 -6 -3.5 z" {...sw(2.6)} />
          <circle cx="48" cy="47.5" r="1.6" {...sw(2)} />
          {!reduce && (
            <animateTransform attributeName="transform" type="translate" values="0 0;0 -1;0 0"
              begin="2s" dur="1.8s" repeatCount="indefinite" />
          )}
        </g>
      </g>
      {/* 바로의 딸과 시녀 — 발견 */}
      <g style={d(2200, reduce)}>
        <circle cx="88" cy="30" r="2.8" {...sw(2.4)} />
        <path d="M88 32.8 v11.5 M85 54 l3 -9.5 l3 9.5 M85.5 36 q-3 2 -4.5 5.5" {...sw(2.4)} />
        <circle cx="98" cy="34" r="2.2" {...sw(1.8, 0.8)} />
        <path d="M98 36.2 v8.5 M96 54 l2 -7 l2 7" {...sw(1.8, 0.8)} />
      </g>
      <Label x="48" y="43" at="1.9" reduce={reduce}>갈 상자의 아기</Label>
      <Label x="90" y="24" at="2.7" reduce={reduce}>바로의 딸</Label>
    </g>
  )
}

// 미디안 도피 (출 2:11-15)
function FleesMidianScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        {/* 애굽 — 멀어지는 피라미드 */}
        <path d="M8 54 l7 -9 l7 9 M12 54 l4 -5 l4 5" {...sw(1.1, 0.35)} />
      </g>
      {/* 광야 지형 — 모래 언덕 */}
      <g style={d(800, reduce)}>
        <path d="M40 54 q14 -7 28 -1 q16 -6 34 0" {...sw(1.3, 0.5)} />
      </g>
      {/* 도망치는 모세 — 핵심: 뒤돌아봄 */}
      <g transform={reduce ? 'translate(30 0)' : undefined} style={d(1600, reduce)}>
        <circle cx="34" cy="32" r="2.8" {...sw(2.5)} />
        <path d="M34 34.8 v10.2 M31 54 l3 -9 l3 9 M36.5 33.5 q2 -1.5 2.5 -3.5" {...sw(2.5)} />
        <path d="M31.5 37 l-4.5 -3" {...sw(1.8)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="translate" from="0 0" to="30 0"
            begin="2.2s" dur="2s" fill="freeze" calcMode="spline" keySplines="0.3 0 0.6 1" keyTimes="0;1" />
        )}
      </g>
      {/* 미디안의 양떼 — 목자로의 예표 */}
      <g style={d(2800, reduce)}>
        <path d="M96 51 q2.5 -2.5 5 0 q1 -2 -0.5 -3.5" {...sw(1.6, 0.75)} />
        <path d="M104 52 q2 -2 4 0" {...sw(1.4, 0.6)} />
      </g>
      <Label x="34" y="24" at="2.5" reduce={reduce}>도망치는 모세</Label>
      <Label x="12" y="38" at="0.9" reduce={reduce}>애굽</Label>
    </g>
  )
}

// 떨기나무 (출 3:1-12)
function BurningBushScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M74 54 L98 26 L114 40" {...sw(1.4, 0.5)} />
      </g>
      {/* 떨기나무 불 — 핵심: 타되 사그라지지 않음 */}
      <g style={d(800, reduce)}>
        <path d="M56 54 q-4 -3 -3 -8 M60 54 q0 -6 0 -9 M64 54 q4 -3 3 -8 M57 47 q3 -2 6 0" {...sw(2)} />
        <path d="M56 45 q-3 -6 1 -10 q3 3 1 7 M60 44 q-2 -7 2 -11 q3 4 0.5 9 M64 44.5 q3 -5 0 -9" {...sw(2.8)}>
          {!reduce && <animate attributeName="opacity" values="1;0.55;1;0.7;1" begin="2s" dur="1.6s" repeatCount="3" />}
        </path>
      </g>
      {/* 모세 — 주역: 무릎, 벗은 신 */}
      <g style={d(1800, reduce)}>
        <circle cx="30" cy="40" r="2.9" {...sw(2.5)} />
        <path d="M30 42.9 l-1.5 5.6 M23 54 h10.5 M28.5 48.5 q-3.8 1.8 -5.5 5.5 M29 45 q4 0.5 6.5 3" {...sw(2.5)} />
        <path d="M17 52.5 q2 -1.6 4 0 M17.8 53.6 h2.8" {...sw(1.3, 0.6)} />
      </g>
      <g style={d(reduce ? 0 : 3000, reduce)} stroke="var(--paper-accent)">
        <path d="M61 28 v-4 M53 31 l-2.6 -2.6 M69 31 l2.6 -2.6" {...sw(1.5)} />
      </g>
      <Label x="30" y="31" at="2.3" reduce={reduce}>모세</Label>
      <Label x="61" y="24" at="1.3" reduce={reduce}>떨기나무 불꽃</Label>
    </g>
  )
}

// 애굽 귀환 (출 4:27-31)
function ReturnsEgyptScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        {/* 피라미드 원경 */}
        <path d="M78 54 l14 -18 l14 18 M96 54 l9 -11 l9 11" {...sw(1.3, 0.5)} />
        <path d="M86 44 l6 7" {...sw(1.1, 0.35)} />
      </g>
      {/* 모세·아론 상봉 — 핵심: 맞잡음 */}
      <g style={d(1000, reduce)}>
        <circle cx="42" cy="33" r="2.9" {...sw(2.5)} />
        <path d="M42 35.9 v9.6 M39 54 l3 -7 M46 53.5 l-3 -7 M44.5 38 l6.5 3.5" {...sw(2.5)} />
        <path d="M39.5 38.5 l-4 9.5 M38 37.5 q-1 -3 1 -4.5" {...sw(1.8)} />
        <circle cx="58" cy="34" r="2.8" {...sw(2.3)} />
        <path d="M58 36.8 v8.7 M55 54 l3 -7 M61.5 53.5 l-3 -7 M55.5 39 l-4.5 2.5" {...sw(2.3)} />
      </g>
      {/* 길 — 점선 */}
      <g style={d(2200, reduce)}>
        <path d="M14 52 h3 m5 0.6 h3 m5 0.6 h3" {...sw(1.2, 0.5)} />
      </g>
      <Label x="40" y="24" at="1.5" reduce={reduce}>모세</Label>
      <Label x="62" y="25" at="1.5" reduce={reduce}>아론</Label>
      <Label x="99" y="30" at="0.9" reduce={reduce}>애굽</Label>
    </g>
  )
}

// 열 재앙 (출 7:14-12:30)
function TenPlaguesScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        {/* 피라미드 원경 */}
        <path d="M92 54 l9 -11 l9 11 M100 54 l5 -6 l5 6" {...sw(1.2, 0.4)} />
        {/* 나일 강 — 잔잔한 물결 */}
        <path d="M10 44 q8 -3 16 0 q8 -3 16 0 q8 -3 16 0 q8 -3 16 0 M10 48 q8 -3 16 0 q8 -3 16 0 q8 -3 16 0 q8 -3 16 0" {...sw(1.1, 0.5)} />
      </g>
      {/* 피가 된 강물 */}
      <g style={d(800, reduce)} stroke="var(--paper-accent)">
        <path d="M10 46 q8 -3 16 0 q8 -3 16 0 q8 -3 16 0 q8 -3 16 0" {...sw(2.2)} />
      </g>
      {/* 개구리 재앙 */}
      <g style={d(800, reduce)}>
        <path d="M20 52.5 q1.6 -2.4 3.2 0 M27 53.2 q1.3 -1.8 2.6 0" {...sw(1.3, 0.6)} />
      </g>
      {/* 흑암 재앙 — 빛을 잃는 해 */}
      <g style={d(1800, reduce)}>
        <circle cx="100" cy="14" r="4.5" {...sw(2)} />
        <path d="M100 6.5 v-2.2 M108 14 h2.2 M92 14 h-2.2 M94.4 8.4 l-1.6 -1.6 M105.6 8.4 l1.6 -1.6" {...sw(1.3, 0.6)}>
          {!reduce && <animate attributeName="opacity" values="1;0.5;0.1" begin="2s" dur="1.3s" fill="freeze" />}
        </path>
      </g>
      {/* 표 없는 문 — 초태생 재앙의 전조 */}
      <g style={d(2800, reduce)}>
        <path d="M76 54 v-18 M90 54 v-18 M73 36 h20" {...sw(2.4)} />
        <path d="M79 54 v-14 h8 v14" {...sw(1.5, 0.7)} />
      </g>
      <Label x="24" y="40" at="2.1" reduce={reduce}>피가 된 나일 강</Label>
      <Label x="100" y="25" at="3.1" reduce={reduce}>짙어진 흑암</Label>
    </g>
  )
}

// 유월절 밤 (출 12:31-42)
function PassoverNightScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M96 16 a6 6 0 1 1 -4 -10 a7.5 7.5 0 0 0 4 10" {...sw(1.6)} />
        <path d="M14 12 v2.4 m-1.2 -1.2 h2.4" {...sw(1.2, 0.6)} />
      </g>
      {/* 문설주 — 핵심 */}
      <g style={d(800, reduce)}>
        <path d="M34 54 v-22 M54 54 v-22 M31 32 h26" {...sw(2.6)} />
        <path d="M38 54 v-18 h12 v18" {...sw(1.6, 0.7)} />
      </g>
      {/* 피 표시 — 강조색 3점 */}
      <g style={d(1800, reduce)} stroke="var(--paper-accent)">
        <path d="M34 38 q1.5 2.5 0 4.5 M54 38 q1.5 2.5 0 4.5 M44 29.5 q1.5 2.5 0 4.5" {...sw(2.4)} />
      </g>
      {/* 떠나는 행렬 — 밤에 나섬 */}
      <g transform={reduce ? 'translate(10 0)' : undefined} style={d(2600, reduce)}>
        <circle cx="72" cy="43" r="2.2" {...sw(2)} />
        <path d="M72 45.2 v4 M70 54 l2 -5 l2 5" {...sw(2)} />
        <circle cx="80" cy="44" r="2" {...sw(1.8)} />
        <path d="M80 46 v3.5 M78.2 54 l1.8 -4.5 l1.8 4.5" {...sw(1.8)} />
        <circle cx="87" cy="44.5" r="1.8" {...sw(1.6, 0.85)} />
        <path d="M87 46.3 v3 M85.5 54 l1.5 -4 l1.5 4" {...sw(1.6, 0.85)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="translate" from="0 0" to="12 0"
            begin="2.9s" dur="2s" fill="freeze" calcMode="spline" keySplines="0.3 0 0.7 1" keyTimes="0;1" />
        )}
      </g>
      <Label x="44" y="60" at="2.1" reduce={reduce}>피 바른 문설주</Label>
      <Label x="84" y="34" at="3.4" reduce={reduce}>떠나는 이스라엘</Label>
    </g>
  )
}

// 숙곳 첫 진영 (출 12:37)
function SuccothCampScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M8 44 q12 -7 24 -2" {...sw(1.1, 0.4)} />
      </g>
      {/* 장막들 */}
      <g style={d(800, reduce)}>
        <path d="M24 54 l9 -13 l9 13 M30 54 l3 -5 l3 5" {...sw(2.2)} />
        <path d="M62 54 l7 -10 l7 10" {...sw(1.8, 0.8)} />
        <path d="M92 54 l6 -8 l6 8" {...sw(1.5, 0.6)} />
      </g>
      {/* 모닥불 + 무교병 — 핵심 */}
      <g style={d(1800, reduce)}>
        <path d="M48 52 l3 -2 m-3 0 l3 2 M47 52.5 h5" {...sw(1.4)} />
        <path d="M49.5 48.5 q-1.8 -3.5 0 -6 q1.8 2.5 0 6 M52 48.5 q-1.4 -4 0.6 -6.5" {...sw(2.6)} />
        <ellipse cx="80" cy="50" rx="5" ry="1.8" {...sw(1.8)} />
        <ellipse cx="86" cy="52" rx="4.5" ry="1.6" {...sw(1.5, 0.8)} />
      </g>
      <g style={d(reduce ? 0 : 2800, reduce)}>
        <path d="M49 40 q-2 -3 -0.5 -5.5" {...sw(1.2, 0.55)} />
      </g>
      <Label x="33" y="35" at="1.3" reduce={reduce}>첫 진영</Label>
      <Label x="83" y="43" at="2.3" reduce={reduce}>누룩 없는 떡</Label>
    </g>
  )
}

// 홍해 도하 (출 14:21-31)
function RedSeaCrossingScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M6 52 q8 -3 16 0 M100 52 q8 -3 14 0" {...sw(1.1, 0.4)} />
        {/* 갈라진 바닥 — 조개·자갈 결 */}
        <path d="M42 53 q1 -1 2 0 M52 52.6 q1 -1 2 0 M62 53.2 q1 -1 2 0 M72 52.8 q1 -1 2 0" {...sw(1.3, 0.5)} />
      </g>
      {/* 갈라진 물벽 — 핵심 */}
      <g style={d(700, reduce)}>
        <path d="M20 54 q-2 -14 1 -28 q3 -8 -1 -16 M26 54 q2 -16 -1 -30 q-2 -6 2 -14 M32 54 q-1 -14 2 -28 q2 -8 -2 -14" {...sw(2.6)} />
        <path d="M88 54 q2 -14 -1 -28 q-3 -8 1 -16 M94 54 q-2 -16 1 -30 q2 -6 -2 -14 M100 54 q1 -14 -2 -28 q-2 -8 2 -14" {...sw(2.6)} />
        <path d="M22 24 q3 -3 6 0 M92 24 q-3 -3 -6 0" {...sw(1.4, 0.6)} />
      </g>
      {/* 모세 — 손을 내밀어 바다를 가름 */}
      <g style={d(1600, reduce)}>
        <circle cx="10" cy="32" r="2.8" {...sw(2.6)} />
        <path d="M10 34.8 v9.4 M7.5 54 l2.5 -7.5 l2.5 7.5" {...sw(2.6)} />
        <g transform={reduce ? undefined : 'rotate(35 12 35)'}>
          <path d="M12 35 L34 25" {...sw(2.4)} />
          {!reduce && (
            <animateTransform attributeName="transform" type="rotate" from="35 12 35" to="0 12 35"
              begin="1.9s" dur="0.6s" fill="freeze" calcMode="spline" keySplines="0.3 0 0.6 1" keyTimes="0;1" />
          )}
        </g>
      </g>
      {/* 마른 땅을 건너는 이스라엘 */}
      <g transform={reduce ? 'translate(8 0)' : undefined} style={d(2400, reduce)}>
        <circle cx="46" cy="47" r="1.9" {...sw(1.8)} />
        <path d="M46 48.9 v3.6 M44.3 54 l1.7 -3.8 l1.7 3.8" {...sw(1.8)} />
        <circle cx="55" cy="47.5" r="1.8" {...sw(1.7, 0.85)} />
        <path d="M55 49.3 v3.2 M53.4 54 l1.6 -3.5 l1.6 3.5" {...sw(1.7, 0.85)} />
        <circle cx="64" cy="48" r="1.7" {...sw(1.6, 0.75)} />
        <path d="M64 49.7 v3 M62.5 54 l1.5 -3.2 l1.5 3.2" {...sw(1.6, 0.75)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="translate" from="0 0" to="8 0"
            begin="2.7s" dur="1.8s" fill="freeze" calcMode="spline" keySplines="0.3 0 0.6 1" keyTimes="0;1" />
        )}
      </g>
      {/* 되돌아온 물에 잠기는 애굽 병거 */}
      <g style={d(3200, reduce)}>
        <path d="M100 54 q2 -5 6 -5 q4 0 6 5" {...sw(2)} />
        <path d="M102 49 l5 -4 M107 45 l4 3" {...sw(1.8)} />
        <path d="M96 51 q2 -2 4 0 q2 -2 4 0" {...sw(1.4, 0.7)} />
      </g>
      <Label x="10" y="24" at="1.9" reduce={reduce}>모세</Label>
      <Label x="60" y="61" at="2.9" reduce={reduce}>마른 땅으로 건너다</Label>
      <Label x="106" y="38" at="3.7" reduce={reduce}>물에 잠긴 애굽 군대</Label>
    </g>
  )
}

// 마라와 엘림 (출 15:22-27)
function MarahElimScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M6 50 q10 -3 20 0" {...sw(1.1, 0.4)} />
      </g>
      {/* 마라의 쓴 물 — 날 선 물결 */}
      <g style={d(800, reduce)}>
        <ellipse cx="26" cy="52" rx="8" ry="2.6" {...sw(1.8)} />
        <path d="M20 51 l2 -1.5 l2 1.5 l2 -1.5 l2 1.5 l2 -1.5 l2 1.5" {...sw(1.4, 0.6)} />
      </g>
      {/* 모세 — 나무를 던짐 */}
      <g style={d(1600, reduce)}>
        <circle cx="14" cy="34" r="2.6" {...sw(2.4)} />
        <path d="M14 36.6 v9.4 M11.5 54 l2.5 -7 l2.5 7 M16.3 38 q3 -1 5 -3" {...sw(2.4)} />
        <path d="M20 34 l3 1 l-1 2 l-3 -1 z" {...sw(1.6)}>
          {!reduce && <animateMotion path="M0 0 q3 8 6 16" begin="1.9s" dur="0.7s" fill="freeze" />}
        </path>
      </g>
      {/* 달게 된 물 — 잔잔한 파문 */}
      <g style={d(2200, reduce)}>
        <path d="M23 50.5 q2 1.6 4 0 M22 52.5 q3 2.2 6 0" {...sw(1.3, 0.55)} />
      </g>
      {/* 엘림의 종려나무와 샘물 열둘 */}
      <g style={d(2600, reduce)}>
        <path d="M70 54 v-9 M65 45 q5 -3 10 0 M66 42.5 q4 -3 8 0" {...sw(1.8)} />
        <path d="M84 54 v-7 M80 46 q4 -2.5 8 0 M81 44 q3 -2.5 6 0" {...sw(1.6, 0.8)} />
        <path d="M96 54 v-6 M93 47 q3 -2 6 0" {...sw(1.3, 0.6)} />
        <ellipse cx="64" cy="53" rx="2.2" ry="0.9" {...sw(1.5, 0.7)} />
        <ellipse cx="76" cy="52.5" rx="2" ry="0.8" {...sw(1.4, 0.6)} />
        <ellipse cx="90" cy="53" rx="1.8" ry="0.7" {...sw(1.3, 0.55)} />
        <ellipse cx="102" cy="53.3" rx="1.6" ry="0.6" {...sw(1.2, 0.5)} />
      </g>
      <Label x="22" y="60" at="2.1" reduce={reduce}>마라의 쓴 물이 달게 되다</Label>
      <Label x="84" y="34" at="3" reduce={reduce}>엘림의 샘과 종려나무</Label>
    </g>
  )
}

// 신 광야의 만나와 메추라기 (출 16:11-15)
function MannaQuailScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M14 54 l6 -8 l6 8 M60 54 l5 -7 l5 7 M96 54 l5 -6 l5 6" {...sw(1.3, 0.5)} />
      </g>
      {/* 저녁의 메추라기 — 진영으로 내려앉음 */}
      <g transform={reduce ? undefined : 'translate(0 -12)'} style={d(800, reduce)}>
        <path d="M40 20 q2 -2 4 0 q2 -2 4 0 M56 16 q2 -2 4 0 q2 -2 4 0 M70 22 q2 -2 4 0 q2 -2 4 0" {...sw(1.8)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="translate" from="0 -12" to="0 0"
            begin="1.4s" dur="1.1s" fill="freeze" calcMode="spline" keySplines="0.3 0 0.6 1" keyTimes="0;1" />
        )}
      </g>
      {/* 아침의 만나 — 서리 같은 것 */}
      <g style={d(1800, reduce)}>
        <circle cx="24" cy="52.4" r="0.6" {...sw(1.4)} />
        <circle cx="28" cy="51" r="0.7" {...sw(1.6)} />
        <circle cx="33" cy="52.2" r="0.6" {...sw(1.5)} />
        <circle cx="38" cy="51.4" r="0.7" {...sw(1.6)} />
        <circle cx="44" cy="52.6" r="0.6" {...sw(1.4)} />
        <circle cx="49" cy="51.6" r="0.7" {...sw(1.6)} />
      </g>
      {/* 만나를 거두는 사람 */}
      <g style={d(2600, reduce)}>
        <circle cx="34" cy="44" r="2.4" {...sw(2.2)} />
        <path d="M34 46.4 v4 M31 54 q0 -2.4 1.5 -3.6 M37 54 l-2 -3.6 M36 47 q3 1 4 4" {...sw(2.2)} />
        <path d="M39 51 q1 2 4 2 q3 0 4 -2" {...sw(1.6)} />
      </g>
      <Label x="56" y="8" at="1.7" reduce={reduce}>저녁의 메추라기</Label>
      <Label x="36" y="38" at="3.2" reduce={reduce}>아침의 만나</Label>
    </g>
  )
}

// 르비딤 반석의 물 (출 17:1-7)
function RephidimWaterScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M70 54 L90 20 L110 54" {...sw(1.6, 0.6)} />
      </g>
      {/* 호렙산 반석 */}
      <g style={d(900, reduce)}>
        <path d="M46 54 q-2 -10 4 -14 q6 -3 10 1 q5 3 2 8 q3 4 -2 6 q-4 3 -9 1 q-4 1 -5 -2 z" {...sw(2.4)} />
      </g>
      {/* 지팡이로 침 */}
      <g style={d(1800, reduce)}>
        <circle cx="26" cy="36" r="2.7" {...sw(2.5)} />
        <path d="M26 38.7 v9.3 M23.5 54 l2.5 -7 l2.5 7" {...sw(2.5)} />
        <g transform={reduce ? undefined : 'rotate(-50 28 38)'}>
          <path d="M28 38 L44 46" {...sw(2.4)} />
          {!reduce && (
            <animateTransform attributeName="transform" type="rotate" from="-50 28 38" to="0 28 38"
              begin="2.1s" dur="0.5s" fill="freeze" calcMode="spline" keySplines="0.3 0 0.7 1" keyTimes="0;1" />
          )}
        </g>
      </g>
      {/* 반석에서 솟는 물 + 마시는 백성 */}
      <g style={d(2600, reduce)}>
        <path d="M50 44 q1 5 -1 10 M54 42 q2 6 0 12" {...sw(2.2)} />
        <circle cx="64" cy="48" r="1.9" {...sw(1.8)} />
        <path d="M64 49.9 v3 M62 54 q0 -1.6 1 -2.4 M66.5 54 l-1.5 -2.4 M65.5 50 q2 1.5 3.5 3.5" {...sw(1.8)} />
        <circle cx="71" cy="49" r="1.7" {...sw(1.6, 0.8)} />
        <path d="M71 50.7 v2.6 M69.3 54 l1.7 -2.9 l1.7 2.9" {...sw(1.6, 0.8)} />
      </g>
      <Label x="26" y="28" at="2.3" reduce={reduce}>모세</Label>
      <Label x="56" y="38" at="3" reduce={reduce}>반석에서 솟은 물</Label>
    </g>
  )
}

// 아말렉 전투와 들린 손 (출 17:8-13)
function AmalekBattleScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M60 54 L78 24 L96 54" {...sw(1.6, 0.6)} />
      </g>
      {/* 여호수아와 아말렉의 싸움 */}
      <g style={d(900, reduce)}>
        <circle cx="24" cy="42" r="2.4" {...sw(2.2)} />
        <path d="M24 44.4 v7.6 M21.5 54 l2.5 -6 l2.5 6 M26.5 43 L36 38" {...sw(2.2)} />
        <circle cx="42" cy="43" r="2.2" {...sw(1.8, 0.85)} />
        <path d="M42 45.2 v6.8 M40 54 l2 -5.5 l2 5.5 M39.5 44 L32 40" {...sw(1.8, 0.85)} />
      </g>
      {/* 모세 — 산꼭대기에 앉아 손을 들다 */}
      <g style={d(1800, reduce)}>
        <path d="M74 24 q4 -3 8 0 q0 3.5 -4 3.5 q-4 0 -4 -3.5 z" {...sw(2.2)} />
        <circle cx="78" cy="14" r="2.7" {...sw(2.6)} />
        <path d="M78 16.7 v4.3 M78 21 q-4 3 -6 8 M78 21 q4 3 6 8 M78 17.5 L69 10 M78 17.5 L87 10" {...sw(2.6)} />
      </g>
      {/* 아론과 훌 — 손을 붙듦 */}
      <g style={d(2600, reduce)}>
        <circle cx="64" cy="16" r="2.1" {...sw(1.9)} />
        <path d="M64 18.1 v7 M62 30 l2 -4.9 l2 4.9 M65.8 17 L69 10" {...sw(1.9)} />
        <circle cx="92" cy="16" r="2" {...sw(1.8, 0.9)} />
        <path d="M92 18 v6.8 M90 29 l2 -4.8 l2 4.8 M90.3 17 L87 10" {...sw(1.8, 0.9)} />
      </g>
      <Label x="30" y="34" at="1.6" reduce={reduce}>여호수아의 싸움</Label>
      <Label x="78" y="7" at="3" reduce={reduce}>들린 손</Label>
    </g>
  )
}

// 이드로의 조언과 재판관 세움 (출 18:1-26)
function JethroCounselScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M90 54 L102 28 L114 54" {...sw(1.4, 0.5)} />
      </g>
      {/* 소송을 기다리는 줄 */}
      <g style={d(900, reduce)}>
        <circle cx="20" cy="45" r="1.8" {...sw(1.7, 0.8)} />
        <path d="M20 46.8 v3.4 M18.3 54 l1.7 -3.8 l1.7 3.8" {...sw(1.7, 0.8)} />
        <circle cx="27" cy="45.5" r="1.7" {...sw(1.6, 0.7)} />
        <path d="M27 47.2 v3.1 M25.4 54 l1.6 -3.7 l1.6 3.7" {...sw(1.6, 0.7)} />
        <circle cx="34" cy="46" r="1.6" {...sw(1.5, 0.6)} />
        <path d="M34 47.6 v2.9 M32.5 54 l1.5 -3.5 l1.5 3.5" {...sw(1.5, 0.6)} />
      </g>
      {/* 홀로 재판하는 모세 */}
      <g style={d(1800, reduce)}>
        <circle cx="50" cy="42" r="2.6" {...sw(2.4)} />
        <path d="M50 44.6 v6 M47.5 54 q0 -2 1 -3 M53 54 l-1.5 -3" {...sw(2.4)} />
      </g>
      {/* 이드로 — 찾아와 조언함 */}
      <g style={d(2600, reduce)}>
        <circle cx="66" cy="34" r="2.7" {...sw(2.5)} />
        <path d="M66 36.7 v9.3 M63.5 54 l2.5 -8 l2.5 8 M70 40 v14 M63.7 39 q-4 1 -7 3" {...sw(2.5)} />
      </g>
      {/* 천부장 · 백부장 · 오십부장 · 십부장 */}
      <g style={d(3200, reduce)}>
        <path d="M90 44 v-2" {...sw(2.2)} />
        <path d="M86 47 v-2 M94 47 v-2" {...sw(1.9)} />
        <path d="M83 50 v-2 M90 50 v-2 M97 50 v-2" {...sw(1.6)} />
        <path d="M80 53 v-2 M87 53 v-2 M94 53 v-2 M101 53 v-2" {...sw(1.3)} />
      </g>
      <Label x="50" y="32" at="1.9" reduce={reduce}>지친 모세</Label>
      <Label x="66" y="26" at="2.7" reduce={reduce}>이드로의 조언</Label>
      <Label x="90" y="40" at="3.4" reduce={reduce}>재판관을 세우다</Label>
    </g>
  )
}

// 시내산 율법 (출 19-20)
function SinaiLawScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M22 54 L60 14 L98 54" {...sw(2.4)} />
        <path d="M40 36 l6 -5 M74 34 l-5 -4" {...sw(1.2, 0.4)} />
      </g>
      {/* 연기·번개 */}
      <g style={d(1000, reduce)}>
        <path d="M52 14 q-4 -4 -1 -8 M60 12 q-3 -5 1 -9 M67 15 q4 -4 1.5 -8" {...sw(1.4, 0.65)} />
        <path d="M46 22 l-5 6 l4 0 l-5 6" {...sw(1.8)}>
          {!reduce && <animate attributeName="opacity" values="1;0.3;1" begin="2s" dur="0.7s" repeatCount="2" />}
        </path>
      </g>
      {/* 두 돌판 — 핵심: 내려옴 */}
      <g transform={reduce ? undefined : 'translate(0 -10)'} style={d(2000, reduce)}>
        <path d="M52 40 v-9 q0 -3 3 -3 h1 q3 0 3 3 v9 z M60 40 v-9 q0 -3 3 -3 h1 q3 0 3 3 v9 z" {...sw(2.6)} />
        <path d="M54.5 32 h4 m-4 3 h4 M62.5 32 h4 m-4 3 h4" {...sw(1.2)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="translate" from="0 -10" to="0 0"
            begin="2.3s" dur="0.7s" fill="freeze" calcMode="spline" keySplines="0.3 0 0.5 1" keyTimes="0;1" />
        )}
      </g>
      {/* 산 아래 회중 */}
      <g style={d(3000, reduce)}>
        <circle cx="14" cy="49" r="1.8" {...sw(1.5, 0.7)} />
        <path d="M14 50.8 v3.2" {...sw(1.5, 0.7)} />
        <circle cx="106" cy="49" r="1.8" {...sw(1.5, 0.7)} />
        <path d="M106 50.8 v3.2" {...sw(1.5, 0.7)} />
      </g>
      <Label x="60" y="60" at="1" reduce={reduce}>시내산</Label>
      <Label x="60" y="22" at="3.2" reduce={reduce}>십계명 돌판</Label>
    </g>
  )
}

// 금송아지와 언약 갱신 (출 32:1-34:28)
function GoldenCalfScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        {/* 시내산 — 방금 내려온 곳 */}
        <path d="M8 54 L24 22 L40 54" {...sw(1.2, 0.4)} />
      </g>
      {/* 금송아지 — 백성이 만들어 뛰놀며 절함 */}
      <g style={d(900, reduce)}>
        <path d="M74 54 v-4 h10 v4" {...sw(1.8)} />
        <path d="M76 50 q3 -3 6 0 q1 -3 -1 -5 M78 44 l-1.5 -2 M84 44 l1.5 -2" {...sw(2)} />
        <circle cx="64" cy="46" r="1.9" {...sw(1.7, 0.8)} />
        <path d="M64 47.9 v3.6 M62 54 l2 -3.8 l2 3.8 M62 47 l-2.5 -2.5 M66 47 l2.5 -2.5" {...sw(1.7, 0.8)} />
        <circle cx="94" cy="46.5" r="1.8" {...sw(1.6, 0.7)} />
        <path d="M94 48.3 v3.3 M92.2 54 l1.8 -3.6 l1.8 3.6 M92.2 47.5 l-2.4 -2.2 M95.8 47.5 l2.4 -2.2" {...sw(1.6, 0.7)} />
      </g>
      {/* 모세 — 진노하여 산에서 내려옴 */}
      <g style={d(1900, reduce)}>
        <circle cx="20" cy="30" r="2.8" {...sw(2.6)} />
        <path d="M20 32.8 v10 M17 54 l3 -8 l3 8 M22.6 32 q3 -2 5 -5" {...sw(2.6)} />
      </g>
      {/* 깨어진 돌판 — 핵심 */}
      <g style={d(2800, reduce)}>
        <path d="M30 52 v-9 q0 -2.5 2.5 -2.5 h1.5 v11.5 z M36 52 v-9 q0 -2.5 -2.5 -2.5 h-1.5" {...sw(2.8)} />
        <path d="M32 46 l2 -4 l2 5" {...sw(1.6)} />
      </g>
      {/* 다시 받아 오르는 새 돌판 — 회복 */}
      <g style={d(reduce ? 0 : 3400, reduce)} stroke="var(--paper-accent)">
        <path d="M22 26 v-6 q0 -2 2 -2 h1.6 v8 z" {...sw(2)} />
      </g>
      <Label x="80" y="38" at="1.6" reduce={reduce}>금송아지</Label>
      <Label x="20" y="24" at="2.7" reduce={reduce}>진노한 모세</Label>
      <Label x="33" y="60" at="3.4" reduce={reduce}>깨어진 돌판</Label>
    </g>
  )
}

// 성막 봉헌과 영광의 임재 (출 40:17-38)
function TabernacleGloryScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M10 46 q10 -6 20 -1 M92 45 q10 -6 20 -1" {...sw(1.1, 0.4)} />
      </g>
      {/* 완성된 성막 */}
      <g style={d(900, reduce)}>
        <path d="M46 54 v-20 h28 v20 M46 34 l14 -6 l14 6" {...sw(2.4)} />
        <path d="M52 54 v-14 h16 v14" {...sw(1.5, 0.7)} />
        <path d="M50 40 h20 M50 45 h20 M50 50 h20" {...sw(1.2, 0.5)} />
      </g>
      {/* 구름이 덮고 영광이 충만함 — 핵심 */}
      <g style={d(1900, reduce)}>
        <path d="M48 20 q0 -6 7 -6 q3 -4 8 -2 q6 -1 6 4 q4 2 1 5 q-5 3 -11 2 q-8 2 -11 -3 z" {...sw(2.8)} />
      </g>
      {/* 들어가지 못하는 모세 */}
      <g style={d(2800, reduce)}>
        <circle cx="30" cy="42" r="2.6" {...sw(2.4)} />
        <path d="M30 44.6 v9.4 M27.5 54 l2.5 -7 l2.5 7 M32.5 45 q3 -1.5 4 -4" {...sw(2.4)} />
      </g>
      <Label x="60" y="12" at="2.2" reduce={reduce}>여호와의 영광</Label>
      <Label x="30" y="34" at="3" reduce={reduce}>들어가지 못한 모세</Label>
    </g>
  )
}

// 바란 광야 방랑 (민 10:12)
function ParanWanderingScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M6 50 q14 -4 28 0 q14 -4 28 0 M70 51 q14 -4 28 0" {...sw(1.2, 0.45)} />
      </g>
      {/* 구름 기둥 — 핵심 */}
      <g style={d(1000, reduce)}>
        <path d="M56 46 q-1 -14 0 -26" {...sw(2)} />
        <path d="M48 18 q0 -6 7 -6 q3 -4 8 -2 q6 -1 6 4 q4 2 1 5 q-5 3 -11 2 q-8 2 -11 -3" {...sw(2.4)} />
      </g>
      {/* 행렬 — 구불한 발자국 + 사람들 */}
      <g transform={reduce ? 'translate(8 0)' : undefined} style={d(2000, reduce)}>
        <path d="M14 50 q10 -3 18 0 q10 -3 18 0" {...sw(1.3, 0.55)} strokeDasharray="2.4 2.2" />
        <circle cx="26" cy="45" r="2" {...sw(1.9)} />
        <path d="M26 47 v3.5 M24.3 54 l1.7 -4 l1.7 4" {...sw(1.9)} />
        <circle cx="36" cy="45.5" r="1.8" {...sw(1.7, 0.85)} />
        <path d="M36 47.3 v3 M34.5 54 l1.5 -3.8 l1.5 3.8" {...sw(1.7, 0.85)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="translate" from="0 0" to="10 0"
            begin="2.4s" dur="2.4s" fill="freeze" />
        )}
      </g>
      <Label x="56" y="30" at="1.5" reduce={reduce}>구름 기둥</Label>
      <Label x="30" y="36" at="2.6" reduce={reduce}>사십 년 광야</Label>
    </g>
  )
}

// 기브롯 핫다아와의 메추라기 (민 11:31-34)
function KibrothHattaavahScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M10 46 q12 -7 24 -1" {...sw(1.1, 0.4)} />
      </g>
      {/* 바람에 실려 오는 메추라기 떼 */}
      <g style={d(900, reduce)}>
        <path d="M40 20 q2 -2 4 0 q2 -2 4 0 M54 16 q2 -2 4 0 q2 -2 4 0 M68 22 q2 -2 4 0 q2 -2 4 0 M82 18 q2 -2 4 0 q2 -2 4 0" {...sw(2)} />
      </g>
      {/* 진영 사방에 두 규빗 높이로 쌓인 메추라기 */}
      <g style={d(1900, reduce)}>
        <path d="M46 52 q2 -1.6 4 0 q2 -1.6 4 0 q2 -1.6 4 0 M64 51.5 q2 -1.6 4 0 q2 -1.6 4 0 q2 -1.6 4 0" {...sw(1.8, 0.85)} />
      </g>
      {/* 탐욕으로 먹다 재앙에 쓰러짐 — 핵심 */}
      <g style={d(2600, reduce)} stroke="var(--paper-accent)">
        <circle cx="30" cy="46" r="2.2" {...sw(2.2)} />
        <path d="M28 51 l4 -3 M28 48 l4 3" {...sw(2)} />
      </g>
      {/* 기브롯 핫다아와 — 탐욕의 무덤 */}
      <g style={d(3200, reduce)}>
        <path d="M18 54 q1 -3 4 -3 q3 0 4 3 M96 54 q1 -3 4 -3 q3 0 4 3" {...sw(2.4)} />
      </g>
      <Label x="60" y="12" at="1.6" reduce={reduce}>바람에 실려 온 메추라기</Label>
      <Label x="20" y="60" at="3.4" reduce={reduce}>탐욕의 무덤</Label>
    </g>
  )
}

// 미리암과 아론의 비방 (민 12:1-15)
function MiriamAaronRebukeScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M10 47 q12 -7 24 -1" {...sw(1.1, 0.4)} />
      </g>
      {/* 미리암과 아론 — 모세를 비방함 */}
      <g style={d(900, reduce)}>
        <circle cx="30" cy="36" r="2.6" {...sw(2.2)} />
        <path d="M30 38.6 v9.4 M27.5 54 l2.5 -7 l2.5 7 M32.5 39 q3 -1 4 -3" {...sw(2.2)} />
        <circle cx="46" cy="35" r="2.4" {...sw(2)} />
        <path d="M46 37.4 v8.6 M43.7 54 l2.3 -6.5 l2.3 6.5 M43.5 38 q-3 -1 -4 -3" {...sw(2)} />
      </g>
      {/* 갑자기 강림한 구름 기둥 사이의 모세 */}
      <g style={d(1800, reduce)}>
        <path d="M62 44 v-16" {...sw(1.6)} />
        <path d="M55 22 q0 -5 6 -5 q2.5 -3 6.5 -1.5 q5 -1 4.5 3 q3 1.5 0.5 4 q-4 2.5 -9 1.5 q-6 1.5 -8.5 -2 z" {...sw(2.4)} />
      </g>
      {/* 나병으로 하얗게 된 미리암 — 핵심 */}
      <g style={d(2600, reduce)} stroke="var(--paper-accent)">
        <circle cx="30" cy="36" r="2.9" {...sw(2.6)} />
        <path d="M27 35 q1.5 1 3 0 q1.5 1 3 0" {...sw(1.4)} />
      </g>
      {/* 진 밖에 이레 동안 갇힘 */}
      <g style={d(3200, reduce)}>
        <path d="M88 54 v-10 h12 v10" {...sw(1.6, 0.7)} />
        <circle cx="80" cy="47" r="1.8" {...sw(1.6, 0.7)} />
        <path d="M80 48.8 v3.2 M78.3 54 l1.7 -3.6 l1.7 3.6" {...sw(1.6, 0.7)} />
      </g>
      <Label x="62" y="16" at="2.1" reduce={reduce}>구름 기둥이 강림하다</Label>
      <Label x="30" y="28" at="2.9" reduce={reduce}>나병에 걸린 미리암</Label>
      <Label x="82" y="40" at="3.5" reduce={reduce}>진 밖에 갇힌 이레</Label>
    </g>
  )
}

// 가데스 정탐 (민 13-14)
function KadeshSpiesScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M84 44 q13 -8 26 -2" {...sw(1.1, 0.4)} />
      </g>
      {/* 포도 멘 두 정탐꾼 — 여호수아·갈렙 */}
      <g style={d(900, reduce)}>
        <path d="M34 40 h24" {...sw(2.2)} />
        <circle cx="44" cy="44" r="2.6" {...sw(2)} />
        <circle cx="47.5" cy="46.5" r="2.6" {...sw(2)} />
        <circle cx="41" cy="47" r="2.6" {...sw(2)} />
        <circle cx="44.5" cy="49.5" r="2.4" {...sw(2)} />
        <circle cx="34" cy="36.5" r="2.4" {...sw(2.2)} />
        <path d="M34 38.9 v7.6 M32 54 l2 -7.5 l2 7.5" {...sw(2.2)} />
        <circle cx="58" cy="36.5" r="2.4" {...sw(2.2)} />
        <path d="M58 38.9 v7.6 M56 54 l2 -7.5 l2 7.5" {...sw(2.2)} />
      </g>
      {/* 물러선 무리 — 두려움 */}
      <g style={d(2000, reduce)}>
        <circle cx="86" cy="44" r="2.2" {...sw(1.8)} />
        <path d="M86 46.2 v3.8 M84 54 l2 -4 l2 4 M84 45 l-3 2.5" {...sw(1.8)} />
        <circle cx="96" cy="45" r="2" {...sw(1.6, 0.85)} />
        <path d="M96 47 v3 M94.5 54 l1.5 -4 l1.5 4 M94 46 l-3 2.5" {...sw(1.6, 0.85)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="translate" from="0 0" to="7 0"
            begin="2.6s" dur="1.2s" fill="freeze" />
        )}
      </g>
      <Label x="46" y="30" at="1.4" reduce={reduce}>에스골 포도송이</Label>
      <Label x="92" y="35" at="2.7" reduce={reduce}>두려워한 무리</Label>
    </g>
  )
}

// 헤브론 정탐 (민 13:22-24)
function SpiesHebronScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M10 43 q12 -7 24 -2 M86 42 q12 -7 24 -2" {...sw(1.1, 0.4)} />
      </g>
      {/* 포도나무 골짜기 — 덩굴 + 대형 송이 */}
      <g style={d(900, reduce)}>
        <path d="M60 54 q-2 -10 -1 -18 M59 36 q-8 -2 -10 -8 q7 -2 10 3 q1 -7 7 -8 q4 3 2 8 q7 -2 9 4 q-4 6 -11 4 q-3 2 -7 -3" {...sw(2)} />
        <circle cx="70" cy="44" r="2.8" {...sw(2.6)} />
        <circle cx="74" cy="47" r="2.8" {...sw(2.6)} />
        <circle cx="67" cy="47.5" r="2.8" {...sw(2.6)} />
        <circle cx="71" cy="50.5" r="2.6" {...sw(2.6)} />
        <path d="M70 41.5 q0 -3 -2 -4.5" {...sw(1.8)} />
      </g>
      {/* 아낙 자손 — 원경 큰 그림자 실루엣 */}
      <g style={d(2000, reduce)}>
        <circle cx="20" cy="28" r="3.6" {...sw(1.4, 0.45)} />
        <path d="M20 31.6 v12 M16 54 l4 -10 l4 10 M14 37 q6 -3.5 12 0" {...sw(1.4, 0.45)} />
      </g>
      <Label x="72" y="34" at="1.4" reduce={reduce}>큰 포도송이</Label>
      <Label x="20" y="18" at="2.6" reduce={reduce}>아낙 자손</Label>
    </g>
  )
}

// 고라의 반역과 싹 난 지팡이 (민 16:1-17:8)
function KorahRebellionScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
      </g>
      {/* 고라와 무리 — 향로를 들고 맞섬 */}
      <g style={d(900, reduce)}>
        <circle cx="34" cy="34" r="2.4" {...sw(2.2)} />
        <path d="M34 36.4 v8.6 M32 50 l2 -6.5 l2 6.5 M36.5 39 l3 -1.5" {...sw(2.2)} />
        <ellipse cx="42" cy="36.5" rx="1.6" ry="0.8" {...sw(1.6)} />
        <circle cx="48" cy="35" r="2.2" {...sw(1.8, 0.85)} />
        <path d="M48 37.2 v7.8 M46 50 l2 -6 l2 6 M50.5 39.5 l3 -1.5" {...sw(1.8, 0.85)} />
      </g>
      {/* 갈라져 삼키는 땅 — 핵심 */}
      <g style={d(1900, reduce)}>
        <path d="M24 54 l4 7 l4 -4 l4 8 l4 -5 l4 8 l4 -5 l4 7 l4 -4" {...sw(2.8)} />
      </g>
      {!reduce && (
        <g style={d(2100, false)}>
          {/* 무리가 산 채로 빠져 들어감 */}
          <circle cx="34" cy="34" r="1" {...sw(1.6)}>
            <animateMotion path="M0 0 q1 10 0 20" begin="2.2s" dur="0.9s" fill="freeze" />
          </circle>
        </g>
      )}
      {/* 분향하던 이백오십 인을 사른 불 */}
      <g style={d(2800, reduce)} stroke="var(--paper-accent)">
        <path d="M40 32 q-2 -3 0 -6 M45 30.5 q-2 -4 0.5 -7" {...sw(1.8)} />
      </g>
      {/* 싹이 나고 살구 열매 맺은 아론의 지팡이 */}
      <g style={d(3400, reduce)}>
        <path d="M92 54 v-18" {...sw(2.6)} />
        <path d="M92 40 q-3 -2 -1 -5 M92 36 q3 -2 1.5 -5 M89.5 33 q1 1.2 3 0" {...sw(1.6)} />
        <circle cx="90" cy="32" r="0.9" {...sw(1.4)} />
        <circle cx="94" cy="31.5" r="0.9" {...sw(1.4)} />
      </g>
      <Label x="42" y="26" at="1.6" reduce={reduce}>고라의 무리</Label>
      <Label x="34" y="61" at="2.8" reduce={reduce} size="4.2">땅이 갈라져 삼키다</Label>
      <Label x="92" y="30" at="3.8" reduce={reduce}>싹 난 지팡이</Label>
    </g>
  )
}

// 므리바의 물 — 모세의 실수 (민 20:1-13)
function MeribahWaterScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
      </g>
      {/* 가데스에 묻힌 미리암 */}
      <g style={d(800, reduce)}>
        <path d="M14 54 q1 -3 4 -3 q3 0 4 3" {...sw(1.8)} />
      </g>
      {/* 반석 */}
      <g style={d(1700, reduce)}>
        <path d="M46 54 q-2 -9 4 -13 q6 -3 10 1 q5 3 2 7 q3 4 -2 6 q-4 3 -9 1 q-4 1 -5 -2 z" {...sw(2.2)} />
      </g>
      {/* 명령을 어기고 지팡이로 반석을 두 번 침 — 핵심 */}
      <g style={d(2400, reduce)} stroke="var(--paper-accent)">
        <circle cx="26" cy="36" r="2.7" {...sw(2.6)} />
        <path d="M26 38.7 v9.3 M23.5 54 l2.5 -7 l2.5 7" {...sw(2.6)} />
        <path d="M28 38 L44 45 M28 41 L44 47" {...sw(2.4)} />
      </g>
      {/* 반석에서 솟는 물 */}
      <g style={d(3100, reduce)}>
        <path d="M50 44 q1 5 -1 10 M54 42 q2 6 0 12" {...sw(2)} />
        <circle cx="64" cy="48" r="1.9" {...sw(1.8)} />
        <path d="M64 49.9 v3 M62 54 q0 -1.6 1 -2.4 M66.5 54 l-1.5 -2.4" {...sw(1.8)} />
      </g>
      <Label x="18" y="60" at="1.6" reduce={reduce}>미리암이 잠들다</Label>
      <Label x="26" y="28" at="2.9" reduce={reduce}>두 번 친 지팡이</Label>
      <Label x="60" y="61" at="3.8" reduce={reduce} size="4.2">모세와 아론에게 가나안이 금지되다</Label>
    </g>
  )
}

// 호르산에서 아론의 죽음 (민 20:22-29)
function AaronDeathHorScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M30 54 L60 12 L90 54" {...sw(2.2)} />
      </g>
      {/* 오르는 세 사람 — 모세, 아론, 엘르아살 */}
      <g style={d(900, reduce)}>
        <circle cx="50" cy="38" r="2.2" {...sw(1.9)} />
        <path d="M50 40.2 v6.8 M48 50 l2 -5 l2 5" {...sw(1.9)} />
        <circle cx="58" cy="32" r="2.3" {...sw(2)} />
        <path d="M58 34.3 v7.2 M56 47 l2 -5.5 l2 5.5" {...sw(2)} />
        <circle cx="66" cy="27" r="2" {...sw(1.7, 0.85)} />
        <path d="M66 29 v6.5 M64 41 l2 -5 l2 5" {...sw(1.7, 0.85)} />
      </g>
      {/* 벗겨져 엘르아살에게 옮겨지는 대제사장 옷 — 핵심 */}
      <g style={d(1900, reduce)}>
        <path d="M55 26 v-6 q0 -2 2.5 -2 h1 q2.5 0 2.5 2 v6 z" {...sw(2.6)} />
        <path d="M56 18 h3" {...sw(1.4)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="translate" from="0 0" to="8 -5"
            begin="2.1s" dur="1.1s" fill="freeze" calcMode="spline" keySplines="0.3 0 0.6 1" keyTimes="0;1" />
        )}
      </g>
      {/* 산꼭대기에 묻힌 아론 */}
      <g style={d(2800, reduce)} stroke="var(--paper-accent)">
        <path d="M54 16 q3 -4 6 -4 q3 0 6 4" {...sw(1.8)} />
      </g>
      {/* 삼십 일을 애곡하는 온 이스라엘 */}
      <g style={d(3400, reduce)}>
        <circle cx="16" cy="48" r="1.7" {...sw(1.5, 0.7)} />
        <path d="M16 49.7 v3 M14.5 54 l1.5 -3.3 l1.5 3.3" {...sw(1.5, 0.7)} />
        <circle cx="104" cy="48" r="1.7" {...sw(1.5, 0.7)} />
        <path d="M104 49.7 v3 M102.5 54 l1.5 -3.3 l1.5 3.3" {...sw(1.5, 0.7)} />
      </g>
      <Label x="66" y="16" at="2.3" reduce={reduce}>대제사장 옷을 넘겨받다</Label>
      <Label x="60" y="8" at="1.9" reduce={reduce}>호르산 정상</Label>
      <Label x="60" y="61" at="3.7" reduce={reduce} size="4.2">이스라엘이 삼십 일을 애곡하다</Label>
    </g>
  )
}

// 놋뱀을 든 장대 (민 21:4-9)
function BronzeSerpentScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M6 50 q16 -5 30 -1 q16 -5 30 0" {...sw(1.1, 0.4)} />
      </g>
      {/* 원망 중에 보내신 불뱀 */}
      <g style={d(800, reduce)} stroke="var(--paper-accent)">
        <path d="M18 52 q3 -3 6 0 q3 -3 6 0" {...sw(1.8)} />
        <path d="M70 51 q3 -3 6 0" {...sw(1.6, 0.85)} />
      </g>
      {/* 물려 쓰러진 백성 */}
      <g style={d(1600, reduce)}>
        <circle cx="28" cy="47" r="1.9" {...sw(1.7, 0.85)} />
        <path d="M28 48.9 l-6 3.5 M25.5 52.3 l4.5 -1.5" {...sw(1.7, 0.85)} />
      </g>
      {/* 모세 — 장대를 세우다 */}
      <g style={d(2400, reduce)}>
        <circle cx="52" cy="30" r="2.8" {...sw(2.5)} />
        <path d="M52 32.8 v10.2 M49 54 l3 -9 l3 9 M54.5 33 q3 -1 5 -3" {...sw(2.5)} />
        <path d="M58 44 v-24" {...sw(2.6)} />
      </g>
      {/* 놋뱀 — 핵심 */}
      <g style={d(3100, reduce)}>
        <path d="M58 20 q4 2 0 5 q-4 2 0 5 q4 2 0 5" {...sw(2.6)} />
      </g>
      {/* 바라보고 사는 자들 */}
      <g style={d(3800, reduce)}>
        <circle cx="80" cy="46" r="1.8" {...sw(1.6, 0.8)} />
        <path d="M80 47.8 v3.3 M78.3 54 l1.7 -3.7 l1.7 3.7 M81.5 47 q2 -3 3 -6" {...sw(1.6, 0.8)} />
      </g>
      <Label x="28" y="41" at="1.9" reduce={reduce}>불뱀에 물리다</Label>
      <Label x="58" y="16" at="3.4" reduce={reduce}>바라보면 사는 놋뱀</Label>
    </g>
  )
}

// 시혼과 옥을 격파한 요단 동편 (민 21:21-35)
function SihonOgScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M6 50 q14 -4 28 0 q14 -4 28 0" {...sw(1.1, 0.4)} />
      </g>
      {/* 헤스본 — 시혼이 통과를 거절하고 맞서 나오다 */}
      <g style={d(900, reduce)}>
        <path d="M28 54 V32 h18 V54" {...sw(1.9, 0.85)} />
        <path d="M31 54 V40 h5 V54 m6 0 V40 h5 V54" {...sw(1.3, 0.5)} />
      </g>
      {/* 야하스에서 쳐서 파하다 */}
      <g style={d(1900, reduce)}>
        <circle cx="14" cy="42" r="2.3" {...sw(2.1)} />
        <path d="M14 44.3 v7.7 M12 54 l2 -6 l2 6 M16.3 43 L24 38" {...sw(2.1)} />
      </g>
      {/* 아르논에서 얍복까지 — 점령한 땅의 경계 */}
      <g style={d(2700, reduce)} stroke="var(--paper-accent)">
        <path d="M12 49 h52" {...sw(1.6)} strokeDasharray="2.4 2.2" />
      </g>
      {/* 바산 왕 옥 — 에드레이에서 맞서다 */}
      <g style={d(3400, reduce)}>
        <path d="M76 54 V32 h18 V54" {...sw(1.9, 0.85)} />
        <path d="M79 54 V40 h5 V54 m6 0 V40 h5 V54" {...sw(1.3, 0.5)} />
      </g>
      {/* 옥마저 쳐서 한 사람도 남기지 않다 — 핵심 */}
      <g style={d(4200, reduce)}>
        <circle cx="62" cy="42" r="2.3" {...sw(2.1)} />
        <path d="M62 44.3 v7.7 M60 54 l2 -6 l2 6 M64.3 43 L72 38" {...sw(2.1)} />
      </g>
      <Label x="37" y="27" at="1.9" reduce={reduce}>헤스본의 시혼</Label>
      <Label x="38" y="45" at="2.8" reduce={reduce}>아르논에서 얍복까지</Label>
      <Label x="85" y="27" at="3.7" reduce={reduce}>바산 왕 옥</Label>
    </g>
  )
}

// 브올의 바알 배교 (민 25:1-9)
function BaalPeorScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
      </g>
      {/* 바알브올 제단 — 절하는 백성 */}
      <g style={d(900, reduce)}>
        <path d="M20 54 v-10 h8 v10" {...sw(2.2)} />
        <circle cx="34" cy="48" r="1.9" {...sw(1.8, 0.85)} />
        <path d="M34 49.9 q-2 1.5 -2 3.5 M34 49.9 q2 1.5 3 3.2" {...sw(1.8, 0.85)} />
        <circle cx="42" cy="49" r="1.7" {...sw(1.6, 0.7)} />
        <path d="M42 50.7 q-1.8 1.4 -2 3.3" {...sw(1.6, 0.7)} />
      </g>
      {/* 회막문에서 우는 회중 */}
      <g style={d(1900, reduce)}>
        <path d="M62 54 v-16 h14 v16" {...sw(2, 0.85)} />
        <circle cx="58" cy="48" r="1.7" {...sw(1.5, 0.65)} />
        <path d="M58 49.7 v3.4 M56.5 54 l1.5 -3.3" {...sw(1.5, 0.65)} />
      </g>
      {/* 비느하스 — 창을 들고 뛰어가다: 핵심 */}
      <g style={d(2800, reduce)}>
        <circle cx="86" cy="40" r="2.6" {...sw(2.5)} />
        <path d="M86 42.6 v9 M83.5 54 l2.5 -7 l2.5 7" {...sw(2.5)} />
        <path d="M88.5 43 L98 35" {...sw(2.6)} />
      </g>
      {/* 창에 찔려 그치는 염병 */}
      <g style={d(3600, reduce)} stroke="var(--paper-accent)">
        <path d="M98 44 l4 -4 m-4 0 l4 4" {...sw(2)} />
      </g>
      <Label x="34" y="42" at="1.9" reduce={reduce}>바알브올에게 절하다</Label>
      <Label x="86" y="34" at="2.9" reduce={reduce}>비느하스의 창</Label>
      <Label x="60" y="61" at="3.9" reduce={reduce} size="4.2">이만 사천 명이 죽은 뒤에 염병이 그치다</Label>
    </g>
  )
}

// 모압 평지 (민 36:13)
function PlainsMoabScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        {/* 요단강 */}
        <path d="M70 54 q4 -12 0 -22 q-3 -8 2 -18" {...sw(2)} />
        <path d="M75 54 q4 -12 0 -22" {...sw(1.3, 0.5)} />
        {/* 건너편 가나안 산지 */}
        <path d="M84 34 q10 -9 20 -3 M92 26 q8 -7 18 -3" {...sw(1.2, 0.45)} />
      </g>
      {/* 진영 장막들 */}
      <g style={d(1000, reduce)}>
        <path d="M14 54 l8 -11 l8 11 M19 54 l3 -4.5 l3 4.5" {...sw(2.2)} />
        <path d="M40 54 l6.5 -9 l6.5 9" {...sw(1.9)} />
        <path d="M56 54 l5 -7 l5 7" {...sw(1.6, 0.75)} />
        <path d="M30 54 l4 -6 l4 6" {...sw(1.5, 0.6)} />
      </g>
      {/* 모세의 설교 — 두루마리 */}
      <g style={d(2200, reduce)}>
        <circle cx="52" cy="32" r="2.6" {...sw(2.4)} />
        <path d="M52 34.6 v7.4 M50 45 h4" {...sw(2.4)} />
        <path d="M54.5 36 q4 -1.5 6 -4 M46 37 h4 q1.5 0 1.5 1.5" {...sw(1.8)} />
      </g>
      <Label x="30" y="34" at="1.5" reduce={reduce}>모압 평지 진영</Label>
      <Label x="99" y="46" at="0.9" reduce={reduce}>요단 건너 가나안</Label>
    </g>
  )
}

// 율법 낭독과 여호수아 위임 (신 31:7-13)
function LawReadingCommissionScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M8 48 q14 -6 28 0 M84 48 q14 -6 28 0" {...sw(1.1, 0.4)} />
      </g>
      {/* 모세 — 여호수아를 불러 부탁함 */}
      <g style={d(900, reduce)}>
        <circle cx="38" cy="32" r="2.8" {...sw(2.6)} />
        <path d="M38 34.8 v10.2 M35 54 l3 -9 l3 9 M40.6 35 q3 -1.5 5 -3.5" {...sw(2.6)} />
      </g>
      {/* 여호수아 — 강하고 담대하라는 위임을 받다 */}
      <g style={d(1800, reduce)}>
        <circle cx="54" cy="32" r="2.6" {...sw(2.4)} />
        <path d="M54 34.6 v9.4 M51.5 54 l2.5 -8 l2.5 8 M51.4 35 q-3 -1.5 -5 -3.5" {...sw(2.4)} />
      </g>
      {/* 써서 넘기는 율법책 — 핵심 */}
      <g style={d(2700, reduce)} stroke="var(--paper-accent)">
        <path d="M43 38 h8 v6 h-8 z M45 40 h4 M45 42 h4" {...sw(2.2)} />
      </g>
      {/* 언약궤를 메는 제사장들과 장로들에게 맡김 */}
      <g style={d(3500, reduce)}>
        <path d="M76 48 h20" {...sw(1.6, 0.75)} />
        <path d="M80 48 v-5 h8 v5 M79 43 h10" {...sw(2, 0.85)} />
        <circle cx="98" cy="41" r="1.8" {...sw(1.5, 0.65)} />
        <path d="M98 42.8 v6 M96.3 54 l1.7 -5.4 l1.7 5.4" {...sw(1.5, 0.65)} />
      </g>
      <Label x="38" y="24" at="1.8" reduce={reduce}>모세</Label>
      <Label x="54" y="24" at="2.7" reduce={reduce}>여호수아</Label>
      <Label x="60" y="61" at="3.9" reduce={reduce} size="4.2">칠 년마다 온 백성에게 낭독하라</Label>
    </g>
  )
}

// 느보산 조망 (신 34:1-4)
function ViewsJerichoScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M6 54 L34 22 L52 34" {...sw(2.2)} />
        {/* 펼쳐진 약속의 땅 — 겹겹 지평 */}
        <path d="M52 42 q18 -6 36 -3 q14 -3 26 0" {...sw(1.3, 0.5)} />
        <path d="M58 48 q20 -5 38 -2 q10 -2 18 0" {...sw(1.1, 0.35)} />
        <path d="M76 34 q12 -6 24 -3" {...sw(1.1, 0.3)} />
      </g>
      {/* 모세 — 정상에서 바라봄 */}
      <g style={d(1400, reduce)}>
        <circle cx="34" cy="14" r="2.6" {...sw(2.5)} />
        <path d="M34 16.6 v6.4 M32 28 l2 -5 l2 5 M36.2 18.5 q3.5 -1 5.5 -3" {...sw(2.5)} />
        <path d="M31.5 19 l-3 8" {...sw(1.8)} />
      </g>
      {/* 여리고 표시 — 강조 */}
      <g style={d(reduce ? 0 : 2600, reduce)} stroke="var(--paper-accent)">
        <path d="M88 40 h8 M90 40 v-3 h4 v3" {...sw(1.6)} />
        <path d="M92 32 v-2 m0 -2.5 v-2" {...sw(1.2)} />
      </g>
      <Label x="26" y="8" at="1.9" reduce={reduce}>느보산의 모세</Label>
      <Label x="92" y="49" at="3" reduce={reduce}>여리고</Label>
    </g>
  )
}

// 모세의 죽음 (신 34:5-8)
function DeathMoabScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M6 50 q16 -7 30 -3 M80 48 q14 -6 28 -3" {...sw(1.2, 0.45)} />
        <path d="M20 12 v2.4 m-1.2 -1.2 h2.4 M96 9 v2.4 m-1.2 -1.2 h2.4 M108 18 v2 m-1 -1 h2" {...sw(1.2, 0.6)} />
      </g>
      {/* 홀로 꽂힌 지팡이 — 핵심 */}
      <g style={d(1200, reduce)}>
        <path d="M60 54 l1.5 -22 q0 -3 3 -3.5" {...sw(2.8)} />
      </g>
      {/* 골짜기 — 아무도 모르는 곳 */}
      <g style={d(2200, reduce)}>
        <path d="M42 54 q8 -5 18 -4 q10 -1 18 4" {...sw(1.4, 0.55)} />
      </g>
      <Label x="62" y="24" at="1.6" reduce={reduce}>모세의 지팡이</Label>
      <Label x="60" y="61" at="2.6" reduce={reduce} size="4.2">아무도 그 묻힌 곳을 알지 못하더라</Label>
    </g>
  )
}

// 여호수아 위임 (수 1:1-9)
function DivineCommissionScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M84 44 q13 -8 26 -2" {...sw(1.1, 0.4)} />
      </g>
      {/* 여호수아 — 주역: 칼 짚고 곧게 */}
      <g style={d(1000, reduce)}>
        <circle cx="56" cy="30" r="3.1" {...sw(2.6)} />
        <path d="M56 33.1 v12.4 M52.5 54 l3.5 -8 l3.5 8" {...sw(2.6)} />
        <path d="M56 36 q-4 1 -5.5 4.5 M56 36 q4 1 5.5 4.5" {...sw(2.3)} />
        <path d="M62 41 v12 M60 42.5 h4" {...sw(2.2)} />
        <path d="M54 40 q2 1.2 4 0" {...sw(1.3, 0.6)} />
      </g>
      {/* 위임의 빛 */}
      <g style={d(reduce ? 0 : 2200, reduce)} stroke="var(--paper-accent)">
        <path d="M56 20 v-6 M48 22 l-3.5 -3.5 M64 22 l3.5 -3.5 M51 20 l-2 -3 M61 20 l2 -3" {...sw(1.6)} />
      </g>
      <Label x="56" y="60" at="1.5" reduce={reduce}>여호수아</Label>
      <Label x="56" y="8" at="2.8" reduce={reduce} size="4.2">강하고 담대하라</Label>
    </g>
  )
}

// 라합과 정탐꾼 (수 2)
function RahabSpiesScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        {/* 여리고 성벽 + 창문 */}
        <path d="M46 54 V20 h30 V54" {...sw(2.4)} />
        <path d="M46 28 h30 M46 38 h30 M46 47 h30" {...sw(1.2, 0.45)} />
        <path d="M56 34 v-4 h8 v4 z" {...sw(2)} />
      </g>
      {/* 붉은 줄 — 핵심: 창에서 내려옴 */}
      <g style={d(1600, reduce)} stroke="var(--paper-accent)">
        <path d="M60 34 v20" {...sw(2.6)}>
          {!reduce && (
            <animate attributeName="stroke-dashoffset" from="1" to="0" begin="1.8s" dur="0.9s" fill="freeze" />
          )}
        </path>
        <path d="M58.5 42 q1.5 1.6 3 0" {...sw(1.6)} />
      </g>
      {/* 내려가는 정탐꾼 둘 */}
      <g style={d(2600, reduce)}>
        <circle cx="30" cy="46" r="2.2" {...sw(2)} />
        <path d="M30 48.2 v3 M28 54 l2 -3 l2 3 M32 49 l3.5 2" {...sw(2)} />
        <circle cx="20" cy="47.5" r="2" {...sw(1.8, 0.9)} />
        <path d="M20 49.5 v2 M18.3 54 l1.7 -2.6 l1.7 2.6" {...sw(1.8, 0.9)} />
      </g>
      <Label x="61" y="16" at="1" reduce={reduce}>라합의 창</Label>
      <Label x="90" y="40" at="2" reduce={reduce}>붉은 줄</Label>
      <Label x="25" y="38" at="3" reduce={reduce}>정탐꾼</Label>
    </g>
  )
}

// 요단 도하 (수 3:14-17)
function JordanCrossingScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
      </g>
      {/* 갈라진 강 — 물결이 양쪽으로 물러남 */}
      <g transform={reduce ? 'translate(-9 0)' : undefined} style={d(900, reduce)}>
        <path d="M8 46 q6 -2.5 12 0 q6 -2.5 12 0 M12 50 q6 -2.5 12 0 q5 -2 10 0" {...sw(2)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="translate" from="0 0" to="-9 0"
            begin="2.2s" dur="1.4s" fill="freeze" calcMode="spline" keySplines="0.3 0 0.6 1" keyTimes="0;1" />
        )}
      </g>
      <g transform={reduce ? 'translate(9 0)' : undefined} style={d(900, reduce)}>
        <path d="M78 46 q6 -2.5 12 0 q6 -2.5 12 0 M82 50 q6 -2.5 12 0 q5 -2 10 0" {...sw(2)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="translate" from="0 0" to="9 0"
            begin="2.2s" dur="1.4s" fill="freeze" calcMode="spline" keySplines="0.3 0 0.6 1" keyTimes="0;1" />
        )}
      </g>
      {/* 법궤 행렬 — 마른 강바닥 한가운데 */}
      <g style={d(2400, reduce)}>
        <path d="M48 43 h24" {...sw(2)} />
        <path d="M54 43 v-6 h12 v6 M52 37 h16" {...sw(2.6)} />
        <path d="M57 36.5 q-2.5 -4 1.5 -5 M63 36.5 q2.5 -4 -1.5 -5" {...sw(1.4)} />
        <circle cx="51" cy="40" r="2.2" {...sw(1.9)} />
        <path d="M51 42.2 v6 M49 54 l2 -6 l2 6" {...sw(1.9)} />
        <circle cx="69" cy="40" r="2.2" {...sw(1.9)} />
        <path d="M69 42.2 v6 M67 54 l2 -6 l2 6" {...sw(1.9)} />
      </g>
      <Label x="60" y="27" at="2.7" reduce={reduce}>법궤</Label>
      <Label x="20" y="38" at="1.4" reduce={reduce}>끊어진 강물</Label>
    </g>
  )
}

// 길갈 열두 돌 (수 4:19-5:12)
function GilgalCampScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M84 44 q13 -8 26 -2" {...sw(1.1, 0.4)} />
      </g>
      {/* 열두 돌 — 층층이 세워짐(단계 draw) */}
      <g style={d(900, reduce)}>
        <path d="M46 54 q0 -3.5 4 -3.5 q4 0 4 3.5 M56 54 q0 -3.5 4 -3.5 q4 0 4 3.5 M66 54 q0 -3.5 4 -3.5 q4 0 4 3.5 M40 54 q0 -3 3.5 -3 q3.5 0 3.5 3" {...sw(2)} />
      </g>
      <g style={d(1700, reduce)}>
        <path d="M50 50.5 q0 -3.2 3.8 -3.2 q3.8 0 3.8 3.2 M60 50.5 q0 -3.2 3.8 -3.2 q3.8 0 3.8 3.2 M70 50.5 q0 -3 3.5 -3 q3.5 0 3.5 3" {...sw(2.1)} />
      </g>
      <g style={d(2400, reduce)}>
        <path d="M54 47.2 q0 -3 3.6 -3 q3.6 0 3.6 3 M63.5 47.2 q0 -3 3.6 -3 q3.6 0 3.6 3" {...sw(2.2)} />
      </g>
      <g style={d(3000, reduce)}>
        <path d="M58 44.2 q0 -3 3.5 -3 q3.5 0 3.5 3 M62 41 q0 -2.6 3 -2.6 q3 0 3 2.6" {...sw(2.3)} />
      </g>
      {/* 진영 + 유월절 불 */}
      <g style={d(3600, reduce)}>
        <path d="M18 54 l6 -8.5 l6 8.5" {...sw(1.7, 0.8)} />
        <path d="M94 51 q-1.6 -3.2 0 -5.5 q1.6 2.5 0 5.5" {...sw(2)} stroke="var(--paper-accent)" />
      </g>
      <Label x="62" y="33" at="3.4" reduce={reduce}>요단의 열두 돌</Label>
      <Label x="24" y="37" at="3.8" reduce={reduce}>길갈 진영</Label>
    </g>
  )
}

// 여리고 함락 (수 6:20)
function JerichoConquestScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
      </g>
      {/* 여리고 성벽 — 무너짐 */}
      <g style={d(800, reduce)}>
        <path d="M44 54 V30 h32 V54" {...sw(2.4)} />
        <path d="M48 30 v-3 h5 v3 m5 0 v-3 h5 v3 m5 0 v-3 h5 v3" {...sw(1.6)} />
        <path d="M48 38 h6 m6 0 h6 m6 0 h6 M50 46 h6 m8 0 h6" {...sw(1.2, 0.45)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="rotate"
            values="0 60 54; 1.5 60 54; -1.5 60 54; 5 60 54" keyTimes="0;0.3;0.6;1"
            begin="3.4s" dur="0.6s" fill="freeze" />
        )}
      </g>
      {/* 무너지는 조각 — 낙하 */}
      {!reduce && (
        <g style={d(3400, false)}>
          <path d="M50 28 l4 1.5 l-1 3 l-4 -1.5 z" {...sw(1.8)}>
            <animateMotion path="M0 0 q-3 10 -5 22" begin="3.6s" dur="0.55s" fill="freeze" />
          </path>
          <path d="M68 27 l4 1 l-0.8 3 l-4 -1 z" {...sw(1.8)}>
            <animateMotion path="M0 0 q4 11 6 23" begin="3.7s" dur="0.55s" fill="freeze" />
          </path>
        </g>
      )}
      {/* 나팔 행렬 */}
      <g style={d(1800, reduce)}>
        <circle cx="20" cy="45" r="2.2" {...sw(2)} />
        <path d="M20 47.2 v3.3 M18 54 l2 -3.5 l2 3.5 M22 44 l5 -2 M27 42 l3 -1 q1.5 -0.5 1.5 1" {...sw(2)} />
        <circle cx="32" cy="47" r="2" {...sw(1.8, 0.9)} />
        <path d="M32 49 v2.2 M30.3 54 l1.7 -2.8 l1.7 2.8" {...sw(1.8, 0.9)} />
      </g>
      <g style={d(reduce ? 0 : 3000, reduce)} stroke="var(--paper-accent)">
        <path d="M32 38 q2 -1.5 4 0 M33 35 q2.5 -2 5 0" {...sw(1.3)} />
      </g>
      <Label x="60" y="22" at="1.3" reduce={reduce}>여리고 성벽</Label>
      <Label x="24" y="35" at="2.3" reduce={reduce}>나팔 행렬</Label>
    </g>
  )
}

// 아간의 범죄와 아골 골짜기 (수 7:1-26)
function AchanSinScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
      </g>
      {/* 감춘 전리품 — 장막 땅속에 묻힌 외투와 은금 */}
      <g style={d(900, reduce)} stroke="var(--paper-accent)">
        <path d="M14 54 v-9 h14 v9" {...sw(1.8)} />
        <path d="M19 51 h4 v2.5 h-4 z" {...sw(1.6)} />
      </g>
      {/* 아이 성 앞에서 패퇴 — 도망치는 이스라엘 */}
      <g style={d(1900, reduce)}>
        <circle cx="42" cy="42" r="2.1" {...sw(1.9)} />
        <path d="M42 44.1 v6.9 M40 54 l2 -5.5 l2 5.5 M39.7 43 l-6 3" {...sw(1.9)} />
        <circle cx="53" cy="41.5" r="1.8" {...sw(1.7, 0.8)} />
        <path d="M53 43.3 v5.7 M51.3 54 l1.7 -4.6 l1.7 4.6 M51 42.5 l-5.5 2.7" {...sw(1.7, 0.8)} />
      </g>
      {/* 여호와의 궤 앞에 옷 찢고 엎드린 여호수아 */}
      <g style={d(2900, reduce)}>
        <path d="M70 51 h12" {...sw(1.6, 0.75)} />
        <path d="M73 51 v-5 h6 v5 M72 46 h8" {...sw(2, 0.85)} />
        <circle cx="60" cy="52.3" r="1.6" {...sw(2.2)} />
        <path d="M61.5 52.8 q3.5 -0.8 6 0.8" {...sw(2.2)} />
      </g>
      {/* 제비뽑혀 드러난 아간과 아골 골짜기의 돌무더기 — 핵심 */}
      <g style={d(3800, reduce)}>
        <circle cx="94" cy="36" r="2.4" {...sw(2.4)} />
        <path d="M94 38.4 v9.6 M91.5 54 l2.5 -6 l2.5 6" {...sw(2.4)} />
        <path d="M88 54 q2 -5 8 -5 q6 0 8 5" {...sw(2.6)} />
      </g>
      <Label x="21" y="42" at="1.9" reduce={reduce}>땅에 감춘 은금</Label>
      <Label x="48" y="35" at="2.9" reduce={reduce}>아이 성 앞에서 패퇴하다</Label>
      <Label x="66" y="43" at="3.6" reduce={reduce}>옷 찢고 엎드린 여호수아</Label>
      <Label x="94" y="60" at="4.4" reduce={reduce} size="4.2">아골 골짜기에서 돌로 치다</Label>
    </g>
  )
}

// 아이 성 전투 (수 8:18-29)
function AiConquestScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M10 43 q12 -7 24 -2" {...sw(1.1, 0.4)} />
      </g>
      {/* 아이 성 — 연기 오름 */}
      <g style={d(900, reduce)}>
        <path d="M66 54 v-14 h26 v14 M70 40 v-4 h6 v4 m6 0 v-4 h6 v4" {...sw(2.2)} />
        <path d="M70 47 h5 m7 0 h5" {...sw(1.2, 0.45)} />
        <path d="M78 32 q-4 -5 0 -9 q4 -4 1 -8 M84 33 q-3 -4 0 -8" {...sw(1.6, 0.75)} />
      </g>
      {/* 내민 단창 — 여호수아의 신호 */}
      <g style={d(1900, reduce)}>
        <circle cx="26" cy="33" r="2.6" {...sw(2.4)} />
        <path d="M26 35.6 v9.4 M23.5 54 l2.5 -7 l2.5 7" {...sw(2.4)} />
        <path d="M28.5 37 L44 30 M44 30 l-3.5 0.5 m3.5 -0.5 l-1 3" {...sw(2.6)} />
      </g>
      {/* 매복 화살표 — 뒤에서 돌아 들어감 */}
      <g style={d(2800, reduce)}>
        <path d="M38 50 q26 6 54 0 q6 -2 6 -8" {...sw(1.4, 0.6)} strokeDasharray="3 2.4" />
        <path d="M98 44 l0 -3.5 m0 3.5 l-3 -1.5" {...sw(1.4, 0.7)} />
      </g>
      <Label x="26" y="24" at="2.2" reduce={reduce}>여호수아</Label>
      <Label x="79" y="60" at="1.2" reduce={reduce}>아이 성</Label>
      <Label x="56" y="46" at="3.1" reduce={reduce} size="4.2">매복</Label>
    </g>
  )
}

// 에발산 언약 (수 8:30-35)
function EbalCovenantScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M6 54 L36 26 L58 40 M64 40 L88 24 L114 44" {...sw(1.6, 0.6)} />
      </g>
      {/* 제단 + 큰 율법 돌판 — 핵심 */}
      <g style={d(1000, reduce)}>
        <path d="M28 54 v-6 h14 v6 M26 48 h18" {...sw(2.2)} />
        <path d="M34 44.5 q-2 -3.5 0 -6.5" {...sw(2)} />
      </g>
      <g style={d(1800, reduce)}>
        <path d="M56 54 v-20 q0 -4 4 -4 h8 q4 0 4 4 v20" {...sw(2.6)} />
        <path d="M60 36 h8 M60 40 h8 M60 44 h6 M60 48 h8" {...sw(1.3)} />
      </g>
      {/* 회중 — 양쪽 산 아래 */}
      <g style={d(2800, reduce)}>
        <circle cx="88" cy="47" r="1.9" {...sw(1.7, 0.85)} />
        <path d="M88 48.9 v2.6 M86.5 54 l1.5 -2.8 l1.5 2.8" {...sw(1.7, 0.85)} />
        <circle cx="96" cy="48" r="1.8" {...sw(1.6, 0.75)} />
        <path d="M96 49.8 v2 M94.6 54 l1.4 -2.4 l1.4 2.4" {...sw(1.6, 0.75)} />
        <circle cx="16" cy="48.5" r="1.8" {...sw(1.6, 0.75)} />
        <path d="M16 50.3 v1.6 M14.6 54 l1.4 -2.2 l1.4 2.2" {...sw(1.6, 0.75)} />
      </g>
      <Label x="64" y="25" at="2.2" reduce={reduce}>돌에 새긴 율법</Label>
      <Label x="34" y="35" at="1.4" reduce={reduce}>에발산 제단</Label>
    </g>
  )
}

// 기브온 전투 (수 10:1-14)
function GibeonAllianceScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M70 48 q14 -8 28 -2 M14 46 q10 -6 20 -1" {...sw(1.1, 0.4)} />
      </g>
      {/* 해와 달 — 멈춰선 하늘 */}
      <g style={d(800, reduce)}>
        <circle cx="98" cy="13" r="5" {...sw(1.8)} />
        <path d="M98 5 v-2.4 M106 13 h2.4 M92.5 6.5 l-1.7 -1.7 M103.5 6.5 l1.7 -1.7" {...sw(1.3, 0.6)} />
        <path d="M18 12 a5 5 0 1 1 -3 -8.6 a6.5 6.5 0 0 0 3 8.6" {...sw(1.5, 0.6)} />
      </g>
      {/* 여호수아 — 핵심: 해를 향해 명함 */}
      <g style={d(1800, reduce)}>
        <circle cx="46" cy="30" r="3" {...sw(2.6)} />
        <path d="M46 33 v12.5 M42.5 54 l3.5 -8.5 l3.5 8.5" {...sw(2.6)} />
        <g transform={reduce ? undefined : 'rotate(40 46 33)'}>
          <path d="M46 33 l14 -12" {...sw(2.4)} />
          {!reduce && (
            <animateTransform attributeName="transform" type="rotate" from="40 46 33" to="0 46 33"
              begin="2.3s" dur="0.5s" fill="freeze" calcMode="spline" keySplines="0.3 0 0.6 1" keyTimes="0;1" />
          )}
        </g>
        <path d="M42.5 36 q3 1.6 5 0" {...sw(1.3, 0.6)} />
      </g>
      {/* 흩어지는 다섯 왕 무리 — 원경 */}
      <g style={d(2800, reduce)}>
        <circle cx="88" cy="42" r="1.8" {...sw(1.5, 0.7)} />
        <path d="M88 43.8 v3.2 M86.5 54 l1.5 -3.6 l1.5 3.6" {...sw(1.5, 0.7)} />
        <circle cx="94" cy="44" r="1.6" {...sw(1.4, 0.6)} />
        <path d="M94 45.6 v2.8 M92.7 54 l1.3 -3.4 l1.3 3.4" {...sw(1.4, 0.6)} />
      </g>
      <Label x="46" y="24" at="2.4" reduce={reduce}>여호수아</Label>
      <Label x="98" y="24" at="1.2" reduce={reduce}>멈춰 선 해</Label>
    </g>
  )
}

// 남부·북부 연합군 격파 — 하솔 (수 10:16-11:23)
function SouthernNorthernCampaignScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M6 48 q14 -6 28 0" {...sw(1.1, 0.4)} />
      </g>
      {/* 막게다 굴 — 다섯 왕이 숨어 돌로 막히다 */}
      <g style={d(900, reduce)}>
        <path d="M16 54 q0 -8 6 -10 q6 -2 8 4" {...sw(2)} />
        <circle cx="24" cy="52" r="2.4" {...sw(2.2)} />
      </g>
      {/* 남부 성읍들 — 립나·라기스·에글론·헤브론·드빌 */}
      <g style={d(1900, reduce)}>
        <path d="M40 54 v-6 h4 v6 m4 0 v-8 h4 v8 m4 0 v-5 h4 v5 m4 0 v-7 h4 v7 m4 0 v-6 h4 v6" {...sw(1.7, 0.8)} />
      </g>
      {/* 메롬 물가로 급습 — 북부 연합군 */}
      <g style={d(2900, reduce)}>
        <path d="M78 51 q6 -2.5 12 0" {...sw(1.4, 0.6)} />
        <circle cx="82" cy="42" r="2" {...sw(1.9)} />
        <path d="M82 44 v6.5 M80.2 54 l1.8 -5.6 l1.8 5.6 M84 43 l4 -3" {...sw(1.9)} />
      </g>
      {/* 불타는 하솔 — 핵심 */}
      <g style={d(3900, reduce)}>
        <path d="M94 54 v-14 h18 v14" {...sw(2.4)} />
        <path d="M98 40 q-3 -4 0 -8 q3 -3 1 -6 M104 40 q-2 -4 1 -7 M110 40 q-3 -4 0 -7" {...sw(2, 0.85)} stroke="var(--paper-accent)" />
      </g>
      <Label x="24" y="44" at="1.9" reduce={reduce}>막게다 굴의 다섯 왕</Label>
      <Label x="58" y="35" at="2.8" reduce={reduce}>립나·라기스·에글론·헤브론·드빌</Label>
      <Label x="104" y="34" at="4" reduce={reduce}>불탄 하솔</Label>
    </g>
  )
}

// 갈렙의 헤브론 분배 요구 (수 14:6-15)
function CalebHebronScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M6 48 q14 -6 28 0" {...sw(1.1, 0.4)} />
      </g>
      {/* 길갈 진영 — 유다 자손과 함께 나아오다 */}
      <g style={d(900, reduce)}>
        <path d="M12 54 l6 -8.5 l6 8.5" {...sw(1.4, 0.6)} />
      </g>
      {/* 팔십오 세에도 강건한 갈렙 — 주역 */}
      <g style={d(1900, reduce)}>
        <circle cx="42" cy="34" r="2.7" {...sw(2.5)} />
        <path d="M42 36.7 v9.3 M39.5 54 l2.5 -7 l2.5 7 M44.5 37 q3 -1 5 -2.5" {...sw(2.5)} />
      </g>
      {/* 여호수아 — 축복하여 헤브론을 넘겨줌 */}
      <g style={d(2800, reduce)}>
        <circle cx="58" cy="33" r="2.6" {...sw(2.3)} />
        <path d="M58 35.6 v9.4 M55.5 54 l2.5 -7 l2.5 7 M55.5 36 q-3 -1 -5 -2.5" {...sw(2.3)} />
      </g>
      {/* 아낙 사람들의 옛 그림자 — 45년 전 두려움의 잔영 */}
      <g style={d(3700, reduce)}>
        <circle cx="90" cy="26" r="3.6" {...sw(1.4, 0.35)} />
        <path d="M90 29.6 v12 M86 54 l4 -10 l4 10 M84 35 q6 -3.5 12 0" {...sw(1.4, 0.35)} />
      </g>
      {/* 유업으로 확정된 헤브론 — 핵심 */}
      <g style={d(4400, reduce)} stroke="var(--paper-accent)">
        <path d="M78 54 v-16 h20 v16" {...sw(2.4)} />
        <path d="M82 54 v-9 h5 v9 m5 0 v-7 h5 v7" {...sw(1.5, 0.7)} />
      </g>
      <Label x="42" y="26" at="2.2" reduce={reduce}>강건한 갈렙</Label>
      <Label x="58" y="25" at="3.1" reduce={reduce}>여호수아의 축복</Label>
      <Label x="88" y="60" at="4.7" reduce={reduce} size="4.2">기럇 아르바가 갈렙의 헤브론이 되다</Label>
    </g>
  )
}

// 실로 회막 (수 18:1-10)
function ShilohTabernacleScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M8 46 q14 -8 28 -1 M84 45 q14 -8 28 -1" {...sw(1.1, 0.4)} />
      </g>
      {/* 회막 — 핵심 */}
      <g style={d(900, reduce)}>
        <path d="M46 54 v-20 h28 v20 M46 34 l14 -6 l14 6" {...sw(2.6)} />
        <path d="M52 54 v-14 h16 v14" {...sw(1.6, 0.75)} />
        <path d="M50 40 h20 M50 45 h20 M50 50 h20" {...sw(1.2, 0.5)} />
      </g>
      {/* 제비뽑기 — 지파별 분배 */}
      <g style={d(1800, reduce)}>
        <circle cx="24" cy="38" r="2.4" {...sw(2.2)} />
        <path d="M24 40.4 v7.6 M21.5 54 l2.5 -6 l2.5 6 M26.5 42 q2 -1 3 -3" {...sw(2.2)} />
        <ellipse cx="30" cy="48.5" rx="3.2" ry="1.4" {...sw(1.6)} />
        <path d="M28.5 40 l1 1.5 l-1 1.5" {...sw(1.4)}>
          {!reduce && <animateMotion path="M0 0 q1 5 1.5 8.5" begin="2.4s" dur="0.6s" fill="freeze" />}
        </path>
      </g>
      {/* 지파 경계선 — 갈라진 기업 */}
      <g style={d(2800, reduce)}>
        <path d="M60 54 v-14 M60 40 l-10 -4 M60 40 l12 -3 M60 40 l6 6" {...sw(1.3, 0.55)} strokeDasharray="2.2 2" />
      </g>
      <Label x="60" y="30" at="2" reduce={reduce}>실로의 회막</Label>
      <Label x="26" y="32" at="3" reduce={reduce}>제비뽑기</Label>
    </g>
  )
}

// 세겜 언약 갱신 (수 24:1-27)
function ShechemCovenantScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M8 47 q12 -7 24 -1 M88 46 q12 -7 24 -1" {...sw(1.1, 0.4)} />
      </g>
      {/* 상수리나무 — 세겜의 언약 나무 */}
      <g style={d(900, reduce)}>
        <path d="M56 54 v-16" {...sw(2.2)} />
        <path d="M48 38 q0 -8 8 -9 q3 -5 10 -3 q7 -1 8 6 q5 1 3 6 q-4 4 -10 3 q-9 3 -14 -1 q-5 1 -5 -2 z" {...sw(1.8)} />
      </g>
      {/* 증거의 돌 */}
      <g style={d(1700, reduce)}>
        <path d="M40 54 v-11 q0 -2.5 2.5 -2.5 h2 q2.5 0 2.5 2.5 v11 z" {...sw(2.6)} />
      </g>
      {/* 새겨진 증언 — 강조색 */}
      <g style={d(reduce ? 0 : 2200, reduce)} stroke="var(--paper-accent)">
        <path d="M41.5 44.5 h4 m-4 3 h4" {...sw(1.3)} />
      </g>
      {/* 여호수아 + 응답하는 회중 */}
      <g style={d(2800, reduce)}>
        <circle cx="26" cy="36" r="2.6" {...sw(2.4)} />
        <path d="M26 38.6 v9.4 M23.5 54 l2.5 -7 l2.5 7 M28.5 40 q2.5 -1 3.5 -3" {...sw(2.4)} />
        <circle cx="88" cy="40" r="1.9" {...sw(1.7, 0.8)} />
        <path d="M88 41.9 v6.4 M86.1 54 l1.9 -5.7 l1.9 5.7 M89.5 42 l2.5 -2" {...sw(1.7, 0.8)} />
        <circle cx="96" cy="41.5" r="1.8" {...sw(1.6, 0.7)} />
        <path d="M96 43.3 v5.7 M94.2 54 l1.8 -5 l1.8 5 M97.5 43 l2 -1.7" {...sw(1.6, 0.7)} />
      </g>
      <Label x="60" y="30" at="1.9" reduce={reduce}>세겜의 상수리나무</Label>
      <Label x="44" y="40" at="2.3" reduce={reduce}>증거의 돌</Label>
    </g>
  )
}

// 여호수아의 죽음 (수 24:29-31)
function FarewellDeathScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M8 50 q16 -7 30 -3 M76 48 q16 -7 30 -3" {...sw(1.2, 0.45)} />
        {/* 딤낫세라 — 원경 성읍 */}
        <path d="M84 54 v-8 h6 v8 m6 0 v-11 h6 v11 m6 0 v-7 h6 v7" {...sw(1.2, 0.4)} />
      </g>
      {/* 기우는 해 — 세대의 저묾 */}
      <g style={d(1000, reduce)}>
        <path d="M22 24 a5 5 0 1 1 3.5 -8.7" {...sw(1.6)}>
          {!reduce && <animate attributeName="opacity" values="1;0.4" begin="2.5s" dur="1.8s" fill="freeze" />}
        </path>
      </g>
      {/* 홀로 선 무덤 표석 — 핵심 */}
      <g style={d(1800, reduce)}>
        <path d="M56 54 v-15 q0 -3 3 -3 h2 q3 0 3 3 v15 z" {...sw(2.8)} />
        <path d="M58 40 h4" {...sw(1.3)} />
      </g>
      {/* 지켜보는 장로들 */}
      <g style={d(2600, reduce)}>
        <circle cx="72" cy="45" r="1.9" {...sw(1.6, 0.7)} />
        <path d="M72 46.9 v3.3 M70.4 54 l1.6 -3.8 l1.6 3.8" {...sw(1.6, 0.7)} />
        <circle cx="80" cy="46" r="1.7" {...sw(1.4, 0.6)} />
        <path d="M80 47.7 v2.8 M78.6 54 l1.4 -3.5 l1.4 3.5" {...sw(1.4, 0.6)} />
      </g>
      <Label x="60" y="34" at="2.4" reduce={reduce}>여호수아의 묻힌 곳</Label>
      <Label x="95" y="60" at="1.4" reduce={reduce}>딤낫세라</Label>
    </g>
  )
}

const SCENES = {
  'authored-moses-birth-egypt': { Scene: BirthEgyptScene, desc: '학살령 아래 태어나 나일강 상자에 놓이다', caption: '아기 모세 — 출애굽기 1-2장' },
  'authored-moses-flees-midian': { Scene: FleesMidianScene, mood: 'dark', desc: '애굽인을 죽이고 미디안 광야로 도망치다', caption: '미디안 도피 — 출애굽기 2장' },
  'authored-moses-burning-bush': { Scene: BurningBushScene, desc: '떨기나무 불꽃 가운데서 부르심을 받다', caption: '떨기나무 — 출애굽기 3장' },
  'authored-moses-returns-egypt': { Scene: ReturnsEgyptScene, desc: '아론과 만나 애굽으로 돌아가다', caption: '귀환 — 출애굽기 4장' },
  'authored-moses-ten-plagues': { Scene: TenPlaguesScene, mood: 'dark', desc: '나일강 핏물부터 흑암까지, 완악한 애굽에 열 재앙이 내리다', caption: '열 재앙 — 출애굽기 7-12장' },
  'authored-moses-passover-night': { Scene: PassoverNightScene, desc: '어린양의 피 아래 죽음이 넘어가다', caption: '유월절 밤 — 출애굽기 12장' },
  'authored-moses-succoth-camp': { Scene: SuccothCampScene, desc: '자유민으로서 첫 진영을 치다', caption: '숙곳 — 출애굽기 12장' },
  'authored-moses-red-sea-crossing': { Scene: RedSeaCrossingScene, desc: '바닷물이 갈라져 마른 땅으로 건너고 애굽 군대는 물에 잠기다', caption: '홍해 도하 — 출애굽기 14장' },
  'authored-moses-marah-elim': { Scene: MarahElimScene, desc: '마라의 쓴 물이 달게 되고 엘림의 샘과 종려나무로 쉬다', caption: '마라와 엘림 — 출애굽기 15장' },
  'authored-moses-manna-quail': { Scene: MannaQuailScene, desc: '저녁 메추라기와 아침 만나로 광야의 양식이 시작되다', caption: '만나와 메추라기 — 출애굽기 16장' },
  'authored-moses-rephidim-water': { Scene: RephidimWaterScene, desc: '호렙산 반석을 치니 마실 물이 솟아나다', caption: '르비딤의 물 — 출애굽기 17장' },
  'authored-moses-amalek-battle': { Scene: AmalekBattleScene, desc: '들린 손이 이기고 내린 손이 지니, 아론과 훌이 그 손을 붙들다', caption: '아말렉 전투 — 출애굽기 17장' },
  'authored-moses-jethro-counsel': { Scene: JethroCounselScene, desc: '이드로의 조언으로 천부장부터 십부장까지 재판관을 세우다', caption: '이드로의 조언 — 출애굽기 18장' },
  'authored-moses-sinai-law': { Scene: SinaiLawScene, desc: '시내산에서 십계명 돌판을 받다', caption: '율법 수여 — 출애굽기 19-20장' },
  'authored-moses-golden-calf': { Scene: GoldenCalfScene, mood: 'dark', desc: '금송아지를 만들어 절하는 백성 앞에서 모세가 돌판을 깨뜨리다', caption: '금송아지 — 출애굽기 32-34장' },
  'authored-moses-tabernacle-glory': { Scene: TabernacleGloryScene, desc: '완성된 성막에 여호와의 영광이 가득해 모세도 들어가지 못하다', caption: '성막 봉헌 — 출애굽기 40장' },
  'authored-moses-paran-wandering': { Scene: ParanWanderingScene, desc: '구름 기둥을 따라 광야를 떠돌다', caption: '바란 광야 — 민수기 10장' },
  'authored-moses-kibroth-hattaavah': { Scene: KibrothHattaavahScene, mood: 'dark', desc: '고기를 탐하며 메추라기를 먹던 백성에게 재앙이 내리다', caption: '기브롯 핫다아와 — 민수기 11장' },
  'authored-moses-miriam-aaron-rebuke': { Scene: MiriamAaronRebukeScene, mood: 'dark', desc: '모세를 비방한 미리암이 나병에 걸렸다가 회복되다', caption: '미리암과 아론의 비방 — 민수기 12장' },
  'authored-moses-kadesh-spies': { Scene: KadeshSpiesScene, mood: 'dark', desc: '열 정탐꾼의 두려움이 사십 년을 부르다', caption: '가데스 바네아 — 민수기 13-14장' },
  'authored-moses-spies-hebron': { Scene: SpiesHebronScene, desc: '에스골 골짜기의 포도 한 송이를 메고 오다', caption: '헤브론 정탐 — 민수기 13장' },
  'authored-moses-korah-rebellion': { Scene: KorahRebellionScene, mood: 'dark', desc: '고라의 무리가 반역하다 땅에 삼켜지고 아론의 지팡이만 싹이 나다', caption: '고라의 반역 — 민수기 16-17장' },
  'authored-moses-meribah-water': { Scene: MeribahWaterScene, mood: 'dark', desc: '명령을 어기고 반석을 두 번 쳐 가나안 입성이 금지되다', caption: '므리바의 물 — 민수기 20장' },
  'authored-moses-aaron-death-hor': { Scene: AaronDeathHorScene, mood: 'dark', desc: '호르산 정상에서 대제사장 옷을 엘르아살에게 넘기고 아론이 죽다', caption: '호르산에서 아론의 죽음 — 민수기 20장' },
  'authored-moses-bronze-serpent': { Scene: BronzeSerpentScene, desc: '원망 중에 물린 백성이 장대 위 놋뱀을 바라보고 살다', caption: '놋뱀 — 민수기 21장' },
  'authored-moses-sihon-og': { Scene: SihonOgScene, desc: '통과를 거절한 시혼과 맞서 나온 옥을 차례로 쳐서 요단 동편을 얻다', caption: '시혼과 옥 — 민수기 21장' },
  'authored-moses-baal-peor': { Scene: BaalPeorScene, mood: 'dark', desc: '모압 여인들과 얽혀 바알브올에게 절하다가 비느하스의 창으로 염병이 그치다', caption: '브올의 바알 배교 — 민수기 25장' },
  'authored-moses-plains-moab': { Scene: PlainsMoabScene, desc: '요단 동편 모압 평지에 진을 치다', caption: '모압 평지 — 민수기 36장' },
  'authored-moses-law-reading-commission': { Scene: LawReadingCommissionScene, desc: '강하고 담대하라 부탁하며 여호수아에게 율법을 넘겨 대대로 낭독하게 하다', caption: '위임과 율법 낭독 — 신명기 31장' },
  'authored-moses-views-jericho': { Scene: ViewsJerichoScene, desc: '느보산에서 약속의 땅을 바라보다', caption: '느보산 — 신명기 34장' },
  'authored-moses-death-moab': { Scene: DeathMoabScene, mood: 'dark', desc: '아무도 모르는 곳에 모세가 잠들다', caption: '모세의 죽음 — 신명기 34장' },
  'authored-joshua-divine-commission': { Scene: DivineCommissionScene, desc: '강하고 담대하라 — 여호수아가 세워지다', caption: '위임 — 여호수아 1장' },
  'authored-joshua-rahab-spies': { Scene: RahabSpiesScene, desc: '라합이 창에 붉은 줄을 매달다', caption: '라합 — 여호수아 2장' },
  'authored-joshua-jordan-crossing': { Scene: JordanCrossingScene, desc: '법궤 앞에서 요단 강물이 끊어지다', caption: '요단 도하 — 여호수아 3장' },
  'authored-joshua-gilgal-camp': { Scene: GilgalCampScene, desc: '요단에서 가져온 열두 돌을 세우다', caption: '길갈 — 여호수아 4-5장' },
  'authored-joshua-jericho-conquest': { Scene: JerichoConquestScene, desc: '이레째 함성에 성벽이 무너지다', caption: '여리고 — 여호수아 6장' },
  'authored-joshua-achan-sin': { Scene: AchanSinScene, mood: 'dark', desc: '감춘 전리품의 죄로 아이 성에서 패퇴하고, 제비뽑혀 드러난 아간이 아골 골짜기에서 심판받다', caption: '아간의 범죄 — 여호수아 7장' },
  'authored-joshua-ai-conquest': { Scene: AiConquestScene, desc: '정결하게 한 후 매복으로 아이를 취하다', caption: '아이 성 — 여호수아 8장' },
  'authored-joshua-ebal-covenant': { Scene: EbalCovenantScene, desc: '에발산에서 율법을 돌에 새겨 낭독하다', caption: '에발산 언약 — 여호수아 8장' },
  'authored-joshua-gibeon-alliance': { Scene: GibeonAllianceScene, desc: '태양을 향해 명하니 해와 달이 멈춰 서다', caption: '기브온 전투 — 여호수아 10장' },
  'authored-joshua-southern-northern-campaign': { Scene: SouthernNorthernCampaignScene, desc: '막게다 굴의 다섯 왕부터 하솔까지, 남부와 북부 연합군을 차례로 격파하다', caption: '남부·북부 정복 — 여호수아 10-11장' },
  'authored-joshua-caleb-hebron': { Scene: CalebHebronScene, desc: '팔십오 세에도 강건한 갈렙이 45년 전 약속된 헤브론을 유업으로 받다', caption: '갈렙의 헤브론 — 여호수아 14장' },
  'authored-joshua-shiloh-tabernacle': { Scene: ShilohTabernacleScene, desc: '실로에 회막을 세우고 땅을 제비뽑아 나누다', caption: '실로 회막 — 여호수아 18장' },
  'authored-joshua-shechem-covenant': { Scene: ShechemCovenantScene, desc: '섬길 자를 오늘 택하라, 세겜에서 언약을 새기다', caption: '세겜 언약 — 여호수아 24장' },
  'authored-joshua-farewell-death': { Scene: FarewellDeathScene, mood: 'dark', desc: '나와 내 집은 여호와를 섬기리라, 110세로 잠들다', caption: '여호수아의 죽음 — 여호수아 24장' },
}

export default SCENES
