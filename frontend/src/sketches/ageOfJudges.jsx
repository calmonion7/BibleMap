// 사사들의 시대 — 17개 정차지 장면 (task#229, #227 표준)
import { sw, d, Label } from './lib'

// 다볼산 집결 (삿 4:12-14)
function TaborMusterScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M14 54 Q46 14 78 54" {...sw(2.2)} />
        <path d="M34 40 l5 -4 M60 38 l-5 -4" {...sw(1.2, 0.4)} />
      </g>
      {/* 산 위의 만 명 — 창들 */}
      <g style={d(1000, reduce)}>
        <path d="M40 28 l1.5 -8 M46 26 l1.5 -8 M52 27 l1.5 -8 M45 30 h10" {...sw(1.8)} />
        <path d="M41.5 20 l1 -2.4 M47.5 18 l1 -2.4 M53.5 19 l1 -2.4" {...sw(1.3)} />
      </g>
      {/* 아래 병거 — 시스라 군 */}
      <g style={d(2000, reduce)}>
        <circle cx="94" cy="49" r="4" {...sw(2)} />
        <path d="M94 45 v8 M90 49 h8 M91.2 46.2 l5.6 5.6 M96.8 46.2 l-5.6 5.6" {...sw(1.4)} />
        <path d="M99 46 h9 q2.5 0 3 2.5" {...sw(1.8)} />
        <circle cx="107" cy="50.5" r="3" {...sw(1.7, 0.8)} />
      </g>
      <g style={d(reduce ? 0 : 2900, reduce)} stroke="var(--paper-accent)">
        <path d="M47 10 v-3 m-1.5 1.5 h3" {...sw(1.4)} />
      </g>
      <Label x="46" y="38" at="1.5" reduce={reduce}>다볼산의 만 명</Label>
      <Label x="98" y="38" at="2.5" reduce={reduce}>철 병거 구백</Label>
    </g>
  )
}

// 기손 강 승리 (삿 4:15-16)
function KishonVictoryScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
      </g>
      {/* 비 */}
      <g style={d(800, reduce)}>
        <path d="M20 10 l-2.5 7 M44 8 l-2.5 7 M70 9 l-2.5 7 M96 10 l-2.5 7 M32 20 l-2.5 7 M58 18 l-2.5 7 M84 19 l-2.5 7" {...sw(1.3, 0.65)}>
          {!reduce && <animate attributeName="opacity" values="0.65;0.3;0.65" begin="1.6s" dur="0.8s" repeatCount="3" />}
        </path>
      </g>
      {/* 불어난 강 — 굽이치는 물결 */}
      <g style={d(1500, reduce)}>
        <path d="M6 44 q8 -4 16 0 q8 -4 16 0 q8 -4 16 0 q8 -4 16 0 q8 -4 16 0 q8 -4 16 0" {...sw(2.4)} />
        <path d="M12 49 q8 -3.5 16 0 q8 -3.5 16 0 q8 -3.5 16 0 q8 -3.5 16 0 q8 -3.5 16 0" {...sw(1.7, 0.7)} />
      </g>
      {/* 휩쓸린 병거 바퀴 — 뒤집힘 */}
      <g style={d(2400, reduce)}>
        <g transform={reduce ? 'rotate(38 60 43)' : undefined}>
          <circle cx="60" cy="43" r="4.2" {...sw(2.2)} />
          <path d="M60 38.8 v8.4 M55.8 43 h8.4 M57 40 l6 6 M63 40 l-6 6" {...sw(1.5)} />
          {!reduce && (
            <animateTransform attributeName="transform" type="rotate" from="0 60 43" to="38 60 43"
              begin="2.7s" dur="0.9s" fill="freeze" />
          )}
        </g>
        <path d="M76 46 l7 -3 m-1 4.5 l5 -4" {...sw(1.5, 0.7)} />
      </g>
      <Label x="24" y="36" at="1.9" reduce={reduce}>범람한 기손 강</Label>
      <Label x="62" y="59" at="3" reduce={reduce}>휩쓸린 병거</Label>
    </g>
  )
}

