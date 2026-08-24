// 인물 정본 — 다윗(David)의 머리 (task#307 S2, ADR 260823-190821 1항).
//
// 그리는 것: 머리 윤곽(원) + 곱슬머리 실루엣뿐이다. 수염·머리쓰개는 없다 — GoliathScene
// (task#227/#303, 재작도 완료)이 이미 세운 다윗의 모습(맨머리·무수염 곱슬머리)을 그대로
// 정본화했다(기존 12건 등장 전부 이 모습). 이목구비(눈·코·입·눈썹)는 슬롯으로 비운다 —
// 표정은 서사이므로 장면이 그린다(ADR 260823-190821 1항, lib.jsx "얼굴" 절).
//
// 호출 규약(lib.jsx "정본 컴포넌트 규약" 절 정본) — S3가 이 소스를 정적으로 읽어 인라인
// 전개한다. 호출부는 cx·cy·scale·delay 숫자 리터럴만 쓴다(표현식·변수·transform 금지).
// 이 파일 내부도 조건 분기가 없다. 좌표 계약:
//   절대 anchor(M)      = cx + 로컬x*scale, cy + 로컬y*scale
//   상대 명령(q/l)의 델타 = 로컬 델타 * scale (평행이동 없이 크기만)
//   반지름도 동일하게 * scale — scale 프롭이 실제 크기를 바꾸지 않으면 프롭 자체가 무의미하다.
// ⇒ 이후 S3 파서는 소스에서 `cx + N * scale` / `cy + N * scale` / `N * scale` 리터럴 패턴의
//   N만 뽑으면 로컬 좌표를 복원할 수 있다.
//
// stroke-width는 scale로 곱하지 않는다(sw(2.6)처럼 리터럴 그대로) — 두 이유. (1) 기존/향후
// 검증기의 굵기 판정(`_SW` 정규식, B7·B11)이 `sw(<리터럴 숫자>)` 형태를 그대로 읽는다.
// `sw(2.6 * scale)`처럼 식을 쓰면 그 정규식이 못 읽어 구조 선이 조용히 미분류된다 — 좌표
// 계약(위)이 명시적으로 다루는 건 x·y·반지름뿐, 굵기는 아니다. (2) 작게 그릴수록 선이
// 상대적으로 굵어지는 쪽이 실제로 더 읽힌다(광학 보정 — 아이콘 시스템이 흔히 쓰는 원칙).
// 원경 배율에서 실루엣이 사라지지 않고 버틴 것도 이 고정폭 덕분이다(재작도 메모 참조).
//
// 규격
//   머리 지름(scale=1) = 8단위(반지름 4 — lib.jsx "얼굴" 절 "머리 반지름 ≥4단위"를 충족해
//     장면이 이 위에 이목구비를 얹을 수 있다). lib.jsx 신체 조립 규칙 "머리 지름 = 어깨 폭의
//     0.45~0.6배"를 적용하면 scale=1 몸의 어깨 폭은 13.3~17.8단위가 맞다.
//   소비 단계 수(STEPS) = 3, 간격(STEP_GAP) = 120ms(B2 단계당 3선 상한을 지킨 최소 분할).
//     ⇒ 이 머리 다음에 이어 그릴 요소의 delay는 호출 delay + 3*120 = delay + 360부터 잡는다.
//   strokes = 8(원 1 + 머리카락 7). 구조 선(굵기 ≥2.0)은 원 1 + 곱슬 윤곽 1 = 2개 — 나머지 몫은
//     몸에서 채워 B7(≥12개)을 맞춘다.
//
// 재작도 메모(1차 실패, 2026-08-23): 처음엔 GoliathScene의 다윗 머리(몸통 맥락 안에서 가는
// 텍스처 선 8가닥으로 곱슬을 흩뿌린 버전)를 그대로 정본화했다 — 몸 없이 머리만 격리하면
// 그 가는 선들이 뭉쳐 "눈썹 두 개"처럼 읽히고, 배율 0.45에서는 거의 소실됐다(원경 실루엣 붕괴).
// 원인: 얇은 텍스처 선(굵기 1.1~1.4)은 "부가 디테일"이지 "실루엣"이 아니다 — 실루엣은 구조
// 선(≥2.0)이 져야 하고, 그 실루엣이 사라지면 얇은 선을 아무리 더해도 사람으로 안 읽힌다.
// 지금 버전은 머리 위로 3봉우리 파도선(곱슬 윤곽, 구조 선)을 한 획으로 그려 배율이 줄어도
// 살아남게 하고, 가는 텍스처는 "주역" 근접 배율에서만 보이는 장식으로 남긴다.
//
// ⚠ 목표 밀도 확정 시(task#305/#304 미결) 이 정본의 stroke 수·굵기는 재개정 대상이다.
//
// reduce 미지원(의도적, eco): 호출 규약이 숫자 리터럴 4개로 못박혀 reduce(불리언 변수 참조)를
// prop으로 받을 수 없다. index.css의 prefers-reduced-motion 미디어쿼리가 모든 요소의
// animation-delay를 전역 !important 0으로 덮어써 실제 접근성 요구는 이미 충족되고, 이 컴포넌트엔
// <animate>류 SMIL이 없어 reduce 분기가 필요한 대상 자체가 없다.
import { sw, d } from '../lib'

