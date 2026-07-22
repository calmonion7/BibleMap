// 포로와 귀환 — 21개 정차지 장면 (task#230, #227 표준)
import { sw, d, Label } from './lib'

// 왕의 음식 거절 (단 1)
function BabylonDietScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M14 54 v-26 M26 54 v-26 M11 28 h18" {...sw(1.4, 0.55)} />
      </g>
      {/* 왕의 진미 상 vs 채소 접시 */}
      <g style={d(900, reduce)}>
        <path d="M40 46 h24 M44 54 v-8 M60 54 v-8" {...sw(2)} />
        <path d="M46 43 q0 -3 3 -3 q3 0 3 3 M55 43 h6 M56.5 43 v-3.5" {...sw(1.8)} />
        <path d="M42 38 l6 8 M48 38 l-6 8" {...sw(1.8)} stroke="var(--paper-accent)" />
      </g>
      <g style={d(1800, reduce)}>
        <ellipse cx="86" cy="47" rx="7" ry="2.2" {...sw(2.4)} />
        <path d="M82 45.5 q1.5 -3 4 -1.5 M87 45 q1.5 -2.5 3.5 -1" {...sw(1.5)} />
      </g>
      {/* 네 청년 */}
      <g style={d(2600, reduce)}>
        <circle cx="98" cy="36" r="2.2" {...sw(2.2)} />
        <path d="M98 38.2 v6 M96 48 l2 -3.8 l2 3.8" {...sw(2.2)} />
        <circle cx="106" cy="37" r="2" {...sw(1.9, 0.9)} />
        <path d="M106 39 v5 M104.3 48 l1.7 -4 l1.7 4" {...sw(1.9, 0.9)} />
      </g>
      <Label x="52" y="32" at="1.4" reduce={reduce}>왕의 진미</Label>
      <Label x="86" y="38" at="2.2" reduce={reduce}>채식</Label>
      <Label x="102" y="28" at="3" reduce={reduce}>다니엘과 세 친구</Label>
    </g>
  )
}

// 신상 꿈 (단 2)
function ImageDreamScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
      </g>
      {/* 신상 — 금·은·놋·철 구분 */}
      <g style={d(900, reduce)}>
        <circle cx="70" cy="16" r="4.5" {...sw(2.4)} />
        <path d="M64 21 h12 l-1.5 10 h-9 z" {...sw(2.2)} />
        <path d="M65.5 31 h9 l-1 9 h-7 z" {...sw(2)} />
        <path d="M67 40 l-2 14 M73 40 l2 14 M67.5 47 h5" {...sw(1.9)} />
        <path d="M64 24 h12 M65 34 h10" {...sw(1.2, 0.5)} />
      </g>
      {/* 뜨인 돌 — 핵심: 날아와 부딪힘 */}
      <g style={d(2000, reduce)}>
        <path d="M20 40 l5 -3 l4.5 2 l0.5 4.5 l-5 2.5 l-4.5 -2.5 z" {...sw(2.8)}>
          {!reduce && (
            <animateMotion path="M0 0 q20 -6 40 3" begin="2.4s" dur="0.7s" fill="freeze"
              calcMode="spline" keySplines="0.3 0 0.75 1" keyTimes="0;1" />
          )}
        </path>
      </g>
      {/* 균열 */}
      <g style={d(reduce ? 0 : 3300, reduce)}>
        <path d="M68 42 l-2.5 3.5 M72 43 l2.5 3 M70 41 l0.5 -3" {...sw(1.4, 0.75)} />
      </g>
      <Label x="86" y="26" at="1.4" reduce={reduce}>금·은·놋·철 신상</Label>
      <Label x="24" y="31" at="2.6" reduce={reduce}>뜨인 돌</Label>
    </g>
  )
}

// 나무 꿈과 광기 (단 4)
function TreeDreamScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M84 44 q13 -8 26 -2" {...sw(1.1, 0.4)} />
      </g>
      {/* 하늘까지 닿은 나무 */}
      <g style={d(900, reduce)}>
        <path d="M52 54 q-1.5 -18 -2.5 -32" {...sw(2.8)} />
        <path d="M48 22 q-16 -2 -18 -12 q11 -4 18 3 q1 -10 10 -12 q7 5 4 13 q12 -4 15 5 q-5 10 -18 8 q-5 2 -11 -5" {...sw(2)} />
      </g>
      {/* 베임 — 도끼 자국 + 기울어짐 예고 */}
      <g style={d(2000, reduce)}>
        <path d="M46 46 l8 -3 M46 49 l8 -3" {...sw(2.4)} stroke="var(--paper-accent)" />
        <path d="M64 44 l6 -6 M70 38 l3.5 -0.5 m-3.5 0.5 l0.5 3.5" {...sw(2)} />
      </g>
      {/* 그루터기 띠 — 남겨둠 */}
      <g style={d(2900, reduce)}>
        <path d="M46 52 q5 2 11 0" {...sw(1.8)} />
      </g>
      <Label x="78" y="14" at="1.4" reduce={reduce}>하늘에 닿은 나무</Label>
      <Label x="52" y="61" at="3.1" reduce={reduce} size="4.2">그루터기는 남겨 두라</Label>
    </g>
  )
}