// 기드온의 부르심 (삿 6:11-32)
function GideonCallScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M84 44 q13 -8 26 -2" {...sw(1.1, 0.4)} />
      </g>
      {/* 포도주 틀 — 구덩이 */}
      <g style={d(800, reduce)}>
        <path d="M34 54 q-3 0 -3 -3 v-8 q0 -3 3 -3 h20 q3 0 3 3 v8 q0 3 -3 3" {...sw(2.2)} />
        <path d="M37 40 h14" {...sw(1.3, 0.5)} />
      </g>
      {/* 타작하는 기드온 — 웅크림 */}
      <g style={d(1600, reduce)}>
        <circle cx="43" cy="44" r="2.6" {...sw(2.5)} />
        <path d="M43 46.6 q-1.5 3 -1 5.4 M40 52 h7" {...sw(2.5)} />
        <path d="M45.5 46.5 l4.5 3 M50 49.5 l2.5 -1.5" {...sw(2)} />
        <path d="M38 48 q2 -1.5 3.5 -0.5" {...sw(1.3, 0.6)} />
      </g>
      {/* 상수리나무 아래 천사 */}
      <g style={d(2400, reduce)}>
        <path d="M84 54 q-1 -8 -1.5 -13 M82 41 q-7 -1 -8 -6 q5 -2 8 1.5 q1 -5.5 6 -5.5 q3 3 1.5 6.5 q6 -1 6.5 3.5 q-3 5 -9 3.5 q-2 1 -4.5 -3.5" {...sw(1.6, 0.75)} />
        <circle cx="94" cy="45" r="2.4" {...sw(2)} />
        <path d="M89.5 54 l2.2 -6.5 h4.6 l2.2 6.5" {...sw(2)} />
      </g>
      <Label x="43" y="33" at="2.1" reduce={reduce}>기드온</Label>
      <Label x="96" y="34" at="2.9" reduce={reduce}>여호와의 사자</Label>
      <Label x="44" y="60" at="1.2" reduce={reduce} size="4.2">포도주 틀의 타작</Label>
    </g>
  )
}

// 하롯 샘 300 선발 (삿 7:1-8)
function HarodSelectionScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M8 44 q12 -7 24 -2" {...sw(1.1, 0.4)} />
      </g>
      {/* 샘물 */}
      <g style={d(800, reduce)}>
        <path d="M40 52 q10 -3 20 0 q10 -3 20 0" {...sw(2)} />
        <path d="M46 49.5 q7 -2 14 0" {...sw(1.3, 0.55)} />
      </g>
      {/* 엎드려 마시는 자 — 돌려보냄 */}
      <g style={d(1600, reduce)}>
        <circle cx="26" cy="49" r="2.2" {...sw(1.7, 0.7)} />
        <path d="M28 50 q4 -1.5 7 0.5 M24 50.5 l-3.5 2.5" {...sw(1.7, 0.7)} />
      </g>
      {/* 손으로 핥는 300 — 무릎, 손 올림 */}
      <g style={d(2400, reduce)}>
        <circle cx="66" cy="41" r="2.6" {...sw(2.5)} />
        <path d="M66 43.6 l-1.2 4.4 M60.5 52 h9 M64.8 48 q-3 1.5 -4.3 4 M67.5 44.5 q2.5 -1.5 3 -4" {...sw(2.5)} />
        <circle cx="82" cy="42" r="2.4" {...sw(2.2)} />
        <path d="M82 44.4 l-1.2 4 M77 52 h8.5 M83.5 45 q2.3 -1.4 2.8 -3.8" {...sw(2.2)} />
      </g>
      <g style={d(reduce ? 0 : 3300, reduce)} stroke="var(--paper-accent)">
        <path d="M74 30 h2 m2.5 0 h2 m2.5 0 h2" {...sw(2)} />
      </g>
      <Label x="74" y="26" at="3.5" reduce={reduce}>남은 삼백 명</Label>
      <Label x="26" y="40" at="1.9" reduce={reduce} size="4.2">돌려보낸 자들</Label>
    </g>
  )
}

