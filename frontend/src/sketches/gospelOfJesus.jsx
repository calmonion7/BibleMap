// 예수의 생애 — 23개 정차지 장면 (task#231, #227 표준). 세 인물(요한·예수·마리아) 교차 서사.
import { sw, d, Label } from './lib'

// 수태고지 (눅 1:26-38)
function AnnunciationScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M14 54 l9 -13 l9 13" {...sw(1.5, 0.6)} />
      </g>
      {/* 가브리엘 — 날개 */}
      <g style={d(900, reduce)}>
        <circle cx="78" cy="28" r="2.9" {...sw(2.4)} />
        <path d="M73.5 44 l2 -13 h5 l2 13 M73.5 44 h11" {...sw(2.4)} />
        <path d="M73 31 q-6 -3 -7.5 -8 M83 31 q6 -3 7.5 -8" {...sw(1.8)} />
        <path d="M76 34 q0.4 6 0 10 M80 34 q0.3 6 0 10" {...sw(1.2, 0.5)} />
      </g>
      {/* 마리아 — 주역: 고개 숙인 순종 */}
      <g style={d(1900, reduce)}>
        <circle cx="42" cy="38" r="2.9" {...sw(2.6)} />
        <path d="M38 54 l2 -13 h4 l2 13 M38 54 h8" {...sw(2.6)} />
        <path d="M40 39.5 q2 2.3 4.5 0.5 M40.5 44 q0.4 5.5 0 10" {...sw(1.4, 0.6)} />
        <path d="M44.5 43 q3 -1 5 0.5" {...sw(2)} />
      </g>
      <g style={d(reduce ? 0 : 2900, reduce)} stroke="var(--paper-accent)">
        <path d="M60 14 v-4 M53 16 l-2.6 -2.6 M67 16 l2.6 -2.6" {...sw(1.5)} />
      </g>
      <Label x="82" y="16" at="1.4" reduce={reduce}>가브리엘</Label>
      <Label x="42" y="28" at="2.4" reduce={reduce}>마리아</Label>
      <Label x="60" y="61" at="3.1" reduce={reduce} size="4.2">말씀대로 내게 이루어지이다</Label>
    </g>
  )
}

// 엘리사벳 방문 (눅 1:39-56)
function VisitationScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M6 50 q16 -8 30 -4 M78 46 q14 -6 28 -3" {...sw(1.2, 0.45)} />
      </g>
      {/* 두 여인 — 포옹 */}
      <g style={d(1100, reduce)}>
        <circle cx="52" cy="32" r="2.9" {...sw(2.6)} />
        <path d="M48 54 l2 -19 h4 l2 19 M48 54 h8 M54.5 37 q4 1.5 7 4" {...sw(2.6)} />
        <circle cx="68" cy="33" r="2.8" {...sw(2.4)} />
        <path d="M64 54 l2 -18 h4 l2 18 M64 54 h8 M65.5 38 q-4 1.5 -7 4" {...sw(2.4)} />
      </g>
      {/* 뛰노는 기쁨 — 강조 */}
      <g style={d(reduce ? 0 : 2300, reduce)} stroke="var(--paper-accent)">
        <path d="M66 44 q1.5 -1.5 3 0 M67.5 42.6 v-1.6" {...sw(1.5)} />
        <path d="M56 22 v-2.6 m-1.3 1.3 h2.6 M74 20 v-2.4 m-1.2 1.2 h2.4" {...sw(1.4)} />
      </g>
      <Label x="48" y="22" at="1.6" reduce={reduce}>마리아</Label>
      <Label x="74" y="24" at="1.6" reduce={reduce}>엘리사벳</Label>
      <Label x="60" y="61" at="2.7" reduce={reduce} size="4.2">내 영혼이 주를 찬양하며</Label>
    </g>
  )
}

// 요한의 출생 (눅 1:57-66)
function JohnBirthScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M14 54 l8 -11 l8 11" {...sw(1.5, 0.6)} />
      </g>
      {/* 서판 — 핵심: "요한" */}
      <g style={d(1000, reduce)}>
        <path d="M46 46 v-16 q0 -2.5 2.5 -2.5 h23 q2.5 0 2.5 2.5 v16 q0 2.5 -2.5 2.5 h-23 q-2.5 0 -2.5 -2.5" {...sw(2.6)} />
        <path d="M52 34 h16 M52 38 h16 M52 42 h10" {...sw(1.4)} stroke="var(--paper-accent)" />
      </g>
      {/* 사가랴 — 서판 들어 보임 */}
      <g style={d(2000, reduce)}>
        <circle cx="88" cy="33" r="2.8" {...sw(2.3)} />
        <path d="M84 54 l2 -18.5 h4 l2 18.5 M84 54 h8 M85 37 q-4 1 -8 0" {...sw(2.3)} />
      </g>
      {/* 아기 요람 */}
      <g style={d(2700, reduce)}>
        <path d="M22 50 q0 -3.5 4 -3.5 h6 q4 0 4 3.5 M24 54 l-1.5 -3.5 M34 54 l1.5 -3.5" {...sw(2)} />
        <circle cx="27" cy="44.5" r="1.7" {...sw(1.8)} />
      </g>
      <Label x="60" y="24" at="1.5" reduce={reduce}>그 이름은 요한</Label>
      <Label x="92" y="24" at="2.5" reduce={reduce}>사가랴</Label>
    </g>
  )
}

