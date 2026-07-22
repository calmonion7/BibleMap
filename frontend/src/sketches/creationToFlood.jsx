// 창조에서 홍수까지 — 12개 정차지 장면 (task#228, #227 표준: 얇은 선 위계·이름표·상황설명·무드·SMIL 안무)
import { sw, d, Label } from './lib'

// 에덴동산에 아담을 두심 (창 2:8,15)
function AdamEdenScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M8 54 q16 -4 30 -1 q4 -1 8 0" {...sw(1.3, 0.55)} />
        <path d="M46 54 q6 -3 4 -8 M50 54 q7 -4 6 -10" {...sw(1.1, 0.45)} />
      </g>
      {/* 생명나무 — 핵심: 굵은 줄기 + 풍성한 관, 열매 */}
      <g style={d(700, reduce)}>
        <path d="M80 54 q-1 -12 -2 -20" {...sw(2.6)} />
        <path d="M78 34 q-14 -2 -16 -12 q10 -4 16 2 q0 -10 8 -12 q6 4 4 12 q10 -4 14 4 q-4 10 -16 8 q-4 2 -10 -2" {...sw(2)} />
        <circle cx="70" cy="28" r="1.4" {...sw(1.3)} />
        <circle cx="88" cy="26" r="1.4" {...sw(1.3)} />
        <circle cx="80" cy="18" r="1.4" {...sw(1.3)} />
      </g>
      {/* 작은 나무·풀 — 원경 */}
      <g style={d(1400, reduce)}>
        <path d="M20 54 v-8 M20 46 q-4 -1 -5 -5 q5 -1 5 5 q0 -6 5 -5 q-1 4 -5 5" {...sw(1.4, 0.7)} />
        <path d="M100 54 v-6 M100 48 q-3 -1 -4 -4 q4 0 4 4 q0 -4 4 -4 q-1 3 -4 4" {...sw(1.2, 0.5)} />
      </g>
      {/* 아담 — 주역: 동산을 향해 팔 벌림 */}
      <g style={d(2200, reduce)}>
        <circle cx="40" cy="36" r="3" {...sw(2.5)} />
        <path d="M40 39 v8.5 M37 54 l3 -6.5 l3 6.5" {...sw(2.5)} />
        <path d="M40 41.5 q-4 -1.5 -6.5 -4 M40 41.5 q4.5 -1 7 -3.5" {...sw(2.2)} />
        <path d="M38.5 44 q1.5 1 3 0" {...sw(1.3, 0.6)} />
      </g>
      {/* 새 두 마리 */}
      <g style={d(reduce ? 0 : 3200, reduce)}>
        <path d="M28 16 q2 -2 4 0 q2 -2 4 0 M50 11 q1.8 -1.8 3.6 0 q1.8 -1.8 3.6 0" {...sw(1.3)}>
          {!reduce && (
            <animateTransform attributeName="transform" type="translate" from="0 0" to="8 -3"
              begin="3.4s" dur="2s" fill="freeze" />
          )}
        </path>
      </g>
      <Label x="40" y="27" at="2.8" reduce={reduce}>아담</Label>
      <Label x="80" y="10" at="1.4" reduce={reduce}>에덴동산</Label>
    </g>
  )
}

// 타락 (창 3:6-7)
function AdamFallScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M10 44 q12 -7 24 -2" {...sw(1.1, 0.4)} />
      </g>
      {/* 선악과 나무 + 감긴 뱀 — 핵심 */}
      <g style={d(700, reduce)}>
        <path d="M62 54 q-1 -13 -2 -22" {...sw(2.6)} />
        <path d="M60 32 q-12 -2 -13 -11 q9 -3 13 3 q1 -9 8 -10 q5 4 3 11 q9 -3 12 4 q-4 9 -14 7 q-4 2 -9 -4" {...sw(2)} />
        <path d="M61 52 q-4 -3 -1 -7 q4 -3 1 -7 q-3 -3 0 -6" {...sw(1.8)} />
        <path d="M61 32 q2 -1.5 3.5 0.5" {...sw(1.4)} />
        <circle cx="55" cy="26" r="1.5" {...sw(1.4)} />
        <circle cx="70" cy="24" r="1.5" {...sw(1.4)} />
      </g>
      {/* 하와·아담 — 주역: 손 뻗음 */}
      <g style={d(1700, reduce)}>
        <circle cx="38" cy="38" r="2.8" {...sw(2.5)} />
        <path d="M38 40.8 v7.7 M35.5 54 l2.5 -5.5 l2.5 5.5 M40.5 42 q5 -2.5 9.5 -6" {...sw(2.5)} />
        <circle cx="88" cy="39" r="2.8" {...sw(2.2)} />
        <path d="M88 41.8 v7.2 M85.5 54 l2.5 -5 l2.5 5 M85.5 43 q-6 -3 -10.5 -7" {...sw(2.2)} />
      </g>
      {/* 열매 떨어짐 — SMIL */}
      {!reduce && (
        <circle cx="63" cy="28" r="1.6" {...sw(2.2)} style={d(2700, false)}>
          <animateMotion path="M0 0 q-2 8 -5 12" begin="2.9s" dur="0.6s" fill="freeze"
            calcMode="spline" keySplines="0.4 0 0.8 1" keyTimes="0;1" />
        </circle>
      )}
      {reduce && <circle cx="58" cy="40" r="1.6" {...sw(2.2)} />}
      <Label x="52" y="16" at="1.5" reduce={reduce}>뱀</Label>
      <Label x="38" y="29" at="2.3" reduce={reduce}>하와</Label>
      <Label x="88" y="30" at="2.3" reduce={reduce}>아담</Label>
    </g>
  )
}