// 모레 산 야습 (삿 7:16-25)
function MorehVictoryScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M70 54 q10 -16 34 -14" {...sw(1.4, 0.5)} />
        <path d="M16 10 v2.4 m-1.2 -1.2 h2.4 M100 8 v2.4 m-1.2 -1.2 h2.4" {...sw(1.2, 0.6)} />
      </g>
      {/* 세 소품 — 나팔·항아리·횃불 */}
      <g style={d(1000, reduce)}>
        <path d="M20 40 q6 -2 10 1 l2 2 q1 1.5 -1 2 l-8 1 q-4 -1 -3 -6" {...sw(2.2)} />
        <path d="M40 46 q-1.5 -6 3 -7 q4.5 1 3 7 q-1 2.5 -3 2.5 q-2 0 -3 -2.5 M41.5 38.5 h3.5" {...sw(2.2)} />
        <path d="M56 48 v-8" {...sw(2)} />
        <path d="M56 38 q-2.2 -4 0 -7 q2.2 3 0 7" {...sw(2.8)} stroke="var(--paper-accent)" />
      </g>
      {/* 흩어지는 미디안 — 산개 */}
      <g style={d(2200, reduce)}>
        <g transform={reduce ? 'translate(7 -2)' : undefined}>
          <circle cx="86" cy="44" r="2" {...sw(1.8)} />
          <path d="M86 46 v3 M84.5 54 l1.5 -3.5 l1.5 3.5 M84 45 l-3 2" {...sw(1.8)} />
          {!reduce && <animateTransform attributeName="transform" type="translate" from="0 0" to="9 -2" begin="2.6s" dur="1.1s" fill="freeze" />}
        </g>
        <g transform={reduce ? 'translate(5 2)' : undefined}>
          <circle cx="98" cy="46" r="1.9" {...sw(1.7, 0.85)} />
          <path d="M98 47.9 v2.6 M96.6 54 l1.4 -2.8 l1.4 2.8 M100 47 l3 2" {...sw(1.7, 0.85)} />
          {!reduce && <animateTransform attributeName="transform" type="translate" from="0 0" to="6 3" begin="2.7s" dur="1.1s" fill="freeze" />}
        </g>
      </g>
      <Label x="40" y="29" at="1.5" reduce={reduce}>나팔·항아리·횃불</Label>
      <Label x="94" y="34" at="2.9" reduce={reduce}>패주하는 미디안</Label>
    </g>
  )
}

// 에봇의 올무 (삿 8:22-28)
function OphrahEphodScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M10 43 q12 -7 24 -2" {...sw(1.1, 0.4)} />
      </g>
      {/* 단 위의 금 에봇 — 핵심 */}
      <g style={d(1000, reduce)}>
        <path d="M52 54 h18 M55 54 v-5 h12 v5" {...sw(2)} />
        <path d="M56 49 v-12 q0 -2.5 2.5 -2.5 h5 q2.5 0 2.5 2.5 v12" {...sw(2.6)} stroke="var(--paper-accent)" />
        <path d="M58 38 h6 M58 42 h6 M59 34.5 q2 -2 4 0" {...sw(1.4)} stroke="var(--paper-accent)" />
      </g>
      {/* 절하는 무리 — 올무 */}
      <g style={d(2000, reduce)}>
        <circle cx="30" cy="48" r="2.2" {...sw(1.9)} />
        <path d="M32 49 q4.5 -1.5 7.5 1 M28 49.5 l-3.5 3" {...sw(1.9)} />
        <circle cx="92" cy="48.5" r="2.1" {...sw(1.8, 0.9)} />
        <path d="M90 49.5 q-4.5 -1.5 -7.5 1 M94 50 l3.5 3" {...sw(1.8, 0.9)} />
      </g>
      <Label x="61" y="27" at="1.6" reduce={reduce}>금 에봇</Label>
      <Label x="61" y="60" at="2.7" reduce={reduce} size="4.2">온 이스라엘의 올무가 되다</Label>
    </g>
  )
}

// 모압 우거 (룻 1:1-5)
function RuthMoabScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M78 44 q14 -8 28 -2" {...sw(1.1, 0.4)} />
      </g>
      {/* 세 무덤 표석 */}
      <g style={d(1000, reduce)}>
        <path d="M70 54 v-8 q0 -3 3 -3 q3 0 3 3 v8 M82 54 v-6.5 q0 -2.6 2.6 -2.6 q2.6 0 2.6 2.6 v6.5 M93 54 v-5.5 q0 -2.3 2.3 -2.3 q2.3 0 2.3 2.3 v5.5" {...sw(2)} />
      </g>
      {/* 나오미와 룻 — 주역 */}
      <g style={d(2000, reduce)}>
        <circle cx="28" cy="37" r="2.9" {...sw(2.5)} />
        <path d="M24 54 l2 -14 h4 l2 14 M24 54 h8" {...sw(2.5)} />
        <path d="M26.5 42 q-2 2 -2.5 4.5" {...sw(1.3, 0.6)} />
        <circle cx="40" cy="38.5" r="2.7" {...sw(2.3)} />
        <path d="M36.5 54 l1.8 -12.5 h3.4 l1.8 12.5 M36.5 54 h7" {...sw(2.3)} />
        <path d="M32 43 q4 2 6 -0.5" {...sw(1.8)} />
      </g>
      <Label x="34" y="28" at="2.5" reduce={reduce}>나오미와 룻</Label>
      <Label x="85" y="38" at="1.4" reduce={reduce}>모압의 무덤들</Label>
    </g>
  )
}