// 네 짐승 환상 (단 7)
function FourBeastsScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M8 50 q8 -3.5 16 0 q8 -3.5 16 0 q8 -3.5 16 0 q8 -3.5 16 0 q8 -3.5 16 0 q8 -3.5 16 0" {...sw(2)} />
        <path d="M14 54 q8 -3 16 0 q8 -3 16 0 q8 -3 16 0 q8 -3 16 0 q8 -3 16 0" {...sw(1.4, 0.6)} />
      </g>
      {/* 네 짐승 — 물결 위로 솟는 간략 형상들 */}
      <g style={d(1100, reduce)}>
        <path d="M18 46 q0 -6 6 -6 q4 0 5 4 M24 40 q-2 -3 1 -5 M27 40 q2 -2.5 5 -2" {...sw(1.9)} />
        <path d="M42 45 q-1 -7 5 -8 q5 -1 6 4 M44 38 l-1.5 -3.5 M49 37 l0.5 -3.5" {...sw(1.9)} />
        <path d="M66 45 q0 -6 5 -7 q4 -1 6 2 M69 38 q0 -3 3 -3 M73 38 q1 -2.5 3.5 -2.5" {...sw(1.9)} />
        <path d="M90 45 q0 -7 6 -8 q5 -1 7 3 M92 37 l-1 -4 M97 36 l0 -4 M101 37 l1 -3.5" {...sw(2.1)} />
      </g>
      {/* 인자 같은 이 — 위 구름과 보좌 */}
      <g style={d(2400, reduce)} stroke="var(--paper-accent)">
        <path d="M48 16 q3 -5 9 -4 q3 -4 8 -2 q5 -1 6 3 q3 2 0.5 5 q-6 3 -12 1.5 q-8 1.5 -11.5 -3.5" {...sw(1.6)} />
        <circle cx="60" cy="10" r="2" {...sw(1.6)} />
      </g>
      <Label x="60" y="61" at="1.9" reduce={reduce}>바다에서 오른 네 짐승</Label>
      <Label x="86" y="10" at="3" reduce={reduce}>인자 같은 이</Label>
    </g>
  )
}

// 숫양과 숫염소 (단 8)
function SusaVisionScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M8 44 q12 -7 24 -2 M88 43 q12 -7 24 -2" {...sw(1.1, 0.4)} />
      </g>
      {/* 숫양 — 두 뿔 */}
      <g style={d(1000, reduce)}>
        <path d="M78 50 q0 -5.5 6.5 -5.5 q6.5 0 6.5 5.5 q0 3.5 -6.5 3.5 q-6.5 0 -6.5 -3.5" {...sw(2.2)} />
        <circle cx="93.5" cy="45" r="2.5" {...sw(2.2)} />
        <path d="M95 42.8 q3.5 -3 2 -6.5 M92.5 42.5 q1.5 -3.5 -0.5 -6" {...sw(1.9)} />
        <path d="M80 54 v-1 M88 54 v-1" {...sw(1.3)} />
      </g>
      {/* 숫염소 — 한 뿔, 돌진 */}
      <g transform={reduce ? 'translate(18 0)' : undefined} style={d(1900, reduce)}>
        <path d="M26 50 q0 -5.5 6.5 -5.5 q6.5 0 6.5 5.5 q0 3.5 -6.5 3.5 q-6.5 0 -6.5 -3.5" {...sw(2.4)} />
        <circle cx="41" cy="45" r="2.5" {...sw(2.4)} />
        <path d="M42 42.8 q1 -4 4.5 -4.5" {...sw(2.2)} />
        <path d="M28 54 v-1 M36 54 v-1" {...sw(1.3)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="translate" from="0 0" to="22 0"
            begin="2.4s" dur="0.8s" fill="freeze" calcMode="spline" keySplines="0.4 0 0.8 1" keyTimes="0;1" />
        )}
      </g>
      <Label x="88" y="34" at="1.5" reduce={reduce}>메대·바사의 숫양</Label>
      <Label x="30" y="34" at="2.4" reduce={reduce}>헬라의 숫염소</Label>
    </g>
  )
}

// 벽의 글씨 (단 5)
function WritingWallScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M40 54 V14 h64" {...sw(2)} />
      </g>
      {/* 잔치 잔들 */}
      <g style={d(900, reduce)}>
        <path d="M14 48 q0 -3 3 -3 q3 0 3 3 M17 48 v4 M14.5 52.5 h5" {...sw(1.8)} />
        <path d="M26 49 q0 -2.6 2.6 -2.6 q2.6 0 2.6 2.6 M28.6 49 v3.5 M26.5 53 h4.2" {...sw(1.6, 0.85)} />
      </g>
      {/* 손가락 — 글씨 획 순차 draw */}
      <g style={d(1800, reduce)}>
        <path d="M50 20 q3 -2 5.5 0 l1.5 3.5" {...sw(2.2)} />
      </g>
      <g style={d(2400, reduce)} stroke="var(--paper-accent)">
        <path d="M52 30 l4 6 m0 -6 l-4 6" {...sw(2)} />
      </g>
      <g style={d(3000, reduce)} stroke="var(--paper-accent)">
        <path d="M64 30 v6 m-2.5 -6 h5" {...sw(2)} />
      </g>
      <g style={d(3600, reduce)} stroke="var(--paper-accent)">
        <path d="M76 30 l3 6 l3 -6 M88 30 q3 3 0 6" {...sw(2)} />
      </g>
      <Label x="72" y="26" at="4.2" reduce={reduce}>메네 메네 데겔 우바르신</Label>
      <Label x="20" y="38" at="1.3" reduce={reduce}>벨사살의 잔치</Label>
    </g>
  )
}