// 에덴 추방 (창 3:23-24)
function AdamExpelledScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M84 54 v-20 M104 54 v-20 M84 34 q10 -8 20 0" {...sw(2.2)} />
        <path d="M88 40 h3 m6 0 h3 M90 46 h8" {...sw(1.2, 0.5)} />
      </g>
      {/* 화염검 — 핵심: 교차 검 + 불꽃, 흔들림 */}
      <g style={d(1000, reduce)}>
        <path d="M89 46 L99 30 M99 46 L89 30" {...sw(2.8)} />
        <path d="M92 26 q-2 -4 0 -7 q2 3 0 7 M96 26 q-1.6 -4.5 0.6 -7.5" {...sw(2)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="rotate"
            values="0 94 38; 4 94 38; -4 94 38; 0 94 38" keyTimes="0;0.3;0.7;1"
            begin="2.2s" dur="1.1s" repeatCount="2" />
        )}
      </g>
      {/* 떠나는 두 사람 — 주역: 고개 숙이고 왼쪽으로 */}
      <g transform={reduce ? 'translate(-8 0)' : undefined} style={d(2000, reduce)}>
        <circle cx="46" cy="38.5" r="2.8" {...sw(2.5)} />
        <path d="M45 41 q-1.5 5.5 -2 12 M42 54 l3.5 -6 M48.5 53 l-2.5 -5.5" {...sw(2.5)} />
        <circle cx="56" cy="39.5" r="2.6" {...sw(2.2)} />
        <path d="M55 42 q-1.5 5 -2 11 M52.5 54 l3 -5.5 M58 53 l-2 -5" {...sw(2.2)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="translate" from="0 0" to="-14 0"
            begin="2.6s" dur="2s" fill="freeze" calcMode="spline" keySplines="0.3 0 0.7 1" keyTimes="0;1" />
        )}
      </g>
      <Label x="94" y="22" at="1.6" reduce={reduce}>화염검</Label>
      <Label x="38" y="30" at="2.5" reduce={reduce}>아담과 하와</Label>
    </g>
  )
}

// 아벨의 제사 (창 4:4)
function AbelOfferingScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M84 44 q13 -8 26 -2" {...sw(1.1, 0.4)} />
      </g>
      {/* 제단 + 향연 — 핵심 */}
      <g style={d(700, reduce)}>
        <path d="M52 54 v-7 h16 v7 M50 47 h20" {...sw(2.2)} />
        <path d="M54 51 h3 m4 0 h3 M56 48.8 h3" {...sw(1.2, 0.55)} />
        <path d="M58 44.5 q-2.5 -4 0 -7 q2.5 3 0 7 M62 44.5 q-2 -4.5 0.5 -7.5" {...sw(2.6)} />
        <path d="M61 36 q-3 -4 0 -8 q3 -3 1.5 -7 M63.5 34 q-2 -3.5 0 -7" {...sw(1.3, 0.6)} />
      </g>
      {/* 아벨 — 주역: 무릎 꿇음 */}
      <g style={d(1600, reduce)}>
        <circle cx="34" cy="41" r="2.8" {...sw(2.5)} />
        <path d="M34 43.8 l-1.5 5.2 M27.5 54 h10 M32.8 49 q-3.5 1.8 -5 5 M33 46 q4 0.5 6.5 2.5" {...sw(2.5)} />
      </g>
      {/* 양 — 보조 */}
      <g style={d(2300, reduce)}>
        <path d="M84 51 q0 -4.5 5.5 -4.5 q5.5 0 5.5 4.5 q0 3 -5.5 3 q-5.5 0 -5.5 -3" {...sw(1.8)} />
        <circle cx="96.5" cy="47.5" r="2.1" {...sw(1.8)} />
        <path d="M86 54 v-1 M92.5 54 v-1" {...sw(1.3)} />
        <path d="M86.5 49 q1.8 1.4 3.6 0" {...sw(1.1, 0.5)} />
      </g>
      {/* 열납의 빛 */}
      <g style={d(reduce ? 0 : 3200, reduce)} stroke="var(--paper-accent)">
        <path d="M60 18 v-4 M52 21 l-2.6 -2.6 M68 21 l2.6 -2.6" {...sw(1.4)} />
      </g>
      <Label x="34" y="32" at="2.1" reduce={reduce}>아벨</Label>
      <Label x="60" y="24" at="1.3" reduce={reduce}>열납된 제물</Label>
    </g>
  )
}

// 가인이 아벨을 죽임 (창 4:8)
function CainKillsAbelScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M14 54 v-6 M14 48 q-3 -1 -4 -4 q4 0 4 4 M20 54 v-5 M20 49 q3 -1 4 -4 q-4 0 -4 4" {...sw(1.2, 0.5)} />
        <path d="M100 54 v-6 M100 48 q-3 -1 -4 -4 q4 0 4 4" {...sw(1.2, 0.5)} />
        <path d="M8 20 q14 5 26 3 M86 18 q14 4 26 7" {...sw(1.1, 0.35)} />
      </g>
      {/* 쓰러진 아벨 — 보조 */}
      <g style={d(1000, reduce)}>
        <circle cx="74" cy="50" r="2.6" {...sw(2)} />
        <path d="M71.5 51 q-8 2 -16 1.5 M55 52.5 l-6 1" {...sw(2)} />
      </g>
      {/* 가인 — 주역: 팔 늘어뜨리고 서 있음, 고개 떨굼 */}
      <g transform={reduce ? 'rotate(6 40 47)' : undefined} style={d(1800, reduce)}>
        <circle cx="40" cy="36.5" r="2.9" {...sw(2.5)} />
        <path d="M40 39.4 v8 M37 54 l3 -6.5 l3 6.5" {...sw(2.5)} />
        <path d="M40 41 q-3.5 2 -4.5 6.5 M40 41 q3.5 2 4.5 6.5" {...sw(2.2)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="rotate" from="0 40 47" to="6 40 47"
            begin="2.8s" dur="0.8s" fill="freeze" />
        )}
      </g>
      <Label x="40" y="28" at="2.3" reduce={reduce}>가인</Label>
      <Label x="72" y="42" at="1.5" reduce={reduce}>아벨</Label>
    </g>
  )
}

// 놋 땅 거주 (창 4:16)
function CainNodScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M6 45 q20 -6 40 -3 M70 41 q22 -5 44 -1" {...sw(1.1, 0.4)} />
      </g>
      {/* 지는 해 — 내려앉음 */}
      <g transform={reduce ? 'translate(0 3)' : undefined} style={d(900, reduce)}>
        <path d="M18 54 a8 8 0 0 1 16 0" {...sw(2.2)} />
        <path d="M26 42.5 v-2.5 M16 47 l-2 -2 M36 47 l2 -2" {...sw(1.2, 0.6)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="translate" from="0 0" to="0 3"
            begin="2s" dur="2.4s" fill="freeze" />
        )}
      </g>
      {/* 떠나는 가인 — 주역: 보따리 지팡이, 동쪽으로 */}
      <g transform={reduce ? 'translate(12 0)' : undefined} style={d(1800, reduce)}>
        <circle cx="66" cy="37" r="2.9" {...sw(2.5)} />
        <path d="M66 39.9 v7.6 M63 54 l3 -6.5 M70 53.5 l-3 -6" {...sw(2.5)} />
        <path d="M68.5 41 l6 -3 M74.5 38 l2.5 3 q2 -3 -0.5 -5" {...sw(2)} />
        <path d="M64 41.5 l-4.5 9" {...sw(1.6)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="translate" from="0 0" to="14 0"
            begin="2.6s" dur="2.2s" fill="freeze" calcMode="spline" keySplines="0.3 0 0.7 1" keyTimes="0;1" />
        )}
      </g>
      {/* 발자국 점선 */}
      <g style={d(reduce ? 0 : 3600, reduce)}>
        <path d="M48 52 h2 m4 0.6 h2 m4 0.6 h2" {...sw(1.2, 0.55)} />
      </g>
      <Label x="66" y="28" at="2.4" reduce={reduce}>가인</Label>
      <Label x="104" y="36" at="1.2" reduce={reduce}>놋 땅, 에덴 동편</Label>
    </g>
  )
}

