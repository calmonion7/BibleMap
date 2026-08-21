// 초대교회와 바울 — 19개 정차지 장면 (task#231, #227 표준)
import { sw, d } from './lib'
import { Label } from './SceneLabel'
// 인트로 오프닝 몽타주가 쓰는 장면 — 정의는 introMontage.jsx로 옮겼다(task#287).
// 방향이 중요하다: 무거운 투어 모듈이 소형 모듈을 참조해야 인트로가 투어 청크를 끌어오지 않는다.
import { PentecostScene } from './introMontage'

// 미문의 앉은뱅이 (행 3:1-10)
function LameManScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        {/* 미문 */}
        <path d="M74 54 v-24 q12 -10 24 0 v24 M79 54 v-19 q7 -6 14 0 v19" {...sw(2.2)} />
      </g>
      {/* 베드로 — 손 내밀어 일으킴 */}
      <g style={d(1100, reduce)}>
        <circle cx="34" cy="32" r="2.9" {...sw(2.6)} />
        <path d="M34 34.9 v11.1 M31 54 l3 -8 l3 8 M36.5 37 q5 2 8.5 5" {...sw(2.6)} />
      </g>
      {/* 일어나 뛰는 자 — 상승 */}
      <g transform={reduce ? undefined : 'translate(0 7)'} style={d(2000, reduce)}>
        <circle cx="52" cy="38" r="2.6" {...sw(2.4)} />
        <path d="M52 40.6 v6.4 M49.5 53 l2.5 -6 M55.5 52 l-3 -5.5 M49.5 42 l-4.5 1.5 M54.5 41 q3 -2.5 3.5 -5.5" {...sw(2.4)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="translate" from="0 7" to="0 0"
            begin="2.3s" dur="0.8s" fill="freeze" calcMode="spline" keySplines="0.3 0 0.5 1" keyTimes="0;1" />
        )}
      </g>
      <g style={d(reduce ? 0 : 3000, reduce)} stroke="var(--paper-accent)">
        <path d="M48 26 l-2 -2.4 M54 25 v-3 M60 26 l2 -2.4" {...sw(1.4)} />
      </g>
      <Label x="34" y="22" at="1.6" reduce={reduce}>베드로</Label>
      <Label x="86" y="22" at="0.9" reduce={reduce}>성전 미문</Label>
      <Label x="52" y="61" at="2.7" reduce={reduce} size="4.2">일어나 걸으라</Label>
    </g>
  )
}

// 공회 앞 증언 (행 3:11-4:22)
function PorticoTrialScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        {/* 공회 단상 */}
        <path d="M64 54 v-8 h42 v8 M62 46 h46" {...sw(2)} />
        <circle cx="76" cy="40" r="2.3" {...sw(1.9)} />
        <path d="M73.5 46 l1.2 -3.5 h2.6 l1.2 3.5" {...sw(1.9)} />
        <circle cx="88" cy="39.5" r="2.3" {...sw(1.9)} />
        <path d="M85.5 46 l1.2 -4 h2.6 l1.2 4" {...sw(1.9)} />
        <circle cx="100" cy="40" r="2.3" {...sw(1.9)} />
        <path d="M97.5 46 l1.2 -3.5 h2.6 l1.2 3.5" {...sw(1.9)} />
      </g>
      {/* 담대한 두 사도 — 주역 */}
      <g style={d(1500, reduce)}>
        <circle cx="30" cy="32" r="3" {...sw(2.6)} />
        <path d="M30 35 v11.5 M26.5 54 l3.5 -7.5 l3.5 7.5 M32.5 38 q4.5 -1 7.5 0.5" {...sw(2.6)} />
        <circle cx="44" cy="34" r="2.7" {...sw(2.3)} />
        <path d="M44 36.7 v9.8 M41 54 l3 -7.5 l3 7.5" {...sw(2.3)} />
      </g>
      <Label x="36" y="22" at="1.9" reduce={reduce}>베드로와 요한</Label>
      <Label x="86" y="31" at="1.1" reduce={reduce}>공회</Label>
      <Label x="60" y="61" at="2.7" reduce={reduce} size="4.2">다른 이름을 주신 일이 없느니라</Label>
    </g>
  )
}

// 사마리아 안수 (행 8:14-24)
function SamariaScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M84 44 q13 -8 26 -2" {...sw(1.1, 0.4)} />
      </g>
      {/* 안수하는 사도 */}
      <g style={d(1000, reduce)}>
        <circle cx="46" cy="30" r="2.9" {...sw(2.6)} />
        <path d="M46 32.9 v12.1 M43 54 l3 -9 l3 9" {...sw(2.6)} />
        <path d="M48.5 35 q6 2 9 6.5" {...sw(2.4)} />
      </g>
      {/* 무릎 꿇은 이들 */}
      <g style={d(1900, reduce)}>
        <circle cx="62" cy="44" r="2.5" {...sw(2.2)} />
        <path d="M62 46.5 l-1.2 3.5 M56.5 53 h9.5" {...sw(2.2)} />
        <circle cx="76" cy="45" r="2.4" {...sw(2, 0.9)} />
        <path d="M76 47.4 l-1.2 3 M71 53.5 h9" {...sw(2, 0.9)} />
      </g>
      {/* 성령 — 비둘기 */}
      <g style={d(reduce ? 0 : 2800, reduce)} stroke="var(--paper-accent)">
        <path d="M62 30 q2.4 -2.4 4.8 0 q2.4 -2.4 4.8 0" {...sw(1.7)} />
      </g>
      <Label x="46" y="20" at="1.5" reduce={reduce}>안수</Label>
      <Label x="70" y="61" at="2.4" reduce={reduce} size="4.2">사마리아가 성령을 받다</Label>
    </g>
  )
}

// 다메섹 회심 (행 9:1-19)
function DamascusScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M14 52 h4 m6 0.6 h4 m6 0.6 h4 m50 -1.6 h4 m6 0.6 h4" {...sw(1.2, 0.5)} />
      </g>
      {/* 하늘 빛 — 방사선 */}
      <g style={d(1000, reduce)} stroke="var(--paper-accent)">
        <path d="M60 8 v10 M48 10 l6 9 M72 10 l-6 9 M40 16 l9 7 M80 16 l-9 7" {...sw(1.8)}>
          {!reduce && <animate attributeName="opacity" values="1;0.5;1" begin="1.8s" dur="0.8s" repeatCount="2" />}
        </path>
      </g>
      {/* 쓰러진 사울 — 주역 */}
      <g style={d(1900, reduce)}>
        <circle cx="56" cy="42" r="2.9" {...sw(2.6)} />
        <path d="M58.5 43.5 q6 -1 10 2.5 M53.5 44 l-5.5 4.5 M60 46.5 l4 6" {...sw(2.6)} />
        <path d="M52 46 q2 -1.6 4 -0.6" {...sw(1.4, 0.6)} />
      </g>
      {/* 떨어진 서슬 — 박해 문서 */}
      <g style={d(2800, reduce)}>
        <path d="M82 50 h7 q1.3 0 1.3 1.3 v1.4 q0 1.3 -1.3 1.3 h-7 z" {...sw(1.6, 0.8)} />
      </g>
      <Label x="60" y="30" at="1.5" reduce={reduce}>하늘의 빛</Label>
      <Label x="52" y="61" at="2.4" reduce={reduce} size="4.2">사울아 사울아 어찌하여 나를 박해하느냐</Label>
    </g>
  )
}

