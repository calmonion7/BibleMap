// 예수의 생애 — 23개 정차지 장면 (task#231, #227 표준). 세 인물(요한·예수·마리아) 교차 서사.
import { sw, d } from './lib'
import { Label } from './SceneLabel'
// 인트로 오프닝 몽타주가 쓰는 장면 — 정의는 introMontage.jsx로 옮겼다(task#287).
// 방향이 중요하다: 무거운 투어 모듈이 소형 모듈을 참조해야 인트로가 투어 청크를 끌어오지 않는다.
import { BethlehemBirthScene } from './introMontage'

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

// 동방박사의 경배 (마 2:1-12)
function MagiVisitScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M56 54 v-15 h16 v15 M56 39 l8 -7 l8 7" {...sw(1.8)} />
      </g>
      {/* 아기 — 문간 안 */}
      <g style={d(900, reduce)}>
        <circle cx="64" cy="43.5" r="1.8" {...sw(2)} />
        <path d="M61.5 49.5 q2.5 -2 5 0" {...sw(1.6)} />
      </g>
      {/* 박사 셋 — 엎드려 경배 */}
      <g style={d(1700, reduce)}>
        <circle cx="40" cy="39" r="2.7" {...sw(2.6)} />
        <path d="M36.5 52 l2 -10.5 h3 l3 5 q3 1 5 -0.5" {...sw(2.6)} />
        <path d="M34 50 h5 v3 h-5 z" {...sw(1.8)} />
        <circle cx="26" cy="41" r="2.3" {...sw(2.1)} />
        <path d="M23 52 l1.8 -9 h2.6 l2.6 4.5 q2.5 1 4 -0.5" {...sw(2.1)} />
        <path d="M21 50.5 h4 v2.6 h-4 z" {...sw(1.6, 0.85)} />
        <circle cx="14" cy="43" r="1.9" {...sw(1.8, 0.8)} />
        <path d="M11.5 52 l1.5 -7.5 h2.2 l2 4 q2 0.8 3.3 -0.4" {...sw(1.8, 0.8)} />
      </g>
      {/* 별 — 강조 */}
      <g style={d(reduce ? 0 : 2500, reduce)} stroke="var(--paper-accent)">
        <path d="M64 12 v4 m-2 -2 h4 M60.5 9.5 l-1.6 -1.6 M67.5 9.5 l1.6 -1.6" {...sw(1.7)} />
      </g>
      <Label x="26" y="30" at="1.9" reduce={reduce}>동방박사</Label>
      <Label x="60" y="61" at="2.7" reduce={reduce} size="4.2">황금과 유향과 몰약을 드리다</Label>
    </g>
  )
}

// 나사렛 유년기 (눅 2:39-40, 51-52)
function NazarethChildhoodScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M14 54 v-10 h14 v10 M14 44 l7 -6 l7 6 M90 54 v-9 h13 v9 M90 45 l6.5 -5.5 l6.5 5.5" {...sw(1.5, 0.6)} />
        <path d="M96 52 q2 -2 4 0" {...sw(1.3, 0.6)} />
      </g>
      {/* 목수 요셉 — 배경 작업 */}
      <g style={d(1100, reduce)}>
        <circle cx="82" cy="41" r="2.3" {...sw(1.9, 0.85)} />
        <path d="M79.5 54 l1.5 -9.5 h3 l1.5 9.5 M77 47 h4" {...sw(1.9, 0.85)} />
      </g>
      {/* 소년 예수 — 곧게 자람, 주역 */}
      <g style={d(1900, reduce)}>
        <circle cx="42" cy="35" r="2.7" {...sw(2.6)} />
        <path d="M42 37.7 v10.3 M39 54 l3 -6 l3 6" {...sw(2.6)} />
        <path d="M39.5 40 q2.5 1.4 5 0" {...sw(1.3, 0.6)} />
      </g>
      {/* 나무 — 자람의 상징 */}
      <g style={d(2700, reduce)}>
        <path d="M56 54 v-10 M56 44 q-4 -1 -5 -5 M56 44 q4 -1 5 -5" {...sw(1.4, 0.6)} />
      </g>
      <Label x="42" y="25" at="2.2" reduce={reduce}>나사렛</Label>
      <Label x="60" y="61" at="3" reduce={reduce} size="4.2">지혜와 키가 자라가시며</Label>
    </g>
  )
}

// 첫 제자들 (요 1:35-39)
function JohnFirstDiscipleScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M6 50 q14 -4 28 0" {...sw(1.2, 0.45)} />
      </g>
      {/* 요한 — 가리킴 */}
      <g style={d(1000, reduce)}>
        <circle cx="24" cy="30" r="2.8" {...sw(2.4)} />
        <path d="M19.5 54 l2.2 -21.5 h4.6 l2.2 21.5 M19.5 54 h9" {...sw(2.4)} />
        <path d="M28 33 q6 -1 9 -4" {...sw(2)} />
      </g>
      {/* 어린 양 — 강조 상징 */}
      <g style={d(1700, reduce)} stroke="var(--paper-accent)">
        <path d="M40 50 q0 -3 3 -3 q3 0 3 3 M40 50 h6 M41.5 47 q-1 -2 0.5 -3 M44.5 47 q1 -2 -0.5 -3" {...sw(1.6)} />
      </g>
      {/* 예수 — 앞서 걸음 */}
      <g style={d(2300, reduce)}>
        <circle cx="70" cy="31" r="2.9" {...sw(2.6)} />
        <path d="M70 33.9 v9.1 M67 54 l3 -11 l3 11" {...sw(2.6)} />
      </g>
      {/* 두 제자 — 뒤따름 */}
      <g style={d(3000, reduce)}>
        <circle cx="84" cy="37" r="2.2" {...sw(1.9)} />
        <path d="M84 39.2 v6.8 M81.5 54 l2.5 -8 l2.5 8" {...sw(1.9)} />
        <circle cx="94" cy="38" r="2.1" {...sw(1.8, 0.9)} />
        <path d="M94 40.1 v6 M91.7 54 l2.3 -7.9 l2.3 7.9" {...sw(1.8, 0.9)} />
      </g>
      <Label x="24" y="21" at="1.6" reduce={reduce}>세례 요한</Label>
      <Label x="60" y="61" at="3.3" reduce={reduce} size="4.2">보라 하나님의 어린 양이로다</Label>
    </g>
  )
}

// 제자들을 부르심 (마 4:18-22)
function CallDisciplesScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M8 48 q8 -3 16 0 q8 -3 16 0 q8 -3 16 0 q8 -3 16 0 q8 -3 16 0 q8 -3 16 0" {...sw(2)} />
      </g>
      {/* 예수 — 부르심 */}
      <g style={d(1000, reduce)}>
        <circle cx="26" cy="31" r="2.9" {...sw(2.6)} />
        <path d="M21.5 54 l2.2 -20 h4.6 l2.2 20 M21.5 54 h9 M29.5 35 q5 -1.5 8 0.5" {...sw(2.6)} />
      </g>
      {/* 배 + 그물 던지는 어부 형제 */}
      <g style={d(1900, reduce)}>
        <path d="M70 48 q2 4 7 4 h14 q5 0 7 -4 l-3 -3.5 h-22 z" {...sw(2.2)} />
        <circle cx="80" cy="37" r="2.4" {...sw(2.2)} />
        <path d="M80 39.4 v6.6 M83 42 q3 -1 5 -3" {...sw(2.2)} />
        <circle cx="94" cy="38" r="2.2" {...sw(2)} />
        <path d="M94 40.2 v6 M91 43 q-3 -1 -4.5 -3" {...sw(2)} />
      </g>
      {/* 버려지는 그물 */}
      <g style={d(2700, reduce)}>
        <path d="M85 44 l4 -8 M89 44 l4 -8 M84 40 h9" {...sw(1.4, 0.6)} />
      </g>
      <Label x="26" y="21" at="1.6" reduce={reduce}>예수</Label>
      <Label x="60" y="61" at="3.1" reduce={reduce} size="4.2">나를 따라오라 — 사람을 낚는 어부가 되게 하리라</Label>
    </g>
  )
}