// 에노스 — 여호와의 이름을 부름 (창 4:26)
function SethEnoshScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M20 14 v2.6 m-1.3 -1.3 h2.6 M96 10 v2.6 m-1.3 -1.3 h2.6 M106 20 v2 m-1 -1 h2" {...sw(1.2, 0.6)} />
      </g>
      {/* 제단 + 향연 */}
      <g style={d(800, reduce)}>
        <path d="M52 54 v-6 h14 v6 M50 48 h18" {...sw(2.2)} />
        <path d="M58 44.5 q-2 -3.5 0 -6.5 q2 2.5 0 6.5" {...sw(2.4)} />
        <path d="M59 37 q-2.5 -3.5 0 -7 q2.5 -3 1 -6" {...sw(1.3, 0.6)} />
      </g>
      {/* 셋과 에노스 — 주역: 팔을 하늘로 */}
      <g style={d(1700, reduce)}>
        <circle cx="32" cy="34" r="3" {...sw(2.5)} />
        <path d="M32 37 v9.5 M29 54 l3 -7 l3 7" {...sw(2.5)} />
        <path d="M32 39 q-4 -4 -4.5 -8.5 M32 39 q4 -4 4.5 -8.5" {...sw(2.3)} />
        <circle cx="42" cy="39" r="2.4" {...sw(2)} />
        <path d="M42 41.4 v6 M39.8 54 l2.2 -6 l2.2 6" {...sw(2)} />
        <path d="M42 43 q-3 -3 -3.5 -6.5 M42 43 q3 -3 3.5 -6.5" {...sw(1.8)} />
      </g>
      <g style={d(reduce ? 0 : 3000, reduce)} stroke="var(--paper-accent)">
        <path d="M59 22 v-4 M52 25 l-2.4 -2.4 M66 25 l2.4 -2.4" {...sw(1.4)} />
      </g>
      <Label x="30" y="24" at="2.2" reduce={reduce}>셋과 에노스</Label>
      <Label x="59" y="60" at="1.2" reduce={reduce} size="4.2">여호와의 이름을 부르다</Label>
    </g>
  )
}

// 에녹의 승천 (창 5:24)
function EnochTakenScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M6 54 L60 30 L88 20" {...sw(1.4, 0.6)} strokeDasharray="3 2.4" />
        <path d="M14 50 l1 -2 l1 2 M40 44 l0.9 -1.8 l0.9 1.8" {...sw(1.1, 0.45)} />
      </g>
      {/* 하늘 문 — 구름 + 빛 */}
      <g style={d(1000, reduce)}>
        <path d="M84 16 q2 -6 9 -5 q3 -4 8 -2 q6 -1 7 4 q4 2 1 6 q-5 3 -12 2 q-8 1 -13 -5" {...sw(1.6)} />
        <path d="M94 24 v3 M87 22 l-2 2.4 M101 22 l2 2.4" stroke="var(--paper-accent)" {...sw(1.4)} />
      </g>
      {/* 에녹 — 주역: 경사로를 올라 사라짐 */}
      <g transform={reduce ? 'translate(26 -12)' : undefined} opacity={reduce ? 0.45 : 1} style={d(1800, reduce)}>
        <circle cx="52" cy="30" r="2.8" {...sw(2.5)} />
        <path d="M52 32.8 v7.2 M49.5 45 l2.5 -5.5 M55 44.5 l-2.5 -5" {...sw(2.5)} />
        <path d="M54 35 l4.5 -2.5" {...sw(2)} />
        {!reduce && (
          <>
            <animateTransform attributeName="transform" type="translate" from="0 0" to="26 -12"
              begin="2.6s" dur="2s" fill="freeze" calcMode="spline" keySplines="0.35 0 0.6 1" keyTimes="0;1" />
            <animate attributeName="opacity" from="1" to="0.35" begin="3.6s" dur="1s" fill="freeze" />
          </>
        )}
      </g>
      <Label x="46" y="21" at="2.3" reduce={reduce}>에녹</Label>
      <Label x="95" y="34" at="1.4" reduce={reduce} size="4.2">하나님과 동행</Label>
    </g>
  )
}

// 의인 노아 (창 6:8-9)
function NoahRighteousScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
      </g>
      {/* 타락한 군상 — 원경: 기울고 흐트러진 실루엣들 */}
      <g style={d(800, reduce)}>
        <path d="M18 54 l4 -8 M22 46 q3 -1 4 2 M26 54 l-2 -6" {...sw(1.3, 0.45)} />
        <circle cx="23" cy="43.5" r="2" {...sw(1.3, 0.45)} />
        <path d="M94 54 l-4 -7.5 M90 46.5 q-3 -0.5 -4 2 M86 54 l2 -5.5" {...sw(1.3, 0.45)} />
        <circle cx="91" cy="44" r="2" {...sw(1.3, 0.45)} />
        <path d="M34 54 l2.5 -5 M104 54 l-2.5 -5" {...sw(1.2, 0.4)} />
      </g>
      {/* 노아 — 주역: 곧게 선 실루엣 */}
      <g style={d(1800, reduce)}>
        <circle cx="60" cy="32" r="3.2" {...sw(2.6)} />
        <path d="M60 35.2 v11 M56.5 54 l3.5 -8 l3.5 8" {...sw(2.6)} />
        <path d="M60 38 q-4 1 -5.5 4.5 M60 38 q4 1 5.5 4.5" {...sw(2.3)} />
        <path d="M58 42.5 q2 1.2 4 0" {...sw(1.3, 0.6)} />
      </g>
      {/* 은혜의 빛 — 한 줄기 */}
      <g style={d(reduce ? 0 : 3000, reduce)} stroke="var(--paper-accent)">
        <path d="M60 22 v-8 M54 24 l-3.5 -3.5 M66 24 l3.5 -3.5" {...sw(1.6)} />
      </g>
      <Label x="60" y="60" at="2.3" reduce={reduce}>노아</Label>
      <Label x="24" y="34" at="1.3" reduce={reduce} size="4.2">타락한 세대</Label>
    </g>
  )
}