// 다리오의 총리 (단 6:1-4)
function DariusAdministratorScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M14 54 v-24 M26 54 v-24 M11 30 h18 M94 54 v-24 M106 54 v-24 M91 30 h18" {...sw(1.4, 0.55)} />
      </g>
      {/* 단 위의 다니엘 — 높이 */}
      <g style={d(1000, reduce)}>
        <path d="M48 54 h24 M52 54 v-6 h16 v6" {...sw(2)} />
        <circle cx="60" cy="34" r="3" {...sw(2.6)} />
        <path d="M60 37 v9 M56.5 48 h7 M60 39.5 q-4 1 -5.5 4.5 M60 39.5 q4 1 5.5 4.5" {...sw(2.6)} />
      </g>
      {/* 인장 반지 — 위임 */}
      <g transform={reduce ? undefined : 'translate(0 -8)'} style={d(2100, reduce)} stroke="var(--paper-accent)">
        <circle cx="60" cy="24" r="2.6" {...sw(2)} />
        <circle cx="60" cy="24" r="1" {...sw(1.4)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="translate" from="0 -8" to="0 0"
            begin="2.4s" dur="0.6s" fill="freeze" />
        )}
      </g>
      {/* 시기하는 총리들 */}
      <g style={d(2900, reduce)}>
        <circle cx="32" cy="45" r="2.2" {...sw(1.9)} />
        <path d="M32 47.2 v3.3 M30 54 l2 -3.5 l2 3.5 M34 46 q2.5 1 4 3" {...sw(1.9)} />
        <circle cx="88" cy="45.5" r="2.1" {...sw(1.8, 0.9)} />
        <path d="M88 47.6 v2.9 M86 54 l2 -3.4 l2 3.4 M86 46.5 q-2.5 1 -4 3" {...sw(1.8, 0.9)} />
      </g>
      <Label x="60" y="14" at="2.4" reduce={reduce}>총리 다니엘</Label>
      <Label x="34" y="36" at="3.2" reduce={reduce} size="4.2">시기하는 자들</Label>
    </g>
  )
}

// 사자 굴 (단 6)
function LionsDenScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M14 54 q2 -26 34 -28 q34 -2 40 28" {...sw(2.2)} />
      </g>
      {/* 사자 둘 — 입 다묾 */}
      <g style={d(1100, reduce)}>
        <path d="M28 50 q0 -6 7 -6 q7 0 7 6 q0 4 -7 4 q-7 0 -7 -4" {...sw(2)} />
        <circle cx="45" cy="46" r="3.2" {...sw(2)} />
        <path d="M42 43 q-2 -3 0.5 -5 M48 43 q2 -3 -0.5 -5 M43 47.5 h4" {...sw(1.6)} />
        <path d="M78 51 q0 -5 6 -5 q6 0 6 5 q0 3 -6 3 q-6 0 -6 -3" {...sw(1.9, 0.9)} />
        <circle cx="74" cy="47.5" r="2.9" {...sw(1.9, 0.9)} />
        <path d="M72.6 48.8 h3.4" {...sw(1.5)} />
      </g>
      {/* 평안한 다니엘 — 중앙에 곧게 */}
      <g style={d(2100, reduce)}>
        <circle cx="60" cy="33" r="2.9" {...sw(2.6)} />
        <path d="M60 35.9 v10.6 M56.5 54 l3.5 -7.5 l3.5 7.5" {...sw(2.6)} />
        <path d="M58 39 q2 1.2 4 0" {...sw(1.3, 0.6)} />
      </g>
      {/* 천사의 빛 */}
      <g style={d(reduce ? 0 : 3200, reduce)} stroke="var(--paper-accent)">
        <path d="M60 22 v-4 M53 24 l-2.6 -2.6 M67 24 l2.6 -2.6" {...sw(1.5)} />
      </g>
      <Label x="60" y="14" at="3.4" reduce={reduce}>사자 입을 봉하시다</Label>
      <Label x="60" y="61" at="2.5" reduce={reduce}>다니엘</Label>
    </g>
  )
}

// 칠십 이레 (단 9)
function SeventyWeeksScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        {/* 열린 창 — 예루살렘 향해 */}
        <path d="M18 40 v-16 h18 v16 M27 40 v-16 M18 32 h18" {...sw(2)} />
      </g>
      {/* 무릎 꿇은 다니엘 — 주역 */}
      <g style={d(1200, reduce)}>
        <circle cx="54" cy="38" r="2.9" {...sw(2.6)} />
        <path d="M54 40.9 l-1.5 6.1 M47 54 h10.5 M52.5 47 q-3.8 1.8 -5.3 5.3 M53 43.5 q-3.5 -0.5 -5.5 -2" {...sw(2.6)} />
      </g>
      {/* 가브리엘 — 날개 곡선 강림 */}
      <g transform={reduce ? undefined : 'translate(0 -12)'} style={d(2200, reduce)}>
        <circle cx="82" cy="26" r="2.6" {...sw(2)} />
        <path d="M78.5 36 l1.7 -7 h3.6 l1.7 7 M78.5 36 h7" {...sw(2)} />
        <path d="M78 28 q-5 -2.5 -6 -6.5 M86 28 q5 -2.5 6 -6.5" {...sw(1.6)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="translate" from="0 -12" to="0 0"
            begin="2.5s" dur="1s" fill="freeze" calcMode="spline" keySplines="0.3 0 0.5 1" keyTimes="0;1" />
        )}
      </g>
      <g style={d(reduce ? 0 : 3400, reduce)} stroke="var(--paper-accent)">
        <path d="M96 46 h2 m2.5 0 h2 m2.5 0 h2 M96 50 h2 m2.5 0 h2" {...sw(1.6)} />
      </g>
      <Label x="54" y="28" at="1.7" reduce={reduce}>기도하는 다니엘</Label>
      <Label x="86" y="16" at="2.9" reduce={reduce}>가브리엘</Label>
      <Label x="102" y="41" at="3.7" reduce={reduce} size="4.2">칠십 이레</Label>
    </g>
  )
}