// 베들레헴 귀향 (룻 1:6-22)
function RuthReturnScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        {/* 베들레헴 원경 */}
        <path d="M88 54 v-6 h5 v6 m3 0 v-8 h5 v8 m3 0 v-5 h5 v5" {...sw(1.4, 0.55)} />
        <path d="M14 52 h3 m5 0.6 h3 m5 0.6 h3" {...sw(1.2, 0.5)} />
      </g>
      {/* 보리 이삭 — 추수의 시작 */}
      <g style={d(900, reduce)}>
        <path d="M74 54 v-8 M74 46 q-3 -1 -3.5 -4.5 q3.5 0 3.5 4.5 q0 -4.5 3.5 -4.5 q-0.5 3.5 -3.5 4.5 M80 54 v-6 M80 48 q-2.5 -1 -3 -3.5 q3 0 3 3.5" {...sw(1.5, 0.75)} />
      </g>
      {/* 함께 걷는 두 여인 — 핵심 */}
      <g transform={reduce ? 'translate(10 0)' : undefined} style={d(1700, reduce)}>
        <circle cx="40" cy="37" r="2.9" {...sw(2.5)} />
        <path d="M36.5 54 l1.8 -14 h3.4 l1.8 14 M36.5 54 h7" {...sw(2.5)} />
        <circle cx="51" cy="38" r="2.7" {...sw(2.4)} />
        <path d="M47.5 54 l1.8 -13 h3.4 l1.8 13 M47.5 54 h7" {...sw(2.4)} />
        <path d="M43 43 q2.5 1.5 4.5 0" {...sw(1.8)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="translate" from="0 0" to="12 0"
            begin="2.3s" dur="2.2s" fill="freeze" calcMode="spline" keySplines="0.3 0 0.7 1" keyTimes="0;1" />
        )}
      </g>
      <Label x="46" y="28" at="2.2" reduce={reduce}>룻과 나오미</Label>
      <Label x="97" y="40" at="1" reduce={reduce}>베들레헴</Label>
    </g>
  )
}

// 이삭줍기 (룻 2)
function RuthGleaningScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
      </g>
      {/* 보리밭 — 이삭들 */}
      <g style={d(800, reduce)}>
        <path d="M14 54 v-7 M14 47 q-2.5 -1 -3 -4 q3 0 3 4 M22 54 v-8 M22 46 q2.5 -1 3 -4 q-3 0 -3 4 M30 54 v-6.5 M30 47.5 q-2.5 -1 -3 -4 q3 0 3 4 M84 54 v-7 M84 47 q2.5 -1 3 -4 q-3 0 -3 4 M92 54 v-8 M92 46 q-2.5 -1 -3 -4 q3 0 3 4 M100 54 v-6 M100 48 q2.5 -1 3 -3.5 q-3 0 -3 3.5" {...sw(1.5, 0.75)} />
      </g>
      {/* 줍는 룻 — 허리 굽힘 */}
      <g style={d(1700, reduce)}>
        <circle cx="48" cy="42" r="2.7" {...sw(2.5)} />
        <path d="M50 43.5 q4 2 5 6 M55 49.5 l-1 4.5 M55 49.5 l4 4.5 M50.5 45.5 l-3.5 4 M46.5 50 l-1 4" {...sw(2.5)} />
        <path d="M45 51.5 h2.5 m1.5 0.6 h2.5" {...sw(1.3, 0.6)} />
      </g>
      {/* 보아스 — 지켜봄 */}
      <g style={d(2600, reduce)}>
        <circle cx="70" cy="35" r="2.8" {...sw(2.2)} />
        <path d="M70 37.8 v9.2 M67 54 l3 -7 l3 7 M67 41 q3 -1.5 6 0" {...sw(2.2)} />
      </g>
      <Label x="48" y="33" at="2.2" reduce={reduce}>룻</Label>
      <Label x="74" y="26" at="3.1" reduce={reduce}>보아스</Label>
    </g>
  )
}

