// 엘리야와 엘리사 — 18개 정차지 장면 (task#230, #227 표준)
import { sw, d, Label } from './lib'

// 가뭄 선언 (왕상 17:1)
function SamariaDroughtScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M20 54 l4 -3 l3 3 M64 54 l5 -3.5 l4 3.5" {...sw(1.2, 0.5)} />
        <path d="M30 52 l6 -2 M74 51.5 l6 -2" {...sw(1.1, 0.4)} />
      </g>
      {/* 아합의 왕좌 */}
      <g style={d(900, reduce)}>
        <path d="M82 54 h24 M100 54 V37 M88 46 h9" {...sw(2)} />
        <circle cx="92" cy="37" r="2.9" {...sw(2.2)} />
        <path d="M92 39.9 v6.1 M89 42.5 q3 -1.5 6 0" {...sw(2.2)} />
        <path d="M89.5 32.5 v-2.4 l1.4 1.4 l1.1 -2 l1.1 2 l1.4 -1.4 v2.4" {...sw(1.6)} />
      </g>
      {/* 엘리야 — 주역: 손 들어 선언 */}
      <g style={d(1800, reduce)}>
        <circle cx="40" cy="30" r="3.1" {...sw(2.6)} />
        <path d="M35.5 54 l2.2 -20 h4.6 l2.2 20 M35.5 54 h9" {...sw(2.6)} />
        <path d="M38 38 q0.5 8 0 14 M42 38 q0.4 8 0 14" {...sw(1.3, 0.55)} />
        <path d="M43.5 33 q5 -3.5 6 -8.5" {...sw(2.4)} />
      </g>
      {/* 마른 하늘 — 해 */}
      <g style={d(reduce ? 0 : 2800, reduce)} stroke="var(--paper-accent)">
        <circle cx="18" cy="14" r="4" {...sw(1.8)} />
        <path d="M18 7.5 v-2 M11.5 14 h-2 M13.5 9.5 l-1.6 -1.6 M22.5 9.5 l1.6 -1.6" {...sw(1.3)} />
      </g>
      <Label x="40" y="20" at="2.3" reduce={reduce}>엘리야</Label>
      <Label x="94" y="26" at="1.4" reduce={reduce}>아합</Label>
      <Label x="46" y="60" at="3" reduce={reduce} size="4.2">수년간 비도 이슬도 없으리라</Label>
    </g>
  )
}

// 사르밧 과부 (왕상 17:8-24)
function ZarephathWidowScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M14 54 l9 -13 l9 13" {...sw(1.6, 0.7)} />
      </g>
      {/* 통과 병 — 핵심: 마르지 않음 */}
      <g style={d(900, reduce)}>
        <path d="M46 54 v-9 q0 -2.5 2.5 -2.5 h7 q2.5 0 2.5 2.5 v9" {...sw(2.6)} />
        <path d="M48.5 46 h7" {...sw(1.4)} />
        <path d="M66 54 q-2.5 -1 -2.5 -4 q0 -4 3.5 -5 l0 -3 h3 l0 3 q3.5 1 3.5 5 q0 3 -2.5 4" {...sw(2.6)} />
        <path d="M68 41 h4" {...sw(1.6)} />
      </g>
      {/* 흘러넘치는 기름 — 강조 */}
      <g style={d(1900, reduce)} stroke="var(--paper-accent)">
        <path d="M70 44 q1.5 3 0.5 6 M50 45 q-1 2.5 -0.5 5" {...sw(1.6)} />
      </g>
      {/* 과부와 아이 */}
      <g style={d(2500, reduce)}>
        <circle cx="88" cy="38" r="2.8" {...sw(2.4)} />
        <path d="M84.5 54 l1.8 -13.5 h3.4 l1.8 13.5 M84.5 54 h7" {...sw(2.4)} />
        <circle cx="98" cy="43" r="2.1" {...sw(1.9)} />
        <path d="M98 45.1 v4.9 M96.2 54 l1.8 -4 l1.8 4 M95.5 45.5 l-3.5 2" {...sw(1.9)} />
      </g>
      <Label x="58" y="33" at="1.5" reduce={reduce}>가루 통과 기름병</Label>
      <Label x="92" y="29" at="3" reduce={reduce}>사르밧 과부</Label>
    </g>
  )
}

