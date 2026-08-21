// 인트로 오프닝 몽타주 전용 소형 모듈 (task#287).
//
// 몽타주 5씬은 **서로 다른 5개 투어 모듈**에 있었다. 투어별 청크 분할만 하면 인트로가 청크 5개를
// 끌어와(밀도 상향 후 ~650KB) 첫 화면이 무거워진다 — 그래서 그 5씬의 **정의를 여기로 옮기고**,
// 각 투어 모듈이 자기 레지스트리를 위해 여기서 되가져간다.
//
// **의존 방향이 이 파일의 존재 이유다.** 처음엔 반대로(여기서 투어 모듈을 재수출) 만들었는데,
// 빌드가 INEFFECTIVE_DYNAMIC_IMPORT로 거부하며 5개 모듈을 전부 메인 청크에 병합했다(260KB).
// 소형 모듈이 무거운 모듈을 참조하면 분할이 무효가 된다 — 참조는 무거운 쪽 → 가벼운 쪽이어야 한다.
//
// 인트로는 reduce로 정적 렌더하므로 desc·caption을 쓰지 않는다 — Scene만 담아 메타데이터를
// 두 곳에 두지 않는다(사본은 언젠가 어긋난다). 그림의 정본 소속은 여전히 각 투어 레지스트리다(ADR-0029).
import { sw, d } from './lib'
import { Label } from './SceneLabel'

// 사람의 창조 (창 1:27, 2:7)
export function AdamCreationScene({ reduce }) {
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

// 떨기나무 (출 3:1-12)
export function BurningBushScene({ reduce }) {
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

// 베들레헴 기름부음 (삼상 16:12-13)
export function BethlehemAnointingScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
        <path d="M82 44 q14 -8 28 -2" {...sw(1.1, 0.4)} />
        <path d="M16 53 l1 -2 l1 2 M46 53.2 l0.8 -1.6 l0.8 1.6" {...sw(1.1, 0.45)} />
      </g>
      {/* 사무엘 — 보조(이 장면의 주역은 다윗과 뿔병) */}
      <g style={d(700, reduce)}>
        <circle cx="32" cy="27" r="3.4" {...sw(2.2)} />
        <path d="M27 54 l2.5 -20.5 h5 l2.5 20.5 M27 54 h10" {...sw(2.2)} />
        <path d="M30.5 38 q0.5 7.5 0 13 M33.5 38 q0.4 7.5 0 13" {...sw(1.3, 0.55)} />
        <path d="M35.5 36 q9 -5 16 -4" {...sw(2)} />
      </g>
      {/* 다윗 — 주역 */}
      <g style={d(1500, reduce)}>
        <circle cx="58" cy="40" r="2.8" {...sw(2.5)} />
        <path d="M58 42.8 v6.7 M55.5 54 l2.5 -4.5 l2.5 4.5" {...sw(2.5)} />
        <path d="M56.4 45.5 q1.6 1 3.2 0" {...sw(1.3, 0.6)} />
        <path d="M64 54 l0.5 -10 q0 -2.5 2.5 -2" {...sw(1.4)} />
        <path d="M74 51.5 q0 -3.5 4.5 -3.5 q4.5 0 4.5 3.5 q0 2.5 -4.5 2.5 q-4.5 0 -4.5 -2.5 M83.5 49.5 h2.5" {...sw(1.4, 0.7)} />
        <path d="M75.5 54 v-0.8 M81 54 v-0.8" {...sw(1.2, 0.6)} />
      </g>
      {/* 뿔병 — 핵심 */}
      <g transform={reduce ? 'rotate(-30 52 31)' : undefined} style={d(2400, reduce)}>
        <path d="M52 31 q4 -3.5 9 -2 l-0.5 2.5 q-4.5 -1 -8.5 1.5" {...sw(2.8)} />
        <path d="M59.5 29.6 l1.2 0.4" {...sw(1.4)} />
        {!reduce && (
          <animateTransform attributeName="transform" type="rotate" from="0 52 31" to="-30 52 31"
            begin="2.8s" dur="0.5s" fill="freeze" />
        )}
      </g>
      <g style={d(reduce ? 0 : 3400, reduce)}>
        <path d="M56.5 32 v2 M58 35 v2" {...sw(1.4)} />
      </g>
      <g style={d(reduce ? 0 : 4000, reduce)} stroke="var(--paper-accent)">
        <path d="M58 20 v-4 M49 23 l-3 -3 M67 23 l3 -3 M53 21 l-1.6 -2.6 M63 21 l1.6 -2.6" {...sw(1.4)} />
      </g>
      <Label x="32" y="18" at="1.5" reduce={reduce}>사무엘</Label><Label x="60" y="60" at="2.3" reduce={reduce}>다윗</Label><Label x="70" y="27" at="3.5" reduce={reduce} anchor="start">기름 뿔</Label>
    </g>
  )
}

