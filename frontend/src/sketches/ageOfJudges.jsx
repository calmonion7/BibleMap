// 사사들의 시대 — 17개 정차지 장면 (task#229, #227 표준)
import { sw, d } from './lib'
import { Label } from './SceneLabel'

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

// 벧엘의 재판석 (삿 4:4-5)
function DeborahJudgingScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        {/* 압제의 원경 — 야빈의 병거 그림자 */}
        <circle cx="104" cy="49.5" r="2.6" {...sw(1.3, 0.35)} />
        <path d="M104 46 v7 M100.5 49.5 h7" {...sw(1.3, 0.35)} />
      </g>
      {/* 드보라의 종려나무 */}
      <g style={d(900, reduce)}>
        <path d="M40 54 q-1 -10 1 -18" {...sw(2)} />
        <path d="M41 36 q-7 -4 -12 -2 M41 36 q-7 1 -11 6 M41 36 q6 -5 12 -3 M41 36 q7 0 11 5 M41 36 q1 -6 -2 -10 M41 36 q3 -5 7 -8" {...sw(1.4, 0.75)} />
      </g>
      {/* 앉은 드보라 — 재판석 */}
      <g style={d(1800, reduce)}>
        <circle cx="40" cy="44" r="2.6" {...sw(2.4)} />
        <path d="M40 46.6 q-0.5 4 0 7.4 M37 54 q3 -3 6 0" {...sw(2.4)} />
        <path d="M37.5 48 q-2.5 1 -3 3.5" {...sw(1.8)} />
      </g>
      {/* 재판을 구하는 자 */}
      <g style={d(2700, reduce)}>
        <circle cx="70" cy="46" r="2.2" {...sw(1.8, 0.85)} />
        <path d="M67 54 l1.7 -6 h3 l1.7 6" {...sw(1.8, 0.85)} />
      </g>
      <Label x="40" y="34" at="2.3" reduce={reduce}>드보라의 종려나무</Label>
      <Label x="70" y="38" at="3.2" reduce={reduce} size="4.2">재판을 구하는 자</Label>
    </g>
  )
}

// 바락을 세움 (삿 4:6-9)
function DeborahSummonsScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M84 54 q10 -14 24 0" {...sw(1.2, 0.45)} />
      </g>
      {/* 드보라 — 명을 전하다, 팔을 뻗음 */}
      <g style={d(900, reduce)}>
        <circle cx="34" cy="35" r="2.8" {...sw(2.5)} />
        <path d="M34 37.8 v11 M30.5 54 l3.5 -6.6 l3.5 6.6" {...sw(2.5)} />
        <path d="M36.5 40 q6 -1 10 2" {...sw(2.2)} />
      </g>
      {/* 바락 — 머뭇거림 */}
      <g style={d(1900, reduce)}>
        <circle cx="60" cy="37" r="2.7" {...sw(2.2, 0.9)} />
        <path d="M60 39.7 v9.8 M56.7 54 l3.3 -6.5 l3.3 6.5" {...sw(2.2, 0.9)} />
        <path d="M58 42 q-2.5 1.5 -3 4" {...sw(1.7, 0.85)} />
      </g>
      <g style={d(reduce ? 0 : 2900, reduce)} stroke="var(--paper-accent)">
        <path d="M55 26 v-3 m-1.5 1.5 h3" {...sw(1.4)} />
      </g>
      <Label x="34" y="25" at="1.8" reduce={reduce}>드보라</Label>
      <Label x="60" y="27" at="2.8" reduce={reduce}>바락</Label>
    </g>
  )
}

// 야엘의 장막 (삿 4:17-22)
function JaelTentScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        {/* 장막 */}
        <path d="M70 54 l14 -16 l14 16 M76 54 v-9 M92 54 v-9" {...sw(2.2)} />
      </g>
      {/* 누운 시스라 — 지친 패주자 */}
      <g style={d(1000, reduce)}>
        <path d="M74 49 h13 M74 49 q-1.5 0 -1.5 2 t1.5 2 M87 49 q1 2 -1 4" {...sw(2.3)} />
      </g>
      {/* 야엘 — 곁에 서다 */}
      <g style={d(2000, reduce)}>
        <circle cx="60" cy="38" r="2.7" {...sw(2.4)} />
        <path d="M60 40.7 v9.3 M56.8 54 l3.2 -6 l3.2 6" {...sw(2.4)} />
        <path d="M62 41 q4 -1 6 2" {...sw(2)} />
      </g>
      {/* 장막 말뚝 — 핵심 */}
      <g style={d(2800, reduce)} stroke="var(--paper-accent)">
        <path d="M66 40 l4 4" {...sw(2.4)} />
      </g>
      <Label x="60" y="28" at="2.3" reduce={reduce}>야엘</Label>
      <Label x="80" y="60" at="3.1" reduce={reduce} size="4.2">여인의 손에 파하시다</Label>
    </g>
  )
}

// 드보라의 노래 (삿 5장)
function DeborahSongScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M10 16 q18 6 34 3 M76 14 q18 5 34 9" {...sw(1.1, 0.4)} />
      </g>
      {/* 드보라 — 찬양, 팔을 들다 */}
      <g style={d(1000, reduce)}>
        <circle cx="46" cy="33" r="2.8" {...sw(2.5)} />
        <path d="M46 35.8 v11.2 M42.5 54 l3.5 -7 l3.5 7" {...sw(2.5)} />
        <path d="M46 37 q-4.5 -3 -5.5 -7.5 M46 37 q4.5 -3 5.5 -7.5" {...sw(2.2)} />
      </g>
      {/* 바락 — 함께 찬양 */}
      <g style={d(2000, reduce)}>
        <circle cx="60" cy="35" r="2.6" {...sw(2.2, 0.9)} />
        <path d="M60 37.6 v9.4 M57 54 l3 -7 l3 7" {...sw(2.2, 0.9)} />
        <path d="M60 39 q-4 -2.5 -5 -6.5 M60 39 q4 -2.5 5 -6.5" {...sw(1.8, 0.85)} />
      </g>
      {/* 노래의 표 — 오르는 소리 */}
      <g style={d(2900, reduce)} stroke="var(--paper-accent)">
        <path d="M52 20 q1 -3 0 -5 M56 18 q1 -3 0 -5" {...sw(1.4)} />
      </g>
      <Label x="53" y="24" at="2.3" reduce={reduce}>드보라와 바락의 노래</Label>
      <Label x="53" y="60" at="3.3" reduce={reduce} size="4.2">사십 년의 평온</Label>
    </g>
  )
}

// 양털 표징 (삿 6:36-40)
function GideonFleeceScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
      </g>
      {/* 양털 — 땅 위에 놓이다 */}
      <g style={d(900, reduce)}>
        <path d="M38 54 q-4 -0.5 -4 -3.5 q0 -3 4 -3 q1 -2 4 -1 q3 -1.5 5 0.5 q3 -1 4 1.5 q0.5 3 -3 3.5 q0 2.5 -3 2.5 q-4 0.5 -7 -0.5" {...sw(2.2)} />
      </g>
      {/* 이슬 방울 — 마른 땅 위 */}
      <g style={d(1700, reduce)}>
        <path d="M30 51 q0.5 -1.3 1 0 q0.5 1.3 -0.5 1.4 q-1 -0.1 -0.5 -1.4 M58 50 q0.5 -1.3 1 0 q0.5 1.3 -0.5 1.4 q-1 -0.1 -0.5 -1.4" {...sw(1.3, 0.7)} />
      </g>
      {/* 기드온 — 짜내는 웅크림 */}
      <g style={d(2500, reduce)}>
        <circle cx="66" cy="41" r="2.6" {...sw(2.4)} />
        <path d="M66 43.6 q-1.5 3 -1 5.4 M62 51 h7" {...sw(2.4)} />
        <path d="M63.5 44.5 l-6 3 M56 49 l-2.5 -1.2" {...sw(2)} />
      </g>
      {/* 그릇 — 짜낸 물 한 그릇 */}
      <g style={d(reduce ? 0 : 3200, reduce)}>
        <path d="M48 52 q3 2 6 0" {...sw(1.6)} />
      </g>
      <Label x="46" y="34" at="1.7" reduce={reduce}>양털</Label>
      <Label x="66" y="30" at="2.9" reduce={reduce}>기드온</Label>
    </g>
  )
}