// 갈멜산 대결 (왕상 18:20-40)
function CarmelContestScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M6 54 q26 -12 52 -8" {...sw(1.3, 0.5)} />
      </g>
      {/* 제단 + 물 두른 도랑 */}
      <g style={d(900, reduce)}>
        <path d="M50 50 v-6 h20 v6 M48 50 h24" {...sw(2.4)} />
        <path d="M52 47.5 h4 m4 0 h4 m4 0 h4 M54 41.5 l5 -1.5 m3 1 l5 -1.5" {...sw(1.4)} />
        <path d="M44 53 q16 -3 32 0" {...sw(1.3, 0.55)} />
      </g>
      {/* 하늘의 불 — 핵심: 내려옴 */}
      <g transform={reduce ? undefined : 'translate(0 -32)'} style={d(1900, reduce)}>
        <path d="M57 39 q-3 -6 0 -11 q3 5 0 11 M62 39 q-2.4 -6.5 0.8 -11" {...sw(3)} stroke="var(--paper-accent)" />
        {!reduce && (
          <animateTransform attributeName="transform" type="translate" from="0 -32" to="0 0"
            begin="2.2s" dur="0.5s" fill="freeze" calcMode="spline" keySplines="0.4 0 0.8 1" keyTimes="0;1" />
        )}
      </g>
      {/* 엎드린 백성 */}
      <g style={d(2800, reduce)}>
        <circle cx="24" cy="49.5" r="2.2" {...sw(1.9)} />
        <path d="M26 50.5 q4 -1.6 7 1 M22 51 l-3.5 3" {...sw(1.9)} />
        <circle cx="94" cy="50" r="2.1" {...sw(1.8, 0.9)} />
        <path d="M92 51 q-4 -1.6 -7 1 M96 51.5 l3.5 2.5" {...sw(1.8, 0.9)} />
      </g>
      <Label x="60" y="60" at="1.4" reduce={reduce}>갈멜산 제단</Label>
      <Label x="60" y="12" at="2.7" reduce={reduce}>여호와의 불</Label>
      <Label x="26" y="41" at="3.2" reduce={reduce} size="4.2">엎드린 백성</Label>
    </g>
  )
}

// 호렙산 세미한 소리 (왕상 19:8-18)
function HorebWhisperScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M28 54 q0 -26 30 -28 q30 -2 34 28" {...sw(2.2)} />
        <path d="M44 34 l4 -2.5 M76 33 l4 2" {...sw(1.2, 0.4)} />
      </g>
      {/* 지나간 것들 — 바람·지진·불(옅게, 왼쪽 바깥) */}
      <g style={d(1000, reduce)}>
        <path d="M6 20 q6 -3 12 0 q6 -3 10 0 M8 27 q5 -2.5 10 0" {...sw(1.2, 0.4)} />
        <path d="M10 38 l3 -3 l2.5 3 l3 -3" {...sw(1.2, 0.4)} />
        <path d="M14 48 q-1.6 -3 0 -5.5 q1.6 2.5 0 5.5" {...sw(1.3, 0.45)} />
      </g>
      {/* 웅크린 엘리야 — 겉옷으로 얼굴 가림 */}
      <g style={d(1900, reduce)}>
        <circle cx="60" cy="42" r="2.9" {...sw(2.6)} />
        <path d="M56 54 l2 -9.5 h4 l2 9.5 M56 54 h8" {...sw(2.6)} />
        <path d="M57 41 q3 -3.5 6.5 -0.5" {...sw(2)} />
      </g>
      {/* 세미한 소리 — 아주 가는 물결 */}
      <g style={d(reduce ? 0 : 3000, reduce)} stroke="var(--paper-accent)">
        <path d="M74 36 q3 -1.4 6 0 M76 32.5 q3 -1.4 6 0 M78 29 q2.6 -1.2 5.2 0" {...sw(1.2)} />
      </g>
      <Label x="60" y="61" at="2.4" reduce={reduce}>엘리야</Label>
      <Label x="86" y="23" at="3.3" reduce={reduce}>세미한 소리</Label>
    </g>
  )
}

