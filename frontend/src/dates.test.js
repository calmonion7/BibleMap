import { describe, it, expect } from 'vitest'
import { parseYear } from './dates'

describe('parseYear — 혼재 연대 문자열 → 라벨', () => {
  it('음수 연도만', () => {
    expect(parseYear('-4003')).toBe('BC 4003')
  })

  it('양수 연도만', () => {
    expect(parseYear('30')).toBe('AD 30')
  })

  it('음수 연-월', () => {
    expect(parseYear('-1451-01')).toBe('BC 1451')
  })

  it('제로패딩 연-월-일 (AD)', () => {
    expect(parseYear('0049-10-01')).toBe('AD 49')
  })

  it('제로패딩 음수 연도 (BC)', () => {
    expect(parseYear('-0049')).toBe('BC 49')
  })

  it('빈값은 빈 문자열', () => {
    expect(parseYear('')).toBe('')
    expect(parseYear(null)).toBe('')
    expect(parseYear(undefined)).toBe('')
  })
})