// 애니아와 도르가 (행 9:32-43)
function AeneasDorcasScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M20 50 h28 M24 54 v-4 M44 54 v-4" {...sw(1.8)} />
      </g>
      {/* 일어나는 다비다 — 침상에서 */}
      <g transform={reduce ? undefined : 'translate(0 6)'} style={d(1200, reduce)}>
        <circle cx="34" cy="40" r="2.7" {...sw(2.4)} />
        <path d="M34 42.7 q0 4 -2 6 M34 44 q2.5 2.5 2 5.5" {...sw(2.4)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="translate" from="0 6" to="0 0"
            begin="2s" dur="0.9s" fill="freeze" calcMode="spline" keySplines="0.3 0 0.5 1" keyTimes="0;1" />
        )}
      </g>
      {/* 베드로 */}
      <g style={d(2000, reduce)}>
        <circle cx="62" cy="32" r="2.9" {...sw(2.6)} />
        <path d="M62 34.9 v11.1 M59 54 l3 -8 l3 8 M59.5 37 q-5 2 -8 5" {...sw(2.6)} />
      </g>
      {/* 지은 옷들 — 도르가의 손길 */}
      <g style={d(2800, reduce)}>
        <path d="M84 48 q4 -2.5 8 0 l1 5 h-10 z M96 50 q3.5 -2 7 0 l0.8 4 h-8.5 z" {...sw(1.6, 0.8)} />
      </g>
      <Label x="62" y="22" at="2.4" reduce={reduce}>베드로</Label>
      <Label x="34" y="30" at="1.6" reduce={reduce}>다비다야 일어나라</Label>
      <Label x="94" y="42" at="3.2" reduce={reduce} size="4.2">도르가의 옷들</Label>
    </g>
  )
}

// 고넬료 (행 10)
function CorneliusScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
      </g>
      {/* 네 귀 보자기 — 핵심: 내려옴 */}
      <g transform={reduce ? undefined : 'translate(0 -12)'} style={d(1000, reduce)}>
        <path d="M42 20 L78 20 L72 38 L48 38 z" {...sw(2.4)} />
        <path d="M42 20 l-4 -6 M78 20 l4 -6 M48 38 l-3 5 M72 38 l3 5" {...sw(1.5)} />
        <circle cx="55" cy="28" r="1.7" {...sw(1.5)} />
        <path d="M62 30 q2 -2 4 0 M58 33 q1.8 -1.6 3.6 0" {...sw(1.4)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="translate" from="0 -12" to="0 0"
            begin="2s" dur="1s" fill="freeze" calcMode="spline" keySplines="0.3 0 0.5 1" keyTimes="0;1" />
        )}
      </g>
      {/* 베드로와 고넬료 */}
      <g style={d(2200, reduce)}>
        <circle cx="24" cy="42" r="2.7" {...sw(2.4)} />
        <path d="M24 44.7 v4.3 M21.5 54 l2.5 -5 l2.5 5 M26.5 45.5 q3 -1 5 0" {...sw(2.4)} />
        <circle cx="94" cy="42.5" r="2.6" {...sw(2.2)} />
        <path d="M94 45.1 v4 M91.5 54 l2.5 -5 l2.5 5 M91.5 46 q-3 -1 -5 0" {...sw(2.2)} />
      </g>
      <Label x="60" y="12" at="1.5" reduce={reduce}>네 귀 보자기</Label>
      <Label x="24" y="33" at="2.7" reduce={reduce}>베드로</Label>
      <Label x="96" y="33" at="2.7" reduce={reduce}>고넬료</Label>
    </g>
  )
}

// 이방 구원 변호 (행 11:1-18)
function DefendsGentilesScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
      </g>
      {/* 베드로 — 손 벌려 변론 */}
      <g style={d(1000, reduce)}>
        <circle cx="60" cy="29" r="3" {...sw(2.6)} />
        <path d="M60 32 v13 M56.5 54 l3.5 -9 l3.5 9" {...sw(2.6)} />
        <path d="M60 35 q-6 0 -9.5 -3 M60 35 q6 0 9.5 -3" {...sw(2.4)} />
      </g>
      {/* 둘러앉은 이들 — 듣다가 수긍 */}
      <g style={d(2000, reduce)}>
        <circle cx="26" cy="44" r="2.4" {...sw(2)} />
        <path d="M23.5 54 l1.2 -7 h2.6 l1.2 7" {...sw(2)} />
        <circle cx="38" cy="46" r="2.3" {...sw(1.9, 0.9)} />
        <path d="M35.8 54 l1.1 -5 h2.2 l1.1 5" {...sw(1.9, 0.9)} />
        <circle cx="82" cy="46" r="2.3" {...sw(1.9, 0.9)} />
        <path d="M79.8 54 l1.1 -5 h2.2 l1.1 5" {...sw(1.9, 0.9)} />
        <circle cx="94" cy="44" r="2.4" {...sw(2)} />
        <path d="M91.5 54 l1.2 -7 h2.6 l1.2 7" {...sw(2)} />
      </g>
      <g style={d(reduce ? 0 : 2900, reduce)} stroke="var(--paper-accent)">
        <path d="M60 16 v-4 M52 18 l-2.6 -2.6 M68 18 l2.6 -2.6" {...sw(1.4)} />
      </g>
      <Label x="60" y="61" at="1.6" reduce={reduce}>베드로의 변론</Label>
      <Label x="60" y="8" at="3.1" reduce={reduce} size="4.2">이방인에게도 생명 얻는 회개를 주셨다</Label>
    </g>
  )
}

// 안디옥 (행 11:25-26)
function AntiochScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M14 54 v-20 M26 54 v-20 M11 34 h18" {...sw(1.4, 0.55)} />
      </g>
      {/* 바나바와 사울 — 가르침 */}
      <g style={d(1000, reduce)}>
        <circle cx="46" cy="31" r="2.9" {...sw(2.5)} />
        <path d="M46 33.9 v11.1 M43 54 l3 -9 l3 9 M48.5 36 q4 1 6.5 3.5" {...sw(2.5)} />
        <circle cx="60" cy="32" r="2.8" {...sw(2.4)} />
        <path d="M60 34.8 v10.2 M57 54 l3 -9 l3 9 M62.5 37 q4 1 6.5 3.5" {...sw(2.4)} />
      </g>
      {/* 듣는 제자들 */}
      <g style={d(2000, reduce)}>
        <circle cx="82" cy="44" r="2.4" {...sw(2)} />
        <path d="M79.5 54 l1.2 -7 h2.6 l1.2 7" {...sw(2)} />
        <circle cx="94" cy="45" r="2.3" {...sw(1.9, 0.9)} />
        <path d="M91.8 54 l1.1 -6 h2.2 l1.1 6" {...sw(1.9, 0.9)} />
      </g>
      <g style={d(reduce ? 0 : 2900, reduce)} stroke="var(--paper-accent)">
        <path d="M84 32 h16 M86 28.5 h12" {...sw(1.5)} />
      </g>
      <Label x="53" y="21" at="1.5" reduce={reduce}>바나바와 사울</Label>
      <Label x="92" y="22" at="3.1" reduce={reduce} size="4.2">그리스도인이라 불리다</Label>
    </g>
  )
}

