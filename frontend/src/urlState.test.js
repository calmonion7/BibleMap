import { describe, it, expect } from 'vitest'
import { encodeHash, parseHash } from './urlState'

// 왕복 대칭 — parseHash(encodeHash(x))가 x의 내비게이션 의미를 보존하는지.
// parseHash는 항상 personSlug/tourSlug/exploreView를 채워 돌려주므로, 입력 x가 명시한 필드만 대조한다.
const roundtrip = (state) => parseHash(encodeHash(state))

describe('encodeHash ↔ parseHash 왕복 대칭', () => {
  const cases = [
    ['허브', { stage: 'hub' }, { stage: 'hub' }],
    ['인트로', { stage: 'intro' }, { stage: 'intro' }],
    ['개요', { stage: 'overview' }, { stage: 'overview' }],
    ['통계', { stage: 'stats' }, { stage: 'stats' }],
    ['주제', { stage: 'topics' }, { stage: 'topics' }],
    ['테마 목록', { stage: 'tours' }, { stage: 'tours' }],
    ['책 상세', { stage: 'book', bookId: '12345' }, { stage: 'book', bookId: '12345' }],
    ['리더(장 그리드)', { stage: 'reader', readerBookId: 'gen' }, { stage: 'reader', readerBookId: 'gen', readerChapter: null }],
    ['리더(장 본문)', { stage: 'reader', readerBookId: 'gen', readerChapter: 3 }, { stage: 'reader', readerBookId: 'gen', readerChapter: 3 }],
    ['가족', { stage: 'family', familyId: 'abraham-clan' }, { stage: 'family', familyId: 'abraham-clan' }],
    ['낱말', { stage: 'words', wordsBookId: 'psa' }, { stage: 'words', wordsBookId: 'psa' }],
    ['투어(지도)', { stage: 'explore', tourSlug: 'exodus-to-conquest' }, { stage: 'explore', tourSlug: 'exodus-to-conquest', exploreView: 'map' }],
    ['투어(연표)', { stage: 'explore', tourSlug: 'exodus-to-conquest', exploreView: 'timeline' }, { stage: 'explore', tourSlug: 'exodus-to-conquest', exploreView: 'timeline' }],
    ['인물(지도)', { stage: 'explore', personSlug: 'moses' }, { stage: 'explore', personSlug: 'moses', exploreView: 'map' }],
    ['인물(연표)', { stage: 'explore', personSlug: 'moses', exploreView: 'timeline' }, { stage: 'explore', personSlug: 'moses', exploreView: 'timeline' }],
    ['인물(관계)', { stage: 'explore', personSlug: 'moses', exploreView: 'relations' }, { stage: 'explore', personSlug: 'moses', exploreView: 'relations' }],
    ['인물(소개)', { stage: 'explore', personSlug: 'moses', exploreView: 'intro' }, { stage: 'explore', personSlug: 'moses', exploreView: 'intro' }],
    ['인물(의지)', { stage: 'explore', personSlug: 'moses', exploreView: 'reliance' }, { stage: 'explore', personSlug: 'moses', exploreView: 'reliance' }],
  ]

  for (const [label, input, expected] of cases) {
    it(label, () => {
      expect(roundtrip(input)).toMatchObject(expected)
    })
  }

  it('slug에 특수문자가 있어도 왕복한다 (encodeURIComponent/decodeURIComponent 쌍)', () => {
    const slug = '이사야/아모스 자손'
    expect(roundtrip({ stage: 'explore', personSlug: slug })).toMatchObject({ stage: 'explore', personSlug: slug })
  })
})

describe('encodeHash 폴백', () => {
  it('slug 없는 explore는 허브로 떨어진다', () => {
    expect(encodeHash({ stage: 'explore' })).toBe('#/')
  })

  it('id 없는 book/reader/family/words도 허브로 떨어진다', () => {
    for (const stage of ['book', 'reader', 'family', 'words']) {
      expect(encodeHash({ stage })).toBe('#/')
    }
  })

  it('readerChapter가 0이면 장 번호를 붙이지 않는다 (falsy 취급 — 현재 구현 고정)', () => {
    expect(encodeHash({ stage: 'reader', readerBookId: 'gen', readerChapter: 0 })).toBe('#/read/gen')
  })
})

describe('parseHash 방어 동작', () => {
  it('빈 문자열·"#"·"#/"는 허브', () => {
    for (const h of ['', '#', '#/', '/']) {
      expect(parseHash(h)).toMatchObject({ stage: 'hub', exploreView: 'map' })
    }
  })

  it('null/undefined도 허브 (빈값 폴백)', () => {
    expect(parseHash(null)).toMatchObject({ stage: 'hub' })
    expect(parseHash(undefined)).toMatchObject({ stage: 'hub' })
  })

  it('알 수 없는 해시는 null — 호출부가 허브로 폴백한다', () => {
    for (const h of ['#/nope', '#/person', '#/person/moses/unknown', '#/book/a/b', '#/read/gen/abc']) {
      expect(parseHash(h)).toBeNull()
    }
  })

  it('선행 # 유무를 가리지 않는다', () => {
    expect(parseHash('#/stats')).toMatchObject({ stage: 'stats' })
    expect(parseHash('/stats')).toMatchObject({ stage: 'stats' })
  })

  it('readerChapter는 숫자로 변환된다', () => {
    expect(parseHash('#/read/gen/12')).toMatchObject({ stage: 'reader', readerBookId: 'gen', readerChapter: 12 })
  })
})