// 가버나움 치유 (막 1:21-34)
function CapernaumHealingScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M16 54 v-22 M28 54 v-22 M13 32 h18" {...sw(1.5, 0.6)} />
      </g>
      {/* 귀신 들린 자 — 쫓겨남 */}
      <g style={d(1000, reduce)}>
        <circle cx="22" cy="41" r="2.4" {...sw(2.1)} />
        <path d="M19 54 l1.5 -10 h3 l1.5 10" {...sw(2.1)} />
        <path d="M25 40 q3 -1.5 3.5 -4.5 q1 3 3.5 3" {...sw(1.3, 0.5)} strokeDasharray="1.4 1.6" />
      </g>
      {/* 예수 — 말씀의 권위 */}
      <g style={d(1900, reduce)}>
        <circle cx="56" cy="30" r="2.9" {...sw(2.6)} />
        <path d="M51.5 54 l2.2 -21 h4.6 l2.2 21 M51.5 54 h9 M59.5 34 q4 -1.5 6 1" {...sw(2.6)} />
      </g>
      {/* 저녁 — 몰려오는 병자들 */}
      <g style={d(2700, reduce)}>
        <circle cx="80" cy="46" r="1.9" {...sw(1.7, 0.85)} />
        <path d="M78 54 l1 -6 h2 l1 6" {...sw(1.7, 0.85)} />
        <circle cx="90" cy="45.5" r="1.9" {...sw(1.7, 0.85)} />
        <path d="M88 54 l1 -6.5 h2 l1 6.5" {...sw(1.7, 0.85)} />
        <circle cx="100" cy="46" r="1.9" {...sw(1.7, 0.85)} />
        <path d="M98 54 l1 -6 h2 l1 6" {...sw(1.7, 0.85)} />
      </g>
      <Label x="56" y="20" at="2.2" reduce={reduce}>가버나움 회당</Label>
      <Label x="60" y="61" at="3" reduce={reduce} size="4.2">온 성이 병자를 데리고 모이더라</Label>
    </g>
  )
}

// 요한의 투옥 (막 6:17-18)
function JohnBaptistPrisonScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M60 54 v-22 h34 v22 M64 32 v-4 h5 v4 m6 0 v-4 h5 v4 m6 0 v-4 h5 v4" {...sw(2.2)} />
      </g>
      {/* 요한 — 갇힘 */}
      <g style={d(1200, reduce)}>
        <circle cx="76" cy="42" r="2.5" {...sw(2.4)} />
        <path d="M73 54 l1.6 -12 h3.2 l1.6 12" {...sw(2.4)} />
        <path d="M71 40 v10 M73 40 v10 M75 40 v10 M77 40 v10 M79 40 v10 M81 40 v10" {...sw(1.6, 0.8)} />
      </g>
      {/* 헤롯 — 왕관, 거리를 둔 */}
      <g style={d(2100, reduce)}>
        <circle cx="26" cy="38" r="2.6" {...sw(2)} />
        <path d="M22.5 54 l1.7 -14.5 h3.6 l1.7 14.5" {...sw(2)} />
        <path d="M23 35 v-2.6 l1.4 1.4 l1.2 -2 l1.2 2 l1.4 -1.4 v2.6 z" {...sw(1.6, 0.8)} />
      </g>
      <Label x="76" y="33" at="1.9" reduce={reduce}>요한</Label>
      <Label x="60" y="61" at="2.9" reduce={reduce} size="4.2">헤롯의 불법을 책망하다 갇히다</Label>
    </g>
  )
}

// 베드로라 이름을 주심 (눅 6:12-14)
function PeterNamedScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M14 54 Q60 26 106 54" {...sw(2)} />
        <path d="M18 16 v2.4 m-1.2 -1.2 h2.4 M30 10 v2 m-1 -1 h2 M96 14 v2.4 m-1.2 -1.2 h2.4" {...sw(1.2, 0.5)} />
      </g>
      {/* 예수 — 산 위 */}
      <g style={d(1100, reduce)}>
        <circle cx="60" cy="28" r="2.9" {...sw(2.6)} />
        <path d="M60 30.9 v9.1 M56.5 54 l3.5 -8 l3.5 8" {...sw(2.6)} />
      </g>
      {/* 시몬 — 새 이름 받음 */}
      <g style={d(2000, reduce)}>
        <circle cx="42" cy="40" r="2.6" {...sw(2.4)} />
        <path d="M39 54 l1.6 -11.5 h3.2 l1.6 11.5 M44.5 44 q3.5 -1 5.5 1" {...sw(2.4)} />
      </g>
      {/* 반석 — 강조 */}
      <g style={d(reduce ? 0 : 2700, reduce)} stroke="var(--paper-accent)">
        <path d="M46 52 q-1 -4 2.5 -5 q4 -1 4.5 3 q0.5 3 -2.5 3.5 z" {...sw(1.8)} />
      </g>
      <Label x="42" y="30" at="2.3" reduce={reduce}>시몬</Label>
      <Label x="60" y="61" at="3" reduce={reduce} size="4.2">네 이름은 베드로 — 반석이라</Label>
    </g>
  )
}

// 옥중에서 보낸 질문 (마 11:2-6)
function JohnPrisonQuestionScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M8 54 v-18 h16 v18 M10 40 v10 M13 40 v10 M16 40 v10 M19 40 v10" {...sw(1.8, 0.8)} />
      </g>
      {/* 요한 — 창살 안 */}
      <g style={d(1000, reduce)}>
        <circle cx="16" cy="37" r="2.3" {...sw(2.1)} />
        <path d="M13.5 47 l1.5 -8.5 h2 l1.5 8.5" {...sw(2.1)} />
      </g>
      {/* 두 제자 — 전하러 감 */}
      <g transform={reduce ? 'translate(10 0)' : undefined} style={d(1800, reduce)}>
        <circle cx="46" cy="42" r="2.1" {...sw(1.9)} />
        <path d="M46 44.1 v6.9 M43.7 54 l2.3 -7 l2.3 7" {...sw(1.9)} />
        <circle cx="56" cy="42.5" r="2" {...sw(1.8, 0.9)} />
        <path d="M56 44.5 v6.5 M53.8 54 l2.2 -6.6 l2.2 6.6" {...sw(1.8, 0.9)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="translate" from="0 0" to="12 0"
            begin="2.1s" dur="1.8s" fill="freeze" calcMode="spline" keySplines="0.3 0 0.7 1" keyTimes="0;1" />
        )}
      </g>
      {/* 예수 — 응답의 증거 */}
      <g style={d(2600, reduce)}>
        <circle cx="90" cy="33" r="2.8" {...sw(2.5)} />
        <path d="M85.5 54 l2.2 -18.5 h4.6 l2.2 18.5 M85.5 54 h9" {...sw(2.5)} />
      </g>
      <g style={d(reduce ? 0 : 3300, reduce)} stroke="var(--paper-accent)">
        <path d="M78 46 q1.5 -1.5 3 0 M79.5 44.6 v-1.6 M100 48 l2.4 -1 m-2.4 3 l2.4 1" {...sw(1.4)} />
      </g>
      <Label x="16" y="28" at="1.4" reduce={reduce}>요한</Label>
      <Label x="60" y="61" at="3.5" reduce={reduce} size="4.2">맹인이 보며 못 걷는 자가 걸으며</Label>
    </g>
  )
}