// 티그리스 강가 환상 (단 10-12)
function TigrisVisionScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M8 49 q9 -3 18 0 q9 -3 18 0 q9 -3 18 0" {...sw(1.8)} />
        <path d="M14 52.5 q8 -2.5 16 0 q8 -2.5 16 0" {...sw(1.3, 0.55)} />
      </g>
      {/* 세마포 입은 이 — 빛나는 */}
      <g style={d(1100, reduce)}>
        <circle cx="76" cy="24" r="3" {...sw(2.4)} />
        <path d="M71 44 l2.2 -17 h5.6 l2.2 17 M71 44 h11" {...sw(2.4)} />
        <path d="M74.5 30 q0.5 8 0 13 M77.5 30 q0.4 8 0 13" {...sw(1.3, 0.55)} />
        <path d="M70 20 l-2.6 -2.6 M76 18.5 v-3.5 M82 20 l2.6 -2.6 M68 26 h-3.5 M84 26 h3.5" {...sw(1.5)} stroke="var(--paper-accent)" />
      </g>
      {/* 엎드러진 다니엘 */}
      <g style={d(2300, reduce)}>
        <circle cx="30" cy="45" r="2.5" {...sw(2.3)} />
        <path d="M32 46 q5 -1.8 8.5 1 M28 46.5 l-4 3.5" {...sw(2.3)} />
      </g>
      <Label x="94" y="30" at="1.7" reduce={reduce}>세마포 입은 이</Label>
      <Label x="28" y="36" at="2.8" reduce={reduce}>다니엘</Label>
      <Label x="60" y="61" at="3.3" reduce={reduce} size="4.2">티끌 가운데서 깨어나리라</Label>
    </g>
  )
}

// 왕후 간택 (에 2:15-17)
function QueenChosenScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M16 54 v-28 M28 54 v-28 M13 26 h18 M92 54 v-28 M104 54 v-28 M89 26 h18" {...sw(1.4, 0.55)} />
        <path d="M19 32 h6 m-6 8 h6 M95 32 h6 m-6 8 h6" {...sw(1.1, 0.4)} />
      </g>
      {/* 에스더 — 주역 */}
      <g style={d(1100, reduce)}>
        <circle cx="60" cy="32" r="3" {...sw(2.6)} />
        <path d="M55.5 54 l2.2 -19 h4.6 l2.2 19 M55.5 54 h9" {...sw(2.6)} />
        <path d="M58 40 q0.5 8 0 13 M62 40 q0.4 8 0 13" {...sw(1.3, 0.55)} />
      </g>
      {/* 왕후의 관 — 강림 */}
      <g transform={reduce ? undefined : 'translate(0 -9)'} style={d(2100, reduce)}>
        <path d="M56.5 26.5 v-3.2 l1.8 2 l1.7 -3 l1.7 3 l1.8 -2 v3.2 h-7" {...sw(2.8)} stroke="var(--paper-accent)" />
        {!reduce && (
          <animateTransform attributeName="transform" type="translate" from="0 -9" to="0 0"
            begin="2.3s" dur="0.6s" fill="freeze" calcMode="spline" keySplines="0.3 0 0.5 1" keyTimes="0;1" />
        )}
      </g>
      <Label x="60" y="60" at="1.7" reduce={reduce}>에스더</Label>
      <Label x="60" y="10" at="2.9" reduce={reduce}>수산 궁의 왕후</Label>
    </g>
  )
}

// 하만의 조서 (에 3:8-13)
function HamanDecreeScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M14 12 q7 -4 14 0 q7 -4 14 0 M74 10 q7 -4 14 0 q7 -4 14 0" {...sw(1.5, 0.6)} />
      </g>
      {/* 조서 두루마리 — 핵심 */}
      <g style={d(1000, reduce)}>
        <path d="M42 46 v-20 q0 -3 3 -3 h28 q3 0 3 3 v20 q0 3 -3 3 h-28 q-3 0 -3 -3" {...sw(2.4)} />
        <path d="M48 30 h22 M48 35 h22 M48 40 h16" {...sw(1.3)} />
      </g>
      {/* 인장 찍힘 — 강조 */}
      <g transform={reduce ? undefined : 'translate(0 -7)'} style={d(2100, reduce)} stroke="var(--paper-accent)">
        <circle cx="68" cy="43" r="2.8" {...sw(2.2)} />
        <path d="M66.5 43 l1.2 1.2 l2 -2.4" {...sw(1.5)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="translate" from="0 -7" to="0 0"
            begin="2.4s" dur="0.45s" fill="freeze" calcMode="spline" keySplines="0.4 0 0.8 1" keyTimes="0;1" />
        )}
      </g>
      {/* 하만 실루엣 */}
      <g style={d(2800, reduce)}>
        <circle cx="92" cy="36" r="2.8" {...sw(2.2)} />
        <path d="M92 38.8 v8.2 M89 54 l3 -7 l3 7 M89.5 42 q-4 -1 -6.5 -2.5" {...sw(2.2)} />
      </g>
      <Label x="58" y="18" at="1.4" reduce={reduce}>멸절의 조서</Label>
      <Label x="96" y="27" at="3.1" reduce={reduce}>하만</Label>
    </g>
  )
}

