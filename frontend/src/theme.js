// 노드 타입 → 색·한글 라벨 — 검색·SidePanel·MapView가 공유하는 단일 정규 팔레트.
// (이전엔 App.jsx·SidePanel.jsx·GraphView.jsx에 따로 정의돼 GraphView만 값이 달랐다 →
//  같은 색이 다른 타입을 뜻하는 충돌. 여기 하나로 통일한다.)
// Night Atlas 다크 단일(ADR-0013) 대비 보정값 — 정본: .forge/reports/design-direction.md
export const TYPE_COLOR = {
  Person: '#8fa8ff',
  Place: '#58a4e8',
  Event: '#f0a844',
  PeopleGroup: '#3cc4b4',
  Book: '#b49dfa',
  Unknown: '#9aa5b8',
}

export const TYPE_KO = {
  Person: '인물', Place: '장소', Event: '사건', PeopleGroup: '집단', Book: '성경책', Unknown: '기타',
}

// 칩·범례 등에서 타입을 보여줄 표시 순서(실 타입 5종).
export const TYPE_ORDER = ['Person', 'Place', 'Event', 'PeopleGroup', 'Book']

export const typeColor = (label) => TYPE_COLOR[label] || TYPE_COLOR.Unknown
export const typeKo = (label) => TYPE_KO[label] || label

// valence(관계 성격) 색 — 채도 완화(다크 대비)
export const VALENCE_COLOR = { 긍정: '#4eba7d', 부정: '#e06c5f', 중립: '#8a94ad' }

// 선택(selectedNode) 시각 강조 — 뷰 공통. 선택 = 금색(Night Atlas 브랜드 액센트).
export const SELECT_HL = 'rgba(201,168,76,0.16)'

// 표면·잉크·금색 등 CSS 변수(index.css) 값이 필요한 JS 지점용 상수
export const NIGHT = {
  bg0: '#0e0f22', bg1: '#16173a', bg2: '#1e2144', bg3: '#272a55',
  ink: '#e9e6da', inkDim: 'rgba(233,230,218,0.64)', inkFaint: 'rgba(233,230,218,0.42)',
  line: 'rgba(255,255,255,0.09)', lineStrong: 'rgba(255,255,255,0.18)',
  gold: '#c9a84c', goldDim: 'rgba(201,168,76,0.35)',
  paper: '#f2ecdc', paperInk: '#2e2a20', paperAccent: '#8a6d1f',
}