// 오병이어 (요 6:1-13)
function BethsaidaFeedingScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M6 50 q20 -5 38 -2 M76 48 q18 -4 32 -1" {...sw(1.2, 0.45)} />
      </g>
      {/* 예수 — 축사 */}
      <g style={d(1000, reduce)}>
        <circle cx="56" cy="29" r="2.9" {...sw(2.6)} />
        <path d="M51.5 54 l2.2 -20.5 h4.6 l2.2 20.5 M51.5 54 h9 M59.5 33 q4 -1.5 6 1" {...sw(2.6)} />
      </g>
      {/* 떡 다섯 개와 물고기 두 마리 — 핵심 */}
      <g style={d(1900, reduce)} stroke="var(--paper-accent)">
        <path d="M66 46 q0 -2.4 2.4 -2.4 q2.4 0 2.4 2.4 q0 2.4 -2.4 2.4 q-2.4 0 -2.4 -2.4 z" {...sw(1.6)} />
        <path d="M72 46 q0 -2.4 2.4 -2.4 q2.4 0 2.4 2.4 q0 2.4 -2.4 2.4 q-2.4 0 -2.4 -2.4 z" {...sw(1.6)} />
        <path d="M78 47 q3 -1.5 5 0 q-2 1.8 -5 0 z" {...sw(1.5)} />
      </g>
      {/* 무리 — 원경 */}
      <g style={d(2200, reduce)}>
        <circle cx="30" cy="47" r="1.8" {...sw(1.4, 0.6)} />
        <path d="M30 48.8 v5.2" {...sw(1.4, 0.6)} />
        <circle cx="38" cy="48" r="1.7" {...sw(1.3, 0.55)} />
        <path d="M38 49.7 v4.3" {...sw(1.3, 0.55)} />
        <circle cx="86" cy="47.5" r="1.8" {...sw(1.4, 0.6)} />
        <path d="M86 49.3 v4.7" {...sw(1.4, 0.6)} />
      </g>
      {/* 열두 바구니 — 남은 조각 */}
      <g style={d(2700, reduce)}>
        <path d="M18 50 q0 -3 3 -3 h6 q3 0 3 3 v2 h-12 z" {...sw(1.8)} />
        <path d="M94 50 q0 -3 3 -3 h6 q3 0 3 3 v2 h-12 z" {...sw(1.8)} />
      </g>
      <Label x="72" y="38" at="2.2" reduce={reduce}>떡 다섯 물고기 두</Label>
      <Label x="60" y="61" at="3" reduce={reduce} size="4.2">열두 바구니에 차고 넘치다</Label>
    </g>
  )
}

// 베드로, 물 위를 걷다 (마 14:22-33)
function PeterWaterScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M8 48 q8 -3 16 0 q8 -3 16 0 q8 -3 16 0 q8 -3 16 0 q8 -3 16 0 q8 -3 16 0" {...sw(2)} />
      </g>
      {/* 예수 — 물 위, 손 내미심 */}
      <g style={d(1100, reduce)}>
        <circle cx="72" cy="34" r="2.8" {...sw(2.6)} />
        <path d="M67.5 50 l2.2 -16 h4.6 l2.2 16" {...sw(2.6)} />
        <path d="M67.5 44 q-5 1 -7 4" {...sw(2.2)} />
      </g>
      {/* 베드로 — 가라앉음 */}
      <g transform={reduce ? 'translate(0 4)' : undefined} style={d(2000, reduce)}>
        <circle cx="48" cy="38" r="2.6" {...sw(2.4)} />
        <path d="M45 52 l1.7 -12 h3.4 l1.7 12 M52 41 q4 1 6 -2" {...sw(2.4)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="translate" from="0 0" to="0 4"
            begin="2.4s" dur="1.6s" fill="freeze" calcMode="spline" keySplines="0.4 0 0.6 1" keyTimes="0;1" />
        )}
      </g>
      <g style={d(reduce ? 0 : 3200, reduce)}>
        <path d="M40 50 q2 -2 0 -4 M56 51 q-2 -2 0 -4" {...sw(1.3, 0.5)} />
      </g>
      <Label x="48" y="27" at="2.3" reduce={reduce}>베드로</Label>
      <Label x="60" y="61" at="3.4" reduce={reduce} size="4.2">믿음이 작은 자여 왜 의심하였느냐</Label>
    </g>
  )
}