// 엘리사를 부름 (왕상 19:19-21)
function CallElishaScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M10 50 q14 -2 28 0 M44 51 q14 -2 28 0" {...sw(1.2, 0.45)} />
      </g>
      {/* 밭 가는 소 — 멍에 */}
      <g style={d(900, reduce)}>
        <path d="M58 48 q0 -5 6 -5 q6 0 6 5 q0 3.5 -6 3.5 q-6 0 -6 -3.5" {...sw(2)} />
        <circle cx="72.5" cy="44.5" r="2.4" {...sw(2)} />
        <path d="M73.5 42.5 q2.5 -2 1.5 -4.5 M60 54 v-1.5 M68 54 v-1.5" {...sw(1.5)} />
        <path d="M78 48.5 q0 -4.5 5.5 -4.5 q5.5 0 5.5 4.5 q0 3 -5.5 3 q-5.5 0 -5.5 -3" {...sw(1.8, 0.85)} />
        <circle cx="91" cy="45.5" r="2.2" {...sw(1.8, 0.85)} />
        <path d="M74 44 h5.5" {...sw(1.6)} />
        <path d="M56 50 l-6 2" {...sw(1.8)} />
      </g>
      {/* 엘리사 — 쟁기 잡던 손 */}
      <g style={d(1800, reduce)}>
        <circle cx="46" cy="41" r="2.8" {...sw(2.5)} />
        <path d="M46 43.8 v5.2 M43.5 54 l2.5 -5 l2.5 5 M48.5 45 l4 3" {...sw(2.5)} />
      </g>
      {/* 겉옷 — 핵심: 날아와 걸쳐짐 */}
      <g style={d(2600, reduce)}>
        <path d="M18 30 q4 -3 8 -1 l1.5 3 q-1 2.5 -4 2 l-5 -1 q-2 -1.5 -0.5 -3" {...sw(2.6)}>
          {!reduce && (
            <animateMotion path="M0 0 q13 -6 26 6" begin="2.8s" dur="0.8s" fill="freeze"
              calcMode="spline" keySplines="0.3 0 0.7 1" keyTimes="0;1" />
          )}
        </path>
      </g>
      <Label x="46" y="31" at="2.2" reduce={reduce}>엘리사</Label>
      <Label x="20" y="22" at="3.2" reduce={reduce}>엘리야의 겉옷</Label>
    </g>
  )
}

// 나봇의 포도원 (왕상 21:17-24)
function NabothVineyardScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        {/* 포도원 — 덩굴 시렁 */}
        <path d="M64 54 v-10 M80 54 v-10 M96 54 v-10 M60 44 h40" {...sw(1.8)} />
        <path d="M66 44 q3 4 7 4 q4 0 7 -4 M82 44 q3 4 7 4 q4 0 6 -3" {...sw(1.4, 0.7)} />
        <circle cx="72" cy="49" r="1.4" {...sw(1.3, 0.7)} />
        <circle cx="88" cy="48.5" r="1.4" {...sw(1.3, 0.7)} />
      </g>
      {/* 아합 — 왕관, 움찔 물러섬 */}
      <g style={d(1200, reduce)}>
        <circle cx="52" cy="36" r="2.8" {...sw(2.2)} />
        <path d="M52 38.8 v8.2 M49.5 54 l2.5 -7 l2.5 7 M50 41.5 l-3.5 2.5" {...sw(2.2)} />
        <path d="M49.8 31.8 v-2.2 l1.3 1.2 l0.9 -1.8 l0.9 1.8 l1.3 -1.2 v2.2" {...sw(1.5)} />
      </g>
      {/* 엘리야 — 주역: 심판 선언 */}
      <g style={d(2200, reduce)}>
        <circle cx="26" cy="31" r="3" {...sw(2.6)} />
        <path d="M22 54 l2 -19.5 h4 l2 19.5 M22 54 h8" {...sw(2.6)} />
        <path d="M29.5 35 q6 -1.5 10 1" {...sw(2.4)} />
      </g>
      <Label x="26" y="21" at="2.7" reduce={reduce}>엘리야</Label>
      <Label x="52" y="27" at="1.7" reduce={reduce}>아합</Label>
      <Label x="82" y="36" at="0.9" reduce={reduce}>나봇의 포도원</Label>
    </g>
  )
}

// 불수레 승천 (왕하 2:1-12)
function JordanAscensionScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M8 50 q8 -2.5 16 0 q8 -2.5 16 0" {...sw(1.3, 0.55)} />
      </g>
      {/* 불수레 — 핵심: 상승 */}
      <g transform={reduce ? 'translate(10 -14)' : undefined} style={d(1000, reduce)}>
        <circle cx="62" cy="34" r="4" {...sw(2.4)} />
        <path d="M62 30 v8 M58 34 h8 M59.2 31.2 l5.6 5.6 M64.8 31.2 l-5.6 5.6" {...sw(1.5)} />
        <path d="M66 30 h10 q3 0 3.5 3 l-1 3 h-10" {...sw(2.4)} />
        <circle cx="76" cy="38" r="3.2" {...sw(2)} />
        <path d="M68 27 q-2 -3.5 0 -6.5 q2 3 0 6.5 M73 26 q-1.6 -3.5 0.6 -6" {...sw(2)} stroke="var(--paper-accent)" />
        {!reduce && (
          <animateTransform attributeName="transform" type="translate" from="0 0" to="12 -17"
            begin="2.4s" dur="1.8s" fill="freeze" calcMode="spline" keySplines="0.35 0 0.6 1" keyTimes="0;1" />
        )}
      </g>
      {/* 회오리 */}
      <g style={d(2000, reduce)}>
        <path d="M46 44 q-5 -3 -2 -8 q4 -3 8 -1 M44 34 q-3 -4 1 -7" {...sw(1.4, 0.6)} />
      </g>
      {/* 엘리사 — 떨어진 겉옷 줍기 */}
      <g style={d(3000, reduce)}>
        <circle cx="26" cy="42" r="2.8" {...sw(2.5)} />
        <path d="M26 44.8 v4 M23.5 54 l2.5 -5 l2.5 5 M28.5 46 l4 4" {...sw(2.5)} />
        <path d="M33 51 q3.5 -2 6.5 0 l1 2.5 q-2.5 1.5 -5.5 0.5 z" {...sw(2.2)} />
      </g>
      <Label x="80" y="20" at="2" reduce={reduce}>불수레</Label>
      <Label x="26" y="33" at="3.5" reduce={reduce}>겉옷을 받은 엘리사</Label>
    </g>
  )
}

