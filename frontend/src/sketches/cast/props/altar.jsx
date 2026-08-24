// 지물 참고 도상 — 제단(Altar). task#307 S5, ADR 260823-190821 2항.
//
// 이 파일은 컴포넌트가 아니라 **참고 도판**이다. 장면은 이 파일을 import하지 않는다 — 저작자가
// `#/cast`에서 보고 손으로 그린다(A안, ADR 2항). 벧엘·모리아·갈멜산의 제단, 성막 놋제단, 아덴의
// "알지 못하는 신" 제단은 서로 다른 개체이므로 복붙 컴포넌트로 만들면 각 장면이 부정확해진다 —
// 그래서 여기 있는 건 "이 좌표를 베끼라"가 아니라 "이 비례로 그리라"는 뜻이다.
//
// 전거(이미 저작된 기존 장면들의 공통분모를 뽑았다 — 참고 도상이 허공에서 나오지 않았다):
//   patriarchsCovenant.jsx  ShechemPromiseScene(세겜) · BethelReturnScene(벧엘)
//   creationToFlood.jsx     NoahAltarScene(방주 직후 첫 제단)
//   elijahAndElisha.jsx     CarmelContestScene(갈멜산)
//   exodusToConquest.jsx    EbalCovenantScene(에발산) · BaalPeorScene(브올, 배교)
//   theEarlyChurch.jsx      AthensScene(아덴, "알지 못하는 신에게")
//
// ── 지물 어휘 형식 정본(이 주석이 그 틀이다 — 추가 README 없음, eco) ─────────────
// 다음 지물(성문 5모듈·장막 5·나무·배·우물)을 추가할 때도 이 틀을 그대로 따른다:
//
//   1. 위치·이름   `cast/props/<영문 소문자>.jsx`. 기본 내보내기는 **prop 없는** 컴포넌트다
//                  (cx·cy·scale·delay 계약 없음 — 인물 정본과 다르다. 매 장면이 다른 개체이므로
//                  재배치할 이유가 없다).
//   2. 상단 주석   (a) 무엇을 그리는가 (b) 전거 — 이 지물이 실제 등장한 기존 장면 목록(위 참조)
//                  (c) 공통 골격의 비례 (d) 변형 예시 목록과 그 변형이 대응하는 축.
//   3. 치수 표기   좌표를 복사하라는 뜻이 아니다(개체가 다르다는 게 이 어휘의 존재 이유다) —
//                  그려진 실제 좌표에서 유도한 **비례 문장**으로 캡션에 적는다(예: "폭:높이 ≈
//                  2.5:1", "상판은 몸통보다 폭의 10%만큼 돌출"). 그 비례가 실제로 어떻게 나오는지
//                  보여주는 치수선(끝 틱 + 숫자)은 **공통 골격 판 한 장에만** 붙인다 — 변형 판마다
//                  반복하면 판이 지저분해지고 어차피 같은 비례다.
//   4. 배치        가로로 나란한 패널들(공통 골격 1 + 변형 N). 패널마다 **자체** `<svg viewBox="0 0
//                  64 64" fill="none" stroke="currentColor" .../>`를 갖는다 — `CastSheet.jsx`의
//                  `PropCard`는 `<Comp/>`를 그대로 꽂을 뿐 감싸주지 않는다(인물 정본용 `CastCard`와
//                  다르다). 패널 아래 HTML 캡션 한 줄(무엇의 변형인지 + 성경 근거).
//   5. 굵기 언어    lib.jsx의 `sw()` 위계를 그대로 쓴다(구조 ≥2.0 · 질감 1.1~1.4 · 강조는
//                  `var(--paper-accent)`) — 정지 도판이라도 장면과 같은 굵기 언어를 쓰면 장면
//                  안에 들어갔을 때와 똑같이 읽힌다. `d()`/붓질 단계는 쓰지 않는다(정지 시트,
//                  애니메이션 없음 — `render_scene.py --cast`가 이미 그렇게 촬영한다).
//   6. 게이트 비대상 `cast/props/*.jsx`는 B1~B12 어디에도 걸리지 않는다(디렉터리 열거 제외,
//                  `validate_scene_sketch_detail.py` 주석 참조) — 검증기를 통과시키려 애쓰지 말 것,
//                  애초에 안 본다.
//
// 이 파일 자체가 위 형식의 실행 예다. 공통 골격 1판 + 변형 3판(향연 유무 · 곡식/번제 · 돌/놋)을
// 담는다.
// ─────────────────────────────────────────────────────────────────────────────
import { sw } from '../../lib'

const PANEL = {
  display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4,
  flexShrink: 0, width: 'clamp(84px, 28vw, 160px)',
}
const SVG_BASE = {
  width: '100%', height: 'auto', aspectRatio: '1 / 1', display: 'block',
  background: 'var(--bg-2)', borderRadius: 6,
}
const CAPTION = { fontSize: 11, color: 'var(--ink-faint)', textAlign: 'center', lineHeight: 1.35 }