// 변화산 (마 17:1-8)
function TransfigurationScene({ reduce }) {
  return (
    <g>
      {/* 지면 + 원경 산 + 능선(원근) */}
      <g style={d(0, reduce)}>
        <path d="M4 54 H119" {...sw(1.6)} />
        <path d="M4 44 Q16 38 26 37 Q36 32 44 34 Q52 22 60 20 Q64 10 68 20 Q76 24 84 33 Q94 32 104 37 Q114 40 116 44" {...sw(1.8)} />
      </g>
      <g style={d(130, reduce)}>
        <path d="M4 50 q9 -5 16 -2" {...sw(1.1, 0.55)} />
        <path d="M100 52 q3 -2 6 -1" {...sw(1.3, 0.6)} />
        <path d="M24 12 q6 -2 12 0 q5 -2 9 1" {...sw(1.1, 0.55)} />
      </g>
      <g style={d(260, reduce)}>
        <path d="M8 44 v-6 M6 40 q2 -2 4 0" {...sw(1.2, 0.45)} />
        <path d="M111 44 v-6 M109 40 q2 -2 4 0" {...sw(1.2, 0.45)} />
        <path d="M21 53.5 q1.5 -1.8 3 0" {...sw(1.2, 0.45)} />
      </g>
      <g style={d(390, reduce)}>
        <path d="M97 53.5 q1.5 -1.8 3 0" {...sw(1.2, 0.45)} />
        <path d="M48 53.6 q0.8 -1.3 1.6 0" {...sw(1.1, 0.4)} />
        <path d="M100 53.6 q0.8 -1.3 1.6 0" {...sw(1.1, 0.4)} />
      </g>
      <g style={d(520, reduce)}>
        <path d="M46 53.7 l0.7 -0.7 l0.7 0.7" {...sw(1.1, 0.4)} />
        <path d="M6 53.6 l0.6 -0.6 l0.6 0.6" {...sw(1.1, 0.4)} />
        <path d="M113 53.6 l0.6 -0.6 l0.6 0.6" {...sw(1.1, 0.4)} />
      </g>
      <g style={d(585, reduce)}>
        <path d="M95 13 q2 -2 4 0" {...sw(1.1, 0.5)} />
        <path d="M28 17 q4 -2.5 8 0" {...sw(1.1, 0.45)} />
      </g>

      {/* ── 예수 — 머리·목·겉옷(광채의 중심) ── */}
      <g style={d(650, reduce)}>
        <circle cx="60" cy="25" r="4.2" {...sw(2.6)} />
        <path d="M57.9 28.6 L55 31 M62.1 28.6 L65 31" {...sw(2.6)} />
        <path d="M52 54 L55 31 L65 31 L68 54" {...sw(2.6)} />
      </g>
      <g style={d(780, reduce)}>
        <path d="M55 31 q-3 5 -1 9 M65 31 q3 5 1 9" {...sw(2.2)} />
        <path d="M60 33 v18" {...sw(1.3, 0.5)} />
        <path d="M56.5 31.4 q3.5 1.5 7 0" {...sw(1.4)} />
      </g>
      <g style={d(910, reduce)}>
        <path d="M58 31.8 L60 34 L62 31.8" {...sw(1.3)} />
        <path d="M57 41.3 H63" {...sw(1.8)} />
        <path d="M57 41.3 l-0.7 1.1 M63 41.3 l0.7 1.1" {...sw(1.2)} />
      </g>
      <g style={d(1040, reduce)}>
        <path d="M54.5 35 q-0.6 2 0 3.6" {...sw(1.2)} />
        <path d="M65.5 35 q0.6 2 0 3.6" {...sw(1.2)} />
        <path d="M53.7 39.5 q1 1 1.9 0.3" {...sw(1.4)} />
      </g>
      <g style={d(1170, reduce)}>
        <path d="M66.3 39.5 q-1 1 -1.9 0.3" {...sw(1.4)} />
        <path d="M53.9 39.7 q-0.4 -1 0.3 -1.8" {...sw(1.1)} />
        <path d="M66.1 39.7 q0.4 -1 -0.3 -1.8" {...sw(1.1)} />
      </g>
      <g style={d(1300, reduce)}>
        <path d="M64 31 q3 1 4 4" {...sw(1.4)} />
        <path d="M66 36 q0.6 3 -0.4 5.5" {...sw(1.2)} />
        <path d="M52 54 h2.2 M65.8 54 h2.2" {...sw(1.4)} />
      </g>
      <g style={d(1430, reduce)}>
        <path d="M52.5 54.3 q0.8 0.5 1.5 0 M65.3 54.3 q0.8 0.5 1.5 0" {...sw(1.1)} />
        <path d="M55.5 53 q0.8 -0.5 1.4 0 M64.5 53 q-0.8 -0.5 -1.4 0" {...sw(1.2)} />
        <path d="M55 45 q0.8 4.5 0 8" {...sw(1.3)} />
      </g>
      <g style={d(1560, reduce)}>
        <path d="M65 45 q-0.8 4.5 0 8" {...sw(1.3)} />
        <path d="M58 49 q0.5 2 0 3.5" {...sw(1.1)} />
        <path d="M62 49 q-0.5 2 0 3.5" {...sw(1.1)} />
      </g>
      <g style={d(1690, reduce)}>
        <path d="M57 32.6 q3 0.6 6 0" {...sw(1.2)} />
        <path d="M58 22.6 q0.6 -0.3 1.2 0 M60.8 22.6 q0.6 -0.3 1.2 0" {...sw(1.1, 0.6)} />
        <path d="M58.5 24 h1 M61.5 24 h1" {...sw(1.1)} />
      </g>
      <g style={d(1820, reduce)}>
        <path d="M59 26.5 q1 0.4 2 0" {...sw(1.1)} />
        <path d="M56.6 22 q-1 2 -0.6 3.6 M63.4 22 q1 2 0.6 3.6" {...sw(1.2, 0.55)} />
        <circle cx="60" cy="25" r="5.3" {...sw(1.3, 0.4)} stroke="var(--paper-accent)" />
      </g>
      <g style={d(1950, reduce)}>
        <circle cx="60" cy="25" r="7" {...sw(1.1, 0.3)} stroke="var(--paper-accent)" />
        <path d="M60.9 20.3 L61.5 17.3 M59.1 20.3 L58.5 17.3" {...sw(1.3, 0.55)} stroke="var(--paper-accent)" />
        <path d="M62.7 21 L64.4 18.5 M57.3 21 L55.6 18.5" {...sw(1.3, 0.55)} stroke="var(--paper-accent)" />
      </g>
      <g style={d(2080, reduce)}>
        <path d="M64 22.4 L66.5 20.8 M56 22.4 L53.5 20.8" {...sw(1.3, 0.55)} stroke="var(--paper-accent)" />
        <path d="M64.7 24.2 L67.7 23.6 M55.3 24.2 L52.3 23.6" {...sw(1.3, 0.55)} stroke="var(--paper-accent)" />
        <path d="M53.5 24.5 L49.5 25.5 M66.5 24.5 L70.5 25.5" {...sw(1.2, 0.5)} stroke="var(--paper-accent)" />
      </g>
      <g style={d(2210, reduce)}>
        <path d="M56.3 26 L52.5 27.5 M63.7 26 L67.5 27.5" {...sw(1.2, 0.5)} stroke="var(--paper-accent)" />
        <path d="M50 24 L46 24.5 M70 24 L74 24.5" {...sw(1.2, 0.5)} stroke="var(--paper-accent)" />
        <path d="M56 46 l0.6 0.6 M64 46 l-0.6 0.6" {...sw(1.1, 0.5)} stroke="var(--paper-accent)" />
      </g>
      <g style={d(2340, reduce)}>
        <path d="M60 44 l0 0.8" {...sw(1.1, 0.5)} stroke="var(--paper-accent)" />
        <path d="M62 50 l0.5 0.5" {...sw(1.1, 0.5)} stroke="var(--paper-accent)" />
        <path d="M58 42 l0.4 0.4" {...sw(1.1, 0.5)} stroke="var(--paper-accent)" />
      </g>
      <g style={d(2405, reduce)}>
        <path d="M56.5 47 q0.4 3 0 5" {...sw(1.1)} />
      </g>

      {/* ── 모세 — 머리·수염·겉옷·두 돌판(예수 쪽을 봄) ── */}
      <g style={d(2470, reduce)}>
        <circle cx="34" cy="29" r="4" {...sw(2.4)} />
        <path d="M32 32.46 L29 35 M36 32.46 L39 35" {...sw(2.4)} />
        <path d="M33.1 28 h1 M35.9 28 h1" {...sw(1.1)} />
      </g>
      <g style={d(2600, reduce)}>
        <path d="M33.5 30.4 q1 0.9 2 0" {...sw(1.1)} />
        <path d="M26 54 L29 35 L39 35 L42 54" {...sw(2.4)} />
        <path d="M30 37 q0.3 8 -1 14" {...sw(1.3)} />
      </g>
      <g style={d(2730, reduce)}>
        <path d="M38 37 q-0.3 8 1 14" {...sw(1.3)} />
        <path d="M29 35 Q29.7 37.5 29.5 40 M39 35 Q38.3 37.5 38.5 40" {...sw(2.4)} />
        <path d="M31 43 V41.3 Q31 39.6 32 39.6 Q33 39.6 33 41.3 V43 Z" {...sw(2.1)} />
      </g>
      <g style={d(2860, reduce)}>
        {/* 두 돌판 — 하나로 이어진 상자+가로대가 창틀로 읽혀 둘로 갈랐다(task#303 UAT 결함A).
            다리 주름 시작점과 겹쳐 통기둥으로 보여, 폭을 좁히고 안쪽으로 모아 다리 주름과
            간격을 뒀다(루프 3). */}
        <path d="M35 43 V41.3 Q35 39.6 36 39.6 Q37 39.6 37 41.3 V43 Z" {...sw(2.1)} />
        <path d="M31.5 41.5 H32.5 M35.5 41.5 H36.5" {...sw(1.1, 0.5)} />
        <path d="M27.5 44 q0.4 4 -0.3 7" {...sw(1.2)} />
      </g>
      <g style={d(2990, reduce)}>
        <path d="M40.5 44 q0.4 4 -0.3 7" {...sw(1.2)} />
        <path d="M29.5 40.3 q0.8 0.6 1.6 0 M38.5 40.3 q-0.8 0.6 -1.6 0" {...sw(1.4)} />
        <path d="M32.3 32.8 Q34 35.6 35.7 32.8" {...sw(2.0)} />
      </g>
      <g style={d(3120, reduce)}>
        <path d="M33 33.2 L32.7 35.2 M35 33.2 L35.3 35.2" {...sw(1.3, 0.55)} />
        <path d="M34 35.4 q0.8 1 1.6 0" {...sw(1.2, 0.55)} />
        <path d="M30.6 26.2 q3.4 -2.4 6.8 0" {...sw(1.4)} />
      </g>
      {/* 눈썹과 눈 사이 여분 호 2개(리뷰 task#303 S5) 제거 — 대칭 인물 엘리야 대비 얼굴이
          번잡해 보였다(7선→5선, 눈썹2+눈2+입1로 정리). */}
      <g style={d(3250, reduce)}>
        <path d="M30.6 26.2 l-0.5 1.4 M37.4 26.2 l0.5 1.4" {...sw(1.1)} />
        <path d="M32.3 26.6 q0.9 -0.4 1.7 0 M34.9 26.6 q0.9 -0.4 1.7 0" {...sw(1.1, 0.6)} />
      </g>
      <g style={d(3510, reduce)}>
        <path d="M31 32.6 q3 1 6 0" {...sw(1.3)} />
        <path d="M28.2 38 q-0.5 2 0 3.4" {...sw(1.2)} />
        <path d="M39.8 38 q0.5 2 0 3.4" {...sw(1.2)} />
      </g>
      <g style={d(3640, reduce)}>
        <path d="M29.5 36.5 q0.4 2 0 3.5" {...sw(1.2)} />
        <path d="M28 45 q0.3 5 -0.5 8" {...sw(1.3)} />
        <path d="M40 45 q-0.3 5 0.5 8" {...sw(1.3)} />
      </g>
      <g style={d(3770, reduce)}>
        <path d="M26 54 h2.3 M39.7 54 h2.3" {...sw(1.4)} />
        <path d="M25 54.4 q1.4 0.5 2.6 -0.2" {...sw(1.2, 0.45)} />
        <path d="M43 53.7 l0.7 -0.7 l0.7 0.7" {...sw(1.1, 0.4)} />
      </g>
      <g style={d(3900, reduce)}>
        <path d="M29.3 47.4 H31.6 M36.4 47.4 H38.7" {...sw(1.1)} />
        <path d="M27 51.5 q1.2 -0.6 2.2 0.3 M39.8 51.8 q1.2 -0.6 2.2 0.3" {...sw(1.2)} />
        <path d="M37.4 26.2 q1.6 1.2 1 3" {...sw(1.2, 0.55)} />
      </g>
      <g style={d(4030, reduce)}>
        <path d="M35.5 34.4 q0.7 0.9 1.4 0" {...sw(1.1, 0.55)} />
        <path d="M28 51 q1 -1.4 2 0 M39 51 q1 -1.4 2 0" {...sw(1.1, 0.5)} />
        <path d="M31.5 51.8 q1 -0.6 1.8 0.2" {...sw(1.1, 0.5)} />
      </g>
      <g style={d(4095, reduce)}>
        <path d="M34 36.2 q0.5 1 1 0" {...sw(1.1, 0.5)} />
      </g>

      {/* ── 엘리야 — 머리·수염·망토·지팡이(예수 쪽을 봄) ── */}
      <g style={d(4160, reduce)}>
        <circle cx="86" cy="29" r="4" {...sw(2.4)} />
        <path d="M84 32.46 L81 35 M88 32.46 L91 35" {...sw(2.4)} />
        <path d="M84.1 28 h1 M86.9 28 h1" {...sw(1.1)} />
      </g>
      <g style={d(4290, reduce)}>
        <path d="M84.5 30.4 q1 0.9 2 0" {...sw(1.1)} />
        <path d="M78 54 L79.4 45 L81 35 L91 35 L92.6 45 L94 54" {...sw(2.4)} />
        <path d="M91 35 Q94 39 97 42" {...sw(2.4)} />
      </g>
      <g style={d(4420, reduce)}>
        <path d="M97 54 L97 42 L97 20" {...sw(2.3)} />
        <path d="M97 20 q-2.4 -1.6 -4.3 0" {...sw(2.0)} />
        <path d="M97 42 q0.6 0.9 1.5 0.4" {...sw(1.4)} />
      </g>
      <g style={d(4550, reduce)}>
        <path d="M81 35 q-2.4 3 -2 6.5" {...sw(2.2)} />
        <path d="M79 41.5 q0.9 0.9 1.8 0.2" {...sw(1.4)} />
        <path d="M83.7 32.8 Q86 35.8 88.3 32.8" {...sw(2.0)} />
      </g>
      <g style={d(4680, reduce)}>
        <path d="M84.7 33.2 L84.3 35.4 M87.3 33.2 L87.7 35.4" {...sw(1.3, 0.55)} />
        <path d="M86 35.6 q0.8 1 1.6 0" {...sw(1.2, 0.55)} />
        <path d="M83.3 25.3 q1.3 -1.8 2.4 -0.5 M89.3 25.3 q-1.3 -1.8 -2.4 -0.5" {...sw(1.2, 0.55)} />
      </g>
      <g style={d(4810, reduce)}>
        <path d="M83.7 26.6 q0.9 -0.4 1.7 0 M87.3 26.6 q0.9 -0.4 1.7 0" {...sw(1.1, 0.6)} />
        <path d="M83.5 35.6 q2 1 4 0" {...sw(1.3)} />
        <path d="M81 40 q-0.3 8 0.7 13" {...sw(1.3)} />
      </g>
      <g style={d(4940, reduce)}>
        <path d="M91 40 q0.3 8 -0.7 13" {...sw(1.3)} />
        <path d="M78.5 47 q-1.4 3 -0.8 6" {...sw(1.3)} />
        <path d="M92.5 47 q1.2 3 0.6 6" {...sw(1.3)} />
      </g>
      <g style={d(5070, reduce)}>
        <path d="M78 54 h2.3 M91.7 54 h2.3" {...sw(1.4)} />
        {/* 허리끈 — 곧은 전폭 가로대(창틀 상 다리) 대신 처진 매듭으로(task#303 UAT 결함A) */}
        <path d="M81.2 45 q3 1.6 6 0" {...sw(2)} />
        <path d="M81.2 45 l-0.6 1 M87.2 45 l0.6 1" {...sw(1.2)} />
      </g>
      <g style={d(5200, reduce)}>
        <path d="M85 36.4 q1 1.6 0.2 3.2" {...sw(1.2)} />
        <path d="M79.4 45 q-2 -2 -1 -5" {...sw(1.3, 0.55)} />
        <path d="M95.6 30 H98.4" {...sw(1.3)} />
      </g>
      <g style={d(5330, reduce)}>
        <path d="M86 29.5 L86 31.8" {...sw(1.2, 0.55)} />
        {/* 어깨~어깨 전폭 옷깃 곡선(위 가로대) 제거 — 나부끼는 겉옷 자락 접힘으로(task#303 UAT 결함A) */}
        <path d="M93 40 q2 4 1 8" {...sw(1.2)} />
        <path d="M76 53.7 l0.7 -0.7 l0.7 0.7" {...sw(1.1, 0.4)} />
      </g>
      <g style={d(5460, reduce)}>
        <path d="M80 50 q0.6 2 0 3.5" {...sw(1.2)} />
        <path d="M83 36 L86 38.5 L89 36" {...sw(1.3)} />
        <path d="M79 51.5 q1.2 -0.6 2.2 0.3 M92.8 51.8 q1.2 -0.6 2.2 0.3" {...sw(1.1)} />
      </g>
      <g style={d(5590, reduce)}>
        <path d="M96.3 54.4 q1.4 0.5 2.4 -0.3" {...sw(1.2, 0.45)} />
        <path d="M84.5 24.6 q1.5 -0.5 3 0" {...sw(1.1, 0.5)} />
        <path d="M85.2 25 q0.8 -1.4 1.6 -0.3" {...sw(1.1, 0.55)} />
      </g>
      <g style={d(5720, reduce)}>
        <path d="M83.2 27.4 q1 -0.3 1.8 0 M86.7 27.4 q1 -0.3 1.8 0" {...sw(1.05, 0.6)} />
        <path d="M95 52.5 q1.4 -0.6 2.5 0.3" {...sw(1.1, 0.5)} />
      </g>
      <g style={d(5785, reduce)}>
        <path d="M84 41 q0.6 2 0 3.5" {...sw(1.2)} />
        <path d="M88 41 q-0.6 2 0 3.5" {...sw(1.2)} />
      </g>

      {/* ── 밝은 구름 + 빛줄기(마 17:5, "너희는 그의 말을 들으라") ── */}
      <g style={d(5850, reduce)}>
        <path d="M44 16 q4 -3 9 -2 q3 -2.5 8 -1 q4 -2 8 0 q4 -2 8 1 q3 -1 4 2" {...sw(1.5, 0.6)} />
        <path d="M44 16 Q60 19 76 16" {...sw(1.4, 0.55)} />
        <path d="M50 13 q2 -2 4 0 M66 12.5 q2 -2 4 0" {...sw(1.3, 0.55)} />
      </g>
      <g style={d(5980, reduce)}>
        <path d="M57 16.5 L42 22 M63 16.5 L78 22" {...sw(1.2, 0.45)} />
        <path d="M60 15.5 L60 19.5" {...sw(1.2, 0.45)} />
        <path d="M18 17 q2 -2 4 0 q2 -2 4 0" {...sw(1.1, 0.5)} />
      </g>

      {/* ── 제자 하나 — 왼쪽, 엎드려 두려워한다(마 17:6) — 몸통을 부드러운 곡선으로 그리니
           눈사람처럼 뭉쳐 보여, 어깨~뒤꿈치·어깨~무릎~발을 곧은 선의 꺾임으로 다시 그렸다
           (task#303 UAT 결함B, 루프 2) ── */}
      <g style={d(6110, reduce)}>
        <circle cx="14" cy="34" r="3.6" {...sw(2.2)} />
        <path d="M13 37.1 L12 38.6 M15.5 37.3 L16.2 39" {...sw(2.1)} />
        <path d="M12 38.6 q2.1 0.7 4.2 0.4" {...sw(2.2)} />
      </g>
      <g style={d(6240, reduce)}>
        <path d="M12 38.6 L9.5 54" {...sw(2.4)} />
        <path d="M16.2 39 L18.5 47 L15 54" {...sw(2.4)} />
        <path d="M16.2 39 L20.5 45 L19.5 53.5" {...sw(2.2)} />
      </g>
      <g style={d(6370, reduce)}>
        <path d="M16.6 39.6 L20.7 45.6 L19.9 51.5" {...sw(1.8)} />
        <path d="M11 32.5 q3 -1.8 6 0" {...sw(1.3)} />
        <path d="M13 36.4 q0.8 0.3 1.4 0" {...sw(1.1, 0.6)} />
      </g>
      <g style={d(6500, reduce)}>
        <path d="M19.1 53.6 q1 0.4 1.7 -0.1" {...sw(1.3)} />
        <path d="M14.6 53.6 q1 0.5 1.8 0" {...sw(1.2)} />
        <path d="M9.1 53.6 q1 0.4 1.7 0" {...sw(1.2)} />
      </g>
      <g style={d(6630, reduce)}>
        <path d="M12.6 35.6 q1 -0.4 1.8 0" {...sw(1.1, 0.6)} />
        <path d="M10.5 44 q-0.3 3 0.2 5.5" {...sw(1.2)} />
        <path d="M17.5 43 q0.4 2 0 3.6" {...sw(1.2)} />
      </g>
      <g style={d(6760, reduce)}>
        <path d="M11.8 47.5 q1.4 0.7 2.6 0" {...sw(1.1, 0.5)} />
        <path d="M9.3 49 q-0.2 2.5 0.2 4.4" {...sw(1.2)} />
        <path d="M16 50 q0.3 2 -0.2 3.6" {...sw(1.2)} />
      </g>
      <g style={d(6890, reduce)}>
        <path d="M19.6 51.7 q0.8 0.4 1.4 -0.1" {...sw(1.1)} />
        <path d="M7 53.6 l0.6 -0.6 l0.6 0.6" {...sw(1.1, 0.4)} />
      </g>
      <g style={d(7020, reduce)}>
        <path d="M8.2 53.7 q1 0.5 1.8 0" {...sw(1.1, 0.45)} />
      </g>

      {/* ── 제자 둘 — 가운데, 엎드려 두려워한다(마 17:6) — 곧은 선의 꺾임으로 어깨~뒤꿈치·
           어깨~무릎~발·어깨~손을 그린다(task#303 UAT 결함B, 루프 2 — 곡선은 눈사람으로 뭉쳤다) ── */}
      <g style={d(7150, reduce)}>
        <circle cx="73" cy="44" r="3.2" {...sw(2.2)} />
        <path d="M71.9 46.6 L70.8 48.2 M74.1 46.6 L75.2 48.2" {...sw(2.1)} />
        <path d="M70.8 48.2 q2.2 -1 4.4 0" {...sw(2.2)} />
      </g>
      <g style={d(7280, reduce)}>
        <path d="M70.8 48.2 L69.5 54" {...sw(2.2)} />
        <path d="M75.2 48.2 L77.5 51.5 L75 54" {...sw(2.2)} />
        <path d="M75.2 48.2 L79 50 L78.5 53.5" {...sw(2.0)} />
      </g>
      <g style={d(7410, reduce)}>
        <path d="M78.1 53.6 q0.8 0.4 1.4 -0.1" {...sw(1.2)} />
        <path d="M74.6 53.6 q0.8 0.4 1.4 0" {...sw(1.1)} />
        <path d="M71 42.3 q2 -1.3 4 0" {...sw(1.2)} />
      </g>
      <g style={d(7540, reduce)}>
        <path d="M71.6 43.4 q1.4 0.6 2.6 0" {...sw(1.1, 0.55)} />
        <path d="M69.8 50 q-0.3 1.8 0.2 3.2" {...sw(1.1, 0.5)} />
        <path d="M76.5 50 q0.3 1.8 -0.2 3.2" {...sw(1.1, 0.5)} />
      </g>
      <g style={d(7670, reduce)}>
        <path d="M68.3 53.6 l0.5 -0.5 l0.5 0.5" {...sw(1.1, 0.4)} />
        <path d="M69.9 53.4 q0.8 0.5 1.4 0" {...sw(1.1, 0.45)} />
      </g>

      {/* ── 제자 셋 — 오른쪽, 엎드려 두려워한다(마 17:6) — 곧은 선의 꺾임으로 어깨~뒤꿈치·
           어깨~무릎~발·어깨~손을 그린다(task#303 UAT 결함B, 루프 2 — 곡선은 눈사람으로 뭉쳤다) ── */}
      <g style={d(7930, reduce)}>
        <circle cx="105" cy="44" r="3.2" {...sw(2.2)} />
        <path d="M103.9 46.6 L102.8 48.2 M106.1 46.6 L107.2 48.2" {...sw(2.1)} />
        <path d="M102.8 48.2 q2.2 -1 4.4 0" {...sw(2.2)} />
      </g>
      <g style={d(8060, reduce)}>
        <path d="M107.2 48.2 L108.5 54" {...sw(2.2)} />
        <path d="M102.8 48.2 L100.5 51.5 L103 54" {...sw(2.2)} />
        <path d="M102.8 48.2 L99 50 L99.5 53.5" {...sw(2.0)} />
      </g>
      <g style={d(8190, reduce)}>
        <path d="M99.1 53.6 q0.8 0.4 1.4 -0.1" {...sw(1.2)} />
        <path d="M102.6 53.6 q0.8 0.4 1.4 0" {...sw(1.1)} />
        <path d="M103 42.3 q2 -1.3 4 0" {...sw(1.2)} />
      </g>
      <g style={d(8320, reduce)}>
        <path d="M103.6 43.4 q1.4 0.6 2.6 0" {...sw(1.1, 0.55)} />
        <path d="M107.7 50 q0.3 1.8 -0.2 3.2" {...sw(1.1, 0.5)} />
        <path d="M101 50 q-0.3 1.8 0.2 3.2" {...sw(1.1, 0.5)} />
      </g>
      <g style={d(8450, reduce)}>
        <path d="M108 53.4 q0.8 0.5 1.4 0" {...sw(1.1, 0.45)} />
        <path d="M110 53.6 l0.5 -0.5 l0.5 0.5" {...sw(1.1, 0.4)} />
        <path d="M104 46.5 q1 0.4 1.8 0" {...sw(1.1, 0.5)} />
      </g>
      <g style={d(8580, reduce)}>
        <path d="M108.3 49 q0.6 1.5 0 2.8" {...sw(1.2)} />
      </g>

      <Label x="60" y="7" at="1.6" reduce={reduce}>예수</Label>
      <Label x="60" y="61" at="9" reduce={reduce} size="4.2">너희는 그의 말을 들으라</Label>
    </g>
  )
}