// 기업 무름 (룻 4)
function RuthRedemptionScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        {/* 성문 아치 */}
        <path d="M20 54 v-22 q14 -12 28 0 v22 M26 54 v-17 q8 -7 16 0 v17" {...sw(2.2)} />
        <path d="M22 38 h4 m16 0 h4" {...sw(1.2, 0.45)} />
      </g>
      {/* 신 벗어 건넴 — 핵심 소품 */}
      <g style={d(1600, reduce)}>
        <path d="M62 44 q3 -2 6 0 q2 1.5 0.5 3 h-6 q-2 -1 -0.5 -3" {...sw(2.6)}>
          {!reduce && (
            <animateMotion path="M0 0 q7 -5 14 -2" begin="2.6s" dur="0.7s" fill="freeze"
              calcMode="spline" keySplines="0.3 0 0.7 1" keyTimes="0;1" />
          )}
        </path>
      </g>
      {/* 보아스와 친족 */}
      <g style={d(2200, reduce)}>
        <circle cx="62" cy="35" r="2.7" {...sw(2.4)} />
        <path d="M62 37.7 v9.3 M59 54 l3 -7 l3 7 M64.5 40 q3.5 -1 5.5 -3" {...sw(2.4)} />
        <circle cx="86" cy="35.5" r="2.6" {...sw(2.1)} />
        <path d="M86 38.1 v8.9 M83 54 l3 -7 l3 7 M83.5 40 q-3 -1 -5 -3" {...sw(2.1)} />
      </g>
      <Label x="34" y="26" at="1.2" reduce={reduce}>성문</Label>
      <Label x="74" y="60" at="3.1" reduce={reduce} size="4.2">신을 벗어 무르다</Label>
    </g>
  )
}

// 입다를 세움 (삿 11:4-11)
function JephthahSummonsScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M84 44 q13 -8 26 -2" {...sw(1.1, 0.4)} />
      </g>
      {/* 장로들 — 손 내밈 */}
      <g style={d(1000, reduce)}>
        <circle cx="34" cy="36" r="2.7" {...sw(2.2)} />
        <path d="M30.5 54 l1.8 -13 h3.4 l1.8 13 M30.5 54 h7 M36.5 40 q4 -1.5 7 0.5" {...sw(2.2)} />
        <circle cx="22" cy="37.5" r="2.5" {...sw(2, 0.9)} />
        <path d="M19 54 l1.5 -11.5 h3 l1.5 11.5 M19 54 h6" {...sw(2, 0.9)} />
      </g>
      {/* 입다 — 주역: 칼 찬 용사 */}
      <g style={d(2000, reduce)}>
        <circle cx="62" cy="34" r="3" {...sw(2.6)} />
        <path d="M62 37 v10 M58.5 54 l3.5 -7.5 l3.5 7.5" {...sw(2.6)} />
        <path d="M59.5 40 q-4 0 -6.5 -1.5" {...sw(2.3)} />
        <path d="M66 42 l3 9 M65 43.5 h4" {...sw(2)} />
        <path d="M60 43 q2 1.2 4 0" {...sw(1.3, 0.6)} />
      </g>
      <g style={d(reduce ? 0 : 3000, reduce)} stroke="var(--paper-accent)">
        <path d="M62 22 v-3 m-1.5 1.5 h3" {...sw(1.4)} />
      </g>
      <Label x="27" y="27" at="1.5" reduce={reduce}>길르앗 장로들</Label>
      <Label x="66" y="25" at="2.5" reduce={reduce}>입다</Label>
    </g>
  )
}

// 입다의 서원 (삿 11:29-31)
function JephthahVowScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M8 20 q16 6 30 4 M78 18 q16 5 30 8" {...sw(1.1, 0.4)} />
      </g>
      {/* 입다 홀로 — 팔 들어 서원 */}
      <g style={d(1200, reduce)}>
        <circle cx="58" cy="28" r="3.1" {...sw(2.6)} />
        <path d="M58 31.1 v13.4 M54.5 54 l3.5 -8.5 l3.5 8.5" {...sw(2.6)} />
        <path d="M58 34 q-4.5 -3 -5.5 -8 M58 34 q4.5 -3 5.5 -8" {...sw(2.4)} />
        <path d="M56 38.5 q2 1.2 4 0" {...sw(1.3, 0.6)} />
      </g>
      {/* 어두운 하늘 — 무거운 구름 */}
      <g style={d(2200, reduce)}>
        <path d="M20 12 q6 -4 12 0 q6 -4 12 0 M74 10 q6 -4 12 0 q6 -4 12 0" {...sw(1.5, 0.6)} />
      </g>
      <Label x="58" y="18" at="1.7" reduce={reduce}>입다의 서원</Label>
      <Label x="58" y="61" at="2.7" reduce={reduce} size="4.2">처음 나오는 자를 번제로</Label>
    </g>
  )
}