// 대홍수 시작 (창 7:11-16)
function FloodBeginsScene({ reduce }) {
  return (
    <g>
      {/* 방주 — 핵심 */}
      <g style={d(0, reduce)}>
        <path d="M28 48 q2 6 8 6 h48 q6 0 8 -6 l-4 -10 h-56 z" {...sw(2.6)} />
        <path d="M40 38 v-8 h40 v8" {...sw(2.2)} />
        <path d="M46 34 h4 m8 0 h4 m8 0 h4" {...sw(1.3)} />
        <path d="M32 44 h56" {...sw(1.2, 0.5)} />
      </g>
      {/* 문 닫힘 — 늦게 그려짐 */}
      <g style={d(2400, reduce)}>
        <path d="M58 48 v-7 h8 v7 M58 44.5 h8" {...sw(2.2)} />
      </g>
      {/* 빗줄기 — 반복 깜빡임 */}
      <g style={d(1200, reduce)}>
        <path d="M16 8 l-3 8 M34 6 l-3 8 M56 5 l-3 8 M78 6 l-3 8 M100 8 l-3 8 M24 18 l-3 8 M46 16 l-3 8 M68 15 l-3 8 M90 17 l-3 8" {...sw(1.3, 0.7)}>
          {!reduce && <animate attributeName="opacity" values="0.7;0.35;0.7" begin="2.2s" dur="0.9s" repeatCount="3" />}
        </path>
      </g>
      {/* 물결 상승 — SMIL */}
      <g transform={reduce ? 'translate(0 -4)' : undefined} style={d(1800, reduce)}>
        <path d="M6 58 q6 -2.5 12 0 q6 -2.5 12 0 q6 -2.5 12 0 q6 -2.5 12 0 q6 -2.5 12 0 q6 -2.5 12 0 q6 -2.5 12 0 q6 -2.5 12 0 q6 -2.5 12 0" {...sw(2)} />
        <path d="M14 62 q6 -2.5 12 0 q6 -2.5 12 0 q6 -2.5 12 0 q6 -2.5 12 0 q6 -2.5 12 0 q6 -2.5 12 0 q6 -2.5 12 0" {...sw(1.4, 0.6)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="translate" from="0 0" to="0 -4"
            begin="2.6s" dur="2s" fill="freeze" />
        )}
      </g>
      <Label x="62" y="24" at="1" reduce={reduce}>방주</Label>
      <Label x="63" y="55" at="3" reduce={reduce} size="4.2">여호와께서 문을 닫으시다</Label>
    </g>
  )
}

// 아라랏 산 (창 8:4,11)
function ArkAraratScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M18 54 L48 26 L66 38 L92 18 L114 34" {...sw(2.2)} />
        <path d="M40 34 l4 -3.5 M86 24 l4 -3" {...sw(1.2, 0.4)} />
      </g>
      {/* 방주 — 봉우리에 얹힘(기울어짐) */}
      <g style={d(1000, reduce)}>
        <g transform="rotate(-8 92 22)">
          <path d="M78 24 q1 4 5 4 h20 q4 0 5 -4 l-2 -6 h-26 z" {...sw(2.4)} />
          <path d="M84 18 v-4 h16 v4" {...sw(1.8)} />
        </g>
      </g>
      {/* 비둘기 — 감람잎 물고 날아옴 */}
      <g style={d(2200, reduce)}>
        <g transform={reduce ? 'translate(-38 12)' : undefined}>
          <path d="M96 8 q2.5 -2.5 5 0 q2.5 -2.5 5 0" {...sw(1.8)} />
          <path d="M101 9 l3 2 q2.5 0 3.5 1.5" {...sw(1.4)} />
          {!reduce && (
            <animateTransform attributeName="transform" type="translate" from="0 0" to="-38 12"
              begin="2.5s" dur="1.6s" fill="freeze" calcMode="spline" keySplines="0.3 0 0.6 1" keyTimes="0;1" />
          )}
        </g>
      </g>
      <Label x="92" y="34" at="1.4" reduce={reduce}>아라랏 산</Label>
      <Label x="46" y="14" at="3.6" reduce={reduce}>감람잎 문 비둘기</Label>
    </g>
  )
}

// 무지개 언약 (창 9:13-17)
function RainbowCovenantScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M90 54 q1 3 4 3 h12 q3 0 4 -3 l-1.5 -4 h-17 z" {...sw(1.4, 0.55)} />
      </g>
      {/* 제단 + 가족 */}
      <g style={d(800, reduce)}>
        <path d="M24 54 v-6 h13 v6 M22 48 h17" {...sw(2.2)} />
        <path d="M29.5 44.5 q-2 -3.5 0 -6.5 q2 2.5 0 6.5" {...sw(2.2)} />
      </g>
      <g style={d(1600, reduce)}>
        <circle cx="52" cy="38" r="2.9" {...sw(2.5)} />
        <path d="M52 40.9 v6.6 M49 54 l3 -6.5 l3 6.5 M52 42.5 q-3.5 -3 -4 -7 M52 42.5 q3.5 -3 4 -7" {...sw(2.5)} />
        <circle cx="63" cy="41" r="2.4" {...sw(2)} />
        <path d="M63 43.4 v5.1 M60.8 54 l2.2 -5.5 l2.2 5.5" {...sw(2)} />
        <circle cx="72" cy="43" r="2" {...sw(1.8)} />
        <path d="M72 45 v4 M70.2 54 l1.8 -5 l1.8 5" {...sw(1.8)} />
      </g>
      {/* 무지개 — 핵심(강조색 3중 아치) */}
      <g style={d(reduce ? 0 : 2800, reduce)} stroke="var(--paper-accent)">
        <path d="M14 40 q46 -44 92 0" {...sw(2.4)} />
        <path d="M20 42 q40 -38 80 0" {...sw(1.7, 0.75)} />
        <path d="M26 44 q34 -32 68 0" {...sw(1.2, 0.5)} />
      </g>
      <Label x="52" y="29" at="2.1" reduce={reduce}>노아의 가족</Label>
      <Label x="60" y="12" at="3.4" reduce={reduce}>언약의 무지개</Label>
    </g>
  )
}