// 삭개오 (눅 19:1-10)
function ZacchaeusScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M30 54 v-20 M30 34 q-8 -1 -10 -8 q8 -3 12 3 q1 -8 9 -9 q4 4 1 10 q7 -2 9 4 q-5 6 -12 4 q-4 2 -9 -4" {...sw(1.8)} />
      </g>
      {/* 삭개오 — 나무 위 */}
      <g style={d(1300, reduce)}>
        <circle cx="30" cy="27" r="2.3" {...sw(2.3)} />
        <path d="M28 34 l1 -5 h2 l1 5 M27 31 q3 1.5 6 0" {...sw(2.3)} />
      </g>
      {/* 예수 — 올려다보며 부름 */}
      <g style={d(2100, reduce)}>
        <circle cx="60" cy="32" r="2.9" {...sw(2.6)} />
        <path d="M55.5 54 l2.2 -18.5 h4.6 l2.2 18.5 M55.5 54 h9" {...sw(2.6)} />
        <path d="M52 34 q-4 -1.5 -8 1" {...sw(2.2)} />
      </g>
      {/* 무리 — 원경 */}
      <g style={d(2700, reduce)}>
        <circle cx="80" cy="46" r="1.9" {...sw(1.6, 0.7)} />
        <path d="M80 47.9 v5.1" {...sw(1.6, 0.7)} />
        <circle cx="90" cy="46.5" r="1.8" {...sw(1.5, 0.65)} />
        <path d="M90 48.3 v4.7" {...sw(1.5, 0.65)} />
      </g>
      <Label x="30" y="19" at="1.9" reduce={reduce}>삭개오</Label>
      <Label x="60" y="61" at="3" reduce={reduce} size="4.2">잃어버린 자를 찾아 구원하려 함이니라</Label>
    </g>
  )
}