// 옥문이 열리다 (행 12:1-17)
function HerodPrisonScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        {/* 옥 창살 */}
        <path d="M22 54 V22 h32 M26 54 V26 M34 54 V26 M42 54 V26 M50 54 V26" {...sw(2)} />
      </g>
      {/* 열린 문 — 벌어짐 */}
      <g transform={reduce ? 'rotate(-24 54 54)' : undefined} style={d(1400, reduce)}>
        <path d="M54 54 V26 h10 M58 54 V28" {...sw(2.2)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="rotate" from="0 54 54" to="-24 54 54"
            begin="2.6s" dur="0.8s" fill="freeze" />
        )}
      </g>
      {/* 끊어진 쇠사슬 */}
      <g style={d(2200, reduce)}>
        <path d="M30 46 q1.6 -1.6 3.2 0 q1.6 1.6 3.2 0 M40 47.5 q1.6 -1.6 3.2 0" {...sw(1.6, 0.85)} />
      </g>
      {/* 천사와 베드로 — 나옴 */}
      <g style={d(2000, reduce)}>
        <circle cx="78" cy="35" r="2.7" {...sw(2.4)} />
        <path d="M78 37.7 v9.3 M75 54 l3 -7 l3 7" {...sw(2.4)} />
        <circle cx="92" cy="33" r="2.6" {...sw(2, 0.85)} />
        <path d="M88.5 45 l1.7 -9.5 h3.6 l1.7 9.5 M87 35 q-3.5 -1.5 -4.5 -4.5 M97 35 q3.5 -1.5 4.5 -4.5" {...sw(2, 0.85)} />
      </g>
      <Label x="38" y="16" at="1.2" reduce={reduce}>헤롯의 옥</Label>
      <Label x="80" y="25" at="2.6" reduce={reduce}>이끌려 나온 베드로</Label>
    </g>
  )
}

// 예루살렘 공의회 (행 15)
function JerusalemCouncilScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M26 46 h68" {...sw(2)} />
      </g>
      {/* 둘러앉은 사도·장로들 */}
      <g style={d(1000, reduce)}>
        <circle cx="34" cy="38" r="2.5" {...sw(2.1)} />
        <path d="M31.5 46 l1.2 -5.5 h2.6 l1.2 5.5" {...sw(2.1)} />
        <circle cx="48" cy="36.5" r="2.6" {...sw(2.3)} />
        <path d="M45.5 46 l1.2 -6.5 h2.6 l1.2 6.5" {...sw(2.3)} />
        <circle cx="62" cy="36" r="2.6" {...sw(2.3)} />
        <path d="M59.5 46 l1.2 -7 h2.6 l1.2 7" {...sw(2.3)} />
        <circle cx="76" cy="36.5" r="2.6" {...sw(2.3)} />
        <path d="M73.5 46 l1.2 -6.5 h2.6 l1.2 6.5" {...sw(2.3)} />
        <circle cx="88" cy="38" r="2.5" {...sw(2.1)} />
        <path d="M85.5 46 l1.2 -5.5 h2.6 l1.2 5.5" {...sw(2.1)} />
      </g>
      {/* 결의의 편지 — 핵심 */}
      <g style={d(2200, reduce)} stroke="var(--paper-accent)">
        <path d="M54 50 h12 q1.6 0 1.6 1.6 v0 q0 1.6 -1.6 1.6 h-12 q-1.6 0 -1.6 -1.6 v0 q0 -1.6 1.6 -1.6" {...sw(2)} />
        <path d="M56.5 51.6 h7" {...sw(1.3)} />
      </g>
      <Label x="60" y="24" at="1.5" reduce={reduce}>예루살렘 공의회</Label>
      <Label x="60" y="61" at="2.6" reduce={reduce} size="4.2">율법의 멍에를 지우지 말라</Label>
    </g>
  )
}

// 빌립보 감옥 (행 16:11-40)
function PhilippiScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        {/* 감옥 기둥 — 흔들림 */}
        <path d="M34 54 V22 M86 54 V22 M30 22 h60" {...sw(2.2)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="translate"
            values="0 0; 1.4 0; -1.4 0; 0.7 0; 0 0" keyTimes="0;0.25;0.5;0.75;1"
            begin="2.8s" dur="0.5s" />
        )}
      </g>
      {/* 바울과 실라 — 찬송 */}
      <g style={d(1200, reduce)}>
        <circle cx="52" cy="38" r="2.7" {...sw(2.4)} />
        <path d="M52 40.7 v7.3 M49.5 54 l2.5 -6 l2.5 6 M52 43 q-3 -2 -3.5 -5" {...sw(2.4)} />
        <circle cx="66" cy="38.5" r="2.6" {...sw(2.3)} />
        <path d="M66 41.1 v6.9 M63.5 54 l2.5 -6 l2.5 6 M66 43.5 q3 -2 3.5 -5" {...sw(2.3)} />
      </g>
      {/* 찬송 음표 + 열린 문 틈 */}
      <g style={d(2100, reduce)} stroke="var(--paper-accent)">
        <path d="M56 26 v-4 M59.5 24 v-4" {...sw(1.5)} />
        <circle cx="55" cy="26.6" r="1" {...sw(1.5)} />
        <circle cx="58.5" cy="24.6" r="1" {...sw(1.5)} />
      </g>
      <g style={d(reduce ? 0 : 3300, reduce)}>
        <path d="M40 50 l-3 -3 M80 50 l3 -3" {...sw(1.4, 0.7)} />
      </g>
      <Label x="59" y="61" at="1.7" reduce={reduce}>한밤의 찬송</Label>
      <Label x="60" y="12" at="3.2" reduce={reduce} size="4.2">옥터가 흔들리고 문이 열리다</Label>
    </g>
  )
}

// 아레오바고 (행 17:16-34)
function AthensScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        {/* 파르테논 원경 */}
        <path d="M74 54 v-4 h34 v4 M78 50 v-10 M86 50 v-10 M94 50 v-10 M102 50 v-10 M74 40 h36 l-4 -5 h-28 z" {...sw(1.4, 0.55)} />
      </g>
      {/* 알지 못하는 신 제단 */}
      <g style={d(1100, reduce)}>
        <path d="M20 54 v-8 h16 v8 M18 46 h20" {...sw(2.2)} />
        <path d="M23 50.5 h10 M25 48.5 h6" {...sw(1.3)} stroke="var(--paper-accent)" />
      </g>
      {/* 바울 — 변증 */}
      <g style={d(1900, reduce)}>
        <circle cx="54" cy="30" r="3" {...sw(2.6)} />
        <path d="M54 33 v13 M50.5 54 l3.5 -8 l3.5 8" {...sw(2.6)} />
        <path d="M54 36 q-5 0.5 -8 -1.5 M54 36 q5 0.5 8 -1.5" {...sw(2.4)} />
      </g>
      <Label x="28" y="37" at="1.7" reduce={reduce}>알지 못하는 신에게</Label>
      <Label x="54" y="20" at="2.4" reduce={reduce}>바울</Label>
      <Label x="91" y="30" at="1" reduce={reduce}>아덴</Label>
    </g>
  )
}

// 고린도 (행 18:1-17)
function CorinthScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
      </g>
      {/* 장막 짓기 — 천과 바느질 */}
      <g style={d(1000, reduce)}>
        <path d="M30 44 q10 -4 20 0 l3 8 q-13 4 -26 0 z" {...sw(2.2)} />
        <path d="M36 46 l3 3 m2 -4 l3 3 m2 -4 l3 3" {...sw(1.3, 0.6)} />
        <path d="M56 40 l4 -5 M60 35 l2.5 0.5" {...sw(1.6)} />
      </g>
      {/* 세 동역자 — 바울·브리스길라·아굴라 */}
      <g style={d(1900, reduce)}>
        <circle cx="70" cy="36" r="2.8" {...sw(2.5)} />
        <path d="M70 38.8 v8.2 M67 54 l3 -7 l3 7 M67.5 41 q-4 1 -6.5 3" {...sw(2.5)} />
        <circle cx="84" cy="38" r="2.5" {...sw(2.1)} />
        <path d="M81 54 l1.5 -11.5 h3 l1.5 11.5" {...sw(2.1)} />
        <circle cx="95" cy="37.5" r="2.5" {...sw(2, 0.9)} />
        <path d="M95 40 v7 M92.5 54 l2.5 -5 l2.5 5" {...sw(2, 0.9)} />
      </g>
      <g style={d(reduce ? 0 : 2900, reduce)} stroke="var(--paper-accent)">
        <path d="M70 24 v-3 m-1.5 1.5 h3" {...sw(1.4)} />
      </g>
      <Label x="42" y="34" at="1.5" reduce={reduce}>장막 만들기</Label>
      <Label x="84" y="27" at="2.5" reduce={reduce}>바울과 동역자들</Label>
      <Label x="60" y="61" at="3.1" reduce={reduce} size="4.2">두려워하지 말라 내가 너와 함께 있다</Label>
    </g>
  )
}