// 숙곳의 냉대 (삿 8:4-9)
function GideonSuccothScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        {/* 요단 강 물결 */}
        <path d="M10 50 q6 -2.5 12 0 q6 -2.5 12 0" {...sw(1.7, 0.7)} />
      </g>
      {/* 지친 삼백 — 행군 */}
      <g transform={reduce ? 'translate(8 0)' : undefined} style={d(1000, reduce)}>
        <circle cx="42" cy="45" r="2.3" {...sw(2, 0.9)} />
        <path d="M39.2 54 l1.7 -6.6 h3 l1.7 6.6" {...sw(2, 0.9)} />
        <path d="M52 47 l7 -3 M54 44 l6 -2.5" {...sw(1.7, 0.75)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="translate" from="0 0" to="8 0"
            begin="2.6s" dur="1.2s" fill="freeze" />
        )}
      </g>
      {/* 숙곳 방백들 — 등 돌림 */}
      <g style={d(2000, reduce)}>
        <circle cx="86" cy="42" r="2.6" {...sw(2.2)} />
        <path d="M83 54 l1.9 -8.5 h3.4 l1.9 8.5 M89 45 q2.5 0.5 3 2.5" {...sw(2.2)} />
        <circle cx="98" cy="43" r="2.4" {...sw(2, 0.9)} />
        <path d="M95.3 54 l1.8 -7.5 h3 l1.8 7.5" {...sw(2, 0.9)} />
      </g>
      {/* 거절당한 떡 */}
      <g style={d(2800, reduce)}>
        <path d="M78 52 q3 -1.5 6 0 q1.5 1.5 -0.5 2.5 h-5 q-2 -1 -0.5 -2.5" {...sw(1.8)} />
      </g>
      <Label x="42" y="35" at="1.7" reduce={reduce}>지친 삼백</Label>
      <Label x="92" y="32" at="2.7" reduce={reduce}>숙곳의 방백들</Label>
    </g>
  )
}

// 브누엘 추격 (삿 8:10-21)
function GideonPenuelScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M8 46 q10 -6 20 -1" {...sw(1.1, 0.4)} />
      </g>
      {/* 사로잡힌 두 왕 — 결박 */}
      <g style={d(1000, reduce)}>
        <circle cx="72" cy="45" r="2.3" {...sw(2, 0.9)} />
        <path d="M70 54 l1.5 -6.5 h2.6 l1.5 6.5 M70.5 49 h3.5" {...sw(2, 0.9)} />
        <circle cx="84" cy="45.5" r="2.2" {...sw(1.9, 0.85)} />
        <path d="M82 54 l1.4 -6 h2.4 l1.4 6 M82.5 49.5 h3" {...sw(1.9, 0.85)} />
      </g>
      {/* 기드온 — 원수를 갚다 */}
      <g style={d(2000, reduce)}>
        <circle cx="46" cy="33" r="2.9" {...sw(2.6)} />
        <path d="M46 35.9 v10.6 M42.5 54 l3.5 -7.5 l3.5 7.5" {...sw(2.6)} />
        <path d="M48.5 40 l4.5 -6 M48 39.5 h4" {...sw(2.2)} />
      </g>
      <Label x="46" y="25" at="2.3" reduce={reduce}>기드온</Label>
      <Label x="78" y="35" at="1.7" reduce={reduce}>세바와 살문나</Label>
      <Label x="46" y="60" at="3" reduce={reduce} size="4.2">다볼의 형제들, 원수를 갚다</Label>
    </g>
  )
}

// 타작마당의 밤 (룻 3장)
function RuthThreshingScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        {/* 밤 — 달 */}
        <path d="M96 14 q4 -3 8 0 q-2 4 -8 0" {...sw(1.6, 0.7)} />
      </g>
      {/* 타작마당 — 곡식 더미 */}
      <g style={d(900, reduce)}>
        <path d="M60 54 q-6 0 -6 -5 q0 -4 6 -4 q6 -1 6 4 q0 5 -6 5" {...sw(1.8, 0.8)} />
      </g>
      {/* 잠든 보아스 */}
      <g style={d(1800, reduce)}>
        <path d="M40 50 h20 M40 50 q-1.5 0 -1.5 2 t1.5 2 M60 50 q1.5 0 1.5 2 t-1.5 2" {...sw(2.4)} />
        <circle cx="38" cy="48" r="2.3" {...sw(2.4)} />
      </g>
      {/* 룻 — 발치에 눕다 */}
      <g style={d(2600, reduce)}>
        <path d="M62 52 h12 M62 52 q-1.2 0 -1.2 1.6 t1.2 1.6" {...sw(2)} />
        <circle cx="76" cy="51" r="1.9" {...sw(2)} />
      </g>
      <Label x="38" y="38" at="1.9" reduce={reduce}>보아스</Label>
      <Label x="76" y="42" at="2.9" reduce={reduce}>룻</Label>
      <Label x="60" y="61" at="3.2" reduce={reduce} size="4.2">옷자락으로 덮으소서</Label>
    </g>
  )
}

// 사무엘의 봉헌 (삼상 1장)
function SamuelDedicationScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        {/* 실로 성막 */}
        <path d="M80 54 v-14 h26 v14 M84 40 h18" {...sw(1.6, 0.6)} />
      </g>
      {/* 한나 — 아이를 이끌다 */}
      <g style={d(1000, reduce)}>
        <circle cx="28" cy="35" r="2.8" {...sw(2.4)} />
        <path d="M28 37.8 v11 M24.5 54 l3.5 -6.6 l3.5 6.6" {...sw(2.4)} />
        <path d="M30.5 42 q3.5 1 5 3.5" {...sw(1.9)} />
      </g>
      {/* 어린 사무엘 */}
      <g style={d(1900, reduce)}>
        <circle cx="40" cy="45" r="1.8" {...sw(1.9)} />
        <path d="M40 46.8 v5.7 M37.6 54 l2.4 -4.2 l2.4 4.2" {...sw(1.9)} />
      </g>
      {/* 엘리 — 받아들이다 */}
      <g style={d(2700, reduce)}>
        <circle cx="60" cy="34" r="2.9" {...sw(2.2, 0.9)} />
        <path d="M60 36.9 v10.5 M56.5 54 l3.5 -6.6 l3.5 6.6" {...sw(2.2, 0.9)} />
        <path d="M57.5 41 q-3.5 1 -5 3.5" {...sw(1.7, 0.85)} />
      </g>
      <Label x="28" y="25" at="1.7" reduce={reduce}>한나</Label>
      <Label x="60" y="24" at="3" reduce={reduce}>엘리</Label>
      <Label x="40" y="58" at="2.4" reduce={reduce} size="4.2">평생을 여호와께 드리다</Label>
    </g>
  )
}