// 여리고 물 고침 (왕하 2:19-22)
function JerichoWaterScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M84 44 q13 -8 26 -2" {...sw(1.1, 0.4)} />
      </g>
      {/* 샘 */}
      <g style={d(900, reduce)}>
        <path d="M40 52 q10 -3.5 20 0 q10 -3.5 20 0" {...sw(2.2)} />
        <path d="M46 48.5 q7 -2.5 14 0 q7 -2.5 14 0" {...sw(1.6, 0.7)} />
      </g>
      {/* 소금 그릇 붓기 — 핵심 */}
      <g transform={reduce ? 'rotate(-35 46 34)' : undefined} style={d(1800, reduce)}>
        <path d="M42 34 q0 -3.5 4.5 -3.5 q4.5 0 4.5 3.5 M42 34 h9" {...sw(2.6)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="rotate" from="0 46 34" to="-35 46 34"
            begin="2.2s" dur="0.6s" fill="freeze" />
        )}
      </g>
      <g style={d(reduce ? 0 : 2900, reduce)}>
        <path d="M49 38 l1 2 m1.5 -1 l1 2 m-5 -1.5 l0.8 1.8" {...sw(1.3)} />
      </g>
      {/* 엘리사 */}
      <g style={d(1400, reduce)}>
        <circle cx="30" cy="32" r="2.9" {...sw(2.5)} />
        <path d="M26 54 l2 -18.5 h4 l2 18.5 M26 54 h8 M33.5 36 q4 -1 7 -0.5" {...sw(2.5)} />
      </g>
      <g style={d(reduce ? 0 : 3400, reduce)} stroke="var(--paper-accent)">
        <path d="M74 42 q2 -1.4 4 0 M77 38.5 q2 -1.4 4 0" {...sw(1.3)} />
      </g>
      <Label x="30" y="22" at="1.9" reduce={reduce}>엘리사</Label>
      <Label x="62" y="38" at="3.3" reduce={reduce}>고쳐진 샘</Label>
    </g>
  )
}

// 과부의 기름 (왕하 4:1-7)
function WidowOilScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M12 54 l8 -11 l8 11" {...sw(1.5, 0.6)} />
      </g>
      {/* 그릇들 — 차례로 채워짐(순차 draw) */}
      <g style={d(900, reduce)}>
        <path d="M44 54 v-5 q0 -2 2 -2 h4 q2 0 2 2 v5" {...sw(2)} />
      </g>
      <g style={d(1500, reduce)}>
        <path d="M58 54 v-6 q0 -2.2 2.2 -2.2 h4.4 q2.2 0 2.2 2.2 v6" {...sw(2.1)} />
      </g>
      <g style={d(2100, reduce)}>
        <path d="M72 54 v-5.5 q0 -2 2 -2 h4 q2 0 2 2 v5.5" {...sw(2.2)} />
      </g>
      <g style={d(2700, reduce)}>
        <path d="M86 54 v-4.5 q0 -1.8 1.8 -1.8 h3.4 q1.8 0 1.8 1.8 v4.5" {...sw(2.2)} />
      </g>
      {/* 붓는 여인 — 주역 */}
      <g style={d(1800, reduce)}>
        <circle cx="30" cy="34" r="2.9" {...sw(2.5)} />
        <path d="M26.5 54 l1.8 -15 h3.4 l1.8 15 M26.5 54 h7" {...sw(2.5)} />
        <path d="M33 38 q4 1 6 3.5" {...sw(2.2)} />
        <path d="M38 42 q2.5 -1.5 5 0 l0.5 2 q-2.5 1 -5 0 z" {...sw(2.2)} />
        <path d="M42 45.5 l1 2.5" {...sw(1.4)} stroke="var(--paper-accent)" />
      </g>
      <Label x="30" y="24" at="2.2" reduce={reduce}>과부</Label>
      <Label x="68" y="38" at="3.1" reduce={reduce}>차오르는 그릇들</Label>
    </g>
  )
}