// 에베소 (행 19)
function EphesusScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        {/* 두란노 서원 강단 */}
        <path d="M22 54 v-6 h24 v6 M20 48 h28" {...sw(2.2)} />
      </g>
      {/* 강론하는 바울 */}
      <g style={d(1000, reduce)}>
        <circle cx="34" cy="32" r="2.9" {...sw(2.6)} />
        <path d="M34 34.9 v8.1 M31 48 l3 -5 l3 5 M36.5 37 q4 -1 7 0.5" {...sw(2.6)} />
      </g>
      {/* 두루마리들 + 불태워지는 마술책 */}
      <g style={d(1900, reduce)}>
        <path d="M58 50 h8 q1.4 0 1.4 1.4 v0 q0 1.4 -1.4 1.4 h-8 q-1.4 0 -1.4 -1.4 v0 q0 -1.4 1.4 -1.4 M60 46.5 h8 q1.4 0 1.4 1.4 v0 q0 1.4 -1.4 1.4" {...sw(1.7)} />
        <path d="M88 52 l3 -2 m-3 0 l3 2 M87 52.5 h5" {...sw(1.4)} />
        <path d="M89.5 48 q-1.8 -3.2 0 -5.8 q1.8 2.6 0 5.8 M92.5 48 q-1.4 -3.4 0.6 -5.6" {...sw(2.2)} stroke="var(--paper-accent)" />
      </g>
      <g style={d(reduce ? 0 : 2900, reduce)}>
        <path d="M96 40 q3 -1.5 6 0 M98 36 q2.6 -1.3 5.2 0" {...sw(1.2, 0.5)} />
      </g>
      <Label x="34" y="22" at="1.5" reduce={reduce}>두란노 강론</Label>
      <Label x="92" y="34" at="2.6" reduce={reduce}>불태운 마술책</Label>
    </g>
  )
}

// 밀레도 고별 (행 20:17-38)
function MiletusScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M70 50 q10 -3 20 0 q9 -2.5 18 0 M76 53 q9 -2.5 18 0" {...sw(1.6)} />
        {/* 배 */}
        <path d="M88 44 q1.5 3.5 6 3.5 h9 q4.5 0 6 -3.5 l-2 -3 h-17 z M97 41 v-8 M97 33 q-5 1.5 -6.5 7" {...sw(1.7, 0.8)} />
      </g>
      {/* 포옹 작별 — 핵심 */}
      <g style={d(1200, reduce)}>
        <circle cx="34" cy="32" r="2.9" {...sw(2.6)} />
        <path d="M34 34.9 q1 6 1.5 11 M35 46 l-2 8 M36.5 46 l2.5 8 M36.5 36 q4.5 1.5 7.5 4.5" {...sw(2.6)} />
        <circle cx="47" cy="33.5" r="2.7" {...sw(2.4)} />
        <path d="M46 36.2 q-1 5.5 -1.5 10 M44 46.5 l-2 7.5 M46.5 46.5 l2.5 7.5 M45 37.5 q-4 1 -7 3.5" {...sw(2.4)} />
      </g>
      {/* 눈물 */}
      <g style={d(reduce ? 0 : 2400, reduce)} stroke="var(--paper-accent)">
        <path d="M32 38.5 q-0.5 1.6 0 3 M49 40 q0.5 1.6 0 3" {...sw(1.4)} />
      </g>
      <Label x="40" y="22" at="1.7" reduce={reduce}>눈물의 고별</Label>
      <Label x="99" y="26" at="1" reduce={reduce}>예루살렘행 배</Label>
      <Label x="60" y="61" at="2.7" reduce={reduce} size="4.2">다시 내 얼굴을 보지 못하리라</Label>
    </g>
  )
}

// 로마 가택연금 (행 28:16-31)
function RomeScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        {/* 셋집 */}
        <path d="M18 54 v-16 h32 v16 M16 38 l18 -10 l18 10 M28 54 v-8 h10 v8" {...sw(2)} />
      </g>
      {/* 사슬 찬 바울 — 그러나 담대히 */}
      <g style={d(1200, reduce)}>
        <circle cx="66" cy="33" r="3" {...sw(2.6)} />
        <path d="M66 36 v11 M62.5 54 l3.5 -7 l3.5 7 M68.5 38 q4.5 -1 7.5 0.5" {...sw(2.6)} />
        <path d="M63 42 q-1.6 1.6 -3.2 0 q-1.6 -1.6 -3.2 0" {...sw(1.5, 0.8)} />
      </g>
      {/* 찾아온 이들 */}
      <g style={d(2100, reduce)}>
        <circle cx="88" cy="42" r="2.4" {...sw(2.1)} />
        <path d="M88 44.4 v4.1 M85.8 54 l2.2 -4.5 l2.2 4.5" {...sw(2.1)} />
        <circle cx="100" cy="43" r="2.3" {...sw(1.9, 0.9)} />
        <path d="M100 45.3 v3.5 M98 54 l2 -4 l2 4" {...sw(1.9, 0.9)} />
      </g>
      <g style={d(reduce ? 0 : 3000, reduce)} stroke="var(--paper-accent)">
        <path d="M66 22 v-3.5 m-1.75 1.75 h3.5" {...sw(1.4)} />
      </g>
      <Label x="34" y="30" at="1.2" reduce={reduce}>로마의 셋집</Label>
      <Label x="70" y="23" at="2" reduce={reduce}>바울</Label>
      <Label x="60" y="61" at="3.1" reduce={reduce} size="4.2">담대히 하나님 나라를 전하다</Label>
    </g>
  )
}

// 에베소의 요한 (요일 1:1-4)
function JohnEphesusScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M30 48 h42 M34 54 v-6 M68 54 v-6" {...sw(2)} />
      </g>
      {/* 책상의 노사도 — 펜과 두루마리 */}
      <g style={d(1100, reduce)}>
        <circle cx="44" cy="34" r="2.9" {...sw(2.6)} />
        <path d="M41 48 l1.5 -11 h3 l1.5 11 M46.5 38 q4 1.5 6.5 4.5" {...sw(2.6)} />
        <path d="M52 43 l3.5 3.5 M55.5 46.5 l1.8 -0.4" {...sw(1.8)} />
        <path d="M56 48 h10 q1.5 0 1.5 -1.5 M58 45.5 h7" {...sw(1.8)} stroke="var(--paper-accent)" />
      </g>
      {/* 등불 — 말년의 증언 */}
      <g style={d(2200, reduce)}>
        <path d="M84 48 h8 M86 48 q0 -2.6 2 -2.6 q2 0 2 2.6 M88 43 q-1.2 -2.2 0 -4 q1.2 1.8 0 4" {...sw(1.8)} />
      </g>
      <Label x="44" y="24" at="1.6" reduce={reduce}>노사도 요한</Label>
      <Label x="60" y="61" at="2.8" reduce={reduce} size="4.2">보고 만진 생명의 말씀을 쓰다</Label>
    </g>
  )
}