// 죽으면 죽으리이다 (에 4:13-16)
function IfIPerishScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        {/* 궁 문 */}
        <path d="M46 54 v-26 M74 54 v-26 M42 28 h36" {...sw(2.2)} />
        <path d="M50 34 h4 m12 0 h4" {...sw(1.2, 0.45)} />
      </g>
      {/* 에스더 — 문 앞에 서다 */}
      <g style={d(1200, reduce)}>
        <circle cx="32" cy="34" r="3" {...sw(2.6)} />
        <path d="M27.5 54 l2.2 -17 h4.6 l2.2 17 M27.5 54 h9" {...sw(2.6)} />
        <path d="M30 41 q0.5 7 0 12" {...sw(1.3, 0.55)} />
      </g>
      {/* 내밀어진 금 홀 — 핵심 */}
      <g style={d(2200, reduce)} stroke="var(--paper-accent)">
        <path d="M92 36 L60 40" {...sw(2.4)}>
          {!reduce && <animate attributeName="stroke-dashoffset" from="1" to="0" begin="2.4s" dur="0.8s" fill="freeze" />}
        </path>
        <circle cx="59" cy="40.2" r="1.6" {...sw(1.8)} />
      </g>
      {/* 왕 실루엣 — 안쪽 */}
      <g style={d(1800, reduce)}>
        <circle cx="96" cy="33" r="2.7" {...sw(2)} />
        <path d="M96 35.7 v9.3 M93 54 l3 -7 l3 7" {...sw(2)} />
        <path d="M93.8 29 v-2.2 l1.3 1.2 l0.9 -1.8 l0.9 1.8 l1.3 -1.2 v2.2" {...sw(1.5)} />
      </g>
      <Label x="30" y="24" at="1.7" reduce={reduce}>에스더</Label>
      <Label x="78" y="60" at="3" reduce={reduce} size="4.2">내밀어진 금 홀 — 죽으면 죽으리이다</Label>
    </g>
  )
}

// 하만의 몰락 (에 7:3-10)
function HamanDownfallScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
      </g>
      {/* 높은 나무(교수대) — 자기가 세운 */}
      <g style={d(1000, reduce)}>
        <path d="M78 54 V12 M78 12 h16 M94 12 v6" {...sw(2.6)} />
        <path d="M74 54 h10 M76 50 l4 4" {...sw(1.6)} />
      </g>
      {/* 엎드린 하만 */}
      <g style={d(2000, reduce)}>
        <circle cx="44" cy="48.5" r="2.5" {...sw(2.3)} />
        <path d="M46 49.5 q5 -1.8 8.5 1 M42 50 l-4 3.5" {...sw(2.3)} />
      </g>
      {/* 에스더와 왕 — 잔치 상 */}
      <g style={d(1500, reduce)}>
        <path d="M14 48 h20 M17 54 v-6 M31 54 v-6" {...sw(1.8)} />
        <circle cx="20" cy="40" r="2.4" {...sw(2.1)} />
        <path d="M17 48 l1.5 -5.5 h3 l1.5 5.5" {...sw(2.1)} />
        <circle cx="29" cy="40.5" r="2.3" {...sw(2, 0.9)} />
        <path d="M26.5 48 l1.3 -5 h2.6 l1.3 5" {...sw(2, 0.9)} />
      </g>
      <Label x="90" y="30" at="1.4" reduce={reduce}>자기가 세운 나무</Label>
      <Label x="46" y="40" at="2.5" reduce={reduce}>하만</Label>
      <Label x="24" y="32" at="2" reduce={reduce} size="4.2">두 번째 잔치</Label>
    </g>
  )
}

// 부림절 (에 9:20-22)
function PurimScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
      </g>
      {/* 잔치 상 */}
      <g style={d(900, reduce)}>
        <path d="M34 48 h52 M38 54 v-6 M82 54 v-6" {...sw(2.2)} />
        <path d="M44 45 q0 -2.6 2.6 -2.6 q2.6 0 2.6 2.6 M60 45 h7 M62.5 45 v-3 M74 45 q0 -2.4 2.4 -2.4 q2.4 0 2.4 2.4" {...sw(1.6)} />
      </g>
      {/* 주고받는 예물 */}
      <g style={d(1800, reduce)}>
        <circle cx="22" cy="38" r="2.6" {...sw(2.3)} />
        <path d="M22 40.6 v7.4 M19.5 54 l2.5 -6 l2.5 6 M24.5 42 q4 -1 7 1" {...sw(2.3)} />
        <path d="M31 41.5 h5 v4 h-5 z M33.5 41.5 v4" {...sw(2)} stroke="var(--paper-accent)" />
        <circle cx="98" cy="38.5" r="2.5" {...sw(2.2)} />
        <path d="M98 41 v7 M95.5 54 l2.5 -6 l2.5 6 M95.5 42.5 q-4 -1 -7 1" {...sw(2.2)} />
      </g>
      <g style={d(reduce ? 0 : 2800, reduce)} stroke="var(--paper-accent)">
        <path d="M56 26 v-3 m-1.5 1.5 h3 M70 22 v-3 m-1.5 1.5 h3 M44 24 v-2.4 m-1.2 1.2 h2.4" {...sw(1.4)} />
      </g>
      <Label x="60" y="60" at="1.4" reduce={reduce}>부림의 잔치</Label>
      <Label x="60" y="12" at="3" reduce={reduce} size="4.2">슬픔이 변하여 기쁜 날이 되다</Label>
    </g>
  )
}

// 예루살렘 소식 (느 1:3-4)
function NewsPrayerScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        {/* 무너진 성벽 — 원경 */}
        <path d="M74 54 v-6 h6 l2 -4 h6 v10 M92 54 v-8 l4 -3 l4 5 v6" {...sw(1.4, 0.55)} />
        <path d="M78 44 l3 -3 M96 41 l2.5 2" {...sw(1.1, 0.4)} />
      </g>
      {/* 앉아 우는 느헤미야 — 주역 */}
      <g style={d(1200, reduce)}>
        <circle cx="34" cy="40" r="2.9" {...sw(2.6)} />
        <path d="M34 42.9 q-1.5 4 -5 5 M26 54 l4.5 -6 M36 47 l2 7" {...sw(2.6)} />
        <path d="M32 41.5 q2 2.5 4.5 0.5" {...sw(2)} />
      </g>
      {/* 술잔 — 관원의 소임 내려놓음 */}
      <g style={d(2200, reduce)}>
        <path d="M48 50 q0 -2.6 2.6 -2.6 q2.6 0 2.6 2.6 M50.6 50 v3 M48.6 53.5 h4" {...sw(1.7)} />
      </g>
      <g style={d(reduce ? 0 : 2900, reduce)} stroke="var(--paper-accent)">
        <path d="M31.5 46 q-0.6 2 0 3.5 M36.5 46 q0.6 2 0 3.5" {...sw(1.5)} />
      </g>
      <Label x="34" y="30" at="1.7" reduce={reduce}>느헤미야</Label>
      <Label x="88" y="32" at="0.9" reduce={reduce}>무너진 성벽 소식</Label>
    </g>
  )
}