// 베들레헴 탄생 (눅 2:1-7)
function BethlehemBirthScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M22 54 l14 -16 l14 16 M28 54 l8 -9 l8 9" {...sw(1.8, 0.8)} />
      </g>
      {/* 구유 + 아기 — 핵심 */}
      <g style={d(1000, reduce)}>
        <path d="M52 50 l3.5 -6 h13 l3.5 6 M54 50 h16" {...sw(2.6)} />
        <path d="M56 54 l1 -4 M68 54 l-1 -4" {...sw(2)} />
        <circle cx="59.5" cy="41" r="1.9" {...sw(2.2)} />
        <path d="M62 42 q3 1 5 0.5" {...sw(2.2)} />
        <path d="M57 46.5 l3 -1.2 m2 0.8 l3 -1.2" {...sw(1.2, 0.55)} />
      </g>
      {/* 마리아·요셉 */}
      <g style={d(2000, reduce)}>
        <circle cx="42" cy="38" r="2.6" {...sw(2.2)} />
        <path d="M39 52 l1.5 -11.5 h3 l1.5 11.5" {...sw(2.2)} />
        <circle cx="82" cy="37" r="2.6" {...sw(2.1)} />
        <path d="M82 39.6 v7.4 M79.5 52 l2.5 -5 l2.5 5" {...sw(2.1)} />
      </g>
      {/* 별 — 강조 */}
      <g style={d(reduce ? 0 : 2900, reduce)} stroke="var(--paper-accent)">
        <path d="M60 14 v4 m-2 -2 h4 M57 11.5 l-1.6 -1.6 M63 11.5 l1.6 -1.6 M60 20 v2 m0 3 v2" {...sw(1.7)} />
      </g>
      <Label x="60" y="33" at="1.6" reduce={reduce}>구유의 아기</Label>
      <Label x="42" y="28" at="2.5" reduce={reduce}>마리아</Label>
    </g>
  )
}

// 성전 봉헌 (눅 2:25-38)
function TemplePresentationScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M16 54 v-26 M28 54 v-26 M13 28 h18 M92 54 v-26 M104 54 v-26 M89 28 h18" {...sw(1.5, 0.6)} />
      </g>
      {/* 시므온 — 아기 안음 */}
      <g style={d(1100, reduce)}>
        <circle cx="56" cy="30" r="3" {...sw(2.6)} />
        <path d="M51.5 54 l2.2 -19 h4.6 l2.2 19 M51.5 54 h9" {...sw(2.6)} />
        <path d="M52 37 q4 3.5 9 1" {...sw(2.2)} />
        <circle cx="61.5" cy="38.5" r="1.7" {...sw(2.2)} />
        <path d="M54 40 q0.4 6.5 0 13" {...sw(1.3, 0.55)} />
      </g>
      {/* 안나 — 감사 */}
      <g style={d(2100, reduce)}>
        <circle cx="78" cy="38" r="2.5" {...sw(2)} />
        <path d="M75 54 l1.5 -13 h3 l1.5 13 M75 54 h6 M76 42 q-2.5 -2.5 -3 -5.5" {...sw(2)} />
      </g>
      <g style={d(reduce ? 0 : 2900, reduce)} stroke="var(--paper-accent)">
        <path d="M58 18 v-3.5 M51 20 l-2.4 -2.4 M65 20 l2.4 -2.4" {...sw(1.4)} />
      </g>
      <Label x="56" y="20" at="1.7" reduce={reduce}>시므온과 아기</Label>
      <Label x="60" y="61" at="3" reduce={reduce} size="4.2">내 눈이 주의 구원을 보았나이다</Label>
    </g>
  )
}

// 애굽 피신 (마 2:13-15)
function FlightEgyptScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M100 14 a6 6 0 1 1 -4 -10 a7.5 7.5 0 0 0 4 10" {...sw(1.6)} />
        <path d="M14 12 v2.4 m-1.2 -1.2 h2.4 M30 8 v2 m-1 -1 h2" {...sw(1.2, 0.6)} />
      </g>
      {/* 나귀 탄 마리아와 아기, 이끄는 요셉 — 밤길 */}
      <g transform={reduce ? 'translate(-12 0)' : undefined} style={d(1200, reduce)}>
        <path d="M56 50 q0 -4.5 5.5 -4.5 q5.5 0 5.5 4.5 M58 54 v-2 M65 54 v-2" {...sw(2)} />
        <path d="M68 46.5 q3 -1.5 3.5 -4.5" {...sw(1.7)} />
        <circle cx="61" cy="37" r="2.6" {...sw(2.4)} />
        <path d="M58.5 45.5 l1.3 -6 h2.6 l1.3 6" {...sw(2.4)} />
        <circle cx="64.5" cy="41.5" r="1.5" {...sw(2)} />
        <circle cx="44" cy="38" r="2.5" {...sw(2.2)} />
        <path d="M44 40.5 v7 M41.5 54 l2.5 -6.5 M47 53.5 l-2.5 -6 M46 42 l5 2.5 M42 42.5 l-3.5 8" {...sw(2.2)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="translate" from="0 0" to="-14 0"
            begin="2s" dur="2.4s" fill="freeze" calcMode="spline" keySplines="0.3 0 0.7 1" keyTimes="0;1" />
        )}
      </g>
      <Label x="48" y="28" at="1.9" reduce={reduce}>밤의 피난길</Label>
      <Label x="96" y="26" at="1" reduce={reduce}>애굽으로</Label>
    </g>
  )
}

