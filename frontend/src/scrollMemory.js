// 목록 stage의 스크롤 위치를 stage 키('hub'·'overview')별로 기억한다 — 항목(인물/책) 클릭 후
// 뒤로 왔을 때 눌렀던 위치로 복원하기 위함(task#214). 모듈 스코프라 컴포넌트 리마운트를 견디고,
// 새로고침 시 자연히 초기화된다.
//
// history.state 대신 모듈 메모리를 쓰는 이유: 인앱 "← 뒤로" 버튼은 popstate가 아니라 전진 push라
// history.state로는 인앱 뒤로 시 복원되지 않는다(ADR-0010). 모듈 메모리는 인앱 뒤로·OS 뒤로 모두 커버한다.
// plain object 사용 — 전역 Map 섀도잉 런타임 크래시 함정 회피(useStageNavigation.js 주석 참조).
const positions = {}

export function saveScroll(key, top) {
  positions[key] = top
}

export function loadScroll(key) {
  return positions[key] || 0
}