// 왕의 허락 (느 2:4-8)
function KingsPermissionScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M78 54 h28 M98 54 V36 M84 46 h10" {...sw(2)} />
      </g>
      {/* 아닥사스다 — 왕좌 */}
      <g style={d(900, reduce)}>
        <circle cx="90" cy="36.5" r="2.9" {...sw(2.2)} />
        <path d="M90 39.4 v6.6 M87 42.5 q3 -1.5 6 0" {...sw(2.2)} />
        <path d="M87.8 32 v-2.2 l1.3 1.2 l0.9 -1.8 l0.9 1.8 l1.3 -1.2 v2.2" {...sw(1.6)} />
      </g>
      {/* 느헤미야 — 조서 받음 */}
      <g style={d(1700, reduce)}>
        <circle cx="42" cy="37" r="2.9" {...sw(2.6)} />
        <path d="M42 39.9 v7.1 M39 54 l3 -7 l3 7 M44.5 42 q5 -1.5 9 0.5" {...sw(2.6)} />
      </g>
      {/* 조서 — 건네짐 */}
      <g style={d(2500, reduce)}>
        <path d="M58 40 h9 q1.5 0 1.5 1.5 v3 q0 1.5 -1.5 1.5 h-9 q-1.5 0 -1.5 -1.5 v-3 q0 -1.5 1.5 -1.5" {...sw(2.4)} stroke="var(--paper-accent)">
          {!reduce && (
            <animateMotion path="M0 0 L18 -1.5" begin="2.7s" dur="0.7s" fill="freeze"
              calcMode="spline" keySplines="0.3 0 0.7 1" keyTimes="0;1" />
          )}
        </path>
      </g>
      <Label x="42" y="27" at="2.2" reduce={reduce}>느헤미야</Label>
      <Label x="94" y="24" at="1.3" reduce={reduce}>아닥사스다 왕</Label>
    </g>
  )
}

// 야간 시찰 (느 2:11-17)
function NightInspectionScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M100 14 a6 6 0 1 1 -4 -10 a7.5 7.5 0 0 0 4 10" {...sw(1.6)} />
        <path d="M14 10 v2.4 m-1.2 -1.2 h2.4" {...sw(1.2, 0.6)} />
      </g>
      {/* 무너진 성벽 돌무더기 */}
      <g style={d(1000, reduce)}>
        <path d="M14 54 v-8 h7 l2 -5 h7 l1.5 4 h6 v9" {...sw(2)} />
        <path d="M42 52 q2 -3.5 5.5 -2.5 q3 1 2.5 4.5 M52 53 q1.5 -2.8 4.5 -2 M20 43 l3 -2.5" {...sw(1.6, 0.8)} />
      </g>
      {/* 나귀 탄 느헤미야 — 전진 */}
      <g transform={reduce ? 'translate(12 0)' : undefined} style={d(2000, reduce)}>
        <path d="M70 50 q0 -4.5 5.5 -4.5 q5.5 0 5.5 4.5 M72 54 v-2 M79 54 v-2" {...sw(2)} />
        <path d="M82 46.5 q3 -1.5 3.5 -4.5" {...sw(1.7)} />
        <circle cx="75" cy="36.5" r="2.6" {...sw(2.4)} />
        <path d="M75 39.1 v5.4 M72.5 46 h5" {...sw(2.4)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="translate" from="0 0" to="-16 0"
            begin="2.4s" dur="2.2s" fill="freeze" calcMode="spline" keySplines="0.3 0 0.7 1" keyTimes="0;1" />
        )}
      </g>
      <Label x="26" y="34" at="1.4" reduce={reduce}>무너진 성벽</Label>
      <Label x="80" y="27" at="2.6" reduce={reduce}>밤의 시찰</Label>
    </g>
  )
}

// 성벽 재건과 방해 (느 4:16-18)
function WallOppositionScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
      </g>
      {/* 반쯤 쌓인 성벽 */}
      <g style={d(900, reduce)}>
        <path d="M40 54 v-12 h40 v12 M40 48 h40 M50 54 v-6 M60 48 v-6 M70 54 v-6" {...sw(2.2)} />
        <path d="M44 44 h6 m6 0 h6 m6 0 h6" {...sw(1.3, 0.55)} />
      </g>
      {/* 한 손 흙손 한 손 창 — 핵심 */}
      <g style={d(1900, reduce)}>
        <circle cx="26" cy="34" r="2.9" {...sw(2.6)} />
        <path d="M26 36.9 v9.1 M23 54 l3 -8 l3 8" {...sw(2.6)} />
        <path d="M28.5 39 l6 2.5 M34.5 41.5 l2.5 -0.5" {...sw(2.2)} />
        <path d="M23.5 39 l-5 -1.5 M18.5 37.5 l-4 -6 M14.5 31.5 l-1.5 -0.5 m1.5 0.5 l0.5 -1.5" {...sw(2.2)} />
      </g>
      {/* 위협 화살 — 원경 */}
      <g style={d(2800, reduce)}>
        <path d="M100 30 l8 -5 m-2.5 -0.5 l2.5 0.5 l-0.5 2.5" {...sw(1.4, 0.6)} />
      </g>
      <Label x="26" y="24" at="2.4" reduce={reduce}>한 손엔 병기</Label>
      <Label x="60" y="60" at="1.3" reduce={reduce}>쌓이는 성벽</Label>
    </g>
  )
}