// 사람의 창조 (창 1:27, 2:7)
function AdamCreationScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M6 50 q20 -3 38 0 q22 -4 40 0 q18 -3 30 0" {...sw(1.1, 0.4)} />
      </g>
      {/* 흙 형체 — 아직 사람이 아닌 흙무더기 */}
      <g style={d(700, reduce)}>
        <path d="M48 54 q0 -8 12 -9 q12 1 12 9 q-6 3 -12 3 q-6 0 -12 -3" {...sw(2)} />
        <path d="M52 52 q2 -1 4 0 M64 51 q2 -1 4 0 M58 47.5 q2 -1 4 0" {...sw(1.3, 0.5)} />
      </g>
      {/* 생기 — 핵심: 위에서 내려오는 숨 */}
      <g style={d(1400, reduce)} stroke="var(--paper-accent)">
        <path d="M60 8 v16 M54 13 l3 8 M66 13 l-3 8" {...sw(1.6)} />
        {!reduce && <animate attributeName="opacity" values="0.35;1;0.6;1" begin="2.4s" dur="1s" fill="freeze" />}
      </g>
      {/* 사람이 되어 일어섬 — 주역 */}
      <g style={d(2200, reduce)}>
        <g transform={reduce ? undefined : 'translate(0 4)'}>
          <circle cx="55" cy="36" r="3" {...sw(2.6)} />
          <path d="M55 39 v9 M52 54 l3 -6.5 l3 6.5" {...sw(2.6)} />
          <path d="M55 41 q-3 1 -4.5 4 M55 41 q3 1 4.5 4" {...sw(2.2)} />
          {!reduce && (
            <animateTransform attributeName="transform" type="translate" from="0 4" to="0 0"
              begin="2.6s" dur="1s" fill="freeze" calcMode="spline" keySplines="0.3 0 0.7 1" keyTimes="0;1" />
          )}
        </g>
      </g>
      {/* 하나님의 형상 — 남자와 여자에게 함께 */}
      <g style={d(2800, reduce)}>
        <circle cx="76" cy="38" r="2.6" {...sw(2.2)} />
        <path d="M76 40.6 v7.8 M73.2 54 l2.8 -5.6 l2.8 5.6" {...sw(2.2)} />
        <g stroke="var(--paper-accent)">
          <path d="M49 32 q6 -4 12 0" {...sw(1.3)} />
          <path d="M70.5 34.5 q5.5 -3.2 11 0" {...sw(1.3)} />
        </g>
      </g>
      <Label x="55" y="27" at="2.6" reduce={reduce}>아담</Label>
      <Label x="63" y="14" at="3.4" reduce={reduce} size="4.2">하나님의 형상</Label>
    </g>
  )
}

// 하와를 창조하시고 아담과 만나게 하심 (창 2:21-23)
function AdamMeetsEveScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M8 54 v-7 M8 47 q-3 -1 -4 -4 q4 0 4 4 M100 54 v-8 M100 46 q3 -1.5 4 -5 q-4 0.5 -4 5" {...sw(1.3, 0.5)} />
      </g>
      {/* 깊이 잠든 아담 — 갈빗대를 취하심 */}
      <g transform={reduce ? undefined : 'rotate(-72 23 52)'} style={d(700, reduce)}>
        <circle cx="26" cy="42" r="2.8" {...sw(2.5)} />
        <path d="M26 44.8 v8.5 M23 54 l3 -6 l3 6 M26 46 q5 -1 9 -3" {...sw(2.5)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="rotate" from="-72 23 52" to="0 23 52"
            begin="3s" dur="1.2s" fill="freeze" calcMode="spline" keySplines="0.3 0 0.7 1" keyTimes="0;1" />
        )}
      </g>
      {/* 갈빗대 자리의 빛 */}
      <g style={d(1400, reduce)} stroke="var(--paper-accent)">
        <path d="M30 44 q3 -2 6 0" {...sw(1.3)} />
      </g>
      {/* 하와 — 주역: 일어섬 */}
      <g style={d(2200, reduce)}>
        <g transform={reduce ? undefined : 'translate(0 4)'}>
          <circle cx="45" cy="38" r="2.9" {...sw(2.6)} />
          <path d="M45 40.9 v9 M42 54 l3 -6.5 l3 6.5 M45 42.5 q-3.5 -2 -4.5 -5" {...sw(2.6)} />
          {!reduce && (
            <animateTransform attributeName="transform" type="translate" from="0 4" to="0 0"
              begin="2.6s" dur="1s" fill="freeze" calcMode="spline" keySplines="0.3 0 0.7 1" keyTimes="0;1" />
          )}
        </g>
      </g>
      <Label x="24" y="33" at="3.6" reduce={reduce}>아담</Label>
      <Label x="45" y="29" at="2.6" reduce={reduce}>하와</Label>
      <Label x="60" y="61" at="3.8" reduce={reduce} size="4.2">동행으로 지어진 사람</Label>
    </g>
  )
}

// 가인의 제사가 열납되지 못함 (창 4:5-7)
function CainOfferingRejectedScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M10 46 q14 -6 28 -2" {...sw(1.1, 0.4)} />
      </g>
      {/* 제단 + 곡식 제물 — 향연이 흩어짐 */}
      <g style={d(700, reduce)}>
        <path d="M50 54 v-7 h16 v7 M48 47 h20" {...sw(2.2)} />
        <path d="M54 44.5 h3 m4 0 h3" {...sw(1.6)} />
        <path d="M58 44.5 q-1.5 -3 -3.5 -4 M62 44.5 q1.5 -3 3.5 -4" {...sw(1.4, 0.55)}>
          {!reduce && <animate attributeName="opacity" values="0.55;0.2;0.4" begin="2s" dur="1.4s" repeatCount="2" />}
        </path>
      </g>
      {/* 가인 — 주역: 안색이 변하여 고개 떨굼 */}
      <g style={d(1600, reduce)}>
        <circle cx="34" cy="42" r="2.8" {...sw(2.5)} />
        <path d="M34.5 44.8 l1 5.2 M28 54 h11 M32.5 47.5 q-4 1 -5.5 4.5 M35.5 47 q4 1 5 4.5" {...sw(2.5)} />
      </g>
      {/* 죄가 문에 엎드림 */}
      <g style={d(2300, reduce)}>
        <path d="M92 54 v-16 M108 54 v-16 M92 38 h16" {...sw(1.8)} />
        <path d="M96 53 q6 -2.5 10 0 q-2 -3.5 -5 -3.5 q-3 0 -5 3.5" {...sw(1.4, 0.6)} />
      </g>
      <Label x="34" y="34" at="2.4" reduce={reduce}>가인</Label>
      <Label x="100" y="30" at="3" reduce={reduce} size="4.2">죄가 문에 엎드리다</Label>
    </g>
  )
}