// 사무엘의 부르심 (삼상 3장)
function SamuelCallingScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M100 14 q4 -3 8 0 q-2 4 -8 0" {...sw(1.6, 0.7)} />
      </g>
      {/* 누운 소년 사무엘 */}
      <g style={d(1000, reduce)}>
        <path d="M36 50 h18 M36 50 q-1.4 0 -1.4 1.8 t1.4 1.8" {...sw(2.4)} />
        <circle cx="34" cy="47.5" r="2" {...sw(2.4)} />
      </g>
      {/* 부르시는 음성 — 세 번 */}
      <g style={d(1900, reduce)} stroke="var(--paper-accent)">
        <path d="M60 34 q4 -1 7 0.5 M60 38 q4 -1 7 0.5 M60 42 q4 -1 7 0.5" {...sw(1.4, 0.8)} />
      </g>
      {/* 엘리에게 달려가 응답 */}
      <g style={d(2700, reduce)}>
        <circle cx="90" cy="33" r="2.8" {...sw(2.1, 0.9)} />
        <path d="M90 35.8 v10.6 M86.6 54 l3.4 -7.6 l3.4 7.6" {...sw(2.1, 0.9)} />
        <path d="M87.5 40 q-3.5 1 -5 3.5" {...sw(1.6, 0.85)} />
      </g>
      <Label x="34" y="41" at="1.7" reduce={reduce}>어린 사무엘</Label>
      <Label x="90" y="24" at="2.9" reduce={reduce}>엘리</Label>
      <Label x="60" y="60" at="3.2" reduce={reduce} size="4.2">말씀하옵소서 듣겠나이다</Label>
    </g>
  )
}

// 돕 땅의 추방자 (삿 11:1-3)
function JephthahExileScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
      </g>
      {/* 형제들 — 내쫓다 */}
      <g style={d(900, reduce)}>
        <circle cx="30" cy="34" r="2.6" {...sw(2.1, 0.9)} />
        <path d="M30 36.6 v10 M26.7 54 l3.3 -7.4 l3.3 7.4" {...sw(2.1, 0.9)} />
        <path d="M32.5 40 q4 0 6 -2" {...sw(1.7, 0.85)} />
        <circle cx="18" cy="35.5" r="2.4" {...sw(2, 0.85)} />
        <path d="M15 54 l1.8 -9.5 h3 l1.8 9.5" {...sw(2, 0.85)} />
      </g>
      {/* 떠나는 입다 */}
      <g transform={reduce ? 'translate(38 0)' : undefined} style={d(1800, reduce)}>
        <circle cx="54" cy="33" r="2.8" {...sw(2.4)} />
        <path d="M54 35.8 v10.4 M50.6 54 l3.4 -7.4 l3.4 7.4" {...sw(2.4)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="translate" from="0 0" to="40 0"
            begin="2.7s" dur="1.6s" fill="freeze" calcMode="spline" keySplines="0.3 0 0.7 1" keyTimes="0;1" />
        )}
      </g>
      {/* 돕 땅 잡류 — 우두머리 */}
      <g style={d(2900, reduce)}>
        <circle cx="100" cy="42" r="2" {...sw(1.7, 0.75)} />
        <path d="M98 54 l1.4 -8 h2.4 l1.4 8" {...sw(1.7, 0.75)} />
        <circle cx="108" cy="44" r="1.8" {...sw(1.5, 0.65)} />
        <path d="M106.3 54 l1.2 -7 h2 l1.2 7" {...sw(1.5, 0.65)} />
      </g>
      <Label x="24" y="26" at="1.6" reduce={reduce}>형제들이 내쫓다</Label>
      <Label x="98" y="34" at="3.1" reduce={reduce}>돕 땅의 잡류</Label>
    </g>
  )
}

// 쉽볼렛 (삿 12장)
function ShibbolethScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        {/* 요단 나루 */}
        <path d="M46 54 q7 -3 14 0 q7 -3 14 0" {...sw(2, 0.75)} />
      </g>
      {/* 나루를 막은 길르앗 사람 */}
      <g style={d(1000, reduce)}>
        <circle cx="40" cy="36" r="2.8" {...sw(2.4)} />
        <path d="M40 38.8 v9.6 M36.6 54 l3.4 -5.6 l3.4 5.6" {...sw(2.4)} />
        <path d="M42.5 42 l6 -1" {...sw(2)} />
      </g>
      {/* 건너려는 에브라임 사람 */}
      <g transform={reduce ? 'translate(-4 1)' : undefined} style={d(2000, reduce)}>
        <circle cx="74" cy="38" r="2.6" {...sw(2, 0.85)} />
        <path d="M74 40.6 v8.4 M71 54 l3 -5 l3 5" {...sw(2, 0.85)} />
        <path d="M71.5 43 q-3 0.5 -5 -0.5" {...sw(1.6, 0.7)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="translate" from="0 0" to="-4 1"
            begin="3s" dur="0.6s" fill="freeze" />
        )}
      </g>
      <g style={d(reduce ? 0 : 2900, reduce)} stroke="var(--paper-accent)">
        <path d="M54 26 h3 m2.5 0 h3" {...sw(1.6)} />
      </g>
      <Label x="55" y="22" at="3.1" reduce={reduce}>쉽볼렛</Label>
      <Label x="40" y="27" at="1.7" reduce={reduce}>길르앗 사람</Label>
      <Label x="80" y="60" at="2.7" reduce={reduce} size="4.2">사만 이천 명이 엎드러지다</Label>
    </g>
  )
}

// 딤나의 수수께끼 (삿 14장)
function SamsonRiddleScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
      </g>
      {/* 사자 — 찢기다 */}
      <g style={d(900, reduce)}>
        <path d="M20 54 q-3 -1 -3 -4 q0 -3 3 -3 q1 -2.5 4 -1.5 q1 -3 4 -0.5 q3 0 2 3 q2 1.5 -0.5 3.5 q0.5 3 -3 2.5 q-3.5 1 -6.5 -0.5" {...sw(2.3)} />
      </g>
      {/* 삼손 — 맨손으로 */}
      <g style={d(1800, reduce)}>
        <circle cx="40" cy="34" r="3" {...sw(2.6)} />
        <path d="M40 37 v9 M36.5 54 l3.5 -8 l3.5 8" {...sw(2.6)} />
        <path d="M37 40 l-9 6 M28.5 46 l7 0" {...sw(2.3)} />
      </g>
      {/* 꿀 — 사자 몸의 벌집 */}
      <g style={d(2600, reduce)}>
        <path d="M18 50 q1.5 -2 3 0 q1.5 -2 3 0" {...sw(1.4, 0.7)} />
      </g>
      {/* 혼인 잔치 — 눈물의 신부 */}
      <g style={d(3200, reduce)}>
        <circle cx="90" cy="36" r="2.6" {...sw(2, 0.85)} />
        <path d="M90 38.6 v9.4 M86.6 54 l3.4 -6 l3.4 6" {...sw(2, 0.85)} />
        <path d="M88.5 41 q1 1.5 0.3 3" {...sw(1.2, 0.6)} />
      </g>
      <Label x="40" y="24" at="2.4" reduce={reduce}>삼손</Label>
      <Label x="90" y="26" at="3.6" reduce={reduce}>눈물의 신부</Label>
      <Label x="24" y="60" at="1.6" reduce={reduce} size="4.2">먹는 자에게서 먹는 것이 나오다</Label>
    </g>
  )
}