// 열두 살 성전에서 (눅 2:41-52)
function BoyAtTempleScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M16 54 v-24 M28 54 v-24 M13 30 h18 M92 54 v-24 M104 54 v-24 M89 30 h18" {...sw(1.5, 0.6)} />
      </g>
      {/* 소년 예수 — 중앙, 작지만 곧게 */}
      <g style={d(1100, reduce)}>
        <circle cx="60" cy="35" r="2.6" {...sw(2.6)} />
        <path d="M60 37.6 v8.4 M57.5 54 l2.5 -8 l2.5 8" {...sw(2.6)} />
        <path d="M60 39.5 q-3.5 -1.5 -4.5 -4.5 M60 39.5 q3.5 -1.5 4.5 -4.5" {...sw(2.3)} />
      </g>
      {/* 둘러앉은 선생들 — 두루마리 */}
      <g style={d(2100, reduce)}>
        <circle cx="36" cy="44" r="2.4" {...sw(2)} />
        <path d="M33 54 l1.5 -8 h3 l1.5 8 M38.5 47 q3 -0.5 5 1" {...sw(2)} />
        <path d="M28 48 h6 q1.2 0 1.2 1.2 v1 q0 1.2 -1.2 1.2 h-6 z" {...sw(1.6)} />
        <circle cx="84" cy="44.5" r="2.3" {...sw(1.9, 0.9)} />
        <path d="M81 54 l1.5 -7.5 h3 l1.5 7.5 M81.5 47.5 q-3 -0.5 -5 1" {...sw(1.9, 0.9)} />
      </g>
      <Label x="60" y="26" at="1.7" reduce={reduce}>열두 살 예수</Label>
      <Label x="60" y="61" at="2.9" reduce={reduce} size="4.2">내 아버지 집에 있어야 할 줄을</Label>
    </g>
  )
}

// 광야의 외침 (마 3:1-4)
function JohnWildernessScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M6 50 q14 -4 28 0 M74 50 q14 -4 28 0" {...sw(1.2, 0.45)} />
        <path d="M20 54 l3 -4 M92 54 l3 -4" {...sw(1.1, 0.4)} />
      </g>
      {/* 요한 — 낙타털 옷·지팡이·외침 */}
      <g style={d(1100, reduce)}>
        <circle cx="56" cy="28" r="3.1" {...sw(2.6)} />
        <path d="M51.5 54 l2.2 -20 h4.6 l2.2 20 M51.5 54 h9" {...sw(2.6)} />
        <path d="M53.5 36 l1.5 -1.5 m-1.8 4 l1.5 -1.5 m-1.7 4 l1.4 -1.4" {...sw(1.2, 0.6)} />
        <path d="M59.5 32 q5 -2.5 6.5 -7 M52.5 33 l-5 10 M47.5 43 l-1 11" {...sw(2.3)} />
      </g>
      {/* 외침 — 퍼지는 선 */}
      <g style={d(reduce ? 0 : 2300, reduce)} stroke="var(--paper-accent)">
        <path d="M68 22 q3 -1.5 6 0 M70 17.5 q3.5 -1.8 7 0 M72 13 q4 -2 8 0" {...sw(1.4)} />
      </g>
      <Label x="52" y="18" at="1.7" reduce={reduce}>세례 요한</Label>
      <Label x="60" y="61" at="2.6" reduce={reduce} size="4.2">회개하라 천국이 가까이 왔느니라</Label>
    </g>
  )
}

// 요단강 세례 (마 3:13-17)
function JordanBaptismScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M8 48 q8 -3 16 0 q8 -3 16 0 q8 -3 16 0 q8 -3 16 0 q8 -3 16 0 q8 -3 16 0" {...sw(2)} />
      </g>
      {/* 두 사람 — 요한이 예수께 세례 */}
      <g style={d(1100, reduce)}>
        <circle cx="66" cy="34" r="2.9" {...sw(2.6)} />
        <path d="M66 36.9 v6.1 M62.5 45 q3.5 -2 7 0" {...sw(2.6)} />
        <circle cx="48" cy="30" r="2.7" {...sw(2.3)} />
        <path d="M48 32.7 v9.3 M45 45 q3 -1.5 6 0 M50.5 34 q5 1.5 8.5 -0.5" {...sw(2.3)} />
      </g>
      {/* 하늘 열림 + 비둘기 강림 — 핵심 */}
      <g transform={reduce ? undefined : 'translate(0 -12)'} style={d(2200, reduce)} stroke="var(--paper-accent)">
        <path d="M62 18 q2.5 -2.5 5 0 q2.5 -2.5 5 0" {...sw(1.8)} />
        <path d="M67 19 q0.5 2 2 3" {...sw(1.4)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="translate" from="0 -12" to="0 0"
            begin="2.5s" dur="0.9s" fill="freeze" calcMode="spline" keySplines="0.3 0 0.5 1" keyTimes="0;1" />
        )}
      </g>
      <g style={d(reduce ? 0 : 3200, reduce)} stroke="var(--paper-accent)">
        <path d="M56 8 q10 -4 20 0 M60 12 q7 -2.5 14 0" {...sw(1.3)} />
      </g>
      <Label x="44" y="20" at="1.6" reduce={reduce}>요한</Label>
      <Label x="72" y="26" at="1.6" reduce={reduce}>예수</Label>
      <Label x="90" y="10" at="3.4" reduce={reduce} size="4.2">이는 내 사랑하는 아들이라</Label>
    </g>
  )
}