// 가인이 저주받고 표를 받음 (창 4:10-15)
function CainCursedScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M40 54 l4 -3 l-2 -3 l5 -2.5" {...sw(1.4, 0.6)} />
      </g>
      {/* 땅에서 호소하는 핏자국 */}
      <g style={d(700, reduce)}>
        <path d="M42 54 l1.5 -2.5 M46 54 l-1.5 -2.5 M50 54 l1 -2" {...sw(1.3, 0.55)}>
          {!reduce && <animate attributeName="opacity" values="0.55;0.85;0.55" begin="1.8s" dur="1.2s" repeatCount="2" />}
        </path>
      </g>
      {/* 가인 — 주역: 저주받아 고개 숙임 */}
      <g style={d(1500, reduce)}>
        <circle cx="60" cy="35" r="2.9" {...sw(2.5)} />
        <path d="M60.5 37.8 l1 6.2 M54 54 l7 -10 M67 54 l-6.5 -10" {...sw(2.5)} />
        <path d="M58.5 39 q-3.5 1 -5 4" {...sw(2.2)} />
      </g>
      {/* 보호의 표 — 심판 속의 긍휼 */}
      <g style={d(2400, reduce)} stroke="var(--paper-accent)">
        <circle cx="60" cy="34" r="0.7" {...sw(1.8)} />
        <path d="M56.5 30 q3.5 -2.5 7 0" {...sw(1.3)} />
      </g>
      <Label x="60" y="26" at="2.7" reduce={reduce}>가인</Label>
      <Label x="60" y="61" at="3.2" reduce={reduce} size="4.2">저주와 보호의 표</Label>
    </g>
  )
}

// 에녹 성을 쌓음 (창 4:17)
function CainCityScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
      </g>
      {/* 성벽과 망대 — 원경 */}
      <g style={d(700, reduce)}>
        <path d="M50 54 v-16 h34 v16 M50 42 h6 m6 0 h6 m6 0 h6" {...sw(2)} />
        <path d="M56 38 v-4 h4 v4 M76 38 v-4 h4 v4" {...sw(1.6)} />
        <path d="M18 54 v-8 h8 v8 M96 54 v-9 h9 v9" {...sw(1.3, 0.55)} />
      </g>
      {/* 성문 */}
      <g style={d(1400, reduce)}>
        <path d="M62 54 v-8 h8 v8" {...sw(1.8)} />
      </g>
      {/* 돌 쌓는 사람 — 주역 */}
      <g style={d(2200, reduce)}>
        <circle cx="38" cy="42" r="2.8" {...sw(2.5)} />
        <path d="M38 44.8 v9 M35 54 l3 -6.5 l3 6.5 M38 46 q4 -1 7 -3.5" {...sw(2.5)} />
      </g>
      {/* 돌 하나가 벽으로 놓임 — SMIL */}
      {!reduce && (
        <path d="M44 40 h2.4 v2.4 h-2.4 z" {...sw(1.6)} style={d(2900, false)}>
          <animateMotion path="M0 0 l6 -2" begin="3.1s" dur="0.6s" fill="freeze" />
        </path>
      )}
      {reduce && <path d="M50 38 h2.4 v2.4 h-2.4 z" {...sw(1.6)} />}
      <Label x="38" y="33" at="2.6" reduce={reduce}>가인</Label>
      <Label x="67" y="60" at="3.4" reduce={reduce} size="4.2">에녹 성</Label>
    </g>
  )
}

// 셋의 출생 — 다른 씨 (창 4:25)
function SethBirthScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
      </g>
      {/* 아벨의 무덤 — 원경, 흐릿하게 */}
      <g style={d(700, reduce)}>
        <path d="M14 54 q0 -3.5 5 -3.5 q5 0 5 3.5" {...sw(1.3, 0.4)} />
        <path d="M19 50.5 v-3" {...sw(1.1, 0.4)} />
      </g>
      {/* 어머니 — 주역: 아기를 안음 */}
      <g style={d(1600, reduce)}>
        <circle cx="55" cy="34" r="3" {...sw(2.6)} />
        <path d="M55 37 v10 M51.5 54 l3.5 -7 l3.5 7 M55 39 q-4 1 -6 4 M55 39 q4 1 6 4" {...sw(2.6)} />
      </g>
      {/* 아기 셋 — 작게, 안겨서 */}
      <g style={d(2300, reduce)}>
        <g transform={reduce ? undefined : 'translate(0 3)'}>
          <circle cx="55" cy="42" r="1.6" {...sw(2)} />
          {!reduce && (
            <animateTransform attributeName="transform" type="translate" from="0 3" to="0 0"
              begin="2.7s" dur="0.9s" fill="freeze" />
          )}
        </g>
      </g>
      {/* 다시 이어진 희망의 빛 */}
      <g style={d(reduce ? 0 : 3200, reduce)} stroke="var(--paper-accent)">
        <path d="M55 24 v-5 M49 27 l-3 -3 M61 27 l3 -3" {...sw(1.4)} />
      </g>
      <Label x="55" y="25" at="2.3" reduce={reduce}>셋</Label>
      <Label x="19" y="45" at="0.8" reduce={reduce} size="4.2">아벨</Label>
    </g>
  )
}