// 밧모 섬 (계 1:9-11)
function PatmosScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M8 50 q8 -3 16 0 q8 -3 16 0 M80 50 q8 -3 16 0 q8 -3 16 0" {...sw(1.8)} />
        <path d="M40 54 q10 -8 20 -8 q10 0 20 8" {...sw(2)} />
      </g>
      {/* 일곱 촛대 — 순차 draw */}
      <g style={d(1200, reduce)} stroke="var(--paper-accent)">
        <path d="M34 26 v6 M31.5 32.5 h5 M34 24 q-1 -1.8 0 -3.4 q1 1.6 0 3.4" {...sw(1.7)} />
        <path d="M46 24 v6 M43.5 30.5 h5 M46 22 q-1 -1.8 0 -3.4 q1 1.6 0 3.4" {...sw(1.7)} />
        <path d="M58 23 v6 M55.5 29.5 h5 M58 21 q-1 -1.8 0 -3.4 q1 1.6 0 3.4" {...sw(1.8)} />
        <path d="M70 24 v6 M67.5 30.5 h5 M70 22 q-1 -1.8 0 -3.4 q1 1.6 0 3.4" {...sw(1.7)} />
        <path d="M82 26 v6 M79.5 32.5 h5 M82 24 q-1 -1.8 0 -3.4 q1 1.6 0 3.4" {...sw(1.7)} />
        <path d="M40 25 v4 M52 23.5 v4 M64 23.5 v4 M76 25 v4" {...sw(1.2, 0.6)} />
      </g>
      {/* 엎드린 요한 */}
      <g style={d(2400, reduce)}>
        <circle cx="56" cy="48" r="2.5" {...sw(2.3)} />
        <path d="M58 49 q4.5 -1.6 7.5 1 M54 49.5 l-4 3.5" {...sw(2.3)} />
      </g>
      <Label x="58" y="10" at="2" reduce={reduce}>일곱 금 촛대</Label>
      <Label x="58" y="61" at="2.9" reduce={reduce} size="4.2">밧모 섬 — 주의 날에 받은 계시</Label>
    </g>
  )
}

// 구브로 선교 (행 13:1-12)
function CyprusMissionScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M60 50 q6 -2.5 12 0 q6 -2.5 12 0 M56 46 q5 -2 10 0" {...sw(1.1, 0.5)} />
      </g>
      {/* 안디옥의 파송 — 안수 */}
      <g style={d(900, reduce)}>
        <circle cx="20" cy="30" r="2.7" {...sw(2.4)} />
        <path d="M20 32.7 v10.3 M17.5 54 l2.5 -11 l2.5 11 M22 36 q4 1 6 4" {...sw(2.4)} />
        <circle cx="34" cy="42" r="2.2" {...sw(1.9, 0.85)} />
        <path d="M34 44.2 l-1.1 3.5 M31 53.5 h6" {...sw(1.9, 0.85)} />
        <circle cx="42" cy="43" r="2.1" {...sw(1.8, 0.8)} />
        <path d="M42 45.1 l-1 3.4 M39.3 53.6 h5.5" {...sw(1.8, 0.8)} />
      </g>
      {/* 구브로로 가는 배 */}
      <g style={d(1700, reduce)}>
        <path d="M64 46 q1.5 3.5 6 3.5 h9 q4.5 0 6 -3.5 l-2 -3 h-17 z M73 43 v-8 M73 35 q-5 1.5 -6.5 7" {...sw(1.7, 0.8)} />
      </g>
      {/* 서기오 바울과 눈이 어두워진 엘루마 */}
      <g style={d(2500, reduce)}>
        <circle cx="100" cy="34" r="2.6" {...sw(2.3)} />
        <path d="M100 36.6 v9.4 M97 54 l3 -8 l3 8 M102.5 38 q3 -1.5 5 -4" {...sw(2.3)} />
        <circle cx="88" cy="38" r="2.3" {...sw(2, 0.8)} />
        <path d="M88 40.3 v8.7 M85.5 54 l2.5 -5 l2.5 5 M85.5 41 q-3 1 -4.5 3.5" {...sw(2, 0.8)} />
        <path d="M86 33.5 q1 -1.6 2 0 q1 -1.6 2 0" {...sw(1.3, 0.7)} />
      </g>
      <g style={d(reduce ? 0 : 3200, reduce)} stroke="var(--paper-accent)">
        <path d="M100 24 v-4 M94 26 l-3 -3 M106 26 l3 -3" {...sw(1.4)}>
          {!reduce && <animate attributeName="opacity" values="1;0.5;1" begin="3.2s" dur="1s" repeatCount="2" />}
        </path>
      </g>
      <Label x="27" y="21" at="1.3" reduce={reduce}>바나바와 사울을 보내다</Label>
      <Label x="86" y="47" at="2.9" reduce={reduce}>눈이 어두워진 엘루마</Label>
      <Label x="60" y="61" at="3.4" reduce={reduce} size="4.2">총독이 믿고, 사울이 바울이라 불리다</Label>
    </g>
  )
}

// 비시디아 안디옥 (행 13:13-52)
function PisidianAntiochScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M20 54 v-4 h30 v4" {...sw(1.4, 0.55)} />
      </g>
      {/* 바울의 회당 설교 */}
      <g style={d(900, reduce)}>
        <circle cx="54" cy="30" r="3" {...sw(2.6)} />
        <path d="M54 33 v12 M50.5 54 l3.5 -9 l3.5 9 M54 36 q-5 0 -8 -2 M54 36 q5 1 8 3" {...sw(2.6)} />
      </g>
      {/* 시기하는 유대인들 */}
      <g style={d(1800, reduce)}>
        <circle cx="22" cy="42" r="2.4" {...sw(2, 0.9)} />
        <path d="M22 44.4 v6.6 M19.5 54 l2.5 -3 l2.5 3 M19.5 47 q2.5 -2 5 0" {...sw(2, 0.9)} />
        <circle cx="33" cy="43" r="2.3" {...sw(1.9, 0.85)} />
        <path d="M33 45.3 v6 M30.7 54 l2.3 -2.7 l2.3 2.7 M30.7 47.5 q2.3 -1.8 4.6 0" {...sw(1.9, 0.85)} />
      </g>
      {/* 이방인에게로 — 열린 무리 */}
      <g style={d(2600, reduce)}>
        <circle cx="90" cy="42" r="2.4" {...sw(2)} />
        <path d="M90 44.4 v6.6 M87.5 54 l2.5 -3 l2.5 3 M87.5 46.5 q-3 -1 -5 1 M92.5 46.5 q3 -1 5 1" {...sw(2)} />
      </g>
      <g style={d(reduce ? 0 : 2600, reduce)} stroke="var(--paper-accent)">
        <path d="M62 30 q10 2 20 8" {...sw(1.5)}>
          {!reduce && <animate attributeName="opacity" values="1;0.45;1" begin="2.7s" dur="0.9s" repeatCount="2" />}
        </path>
      </g>
      <Label x="54" y="20" at="1.6" reduce={reduce}>바울의 회당 설교</Label>
      <Label x="27" y="33" at="2.3" reduce={reduce}>시기하는 무리</Label>
      <Label x="60" y="61" at="3" reduce={reduce} size="4.2">우리가 이방인에게로 향하노라</Label>
    </g>
  )
}