// 수넴 여인의 아들 (왕하 4:32-37)
function ShunemSonScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M18 22 h20 M18 22 v-4 M38 22 v-4" {...sw(1.2, 0.45)} />
      </g>
      {/* 침상 + 아이 */}
      <g style={d(900, reduce)}>
        <path d="M34 50 h52 M38 54 v-4 M82 54 v-4" {...sw(2)} />
        <circle cx="46" cy="46.5" r="2.3" {...sw(2)} />
        <path d="M48.5 47.5 q8 1.5 16 1" {...sw(2)} />
      </g>
      {/* 몸을 포갠 엘리사 — 위로 굽힘 */}
      <g style={d(1800, reduce)}>
        <circle cx="52" cy="34" r="2.8" {...sw(2.5)} />
        <path d="M54.5 35.5 q6 2 10 6 M64 41 l4 6 M55 37 l-2 5 M53 42 l3.5 4.5" {...sw(2.5)} />
      </g>
      {/* 깨어남 — 강조 */}
      <g style={d(reduce ? 0 : 3000, reduce)} stroke="var(--paper-accent)">
        <path d="M42 38 l-2 -2.6 M46 37 v-3 M50 38 l2 -2.6" {...sw(1.5)} />
      </g>
      <Label x="58" y="26" at="2.3" reduce={reduce}>엘리사</Label>
      <Label x="44" y="60" at="1.3" reduce={reduce}>수넴 여인의 아들</Label>
    </g>
  )
}

// 나아만 (왕하 5:10-14)
function NaamanScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
      </g>
      {/* 요단강 — 일곱 물결 */}
      <g style={d(900, reduce)}>
        <path d="M10 46 q7 -3 14 0 q7 -3 14 0 q7 -3 14 0 q7 -3 14 0 q7 -3 14 0 q7 -3 14 0 q7 -3 14 0" {...sw(2.2)} />
        <path d="M16 50.5 q7 -2.5 14 0 q7 -2.5 14 0 q7 -2.5 14 0 q7 -2.5 14 0 q7 -2.5 14 0" {...sw(1.5, 0.65)} />
      </g>
      {/* 물에 잠긴 나아만 — 상반신만 */}
      <g style={d(1800, reduce)}>
        <circle cx="58" cy="38" r="2.9" {...sw(2.6)} />
        <path d="M58 40.9 v4.1 M54 43 q4 -2 8 0" {...sw(2.6)} />
      </g>
      {/* 벗어둔 갑옷·투구 — 강가 */}
      <g style={d(2600, reduce)}>
        <path d="M88 54 v-6 h10 v6 M89.5 50 h7 M90 46 a4 4 0 0 1 6 0" {...sw(1.8)} />
        <path d="M102 52 l5 -2" {...sw(1.6)} />
      </g>
      <g style={d(reduce ? 0 : 3300, reduce)} stroke="var(--paper-accent)">
        <path d="M52 30 l-2 -2.4 M58 29 v-3 M64 30 l2 -2.4" {...sw(1.5)} />
      </g>
      <Label x="58" y="23" at="3.4" reduce={reduce}>나아만</Label>
      <Label x="94" y="38" at="2.8" reduce={reduce} size="4.2">벗어둔 갑주</Label>
      <Label x="60" y="61" at="1.3" reduce={reduce} size="4.2">요단강 일곱 번</Label>
    </g>
  )
}

// 도단의 불병거 (왕하 6:15-17)
function DothanChariotsScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M6 40 L34 22 L60 34 L88 18 L114 32" {...sw(1.8, 0.7)} />
      </g>
      {/* 산에 가득한 불말·불병거 — 능선 위 */}
      <g style={d(1100, reduce)} stroke="var(--paper-accent)">
        <circle cx="30" cy="17" r="2.6" {...sw(1.8)} />
        <path d="M30 14.4 v5.2 M27.4 17 h5.2" {...sw(1.2)} />
        <path d="M35 15 h7 q2 0 2.5 2" {...sw(1.6)} />
        <circle cx="86" cy="13" r="2.4" {...sw(1.7)} />
        <path d="M86 10.6 v4.8 M83.6 13 h4.8" {...sw(1.2)} />
        <path d="M91 11.5 h6 q1.8 0 2.2 1.8" {...sw(1.5)} />
        <path d="M56 25 q-1.6 -3 0 -5.5 q1.6 2.5 0 5.5 M62 24 q-1.4 -3 0.5 -5" {...sw(1.5)} />
        {!reduce && <animate attributeName="opacity" values="1;0.55;1" begin="2.4s" dur="1.4s" repeatCount="2" />}
      </g>
      {/* 엘리사와 사환 */}
      <g style={d(2200, reduce)}>
        <circle cx="44" cy="42" r="2.8" {...sw(2.5)} />
        <path d="M40.5 54 l1.8 -9.5 h3.4 l1.8 9.5 M40.5 54 h7 M47 45 q3.5 -2 4.5 -5" {...sw(2.5)} />
        <circle cx="56" cy="44" r="2.3" {...sw(2)} />
        <path d="M56 46.3 v3.7 M54 54 l2 -4 l2 4 M54 45.5 q-2 1.5 -2.5 3.5" {...sw(2)} />
      </g>
      <Label x="58" y="8" at="1.8" reduce={reduce}>불말과 불병거</Label>
      <Label x="50" y="34" at="2.8" reduce={reduce}>엘리사와 사환</Label>
    </g>
  )
}

