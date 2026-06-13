// 노드 타입 → 색·한글 라벨 — 검색·SidePanel·MapView·GraphView가 공유하는 단일 정규 팔레트.
// (이전엔 App.jsx·SidePanel.jsx·GraphView.jsx에 따로 정의돼 GraphView만 값이 달랐다 →
//  같은 색이 다른 타입을 뜻하는 충돌. 여기 하나로 통일한다.)
export const TYPE_COLOR = {
  Person: '#7c9cfc',
  Place: '#4a90d9',
  Event: '#f5a623',
  PeopleGroup: '#2bb6a8',
  Unknown: '#9aa5b8',
}

export const TYPE_KO = {
  Person: '인물', Place: '장소', Event: '사건', PeopleGroup: '집단', Unknown: '기타',
}

// 칩·범례 등에서 타입을 보여줄 표시 순서(실 타입 4종).
export const TYPE_ORDER = ['Person', 'Place', 'Event', 'PeopleGroup']

export const typeColor = (label) => TYPE_COLOR[label] || TYPE_COLOR.Unknown
export const typeKo = (label) => TYPE_KO[label] || label

// 선택(selectedNode) 시각 강조 — 뷰 공통(페리윙클 틴트). 검색·SidePanel과 동일.
export const SELECT_HL = 'rgba(124,156,252,0.18)'