// 광야 시험 (마 4:1-11)
function WildernessTemptationScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M6 46 l16 -12 l12 8 M78 42 l14 -10 l16 10" {...sw(1.4, 0.55)} />
      </g>
      {/* 예수 — 홀로 곧게 */}
      <g style={d(1100, reduce)}>
        <circle cx="56" cy="31" r="3" {...sw(2.6)} />
        <path d="M56 34 v12 M52.5 54 l3.5 -8 l3.5 8" {...sw(2.6)} />
        <path d="M54 37.5 q2 1.2 4 0" {...sw(1.3, 0.6)} />
      </g>
      {/* 세 시험 상징 — 돌·성전 꼭대기·왕관(내쳐짐) */}
      <g style={d(2100, reduce)}>
        <path d="M20 51 q1.5 -3 4.5 -2 q2.5 1 1.5 4 z" {...sw(1.8)} />
        <path d="M88 48 v-8 h8 v8 M90 40 l2 -3 l2 3" {...sw(1.6, 0.8)} />
        <path d="M104 50 v-2 l1.2 1 l1 -1.5 l1 1.5 l1.2 -1 v2" {...sw(1.6, 0.75)} />
      </g>
      {/* 말씀 — 강조 */}
      <g style={d(reduce ? 0 : 3000, reduce)} stroke="var(--paper-accent)">
        <path d="M44 22 h6 q1.4 0 1.4 1.4 v2 q0 1.4 -1.4 1.4 h-6 z M45.5 24 h3 m-3 1.6 h3" {...sw(1.5)} />
      </g>
      <Label x="56" y="21" at="1.7" reduce={reduce}>사십 일의 시험</Label>
      <Label x="60" y="61" at="3.2" reduce={reduce} size="4.2">기록되었으되 — 말씀으로 이기시다</Label>
    </g>
  )
}

// 가나 혼인 잔치 (요 2:3-11)
function CanaWeddingScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
      </g>
      {/* 여섯 항아리 — 순차 draw */}
      <g style={d(900, reduce)}>
        <path d="M18 54 q-2 -6 2 -8 q4 1 3.5 8 M30 54 q-2 -6 2 -8 q4 1 3.5 8 M42 54 q-2 -6 2 -8 q4 1 3.5 8" {...sw(2)} />
      </g>
      <g style={d(1600, reduce)}>
        <path d="M54 54 q-2 -6 2 -8 q4 1 3.5 8 M66 54 q-2 -6 2 -8 q4 1 3.5 8 M78 54 q-2 -6 2 -8 q4 1 3.5 8" {...sw(2.1)} />
      </g>
      {/* 포도주 — 강조: 잔에 차오름 */}
      <g style={d(2400, reduce)} stroke="var(--paper-accent)">
        <path d="M94 44 q0 -3.5 4 -3.5 q4 0 4 3.5 M98 44 v5 M95 49.5 h6" {...sw(2.2)} />
        <path d="M95.5 42 q2.5 1.4 5 0" {...sw(1.5)} />
      </g>
      {/* 마리아 — 간청 */}
      <g style={d(1900, reduce)}>
        <circle cx="30" cy="30" r="2.7" {...sw(2.3)} />
        <path d="M26.5 44 l1.8 -11.5 h3.4 l1.8 11.5 M32.5 34 q4 -1 7 0.5" {...sw(2.3)} />
      </g>
      <Label x="48" y="34" at="1.9" reduce={reduce}>돌항아리 여섯</Label>
      <Label x="98" y="34" at="3" reduce={reduce}>새 포도주</Label>
      <Label x="26" y="21" at="2.3" reduce={reduce}>마리아</Label>
    </g>
  )
}

// 가버나움 이주 (마 4:13-16)
function CapernaumBaseScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M60 50 q10 -3 20 0 q10 -3 20 0 M66 53 q9 -2.5 18 0" {...sw(1.6)} />
      </g>
      {/* 바닷가 집 */}
      <g style={d(1000, reduce)}>
        <path d="M14 54 v-12 h20 v12 M12 42 l12 -8 l12 8 M20 54 v-7 h8 v7" {...sw(2.2)} />
      </g>
      {/* 배와 그물 */}
      <g style={d(1900, reduce)}>
        <path d="M78 46 q2 4 7 4 h12 q5 0 7 -4 l-2.5 -3.5 h-21 z" {...sw(2.2)} />
        <path d="M88 42 V32 M88 32 q-6 1.5 -8 8" {...sw(1.8)} />
        <path d="M44 50 l10 -6 M46 52 l10 -6 M48 46 l4 6 M52 44 l4 6" {...sw(1.2, 0.55)} />
      </g>
      <g style={d(reduce ? 0 : 2800, reduce)} stroke="var(--paper-accent)">
        <path d="M24 26 v-4 M18 28 l-2.4 -2.4 M30 28 l2.4 -2.4" {...sw(1.4)} />
      </g>
      <Label x="24" y="61" at="1.4" reduce={reduce}>가버나움</Label>
      <Label x="60" y="24" at="3" reduce={reduce} size="4.2">흑암에 앉은 백성이 큰 빛을 보다</Label>
    </g>
  )
}

// 산상수훈 (마 5:1-12)
function SermonMountScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M14 54 Q60 22 106 54" {...sw(2.2)} />
      </g>
      {/* 앉으신 예수 — 산 위 */}
      <g style={d(1100, reduce)}>
        <circle cx="60" cy="27" r="2.9" {...sw(2.6)} />
        <path d="M60 29.9 q-1 4 -3.5 5.5 M54 34 l4 4 M60 31 q3.5 1.5 4.5 4.5" {...sw(2.6)} />
        <path d="M56 38.5 h8" {...sw(2)} />
      </g>
      {/* 둘러앉은 무리 */}
      <g style={d(2100, reduce)}>
        <circle cx="34" cy="46" r="2.2" {...sw(1.9)} />
        <path d="M31.5 52 l1.2 -3.5 h2.6 l1.2 3.5" {...sw(1.9)} />
        <circle cx="46" cy="49" r="2.1" {...sw(1.8, 0.9)} />
        <path d="M43.8 54 l1.1 -3 h2.2 l1.1 3" {...sw(1.8, 0.9)} />
        <circle cx="76" cy="48.5" r="2.1" {...sw(1.8, 0.9)} />
        <path d="M73.8 54 l1.1 -3.2 h2.2 l1.1 3.2" {...sw(1.8, 0.9)} />
        <circle cx="88" cy="46.5" r="2.2" {...sw(1.9)} />
        <path d="M85.5 52.5 l1.2 -3.6 h2.6 l1.2 3.6" {...sw(1.9)} />
      </g>
      <Label x="60" y="16" at="1.7" reduce={reduce}>산 위의 가르침</Label>
      <Label x="60" y="61" at="2.9" reduce={reduce} size="4.2">심령이 가난한 자는 복이 있나니</Label>
    </g>
  )
}