// 베들레헴 탄생 (눅 2:1-7)
export function BethlehemBirthScene({ reduce }) {
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

// 오순절 (행 2:14-41)
export function PentecostScene({ reduce }) {
  return (
    <g>
      <g style={d(0, reduce)}>
        <path d="M6 54 h108" {...sw(1.6)} />
      </g>
      {/* 모인 무리 */}
      <g style={d(900, reduce)}>
        <circle cx="36" cy="42" r="2.4" {...sw(2)} />
        <path d="M36 44.4 v5.6 M34 54 l2 -4 l2 4" {...sw(2)} />
        <circle cx="50" cy="40.5" r="2.5" {...sw(2.2)} />
        <path d="M50 43 v7 M48 54 l2 -4 l2 4" {...sw(2.2)} />
        <circle cx="64" cy="41" r="2.5" {...sw(2.2)} />
        <path d="M64 43.5 v6.5 M62 54 l2 -4 l2 4" {...sw(2.2)} />
        <circle cx="78" cy="42.5" r="2.4" {...sw(2)} />
        <path d="M78 44.9 v5.1 M76 54 l2 -4 l2 4" {...sw(2)} />
      </g>
      {/* 불의 혀 — 각 사람 위에 */}
      <g style={d(1900, reduce)} stroke="var(--paper-accent)">
        <path d="M36 34 q-1.6 -3 0 -5.5 q1.6 2.5 0 5.5 M50 32 q-1.6 -3 0 -5.5 q1.6 2.5 0 5.5 M64 32.5 q-1.6 -3 0 -5.5 q1.6 2.5 0 5.5 M78 34.5 q-1.6 -3 0 -5.5 q1.6 2.5 0 5.5" {...sw(2.2)}>
          {!reduce && <animate attributeName="opacity" values="1;0.55;1" begin="2.6s" dur="1.2s" repeatCount="2" />}
        </path>
      </g>
      {/* 바람 */}
      <g style={d(2600, reduce)}>
        <path d="M14 18 q6 -2.5 12 0 M90 16 q6 -2.5 12 0 M20 12 q5 -2 10 0" {...sw(1.3, 0.5)} />
      </g>
      <Label x="57" y="16" at="2.2" reduce={reduce}>불의 혀같이</Label>
      <Label x="60" y="61" at="3" reduce={reduce} size="4.2">오순절에 성령이 임하시다</Label>
    </g>
  )
}

const INTRO_SCENES = {
  'authored-adam-creation': { Scene: AdamCreationScene },
  'authored-moses-burning-bush': { Scene: BurningBushScene },
  'authored-samuel-bethlehem-david-anointing': { Scene: BethlehemAnointingScene },
  'authored-jesus-bethlehem-birth': { Scene: BethlehemBirthScene },
  'authored-peter-pentecost': { Scene: PentecostScene },
}

export default INTRO_SCENES