// 하사엘과 다메섹 (왕하 8:7-15)
function HazaelDamascusScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M82 54 v-6 h5 v6 m3 0 v-9 h5 v9 m3 0 v-5 h5 v5" {...sw(1.3, 0.5)} />
      </g>
      {/* 하사엘 — 서 있음 */}
      <g style={d(1000, reduce)}>
        <circle cx="70" cy="36" r="2.8" {...sw(2.2)} />
        <path d="M70 38.8 v8.2 M67 54 l3 -7 l3 7 M67.5 42 q-3 -1 -5 -2.5" {...sw(2.2)} />
      </g>
      {/* 우는 엘리사 — 주역: 얼굴 가림 + 눈물 */}
      <g style={d(1900, reduce)}>
        <circle cx="38" cy="33" r="3" {...sw(2.6)} />
        <path d="M34 54 l2 -18 h4 l2 18 M34 54 h8" {...sw(2.6)} />
        <path d="M36 34.5 q2 2.5 4.5 0.5" {...sw(2)} />
      </g>
      <g style={d(reduce ? 0 : 2900, reduce)} stroke="var(--paper-accent)">
        <path d="M35.5 39 q-0.6 2 0 3.5 M40.5 39 q0.6 2 0 3.5" {...sw(1.5)} />
      </g>
      <Label x="38" y="23" at="2.4" reduce={reduce}>우는 엘리사</Label>
      <Label x="72" y="27" at="1.5" reduce={reduce}>하사엘</Label>
      <Label x="94" y="38" at="0.9" reduce={reduce}>다메섹</Label>
    </g>
  )
}

// 사마리아 포위 구원 (왕하 7:1-2)
function SamariaSiegeScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        {/* 성문 */}
        <path d="M18 54 v-20 M42 54 v-20 M15 34 h30 M24 54 v-14 q6 -5 12 0 v14" {...sw(2.2)} />
        <path d="M20 40 h2 m16 0 h2" {...sw(1.2, 0.45)} />
      </g>
      {/* 쏟아진 곡식 자루 — 핵심 */}
      <g style={d(1400, reduce)}>
        <path d="M62 54 q-1 -7 4 -8 q6 -1 7 5 q0.5 3 -3 3 z" {...sw(2.4)} />
        <path d="M76 54 q0 -5.5 5 -5.5 q5 0 5 5.5" {...sw(2.2)} />
        <path d="M70 47 l1.5 -2 m2 3 l1.5 -2 m-7 0.5 l1.2 -1.6" {...sw(1.3)} stroke="var(--paper-accent)" />
      </g>
      {/* 저울 */}
      <g style={d(2400, reduce)}>
        <path d="M98 38 v12 M92 40 h12 M92 40 q0 4 3 4 q3 0 3 -4 M104 40 q0 4 -3 4" {...sw(1.8)} />
      </g>
      <Label x="30" y="27" at="1.2" reduce={reduce}>사마리아 성문</Label>
      <Label x="74" y="38" at="2" reduce={reduce}>헐값이 된 곡식</Label>
    </g>
  )
}

// 엘리사의 뼈 (왕하 13:20-21)
function BoneResurrectionScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M84 44 q13 -8 26 -2" {...sw(1.1, 0.4)} />
      </g>
      {/* 무덤 석곽 */}
      <g style={d(900, reduce)}>
        <path d="M34 54 v-8 h32 v8 M32 46 h36" {...sw(2.2)} />
        <path d="M38 50 h5 m6 0 h5 m6 0 h5" {...sw(1.2, 0.5)} />
      </g>
      {/* 일어나는 자 — 핵심: 상승 */}
      <g transform={reduce ? undefined : 'translate(0 10)'} style={d(1800, reduce)}>
        <circle cx="50" cy="30" r="2.9" {...sw(2.6)} />
        <path d="M50 32.9 v8.1 M47 44 l3 -3 l3 3 M50 35 q-4 1 -5.5 4 M50 35 q4 1 5.5 4" {...sw(2.6)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="translate" from="0 10" to="0 0"
            begin="2.2s" dur="1s" fill="freeze" calcMode="spline" keySplines="0.3 0 0.5 1" keyTimes="0;1" />
        )}
      </g>
      {/* 놀라 물러선 장사꾼들 */}
      <g style={d(3000, reduce)}>
        <circle cx="88" cy="45" r="2.2" {...sw(1.9)} />
        <path d="M88 47.2 v3.3 M86 54 l2 -3.5 l2 3.5 M86 46 l-3 2" {...sw(1.9)} />
      </g>
      <Label x="50" y="20" at="2.9" reduce={reduce}>일어난 자</Label>
      <Label x="50" y="61" at="1.3" reduce={reduce}>엘리사의 묘</Label>
    </g>
  )
}