// 마케루스 순교 (막 6:27-29)
function MachaerusDeathScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M6 54 L28 30 L48 42" {...sw(1.6, 0.6)} />
        {/* 요새 */}
        <path d="M64 54 v-22 h30 v22 M68 32 v-4 h5 v4 m6 0 v-4 h5 v4 m6 0 v-4 h5 v4" {...sw(2.2)} />
        <path d="M70 40 h4 m8 0 h4 M72 47 h4 m8 0 h4" {...sw(1.2, 0.45)} />
      </g>
      {/* 꺼진 등불 — 예비자의 길이 끝남 */}
      <g style={d(1600, reduce)}>
        <path d="M28 48 h9 M30 48 q0 -3 2.5 -3 q2.5 0 2.5 3 M32.5 45 v-2" {...sw(2.2)} />
        <path d="M32.5 40 q-1.4 -1.6 -0.6 -3.4" {...sw(1.4, 0.5)} />
        <path d="M36 38 q2 -1.5 3.5 -2.8" {...sw(1.2, 0.4)} strokeDasharray="1.6 1.8" />
      </g>
      <Label x="79" y="26" at="1.2" reduce={reduce}>마케루스 요새</Label>
      <Label x="33" y="59" at="2.2" reduce={reduce} size="4.2">꺼진 등불 — 예비자의 마지막</Label>
    </g>
  )
}

// 가이사랴 빌립보 (마 16:13-16)
function CaesareaPhilippiScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        {/* 큰 바위 */}
        <path d="M72 54 q-2 -18 12 -22 q16 -3 22 10 q3 8 -2 12" {...sw(2)} />
        <path d="M82 40 l5 -3 M94 38 l4 3" {...sw(1.2, 0.4)} />
      </g>
      {/* 예수 */}
      <g style={d(1100, reduce)}>
        <circle cx="52" cy="31" r="3" {...sw(2.6)} />
        <path d="M47.5 54 l2.2 -20 h4.6 l2.2 20 M47.5 54 h9 M55.5 36 q4 -1 6.5 0.5" {...sw(2.6)} />
      </g>
      {/* 베드로 — 고백 */}
      <g style={d(2000, reduce)}>
        <circle cx="30" cy="38" r="2.7" {...sw(2.3)} />
        <path d="M30 40.7 v6.3 M27.5 54 l2.5 -7 l2.5 7 M32.5 42 q3 -1.5 5 -0.5" {...sw(2.3)} />
      </g>
      <g style={d(reduce ? 0 : 2900, reduce)} stroke="var(--paper-accent)">
        <path d="M30 28 v-3 m-1.5 1.5 h3" {...sw(1.4)} />
      </g>
      <Label x="30" y="21" at="2.3" reduce={reduce}>베드로</Label>
      <Label x="90" y="26" at="1.1" reduce={reduce}>이방의 바위 앞</Label>
      <Label x="60" y="61" at="3.1" reduce={reduce} size="4.2">주는 그리스도시요 하나님의 아들이시니이다</Label>
    </g>
  )
}

// 나사로 (요 11:43-44)
function LazarusScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        {/* 무덤 굴 + 굴린 돌 */}
        <path d="M64 54 q0 -18 18 -18 q18 0 18 18" {...sw(2.2)} />
        <circle cx="104" cy="47" r="6.5" {...sw(2)} />
        <path d="M101 45 l6 4 M104 43.5 v7" {...sw(1.2, 0.45)} />
      </g>
      {/* 나사로 — 베로 감긴 채 나옴 */}
      <g transform={reduce ? 'translate(-8 0)' : undefined} style={d(1600, reduce)}>
        <circle cx="82" cy="38" r="2.7" {...sw(2.4)} />
        <path d="M82 40.7 v8.3 M79.5 54 l2.5 -5 l2.5 5" {...sw(2.4)} />
        <path d="M79.8 42 h4.4 m-4.6 3 h4.8 m-4.6 3 h4.4" {...sw(1.3, 0.7)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="translate" from="0 0" to="-9 0"
            begin="2.4s" dur="1.4s" fill="freeze" calcMode="spline" keySplines="0.3 0 0.6 1" keyTimes="0;1" />
        )}
      </g>
      {/* 예수 — 부르심 */}
      <g style={d(1000, reduce)}>
        <circle cx="34" cy="31" r="3" {...sw(2.6)} />
        <path d="M29.5 54 l2.2 -20 h4.6 l2.2 20 M29.5 54 h9 M37.5 35 q5 -1.5 8 0.5" {...sw(2.6)} />
      </g>
      <Label x="34" y="21" at="1.5" reduce={reduce}>나사로야 나오라</Label>
      <Label x="76" y="28" at="2.9" reduce={reduce}>나사로</Label>
    </g>
  )
}