// 레히의 턱뼈 (삿 15장)
function SamsonJawboneScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
      </g>
      {/* 끊어지는 밧줄 */}
      <g style={d(900, reduce)}>
        <path d="M36 44 q3 -2 6 0 M36 48 q3 -2 6 0" {...sw(1.6, 0.7)} />
      </g>
      {/* 삼손 — 턱뼈를 들다 */}
      <g style={d(1700, reduce)}>
        <circle cx="46" cy="33" r="3" {...sw(2.6)} />
        <path d="M46 36 v10 M42.5 54 l3.5 -8 l3.5 8" {...sw(2.6)} />
        <path d="M49 38 l7 -6" {...sw(2.3)} />
        <g transform={reduce ? 'rotate(-25 58 33)' : undefined}>
          <path d="M56 32 q3 -1 5 1 q0.5 2 -2 2.5 q-3 0.5 -3 -3.5" {...sw(2.4)} stroke="var(--paper-accent)" />
          {!reduce && (
            <animateTransform attributeName="transform" type="rotate" from="0 58 33" to="-25 58 33"
              begin="2.6s" dur="0.5s" fill="freeze" />
          )}
        </g>
      </g>
      {/* 쓰러진 자들 */}
      <g style={d(2600, reduce)}>
        <path d="M78 52 h9 M78 52 q-1.2 0 -1.2 1.6 t1.2 1.6 M96 51 h8 M96 51 q-1.1 0 -1.1 1.5 t1.1 1.5" {...sw(1.7, 0.7)} />
      </g>
      {/* 엔학고레 샘 — 목마름의 응답 */}
      <g style={d(3300, reduce)}>
        <path d="M46 54 q0 -3 2 -3 q2 0 2 3" {...sw(1.6)} />
      </g>
      <Label x="46" y="24" at="2.1" reduce={reduce}>나귀 턱뼈</Label>
      <Label x="46" y="60" at="3.5" reduce={reduce} size="4.2">엔학고레 — 부르짖음에 응답한 샘</Label>
    </g>
  )
}

// 가사 성문 (삿 16:1-3)
function SamsonGateScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        {/* 헤브론 앞산 원경 */}
        <path d="M84 54 q10 -14 24 0" {...sw(1.2, 0.45)} />
        <path d="M96 12 q4 -3 8 0 q-2 4 -8 0" {...sw(1.4, 0.6)} />
      </g>
      {/* 성문 — 빗장째 들어 올리다 */}
      <g transform={reduce ? 'translate(0 -20)' : undefined} style={d(1000, reduce)}>
        <path d="M34 54 v-16 h24 v16 M34 46 h24" {...sw(2.4)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="translate" from="0 0" to="0 -20"
            begin="2.6s" dur="1s" fill="freeze" calcMode="spline" keySplines="0.3 0 0.7 1" keyTimes="0;1" />
        )}
      </g>
      {/* 삼손 — 짊어지다 */}
      <g style={d(1900, reduce)}>
        <circle cx="46" cy="35" r="3" {...sw(2.6)} />
        <path d="M46 38 v9 M42.5 54 l3.5 -7 l3.5 7" {...sw(2.6)} />
        <path d="M43 40 q-3 -2 -4 -4.5 M49 40 q3 -2 4 -4.5" {...sw(2.3)} />
      </g>
      <Label x="46" y="25" at="2.2" reduce={reduce}>삼손</Label>
      <Label x="46" y="60" at="3" reduce={reduce} size="4.2">성문을 빗장째 메고 오르다</Label>
    </g>
  )
}

// 에벤에셀 (삼상 7장)
function SamuelMizpahVictoryScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
      </g>
      {/* 금식하며 자백하는 백성 */}
      <g style={d(900, reduce)}>
        <circle cx="26" cy="46" r="2.2" {...sw(1.9, 0.85)} />
        <path d="M23.5 54 l1.4 -6 h2.2 l1.4 6" {...sw(1.9, 0.85)} />
        <circle cx="36" cy="45.5" r="2" {...sw(1.7, 0.75)} />
        <path d="M33.8 54 l1.3 -6.5 h2 l1.3 6.5" {...sw(1.7, 0.75)} />
      </g>
      {/* 진격하는 블레셋 — 흩어지다 */}
      <g transform={reduce ? 'translate(10 4)' : undefined} style={d(1800, reduce)}>
        <path d="M76 48 l8 -4 M80 46 l7 -3.5" {...sw(2, 0.8)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="translate" from="0 0" to="10 4"
            begin="3s" dur="0.9s" fill="freeze" />
        )}
      </g>
      {/* 큰 우레 */}
      <g style={d(2400, reduce)} stroke="var(--paper-accent)">
        <path d="M70 14 l-3 6 h4 l-3 6" {...sw(2.2)} />
      </g>
      {/* 에벤에셀 돌 */}
      <g style={d(3300, reduce)}>
        <path d="M54 54 v-9 q0 -2.5 3 -2.5 q3 0 3 2.5 v9" {...sw(2)} />
      </g>
      <Label x="30" y="37" at="1.7" reduce={reduce} size="4.2">범죄하였나이다</Label>
      <Label x="57" y="61" at="3.5" reduce={reduce}>에벤에셀</Label>
    </g>
  )
}