// 요나의 도피 (욘 1:1-3)
function JonahFlightScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M8 48 q8 -3 16 0 q8 -3 16 0 q8 -3 16 0 q8 -3 16 0 q8 -3 16 0 q8 -3 16 0" {...sw(2)} />
      </g>
      {/* 다시스행 배 — 왼쪽으로(반대 방향) */}
      <g transform={reduce ? 'translate(-10 0)' : undefined} style={d(1100, reduce)}>
        <path d="M46 44 q2 5 8 5 h20 q6 0 8 -5 l-3 -4 h-30 z" {...sw(2.4)} />
        <path d="M64 40 V24 M64 24 q-9 2 -12 12 q6 2 12 0 M64 28 q7 1 10 8" {...sw(2)} />
        <circle cx="56" cy="46" r="1.6" {...sw(1.8)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="translate" from="0 0" to="-14 0"
            begin="2s" dur="2.4s" fill="freeze" calcMode="spline" keySplines="0.3 0 0.7 1" keyTimes="0;1" />
        )}
      </g>
      {/* 니느웨 방향 표시 — 반대편 */}
      <g style={d(2400, reduce)}>
        <path d="M96 32 h12 m-3 -3 l3 3 l-3 3" {...sw(1.5, 0.7)} />
      </g>
      <Label x="60" y="14" at="1.6" reduce={reduce}>다시스행 배</Label>
      <Label x="100" y="26" at="2.8" reduce={reduce} size="4.2">니느웨는 반대편</Label>
    </g>
  )
}

// 니느웨의 회개 (욘 3:4-10)
function JonahNinevehScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        {/* 큰 성 니느웨 */}
        <path d="M14 54 v-16 h20 v16 M40 54 v-22 h22 v22 M68 54 v-14 h18 v14" {...sw(1.8, 0.8)} />
        <path d="M44 32 v-4 h5 v4 m5 0 v-4 h5 v4 M18 38 v-3 h4 v3" {...sw(1.3, 0.55)} />
      </g>
      {/* 베옷 입은 왕 — 왕관 내려놓음 */}
      <g style={d(1500, reduce)}>
        <circle cx="94" cy="45" r="2.5" {...sw(2.4)} />
        <path d="M96 46.5 q4.5 -2 8 1 M92 47 l-4 3.5" {...sw(2.4)} />
        <path d="M104 51 v-2 l1.2 1 l1 -1.5 l1 1.5 l1.2 -1 v2" {...sw(1.6)} />
      </g>
      {/* 요나 — 외침 */}
      <g style={d(2300, reduce)}>
        <circle cx="76" cy="34" r="2.7" {...sw(2.4)} />
        <path d="M72.5 48 l1.8 -11.5 h3.4 l1.8 11.5 M72.5 48 h7 M79 37.5 q3.5 -1.5 5.5 -3.5" {...sw(2.4)} />
      </g>
      <Label x="38" y="26" at="1.2" reduce={reduce}>큰 성 니느웨</Label>
      <Label x="98" y="37" at="1.9" reduce={reduce}>회개한 왕</Label>
    </g>
  )
}