// 예루살렘 입성 (마 21:1-11)
function TriumphalEntryScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M92 54 v-16 q8 -7 16 0 v16" {...sw(1.6, 0.7)} />
      </g>
      {/* 나귀 탄 예수 — 전진 */}
      <g transform={reduce ? 'translate(12 0)' : undefined} style={d(1100, reduce)}>
        <path d="M46 50 q0 -4.5 5.5 -4.5 q5.5 0 5.5 4.5 M48 54 v-2 M55 54 v-2" {...sw(2.1)} />
        <path d="M58 46.5 q3 -1.5 3.5 -4.5" {...sw(1.8)} />
        <circle cx="51" cy="35.5" r="2.8" {...sw(2.6)} />
        <path d="M48.5 45.5 l1.3 -7 h2.6 l1.3 7" {...sw(2.6)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="translate" from="0 0" to="14 0"
            begin="2.2s" dur="2.2s" fill="freeze" calcMode="spline" keySplines="0.3 0 0.7 1" keyTimes="0;1" />
        )}
      </g>
      {/* 종려가지 — 흔들림 */}
      <g style={d(2000, reduce)}>
        <path d="M20 44 q-2 -7 3 -10 M20 44 q-6 -4 -5 -9 M20 44 q1 -8 -3 -11" {...sw(1.7)}>
          {!reduce && (
            <animateTransform attributeName="transform" type="rotate"
              values="-6 20 44; 6 20 44; -6 20 44" keyTimes="0;0.5;1" begin="2.4s" dur="1.2s" repeatCount="2" />
          )}
        </path>
        <circle cx="20" cy="47" r="2" {...sw(1.9)} />
        <path d="M18.2 49 l-1.2 5 M22 49 l1 5" {...sw(1.9)} />
      </g>
      {/* 겉옷 길 */}
      <g style={d(2800, reduce)}>
        <path d="M64 52.5 q4 -1.5 8 0 M74 53 q4 -1.5 8 0" {...sw(1.3, 0.55)} />
      </g>
      <g style={d(reduce ? 0 : 3400, reduce)} stroke="var(--paper-accent)">
        <path d="M56 20 v-3 m-1.5 1.5 h3 M70 24 v-2.4 m-1.2 1.2 h2.4" {...sw(1.4)} />
      </g>
      <Label x="52" y="26" at="1.7" reduce={reduce}>나귀 탄 왕</Label>
      <Label x="20" y="30" at="2.5" reduce={reduce}>호산나</Label>
    </g>
  )
}

// 최후의 만찬 (눅 22:14-20)
function LastSupperScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M22 44 h76 M28 54 v-10 M92 54 v-10" {...sw(2.2)} />
      </g>
      {/* 떡과 잔 — 핵심 */}
      <g style={d(1300, reduce)}>
        <ellipse cx="52" cy="41" rx="5" ry="1.8" {...sw(2.4)} />
        <path d="M66 36 q0 -3 3 -3 q3 0 3 3 M69 36 v4 M66.5 40.5 h5" {...sw(2.6)} stroke="var(--paper-accent)" />
      </g>
      {/* 예수 — 중앙 */}
      <g style={d(900, reduce)}>
        <circle cx="60" cy="28" r="2.9" {...sw(2.6)} />
        <path d="M60 30.9 v7.1 M56 34 q4 -2.5 8 0" {...sw(2.6)} />
      </g>
      {/* 제자들 — 양옆 */}
      <g style={d(2200, reduce)}>
        <circle cx="34" cy="33" r="2.3" {...sw(1.9)} />
        <path d="M34 35.3 v5.7" {...sw(1.9)} />
        <circle cx="44" cy="31.5" r="2.4" {...sw(2)} />
        <path d="M44 33.9 v7.1" {...sw(2)} />
        <circle cx="76" cy="31.5" r="2.4" {...sw(2)} />
        <path d="M76 33.9 v7.1" {...sw(2)} />
        <circle cx="86" cy="33" r="2.3" {...sw(1.9)} />
        <path d="M86 35.3 v5.7" {...sw(1.9)} />
      </g>
      <Label x="60" y="18" at="1.4" reduce={reduce}>마지막 만찬</Label>
      <Label x="60" y="61" at="2.7" reduce={reduce} size="4.2">내 피로 세우는 새 언약이라</Label>
    </g>
  )
}

// 겟세마네 (마 26:36-46)
function GethsemaneScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        {/* 감람나무 */}
        <path d="M84 54 q-2 -10 -1 -16 M83 38 q-9 -1 -11 -8 q7 -2.5 11 2 q1 -7 8 -8 q4.5 3.5 3 9 q8 -2 10 4 q-4 7 -12 5 q-4 2 -9 -4" {...sw(1.8)} />
      </g>
      {/* 엎드려 기도 — 주역 */}
      <g style={d(1300, reduce)}>
        <circle cx="42" cy="45" r="2.9" {...sw(2.6)} />
        <path d="M44.5 46.5 q6 -2 10 1.5 M39.5 47 l-5 4 M45 49.5 l4.5 3.5" {...sw(2.6)} />
        <path d="M36 50.5 q2 -1.6 4 -0.5" {...sw(1.4, 0.6)} />
      </g>
      {/* 땀방울 — 핏방울같이 */}
      <g style={d(reduce ? 0 : 2500, reduce)} stroke="var(--paper-accent)">
        <path d="M40 38 q1 1.6 0 3 M45 37.5 q1 1.6 0 3" {...sw(1.6)} />
      </g>
      {/* 잠든 제자들 — 원경 */}
      <g style={d(3100, reduce)}>
        <circle cx="16" cy="50.5" r="2" {...sw(1.5, 0.6)} />
        <path d="M18 51.5 q3.5 -1.2 6 0.8" {...sw(1.5, 0.6)} />
      </g>
      <Label x="46" y="34" at="1.9" reduce={reduce}>겟세마네의 기도</Label>
      <Label x="60" y="61" at="2.9" reduce={reduce} size="4.2">내 원대로 마시고 아버지의 원대로</Label>
    </g>
  )
}