// 사무엘의 순회 재판 (삼상 7:15-17) — 벧엘·길갈·미스바를 돌며 재판하고 라마로 돌아와
// 제단을 쌓다. 새 선 예산(task#303 S1, 천장 240)의 첫 실작 — 인물 4명(사무엘+청원자 3인)을
// 옷 실루엣·얼굴·손·발까지 자세히 그려 "사람으로 읽히는" 밀도를 확보한다. 재판 순서:
// 무대(성문 3곳·라마·제단) → 사무엘 몸(눈은 비워 둔다) → 줄지어 선 청원자 C·B·A(각자
// 얼굴까지 완성) → 마지막에 사무엘의 눈·입이 열려 그들을 **본다**(판결의 순간) → 팔이 판결
// 몸짓으로 튼다.
function SamuelCircuitScene({ reduce }) {
  return (
    <g>
      {/* 지면 + 원경 능선 */}
      <g style={d(0, reduce)}>
        <path d="M4 54 h114" {...sw(1.6)} />
        <path d="M6 14 q54 -4 108 0" {...sw(1.1, 0.4)} />
      </g>
      {/* 벧엘 성문 — 쌍탑·문루·문 */}
      <g style={d(130, reduce)}>
        <path d="M12 15 v-6 h4 v6" {...sw(1.5)} />
        <path d="M22 15 v-6 h4 v6" {...sw(1.5)} />
        <path d="M16 10 h6" {...sw(1.4)} />
      </g>
      <g style={d(260, reduce)}>
        <path d="M18 15 v-4 h2 v4" {...sw(1.3)} />
        <path d="M10 15.2 h18" {...sw(1.1, 0.45)} />
        <path d="M12.5 12 h3 M22.5 12 h3" {...sw(1.1, 0.5)} />
      </g>
      <g style={d(390, reduce)}>
        <path d="M12.5 13.5 h3 M22.5 13.5 h3" {...sw(1.1, 0.5)} />
        <path d="M15 15.5 q3 1 6 0" {...sw(1.1, 0.45)} />
      </g>
      {/* 길갈 성문 — 동일 구조를 오른쪽으로 옮겨 */}
      <g style={d(520, reduce)}>
        <path d="M50 15 v-6 h4 v6" {...sw(1.5)} />
        <path d="M60 15 v-6 h4 v6" {...sw(1.5)} />
        <path d="M54 10 h6" {...sw(1.4)} />
      </g>
      <g style={d(650, reduce)}>
        <path d="M56 15 v-4 h2 v4" {...sw(1.3)} />
        <path d="M48 15.2 h18" {...sw(1.1, 0.45)} />
        <path d="M50.5 12 h3 M60.5 12 h3" {...sw(1.1, 0.5)} />
      </g>
      <g style={d(780, reduce)}>
        <path d="M50.5 13.5 h3 M60.5 13.5 h3" {...sw(1.1, 0.5)} />
        <path d="M53 15.5 q3 1 6 0" {...sw(1.1, 0.45)} />
      </g>
      {/* 미스바 성문 */}
      <g style={d(910, reduce)}>
        <path d="M88 15 v-6 h4 v6" {...sw(1.5)} />
        <path d="M98 15 v-6 h4 v6" {...sw(1.5)} />
        <path d="M92 10 h6" {...sw(1.4)} />
      </g>
      <g style={d(1040, reduce)}>
        <path d="M94 15 v-4 h2 v4" {...sw(1.3)} />
        <path d="M86 15.2 h18" {...sw(1.1, 0.45)} />
        <path d="M88.5 12 h3 M98.5 12 h3" {...sw(1.1, 0.5)} />
      </g>
      <g style={d(1170, reduce)}>
        <path d="M88.5 13.5 h3 M98.5 13.5 h3" {...sw(1.1, 0.5)} />
        <path d="M91 15.5 q3 1 6 0" {...sw(1.1, 0.45)} />
      </g>
      {/* 라마 — 지붕·벽·문(순회를 마치고 돌아오는 곳) */}
      <g style={d(1300, reduce)}>
        <path d="M99 46 l8 -5 l8 5" {...sw(1.6)} />
        <path d="M101 46 v8" {...sw(1.4)} />
        <path d="M113 46 v8" {...sw(1.4)} />
      </g>
      <g style={d(1430, reduce)}>
        <path d="M105 54 v-5 h4 v5" {...sw(1.3)} />
        <path d="M108.5 48 h3" {...sw(1.1, 0.5)} />
        <path d="M98 54.3 h17" {...sw(1.1, 0.5)} />
      </g>
      <g style={d(1560, reduce)}>
        <path d="M103 44.3 h8" {...sw(1.2, 0.5)} />
      </g>
      {/* 제단 — "거기서 여호와를 위하여 단을 쌓았더라"(삼상 7:17) */}
      <g style={d(1690, reduce)}>
        <path d="M92 54 q1.4 -3 2.8 0" {...sw(1.5)} />
        <path d="M95.4 54 q1.4 -3.2 2.8 0" {...sw(1.5)} />
        <path d="M94 51 q1.4 -1.6 2.8 0" {...sw(1.5)} />
      </g>
      <g style={d(1820, reduce)}>
        <path d="M93 53 q0.8 -1.6 1.6 0" {...sw(1.4)} />
        <path d="M93.2 52.6 h1" {...sw(1.1, 0.5)} />
        <path d="M96.4 52.3 h1" {...sw(1.1, 0.5)} />
      </g>
      <g style={d(1950, reduce)}>
        <path d="M95.2 50 q0.6 -2 -0.3 -3.6" {...sw(1.1, 0.45)} />
      </g>

      {/* ── 사무엘 — 두건·목·어깨·겉옷(눈은 마지막 순간까지 비워 둔다) ── */}
      <g style={d(2080, reduce)}>
        <circle cx="72" cy="22.5" r="4.6" {...sw(2.6)} />
        <path d="M67.3 19 q4.7 -3 9.4 0" {...sw(2.2)} />
        <path d="M69 20.4 q3 -1.5 6 0" {...sw(1.4)} />
      </g>
      <g style={d(2210, reduce)}>
        <path d="M76.7 20 q1.6 1.4 0.8 3.4" {...sw(1.8)} />
        <path d="M70.5 27.1 v1.4" {...sw(2.2)} />
        <path d="M73.5 27.1 v1.4" {...sw(2.2)} />
      </g>
      <g style={d(2340, reduce)}>
        <path d="M67 29 q5 -1.6 10 0" {...sw(2.3)} />
        <path d="M67 29 q-2 6 -3 12 q-1 6.5 -2 13" {...sw(2.4)} />
        <path d="M77 29 q2 6 3 12 q1 6.5 2 13" {...sw(2.4)} />
      </g>
      <g style={d(2470, reduce)}>
        <path d="M69.3 31 q-0.47 3 -0.77 6" {...sw(1.5, 0.6)} />
        <path d="M74.7 31 q0.47 3 0.77 6" {...sw(1.5, 0.6)} />
        <path d="M69 29.6 q3 1 6 0" {...sw(1.4)} />
      </g>
      {/* 수염·매듭·허리끈(짧게 — 전폭 가로대 금지) */}
      <g style={d(2600, reduce)}>
        <path d="M75 30 l0.8 1.2" {...sw(1.3, 0.6)} />
        <path d="M69.8 28.3 L72 32.5 L74.2 28.3" {...sw(1.6)} />
      </g>
      <g style={d(2730, reduce)}>
        <path d="M70 38.2 h4.2" {...sw(1.8)} />
        <path d="M74.2 38.2 l1 1.8" {...sw(1.4)} />
      </g>
      {/* 옷자락 주름(두 겹)·발 */}
      <g style={d(2860, reduce)}>
        <path d="M64 49 q2.5 -1 4.5 0" {...sw(1.3, 0.6)} />
        <path d="M75 49 q2.5 -1 4.5 0" {...sw(1.3, 0.6)} />
        <path d="M62.5 51 q2 -0.8 3.6 0" {...sw(1.3, 0.55)} />
      </g>
      <g style={d(2990, reduce)}>
        <path d="M76.5 51.3 q2 -0.8 3.6 0" {...sw(1.3, 0.55)} />
        <path d="M61 54 h3" {...sw(1.3, 0.5)} />
        <path d="M81 54 h3" {...sw(1.3, 0.5)} />
      </g>
      {/* 판결하는 팔·손(회전은 절정에서, 지금은 자세만) */}
      <g transform={reduce ? 'rotate(-8 67 29)' : undefined}>
        <g style={d(3120, reduce)}>
          <path d="M67 29 q-7 3.5 -13 7" {...sw(2.3)} />
          <path d="M67.5 30 q-6.5 4 -12.5 6.5" {...sw(2.2)} />
          <path d="M60 33.2 l-1.6 0.9" {...sw(1.3, 0.55)} />
        </g>
        <g style={d(3250, reduce)}>
          <path d="M55 36.5 l-2.3 -1.3" {...sw(1.4, 0.6)} />
          <path d="M55 36.5 l-2.6 0.3" {...sw(1.4, 0.6)} />
          <path d="M55 36.5 l-1.8 2" {...sw(1.4, 0.6)} />
        </g>
        {!reduce && (
          <animateTransform attributeName="transform" type="rotate" from="0 67 29" to="-8 67 29"
            begin="9.8s" dur="0.8s" fill="freeze" calcMode="spline" keySplines="0.3 0 0.7 1" keyTimes="0;1" />
        )}
      </g>
      {/* 두루마리 — 재판의 근거, 손에 닿는다 */}
      <g style={d(3380, reduce)}>
        <path d="M77 29 q4 4 -2 10" {...sw(2)} />
        <path d="M73 39 h4" {...sw(2.1)} />
        <path d="M73 38.3 v1.4" {...sw(1.3, 0.6)} />
      </g>
      <g style={d(3510, reduce)}>
        <path d="M77 38.3 v1.4" {...sw(1.3, 0.6)} />
        <path d="M75 39.4 v1.3" {...sw(1.2, 0.55)} />
        <path d="M75.5 34 l1.3 1.3" {...sw(1.3, 0.55)} />
      </g>
      {/* 수염 결 */}
      <g style={d(3640, reduce)}>
        <path d="M71 28 v1" {...sw(1.2, 0.55)} />
        <path d="M73 28 v1" {...sw(1.2, 0.55)} />
        <path d="M72 28.5 v0.8" {...sw(1.1)} />
      </g>
      <g style={d(3770, reduce)}>
        <path d="M56.5 35.8 l-0.9 -0.5" {...sw(1.2)} />
      </g>

      {/* ── 청원자 C — 줄 맨 뒤, 지팡이를 짚고 기다린다 ── */}
      <g style={d(3900, reduce)}>
        <circle cx="15" cy="28" r="4" {...sw(2.2)} />
        <path d="M11 26 q4 -2.8 8 0" {...sw(1.8)} />
        <path d="M18.7 26.5 q1.3 1.2 0.6 2.6" {...sw(1.6)} />
      </g>
      <g style={d(4030, reduce)}>
        <path d="M13.4 32 v1.4" {...sw(2)} />
        <path d="M16.6 32 v1.4" {...sw(2)} />
        <path d="M10 33.4 q5 -1.3 10 0" {...sw(2.1)} />
      </g>
      <g style={d(4160, reduce)}>
        <path d="M10 33.4 L9 44.5" {...sw(2.1)} />
        <path d="M20 33.4 L21 44.5" {...sw(2.1)} />
        <path d="M15 35 q-0.05 0.5 -0.08 1" {...sw(1.4, 0.55)} />
      </g>
      <g style={d(4290, reduce)}>
        <path d="M12 34 q3 0.9 6 0" {...sw(1.3)} />
        <path d="M12.5 39 h5" {...sw(1.8)} />
      </g>
      <g style={d(4420, reduce)}>
        <path d="M9.3 43.6 q1.2 -0.7 2 0" {...sw(1.3, 0.55)} />
        <path d="M19.7 43.9 q1.2 -0.7 2 0" {...sw(1.3, 0.55)} />
        <path d="M8 42 q1 -0.5 1.7 0" {...sw(1.2, 0.5)} />
      </g>
      <g style={d(4550, reduce)}>
        <path d="M21 42.3 q1 -0.5 1.7 0" {...sw(1.2, 0.5)} />
        <path d="M9 44.5 q-0.3 5 0.2 8.5" {...sw(2)} />
        <path d="M10 44.5 v8" {...sw(1.3, 0.5)} />
      </g>
      <g style={d(4680, reduce)}>
        <path d="M21 44.5 q0.3 5 -0.2 8.5" {...sw(2)} />
        <path d="M20 44.5 v8" {...sw(1.3, 0.5)} />
        <path d="M8.5 54 h2.6" {...sw(1.4)} />
      </g>
      <g style={d(4810, reduce)}>
        <path d="M20.3 54 h2.6" {...sw(1.4)} />
        <path d="M9.7 52.5 v1.5" {...sw(1.2, 0.5)} />
        <path d="M19.7 52.5 v1.5" {...sw(1.2, 0.5)} />
      </g>
      {/* 팔짱을 낀 채(순서를 기다리는 자세) */}
      <g style={d(4940, reduce)}>
        <path d="M10.5 34 q3 1 4.5 2" {...sw(1.9)} />
        <path d="M19.5 34 q-3 1 -4.5 2" {...sw(1.9)} />
        <path d="M14 36 l1 0.6" {...sw(1.2, 0.55)} />
      </g>
      <g style={d(5070, reduce)}>
        <path d="M16 36 l-1 0.6" {...sw(1.2, 0.55)} />
        <path d="M14 37 h2" {...sw(1.3)} />
        <path d="M6 54 V33" {...sw(1.8)} />
      </g>
      <g style={d(5200, reduce)}>
        <path d="M5 33 h2" {...sw(1.2, 0.5)} />
        <path d="M10.5 34 l4 1" {...sw(1.3)} />
      </g>
      {/* 얼굴 — 담담히 앞을 본다 */}
      <g style={d(5330, reduce)}>
        <path d="M13.2 26.6 l0.9 0" {...sw(1.15)} />
        <path d="M15.9 26.6 l0.9 0" {...sw(1.15)} />
        <path d="M13.4 28.3 h0.9" {...sw(1.2)} />
      </g>
      <g style={d(5460, reduce)}>
        <path d="M15.7 28.3 h0.9" {...sw(1.2)} />
        <path d="M14.2 30.5 h1.6" {...sw(1.2)} />
      </g>

      {/* ── 청원자 B — 두 번째 사건, 고개 숙여 두 손을 모은다 ── */}
      <g style={d(5590, reduce)}>
        <circle cx="31" cy="29" r="4" {...sw(2.2)} />
        <path d="M27 27 q4 -2.8 8 0" {...sw(1.8)} />
        <path d="M34.7 27.5 q1.3 1.2 0.6 2.6" {...sw(1.6)} />
      </g>
      <g style={d(5720, reduce)}>
        <path d="M29.4 33 v1.4" {...sw(2)} />
        <path d="M32.6 33 v1.4" {...sw(2)} />
        <path d="M26 34.4 q5 -1.3 10 0" {...sw(2.1)} />
      </g>
      <g style={d(5850, reduce)}>
        <path d="M26 34.4 L25 45.5" {...sw(2.1)} />
        <path d="M36 34.4 L37 45.5" {...sw(2.1)} />
        <path d="M31 36 q-0.05 0.5 -0.08 1" {...sw(1.4, 0.55)} />
      </g>
      <g style={d(5980, reduce)}>
        <path d="M28 35 q3 0.9 6 0" {...sw(1.3)} />
        <path d="M27 36 q0.54 1.07 0.36 2.5" {...sw(1.4, 0.6)} />
        <path d="M28.5 40 h5" {...sw(1.8)} />
      </g>
      <g style={d(6110, reduce)}>
        <path d="M25.3 44.6 q1.2 -0.7 2 0" {...sw(1.3, 0.55)} />
        <path d="M35.7 44.9 q1.2 -0.7 2 0" {...sw(1.3, 0.55)} />
        <path d="M24 43 q1 -0.5 1.7 0" {...sw(1.2, 0.5)} />
      </g>
      <g style={d(6240, reduce)}>
        <path d="M37 43.3 q1 -0.5 1.7 0" {...sw(1.2, 0.5)} />
        <path d="M25 45.5 q-0.3 5 0.2 8.5" {...sw(2)} />
        <path d="M26 45.5 v8" {...sw(1.3, 0.5)} />
      </g>
      <g style={d(6370, reduce)}>
        <path d="M37 45.5 q0.3 5 -0.2 8.5" {...sw(2)} />
        <path d="M36 45.5 v8" {...sw(1.3, 0.5)} />
        <path d="M24.5 54 h2.6" {...sw(1.4)} />
      </g>
      <g style={d(6500, reduce)}>
        <path d="M36.3 54 h2.6" {...sw(1.4)} />
        <path d="M25.7 52.5 v1.5" {...sw(1.2, 0.5)} />
        <path d="M35.7 52.5 v1.5" {...sw(1.2, 0.5)} />
      </g>
      {/* 두 손을 모은 팔 */}
      <g style={d(6630, reduce)}>
        <path d="M26.5 35 q3 1 3.5 2" {...sw(1.9)} />
        <path d="M35.5 35 q-3 1 -3.5 2" {...sw(1.9)} />
        <path d="M29 35.5 l1 0.8" {...sw(1.2, 0.55)} />
      </g>
      <g style={d(6760, reduce)}>
        <path d="M33 35.5 l-1 0.8" {...sw(1.2, 0.55)} />
        <path d="M30 37 q1 1 2 0" {...sw(1.4)} />
        <path d="M30.5 38 q1 0.6 1.6 0" {...sw(1.2)} />
      </g>
      <g style={d(6890, reduce)}>
        <path d="M34 36 l1 1.6" {...sw(1.3)} />
        <path d="M30 47 h1.6" {...sw(1.2)} />
      </g>
      {/* 얼굴 — 고개 숙여 눈을 내리깐다 */}
      <g style={d(7020, reduce)}>
        <path d="M29.2 27.4 l0.9 0.5" {...sw(1.15)} />
        <path d="M31.9 27.9 l0.9 -0.5" {...sw(1.15)} />
        <path d="M29.4 29.3 h0.9" {...sw(1.2)} />
      </g>
      <g style={d(7150, reduce)}>
        <path d="M31.7 29.3 h0.9" {...sw(1.2)} />
        <path d="M30.2 31.6 q0.9 0.3 1.8 0" {...sw(1.2)} />
      </g>

      {/* ── 청원자 A — 사무엘 바로 앞, 손을 들어 호소한다 ── */}
      <g style={d(7280, reduce)}>
        <circle cx="50" cy="27" r="4.2" {...sw(2.2)} />
        <path d="M45.8 25 q4.2 -3 8.4 0" {...sw(1.8)} />
        <path d="M54.2 25.6 q1.3 1.3 0.6 2.8" {...sw(1.6)} />
      </g>
      <g style={d(7410, reduce)}>
        <path d="M48.3 31.1 v1.4" {...sw(2)} />
        <path d="M51.7 31.1 v1.4" {...sw(2)} />
        <path d="M45 32.5 q5 -1.4 10 0" {...sw(2.1)} />
      </g>
      <g style={d(7540, reduce)}>
        <path d="M45 32.5 L44 44" {...sw(2.1)} />
        <path d="M55 32.5 L56 44" {...sw(2.1)} />
        <path d="M50 34 q-0.09 1.8 -0.18 3" {...sw(1.4, 0.55)} />
      </g>
      <g style={d(7670, reduce)}>
        <path d="M47.5 33.5 q2.5 1.8 5 0" {...sw(1.3)} />
        <path d="M47 38 h5" {...sw(1.8)} />
        <path d="M44.3 43 q1.2 -0.7 2 0" {...sw(1.3, 0.55)} />
      </g>
      <g style={d(7800, reduce)}>
        <path d="M53.8 43.3 q1.2 -0.7 2 0" {...sw(1.3, 0.55)} />
        <path d="M43 41.5 q1 -0.5 1.7 0" {...sw(1.2, 0.5)} />
        <path d="M55.5 41.8 q1 -0.5 1.7 0" {...sw(1.2, 0.5)} />
      </g>
      <g style={d(7930, reduce)}>
        <path d="M44 44 q-0.3 5 0.2 10" {...sw(2)} />
        <path d="M45 44 v9" {...sw(1.3, 0.5)} />
        <path d="M56 44 q0.3 5 -0.2 10" {...sw(2)} />
      </g>
      <g style={d(8060, reduce)}>
        <path d="M55 44 v9" {...sw(1.3, 0.5)} />
        <path d="M43.5 54 h2.6" {...sw(1.4)} />
        <path d="M55.4 54 h2.6" {...sw(1.4)} />
      </g>
      <g style={d(8190, reduce)}>
        <path d="M44.7 52.5 v1.5" {...sw(1.2, 0.5)} />
        <path d="M54.7 52.5 v1.5" {...sw(1.2, 0.5)} />
        <path d="M55 32.5 q3 -5 6 -9" {...sw(2)} />
      </g>
      {/* 들어 올린 손 — 사무엘 쪽을 향해 */}
      <g style={d(8320, reduce)}>
        <path d="M55.6 33.1 q2.8 -4.6 5.6 -8.2" {...sw(1.3, 0.55)} />
        <path d="M59 26 l-1.4 -0.4" {...sw(1.2, 0.5)} />
        <path d="M58 27.5 l-1.2 0.3" {...sw(1.1, 0.5)} />
      </g>
      <g style={d(8450, reduce)}>
        <path d="M61 24.3 l-1 -0.6" {...sw(1.3, 0.55)} />
        <path d="M61 24.3 l1 -0.3" {...sw(1.3, 0.55)} />
        <path d="M45.5 34 q-2 3 -3 6" {...sw(1.9)} />
      </g>
      <g style={d(8580, reduce)}>
        <path d="M46 34.6 q-1.7 2.6 -2.6 5.2" {...sw(1.3, 0.55)} />
        <path d="M42.6 39.8 l-1.2 0.6" {...sw(1.2, 0.5)} />
        <path d="M41.8 40.6 l-1 1" {...sw(1.3)} />
      </g>
      {/* 손에 든 자루(다툼의 증거물) */}
      <g style={d(8710, reduce)}>
        <path d="M40.5 42 q1.4 -1 2.8 0 q0.4 1.6 -0.2 3 q-1.2 0.6 -2.4 0 q-0.6 -1.4 -0.2 -3" {...sw(1.5)} />
        <path d="M41.3 41.5 v-1.4" {...sw(1.2)} />
        <path d="M48.5 46 h1.8" {...sw(1.2)} />
      </g>
      {/* 얼굴 — 사무엘을 올려다보며 입을 열어 호소한다 */}
      <g style={d(8840, reduce)}>
        <path d="M47.8 25.3 l1 0.3" {...sw(1.15)} />
        <path d="M51.2 25.3 l1 -0.3" {...sw(1.15)} />
        <path d="M48.3 27 h1" {...sw(1.2)} />
      </g>
      <g style={d(8970, reduce)}>
        <path d="M51.3 27 h1" {...sw(1.2)} />
        <path d="M49.3 29.5 q0.9 0.8 1.8 0" {...sw(1.2)} />
      </g>

      {/* ── 절정 — 사무엘의 눈과 입이 비로소 열려 그들을 본다 ── */}
      <g style={d(9100, reduce)}>
        <path d="M70.35 23 l-0.8 0.4" {...sw(1.2)} />
        <path d="M73.65 23 l-0.8 0.4" {...sw(1.2)} />
        <path d="M70.8 25.8 h1" {...sw(1.2)} />
      </g>
      <g style={d(9230, reduce)}>
        <path d="M73.2 25.8 h1" {...sw(1.2)} />
        <path d="M71.3 27.6 q1 0.4 2 0" {...sw(1.2)} />
      </g>

      <Label x="59" y="5" at="1.3" reduce={reduce} size="3.8">벧엘·길갈·미스바</Label>
      <Label x="86" y="61" at="2.6" reduce={reduce} size="4.2">라마로 돌아오다</Label>
    </g>
  )
}