export const aliases = ['다윗']
export const STEPS = 3
export const STEP_GAP = 120
export const HEAD_DIAMETER = 8
// 5축(task#314 S1 NEEDS.md, S2 확정) — 골리앗(cast/goliath.jsx)과 구별성 대조 대상.
export const AXES = { hair: '곱슬머리', beard: '없음', headwear: '없음', age: '소년/청년', sex: '남' }

// BRIEF — 2층 얼굴 레퍼런스 생성용 한 줄 개요. 5축은 **구별**을 위한 것이라(ADR 260824-075708 ②)
// 「목동 소년」처럼 그 인물을 그리는 데 필요한 성질을 담는 축이 없다. 장면 소스 주석에서 파생한다
// — GoliathScene 다윗의 「얼굴 — 결의(눈썹을 살짝 모아 집중한 표정)」(davidUnitedKingdom.jsx)와
// 삼상 17장의 목동. 1층 SVG는 여전히 이목구비를 그리지 않는다(ADR 260823-190821 1항 유지) —
// 이 문자열은 SVG가 아니라 2층 래스터 후보의 프롬프트로만 나간다.
export const BRIEF = 'lean-faced shepherd with calm steady eyes'

export default function David({ cx, cy, scale, delay }) {
  return (
    <>
      {/* 머리 윤곽(구조) + 3봉우리 곱슬 윤곽(구조, 배율이 줄어도 실루엣을 지킨다) + 왼쪽 관자놀이 곱슬 */}
      <g style={d(delay + 0 * STEP_GAP, false)}>
        <circle cx={cx + 0 * scale} cy={cy + 0 * scale} r={4 * scale} {...sw(2.6)} />
        <path d={`M${cx + -3.4 * scale} ${cy + -2.3 * scale} Q${cx + -2.8 * scale} ${cy + -6 * scale} ${cx + -1.1 * scale} ${cy + -3.2 * scale} Q${cx + 0 * scale} ${cy + -6.2 * scale} ${cx + 1.3 * scale} ${cy + -3.3 * scale} Q${cx + 2.4 * scale} ${cy + -5.8 * scale} ${cx + 3.4 * scale} ${cy + -2.3 * scale}`} {...sw(2.2)} />
        <path d={`M${cx + -3.4 * scale} ${cy + -2.3 * scale} q${-1.2 * scale} ${0.8 * scale} ${-1 * scale} ${2.4 * scale}`} {...sw(1.3, 0.7)} />
      </g>
      {/* 오른쪽 관자놀이 곱슬 + 정수리 봉우리 아래 텍스처 2가닥(근접 배율 전용 장식) */}
      <g style={d(delay + 1 * STEP_GAP, false)}>
        <path d={`M${cx + 3.4 * scale} ${cy + -2.3 * scale} q${1.2 * scale} ${0.8 * scale} ${1 * scale} ${2.4 * scale}`} {...sw(1.3, 0.7)} />
        <path d={`M${cx + -2.2 * scale} ${cy + -3.6 * scale} q${0.6 * scale} ${0.7 * scale} 0 ${1.3 * scale}`} {...sw(1.1)} />
        <path d={`M${cx + 0.1 * scale} ${cy + -3.9 * scale} q${0.6 * scale} ${0.7 * scale} 0 ${1.3 * scale}`} {...sw(1.1)} />
      </g>
      {/* 마지막 텍스처 2가닥 */}
      <g style={d(delay + 2 * STEP_GAP, false)}>
        <path d={`M${cx + 2.3 * scale} ${cy + -3.6 * scale} q${-0.6 * scale} ${0.7 * scale} 0 ${1.3 * scale}`} {...sw(1.1)} />
        <path d={`M${cx + -0.1 * scale} ${cy + -6.2 * scale} q${0.4 * scale} ${-0.6 * scale} ${0.9 * scale} ${-0.3 * scale}`} {...sw(1.1)} />
      </g>
    </>
  )
}