// 베드로의 부인 (마 26:69-75)
function PeterDenialScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M52 54 q10 -3 20 0" {...sw(1.8)} />
        <path d="M56 51.5 q1.5 -1.5 0 -3 M60 51 q1.5 -1.5 0 -3 M64 51.5 q1.5 -1.5 0 -3" {...sw(1.2, 0.5)} />
      </g>
      {/* 베드로 — 돌아섬 */}
      <g transform={reduce ? 'translate(-6 0)' : undefined} style={d(1300, reduce)}>
        <circle cx="40" cy="38" r="2.7" {...sw(2.4)} />
        <path d="M37 54 l1.6 -12 h3.4 l1.6 12" {...sw(2.4)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="translate" from="0 0" to="-7 0"
            begin="2.1s" dur="1.4s" fill="freeze" />
        )}
      </g>
      {/* 예수 — 돌이켜 보심, 원경 */}
      <g style={d(2200, reduce)}>
        <circle cx="94" cy="32" r="2.2" {...sw(1.8, 0.75)} />
        <path d="M92 43 l1.2 -8.5 h1.8 l1.2 8.5" {...sw(1.8, 0.75)} />
      </g>
      {/* 닭 — 울음 */}
      <g style={d(reduce ? 0 : 3000, reduce)}>
        <path d="M18 50 q-1.5 -3.5 1.5 -5 q3 0.5 2 3.5 M21.5 46 q2 -1 3.5 0.5" {...sw(1.5)} />
      </g>
      <Label x="40" y="29" at="1.9" reduce={reduce}>베드로</Label>
      <Label x="60" y="61" at="3.2" reduce={reduce} size="4.2">닭이 울매 심히 통곡하니라</Label>
    </g>
  )
}