// 에녹이 하나님과 동행함 (창 5:22-24)
function EnochWalksScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
      </g>
      {/* 반복되는 계보 — 낳고 죽었더라 */}
      <g style={d(700, reduce)}>
        <circle cx="16" cy="49" r="1.6" {...sw(1.3, 0.4)} />
        <path d="M16 50.6 v3.4 M14 54 l2 -1.5 l2 1.5" {...sw(1.3, 0.4)} />
        <circle cx="26" cy="49" r="1.6" {...sw(1.3, 0.4)} />
        <path d="M26 50.6 v3.4 M24 54 l2 -1.5 l2 1.5" {...sw(1.3, 0.4)} />
        <circle cx="100" cy="49" r="1.6" {...sw(1.3, 0.4)} />
        <path d="M100 50.6 v3.4 M98 54 l2 -1.5 l2 1.5" {...sw(1.3, 0.4)} />
      </g>
      {/* 에녹 + 동행하는 빛 — 주역 */}
      <g style={d(1800, reduce)}>
        <g transform={reduce ? 'translate(10 0)' : undefined}>
          <circle cx="52" cy="36" r="3" {...sw(2.6)} />
          <path d="M52 39 v9.5 M48.5 54 l3.5 -6.5 l3.5 6.5 M52 41 q4 -1 6.5 -3.5" {...sw(2.6)} />
          <path d="M60 44 v-16" stroke="var(--paper-accent)" {...sw(1.6)} />
          {!reduce && (
            <animateTransform attributeName="transform" type="translate" from="0 0" to="10 0"
              begin="2.6s" dur="2.2s" fill="freeze" calcMode="spline" keySplines="0.3 0 0.7 1" keyTimes="0;1" />
          )}
        </g>
      </g>
      <Label x="52" y="27" at="2.2" reduce={reduce}>에녹</Label>
      <Label x="60" y="24" at="1.5" reduce={reduce} size="4.2">하나님과 동행</Label>
    </g>
  )
}

// 아담의 죽음 (창 5:5)
function AdamDeathScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
      </g>
      {/* 늙은 아담 — 주역, 쓰러짐 */}
      <g transform={reduce ? 'rotate(78 40 54)' : undefined} style={d(900, reduce)}>
        <circle cx="40" cy="34" r="3" {...sw(2.6)} />
        <path d="M40 37 v10 M36.5 54 l3.5 -7 l3.5 7" {...sw(2.6)} />
        <path d="M38 40 q1.5 1 3 0" {...sw(1.3, 0.5)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="rotate" from="0 40 54" to="78 40 54"
            begin="2.4s" dur="1.4s" fill="freeze" calcMode="spline" keySplines="0.4 0 0.7 1" keyTimes="0;1" />
        )}
      </g>
      {/* 흙으로 돌아감 — 무덤 흙 */}
      <g style={d(2600, reduce)}>
        <path d="M20 54 q0 -6 12 -6.5 q12 0.5 12 6.5" {...sw(1.8)} />
      </g>
      {/* 죽었더라 — 반복되는 후렴 */}
      <g style={d(reduce ? 0 : 3400, reduce)}>
        <path d="M70 54 v-3 M74 54 v-3 M78 54 v-3" {...sw(1.2, 0.5)} />
      </g>
      <Label x="40" y="26" at="2.2" reduce={reduce}>아담</Label>
      <Label x="26" y="45" at="3.1" reduce={reduce} size="4.2">930년, 흙으로 돌아가다</Label>
    </g>
  )
}

// 방주를 지으라는 명령과 순종 (창 6:14-22)
function NoahArkCommandScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
      </g>
      {/* 방주 골조 — 아직 미완 */}
      <g style={d(700, reduce)}>
        <path d="M40 54 h50" {...sw(2.2)} />
        <path d="M46 54 v-10 M56 54 v-13 M66 54 v-13 M76 54 v-10" {...sw(1.8)} />
        <path d="M46 44 h30" {...sw(1.4, 0.6)} />
      </g>
      {/* 노아 — 주역: 못을 박음 */}
      <g style={d(1700, reduce)}>
        <circle cx="30" cy="41" r="2.8" {...sw(2.5)} />
        <path d="M30 43.8 v8 M27 54 l3 -6 l3 6 M32.5 45 q3.5 -0.5 6 1.5" {...sw(2.5)} />
      </g>
      {/* 망치질 — SMIL */}
      {!reduce && (
        <path d="M40 45 l3.5 -2.5" {...sw(1.8)} style={d(2400, false)}>
          <animateTransform attributeName="transform" type="rotate" values="0 40 45;-20 40 45;0 40 45"
            begin="2.7s" dur="0.5s" repeatCount="3" />
        </path>
      )}
      {reduce && <path d="M40 45 l3.5 -2.5" {...sw(1.8)} />}
      <Label x="30" y="32" at="2.1" reduce={reduce}>노아</Label>
      <Label x="65" y="60" at="1" reduce={reduce} size="4.2">명하신 대로 준행하다</Label>
    </g>
  )
}

// 방주에서 나와 제단을 쌓음 (창 8:20-21)
function NoahAltarScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M86 54 q2 5 8 5 h14 q6 0 8 -5 l-3 -8 h-24 z" {...sw(1.8, 0.6)} />
        <path d="M94 46 v-1" {...sw(1.4, 0.5)} />
      </g>
      {/* 노아 — 주역: 방주를 나섬 */}
      <g style={d(1200, reduce)}>
        <g transform={reduce ? 'translate(-14 0)' : undefined}>
          <circle cx="76" cy="41" r="2.8" {...sw(2.5)} />
          <path d="M76 43.8 v8 M73 54 l3 -6 l3 6" {...sw(2.5)} />
          {!reduce && (
            <animateTransform attributeName="transform" type="translate" from="0 0" to="-14 0"
              begin="2.4s" dur="1.8s" fill="freeze" calcMode="spline" keySplines="0.3 0 0.7 1" keyTimes="0;1" />
          )}
        </g>
      </g>
      {/* 제단 — 핵심 */}
      <g style={d(2000, reduce)}>
        <path d="M40 54 v-7 h16 v7 M38 47 h20" {...sw(2.4)} />
      </g>
      {/* 번제 향기 — 핵심(강조색) */}
      <g style={d(2700, reduce)} stroke="var(--paper-accent)">
        <path d="M46 43 q-2.5 -4 0 -7 q2.5 3 0 7 M50 43 q-2 -4.5 0.5 -7.5" {...sw(2.4)} />
        <path d="M49 34 q-3 -4 0 -8 q3 -3 1.5 -6.5" {...sw(1.3, 0.6)}>
          {!reduce && <animate attributeName="opacity" values="0.6;1;0.6" begin="3s" dur="1.4s" repeatCount="2" />}
        </path>
      </g>
      <Label x="62" y="59" at="2.3" reduce={reduce}>노아</Label>
      <Label x="47" y="14" at="3.4" reduce={reduce} size="4.2">다시는 저주하지 않으리라</Label>
    </g>
  )
}