// 52일 완공 (느 6:15-16)
function WallCompletedScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
      </g>
      {/* 완성된 성벽 — 성문 + 총안 */}
      <g style={d(900, reduce)}>
        <path d="M14 54 v-18 h92 v18" {...sw(2.4)} />
        <path d="M14 36 v-4 h6 v4 m8 0 v-4 h6 v4 m8 0 v-4 h6 v4 m8 0 v-4 h6 v4 m8 0 v-4 h6 v4 m8 0 v-4 h6 v4 m8 0 v-4 h6 v4 m8 0 v-4 h6 v4" {...sw(1.6)} />
        <path d="M52 54 v-11 q8 -6 16 0 v11" {...sw(2.2)} />
        <path d="M20 44 h5 m8 0 h5 m45 0 h5 m8 0 h5" {...sw(1.2, 0.45)} />
      </g>
      {/* 나팔 — 낙성 */}
      <g style={d(2200, reduce)} stroke="var(--paper-accent)">
        <path d="M30 24 q3 -2 6 0 M31.5 20.5 q3 -2.5 6 0 M84 24 q3 -2 6 0 M85.5 20.5 q3 -2.5 6 0" {...sw(1.5)} />
      </g>
      <Label x="60" y="28" at="1.4" reduce={reduce}>완공된 성벽</Label>
      <Label x="60" y="61" at="2.6" reduce={reduce} size="4.2">오십이 일 만에 — 하나님께서 이루신 일</Label>
    </g>
  )
}

// 수문 앞 율법 낭독 (느 8:8-10)
function LawReadingScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
      </g>
      {/* 나무 강단 + 펼친 두루마리 */}
      <g style={d(900, reduce)}>
        <path d="M46 54 v-10 h28 v10 M44 44 h32 M50 54 v-10 M70 54 v-10" {...sw(2.2)} />
        <circle cx="60" cy="32" r="2.8" {...sw(2.5)} />
        <path d="M60 34.8 v9.2 M57 40 q3 -1.5 6 0" {...sw(2.5)} />
        <path d="M50 36 q0 -2 2 -2 h4 M70 36 q0 -2 -2 -2 h-4 M52 34 h16" {...sw(2)} stroke="var(--paper-accent)" />
      </g>
      {/* 듣는 회중 — 울다가 기뻐함 */}
      <g style={d(2100, reduce)}>
        <circle cx="22" cy="46" r="2.2" {...sw(1.9)} />
        <path d="M22 48.2 v2.3 M20 54 l2 -3 l2 3 M20 44 l-2.6 -3.4 M24 44 l2.6 -3.4" {...sw(1.9)} />
        <circle cx="34" cy="47" r="2" {...sw(1.7, 0.85)} />
        <path d="M34 49 v1.6 M32.4 54 l1.6 -2.6 l1.6 2.6" {...sw(1.7, 0.85)} />
        <circle cx="94" cy="46.5" r="2.1" {...sw(1.8, 0.9)} />
        <path d="M94 48.6 v1.9 M92.2 54 l1.8 -2.8 l1.8 2.8 M92 44.5 l-2.6 -3.2 M96 44.5 l2.6 -3.2" {...sw(1.8, 0.9)} />
        <circle cx="104" cy="47.5" r="1.9" {...sw(1.6, 0.75)} />
        <path d="M104 49.4 v1.4 M102.6 54 l1.4 -2.4 l1.4 2.4" {...sw(1.6, 0.75)} />
      </g>
      <Label x="60" y="24" at="1.5" reduce={reduce}>에스라의 낭독</Label>
      <Label x="60" y="61" at="2.9" reduce={reduce} size="4.2">여호와로 인한 기쁨이 너희의 힘이라</Label>
    </g>
  )
}

// 모르드개의 발각 (에 2:21-23)
function MordecaiPlotScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M14 54 v-24 M32 54 v-24 M11 30 h24" {...sw(1.4, 0.55)} />
        <path d="M19 34 h6 m-6 8 h6" {...sw(1.1, 0.4)} />
      </g>
      {/* 대궐 문에 앉은 모르드개 — 주역 */}
      <g style={d(900, reduce)}>
        <circle cx="23" cy="38" r="2.8" {...sw(2.6)} />
        <path d="M23 40.8 q-1.5 4 -5 5 M15 54 l4.5 -6 M25 46 l2 7" {...sw(2.6)} />
      </g>
      {/* 빅단과 데레스 — 음모하는 두 내시 */}
      <g style={d(1800, reduce)}>
        <circle cx="65" cy="34" r="2.4" {...sw(2)} />
        <path d="M65 36.4 v8.6 M62 54 l3 -9 l3 9 M67 39 q3 -1 4 -3" {...sw(2)} />
        <circle cx="76" cy="35" r="2.3" {...sw(1.9, 0.9)} />
        <path d="M76 37.3 v8.2 M73 54 l3 -8.5 l3 8.5 M74 39.5 q-3 -1 -4 -3" {...sw(1.9, 0.9)} />
        <path d="M68 35 q3.5 -1 5 0.5" {...sw(1.3, 0.6)} />
      </g>
      {/* 알아채고 에스더에게 전함 — 핵심 */}
      <g style={d(2600, reduce)} stroke="var(--paper-accent)">
        <path d="M26 36 q3 -1.5 5 0.3" {...sw(1.5)} />
        <path d="M30 33 L54 20" {...sw(1.8)}>
          {!reduce && <animate attributeName="stroke-dashoffset" from="1" to="0" begin="2.6s" dur="0.8s" fill="freeze" />}
        </path>
        <path d="M50.5 20 v-2.6 l1.5 1.6 l1.4 -2.4 l1.4 2.4 l1.5 -1.6 v2.6 h-5.8" {...sw(2.2)} />
      </g>
      {/* 궁중 일기에 기록되다 */}
      <g style={d(3400, reduce)}>
        <path d="M92 46 q4 -2 8 0 q4 -2 8 0" {...sw(1.8)} />
        <path d="M92 50 q4 -2 8 0 q4 -2 8 0" {...sw(1.4, 0.7)} />
        <path d="M92 46 v4 M108 46 v4 M100 45.5 v4.5" {...sw(1.3)} />
      </g>
      <Label x="23" y="25" at="1.4" reduce={reduce}>모르드개</Label>
      <Label x="70" y="26" at="2.3" reduce={reduce} size="4.2">빅단과 데레스</Label>
      <Label x="60" y="61" at="3.9" reduce={reduce} size="4.2">궁중 일기에 기록되다</Label>
    </g>
  )
}