// 베드로의 회복 (요 21:15-17)
function PeterRestorationScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M8 48 q8 -3 16 0 q8 -3 16 0 q8 -3 16 0" {...sw(1.8)} />
        <path d="M50 53 q5 -1.5 10 0" {...sw(1.6)} />
        <path d="M53 51 q1.4 -1.4 0 -2.8 M57 50.5 q1.4 -1.4 0 -2.8" {...sw(1.1, 0.5)} />
      </g>
      {/* 예수 — 물으심 */}
      <g style={d(1200, reduce)}>
        <circle cx="42" cy="32" r="2.9" {...sw(2.6)} />
        <path d="M37.5 54 l2.2 -19 h4.6 l2.2 19 M37.5 54 h9 M45.5 36 q4 -1.5 6 1" {...sw(2.6)} />
      </g>
      {/* 베드로 — 세 번의 사랑 고백 */}
      <g style={d(2000, reduce)}>
        <circle cx="68" cy="33" r="2.7" {...sw(2.4)} />
        <path d="M64.5 54 l2 -18 h3.6 l2 18 M64.5 54 h7 M62 36 q4 -1 6 1" {...sw(2.4)} />
      </g>
      {/* 어린 양 — 강조 */}
      <g style={d(reduce ? 0 : 2800, reduce)} stroke="var(--paper-accent)">
        <path d="M90 51 q0 -3 3 -3 q3 0 3 3 M90 51 h6 M91.4 48 q-1 -2 0.4 -3 M94.6 48 q1 -2 -0.4 -3" {...sw(1.6)} />
      </g>
      <Label x="68" y="24" at="2.3" reduce={reduce}>베드로</Label>
      <Label x="60" y="61" at="3.3" reduce={reduce} size="4.2">내 양을 먹이라</Label>
    </g>
  )
}