// 나욧의 학교 (삼상 19장)
function SamuelRamahSchoolScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
      </g>
      {/* 사무엘 — 가르치다 */}
      <g style={d(900, reduce)}>
        <circle cx="34" cy="33" r="2.9" {...sw(2.5)} />
        <path d="M34 35.9 v11 M30.5 54 l3.5 -7.4 l3.5 7.4" {...sw(2.5)} />
        <path d="M36.5 40 q4 0 6 2" {...sw(2)} />
      </g>
      {/* 생도들 — 둘러앉다 */}
      <g style={d(1800, reduce)}>
        <circle cx="58" cy="45" r="2" {...sw(1.7, 0.8)} />
        <path d="M56 54 q0 -5 2 -6 q2 1 2 6" {...sw(1.7, 0.8)} />
        <circle cx="70" cy="46" r="1.9" {...sw(1.6, 0.75)} />
        <path d="M68.2 54 q0 -4.5 1.8 -5.5 q1.8 1 1.8 5.5" {...sw(1.6, 0.75)} />
        <circle cx="82" cy="45.5" r="1.9" {...sw(1.6, 0.7)} />
        <path d="M80.2 54 q0 -4.5 1.8 -5.5 q1.8 1 1.8 5.5" {...sw(1.6, 0.7)} />
      </g>
      {/* 두루마리 */}
      <g style={d(2700, reduce)}>
        <path d="M42 49 q3 -1 6 0" {...sw(1.4, 0.65)} />
      </g>
      <Label x="34" y="24" at="1.7" reduce={reduce}>사무엘</Label>
      <Label x="70" y="38" at="2.6" reduce={reduce} size="4.2">라마 나욧의 선지자 생도들</Label>
    </g>
  )
}

