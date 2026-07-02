// startDate("사건 연대")는 혼재 형식 문자열 — 연도만("-4003","30"), 연-월("-1451-01"),
// 제로패딩("0049-10-01")이 공존하고 BC는 음수 접두. 숫자 강제변환·사전순 정렬은 함정
// (.forge/CONTEXT.md '사건 연대' 참조). 라벨 변환은 반드시 이 헬퍼를 거친다.
export function parseYear(startDate) {
  if (!startDate) return ''
  if (startDate.startsWith('-')) {
    const year = startDate.slice(1).split('-')[0].replace(/^0+/, '') || '0'
    return 'BC ' + year
  }
  const year = startDate.split('-')[0].replace(/^0+/, '') || '1'
  return 'AD ' + year
}