// 이사야의 소명 (사 6:1-8)
function IsaiahCallingScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
      </g>
      {/* 높이 들린 보좌 */}
      <g style={d(900, reduce)}>
        <path d="M48 34 h24 M52 34 v-12 M68 34 v-12 M50 22 h20 M46 34 l-2 6 h32 l-2 -6" {...sw(2.4)} />
        <path d="M54 40 q6 3 12 0 M50 44 q10 4 20 0" {...sw(1.4, 0.6)} />
      </g>
      {/* 스랍 날개 — 여섯 날개 두 쌍 곡선 */}
      <g style={d(1800, reduce)}>
        <path d="M40 16 q-8 -3 -10 -10 M44 18 q-4 -6 -2 -12 M40 22 q-8 1 -12 6" {...sw(1.5, 0.75)} />
        <path d="M80 16 q8 -3 10 -10 M76 18 q4 -6 2 -12 M80 22 q8 1 12 6" {...sw(1.5, 0.75)} />
      </g>
      {/* 숯불 부젓가락 — 강조 */}
      <g style={d(2600, reduce)} stroke="var(--paper-accent)">
        <path d="M34 38 l8 6 M33 40 l8 4.5" {...sw(1.6)} />
        <circle cx="32.5" cy="38.5" r="1.8" {...sw(2)} />
      </g>
      {/* 엎드린 이사야 */}
      <g style={d(3200, reduce)}>
        <circle cx="22" cy="49" r="2.4" {...sw(2.2)} />
        <path d="M24 50 q4.5 -1.6 7.5 1 M20 50.5 l-3.5 3" {...sw(2.2)} />
      </g>
      <Label x="60" y="12" at="1.4" reduce={reduce}>높이 들린 보좌</Label>
      <Label x="22" y="41" at="3.6" reduce={reduce}>이사야</Label>
      <Label x="60" y="61" at="3.9" reduce={reduce} size="4.2">내가 여기 있나이다 나를 보내소서</Label>
    </g>
  )
}

const SCENES = {
  'authored-elijah-samaria-drought': { Scene: SamariaDroughtScene, desc: '내 말이 없으면 비도 이슬도 없으리라', caption: '가뭄 선언 — 열왕기상 17장' },
  'authored-elijah-zarephath-widow': { Scene: ZarephathWidowScene, desc: '통의 가루와 병의 기름이 마르지 않다', caption: '사르밧 — 열왕기상 17장' },
  'authored-elijah-carmel-contest': { Scene: CarmelContestScene, desc: '여호와께서 불로 응답하시다', caption: '갈멜산 — 열왕기상 18장' },
  'authored-elijah-horeb-whisper': { Scene: HorebWhisperScene, desc: '바람과 지진과 불이 아닌 세미한 소리', caption: '호렙산 — 열왕기상 19장' },
  'authored-elijah-abelmeholah-elisha': { Scene: CallElishaScene, desc: '밭 갈던 엘리사에게 겉옷이 던져지다', caption: '부르심 — 열왕기상 19장' },
  'authored-elijah-naboth-vineyard': { Scene: NabothVineyardScene, mood: 'dark', desc: '네가 죽이고 또 빼앗았느냐', caption: '나봇의 포도원 — 열왕기상 21장' },
  'authored-elijah-jordan-ascension': { Scene: JordanAscensionScene, desc: '불수레와 회오리로 하늘에 오르다', caption: '승천 — 열왕기하 2장' },
  'authored-elisha-jericho-water': { Scene: JerichoWaterScene, desc: '소금을 던지니 물이 고쳐지다', caption: '여리고의 샘 — 열왕기하 2장' },
  'authored-elisha-widow-oil': { Scene: WidowOilScene, desc: '빈 그릇마다 기름이 차오르다', caption: '과부의 기름 — 열왕기하 4장' },
  'authored-elisha-shunem-son': { Scene: ShunemSonScene, desc: '죽은 아이가 다시 숨을 쉬다', caption: '수넴 — 열왕기하 4장' },
  'authored-elisha-naaman': { Scene: NaamanScene, desc: '일곱 번 씻으매 어린아이 살같이 되다', caption: '나아만 — 열왕기하 5장' },
  'authored-elisha-dothan-chariots': { Scene: DothanChariotsScene, desc: '산에 가득한 불말과 불병거를 보다', caption: '도단 — 열왕기하 6장' },
  'authored-elisha-hazael-damascus': { Scene: HazaelDamascusScene, mood: 'dark', desc: '이스라엘에 닥칠 재앙을 알고 울다', caption: '다메섹 — 열왕기하 8장' },
  'authored-elisha-samaria-siege': { Scene: SamariaSiegeScene, desc: '내일 이맘때 고운 가루가 헐값 되리라', caption: '포위의 끝 — 열왕기하 7장' },
  'authored-elisha-death-bone-resurrection': { Scene: BoneResurrectionScene, desc: '엘리사의 뼈에 닿자 죽은 자가 일어서다', caption: '마지막 기적 — 열왕기하 13장' },
  'authored-jonah-flight-joppa': { Scene: JonahFlightScene, mood: 'dark', desc: '니느웨를 피해 다시스로 달아나다', caption: '욥바 — 요나 1장' },
  'authored-jonah-nineveh-preaching': { Scene: JonahNinevehScene, desc: '왕부터 백성까지 굵은 베를 입다', caption: '니느웨 — 요나 3장' },
  'authored-isaiah-jerusalem-calling': { Scene: IsaiahCallingScene, desc: '내가 여기 있나이다 나를 보내소서', caption: '소명 — 이사야 6장' },
}

export default SCENES