const SCENES = {
  'authored-mary-nazareth-annunciation': { Scene: AnnunciationScene, desc: '은혜를 받은 자여 — 가브리엘이 이르다', caption: '수태고지 — 누가복음 1장' },
  'authored-mary-judah-visitation': { Scene: VisitationScene, desc: '태중의 아기가 기쁨으로 뛰놀다', caption: '방문 — 누가복음 1장' },
  'authored-john-baptist-birth-naming': { Scene: JohnBirthScene, desc: '그 이름은 요한이라 — 벙어리가 풀리다', caption: '요한의 출생 — 누가복음 1장' },
  'authored-jesus-bethlehem-birth': { Scene: BethlehemBirthScene, desc: '구유에 뉘인 첫 아들', caption: '탄생 — 누가복음 2장' },
  'authored-jesus-temple-presentation': { Scene: TemplePresentationScene, desc: '시므온이 아기를 안고 찬송하다', caption: '성전 봉헌 — 누가복음 2장' },
  'authored-jesus-magi-visit': { Scene: MagiVisitScene, desc: '박사들이 엎드려 황금과 유향과 몰약을 드리다', caption: '박사들의 경배 — 마태복음 2장' },
  'authored-jesus-flight-egypt': { Scene: FlightEgyptScene, mood: 'dark', desc: '헤롯의 칼을 피해 애굽으로 내려가다', caption: '피신 — 마태복음 2장' },
  'authored-jesus-nazareth-childhood': { Scene: NazarethChildhoodScene, desc: '지혜와 키가 자라 하나님과 사람에게 사랑받다', caption: '나사렛 유년기 — 누가복음 2장' },
  'authored-jesus-boy-at-temple': { Scene: BoyAtTempleScene, desc: '선생들 가운데서 묻고 대답하다', caption: '열두 살 — 누가복음 2장' },
  'authored-john-baptist-wilderness-ministry': { Scene: JohnWildernessScene, desc: '광야에서 회개를 외치다', caption: '광야의 소리 — 마태복음 3장' },
  'authored-jesus-jordan-baptism': { Scene: JordanBaptismScene, desc: '하늘이 열리고 성령이 비둘기같이 임하다', caption: '세례 — 마태복음 3장' },
  'authored-jesus-wilderness-temptation': { Scene: WildernessTemptationScene, desc: '말씀으로 세 가지 시험을 물리치다', caption: '광야 시험 — 마태복음 4장' },
  'authored-john-first-disciple': { Scene: JohnFirstDiscipleScene, desc: '보라 하나님의 어린 양이라 — 제자들이 따르다', caption: '첫 제자들 — 요한복음 1장' },
  'authored-mary-cana-wedding': { Scene: CanaWeddingScene, desc: '물이 변하여 포도주가 되다', caption: '가나 혼인 잔치 — 요한복음 2장' },
  'authored-jesus-capernaum-base': { Scene: CapernaumBaseScene, desc: '바닷가 가버나움에 자리 잡으시다', caption: '갈릴리 — 마태복음 4장' },
  'authored-jesus-call-disciples': { Scene: CallDisciplesScene, desc: '나를 따라오라 — 그물을 버려두다', caption: '제자 부름 — 마태복음 4장' },
  'authored-jesus-capernaum-healing': { Scene: CapernaumHealingScene, desc: '더러운 귀신이 쫓겨나고 온 성이 몰려오다', caption: '가버나움 치유 — 마가복음 1장' },
  'authored-john-baptist-machaerus-prison': { Scene: JohnBaptistPrisonScene, mood: 'dark', desc: '헤롯의 죄를 책망하다 옥에 갇히다', caption: '요한의 투옥 — 마가복음 6장' },
  'authored-peter-apostle-named': { Scene: PeterNamedScene, desc: '시몬에게 반석이라는 새 이름을 주시다', caption: '베드로라 이름하다 — 누가복음 6장' },
  'authored-jesus-sermon-mount': { Scene: SermonMountScene, desc: '산에 올라 팔복을 선포하시다', caption: '산상수훈 — 마태복음 5장' },
  'authored-john-baptist-prison-question': { Scene: JohnPrisonQuestionScene, desc: '오실 그이가 당신이오니이까 — 옥중에서 묻다', caption: '옥중의 질문 — 마태복음 11장' },
  'authored-john-baptist-machaerus-death': { Scene: MachaerusDeathScene, mood: 'dark', desc: '예비하는 자의 길이 끝나다', caption: '순교 — 마가복음 6장' },
  'authored-jesus-bethsaida-feeding': { Scene: BethsaidaFeedingScene, desc: '한 아이의 도시락으로 오천 명을 먹이시다', caption: '오병이어 — 요한복음 6장' },
  'authored-peter-walks-on-water': { Scene: PeterWaterScene, desc: '바다 위로 걷다가 바람을 보고 빠져들다', caption: '물 위를 걷다 — 마태복음 14장' },
  'authored-jesus-caesarea-philippi': { Scene: CaesareaPhilippiScene, desc: '너희는 나를 누구라 하느냐', caption: '베드로의 고백 — 마태복음 16장' },
  'authored-jesus-transfiguration': { Scene: TransfigurationScene, desc: '얼굴이 해같이 빛나고 모세와 엘리야가 나타나다', caption: '변화산 — 마태복음 17장' },
  'authored-jesus-bethany-lazarus': { Scene: LazarusScene, desc: '나사로야 나오라', caption: '베다니 — 요한복음 11장' },
  'authored-jesus-jericho-zacchaeus': { Scene: ZacchaeusScene, desc: '뽕나무 위의 세리장을 이름으로 부르시다', caption: '삭개오 — 누가복음 19장' },
  'authored-jesus-triumphal-entry': { Scene: TriumphalEntryScene, desc: '호산나 — 종려가지를 흔들다', caption: '입성 — 마태복음 21장' },
  'authored-jesus-last-supper': { Scene: LastSupperScene, desc: '떡을 떼어 이것은 내 몸이라 하시다', caption: '최후의 만찬 — 누가복음 22장' },
  'authored-jesus-gethsemane-prayer': { Scene: GethsemaneScene, mood: 'dark', desc: '땀이 핏방울같이 되도록 기도하시다', caption: '겟세마네 — 마태복음 26장' },
  'authored-peter-denial': { Scene: PeterDenialScene, mood: 'dark', desc: '세 번 부인한 뒤 닭 울음에 통곡하다', caption: '베드로의 부인 — 마태복음 26장' },
  'authored-jesus-crucifixion': { Scene: CrucifixionScene, mood: 'dark', desc: '다 이루었다', caption: '십자가 — 누가복음 23장' },
  'authored-mary-jerusalem-cross': { Scene: MaryCrossScene, mood: 'dark', desc: '보라 네 어머니라 — 십자가 아래에서', caption: '어머니 — 요한복음 19장' },
  'authored-jesus-resurrection': { Scene: ResurrectionScene, desc: '돌이 굴려지고 무덤이 비다', caption: '부활 — 누가복음 24장' },
  'authored-peter-restoration': { Scene: PeterRestorationScene, desc: '세 번 물으시고 내 양을 먹이라 맡기시다', caption: '베드로의 회복 — 요한복음 21장' },
  'authored-jesus-ascension': { Scene: AscensionScene, desc: '축복하시며 하늘로 올려지시다', caption: '승천 — 사도행전 1장' },
}

export default SCENES