// 아로엘 대승 (삿 11:32-33)
function JephthahVictoryScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        {/* 스무 성읍 — 원경 성벽들 */}
        <path d="M70 54 v-5 h6 v5 m4 0 v-7 h6 v7 m4 0 v-4 h6 v4 m4 0 v-6 h6 v6" {...sw(1.4, 0.55)} />
        <path d="M72 47 l2 -2 M88 45 l2 -2" {...sw(1.1, 0.4)} />
      </g>
      {/* 진군 — 창 든 무리 전진 */}
      <g transform={reduce ? 'translate(10 0)' : undefined} style={d(1400, reduce)}>
        <path d="M20 50 l10 -5.5 M22 45 l10 -5 M18 42 l9 -4.5" {...sw(2.4)} />
        <path d="M30 44.5 l3 -1.6 M32 40 l3 -1.5 M27 37.5 l2.8 -1.4" {...sw(1.6)} />
        <circle cx="16" cy="46" r="2.2" {...sw(2)} />
        <path d="M16 48.2 v2.6 M14.3 54 l1.7 -3 l1.7 3" {...sw(2)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="translate" from="0 0" to="12 0"
            begin="2s" dur="1.6s" fill="freeze" calcMode="spline" keySplines="0.35 0 0.6 1" keyTimes="0;1" />
        )}
      </g>
      <Label x="88" y="36" at="1" reduce={reduce}>암몬 이십 성읍</Label>
      <Label x="26" y="30" at="2.3" reduce={reduce}>입다의 진군</Label>
    </g>
  )
}

// 입다의 딸 (삿 11:34-40)
function JephthahDaughterScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        {/* 집 문 */}
        <path d="M78 54 v-16 h22 v16 M84 54 v-10 h10 v10" {...sw(2)} />
      </g>
      {/* 소고 치며 나오는 딸 */}
      <g transform={reduce ? 'translate(-10 0)' : undefined} style={d(1200, reduce)}>
        <circle cx="70" cy="38" r="2.7" {...sw(2.4)} />
        <path d="M66.5 54 l1.8 -13 h3.4 l1.8 13 M66.5 54 h7" {...sw(2.4)} />
        <circle cx="63" cy="40" r="2.4" {...sw(1.9)} />
        <path d="M67.5 41 q-2 -1.5 -2.3 -1.3" {...sw(1.6)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="translate" from="0 0" to="-12 0"
            begin="1.8s" dur="1.6s" fill="freeze" calcMode="spline" keySplines="0.3 0 0.6 1" keyTimes="0;1" />
        )}
      </g>
      {/* 멈춰선 입다 — 고개 떨굼, 찢는 옷 */}
      <g transform={reduce ? 'rotate(7 30 46)' : undefined} style={d(2400, reduce)}>
        <circle cx="30" cy="35" r="3" {...sw(2.6)} />
        <path d="M30 38 v8.5 M27 54 l3 -7 l3 7" {...sw(2.6)} />
        <path d="M30 40 q-3.5 2 -4.5 6 M30 40 q3.5 2 4.5 6" {...sw(2.3)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="rotate" from="0 30 46" to="7 30 46"
            begin="3.2s" dur="0.7s" fill="freeze" />
        )}
      </g>
      <Label x="30" y="25" at="3.4" reduce={reduce}>입다</Label>
      <Label x="62" y="28" at="1.7" reduce={reduce}>소고 치는 딸</Label>
    </g>
  )
}