// 루스드라 (행 14)
function LystraScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M96 54 v-14 q6 -6 12 0 v14" {...sw(1.3, 0.5)} />
      </g>
      {/* 치유된 이 — 신격화되는 무리 */}
      <g style={d(1000, reduce)}>
        <g transform={reduce ? undefined : 'translate(0 7)'}>
          <circle cx="30" cy="34" r="2.6" {...sw(2.3)} />
          <path d="M30 36.6 v9.4 M27 54 l3 -8 l3 8 M32.5 38 q3 -1 5 -3" {...sw(2.3)} />
          {!reduce && (
            <animateTransform attributeName="transform" type="translate" from="0 7" to="0 0"
              begin="1s" dur="0.8s" fill="freeze" calcMode="spline" keySplines="0.3 0 0.5 1" keyTimes="0;1" />
          )}
        </g>
        <circle cx="48" cy="42" r="2.2" {...sw(1.9, 0.85)} />
        <path d="M48 44.2 v6.5 M45.8 54 l2.2 -3.3 l2.2 3.3 M45.8 45 q2.2 -3 4.4 -1" {...sw(1.9, 0.85)} />
        <path d="M22 30 q8 -5 16 0" {...sw(1.6)} />
      </g>
      {/* 돌팔매에 쓰러지다 */}
      <g style={d(2000, reduce)}>
        <circle cx="66" cy="30" r="0.9" {...sw(1.4)} />
        <circle cx="72" cy="27" r="0.9" {...sw(1.4)} />
        <circle cx="78" cy="31" r="0.9" {...sw(1.4)} />
        <circle cx="60" cy="48" r="2.6" {...sw(2.4)} />
        <path d="M62.6 49 q5 -1 8 1.5 M57.5 49.5 l-5 2.5" {...sw(2.4)} />
      </g>
      {/* 다시 일어나 더베로 */}
      <g style={d(2900, reduce)}>
        <circle cx="94" cy="36" r="2.5" {...sw(2.2)} />
        <path d="M94 38.5 v9.5 M91 54 l3 -6 l4 6 M96.5 40 q3 1 5 3" {...sw(2.2)} />
      </g>
      <Label x="30" y="24" at="1.6" reduce={reduce}>루스드라의 치유</Label>
      <Label x="48" y="33" at="1.9" reduce={reduce}>신이라 외치는 무리</Label>
      <Label x="60" y="61" at="3.1" reduce={reduce} size="4.2">하나님 나라에 들어가려면 많은 환난을 겪어야 하리라</Label>
    </g>
  )
}

// 데살로니가와 베뢰아 (행 17:1-15)
function ThessalonicaBereaScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M10 54 v-10 h14 v10" {...sw(1.3, 0.5)} />
        <path d="M96 54 v-10 h14 v10" {...sw(1.3, 0.5)} />
      </g>
      {/* 데살로니가의 소동 */}
      <g style={d(900, reduce)}>
        <circle cx="26" cy="40" r="2.3" {...sw(2, 0.9)} />
        <path d="M23.7 54 l1.4 -8 h2.6 l1.4 8 M23.7 46 l-3 -3 M28.3 46 l3 -3" {...sw(2, 0.9)} />
        <circle cx="36" cy="41.5" r="2.2" {...sw(1.9, 0.85)} />
        <path d="M33.9 54 l1.3 -7.5 h2.4 l1.3 7.5 M33.9 47.5 l-2.7 -2.5 M38.1 47.5 l2.7 -2.5" {...sw(1.9, 0.85)} />
      </g>
      {/* 베뢰아 — 성경을 상고하다 */}
      <g style={d(1900, reduce)}>
        <circle cx="88" cy="42" r="2.3" {...sw(2)} />
        <path d="M85.7 54 l1.4 -7.5 h2.6 l1.4 7.5 M83 50 h5.5" {...sw(2)} />
        <path d="M80 50 h9 q1.3 0 1.3 1.3 v0 q0 1.3 -1.3 1.3 h-9" {...sw(1.6)} />
        <circle cx="98" cy="42.5" r="2.2" {...sw(1.9, 0.9)} />
        <path d="M95.9 54 l1.2 -7 h2.3 l1.2 7 M99 50 h4" {...sw(1.9, 0.9)} />
      </g>
      <g style={d(reduce ? 0 : 2700, reduce)} stroke="var(--paper-accent)">
        <path d="M82 51.6 h6" {...sw(1.3)}>
          {!reduce && <animate attributeName="opacity" values="1;0.4;1" begin="2.7s" dur="1s" repeatCount="2" />}
        </path>
      </g>
      <Label x="31" y="32" at="1.5" reduce={reduce}>데살로니가의 소동</Label>
      <Label x="90" y="33" at="2.3" reduce={reduce}>날마다 말씀을 상고하다</Label>
      <Label x="60" y="61" at="3" reduce={reduce} size="4.2">이것이 그러한가 성경을 상고하다</Label>
    </g>
  )
}

// 예루살렘 체포 (행 21:27-36)
function JerusalemArrestScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M18 54 V24 M30 54 V24 M14 24 h20" {...sw(1.4, 0.5)} />
      </g>
      {/* 성전 앞 격앙된 무리 */}
      <g style={d(900, reduce)}>
        <circle cx="70" cy="40" r="2.3" {...sw(2, 0.9)} />
        <path d="M67.7 54 l1.4 -8 h2.6 l1.4 8 M70 46 l3 -4 M67.7 46 l-2 -3" {...sw(2, 0.9)} />
        <circle cx="80" cy="41" r="2.2" {...sw(1.9, 0.85)} />
        <path d="M77.9 54 l1.2 -7.5 h2.4 l1.2 7.5 M80 47 l3 -3.5" {...sw(1.9, 0.85)} />
        <circle cx="90" cy="40.5" r="2.2" {...sw(1.9, 0.8)} />
        <path d="M87.9 54 l1.2 -8 h2.4 l1.2 8 M90 46.5 l-3 -4" {...sw(1.9, 0.8)} />
      </g>
      {/* 붙잡힌 바울 */}
      <g style={d(1900, reduce)}>
        <circle cx="52" cy="32" r="2.9" {...sw(2.6)} />
        <path d="M52 34.9 v11.1 M49 54 l3 -8 l3 8 M49.5 37 q-3.5 0 -5.5 2 M54.5 37 q3.5 0 5.5 2" {...sw(2.6)} />
      </g>
      {/* 결박하는 쇠사슬 */}
      <g style={d(2700, reduce)}>
        <path d="M40 50 v-16 M38 36 l4 -2" {...sw(1.6, 0.85)} />
        <path d="M46 46 q1.6 -1.6 3.2 0 q1.6 1.6 3.2 0" {...sw(1.7)}>
          {!reduce && <animate attributeName="opacity" values="0.5;1" begin="2.7s" dur="0.6s" fill="freeze" />}
        </path>
      </g>
      <Label x="80" y="32" at="1.6" reduce={reduce}>성전의 무리</Label>
      <Label x="52" y="22" at="2.4" reduce={reduce}>결박된 바울</Label>
      <Label x="60" y="61" at="3" reduce={reduce} size="4.2">결박과 환난이 나를 기다리는 줄 알았노라</Label>
    </g>
  )
}

// 가이사랴 감금 (행 24-26)
function CaesareaScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M74 54 v-10 h34 v10 M78 44 h26" {...sw(2)} />
      </g>
      {/* 벨릭스와 아그립바 */}
      <g style={d(900, reduce)}>
        <circle cx="86" cy="36" r="2.3" {...sw(1.9)} />
        <path d="M83.7 44 l1.2 -4.5 h2.6 l1.2 4.5" {...sw(1.9)} />
        <circle cx="98" cy="35.5" r="2.3" {...sw(1.9)} />
        <path d="M95.7 44 l1.2 -5 h2.6 l1.2 5" {...sw(1.9)} />
      </g>
      {/* 바울의 변론 — 사슬 찬 손 */}
      <g style={d(1900, reduce)}>
        <circle cx="34" cy="32" r="2.9" {...sw(2.6)} />
        <path d="M34 34.9 v11.1 M31 54 l3 -8 l3 8 M31.5 37 q-4.5 0.5 -7 2.5 M36.5 37 q4.5 0.5 7 2.5" {...sw(2.6)} />
        <path d="M29 47 q1.4 -1.4 2.8 0" {...sw(1.5, 0.8)} />
      </g>
      <g style={d(reduce ? 0 : 2700, reduce)} stroke="var(--paper-accent)">
        <path d="M34 20 v-4 M28 22 l-2.6 -2.6 M40 22 l2.6 -2.6" {...sw(1.4)}>
          {!reduce && <animate attributeName="opacity" values="1;0.5;1" begin="2.7s" dur="0.9s" repeatCount="2" />}
        </path>
      </g>
      <Label x="92" y="27" at="1.5" reduce={reduce}>벨릭스와 아그립바 앞에서</Label>
      <Label x="20" y="23" at="2.3" reduce={reduce}>바울의 변론</Label>
      <Label x="60" y="61" at="3" reduce={reduce} size="4.2">내가 가이사에게 상소하노라</Label>
    </g>
  )
}