// 노아의 포도원과 아들들의 상반된 반응 (창 9:20-27)
function NoahVineyardScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
      </g>
      {/* 포도원 — 원경 */}
      <g style={d(700, reduce)}>
        <path d="M10 54 v-14 M10 42 q4 -1 4 -5 q4 0 4 5 M10 46 q-4 -1 -4 -5 q-4 0 -4 5" {...sw(1.8, 0.6)} />
        <circle cx="12" cy="36" r="1" {...sw(1.4, 0.5)} />
        <circle cx="14.5" cy="38" r="1" {...sw(1.4, 0.5)} />
      </g>
      {/* 취하여 쓰러진 노아 */}
      <g transform={reduce ? 'rotate(80 55 54)' : undefined} style={d(1600, reduce)}>
        <circle cx="55" cy="34" r="2.9" {...sw(2.5)} />
        <path d="M55 36.9 v9.5 M51.5 54 l3.5 -7.5 l3.5 7.5" {...sw(2.5)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="rotate" from="0 55 54" to="80 55 54"
            begin="2.6s" dur="1.2s" fill="freeze" calcMode="spline" keySplines="0.4 0 0.7 1" keyTimes="0;1" />
        )}
      </g>
      {/* 아들 — 얼굴 돌리고 옷을 덮어줌 */}
      <g style={d(2400, reduce)}>
        <circle cx="88" cy="40" r="2.6" {...sw(2.2)} />
        <path d="M88 42.6 v7.4 M85.2 54 l2.8 -5.5 l2.8 5.5 M85.5 44 q-6 0 -10 2.5" {...sw(2.2)} />
      </g>
      <Label x="55" y="27" at="2.4" reduce={reduce}>노아</Label>
      <Label x="88" y="32" at="3" reduce={reduce} size="4.2">축복과 저주로 갈리다</Label>
    </g>
  )
}

const SCENES = {
  'authored-adam-creation': { Scene: AdamCreationScene, desc: '흙에 생기를 불어넣어 사람을 지으시다', caption: '사람의 창조 — 창세기 1-2장' },
  'authored-adam-placed-in-eden': { Scene: AdamEdenScene, desc: '하나님이 지으신 동산에 아담을 두시다', caption: '에덴동산 — 창세기 2장' },
  'authored-adam-meets-eve': { Scene: AdamMeetsEveScene, desc: '갈빗대로 하와를 지으시고 아담과 만나게 하시다', caption: '돕는 배필 — 창세기 2장' },
  'authored-adam-fall': { Scene: AdamFallScene, mood: 'dark', desc: '뱀의 꾐에 넘어가 금단의 열매를 먹다', caption: '타락 — 창세기 3장' },
  'authored-adam-expelled-from-eden': { Scene: AdamExpelledScene, mood: 'dark', desc: '그룹과 화염검이 에덴으로 가는 길을 막다', caption: '추방 — 창세기 3장' },
  'authored-abel-offering': { Scene: AbelOfferingScene, desc: '양의 첫 새끼 제물을 하나님이 받으시다', caption: '아벨의 제사 — 창세기 4장' },
  'authored-cain-offering-rejected': { Scene: CainOfferingRejectedScene, desc: '가인의 제물이 열납되지 못하고 안색이 변하다', caption: '열납되지 못한 제사 — 창세기 4장' },
  'authored-cain-kills-abel': { Scene: CainKillsAbelScene, mood: 'dark', desc: '가인이 들에서 아우 아벨을 쳐죽이다', caption: '첫 살인 — 창세기 4장' },
  'authored-cain-cursed-and-marked': { Scene: CainCursedScene, mood: 'dark', desc: '가인이 저주받으나 보호의 표를 받다', caption: '저주와 표 — 창세기 4장' },
  'authored-cain-dwells-in-nod': { Scene: CainNodScene, mood: 'dark', desc: '하나님 앞을 떠나 에덴 동편 놋 땅으로 가다', caption: '유리하는 자 — 창세기 4장' },
  'authored-cain-builds-city-of-enoch': { Scene: CainCityScene, mood: 'dark', desc: '유리하는 자가 자기 이름으로 성을 쌓다', caption: '에녹 성 — 창세기 4장' },
  'authored-seth-birth': { Scene: SethBirthScene, desc: '아벨의 피 위에 다른 씨 셋이 주어지다', caption: '다른 씨 — 창세기 4장' },
  'authored-seth-enosh-and-calling': { Scene: SethEnoshScene, desc: '사람들이 비로소 여호와의 이름을 부르다', caption: '예배의 시작 — 창세기 4장' },
  'authored-enoch-walked-with-god': { Scene: EnochWalksScene, desc: '낳고 죽었더라는 후렴 속에 300년을 동행하다', caption: '동행 — 창세기 5장' },
  'authored-adam-death': { Scene: AdamDeathScene, mood: 'dark', desc: '930년을 살고 흙으로 돌아가다', caption: '아담의 죽음 — 창세기 5장' },
  'authored-enoch-taken-by-god': { Scene: EnochTakenScene, desc: '하나님과 동행하다 죽음을 보지 않고 옮겨지다', caption: '에녹 — 창세기 5장' },
  'authored-noah-righteous-man': { Scene: NoahRighteousScene, desc: '타락한 세대 가운데 홀로 은혜를 입다', caption: '의인 노아 — 창세기 6장' },
  'authored-noah-ark-command': { Scene: NoahArkCommandScene, desc: '명하신 대로 방주를 지어 순종하다', caption: '방주 건조 — 창세기 6장' },
  'authored-noah-flood-begins': { Scene: FloodBeginsScene, mood: 'dark', desc: '하늘의 창들이 열리고 여호와께서 문을 닫으시다', caption: '대홍수 — 창세기 7장' },
  'authored-noah-ark-rests-ararat': { Scene: ArkAraratScene, desc: '비둘기가 감람 새 잎사귀를 물고 돌아오다', caption: '아라랏 산 — 창세기 8장' },
  'authored-noah-leaves-ark-altar': { Scene: NoahAltarScene, desc: '방주에서 나와 제단을 쌓고 번제를 드리다', caption: '첫 제단 — 창세기 8장' },
  'authored-noah-rainbow-covenant': { Scene: RainbowCovenantScene, desc: '다시는 홍수로 멸하지 않으리라 — 언약의 표징', caption: '무지개 언약 — 창세기 9장' },
  'authored-noah-vineyard': { Scene: NoahVineyardScene, mood: 'dark', desc: '포도주에 취해 벗은 노아, 아들들의 상반된 반응', caption: '노아의 포도원 — 창세기 9장' },
}

export default SCENES