const SCENES = {
  'authored-deborah-bethel-judging': { Scene: DeborahJudgingScene, desc: '종려나무 아래 드보라가 이스라엘을 재판하다', caption: '재판 — 사사기 4장' },
  'authored-deborah-kedesh-summons': { Scene: DeborahSummonsScene, desc: '드보라가 바락을 불러 다볼산 진군을 명하다', caption: '부름 — 사사기 4장' },
  'authored-deborah-tabor-muster': { Scene: TaborMusterScene, desc: '다볼산에 만 명이 진을 치다', caption: '집결 — 사사기 4장' },
  'authored-deborah-kishon-victory': { Scene: KishonVictoryScene, desc: '기손 강이 시스라의 병거를 휩쓸다', caption: '기손 강 — 사사기 4장' },
  'authored-deborah-kedesh-jael': { Scene: JaelTentScene, mood: 'dark', desc: '야엘의 장막 말뚝으로 시스라를 파하다', caption: '야엘의 장막 — 사사기 4장' },
  'authored-deborah-song': { Scene: DeborahSongScene, desc: '드보라와 바락이 승리를 노래로 돌리다', caption: '드보라의 노래 — 사사기 5장' },
  'authored-gideon-ophrah-call': { Scene: GideonCallScene, desc: '포도주 틀의 겁쟁이를 큰 용사라 부르시다', caption: '부르심 — 사사기 6장' },
  'authored-gideon-ophrah-fleece': { Scene: GideonFleeceScene, desc: '겁 많은 기드온이 양털로 표징을 구하다', caption: '양털 표징 — 사사기 6장' },
  'authored-gideon-harod-selection': { Scene: HarodSelectionScene, desc: '물을 핥은 삼백 명만 남기시다', caption: '하롯 샘 — 사사기 7장' },
  'authored-gideon-moreh-victory': { Scene: MorehVictoryScene, desc: '횃불과 나팔에 미디안이 무너지다', caption: '야습 — 사사기 7장' },
  'authored-gideon-succoth-pursuit': { Scene: GideonSuccothScene, desc: '지친 삼백이 숙곳에서 떡을 거절당하다', caption: '숙곳의 냉대 — 사사기 8장' },
  'authored-gideon-penuel-pursuit': { Scene: GideonPenuelScene, mood: 'dark', desc: '갈골에서 세바와 살문나를 사로잡아 원수를 갚다', caption: '브누엘 추격 — 사사기 8장' },
  'authored-gideon-ophrah-ephod': { Scene: OphrahEphodScene, mood: 'dark', desc: '전리품 금이 온 이스라엘의 올무가 되다', caption: '에봇 — 사사기 8장' },
  'authored-ruth-moab-sojourn': { Scene: RuthMoabScene, mood: 'dark', desc: '기근과 죽음이 모압 땅에 두 여인을 남기다', caption: '모압 우거 — 룻기 1장' },
  'authored-ruth-bethlehem-return': { Scene: RuthReturnScene, desc: '어머니의 하나님이 나의 하나님 — 함께 돌아오다', caption: '귀향 — 룻기 1장' },
  'authored-ruth-bethlehem-gleaning': { Scene: RuthGleaningScene, desc: '보아스의 밭에서 이삭을 줍다', caption: '이삭줍기 — 룻기 2장' },
  'authored-ruth-bethlehem-threshing': { Scene: RuthThreshingScene, desc: '룻이 타작마당의 보아스 발치에 눕다', caption: '타작마당의 밤 — 룻기 3장' },
  'authored-ruth-bethlehem-redemption': { Scene: RuthRedemptionScene, desc: '성문에서 기업 무름이 이루어지다', caption: '기업 무름 — 룻기 4장' },
  'authored-samuel-shiloh-dedication': { Scene: SamuelDedicationScene, desc: '한나가 젖 뗀 사무엘을 실로에 봉헌하다', caption: '봉헌 — 사무엘상 1장' },
  'authored-samuel-shiloh-calling': { Scene: SamuelCallingScene, desc: '세 번 부르시는 음성에 소년이 응답하다', caption: '부르심 — 사무엘상 3장' },
  'authored-jephthah-gilead-exile': { Scene: JephthahExileScene, desc: '쫓겨난 입다가 돕 땅 잡류의 우두머리가 되다', caption: '돕 땅의 추방자 — 사사기 11장' },
  'authored-jephthah-mizpah-summons': { Scene: JephthahSummonsScene, desc: '쫓겨난 자를 머리로 세우다', caption: '입다 — 사사기 11장' },
  'authored-jephthah-mizpah-vow': { Scene: JephthahVowScene, mood: 'dark', desc: '승리를 흥정하는 서원을 입에 담다', caption: '서원 — 사사기 11장' },
  'authored-jephthah-aroer-victory': { Scene: JephthahVictoryScene, desc: '아로엘에서 암몬 이십 성읍을 치다', caption: '대승 — 사사기 11장' },
  'authored-jephthah-mizpah-daughter': { Scene: JephthahDaughterScene, mood: 'dark', desc: '소고 치며 나온 것은 무남독녀였다', caption: '입다의 딸 — 사사기 11장' },
  'authored-jephthah-jordan-shibboleth': { Scene: ShibbolethScene, mood: 'dark', desc: '쉽볼렛 발음이 생사를 가르다', caption: '쉽볼렛 — 사사기 12장' },
  'authored-samson-zorah-birth': { Scene: SamsonBirthScene, desc: '제단 불꽃 위로 천사가 올라가다', caption: '출생 예고 — 사사기 13장' },
  'authored-samson-timnah-riddle': { Scene: SamsonRiddleScene, desc: '삼손이 사자를 찢고 꿀로 수수께끼를 내다', caption: '딤나의 수수께끼 — 사사기 14장' },
  'authored-samson-lehi-jawbone': { Scene: SamsonJawboneScene, desc: '나귀 턱뼈로 천 명을 치고 샘으로 응답받다', caption: '레히의 턱뼈 — 사사기 15장' },
  'authored-samson-gaza-gate': { Scene: SamsonGateScene, desc: '삼손이 가사 성문을 빗장째 뽑아 메고 오르다', caption: '가사 성문 — 사사기 16장' },
  'authored-samson-sorek-delilah': { Scene: SorekDelilahScene, mood: 'dark', desc: '머리털과 함께 힘이 떠나다', caption: '소렉 골짜기 — 사사기 16장' },
  'authored-samson-gaza-death': { Scene: GazaDeathScene, mood: 'dark', desc: '기둥을 무너뜨려 마지막 승리를 거두다', caption: '가사 신전 — 사사기 16장' },
  'authored-samuel-mizpah-victory': { Scene: SamuelMizpahVictoryScene, desc: '미스바의 회개 위로 우레가 블레셋을 흩다', caption: '에벤에셀 — 사무엘상 7장' },
  'authored-samuel-circuit-judge': { Scene: SamuelCircuitScene, desc: '사무엘이 세 성읍을 돌며 재판하다', caption: '순회 재판 — 사무엘상 7장' },
  'authored-samuel-ramah-school': { Scene: SamuelRamahSchoolScene, desc: '라마에서 선지자 생도들을 길러내다', caption: '나욧의 학교 — 사무엘상 19장' },
}

export default SCENES