// 삼손 출생 예고 (삿 13:2-24)
function SamsonBirthScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M84 44 q13 -8 26 -2" {...sw(1.1, 0.4)} />
      </g>
      {/* 제단 불 */}
      <g style={d(800, reduce)}>
        <path d="M50 54 v-6 h16 v6 M48 48 h20" {...sw(2.2)} />
        <path d="M57 44.5 q-2.2 -4 0 -7 q2.2 3 0 7 M61 44.5 q-1.8 -4.5 0.5 -7" {...sw(2.6)} />
      </g>
      {/* 천사 — 불꽃 위로 상승 */}
      <g transform={reduce ? 'translate(0 -16)' : undefined} opacity={reduce ? 0.5 : 1} style={d(1600, reduce)}>
        <circle cx="59" cy="30" r="2.6" {...sw(2)} />
        <path d="M55.5 40 l1.7 -7.5 h3.6 l1.7 7.5 M55.5 40 h7.6" {...sw(2)} />
        <path d="M55 32 q-4 -2 -5 -5.5 M63 32 q4 -2 5 -5.5" {...sw(1.6)} />
        {!reduce && (
          <>
            <animateTransform attributeName="transform" type="translate" from="0 0" to="0 -17"
              begin="2.4s" dur="1.6s" fill="freeze" calcMode="spline" keySplines="0.35 0 0.6 1" keyTimes="0;1" />
            <animate attributeName="opacity" from="1" to="0.4" begin="3.3s" dur="0.8s" fill="freeze" />
          </>
        )}
      </g>
      {/* 엎드린 마노아 부부 */}
      <g style={d(2800, reduce)}>
        <circle cx="26" cy="48.5" r="2.3" {...sw(2)} />
        <path d="M28 49.5 q4.5 -1.6 7.5 1 M24 50 l-3.5 3" {...sw(2)} />
        <circle cx="90" cy="49" r="2.2" {...sw(1.9)} />
        <path d="M88 50 q-4.5 -1.6 -7.5 1 M92 50.5 l3.5 3" {...sw(1.9)} />
      </g>
      <Label x="59" y="12" at="3.6" reduce={reduce}>불꽃 위의 사자</Label>
      <Label x="26" y="39" at="3.2" reduce={reduce}>마노아 부부</Label>
    </g>
  )
}

// 소렉의 들릴라 (삿 16:4-22)
function SorekDelilahScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M8 22 q20 8 38 5 M74 20 q20 6 36 10" {...sw(1.2, 0.45)} />
      </g>
      {/* 잠든 삼손 — 무릎 위 */}
      <g style={d(1000, reduce)}>
        <circle cx="52" cy="44" r="3" {...sw(2.5)} />
        <path d="M55 44.5 q9 1.5 18 1 M74 45.5 l7 1" {...sw(2.5)} />
        <path d="M49.5 42 q-3 -2.5 -3 -6 M51 41 q-1.5 -3 -0.5 -6 M54 41.5 q1 -3 3 -4.5" {...sw(1.8)} />
      </g>
      {/* 들릴라 — 가위 든 손 */}
      <g style={d(2000, reduce)}>
        <circle cx="38" cy="32" r="2.8" {...sw(2.2)} />
        <path d="M34.5 48 l1.7 -13 h3.6 l1.7 13" {...sw(2.2)} />
        <path d="M41 36 q4 1.5 6.5 4" {...sw(2)} />
      </g>
      {/* 가위 — 핵심 */}
      <g style={d(2800, reduce)}>
        <path d="M48 39 l6 -4 m-6 0 l6 4 M47 34.5 a1.6 1.6 0 1 0 0.1 0 M47 39.5 a1.6 1.6 0 1 0 0.1 0" {...sw(2.4)} stroke="var(--paper-accent)" />
      </g>
      <Label x="38" y="23" at="2.5" reduce={reduce}>들릴라</Label>
      <Label x="66" y="36" at="1.4" reduce={reduce}>잠든 삼손</Label>
      <Label x="60" y="61" at="3.2" reduce={reduce} size="4.2">머리털과 함께 힘이 떠나다</Label>
    </g>
  )
}

// 가사 신전 (삿 16:23-31)
function GazaDeathScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M30 16 h60 M26 19 h68" {...sw(2.2)} />
        <path d="M36 16 l-2 -4 h52 l-2 4" {...sw(1.4, 0.6)} />
      </g>
      {/* 두 기둥 — 기울어짐 */}
      <g style={d(900, reduce)}>
        <g transform={reduce ? 'rotate(-7 46 54)' : undefined}>
          <path d="M46 54 V19" {...sw(2.8)} />
          <path d="M43.5 22 h5" {...sw(1.4)} />
          {!reduce && (
            <animateTransform attributeName="transform" type="rotate" from="0 46 54" to="-7 46 54"
              begin="3.2s" dur="0.7s" fill="freeze" />
          )}
        </g>
        <g transform={reduce ? 'rotate(7 74 54)' : undefined}>
          <path d="M74 54 V19" {...sw(2.8)} />
          <path d="M71.5 22 h5" {...sw(1.4)} />
          {!reduce && (
            <animateTransform attributeName="transform" type="rotate" from="0 74 54" to="7 74 54"
              begin="3.2s" dur="0.7s" fill="freeze" />
          )}
        </g>
      </g>
      {/* 팔 벌린 삼손 — 기둥 사이 */}
      <g style={d(1900, reduce)}>
        <circle cx="60" cy="34" r="3" {...sw(2.6)} />
        <path d="M60 37 v9.5 M56.5 54 l3.5 -7.5 l3.5 7.5" {...sw(2.6)} />
        <path d="M60 38.5 q-6.5 -1.5 -12 -6 M60 38.5 q6.5 -1.5 12 -6" {...sw(2.4)} />
      </g>
      {/* 지붕 균열 */}
      <g style={d(reduce ? 0 : 3400, reduce)}>
        <path d="M56 16 l3 -5 M62 16 l-2 -4.5 M50 16 l2 -4" {...sw(1.4, 0.7)} />
      </g>
      <Label x="60" y="26" at="2.4" reduce={reduce}>삼손</Label>
      <Label x="60" y="61" at="3.6" reduce={reduce} size="4.2">다곤 신전의 마지막 기도</Label>
    </g>
  )
}

