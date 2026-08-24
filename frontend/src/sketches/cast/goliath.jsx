// 인물 정본 — 골리앗(Goliath)의 머리 (task#314 S2, ADR 260824-075708).
//
// 그리는 것: 머리 윤곽(원) + 투구(돔+볼가림 두 쪽)뿐이다. 머리카락·수염은 없다 — 투구가 머리
// 전체를 덮어 GoliathScene 소스에 머리카락 표지가 전혀 없었고(davidUnitedKingdom.jsx 원본
// 서 있는 자세), 성경 본문(삼상 17장)도 머리카락을 규정하지 않는다. 없는 값을 임의로 지어내지
// 않고 "없음"으로 정본화한다. 이목구비(눈썹·눈·입)는 슬롯으로 비운다 — 표정은 서사이므로
// 장면이 그린다(cast/david.jsx와 동일 원칙, lib.jsx "얼굴" 절).
//
// 호출 규약(lib.jsx "정본 컴포넌트 규약" 절 정본)은 cast/david.jsx 헤더 주석을 그대로 따른다 —
// 호출부는 cx·cy·scale·delay 숫자 리터럴만, 컴포넌트 내부 transform·조건 분기 금지, 좌표 계약
// (절대 anchor = cx+로컬x*scale, 상대 델타 = 로컬 델타*scale, 반지름도 동일), stroke-width는
// scale로 곱하지 않는다(sw(2.6)처럼 리터럴 그대로 — _SW 정규식이 리터럴만 읽는다).
//
// 규격
//   머리 지름(scale=1) = 8.4단위(반지름 4.2) — GoliathScene 쓰러진 자세 머리 원
//     (davidUnitedKingdom.jsx `circle cx="79" cy="26" r="4.2"`, 이미 승인된 기준점)에서 그대로
//     파생했다(ADR 260823-221839 결정①). lib.jsx "머리 반지름 ≥4단위" 하한을 충족한다.
//   로컬 좌표 원점(0,0) = GoliathScene 서 있는 자세의 투구 폭 중심·머리 세로 중심
//     (원래 절대좌표 cx=103.5, cy=19 — 투구 돔 밑변 중점(103.5,15.3)과 볼가림 끝(y22.5)의 중간).
//     서 있는 자세 호출부는 이 값 그대로 cx={103.5} cy={19} scale={1}을 써야 원본과 같은 픽셀이 나온다.
//   소비 단계 수(STEPS) = 2, 간격(STEP_GAP) = 120ms(B2 단계당 3선 상한을 지킨 최소 분할 — 원 1+
//     돔 1을 1단계, 볼가림 2를 다음 단계).
//     ⇒ 이 머리 다음에 이어 그릴 요소의 delay는 호출 delay + 2*120 = delay + 240부터 잡는다.
//   strokes = 4(머리 윤곽 원 1 + 투구 돔 1 + 볼가림 2). 전부 구조 선(굵기 ≥2.0)이다.
//
// 5축(task#314 S1 NEEDS.md 결정, S2 확정): 머리카락 없음(투구가 전체를 덮음) · 수염 없음 ·
// 머리쓰개 투구 · 나이대 성인 · 성별 남. 다윗(곱슬머리·맨머리·소년/청년)과 머리카락·머리쓰개·
// 나이대 세 축에서부터 갈려 구별성 1단(5축 조합 겹침 0)을 충족한다
// (scripts/check_cast_axes.py가 기계로 단정 — scripts/check.sh에 배선돼 있다).
//
// reduce 미지원(의도적, eco): cast/david.jsx와 동일 이유 — 호출 규약이 숫자 리터럴 4개로 못박혀
// reduce를 prop으로 받을 수 없고, index.css의 prefers-reduced-motion 미디어쿼리가 이미
// animation-delay를 전역 0으로 덮어써 접근성 요구가 CSS 레벨에서 충족된다. SMIL도 없다.
import { sw, d } from '../lib'

export const aliases = ['골리앗']
export const STEPS = 2
export const STEP_GAP = 120
export const HEAD_DIAMETER = 8.4
export const AXES = { hair: '없음', beard: '없음', headwear: '투구', age: '성인', sex: '남' }

// BRIEF — 2층 얼굴 레퍼런스 생성용 한 줄 개요(근거·경계는 cast/david.jsx의 같은 절 참조).
// 장면 소스 주석 「얼굴 — 위협(눈썹을 아래로 모은다)」(davidUnitedKingdom.jsx:162)과 삼상 17:4의
// 거인 전사에서 파생. 5축에 「거인」·「위협」을 담을 자리가 없어 골리앗 후보 4장이 전부 빈 타원으로
// 나왔다(사용자 UAT 2026-08-24) — 그 공백을 메우는 입력이다.
export const BRIEF = 'fierce giant warrior with heavy brow and hard jaw'

export default function Goliath({ cx, cy, scale, delay }) {
  return (
    <>
      {/* 머리 윤곽(원) + 투구 돔(구조) */}
      <g style={d(delay + 0 * STEP_GAP, false)}>
        <circle cx={cx + 0 * scale} cy={cy + 0 * scale} r={4.2 * scale} {...sw(2.6)} />
        <path d={`M${cx + -5.5 * scale} ${cy + -3.7 * scale} q${5.5 * scale} ${-5 * scale} ${11 * scale} 0`} {...sw(2.6)} />
      </g>
      {/* 투구 볼가림 두 쪽 */}
      <g style={d(delay + 1 * STEP_GAP, false)}>
        <path d={`M${cx + -5.5 * scale} ${cy + -3.7 * scale} l${-0.8 * scale} ${7.2 * scale}`} {...sw(2.2)} />
        <path d={`M${cx + 5.5 * scale} ${cy + -3.7 * scale} l${0.8 * scale} ${7.2 * scale}`} {...sw(2.2)} />
      </g>
    </>
  )
}
