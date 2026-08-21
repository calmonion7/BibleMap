// 시대 밴드(task#200) — ADR-0014 보수 연대 기반 연도 경계, curated.py ERA_ORDER 8구간과 정합(task#278에 persons.py에서 이관).
// 경계 근거: 아브라함 출생 BC 2166 · 야곱 애굽 이주 BC 1876 · 사사기 시작 BC 1375 ·
// 사울 즉위 BC 1050 · 왕국 분열 BC 930 · 예루살렘 함락 BC 586 · 예수 탄생 BC 5경.
//
// task#271에서 TimelineView.jsx에서 이 공용 모듈로 승급했다 — 통사 연표가 같은 경계를 써야 하는데
// 컴포넌트 파일에서 상수를 export하면 react-refresh 규칙에 걸리고, 재선언하면 **세 번째 복제**가 된다.
// 배포 게이트 validate_era_bands_consistency.py가 이 파일의 `const ERA_BANDS = [` 리터럴을
// 스크래핑해 stats.py·persons.py와 대조하므로, 리터럴 모양을 바꾸지 말 것.
export const ERA_BANDS = [
  { name: '원시사', from: -Infinity, range: '창조 – BC 2166' },
  { name: '족장', from: -2166, range: 'BC 2166 – 1876' },
  { name: '출애굽·정복', from: -1876, range: 'BC 1876 – 1375' },
  { name: '사사', from: -1375, range: 'BC 1375 – 1050' },
  { name: '왕국', from: -1050, range: 'BC 1050 – 930' },
  { name: '선지자', from: -930, range: 'BC 930 – 586' },
  { name: '포로', from: -586, range: 'BC 586 – 5' },
  { name: '신약', from: -5, range: 'BC 5 –' },
]

export const eraOf = (y) => {
  let band = ERA_BANDS[0]
  for (const b of ERA_BANDS) { if (y >= b.from) band = b }
  return band
}