const SCENES = {
  'authored-deborah-tabor-muster': { Scene: TaborMusterScene, desc: '다볼산에 만 명이 진을 치다', caption: '집결 — 사사기 4장' },
  'authored-deborah-kishon-victory': { Scene: KishonVictoryScene, desc: '기손 강이 시스라의 병거를 휩쓸다', caption: '기손 강 — 사사기 4장' },
  'authored-gideon-ophrah-call': { Scene: GideonCallScene, desc: '포도주 틀의 겁쟁이를 큰 용사라 부르시다', caption: '부르심 — 사사기 6장' },
  'authored-gideon-harod-selection': { Scene: HarodSelectionScene, desc: '물을 핥은 삼백 명만 남기시다', caption: '하롯 샘 — 사사기 7장' },
  'authored-gideon-moreh-victory': { Scene: MorehVictoryScene, desc: '횃불과 나팔에 미디안이 무너지다', caption: '야습 — 사사기 7장' },
  'authored-gideon-ophrah-ephod': { Scene: OphrahEphodScene, mood: 'dark', desc: '전리품 금이 온 이스라엘의 올무가 되다', caption: '에봇 — 사사기 8장' },
  'authored-ruth-moab-sojourn': { Scene: RuthMoabScene, mood: 'dark', desc: '기근과 죽음이 모압 땅에 두 여인을 남기다', caption: '모압 우거 — 룻기 1장' },
  'authored-ruth-bethlehem-return': { Scene: RuthReturnScene, desc: '어머니의 하나님이 나의 하나님 — 함께 돌아오다', caption: '귀향 — 룻기 1장' },
  'authored-ruth-bethlehem-gleaning': { Scene: RuthGleaningScene, desc: '보아스의 밭에서 이삭을 줍다', caption: '이삭줍기 — 룻기 2장' },
  'authored-ruth-bethlehem-redemption': { Scene: RuthRedemptionScene, desc: '성문에서 기업 무름이 이루어지다', caption: '기업 무름 — 룻기 4장' },
  'authored-jephthah-mizpah-summons': { Scene: JephthahSummonsScene, desc: '쫓겨난 자를 머리로 세우다', caption: '입다 — 사사기 11장' },
  'authored-jephthah-mizpah-vow': { Scene: JephthahVowScene, mood: 'dark', desc: '승리를 흥정하는 서원을 입에 담다', caption: '서원 — 사사기 11장' },
  'authored-jephthah-aroer-victory': { Scene: JephthahVictoryScene, desc: '아로엘에서 암몬 이십 성읍을 치다', caption: '대승 — 사사기 11장' },
  'authored-jephthah-mizpah-daughter': { Scene: JephthahDaughterScene, mood: 'dark', desc: '소고 치며 나온 것은 무남독녀였다', caption: '입다의 딸 — 사사기 11장' },
  'authored-samson-zorah-birth': { Scene: SamsonBirthScene, desc: '제단 불꽃 위로 천사가 올라가다', caption: '출생 예고 — 사사기 13장' },
  'authored-samson-sorek-delilah': { Scene: SorekDelilahScene, mood: 'dark', desc: '머리털과 함께 힘이 떠나다', caption: '소렉 골짜기 — 사사기 16장' },
  'authored-samson-gaza-death': { Scene: GazaDeathScene, mood: 'dark', desc: '기둥을 무너뜨려 마지막 승리를 거두다', caption: '가사 신전 — 사사기 16장' },
}

export default SCENES