const SCENES = {
  'authored-daniel-babylon-diet': { Scene: BabylonDietScene, desc: '왕의 음식 대신 채식을 청하다', caption: '결단 — 다니엘 1장' },
  'authored-daniel-babylon-image-dream': { Scene: ImageDreamScene, desc: '뜨인 돌이 신상을 쳐서 부수다', caption: '신상 꿈 — 다니엘 2장' },
  'authored-daniel-babylon-tree-dream': { Scene: TreeDreamScene, desc: '하늘까지 닿은 나무가 베이다', caption: '나무 꿈 — 다니엘 4장' },
  'authored-daniel-babylon-four-beasts': { Scene: FourBeastsScene, desc: '바다에서 네 짐승이 올라오다', caption: '네 짐승 환상 — 다니엘 7장' },
  'authored-daniel-susa-vision': { Scene: SusaVisionScene, desc: '숫양과 숫염소가 부딪치다', caption: '수산 궁 환상 — 다니엘 8장' },
  'authored-daniel-babylon-writing-wall': { Scene: WritingWallScene, mood: 'dark', desc: '벽에 나타난 손가락이 글을 쓰다', caption: '벨사살의 밤 — 다니엘 5장' },
  'authored-daniel-babylon-darius-administrator': { Scene: DariusAdministratorScene, desc: '다리오가 다니엘을 총리로 세우다', caption: '총리 — 다니엘 6장' },
  'authored-daniel-babylon-lions-den': { Scene: LionsDenScene, desc: '하나님이 사자들의 입을 봉하시다', caption: '사자 굴 — 다니엘 6장' },
  'authored-daniel-babylon-seventy-weeks': { Scene: SeventyWeeksScene, desc: '금식하며 기도할 때 가브리엘이 이르다', caption: '칠십 이레 — 다니엘 9장' },
  'authored-daniel-tigris-vision': { Scene: TigrisVisionScene, desc: '히데겔 강가에서 마지막 계시를 받다', caption: '마지막 환상 — 다니엘 10-12장' },
  'authored-esther-queen-chosen': { Scene: QueenChosenScene, desc: '에스더가 왕후의 관을 쓰다', caption: '간택 — 에스더 2장' },
  'authored-esther-mordecai-plot': { Scene: MordecaiPlotScene, desc: '모르드개가 왕 암살 음모를 밝혀 궁중 일기에 기록되다', caption: '음모의 발각 — 에스더 2장' },
  'authored-esther-haman-decree': { Scene: HamanDecreeScene, mood: 'dark', desc: '유다인을 멸하라는 조서가 내리다', caption: '하만의 조서 — 에스더 3장' },
  'authored-esther-if-i-perish': { Scene: IfIPerishScene, desc: '죽으면 죽으리이다 — 왕 앞에 나아가다', caption: '결단 — 에스더 4장' },
  'authored-esther-haman-downfall': { Scene: HamanDownfallScene, desc: '자기가 세운 나무에 하만이 달리다', caption: '반전 — 에스더 7장' },
  'authored-esther-purim': { Scene: PurimScene, desc: '슬픔이 변하여 기쁜 날이 되다', caption: '부림절 — 에스더 9장' },
  'authored-nehemiah-news-prayer': { Scene: NewsPrayerScene, mood: 'dark', desc: '무너진 성벽 소식에 앉아서 울다', caption: '수산 궁 — 느헤미야 1장' },
  'authored-nehemiah-kings-permission': { Scene: KingsPermissionScene, desc: '왕이 조서와 재목을 허락하다', caption: '파견 — 느헤미야 2장' },
  'authored-nehemiah-night-inspection': { Scene: NightInspectionScene, desc: '밤에 무너진 성벽을 홀로 둘러보다', caption: '야간 시찰 — 느헤미야 2장' },
  'authored-nehemiah-wall-opposition': { Scene: WallOppositionScene, desc: '한 손에 병기를 잡고 성을 쌓다', caption: '재건 — 느헤미야 4장' },
  'authored-nehemiah-wall-completed': { Scene: WallCompletedScene, desc: '오십이 일 만에 성벽이 완공되다', caption: '완공 — 느헤미야 6장' },
  'authored-nehemiah-law-reading': { Scene: LawReadingScene, desc: '새벽부터 정오까지 율법을 낭독하다', caption: '수문 광장 — 느헤미야 8장' },
}

export default SCENES