// 십자가 (눅 23:33-46)
function CrucifixionScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M6 52 q20 -5 38 -3 M76 49 q18 -4 32 -2" {...sw(1.2, 0.45)} />
      </g>
      {/* 세 십자가 — 중앙 큰 */}
      <g style={d(1000, reduce)}>
        <path d="M60 54 V14 M48 24 h24" {...sw(2.8)} />
      </g>
      <g style={d(1800, reduce)}>
        <path d="M28 54 V28 M20 35 h16" {...sw(1.8, 0.75)} />
        <path d="M92 54 V28 M84 35 h16" {...sw(1.8, 0.75)} />
      </g>
      {/* 어두워진 하늘 */}
      <g style={d(2600, reduce)}>
        <path d="M14 12 q7 -4 14 0 q7 -4 14 0 M74 10 q7 -4 14 0 q7 -4 14 0" {...sw(1.5, 0.6)} />
      </g>
      <Label x="60" y="10" at="1.4" reduce={reduce}>해골 언덕</Label>
      <Label x="60" y="61" at="3" reduce={reduce} size="4.2">다 이루었다</Label>
    </g>
  )
}

// 십자가 아래 마리아 (요 19:25-27)
function MaryCrossScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M60 54 V14 M48 24 h24" {...sw(2.6)} />
      </g>
      {/* 마리아 — 십자가 아래 */}
      <g style={d(1200, reduce)}>
        <circle cx="42" cy="40" r="2.8" {...sw(2.5)} />
        <path d="M38.5 54 l1.8 -11.5 h3.4 l1.8 11.5 M38.5 54 h7" {...sw(2.5)} />
        <path d="M40 41.5 q2 2.3 4.4 0.4" {...sw(1.9)} />
      </g>
      {/* 요한 — 곁에 */}
      <g style={d(2000, reduce)}>
        <circle cx="78" cy="39.5" r="2.7" {...sw(2.3)} />
        <path d="M78 42.2 v6.8 M75.5 54 l2.5 -5 l2.5 5 M75.5 43.5 q-3 1 -4.5 3" {...sw(2.3)} />
      </g>
      <Label x="38" y="30" at="1.8" reduce={reduce}>마리아</Label>
      <Label x="82" y="30" at="2.6" reduce={reduce}>사랑하는 제자</Label>
      <Label x="60" y="61" at="3" reduce={reduce} size="4.2">보라 네 어머니라</Label>
    </g>
  )
}

// 부활 (눅 24:1-12)
function ResurrectionScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        {/* 열린 무덤 + 굴려진 돌 */}
        <path d="M28 54 q0 -18 18 -18 q18 0 18 18" {...sw(2.4)} />
        <circle cx="14" cy="47" r="6.5" {...sw(2)} />
      </g>
      {/* 빈 세마포 */}
      <g style={d(1400, reduce)}>
        <path d="M40 50 q6 -2.5 12 0 M42 52.5 q5 -2 10 0" {...sw(1.6)} />
      </g>
      {/* 새벽 해 — 상승 */}
      <g transform={reduce ? 'translate(0 -3)' : undefined} style={d(2000, reduce)} stroke="var(--paper-accent)">
        <path d="M88 54 a9 9 0 0 1 18 0" {...sw(2.2)} />
        <path d="M97 41 v-3.5 M87 45 l-2.6 -2.6 M107 45 l2.6 -2.6" {...sw(1.5)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="translate" from="0 3" to="0 -3"
            begin="2.3s" dur="1.8s" fill="freeze" />
        )}
      </g>
      {/* 천사 */}
      <g style={d(2900, reduce)}>
        <circle cx="46" cy="38" r="2.2" {...sw(1.9, 0.85)} />
        <path d="M43 46 l1.4 -5.5 h3.2 l1.4 5.5 M42 40 q-3.5 -1.5 -4.5 -4.5 M50 40 q3.5 -1.5 4.5 -4.5" {...sw(1.9, 0.85)} />
      </g>
      <Label x="46" y="27" at="1.4" reduce={reduce}>빈 무덤</Label>
      <Label x="60" y="61" at="3.2" reduce={reduce} size="4.2">여기 계시지 않고 살아나셨느니라</Label>
    </g>
  )
}

// 승천 (행 1:9-11)
function AscensionScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M6 54 q30 -10 54 -8 q30 -2 54 8" {...sw(1.4, 0.55)} />
      </g>
      {/* 올려지시는 예수 — 핵심: 상승 + 축복의 팔 */}
      <g transform={reduce ? 'translate(0 -14)' : undefined} style={d(1100, reduce)}>
        <circle cx="60" cy="26" r="2.9" {...sw(2.6)} />
        <path d="M56 40 l1.8 -11 h4.4 l1.8 11 M56 40 h8" {...sw(2.6)} />
        <path d="M57 30 q-4.5 -2 -6 -5.5 M63 30 q4.5 -2 6 -5.5" {...sw(2.3)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="translate" from="0 0" to="0 -15"
            begin="2.3s" dur="2s" fill="freeze" calcMode="spline" keySplines="0.35 0 0.55 1" keyTimes="0;1" />
        )}
      </g>
      {/* 구름 */}
      <g style={d(2200, reduce)}>
        <path d="M46 14 q2 -5 8 -4 q3 -4 8 -2 q5 -1 6 3 q4 2 1 5 q-6 3 -12 1.5 q-7 1.5 -11 -3.5" {...sw(1.6, 0.8)} />
      </g>
      {/* 우러러보는 제자들 + 두 천사 */}
      <g style={d(3000, reduce)}>
        <circle cx="34" cy="47" r="2.2" {...sw(1.9)} />
        <path d="M34 49.2 v1.6 M32.3 54 l1.7 -2.6 l1.7 2.6 M32 45.5 l-2.4 -3" {...sw(1.9)} />
        <circle cx="86" cy="47.5" r="2.1" {...sw(1.8, 0.9)} />
        <path d="M86 49.6 v1.4 M84.4 54 l1.6 -2.4 l1.6 2.4 M88 46 l2.4 -3" {...sw(1.8, 0.9)} />
      </g>
      <g style={d(reduce ? 0 : 3600, reduce)} stroke="var(--paper-accent)">
        <path d="M18 30 v-2.6 m-1.3 1.3 h2.6 M102 28 v-2.6 m-1.3 1.3 h2.6" {...sw(1.4)} />
      </g>
      <Label x="60" y="47" at="2.5" reduce={reduce}>감람산</Label>
      <Label x="60" y="61" at="3.6" reduce={reduce} size="4.2">본 그대로 다시 오시리라</Label>
    </g>
  )
}