// 멜리데 난파 (행 27-28)
function MaltaScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M10 50 q6 -2.5 12 0 q6 -2.5 12 0 M70 50 q8 -3 16 0 q8 -3 16 0" {...sw(1.3, 0.55)} />
        <path d="M46 46 q1 3 5 3 h7 l1 -4 M64 45 l1 4 h7 q4 0 5 -3 M58 42 v-10 M58 32 q-5 1.5 -6 6" {...sw(1.7, 0.75)} />
      </g>
      {/* 광풍 */}
      <g style={d(900, reduce)}>
        <path d="M14 16 q7 -3 14 0 M90 14 q7 -3 14 0 M30 10 q6 -2.5 12 0" {...sw(1.3, 0.5)} />
      </g>
      {/* 해안에 오른 생존자들 */}
      <g style={d(1900, reduce)}>
        <circle cx="30" cy="42" r="2.5" {...sw(2.2)} />
        <path d="M30 44.5 v6.5 M27.5 54 l2.5 -3 l2.5 3 M27.5 47 q-2.5 2 -4 4.5" {...sw(2.2)} />
        <circle cx="40" cy="43" r="2.3" {...sw(2, 0.85)} />
        <path d="M40 45.3 v6 M37.7 54 l2.3 -2.7 l2.3 2.7" {...sw(2, 0.85)} />
      </g>
      {/* 독사에 물려도 상하지 않은 바울 */}
      <g style={d(2700, reduce)}>
        <circle cx="86" cy="34" r="2.8" {...sw(2.5)} />
        <path d="M86 36.8 v10.2 M83 54 l3 -7.5 l3 7.5 M88.5 39 q4 -1 6 -3.5" {...sw(2.5)} />
        <circle cx="100" cy="45" r="2" {...sw(1.7, 0.8)} />
        <path d="M98.3 54 l0.9 -5.5 M101.7 54 l-0.9 -5.5 M98.3 48.5 h3.4" {...sw(1.7, 0.8)} />
        <g transform={reduce ? undefined : 'translate(0 0)'}>
          <path d="M94 34 q3 -1.5 2 -4 q-1 -2 -3.5 -1" {...sw(1.5, 0.8)} />
          {!reduce && (
            <animateTransform attributeName="transform" type="translate" from="0 0" to="3 5"
              begin="3s" dur="0.7s" fill="freeze" />
          )}
          {!reduce && <animate attributeName="opacity" from="1" to="0" begin="3s" dur="0.7s" fill="freeze" />}
        </g>
      </g>
      <Label x="58" y="24" at="1.2" reduce={reduce}>멜리데의 파선</Label>
      <Label x="94" y="25" at="2.9" reduce={reduce}>독사에 물려도 상하지 않다</Label>
      <Label x="60" y="61" at="3.1" reduce={reduce} size="4.2">네가 가이사 앞에 서야 하리라</Label>
    </g>
  )
}

// 목회서신 (딤전·딛 — 로마 첫 투옥 이후)
function ReleasePastoralsScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M20 54 v-6 h20 v6 M22 48 h16" {...sw(2)} />
      </g>
      {/* 목회서신을 쓰는 바울 */}
      <g style={d(900, reduce)}>
        <circle cx="30" cy="34" r="2.8" {...sw(2.5)} />
        <path d="M27 48 l1.5 -11.4 h3 l1.5 11.4 M32.5 39 q4 1 6 3.5" {...sw(2.5)} />
        <path d="M36 44 l3 3 M39.5 47.5 l1.6 -0.3" {...sw(1.6)} />
      </g>
      {/* 디모데와 디도 */}
      <g style={d(1900, reduce)}>
        <circle cx="70" cy="40" r="2.3" {...sw(2)} />
        <path d="M67.7 54 l1.4 -8 h2.6 l1.4 8 M70 46 q3 -1 5 -3" {...sw(2)} />
        <path d="M75 42 h6 q1.2 0 1.2 1.2 v0 q0 1.2 -1.2 1.2 h-6" {...sw(1.6)} />
        <circle cx="88" cy="40.5" r="2.3" {...sw(2)} />
        <path d="M85.7 54 l1.4 -7.5 h2.6 l1.4 7.5 M88 46.5 q3 -1 5 -3" {...sw(2)} />
        <path d="M93 42.5 h6 q1.2 0 1.2 1.2 v0 q0 1.2 -1.2 1.2 h-6" {...sw(1.6)} />
      </g>
      <g style={d(reduce ? 0 : 2700, reduce)} stroke="var(--paper-accent)">
        <path d="M76.5 43.6 h3.5 M94.5 44.1 h3.5" {...sw(1.3)}>
          {!reduce && <animate attributeName="opacity" values="1;0.5;1" begin="2.7s" dur="1s" repeatCount="2" />}
        </path>
      </g>
      <Label x="30" y="24" at="1.5" reduce={reduce}>목회서신을 쓰는 바울</Label>
      <Label x="79" y="32" at="2.3" reduce={reduce}>디모데와 디도</Label>
      <Label x="60" y="61" at="3" reduce={reduce} size="4.2">복음의 바통을 다음 세대에 넘기다</Label>
    </g>
  )
}

// 베드로의 로마 순교 (요 21:18-19)
function PeterRomeMartyrdomScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M80 54 v-14 q14 -10 28 0 v14 M86 54 v-9 M94 54 v-9 M102 54 v-9" {...sw(1.4, 0.5)} />
        <path d="M16 46 q5 -4.5 10 0" {...sw(1.3, 0.5)} />
      </g>
      {/* 노년의 베드로 — 지팡이 짚은 */}
      <g style={d(900, reduce)}>
        <circle cx="40" cy="34" r="2.8" {...sw(2.5)} />
        <path d="M40 36.8 q0 6 -1.5 10 M38.5 46.8 l-1 7 M41.5 47 l1 7 M43 38 q3.5 2 5 6" {...sw(2.5)} />
        <path d="M48 44 v10" {...sw(1.8)} />
      </g>
      {/* 결박하는 사슬 */}
      <g style={d(1900, reduce)}>
        <path d="M35 44 q1.6 -1.6 3.2 0 q1.6 1.6 3.2 0" {...sw(1.7, 0.85)} />
      </g>
      {/* 하늘 향한 소망 */}
      <g style={d(reduce ? 0 : 2700, reduce)}>
        <g transform={reduce ? undefined : 'translate(0 3)'} stroke="var(--paper-accent)">
          <path d="M40 22 v-6 M35 24 l-3 -3.5 M45 24 l3 -3.5" {...sw(1.6)} />
          {!reduce && (
            <animateTransform attributeName="transform" type="translate" from="0 3" to="0 -3"
              begin="2.7s" dur="1.4s" fill="freeze" />
          )}
          {!reduce && <animate attributeName="opacity" values="0.6;1" begin="2.7s" dur="1.4s" fill="freeze" />}
        </g>
      </g>
      <Label x="54" y="22" at="1.5" reduce={reduce}>로마의 노사도 베드로</Label>
      <Label x="94" y="33" at="1" reduce={reduce}>로마</Label>
      <Label x="60" y="61" at="3" reduce={reduce} size="4.2">네 양을 먹이라 — 장막을 벗을 날이 가까웠도다</Label>
    </g>
  )
}