// 공통 지면선 — 네 패널이 공유(y=50, x 6~58).
function Ground() {
  return <path d="M6 50 h52" {...sw(1.4, 0.5)} />
}

// 공통 골격: 단 + 상판(돌 쌓기). 박스 폭20×높이8(약 2.5:1) · 상판 폭24(양쪽 2단위, 10%씩 돌출).
function Skeleton() {
  return (
    <>
      <Ground />
      <path d="M20 50 v-8 h20 v8" {...sw(2.4)} />
      <path d="M18 42 h24" {...sw(2.2)} />
      {/* 돌 쌓기 결(질감) */}
      <path d="M23 46 h2.5 m3.5 0 h2.5 m3.5 0 h2.5" {...sw(1.2, 0.5)} />
      {/* 치수선 — 폭 */}
      <path d="M18 37 v2 M42 37 v2 M18 38 h24" {...sw(1.1, 0.55)} />
      <text x="30" y="35" fontSize="3.4" textAnchor="middle" fill="var(--ink-faint)" stroke="none">24</text>
      {/* 치수선 — 높이(박스 폭 20) */}
      <path d="M45 42 h2 M45 50 h2 M46 42 v8" {...sw(1.1, 0.55)} />
      <text x="50" y="47" fontSize="3.4" textAnchor="middle" fill="var(--ink-faint)" stroke="none">8</text>
    </>
  )
}

// 변형 1 — 번제 + 향연(창 8장 노아 · 왕상 18장 갈멜): 상판 위로 연기가 오른다(강조색).
function BurntWithSmoke() {
  return (
    <>
      <Ground />
      <path d="M20 50 v-8 h20 v8" {...sw(2.4)} />
      <path d="M18 42 h24" {...sw(2.2)} />
      <path d="M23 46 h2.5 m3.5 0 h2.5 m3.5 0 h2.5" {...sw(1.2, 0.5)} />
      <path d="M26 42 q-2 -8 1 -14 q3 6 0 14" {...sw(1.3, 0.6)} stroke="var(--paper-accent)" />
      <path d="M34 42 q2.4 -9 -1 -15" {...sw(1.2, 0.5)} stroke="var(--paper-accent)" />
    </>
  )
}

// 변형 2 — 곡식 제물, 향연 없음(창 4장 가인): 상판에 곡식 더미, 연기 없음.
function GrainOffering() {
  return (
    <>
      <Ground />
      <path d="M20 50 v-8 h20 v8" {...sw(2.4)} />
      <path d="M18 42 h24" {...sw(2.2)} />
      <path d="M23 46 h2.5 m3.5 0 h2.5 m3.5 0 h2.5" {...sw(1.2, 0.5)} />
      <path d="M25 42 q3 -3 6 0" {...sw(1.8)} />
      <path d="M31 42 q3 -3 6 0" {...sw(1.8)} />
    </>
  )
}

// 변형 3 — 돌/놋: 놋 제단(뿔), 출 27장 성막 번제단. 폭:높이 ≈ 1.5:1(공통 골격 2.5:1보다 곧다) ·
// 돌 결(끊긴 짧은 선) 대신 놋 판금 띠(이어진 가로 띠) · 위쪽 두 모서리에 뿔(위로 말려 올라간 짧은 획).
function BronzeHorned() {
  return (
    <>
      <Ground />
      <path d="M18 50 v-16 h24 v16" {...sw(2.6)} />
      <path d="M18 34 q-1 -3.5 2 -4 M42 34 q1 -3.5 -2 -4" {...sw(2.2)} />
      <path d="M21 40 h18 M21 45 h18" {...sw(1.3, 0.55)} />
    </>
  )
}

function Panel({ title, children }) {
  return (
    <div style={PANEL}>
      <svg viewBox="0 0 64 64" style={SVG_BASE} fill="none" stroke="currentColor"
        strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        {children}
      </svg>
      <div style={CAPTION}>{title}</div>
    </div>
  )
}

export default function Altar() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      <div style={{ fontSize: 12, color: 'var(--ink-faint)', maxWidth: '55ch' }}>
        제단 — 공통 골격(단·돌쌓기·비례) + 변형 3종(향연 유무 · 곡식/번제 · 돌/놋).
        비례는 참고용이다 — 장면마다 실제 좌표는 다르게 그린다(개체가 다르다).
      </div>
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
        <Panel title="공통 골격 — 폭:높이 ≈ 2.5:1, 상판 돌출 10%">
          <Skeleton />
        </Panel>
        <Panel title="번제 + 향연 — 창 8장(노아) · 왕상 18장(갈멜)">
          <BurntWithSmoke />
        </Panel>
        <Panel title="곡식 제물 — 향연 없음(창 4장, 가인)">
          <GrainOffering />
        </Panel>
        <Panel title="돌/놋 — 놋 제단(뿔), 출 27장">
          <BronzeHorned />
        </Panel>
      </div>
    </div>
  )
}