const SCENES = {
  'authored-mary-nazareth-annunciation': { Scene: AnnunciationScene, desc: '은혜를 받은 자여 — 가브리엘이 이르다', caption: '수태고지 — 누가복음 1장' },
  'authored-mary-judah-visitation': { Scene: VisitationScene, desc: '태중의 아기가 기쁨으로 뛰놀다', caption: '방문 — 누가복음 1장' },
  'authored-john-baptist-birth-naming': { Scene: JohnBirthScene, desc: '그 이름은 요한이라 — 벙어리가 풀리다', caption: '요한의 출생 — 누가복음 1장' },
  'authored-jesus-bethlehem-birth': { Scene: BethlehemBirthScene, desc: '구유에 뉘인 첫 아들', caption: '탄생 — 누가복음 2장' },
  'authored-jesus-temple-presentation': { Scene: TemplePresentationScene, desc: '시므온이 아기를 안고 찬송하다', caption: '성전 봉헌 — 누가복음 2장' },
  'authored-jesus-flight-egypt': { Scene: FlightEgyptScene, mood: 'dark', desc: '헤롯의 칼을 피해 애굽으로 내려가다', caption: '피신 — 마태복음 2장' },
  'authored-jesus-boy-at-temple': { Scene: BoyAtTempleScene, desc: '선생들 가운데서 묻고 대답하다', caption: '열두 살 — 누가복음 2장' },
  'authored-john-baptist-wilderness-ministry': { Scene: JohnWildernessScene, desc: '광야에서 회개를 외치다', caption: '광야의 소리 — 마태복음 3장' },
  'authored-jesus-jordan-baptism': { Scene: JordanBaptismScene, desc: '하늘이 열리고 성령이 비둘기같이 임하다', caption: '세례 — 마태복음 3장' },
  'authored-jesus-wilderness-temptation': { Scene: WildernessTemptationScene, desc: '말씀으로 세 가지 시험을 물리치다', caption: '광야 시험 — 마태복음 4장' },
  'authored-mary-cana-wedding': { Scene: CanaWeddingScene, desc: '물이 변하여 포도주가 되다', caption: '가나 혼인 잔치 — 요한복음 2장' },
  'authored-jesus-capernaum-base': { Scene: CapernaumBaseScene, desc: '바닷가 가버나움에 자리 잡으시다', caption: '갈릴리 — 마태복음 4장' },
  'authored-jesus-sermon-mount': { Scene: SermonMountScene, desc: '산에 올라 팔복을 선포하시다', caption: '산상수훈 — 마태복음 5장' },
  'authored-john-baptist-machaerus-death': { Scene: MachaerusDeathScene, mood: 'dark', desc: '예비하는 자의 길이 끝나다', caption: '순교 — 마가복음 6장' },
  'authored-jesus-caesarea-philippi': { Scene: CaesareaPhilippiScene, desc: '너희는 나를 누구라 하느냐', caption: '베드로의 고백 — 마태복음 16장' },
  'authored-jesus-bethany-lazarus': { Scene: LazarusScene, desc: '나사로야 나오라', caption: '베다니 — 요한복음 11장' },
  'authored-jesus-triumphal-entry': { Scene: TriumphalEntryScene, desc: '호산나 — 종려가지를 흔들다', caption: '입성 — 마태복음 21장' },
  'authored-jesus-last-supper': { Scene: LastSupperScene, desc: '떡을 떼어 이것은 내 몸이라 하시다', caption: '최후의 만찬 — 누가복음 22장' },
  'authored-jesus-gethsemane-prayer': { Scene: GethsemaneScene, mood: 'dark', desc: '땀이 핏방울같이 되도록 기도하시다', caption: '겟세마네 — 마태복음 26장' },
  'authored-jesus-crucifixion': { Scene: CrucifixionScene, mood: 'dark', desc: '다 이루었다', caption: '십자가 — 누가복음 23장' },
  'authored-mary-jerusalem-cross': { Scene: MaryCrossScene, mood: 'dark', desc: '보라 네 어머니라 — 십자가 아래에서', caption: '어머니 — 요한복음 19장' },
  'authored-jesus-resurrection': { Scene: ResurrectionScene, desc: '돌이 굴려지고 무덤이 비다', caption: '부활 — 누가복음 24장' },
  'authored-jesus-ascension': { Scene: AscensionScene, desc: '축복하시며 하늘로 올려지시다', caption: '승천 — 사도행전 1장' },
}

export default SCENES