// 바울의 로마 순교 (딤후 4장)
function PaulRomeMartyrdomScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M78 54 V26 h26 V54 M84 54 V30 M90 54 V30 M96 54 V30" {...sw(2)} />
      </g>
      {/* 옥중에서 마지막 편지를 쓰다 */}
      <g style={d(900, reduce)}>
        <circle cx="30" cy="34" r="2.8" {...sw(2.5)} />
        <path d="M27 48 l1.5 -11.4 h3 l1.5 11.4 M32.5 39 q4 1 6 3.5" {...sw(2.5)} />
        <path d="M25 44 q1.5 -1.5 3 0" {...sw(1.6, 0.8)} />
        <path d="M38 44 l3 2.5 M41.5 47 l1.6 -0.2" {...sw(1.6)} />
      </g>
      {/* 관제와 같이 부어지다 */}
      <g style={d(1900, reduce)}>
        <path d="M52 48 q1 -5 5 -5 q4 0 5 5 l-1 3 h-8 z" {...sw(1.8)} />
        <path d="M60 46 q3 1 4 4.5" {...sw(1.5, 0.75)} />
      </g>
      {/* 의의 면류관 */}
      <g style={d(reduce ? 0 : 2700, reduce)} stroke="var(--paper-accent)">
        <path d="M60 24 l2 -4 l2 3 l2 -4 l2 3 l2 -4 l2 4" {...sw(1.6)}>
          {!reduce && <animate attributeName="opacity" values="1;0.55;1" begin="2.7s" dur="1s" repeatCount="2" />}
        </path>
      </g>
      <Label x="30" y="24" at="1.5" reduce={reduce}>옥중에서 마지막 편지를 쓰다</Label>
      <Label x="60" y="40" at="2" reduce={reduce}>관제와 같이 부어지다</Label>
      <Label x="60" y="61" at="3.1" reduce={reduce} size="4.2">선한 싸움을 싸우고 달려갈 길을 마치다</Label>
    </g>
  )
}

const SCENES = {
  'authored-peter-pentecost': { Scene: PentecostScene, desc: '성령이 불의 혀같이 각 사람 위에', caption: '오순절 — 사도행전 2장' },
  'authored-peter-lame-man': { Scene: LameManScene, desc: '나사렛 예수의 이름으로 일어나 걸으라', caption: '미문 — 사도행전 3장' },
  'authored-peter-solomons-portico-trial': { Scene: PorticoTrialScene, desc: '공회 앞에서 담대히 증언하다', caption: '증언 — 사도행전 4장' },
  'authored-peter-samaria': { Scene: SamariaScene, desc: '안수하매 성령을 받다', caption: '사마리아 — 사도행전 8장' },
  'authored-paul-damascus-conversion': { Scene: DamascusScene, desc: '다메섹 길의 빛 앞에 엎드러지다', caption: '회심 — 사도행전 9장' },
  'authored-peter-aeneas-dorcas': { Scene: AeneasDorcasScene, desc: '애니아가 일어나고 다비다가 살아나다', caption: '룻다와 욥바 — 사도행전 9장' },
  'authored-peter-cornelius': { Scene: CorneliusScene, desc: '하나님이 깨끗하게 하신 것을 속되다 말라', caption: '고넬료 — 사도행전 10장' },
  'authored-peter-defends-gentiles': { Scene: DefendsGentilesScene, desc: '고넬료 집의 일을 차례로 증언하다', caption: '변호 — 사도행전 11장' },
  'authored-paul-antioch-ministry': { Scene: AntiochScene, desc: '일 년간 함께 가르치다 — 그리스도인의 탄생', caption: '안디옥 — 사도행전 11장' },
  'authored-peter-herod-prison': { Scene: HerodPrisonScene, desc: '쇠사슬이 벗어지고 옥문이 열리다', caption: '구출 — 사도행전 12장' },
  'authored-paul-cyprus-mission': { Scene: CyprusMissionScene, desc: '금식 중 성령의 지시로 바나바와 사울을 보내다 — 총독이 믿다', caption: '구브로 — 사도행전 13장' },
  'authored-paul-pisidian-antioch': { Scene: PisidianAntiochScene, desc: '시기하는 무리 앞에서 이방인에게로 향하다', caption: '비시디아 안디옥 — 사도행전 13장' },
  'authored-paul-iconium-lystra-derbe': { Scene: LystraScene, desc: '신으로 떠받들리다 돌에 맞고, 다시 일어나 더베로 가다', caption: '루스드라 — 사도행전 14장' },
  'authored-paul-jerusalem-council': { Scene: JerusalemCouncilScene, desc: '이방인에게 율법의 멍에를 지우지 말라', caption: '공의회 — 사도행전 15장' },
  'authored-paul-philippi': { Scene: PhilippiScene, desc: '한밤의 찬송에 옥터가 흔들리다', caption: '빌립보 — 사도행전 16장' },
  'authored-paul-thessalonica-berea': { Scene: ThessalonicaBereaScene, desc: '폭동으로 끝난 데살로니가와 날마다 상고한 베뢰아', caption: '데살로니가와 베뢰아 — 사도행전 17장' },
  'authored-paul-athens-areopagus': { Scene: AthensScene, desc: '알지 못하는 신에게 — 그를 전하노라', caption: '아레오바고 — 사도행전 17장' },
  'authored-paul-corinth': { Scene: CorinthScene, desc: '장막을 지으며 일 년 육 개월을 머물다', caption: '고린도 — 사도행전 18장' },
  'authored-paul-ephesus': { Scene: EphesusScene, desc: '두란노에서 두 해 동안 강론하다', caption: '에베소 — 사도행전 19장' },
  'authored-paul-miletus-farewell': { Scene: MiletusScene, desc: '결박이 기다림을 알고도 작별하다', caption: '밀레도 — 사도행전 20장' },
  'authored-paul-jerusalem-arrest': { Scene: JerusalemArrestScene, mood: 'dark', desc: '성전에서 붙잡혀 쇠사슬에 결박되다', caption: '체포 — 사도행전 21장' },
  'authored-paul-caesarea-imprisonment': { Scene: CaesareaScene, mood: 'dark', desc: '총독과 왕 앞에서 변론하고 가이사에게 상소하다', caption: '가이사랴 — 사도행전 25장' },
  'authored-paul-voyage-malta': { Scene: MaltaScene, mood: 'dark', desc: '광풍에 파선하나 한 생명도 잃지 않고 독사에도 상하지 않다', caption: '멜리데 난파 — 사도행전 27장' },
  'authored-paul-rome-house-arrest': { Scene: RomeScene, desc: '셋집에서 담대히 하나님 나라를 전하다', caption: '로마 — 사도행전 28장' },
  'authored-paul-release-pastorals': { Scene: ReleasePastoralsScene, desc: '풀려난 뒤 디모데와 디도에게 목회서신을 쓰다', caption: '목회서신 — 디모데전서 1장' },
  'authored-peter-rome-martyrdom': { Scene: PeterRomeMartyrdomScene, mood: 'dark', desc: '장막을 벗을 날을 알며 로마에서 생을 마치다', caption: '순교 — 요한복음 21장' },
  'authored-paul-rome-martyrdom': { Scene: PaulRomeMartyrdomScene, mood: 'dark', desc: '선한 싸움을 마치고 의의 면류관을 바라보다', caption: '순교 — 디모데후서 4장' },
  'authored-john-ephesus': { Scene: JohnEphesusScene, desc: '우리가 보고 만진 생명의 말씀을 쓰다', caption: '에베소의 요한 — 요한일서 1장' },
  'authored-john-patmos': { Scene: PatmosScene, desc: '주의 날에 일곱 교회에 보낼 계시를 받다', caption: '밧모 섬 — 요한계시록 1장' },
}

export default SCENES
